"""No-network execution observability for controlled NAR reacquisition.

This module records control metadata only.  It does not acquire, parse, persist,
or publish provider content.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Callable, Iterator, Mapping

from scripts.simulation import nar_race_entry_status_raw_capture as _raw_capture


JOURNAL_SCHEMA = "nar-race-entry-status-reacquisition-observability-journal"
JOURNAL_SCHEMA_VERSION = 1
PREFLIGHT_PASS_TOKEN = "NAR_REACQUISITION_OBSERVABILITY_PREFLIGHT_PASS"
FINAL_REPORT_PREFIX = "PHASE50_FINAL_REPORT:"
MAX_STRING_BYTES = 512
MAX_RECORD_BYTES = 4096
MAX_JOURNAL_BYTES = 131072
MAX_PROCESS_STREAM_BYTES = 16384
_MAX_SAFE_COUNT = 10_000

_RUN_ID = re.compile(r"[0-9a-f]{32}\Z", flags=re.ASCII)
_LOWER_HEX_64 = re.compile(r"[0-9a-f]{64}\Z", flags=re.ASCII)
_UTC_TEXT = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z\Z", flags=re.ASCII)
_REQUEST_ID = re.compile(r"nar-race-entry-status-request-v1:[0-9a-f]{64}\Z", flags=re.ASCII)
_CAPTURE_ID = re.compile(r"nar-race-entry-status-capture-v1:[0-9a-f]{64}\Z", flags=re.ASCII)
_BUNDLE_ID = re.compile(r"nar-race-entry-status-raw-bundle-v1:[0-9a-f]{64}\Z", flags=re.ASCII)
_FIXTURE_SET_ID_BY_VERSION = (
    (1, re.compile(r"nar-race-entry-status-source-profile-fixture-set-v1:[0-9a-f]{64}\Z", flags=re.ASCII)),
    (2, re.compile(r"nar-race-entry-status-source-profile-fixture-set-v2:[0-9a-f]{64}\Z", flags=re.ASCII)),
    (3, re.compile(r"nar-race-entry-status-source-profile-fixture-set-v3:[0-9a-f]{64}\Z", flags=re.ASCII)),
)
_QUALIFICATION_ID_BY_VERSION = (
    (1, re.compile(r"nar-race-entry-status-source-profile-qualification-v1:[0-9a-f]{64}\Z", flags=re.ASCII)),
    (2, re.compile(r"nar-race-entry-status-source-profile-qualification-v2:[0-9a-f]{64}\Z", flags=re.ASCII)),
    (3, re.compile(r"nar-race-entry-status-source-profile-qualification-v3:[0-9a-f]{64}\Z", flags=re.ASCII)),
)
_SAFE_ENUM = re.compile(r"[A-Z][A-Z0-9_]{0,127}\Z", flags=re.ASCII)
_BABA_CODE = re.compile(r"[1-9][0-9]*\Z", flags=re.ASCII)
_RACE_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z", flags=re.ASCII)
_ALLOWED_OUTCOMES = frozenset(
    {"READY_FOR_REVIEW", "SOURCE_PROFILE_FIXTURE_BLOCKED", "RECOVERY_PREFLIGHT_BLOCKED", "SYNTHETIC_SUCCESS", "SYNTHETIC_FAILURE"},
)
_ALLOWED_AUTHORIZATION_STATES = frozenset(
    {"UNCONSUMED", "CONSUMED_FAIL_CLOSED", "CONSUMED_CONFIRMED"},
)
_DEDICATED_TEST_PATHS = frozenset(
    {
        "tests/test_nar_race_entry_status_source_profile_fixtures.py",
        "tests/test_nar_race_entry_status_source_profile_v2_fixtures.py",
    },
)


class NARReacquisitionObservabilityError(Exception):
    """Base error for no-network observability support."""


class NARReacquisitionObservabilityValidationError(NARReacquisitionObservabilityError):
    """Raised when control metadata is not canonical or allowlisted."""


class NARReacquisitionObservabilityJournalError(NARReacquisitionObservabilityError):
    """Raised when durable journal I/O cannot be completed."""


class ObservationMilestone(StrEnum):
    PARENT_EXECUTION_PREPARED = "PARENT_EXECUTION_PREPARED"
    LIVE_PROCESS_START = "LIVE_PROCESS_START"
    TARGET_CONSTRUCTED = "TARGET_CONSTRUCTED"
    PHASE44_CALL_ABOUT_TO_ENTER = "PHASE44_CALL_ABOUT_TO_ENTER"
    PHASE44_FUNCTION_ENTERED = "PHASE44_FUNCTION_ENTERED"
    DEBA_TRANSPORT_FETCH_ENTERED = "DEBA_TRANSPORT_FETCH_ENTERED"
    DEBA_HTTP_GET_ATTEMPT_ABOUT_TO_START = "DEBA_HTTP_GET_ATTEMPT_ABOUT_TO_START"
    DEBA_HTTP_RESPONSE_RETURNED = "DEBA_HTTP_RESPONSE_RETURNED"
    DEBA_RAW_RESPONSE_CONSTRUCTED = "DEBA_RAW_RESPONSE_CONSTRUCTED"
    RACELIST_TRANSPORT_FETCH_ENTERED = "RACELIST_TRANSPORT_FETCH_ENTERED"
    RACELIST_HTTP_GET_ATTEMPT_ABOUT_TO_START = "RACELIST_HTTP_GET_ATTEMPT_ABOUT_TO_START"
    RACELIST_HTTP_RESPONSE_RETURNED = "RACELIST_HTTP_RESPONSE_RETURNED"
    RACELIST_RAW_RESPONSE_CONSTRUCTED = "RACELIST_RAW_RESPONSE_CONSTRUCTED"
    CLOSED_BUNDLE_RETURNED = "CLOSED_BUNDLE_RETURNED"
    DEBA_CAPTURE_METADATA_RETAINED = "DEBA_CAPTURE_METADATA_RETAINED"
    RACELIST_CAPTURE_METADATA_RETAINED = "RACELIST_CAPTURE_METADATA_RETAINED"
    PROFILE_B_DIAGNOSTICS_RETAINED = "PROFILE_B_DIAGNOSTICS_RETAINED"
    PROFILE_B_RECOVERY_DIAGNOSTICS_RETAINED = "PROFILE_B_RECOVERY_DIAGNOSTICS_RETAINED"
    PROFILE_B_CANDIDATE_ANCESTRY_RECOVERY_DIAGNOSTICS_RETAINED = "PROFILE_B_CANDIDATE_ANCESTRY_RECOVERY_DIAGNOSTICS_RETAINED"
    IDENTITY_VERIFICATION_PASS = "IDENTITY_VERIFICATION_PASS"
    PUBLICATION_SAFETY_RECOVERY_DIAGNOSTICS_RETAINED = "PUBLICATION_SAFETY_RECOVERY_DIAGNOSTICS_RETAINED"
    STRICT_STRUCTURE_RECOVERY_DIAGNOSTICS_RETAINED = "STRICT_STRUCTURE_RECOVERY_DIAGNOSTICS_RETAINED"
    PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED = "PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED"
    SAFETY_PASS = "SAFETY_PASS"
    PROFILE_A_BLOCKED_DIAGNOSTICS_RETAINED = "PROFILE_A_BLOCKED_DIAGNOSTICS_RETAINED"
    PROFILE_A_QUALIFIED = "PROFILE_A_QUALIFIED"
    PROFILE_B_QUALIFIED = "PROFILE_B_QUALIFIED"
    PUBLICATION_BEGIN = "PUBLICATION_BEGIN"
    RAW_FIXTURES_WRITTEN = "RAW_FIXTURES_WRITTEN"
    MANIFEST_WRITTEN = "MANIFEST_WRITTEN"
    DEDICATED_TEST_WRITTEN = "DEDICATED_TEST_WRITTEN"
    REGRESSIONS_PASS = "REGRESSIONS_PASS"
    ROLLBACK_BEGIN = "ROLLBACK_BEGIN"
    ROLLBACK_COMPLETE = "ROLLBACK_COMPLETE"
    LIVE_PROCESS_COMPLETE = "LIVE_PROCESS_COMPLETE"
    PARENT_EVIDENCE_VALIDATION_PASS = "PARENT_EVIDENCE_VALIDATION_PASS"
    PARENT_CLEANUP_COMPLETE = "PARENT_CLEANUP_COMPLETE"


_DETAIL_KEYS: dict[ObservationMilestone, frozenset[str]] = {
    ObservationMilestone.PARENT_EXECUTION_PREPARED: frozenset({"run_id"}),
    ObservationMilestone.LIVE_PROCESS_START: frozenset({"pid"}),
    ObservationMilestone.TARGET_CONSTRUCTED: frozenset({"baba_code", "race_date", "race_no"}),
    ObservationMilestone.PHASE44_CALL_ABOUT_TO_ENTER: frozenset({"baba_code", "race_date", "race_no"}),
    ObservationMilestone.PHASE44_FUNCTION_ENTERED: frozenset(),
    ObservationMilestone.DEBA_TRANSPORT_FETCH_ENTERED: frozenset({"request_identity"}),
    ObservationMilestone.DEBA_HTTP_GET_ATTEMPT_ABOUT_TO_START: frozenset({"request_identity"}),
    ObservationMilestone.DEBA_HTTP_RESPONSE_RETURNED: frozenset({"request_identity"}),
    ObservationMilestone.DEBA_RAW_RESPONSE_CONSTRUCTED: frozenset(
        {"request_identity", "response_sha256", "response_byte_length"},
    ),
    ObservationMilestone.RACELIST_TRANSPORT_FETCH_ENTERED: frozenset({"request_identity"}),
    ObservationMilestone.RACELIST_HTTP_GET_ATTEMPT_ABOUT_TO_START: frozenset({"request_identity"}),
    ObservationMilestone.RACELIST_HTTP_RESPONSE_RETURNED: frozenset({"request_identity"}),
    ObservationMilestone.RACELIST_RAW_RESPONSE_CONSTRUCTED: frozenset(
        {"request_identity", "response_sha256", "response_byte_length"},
    ),
    ObservationMilestone.CLOSED_BUNDLE_RETURNED: frozenset({"bundle_id"}),
    ObservationMilestone.DEBA_CAPTURE_METADATA_RETAINED: frozenset({"capture_metadata"}),
    ObservationMilestone.RACELIST_CAPTURE_METADATA_RETAINED: frozenset({"capture_metadata"}),
    ObservationMilestone.PROFILE_B_DIAGNOSTICS_RETAINED: frozenset({"profile_b_diagnostics"}),
    ObservationMilestone.PROFILE_B_RECOVERY_DIAGNOSTICS_RETAINED: frozenset({"profile_b_recovery_diagnostics"}),
    ObservationMilestone.PROFILE_B_CANDIDATE_ANCESTRY_RECOVERY_DIAGNOSTICS_RETAINED: frozenset({"profile_b_candidate_ancestry_recovery_diagnostics"}),
    ObservationMilestone.IDENTITY_VERIFICATION_PASS: frozenset({"bundle_id"}),
    ObservationMilestone.PUBLICATION_SAFETY_RECOVERY_DIAGNOSTICS_RETAINED: frozenset({"publication_safety_recovery_diagnostics"}),
    ObservationMilestone.STRICT_STRUCTURE_RECOVERY_DIAGNOSTICS_RETAINED: frozenset({"strict_structure_recovery_diagnostics"}),
    ObservationMilestone.PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED: frozenset({"publication_safety"}),
    ObservationMilestone.SAFETY_PASS: frozenset(),
    ObservationMilestone.PROFILE_A_BLOCKED_DIAGNOSTICS_RETAINED: frozenset(
        {"profile_a_blocked_diagnostics"},
    ),
    ObservationMilestone.PROFILE_A_QUALIFIED: frozenset(),
    ObservationMilestone.PROFILE_B_QUALIFIED: frozenset(),
    ObservationMilestone.PUBLICATION_BEGIN: frozenset({"planned_path_count"}),
    ObservationMilestone.RAW_FIXTURES_WRITTEN: frozenset({"document_count"}),
    ObservationMilestone.MANIFEST_WRITTEN: frozenset(
        {"fixture_set_identity", "qualification_identity"},
    ),
    ObservationMilestone.DEDICATED_TEST_WRITTEN: frozenset({"test_path"}),
    ObservationMilestone.REGRESSIONS_PASS: frozenset({"command_count"}),
    ObservationMilestone.ROLLBACK_BEGIN: frozenset(),
    ObservationMilestone.ROLLBACK_COMPLETE: frozenset(),
    ObservationMilestone.LIVE_PROCESS_COMPLETE: frozenset({"outcome", "authorization_state"}),
    ObservationMilestone.PARENT_EVIDENCE_VALIDATION_PASS: frozenset({"journal_sha256"}),
    ObservationMilestone.PARENT_CLEANUP_COMPLETE: frozenset(),
}


_MILESTONE_ORDER = {milestone: index for index, milestone in enumerate(ObservationMilestone)}
_TOP_LEVEL_KEYS = frozenset(
    {"journal_schema", "schema_version", "run_id", "sequence", "milestone", "occurred_at", "details"},
)


@dataclass(frozen=True, slots=True)
class JournalRecord:
    journal_schema: str
    schema_version: int
    run_id: str
    sequence: int
    milestone: ObservationMilestone
    occurred_at: str
    details: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class ReconstructedExecution:
    last_sequence: int
    last_milestone: ObservationMilestone
    authorization_state: str
    publication_began: bool
    rollback_state: str
    semantic_complete: bool


@dataclass(frozen=True, slots=True)
class SanitizedProcessStream:
    classification: str
    present: bool
    byte_length: int
    sha256: str
    safe_text: str | None


@dataclass(frozen=True, slots=True)
class ChildProcessEvidence:
    return_code: int
    stdout: SanitizedProcessStream
    stderr: SanitizedProcessStream
    journal_syntactically_valid: bool
    journal_semantically_valid: bool
    execution: ReconstructedExecution | None


def _error(message: str) -> NARReacquisitionObservabilityValidationError:
    return NARReacquisitionObservabilityValidationError(message)


def _canonical_json_bytes(payload: object) -> bytes:
    try:
        return json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, OverflowError) as error:
        raise _error("journal record is not canonically serializable") from error


def _utc_text(value: object) -> str:
    if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
        raise _error("operational clock must return an aware datetime")
    try:
        return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    except (OverflowError, ValueError) as error:
        raise _error("operational clock value cannot be normalized") from error


def _safe_string(value: object, name: str) -> str:
    if type(value) is not str:
        raise _error(f"{name} must be exact str")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as error:
        raise _error(f"{name} must be valid UTF-8") from error
    if not encoded or len(encoded) > MAX_STRING_BYTES:
        raise _error(f"{name} length is outside the allowlist")
    if any(character in value for character in ("\r", "\n", "\x00")) or any(
        ord(character) < 0x20 for character in value
    ):
        raise _error(f"{name} contains a control character")
    return value


def _validate_fixture_set_identity(value: object) -> tuple[str, int]:
    text = _safe_string(value, "fixture_set_identity")
    for version, pattern in _FIXTURE_SET_ID_BY_VERSION:
        if pattern.fullmatch(text) is not None:
            return text, version
    raise _error("fixture_set_identity is noncanonical")


def _validate_qualification_identity(value: object) -> tuple[str, int]:
    text = _safe_string(value, "qualification_identity")
    for version, pattern in _QUALIFICATION_ID_BY_VERSION:
        if pattern.fullmatch(text) is not None:
            return text, version
    raise _error("qualification_identity is noncanonical")


def _exact_positive_int(value: object, name: str) -> int:
    if type(value) is not int or value <= 0:
        raise _error(f"{name} must be an exact positive int")
    return value


def _exact_nonnegative_int(value: object, name: str) -> int:
    if type(value) is not int or not 0 <= value <= _MAX_SAFE_COUNT:
        raise _error(f"{name} must be an exact nonnegative int")
    return value


def _canonical_utc_detail(value: object, name: str) -> str:
    text = _safe_string(value, name)
    if _UTC_TEXT.fullmatch(text) is None:
        raise _error(f"{name} must be canonical UTC text")
    try:
        parsed = datetime.strptime(text, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError as error:
        raise _error(f"{name} is invalid") from error
    if parsed.strftime("%Y-%m-%dT%H:%M:%S.%fZ") != text:
        raise _error(f"{name} is noncanonical")
    return text


def _validate_capture_metadata(value: object) -> dict[str, object]:
    if type(value) is not dict:
        raise _error("capture_metadata must be exact dict")
    expected = {
        "schema_version",
        "document_role",
        "request_identity",
        "capture_identity",
        "response_sha256",
        "response_byte_length",
        "requested_at",
        "observed_at",
        "captured_at",
        "effective_url_matches_canonical",
        "closed_bundle_identity",
    }
    if set(value) != expected:
        raise _error("capture_metadata keys do not match the exact allowlist")
    if value["schema_version"] != 1 or type(value["schema_version"]) is not int:
        raise _error("capture_metadata schema_version must be exact 1")
    role = _safe_string(value["document_role"], "document_role")
    if role not in {"deba_table", "race_list"}:
        raise _error("document_role is outside the exact allowlist")
    request_identity = _safe_string(value["request_identity"], "request_identity")
    if _REQUEST_ID.fullmatch(request_identity) is None:
        raise _error("request_identity is noncanonical")
    capture_identity = _safe_string(value["capture_identity"], "capture_identity")
    if _CAPTURE_ID.fullmatch(capture_identity) is None:
        raise _error("capture_identity is noncanonical")
    response_sha256 = _safe_string(value["response_sha256"], "response_sha256")
    if _LOWER_HEX_64.fullmatch(response_sha256) is None:
        raise _error("response_sha256 is noncanonical")
    response_byte_length = _exact_positive_int(value["response_byte_length"], "response_byte_length")
    requested_at = _canonical_utc_detail(value["requested_at"], "requested_at")
    observed_at = _canonical_utc_detail(value["observed_at"], "observed_at")
    captured_at = _canonical_utc_detail(value["captured_at"], "captured_at")
    if not requested_at <= observed_at <= captured_at:
        raise _error("capture_metadata timestamps are out of order")
    effective_match = value["effective_url_matches_canonical"]
    if type(effective_match) is not bool or not effective_match:
        raise _error("effective_url_matches_canonical must be exact true")
    bundle_identity = _safe_string(value["closed_bundle_identity"], "closed_bundle_identity")
    if _BUNDLE_ID.fullmatch(bundle_identity) is None:
        raise _error("closed_bundle_identity is noncanonical")
    return {
        "schema_version": 1,
        "document_role": role,
        "request_identity": request_identity,
        "capture_identity": capture_identity,
        "response_sha256": response_sha256,
        "response_byte_length": response_byte_length,
        "requested_at": requested_at,
        "observed_at": observed_at,
        "captured_at": captured_at,
        "effective_url_matches_canonical": effective_match,
        "closed_bundle_identity": bundle_identity,
    }


_PUBLICATION_SAFETY_CATEGORIES = (
    "NO_AUTHENTICATION_MATERIAL",
    "NO_COOKIE_OR_SESSION_SECRET",
    "NO_CSRF_OR_SECRET_TOKEN",
    "NO_USER_ACCOUNT_IDENTIFIER",
    "NO_PERSONALIZATION_IDENTIFIER",
)
_PUBLICATION_SAFETY_OUTCOMES = frozenset({"SAFE", "UNSAFE", "AMBIGUOUS", "UNSUPPORTED"})


def _validate_publication_safety_blocked_result(value: object) -> dict[str, object]:
    if type(value) is not dict:
        raise _error("publication_safety must be exact dict")
    expected = {"schema_version", "result", "raw_fixture_publication_safe", "category_results"}
    if set(value) != expected:
        raise _error("publication_safety keys do not match the exact allowlist")
    schema_version = value["schema_version"]
    if type(schema_version) is not int or schema_version not in {2, 3}:
        raise _error("publication_safety schema_version is unsupported")
    results = value["category_results"]
    if type(results) is not list or len(results) != len(_PUBLICATION_SAFETY_CATEGORIES):
        raise _error("category_results must be the exact five-result list")
    normalized_results: list[dict[str, object]] = []
    outcomes: list[str] = []
    for expected_identifier, result in zip(_PUBLICATION_SAFETY_CATEGORIES, results, strict=True):
        if type(result) is not dict or set(result) != {"identifier", "outcome", "finding_count"}:
            raise _error("publication safety category keys do not match the exact allowlist")
        if result["identifier"] != expected_identifier or type(result["identifier"]) is not str:
            raise _error("publication safety category order or identifier is invalid")
        outcome = result["outcome"]
        if type(outcome) is not str or outcome not in _PUBLICATION_SAFETY_OUTCOMES:
            raise _error("publication safety category outcome is outside the exact allowlist")
        finding_count = _exact_nonnegative_int(result["finding_count"], "finding_count")
        normalized_results.append(
            {"identifier": expected_identifier, "outcome": outcome, "finding_count": finding_count},
        )
        outcomes.append(outcome)
    expected_result = (
        "SAFE"
        if all(outcome == "SAFE" for outcome in outcomes)
        else "UNSAFE"
        if "UNSAFE" in outcomes
        else "UNSUPPORTED"
        if "UNSUPPORTED" in outcomes
        else "AMBIGUOUS"
    )
    result = value["result"]
    if type(result) is not str or result != expected_result:
        raise _error("publication safety aggregate result is inconsistent with category outcomes")
    publication_safe = value["raw_fixture_publication_safe"]
    if type(publication_safe) is not bool or publication_safe is not (expected_result == "SAFE"):
        raise _error("raw_fixture_publication_safe is inconsistent with aggregate result")
    if expected_result == "SAFE":
        raise _error("blocked publication safety evidence cannot retain a SAFE result")
    return {
        "schema_version": schema_version,
        "result": expected_result,
        "raw_fixture_publication_safe": False,
        "category_results": normalized_results,
    }


_PROFILE_A_PREDICATES = (
    "ENTRY_TABLE_SCOPE",
    "ORDINARY_HORSE_ROW_SHAPE",
    "SELECTED_NON14_LISTING",
)
_PROFILE_A_SAFE_FIELDS: dict[str, frozenset[str]] = {
    "ENTRY_TABLE_SCOPE": frozenset({"entry_table_scope_count"}),
    "ORDINARY_HORSE_ROW_SHAPE": frozenset({"ordinary_row_count"}),
    "SELECTED_NON14_LISTING": frozenset(
        {"selected_non14_candidate_count", "selected_provider_horse_no"},
    ),
}
_PROFILE_A_OUTCOMES = frozenset({"PASS", "FAIL", "AMBIGUOUS", "UNSUPPORTED"})


def _validate_profile_a_blocked_diagnostics(value: object) -> dict[str, object]:
    if type(value) is not dict:
        raise _error("profile_a_blocked_diagnostics must be exact dict")
    expected = {
        "schema_version",
        "profile",
        "overall_result",
        "terminal_semantic",
        "predicate_results",
        "first_nonpass_predicate",
        "terminal_reason",
    }
    if set(value) != expected:
        raise _error("profile_a_blocked_diagnostics keys do not match the exact allowlist")
    schema_version = value["schema_version"]
    if type(schema_version) is not int or schema_version not in {2, 3}:
        raise _error("profile_a_blocked_diagnostics schema_version is unsupported")
    if value["profile"] != "ENTRY_LISTING_PRESENT" or type(value["profile"]) is not str:
        raise _error("Profile-A semantic is outside the exact allowlist")
    if value["overall_result"] != "BLOCKED" or type(value["overall_result"]) is not str:
        raise _error("blocked Profile-A evidence must have exact BLOCKED overall_result")
    if value["terminal_semantic"] is not None:
        raise _error("blocked Profile-A terminal_semantic must be exact null")
    results = value["predicate_results"]
    if type(results) is not list or len(results) != len(_PROFILE_A_PREDICATES):
        raise _error("Profile-A predicate_results must be the exact three-result list")
    normalized_results: list[dict[str, object]] = []
    outcomes: list[str] = []
    for expected_identifier, result in zip(_PROFILE_A_PREDICATES, results, strict=True):
        if type(result) is not dict or set(result) != {"identifier", "outcome", "safe_fields"}:
            raise _error("Profile-A predicate result keys do not match the exact allowlist")
        if result["identifier"] != expected_identifier or type(result["identifier"]) is not str:
            raise _error("Profile-A predicate order or identifier is invalid")
        outcome = result["outcome"]
        if type(outcome) is not str or outcome not in _PROFILE_A_OUTCOMES:
            raise _error("Profile-A predicate outcome is outside the exact allowlist")
        safe_fields = result["safe_fields"]
        if type(safe_fields) is not dict or frozenset(safe_fields) != _PROFILE_A_SAFE_FIELDS[expected_identifier]:
            raise _error("Profile-A safe_fields do not match the exact allowlist")
        normalized_fields: dict[str, object] = {}
        for name, item in safe_fields.items():
            if name == "selected_provider_horse_no":
                if item is not None:
                    raise _error("blocked Profile-A selected_provider_horse_no must be exact null")
            else:
                item = _exact_nonnegative_int(item, name)
            normalized_fields[name] = item
        normalized_results.append(
            {"identifier": expected_identifier, "outcome": outcome, "safe_fields": normalized_fields},
        )
        outcomes.append(outcome)
    first_index = next((index for index, outcome in enumerate(outcomes) if outcome != "PASS"), None)
    if first_index is None:
        raise _error("blocked Profile-A evidence requires a non-PASS predicate")
    expected_first = _PROFILE_A_PREDICATES[first_index]
    if value["first_nonpass_predicate"] != expected_first or type(value["first_nonpass_predicate"]) is not str:
        raise _error("Profile-A first_nonpass_predicate is inconsistent with predicate order")
    expected_reason = "UNSUPPORTED_INPUT" if "UNSUPPORTED" in outcomes else "FIRST_NONPASS_PREDICATE"
    if value["terminal_reason"] != expected_reason or type(value["terminal_reason"]) is not str:
        raise _error("Profile-A terminal_reason is inconsistent with predicate outcomes")
    return {
        "schema_version": schema_version,
        "profile": "ENTRY_LISTING_PRESENT",
        "overall_result": "BLOCKED",
        "terminal_semantic": None,
        "predicate_results": normalized_results,
        "first_nonpass_predicate": expected_first,
        "terminal_reason": expected_reason,
    }


_PROFILE_B_PREDICATES = (
    "RACE_TABLE_SCOPE",
    "UNIQUE_TARGET_6R",
    "DEBA_LINK_RELATIONSHIP",
    "DEBA_LINK_QUERY_BINDING",
    "WITHDRAWAL_ROW_SHAPE",
    "HORSE_14_WITHDRAWAL_ASSOCIATION",
)
_PROFILE_B_SAFE_FIELDS: dict[str, frozenset[str]] = {
    "RACE_TABLE_SCOPE": frozenset({"race_table_scope_count"}),
    "UNIQUE_TARGET_6R": frozenset({"target_race_no", "target_6r_row_count"}),
    "DEBA_LINK_RELATIONSHIP": frozenset({"deba_relationship_count", "deba_relationship_present"}),
    "DEBA_LINK_QUERY_BINDING": frozenset({"deba_query_binding_count", "deba_query_binding_match"}),
    "WITHDRAWAL_ROW_SHAPE": frozenset({"withdrawal_row_shape_count"}),
    "HORSE_14_WITHDRAWAL_ASSOCIATION": frozenset(
        {"withdrawn_provider_horse_no", "horse_14_withdrawal_count", "withdrawal_label_match"},
    ),
}


def _validate_profile_b_diagnostics(value: object) -> dict[str, object]:
    if type(value) is not dict:
        raise _error("profile_b_diagnostics must be exact dict")
    expected = {
        "schema_version",
        "profile",
        "overall_result",
        "terminal_semantic",
        "target",
        "predicate_results",
        "first_nonpass_predicate",
        "terminal_reason",
    }
    if set(value) != expected:
        raise _error("profile_b_diagnostics keys do not match the exact allowlist")
    schema_version = value["schema_version"]
    if type(schema_version) is not int or schema_version not in {1, 2}:
        raise _error("profile_b_diagnostics schema_version is unsupported")
    if value["profile"] != "EXPLICIT_WITHDRAWAL_PRESENT" or type(value["profile"]) is not str:
        raise _error("profile is outside the exact allowlist")
    if value["terminal_semantic"] != "EXPLICIT_WITHDRAWAL_PRESENT" or type(value["terminal_semantic"]) is not str:
        raise _error("terminal_semantic is outside the exact allowlist")
    overall = value["overall_result"]
    if type(overall) is not str or overall not in {"QUALIFIED", "BLOCKED"}:
        raise _error("overall_result is outside the exact allowlist")
    target = value["target"]
    if type(target) is not dict or set(target) != {"baba_code", "race_date", "race_no"}:
        raise _error("diagnostic target keys do not match the exact allowlist")
    baba_code = _safe_string(target["baba_code"], "baba_code")
    race_date = _safe_string(target["race_date"], "race_date")
    race_no = _exact_positive_int(target["race_no"], "race_no")
    if _BABA_CODE.fullmatch(baba_code) is None or _RACE_DATE.fullmatch(race_date) is None or race_no > 12:
        raise _error("diagnostic target is noncanonical")
    try:
        datetime.strptime(race_date, "%Y-%m-%d")
    except ValueError as error:
        raise _error("diagnostic race_date is invalid") from error
    results = value["predicate_results"]
    if type(results) is not list or len(results) != len(_PROFILE_B_PREDICATES):
        raise _error("predicate_results must be the exact six-result list")
    normalized_results: list[dict[str, object]] = []
    outcomes: list[str] = []
    for expected_identifier, result in zip(_PROFILE_B_PREDICATES, results, strict=True):
        if type(result) is not dict or set(result) != {"identifier", "outcome", "safe_fields"}:
            raise _error("predicate result keys do not match the exact allowlist")
        if result["identifier"] != expected_identifier or type(result["identifier"]) is not str:
            raise _error("predicate result order or identifier is invalid")
        outcome = result["outcome"]
        if type(outcome) is not str or outcome not in {"PASS", "FAIL", "AMBIGUOUS", "UNSUPPORTED"}:
            raise _error("predicate outcome is outside the exact allowlist")
        safe_fields = result["safe_fields"]
        if type(safe_fields) is not dict or frozenset(safe_fields) != _PROFILE_B_SAFE_FIELDS[expected_identifier]:
            raise _error("predicate safe_fields do not match the exact allowlist")
        normalized_fields: dict[str, object] = {}
        for name, item in safe_fields.items():
            if name in {"deba_relationship_present", "deba_query_binding_match", "withdrawal_label_match"}:
                if type(item) is not bool:
                    raise _error(f"{name} must be exact bool")
            else:
                _exact_nonnegative_int(item, name)
                if name == "target_race_no" and item != race_no:
                    raise _error("target_race_no must match the diagnostic target")
                if name == "withdrawn_provider_horse_no" and item != 14:
                    raise _error("withdrawn_provider_horse_no must be exact 14")
            normalized_fields[name] = item
        normalized_results.append(
            {"identifier": expected_identifier, "outcome": outcome, "safe_fields": normalized_fields},
        )
        outcomes.append(outcome)
    first_index = next((index for index, outcome in enumerate(outcomes) if outcome != "PASS"), None)
    expected_first = None if first_index is None else _PROFILE_B_PREDICATES[first_index]
    if value["first_nonpass_predicate"] != expected_first:
        raise _error("first_nonpass_predicate is inconsistent with predicate order")
    expected_overall = "QUALIFIED" if first_index is None else "BLOCKED"
    if overall != expected_overall:
        raise _error("overall_result is inconsistent with predicate outcomes")
    expected_reason = (
        "QUALIFIED"
        if first_index is None
        else "UNSUPPORTED_INPUT"
        if "UNSUPPORTED" in outcomes
        else "FIRST_NONPASS_PREDICATE"
    )
    if value["terminal_reason"] != expected_reason or type(value["terminal_reason"]) is not str:
        raise _error("terminal_reason is inconsistent with predicate outcomes")
    return {
        "schema_version": schema_version,
        "profile": "EXPLICIT_WITHDRAWAL_PRESENT",
        "overall_result": overall,
        "terminal_semantic": "EXPLICIT_WITHDRAWAL_PRESENT",
        "target": {"baba_code": baba_code, "race_date": race_date, "race_no": race_no},
        "predicate_results": normalized_results,
        "first_nonpass_predicate": expected_first,
        "terminal_reason": expected_reason,
    }


def _validate_publication_safety_recovery_diagnostics(value: object) -> dict[str, object]:
    if type(value) is not dict or set(value) != {"schema", "schema_version", "document_results"}:
        raise _error("Safety recovery keys are not exact")
    if type(value["schema"]) is not str or value["schema"] != "nar-race-entry-status-publication-safety-recovery-diagnostics":
        raise _error("Safety recovery schema is unsupported")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise _error("Safety recovery version must be exact 1")
    results = value["document_results"]
    if type(results) is not list or len(results) != 2:
        raise _error("Safety recovery requires exactly two document results")
    states = {
        ("FAIL", "NOT_REACHED", "NOT_REACHED"), ("PASS", "FAIL", "NOT_REACHED"),
        ("PASS", "PASS", "PASS"), ("PASS", "PASS", "FAIL"),
    }
    normalized = []
    for role, result in zip(("deba_table", "race_list"), results, strict=True):
        if type(result) is not dict or set(result) != {"document_role", "utf8_decode", "strict_structure", "beautifulsoup_parse"}:
            raise _error("Safety recovery result keys are not exact")
        if type(result["document_role"]) is not str or result["document_role"] != role:
            raise _error("Safety recovery role order is invalid")
        stages = tuple(result[name] for name in ("utf8_decode", "strict_structure", "beautifulsoup_parse"))
        if any(type(stage) is not str for stage in stages) or stages not in states:
            raise _error("Safety recovery stage state is impossible")
        normalized.append(dict(result))
    return {"schema": value["schema"], "schema_version": 1, "document_results": normalized}


def _validate_profile_b_recovery_diagnostics(value: object) -> dict[str, object]:
    keys = {
        "schema", "schema_version", "target", "race_table_scope_count", "target_candidate_count",
        "candidate_details_complete", "candidate_results", "all_candidate_safe_projections_equal",
    }
    if type(value) is not dict or set(value) != keys:
        raise _error("Profile-B recovery keys are not exact")
    if type(value["schema"]) is not str or value["schema"] != "nar-race-entry-status-profile-b-recovery-diagnostics":
        raise _error("Profile-B recovery schema is unsupported")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise _error("Profile-B recovery version must be exact 1")
    target = value["target"]
    if type(target) is not dict or set(target) != {"baba_code", "race_date", "race_no"}:
        raise _error("Profile-B recovery target keys are not exact")
    baba = _safe_string(target["baba_code"], "baba_code")
    race_date = _safe_string(target["race_date"], "race_date")
    race_no = _exact_nonnegative_int(target["race_no"], "race_no")
    if race_no == 0 or _BABA_CODE.fullmatch(baba) is None or _RACE_DATE.fullmatch(race_date) is None:
        raise _error("Profile-B recovery target is noncanonical")
    try:
        parsed_date = datetime.strptime(race_date, "%Y-%m-%d").date()
        _raw_capture.NARRaceEntryStatusRaceIdentity(baba, parsed_date, race_no)
    except (ValueError, _raw_capture.NARRaceEntryStatusRawCaptureError):
        raise _error("Profile-B recovery target is invalid") from None
    if parsed_date.isoformat() != race_date:
        raise _error("Profile-B recovery date is noncanonical")
    scope_count = _exact_nonnegative_int(value["race_table_scope_count"], "race_table_scope_count")
    candidate_count = _exact_nonnegative_int(value["target_candidate_count"], "target_candidate_count")
    complete = value["candidate_details_complete"]
    equal = value["all_candidate_safe_projections_equal"]
    if type(complete) is not bool or type(equal) is not bool:
        raise _error("Profile-B recovery booleans must be exact bool")
    results = value["candidate_results"]
    if type(results) is not list or len(results) > 8:
        raise _error("Profile-B recovery candidate results exceed the exact bound")
    count_keys = (
        "direct_cell_count", "anchor_count", "deba_path_link_count", "deba_href_unsupported_count",
        "canonical_target_query_match_count", "canonical_query_unsupported_count",
    )
    result_keys = set(count_keys) | {"candidate_ordinal", "canonical_target_query_match"}
    normalized = []
    projections = []
    for ordinal, result in enumerate(results, start=1):
        if type(result) is not dict or set(result) != result_keys:
            raise _error("Profile-B recovery candidate keys are not exact")
        if type(result["candidate_ordinal"]) is not int or result["candidate_ordinal"] != ordinal:
            raise _error("Profile-B recovery candidate ordinal is noncontiguous")
        counts = tuple(_exact_nonnegative_int(result[name], name) for name in count_keys)
        match = result["canonical_target_query_match"]
        if type(match) is not bool or match != (result["canonical_target_query_match_count"] >= 1):
            raise _error("Profile-B recovery query boolean is inconsistent")
        projections.append(counts + (match,))
        normalized.append(dict(result))
    if complete:
        if scope_count != 1 or candidate_count != len(results):
            raise _error("Profile-B recovery complete cardinality is inconsistent")
    elif results or equal:
        raise _error("Profile-B recovery incomplete results must be empty and nonassertive")
    elif scope_count == 1 and candidate_count <= 8:
        raise _error("Profile-B recovery reachable bounded details must be complete")
    if scope_count != 1 and candidate_count != 0:
        raise _error("Profile-B recovery candidate discovery requires a unique scope")
    expected_equal = bool(projections) and all(projection == projections[0] for projection in projections)
    if equal != expected_equal:
        raise _error("Profile-B recovery safe-projection equality is inconsistent")
    return {
        "schema": value["schema"], "schema_version": 1,
        "target": {"baba_code": baba, "race_date": race_date, "race_no": race_no},
        "race_table_scope_count": scope_count, "target_candidate_count": candidate_count,
        "candidate_details_complete": complete, "candidate_results": normalized,
        "all_candidate_safe_projections_equal": equal,
    }


def _validate_strict_structure_recovery_diagnostics(value: object) -> dict[str, object]:
    if type(value) is not dict or set(value) != {"schema", "schema_version", "document_results"}:
        raise _error("strict recovery keys are not exact")
    if type(value["schema"]) is not str or value["schema"] != "nar-race-entry-status-strict-structure-recovery-diagnostics":
        raise _error("strict recovery schema is unsupported")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise _error("strict recovery version must be exact 1")
    results = value["document_results"]
    if type(results) is not list or len(results) != 2:
        raise _error("strict recovery requires exactly two results")
    tags = frozenset({
        "HTML", "HEAD", "TITLE", "BODY", "MAIN", "HEADER", "FOOTER", "NAV", "ARTICLE",
        "SECTION", "ASIDE", "DIV", "H1", "H2", "H3", "H4", "H5", "H6", "P", "SPAN",
        "A", "STRONG", "EM", "B", "I", "U", "UL", "OL", "LI", "DL", "DT", "DD",
        "TABLE", "CAPTION", "COLGROUP", "THEAD", "TBODY", "TFOOT", "TR", "TH", "TD",
        "FORM", "FIELDSET", "LEGEND", "LABEL", "BUTTON", "SELECT", "OPTGROUP", "OPTION",
        "TEXTAREA", "SCRIPT", "STYLE", "NOSCRIPT", "TEMPLATE", "DETAILS", "SUMMARY",
        "FIGURE", "FIGCAPTION", "PICTURE", "CANVAS", "VIDEO", "AUDIO", "OBJECT", "MAP",
        "FONT", "CENTER", "OTHER_OR_CUSTOM",
    })
    keys = {"document_role", "failure_kind", "event_index", "stack_depth", "expected_open_tag", "observed_end_tag", "tolerant_parse"}
    normalized = []
    for role, result in zip(("deba_table", "race_list"), results, strict=True):
        if type(result) is not dict or set(result) != keys:
            raise _error("strict recovery result keys are not exact")
        if type(result["document_role"]) is not str or result["document_role"] != role:
            raise _error("strict recovery role order is invalid")
        kind = result["failure_kind"]
        if type(kind) is not str or kind not in {"PASS", "END_TAG_EMPTY_STACK", "END_TAG_MISMATCH", "UNCLOSED_STACK_AT_CLOSE"}:
            raise _error("strict recovery failure kind is invalid")
        index = _exact_nonnegative_int(result["event_index"], "event_index")
        depth = _exact_nonnegative_int(result["stack_depth"], "stack_depth")
        expected, observed = result["expected_open_tag"], result["observed_end_tag"]
        for tag in (expected, observed):
            if tag is not None and (type(tag) is not str or tag not in tags):
                raise _error("strict recovery tag is invalid")
        tolerant = result["tolerant_parse"]
        if type(tolerant) is not str or tolerant not in {"PASS", "FAIL"}:
            raise _error("strict recovery tolerant parse is invalid")
        valid = {
            "PASS": depth == 0 and expected is None and observed is None,
            "END_TAG_EMPTY_STACK": index >= 1 and depth == 0 and expected is None and observed is not None,
            "END_TAG_MISMATCH": index >= 1 and depth >= 1 and expected is not None and observed is not None,
            "UNCLOSED_STACK_AT_CLOSE": depth >= 1 and expected is not None and observed is None,
        }
        if not valid[kind]:
            raise _error("strict recovery fields are contradictory")
        normalized.append(dict(result))
    return {"schema": value["schema"], "schema_version": 1, "document_results": normalized}


def _validate_profile_b_candidate_ancestry_recovery_diagnostics(value: object) -> dict[str, object]:
    keys = {"schema", "schema_version", "target", "race_table_scope_count", "target_candidate_count", "candidate_details_complete", "candidate_results"}
    if type(value) is not dict or set(value) != keys:
        raise _error("ancestry recovery keys are not exact")
    if type(value["schema"]) is not str or value["schema"] != "nar-race-entry-status-profile-b-candidate-ancestry-recovery-diagnostics":
        raise _error("ancestry recovery schema is unsupported")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise _error("ancestry recovery version must be exact 1")
    target = value["target"]
    if type(target) is not dict or set(target) != {"baba_code", "race_date", "race_no"}:
        raise _error("ancestry recovery target keys are not exact")
    baba = _safe_string(target["baba_code"], "baba_code")
    race_date = _safe_string(target["race_date"], "race_date")
    race_no = _exact_nonnegative_int(target["race_no"], "race_no")
    if race_no == 0 or _BABA_CODE.fullmatch(baba) is None or _RACE_DATE.fullmatch(race_date) is None:
        raise _error("ancestry recovery target is noncanonical")
    try:
        parsed_date = datetime.strptime(race_date, "%Y-%m-%d").date()
        _raw_capture.NARRaceEntryStatusRaceIdentity(baba, parsed_date, race_no)
    except (ValueError, _raw_capture.NARRaceEntryStatusRawCaptureError):
        raise _error("ancestry recovery target is invalid") from None
    if parsed_date.isoformat() != race_date:
        raise _error("ancestry recovery date is noncanonical")
    scope_count = _exact_nonnegative_int(value["race_table_scope_count"], "race_table_scope_count")
    count = _exact_nonnegative_int(value["target_candidate_count"], "target_candidate_count")
    complete = value["candidate_details_complete"]
    if type(complete) is not bool:
        raise _error("ancestry recovery completeness must be exact bool")
    results = value["candidate_results"]
    if type(results) is not list or len(results) > 8:
        raise _error("ancestry recovery detail bound is invalid")
    if complete != (scope_count == 1 and count <= 8):
        raise _error("ancestry recovery completeness is inconsistent")
    if (complete and len(results) != count) or (not complete and results):
        raise _error("ancestry recovery cardinality is inconsistent")
    if scope_count != 1 and count != 0:
        raise _error("ancestry recovery requires unique scope")
    result_keys = {"candidate_ordinal", "nearest_table_role", "inside_change_info_table", "nested_table_depth_within_race_scope", "direct_schedule_table_descendant"}
    normalized = []
    for ordinal, result in enumerate(results, 1):
        if type(result) is not dict or set(result) != result_keys:
            raise _error("ancestry recovery candidate keys are not exact")
        if type(result["candidate_ordinal"]) is not int or result["candidate_ordinal"] != ordinal:
            raise _error("ancestry recovery ordinals are not contiguous")
        role = result["nearest_table_role"]
        if type(role) is not str or role not in {"NO_TABLE", "RACE_SCHEDULE_TABLE", "CHANGE_INFO_TABLE", "OTHER_TABLE"}:
            raise _error("ancestry recovery table role is invalid")
        inside, direct = result["inside_change_info_table"], result["direct_schedule_table_descendant"]
        if type(inside) is not bool or type(direct) is not bool:
            raise _error("ancestry recovery booleans must be exact bool")
        depth = _exact_nonnegative_int(result["nested_table_depth_within_race_scope"], "table_depth")
        valid = {"NO_TABLE": depth == 0 and not inside and not direct,
                 "RACE_SCHEDULE_TABLE": depth == 1 and not inside and direct,
                 "CHANGE_INFO_TABLE": depth >= 1 and inside and not direct,
                 "OTHER_TABLE": depth >= 2 and not direct}
        if not valid[role]:
            raise _error("ancestry recovery fields are contradictory")
        normalized.append(dict(result))
    return {"schema": value["schema"], "schema_version": 1,
            "target": {"baba_code": baba, "race_date": race_date, "race_no": race_no},
            "race_table_scope_count": scope_count, "target_candidate_count": count,
            "candidate_details_complete": complete, "candidate_results": normalized}


def _validate_detail(name: str, value: object, run_id: str) -> object:
    if name == "run_id":
        if _safe_string(value, name) != run_id:
            raise _error("details run_id must match record run_id")
        return value
    if name in {"pid", "race_no", "response_byte_length", "planned_path_count", "document_count", "command_count"}:
        return _exact_positive_int(value, name)
    if name == "capture_metadata":
        return _validate_capture_metadata(value)
    if name == "publication_safety":
        return _validate_publication_safety_blocked_result(value)
    if name == "profile_a_blocked_diagnostics":
        return _validate_profile_a_blocked_diagnostics(value)
    if name == "profile_b_diagnostics":
        return _validate_profile_b_diagnostics(value)
    if name == "profile_b_recovery_diagnostics":
        return _validate_profile_b_recovery_diagnostics(value)
    if name == "publication_safety_recovery_diagnostics":
        return _validate_publication_safety_recovery_diagnostics(value)
    if name == "strict_structure_recovery_diagnostics":
        return _validate_strict_structure_recovery_diagnostics(value)
    if name == "profile_b_candidate_ancestry_recovery_diagnostics":
        return _validate_profile_b_candidate_ancestry_recovery_diagnostics(value)
    if name == "fixture_set_identity":
        return _validate_fixture_set_identity(value)[0]
    if name == "qualification_identity":
        return _validate_qualification_identity(value)[0]
    text = _safe_string(value, name)
    if name == "baba_code" and _BABA_CODE.fullmatch(text) is None:
        raise _error("baba_code is noncanonical")
    if name == "race_date":
        if _RACE_DATE.fullmatch(text) is None:
            raise _error("race_date is noncanonical")
        try:
            datetime.strptime(text, "%Y-%m-%d")
        except ValueError as error:
            raise _error("race_date is invalid") from error
    if name == "request_identity" and _REQUEST_ID.fullmatch(text) is None:
        raise _error("request_identity is noncanonical")
    if name == "response_sha256" and _LOWER_HEX_64.fullmatch(text) is None:
        raise _error("response_sha256 is noncanonical")
    if name == "bundle_id" and _BUNDLE_ID.fullmatch(text) is None:
        raise _error("bundle_id is noncanonical")
    if name == "journal_sha256" and _LOWER_HEX_64.fullmatch(text) is None:
        raise _error("journal_sha256 is noncanonical")
    if name == "outcome" and text not in _ALLOWED_OUTCOMES:
        raise _error("outcome is outside the exact allowlist")
    if name == "authorization_state" and text not in _ALLOWED_AUTHORIZATION_STATES:
        raise _error("authorization_state is outside the exact allowlist")
    if name == "test_path" and text not in _DEDICATED_TEST_PATHS:
        raise _error("test_path is not the approved repository-relative path")
    return value


def _record_payload(
    *,
    run_id: str,
    sequence: int,
    milestone: ObservationMilestone,
    occurred_at: str,
    details: Mapping[str, object],
) -> dict[str, object]:
    if type(run_id) is not str or _RUN_ID.fullmatch(run_id) is None:
        raise _error("run_id must be 32 lowercase hexadecimal characters")
    _exact_positive_int(sequence, "sequence")
    if type(milestone) is not ObservationMilestone:
        raise _error("milestone must be exact ObservationMilestone")
    if type(occurred_at) is not str or _UTC_TEXT.fullmatch(occurred_at) is None:
        raise _error("occurred_at must be canonical UTC text")
    try:
        parsed = datetime.strptime(occurred_at, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError as error:
        raise _error("occurred_at is invalid") from error
    if parsed.strftime("%Y-%m-%dT%H:%M:%S.%fZ") != occurred_at:
        raise _error("occurred_at is noncanonical")
    if type(details) is not dict:
        raise _error("details must be exact dict")
    expected_keys = _DETAIL_KEYS[milestone]
    if frozenset(details) != expected_keys:
        raise _error("details keys do not match the milestone allowlist")
    normalized = {name: _validate_detail(name, value, run_id) for name, value in details.items()}
    if milestone is ObservationMilestone.DEBA_CAPTURE_METADATA_RETAINED:
        if normalized["capture_metadata"]["document_role"] != "deba_table":  # type: ignore[index]
            raise _error("Deba capture metadata has the wrong document role")
    if milestone is ObservationMilestone.RACELIST_CAPTURE_METADATA_RETAINED:
        if normalized["capture_metadata"]["document_role"] != "race_list":  # type: ignore[index]
            raise _error("RaceList capture metadata has the wrong document role")
    if milestone is ObservationMilestone.MANIFEST_WRITTEN:
        _, fixture_version = _validate_fixture_set_identity(normalized["fixture_set_identity"])
        _, qualification_version = _validate_qualification_identity(normalized["qualification_identity"])
        if fixture_version != qualification_version:
            raise _error("manifest identity versions must match")
    return {
        "journal_schema": JOURNAL_SCHEMA,
        "schema_version": JOURNAL_SCHEMA_VERSION,
        "run_id": run_id,
        "sequence": sequence,
        "milestone": milestone.value,
        "occurred_at": occurred_at,
        "details": normalized,
    }


class ObservabilityJournalWriter:
    """Exclusive append-only durable writer for safe external control metadata."""

    def __init__(
        self,
        *,
        journal_path: Path,
        repository_root: Path,
        run_id: str,
        clock: Callable[[], datetime],
    ) -> None:
        if not callable(clock):
            raise _error("operational clock must be callable")
        if not isinstance(journal_path, Path) or not isinstance(repository_root, Path):
            raise _error("journal_path and repository_root must be pathlib paths")
        resolved_repository = repository_root.resolve(strict=True)
        resolved_journal = journal_path.resolve(strict=False)
        if not resolved_journal.is_absolute() or resolved_journal == resolved_repository or resolved_repository in resolved_journal.parents:
            raise _error("journal must be outside the repository worktree")
        if not resolved_journal.parent.is_dir():
            raise _error("journal parent directory must already exist")
        if type(run_id) is not str or _RUN_ID.fullmatch(run_id) is None:
            raise _error("run_id must be 32 lowercase hexadecimal characters")
        self._path = resolved_journal
        self._run_id = run_id
        self._clock = clock
        self._sequence = 0
        self._stream = None
        try:
            self._stream = self._path.open("xb")
        except OSError as error:
            raise NARReacquisitionObservabilityJournalError("journal creation failed") from error

    @property
    def path(self) -> Path:
        return self._path

    @property
    def run_id(self) -> str:
        return self._run_id

    @property
    def sequence(self) -> int:
        return self._sequence

    def append(self, milestone: ObservationMilestone, details: Mapping[str, object]) -> JournalRecord:
        if self._stream is None or self._stream.closed:
            raise NARReacquisitionObservabilityJournalError("journal is closed")
        try:
            occurred_at = _utc_text(self._clock())
        except NARReacquisitionObservabilityError:
            raise
        except Exception as error:
            raise NARReacquisitionObservabilityJournalError("operational clock failed") from error
        sequence = self._sequence + 1
        payload = _record_payload(
            run_id=self._run_id,
            sequence=sequence,
            milestone=milestone,
            occurred_at=occurred_at,
            details=dict(details),
        )
        record_bytes = _canonical_json_bytes(payload)
        if len(record_bytes) > MAX_RECORD_BYTES:
            raise _error("journal record exceeds the byte limit")
        try:
            self._stream.write(record_bytes + b"\n")
            self._stream.flush()
            os.fsync(self._stream.fileno())
        except (OSError, ValueError) as error:
            raise NARReacquisitionObservabilityJournalError("durable journal append failed") from error
        self._sequence = sequence
        return JournalRecord(
            journal_schema=JOURNAL_SCHEMA,
            schema_version=JOURNAL_SCHEMA_VERSION,
            run_id=self._run_id,
            sequence=sequence,
            milestone=milestone,
            occurred_at=occurred_at,
            details=dict(payload["details"]),  # type: ignore[arg-type]
        )

    def close(self) -> None:
        if self._stream is not None and not self._stream.closed:
            try:
                self._stream.close()
            except OSError as error:
                raise NARReacquisitionObservabilityJournalError("journal close failed") from error

    def __enter__(self) -> ObservabilityJournalWriter:
        return self

    def __exit__(self, _exc_type: object, _exc: object, _traceback: object) -> None:
        self.close()


def validate_journal_bytes(value: bytes, *, expected_run_id: str | None = None) -> tuple[JournalRecord, ...]:
    if type(value) is not bytes:
        raise _error("journal must be exact bytes")
    if not value or len(value) > MAX_JOURNAL_BYTES:
        raise _error("journal size is outside the allowed range")
    if not value.endswith(b"\n"):
        raise _error("journal must end with exactly one LF-terminated record")
    try:
        text = value.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise _error("journal is not strict UTF-8") from error
    lines = text.splitlines(keepends=True)
    if not lines or any(not line.endswith("\n") or line.endswith("\r\n") for line in lines):
        raise _error("every journal record must end with one LF byte")
    records: list[JournalRecord] = []
    run_id: str | None = None
    seen: set[ObservationMilestone] = set()
    for expected_sequence, line in enumerate(lines, start=1):
        encoded_line = line[:-1].encode("utf-8")
        if not encoded_line or len(encoded_line) > MAX_RECORD_BYTES:
            raise _error("journal record size is outside the allowed range")
        try:
            payload = json.loads(encoded_line)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise _error("journal contains malformed JSON") from error
        if type(payload) is not dict or frozenset(payload) != _TOP_LEVEL_KEYS:
            raise _error("journal record top-level keys are not exact")
        if _canonical_json_bytes(payload) != encoded_line:
            raise _error("journal record is not canonical JSON")
        if payload.get("journal_schema") != JOURNAL_SCHEMA or payload.get("schema_version") != JOURNAL_SCHEMA_VERSION:
            raise _error("journal schema is unsupported")
        payload_run_id = payload.get("run_id")
        if type(payload_run_id) is not str or _RUN_ID.fullmatch(payload_run_id) is None:
            raise _error("journal run_id is noncanonical")
        if run_id is None:
            run_id = payload_run_id
        if payload_run_id != run_id or (expected_run_id is not None and payload_run_id != expected_run_id):
            raise _error("journal run_id is inconsistent")
        if payload.get("sequence") != expected_sequence or type(payload.get("sequence")) is not int:
            raise _error("journal sequence must start at one and increase by one")
        try:
            milestone = ObservationMilestone(payload.get("milestone"))
        except (TypeError, ValueError) as error:
            raise _error("journal milestone is unknown") from error
        if milestone in seen:
            raise _error("journal milestone is duplicated")
        seen.add(milestone)
        normalized = _record_payload(
            run_id=payload_run_id,
            sequence=expected_sequence,
            milestone=milestone,
            occurred_at=payload.get("occurred_at"),  # type: ignore[arg-type]
            details=payload.get("details"),  # type: ignore[arg-type]
        )
        if normalized != payload:
            raise _error("journal record differs from its normalized form")
        records.append(
            JournalRecord(
                journal_schema=JOURNAL_SCHEMA,
                schema_version=JOURNAL_SCHEMA_VERSION,
                run_id=payload_run_id,
                sequence=expected_sequence,
                milestone=milestone,
                occurred_at=payload["occurred_at"],
                details=dict(payload["details"]),
            ),
        )
    return tuple(records)


def validate_journal_semantics(records: tuple[JournalRecord, ...]) -> None:
    if type(records) is not tuple or not records:
        raise _error("journal records must be a nonempty exact tuple")
    if records[0].milestone is not ObservationMilestone.PARENT_EXECUTION_PREPARED:
        raise _error("journal must begin with PARENT_EXECUTION_PREPARED")
    previous_rank = -1
    seen = {record.milestone for record in records}
    for record in records:
        rank = _MILESTONE_ORDER[record.milestone]
        if rank <= previous_rank:
            raise _error("journal milestones are not in semantic order")
        previous_rank = rank
    if ObservationMilestone.PHASE44_FUNCTION_ENTERED in seen and ObservationMilestone.PHASE44_CALL_ABOUT_TO_ENTER not in seen:
        raise _error("Phase44 entry lacks its durable authorization boundary")
    retained = {
        ObservationMilestone.DEBA_CAPTURE_METADATA_RETAINED,
        ObservationMilestone.RACELIST_CAPTURE_METADATA_RETAINED,
        ObservationMilestone.PROFILE_B_DIAGNOSTICS_RETAINED,
        ObservationMilestone.PROFILE_B_RECOVERY_DIAGNOSTICS_RETAINED,
        ObservationMilestone.PROFILE_B_CANDIDATE_ANCESTRY_RECOVERY_DIAGNOSTICS_RETAINED,
        ObservationMilestone.PUBLICATION_SAFETY_RECOVERY_DIAGNOSTICS_RETAINED,
        ObservationMilestone.STRICT_STRUCTURE_RECOVERY_DIAGNOSTICS_RETAINED,
        ObservationMilestone.PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED,
        ObservationMilestone.PROFILE_A_BLOCKED_DIAGNOSTICS_RETAINED,
    }
    if seen & retained and ObservationMilestone.CLOSED_BUNDLE_RETURNED not in seen:
        raise _error("retained source evidence requires a closed bundle")
    if ObservationMilestone.RACELIST_CAPTURE_METADATA_RETAINED in seen and ObservationMilestone.DEBA_CAPTURE_METADATA_RETAINED not in seen:
        raise _error("RaceList capture metadata requires prior Deba capture metadata")
    if ObservationMilestone.PROFILE_B_DIAGNOSTICS_RETAINED in seen and not {
        ObservationMilestone.DEBA_CAPTURE_METADATA_RETAINED,
        ObservationMilestone.RACELIST_CAPTURE_METADATA_RETAINED,
    }.issubset(seen):
        raise _error("Profile-B diagnostics require both capture metadata records")
    capture_and_identity = {
        ObservationMilestone.DEBA_CAPTURE_METADATA_RETAINED,
        ObservationMilestone.RACELIST_CAPTURE_METADATA_RETAINED,
        ObservationMilestone.IDENTITY_VERIFICATION_PASS,
    }
    if ObservationMilestone.PROFILE_B_RECOVERY_DIAGNOSTICS_RETAINED in seen:
        if ObservationMilestone.PROFILE_B_DIAGNOSTICS_RETAINED not in seen:
            raise _error("Profile-B recovery requires retained normal diagnostics")
        by_milestone = {record.milestone: record for record in records}
        recovery_target = by_milestone[ObservationMilestone.PROFILE_B_RECOVERY_DIAGNOSTICS_RETAINED].details["profile_b_recovery_diagnostics"]["target"]
        normal_target = by_milestone[ObservationMilestone.PROFILE_B_DIAGNOSTICS_RETAINED].details["profile_b_diagnostics"]["target"]
        if recovery_target != normal_target:
            raise _error("Profile-B recovery target contradicts normal diagnostics")
    if (
        ObservationMilestone.PUBLICATION_SAFETY_RECOVERY_DIAGNOSTICS_RETAINED in seen
        and not capture_and_identity.issubset(seen)
    ):
        raise _error("Safety recovery requires retained captures and verified identity")
    if ObservationMilestone.PROFILE_B_CANDIDATE_ANCESTRY_RECOVERY_DIAGNOSTICS_RETAINED in seen:
        if ObservationMilestone.PROFILE_B_RECOVERY_DIAGNOSTICS_RETAINED not in seen:
            raise _error("candidate ancestry requires Phase63 Profile-B recovery")
        by_milestone = {record.milestone: record for record in records}
        ancestry = by_milestone[ObservationMilestone.PROFILE_B_CANDIDATE_ANCESTRY_RECOVERY_DIAGNOSTICS_RETAINED].details["profile_b_candidate_ancestry_recovery_diagnostics"]
        recovery = by_milestone[ObservationMilestone.PROFILE_B_RECOVERY_DIAGNOSTICS_RETAINED].details["profile_b_recovery_diagnostics"]
        for name in ("target", "race_table_scope_count", "target_candidate_count", "candidate_details_complete"):
            if ancestry[name] != recovery[name]:
                raise _error("candidate ancestry contradicts Phase63 recovery")
    if ObservationMilestone.STRICT_STRUCTURE_RECOVERY_DIAGNOSTICS_RETAINED in seen:
        if ObservationMilestone.PUBLICATION_SAFETY_RECOVERY_DIAGNOSTICS_RETAINED not in seen:
            raise _error("strict recovery requires Phase63 Safety recovery")
        by_milestone = {record.milestone: record for record in records}
        stages = by_milestone[ObservationMilestone.PUBLICATION_SAFETY_RECOVERY_DIAGNOSTICS_RETAINED].details["publication_safety_recovery_diagnostics"]["document_results"]
        structures = by_milestone[ObservationMilestone.STRICT_STRUCTURE_RECOVERY_DIAGNOSTICS_RETAINED].details["strict_structure_recovery_diagnostics"]["document_results"]
        for stage, structure in zip(stages, structures, strict=True):
            strict_pass = structure["failure_kind"] == "PASS"
            if stage["utf8_decode"] != "PASS" or stage["strict_structure"] != ("PASS" if strict_pass else "FAIL"):
                raise _error("strict recovery contradicts Phase63 stages")
            if strict_pass and stage["beautifulsoup_parse"] != structure["tolerant_parse"]:
                raise _error("strict recovery contradicts Phase63 DOM parse")
    if (
        ObservationMilestone.PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED in seen
        and not capture_and_identity.issubset(seen)
    ):
        raise _error("blocked publication safety evidence requires retained captures and verified identity")
    if ObservationMilestone.PROFILE_A_BLOCKED_DIAGNOSTICS_RETAINED in seen and not {
        ObservationMilestone.TARGET_CONSTRUCTED,
        ObservationMilestone.SAFETY_PASS,
    }.issubset(seen):
        raise _error("blocked Profile-A evidence requires the constructed target and successful safety gate")
    if ObservationMilestone.PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED in seen and seen & {
        ObservationMilestone.SAFETY_PASS,
        ObservationMilestone.PROFILE_A_BLOCKED_DIAGNOSTICS_RETAINED,
        ObservationMilestone.PROFILE_A_QUALIFIED,
        ObservationMilestone.PROFILE_B_QUALIFIED,
        ObservationMilestone.PUBLICATION_BEGIN,
    }:
        raise _error("blocked publication safety evidence contradicts later success progression")
    if ObservationMilestone.PROFILE_A_BLOCKED_DIAGNOSTICS_RETAINED in seen and seen & {
        ObservationMilestone.PROFILE_A_QUALIFIED,
        ObservationMilestone.PROFILE_B_QUALIFIED,
        ObservationMilestone.PUBLICATION_BEGIN,
    }:
        raise _error("blocked Profile-A evidence contradicts later success progression")
    if ObservationMilestone.ROLLBACK_COMPLETE in seen and ObservationMilestone.ROLLBACK_BEGIN not in seen:
        raise _error("rollback completion lacks rollback start")
    if ObservationMilestone.ROLLBACK_BEGIN in seen and ObservationMilestone.PUBLICATION_BEGIN not in seen:
        raise _error("rollback cannot begin before publication")
    if ObservationMilestone.PARENT_EVIDENCE_VALIDATION_PASS in seen and ObservationMilestone.LIVE_PROCESS_COMPLETE not in seen:
        raise _error("parent validation requires child completion")
    if ObservationMilestone.PARENT_CLEANUP_COMPLETE in seen and ObservationMilestone.PARENT_EVIDENCE_VALIDATION_PASS not in seen:
        raise _error("parent cleanup requires validated evidence")


def reconstruct_execution(records: tuple[JournalRecord, ...]) -> ReconstructedExecution:
    validate_journal_semantics(records)
    milestones = {record.milestone for record in records}
    if ObservationMilestone.PHASE44_FUNCTION_ENTERED in milestones:
        authorization = "CONSUMED_CONFIRMED"
    elif ObservationMilestone.PHASE44_CALL_ABOUT_TO_ENTER in milestones:
        authorization = "CONSUMED_FAIL_CLOSED"
    else:
        authorization = "UNCONSUMED"
    if ObservationMilestone.ROLLBACK_COMPLETE in milestones:
        rollback = "COMPLETE"
    elif ObservationMilestone.ROLLBACK_BEGIN in milestones:
        rollback = "STARTED_NOT_COMPLETED"
    else:
        rollback = "NOT_STARTED"
    return ReconstructedExecution(
        last_sequence=records[-1].sequence,
        last_milestone=records[-1].milestone,
        authorization_state=authorization,
        publication_began=ObservationMilestone.PUBLICATION_BEGIN in milestones,
        rollback_state=rollback,
        semantic_complete=ObservationMilestone.LIVE_PROCESS_COMPLETE in milestones,
    )


def sanitize_process_stream(value: bytes) -> SanitizedProcessStream:
    if type(value) is not bytes:
        raise _error("process stream must be exact bytes")
    digest = hashlib.sha256(value).hexdigest()
    if not value:
        return SanitizedProcessStream("EMPTY", False, 0, digest, None)
    if len(value) > MAX_PROCESS_STREAM_BYTES:
        return SanitizedProcessStream("OVERSIZED_REDACTED", True, len(value), digest, None)
    try:
        text = value.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return SanitizedProcessStream("INVALID_UTF8", True, len(value), digest, None)
    safe_text: str | None = None
    classification = "UNCONTROLLED_OUTPUT_REDACTED"
    if text == PREFLIGHT_PASS_TOKEN + "\n":
        classification = "SAFE_PREFLIGHT_TOKEN"
        safe_text = text
    elif text.startswith(FINAL_REPORT_PREFIX) and text.endswith("\n") and text.count("\n") == 1:
        encoded_payload = text[len(FINAL_REPORT_PREFIX) : -1].encode("utf-8")
        try:
            payload = json.loads(encoded_payload)
        except json.JSONDecodeError:
            payload = None
        expected = {"schema_version", "outcome", "authorization_state", "last_sequence", "last_milestone"}
        if type(payload) is dict and set(payload) == expected and _canonical_json_bytes(payload) == encoded_payload:
            try:
                _exact_positive_int(payload["last_sequence"], "last_sequence")
                if _safe_string(payload["outcome"], "outcome") not in _ALLOWED_OUTCOMES:
                    raise _error("outcome is outside the exact allowlist")
                if _safe_string(payload["authorization_state"], "authorization_state") not in _ALLOWED_AUTHORIZATION_STATES:
                    raise _error("authorization_state is outside the exact allowlist")
                ObservationMilestone(_safe_string(payload["last_milestone"], "last_milestone"))
            except NARReacquisitionObservabilityValidationError:
                pass
            else:
                classification = "SAFE_FINAL_REPORT"
                safe_text = text
    return SanitizedProcessStream(classification, True, len(value), digest, safe_text)


def retain_child_process_evidence(
    *,
    return_code: int,
    stdout: bytes,
    stderr: bytes,
    journal_bytes: bytes,
    expected_run_id: str,
) -> ChildProcessEvidence:
    if type(return_code) is not int:
        raise _error("return_code must be exact int")
    sanitized_stdout = sanitize_process_stream(stdout)
    sanitized_stderr = sanitize_process_stream(stderr)
    try:
        records = validate_journal_bytes(journal_bytes, expected_run_id=expected_run_id)
    except NARReacquisitionObservabilityValidationError:
        return ChildProcessEvidence(
            return_code,
            sanitized_stdout,
            sanitized_stderr,
            False,
            False,
            None,
        )
    try:
        execution = reconstruct_execution(records)
    except NARReacquisitionObservabilityValidationError:
        return ChildProcessEvidence(
            return_code,
            sanitized_stdout,
            sanitized_stderr,
            True,
            False,
            None,
        )
    return ChildProcessEvidence(
        return_code,
        sanitized_stdout,
        sanitized_stderr,
        True,
        True,
        execution,
    )


class Phase44ObservationBridge:
    """Translate private Phase44 callbacks into safe durable milestones."""

    def __init__(self, writer: ObservabilityJournalWriter) -> None:
        if type(writer) is not ObservabilityJournalWriter:
            raise _error("writer must be exact ObservabilityJournalWriter")
        self._writer = writer
        self._constructed_bundle_id: str | None = None

    def __call__(self, event: _raw_capture._RawCaptureObservationEvent) -> None:
        if type(event) is not _raw_capture._RawCaptureObservationEvent:
            raise _error("Phase44 observation event has an unexpected type")
        if event.kind == "CLOSED_BUNDLE_CONSTRUCTED":
            if event.bundle_id is None or _BUNDLE_ID.fullmatch(event.bundle_id) is None:
                raise _error("constructed bundle event is invalid")
            self._constructed_bundle_id = event.bundle_id
            return
        page_prefix = {
            _raw_capture.NARRaceEntryStatusPageKind.DEBA_TABLE: "DEBA",
            _raw_capture.NARRaceEntryStatusPageKind.RACE_LIST: "RACELIST",
        }.get(event.page_kind)
        if event.kind == "ACQUISITION_FUNCTION_ENTERED":
            if any(
                value is not None
                for value in (
                    event.page_kind,
                    event.request_identity,
                    event.response_sha256,
                    event.response_byte_length,
                    event.bundle_id,
                )
            ):
                raise _error("function-entry event carries unexpected metadata")
            self._writer.append(ObservationMilestone.PHASE44_FUNCTION_ENTERED, {})
            return
        if page_prefix is None or event.request_identity is None:
            raise _error("Phase44 page observation is incomplete")
        milestone_name = {
            "TRANSPORT_FETCH_ABOUT_TO_START": f"{page_prefix}_TRANSPORT_FETCH_ENTERED",
            "HTTP_GET_ATTEMPT_ABOUT_TO_START": f"{page_prefix}_HTTP_GET_ATTEMPT_ABOUT_TO_START",
            "HTTP_RESPONSE_RETURNED": f"{page_prefix}_HTTP_RESPONSE_RETURNED",
            "RAW_RESPONSE_CONSTRUCTED": f"{page_prefix}_RAW_RESPONSE_CONSTRUCTED",
        }.get(event.kind)
        if milestone_name is None:
            raise _error("Phase44 observation kind is unknown")
        details: dict[str, object] = {"request_identity": event.request_identity}
        if event.kind == "RAW_RESPONSE_CONSTRUCTED":
            details["response_sha256"] = event.response_sha256
            details["response_byte_length"] = event.response_byte_length
        elif any(
            value is not None
            for value in (event.response_sha256, event.response_byte_length, event.bundle_id)
        ):
            raise _error("Phase44 boundary event carries unexpected metadata")
        self._writer.append(ObservationMilestone(milestone_name), details)

    def record_closed_bundle_returned(self, bundle_id: str) -> None:
        if self._constructed_bundle_id is None or bundle_id != self._constructed_bundle_id:
            raise _error("returned bundle does not match the observed constructed bundle")
        self._writer.append(ObservationMilestone.CLOSED_BUNDLE_RETURNED, {"bundle_id": bundle_id})


@contextmanager
def bind_phase44_observer(writer: ObservabilityJournalWriter) -> Iterator[Phase44ObservationBridge]:
    bridge = Phase44ObservationBridge(writer)
    with _raw_capture._raw_capture_observer_scope(bridge):
        yield bridge


def validate_generated_source(source: str, filename: str = "<nar_reacquisition_observability_executor.py>") -> None:
    if type(source) is not str or not source:
        raise _error("generated source must be nonempty exact str")
    if type(filename) is not str or not filename.startswith("<") or not filename.endswith(">"):
        raise _error("generated source filename must be a synthetic bracketed name")
    try:
        compile(source, filename, "exec")
    except (SyntaxError, ValueError, TypeError) as error:
        raise _error("generated source failed the mandatory compile gate") from error


def preflight_result(
    *,
    child_evidence: ChildProcessEvidence,
    cleanup_succeeded: bool,
    bytecode_residue_absent: bool,
) -> str:
    if type(child_evidence) is not ChildProcessEvidence:
        raise _error("child_evidence must be exact ChildProcessEvidence")
    if type(cleanup_succeeded) is not bool or type(bytecode_residue_absent) is not bool:
        raise _error("preflight cleanup flags must be exact bool")
    execution = child_evidence.execution
    if not (
        child_evidence.return_code == 0
        and child_evidence.journal_syntactically_valid
        and child_evidence.journal_semantically_valid
        and execution is not None
        and execution.semantic_complete
        and child_evidence.stdout.classification == "SAFE_PREFLIGHT_TOKEN"
        and cleanup_succeeded
        and bytecode_residue_absent
    ):
        raise _error("observability preflight did not satisfy every approved gate")
    return PREFLIGHT_PASS_TOKEN


__all__ = (
    "ChildProcessEvidence",
    "FINAL_REPORT_PREFIX",
    "JOURNAL_SCHEMA",
    "JOURNAL_SCHEMA_VERSION",
    "JournalRecord",
    "MAX_JOURNAL_BYTES",
    "MAX_PROCESS_STREAM_BYTES",
    "MAX_RECORD_BYTES",
    "MAX_STRING_BYTES",
    "NARReacquisitionObservabilityError",
    "NARReacquisitionObservabilityJournalError",
    "NARReacquisitionObservabilityValidationError",
    "ObservationMilestone",
    "ObservabilityJournalWriter",
    "PREFLIGHT_PASS_TOKEN",
    "Phase44ObservationBridge",
    "ReconstructedExecution",
    "SanitizedProcessStream",
    "bind_phase44_observer",
    "preflight_result",
    "reconstruct_execution",
    "retain_child_process_evidence",
    "sanitize_process_stream",
    "validate_generated_source",
    "validate_journal_bytes",
    "validate_journal_semantics",
)
