from datetime import datetime, timezone
from hashlib import sha256

import pytest

from scripts.simulation.nar_operational_timing_attempt_v2 import (
    NARExpectedRequestEnvironmentPolicy as Policy,
    NAROperationalTimingAttemptV2 as Attempt,
    NAROperationalTimingTerminalV2 as Terminal,
    NARRequestEffectiveEnvironmentVerification as Environment,
    NARRequestEnvironmentQualification as Qualification,
    NARSafeSendSetting as Safe,
    NARTimingFailureClassificationV2 as Failure,
    NARTimingTerminalDispositionV2 as Disposition,
    elapsed_microseconds_from_ns,
)
from scripts.simulation.nar_operational_timing_observability import (
    NARTimingCorrelation, NARTimingCorrelationScope, NARTimingLoadContext,
)
from scripts.simulation.nar_operational_timing_observability_v2 import NAROperationalTimingStageV2 as Stage


NOW = datetime(2030, 1, 1, tzinfo=timezone.utc)
CONFIG = "nar-operational-timing-config-v2:" + "1" * 64
SESSION = "nar-operational-timing-session-v2:" + "2" * 64
CLAIM = "nar-operational-timing-campaign-execution-v1:" + "3" * 64
PROFILE = "nar-static-runtime-transport-profile-v1:" + "4" * 64


def _attempt(stage=Stage.BOOTSTRAP_HOME_ACQUISITION, policy=Policy.DIRECT_REQUEST_ENVIRONMENT_V1):
    return Attempt(CONFIG, SESSION, CLAIM, stage, NARTimingCorrelation(NARTimingCorrelationScope.PROVIDER),
                   0, NOW, NARTimingLoadContext(1, 1, False), policy,
                   sha256(b"https://www.keiba.go.jp/").hexdigest() if stage is Stage.BOOTSTRAP_HOME_ACQUISITION else None)


def test_attempt_canonical_identity_and_no_future_environment_identity():
    attempt = _attempt()
    assert Attempt.from_json(attempt.canonical_bytes().decode()) == attempt
    assert attempt.attempt_identity.startswith("nar-operational-timing-attempt-v2:")
    assert "verification" not in attempt.payload()
    assert attempt.payload()["expected_request_url_sha256"] == sha256(b"https://www.keiba.go.jp/").hexdigest()
    assert "result" not in attempt.payload() and "roi" not in attempt.payload()
    assert _attempt(Stage.SNAPSHOT_CONSTRUCTION, None).attempt_identity != attempt.attempt_identity
    with pytest.raises(ValueError):
        _attempt(Stage.SNAPSHOT_CONSTRUCTION)
    with pytest.raises(ValueError):
        _attempt(Stage.BOOTSTRAP_HOME_ACQUISITION, None)


def test_terminal_and_integer_monotonic_semantics():
    attempt = _attempt()
    assert elapsed_microseconds_from_ns(100, 1099) == 0
    assert elapsed_microseconds_from_ns(100, 1100) == 1
    for args in ((1.0, 1000), (1000, 999)):
        with pytest.raises(ValueError):
            elapsed_microseconds_from_ns(*args)
    for disposition, failure in ((Disposition.SUCCESS, None),
                                 (Disposition.TIMEOUT, Failure.CONNECT_TIMEOUT),
                                 (Disposition.TIMEOUT, Failure.READ_TIMEOUT),
                                 (Disposition.FAILURE, Failure.TRANSPORT),
                                 (Disposition.UNSUPPORTED, Failure.UNSUPPORTED)):
        terminal = Terminal(attempt.attempt_identity, NOW, 0, disposition, failure)
        assert Terminal.from_json(terminal.canonical_bytes().decode()) == terminal
    with pytest.raises(ValueError):
        Terminal(attempt.attempt_identity, NOW, 1.5, Disposition.SUCCESS)
    with pytest.raises(ValueError):
        Terminal(attempt.attempt_identity, NOW, 1, Disposition.SUCCESS, Failure.INTERNAL)


def test_safe_environment_identity_has_no_secret_material():
    attempt = _attempt()
    value = Environment(attempt.attempt_identity, "5" * 64, PROFILE, True, Safe.DIRECT, Safe.TRUE,
                        Safe.ABSENT, Safe.ABSENT, Safe.ABSENT, True, True,
                        Qualification.QUALIFIED_DIRECT_REQUEST_ENVIRONMENT)
    assert Environment.from_json(value.canonical_bytes().decode()) == value
    assert "password" not in value.canonical_bytes().decode()
    with pytest.raises(ValueError):
        Environment(attempt.attempt_identity, "5" * 64, PROFILE, True, Safe.NONEMPTY, Safe.TRUE,
                    Safe.ABSENT, Safe.ABSENT, Safe.ABSENT, True, True,
                    Qualification.QUALIFIED_DIRECT_REQUEST_ENVIRONMENT)
