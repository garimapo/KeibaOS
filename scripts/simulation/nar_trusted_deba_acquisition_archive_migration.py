"""Explicit isolated Phase111 lineage schema; existing response archives stay separate."""
import sqlite3

VERSION = 1
NAME = "nar_trusted_deba_acquisition_v1"
REGISTRY = "nar_trusted_deba_acquisition_schema_versions"
REGISTRY_SQL = f"CREATE TABLE {REGISTRY}(version INTEGER NOT NULL PRIMARY KEY CHECK(version=1), name TEXT NOT NULL CHECK(typeof(name)='text'))"


def _record_table(name, extra=""):
    return (f"CREATE TABLE {name}(identity TEXT NOT NULL PRIMARY KEY CHECK(typeof(identity)='text' AND length(identity)>64), "
            f"payload TEXT NOT NULL CHECK(typeof(payload)='text' AND length(payload)>0){extra})")


TABLES = {
    REGISTRY: REGISTRY_SQL,
    "phase111_declarations": _record_table("phase111_declarations"),
    "phase111_claims": _record_table("phase111_claims", ", declaration_id TEXT NOT NULL UNIQUE REFERENCES phase111_declarations(identity) ON UPDATE RESTRICT ON DELETE RESTRICT, UNIQUE(identity,declaration_id)"),
    "phase111_failures": _record_table("phase111_failures", ", declaration_id TEXT NOT NULL, claim_id TEXT NOT NULL UNIQUE, FOREIGN KEY(claim_id,declaration_id) REFERENCES phase111_claims(identity,declaration_id) ON UPDATE RESTRICT ON DELETE RESTRICT"),
    "phase111_receipts": _record_table("phase111_receipts", ", declaration_id TEXT NOT NULL, claim_id TEXT NOT NULL UNIQUE, FOREIGN KEY(claim_id,declaration_id) REFERENCES phase111_claims(identity,declaration_id) ON UPDATE RESTRICT ON DELETE RESTRICT"),
}
TRIGGERS = {}
for table in TABLES:
    for operation in ("UPDATE", "DELETE"):
        name = f"{table}_deny_{operation.lower()}"
        TRIGGERS[name] = f"CREATE TRIGGER {name} BEFORE {operation} ON {table} BEGIN SELECT RAISE(ABORT,'Phase111 archive is append-only'); END"
for table, other in (("phase111_receipts", "phase111_failures"), ("phase111_failures", "phase111_receipts")):
    name = f"{table}_deny_other_terminal"
    TRIGGERS[name] = f"CREATE TRIGGER {name} BEFORE INSERT ON {table} WHEN EXISTS(SELECT 1 FROM {other} WHERE claim_id=NEW.claim_id) BEGIN SELECT RAISE(ABORT,'claim already has a terminal'); END"
EXPECTED = {**{k: ("table", v) for k, v in TABLES.items()},
            **{k: ("trigger", v) for k, v in TRIGGERS.items()}}


def _connection(connection):
    if type(connection) is not sqlite3.Connection:
        raise ValueError("exact sqlite3.Connection required")
    return connection


def _objects(connection):
    return {row[0]: (row[1], " ".join(row[2].split())) for row in connection.execute(
        "SELECT name,type,sql FROM sqlite_master WHERE name NOT GLOB 'sqlite_*'").fetchall()}


def _foreign_keys(connection):
    connection.execute("PRAGMA foreign_keys=ON")
    if connection.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
        raise RuntimeError("foreign keys must be enabled")


def require_nar_trusted_deba_acquisition_archive_schema(connection):
    """Exact read-only topology/version/integrity gate; never creates or repairs."""
    _connection(connection)
    _foreign_keys(connection)
    expected = {k: (v[0], " ".join(v[1].split())) for k, v in EXPECTED.items()}
    if _objects(connection) != expected:
        raise RuntimeError("Phase111 archive has missing/unknown/incompatible schema")
    if connection.execute(f"SELECT version,name FROM {REGISTRY}").fetchall() != [(VERSION, NAME)]:
        raise RuntimeError("Phase111 archive registry mismatch")
    if connection.execute("PRAGMA foreign_key_check").fetchall():
        raise RuntimeError("Phase111 foreign-key integrity failed")


def apply_nar_trusted_deba_acquisition_archive_migrations(connection):
    """Explicit all-or-nothing installation into an empty dedicated database."""
    _connection(connection)
    if connection.in_transaction:
        raise RuntimeError("active caller transaction rejected")
    _foreign_keys(connection)
    connection.execute("BEGIN IMMEDIATE")
    try:
        if _objects(connection):
            require_nar_trusted_deba_acquisition_archive_schema(connection)
        else:
            for sql in TABLES.values():
                connection.execute(sql)
            for sql in TRIGGERS.values():
                connection.execute(sql)
            connection.execute(f"INSERT INTO {REGISTRY}(version,name) VALUES(?,?)", (VERSION, NAME))
            require_nar_trusted_deba_acquisition_archive_schema(connection)
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
