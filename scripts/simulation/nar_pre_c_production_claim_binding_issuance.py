"""Claim-binding issuer: identities/equality constraints only, no execution input."""

from __future__ import annotations

from datetime import datetime

from scripts.simulation.nar_pre_c_production_claim_binding import (
    NARPreCProductionClaimBindingV1, NARPreCProductionClaimBindingError,
)
from scripts.simulation.sqlite_nar_pre_c_production_claim_binding_archive import (
    SQLiteNARPreCProductionClaimBindingArchive,
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


def issue_nar_pre_c_production_claim_binding(
    *, companion_archive: SQLiteNARPreCProductionClaimBindingArchive,
    runtime_archive: SQLiteNAROperationalTimingRuntimeExecutionArchive,
    phase112_archive: SQLiteNARPreCProductionPrestagedManifestArchive,
    phase109_repository: SQLiteNARProductionMappingRepository,
    session_identity: str, expected_claim_identity: str,
    phase112_manifest_identity: str, expected_availability_receipt_identity: str,
    expected_external_race_id: str | None = None,
    expected_prediction_cutoff: datetime | None = None,
) -> NARPreCProductionClaimBindingV1:
    if type(companion_archive) is not SQLiteNARPreCProductionClaimBindingArchive:
        raise NARPreCProductionClaimBindingError("exact injected Phase113 archive required")
    return companion_archive.publish(
        runtime_archive=runtime_archive, phase112_archive=phase112_archive,
        phase109_repository=phase109_repository, session_identity=session_identity,
        expected_claim_identity=expected_claim_identity,
        phase112_manifest_identity=phase112_manifest_identity,
        expected_availability_receipt_identity=expected_availability_receipt_identity,
        expected_external_race_id=expected_external_race_id,
        expected_prediction_cutoff=expected_prediction_cutoff)
