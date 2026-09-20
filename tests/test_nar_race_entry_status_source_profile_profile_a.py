from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError
from datetime import date
import json
from pathlib import Path

import pytest

from scripts.simulation import nar_race_entry_status_raw_capture as raw_capture
from scripts.simulation import nar_race_entry_status_source_profile_profile_a as subject


TARGET = raw_capture.NARRaceEntryStatusRaceIdentity("21", date(2025, 1, 1), 6)
PREDICATES = (
    "ENTRY_TABLE_SCOPE",
    "ORDINARY_HORSE_ROW_SHAPE",
    "SELECTED_NON14_LISTING",
)


def _row(number: str, *, href: str = "/horse/profile", duplicate_link: bool = False) -> str:
    link = f'<a class="horseName" href="{href}">synthetic horse</a>'
    if duplicate_link:
        link += f'<a class="horseName" href="{href}">duplicate</a>'
    return f'<tr><td class="horseNum">{number}</td><td>{link}</td></tr>'


def _source(*rows: str, duplicate_scope: bool = False) -> bytes:
    table = '<article class="raceCard"><section class="cardTable"><table>' + "".join(rows) + "</table></section></article>"
    return ("<html><body>" + table + (table if duplicate_scope else "") + "</body></html>").encode("utf-8")


def _diagnose(source: bytes) -> subject.ProfileADiagnostics:
    return subject.diagnose_nar_race_entry_status_profile_a(deba_table_bytes=source, target=TARGET)


def _outcomes(result: subject.ProfileADiagnostics) -> tuple[str, ...]:
    return tuple(item.outcome.value for item in result.predicate_results)


def test_valid_listing_qualifies_in_frozen_order_and_selects_lowest_non14() -> None:
    result = _diagnose(_source(_row("14"), _row("7"), _row("3")))

    assert tuple(item.identifier.value for item in result.predicate_results) == PREDICATES
    assert _outcomes(result) == ("PASS", "PASS", "PASS")
    assert result.overall_result == "QUALIFIED"
    assert result.first_nonpass_predicate is None
    assert result.terminal_reason == "QUALIFIED"
    payload = result.to_canonical_dict()
    assert payload["terminal_semantic"] == "ENTRY_LISTING_PRESENT"
    assert payload["predicate_results"][2]["safe_fields"] == {  # type: ignore[index]
        "selected_non14_candidate_count": 2,
        "selected_provider_horse_no": 3,
    }


@pytest.mark.parametrize(
    ("source", "expected_outcomes", "first_nonpass"),
    [
        (b"<html><body></body></html>", ("FAIL", "UNSUPPORTED", "UNSUPPORTED"), "ENTRY_TABLE_SCOPE"),
        (_source(_row("3"), duplicate_scope=True), ("AMBIGUOUS", "UNSUPPORTED", "UNSUPPORTED"), "ENTRY_TABLE_SCOPE"),
        (_source(_row("14")), ("PASS", "PASS", "FAIL"), "SELECTED_NON14_LISTING"),
        (_source(_row("3"), _row("3")), ("PASS", "PASS", "AMBIGUOUS"), "SELECTED_NON14_LISTING"),
        (_source(_row("horse")), ("PASS", "UNSUPPORTED", "UNSUPPORTED"), "ORDINARY_HORSE_ROW_SHAPE"),
        (_source(_row("3", duplicate_link=True)), ("PASS", "AMBIGUOUS", "UNSUPPORTED"), "ORDINARY_HORSE_ROW_SHAPE"),
        (b'<html><body><table><tr><td class="horseNum">3</td></tr></table></body></html>', ("FAIL", "UNSUPPORTED", "UNSUPPORTED"), "ENTRY_TABLE_SCOPE"),
    ],
)
def test_fail_closed_profile_a_matrix(
    source: bytes,
    expected_outcomes: tuple[str, str, str],
    first_nonpass: str,
) -> None:
    result = _diagnose(source)

    assert _outcomes(result) == expected_outcomes
    assert result.overall_result == "BLOCKED"
    assert result.first_nonpass_predicate is not None
    assert result.first_nonpass_predicate.value == first_nonpass
    assert result.to_canonical_dict()["terminal_semantic"] is None


