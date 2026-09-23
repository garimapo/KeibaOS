"""Activation ancestry, immutable rows, and Phase99 coexistence."""

import sqlite3

import pytest

from scripts.simulation import nar_operational_timing_activation_archive_migration as schema
from scripts.simulation.nar_operational_timing_observability_archive_migration import (
    apply_nar_operational_timing_observability_archive_migrations as base_migrate,
)
from scripts.simulation.nar_operational_timing_session_activation import (
    NAROperationalTimingMeasurementSessionActivationDeclaration as Declaration,
    NAROperationalTimingMeasurementSessionActivationVerificationReceipt as Verification,
    _ISSUANCE_MARKER, issue_nar_operational_timing_session_activation as issue,
)
from scripts.simulation.sqlite_nar_operational_timing_observability_archive import (
    SQLiteNAROperationalTimingObservabilityArchive as BaseArchive,
    TimingArchiveConflict, TimingArchiveError,
)
from scripts.simulation.sqlite_nar_operational_timing_activation_archive import (
    SQLiteNAROperationalTimingActivationArchive as ActivationArchive,
)
from scripts.simulation.nar_operational_timing_observability import (
    NAROperationalTimingAttempt, NAROperationalTimingTerminalObservation,
    NARTimingStage, NARTimingTerminalDisposition,
)
from scripts.simulation.historical_input_snapshot_freeze_receipt import (
    issue_historical_input_snapshot_freeze_receipt,
)
from tests.test_historical_input_snapshots import _snapshot
from tests.test_nar_operational_timing_observability import START, CORRELATION, session


def _ready():
    connection = sqlite3.connect(":memory:")
    base_migrate(connection)
    schema.apply_nar_operational_timing_activation_archive_migrations(connection)
    base = BaseArchive(connection=connection)
    activation = ActivationArchive(connection=connection)
    campaign = session()
    base.save_configuration(configuration=campaign.configuration)
    base.save_session(session=campaign)
    return connection, base, activation, campaign


def test_no_constructor_migration_and_base_archive_still_works():
    connection = sqlite3.connect(":memory:")
    with pytest.raises(RuntimeError):
        ActivationArchive(connection=connection)
    assert not connection.execute("SELECT name FROM sqlite_master WHERE name LIKE 'nar_operational_%'").fetchall()
    connection, base, _, campaign = _ready()
    attempt = NAROperationalTimingAttempt(campaign, NARTimingStage.RACE_LIST_ACQUISITION,
                                          CORRELATION, 0, START)
    base.save_attempt(attempt=attempt)
    assert base.list_unresolved_attempts(session_identity=campaign.session_identity) == (attempt,)
    terminal = NAROperationalTimingTerminalObservation(
        attempt, START, 0, NARTimingTerminalDisposition.SUCCESS)
    base.save_terminal(observation=terminal)
    assert base.load_terminal(observation_identity=terminal.observation_identity) == terminal
    assert base.list_unresolved_attempts(session_identity=campaign.session_identity) == ()
    snapshot = _snapshot()
    class SnapshotRepo:
        def save_snapshot(self, *, snapshot):
            return None
        def load_snapshot_by_identity(self, *, identity):
            return snapshot
    receipt = issue_historical_input_snapshot_freeze_receipt(
        snapshot=snapshot, snapshot_repository=SnapshotRepo(), archive=base,
        utc_clock=lambda: snapshot.identity.captured_at)
    assert base.load_freeze_receipt(receipt_identity=receipt.receipt_identity) == receipt


def test_controlled_issuance_duplicate_and_immutable_triggers():
    connection, _, archive, campaign = _ready()
    declaration = Declaration(campaign.session_identity, campaign.configuration.configuration_identity)
    with pytest.raises(TimingArchiveError, match="controlled"):
        archive.save_declaration(declaration=declaration)
    first = issue(session=campaign, archive=archive, utc_clock=lambda: START)
    assert archive.load_declaration_for_session(session_identity=campaign.session_identity) == first.declaration
    assert archive.load_verification_for_declaration(
        declaration_identity=first.declaration.declaration_identity) == first.verification_receipt
    issue(session=campaign, archive=archive,
          utc_clock=lambda: (_ for _ in ()).throw(AssertionError("unexpected sample")))
    assert connection.execute(f"SELECT count(*) FROM {schema.DECLARATIONS}").fetchone() == (1,)
    assert connection.execute(f"SELECT count(*) FROM {schema.VERIFICATIONS}").fetchone() == (1,)
    for table in (schema.DECLARATIONS, schema.VERIFICATIONS):
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(f"UPDATE {table} SET payload_json='x'")
        connection.rollback()
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(f"DELETE FROM {table}")
        connection.rollback()


def test_foreign_parent_and_corrupt_content_fail_closed():
    connection, _, archive, campaign = _ready()
    declaration = Declaration(campaign.session_identity, campaign.configuration.configuration_identity)
    receipt = Verification(declaration.declaration_identity, campaign.session_identity,
                           campaign.configuration.configuration_identity, START)
    with pytest.raises(TimingArchiveError):
        archive.save_verification_receipt(receipt=receipt, _issuance_marker=_ISSUANCE_MARKER)
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            f"INSERT INTO {schema.DECLARATIONS}(identity,session_identity,configuration_identity,payload_json) "
            "VALUES('bad','missing',?,'{}')", (campaign.configuration.configuration_identity,))
    connection.rollback()
    issue(session=campaign, archive=archive, utc_clock=lambda: START)
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            f"INSERT INTO {schema.VERIFICATIONS}(identity,declaration_identity,session_identity,configuration_identity,payload_json) "
            "VALUES('bad','missing',?,?, '{}')",
            (campaign.session_identity, campaign.configuration.configuration_identity))
    connection.rollback()
    # Altered payload cannot pass exact reload even if SQL immutability was bypassed.
    connection.execute(f"DROP TRIGGER trg_{schema.VERIFICATIONS}_no_update")
    connection.execute(f"UPDATE {schema.VERIFICATIONS} SET payload_json='{{}}'")
    connection.commit()
    with pytest.raises(RuntimeError):
        archive.load_verification_for_declaration(declaration_identity=declaration.declaration_identity)


def test_one_declaration_and_verification_per_parent():
    connection, _, archive, campaign = _ready()
    first = issue(session=campaign, archive=archive, utc_clock=lambda: START)
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            f"INSERT INTO {schema.DECLARATIONS}(identity,session_identity,configuration_identity,payload_json) "
            "VALUES('other',?,?, '{}')",
            (campaign.session_identity, campaign.configuration.configuration_identity))
    connection.rollback()
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            f"INSERT INTO {schema.VERIFICATIONS}(identity,declaration_identity,session_identity,configuration_identity,payload_json) "
            "VALUES('other',?,?,?, '{}')",
            (first.declaration.declaration_identity, campaign.session_identity,
             campaign.configuration.configuration_identity))
    connection.rollback()
    assert connection.execute(f"SELECT count(*) FROM {schema.DECLARATIONS}").fetchone() == (1,)
    assert connection.execute(f"SELECT count(*) FROM {schema.VERIFICATIONS}").fetchone() == (1,)
