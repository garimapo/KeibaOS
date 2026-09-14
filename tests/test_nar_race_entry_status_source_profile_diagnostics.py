from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path

import pytest

from scripts.simulation import nar_race_entry_status_raw_capture as raw_capture
from scripts.simulation import nar_race_entry_status_source_profile_diagnostics as subject


UTC = timezone.utc
TARGET = raw_capture.NARRaceEntryStatusRaceIdentity("21", date(2025, 1, 1), 6)
DEBA_HREF = (
    "/KeibaWeb/TodayRaceInfo/DebaTable?"
    "k_babaCode=21&k_raceDate=2025%2F01%2F01&k_raceNo=6"
)
PREDICATES = (
    "RACE_TABLE_SCOPE",
    "UNIQUE_TARGET_6R",
    "DEBA_LINK_RELATIONSHIP",
    "DEBA_LINK_QUERY_BINDING",
    "WITHDRAWAL_ROW_SHAPE",
    "HORSE_14_WITHDRAWAL_ASSOCIATION",
)


def _source(
    *,
    schedule_rows: str | None = None,
    change_rows: str | None = None,
    duplicate_scope: bool = False,
    include_change_table: bool = True,
) -> bytes:
    schedule = schedule_rows if schedule_rows is not None else (
        f'<tr class="data"><td>6R</td><td><a href="{DEBA_HREF}">entry</a></td></tr>'
    )
    change = change_rows if change_rows is not None else (
        '<tr class="data"><td>6R</td><td>14</td><td>x</td>'
        '<td>出走取消</td><td>x</td><td>x</td></tr>'
    )
    scope = f'<section class="raceTable"><table>{schedule}</table></section>'
    scopes = scope + scope if duplicate_scope else scope
    changes = f'<table class="changeInfo">{change}</table>' if include_change_table else ""
    return f"<html><body>{scopes}{changes}</body></html>".encode("utf-8")


def _diagnose(**changes: object) -> subject.ProfileBDiagnostics:
    return subject.diagnose_nar_race_entry_status_profile_b(
        race_list_bytes=_source(**changes),
        target=TARGET,
    )


def _outcomes(result: subject.ProfileBDiagnostics) -> tuple[str, ...]:
    return tuple(item.outcome.value for item in result.predicate_results)


def test_valid_synthetic_source_qualifies_all_six_predicates() -> None:
    result = _diagnose()

    assert tuple(item.identifier.value for item in result.predicate_results) == PREDICATES
    assert _outcomes(result) == ("PASS",) * 6
    assert result.overall_result == "QUALIFIED"
    assert result.first_nonpass_predicate is None
    assert result.terminal_reason == "QUALIFIED"
    assert result.to_canonical_dict()["terminal_semantic"] == "EXPLICIT_WITHDRAWAL_PRESENT"
    assert b"MARKET_ELIGIBLE" not in result.canonical_bytes()


@pytest.mark.parametrize(
    ("changes", "predicate", "outcome"),
    [
        ({"schedule_rows": '<tr class="data"><td>5R</td></tr>'}, "UNIQUE_TARGET_6R", "FAIL"),
        (
            {"schedule_rows": '<tr class="data"><td>6R</td></tr><tr class="data"><td>6R</td></tr>'},
            "UNIQUE_TARGET_6R",
            "AMBIGUOUS",
        ),
        ({"duplicate_scope": True}, "RACE_TABLE_SCOPE", "AMBIGUOUS"),
        (
            {"schedule_rows": '<tr class="data"><td>6R</td><td>no link</td></tr>'},
            "DEBA_LINK_RELATIONSHIP",
            "FAIL",
        ),
        (
            {"schedule_rows": '<tr class="data"><td>6R</td><td><a href="/wrong">x</a></td></tr>'},
            "DEBA_LINK_RELATIONSHIP",
            "FAIL",
        ),
        (
            {
                "schedule_rows": (
                    '<tr class="data"><td>6R</td><td>'
                    '<a href="/KeibaWeb/TodayRaceInfo/DebaTable?k_babaCode=21&amp;k_raceDate=2025%2F01%2F01&amp;k_raceNo=5">x</a>'
                    "</td></tr>"
                ),
            },
            "DEBA_LINK_QUERY_BINDING",
            "FAIL",
        ),
        ({"include_change_table": False}, "WITHDRAWAL_ROW_SHAPE", "UNSUPPORTED"),
        (
            {"change_rows": '<tr class="data"><td>6R</td><td>14</td><td>x</td><td>出走取消</td></tr>'},
            "WITHDRAWAL_ROW_SHAPE",
            "UNSUPPORTED",
        ),
        (
            {"change_rows": '<tr class="data"><td>6R</td><td>14</td><td>x</td><td>出走</td><td>x</td><td>x</td></tr>'},
            "HORSE_14_WITHDRAWAL_ASSOCIATION",
            "FAIL",
        ),
        (
            {"change_rows": '<tr class="data"><td>6R</td><td>13</td><td>x</td><td>出走取消</td><td>x</td><td>x</td></tr>'},
            "HORSE_14_WITHDRAWAL_ASSOCIATION",
            "FAIL",
        ),
        (
            {"change_rows": '<tr class="data"><td>6R</td><td>horse</td><td>x</td><td>出走取消</td><td>x</td><td>x</td></tr>'},
            "HORSE_14_WITHDRAWAL_ASSOCIATION",
            "UNSUPPORTED",
        ),
        (
            {
                "change_rows": (
                    '<tr class="data"><td>6R</td><td>14</td><td>x</td><td>出走取消</td><td>x</td><td>x</td></tr>'
                    '<tr class="data"><td>6R</td><td>14</td><td>x</td><td>出走取消</td><td>x</td><td>x</td></tr>'
                ),
            },
            "WITHDRAWAL_ROW_SHAPE",
            "AMBIGUOUS",
        ),
        (
            {"change_rows": '<tr class="data"><td>5R</td><td>14</td><td>x</td><td>出走取消</td><td>x</td><td>x</td></tr>'},
            "WITHDRAWAL_ROW_SHAPE",
            "FAIL",
        ),
    ],
)
def test_synthetic_failure_matrix_is_predicate_specific(
    changes: dict[str, object],
    predicate: str,
    outcome: str,
) -> None:
    result = _diagnose(**changes)
    by_name = {item.identifier.value: item.outcome.value for item in result.predicate_results}

    assert by_name[predicate] == outcome
    assert result.overall_result == "BLOCKED"
    assert result.first_nonpass_predicate is not None


