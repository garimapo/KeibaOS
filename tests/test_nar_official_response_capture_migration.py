from __future__ import annotations

import inspect
import sqlite3
import unittest

from scripts.migrations.runner import MIGRATIONS
from scripts.simulation import nar_official_response_capture_migration as migration
from scripts.simulation.nar_official_response_capture_migration_runner import (
    CAPTURE_MIGRATIONS,
    apply_capture_schema_migrations,
    get_applied_capture_schema_versions,
    get_pending_capture_schema_migrations,
)
import scripts.simulation.nar_official_response_capture_migration_runner as runner_module


class CaptureMigrationTests(unittest.TestCase):
    def _connection(self) -> sqlite3.Connection:
        return sqlite3.connect(":memory:")

    def test_v001_metadata_and_direct_apply_are_transaction_neutral(self) -> None:
        self.assertEqual(migration.VERSION, 1)
        self.assertEqual(migration.NAME, "v001_nar_official_response_capture_schema")
        connection = self._connection()
        migration.apply(connection)
        self.assertFalse(connection.in_transaction)
        with self.assertRaises(sqlite3.OperationalError):
            migration.apply(connection)
        self.assertFalse(connection.in_transaction)
        source = inspect.getsource(migration.apply)
        for forbidden in ("BEGIN", "COMMIT", "ROLLBACK", "executescript", "IF NOT EXISTS"):
            self.assertNotIn(forbidden, source)

    def test_runner_creates_exact_dedicated_schema_and_no_global_tables(self) -> None:
        connection = self._connection()
        apply_capture_schema_migrations(connection)
        self.assertEqual(get_applied_capture_schema_versions(connection), {1: migration.NAME})
        self.assertEqual(get_pending_capture_schema_migrations(connection), ())
        names = {
            row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        self.assertEqual(
            names,
            {
                "nar_official_response_capture_schema_migrations",
                "nar_official_response_bodies",
                "nar_official_response_captures",
            },
        )
        index_rows = connection.execute("PRAGMA index_list(nar_official_response_captures)").fetchall()
        evidence_indexes = [row for row in index_rows if row[1] == "ux_nar_official_response_captures_evidence"]
        self.assertEqual(len(evidence_indexes), 1)
        self.assertEqual(
            [row[2] for row in connection.execute("PRAGMA index_info(ux_nar_official_response_captures_evidence)")],
            ["canonical_source_url", "response_sha256", "observed_at_utc"],
        )
        self.assertEqual(connection.execute("PRAGMA foreign_keys").fetchone()[0], 1)
        self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(tuple(item.VERSION for item in MIGRATIONS), (8, 9, 10, 11, 12, 13, 14, 15))
        self.assertEqual(tuple(item.VERSION for item in CAPTURE_MIGRATIONS), (1,))
        columns = [row[1] for row in connection.execute("PRAGMA table_info(nar_official_response_captures)")]
        self.assertEqual(
            columns,
            [
                "capture_id", "schema_version", "page_kind", "canonical_source_url", "response_sha256", "charset",
                "requested_at_utc", "observed_at_utc", "stored_at_utc", "http_status", "content_type",
                "content_encoding", "http_date", "etag", "last_modified", "content_length",
            ],
        )
        foreign_keys = connection.execute("PRAGMA foreign_key_list(nar_official_response_captures)").fetchall()
        self.assertEqual([(row[2], row[3], row[4], row[5], row[6]) for row in foreign_keys], [
            ("nar_official_response_bodies", "response_sha256", "response_sha256", "RESTRICT", "RESTRICT"),
        ])

    def test_runner_is_idempotent_rejects_active_and_invalid_registry_state(self) -> None:
        connection = self._connection()
        apply_capture_schema_migrations(connection)
        apply_capture_schema_migrations(connection)
        connection.execute("BEGIN")
        with self.assertRaises(RuntimeError):
            apply_capture_schema_migrations(connection)
        connection.rollback()
        connection.execute("PRAGMA ignore_check_constraints=ON")
        connection.execute("INSERT INTO nar_official_response_capture_schema_migrations(version,name) VALUES(2,'future')")
        connection.commit()
        with self.assertRaises(RuntimeError):
            get_pending_capture_schema_migrations(connection)
        self.assertFalse(connection.in_transaction)

    def test_registry_and_migration_failure_roll_back(self) -> None:
        connection = self._connection()

        class Failing:
            VERSION = 1
            NAME = "failure"

            @staticmethod
            def apply(connection: sqlite3.Connection) -> None:
                connection.execute("CREATE TABLE should_rollback (id INTEGER)")
                raise RuntimeError("boom")

        with self.assertRaises(RuntimeError):
            apply_capture_schema_migrations(connection, (Failing,))
        self.assertFalse(connection.in_transaction)
        self.assertIsNone(connection.execute("SELECT 1 FROM sqlite_master WHERE name='should_rollback'").fetchone())
        self.assertIsNone(connection.execute("SELECT 1 FROM sqlite_master WHERE name='nar_official_response_capture_schema_migrations'").fetchone())
        with self.assertRaises(ValueError):
            get_pending_capture_schema_migrations(connection, (migration, migration))

    def test_unregistered_preexisting_capture_table_is_not_adopted(self) -> None:
        connection = self._connection()
        connection.execute("CREATE TABLE nar_official_response_bodies (wrong TEXT)")
        with self.assertRaises(sqlite3.OperationalError):
            apply_capture_schema_migrations(connection)
        self.assertFalse(connection.in_transaction)
        self.assertIsNone(
            connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='nar_official_response_capture_schema_migrations'",
            ).fetchone(),
        )
        self.assertEqual(connection.execute("SELECT sql FROM sqlite_master WHERE name='nar_official_response_bodies'").fetchone()[0], "CREATE TABLE nar_official_response_bodies (wrong TEXT)")

    def test_malformed_existing_registry_is_rejected_before_v001(self) -> None:
        connection = self._connection()
        malformed_sql = "CREATE TABLE nar_official_response_capture_schema_migrations (version INTEGER,name TEXT)"
        connection.execute(malformed_sql)
        with self.assertRaises(RuntimeError):
            apply_capture_schema_migrations(connection)
        with self.assertRaises(RuntimeError):
            get_applied_capture_schema_versions(connection)
        self.assertFalse(connection.in_transaction)
        names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertEqual(names, {"nar_official_response_capture_schema_migrations"})
        self.assertEqual(
            connection.execute("SELECT sql FROM sqlite_master WHERE name='nar_official_response_capture_schema_migrations'").fetchone()[0],
            malformed_sql,
        )

    def test_registry_name_mismatch_and_malformed_row_are_rejected(self) -> None:
        connection = self._connection()
        apply_capture_schema_migrations(connection)
        connection.execute(
            "UPDATE nar_official_response_capture_schema_migrations SET name='wrong-name' WHERE version=1",
        )
        connection.commit()
        with self.assertRaises(RuntimeError):
            get_pending_capture_schema_migrations(connection)
        connection = self._connection()
        apply_capture_schema_migrations(connection)
        connection.execute("PRAGMA ignore_check_constraints=ON")
        connection.execute(
            "INSERT INTO nar_official_response_capture_schema_migrations(version,name) VALUES(0,'')",
        )
        connection.commit()
        with self.assertRaises(RuntimeError):
            get_applied_capture_schema_versions(connection)
        self.assertFalse(connection.in_transaction)

    def test_runner_rollback_boundary_immediately_reraises(self) -> None:
        source = inspect.getsource(runner_module.apply_capture_schema_migrations)
        self.assertIn("except BaseException:", source)
        self.assertIn("connection.rollback()", source)
        self.assertIn("raise", source[source.index("except BaseException:"):])
        self.assertNotIn("scripts.migrations.runner", inspect.getsource(runner_module))
