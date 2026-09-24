from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3

import pytest
import requests

from scripts.simulation.nar_operational_timing_attempt_v2 import (
    NARRequestEnvironmentQualification, NARTimingTerminalDispositionV2,
)
from scripts.simulation.nar_operational_timing_campaign_runner import NAROperationalTimingCampaignRunner
from scripts.simulation.nar_operational_timing_guarded_session import (
    NAROfficialTimingGuardedSession, NARRequestEnvironmentRejected,
)
from scripts.simulation.nar_operational_timing_observability import (
    NARHTTPTransportKind, NARHTTPTransportProfile, NARTimingCorrelation,
    NARTimingCorrelationScope, NARTimingLoadContext,
)
from scripts.simulation.nar_operational_timing_observability_v2 import (
    NAROperationalTimingMeasurementConfigurationV2 as Configuration,
    NAROperationalTimingMeasurementSessionV2 as Session,
    NAROperationalTimingStageV2 as Stage,
)
from scripts.simulation.nar_operational_timing_passive_wrapper import measure_nar_operation, classify_timing_failure
from scripts.simulation.nar_operational_timing_runtime_profile import derive_static_runtime_transport_profile
from scripts.simulation.nar_operational_timing_runtime_source_provenance import _git_manifest
from scripts.simulation.nar_operational_timing_session_activation_v2 import issue_nar_operational_timing_session_activation_v2
from scripts.simulation.sqlite_nar_operational_timing_observability_archive import TimingArchiveError


ROOT = Path(__file__).resolve().parents[1]
COMMIT = "8d6411f7d886caf70db44e1e92ccd1f5bd6711d8"
START = datetime(2030, 1, 1, tzinfo=timezone.utc)
URL = "https://www.keiba.go.jp/"
CORRELATION = NARTimingCorrelation(NARTimingCorrelationScope.PROVIDER)
LOAD = NARTimingLoadContext(1, 1, False)


def _campaign(tmp_path, monkeypatch, *, stages=(Stage.SNAPSHOT_CONSTRUCTION,), clock_times=None):
    bundle, _ = _git_manifest(ROOT, COMMIT)
    profile = derive_static_runtime_transport_profile()
    config = Configuration(COMMIT, stages, tuple(NARHTTPTransportProfile(
        x.kind, x.connect_timeout_microseconds, x.read_timeout_microseconds) for x in profile.descriptors))
    session = Session(config, START, START + timedelta(hours=1))
    times = iter(clock_times or (START - timedelta(seconds=2), START - timedelta(seconds=1),
                                 START + timedelta(seconds=1), START + timedelta(seconds=2)))
    ticks = iter(range(0, 100_000_000, 1_000_000))
    runner = NAROperationalTimingCampaignRunner(
        archive_path=tmp_path / "archive.sqlite", repository_root=ROOT, bundle_root=tmp_path,
        bundle=bundle, session_identity=session.session_identity, utc_clock=lambda: next(times),
        monotonic_timer_ns=lambda: next(ticks), enable_attempt_archive=True)
    monkeypatch.setattr(NAROperationalTimingCampaignRunner, "_require_isolated_source", lambda self: None)
    return runner, config, session


def _activate(runner, config, session):
    archive = runner.attempt_archive
    archive.runtime.v2.save_configuration(configuration=config)
    archive.runtime.v2.save_session(session=session)
    issue_nar_operational_timing_session_activation_v2(
        session=session, archive=archive.runtime.v2, utc_clock=lambda: START - timedelta(minutes=1))
    return runner.issue_current_process_execution()


