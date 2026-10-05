"""Exact standalone companion topology and runner-owned rollback behavior."""

import sqlite3

import pytest

from scripts.simulation import nar_pre_c_production_prestaged_manifest_archive_migration as schema


def test_absent_install_exact_topology_and_idempotent_rerun():
    connection = sqlite3.connect(":memory:")
    try:
        assert schema.phase112_schema_state(connection) == schema.NOT_INSTALLED
        schema.apply(connection)
        assert schema.phase112_schema_state(connection) == schema.ACTIVE
        assert schema._objects(connection) == schema._expected()
        assert connection.execute(f"SELECT version,name FROM {schema.REGISTRY}").fetchall() == [
            (schema.VERSION, schema.NAME)]
        schema.apply(connection)
        assert schema.phase112_schema_state(connection) == schema.ACTIVE
        assert not connection.in_transaction
    finally:
        connection.close()


@pytest.mark.parametrize("drift", ["missing_trigger", "wrong_registry", "extra_index", "missing_table"])
def test_partial_or_contradictory_schema_is_not_absence(drift):
    connection = sqlite3.connect(":memory:")
    try:
        schema.apply(connection)
        if drift == "missing_trigger":
            connection.execute(f"DROP TRIGGER {schema.MANIFESTS}_no_update")
        elif drift == "wrong_registry":
            connection.execute("PRAGMA ignore_check_constraints=ON")
            connection.execute(f"UPDATE {schema.REGISTRY} SET name='wrong'")
            connection.execute("PRAGMA ignore_check_constraints=OFF")
        elif drift == "extra_index":
            connection.execute(f"CREATE INDEX unreviewed ON {schema.MANIFESTS}(external_race_id)")
        else:
            connection.execute(f"DROP TABLE {schema.AVAILABILITY}")
        connection.commit()
        assert schema.phase112_schema_state(connection) == schema.INTEGRITY_FAILURE
        with pytest.raises(RuntimeError, match="contradictory"):
            schema.apply(connection)
    finally:
        connection.close()


def test_unregistered_objects_are_corruption():
    connection = sqlite3.connect(":memory:")
    try:
        connection.execute(f"CREATE TABLE {schema.MANIFESTS}(identity TEXT)")
        connection.commit()
        assert schema.phase112_schema_state(connection) == schema.INTEGRITY_FAILURE
    finally:
        connection.close()


def test_sqlite_like_wildcard_name_is_not_hidden_from_exact_topology():
    connection = sqlite3.connect(":memory:")
    try:
        schema.apply(connection)
        connection.execute("CREATE TABLE sqliteXunreviewed(value INTEGER)")
        connection.commit()
        assert connection.execute(
            "SELECT name FROM sqlite_schema WHERE name='sqliteXunreviewed'"
        ).fetchone() == ("sqliteXunreviewed",)
        assert "sqliteXunreviewed" in schema._objects(connection)
        assert schema.phase112_schema_state(connection) == schema.INTEGRITY_FAILURE
    finally:
        connection.close()


def test_install_failure_rolls_back_every_object_and_registry():
    connection = sqlite3.connect(":memory:")
    def deny_trigger(action, *_args):
        return sqlite3.SQLITE_DENY if action == sqlite3.SQLITE_CREATE_TRIGGER else sqlite3.SQLITE_OK
    try:
        connection.set_authorizer(deny_trigger)
        with pytest.raises(sqlite3.DatabaseError):
            schema.apply(connection)
        connection.set_authorizer(None)
        assert schema.phase112_schema_state(connection) == schema.NOT_INSTALLED
        assert schema._objects(connection) == {}
        assert not connection.in_transaction
    finally:
        connection.close()


def test_unexpected_database_lock_is_not_relabelled_as_corruption(tmp_path):
    path = tmp_path / "phase112-lock.sqlite"
    writer = sqlite3.connect(path)
    reader = sqlite3.connect(path, timeout=0)
    try:
        schema.apply(writer)
        writer.execute("BEGIN EXCLUSIVE")
        with pytest.raises(sqlite3.OperationalError, match="locked"):
            schema.phase112_schema_state(reader)
    finally:
        writer.rollback()
        writer.close()
        reader.close()
