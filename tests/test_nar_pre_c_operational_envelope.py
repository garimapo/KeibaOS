"""Precommit mechanics only; these are NOT final sealed Git-object verification."""
from contextlib import contextmanager
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3

import pytest

from scripts.simulation.nar_pre_c_operational_envelope import (
    NARPreCHistoryMode as Mode, NARPreCEnvelopeError, NARPreCPrestagedInputManifestV1 as Manifest,
    NARPreCOperationalEnvelopeExecutionPlanV1 as Plan, NARPreCOperationalEnvelopeV1 as Root,
    NARPreCEnvelopeStartEvidenceV1 as Start, NARCurrentEntryDiscoveryClosureV1 as Entries,
    NARPastRaceDiscoveryClosureV1 as History, NARPreCEnvelopeCompletionEvidenceV1 as Completion,
    elapsed_microseconds_from_ns,
)
from scripts.simulation.nar_pre_c_operational_envelope_harness import (
    NARPreCCurrentProcessRootContext as Context, run_phase108_no_network_rehearsal,
    prepare_rehearsal_plan, issue_target_pre_c_root, prerequisite_proof, rehearsal_fixture_responses,
)
from scripts.simulation.nar_pre_c_operational_envelope_reconciliation import reconcile_pre_c_archive, NARPreCEnvelopeReconciliationState as State
from scripts.simulation.sqlite_nar_pre_c_operational_envelope_archive import SQLiteNARPreCOperationalEnvelopeArchive as Archive
from scripts.simulation import nar_pre_c_operational_envelope_archive_migration as schema
from scripts.simulation.nar_pre_c_operational_envelope_archive_bootstrap import bootstrap_nar_pre_c_operational_envelope_archive
from scripts.simulation.nar_operational_timing_campaign_runner import NAROperationalTimingCampaignRunner
from scripts.simulation.nar_operational_timing_runtime_source_provenance import _git_manifest
from scripts.simulation.nar_operational_timing_runtime_profile import derive_static_runtime_transport_profile
from scripts.simulation.nar_operational_timing_observability import NARHTTPTransportProfile
from scripts.simulation.nar_operational_timing_observability_v2 import NAROperationalTimingMeasurementConfigurationV2 as Configuration, NAROperationalTimingMeasurementSessionV2 as Session, NAROperationalTimingStageV2 as Stage
from scripts.simulation.nar_operational_timing_session_activation_v2 import issue_nar_operational_timing_session_activation_v2
from scripts.simulation.nar_operational_timing_diagnostic_campaign import NAROperationalTimingDiagnosticFixtureBundleV1 as Fixture
from scripts.simulation.nar_historical_input_source import normalize_nar_historical_input_source_records
from scripts.simulation.nar_official_response_capture_migration_runner import apply_capture_schema_migrations
from scripts.simulation.repositories.sqlite_nar_official_response_capture_repository import SQLiteNAROfficialResponseCaptureRepository
from scripts.simulation.repositories.sqlite_historical_input_snapshot_repository import SQLiteHistoricalInputSnapshotRepository
from scripts.migrations.runner import apply_migrations

