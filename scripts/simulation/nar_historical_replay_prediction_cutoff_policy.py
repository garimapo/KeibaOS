"""Pure fixed-offset semantics for producing Phase96 NAR cutoff plans.

POLICY_IDENTITY != PRE_OUTCOME_POLICY_AUTHORITY. This module defines a rule
and deterministically derives a plan; it does not prove when the rule was
authorized. Retrospective plans require separate pre-outcome provenance before
they can be admitted to strict historical evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass as _dataclass, field as _field
from datetime import timedelta as _timedelta
from hashlib import sha256 as _sha256
import json as _json

from scripts.simulation.historical_daily_targets import (
    DailyHistoricalReplayTargetSet as _TargetSet,
)
from scripts.simulation.nar_historical_replay_prediction_cutoff import (
    NARHistoricalReplayPredictionCutoffDecision as _Decision,
    NARHistoricalReplayPredictionCutoffPlan as _Plan,
    validate_nar_historical_replay_prediction_cutoff_plan as _validate_plan,
)


__all__ = (
    "NARHistoricalReplayPredictionCutoffPolicy",
    "build_nar_historical_replay_prediction_cutoff_plan",
)


_ORGANIZATION = "NAR"
_SOURCE_SYSTEM = "nar_official"
_KIND = "FIXED_OFFSET_BEFORE_SCHEDULED_START"
_START_BASIS = "DAILY_HISTORICAL_REPLAY_TARGET_SCHEDULED_START_AT_V1"
_BOUNDARY = "C_EQUALS_SCHEDULED_START_AT_MINUS_OFFSET_V1"
_IDENTITY_PREFIX = "nar-prediction-cutoff-policy-v1:"


@_dataclass(frozen=True, slots=True)
class NARHistoricalReplayPredictionCutoffPolicy:
    """Content-addressed C-selection rule, without authorization provenance."""

    offset_microseconds: int
    schema_version: int = 1
    policy_sha256: str = _field(init=False)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ValueError("unsupported NAR cutoff policy schema version")
        if type(self.offset_microseconds) is not int or self.offset_microseconds <= 0:
            raise ValueError("offset_microseconds must be a positive exact int")
        try:
            duration = _timedelta(microseconds=self.offset_microseconds)
        except (OverflowError, TypeError, ValueError) as error:
            raise ValueError("offset_microseconds is not representable") from error
        if duration // _timedelta(microseconds=1) != self.offset_microseconds:
            raise ValueError("offset_microseconds is not represented exactly")
        object.__setattr__(self, "policy_sha256", _sha256(self.canonical_bytes()).hexdigest())

    @property
    def organization(self) -> str:
        return _ORGANIZATION

    @property
    def source_system(self) -> str:
        return _SOURCE_SYSTEM

    @property
    def policy_kind(self) -> str:
        return _KIND

    @property
    def scheduled_start_basis(self) -> str:
        return _START_BASIS

    @property
    def boundary_semantics(self) -> str:
        return _BOUNDARY

    @property
    def policy_identity(self) -> str:
        return _IDENTITY_PREFIX + self.policy_sha256

    def canonical_bytes(self) -> bytes:
        return _json.dumps(
            {
                "schema_version": self.schema_version,
                "organization": self.organization,
                "source_system": self.source_system,
                "policy_kind": self.policy_kind,
                "offset_microseconds": self.offset_microseconds,
                "scheduled_start_basis": self.scheduled_start_basis,
                "boundary_semantics": self.boundary_semantics,
            },
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")


def build_nar_historical_replay_prediction_cutoff_plan(
    *, target_set: _TargetSet, policy: NARHistoricalReplayPredictionCutoffPolicy,
) -> _Plan:
    """Derive one canonical plan; historical admissibility remains future-gated."""

    if type(target_set) is not _TargetSet or not target_set.target_races:
        raise ValueError("an exact nonempty target set is required")
    if type(policy) is not NARHistoricalReplayPredictionCutoffPolicy:
        raise ValueError("an exact NAR cutoff policy is required")
    rebuilt = NARHistoricalReplayPredictionCutoffPolicy(
        offset_microseconds=policy.offset_microseconds,
        schema_version=policy.schema_version,
    )
    if rebuilt != policy or rebuilt.policy_sha256 != policy.policy_sha256:
        raise ValueError("cutoff policy content identity is contradictory")
    if len(target_set.provider_scope.providers) != 1 or (
        target_set.provider_scope.providers[0].organization,
        target_set.provider_scope.providers[0].source_system,
    ) != (_ORGANIZATION, _SOURCE_SYSTEM):
        raise ValueError("target set must have exact NAR/nar_official scope")
    try:
        duration = _timedelta(microseconds=policy.offset_microseconds)
        decisions = tuple(
            _Decision(target, target.scheduled_start_at - duration)
            for target in target_set.target_races
        )
    except (OverflowError, TypeError) as error:
        raise ValueError("prediction cutoff arithmetic is not representable") from error
    plan = _Plan(target_set, policy.policy_identity, decisions)
    return _validate_plan(plan=plan, target_set=target_set)
