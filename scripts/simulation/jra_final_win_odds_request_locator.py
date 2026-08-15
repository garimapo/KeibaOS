"""Pure extraction of JRA accessO final-win-odds navigation from accessS evidence."""

from __future__ import annotations

import re as _re
from unicodedata import normalize as _normalize

from bs4 import BeautifulSoup as _BeautifulSoup
from bs4.element import Tag as _Tag

from scripts.simulation.jra_official_identity import (
    JRAOfficialFinalWinOddsRequestLocator as _JRAOfficialFinalWinOddsRequestLocator,
    JRAOfficialIdentityValidationError as _JRAOfficialIdentityValidationError,
    build_jra_final_win_odds_request_locator as _build_jra_final_win_odds_request_locator,
    parse_jra_result_url_identity as _parse_jra_result_url_identity,
)
from scripts.simulation.jra_official_response_capture import (
    JRASuppliedOfficialResponse as _JRASuppliedOfficialResponse,
)


class JRAFinalWinOddsRequestLocatorExtractionError(ValueError):
    """Base error for pure final-win-odds locator extraction."""


class JRAFinalWinOddsRequestLocatorExtractionValidationError(
    JRAFinalWinOddsRequestLocatorExtractionError
):
    """Raised for malformed or contradictory supplied JRA result evidence."""


_RESULT_TABLE_SELECTOR = "div#race_result.mt20 > div.race_result_unit > table.basic.narrow-xy.striped"
_CONTROL_SELECTOR = (
    ":scope > caption > div.race_header > div.right > div.race_related_link > ul > li "
    "> a.btn-def.btn-sm.blue.btn-block"
)
_ONCLICK = _re.compile(
    r"return[ \t\r\n]+doAction[ \t\r\n]*\([ \t\r\n]*'/JRADB/accessO\.html'"
    r"[ \t\r\n]*,[ \t\r\n]*'(?P<cname>[^'\\\s]+)'[ \t\r\n]*\)[ \t\r\n]*;[ \t\r\n]*\Z"
)
_TAG_NAME = _re.compile(r"<[ \t\r\n]*([A-Za-z][A-Za-z0-9:_-]*)")
_ATTRIBUTE_NAME = _re.compile(r"[A-Za-z_:][A-Za-z0-9:_.-]*")
_ASCII_WHITESPACE = " \t\r\n\f"


def _validation(message: str) -> JRAFinalWinOddsRequestLocatorExtractionValidationError:
    return JRAFinalWinOddsRequestLocatorExtractionValidationError(message)


def _one(nodes: object, name: str) -> _Tag:
    values = tuple(nodes)  # type: ignore[arg-type]
    if len(values) != 1 or not isinstance(values[0], _Tag):
        raise _validation(f"{name} must be unique")
    return values[0]


def _display(value: object) -> str:
    if type(value) is not str:
        raise _validation("official display value is invalid")
    return " ".join(_normalize("NFC", value).split())


def _document(response: _JRASuppliedOfficialResponse) -> tuple[str, _BeautifulSoup]:
    if type(response.charset) is not str or response.charset != "cp932":
        raise _validation("race_result_response charset is invalid")
    body = response.response_body
    if type(body) is not bytes:
        raise _validation("race_result_response body is invalid")
    try:
        html = body.decode("cp932", errors="strict")
    except UnicodeDecodeError as error:
        raise _validation("race_result_response is not strict cp932") from error
    return html, _BeautifulSoup(html, "html.parser")


def _raw_tag_end(html: str, start: int) -> int:
    quote: str | None = None
    for index in range(start + 1, len(html)):
        character = html[index]
        if quote is not None:
            if character == quote:
                quote = None
        elif character in {"'", '"'}:
            quote = character
        elif character == ">":
            return index
    raise _validation("official HTML tag is malformed")


def _raw_anchor_start_tags(html: str) -> tuple[str, ...]:
    anchors: list[str] = []
    index = 0
    lower_html = html.lower()
    while index < len(html):
        opening = html.find("<", index)
        if opening < 0:
            break
        if html.startswith("<!--", opening):
            closing = html.find("-->", opening + 4)
            if closing < 0:
                raise _validation("official HTML comment is malformed")
            index = closing + 3
            continue
        ending = _raw_tag_end(html, opening)
        tag = html[opening : ending + 1]
        match = _TAG_NAME.match(tag)
        if match is None:
            index = ending + 1
            continue
        name = match.group(1).lower()
        if name == "script":
            closing = lower_html.find("</script", ending + 1)
            if closing < 0:
                raise _validation("official script element is malformed")
            index = _raw_tag_end(html, closing) + 1
            continue
        if name == "a":
            anchors.append(tag)
        index = ending + 1
    return tuple(anchors)


