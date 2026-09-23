"""Immutable replay-policy cutoffs for one exact NAR target denominator."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass, field as _field
from datetime import datetime as _datetime, timezone as _timezone
from hashlib import sha256 as _sha256
import json as _json
import re as _re
from unicodedata import normalize as _normalize

from scripts.simulation.historical_daily_targets import (
    DailyHistoricalReplayTarget as _Target,
    DailyHistoricalReplayTargetSet as _TargetSet,
)


__all__ = (
    "NARHistoricalReplayPredictionCutoffDecision",
    "NARHistoricalReplayPredictionCutoffPlan",
    "validate_nar_historical_replay_prediction_cutoff_plan",
    "validate_nar_historical_replay_prediction_cutoff_plan_json",
)


_POLICY = _re.compile(r"nar-prediction-cutoff-policy-v1:[0-9a-f]{64}\Z", _re.ASCII)
_DIGEST = _re.compile(r"[0-9a-f]{64}\Z", _re.ASCII)


def _key(target: _Target) -> tuple[str, str, str]:
    provider = target.provider_identity
    return provider.organization, provider.source_system, target.external_race_id


def _utc(value: object) -> _datetime:
    if type(value) is not _datetime or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("prediction_information_cutoff must be an exact aware datetime")
    return value.astimezone(_timezone.utc)


def _time(value: _datetime) -> str:
    return value.astimezone(_timezone.utc).isoformat(timespec="microseconds")


def _canonical(payload: object) -> bytes:
    return _json.dumps(
        payload, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


@_dataclass(frozen=True, slots=True)
class NARHistoricalReplayPredictionCutoffDecision:
    target: _Target
    prediction_information_cutoff: _datetime

    def __post_init__(self) -> None:
        if type(self.target) is not _Target or _key(self.target)[:2] != ("NAR", "nar_official"):
            raise ValueError("cutoff decision requires an exact NAR target")
        if self.target.scheduled_start_at is None:
            raise ValueError("scheduled_start_at is required for prediction cutoff")
        cutoff = _utc(self.prediction_information_cutoff)
        if cutoff > self.target.scheduled_start_at:
            raise ValueError("prediction cutoff follows scheduled start")
        object.__setattr__(self, "prediction_information_cutoff", cutoff)


@_dataclass(frozen=True, slots=True)
class NARHistoricalReplayPredictionCutoffPlan:
    target_set: _TargetSet
    cutoff_policy_identity: str
    decisions: tuple[NARHistoricalReplayPredictionCutoffDecision, ...]
    schema_version: int = 1
    plan_sha256: str = _field(init=False)

    def __post_init__(self) -> None:
        if type(self.target_set) is not _TargetSet or not self.target_set.target_races:
            raise ValueError("cutoff plan requires an exact nonempty target set")
        if self.target_set.provider_scope.providers != (
            self.target_set.target_races[0].provider_identity,
        ) or _key(self.target_set.target_races[0])[:2] != ("NAR", "nar_official"):
            raise ValueError("cutoff plan requires NAR/nar_official target scope")
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ValueError("unsupported cutoff plan schema version")
        if (
            type(self.cutoff_policy_identity) is not str
            or self.cutoff_policy_identity != _normalize("NFC", self.cutoff_policy_identity)
            or _POLICY.fullmatch(self.cutoff_policy_identity) is None
        ):
            raise ValueError("cutoff policy identity must be an exact versioned identity")
        if type(self.decisions) is not tuple or any(
            type(item) is not NARHistoricalReplayPredictionCutoffDecision for item in self.decisions
        ):
            raise ValueError("cutoff decisions must be an exact tuple")
        if tuple(item.target for item in self.decisions) != self.target_set.target_races:
            raise ValueError("cutoff decisions must cover the exact canonical target order")
        if len({_key(item.target) for item in self.decisions}) != len(self.decisions):
            raise ValueError("cutoff decisions have duplicate target identity")
        rebuilt = _TargetSet(
            target_date=self.target_set.target_date,
            provider_scope=self.target_set.provider_scope,
            target_races=self.target_set.target_races,
            completeness_evidence=self.target_set.completeness_evidence,
        )
        if rebuilt != self.target_set or rebuilt.content_sha256 != self.target_set.content_sha256:
            raise ValueError("target-set content identity is contradictory")
        object.__setattr__(self, "plan_sha256", _sha256(self.canonical_bytes()).hexdigest())

    @property
    def target_set_content_sha256(self) -> str:
        return self.target_set.content_sha256

    def canonical_bytes(self) -> bytes:
        return _canonical({
            "schema_version": self.schema_version,
            "target_set_content_sha256": self.target_set.content_sha256,
            "cutoff_policy_identity": self.cutoff_policy_identity,
            "target_coverage": [
                {"organization": _key(item.target)[0], "source_system": _key(item.target)[1],
                 "external_race_id": _key(item.target)[2]}
                for item in self.decisions
            ],
            "decisions": [
                {"organization": _key(item.target)[0], "source_system": _key(item.target)[1],
                 "external_race_id": _key(item.target)[2],
                 "prediction_information_cutoff": _time(item.prediction_information_cutoff)}
                for item in self.decisions
            ],
        })


def validate_nar_historical_replay_prediction_cutoff_plan(
    *, plan: NARHistoricalReplayPredictionCutoffPlan, target_set: _TargetSet,
) -> NARHistoricalReplayPredictionCutoffPlan:
    if type(plan) is not NARHistoricalReplayPredictionCutoffPlan or plan.target_set is not target_set:
        raise ValueError("cutoff plan must bind the exact acquisition target set")
    rebuilt = NARHistoricalReplayPredictionCutoffPlan(
        plan.target_set, plan.cutoff_policy_identity, plan.decisions, plan.schema_version,
    )
    if rebuilt != plan or rebuilt.plan_sha256 != plan.plan_sha256:
        raise ValueError("cutoff plan content identity is contradictory")
    return plan


def validate_nar_historical_replay_prediction_cutoff_plan_json(
    *, canonical_json: str, plan_sha256: str, target_set_content_sha256: str,
) -> dict[str, object]:
    """Validate stored policy provenance without inventing a missing target set."""
    if type(canonical_json) is not str or type(plan_sha256) is not str or _DIGEST.fullmatch(plan_sha256) is None:
        raise ValueError("stored cutoff plan identity is invalid")
    if type(target_set_content_sha256) is not str or _DIGEST.fullmatch(target_set_content_sha256) is None:
        raise ValueError("stored target-set identity is invalid")
    def unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate cutoff plan JSON key")
            result[key] = value
        return result
    try:
        parsed = _json.loads(canonical_json, object_pairs_hook=unique,
                             parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    except (_json.JSONDecodeError, UnicodeError) as error:
        raise ValueError("stored cutoff plan JSON is malformed") from error
    if type(parsed) is not dict or set(parsed) != {
        "schema_version", "target_set_content_sha256", "cutoff_policy_identity", "target_coverage", "decisions"
    } or _canonical(parsed) != canonical_json.encode("utf-8"):
        raise ValueError("stored cutoff plan JSON is noncanonical or incompatible")
    if parsed["schema_version"] != 1 or type(parsed["schema_version"]) is not int:
        raise ValueError("stored cutoff plan version is unsupported")
    if parsed["target_set_content_sha256"] != target_set_content_sha256:
        raise ValueError("stored cutoff plan contradicts parent target set")
    policy = parsed["cutoff_policy_identity"]
    if type(policy) is not str or _POLICY.fullmatch(policy) is None:
        raise ValueError("stored cutoff policy identity is invalid")
    coverage, decisions = parsed["target_coverage"], parsed["decisions"]
    if type(coverage) is not list or type(decisions) is not list or not coverage or len(coverage) != len(decisions):
        raise ValueError("stored cutoff plan coverage is incomplete")
    keys: list[tuple[str, str, str]] = []
    for cover, decision in zip(coverage, decisions, strict=True):
        required = {"organization", "source_system", "external_race_id"}
        if type(cover) is not dict or set(cover) != required or type(decision) is not dict or set(decision) != required | {"prediction_information_cutoff"}:
            raise ValueError("stored cutoff decision shape is invalid")
        key = tuple(cover[name] for name in ("organization", "source_system", "external_race_id"))
        if any(type(value) is not str or not value or value != _normalize("NFC", value) for value in key):
            raise ValueError("stored cutoff target identity is invalid")
        if key[:2] != ("NAR", "nar_official") or any(decision[name] != cover[name] for name in required):
            raise ValueError("stored cutoff target coverage is contradictory")
        timestamp = decision["prediction_information_cutoff"]
        try:
            observed = _datetime.fromisoformat(timestamp)
            if type(timestamp) is not str or _time(_utc(observed)) != timestamp:
                raise ValueError("noncanonical cutoff timestamp")
        except (TypeError, ValueError) as error:
            raise ValueError("stored cutoff timestamp is invalid") from error
        keys.append(key)
    if keys != sorted(set(keys)):
        raise ValueError("stored cutoff target order is noncanonical")
    if _sha256(canonical_json.encode("utf-8")).hexdigest() != plan_sha256:
        raise ValueError("stored cutoff plan SHA-256 is invalid")
    return parsed
