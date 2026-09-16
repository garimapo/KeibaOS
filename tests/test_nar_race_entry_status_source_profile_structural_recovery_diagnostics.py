from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, replace
from datetime import date
import inspect
import json

from bs4 import BeautifulSoup, ParserRejectedMarkup
import pytest

from scripts.simulation import nar_race_entry_status_raw_capture as raw
from scripts.simulation import nar_race_entry_status_source_profile_diagnostics as ordinary
from scripts.simulation import nar_race_entry_status_source_profile_profile_a as profile_a
from scripts.simulation import nar_race_entry_status_source_profile_recovery_diagnostics as phase63
from scripts.simulation import nar_race_entry_status_source_profile_structural_recovery_diagnostics as subject


TARGET = raw.NARRaceEntryStatusRaceIdentity("21", date(2025, 1, 1), 6)
ERROR = subject.NARStructuralRecoveryDiagnosticsValidationError
TAG = subject.StructuralTag
ROW = '<tr class="data"><td>6<span>R</span></td><td>PRIVATE_TEXT</td></tr>'


def strict(source: bytes = b"<div></div>") -> subject.StrictStructureRecoveryDiagnostics:
    return subject.diagnose_nar_race_entry_status_strict_structure_recovery(deba_table_bytes=source, race_list_bytes=source)


def ancestry(rows: str = ROW, *, wrapper: str = "<table>{}</table>") -> subject.ProfileBCandidateAncestryRecoveryDiagnostics:
    source = ('<section class="raceTable">' + wrapper.format(rows) + '</section>').encode()
    return subject.diagnose_nar_race_entry_status_profile_b_candidate_ancestry_recovery(race_list_bytes=source, target=TARGET)


@pytest.mark.parametrize("source,kind,index,depth,expected,observed", [
    (b"", "PASS", 0, 0, None, None),
    (b"<html><body><div></div></body></html>", "PASS", 6, 0, None, None),
    (b"</div>", "END_TAG_EMPTY_STACK", 1, 0, None, TAG.DIV),
    (b"<div><p></div>", "END_TAG_MISMATCH", 3, 2, TAG.P, TAG.DIV),
    (b"<div><p>", "UNCLOSED_STACK_AT_CLOSE", 2, 2, TAG.P, None),
    (b"<div><img><br></br></div>", "PASS", 5, 0, None, None),
    (b"<custom/>", "PASS", 1, 0, None, None),
    (b"<!--PRIVATE--><div>text &amp; &#65;</div>", "PASS", 2, 0, None, None),
    (b"<private-one></private-two>", "END_TAG_MISMATCH", 2, 1, TAG.OTHER_OR_CUSTOM, TAG.OTHER_OR_CUSTOM),
    (b"<!DOCTYPE html><DIV></DIV>", "PASS", 2, 0, None, None),
])
def test_strict_branch_indices_depths_and_profile_a_parity(source, kind, index, depth, expected, observed) -> None:
    result = strict(source).document_results[0]
    assert (result.failure_kind, result.event_index, result.stack_depth, result.expected_open_tag, result.observed_end_tag) == (kind, index, depth, expected, observed)
    try:
        profile_a._validate_html_structure(source.decode("utf-8"))
        authoritative_pass = True
    except ValueError:
        authoritative_pass = False
    assert (kind == "PASS") is authoritative_pass
    assert subject._VOID_TAGS is profile_a._VOID_TAGS


@pytest.mark.parametrize("token", [tag for tag in TAG if tag is not TAG.OTHER_OR_CUSTOM])
def test_every_fixed_tag_mapping(token: TAG) -> None:
    result = strict(("<" + token.value.lower() + ">").encode()).document_results[0]
    assert result.expected_open_tag is token