ROOT = Path(__file__).resolve().parents[1]
BASE = "fefcda45ce9e01a13724209ae6012b81bbc0bd46"
START = datetime(2026, 7, 4, 10, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def precommit_composition_only(monkeypatch, tmp_path):
    # Explicit test-only source dependency isolation. No production bypass API;
    # final Phase108 source authority is pending approved local commit creation.
    monkeypatch.setattr(NAROperationalTimingCampaignRunner, "_require_isolated_source", lambda self: None)
    for name in ("HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY", "NO_PROXY", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE"):
        monkeypatch.delenv(name, raising=False)
        monkeypatch.delenv(name.lower(), raising=False)
    monkeypatch.setenv("NETRC", str(tmp_path / "nonexistent-netrc"))
    import requests
    monkeypatch.setattr(requests.adapters.HTTPAdapter, "send", lambda *a, **k: pytest.fail("real provider adapter forbidden"))


@contextmanager
def opened(tmp_path):
    bundle, _ = _git_manifest(ROOT, BASE)
    profile = derive_static_runtime_transport_profile()
    config = Configuration(BASE, (Stage.OFFICIAL_RESPONSE_ACQUISITION,), tuple(NARHTTPTransportProfile(
        d.kind, d.connect_timeout_microseconds, d.read_timeout_microseconds) for d in profile.descriptors))
    session = Session(config, START, START + timedelta(hours=1))
    times = iter((START - timedelta(seconds=2), START - timedelta(seconds=1), *(START + timedelta(seconds=i) for i in range(600))))
    ticks = iter(range(0, 1_000_000_000, 100_001))
    runner = NAROperationalTimingCampaignRunner(archive_path=tmp_path / "timing.sqlite", repository_root=ROOT,
        bundle_root=tmp_path, bundle=bundle, session_identity=session.session_identity,
        utc_clock=lambda: next(times), monotonic_timer_ns=lambda: next(ticks), enable_attempt_archive=True)
    capture_conn = sqlite3.connect(tmp_path / "captures.sqlite")
    snapshot_conn = sqlite3.connect(tmp_path / "snapshots.sqlite")
    apply_capture_schema_migrations(capture_conn)
    captures = SQLiteNAROfficialResponseCaptureRepository(connection=capture_conn)
    snapshot_conn.execute("CREATE TABLE races(id INTEGER PRIMARY KEY)")
    snapshot_conn.execute("CREATE TABLE horses(id INTEGER PRIMARY KEY,race_id INTEGER NOT NULL)")
    snapshot_conn.execute("INSERT INTO races VALUES(1)")
    snapshot_conn.executemany("INSERT INTO horses VALUES(?,1)", ((101,), (102,)))
    snapshot_conn.commit()
    apply_migrations(snapshot_conn)
    snapshots = SQLiteHistoricalInputSnapshotRepository(connection=snapshot_conn)
    try:
        with runner:
            authority = runner.attempt_archive.runtime.v2
            authority.save_configuration(configuration=config)
            authority.save_session(session=session)
            issue_nar_operational_timing_session_activation_v2(session=session, archive=authority, utc_clock=lambda: START - timedelta(minutes=1))
            capability = runner.issue_current_process_execution()
            yield runner, capability, captures, snapshots
    finally:
        capture_conn.close()
        snapshot_conn.close()


def issued(runner, capability, mode=Mode.GENERATED):
    manifest, plan, historical = prepare_rehearsal_plan(runner=runner, capability=capability, history_mode=mode)
    context = issue_target_pre_c_root(runner=runner, capability=capability, manifest=manifest, plan=plan)
    return context, historical


@pytest.mark.parametrize("mode", (Mode.PRESTAGED, Mode.GENERATED))
def test_precommit_no_network_rehearsal_pass(tmp_path, mode):
    result, calls = run_phase108_no_network_rehearsal(repository_root=ROOT, bundle_root=tmp_path,
        commit_sha=BASE, temporary_root=tmp_path, history_mode=mode)
    assert result.state == State.COMPLETE.value, result
    assert result.classification == "DIAGNOSTIC_ONLY_NO_NETWORK"
    assert result.critical_path_owner == "ROOT_ONLY_NO_ADDITIVE_CHILD_TIMING"
    assert not result.errors and not result.missing_requests and not result.unexpected_attempts
    assert len(calls) == (1 if mode is Mode.PRESTAGED else 4)
    assert all(count == 1 for url, count in calls)
    if mode is Mode.PRESTAGED:
        assert all("HorseMarkInfo" not in url and "RaceMarkTable" not in url for url, count in calls)
    assert len(result.child_observations) == len(calls)
    assert all(x[1] == "QUALIFIED_OPERATIONAL_TIMING_OBSERVATION" for x in result.child_observations)


def test_domains_exact_reload_immutable_and_nonrecursive_plan(tmp_path):
    with opened(tmp_path) as (runner, cap, captures, snapshots):
        ctx, history = issued(runner, cap)
        for value in (ctx.manifest, ctx.plan, ctx.root, ctx.start):
            assert type(value).from_json(value.canonical_bytes().decode()) == value
            assert ctx.archive.load(kind=type(value), identity=value.identity) == value
            with pytest.raises(FrozenInstanceError):
                value.identity = "mutated"
            with pytest.raises(ValueError):
                type(value).from_json(value.canonical_bytes().decode() + " ")
        with pytest.raises(ValueError):
            replace(ctx.plan, max_retries=1)
        with pytest.raises(ValueError):
            replace(ctx.plan, initial_operations=ctx.plan.initial_operations[:-1])
        with pytest.raises(ValueError):
            replace(ctx.root.scope, prediction_information_cutoff=START)
        with pytest.raises(ValueError):
            replace(ctx.root, classification="OFFICIAL")


def test_explicit_schema_normal_bootstrap_strict_compatibility_append_only(tmp_path):
    from scripts.simulation.nar_operational_timing_attempt_archive_migration import require_nar_operational_timing_attempt_archive_schema
    from scripts.simulation.nar_operational_timing_runtime_execution_archive_migration import require_nar_operational_timing_runtime_execution_archive_schema
    with opened(tmp_path) as (runner, cap, captures, snapshots):
        assert not any(name.startswith("nar_pre_c_") for name in schema.base._objects(runner._connection))
        bootstrap_nar_pre_c_operational_envelope_archive(runner=runner, capability=cap)
        schema.require_nar_pre_c_operational_envelope_archive_schema(runner._connection)
        with pytest.raises(RuntimeError):
            require_nar_operational_timing_attempt_archive_schema(runner._connection)
        with pytest.raises(RuntimeError):
            require_nar_operational_timing_runtime_execution_archive_schema(runner._connection)
        assert runner.attempt_archive.runtime.v2.load_session(session_identity=cap.session_identity)
        assert runner.attempt_archive.runtime.load_claim_for_session(session_identity=cap.session_identity)
        ctx, _ = issued(runner, cap)
        for table in (schema.MANIFESTS, schema.PLANS, schema.ROOTS, schema.STARTS):
            for verb in (f"UPDATE {table} SET payload_json=payload_json", f"DELETE FROM {table}"):
                with pytest.raises(sqlite3.IntegrityError):
                    runner._connection.execute(verb)
                runner._connection.rollback()
        runner._connection.execute("CREATE TABLE unexpected(identity TEXT)")
        runner._connection.commit()
        with pytest.raises(RuntimeError, match="topology"):
            ctx.archive.load(kind=Start, identity=ctx.start.identity)


def test_controlled_issuance_duplicate_and_old_claim_rejected(tmp_path):
    with opened(tmp_path) as (runner, cap, captures, snapshots):
        ctx, _ = issued(runner, cap)
        with pytest.raises(ValueError, match="controlled"):
            ctx.archive.publish(value=ctx.start, runner=runner, capability=cap)
        with pytest.raises(ValueError, match="controlled fresh"):
            Context(runner=runner, capability=cap, archive=ctx.archive, root=ctx.root,
                manifest=ctx.manifest, plan=ctx.plan)
        with pytest.raises(ValueError, match="after root start"):
            issue_target_pre_c_root(runner=runner, capability=cap, manifest=ctx.manifest, plan=ctx.plan)
    with pytest.raises(RuntimeError):
        ctx.require_live()
    with pytest.raises(RuntimeError):
        bootstrap_nar_pre_c_operational_envelope_archive(runner=runner, capability=cap)


def test_start_publication_failure_prevents_all_causal_work(tmp_path, monkeypatch):
    original = Archive.publish
    def fail_start(self, **kwargs):
        if type(kwargs["value"]) is Start:
            raise RuntimeError("start publication unavailable")
        return original(self, **kwargs)
    monkeypatch.setattr(Archive, "publish", fail_start)
    from scripts.simulation.nar_operational_timing_diagnostic_harness import NARDiagnosticFakeHTTPAdapter
    monkeypatch.setattr(NARDiagnosticFakeHTTPAdapter, "send", lambda *a, **k: pytest.fail("causal IO before durable start"))
    with opened(tmp_path) as (runner, cap, captures, snapshots):
        manifest, plan, _ = prepare_rehearsal_plan(runner=runner, capability=cap, history_mode=Mode.GENERATED)
        with pytest.raises(RuntimeError, match="start publication"):
            issue_target_pre_c_root(runner=runner, capability=cap, manifest=manifest, plan=plan)
        assert runner._connection.execute("SELECT COUNT(*) FROM nar_operational_timing_v2_attempts").fetchone() == (0,)
        assert runner._connection.execute(f"SELECT COUNT(*) FROM {schema.STARTS}").fetchone() == (0,)


def test_derived_requests_rejected_before_closures(tmp_path):
    with opened(tmp_path) as (runner, cap, captures, snapshots):
        ctx, _ = issued(runner, cap)
        responses = rehearsal_fixture_responses(fixture=Fixture.from_json(ctx.manifest.fixture_bundle_json), repository_root=ROOT, current_url=ctx.plan.current_url)
        for url, body in responses[1:]:
            with pytest.raises(ValueError, match="closure"):
                ctx.authorize_request(url)
        assert not ctx.adapter_calls


@pytest.mark.parametrize("page", ("HorseMarkInfo", "RaceMarkTable"))
@pytest.mark.parametrize("failure", ("READ_TIMEOUT", "CONNECT_TIMEOUT", "TRANSPORT"))
def test_provider_timeout_retained_no_zero_history_and_sibling_continues(tmp_path, page, failure):
    with opened(tmp_path) as (runner, cap, captures, snapshots):
        ctx, _ = issued(runner, cap)
        responses = rehearsal_fixture_responses(fixture=Fixture.from_json(ctx.manifest.fixture_bundle_json), repository_root=ROOT, current_url=ctx.plan.current_url)
        url = next(url for url, body in responses if page in url)
        assert ctx.run_rehearsal(capture_archive=captures, snapshot_repository=snapshots, failures={url: failure}) is None
        result = reconcile_pre_c_archive(context=ctx, capture_archive=captures, snapshot_repository=snapshots)
        assert result.state == State.PROVIDER.value, result
        disposition = "FAILURE" if failure == "TRANSPORT" else "TIMEOUT"
        assert any(x[1] == "QUALIFIED_OPERATIONAL_TIMING_OBSERVATION" and x[2:] == (disposition, failure) for x in result.child_observations)
        assert any("30055402717" in url for url, count in ctx.adapter_calls)
        assert ctx.receipt is None and ctx.completion is None
        if page == "HorseMarkInfo":
            assert all(h.horse_identity != "nar:horse:30074407776" for h in ctx.histories)
        assert any(h.proven_zero_history for h in ctx.histories)  # independent genuine-zero sibling only


def test_zero_history_exact_closure_and_nonadditive_pure_reconciliation(tmp_path, monkeypatch):
    with opened(tmp_path) as (runner, cap, captures, snapshots):
        ctx, _ = issued(runner, cap)
        assert ctx.run_rehearsal(capture_archive=captures, snapshot_repository=snapshots)
        assert ctx.completion and ctx.endpoint
        assert any(h.proven_zero_history and not h.request_urls for h in ctx.histories)
        assert any(not h.proven_zero_history and h.request_urls for h in ctx.histories)
        assert ctx.completion.elapsed_microseconds == (ctx.endpoint[1] - ctx.start.monotonic_start_ns) // 1000
        before = runner._connection.total_changes
        runner.utc_clock = lambda: pytest.fail("reconciliation sampled clock")
        first = reconcile_pre_c_archive(context=ctx, capture_archive=captures, snapshot_repository=snapshots)
        second = reconcile_pre_c_archive(context=ctx, capture_archive=captures, snapshot_repository=snapshots)
        assert first == second and first.canonical_bytes() == second.canonical_bytes() and first.identity == second.identity
        assert runner._connection.total_changes == before
        assert first.elapsed_microseconds == ctx.completion.elapsed_microseconds
        assert first.state == State.COMPLETE.value, first
        assert first.current_entry_closure_identity == ctx.entries.identity
        assert first.past_race_closure_identities == tuple(sorted(h.identity for h in ctx.histories))
        assert first.snapshot_prerequisite_proof == ctx.completion.prerequisite_proof
        assert first.timing_endpoint_result == "VERIFIED_SAME_PROCESS_ENDPOINT"
        with pytest.raises(ValueError):
            replace(ctx.completion, elapsed_microseconds=True)


def test_endpoint_telemetry_failure_preserves_semantic_freeze(tmp_path, monkeypatch):
    def failed_endpoint(self, completed):
        self.endpoint_error = True
        raise RuntimeError("timing observer failed")
    monkeypatch.setattr(Context, "observe_freeze_endpoint", failed_endpoint)
    with opened(tmp_path) as (runner, cap, captures, snapshots):
        ctx, _ = issued(runner, cap)
        receipt = ctx.run_rehearsal(capture_archive=captures, snapshot_repository=snapshots)
        assert receipt and snapshots.load_snapshot_by_identity(identity=receipt.snapshot_identity)
        assert ctx.endpoint is None and ctx.completion is None
        result = reconcile_pre_c_archive(context=ctx, capture_archive=captures, snapshot_repository=snapshots)
        assert result.state == State.TELEMETRY.value and result.semantic_freeze_identity == receipt.receipt_identity


def test_completion_publication_failure_preserves_freeze_and_incomplete_timing(tmp_path, monkeypatch):
    original = Archive.publish
    def failed_completion(self, **kwargs):
        if type(kwargs["value"]) is Completion:
            raise RuntimeError("completion unavailable")
        return original(self, **kwargs)
    monkeypatch.setattr(Archive, "publish", failed_completion)
    with opened(tmp_path) as (runner, cap, captures, snapshots):
        ctx, _ = issued(runner, cap)
        receipt = ctx.run_rehearsal(capture_archive=captures, snapshot_repository=snapshots)
        assert receipt and ctx.endpoint and not ctx.completion
        result = reconcile_pre_c_archive(context=ctx, capture_archive=captures, snapshot_repository=snapshots)
        assert result.state == State.TELEMETRY.value


def test_stale_mapping_and_missing_prerequisite_rejected(tmp_path):
    with opened(tmp_path) as (runner, cap, captures, snapshots):
        manifest, plan, _ = prepare_rehearsal_plan(runner=runner, capability=cap, history_mode=Mode.GENERATED)
        stale = replace(manifest, entry_mapping=((manifest.scope.external_race_id + ":entry:99", 101),))
        with pytest.raises(ValueError, match="mapping"):
            issue_target_pre_c_root(runner=runner, capability=cap, manifest=stale, plan=replace(plan, manifest_identity=stale.identity))
        ctx, _ = issued(runner, cap)
        responses = rehearsal_fixture_responses(fixture=Fixture.from_json(ctx.manifest.fixture_bundle_json), repository_root=ROOT, current_url=ctx.plan.current_url)
        capture = ctx.capture(url=ctx.plan.current_url, bodies=dict(responses), capture_archive=captures)
        records = normalize_nar_historical_input_source_records(response=capture.to_supplied_official_response())
        with pytest.raises(ValueError, match="prerequisite"):
            prerequisite_proof(root=ctx.root, manifest=ctx.manifest,
                current_records=tuple(r for r in records if r.record_kind != "jockey"), history_records=())


def test_cross_process_clock_domain_and_resume_rejected(tmp_path, monkeypatch):
    with opened(tmp_path) as (runner, cap, captures, snapshots):
        ctx, _ = issued(runner, cap)
        original_pid = ctx._pid
        ctx._pid = original_pid + 1
        with pytest.raises(ValueError, match="process"):
            ctx.require_live()
        ctx._pid = original_pid
        runner.monotonic_timer_ns = lambda: 123
        with pytest.raises(ValueError, match="clock"):
            ctx.require_live()


def test_discovery_failure_and_corrupt_partial_closure_prevent_complete(tmp_path, monkeypatch):
    original = Context.close_history
    def corrupt(self, **kwargs):
        discovery = kwargs["discovery"]
        if not discovery.proven_zero_history:
            kwargs["discovery"] = replace(discovery, events=(), proven_zero_history=True)
        return original(self, **kwargs)
    monkeypatch.setattr(Context, "close_history", corrupt)
    with opened(tmp_path) as (runner, cap, captures, snapshots):
        ctx, _ = issued(runner, cap)
        assert ctx.run_rehearsal(capture_archive=captures, snapshot_repository=snapshots) is None
        assert not ctx.completion and not ctx.receipt
        assert not any("RaceMarkTable" in url for url, count in ctx.adapter_calls)
        assert all(h.horse_identity != "nar:horse:30074407776" for h in ctx.histories)
        result = reconcile_pre_c_archive(context=ctx, capture_archive=captures, snapshot_repository=snapshots)
        assert result.state != State.COMPLETE.value


def test_environment_rejection_blocks_adapter_and_provider_observation(tmp_path, monkeypatch):
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:1")
    with opened(tmp_path) as (runner, cap, captures, snapshots):
        ctx, _ = issued(runner, cap)
        assert ctx.run_rehearsal(capture_archive=captures, snapshot_repository=snapshots) is None
        assert all(count == 0 for url, count in ctx.adapter_calls)
        result = reconcile_pre_c_archive(context=ctx, capture_archive=captures, snapshot_repository=snapshots)
        assert result.state != State.COMPLETE.value
        assert result.child_observations[0][1] == "NONQUALIFYING_REQUEST_ENVIRONMENT"


def test_unresolved_terminal_is_not_provider_failure(tmp_path, monkeypatch):
    from scripts.simulation.sqlite_nar_operational_timing_attempt_archive import SQLiteNAROperationalTimingAttemptArchive
    monkeypatch.setattr(SQLiteNAROperationalTimingAttemptArchive, "save_terminal", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("terminal unavailable")))
    with opened(tmp_path) as (runner, cap, captures, snapshots):
        ctx, _ = issued(runner, cap)
        ctx.run_rehearsal(capture_archive=captures, snapshot_repository=snapshots)
        result = reconcile_pre_c_archive(context=ctx, capture_archive=captures, snapshot_repository=snapshots)
        assert result.state == State.INTEGRITY.value
        assert all(x[1] == "UNRESOLVED_ATTEMPT" for x in result.child_observations)


def test_elapsed_floor_integer_and_no_utc_reconstruction():
    assert elapsed_microseconds_from_ns(10, 1009) == 0
    assert elapsed_microseconds_from_ns(10, 1010) == 1
    for start, end in ((False, 10), (1.0, 10), (11, 10)):
        with pytest.raises(ValueError):
            elapsed_microseconds_from_ns(start, end)


def test_closure_publication_failure_blocks_derived_request(tmp_path, monkeypatch):
    original = Archive.publish
    def fail_history(self, **kwargs):
        if type(kwargs["value"]) is History and not kwargs["value"].proven_zero_history:
            raise RuntimeError("closure publication unavailable")
        return original(self, **kwargs)
    monkeypatch.setattr(Archive, "publish", fail_history)
    with opened(tmp_path) as (runner, cap, captures, snapshots):
        ctx, _ = issued(runner, cap)
        assert ctx.run_rehearsal(capture_archive=captures, snapshot_repository=snapshots) is None
        assert not any("RaceMarkTable" in url for url, count in ctx.adapter_calls)
        assert any("30055402717" in url for url, count in ctx.adapter_calls)
        assert not ctx.receipt
        assert reconcile_pre_c_archive(context=ctx, capture_archive=captures, snapshot_repository=snapshots).state == State.DISCOVERY.value


def test_canonical_discovery_validation_failure_never_becomes_absence(tmp_path, monkeypatch):
    import scripts.simulation.nar_pre_c_operational_envelope_harness as harness
    original = harness.discover_nar_historical_past_race_history
    def invalid_discovery(**kwargs):
        if "30074407776" in kwargs["horse_history_response"].response_url:
            raise ValueError("canonical validation failure")
        return original(**kwargs)
    monkeypatch.setattr(harness, "discover_nar_historical_past_race_history", invalid_discovery)
    with opened(tmp_path) as (runner, cap, captures, snapshots):
        ctx, _ = issued(runner, cap)
        assert ctx.run_rehearsal(capture_archive=captures, snapshot_repository=snapshots) is None
        assert not any(h.horse_identity == "nar:horse:30074407776" for h in ctx.histories)
        assert not any("RaceMarkTable" in url for url, count in ctx.adapter_calls)


def test_db_admission_rejects_wrapper_outside_closure_before_any_fake_send(tmp_path):
    from scripts.simulation.nar_operational_timing_passive_wrapper import measure_nar_operation
    from scripts.simulation.nar_operational_timing_observability import NARTimingLoadContext, NARHTTPTransportKind
    from scripts.simulation.sqlite_nar_operational_timing_observability_archive import TimingArchiveError
    with opened(tmp_path) as (runner, cap, captures, snapshots):
        ctx, _ = issued(runner, cap)
        responses = rehearsal_fixture_responses(fixture=Fixture.from_json(ctx.manifest.fixture_bundle_json), repository_root=ROOT, current_url=ctx.plan.current_url)
        with pytest.raises(TimingArchiveError):
            measure_nar_operation(runner=runner, capability=cap, stage=Stage.OFFICIAL_RESPONSE_ACQUISITION,
                correlation=ctx.correlation, load_context=NARTimingLoadContext(1,1,False), expected_url=responses[1][0],
                transport_kind=NARHTTPTransportKind.NAR_OFFICIAL_RESPONSE_HTTP, operation=lambda: pytest.fail("unauthorized child executed"))
        assert runner._connection.execute("SELECT COUNT(*) FROM nar_operational_timing_v2_attempts").fetchone() == (0,)


def test_attempt_start_overhead_failure_has_no_provider_observation(tmp_path, monkeypatch):
    from scripts.simulation.sqlite_nar_operational_timing_attempt_archive import SQLiteNAROperationalTimingAttemptArchive
    monkeypatch.setattr(SQLiteNAROperationalTimingAttemptArchive, "save_overhead", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("overhead unavailable")))
    with opened(tmp_path) as (runner, cap, captures, snapshots):
        ctx, _ = issued(runner, cap)
        assert ctx.run_rehearsal(capture_archive=captures, snapshot_repository=snapshots) is None
        assert all(count == 0 for url, count in ctx.adapter_calls)
        result = reconcile_pre_c_archive(context=ctx, capture_archive=captures, snapshot_repository=snapshots)
        assert result.state == State.INTEGRITY.value
        assert result.child_observations[0][1] == "UNRESOLVED_ATTEMPT"