def test_attempt_precedes_callable_and_success_result_identity_is_preserved(tmp_path, monkeypatch):
    runner, config, session = _campaign(tmp_path, monkeypatch)
    with runner:
        capability = _activate(runner, config, session)
        value = object()
        def operation():
            assert len(runner.attempt_archive.list_unresolved_attempts(claim_identity=capability.claim_identity)) == 1
            return value
        result = measure_nar_operation(runner=runner, capability=capability,
                                       stage=Stage.SNAPSHOT_CONSTRUCTION, correlation=CORRELATION,
                                       load_context=LOAD, operation=operation)
        assert result is value
        assert not runner.attempt_archive.list_unresolved_attempts(claim_identity=capability.claim_identity)
        attempt_id = runner._connection.execute("SELECT identity FROM nar_operational_timing_v2_attempts").fetchone()[0]
        attempt = runner.attempt_archive.load_attempt(attempt_identity=attempt_id)
        terminal = runner.attempt_archive.load_terminal_for_attempt(attempt_identity=attempt_id)
        assert terminal.disposition is NARTimingTerminalDispositionV2.SUCCESS
        assert runner.attempt_archive.save_attempt(attempt=attempt) is False
        assert runner.attempt_archive.save_terminal(terminal=terminal) is False
        for table in ("nar_operational_timing_v2_attempts", "nar_operational_timing_v2_terminals"):
            with pytest.raises(sqlite3.DatabaseError):
                runner._connection.execute(f"UPDATE {table} SET identity='other'")
            with pytest.raises(sqlite3.DatabaseError):
                runner._connection.execute(f"DELETE FROM {table}")
        assert runner._connection.execute("SELECT COUNT(*) FROM nar_operational_timing_publication_overhead").fetchone()[0] == 2


def test_original_exception_preserved_and_terminal_failure_unresolved(tmp_path, monkeypatch):
    runner, config, session = _campaign(tmp_path, monkeypatch)
    with runner:
        capability = _activate(runner, config, session)
        error = ValueError("production error")
        original_save = type(runner.attempt_archive).save_terminal
        monkeypatch.setattr(type(runner.attempt_archive), "save_terminal", lambda self, **_: (_ for _ in ()).throw(RuntimeError("telemetry failed")))
        with pytest.raises(ValueError) as caught:
            measure_nar_operation(runner=runner, capability=capability,
                                  stage=Stage.SNAPSHOT_CONSTRUCTION, correlation=CORRELATION,
                                  load_context=LOAD, operation=lambda: (_ for _ in ()).throw(error))
        assert caught.value is error
        assert len(runner.attempt_archive.list_unresolved_attempts(claim_identity=capability.claim_identity)) == 1
        monkeypatch.setattr(type(runner.attempt_archive), "save_terminal", original_save)


def test_classification_failure_cannot_replace_original_exception(tmp_path, monkeypatch):
    runner, config, session = _campaign(tmp_path, monkeypatch)
    with runner:
        capability = _activate(runner, config, session)
        error = RuntimeError("production failure")
        monkeypatch.setattr("scripts.simulation.nar_operational_timing_passive_wrapper.classify_timing_failure",
                            lambda _: (_ for _ in ()).throw(RuntimeError("telemetry classifier failed")))
        with pytest.raises(RuntimeError) as caught:
            measure_nar_operation(runner=runner, capability=capability,
                                  stage=Stage.SNAPSHOT_CONSTRUCTION, correlation=CORRELATION,
                                  load_context=LOAD, operation=lambda: (_ for _ in ()).throw(error))
        assert caught.value is error


def test_attempt_publication_failure_or_end_equality_never_invokes_operation(tmp_path, monkeypatch):
    runner, config, session = _campaign(tmp_path, monkeypatch)
    with runner:
        capability = _activate(runner, config, session)
        called = []
        original_save = type(runner.attempt_archive).save_attempt
        monkeypatch.setattr(type(runner.attempt_archive), "save_attempt",
                            lambda self, **_: (_ for _ in ()).throw(RuntimeError("archive failed")))
        with pytest.raises(RuntimeError, match="archive failed"):
            measure_nar_operation(runner=runner, capability=capability,
                                  stage=Stage.SNAPSHOT_CONSTRUCTION, correlation=CORRELATION,
                                  load_context=LOAD, operation=lambda: called.append(1))
        assert called == []
        assert runner._connection.execute("SELECT COUNT(*) FROM nar_operational_timing_v2_attempts").fetchone()[0] == 0
        monkeypatch.setattr(type(runner.attempt_archive), "save_attempt", original_save)
    (tmp_path / "other").mkdir()
    second, config2, session2 = _campaign(tmp_path / "other", monkeypatch,
        clock_times=(START - timedelta(seconds=2), START - timedelta(seconds=1), START + timedelta(hours=1)))
    with second:
        cap2 = _activate(second, config2, session2)
        with pytest.raises(RuntimeError, match="outside fixed"):
            measure_nar_operation(runner=second, capability=cap2,
                                  stage=Stage.SNAPSHOT_CONSTRUCTION, correlation=CORRELATION,
                                  load_context=LOAD, operation=lambda: called.append(1))
        assert called == []


