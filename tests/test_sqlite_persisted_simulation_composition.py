"""Contracts for the caller-owned SQLite persisted simulation composition root."""

from __future__ import annotations

import ast
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
import inspect
import sqlite3
from typing import get_type_hints
import unittest

from scripts.migrations.runner import apply_migrations
from scripts.prediction.allocation_policy import AllocationPolicyConfig
from scripts.prediction.ability_engine import AbilityEngine
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
    SettlementStatus,
    SimulationRaceInput,
    SimulationRunContext,
    StrategyIdentity,
    build_strategy_identity,
)
from scripts.simulation.persisted_bet_plan_service import PersistedSimulationBetPlanService
from scripts.simulation.persisted_executor import PersistedRaceSimulationExecutor
from scripts.simulation.persisted_simulation_bet_source import PersistedSimulationBetSource
from scripts.simulation.persisted_simulation_run_service import (
    PersistedSimulationRunService,
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
from scripts.simulation.repositories.sqlite_race_entry_source import SQLiteRaceEntrySource
from scripts.simulation.repository_backed_persisted_settlement_source import (
    RepositoryBackedPersistedRaceSettlementSource,
)
from scripts.simulation.repository_backed_selection_resolver import (
    RepositoryBackedRaceEntrySelectionResolver,
)
from scripts.simulation.simulator import Simulator
from scripts.simulation.sqlite_persisted_simulation_composition import (
    build_sqlite_persisted_simulation_run_service,
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


class SQLiteConnectionSubclass(sqlite3.Connection):
    pass


class SQLitePersistedSimulationCompositionTests(unittest.TestCase):
    def _connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(":memory:")
        self.addCleanup(connection.close)
        return connection

    def _policy_config(
        self,
        *,
        policy_name: str = "fixed_stake_per_recommendation",
        policy_version: str = "1",
        parameters: dict[str, int] | None = None,
    ) -> AllocationPolicyConfig:
        return AllocationPolicyConfig(
            policy_name=policy_name,
            policy_version=policy_version,
            parameters={"stake_amount": 100} if parameters is None else parameters,
        )

    def _strategy_config(
        self,
        *,
        policy_config: AllocationPolicyConfig | None = None,
    ) -> StrategyConfig:
        return StrategyConfig(
            allocation_policy=(
                self._policy_config() if policy_config is None else policy_config
            ),
        )

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
    ) -> tuple[SimulationRunContext, StrategyIdentity, PredictionPipeline]:
        strategy_config = self._strategy_config()
        return (
            SimulationRunContext(
                run_id="composition-run",
                dataset_id="composition-dataset",
                started_at=RUN_STARTED_AT,
                target_commit_id="composition-commit",
            ),
            build_strategy_identity("CompositionStrategy", strategy_config),
            self._pipeline(strategy_config=strategy_config),
        )

    def _assert_no_statements_for_invalid_input(
        self,
        *,
        run_context: object,
        strategy_identity: object,
        prediction_pipeline: object,
        reason: str,
    ) -> None:
        connection = self._connection()
        statements: list[str] = []
        connection.set_trace_callback(statements.append)
        with self.assertRaisesRegex(ValueError, reason):
            build_sqlite_persisted_simulation_run_service(
                connection=connection,
                run_context=run_context,
                strategy_identity=strategy_identity,
                prediction_pipeline=prediction_pipeline,
            )
        self.assertEqual(statements, [])

    def _create_parent_schema_and_seed(
        self,
        connection: sqlite3.Connection,
        *,
        race_id: int,
        horse_id: int,
    ) -> None:
        connection.execute("CREATE TABLE races (id INTEGER PRIMARY KEY)")
        connection.execute(
            "CREATE TABLE horses (id INTEGER PRIMARY KEY, race_id INTEGER NOT NULL, horse_no INTEGER NOT NULL)",
        )
        connection.execute("INSERT INTO races (id) VALUES (?)", (race_id,))
        connection.execute(
            "INSERT INTO horses (id, race_id, horse_no) VALUES (?, ?, ?)",
            (horse_id, race_id, 1),
        )
        connection.commit()
        apply_migrations(connection)

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
            "composition-dataset",
            "fixture",
            INFORMATION_CUTOFF,
            (
                InputAuditEntry("entry", f"entry/{horse_id}", "fixture", f"entry/{horse_id}", horse_id, observed_at=INFORMATION_CUTOFF),
                InputAuditEntry("odds", f"odds/{horse_id}", "fixture", f"odds/{horse_id}", horse_id, observed_at=INFORMATION_CUTOFF),
                InputAuditEntry("jockey", f"jockey/{horse_id}", "fixture", f"jockey/{horse_id}", horse_id, observed_at=INFORMATION_CUTOFF),
                InputAuditEntry("track", "track", "fixture", "track", None, observed_at=INFORMATION_CUTOFF),
                InputAuditEntry("past_race", f"past_race/{horse_id}/none", "fixture", f"past_race/{horse_id}/none", horse_id, observed_at=INFORMATION_CUTOFF),
            ),
            True,
        )
        return SimulationRaceInput(
            race_id,
            date(2026, 8, 5),
            INFORMATION_CUTOFF + timedelta(hours=1),
            INFORMATION_CUTOFF,
            pipeline_input,
            audit,
        )

    def test_public_factory_api_is_the_only_production_definition(self) -> None:
        module = inspect.getmodule(build_sqlite_persisted_simulation_run_service)
        self.assertIsNotNone(module)
        self.assertEqual(
            build_sqlite_persisted_simulation_run_service.__module__,
            "scripts.simulation.sqlite_persisted_simulation_composition",
        )
        self.assertTrue(inspect.isfunction(build_sqlite_persisted_simulation_run_service))
        signature = inspect.signature(build_sqlite_persisted_simulation_run_service)
        self.assertEqual(
            tuple(signature.parameters),
            ("connection", "run_context", "strategy_identity", "prediction_pipeline"),
        )
        self.assertTrue(
            all(
                parameter.kind is inspect.Parameter.KEYWORD_ONLY
                for parameter in signature.parameters.values()
            )
        )
        hints = get_type_hints(build_sqlite_persisted_simulation_run_service)
        self.assertIs(hints["connection"], sqlite3.Connection)
        self.assertIs(hints["run_context"], SimulationRunContext)
        self.assertIs(hints["strategy_identity"], StrategyIdentity)
        self.assertIs(hints["prediction_pipeline"], PredictionPipeline)
        self.assertIs(hints["return"], PersistedSimulationRunService)
        source = inspect.getsource(module)
        tree = ast.parse(source)
        self.assertEqual(
            [node.name for node in tree.body if isinstance(node, ast.FunctionDef)],
            ["build_sqlite_persisted_simulation_run_service"],
        )
        self.assertEqual(
            [node for node in tree.body if isinstance(node, ast.ClassDef)],
            [],
        )

    def test_direct_validation_rejects_invalid_connection_before_component_construction(self) -> None:
        run_context, strategy_identity, pipeline = self._valid_inputs()
        with self.assertRaisesRegex(ValueError, "connection must be sqlite3.Connection"):
            build_sqlite_persisted_simulation_run_service(
                connection=object(),
                run_context=run_context,
                strategy_identity=strategy_identity,
                prediction_pipeline=pipeline,
            )

    def test_connection_subclass_is_accepted(self) -> None:
        connection = sqlite3.connect(":memory:", factory=SQLiteConnectionSubclass)
        self.addCleanup(connection.close)
        run_context, strategy_identity, pipeline = self._valid_inputs()

        service = build_sqlite_persisted_simulation_run_service(
            connection=connection,
            run_context=run_context,
            strategy_identity=strategy_identity,
            prediction_pipeline=pipeline,
        )

        self.assertIs(type(service), PersistedSimulationRunService)
        self.assertIs(service._bet_plan_service._snapshot_repository._connection, connection)

    def test_direct_validation_rejects_exact_type_and_coherence_violations_without_sql(self) -> None:
        valid_context, valid_identity, valid_pipeline = self._valid_inputs()
        subclass_context = SimulationRunContextSubclass(
            valid_context.run_id,
            valid_context.dataset_id,
            valid_context.started_at,
            valid_context.target_commit_id,
        )
        subclass_identity = StrategyIdentitySubclass(
            valid_identity.strategy_id,
            valid_identity.strategy_name,
            valid_identity.strategy_config,
            valid_identity.strategy_config_hash,
        )
        invalid_config_pipeline = self._pipeline(
            strategy_config=valid_identity.strategy_config,
        )
        object.__setattr__(invalid_config_pipeline, "config", object())
        different_config = self._strategy_config(
            policy_config=valid_identity.strategy_config.allocation_policy,
        )
        mismatch_pipeline = self._pipeline(strategy_config=different_config)
        no_policy_config = StrategyConfig(allocation_policy=None)
        no_policy_identity = build_strategy_identity("NoPolicy", no_policy_config)
        no_policy_pipeline = self._pipeline(strategy_config=no_policy_config)
        invalid_policy_config = self._strategy_config()
        object.__setattr__(invalid_policy_config, "allocation_policy", object())
        invalid_policy_identity = build_strategy_identity(
            "InvalidPolicy",
            self._strategy_config(),
        )
        object.__setattr__(invalid_policy_identity, "strategy_config", invalid_policy_config)
        invalid_policy_pipeline = self._pipeline(strategy_config=invalid_policy_config)

        cases = (
            (object(), valid_identity, valid_pipeline, "run_context must be a SimulationRunContext"),
            (subclass_context, valid_identity, valid_pipeline, "run_context must be a SimulationRunContext"),
            (valid_context, object(), valid_pipeline, "strategy_identity must be a StrategyIdentity"),
            (valid_context, subclass_identity, valid_pipeline, "strategy_identity must be a StrategyIdentity"),
            (valid_context, valid_identity, object(), "prediction_pipeline must be a PredictionPipeline"),
            (valid_context, valid_identity, PredictionPipelineSubclass.__new__(PredictionPipelineSubclass), "prediction_pipeline must be a PredictionPipeline"),
            (valid_context, valid_identity, invalid_config_pipeline, "prediction_pipeline.config must be a PipelineConfig"),
            (valid_context, valid_identity, mismatch_pipeline, "prediction_pipeline.config.strategy_config must be strategy_identity.strategy_config"),
            (valid_context, no_policy_identity, no_policy_pipeline, "strategy_identity.strategy_config.allocation_policy is required"),
            (valid_context, invalid_policy_identity, invalid_policy_pipeline, "allocation_policy must be an AllocationPolicyConfig"),
        )
        for run_context, strategy_identity, pipeline, reason in cases:
            with self.subTest(reason=reason):
                self._assert_no_statements_for_invalid_input(
                    run_context=run_context,
                    strategy_identity=strategy_identity,
                    prediction_pipeline=pipeline,
                    reason=reason,
                )

    def test_fixed_stake_configuration_failures_propagate_without_translation(self) -> None:
        cases = (
            (self._policy_config(policy_name="unsupported"), "policy_config has an unsupported fixed-stake policy name"),
            (self._policy_config(policy_version="2"), "policy_config has an unsupported fixed-stake policy version"),
            (self._policy_config(parameters={"stake_amount": 50}), "stake_amount must be a positive multiple of 100"),
        )
        for policy_config, reason in cases:
            with self.subTest(reason=reason):
                strategy_config = self._strategy_config(policy_config=policy_config)
                run_context = SimulationRunContext(
                    "failing-run",
                    "failing-dataset",
                    RUN_STARTED_AT,
                    "failing-commit",
                )
                strategy_identity = build_strategy_identity("FailingPolicy", strategy_config)
                pipeline = self._pipeline(strategy_config=strategy_config)
                connection = self._connection()
                with self.assertRaisesRegex(ValueError, reason):
                    build_sqlite_persisted_simulation_run_service(
                        connection=connection,
                        run_context=run_context,
                        strategy_identity=strategy_identity,
                        prediction_pipeline=pipeline,
                    )
                self.assertFalse(connection.in_transaction)
                self.assertEqual(connection.execute("SELECT 1").fetchone(), (1,))

    def test_exact_composition_shares_one_connection_and_snapshot_repository(self) -> None:
        connection = self._connection()
        run_context, strategy_identity, pipeline = self._valid_inputs()
        statements: list[str] = []
        connection.set_trace_callback(statements.append)

        service = build_sqlite_persisted_simulation_run_service(
            connection=connection,
            run_context=run_context,
            strategy_identity=strategy_identity,
            prediction_pipeline=pipeline,
        )
        connection.set_trace_callback(None)

        bet_plan_service = service._bet_plan_service
        simulator = service._simulator
        executor = simulator._race_executor
        settlement_source = executor._settlement_source
        bet_source = settlement_source._bet_source
        snapshot_repository = bet_plan_service._snapshot_repository
        plan_builder = bet_plan_service._plan_builder
        selection_resolver = plan_builder._selection_resolver
        race_entry_source = selection_resolver._race_entry_source
        race_result_repository = settlement_source._race_result_repository
        payout_repository = settlement_source._payout_repository

        self.assertIs(type(service), PersistedSimulationRunService)
        self.assertIs(type(bet_plan_service), PersistedSimulationBetPlanService)
        self.assertIs(type(simulator), Simulator)
        self.assertIs(type(executor), PersistedRaceSimulationExecutor)
        self.assertIs(type(settlement_source), RepositoryBackedPersistedRaceSettlementSource)
        self.assertIs(type(bet_source), PersistedSimulationBetSource)
        self.assertIs(bet_plan_service._run_context, run_context)
        self.assertIs(bet_source._run_context, run_context)
        self.assertIs(bet_plan_service._strategy_identity, strategy_identity)
        self.assertIs(simulator._strategy_identity, strategy_identity)
        self.assertIs(executor._strategy_identity, strategy_identity)
        self.assertIs(bet_plan_service._prediction_pipeline, pipeline)
        self.assertIs(snapshot_repository, bet_source._snapshot_source)
        self.assertIs(snapshot_repository._connection, connection)
        self.assertIs(race_entry_source._connection, connection)
        self.assertIs(race_result_repository._connection, connection)
        self.assertIs(payout_repository._connection, connection)
        self.assertFalse(connection.in_transaction)
        self.assertTrue(statements)
        self.assertTrue(all(statement.startswith("PRAGMA foreign_keys") for statement in statements))
        self.assertEqual(connection.execute("SELECT 1").fetchone(), (1,))

    def test_factory_source_has_no_lifecycle_or_runtime_work(self) -> None:
        module = inspect.getmodule(build_sqlite_persisted_simulation_run_service)
        self.assertIsNotNone(module)
        source = inspect.getsource(module)
        forbidden = (
            "sqlite3.connect",
            "apply_migrations",
            "get_pending_migrations",
            "get_connection",
            "DB_PATH",
            "database/" + "keiba.db",
            ".close(",
            ".commit(",
            ".rollback(",
            "BEGIN",
            "datetime.now",
            "datetime.utcnow",
            "date.today",
            "requests",
            "logging",
            "print(",
            "argparse",
        )
        for text in forbidden:
            with self.subTest(text=text):
                self.assertNotIn(text, source)
        self.assertNotIn("try:", source)

    def test_in_memory_composition_executes_one_settled_race_and_leaves_connection_owned_by_caller(self) -> None:
        connection = self._connection()
        race_id = 401
        horse_id = 4011
        self._create_parent_schema_and_seed(
            connection,
            race_id=race_id,
            horse_id=horse_id,
        )
        run_context, strategy_identity, pipeline = self._valid_inputs()
        race_input = self._race_input(race_id=race_id, horse_id=horse_id)
        race_result_repository = SQLiteRaceResultRepository(connection)
        payout_repository = SQLitePayoutRepository(connection)
        result_finalized_at = datetime(2026, 8, 5, 14, 0, tzinfo=UTC)
        payout_finalized_at = datetime(2026, 8, 5, 14, 10, tzinfo=UTC)
        race_result_repository.save_race_result(
            PersistedRaceResult(
                race_id=race_id,
                result_status=RaceResultStatus.COMPLETE,
                finalized_at=result_finalized_at,
                observed_at=result_finalized_at + timedelta(minutes=1),
                source="fixture",
                entries=(
                    PersistedRaceResultEntry(
                        horse_no=1,
                        race_entry_id=horse_id,
                        finish_position=1,
                        result_status=RaceResultEntryStatus.CONFIRMED,
                    ),
                ),
            )
        )
        payout_repository.save_payout_publication(
            PayoutPublication(
                race_id=race_id,
                bet_type=WIN,
                finalized_at=payout_finalized_at,
                observed_at=payout_finalized_at + timedelta(minutes=1),
                is_complete=True,
                source="fixture",
                entries=(
                    PayoutRecord((horse_id,), 300, PayoutStatus.WINNING),
                ),
            )
        )
        service = build_sqlite_persisted_simulation_run_service(
            connection=connection,
            run_context=run_context,
            strategy_identity=strategy_identity,
            prediction_pipeline=pipeline,
        )

        summary = service.run(
            race_inputs=(race_input,),
            budgets_by_race_id={race_id: BetStakeBudget(total_amount=100)},
        )

        self.assertEqual(
            (
                summary.race_count,
                summary.settled_race_count,
                summary.no_bet_race_count,
                summary.unsettled_race_count,
                summary.settled_purchase_race_count,
            ),
            (1, 1, 0, 0, 1),
        )
        self.assertEqual(
            (
                summary.bet_count,
                summary.settled_bet_count,
                summary.hit_bet_count,
                summary.hit_race_count,
                summary.investment,
                summary.payout,
                summary.profit,
                summary.roi,
                summary.bet_hit_rate,
                summary.race_hit_rate,
                summary.maximum_drawdown,
            ),
            (1, 1, 1, 1, 100, 300, 200, Decimal("300"), Decimal("100"), Decimal("100"), 0),
        )
        by_bet_type = summary.by_bet_type[WIN]
        self.assertEqual(
            (
                by_bet_type.bet_count,
                by_bet_type.settled_bet_count,
                by_bet_type.hit_bet_count,
                by_bet_type.investment,
                by_bet_type.payout,
                by_bet_type.profit,
                by_bet_type.roi,
                by_bet_type.bet_hit_rate,
            ),
            (1, 1, 1, 100, 300, 200, Decimal("300"), Decimal("100")),
        )
        snapshot_repository = service._bet_plan_service._snapshot_repository
        identity = SimulationBetPlanIdentity(
            run_id=run_context.run_id,
            race_id=race_id,
            strategy_id=strategy_identity.strategy_id,
            strategy_config_hash=strategy_identity.strategy_config_hash,
            information_cutoff=race_input.information_cutoff,
        )
        snapshot = snapshot_repository.load_snapshot(identity=identity)
        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot.budget, BetStakeBudget(total_amount=100))
        self.assertEqual(len(snapshot.bets), 1)
        self.assertEqual(snapshot.bets[0].race_entry_ids, (horse_id,))
        self.assertEqual(summary.by_bet_type[WIN].bet_count, 1)
        self.assertEqual(race_result_repository.get_race_result(race_id).result_status, RaceResultStatus.COMPLETE)
        self.assertTrue(
            payout_repository.get_latest_payout_publication(
                race_id,
                WIN,
                observed_at_lte=None,
                require_complete=True,
            ).is_complete
        )
        self.assertFalse(connection.in_transaction)
        self.assertEqual(connection.execute("SELECT 1").fetchone(), (1,))


if __name__ == "__main__":
    unittest.main()
