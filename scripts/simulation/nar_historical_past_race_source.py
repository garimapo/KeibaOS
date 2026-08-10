"""Pure normalization of one supplied NAR HorseMarkInfo/RaceMarkTable pair."""

from __future__ import annotations

from datetime import date as _date
from decimal import Decimal as _Decimal, InvalidOperation as _InvalidOperation
import hashlib as _hashlib
import re as _re
from unicodedata import category as _category, normalize as _normalize
from urllib.parse import parse_qsl as _parse_qsl, urljoin as _urljoin, urlsplit as _urlsplit

from bs4 import BeautifulSoup as _BeautifulSoup
from bs4.element import Tag as _Tag

from scripts.simulation.historical_input_evidence import (
    HistoricalInputEvidenceReference as _HistoricalInputEvidenceReference,
)
from scripts.simulation.historical_input_source_records import (
    HistoricalInputSourceRecord as _HistoricalInputSourceRecord,
)
from scripts.simulation.nar_historical_input_source import (
    NarHistoricalInputSourceUnsupportedError as _NarHistoricalInputSourceUnsupportedError,
    NarHistoricalInputSourceValidationError as _NarHistoricalInputSourceValidationError,
    NarSuppliedOfficialResponse as _NarSuppliedOfficialResponse,
)


_HORSE_HOSTS = frozenset({"www.keiba.go.jp", "www2.keiba.go.jp"})
_RACE_HOST = "www.keiba.go.jp"
_HORSE_PATH = "/KeibaWeb/DataRoom/HorseMarkInfo"
_RACE_PATH = "/KeibaWeb/TodayRaceInfo/RaceMarkTable"
_LINEAGE_KEY = "k_lineageLoginCode"
_RACE_KEYS = frozenset({"k_babaCode", "k_raceDate", "k_raceNo"})
_LINEAGE = _re.compile(r"[1-9][0-9]*\Z")
_DATE = _re.compile(r"[0-9]{4}/[0-9]{2}/[0-9]{2}\Z")
_TARGET_RACE = _re.compile(r"nar:([0-9]{8}):([1-9][0-9]*):([1-9][0-9]*)\Z")
_DECIMAL = _re.compile(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?\Z")
_POSITIVE = _re.compile(r"[1-9][0-9]*\Z")
_TIME = _re.compile(r"[0-9]+:[0-5][0-9]\.[0-9]+\Z")
_WEIGHT = _re.compile(r"([1-9][0-9]*)\s*\(\s*([+-]?[0-9]+)\s*\)\Z")
_PASSING = _re.compile(r"[1-9][0-9]*(?:-[1-9][0-9]*)*\Z")
_PERCENT = _re.compile(r"%(?:[0-9A-Fa-f]{2})")
_H4_DATE = _re.compile(r"([0-9]{4})年\s*([0-9]{1,2})月\s*([0-9]{1,2})日")
_H4_RACE = _re.compile(r"第\s*([0-9]+)\s*競走")
_WEEKDAY = _re.compile(r"^(?:\([^)]*\)|（[^）]*）)\s*")
_SURFACE_DISTANCE = _re.compile(r"(ダート|芝|障害)\s*([1-9][0-9]*)\s*(?:m|ｍ)")
_WEATHER = _re.compile(r"天候\s*[:：]\s*([^\s]+)")
_CONDITION = _re.compile(r"馬場\s*[:：]\s*([^\s]+)")
_CORNER_LABEL = _re.compile(r"([１２３４])(?:コーナー|角)\Z")
_CORNER_ORDINAL = {"１": 1, "２": 2, "３": 3, "４": 4}
_CANCELLATIONS = ("取消", "除外", "中止", "失格", "降着")
_HISTORY_HEADINGS = (
    "年月日",
    "競馬場",
    "R",
    "競走名",
    "格組",
    "距離",
    "天候・馬場",
    "人気",
    "着順",
    "タイム",
    "差",
    "体重",
    "騎手(所属)",
)


def _validation(message: str) -> _NarHistoricalInputSourceValidationError:
    return _NarHistoricalInputSourceValidationError(message)


def _unsupported(message: str) -> _NarHistoricalInputSourceUnsupportedError:
    return _NarHistoricalInputSourceUnsupportedError(message)


def _display(value: object) -> str:
    if type(value) is not str:
        raise _validation("display text must be str")
    return _re.sub(r"\s+", " ", _normalize("NFC", value)).strip()


def _required(value: object, name: str) -> str:
    result = _display(value)
    if not result:
        raise _validation(f"{name} is missing")
    return result


def _one(nodes: list[_Tag], name: str) -> _Tag:
    if len(nodes) != 1:
        raise _validation(f"{name} is missing or ambiguous")
    return nodes[0]


def _bad_percent(value: str) -> bool:
    return any(value[index] == "%" and _PERCENT.match(value, index) is None for index in range(len(value)))


def _url_parts(value: object, name: str):
    if type(value) is not str or not value:
        raise _validation(f"{name} must be a non-empty str")
    if value != _normalize("NFC", value) or value != value.strip():
        raise _validation(f"{name} must be NFC-normalized without surrounding whitespace")
    if any(character.isspace() or _category(character) == "Cc" for character in value):
        raise _validation(f"{name} contains whitespace or control characters")
    try:
        parsed = _urlsplit(value)
        _ = parsed.port
    except ValueError as error:
        raise _validation(f"{name} is invalid") from error
    if parsed.username is not None or parsed.password is not None or parsed.fragment:
        raise _validation(f"{name} contains credentials or fragment")
    if "+" in parsed.query or _bad_percent(parsed.query):
        raise _validation(f"{name} query encoding is ambiguous or malformed")
    return parsed


def _query(parsed, keys: frozenset[str], name: str) -> dict[str, str]:
    if not parsed.query:
        raise _validation(f"{name} query is required")
    try:
        pairs = _parse_qsl(
            parsed.query,
            keep_blank_values=True,
            strict_parsing=True,
            encoding="utf-8",
            errors="strict",
        )
    except ValueError as error:
        raise _validation(f"{name} query is invalid") from error
    values: dict[str, str] = {}
    for key, item in pairs:
        if not key or not item or key != _normalize("NFC", key) or item != _normalize("NFC", item):
            raise _validation(f"{name} query key or value is invalid")
        if key not in keys or key in values:
            raise _validation(f"{name} query keys are invalid")
        values[key] = item
    if set(values) != keys:
        raise _validation(f"{name} query keys are incomplete")
    return values


def _parse_date(value: str, name: str) -> _date:
    if _DATE.fullmatch(value) is None:
        raise _validation(f"{name} must be YYYY/MM/DD")
    try:
        return _date.fromisoformat(value.replace("/", "-"))
    except ValueError as error:
        raise _validation(f"{name} must be a real date") from error


def _token(value: str, name: str) -> str:
    if _LINEAGE.fullmatch(value) is None:
        raise _validation(f"{name} must be a positive canonical decimal token")
    return value


def _positive_int(value: str, name: str) -> int:
    token = _token(value, name)
    try:
        return int(token)
    except ValueError as error:
        raise _validation(f"{name} is invalid") from error


def _canonical_horse_url(value: object, *, base_url: str | None = None) -> tuple[str, str]:
    parsed = _url_parts(value, "HorseMarkInfo URL")
    if parsed.scheme:
        if parsed.scheme.lower() != "https" or (parsed.hostname or "").lower() not in _HORSE_HOSTS:
            raise _validation("HorseMarkInfo URL host or scheme is invalid")
        if parsed.port not in (None, 443):
            raise _validation("HorseMarkInfo URL port is invalid")
        candidate = str(value)
    else:
        if parsed.netloc or base_url is None:
            raise _validation("HorseMarkInfo URL host is invalid")
        candidate = _urljoin(base_url, str(value))
    resolved = _url_parts(candidate, "HorseMarkInfo URL")
    host = (resolved.hostname or "").lower()
    if (
        resolved.scheme.lower() != "https"
        or host not in _HORSE_HOSTS
        or resolved.port not in (None, 443)
        or resolved.path != _HORSE_PATH
    ):
        raise _validation("HorseMarkInfo URL is invalid")
    values = _query(resolved, frozenset({_LINEAGE_KEY}), "HorseMarkInfo URL")
    lineage = _token(values[_LINEAGE_KEY], "k_lineageLoginCode")
    return f"https://{host}{_HORSE_PATH}?{_LINEAGE_KEY}={lineage}", lineage


def _canonical_race_url(value: object, *, base_url: str | None = None) -> tuple[str, _date, str, str]:
    parsed = _url_parts(value, "RaceMarkTable URL")
    if parsed.scheme:
        if parsed.scheme.lower() != "https" or (parsed.hostname or "").lower() not in _HORSE_HOSTS:
            raise _validation("RaceMarkTable URL host or scheme is invalid")
        if parsed.port not in (None, 443):
            raise _validation("RaceMarkTable URL port is invalid")
        candidate = str(value)
    else:
        if parsed.netloc or base_url is None:
            raise _validation("RaceMarkTable URL host is invalid")
        candidate = _urljoin(base_url, str(value))
    resolved = _url_parts(candidate, "RaceMarkTable URL")
    host = (resolved.hostname or "").lower()
    if (
        resolved.scheme.lower() != "https"
        or host not in _HORSE_HOSTS
        or resolved.port not in (None, 443)
        or resolved.path != _RACE_PATH
    ):
        raise _validation("RaceMarkTable URL is invalid")
    values = _query(resolved, _RACE_KEYS, "RaceMarkTable URL")
    race_date = _parse_date(values["k_raceDate"], "k_raceDate")
    baba_code = _token(values["k_babaCode"], "k_babaCode")
    race_no = _token(values["k_raceNo"], "k_raceNo")
    canonical = (
        f"https://{host}{_RACE_PATH}?k_babaCode={baba_code}"
        f"&k_raceDate={race_date:%Y%%2F%m%%2F%d}&k_raceNo={race_no}"
    )
    return canonical, race_date, baba_code, race_no


def _canonical_supplied_race_url(value: object) -> tuple[str, _date, str, str]:
    canonical, race_date, baba_code, race_no = _canonical_race_url(value)
    if not canonical.startswith(f"https://{_RACE_HOST}/"):
        raise _validation("RaceMarkTable supplied host is invalid")
    return canonical, race_date, baba_code, race_no


def _document(response: _NarSuppliedOfficialResponse) -> _BeautifulSoup:
    try:
        html = response.response_body.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise _validation("response_body is not strict UTF-8") from error
    soup = _BeautifulSoup(html, "html.parser")
    declarations = [
        node
        for node in soup.find_all("meta")
        if isinstance(node.get("charset"), str) and node.get("charset").lower() == "utf-8"
    ]
    if len(declarations) != 1:
        raise _validation("document must declare exactly one utf-8 charset")
    return soup


def _target_identity(record: object) -> tuple[_date, str, str, str, str]:
    if type(record) is not _HistoricalInputSourceRecord:
        raise _validation("target_entry_record must be HistoricalInputSourceRecord")
    if record.record_kind != "entry" or record.organization != "NAR" or record.source_system != "nar_official":
        raise _validation("target_entry_record is incompatible")
    if record.external_entry_id is None:
        raise _validation("target_entry_record external_entry_id is required")
    match = _TARGET_RACE.fullmatch(record.external_race_id)
    if match is None:
        raise _validation("target external_race_id is invalid")
    date_text, baba_code, race_no = match.groups()
    try:
        target_date = _date.fromisoformat(f"{date_text[:4]}-{date_text[4:6]}-{date_text[6:]}")
    except ValueError as error:
        raise _validation("target external_race_id date is invalid") from error
    expected_entry = _re.compile(rf"{_re.escape(record.external_race_id)}:entry:([1-9][0-9]*)\Z")
    entry_match = expected_entry.fullmatch(record.external_entry_id)
    if entry_match is None:
        raise _validation("target external_entry_id is invalid")
    entry_horse_no = _positive_int(entry_match.group(1), "target external_entry_id horse number")
    if entry_horse_no != record.record_values["horse_no"]:
        raise _validation("target entry horse number is inconsistent")
    horse = record.record_values["external_horse_id"]
    if type(horse) is not str:
        raise _validation("target external_horse_id is required")
    horse_match = _re.fullmatch(r"nar:horse:([1-9][0-9]*)", horse)
    if horse_match is None:
        raise _validation("target external_horse_id is invalid")
    return target_date, baba_code, race_no, record.external_entry_id, horse_match.group(1)


def _history_table(soup: _BeautifulSoup) -> _Tag:
    candidates = []
    for table in soup.select("table.HorseMarkInfo_table"):
        headings = tuple(_display(item.get_text(" ", strip=True)) for item in table.select("thead th"))
        if all(heading in headings for heading in _HISTORY_HEADINGS):
            candidates.append(table)
    return _one(candidates, "HorseMarkInfo history table")


def _history_values(row: _Tag) -> dict[str, str]:
    cells = row.find_all("td", recursive=False)
    if len(cells) != 23:
        raise _validation("HorseMarkInfo history row columns are invalid")
    values = {
        "race_date": _required(cells[0].get_text(" ", strip=True), "HorseMarkInfo race_date"),
        "place": _required(cells[1].get_text(" ", strip=True), "HorseMarkInfo place"),
        "race_no": _required(cells[2].get_text(" ", strip=True), "HorseMarkInfo race_no"),
        "race_name": _required(cells[3].get_text(" ", strip=True), "HorseMarkInfo race_name"),
        "race_class": _display(cells[4].get_text(" ", strip=True)),
        "distance": _required(cells[5].get_text(" ", strip=True), "HorseMarkInfo distance"),
        "weather": _required(cells[6].get_text(" ", strip=True), "HorseMarkInfo weather"),
        "track_condition": _required(cells[7].get_text(" ", strip=True), "HorseMarkInfo track_condition"),
        "popularity": _required(cells[12].get_text(" ", strip=True), "HorseMarkInfo popularity"),
        "finish": _required(cells[13].get_text(" ", strip=True), "HorseMarkInfo finish"),
        "race_time": _required(cells[14].get_text(" ", strip=True), "HorseMarkInfo race_time"),
        "difference": _display(cells[15].get_text(" ", strip=True)),
        "weight": _required(cells[17].get_text(" ", strip=True), "HorseMarkInfo weight"),
        "jockey": _required(cells[18].get_text(" ", strip=True), "HorseMarkInfo jockey"),
    }
    if not values["race_class"]:
        raise _unsupported("HorseMarkInfo race class is unsupported")
    return values


def _history_row(
    soup: _BeautifulSoup,
    horse_url: str,
    race_identity: tuple[_date, str, str],
) -> tuple[_Tag, dict[str, str]]:
    table = _history_table(soup)
    matches: list[tuple[_Tag, dict[str, str]]] = []
    nar_history_links = 0
    recognized_jra_rows = 0
    for row in table.select("tbody > tr"):
        links = row.select("a[href]")
        nar_links: list[tuple[_date, str, str]] = []
        jra_link = False
        for link in links:
            href = link.get("href")
            parsed = _url_parts(href, "HorseMarkInfo history navigation")
            candidate = str(href) if parsed.scheme else _urljoin(horse_url, str(href))
            resolved = _url_parts(candidate, "HorseMarkInfo history navigation")
            if resolved.path == _RACE_PATH:
                _, race_date, baba_code, race_no = _canonical_race_url(href, base_url=horse_url)
                nar_links.append((race_date, baba_code, race_no))
            elif (
                resolved.scheme.lower() == "https"
                and (resolved.hostname or "").lower() == "www.jra.go.jp"
                and resolved.path.startswith("/JRADB/")
                and bool(resolved.query)
            ):
                jra_link = True
        if len(nar_links) > 1:
            raise _validation("HorseMarkInfo history result link is ambiguous")
        if nar_links:
            nar_history_links += 1
            if jra_link:
                raise _validation("HorseMarkInfo history navigation is contradictory")
            if nar_links[0] == race_identity:
                matches.append((row, _history_values(row)))
        elif jra_link:
            recognized_jra_rows += 1
    if not matches:
        if nar_history_links == 0 and recognized_jra_rows:
            raise _unsupported("JRA history is unsupported")
        raise _validation("HorseMarkInfo history row is missing")
    if len(matches) != 1:
        raise _validation("HorseMarkInfo history row is ambiguous")
    return matches[0]


def _race_header(soup: _BeautifulSoup, race_date: _date, race_no: str) -> tuple[str, dict[str, object]]:
    h4s = [
        node
        for node in soup.find_all("h4")
        if _H4_DATE.search(_display(node.get_text(" ", strip=True))) is not None
        and _H4_RACE.search(_display(node.get_text(" ", strip=True))) is not None
    ]
    h4 = _one(h4s, "RaceMarkTable result header")
    header = _display(h4.get_text(" ", strip=True))
    date_match = _H4_DATE.search(header)
    race_match = _H4_RACE.search(header)
    assert date_match is not None and race_match is not None
    try:
        visible_date = _date(*(int(value) for value in date_match.groups()))
    except ValueError as error:
        raise _validation("RaceMarkTable visible date is invalid") from error
    if visible_date != race_date or _token(race_match.group(1), "RaceMarkTable visible race number") != race_no:
        raise _validation("RaceMarkTable visible identity disagrees with URL")
    active = _one(
        soup.select(".chartNavi.trackNameNavi a.cNaviBtn.courseBtn.active"),
        "RaceMarkTable active course",
    )
    place = _required(active.get_text(" ", strip=True), "RaceMarkTable active course")
    place_segment = _WEEKDAY.sub("", header[date_match.end() : race_match.start()])
    if _normalize("NFC", "".join(item for item in place_segment if not item.isspace())) != place:
        raise _validation("RaceMarkTable visible place disagrees with active course")
    facts = _one(soup.select("section.raceTitle ul.dataArea > li:first-child"), "RaceMarkTable race facts")
    fact_text = _display(facts.get_text(" ", strip=True))
    if "ばんえい" in fact_text:
        raise _unsupported("Banei RaceMarkTable is unsupported")
    surface_distance = _SURFACE_DISTANCE.findall(fact_text)
    weather = _WEATHER.findall(fact_text)
    condition = _CONDITION.findall(fact_text)
    if len(surface_distance) != 1 or len(weather) != 1 or len(condition) != 1:
        raise _validation("RaceMarkTable race facts are missing or ambiguous")
    return place, {
        "track": surface_distance[0][0],
        "distance_m": _positive_int(surface_distance[0][1], "RaceMarkTable distance"),
        "weather": _required(weather[0], "RaceMarkTable weather"),
        "track_condition": _required(condition[0], "RaceMarkTable track_condition"),
    }


def _result_table(soup: _BeautifulSoup) -> _Tag:
    candidates = []
    required = {"着順", "馬名", "馬体重（増減）", "タイム", "コーナー通過順", "人気", "単勝オッズ"}
    for table in soup.find_all("table"):
        header_rows = [row for row in table.find_all("tr") if row.find_all("th", recursive=False)]
        headings = {
            _re.sub(r"\s+", "", _display(item.get_text(" ", strip=True)))
            for row in header_rows[:1]
            for item in row.find_all("th", recursive=False)
        }
        if required <= headings and table.select("tbody > tr > td.horseName"):
            candidates.append(table)
    return _one(candidates, "RaceMarkTable result table")


def _canonical_result_horse_href(value: object, race_url: str) -> str:
    _, lineage = _canonical_horse_url(value, base_url=race_url)
    return lineage


def _result_row(table: _Tag, lineage: str, race_url: str) -> _Tag:
    matches = []
    for row in table.select("tbody > tr"):
        anchors = row.select("td.horseName a[href]")
        if len(anchors) > 1:
            raise _validation("RaceMarkTable horse link is ambiguous")
        if len(anchors) == 1 and _canonical_result_horse_href(anchors[0].get("href"), race_url) == lineage:
            matches.append(row)
    return _one(matches, "RaceMarkTable horse result row")


def _cell(row: _Tag, css_class: str, name: str) -> _Tag:
    return _one(row.select(f"td.{css_class}"), name)


def _jockey(value: _Tag) -> str:
    anchor = _one(value.select("a"), "RaceMarkTable jockey")
    direct = " ".join(str(item) for item in anchor.find_all(string=True, recursive=False) if str(item).strip())
    return _required(direct, "RaceMarkTable jockey")


def _without_affiliation(value: str) -> str:
    return _re.sub(r"\s*(?:\([^)]*\)|（[^）]*）)\s*\Z", "", _display(value))


def _decimal(value: str, name: str, *, positive: bool = False) -> _Decimal:
    if _DECIMAL.fullmatch(value) is None:
        raise _unsupported(f"{name} is unsupported")
    try:
        parsed = _Decimal(value)
    except _InvalidOperation as error:
        raise _validation(f"{name} is invalid") from error
    if not parsed.is_finite() or (positive and parsed <= 0):
        raise _unsupported(f"{name} is unsupported")
    return parsed


def _result_values(row: _Tag, corner_labels: tuple[int, ...]) -> dict[str, object]:
    row_text = _display(row.get_text(" ", strip=True))
    if any(marker in row_text for marker in _CANCELLATIONS):
        raise _unsupported("RaceMarkTable result state is unsupported")
    finish_text = _required(_cell(row, "a", "RaceMarkTable finish").get_text(" ", strip=True), "RaceMarkTable finish")
    popularity_text = _required(_cell(row, "o", "RaceMarkTable popularity").get_text(" ", strip=True), "RaceMarkTable popularity")
    time_text = _display(_cell(row, "k", "RaceMarkTable race_time").get_text(" ", strip=True))
    odds_text = _display(_cell(row, "p", "RaceMarkTable odds").get_text(" ", strip=True))
    if _POSITIVE.fullmatch(finish_text) is None or _POSITIVE.fullmatch(popularity_text) is None:
        raise _unsupported("RaceMarkTable finish or popularity is unsupported")
    if not time_text or _TIME.fullmatch(time_text) is None:
        raise _unsupported("RaceMarkTable race_time is unsupported")
    weight_text = _required(_cell(row, "horseWeight", "RaceMarkTable body weight").get_text(" ", strip=True), "RaceMarkTable body weight")
    weight_match = _WEIGHT.fullmatch(weight_text)
    if weight_match is None:
        raise _unsupported("RaceMarkTable body weight is unsupported")
    passing_order = _required(_cell(row, "corner_position", "RaceMarkTable passing order").get_text(" ", strip=True), "RaceMarkTable passing order")
    if _PASSING.fullmatch(passing_order) is None:
        raise _unsupported("RaceMarkTable passing order is unsupported")
    components = tuple(_positive_int(item, "RaceMarkTable passing component") for item in passing_order.split("-"))
    if len(components) != len(corner_labels):
        raise _unsupported("RaceMarkTable corner labels and passing order disagree")
    return {
        "finish": _positive_int(finish_text, "RaceMarkTable finish"),
        "race_time": time_text,
        "weight": _Decimal(weight_match.group(1)),
        "weight_diff": _Decimal(weight_match.group(2)),
        "jockey": _jockey(_cell(row, "jockeyName", "RaceMarkTable jockey")),
        "popularity": _positive_int(popularity_text, "RaceMarkTable popularity"),
        "odds": _decimal(odds_text, "RaceMarkTable odds", positive=True),
        "passing_order": passing_order,
        "fourth_corner_position": components[corner_labels.index(4)],
    }


def _corner_labels(soup: _BeautifulSoup) -> tuple[int, ...]:
    sections = [
        section
        for section in soup.select("section.cornerPassTable")
        if "全馬コーナー通過順" in _display(section.get_text(" ", strip=True))
    ]
    if not sections:
        raise _unsupported("RaceMarkTable corner section is missing")
    section = _one(sections, "RaceMarkTable corner section")
    rows = section.select("table tbody > tr")
    if not rows:
        raise _unsupported("RaceMarkTable corner labels are missing")
    labels: list[int] = []
    for row in rows:
        cells = row.find_all("td", recursive=False)
        if len(cells) < 2:
            raise _unsupported("RaceMarkTable corner label is unsupported")
        match = _CORNER_LABEL.fullmatch(_display(cells[0].get_text(" ", strip=True)))
        if match is None:
            raise _unsupported("RaceMarkTable corner label is unsupported")
        labels.append(_CORNER_ORDINAL[match.group(1)])
    result = tuple(labels)
    if len(set(result)) != len(result) or result != tuple(sorted(result)) or result.count(4) != 1:
        raise _unsupported("RaceMarkTable corner labels are unsupported")
    return result


def _cross_check(
    history: dict[str, str],
    race_date: _date,
    race_no: str,
    place: str,
    facts: dict[str, object],
    result: dict[str, object],
) -> None:
    if _parse_date(history["race_date"], "HorseMarkInfo race_date") != race_date:
        raise _validation("HorseMarkInfo race_date disagrees with RaceMarkTable")
    if history["place"] != place:
        raise _validation("HorseMarkInfo place disagrees with RaceMarkTable")
    if _token(history["race_no"], "HorseMarkInfo race_no") != race_no:
        raise _validation("HorseMarkInfo race_no disagrees with RaceMarkTable")
    if _positive_int(history["distance"], "HorseMarkInfo distance") != facts["distance_m"]:
        raise _validation("HorseMarkInfo distance disagrees with RaceMarkTable")
    if history["weather"] != facts["weather"] or history["track_condition"] != facts["track_condition"]:
        raise _validation("HorseMarkInfo race facts disagree with RaceMarkTable")
    if _positive_int(history["finish"], "HorseMarkInfo finish") != result["finish"]:
        raise _validation("HorseMarkInfo finish disagrees with RaceMarkTable")
    if history["race_time"] != result["race_time"]:
        raise _validation("HorseMarkInfo race_time disagrees with RaceMarkTable")
    if _decimal(history["weight"], "HorseMarkInfo weight") != result["weight"]:
        raise _validation("HorseMarkInfo weight disagrees with RaceMarkTable")
    if _without_affiliation(history["jockey"]) != result["jockey"]:
        raise _validation("HorseMarkInfo jockey disagrees with RaceMarkTable")
    if _positive_int(history["popularity"], "HorseMarkInfo popularity") != result["popularity"]:
        raise _validation("HorseMarkInfo popularity disagrees with RaceMarkTable")


def normalize_nar_historical_past_race_source_record(
    *,
    target_entry_record: _HistoricalInputSourceRecord,
    horse_history_response: _NarSuppliedOfficialResponse,
    race_result_response: _NarSuppliedOfficialResponse,
) -> _HistoricalInputSourceRecord:
    """Normalize one exact official NAR HorseMarkInfo/RaceMarkTable evidence pair."""

    target_date, _, _, target_entry_id, lineage = _target_identity(target_entry_record)
    if type(horse_history_response) is not _NarSuppliedOfficialResponse:
        raise _validation("horse_history_response must be NarSuppliedOfficialResponse")
    if type(race_result_response) is not _NarSuppliedOfficialResponse:
        raise _validation("race_result_response must be NarSuppliedOfficialResponse")
    horse_url, horse_lineage = _canonical_horse_url(horse_history_response.response_url)
    if horse_lineage != lineage:
        raise _validation("HorseMarkInfo lineage does not match target entry")
    race_url, race_date, baba_code, race_no = _canonical_supplied_race_url(race_result_response.response_url)
    if race_date >= target_date:
        raise _validation("historical race must precede target race")
    horse_sha256 = _hashlib.sha256(horse_history_response.response_body).hexdigest()
    race_sha256 = _hashlib.sha256(race_result_response.response_body).hexdigest()
    if (horse_url, horse_sha256) == (race_url, race_sha256):
        raise _validation("NAR past-race evidence requires two distinct responses")
    history_soup = _document(horse_history_response)
    race_soup = _document(race_result_response)
    _, history = _history_row(history_soup, horse_url, (race_date, baba_code, race_no))
    place, facts = _race_header(race_soup, race_date, race_no)
    labels = _corner_labels(race_soup)
    result = _result_values(_result_row(_result_table(race_soup), lineage, race_url), labels)
    _cross_check(history, race_date, race_no, place, facts, result)
    difference = _decimal(history["difference"], "HorseMarkInfo difference")
    evidence = (
        _HistoricalInputEvidenceReference(
            "historical_race_context", horse_url, horse_sha256, None, horse_history_response.observed_at
        ),
        _HistoricalInputEvidenceReference(
            "historical_race_result", race_url, race_sha256, None, race_result_response.observed_at
        ),
    )
    return _HistoricalInputSourceRecord(
        record_kind="past_race",
        organization="NAR",
        source_system="nar_official",
        external_race_id=target_entry_record.external_race_id,
        external_entry_id=target_entry_id,
        provider_record_id=f"nar:result:{race_date:%Y%m%d}:{baba_code}:{race_no}:horse:{lineage}",
        record_values={
            "race_date": race_date,
            "place": place,
            "race_name": history["race_name"],
            "race_class": history["race_class"],
            "distance_m": facts["distance_m"],
            "track": facts["track"],
            "weather": facts["weather"],
            "track_condition": facts["track_condition"],
            "finish": result["finish"],
            "reference_time_difference_seconds": difference,
            "race_time": result["race_time"],
            "weight": result["weight"],
            "weight_diff": result["weight_diff"],
            "jockey": result["jockey"],
            "popularity": result["popularity"],
            "odds": result["odds"],
            "passing_order": result["passing_order"],
            "fourth_corner_position": result["fourth_corner_position"],
        },
        evidence=evidence,
    )


if "annotations" in globals():
    del annotations
