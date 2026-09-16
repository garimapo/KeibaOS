from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, replace
from datetime import date
import inspect
import itertools
import json

from bs4 import BeautifulSoup, ParserRejectedMarkup
import pytest

from scripts.simulation import nar_race_entry_status_raw_capture as raw_capture
from scripts.simulation import nar_race_entry_status_source_profile_diagnostics as ordinary
from scripts.simulation import nar_race_entry_status_source_profile_profile_a as profile_a
from scripts.simulation import nar_race_entry_status_source_profile_recovery_diagnostics as subject


TARGET = raw_capture.NARRaceEntryStatusRaceIdentity("21", date(2025, 1, 1), 6)
VALID = b"<html><body><p>synthetic</p></body></html>"
PATH = "/KeibaWeb/TodayRaceInfo/DebaTable"
QUERY = "?k_babaCode=21&k_raceDate=2025/01/01&k_raceNo=6"


def _row(cells: int = 2, href: str = PATH + QUERY, extra: str = "") -> str:
    return '<tr class="data"><td> 6<span>R</span> </td><td><a href="' + href + '">PRIVATE_MARKER</a>' + extra + "</td>" + "<td></td>" * (cells - 2) + "</tr>"


def _source(rows: str) -> bytes:
    return ('<section class="raceTable"><table>' + rows + "</table></section>").encode("utf-8")


def _diagnose(rows: str) -> subject.ProfileBRecoveryDiagnostics:
    return subject.diagnose_nar_race_entry_status_profile_b_recovery(race_list_bytes=_source(rows), target=TARGET)


def _candidate(ordinal: int = 1) -> subject.ProfileBRecoveryCandidateResult:
    return subject.ProfileBRecoveryCandidateResult(ordinal, 2, 1, 1, 0, 1, 0, True)


def test_valid_safety_stages_and_exact_canonical_shape() -> None:
    result = subject.diagnose_nar_race_entry_status_publication_safety_recovery(deba_table_bytes=VALID, race_list_bytes=VALID)
    payload = result.to_canonical_dict()
    assert set(payload) == {"schema", "schema_version", "document_results"}
    assert payload["schema"] == "nar-race-entry-status-publication-safety-recovery-diagnostics"
    assert payload["schema_version"] == 1
    assert [(r.document_role, r.utf8_decode, r.strict_structure, r.beautifulsoup_parse) for r in result.document_results] == [
        ("deba_table", "PASS", "PASS", "PASS"), ("race_list", "PASS", "PASS", "PASS"),
    ]
    assert subject._validate_html_structure is profile_a._validate_html_structure
    assert result.canonical_bytes() == json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    assert result.canonical_bytes() == result.canonical_bytes()


@pytest.mark.parametrize("role", ["deba_table", "race_list"])
@pytest.mark.parametrize("source,state", [
    (b"\xff", ("FAIL", "NOT_REACHED", "NOT_REACHED")),
    (b"<div><p></div>", ("PASS", "FAIL", "NOT_REACHED")),
    (b"<div>", ("PASS", "FAIL", "NOT_REACHED")),
])
def test_role_specific_safety_stage_failure(role: str, source: bytes, state: tuple[str, str, str]) -> None:
    inputs = {"deba_table_bytes": VALID, "race_list_bytes": VALID}
    inputs[role + "_bytes"] = source
    result = subject.diagnose_nar_race_entry_status_publication_safety_recovery(**inputs)
    selected = next(r for r in result.document_results if r.document_role == role)
    assert (selected.utf8_decode, selected.strict_structure, selected.beautifulsoup_parse) == state
    assert b"<div>" not in result.canonical_bytes()


@pytest.mark.parametrize("role", ["deba_table", "race_list"])
def test_parser_rejection_stage_is_bounded(monkeypatch: pytest.MonkeyPatch, role: str) -> None:
    def reject(source: str, parser: str) -> object:
        if "REJECT_MARKER" in source:
            raise ParserRejectedMarkup("PRIVATE_EXCEPTION_MARKER")
        return BeautifulSoup(source, parser)
    monkeypatch.setattr(subject, "BeautifulSoup", reject)
    inputs = {"deba_table_bytes": VALID, "race_list_bytes": VALID}
    inputs[role + "_bytes"] = b"<p>REJECT_MARKER</p>"
    result = subject.diagnose_nar_race_entry_status_publication_safety_recovery(**inputs)
    selected = next(r for r in result.document_results if r.document_role == role)
    assert (selected.utf8_decode, selected.strict_structure, selected.beautifulsoup_parse) == ("PASS", "PASS", "FAIL")
    assert b"PRIVATE_EXCEPTION_MARKER" not in result.canonical_bytes()
    assert b"REJECT_MARKER" not in result.canonical_bytes()


