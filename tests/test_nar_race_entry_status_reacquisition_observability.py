from __future__ import annotations

import copy
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.simulation import nar_race_entry_status_raw_capture as raw_capture
from scripts.simulation import nar_race_entry_status_reacquisition_observability as subject
from scripts.simulation import nar_race_entry_status_source_profile_profile_a as profile_a


RUN_ID = "0123456789abcdef0123456789abcdef"
UTC = timezone.utc
REQUEST_ID = "nar-race-entry-status-request-v1:" + "a" * 64
BUNDLE_ID = "nar-race-entry-status-raw-bundle-v1:" + "b" * 64
CAPTURE_ID = "nar-race-entry-status-capture-v1:" + "9" * 64
FIXTURE_ID_V1 = "nar-race-entry-status-source-profile-fixture-set-v1:" + "e" * 64
FIXTURE_ID_V2 = "nar-race-entry-status-source-profile-fixture-set-v2:" + "e" * 64
FIXTURE_ID_V3 = "nar-race-entry-status-source-profile-fixture-set-v3:" + "e" * 64
QUALIFICATION_ID_V1 = "nar-race-entry-status-source-profile-qualification-v1:" + "f" * 64
QUALIFICATION_ID_V2 = "nar-race-entry-status-source-profile-qualification-v2:" + "f" * 64
QUALIFICATION_ID_V3 = "nar-race-entry-status-source-profile-qualification-v3:" + "f" * 64
DEDICATED_TEST_PATH_V1 = "tests/test_nar_race_entry_status_source_profile_fixtures.py"
DEDICATED_TEST_PATH_V2 = "tests/test_nar_race_entry_status_source_profile_v2_fixtures.py"


def _profile_b_recovery_diagnostics(count: int = 1, *, maximal: bool = False) -> dict[str, object]:
    candidates = []
    if count <= 8:
        for ordinal in range(1, count + 1):
            candidates.append({
                "candidate_ordinal": ordinal, "direct_cell_count": 10000 if maximal else 2,
                "anchor_count": 10000 if maximal else 1,
                "deba_path_link_count": 10000 if maximal else 1,
                "deba_href_unsupported_count": 10000 if maximal else 0,
                "canonical_target_query_match_count": 10000 if maximal else 1,
                "canonical_query_unsupported_count": 10000 if maximal else 0,
                "canonical_target_query_match": True,
            })
    return {
        "schema": "nar-race-entry-status-profile-b-recovery-diagnostics", "schema_version": 1,
        "target": {"baba_code": "21", "race_date": "2025-01-01", "race_no": 6},
        "race_table_scope_count": 1, "target_candidate_count": count,
        "candidate_details_complete": count <= 8, "candidate_results": candidates,
        "all_candidate_safe_projections_equal": 1 <= count <= 8,
    }


def _safety_recovery_diagnostics() -> dict[str, object]:
    return {
        "schema": "nar-race-entry-status-publication-safety-recovery-diagnostics", "schema_version": 1,
        "document_results": [{
            "document_role": role, "utf8_decode": "FAIL",
            "strict_structure": "NOT_REACHED", "beautifulsoup_parse": "NOT_REACHED",
        } for role in ("deba_table", "race_list")],
    }


def _capture_metadata(role: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "document_role": role,
        "request_identity": REQUEST_ID,
        "capture_identity": CAPTURE_ID,
        "response_sha256": "c" * 64,
        "response_byte_length": 123,
        "requested_at": "2026-09-14T00:00:00.000000Z",
        "observed_at": "2026-09-14T00:00:00.000001Z",
        "captured_at": "2026-09-14T00:00:00.000002Z",
        "effective_url_matches_canonical": True,
        "closed_bundle_identity": BUNDLE_ID,
    }


def _strict_structure_recovery_diagnostics() -> dict[str, object]:
    return {
        "schema": "nar-race-entry-status-strict-structure-recovery-diagnostics",
        "schema_version": 1,
        "document_results": [{
            "document_role": role, "failure_kind": "END_TAG_MISMATCH",
            "event_index": 10000, "stack_depth": 10000,
            "expected_open_tag": "OTHER_OR_CUSTOM", "observed_end_tag": "OTHER_OR_CUSTOM",
            "tolerant_parse": "PASS",
        } for role in ("deba_table", "race_list")],
    }


def _candidate_ancestry_recovery_diagnostics(count: int = 1) -> dict[str, object]:
    return {
        "schema": "nar-race-entry-status-profile-b-candidate-ancestry-recovery-diagnostics",
        "schema_version": 1,
        "target": {"baba_code": "21", "race_date": "2025-01-01", "race_no": 6},
        "race_table_scope_count": 1, "target_candidate_count": count,
        "candidate_details_complete": count <= 8,
        "candidate_results": [{
            "candidate_ordinal": ordinal, "nearest_table_role": "CHANGE_INFO_TABLE",
            "inside_change_info_table": True,
            "nested_table_depth_within_race_scope": 10000,
            "direct_schedule_table_descendant": False,
        } for ordinal in range(1, count + 1)] if count <= 8 else [],
    }


def _structural_stage_recovery_diagnostics() -> dict[str, object]:
    payload = _safety_recovery_diagnostics()
    for role in payload["document_results"]:
        role.update(utf8_decode="PASS", strict_structure="FAIL")
    return payload


def _profile_b_diagnostics(schema_version: int = 1) -> dict[str, object]:
    fields = {
        "RACE_TABLE_SCOPE": {"race_table_scope_count": 1},
        "UNIQUE_TARGET_6R": {"target_race_no": 6, "target_6r_row_count": 1},
        "DEBA_LINK_RELATIONSHIP": {"deba_relationship_count": 1, "deba_relationship_present": True},
        "DEBA_LINK_QUERY_BINDING": {"deba_query_binding_count": 1, "deba_query_binding_match": True},
        "WITHDRAWAL_ROW_SHAPE": {"withdrawal_row_shape_count": 1},
        "HORSE_14_WITHDRAWAL_ASSOCIATION": {
            "withdrawn_provider_horse_no": 14,
            "horse_14_withdrawal_count": 1,
            "withdrawal_label_match": True,
        },
    }
    return {
        "schema_version": schema_version,
        "profile": "EXPLICIT_WITHDRAWAL_PRESENT",
        "overall_result": "QUALIFIED",
        "terminal_semantic": "EXPLICIT_WITHDRAWAL_PRESENT",
        "target": {"baba_code": "21", "race_date": "2025-01-01", "race_no": 6},
        "predicate_results": [
            {"identifier": identifier, "outcome": "PASS", "safe_fields": safe_fields}
            for identifier, safe_fields in fields.items()
        ],
        "first_nonpass_predicate": None,
        "terminal_reason": "QUALIFIED",
    }


SAFETY_CATEGORIES = (
    "NO_AUTHENTICATION_MATERIAL",
    "NO_COOKIE_OR_SESSION_SECRET",
    "NO_CSRF_OR_SECRET_TOKEN",
    "NO_USER_ACCOUNT_IDENTIFIER",
    "NO_PERSONALIZATION_IDENTIFIER",
)


def _publication_safety_result(
    outcomes: tuple[str, str, str, str, str] = ("UNSAFE", "SAFE", "SAFE", "SAFE", "SAFE"),
    *,
    finding_count: int = 1,
    schema_version: int = 2,
) -> dict[str, object]:
    aggregate = (
        "SAFE"
        if all(outcome == "SAFE" for outcome in outcomes)
        else "UNSAFE"
        if "UNSAFE" in outcomes
        else "UNSUPPORTED"
        if "UNSUPPORTED" in outcomes
        else "AMBIGUOUS"
    )
    return {
        "schema_version": schema_version,
        "result": aggregate,
        "raw_fixture_publication_safe": aggregate == "SAFE",
        "category_results": [
            {"identifier": identifier, "outcome": outcome, "finding_count": finding_count}
            for identifier, outcome in zip(SAFETY_CATEGORIES, outcomes, strict=True)
        ],
    }


PROFILE_A_PREDICATES = (
    "ENTRY_TABLE_SCOPE",
    "ORDINARY_HORSE_ROW_SHAPE",
    "SELECTED_NON14_LISTING",
)


def _profile_a_blocked_diagnostics(
    outcomes: tuple[str, str, str] = ("PASS", "PASS", "FAIL"),
    *,
    count: int = 1,
    schema_version: int = 2,
) -> dict[str, object]:
    fields = (
        {"entry_table_scope_count": count},
        {"ordinary_row_count": count},
        {"selected_non14_candidate_count": count, "selected_provider_horse_no": None},
    )
    first_index = next(index for index, outcome in enumerate(outcomes) if outcome != "PASS")
    payload: dict[str, object] = {
        "schema_version": schema_version,
        "profile": "ENTRY_LISTING_PRESENT",
        "overall_result": "BLOCKED",
        "terminal_semantic": None,
        "predicate_results": [
            {"identifier": identifier, "outcome": outcome, "safe_fields": safe_fields}
            for identifier, outcome, safe_fields in zip(PROFILE_A_PREDICATES, outcomes, fields, strict=True)
        ],
        "first_nonpass_predicate": PROFILE_A_PREDICATES[first_index],
        "terminal_reason": "UNSUPPORTED_INPUT" if "UNSUPPORTED" in outcomes else "FIRST_NONPASS_PREDICATE",
    }
    if schema_version == 3:
        payload["target"] = {"baba_code": "21", "race_date": "2025-01-01", "race_no": 6}
    return payload


class _Clock:
    def __init__(self) -> None:
        self.value = datetime(2026, 9, 14, tzinfo=UTC)

    def __call__(self) -> datetime:
        current = self.value
        self.value += timedelta(microseconds=1)
        return current


def _paths(tmp_path: Path) -> tuple[Path, Path]:
    repository = tmp_path / "repository"
    external = tmp_path / "external"
    repository.mkdir()
    external.mkdir()
    return repository, external / "journal.jsonl"


def _writer(tmp_path: Path) -> subject.ObservabilityJournalWriter:
    repository, journal = _paths(tmp_path)
    return subject.ObservabilityJournalWriter(
        journal_path=journal,
        repository_root=repository,
        run_id=RUN_ID,
        clock=_Clock(),
    )


def _append_minimal_success(writer: subject.ObservabilityJournalWriter) -> None:
    writer.append(subject.ObservationMilestone.PARENT_EXECUTION_PREPARED, {"run_id": RUN_ID})
    writer.append(subject.ObservationMilestone.LIVE_PROCESS_START, {"pid": 123})
    writer.append(
        subject.ObservationMilestone.LIVE_PROCESS_COMPLETE,
        {"outcome": "SYNTHETIC_SUCCESS", "authorization_state": "UNCONSUMED"},
    )


def _append_through_identity_verification(writer: subject.ObservabilityJournalWriter) -> None:
    writer.append(subject.ObservationMilestone.PARENT_EXECUTION_PREPARED, {"run_id": RUN_ID})
    writer.append(subject.ObservationMilestone.LIVE_PROCESS_START, {"pid": 123})
    writer.append(
        subject.ObservationMilestone.TARGET_CONSTRUCTED,
        {"baba_code": "21", "race_date": "2025-01-01", "race_no": 6},
    )
    writer.append(subject.ObservationMilestone.CLOSED_BUNDLE_RETURNED, {"bundle_id": BUNDLE_ID})
    writer.append(
        subject.ObservationMilestone.DEBA_CAPTURE_METADATA_RETAINED,
        {"capture_metadata": _capture_metadata("deba_table")},
    )
    writer.append(
        subject.ObservationMilestone.RACELIST_CAPTURE_METADATA_RETAINED,
        {"capture_metadata": _capture_metadata("race_list")},
    )
    writer.append(
        subject.ObservationMilestone.PROFILE_B_DIAGNOSTICS_RETAINED,
        {"profile_b_diagnostics": _profile_b_diagnostics()},
    )
    writer.append(subject.ObservationMilestone.IDENTITY_VERIFICATION_PASS, {"bundle_id": BUNDLE_ID})


def _canonical(payload: object) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _record(
    sequence: int = 1,
    *,
    milestone: str = "PARENT_EXECUTION_PREPARED",
    details: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "journal_schema": subject.JOURNAL_SCHEMA,
        "schema_version": 1,
        "run_id": RUN_ID,
        "sequence": sequence,
        "milestone": milestone,
        "occurred_at": "2026-09-14T00:00:00.000000Z",
        "details": {"run_id": RUN_ID} if details is None else details,
    }


