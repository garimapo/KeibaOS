from __future__ import annotations

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


RUN_ID = "0123456789abcdef0123456789abcdef"
UTC = timezone.utc
REQUEST_ID = "nar-race-entry-status-request-v1:" + "a" * 64
BUNDLE_ID = "nar-race-entry-status-raw-bundle-v1:" + "b" * 64
CAPTURE_ID = "nar-race-entry-status-capture-v1:" + "9" * 64


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


def _profile_b_diagnostics() -> dict[str, object]:
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
        "schema_version": 1,
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
        subject.ObservationMilestone.IDENTITY_VERIFICATION_PASS: {"bundle_id": BUNDLE_ID},
        subject.ObservationMilestone.PUBLICATION_BEGIN: {"planned_path_count": 7},
        subject.ObservationMilestone.RAW_FIXTURES_WRITTEN: {"document_count": 2},
        subject.ObservationMilestone.MANIFEST_WRITTEN: {
            "fixture_set_identity": "nar-race-entry-status-source-profile-fixture-set-v1:" + "e" * 64,
            "qualification_identity": "nar-race-entry-status-source-profile-qualification-v1:" + "f" * 64,
        },
        subject.ObservationMilestone.DEDICATED_TEST_WRITTEN: {"test_path": "tests/test_nar_race_entry_status_source_profile_fixtures.py"},
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
    for milestone in subject.ObservationMilestone:
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
