"""Normalize one trusted JRA accessS normal-final result and persist it once."""

from __future__ import annotations

from datetime import date as _date
import re as _re
from unicodedata import normalize as _normalize

from bs4 import BeautifulSoup as _BeautifulSoup
from bs4.element import Tag as _Tag

from scripts.simulation.historical_input_snapshots import HistoricalInputSnapshot
from scripts.simulation.jra_official_identity import (
    JRAOfficialIdentityValidationError as _JRAOfficialIdentityValidationError,
    build_jra_external_entry_id as _build_jra_external_entry_id,
    parse_jra_external_race_id as _parse_jra_external_race_id,
    parse_jra_result_url_identity as _parse_jra_result_url_identity,
)
from scripts.simulation.jra_official_response_capture import (
    JRAOfficialPageKind,
    JRAOfficialResponseCapture,
    JRAOfficialResponseCaptureArchive,
)
from scripts.simulation.repositories.interfaces import (
    PersistedRaceResult,
    PersistedRaceResultEntry,
    RaceResultEntryStatus,
    RaceResultRepository,
    RaceResultStatus,
)

__all__ = (
    "JRATargetRaceResultPersistenceError",
    "JRATargetRaceResultPersistenceValidationError",
    "JRATargetRaceResultPersistenceUnavailableError",
    "JRATargetRaceResultPersistenceUnsupportedError",
    "normalize_and_persist_jra_target_race_result",
)


class JRATargetRaceResultPersistenceError(ValueError):
    """Base error for the narrow JRA target-result persistence boundary."""


class JRATargetRaceResultPersistenceValidationError(JRATargetRaceResultPersistenceError):
    """Raised when archived evidence or a supplied snapshot is contradictory."""


class JRATargetRaceResultPersistenceUnavailableError(JRATargetRaceResultPersistenceError):
    """Raised when exact capture or positive terminality evidence is unavailable."""


class JRATargetRaceResultPersistenceUnsupportedError(JRATargetRaceResultPersistenceError):
    """Raised for a recognized result representation outside normal-final-only support."""


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
_DATE_LINE = _re.compile(
    r"(?P<year>[0-9]{4})年(?P<month>[0-9]{1,2})月(?P<day>[0-9]{1,2})日(?:\([^)]*\)|（[^）]*）)?\s*"
    r"(?P<meeting>[0-9]{1,2})回(?P<venue>札幌|函館|福島|新潟|東京|中山|中京|京都|阪神|小倉)(?P<meeting_day>[0-9]{1,2})日\Z"
)
_RACE_NUMBER = _re.compile(r"(?P<race>[1-9]|1[0-2])(?:R|レース)\Z")
_POSITIVE = _re.compile(r"[1-9][0-9]*\Z")
_YEN = _re.compile(r"[1-9][0-9]{0,2}(?:,[0-9]{3})*円\Z")
_RESULT_HEADINGS = frozenset(
    {
        "着順",
        "枠",
        "馬番",
        "馬名",
        "性齢",
        "負担重量",
        "騎手名",
        "タイム",
        "着差",
        "コーナー通過順位",
        "馬体重（増減）",
        "調教師名",
        "単勝人気",
    }
)


def _validation(message: str) -> JRATargetRaceResultPersistenceValidationError:
    return JRATargetRaceResultPersistenceValidationError(message)


def _unavailable(message: str) -> JRATargetRaceResultPersistenceUnavailableError:
    return JRATargetRaceResultPersistenceUnavailableError(message)


def _unsupported(message: str) -> JRATargetRaceResultPersistenceUnsupportedError:
    return JRATargetRaceResultPersistenceUnsupportedError(message)


def _one(nodes: object, name: str) -> _Tag:
    values = tuple(nodes)  # type: ignore[arg-type]
    if len(values) != 1 or not isinstance(values[0], _Tag):
        raise _validation(f"{name} must be unique")
    return values[0]


def _display(value: object, name: str) -> str:
    if type(value) is not str:
        raise _validation(f"{name} is invalid")
    result = " ".join(_normalize("NFC", value).split())
    if not result:
        raise _validation(f"{name} is missing")
    return result


def _heading(node: _Tag) -> str:
    return "".join(_normalize("NFC", node.get_text(" ", strip=True)).split())


def _cell_text(row: _Tag, selector: str, name: str) -> str:
    return _display(_one(row.select(selector), name).get_text(" ", strip=True), name)