def _details_for(milestone: subject.ObservationMilestone) -> dict[str, object]:
    by_milestone: dict[subject.ObservationMilestone, dict[str, object]] = {
        subject.ObservationMilestone.PARENT_EXECUTION_PREPARED: {"run_id": RUN_ID},
        subject.ObservationMilestone.LIVE_PROCESS_START: {"pid": 123},
        subject.ObservationMilestone.TARGET_CONSTRUCTED: {"baba_code": "21", "race_date": "2025-01-01", "race_no": 6},
        subject.ObservationMilestone.PHASE44_CALL_ABOUT_TO_ENTER: {"baba_code": "21", "race_date": "2025-01-01", "race_no": 6},
        subject.ObservationMilestone.DEBA_TRANSPORT_FETCH_ENTERED: {"request_identity": REQUEST_ID},
        subject.ObservationMilestone.DEBA_HTTP_GET_ATTEMPT_ABOUT_TO_START: {"request_identity": REQUEST_ID},
        subject.ObservationMilestone.DEBA_HTTP_RESPONSE_RETURNED: {"request_identity": REQUEST_ID},
        subject.ObservationMilestone.DEBA_RAW_RESPONSE_CONSTRUCTED: {"request_identity": REQUEST_ID, "response_sha256": "c" * 64, "response_byte_length": 123},
        subject.ObservationMilestone.RACELIST_TRANSPORT_FETCH_ENTERED: {"request_identity": REQUEST_ID},
        subject.ObservationMilestone.RACELIST_HTTP_GET_ATTEMPT_ABOUT_TO_START: {"request_identity": REQUEST_ID},
        subject.ObservationMilestone.RACELIST_HTTP_RESPONSE_RETURNED: {"request_identity": REQUEST_ID},
        subject.ObservationMilestone.RACELIST_RAW_RESPONSE_CONSTRUCTED: {"request_identity": REQUEST_ID, "response_sha256": "d" * 64, "response_byte_length": 456},
        subject.ObservationMilestone.CLOSED_BUNDLE_RETURNED: {"bundle_id": BUNDLE_ID},
        subject.ObservationMilestone.DEBA_CAPTURE_METADATA_RETAINED: {"capture_metadata": _capture_metadata("deba_table")},
        subject.ObservationMilestone.RACELIST_CAPTURE_METADATA_RETAINED: {"capture_metadata": _capture_metadata("race_list")},
        subject.ObservationMilestone.PROFILE_B_DIAGNOSTICS_RETAINED: {"profile_b_diagnostics": _profile_b_diagnostics()},
        subject.ObservationMilestone.PROFILE_B_RECOVERY_DIAGNOSTICS_RETAINED: {"profile_b_recovery_diagnostics": _profile_b_recovery_diagnostics()},
        subject.ObservationMilestone.PROFILE_B_CANDIDATE_ANCESTRY_RECOVERY_DIAGNOSTICS_RETAINED: {"profile_b_candidate_ancestry_recovery_diagnostics": _candidate_ancestry_recovery_diagnostics()},
        subject.ObservationMilestone.IDENTITY_VERIFICATION_PASS: {"bundle_id": BUNDLE_ID},
        subject.ObservationMilestone.PUBLICATION_SAFETY_RECOVERY_DIAGNOSTICS_RETAINED: {"publication_safety_recovery_diagnostics": _structural_stage_recovery_diagnostics()},
        subject.ObservationMilestone.STRICT_STRUCTURE_RECOVERY_DIAGNOSTICS_RETAINED: {"strict_structure_recovery_diagnostics": _strict_structure_recovery_diagnostics()},
        subject.ObservationMilestone.PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED: {
            "publication_safety": _publication_safety_result(),
        },
        subject.ObservationMilestone.PROFILE_A_BLOCKED_DIAGNOSTICS_RETAINED: {
            "profile_a_blocked_diagnostics": _profile_a_blocked_diagnostics(),
        },
        subject.ObservationMilestone.PUBLICATION_BEGIN: {"planned_path_count": 7},
        subject.ObservationMilestone.RAW_FIXTURES_WRITTEN: {"document_count": 2},
        subject.ObservationMilestone.MANIFEST_WRITTEN: {
            "fixture_set_identity": FIXTURE_ID_V1,
            "qualification_identity": QUALIFICATION_ID_V1,
        },
        subject.ObservationMilestone.DEDICATED_TEST_WRITTEN: {"test_path": DEDICATED_TEST_PATH_V1},
        subject.ObservationMilestone.REGRESSIONS_PASS: {"command_count": 4},
        subject.ObservationMilestone.LIVE_PROCESS_COMPLETE: {"outcome": "SYNTHETIC_FAILURE", "authorization_state": "CONSUMED_CONFIRMED"},
        subject.ObservationMilestone.PARENT_EVIDENCE_VALIDATION_PASS: {"journal_sha256": "0" * 64},
    }
    return dict(by_milestone.get(milestone, {}))


def test_journal_writes_canonical_lf_records_and_round_trips(tmp_path: Path) -> None:
    writer = _writer(tmp_path)
    first = writer.append(subject.ObservationMilestone.PARENT_EXECUTION_PREPARED, {"run_id": RUN_ID})
    second = writer.append(subject.ObservationMilestone.LIVE_PROCESS_START, {"pid": 123})
    path = writer.path
    writer.close()

    data = path.read_bytes()
    assert data.endswith(b"\n") and b"\r\n" not in data
    assert len(data.splitlines()) == 2
    records = subject.validate_journal_bytes(data, expected_run_id=RUN_ID)
    assert records == (first, second)
    subject.validate_journal_semantics(records)


def _manifest_record_bytes(fixture_identity: object, qualification_identity: object) -> bytes:
    payload = _record(
        milestone="MANIFEST_WRITTEN",
        details={
            "fixture_set_identity": fixture_identity,
            "qualification_identity": qualification_identity,
        },
    )
    return _canonical(payload) + b"\n"


def _dedicated_test_record_bytes(test_path: object, details: dict[str, object] | None = None) -> bytes:
    payload = _record(
        milestone="DEDICATED_TEST_WRITTEN",
        details={"test_path": test_path} if details is None else details,
    )
    return _canonical(payload) + b"\n"


@pytest.mark.parametrize(
    ("test_path", "expected_record_bytes"),
    [(DEDICATED_TEST_PATH_V1, 322), (DEDICATED_TEST_PATH_V2, 325)],
)
def test_dedicated_test_written_accepts_exact_closed_path_union(
    test_path: str,
    expected_record_bytes: int,
) -> None:
    data = _dedicated_test_record_bytes(test_path)
    records = subject.validate_journal_bytes(data, expected_run_id=RUN_ID)

    assert records[0].milestone is subject.ObservationMilestone.DEDICATED_TEST_WRITTEN
    assert records[0].details == {"test_path": test_path}
    assert len(data) == expected_record_bytes < subject.MAX_RECORD_BYTES


@pytest.mark.parametrize(
    "test_path",
    [
        "tests/test_nar_race_entry_status_source_profile_v3_fixtures.py",
        "tests/arbitrary_third_test.py",
        DEDICATED_TEST_PATH_V1 + ".bak",
        DEDICATED_TEST_PATH_V2 + ".bak",
        "test/test_nar_race_entry_status_source_profile_v2_fixtures.py",
        "/" + DEDICATED_TEST_PATH_V2,
        "C:/" + DEDICATED_TEST_PATH_V2,
        DEDICATED_TEST_PATH_V2.replace("/", "\\"),
        " " + DEDICATED_TEST_PATH_V2,
        DEDICATED_TEST_PATH_V2 + " ",
        DEDICATED_TEST_PATH_V2 + "\n",
        DEDICATED_TEST_PATH_V2 + "\r",
        DEDICATED_TEST_PATH_V2 + "\x00",
        DEDICATED_TEST_PATH_V2 + "\x1f",
        "tests/../" + DEDICATED_TEST_PATH_V2,
    ],
)
def test_dedicated_test_written_rejects_every_path_outside_closed_union(test_path: str) -> None:
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        subject.validate_journal_bytes(
            _dedicated_test_record_bytes(test_path),
            expected_run_id=RUN_ID,
        )


@pytest.mark.parametrize("details", [{}, {"test_path": DEDICATED_TEST_PATH_V2, "extra": "forbidden"}])
def test_dedicated_test_written_requires_exact_detail_key(details: dict[str, object]) -> None:
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        subject.validate_journal_bytes(
            _dedicated_test_record_bytes(DEDICATED_TEST_PATH_V2, details),
            expected_run_id=RUN_ID,
        )


def test_phase61_dedicated_test_path_compatibility_preserves_phase50_contracts() -> None:
    expected_order = (
        subject.ObservationMilestone.RAW_FIXTURES_WRITTEN,
        subject.ObservationMilestone.MANIFEST_WRITTEN,
        subject.ObservationMilestone.DEDICATED_TEST_WRITTEN,
        subject.ObservationMilestone.REGRESSIONS_PASS,
    )
    start = list(subject.ObservationMilestone).index(expected_order[0])

    assert tuple(subject.ObservationMilestone)[start : start + len(expected_order)] == expected_order
    assert subject._DETAIL_KEYS[subject.ObservationMilestone.DEDICATED_TEST_WRITTEN] == frozenset({"test_path"})
    assert subject._DEDICATED_TEST_PATHS == frozenset({DEDICATED_TEST_PATH_V1, DEDICATED_TEST_PATH_V2})
    assert subject.JOURNAL_SCHEMA_VERSION == 1
    assert subject.MAX_STRING_BYTES == 512
    assert subject.MAX_RECORD_BYTES == 4096
    assert subject.MAX_JOURNAL_BYTES == 131072
    assert subject.MAX_PROCESS_STREAM_BYTES == 16384
    assert subject.PREFLIGHT_PASS_TOKEN == "NAR_REACQUISITION_OBSERVABILITY_PREFLIGHT_PASS"
    assert subject._ALLOWED_OUTCOMES == frozenset(
        {
            "READY_FOR_REVIEW",
            "SOURCE_PROFILE_FIXTURE_BLOCKED",
            "RECOVERY_PREFLIGHT_BLOCKED",
            "SYNTHETIC_SUCCESS",
            "SYNTHETIC_FAILURE",
        },
    )


@pytest.mark.parametrize(
    ("fixture_identity", "qualification_identity"),
    [
        (FIXTURE_ID_V1, QUALIFICATION_ID_V1),
        (FIXTURE_ID_V2, QUALIFICATION_ID_V2),
        (FIXTURE_ID_V3, QUALIFICATION_ID_V3),
    ],
)
def test_manifest_written_accepts_only_canonical_same_version_identity_pairs(
    fixture_identity: str,
    qualification_identity: str,
) -> None:
    data = _manifest_record_bytes(fixture_identity, qualification_identity)
    records = subject.validate_journal_bytes(data, expected_run_id=RUN_ID)
    assert records[0].details == {
        "fixture_set_identity": fixture_identity,
        "qualification_identity": qualification_identity,
    }
    assert len(data) - 1 <= subject.MAX_RECORD_BYTES
    assert subject._DETAIL_KEYS[subject.ObservationMilestone.MANIFEST_WRITTEN] == frozenset(
        {"fixture_set_identity", "qualification_identity"},
    )


@pytest.mark.parametrize(
    ("fixture_identity", "qualification_identity"),
    [
        (FIXTURE_ID_V1, QUALIFICATION_ID_V2),
        (FIXTURE_ID_V2, QUALIFICATION_ID_V1),
        (FIXTURE_ID_V2, QUALIFICATION_ID_V3),
        (FIXTURE_ID_V3, QUALIFICATION_ID_V2),
    ],
)
def test_manifest_written_rejects_mixed_identity_versions(
    fixture_identity: str,
    qualification_identity: str,
) -> None:
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        subject.validate_journal_bytes(
            _manifest_record_bytes(fixture_identity, qualification_identity),
            expected_run_id=RUN_ID,
        )


