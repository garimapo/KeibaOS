from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
import subprocess

import pytest
import requests

from scripts.simulation.nar_operational_timing_diagnostic_campaign import (
    NAROperationalTimingDiagnosticFixtureBundleV1 as Fixture,
    NAROperationalTimingDiagnosticCampaignPlanV1 as Plan,
    NARDiagnosticPlanNodeSpecV1 as Node,
    NARDiagnosticContinuationV1 as Continuation,
    NARDiagnosticCompositionV1 as Composition,
    NAROperationalTimingDiagnosticExecutionDeclarationV1 as Declaration,
    NARDiagnosticFixtureMemberV1,
)
from scripts.simulation.nar_operational_timing_campaign_reconciliation import (
    NARDiagnosticPlanNodeState as NodeState,
    NARDiagnosticObservationQualification as Observation,
    reconcile_diagnostic_evidence, reconcile_diagnostic_archive,
)
from scripts.simulation.nar_operational_timing_diagnostic_harness import (
    NARDiagnosticOperationV1, NARDiagnosticFakeHTTPAdapter,
    issue_diagnostic_execution_context, diagnostic_guarded_session_factory,
)
from scripts.simulation.nar_operational_timing_campaign_runner import NAROperationalTimingCampaignRunner
from scripts.simulation.nar_operational_timing_runtime_source_provenance import _git_manifest
from scripts.simulation.nar_operational_timing_runtime_profile import derive_static_runtime_transport_profile
from scripts.simulation.nar_operational_timing_observability import (
    NARHTTPTransportKind, NARHTTPTransportProfile, NARTimingCorrelation,
    NARTimingCorrelationScope, NARTimingLoadContext,
)
from scripts.simulation.nar_operational_timing_observability_v2 import (
    NAROperationalTimingMeasurementConfigurationV2 as Configuration,
    NAROperationalTimingMeasurementSessionV2 as Session,
    NAROperationalTimingStageV2 as Stage,
)
from scripts.simulation.nar_operational_timing_attempt_v2 import (
    NAROperationalTimingAttemptV2 as Attempt, NAROperationalTimingTerminalV2 as Terminal,
    NARRequestEffectiveEnvironmentVerification as Environment,
    NARExpectedRequestEnvironmentPolicy,
    NARRequestEnvironmentQualification as EnvironmentQualification,
    NARSafeSendSetting, NARTimingTerminalDispositionV2 as Disposition,
    NARTimingFailureClassificationV2 as Failure,
)
from scripts.simulation.nar_operational_timing_session_activation_v2 import issue_nar_operational_timing_session_activation_v2
from scripts.simulation.nar_operational_timing_diagnostic_archive_migration import (
    REGISTRY, DECLARATIONS, PLANS, _DDL, bootstrap_nar_operational_timing_diagnostic_archive,
    require_nar_operational_timing_diagnostic_archive_schema,
)
from scripts.simulation.nar_operational_timing_attempt_archive_migration import (
    require_nar_operational_timing_attempt_archive_schema,
)
from scripts.simulation.sqlite_nar_operational_timing_diagnostic_archive import _DIAGNOSTIC_ISSUANCE_MARKER
from scripts.simulation.sqlite_nar_operational_timing_attempt_archive import _TIMING_EVIDENCE_ISSUANCE_MARKER
from scripts.simulation.sqlite_nar_operational_timing_observability_archive import TimingArchiveError
from scripts.simulation.nar_historical_daily_target_bootstrap_live_capture import (
    RequestsNARMonthlyConveneInfoBootstrapHTTPTransport,
    _PageKind, _URLS, _CONTENT_TYPES,
)
from scripts.simulation.nar_historical_daily_target_live_capture import _RequestsNARHistoricalDailyTargetHTTPTransport
from scripts.simulation.nar_official_response_live_capture import _RequestsNAROfficialHTTPTransport


ROOT = Path(__file__).resolve().parents[1]
COMMIT = "d250e0954f50dfe27d6efe569f149a876b8ca684"
FIXTURE_PATH = "tests/fixtures/nar_daily_target_bootstrap/nar_home_supplier.utf8.html"
START = datetime(2030, 1, 1, tzinfo=timezone.utc)
URL = _URLS[_PageKind.OFFICIAL_HOME]
URL_SHA = sha256(URL.encode("utf-8")).hexdigest()
CORRELATION = NARTimingCorrelation(NARTimingCorrelationScope.PROVIDER)
LOAD = NARTimingLoadContext(1, 1, False)