@pytest.mark.parametrize("state", list(itertools.product(("PASS", "FAIL", "NOT_REACHED"), repeat=3)))
def test_exact_safety_state_machine(state: tuple[str, str, str]) -> None:
    valid = {("FAIL", "NOT_REACHED", "NOT_REACHED"), ("PASS", "FAIL", "NOT_REACHED"), ("PASS", "PASS", "PASS"), ("PASS", "PASS", "FAIL")}
    if state in valid:
        subject.PublicationSafetyRecoveryDocumentResult("deba_table", *state)
    else:
        with pytest.raises(subject.NARSourceProfileRecoveryDiagnosticsValidationError):
            subject.PublicationSafetyRecoveryDocumentResult("deba_table", *state)


@pytest.mark.parametrize("role", ["other", "deba_table\n", 1])
def test_wrong_safety_role_rejected(role: object) -> None:
    with pytest.raises(subject.NARSourceProfileRecoveryDiagnosticsValidationError):
        subject.PublicationSafetyRecoveryDocumentResult(role, "PASS", "PASS", "PASS")


def test_wrong_safety_role_order_and_mutability_rejected() -> None:
    a = subject.PublicationSafetyRecoveryDocumentResult("deba_table", "PASS", "PASS", "PASS")
    b = subject.PublicationSafetyRecoveryDocumentResult("race_list", "PASS", "PASS", "PASS")
    with pytest.raises(subject.NARSourceProfileRecoveryDiagnosticsValidationError):
        subject.PublicationSafetyRecoveryDiagnostics((b, a))
    with pytest.raises(FrozenInstanceError):
        a.utf8_decode = "FAIL"


@pytest.mark.parametrize("count,equal", [(0, False), (1, True), (2, True), (8, True), (9, False)])
def test_candidate_count_overflow_and_equality(count: int, equal: bool) -> None:
    result = _diagnose(_row() * count)
    assert result.target_candidate_count == count
    assert result.candidate_details_complete is (count <= 8)
    assert len(result.candidate_results) == (count if count <= 8 else 0)
    assert result.all_candidate_safe_projections_equal is equal
    assert [r.candidate_ordinal for r in result.candidate_results] == (list(range(1, count + 1)) if count <= 8 else [])


def test_candidate_boundary_and_dom_order_are_exact() -> None:
    rows = _row(2) + '<tr class="data"><td>16R</td></tr>' + _row(4)
    source = _source(rows) + b'<table><tr class="data"><td>6R</td></tr></table>'
    result = subject.diagnose_nar_race_entry_status_profile_b_recovery(race_list_bytes=source, target=TARGET)
    assert result.race_table_scope_count == 1
    assert result.target_candidate_count == 2
    assert [r.direct_cell_count for r in result.candidate_results] == [2, 4]
    assert not result.all_candidate_safe_projections_equal
    assert subject._direct_cells is ordinary._direct_cells
    assert subject._normalized_cell is ordinary._normalized_cell


