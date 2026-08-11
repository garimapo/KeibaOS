"""Pure complete-history discovery from one supplied NAR HorseMarkInfo response."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass
from datetime import date as _date, datetime as _datetime
from enum import StrEnum as _StrEnum
import re as _re
from unicodedata import category as _category, normalize as _normalize
from urllib.parse import parse_qsl as _parse_qsl, urljoin as _urljoin, urlsplit as _urlsplit

from bs4 import BeautifulSoup as _BeautifulSoup
from bs4.element import Tag as _Tag

from scripts.simulation.historical_input_source_records import (
    HistoricalInputSourceRecord as _HistoricalInputSourceRecord,
)
from scripts.simulation.nar_historical_input_source import (
    NarSuppliedOfficialResponse as _NarSuppliedOfficialResponse,
)

if "annotations" in globals():
    del annotations


class NARHistoricalEventKind(_StrEnum):
    """Closed classification vocabulary for an official HorseMarkInfo event row."""

    NAR_ACTUAL_START = "nar_actual_start"
    JRA_ACTUAL_START = "jra_actual_start"
    PROVEN_NON_START = "proven_non_start"
    UNSUPPORTED_ACTUAL_START = "unsupported_actual_start"


class NARHistoricalPastRaceDiscoveryError(ValueError):
    """Base error for the supplied HorseMarkInfo history-discovery boundary."""


class NARHistoricalPastRaceDiscoveryValidationError(
    NARHistoricalPastRaceDiscoveryError,
):
    """Raised for malformed, ambiguous, or contradictory supplied evidence."""


class NARHistoricalPastRaceDiscoveryUnsupportedError(
    NARHistoricalPastRaceDiscoveryError,
):
    """Raised for a recognized official event outside c1 discovery support."""


_HOSTS = frozenset({"www.keiba.go.jp", "www2.keiba.go.jp"})
_HORSE_PATH = "/KeibaWeb/DataRoom/HorseMarkInfo"
_RACE_PATH = "/KeibaWeb/TodayRaceInfo/RaceMarkTable"
_LINEAGE_KEY = "k_lineageLoginCode"
_RACE_KEYS = frozenset({"k_babaCode", "k_raceDate", "k_raceNo"})
_TOKEN = _re.compile(r"[1-9][0-9]*\Z")
_DATE = _re.compile(r"[0-9]{4}/[0-9]{2}/[0-9]{2}\Z")
_TARGET_RACE = _re.compile(r"nar:([0-9]{8}):([1-9][0-9]*):([1-9][0-9]*)\Z")
_ENTRY = _re.compile(r"(?P<race>nar:[0-9]{8}:[1-9][0-9]*:[1-9][0-9]*):entry:([1-9][0-9]*)\Z")
_HORSE = _re.compile(r"nar:horse:([1-9][0-9]*)\Z")
_PERCENT = _re.compile(r"%(?:[0-9A-Fa-f]{2})")
_HISTORY_HEADINGS = (
    "年月日", "競馬場", "R", "競走名", "格組", "距離", "天候・馬場", "頭数", "枠", "馬番", "人気", "着順", "タイム", "差", "上3F", "体重", "騎手(所属)", "重量", "調教師", "収得賞金", "1着馬または(2着馬)",
)
_ZERO_MESSAGE = "指定の馬の出走履歴がありません。"
_JRA_PLACE = _re.compile(r"Ｊ.+\Z")
_FINISH = _re.compile(r"[1-9][0-9]*\Z")
_BODY_WEIGHT = _re.compile(r"[1-9][0-9]*\Z")
_KNOWN_STARTED_ABNORMAL = frozenset({"中止", "失格", "降着"})
_NON_STARTS = frozenset({"取消", "取止"})
_CONTINUATION = _re.compile(r"(?:next|previous|more|pagination|continuation|page|offset|limit)", _re.IGNORECASE)


def _validation(message: str) -> NARHistoricalPastRaceDiscoveryValidationError:
    return NARHistoricalPastRaceDiscoveryValidationError(message)


def _unsupported(message: str) -> NARHistoricalPastRaceDiscoveryUnsupportedError:
    return NARHistoricalPastRaceDiscoveryUnsupportedError(message)


def _text(value: object) -> str:
    if type(value) is not str:
        raise _validation("display text must be str")
    return _re.sub(r"\s+", " ", _normalize("NFC", value)).strip()


def _required(value: object, name: str) -> str:
    result = _text(value)
    if not result:
        raise _validation(f"{name} is required")
    return result


def _token(value: object, name: str) -> str:
    if type(value) is not str or _TOKEN.fullmatch(value) is None:
        raise _validation(f"{name} must be a positive canonical decimal token")
    return value


def _parse_date(value: object, name: str) -> _date:
    if type(value) is not str or _DATE.fullmatch(value) is None:
        raise _validation(f"{name} must be YYYY/MM/DD")
    try:
        return _date.fromisoformat(value.replace("/", "-"))
    except ValueError as error:
        raise _validation(f"{name} must be a real date") from error


def _bad_percent(value: str) -> bool:
    return any(value[index] == "%" and _PERCENT.match(value, index) is None for index in range(len(value)))


def _url(value: object, name: str):
    if type(value) is not str or not value or value != _normalize("NFC", value) or value != value.strip():
        raise _validation(f"{name} is invalid")
    if any(character.isspace() or _category(character) == "Cc" for character in value):
        raise _validation(f"{name} contains whitespace or control characters")
    try:
        parsed = _urlsplit(value)
        _ = parsed.port
    except ValueError as error:
        raise _validation(f"{name} is invalid") from error
    if parsed.username is not None or parsed.password is not None or parsed.fragment or "+" in parsed.query or _bad_percent(parsed.query):
        raise _validation(f"{name} is invalid")
    return parsed


def _query(parsed, keys: frozenset[str], name: str) -> dict[str, str]:
    if not parsed.query:
        raise _validation(f"{name} query is required")
    try:
        pairs = _parse_qsl(parsed.query, keep_blank_values=True, strict_parsing=True, encoding="utf-8", errors="strict")
    except ValueError as error:
        raise _validation(f"{name} query is invalid") from error
    values: dict[str, str] = {}
    for key, value in pairs:
        if not key or not value or key not in keys or key in values:
            raise _validation(f"{name} query keys are invalid")
        values[key] = value
    if set(values) != keys:
        raise _validation(f"{name} query keys are incomplete")
    return values


def _horse_url(value: object) -> tuple[str, str]:
    parsed = _url(value, "HorseMarkInfo URL")
    host = (parsed.hostname or "").lower()
    if parsed.scheme.lower() != "https" or host not in _HOSTS or parsed.port not in (None, 443) or parsed.path != _HORSE_PATH:
        raise _validation("HorseMarkInfo URL is invalid")
    lineage = _token(_query(parsed, frozenset({_LINEAGE_KEY}), "HorseMarkInfo URL")[_LINEAGE_KEY], "k_lineageLoginCode")
    canonical = f"https://{host}{_HORSE_PATH}?{_LINEAGE_KEY}={lineage}"
    if canonical != value:
        raise _validation("HorseMarkInfo URL must be canonical")
    return canonical, lineage


def _race_url(value: object, base_url: str) -> tuple[str, _date, str, str]:
    if type(value) is not str or not value:
        raise _validation("HorseMarkInfo result navigation is invalid")
    parsed = _url(value, "HorseMarkInfo result navigation")
    candidate = value if parsed.scheme else _urljoin(base_url, value)
    resolved = _url(candidate, "HorseMarkInfo result navigation")
    host = (resolved.hostname or "").lower()
    if resolved.scheme.lower() != "https" or host not in _HOSTS or resolved.port not in (None, 443) or resolved.path != _RACE_PATH:
        raise _validation("HorseMarkInfo result navigation is invalid")
    query = _query(resolved, _RACE_KEYS, "HorseMarkInfo result navigation")
    race_date = _parse_date(query["k_raceDate"], "k_raceDate")
    baba = _token(query["k_babaCode"], "k_babaCode")
    race_no = _token(query["k_raceNo"], "k_raceNo")
    return (
        f"https://www.keiba.go.jp{_RACE_PATH}?k_babaCode={baba}&k_raceDate={race_date:%Y%%2F%m%%2F%d}&k_raceNo={race_no}",
        race_date,
        baba,
        race_no,
    )


def _document(response: _NarSuppliedOfficialResponse) -> _BeautifulSoup:
    try:
        html = response.response_body.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise _validation("response_body must be strict UTF-8") from error
    soup = _BeautifulSoup(html, "html.parser")
    declarations = [node for node in soup.find_all("meta") if isinstance(node.get("charset"), str) and node.get("charset").lower() == "utf-8"]
    if len(declarations) != 1 or len(soup.select("h4.odd_title")) != 1:
        raise _validation("HorseMarkInfo document identity is invalid")
    return soup


def _track(record: object) -> tuple[str, _date, _datetime, str]:
    if type(record) is not _HistoricalInputSourceRecord or record.record_kind != "track" or record.organization != "NAR" or record.source_system != "nar_official":
        raise _validation("target_track_record is incompatible")
    match = _TARGET_RACE.fullmatch(record.external_race_id)
    if match is None:
        raise _validation("target track external_race_id is invalid")
    date_text = match.group(1)
    try:
        race_date = _date.fromisoformat(f"{date_text[:4]}-{date_text[4:6]}-{date_text[6:]}")
    except ValueError as error:
        raise _validation("target track external_race_id date is invalid") from error
    target_date = record.record_values["target_race_date"]
    scheduled_start = record.record_values["scheduled_start_at"]
    if type(target_date) is not _date or type(scheduled_start) is not _datetime or target_date != race_date:
        raise _validation("target track race identity is inconsistent")
    return record.external_race_id, target_date, scheduled_start, record.source_system


def _entry(record: object, race_id: str, source_system: str) -> tuple[str, str]:
    if type(record) is not _HistoricalInputSourceRecord or record.record_kind != "entry" or record.organization != "NAR" or record.source_system != source_system:
        raise _validation("target_entry_record is incompatible")
    if record.external_race_id != race_id or record.external_entry_id is None:
        raise _validation("target entry race identity is inconsistent")
    match = _ENTRY.fullmatch(record.external_entry_id)
    if match is None or match.group("race") != race_id:
        raise _validation("target external_entry_id is invalid")
    if type(record.record_values["horse_no"]) is not int or str(record.record_values["horse_no"]) != match.group(2):
        raise _validation("target entry horse number is inconsistent")
    horse = record.record_values["external_horse_id"]
    if type(horse) is not str:
        raise _validation("target external_horse_id is required")
    lineage = _HORSE.fullmatch(horse)
    if lineage is None:
        raise _validation("target external_horse_id is invalid")
    return record.external_entry_id, lineage.group(1)


def _history_table(soup: _BeautifulSoup) -> _Tag:
    tables = soup.select("table.HorseMarkInfo_table")
    if len(tables) != 1:
        raise _validation("HorseMarkInfo history table is missing or ambiguous")
    table = tables[0]
    heads = table.find_all("thead", recursive=False)
    if len(heads) != 1:
        raise _validation("HorseMarkInfo history heading structure is invalid")
    header_rows = heads[0].find_all("tr", recursive=False)
    if len(header_rows) != 1:
        raise _validation("HorseMarkInfo history heading structure is invalid")
    nodes = header_rows[0].find_all(["th", "td"], recursive=False)
    if any(node.name != "th" for node in nodes):
        raise _validation("HorseMarkInfo history heading structure is invalid")
    headings = tuple(_text(node.get_text(" ", strip=True)) for node in nodes)
    if headings != _HISTORY_HEADINGS:
        raise _validation("HorseMarkInfo history headings are invalid")
    for index, node in enumerate(nodes):
        if index == 6:
            if node.get("colspan") != "3" or node.has_attr("rowspan"):
                raise _validation("HorseMarkInfo weather/track heading span is invalid")
        elif node.has_attr("colspan") or node.has_attr("rowspan"):
            raise _validation("HorseMarkInfo history heading span is invalid")
    return table


def _continuation(soup: _BeautifulSoup) -> bool:
    for node in soup.find_all(True):
        values = " ".join(str(node.get(key, "")) for key in ("id", "class", "href", "data-page", "data-offset", "data-limit"))
        if _CONTINUATION.search(values):
            return True
    return False


def _cells(row: _Tag) -> list[_Tag]:
    cells = row.find_all("td", recursive=False)
    if len(cells) != 23 or any(cell.has_attr("colspan") or cell.has_attr("rowspan") for cell in cells):
        raise _validation("HorseMarkInfo history row columns are invalid")
    return cells


def _reference(row: _Tag, base_url: str) -> NARHistoricalPastRaceReference:
    cells = _cells(row)
    race_date = _parse_date(_required(cells[0].get_text(" ", strip=True), "HorseMarkInfo race_date"), "HorseMarkInfo race_date")
    place = _required(cells[1].get_text(" ", strip=True), "HorseMarkInfo place")
    race_no = _required(cells[2].get_text(" ", strip=True), "HorseMarkInfo race number")
    finish = _text(cells[13].get_text(" ", strip=True))
    race_time = _text(cells[14].get_text(" ", strip=True))
    difference = _text(cells[15].get_text(" ", strip=True))
    body_weight = _text(cells[17].get_text(" ", strip=True))
    links = row.select("a[href]")
    race_links = [link for link in links if _urljoin(base_url, str(link.get("href"))).split("?", 1)[0].endswith(_RACE_PATH)]
    if len(race_links) > 1:
        raise _validation("HorseMarkInfo result navigation is ambiguous")
    if race_links:
        canonical, linked_date, baba, linked_race_no = _race_url(str(race_links[0].get("href")), base_url)
        if linked_date != race_date or linked_race_no != _token(race_no, "HorseMarkInfo race number"):
            raise _validation("HorseMarkInfo row identity disagrees with result navigation")
        provider_event_id = f"nar:event:{linked_date:%Y%m%d}:{baba}:{linked_race_no}"
        if _FINISH.fullmatch(finish) is not None and race_time and _BODY_WEIGHT.fullmatch(body_weight) is not None:
            return NARHistoricalPastRaceReference(NARHistoricalEventKind.NAR_ACTUAL_START, race_date, provider_event_id, canonical)
        if finish in _NON_STARTS and not race_time and not difference and body_weight == "－":
            return NARHistoricalPastRaceReference(NARHistoricalEventKind.PROVEN_NON_START, race_date, provider_event_id, canonical)
        if finish in _KNOWN_STARTED_ABNORMAL and _BODY_WEIGHT.fullmatch(body_weight) is not None:
            return NARHistoricalPastRaceReference(NARHistoricalEventKind.UNSUPPORTED_ACTUAL_START, race_date, provider_event_id, canonical)
        raise _validation("HorseMarkInfo NAR event state is unclassified")
    if place.startswith("Ｊ"):
        if _JRA_PLACE.fullmatch(place) is None or _TOKEN.fullmatch(race_no) is None or _FINISH.fullmatch(finish) is None or not race_time:
            raise _unsupported("HorseMarkInfo JRA event identity or start state is unsupported")
        return NARHistoricalPastRaceReference(
            NARHistoricalEventKind.JRA_ACTUAL_START,
            race_date,
            f"jra:event:{race_date:%Y%m%d}:{place}:{race_no}",
            None,
        )
    raise _validation("HorseMarkInfo event has no recognized result identity")


@_dataclass(frozen=True, slots=True)
class NARHistoricalPastRaceReference:
    """One immutable provider-native event identity discovered on HorseMarkInfo."""

    event_kind: NARHistoricalEventKind
    race_date: _date
    provider_event_id: str
    canonical_race_result_url: str | None

    def __post_init__(self) -> None:
        if type(self.event_kind) is not NARHistoricalEventKind or type(self.race_date) is not _date or type(self.provider_event_id) is not str or not self.provider_event_id:
            raise NARHistoricalPastRaceDiscoveryValidationError("historical event reference is invalid")
        if self.event_kind is NARHistoricalEventKind.NAR_ACTUAL_START and self.canonical_race_result_url is None:
            raise NARHistoricalPastRaceDiscoveryValidationError("NAR actual start requires result URL")
        if self.event_kind is NARHistoricalEventKind.JRA_ACTUAL_START and self.canonical_race_result_url is not None:
            raise NARHistoricalPastRaceDiscoveryValidationError("JRA actual start must not carry NAR result URL")
        if self.canonical_race_result_url is not None and (type(self.canonical_race_result_url) is not str or not self.canonical_race_result_url):
            raise NARHistoricalPastRaceDiscoveryValidationError("historical result URL is invalid")


@_dataclass(frozen=True, slots=True)
class NARHistoricalPastRaceDiscovery:
    """Complete ordered event sequence for one validated target entry."""

    target_external_race_id: str
    target_external_entry_id: str
    target_external_horse_id: str
    target_race_date: _date
    events: tuple[NARHistoricalPastRaceReference, ...]
    proven_zero_history: bool

    def __post_init__(self) -> None:
        if type(self.target_external_race_id) is not str or type(self.target_external_entry_id) is not str or type(self.target_external_horse_id) is not str or type(self.target_race_date) is not _date or type(self.events) is not tuple or type(self.proven_zero_history) is not bool:
            raise NARHistoricalPastRaceDiscoveryValidationError("historical discovery is invalid")
        if any(type(event) is not NARHistoricalPastRaceReference for event in self.events) or self.proven_zero_history != (self.events == ()):
            raise NARHistoricalPastRaceDiscoveryValidationError("historical discovery invariant is invalid")


def discover_nar_historical_past_race_history(
    *,
    target_track_record: _HistoricalInputSourceRecord,
    target_entry_record: _HistoricalInputSourceRecord,
    horse_history_response: _NarSuppliedOfficialResponse,
) -> NARHistoricalPastRaceDiscovery:
    """Discover the complete ordered official HorseMarkInfo event sequence."""

    race_id, target_date, scheduled_start, source_system = _track(target_track_record)
    entry_id, lineage = _entry(target_entry_record, race_id, source_system)
    if type(horse_history_response) is not _NarSuppliedOfficialResponse:
        raise _validation("horse_history_response must be NarSuppliedOfficialResponse")
    canonical_horse_url, response_lineage = _horse_url(horse_history_response.response_url)
    if response_lineage != lineage:
        raise _validation("HorseMarkInfo lineage does not match target entry")
    if horse_history_response.observed_at > scheduled_start:
        raise _validation("HorseMarkInfo observation is after target scheduled start")
    soup = _document(horse_history_response)
    tables = soup.select("table.HorseMarkInfo_table")
    zero_nodes = [node for node in soup.find_all("p") if _text(node.get_text(" ", strip=True)) == _ZERO_MESSAGE]
    if tables and zero_nodes:
        raise _validation("HorseMarkInfo history and zero states conflict")
    if zero_nodes:
        if len(zero_nodes) != 1 or soup.select(f'a[href*="{_RACE_PATH}"]') or _continuation(soup):
            raise _validation("HorseMarkInfo zero history state is invalid")
        return NARHistoricalPastRaceDiscovery(race_id, entry_id, f"nar:horse:{lineage}", target_date, (), True)
    if not tables:
        raise _validation("HorseMarkInfo has neither history nor zero state")
    table = _history_table(soup)
    if _continuation(soup):
        raise _validation("HorseMarkInfo history continuation is unsupported")
    bodies = table.find_all("tbody", recursive=False)
    if len(bodies) != 1:
        raise _validation("HorseMarkInfo history body structure is invalid")
    rows = bodies[0].find_all("tr", recursive=False)
    if not rows:
        raise _validation("HorseMarkInfo history table is empty")
    events = tuple(_reference(row, canonical_horse_url) for row in rows)
    if len({event.provider_event_id for event in events}) != len(events):
        raise _validation("HorseMarkInfo event identity is duplicated")
    if any(event.race_date >= target_date for event in events):
        raise _validation("HorseMarkInfo event is not before target race")
    if any(events[index].race_date < events[index + 1].race_date for index in range(len(events) - 1)):
        raise _validation("HorseMarkInfo chronology is out of order")
    return NARHistoricalPastRaceDiscovery(race_id, entry_id, f"nar:horse:{lineage}", target_date, events, False)


__all__ = (
    "NARHistoricalEventKind",
    "NARHistoricalPastRaceReference",
    "NARHistoricalPastRaceDiscovery",
    "NARHistoricalPastRaceDiscoveryError",
    "NARHistoricalPastRaceDiscoveryValidationError",
    "NARHistoricalPastRaceDiscoveryUnsupportedError",
    "discover_nar_historical_past_race_history",
)
