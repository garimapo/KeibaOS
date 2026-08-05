"""SQLite schema tests for the v009 simulation bet-plan migration (:memory: only)."""

from __future__ import annotations

import sqlite3
from types import SimpleNamespace
import unittest

from scripts.migrations.runner import MIGRATIONS, apply_migrations, get_applied_versions
from scripts.migrations.versions import (
    v008_simulation_schema,
    v009_simulation_bet_plan_schema,
    v010_historical_input_snapshot_schema,
)


HASH = "a" * 64
CUTOFF = "2026-07-26T00:00:00.123456+00:00"
PLAN_TABLES = {
    "simulation_bet_plans",
    "simulation_bet_plan_bets",
    "simulation_bet_plan_bet_selections",
}
PLAN_TRIGGERS = {
    "sbpbs_entry_race_insert",
    "sbpbs_entry_race_update",
    "sbpb_plan_race_update",
}


class SimulationBetPlanMigrationTests(unittest.TestCase):
    def db(self) -> sqlite3.Connection:
        connection = sqlite3.connect(":memory:")
        connection.execute("CREATE TABLE races(id INTEGER PRIMARY KEY)")
        connection.execute("CREATE TABLE horses(id INTEGER PRIMARY KEY, race_id INTEGER)")
        connection.executemany("INSERT INTO races(id) VALUES(?)", ((1,), (2,)))
        connection.executemany("INSERT INTO horses(id,race_id) VALUES(?,?)", ((11, 1), (12, 1), (21, 2)))
        connection.commit()
        return connection

    def migrated(self) -> sqlite3.Connection:
        connection = self.db()
        apply_migrations(connection)
        return connection

    def plan(self, connection: sqlite3.Connection, **overrides: object) -> int:
        values: dict[str, object] = {
            "run_id": "run-1",
            "race_id": 1,
            "strategy_id": "strategy-1",
            "strategy_config_hash": HASH,
            "information_cutoff": CUTOFF,
            "allocation_policy_name": "fixed-stake",
            "allocation_policy_version": "1",
            "allocation_policy_config_hash": HASH,
            "budget_total_amount": 500,
        }
        values.update(overrides)
        columns = tuple(values)
        placeholders = ", ".join("?" for _ in columns)
        connection.execute(
            f"INSERT INTO simulation_bet_plans({', '.join(columns)}) VALUES({placeholders})",
            tuple(values[column] for column in columns),
        )
        return int(connection.execute("SELECT last_insert_rowid()").fetchone()[0])

    def bet(self, connection: sqlite3.Connection, plan_id: int, **overrides: object) -> int:
        values: dict[str, object] = {
            "plan_id": plan_id,
            "purchase_order": 0,
            "bet_type": "single",
            "stake": 100,
            "recommendation_rank": 0,
        }
        values.update(overrides)
        columns = tuple(values)
        placeholders = ", ".join("?" for _ in columns)
        connection.execute(
            f"INSERT INTO simulation_bet_plan_bets({', '.join(columns)}) VALUES({placeholders})",
            tuple(values[column] for column in columns),
        )
        return int(connection.execute("SELECT last_insert_rowid()").fetchone()[0])

    def selection(self, connection: sqlite3.Connection, bet_id: int, **overrides: object) -> None:
        values: dict[str, object] = {
            "bet_id": bet_id,
            "selection_order": 0,
            "race_entry_id": 11,
        }
        values.update(overrides)
        columns = tuple(values)
        placeholders = ", ".join("?" for _ in columns)
        connection.execute(
            f"INSERT INTO simulation_bet_plan_bet_selections({', '.join(columns)}) VALUES({placeholders})",
            tuple(values[column] for column in columns),
        )

    def test_v009_is_registered_after_v008_without_duplicate_version(self) -> None:
        self.assertEqual(tuple(migration.VERSION for migration in MIGRATIONS), (8, 9, 10))
        self.assertEqual(v009_simulation_bet_plan_schema.VERSION, 9)
        self.assertEqual(v009_simulation_bet_plan_schema.NAME, "v009_simulation_bet_plan_schema")
        self.assertEqual(sum(migration.VERSION == 9 for migration in MIGRATIONS), 1)
        self.assertEqual(v010_historical_input_snapshot_schema.VERSION, 10)
        self.assertEqual(v010_historical_input_snapshot_schema.NAME, "v010_historical_input_snapshot_schema")
        self.assertEqual(sum(migration.VERSION == 10 for migration in MIGRATIONS), 1)

    def test_fresh_database_applies_v008_and_v009_once(self) -> None:
        connection = self.migrated()
        self.assertEqual(
            get_applied_versions(connection),
            {8: "v008_simulation_schema", 9: "v009_simulation_bet_plan_schema", 10: "v010_historical_input_snapshot_schema"},
        )
        self.assertTrue(PLAN_TABLES <= {row[0] for row in connection.execute("SELECT name FROM sqlite_master")})
        self.assertTrue(PLAN_TRIGGERS <= {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='trigger'")})
        self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
        apply_migrations(connection)
        self.assertEqual(connection.execute("SELECT count(*) FROM schema_migrations WHERE version=9").fetchone()[0], 1)

    def test_v008_to_v009_upgrade_preserves_existing_rows(self) -> None:
        connection = self.db()
        apply_migrations(connection, (v008_simulation_schema,))
        connection.execute("INSERT INTO race_results VALUES(1,'void',NULL,?,'source',NULL)", (CUTOFF,))
        connection.commit()
        apply_migrations(connection)
        self.assertEqual(connection.execute("SELECT result_status FROM race_results WHERE race_id=1").fetchone()[0], "void")
        self.assertEqual(get_applied_versions(connection), {8: "v008_simulation_schema", 9: "v009_simulation_bet_plan_schema", 10: "v010_historical_input_snapshot_schema"})
        self.assertTrue(PLAN_TABLES <= {row[0] for row in connection.execute("SELECT name FROM sqlite_master")})

    def test_schema_columns_primary_keys_and_defaults(self) -> None:
        connection = self.migrated()
        expected = {
            "simulation_bet_plans": (
                ("id", "INTEGER", 0, 1, None), ("run_id", "TEXT", 1, 0, None),
                ("race_id", "INTEGER", 1, 0, None), ("strategy_id", "TEXT", 1, 0, None),
                ("strategy_config_hash", "TEXT", 1, 0, None), ("information_cutoff", "TEXT", 1, 0, None),
                ("allocation_policy_name", "TEXT", 1, 0, None), ("allocation_policy_version", "TEXT", 1, 0, None),
                ("allocation_policy_config_hash", "TEXT", 1, 0, None), ("budget_total_amount", "INTEGER", 1, 0, None),
            ),
            "simulation_bet_plan_bets": (
                ("id", "INTEGER", 0, 1, None), ("plan_id", "INTEGER", 1, 0, None),
                ("purchase_order", "INTEGER", 1, 0, None), ("bet_type", "TEXT", 1, 0, None),
                ("stake", "INTEGER", 1, 0, None), ("recommendation_rank", "INTEGER", 1, 0, None),
            ),
            "simulation_bet_plan_bet_selections": (
                ("bet_id", "INTEGER", 1, 1, None), ("selection_order", "INTEGER", 1, 2, None),
                ("race_entry_id", "INTEGER", 1, 0, None),
            ),
        }
        for table, columns in expected.items():
            with self.subTest(table=table):
                actual = tuple((row[1], row[2], row[3], row[5], row[4]) for row in connection.execute(f"PRAGMA table_info({table})"))
                self.assertEqual(actual, columns)

    def test_header_natural_identity_rejects_policy_or_budget_variants(self) -> None:
        connection = self.migrated()
        self.plan(connection)
        for overrides in (
            {"allocation_policy_name": "other"},
            {"allocation_policy_config_hash": "b" * 64},
            {"budget_total_amount": 0},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.plan(connection, **overrides)

    def test_each_natural_identity_component_can_distinguish_a_header(self) -> None:
        connection = self.migrated()
        self.plan(connection)
        variants = (
            {"run_id": "run-2"}, {"race_id": 2}, {"strategy_id": "strategy-2"},
            {"strategy_config_hash": "b" * 64}, {"information_cutoff": "2026-07-26T00:00:01+00:00"},
        )
        for index, overrides in enumerate(variants, start=1):
            with self.subTest(overrides=overrides):
                values = {"run_id": f"run-{index + 1}"}
                values.update(overrides)
                self.plan(connection, **values)
        self.assertEqual(connection.execute("SELECT count(*) FROM simulation_bet_plans").fetchone()[0], 6)

    def test_budget_check_accepts_only_nonnegative_hundred_yen_amounts(self) -> None:
        connection = self.migrated()
        for amount in (0, 100, 500):
            with self.subTest(amount=amount):
                self.plan(connection, run_id=f"accepted-{amount}", budget_total_amount=amount)
        for amount in (-100, 1, 50, 150):
            with self.subTest(amount=amount):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.plan(connection, run_id=f"rejected-{amount}", budget_total_amount=amount)

    def test_empty_plan_is_a_header_without_children(self) -> None:
        connection = self.migrated()
        first = self.plan(connection, budget_total_amount=0)
        second = self.plan(connection, run_id="positive-empty", budget_total_amount=500)
        self.assertEqual(connection.execute("SELECT count(*) FROM simulation_bet_plans WHERE id IN (?,?)", (first, second)).fetchone()[0], 2)
        self.assertEqual(connection.execute("SELECT count(*) FROM simulation_bet_plan_bets").fetchone()[0], 0)
        self.assertEqual(connection.execute("SELECT count(*) FROM simulation_bet_plan_bet_selections").fetchone()[0], 0)

    def test_purchase_order_checks_uniqueness_and_allows_gaps_per_plan(self) -> None:
        connection = self.migrated()
        plan_one, plan_two = self.plan(connection), self.plan(connection, run_id="run-2")
        self.bet(connection, plan_one, purchase_order=0)
        self.bet(connection, plan_one, purchase_order=2)
        self.bet(connection, plan_two, purchase_order=0)
        with self.assertRaises(sqlite3.IntegrityError):
            self.bet(connection, plan_one, purchase_order=-1)
        with self.assertRaises(sqlite3.IntegrityError):
            self.bet(connection, plan_one, purchase_order=0)

    def test_stake_and_rank_checks_match_domain_range(self) -> None:
        connection = self.migrated()
        plan_id = self.plan(connection)
        self.bet(connection, plan_id, purchase_order=0, stake=100, recommendation_rank=0)
        self.bet(connection, plan_id, purchase_order=1, stake=500, recommendation_rank=0)
        for stake in (0, -100, 1, 50, 150):
            with self.subTest(stake=stake):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.bet(connection, plan_id, purchase_order=10 + stake, stake=stake)
        with self.assertRaises(sqlite3.IntegrityError):
            self.bet(connection, plan_id, purchase_order=99, recommendation_rank=-1)

    def test_selection_order_and_entry_uniqueness_allow_gaps_and_cross_bet_reuse(self) -> None:
        connection = self.migrated()
        plan_id = self.plan(connection)
        first = self.bet(connection, plan_id, purchase_order=0)
        second = self.bet(connection, plan_id, purchase_order=1)
        self.selection(connection, first, selection_order=0, race_entry_id=11)
        self.selection(connection, first, selection_order=2, race_entry_id=12)
        self.selection(connection, second, selection_order=0, race_entry_id=11)
        with self.assertRaises(sqlite3.IntegrityError):
            self.selection(connection, first, selection_order=-1, race_entry_id=12)
        with self.assertRaises(sqlite3.IntegrityError):
            self.selection(connection, first, selection_order=0, race_entry_id=12)
        with self.assertRaises(sqlite3.IntegrityError):
            self.selection(connection, first, selection_order=1, race_entry_id=11)

    def test_foreign_keys_are_enabled_and_reject_missing_relations(self) -> None:
        connection = self.migrated()
        self.assertEqual(connection.execute("PRAGMA foreign_keys").fetchone()[0], 1)
        with self.assertRaises(sqlite3.IntegrityError):
            self.plan(connection, race_id=999)
        with self.assertRaises(sqlite3.IntegrityError):
            self.bet(connection, 999)
        plan_id = self.plan(connection)
        with self.assertRaises(sqlite3.IntegrityError):
            self.selection(connection, 999)
        bet_id = self.bet(connection, plan_id)
        with self.assertRaises(sqlite3.IntegrityError):
            self.selection(connection, bet_id, race_entry_id=999)

    def test_race_membership_triggers_reject_insert_and_update_without_partial_write(self) -> None:
        connection = self.migrated()
        plan_one = self.plan(connection, race_id=1)
        plan_two = self.plan(connection, run_id="race-two", race_id=2)
        bet_one = self.bet(connection, plan_one)
        self.selection(connection, bet_one, race_entry_id=11)
        with self.assertRaises(sqlite3.IntegrityError):
            self.selection(connection, bet_one, selection_order=1, race_entry_id=21)
        with self.assertRaises(sqlite3.IntegrityError):
            connection.execute("UPDATE simulation_bet_plan_bet_selections SET race_entry_id=21 WHERE bet_id=? AND selection_order=0", (bet_one,))
        with self.assertRaises(sqlite3.IntegrityError):
            connection.execute("UPDATE simulation_bet_plan_bets SET plan_id=? WHERE id=?", (plan_two, bet_one))
        self.assertEqual(connection.execute("SELECT race_entry_id FROM simulation_bet_plan_bet_selections WHERE bet_id=?", (bet_one,)).fetchone()[0], 11)
        self.assertEqual(connection.execute("SELECT plan_id FROM simulation_bet_plan_bets WHERE id=?", (bet_one,)).fetchone()[0], plan_one)

    def test_cascades_remove_bets_and_selections_only_from_deleted_parent(self) -> None:
        connection = self.migrated()
        plan_id = self.plan(connection)
        bet_id = self.bet(connection, plan_id)
        self.selection(connection, bet_id)
        connection.execute("DELETE FROM simulation_bet_plan_bets WHERE id=?", (bet_id,))
        self.assertEqual(connection.execute("SELECT count(*) FROM simulation_bet_plan_bet_selections").fetchone()[0], 0)
        bet_id = self.bet(connection, plan_id)
        self.selection(connection, bet_id)
        connection.execute("DELETE FROM simulation_bet_plans WHERE id=?", (plan_id,))
        self.assertEqual(connection.execute("SELECT count(*) FROM simulation_bet_plan_bets").fetchone()[0], 0)
        self.assertEqual(connection.execute("SELECT count(*) FROM simulation_bet_plan_bet_selections").fetchone()[0], 0)

    def test_bet_type_and_datetime_hash_text_are_preserved_without_defaults_or_normalization(self) -> None:
        connection = self.migrated()
        plan_id = self.plan(
            connection,
            strategy_config_hash="A" * 64,
            information_cutoff="not-a-date",
            allocation_policy_config_hash="B" * 64,
        )
        for order, bet_type in enumerate(("single", "quinella", "wide", "trio", "future-type")):
            self.bet(connection, plan_id, purchase_order=order, bet_type=bet_type)
        header = connection.execute(
            "SELECT strategy_config_hash,information_cutoff,allocation_policy_config_hash FROM simulation_bet_plans WHERE id=?",
            (plan_id,),
        ).fetchone()
        self.assertEqual(header, ("A" * 64, "not-a-date", "B" * 64))
        self.assertEqual(
            tuple(row[0] for row in connection.execute("SELECT bet_type FROM simulation_bet_plan_bets ORDER BY purchase_order")),
            ("single", "quinella", "wide", "trio", "future-type"),
        )
        for table in PLAN_TABLES:
            self.assertTrue(all(row[4] is None for row in connection.execute(f"PRAGMA table_info({table})")))

    def test_v009_failure_rolls_back_all_its_schema_and_version(self) -> None:
        connection = self.db()

        def fail_after_v009(target: sqlite3.Connection) -> None:
            v009_simulation_bet_plan_schema.apply(target)
            target.execute("INVALID SQL")

        failing_v009 = SimpleNamespace(VERSION=9, NAME=v009_simulation_bet_plan_schema.NAME, apply=fail_after_v009)
        with self.assertRaises(sqlite3.OperationalError):
            apply_migrations(connection, (v008_simulation_schema, failing_v009))
        names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master")}
        self.assertTrue(PLAN_TABLES.isdisjoint(names))
        self.assertEqual(get_applied_versions(connection), {8: "v008_simulation_schema"})
        self.assertFalse(connection.in_transaction)

    def test_v009_adds_no_redundant_explicit_indexes(self) -> None:
        connection = self.migrated()
        explicit_indexes = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name IN (?, ?, ?)", tuple(PLAN_TABLES))
            if not row[0].startswith("sqlite_autoindex")
        }
        self.assertEqual(explicit_indexes, set())


if __name__ == "__main__":
    unittest.main()
