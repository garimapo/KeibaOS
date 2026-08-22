"""Pure supplied-navigation domains and lexical JRA target-card locators."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass
from datetime import date as _date, datetime as _datetime
import hashlib as _hashlib
import json as _json
import re as _re

from bs4 import BeautifulSoup as _BeautifulSoup
from bs4.element import Tag as _Tag

from scripts.simulation.jra_official_identity import (
    JRAOfficialIdentityValidationError as _IdentityValidationError,
    canonicalize_jra_race_card_href as _canonicalize_card_href,
    parse_jra_external_race_id as _parse_race_id,
    parse_jra_race_card_url_identity as _parse_card_url,
)


class JRATargetRaceCardLocatorError(ValueError):
    """Base error for pure JRA target-navigation locator work."""


class JRATargetRaceCardLocatorValidationError(JRATargetRaceCardLocatorError):
    """Raised when supplied official navigation material is malformed."""


class JRATargetRaceCardLocatorUnavailableError(JRATargetRaceCardLocatorError):
    """Raised when valid navigation has no requested official choice."""


_ROOT_URL = "https://www.jra.go.jp/"
_ACCESSD_ENDPOINT = "https://www.jra.go.jp/JRADB/accessD.html"
_MEETING_CNAME = _re.compile(r"pw01dli00/[0-9A-F]{2}\Z")
_RACE_CNAME = _re.compile(
    r"pw01drl00(?P<venue>(?:0[1-9]|10))(?P<year>[0-9]{4})"
    r"(?P<meeting>(?:0[1-9]|[1-9][0-9]))(?P<day>(?:0[1-9]|1[0-2]))"
    r"(?P<date>[0-9]{8})/(?P<tail>[0-9A-F]{2}\Z)"
)
_SHA256 = _re.compile(r"[0-9a-f]{64}\Z")
_ROOT_ONCLICK = _re.compile(
    r"doAction\('/JRADB/accessD\.html','(?P<cname>[^']+)'\);return false;\Z"
)
_MEETING_ONCLICK = _re.compile(
    r"return doAction\('/JRADB/accessD\.html', ?'(?P<cname>[^']+)'\);\Z"
)
_ROOT_SELECTOR = '#quick_menu a[href="#"][data-ga-click="quick_pc-1"]'
_MEETING_SELECTOR = '#contentsBody div.link_list.multi.div3.center > div.waku > a[href="#"][onclick]'


def _validation(message: str) -> JRATargetRaceCardLocatorValidationError:
    return JRATargetRaceCardLocatorValidationError(message)


def _strict_string(value: object, name: str) -> str:
    if type(value) is not str or not value:
        raise _validation(f"{name} must be a non-empty exact str")
    if any(character.isspace() or ord(character) < 32 or ord(character) == 127 for character in value):
        raise _validation(f"{name} contains whitespace or controls")
    return value


def _aware(value: object, name: str) -> _datetime:
    if type(value) is not _datetime or value.tzinfo is None or value.utcoffset() is None:
        raise _validation(f"{name} must be an aware exact datetime")
    return value


def _strict_cp932(value: object, name: str) -> bytes:
    if type(value) is not bytes or not value:
        raise _validation(f"{name} must be non-empty exact bytes")
    try:
        value.decode("cp932", errors="strict")
    except UnicodeDecodeError as error:
        raise _validation(f"{name} is not strict cp932") from error
    return value


def _fingerprint(cname: str) -> str:
    material = {
        "endpoint_url": _ACCESSD_ENDPOINT,
        "form": {"cname": cname},
        "method": "POST",
        "schema_version": 1,
    }
    return _hashlib.sha256(
        _json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


def _meeting_cname(value: object) -> str:
    cname = _strict_string(value, "cname")
    if "%" in cname or "+" in cname or _MEETING_CNAME.fullmatch(cname) is None:
        raise _validation("cname is outside the approved meeting-selection family")
    return cname


def _race_cname(value: object) -> dict[str, str]:
    cname = _strict_string(value, "cname")
    if "%" in cname or "+" in cname:
        raise _validation("cname must be raw race-selection request material")
    match = _RACE_CNAME.fullmatch(cname)
    if match is None:
        raise _validation("cname is outside the approved race-selection family")
    fields = match.groupdict()
    try:
        calendar = _date(int(fields["date"][:4]), int(fields["date"][4:6]), int(fields["date"][6:8]))
    except ValueError as error:
        raise _validation("race-selection CNAME calendar date is invalid") from error
    if fields["date"][:4] != fields["year"] or calendar.year != int(fields["year"]):
        raise _validation("race-selection CNAME calendar date disagrees with year")
    return fields


@_dataclass(frozen=True, slots=True)
class JRAOfficialTargetNavigationMenuSuppliedResponse:
    """Exact supplied bytes from the fixed public JRA navigation root."""

    response_body: bytes
    charset: str
    observed_at: _datetime

    def __post_init__(self) -> None:
        _strict_cp932(self.response_body, "response_body")
        if type(self.charset) is not str or self.charset != "cp932":
            raise _validation("charset must be exact cp932")
        _aware(self.observed_at, "observed_at")


@_dataclass(frozen=True, slots=True)
class JRATargetMeetingSelectionRequestLocator:
    """Exact official POST material for the accessD meeting-selection response."""

    endpoint_url: str
    cname: str
    request_identity_sha256: str

    def __post_init__(self) -> None:
        if type(self.endpoint_url) is not str or self.endpoint_url != _ACCESSD_ENDPOINT:
            raise _validation("endpoint_url is not the approved accessD endpoint")
        cname = _meeting_cname(self.cname)
        fingerprint = _fingerprint(cname)
        if type(self.request_identity_sha256) is not str or self.request_identity_sha256 != fingerprint:
            raise _validation("request_identity_sha256 disagrees with request material")


def build_jra_target_meeting_selection_request_locator(
    *, cname: str
) -> JRATargetMeetingSelectionRequestLocator:
    """Validate lexical official meeting-selection POST material."""

    canonical = _meeting_cname(cname)
    return JRATargetMeetingSelectionRequestLocator(_ACCESSD_ENDPOINT, canonical, _fingerprint(canonical))


@_dataclass(frozen=True, slots=True)
class JRATargetMeetingSelectionSuppliedOfficialResponse:
    """Exact supplied CP932 response for one meeting-selection POST request."""

    request_locator: JRATargetMeetingSelectionRequestLocator
    response_body: bytes
    charset: str
    observed_at: _datetime

    def __post_init__(self) -> None:
        if type(self.request_locator) is not JRATargetMeetingSelectionRequestLocator:
            raise _validation("request_locator is not an exact meeting-selection locator")
        _strict_cp932(self.response_body, "response_body")
        if type(self.charset) is not str or self.charset != "cp932":
            raise _validation("charset must be exact cp932")
        _aware(self.observed_at, "observed_at")


@_dataclass(frozen=True, slots=True)
class JRATargetRaceSelectionRequestLocator:
    """Exact official POST material for one date/venue/meeting/day race list."""

    endpoint_url: str
    cname: str
    year: str
    venue_code: str
    meeting_number: str
    meeting_day: str
    calendar_date: str
    request_identity_sha256: str

    def __post_init__(self) -> None:
        if type(self.endpoint_url) is not str or self.endpoint_url != _ACCESSD_ENDPOINT:
            raise _validation("endpoint_url is not the approved accessD endpoint")
        fields = _race_cname(self.cname)
        expected = (
            fields["year"], fields["venue"], fields["meeting"], fields["day"], fields["date"]
        )
        if (
            type(self.year) is not str
            or type(self.venue_code) is not str
            or type(self.meeting_number) is not str
            or type(self.meeting_day) is not str
            or type(self.calendar_date) is not str
            or (self.year, self.venue_code, self.meeting_number, self.meeting_day, self.calendar_date) != expected
        ):
            raise _validation("race-selection navigation identity disagrees with cname")
        fingerprint = _fingerprint(self.cname)
        if type(self.request_identity_sha256) is not str or self.request_identity_sha256 != fingerprint:
            raise _validation("request_identity_sha256 disagrees with request material")


def build_jra_target_race_selection_request_locator(*, cname: str) -> JRATargetRaceSelectionRequestLocator:
    """Validate lexical official race-selection POST material."""

    fields = _race_cname(cname)
    return JRATargetRaceSelectionRequestLocator(
        _ACCESSD_ENDPOINT,
        cname,
        fields["year"],
        fields["venue"],
        fields["meeting"],
        fields["day"],
        fields["date"],
        _fingerprint(cname),
    )


@_dataclass(frozen=True, slots=True)
class JRATargetRaceCardLocator:
    """One exact canonical accessD card URL bound to one JRA external race ID."""

    external_race_id: str
    canonical_target_race_card_url: str

    def __post_init__(self) -> None:
        try:
            race = _parse_race_id(self.external_race_id)
            card = _parse_card_url(self.canonical_target_race_card_url)
        except _IdentityValidationError as error:
            raise _validation("target race-card locator identity is invalid") from error
        if card != race:
            raise _validation("target race-card URL disagrees with external_race_id")


def _document(body: bytes) -> _BeautifulSoup:
    return _BeautifulSoup(body.decode("cp932", errors="strict"), "html.parser")


def _tag_end(html: str, start: int) -> int:
    quote: str | None = None
    for index in range(start, len(html)):
        character = html[index]
        if quote is not None:
            if character == quote:
                quote = None
        elif character in ("\"", "'"):
            quote = character
        elif character == ">":
            return index + 1
    raise _validation("official HTML start tag is unterminated")


def _raw_anchor_start_tags(html: str) -> tuple[str, ...]:
    """Return real anchor start tags in document order, excluding comments/scripts."""

    tags: list[str] = []
    index = 0
    lower = html.lower()
    while index < len(html):
        if html.startswith("<!--", index):
            end = html.find("-->", index + 4)
            if end < 0:
                raise _validation("official HTML comment is unterminated")
            index = end + 3
            continue
        if lower.startswith("<script", index) and (index + 7 == len(html) or not lower[index + 7].isalnum()):
            open_end = _tag_end(html, index)
            close = lower.find("</script", open_end)
            if close < 0:
                raise _validation("official HTML script is unterminated")
            index = _tag_end(html, close)
            continue
        if lower.startswith("<a", index) and (index + 2 == len(html) or not lower[index + 2].isalnum()):
            end = _tag_end(html, index)
            tags.append(html[index:end])
            index = end
            continue
        index += 1
    return tuple(tags)


def _raw_anchor_for(node: _Tag, soup: _BeautifulSoup, html: str) -> str:
    parsed = tuple(soup.select("a"))
    raw = _raw_anchor_start_tags(html)
    if len(parsed) != len(raw):
        raise _validation("parsed/raw anchor count disagrees")
    for index, parsed_node in enumerate(parsed):
        if parsed_node is node:
            return raw[index]
    raise _validation("selected official anchor is not in document order")


def _raw_onclick(tag: str) -> str:
    matches = tuple(_re.finditer(r'(?:^|\s)onclick="([^"]*)"', tag))
    if len(matches) != 1:
        raise _validation("official onclick attribute is invalid")
    return matches[0].group(1)


def discover_jra_target_meeting_selection_request_locator(
    *, navigation_menu_response: JRAOfficialTargetNavigationMenuSuppliedResponse
) -> JRATargetMeetingSelectionRequestLocator:
    """Extract the sole direct meeting-selection POST locator from root-menu bytes."""

    if type(navigation_menu_response) is not JRAOfficialTargetNavigationMenuSuppliedResponse:
        raise _validation("navigation_menu_response is not an exact root-menu response")
    html = navigation_menu_response.response_body.decode("cp932", errors="strict")
    soup = _document(navigation_menu_response.response_body)
    nodes = tuple(soup.select(_ROOT_SELECTOR))
    if len(nodes) != 1 or not isinstance(nodes[0], _Tag) or nodes[0].get("href") != "#":
        raise _validation("official root meeting-selection control must be unique")
    raw_onclick = _raw_onclick(_raw_anchor_for(nodes[0], soup, html))
    match = _ROOT_ONCLICK.fullmatch(raw_onclick)
    if match is None:
        raise _validation("official root meeting-selection onclick is invalid")
    return build_jra_target_meeting_selection_request_locator(cname=match.group("cname"))


def discover_jra_target_race_selection_request_locator(
    *,
    external_race_id: str,
    meeting_selection_response: JRATargetMeetingSelectionSuppliedOfficialResponse,
) -> JRATargetRaceSelectionRequestLocator:
    """Select one direct official race-selection POST request by meeting identity only."""

    try:
        requested = _parse_race_id(external_race_id)
    except _IdentityValidationError as error:
        raise _validation("external_race_id is invalid") from error
    if type(meeting_selection_response) is not JRATargetMeetingSelectionSuppliedOfficialResponse:
        raise _validation("meeting_selection_response is not an exact supplied response")
    html = meeting_selection_response.response_body.decode("cp932", errors="strict")
    soup = _document(meeting_selection_response.response_body)
    nodes = tuple(soup.select(_MEETING_SELECTOR))
    if not nodes or any(not isinstance(node, _Tag) or node.get("href") != "#" for node in nodes):
        raise _validation("official meeting-selection controls are invalid")
    choices: list[JRATargetRaceSelectionRequestLocator] = []
    for node in nodes:
        raw_onclick = _raw_onclick(_raw_anchor_for(node, soup, html))
        match = _MEETING_ONCLICK.fullmatch(raw_onclick)
        if match is None:
            raise _validation("official meeting-selection onclick is invalid")
        candidate = build_jra_target_race_selection_request_locator(cname=match.group("cname"))
        if (
            candidate.year,
            candidate.venue_code,
            candidate.meeting_number,
            candidate.meeting_day,
        ) == (
            requested.year,
            requested.venue_code,
            requested.meeting_number,
            requested.meeting_day,
        ):
            choices.append(candidate)
    distinct = {choice.cname: choice for choice in choices}
    if not distinct:
        raise JRATargetRaceCardLocatorUnavailableError("no official race-selection request matches target meeting")
    if len(distinct) != 1:
        raise _validation("official meeting-selection has distinct matching request locators")
    return next(iter(distinct.values()))


__all__ = (
    "JRAOfficialTargetNavigationMenuSuppliedResponse",
    "JRATargetMeetingSelectionRequestLocator",
    "JRATargetMeetingSelectionSuppliedOfficialResponse",
    "JRATargetRaceSelectionRequestLocator",
    "JRATargetRaceCardLocator",
    "JRATargetRaceCardLocatorError",
    "JRATargetRaceCardLocatorValidationError",
    "JRATargetRaceCardLocatorUnavailableError",
    "build_jra_target_meeting_selection_request_locator",
    "build_jra_target_race_selection_request_locator",
    "discover_jra_target_meeting_selection_request_locator",
    "discover_jra_target_race_selection_request_locator",
)