def test_exact_candidate_fields_counts_and_no_provider_text() -> None:
    result = _diagnose(_row(extra='<a>UNRETAINED</a><a href="/unrelated?bad">OTHER</a>'))
    candidate = result.candidate_results[0]
    assert candidate == subject.ProfileBRecoveryCandidateResult(1, 2, 3, 1, 0, 1, 0, True)
    assert set(candidate.to_canonical_dict()) == {
        "candidate_ordinal", "direct_cell_count", "anchor_count", "deba_path_link_count",
        "deba_href_unsupported_count", "canonical_target_query_match_count",
        "canonical_query_unsupported_count", "canonical_target_query_match",
    }
    payload = result.to_canonical_dict()
    assert set(payload) == {"schema", "schema_version", "target", "race_table_scope_count", "target_candidate_count", "candidate_details_complete", "candidate_results", "all_candidate_safe_projections_equal"}
    assert payload["schema"] == "nar-race-entry-status-profile-b-recovery-diagnostics"
    assert payload["target"] == {"baba_code": "21", "race_date": "2025-01-01", "race_no": 6}
    for marker in (b"PRIVATE_MARKER", b"UNRETAINED", b"/unrelated", PATH.encode(), b"k_babaCode"):
        assert marker not in result.canonical_bytes()
    assert result.canonical_bytes() == _diagnose(_row(extra='<a>UNRETAINED</a><a href="/unrelated?bad">OTHER</a>')).canonical_bytes()


@pytest.mark.parametrize("href,path_count,unsupported,matches,query_unsupported", [
    (PATH + QUERY, 1, 0, 1, 0),
    (PATH + QUERY.replace("raceNo=6", "raceNo=7"), 1, 0, 0, 0),
    (PATH + "?bad", 1, 0, 0, 1),
    ("/unrelated?bad", 0, 0, 0, 0),
    ("http://[malformed", 0, 1, 0, 0),
    (PATH + QUERY + "&extra=value", 1, 0, 0, 0),
])
def test_href_and_strict_query_unsupported_counters(href: str, path_count: int, unsupported: int, matches: int, query_unsupported: int) -> None:
    candidate = _diagnose(_row(href=href)).candidate_results[0]
    assert (candidate.deba_path_link_count, candidate.deba_href_unsupported_count, candidate.canonical_target_query_match_count, candidate.canonical_query_unsupported_count) == (path_count, unsupported, matches, query_unsupported)
    assert candidate.canonical_target_query_match is (matches >= 1)


def test_multiple_canonical_matches_boolean_means_at_least_one() -> None:
    candidate = _diagnose(_row(extra='<a href="' + PATH + QUERY + '">x</a>')).candidate_results[0]
    assert candidate.canonical_target_query_match_count == 2
    assert candidate.canonical_target_query_match


def test_non_string_href_is_counted_without_retention(monkeypatch: pytest.MonkeyPatch) -> None:
    def parse(source: str, parser: str) -> object:
        soup = BeautifulSoup(source, parser)
        soup.find("a")["href"] = ["PRIVATE_VALUE"]
        return soup
    monkeypatch.setattr(subject, "BeautifulSoup", parse)
    result = _diagnose(_row())
    assert result.candidate_results[0].deba_href_unsupported_count == 1
    assert result.candidate_results[0].deba_path_link_count == 0
    assert b"PRIVATE_VALUE" not in result.canonical_bytes()


@pytest.mark.parametrize("source", [b"\xff", b"<section></section>", b'<section class="raceTable"></section>' * 2])
def test_frozen_unavailable_discovery_representation(source: bytes) -> None:
    result = subject.diagnose_nar_race_entry_status_profile_b_recovery(race_list_bytes=source, target=TARGET)
    assert not result.candidate_details_complete
    assert result.target_candidate_count == 0
    assert not result.candidate_results
    assert not result.all_candidate_safe_projections_equal


@pytest.mark.parametrize("changes", [
    {"target_candidate_count": 2}, {"candidate_details_complete": False},
    {"all_candidate_safe_projections_equal": False},
    {"candidate_results": (_candidate(2),)}, {"candidate_results": [_candidate()]},
    {"target_candidate_count": 10001}, {"race_table_scope_count": True},
])
def test_invalid_typed_candidate_result_rejected(changes: dict[str, object]) -> None:
    result = _diagnose(_row())
    with pytest.raises(subject.NARSourceProfileRecoveryDiagnosticsValidationError):
        replace(result, **changes)


@pytest.mark.parametrize("changes", [
    {"canonical_target_query_match": False}, {"anchor_count": -1},
    {"direct_cell_count": 10001}, {"anchor_count": True}, {"anchor_count": "private"},
])
def test_invalid_candidate_counts_and_boolean_rejected(changes: dict[str, object]) -> None:
    with pytest.raises(subject.NARSourceProfileRecoveryDiagnosticsValidationError):
        replace(_candidate(), **changes)


