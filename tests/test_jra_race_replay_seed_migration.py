from __future__ import annotations

import sqlite3

from scripts.migrations.runner import apply_migrations, get_applied_versions


def _connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE races(id INTEGER PRIMARY KEY)")
    connection.execute("CREATE TABLE horses(id INTEGER PRIMARY KEY, race_id INTEGER)")
    return connection


def test_v015_registers_two_seed_tables_and_one_entry_mapping_index() -> None:
    connection = _connection()
    apply_migrations(connection)
    assert get_applied_versions(connection)[15] == "v015_jra_race_replay_seed_schema"
    names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master")}
    assert {"jra_race_replay_seeds", "jra_race_replay_seed_entries", "ux_historical_input_external_entries_exact_mapping"} <= names
    assert connection.execute("SELECT 1 FROM sqlite_master WHERE name='jra_race_replay_seeds'").fetchone()


def test_v015_runner_is_idempotent() -> None:
    connection = _connection()
    apply_migrations(connection)
    apply_migrations(connection)
    assert get_applied_versions(connection)[15] == "v015_jra_race_replay_seed_schema"