def test_multiple_relationships_and_invalid_query_are_fail_closed() -> None:
    two_links = (
        '<tr class="data"><td>6R</td><td>'
        f'<a href="{DEBA_HREF}">a</a><a href="{DEBA_HREF}">b</a>'
        "</td></tr>"
    )
    multiple = _diagnose(schedule_rows=two_links)
    assert multiple.predicate_results[2].outcome is subject.ProfileBPredicateOutcome.AMBIGUOUS
    assert multiple.predicate_results[3].outcome is subject.ProfileBPredicateOutcome.UNSUPPORTED

    malformed = _diagnose(
        schedule_rows=(
            '<tr class="data"><td>6R</td><td>'
            '<a href="/KeibaWeb/TodayRaceInfo/DebaTable?broken">x</a>'
            "</td></tr>"
        ),
    )
    assert malformed.predicate_results[3].outcome is subject.ProfileBPredicateOutcome.UNSUPPORTED


def test_invalid_utf8_and_unavailable_structure_are_unsupported() -> None:
    invalid = subject.diagnose_nar_race_entry_status_profile_b(
        race_list_bytes=b"\xff",
        target=TARGET,
    )
    assert _outcomes(invalid) == ("UNSUPPORTED",) * 6
    assert invalid.first_nonpass_predicate is subject.ProfileBPredicateIdentifier.RACE_TABLE_SCOPE
    assert invalid.terminal_reason == "UNSUPPORTED_INPUT"

    missing = subject.diagnose_nar_race_entry_status_profile_b(
        race_list_bytes=b"<html></html>",
        target=TARGET,
    )
    assert missing.predicate_results[0].outcome is subject.ProfileBPredicateOutcome.FAIL


def test_result_order_first_nonpass_and_canonical_bytes_are_deterministic() -> None:
    source = _source(schedule_rows='<tr class="data"><td>5R</td></tr>')
    first = subject.diagnose_nar_race_entry_status_profile_b(race_list_bytes=source, target=TARGET)
    second = subject.diagnose_nar_race_entry_status_profile_b(race_list_bytes=source, target=TARGET)

    assert first == second
    assert first.canonical_bytes() == second.canonical_bytes()
    assert first.first_nonpass_predicate is subject.ProfileBPredicateIdentifier.UNIQUE_TARGET_6R
    assert json.loads(first.canonical_bytes())["first_nonpass_predicate"] == "UNIQUE_TARGET_6R"


def test_result_is_frozen_and_retains_no_raw_or_arbitrary_url_text() -> None:
    marker = "unsafe-visible-marker"
    source = _source(
        schedule_rows=(
            '<tr class="data"><td>6R</td><td>'
            f'<a href="https://invalid.example/{marker}?token={marker}">x</a>'
            "</td></tr>"
        ),
    )
    result = subject.diagnose_nar_race_entry_status_profile_b(race_list_bytes=source, target=TARGET)
    canonical = result.canonical_bytes()

    assert marker.encode() not in canonical
    assert b"<html" not in canonical
    assert b"https://" not in canonical
    assert b"token" not in canonical
    with pytest.raises(FrozenInstanceError):
        result.target = TARGET  # type: ignore[misc]
    with pytest.raises(TypeError):
        result.predicate_results[0].safe_fields["raw_html"] = "x"  # type: ignore[index]


