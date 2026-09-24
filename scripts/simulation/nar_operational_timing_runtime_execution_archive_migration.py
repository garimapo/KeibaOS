"""Exact Phase104 runtime/execution companion over immutable Phase99-103 schemas."""

from __future__ import annotations

import sqlite3

from scripts.simulation import nar_operational_timing_observability_archive_migration as base
from scripts.simulation import nar_operational_timing_activation_archive_migration as activation
from scripts.simulation import nar_operational_timing_v2_authority_archive_migration as v2


VERSION = 1
NAME = "v001_nar_operational_timing_runtime_execution_companion"
REGISTRY = "nar_operational_timing_runtime_execution_schema_migrations"
BUNDLES = "nar_operational_timing_runtime_source_bundles"
DEPENDENCIES = "nar_operational_timing_runtime_dependencies"
TRANSPORTS = "nar_operational_timing_runtime_transports"
BINDINGS = "nar_operational_timing_runtime_bindings"
CLAIMS = "nar_operational_timing_campaign_execution_claims"
READINESS = "nar_operational_timing_campaign_readiness_receipts"

_DDL = {
    REGISTRY: f"CREATE TABLE {REGISTRY} (version INTEGER PRIMARY KEY CHECK(version=1), name TEXT NOT NULL CHECK(name='{NAME}')) WITHOUT ROWID",
    BUNDLES: f"CREATE TABLE {BUNDLES} (identity TEXT PRIMARY KEY, payload_json TEXT NOT NULL) WITHOUT ROWID",
    DEPENDENCIES: f"CREATE TABLE {DEPENDENCIES} (identity TEXT PRIMARY KEY, payload_json TEXT NOT NULL) WITHOUT ROWID",
    TRANSPORTS: f"CREATE TABLE {TRANSPORTS} (identity TEXT PRIMARY KEY, payload_json TEXT NOT NULL) WITHOUT ROWID",
    BINDINGS: (
        f"CREATE TABLE {BINDINGS} (identity TEXT PRIMARY KEY, "
        f"configuration_identity TEXT NOT NULL REFERENCES {v2.CONFIGS}(identity) ON UPDATE RESTRICT ON DELETE RESTRICT, "
        f"session_identity TEXT NOT NULL REFERENCES {v2.SESSIONS}(identity) ON UPDATE RESTRICT ON DELETE RESTRICT, "
        f"declaration_identity TEXT NOT NULL REFERENCES {v2.DECLARATIONS}(identity) ON UPDATE RESTRICT ON DELETE RESTRICT, "
        f"verification_identity TEXT NOT NULL REFERENCES {v2.VERIFICATIONS}(identity) ON UPDATE RESTRICT ON DELETE RESTRICT, "
        f"bundle_identity TEXT NOT NULL REFERENCES {BUNDLES}(identity) ON UPDATE RESTRICT ON DELETE RESTRICT, "
        f"dependency_identity TEXT NOT NULL REFERENCES {DEPENDENCIES}(identity) ON UPDATE RESTRICT ON DELETE RESTRICT, "
        f"transport_identity TEXT NOT NULL REFERENCES {TRANSPORTS}(identity) ON UPDATE RESTRICT ON DELETE RESTRICT, "
        "lock_scope_identity TEXT NOT NULL, payload_json TEXT NOT NULL) WITHOUT ROWID"
    ),
    CLAIMS: (
        f"CREATE TABLE {CLAIMS} (identity TEXT PRIMARY KEY, "
        f"session_identity TEXT NOT NULL UNIQUE REFERENCES {v2.SESSIONS}(identity) ON UPDATE RESTRICT ON DELETE RESTRICT, "
        f"binding_identity TEXT NOT NULL UNIQUE REFERENCES {BINDINGS}(identity) ON UPDATE RESTRICT ON DELETE RESTRICT, "
        f"configuration_identity TEXT NOT NULL REFERENCES {v2.CONFIGS}(identity) ON UPDATE RESTRICT ON DELETE RESTRICT, "
        f"verification_identity TEXT NOT NULL REFERENCES {v2.VERIFICATIONS}(identity) ON UPDATE RESTRICT ON DELETE RESTRICT, "
        "payload_json TEXT NOT NULL) WITHOUT ROWID"
    ),
    READINESS: (
        f"CREATE TABLE {READINESS} (identity TEXT PRIMARY KEY, "
        f"claim_identity TEXT NOT NULL UNIQUE REFERENCES {CLAIMS}(identity) ON UPDATE RESTRICT ON DELETE RESTRICT, "
        f"binding_identity TEXT NOT NULL REFERENCES {BINDINGS}(identity) ON UPDATE RESTRICT ON DELETE RESTRICT, "
        f"session_identity TEXT NOT NULL REFERENCES {v2.SESSIONS}(identity) ON UPDATE RESTRICT ON DELETE RESTRICT, "
        "payload_json TEXT NOT NULL) WITHOUT ROWID"
    ),
}
for _table in (REGISTRY, BUNDLES, DEPENDENCIES, TRANSPORTS, BINDINGS, CLAIMS, READINESS):
    _DDL[f"trg_{_table}_no_update"] = (
        f"CREATE TRIGGER trg_{_table}_no_update BEFORE UPDATE ON {_table} "
        "BEGIN SELECT RAISE(ABORT, 'immutable runtime execution authority'); END"
    )
    _DDL[f"trg_{_table}_no_delete"] = (
        f"CREATE TRIGGER trg_{_table}_no_delete BEFORE DELETE ON {_table} "
        "BEGIN SELECT RAISE(ABORT, 'immutable runtime execution authority'); END"
    )
