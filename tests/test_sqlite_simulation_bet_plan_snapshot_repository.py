"""Tests for the v009 SQLite simulation bet-plan snapshot repository (:memory: by default)."""

from __future__ import annotations

from datetime import UTC, datetime
import inspect
from pathlib import Path
import sqlite3
import tempfile
from typing import get_type_hints
import unittest
from zoneinfo import ZoneInfo

from scripts.prediction.allocation_policy import AllocationPolicyIdentity
from scripts.migrations.runner import apply_migrations
from scripts.simulation.bet_plan_identity import SimulationBetPlanIdentity
from scripts.simulation.bet_plan_snapshot import SimulationBetPlanSnapshot
from scripts.simulation.bet_plan_snapshot_repository import (
    SimulationBetPlanSnapshotRepository,
    SimulationBetPlanSnapshotSource,
)
from scripts.simulation.models import SimulationBet
from scripts.simulation.repositories.errors import (
    RepositoryConflictError,
    RepositoryDataIntegrityError,
    RepositoryValidationError,
)
from scripts.simulation.repositories.sqlite_bet_plan_snapshot_repository import SQLiteSimulationBetPlanSnapshotRepository
from scripts.simulation.stake_allocation import BetStakeBudget


HASH = "a" * 64


def identity(
    *,
    run_id: str = "run-1",
    race_id: int = 1,
    strategy_id: str = "strategy-1",
    strategy_config_hash: str = HASH,
    information_cutoff: datetime | None = None,
) -> SimulationBetPlanIdentity:
    return SimulationBetPlanIdentity(
        run_id=run_id,
        race_id=race_id,
        strategy_id=strategy_id,
        strategy_config_hash=strategy_config_hash,
        information_cutoff=information_cutoff or datetime(2026, 7, 26, 9, 0, 0, 123456, tzinfo=UTC),
    )


def policy(*, name: str = "fixed-stake", version: str = "1", config_hash: str = HASH) -> AllocationPolicyIdentity:
    return AllocationPolicyIdentity(name, version, config_hash)


def bet(
    plan_identity: SimulationBetPlanIdentity,
    bet_type: str,
    entries: tuple[int, ...],
    *,
    stake: int = 100,
    rank: int = 0,
) -> SimulationBet:
    return SimulationBet(
        race_id=plan_identity.race_id,
        strategy_id=plan_identity.strategy_id,
        bet_type=bet_type,
        race_entry_ids=entries,
        stake=stake,
        recommendation_rank=rank,
        placed_at_cutoff=plan_identity.information_cutoff,
    )


def snapshot(
    plan_identity: SimulationBetPlanIdentity | None = None,
    *,
    policy_identity: AllocationPolicyIdentity | None = None,
    budget: int = 1000,
    bets: tuple[SimulationBet, ...] = (),
) -> SimulationBetPlanSnapshot:
    return SimulationBetPlanSnapshot(
        identity=plan_identity or identity(),
        policy_identity=policy_identity or policy(),
        budget=BetStakeBudget(budget),
        bets=bets,
    )