def _optional_cell_text(row: _Tag, selector: str, name: str) -> str:
    value = _one(row.select(selector), name).get_text(" ", strip=True)
    if type(value) is not str:
        raise _validation(f"{name} is invalid")
    return " ".join(_normalize("NFC", value).split())


def _positive(value: str, name: str) -> int:
    if _POSITIVE.fullmatch(value) is None:
        raise _validation(f"{name} must be a positive integer")
    return int(value)


def _document(capture: JRAOfficialResponseCapture) -> _BeautifulSoup:
    try:
        html = capture.response_body.decode("cp932", errors="strict")
    except UnicodeDecodeError as error:
        raise _validation("capture response_body is not strict cp932") from error
    return _BeautifulSoup(html, "html.parser")


def _validate_visible_header(
    soup: _BeautifulSoup,
    *,
    snapshot: HistoricalInputSnapshot,
    race_identity: object,
) -> None:
    header = _one(soup.select("#race_result .race_header"), "official JRA race header")
    date_value = _display(
        _one(header.select(".cell.date"), "official JRA race date").get_text(" ", strip=True),
        "official JRA race date",
    )
    match = _DATE_LINE.fullmatch(date_value)
    if match is None:
        raise _validation("official JRA race date is invalid")
    try:
        visible_date = _date(int(match.group("year")), int(match.group("month")), int(match.group("day")))
    except ValueError as error:
        raise _validation("official JRA race date is invalid") from error
    if (
        visible_date != snapshot.race.target_race_date
        or match.group("venue") != _VENUES[race_identity.venue_code]
        or int(match.group("meeting")) != int(race_identity.meeting_number)
        or int(match.group("meeting_day")) != int(race_identity.meeting_day)
    ):
        raise _validation("official JRA visible race identity disagrees")
    race_node = _one(header.select(".race_number img[alt]"), "official JRA race number")
    race_text = race_node.get("alt")
    race_match = _RACE_NUMBER.fullmatch(_display(race_text, "official JRA race number"))
    if race_match is None or int(race_match.group("race")) != int(race_identity.race_number):
        raise _validation("official JRA race number disagrees")


def _result_rows(soup: _BeautifulSoup) -> tuple[tuple[int, int], ...]:
    candidates: list[_Tag] = []
    for table in soup.select("#race_result table"):
        headings = {_heading(item) for item in table.select("thead th")}
        if _RESULT_HEADINGS.issubset(headings):
            candidates.append(table)
    table = _one(candidates, "official JRA result table")
    rows = tuple(table.select("tbody > tr"))
    if not rows:
        raise _validation("official JRA result rows are missing")
    values: list[tuple[int, int]] = []
    for row in rows:
        if not isinstance(row, _Tag):
            raise _validation("official JRA result row is invalid")
        margin = _optional_cell_text(row, "td.margin", "official JRA result margin")
        if margin == "同着":
            raise _unsupported("official JRA dead heat is unsupported")
        horse_no = _positive(_cell_text(row, "td.num", "official JRA horse number"), "official JRA horse number")
        place = _cell_text(row, "td.place", "official JRA finish position")
        if _POSITIVE.fullmatch(place) is None:
            raise _unsupported("official JRA non-normal finish position is unsupported")
        values.append((horse_no, int(place)))
    horse_numbers = tuple(item[0] for item in values)
    finish_positions = tuple(item[1] for item in values)
    if len(set(horse_numbers)) != len(horse_numbers):
        raise _validation("official JRA horse numbers must be unique")
    if len(set(finish_positions)) != len(finish_positions):
        raise _validation("official JRA finish positions must be unique")
    if set(finish_positions) != set(range(1, len(values) + 1)):
        raise _validation("official JRA finish positions must be contiguous")
    return tuple(values)


def _validate_positive_finality(soup: _BeautifulSoup) -> None:
    area = _one(soup.select("#race_result .refund_area"), "official JRA payout publication area")
    header = _one(area.select(".block_header"), "official JRA payout publication heading")
    if _display(header.get_text(" ", strip=True), "official JRA payout publication heading") != "払戻金":
        raise _unavailable("official JRA payout publication heading is unavailable")
    unit = _one(area.select(".refund_unit"), "official JRA payout publication container")
    amounts = tuple(unit.select("li .yen"))
    if not amounts:
        raise _unavailable("official JRA published payout amount is unavailable")
    for amount in amounts:
        normalized = "".join(_display(amount.get_text(" ", strip=True), "official JRA payout amount").split())
        if _YEN.fullmatch(normalized) is None:
            raise _unavailable("official JRA published payout amount is unavailable")


