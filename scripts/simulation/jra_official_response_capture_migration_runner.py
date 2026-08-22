"""Dedicated migration runner for JRA capture archive schema only."""

from __future__ import annotations

import sqlite3 as _sqlite3

from scripts.simulation import jra_official_response_capture_migration as _v001
from scripts.simulation import jra_official_response_capture_migration_v002 as _v002
from scripts.simulation import jra_official_response_capture_migration_v003 as _v003
from scripts.simulation import jra_official_response_capture_migration_v004 as _v004

JRA_CAPTURE_MIGRATIONS = (_v001, _v002, _v003, _v004)
_TABLE = "jra_official_response_capture_schema_migrations"


def _connection(value: object) -> _sqlite3.Connection:
    if type(value) is not _sqlite3.Connection:
        raise ValueError("connection must be exact sqlite3.Connection")
    return value


def _registry(connection: _sqlite3.Connection) -> None:
    row = connection.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (_TABLE,)).fetchone()
    if row is None:
        collisions = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('jra_official_response_bodies','jra_official_response_captures')"
        ).fetchall()
        if collisions:
            raise RuntimeError("unregistered JRA capture schema is invalid")
        connection.execute("""CREATE TABLE jra_official_response_capture_schema_migrations (
            version INTEGER PRIMARY KEY CHECK(typeof(version)='integer' AND version>0),
            name TEXT NOT NULL UNIQUE CHECK(typeof(name)='text' AND length(name)>0)
        ) WITHOUT ROWID""")
        return
    columns = connection.execute(f"PRAGMA table_info({_TABLE})").fetchall()
    if [(item[1], item[2], item[3], item[5]) for item in columns] != [("version", "INTEGER", 1, 1), ("name", "TEXT", 1, 0)]:
        raise RuntimeError("JRA capture migration registry schema is invalid")
    table_rows = connection.execute("PRAGMA table_list").fetchall()
    table = [item for item in table_rows if item[0] == "main" and item[1] == _TABLE]
    if table != [("main", _TABLE, "table", 2, 1, 0)]:
        raise RuntimeError("JRA capture migration registry WITHOUT ROWID schema is invalid")
    indexes = connection.execute(f"PRAGMA index_list({_TABLE})").fetchall()
    unique_name_indexes = [item[1] for item in indexes if item[2] == 1 and item[3] == "u"]
    if len(unique_name_indexes) != 1:
        raise RuntimeError("JRA capture migration registry unique constraint is invalid")
    index_columns = connection.execute(f"PRAGMA index_info({unique_name_indexes[0]})").fetchall()
    if [(item[0], item[2]) for item in index_columns] != [(0, "name")]:
        raise RuntimeError("JRA capture migration registry unique constraint is invalid")
    _probe_registry_constraints(connection)


def _probe_registry_constraints(connection: _sqlite3.Connection) -> None:
    if connection.execute(f"SELECT 1 FROM {_TABLE} WHERE version IN (0,-1)").fetchone() is not None:
        raise RuntimeError("JRA capture migration registry rows are invalid")
    if connection.execute(f"SELECT 1 FROM {_TABLE} WHERE name=''").fetchone() is not None:
        raise RuntimeError("JRA capture migration registry rows are invalid")
    versions = _probe_versions(connection)
    name = _probe_name(connection)
    connection.execute("SAVEPOINT jra_capture_registry_constraint_probe")
    try:
        _probe_rejected(connection, 0, name)
        _probe_rejected(connection, -1, name)
        _probe_rejected(connection, "not-an-integer", name)
        _probe_rejected(connection, versions[0], "")
        _probe_rejected(connection, versions[0], _sqlite3.Binary(b"not-text"))
        connection.execute(f"INSERT INTO {_TABLE}(version,name) VALUES(?,?)", (versions[0], name))
        _probe_rejected(connection, versions[1], name)
    finally:
        connection.execute("ROLLBACK TO jra_capture_registry_constraint_probe")
        connection.execute("RELEASE jra_capture_registry_constraint_probe")


def _probe_versions(connection: _sqlite3.Connection) -> tuple[int, int]:
    values: list[int] = []
    for candidate in range(9_223_372_036_854_775_807, 9_223_372_036_854_774_783, -1):
        if connection.execute(f"SELECT 1 FROM {_TABLE} WHERE version=?", (candidate,)).fetchone() is None:
            values.append(candidate)
            if len(values) == 2:
                return values[0], values[1]
    raise RuntimeError("unable to allocate JRA capture migration registry probe versions")


def _probe_name(connection: _sqlite3.Connection) -> str:
    for suffix in range(1, 1025):
        value = f"__jra_capture_registry_probe_{suffix}__"
        if connection.execute(f"SELECT 1 FROM {_TABLE} WHERE name=?", (value,)).fetchone() is None:
            return value
    raise RuntimeError("unable to allocate JRA capture migration registry probe name")


def _probe_rejected(connection: _sqlite3.Connection, version: object, name: object) -> None:
    try:
        connection.execute(f"INSERT INTO {_TABLE}(version,name) VALUES(?,?)", (version, name))
    except _sqlite3.IntegrityError:
        return
    raise RuntimeError("JRA capture migration registry constraints are invalid")


def get_applied_jra_capture_schema_versions(connection: _sqlite3.Connection) -> dict[int, str]:
    connection = _connection(connection)
    row = connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (_TABLE,)).fetchone()
    if row is None:
        return {}
    _registry(connection)
    values: dict[int, str] = {}
    for version, name in connection.execute(f"SELECT version,name FROM {_TABLE} ORDER BY version"):
        if type(version) is not int or version <= 0 or type(name) is not str or not name or version in values:
            raise RuntimeError("JRA capture migration registry row is invalid")
        values[version] = name
    return values


def get_pending_jra_capture_schema_migrations(connection: _sqlite3.Connection) -> tuple[object, ...]:
    applied = get_applied_jra_capture_schema_versions(connection)
    known = {item.VERSION: item.NAME for item in JRA_CAPTURE_MIGRATIONS}
    if set(applied) - set(known) or any(known[key] != value for key, value in applied.items()):
        raise RuntimeError("JRA capture migration registry is incompatible")
    return tuple(item for item in JRA_CAPTURE_MIGRATIONS if item.VERSION not in applied)


def apply_jra_capture_schema_migrations(connection: _sqlite3.Connection) -> None:
    connection = _connection(connection)
    if connection.in_transaction:
        raise RuntimeError("connection must not already be in a transaction")
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("BEGIN IMMEDIATE")
    try:
        _registry(connection)
        for migration in get_pending_jra_capture_schema_migrations(connection):
            migration.apply(connection)
            connection.execute(f"INSERT INTO {_TABLE}(version,name) VALUES(?,?)", (migration.VERSION, migration.NAME))
        connection.commit()
    except BaseException:
        connection.rollback()
        raise


if "annotations" in globals():
    del annotations
