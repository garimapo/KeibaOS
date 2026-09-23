"""Exact Phase100 companion migration with an unchanged Phase99 base."""

import sqlite3

import pytest

from scripts.simulation import nar_operational_timing_observability_archive_migration as base
from scripts.simulation import nar_operational_timing_activation_archive_migration as companion


def _connection():
    connection = sqlite3.connect(":memory:")
    base.apply_nar_operational_timing_observability_archive_migrations(connection)
    return connection


def test_exact_upgrade_idempotency_base_identity_and_no_backfill():
    connection = _connection()
    before = base._objects(connection)
    connection.execute(f"INSERT INTO {base.CONFIGS}(identity,payload_json) VALUES('legacy','{{}}')")
    connection.commit()
    companion.apply_nar_operational_timing_activation_archive_migrations(connection)
    companion.require_nar_operational_timing_activation_archive_schema(connection)
    assert connection.execute(f"SELECT version,name FROM {base.REGISTRY}").fetchall() == [(1, base.NAME)]
    assert connection.execute(f"SELECT version,name FROM {companion.REGISTRY}").fetchall() == [(1, companion.NAME)]
    assert {k: base._objects(connection)[k] for k in before} == before
    assert connection.execute(f"SELECT identity,payload_json FROM {base.CONFIGS}").fetchall() == [("legacy", "{}")]
    assert connection.execute(f"SELECT count(*) FROM {companion.DECLARATIONS}").fetchone() == (0,)
    assert connection.execute(f"SELECT count(*) FROM {companion.VERIFICATIONS}").fetchone() == (0,)
    objects = base._objects(connection)
    companion.apply_nar_operational_timing_activation_archive_migrations(connection)
    assert base._objects(connection) == objects
    companion.require_nar_operational_timing_archive_compatible_schema(connection)
    with pytest.raises(RuntimeError, match="exact v1"):
        base.require_nar_operational_timing_observability_archive_schema(connection)


def test_partial_unknown_and_malformed_base_rejected_without_repair():
    connection = _connection()
    connection.execute("CREATE TABLE nar_operational_timing_activation_declarations(x INTEGER)")
    connection.commit()
    with pytest.raises(RuntimeError):
        companion.apply_nar_operational_timing_activation_archive_migrations(connection)
    assert not connection.in_transaction
    assert connection.execute(f"SELECT name FROM sqlite_master WHERE name='{companion.REGISTRY}'").fetchone() is None

    connection = _connection()
    connection.execute(f"DROP TRIGGER trg_{base.SESSIONS}_no_update")
    connection.commit()
    with pytest.raises(RuntimeError):
        companion.apply_nar_operational_timing_activation_archive_migrations(connection)
    assert connection.execute(f"SELECT count(*) FROM {base.REGISTRY}").fetchone() == (1,)

    connection = _connection()
    companion.apply_nar_operational_timing_activation_archive_migrations(connection)
    connection.execute("CREATE TABLE unknown_companion_object(x INTEGER)")
    connection.commit()
    with pytest.raises(RuntimeError):
        companion.require_nar_operational_timing_activation_archive_schema(connection)
    with pytest.raises(RuntimeError):
        companion.require_nar_operational_timing_archive_compatible_schema(connection)


def test_migration_respects_caller_transaction_and_restrictive_foreign_keys():
    connection = _connection()
    connection.execute("BEGIN")
    with pytest.raises(RuntimeError, match="transaction"):
        companion.apply_nar_operational_timing_activation_archive_migrations(connection)
    assert connection.in_transaction
    connection.rollback()
    companion.apply_nar_operational_timing_activation_archive_migrations(connection)
    for table, parent in ((companion.DECLARATIONS, base.SESSIONS),
                          (companion.VERIFICATIONS, companion.DECLARATIONS)):
        keys = connection.execute(f"PRAGMA foreign_key_list({table})").fetchall()
        assert any(row[2] == parent and row[5:7] == ("RESTRICT", "RESTRICT") for row in keys)
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(f"UPDATE {companion.REGISTRY} SET name='x'")
    connection.rollback()