def _fixture():
    return Fixture.from_git(repository_root=ROOT, repository_identity="garimapo/KeibaOS",
                            commit_sha=COMMIT, paths=(FIXTURE_PATH,))


def _node(key, stage, sequence, *, parents=(), continuation=Continuation.INDEPENDENT,
          http=False, fixture_path=None):
    return Node(key, stage, sequence,
                "request-url-sha256:" + URL_SHA if http else "correlation:" + CORRELATION.correlation_identity,
                CORRELATION, tuple(parents), continuation, Composition.EXCLUSIVE_LEAF,
                fixture_path, NARHTTPTransportKind.NAR_BOOTSTRAP_HTTP if http else None,
                URL_SHA if http else None)


def _plan(fixture, config, session, nodes):
    return Plan("garimapo/KeibaOS", COMMIT, config.configuration_identity,
                session.session_identity, fixture.bundle_identity, tuple(nodes), "diagnostic-fixture-target")


def _setup(tmp_path, monkeypatch, *, stages=(Stage.SNAPSHOT_CONSTRUCTION,)):
    bundle, _ = _git_manifest(ROOT, COMMIT)
    profile = derive_static_runtime_transport_profile()
    config = Configuration(COMMIT, stages, tuple(NARHTTPTransportProfile(
        x.kind, x.connect_timeout_microseconds, x.read_timeout_microseconds)
        for x in profile.descriptors))
    session = Session(config, START, START + timedelta(hours=1))
    times = iter((START - timedelta(seconds=2), START - timedelta(seconds=1),
                  *(START + timedelta(seconds=i) for i in range(1, 60))))
    ticks = iter(range(0, 100_000_000, 100_000))
    runner = NAROperationalTimingCampaignRunner(
        archive_path=tmp_path / "diagnostic.sqlite", repository_root=ROOT, bundle_root=tmp_path,
        bundle=bundle, session_identity=session.session_identity, utc_clock=lambda: next(times),
        monotonic_timer_ns=lambda: next(ticks), enable_attempt_archive=True)
    monkeypatch.setattr(NAROperationalTimingCampaignRunner, "_require_isolated_source", lambda self: None)
    return runner, config, session


def _activate(runner, config, session):
    authority = runner.attempt_archive.runtime.v2
    authority.save_configuration(configuration=config)
    authority.save_session(session=session)
    issue_nar_operational_timing_session_activation_v2(
        session=session, archive=authority, utc_clock=lambda: START - timedelta(minutes=1))
    return runner.issue_current_process_execution()


def test_git_fixture_identity_and_immutable_bytes():
    fixture = _fixture()
    assert fixture == _fixture()
    assert fixture.read_verified_bytes(repository_root=ROOT)[FIXTURE_PATH]
    assert fixture == Fixture.from_json(fixture.canonical_bytes().decode("utf-8"))
    member = fixture.members[0]
    with pytest.raises(ValueError):
        Fixture(fixture.repository_identity, fixture.commit_sha, fixture.tree_sha, (member, member))
    wrong = NARDiagnosticFixtureMemberV1(member.path, member.blob_sha, member.byte_length + 1, member.sha256_hex)
    with pytest.raises(ValueError, match="bytes differ"):
        Fixture(fixture.repository_identity, fixture.commit_sha, fixture.tree_sha, (wrong,)).read_verified_bytes(repository_root=ROOT)
    bad_hash = NARDiagnosticFixtureMemberV1(member.path, member.blob_sha, member.byte_length, "0" * 64)
    with pytest.raises(ValueError, match="bytes differ"):
        Fixture(fixture.repository_identity, fixture.commit_sha, fixture.tree_sha, (bad_hash,)).read_verified_bytes(repository_root=ROOT)
    bad_blob = NARDiagnosticFixtureMemberV1(member.path, "0" * 40, member.byte_length, member.sha256_hex)
    with pytest.raises(ValueError, match="path/blob"):
        Fixture(fixture.repository_identity, fixture.commit_sha, fixture.tree_sha, (bad_blob,)).read_verified_bytes(repository_root=ROOT)


