from __future__ import annotations

import inspect
import sqlite3
import unittest

from scripts.simulation import nar_market_odds_capture_archive_migration as migration
from scripts.simulation.sqlite_nar_market_odds_capture_archive import (
    SQLiteNARMarketOddsCaptureArchive,
)
from scripts.simulation.repositories.errors import RepositoryDataIntegrityError


class NARMarketOddsCaptureArchiveMigrationTests(unittest.TestCase):
    def connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(":memory:")
        self.addCleanup(connection.close)
        return connection

    def test_exact_identity_fresh_schema_and_foreign_keys(self) -> None:
        connection = self.connection()
        self.assertEqual(migration.VERSION, 1)
        self.assertEqual(migration.NAME, "v001_nar_market_odds_capture_archive_schema")
        migration.apply_nar_market_odds_capture_archive_migrations(connection)
        migration.require_nar_market_odds_capture_archive_schema(connection)
        objects = {
            (row[0], row[1])
            for row in connection.execute(
                "SELECT name,type FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
            )
        }
        self.assertEqual(
            objects,
            {
                ("nar_market_odds_capture_archive_schema_migrations", "table"),
                ("nar_market_odds_response_bodies", "table"),
                ("nar_market_odds_response_captures", "table"),
                ("ux_nar_market_odds_response_captures_evidence", "index"),
            },
        )
        self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(connection.execute("PRAGMA foreign_keys").fetchone(), (1,))

    def test_pending_applied_and_repeated_runner_are_exact(self) -> None:
        connection = self.connection()
        self.assertEqual(
            migration.get_applied_nar_market_odds_capture_archive_schema_versions(connection),
            {},
        )
        self.assertEqual(
            migration.get_pending_nar_market_odds_capture_archive_migrations(connection),
            (migration.apply,),
        )
        migration.apply_nar_market_odds_capture_archive_migrations(connection)
        migration.apply_nar_market_odds_capture_archive_migrations(connection)
        self.assertEqual(
            migration.get_applied_nar_market_odds_capture_archive_schema_versions(connection),
            {1: migration.NAME},
        )
        self.assertEqual(
            migration.get_pending_nar_market_odds_capture_archive_migrations(connection),
            (),
        )

    def test_direct_apply_is_transaction_neutral_and_runner_rolls_back(self) -> None:
        direct = self.connection()
        migration.apply(direct)
        self.assertFalse(direct.in_transaction)
        self.assertNotIn(
            "nar_market_odds_capture_archive_schema_migrations",
            {row[0] for row in direct.execute("SELECT name FROM sqlite_master")},
        )

        connection = self.connection()
        original = migration.apply

        def failing(value: sqlite3.Connection) -> None:
            original(value)
            raise RuntimeError("stop")

        migration.apply = failing
        try:
            with self.assertRaisesRegex(RuntimeError, "stop"):
                migration.apply_nar_market_odds_capture_archive_migrations(connection)
        finally:
            migration.apply = original
        self.assertFalse(connection.in_transaction)
        self.assertEqual(
            connection.execute(
                "SELECT name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
            ).fetchall(),
            [],
        )

    def test_exact_connection_and_active_transaction_are_rejected(self) -> None:
        for function in (
            migration.apply,
            migration.get_applied_nar_market_odds_capture_archive_schema_versions,
            migration.get_pending_nar_market_odds_capture_archive_migrations,
            migration.apply_nar_market_odds_capture_archive_migrations,
            migration.require_nar_market_odds_capture_archive_schema,
        ):
            with self.subTest(function=function.__name__):
                with self.assertRaises(ValueError):
                    function(object())  # type: ignore[arg-type]
        connection = self.connection()
        connection.execute("BEGIN")
        with self.assertRaises(RuntimeError):
            migration.apply_nar_market_odds_capture_archive_migrations(connection)
        connection.rollback()

    def test_unknown_future_name_drift_and_unexpected_objects_fail_closed(self) -> None:
        connection = self.connection()
        migration.apply_nar_market_odds_capture_archive_migrations(connection)
        connection.execute(
            "INSERT INTO nar_market_odds_capture_archive_schema_migrations(version,name) "
            "VALUES(2,'future')"
        )
        connection.commit()
        with self.assertRaises(RuntimeError):
            migration.require_nar_market_odds_capture_archive_schema(connection)

        connection = self.connection()
        migration.apply_nar_market_odds_capture_archive_migrations(connection)
        connection.execute(
            "UPDATE nar_market_odds_capture_archive_schema_migrations "
            "SET name='wrong' WHERE version=1"
        )
        connection.commit()
        with self.assertRaises(RuntimeError):
            migration.require_nar_market_odds_capture_archive_schema(connection)

        connection = self.connection()
        migration.apply_nar_market_odds_capture_archive_migrations(connection)
        connection.execute("CREATE TABLE unrelated(value TEXT)")
        connection.commit()
        with self.assertRaises(RuntimeError):
            migration.require_nar_market_odds_capture_archive_schema(connection)

    def test_partial_registry_or_foreign_schema_is_never_adopted(self) -> None:
        for ddl in (
            "CREATE TABLE nar_market_odds_response_bodies(wrong TEXT)",
            "CREATE TABLE unrelated(value TEXT)",
            "CREATE TABLE nar_market_odds_capture_archive_schema_migrations(version INTEGER)",
        ):
            with self.subTest(ddl=ddl):
                connection = sqlite3.connect(":memory:")
                self.addCleanup(connection.close)
                connection.execute(ddl)
                with self.assertRaises(RuntimeError):
                    migration.apply_nar_market_odds_capture_archive_migrations(connection)
                self.assertFalse(connection.in_transaction)

    def test_every_material_schema_drift_is_rejected(self) -> None:
        mutations = {
            "body columns": lambda c: c.execute(
                "ALTER TABLE nar_market_odds_response_bodies ADD COLUMN extra TEXT"
            ),
            "capture columns": lambda c: c.execute(
                "ALTER TABLE nar_market_odds_response_captures ADD COLUMN extra TEXT"
            ),
            "index columns": lambda c: (
                c.execute("DROP INDEX ux_nar_market_odds_response_captures_evidence"),
                c.execute(
                    "CREATE UNIQUE INDEX ux_nar_market_odds_response_captures_evidence "
                    "ON nar_market_odds_response_captures(response_sha256,request_identity_sha256,"
                    "requested_at_utc,observed_at_utc,captured_at_utc)"
                ),
            ),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                connection = sqlite3.connect(":memory:")
                self.addCleanup(connection.close)
                migration.apply_nar_market_odds_capture_archive_migrations(connection)
                mutate(connection)
                connection.commit()
                with self.assertRaises(RuntimeError):
                    migration.require_nar_market_odds_capture_archive_schema(connection)

        for name, old, new in (
            ("missing check", "AND byte_length = length(response_body)", ""),
            ("missing without rowid", ") WITHOUT ROWID", ")"),
            ("changed foreign key action", "ON UPDATE RESTRICT ON DELETE RESTRICT", "ON UPDATE CASCADE ON DELETE RESTRICT"),
            ("changed semantic literal", "organization = 'NAR'", "organization = 'nar'"),
        ):
            with self.subTest(name=name):
                connection = sqlite3.connect(":memory:")
                self.addCleanup(connection.close)
                connection.execute(migration._REGISTRY_DDL)  # type: ignore[attr-defined]
                body_ddl = migration._BODY_DDL  # type: ignore[attr-defined]
                capture_ddl = migration._CAPTURE_DDL  # type: ignore[attr-defined]
                if name == "missing check":
                    body_ddl = body_ddl.replace(old, new)
                else:
                    capture_ddl = capture_ddl.replace(old, new)
                connection.execute(body_ddl)
                connection.execute(capture_ddl)
                connection.execute(migration._INDEX_DDL)  # type: ignore[attr-defined]
                connection.execute(
                    "INSERT INTO nar_market_odds_capture_archive_schema_migrations(version,name) "
                    "VALUES(1,?)",
                    (migration.NAME,),
                )
                connection.commit()
                with self.assertRaises(RuntimeError):
                    migration.require_nar_market_odds_capture_archive_schema(connection)

    def test_repository_requires_schema_without_migrating_or_repairing(self) -> None:
        connection = self.connection()
        with self.assertRaises(RepositoryDataIntegrityError):
            SQLiteNARMarketOddsCaptureArchive(connection=connection)
        self.assertEqual(
            connection.execute(
                "SELECT name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
            ).fetchall(),
            [],
        )
        constructor = inspect.getsource(SQLiteNARMarketOddsCaptureArchive.__init__)
        self.assertNotIn("apply_nar_market", constructor)

    def test_schema_has_no_clock_backfill_or_main_registry_dependency(self) -> None:
        source = inspect.getsource(migration)
        for forbidden in (
            "CURRENT_TIMESTAMP",
            "datetime.now",
            "datetime.utcnow",
            "scripts.migrations.runner",
            "seed",
            "backfill",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
