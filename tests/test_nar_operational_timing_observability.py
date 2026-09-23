"""Phase99 immutable timing configuration, session, and denominator contracts."""

from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import inspect

import pytest

from scripts.simulation.nar_operational_timing_observability import (
    NARConcurrencyRegime, NARHTTPTransportKind, NARHTTPTransportProfile,
    NAROperationalTimingAttempt, NAROperationalTimingMeasurementConfiguration,
    NAROperationalTimingMeasurementSession, NAROperationalTimingTerminalObservation,
    NARSampleAdmissionRule, NARSessionCompletionRule, NARTimingCorrelation,
    NARTimingCorrelationScope, NARTimingFailureClassification,
    NARTimingLoadContext, NARTimingStage, NARTimingStageFamily,
    NARTimingTerminalDisposition, stage_family,
)


START = datetime(2026, 10, 1, 1, tzinfo=timezone.utc)
PROFILES = tuple(NARHTTPTransportProfile(kind, 10_000_000,
    20_000_000 if kind is NARHTTPTransportKind.NAR_MARKET_ODDS_RAW_HTTP else 10_000_000)
    for kind in NARHTTPTransportKind)
CORRELATION = NARTimingCorrelation(NARTimingCorrelationScope.RACE, "nar:20261001:01:1")


def config(**changes):
    values = dict(software_commit_sha="a" * 40,
                  enabled_stages=(NARTimingStage.RACE_LIST_ACQUISITION,
                                  NARTimingStage.SNAPSHOT_PERSISTENCE),
                  transport_profiles=PROFILES)
    values.update(changes)
    return NAROperationalTimingMeasurementConfiguration(**values)


def session(**changes):
    values = dict(configuration=config(), measurement_start_at=START,
                  measurement_end_at=START + timedelta(minutes=1))
    values.update(changes)
    return NAROperationalTimingMeasurementSession(**values)


def test_configuration_canonical_identity_and_closed_regime():
    first = config()
    reversed_profiles = config(transport_profiles=tuple(reversed(PROFILES)))
    assert first == reversed_profiles
    assert first.canonical_bytes() == reversed_profiles.canonical_bytes()
    assert first.configuration_identity == "nar-operational-timing-config-v1:" + first.configuration_sha256
    assert NAROperationalTimingMeasurementConfiguration.from_json(first.canonical_bytes().decode()) == first
    assert first.concurrency_regime is NARConcurrencyRegime.CONTROLLED_SINGLE_WORKER_SERIAL_V1
    assert first.max_concurrent_target_workflows == first.max_concurrent_http_requests == 1
    assert [(p.connect_timeout_microseconds, p.read_timeout_microseconds) for p in first.transport_profiles] == [
        (10_000_000, 10_000_000)] * 3 + [(10_000_000, 20_000_000)]
    assert stage_family(NARTimingStage.RACE_LIST_ACQUISITION) is NARTimingStageFamily.PRE_C
    assert stage_family(NARTimingStage.PREDICTION_PIPELINE) is NARTimingStageFamily.POST_C
    assert config(software_commit_sha="b" * 40).configuration_sha256 != first.configuration_sha256
    assert config(enabled_stages=(NARTimingStage.SNAPSHOT_PERSISTENCE,)).configuration_sha256 != first.configuration_sha256
    with pytest.raises(FrozenInstanceError):
        first.software_commit_sha = "b" * 40


@pytest.mark.parametrize("value", ["A" * 40, "a" * 39, "a" * 41, "feature/main", True])
def test_software_commit_must_be_exact_sha(value):
    with pytest.raises(ValueError):
        config(software_commit_sha=value)


@pytest.mark.parametrize("value", [True, 0, -1, 1.5, Decimal("1")])
def test_timeout_must_be_exact_positive_microseconds(value):
    with pytest.raises(ValueError):
        NARHTTPTransportProfile(NARHTTPTransportKind.NAR_BOOTSTRAP_HTTP, value, 10_000_000)


def test_profile_stage_retry_and_concurrency_fail_closed():
    with pytest.raises(ValueError, match="duplicate"):
        config(transport_profiles=PROFILES + (PROFILES[0],))
    with pytest.raises(ValueError, match="lacks"):
        config(transport_profiles=())
    with pytest.raises(ValueError):
        config(enabled_stages=(NARTimingStage.RACE_LIST_ACQUISITION,) * 2)
    with pytest.raises(ValueError):
        config(enabled_stages=("RACE_LIST_ACQUISITION",))
    with pytest.raises(ValueError):
        config(enabled_stages=())
    with pytest.raises(ValueError):
        config(max_retries=1)
    with pytest.raises(ValueError):
        config(backoff_microseconds=1)
    with pytest.raises(ValueError):
        config(max_concurrent_http_requests=2)


