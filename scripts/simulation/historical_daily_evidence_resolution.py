"""Immutable provider-neutral daily evidence resolution, not replay results."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass
from datetime import datetime as _datetime, timezone as _timezone
from enum import StrEnum as _StrEnum
import re as _re
from unicodedata import normalize as _normalize
from urllib.parse import urlsplit as _urlsplit

from scripts.simulation.historical_daily_targets import (
    DailyHistoricalReplayTarget as _Target,
    DailyHistoricalReplayTargetSet as _TargetSet,
)
from scripts.simulation.historical_input_snapshots import HistoricalInputSnapshotIdentity as _SnapshotIdentity


def _text(value: object, name: str) -> str:
    if type(value) is not str or not value or value != value.strip() or value != _normalize("NFC", value):
        raise ValueError(f"{name} must be nonempty canonical text")
    return value


def _digest(value: object) -> str:
    if type(value) is not str or _re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError("digest must be lowercase SHA-256")
    return value


def _utc(value: object) -> _datetime:
    if type(value) is not _datetime or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be an aware datetime")
    return value.astimezone(_timezone.utc)


def _key(target: _Target) -> tuple[str, str, str]:
    return target.provider_identity.organization, target.provider_identity.source_system, target.external_race_id


class DailyHistoricalReplayEvidenceDisposition(_StrEnum):
    EXECUTABLE = "EXECUTABLE"
    MISSING_PREDICTION_EVIDENCE = "MISSING_PREDICTION_EVIDENCE"
    MISSING_SETTLEMENT_EVIDENCE = "MISSING_SETTLEMENT_EVIDENCE"
    UNSUPPORTED = "UNSUPPORTED"
    INVALID_EVIDENCE = "INVALID_EVIDENCE"


class DailyHistoricalReplayResolutionState(_StrEnum):
    ALL_TARGETS_RESOLVED = "ALL_TARGETS_RESOLVED"
    PARTIALLY_RESOLVED = "PARTIALLY_RESOLVED"
    NO_EXECUTABLE_TARGETS = "NO_EXECUTABLE_TARGETS"


@_dataclass(frozen=True, slots=True)
class DailyHistoricalReplayCaptureReference:
    capture_id: str
    canonical_source_url: str
    response_sha256: str
    observed_at: _datetime

    def __post_init__(self) -> None:
        _text(self.capture_id, "capture_id")
        url = _text(self.canonical_source_url, "canonical_source_url")
        if any(char.isspace() or ord(char) < 32 for char in url):
            raise ValueError("capture URL contains whitespace/control characters")
        parsed = _urlsplit(url)
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username is not None
                or parsed.password is not None or parsed.fragment):
            raise ValueError("capture URL must be HTTPS without credentials or fragment")
        _ = parsed.port
        _digest(self.response_sha256)
        object.__setattr__(self, "observed_at", _utc(self.observed_at))


@_dataclass(frozen=True, slots=True)
class DailyHistoricalReplayTargetOutcome:
    target: _Target
    disposition: DailyHistoricalReplayEvidenceDisposition
    reason_codes: tuple[str, ...]
    internal_race_id: int | None
    snapshot_identity: _SnapshotIdentity | None
    snapshot_content_sha256: str | None
    result_capture_reference: DailyHistoricalReplayCaptureReference | None
    payout_capture_reference: DailyHistoricalReplayCaptureReference | None

    def __post_init__(self) -> None:
        if type(self.target) is not _Target or type(self.disposition) is not DailyHistoricalReplayEvidenceDisposition:
            raise ValueError("target and disposition must be exact domain types")
        if type(self.reason_codes) is not tuple:
            raise ValueError("reason_codes must be a tuple")
        for reason in self.reason_codes:
            _text(reason, "reason code")
        if len(set(self.reason_codes)) != len(self.reason_codes):
            raise ValueError("reason codes are duplicated")
        object.__setattr__(self, "reason_codes", tuple(sorted(self.reason_codes)))
        if self.internal_race_id is not None and (type(self.internal_race_id) is not int or self.internal_race_id <= 0):
            raise ValueError("internal_race_id must be a positive int or None")
        if (self.snapshot_identity is None) != (self.snapshot_content_sha256 is None):
            raise ValueError("snapshot identity and digest must be present together")
        if self.snapshot_identity is not None:
            if type(self.snapshot_identity) is not _SnapshotIdentity or self.internal_race_id is None:
                raise ValueError("snapshot requires exact identity and internal linkage")
            _digest(self.snapshot_content_sha256)
            source = self.snapshot_identity.source_identity
            if (source.organization, source.source_system, source.external_race_id) != _key(self.target):
                raise ValueError("snapshot identity disagrees with target")
        for reference in (self.result_capture_reference, self.payout_capture_reference):
            if reference is not None and type(reference) is not DailyHistoricalReplayCaptureReference:
                raise ValueError("capture reference must be exact domain type or None")
        if self.disposition is DailyHistoricalReplayEvidenceDisposition.EXECUTABLE:
            if (self.reason_codes or self.target.scheduled_start_at is None or self.snapshot_identity is None
                    or self.result_capture_reference is None or self.payout_capture_reference is None):
                raise ValueError("executable target requires all references, exact start and no reasons")
        elif not self.reason_codes:
            raise ValueError("non-executable target requires a reason")


@_dataclass(frozen=True, slots=True)
class DailyHistoricalReplayEvidenceResolution:
    target_set: _TargetSet
    dataset_id: str
    selection_policy: str
    settlement_information_cutoff: _datetime
    outcomes: tuple[DailyHistoricalReplayTargetOutcome, ...]

    def __post_init__(self) -> None:
        if type(self.target_set) is not _TargetSet or not self.target_set.target_races:
            raise ValueError("resolution requires a nonempty exact target set")
        _text(self.dataset_id, "dataset_id")
        if type(self.selection_policy) is not str or self.selection_policy != "LATEST_CAUSAL_IN_DATASET":
            raise ValueError("unsupported selection policy")
        cutoff = _utc(self.settlement_information_cutoff)
        object.__setattr__(self, "settlement_information_cutoff", cutoff)
        if type(self.outcomes) is not tuple or any(type(item) is not DailyHistoricalReplayTargetOutcome for item in self.outcomes):
            raise ValueError("outcomes must be a tuple of exact outcomes")
        keyed = {_key(item.target): item for item in self.outcomes}
        if len(keyed) != len(self.outcomes):
            raise ValueError("duplicate target outcome")
        targets = self.target_set.target_races
        if set(keyed) != {_key(target) for target in targets}:
            raise ValueError("outcomes must cover the original denominator exactly")
        for target in targets:
            outcome = keyed[_key(target)]
            if outcome.target != target:
                raise ValueError("outcome target content is contradictory")
            if outcome.snapshot_identity is not None and outcome.snapshot_identity.dataset_id != self.dataset_id:
                raise ValueError("snapshot dataset is contradictory")
            for reference in (outcome.result_capture_reference, outcome.payout_capture_reference):
                if reference is not None and reference.observed_at > cutoff:
                    raise ValueError("capture exceeds settlement cutoff")
        object.__setattr__(self, "outcomes", tuple(keyed[_key(target)] for target in targets))

    @property
    def day_state(self) -> DailyHistoricalReplayResolutionState:
        executable = sum(item.disposition is DailyHistoricalReplayEvidenceDisposition.EXECUTABLE for item in self.outcomes)
        if executable == len(self.outcomes):
            return DailyHistoricalReplayResolutionState.ALL_TARGETS_RESOLVED
        if executable:
            return DailyHistoricalReplayResolutionState.PARTIALLY_RESOLVED
        return DailyHistoricalReplayResolutionState.NO_EXECUTABLE_TARGETS


if "annotations" in globals():
    del annotations
