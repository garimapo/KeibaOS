"""Pure NAR fixed-offset policy semantics and Phase96 plan compatibility."""

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
import inspect
import json
from pathlib import Path

import pytest

from scripts.simulation.historical_daily_targets import HistoricalDailyProviderIdentity
from scripts.simulation.nar_historical_replay_prediction_cutoff import (
    NARHistoricalReplayPredictionCutoffPlan,
    validate_nar_historical_replay_prediction_cutoff_plan,
)
from scripts.simulation.nar_historical_replay_prediction_cutoff_policy import (
    NARHistoricalReplayPredictionCutoffPolicy as Policy,
    build_nar_historical_replay_prediction_cutoff_plan as build_plan,
)
from tests.test_historical_daily_replay_manifest_projection import _target, _target_set


def test_policy_canonical_content_and_immutable_public_identity():
    first = Policy(offset_microseconds=60_000_000)
    second = Policy(offset_microseconds=60_000_000)
    changed = Policy(offset_microseconds=120_000_000)
    body = first.canonical_bytes()
    assert body == second.canonical_bytes()
    assert first.policy_sha256 == second.policy_sha256 == sha256(body).hexdigest()
    assert first.policy_identity == "nar-prediction-cutoff-policy-v1:" + first.policy_sha256
    assert first.policy_identity != changed.policy_identity
    assert first.policy_sha256 != changed.policy_sha256
    assert body == json.dumps(
        json.loads(body), ensure_ascii=False, allow_nan=False, sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    assert json.loads(body) == {
        "schema_version": 1,
        "organization": "NAR",
        "source_system": "nar_official",
        "policy_kind": "FIXED_OFFSET_BEFORE_SCHEDULED_START",
        "offset_microseconds": 60_000_000,
        "scheduled_start_basis": "DAILY_HISTORICAL_REPLAY_TARGET_SCHEDULED_START_AT_V1",
        "boundary_semantics": "C_EQUALS_SCHEDULED_START_AT_MINUS_OFFSET_V1",
    }
    assert tuple(field.name for field in fields(first)) == (
        "offset_microseconds", "schema_version", "policy_sha256",
    )
    assert not hasattr(first, "__dict__")
    with pytest.raises(FrozenInstanceError):
        first.offset_microseconds = 1
    assert not any("authoriz" in field.name.lower() for field in fields(first))


@pytest.mark.parametrize(
    "value",
    [True, False, 0, -1, 1.0, Decimal("1"), timedelta(microseconds=1), "1 minute", 10**30],
)
def test_offset_requires_positive_exact_representable_integer(value):
    with pytest.raises(ValueError):
        Policy(offset_microseconds=value)


@pytest.mark.parametrize("version", [True, 0, 2, "1"])
def test_policy_schema_version_is_closed(version):
    with pytest.raises(ValueError):
        Policy(offset_microseconds=1, schema_version=version)


def test_producer_is_deterministic_and_compatible_with_phase96():
    targets = _target_set(_target("02"), _target("01"))
    policy = Policy(offset_microseconds=45_000_001)
    first = build_plan(target_set=targets, policy=policy)
    repeated = build_plan(target_set=targets, policy=Policy(offset_microseconds=45_000_001))
    changed = build_plan(target_set=targets, policy=Policy(offset_microseconds=45_000_002))
    assert type(first) is NARHistoricalReplayPredictionCutoffPlan
    assert first == repeated
    assert first.canonical_bytes() == repeated.canonical_bytes()
    assert first.plan_sha256 == repeated.plan_sha256
    assert first.target_set is targets
    assert first.cutoff_policy_identity == policy.policy_identity
    assert tuple(decision.target for decision in first.decisions) == targets.target_races
    assert all(
        decision.prediction_information_cutoff
        == decision.target.scheduled_start_at - timedelta(microseconds=policy.offset_microseconds)
        for decision in first.decisions
    )
    assert changed.cutoff_policy_identity != first.cutoff_policy_identity
    assert changed.plan_sha256 != first.plan_sha256
    assert validate_nar_historical_replay_prediction_cutoff_plan(
        plan=first, target_set=targets,
    ) is first


def test_offset_has_no_timezone_dependent_policy_representation():
    policy = Policy(offset_microseconds=1_000_000)
    target = _target("01")
    local_time = target.scheduled_start_at.astimezone(timezone(timedelta(hours=9)))
    equivalent_target = replace(target, scheduled_start_at=local_time)
    assert equivalent_target.scheduled_start_at == target.scheduled_start_at
    assert build_plan(target_set=_target_set(target), policy=policy).canonical_bytes() == build_plan(
        target_set=_target_set(equivalent_target), policy=policy,
    ).canonical_bytes()
    assert json.loads(policy.canonical_bytes())["offset_microseconds"] == 1_000_000


def test_missing_start_unsupported_scope_and_nonexact_inputs_fail_closed():
    policy = Policy(offset_microseconds=1)
    missing_start = replace(_target("01"), scheduled_start_at=None)
    with pytest.raises(ValueError):
        build_plan(target_set=_target_set(missing_start), policy=policy)
    with pytest.raises(ValueError):
        build_plan(target_set=_target_set(), policy=policy)
    jra = HistoricalDailyProviderIdentity("JRA", "jra_official")
    with pytest.raises(ValueError):
        build_plan(target_set=_target_set(_target("01", provider=jra), provider=jra), policy=policy)
    with pytest.raises(ValueError):
        build_plan(target_set=object(), policy=policy)
    with pytest.raises(ValueError):
        build_plan(target_set=_target_set(_target("01")), policy=object())


def test_unrepresentable_cutoff_arithmetic_fails_with_validation_error():
    earliest = replace(
        _target("01"), scheduled_start_at=datetime.min.replace(tzinfo=timezone.utc),
    )
    with pytest.raises(ValueError, match="not representable"):
        build_plan(target_set=_target_set(earliest), policy=Policy(offset_microseconds=1))


def test_producer_derives_identity_and_has_no_authority_or_io_input():
    assert tuple(inspect.signature(build_plan).parameters) == ("target_set", "policy")
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in inspect.signature(build_plan).parameters.values()
    )
    source = Path(inspect.getfile(build_plan)).read_text(encoding="utf-8")
    syntax = ast.parse(source)
    imports = {
        alias.name
        for node in ast.walk(syntax)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert imports <= {
        "annotations", "dataclass", "field", "timedelta", "sha256", "json",
        "DailyHistoricalReplayTargetSet", "NARHistoricalReplayPredictionCutoffDecision",
        "NARHistoricalReplayPredictionCutoffPlan",
        "validate_nar_historical_replay_prediction_cutoff_plan",
    }
    calls = {
        node.func.id if isinstance(node.func, ast.Name) else node.func.attr
        for node in ast.walk(syntax)
        if isinstance(node, ast.Call)
        if isinstance(node.func, (ast.Name, ast.Attribute))
    }
    assert not calls.intersection({
        "open", "connect", "now", "utcnow", "today", "getenv", "socket",
        "request", "execute", "run_replay", "uuid4",
    })
    assert "cutoff_policy_identity" not in inspect.signature(build_plan).parameters