@pytest.mark.parametrize("source", [b"\xff", b"<html><body><article></body></html>"])
def test_invalid_utf8_or_malformed_source_is_unsupported(source: bytes) -> None:
    result = _diagnose(source)

    assert _outcomes(result) == ("UNSUPPORTED",) * 3
    assert result.first_nonpass_predicate is subject.ProfileAPredicateIdentifier.ENTRY_TABLE_SCOPE
    assert result.terminal_reason == "UNSUPPORTED_INPUT"


def test_profile_a_v3_accepts_noncritical_nesting_mismatch_but_v2_remains_frozen() -> None:
    source = _source(_row("3")).replace(b"</article>", b"</main>")
    legacy = subject.diagnose_nar_race_entry_status_profile_a(deba_table_bytes=source, target=TARGET)
    corrected = subject.diagnose_nar_race_entry_status_profile_a_v3(deba_table_bytes=source, target=TARGET)
    assert type(legacy) is subject.ProfileADiagnostics
    assert legacy.to_canonical_dict()["schema_version"] == 2
    assert legacy.overall_result == "BLOCKED"
    assert type(corrected) is subject.ProfileADiagnosticsV3
    assert corrected.to_canonical_dict()["schema_version"] == 3
    assert corrected.overall_result == "QUALIFIED"


def test_profile_a_v3_keeps_semantic_ambiguity_and_utf8_fail_closed() -> None:
    ambiguous = subject.diagnose_nar_race_entry_status_profile_a_v3(
        deba_table_bytes=_source(_row("3"), duplicate_scope=True), target=TARGET
    )
    invalid = subject.diagnose_nar_race_entry_status_profile_a_v3(deba_table_bytes=b"\xff", target=TARGET)
    assert ambiguous.predicate_results[0].outcome is subject.ProfileAOutcome.AMBIGUOUS
    assert invalid.to_canonical_dict()["schema_version"] == 3
    assert _outcomes(invalid) == ("UNSUPPORTED",) * 3


def test_profile_a_v3_canonical_output_is_deterministic() -> None:
    source = _source(_row("3"))
    first = subject.diagnose_nar_race_entry_status_profile_a_v3(deba_table_bytes=source, target=TARGET)
    second = subject.diagnose_nar_race_entry_status_profile_a_v3(deba_table_bytes=source, target=TARGET)
    assert first == second
    assert first.canonical_bytes() == second.canonical_bytes()


def test_result_and_canonical_representation_are_deterministic_and_frozen() -> None:
    source = _source(_row("3"))
    first = _diagnose(source)
    second = _diagnose(source)

    assert first == second
    assert first.canonical_bytes() == second.canonical_bytes()
    assert first.canonical_bytes() == json.dumps(
        first.to_canonical_dict(),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    with pytest.raises(FrozenInstanceError):
        first.target = TARGET  # type: ignore[misc]
    with pytest.raises(TypeError):
        first.predicate_results[0].safe_fields["raw_html"] = "x"  # type: ignore[index]


def test_safe_result_retains_no_raw_html_url_query_or_market_eligibility() -> None:
    marker = "unsafe-visible-marker"
    result = _diagnose(_source(_row("3", href=f"https://invalid.example/{marker}?token={marker}")))
    canonical = result.canonical_bytes()

    assert marker.encode() not in canonical
    assert b"<html" not in canonical
    assert b"https://" not in canonical
    assert b"token=" not in canonical
    assert b"MARKET_ELIGIBLE" not in canonical


def test_exact_input_types_are_required() -> None:
    with pytest.raises(subject.NARRaceEntryStatusProfileAValidationError):
        subject.diagnose_nar_race_entry_status_profile_a(deba_table_bytes=bytearray(b"x"), target=TARGET)  # type: ignore[arg-type]
    with pytest.raises(subject.NARRaceEntryStatusProfileAValidationError):
        subject.diagnose_nar_race_entry_status_profile_a(deba_table_bytes=b"x", target=object())  # type: ignore[arg-type]


def test_module_has_no_network_process_database_clock_or_filesystem_write_path() -> None:
    tree = ast.parse(Path(subject.__file__).read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr)

    assert imported_roots.isdisjoint({"requests", "urllib3", "socket", "subprocess", "sqlite3"})
    assert calls.isdisjoint({"open", "write_bytes", "write_text", "now", "utcnow", "time"})
