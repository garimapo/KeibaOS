"""Pure NAR source-profile publication contract v2 support."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
import json
import re
from typing import Mapping
from urllib.parse import parse_qsl, urlsplit

from bs4 import BeautifulSoup
from bs4 import ParserRejectedMarkup
from bs4.element import Tag

from scripts.simulation import nar_race_entry_status_raw_capture as _raw_capture
from scripts.simulation.nar_race_entry_status_source_profile_diagnostics import (
    CaptureMetadataSummary,
    ProfileBDiagnostics,
)
from scripts.simulation.nar_race_entry_status_source_profile_profile_a import (
    ProfileADiagnostics,
    _validate_html_structure,
)


FIXTURE_SET_SCHEMA = "nar-race-entry-status-source-profile-fixture-set"
QUALIFICATION_SCHEMA = "nar-race-entry-status-source-profile-qualification"
MANIFEST_SCHEMA = "nar-race-entry-status-source-profile-fixture-manifest"
SCHEMA_VERSION = 2
FIXTURE_ID_PREFIX = "nar-race-entry-status-source-profile-fixture-set-v2:"
QUALIFICATION_ID_PREFIX = "nar-race-entry-status-source-profile-qualification-v2:"
ACQUISITION_SEMANTICS = "CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET"
MARKET_ELIGIBILITY = "UNSUPPORTED"

_ALLOWED_TAGS = ("meta", "input", "form", "a", "link", "script", "img", "iframe")
_URL_ATTRIBUTES = frozenset({"href", "src", "action"})
_PERCENT = re.compile(r"%(?:[0-9A-Fa-f]{2})")
_TOKEN_GROUPS = {
    "NO_AUTHENTICATION_MATERIAL": frozenset(
        {"authorization", "authentication", "password", "credential", "api_key", "access_token", "refresh_token", "bearer"}
    ),
    "NO_COOKIE_OR_SESSION_SECRET": frozenset(
        {"cookie", "set_cookie", "session", "session_id", "sessionid", "sid"}
    ),
    "NO_CSRF_OR_SECRET_TOKEN": frozenset({"csrf", "xsrf", "token", "secret", "nonce"}),
    "NO_USER_ACCOUNT_IDENTIFIER": frozenset(
        {"user", "username", "user_id", "account", "account_id", "member", "member_id", "login_id", "email"}
    ),
    "NO_PERSONALIZATION_IDENTIFIER": frozenset(
        {"personalization", "personalised", "my_page", "mypage", "preference", "favorite", "history"}
    ),
}


class SourceProfilePublicationContractError(Exception):
    """Raised for invalid v2 contract objects or validation mismatches."""


class PublicationSafetyOutcome(StrEnum):
    SAFE = "SAFE"
    UNSAFE = "UNSAFE"
    AMBIGUOUS = "AMBIGUOUS"
    UNSUPPORTED = "UNSUPPORTED"


class PublicationSafetyCategory(StrEnum):
    NO_AUTHENTICATION_MATERIAL = "NO_AUTHENTICATION_MATERIAL"
    NO_COOKIE_OR_SESSION_SECRET = "NO_COOKIE_OR_SESSION_SECRET"
    NO_CSRF_OR_SECRET_TOKEN = "NO_CSRF_OR_SECRET_TOKEN"
    NO_USER_ACCOUNT_IDENTIFIER = "NO_USER_ACCOUNT_IDENTIFIER"
    NO_PERSONALIZATION_IDENTIFIER = "NO_PERSONALIZATION_IDENTIFIER"


def _error(message: str) -> SourceProfilePublicationContractError:
    return SourceProfilePublicationContractError(message)


def _canonical_bytes(payload: object) -> bytes:
    try:
        return json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, OverflowError) as error:
        raise _error("value is not canonically serializable") from error


def _canonical_target(value: object) -> _raw_capture.NARRaceEntryStatusRaceIdentity:
    if type(value) is not _raw_capture.NARRaceEntryStatusRaceIdentity:
        raise _error("target must be exact NARRaceEntryStatusRaceIdentity")
    try:
        return _raw_capture.NARRaceEntryStatusRaceIdentity(
            baba_code=value.baba_code,
            race_date=value.race_date,
            race_no=value.race_no,
        )
    except (_raw_capture.NARRaceEntryStatusRawCaptureError, AttributeError, TypeError) as error:
        raise _error("target identity is malformed") from error


def _target_dict(target: _raw_capture.NARRaceEntryStatusRaceIdentity) -> dict[str, object]:
    return {
        "baba_code": target.baba_code,
        "race_date": target.race_date.isoformat(),
        "race_no": target.race_no,
    }


def _normalize_token(value: str) -> str:
    return value.lower().replace("-", "_")


def _category_for(value: str) -> PublicationSafetyCategory | None:
    normalized = _normalize_token(value)
    for category in PublicationSafetyCategory:
        if normalized in _TOKEN_GROUPS[category.value]:
            return category
    return None


@dataclass(frozen=True, slots=True)
class _SafetyCategoryResult:
    identifier: PublicationSafetyCategory
    outcome: PublicationSafetyOutcome
    finding_count: int

    def __post_init__(self) -> None:
        if type(self.identifier) is not PublicationSafetyCategory:
            raise _error("safety identifier has the wrong type")
        if type(self.outcome) is not PublicationSafetyOutcome:
            raise _error("safety outcome has the wrong type")
        if type(self.finding_count) is not int or not 0 <= self.finding_count <= 10_000:
            raise _error("safety finding_count is invalid")

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "identifier": self.identifier.value,
            "outcome": self.outcome.value,
            "finding_count": self.finding_count,
        }


@dataclass(frozen=True, slots=True)
class RawFixturePublicationSafety:
    category_results: tuple[_SafetyCategoryResult, ...]

    def __post_init__(self) -> None:
        expected = tuple(PublicationSafetyCategory)
        if type(self.category_results) is not tuple or len(self.category_results) != len(expected):
            raise _error("category_results must be the exact five-result tuple")
        if any(type(item) is not _SafetyCategoryResult for item in self.category_results):
            raise _error("category_results contains an unexpected type")
        if tuple(item.identifier for item in self.category_results) != expected:
            raise _error("category_results are outside the frozen order")

    @property
    def result(self) -> PublicationSafetyOutcome:
        outcomes = tuple(item.outcome for item in self.category_results)
        if all(outcome is PublicationSafetyOutcome.SAFE for outcome in outcomes):
            return PublicationSafetyOutcome.SAFE
        if any(outcome is PublicationSafetyOutcome.UNSAFE for outcome in outcomes):
            return PublicationSafetyOutcome.UNSAFE
        if any(outcome is PublicationSafetyOutcome.UNSUPPORTED for outcome in outcomes):
            return PublicationSafetyOutcome.UNSUPPORTED
        return PublicationSafetyOutcome.AMBIGUOUS

    @property
    def raw_fixture_publication_safe(self) -> bool:
        return self.result is PublicationSafetyOutcome.SAFE

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "schema_version": SCHEMA_VERSION,
            "result": self.result.value,
            "raw_fixture_publication_safe": self.raw_fixture_publication_safe,
            "category_results": [item.to_canonical_dict() for item in self.category_results],
        }

    def canonical_bytes(self) -> bytes:
        return _canonical_bytes(self.to_canonical_dict())


def _unsupported_safety() -> RawFixturePublicationSafety:
    return RawFixturePublicationSafety(
        tuple(
            _SafetyCategoryResult(category, PublicationSafetyOutcome.UNSUPPORTED, 0)
            for category in PublicationSafetyCategory
        )
    )


def _malformed_percent(value: str) -> bool:
    index = 0
    while index < len(value):
        if value[index] == "%":
            if _PERCENT.match(value, index) is None:
                return True
            index += 3
        else:
            index += 1
    return False


def assess_nar_race_entry_status_raw_fixture_publication_safety(
    *,
    deba_table_bytes: bytes,
    race_list_bytes: bytes,
) -> RawFixturePublicationSafety:
    """Evaluate exact response bytes without retaining their contents."""

    if type(deba_table_bytes) is not bytes or type(race_list_bytes) is not bytes:
        raise _error("publication safety inputs must be exact bytes")
    unsafe = {category: 0 for category in PublicationSafetyCategory}
    ambiguous = {category: 0 for category in PublicationSafetyCategory}
    try:
        sources = (
            deba_table_bytes.decode("utf-8", errors="strict"),
            race_list_bytes.decode("utf-8", errors="strict"),
        )
        for source in sources:
            _validate_html_structure(source)
            document = BeautifulSoup(source, "html.parser")
            for node in document.find_all(_ALLOWED_TAGS):
                if type(node) is not Tag:
                    continue
                attrs: Mapping[str, object] = node.attrs
                for name, value in attrs.items():
                    category = _category_for(name)
                    if category is not None:
                        if value is None or value == "":
                            ambiguous[category] += 1
                        else:
                            unsafe[category] += 1
                for carrier in ("name", "id"):
                    key = attrs.get(carrier)
                    if type(key) is str:
                        category = _category_for(key)
                        if category is not None:
                            associated = attrs.get("value", attrs.get("content"))
                            if associated is None or associated == "":
                                ambiguous[category] += 1
                            else:
                                unsafe[category] += 1
                for name in _URL_ATTRIBUTES:
                    value = attrs.get(name)
                    if value is None:
                        continue
                    if type(value) is not str:
                        for category in PublicationSafetyCategory:
                            ambiguous[category] += 1
                        continue
                    try:
                        query = urlsplit(value).query
                    except ValueError:
                        for category in PublicationSafetyCategory:
                            ambiguous[category] += 1
                        continue
                    if not query:
                        continue
                    for component in query.split("&"):
                        raw_key = component.split("=", 1)[0]
                        if _malformed_percent(component):
                            category = _category_for(raw_key)
                            targets = (
                                {category}
                                if category is not None
                                else (set(PublicationSafetyCategory) if "%" in raw_key else set())
                            )
                            for target in targets:
                                ambiguous[target] += 1
                            continue
                        try:
                            pairs = parse_qsl(component, keep_blank_values=True, strict_parsing=True)
                        except ValueError:
                            category = _category_for(raw_key)
                            targets = {category} if category is not None else set()
                            for target in targets:
                                ambiguous[target] += 1
                            continue
                        for key, query_value in pairs:
                            category = _category_for(key)
                            if category is None:
                                continue
                            if query_value:
                                unsafe[category] += 1
                            else:
                                ambiguous[category] += 1
            for line in source.splitlines():
                normalized = line.lstrip().lower()
                for prefix, category in (
                    ("authorization:", PublicationSafetyCategory.NO_AUTHENTICATION_MATERIAL),
                    ("cookie:", PublicationSafetyCategory.NO_COOKIE_OR_SESSION_SECRET),
                    ("set-cookie:", PublicationSafetyCategory.NO_COOKIE_OR_SESSION_SECRET),
                ):
                    if normalized.startswith(prefix):
                        if normalized[len(prefix):].strip():
                            unsafe[category] += 1
                        else:
                            ambiguous[category] += 1
    except (UnicodeDecodeError, ValueError, ParserRejectedMarkup):
        return _unsupported_safety()

    results = []
    for category in PublicationSafetyCategory:
        if unsafe[category]:
            outcome = PublicationSafetyOutcome.UNSAFE
        elif ambiguous[category]:
            outcome = PublicationSafetyOutcome.AMBIGUOUS
        else:
            outcome = PublicationSafetyOutcome.SAFE
        results.append(_SafetyCategoryResult(category, outcome, unsafe[category] + ambiguous[category]))
    return RawFixturePublicationSafety(tuple(results))


def _fixture_path(target: _raw_capture.NARRaceEntryStatusRaceIdentity, role: str) -> str:
    return (
        "tests/fixtures/nar_race_entry_status/source_profiles/v2/"
        f"baba_{target.baba_code}__{target.race_date.isoformat()}__race_{target.race_no:02d}/"
        + ("deba_table.html" if role == "deba_table" else "race_list.html")
    )


def _validate_capture_target(
    target: _raw_capture.NARRaceEntryStatusRaceIdentity,
    capture_summary: CaptureMetadataSummary,
) -> None:
    try:
        day_scope = _raw_capture.NARRaceEntryStatusDayScope(target.baba_code, target.race_date)
        deba_request = _raw_capture.build_nar_race_entry_status_request_identity(
            page_kind=_raw_capture.NARRaceEntryStatusPageKind.DEBA_TABLE,
            day_scope=day_scope,
            request_race_no=target.race_no,
        )
        race_list_request = _raw_capture.build_nar_race_entry_status_request_identity(
            page_kind=_raw_capture.NARRaceEntryStatusPageKind.RACE_LIST,
            day_scope=day_scope,
            request_race_no=None,
        )
    except _raw_capture.NARRaceEntryStatusRawCaptureError as error:
        raise _error("capture target authority is malformed") from error
    if capture_summary.deba_table.request_identity != deba_request.request_identity:
        raise _error("DebaTable capture request does not match target")
    if capture_summary.race_list.request_identity != race_list_request.request_identity:
        raise _error("RaceList capture request does not match target")


@dataclass(frozen=True, slots=True)
class FixtureSetV2:
    target: _raw_capture.NARRaceEntryStatusRaceIdentity
    capture_summary: CaptureMetadataSummary

    def __post_init__(self) -> None:
        target = _canonical_target(self.target)
        object.__setattr__(self, "target", target)
        if type(self.capture_summary) is not CaptureMetadataSummary:
            raise _error("capture_summary must be exact CaptureMetadataSummary")
        _validate_capture_target(target, self.capture_summary)

    def to_canonical_dict(self) -> dict[str, object]:
        documents = []
        for role, item in (
            ("deba_table", self.capture_summary.deba_table),
            ("race_list", self.capture_summary.race_list),
        ):
            documents.append(
                {
                    "role": role,
                    "fixture_relative_path": _fixture_path(self.target, role),
                    "request_identity": item.request_identity,
                    "capture_identity": item.capture_identity,
                    "response_sha256": item.response_sha256,
                    "response_byte_length": item.response_byte_length,
                    "requested_at": item.requested_at,
                    "observed_at": item.observed_at,
                    "captured_at": item.captured_at,
                    "effective_url_matches_canonical": item.effective_url_matches_canonical,
                }
            )
        return {
            "schema": FIXTURE_SET_SCHEMA,
            "schema_version": SCHEMA_VERSION,
            "provider": "NAR",
            "target": _target_dict(self.target),
            "documents": documents,
            "closed_bundle_identity": self.capture_summary.closed_bundle_identity,
        }

    def canonical_bytes(self) -> bytes:
        return _canonical_bytes(self.to_canonical_dict())

    @property
    def identity(self) -> str:
        return FIXTURE_ID_PREFIX + sha256(self.canonical_bytes()).hexdigest()


def build_nar_race_entry_status_fixture_set_v2(
    *,
    target: _raw_capture.NARRaceEntryStatusRaceIdentity,
    capture_summary: CaptureMetadataSummary,
) -> FixtureSetV2:
    return FixtureSetV2(target, capture_summary)


def validate_nar_race_entry_status_fixture_set_v2(
    *,
    value: FixtureSetV2,
    target: _raw_capture.NARRaceEntryStatusRaceIdentity,
    capture_summary: CaptureMetadataSummary,
) -> FixtureSetV2:
    if type(value) is not FixtureSetV2:
        raise _error("fixture-set value has the wrong type")
    expected = build_nar_race_entry_status_fixture_set_v2(target=target, capture_summary=capture_summary)
    if value.canonical_bytes() != expected.canonical_bytes() or value.identity != expected.identity:
        raise _error("fixture-set value does not match deterministic authority")
    return value


@dataclass(frozen=True, slots=True)
class QualificationV2:
    target: _raw_capture.NARRaceEntryStatusRaceIdentity
    fixture_set: FixtureSetV2
    profile_a: ProfileADiagnostics
    profile_b: ProfileBDiagnostics

    def __post_init__(self) -> None:
        target = _canonical_target(self.target)
        object.__setattr__(self, "target", target)
        if type(self.fixture_set) is not FixtureSetV2 or self.fixture_set.target != target:
            raise _error("fixture_set target is contradictory")
        if type(self.profile_a) is not ProfileADiagnostics or self.profile_a.target != target:
            raise _error("Profile-A target is contradictory")
        if type(self.profile_b) is not ProfileBDiagnostics or self.profile_b.target != target:
            raise _error("Profile-B target is contradictory")

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "schema": QUALIFICATION_SCHEMA,
            "schema_version": SCHEMA_VERSION,
            "provider": "NAR",
            "target": _target_dict(self.target),
            "fixture_set_identity": self.fixture_set.identity,
            "profile_a": self.profile_a.to_canonical_dict(),
            "profile_b": self.profile_b.to_canonical_dict(),
            "market_eligibility": MARKET_ELIGIBILITY,
        }

    def canonical_bytes(self) -> bytes:
        return _canonical_bytes(self.to_canonical_dict())

    @property
    def identity(self) -> str:
        return QUALIFICATION_ID_PREFIX + sha256(self.canonical_bytes()).hexdigest()


def build_nar_race_entry_status_qualification_v2(
    *,
    target: _raw_capture.NARRaceEntryStatusRaceIdentity,
    fixture_set: FixtureSetV2,
    profile_a: ProfileADiagnostics,
    profile_b: ProfileBDiagnostics,
) -> QualificationV2:
    return QualificationV2(target, fixture_set, profile_a, profile_b)


def validate_nar_race_entry_status_qualification_v2(
    *,
    value: QualificationV2,
    target: _raw_capture.NARRaceEntryStatusRaceIdentity,
    fixture_set: FixtureSetV2,
    profile_a: ProfileADiagnostics,
    profile_b: ProfileBDiagnostics,
) -> QualificationV2:
    if type(value) is not QualificationV2:
        raise _error("qualification value has the wrong type")
    expected = build_nar_race_entry_status_qualification_v2(
        target=target,
        fixture_set=fixture_set,
        profile_a=profile_a,
        profile_b=profile_b,
    )
    if value.canonical_bytes() != expected.canonical_bytes() or value.identity != expected.identity:
        raise _error("qualification value does not match deterministic authority")
    return value


@dataclass(frozen=True, slots=True)
class SourceProfileManifestV2:
    fixture_set: FixtureSetV2
    qualification: QualificationV2
    publication_safety: RawFixturePublicationSafety

    def __post_init__(self) -> None:
        if type(self.fixture_set) is not FixtureSetV2:
            raise _error("manifest fixture_set has the wrong type")
        if type(self.qualification) is not QualificationV2 or self.qualification.fixture_set != self.fixture_set:
            raise _error("manifest qualification is contradictory")
        if type(self.publication_safety) is not RawFixturePublicationSafety:
            raise _error("manifest publication_safety has the wrong type")
        if not self.publication_safety.raw_fixture_publication_safe:
            raise _error("manifest requires publication-safe source")
        if self.qualification.profile_a.overall_result != "QUALIFIED":
            raise _error("manifest requires qualified Profile A")
        if self.qualification.profile_b.overall_result != "QUALIFIED":
            raise _error("manifest requires qualified Profile B")

    def to_canonical_dict(self) -> dict[str, object]:
        fixture_payload = self.fixture_set.to_canonical_dict()
        return {
            "manifest_schema": MANIFEST_SCHEMA,
            "manifest_schema_version": SCHEMA_VERSION,
            "acquisition_semantics": ACQUISITION_SEMANTICS,
            "provider": "NAR",
            "target": fixture_payload["target"],
            "documents": fixture_payload["documents"],
            "closed_bundle_identity": fixture_payload["closed_bundle_identity"],
            "fixture_set_identity": self.fixture_set.identity,
            "qualification_identity": self.qualification.identity,
            "publication_safety": self.publication_safety.to_canonical_dict(),
            "profile_a": self.qualification.profile_a.to_canonical_dict(),
            "profile_b": self.qualification.profile_b.to_canonical_dict(),
            "market_eligibility": MARKET_ELIGIBILITY,
        }

    def canonical_bytes(self) -> bytes:
        return _canonical_bytes(self.to_canonical_dict())


def build_nar_race_entry_status_manifest_v2(
    *,
    fixture_set: FixtureSetV2,
    qualification: QualificationV2,
    publication_safety: RawFixturePublicationSafety,
) -> SourceProfileManifestV2:
    return SourceProfileManifestV2(fixture_set, qualification, publication_safety)


def validate_nar_race_entry_status_manifest_v2(
    *,
    manifest_bytes: bytes,
    fixture_set: FixtureSetV2,
    qualification: QualificationV2,
    publication_safety: RawFixturePublicationSafety,
) -> SourceProfileManifestV2:
    if type(manifest_bytes) is not bytes:
        raise _error("manifest_bytes must be exact bytes")
    expected = build_nar_race_entry_status_manifest_v2(
        fixture_set=fixture_set,
        qualification=qualification,
        publication_safety=publication_safety,
    )
    try:
        payload = json.loads(manifest_bytes.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise _error("manifest bytes are invalid") from error
    if type(payload) is not dict:
        raise _error("manifest root must be an object")
    if manifest_bytes != _canonical_bytes(payload):
        raise _error("manifest bytes are noncanonical")
    if manifest_bytes != expected.canonical_bytes():
        raise _error("manifest does not match deterministic authority")
    return expected


__all__ = (
    "FIXTURE_ID_PREFIX",
    "FIXTURE_SET_SCHEMA",
    "MANIFEST_SCHEMA",
    "MARKET_ELIGIBILITY",
    "QUALIFICATION_ID_PREFIX",
    "QUALIFICATION_SCHEMA",
    "FixtureSetV2",
    "PublicationSafetyCategory",
    "PublicationSafetyOutcome",
    "QualificationV2",
    "RawFixturePublicationSafety",
    "SourceProfileManifestV2",
    "SourceProfilePublicationContractError",
    "assess_nar_race_entry_status_raw_fixture_publication_safety",
    "build_nar_race_entry_status_fixture_set_v2",
    "build_nar_race_entry_status_manifest_v2",
    "build_nar_race_entry_status_qualification_v2",
    "validate_nar_race_entry_status_fixture_set_v2",
    "validate_nar_race_entry_status_manifest_v2",
    "validate_nar_race_entry_status_qualification_v2",
)
