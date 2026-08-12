from __future__ import annotations

import sqlite3
import unittest

from scripts.simulation.jra_official_response_capture_migration import NAME, VERSION, apply
from scripts.simulation.jra_official_response_capture_migration_runner import apply_jra_capture_schema_migrations, get_applied_jra_capture_schema_versions


class JRAMigrationTests(unittest.TestCase):
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
