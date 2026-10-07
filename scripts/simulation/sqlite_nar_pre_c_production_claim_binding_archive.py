"""One-store immutable binding publication; upstream stores are read-only."""

from __future__ import annotations

import sqlite3
from datetime import datetime

from scripts.simulation import nar_pre_c_production_claim_binding_archive_migration as schema
from scripts.simulation.nar_pre_c_production_claim_binding import (
    PREFIX, NARPreCProductionClaimBindingV1, NARPreCProductionClaimBindingError,
    NARPreCProductionClaimBindingConflict, _PREFIXES, _utc,
    binding_row, parse_binding, require_identity,
)
from scripts.simulation.nar_operational_timing_runtime_execution import (
    NAROperationalTimingCampaignExecutionClaim,
    NAROperationalTimingRuntimeBinding,
    NAROperationalTimingCampaignReadinessVerificationReceipt,
)
from scripts.simulation.nar_operational_timing_observability_v2 import (
    NAROperationalTimingMeasurementSessionV2,
)
from scripts.simulation.nar_pre_c_production_prestaged_manifest import (
    NARPreCProductionPrestagedAuthorityV1,
)
from scripts.simulation.sqlite_nar_operational_timing_runtime_execution_archive import (
    SQLiteNAROperationalTimingRuntimeExecutionArchive,
)
from scripts.simulation.sqlite_nar_pre_c_production_prestaged_manifest_archive import (
    SQLiteNARPreCProductionPrestagedManifestArchive,
)
from scripts.simulation.repositories.sqlite_nar_production_mapping_repository import (
    SQLiteNARProductionMappingRepository,
)


def _upstream_binding(
    *, runtime_archive: SQLiteNAROperationalTimingRuntimeExecutionArchive,
    phase112_archive: SQLiteNARPreCProductionPrestagedManifestArchive,
    phase109_repository: SQLiteNARProductionMappingRepository,
    session_identity: str, expected_claim_identity: str,
    phase112_manifest_identity: str, expected_availability_receipt_identity: str,
) -> NARPreCProductionClaimBindingV1:
    if (type(runtime_archive) is not SQLiteNAROperationalTimingRuntimeExecutionArchive
            or type(phase112_archive) is not SQLiteNARPreCProductionPrestagedManifestArchive
            or type(phase109_repository) is not SQLiteNARProductionMappingRepository):
        raise NARPreCProductionClaimBindingError("exact injected upstream repositories required")
    for repository in (runtime_archive, phase112_archive, phase109_repository):
        if repository._connection.in_transaction:
            raise NARPreCProductionClaimBindingError("committed upstream read required")
    for value, name in ((session_identity, "session_identity"),
                        (expected_claim_identity, "claim_identity"),
                        (phase112_manifest_identity, "phase112_manifest_identity"),
                        (expected_availability_receipt_identity, "phase112_availability_receipt_identity")):
        require_identity(value, _PREFIXES[name])
    claim = runtime_archive.load_claim_for_session(session_identity=session_identity)
    if (type(claim) is not NAROperationalTimingCampaignExecutionClaim
            or claim.claim_identity != expected_claim_identity or claim.session_identity != session_identity):
        raise NARPreCProductionClaimBindingError("exact runtime claim required")
    binding = runtime_archive.load_binding(binding_identity=claim.binding_identity)
    session = runtime_archive.v2.load_session(session_identity=session_identity)
    if (type(binding) is not NAROperationalTimingRuntimeBinding
            or type(session) is not NAROperationalTimingMeasurementSessionV2
            or session.session_identity != session_identity
            or session.configuration.configuration_identity != claim.configuration_identity
            or any(getattr(claim, name) != getattr(binding, name) for name in (
                "configuration_identity", "session_identity", "declaration_identity",
                "verification_identity", "bundle_identity", "lock_scope_identity"))
            or claim.binding_identity != binding.binding_identity):
        raise NARPreCProductionClaimBindingError("runtime binding/session ancestry differs")
    readiness = runtime_archive.load_readiness_for_claim(claim_identity=claim.claim_identity)
    if (type(readiness) is not NAROperationalTimingCampaignReadinessVerificationReceipt
            or readiness.claim_identity != claim.claim_identity
            or readiness.binding_identity != binding.binding_identity
            or readiness.session_identity != session.session_identity
            or readiness.configuration_identity != claim.configuration_identity
            or readiness.readiness_verified_at > session.measurement_start_at):
        raise NARPreCProductionClaimBindingError("qualifying exact runtime readiness required")
    authority = phase112_archive.load_authority(
        manifest_identity=phase112_manifest_identity, phase109_repository=phase109_repository)
    if (type(authority) is not NARPreCProductionPrestagedAuthorityV1
            or authority.manifest.identity != phase112_manifest_identity
            or authority.availability_receipt.identity != expected_availability_receipt_identity):
        raise NARPreCProductionClaimBindingError("exact Phase112 authority pair required")
    manifest = authority.manifest
    config = session.configuration
    if ((config.organization, config.source_system) != ("NAR", "nar_official")
            or (manifest.organization, manifest.source_system) != (config.organization, config.source_system)):
        raise NARPreCProductionClaimBindingError("upstream provider scope differs")
    return NARPreCProductionClaimBindingV1(
        claim.claim_identity, binding.binding_identity, session.session_identity,
        readiness.receipt_identity, manifest.identity, authority.availability_receipt.identity,
        manifest.phase109_receipt_id, manifest.organization, manifest.source_system,
        manifest.external_race_id, manifest.internal_race_id, manifest.prediction_cutoff)


