"""Pure discovery of an exact JRA accessD target-card locator from a race list."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass
from datetime import datetime as _datetime
import hashlib as _hashlib
import re as _re

from bs4 import BeautifulSoup as _BeautifulSoup
from bs4.element import Tag as _Tag

from scripts.simulation.jra_official_identity import (
    JRAOfficialIdentityValidationError as _IdentityValidationError,
    canonicalize_jra_race_card_href as _canonicalize_card_href,
    parse_jra_external_race_id as _parse_race_id,
    parse_jra_race_card_url_identity as _parse_card_url,
)
from scripts.simulation.jra_target_race_card_locator import (
    JRATargetRaceCardLocator as _Locator,
    JRATargetRaceCardLocatorValidationError as _LocatorValidationError,
    JRATargetRaceSelectionRequestLocator as _RequestLocator,
)


class JRATargetRaceCardDiscoveryError(ValueError):
    """Base error for pure race-selection target-card discovery."""


class JRATargetRaceCardDiscoveryValidationError(JRATargetRaceCardDiscoveryError):
    """Raised for malformed, ambiguous, or contradictory race-selection evidence."""


class JRATargetRaceCardDiscoveryUnavailableError(JRATargetRaceCardDiscoveryError):
    """Raised when valid race-selection evidence does not list the requested race."""


_SHA256 = _re.compile(r"[0-9a-f]{64}\Z")
_TABLE_SELECTOR = "#contentsBody > div.race_select > table#race_list.basic.mt20"


def _validation(message: str) -> JRATargetRaceCardDiscoveryValidationError:
    return JRATargetRaceCardDiscoveryValidationError(message)


def _aware(value: object, name: str) -> _datetime:
    if type(value) is not _datetime or value.tzinfo is None or value.utcoffset() is None:
        raise _validation(f"{name} must be an aware exact datetime")
    return value


def _one(nodes: object, name: str) -> _Tag:
    values = tuple(nodes)  # type: ignore[arg-type]
    if len(values) != 1 or not isinstance(values[0], _Tag):
        raise _validation(f"{name} must be unique")
    return values[0]


@_dataclass(frozen=True, slots=True)
class JRATargetRaceSelectionSuppliedOfficialResponse:
    """Exact CP932 response bytes for one race-selection POST request."""

    request_locator: _RequestLocator
    response_body: bytes
    charset: str
    observed_at: _datetime

    def __post_init__(self) -> None:
        if type(self.request_locator) is not _RequestLocator:
            raise _validation("request_locator is not an exact race-selection locator")
        if type(self.response_body) is not bytes or not self.response_body:
            raise _validation("response_body must be non-empty exact bytes")
        if type(self.charset) is not str or self.charset != "cp932":
            raise _validation("charset must be exact cp932")
        try:
            self.response_body.decode("cp932", errors="strict")
        except UnicodeDecodeError as error:
            raise _validation("response_body is not strict cp932") from error
        _aware(self.observed_at, "observed_at")


@_dataclass(frozen=True, slots=True)
class JRATargetRaceCardDiscovery:
    """Exact lexical accessD locator plus its race-selection response provenance."""

    locator: _Locator
    navigation_request_locator: _RequestLocator
    navigation_response_sha256: str
    navigation_observed_at: _datetime

    def __post_init__(self) -> None:
        if type(self.locator) is not _Locator or type(self.navigation_request_locator) is not _RequestLocator:
            raise _validation("target-card discovery domain types are invalid")
        if type(self.navigation_response_sha256) is not str or _SHA256.fullmatch(self.navigation_response_sha256) is None:
            raise _validation("navigation_response_sha256 is invalid")
        _aware(self.navigation_observed_at, "navigation_observed_at")
        try:
            race = _parse_race_id(self.locator.external_race_id)
        except _IdentityValidationError as error:
            raise _validation("target-card discovery race identity is invalid") from error
        request = self.navigation_request_locator
        if (race.year, race.venue_code, race.meeting_number, race.meeting_day) != (
            request.year,
            request.venue_code,
            request.meeting_number,
            request.meeting_day,
        ):
            raise _validation("target-card locator disagrees with navigation request identity")


def _document(response: JRATargetRaceSelectionSuppliedOfficialResponse) -> _BeautifulSoup:
    return _BeautifulSoup(response.response_body.decode("cp932", errors="strict"), "html.parser")


def _canonical_href(node: _Tag, name: str) -> tuple[str, object]:
    href = node.get("href")
    if type(href) is not str:
        raise _validation(f"{name} href is invalid")
    try:
        canonical = _canonicalize_card_href(href)
        return canonical, _parse_card_url(canonical)
    except (_IdentityValidationError, TypeError, ValueError) as error:
        raise _validation(f"{name} href is invalid") from error


def discover_jra_target_race_card_locator(
    *,
    external_race_id: str,
    navigation_response: JRATargetRaceSelectionSuppliedOfficialResponse,
) -> JRATargetRaceCardDiscovery:
    """Select exactly one direct accessD target-card URL from one supplied race list."""

    try:
        requested = _parse_race_id(external_race_id)
    except _IdentityValidationError as error:
        raise _validation("external_race_id is invalid") from error
    if type(navigation_response) is not JRATargetRaceSelectionSuppliedOfficialResponse:
        raise _validation("navigation_response is not an exact supplied race-selection response")
    request = navigation_response.request_locator
    if (requested.year, requested.venue_code, requested.meeting_number, requested.meeting_day) != (
        request.year,
        request.venue_code,
        request.meeting_number,
        request.meeting_day,
    ):
        raise _validation("requested target race disagrees with navigation request identity")
    soup = _document(navigation_response)
    table = _one(soup.select(_TABLE_SELECTOR), "official race-selection table")
    tbody = _one(table.find_all("tbody", recursive=False), "official race-selection table body")
    rows = tuple(tbody.find_all("tr", recursive=False))
    if not rows:
        raise _validation("official race-selection table has no rows")
    matches: list[str] = []
    for row in rows:
        if not isinstance(row, _Tag):
            raise _validation("official race-selection row is invalid")
        race_anchor = _one(row.select("th.race_num > a[href]"), "official race-number anchor")
        card_anchor = _one(
            row.select("td.syutsuba > a.btn-def.btn-sm.btn-narrow[href]"),
            "official target-card anchor",
        )
        race_url, race_identity = _canonical_href(race_anchor, "official race-number")
        card_url, card_identity = _canonical_href(card_anchor, "official target-card")
        if race_url != card_url or race_identity != card_identity:
            raise _validation("same-row official target-card anchors disagree")
        if (race_identity.year, race_identity.venue_code, race_identity.meeting_number, race_identity.meeting_day) != (
            request.year,
            request.venue_code,
            request.meeting_number,
            request.meeting_day,
        ):
            raise _validation("official target-card URL disagrees with navigation request identity")
        if race_identity == requested:
            matches.append(race_url)
    if not matches:
        raise JRATargetRaceCardDiscoveryUnavailableError("requested target race is absent from official race selection")
    if len(matches) != 1:
        raise _validation("official race selection has duplicate target race rows")
    try:
        locator = _Locator(external_race_id, matches[0])
    except _LocatorValidationError as error:
        raise _validation("official target-card locator is invalid") from error
    return JRATargetRaceCardDiscovery(
        locator,
        request,
        _hashlib.sha256(navigation_response.response_body).hexdigest(),
        navigation_response.observed_at,
    )


__all__ = (
    "JRATargetRaceSelectionSuppliedOfficialResponse",
    "JRATargetRaceCardDiscovery",
    "JRATargetRaceCardDiscoveryError",
    "JRATargetRaceCardDiscoveryValidationError",
    "JRATargetRaceCardDiscoveryUnavailableError",
    "discover_jra_target_race_card_locator",
)