def test_explicit_companion_controlled_publication_and_normal_bootstrap(tmp_path, monkeypatch):
    runner, config, session = _setup(tmp_path, monkeypatch)
    fixture = _fixture()
    plan = _plan(fixture, config, session, (_node("snapshot", Stage.SNAPSHOT_CONSTRUCTION, 0),))
    with runner:
        capability = _activate(runner, config, session)
        assert runner._connection.execute(
            "SELECT name FROM sqlite_master WHERE name=?", (REGISTRY,)).fetchone() is None
        context = issue_diagnostic_execution_context(runner=runner, capability=capability,
                                                     fixture=fixture, plan=plan)
        require_nar_operational_timing_diagnostic_archive_schema(runner._connection)
        with pytest.raises(RuntimeError):
            require_nar_operational_timing_attempt_archive_schema(runner._connection)
        with pytest.raises(TimingArchiveError):
            context.archive.save_fixture(fixture=fixture)
        with pytest.raises(TimingArchiveError):
            context.archive.save_plan(plan=plan)
        with pytest.raises(TimingArchiveError):
            context.archive.save_declaration(declaration=context.declaration)
        assert context.archive.save_fixture(fixture=fixture, _issuance_marker=_DIAGNOSTIC_ISSUANCE_MARKER) is False
        assert runner._connection.execute(f"SELECT COUNT(*) FROM {PLANS}").fetchone() == (1,)
        assert runner._connection.execute(f"SELECT COUNT(*) FROM {DECLARATIONS}").fetchone() == (1,)
        assert context.measure_next(node_key="snapshot", operation=NARDiagnosticOperationV1(
            lambda: "value", LOAD)) == "value"
        changes = runner._connection.total_changes
        result = reconcile_diagnostic_archive(archive=context.archive, declaration=context.declaration)
        assert result == reconcile_diagnostic_archive(archive=context.archive, declaration=context.declaration)
        assert runner._connection.total_changes == changes
        assert result.completeness == "COMPLETE_AS_PREDECLARED_DIAGNOSTIC_PLAN"
        assert result.nodes[0].inner_observation is Observation.QUALIFIED_OPERATIONAL_TIMING_OBSERVATION
        assert result.nodes[0].payload()["official_eligibility"] == "DIAGNOSTIC_ONLY"


def test_plan_cannot_declare_stage_absent_from_activated_v2_configuration(tmp_path, monkeypatch):
    runner, config, session = _setup(tmp_path, monkeypatch)
    fixture = _fixture()
    plan = _plan(fixture, config, session, (_node("normalization", Stage.NORMALIZATION, 0),))
    with runner:
        capability = _activate(runner, config, session)
        with pytest.raises(TimingArchiveError, match="plan fixture/session ancestry"):
            issue_diagnostic_execution_context(runner=runner, capability=capability,
                                               fixture=fixture, plan=plan)
        assert runner._connection.execute(f"SELECT COUNT(*) FROM {PLANS}").fetchone() == (0,)


def _pure_plan():
    fixture = _fixture()
    config = "nar-operational-timing-config-v2:" + "a" * 64
    session = "nar-operational-timing-session-v2:" + "b" * 64
    nodes = (
        _node("http", Stage.BOOTSTRAP_HOME_ACQUISITION, 0, http=True),
        _node("normalize", Stage.NORMALIZATION, 1, parents=("http",),
              continuation=Continuation.REQUIRES_ALL_PREDECESSOR_SUCCESSFUL_OUTPUTS),
        _node("snapshot", Stage.SNAPSHOT_CONSTRUCTION, 2, parents=("normalize",),
              continuation=Continuation.REQUIRES_ALL_PREDECESSOR_SUCCESSFUL_OUTPUTS),
        _node("independent", Stage.SNAPSHOT_ADAPTER, 3),
    )
    plan = Plan("garimapo/KeibaOS", COMMIT, config, session, fixture.bundle_identity,
                nodes, "diagnostic-fixture-target")
    claim = "nar-operational-timing-campaign-execution-v1:" + "c" * 64
    declaration = Declaration(plan.plan_identity, claim, config, session, fixture.bundle_identity)
    return plan, declaration


def _attempt(plan, declaration, node, seq):
    return Attempt(plan.configuration_identity, plan.session_identity, declaration.claim_identity,
                   node.stage, node.correlation, seq, START + timedelta(seconds=seq), LOAD,
                   NARExpectedRequestEnvironmentPolicy.DIRECT_REQUEST_ENVIRONMENT_V1 if node.transport_kind else None,
                   node.expected_url_sha256)


