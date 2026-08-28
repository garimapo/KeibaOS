"""Normalize one trusted NAR RaceMarkTable normal-final result and persist it once."""

from __future__ import annotations

from datetime import date as _date
import re as _re
from unicodedata import normalize as _normalize

from bs4 import BeautifulSoup as _BeautifulSoup
from bs4.element import NavigableString as _NavigableString, Tag as _Tag

from scripts.simulation.historical_input_snapshots import HistoricalInputSnapshot
from scripts.simulation.nar_official_response_capture import (
    NAROfficialPageKind,
    NAROfficialResponseCapture,
    NAROfficialResponseCaptureArchive,
    NAROfficialResponseCaptureError as _NAROfficialResponseCaptureError,
    canonicalize_nar_official_capture_url as _canonicalize_nar_official_capture_url,
)
from scripts.simulation.repositories.interfaces import (
    PersistedRaceResult,
    PersistedRaceResultEntry,
    RaceResultEntryStatus,
    RaceResultRepository,
    RaceResultStatus,
)

__all__ = (
    "NARTargetRaceResultPersistenceError",
    "NARTargetRaceResultPersistenceValidationError",
    "NARTargetRaceResultPersistenceUnavailableError",
    "NARTargetRaceResultPersistenceUnsupportedError",
    "normalize_and_persist_nar_target_race_result",
)


class NARTargetRaceResultPersistenceError(ValueError):
    """Base error for the narrow NAR target-result persistence boundary."""


class NARTargetRaceResultPersistenceValidationError(NARTargetRaceResultPersistenceError):
    """Raised when archived evidence or a supplied snapshot is contradictory."""


class NARTargetRaceResultPersistenceUnavailableError(NARTargetRaceResultPersistenceError):
    """Raised when exact capture or positive terminality evidence is unavailable."""


class NARTargetRaceResultPersistenceUnsupportedError(NARTargetRaceResultPersistenceError):
    """Raised for a recognized result representation outside normal-final-only support."""


_CANONICAL_RACE_URL = _re.compile(
    r"https://www\.keiba\.go\.jp/KeibaWeb/TodayRaceInfo/RaceMarkTable\?"
    r"k_babaCode=(?P<baba_code>[1-9][0-9]*)&k_raceDate="
    r"(?P<year>[0-9]{4})%2F(?P<month>[0-9]{2})%2F(?P<day>[0-9]{2})"
    r"&k_raceNo=(?P<race_no>[1-9][0-9]*)\Z"
)
_VISIBLE_HEADING = _re.compile(
    r"(?P<year>[0-9]{4})年(?P<month>[0-9]{1,2})月(?P<day>[0-9]{1,2})日"
    r"(?:\([^\s()]+\)|（[^\s（）]+）)\s*(?P<place>.*?)\s*"
    r"第(?P<race_no>[1-9][0-9]*)競走\s+競走成績\Z"
)
_POSITIVE = _re.compile(r"[1-9][0-9]*\Z")
_FIELD_CLASSES = tuple(chr(code) for code in range(ord("a"), ord("p") + 1))
_HEADER_LABELS = (
    "着順",
    "枠",
    "馬番",
    "馬名",
    "所属",
    "性齢",
    "負担重量",
    "騎手（所属）",
    "調教師",
    "馬体重（増減）",
    "タイム",
    "着差",
    "上がり3F",
    "コーナー通過順",
    "人気",
    "単勝オッズ",
)
_HEADER_CHILD_TAGS = (
    (), (), (), (), (), (), ("br",), ("span",), (), ("br", "span"), (), (), ("br",), ("br",), (), ("br",),
)
_COURSE_CLASS = _re.compile(r"course_0[1-8]\Z")
_FINALITY_STATEMENT = (
    "※2026年4月以降、優勝馬の情報はレース終了翌日までに表示されます。"
    "また、優勝馬の情報はレース結果確定時点の情報となります。"
)
_KNOWN_EXCEPTIONAL_ROW_MARKERS_FOR_FAIL_CLOSED_REJECTION_ONLY = (
    "取消",
    "除外",
    "中止",
    "失格",
    "降着",
)


def _validation(message: str) -> NARTargetRaceResultPersistenceValidationError:
    return NARTargetRaceResultPersistenceValidationError(message)


def _unavailable(message: str) -> NARTargetRaceResultPersistenceUnavailableError:
    return NARTargetRaceResultPersistenceUnavailableError(message)


def _unsupported(message: str) -> NARTargetRaceResultPersistenceUnsupportedError:
    return NARTargetRaceResultPersistenceUnsupportedError(message)


def _display(value: object, name: str) -> str:
    if type(value) is not str:
        raise _validation(f"{name} is invalid")
    result = " ".join(_normalize("NFC", value).split())
    if not result:
        raise _validation(f"{name} is missing")
    return result