def test_exact_input_types_are_required() -> None:
    with pytest.raises(subject.NARRaceEntryStatusSourceProfileDiagnosticsValidationError):
        subject.diagnose_nar_race_entry_status_profile_b(race_list_bytes=bytearray(b"x"), target=TARGET)  # type: ignore[arg-type]
    with pytest.raises(subject.NARRaceEntryStatusSourceProfileDiagnosticsValidationError):
        subject.diagnose_nar_race_entry_status_profile_b(race_list_bytes=b"x", target=object())  # type: ignore[arg-type]


def _request(page_kind: raw_capture.NARRaceEntryStatusPageKind) -> raw_capture.NARRaceEntryStatusRequestIdentity:
    return raw_capture.build_nar_race_entry_status_request_identity(
        page_kind=page_kind,
        day_scope=raw_capture.NARRaceEntryStatusDayScope(TARGET.baba_code, TARGET.race_date),
        request_race_no=(TARGET.race_no if page_kind is raw_capture.NARRaceEntryStatusPageKind.DEBA_TABLE else None),
    )


def _capture(
    page_kind: raw_capture.NARRaceEntryStatusPageKind,
    second_offset: int,
) -> raw_capture.NARRaceEntryStatusResponseCapture:
    request = _request(page_kind)
    instant = datetime(2026, 9, 14, 1, 2, second_offset, 123456, tzinfo=UTC)
    return raw_capture.NARRaceEntryStatusResponseCapture(
        request_identity=request,
        effective_url=request.canonical_request_url,
        response_body=b"<html>synthetic</html>",
        charset="UTF-8",
        requested_at=instant,
        observed_at=instant + timedelta(microseconds=1),
        captured_at=instant + timedelta(microseconds=2),
        http_status=200,
        content_type="text/html; charset=UTF-8",
    )


def _bundle() -> raw_capture.NARRaceEntryStatusRawCaptureBundle:
    return raw_capture.NARRaceEntryStatusRawCaptureBundle(
        target_race_identity=TARGET,
        deba_table_capture=_capture(raw_capture.NARRaceEntryStatusPageKind.DEBA_TABLE, 0),
        race_list_capture=_capture(raw_capture.NARRaceEntryStatusPageKind.RACE_LIST, 1),
    )


def test_capture_metadata_summary_is_complete_safe_and_canonical() -> None:
    bundle = _bundle()
    summary = subject.summarize_nar_race_entry_status_capture_bundle(bundle=bundle)
    payload = summary.to_canonical_dict()

    assert summary.closed_bundle_identity == bundle.bundle_id
    assert payload["deba_table"]["request_identity"] == bundle.deba_table_capture.request_identity.request_identity  # type: ignore[index]
    assert payload["race_list"]["capture_identity"] == bundle.race_list_capture.capture_id  # type: ignore[index]
    assert payload["deba_table"]["response_sha256"] == bundle.deba_table_capture.response_sha256  # type: ignore[index]
    assert payload["race_list"]["response_byte_length"] == bundle.race_list_capture.byte_length  # type: ignore[index]
    assert payload["deba_table"]["effective_url_matches_canonical"] is True  # type: ignore[index]
    assert summary.canonical_bytes() == subject.summarize_nar_race_entry_status_capture_bundle(bundle=bundle).canonical_bytes()
    assert b"synthetic" not in summary.canonical_bytes()
    assert b"https://" not in summary.canonical_bytes()


def test_capture_metadata_survives_separate_qualification_failure_representation() -> None:
    summary = subject.summarize_nar_race_entry_status_capture_bundle(bundle=_bundle())
    failed = _diagnose(change_rows='<tr class="data"><td>6R</td><td>14</td><td>x</td><td>出走</td><td>x</td><td>x</td></tr>')

    assert failed.overall_result == "BLOCKED"
    assert summary.deba_table.capture_identity.startswith("nar-race-entry-status-capture-v1:")
    assert summary.race_list.capture_identity.startswith("nar-race-entry-status-capture-v1:")


def test_capture_metadata_missing_or_contradictory_formal_data_fails_closed() -> None:
    bundle = _bundle()
    object.__setattr__(bundle, "bundle_id", "contradictory")
    with pytest.raises(subject.NARRaceEntryStatusSourceProfileDiagnosticsValidationError):
        subject.summarize_nar_race_entry_status_capture_bundle(bundle=bundle)
    with pytest.raises(subject.NARRaceEntryStatusSourceProfileDiagnosticsValidationError):
        subject.summarize_nar_race_entry_status_capture_bundle(bundle=object())  # type: ignore[arg-type]


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