def test_missing_separate_overhead_keeps_success_observation(tmp_path, monkeypatch):
    from scripts.simulation.sqlite_nar_operational_timing_attempt_archive import SQLiteNAROperationalTimingAttemptArchive
    original = SQLiteNAROperationalTimingAttemptArchive.save_overhead
    def missing_terminal_overhead(self, **kwargs):
        if kwargs["overhead"].stage is Stage.TERMINAL_PUBLICATION:
            raise RuntimeError("nonrecursive telemetry unavailable")
        return original(self, **kwargs)
    monkeypatch.setattr(SQLiteNAROperationalTimingAttemptArchive, "save_overhead", missing_terminal_overhead)
    with opened(tmp_path) as (runner, cap, captures, snapshots):
        ctx, _ = issued(runner, cap)
        assert ctx.run_rehearsal(capture_archive=captures, snapshot_repository=snapshots)
        result = reconcile_pre_c_archive(context=ctx, capture_archive=captures, snapshot_repository=snapshots)
        assert result.state == State.INTEGRITY.value and result.overhead_defects
        assert all(o[1:3] == ("QUALIFIED_OPERATIONAL_TIMING_OBSERVATION", "SUCCESS") for o in result.child_observations)


def test_snapshot_exact_reload_failure_has_no_successful_endpoint(tmp_path, monkeypatch):
    monkeypatch.setattr(SQLiteHistoricalInputSnapshotRepository, "load_snapshot_by_identity", lambda *a, **k: None)
    with opened(tmp_path) as (runner, cap, captures, snapshots):
        ctx, _ = issued(runner, cap)
        assert ctx.run_rehearsal(capture_archive=captures, snapshot_repository=snapshots) is None
        assert ctx.endpoint is None and ctx.receipt is None
        assert reconcile_pre_c_archive(context=ctx, capture_archive=captures, snapshot_repository=snapshots).state == State.FREEZE.value