@pytest.mark.parametrize("kind,index,depth,expected,observed", [
    ("PASS", 0, 0, None, None),
    ("END_TAG_EMPTY_STACK", 1, 0, None, TAG.DIV),
    ("END_TAG_MISMATCH", 1, 1, TAG.OTHER_OR_CUSTOM, TAG.OTHER_OR_CUSTOM),
    ("UNCLOSED_STACK_AT_CLOSE", 0, 1, TAG.DIV, None),
])
def test_legal_typed_states_and_immutability(kind, index, depth, expected, observed) -> None:
    result = subject.StrictStructureRecoveryDocumentResult("deba_table", kind, index, depth, expected, observed, "PASS")
    with pytest.raises(FrozenInstanceError):
        result.stack_depth = 10


@pytest.mark.parametrize("changes", [
    {"failure_kind": "FAIL"}, {"document_role": "other"}, {"event_index": True},
    {"event_index": -1}, {"event_index": 10001}, {"stack_depth": True},
    {"stack_depth": -1}, {"stack_depth": 10001}, {"expected_open_tag": "PRIVATE_TAG"},
    {"observed_end_tag": "DIV"}, {"tolerant_parse": "NOT_RUN"},
    {"stack_depth": 1}, {"expected_open_tag": TAG.DIV},
    {"failure_kind": "END_TAG_EMPTY_STACK", "observed_end_tag": TAG.DIV},
    {"failure_kind": "END_TAG_MISMATCH", "event_index": 1, "expected_open_tag": TAG.DIV, "observed_end_tag": TAG.P},
    {"failure_kind": "UNCLOSED_STACK_AT_CLOSE", "expected_open_tag": TAG.DIV},
])
def test_strict_contradictory_objects_rejected(changes) -> None:
    with pytest.raises(ERROR):
        replace(strict(b"").document_results[0], **changes)


def test_order_cardinality_canonical_form_and_no_content() -> None:
    result = strict(b'<private-element secret="PRIVATE_ATTR">PRIVATE_BODY</other-private>')
    payload = result.to_canonical_dict()
    assert set(payload) == {"schema", "schema_version", "document_results"}
    assert payload["schema"] == subject.STRICT_STRUCTURE_RECOVERY_SCHEMA
    assert payload["schema_version"] == 1
    assert [r["document_role"] for r in payload["document_results"]] == ["deba_table", "race_list"]
    assert set(payload["document_results"][0]) == {"document_role", "failure_kind", "event_index", "stack_depth", "expected_open_tag", "observed_end_tag", "tolerant_parse"}
    assert result.canonical_bytes() == json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    assert b"PRIVATE" not in result.canonical_bytes() and b"private-element" not in result.canonical_bytes()
    with pytest.raises(ERROR):
        replace(result, document_results=result.document_results[::-1])
    with pytest.raises(ERROR):
        replace(result, document_results=result.document_results[:1])


@pytest.mark.parametrize("which", ["deba_table_bytes", "race_list_bytes"])
@pytest.mark.parametrize("bad", [b"\xff", bytearray(b"<div></div>"), "PRIVATE_SOURCE", None])
def test_strict_input_and_utf8_failure_bounded(which, bad) -> None:
    args = {"deba_table_bytes": b"", "race_list_bytes": b""}
    args[which] = bad
    with pytest.raises(ERROR) as caught:
        subject.diagnose_nar_race_entry_status_strict_structure_recovery(**args)
    assert "PRIVATE" not in str(caught.value)
    assert caught.value.__context__ is None


@pytest.mark.parametrize("source", [b"<div></div>", b"<div></span>"])
def test_tolerant_rejection_after_strict_classification(monkeypatch, source) -> None:
    def reject(*args, **kwargs):
        raise ParserRejectedMarkup("PRIVATE_MARKUP")
    monkeypatch.setattr(subject, "BeautifulSoup", reject)
    assert all(r.tolerant_parse == "FAIL" for r in strict(source).document_results)
    assert b"PRIVATE_MARKUP" not in strict(source).canonical_bytes()


