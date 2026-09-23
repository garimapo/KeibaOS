"""The observability schema is isolated, exact, and explicitly applied."""

import sqlite3

import pytest

from scripts.simulation.nar_operational_timing_observability_archive_migration import (
    ATTEMPTS, CONFIGS, NAME, RECEIPTS, TERMINALS, VERSION,
    apply_nar_operational_timing_observability_archive_migrations as apply,
    require_nar_operational_timing_observability_archive_schema as require,
)


def test_exact_migration_and_idempotency():
    connection = sqlite3.connect(":memory:")
    with pytest.raises(RuntimeError):
        require(connection)
    apply(connection)
    require(connection)
    first = connection.execute("SELECT name,sql FROM sqlite_master ORDER BY name").fetchall()
    apply(connection)
    assert connection.execute("SELECT name,sql FROM sqlite_master ORDER BY name").fetchall() == first
    assert VERSION == 1 and NAME == "v001_nar_operational_timing_observability_archive"
    foreign_keys = connection.execute(f"PRAGMA foreign_key_list({TERMINALS})").fetchall()
    assert any(row[2] == ATTEMPTS and row[5:7] == ("RESTRICT", "RESTRICT") for row in foreign_keys)


def test_partial_schema_rejected_and_caller_transaction_preserved():
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE unexpected(x INTEGER)")
    connection.commit()
    with pytest.raises(RuntimeError):
        apply(connection)
    assert connection.execute("SELECT name FROM sqlite_master WHERE name='unexpected'").fetchone()
    connection.execute("BEGIN")
    with pytest.raises(RuntimeError):
        apply(connection)
    assert connection.in_transaction
    connection.rollback()


def test_immutable_triggers_and_exact_schema_gate():
    connection = sqlite3.connect(":memory:")
    apply(connection)
    connection.execute(f"INSERT INTO {CONFIGS}(identity,payload_json) VALUES('x','{{}}')")
    connection.commit()
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(f"UPDATE {CONFIGS} SET payload_json='different' WHERE identity='x'")
    connection.rollback()
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(f"DELETE FROM {CONFIGS} WHERE identity='x'")
    connection.rollback()
    connection.execute(f"DROP TRIGGER trg_{RECEIPTS}_no_update")
    with pytest.raises(RuntimeError):
        require(connection)
