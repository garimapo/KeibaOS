"""Controlled snapshot save, exact reload, clock sampling, and cutoff qualification."""

from dataclasses import replace
from datetime import date, timedelta
import sqlite3

import pytest

from scripts.simulation.historical_input_snapshot_freeze_receipt import (
    HistoricalInputSnapshotFreezeReceipt, NARSnapshotFreezeQualificationState,
    SnapshotFreezeError, issue_historical_input_snapshot_freeze_receipt,
    qualify_nar_snapshot_freeze,
)
from scripts.simulation.nar_historical_replay_prediction_cutoff import (
    NARHistoricalReplayPredictionCutoffDecision as Decision,
    NARHistoricalReplayPredictionCutoffPlan as Plan,
)
from scripts.simulation.nar_operational_timing_observability_archive_migration import (
    apply_nar_operational_timing_observability_archive_migrations as migrate,
)
from scripts.simulation.sqlite_nar_operational_timing_observability_archive import (
    SQLiteNAROperationalTimingObservabilityArchive as Archive,
)
from tests.test_historical_input_snapshots import _snapshot
from tests.test_historical_daily_replay_manifest_projection import _target, _target_set


class SnapshotRepoSpy:
    def __init__(self, snapshot):
        self.snapshot = snapshot
        self.events = []
        self.loaded = snapshot

    def save_snapshot(self, *, snapshot):
        self.events.append("commit-return")
        assert snapshot == self.snapshot

    def load_snapshot_by_identity(self, *, identity):
        self.events.append("exact-reload")
        assert identity == self.snapshot.identity
        return self.loaded


def _archive():
    connection = sqlite3.connect(":memory:")
    migrate(connection)
    return connection, Archive(connection=connection)


def test_clock_only_after_commit_and_exact_reload_then_archive():
    snapshot = _snapshot()
    repo = SnapshotRepoSpy(snapshot)
    connection, archive = _archive()
    observed = snapshot.identity.captured_at + timedelta(minutes=2)
    def clock():
        repo.events.append("clock")
        return observed
    receipt = issue_historical_input_snapshot_freeze_receipt(
        snapshot=snapshot, snapshot_repository=repo, archive=archive, utc_clock=clock)
    assert repo.events == ["commit-return", "exact-reload", "clock"]
    assert receipt.freeze_completed_at == observed
    assert archive.load_freeze_receipt(receipt_identity=receipt.receipt_identity) == receipt
    assert "freeze_completed_at" not in issue_historical_input_snapshot_freeze_receipt.__code__.co_varnames[:4]
    assert receipt.freeze_semantic.value == "COMMITTED_AND_EXACT_RELOAD_VERIFIED"
    assert connection.execute("SELECT count(*) FROM nar_snapshot_freeze_receipts").fetchone() == (1,)


def test_missing_mismatched_reload_blocks_clock_and_receipt():
    snapshot = _snapshot()
    for loaded in (None, _snapshot(passing_order="2-2-2-2"), _snapshot(source_url="https://example.test/other")):
        repo = SnapshotRepoSpy(snapshot)
        repo.loaded = loaded
        _, archive = _archive()
        with pytest.raises(SnapshotFreezeError):
            issue_historical_input_snapshot_freeze_receipt(
                snapshot=snapshot, snapshot_repository=repo, archive=archive,
                utc_clock=lambda: (_ for _ in ()).throw(AssertionError("clock sampled early")))
        assert repo.events == ["commit-return", "exact-reload"]


def test_archive_failure_leaves_snapshot_but_no_qualification():
    snapshot = _snapshot()
    repo = SnapshotRepoSpy(snapshot)
    class FailingArchive:
        def save_freeze_receipt(self, *, receipt, _issuance_marker):
            raise RuntimeError("archive unavailable")
    with pytest.raises(RuntimeError, match="archive unavailable"):
        issue_historical_input_snapshot_freeze_receipt(
            snapshot=snapshot, snapshot_repository=repo, archive=FailingArchive(),
            utc_clock=lambda: snapshot.identity.captured_at + timedelta(minutes=1))
    assert repo.events == ["commit-return", "exact-reload"]


def test_controlled_service_uses_existing_sqlite_snapshot_commit_and_reload():
    from tests.test_sqlite_historical_input_snapshot_repository import (
        SQLiteHistoricalInputSnapshotRepositoryTests,
    )
    helper = SQLiteHistoricalInputSnapshotRepositoryTests()
    snapshot_connection, repository = helper.repository()
    snapshot = helper.snapshot()
    _, archive = _archive()
    completed = snapshot.identity.captured_at + timedelta(minutes=1)
    receipt = issue_historical_input_snapshot_freeze_receipt(
        snapshot=snapshot, snapshot_repository=repository, archive=archive,
        utc_clock=lambda: completed)
    assert snapshot_connection.in_transaction is False
    assert repository.load_snapshot_by_identity(identity=snapshot.identity).content_sha256 == snapshot.content_sha256
    assert receipt.freeze_completed_at == completed
    assert archive.load_freeze_receipt(receipt_identity=receipt.receipt_identity) == receipt


def test_receipt_new_verification_time_not_snapshot_capture_time():
    snapshot = _snapshot()
    repo = SnapshotRepoSpy(snapshot)
    _, archive = _archive()
    first = issue_historical_input_snapshot_freeze_receipt(
        snapshot=snapshot, snapshot_repository=repo, archive=archive,
        utc_clock=lambda: snapshot.identity.captured_at + timedelta(minutes=1))
    second = issue_historical_input_snapshot_freeze_receipt(
        snapshot=snapshot, snapshot_repository=repo, archive=archive,
        utc_clock=lambda: snapshot.identity.captured_at + timedelta(minutes=2))
    assert first != second
    assert second.freeze_completed_at > first.freeze_completed_at > snapshot.identity.captured_at


def test_qualification_before_equal_after_cutoff_and_archived_authority():
    snapshot = _snapshot()
    target = replace(_target("01"),
                     external_race_id=snapshot.identity.source_identity.external_race_id,
                     scheduled_start_at=snapshot.race.scheduled_start_at)
    targets = replace(_target_set(_target("01")),
                      target_date=date(2026, 8, 5), target_races=(target,))
    cutoff = snapshot.information_cutoff + timedelta(minutes=10)
    plan = Plan(targets, "nar-prediction-cutoff-policy-v1:" + "a" * 64,
                (Decision(target, cutoff),))
    _, archive = _archive()
    for offset, expected in ((-1, NARSnapshotFreezeQualificationState.SNAPSHOT_FROZEN_BY_PREDICTION_CUTOFF),
                             (0, NARSnapshotFreezeQualificationState.SNAPSHOT_FROZEN_BY_PREDICTION_CUTOFF),
                             (1, NARSnapshotFreezeQualificationState.SNAPSHOT_FREEZE_COMPLETED_AFTER_PREDICTION_CUTOFF)):
        receipt = issue_historical_input_snapshot_freeze_receipt(
            snapshot=snapshot, snapshot_repository=SnapshotRepoSpy(snapshot),
            archive=archive, utc_clock=lambda: cutoff + timedelta(seconds=offset))
        assert qualify_nar_snapshot_freeze(receipt=receipt, archive=archive,
                                           target=target, cutoff_plan=plan).state is expected
    with pytest.raises(SnapshotFreezeError):
        qualify_nar_snapshot_freeze(receipt=receipt, archive=archive,
                                    target=_target("01"), cutoff_plan=plan)
