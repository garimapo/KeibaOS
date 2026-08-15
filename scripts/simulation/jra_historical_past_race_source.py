"""Pure normalization of one trusted JRA result/final-odds evidence pair."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass
from datetime import date as _date
from decimal import Decimal as _Decimal, InvalidOperation as _InvalidOperation
import hashlib as _hashlib
import re as _re
from unicodedata import normalize as _normalize
from urllib.parse import urljoin as _urljoin, urlsplit as _urlsplit

from bs4 import BeautifulSoup as _BeautifulSoup
from bs4.element import Tag as _Tag

from scripts.simulation.historical_input_evidence import (
    HistoricalInputEvidenceReference as _HistoricalInputEvidenceReference,
)
from scripts.simulation.historical_input_source_records import (
    HistoricalInputSourceRecord as _HistoricalInputSourceRecord,
)
from scripts.simulation.jra_official_identity import (
    JRAExternalHorseIdentity as _JRAExternalHorseIdentity,
    JRAExternalRaceIdentity as _JRAExternalRaceIdentity,
    JRAOfficialIdentityValidationError as _JRAOfficialIdentityValidationError,
    build_jra_external_entry_id as _build_jra_external_entry_id,
    build_jra_provider_record_id as _build_jra_provider_record_id,
    parse_jra_external_horse_id as _parse_jra_external_horse_id,
    parse_jra_external_race_id as _parse_jra_external_race_id,
    parse_jra_horse_profile_url_identity as _parse_jra_horse_profile_url_identity,
    parse_jra_result_url_identity as _parse_jra_result_url_identity,
)
from scripts.simulation.jra_official_response_capture import (
    JRAFinalWinOddsSuppliedOfficialResponse as _JRAFinalWinOddsSuppliedOfficialResponse,
    JRAOfficialPageKind as _JRAOfficialPageKind,
    JRASuppliedOfficialResponse as _JRASuppliedOfficialResponse,
)


class JRAHistoricalPastRaceSourceError(ValueError):
    """Base error for the pure JRA historical past-race normalizer."""


class JRAHistoricalPastRaceSourceValidationError(JRAHistoricalPastRaceSourceError):
    """Raised for malformed or contradictory supplied JRA evidence."""


class JRAHistoricalPastRaceSourceUnsupportedError(JRAHistoricalPastRaceSourceError):
    """Raised for a recognized official state outside the initial support envelope."""


_VENUES = {
    "01": "札幌",
    "02": "函館",
    "03": "福島",
    "04": "新潟",
    "05": "東京",
    "06": "中山",
    "07": "中京",
    "08": "京都",
    "09": "阪神",
    "10": "小倉",
}
_CNAME_DATE = _re.compile(r"(?P<date>[0-9]{8})/[0-9A-F]{2}\Z")
_DATE_LINE = _re.compile(
    r"(?P<year>[0-9]{4})年(?P<month>[0-9]{1,2})月(?P<day>[0-9]{1,2})日(?:\([^)]*\)|（[^）]*）)?\s*"
    r"(?P<meeting>[0-9]{1,2})回(?P<venue>札幌|函館|福島|新潟|東京|中山|中京|京都|阪神|小倉)(?P<meeting_day>[0-9]{1,2})日\Z"
)
_RACE_NUMBER = _re.compile(r"(?P<race>[0-9]{1,2})R")
_POSITIVE = _re.compile(r"[1-9][0-9]*\Z")
_TIME = _re.compile(r"[0-9]{1,2}:[0-5][0-9]\.[0-9]\Z")
_WEIGHT = _re.compile(r"(?P<weight>[0-9]+)\s*\((?P<change>[+-]?[0-9]+)\)\Z")
_ODDS = _re.compile(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?\Z")
_DISTANCE = _re.compile(r"(?P<distance>[1-9][0-9,]*)\s*メートル")
_CORNER = _re.compile(r"(?P<corner>[1-4１-４])コーナー通過順位\Z")
_CORNER_ORDINAL = {"1": 1, "2": 2, "3": 3, "4": 4, "１": 1, "２": 2, "３": 3, "４": 4}
_RESULT_HEADINGS = frozenset(
    {"着順", "枠", "馬番", "馬名", "性齢", "負担重量", "騎手名", "タイム", "着差", "コーナー通過順位", "馬体重（増減）", "調教師名", "単勝人気"}
)


@_dataclass(frozen=True, slots=True)
class _Header:
    race_date: _date
    place: str
    race_name: str


def _validation(message: str) -> JRAHistoricalPastRaceSourceValidationError:
    return JRAHistoricalPastRaceSourceValidationError(message)


def _unsupported(message: str) -> JRAHistoricalPastRaceSourceUnsupportedError:
    return JRAHistoricalPastRaceSourceUnsupportedError(message)


def _one(nodes: object, name: str) -> _Tag:
    values = tuple(nodes)  # type: ignore[arg-type]
    if len(values) != 1 or not isinstance(values[0], _Tag):
        raise _validation(f"{name} must be unique")
    return values[0]


def _display(value: object) -> str:
    if type(value) is not str:
        raise _validation("official display value is invalid")
    return " ".join(_normalize("NFC", value).split())


def _text(node: _Tag, name: str, *, unsupported: bool = False) -> str:
    value = _display(node.get_text(" ", strip=True))
    if value:
        return value
    if unsupported:
        raise _unsupported(f"{name} is unsupported")
    raise _validation(f"{name} is missing")


def _cell(row: _Tag, selector: str, name: str) -> _Tag:
    return _one(row.select(selector), name)


def _positive(value: str, name: str, *, unsupported: bool = False) -> int:
    if _POSITIVE.fullmatch(value) is not None:
        return int(value)
    if unsupported:
        raise _unsupported(f"{name} is unsupported")
    raise _validation(f"{name} is invalid")


def _decimal(value: str, name: str) -> _Decimal:
    if _ODDS.fullmatch(value) is None:
        raise _unsupported(f"{name} is unsupported")
    try:
        result = _Decimal(value)
    except _InvalidOperation as error:
        raise _unsupported(f"{name} is unsupported") from error
    if not result.is_finite() or result <= 0:
        raise _unsupported(f"{name} is unsupported")
    return result


def _document(response: object, name: str) -> _BeautifulSoup:
    try:
        html = response.response_body.decode("cp932", errors="strict")
    except UnicodeDecodeError as error:
        raise _validation(f"{name} is not strict cp932") from error
    return _BeautifulSoup(html, "html.parser")


def _historical_date(response_url: str, identity: _JRAExternalRaceIdentity) -> _date:
    try:
        raw_cname = _urlsplit(response_url).query.split("=", 1)[1].replace("%2F", "/")
    except (AttributeError, IndexError) as error:
        raise _validation("accessS CNAME is invalid") from error
    match = _CNAME_DATE.search(raw_cname)
    if match is None:
        raise _validation("accessS CNAME calendar date is invalid")
    value = match.group("date")
    try:
        result = _date(int(value[:4]), int(value[4:6]), int(value[6:8]))
    except ValueError as error:
        raise _validation("accessS CNAME calendar date is invalid") from error
    if str(result.year) != identity.year:
        raise _validation("accessS CNAME calendar date disagrees with race identity")
    return result


def _header(
    soup: _BeautifulSoup,
    *,
    selector: str,
    identity: _JRAExternalRaceIdentity,
    expected_date: _date,
    access_s: bool,
) -> _Header:
    header = _one(soup.select(selector), "official JRA race header")
    date_node = _one(header.select(".cell.date"), "official JRA race date")
    date_match = _DATE_LINE.fullmatch(_text(date_node, "official JRA race date"))
    if date_match is None:
        raise _validation("official JRA race date is invalid")
    try:
        visible_date = _date(
            int(date_match.group("year")), int(date_match.group("month")), int(date_match.group("day"))
        )
    except ValueError as error:
        raise _validation("official JRA race date is invalid") from error
    if (
        visible_date != expected_date
        or date_match.group("venue") != _VENUES[identity.venue_code]
        or int(date_match.group("meeting")) != int(identity.meeting_number)
        or int(date_match.group("meeting_day")) != int(identity.meeting_day)
    ):
        raise _validation("official JRA visible race identity disagrees")
    race_node = _one(
        header.select(".race_number img[alt]") if access_s else header.select(".race_number"),
        "official JRA race number",
    )
    race_text = race_node.get("alt") if access_s else race_node.get_text(" ", strip=True)
    race_match = _RACE_NUMBER.search(_display(race_text)) if type(race_text) is str else None
    if race_match is None or int(race_match.group("race")) != int(identity.race_number):
        raise _validation("official JRA race number disagrees")
    return _Header(
        race_date=visible_date,
        place=date_match.group("venue"),
        race_name=_text(_one(header.select(".race_name"), "official JRA race heading"), "official JRA race heading", unsupported=True),
    )


def _target_identity(
    target_track_record: _HistoricalInputSourceRecord,
    target_entry_record: _HistoricalInputSourceRecord,
) -> tuple[_JRAExternalRaceIdentity, _date, _JRAExternalHorseIdentity]:
    if type(target_track_record) is not _HistoricalInputSourceRecord or type(target_entry_record) is not _HistoricalInputSourceRecord:
        raise _validation("target records must be exact HistoricalInputSourceRecord")
    if (
        target_track_record.record_kind != "track"
        or target_track_record.organization != "JRA"
        or target_track_record.source_system != "jra_official"
        or target_track_record.external_entry_id is not None
    ):
        raise _validation("target track record is incompatible")
    if (
        target_entry_record.record_kind != "entry"
        or target_entry_record.organization != "JRA"
        or target_entry_record.source_system != "jra_official"
        or target_entry_record.external_entry_id is None
        or target_entry_record.external_race_id != target_track_record.external_race_id
    ):
        raise _validation("target entry record is incompatible")
    try:
        race_identity = _parse_jra_external_race_id(target_track_record.external_race_id)
        target_date = target_track_record.record_values["target_race_date"]
        horse_identity = _parse_jra_external_horse_id(target_entry_record.record_values["external_horse_id"])
        horse_no = target_entry_record.record_values["horse_no"]
        value_entry_id = target_entry_record.record_values["external_entry_id"]
    except (_JRAOfficialIdentityValidationError, KeyError) as error:
        raise _validation("target JRA identities are invalid") from error
    if type(target_date) is not _date or type(horse_no) is not int or horse_no <= 0 or type(value_entry_id) is not str:
        raise _validation("target record values are invalid")
    expected_entry_id = _build_jra_external_entry_id(race_identity=race_identity, horse_no=horse_no)
    if target_entry_record.external_entry_id != expected_entry_id or value_entry_id != expected_entry_id:
        raise _validation("target entry identity is incoherent")
    return race_identity, target_date, horse_identity


def _result_table(soup: _BeautifulSoup) -> _Tag:
    candidates: list[_Tag] = []
    for table in soup.select("#race_result table"):
        headings = {_display(item.get_text(" ", strip=True)) for item in table.select("thead th")}
        if _RESULT_HEADINGS.issubset(headings):
            candidates.append(table)
    return _one(candidates, "official JRA result table")


def _result_row(table: _Tag, response_url: str, horse_identity: _JRAExternalHorseIdentity) -> _Tag:
    matches: list[_Tag] = []
    rows = tuple(table.select("tbody > tr"))
    if not rows:
        raise _validation("official JRA result rows are missing")
    for row in rows:
        anchor = _one(row.select("td.horse a[href]"), "official JRA accessU horse anchor")
        href = anchor.get("href")
        if type(href) is not str or not href:
            raise _validation("official JRA accessU horse anchor is invalid")
        try:
            row_horse_identity = _parse_jra_horse_profile_url_identity(_urljoin(response_url, href))
        except _JRAOfficialIdentityValidationError as error:
            raise _validation("official JRA accessU horse anchor is invalid") from error
        if row_horse_identity == horse_identity:
            matches.append(row)
    return _one(matches, "target historical JRA horse row")


def _race_facts(header: _Tag) -> dict[str, object]:
    race_class = _text(_one(header.select(".type > .cell.class"), "official JRA race class"), "official JRA race class", unsupported=True)
    course = _text(_one(header.select(".type > .cell.course"), "official JRA race course"), "official JRA race course", unsupported=True)
    distance_match = _DISTANCE.search(course)
    if distance_match is None:
        raise _unsupported("official JRA race distance is unsupported")
    try:
        distance = int(distance_match.group("distance").replace(",", ""))
    except ValueError as error:
        raise _unsupported("official JRA race distance is unsupported") from error
    baba = _text(_one(header.select(".baba"), "official JRA track facts"), "official JRA track facts", unsupported=True)
    tracks = tuple(item for item in ("芝", "ダート") if item in baba)
    if len(tracks) != 1:
        raise _unsupported("official JRA track is unsupported")
    conditions = tuple(_text(item, "official JRA track condition", unsupported=True) for item in header.select(".baba li > .txt"))
    if len(conditions) != 1:
        raise _unsupported("official JRA track condition is unsupported")
    return {
        "race_class": race_class,
        "distance_m": distance,
        "track": tracks[0],
        "weather": _text(_one(header.select("li.weather .txt"), "official JRA weather"), "official JRA weather", unsupported=True),
        "track_condition": conditions[0],
    }


def _corner_values(row: _Tag) -> tuple[str, int]:
    nodes = tuple(row.select("td.corner li[title]"))
    if not nodes:
        raise _unsupported("official JRA corner order is unsupported")
    labels: list[int] = []
    values: list[int] = []
    for node in nodes:
        title = node.get("title")
        match = _CORNER.fullmatch(_display(title)) if type(title) is str else None
        value = _display(node.get_text(" ", strip=True))
        if match is None or _POSITIVE.fullmatch(value) is None:
            raise _unsupported("official JRA corner order is unsupported")
        labels.append(_CORNER_ORDINAL[match.group("corner")])
        values.append(int(value))
    if len(set(labels)) != len(labels) or labels != sorted(labels) or labels.count(4) != 1:
        raise _unsupported("official JRA corner order is unsupported")
    return "-".join(str(value) for value in values), values[labels.index(4)]


def _result_values(row: _Tag) -> tuple[int, dict[str, object]]:
    horse_no = _positive(_text(_cell(row, "td.num", "official JRA horse number"), "official JRA horse number"), "official JRA horse number")
    finish = _positive(_text(_cell(row, "td.place", "official JRA finish"), "official JRA finish", unsupported=True), "official JRA finish", unsupported=True)
    race_time = _text(_cell(row, "td.time", "official JRA race time"), "official JRA race time", unsupported=True)
    if _TIME.fullmatch(race_time) is None:
        raise _unsupported("official JRA race time is unsupported")
    weight_text = _text(_cell(row, "td.h_weight", "official JRA body weight"), "official JRA body weight", unsupported=True)
    weight_match = _WEIGHT.fullmatch(weight_text)
    if weight_match is None:
        raise _unsupported("official JRA body weight is unsupported")
    try:
        weight = _Decimal(weight_match.group("weight"))
        weight_diff = _Decimal(weight_match.group("change"))
    except _InvalidOperation as error:
        raise _unsupported("official JRA body weight is unsupported") from error
    passing_order, fourth_corner_position = _corner_values(row)
    return horse_no, {
        "finish": finish,
        "race_time": race_time,
        "weight": weight,
        "weight_diff": weight_diff,
        "jockey": _text(_cell(row, "td.jockey", "official JRA jockey"), "official JRA jockey", unsupported=True),
        "popularity": _positive(_text(_cell(row, "td.pop", "official JRA popularity"), "official JRA popularity", unsupported=True), "official JRA popularity", unsupported=True),
        "passing_order": passing_order,
        "fourth_corner_position": fourth_corner_position,
    }


def _odds(table: _Tag, horse_no: int) -> _Decimal:
    matches: list[_Tag] = []
    for row in table.select("tbody > tr"):
        number = _positive(_text(_cell(row, "td.num", "official JRA odds horse number"), "official JRA odds horse number"), "official JRA odds horse number")
        if number == horse_no:
            matches.append(row)
    row = _one(matches, "official JRA final-odds horse row")
    return _decimal(_text(_cell(row, "td.odds_tan", "official JRA final single-win odds"), "official JRA final single-win odds", unsupported=True), "official JRA final single-win odds")


def normalize_jra_historical_past_race_source_record(
    *,
    target_track_record: _HistoricalInputSourceRecord,
    target_entry_record: _HistoricalInputSourceRecord,
    race_result_response: _JRASuppliedOfficialResponse,
    final_win_odds_response: _JRAFinalWinOddsSuppliedOfficialResponse,
) -> _HistoricalInputSourceRecord:
    """Normalize one trusted accessS/accessO pair into one JRA past-race source record."""

    _, target_date, target_horse_identity = _target_identity(target_track_record, target_entry_record)
    if type(race_result_response) is not _JRASuppliedOfficialResponse:
        raise _validation("race_result_response must be exact JRASuppliedOfficialResponse")
    if type(final_win_odds_response) is not _JRAFinalWinOddsSuppliedOfficialResponse:
        raise _validation("final_win_odds_response must be exact JRAFinalWinOddsSuppliedOfficialResponse")
    try:
        historical_identity = _parse_jra_result_url_identity(race_result_response.response_url)
    except _JRAOfficialIdentityValidationError as error:
        raise _validation("race_result_response must be accessS race-result evidence") from error
    historical_date = _historical_date(race_result_response.response_url, historical_identity)
    if historical_date >= target_date:
        raise _validation("historical JRA race must precede target race")
    if final_win_odds_response.request_locator.external_race_identity != historical_identity:
        raise _validation("accessO final-odds race identity disagrees with accessS")
    result_sha256 = _hashlib.sha256(race_result_response.response_body).hexdigest()
    odds_sha256 = _hashlib.sha256(final_win_odds_response.response_body).hexdigest()
    result_soup = _document(race_result_response, "accessS result response")
    odds_soup = _document(final_win_odds_response, "accessO final-odds response")
    result_header = _header(result_soup, selector="#race_result .race_header", identity=historical_identity, expected_date=historical_date, access_s=True)
    odds_header = _header(odds_soup, selector=".race_header", identity=historical_identity, expected_date=historical_date, access_s=False)
    if result_header != odds_header:
        raise _validation("accessS and accessO visible race headings disagree")
    result_table = _result_table(result_soup)
    result_row = _result_row(result_table, race_result_response.response_url, target_horse_identity)
    historical_horse_no, result_values = _result_values(result_row)
    odds_table = _one(odds_soup.select("table.tanpuku"), "official JRA final-odds table")
    odds = _odds(odds_table, historical_horse_no)
    header_node = _one(result_soup.select("#race_result .race_header"), "official JRA race header")
    facts = _race_facts(header_node)
    evidence = (
        _HistoricalInputEvidenceReference("historical_race_context", race_result_response.response_url, result_sha256, None, race_result_response.observed_at),
        _HistoricalInputEvidenceReference("historical_race_final_odds", final_win_odds_response.request_locator.endpoint_url, odds_sha256, None, final_win_odds_response.observed_at, final_win_odds_response.request_locator.request_identity_sha256),
        _HistoricalInputEvidenceReference("historical_race_result", race_result_response.response_url, result_sha256, None, race_result_response.observed_at),
    )
    return _HistoricalInputSourceRecord(
        record_kind="past_race",
        organization="JRA",
        source_system="jra_official",
        external_race_id=target_entry_record.external_race_id,
        external_entry_id=target_entry_record.external_entry_id,
        provider_record_id=_build_jra_provider_record_id(race_identity=historical_identity, horse_identity=target_horse_identity),
        record_values={
            "race_date": result_header.race_date,
            "place": result_header.place,
            "race_name": result_header.race_name,
            "race_class": facts["race_class"],
            "distance_m": facts["distance_m"],
            "track": facts["track"],
            "weather": facts["weather"],
            "track_condition": facts["track_condition"],
            "finish": result_values["finish"],
            "race_time": result_values["race_time"],
            "weight": result_values["weight"],
            "weight_diff": result_values["weight_diff"],
            "jockey": result_values["jockey"],
            "popularity": result_values["popularity"],
            "odds": odds,
            "passing_order": result_values["passing_order"],
            "fourth_corner_position": result_values["fourth_corner_position"],
        },
        evidence=evidence,
    )


if "annotations" in globals():
    del annotations