@pytest.mark.parametrize(
    "fixture_identity",
    [
        "nar-race-entry-status-source-profile-fixture-set-v0:" + "e" * 64,
        "nar-race-entry-status-source-profile-fixture-set-v4:" + "e" * 64,
        "nar-race-entry-status-source-profile-fixture-set-v2:" + "E" * 64,
        "NAR-race-entry-status-source-profile-fixture-set-v2:" + "e" * 64,
        "nar-race-entry-status-source-profile-fixture-set-v2:" + "e" * 63,
        "nar-race-entry-status-source-profile-fixture-set-v2:" + "e" * 65,
        "nar-race-entry-status-source-profile-fixture-set-v2:" + "g" * 64,
        "nar-race-entry-status-source-profile-fixture-set-v2:",
        "nar-race-entry-status-source-profile-fixture-v2:" + "e" * 64,
        FIXTURE_ID_V2 + "suffix",
        " " + FIXTURE_ID_V2,
        FIXTURE_ID_V2 + " ",
        FIXTURE_ID_V2 + "\n",
        FIXTURE_ID_V2 + "\r",
    ],
)
def test_manifest_written_rejects_noncanonical_fixture_identity(fixture_identity: str) -> None:
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        subject.validate_journal_bytes(
            _manifest_record_bytes(fixture_identity, QUALIFICATION_ID_V2),
            expected_run_id=RUN_ID,
        )


@pytest.mark.parametrize(
    "qualification_identity",
    [
        "nar-race-entry-status-source-profile-qualification-v0:" + "f" * 64,
        "nar-race-entry-status-source-profile-qualification-v4:" + "f" * 64,
        "nar-race-entry-status-source-profile-qualification-v2:" + "F" * 64,
        "NAR-race-entry-status-source-profile-qualification-v2:" + "f" * 64,
        "nar-race-entry-status-source-profile-qualification-v2:" + "f" * 63,
        "nar-race-entry-status-source-profile-qualification-v2:" + "f" * 65,
        "nar-race-entry-status-source-profile-qualification-v2:" + "g" * 64,
        "nar-race-entry-status-source-profile-qualification-v2:",
        "nar-race-entry-status-source-profile-qualifier-v2:" + "f" * 64,
        QUALIFICATION_ID_V2 + "suffix",
        " " + QUALIFICATION_ID_V2,
        QUALIFICATION_ID_V2 + " ",
        QUALIFICATION_ID_V2 + "\n",
        QUALIFICATION_ID_V2 + "\r",
    ],
)
def test_manifest_written_rejects_noncanonical_qualification_identity(qualification_identity: str) -> None:
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        subject.validate_journal_bytes(
            _manifest_record_bytes(FIXTURE_ID_V2, qualification_identity),
            expected_run_id=RUN_ID,
        )


def test_phase59_identity_compatibility_preserves_observability_contracts() -> None:
    expected_order = (
        subject.ObservationMilestone.PROFILE_B_DIAGNOSTICS_RETAINED,
        subject.ObservationMilestone.PROFILE_B_RECOVERY_DIAGNOSTICS_RETAINED,
        subject.ObservationMilestone.IDENTITY_VERIFICATION_PASS,
        subject.ObservationMilestone.PUBLICATION_SAFETY_RECOVERY_DIAGNOSTICS_RETAINED,
        subject.ObservationMilestone.PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED,
        subject.ObservationMilestone.SAFETY_PASS,
        subject.ObservationMilestone.PROFILE_A_BLOCKED_DIAGNOSTICS_RETAINED,
        subject.ObservationMilestone.PROFILE_A_QUALIFIED,
        subject.ObservationMilestone.PROFILE_B_QUALIFIED,
        subject.ObservationMilestone.PUBLICATION_BEGIN,
        subject.ObservationMilestone.RAW_FIXTURES_WRITTEN,
        subject.ObservationMilestone.MANIFEST_WRITTEN,
    )
    historical_order = tuple(m for m in subject.ObservationMilestone if m not in {
        subject.ObservationMilestone.PROFILE_B_CANDIDATE_ANCESTRY_RECOVERY_DIAGNOSTICS_RETAINED,
        subject.ObservationMilestone.STRICT_STRUCTURE_RECOVERY_DIAGNOSTICS_RETAINED,
    })
    start = historical_order.index(expected_order[0])
    assert historical_order[start : start + len(expected_order)] == expected_order
    assert subject.JOURNAL_SCHEMA_VERSION == 1
    assert subject.PREFLIGHT_PASS_TOKEN == "NAR_REACQUISITION_OBSERVABILITY_PREFLIGHT_PASS"
    assert subject._ALLOWED_OUTCOMES == frozenset(
        {
            "READY_FOR_REVIEW",
            "SOURCE_PROFILE_FIXTURE_BLOCKED",
            "RECOVERY_PREFLIGHT_BLOCKED",
            "SYNTHETIC_SUCCESS",
            "SYNTHETIC_FAILURE",
        },
    )


def test_journal_path_must_be_external_and_creation_is_exclusive(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        subject.ObservabilityJournalWriter(
            journal_path=repository / "journal.jsonl",
            repository_root=repository,
            run_id=RUN_ID,
            clock=_Clock(),
        )
    external = tmp_path / "journal.jsonl"
    external.write_bytes(b"existing")
    with pytest.raises(subject.NARReacquisitionObservabilityJournalError):
        subject.ObservabilityJournalWriter(
            journal_path=external,
            repository_root=repository,
            run_id=RUN_ID,
            clock=_Clock(),
        )


def test_journal_append_flushes_and_fsyncs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[int] = []
    monkeypatch.setattr(subject.os, "fsync", calls.append)
    writer = _writer(tmp_path)
    writer.append(subject.ObservationMilestone.PARENT_EXECUTION_PREPARED, {"run_id": RUN_ID})
    writer.close()
    assert len(calls) == 1
    assert type(calls[0]) is int


@pytest.mark.parametrize("operation", ["write", "flush", "fsync"])
def test_journal_durability_failure_is_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    operation: str,
) -> None:
    writer = _writer(tmp_path)
    if operation == "fsync":
        monkeypatch.setattr(subject.os, "fsync", lambda _fd: (_ for _ in ()).throw(OSError("fsync")))
    else:
        stream = writer._stream
        assert stream is not None
        monkeypatch.setattr(stream, operation, lambda *_args: (_ for _ in ()).throw(OSError(operation)))
    with pytest.raises(subject.NARReacquisitionObservabilityJournalError):
        writer.append(subject.ObservationMilestone.PARENT_EXECUTION_PREPARED, {"run_id": RUN_ID})
    assert writer.sequence == 0
    try:
        writer.close()
    except subject.NARReacquisitionObservabilityJournalError:
        pass


@pytest.mark.parametrize(
    "mutation",
    [
        "invalid_utf8",
        "truncated",
        "crlf",
        "malformed",
        "noncanonical",
        "unexpected_top_key",
        "unknown_event",
        "unexpected_detail_key",
        "control_character",
        "oversized_value",
    ],
)
def test_journal_validation_rejects_malformed_or_unsafe_records(mutation: str) -> None:
    payload = _record()
    if mutation == "invalid_utf8":
        data = b"\xff\n"
    elif mutation == "truncated":
        data = _canonical(payload)
    elif mutation == "crlf":
        data = _canonical(payload) + b"\r\n"
    elif mutation == "malformed":
        data = b"{\n"
    elif mutation == "noncanonical":
        data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    else:
        if mutation == "unexpected_top_key":
            payload["secret"] = "value"
        elif mutation == "unknown_event":
            payload["milestone"] = "UNKNOWN_EVENT"
        elif mutation == "unexpected_detail_key":
            payload["details"] = {"run_id": RUN_ID, "token": "secret"}
        elif mutation == "control_character":
            payload["details"] = {"run_id": RUN_ID + "\t"}
        elif mutation == "oversized_value":
            payload["details"] = {"run_id": "a" * 513}
        data = _canonical(payload) + b"\n"
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        subject.validate_journal_bytes(data)


@pytest.mark.parametrize("sequences", [(1, 1), (1, 3), (2, 1)])
def test_journal_validation_rejects_duplicate_skipped_or_decreasing_sequence(
    sequences: tuple[int, int],
) -> None:
    first = _record(sequences[0])
    second = _record(
        sequences[1],
        milestone="LIVE_PROCESS_START",
        details={"pid": 123},
    )
    data = _canonical(first) + b"\n" + _canonical(second) + b"\n"
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        subject.validate_journal_bytes(data)


def test_journal_rejects_duplicate_event_and_semantic_reordering() -> None:
    first = _record()
    duplicate = _record(2)
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        subject.validate_journal_bytes(_canonical(first) + b"\n" + _canonical(duplicate) + b"\n")

    records = (
        subject.JournalRecord(subject.JOURNAL_SCHEMA, 1, RUN_ID, 1, subject.ObservationMilestone.PARENT_EXECUTION_PREPARED, "2026-09-14T00:00:00.000000Z", {"run_id": RUN_ID}),
        subject.JournalRecord(subject.JOURNAL_SCHEMA, 1, RUN_ID, 2, subject.ObservationMilestone.SAFETY_PASS, "2026-09-14T00:00:00.000001Z", {}),
        subject.JournalRecord(subject.JOURNAL_SCHEMA, 1, RUN_ID, 3, subject.ObservationMilestone.PHASE44_FUNCTION_ENTERED, "2026-09-14T00:00:00.000002Z", {}),
    )
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        subject.validate_journal_semantics(records)


def test_sensitive_value_is_rejected_even_in_an_allowlisted_key() -> None:
    payload = _record(
        milestone="LIVE_PROCESS_COMPLETE",
        details={"outcome": "SECRET_TOKEN", "authorization_state": "UNCONSUMED"},
    )
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        subject.validate_journal_bytes(_canonical(payload) + b"\n")


@pytest.mark.parametrize("last_milestone", list(subject.ObservationMilestone))
def test_parent_reconstructs_every_confirmed_failure_boundary(
    tmp_path: Path,
    last_milestone: subject.ObservationMilestone,
) -> None:
    writer = _writer(tmp_path)
    blocking = {
        subject.ObservationMilestone.PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED,
        subject.ObservationMilestone.PROFILE_A_BLOCKED_DIAGNOSTICS_RETAINED,
    }
    if last_milestone is subject.ObservationMilestone.PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED:
        milestones = tuple(
            milestone
            for milestone in subject.ObservationMilestone
            if subject._MILESTONE_ORDER[milestone]
            <= subject._MILESTONE_ORDER[subject.ObservationMilestone.IDENTITY_VERIFICATION_PASS]
            and milestone not in blocking
        ) + (last_milestone,)
    elif last_milestone is subject.ObservationMilestone.PROFILE_A_BLOCKED_DIAGNOSTICS_RETAINED:
        milestones = tuple(
            milestone
            for milestone in subject.ObservationMilestone
            if milestone not in blocking
            and subject._MILESTONE_ORDER[milestone] <= subject._MILESTONE_ORDER[subject.ObservationMilestone.SAFETY_PASS]
        ) + (last_milestone,)
    else:
        milestones = tuple(milestone for milestone in subject.ObservationMilestone if milestone not in blocking)
    for milestone in milestones:
        writer.append(milestone, _details_for(milestone))
        if milestone is last_milestone:
            break
    writer.close()
    evidence = subject.retain_child_process_evidence(
        return_code=17,
        stdout=b"",
        stderr=b"synthetic child failure",
        journal_bytes=writer.path.read_bytes(),
        expected_run_id=RUN_ID,
    )
    assert evidence.return_code == 17
    assert evidence.journal_syntactically_valid
    assert evidence.journal_semantically_valid
    assert evidence.execution is not None
    assert evidence.execution.last_milestone is last_milestone


def test_authorization_reconstruction_is_fail_closed(tmp_path: Path) -> None:
    writer = _writer(tmp_path)
    writer.append(subject.ObservationMilestone.PARENT_EXECUTION_PREPARED, {"run_id": RUN_ID})
    writer.append(subject.ObservationMilestone.LIVE_PROCESS_START, {"pid": 123})
    writer.append(
        subject.ObservationMilestone.TARGET_CONSTRUCTED,
        {"baba_code": "21", "race_date": "2025-01-01", "race_no": 6},
    )
    before = subject.reconstruct_execution(
        subject.validate_journal_bytes(writer.path.read_bytes(), expected_run_id=RUN_ID),
    )
    assert before.authorization_state == "UNCONSUMED"
    writer.append(
        subject.ObservationMilestone.PHASE44_CALL_ABOUT_TO_ENTER,
        {"baba_code": "21", "race_date": "2025-01-01", "race_no": 6},
    )
    durable = subject.reconstruct_execution(
        subject.validate_journal_bytes(writer.path.read_bytes(), expected_run_id=RUN_ID),
    )
    assert durable.authorization_state == "CONSUMED_FAIL_CLOSED"
    writer.append(subject.ObservationMilestone.PHASE44_FUNCTION_ENTERED, {})
    entered = subject.reconstruct_execution(
        subject.validate_journal_bytes(writer.path.read_bytes(), expected_run_id=RUN_ID),
    )
    assert entered.authorization_state == "CONSUMED_CONFIRMED"
    writer.close()


