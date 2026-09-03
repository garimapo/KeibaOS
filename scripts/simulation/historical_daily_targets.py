"""Provider-neutral audited historical daily target contracts."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass, field as _field
from datetime import date as _date, datetime as _datetime, timezone as _timezone
from enum import StrEnum as _StrEnum
import hashlib as _hashlib
import json as _json
import re as _re
from unicodedata import normalize as _normalize


_SHA256 = _re.compile(r"[0-9a-f]{64}\Z")


class DailyTargetDiscoveryFailureCode(_StrEnum):
    """Stable fail-closed daily target discovery outcomes."""

    UNSUPPORTED_TARGET_DATE = "UNSUPPORTED_TARGET_DATE"
    MISSING_ENVELOPE_EVIDENCE = "MISSING_ENVELOPE_EVIDENCE"
    INVALID_OFFICIAL_REQUEST_IDENTITY = "INVALID_OFFICIAL_REQUEST_IDENTITY"
    DUPLICATE_EVIDENCE = "DUPLICATE_EVIDENCE"
    MISSING_PARTITION_EVIDENCE = "MISSING_PARTITION_EVIDENCE"
    MALFORMED_OFFICIAL_EVIDENCE = "MALFORMED_OFFICIAL_EVIDENCE"
    UNSUPPORTED_ENVELOPE_STATE = "UNSUPPORTED_ENVELOPE_STATE"
    UNSUPPORTED_NATIVE_DISPOSITION = "UNSUPPORTED_NATIVE_DISPOSITION"
    CONTRADICTORY_EVIDENCE = "CONTRADICTORY_EVIDENCE"
    COVERAGE_SET_MISMATCH = "COVERAGE_SET_MISMATCH"
    MISSING_SCHEDULED_START = "MISSING_SCHEDULED_START"


class DailyHistoricalTargetValidationError(ValueError):
    """Raised for malformed provider-neutral API values."""


class DailyHistoricalTargetIntegrityError(RuntimeError):
    """Raised when purported immutable evidence is corrupt or contradictory."""


class TargetDiscoveryIncompleteError(RuntimeError):
    """Raised instead of returning a partial daily denominator."""

    def __init__(
        self,
        code: DailyTargetDiscoveryFailureCode,
        message: str,
        *,
        evidence_references: tuple[str, ...] = (),
    ) -> None:
        if type(code) is not DailyTargetDiscoveryFailureCode:
            raise DailyHistoricalTargetValidationError("code must be DailyTargetDiscoveryFailureCode")
        if type(message) is not str or not message:
            raise DailyHistoricalTargetValidationError("message must be a non-empty str")
        if type(evidence_references) is not tuple or any(
            type(item) is not str or not item for item in evidence_references
        ):
            raise DailyHistoricalTargetValidationError("evidence_references must contain non-empty str values")
        self.code = code
        self.evidence_references = tuple(sorted(evidence_references))
        super().__init__(f"{code.value}: {message}")


def _text(value: object, name: str) -> str:
    if type(value) is not str or not value:
        raise DailyHistoricalTargetValidationError(f"{name} must be a non-empty str")
    if value != _normalize("NFC", value) or value != value.strip():
        raise DailyHistoricalTargetValidationError(f"{name} must be exact NFC text without surrounding whitespace")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise DailyHistoricalTargetValidationError(f"{name} must not contain control characters")
    return value


def _sha256(value: object, name: str) -> str:
    value = _text(value, name)
    if _SHA256.fullmatch(value) is None:
        raise DailyHistoricalTargetValidationError(f"{name} must be lowercase SHA-256")
    return value


def _date_value(value: object, name: str) -> _date:
    if type(value) is not _date:
        raise DailyHistoricalTargetValidationError(f"{name} must be exact date")
    return value


def _utc(value: object, name: str) -> _datetime:
    if type(value) is not _datetime:
        raise DailyHistoricalTargetValidationError(f"{name} must be exact datetime")
    try:
        if value.tzinfo is None or value.utcoffset() is None:
            raise DailyHistoricalTargetValidationError(f"{name} must be timezone-aware")
        return value.astimezone(_timezone.utc)
    except DailyHistoricalTargetValidationError:
        raise
    except (OverflowError, TypeError, ValueError) as error:
        raise DailyHistoricalTargetValidationError(f"{name} cannot be converted to UTC") from error


def _optional_utc(value: object, name: str) -> _datetime | None:
    return None if value is None else _utc(value, name)


def _tuple(value: object, name: str) -> tuple[object, ...]:
    if type(value) is not tuple:
        raise DailyHistoricalTargetValidationError(f"{name} must be tuple")
    return value


def _canonical_datetime(value: _datetime) -> str:
    return value.astimezone(_timezone.utc).isoformat(timespec="microseconds")


def _canonical_bytes(payload: dict[str, object]) -> bytes:
    return _json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


@_dataclass(frozen=True, slots=True, order=True)
class HistoricalDailyProviderIdentity:
    organization: str
    source_system: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "organization", _text(self.organization, "organization"))
        object.__setattr__(self, "source_system", _text(self.source_system, "source_system"))


@_dataclass(frozen=True, slots=True)
class DailyHistoricalReplayProviderScope:
    providers: tuple[HistoricalDailyProviderIdentity, ...]

    def __post_init__(self) -> None:
        values = _tuple(self.providers, "providers")
        if not values:
            raise DailyHistoricalTargetValidationError("providers must not be empty")
        if any(type(item) is not HistoricalDailyProviderIdentity for item in values):
            raise DailyHistoricalTargetValidationError("providers items must be HistoricalDailyProviderIdentity")
        if len(set(values)) != len(values):
            raise DailyHistoricalTargetValidationError("providers must be unique")
        object.__setattr__(self, "providers", tuple(sorted(values)))


@_dataclass(frozen=True, slots=True)
class ProviderNativeDispositionEvidenceReference:
    evidence_kind_and_version: str
    exact_capture_or_reference_identity: str
    content_sha256: str
    structural_locator: str
    native_value_sha256: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_kind_and_version", _text(self.evidence_kind_and_version, "evidence_kind_and_version"))
        object.__setattr__(
            self,
            "exact_capture_or_reference_identity",
            _text(self.exact_capture_or_reference_identity, "exact_capture_or_reference_identity"),
        )
        object.__setattr__(self, "content_sha256", _sha256(self.content_sha256, "content_sha256"))
        object.__setattr__(self, "structural_locator", _text(self.structural_locator, "structural_locator"))
        object.__setattr__(self, "native_value_sha256", _sha256(self.native_value_sha256, "native_value_sha256"))


@_dataclass(frozen=True, slots=True)
class DailyHistoricalReplayCompletenessEvidence:
    provider_identity: HistoricalDailyProviderIdentity
    evidence_kind_and_version: str
    exact_capture_or_reference_identity: str
    canonical_source_or_request_identity: str
    content_sha256: str
    observed_at: _datetime
    provider_available_at: _datetime | None
    coverage_identity: str

    def __post_init__(self) -> None:
        if type(self.provider_identity) is not HistoricalDailyProviderIdentity:
            raise DailyHistoricalTargetValidationError("provider_identity must be HistoricalDailyProviderIdentity")
        for name in (
            "evidence_kind_and_version",
            "exact_capture_or_reference_identity",
            "canonical_source_or_request_identity",
            "coverage_identity",
        ):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(self, "content_sha256", _sha256(self.content_sha256, "content_sha256"))
        observed = _utc(self.observed_at, "observed_at")
        available = _optional_utc(self.provider_available_at, "provider_available_at")
        if available is not None and available > observed:
            raise DailyHistoricalTargetValidationError("provider_available_at must not be later than observed_at")
        object.__setattr__(self, "observed_at", observed)
        object.__setattr__(self, "provider_available_at", available)


def _evidence_key(value: DailyHistoricalReplayCompletenessEvidence) -> tuple[str, ...]:
    provider = value.provider_identity
    return (
        provider.organization,
        provider.source_system,
        value.coverage_identity,
        value.evidence_kind_and_version,
        value.canonical_source_or_request_identity,
        value.exact_capture_or_reference_identity,
    )


@_dataclass(frozen=True, slots=True)
class DailyHistoricalReplayTarget:
    provider_identity: HistoricalDailyProviderIdentity
    external_race_id: str
    scheduled_start_at: _datetime | None
    provider_disposition_evidence: ProviderNativeDispositionEvidenceReference

    def __post_init__(self) -> None:
        if type(self.provider_identity) is not HistoricalDailyProviderIdentity:
            raise DailyHistoricalTargetValidationError("provider_identity must be HistoricalDailyProviderIdentity")
        object.__setattr__(self, "external_race_id", _text(self.external_race_id, "external_race_id"))
        object.__setattr__(self, "scheduled_start_at", _optional_utc(self.scheduled_start_at, "scheduled_start_at"))
        if type(self.provider_disposition_evidence) is not ProviderNativeDispositionEvidenceReference:
            raise DailyHistoricalTargetValidationError(
                "provider_disposition_evidence must be ProviderNativeDispositionEvidenceReference"
            )


def _target_key(value: DailyHistoricalReplayTarget) -> tuple[str, str, str]:
    provider = value.provider_identity
    return provider.organization, provider.source_system, value.external_race_id


@_dataclass(frozen=True, slots=True)
class HistoricalDailyTargetEvidenceBundle:
    provider_identity: HistoricalDailyProviderIdentity
    target_date: _date
    target_races: tuple[DailyHistoricalReplayTarget, ...]
    completeness_evidence: tuple[DailyHistoricalReplayCompletenessEvidence, ...]

    def __post_init__(self) -> None:
        if type(self.provider_identity) is not HistoricalDailyProviderIdentity:
            raise DailyHistoricalTargetValidationError("provider_identity must be HistoricalDailyProviderIdentity")
        object.__setattr__(self, "target_date", _date_value(self.target_date, "target_date"))
        targets = _tuple(self.target_races, "target_races")
        evidence = _tuple(self.completeness_evidence, "completeness_evidence")
        if not evidence:
            raise DailyHistoricalTargetValidationError("completeness_evidence must not be empty")
        if any(type(item) is not DailyHistoricalReplayTarget for item in targets):
            raise DailyHistoricalTargetValidationError("target_races items must be DailyHistoricalReplayTarget")
        if any(type(item) is not DailyHistoricalReplayCompletenessEvidence for item in evidence):
            raise DailyHistoricalTargetValidationError(
                "completeness_evidence items must be DailyHistoricalReplayCompletenessEvidence"
            )
        if any(item.provider_identity != self.provider_identity for item in targets + evidence):
            raise DailyHistoricalTargetValidationError("bundle provider identity is contradictory")
        target_keys = tuple(_target_key(item) for item in targets)
        evidence_keys = tuple(_evidence_key(item) for item in evidence)
        if len(set(target_keys)) != len(target_keys):
            raise DailyHistoricalTargetValidationError("target_races contain duplicate identity")
        if len(set(evidence_keys)) != len(evidence_keys):
            raise DailyHistoricalTargetValidationError("completeness_evidence contains duplicate identity")
        object.__setattr__(self, "target_races", tuple(sorted(targets, key=_target_key)))
        object.__setattr__(self, "completeness_evidence", tuple(sorted(evidence, key=_evidence_key)))


@_dataclass(frozen=True, slots=True)
class DailyHistoricalReplayTargetSet:
    target_date: _date
    provider_scope: DailyHistoricalReplayProviderScope
    target_races: tuple[DailyHistoricalReplayTarget, ...]
    completeness_evidence: tuple[DailyHistoricalReplayCompletenessEvidence, ...]
    content_sha256: str = _field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "target_date", _date_value(self.target_date, "target_date"))
        if type(self.provider_scope) is not DailyHistoricalReplayProviderScope:
            raise DailyHistoricalTargetValidationError("provider_scope must be DailyHistoricalReplayProviderScope")
        targets = _tuple(self.target_races, "target_races")
        evidence = _tuple(self.completeness_evidence, "completeness_evidence")
        if not evidence:
            raise DailyHistoricalTargetValidationError("completeness_evidence must not be empty")
        if any(type(item) is not DailyHistoricalReplayTarget for item in targets):
            raise DailyHistoricalTargetValidationError("target_races items must be DailyHistoricalReplayTarget")
        if any(type(item) is not DailyHistoricalReplayCompletenessEvidence for item in evidence):
            raise DailyHistoricalTargetValidationError(
                "completeness_evidence items must be DailyHistoricalReplayCompletenessEvidence"
            )
        target_keys = tuple(_target_key(item) for item in targets)
        evidence_keys = tuple(_evidence_key(item) for item in evidence)
        if len(set(target_keys)) != len(target_keys):
            raise DailyHistoricalTargetValidationError("target_races contain duplicate identity")
        if len(set(evidence_keys)) != len(evidence_keys):
            raise DailyHistoricalTargetValidationError("completeness_evidence contains duplicate identity")
        canonical_targets = tuple(sorted(targets, key=_target_key))
        canonical_evidence = tuple(sorted(evidence, key=_evidence_key))
        scope = set(self.provider_scope.providers)
        if any(item.provider_identity not in scope for item in canonical_targets + canonical_evidence):
            raise DailyHistoricalTargetValidationError("target-set content falls outside provider_scope")
        if {item.provider_identity for item in canonical_evidence} != scope:
            raise DailyHistoricalTargetValidationError("completeness_evidence does not exactly cover provider_scope")
        object.__setattr__(self, "target_races", canonical_targets)
        object.__setattr__(self, "completeness_evidence", canonical_evidence)
        object.__setattr__(self, "content_sha256", _hashlib.sha256(_target_set_bytes(self)).hexdigest())


def _target_set_bytes(value: DailyHistoricalReplayTargetSet) -> bytes:
    return _canonical_bytes(
        {
            "completeness_evidence": [
                {
                    "canonical_source_or_request_identity": item.canonical_source_or_request_identity,
                    "content_sha256": item.content_sha256,
                    "coverage_identity": item.coverage_identity,
                    "evidence_kind_and_version": item.evidence_kind_and_version,
                    "exact_capture_or_reference_identity": item.exact_capture_or_reference_identity,
                    "observed_at_utc": _canonical_datetime(item.observed_at),
                    "organization": item.provider_identity.organization,
                    "provider_available_at_utc": (
                        None if item.provider_available_at is None else _canonical_datetime(item.provider_available_at)
                    ),
                    "source_system": item.provider_identity.source_system,
                }
                for item in value.completeness_evidence
            ],
            "provider_scope": [
                {"organization": item.organization, "source_system": item.source_system}
                for item in value.provider_scope.providers
            ],
            "schema_version": 1,
            "target_date": value.target_date.isoformat(),
            "target_races": [
                {
                    "external_race_id": item.external_race_id,
                    "organization": item.provider_identity.organization,
                    "provider_disposition_evidence": {
                        "content_sha256": item.provider_disposition_evidence.content_sha256,
                        "evidence_kind_and_version": item.provider_disposition_evidence.evidence_kind_and_version,
                        "exact_capture_or_reference_identity": (
                            item.provider_disposition_evidence.exact_capture_or_reference_identity
                        ),
                        "native_value_sha256": item.provider_disposition_evidence.native_value_sha256,
                        "structural_locator": item.provider_disposition_evidence.structural_locator,
                    },
                    "scheduled_start_at_utc": (
                        None if item.scheduled_start_at is None else _canonical_datetime(item.scheduled_start_at)
                    ),
                    "source_system": item.provider_identity.source_system,
                }
                for item in value.target_races
            ],
        }
    )


def build_daily_historical_replay_target_set(
    *,
    target_date: _date,
    provider_scope: DailyHistoricalReplayProviderScope,
    evidence_bundles: tuple[HistoricalDailyTargetEvidenceBundle, ...],
) -> DailyHistoricalReplayTargetSet:
    """Build one immutable complete denominator from exact provider bundles."""

    target_date = _date_value(target_date, "target_date")
    if type(provider_scope) is not DailyHistoricalReplayProviderScope:
        raise DailyHistoricalTargetValidationError("provider_scope must be DailyHistoricalReplayProviderScope")
    bundles = _tuple(evidence_bundles, "evidence_bundles")
    if any(type(item) is not HistoricalDailyTargetEvidenceBundle for item in bundles):
        raise DailyHistoricalTargetValidationError("evidence_bundles items must be HistoricalDailyTargetEvidenceBundle")
    bundle_providers = tuple(item.provider_identity for item in bundles)
    if len(set(bundle_providers)) != len(bundle_providers):
        raise TargetDiscoveryIncompleteError(
            DailyTargetDiscoveryFailureCode.DUPLICATE_EVIDENCE,
            "provider bundle identity is duplicated",
        )
    if set(bundle_providers) != set(provider_scope.providers):
        raise TargetDiscoveryIncompleteError(
            DailyTargetDiscoveryFailureCode.MISSING_ENVELOPE_EVIDENCE,
            "provider bundles do not exactly cover the closed scope",
        )
    if any(item.target_date != target_date for item in bundles):
        raise TargetDiscoveryIncompleteError(
            DailyTargetDiscoveryFailureCode.CONTRADICTORY_EVIDENCE,
            "bundle target_date is contradictory",
        )
    targets = tuple(item for bundle in bundles for item in bundle.target_races)
    evidence = tuple(item for bundle in bundles for item in bundle.completeness_evidence)
    return DailyHistoricalReplayTargetSet(target_date, provider_scope, targets, evidence)


if "annotations" in globals():
    del annotations
