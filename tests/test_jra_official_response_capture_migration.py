from __future__ import annotations

import sqlite3
import unittest

from scripts.simulation.jra_official_response_capture_migration import NAME, VERSION, apply
from scripts.simulation.jra_official_response_capture_migration_runner import apply_jra_capture_schema_migrations, get_applied_jra_capture_schema_versions


class JRAMigrationTests(unittest.TestCase):
    _REGISTRY = "jra_official_response_capture_schema_migrations"

    def _reject_registry(self, ddl: str) -> None:
        c = sqlite3.connect(":memory:")
        c.execute(ddl)
        c.commit()
        with self.assertRaises(RuntimeError):
            apply_jra_capture_schema_migrations(c)
        self.assertFalse(c.in_transaction)
        self.assertIsNone(c.execute("SELECT 1 FROM sqlite_master WHERE name='jra_official_response_bodies'").fetchone())

    def test_dedicated_v001_fresh_and_idempotent(self):
        c = sqlite3.connect(":memory:")
        apply_jra_capture_schema_migrations(c)
        self.assertEqual(get_applied_jra_capture_schema_versions(c), {VERSION: NAME})
        self.assertEqual({r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}, {"jra_official_response_capture_schema_migrations", "jra_official_response_bodies", "jra_official_response_captures"})
        apply_jra_capture_schema_migrations(c)
        self.assertFalse(c.in_transaction)
        self.assertIsNone(c.execute("SELECT 1 FROM sqlite_master WHERE name='schema_migrations'").fetchone())

    def test_apply_is_transaction_neutral_and_bad_registry_fails(self):
        c = sqlite3.connect(":memory:")
        apply(c)
        self.assertFalse(c.in_transaction)
        c2 = sqlite3.connect(":memory:")
        c2.execute("CREATE TABLE jra_official_response_capture_schema_migrations(version INTEGER, name TEXT)")
        with self.assertRaises(RuntimeError):
            apply_jra_capture_schema_migrations(c2)
        self.assertIsNone(c2.execute("SELECT 1 FROM sqlite_master WHERE name='jra_official_response_bodies'").fetchone())

    def test_exact_preexisting_registry_is_accepted(self):
        c = sqlite3.connect(":memory:")
        c.execute("""CREATE TABLE jra_official_response_capture_schema_migrations (
            version INTEGER PRIMARY KEY CHECK(typeof(version)='integer' AND version>0),
            name TEXT NOT NULL UNIQUE CHECK(typeof(name)='text' AND length(name)>0)
        ) WITHOUT ROWID""")
        c.commit()
        apply_jra_capture_schema_migrations(c)
        self.assertEqual(get_applied_jra_capture_schema_versions(c), {1: NAME})

    def test_weakened_registry_constraints_and_extra_columns_fail_closed(self):
        variants = (
            "CREATE TABLE jra_official_response_capture_schema_migrations(version INTEGER PRIMARY KEY CHECK(typeof(version)='integer'),name TEXT NOT NULL UNIQUE CHECK(typeof(name)='text' AND length(name)>0)) WITHOUT ROWID",
            "CREATE TABLE jra_official_response_capture_schema_migrations(version INTEGER PRIMARY KEY CHECK(version>0),name TEXT NOT NULL UNIQUE CHECK(typeof(name)='text' AND length(name)>0)) WITHOUT ROWID",
            "CREATE TABLE jra_official_response_capture_schema_migrations(version INTEGER PRIMARY KEY CHECK(typeof(version)='integer' AND version>0),name TEXT NOT NULL CHECK(typeof(name)='text' AND length(name)>0)) WITHOUT ROWID",
            "CREATE TABLE jra_official_response_capture_schema_migrations(version INTEGER PRIMARY KEY CHECK(typeof(version)='integer' AND version>0),name TEXT NOT NULL UNIQUE CHECK(typeof(name)='text')) WITHOUT ROWID",
            "CREATE TABLE jra_official_response_capture_schema_migrations(version INTEGER PRIMARY KEY CHECK(typeof(version)='integer' AND version>0),name TEXT NOT NULL UNIQUE CHECK(length(name)>0)) WITHOUT ROWID",
            "CREATE TABLE jra_official_response_capture_schema_migrations(version INTEGER PRIMARY KEY CHECK(typeof(version)='integer' AND version>0),name TEXT NOT NULL UNIQUE CHECK(typeof(name)='text' AND length(name)>0),extra TEXT) WITHOUT ROWID",
            "CREATE TABLE jra_official_response_capture_schema_migrations(version INTEGER PRIMARY KEY CHECK(typeof(version)='integer' AND version>0),name TEXT NOT NULL UNIQUE CHECK(typeof(name)='text' AND length(name)>0))",
        )
        for ddl in variants:
            with self.subTest(ddl=ddl):
                self._reject_registry(ddl)

    def test_registered_version_name_and_malformed_rows_fail_closed(self):
        for version, name, ignore in ((1, "wrong", False), (2, "future", False), (0, NAME, True), (1, "", True)):
            with self.subTest(version=version, name=name):
                c = sqlite3.connect(":memory:")
                apply_jra_capture_schema_migrations(c)
                if ignore:
                    c.execute("PRAGMA ignore_check_constraints=ON")
                c.execute("DELETE FROM jra_official_response_capture_schema_migrations")
                c.execute("INSERT INTO jra_official_response_capture_schema_migrations(version,name) VALUES(?,?)", (version, name))
                c.commit()
                if ignore:
                    c.execute("PRAGMA ignore_check_constraints=OFF")
                with self.assertRaises(RuntimeError):
                    apply_jra_capture_schema_migrations(c)
                self.assertFalse(c.in_transaction)

    def test_unregistered_capture_tables_are_not_adopted_or_repaired(self):
        for table in ("jra_official_response_bodies", "jra_official_response_captures"):
            with self.subTest(table=table):
                c = sqlite3.connect(":memory:")
                c.execute(f"CREATE TABLE {table}(value TEXT)")
                c.commit()
                with self.assertRaises(RuntimeError):
                    apply_jra_capture_schema_migrations(c)
                self.assertFalse(c.in_transaction)
                self.assertIsNotNone(c.execute("SELECT 1 FROM sqlite_master WHERE name=?", (table,)).fetchone())
                self.assertIsNone(c.execute("SELECT 1 FROM sqlite_master WHERE name=?", (self._REGISTRY,)).fetchone())