def _heading(value: object, name: str) -> str:
    return "".join(_display(value, name).split())


def _one(nodes: object, name: str) -> _Tag:
    values = tuple(nodes)  # type: ignore[arg-type]
    if len(values) != 1 or not isinstance(values[0], _Tag):
        raise _validation(f"{name} must be unique")
    return values[0]


def _direct_elements(node: _Tag) -> tuple[_Tag, ...]:
    return tuple(item for item in node.children if isinstance(item, _Tag))


def _require_no_direct_text(node: _Tag, name: str) -> None:
    if any(isinstance(item, _NavigableString) and str(item).strip() for item in node.children):
        raise _validation(f"{name} has unclassified direct text")


def _require_tags(node: _Tag, names: tuple[str, ...], name: str) -> tuple[_Tag, ...]:
    values = _direct_elements(node)
    if tuple(item.name for item in values) != names:
        raise _validation(f"{name} direct structure is invalid")
    _require_no_direct_text(node, name)
    return values


def _positive_direct_token(node: _Tag, name: str) -> int:
    if _direct_elements(node):
        raise _validation(f"{name} direct structure is invalid")
    value = "".join(str(item) for item in node.children if isinstance(item, _NavigableString))
    if _POSITIVE.fullmatch(value) is None:
        raise _validation(f"{name} must be a positive canonical decimal token")
    return int(value)


def _validate_header_cell(cell: _Tag, *, expected_tags: tuple[str, ...], label: str) -> None:
    if tuple(item.name for item in _direct_elements(cell)) != expected_tags:
        raise _validation("official NAR result header direct structure is invalid")
    if _heading(cell.get_text(" ", strip=True), "official NAR result header label") != label:
        raise _validation("official NAR result header labels are invalid")


def _valid_field_classes(value: object, field: str) -> bool:
    if not isinstance(value, list):
        return False
    classes = tuple(value)
    if field in {"a", "c", "e", "g", "i", "k", "l"}:
        return classes == (field,)
    if field == "b":
        return len(classes) == 3 and classes[:2] == ("b", "courseNum") and _COURSE_CLASS.fullmatch(classes[2]) is not None
    if field == "d":
        return classes == ("d", "horseName")
    if field == "f":
        return classes in (("f",), ("f", "femal"))
    if field == "h":
        return classes == ("h", "jockeyName")
    if field == "j":
        return classes == ("j", "horseWeight")
    if field == "m":
        return classes == ("m",) or (
            len(classes) == 3 and classes[:2] == ("m", "furlongNum") and _COURSE_CLASS.fullmatch(classes[2]) is not None
        )
    if field == "n":
        return classes == ("n", "corner_position")
    if field == "o":
        return classes == ("o",) or (
            len(classes) == 3 and classes[:2] == ("o", "popularNum") and _COURSE_CLASS.fullmatch(classes[2]) is not None
        )
    if field == "p":
        return classes in (("p",), ("p", "femal"))
    return False


def _document(capture: NAROfficialResponseCapture) -> _BeautifulSoup:
    try:
        html = capture.response_body.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise _validation("capture response_body is not strict utf-8") from error
    return _BeautifulSoup(html, "html.parser")


def _canonical_race_context(capture: NAROfficialResponseCapture) -> tuple[str, _date, str]:
    try:
        page_kind, canonical_url = _canonicalize_nar_official_capture_url(capture.canonical_source_url)
    except _NAROfficialResponseCaptureError as error:
        raise _validation("capture canonical_source_url is invalid") from error
    if page_kind is not NAROfficialPageKind.RACE_MARK_TABLE or canonical_url != capture.canonical_source_url:
        raise _validation("capture canonical_source_url is incompatible")
    match = _CANONICAL_RACE_URL.fullmatch(canonical_url)
    if match is None:
        raise _validation("capture canonical RaceMarkTable URL is invalid")
    try:
        race_date = _date(int(match.group("year")), int(match.group("month")), int(match.group("day")))
    except ValueError as error:
        raise _validation("capture canonical RaceMarkTable date is invalid") from error
    race_id = f"nar:{race_date:%Y%m%d}:{match.group('baba_code')}:{match.group('race_no')}"
    return race_id, race_date, match.group("race_no")