def test_phase44_bridge_records_truthful_boundaries_and_restores_binding(tmp_path: Path) -> None:
    writer = _writer(tmp_path)
    writer.append(subject.ObservationMilestone.PARENT_EXECUTION_PREPARED, {"run_id": RUN_ID})
    writer.append(subject.ObservationMilestone.LIVE_PROCESS_START, {"pid": 123})
    writer.append(
        subject.ObservationMilestone.TARGET_CONSTRUCTED,
        {"baba_code": "21", "race_date": "2025-01-01", "race_no": 6},
    )
    writer.append(
        subject.ObservationMilestone.PHASE44_CALL_ABOUT_TO_ENTER,
        {"baba_code": "21", "race_date": "2025-01-01", "race_no": 6},
    )
    bridge = subject.Phase44ObservationBridge(writer)
    with raw_capture._raw_capture_observer_scope(bridge):
        raw_capture._emit_raw_capture_observation(
            raw_capture._RawCaptureObservationEvent(kind="ACQUISITION_FUNCTION_ENTERED"),
        )
        raw_capture._emit_raw_capture_observation(
            raw_capture._RawCaptureObservationEvent(
                kind="TRANSPORT_FETCH_ABOUT_TO_START",
                page_kind=raw_capture.NARRaceEntryStatusPageKind.DEBA_TABLE,
                request_identity=REQUEST_ID,
            ),
        )
        raw_capture._emit_raw_capture_observation(
            raw_capture._RawCaptureObservationEvent(
                kind="HTTP_GET_ATTEMPT_ABOUT_TO_START",
                page_kind=raw_capture.NARRaceEntryStatusPageKind.DEBA_TABLE,
                request_identity=REQUEST_ID,
            ),
        )
    raw_capture._emit_raw_capture_observation(
        raw_capture._RawCaptureObservationEvent(kind="ACQUISITION_FUNCTION_ENTERED"),
    )
    writer.close()
    records = subject.validate_journal_bytes(writer.path.read_bytes())
    assert [record.milestone for record in records][-3:] == [
        subject.ObservationMilestone.PHASE44_FUNCTION_ENTERED,
        subject.ObservationMilestone.DEBA_TRANSPORT_FETCH_ENTERED,
        subject.ObservationMilestone.DEBA_HTTP_GET_ATTEMPT_ABOUT_TO_START,
    ]


def test_phase44_bridge_requires_constructed_bundle_before_return_record(tmp_path: Path) -> None:
    writer = _writer(tmp_path)
    bridge = subject.Phase44ObservationBridge(writer)
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        bridge.record_closed_bundle_returned(BUNDLE_ID)
    bridge(raw_capture._RawCaptureObservationEvent(kind="CLOSED_BUNDLE_CONSTRUCTED", bundle_id=BUNDLE_ID))
    bridge.record_closed_bundle_returned(BUNDLE_ID)
    writer.close()
    assert subject.validate_journal_bytes(writer.path.read_bytes())[-1].milestone is subject.ObservationMilestone.CLOSED_BUNDLE_RETURNED


def test_durable_pre_get_journal_failure_prevents_session_get(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class Session:
        def __init__(self) -> None:
            self.trust_env = True
            self.headers: dict[str, str] = {"default": "value"}
            self.get_called = False

        def mount(self, _prefix: str, _adapter: object) -> None:
            pass

        def get(self, _url: str, **_options: object) -> object:
            self.get_called = True
            raise AssertionError("Session.get must not be reached")

        def close(self) -> None:
            pass

    session = Session()
    monkeypatch.setattr(raw_capture._requests, "Session", lambda: session)
    writer = _writer(tmp_path)
    bridge = subject.Phase44ObservationBridge(writer)
    monkeypatch.setattr(subject.os, "fsync", lambda _fd: (_ for _ in ()).throw(OSError("fsync failed")))
    request = raw_capture.build_nar_race_entry_status_request_identity(
        page_kind=raw_capture.NARRaceEntryStatusPageKind.DEBA_TABLE,
        day_scope=raw_capture.NARRaceEntryStatusDayScope("21", date(2025, 1, 1)),
        request_race_no=6,
    )
    with pytest.raises(raw_capture.NARRaceEntryStatusRawCaptureTransportError):
        with raw_capture._raw_capture_observer_scope(bridge):
            raw_capture.RequestsNARRaceEntryStatusRawCaptureTransport().fetch(
                request_identity=request,
            )
    assert not session.get_called
    assert writer.sequence == 0
    writer.close()


@pytest.mark.parametrize(
    ("return_code", "stdout", "stderr", "stdout_class", "stderr_class"),
    [
        (0, b"", b"", "EMPTY", "EMPTY"),
        (0, subject.PREFLIGHT_PASS_TOKEN.encode() + b"\n", b"warning", "SAFE_PREFLIGHT_TOKEN", "UNCONTROLLED_OUTPUT_REDACTED"),
        (1, b"failed", b"problem", "UNCONTROLLED_OUTPUT_REDACTED", "UNCONTROLLED_OUTPUT_REDACTED"),
        (1, b"\xff", b"", "INVALID_UTF8", "EMPTY"),
    ],
)
def test_child_evidence_retains_return_and_sanitized_stream_dimensions(
    tmp_path: Path,
    return_code: int,
    stdout: bytes,
    stderr: bytes,
    stdout_class: str,
    stderr_class: str,
) -> None:
    writer = _writer(tmp_path)
    _append_minimal_success(writer)
    writer.close()
    evidence = subject.retain_child_process_evidence(
        return_code=return_code,
        stdout=stdout,
        stderr=stderr,
        journal_bytes=writer.path.read_bytes(),
        expected_run_id=RUN_ID,
    )
    assert evidence.return_code == return_code
    assert evidence.stdout.classification == stdout_class
    assert evidence.stderr.classification == stderr_class
    assert evidence.journal_syntactically_valid
    assert evidence.journal_semantically_valid


def test_nonempty_stderr_does_not_override_valid_zero_exit_or_journal(tmp_path: Path) -> None:
    writer = _writer(tmp_path)
    _append_minimal_success(writer)
    writer.close()
    evidence = subject.retain_child_process_evidence(
        return_code=0,
        stdout=subject.PREFLIGHT_PASS_TOKEN.encode() + b"\n",
        stderr=b"synthetic warning",
        journal_bytes=writer.path.read_bytes(),
        expected_run_id=RUN_ID,
    )
    assert evidence.return_code == 0
    assert evidence.stderr.present
    assert subject.preflight_result(
        child_evidence=evidence,
        cleanup_succeeded=True,
        bytecode_residue_absent=True,
    ) == subject.PREFLIGHT_PASS_TOKEN


@pytest.mark.parametrize(
    ("return_code", "stdout", "cleanup", "no_residue"),
    [
        (1, b"NAR_REACQUISITION_OBSERVABILITY_PREFLIGHT_PASS\n", True, True),
        (0, b"wrong\n", True, True),
        (0, b"NAR_REACQUISITION_OBSERVABILITY_PREFLIGHT_PASS\n", False, True),
        (0, b"NAR_REACQUISITION_OBSERVABILITY_PREFLIGHT_PASS\n", True, False),
    ],
)
def test_preflight_token_is_unavailable_when_any_gate_fails(
    tmp_path: Path,
    return_code: int,
    stdout: bytes,
    cleanup: bool,
    no_residue: bool,
) -> None:
    writer = _writer(tmp_path)
    _append_minimal_success(writer)
    writer.close()
    evidence = subject.retain_child_process_evidence(
        return_code=return_code,
        stdout=stdout,
        stderr=b"",
        journal_bytes=writer.path.read_bytes(),
        expected_run_id=RUN_ID,
    )
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        subject.preflight_result(
            child_evidence=evidence,
            cleanup_succeeded=cleanup,
            bytecode_residue_absent=no_residue,
        )


def test_parent_retains_stream_metadata_even_when_journal_is_invalid() -> None:
    evidence = subject.retain_child_process_evidence(
        return_code=7,
        stdout=b"child output",
        stderr=b"child error",
        journal_bytes=b"invalid\n",
        expected_run_id=RUN_ID,
    )
    assert evidence.return_code == 7
    assert evidence.stdout.byte_length == len(b"child output")
    assert evidence.stderr.sha256 == hashlib.sha256(b"child error").hexdigest()
    assert not evidence.journal_syntactically_valid
    assert evidence.execution is None


def test_generated_source_compile_gate_and_bytecode_disabled_child_leave_no_residue(tmp_path: Path) -> None:
    source_lines = ["from pathlib import Path", "print('synthetic-child')"]
    generated_source = "\n".join(source_lines) + "\n"
    subject.validate_generated_source(generated_source)
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        subject.validate_generated_source("def broken(:\n")

    source_path = tmp_path / "synthetic_child.py"
    source_path.write_text(generated_source, encoding="utf-8", newline="\n")
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [sys.executable, "-B", str(source_path)],
        cwd=tmp_path,
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == b"synthetic-child\r\n" or completed.stdout == b"synthetic-child\n"
    assert not list(tmp_path.rglob("*.pyc"))
    assert not list(tmp_path.rglob("__pycache__"))
    source_path.unlink()
    assert not source_path.exists()


def test_module_has_no_network_database_or_raw_content_functionality() -> None:
    source = Path(subject.__file__).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests.",
        "urllib",
        "session.get",
        "sqlite",
        "keiba.db",
        "response_body",
        "set-cookie",
    ):
        assert forbidden not in lowered


def test_three_typed_retention_events_round_trip_canonically(tmp_path: Path) -> None:
    writer = _writer(tmp_path)
    for milestone in subject.ObservationMilestone:
        writer.append(milestone, _details_for(milestone))
        if milestone is subject.ObservationMilestone.PROFILE_B_DIAGNOSTICS_RETAINED:
            break
    writer.close()

    data = writer.path.read_bytes()
    records = subject.validate_journal_bytes(data, expected_run_id=RUN_ID)
    subject.validate_journal_semantics(records)
    assert [record.milestone for record in records[-3:]] == [
        subject.ObservationMilestone.DEBA_CAPTURE_METADATA_RETAINED,
        subject.ObservationMilestone.RACELIST_CAPTURE_METADATA_RETAINED,
        subject.ObservationMilestone.PROFILE_B_DIAGNOSTICS_RETAINED,
    ]
    assert records[-3].details["capture_metadata"] == _capture_metadata("deba_table")
    assert records[-2].details["capture_metadata"] == _capture_metadata("race_list")
    assert records[-1].details["profile_b_diagnostics"] == _profile_b_diagnostics()


