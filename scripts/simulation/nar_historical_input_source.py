"""Pure normalization of one supplied official NAR DebaTable response."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass
from datetime import date as _date, datetime as _datetime
from decimal import Decimal as _Decimal, InvalidOperation as _InvalidOperation
import hashlib as _hashlib
import re as _re
from typing import Literal as _Literal
from unicodedata import normalize as _normalize
from urllib.parse import parse_qsl as _parse_qsl, urljoin as _urljoin, urlsplit as _urlsplit
from zoneinfo import ZoneInfo as _ZoneInfo

from bs4 import BeautifulSoup as _BeautifulSoup
from bs4.element import Tag as _Tag

from scripts.simulation.historical_input_source_records import (
    HistoricalInputSourceConflictError as _HistoricalInputSourceConflictError,
    HistoricalInputSourceError as _HistoricalInputSourceError,
    HistoricalInputSourceRecord as _HistoricalInputSourceRecord,
    HistoricalInputSourceValidationError as _HistoricalInputSourceValidationError,
    validate_historical_input_source_record_set as _validate_historical_input_source_record_set,
)
from scripts.simulation.historical_input_evidence import (
    HistoricalInputEvidenceReference as _HistoricalInputEvidenceReference,
)

if "annotations" in globals():
    del annotations


class NarHistoricalInputSourceError(_HistoricalInputSourceError):
    """Base error for the supplied NAR normalization boundary."""


class NarHistoricalInputSourceValidationError(
    NarHistoricalInputSourceError,
    _HistoricalInputSourceValidationError,
):
    """Raised when supplied NAR input is malformed or ambiguous."""


class NarHistoricalInputSourceUnsupportedError(NarHistoricalInputSourceError):
    """Raised for a recognized NAR page or state outside initial c1b support."""


@_dataclass(frozen=True, slots=True)
class NarSuppliedOfficialResponse:
    response_url: str
    response_body: bytes
    charset: _Literal["utf-8"]
    observed_at: _datetime

    def __post_init__(self) -> None:
        if type(self.response_url) is not str or not self.response_url:
            raise NarHistoricalInputSourceValidationError(
                "response_url must be a non-empty str",
            )
        if type(self.response_body) is not bytes:
            raise NarHistoricalInputSourceValidationError(
                "response_body must be exact bytes",
            )
        if type(self.charset) is not str or self.charset != "utf-8":
            raise NarHistoricalInputSourceValidationError(
                "charset must be exact utf-8",
            )
        if type(self.observed_at) is not _datetime:
            raise NarHistoricalInputSourceValidationError(
                "observed_at must be exact datetime",
            )
        try:
            aware = (
                self.observed_at.tzinfo is not None
                and self.observed_at.utcoffset() is not None
            )
        except (TypeError, ValueError, OverflowError) as error:
            raise NarHistoricalInputSourceValidationError(
                "observed_at must be timezone-aware",
            ) from error
        if not aware:
            raise NarHistoricalInputSourceValidationError(
                "observed_at must be timezone-aware",
            )


_HOST = "www.keiba.go.jp"
_PATH = "/KeibaWeb/TodayRaceInfo/DebaTable"
_QUERY_KEYS = frozenset({"k_babaCode", "k_raceDate", "k_raceNo"})
_HORSE_PATH = "/KeibaWeb/DataRoom/HorseMarkInfo"
_HORSE_QUERY_KEY = "k_lineageLoginCode"
_DECIMAL_TOKEN = _re.compile(r"[1-9][0-9]*\Z")
_DATE_TOKEN = _re.compile(r"[0-9]{4}/[0-9]{2}/[0-9]{2}\Z")
_PERCENT_ESCAPE = _re.compile(r"%(?:[0-9A-Fa-f]{2})")
_H4_DATE = _re.compile(r"([0-9]{4})\u5e74\s*([0-9]{1,2})\u6708\s*([0-9]{1,2})\u65e5")
_H4_RACE = _re.compile(r"\u7b2c\s*([0-9]+)\s*\u7af6\u8d70")
_H4_TIME = _re.compile(r"([0-9]{1,2}):([0-9]{2})\s*\u767a\u8d70")
_WEEKDAY_PREFIX = _re.compile(r"^(?:\([^)]*\)|\uff08[^\uff09]*\uff09)\s*")
_SURFACE = _re.compile(r"(\u30c0\u30fc\u30c8|\u829d|\u969c\u5bb3)")
_DISTANCE = _re.compile(
    r"(?:\u30c0\u30fc\u30c8|\u829d|\u969c\u5bb3)\s*([1-9][0-9]*)\s*(?:m|\uff4d)",
)
_WEATHER = _re.compile(r"\u5929\u5019\s*[:\uff1a]\s*([^\s]+)")
_CONDITION = _re.compile(r"\u99ac\u5834\s*[:\uff1a]\s*([^\s]+)")
_ODDS = _re.compile(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?\Z")
_CANCELLATION_MARKERS = (
    "\u53d6\u6d88",
    "\u9664\u5916",
    "\u51fa\u8d70\u53d6\u6d88",
    "\u7af6\u8d70\u9664\u5916",
)


def _validation(message: str) -> NarHistoricalInputSourceValidationError:
    return NarHistoricalInputSourceValidationError(message)


def _display_text(value: object) -> str:
    if type(value) is not str:
        raise _validation("display text must be str")
    return _re.sub(r"\s+", " ", _normalize("NFC", value)).strip()


def _required_text(value: object, name: str) -> str:
    normalized = _display_text(value)
    if not normalized:
        raise _validation(f"{name} must not be empty")
    return normalized


def _has_bad_percent_encoding(value: str) -> bool:
    return any(
        value[index] == "%" and _PERCENT_ESCAPE.match(value, index) is None
        for index in range(len(value))
    )


def _parse_decimal_token(value: str, name: str) -> str:
    if _DECIMAL_TOKEN.fullmatch(value) is None:
        raise _validation(f"{name} must be a positive canonical decimal token")
    return value


def _parse_positive_int(value: str, name: str) -> int:
    token = _parse_decimal_token(value, name)
    try:
        return int(token)
    except ValueError as error:
        raise _validation(f"{name} is invalid") from error


def _canonical_url(value: str) -> tuple[str, _date, str, str]:
    if value != _normalize("NFC", value) or value != value.strip():
        raise _validation("response_url must already be NFC-normalized without whitespace")
    if any(character.isspace() or ord(character) < 32 for character in value):
        raise _validation("response_url contains whitespace or control characters")
    try:
        parsed = _urlsplit(value)
        port = parsed.port
    except ValueError as error:
        raise _validation("response_url is invalid") from error
    if "+" in parsed.query or _has_bad_percent_encoding(parsed.query):
        raise _validation("response_url query encoding is ambiguous or malformed")
    if parsed.scheme.lower() != "https":
        raise _validation("response_url must use https")
    if parsed.username is not None or parsed.password is not None or parsed.fragment:
        raise _validation("response_url must not contain credentials or fragment")
    if (parsed.hostname or "").lower() != _HOST or port not in (None, 443):
        raise _validation("response_url host or port is invalid")
    if parsed.path != _PATH:
        raise NarHistoricalInputSourceUnsupportedError("NAR page kind is unsupported")
    if not parsed.query:
        raise _validation("response_url query is required")
    try:
        pairs = _parse_qsl(
            parsed.query,
            keep_blank_values=True,
            strict_parsing=True,
            encoding="utf-8",
            errors="strict",
        )
    except ValueError as error:
        raise _validation("response_url query is invalid") from error
    values: dict[str, str] = {}
    for key, item in pairs:
        if not key or not item:
            raise _validation("response_url query key or value is invalid")
        if key != _normalize("NFC", key) or item != _normalize("NFC", item):
            raise _validation("response_url query key or value is invalid")
        if key not in _QUERY_KEYS or key in values:
            raise _validation("response_url query keys are invalid")
        values[key] = item
    if set(values) != _QUERY_KEYS:
        raise _validation("response_url query keys are incomplete")
    race_date_text = values["k_raceDate"]
    if _DATE_TOKEN.fullmatch(race_date_text) is None:
        raise _validation("k_raceDate must be YYYY/MM/DD")
    try:
        race_date = _date.fromisoformat(race_date_text.replace("/", "-"))
    except ValueError as error:
        raise _validation("k_raceDate must be a real date") from error
    baba_code = _parse_decimal_token(values["k_babaCode"], "k_babaCode")
    race_no = _parse_decimal_token(values["k_raceNo"], "k_raceNo")
    canonical = (
        f"https://{_HOST}{_PATH}?k_babaCode={baba_code}"
        f"&k_raceDate={race_date_text.replace('/', '%2F')}&k_raceNo={race_no}"
    )
    return canonical, race_date, baba_code, race_no


def _canonical_horse_identity(value: object) -> str:
    if type(value) is not str:
        raise _validation("horse href must be str")
    if value != _normalize("NFC", value) or value != value.strip():
        raise _validation("horse href must already be NFC-normalized without whitespace")
    if any(character.isspace() or ord(character) < 32 for character in value):
        raise _validation("horse href contains whitespace or control characters")
    try:
        raw = _urlsplit(value)
        raw_port = raw.port
    except ValueError as error:
        raise _validation("horse href is invalid") from error
    if raw.username is not None or raw.password is not None or raw.fragment:
        raise _validation("horse href must not contain credentials or fragment")
    if raw.scheme:
        if raw.scheme.lower() != "https" or (raw.hostname or "").lower() != _HOST:
            raise _validation("horse href host or scheme is invalid")
        if raw_port not in (None, 443):
            raise _validation("horse href port is invalid")
        candidate = value
    else:
        if raw.netloc:
            raise _validation("horse href host is invalid")
        candidate = _urljoin(f"https://{_HOST}{_PATH}", value)
    try:
        parsed = _urlsplit(candidate)
        port = parsed.port
    except ValueError as error:
        raise _validation("horse href is invalid") from error
    if "+" in parsed.query or _has_bad_percent_encoding(parsed.query):
        raise _validation("horse href query encoding is ambiguous or malformed")
    if (
        parsed.scheme != "https"
        or parsed.hostname != _HOST
        or port not in (None, 443)
        or parsed.path != _HORSE_PATH
        or not parsed.query
    ):
        raise _validation("horse href is invalid")
    try:
        pairs = _parse_qsl(
            parsed.query,
            keep_blank_values=True,
            strict_parsing=True,
            encoding="utf-8",
            errors="strict",
        )
    except ValueError as error:
        raise _validation("horse href query is invalid") from error
    if len(pairs) != 1:
        raise _validation("horse href query is invalid")
    key, token = pairs[0]
    if (
        key != _HORSE_QUERY_KEY
        or token != _normalize("NFC", token)
        or _DECIMAL_TOKEN.fullmatch(token) is None
    ):
        raise _validation("horse lineage identity is invalid")
    return f"nar:horse:{token}"


def _require_utf8_document(response: NarSuppliedOfficialResponse) -> _BeautifulSoup:
    try:
        html = response.response_body.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise _validation("response_body is not strict UTF-8") from error
    soup = _BeautifulSoup(html, "html.parser")
    declarations = [
        node
        for node in soup.find_all("meta")
        if node.get("charset") == "utf-8"
    ]
    if len(declarations) != 1:
        raise _validation("document must declare exactly one utf-8 charset")
    return soup


def _header_card(soup: _BeautifulSoup) -> _Tag:
    cards = [
        card
        for card in soup.select("article.raceCard")
        if len(
            card.select(
                ".chartNavi.trackNameNavi a.cNaviBtn.courseBtn.active",
            ),
        )
        == 1
        and len(card.find_all("h4", recursive=True)) == 1
        and len(card.select("section.raceTitle ul.dataArea > li:first-child")) == 1
    ]
    if len(cards) != 1:
        raise _validation("target header race card is missing or ambiguous")
    return cards[0]


def _one(nodes: list[_Tag], name: str) -> _Tag:
    if len(nodes) != 1:
        raise _validation(f"{name} is missing or ambiguous")
    return nodes[0]


def _h4_facts(
    card: _Tag,
    expected_date: _date,
    expected_race_no: str,
    semantic_place: str,
) -> _datetime:
    h4 = _one(card.find_all("h4", recursive=True), "target h4")
    text = _display_text(h4.get_text(" ", strip=True))
    date_match = _H4_DATE.search(text)
    race_match = _H4_RACE.search(text)
    time_match = _H4_TIME.search(text)
    if date_match is None or race_match is None or time_match is None:
        raise _validation("target h4 facts are incomplete")
    try:
        h4_date = _date(*(int(part) for part in date_match.groups()))
    except ValueError as error:
        raise _validation("target h4 date is invalid") from error
    if (
        h4_date != expected_date
        or _parse_decimal_token(race_match.group(1), "h4 race number")
        != expected_race_no
    ):
        raise _validation("target h4 identity does not match URL")
    place_segment = _WEEKDAY_PREFIX.sub("", text[date_match.end() : race_match.start()])
    compact_place = _normalize(
        "NFC",
        "".join(character for character in place_segment if not character.isspace()),
    )
    if compact_place != semantic_place:
        raise _validation("target h4 place does not match active course")
    hour, minute = (int(part) for part in time_match.groups())
    if hour > 23 or minute > 59:
        raise _validation("target h4 start time is invalid")
    return _datetime(
        expected_date.year,
        expected_date.month,
        expected_date.day,
        hour,
        minute,
        tzinfo=_ZoneInfo("Asia/Tokyo"),
    )


def _track_values(
    card: _Tag,
    race_date: _date,
    race_no: str,
) -> dict[str, object]:
    active = _one(
        card.select(".chartNavi.trackNameNavi a.cNaviBtn.courseBtn.active"),
        "active course",
    )
    place = _required_text(active.get_text(" ", strip=True), "active course")
    scheduled_start_at = _h4_facts(card, race_date, race_no, place)
    headings = card.select("section.raceTitle h3")
    if len(headings) > 1:
        raise _validation("race_name is ambiguous")
    race_name = (
        None
        if not headings
        else _required_text(headings[0].get_text(" ", strip=True), "race_name")
    )
    facts = _one(
        card.select("section.raceTitle ul.dataArea > li:first-child"),
        "race facts",
    )
    fact_text = _display_text(facts.get_text(" ", strip=True))
    surfaces = _SURFACE.findall(fact_text)
    distance = _DISTANCE.findall(fact_text)
    weather = _WEATHER.findall(fact_text)
    condition = _CONDITION.findall(fact_text)
    if (
        len(surfaces) != 1
        or len(distance) != 1
        or len(weather) != 1
        or len(condition) != 1
    ):
        raise _validation("race facts are missing or ambiguous")
    return {
        "target_race_date": race_date,
        "scheduled_start_at": scheduled_start_at,
        "place": place,
        "distance_m": _parse_positive_int(distance[0], "distance_m"),
        "track": surfaces[0],
        "track_condition": _required_text(condition[0], "track_condition"),
        "race_name": race_name,
        "race_class": None,
        "weather": _required_text(weather[0], "weather"),
    }


def _direct_text(node: _Tag) -> str:
    values = tuple(
        str(item)
        for item in node.find_all(string=True, recursive=False)
        if str(item).strip()
    )
    return _required_text(" ".join(values), "jockey")


def _horse_rows(soup: _BeautifulSoup) -> tuple[_Tag, ...]:
    tables = []
    for card in soup.select("article.raceCard"):
        for table in card.select("section.cardTable table"):
            if table.find("td", class_="horseNum") is not None:
                tables.append(table)
    table = _one(tables, "entry table")
    rows = tuple(
        row
        for row in table.find_all("tr")
        if row.find_all("td", class_="horseNum", recursive=False)
    )
    if not rows:
        raise _validation("entry rows are missing")
    return rows


def _row_values(
    row: _Tag,
    external_race_id: str,
) -> tuple[int, str, str, str, _Decimal]:
    row_text = _display_text(row.get_text(" ", strip=True))
    if any(marker in row_text for marker in _CANCELLATION_MARKERS):
        raise NarHistoricalInputSourceUnsupportedError(
            "cancelled NAR row is unsupported",
        )
    horse_cell = _one(
        row.find_all("td", class_="horseNum", recursive=False),
        "horseNum",
    )
    horse_no = _parse_positive_int(
        _required_text(horse_cell.get_text(" ", strip=True), "horseNum"),
        "horseNum",
    )
    horse_anchor = _one(row.select("a.horseName[href]"), "horseName")
    external_horse_id = _canonical_horse_identity(horse_anchor.get("href"))
    jockey = _direct_text(_one(row.select("a.jockeyName"), "jockeyName"))
    odds_spans = [
        span
        for span in row.select("td.odds_weight span")
        if any(
            str(css_class).startswith("odds_")
            for css_class in span.get("class", ())
        )
    ]
    odds_text = _required_text(
        _one(odds_spans, "win odds").get_text(" ", strip=True),
        "win odds",
    )
    if _ODDS.fullmatch(odds_text) is None:
        raise NarHistoricalInputSourceUnsupportedError(
            "win odds representation is unsupported",
        )
    try:
        odds = _Decimal(odds_text)
    except _InvalidOperation as error:
        raise _validation("win odds is invalid") from error
    if not odds.is_finite() or odds <= 0:
        raise NarHistoricalInputSourceUnsupportedError(
            "win odds must be positive",
        )
    return (
        horse_no,
        f"{external_race_id}:entry:{horse_no}",
        external_horse_id,
        jockey,
        odds,
    )


def normalize_nar_historical_input_source_records(
    *,
    response: NarSuppliedOfficialResponse,
) -> tuple[_HistoricalInputSourceRecord, ...]:
    """Normalize one supplied official DebaTable response without side effects."""

    if type(response) is not NarSuppliedOfficialResponse:
        raise _validation("response must be NarSuppliedOfficialResponse")
    canonical_url, race_date, baba_code, race_no = _canonical_url(
        response.response_url,
    )
    response_sha256 = _hashlib.sha256(response.response_body).hexdigest()
    def evidence(role: str) -> tuple[_HistoricalInputEvidenceReference, ...]:
        return (
            _HistoricalInputEvidenceReference(
                role,
                canonical_url,
                response_sha256,
                None,
                response.observed_at,
            ),
        )
    soup = _require_utf8_document(response)
    card = _header_card(soup)
    external_race_id = f"nar:{race_date:%Y%m%d}:{baba_code}:{race_no}"
    track = _HistoricalInputSourceRecord(
        record_kind="track",
        organization="NAR",
        source_system="nar_official",
        external_race_id=external_race_id,
        external_entry_id=None,
        provider_record_id=None,
        record_values=_track_values(card, race_date, race_no),
        evidence=evidence("track"),
    )
    parsed_rows = tuple(
        _row_values(row, external_race_id)
        for row in _horse_rows(soup)
    )
    if len({item[0] for item in parsed_rows}) != len(parsed_rows):
        raise _validation("duplicate horseNum")
    records: list[_HistoricalInputSourceRecord] = [track]
    for horse_no, entry_id, external_horse_id, jockey, odds in sorted(parsed_rows):
        common = {
            "organization": "NAR",
            "source_system": "nar_official",
            "external_race_id": external_race_id,
            "external_entry_id": entry_id,
            "provider_record_id": None,
        }
        records.extend(
            (
                _HistoricalInputSourceRecord(
                    record_kind="entry",
                    record_values={
                        "external_entry_id": entry_id,
                        "external_horse_id": external_horse_id,
                        "horse_no": horse_no,
                    },
                    evidence=evidence("entry"),
                    **common,
                ),
                _HistoricalInputSourceRecord(
                    record_kind="jockey",
                    record_values={
                        "external_entry_id": entry_id,
                        "jockey": jockey,
                    },
                    evidence=evidence("jockey"),
                    **common,
                ),
                _HistoricalInputSourceRecord(
                    record_kind="odds_win",
                    record_values={
                        "external_entry_id": entry_id,
                        "horse_no": horse_no,
                        "win_odds": odds,
                    },
                    evidence=evidence("odds_win"),
                    **common,
                ),
            ),
        )
    try:
        return _validate_historical_input_source_record_set(records=tuple(records))
    except (
        _HistoricalInputSourceValidationError,
        _HistoricalInputSourceConflictError,
    ):
        raise
