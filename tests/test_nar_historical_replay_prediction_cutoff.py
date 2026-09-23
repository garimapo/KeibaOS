"""Exact, separately content-addressed NAR replay cutoff plans."""

from dataclasses import FrozenInstanceError, replace
from datetime import timedelta, timezone
import json

import pytest

from scripts.simulation.nar_historical_replay_prediction_cutoff import (
    NARHistoricalReplayPredictionCutoffDecision as Decision,
    NARHistoricalReplayPredictionCutoffPlan as Plan,
    validate_nar_historical_replay_prediction_cutoff_plan as validate,
    validate_nar_historical_replay_prediction_cutoff_plan_json as validate_json,
)
from tests.test_historical_daily_replay_manifest_projection import _target, _target_set


POLICY = "nar-prediction-cutoff-policy-v1:" + "a" * 64


def _plan(target_set, *, offset=timedelta(minutes=1), policy=POLICY):
    return Plan(
        target_set,
        policy,
        tuple(Decision(target, target.scheduled_start_at - offset) for target in target_set.target_races),
    )


def test_content_identity_and_canonical_utc_time():
    targets = _target_set(_target("02"), _target("01"))
    first = _plan(targets)
    changed = _plan(targets, offset=timedelta(minutes=2))
    assert first.target_set is changed.target_set is targets
    assert first.target_set_content_sha256 == changed.target_set_content_sha256
    assert first.plan_sha256 != changed.plan_sha256
    assert first.canonical_bytes() == _plan(targets).canonical_bytes()
    assert tuple(item.target for item in first.decisions) == targets.target_races
    payload = validate_json(
        canonical_json=first.canonical_bytes().decode("utf-8"),
        plan_sha256=first.plan_sha256,
        target_set_content_sha256=targets.content_sha256,
    )
    assert payload["target_coverage"][0]["external_race_id"] == targets.target_races[0].external_race_id
    assert payload["decisions"][0]["prediction_information_cutoff"].endswith("+00:00")
    equivalent = tuple(Decision(item.target, item.prediction_information_cutoff.astimezone(timezone(timedelta(hours=9))))
                       for item in first.decisions)
    assert Plan(targets, POLICY, equivalent).plan_sha256 == first.plan_sha256
    assert validate(plan=first, target_set=targets) is first
    with pytest.raises(FrozenInstanceError):
        first.cutoff_policy_identity = "changed"


def test_target_closure_and_order_fail_closed():
    targets = _target_set(_target("01"), _target("02"))
    first = _plan(targets)
    for decisions in (
        first.decisions[:1],
        first.decisions + (Decision(_target("03"), _target("03").scheduled_start_at),),
        first.decisions + (first.decisions[0],),
        tuple(reversed(first.decisions)),
    ):
        with pytest.raises(ValueError):
            Plan(targets, POLICY, decisions)
    with pytest.raises(ValueError):
        validate(plan=first, target_set=_target_set(_target("01"), _target("02")))


def test_missing_or_late_cutoff_and_bad_policy_fail_closed():
    target = _target("01")
    targets = _target_set(target)
    for value in (None, target.scheduled_start_at + timedelta(microseconds=1), "2025-01-01"):
        with pytest.raises(ValueError):
            Decision(target, value)
    with pytest.raises(ValueError):
        missing_start = replace(target, scheduled_start_at=None)
        Plan(_target_set(missing_start), POLICY, (Decision(missing_start, target.scheduled_start_at),))
    with pytest.raises(ValueError):
        _plan(targets, policy="caller supplied text")


def test_stored_plan_rejects_corruption_and_noncanonical_encoding():
    targets = _target_set(_target("01"))
    plan = _plan(targets)
    body = plan.canonical_bytes().decode("utf-8")
    with pytest.raises(ValueError):
        validate_json(canonical_json=body + " ", plan_sha256=plan.plan_sha256,
                      target_set_content_sha256=targets.content_sha256)
    with pytest.raises(ValueError):
        validate_json(canonical_json=body, plan_sha256="0" * 64,
                      target_set_content_sha256=targets.content_sha256)
    with pytest.raises(ValueError):
        validate_json(canonical_json=body, plan_sha256=plan.plan_sha256,
                      target_set_content_sha256="0" * 64)
    parsed = json.loads(body)
    parsed["decisions"].append(parsed["decisions"][0])
    with pytest.raises(ValueError):
        validate_json(canonical_json=json.dumps(parsed, sort_keys=True, separators=(",", ":")),
                      plan_sha256=plan.plan_sha256,
                      target_set_content_sha256=targets.content_sha256)
