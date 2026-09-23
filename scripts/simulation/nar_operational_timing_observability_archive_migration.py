"""Explicit isolated v1 migration for immutable NAR timing observability."""

from __future__ import annotations

import sqlite3


VERSION = 1
NAME = "v001_nar_operational_timing_observability_archive"
REGISTRY = "nar_operational_timing_schema_migrations"
CONFIGS = "nar_operational_timing_configurations"
SESSIONS = "nar_operational_timing_sessions"
ATTEMPTS = "nar_operational_timing_attempts"
TERMINALS = "nar_operational_timing_terminals"
RECEIPTS = "nar_snapshot_freeze_receipts"

_DDL = {
    REGISTRY: f"CREATE TABLE {REGISTRY} (version INTEGER PRIMARY KEY CHECK(version=1), name TEXT NOT NULL CHECK(name='{NAME}')) WITHOUT ROWID",
    CONFIGS: f"CREATE TABLE {CONFIGS} (identity TEXT PRIMARY KEY, payload_json TEXT NOT NULL) WITHOUT ROWID",
    SESSIONS: f"CREATE TABLE {SESSIONS} (identity TEXT PRIMARY KEY, configuration_identity TEXT NOT NULL REFERENCES {CONFIGS}(identity) ON UPDATE RESTRICT ON DELETE RESTRICT, payload_json TEXT NOT NULL) WITHOUT ROWID",
    ATTEMPTS: f"CREATE TABLE {ATTEMPTS} (identity TEXT PRIMARY KEY, session_identity TEXT NOT NULL REFERENCES {SESSIONS}(identity) ON UPDATE RESTRICT ON DELETE RESTRICT, payload_json TEXT NOT NULL) WITHOUT ROWID",
    TERMINALS: f"CREATE TABLE {TERMINALS} (identity TEXT PRIMARY KEY, attempt_identity TEXT NOT NULL UNIQUE REFERENCES {ATTEMPTS}(identity) ON UPDATE RESTRICT ON DELETE RESTRICT, payload_json TEXT NOT NULL) WITHOUT ROWID",
    RECEIPTS: f"CREATE TABLE {RECEIPTS} (identity TEXT PRIMARY KEY, payload_json TEXT NOT NULL) WITHOUT ROWID",
}
for _table in (CONFIGS, SESSIONS, ATTEMPTS, TERMINALS, RECEIPTS):
    _DDL[f"trg_{_table}_no_update"] = f"CREATE TRIGGER trg_{_table}_no_update BEFORE UPDATE ON {_table} BEGIN SELECT RAISE(ABORT, 'immutable timing archive'); END"
    _DDL[f"trg_{_table}_no_delete"] = f"CREATE TRIGGER trg_{_table}_no_delete BEFORE DELETE ON {_table} BEGIN SELECT RAISE(ABORT, 'immutable timing archive'); END"


def _connection(connection: sqlite3.Connection) -> sqlite3.Connection:
    if type(connection) is not sqlite3.Connection:
        raise ValueError("connection must be exact sqlite3.Connection")
    connection.execute("PRAGMA foreign_keys=ON")
    if connection.execute("PRAGMA foreign_keys").fetchone() != (1,):
        raise RuntimeError("foreign keys could not be enabled")
    return connection


def _objects(connection: sqlite3.Connection) -> dict[str, str]:
    return {row[0]: row[1] for row in connection.execute(
        "SELECT name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' AND type IN ('table','index','trigger','view')"
    ).fetchall()}


def require_nar_operational_timing_observability_archive_schema(connection: sqlite3.Connection) -> None:
    """Reject partial, modified, unregistered, or unknown archive objects."""
    connection = _connection(connection)
    if _objects(connection) != _DDL:
        raise RuntimeError("timing observability archive schema is not exact v1")
    if connection.execute(f"SELECT version,name FROM {REGISTRY}").fetchall() != [(VERSION, NAME)]:
        raise RuntimeError("timing observability migration registry is not exact v1")
    if connection.execute("PRAGMA foreign_key_check").fetchall():
        raise RuntimeError("timing observability foreign-key integrity failed")


def apply_nar_operational_timing_observability_archive_migrations(connection: sqlite3.Connection) -> None:
    """Create the archive explicitly and atomically; never repair partial schema."""
    connection = _connection(connection)
    if connection.in_transaction:
        raise RuntimeError("migration requires no caller transaction")
    connection.execute("BEGIN IMMEDIATE")
    try:
        existing = _objects(connection)
        if existing:
            require_nar_operational_timing_observability_archive_schema(connection)
        else:
            for sql in _DDL.values():
                connection.execute(sql)
            connection.execute(f"INSERT INTO {REGISTRY}(version,name) VALUES(?,?)", (VERSION, NAME))
            require_nar_operational_timing_observability_archive_schema(connection)
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