class SQLiteNARPreCProductionClaimBindingArchive:
    def __init__(self, *, connection: sqlite3.Connection):
        schema.require_phase113_schema(connection)
        if connection.in_transaction:
            raise NARPreCProductionClaimBindingError("idle companion connection required")
        self._connection = connection

    def _load_content(self, identity: str) -> NARPreCProductionClaimBindingV1 | None:
        schema.require_phase113_schema(self._connection)
        row = self._connection.execute(
            f"SELECT * FROM {schema.BINDINGS} WHERE identity=?", (identity,)).fetchone()
        if row is None:
            return None
        value = parse_binding(row[-1], identity)
        if tuple(row) != binding_row(value):
            raise NARPreCProductionClaimBindingError("binding SQL projection differs")
        return value

    def load_binding(
        self, *, identity: str,
        runtime_archive: SQLiteNAROperationalTimingRuntimeExecutionArchive,
        phase112_archive: SQLiteNARPreCProductionPrestagedManifestArchive,
        phase109_repository: SQLiteNARProductionMappingRepository,
    ) -> NARPreCProductionClaimBindingV1 | None:
        """Durable ancestry only; no liveness, consumption or execution capability."""
        if self._connection.in_transaction:
            raise NARPreCProductionClaimBindingError("committed binding read required")
        require_identity(identity, PREFIX)
        value = self._load_content(identity)
        if value is None:
            return None
        expected = _upstream_binding(
            runtime_archive=runtime_archive, phase112_archive=phase112_archive,
            phase109_repository=phase109_repository, session_identity=value.session_identity,
            expected_claim_identity=value.claim_identity,
            phase112_manifest_identity=value.phase112_manifest_identity,
            expected_availability_receipt_identity=value.phase112_availability_receipt_identity)
        if value != expected:
            raise NARPreCProductionClaimBindingError("binding/upstream exact projection differs")
        return value

    def publish(
        self, *, runtime_archive: SQLiteNAROperationalTimingRuntimeExecutionArchive,
        phase112_archive: SQLiteNARPreCProductionPrestagedManifestArchive,
        phase109_repository: SQLiteNARProductionMappingRepository,
        session_identity: str, expected_claim_identity: str,
        phase112_manifest_identity: str, expected_availability_receipt_identity: str,
        expected_external_race_id: str | None = None,
        expected_prediction_cutoff: datetime | None = None,
    ) -> NARPreCProductionClaimBindingV1:
        c = self._connection
        if c.in_transaction:
            raise NARPreCProductionClaimBindingError("caller transaction not accepted")
        value = _upstream_binding(
            runtime_archive=runtime_archive, phase112_archive=phase112_archive,
            phase109_repository=phase109_repository, session_identity=session_identity,
            expected_claim_identity=expected_claim_identity,
            phase112_manifest_identity=phase112_manifest_identity,
            expected_availability_receipt_identity=expected_availability_receipt_identity)
        if (expected_external_race_id is not None
                and (type(expected_external_race_id) is not str or expected_external_race_id != value.external_race_id)):
            raise NARPreCProductionClaimBindingError("expected external target differs")
        if (expected_prediction_cutoff is not None
                and _utc(expected_prediction_cutoff) != value.prediction_cutoff):
            raise NARPreCProductionClaimBindingError("expected prediction cutoff differs")
        schema.require_phase113_schema(c)
        c.execute("BEGIN IMMEDIATE")
        try:
            schema.require_phase113_schema(c)
            rows = c.execute(
                f"SELECT identity FROM {schema.BINDINGS} WHERE identity=? "
                "OR phase112_manifest_identity=? OR phase112_availability_receipt_identity=? "
                "OR (organization=? AND source_system=? AND external_race_id=? AND prediction_cutoff=?) "
                "OR (organization=? AND source_system=? AND internal_race_id=? AND prediction_cutoff=?)",
                (value.identity, value.phase112_manifest_identity, value.phase112_availability_receipt_identity,
                 value.organization, value.source_system, value.external_race_id, value.prediction_cutoff.isoformat(),
                 value.organization, value.source_system, value.internal_race_id, value.prediction_cutoff.isoformat()),
            ).fetchall()
            if rows:
                if (len(rows) != 1 or rows[0][0] != value.identity
                        or self._load_content(value.identity) != value):
                    raise NARPreCProductionClaimBindingConflict("permanent target/manifest binding conflict")
            else:
                row = binding_row(value)
                c.execute(f"INSERT INTO {schema.BINDINGS} VALUES({','.join('?' for _ in row)})", row)
            c.commit()
        except BaseException:
            c.rollback()
            raise
        # Outside the write transaction: failures leave the durable row, never success.
        reloaded = self.load_binding(
            identity=value.identity, runtime_archive=runtime_archive,
            phase112_archive=phase112_archive, phase109_repository=phase109_repository)
        if reloaded != value:
            raise NARPreCProductionClaimBindingError("committed binding did not exact-reload")
        return reloaded