def test_session_expiry_never_backdates_endpoint(tmp_path, monkeypatch):
    import scripts.simulation.nar_pre_c_operational_envelope_harness as harness
    original = harness.issue_historical_input_snapshot_freeze_receipt
    def expired_freeze(**kwargs):
        kwargs["utc_clock"] = lambda: START + timedelta(hours=1, seconds=1)
        return original(**kwargs)
    monkeypatch.setattr(harness, "issue_historical_input_snapshot_freeze_receipt", expired_freeze)
    with opened(tmp_path) as (runner, cap, captures, snapshots):
        ctx, _ = issued(runner, cap)
        receipt = ctx.run_rehearsal(capture_archive=captures, snapshot_repository=snapshots)
        assert receipt.freeze_completed_at == START + timedelta(hours=1, seconds=1)
        assert reconcile_pre_c_archive(context=ctx, capture_archive=captures, snapshot_repository=snapshots).state == State.SESSION.value


def test_reconciliation_uses_archive_evidence_not_mutable_execution_state(tmp_path):
    with opened(tmp_path) as (runner, cap, captures, snapshots):
        ctx, _ = issued(runner, cap)
        assert ctx.run_rehearsal(capture_archive=captures, snapshot_repository=snapshots)
        first = reconcile_pre_c_archive(context=ctx, capture_archive=captures, snapshot_repository=snapshots)
        ctx.children.clear()
        ctx.receipt = None
        ctx.completion = None
        ctx.endpoint = None
        second = reconcile_pre_c_archive(context=ctx, capture_archive=captures, snapshot_repository=snapshots)
        assert first == second and second.state == State.COMPLETE.value


