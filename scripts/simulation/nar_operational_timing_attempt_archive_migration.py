"""Exact append-only Phase105 companion; execution claims are existing parents."""

from __future__ import annotations

import sqlite3

from scripts.simulation import nar_operational_timing_observability_archive_migration as base
from scripts.simulation import nar_operational_timing_activation_archive_migration as activation
from scripts.simulation import nar_operational_timing_v2_authority_archive_migration as v2
from scripts.simulation import nar_operational_timing_runtime_execution_archive_migration as runtime


VERSION = 1
NAME = "v001_nar_operational_timing_attempt_companion"
REGISTRY = "nar_operational_timing_attempt_schema_migrations"
ATTEMPTS = "nar_operational_timing_v2_attempts"
ENVIRONMENTS = "nar_operational_timing_request_environment_verifications"
TERMINALS = "nar_operational_timing_v2_terminals"
OVERHEAD = "nar_operational_timing_publication_overhead"

_DDL = {
    REGISTRY: f"CREATE TABLE {REGISTRY} (version INTEGER PRIMARY KEY CHECK(version=1), name TEXT NOT NULL CHECK(name='{NAME}')) WITHOUT ROWID",
    ATTEMPTS: (
        f"CREATE TABLE {ATTEMPTS} (identity TEXT PRIMARY KEY, "
        f"claim_identity TEXT NOT NULL REFERENCES {runtime.CLAIMS}(identity) ON UPDATE RESTRICT ON DELETE RESTRICT, "
        f"session_identity TEXT NOT NULL REFERENCES {v2.SESSIONS}(identity) ON UPDATE RESTRICT ON DELETE RESTRICT, "
        f"configuration_identity TEXT NOT NULL REFERENCES {v2.CONFIGS}(identity) ON UPDATE RESTRICT ON DELETE RESTRICT, "
        "attempt_sequence INTEGER NOT NULL CHECK(attempt_sequence>=0), stage TEXT NOT NULL, "
        "http_policy TEXT, payload_json TEXT NOT NULL, UNIQUE(claim_identity,attempt_sequence)) WITHOUT ROWID"
    ),
    ENVIRONMENTS: (
        f"CREATE TABLE {ENVIRONMENTS} (identity TEXT PRIMARY KEY, "
        f"attempt_identity TEXT NOT NULL UNIQUE REFERENCES {ATTEMPTS}(identity) ON UPDATE RESTRICT ON DELETE RESTRICT, "
        "qualification TEXT NOT NULL, payload_json TEXT NOT NULL) WITHOUT ROWID"
    ),
    TERMINALS: (
        f"CREATE TABLE {TERMINALS} (identity TEXT PRIMARY KEY, "
        f"attempt_identity TEXT NOT NULL UNIQUE REFERENCES {ATTEMPTS}(identity) ON UPDATE RESTRICT ON DELETE RESTRICT, "
        "payload_json TEXT NOT NULL) WITHOUT ROWID"
    ),
    OVERHEAD: (
        f"CREATE TABLE {OVERHEAD} (identity TEXT PRIMARY KEY, "
        f"claim_identity TEXT NOT NULL REFERENCES {runtime.CLAIMS}(identity) ON UPDATE RESTRICT ON DELETE RESTRICT, "
        f"attempt_identity TEXT NOT NULL REFERENCES {ATTEMPTS}(identity) ON UPDATE RESTRICT ON DELETE RESTRICT, "
        "stage TEXT NOT NULL, payload_json TEXT NOT NULL, UNIQUE(attempt_identity,stage)) WITHOUT ROWID"
    ),
}
for _table in (REGISTRY, ATTEMPTS, ENVIRONMENTS, TERMINALS, OVERHEAD):
    _DDL[f"trg_{_table}_no_update"] = (
        f"CREATE TRIGGER trg_{_table}_no_update BEFORE UPDATE ON {_table} "
        "BEGIN SELECT RAISE(ABORT, 'immutable timing evidence'); END"
    )
    _DDL[f"trg_{_table}_no_delete"] = (
        f"CREATE TRIGGER trg_{_table}_no_delete BEFORE DELETE ON {_table} "
        "BEGIN SELECT RAISE(ABORT, 'immutable timing evidence'); END"
    )