@pytest.mark.parametrize(
    "mutation",
    [
        "unexpected_capture_key",
        "raw_capture_field",
        "wrong_capture_type",
        "wrong_role",
        "unsafe_url",
        "wrong_diagnostics_type",
        "unexpected_diagnostics_key",
        "raw_diagnostics_field",
        "unsafe_predicate_key",
        "wrong_predicate_type",
        "oversized_predicate_value",
        "inconsistent_first_failure",
    ],
)
def test_typed_retention_events_reject_unsafe_or_invalid_fields(
    tmp_path: Path,
    mutation: str,
) -> None:
    writer = _writer(tmp_path)
    if mutation.startswith(("unexpected_capture", "raw_capture", "wrong_capture", "wrong_role", "unsafe_url")):
        metadata: object = _capture_metadata("deba_table")
        if mutation == "unexpected_capture_key":
            metadata["extra"] = "x"  # type: ignore[index]
        elif mutation == "raw_capture_field":
            metadata["response_body"] = "<html>"  # type: ignore[index]
        elif mutation == "wrong_capture_type":
            metadata["response_byte_length"] = "123"  # type: ignore[index]
        elif mutation == "wrong_role":
            metadata["document_role"] = "race_list"  # type: ignore[index]
        else:
            metadata["effective_url"] = "https://example.invalid/?token=secret"  # type: ignore[index]
        milestone = subject.ObservationMilestone.DEBA_CAPTURE_METADATA_RETAINED
        details = {"capture_metadata": metadata}
    else:
        diagnostics: object = _profile_b_diagnostics()
        if mutation == "wrong_diagnostics_type":
            diagnostics = []
        elif mutation == "unexpected_diagnostics_key":
            diagnostics["extra"] = "x"  # type: ignore[index]
        elif mutation == "raw_diagnostics_field":
            diagnostics["raw_html"] = "<html>"  # type: ignore[index]
        elif mutation == "unsafe_predicate_key":
            diagnostics["predicate_results"][0]["safe_fields"]["url"] = "https://example.invalid"  # type: ignore[index]
        elif mutation == "wrong_predicate_type":
            diagnostics["predicate_results"][0]["safe_fields"]["race_table_scope_count"] = "1"  # type: ignore[index]
        elif mutation == "oversized_predicate_value":
            diagnostics["predicate_results"][0]["safe_fields"]["race_table_scope_count"] = 10**100  # type: ignore[index]
        else:
            diagnostics["first_nonpass_predicate"] = "RACE_TABLE_SCOPE"  # type: ignore[index]
        milestone = subject.ObservationMilestone.PROFILE_B_DIAGNOSTICS_RETAINED
        details = {"profile_b_diagnostics": diagnostics}
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        writer.append(milestone, details)
    writer.close()


def test_retention_event_semantics_require_closed_bundle_and_order(tmp_path: Path) -> None:
    writer = _writer(tmp_path)
    writer.append(subject.ObservationMilestone.PARENT_EXECUTION_PREPARED, {"run_id": RUN_ID})
    writer.append(
        subject.ObservationMilestone.DEBA_CAPTURE_METADATA_RETAINED,
        {"capture_metadata": _capture_metadata("deba_table")},
    )
    writer.close()
    records = subject.validate_journal_bytes(writer.path.read_bytes())
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        subject.validate_journal_semantics(records)


def test_existing_preflight_contract_is_unchanged_after_additive_events(tmp_path: Path) -> None:
    writer = _writer(tmp_path)
    _append_minimal_success(writer)
    writer.close()
    evidence = subject.retain_child_process_evidence(
        return_code=0,
        stdout=subject.PREFLIGHT_PASS_TOKEN.encode("ascii") + b"\n",
        stderr=b"",
        journal_bytes=writer.path.read_bytes(),
        expected_run_id=RUN_ID,
    )
    assert subject.preflight_result(
        child_evidence=evidence,
        cleanup_succeeded=True,
        bytecode_residue_absent=True,
    ) == subject.PREFLIGHT_PASS_TOKEN


@pytest.mark.parametrize(
    "outcomes",
    [
        ("UNSAFE", "SAFE", "SAFE", "SAFE", "SAFE"),
        ("AMBIGUOUS", "SAFE", "SAFE", "SAFE", "SAFE"),
        ("UNSUPPORTED", "SAFE", "SAFE", "SAFE", "SAFE"),
    ],
)
def test_publication_safety_blocked_result_round_trips_canonically(
    tmp_path: Path,
    outcomes: tuple[str, str, str, str, str],
) -> None:
    safety = _publication_safety_result(outcomes)
    writer = _writer(tmp_path)
    writer.append(
        subject.ObservationMilestone.PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED,
        {"publication_safety": safety},
    )
    writer.close()

    data = writer.path.read_bytes()
    records = subject.validate_journal_bytes(data, expected_run_id=RUN_ID)
    assert records[0].details == {"publication_safety": safety}
    assert data == _canonical(_record(
        milestone="PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED",
        details={"publication_safety": safety},
    )) + b"\n"


def test_publication_safety_blocked_result_rejects_safe_result(tmp_path: Path) -> None:
    writer = _writer(tmp_path)
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        writer.append(
            subject.ObservationMilestone.PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED,
            {"publication_safety": _publication_safety_result(("SAFE",) * 5)},
        )
    writer.close()


@pytest.mark.parametrize("version", [2, 3])
def test_publication_safety_supported_versions_are_retained(version: int) -> None:
    value = _publication_safety_result(schema_version=version)
    assert subject._validate_publication_safety_blocked_result(value)["schema_version"] == version


@pytest.mark.parametrize("version", [2, 3])
def test_profile_a_supported_versions_are_retained(version: int) -> None:
    value = _profile_a_blocked_diagnostics(schema_version=version)
    assert subject._validate_profile_a_blocked_diagnostics(value)["schema_version"] == version


def test_profile_a_v2_blocked_payload_remains_targetless_and_rejects_target() -> None:
    historical = _profile_a_blocked_diagnostics(schema_version=2)
    assert "target" not in subject._validate_profile_a_blocked_diagnostics(historical)

    targetful = copy.deepcopy(historical)
    targetful["target"] = {"baba_code": "21", "race_date": "2025-01-01", "race_no": 6}
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        subject._validate_profile_a_blocked_diagnostics(targetful)


def test_actual_profile_a_v3_blocked_canonical_payload_is_accepted_directly() -> None:
    target = raw_capture.NARRaceEntryStatusRaceIdentity("21", date(2025, 1, 1), 6)
    result = profile_a.diagnose_nar_race_entry_status_profile_a_v3(
        deba_table_bytes=b"<html><body></body></html>",
        target=target,
    )

    payload = result.to_canonical_dict()
    assert payload["overall_result"] == "BLOCKED"
    assert subject._validate_profile_a_blocked_diagnostics(payload) == payload


def test_profile_a_v3_blocked_payload_requires_target() -> None:
    value = _profile_a_blocked_diagnostics(schema_version=3)
    del value["target"]
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        subject._validate_profile_a_blocked_diagnostics(value)


@pytest.mark.parametrize(
    "target",
    [
        {"baba_code": "21", "race_date": "2025-01-01"},
        {"baba_code": "21", "race_date": "2025-01-01", "race_no": 6, "extra": 1},
        {"baba_code": "021", "race_date": "2025-01-01", "race_no": 6},
        {"baba_code": "21", "race_date": "2025-1-01", "race_no": 6},
        {"baba_code": "21", "race_date": "2025-02-30", "race_no": 6},
        {"baba_code": "21", "race_date": "2025-01-01", "race_no": True},
        {"baba_code": "21", "race_date": "2025-01-01", "race_no": 0},
        {"baba_code": "21", "race_date": "2025-01-01", "race_no": 13},
    ],
)
def test_profile_a_v3_blocked_payload_rejects_noncanonical_target(target: dict[str, object]) -> None:
    value = _profile_a_blocked_diagnostics(schema_version=3)
    value["target"] = target
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        subject._validate_profile_a_blocked_diagnostics(value)


@pytest.mark.parametrize("version", [1, 2])
def test_profile_b_supported_versions_are_retained(version: int) -> None:
    value = _profile_b_diagnostics(schema_version=version)
    assert subject._validate_profile_b_diagnostics(value)["schema_version"] == version


@pytest.mark.parametrize(
    ("validator", "value"),
    [
        (subject._validate_publication_safety_blocked_result, _publication_safety_result(schema_version=4)),
        (subject._validate_profile_a_blocked_diagnostics, _profile_a_blocked_diagnostics(schema_version=4)),
        (subject._validate_profile_b_diagnostics, _profile_b_diagnostics(schema_version=3)),
    ],
)
def test_nested_payload_unsupported_versions_are_rejected(validator: object, value: object) -> None:
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        validator(value)  # type: ignore[operator]


def test_phase69_new_nested_payload_records_fit_unchanged_limits() -> None:
    records = (
        _canonical(_record(
            milestone="PROFILE_B_DIAGNOSTICS_RETAINED",
            details={"profile_b_diagnostics": _profile_b_diagnostics(schema_version=2)},
        )) + b"\n",
        _canonical(_record(
            milestone="PROFILE_A_BLOCKED_DIAGNOSTICS_RETAINED",
            details={"profile_a_blocked_diagnostics": _profile_a_blocked_diagnostics(schema_version=3)},
        )) + b"\n",
        _canonical(_record(
            milestone="PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED",
            details={"publication_safety": _publication_safety_result(schema_version=3)},
        )) + b"\n",
    )
    assert max(map(len, records)) <= subject.MAX_RECORD_BYTES == 4096
    assert sum(map(len, records)) <= subject.MAX_JOURNAL_BYTES == 131072


@pytest.mark.parametrize(
    "mutation",
    [
        "wrong_type",
        "missing_field",
        "extra_field",
        "category_missing",
        "category_extra",
        "category_order",
        "category_identifier",
        "category_outcome",
        "aggregate",
        "safe_boolean",
        "negative_count",
        "oversized_count",
        "wrong_count_type",
        "raw_source",
        "secret_value",
        "url_query",
    ],
)
def test_publication_safety_blocked_result_rejects_invalid_or_unsafe_shape(
    tmp_path: Path,
    mutation: str,
) -> None:
    value: object = _publication_safety_result()
    if mutation == "wrong_type":
        value = []
    else:
        value = copy.deepcopy(value)
        assert type(value) is dict
        categories = value["category_results"]
        assert type(categories) is list
        if mutation == "missing_field":
            del value["result"]
        elif mutation == "extra_field":
            value["matched_text"] = "synthetic"
        elif mutation == "category_missing":
            categories.pop()
        elif mutation == "category_extra":
            categories.append(copy.deepcopy(categories[-1]))
        elif mutation == "category_order":
            categories[0], categories[1] = categories[1], categories[0]
        elif mutation == "category_identifier":
            categories[0]["identifier"] = "UNKNOWN"  # type: ignore[index]
        elif mutation == "category_outcome":
            categories[0]["outcome"] = "BLOCKED"  # type: ignore[index]
        elif mutation == "aggregate":
            value["result"] = "AMBIGUOUS"
        elif mutation == "safe_boolean":
            value["raw_fixture_publication_safe"] = True
        elif mutation == "negative_count":
            categories[0]["finding_count"] = -1  # type: ignore[index]
        elif mutation == "oversized_count":
            categories[0]["finding_count"] = 10001  # type: ignore[index]
        elif mutation == "wrong_count_type":
            categories[0]["finding_count"] = "1"  # type: ignore[index]
        elif mutation == "raw_source":
            categories[0]["raw_html"] = "<html>"  # type: ignore[index]
        elif mutation == "secret_value":
            categories[0]["token"] = "synthetic-secret"  # type: ignore[index]
        else:
            categories[0]["url"] = "https://invalid.example/?query=value"  # type: ignore[index]
    writer = _writer(tmp_path)
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        writer.append(
            subject.ObservationMilestone.PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED,
            {"publication_safety": value},
        )
    writer.close()


@pytest.mark.parametrize(
    "outcomes",
    [
        ("PASS", "PASS", "FAIL"),
        ("PASS", "PASS", "AMBIGUOUS"),
        ("PASS", "UNSUPPORTED", "UNSUPPORTED"),
    ],
)
def test_profile_a_blocked_diagnostics_round_trips_canonically(
    tmp_path: Path,
    outcomes: tuple[str, str, str],
) -> None:
    diagnostics = _profile_a_blocked_diagnostics(outcomes)
    writer = _writer(tmp_path)
    writer.append(
        subject.ObservationMilestone.PROFILE_A_BLOCKED_DIAGNOSTICS_RETAINED,
        {"profile_a_blocked_diagnostics": diagnostics},
    )
    writer.close()

    data = writer.path.read_bytes()
    records = subject.validate_journal_bytes(data, expected_run_id=RUN_ID)
    assert records[0].details == {"profile_a_blocked_diagnostics": diagnostics}
    assert diagnostics["predicate_results"][2]["safe_fields"]["selected_provider_horse_no"] is None  # type: ignore[index]
    assert data == _canonical(_record(
        milestone="PROFILE_A_BLOCKED_DIAGNOSTICS_RETAINED",
        details={"profile_a_blocked_diagnostics": diagnostics},
    )) + b"\n"


