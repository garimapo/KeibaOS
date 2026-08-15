"""Pure complete-history discovery from one supplied JRA accessU response."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass
from datetime import date as _date, datetime as _datetime
from enum import StrEnum as _StrEnum
import hashlib as _hashlib
import re as _re
from unicodedata import normalize as _normalize
from urllib.parse import urljoin as _urljoin, urlsplit as _urlsplit

from bs4 import BeautifulSoup as _BeautifulSoup
from bs4.element import Tag as _Tag

from scripts.simulation.historical_input_source_records import (
    HistoricalInputSourceRecord as _HistoricalInputSourceRecord,
)
from scripts.simulation.jra_official_identity import (
    JRAExternalHorseIdentity as _JRAExternalHorseIdentity,
    JRAExternalRaceIdentity as _JRAExternalRaceIdentity,
    JRAOfficialIdentityValidationError as _JRAOfficialIdentityValidationError,
    build_jra_external_entry_id as _build_jra_external_entry_id,
    parse_jra_external_horse_id as _parse_jra_external_horse_id,
    parse_jra_external_race_id as _parse_jra_external_race_id,
    parse_jra_horse_profile_url_identity as _parse_jra_horse_profile_url_identity,
    parse_jra_result_url_identity as _parse_jra_result_url_identity,
)
from scripts.simulation.jra_official_response_capture import (
    JRAOfficialPageKind as _JRAOfficialPageKind,
    JRASuppliedOfficialResponse as _JRASuppliedOfficialResponse,
)


class JRAHistoricalEventKind(_StrEnum):
    """Closed event vocabulary for one official JRA accessU history row."""

    JRA_ACTUAL_START = "jra_actual_start"
    NON_JRA_ACTUAL_START = "non_jra_actual_start"
    PROVEN_NON_START = "proven_non_start"
    UNSUPPORTED_ACTUAL_START = "unsupported_actual_start"


class JRAHistoricalPastRaceDiscoveryError(ValueError):
    """Base error for the pure JRA accessU history-discovery boundary."""


class JRAHistoricalPastRaceDiscoveryValidationError(
    JRAHistoricalPastRaceDiscoveryError,
):
    """Raised for malformed, incomplete, ambiguous, or contradictory evidence."""


class JRAHistoricalPastRaceDiscoveryUnsupportedError(
    JRAHistoricalPastRaceDiscoveryError,
):
    """Raised for recognized provider semantics outside this discovery envelope."""


_HEADINGS = (
    "年月日", "場", "レース名", "距離", "馬場", "頭数", "人気", "着順", "騎手名", "負担重量", "馬体重", "タイム", "Rt", "1着馬（2着馬）",
)
_AGGREGATE_HEADINGS = ("1着", "2着", "3着", "4着以下", "出走回数", "勝率", "連対率", "3着内率")
_NO_DATA = "該当するデータがありません。"
_INTEGER = _re.compile(r"(?:0|[1-9][0-9]*)\Z")
_POSITIVE = _re.compile(r"[1-9][0-9]*\Z")
_DATE = _re.compile(r"[0-9]{4}年[0-9]{1,2}月[0-9]{1,2}日\Z")
_CNAME_DATE = _re.compile(r"(?P<date>[0-9]{8})/[0-9A-F]{2}\Z")
_TIME = _re.compile(r"[0-9]{1,2}:[0-5][0-9](?:\.[0-9])?\Z")
_CONTINUATION = _re.compile(r"(?:next|previous|more|pagination|continuation|page|offset|limit|lazy)", _re.IGNORECASE)
_NON_START_NAMES = frozenset({"JRAへ転入", "JRAより転出"})
_UNSUPPORTED_FINISH = frozenset({"中止", "失格", "降着", "競走中止"})
_NON_START_FINISH = frozenset({"取消", "取止", "除外"})
_JRA_PLACES = frozenset({"札幌", "函館", "福島", "新潟", "東京", "中山", "中京", "京都", "阪神", "小倉"})


def _validation(message: str) -> JRAHistoricalPastRaceDiscoveryValidationError:
    return JRAHistoricalPastRaceDiscoveryValidationError(message)


def _unsupported(message: str) -> JRAHistoricalPastRaceDiscoveryUnsupportedError:
    return JRAHistoricalPastRaceDiscoveryUnsupportedError(message)


def _text(value: object) -> str:
    if type(value) is not str:
        raise _validation("official display text is invalid")
    return " ".join(_normalize("NFC", value).split())


def _node_text(node: _Tag, name: str) -> str:
    value = _text(node.get_text(" ", strip=True))
    if not value:
        raise _validation(f"{name} is missing")
    return value


def _one(nodes: object, name: str) -> _Tag:
    values = tuple(nodes)  # type: ignore[arg-type]
    if len(values) != 1 or not isinstance(values[0], _Tag):
        raise _validation(f"{name} must be unique")
    return values[0]


def _parse_date(value: str, name: str) -> _date:
    if _DATE.fullmatch(value) is None:
        raise _validation(f"{name} is invalid")
    numbers = _re.findall(r"[0-9]+", value)
    try:
        return _date(int(numbers[0]), int(numbers[1]), int(numbers[2]))
    except (IndexError, ValueError) as error:
        raise _validation(f"{name} is invalid") from error


def _integer(value: str, name: str) -> int:
    if _INTEGER.fullmatch(value) is None:
        raise _validation(f"{name} must be a canonical non-negative integer")
    return int(value)


def _positive(value: str, name: str) -> int:
    if _POSITIVE.fullmatch(value) is None:
        raise _validation(f"{name} must be a positive canonical integer")
    return int(value)


def _document(response: _JRASuppliedOfficialResponse) -> _BeautifulSoup:
    try:
        return _BeautifulSoup(response.response_body.decode("cp932", errors="strict"), "html.parser")
    except UnicodeDecodeError as error:
        raise _validation("horse_history_response is not strict cp932") from error


def _target(
    track: object,
    entry: object,
) -> tuple[_JRAExternalRaceIdentity, str, _JRAExternalHorseIdentity, _date, _datetime]:
    if type(track) is not _HistoricalInputSourceRecord or type(entry) is not _HistoricalInputSourceRecord:
        raise _validation("target records must be exact HistoricalInputSourceRecord")
    if (
        track.record_kind != "track" or track.organization != "JRA" or track.source_system != "jra_official"
        or track.external_entry_id is not None
    ):
        raise _validation("target_track_record is incompatible")
    if (
        entry.record_kind != "entry" or entry.organization != "JRA" or entry.source_system != "jra_official"
        or entry.external_race_id != track.external_race_id or entry.external_entry_id is None
    ):
        raise _validation("target_entry_record is incompatible")
    try:
        race = _parse_jra_external_race_id(track.external_race_id)
        horse = _parse_jra_external_horse_id(entry.record_values["external_horse_id"])
        target_date = track.record_values["target_race_date"]
        scheduled = track.record_values["scheduled_start_at"]
        horse_no = entry.record_values["horse_no"]
        value_entry_id = entry.record_values["external_entry_id"]
    except (_JRAOfficialIdentityValidationError, KeyError) as error:
        raise _validation("target JRA identities are invalid") from error
    if type(target_date) is not _date or type(scheduled) is not _datetime:
        raise _validation("target track timing is invalid")
    try:
        if scheduled.tzinfo is None or scheduled.utcoffset() is None:
            raise _validation("target scheduled_start_at must be aware")
    except (TypeError, ValueError, OverflowError) as error:
        raise _validation("target scheduled_start_at is invalid") from error
    if type(horse_no) is not int or horse_no <= 0 or type(value_entry_id) is not str:
        raise _validation("target entry values are invalid")
    try:
        expected_entry_id = _build_jra_external_entry_id(race_identity=race, horse_no=horse_no)
    except _JRAOfficialIdentityValidationError as error:
        raise _validation("target external_entry_id is invalid") from error
    if entry.external_entry_id != expected_entry_id or value_entry_id != expected_entry_id:
        raise _validation("target entry identity is incoherent")
    return race, expected_entry_id, horse, target_date, scheduled


def _continuation(soup: _BeautifulSoup) -> bool:
    for node in soup.find_all(True):
        values = " ".join(str(node.get(key, "")) for key in ("id", "class", "href", "data-page", "data-offset", "data-limit"))
        if _CONTINUATION.search(values):
            return True
    return False


def _history_container(soup: _BeautifulSoup) -> _Tag:
    return _one(soup.select("div.race_detail"), "official accessU history section")


def _history_table(container: _Tag) -> _Tag:
    table = _one(container.select(":scope > table.basic.narrow-xy.striped"), "official accessU history table")
    head = _one(table.find_all("thead", recursive=False), "official accessU history heading")
    row = _one(head.find_all("tr", recursive=False), "official accessU history heading row")
    cells = row.find_all(["th", "td"], recursive=False)
    if any(cell.name != "th" or cell.has_attr("colspan") or cell.has_attr("rowspan") for cell in cells):
        raise _validation("official accessU history heading structure is invalid")
    if tuple(_text(cell.get_text(" ", strip=True)) for cell in cells) != _HEADINGS:
        raise _validation("official accessU history headings are invalid")
    return table


def _row_cells(row: _Tag) -> tuple[_Tag, ...]:
    cells = tuple(row.find_all("td", recursive=False))
    if len(cells) != len(_HEADINGS) or any(cell.has_attr("colspan") or cell.has_attr("rowspan") for cell in cells):
        raise _validation("official accessU history row columns are invalid")
    return cells


def _row_fingerprint(cells: tuple[_Tag, ...]) -> str:
    material = "\x1f".join(_text(cell.get_text(" ", strip=True)) for cell in cells).encode("utf-8")
    return _hashlib.sha256(material).hexdigest()


def _access_s_anchor(row: _Tag, base_url: str) -> tuple[_JRAExternalRaceIdentity, str] | None:
    matches: list[tuple[_JRAExternalRaceIdentity, str]] = []
    for anchor in row.select("a[href]"):
        href = anchor.get("href")
        if type(href) is not str or not href:
            raise _validation("official accessU history anchor is invalid")
        candidate = _urljoin(base_url, href)
        try:
            identity = _parse_jra_result_url_identity(candidate)
        except _JRAOfficialIdentityValidationError:
            continue
        matches.append((identity, candidate))
    if len(matches) > 1:
        raise _validation("official accessU result navigation is ambiguous")
    return matches[0] if matches else None


def _result_date(url: str, identity: _JRAExternalRaceIdentity) -> _date:
    try:
        cname = _urlsplit(url).query.split("=", 1)[1].replace("%2F", "/")
    except (AttributeError, IndexError) as error:
        raise _validation("official accessU result navigation is invalid") from error
    match = _CNAME_DATE.search(cname)
    if match is None:
        raise _validation("official accessU result navigation date is invalid")
    value = match.group("date")
    try:
        result = _date(int(value[:4]), int(value[4:6]), int(value[6:8]))
    except ValueError as error:
        raise _validation("official accessU result navigation date is invalid") from error
    if str(result.year) != identity.year:
        raise _validation("official accessU result navigation date disagrees with race identity")
    return result


def _is_non_start(cells: tuple[_Tag, ...], anchor: object) -> bool:
    name = _text(cells[2].get_text(" ", strip=True))
    if name not in _NON_START_NAMES:
        return False
    if anchor is not None or any(_text(cell.get_text(" ", strip=True)) for index, cell in enumerate(cells) if index not in {0, 2}):
        raise _validation("official accessU transfer row conflicts with start facts")
    return True


def _is_started(cells: tuple[_Tag, ...]) -> tuple[bool, bool]:
    finish = _text(cells[7].get_text(" ", strip=True))
    if finish in _UNSUPPORTED_FINISH:
        return True, True
    if finish in _NON_START_FINISH:
        return False, False
    ordinary = (
        bool(_text(cells[1].get_text(" ", strip=True)))
        and bool(_text(cells[2].get_text(" ", strip=True)))
        and _POSITIVE.fullmatch(_text(cells[5].get_text(" ", strip=True))) is not None
        and _POSITIVE.fullmatch(finish) is not None
        and bool(_text(cells[8].get_text(" ", strip=True)))
    )
    return ordinary, False


@_dataclass(frozen=True, slots=True)
class JRAHistoricalPastRaceReference:
    """One immutable ordered official accessU event."""

    event_kind: JRAHistoricalEventKind
    race_date: _date
    provider_event_id: str
    race_identity: _JRAExternalRaceIdentity | None
    canonical_race_result_url: str | None

    def __post_init__(self) -> None:
        if (
            type(self.event_kind) is not JRAHistoricalEventKind or type(self.race_date) is not _date
            or type(self.provider_event_id) is not str or not self.provider_event_id
        ):
            raise JRAHistoricalPastRaceDiscoveryValidationError("historical event reference is invalid")
        is_jra = self.event_kind is JRAHistoricalEventKind.JRA_ACTUAL_START
        if is_jra != (type(self.race_identity) is _JRAExternalRaceIdentity and type(self.canonical_race_result_url) is str and bool(self.canonical_race_result_url)):
            raise JRAHistoricalPastRaceDiscoveryValidationError("JRA event reference identity is invalid")
        if not is_jra and (self.race_identity is not None or self.canonical_race_result_url is not None):
            raise JRAHistoricalPastRaceDiscoveryValidationError("non-JRA event must not carry a JRA result identity")


@_dataclass(frozen=True, slots=True)
class JRAHistoricalPastRaceDiscovery:
    """Complete ordered accessU event sequence for one validated JRA target entry."""

    target_external_race_id: str
    target_external_entry_id: str
    target_external_horse_id: str
    target_race_date: _date
    events: tuple[JRAHistoricalPastRaceReference, ...]
    proven_zero_history: bool

    def __post_init__(self) -> None:
        if (
            type(self.target_external_race_id) is not str or type(self.target_external_entry_id) is not str
            or type(self.target_external_horse_id) is not str or type(self.target_race_date) is not _date
            or type(self.events) is not tuple or type(self.proven_zero_history) is not bool
            or any(type(event) is not JRAHistoricalPastRaceReference for event in self.events)
            or self.proven_zero_history != (self.events == ())
        ):
            raise JRAHistoricalPastRaceDiscoveryValidationError("historical discovery is invalid")


def _reference(row: _Tag, base_url: str) -> JRAHistoricalPastRaceReference:
    cells = _row_cells(row)
    race_date = _parse_date(_node_text(cells[0], "official accessU event date"), "official accessU event date")
    anchor = _access_s_anchor(row, base_url)
    fingerprint = _row_fingerprint(cells)
    if _is_non_start(cells, anchor):
        return JRAHistoricalPastRaceReference(JRAHistoricalEventKind.PROVEN_NON_START, race_date, f"accessu:event:{fingerprint}", None, None)
    started, unsupported = _is_started(cells)
    if not started:
        if _text(cells[7].get_text(" ", strip=True)) in _NON_START_FINISH and anchor is None:
            return JRAHistoricalPastRaceReference(JRAHistoricalEventKind.PROVEN_NON_START, race_date, f"accessu:event:{fingerprint}", None, None)
        raise _validation("official accessU event is unclassified")
    if anchor is not None and not unsupported:
        identity, canonical = anchor
        if _result_date(canonical, identity) != race_date:
            raise _validation("official accessU row date disagrees with result navigation")
        return JRAHistoricalPastRaceReference(
            JRAHistoricalEventKind.JRA_ACTUAL_START,
            race_date,
            f"jra:event:{identity.external_race_id}",
            identity,
            canonical,
        )
    if anchor is None and _text(cells[1].get_text(" ", strip=True)) in _JRA_PLACES:
        raise _validation("official accessU JRA start is missing result navigation")
    return JRAHistoricalPastRaceReference(
        JRAHistoricalEventKind.UNSUPPORTED_ACTUAL_START if unsupported else JRAHistoricalEventKind.NON_JRA_ACTUAL_START,
        race_date,
        f"accessu:event:{fingerprint}",
        None,
        None,
    )


def _aggregate_table(cell: _Tag, caption: str) -> int | None:
    table = _one(cell.select(":scope > table.basic.narrow"), f"{caption} aggregate table")
    caption_node = _one(table.select("caption.simple .main"), f"{caption} aggregate caption")
    if _node_text(caption_node, f"{caption} aggregate caption") != caption:
        raise _validation("official accessU aggregate caption is invalid")
    no_data = [node for node in table.find_all(["td", "th"]) if _text(node.get_text(" ", strip=True)) == _NO_DATA]
    if no_data:
        if len(no_data) != 1 or table.find("thead") is not None:
            raise _validation("official accessU aggregate no-data state is invalid")
        body = _one(table.find_all("tbody", recursive=False), f"{caption} aggregate body")
        row = _one(body.find_all("tr", recursive=False), f"{caption} aggregate no-data row")
        if tuple(row.find_all("td", recursive=False)) != tuple(no_data):
            raise _validation("official accessU aggregate no-data state is invalid")
        return None
    head = _one(table.find_all("thead", recursive=False), f"{caption} aggregate heading")
    header_row = _one(head.find_all("tr", recursive=False), f"{caption} aggregate heading row")
    headings = tuple(_text(item.get_text(" ", strip=True)) for item in header_row.find_all("th", recursive=False))
    if headings != _AGGREGATE_HEADINGS:
        raise _validation("official accessU aggregate headings are invalid")
    body = _one(table.find_all("tbody", recursive=False), f"{caption} aggregate body")
    row = _one(body.find_all("tr", recursive=False), f"{caption} aggregate data row")
    cells = tuple(row.find_all("td", recursive=False))
    if len(cells) != len(_AGGREGATE_HEADINGS):
        raise _validation("official accessU aggregate data columns are invalid")
    values = tuple(_text(cell.get_text(" ", strip=True)) for cell in cells)
    counts = tuple(_integer(values[index], f"{caption} {_AGGREGATE_HEADINGS[index]}") for index in range(5))
    if sum(counts[:4]) != counts[4]:
        raise _validation("official accessU aggregate arithmetic disagrees")
    return counts[4]


def _aggregate(soup: _BeautifulSoup) -> tuple[int | None, int | None]:
    section = _one((node for node in soup.select("li#result_unit") if _node_text(_one(node.select(":scope > div.contents_header > h2"), "official accessU aggregate heading"), "official accessU aggregate heading") == "レース条件別成績"), "official accessU aggregate section")
    race_data = _one(section.select(":scope > div.race_data.mt10"), "official accessU aggregate data")
    grid = _one(race_data.select(":scope > div.layout_grid"), "official accessU aggregate grid")
    return (
        _aggregate_table(_one(grid.select(":scope > div.cell.left"), "flat aggregate cell"), "平地レース合計"),
        _aggregate_table(_one(grid.select(":scope > div.cell.right"), "obstacle aggregate cell"), "障害レース合計"),
    )


def _zero_state(container: _Tag) -> bool:
    tables = container.select("table")
    messages = [node for node in container.find_all("strong") if _text(node.get_text(" ", strip=True)) == _NO_DATA]
    return not tables and len(messages) == 1


def discover_jra_historical_past_race_history(
    *,
    target_track_record: _HistoricalInputSourceRecord,
    target_entry_record: _HistoricalInputSourceRecord,
    horse_history_response: _JRASuppliedOfficialResponse,
) -> JRAHistoricalPastRaceDiscovery:
    """Discover a complete ordered JRA accessU history only when count proof succeeds."""

    target_race, entry_id, horse, target_date, scheduled = _target(target_track_record, target_entry_record)
    if type(horse_history_response) is not _JRASuppliedOfficialResponse:
        raise _validation("horse_history_response must be exact JRASuppliedOfficialResponse")
    try:
        response_horse = _parse_jra_horse_profile_url_identity(horse_history_response.response_url)
    except _JRAOfficialIdentityValidationError as error:
        raise _validation("horse_history_response must be accessU horse-history evidence") from error
    if response_horse != horse:
        raise _validation("accessU horse identity disagrees with target entry")
    if horse_history_response.observed_at > scheduled:
        raise _validation("accessU observation is after target scheduled start")
    soup = _document(horse_history_response)
    if _continuation(soup):
        raise _validation("accessU continuation is unsupported")
    flat, obstacle = _aggregate(soup)
    container = _history_container(soup)
    if _zero_state(container):
        if (flat, obstacle) not in {(None, None), (0, 0)}:
            raise _validation("accessU zero history disagrees with aggregate counts")
        return JRAHistoricalPastRaceDiscovery(target_race.external_race_id, entry_id, horse.external_horse_id, target_date, (), True)
    if flat is None or obstacle is None:
        raise _validation("accessU history and aggregate no-data states conflict")
    table = _history_table(container)
    body = _one(table.find_all("tbody", recursive=False), "official accessU history body")
    rows = tuple(body.find_all("tr", recursive=False))
    if not rows:
        raise _validation("official accessU history rows are missing")
    events = tuple(_reference(row, horse_history_response.response_url) for row in rows)
    if len({event.provider_event_id for event in events}) != len(events):
        raise _validation("accessU historical event is duplicated")
    if any(event.race_date >= target_date for event in events):
        raise _validation("accessU historical event is not before target race")
    if any(events[index].race_date < events[index + 1].race_date for index in range(len(events) - 1)):
        raise _validation("accessU historical chronology is out of order")
    actual_count = sum(event.event_kind is not JRAHistoricalEventKind.PROVEN_NON_START for event in events)
    if actual_count != flat + obstacle:
        raise _validation("accessU displayed actual-start count disagrees with aggregate total")
    return JRAHistoricalPastRaceDiscovery(target_race.external_race_id, entry_id, horse.external_horse_id, target_date, events, False)


if "annotations" in globals():
    del annotations