_DDL[f"trg_{ATTEMPTS}_parent_match"] = (
    f"CREATE TRIGGER trg_{ATTEMPTS}_parent_match BEFORE INSERT ON {ATTEMPTS} WHEN "
    f"(SELECT session_identity FROM {runtime.CLAIMS} WHERE identity=NEW.claim_identity) IS NOT NEW.session_identity OR "
    f"(SELECT configuration_identity FROM {runtime.CLAIMS} WHERE identity=NEW.claim_identity) IS NOT NEW.configuration_identity OR "
    f"(SELECT configuration_identity FROM {v2.SESSIONS} WHERE identity=NEW.session_identity) IS NOT NEW.configuration_identity "
    "BEGIN SELECT RAISE(ABORT, 'attempt parent contradiction'); END"
)
_DDL[f"trg_{ENVIRONMENTS}_http_parent"] = (
    f"CREATE TRIGGER trg_{ENVIRONMENTS}_http_parent BEFORE INSERT ON {ENVIRONMENTS} WHEN "
    f"(SELECT http_policy FROM {ATTEMPTS} WHERE identity=NEW.attempt_identity) IS NULL "
    "BEGIN SELECT RAISE(ABORT, 'request environment requires HTTP attempt'); END"
)
_DDL[f"trg_{OVERHEAD}_parent_match"] = (
    f"CREATE TRIGGER trg_{OVERHEAD}_parent_match BEFORE INSERT ON {OVERHEAD} WHEN "
    f"(SELECT claim_identity FROM {ATTEMPTS} WHERE identity=NEW.attempt_identity) IS NOT NEW.claim_identity "
    "BEGIN SELECT RAISE(ABORT, 'overhead parent contradiction'); END"
)


def require_nar_operational_timing_attempt_archive_schema(connection: sqlite3.Connection) -> None:
    connection = base._connection(connection)
    if base._objects(connection) != base._DDL | activation._DDL | v2._DDL | runtime._DDL | _DDL:
        raise RuntimeError("Phase105 attempt archive schema is not exact")
    for table, version, name in ((base.REGISTRY, base.VERSION, base.NAME),
                                 (activation.REGISTRY, activation.VERSION, activation.NAME),
                                 (v2.REGISTRY, v2.VERSION, v2.NAME),
                                 (runtime.REGISTRY, runtime.VERSION, runtime.NAME),
                                 (REGISTRY, VERSION, NAME)):
        if connection.execute(f"SELECT version,name FROM {table}").fetchall() != [(version, name)]:
            raise RuntimeError("Phase105 archive registry contradicts known state")
    if connection.execute("PRAGMA foreign_key_check").fetchall():
        raise RuntimeError("Phase105 archive foreign key integrity failed")


def require_nar_operational_timing_attempt_archive_compatible_schema(connection: sqlite3.Connection) -> None:
    """Normal repository use accepts only exact Phase105 or explicit diagnostic union."""
    connection = base._connection(connection)
    objects = base._objects(connection)
    if objects == base._DDL | activation._DDL | v2._DDL | runtime._DDL | _DDL:
        require_nar_operational_timing_attempt_archive_schema(connection)
    else:
        from scripts.simulation import nar_operational_timing_diagnostic_archive_migration as diagnostic
        if objects != base._DDL | activation._DDL | v2._DDL | runtime._DDL | _DDL | diagnostic._DDL:
            raise RuntimeError("attempt archive is not an exact known union")
        diagnostic.require_nar_operational_timing_diagnostic_archive_schema(connection)


def apply_nar_operational_timing_attempt_archive_migrations(connection: sqlite3.Connection) -> None:
    connection = base._connection(connection)
    if connection.in_transaction:
        raise RuntimeError("Phase105 migration requires idle connection")
    connection.execute("BEGIN IMMEDIATE")
    try:
        objects = base._objects(connection)
        if objects == base._DDL | activation._DDL | v2._DDL | runtime._DDL:
            runtime.require_nar_operational_timing_runtime_execution_archive_schema(connection)
            for statement in _DDL.values():
                connection.execute(statement)
            connection.execute(f"INSERT INTO {REGISTRY}(version,name) VALUES(?,?)", (VERSION, NAME))
        elif objects != base._DDL | activation._DDL | v2._DDL | runtime._DDL | _DDL:
            raise RuntimeError("Phase105 migration requires exact Phase104 or Phase105 schema")
        require_nar_operational_timing_attempt_archive_schema(connection)
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