_DDL[f"trg_{BINDINGS}_parent_match"] = (
    f"CREATE TRIGGER trg_{BINDINGS}_parent_match BEFORE INSERT ON {BINDINGS} WHEN "
    f"(SELECT configuration_identity FROM {v2.SESSIONS} WHERE identity=NEW.session_identity) IS NOT NEW.configuration_identity OR "
    f"(SELECT session_identity FROM {v2.DECLARATIONS} WHERE identity=NEW.declaration_identity) IS NOT NEW.session_identity OR "
    f"(SELECT configuration_identity FROM {v2.DECLARATIONS} WHERE identity=NEW.declaration_identity) IS NOT NEW.configuration_identity OR "
    f"(SELECT declaration_identity FROM {v2.VERIFICATIONS} WHERE identity=NEW.verification_identity) IS NOT NEW.declaration_identity "
    "BEGIN SELECT RAISE(ABORT, 'runtime binding parent contradiction'); END"
)
_DDL[f"trg_{CLAIMS}_parent_match"] = (
    f"CREATE TRIGGER trg_{CLAIMS}_parent_match BEFORE INSERT ON {CLAIMS} WHEN "
    f"(SELECT session_identity FROM {BINDINGS} WHERE identity=NEW.binding_identity) IS NOT NEW.session_identity OR "
    f"(SELECT configuration_identity FROM {BINDINGS} WHERE identity=NEW.binding_identity) IS NOT NEW.configuration_identity OR "
    f"(SELECT verification_identity FROM {BINDINGS} WHERE identity=NEW.binding_identity) IS NOT NEW.verification_identity "
    "BEGIN SELECT RAISE(ABORT, 'execution claim parent contradiction'); END"
)
_DDL[f"trg_{READINESS}_parent_match"] = (
    f"CREATE TRIGGER trg_{READINESS}_parent_match BEFORE INSERT ON {READINESS} WHEN "
    f"(SELECT binding_identity FROM {CLAIMS} WHERE identity=NEW.claim_identity) IS NOT NEW.binding_identity OR "
    f"(SELECT session_identity FROM {CLAIMS} WHERE identity=NEW.claim_identity) IS NOT NEW.session_identity "
    "BEGIN SELECT RAISE(ABORT, 'readiness parent contradiction'); END"
)


def require_nar_operational_timing_runtime_execution_archive_schema(connection: sqlite3.Connection) -> None:
    connection = base._connection(connection)
    if base._objects(connection) != base._DDL | activation._DDL | v2._DDL | _DDL:
        raise RuntimeError("runtime/execution archive schema is not exact")
    for table, version, name in ((base.REGISTRY, base.VERSION, base.NAME),
                                  (activation.REGISTRY, activation.VERSION, activation.NAME),
                                  (v2.REGISTRY, v2.VERSION, v2.NAME),
                                  (REGISTRY, VERSION, NAME)):
        if connection.execute(f"SELECT version,name FROM {table}").fetchall() != [(version, name)]:
            raise RuntimeError("runtime/execution archive registry contradicts known state")
    if connection.execute("PRAGMA foreign_key_check").fetchall():
        raise RuntimeError("runtime/execution archive foreign key integrity failed")


def require_nar_operational_timing_runtime_execution_archive_compatible_schema(connection: sqlite3.Connection) -> None:
    """Normal repository gate; historical Phase104 exact validator remains strict."""
    connection = base._connection(connection)
    objects = base._objects(connection)
    if objects == base._DDL | activation._DDL | v2._DDL | _DDL:
        require_nar_operational_timing_runtime_execution_archive_schema(connection)
    else:
        from scripts.simulation import nar_operational_timing_attempt_archive_migration as attempt
        if objects != base._DDL | activation._DDL | v2._DDL | _DDL | attempt._DDL:
            raise RuntimeError("runtime/execution archive is not an exact known union")
        attempt.require_nar_operational_timing_attempt_archive_schema(connection)


def apply_nar_operational_timing_runtime_execution_archive_migrations(connection: sqlite3.Connection) -> None:
    connection = base._connection(connection)
    if connection.in_transaction:
        raise RuntimeError("runtime/execution migration requires idle connection")
    connection.execute("BEGIN IMMEDIATE")
    try:
        objects = base._objects(connection)
        if objects == base._DDL | activation._DDL | v2._DDL:
            v2.require_nar_operational_timing_v2_authority_archive_schema(connection)
            for statement in _DDL.values():
                connection.execute(statement)
            connection.execute(f"INSERT INTO {REGISTRY}(version,name) VALUES(?,?)", (VERSION, NAME))
        elif objects != base._DDL | activation._DDL | v2._DDL | _DDL:
            raise RuntimeError("runtime/execution migration requires exact Phase103 or Phase104 schema")
        require_nar_operational_timing_runtime_execution_archive_schema(connection)
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
