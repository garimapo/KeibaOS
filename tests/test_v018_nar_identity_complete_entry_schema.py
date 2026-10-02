"""V018 exact topology, duplicate preflight, and rollback; SQLite memory only."""

import sqlite3

import pytest

from scripts.migrations.runner import MIGRATIONS, apply_migrations, get_applied_versions
from scripts.migrations.versions.v018_nar_identity_complete_entry_schema import (
    NAME, PHASE110_SCHEMA_ACTIVE, PHASE110_SCHEMA_INTEGRITY_FAILURE,
    PHASE110_SCHEMA_NOT_INSTALLED, phase110_schema_state,
)


def legacy_db():
    connection = sqlite3.connect(":memory:")
    connection.execute("""CREATE TABLE races(id INTEGER PRIMARY KEY,race_date TEXT,
                         organization TEXT,place TEXT,race_no INTEGER,deba_table_url TEXT)""")
    connection.execute("CREATE TABLE horses(id INTEGER PRIMARY KEY,race_id INTEGER,horse_no INTEGER,horse_detail_url TEXT)")
    connection.execute("INSERT INTO races VALUES(1,'2025-01-01','NAR','A',1,'url')")
    connection.execute("INSERT INTO horses(id,race_id,horse_no) VALUES(1,1,1)")
    connection.commit()
    return connection


def through_v017(connection):
    apply_migrations(connection, tuple(migration for migration in MIGRATIONS if migration.VERSION <= 17))
    return connection


def test_v018_installs_exact_registered_topology_and_rerun_is_noop():
    connection = through_v017(legacy_db())
    assert phase110_schema_state(connection) == PHASE110_SCHEMA_NOT_INSTALLED
    apply_migrations(connection)
    assert get_applied_versions(connection)[18] == NAME
    assert phase110_schema_state(connection) == PHASE110_SCHEMA_ACTIVE
    apply_migrations(connection)
    assert phase110_schema_state(connection) == PHASE110_SCHEMA_ACTIVE
    assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    indexes = {row[0] for row in connection.execute("SELECT name FROM sqlite_schema WHERE type='index'")}
    assert {"nar_identity_complete_unique_race_key", "nar_identity_complete_unique_horse_key"} <= indexes
    connection.close()


@pytest.mark.parametrize("table,insert", [
    ("races", "INSERT INTO races(id,race_date,organization,place,race_no) VALUES(2,'2025-01-01','NAR','A',1)"),
    ("horses", "INSERT INTO horses(id,race_id,horse_no) VALUES(2,1,1)"),
])
def test_duplicate_preflight_rolls_back_without_repair(table, insert):
    connection = through_v017(legacy_db())
    connection.execute(insert)
    connection.commit()
    with pytest.raises(RuntimeError, match="duplicate natural key"):
        apply_migrations(connection)
    assert 18 not in get_applied_versions(connection)
    assert phase110_schema_state(connection) == PHASE110_SCHEMA_NOT_INSTALLED
    assert connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == 2
    assert not connection.in_transaction
    connection.close()


def test_schema_absent_active_and_partial_fail_closed():
    connection = through_v017(legacy_db())
    assert phase110_schema_state(connection) == PHASE110_SCHEMA_NOT_INSTALLED
    connection.execute("CREATE TABLE nar_identity_complete_receipts(x INTEGER)")
    connection.commit()
    assert phase110_schema_state(connection) == PHASE110_SCHEMA_INTEGRITY_FAILURE
    connection.close()
    active = through_v017(legacy_db())
    apply_migrations(active)
    assert phase110_schema_state(active) == PHASE110_SCHEMA_ACTIVE
    active.execute("DROP TRIGGER nar_identity_complete_entries_issue_denial")
    active.commit()
    assert phase110_schema_state(active) == PHASE110_SCHEMA_INTEGRITY_FAILURE
    active.close()


def test_registered_without_objects_and_extra_topology_fail_closed():
    connection = through_v017(legacy_db())
    connection.execute("INSERT INTO schema_migrations VALUES(18,?, '2025-01-01')", (NAME,))
    connection.commit()
    assert phase110_schema_state(connection) == PHASE110_SCHEMA_INTEGRITY_FAILURE
    connection.close()
    connection = through_v017(legacy_db())
    apply_migrations(connection)
    connection.execute("CREATE INDEX extra_idx ON nar_identity_complete_entries(horse_no)")
    connection.commit()
    assert phase110_schema_state(connection) == PHASE110_SCHEMA_INTEGRITY_FAILURE
    connection.close()