def test_profile_a_blocked_diagnostics_rejects_qualified_result(tmp_path: Path) -> None:
    diagnostics = _profile_a_blocked_diagnostics()
    diagnostics["overall_result"] = "QUALIFIED"
    diagnostics["terminal_semantic"] = "ENTRY_LISTING_PRESENT"
    diagnostics["first_nonpass_predicate"] = None
    diagnostics["terminal_reason"] = "QUALIFIED"
    for result in diagnostics["predicate_results"]:  # type: ignore[union-attr]
        result["outcome"] = "PASS"
    writer = _writer(tmp_path)
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        writer.append(
            subject.ObservationMilestone.PROFILE_A_BLOCKED_DIAGNOSTICS_RETAINED,
            {"profile_a_blocked_diagnostics": diagnostics},
        )
    writer.close()


@pytest.mark.parametrize(
    "mutation",
    [
        "wrong_type",
        "missing_field",
        "extra_field",
        "missing_predicate",
        "extra_predicate",
        "predicate_order",
        "predicate_identifier",
        "predicate_outcome",
        "wrong_safe_fields",
        "negative_count",
        "oversized_count",
        "wrong_count_type",
        "numeric_selected_horse",
        "first_failure",
        "terminal_reason",
        "terminal_semantic",
        "raw_source",
        "url_query",
    ],
)
def test_profile_a_blocked_diagnostics_rejects_invalid_or_unsafe_shape(
    tmp_path: Path,
    mutation: str,
) -> None:
    value: object = _profile_a_blocked_diagnostics()
    if mutation == "wrong_type":
        value = []
    else:
        value = copy.deepcopy(value)
        assert type(value) is dict
        predicates = value["predicate_results"]
        assert type(predicates) is list
        if mutation == "missing_field":
            del value["profile"]
        elif mutation == "extra_field":
            value["source_text"] = "synthetic"
        elif mutation == "missing_predicate":
            predicates.pop()
        elif mutation == "extra_predicate":
            predicates.append(copy.deepcopy(predicates[-1]))
        elif mutation == "predicate_order":
            predicates[0], predicates[1] = predicates[1], predicates[0]
        elif mutation == "predicate_identifier":
            predicates[0]["identifier"] = "UNKNOWN"  # type: ignore[index]
        elif mutation == "predicate_outcome":
            predicates[2]["outcome"] = "BLOCKED"  # type: ignore[index]
        elif mutation == "wrong_safe_fields":
            predicates[0]["safe_fields"] = {"ordinary_row_count": 1}  # type: ignore[index]
        elif mutation == "negative_count":
            predicates[0]["safe_fields"]["entry_table_scope_count"] = -1  # type: ignore[index]
        elif mutation == "oversized_count":
            predicates[0]["safe_fields"]["entry_table_scope_count"] = 10001  # type: ignore[index]
        elif mutation == "wrong_count_type":
            predicates[0]["safe_fields"]["entry_table_scope_count"] = "1"  # type: ignore[index]
        elif mutation == "numeric_selected_horse":
            predicates[2]["safe_fields"]["selected_provider_horse_no"] = 3  # type: ignore[index]
        elif mutation == "first_failure":
            value["first_nonpass_predicate"] = "ENTRY_TABLE_SCOPE"
        elif mutation == "terminal_reason":
            value["terminal_reason"] = "UNSUPPORTED_INPUT"
        elif mutation == "terminal_semantic":
            value["terminal_semantic"] = "ENTRY_LISTING_PRESENT"
        elif mutation == "raw_source":
            predicates[0]["safe_fields"]["raw_html"] = "<html>"  # type: ignore[index]
        else:
            predicates[0]["safe_fields"]["url"] = "https://invalid.example/?query=value"  # type: ignore[index]
    writer = _writer(tmp_path)
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        writer.append(
            subject.ObservationMilestone.PROFILE_A_BLOCKED_DIAGNOSTICS_RETAINED,
            {"profile_a_blocked_diagnostics": value},
        )
    writer.close()


def test_blocked_retention_complete_records_fit_approved_bounds() -> None:
    safety = _publication_safety_result(("UNSUPPORTED",) * 5, finding_count=10000)
    profile_a = _profile_a_blocked_diagnostics(("UNSUPPORTED",) * 3, count=10000)
    safety_record = _canonical(_record(
        131072,
        milestone="PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED",
        details={"publication_safety": safety},
    )) + b"\n"
    profile_a_record = _canonical(_record(
        131072,
        milestone="PROFILE_A_BLOCKED_DIAGNOSTICS_RETAINED",
        details={"profile_a_blocked_diagnostics": profile_a},
    )) + b"\n"

    assert len(safety_record) == 847 <= subject.MAX_RECORD_BYTES
    assert len(profile_a_record) == 883 <= subject.MAX_RECORD_BYTES


def test_safety_blocked_path_is_durable_terminal_failure_evidence(tmp_path: Path) -> None:
    writer = _writer(tmp_path)
    _append_through_identity_verification(writer)
    writer.append(
        subject.ObservationMilestone.PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED,
        {"publication_safety": _publication_safety_result()},
    )
    writer.append(
        subject.ObservationMilestone.LIVE_PROCESS_COMPLETE,
        {"outcome": "SOURCE_PROFILE_FIXTURE_BLOCKED", "authorization_state": "CONSUMED_CONFIRMED"},
    )
    writer.close()
    subject.validate_journal_semantics(subject.validate_journal_bytes(writer.path.read_bytes()))


def test_profile_a_blocked_path_is_durable_terminal_failure_evidence(tmp_path: Path) -> None:
    writer = _writer(tmp_path)
    _append_through_identity_verification(writer)
    writer.append(subject.ObservationMilestone.SAFETY_PASS, {})
    writer.append(
        subject.ObservationMilestone.PROFILE_A_BLOCKED_DIAGNOSTICS_RETAINED,
        {"profile_a_blocked_diagnostics": _profile_a_blocked_diagnostics()},
    )
    writer.append(
        subject.ObservationMilestone.LIVE_PROCESS_COMPLETE,
        {"outcome": "SOURCE_PROFILE_FIXTURE_BLOCKED", "authorization_state": "CONSUMED_CONFIRMED"},
    )
    writer.close()
    subject.validate_journal_semantics(subject.validate_journal_bytes(writer.path.read_bytes()))


