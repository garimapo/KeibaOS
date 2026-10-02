"""V019 registration, exact topology, and fail-closed schema states."""

import sqlite3

import pytest

from scripts.migrations.runner import MIGRATIONS, apply_migrations, get_applied_versions
from scripts.migrations.versions.v019_nar_production_mapping_authority_schema import (
    NAME, PHASE109_SCHEMA_ACTIVE, PHASE109_SCHEMA_INTEGRITY_FAILURE,
    PHASE109_SCHEMA_NOT_INSTALLED, phase109_schema_state, require_phase109_schema,
)
from test_sqlite_nar_identity_complete_entry_repository import close_all, repository_env
from test_v018_nar_identity_complete_entry_schema import legacy_db


def test_v019_registered_exact_and_rerun_is_idempotent():
    env, _, connection, _ = repository_env()
    try:
        assert tuple(item.VERSION for item in MIGRATIONS)[-2:] == (18, 19)
        assert get_applied_versions(connection)[19] == NAME
        assert phase109_schema_state(connection) == PHASE109_SCHEMA_ACTIVE
        require_phase109_schema(connection)
        apply_migrations(connection)
        assert phase109_schema_state(connection) == PHASE109_SCHEMA_ACTIVE
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        close_all(env, connection)


def test_absent_and_partial_topology_are_distinct():
    c = sqlite3.connect(":memory:")
    try:
        assert phase109_schema_state(c) == PHASE109_SCHEMA_NOT_INSTALLED
        c.execute("CREATE TABLE nar_production_mapping_receipts(id TEXT)")
        assert phase109_schema_state(c) == PHASE109_SCHEMA_INTEGRITY_FAILURE
    finally:
        c.close()


def test_registered_but_missing_object_fails_closed():
    env, _, connection, _ = repository_env()
    try:
        connection.execute("DROP TRIGGER nar_production_mapping_v010_entry_no_extra")
        connection.commit()
        assert phase109_schema_state(connection) == PHASE109_SCHEMA_INTEGRITY_FAILURE
        with pytest.raises(RuntimeError, match="exact active"):
            require_phase109_schema(connection)
    finally:
        close_all(env, connection)


def test_wrong_registration_fails_closed():
    env, _, connection, _ = repository_env()
    try:
        connection.execute("UPDATE schema_migrations SET name='wrong' WHERE version=19")
        connection.commit()
        assert phase109_schema_state(connection) == PHASE109_SCHEMA_INTEGRITY_FAILURE
    finally:
        close_all(env, connection)


def test_v010_mapping_topology_drift_fails_closed():
    env, _, connection, _ = repository_env()
    try:
        connection.execute("ALTER TABLE historical_input_external_entries ADD COLUMN unauthorized TEXT")
        connection.commit()
        assert phase109_schema_state(connection) == PHASE109_SCHEMA_INTEGRITY_FAILURE
    finally:
        close_all(env, connection)


def test_v019_preflight_rejects_preexisting_v010_topology_drift_without_partial_install():
    connection = legacy_db()
    try:
        apply_migrations(connection, tuple(m for m in MIGRATIONS if m.VERSION <= 18))
        assert set(get_applied_versions(connection)) == set(range(8, 19))
        connection.execute("ALTER TABLE historical_input_external_entries ADD COLUMN unauthorized TEXT")
        connection.commit()
        assert phase109_schema_state(connection) == PHASE109_SCHEMA_NOT_INSTALLED

        with pytest.raises(RuntimeError, match="exact V010 mapping topology"):
            apply_migrations(connection)

        assert 19 not in get_applied_versions(connection)
        assert connection.execute("""SELECT name FROM sqlite_schema
            WHERE name GLOB 'nar_production_mapping_*'""").fetchall() == []
        assert any(row[1] == "unauthorized" for row in connection.execute(
            "PRAGMA table_xinfo('historical_input_external_entries')"))
        assert not connection.in_transaction
    finally:
        connection.close()


def test_operational_lock_is_not_schema_corruption():
    class LockedConnection(sqlite3.Connection):
        def execute(self, *_args, **_kwargs):
            raise sqlite3.OperationalError("database is locked")

    c = sqlite3.connect(":memory:", factory=LockedConnection)
    try:
        with pytest.raises(sqlite3.OperationalError, match="database is locked"):
            phase109_schema_state(c)
    finally:
        c.close()
