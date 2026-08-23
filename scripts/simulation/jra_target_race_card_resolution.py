"""Pure causal resolution of retained JRA accessD target-card evidence."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass, field as _field
from datetime import datetime as _datetime, timezone as _timezone
import re as _re
from typing import Protocol as _Protocol

from scripts.simulation.jra_official_identity import (
    JRAOfficialIdentityValidationError as _IdentityError,
    parse_jra_external_race_id as _parse_race_id,
    parse_jra_race_card_url_identity as _parse_card_url,
)
from scripts.simulation.jra_official_response_capture import (
    JRAOfficialTargetRaceCardResponseCapture as _TargetCapture,
    JRASuppliedOfficialResponse as _Supplied,
    JRATargetRaceSelectionResponseCapture as _SelectionCapture,
)
from scripts.simulation.jra_target_race_card_discovery import (
    JRATargetRaceCardDiscovery as _Discovery,
    JRATargetRaceCardDiscoveryError as _DiscoveryError,
    discover_jra_target_race_card_locator as _discover,
)
from scripts.simulation.jra_target_race_card_locator import JRATargetRaceCardLocator as _Locator


class JRATargetRaceCardResolutionError(ValueError):
    """Base error for causal JRA target-card response resolution."""


class JRATargetRaceCardResolutionValidationError(JRATargetRaceCardResolutionError):
    """Raised when target, provenance, bound, or supplied capture evidence is invalid."""


class JRATargetRaceCardResolutionUnavailableError(JRATargetRaceCardResolutionError):
    """Raised when exact causally eligible archived evidence is unavailable."""


class JRATargetRaceSelectionCaptureProvider(_Protocol):
    def __call__(
        self,
        *,
        capture_id: str,
    ) -> _SelectionCapture | None: ...


class JRATargetRaceCardCaptureProvider(_Protocol):
    def __call__(
        self,
        *,
        locator: _Locator,
        observed_at_not_after: _datetime,
    ) -> _TargetCapture | None: ...


_V4_CAPTURE_ID = _re.compile(r"jra-capture-v4:[0-9a-f]{64}\Z")


def _validation(message: str) -> JRATargetRaceCardResolutionValidationError:
    return JRATargetRaceCardResolutionValidationError(message)


def _utc(value: object, name: str) -> _datetime:
    if type(value) is not _datetime:
        raise _validation(f"{name} must be exact datetime")
    try:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError
        return value.astimezone(_timezone.utc)
    except (TypeError, ValueError, OverflowError) as error:
        raise _validation(f"{name} must be timezone-aware") from error


def _caller_inputs(
    *,
    external_race_id: object,
    target_race_selection_capture_id: object,
    captured_at: object,
    target_race_selection_capture_provider: object,
    target_race_card_capture_provider: object,
) -> tuple[str, _datetime]:
    try:
        race = _parse_race_id(external_race_id)
    except _IdentityError as error:
        raise _validation("external_race_id is invalid") from error
    if (
        type(target_race_selection_capture_id) is not str
        or _V4_CAPTURE_ID.fullmatch(target_race_selection_capture_id) is None
    ):
        raise _validation("target_race_selection_capture_id is invalid")
    bound = _utc(captured_at, "captured_at")
    if not callable(target_race_selection_capture_provider):
        raise _validation("target_race_selection_capture_provider must be callable")
    if not callable(target_race_card_capture_provider):
        raise _validation("target_race_card_capture_provider must be callable")
    return race.external_race_id, bound


@_dataclass(frozen=True, slots=True, init=False)
class JRATargetRaceCardResolution:
    """One target-card supplied response bound to exact retained archive provenance."""

    response: _Supplied = _field(init=False)
    discovery: _Discovery = _field(init=False)
    target_race_selection_capture_id: str = _field(init=False)
    target_race_card_capture_id: str = _field(init=False)
    target_race_card_response_sha256: str = _field(init=False)
    captured_at: _datetime = _field(init=False)

    def __init__(
        self,
        *,
        discovery: _Discovery,
        target_race_selection_capture: _SelectionCapture,
        target_race_card_capture: _TargetCapture,
        captured_at: _datetime,
    ) -> None:
        if type(discovery) is not _Discovery:
            raise _validation("discovery must be exact JRATargetRaceCardDiscovery")
        if type(target_race_selection_capture) is not _SelectionCapture:
            raise _validation("target_race_selection_capture is invalid")
        if type(target_race_card_capture) is not _TargetCapture:
            raise _validation("target_race_card_capture is invalid")
        bound = _utc(captured_at, "captured_at")
        selection = target_race_selection_capture
        card = target_race_card_capture
        if (
            selection.request_locator != discovery.navigation_request_locator
            or selection.response_sha256 != discovery.navigation_response_sha256
            or selection.observed_at != discovery.navigation_observed_at
        ):
            raise _validation("target race-selection capture disagrees with discovery provenance")
        if selection.observed_at > bound:
            raise _validation("target race-selection capture is after captured_at")
        if card.canonical_source_url != discovery.locator.canonical_target_race_card_url:
            raise _validation("target-card capture URL disagrees with discovery locator")
        try:
            if _parse_card_url(card.canonical_source_url) != _parse_race_id(discovery.locator.external_race_id):
                raise ValueError
        except (_IdentityError, TypeError, ValueError) as error:
            raise _validation("target-card capture race identity disagrees with discovery") from error
        if card.observed_at > bound:
            raise _validation("target-card capture is after captured_at")
        response = card.to_supplied_official_response()
        if type(response) is not _Supplied:
            raise _validation("target-card supplied response is invalid")
        object.__setattr__(self, "response", response)
        object.__setattr__(self, "discovery", discovery)
        object.__setattr__(self, "target_race_selection_capture_id", selection.capture_id)
        object.__setattr__(self, "target_race_card_capture_id", card.capture_id)
        object.__setattr__(self, "target_race_card_response_sha256", card.response_sha256)
        object.__setattr__(self, "captured_at", captured_at)


def resolve_jra_target_race_card_response(
    *,
    external_race_id: str,
    target_race_selection_capture_id: str,
    captured_at: _datetime,
    target_race_selection_capture_provider: JRATargetRaceSelectionCaptureProvider,
    target_race_card_capture_provider: JRATargetRaceCardCaptureProvider,
) -> JRATargetRaceCardResolution:
    """Resolve exact retained v4 navigation and v3 target-card evidence without fallback."""

    race_id, bound = _caller_inputs(
        external_race_id=external_race_id,
        target_race_selection_capture_id=target_race_selection_capture_id,
        captured_at=captured_at,
        target_race_selection_capture_provider=target_race_selection_capture_provider,
        target_race_card_capture_provider=target_race_card_capture_provider,
    )
    selection = target_race_selection_capture_provider(capture_id=target_race_selection_capture_id)
    if selection is None:
        raise JRATargetRaceCardResolutionUnavailableError("exact target race-selection capture is unavailable")
    if type(selection) is not _SelectionCapture:
        raise _validation("target race-selection provider response is invalid")
    if selection.capture_id != target_race_selection_capture_id:
        raise _validation("target race-selection provider response has a different capture ID")
    if selection.observed_at > bound:
        raise _validation("target race-selection capture is after captured_at")
    try:
        discovery = _discover(
            external_race_id=race_id,
            navigation_response=selection.to_supplied_official_response(),
        )
    except _DiscoveryError as error:
        raise _validation("exact target race-selection capture does not prove the requested target card") from error
    card = target_race_card_capture_provider(
        locator=discovery.locator,
        observed_at_not_after=captured_at,
    )
    if card is None:
        raise JRATargetRaceCardResolutionUnavailableError("causally eligible target-card capture is unavailable")
    if type(card) is not _TargetCapture:
        raise _validation("target-card provider response is invalid")
    if card.canonical_source_url != discovery.locator.canonical_target_race_card_url:
        raise _validation("target-card provider response disagrees with discovered URL")
    if card.observed_at > bound:
        raise _validation("target-card capture is after captured_at")
    return JRATargetRaceCardResolution(
        discovery=discovery,
        target_race_selection_capture=selection,
        target_race_card_capture=card,
        captured_at=captured_at,
    )


__all__ = (
    "JRATargetRaceSelectionCaptureProvider",
    "JRATargetRaceCardCaptureProvider",
    "JRATargetRaceCardResolutionError",
    "JRATargetRaceCardResolutionValidationError",
    "JRATargetRaceCardResolutionUnavailableError",
    "JRATargetRaceCardResolution",
    "resolve_jra_target_race_card_response",
)
