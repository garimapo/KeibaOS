"""Pure normalization of one trusted JRA accessD target-race card."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass
from datetime import date as _date, datetime as _datetime, time as _time, timezone as _timezone
from decimal import Decimal as _Decimal, InvalidOperation as _InvalidOperation
import hashlib as _hashlib
import re as _re
from unicodedata import normalize as _normalize
from urllib.parse import urljoin as _urljoin, urlsplit as _urlsplit
from zoneinfo import ZoneInfo as _ZoneInfo

from bs4 import BeautifulSoup as _BeautifulSoup
from bs4.element import Tag as _Tag

from scripts.simulation.historical_input_evidence import HistoricalInputEvidenceReference as _Evidence
from scripts.simulation.historical_input_source_records import (
    HistoricalInputSourceConflictError as _SourceConflictError,
    HistoricalInputSourceError as _SourceError,
    HistoricalInputSourceRecord as _Record,
    validate_historical_input_source_record_set as _validate_record_set,
)
from scripts.simulation.jra_official_identity import (
    JRAOfficialIdentityValidationError as _IdentityError,
    build_jra_external_entry_id as _build_entry_id,
    parse_jra_external_horse_id as _parse_horse_id,
    parse_jra_external_race_id as _parse_race_id,
    parse_jra_horse_profile_url_identity as _parse_profile_url,
    parse_jra_race_card_url_identity as _parse_card_url,
)
from scripts.simulation.jra_official_response_capture import JRASuppliedOfficialResponse as _Response


class JRATargetRaceSourceError(ValueError):
    """Base error for the pure JRA accessD target-source boundary."""


class JRATargetRaceSourceValidationError(JRATargetRaceSourceError):
    """Raised for malformed, ambiguous, or contradictory official evidence."""


class JRATargetRaceSourceUnsupportedError(JRATargetRaceSourceError):
    """Raised for one unique direct value outside the normal-runner envelope."""


_VENUES = {"01": "札幌", "02": "函館", "03": "福島", "04": "新潟", "05": "東京", "06": "中山", "07": "中京", "08": "京都", "09": "阪神", "10": "小倉"}
_DATE_LINE = _re.compile(r"(?P<year>[0-9]{4})年(?P<month>[0-9]{1,2})月(?P<day>[0-9]{1,2})日(?:\([^)]*\)|（[^）]*）)?\s*(?P<meeting>[0-9]{1,2})回(?P<venue>札幌|函館|福島|新潟|東京|中山|中京|京都|阪神|小倉)(?P<day_no>[0-9]{1,2})日\Z")
_RACE = _re.compile(r"(?P<race>[0-9]{1,2})レース\Z")
_TIME = _re.compile(r"(?P<hour>[0-2][0-9])時(?P<minute>[0-5][0-9])分\Z")
_COURSE = _re.compile(r"コース：(?P<distance>[1-9][0-9,]*)メートル（(?P<surface>芝|ダート)・[^）]+）\Z")
_POSITIVE = _re.compile(r"[1-9][0-9]*\Z")
_DECIMAL = _re.compile(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?\Z")
_CNAME_DATE = _re.compile(r"(?P<date>[0-9]{8})/[0-9A-F]{2}\Z")
_TOKYO = _ZoneInfo("Asia/Tokyo")


def _validation(message: str) -> JRATargetRaceSourceValidationError:
    return JRATargetRaceSourceValidationError(message)


def _unsupported(message: str) -> JRATargetRaceSourceUnsupportedError:
    return JRATargetRaceSourceUnsupportedError(message)


def _one(nodes: object, name: str) -> _Tag:
    values = tuple(nodes)  # type: ignore[arg-type]
    if len(values) != 1 or not isinstance(values[0], _Tag):
        raise _validation(f"{name} must be unique")
    return values[0]


def _display(value: object) -> str:
    if type(value) is not str:
        raise _validation("official display value is invalid")
    return " ".join(_normalize("NFC", value).split())


def _text(node: _Tag, name: str) -> str:
    value = _display(node.get_text(" ", strip=True))
    if not value:
        raise _validation(f"{name} is missing")
    return value


def _cell(row: _Tag, selector: str, name: str) -> _Tag:
    return _one(row.select(selector), name)


def _positive(value: str, name: str) -> int:
    if _POSITIVE.fullmatch(value) is None:
        raise _validation(f"{name} is invalid")
    return int(value)


def _odds(value: str) -> _Decimal:
    if _DECIMAL.fullmatch(value) is None:
        raise _unsupported("official JRA target odds is unsupported")
    try:
        result = _Decimal(value)
    except _InvalidOperation as error:
        raise _unsupported("official JRA target odds is unsupported") from error
    if not result.is_finite() or result <= 0:
        raise _unsupported("official JRA target odds is unsupported")
    return result


def _document(response: _Response) -> _BeautifulSoup:
    try:
        html = response.response_body.decode("cp932", errors="strict")
    except UnicodeDecodeError as error:
        raise _validation("accessD response is not strict cp932") from error
    return _BeautifulSoup(html, "html.parser")


def _card_date(response_url: str) -> _date:
    try:
        raw = _urlsplit(response_url).query.split("=", 1)[1].replace("%2F", "/")
    except (AttributeError, IndexError) as error:
        raise _validation("accessD CNAME is invalid") from error
    match = _CNAME_DATE.search(raw)
    if match is None:
        raise _validation("accessD CNAME calendar date is invalid")
    value = match.group("date")
    try:
        return _date(int(value[:4]), int(value[4:6]), int(value[6:8]))
    except ValueError as error:
        raise _validation("accessD CNAME calendar date is invalid") from error


@_dataclass(frozen=True, slots=True)
class _CardFacts:
    race_date: _date
    scheduled_start_at: _datetime
    place: str
    distance_m: int
    track: str
    track_condition: str
    race_name: str
    race_class: str
    weather: str | None


def _header_facts(soup: _BeautifulSoup, identity: object, cname_date: _date) -> _CardFacts:
    card = _one(soup.select("#contentsBody > div.syutsuba > table.basic.narrow-xy.mt20"), "official JRA accessD card")
    header = _one(card.select("caption > div.race_header"), "official JRA accessD race header")
    date_node = _one(header.select("div.left > div.date_line > div.inner > div.cell.date"), "official JRA accessD date")
    date_match = _DATE_LINE.fullmatch(_text(date_node, "official JRA accessD date"))
    if date_match is None:
        raise _validation("official JRA accessD date is invalid")
    try:
        race_date = _date(int(date_match.group("year")), int(date_match.group("month")), int(date_match.group("day")))
    except ValueError as error:
        raise _validation("official JRA accessD date is invalid") from error
    if race_date != cname_date or str(race_date.year) != identity.year or date_match.group("venue") != _VENUES[identity.venue_code] or int(date_match.group("meeting")) != int(identity.meeting_number) or int(date_match.group("day_no")) != int(identity.meeting_day):
        raise _validation("official JRA accessD visible race identity disagrees")
    race_node = _one(soup.select("#contentsBody > div.line.main > div.inner > h1"), "official JRA accessD race number")
    race_match = _RACE.fullmatch(_text(race_node, "official JRA accessD race number"))
    if race_match is None or int(race_match.group("race")) != int(identity.race_number):
        raise _validation("official JRA accessD race number disagrees")
    time_node = _one(header.select("div.left > div.date_line > div.inner > div.cell.time > strong"), "official JRA accessD scheduled start")
    time_match = _TIME.fullmatch(_text(time_node, "official JRA accessD scheduled start"))
    if time_match is None:
        raise _validation("official JRA accessD scheduled start is invalid")
    try:
        scheduled = _datetime.combine(race_date, _time(int(time_match.group("hour")), int(time_match.group("minute"))), tzinfo=_TOKYO).astimezone(_timezone.utc)
    except ValueError as error:
        raise _validation("official JRA accessD scheduled start is invalid") from error
    course_node = _one(header.select("div.race_title > div.type > div.cell.course"), "official JRA accessD course")
    course_match = _COURSE.fullmatch(_text(course_node, "official JRA accessD course"))
    if course_match is None:
        raise _validation("official JRA accessD course is invalid")
    distance = int(course_match.group("distance").replace(",", ""))
    baba = _one(header.select("div.cell.baba"), "official JRA accessD track facts")
    surface_selector = "li.turf" if course_match.group("surface") == "芝" else "li.dirt"
    condition_row = _one(baba.select(surface_selector), "official JRA accessD surface condition")
    cap = _text(_one(condition_row.select("span.cap"), "official JRA accessD surface label"), "official JRA accessD surface label")
    if cap != course_match.group("surface"):
        raise _validation("official JRA accessD course and condition surface disagree")
    condition = _text(_one(condition_row.select("span.txt"), "official JRA accessD track condition"), "official JRA accessD track condition")
    weather_nodes = tuple(baba.select("li.weather > span.inner > span.txt"))
    if len(weather_nodes) > 1:
        raise _validation("official JRA accessD weather is ambiguous")
    weather = None if not weather_nodes else _text(weather_nodes[0], "official JRA accessD weather")
    return _CardFacts(race_date, scheduled, date_match.group("venue"), distance, course_match.group("surface"), condition, _text(_one(header.select("div.race_title > div.inner > div.txt > span.main > span.race_name"), "official JRA accessD race name"), "official JRA accessD race name"), _text(_one(header.select("div.race_title > div.type > div.cell.class"), "official JRA accessD race class"), "official JRA accessD race class"), weather)


def _evidence(response: _Response, role: str) -> tuple[_Evidence, ...]:
    return (_Evidence(role, response.response_url, _hashlib.sha256(response.response_body).hexdigest(), None, response.observed_at, None),)


def _record(kind: str, race_id: str, entry_id: str | None, values: dict[str, object], response: _Response) -> _Record:
    return _Record(record_kind=kind, organization="JRA", source_system="jra_official", external_race_id=race_id, external_entry_id=entry_id, provider_record_id=None, record_values=values, evidence=_evidence(response, kind))


@_dataclass(frozen=True, slots=True)
class JRATargetRaceSourceCollection:
    target_track_record: _Record
    target_entry_records: tuple[_Record, ...]
    source_records: tuple[_Record, ...]

    def __post_init__(self) -> None:
        if type(self.target_track_record) is not _Record or type(self.target_entry_records) is not tuple or type(self.source_records) is not tuple:
            raise _validation("target source collection has invalid types")
        track = self.target_track_record
        if track.record_kind != "track" or track.organization != "JRA" or track.source_system != "jra_official" or track.external_entry_id is not None:
            raise _validation("target track record is invalid")
        if not self.source_records or self.source_records[0] is not track:
            raise _validation("target source records must start with target track")
        for record in self.source_records:
            if type(record) is not _Record:
                raise _validation("target source record is invalid")
            if record.organization != "JRA" or record.source_system != "jra_official" or record.external_race_id != track.external_race_id:
                raise _validation("target source record family is invalid")
        try:
            race = _parse_race_id(track.external_race_id)
        except _IdentityError as error:
            raise _validation("target track race identity is invalid") from error
        if len(self.source_records) != 1 + 3 * len(self.target_entry_records):
            raise _validation("target source record count is invalid")
        expected: list[_Record] = [track]
        seen_no: set[int] = set()
        seen_horse: set[str] = set()
        previous = 0
        for index, entry in enumerate(self.target_entry_records):
            if type(entry) is not _Record or entry.record_kind != "entry" or entry.organization != "JRA" or entry.source_system != "jra_official" or entry.external_race_id != track.external_race_id or entry.external_entry_id is None:
                raise _validation("target entry record is invalid")
            try:
                horse = _parse_horse_id(entry.record_values["external_horse_id"])
                horse_no = entry.record_values["horse_no"]
                rebuilt = _build_entry_id(race_identity=race, horse_no=horse_no)
            except (_IdentityError, KeyError, TypeError, ValueError) as error:
                raise _validation("target entry identity is invalid") from error
            if type(horse_no) is not int or horse_no <= previous or entry.external_entry_id != rebuilt or entry.record_values["external_entry_id"] != rebuilt or horse_no in seen_no or horse.external_horse_id in seen_horse:
                raise _validation("target entry ordering or identity is invalid")
            previous = horse_no
            seen_no.add(horse_no)
            seen_horse.add(horse.external_horse_id)
            group = self.source_records[1 + index * 3 : 1 + (index + 1) * 3]
            if (
                tuple(record.record_kind for record in group) != ("entry", "jockey", "odds_win")
                or group[0] is not entry
                or any(record.external_entry_id != rebuilt for record in group)
                or group[2].record_values["horse_no"] != horse_no
            ):
                raise _validation("target source record group is invalid")
            expected.extend(group)
        if not self.target_entry_records or self.source_records != tuple(expected):
            raise _validation("target source record ordering is invalid")


def normalize_jra_target_race_input_source_records(*, response: _Response) -> JRATargetRaceSourceCollection:
    """Normalize one supplied canonical accessD card into neutral target records."""

    if type(response) is not _Response:
        raise _validation("response must be exact JRASuppliedOfficialResponse")
    try:
        identity = _parse_card_url(response.response_url)
    except _IdentityError as error:
        raise _validation("response must be canonical accessD evidence") from error
    cname_date = _card_date(response.response_url)
    if str(cname_date.year) != identity.year:
        raise _validation("accessD CNAME calendar date disagrees with race identity")
    soup = _document(response)
    facts = _header_facts(soup, identity, cname_date)
    if response.observed_at > facts.scheduled_start_at:
        raise _validation("accessD response is observed after scheduled start")
    card = _one(soup.select("#contentsBody > div.syutsuba > table.basic.narrow-xy.mt20"), "official JRA accessD card")
    rows = tuple(card.select("tbody > tr"))
    if not rows:
        raise _validation("official JRA accessD runner rows are missing")
    try:
        track = _record("track", identity.external_race_id, None, {"target_race_date": facts.race_date, "scheduled_start_at": facts.scheduled_start_at, "place": facts.place, "distance_m": facts.distance_m, "track": facts.track, "track_condition": facts.track_condition, "race_name": facts.race_name, "race_class": facts.race_class, "weather": facts.weather}, response)
        parsed: list[tuple[int, str, _Record, _Record, _Record]] = []
        seen_no: set[int] = set()
        seen_horse: set[str] = set()
        for row in rows:
            horse_no = _positive(_text(_cell(row, "td.num", "official JRA target horse number"), "official JRA target horse number"), "official JRA target horse number")
            anchor = _one(row.select("td.horse > div.name_line > div.name > a[href]"), "official JRA accessU horse anchor")
            href = anchor.get("href")
            if type(href) is not str or not href:
                raise _validation("official JRA accessU horse anchor is invalid")
            try:
                horse = _parse_profile_url(_urljoin("https://www.jra.go.jp", href))
            except _IdentityError as error:
                raise _validation("official JRA accessU horse anchor is invalid") from error
            if horse_no in seen_no or horse.external_horse_id in seen_horse:
                raise _validation("official JRA target runner identity is duplicated")
            seen_no.add(horse_no)
            seen_horse.add(horse.external_horse_id)
            entry_id = _build_entry_id(race_identity=identity, horse_no=horse_no)
            odds_node = _cell(row, "td.horse > div.name_line > div.odds > div.odds_line > span.num", "official JRA target odds")
            odds = _odds(_display(odds_node.get_text(" ", strip=True)))
            jockey = _text(_cell(row, "td.jockey > p.jockey", "official JRA target jockey"), "official JRA target jockey")
            entry = _record("entry", identity.external_race_id, entry_id, {"external_entry_id": entry_id, "external_horse_id": horse.external_horse_id, "horse_no": horse_no}, response)
            jockey_record = _record("jockey", identity.external_race_id, entry_id, {"external_entry_id": entry_id, "jockey": jockey}, response)
            odds_record = _record("odds_win", identity.external_race_id, entry_id, {"external_entry_id": entry_id, "horse_no": horse_no, "win_odds": odds}, response)
            parsed.append((horse_no, horse.external_horse_id, entry, jockey_record, odds_record))
        parsed.sort(key=lambda item: item[0])
        entries = tuple(item[2] for item in parsed)
        records: tuple[_Record, ...] = (track,) + tuple(record for item in parsed for record in item[2:])
        validated = _validate_record_set(records=records)
        return JRATargetRaceSourceCollection(track, entries, validated)
    except (_SourceError, _SourceConflictError, TypeError, ValueError, OverflowError) as error:
        if isinstance(error, JRATargetRaceSourceError):
            raise
        raise _validation("JRA target source records are invalid") from error


__all__ = (
    "JRATargetRaceSourceError",
    "JRATargetRaceSourceValidationError",
    "JRATargetRaceSourceUnsupportedError",
    "JRATargetRaceSourceCollection",
    "normalize_jra_target_race_input_source_records",
)