@pytest.mark.parametrize("stage", ["feed", "close", "tolerant"])
def test_unexpected_parser_failure_is_bounded_operation_error(monkeypatch, stage) -> None:
    def fail(*args, **kwargs):
        raise RuntimeError("PRIVATE_EXCEPTION")
    if stage == "tolerant":
        monkeypatch.setattr(subject, "BeautifulSoup", fail)
    else:
        monkeypatch.setattr(subject._DiagnosticStrictStructureParser, stage, fail)
    with pytest.raises(ERROR) as caught:
        strict()
    assert "PRIVATE" not in str(caught.value) and caught.value.__context__ is None


def test_event_bound_fails_without_clamping() -> None:
    with pytest.raises(ERROR):
        strict(b"<br>" * 10001)
    assert strict(b"<br>" * 10000).document_results[0].event_index == 10000


@pytest.mark.parametrize("count", [0, 1, 2, 8, 9])
def test_count_order_no_deduplication_and_phase53_63_parity(count) -> None:
    result = ancestry(ROW * count)
    assert result.target_candidate_count == count
    assert result.candidate_details_complete is (count <= 8)
    assert len(result.candidate_results) == (count if count <= 8 else 0)
    assert [r.candidate_ordinal for r in result.candidate_results] == list(range(1, min(count, 8) + 1)) if count <= 8 else not result.candidate_results
    source = ('<section class="raceTable"><table>' + ROW * count + '</table></section>').encode()
    normal = ordinary.diagnose_nar_race_entry_status_profile_b(race_list_bytes=source, target=TARGET).to_canonical_dict()
    old = phase63.diagnose_nar_race_entry_status_profile_b_recovery(race_list_bytes=source, target=TARGET)
    assert normal["predicate_results"][1]["safe_fields"]["target_6r_row_count"] == count == old.target_candidate_count
    assert result.candidate_details_complete == old.candidate_details_complete
    assert [r.candidate_ordinal for r in result.candidate_results] == [r.candidate_ordinal for r in old.candidate_results]
    assert subject._direct_cells is ordinary._direct_cells and subject._normalized_cell is ordinary._normalized_cell
    assert subject.MAX_RETAINED_CANDIDATE_DETAILS == phase63.MAX_RETAINED_CANDIDATE_DETAILS


@pytest.mark.parametrize("wrapper,role,depth,inside,direct", [
    ("<table>{}</table>", "RACE_SCHEDULE_TABLE", 1, False, True),
    ('<table class="changeInfo">{}</table>', "CHANGE_INFO_TABLE", 1, True, False),
    ('<table class="changeInfo"><tr><td><table>{}</table></td></tr></table>', "OTHER_TABLE", 2, True, False),
    ('<table><tr><td><table>{}</table></td></tr></table>', "OTHER_TABLE", 2, False, False),
    ("{}", "NO_TABLE", 0, False, False),
    ('<table class="changeInformation">{}</table>', "RACE_SCHEDULE_TABLE", 1, False, True),
    ('<table class="CHANGEINFO">{}</table>', "RACE_SCHEDULE_TABLE", 1, False, True),
    ('<table class="other changeInfo extra">{}</table>', "CHANGE_INFO_TABLE", 1, True, False),
])
def test_fixed_class_tokens_table_depths_and_roles(wrapper, role, depth, inside, direct) -> None:
    r = ancestry(wrapper=wrapper).candidate_results[0]
    assert (r.nearest_table_role, r.nested_table_depth_within_race_scope, r.inside_change_info_table, r.direct_schedule_table_descendant) == (role, depth, inside, direct)


def test_ancestry_walk_stops_at_selected_section() -> None:
    source = ('<table class="changeInfo"><tr><td><section class="raceTable"><table>' + ROW + '</table></section></td></tr></table>').encode()
    r = subject.diagnose_nar_race_entry_status_profile_b_candidate_ancestry_recovery(race_list_bytes=source, target=TARGET).candidate_results[0]
    assert r.nested_table_depth_within_race_scope == 1 and not r.inside_change_info_table


