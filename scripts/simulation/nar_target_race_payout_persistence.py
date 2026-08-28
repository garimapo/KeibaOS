"""Persist one exact archived NAR normal-winning payout publication."""

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
    BET_TYPES,
    PayoutPublication,
    PayoutRecord,
    PayoutRepository,
    PayoutStatus,
    normalize_selection as _normalize_selection,
)

__all__ = (
    "NARTargetRacePayoutPersistenceError",
    "NARTargetRacePayoutPersistenceValidationError",
    "NARTargetRacePayoutPersistenceUnavailableError",
    "NARTargetRacePayoutPersistenceUnsupportedError",
    "normalize_and_persist_nar_target_race_payout",
)


class NARTargetRacePayoutPersistenceError(ValueError):
    """Base error for the narrow NAR target-payout persistence boundary."""


class NARTargetRacePayoutPersistenceValidationError(NARTargetRacePayoutPersistenceError):
    """Raised for malformed or contradictory archived payout evidence."""


class NARTargetRacePayoutPersistenceUnavailableError(NARTargetRacePayoutPersistenceError):
    """Raised when exact capture or normal-final payout evidence is unavailable."""


class NARTargetRacePayoutPersistenceUnsupportedError(NARTargetRacePayoutPersistenceError):
    """Raised for recognized payout representations outside normal-winning support."""


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
_AMOUNT = _re.compile(r"[1-9][0-9]{0,2}(?:,[0-9]{3})*円\Z")
_SELECTIONS = {
    "単勝": _re.compile(r"[1-9][0-9]*\Z"),
    "馬連": _re.compile(r"[1-9][0-9]*-[1-9][0-9]*\Z"),
    "ワイド": _re.compile(r"[1-9][0-9]*-[1-9][0-9]*\Z"),
    "3連複": _re.compile(r"[1-9][0-9]*-[1-9][0-9]*-[1-9][0-9]*\Z"),
}
_ARITIES = {"単勝": 1, "馬連": 2, "ワイド": 2, "3連複": 3}
_NORMAL_ROW_COUNTS = {"単勝": 1, "馬連": 1, "ワイド": 3, "3連複": 1}
_PROVIDER_TO_FORMAL = {"単勝": "単勝", "馬連複": "馬連", "ワイド": "ワイド", "三連複": "3連複"}
_TABLE_GROUPS = (
    frozenset({"単勝", "複勝", "枠連複", "馬連複"}),
    frozenset({"馬連単", "ワイド", "三連複", "三連単"}),
)
_SELECTION_CLASSES = ("a", "d")
_UNSUPPORTED_MARKERS = ("返還", "不成立", "同着", "特払い")
_FINALITY_STATEMENT = (
    "※2026年4月以降、優勝馬の情報はレース終了翌日までに表示されます。"
    "また、優勝馬の情報はレース結果確定時点の情報となります。"
)


def _validation(message: str) -> NARTargetRacePayoutPersistenceValidationError:
    return NARTargetRacePayoutPersistenceValidationError(message)


def _unavailable(message: str) -> NARTargetRacePayoutPersistenceUnavailableError:
    return NARTargetRacePayoutPersistenceUnavailableError(message)


def _unsupported(message: str) -> NARTargetRacePayoutPersistenceUnsupportedError:
    return NARTargetRacePayoutPersistenceUnsupportedError(message)


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


