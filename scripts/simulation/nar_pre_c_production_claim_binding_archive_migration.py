"""Standalone exact Phase113 companion; never a main simulation migration."""

from __future__ import annotations

import sqlite3

from scripts.simulation.nar_pre_c_production_claim_binding import (
    NARPreCProductionClaimBindingError, binding_row, parse_binding,
)

VERSION = 1
NAME = "v001_nar_pre_c_production_claim_binding_companion"
NOT_INSTALLED = "PHASE113_SCHEMA_NOT_INSTALLED"
ACTIVE = "PHASE113_SCHEMA_ACTIVE"
INTEGRITY_FAILURE = "PHASE113_SCHEMA_INTEGRITY_FAILURE"
REGISTRY = "nar_pre_c_production_claim_binding_schema_migrations"
BINDINGS = "nar_pre_c_production_claim_bindings"

_DDL = {
    REGISTRY: (
        f"CREATE TABLE {REGISTRY} (version INTEGER PRIMARY KEY CHECK(version=1), "
        f"name TEXT NOT NULL CHECK(name='{NAME}')) WITHOUT ROWID"
    ),
    BINDINGS: (
        f"CREATE TABLE {BINDINGS} (identity TEXT PRIMARY KEY, "
        "claim_identity TEXT NOT NULL, runtime_binding_identity TEXT NOT NULL, "
        "session_identity TEXT NOT NULL, campaign_readiness_receipt_identity TEXT NOT NULL, "
        "phase112_manifest_identity TEXT NOT NULL UNIQUE, "
        "phase112_availability_receipt_identity TEXT NOT NULL UNIQUE, "
        "phase109_receipt_id TEXT NOT NULL, "
        "organization TEXT NOT NULL CHECK(organization='NAR'), "
        "source_system TEXT NOT NULL CHECK(source_system='nar_official'), "
        "external_race_id TEXT NOT NULL, "
        "internal_race_id INTEGER NOT NULL CHECK(internal_race_id>0), "
        "prediction_cutoff TEXT NOT NULL, schema_version INTEGER NOT NULL CHECK(schema_version=1), "
        "payload_json TEXT NOT NULL, "
        "UNIQUE(organization,source_system,external_race_id,prediction_cutoff), "
        "UNIQUE(organization,source_system,internal_race_id,prediction_cutoff)) WITHOUT ROWID"
    ),
}
for _table in (REGISTRY, BINDINGS):
    for _verb in ("UPDATE", "DELETE"):
        _name = f"{_table}_no_{_verb.lower()}"
        _DDL[_name] = (f"CREATE TRIGGER {_name} BEFORE {_verb} ON {_table} "
                       "BEGIN SELECT RAISE(ABORT, 'immutable Phase113 binding evidence'); END")


def _objects(connection: sqlite3.Connection) -> dict[str, tuple[str, str, str]]:
    return {name: (kind, table, sql) for kind, name, table, sql in connection.execute(
        "SELECT type,name,tbl_name,sql FROM sqlite_schema WHERE name NOT GLOB 'sqlite_*'")}


def _expected() -> dict[str, tuple[str, str, str]]:
    return {name: ("table" if name in (REGISTRY, BINDINGS) else "trigger",
                   name if name in (REGISTRY, BINDINGS) else name.rsplit("_no_", 1)[0], ddl)
            for name, ddl in _DDL.items()}


def phase113_schema_state(connection: sqlite3.Connection) -> str:
    if not isinstance(connection, sqlite3.Connection):
        return INTEGRITY_FAILURE
    try:
        objects = _objects(connection)
        if not objects:
            return NOT_INSTALLED
        if objects != _expected():
            return INTEGRITY_FAILURE
        if connection.execute(f"SELECT version,name FROM {REGISTRY}").fetchall() != [(VERSION, NAME)]:
            return INTEGRITY_FAILURE
        if connection.execute(f"PRAGMA foreign_key_list({BINDINGS})").fetchall():
            return INTEGRITY_FAILURE  # No cross-store FK can replace exact upstream load.
        for row in connection.execute(f"SELECT * FROM {BINDINGS}"):
            if tuple(row) != binding_row(parse_binding(row[-1], row[0])):
                return INTEGRITY_FAILURE
        return ACTIVE
    except NARPreCProductionClaimBindingError:
        return INTEGRITY_FAILURE
    except sqlite3.OperationalError as exc:
        if str(exc).lower().startswith(("no such table:", "no such column:", "malformed database schema")):
            return INTEGRITY_FAILURE
        raise


def require_phase113_schema(connection: sqlite3.Connection) -> None:
    state = phase113_schema_state(connection)
    if state != ACTIVE:
        raise RuntimeError(f"exact active Phase113 companion required: {state}")


def apply(connection: sqlite3.Connection) -> None:
    if not isinstance(connection, sqlite3.Connection) or connection.in_transaction:
        raise RuntimeError("Phase113 installation requires idle injected SQLite connection")
    connection.execute("PRAGMA foreign_keys=ON")
    if connection.execute("PRAGMA foreign_keys").fetchone() != (1,):
        raise RuntimeError("Phase113 installation requires foreign keys")
    state = phase113_schema_state(connection)
    if state == ACTIVE:
        return
    if state != NOT_INSTALLED:
        raise RuntimeError("contradictory Phase113 companion schema")
    connection.execute("BEGIN IMMEDIATE")
    try:
        # Recheck under the write lock: another installer may have committed.
        state = phase113_schema_state(connection)
        if state == NOT_INSTALLED:
            for statement in _DDL.values():
                connection.execute(statement)
            connection.execute(f"INSERT INTO {REGISTRY} VALUES(?,?)", (VERSION, NAME))
        require_phase113_schema(connection)
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