def test_request_family_tuple_is_canonical_identity_bound_and_closed(tmp_path, monkeypatch):
    import scripts.simulation.nar_pre_c_operational_envelope as domain
    from hashlib import sha256
    from scripts.simulation.nar_operational_timing_observability import _json_bytes
    with opened(tmp_path) as (runner, cap, captures, snapshots):
        ctx, _ = issued(runner, cap)
        payload = ctx.plan.payload()
        assert payload["request_families"] == ["deba_table", "horse_mark_info", "race_mark_table"]
        assert Plan.from_json(ctx.plan.canonical_bytes().decode()) == ctx.plan
        assert ctx.archive.load(kind=Plan, identity=ctx.plan.identity) == ctx.plan
        for families in (payload["request_families"] + ["future_page"], payload["request_families"][:-1], list(reversed(payload["request_families"]))):
            changed = {**payload, "request_families": families}
            assert Plan.prefix + ":" + sha256(_json_bytes(changed)).hexdigest() != ctx.plan.identity
            with pytest.raises(ValueError, match="unreviewed"):
                Plan.from_payload(changed)
        original = domain.NAROfficialPageKind
        class FutureEnum:
            # The hypothetical extra member is never part of V1 authority.
            DEBA_TABLE = original.DEBA_TABLE
            FUTURE_PAGE = "future_page"
            def __new__(cls, value):
                return original(value)
        monkeypatch.setattr(domain, "NAROfficialPageKind", FutureEnum)
        assert tuple(x.value for x in ctx.plan.allowed_request_families) == domain.REQUEST_FAMILIES_V1
        assert FutureEnum.FUTURE_PAGE not in ctx.plan.allowed_request_families
        assert Plan.from_payload(payload).identity == ctx.plan.identity


