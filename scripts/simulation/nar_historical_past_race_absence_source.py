"""Pure HorseMarkInfo-only zero-history past-race-absence normalization."""

from __future__ import annotations

import hashlib as _hashlib

from scripts.simulation.historical_input_evidence import (
    HistoricalInputEvidenceReference as _HistoricalInputEvidenceReference,
)
from scripts.simulation.historical_input_source_records import (
    HistoricalInputSourceRecord as _HistoricalInputSourceRecord,
)
from scripts.simulation.nar_historical_input_source import (
    NarSuppliedOfficialResponse as _NarSuppliedOfficialResponse,
)
from scripts.simulation.nar_historical_past_race_discovery import (
    discover_nar_historical_past_race_history as _discover_nar_historical_past_race_history,
)

if "annotations" in globals():
    del annotations


class NARHistoricalPastRaceAbsenceSourceError(ValueError):
    """Base error for the narrow NAR zero-history source-record boundary."""


class NARHistoricalPastRaceAbsenceSourceValidationError(
    NARHistoricalPastRaceAbsenceSourceError,
):
    """Raised when supplied target or zero-history evidence is invalid."""


def normalize_nar_historical_past_race_absence_source_record(
    *,
    target_track_record: _HistoricalInputSourceRecord,
    target_entry_record: _HistoricalInputSourceRecord,
    horse_history_response: _NarSuppliedOfficialResponse,
) -> _HistoricalInputSourceRecord:
    """Normalize the exact official HorseMarkInfo zero-history state into c1a."""

    try:
        discovery = _discover_nar_historical_past_race_history(
            target_track_record=target_track_record,
            target_entry_record=target_entry_record,
            horse_history_response=horse_history_response,
        )
    except (ValueError, TypeError, OverflowError) as error:
        raise NARHistoricalPastRaceAbsenceSourceValidationError(
            "HorseMarkInfo zero-history discovery is invalid",
        ) from error
    if not discovery.proven_zero_history or discovery.events != ():
        raise NARHistoricalPastRaceAbsenceSourceValidationError(
            "HorseMarkInfo does not prove zero actual history",
        )
    if type(horse_history_response) is not _NarSuppliedOfficialResponse:
        raise NARHistoricalPastRaceAbsenceSourceValidationError(
            "horse_history_response must be NarSuppliedOfficialResponse",
        )
    query_scope = {
        "external_entry_id": discovery.target_external_entry_id,
        "target_race_date": discovery.target_race_date,
        "strictly_before_target_race": True,
    }
    try:
        return _HistoricalInputSourceRecord(
            record_kind="past_race_absence",
            organization="NAR",
            source_system=target_track_record.source_system,
            external_race_id=discovery.target_external_race_id,
            external_entry_id=discovery.target_external_entry_id,
            provider_record_id=None,
            record_values={
                "external_entry_id": discovery.target_external_entry_id,
                "query_scope": query_scope,
                "result_count": 0,
            },
            evidence=(
                _HistoricalInputEvidenceReference(
                    "past_race_absence_query",
                    horse_history_response.response_url,
                    _hashlib.sha256(horse_history_response.response_body).hexdigest(),
                    None,
                    horse_history_response.observed_at,
                ),
            ),
        )
    except (ValueError, TypeError, OverflowError) as error:
        raise NARHistoricalPastRaceAbsenceSourceValidationError(
            "past_race_absence source record is invalid",
        ) from error


__all__ = (
    "NARHistoricalPastRaceAbsenceSourceError",
    "NARHistoricalPastRaceAbsenceSourceValidationError",
    "normalize_nar_historical_past_race_absence_source_record",
)