def _environment(attempt):
    return Environment(attempt.attempt_identity, URL_SHA,
                       derive_static_runtime_transport_profile().profile_identity, True,
                       NARSafeSendSetting.DIRECT, NARSafeSendSetting.TRUE,
                       NARSafeSendSetting.ABSENT, NARSafeSendSetting.ABSENT,
                       NARSafeSendSetting.ABSENT, True, True,
                       EnvironmentQualification.QUALIFIED_DIRECT_REQUEST_ENVIRONMENT)


def test_timeout_observation_survives_dependent_causal_nonexecution_and_independent_node():
    plan, declaration = _pure_plan()
    http = _attempt(plan, declaration, plan.nodes[0], 0)
    independent = _attempt(plan, declaration, plan.nodes[3], 1)
    timeout = Terminal(http.attempt_identity, START + timedelta(seconds=1), 1000,
                       Disposition.TIMEOUT, Failure.READ_TIMEOUT)
    success = Terminal(independent.attempt_identity, START + timedelta(seconds=3), 1000, Disposition.SUCCESS)
    result = reconcile_diagnostic_evidence(
        plan=plan, declaration=declaration, attempts=(http, independent),
        terminals=(timeout, success), environments=(_environment(http),), overhead=())
    assert [x.state for x in result.nodes] == [
        NodeState.OBSERVED_AS_PLANNED,
        NodeState.EXPECTED_NOT_EXECUTABLE_DUE_TO_UPSTREAM_FAILURE,
        NodeState.EXPECTED_NOT_EXECUTABLE_DUE_TO_UPSTREAM_FAILURE,
        NodeState.OBSERVED_AS_PLANNED]
    assert result.nodes[0].inner_observation is Observation.QUALIFIED_OPERATIONAL_TIMING_OBSERVATION
    assert result.nodes[0].terminal_disposition is Disposition.TIMEOUT
    assert result.nodes[0].missing_publication_overhead
    assert result.payload()["official_eligibility"] == "DIAGNOSTIC_ONLY"


def test_unresolved_predecessor_never_proves_failure_and_success_missing_is_unexplained():
    plan, declaration = _pure_plan()
    http = _attempt(plan, declaration, plan.nodes[0], 0)
    unresolved = reconcile_diagnostic_evidence(plan=plan, declaration=declaration,
        attempts=(http,), terminals=(), environments=(_environment(http),), overhead=())
    assert unresolved.nodes[0].state is NodeState.EVIDENCE_INTEGRITY_FAILURE
    assert unresolved.nodes[1].state is NodeState.BLOCKED_BY_UNRESOLVED_PREDECESSOR
    success = Terminal(http.attempt_identity, START + timedelta(seconds=1), 1000, Disposition.SUCCESS)
    missing = reconcile_diagnostic_evidence(plan=plan, declaration=declaration,
        attempts=(http,), terminals=(success,), environments=(_environment(http),), overhead=())
    assert missing.nodes[1].state is NodeState.MISSING_UNEXPLAINED
    assert missing.nodes[0].inner_observation is Observation.QUALIFIED_OPERATIONAL_TIMING_OBSERVATION


def test_precondition_rejection_blocks_descendants_without_provider_observation():
    plan, declaration = _pure_plan()
    http = _attempt(plan, declaration, plan.nodes[0], 0)
    terminal = Terminal(http.attempt_identity, START + timedelta(seconds=1), 1000,
                        Disposition.UNSUPPORTED, Failure.UNSUPPORTED)
    result = reconcile_diagnostic_evidence(plan=plan, declaration=declaration,
        attempts=(http,), terminals=(terminal,), environments=(), overhead=())
    assert result.nodes[0].inner_observation is Observation.NONQUALIFYING_REQUEST_ENVIRONMENT
    assert result.nodes[0].state is NodeState.PRECONDITION_BLOCKED
    assert result.nodes[1].state is NodeState.PRECONDITION_BLOCKED