def shared_race_fixture_responses(original, **kwargs):
    """Deterministic synthetic two-horse page from verified Git-object fixtures.

    Extend the one-row minimized result fixture in memory only. Existing source
    normalizers validate both horses against their respective history rows.
    This supplies no official evidence and changes no committed fixture/source.
    """
    from bs4 import BeautifulSoup
    from copy import deepcopy
    responses = original(**kwargs)
    history = BeautifulSoup(responses[1][1].decode(), "html.parser")
    cells = history.select_one("table.HorseMarkInfo_table tbody tr").find_all("td", recursive=False)
    cells[10].string = "4"  # past-race frame/horse numbers, never internal entry IDs
    cells[11].string = "4"
    cells[12].string = "7"
    cells[13].string = "8"
    cells[14].string = "1:32.0"
    cells[17].string = "494"
    page = BeautifulSoup(responses[3][1].decode(), "html.parser")
    row = page.select_one("tr.tBorder")
    second = deepcopy(row)
    second.select_one("td.horseName a")["href"] = "/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=30055402717"
    second.select_one("td.a").string = "8"
    second.select_one("td.c").string = "4"
    second.select_one("td.o").string = "7"
    second.select_one("td.k").string = "1:32.0"
    second.select_one("td.horseWeight").string = "494(1)"
    row.insert_after(second)
    return (responses[0], responses[1], (responses[2][0], str(history).encode()), (responses[3][0], str(page).encode()))


