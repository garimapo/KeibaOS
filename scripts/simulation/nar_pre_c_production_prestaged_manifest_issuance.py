"""Phase112 controlled issuer; no provider, parser, claim, or root dependency."""

from __future__ import annotations

from datetime import datetime
from typing import Callable

from scripts.simulation.nar_pre_c_production_prestaged_manifest import (
    NARPreCProductionPrestagedAuthorityV1,
    NARPreCProductionPrestagingError,
)
from scripts.simulation.repositories.sqlite_nar_production_mapping_repository import (
    SQLiteNARProductionMappingRepository,
)
from scripts.simulation.sqlite_nar_pre_c_production_prestaged_manifest_archive import (
    SQLiteNARPreCProductionPrestagedManifestArchive,
)


def issue_nar_pre_c_production_prestaged_authority(
    *, phase109_repository: SQLiteNARProductionMappingRepository,
    companion_archive: SQLiteNARPreCProductionPrestagedManifestArchive,
    phase109_receipt_id: str, expected_external_race_id: str,
    expected_prediction_cutoff: datetime,
    utc_clock: Callable[[], datetime],
) -> NARPreCProductionPrestagedAuthorityV1:
    """Publish an exact mapping, then its first truthful availability proof."""
    if (type(phase109_repository) is not SQLiteNARProductionMappingRepository
            or type(companion_archive) is not SQLiteNARPreCProductionPrestagedManifestArchive):
        raise NARPreCProductionPrestagingError("exact injected repositories required")
    return companion_archive.publish(
        phase109_repository=phase109_repository,
        phase109_receipt_id=phase109_receipt_id,
        expected_external_race_id=expected_external_race_id,
        expected_prediction_cutoff=expected_prediction_cutoff,
        utc_clock=utc_clock,
    )
