"""Exact same-database v1 companion for Phase99 timing session activation.

The Phase99 registry remains v1-only. This companion has its own registry and
never changes or backfills the base archive.
"""

from __future__ import annotations

import sqlite3

from scripts.simulation import nar_operational_timing_observability_archive_migration as base


VERSION = 1
NAME = "v001_nar_operational_timing_activation_companion"
REGISTRY = "nar_operational_timing_activation_schema_migrations"
DECLARATIONS = "nar_operational_timing_activation_declarations"
VERIFICATIONS = "nar_operational_timing_activation_verifications"

_DDL = {
    REGISTRY: f"CREATE TABLE {REGISTRY} (version INTEGER PRIMARY KEY CHECK(version=1), name TEXT NOT NULL CHECK(name='{NAME}')) WITHOUT ROWID",
    DECLARATIONS: (
        f"CREATE TABLE {DECLARATIONS} (identity TEXT PRIMARY KEY, "
        f"session_identity TEXT NOT NULL UNIQUE REFERENCES {base.SESSIONS}(identity) ON UPDATE RESTRICT ON DELETE RESTRICT, "
        f"configuration_identity TEXT NOT NULL REFERENCES {base.CONFIGS}(identity) ON UPDATE RESTRICT ON DELETE RESTRICT, "
        "payload_json TEXT NOT NULL) WITHOUT ROWID"
    ),
    VERIFICATIONS: (
        f"CREATE TABLE {VERIFICATIONS} (identity TEXT PRIMARY KEY, "
        f"declaration_identity TEXT NOT NULL UNIQUE REFERENCES {DECLARATIONS}(identity) ON UPDATE RESTRICT ON DELETE RESTRICT, "
        "session_identity TEXT NOT NULL, configuration_identity TEXT NOT NULL, "
        "payload_json TEXT NOT NULL) WITHOUT ROWID"
    ),
}
for _table in (DECLARATIONS, VERIFICATIONS):
    _DDL[f"trg_{_table}_no_update"] = (
        f"CREATE TRIGGER trg_{_table}_no_update BEFORE UPDATE ON {_table} "
        "BEGIN SELECT RAISE(ABORT, 'immutable timing activation'); END"
    )
    _DDL[f"trg_{_table}_no_delete"] = (
        f"CREATE TRIGGER trg_{_table}_no_delete BEFORE DELETE ON {_table} "
        "BEGIN SELECT RAISE(ABORT, 'immutable timing activation'); END"
    )
_DDL[f"trg_{REGISTRY}_no_update"] = (
    f"CREATE TRIGGER trg_{REGISTRY}_no_update BEFORE UPDATE ON {REGISTRY} "
    "BEGIN SELECT RAISE(ABORT, 'immutable timing activation registry'); END"
)
_DDL[f"trg_{REGISTRY}_no_delete"] = (
    f"CREATE TRIGGER trg_{REGISTRY}_no_delete BEFORE DELETE ON {REGISTRY} "
    "BEGIN SELECT RAISE(ABORT, 'immutable timing activation registry'); END"
)
_DDL[f"trg_{DECLARATIONS}_parent_match"] = (
    f"CREATE TRIGGER trg_{DECLARATIONS}_parent_match BEFORE INSERT ON {DECLARATIONS} "
    f"WHEN (SELECT configuration_identity FROM {base.SESSIONS} WHERE identity=NEW.session_identity) "
    "IS NOT NEW.configuration_identity "
    "BEGIN SELECT RAISE(ABORT, 'activation session configuration mismatch'); END"
)
_DDL[f"trg_{VERIFICATIONS}_parent_match"] = (
    f"CREATE TRIGGER trg_{VERIFICATIONS}_parent_match BEFORE INSERT ON {VERIFICATIONS} "
    f"WHEN (SELECT session_identity FROM {DECLARATIONS} WHERE identity=NEW.declaration_identity) "
    "IS NOT NEW.session_identity OR "
    f"(SELECT configuration_identity FROM {DECLARATIONS} WHERE identity=NEW.declaration_identity) "
    "IS NOT NEW.configuration_identity "
    "BEGIN SELECT RAISE(ABORT, 'activation declaration mismatch'); END"
)


def _require_base_registry(connection: sqlite3.Connection) -> None:
    if connection.execute(f"SELECT version,name FROM {base.REGISTRY}").fetchall() != [(base.VERSION, base.NAME)]:
        raise RuntimeError("timing base migration registry is not exact v1")
    if connection.execute("PRAGMA foreign_key_check").fetchall():
        raise RuntimeError("timing archive foreign-key integrity failed")


def require_nar_operational_timing_archive_compatible_schema(connection: sqlite3.Connection) -> None:
    """Accept only exact historical base v1 or exact base with companion v1."""
    connection = base._connection(connection)
    objects = base._objects(connection)
    if objects == base._DDL:
        base.require_nar_operational_timing_observability_archive_schema(connection)
    elif objects == base._DDL | _DDL:
        require_nar_operational_timing_activation_archive_schema(connection)
    else:
        raise RuntimeError("timing archive is neither exact base v1 nor exact companion v1")


def require_nar_operational_timing_activation_archive_schema(connection: sqlite3.Connection) -> None:
    """Require the exact union; never accept a partial or unknown companion."""
    connection = base._connection(connection)
    if base._objects(connection) != base._DDL | _DDL:
        raise RuntimeError("timing activation companion schema is not exact")
    _require_base_registry(connection)
    if connection.execute(f"SELECT version,name FROM {REGISTRY}").fetchall() != [(VERSION, NAME)]:
        raise RuntimeError("timing activation companion registry is not exact v1")


def apply_nar_operational_timing_activation_archive_migrations(connection: sqlite3.Connection) -> None:
    """Explicit atomic companion installation on an exact Phase99 archive."""
    connection = base._connection(connection)
    if connection.in_transaction:
        raise RuntimeError("activation migration requires no caller transaction")
    connection.execute("BEGIN IMMEDIATE")
    try:
        objects = base._objects(connection)
        if objects == base._DDL:
            base.require_nar_operational_timing_observability_archive_schema(connection)
            for sql in _DDL.values():
                connection.execute(sql)
            connection.execute(f"INSERT INTO {REGISTRY}(version,name) VALUES(?,?)", (VERSION, NAME))
        elif objects != base._DDL | _DDL:
            raise RuntimeError("activation migration requires exact base or companion schema")
        require_nar_operational_timing_activation_archive_schema(connection)
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