def test_profile_a_v3_blocked_target_matches_constructed_target(tmp_path: Path) -> None:
    writer = _writer(tmp_path)
    _append_through_identity_verification(writer)
    writer.append(subject.ObservationMilestone.SAFETY_PASS, {})
    writer.append(
        subject.ObservationMilestone.PROFILE_A_BLOCKED_DIAGNOSTICS_RETAINED,
        {"profile_a_blocked_diagnostics": _profile_a_blocked_diagnostics(schema_version=3)},
    )
    writer.append(
        subject.ObservationMilestone.LIVE_PROCESS_COMPLETE,
        {"outcome": "SOURCE_PROFILE_FIXTURE_BLOCKED", "authorization_state": "CONSUMED_CONFIRMED"},
    )
    writer.close()

    journal_bytes = writer.path.read_bytes()
    assert max(len(line) for line in journal_bytes.splitlines(keepends=True)) <= subject.MAX_RECORD_BYTES == 4096
    assert len(journal_bytes) <= subject.MAX_JOURNAL_BYTES == 131072
    records = subject.validate_journal_bytes(journal_bytes)
    subject.validate_journal_semantics(records)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("baba_code", "22"),
        ("race_date", "2025-01-02"),
        ("race_no", 7),
    ],
)
def test_profile_a_v3_blocked_target_mismatch_fails_semantics(
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    writer = _writer(tmp_path)
    _append_through_identity_verification(writer)
    writer.append(subject.ObservationMilestone.SAFETY_PASS, {})
    payload = _profile_a_blocked_diagnostics(schema_version=3)
    payload["target"][field] = value  # type: ignore[index]
    writer.append(
        subject.ObservationMilestone.PROFILE_A_BLOCKED_DIAGNOSTICS_RETAINED,
        {"profile_a_blocked_diagnostics": payload},
    )
    writer.append(
        subject.ObservationMilestone.LIVE_PROCESS_COMPLETE,
        {"outcome": "SOURCE_PROFILE_FIXTURE_BLOCKED", "authorization_state": "CONSUMED_CONFIRMED"},
    )
    writer.close()

    records = subject.validate_journal_bytes(writer.path.read_bytes())
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        subject.validate_journal_semantics(records)


@pytest.mark.parametrize(
    ("blocked", "later"),
    [
        (
            subject.ObservationMilestone.PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED,
            subject.ObservationMilestone.SAFETY_PASS,
        ),
        (
            subject.ObservationMilestone.PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED,
            subject.ObservationMilestone.PROFILE_A_QUALIFIED,
        ),
        (
            subject.ObservationMilestone.PROFILE_A_BLOCKED_DIAGNOSTICS_RETAINED,
            subject.ObservationMilestone.PROFILE_A_QUALIFIED,
        ),
        (
            subject.ObservationMilestone.PROFILE_A_BLOCKED_DIAGNOSTICS_RETAINED,
            subject.ObservationMilestone.PROFILE_B_DIAGNOSTICS_RETAINED,
        ),
        (
            subject.ObservationMilestone.PROFILE_A_BLOCKED_DIAGNOSTICS_RETAINED,
            subject.ObservationMilestone.PUBLICATION_BEGIN,
        ),
    ],
)
def test_blocked_retention_rejects_contradictory_success_progression(
    tmp_path: Path,
    blocked: subject.ObservationMilestone,
    later: subject.ObservationMilestone,
) -> None:
    writer = _writer(tmp_path)
    _append_through_identity_verification(writer)
    if blocked is subject.ObservationMilestone.PROFILE_A_BLOCKED_DIAGNOSTICS_RETAINED:
        writer.append(subject.ObservationMilestone.SAFETY_PASS, {})
    writer.append(blocked, _details_for(blocked))
    writer.append(later, _details_for(later))
    writer.close()
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        records = subject.validate_journal_bytes(writer.path.read_bytes())
        subject.validate_journal_semantics(records)


def test_normal_success_path_remains_valid_without_blocked_events(tmp_path: Path) -> None:
    writer = _writer(tmp_path)
    blocked = {
        subject.ObservationMilestone.PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED,
        subject.ObservationMilestone.PROFILE_A_BLOCKED_DIAGNOSTICS_RETAINED,
    }
    for milestone in subject.ObservationMilestone:
        if milestone not in blocked:
            writer.append(milestone, _details_for(milestone))
    writer.close()
    records = subject.validate_journal_bytes(writer.path.read_bytes())
    subject.validate_journal_semantics(records)
    seen = {record.milestone for record in records}
    assert subject.ObservationMilestone.SAFETY_PASS in seen
    assert subject.ObservationMilestone.PROFILE_A_QUALIFIED in seen
    assert subject.PREFLIGHT_PASS_TOKEN == "NAR_REACQUISITION_OBSERVABILITY_PREFLIGHT_PASS"


def test_phase58_additions_are_closed_no_network_evidence_validators() -> None:
    source = Path(subject.__file__).read_text(encoding="utf-8")
    assert "nar_race_entry_status_source_profile_profile_a" not in source
    assert "nar_race_entry_status_source_profile_publication_contract" not in source
    assert subject.JOURNAL_SCHEMA_VERSION == 1


@pytest.mark.parametrize("milestone", [
    subject.ObservationMilestone.PROFILE_B_RECOVERY_DIAGNOSTICS_RETAINED,
    subject.ObservationMilestone.PUBLICATION_SAFETY_RECOVERY_DIAGNOSTICS_RETAINED,
])
def test_recovery_records_roundtrip_with_exact_detail_keys(tmp_path: Path, milestone: subject.ObservationMilestone) -> None:
    details = _details_for(milestone)
    writer = _writer(tmp_path)
    writer.append(milestone, details)
    writer.close()
    records = subject.validate_journal_bytes(writer.path.read_bytes(), expected_run_id=RUN_ID)
    assert records[0].details == details
    assert subject._DETAIL_KEYS[milestone] == frozenset(details)


@pytest.mark.parametrize("milestone", [
    subject.ObservationMilestone.PROFILE_B_RECOVERY_DIAGNOSTICS_RETAINED,
    subject.ObservationMilestone.PUBLICATION_SAFETY_RECOVERY_DIAGNOSTICS_RETAINED,
])
@pytest.mark.parametrize("mutation", ["missing", "extra", "schema", "version", "version_two", "raw", "nested_type"])
def test_recovery_records_reject_detail_and_schema_mutations(milestone: subject.ObservationMilestone, mutation: str) -> None:
    details = _details_for(milestone)
    key = next(iter(details))
    if mutation == "missing":
        details = {}
    elif mutation == "extra":
        details["extra"] = 1
    elif mutation == "schema":
        details[key]["schema"] = "wrong"
    elif mutation == "version":
        details[key]["schema_version"] = True
    elif mutation == "version_two":
        details[key]["schema_version"] = 2
    elif mutation == "raw":
        details[key]["raw_html"] = "<synthetic>"
    else:
        details[key] = b"raw"
    data = _canonical(_record(milestone=milestone.value, details=details)) + b"\n" if mutation != "nested_type" else None
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        if data is not None:
            subject.validate_journal_bytes(data)
        else:
            subject._record_payload(run_id=RUN_ID, sequence=1, milestone=milestone, occurred_at="2026-09-14T00:00:00.000000Z", details=details)


@pytest.mark.parametrize("mutation", ["state", "role_order", "missing_role", "extra_field", "stage_type"])
def test_safety_recovery_nested_validation_is_independent(mutation: str) -> None:
    payload = _safety_recovery_diagnostics()
    results = payload["document_results"]
    if mutation == "state":
        results[0]["strict_structure"] = "PASS"
    elif mutation == "role_order":
        results.reverse()
    elif mutation == "missing_role":
        results.pop()
    elif mutation == "extra_field":
        results[0]["text"] = "private"
    else:
        results[0]["utf8_decode"] = 1
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        subject._validate_publication_safety_recovery_diagnostics(payload)


@pytest.mark.parametrize("mutation", [
    "cardinality", "nine_details", "incomplete_details", "overflow_complete", "ordinal",
    "equal", "match_boolean", "count_type", "count_bound", "extra_candidate_field",
    "target_extra", "target_date", "target_type", "complete_type",
])
def test_profile_b_recovery_nested_validation_is_independent(mutation: str) -> None:
    payload = _profile_b_recovery_diagnostics()
    results = payload["candidate_results"]
    if mutation == "cardinality":
        payload["target_candidate_count"] = 2
    elif mutation == "nine_details":
        payload = _profile_b_recovery_diagnostics(8)
        payload["candidate_results"].append(copy.deepcopy(payload["candidate_results"][-1]))
        payload["target_candidate_count"] = 9
    elif mutation == "incomplete_details":
        payload["candidate_details_complete"] = False
    elif mutation == "overflow_complete":
        payload = _profile_b_recovery_diagnostics(9)
        payload["candidate_details_complete"] = True
    elif mutation == "ordinal":
        results[0]["candidate_ordinal"] = 2
    elif mutation == "equal":
        payload["all_candidate_safe_projections_equal"] = False
    elif mutation == "match_boolean":
        results[0]["canonical_target_query_match"] = False
    elif mutation == "count_type":
        results[0]["anchor_count"] = True
    elif mutation == "count_bound":
        results[0]["anchor_count"] = 10001
    elif mutation == "extra_candidate_field":
        results[0]["href"] = "private"
    elif mutation == "target_extra":
        payload["target"]["provider_text"] = "private"
    elif mutation == "target_date":
        payload["target"]["race_date"] = "2025-02-30"
    elif mutation == "target_type":
        payload["target"]["race_no"] = True
    else:
        payload["candidate_details_complete"] = 1
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        subject._validate_profile_b_recovery_diagnostics(payload)


@pytest.mark.parametrize("count", [0, 1, 2, 8, 9])
def test_recovery_candidate_cardinality_and_overflow_are_valid(count: int) -> None:
    payload = _profile_b_recovery_diagnostics(count)
    assert subject._validate_profile_b_recovery_diagnostics(payload) == payload


def test_recovery_milestone_order_and_historical_phase57_shape(tmp_path: Path) -> None:
    recovery = {
        subject.ObservationMilestone.PROFILE_B_RECOVERY_DIAGNOSTICS_RETAINED,
        subject.ObservationMilestone.PUBLICATION_SAFETY_RECOVERY_DIAGNOSTICS_RETAINED,
        subject.ObservationMilestone.PROFILE_B_CANDIDATE_ANCESTRY_RECOVERY_DIAGNOSTICS_RETAINED,
        subject.ObservationMilestone.STRICT_STRUCTURE_RECOVERY_DIAGNOSTICS_RETAINED,
    }
    old = tuple(m for m in subject.ObservationMilestone if m not in recovery)
    historical = tuple(m for m in old if subject._MILESTONE_ORDER[m] <= subject._MILESTONE_ORDER[subject.ObservationMilestone.PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED]) + (
        subject.ObservationMilestone.LIVE_PROCESS_COMPLETE,
        subject.ObservationMilestone.PARENT_EVIDENCE_VALIDATION_PASS,
        subject.ObservationMilestone.PARENT_CLEANUP_COMPLETE,
    )
    assert len(historical) == 22
    writer = _writer(tmp_path)
    for milestone in historical:
        details = _details_for(milestone)
        if milestone is subject.ObservationMilestone.PROFILE_B_DIAGNOSTICS_RETAINED:
            normal = details["profile_b_diagnostics"]
            normal["overall_result"] = "BLOCKED"
            normal["first_nonpass_predicate"] = "UNIQUE_TARGET_6R"
            normal["terminal_reason"] = "UNSUPPORTED_INPUT"
            normal["predicate_results"][1]["outcome"] = "AMBIGUOUS"
            normal["predicate_results"][1]["safe_fields"]["target_6r_row_count"] = 2
            for index in (2, 3):
                normal["predicate_results"][index]["outcome"] = "UNSUPPORTED"
                for key, value in normal["predicate_results"][index]["safe_fields"].items():
                    normal["predicate_results"][index]["safe_fields"][key] = False if type(value) is bool else 0
        elif milestone is subject.ObservationMilestone.PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED:
            details = {"publication_safety": _publication_safety_result(("UNSUPPORTED",) * 5)}
        elif milestone is subject.ObservationMilestone.LIVE_PROCESS_COMPLETE:
            details["outcome"] = "SOURCE_PROFILE_FIXTURE_BLOCKED"
        writer.append(milestone, details)
    writer.close()
    records = subject.validate_journal_bytes(writer.path.read_bytes())
    execution = subject.reconstruct_execution(records)
    assert execution.authorization_state == "CONSUMED_CONFIRMED"
    assert execution.last_milestone is subject.ObservationMilestone.PARENT_CLEANUP_COMPLETE
    assert not execution.publication_began
    assert not recovery.intersection(r.milestone for r in records)


def test_recovery_valid_chronology_and_out_of_order_rejected(tmp_path: Path) -> None:
    writer = _writer(tmp_path)
    for milestone in subject.ObservationMilestone:
        writer.append(milestone, _details_for(milestone))
        if milestone is subject.ObservationMilestone.PUBLICATION_SAFETY_RECOVERY_DIAGNOSTICS_RETAINED:
            break
    writer.close()
    records = subject.validate_journal_bytes(writer.path.read_bytes())
    subject.validate_journal_semantics(records)
    wrong = records[:-2] + (records[-1], records[-2])
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        subject.validate_journal_semantics(wrong)
    assert [r.milestone for r in records[-6:]] == [
        subject.ObservationMilestone.RACELIST_CAPTURE_METADATA_RETAINED,
        subject.ObservationMilestone.PROFILE_B_DIAGNOSTICS_RETAINED,
        subject.ObservationMilestone.PROFILE_B_RECOVERY_DIAGNOSTICS_RETAINED,
        subject.ObservationMilestone.PROFILE_B_CANDIDATE_ANCESTRY_RECOVERY_DIAGNOSTICS_RETAINED,
        subject.ObservationMilestone.IDENTITY_VERIFICATION_PASS,
        subject.ObservationMilestone.PUBLICATION_SAFETY_RECOVERY_DIAGNOSTICS_RETAINED,
    ]


def test_recovery_worst_case_records_fit_unchanged_limits() -> None:
    profile_b = _profile_b_recovery_diagnostics(8, maximal=True)
    profile_b["target"] = {"baba_code": "9" * 512, "race_date": "9999-12-31", "race_no": 10000}
    subject._validate_profile_b_recovery_diagnostics(profile_b)
    safety = _safety_recovery_diagnostics()
    subject._validate_publication_safety_recovery_diagnostics(safety)
    for milestone, key, payload in [
        (subject.ObservationMilestone.PROFILE_B_RECOVERY_DIAGNOSTICS_RETAINED, "profile_b_recovery_diagnostics", profile_b),
        (subject.ObservationMilestone.PUBLICATION_SAFETY_RECOVERY_DIAGNOSTICS_RETAINED, "publication_safety_recovery_diagnostics", safety),
    ]:
        record = _canonical(_record(131072, milestone=milestone.value, details={key: payload})) + b"\n"
        expected_size = 3177 if key == "profile_b_recovery_diagnostics" else 677
        assert len(record) == expected_size <= subject.MAX_RECORD_BYTES == 4096
    oversized = _canonical(_record(10**3000, milestone=subject.ObservationMilestone.PROFILE_B_RECOVERY_DIAGNOSTICS_RETAINED.value, details={"profile_b_recovery_diagnostics": profile_b})) + b"\n"
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        subject.validate_journal_bytes(oversized)


@pytest.mark.parametrize("decode", ["PASS", "FAIL", "NOT_REACHED"])
@pytest.mark.parametrize("structure", ["PASS", "FAIL", "NOT_REACHED"])
@pytest.mark.parametrize("parse", ["PASS", "FAIL", "NOT_REACHED"])
def test_phase50_safety_recovery_all_stage_combinations(decode: str, structure: str, parse: str) -> None:
    payload = _safety_recovery_diagnostics()
    payload["document_results"][0].update(utf8_decode=decode, strict_structure=structure, beautifulsoup_parse=parse)
    valid = {("FAIL", "NOT_REACHED", "NOT_REACHED"), ("PASS", "FAIL", "NOT_REACHED"), ("PASS", "PASS", "PASS"), ("PASS", "PASS", "FAIL")}
    if (decode, structure, parse) in valid:
        assert subject._validate_publication_safety_recovery_diagnostics(payload) == payload
    else:
        with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
            subject._validate_publication_safety_recovery_diagnostics(payload)


@pytest.mark.parametrize("family", ["strict", "ancestry"])
def test_phase66_exact_event_details_and_payload_round_trip(family: str) -> None:
    milestone = (subject.ObservationMilestone.STRICT_STRUCTURE_RECOVERY_DIAGNOSTICS_RETAINED
                 if family == "strict" else subject.ObservationMilestone.PROFILE_B_CANDIDATE_ANCESTRY_RECOVERY_DIAGNOSTICS_RETAINED)
    details = _details_for(milestone)
    record = _canonical(_record(milestone=milestone.value, details=details)) + b"\n"
    assert dict(subject.validate_journal_bytes(record)[0].details) == details
    for wrong in ({}, {**details, "extra": 1}, {"unrelated": next(iter(details.values()))}):
        with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
            subject.validate_journal_bytes(_canonical(_record(milestone=milestone.value, details=wrong)) + b"\n")


@pytest.mark.parametrize("where,key,value", [
    ("top", "schema", "wrong"), ("top", "schema_version", 2),
    ("top", "schema_version", True), ("top", "extra", "provider text"),
    ("role", "document_role", "race_list"), ("role", "failure_kind", "FAIL"),
    ("role", "event_index", -1), ("role", "event_index", 10001),
    ("role", "event_index", True), ("role", "stack_depth", -1),
    ("role", "stack_depth", 10001), ("role", "stack_depth", False),
    ("role", "expected_open_tag", "custom-provider-tag"),
    ("role", "observed_end_tag", "div"), ("role", "tolerant_parse", "NOT_RUN"),
    ("role", "expected_open_tag", None), ("role", "stack_depth", 0),
    ("role", "event_index", 0), ("role", "extra", "provider text"),
])
def test_phase66_strict_nested_validation_rejects(where: str, key: str, value: object) -> None:
    payload = _strict_structure_recovery_diagnostics()
    (payload if where == "top" else payload["document_results"][0])[key] = value
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        subject._validate_strict_structure_recovery_diagnostics(payload)


@pytest.mark.parametrize("kind,index,depth,expected,observed", [
    ("PASS", 0, 0, None, None),
    ("END_TAG_EMPTY_STACK", 1, 0, None, "DIV"),
    ("END_TAG_MISMATCH", 2, 1, "OTHER_OR_CUSTOM", "OTHER_OR_CUSTOM"),
    ("UNCLOSED_STACK_AT_CLOSE", 1, 1, "DIV", None),
])
def test_phase66_strict_independent_state_machine(kind, index, depth, expected, observed) -> None:
    payload = _strict_structure_recovery_diagnostics()
    role = payload["document_results"][0]
    role.update(failure_kind=kind, event_index=index, stack_depth=depth,
                expected_open_tag=expected, observed_end_tag=observed)
    assert subject._validate_strict_structure_recovery_diagnostics(payload) == payload
    role["observed_end_tag"] = "DIV" if observed is None else None
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        subject._validate_strict_structure_recovery_diagnostics(payload)


@pytest.mark.parametrize("where,key,value", [
    ("top", "schema", "wrong"), ("top", "schema_version", 2),
    ("top", "schema_version", True), ("top", "extra", "raw class"),
    ("top", "target_candidate_count", 2), ("top", "race_table_scope_count", 0),
    ("top", "race_table_scope_count", 10001), ("top", "target_candidate_count", True),
    ("top", "candidate_details_complete", False), ("top", "candidate_details_complete", 1),
    ("candidate", "candidate_ordinal", 2), ("candidate", "candidate_ordinal", True),
    ("candidate", "nearest_table_role", "provider-class"),
    ("candidate", "nested_table_depth_within_race_scope", -1),
    ("candidate", "nested_table_depth_within_race_scope", 10001),
    ("candidate", "nested_table_depth_within_race_scope", True),
    ("candidate", "nested_table_depth_within_race_scope", 0),
    ("candidate", "inside_change_info_table", False),
    ("candidate", "inside_change_info_table", 1),
    ("candidate", "direct_schedule_table_descendant", True),
    ("candidate", "direct_schedule_table_descendant", 0),
    ("candidate", "extra", "provider-class"),
])
def test_phase66_ancestry_nested_validation_rejects(where: str, key: str, value: object) -> None:
    payload = _candidate_ancestry_recovery_diagnostics()
    (payload if where == "top" else payload["candidate_results"][0])[key] = value
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        subject._validate_profile_b_candidate_ancestry_recovery_diagnostics(payload)


@pytest.mark.parametrize("role,depth,inside,direct", [
    ("NO_TABLE", 0, False, False), ("RACE_SCHEDULE_TABLE", 1, False, True),
    ("CHANGE_INFO_TABLE", 1, True, False), ("OTHER_TABLE", 2, False, False),
    ("OTHER_TABLE", 2, True, False),
])
def test_phase66_ancestry_independent_invariants(role, depth, inside, direct) -> None:
    payload = _candidate_ancestry_recovery_diagnostics()
    payload["candidate_results"][0].update(nearest_table_role=role,
        nested_table_depth_within_race_scope=depth, inside_change_info_table=inside,
        direct_schedule_table_descendant=direct)
    assert subject._validate_profile_b_candidate_ancestry_recovery_diagnostics(payload) == payload
    payload["candidate_results"][0]["direct_schedule_table_descendant"] = not direct
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        subject._validate_profile_b_candidate_ancestry_recovery_diagnostics(payload)


def test_phase66_ancestry_bounds_cardinality_scope_and_target() -> None:
    for count in (0, 8, 9, 10000):
        payload = _candidate_ancestry_recovery_diagnostics(count)
        assert subject._validate_profile_b_candidate_ancestry_recovery_diagnostics(payload) == payload
    overflow = _candidate_ancestry_recovery_diagnostics(9)
    overflow["candidate_results"] = _candidate_ancestry_recovery_diagnostics(8)["candidate_results"] + [_candidate_ancestry_recovery_diagnostics()["candidate_results"][0]]
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        subject._validate_profile_b_candidate_ancestry_recovery_diagnostics(overflow)
    for scope in (0, 2):
        payload = _candidate_ancestry_recovery_diagnostics(0)
        payload.update(race_table_scope_count=scope, candidate_details_complete=False)
        assert subject._validate_profile_b_candidate_ancestry_recovery_diagnostics(payload) == payload
    for target in ({"baba_code": "21", "race_date": "2025-1-1", "race_no": 6},
                   {"baba_code": "21", "race_date": "2025-01-01", "race_no": True},
                   {"baba_code": "21", "race_date": "2025-01-01", "race_no": 6, "raw": "text"}):
        payload = _candidate_ancestry_recovery_diagnostics()
        payload["target"] = target
        with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
            subject._validate_profile_b_candidate_ancestry_recovery_diagnostics(payload)


def _phase66_records(tmp_path: Path, *, historical: bool = False):
    writer = _writer(tmp_path)
    new = {subject.ObservationMilestone.PROFILE_B_CANDIDATE_ANCESTRY_RECOVERY_DIAGNOSTICS_RETAINED,
           subject.ObservationMilestone.STRICT_STRUCTURE_RECOVERY_DIAGNOSTICS_RETAINED}
    for milestone in subject.ObservationMilestone:
        if historical and milestone in new:
            continue
        writer.append(milestone, _details_for(milestone))
        if milestone is subject.ObservationMilestone.PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED:
            break
    writer.append(subject.ObservationMilestone.LIVE_PROCESS_COMPLETE,
                  {"outcome": "SOURCE_PROFILE_FIXTURE_BLOCKED", "authorization_state": "CONSUMED_FAIL_CLOSED"})
    writer.append(subject.ObservationMilestone.PARENT_EVIDENCE_VALIDATION_PASS, {"journal_sha256": "0" * 64})
    writer.append(subject.ObservationMilestone.PARENT_CLEANUP_COMPLETE, {})
    writer.close()
    return subject.validate_journal_bytes(writer.path.read_bytes())


def test_phase66_valid_order_and_phase64_historical_24_record_shape(tmp_path: Path) -> None:
    records = _phase66_records(tmp_path)
    subject.validate_journal_semantics(records)
    assert len(records) == 26
    historical_path = tmp_path / "historical"
    historical_path.mkdir()
    historical = _phase66_records(historical_path, historical=True)
    subject.validate_journal_semantics(historical)
    assert len(historical) == 24
    assert not subject.reconstruct_execution(historical).publication_began
    # Synthetic milestone-shape regression, not a claim to read external safe-final bytes.
    assert subject.JOURNAL_SCHEMA_VERSION == 1
    assert subject._ALLOWED_OUTCOMES == frozenset({"READY_FOR_REVIEW", "SOURCE_PROFILE_FIXTURE_BLOCKED",
        "RECOVERY_PREFLIGHT_BLOCKED", "SYNTHETIC_SUCCESS", "SYNTHETIC_FAILURE"})


@pytest.mark.parametrize("move,reference,before", [
    ("PROFILE_B_CANDIDATE_ANCESTRY_RECOVERY_DIAGNOSTICS_RETAINED", "PROFILE_B_RECOVERY_DIAGNOSTICS_RETAINED", True),
    ("PROFILE_B_CANDIDATE_ANCESTRY_RECOVERY_DIAGNOSTICS_RETAINED", "IDENTITY_VERIFICATION_PASS", False),
    ("STRICT_STRUCTURE_RECOVERY_DIAGNOSTICS_RETAINED", "PUBLICATION_SAFETY_RECOVERY_DIAGNOSTICS_RETAINED", True),
    ("STRICT_STRUCTURE_RECOVERY_DIAGNOSTICS_RETAINED", "PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED", False),
])
def test_phase66_milestone_order_violations(tmp_path: Path, move, reference, before) -> None:
    records = list(_phase66_records(tmp_path))
    moved = next(r for r in records if r.milestone.value == move)
    records.remove(moved)
    index = next(i for i, r in enumerate(records) if r.milestone.value == reference)
    records.insert(index if before else index + 1, moved)
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        subject.validate_journal_semantics(tuple(records))


@pytest.mark.parametrize("event,prerequisite", [
    ("PROFILE_B_CANDIDATE_ANCESTRY_RECOVERY_DIAGNOSTICS_RETAINED", "PROFILE_B_RECOVERY_DIAGNOSTICS_RETAINED"),
    ("STRICT_STRUCTURE_RECOVERY_DIAGNOSTICS_RETAINED", "PUBLICATION_SAFETY_RECOVERY_DIAGNOSTICS_RETAINED"),
])
def test_phase66_required_supplemental_predecessor(tmp_path: Path, event, prerequisite) -> None:
    records = _phase66_records(tmp_path)
    assert any(r.milestone.value == event for r in records)
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        subject.validate_journal_semantics(tuple(r for r in records if r.milestone.value != prerequisite))


def test_phase66_maximum_valid_canonical_records(tmp_path: Path) -> None:
    strict = _strict_structure_recovery_diagnostics()
    for role in strict["document_results"]:
        role["failure_kind"] = "UNCLOSED_STACK_AT_CLOSE"
        role["observed_end_tag"] = None
    # Compare every valid maximum-metadata state: mismatch may encode longer tags.
    strict_variants = [strict, _strict_structure_recovery_diagnostics()]
    ancestry = _candidate_ancestry_recovery_diagnostics(8)
    ancestry["target"] = {"baba_code": "9" * 512, "race_date": "9999-12-31", "race_no": 10000}
    measured = []
    for milestone, key, variants, validator in [
        (subject.ObservationMilestone.STRICT_STRUCTURE_RECOVERY_DIAGNOSTICS_RETAINED,
         "strict_structure_recovery_diagnostics", strict_variants, subject._validate_strict_structure_recovery_diagnostics),
        (subject.ObservationMilestone.PROFILE_B_CANDIDATE_ANCESTRY_RECOVERY_DIAGNOSTICS_RETAINED,
         "profile_b_candidate_ancestry_recovery_diagnostics", [ancestry], subject._validate_profile_b_candidate_ancestry_recovery_diagnostics),
    ]:
        sizes = []
        for payload in variants:
            validator(payload)
            encoded = _canonical(_record(131072, milestone=milestone.value, details={key: payload})) + b"\n"
            # A standalone journal starts at 1; measure with the established
            # conservative six-digit envelope as in the Phase63 size regression.
            standalone = _canonical(_record(milestone=milestone.value, details={key: payload})) + b"\n"
            subject.validate_journal_bytes(standalone)
            external = tmp_path / f"{key}-{len(sizes)}"
            external.mkdir()
            writer = _writer(external)
            writer.append(milestone, {key: payload})
            writer.close()
            assert writer.path.read_bytes() == standalone
            sizes.append(len(encoded))
        measured.append(max(sizes))
    assert all(size <= subject.MAX_RECORD_BYTES == 4096 for size in measured)
    assert measured == [837, 2598]
    print("Phase66 maximum canonical JSONL bytes including LF:", measured)


@pytest.mark.parametrize("family", ["strict", "ancestry"])
def test_phase66_cross_event_evidence_contradictions(tmp_path: Path, family: str) -> None:
    records = _phase66_records(tmp_path)
    # Alter an individually valid payload, retaining the original sequence/order.
    encoded = [json.loads(_canonical(_record(r.sequence, milestone=r.milestone.value,
                                             details=dict(r.details)))) for r in records]
    if family == "strict":
        payload = next(r for r in encoded if r["milestone"] == "PUBLICATION_SAFETY_RECOVERY_DIAGNOSTICS_RETAINED")
        payload["details"]["publication_safety_recovery_diagnostics"]["document_results"][0].update(
            utf8_decode="FAIL", strict_structure="NOT_REACHED")
    else:
        payload = next(r for r in encoded if r["milestone"] == "PROFILE_B_CANDIDATE_ANCESTRY_RECOVERY_DIAGNOSTICS_RETAINED")
        payload["details"]["profile_b_candidate_ancestry_recovery_diagnostics"]["target"]["race_no"] = 7
    validated = subject.validate_journal_bytes(b"".join(_canonical(r) + b"\n" for r in encoded))
    with pytest.raises(subject.NARReacquisitionObservabilityValidationError):
        subject.validate_journal_semantics(validated)
