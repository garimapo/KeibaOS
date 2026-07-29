"""Contracts for the file-backed persisted simulation application runner."""

from __future__ import annotations

import ast
from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
import inspect
from pathlib import Path
import sqlite3
import tempfile
from typing import get_type_hints
import unittest

from scripts.migrations.runner import apply_migrations
from scripts.prediction.ability_engine import AbilityEngine
from scripts.prediction.allocation_policy import AllocationPolicyConfig
from scripts.prediction.bet_generator import BetGenerator
from scripts.prediction.bet_strategy import RuleBasedBetStrategy, StrategyConfig
from scripts.prediction.jockey_engine import JockeyEngine
from scripts.prediction.pace_engine import PaceEngine
from scripts.prediction.prediction_pipeline import (
    PipelineConfig,
    PredictionPipeline,
    RacePredictionInput,
)
from scripts.prediction.predictor import Predictor
from scripts.prediction.track_engine import RaceTrackConditions, TrackEngine
from scripts.prediction.value_engine import ValueEngine
from scripts.simulation.bet_plan_identity import SimulationBetPlanIdentity
from scripts.simulation.models import (
    InputAuditEntry,
    InputSnapshotAudit,
    SimulationRaceInput,
    SimulationRunContext,
    SimulationSummary,
    StrategyIdentity,
    build_strategy_identity,
)
from scripts.simulation.repositories.interfaces import (
    PayoutPublication,
    PayoutRecord,
    PayoutStatus,
    PersistedRaceResult,
    PersistedRaceResultEntry,
    RaceResultEntryStatus,
    RaceResultStatus,
)
from scripts.simulation.repositories.sqlite import (
    SQLitePayoutRepository,
    SQLiteRaceResultRepository,
)
from scripts.simulation.repositories.sqlite_bet_plan_snapshot_repository import (
    SQLiteSimulationBetPlanSnapshotRepository,
)
from scripts.simulation.sqlite_persisted_simulation_application import (
    run_sqlite_persisted_simulation,
)
from scripts.simulation.stake_allocation import BetStakeBudget


RUN_STARTED_AT = datetime(2026, 8, 5, 8, 0, tzinfo=UTC)
INFORMATION_CUTOFF = datetime(2026, 8, 5, 9, 0, tzinfo=UTC)
REFERENCE_DATE = date(2026, 8, 5)
WIN = "単勝"


class SimulationRunContextSubclass(SimulationRunContext):
    pass


class StrategyIdentitySubclass(StrategyIdentity):
    pass


class PredictionPipelineSubclass(PredictionPipeline):
    pass