def test_timeout_classification_uses_explicit_cause_not_message():
    outer = RuntimeError("wrapped")
    outer.__cause__ = requests.exceptions.ConnectTimeout("proof")
    assert classify_timing_failure(outer)[1].value == "CONNECT_TIMEOUT"
    assert classify_timing_failure(RuntimeError("ReadTimeout happened"))[1].value == "INTERNAL"


def test_http_attempt_without_guard_verification_is_not_official_sample(tmp_path, monkeypatch):
    runner, config, session = _campaign(tmp_path, monkeypatch, stages=(Stage.BOOTSTRAP_HOME_ACQUISITION,))
    with runner:
        capability = _activate(runner, config, session)
        assert measure_nar_operation(runner=runner, capability=capability,
                                     stage=Stage.BOOTSTRAP_HOME_ACQUISITION, correlation=CORRELATION,
                                     load_context=LOAD, expected_url=URL,
                                     transport_kind=NARHTTPTransportKind.NAR_BOOTSTRAP_HTTP,
                                     operation=lambda: "no provider call") == "no provider call"
        assert len(runner.attempt_archive.list_nonqualifying_http_attempts(claim_identity=capability.claim_identity)) == 1


class _FakeAdapter(requests.adapters.HTTPAdapter):
    def __init__(self, events):
        super().__init__(max_retries=0)
        self.events = events

    def send(self, request, **kwargs):
        self.events.append("adapter")
        response = requests.Response()
        response.status_code = 200
        response.url = request.url
        response._content = b"okay"
        response.request = request
        return response


def test_guard_qualifies_actual_send_before_fake_adapter_and_blocks_proxy(tmp_path, monkeypatch):
    monkeypatch.delenv("HTTPS_PROXY", raising=False)
    monkeypatch.delenv("HTTP_PROXY", raising=False)
    monkeypatch.delenv("ALL_PROXY", raising=False)
    monkeypatch.delenv("REQUESTS_CA_BUNDLE", raising=False)
    monkeypatch.delenv("CURL_CA_BUNDLE", raising=False)
    runner, config, session = _campaign(tmp_path, monkeypatch, stages=(Stage.BOOTSTRAP_HOME_ACQUISITION,))
    with runner:
        capability = _activate(runner, config, session)
        events = []
        guarded = NAROfficialTimingGuardedSession(runner=runner, capability=capability,
                                                   transport_kind=NARHTTPTransportKind.NAR_BOOTSTRAP_HTTP)
        guarded.mount("https://", _FakeAdapter(events))
        def operation():
            response = guarded.get(URL, headers={"Accept-Encoding": "identity"}, stream=True,
                                   allow_redirects=False, verify=True, timeout=(10.0, 10.0))
            return response.content
        assert measure_nar_operation(runner=runner, capability=capability,
                                     stage=Stage.BOOTSTRAP_HOME_ACQUISITION, correlation=CORRELATION,
                                     load_context=LOAD, expected_url=URL,
                                     transport_kind=NARHTTPTransportKind.NAR_BOOTSTRAP_HTTP,
                                     operation=operation) == b"okay"
        assert events == ["adapter"]
        first = runner._connection.execute("SELECT identity FROM nar_operational_timing_v2_attempts ORDER BY attempt_sequence").fetchone()[0]
        env = runner.attempt_archive.load_environment_for_attempt(attempt_identity=first)
        assert env.qualification is NARRequestEnvironmentQualification.QUALIFIED_DIRECT_REQUEST_ENVIRONMENT
        with pytest.raises(TimingArchiveError, match="controlled pre-send"):
            runner.attempt_archive.save_environment(verification=env)
        assert runner.attempt_archive.list_nonqualifying_http_attempts(claim_identity=capability.claim_identity) == ()


