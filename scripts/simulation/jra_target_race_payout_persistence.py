"""Persist one exact archived JRA normal-winning payout publication."""

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
    BET_TYPES,
    PayoutPublication,
    PayoutRecord,
    PayoutRepository,
    PayoutStatus,
    normalize_selection as _normalize_selection,
)

__all__ = (
    "JRATargetRacePayoutPersistenceError",
    "JRATargetRacePayoutPersistenceValidationError",
    "JRATargetRacePayoutPersistenceUnavailableError",
    "JRATargetRacePayoutPersistenceUnsupportedError",
    "normalize_and_persist_jra_target_race_payout",
)


class JRATargetRacePayoutPersistenceError(ValueError):
    """Base error for the narrow JRA target-payout persistence boundary."""


class JRATargetRacePayoutPersistenceValidationError(JRATargetRacePayoutPersistenceError):
    """Raised for malformed or contradictory archived payout evidence."""


class JRATargetRacePayoutPersistenceUnavailableError(JRATargetRacePayoutPersistenceError):
    """Raised when exact capture or normal-final payout evidence is unavailable."""


class JRATargetRacePayoutPersistenceUnsupportedError(JRATargetRacePayoutPersistenceError):
    """Raised for recognized payout representations outside normal-winning support."""


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
_HORSE_NUMBER = _re.compile(r"[1-9][0-9]*\Z")
_AMOUNT = _re.compile(r"[1-9][0-9]{0,2}(?:,[0-9]{3})*\Z")
_UNSUPPORTED_MARKERS = frozenset({"返還", "不成立", "同着", "特払い"})
_GROUP_ITEMS = {
    "left": (("win", "単勝"), ("place", "複勝")),
    "center": (("wakuren", "枠連"), ("wide", "ワイド")),
    "right": (("umaren", "馬連"), ("umatan", "馬単"), ("trio", "3連複"), ("tierce", "3連単")),
}
_REQUESTED_ITEMS = {
    "単勝": ("left", "win"),
    "馬連": ("right", "umaren"),
    "ワイド": ("center", "wide"),
    "3連複": ("right", "trio"),
}
_ARITIES = {"単勝": 1, "馬連": 2, "ワイド": 2, "3連複": 3}
_NORMAL_LINE_COUNTS = {"単勝": 1, "馬連": 1, "ワイド": 3, "3連複": 1}


def _validation(message: str) -> JRATargetRacePayoutPersistenceValidationError:
    return JRATargetRacePayoutPersistenceValidationError(message)


def _unavailable(message: str) -> JRATargetRacePayoutPersistenceUnavailableError:
    return JRATargetRacePayoutPersistenceUnavailableError(message)


def _unsupported(message: str) -> JRATargetRacePayoutPersistenceUnsupportedError:
    return JRATargetRacePayoutPersistenceUnsupportedError(message)


def _one(values: object, name: str) -> _Tag:
    items = tuple(values)  # type: ignore[arg-type]
    if len(items) != 1 or not isinstance(items[0], _Tag):
        raise _validation(f"{name} must be unique")
    return items[0]


def _direct_tags(node: _Tag) -> tuple[_Tag, ...]:
    return tuple(value for value in node.children if isinstance(value, _Tag))


def _require_no_direct_text(node: _Tag, name: str) -> None:
    if any(
        _normalize("NFC", str(value)).strip()
        for value in node.children
        if not isinstance(value, _Tag)
    ):
        raise _validation(f"{name} has unclassified direct text")


def _one_direct(node: _Tag, *, tag_name: str, class_name: str, name: str) -> _Tag:
    return _one(
        tuple(
            value
            for value in _direct_tags(node)
            if value.name == tag_name
            and (
                not tuple(value.get("class", ()))
                if class_name == ""
                else class_name in tuple(value.get("class", ()))
            )
        ),
        name,
    )


def _display(value: object, name: str) -> str:
    if type(value) is not str:
        raise _validation(f"{name} is invalid")
    result = " ".join(_normalize("NFC", value).split())
    if not result:
        raise _validation(f"{name} is missing")
    return result


def _strict_direct_text(node: _Tag, name: str) -> str:
    if _direct_tags(node):
        raise _validation(f"{name} structure is invalid")
    text = _normalize("NFC", "".join(str(value) for value in node.children)).strip()
    if not text:
        raise _validation(f"{name} is missing")
    if any(character.isspace() for character in text):
        raise _validation(f"{name} contains whitespace")
    return text


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
    race_match = _RACE_NUMBER.fullmatch(_display(race_node.get("alt"), "official JRA race number"))
    if race_match is None or int(race_match.group("race")) != int(race_identity.race_number):
        raise _validation("official JRA race number disagrees")


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