@pytest.mark.parametrize("value", ["<html>", bytearray(VALID), None])
def test_exact_bytes_required(value: object) -> None:
    with pytest.raises(subject.NARSourceProfileRecoveryDiagnosticsValidationError):
        subject.diagnose_nar_race_entry_status_publication_safety_recovery(deba_table_bytes=value, race_list_bytes=VALID)
    with pytest.raises(subject.NARSourceProfileRecoveryDiagnosticsValidationError):
        subject.diagnose_nar_race_entry_status_profile_b_recovery(race_list_bytes=value, target=TARGET)


def test_invalid_target_and_ordinary_profile_b_invariance() -> None:
    with pytest.raises(subject.NARSourceProfileRecoveryDiagnosticsValidationError):
        subject.diagnose_nar_race_entry_status_profile_b_recovery(race_list_bytes=VALID, target={})
    source = _source(_row() * 2)
    before = ordinary.diagnose_nar_race_entry_status_profile_b(race_list_bytes=source, target=TARGET).canonical_bytes()
    result = subject.diagnose_nar_race_entry_status_profile_b_recovery(race_list_bytes=source, target=TARGET)
    after = ordinary.diagnose_nar_race_entry_status_profile_b(race_list_bytes=source, target=TARGET).canonical_bytes()
    assert before == after
    assert result.target_candidate_count == 2
    assert json.loads(before)["overall_result"] == "BLOCKED"


@pytest.mark.parametrize("target", [
    raw_capture.NARRaceEntryStatusRaceIdentity("21", date(2025, 1, 1), 10001),
    raw_capture.NARRaceEntryStatusRaceIdentity("9" * 513, date(2025, 1, 1), 6),
])
def test_formal_target_safe_output_bounds(target: raw_capture.NARRaceEntryStatusRaceIdentity) -> None:
    with pytest.raises(subject.NARSourceProfileRecoveryDiagnosticsValidationError):
        subject.diagnose_nar_race_entry_status_profile_b_recovery(race_list_bytes=VALID, target=target)


@pytest.mark.parametrize("stage", ["strict_structure", "beautifulsoup"])
def test_unexpected_safety_exception_is_a_bounded_diagnostic_error(monkeypatch: pytest.MonkeyPatch, stage: str) -> None:
    def fail(*args: object) -> object:
        raise RuntimeError("PRIVATE_EXCEPTION_MARKER")
    monkeypatch.setattr(subject, "_validate_html_structure" if stage == "strict_structure" else "BeautifulSoup", fail)
    with pytest.raises(subject.NARSourceProfileRecoveryDiagnosticsValidationError) as caught:
        subject.diagnose_nar_race_entry_status_publication_safety_recovery(deba_table_bytes=VALID, race_list_bytes=VALID)
    assert "PRIVATE_EXCEPTION_MARKER" not in str(caught.value)
    assert caught.value.__suppress_context__
    assert caught.value.__context__ is None


def test_unexpected_candidate_exception_is_a_bounded_diagnostic_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*args: object) -> object:
        raise RuntimeError("PRIVATE_EXCEPTION_MARKER")
    monkeypatch.setattr(subject, "_normalized_cell", fail)
    with pytest.raises(subject.NARSourceProfileRecoveryDiagnosticsValidationError) as caught:
        _diagnose(_row())
    assert "PRIVATE_EXCEPTION_MARKER" not in str(caught.value)
    assert caught.value.__suppress_context__
    assert caught.value.__context__ is None


def test_pure_recovery_source_static_audit() -> None:
    tree = ast.parse(inspect.getsource(subject))
    forbidden = {"requests", "socket", "subprocess", "pathlib", "sqlite3", "time", "random", "os"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(alias.name.split(".")[0] not in forbidden for alias in node.names)
        if isinstance(node, ast.ImportFrom):
            assert node.module != "urllib.request"
            assert (node.module or "").split(".")[0] not in forbidden
        if isinstance(node, ast.Call):
            assert not (isinstance(node.func, ast.Name) and node.func.id in {"open", "eval", "exec"})
            assert not (isinstance(node.func, ast.Attribute) and node.func.attr in {"now", "utcnow", "urlopen", "getenv", "acquire_nar_race_entry_status_raw_bundle"})