def test_guarded_fake_adapter_runs_after_verification_without_provider_network(tmp_path, monkeypatch):
    for key in ("HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE"):
        monkeypatch.delenv(key, raising=False)
    runner, config, session = _setup(tmp_path, monkeypatch, stages=(Stage.BOOTSTRAP_HOME_ACQUISITION,))
    fixture = _fixture()
    plan = _plan(fixture, config, session, (_node("home", Stage.BOOTSTRAP_HOME_ACQUISITION,
                                                0, http=True, fixture_path=FIXTURE_PATH),))
    with runner:
        capability = _activate(runner, config, session)
        context = issue_diagnostic_execution_context(runner=runner, capability=capability,
                                                     fixture=fixture, plan=plan)
        adapter = NARDiagnosticFakeHTTPAdapter(
            body=fixture.read_verified_bytes(repository_root=ROOT)[FIXTURE_PATH],
            content_type=_CONTENT_TYPES[_PageKind.OFFICIAL_HOME])
        session_factory, adapter_factory = diagnostic_guarded_session_factory(
            runner=runner, capability=capability, transport_kind=NARHTTPTransportKind.NAR_BOOTSTRAP_HTTP,
            adapter=adapter)
        transport = RequestsNARMonthlyConveneInfoBootstrapHTTPTransport(
            _session_factory=session_factory, _diagnostic_adapter_factory=adapter_factory)
        result = context.measure_next(node_key="home", operation=NARDiagnosticOperationV1(
            lambda: transport.fetch(page_kind=_PageKind.OFFICIAL_HOME, canonical_request_url=URL),
            LOAD, expected_url=URL))
        assert result.response_body == fixture.read_verified_bytes(repository_root=ROOT)[FIXTURE_PATH]
        assert adapter.send_count == 1
        evidence = reconcile_diagnostic_archive(archive=context.archive, declaration=context.declaration)
        assert evidence.nodes[0].inner_observation is Observation.QUALIFIED_OPERATIONAL_TIMING_OBSERVATION
        assert evidence.payload()["official_eligibility"] == "DIAGNOSTIC_ONLY"


def test_no_network_timeout_harness_preserves_observation_and_independent_continuation(tmp_path, monkeypatch):
    for key in ("HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE"):
        monkeypatch.delenv(key, raising=False)
    stages = (Stage.BOOTSTRAP_HOME_ACQUISITION, Stage.NORMALIZATION, Stage.SNAPSHOT_ADAPTER)
    runner, config, session = _setup(tmp_path, monkeypatch, stages=stages)
    fixture = _fixture()
    plan = _plan(fixture, config, session, (
        _node("home", Stage.BOOTSTRAP_HOME_ACQUISITION, 0, http=True, fixture_path=FIXTURE_PATH),
        _node("normalize", Stage.NORMALIZATION, 1, parents=("home",),
              continuation=Continuation.REQUIRES_ALL_PREDECESSOR_SUCCESSFUL_OUTPUTS),
        _node("independent", Stage.SNAPSHOT_ADAPTER, 2),
    ))
    with runner:
        capability = _activate(runner, config, session)
        context = issue_diagnostic_execution_context(runner=runner, capability=capability,
                                                     fixture=fixture, plan=plan)
        adapter = NARDiagnosticFakeHTTPAdapter(failure="READ_TIMEOUT")
        session_factory, adapter_factory = diagnostic_guarded_session_factory(
            runner=runner, capability=capability, transport_kind=NARHTTPTransportKind.NAR_BOOTSTRAP_HTTP,
            adapter=adapter)
        transport = RequestsNARMonthlyConveneInfoBootstrapHTTPTransport(
            _session_factory=session_factory, _diagnostic_adapter_factory=adapter_factory)
        independent_calls = []
        result = context.run(operations={
            "home": NARDiagnosticOperationV1(
                lambda: transport.fetch(page_kind=_PageKind.OFFICIAL_HOME, canonical_request_url=URL),
                LOAD, expected_url=URL),
            "normalize": NARDiagnosticOperationV1(lambda: pytest.fail("causally blocked node executed"), LOAD),
            "independent": NARDiagnosticOperationV1(lambda: independent_calls.append(1) or "ok", LOAD),
        })
        assert isinstance(result["home"], Exception)
        assert result["independent"] == "ok" and independent_calls == [1]
        evidence = reconcile_diagnostic_archive(archive=context.archive, declaration=context.declaration)
        assert [x.state for x in evidence.nodes] == [
            NodeState.OBSERVED_AS_PLANNED,
            NodeState.EXPECTED_NOT_EXECUTABLE_DUE_TO_UPSTREAM_FAILURE,
            NodeState.OBSERVED_AS_PLANNED]
        assert evidence.nodes[0].inner_observation is Observation.QUALIFIED_OPERATIONAL_TIMING_OBSERVATION
        assert evidence.nodes[0].terminal_disposition is Disposition.TIMEOUT
        assert adapter.send_count == 1


