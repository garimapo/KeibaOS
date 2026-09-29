import sqlite3

import pytest

from scripts.simulation import nar_trusted_deba_acquisition_archive_migration as subject
from scripts.simulation.sqlite_nar_trusted_deba_acquisition_archive import SQLiteNARTrustedDebaAcquisitionArchive


@pytest.fixture
def connection():
    value = sqlite3.connect(":memory:")
    yield value
    value.close()


def test_explicit_migration_exact_schema_and_idempotence(connection):
    subject.apply_nar_trusted_deba_acquisition_archive_migrations(connection)
    subject.require_nar_trusted_deba_acquisition_archive_schema(connection)
    subject.apply_nar_trusted_deba_acquisition_archive_migrations(connection)
    assert connection.execute("PRAGMA foreign_keys").fetchone() == (1,)
    assert connection.execute(f"SELECT version,name FROM {subject.REGISTRY}").fetchall() == [(1, subject.NAME)]
    assert set(subject._objects(connection)) == set(subject.EXPECTED)


def test_constructor_does_not_migrate(connection):
    with pytest.raises(RuntimeError):
        SQLiteNARTrustedDebaAcquisitionArchive(connection=connection)
    assert connection.execute("SELECT name FROM sqlite_master").fetchall() == []


@pytest.mark.parametrize("sql", [
    "CREATE TABLE unexpected(x TEXT)",
    "CREATE TABLE sqliteXunexpected(x TEXT)",
    "CREATE TABLE phase111_declarations(identity TEXT PRIMARY KEY)",
])
def test_unknown_or_partial_initial_schema_is_rejected(connection, sql):
    connection.execute(sql)
    with pytest.raises(RuntimeError):
        subject.apply_nar_trusted_deba_acquisition_archive_migrations(connection)
    assert not connection.in_transaction
    assert subject.REGISTRY not in subject._objects(connection)


@pytest.mark.parametrize("change", ["extra", "sqlite_prefix_extra", "missing_trigger", "wrong_version"])
def test_schema_drift_fails_closed(connection, change):
    subject.apply_nar_trusted_deba_acquisition_archive_migrations(connection)
    if change == "extra":
        connection.execute("CREATE TABLE unexpected(x)")
    elif change == "sqlite_prefix_extra":
        connection.execute("CREATE TABLE sqliteXunexpected(x)")
    elif change == "missing_trigger":
        connection.execute("DROP TRIGGER phase111_claims_deny_delete")
    else:
        connection.execute("DROP TRIGGER nar_trusted_deba_acquisition_schema_versions_deny_update")
        connection.execute(f"UPDATE {subject.REGISTRY} SET name='unknown'")
        connection.commit()
    with pytest.raises(RuntimeError):
        subject.require_nar_trusted_deba_acquisition_archive_schema(connection)


def test_migration_rejects_caller_transaction(connection):
    connection.execute("BEGIN")
    with pytest.raises(RuntimeError):
        subject.apply_nar_trusted_deba_acquisition_archive_migrations(connection)
    assert connection.in_transaction
    connection.rollback()


def test_wrong_connection_type_rejected():
    with pytest.raises(ValueError):
        subject.apply_nar_trusted_deba_acquisition_archive_migrations(None)


@pytest.mark.parametrize("operation", ["UPDATE", "DELETE"])
def test_registry_append_only(connection, operation):
    subject.apply_nar_trusted_deba_acquisition_archive_migrations(connection)
    sql = f"UPDATE {subject.REGISTRY} SET name='bad'" if operation == "UPDATE" else f"DELETE FROM {subject.REGISTRY}"
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(sql)
    connection.rollback()


def test_restrictive_foreign_key_rejects_orphan_claim(connection):
    subject.apply_nar_trusted_deba_acquisition_archive_migrations(connection)
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute("INSERT INTO phase111_claims VALUES(?,?,?)", ("x" * 65, "{}", "missing"))
    connection.rollback()
