"""Strict no-network NAR historical daily-target normalization."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass
from datetime import date as _date, datetime as _datetime, time as _time, timedelta as _timedelta, timezone as _timezone
from html import unescape as _html_unescape
from html.parser import HTMLParser as _HTMLParser
import hashlib as _hashlib
import re as _re

from scripts.simulation.historical_daily_targets import (
    DailyHistoricalReplayCompletenessEvidence as _DailyHistoricalReplayCompletenessEvidence,
    DailyHistoricalReplayProviderScope as _DailyHistoricalReplayProviderScope,
    DailyHistoricalReplayTarget as _DailyHistoricalReplayTarget,
    DailyHistoricalReplayTargetSet as _DailyHistoricalReplayTargetSet,
    DailyHistoricalTargetIntegrityError as _DailyHistoricalTargetIntegrityError,
    DailyTargetDiscoveryFailureCode as _DailyTargetDiscoveryFailureCode,
    HistoricalDailyProviderIdentity as _HistoricalDailyProviderIdentity,
    HistoricalDailyTargetEvidenceBundle as _HistoricalDailyTargetEvidenceBundle,
    ProviderNativeDispositionEvidenceReference as _ProviderNativeDispositionEvidenceReference,
    TargetDiscoveryIncompleteError as _TargetDiscoveryIncompleteError,
    build_daily_historical_replay_target_set as _build_daily_historical_replay_target_set,
)
from scripts.simulation.nar_historical_daily_target_capture import (
    NARHistoricalDailyTargetPageKind as _NARHistoricalDailyTargetPageKind,
    NARHistoricalDailyTargetRequestIdentity as _NARHistoricalDailyTargetRequestIdentity,
    NARHistoricalDailyTargetResponseCapture as _NARHistoricalDailyTargetResponseCapture,
)


_NAR = _HistoricalDailyProviderIdentity("NAR", "nar_official")
_NAR_SCOPE = _DailyHistoricalReplayProviderScope((_NAR,))
_INITIAL_DATE = _date(2020, 1, 1)
_POSITIVE = _re.compile(r"[1-9][0-9]*\Z")
_RACE_CELL = _re.compile(r"([1-9][0-9]*)R\Z")
_START_TIME = _re.compile(r"([0-9]{2}):([0-9]{2})\Z")
_RACE_LIST_RAW_TEXT = _re.compile(
    r"/KeibaWeb/TodayRaceInfo/RaceList\?k_raceDate=([0-9]{4})%2F([0-9]{2})%2F([0-9]{2})"
    r"&amp;k_babaCode=([1-9][0-9]*)\Z"
)
_DEBA_RAW_TEXT = _re.compile(
    r"/KeibaWeb/TodayRaceInfo/DebaTable\?k_raceDate=([0-9]{4})%2F([0-9]{2})%2F([0-9]{2})"
    r"&amp;k_raceNo=([1-9][0-9]*)&amp;k_babaCode=([1-9][0-9]*)\Z"
)
_HREF_DOUBLE = _re.compile(r'(?:^|\s)href\s*=\s*"([^"]*)"(?:\s|>)')
_HREF_ANY = _re.compile(r"(?:^|\s)href\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s>]+))(?:\s|>)")
_WARNING_SLICE = _re.compile(
    r'<section class="earlyWarning">\s*<div class="message">(?P<inner>.*?)</div>\s*</section>',
    _re.DOTALL,
)
_KANAZAWA_LINE_1 = "１２月２６日（金）金沢競馬は、降雪の影響により取り止めになりました。"
_KANAZAWA_LINE_2 = "なお、代替開催はありません。"
_KANAZAWA_WARNING = _re.compile(
    r"^[ \t\r\n]*" + _re.escape(_KANAZAWA_LINE_1) + r"<br>" + _re.escape(_KANAZAWA_LINE_2) + r"[ \t\r\n]*\Z"
)
_WEEKDAYS = "月火水木金土日"
_JST = _timezone(_timedelta(hours=9), "JST")
_VOID = frozenset({"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"})


class NARHistoricalDailyTargetSourceError(Exception):
    """Base error for NAR daily-target source normalization."""


class NARHistoricalDailyTargetSourceValidationError(NARHistoricalDailyTargetSourceError, ValueError):
    """Raised for malformed API input before evidence classification."""


class NARHistoricalDailyTargetSourceUnsupportedError(NARHistoricalDailyTargetSourceError):
    """Raised for direct use of a source state outside the initial profile."""


def _incomplete(
    code: _DailyTargetDiscoveryFailureCode,
    message: str,
    *references: str,
) -> _TargetDiscoveryIncompleteError:
    return _TargetDiscoveryIncompleteError(code, message, evidence_references=tuple(references))


def _required_text(value: object, name: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise NARHistoricalDailyTargetSourceValidationError(f"{name} must be an exact non-empty str")
    return value


def _positive(value: object, name: str) -> str:
    value = _required_text(value, name)
    if _POSITIVE.fullmatch(value) is None:
        raise NARHistoricalDailyTargetSourceValidationError(
            f"{name} must be a positive canonical ASCII decimal token"
        )
    return value


@_dataclass(slots=True)
class _Node:
    tag: str
    attrs: tuple[tuple[str, str | None], ...]
    raw_start: str
    content: list[object]

    def attr(self, name: str) -> str | None:
        values = [value for key, value in self.attrs if key == name]
        if len(values) > 1:
            raise ValueError(f"duplicate {name} attribute")
        return values[0] if values else None

    def has_attr(self, name: str) -> bool:
        values = [value for key, value in self.attrs if key == name]
        if len(values) > 1:
            raise ValueError(f"duplicate {name} attribute")
        return bool(values)

    def classes(self) -> tuple[str, ...]:
        value = self.attr("class")
        return () if value is None else tuple(value.split())

    def children(self, tag: str | None = None) -> tuple[_Node, ...]:
        values = tuple(item for item in self.content if type(item) is _Node)
        return values if tag is None else tuple(item for item in values if item.tag == tag)

    def descendants(self, tag: str | None = None) -> tuple[_Node, ...]:
        result: list[_Node] = []
        for child in self.children():
            if tag is None or child.tag == tag:
                result.append(child)
            result.extend(child.descendants(tag))
        return tuple(result)

    def raw_text(self) -> str:
        return "".join(item.raw_text() if type(item) is _Node else str(item) for item in self.content)

    def text(self) -> str:
        return _html_unescape(self.raw_text())


class _TreeParser(_HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.root = _Node("#document", (), "", [])
        self.stack = [self.root]
        self.structural_errors: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = _Node(tag, tuple(attrs), self.get_starttag_text(), [])
        self.stack[-1].content.append(node)
        if tag not in _VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.stack[-1].content.append(_Node(tag, tuple(attrs), self.get_starttag_text(), []))

    def handle_endtag(self, tag: str) -> None:
        positions = [index for index, node in enumerate(self.stack) if node.tag == tag]
        if not positions:
            self.structural_errors.append(f"unmatched closing tag {tag}")
            return
        del self.stack[positions[-1]:]

    def handle_data(self, data: str) -> None:
        self.stack[-1].content.append(data)

    def handle_entityref(self, name: str) -> None:
        self.stack[-1].content.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self.stack[-1].content.append(f"&#{name};")


def _parse(body: bytes, capture_id: str) -> tuple[str, _Node]:
    try:
        text = body.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise _incomplete(
            _DailyTargetDiscoveryFailureCode.MALFORMED_OFFICIAL_EVIDENCE,
            "official NAR response is not strict UTF-8",
            capture_id,
        ) from error
    parser = _TreeParser()
    try:
        parser.feed(text)
        parser.close()
    except (ValueError, TypeError) as error:
        raise _incomplete(
            _DailyTargetDiscoveryFailureCode.MALFORMED_OFFICIAL_EVIDENCE,
            "official NAR HTML cannot be parsed",
            capture_id,
        ) from error
    return text, parser.root


def _class_nodes(root: _Node, tag: str, class_name: str) -> tuple[_Node, ...]:
    result: list[_Node] = []
    for node in root.descendants(tag):
        try:
            if class_name in node.classes():
                result.append(node)
        except ValueError:
            continue
    return tuple(result)


def _single(values: tuple[_Node, ...], message: str, capture_id: str) -> _Node:
    if len(values) != 1:
        raise _incomplete(
            _DailyTargetDiscoveryFailureCode.MALFORMED_OFFICIAL_EVIDENCE,
            message,
            capture_id,
        )
    return values[0]


def _collapsed(node: _Node) -> str:
    return " ".join(node.text().split())


def _raw_href(node: _Node, *, require_double_quote: bool) -> str:
    pattern = _HREF_DOUBLE if require_double_quote else _HREF_ANY
    matches = tuple(pattern.finditer(node.raw_start))
    if len(matches) != 1:
        raise ValueError("href lexical attribute is missing or duplicated")
    groups = matches[0].groups()
    return next(value for value in groups if value is not None)


def _table_rows(table: _Node) -> tuple[_Node, ...]:
    direct = table.children("tr")
    bodies = table.children("tbody")
    if direct and bodies:
        raise ValueError("table mixes direct rows and tbody")
    if direct:
        return direct
    if len(bodies) != 1:
        raise ValueError("table must have exactly one tbody")
    return bodies[0].children("tr")


@_dataclass(frozen=True, slots=True)
class NARHistoricalVenueIdentity:
    baba_code: str
    display_name: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "baba_code", _positive(self.baba_code, "baba_code"))
        object.__setattr__(self, "display_name", _required_text(self.display_name, "display_name"))


@_dataclass(frozen=True, slots=True)
class NARMonthlyConveneInfoVenueLocator:
    venue_identity: NARHistoricalVenueIdentity
    official_mark: str
    raw_href: bytes
    request_identity: _NARHistoricalDailyTargetRequestIdentity
    envelope_capture_id: str
    envelope_response_sha256: str
    structural_locator: str


@_dataclass(frozen=True, slots=True)
class NARMonthlyConveneInfoEnvelope:
    target_date: _date
    capture_id: str
    response_sha256: str
    venue_locators: tuple[NARMonthlyConveneInfoVenueLocator, ...]


@_dataclass(frozen=True, slots=True)
class NARNativeDispositionEvidence:
    evidence_kind_and_version: str
    raw_value: bytes
    capture_id: str
    response_sha256: str
    structural_locator: str

    def to_reference(self) -> _ProviderNativeDispositionEvidenceReference:
        return _ProviderNativeDispositionEvidenceReference(
            self.evidence_kind_and_version,
            self.capture_id,
            self.response_sha256,
            self.structural_locator,
            _hashlib.sha256(self.raw_value).hexdigest(),
        )


@_dataclass(frozen=True, slots=True)
class NARRaceListTargetFragment:
    target_date: _date
    venue_identity: NARHistoricalVenueIdentity
    request_identity: _NARHistoricalDailyTargetRequestIdentity
    capture_id: str
    response_sha256: str
    navigation_venues: tuple[NARHistoricalVenueIdentity, ...]
    target_races: tuple[_DailyHistoricalReplayTarget, ...]
    completeness_evidence: _DailyHistoricalReplayCompletenessEvidence
    native_disposition: NARNativeDispositionEvidence | None


def _capture(
    value: object,
    kind: _NARHistoricalDailyTargetPageKind,
    name: str,
) -> _NARHistoricalDailyTargetResponseCapture:
    if type(value) is not _NARHistoricalDailyTargetResponseCapture:
        raise NARHistoricalDailyTargetSourceValidationError(
            f"{name} must be NARHistoricalDailyTargetResponseCapture"
        )
    if value.request_identity.page_kind is not kind:
        raise _incomplete(
            _DailyTargetDiscoveryFailureCode.INVALID_OFFICIAL_REQUEST_IDENTITY,
            f"{name} page kind is contradictory",
            value.capture_id,
        )
    try:
        request = _NARHistoricalDailyTargetRequestIdentity(
            value.request_identity.page_kind,
            value.request_identity.official_supplied_request_material,
            value.request_identity.resolved_request_url,
            value.request_identity.supplier_evidence_identity,
        )
        verified = _NARHistoricalDailyTargetResponseCapture(
            request,
            value.response_body,
            value.charset,
            value.requested_at,
            value.observed_at,
            value.stored_at,
            value.http_status,
            value.content_type,
            value.content_encoding,
            value.http_date,
            value.etag,
            value.last_modified,
            value.content_length,
        )
    except Exception as error:
        raise _DailyHistoricalTargetIntegrityError(
            f"{name} cannot be reconstructed as an immutable exact capture"
        ) from error
    if request != value.request_identity or verified != value:
        raise _DailyHistoricalTargetIntegrityError(
            f"{name} exact request/capture identity or digest is corrupt"
        )
    return value


def _race_list_raw_identity(raw_href: str) -> tuple[_date, str]:
    match = _RACE_LIST_RAW_TEXT.fullmatch(raw_href)
    if match is None:
        raise ValueError("RaceList href does not match exact source grammar")
    try:
        target_date = _date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    except ValueError as error:
        raise ValueError("RaceList href date is invalid") from error
    return target_date, match.group(4)


def normalize_nar_monthly_convene_info(
    *,
    target_date: _date,
    capture: _NARHistoricalDailyTargetResponseCapture,
) -> NARMonthlyConveneInfoEnvelope:
    if type(target_date) is not _date:
        raise NARHistoricalDailyTargetSourceValidationError("target_date must be exact date")
    capture = _capture(capture, _NARHistoricalDailyTargetPageKind.MONTHLY_CONVENE_INFO, "capture")
    request = capture.request_identity
    if request.target_year != target_date.year or request.target_month != target_date.month:
        raise _incomplete(
            _DailyTargetDiscoveryFailureCode.INVALID_OFFICIAL_REQUEST_IDENTITY,
            "MonthlyConveneInfo request does not identify target month",
            capture.capture_id,
        )
    _text, root = _parse(capture.response_body, capture.capture_id)
    try:
        article = _single(_class_nodes(root, "article", "monthlySchedule"), "Monthly article is not unique", capture.capture_id)
        selects = tuple(
            node for node in article.descendants("select")
            if node.attr("id") == "selectedYear" and node.attr("name") == "k_year"
        )
        select = _single(selects, "selected year control is not unique", capture.capture_id)
        selected = tuple(node for node in select.children("option") if node.has_attr("selected"))
        selected_year = _single(selected, "selected year is not unique", capture.capture_id)
        if selected_year.attr("value") != str(target_date.year) or _collapsed(selected_year) != str(target_date.year):
            raise ValueError("selected year contradicts request")
        tabs = _single(_class_nodes(article, "ul", "monthTab"), "month tab is not unique", capture.capture_id)
        active_tabs = tuple(node for node in tabs.children("li") if "active" in node.classes())
        active = _single(active_tabs, "active month is not unique", capture.capture_id)
        if (
            active.attr("id") != f"monthTab{target_date.month}"
            or active.attr("month") != str(target_date.month)
            or _collapsed(active) != f"{target_date.month}月"
        ):
            raise ValueError("active month contradicts request")
        table = _single(_class_nodes(article, "table", "schedule"), "schedule table is not unique", capture.capture_id)
        rows = _table_rows(table)
        if len(rows) < 3:
            raise ValueError("schedule table has no venue rows")
        header = rows[0].children()
        import calendar as _calendar
        days = _calendar.monthrange(target_date.year, target_date.month)[1]
        if len(header) != days + 2:
            raise ValueError("calendar header width is invalid")
        if _collapsed(header[0]) or _collapsed(header[-1]):
            raise ValueError("calendar boundary headers must be empty")
        if tuple(_collapsed(node) for node in header[1:-1]) != tuple(str(day) for day in range(1, days + 1)):
            raise ValueError("calendar day headers are invalid")
        weekday_row = rows[1].children()
        if len(weekday_row) != days + 2:
            raise ValueError("calendar weekday header width is invalid")
        if _collapsed(weekday_row[0]) or _collapsed(weekday_row[-1]):
            raise ValueError("calendar weekday boundary cells must be empty")
        expected_weekdays = tuple(
            _WEEKDAYS[_date(target_date.year, target_date.month, day).weekday()]
            for day in range(1, days + 1)
        )
        if tuple(_collapsed(node) for node in weekday_row[1:-1]) != expected_weekdays:
            raise ValueError("calendar weekday headers are invalid")
        locators: list[NARMonthlyConveneInfoVenueLocator] = []
        saw_unsupported = False
        for row_index, row in enumerate(rows[2:], start=2):
            cells = row.children()
            if len(cells) != days + 2 or any(cell.tag != "td" for cell in cells):
                raise ValueError("venue row width is invalid")
            display_name = _collapsed(cells[0])
            if not display_name or display_name != _collapsed(cells[-1]):
                raise ValueError("venue boundary display is invalid")
            cell = cells[target_date.day]
            anchors = cell.children("a")
            cell_text = _collapsed(cell)
            if not anchors and not cell_text:
                continue
            if len(anchors) != 1:
                saw_unsupported = True
                continue
            anchor = anchors[0]
            pair = (anchor.classes(), _collapsed(anchor))
            if pair not in {
                (("day",), "●"),
                (("night",), "☆"),
                (("day",), "Ｄ"),
                (("night",), "Ｄ"),
            }:
                saw_unsupported = True
                continue
            raw_href = _raw_href(anchor, require_double_quote=True)
            href_date, baba_code = _race_list_raw_identity(raw_href)
            if href_date != target_date:
                raise ValueError("target-date href is contradictory")
            venue = NARHistoricalVenueIdentity(baba_code, display_name)
            request_identity = _NARHistoricalDailyTargetRequestIdentity(
                _NARHistoricalDailyTargetPageKind.RACE_LIST,
                raw_href.encode("utf-8"),
                "https://www.keiba.go.jp" + _html_unescape(raw_href),
                capture.capture_id,
            )
            locators.append(
                NARMonthlyConveneInfoVenueLocator(
                    venue,
                    pair[1],
                    raw_href.encode("utf-8"),
                    request_identity,
                    capture.capture_id,
                    capture.response_sha256,
                    f"monthly-convene-info-v1:venue-row:{row_index}:day:{target_date.day}",
                )
            )
        if saw_unsupported:
            raise _incomplete(
                _DailyTargetDiscoveryFailureCode.UNSUPPORTED_ENVELOPE_STATE,
                "target-date calendar cell contains an unsupported mark or structure",
                capture.capture_id,
            )
        if not locators:
            raise _incomplete(
                _DailyTargetDiscoveryFailureCode.UNSUPPORTED_ENVELOPE_STATE,
                "blank MonthlyConveneInfo cells do not prove zero",
                capture.capture_id,
            )
        venue_keys = tuple(item.venue_identity.baba_code for item in locators)
        request_keys = tuple(item.request_identity.request_identity for item in locators)
        if len(set(venue_keys)) != len(venue_keys) or len(set(request_keys)) != len(request_keys):
            raise _incomplete(
                _DailyTargetDiscoveryFailureCode.DUPLICATE_EVIDENCE,
                "MonthlyConveneInfo contains duplicate venue or locator evidence",
                capture.capture_id,
            )
        return NARMonthlyConveneInfoEnvelope(
            target_date,
            capture.capture_id,
            capture.response_sha256,
            tuple(locators),
        )
    except _TargetDiscoveryIncompleteError:
        raise
    except (ValueError, TypeError) as error:
        raise _incomplete(
            _DailyTargetDiscoveryFailureCode.MALFORMED_OFFICIAL_EVIDENCE,
            str(error),
            capture.capture_id,
        ) from error


def _navigation(
    *,
    root: _Node,
    target_date: _date,
    expected_venue: NARHistoricalVenueIdentity,
    capture_id: str,
) -> tuple[NARHistoricalVenueIdentity, ...]:
    nav = _single(_class_nodes(root, "nav", "navWrapper"), "RaceList navigation is not unique", capture_id)
    area = _single(_class_nodes(nav, "div", "courseArea"), "RaceList course navigation is not unique", capture_id)
    anchors = tuple(node for node in area.children("a") if "courseBtn" in node.classes())
    active = tuple(node for node in anchors if "active" in node.classes())
    current = _single(active, "RaceList active course is not unique", capture_id)
    if current.has_attr("href") or _collapsed(current) != expected_venue.display_name:
        raise ValueError("RaceList active course contradicts expected venue")
    venues = [expected_venue]
    for anchor in anchors:
        if anchor is current:
            continue
        if "active" in anchor.classes():
            raise ValueError("RaceList course activity is contradictory")
        raw_href = _raw_href(anchor, require_double_quote=False)
        href_date, baba_code = _race_list_raw_identity(raw_href)
        if href_date != target_date:
            raise ValueError("RaceList navigation date is contradictory")
        venues.append(NARHistoricalVenueIdentity(baba_code, _collapsed(anchor)))
    if len({item.baba_code for item in venues}) != len(venues):
        raise ValueError("RaceList navigation venue is duplicated")
    return tuple(sorted(venues, key=lambda item: int(item.baba_code)))


def _warning(
    *,
    text: str,
    root: _Node,
    target_date: _date,
    expected_venue: NARHistoricalVenueIdentity,
    capture: _NARHistoricalDailyTargetResponseCapture,
) -> NARNativeDispositionEvidence | None:
    nodes = _class_nodes(root, "section", "earlyWarning")
    slices = tuple(match.group("inner") for match in _WARNING_SLICE.finditer(text))
    if not nodes and not slices:
        return None
    if len(nodes) != 1 or len(slices) != 1:
        raise _incomplete(
            _DailyTargetDiscoveryFailureCode.UNSUPPORTED_NATIVE_DISPOSITION,
            "RaceList warning structure is unsupported",
            capture.capture_id,
        )
    message_nodes = _class_nodes(nodes[0], "div", "message")
    if len(message_nodes) != 1:
        raise _incomplete(
            _DailyTargetDiscoveryFailureCode.UNSUPPORTED_NATIVE_DISPOSITION,
            "RaceList warning message is not unique",
            capture.capture_id,
        )
    inner = slices[0]
    if (
        target_date != _date(2025, 12, 26)
        or expected_venue.baba_code != "22"
        or expected_venue.display_name != "金沢"
        or _KANAZAWA_WARNING.fullmatch(inner) is None
    ):
        raise _incomplete(
            _DailyTargetDiscoveryFailureCode.UNSUPPORTED_NATIVE_DISPOSITION,
            "RaceList native disposition is outside the approved exact shape",
            capture.capture_id,
        )
    return NARNativeDispositionEvidence(
        "nar-race-list-whole-meeting-cancelled-no-substitute-v1",
        inner.encode("utf-8"),
        capture.capture_id,
        capture.response_sha256,
        "nar-race-list-v1:section.earlyWarning:div.message",
    )


def normalize_nar_race_list(
    *,
    target_date: _date,
    expected_venue: NARHistoricalVenueIdentity,
    expected_request: _NARHistoricalDailyTargetRequestIdentity,
    capture: _NARHistoricalDailyTargetResponseCapture,
) -> NARRaceListTargetFragment:
    if type(target_date) is not _date:
        raise NARHistoricalDailyTargetSourceValidationError("target_date must be exact date")
    if type(expected_venue) is not NARHistoricalVenueIdentity:
        raise NARHistoricalDailyTargetSourceValidationError("expected_venue must be NARHistoricalVenueIdentity")
    if type(expected_request) is not _NARHistoricalDailyTargetRequestIdentity:
        raise NARHistoricalDailyTargetSourceValidationError(
            "expected_request must be NARHistoricalDailyTargetRequestIdentity"
        )
    capture = _capture(capture, _NARHistoricalDailyTargetPageKind.RACE_LIST, "capture")
    if capture.request_identity != expected_request:
        raise _incomplete(
            _DailyTargetDiscoveryFailureCode.INVALID_OFFICIAL_REQUEST_IDENTITY,
            "RaceList capture does not match exact envelope-supplied request identity",
            capture.capture_id,
        )
    if expected_request.target_date != target_date or expected_request.baba_code != expected_venue.baba_code:
        raise _incomplete(
            _DailyTargetDiscoveryFailureCode.CONTRADICTORY_EVIDENCE,
            "RaceList request, date, and venue are contradictory",
            capture.capture_id,
        )
    text, root = _parse(capture.response_body, capture.capture_id)
    try:
        navigation = _navigation(
            root=root,
            target_date=target_date,
            expected_venue=expected_venue,
            capture_id=capture.capture_id,
        )
        section = _single(_class_nodes(root, "section", "raceTable"), "RaceList target section is not unique", capture.capture_id)
        direct_tables = section.children("table")
        candidates = tuple(table for table in direct_tables if not table.classes())
        table = _single(candidates, "RaceList target table is not unique", capture.capture_id)
        rows = _table_rows(table)
        if len(rows) < 3:
            raise ValueError("RaceList target table is incomplete")
        heading_cells = rows[0].children()
        if len(heading_cells) != 1 or heading_cells[0].tag != "th":
            raise ValueError("RaceList target heading is malformed")
        weekday = _WEEKDAYS[target_date.weekday()]
        expected_heading = (
            f"{target_date.year}年{target_date.month}月{target_date.day}日（{weekday}）"
            f"{expected_venue.display_name}競馬　当日メニュー"
        )
        heading = _re.sub(r"[ \t\r\n]+", "", heading_cells[0].text())
        if heading != expected_heading:
            raise ValueError("RaceList heading contradicts target date or venue")
        if rows[1].tag != "tr" or rows[1].classes() != ("subHeader",):
            raise ValueError("RaceList subheader is malformed")
        target_rows = rows[2:]
        if not target_rows or any(row.classes() != ("data",) for row in target_rows):
            raise ValueError("RaceList target rows are malformed")
        native = _warning(
            text=text,
            root=root,
            target_date=target_date,
            expected_venue=expected_venue,
            capture=capture,
        )
        targets: list[_DailyHistoricalReplayTarget] = []
        seen: set[str] = set()
        for row_index, row in enumerate(target_rows, start=1):
            cells = row.children("td")
            if len(cells) != 10 or len(row.children()) != 10:
                raise ValueError("RaceList target row must contain exactly ten cells")
            race_match = _RACE_CELL.fullmatch(_collapsed(cells[0]))
            time_match = _START_TIME.fullmatch(_collapsed(cells[1]))
            if race_match is None or time_match is None:
                raise ValueError("RaceList race number or start time is malformed")
            race_no = race_match.group(1)
            hour, minute = int(time_match.group(1)), int(time_match.group(2))
            if hour > 23 or minute > 59:
                raise ValueError("RaceList start time is invalid")
            title_anchors = cells[4].descendants("a")
            if len(title_anchors) != 1:
                raise ValueError("RaceList title anchor is not unique")
            raw_href = _raw_href(title_anchors[0], require_double_quote=False)
            href_match = _DEBA_RAW_TEXT.fullmatch(raw_href)
            if href_match is None:
                raise ValueError("RaceList title href grammar is malformed")
            try:
                href_date = _date(int(href_match.group(1)), int(href_match.group(2)), int(href_match.group(3)))
            except ValueError as error:
                raise ValueError("RaceList title href date is invalid") from error
            if (
                href_date != target_date
                or href_match.group(4) != race_no
                or href_match.group(5) != expected_venue.baba_code
            ):
                raise ValueError("RaceList row identity is contradictory")
            external_race_id = (
                f"nar:{target_date:%Y%m%d}:{expected_venue.baba_code}:{race_no}"
            )
            if external_race_id in seen:
                raise _incomplete(
                    _DailyTargetDiscoveryFailureCode.DUPLICATE_EVIDENCE,
                    "RaceList target identity is duplicated",
                    capture.capture_id,
                )
            seen.add(external_race_id)
            scheduled = _datetime.combine(target_date, _time(hour, minute), tzinfo=_JST).astimezone(_timezone.utc)
            disposition = native or NARNativeDispositionEvidence(
                "nar-race-list-target-row-v1",
                raw_href.encode("utf-8"),
                capture.capture_id,
                capture.response_sha256,
                f"nar-race-list-v1:target-row:{row_index}",
            )
            targets.append(
                _DailyHistoricalReplayTarget(
                    _NAR,
                    external_race_id,
                    scheduled,
                    disposition.to_reference(),
                )
            )
        completeness = _DailyHistoricalReplayCompletenessEvidence(
            _NAR,
            "nar-race-list-v1",
            capture.capture_id,
            capture.request_identity.request_identity,
            capture.response_sha256,
            capture.observed_at,
            None,
            f"nar:venue-day:{target_date.isoformat()}:{expected_venue.baba_code}",
        )
        return NARRaceListTargetFragment(
            target_date,
            expected_venue,
            expected_request,
            capture.capture_id,
            capture.response_sha256,
            navigation,
            tuple(targets),
            completeness,
            native,
        )
    except _TargetDiscoveryIncompleteError:
        raise
    except (ValueError, TypeError) as error:
        raise _incomplete(
            _DailyTargetDiscoveryFailureCode.MALFORMED_OFFICIAL_EVIDENCE,
            str(error),
            capture.capture_id,
        ) from error


def build_nar_historical_daily_target_evidence_bundle(
    *,
    target_date: _date,
    envelope_capture: _NARHistoricalDailyTargetResponseCapture,
    race_list_captures: tuple[_NARHistoricalDailyTargetResponseCapture, ...],
) -> _HistoricalDailyTargetEvidenceBundle:
    if type(target_date) is not _date:
        raise NARHistoricalDailyTargetSourceValidationError("target_date must be exact date")
    if target_date < _INITIAL_DATE:
        raise _incomplete(
            _DailyTargetDiscoveryFailureCode.UNSUPPORTED_TARGET_DATE,
            "target date precedes the approved NAR historical floor",
        )
    if envelope_capture is None:
        raise _incomplete(
            _DailyTargetDiscoveryFailureCode.MISSING_ENVELOPE_EVIDENCE,
            "MonthlyConveneInfo capture is missing",
        )
    envelope_capture = _capture(
        envelope_capture,
        _NARHistoricalDailyTargetPageKind.MONTHLY_CONVENE_INFO,
        "envelope_capture",
    )
    if type(race_list_captures) is not tuple:
        raise NARHistoricalDailyTargetSourceValidationError("race_list_captures must be tuple")
    if any(type(item) is not _NARHistoricalDailyTargetResponseCapture for item in race_list_captures):
        raise NARHistoricalDailyTargetSourceValidationError(
            "race_list_captures items must be NARHistoricalDailyTargetResponseCapture"
        )
    envelope = normalize_nar_monthly_convene_info(target_date=target_date, capture=envelope_capture)
    capture_keys = tuple(item.request_identity.request_identity for item in race_list_captures)
    if len(set(capture_keys)) != len(capture_keys):
        raise _incomplete(
            _DailyTargetDiscoveryFailureCode.DUPLICATE_EVIDENCE,
            "RaceList capture identity is duplicated",
            *(item.capture_id for item in race_list_captures),
        )
    by_request = {item.request_identity.request_identity: item for item in race_list_captures}
    expected = {item.request_identity.request_identity for item in envelope.venue_locators}
    actual = set(by_request)
    if expected - actual:
        raise _incomplete(
            _DailyTargetDiscoveryFailureCode.MISSING_PARTITION_EVIDENCE,
            "one or more envelope-supplied RaceList captures are missing",
            envelope.capture_id,
        )
    if actual - expected:
        raise _incomplete(
            _DailyTargetDiscoveryFailureCode.COVERAGE_SET_MISMATCH,
            "extra RaceList capture is outside the envelope",
            envelope.capture_id,
        )
    fragments = tuple(
        normalize_nar_race_list(
            target_date=target_date,
            expected_venue=locator.venue_identity,
            expected_request=locator.request_identity,
            capture=by_request[locator.request_identity.request_identity],
        )
        for locator in envelope.venue_locators
    )
    envelope_venues = {(item.venue_identity.baba_code, item.venue_identity.display_name) for item in envelope.venue_locators}
    fragment_venues = {(item.venue_identity.baba_code, item.venue_identity.display_name) for item in fragments}
    if envelope_venues != fragment_venues or any(
        {(item.baba_code, item.display_name) for item in fragment.navigation_venues} != envelope_venues
        for fragment in fragments
    ):
        raise _incomplete(
            _DailyTargetDiscoveryFailureCode.COVERAGE_SET_MISMATCH,
            "envelope, fragment, and navigation venue sets are not exactly equal",
            envelope.capture_id,
            *(item.capture_id for item in fragments),
        )
    targets = tuple(item for fragment in fragments for item in fragment.target_races)
    if len({_target.external_race_id for _target in targets}) != len(targets):
        raise _incomplete(
            _DailyTargetDiscoveryFailureCode.CONTRADICTORY_EVIDENCE,
            "target race identity overlaps across RaceList fragments",
            *(item.capture_id for item in fragments),
        )
    envelope_evidence = _DailyHistoricalReplayCompletenessEvidence(
        _NAR,
        "nar-monthly-convene-info-v1",
        envelope_capture.capture_id,
        envelope_capture.request_identity.request_identity,
        envelope_capture.response_sha256,
        envelope_capture.observed_at,
        None,
        f"nar:provider-day-envelope:{target_date.isoformat()}",
    )
    return _HistoricalDailyTargetEvidenceBundle(
        _NAR,
        target_date,
        targets,
        (envelope_evidence,) + tuple(item.completeness_evidence for item in fragments),
    )


def build_nar_historical_daily_replay_target_set(
    *,
    target_date: _date,
    envelope_capture: _NARHistoricalDailyTargetResponseCapture,
    race_list_captures: tuple[_NARHistoricalDailyTargetResponseCapture, ...],
) -> _DailyHistoricalReplayTargetSet:
    bundle = build_nar_historical_daily_target_evidence_bundle(
        target_date=target_date,
        envelope_capture=envelope_capture,
        race_list_captures=race_list_captures,
    )
    return _build_daily_historical_replay_target_set(
        target_date=target_date,
        provider_scope=_NAR_SCOPE,
        evidence_bundles=(bundle,),
    )


if "annotations" in globals():
    del annotations
