"""Dedicated migration runner for JRA capture archive schema only."""

from __future__ import annotations

import sqlite3 as _sqlite3

from scripts.simulation import jra_official_response_capture_migration as _v001

JRA_CAPTURE_MIGRATIONS = (_v001,)
_TABLE = "jra_official_response_capture_schema_migrations"


def _connection(value: object) -> _sqlite3.Connection:
    if type(value) is not _sqlite3.Connection:
        raise ValueError("connection must be exact sqlite3.Connection")
    return value


def _registry(connection: _sqlite3.Connection) -> None:
    row = connection.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (_TABLE,)).fetchone()
    if row is None:
        connection.execute("""CREATE TABLE jra_official_response_capture_schema_migrations (
            version INTEGER PRIMARY KEY CHECK(typeof(version)='integer' AND version>0),
            name TEXT NOT NULL UNIQUE CHECK(typeof(name)='text' AND length(name)>0)
        ) WITHOUT ROWID""")
        return
    columns = connection.execute(f"PRAGMA table_info({_TABLE})").fetchall()
    if [(item[1], item[2], item[3], item[5]) for item in columns] != [("version", "INTEGER", 1, 1), ("name", "TEXT", 1, 0)]:
        raise RuntimeError("JRA capture migration registry schema is invalid")
    sql = row[0]
    if type(sql) is not str or "WITHOUT ROWID" not in sql.upper():
        raise RuntimeError("JRA capture migration registry is invalid")


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