def test_guard_environment_rejection_does_not_call_fake_adapter(tmp_path, monkeypatch):
    monkeypatch.setenv("NO_PROXY", "")
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:1")
    runner, config, session = _setup(tmp_path, monkeypatch, stages=(Stage.BOOTSTRAP_HOME_ACQUISITION, Stage.NORMALIZATION))
    fixture = _fixture()
    plan = _plan(fixture, config, session, (
        _node("home", Stage.BOOTSTRAP_HOME_ACQUISITION, 0, http=True),
        _node("normalize", Stage.NORMALIZATION, 1, parents=("home",),
              continuation=Continuation.REQUIRES_ALL_PREDECESSOR_SUCCESSFUL_OUTPUTS),
    ))
    with runner:
        capability = _activate(runner, config, session)
        context = issue_diagnostic_execution_context(runner=runner, capability=capability,
                                                     fixture=fixture, plan=plan)
        adapter = NARDiagnosticFakeHTTPAdapter(body=b"never sent")
        session_factory, adapter_factory = diagnostic_guarded_session_factory(
            runner=runner, capability=capability, transport_kind=NARHTTPTransportKind.NAR_BOOTSTRAP_HTTP,
            adapter=adapter)
        transport = RequestsNARMonthlyConveneInfoBootstrapHTTPTransport(
            _session_factory=session_factory, _diagnostic_adapter_factory=adapter_factory)
        context.run(operations={
            "home": NARDiagnosticOperationV1(
                lambda: transport.fetch(page_kind=_PageKind.OFFICIAL_HOME, canonical_request_url=URL),
                LOAD, expected_url=URL),
            "normalize": NARDiagnosticOperationV1(lambda: pytest.fail("blocked normalization executed"), LOAD),
        })
        evidence = reconcile_diagnostic_archive(archive=context.archive, declaration=context.declaration)
        assert adapter.send_count == 0
        assert evidence.nodes[0].inner_observation is Observation.NONQUALIFYING_REQUEST_ENVIRONMENT
        assert evidence.nodes[0].state is NodeState.PRECONDITION_BLOCKED
        assert evidence.nodes[1].state is NodeState.PRECONDITION_BLOCKED


def test_unplanned_node_and_predeclaration_gate_fail_closed(tmp_path, monkeypatch):
    runner, config, session = _setup(tmp_path, monkeypatch)
    fixture = _fixture()
    plan = _plan(fixture, config, session, (_node("snapshot", Stage.SNAPSHOT_CONSTRUCTION, 0),))
    with runner:
        capability = _activate(runner, config, session)
        context = issue_diagnostic_execution_context(runner=runner, capability=capability,
                                                     fixture=fixture, plan=plan)
        with pytest.raises(RuntimeError, match="exact runnable plan node"):
            context.measure_next(node_key="other", operation=NARDiagnosticOperationV1(lambda: None, LOAD))
        assert runner._connection.execute(
            "SELECT COUNT(*) FROM nar_operational_timing_v2_attempts").fetchone() == (0,)
        direct = Attempt(config.configuration_identity, session.session_identity, capability.claim_identity,
                         Stage.SNAPSHOT_CONSTRUCTION, CORRELATION, 0, START + timedelta(seconds=1), LOAD)
        # A direct archive write cannot gain current-process controlled publication merely from ancestry.
        with pytest.raises(TimingArchiveError):
            runner.attempt_archive.save_attempt(attempt=direct)
        out_of_plan = Attempt(config.configuration_identity, session.session_identity, capability.claim_identity,
                              Stage.SNAPSHOT_CONSTRUCTION, CORRELATION, 5,
                              START + timedelta(seconds=2), LOAD)
        with pytest.raises(TimingArchiveError):
            runner.attempt_archive.save_attempt(attempt=out_of_plan,
                _issuance_marker=_TIMING_EVIDENCE_ISSUANCE_MARKER)
        assert context.measure_next(node_key="snapshot", operation=NARDiagnosticOperationV1(
            lambda: "ok", LOAD)) == "ok"
        with pytest.raises(TimingArchiveError, match="backfill"):
            context.archive.save_declaration(declaration=context.declaration,
                                             _issuance_marker=_DIAGNOSTIC_ISSUANCE_MARKER)


