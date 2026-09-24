"""Connection-injected append-only Phase104 runtime/execution parent archive."""

from __future__ import annotations

import sqlite3

from scripts.simulation import nar_operational_timing_runtime_execution_archive_migration as schema
from scripts.simulation.nar_operational_timing_runtime_source_provenance import NARRuntimeSourceBundle
from scripts.simulation.nar_operational_timing_runtime_profile import (
    NARRuntimeDependencyProfile, NARStaticRuntimeTransportProfile,
)
from scripts.simulation.nar_operational_timing_runtime_execution import (
    NAROperationalTimingRuntimeBinding, NAROperationalTimingCampaignExecutionClaim,
    NAROperationalTimingCampaignReadinessVerificationReceipt,
)
from scripts.simulation.sqlite_nar_operational_timing_v2_authority_archive import (
    SQLiteNAROperationalTimingV2AuthorityArchive,
)
from scripts.simulation.sqlite_nar_operational_timing_observability_archive import (
    TimingArchiveError, TimingArchiveConflict,
)


_ISSUANCE_MARKER = object()  # Trusted API discipline, not cryptographic authority.


class SQLiteNAROperationalTimingRuntimeExecutionArchive:
    __slots__ = ("_connection", "v2")

    def __init__(self, *, connection: sqlite3.Connection) -> None:
        if type(connection) is not sqlite3.Connection or connection.in_transaction:
            raise TimingArchiveError("runtime archive requires exact idle SQLite connection")
        schema.require_nar_operational_timing_runtime_execution_archive_compatible_schema(connection)
        self._connection = connection
        self.v2 = SQLiteNAROperationalTimingV2AuthorityArchive(connection=connection)

    def _row(self, table: str, column: str, identity: str) -> tuple | None:
        schema.require_nar_operational_timing_runtime_execution_archive_compatible_schema(self._connection)
        rows = self._connection.execute(f"SELECT * FROM {table} WHERE {column}=?", (identity,)).fetchall()
        if len(rows) > 1:
            raise TimingArchiveError("runtime authority natural identity is duplicated")
        return tuple(rows[0]) if rows else None

    def _save(self, *, table: str, natural_column: str, natural_identity: str,
              row: tuple, columns: str) -> bool:
        if self._connection.in_transaction:
            raise TimingArchiveError("runtime authority write requires idle connection")
        schema.require_nar_operational_timing_runtime_execution_archive_compatible_schema(self._connection)
        try:
            self._connection.execute("BEGIN IMMEDIATE")
            rows = self._connection.execute(
                f"SELECT * FROM {table} WHERE {natural_column}=? OR identity=?",
                (natural_identity, row[0]),
            ).fetchall()
            if rows:
                if len(rows) != 1 or tuple(rows[0]) != row:
                    raise TimingArchiveConflict("immutable runtime identity conflicts")
                inserted = False
            else:
                values = ",".join("?" for _ in row)
                self._connection.execute(f"INSERT INTO {table}({columns}) VALUES({values})", row)
                if tuple(self._connection.execute(
                    f"SELECT * FROM {table} WHERE identity=?", (row[0],)
                ).fetchone()) != row:
                    raise TimingArchiveError("runtime authority did not reload exactly")
                inserted = True
            self._connection.commit()
            return inserted
        except sqlite3.IntegrityError as error:
            self._connection.rollback()
            raise TimingArchiveConflict("runtime authority parent or identity conflicts") from error
        except BaseException:
            self._connection.rollback()
            raise

    def _save_simple(self, table: str, value: object, value_type: type,
                     identity_name: str) -> None:
        if type(value) is not value_type:
            raise TimingArchiveError("exact runtime authority value required")
        encoded = value.canonical_bytes().decode("utf-8")
        if value_type.from_json(encoded) != value:
            raise TimingArchiveError("runtime authority content is contradictory")
        identity = getattr(value, identity_name)
        self._save(table=table, natural_column="identity", natural_identity=identity,
                   row=(identity, encoded), columns="identity,payload_json")

    def _load_simple(self, table: str, identity: str, value_type: type,
                     identity_name: str):
        row = self._row(table, "identity", identity)
        if row is None:
            return None
        try:
            result = value_type.from_json(row[1])
            if getattr(result, identity_name) != row[0]:
                raise ValueError("runtime content identity mismatch")
            return result
        except (KeyError, TypeError, ValueError) as error:
            raise TimingArchiveError("stored runtime authority is corrupt") from error

    def save_bundle(self, *, bundle: NARRuntimeSourceBundle) -> None:
        self._save_simple(schema.BUNDLES, bundle, NARRuntimeSourceBundle, "bundle_identity")

    def load_bundle(self, *, bundle_identity: str) -> NARRuntimeSourceBundle | None:
        return self._load_simple(schema.BUNDLES, bundle_identity, NARRuntimeSourceBundle, "bundle_identity")

    def save_dependency_profile(self, *, profile: NARRuntimeDependencyProfile) -> None:
        self._save_simple(schema.DEPENDENCIES, profile, NARRuntimeDependencyProfile, "profile_identity")

    def load_dependency_profile(self, *, profile_identity: str) -> NARRuntimeDependencyProfile | None:
        return self._load_simple(schema.DEPENDENCIES, profile_identity, NARRuntimeDependencyProfile, "profile_identity")

    def save_transport_profile(self, *, profile: NARStaticRuntimeTransportProfile) -> None:
        self._save_simple(schema.TRANSPORTS, profile, NARStaticRuntimeTransportProfile, "profile_identity")

    def load_transport_profile(self, *, profile_identity: str) -> NARStaticRuntimeTransportProfile | None:
        return self._load_simple(schema.TRANSPORTS, profile_identity, NARStaticRuntimeTransportProfile, "profile_identity")

    def _require_binding_ancestry(self, binding: NAROperationalTimingRuntimeBinding) -> None:
        session = self.v2.load_session(session_identity=binding.session_identity)
        if session is None or session.configuration.configuration_identity != binding.configuration_identity:
            raise TimingArchiveError("runtime binding lacks exact V2 session/configuration")
        declaration = self.v2.load_declaration_for_session(session_identity=binding.session_identity)
        receipt = self.v2.load_verification_for_declaration(declaration_identity=binding.declaration_identity)
        if (declaration is None or declaration.declaration_identity != binding.declaration_identity
                or receipt is None or receipt.verification_identity != binding.verification_identity
                or receipt.activation_verified_at > session.measurement_start_at):
            raise TimingArchiveError("runtime binding lacks qualifying V2 activation")
        bundle = self.load_bundle(bundle_identity=binding.bundle_identity)
        if bundle is None or bundle.commit_sha != session.configuration.software_commit_sha:
            raise TimingArchiveError("runtime source differs from declared commit")
        if self.load_dependency_profile(profile_identity=binding.dependency_profile_identity) is None:
            raise TimingArchiveError("runtime dependency profile absent")
        transport = self.load_transport_profile(profile_identity=binding.transport_profile_identity)
        if transport is None:
            raise TimingArchiveError("static transport profile absent")
        transport.require_matches_declared(session.configuration)

    def save_binding(self, *, binding: NAROperationalTimingRuntimeBinding,
                     _issuance_marker: object = None) -> None:
        if type(binding) is not NAROperationalTimingRuntimeBinding or _issuance_marker is not _ISSUANCE_MARKER:
            raise TimingArchiveError("runtime binding requires controlled issuance")
        self._require_binding_ancestry(binding)
        row = (binding.binding_identity, binding.configuration_identity, binding.session_identity,
               binding.declaration_identity, binding.verification_identity, binding.bundle_identity,
               binding.dependency_profile_identity, binding.transport_profile_identity,
               binding.lock_scope_identity, binding.canonical_bytes().decode("utf-8"))
        self._save(table=schema.BINDINGS, natural_column="identity", natural_identity=row[0], row=row,
                   columns="identity,configuration_identity,session_identity,declaration_identity,verification_identity,bundle_identity,dependency_identity,transport_identity,lock_scope_identity,payload_json")

    def load_binding(self, *, binding_identity: str) -> NAROperationalTimingRuntimeBinding | None:
        row = self._row(schema.BINDINGS, "identity", binding_identity)
        if row is None:
            return None
        try:
            result = NAROperationalTimingRuntimeBinding.from_json(row[-1])
            if (result.binding_identity, result.configuration_identity, result.session_identity,
                    result.declaration_identity, result.verification_identity, result.bundle_identity,
                    result.dependency_profile_identity, result.transport_profile_identity,
                    result.lock_scope_identity) != row[:-1]:
                raise ValueError("runtime binding row/content mismatch")
            self._require_binding_ancestry(result)
            return result
        except (KeyError, TypeError, ValueError) as error:
            raise TimingArchiveError("stored runtime binding is corrupt") from error

    def load_claim_for_session(self, *, session_identity: str) -> NAROperationalTimingCampaignExecutionClaim | None:
        row = self._row(schema.CLAIMS, "session_identity", session_identity)
        if row is None:
            return None
        try:
            result = NAROperationalTimingCampaignExecutionClaim.from_json(row[-1])
            if (result.claim_identity, result.session_identity, result.binding_identity,
                    result.configuration_identity, result.verification_identity) != row[:-1]:
                raise ValueError("claim row/content mismatch")
            binding = self.load_binding(binding_identity=result.binding_identity)
            if (binding is None or result.configuration_identity != binding.configuration_identity
                    or result.session_identity != binding.session_identity
                    or result.declaration_identity != binding.declaration_identity
                    or result.verification_identity != binding.verification_identity
                    or result.bundle_identity != binding.bundle_identity
                    or result.lock_scope_identity != binding.lock_scope_identity):
                raise ValueError("claim contradicts runtime binding")
            return result
        except (KeyError, TypeError, ValueError) as error:
            raise TimingArchiveError("stored execution claim is corrupt") from error

    def save_claim(self, *, claim: NAROperationalTimingCampaignExecutionClaim,
                   _issuance_marker: object = None) -> bool:
        if type(claim) is not NAROperationalTimingCampaignExecutionClaim or _issuance_marker is not _ISSUANCE_MARKER:
            raise TimingArchiveError("execution claim requires controlled issuance")
        binding = self.load_binding(binding_identity=claim.binding_identity)
        if (binding is None or claim.configuration_identity != binding.configuration_identity
                or claim.session_identity != binding.session_identity
                or claim.declaration_identity != binding.declaration_identity
                or claim.verification_identity != binding.verification_identity
                or claim.bundle_identity != binding.bundle_identity
                or claim.lock_scope_identity != binding.lock_scope_identity):
            raise TimingArchiveError("execution claim binding contradicts archive")
        row = (claim.claim_identity, claim.session_identity, claim.binding_identity,
               claim.configuration_identity, claim.verification_identity,
               claim.canonical_bytes().decode("utf-8"))
        return self._save(table=schema.CLAIMS, natural_column="session_identity",
                          natural_identity=claim.session_identity, row=row,
                          columns="identity,session_identity,binding_identity,configuration_identity,verification_identity,payload_json")

    def save_readiness(self, *, receipt: NAROperationalTimingCampaignReadinessVerificationReceipt,
                       _issuance_marker: object = None) -> None:
        if (type(receipt) is not NAROperationalTimingCampaignReadinessVerificationReceipt
                or _issuance_marker is not _ISSUANCE_MARKER):
            raise TimingArchiveError("readiness requires controlled issuance")
        claim = self.load_claim_for_session(session_identity=receipt.session_identity)
        if (claim is None or claim.claim_identity != receipt.claim_identity
                or claim.binding_identity != receipt.binding_identity
                or claim.configuration_identity != receipt.configuration_identity):
            raise TimingArchiveError("readiness claim contradicts archive")
        row = (receipt.receipt_identity, receipt.claim_identity, receipt.binding_identity,
               receipt.session_identity, receipt.canonical_bytes().decode("utf-8"))
        self._save(table=schema.READINESS, natural_column="claim_identity",
                   natural_identity=receipt.claim_identity, row=row,
                   columns="identity,claim_identity,binding_identity,session_identity,payload_json")

    def load_readiness_for_claim(self, *, claim_identity: str) -> NAROperationalTimingCampaignReadinessVerificationReceipt | None:
        row = self._row(schema.READINESS, "claim_identity", claim_identity)
        if row is None:
            return None
        try:
            result = NAROperationalTimingCampaignReadinessVerificationReceipt.from_json(row[-1])
            if (result.receipt_identity, result.claim_identity,
                    result.binding_identity, result.session_identity) != row[:-1]:
                raise ValueError("readiness row/content mismatch")
            claim = self.load_claim_for_session(session_identity=result.session_identity)
            if (claim is None or claim.claim_identity != result.claim_identity
                    or claim.binding_identity != result.binding_identity
                    or claim.configuration_identity != result.configuration_identity):
                raise ValueError("readiness ancestry contradicts claim")
            return result
        except (KeyError, TypeError, ValueError) as error:
            raise TimingArchiveError("stored readiness is corrupt") from error
