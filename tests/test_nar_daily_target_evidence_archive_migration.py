from __future__ import annotations

import inspect
import sqlite3
import unittest

from scripts.migrations.runner import MIGRATIONS
from scripts.simulation import nar_daily_target_evidence_archive_migration as migration
from scripts.simulation.nar_official_response_capture_migration_runner import CAPTURE_MIGRATIONS
from scripts.simulation.sqlite_nar_daily_target_evidence_archive import (
    SQLiteNARDailyTargetEvidenceArchive,
)
from scripts.simulation.repositories.errors import RepositoryDataIntegrityError


class NARDailyTargetEvidenceArchiveMigrationTests(unittest.TestCase):
    def connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(":memory:")
        self.addCleanup(connection.close)
        return connection

    def test_fresh_migration_creates_exact_v1_schema(self) -> None:
        connection = self.connection()
        migration.apply_nar_daily_target_evidence_archive_migrations(connection)
        migration.require_nar_daily_target_evidence_archive_schema(connection)
        names = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
            )
        }
        self.assertEqual(
            names,
            {
                "nar_daily_target_evidence_archive_schema_migrations",
                "nar_daily_target_evidence_bodies",
                "nar_daily_target_supplier_captures",
                "nar_daily_target_response_captures",
                "ux_nar_daily_target_supplier_captures_evidence",
                "ux_nar_daily_target_response_captures_evidence",
            },
        )
        self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_runner_is_idempotent_and_reports_exact_versions(self) -> None:
        connection = self.connection()
        self.assertEqual(
            migration.get_applied_nar_daily_target_evidence_archive_schema_versions(connection),
            {},
        )
        self.assertEqual(
            migration.get_pending_nar_daily_target_evidence_archive_migrations(connection),
            (migration.apply,),
        )
        migration.apply_nar_daily_target_evidence_archive_migrations(connection)
        migration.apply_nar_daily_target_evidence_archive_migrations(connection)
        self.assertEqual(
            migration.get_applied_nar_daily_target_evidence_archive_schema_versions(connection),
            {1: migration.NAME},
        )
        self.assertEqual(
            migration.get_pending_nar_daily_target_evidence_archive_migrations(connection),
            (),
        )

    def test_direct_apply_is_transaction_neutral_and_runner_owns_rollback(self) -> None:
        direct = self.connection()
        migration.apply(direct)
        self.assertFalse(direct.in_transaction)
        with self.assertRaises(sqlite3.OperationalError):
            migration.apply(direct)
        self.assertFalse(direct.in_transaction)

        connection = self.connection()
        original = migration.apply

        def failing(value: sqlite3.Connection) -> None:
            original(value)
            raise RuntimeError("stop")

        migration.apply = failing
        try:
            with self.assertRaisesRegex(RuntimeError, "stop"):
                migration.apply_nar_daily_target_evidence_archive_migrations(connection)
        finally:
            migration.apply = original
        self.assertFalse(connection.in_transaction)
        self.assertEqual(
            connection.execute(
                "SELECT name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
            ).fetchall(),
            [],
        )

    def test_incompatible_partial_or_foreign_schema_fails_closed(self) -> None:
        for ddl in (
            "CREATE TABLE nar_daily_target_evidence_bodies (wrong TEXT)",
            "CREATE TABLE races (id INTEGER PRIMARY KEY)",
            "CREATE TABLE nar_official_response_capture_schema_migrations (version INTEGER)",
            "CREATE TABLE jra_official_response_capture_schema_migrations (version INTEGER)",
        ):
            with self.subTest(ddl=ddl):
                connection = sqlite3.connect(":memory:")
                self.addCleanup(connection.close)
                connection.execute(ddl)
                with self.assertRaises(RuntimeError):
                    migration.apply_nar_daily_target_evidence_archive_migrations(connection)
                self.assertFalse(connection.in_transaction)

    def test_registry_drift_unknown_version_and_schema_drift_fail_closed(self) -> None:
        connection = self.connection()
        migration.apply_nar_daily_target_evidence_archive_migrations(connection)
        connection.execute(
            "UPDATE nar_daily_target_evidence_archive_schema_migrations SET name='wrong' WHERE version=1"
        )
        connection.commit()
        with self.assertRaises(RuntimeError):
            migration.require_nar_daily_target_evidence_archive_schema(connection)

        connection = self.connection()
        migration.apply_nar_daily_target_evidence_archive_migrations(connection)
        connection.execute("PRAGMA ignore_check_constraints=ON")
        connection.execute(
            "INSERT INTO nar_daily_target_evidence_archive_schema_migrations(version,name) VALUES(2,'future')"
        )
        connection.commit()
        with self.assertRaises(RuntimeError):
            migration.get_pending_nar_daily_target_evidence_archive_migrations(connection)

        connection = self.connection()
        migration.apply_nar_daily_target_evidence_archive_migrations(connection)
        connection.execute("CREATE TABLE unexpected (id INTEGER)")
        with self.assertRaises(RuntimeError):
            migration.require_nar_daily_target_evidence_archive_schema(connection)

    def test_repository_constructor_never_migrates(self) -> None:
        connection = self.connection()
        with self.assertRaises(RepositoryDataIntegrityError):
            SQLiteNARDailyTargetEvidenceArchive(connection=connection)
        self.assertEqual(
            connection.execute(
                "SELECT name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
            ).fetchall(),
            [],
        )

    def test_migration_is_isolated_from_existing_registries(self) -> None:
        self.assertNotIn(migration, MIGRATIONS)
        self.assertNotIn(migration, CAPTURE_MIGRATIONS)
        source = inspect.getsource(migration)
        self.assertNotIn("scripts.migrations.runner", source)
        self.assertNotIn("nar_official_response_capture_migration", source)
        self.assertNotIn("jra_official_response_capture_migration", source)

    def test_migration_has_no_network_clock_or_implicit_time(self) -> None:
        source = inspect.getsource(migration)
        for forbidden in (
            "requests",
            "httpx",
            "urllib.request",
            "urlopen",
            "datetime.now",
            "datetime.utcnow",
            "time.time",
            "CURRENT_TIMESTAMP",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
