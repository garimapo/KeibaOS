"""Independent V2 timing configuration, stage roles, and fixed session window."""

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json

import pytest

from scripts.simulation.nar_operational_timing_observability import (
    NARHTTPTransportKind, NARHTTPTransportProfile,
    NAROperationalTimingMeasurementConfiguration as ConfigurationV1,
    NARTimingStage,
)
from scripts.simulation.nar_operational_timing_observability_v2 import (
    NAROperationalTimingMeasurementConfigurationV2 as Configuration,
    NAROperationalTimingMeasurementSessionV2 as Session,
    NAROperationalTimingStageV2 as Stage,
    NARTimingBudgetRoleV2 as Role, budget_role_v2,
)


START = datetime(2026, 10, 1, 1, tzinfo=timezone.utc)
PROFILES = tuple(NARHTTPTransportProfile(kind, 10_000_000,
    20_000_000 if kind is NARHTTPTransportKind.NAR_MARKET_ODDS_RAW_HTTP else 10_000_000)
    for kind in NARHTTPTransportKind)


def config(**changes):
    values = dict(software_commit_sha="a" * 40,
                  enabled_stages=(Stage.RACE_LIST_ACQUISITION, Stage.SNAPSHOT_PERSISTENCE,
                                  Stage.ATTEMPT_START_PUBLICATION),
                  transport_profiles=PROFILES)
    values.update(changes)
    return Configuration(**values)


def session(**changes):
    values = dict(configuration=config(), measurement_start_at=START,
                  measurement_end_at=START + timedelta(minutes=1))
    values.update(changes)
    return Session(**values)


def test_configuration_is_canonical_distinct_and_declared_only():
    first = config()
    reordered = config(enabled_stages=tuple(reversed(first.enabled_stages)),
                       transport_profiles=tuple(reversed(PROFILES)))
    assert first == reordered
    assert first.canonical_bytes() == reordered.canonical_bytes()
    assert first.configuration_sha256 == sha256(first.canonical_bytes()).hexdigest()
    assert first.configuration_identity == "nar-operational-timing-config-v2:" + first.configuration_sha256
    assert Configuration.from_json(first.canonical_bytes().decode("utf-8")) == first
    assert first.instrumentation_schema_version == first.schema_version == 2
    assert first.execution_authority_semantic_version == 1
    assert first.concurrency_regime.value == "CONTROLLED_SINGLE_WORKER_SERIAL_V1"
    assert "authority" not in first.payload() and "result" not in first.payload()
    with pytest.raises(FrozenInstanceError):
        first.software_commit_sha = "b" * 40
    assert config(software_commit_sha="b" * 40).configuration_identity != first.configuration_identity
    assert config(enabled_stages=(Stage.RACE_LIST_ACQUISITION,)).configuration_identity != first.configuration_identity
    v1 = ConfigurationV1("a" * 40, (NARTimingStage.RACE_LIST_ACQUISITION,), PROFILES)
    assert v1.configuration_identity.startswith("nar-operational-timing-config-v1:")
    assert v1.configuration_identity != first.configuration_identity


@pytest.mark.parametrize("changes", [
    {"software_commit_sha": "A" * 40}, {"software_commit_sha": "a" * 39},
    {"schema_version": 1}, {"instrumentation_schema_version": 1},
    {"enabled_stages": ()}, {"enabled_stages": (Stage.PARSING,) * 2},
    {"enabled_stages": ("PARSING",)}, {"transport_profiles": PROFILES + (PROFILES[0],)},
    {"enabled_stages": (Stage.RACE_LIST_ACQUISITION,), "transport_profiles": ()},
    {"max_retries": 1}, {"backoff_microseconds": 1},
    {"max_concurrent_http_requests": 2}, {"execution_authority_semantic_version": 2},
])
def test_invalid_configuration_fails_closed(changes):
    with pytest.raises(ValueError):
        config(**changes)


def test_v2_stage_role_mapping_is_total_and_v1_does_not_change():
    assert {s for role in Role for s in Stage if budget_role_v2(s) is role} == set(Stage)
    assert sum(sum(budget_role_v2(s) is role for role in Role) for s in Stage) == len(Stage)
    assert budget_role_v2(Stage.RACE_LIST_ACQUISITION) is Role.PRE_C_FREEZE
    assert budget_role_v2(Stage.FREEZE_RECEIPT_PUBLICATION) is Role.FREEZE_PROVENANCE
    assert budget_role_v2(Stage.ATTEMPT_START_PUBLICATION) is Role.OBSERVABILITY_OVERHEAD
    assert budget_role_v2(Stage.PREDICTION_PIPELINE) is Role.POST_C_COMPUTE
    assert budget_role_v2(Stage.RUNTIME_BINDING_READINESS) is Role.CAMPAIGN_CONTROL
    with pytest.raises(ValueError):
        budget_role_v2(NARTimingStage.PARSING)
    assert "ATTEMPT_START_PUBLICATION" not in {stage.value for stage in NARTimingStage}


def test_v2_session_utc_half_open_and_version_separation():
    first = session()
    shifted = session(measurement_start_at=START.astimezone(timezone(timedelta(hours=9))),
                      measurement_end_at=(START + timedelta(minutes=1)).astimezone(timezone(timedelta(hours=9))))
    assert shifted == first
    assert Session.from_json(first.canonical_bytes().decode(), first.configuration) == first
    assert first.session_identity == "nar-operational-timing-session-v2:" + first.session_sha256
    assert first.admits(START) and first.admits(START + timedelta(seconds=59))
    assert not first.admits(START + timedelta(minutes=1))
    with pytest.raises(ValueError):
        session(measurement_end_at=START)
    with pytest.raises(ValueError):
        session(measurement_start_at=START.replace(tzinfo=None))
    with pytest.raises(ValueError):
        session(configuration=ConfigurationV1("a" * 40, (NARTimingStage.PARSING,), ()))
    with pytest.raises(ValueError):
        Session.from_json(first.canonical_bytes().decode(), config(software_commit_sha="b" * 40))
    extra = json.loads(first.canonical_bytes())
    extra["result"] = "forbidden"
    with pytest.raises(ValueError):
        Session.from_json(json.dumps(extra, separators=(",", ":"), sort_keys=True), first.configuration)
