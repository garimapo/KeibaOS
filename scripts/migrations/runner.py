"""接続注入型・原子的SQLiteマイグレーションランナー。"""
from datetime import datetime, timezone
import sqlite3
from typing import Iterable
from .versions import (
    v008_simulation_schema,
    v009_simulation_bet_plan_schema,
    v010_historical_input_snapshot_schema,
    v011_historical_past_race_time_difference_schema,
)

MIGRATIONS = (
    v008_simulation_schema,
    v009_simulation_bet_plan_schema,
    v010_historical_input_snapshot_schema,
    v011_historical_past_race_time_difference_schema,
)

def _enable_foreign_keys(connection: sqlite3.Connection) -> None:
    connection.execute("PRAGMA foreign_keys = ON")
    if connection.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
        raise RuntimeError("SQLite foreign_keys could not be enabled")

def _registry(migrations: Iterable[object]) -> tuple[object, ...]:
    raw = tuple(migrations)
    for item in raw:
        if not hasattr(item, "VERSION") or not hasattr(item, "NAME") or not hasattr(item, "apply"):
            raise ValueError("migration must define VERSION, NAME, and apply")
        if (not isinstance(item.VERSION, int) or isinstance(item.VERSION, bool) or item.VERSION <= 0
                or not isinstance(item.NAME, str) or not item.NAME.strip()
                or not callable(item.apply)):
            raise ValueError("invalid migration registry entry")
    result = tuple(sorted(raw, key=lambda item: item.VERSION))
    versions = [item.VERSION for item in result]
    if any(not isinstance(v, int) or isinstance(v, bool) or v <= 0 for v in versions):
        raise ValueError("migration versions must be positive integers")
    if len(set(versions)) != len(versions) or any(not isinstance(item.NAME, str) or not item.NAME.strip() or not callable(getattr(item, "apply", None)) for item in result):
        raise ValueError("migration registry has duplicate versions or empty names")
    return result

def get_applied_versions(connection: sqlite3.Connection) -> dict[int, str]:
    _enable_foreign_keys(connection)
    if connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_migrations'").fetchone() is None:
        return {}
    return dict(connection.execute("SELECT version, name FROM schema_migrations"))

def get_pending_migrations(connection: sqlite3.Connection, migrations=MIGRATIONS):
    registry = _registry(migrations); applied = get_applied_versions(connection)
    known = {item.VERSION: item.NAME for item in registry}
    if set(applied) - set(known): raise RuntimeError("unknown future migration version")
    if any(known[v] != name for v, name in applied.items()): raise RuntimeError("migration name mismatch")
    return tuple(item for item in registry if item.VERSION not in applied)

def apply_migrations(connection: sqlite3.Connection, migrations=MIGRATIONS) -> None:
    if connection.in_transaction: raise RuntimeError("connection must not already be in a transaction")
    registry = _registry(migrations)
    _enable_foreign_keys(connection)
    connection.execute("BEGIN IMMEDIATE")
    try:
        connection.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_at TEXT NOT NULL)")
        connection.commit()
    except Exception:
        connection.rollback(); raise
    for migration in get_pending_migrations(connection, registry):
        connection.execute("BEGIN IMMEDIATE")
        try:
            migration.apply(connection)
            connection.execute("INSERT INTO schema_migrations VALUES (?,?,?)", (migration.VERSION, migration.NAME, datetime.now(timezone.utc).isoformat()))
            connection.commit()
        except Exception:
            connection.rollback(); raise