class SQLitePersistedSimulationApplicationTests(unittest.TestCase):
    def _temporary_path(self) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        return Path(directory.name) / "simulation.db"

    def _policy_config(self) -> AllocationPolicyConfig:
        return AllocationPolicyConfig(
            policy_name="fixed_stake_per_recommendation",
            policy_version="1",
            parameters={"stake_amount": 100},
        )

    def _strategy_config(self) -> StrategyConfig:
        return StrategyConfig(allocation_policy=self._policy_config())

    def _pipeline(self, *, strategy_config: StrategyConfig) -> PredictionPipeline:
        return PredictionPipeline(
            PipelineConfig(
                ability_engine=AbilityEngine(reference_date=REFERENCE_DATE),
                pace_engine=PaceEngine(),
                jockey_engine=JockeyEngine(reference_date=REFERENCE_DATE),
                track_engine=TrackEngine(reference_date=REFERENCE_DATE),
                predictor=Predictor(),
                value_engine=ValueEngine(),
                bet_generator=BetGenerator(),
                bet_strategy=RuleBasedBetStrategy(),
                strategy_config=strategy_config,
            )
        )

    def _valid_inputs(
        self,
        *,
        run_id: str = "application-run",
    ) -> tuple[SimulationRunContext, StrategyIdentity, PredictionPipeline]:
        strategy_config = self._strategy_config()
        return (
            SimulationRunContext(
                run_id=run_id,
                dataset_id="application-dataset",
                started_at=RUN_STARTED_AT,
                target_commit_id="application-commit",
            ),
            build_strategy_identity("ApplicationStrategy", strategy_config),
            self._pipeline(strategy_config=strategy_config),
        )

    def _create_parent_schema_and_seed(
        self,
        connection: sqlite3.Connection,
        *,
        race_id: int,
        horse_id: int,
    ) -> None:
        connection.execute("CREATE TABLE races (id INTEGER PRIMARY KEY)")
        connection.execute(
            "CREATE TABLE horses ("
            "id INTEGER PRIMARY KEY, race_id INTEGER NOT NULL, horse_no INTEGER NOT NULL)",
        )
        connection.execute("INSERT INTO races (id) VALUES (?)", (race_id,))
        connection.execute(
            "INSERT INTO horses (id, race_id, horse_no) VALUES (?, ?, 1)",
            (horse_id, race_id),
        )
        connection.commit()

    def _race_input(self, *, race_id: int, horse_id: int) -> SimulationRaceInput:
        pipeline_input = RacePredictionInput(
            {horse_id: []},
            {horse_id: "Fixture Jockey"},
            RaceTrackConditions("Tokyo", 1600, "turf", "firm"),
            {horse_id: 2.0},
            1,
            race_id,
        )
        audit = InputSnapshotAudit(
            "application-dataset",
            "fixture",
            INFORMATION_CUTOFF,
            (
                InputAuditEntry(
                    "entry", f"entry/{horse_id}", "fixture", f"entry/{horse_id}",
                    horse_id, observed_at=INFORMATION_CUTOFF,
                ),
                InputAuditEntry(
                    "odds", f"odds/{horse_id}", "fixture", f"odds/{horse_id}",
                    horse_id, observed_at=INFORMATION_CUTOFF,
                ),
                InputAuditEntry(
                    "jockey", f"jockey/{horse_id}", "fixture", f"jockey/{horse_id}",
                    horse_id, observed_at=INFORMATION_CUTOFF,
                ),
                InputAuditEntry(
                    "track", "track", "fixture", "track", None,
                    observed_at=INFORMATION_CUTOFF,
                ),
                InputAuditEntry(
                    "past_race", f"past_race/{horse_id}/none", "fixture",
                    f"past_race/{horse_id}/none", horse_id,
                    observed_at=INFORMATION_CUTOFF,
                ),
            ),
            True,
        )
        return SimulationRaceInput(
            race_id=race_id,
            target_race_date=date(2026, 8, 5),
            scheduled_start_at=INFORMATION_CUTOFF + timedelta(hours=1),
            information_cutoff=INFORMATION_CUTOFF,
            pipeline_input=pipeline_input,
            input_snapshot_audit=audit,
        )

    def _run(
        self,
        *,
        database_path: object,
        run_context: object,
        strategy_identity: object,
        prediction_pipeline: object,
        race_inputs: object,
        budgets_by_race_id: object,
    ) -> SimulationSummary:
        return run_sqlite_persisted_simulation(
            database_path=database_path,
            run_context=run_context,
            strategy_identity=strategy_identity,
            prediction_pipeline=prediction_pipeline,
            race_inputs=race_inputs,
            budgets_by_race_id=budgets_by_race_id,
        )

    def test_public_api_and_source_structure(self) -> None:
        module = inspect.getmodule(run_sqlite_persisted_simulation)
        self.assertIsNotNone(module)
        self.assertTrue(inspect.isfunction(run_sqlite_persisted_simulation))
        self.assertEqual(
            run_sqlite_persisted_simulation.__module__,
            "scripts.simulation.sqlite_persisted_simulation_application",
        )
        signature = inspect.signature(run_sqlite_persisted_simulation)
        self.assertEqual(
            tuple(signature.parameters),
            (
                "database_path",
                "run_context",
                "strategy_identity",
                "prediction_pipeline",
                "race_inputs",
                "budgets_by_race_id",
            ),
        )
        self.assertTrue(
            all(
                parameter.kind is inspect.Parameter.KEYWORD_ONLY
                for parameter in signature.parameters.values()
            )
        )
        hints = get_type_hints(run_sqlite_persisted_simulation)
        self.assertEqual(hints["database_path"], str | Path)
        self.assertIs(hints["run_context"], SimulationRunContext)
        self.assertIs(hints["strategy_identity"], StrategyIdentity)
        self.assertIs(hints["prediction_pipeline"], PredictionPipeline)
        self.assertEqual(
            hints["race_inputs"],
            Sequence[SimulationRaceInput],
        )
        self.assertEqual(
            hints["budgets_by_race_id"],
            Mapping[int, BetStakeBudget],
        )
        self.assertIs(hints["return"], SimulationSummary)
        source = inspect.getsource(module)
        tree = ast.parse(source)
        function_node = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "run_sqlite_persisted_simulation"
        )
        self.assertEqual(
            [node.name for node in tree.body if isinstance(node, ast.FunctionDef)],
            ["run_sqlite_persisted_simulation"],
        )
        self.assertEqual(
            [node for node in tree.body if isinstance(node, ast.ClassDef)],
            [],
        )
        self.assertFalse(any(isinstance(node, ast.ExceptHandler) for node in ast.walk(tree)))
        try_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.Try)]
        self.assertEqual(len(try_nodes), 1)
        self.assertTrue(try_nodes[0].finalbody)
        close_calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "connection"
            and node.func.attr == "close"
        ]
        self.assertEqual(len(close_calls), 1)
        self.assertTrue(
            any(close_calls[0] is node for node in ast.walk(try_nodes[0].finalbody[0]))
        )
        self.assertFalse(
            any(close_calls[0] is node for statement in try_nodes[0].body for node in ast.walk(statement))
        )
        body = function_node.body
        connect_statement_index = next(
            index
            for index, statement in enumerate(body)
            if any(
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "sqlite3"
                and node.func.attr == "connect"
                for node in ast.walk(statement)
            )
        )
        snapshot_statement_indices = [
            index
            for index, statement in enumerate(body)
            if isinstance(statement, ast.Assign)
            and any(
                isinstance(target, ast.Name)
                and target.id in {"race_input_values", "budget_values"}
                for target in statement.targets
            )
        ]
        validation_statement_indices = [
            index
            for index, statement in enumerate(body)
            if isinstance(statement, ast.If)
        ]
        self.assertEqual(len(validation_statement_indices), 7)
        self.assertEqual(len(snapshot_statement_indices), 2)
        self.assertTrue(
            all(index < min(snapshot_statement_indices) for index in validation_statement_indices)
        )
        self.assertTrue(all(index < connect_statement_index for index in snapshot_statement_indices))
        self.assertIsInstance(body[connect_statement_index], ast.Assign)
        self.assertIsInstance(body[connect_statement_index + 1], ast.Try)

    def test_pre_open_validation_rejects_invalid_paths_without_creating_a_file(self) -> None:
        run_context, strategy_identity, pipeline = self._valid_inputs()
        cases = (None, b"db", bytearray(b"db"), 1, True, object(), "", "   ", "bad\x00path")
        for value in cases:
            with self.subTest(value=repr(value)):
                with self.assertRaisesRegex(ValueError, "database_path must be a non-empty path"):
                    self._run(
                        database_path=value,
                        run_context=run_context,
                        strategy_identity=strategy_identity,
                        prediction_pipeline=pipeline,
                        race_inputs=(),
                        budgets_by_race_id={},
                    )

    def test_pre_open_validation_rejects_exact_inputs_and_containers_without_creating_a_file(self) -> None:
        run_context, strategy_identity, pipeline = self._valid_inputs()
        path = self._temporary_path()
        context_subclass = SimulationRunContextSubclass(
            run_context.run_id, run_context.dataset_id, run_context.started_at,
            run_context.target_commit_id,
        )
        identity_subclass = StrategyIdentitySubclass(
            strategy_identity.strategy_id, strategy_identity.strategy_name,
            strategy_identity.strategy_config, strategy_identity.strategy_config_hash,
        )
        pipeline_subclass = PredictionPipelineSubclass.__new__(PredictionPipelineSubclass)
        cases = (
            (object(), strategy_identity, pipeline, (), {}, "run_context must be a SimulationRunContext"),
            (context_subclass, strategy_identity, pipeline, (), {}, "run_context must be a SimulationRunContext"),
            (run_context, object(), pipeline, (), {}, "strategy_identity must be a StrategyIdentity"),
            (run_context, identity_subclass, pipeline, (), {}, "strategy_identity must be a StrategyIdentity"),
            (run_context, strategy_identity, object(), (), {}, "prediction_pipeline must be a PredictionPipeline"),
            (run_context, strategy_identity, pipeline_subclass, (), {}, "prediction_pipeline must be a PredictionPipeline"),
            (run_context, strategy_identity, pipeline, None, {}, "race_inputs must be a Sequence"),
            (run_context, strategy_identity, pipeline, 1, {}, "race_inputs must be a Sequence"),
            (run_context, strategy_identity, pipeline, object(), {}, "race_inputs must be a Sequence"),
            (run_context, strategy_identity, pipeline, "races", {}, "race_inputs must be a Sequence"),
            (run_context, strategy_identity, pipeline, b"races", {}, "race_inputs must be a Sequence"),
            (run_context, strategy_identity, pipeline, bytearray(b"races"), {}, "race_inputs must be a Sequence"),
            (run_context, strategy_identity, pipeline, {1: object()}, {}, "race_inputs must be a Sequence"),
            (run_context, strategy_identity, pipeline, (value for value in ()), {}, "race_inputs must be a Sequence"),
            (run_context, strategy_identity, pipeline, (), None, "budgets_by_race_id must be a Mapping"),
            (run_context, strategy_identity, pipeline, (), [], "budgets_by_race_id must be a Mapping"),
            (run_context, strategy_identity, pipeline, (), (), "budgets_by_race_id must be a Mapping"),
            (run_context, strategy_identity, pipeline, (), (value for value in ()), "budgets_by_race_id must be a Mapping"),
            (run_context, strategy_identity, pipeline, (), object(), "budgets_by_race_id must be a Mapping"),
        )
        for context, identity, selected_pipeline, inputs, budgets, reason in cases:
            with self.subTest(reason=reason, inputs=repr(inputs), budgets=repr(budgets)):
                with self.assertRaisesRegex(ValueError, reason):
                    self._run(
                        database_path=path,
                        run_context=context,
                        strategy_identity=identity,
                        prediction_pipeline=selected_pipeline,
                        race_inputs=inputs,
                        budgets_by_race_id=budgets,
                    )
                self.assertFalse(path.exists())

    def test_pending_migrations_are_applied_for_empty_run_and_connection_closes(self) -> None:
        path = self._temporary_path()
        setup = sqlite3.connect(path)
        self.addCleanup(setup.close)
        setup.execute("CREATE TABLE races (id INTEGER PRIMARY KEY)")
        setup.execute(
            "CREATE TABLE horses (id INTEGER PRIMARY KEY, race_id INTEGER NOT NULL, horse_no INTEGER NOT NULL)",
        )
        setup.commit()
        setup.close()
        run_context, strategy_identity, pipeline = self._valid_inputs()

        summary = self._run(
            database_path=path,
            run_context=run_context,
            strategy_identity=strategy_identity,
            prediction_pipeline=pipeline,
            race_inputs=(),
            budgets_by_race_id={},
        )

        self.assertEqual(
            (summary.race_count, summary.bet_count, summary.investment, summary.payout,
             summary.profit, summary.roi, summary.maximum_drawdown),
            (0, 0, 0, 0, 0, None, 0),
        )
        verification = sqlite3.connect(path)
        self.addCleanup(verification.close)
        self.assertEqual(
            dict(verification.execute("SELECT version, name FROM schema_migrations")),
            {8: "v008_simulation_schema", 9: "v009_simulation_bet_plan_schema"},
        )
        self.assertIsNotNone(
            verification.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='race_results'",
            ).fetchone(),
        )
        self.assertIsNotNone(
            verification.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='simulation_bet_plans'",
            ).fetchone(),
        )
        self.assertEqual(verification.execute("SELECT 1").fetchone(), (1,))

    def test_file_backed_settled_run_preserves_caller_collections_and_persists_snapshot(self) -> None:
        path = self._temporary_path()
        race_id = 501
        horse_id = 5011
        setup = sqlite3.connect(path)
        self._create_parent_schema_and_seed(setup, race_id=race_id, horse_id=horse_id)
        apply_migrations(setup)
        result_repository = SQLiteRaceResultRepository(setup)
        payout_repository = SQLitePayoutRepository(setup)
        result_time = datetime(2026, 8, 5, 14, 0, tzinfo=UTC)
        payout_time = datetime(2026, 8, 5, 14, 10, tzinfo=UTC)
        result_repository.save_race_result(
            PersistedRaceResult(
                race_id=race_id,
                result_status=RaceResultStatus.COMPLETE,
                finalized_at=result_time,
                observed_at=result_time + timedelta(minutes=1),
                source="fixture",
                entries=(PersistedRaceResultEntry(
                    horse_no=1,
                    race_entry_id=horse_id,
                    finish_position=1,
                    result_status=RaceResultEntryStatus.CONFIRMED,
                ),),
            )
        )
        payout_repository.save_payout_publication(
            PayoutPublication(
                race_id=race_id,
                bet_type=WIN,
                finalized_at=payout_time,
                observed_at=payout_time + timedelta(minutes=1),
                is_complete=True,
                source="fixture",
                entries=(PayoutRecord((horse_id,), 300, PayoutStatus.WINNING),),
            )
        )
        setup.close()
        run_context, strategy_identity, pipeline = self._valid_inputs()
        race_input = self._race_input(race_id=race_id, horse_id=horse_id)
        budget = BetStakeBudget(total_amount=100)
        race_inputs = [race_input]
        budgets = {race_id: budget}

        summary = self._run(
            database_path=path,
            run_context=run_context,
            strategy_identity=strategy_identity,
            prediction_pipeline=pipeline,
            race_inputs=race_inputs,
            budgets_by_race_id=budgets,
        )

        self.assertEqual(race_inputs, [race_input])
        self.assertIs(race_inputs[0], race_input)
        self.assertEqual(budgets, {race_id: budget})
        self.assertIs(budgets[race_id], budget)
        self.assertEqual(
            (summary.race_count, summary.settled_race_count, summary.no_bet_race_count,
             summary.unsettled_race_count, summary.settled_purchase_race_count),
            (1, 1, 0, 0, 1),
        )
        self.assertEqual(
            (summary.bet_count, summary.settled_bet_count, summary.hit_bet_count,
             summary.hit_race_count, summary.investment, summary.payout, summary.profit,
             summary.roi, summary.bet_hit_rate, summary.race_hit_rate, summary.maximum_drawdown),
            (1, 1, 1, 1, 100, 300, 200, Decimal("300"), Decimal("100"), Decimal("100"), 0),
        )
        run_context_tuple, strategy_identity_tuple, pipeline_tuple = self._valid_inputs(
            run_id="application-run-tuple",
        )
        race_inputs_tuple = (race_input,)
        summary_tuple = self._run(
            database_path=path,
            run_context=run_context_tuple,
            strategy_identity=strategy_identity_tuple,
            prediction_pipeline=pipeline_tuple,
            race_inputs=race_inputs_tuple,
            budgets_by_race_id=budgets,
        )
        self.assertEqual(race_inputs_tuple, (race_input,))
        self.assertIs(race_inputs_tuple[0], race_input)
        self.assertEqual(budgets, {race_id: budget})
        self.assertIs(budgets[race_id], budget)
        self.assertEqual(
            (summary_tuple.race_count, summary_tuple.settled_race_count,
             summary_tuple.bet_count, summary_tuple.investment, summary_tuple.payout,
             summary_tuple.profit, summary_tuple.roi),
            (1, 1, 1, 100, 300, 200, Decimal("300")),
        )
        verification = sqlite3.connect(path)
        self.addCleanup(verification.close)
        snapshot_repository = SQLiteSimulationBetPlanSnapshotRepository(
            connection=verification,
        )
        identity = SimulationBetPlanIdentity(
            run_id=run_context.run_id,
            race_id=race_id,
            strategy_id=strategy_identity.strategy_id,
            strategy_config_hash=strategy_identity.strategy_config_hash,
            information_cutoff=race_input.information_cutoff,
        )
        snapshot = snapshot_repository.load_snapshot(identity=identity)
        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot.budget, budget)
        self.assertEqual(len(snapshot.bets), 1)
        self.assertEqual(snapshot.bets[0].race_entry_ids, (horse_id,))
        self.assertEqual(
            verification.execute("SELECT COUNT(*) FROM simulation_bet_plans").fetchone(),
            (2,),
        )
        self.assertEqual(
            dict(verification.execute("SELECT version, name FROM schema_migrations")),
            {8: "v008_simulation_schema", 9: "v009_simulation_bet_plan_schema"},
        )
        self.assertFalse(verification.in_transaction)
        self.assertEqual(verification.execute("SELECT 1").fetchone(), (1,))

    def test_unknown_future_migration_version_fails_before_composition_and_leaves_database_reconnectable(self) -> None:
        path = self._temporary_path()
        setup = sqlite3.connect(path)
        setup.execute(
            "CREATE TABLE schema_migrations ("
            "version INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_at TEXT NOT NULL)",
        )
        setup.execute(
            "INSERT INTO schema_migrations (version, name, applied_at) VALUES (999, ?, ?)",
            ("future_migration", "2026-08-05T00:00:00+00:00"),
        )
        setup.commit()
        setup.close()
        run_context, strategy_identity, pipeline = self._valid_inputs()

        with self.assertRaisesRegex(RuntimeError, "unknown future migration version"):
            self._run(
                database_path=path,
                run_context=run_context,
                strategy_identity=strategy_identity,
                prediction_pipeline=pipeline,
                race_inputs=(),
                budgets_by_race_id={},
            )

        verification = sqlite3.connect(path)
        self.addCleanup(verification.close)
        self.assertIsNone(
            verification.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='simulation_bet_plans'",
            ).fetchone(),
        )
        self.assertEqual(verification.execute("SELECT 1").fetchone(), (1,))

    def test_duplicate_race_id_run_failure_closes_connection_without_snapshot(self) -> None:
        path = self._temporary_path()
        race_id = 601
        horse_id = 6011
        setup = sqlite3.connect(path)
        self._create_parent_schema_and_seed(setup, race_id=race_id, horse_id=horse_id)
        apply_migrations(setup)
        setup.close()
        run_context, strategy_identity, pipeline = self._valid_inputs()
        race_input = self._race_input(race_id=race_id, horse_id=horse_id)

        with self.assertRaisesRegex(ValueError, "race_inputs must not contain duplicate race_id values"):
            self._run(
                database_path=path,
                run_context=run_context,
                strategy_identity=strategy_identity,
                prediction_pipeline=pipeline,
                race_inputs=(race_input, race_input),
                budgets_by_race_id={race_id: BetStakeBudget(total_amount=100)},
            )

        verification = sqlite3.connect(path)
        self.addCleanup(verification.close)
        self.assertEqual(verification.execute("SELECT COUNT(*) FROM simulation_bet_plans").fetchone(), (0,))
        self.assertEqual(verification.execute("SELECT 1").fetchone(), (1,))

    def test_source_contract_limits_side_effects_to_the_runner_boundary(self) -> None:
        module = inspect.getmodule(run_sqlite_persisted_simulation)
        self.assertIsNotNone(module)
        source = inspect.getsource(module)
        tree = ast.parse(source)
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
        self.assertEqual(
            sum(
                isinstance(call.func, ast.Attribute)
                and isinstance(call.func.value, ast.Name)
                and call.func.value.id == "sqlite3"
                and call.func.attr == "connect"
                for call in calls
            ),
            1,
        )
        self.assertEqual(
            sum(isinstance(call.func, ast.Name) and call.func.id == "apply_migrations" for call in calls),
            1,
        )
        self.assertEqual(
            sum(
                isinstance(call.func, ast.Name)
                and call.func.id == "build_sqlite_persisted_simulation_run_service"
                for call in calls
            ),
            1,
        )
        self.assertEqual(
            sum(isinstance(call.func, ast.Attribute) and call.func.attr == "run" for call in calls),
            1,
        )
        self.assertEqual(
            sum(isinstance(call.func, ast.Attribute) and call.func.attr == "close" for call in calls),
            1,
        )
        forbidden = (
            "get_connection", "DB_PATH", "database/keiba.db", "create_tables",
            "datetime.now", "datetime.utcnow", "date.today", "uuid", "requests", "logging",
            "print(", "argparse", "json", "open(", "connection.commit",
            "connection.rollback", "BEGIN",
        )
        for text in forbidden:
            with self.subTest(text=text):
                self.assertNotIn(text, source)
        self.assertFalse(
            any(
                alias.name in {"Any", "cast", "runtime_checkable"}
                for node in ast.walk(tree)
                if isinstance(node, (ast.Import, ast.ImportFrom))
                for alias in node.names
            )
        )
        self.assertFalse(
            any(
                isinstance(node, ast.Name)
                and node.id in {"Any", "cast", "runtime_checkable"}
                for node in ast.walk(tree)
            )
        )
        self.assertEqual(tree.type_ignores, [])


if __name__ == "__main__":
    unittest.main()