@pytest.mark.parametrize("failure", (None, "READ_TIMEOUT", "TRANSPORT"))
def test_shared_request_one_provider_observation_multiple_closed_dependencies(tmp_path, monkeypatch, failure):
    import scripts.simulation.nar_pre_c_operational_envelope_harness as harness
    original = harness.rehearsal_fixture_responses
    monkeypatch.setattr(harness, "rehearsal_fixture_responses", lambda **kwargs: shared_race_fixture_responses(original, **kwargs))
    with opened(tmp_path) as (runner, cap, captures, snapshots):
        ctx, _ = issued(runner, cap)
        responses = harness.rehearsal_fixture_responses(fixture=Fixture.from_json(ctx.manifest.fixture_bundle_json), repository_root=ROOT, current_url=ctx.plan.current_url)
        url = responses[3][0]
        reuse_checks = []
        original_consume = ctx.capture_history_request
        def consume(**kwargs):
            closure = kwargs["closure"]
            # The later closure and its exact edge must reload before consumption.
            assert ctx.archive.load(kind=History, identity=closure.identity) == closure
            nodes, edges = ctx.archive.request_graph(start_identity=ctx.start.identity)
            from hashlib import sha256
            assert (closure.identity, ctx.start.identity, sha256(url.encode()).hexdigest()) in edges
            reused = url in ctx._requested_urls
            value = original_consume(**kwargs)
            with pytest.raises(ValueError, match="no retry"):
                ctx.authorize_request(url)  # duplicate IO remains forbidden while live
            reuse_checks.append((closure.identity, reused, value.capture_id))
            return value
        monkeypatch.setattr(ctx, "capture_history_request", consume)
        receipt = ctx.run_rehearsal(capture_archive=captures, snapshot_repository=snapshots, failures={url: failure} if failure else {})
        result = reconcile_pre_c_archive(context=ctx, capture_archive=captures, snapshot_repository=snapshots)
        assert len(ctx.histories) == 2 and all(h.request_urls == (url,) for h in ctx.histories)
        assert len(result.provider_request_nodes) == 4  # DebaTable, 2 HorseMarkInfo, 1 shared RaceMarkTable
        assert len(result.closure_request_dependencies) == 2
        assert len(result.child_observations) == 4
        assert [(u, count) for u, count in ctx.adapter_calls if u == url] == [(url, 1)]
        assert all(ctx.archive.load(kind=History, identity=h.identity) == h for h in ctx.histories)
        for table in (schema.REQUESTS, schema.DEPENDENCIES):
            with pytest.raises(sqlite3.IntegrityError, match="immutable"):
                runner._connection.execute(f"DELETE FROM {table}")
            runner._connection.rollback()
        if failure is None:
            assert receipt and ctx.completion and result.state == State.COMPLETE.value, result
            assert not result.unsatisfied_closure_dependencies
            assert [x[1] for x in reuse_checks] == [False, True]
            assert reuse_checks[0][2] == reuse_checks[1][2]
            # Reconciliation calls the unchanged entry-specific normalizer twice
            # on the same persisted capture and proves both snapshot prerequisites.
            assert len(ctx.completion.children) == 4
            assert len([p for p in result.snapshot_prerequisite_proof if "past_race" in p[0]]) == 2
            # Pure reconciliation must independently reject a missing dependency
            # even when the snapshot and provider captures are all valid.
            nodes, edges = ctx.archive.request_graph(start_identity=ctx.start.identity)
            monkeypatch.setattr(ctx.archive, "request_graph", lambda **kwargs: (nodes, edges[:-1]))
            broken = reconcile_pre_c_archive(context=ctx, capture_archive=captures, snapshot_repository=snapshots)
            assert broken.state == State.INTEGRITY.value and "CHILD_REQUEST_GRAPH_INVALID" in broken.errors
        else:
            assert receipt is None and result.state == State.PROVIDER.value, result
            assert len(result.unsatisfied_closure_dependencies) == 2
            assert sum(o[2] == ("TIMEOUT" if failure == "READ_TIMEOUT" else "FAILURE") for o in result.child_observations) == 1
            assert not ctx.completion


