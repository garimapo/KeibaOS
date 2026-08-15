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
    if html.count(f'onclick="{onclick}"') != 1:
        raise _validation("official final-win-odds control source spelling is invalid")
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
