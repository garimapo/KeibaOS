from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from scripts.simulation.nar_operational_timing_campaign_runner import (
    NARCurrentProcessExecutionCapability, NAROperationalTimingCampaignRunner,
)
from scripts.simulation.nar_operational_timing_runtime_source_provenance import _git_manifest
from scripts.simulation.nar_operational_timing_runtime_execution import (
    NAROperationalTimingCampaignReadinessVerificationReceipt,
)
from scripts.simulation.nar_operational_timing_observability import NARHTTPTransportProfile
from scripts.simulation.nar_operational_timing_observability_v2 import (
    NAROperationalTimingMeasurementConfigurationV2 as Configuration,
    NAROperationalTimingMeasurementSessionV2 as Session,
    NAROperationalTimingStageV2 as Stage,
)
from scripts.simulation.nar_operational_timing_runtime_profile import derive_static_runtime_transport_profile
from scripts.simulation.nar_operational_timing_session_activation_v2 import issue_nar_operational_timing_session_activation_v2
from scripts.simulation.sqlite_nar_operational_timing_runtime_execution_archive import (
    SQLiteNAROperationalTimingRuntimeExecutionArchive as Archive,
)


ROOT = Path(__file__).resolve().parents[1]
COMMIT = "1236f1e0db84ce6025d07c052abbb3c7348aab3e"
START = datetime(2030, 1, 1, tzinfo=timezone.utc)


def _prepare(tmp_path, monkeypatch, times, start=START):
    bundle, _ = _git_manifest(ROOT, COMMIT)
    profile = derive_static_runtime_transport_profile()
    config = Configuration(COMMIT, (Stage.SNAPSHOT_CONSTRUCTION,),
                           tuple(NARHTTPTransportProfile(x.kind, x.connect_timeout_microseconds,
                                                         x.read_timeout_microseconds)
                                 for x in profile.descriptors))
    monkeypatch.setattr(NAROperationalTimingCampaignRunner, "_require_isolated_source", lambda self: None)
    intended = Session(config, start, start + timedelta(hours=1))
    runner = NAROperationalTimingCampaignRunner(
        archive_path=tmp_path / "timing.sqlite", repository_root=ROOT,
        bundle_root=tmp_path, bundle=bundle, session_identity=intended.session_identity,
        utc_clock=lambda: next(times))
    return runner, config


def _archive_session(runner, config, start=START):
    archive = Archive(connection=runner._connection)
    session = Session(config, start, start + timedelta(hours=1))
    archive.v2.save_configuration(configuration=config)
    archive.v2.save_session(session=session)
    issue_nar_operational_timing_session_activation_v2(
        session=session, archive=archive.v2, utc_clock=lambda: start - timedelta(minutes=1))
    return archive, session


def test_claim_and_readiness_precede_process_capability_and_old_claim_cannot_resume(tmp_path, monkeypatch):
    times = iter((START - timedelta(seconds=2), START - timedelta(seconds=1)))
    runner, config = _prepare(tmp_path, monkeypatch, times)
    with runner:
        archive, session = _archive_session(runner, config)
        capability = runner.issue_current_process_execution()
        capability.require_current_owner(runner)
        claim = archive.load_claim_for_session(session_identity=session.session_identity)
        assert claim.claim_identity == capability.claim_identity
        receipt = archive.load_readiness_for_claim(claim_identity=claim.claim_identity)
        assert receipt.readiness_verified_at < START
        assert receipt.binding_identity == capability.binding_identity
        with pytest.raises(RuntimeError):
            runner.issue_current_process_execution()
    with pytest.raises(RuntimeError):
        capability.require_current_owner(runner)
    later, _ = _prepare(tmp_path, monkeypatch, iter(()))
    with later:
        with pytest.raises(RuntimeError, match="permanently consumed"):
            later.issue_current_process_execution()
        new_session = Session(config, START + timedelta(days=1), START + timedelta(days=1, hours=1))
        second_archive = Archive(connection=later._connection)
        second_archive.v2.save_session(session=new_session)
        issue_nar_operational_timing_session_activation_v2(
            session=new_session, archive=second_archive.v2, utc_clock=lambda: START)
    next_runner, _ = _prepare(tmp_path, monkeypatch,
                              iter((START + timedelta(hours=23), START + timedelta(hours=23, seconds=1))),
                              start=START + timedelta(days=1))
    with next_runner:
        new_capability = next_runner.issue_current_process_execution()
        assert new_capability.session_identity == new_session.session_identity
        forged = NARCurrentProcessExecutionCapability(
            claim_identity=capability.claim_identity, binding_identity=capability.binding_identity,
            session_identity=capability.session_identity, _owner=next_runner)
        with pytest.raises(RuntimeError):
            forged.require_current_owner(next_runner)


@pytest.mark.parametrize("verified_at", [START, START + timedelta(microseconds=1)])
def test_equality_qualifies_and_late_readiness_consumes_session(tmp_path, monkeypatch, verified_at):
    times = iter((verified_at, verified_at))
    runner, config = _prepare(tmp_path, monkeypatch, times)
    with runner:
        archive, session = _archive_session(runner, config)
        if verified_at == START:
            assert runner.issue_current_process_execution().session_identity == session.session_identity
        else:
            with pytest.raises(RuntimeError, match="after fixed session start"):
                runner.issue_current_process_execution()
        claim = archive.load_claim_for_session(session_identity=session.session_identity)
        assert claim is not None
        receipt = archive.load_readiness_for_claim(claim_identity=claim.claim_identity)
        assert type(receipt) is NAROperationalTimingCampaignReadinessVerificationReceipt
        assert receipt.readiness_verified_at == verified_at


def test_isolation_guard_fails_closed_in_normal_pytest_process(tmp_path):
    bundle, _ = _git_manifest(ROOT, COMMIT)
    runner = NAROperationalTimingCampaignRunner(
        archive_path=tmp_path / "timing.sqlite", repository_root=ROOT,
        bundle_root=tmp_path, bundle=bundle,
        session_identity="nar-operational-timing-session-v2:" + "a" * 64)
    with runner:
        with pytest.raises(RuntimeError, match="isolated"):
            runner.issue_current_process_execution()


def test_clock_is_sampled_only_after_binding_and_claim_exact_reload(tmp_path, monkeypatch):
    observed = []
    runner, config = _prepare(tmp_path, monkeypatch, iter(()))

    def clock():
        binding_rows = runner._connection.execute(
            "SELECT COUNT(*) FROM nar_operational_timing_runtime_bindings").fetchone()[0]
        claim_rows = runner._connection.execute(
            "SELECT COUNT(*) FROM nar_operational_timing_campaign_execution_claims").fetchone()[0]
        observed.append((binding_rows, claim_rows))
        return START - timedelta(seconds=1)

    runner.utc_clock = clock
    with runner:
        _, session = _archive_session(runner, config)
        runner.issue_current_process_execution()
    assert observed == [(1, 1), (1, 1)]
