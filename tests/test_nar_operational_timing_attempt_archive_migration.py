import sqlite3

import pytest

from scripts.simulation import nar_operational_timing_attempt_archive_migration as attempt
from scripts.simulation import nar_operational_timing_runtime_execution_archive_migration as runtime
from scripts.simulation import nar_operational_timing_observability_archive_migration as base
from scripts.simulation.nar_operational_timing_archive_bootstrap import bootstrap_nar_operational_timing_runtime_archive
from scripts.simulation.nar_operational_timing_attempt_archive_bootstrap import bootstrap_nar_operational_timing_attempt_archive
from scripts.simulation.nar_operational_timing_campaign_lock import NAROperationalTimingCampaignLock
from scripts.simulation.sqlite_nar_operational_timing_attempt_archive import SQLiteNAROperationalTimingAttemptArchive
from scripts.simulation.sqlite_nar_operational_timing_runtime_execution_archive import SQLiteNAROperationalTimingRuntimeExecutionArchive


def test_exact_bootstrap_and_historical_compatibility(tmp_path):
    path = tmp_path / "archive.sqlite"
    with NAROperationalTimingCampaignLock(archive_path=path) as lock, sqlite3.connect(path) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        bootstrap_nar_operational_timing_attempt_archive(connection=connection, campaign_lock=lock)
        before = {table: connection.execute(f"SELECT * FROM {table}").fetchall()
                  for table in (base.REGISTRY, runtime.REGISTRY)}
        bootstrap_nar_operational_timing_attempt_archive(connection=connection, campaign_lock=lock)
        bootstrap_nar_operational_timing_runtime_archive(connection=connection, campaign_lock=lock)
        assert before == {table: connection.execute(f"SELECT * FROM {table}").fetchall() for table in before}
        assert connection.execute(f"SELECT * FROM {attempt.REGISTRY}").fetchall() == [(1, attempt.NAME)]
        assert all(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0 for table in
                   (attempt.ATTEMPTS, attempt.ENVIRONMENTS, attempt.TERMINALS, attempt.OVERHEAD))
        assert SQLiteNAROperationalTimingAttemptArchive(connection=connection)
        assert SQLiteNAROperationalTimingRuntimeExecutionArchive(connection=connection)
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                f"INSERT INTO {attempt.ATTEMPTS}(identity,claim_identity,session_identity,configuration_identity,attempt_sequence,stage,http_policy,payload_json) "
                "VALUES(?,?,?,?,?,?,?,?)",
                ("fake", "missing-claim", "missing-session", "missing-config", 0, "SNAPSHOT_CONSTRUCTION", None, "{}"),
            )
        connection.rollback()
        with pytest.raises(RuntimeError):
            runtime.require_nar_operational_timing_runtime_execution_archive_schema(connection)
        with pytest.raises(sqlite3.DatabaseError):
            connection.execute(f"DELETE FROM {attempt.REGISTRY}")
        with pytest.raises(sqlite3.DatabaseError):
            connection.execute(f"UPDATE {attempt.REGISTRY} SET name='other'")


def test_partial_or_unknown_schema_fails_without_repair(tmp_path):
    path = tmp_path / "archive.sqlite"
    with NAROperationalTimingCampaignLock(archive_path=path) as lock, sqlite3.connect(path) as connection:
        bootstrap_nar_operational_timing_runtime_archive(connection=connection, campaign_lock=lock)
        connection.execute("CREATE TABLE unexpected(x TEXT)")
        with pytest.raises(RuntimeError):
            bootstrap_nar_operational_timing_attempt_archive(connection=connection, campaign_lock=lock)
        assert attempt.REGISTRY not in base._objects(connection)
        connection.execute("DROP TABLE unexpected")
        connection.execute(attempt._DDL[attempt.REGISTRY])
        with pytest.raises(RuntimeError):
            bootstrap_nar_operational_timing_attempt_archive(connection=connection, campaign_lock=lock)