def _validate_visible_identity(
    soup: _BeautifulSoup,
    *,
    snapshot: HistoricalInputSnapshot,
    race_date: _date,
    race_no: str,
) -> None:
    active = _one(
        soup.select(".chartNavi.trackNameNavi a.cNaviBtn.courseBtn.active"),
        "official NAR active course",
    )
    active_place = _heading(active.get_text(" ", strip=True), "official NAR active course")
    header = _one(
        soup.select("article.raceResult > div.innerWrapper > h4"),
        "official NAR race heading",
    )
    match = _VISIBLE_HEADING.fullmatch(_display(header.get_text(" ", strip=True), "official NAR race heading"))
    if match is None:
        raise _validation("official NAR visible race heading is invalid")
    try:
        visible_date = _date(int(match.group("year")), int(match.group("month")), int(match.group("day")))
    except ValueError as error:
        raise _validation("official NAR visible race date is invalid") from error
    visible_place = "".join(_normalize("NFC", match.group("place")).split())
    if (
        visible_date != race_date
        or visible_date != snapshot.race.target_race_date
        or match.group("race_no") != race_no
        or visible_place != active_place
        or visible_place != snapshot.race.place
    ):
        raise _validation("official NAR visible race identity disagrees")


def _result_rows(soup: _BeautifulSoup) -> tuple[tuple[int, int], ...]:
    table = _one(
        soup.select("article.raceResult > div.innerWrapper > section.gradeTable > table"),
        "official NAR result table",
    )
    if table.find_all("thead"):
        raise _validation("official NAR result table must not contain thead")
    (tbody,) = _require_tags(table, ("tbody",), "official NAR result table")
    rows = _require_tags(tbody, tuple("tr" for _ in _direct_elements(tbody)), "official NAR result tbody")
    if len(rows) < 2:
        raise _validation("official NAR result rows are missing")
    header = rows[0]
    header_cells = _require_tags(header, tuple("th" for _ in _FIELD_CLASSES), "official NAR result header")
    if tuple(cell.get("class") for cell in header_cells) != tuple([field] for field in _FIELD_CLASSES):
        raise _validation("official NAR result header classes are invalid")
    for cell, expected_tags, label in zip(header_cells, _HEADER_CHILD_TAGS, _HEADER_LABELS, strict=True):
        _validate_header_cell(cell, expected_tags=expected_tags, label=label)

    values: list[tuple[int, int]] = []
    for row in rows[1:]:
        if row.get("class") != ["tBorder"]:
            raise _validation("official NAR result row class is invalid")
        cells = _require_tags(row, tuple("td" for _ in _FIELD_CLASSES), "official NAR result row")
        classes = tuple(cell.get("class") for cell in cells)
        if any(not _valid_field_classes(item, field) for item, field in zip(classes, _FIELD_CLASSES, strict=True)):
            raise _validation("official NAR result row field classes are invalid")
        row_text = _display(row.get_text(" ", strip=True), "official NAR result row")
        if any(marker in row_text for marker in _KNOWN_EXCEPTIONAL_ROW_MARKERS_FOR_FAIL_CLOSED_REJECTION_ONLY):
            raise _unsupported("official NAR exceptional result row is unsupported")
        horse_no = _positive_direct_token(cells[2], "official NAR horse number")
        finish_position = _positive_direct_token(cells[0], "official NAR finish position")
        values.append((horse_no, finish_position))

    horse_numbers = tuple(item[0] for item in values)
    finish_positions = tuple(item[1] for item in values)
    if len(set(horse_numbers)) != len(horse_numbers):
        raise _validation("official NAR horse numbers must be unique")
    if len(set(finish_positions)) != len(finish_positions):
        raise _unsupported("official NAR non-normal finish positions are unsupported")
    if set(finish_positions) != set(range(1, len(values) + 1)):
        raise _unsupported("official NAR non-contiguous finish positions are unsupported")
    return tuple(values)


def _validate_positive_finality(soup: _BeautifulSoup) -> None:
    section = _one(
        soup.select("article.raceResult > div.innerWrapper > section.winHorseTable"),
        "official NAR winner information section",
    )
    children = _require_tags(
        section,
        ("h4", "h3", "table", "table", "table"),
        "official NAR winner information section",
    )
    heading, winner, info_table, pedigree_table, grade_table = children
    if (
        info_table.get("class") != ["infoAndBonus"]
        or pedigree_table.get("class") != ["pedigreeTable"]
        or grade_table.get("class") != ["horseGrade"]
    ):
        raise _validation("official NAR winner information structure is invalid")
    (label,) = _require_tags(heading, ("span",), "official NAR winner information heading")
    if label.get("class") != ["smallTitle"] or _heading(label.get_text(" ", strip=True), "official NAR winner information heading") != "優勝馬情報":
        raise _unavailable("official NAR winner information heading is unavailable")
    winner_children = _direct_elements(winner)
    if (
        tuple(item.name for item in winner_children) != ("span", "span", "a")
        or tuple(item.get("class") for item in winner_children) != (["smallFont01"], ["smallFont03"], ["cNaviBtn"])
        or not any(isinstance(item, _NavigableString) and str(item).strip() for item in winner.children)
        or any(not _display(table.get_text(" ", strip=True), "official NAR winner information table") for table in (info_table, pedigree_table, grade_table))
    ):
        raise _unavailable("official NAR winner information is unavailable")
    statements = tuple(
        item
        for item in soup.select("article.attention > div.innerWrapper > p")
        if _heading(item.get_text(" ", strip=True), "official NAR finality statement") == _FINALITY_STATEMENT
    )
    if len(statements) != 1:
        raise _unavailable("official NAR result finalization evidence is unavailable")


