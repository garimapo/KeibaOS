"""Pure diagnostics for the NAR RaceList withdrawal source profile.

The module accepts exact Phase44 authority objects and source bytes.  It has no
network, clock, filesystem, database, or publication responsibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
import json
import re
from types import MappingProxyType
from typing import Mapping
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup as _BeautifulSoup
from bs4 import ParserRejectedMarkup as _ParserRejectedMarkup
from bs4.element import Tag as _Tag

from scripts.simulation import nar_race_entry_status_raw_capture as _raw_capture


PROFILE_B_DIAGNOSTICS_SCHEMA = "profile_b_diagnostics_v1"
PROFILE_B_DIAGNOSTICS_SCHEMA_VERSION = 1
PROFILE_B_DIAGNOSTICS_SCHEMA_VERSION_V2 = 2
PROFILE_B_TERMINAL_SEMANTIC = "EXPLICIT_WITHDRAWAL_PRESENT"
CAPTURE_METADATA_SCHEMA = "nar_race_entry_status_capture_metadata_v1"
CAPTURE_METADATA_SCHEMA_VERSION = 1

_DEBA_PATH = "/KeibaWeb/TodayRaceInfo/DebaTable"
_WITHDRAWN_HORSE_NO = 14
_WITHDRAWAL_LABEL = "出走取消"
_MAX_SAFE_COUNT = 10_000
_REQUEST_ID = re.compile(r"nar-race-entry-status-request-v1:[0-9a-f]{64}\Z", flags=re.ASCII)
_CAPTURE_ID = re.compile(r"nar-race-entry-status-capture-v1:[0-9a-f]{64}\Z", flags=re.ASCII)
_BUNDLE_ID = re.compile(r"nar-race-entry-status-raw-bundle-v1:[0-9a-f]{64}\Z", flags=re.ASCII)
_LOWER_HEX_64 = re.compile(r"[0-9a-f]{64}\Z", flags=re.ASCII)
_UTC_TEXT = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z\Z",
    flags=re.ASCII,
)


class NARRaceEntryStatusSourceProfileDiagnosticsError(Exception):
    """Base error for invalid diagnostic authority or result data."""


class NARRaceEntryStatusSourceProfileDiagnosticsValidationError(
    NARRaceEntryStatusSourceProfileDiagnosticsError,
):
    """Raised when formal input or safe output data is contradictory."""


class ProfileBPredicateIdentifier(StrEnum):
    RACE_TABLE_SCOPE = "RACE_TABLE_SCOPE"
    UNIQUE_TARGET_6R = "UNIQUE_TARGET_6R"
    DEBA_LINK_RELATIONSHIP = "DEBA_LINK_RELATIONSHIP"
    DEBA_LINK_QUERY_BINDING = "DEBA_LINK_QUERY_BINDING"
    WITHDRAWAL_ROW_SHAPE = "WITHDRAWAL_ROW_SHAPE"
    HORSE_14_WITHDRAWAL_ASSOCIATION = "HORSE_14_WITHDRAWAL_ASSOCIATION"


class ProfileBPredicateOutcome(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    AMBIGUOUS = "AMBIGUOUS"
    UNSUPPORTED = "UNSUPPORTED"


_PREDICATE_ORDER = tuple(ProfileBPredicateIdentifier)
_SAFE_FIELDS: dict[ProfileBPredicateIdentifier, frozenset[str]] = {
    ProfileBPredicateIdentifier.RACE_TABLE_SCOPE: frozenset({"race_table_scope_count"}),
    ProfileBPredicateIdentifier.UNIQUE_TARGET_6R: frozenset(
        {"target_race_no", "target_6r_row_count"},
    ),
    ProfileBPredicateIdentifier.DEBA_LINK_RELATIONSHIP: frozenset(
        {"deba_relationship_count", "deba_relationship_present"},
    ),
    ProfileBPredicateIdentifier.DEBA_LINK_QUERY_BINDING: frozenset(
        {"deba_query_binding_count", "deba_query_binding_match"},
    ),
    ProfileBPredicateIdentifier.WITHDRAWAL_ROW_SHAPE: frozenset(
        {"withdrawal_row_shape_count"},
    ),
    ProfileBPredicateIdentifier.HORSE_14_WITHDRAWAL_ASSOCIATION: frozenset(
        {"withdrawn_provider_horse_no", "horse_14_withdrawal_count", "withdrawal_label_match"},
    ),
}


def _validation(message: str) -> NARRaceEntryStatusSourceProfileDiagnosticsValidationError:
    return NARRaceEntryStatusSourceProfileDiagnosticsValidationError(message)


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
        raise _validation("diagnostic result is not canonically serializable") from error


def _safe_fields(
    identifier: ProfileBPredicateIdentifier,
    fields: Mapping[str, object],
) -> Mapping[str, object]:
    if type(fields) is not dict or frozenset(fields) != _SAFE_FIELDS[identifier]:
        raise _validation("predicate safe fields do not match the exact allowlist")
    normalized: dict[str, object] = {}
    for name, value in fields.items():
        if name in {
            "deba_relationship_present",
            "deba_query_binding_match",
            "withdrawal_label_match",
        }:
            if type(value) is not bool:
                raise _validation(f"{name} must be exact bool")
        else:
            if type(value) is not int or not 0 <= value <= _MAX_SAFE_COUNT:
                raise _validation(f"{name} must be a nonnegative exact int")
            if name == "target_race_no" and not 1 <= value <= 12:
                raise _validation("target_race_no is outside the formal range")
            if name == "withdrawn_provider_horse_no" and value != _WITHDRAWN_HORSE_NO:
                raise _validation("withdrawn_provider_horse_no is not the frozen value")
        normalized[name] = value
    return MappingProxyType(normalized)


@dataclass(frozen=True, slots=True)
class ProfileBPredicateResult:
    identifier: ProfileBPredicateIdentifier
    outcome: ProfileBPredicateOutcome
    safe_fields: Mapping[str, object]

    def __post_init__(self) -> None:
        if type(self.identifier) is not ProfileBPredicateIdentifier:
            raise _validation("predicate identifier must be exact ProfileBPredicateIdentifier")
        if type(self.outcome) is not ProfileBPredicateOutcome:
            raise _validation("predicate outcome must be exact ProfileBPredicateOutcome")
        object.__setattr__(self, "safe_fields", _safe_fields(self.identifier, self.safe_fields))

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "identifier": self.identifier.value,
            "outcome": self.outcome.value,
            "safe_fields": dict(self.safe_fields),
        }


@dataclass(frozen=True, slots=True)
class ProfileBDiagnostics:
    target: _raw_capture.NARRaceEntryStatusRaceIdentity
    predicate_results: tuple[ProfileBPredicateResult, ...]

    def __post_init__(self) -> None:
        target = _canonical_target(self.target)
        if type(self.predicate_results) is not tuple or len(self.predicate_results) != len(_PREDICATE_ORDER):
            raise _validation("predicate_results must contain the exact six-result tuple")
        if any(type(item) is not ProfileBPredicateResult for item in self.predicate_results):
            raise _validation("predicate_results contains an unexpected result type")
        if tuple(item.identifier for item in self.predicate_results) != _PREDICATE_ORDER:
            raise _validation("predicate_results are outside the frozen order")
        object.__setattr__(self, "target", target)

    @property
    def overall_result(self) -> str:
        return "QUALIFIED" if all(
            result.outcome is ProfileBPredicateOutcome.PASS for result in self.predicate_results
        ) else "BLOCKED"

    @property
    def first_nonpass_predicate(self) -> ProfileBPredicateIdentifier | None:
        return next(
            (
                result.identifier
                for result in self.predicate_results
                if result.outcome is not ProfileBPredicateOutcome.PASS
            ),
            None,
        )

    @property
    def terminal_reason(self) -> str:
        if self.first_nonpass_predicate is None:
            return "QUALIFIED"
        if any(
            result.outcome is ProfileBPredicateOutcome.UNSUPPORTED
            for result in self.predicate_results
        ):
            return "UNSUPPORTED_INPUT"
        return "FIRST_NONPASS_PREDICATE"

    def to_canonical_dict(self) -> dict[str, object]:
        first = self.first_nonpass_predicate
        return {
            "schema_version": PROFILE_B_DIAGNOSTICS_SCHEMA_VERSION,
            "profile": PROFILE_B_TERMINAL_SEMANTIC,
            "overall_result": self.overall_result,
            "terminal_semantic": PROFILE_B_TERMINAL_SEMANTIC,
            "target": {
                "baba_code": self.target.baba_code,
                "race_date": self.target.race_date.isoformat(),
                "race_no": self.target.race_no,
            },
            "predicate_results": [result.to_canonical_dict() for result in self.predicate_results],
            "first_nonpass_predicate": None if first is None else first.value,
            "terminal_reason": self.terminal_reason,
        }

    def canonical_bytes(self) -> bytes:
        return _canonical_json_bytes(self.to_canonical_dict())


@dataclass(frozen=True, slots=True)
class ProfileBDiagnosticsV2(ProfileBDiagnostics):
    """Version 2 diagnostics with a structural schedule-row boundary."""

    def to_canonical_dict(self) -> dict[str, object]:
        payload = super().to_canonical_dict()
        payload["schema_version"] = PROFILE_B_DIAGNOSTICS_SCHEMA_VERSION_V2
        return payload


@dataclass(frozen=True, slots=True)
class CaptureDocumentMetadata:
    document_role: str
    request_identity: str
    capture_identity: str
    response_sha256: str
    response_byte_length: int
    requested_at: str
    observed_at: str
    captured_at: str
    effective_url_matches_canonical: bool

    def __post_init__(self) -> None:
        if self.document_role not in {"deba_table", "race_list"} or type(self.document_role) is not str:
            raise _validation("document_role is outside the exact allowlist")
        if type(self.request_identity) is not str or _REQUEST_ID.fullmatch(self.request_identity) is None:
            raise _validation("request_identity is noncanonical")
        if type(self.capture_identity) is not str or _CAPTURE_ID.fullmatch(self.capture_identity) is None:
            raise _validation("capture_identity is noncanonical")
        if type(self.response_sha256) is not str or _LOWER_HEX_64.fullmatch(self.response_sha256) is None:
            raise _validation("response_sha256 is noncanonical")
        if type(self.response_byte_length) is not int or self.response_byte_length <= 0:
            raise _validation("response_byte_length must be an exact positive int")
        timestamp_values = (self.requested_at, self.observed_at, self.captured_at)
        if any(type(value) is not str or _UTC_TEXT.fullmatch(value) is None for value in timestamp_values):
            raise _validation("capture timestamp is noncanonical")
        try:
            parsed = tuple(datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ") for value in timestamp_values)
        except ValueError as error:
            raise _validation("capture timestamp is invalid") from error
        if not parsed[0] <= parsed[1] <= parsed[2]:
            raise _validation("capture timestamps are out of order")
        if type(self.effective_url_matches_canonical) is not bool or not self.effective_url_matches_canonical:
            raise _validation("effective_url_matches_canonical must be exact true")

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "schema_version": CAPTURE_METADATA_SCHEMA_VERSION,
            "document_role": self.document_role,
            "request_identity": self.request_identity,
            "capture_identity": self.capture_identity,
            "response_sha256": self.response_sha256,
            "response_byte_length": self.response_byte_length,
            "requested_at": self.requested_at,
            "observed_at": self.observed_at,
            "captured_at": self.captured_at,
            "effective_url_matches_canonical": self.effective_url_matches_canonical,
        }


@dataclass(frozen=True, slots=True)
class CaptureMetadataSummary:
    deba_table: CaptureDocumentMetadata
    race_list: CaptureDocumentMetadata
    closed_bundle_identity: str

    def __post_init__(self) -> None:
        if type(self.deba_table) is not CaptureDocumentMetadata or self.deba_table.document_role != "deba_table":
            raise _validation("deba_table metadata has the wrong role or type")
        if type(self.race_list) is not CaptureDocumentMetadata or self.race_list.document_role != "race_list":
            raise _validation("race_list metadata has the wrong role or type")
        if type(self.closed_bundle_identity) is not str or _BUNDLE_ID.fullmatch(self.closed_bundle_identity) is None:
            raise _validation("closed_bundle_identity is noncanonical")
        deba_end = datetime.strptime(self.deba_table.captured_at, "%Y-%m-%dT%H:%M:%S.%fZ")
        race_list_start = datetime.strptime(self.race_list.requested_at, "%Y-%m-%dT%H:%M:%S.%fZ")
        if deba_end > race_list_start:
            raise _validation("capture summary document timestamps are out of order")

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "schema_version": CAPTURE_METADATA_SCHEMA_VERSION,
            "deba_table": self.deba_table.to_canonical_dict(),
            "race_list": self.race_list.to_canonical_dict(),
            "closed_bundle_identity": self.closed_bundle_identity,
        }

    def canonical_bytes(self) -> bytes:
        return _canonical_json_bytes(self.to_canonical_dict())


def _canonical_target(value: object) -> _raw_capture.NARRaceEntryStatusRaceIdentity:
    if type(value) is not _raw_capture.NARRaceEntryStatusRaceIdentity:
        raise _validation("target must be exact NARRaceEntryStatusRaceIdentity")
    try:
        return _raw_capture.NARRaceEntryStatusRaceIdentity(
            baba_code=value.baba_code,
            race_date=value.race_date,
            race_no=value.race_no,
        )
    except (_raw_capture.NARRaceEntryStatusRawCaptureError, AttributeError, TypeError) as error:
        raise _validation("target identity is malformed") from error


def _outcome(count: int) -> ProfileBPredicateOutcome:
    if count == 1:
        return ProfileBPredicateOutcome.PASS
    if count == 0:
        return ProfileBPredicateOutcome.FAIL
    return ProfileBPredicateOutcome.AMBIGUOUS


def _result(
    identifier: ProfileBPredicateIdentifier,
    outcome: ProfileBPredicateOutcome,
    **safe_fields: object,
) -> ProfileBPredicateResult:
    return ProfileBPredicateResult(identifier, outcome, safe_fields)


def _direct_cells(row: _Tag) -> list[_Tag]:
    return [cell for cell in row.find_all("td", recursive=False) if type(cell) is _Tag]


def _normalized_cell(cell: _Tag) -> str:
    return "".join(cell.stripped_strings)


def _has_exact_class_token(node: _Tag, token: str) -> bool:
    value = node.get("class")
    if type(value) is str:
        return value == token
    if type(value) is list:
        return any(type(item) is str and item == token for item in value)
    return False


def _is_v2_schedule_domain_row(row: _Tag, scope: _Tag) -> bool:
    tables: list[_Tag] = []
    parent = row.parent
    while type(parent) is _Tag and parent is not scope:
        if parent.name == "table":
            tables.append(parent)
        parent = parent.parent
    return parent is scope and len(tables) == 1 and not _has_exact_class_token(tables[0], "changeInfo")


def _unsupported_results(
    target: _raw_capture.NARRaceEntryStatusRaceIdentity,
    result_type: type[ProfileBDiagnostics],
) -> ProfileBDiagnostics:
    return result_type(
        target=target,
        predicate_results=(
            _result(ProfileBPredicateIdentifier.RACE_TABLE_SCOPE, ProfileBPredicateOutcome.UNSUPPORTED, race_table_scope_count=0),
            _result(ProfileBPredicateIdentifier.UNIQUE_TARGET_6R, ProfileBPredicateOutcome.UNSUPPORTED, target_race_no=target.race_no, target_6r_row_count=0),
            _result(ProfileBPredicateIdentifier.DEBA_LINK_RELATIONSHIP, ProfileBPredicateOutcome.UNSUPPORTED, deba_relationship_count=0, deba_relationship_present=False),
            _result(ProfileBPredicateIdentifier.DEBA_LINK_QUERY_BINDING, ProfileBPredicateOutcome.UNSUPPORTED, deba_query_binding_count=0, deba_query_binding_match=False),
            _result(ProfileBPredicateIdentifier.WITHDRAWAL_ROW_SHAPE, ProfileBPredicateOutcome.UNSUPPORTED, withdrawal_row_shape_count=0),
            _result(ProfileBPredicateIdentifier.HORSE_14_WITHDRAWAL_ASSOCIATION, ProfileBPredicateOutcome.UNSUPPORTED, withdrawn_provider_horse_no=14, horse_14_withdrawal_count=0, withdrawal_label_match=False),
        ),
    )


def _diagnose_nar_race_entry_status_profile_b(
    *,
    race_list_bytes: bytes,
    target: _raw_capture.NARRaceEntryStatusRaceIdentity,
    result_type: type[ProfileBDiagnostics],
    structural_schedule_domain: bool,
) -> ProfileBDiagnostics:

    canonical_target = _canonical_target(target)
    if type(race_list_bytes) is not bytes:
        raise _validation("race_list_bytes must be exact bytes")
    try:
        source = race_list_bytes.decode("utf-8", errors="strict")
        document = _BeautifulSoup(source, "html.parser")
    except (UnicodeDecodeError, _ParserRejectedMarkup):
        return _unsupported_results(canonical_target, result_type)

    scopes = [node for node in document.select("section.raceTable") if type(node) is _Tag]
    scope_outcome = _outcome(len(scopes))
    scope_result = _result(
        ProfileBPredicateIdentifier.RACE_TABLE_SCOPE,
        scope_outcome,
        race_table_scope_count=len(scopes),
    )

    target_text = f"{canonical_target.race_no}R"
    target_rows: list[_Tag] = []
    malformed_schedule_rows = False
    if scope_outcome is ProfileBPredicateOutcome.PASS:
        schedule_rows = [node for node in scopes[0].select("tr.data") if type(node) is _Tag]
        for row in schedule_rows:
            if structural_schedule_domain and not _is_v2_schedule_domain_row(row, scopes[0]):
                continue
            cells = _direct_cells(row)
            if not cells:
                malformed_schedule_rows = True
                continue
            if _normalized_cell(cells[0]) == target_text:
                target_rows.append(row)
    if scope_outcome is not ProfileBPredicateOutcome.PASS:
        target_outcome = ProfileBPredicateOutcome.UNSUPPORTED
    elif malformed_schedule_rows and not target_rows:
        target_outcome = ProfileBPredicateOutcome.UNSUPPORTED
    else:
        target_outcome = _outcome(len(target_rows))
    target_result = _result(
        ProfileBPredicateIdentifier.UNIQUE_TARGET_6R,
        target_outcome,
        target_race_no=canonical_target.race_no,
        target_6r_row_count=len(target_rows),
    )

    relationship_links: list[str] = []
    href_unsupported = False
    if target_outcome is ProfileBPredicateOutcome.PASS:
        for anchor in target_rows[0].find_all("a", recursive=True):
            if type(anchor) is not _Tag or not anchor.has_attr("href"):
                continue
            href = anchor.get("href")
            if type(href) is not str:
                href_unsupported = True
                continue
            try:
                parsed = urlparse(href)
            except (TypeError, ValueError):
                href_unsupported = True
                continue
            if parsed.path == _DEBA_PATH:
                relationship_links.append(href)
    if target_outcome is not ProfileBPredicateOutcome.PASS:
        relationship_outcome = ProfileBPredicateOutcome.UNSUPPORTED
    elif href_unsupported:
        relationship_outcome = ProfileBPredicateOutcome.UNSUPPORTED
    else:
        relationship_outcome = _outcome(len(relationship_links))
    relationship_result = _result(
        ProfileBPredicateIdentifier.DEBA_LINK_RELATIONSHIP,
        relationship_outcome,
        deba_relationship_count=len(relationship_links),
        deba_relationship_present=len(relationship_links) == 1,
    )

    query_matches = 0
    query_unsupported = False
    if relationship_outcome is ProfileBPredicateOutcome.PASS:
        try:
            query = parse_qs(
                urlparse(relationship_links[0]).query,
                keep_blank_values=True,
                strict_parsing=True,
            )
        except (TypeError, ValueError):
            query_unsupported = True
        else:
            expected = {
                "k_babaCode": [canonical_target.baba_code],
                "k_raceDate": [canonical_target.race_date.strftime("%Y/%m/%d")],
                "k_raceNo": [str(canonical_target.race_no)],
            }
            query_matches = int(query == expected)
    if relationship_outcome is not ProfileBPredicateOutcome.PASS:
        query_outcome = ProfileBPredicateOutcome.UNSUPPORTED
    elif query_unsupported:
        query_outcome = ProfileBPredicateOutcome.UNSUPPORTED
    else:
        query_outcome = _outcome(query_matches)
    query_result = _result(
        ProfileBPredicateIdentifier.DEBA_LINK_QUERY_BINDING,
        query_outcome,
        deba_query_binding_count=query_matches,
        deba_query_binding_match=query_matches == 1,
    )

    change_tables = [node for node in document.select("table.changeInfo") if type(node) is _Tag]
    shaped_rows: list[tuple[_Tag, list[_Tag]]] = []
    malformed_target_shape = False
    for table in change_tables:
        for row in table.select("tr.data"):
            if type(row) is not _Tag:
                continue
            cells = _direct_cells(row)
            if cells and _normalized_cell(cells[0]) == target_text:
                if len(cells) == 6:
                    shaped_rows.append((row, cells))
                else:
                    malformed_target_shape = True
    if not change_tables or (malformed_target_shape and not shaped_rows):
        shape_outcome = ProfileBPredicateOutcome.UNSUPPORTED
    else:
        shape_outcome = _outcome(len(shaped_rows))
    shape_result = _result(
        ProfileBPredicateIdentifier.WITHDRAWAL_ROW_SHAPE,
        shape_outcome,
        withdrawal_row_shape_count=len(shaped_rows),
    )

    association_count = 0
    numeric_unsupported = False
    label_match = False
    if shape_outcome is ProfileBPredicateOutcome.PASS:
        cells = shaped_rows[0][1]
        horse_text = _normalized_cell(cells[1])
        status_text = _normalized_cell(cells[3])
        label_match = status_text == _WITHDRAWAL_LABEL
        if not horse_text.isascii() or not horse_text.isdecimal():
            numeric_unsupported = True
        else:
            association_count = int(int(horse_text) == _WITHDRAWN_HORSE_NO and label_match)
    if shape_outcome is not ProfileBPredicateOutcome.PASS:
        association_outcome = ProfileBPredicateOutcome.UNSUPPORTED
    elif numeric_unsupported:
        association_outcome = ProfileBPredicateOutcome.UNSUPPORTED
    else:
        association_outcome = _outcome(association_count)
    association_result = _result(
        ProfileBPredicateIdentifier.HORSE_14_WITHDRAWAL_ASSOCIATION,
        association_outcome,
        withdrawn_provider_horse_no=_WITHDRAWN_HORSE_NO,
        horse_14_withdrawal_count=association_count,
        withdrawal_label_match=label_match,
    )

    return result_type(
        target=canonical_target,
        predicate_results=(
            scope_result,
            target_result,
            relationship_result,
            query_result,
            shape_result,
            association_result,
        ),
    )


def diagnose_nar_race_entry_status_profile_b(
    *,
    race_list_bytes: bytes,
    target: _raw_capture.NARRaceEntryStatusRaceIdentity,
) -> ProfileBDiagnostics:
    """Evaluate the frozen version 1 six-predicate Profile-B grammar."""

    return _diagnose_nar_race_entry_status_profile_b(
        race_list_bytes=race_list_bytes,
        target=target,
        result_type=ProfileBDiagnostics,
        structural_schedule_domain=False,
    )


def diagnose_nar_race_entry_status_profile_b_v2(
    *,
    race_list_bytes: bytes,
    target: _raw_capture.NARRaceEntryStatusRaceIdentity,
) -> ProfileBDiagnosticsV2:
    """Evaluate Profile-B v2 with structural schedule/change-info separation."""

    result = _diagnose_nar_race_entry_status_profile_b(
        race_list_bytes=race_list_bytes,
        target=target,
        result_type=ProfileBDiagnosticsV2,
        structural_schedule_domain=True,
    )
    if type(result) is not ProfileBDiagnosticsV2:
        raise _validation("Profile-B v2 result type is invalid")
    return result


def _utc_text(value: datetime, field_name: str) -> str:
    if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
        raise _validation(f"{field_name} must be an aware datetime")
    normalized = value.astimezone(timezone.utc)
    return normalized.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _document_metadata(
    capture: _raw_capture.NARRaceEntryStatusResponseCapture,
    role: str,
) -> CaptureDocumentMetadata:
    request = capture.request_identity
    return CaptureDocumentMetadata(
        document_role=role,
        request_identity=request.request_identity,
        capture_identity=capture.capture_id,
        response_sha256=capture.response_sha256,
        response_byte_length=capture.byte_length,
        requested_at=_utc_text(capture.requested_at, f"{role}.requested_at"),
        observed_at=_utc_text(capture.observed_at, f"{role}.observed_at"),
        captured_at=_utc_text(capture.captured_at, f"{role}.captured_at"),
        effective_url_matches_canonical=capture.effective_url == request.canonical_request_url,
    )


def summarize_nar_race_entry_status_capture_bundle(
    *,
    bundle: _raw_capture.NARRaceEntryStatusRawCaptureBundle,
) -> CaptureMetadataSummary:
    """Retain formal Phase44 capture metadata without retaining response bodies."""

    if type(bundle) is not _raw_capture.NARRaceEntryStatusRawCaptureBundle:
        raise _validation("bundle must be exact NARRaceEntryStatusRawCaptureBundle")
    try:
        canonical = _raw_capture.NARRaceEntryStatusRawCaptureBundle(
            target_race_identity=bundle.target_race_identity,
            deba_table_capture=bundle.deba_table_capture,
            race_list_capture=bundle.race_list_capture,
        )
        if bundle.bundle_sha256 != canonical.bundle_sha256 or bundle.bundle_id != canonical.bundle_id:
            raise _validation("bundle derived identity is contradictory")
        return CaptureMetadataSummary(
            deba_table=_document_metadata(canonical.deba_table_capture, "deba_table"),
            race_list=_document_metadata(canonical.race_list_capture, "race_list"),
            closed_bundle_identity=canonical.bundle_id,
        )
    except NARRaceEntryStatusSourceProfileDiagnosticsError:
        raise
    except (_raw_capture.NARRaceEntryStatusRawCaptureError, AttributeError, TypeError) as error:
        raise _validation("bundle metadata is missing or contradictory") from error


__all__ = (
    "CAPTURE_METADATA_SCHEMA",
    "CAPTURE_METADATA_SCHEMA_VERSION",
    "CaptureDocumentMetadata",
    "CaptureMetadataSummary",
    "NARRaceEntryStatusSourceProfileDiagnosticsError",
    "NARRaceEntryStatusSourceProfileDiagnosticsValidationError",
    "PROFILE_B_DIAGNOSTICS_SCHEMA",
    "PROFILE_B_DIAGNOSTICS_SCHEMA_VERSION",
    "PROFILE_B_DIAGNOSTICS_SCHEMA_VERSION_V2",
    "PROFILE_B_TERMINAL_SEMANTIC",
    "ProfileBDiagnostics",
    "ProfileBDiagnosticsV2",
    "ProfileBPredicateIdentifier",
    "ProfileBPredicateOutcome",
    "ProfileBPredicateResult",
    "diagnose_nar_race_entry_status_profile_b",
    "diagnose_nar_race_entry_status_profile_b_v2",
    "summarize_nar_race_entry_status_capture_bundle",
)