class SQLiteSimulationBetPlanSnapshotRepositoryTests(unittest.TestCase):
    def connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(":memory:")
        connection.execute("CREATE TABLE races(id INTEGER PRIMARY KEY)")
        connection.execute("CREATE TABLE horses(id INTEGER PRIMARY KEY,race_id INTEGER)")
        connection.executemany("INSERT INTO races(id) VALUES(?)", ((1,), (2,)))
        connection.executemany("INSERT INTO horses(id,race_id) VALUES(?,?)", ((11, 1), (12, 1), (13, 1), (21, 2)))
        connection.commit()
        apply_migrations(connection)
        return connection

    def repository(self) -> tuple[sqlite3.Connection, SQLiteSimulationBetPlanSnapshotRepository]:
        connection = self.connection()
        return connection, SQLiteSimulationBetPlanSnapshotRepository(connection=connection)

    @staticmethod
    def multi_snapshot(plan_identity: SimulationBetPlanIdentity | None = None) -> SimulationBetPlanSnapshot:
        plan_identity = plan_identity or identity()
        return snapshot(
            plan_identity,
            budget=1000,
            bets=(
                bet(plan_identity, "単勝", (11,), stake=100, rank=1),
                bet(plan_identity, "馬連", (11, 12), stake=200, rank=2),
                bet(plan_identity, "ワイド", (12, 13), stake=300, rank=2),
                bet(plan_identity, "3連複", (11, 12, 13), stake=400, rank=3),
            ),
        )

    def test_constructor_keeps_the_injected_connection_without_mutating_settings(self) -> None:
        connection = self.connection()
        connection.row_factory = sqlite3.Row
        isolation_level = connection.isolation_level
        repository = SQLiteSimulationBetPlanSnapshotRepository(connection=connection)
        self.assertIs(repository._connection, connection)
        self.assertIs(connection.row_factory, sqlite3.Row)
        self.assertEqual(connection.isolation_level, isolation_level)
        connection.execute("SELECT 1").fetchone()

    def test_constructor_is_keyword_only_and_enables_foreign_keys_like_existing_repositories(self) -> None:
        signature = inspect.signature(SQLiteSimulationBetPlanSnapshotRepository)
        self.assertEqual(tuple(signature.parameters), ("connection",))
        self.assertIs(signature.parameters["connection"].kind, inspect.Parameter.KEYWORD_ONLY)
        connection = sqlite3.connect(":memory:")
        self.assertEqual(connection.execute("PRAGMA foreign_keys").fetchone()[0], 0)
        SQLiteSimulationBetPlanSnapshotRepository(connection=connection)
        self.assertEqual(connection.execute("PRAGMA foreign_keys").fetchone()[0], 1)

    def test_constructor_rejects_invalid_or_closed_connections(self) -> None:
        for value in (None, "connection", sqlite3.Connection):
            with self.subTest(value=value):
                with self.assertRaises(RepositoryValidationError):
                    SQLiteSimulationBetPlanSnapshotRepository(connection=value)  # type: ignore[arg-type]
        closed = sqlite3.connect(":memory:")
        closed.close()
        with self.assertRaises(RepositoryValidationError):
            SQLiteSimulationBetPlanSnapshotRepository(connection=closed)

    def test_constructor_does_not_apply_migrations_or_create_schema(self) -> None:
        connection = sqlite3.connect(":memory:")
        connection.execute("CREATE TABLE races(id INTEGER PRIMARY KEY)")
        connection.execute("CREATE TABLE horses(id INTEGER PRIMARY KEY,race_id INTEGER)")
        SQLiteSimulationBetPlanSnapshotRepository(connection=connection)
        names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master")}
        self.assertNotIn("simulation_bet_plans", names)
        with self.assertRaises(sqlite3.OperationalError):
            SQLiteSimulationBetPlanSnapshotRepository(connection=connection).load_snapshot(identity=identity())

    def test_protocol_method_signatures_match_both_boundaries(self) -> None:
        self.assertEqual(
            inspect.signature(SQLiteSimulationBetPlanSnapshotRepository.load_snapshot),
            inspect.signature(SimulationBetPlanSnapshotSource.load_snapshot),
        )
        self.assertEqual(
            inspect.signature(SQLiteSimulationBetPlanSnapshotRepository.save_snapshot),
            inspect.signature(SimulationBetPlanSnapshotRepository.save_snapshot),
        )
        self.assertEqual(
            get_type_hints(SQLiteSimulationBetPlanSnapshotRepository.load_snapshot),
            get_type_hints(SimulationBetPlanSnapshotSource.load_snapshot),
        )
        self.assertEqual(
            get_type_hints(SQLiteSimulationBetPlanSnapshotRepository.save_snapshot),
            get_type_hints(SimulationBetPlanSnapshotRepository.save_snapshot),
        )

    def test_has_only_two_public_repository_methods(self) -> None:
        methods = {
            name
            for name, member in SQLiteSimulationBetPlanSnapshotRepository.__dict__.items()
            if inspect.isfunction(member) and not name.startswith("_")
        }
        self.assertEqual(methods, {"load_snapshot", "save_snapshot"})

    def test_load_and_save_reject_wrong_boundary_types(self) -> None:
        _connection, repository = self.repository()
        for value in (None, {}, (), "identity", object()):
            with self.subTest(load_type=type(value).__name__):
                with self.assertRaises(RepositoryValidationError):
                    repository.load_snapshot(identity=value)  # type: ignore[arg-type]
        for value in (None, {}, (), "snapshot", object()):
            with self.subTest(save_type=type(value).__name__):
                with self.assertRaises(RepositoryValidationError):
                    repository.save_snapshot(snapshot=value)  # type: ignore[arg-type]

    def test_round_trip_preserves_empty_single_and_multi_bet_snapshots(self) -> None:
        connection, repository = self.repository()
        cases = (
            snapshot(identity(run_id="empty"), budget=0),
            snapshot(identity(run_id="single"), budget=300, bets=(bet(identity(run_id="single"), "単勝", (11,), stake=100, rank=0),)),
            self.multi_snapshot(identity(run_id="multi")),
        )
        for value in cases:
            with self.subTest(run_id=value.identity.run_id):
                repository.save_snapshot(snapshot=value)
                loaded = repository.load_snapshot(identity=value.identity)
                self.assertEqual(loaded, value)
                self.assertIsNot(loaded, value)
        self.assertEqual(connection.execute("SELECT count(*) FROM simulation_bet_plans").fetchone()[0], 3)

    def test_round_trip_preserves_tuple_order_ranks_budget_policy_and_unused_budget(self) -> None:
        connection, repository = self.repository()
        plan_identity = identity()
        value = snapshot(
            plan_identity,
            policy_identity=policy(name="fixed-stake", version="2", config_hash="b" * 64),
            budget=1000,
            bets=(
                bet(plan_identity, "単勝", (11,), stake=100, rank=7),
                bet(plan_identity, "馬連", (11, 12), stake=200, rank=3),
            ),
        )
        repository.save_snapshot(snapshot=value)
        loaded = repository.load_snapshot(identity=plan_identity)
        self.assertEqual(loaded, value)
        self.assertEqual(loaded.budget.total_amount - sum(item.stake for item in loaded.bets), 700)
        self.assertEqual(tuple(item.recommendation_rank for item in loaded.bets), (7, 3))
        self.assertEqual(loaded.bets[1].race_entry_ids, (11, 12))
        self.assertEqual(connection.execute("SELECT purchase_order FROM simulation_bet_plan_bets ORDER BY id").fetchall(), [(0,), (1,)])

    def test_timezone_round_trip_is_canonical_utc_and_preserves_instant_and_microseconds(self) -> None:
        connection, repository = self.repository()
        cutoff = datetime(2026, 7, 26, 18, 1, 2, 123456, tzinfo=ZoneInfo("Asia/Tokyo"))
        plan_identity = identity(information_cutoff=cutoff)
        value = snapshot(plan_identity, budget=0)
        repository.save_snapshot(snapshot=value)
        stored = connection.execute("SELECT information_cutoff FROM simulation_bet_plans").fetchone()[0]
        loaded = repository.load_snapshot(identity=plan_identity)
        self.assertEqual(stored, "2026-07-26T09:01:02.123456+00:00")
        self.assertNotIn("Z", stored)
        self.assertEqual(loaded.identity.information_cutoff.tzinfo, UTC)
        self.assertEqual(loaded.identity.information_cutoff, cutoff)

    def test_not_found_and_stored_empty_snapshot_are_distinct(self) -> None:
        _connection, repository = self.repository()
        missing = identity(run_id="missing")
        self.assertIsNone(repository.load_snapshot(identity=missing))
        empty = snapshot(identity(run_id="empty"), budget=500)
        repository.save_snapshot(snapshot=empty)
        loaded = repository.load_snapshot(identity=empty.identity)
        self.assertEqual(loaded, empty)
        self.assertEqual(loaded.bets, ())

    def test_identical_save_is_idempotent_for_nonempty_and_empty_snapshots(self) -> None:
        for value in (self.multi_snapshot(), snapshot(identity(run_id="empty"), budget=0)):
            with self.subTest(run_id=value.identity.run_id):
                connection, repository = self.repository()
                repository.save_snapshot(snapshot=value)
                before = tuple(connection.execute("SELECT id FROM simulation_bet_plans"))
                repository.save_snapshot(snapshot=value)
                self.assertEqual(tuple(connection.execute("SELECT id FROM simulation_bet_plans")), before)
                self.assertEqual(connection.execute("SELECT count(*) FROM simulation_bet_plans").fetchone()[0], 1)
                self.assertEqual(repository.load_snapshot(identity=value.identity), value)

    def test_conflicting_content_for_same_identity_is_rejected_without_mutation(self) -> None:
        variants = (
            lambda base: snapshot(base.identity, policy_identity=policy(name="other"), budget=base.budget.total_amount, bets=base.bets),
            lambda base: snapshot(base.identity, policy_identity=policy(version="2"), budget=base.budget.total_amount, bets=base.bets),
            lambda base: snapshot(base.identity, policy_identity=policy(config_hash="b" * 64), budget=base.budget.total_amount, bets=base.bets),
            lambda base: snapshot(base.identity, budget=base.budget.total_amount - 100, bets=base.bets),
            lambda base: snapshot(base.identity, budget=base.budget.total_amount, bets=base.bets[:-1]),
            lambda base: snapshot(base.identity, budget=base.budget.total_amount, bets=tuple(reversed(base.bets))),
            lambda base: snapshot(base.identity, budget=base.budget.total_amount, bets=(base.bets[0], bet(base.identity, "ワイド", (11, 12), stake=200, rank=2), *base.bets[2:])),
            lambda base: snapshot(base.identity, budget=base.budget.total_amount, bets=(bet(base.identity, "単勝", (11,), stake=200, rank=1), *base.bets[1:])),
            lambda base: snapshot(base.identity, budget=base.budget.total_amount, bets=(bet(base.identity, "単勝", (11,), stake=100, rank=9), *base.bets[1:])),
            lambda base: snapshot(base.identity, budget=base.budget.total_amount, bets=(base.bets[0], bet(base.identity, "馬連", (11, 13), stake=200, rank=2), *base.bets[2:])),
        )
        for change in variants:
            with self.subTest(change=change):
                _connection, repository = self.repository()
                base = snapshot(identity(), budget=1200, bets=self.multi_snapshot().bets)
                repository.save_snapshot(snapshot=base)
                with self.assertRaises(RepositoryConflictError):
                    repository.save_snapshot(snapshot=change(base))
                self.assertEqual(repository.load_snapshot(identity=base.identity), base)

    def test_different_natural_identity_creates_a_second_snapshot(self) -> None:
        connection, repository = self.repository()
        first = self.multi_snapshot()
        second = self.multi_snapshot(identity(run_id="run-2", strategy_config_hash="b" * 64))
        repository.save_snapshot(snapshot=first)
        repository.save_snapshot(snapshot=second)
        self.assertEqual(connection.execute("SELECT count(*) FROM simulation_bet_plans").fetchone()[0], 2)

    def test_active_caller_transaction_is_rejected_without_rolling_it_back(self) -> None:
        connection, repository = self.repository()
        connection.execute("BEGIN")
        with self.assertRaises(RepositoryValidationError):
            repository.save_snapshot(snapshot=snapshot())
        self.assertTrue(connection.in_transaction)
        connection.rollback()
        repository.save_snapshot(snapshot=snapshot())

    def test_integrity_failure_rolls_back_all_rows_and_connection_can_be_reused(self) -> None:
        connection, repository = self.repository()
        invalid_identity = identity(run_id="invalid")
        invalid = snapshot(
            invalid_identity,
            budget=100,
            bets=(bet(invalid_identity, "単勝", (21,), stake=100),),
        )
        with self.assertRaises(RepositoryDataIntegrityError):
            repository.save_snapshot(snapshot=invalid)
        self.assertEqual(connection.execute("SELECT count(*) FROM simulation_bet_plans").fetchone()[0], 0)
        self.assertEqual(connection.execute("SELECT count(*) FROM simulation_bet_plan_bets").fetchone()[0], 0)
        self.assertEqual(connection.execute("SELECT count(*) FROM simulation_bet_plan_bet_selections").fetchone()[0], 0)
        self.assertFalse(connection.in_transaction)
        repository.save_snapshot(snapshot=snapshot())

    def test_load_rejects_purchase_and_selection_order_corruption(self) -> None:
        for target, value in (("purchase", 1), ("selection", 1)):
            with self.subTest(target=target):
                connection, repository = self.repository()
                base = snapshot(identity(), budget=200, bets=(bet(identity(), "馬連", (11, 12), stake=200),))
                repository.save_snapshot(snapshot=base)
                if target == "purchase":
                    connection.execute("UPDATE simulation_bet_plan_bets SET purchase_order=?", (value,))
                else:
                    connection.execute("UPDATE simulation_bet_plan_bet_selections SET selection_order=? WHERE selection_order=1", (value + 1,))
                connection.commit()
                with self.assertRaises(RepositoryDataIntegrityError):
                    repository.load_snapshot(identity=base.identity)

    def test_load_rejects_domain_corruption_without_repair(self) -> None:
        mutations = (
            "UPDATE simulation_bet_plans SET allocation_policy_config_hash='invalid'",
            "UPDATE simulation_bet_plan_bets SET bet_type='unsupported'",
            "UPDATE simulation_bet_plans SET budget_total_amount=100",
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                connection, repository = self.repository()
                base = self.multi_snapshot()
                repository.save_snapshot(snapshot=base)
                connection.execute(mutation)
                connection.commit()
                with self.assertRaises(RepositoryDataIntegrityError):
                    repository.load_snapshot(identity=base.identity)

    def test_cutoff_parser_rejects_malformed_naive_and_noncanonical_values(self) -> None:
        for value in ("not-a-date", "2026-07-26T09:00:00", "2026-07-26T18:00:00+09:00", "2026-07-26T09:00:00Z"):
            with self.subTest(value=value):
                with self.assertRaises(RepositoryDataIntegrityError):
                    SQLiteSimulationBetPlanSnapshotRepository._cutoff_from_text(value)

    def test_load_rejects_missing_selection_and_race_membership_corruption(self) -> None:
        connection, repository = self.repository()
        base = snapshot(identity(), budget=200, bets=(bet(identity(), "馬連", (11, 12), stake=200),))
        repository.save_snapshot(snapshot=base)
        connection.execute("DELETE FROM simulation_bet_plan_bet_selections WHERE selection_order=1")
        connection.commit()
        with self.assertRaises(RepositoryDataIntegrityError):
            repository.load_snapshot(identity=base.identity)

        connection, repository = self.repository()
        base = snapshot(identity(), budget=100, bets=(bet(identity(), "単勝", (11,), stake=100),))
        repository.save_snapshot(snapshot=base)
        connection.execute("UPDATE simulation_bet_plans SET race_id=2")
        connection.commit()
        with self.assertRaises(RepositoryDataIntegrityError):
            repository.load_snapshot(identity=identity(race_id=2))

    def test_file_backed_sequential_saves_obey_idempotency_and_conflict_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "plans.db"
            first_connection = sqlite3.connect(path)
            first_connection.execute("CREATE TABLE races(id INTEGER PRIMARY KEY)")
            first_connection.execute("CREATE TABLE horses(id INTEGER PRIMARY KEY,race_id INTEGER)")
            first_connection.execute("INSERT INTO races VALUES(1)")
            first_connection.execute("INSERT INTO horses VALUES(11,1)")
            first_connection.commit()
            apply_migrations(first_connection)
            second_connection = sqlite3.connect(path)
            first = SQLiteSimulationBetPlanSnapshotRepository(connection=first_connection)
            second = SQLiteSimulationBetPlanSnapshotRepository(connection=second_connection)
            value = snapshot(identity(), budget=100, bets=(bet(identity(), "単勝", (11,), stake=100),))
            first.save_snapshot(snapshot=value)
            second.save_snapshot(snapshot=value)
            with self.assertRaises(RepositoryConflictError):
                second.save_snapshot(snapshot=snapshot(value.identity, budget=200, bets=value.bets))
            first_connection.close()
            second_connection.close()

    def test_module_has_no_external_state_or_unrelated_simulation_dependencies(self) -> None:
        import scripts.simulation.repositories.sqlite_bet_plan_snapshot_repository as module

        source = inspect.getsource(module)
        for forbidden in (
            "database/keiba.db", "datetime.now", "random", "requests", "httpx", "urllib", "Provider",
            "PredictionPipeline", "Simulator", "_build_simulation_result", "_build_simulation_summary",
        ):
            self.assertNotIn(forbidden, source)

    def test_repository_is_imported_directly_without_creating_a_package_cycle(self) -> None:
        from scripts.simulation import repositories

        self.assertFalse(hasattr(repositories, "SQLiteSimulationBetPlanSnapshotRepository"))
        self.assertEqual(
            SQLiteSimulationBetPlanSnapshotRepository.__module__,
            "scripts.simulation.repositories.sqlite_bet_plan_snapshot_repository",
        )

    def test_target_race_count_is_not_added(self) -> None:
        import scripts.simulation.repositories.sqlite_bet_plan_snapshot_repository as module

        self.assertNotIn("target_race_count", inspect.getsource(module))


if __name__ == "__main__":
    unittest.main()
