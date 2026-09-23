"""Exact append-only publication of configuration, attempts, and freeze receipts."""

from dataclasses import replace
from datetime import timedelta
import sqlite3

import pytest

from scripts.simulation.historical_input_snapshot_freeze_receipt import (
    HistoricalInputSnapshotFreezeReceipt, issue_historical_input_snapshot_freeze_receipt,
)
from scripts.simulation.nar_operational_timing_observability import (
    NAROperationalTimingAttempt, NAROperationalTimingTerminalObservation,
    NARTimingFailureClassification, NARTimingStage, NARTimingTerminalDisposition,
)
from scripts.simulation.nar_operational_timing_observability_archive_migration import (
    ATTEMPTS, CONFIGS, RECEIPTS, TERMINALS,
    apply_nar_operational_timing_observability_archive_migrations as migrate,
)
from scripts.simulation.sqlite_nar_operational_timing_observability_archive import (
    SQLiteNAROperationalTimingObservabilityArchive as Archive, TimingArchiveConflict,
    TimingArchiveError,
)
from tests.test_nar_operational_timing_observability import START, CORRELATION, config, session
from tests.test_historical_input_snapshots import _snapshot


def _archive():
    connection = sqlite3.connect(":memory:")
    migrate(connection)
    return connection, Archive(connection=connection)


def test_constructor_does_not_migrate_and_exact_roundtrip():
    connection = sqlite3.connect(":memory:")
    with pytest.raises(RuntimeError):
        Archive(connection=connection)
    assert not connection.execute("SELECT name FROM sqlite_master WHERE name LIKE 'nar_operational_%'").fetchall()
    migrate(connection)
    archive = Archive(connection=connection)
    configuration = config()
    campaign = session(configuration=configuration)
    attempt = NAROperationalTimingAttempt(campaign, NARTimingStage.RACE_LIST_ACQUISITION,
                                          CORRELATION, 0, START)
    archive.save_configuration(configuration=configuration)
    archive.save_session(session=campaign)
    archive.save_attempt(attempt=attempt)
    assert archive.load_configuration(configuration_identity=configuration.configuration_identity) == configuration
    assert archive.load_session(session_identity=campaign.session_identity) == campaign
    assert archive.load_attempt(attempt_identity=attempt.attempt_identity) == attempt
    assert archive.list_unresolved_attempts(session_identity=campaign.session_identity) == (attempt,)
    timeout = NAROperationalTimingTerminalObservation(
        attempt, campaign.measurement_end_at + timedelta(seconds=1), 2_000_000,
        NARTimingTerminalDisposition.TIMEOUT, NARTimingFailureClassification.TIMEOUT)
    archive.save_terminal(observation=timeout)
    assert archive.load_terminal(observation_identity=timeout.observation_identity) == timeout
    assert archive.list_unresolved_attempts(session_identity=campaign.session_identity) == ()
    for action, value in ((archive.save_configuration, configuration),
                          (archive.save_session, campaign), (archive.save_attempt, attempt),
                          (archive.save_terminal, timeout)):
        name = next(iter(action.__annotations__), None)
        action(**{name: value})
    conflict = replace(timeout, elapsed_microseconds=2_000_001)
    with pytest.raises(TimingArchiveConflict):
        archive.save_terminal(observation=conflict)
    assert connection.execute(f"SELECT count(*) FROM {TERMINALS}").fetchone() == (1,)


def test_unknown_parent_and_corruption_fail_closed():
    connection, archive = _archive()
    campaign = session()
    with pytest.raises(TimingArchiveError):
        archive.save_session(session=campaign)
    attempt = NAROperationalTimingAttempt(campaign, NARTimingStage.RACE_LIST_ACQUISITION, CORRELATION, 0, START)
    with pytest.raises(TimingArchiveError):
        archive.save_attempt(attempt=attempt)
    assert not connection.in_transaction
    archive.save_configuration(configuration=campaign.configuration)
    forged = replace(campaign.configuration, software_commit_sha="b" * 40)
    object.__setattr__(forged, "configuration_sha256", campaign.configuration.configuration_sha256)
    with pytest.raises(TimingArchiveError, match="contradictory"):
        archive.save_configuration(configuration=forged)
    connection.execute(f"INSERT INTO {CONFIGS}(identity,payload_json) VALUES(?,?)",
                       ("nar-operational-timing-config-v1:" + "f" * 64, "{}"))
    connection.commit()
    with pytest.raises(TimingArchiveError):
        archive.load_configuration(configuration_identity="nar-operational-timing-config-v1:" + "f" * 64)
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(f"UPDATE {CONFIGS} SET payload_json='x'")
    connection.rollback()


def test_freeze_receipt_roundtrip_duplicate_and_corruption():
    connection, archive = _archive()
    snapshot = _snapshot()
    receipt = HistoricalInputSnapshotFreezeReceipt(
        snapshot.identity, snapshot.internal_race_id, snapshot.content_sha256,
        snapshot.information_cutoff, snapshot.identity.captured_at + timedelta(minutes=1))
    with pytest.raises(TimingArchiveError, match="controlled"):
        archive.save_freeze_receipt(receipt=receipt)
    class Repo:
        def save_snapshot(self, *, snapshot):
            pass
        def load_snapshot_by_identity(self, *, identity):
            return snapshot
    issued = issue_historical_input_snapshot_freeze_receipt(
        snapshot=snapshot, snapshot_repository=Repo(), archive=archive,
        utc_clock=lambda: receipt.freeze_completed_at)
    assert issued == receipt
    issue_historical_input_snapshot_freeze_receipt(
        snapshot=snapshot, snapshot_repository=Repo(), archive=archive,
        utc_clock=lambda: receipt.freeze_completed_at)
    assert archive.load_freeze_receipt(receipt_identity=receipt.receipt_identity) == receipt
    assert connection.execute(f"SELECT count(*) FROM {RECEIPTS}").fetchone() == (1,)
    connection.execute(f"INSERT INTO {RECEIPTS}(identity,payload_json) VALUES(?,?)",
                       ("historical-input-snapshot-freeze-v1:" + "f" * 64, receipt.canonical_bytes().decode()))
    connection.commit()
    with pytest.raises(TimingArchiveError):
        archive.load_freeze_receipt(receipt_identity="historical-input-snapshot-freeze-v1:" + "f" * 64)


def test_attempt_write_rollback_on_trigger_failure():
    connection, archive = _archive()
    campaign = session()
    archive.save_configuration(configuration=campaign.configuration)
    archive.save_session(session=campaign)
    connection.execute(f"CREATE TRIGGER test_fail_attempt BEFORE INSERT ON {ATTEMPTS} BEGIN SELECT RAISE(ABORT,'fail'); END")
    connection.commit()
    attempt = NAROperationalTimingAttempt(campaign, NARTimingStage.RACE_LIST_ACQUISITION, CORRELATION, 0, START)
    with pytest.raises(RuntimeError):  # exact schema gate detects unregistered trigger
        archive.save_attempt(attempt=attempt)
    assert connection.execute(f"SELECT count(*) FROM {ATTEMPTS}").fetchone() == (0,)
