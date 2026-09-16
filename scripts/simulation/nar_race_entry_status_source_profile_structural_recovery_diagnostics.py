"""Pure bounded structural explanations; no qualification or publication decisions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from html.parser import HTMLParser
import json

from bs4 import BeautifulSoup, ParserRejectedMarkup
from bs4.element import Tag

from scripts.simulation import nar_race_entry_status_raw_capture as _raw_capture
from scripts.simulation.nar_race_entry_status_source_profile_diagnostics import (
    _direct_cells,
    _normalized_cell,
)
from scripts.simulation.nar_race_entry_status_source_profile_profile_a import _VOID_TAGS


STRICT_STRUCTURE_RECOVERY_SCHEMA = "nar-race-entry-status-strict-structure-recovery-diagnostics"
CANDIDATE_ANCESTRY_RECOVERY_SCHEMA = "nar-race-entry-status-profile-b-candidate-ancestry-recovery-diagnostics"
SCHEMA_VERSION = 1
MAX_RETAINED_CANDIDATE_DETAILS = 8
_MAX_SAFE_COUNT = 10_000
_ROLES = ("deba_table", "race_list")
_FAILURE_KINDS = frozenset({
    "PASS", "END_TAG_EMPTY_STACK", "END_TAG_MISMATCH", "UNCLOSED_STACK_AT_CLOSE",
})
_TABLE_ROLES = frozenset({"RACE_SCHEDULE_TABLE", "CHANGE_INFO_TABLE", "OTHER_TABLE", "NO_TABLE"})


class StructuralTag(StrEnum):
    HTML = "HTML"
    HEAD = "HEAD"
    TITLE = "TITLE"
    BODY = "BODY"
    MAIN = "MAIN"
    HEADER = "HEADER"
    FOOTER = "FOOTER"
    NAV = "NAV"
    ARTICLE = "ARTICLE"
    SECTION = "SECTION"
    ASIDE = "ASIDE"
    DIV = "DIV"
    H1 = "H1"
    H2 = "H2"
    H3 = "H3"
    H4 = "H4"
    H5 = "H5"
    H6 = "H6"
    P = "P"
    SPAN = "SPAN"
    A = "A"
    STRONG = "STRONG"
    EM = "EM"
    B = "B"
    I = "I"
    U = "U"
    UL = "UL"
    OL = "OL"
    LI = "LI"
    DL = "DL"
    DT = "DT"
    DD = "DD"
    TABLE = "TABLE"
    CAPTION = "CAPTION"
    COLGROUP = "COLGROUP"
    THEAD = "THEAD"
    TBODY = "TBODY"
    TFOOT = "TFOOT"
    TR = "TR"
    TH = "TH"
    TD = "TD"
    FORM = "FORM"
    FIELDSET = "FIELDSET"
    LEGEND = "LEGEND"
    LABEL = "LABEL"
    BUTTON = "BUTTON"
    SELECT = "SELECT"
    OPTGROUP = "OPTGROUP"
    OPTION = "OPTION"
    TEXTAREA = "TEXTAREA"
    SCRIPT = "SCRIPT"
    STYLE = "STYLE"
    NOSCRIPT = "NOSCRIPT"
    TEMPLATE = "TEMPLATE"
    DETAILS = "DETAILS"
    SUMMARY = "SUMMARY"
    FIGURE = "FIGURE"
    FIGCAPTION = "FIGCAPTION"
    PICTURE = "PICTURE"
    CANVAS = "CANVAS"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    OBJECT = "OBJECT"
    MAP = "MAP"
    FONT = "FONT"
    CENTER = "CENTER"
    OTHER_OR_CUSTOM = "OTHER_OR_CUSTOM"


_TAG_BY_NAME = {tag.value.lower(): tag for tag in StructuralTag if tag is not StructuralTag.OTHER_OR_CUSTOM}


class NARStructuralRecoveryDiagnosticsValidationError(ValueError):
    """Malformed input, contradictory bounded evidence, or failed diagnosis."""


def _error(message: str) -> NARStructuralRecoveryDiagnosticsValidationError:
    return NARStructuralRecoveryDiagnosticsValidationError(message)


def _count(value: object) -> int:
    if type(value) is not int or not 0 <= value <= _MAX_SAFE_COUNT:
        raise _error("count must be an exact bounded nonnegative int")
    return value


def _bool(value: object) -> bool:
    if type(value) is not bool:
        raise _error("boolean must be exact bool")
    return value


def _target(value: object) -> _raw_capture.NARRaceEntryStatusRaceIdentity:
    if type(value) is not _raw_capture.NARRaceEntryStatusRaceIdentity:
        raise _error("target must be exact formal race identity")
    try:
        target = _raw_capture.NARRaceEntryStatusRaceIdentity(value.baba_code, value.race_date, value.race_no)
        _count(target.race_no)
        if len(target.baba_code.encode("utf-8")) > 512:
            raise _error("formal code exceeds safe string bound")
        return target
    except Exception:
        pass
    raise _error("formal target is invalid") from None


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


@dataclass(frozen=True, slots=True)
class StrictStructureRecoveryDocumentResult:
    document_role: str
    failure_kind: str
    event_index: int
    stack_depth: int
    expected_open_tag: StructuralTag | None
    observed_end_tag: StructuralTag | None
    tolerant_parse: str

    def __post_init__(self) -> None:
        if type(self.document_role) is not str or self.document_role not in _ROLES:
            raise _error("document role is invalid")
        if type(self.failure_kind) is not str or self.failure_kind not in _FAILURE_KINDS:
            raise _error("structural failure kind is invalid")
        _count(self.event_index)
        _count(self.stack_depth)
        for tag in (self.expected_open_tag, self.observed_end_tag):
            if tag is not None and type(tag) is not StructuralTag:
                raise _error("tag must be exact bounded enum or null")
        if type(self.tolerant_parse) is not str or self.tolerant_parse not in {"PASS", "FAIL"}:
            raise _error("tolerant parse outcome is invalid")
        expected, observed = self.expected_open_tag, self.observed_end_tag
        valid = {
            "PASS": self.stack_depth == 0 and expected is None and observed is None,
            "END_TAG_EMPTY_STACK": self.event_index >= 1 and self.stack_depth == 0 and expected is None and observed is not None,
            "END_TAG_MISMATCH": self.event_index >= 1 and self.stack_depth >= 1 and expected is not None and observed is not None,
            "UNCLOSED_STACK_AT_CLOSE": self.stack_depth >= 1 and expected is not None and observed is None,
        }
        if not valid[self.failure_kind]:
            raise _error("structural fields are contradictory")

    def to_canonical_dict(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "document_role": self.document_role, "failure_kind": self.failure_kind,
            "event_index": self.event_index, "stack_depth": self.stack_depth,
            "expected_open_tag": None if self.expected_open_tag is None else self.expected_open_tag.value,
            "observed_end_tag": None if self.observed_end_tag is None else self.observed_end_tag.value,
            "tolerant_parse": self.tolerant_parse,
        }


@dataclass(frozen=True, slots=True)
class StrictStructureRecoveryDiagnostics:
    document_results: tuple[StrictStructureRecoveryDocumentResult, ...]

    def __post_init__(self) -> None:
        if type(self.document_results) is not tuple or len(self.document_results) != 2:
            raise _error("document results require exact two-result tuple")
        if any(type(result) is not StrictStructureRecoveryDocumentResult for result in self.document_results):
            raise _error("document result type is invalid")
        if tuple(result.document_role for result in self.document_results) != _ROLES:
            raise _error("document role order is invalid")
        for result in self.document_results:
            result.__post_init__()

    def to_canonical_dict(self) -> dict[str, object]:
        self.__post_init__()
        return {"schema": STRICT_STRUCTURE_RECOVERY_SCHEMA, "schema_version": SCHEMA_VERSION,
                "document_results": [result.to_canonical_dict() for result in self.document_results]}

    def canonical_bytes(self) -> bytes:
        return _canonical_bytes(self.to_canonical_dict())


class _StructuralStop(Exception):
    """Internal control signal with no source or exception text."""


class _DiagnosticStrictStructureParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.stack: list[str] = []
        self.event_index = 0
        self.failure_kind = "PASS"
        self.expected: StructuralTag | None = None
        self.observed: StructuralTag | None = None

    def _event(self) -> None:
        self.event_index = _count(self.event_index + 1)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._event()
        if tag not in _VOID_TAGS:
            _count(len(self.stack) + 1)
            self.stack.append(tag)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._event()

    def handle_endtag(self, tag: str) -> None:
        self._event()
        if tag in _VOID_TAGS:
            return
        if not self.stack:
            self.failure_kind = "END_TAG_EMPTY_STACK"
        elif self.stack[-1] != tag:
            self.failure_kind = "END_TAG_MISMATCH"
            self.expected = _TAG_BY_NAME.get(self.stack[-1], StructuralTag.OTHER_OR_CUSTOM)
        else:
            self.stack.pop()
            return
        self.observed = _TAG_BY_NAME.get(tag, StructuralTag.OTHER_OR_CUSTOM)
        raise _StructuralStop()

    def close(self) -> None:
        super().close()
        if self.stack:
            self.failure_kind = "UNCLOSED_STACK_AT_CLOSE"
            self.expected = _TAG_BY_NAME.get(self.stack[-1], StructuralTag.OTHER_OR_CUSTOM)
            raise _StructuralStop()


def _strict_document(role: str, value: bytes) -> StrictStructureRecoveryDocumentResult:
    if type(value) is not bytes:
        raise _error("document input must be exact bytes")
    source = value.decode("utf-8", errors="strict")
    parser = _DiagnosticStrictStructureParser()
    try:
        parser.feed(source)
        parser.close()
    except _StructuralStop:
        pass
    tolerant = "PASS"
    try:
        BeautifulSoup(source, "html.parser")
    except ParserRejectedMarkup:
        tolerant = "FAIL"
    return StrictStructureRecoveryDocumentResult(
        role, parser.failure_kind, parser.event_index, len(parser.stack),
        parser.expected, parser.observed, tolerant,
    )


def diagnose_nar_race_entry_status_strict_structure_recovery(
    *, deba_table_bytes: bytes, race_list_bytes: bytes,
) -> StrictStructureRecoveryDiagnostics:
    """Explain structural branches for exact bytes without retaining source data."""
    try:
        return StrictStructureRecoveryDiagnostics((
            _strict_document("deba_table", deba_table_bytes),
            _strict_document("race_list", race_list_bytes),
        ))
    except Exception:
        pass
    raise _error("strict structural diagnosis could not be completed") from None


@dataclass(frozen=True, slots=True)
class ProfileBCandidateAncestryRecoveryResult:
    candidate_ordinal: int
    nearest_table_role: str
    inside_change_info_table: bool
    nested_table_depth_within_race_scope: int
    direct_schedule_table_descendant: bool

    def __post_init__(self) -> None:
        if type(self.candidate_ordinal) is not int or not 1 <= self.candidate_ordinal <= MAX_RETAINED_CANDIDATE_DETAILS:
            raise _error("candidate ordinal is invalid")
        if type(self.nearest_table_role) is not str or self.nearest_table_role not in _TABLE_ROLES:
            raise _error("nearest table role is invalid")
        inside = _bool(self.inside_change_info_table)
        direct = _bool(self.direct_schedule_table_descendant)
        depth = _count(self.nested_table_depth_within_race_scope)
        valid = {
            "NO_TABLE": depth == 0 and not inside and not direct,
            "RACE_SCHEDULE_TABLE": depth == 1 and not inside and direct,
            "CHANGE_INFO_TABLE": depth >= 1 and inside and not direct,
            "OTHER_TABLE": depth >= 2 and not direct,
        }
        if not valid[self.nearest_table_role]:
            raise _error("ancestry fields are contradictory")

    def to_canonical_dict(self) -> dict[str, object]:
        self.__post_init__()
        return {"candidate_ordinal": self.candidate_ordinal, "nearest_table_role": self.nearest_table_role,
                "inside_change_info_table": self.inside_change_info_table,
                "nested_table_depth_within_race_scope": self.nested_table_depth_within_race_scope,
                "direct_schedule_table_descendant": self.direct_schedule_table_descendant}


@dataclass(frozen=True, slots=True)
class ProfileBCandidateAncestryRecoveryDiagnostics:
    target: _raw_capture.NARRaceEntryStatusRaceIdentity
    race_table_scope_count: int
    target_candidate_count: int
    candidate_details_complete: bool
    candidate_results: tuple[ProfileBCandidateAncestryRecoveryResult, ...]

    def __post_init__(self) -> None:
        _target(self.target)
        _count(self.race_table_scope_count)
        _count(self.target_candidate_count)
        _bool(self.candidate_details_complete)
        if type(self.candidate_results) is not tuple or len(self.candidate_results) > MAX_RETAINED_CANDIDATE_DETAILS:
            raise _error("candidate results must be exact bounded tuple")
        for ordinal, result in enumerate(self.candidate_results, 1):
            if type(result) is not ProfileBCandidateAncestryRecoveryResult:
                raise _error("candidate result type is invalid")
            result.__post_init__()
            if result.candidate_ordinal != ordinal:
                raise _error("candidate ordinals are not contiguous")
        complete = self.race_table_scope_count == 1 and self.target_candidate_count <= MAX_RETAINED_CANDIDATE_DETAILS
        if self.candidate_details_complete != complete:
            raise _error("candidate completeness is inconsistent")
        if complete and len(self.candidate_results) != self.target_candidate_count:
            raise _error("candidate cardinality is inconsistent")
        if not complete and self.candidate_results:
            raise _error("incomplete candidate details must be empty")
        if self.race_table_scope_count != 1 and self.target_candidate_count != 0:
            raise _error("candidate discovery requires unique scope")

    def to_canonical_dict(self) -> dict[str, object]:
        self.__post_init__()
        target = _target(self.target)
        return {"schema": CANDIDATE_ANCESTRY_RECOVERY_SCHEMA, "schema_version": SCHEMA_VERSION,
                "target": {"baba_code": target.baba_code, "race_date": target.race_date.isoformat(), "race_no": target.race_no},
                "race_table_scope_count": self.race_table_scope_count, "target_candidate_count": self.target_candidate_count,
                "candidate_details_complete": self.candidate_details_complete,
                "candidate_results": [result.to_canonical_dict() for result in self.candidate_results]}

    def canonical_bytes(self) -> bytes:
        return _canonical_bytes(self.to_canonical_dict())


def _has_change_info_class(table: Tag) -> bool:
    value = table.get("class")
    if value is None:
        return False
    if type(value) is str:
        values = value.split()
    elif isinstance(value, (list, tuple)):
        values = value
    else:
        raise _error("table class representation is invalid")
    if any(type(token) is not str for token in values):
        raise _error("table class representation is invalid")
    return "changeInfo" in values


def _ancestry(row: Tag, scope: Tag, ordinal: int) -> ProfileBCandidateAncestryRecoveryResult:
    tables = []
    parent = row.parent
    while parent is not scope:
        if not isinstance(parent, Tag):
            raise _error("candidate is outside selected scope")
        if parent.name == "table":
            _count(len(tables) + 1)
            tables.append(parent)
        parent = parent.parent
    depth = len(tables)
    inside = any(_has_change_info_class(table) for table in tables)
    role = ("NO_TABLE" if not tables else "CHANGE_INFO_TABLE" if _has_change_info_class(tables[0])
            else "RACE_SCHEDULE_TABLE" if depth == 1 else "OTHER_TABLE")
    return ProfileBCandidateAncestryRecoveryResult(ordinal, role, inside, depth, role == "RACE_SCHEDULE_TABLE" and depth == 1)


def _diagnose_ancestry(race_list_bytes: bytes, target: _raw_capture.NARRaceEntryStatusRaceIdentity) -> ProfileBCandidateAncestryRecoveryDiagnostics:
    canonical_target = _target(target)
    if type(race_list_bytes) is not bytes:
        raise _error("RaceList input must be exact bytes")
    try:
        document = BeautifulSoup(race_list_bytes.decode("utf-8", errors="strict"), "html.parser")
    except (UnicodeDecodeError, ParserRejectedMarkup):
        return ProfileBCandidateAncestryRecoveryDiagnostics(canonical_target, 0, 0, False, ())
    scopes = [node for node in document.select("section.raceTable") if type(node) is Tag]
    _count(len(scopes))
    if len(scopes) != 1:
        return ProfileBCandidateAncestryRecoveryDiagnostics(canonical_target, len(scopes), 0, False, ())
    rows = []
    for row in scopes[0].select("tr.data"):
        if type(row) is not Tag:
            continue
        cells = _direct_cells(row)
        if cells and _normalized_cell(cells[0]) == f"{canonical_target.race_no}R":
            rows.append(row)
            _count(len(rows))
    if len(rows) > MAX_RETAINED_CANDIDATE_DETAILS:
        return ProfileBCandidateAncestryRecoveryDiagnostics(canonical_target, 1, len(rows), False, ())
    return ProfileBCandidateAncestryRecoveryDiagnostics(canonical_target, 1, len(rows), True, tuple(
        _ancestry(row, scopes[0], ordinal) for ordinal, row in enumerate(rows, 1)
    ))


def diagnose_nar_race_entry_status_profile_b_candidate_ancestry_recovery(
    *, race_list_bytes: bytes, target: _raw_capture.NARRaceEntryStatusRaceIdentity,
) -> ProfileBCandidateAncestryRecoveryDiagnostics:
    """Retain bounded ancestry without selecting or qualifying candidates."""
    try:
        return _diagnose_ancestry(race_list_bytes, target)
    except Exception:
        pass
    raise _error("candidate ancestry diagnosis could not be completed") from None
