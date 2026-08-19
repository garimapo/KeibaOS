"""Pure injected orchestration of complete JRA historical input sources."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass
from datetime import datetime as _datetime, timezone as _timezone
import re as _re
from typing import Protocol as _Protocol

from scripts.simulation.historical_input_source_records import (
    HistoricalInputSourceError as _HistoricalInputSourceError,
    HistoricalInputSourceRecord as _HistoricalInputSourceRecord,
    validate_historical_input_source_record_set as _validate_historical_input_source_record_set,
)
from scripts.simulation.jra_final_win_odds_request_locator import (
    JRAFinalWinOddsRequestLocatorExtractionValidationError as _LocatorValidationError,
    extract_jra_final_win_odds_request_locator as _extract_locator,
)
from scripts.simulation.jra_historical_past_race_absence_source import (
    JRAHistoricalPastRaceAbsenceSourceValidationError as _AbsenceValidationError,
    project_jra_historical_past_race_absence_source_record as _project_absence,
)
from scripts.simulation.jra_historical_past_race_discovery import (
    JRAHistoricalEventKind as _EventKind,
    JRAHistoricalPastRaceDiscovery as _Discovery,
    JRAHistoricalPastRaceDiscoveryUnsupportedError as _DiscoveryUnsupportedError,
    JRAHistoricalPastRaceDiscoveryValidationError as _DiscoveryValidationError,
    JRAHistoricalPastRaceReference as _Reference,
    discover_jra_historical_past_race_history as _discover,
)
from scripts.simulation.jra_historical_past_race_source import (
    JRAHistoricalPastRaceSourceUnsupportedError as _PastRaceUnsupportedError,
    JRAHistoricalPastRaceSourceValidationError as _PastRaceValidationError,
    normalize_jra_historical_past_race_source_record as _normalize_past_race,
)
from scripts.simulation.jra_official_identity import (
    JRAOfficialFinalWinOddsRequestLocator as _Locator,
    JRAOfficialIdentityValidationError as _IdentityValidationError,
    build_jra_external_entry_id as _build_entry_id,
    parse_jra_external_race_id as _parse_race_id,
    parse_jra_result_url_identity as _parse_result_url,
)
from scripts.simulation.jra_official_response_capture import (
    JRAFinalWinOddsSuppliedOfficialResponse as _FinalOddsResponse,
    JRASuppliedOfficialResponse as _ResultResponse,
)


class JRAHistoricalSourceCollectionError(ValueError):
    """Base error for complete JRA historical-source collection."""


class JRAHistoricalSourceCollectionValidationError(JRAHistoricalSourceCollectionError):
    """Raised for malformed, incomplete, or contradictory collection evidence."""


class JRAHistoricalSourceCollectionUnsupportedError(JRAHistoricalSourceCollectionError):
    """Raised for complete history containing an unsupported actual-start kind."""


class JRAHistoricalSourceCollectionUnavailableError(JRAHistoricalSourceCollectionError):
    """Raised when an otherwise required causal historical response is unavailable."""


class JRAHistoricalRaceResultResponseProvider(_Protocol):
    def __call__(
        self,
        *,
        race_reference: _Reference,
        observed_at_not_after: _datetime,
    ) -> _ResultResponse | None: ...


class JRAHistoricalFinalWinOddsResponseProvider(_Protocol):
    def __call__(
        self,
        *,
        request_locator: _Locator,
        observed_at_not_after: _datetime,
    ) -> _FinalOddsResponse | None: ...


_POSITIVE = _re.compile(r"[1-9][0-9]*\Z")


def _validation(message: str) -> JRAHistoricalSourceCollectionValidationError:
    return JRAHistoricalSourceCollectionValidationError(message)


def _unsupported(message: str) -> JRAHistoricalSourceCollectionUnsupportedError:
    return JRAHistoricalSourceCollectionUnsupportedError(message)


def _entry_lineage(*, race_id: str, entry_id: str) -> None:
    try:
        race = _parse_race_id(race_id)
        prefix = f"{race.external_race_id}:entry:"
        if not entry_id.startswith(prefix):
            raise ValueError
        horse_no = entry_id.removeprefix(prefix)
        if _POSITIVE.fullmatch(horse_no) is None:
            raise ValueError
        if _build_entry_id(race_identity=race, horse_no=horse_no) != entry_id:
            raise ValueError
    except (_IdentityValidationError, TypeError, ValueError, OverflowError) as error:
        raise _validation("collection target lineage is invalid") from error


@_dataclass(frozen=True, slots=True)
class JRAHistoricalSourceCollection:
    target_external_race_id: str
    target_external_entry_id: str
    source_records: tuple[_HistoricalInputSourceRecord, ...]

    def __post_init__(self) -> None:
        if (
            type(self.target_external_race_id) is not str
            or type(self.target_external_entry_id) is not str
            or type(self.source_records) is not tuple
            or not self.source_records
            or any(type(record) is not _HistoricalInputSourceRecord for record in self.source_records)
        ):
            raise _validation("historical source collection is invalid")
        _entry_lineage(
            race_id=self.target_external_race_id,
            entry_id=self.target_external_entry_id,
        )
        for record in self.source_records:
            if (
                record.organization != "JRA"
                or record.source_system != "jra_official"
                or record.external_race_id != self.target_external_race_id
                or record.external_entry_id != self.target_external_entry_id
                or record.record_kind not in {"past_race", "past_race_absence"}
            ):
                raise _validation("collection source record is not target-bound")
        races = tuple(record for record in self.source_records if record.record_kind == "past_race")
        absences = tuple(record for record in self.source_records if record.record_kind == "past_race_absence")
        if (not races and len(absences) != 1) or (races and absences):
            raise _validation("collection past-race evidence is incoherent")


def _scheduled_start(track: object) -> _datetime:
    if type(track) is not _HistoricalInputSourceRecord:
        raise _validation("target_track_record is invalid")
    try:
        value = track.record_values["scheduled_start_at"]
    except KeyError as error:
        raise _validation("target scheduled start is missing") from error
    if type(value) is not _datetime:
        raise _validation("target scheduled start is invalid")
    try:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError
    except (TypeError, ValueError, OverflowError) as error:
        raise _validation("target scheduled start is invalid") from error
    return value


def _bound(value: object, scheduled: _datetime) -> _datetime:
    if type(value) is not _datetime:
        raise _validation("observed_at_not_after is invalid")
    try:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError
        result = value.astimezone(_timezone.utc)
    except (TypeError, ValueError, OverflowError) as error:
        raise _validation("observed_at_not_after is invalid") from error
    if result > scheduled.astimezone(_timezone.utc):
        raise _validation("observed_at_not_after is after target scheduled start")
    return result


def _horse_history_response(*, response: object, scheduled: _datetime, bound: _datetime) -> _ResultResponse:
    if type(response) is not _ResultResponse or response.observed_at > scheduled or response.observed_at > bound:
        raise _validation("horse-history response is outside the causal bound")
    return response


def _result_response(*, response: object, reference: _Reference, scheduled: _datetime, bound: _datetime) -> _ResultResponse:
    if type(response) is not _ResultResponse:
        raise _validation("race-result provider response is invalid")
    try:
        identity = _parse_result_url(response.response_url)
    except _IdentityValidationError as error:
        raise _validation("race-result provider response is not accessS evidence") from error
    if (
        response.response_url != reference.canonical_race_result_url
        or identity != reference.race_identity
        or response.observed_at > scheduled
        or response.observed_at > bound
    ):
        raise _validation("race-result provider response disagrees with historical reference")
    return response


def _odds_response(*, response: object, locator: _Locator, scheduled: _datetime, bound: _datetime) -> _FinalOddsResponse:
    if type(response) is not _FinalOddsResponse:
        raise _validation("final-odds provider response is invalid")
    if response.request_locator != locator or response.observed_at > scheduled or response.observed_at > bound:
        raise _validation("final-odds provider response disagrees with request locator")
    return response


def _discovery(
    *,
    target_track_record: _HistoricalInputSourceRecord,
    target_entry_record: _HistoricalInputSourceRecord,
    horse_history_response: _ResultResponse,
) -> _Discovery:
    try:
        return _discover(
            target_track_record=target_track_record,
            target_entry_record=target_entry_record,
            horse_history_response=horse_history_response,
        )
    except _DiscoveryValidationError as error:
        raise _validation("JRA horse-history discovery is invalid") from error
    except _DiscoveryUnsupportedError as error:
        raise _unsupported("JRA horse-history discovery is unsupported") from error


def collect_jra_historical_input_source_records(
    *,
    target_track_record: _HistoricalInputSourceRecord,
    target_entry_record: _HistoricalInputSourceRecord,
    horse_history_response: _ResultResponse,
    observed_at_not_after: _datetime,
    race_result_response_provider: JRAHistoricalRaceResultResponseProvider,
    final_win_odds_response_provider: JRAHistoricalFinalWinOddsResponseProvider,
) -> JRAHistoricalSourceCollection:
    """Collect one complete, all-or-nothing JRA historical source set."""

    scheduled = _scheduled_start(target_track_record)
    bound = _bound(observed_at_not_after, scheduled)
    horse_history_response = _horse_history_response(
        response=horse_history_response,
        scheduled=scheduled,
        bound=bound,
    )
    discovery = _discovery(
        target_track_record=target_track_record,
        target_entry_record=target_entry_record,
        horse_history_response=horse_history_response,
    )
    for reference in discovery.events:
        if reference.event_kind is _EventKind.NON_JRA_ACTUAL_START:
            raise _unsupported("non-JRA actual start prevents JRA-only collection")
        if reference.event_kind is _EventKind.UNSUPPORTED_ACTUAL_START:
            raise _unsupported("unsupported actual start prevents JRA-only collection")
    actual = tuple(reference for reference in discovery.events if reference.event_kind is _EventKind.JRA_ACTUAL_START)
    if not actual:
        try:
            records = (_project_absence(discovery=discovery, horse_history_response=horse_history_response),)
        except _AbsenceValidationError as error:
            raise _validation("JRA absence projection is invalid") from error
    else:
        if not callable(race_result_response_provider) or not callable(final_win_odds_response_provider):
            raise _validation("historical response providers must be callable")
        result_cache: dict[tuple[str, str], _ResultResponse] = {}
        odds_cache: dict[str, _FinalOddsResponse] = {}
        records_list: list[_HistoricalInputSourceRecord] = []
        for reference in actual:
            if reference.race_identity is None or reference.canonical_race_result_url is None:
                raise _validation("JRA actual-start reference is invalid")
            race_key = (reference.race_identity.external_race_id, reference.canonical_race_result_url)
            result = result_cache.get(race_key)
            if result is None:
                provided = race_result_response_provider(
                    race_reference=reference,
                    observed_at_not_after=observed_at_not_after,
                )
                if provided is None:
                    raise JRAHistoricalSourceCollectionUnavailableError("causally eligible JRA race-result response is unavailable")
                result = _result_response(
                    response=provided,
                    reference=reference,
                    scheduled=scheduled,
                    bound=bound,
                )
                result_cache[race_key] = result
            else:
                _result_response(response=result, reference=reference, scheduled=scheduled, bound=bound)
            try:
                locator = _extract_locator(race_result_response=result)
            except _LocatorValidationError as error:
                raise _validation("JRA final-odds locator extraction is invalid") from error
            if locator.external_race_identity != reference.race_identity:
                raise _validation("JRA final-odds locator disagrees with historical reference")
            odds = odds_cache.get(locator.request_identity_sha256)
            if odds is None:
                provided_odds = final_win_odds_response_provider(
                    request_locator=locator,
                    observed_at_not_after=observed_at_not_after,
                )
                if provided_odds is None:
                    raise JRAHistoricalSourceCollectionUnavailableError("causally eligible JRA final-odds response is unavailable")
                odds = _odds_response(
                    response=provided_odds,
                    locator=locator,
                    scheduled=scheduled,
                    bound=bound,
                )
                odds_cache[locator.request_identity_sha256] = odds
            else:
                _odds_response(response=odds, locator=locator, scheduled=scheduled, bound=bound)
            try:
                records_list.append(
                    _normalize_past_race(
                        target_track_record=target_track_record,
                        target_entry_record=target_entry_record,
                        race_result_response=result,
                        final_win_odds_response=odds,
                    )
                )
            except _PastRaceValidationError as error:
                raise _validation("JRA past-race normalization is invalid") from error
            except _PastRaceUnsupportedError as error:
                raise _unsupported("JRA past-race normalization is unsupported") from error
        records = tuple(records_list)
    try:
        validated = _validate_historical_input_source_record_set(records=records)
    except _HistoricalInputSourceError as error:
        raise _validation("JRA historical source records are invalid") from error
    return JRAHistoricalSourceCollection(
        target_external_race_id=discovery.target_external_race_id,
        target_external_entry_id=discovery.target_external_entry_id,
        source_records=validated,
    )


__all__ = (
    "JRAHistoricalRaceResultResponseProvider",
    "JRAHistoricalFinalWinOddsResponseProvider",
    "JRAHistoricalSourceCollection",
    "JRAHistoricalSourceCollectionError",
    "JRAHistoricalSourceCollectionValidationError",
    "JRAHistoricalSourceCollectionUnsupportedError",
    "JRAHistoricalSourceCollectionUnavailableError",
    "collect_jra_historical_input_source_records",
)


if "annotations" in globals():
    del annotations