def test_guard_nonqualifying_proxy_prevents_send_and_is_not_official_sample(tmp_path, monkeypatch):
    monkeypatch.setenv("HTTPS_PROXY", "http://secret:password@proxy.invalid:8888")
    monkeypatch.delenv("NO_PROXY", raising=False)
    runner, config, session = _campaign(tmp_path, monkeypatch, stages=(Stage.BOOTSTRAP_HOME_ACQUISITION,))
    with runner:
        capability = _activate(runner, config, session)
        events = []
        guarded = NAROfficialTimingGuardedSession(runner=runner, capability=capability,
                                                   transport_kind=NARHTTPTransportKind.NAR_BOOTSTRAP_HTTP)
        guarded.mount("https://", _FakeAdapter(events))
        with pytest.raises(NARRequestEnvironmentRejected):
            measure_nar_operation(runner=runner, capability=capability,
                                  stage=Stage.BOOTSTRAP_HOME_ACQUISITION, correlation=CORRELATION,
                                  load_context=LOAD, expected_url=URL,
                                  transport_kind=NARHTTPTransportKind.NAR_BOOTSTRAP_HTTP,
                                  operation=lambda: guarded.get(URL, headers={"Accept-Encoding": "identity"}, stream=True,
                                                                allow_redirects=False, verify=True, timeout=(10.0, 10.0)))
        assert events == []
        assert len(runner.attempt_archive.list_nonqualifying_http_attempts(claim_identity=capability.claim_identity)) == 1
        payload = runner._connection.execute("SELECT payload_json FROM nar_operational_timing_request_environment_verifications").fetchone()[0]
        assert "password" not in payload and "proxy.invalid" not in payload


@pytest.mark.parametrize("environment,request_options,qualifies", [
    ({"ALL_PROXY": "http://proxy.invalid:9"}, {}, False),
    ({"HTTPS_PROXY": "http://proxy.invalid:9", "NO_PROXY": "www.keiba.go.jp"}, {}, True),
    ({"REQUESTS_CA_BUNDLE": "C:/private/ca.pem"}, {}, False),
    ({"CURL_CA_BUNDLE": "C:/private/ca.pem"}, {}, False),
    ({}, {"verify": False}, False),
    ({}, {"cert": "C:/private/client.pem"}, False),
    ({}, {"headers": {"Accept-Encoding": "identity", "Authorization": "Bearer SECRET"}}, False),
])
def test_actual_send_direct_policy_variants(tmp_path, monkeypatch, environment, request_options, qualifies):
    for name in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE"):
        monkeypatch.delenv(name, raising=False)
    for name, value in environment.items():
        monkeypatch.setenv(name, value)
    runner, config, session = _campaign(tmp_path, monkeypatch, stages=(Stage.BOOTSTRAP_HOME_ACQUISITION,))
    with runner:
        capability = _activate(runner, config, session)
        events = []
        guarded = NAROfficialTimingGuardedSession(runner=runner, capability=capability,
                                                   transport_kind=NARHTTPTransportKind.NAR_BOOTSTRAP_HTTP)
        guarded.mount("https://", _FakeAdapter(events))
        kwargs = {"headers": {"Accept-Encoding": "identity"}, "stream": True,
                  "allow_redirects": False, "verify": True, "timeout": (10.0, 10.0)} | request_options
        def operation():
            return guarded.get(URL, **kwargs)
        if qualifies:
            measure_nar_operation(runner=runner, capability=capability,
                                  stage=Stage.BOOTSTRAP_HOME_ACQUISITION, correlation=CORRELATION,
                                  load_context=LOAD, expected_url=URL,
                                  transport_kind=NARHTTPTransportKind.NAR_BOOTSTRAP_HTTP,
                                  operation=operation)
            assert events == ["adapter"]
        else:
            with pytest.raises(NARRequestEnvironmentRejected):
                measure_nar_operation(runner=runner, capability=capability,
                                      stage=Stage.BOOTSTRAP_HOME_ACQUISITION, correlation=CORRELATION,
                                      load_context=LOAD, expected_url=URL,
                                      transport_kind=NARHTTPTransportKind.NAR_BOOTSTRAP_HTTP,
                                      operation=operation)
            assert events == []
        row = runner._connection.execute("SELECT payload_json FROM nar_operational_timing_request_environment_verifications").fetchone()[0]
        assert "SECRET" not in row and "C:/private" not in row and "proxy.invalid" not in row