def _payout_unit(soup: _BeautifulSoup) -> _Tag:
    area = _one(soup.select("#race_result .refund_area"), "official JRA payout publication area")
    header = _one_direct(area, tag_name="div", class_name="block_header", name="official JRA payout publication heading")
    content = _one_direct(header, tag_name="div", class_name="content", name="official JRA payout heading content")
    heading = _one_direct(content, tag_name="h2", class_name="", name="official JRA payout heading")
    if _display(heading.get_text(" ", strip=True), "official JRA payout publication heading") != "払戻金":
        raise _unavailable("official JRA payout publication heading is unavailable")
    unit = _one_direct(area, tag_name="div", class_name="refund_unit", name="official JRA payout publication container")
    _validate_unit_layout(unit)
    return unit


def _validate_unit_layout(unit: _Tag) -> None:
    groups = _direct_tags(unit)
    if len(groups) != len(_GROUP_ITEMS):
        raise _validation("official JRA payout groups are invalid")
    by_name: dict[str, _Tag] = {}
    for group in groups:
        names = tuple(group.get("class", ()))
        if group.name != "div" or len(names) != 1 or names[0] not in _GROUP_ITEMS or names[0] in by_name:
            raise _validation("official JRA payout groups are invalid")
        by_name[names[0]] = group
    if set(by_name) != set(_GROUP_ITEMS):
        raise _validation("official JRA payout groups are invalid")
    for group_name, expected in _GROUP_ITEMS.items():
        listing = _one_direct(
            by_name[group_name],
            tag_name="ul",
            class_name="",
            name=f"official JRA {group_name} payout list",
        )
        items = _direct_tags(listing)
        if len(items) != len(expected):
            raise _validation("official JRA payout item layout is invalid")
        found: dict[str, _Tag] = {}
        labels = dict(expected)
        for item in items:
            classes = tuple(item.get("class", ()))
            if item.name != "li" or len(classes) != 1 or classes[0] not in labels or classes[0] in found:
                raise _validation("official JRA payout item layout is invalid")
            label = _item_label(item)
            if label != labels[classes[0]]:
                raise _validation("official JRA payout item label is invalid")
            found[classes[0]] = item
        if set(found) != set(labels):
            raise _validation("official JRA payout item layout is invalid")


def _item_label(item: _Tag) -> str:
    definition = _one_direct(item, tag_name="dl", class_name="", name="official JRA payout item definition")
    children = _direct_tags(definition)
    if len(children) != 2 or tuple(child.name for child in children) != ("dt", "dd"):
        raise _validation("official JRA payout item definition is invalid")
    return _display(children[0].get_text(" ", strip=True), "official JRA payout item label")


def _requested_item(unit: _Tag, bet_type: str) -> _Tag:
    group_name, class_name = _REQUESTED_ITEMS[bet_type]
    group = _one(
        tuple(
            value
            for value in _direct_tags(unit)
            if value.name == "div" and tuple(value.get("class", ())) == (group_name,)
        ),
        "official JRA requested payout group",
    )
    listing = _one_direct(group, tag_name="ul", class_name="", name="official JRA requested payout list")
    item = _one(
        tuple(
            value
            for value in _direct_tags(listing)
            if value.name == "li" and tuple(value.get("class", ())) == (class_name,)
        ),
        "official JRA requested payout item",
    )
    if _item_label(item) != bet_type:
        raise _validation("official JRA requested payout label disagrees")
    return item


def _requested_lines(item: _Tag, bet_type: str) -> tuple[_Tag, ...]:
    _require_no_direct_text(item, "official JRA requested payout item")
    item_children = _direct_tags(item)
    if len(item_children) != 1 or item_children[0].name != "dl" or tuple(item_children[0].get("class", ())) != ():
        raise _validation("official JRA requested payout item structure is invalid")
    definition = item_children[0]
    _require_no_direct_text(definition, "official JRA requested payout definition")
    children = _direct_tags(definition)
    if len(children) != 2 or tuple(child.name for child in children) != ("dt", "dd"):
        raise _validation("official JRA requested payout definition is invalid")
    if _display(children[0].get_text(" ", strip=True), "official JRA requested payout label") != bet_type:
        raise _validation("official JRA requested payout label disagrees")
    payout_rows = children[1]
    _require_no_direct_text(payout_rows, "official JRA requested payout rows")
    lines = _direct_tags(payout_rows)
    if len(lines) != _NORMAL_LINE_COUNTS[bet_type]:
        raise _validation("official JRA normal winning payout line count is invalid")
    if any(line.name != "div" or tuple(line.get("class", ())) != ("line",) for line in lines):
        raise _validation("official JRA payout line structure is invalid")
    return lines


