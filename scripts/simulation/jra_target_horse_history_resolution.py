"""Pure binding of one retained JRA accessU locator to supplied history evidence."""

from __future__ import annotations

from datetime import datetime as _datetime, timezone as _timezone
import re as _re
from typing import Protocol as _Protocol

from scripts.simulation.historical_input_source_records import HistoricalInputSourceRecord as _Record
from scripts.simulation.jra_official_identity import (
    JRAOfficialIdentityValidationError as _IdentityError,
    build_jra_external_entry_id as _build_entry_id,
    parse_jra_external_horse_id as _parse_horse_id,
    parse_jra_external_race_id as _parse_race_id,
    parse_jra_horse_profile_url_identity as _parse_profile_url,
)
from scripts.simulation.jra_official_response_capture import (
    JRAOfficialPageKind as _PageKind,
    JRAOfficialResponseCaptureError as _CaptureError,
    JRASuppliedOfficialResponse as _Response,
    canonicalize_jra_official_capture_url as _canonicalize_url,
)
from scripts.simulation.jra_target_race_input_source import JRATargetHorseHistoryLocator as _Locator


class JRATargetHorseHistoryResolutionError(ValueError):
    """Base error for target-horse accessU history response resolution."""


class JRATargetHorseHistoryResolutionValidationError(JRATargetHorseHistoryResolutionError):
    """Raised for invalid target, locator, bound, or supplied response evidence."""


class JRATargetHorseHistoryResolutionUnavailableError(JRATargetHorseHistoryResolutionError):
    """Raised when no causally eligible history response is available."""


class JRATargetHorseHistoryResponseProvider(_Protocol):
    def __call__(
        self,
        *,
        locator: _Locator,
        observed_at_not_after: _datetime,
    ) -> _Response | None: ...


_POSITIVE = _re.compile(r"[1-9][0-9]*\Z")


def _validation(message: str) -> JRATargetHorseHistoryResolutionValidationError:
    return JRATargetHorseHistoryResolutionValidationError(message)


def _utc_bound(value: object, name: str) -> _datetime:
    if type(value) is not _datetime:
        raise _validation(f"{name} must be exact datetime")
    try:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError
        return value.astimezone(_timezone.utc)
    except (TypeError, ValueError, OverflowError) as error:
        raise _validation(f"{name} must be timezone-aware") from error


def _target(track: object, entry: object) -> tuple[str, str, str, _datetime]:
    if type(track) is not _Record or type(entry) is not _Record:
        raise _validation("target records must be exact HistoricalInputSourceRecord")
    if track.record_kind != "track" or track.organization != "JRA" or track.source_system != "jra_official" or track.external_entry_id is not None:
        raise _validation("target track record is invalid")
    if entry.record_kind != "entry" or entry.organization != "JRA" or entry.source_system != "jra_official" or entry.external_entry_id is None or entry.external_race_id != track.external_race_id:
        raise _validation("target entry record is invalid")
    try:
        race = _parse_race_id(track.external_race_id)
        horse = _parse_horse_id(entry.record_values["external_horse_id"])
        horse_no = entry.record_values["horse_no"]
        stored_entry_id = entry.record_values["external_entry_id"]
        scheduled = _utc_bound(track.record_values["scheduled_start_at"], "target scheduled_start_at")
        rebuilt = _build_entry_id(race_identity=race, horse_no=horse_no)
    except (_IdentityError, KeyError, TypeError, ValueError, OverflowError) as error:
        raise _validation("target lineage is invalid") from error
    if type(stored_entry_id) is not str or not _POSITIVE.fullmatch(str(horse_no)) or entry.external_entry_id != rebuilt or stored_entry_id != rebuilt:
        raise _validation("target entry identity is invalid")
    return race.external_race_id, rebuilt, horse.external_horse_id, scheduled


def resolve_jra_target_horse_history_response(
    *,
    target_track_record: _Record,
    target_entry_record: _Record,
    locator: _Locator,
    observed_at_not_after: _datetime,
    horse_history_response_provider: JRATargetHorseHistoryResponseProvider,
) -> _Response:
    """Resolve exactly one target-bound, explicitly cutoff-bounded accessU response."""

    race_id, entry_id, horse_id, scheduled = _target(target_track_record, target_entry_record)
    if type(locator) is not _Locator or (locator.external_race_id, locator.external_entry_id, locator.external_horse_id) != (race_id, entry_id, horse_id):
        raise _validation("target horse-history locator is not target-bound")
    bound = _utc_bound(observed_at_not_after, "observed_at_not_after")
    if bound > scheduled:
        raise _validation("observed_at_not_after is after target scheduled start")
    if not callable(horse_history_response_provider):
        raise _validation("horse_history_response_provider must be callable")
    response = horse_history_response_provider(locator=locator, observed_at_not_after=observed_at_not_after)
    if response is None:
        raise JRATargetHorseHistoryResolutionUnavailableError("no eligible JRA horse-history response")
    if type(response) is not _Response:
        raise _validation("horse-history provider response is invalid")
    try:
        canonical = _canonicalize_url(page_kind=_PageKind.HORSE_PROFILE_HISTORY, response_url=response.response_url)
        profile = _parse_profile_url(response.response_url)
    except (_CaptureError, _IdentityError) as error:
        raise _validation("horse-history provider response is not canonical accessU") from error
    if canonical != response.response_url or response.response_url != locator.canonical_horse_history_url or profile.external_horse_id != horse_id:
        raise _validation("horse-history provider response disagrees with target locator")
    if response.observed_at > bound:
        raise _validation("horse-history provider response is after explicit cutoff")
    return response


__all__ = (
    "JRATargetHorseHistoryResponseProvider",
    "JRATargetHorseHistoryResolutionError",
    "JRATargetHorseHistoryResolutionValidationError",
    "JRATargetHorseHistoryResolutionUnavailableError",
    "resolve_jra_target_horse_history_response",
)
