"""Pure, target-complete NAR historical entry-status readiness authority."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass
from datetime import datetime as _datetime, timezone as _timezone
from enum import StrEnum as _StrEnum
import re as _re

from scripts.simulation.historical_daily_targets import (
    DailyHistoricalReplayTarget as _Target,
    DailyHistoricalReplayTargetSet as _TargetSet,
)


__all__ = (
    "NARHistoricalEntryStatusAuthority",
    "NARHistoricalEntryStatusAuthoritySet",
    "NARHistoricalEntryStatusCoverage",
    "NARHistoricalEntryStatusTimestampProvenance",
    "NARHistoricalReplayEligibilityDecision",
    "NARHistoricalReplayEligibilityResolution",
    "NARHistoricalReplayEligibilityState",
    "resolve_nar_historical_replay_eligibility",
)


_SHA256 = _re.compile(r"[0-9a-f]{64}\Z", flags=_re.ASCII)
_PROVIDER = ("NAR", "nar_official")
_BLOCKER = "HISTORICAL_REPLAY_BLOCKED_ENTRY_STATUS_AUTHORITY_UNAVAILABLE"
_MISSING = "COMPLETE_PRE_CUTOFF_ENTRY_STATUS_UNIVERSE"


def _text(value: object, name: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise ValueError(f"{name} must be nonempty exact text")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ValueError(f"{name} contains a control character")
    return value


def _digest(value: object, name: str) -> str:
    if type(value) is not str or _SHA256.fullmatch(value) is None:
        raise ValueError(f"{name} must be lowercase SHA-256")
    return value


def _utc(value: object, name: str) -> _datetime:
    if type(value) is not _datetime or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be an exact aware datetime")
    return value.astimezone(_timezone.utc)


def _key(target: _Target) -> tuple[str, str, str]:
    provider = target.provider_identity
    return provider.organization, provider.source_system, target.external_race_id


def _nar_target(target: object) -> _Target:
    if type(target) is not _Target or _key(target)[:2] != _PROVIDER:
        raise ValueError("target must be an exact NAR/nar_official target")
    return target


def _target_set(value: object) -> _TargetSet:
    if type(value) is not _TargetSet or not value.target_races:
        raise ValueError("target_set must be an exact nonempty target set")
    if tuple((item.organization, item.source_system) for item in value.provider_scope.providers) != (_PROVIDER,):
        raise ValueError("target_set must have exact NAR/nar_official scope")
    for target in value.target_races:
        _nar_target(target)
    return value


class NARHistoricalEntryStatusCoverage(_StrEnum):
    COMPLETE_PRE_CUTOFF_ENTRY_STATUS_UNIVERSE = "COMPLETE_PRE_CUTOFF_ENTRY_STATUS_UNIVERSE"


class NARHistoricalEntryStatusTimestampProvenance(_StrEnum):
    PROVIDER_PUBLICATION_AVAILABILITY = "PROVIDER_PUBLICATION_AVAILABILITY"
    INDEPENDENT_ARCHIVE_OBSERVATION = "INDEPENDENT_ARCHIVE_OBSERVATION"


class NARHistoricalReplayEligibilityState(_StrEnum):
    ELIGIBLE_WITH_PRE_CUTOFF_ENTRY_STATUS_AUTHORITY = "ELIGIBLE_WITH_PRE_CUTOFF_ENTRY_STATUS_AUTHORITY"
    BLOCKED_ENTRY_STATUS_AUTHORITY_UNAVAILABLE = "BLOCKED_ENTRY_STATUS_AUTHORITY_UNAVAILABLE"


@_dataclass(frozen=True, slots=True)
class NARHistoricalEntryStatusAuthority:
    target: _Target
    authority_identity: str
    canonical_source_identity: str
    response_sha256: str
    availability_proof_identity: str
    timestamp_provenance: NARHistoricalEntryStatusTimestampProvenance
    available_at: _datetime
    observed_at: _datetime
    coverage_semantic: NARHistoricalEntryStatusCoverage
    entry_universe_identity: str
    covered_entry_universe_identity: str

    def __post_init__(self) -> None:
        _nar_target(self.target)
        for name in (
            "authority_identity", "canonical_source_identity", "availability_proof_identity",
            "entry_universe_identity", "covered_entry_universe_identity",
        ):
            _text(getattr(self, name), name)
        _digest(self.response_sha256, "response_sha256")
        if type(self.timestamp_provenance) is not NARHistoricalEntryStatusTimestampProvenance:
            raise ValueError("timestamp provenance must be a closed authority value")
        if type(self.coverage_semantic) is not NARHistoricalEntryStatusCoverage:
            raise ValueError("coverage semantic must be the complete closed authority value")
        if self.entry_universe_identity != self.covered_entry_universe_identity:
            raise ValueError("status coverage does not identify the complete entry universe")
        available = _utc(self.available_at, "available_at")
        observed = _utc(self.observed_at, "observed_at")
        if available > observed:
            raise ValueError("availability cannot follow observation")
        if (
            self.timestamp_provenance
            is NARHistoricalEntryStatusTimestampProvenance.INDEPENDENT_ARCHIVE_OBSERVATION
            and available != observed
        ):
            raise ValueError("archive availability must equal its independent observation")
        object.__setattr__(self, "available_at", available)
        object.__setattr__(self, "observed_at", observed)


@_dataclass(frozen=True, slots=True)
class NARHistoricalEntryStatusAuthoritySet:
    target_set: _TargetSet
    authorities: tuple[NARHistoricalEntryStatusAuthority, ...]

    def __post_init__(self) -> None:
        _target_set(self.target_set)
        if type(self.authorities) is not tuple or any(
            type(item) is not NARHistoricalEntryStatusAuthority for item in self.authorities
        ):
            raise ValueError("authorities must be a tuple of exact authority values")
        targets = {_key(item): item for item in self.target_set.target_races}
        by_key: dict[tuple[str, str, str], NARHistoricalEntryStatusAuthority] = {}
        for authority in self.authorities:
            key = _key(authority.target)
            if key not in targets or authority.target != targets[key]:
                raise ValueError("authority target falls outside the exact canonical target set")
            if key in by_key:
                raise ValueError("duplicate target authority")
            by_key[key] = authority
        object.__setattr__(self, "authorities", tuple(by_key[_key(item)] for item in self.target_set.target_races if _key(item) in by_key))


@_dataclass(frozen=True, slots=True)
class NARHistoricalReplayEligibilityDecision:
    target: _Target
    eligibility: NARHistoricalReplayEligibilityState
    blocker_classification: str | None
    missing_authority: str | None
    causal_reason: str

    def __post_init__(self) -> None:
        _nar_target(self.target)
        if type(self.eligibility) is not NARHistoricalReplayEligibilityState:
            raise ValueError("eligibility must be an exact closed value")
        if self.eligibility is NARHistoricalReplayEligibilityState.BLOCKED_ENTRY_STATUS_AUTHORITY_UNAVAILABLE:
            if self.blocker_classification != _BLOCKER or self.missing_authority != _MISSING:
                raise ValueError("blocked decision must carry the exact missing authority")
        elif self.blocker_classification is not None or self.missing_authority is not None:
            raise ValueError("eligible decision cannot carry a blocker")
        _text(self.causal_reason, "causal_reason")


@_dataclass(frozen=True, slots=True)
class NARHistoricalReplayEligibilityResolution:
    target_set: _TargetSet
    decisions: tuple[NARHistoricalReplayEligibilityDecision, ...]

    def __post_init__(self) -> None:
        _target_set(self.target_set)
        if type(self.decisions) is not tuple or len(self.decisions) != len(self.target_set.target_races):
            raise ValueError("decisions must cover the complete target set")
        if any(type(item) is not NARHistoricalReplayEligibilityDecision for item in self.decisions):
            raise ValueError("decisions must have exact types")
        if tuple(item.target for item in self.decisions) != self.target_set.target_races:
            raise ValueError("decisions must retain canonical target order and identity")

    @property
    def all_eligible(self) -> bool:
        return all(
            item.eligibility is NARHistoricalReplayEligibilityState.ELIGIBLE_WITH_PRE_CUTOFF_ENTRY_STATUS_AUTHORITY
            for item in self.decisions
        )


def resolve_nar_historical_replay_eligibility(
    *, target_set: _TargetSet, historical_entry_status_authorities: NARHistoricalEntryStatusAuthoritySet,
) -> NARHistoricalReplayEligibilityResolution:
    """Resolve only explicit pre-cutoff complete status authority, without I/O."""
    targets = _target_set(target_set)
    supplied = historical_entry_status_authorities
    if type(supplied) is not NARHistoricalEntryStatusAuthoritySet or supplied.target_set is not targets:
        raise ValueError("historical authority must retain the exact canonical target set")
    # Rebuild the public value so forged frozen members cannot bypass its invariants.
    supplied = NARHistoricalEntryStatusAuthoritySet(
        targets,
        tuple(NARHistoricalEntryStatusAuthority(**{
            name: getattr(item, name) for name in NARHistoricalEntryStatusAuthority.__dataclass_fields__
        }) for item in supplied.authorities),
    )
    by_key = {_key(item.target): item for item in supplied.authorities}
    decisions = []
    for target in targets.target_races:
        authority = by_key.get(_key(target))
        start = target.scheduled_start_at
        eligible = (
            authority is not None and start is not None
            and authority.available_at <= start and authority.observed_at <= start
        )
        if eligible:
            decision = NARHistoricalReplayEligibilityDecision(
                target, NARHistoricalReplayEligibilityState.ELIGIBLE_WITH_PRE_CUTOFF_ENTRY_STATUS_AUTHORITY,
                None, None, "COMPLETE_PRE_CUTOFF_ENTRY_STATUS_UNIVERSE_VERIFIED",
            )
        else:
            reason = (
                "SCHEDULED_START_UNAVAILABLE" if start is None else
                "ENTRY_STATUS_AUTHORITY_MISSING" if authority is None else
                "ENTRY_STATUS_AUTHORITY_AFTER_PREDICTION_CUTOFF"
            )
            decision = NARHistoricalReplayEligibilityDecision(
                target, NARHistoricalReplayEligibilityState.BLOCKED_ENTRY_STATUS_AUTHORITY_UNAVAILABLE,
                _BLOCKER, _MISSING, reason,
            )
        decisions.append(decision)
    return NARHistoricalReplayEligibilityResolution(targets, tuple(decisions))