def _exceptional(value: str) -> bool:
    return any(marker in value for marker in _UNSUPPORTED_MARKERS)


def _selection_numbers(line: _Tag, bet_type: str) -> tuple[int, ...]:
    _require_no_direct_text(line, "official JRA payout line")
    children = _direct_tags(line)
    if (
        len(children) != 3
        or tuple(child.name for child in children) != ("div", "div", "div")
        or tuple(tuple(child.get("class", ())) for child in children) != (("num",), ("yen",), ("pop",))
    ):
        raise _validation("official JRA payout line structure is invalid")
    value = _strict_direct_text(children[0], "official JRA payout selection")
    if _exceptional(value):
        raise _unsupported("official JRA exceptional payout representation is unsupported")
    tokens = value.split("-")
    if len(tokens) != _ARITIES[bet_type] or any(_HORSE_NUMBER.fullmatch(token) is None for token in tokens):
        raise _validation("official JRA payout selection is invalid")
    numbers = tuple(int(token) for token in tokens)
    if len(set(numbers)) != len(numbers):
        raise _validation("official JRA payout selection has duplicate horse numbers")
    return numbers


def _amount(line: _Tag) -> int:
    yen = _direct_tags(line)[1]
    children = _direct_tags(yen)
    if len(children) != 1 or children[0].name != "span" or tuple(children[0].get("class", ())) != ("unit",):
        raise _validation("official JRA payout amount structure is invalid")
    unit = _strict_direct_text(children[0], "official JRA payout amount unit")
    if unit != "円":
        raise _validation("official JRA payout amount unit is invalid")
    texts = tuple(
        _normalize("NFC", str(value)).strip()
        for value in yen.children
        if not isinstance(value, _Tag) and _normalize("NFC", str(value)).strip()
    )
    if len(texts) != 1:
        raise _validation("official JRA payout amount has duplicate numeric text")
    direct_text = texts[0]
    if not direct_text:
        raise _validation("official JRA payout amount is missing")
    if any(character.isspace() for character in direct_text) or _AMOUNT.fullmatch(direct_text) is None:
        if _exceptional(direct_text):
            raise _unsupported("official JRA exceptional payout representation is unsupported")
        raise _validation("official JRA payout amount is invalid")
    return int(direct_text.replace(",", ""))


def normalize_and_persist_jra_target_race_payout(
    *,
    capture_id: str,
    capture_archive: JRAOfficialResponseCaptureArchive,
    snapshot: HistoricalInputSnapshot,
    bet_type: str,
    payout_repository: PayoutRepository,
) -> PayoutPublication:
    """Persist one exact archived JRA normal-winning payout publication."""

    if type(capture_id) is not str or not capture_id:
        raise ValueError("capture_id must be a non-empty exact str")
    if isinstance(capture_archive, type) or not callable(getattr(capture_archive, "load_capture", None)):
        raise ValueError("capture_archive must provide callable load_capture")
    if type(snapshot) is not HistoricalInputSnapshot:
        raise ValueError("snapshot must be exact HistoricalInputSnapshot")
    if type(bet_type) is not str or bet_type not in BET_TYPES:
        raise ValueError("bet_type must be a supported exact str")
    if isinstance(payout_repository, type) or not callable(getattr(payout_repository, "save_payout_publication", None)):
        raise ValueError("payout_repository must provide callable save_payout_publication")

    capture = capture_archive.load_capture(capture_id=capture_id)
    if capture is None:
        raise _unavailable("exact JRA payout capture is unavailable")
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
    snapshot_entry_ids = _snapshot_entry_ids(snapshot=snapshot, race_identity=capture_race_identity)
    item = _requested_item(_payout_unit(soup), bet_type)

    records: list[PayoutRecord] = []
    selections: set[tuple[int, ...]] = set()
    for line in _requested_lines(item, bet_type):
        horse_numbers = _selection_numbers(line, bet_type)
        race_entry_ids: list[int] = []
        for horse_no in horse_numbers:
            external_entry_id = _build_jra_external_entry_id(race_identity=capture_race_identity, horse_no=horse_no)
            race_entry_id = snapshot_entry_ids.get(external_entry_id)
            if race_entry_id is None:
                raise _validation("official JRA payout entry is unresolved")
            race_entry_ids.append(race_entry_id)
        try:
            normalized = _normalize_selection(race_entry_ids, bet_type)
        except ValueError as error:
            raise _validation("official JRA payout selection is invalid") from error
        if normalized in selections:
            raise _validation("official JRA payout selections must be unique")
        selections.add(normalized)
        records.append(PayoutRecord(normalized, _amount(line), PayoutStatus.WINNING))

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