def _raw_attribute_values(raw_tag: str, expected_name: str) -> tuple[str, ...]:
    match = _TAG_NAME.match(raw_tag)
    if match is None:
        raise _validation("official anchor source is malformed")
    index = match.end()
    values: list[str] = []
    while index < len(raw_tag):
        while index < len(raw_tag) and raw_tag[index] in _ASCII_WHITESPACE:
            index += 1
        if index >= len(raw_tag) or raw_tag[index] in "/>":
            break
        attribute = _ATTRIBUTE_NAME.match(raw_tag, index)
        if attribute is None:
            raise _validation("official anchor source is malformed")
        name = attribute.group(0)
        index = attribute.end()
        while index < len(raw_tag) and raw_tag[index] in _ASCII_WHITESPACE:
            index += 1
        if index >= len(raw_tag) or raw_tag[index] != "=":
            raise _validation("official anchor source is malformed")
        index += 1
        while index < len(raw_tag) and raw_tag[index] in _ASCII_WHITESPACE:
            index += 1
        if index >= len(raw_tag) or raw_tag[index] != '"':
            raise _validation("official anchor source is malformed")
        value_start = index + 1
        value_end = raw_tag.find('"', value_start)
        if value_end < 0:
            raise _validation("official anchor source is malformed")
        if name == expected_name:
            values.append(raw_tag[value_start:value_end])
        index = value_end + 1
    return tuple(values)


def _raw_onclick_for_candidate(html: str, soup: _BeautifulSoup, candidate: _Tag, onclick: str) -> None:
    parsed_anchors = tuple(soup.find_all("a"))
    raw_anchors = _raw_anchor_start_tags(html)
    if len(parsed_anchors) != len(raw_anchors):
        raise _validation("official anchor source disagrees with parsed HTML")
    candidate_index = next((index for index, anchor in enumerate(parsed_anchors) if anchor is candidate), None)
    if candidate_index is None:
        raise _validation("official final-win-odds control source is missing")
    if _raw_attribute_values(raw_anchors[candidate_index], "onclick") != (onclick,):
        raise _validation("official final-win-odds control source spelling is invalid")


def _control(soup: _BeautifulSoup, html: str) -> str:
    table = _one(soup.select(_RESULT_TABLE_SELECTOR), "official accessS result table")
    candidate = _one(table.select(_CONTROL_SELECTOR), "official final-win-odds control")
    if _display(candidate.get_text(" ", strip=True)) != "オッズ":
        raise _validation("official final-win-odds control label is invalid")
    if candidate.get("href") != "#":
        raise _validation("official final-win-odds control href is invalid")
    onclick = candidate.get("onclick")
    if type(onclick) is not str:
        raise _validation("official final-win-odds control onclick is invalid")
    match = _ONCLICK.fullmatch(onclick)
    if match is None:
        raise _validation("official final-win-odds control onclick is invalid")
    _raw_onclick_for_candidate(html, soup, candidate, onclick)
    return match.group("cname")


def extract_jra_final_win_odds_request_locator(
    *, race_result_response: _JRASuppliedOfficialResponse
) -> _JRAOfficialFinalWinOddsRequestLocator:
    """Extract one formally validated accessO request locator from supplied accessS bytes."""

    if type(race_result_response) is not _JRASuppliedOfficialResponse:
        raise _validation("race_result_response must be exact JRASuppliedOfficialResponse")
    try:
        race_identity = _parse_jra_result_url_identity(race_result_response.response_url)
    except _JRAOfficialIdentityValidationError as error:
        raise _validation("race_result_response URL is not a valid accessS result URL") from error
    html, soup = _document(race_result_response)
    cname = _control(soup, html)
    try:
        locator = _build_jra_final_win_odds_request_locator(cname=cname)
    except _JRAOfficialIdentityValidationError as error:
        raise _validation("official final-win-odds CNAME is invalid") from error
    if locator.external_race_identity != race_identity:
        raise _validation("official accessS/accessO race identities disagree")
    return locator


if "annotations" in globals():
    del annotations