def test_session_fixed_window_and_half_open_admission():
    first = session()
    equivalent = session(measurement_start_at=START.astimezone(timezone(timedelta(hours=9))),
                         measurement_end_at=(START + timedelta(minutes=1)).astimezone(timezone(timedelta(hours=9))))
    assert first == equivalent
    assert first.session_identity == "nar-operational-timing-session-v1:" + first.session_sha256
    assert NAROperationalTimingMeasurementSession.from_json(first.canonical_bytes().decode(), first.configuration) == first
    assert first.admits(START)
    assert first.admits(START + timedelta(seconds=59))
    assert not first.admits(START + timedelta(minutes=1))
    assert session(measurement_end_at=START + timedelta(minutes=2)).session_sha256 != first.session_sha256
    with pytest.raises(ValueError):
        session(measurement_end_at=START)
    with pytest.raises(ValueError):
        session(measurement_start_at=START.replace(tzinfo=None))
    with pytest.raises(ValueError):
        session(session_completion_rule="FIXED_WALL_CLOCK_END")
    assert first.sample_admission_rule is NARSampleAdmissionRule.OPERATION_STARTED_IN_HALF_OPEN_SESSION_WINDOW
    assert first.session_completion_rule is NARSessionCompletionRule.FIXED_WALL_CLOCK_END


def test_attempt_exists_independently_of_terminal_and_monotonic_duration_is_explicit():
    window = session()
    started = START + timedelta(seconds=59)
    attempt = NAROperationalTimingAttempt(window, NARTimingStage.RACE_LIST_ACQUISITION,
                                          CORRELATION, 0, started)
    assert NAROperationalTimingAttempt.from_json(attempt.canonical_bytes().decode(), window) == attempt
    terminal = NAROperationalTimingTerminalObservation(
        attempt, START + timedelta(minutes=2), 9_000_000,
        NARTimingTerminalDisposition.TIMEOUT, NARTimingFailureClassification.TIMEOUT)
    assert terminal.elapsed_microseconds == 9_000_000
    assert NAROperationalTimingTerminalObservation.from_json(terminal.canonical_bytes().decode(), attempt) == terminal
    assert terminal.operation_finished_at > window.measurement_end_at
    for kind, reason in ((NARTimingTerminalDisposition.SUCCESS, None),
                         (NARTimingTerminalDisposition.FAILURE, NARTimingFailureClassification.TRANSPORT),
                         (NARTimingTerminalDisposition.TIMEOUT, NARTimingFailureClassification.TIMEOUT)):
        assert NAROperationalTimingTerminalObservation(attempt, started, 0, kind, reason).disposition is kind
    with pytest.raises(ValueError):
        NAROperationalTimingAttempt(window, NARTimingStage.RACE_LIST_ACQUISITION,
                                    CORRELATION, 1, window.measurement_end_at)
    with pytest.raises(ValueError):
        replace(terminal, elapsed_microseconds=-1)
    with pytest.raises(ValueError):
        replace(terminal, elapsed_microseconds=1.5)
    assert not {"result", "payout", "roi", "authorized"} & set(inspect.signature(NAROperationalTimingMeasurementSession).parameters)


def test_correlation_is_provider_scoped_and_content_addressed():
    assert CORRELATION.correlation_identity.startswith("nar-operational-timing-correlation-v1:")
    assert NARTimingCorrelation.from_payload(CORRELATION.payload()) == CORRELATION
    changed = NARTimingCorrelation(NARTimingCorrelationScope.RACE, "nar:20261001:01:2")
    assert changed.correlation_identity != CORRELATION.correlation_identity
    with pytest.raises(ValueError):
        NARTimingCorrelation(NARTimingCorrelationScope.RACE)
    with pytest.raises(ValueError):
        NARTimingCorrelation(NARTimingCorrelationScope.TARGET_SET)
    with pytest.raises(ValueError):
        NARTimingCorrelation(NARTimingCorrelationScope.PROVIDER, external_race_id="race")


def test_load_context_is_closed_and_unmeasured_is_not_zero():
    assert NARTimingLoadContext().payload()["active_http_requests"] is None
    assert NARTimingLoadContext(1, 1, False).payload()["process_cold_start"] is False
    for invalid in (True, -1, 1.0):
        with pytest.raises(ValueError):
            NARTimingLoadContext(active_target_workflows=invalid)
    with pytest.raises(ValueError):
        NARTimingLoadContext(process_cold_start="false")
