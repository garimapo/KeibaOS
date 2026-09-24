"""Phase103 companion is exact and leaves Phase99/100 records untouched."""

import sqlite3

import pytest

from scripts.simulation import nar_operational_timing_observability_archive_migration as base
from scripts.simulation import nar_operational_timing_activation_archive_migration as activation
from scripts.simulation import nar_operational_timing_v2_authority_archive_migration as v2
from scripts.simulation.sqlite_nar_operational_timing_observability_archive import SQLiteNAROperationalTimingObservabilityArchive
from scripts.simulation.sqlite_nar_operational_timing_activation_archive import SQLiteNAROperationalTimingActivationArchive
from scripts.simulation.sqlite_nar_operational_timing_v2_authority_archive import SQLiteNAROperationalTimingV2AuthorityArchive
from scripts.simulation.nar_operational_timing_observability import (
    NAROperationalTimingAttempt, NAROperationalTimingTerminalObservation,
    NARTimingStage, NARTimingTerminalDisposition,
)
from scripts.simulation.nar_operational_timing_session_activation import issue_nar_operational_timing_session_activation
from tests.test_nar_operational_timing_observability import START, CORRELATION, config as config_v1, session as session_v1


def migrated():
    connection = sqlite3.connect(":memory:")
    base.apply_nar_operational_timing_observability_archive_migrations(connection)
    activation.apply_nar_operational_timing_activation_archive_migrations(connection)
    return connection


def test_exact_upgrade_idempotency_and_v1_compatibility():
    connection = migrated()
    old = SQLiteNAROperationalTimingObservabilityArchive(connection=connection)
    configuration = config_v1()
    old.save_configuration(configuration=configuration)
    before = connection.execute(f"SELECT * FROM {base.CONFIGS}").fetchall()
    v2.apply_nar_operational_timing_v2_authority_archive_migrations(connection)
    v2.apply_nar_operational_timing_v2_authority_archive_migrations(connection)
    v2.require_nar_operational_timing_v2_authority_archive_schema(connection)
    assert base._objects(connection) == base._DDL | activation._DDL | v2._DDL
    assert connection.execute(f"SELECT * FROM {base.CONFIGS}").fetchall() == before
    assert connection.execute(f"SELECT * FROM {base.REGISTRY}").fetchall() == [(1, base.NAME)]
    assert connection.execute(f"SELECT * FROM {activation.REGISTRY}").fetchall() == [(1, activation.NAME)]
    assert connection.execute(f"SELECT * FROM {v2.REGISTRY}").fetchall() == [(1, v2.NAME)]
    for table in (v2.CONFIGS, v2.SESSIONS, v2.DECLARATIONS, v2.VERIFICATIONS):
        assert connection.execute(f"SELECT count(*) FROM {table}").fetchone() == (0,)
    assert SQLiteNAROperationalTimingObservabilityArchive(connection=connection).load_configuration(
        configuration_identity=configuration.configuration_identity) == configuration
    legacy_activation = SQLiteNAROperationalTimingActivationArchive(connection=connection)
    assert SQLiteNAROperationalTimingV2AuthorityArchive(connection=connection)
    campaign = session_v1(configuration=configuration)
    old.save_session(session=campaign)
    attempt = NAROperationalTimingAttempt(campaign, NARTimingStage.RACE_LIST_ACQUISITION,
                                          CORRELATION, 0, START)
    old.save_attempt(attempt=attempt)
    terminal = NAROperationalTimingTerminalObservation(
        attempt, START, 0, NARTimingTerminalDisposition.SUCCESS)
    old.save_terminal(observation=terminal)
    assert old.load_terminal(observation_identity=terminal.observation_identity) == terminal
    assert old.list_unresolved_attempts(session_identity=campaign.session_identity) == ()
    activated = issue_nar_operational_timing_session_activation(
        session=campaign, archive=legacy_activation, utc_clock=lambda: START)
    assert activated.verification_receipt is not None
    with pytest.raises(RuntimeError):
        base.require_nar_operational_timing_observability_archive_schema(connection)
    with pytest.raises(RuntimeError):
        activation.require_nar_operational_timing_activation_archive_schema(connection)


def test_partial_unknown_and_malformed_state_fail_closed():
    connection = migrated()
    connection.execute("CREATE TABLE nar_operational_timing_v2_configurations (identity TEXT PRIMARY KEY)")
    connection.commit()
    with pytest.raises(RuntimeError):
        v2.apply_nar_operational_timing_v2_authority_archive_migrations(connection)
    assert connection.execute(f"SELECT count(*) FROM {v2.CONFIGS}").fetchone() == (0,)
    connection = migrated()
    connection.execute(f"DROP TRIGGER trg_{base.CONFIGS}_no_update")
    connection.commit()
    with pytest.raises(RuntimeError):
        v2.apply_nar_operational_timing_v2_authority_archive_migrations(connection)
    connection = migrated()
    v2.apply_nar_operational_timing_v2_authority_archive_migrations(connection)
    connection.execute("CREATE TABLE unexpected_extra (id INTEGER)")
    with pytest.raises(RuntimeError):
        v2.require_nar_operational_timing_v2_authority_archive_schema(connection)


def test_immutable_tables_and_restrictive_foreign_keys():
    connection = migrated()
    v2.apply_nar_operational_timing_v2_authority_archive_migrations(connection)
    connection.execute(f"INSERT INTO {v2.CONFIGS}(identity,payload_json) VALUES('x','x')")
    connection.commit()
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(f"UPDATE {v2.CONFIGS} SET payload_json='y' WHERE identity='x'")
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(f"DELETE FROM {v2.CONFIGS} WHERE identity='x'")
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(f"INSERT INTO {v2.SESSIONS}(identity,configuration_identity,payload_json) VALUES('s','missing','s')")
    assert "ON UPDATE RESTRICT ON DELETE RESTRICT" in v2._DDL[v2.SESSIONS]
    assert "ON UPDATE RESTRICT ON DELETE RESTRICT" in v2._DDL[v2.DECLARATIONS]
    assert "ON UPDATE RESTRICT ON DELETE RESTRICT" in v2._DDL[v2.VERIFICATIONS]
