"""Pure JRA zero-actual-start past-race-absence normalization."""

from __future__ import annotations

from datetime import datetime as _datetime, timezone as _timezone
import hashlib as _hashlib

from scripts.simulation.historical_input_evidence import (
    HistoricalInputEvidenceReference as _HistoricalInputEvidenceReference,
)
from scripts.simulation.historical_input_source_records import (
    HistoricalInputSourceError as _HistoricalInputSourceError,
    HistoricalInputSourceRecord as _HistoricalInputSourceRecord,
)
from scripts.simulation.jra_historical_past_race_discovery import (
    JRAHistoricalEventKind as _JRAHistoricalEventKind,
    JRAHistoricalPastRaceDiscovery as _JRAHistoricalPastRaceDiscovery,
    JRAHistoricalPastRaceDiscoveryError as _JRAHistoricalPastRaceDiscoveryError,
    JRAHistoricalPastRaceReference as _JRAHistoricalPastRaceReference,
    discover_jra_historical_past_race_history as _discover_jra_historical_past_race_history,
)
from scripts.simulation.jra_official_identity import (
    JRAOfficialIdentityValidationError as _JRAOfficialIdentityValidationError,
    parse_jra_horse_profile_url_identity as _parse_jra_horse_profile_url_identity,
)
from scripts.simulation.jra_official_response_capture import (
    JRASuppliedOfficialResponse as _JRASuppliedOfficialResponse,
)


class JRAHistoricalPastRaceAbsenceSourceError(ValueError):
    """Base error for the pure JRA zero-actual-start source boundary."""


class JRAHistoricalPastRaceAbsenceSourceValidationError(
    JRAHistoricalPastRaceAbsenceSourceError,
):
    """Raised when supplied evidence does not prove zero actual prior starts."""


def _proves_zero_actual_prior_starts(discovery: object) -> bool:
    """Project only the formal discovery domain's closed event classification."""

    if type(discovery) is not _JRAHistoricalPastRaceDiscovery:
        raise JRAHistoricalPastRaceAbsenceSourceValidationError("historical discovery has an invalid type")
    if type(discovery.proven_zero_history) is not bool or type(discovery.events) is not tuple:
        raise JRAHistoricalPastRaceAbsenceSourceValidationError("historical discovery is incoherent")
    if discovery.proven_zero_history:
        if discovery.events != ():
            raise JRAHistoricalPastRaceAbsenceSourceValidationError("empty discovery is incoherent")
        return True
    events = discovery.events
    if not events:
        raise JRAHistoricalPastRaceAbsenceSourceValidationError("non-empty discovery is incoherent")
    if any(type(event) is not _JRAHistoricalPastRaceReference for event in events):
        raise JRAHistoricalPastRaceAbsenceSourceValidationError("historical event is incoherent")
    return all(event.event_kind is _JRAHistoricalEventKind.PROVEN_NON_START for event in events)


def _bound_response(
    *,
    discovery: _JRAHistoricalPastRaceDiscovery,
    horse_history_response: _JRASuppliedOfficialResponse,
) -> None:
    if type(horse_history_response) is not _JRASuppliedOfficialResponse:
        raise JRAHistoricalPastRaceAbsenceSourceValidationError(
            "horse_history_response must be JRASuppliedOfficialResponse",
        )
    if (
        type(discovery.horse_history_observed_at) is not _datetime
        or discovery.horse_history_observed_at.tzinfo is not _timezone.utc
        or discovery.horse_history_observed_at.utcoffset() != _timezone.utc.utcoffset(None)
    ):
        raise JRAHistoricalPastRaceAbsenceSourceValidationError(
            "discovery observed_at binding is incoherent",
        )
    if horse_history_response.response_url != discovery.horse_history_response_url:
        raise JRAHistoricalPastRaceAbsenceSourceValidationError(
            "horse_history_response URL disagrees with discovery",
        )
    if _hashlib.sha256(horse_history_response.response_body).hexdigest() != discovery.horse_history_response_sha256:
        raise JRAHistoricalPastRaceAbsenceSourceValidationError(
            "horse_history_response body disagrees with discovery",
        )
    if horse_history_response.observed_at != discovery.horse_history_observed_at:
        raise JRAHistoricalPastRaceAbsenceSourceValidationError(
            "horse_history_response observed_at disagrees with discovery",
        )
    try:
        response_horse = _parse_jra_horse_profile_url_identity(horse_history_response.response_url)
    except _JRAOfficialIdentityValidationError as error:
        raise JRAHistoricalPastRaceAbsenceSourceValidationError(
            "horse_history_response is not accessU evidence",
        ) from error
    if response_horse.external_horse_id != discovery.target_external_horse_id:
        raise JRAHistoricalPastRaceAbsenceSourceValidationError(
            "horse_history_response horse identity disagrees with discovery",
        )


def project_jra_historical_past_race_absence_source_record(
    *,
    discovery: _JRAHistoricalPastRaceDiscovery,
    horse_history_response: _JRASuppliedOfficialResponse,
) -> _HistoricalInputSourceRecord:
    """Project one bound complete discovery into a neutral absence record."""

    if type(discovery) is not _JRAHistoricalPastRaceDiscovery:
        raise JRAHistoricalPastRaceAbsenceSourceValidationError(
            "discovery must be exact JRAHistoricalPastRaceDiscovery",
        )
    _bound_response(discovery=discovery, horse_history_response=horse_history_response)
    if not _proves_zero_actual_prior_starts(discovery):
        raise JRAHistoricalPastRaceAbsenceSourceValidationError(
            "JRA discovery does not prove zero actual prior starts",
        )
    query_scope = {
        "external_entry_id": discovery.target_external_entry_id,
        "target_race_date": discovery.target_race_date,
        "strictly_before_target_race": True,
    }
    try:
        return _HistoricalInputSourceRecord(
            record_kind="past_race_absence",
            organization="JRA",
            source_system="jra_official",
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
                    discovery.horse_history_response_url,
                    discovery.horse_history_response_sha256,
                    None,
                    discovery.horse_history_observed_at,
                ),
            ),
        )
    except (_HistoricalInputSourceError, TypeError, ValueError, OverflowError) as error:
        raise JRAHistoricalPastRaceAbsenceSourceValidationError(
            "past_race_absence source record is invalid",
        ) from error


def normalize_jra_historical_past_race_absence_source_record(
    *,
    target_track_record: _HistoricalInputSourceRecord,
    target_entry_record: _HistoricalInputSourceRecord,
    horse_history_response: _JRASuppliedOfficialResponse,
) -> _HistoricalInputSourceRecord:
    """Normalize formal JRA zero-actual-start discovery into one absence record."""

    try:
        discovery = _discover_jra_historical_past_race_history(
            target_track_record=target_track_record,
            target_entry_record=target_entry_record,
            horse_history_response=horse_history_response,
        )
    except _JRAHistoricalPastRaceDiscoveryError as error:
        raise JRAHistoricalPastRaceAbsenceSourceValidationError(
            "JRA horse-history discovery is invalid",
        ) from error
    return project_jra_historical_past_race_absence_source_record(
        discovery=discovery,
        horse_history_response=horse_history_response,
    )


__all__ = (
    "JRAHistoricalPastRaceAbsenceSourceError",
    "JRAHistoricalPastRaceAbsenceSourceValidationError",
    "normalize_jra_historical_past_race_absence_source_record",
    "project_jra_historical_past_race_absence_source_record",
)


if "annotations" in globals():
    del annotations