def _snapshot_entry_ids(*, snapshot: HistoricalInputSnapshot, external_race_id: str) -> dict[str, int]:
    source = snapshot.identity.source_identity
    if (
        source.organization != "NAR"
        or source.source_system != "nar_official"
        or source.external_race_id != external_race_id
    ):
        raise _validation("snapshot source identity is incompatible")
    values: dict[str, int] = {}
    race_entry_ids: set[int] = set()
    for entry in snapshot.entries:
        external = entry.external_entry_identity
        external_race = external.external_race_identity
        expected_entry_id = f"{external_race_id}:entry:{entry.horse_no}"
        if (
            external_race.organization != "NAR"
            or external_race.source_system != "nar_official"
            or external_race.external_race_id != external_race_id
            or external.external_entry_id != expected_entry_id
        ):
            raise _validation("snapshot entry external identity is incompatible")
        if expected_entry_id in values or entry.race_entry_id in race_entry_ids:
            raise _validation("snapshot entry identities must be unique")
        values[expected_entry_id] = entry.race_entry_id
        race_entry_ids.add(entry.race_entry_id)
    return values


def normalize_and_persist_nar_target_race_result(
    *,
    capture_id: str,
    capture_archive: NAROfficialResponseCaptureArchive,
    snapshot: HistoricalInputSnapshot,
    race_result_repository: RaceResultRepository,
) -> PersistedRaceResult:
    """Persist one exact archived NAR complete normal-final result after validation."""

    if type(capture_id) is not str or not capture_id:
        raise ValueError("capture_id must be a non-empty exact str")
    if isinstance(capture_archive, type) or not callable(getattr(capture_archive, "load_capture", None)):
        raise ValueError("capture_archive must provide callable load_capture")
    if type(snapshot) is not HistoricalInputSnapshot:
        raise ValueError("snapshot must be exact HistoricalInputSnapshot")
    if isinstance(race_result_repository, type) or not callable(getattr(race_result_repository, "save_race_result", None)):
        raise ValueError("race_result_repository must provide callable save_race_result")

    capture = capture_archive.load_capture(capture_id=capture_id)
    if capture is None:
        raise _unavailable("exact NAR result capture is unavailable")
    if type(capture) is not NAROfficialResponseCapture:
        raise _validation("capture archive returned an invalid type")
    if capture.capture_id != capture_id:
        raise _validation("capture archive returned a different capture")
    if capture.page_kind is not NAROfficialPageKind.RACE_MARK_TABLE:
        raise _validation("capture page_kind must be RACE_MARK_TABLE")

    external_race_id, race_date, race_no = _canonical_race_context(capture)
    soup = _document(capture)
    _validate_visible_identity(soup, snapshot=snapshot, race_date=race_date, race_no=race_no)
    rows = _result_rows(soup)
    _validate_positive_finality(soup)
    snapshot_entry_ids = _snapshot_entry_ids(snapshot=snapshot, external_race_id=external_race_id)

    entries: list[PersistedRaceResultEntry] = []
    mapped_race_entry_ids: set[int] = set()
    for horse_no, finish_position in rows:
        external_entry_id = f"{external_race_id}:entry:{horse_no}"
        race_entry_id = snapshot_entry_ids.get(external_entry_id)
        if race_entry_id is None:
            raise _validation("official NAR result entry is unresolved")
        if race_entry_id in mapped_race_entry_ids:
            raise _validation("official NAR result entries are not unique")
        mapped_race_entry_ids.add(race_entry_id)
        entries.append(
            PersistedRaceResultEntry(
                horse_no=horse_no,
                race_entry_id=race_entry_id,
                finish_position=finish_position,
                result_status=RaceResultEntryStatus.CONFIRMED,
            )
        )
    if mapped_race_entry_ids != set(snapshot_entry_ids.values()):
        raise _validation("official NAR result entries do not exactly cover snapshot entries")

    result = PersistedRaceResult(
        race_id=snapshot.internal_race_id,
        result_status=RaceResultStatus.COMPLETE,
        finalized_at=capture.observed_at,
        observed_at=capture.observed_at,
        source=capture.capture_id,
        entries=tuple(entries),
    )
    race_result_repository.save_race_result(result)
    return result