def _strict_direct_text(node: _Tag, name: str) -> str:
    if _direct_elements(node):
        raise _validation(f"{name} direct structure is invalid")
    values = tuple(item for item in node.children if isinstance(item, _NavigableString))
    if len(values) != 1:
        raise _validation(f"{name} direct text is invalid")
    value = _normalize("NFC", str(values[0]))
    if not value:
        raise _validation(f"{name} is missing")
    if any(character.isspace() for character in value):
        raise _validation(f"{name} contains whitespace")
    return value


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
    external_race_id = f"nar:{race_date:%Y%m%d}:{match.group('baba_code')}:{match.group('race_no')}"
    return external_race_id, race_date, match.group("race_no")


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
    if (
        label.get("class") != ["smallTitle"]
        or _heading(label.get_text(" ", strip=True), "official NAR winner information heading") != "優勝馬情報"
    ):
        raise _unavailable("official NAR winner information heading is unavailable")
    winner_children = _direct_elements(winner)
    if (
        tuple(item.name for item in winner_children) != ("span", "span", "a")
        or tuple(item.get("class") for item in winner_children)
        != (["smallFont01"], ["smallFont03"], ["cNaviBtn"])
        or not any(isinstance(item, _NavigableString) and str(item).strip() for item in winner.children)
        or any(
            not _display(table.get_text(" ", strip=True), "official NAR winner information table")
            for table in (info_table, pedigree_table, grade_table)
        )
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


def _known_unsupported(value: str) -> bool:
    return any(marker in value for marker in _UNSUPPORTED_MARKERS)


def _payout_tables(soup: _BeautifulSoup) -> tuple[_Tag, _Tag]:
    section = _one(
        soup.select("article.raceResult > div.innerWrapper > section.newRefundTable"),
        "official NAR payout publication section",
    )
    if section.get("class") != ["newRefundTable"] or set(section.attrs) != {"class"}:
        raise _validation("official NAR payout publication section is invalid")
    heading, wrapper = _require_tags(
        section,
        ("h4", "div"),
        "official NAR payout publication section",
    )
    if heading.attrs or wrapper.get("class") != ["twoRefundTable"] or set(wrapper.attrs) != {"class"}:
        raise _validation("official NAR payout table wrapper is invalid")
    (title,) = _require_tags(heading, ("span",), "official NAR payout publication heading")
    if (
        title.get("class") != ["smallTitle"]
        or set(title.attrs) != {"class"}
        or _heading(title.get_text(" ", strip=True), "official NAR payout publication heading") != "払戻金"
    ):
        raise _unavailable("official NAR payout publication heading is unavailable")
    tables = _require_tags(wrapper, ("table", "table"), "official NAR payout table wrapper")
    if any(table.attrs for table in tables):
        raise _validation("official NAR payout tables are invalid")
    return tables


def _row_cells(row: _Tag, *, selection_class: str, has_title: bool) -> tuple[_Tag, _Tag, _Tag, _Tag | None]:
    cells = _require_tags(
        row,
        tuple("td" for _ in range(4 if has_title else 3)),
        "official NAR payout row",
    )
    if row.attrs:
        raise _validation("official NAR payout row attributes are invalid")
    title = cells[0] if has_title else None
    offset = 1 if has_title else 0
    selection, amount, popularity = cells[offset:]
    expected_classes = ([selection_class], ["refundMoney"], ["c"])
    if tuple(cell.get("class") for cell in (selection, amount, popularity)) != expected_classes:
        raise _validation("official NAR payout row cell classes are invalid")
    if any(set(cell.attrs) != {"class"} for cell in (selection, amount, popularity)):
        raise _validation("official NAR payout row cell attributes are invalid")
    return selection, amount, popularity, title


def _table_groups(table: _Tag, *, table_index: int) -> dict[str, tuple[tuple[_Tag, _Tag], ...]]:
    (tbody,) = _require_tags(table, ("tbody",), "official NAR payout table")
    if tbody.attrs:
        raise _validation("official NAR payout tbody attributes are invalid")
    rows = _require_tags(
        tbody,
        tuple("tr" for _ in _direct_elements(tbody)),
        "official NAR payout tbody",
    )
    if not rows:
        raise _unavailable("official NAR payout rows are unavailable")
    expected_labels = _TABLE_GROUPS[table_index]
    selection_class = _SELECTION_CLASSES[table_index]
    groups: dict[str, tuple[tuple[_Tag, _Tag], ...]] = {}
    index = 0
    while index < len(rows):
        selection, amount, _popularity, title = _row_cells(
            rows[index],
            selection_class=selection_class,
            has_title=True,
        )
        assert title is not None
        if title.get("class") != ["title"] or set(title.attrs) != {"class", "rowspan"}:
            raise _validation("official NAR payout group title structure is invalid")
        rowspan = title.get("rowspan")
        if type(rowspan) is not str or _POSITIVE.fullmatch(rowspan) is None:
            raise _validation("official NAR payout group rowspan is invalid")
        count = int(rowspan)
        if index + count > len(rows):
            raise _validation("official NAR payout group exceeds table rows")
        label = _strict_direct_text(title, "official NAR payout group label")
        if label not in expected_labels:
            if _known_unsupported(label):
                raise _unsupported("official NAR exceptional payout group is unsupported")
            raise _validation("official NAR payout group label is unknown")
        if label in groups:
            raise _validation("official NAR payout group labels must be unique")
        values: list[tuple[_Tag, _Tag]] = [(selection, amount)]
        for continuation_index in range(index + 1, index + count):
            continuation = _row_cells(
                rows[continuation_index],
                selection_class=selection_class,
                has_title=False,
            )
            values.append((continuation[0], continuation[1]))
        groups[label] = tuple(values)
        index += count
    if set(groups) != set(expected_labels):
        raise _validation("official NAR payout group coverage is incomplete")
    return groups


def _requested_rows(soup: _BeautifulSoup, bet_type: str) -> tuple[tuple[_Tag, _Tag], ...]:
    tables = _payout_tables(soup)
    classified = tuple(_table_groups(table, table_index=index) for index, table in enumerate(tables))
    provider_label = next(label for label, formal in _PROVIDER_TO_FORMAL.items() if formal == bet_type)
    matching = tuple(rows for groups in classified for label, rows in groups.items() if label == provider_label)
    if len(matching) != 1:
        raise _validation("official NAR requested payout group must be unique")
    rows = matching[0]
    if len(rows) != _NORMAL_ROW_COUNTS[bet_type]:
        raise _validation("official NAR normal winning payout row count is invalid")
    return rows


def _selection_numbers(node: _Tag, bet_type: str) -> tuple[int, ...]:
    value = _strict_direct_text(node, "official NAR payout selection")
    if _known_unsupported(value):
        raise _unsupported("official NAR exceptional payout representation is unsupported")
    if _SELECTIONS[bet_type].fullmatch(value) is None:
        raise _validation("official NAR payout selection is invalid")
    tokens = value.split("-")
    numbers = tuple(int(token) for token in tokens)
    if len(numbers) != _ARITIES[bet_type] or len(set(numbers)) != len(numbers):
        raise _validation("official NAR payout selection is invalid")
    return numbers


def _amount(node: _Tag) -> int:
    value = _strict_direct_text(node, "official NAR payout amount")
    if _known_unsupported(value):
        raise _unsupported("official NAR exceptional payout representation is unsupported")
    if _AMOUNT.fullmatch(value) is None:
        raise _validation("official NAR payout amount is invalid")
    return int(value[:-1].replace(",", ""))


def normalize_and_persist_nar_target_race_payout(
    *,
    capture_id: str,
    capture_archive: NAROfficialResponseCaptureArchive,
    snapshot: HistoricalInputSnapshot,
    bet_type: str,
    payout_repository: PayoutRepository,
) -> PayoutPublication:
    """Persist one exact archived NAR normal-winning payout publication."""

    if type(capture_id) is not str or not capture_id:
        raise ValueError("capture_id must be a non-empty exact str")
    if isinstance(capture_archive, type) or not callable(getattr(capture_archive, "load_capture", None)):
        raise ValueError("capture_archive must provide callable load_capture")
    if type(snapshot) is not HistoricalInputSnapshot:
        raise ValueError("snapshot must be exact HistoricalInputSnapshot")
    if type(bet_type) is not str or bet_type not in BET_TYPES:
        raise ValueError("bet_type must be a supported exact str")
    if isinstance(payout_repository, type) or not callable(
        getattr(payout_repository, "save_payout_publication", None)
    ):
        raise ValueError("payout_repository must provide callable save_payout_publication")

    capture = capture_archive.load_capture(capture_id=capture_id)
    if capture is None:
        raise _unavailable("exact NAR payout capture is unavailable")
    if type(capture) is not NAROfficialResponseCapture:
        raise _validation("capture archive returned an invalid type")
    if capture.capture_id != capture_id:
        raise _validation("capture archive returned a different capture")
    if capture.page_kind is not NAROfficialPageKind.RACE_MARK_TABLE:
        raise _validation("capture page_kind must be RACE_MARK_TABLE")

    external_race_id, race_date, race_no = _canonical_race_context(capture)
    soup = _document(capture)
    _validate_visible_identity(soup, snapshot=snapshot, race_date=race_date, race_no=race_no)
    _validate_positive_finality(soup)
    snapshot_entry_ids = _snapshot_entry_ids(snapshot=snapshot, external_race_id=external_race_id)

    records: list[PayoutRecord] = []
    selections: set[tuple[int, ...]] = set()
    for selection_node, amount_node in _requested_rows(soup, bet_type):
        race_entry_ids: list[int] = []
        for horse_no in _selection_numbers(selection_node, bet_type):
            external_entry_id = f"{external_race_id}:entry:{horse_no}"
            race_entry_id = snapshot_entry_ids.get(external_entry_id)
            if race_entry_id is None:
                raise _validation("official NAR payout entry is unresolved")
            race_entry_ids.append(race_entry_id)
        try:
            normalized = _normalize_selection(race_entry_ids, bet_type)
        except ValueError as error:
            raise _validation("official NAR payout selection is invalid") from error
        if normalized in selections:
            raise _validation("official NAR payout selections must be unique")
        selections.add(normalized)
        records.append(PayoutRecord(normalized, _amount(amount_node), PayoutStatus.WINNING))

    publication = PayoutPublication(
        race_id=snapshot.internal_race_id,
        bet_type=bet_type,
        finalized_at=capture.observed_at,
        observed_at=capture.observed_at,
        is_complete=True,
        source=capture.capture_id,
        entries=tuple(records),
        source_url=capture.canonical_source_url,
    )
    return payout_repository.save_payout_publication(publication)