def test_default_transport_profile_preserved_with_private_diagnostic_factory():
    profile = derive_static_runtime_transport_profile()
    assert profile.profile_identity == "nar-static-runtime-transport-profile-v1:4d5cc1d495cdfc4a24561b85a2ad90c980438320f1cc36e8f0dec47fcd3e537c"
    assert [(x.connect_timeout_microseconds, x.read_timeout_microseconds, x.adapter_retry_total,
             x.adapter_retry_read, x.adapter_backoff_microseconds, x.allow_redirects,
             x.verify_tls, x.stream, x.accept_encoding, x.trust_env) for x in profile.descriptors] == [
        (10_000_000, 10_000_000, 0, False, 0, False, True, True, "identity", True),
        (10_000_000, 10_000_000, 0, False, 0, False, True, True, "identity", True),
        (10_000_000, 10_000_000, 0, False, 0, False, True, True, "identity", True),
        (10_000_000, 20_000_000, 0, False, 0, False, True, True, "identity", False),
    ]


def test_three_persistent_transports_mount_private_adapter_without_changing_defaults():
    for transport_type in (RequestsNARMonthlyConveneInfoBootstrapHTTPTransport,
                           _RequestsNARHistoricalDailyTargetHTTPTransport,
                           _RequestsNAROfficialHTTPTransport):
        adapter = NARDiagnosticFakeHTTPAdapter()
        transport = transport_type(_diagnostic_adapter_factory=lambda: adapter)
        assert transport._session.get_adapter("https://www.keiba.go.jp/") is adapter
        transport._session.close()


@pytest.mark.parametrize(("failure", "error_type"), (
    ("CONNECT_TIMEOUT", requests.exceptions.ConnectTimeout),
    ("READ_TIMEOUT", requests.exceptions.ReadTimeout),
    ("TRANSPORT", requests.exceptions.ConnectionError),
))
def test_fake_adapter_closed_failure_outcomes_never_use_network(failure, error_type):
    adapter = NARDiagnosticFakeHTTPAdapter(failure=failure)
    with pytest.raises(error_type):
        adapter.send(object())
    assert adapter.send_count == 1


def test_attempt_before_declaration_and_partial_companion_fail_closed(tmp_path, monkeypatch):
    runner, config, session = _setup(tmp_path, monkeypatch)
    with runner:
        capability = _activate(runner, config, session)
        bootstrap_nar_operational_timing_diagnostic_archive(connection=runner._connection,
                                                            campaign_lock=runner.lock)
        attempt = Attempt(config.configuration_identity, session.session_identity,
                          capability.claim_identity, Stage.SNAPSHOT_CONSTRUCTION,
                          CORRELATION, 0, START + timedelta(seconds=1), LOAD)
        with pytest.raises(TimingArchiveError, match="parent or identity conflicts"):
            runner.attempt_archive.save_attempt(attempt=attempt,
                _issuance_marker=_TIMING_EVIDENCE_ISSUANCE_MARKER)
        assert runner._connection.execute(
            "SELECT COUNT(*) FROM nar_operational_timing_v2_attempts").fetchone() == (0,)
        trigger = "trg_nar_operational_timing_v2_attempts_diagnostic_plan_gate"
        assert trigger in _DDL
        runner._connection.execute(f"DROP TRIGGER {trigger}")
        runner._connection.commit()
        with pytest.raises(RuntimeError, match="topology"):
            require_nar_operational_timing_diagnostic_archive_schema(runner._connection)
        with pytest.raises(RuntimeError):
            runner.attempt_archive.runtime.v2.load_session(session_identity=session.session_identity)


def test_fixture_uses_committed_blob_after_worktree_mutation(tmp_path):
    root = tmp_path / "fixture-repo"
    root.mkdir()
    def git(*args):
        return subprocess.run(("git", "-C", str(root), *args), check=True,
                              capture_output=True, text=True).stdout.strip()
    git("init", "-q")
    git("remote", "add", "origin", "https://github.com/garimapo/KeibaOS.git")
    path = root / "fixture.html"
    path.write_bytes(b"reviewed committed fixture")
    git("add", "fixture.html")
    git("-c", "user.name=Diagnostic Test", "-c", "user.email=diagnostic@example.invalid",
        "commit", "-qm", "fixture")
    commit = git("rev-parse", "HEAD")
    bundle = Fixture.from_git(repository_root=root, repository_identity="garimapo/KeibaOS",
                              commit_sha=commit, paths=("fixture.html",))
    path.write_bytes(b"mutable worktree changed")
    assert bundle.read_verified_bytes(repository_root=root)["fixture.html"] == b"reviewed committed fixture"
    with pytest.raises(ValueError):
        Fixture.from_git(repository_root=root, repository_identity="garimapo/KeibaOS",
                         commit_sha=commit, paths=("absent.html",))


