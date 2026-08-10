"""Dedicated migration runner for the separate NAR trusted-capture database."""

from __future__ import annotations

import sqlite3 as _sqlite3
from typing import Iterable as _Iterable

from scripts.simulation import nar_official_response_capture_migration as _v001


CAPTURE_MIGRATIONS = (_v001,)
_REGISTRY_TABLE = "nar_official_response_capture_schema_migrations"
_REGISTRY_DDL = """CREATE TABLE nar_official_response_capture_schema_migrations (
    version INTEGER PRIMARY KEY CHECK (typeof(version) = 'integer' AND version > 0),
    name TEXT NOT NULL CHECK (typeof(name) = 'text' AND name <> '')
) WITHOUT ROWID"""


def _require_connection(connection: object) -> _sqlite3.Connection:
    if type(connection) is not _sqlite3.Connection:
        raise ValueError("connection must be exact sqlite3.Connection")
    return connection


def _enable_foreign_keys(connection: _sqlite3.Connection) -> None:
    connection.execute("PRAGMA foreign_keys = ON")
    enabled = connection.execute("PRAGMA foreign_keys").fetchone()
    if enabled is None or enabled[0] != 1:
        raise RuntimeError("SQLite foreign_keys could not be enabled")


def _registry(migrations: _Iterable[object]) -> tuple[object, ...]:
    raw = tuple(migrations)
    for item in raw:
        if not hasattr(item, "VERSION") or not hasattr(item, "NAME") or not hasattr(item, "apply"):
            raise ValueError("capture migration must define VERSION, NAME, and apply")
        version = item.VERSION
        name = item.NAME
        if type(version) is not int or version <= 0 or type(name) is not str or not name or not callable(item.apply):
            raise ValueError("capture migration registry entry is invalid")
    ordered = tuple(sorted(raw, key=lambda item: item.VERSION))
    if len({item.VERSION for item in ordered}) != len(ordered):
        raise ValueError("capture migration registry has duplicate versions")
    return ordered


def _normalized_schema_sql(value: str) -> str:
    return " ".join(value.upper().split())


def _existing_registry_is_valid(connection: _sqlite3.Connection) -> bool:
    rows = connection.execute(
        "SELECT type,sql FROM sqlite_master WHERE name=?", (_REGISTRY_TABLE,),
    ).fetchall()
    if not rows:
        return False
    if len(rows) != 1 or rows[0][0] != "table" or type(rows[0][1]) is not str:
        raise RuntimeError("capture migration registry schema is malformed")
    if _normalized_schema_sql(rows[0][1]) != _normalized_schema_sql(_REGISTRY_DDL):
        raise RuntimeError("capture migration registry schema is malformed")
    columns = connection.execute(f"PRAGMA table_info({_REGISTRY_TABLE})").fetchall()
    expected = (("version", "INTEGER", 1, 1), ("name", "TEXT", 1, 0))
    actual = tuple((row[1], row[2], row[3], row[5]) for row in columns)
    if actual != expected:
        raise RuntimeError("capture migration registry schema is malformed")
    return True


def _create_registry(connection: _sqlite3.Connection) -> None:
    connection.execute(_REGISTRY_DDL)


def get_applied_capture_schema_versions(connection: _sqlite3.Connection) -> dict[int, str]:
    """Return validated applied dedicated-capture versions, without creating schema."""

    connection = _require_connection(connection)
    _enable_foreign_keys(connection)
    if not _existing_registry_is_valid(connection):
        return {}
    rows = connection.execute(f"SELECT version,name FROM {_REGISTRY_TABLE}").fetchall()
    applied: dict[int, str] = {}
    for version, name in rows:
        if type(version) is not int or version <= 0 or type(name) is not str or not name or version in applied:
            raise RuntimeError("capture migration registry is malformed")
        applied[version] = name
    return applied


def get_pending_capture_schema_migrations(
    connection: _sqlite3.Connection,
    migrations: _Iterable[object] = CAPTURE_MIGRATIONS,
) -> tuple[object, ...]:
    """Validate archive registry state and return its pending dedicated migrations."""

    registry = _registry(migrations)
    applied = get_applied_capture_schema_versions(connection)
    known = {item.VERSION: item.NAME for item in registry}
    if set(applied) - set(known):
        raise RuntimeError("unknown future capture schema migration version")
    if any(known[version] != name for version, name in applied.items()):
        raise RuntimeError("capture migration name mismatch")
    return tuple(item for item in registry if item.VERSION not in applied)


def apply_capture_schema_migrations(
    connection: _sqlite3.Connection,
    migrations: _Iterable[object] = CAPTURE_MIGRATIONS,
) -> None:
    """Atomically apply dedicated-capture migrations and their registry entries."""

    connection = _require_connection(connection)
    if connection.in_transaction:
        raise RuntimeError("connection must not already be in a transaction")
    registry = _registry(migrations)
    _enable_foreign_keys(connection)
    connection.execute("BEGIN IMMEDIATE")
    try:
        if not _existing_registry_is_valid(connection):
            _create_registry(connection)
        _existing_registry_is_valid(connection)
        pending = get_pending_capture_schema_migrations(connection, registry)
        for migration in pending:
            migration.apply(connection)
            connection.execute(
                f"INSERT INTO {_REGISTRY_TABLE}(version,name) VALUES(?,?)",
                (migration.VERSION, migration.NAME),
            )
        connection.commit()
    except BaseException:
        # The only broad boundary is transaction cleanup; the original error is re-raised unchanged.
        connection.rollback()
        raise


if "annotations" in globals():
    del annotations