def test_shared_capture_requires_later_closure_and_exact_dependency_reload(tmp_path, monkeypatch):
    import scripts.simulation.nar_pre_c_operational_envelope_harness as harness
    original = harness.rehearsal_fixture_responses
    monkeypatch.setattr(harness, "rehearsal_fixture_responses", lambda **kwargs: shared_race_fixture_responses(original, **kwargs))
    with opened(tmp_path) as (runner, cap, captures, snapshots):
        ctx, _ = issued(runner, cap)
        responses = harness.rehearsal_fixture_responses(fixture=Fixture.from_json(ctx.manifest.fixture_bundle_json), repository_root=ROOT, current_url=ctx.plan.current_url)
        bodies = dict(responses)
        current = ctx.capture(url=ctx.plan.current_url, bodies=bodies, capture_archive=captures)
        records = normalize_nar_historical_input_source_records(response=current.to_supplied_official_response())
        entries = ctx.close_entries(capture=current, records=records, attempt=ctx._attempt(ctx.start.first_attempt_sequence))
        track = next(r for r in records if r.record_kind == "track")
        closures = []
        prior = None
        for entry_id, _, _, horse_url in entries.entries:
            entry = next(r for r in records if r.record_kind == "entry" and r.external_entry_id == entry_id)
            sequence = runner._next_attempt_sequence
            horse = ctx.capture(url=horse_url, bodies=bodies, capture_archive=captures)
            discovery = harness.discover_nar_historical_past_race_history(target_track_record=track, target_entry_record=entry, horse_history_response=horse.to_supplied_official_response())
            if prior is not None:
                # Prior successful capture cannot stand in for this unsaved closure.
                pending = History(entries.identity, horse.capture_id, ctx._attempt(sequence).attempt_identity, entry_id,
                    discovery.target_external_horse_id, harness.history_events(discovery), False,
                    runner._next_attempt_sequence, runner.utc_clock())
                with pytest.raises(ValueError, match="reloaded history closure"):
                    ctx.capture_history_request(closure=pending, url=responses[3][0], bodies=bodies, capture_archive=captures)
            h = ctx.close_history(capture=horse, track=track, entry=entry, discovery=discovery, attempt=ctx._attempt(sequence))
            closures.append(h)
            actual = ctx.capture_history_request(closure=h, url=responses[3][0], bodies=bodies, capture_archive=captures)
            if prior is not None:
                assert actual == prior and actual.capture_id == prior.capture_id
            prior = actual
        # Foreign-key and closure URL gates reject orphans/unrelated dependencies.
        from hashlib import sha256
        with pytest.raises(sqlite3.IntegrityError):
            runner._connection.execute(f"INSERT INTO {schema.DEPENDENCIES} VALUES(?,?,?)", (closures[1].identity, ctx.start.identity, sha256(ctx.plan.current_url.encode()).hexdigest()))
        runner._connection.rollback()
        with pytest.raises(sqlite3.IntegrityError):
            runner._connection.execute(f"INSERT INTO {schema.DEPENDENCIES} VALUES(?,?,?)", ("orphan", ctx.start.identity, sha256(responses[3][0].encode()).hexdigest()))
        runner._connection.rollback()
        node = next(n for n in ctx.archive.request_graph(start_identity=ctx.start.identity)[0] if n[2] == responses[3][0])
        with pytest.raises(sqlite3.IntegrityError):
            runner._connection.execute(f"INSERT INTO {schema.REQUESTS} VALUES(?,?,?,?)", node)
        runner._connection.rollback()
        assert sum(count for url, count in ctx.adapter_calls if url == responses[3][0]) == 1