def test_unexpected_extra_attempt_and_sequence_gap_are_integrity_defects():
    plan, declaration = _pure_plan()
    expected = _attempt(plan, declaration, plan.nodes[0], 0)
    extra = _attempt(plan, declaration, plan.nodes[3], 2)
    result = reconcile_diagnostic_evidence(plan=plan, declaration=declaration,
        attempts=(expected, extra), terminals=(
            Terminal(expected.attempt_identity, START + timedelta(seconds=1), 1000, Disposition.SUCCESS),
            Terminal(extra.attempt_identity, START + timedelta(seconds=3), 1000, Disposition.SUCCESS)),
        environments=(_environment(expected),), overhead=())
    assert extra.attempt_identity in result.extra_attempt_identities
    assert 1 in result.sequence_errors
    assert result.completeness == "EVIDENCE_INCOMPLETE"


def test_unresolved_stage_boundaries_and_recursive_overhead_cannot_be_operation_nodes():
    for stage in (Stage.PARSING, Stage.RAW_CAPTURE_VALIDATION,
                  Stage.FREEZE_RECEIPT_PUBLICATION, Stage.ATTEMPT_START_PUBLICATION,
                  Stage.CAMPAIGN_EXECUTION_PREPARATION, Stage.SHADOW_ARTIFACT_PUBLICATION):
        with pytest.raises(ValueError, match="invalid diagnostic operation node"):
            _node("not_reviewed", stage, 0)


def test_skipped_predecessor_cannot_authorize_after_terminal_continuation():
    plan, declaration = _pure_plan()
    http = _attempt(plan, declaration, plan.nodes[0], 0)
    timeout = Terminal(http.attempt_identity, START + timedelta(seconds=1), 1000,
                       Disposition.TIMEOUT, Failure.READ_TIMEOUT)
    result = reconcile_diagnostic_evidence(
        plan=plan, declaration=declaration, attempts=(http,),
        terminals=(timeout,), environments=(_environment(http),), overhead=())
    assert result.nodes[1].state is NodeState.EXPECTED_NOT_EXECUTABLE_DUE_TO_UPSTREAM_FAILURE
    assert result.nodes[2].state is NodeState.EXPECTED_NOT_EXECUTABLE_DUE_TO_UPSTREAM_FAILURE
    with pytest.raises(ValueError, match="terminal branch"):
        Plan(plan.repository_identity, plan.commit_sha, plan.configuration_identity,
             plan.session_identity, plan.fixture_bundle_identity, (
                 Node("upstream", Stage.NORMALIZATION, 0,
                      "correlation:" + CORRELATION.correlation_identity,
                      CORRELATION, (), Continuation.INDEPENDENT, Composition.EXCLUSIVE_LEAF,
                      terminal_on_non_success=True),
                 Node("invalid", Stage.SNAPSHOT_CONSTRUCTION, 1,
                      "correlation:" + CORRELATION.correlation_identity,
                      CORRELATION, ("upstream",),
                      Continuation.EXECUTE_AFTER_PREDECESSORS_TERMINATE_REGARDLESS_OUTCOME,
                      Composition.EXCLUSIVE_LEAF)), plan.scope)


def test_duplicate_child_evidence_is_not_silently_collapsed():
    plan, declaration = _pure_plan()
    http = _attempt(plan, declaration, plan.nodes[0], 0)
    terminal = Terminal(http.attempt_identity, START + timedelta(seconds=1), 1000,
                        Disposition.SUCCESS)
    result = reconcile_diagnostic_evidence(
        plan=plan, declaration=declaration, attempts=(http,),
        terminals=(terminal, terminal), environments=(_environment(http),), overhead=())
    assert "DUPLICATE_TERMINAL" in result.ancestry_errors
    assert result.completeness == "EVIDENCE_INCOMPLETE"