def test_market_trust_env_false_still_guarded(tmp_path, monkeypatch):
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.invalid:9")
    runner, config, session = _campaign(tmp_path, monkeypatch, stages=(Stage.MARKET_ODDS_RAW_ACQUISITION,))
    with runner:
        capability = _activate(runner, config, session)
        events = []
        guarded = NAROfficialTimingGuardedSession(runner=runner, capability=capability,
                                                   transport_kind=NARHTTPTransportKind.NAR_MARKET_ODDS_RAW_HTTP)
        guarded.trust_env = False
        guarded.mount("https://", _FakeAdapter(events))
        measure_nar_operation(runner=runner, capability=capability,
                              stage=Stage.MARKET_ODDS_RAW_ACQUISITION, correlation=CORRELATION,
                              load_context=LOAD, expected_url=URL,
                              transport_kind=NARHTTPTransportKind.NAR_MARKET_ODDS_RAW_HTTP,
                              operation=lambda: guarded.get(URL, headers={"Accept-Encoding": "identity"},
                                                            stream=True, allow_redirects=False, verify=True,
                                                            timeout=(10.0, 20.0)))
        assert events == ["adapter"]


def test_netrc_auth_and_prepared_url_mismatch_are_nonqualifying(tmp_path, monkeypatch):
    for name in ("HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE"):
        monkeypatch.delenv(name, raising=False)
    netrc_path = tmp_path / "netrc"
    netrc_path.write_text("machine www.keiba.go.jp login alice password SECRET\n", encoding="utf-8")
    monkeypatch.setenv("NETRC", str(netrc_path))
    runner, config, session = _campaign(tmp_path, monkeypatch, stages=(Stage.BOOTSTRAP_HOME_ACQUISITION,))
    with runner:
        capability = _activate(runner, config, session)
        events = []
        guarded = NAROfficialTimingGuardedSession(runner=runner, capability=capability,
                                                   transport_kind=NARHTTPTransportKind.NAR_BOOTSTRAP_HTTP)
        guarded.mount("https://", _FakeAdapter(events))
        with pytest.raises(NARRequestEnvironmentRejected):
            measure_nar_operation(runner=runner, capability=capability,
                                  stage=Stage.BOOTSTRAP_HOME_ACQUISITION, correlation=CORRELATION,
                                  load_context=LOAD, expected_url=URL,
                                  transport_kind=NARHTTPTransportKind.NAR_BOOTSTRAP_HTTP,
                                  operation=lambda: guarded.get(URL, headers={"Accept-Encoding": "identity"},
                                                                stream=True, allow_redirects=False, verify=True,
                                                                timeout=(10.0, 10.0)))
        assert events == []
        payload = runner._connection.execute("SELECT payload_json FROM nar_operational_timing_request_environment_verifications").fetchone()[0]
        assert "SECRET" not in payload and "alice" not in payload


def test_guard_rejects_second_send_within_one_attempt(tmp_path, monkeypatch):
    for name in ("HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE", "NETRC"):
        monkeypatch.delenv(name, raising=False)
    runner, config, session = _campaign(tmp_path, monkeypatch, stages=(Stage.BOOTSTRAP_HOME_ACQUISITION,))
    with runner:
        capability = _activate(runner, config, session)
        events = []
        guarded = NAROfficialTimingGuardedSession(runner=runner, capability=capability,
                                                   transport_kind=NARHTTPTransportKind.NAR_BOOTSTRAP_HTTP)
        guarded.mount("https://", _FakeAdapter(events))
        def two_sends():
            for _ in range(2):
                guarded.get(URL, headers={"Accept-Encoding": "identity"}, stream=True,
                            allow_redirects=False, verify=True, timeout=(10.0, 10.0))
        with pytest.raises(NARRequestEnvironmentRejected, match="second send"):
            measure_nar_operation(runner=runner, capability=capability,
                                  stage=Stage.BOOTSTRAP_HOME_ACQUISITION, correlation=CORRELATION,
                                  load_context=LOAD, expected_url=URL,
                                  transport_kind=NARHTTPTransportKind.NAR_BOOTSTRAP_HTTP,
                                  operation=two_sends)
        assert events == ["adapter"]
        assert runner._connection.execute("SELECT COUNT(*) FROM nar_operational_timing_request_environment_verifications").fetchone()[0] == 1
