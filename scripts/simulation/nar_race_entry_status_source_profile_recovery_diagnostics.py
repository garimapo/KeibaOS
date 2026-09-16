"""Pure bounded parser-stage and candidate-structure recovery diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
import json
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup, ParserRejectedMarkup
from bs4.element import Tag

from scripts.simulation import nar_race_entry_status_raw_capture as _raw_capture
from scripts.simulation.nar_race_entry_status_source_profile_diagnostics import (
    _direct_cells,
    _normalized_cell,
)
from scripts.simulation.nar_race_entry_status_source_profile_profile_a import (
    _validate_html_structure,
)


PUBLICATION_SAFETY_RECOVERY_SCHEMA = "nar-race-entry-status-publication-safety-recovery-diagnostics"
PROFILE_B_RECOVERY_SCHEMA = "nar-race-entry-status-profile-b-recovery-diagnostics"
RECOVERY_SCHEMA_VERSION = 1
MAX_RETAINED_CANDIDATE_DETAILS = 8
_MAX_SAFE_COUNT = 10_000
_DEBA_PATH = "/KeibaWeb/TodayRaceInfo/DebaTable"
_ROLES = ("deba_table", "race_list")
_STATES = frozenset({
    ("FAIL", "NOT_REACHED", "NOT_REACHED"),
    ("PASS", "FAIL", "NOT_REACHED"),
    ("PASS", "PASS", "PASS"),
    ("PASS", "PASS", "FAIL"),
})


class NARSourceProfileRecoveryDiagnosticsValidationError(ValueError):
    """Raised for malformed authority or contradictory bounded evidence."""


def _error(message: str) -> NARSourceProfileRecoveryDiagnosticsValidationError:
    return NARSourceProfileRecoveryDiagnosticsValidationError(message)


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
        canonical = _raw_capture.NARRaceEntryStatusRaceIdentity(
            baba_code=value.baba_code, race_date=value.race_date, race_no=value.race_no,
        )
    except (_raw_capture.NARRaceEntryStatusRawCaptureError, AttributeError, TypeError):
        raise _error("target is malformed") from None
    _count(canonical.race_no)
    if len(canonical.baba_code.encode("utf-8")) > 512:
        raise _error("formal provider code exceeds the safe string bound")
    return canonical


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")


@dataclass(frozen=True, slots=True)
class PublicationSafetyRecoveryDocumentResult:
    document_role: str
    utf8_decode: str
    strict_structure: str
    beautifulsoup_parse: str

    def __post_init__(self) -> None:
        values = (self.utf8_decode, self.strict_structure, self.beautifulsoup_parse)
        if type(self.document_role) is not str or self.document_role not in _ROLES:
            raise _error("document role is outside the exact allowlist")
        if any(type(value) is not str for value in values) or values not in _STATES:
            raise _error("parser-stage state is impossible")

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "document_role": self.document_role, "utf8_decode": self.utf8_decode,
            "strict_structure": self.strict_structure, "beautifulsoup_parse": self.beautifulsoup_parse,
        }


@dataclass(frozen=True, slots=True)
class PublicationSafetyRecoveryDiagnostics:
    document_results: tuple[PublicationSafetyRecoveryDocumentResult, ...]

    def __post_init__(self) -> None:
        if type(self.document_results) is not tuple or len(self.document_results) != 2:
            raise _error("document results must be an exact two-result tuple")
        if any(type(result) is not PublicationSafetyRecoveryDocumentResult for result in self.document_results):
            raise _error("document result type is invalid")
        if tuple(result.document_role for result in self.document_results) != _ROLES:
            raise _error("document role order is invalid")
        for result in self.document_results:
            result.__post_init__()

    def to_canonical_dict(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "schema": PUBLICATION_SAFETY_RECOVERY_SCHEMA, "schema_version": RECOVERY_SCHEMA_VERSION,
            "document_results": [result.to_canonical_dict() for result in self.document_results],
        }

    def canonical_bytes(self) -> bytes:
        return _canonical_bytes(self.to_canonical_dict())


def _diagnose_document(role: str, value: bytes) -> PublicationSafetyRecoveryDocumentResult:
    if type(value) is not bytes:
        raise _error("document input must be exact bytes")
    try:
        source = value.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return PublicationSafetyRecoveryDocumentResult(role, "FAIL", "NOT_REACHED", "NOT_REACHED")
    try:
        _validate_html_structure(source)
    except ValueError:
        return PublicationSafetyRecoveryDocumentResult(role, "PASS", "FAIL", "NOT_REACHED")
    try:
        BeautifulSoup(source, "html.parser")
    except ParserRejectedMarkup:
        return PublicationSafetyRecoveryDocumentResult(role, "PASS", "PASS", "FAIL")
    return PublicationSafetyRecoveryDocumentResult(role, "PASS", "PASS", "PASS")


def diagnose_nar_race_entry_status_publication_safety_recovery(
    *, deba_table_bytes: bytes, race_list_bytes: bytes,
) -> PublicationSafetyRecoveryDiagnostics:
    """Explain parser-stage reachability without assessing publication Safety."""
    if type(deba_table_bytes) is not bytes or type(race_list_bytes) is not bytes:
        raise _error("document inputs must be exact bytes")
    try:
        return PublicationSafetyRecoveryDiagnostics((
            _diagnose_document("deba_table", deba_table_bytes),
            _diagnose_document("race_list", race_list_bytes),
        ))
    except NARSourceProfileRecoveryDiagnosticsValidationError:
        raise
    except Exception:
        pass
    raise _error("parser-stage recovery could not be completed") from None


@dataclass(frozen=True, slots=True)
class ProfileBRecoveryCandidateResult:
    candidate_ordinal: int
    direct_cell_count: int
    anchor_count: int
    deba_path_link_count: int
    deba_href_unsupported_count: int
    canonical_target_query_match_count: int
    canonical_query_unsupported_count: int
    canonical_target_query_match: bool

    def __post_init__(self) -> None:
        if type(self.candidate_ordinal) is not int or not 1 <= self.candidate_ordinal <= MAX_RETAINED_CANDIDATE_DETAILS:
            raise _error("candidate ordinal is invalid")
        for value in self.safe_projection()[:-1]:
            _count(value)
        if _bool(self.canonical_target_query_match) != (self.canonical_target_query_match_count >= 1):
            raise _error("canonical-query boolean contradicts match count")

    def safe_projection(self) -> tuple[object, ...]:
        return (
            self.direct_cell_count, self.anchor_count, self.deba_path_link_count,
            self.deba_href_unsupported_count, self.canonical_target_query_match_count,
            self.canonical_query_unsupported_count, self.canonical_target_query_match,
        )

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "candidate_ordinal": self.candidate_ordinal, "direct_cell_count": self.direct_cell_count,
            "anchor_count": self.anchor_count, "deba_path_link_count": self.deba_path_link_count,
            "deba_href_unsupported_count": self.deba_href_unsupported_count,
            "canonical_target_query_match_count": self.canonical_target_query_match_count,
            "canonical_query_unsupported_count": self.canonical_query_unsupported_count,
            "canonical_target_query_match": self.canonical_target_query_match,
        }


@dataclass(frozen=True, slots=True)
class ProfileBRecoveryDiagnostics:
    target: _raw_capture.NARRaceEntryStatusRaceIdentity
    race_table_scope_count: int
    target_candidate_count: int
    candidate_details_complete: bool
    candidate_results: tuple[ProfileBRecoveryCandidateResult, ...]
    all_candidate_safe_projections_equal: bool

    def __post_init__(self) -> None:
        _target(self.target)
        _count(self.race_table_scope_count)
        _count(self.target_candidate_count)
        _bool(self.candidate_details_complete)
        _bool(self.all_candidate_safe_projections_equal)
        if type(self.candidate_results) is not tuple or len(self.candidate_results) > MAX_RETAINED_CANDIDATE_DETAILS:
            raise _error("candidate results must be an exact bounded tuple")
        if any(type(result) is not ProfileBRecoveryCandidateResult for result in self.candidate_results):
            raise _error("candidate result type is invalid")
        for ordinal, result in enumerate(self.candidate_results, start=1):
            result.__post_init__()
            if result.candidate_ordinal != ordinal:
                raise _error("candidate ordinals are not contiguous")
        if self.candidate_details_complete:
            if self.race_table_scope_count != 1 or self.target_candidate_count != len(self.candidate_results):
                raise _error("complete candidate count is inconsistent")
        elif self.candidate_results or self.all_candidate_safe_projections_equal:
            raise _error("incomplete candidate details cannot assert a projection")
        elif self.race_table_scope_count == 1 and self.target_candidate_count <= MAX_RETAINED_CANDIDATE_DETAILS:
            raise _error("bounded reachable candidate details must be complete")
        if self.race_table_scope_count != 1 and self.target_candidate_count != 0:
            raise _error("candidate discovery requires exactly one scope")
        expected_equal = bool(self.candidate_results) and all(
            result.safe_projection() == self.candidate_results[0].safe_projection()
            for result in self.candidate_results
        )
        if self.all_candidate_safe_projections_equal != expected_equal:
            raise _error("safe-projection equality is inconsistent")

    def to_canonical_dict(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "schema": PROFILE_B_RECOVERY_SCHEMA, "schema_version": RECOVERY_SCHEMA_VERSION,
            "target": {"baba_code": self.target.baba_code, "race_date": self.target.race_date.isoformat(), "race_no": self.target.race_no},
            "race_table_scope_count": self.race_table_scope_count,
            "target_candidate_count": self.target_candidate_count,
            "candidate_details_complete": self.candidate_details_complete,
            "candidate_results": [result.to_canonical_dict() for result in self.candidate_results],
            "all_candidate_safe_projections_equal": self.all_candidate_safe_projections_equal,
        }

    def canonical_bytes(self) -> bytes:
        return _canonical_bytes(self.to_canonical_dict())


def _candidate_result(row: Tag, ordinal: int, expected: dict[str, list[str]]) -> ProfileBRecoveryCandidateResult:
    anchors = [node for node in row.find_all("a", recursive=True) if type(node) is Tag]
    path_count = href_unsupported = query_matches = query_unsupported = 0
    for anchor in anchors:
        if not anchor.has_attr("href"):
            continue
        href = anchor.get("href")
        if type(href) is not str:
            href_unsupported += 1
            continue
        try:
            parsed = urlparse(href)
        except (TypeError, ValueError):
            href_unsupported += 1
            continue
        if parsed.path != _DEBA_PATH:
            continue
        path_count += 1
        try:
            query = parse_qs(parsed.query, keep_blank_values=True, strict_parsing=True)
        except (TypeError, ValueError):
            query_unsupported += 1
        else:
            query_matches += int(query == expected)
    return ProfileBRecoveryCandidateResult(
        ordinal, len(_direct_cells(row)), len(anchors), path_count, href_unsupported,
        query_matches, query_unsupported, query_matches >= 1,
    )


def _diagnose_profile_b_recovery(
    *, race_list_bytes: bytes, target: _raw_capture.NARRaceEntryStatusRaceIdentity,
) -> ProfileBRecoveryDiagnostics:
    """Retain safe candidate structure without selecting or qualifying a row."""
    canonical_target = _target(target)
    if type(race_list_bytes) is not bytes:
        raise _error("RaceList input must be exact bytes")
    try:
        source = race_list_bytes.decode("utf-8", errors="strict")
        document = BeautifulSoup(source, "html.parser")
    except (UnicodeDecodeError, ParserRejectedMarkup):
        # Frozen unavailable-discovery representation, not a claim of zero rows.
        return ProfileBRecoveryDiagnostics(canonical_target, 0, 0, False, (), False)
    scopes = [node for node in document.select("section.raceTable") if type(node) is Tag]
    _count(len(scopes))
    if len(scopes) != 1:
        return ProfileBRecoveryDiagnostics(canonical_target, len(scopes), 0, False, (), False)
    rows = []
    for row in scopes[0].select("tr.data"):
        if type(row) is not Tag:
            continue
        cells = _direct_cells(row)
        if cells and _normalized_cell(cells[0]) == f"{canonical_target.race_no}R":
            rows.append(row)
    _count(len(rows))
    if len(rows) > MAX_RETAINED_CANDIDATE_DETAILS:
        return ProfileBRecoveryDiagnostics(canonical_target, 1, len(rows), False, (), False)
    expected = {
        "k_babaCode": [canonical_target.baba_code],
        "k_raceDate": [canonical_target.race_date.strftime("%Y/%m/%d")],
        "k_raceNo": [str(canonical_target.race_no)],
    }
    results = tuple(_candidate_result(row, ordinal, expected) for ordinal, row in enumerate(rows, start=1))
    equal = bool(results) and all(result.safe_projection() == results[0].safe_projection() for result in results)
    return ProfileBRecoveryDiagnostics(canonical_target, 1, len(rows), True, results, equal)


def diagnose_nar_race_entry_status_profile_b_recovery(
    *, race_list_bytes: bytes, target: _raw_capture.NARRaceEntryStatusRaceIdentity,
) -> ProfileBRecoveryDiagnostics:
    """Produce bounded candidate evidence or a fixed diagnostic error."""
    try:
        return _diagnose_profile_b_recovery(race_list_bytes=race_list_bytes, target=target)
    except NARSourceProfileRecoveryDiagnosticsValidationError:
        raise
    except Exception:
        pass
    raise _error("candidate recovery could not be completed") from None