@pytest.mark.parametrize("changes", [
    {"candidate_ordinal": 0}, {"candidate_ordinal": True}, {"candidate_ordinal": 9},
    {"nearest_table_role": "PRIVATE_CLASS"}, {"inside_change_info_table": 1},
    {"direct_schedule_table_descendant": 1}, {"nested_table_depth_within_race_scope": True},
    {"nested_table_depth_within_race_scope": -1}, {"nested_table_depth_within_race_scope": 10001},
    {"nearest_table_role": "NO_TABLE"}, {"nearest_table_role": "CHANGE_INFO_TABLE"},
    {"nearest_table_role": "OTHER_TABLE"}, {"inside_change_info_table": True},
    {"direct_schedule_table_descendant": False},
])
def test_ancestry_candidate_contradictions(changes) -> None:
    with pytest.raises(ERROR):
        replace(ancestry().candidate_results[0], **changes)


@pytest.mark.parametrize("changes", [
    {"target_candidate_count": 2}, {"candidate_details_complete": False},
    {"race_table_scope_count": True}, {"target_candidate_count": 10001},
    {"target": {}}, {"candidate_results": []}, {"race_table_scope_count": 0},
])
def test_ancestry_top_level_contradictions(changes) -> None:
    with pytest.raises(ERROR):
        replace(ancestry(), **changes)


@pytest.mark.parametrize("source", [b"\xff", b"", b'<section class="raceTable"></section>' * 2])
def test_unavailable_discovery(source) -> None:
    result = subject.diagnose_nar_race_entry_status_profile_b_candidate_ancestry_recovery(race_list_bytes=source, target=TARGET)
    assert result.target_candidate_count == 0 and not result.candidate_details_complete and not result.candidate_results


def test_canonical_safe_ancestry_boundary_and_no_selection() -> None:
    source = ('<section class="raceTable"><table class="PRIVATE_CLASS">' + ROW + '<tr class="data"><td>16R</td></tr></table></section>' + ROW).encode()
    result = subject.diagnose_nar_race_entry_status_profile_b_candidate_ancestry_recovery(race_list_bytes=source, target=TARGET)
    assert result.target_candidate_count == 1
    payload = result.to_canonical_dict()
    assert set(payload) == {"schema", "schema_version", "target", "race_table_scope_count", "target_candidate_count", "candidate_details_complete", "candidate_results"}
    assert set(payload["candidate_results"][0]) == {"candidate_ordinal", "nearest_table_role", "inside_change_info_table", "nested_table_depth_within_race_scope", "direct_schedule_table_descendant"}
    assert result.canonical_bytes() == json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()
    for marker in (b"PRIVATE", b"selected", b"preferred", b"qualification", b"href", b"<tr"):
        assert marker not in result.canonical_bytes()


def test_ancestry_parser_rejection_and_unexpected_failure(monkeypatch) -> None:
    def rejected(*args, **kwargs):
        raise ParserRejectedMarkup("PRIVATE")
    monkeypatch.setattr(subject, "BeautifulSoup", rejected)
    assert not ancestry().candidate_details_complete
    def unexpected(*args, **kwargs):
        raise RuntimeError("PRIVATE")
    monkeypatch.setattr(subject, "BeautifulSoup", unexpected)
    with pytest.raises(ERROR) as caught:
        ancestry()
    assert "PRIVATE" not in str(caught.value) and caught.value.__context__ is None


def test_static_no_side_effect_authority() -> None:
    tree = ast.parse(inspect.getsource(subject))
    imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    imports += [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names]
    forbidden = {"requests", "socket", "subprocess", "pathlib", "os", "sqlite3", "time", "datetime", "random", "urllib.request"}
    assert not any(name in forbidden or any(name.startswith(prefix + ".") for prefix in forbidden) for name in imports)
    calls = {node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
    assert not calls.intersection({"open", "exec", "eval", "__import__"})
