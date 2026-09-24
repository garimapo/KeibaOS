"""Exact same-database V2 config/session/activation companion; no observation rows."""

from __future__ import annotations

import sqlite3

from scripts.simulation import nar_operational_timing_observability_archive_migration as base
from scripts.simulation import nar_operational_timing_activation_archive_migration as activation


VERSION = 1
NAME = "v001_nar_operational_timing_v2_authority_companion"
REGISTRY = "nar_operational_timing_v2_authority_schema_migrations"
CONFIGS = "nar_operational_timing_v2_configurations"
SESSIONS = "nar_operational_timing_v2_sessions"
DECLARATIONS = "nar_operational_timing_v2_activation_declarations"
VERIFICATIONS = "nar_operational_timing_v2_activation_verifications"

_DDL = {
    REGISTRY: f"CREATE TABLE {REGISTRY} (version INTEGER PRIMARY KEY CHECK(version=1), name TEXT NOT NULL CHECK(name='{NAME}')) WITHOUT ROWID",
    CONFIGS: f"CREATE TABLE {CONFIGS} (identity TEXT PRIMARY KEY, payload_json TEXT NOT NULL) WITHOUT ROWID",
    SESSIONS: (
        f"CREATE TABLE {SESSIONS} (identity TEXT PRIMARY KEY, "
        f"configuration_identity TEXT NOT NULL REFERENCES {CONFIGS}(identity) ON UPDATE RESTRICT ON DELETE RESTRICT, "
        "payload_json TEXT NOT NULL) WITHOUT ROWID"
    ),
    DECLARATIONS: (
        f"CREATE TABLE {DECLARATIONS} (identity TEXT PRIMARY KEY, "
        f"session_identity TEXT NOT NULL UNIQUE REFERENCES {SESSIONS}(identity) ON UPDATE RESTRICT ON DELETE RESTRICT, "
        f"configuration_identity TEXT NOT NULL REFERENCES {CONFIGS}(identity) ON UPDATE RESTRICT ON DELETE RESTRICT, "
        "payload_json TEXT NOT NULL) WITHOUT ROWID"
    ),
    VERIFICATIONS: (
        f"CREATE TABLE {VERIFICATIONS} (identity TEXT PRIMARY KEY, "
        f"declaration_identity TEXT NOT NULL UNIQUE REFERENCES {DECLARATIONS}(identity) ON UPDATE RESTRICT ON DELETE RESTRICT, "
        "session_identity TEXT NOT NULL, configuration_identity TEXT NOT NULL, "
        "payload_json TEXT NOT NULL) WITHOUT ROWID"
    ),
}
for _table in (CONFIGS, SESSIONS, DECLARATIONS, VERIFICATIONS, REGISTRY):
    _DDL[f"trg_{_table}_no_update"] = (
        f"CREATE TRIGGER trg_{_table}_no_update BEFORE UPDATE ON {_table} "
        "BEGIN SELECT RAISE(ABORT, 'immutable timing V2 authority'); END"
    )
    _DDL[f"trg_{_table}_no_delete"] = (
        f"CREATE TRIGGER trg_{_table}_no_delete BEFORE DELETE ON {_table} "
        "BEGIN SELECT RAISE(ABORT, 'immutable timing V2 authority'); END"
    )
_DDL[f"trg_{DECLARATIONS}_parent_match"] = (
    f"CREATE TRIGGER trg_{DECLARATIONS}_parent_match BEFORE INSERT ON {DECLARATIONS} "
    f"WHEN (SELECT configuration_identity FROM {SESSIONS} WHERE identity=NEW.session_identity) "
    "IS NOT NEW.configuration_identity "
    "BEGIN SELECT RAISE(ABORT, 'V2 session configuration mismatch'); END"
)
_DDL[f"trg_{VERIFICATIONS}_parent_match"] = (
    f"CREATE TRIGGER trg_{VERIFICATIONS}_parent_match BEFORE INSERT ON {VERIFICATIONS} "
    f"WHEN (SELECT session_identity FROM {DECLARATIONS} WHERE identity=NEW.declaration_identity) "
    "IS NOT NEW.session_identity OR "
    f"(SELECT configuration_identity FROM {DECLARATIONS} WHERE identity=NEW.declaration_identity) "
    "IS NOT NEW.configuration_identity "
    "BEGIN SELECT RAISE(ABORT, 'V2 declaration mismatch'); END"
)


def require_nar_operational_timing_v2_authority_archive_schema(connection: sqlite3.Connection) -> None:
    """Require exact base + activation + V2 authority union and registered rows."""
    connection = base._connection(connection)
    if base._objects(connection) != base._DDL | activation._DDL | _DDL:
        raise RuntimeError("timing V2 authority companion schema is not exact")
    if connection.execute(f"SELECT version,name FROM {base.REGISTRY}").fetchall() != [(base.VERSION, base.NAME)]:
        raise RuntimeError("timing base registry is not exact v1")
    if connection.execute(f"SELECT version,name FROM {activation.REGISTRY}").fetchall() != [(activation.VERSION, activation.NAME)]:
        raise RuntimeError("timing activation registry is not exact v1")
    if connection.execute(f"SELECT version,name FROM {REGISTRY}").fetchall() != [(VERSION, NAME)]:
        raise RuntimeError("timing V2 authority registry is not exact v1")
    if connection.execute("PRAGMA foreign_key_check").fetchall():
        raise RuntimeError("timing V2 authority foreign-key integrity failed")


def require_nar_operational_timing_v2_authority_archive_compatible_schema(connection: sqlite3.Connection) -> None:
    """Repository gate for exact Phase103 or exact Phase104 union; strict gate remains."""
    connection = base._connection(connection)
    objects = base._objects(connection)
    if objects == base._DDL | activation._DDL | _DDL:
        require_nar_operational_timing_v2_authority_archive_schema(connection)
    else:
        from scripts.simulation import nar_operational_timing_runtime_execution_archive_migration as runtime
        runtime.require_nar_operational_timing_runtime_execution_archive_compatible_schema(connection)


def apply_nar_operational_timing_v2_authority_archive_migrations(connection: sqlite3.Connection) -> None:
    """Atomically add V2 authority only to an exact Phase100-installed archive."""
    connection = base._connection(connection)
    if connection.in_transaction:
        raise RuntimeError("V2 authority migration requires no caller transaction")
    connection.execute("BEGIN IMMEDIATE")
    try:
        objects = base._objects(connection)
        if objects == base._DDL | activation._DDL:
            activation.require_nar_operational_timing_activation_archive_schema(connection)
            for sql in _DDL.values():
                connection.execute(sql)
            connection.execute(f"INSERT INTO {REGISTRY}(version,name) VALUES(?,?)", (VERSION, NAME))
        elif objects != base._DDL | activation._DDL | _DDL:
            raise RuntimeError("V2 authority migration requires exact Phase100 or V2 schema")
        require_nar_operational_timing_v2_authority_archive_schema(connection)
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