def _snapshot_entry_ids(
    *,
    snapshot: HistoricalInputSnapshot,
    race_identity: object,
) -> dict[str, int]:
    source = snapshot.identity.source_identity
    values: dict[str, int] = {}
    race_entry_ids: set[int] = set()
    for entry in snapshot.entries:
        external = entry.external_entry_identity
        external_race = external.external_race_identity
        if (
            external_race.organization != "JRA"
            or external_race.source_system != "jra_official"
            or external_race.external_race_id != source.external_race_id
        ):
            raise _validation("snapshot entry external race identity is incompatible")
        expected_entry_id = _build_jra_external_entry_id(race_identity=race_identity, horse_no=entry.horse_no)
        if external.external_entry_id != expected_entry_id:
            raise _validation("snapshot entry external entry identity is incoherent")
        if expected_entry_id in values or entry.race_entry_id in race_entry_ids:
            raise _validation("snapshot entry identities must be unique")
        values[expected_entry_id] = entry.race_entry_id
        race_entry_ids.add(entry.race_entry_id)
    return values


def normalize_and_persist_jra_target_race_result(
    *,
    capture_id: str,
    capture_archive: JRAOfficialResponseCaptureArchive,
    snapshot: HistoricalInputSnapshot,
    race_result_repository: RaceResultRepository,
) -> PersistedRaceResult:
    """Persist one exact archived JRA normal-final result after complete validation."""

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
        raise _unavailable("exact JRA result capture is unavailable")
    if type(capture) is not JRAOfficialResponseCapture:
        raise _validation("capture archive returned an invalid type")
    if capture.capture_id != capture_id:
        raise _validation("capture archive returned a different capture")
    if capture.page_kind is not JRAOfficialPageKind.RACE_RESULT:
        raise _validation("capture page_kind must be RACE_RESULT")

    source = snapshot.identity.source_identity
    if source.organization != "JRA" or source.source_system != "jra_official":
        raise _validation("snapshot source identity is incompatible")
    try:
        capture_race_identity = _parse_jra_result_url_identity(capture.canonical_source_url)
        snapshot_race_identity = _parse_jra_external_race_id(source.external_race_id)
    except _JRAOfficialIdentityValidationError as error:
        raise _validation("JRA race identity is invalid") from error
    if capture_race_identity != snapshot_race_identity:
        raise _validation("capture and snapshot JRA race identities disagree")

    soup = _document(capture)
    _validate_visible_header(soup, snapshot=snapshot, race_identity=capture_race_identity)
    rows = _result_rows(soup)
    _validate_positive_finality(soup)
    snapshot_entry_ids = _snapshot_entry_ids(snapshot=snapshot, race_identity=capture_race_identity)

    result_entry_ids: dict[str, tuple[int, int]] = {}
    mapped_race_entry_ids: set[int] = set()
    for horse_no, finish_position in rows:
        external_entry_id = _build_jra_external_entry_id(race_identity=capture_race_identity, horse_no=horse_no)
        race_entry_id = snapshot_entry_ids.get(external_entry_id)
        if race_entry_id is None:
            raise _validation("official JRA result entry is unresolved")
        if external_entry_id in result_entry_ids or race_entry_id in mapped_race_entry_ids:
            raise _validation("official JRA result entry identities must be unique")
        result_entry_ids[external_entry_id] = (horse_no, finish_position)
        mapped_race_entry_ids.add(race_entry_id)
    if set(result_entry_ids) != set(snapshot_entry_ids):
        raise _validation("official JRA result entries do not exactly cover snapshot entries")

    result = PersistedRaceResult(
        race_id=snapshot.internal_race_id,
        result_status=RaceResultStatus.COMPLETE,
        finalized_at=capture.observed_at,
        observed_at=capture.observed_at,
        source=capture.capture_id,
        entries=tuple(
            PersistedRaceResultEntry(
                horse_no=horse_no,
                race_entry_id=snapshot_entry_ids[external_entry_id],
                finish_position=finish_position,
                result_status=RaceResultEntryStatus.CONFIRMED,
            )
            for external_entry_id, (horse_no, finish_position) in result_entry_ids.items()
        ),
    )
    race_result_repository.save_race_result(result)
    return result
