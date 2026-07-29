"""Integration coverage for the persisted simulation composition path."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
import sqlite3
import unittest

from scripts.migrations.runner import apply_migrations
from scripts.prediction.allocation_policy import (
    AllocationPolicyConfig,
    build_allocation_policy_identity,
)
from scripts.prediction.ability_engine import AbilityEngine
from scripts.prediction.bet_generator import BetGenerator, BetRecommendation
from scripts.prediction.bet_strategy import (
    BetPlan,
    BetStrategy,
    RuleBasedBetStrategy,
    StrategyConfig,
)
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
from scripts.simulation.bet_plan_builder import SimulationBetPlanBuilder
from scripts.simulation.bet_plan_identity import SimulationBetPlanIdentity
from scripts.simulation.fixed_stake_allocator import FixedStakeBetAllocator
from scripts.simulation.models import (
    InputAuditEntry,
    InputSnapshotAudit,
    SettlementStatus,
    SimulationRaceInput,
    SimulationRunContext,
    StrategyIdentity,
    build_strategy_identity,
)
from scripts.simulation.persisted_executor import PersistedRaceSimulationExecutor
from scripts.simulation.persisted_bet_plan_service import PersistedSimulationBetPlanService
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
from scripts.simulation.selection_resolver import RaceEntrySelectionResolver
from scripts.simulation.simulator import Simulator
from scripts.simulation.stake_allocation import BetStakeBudget
from scripts.simulation.validation import SimulationValidationError


WIN = "\u5358\u52dd"
RUN_STARTED_AT = datetime(2026, 8, 1, 8, 0, tzinfo=UTC)
INFORMATION_CUTOFF = datetime(2026, 8, 1, 9, 0, tzinfo=UTC)
REFERENCE_DATE = date(2026, 8, 1)


class EmptyPlanForHorseBetStrategy(BetStrategy):
    """Use the real Pipeline while selecting no purchase for one fixture horse."""

    def __init__(self, *, empty_horse_id: int) -> None:
        self._empty_horse_id = empty_horse_id
        self._delegate = RuleBasedBetStrategy()

    def create_plan(
        self,
        recommendations: Sequence[BetRecommendation],
        config: StrategyConfig,
    ) -> BetPlan:
        if any(self._empty_horse_id in recommendation.horse_ids for recommendation in recommendations):
            return BetPlan(
                strategy_name=self.__class__.__name__,
                recommendations=(),
                candidate_count=0,
            )
        return self._delegate.create_plan(recommendations, config)


class PersistedSimulationIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.connection = sqlite3.connect(":memory:")
        self.addCleanup(self.connection.close)
        self._create_parent_schema_and_seed()
        self.connection.commit()
        self.assertFalse(self.connection.in_transaction)
        apply_migrations(self.connection)

        self.snapshot_repository = SQLiteSimulationBetPlanSnapshotRepository(
            connection=self.connection,
        )
        self.race_result_repository = SQLiteRaceResultRepository(self.connection)
        self.payout_repository = SQLitePayoutRepository(self.connection)
        self.race_entry_source = SQLiteRaceEntrySource(connection=self.connection)
        self.selection_resolver: RaceEntrySelectionResolver = (
            RepositoryBackedRaceEntrySelectionResolver(
                race_entry_source=self.race_entry_source,
            )
        )
        self.plan_builder = SimulationBetPlanBuilder(
            selection_resolver=self.selection_resolver,
        )
        self.run_context = SimulationRunContext(
            run_id="integration-run-20260801",
            dataset_id="integration-dataset",
            started_at=RUN_STARTED_AT,
            target_commit_id="integration-commit",
        )
        self.policy_config = AllocationPolicyConfig(
            policy_name="fixed_stake_per_recommendation",
            policy_version="1",
            parameters={"stake_amount": 100},
        )
        self.policy_identity = build_allocation_policy_identity(self.policy_config)
        self.allocator = FixedStakeBetAllocator(policy_config=self.policy_config)
        self.strategy_identity = build_strategy_identity(
            "PersistedIntegrationStrategy",
            StrategyConfig(allocation_policy=self.policy_config),
        )

    def _create_parent_schema_and_seed(self) -> None:
        self.connection.execute("CREATE TABLE races (id INTEGER PRIMARY KEY)")
        self.connection.execute(
            "CREATE TABLE horses (id INTEGER PRIMARY KEY, race_id INTEGER NOT NULL, horse_no INTEGER NOT NULL)",
        )
        race_ids = (101, 102, 103, 104, 105, 106)
        self.connection.executemany("INSERT INTO races (id) VALUES (?)", ((race_id,) for race_id in race_ids))
        self.connection.executemany(
            "INSERT INTO horses (id, race_id, horse_no) VALUES (?, ?, ?)",
            ((self.horse_id_for(race_id), race_id, 1) for race_id in race_ids),
        )

    @staticmethod
    def horse_id_for(race_id: int) -> int:
        return race_id * 10 + 1

    def race_input(
        self,
        race_id: int,
        *,
        information_cutoff: datetime = INFORMATION_CUTOFF,
        scheduled_start_at: datetime | None = None,
    ) -> SimulationRaceInput:
        horse_id = self.horse_id_for(race_id)
        scheduled_at = (
            information_cutoff + timedelta(hours=1)
            if scheduled_start_at is None
            else scheduled_start_at
        )
        pipeline_input = RacePredictionInput(
            {horse_id: []},
            {horse_id: f"Jockey {race_id}"},
            RaceTrackConditions("Tokyo", 1600, "turf", "firm"),
            {horse_id: 2.0},
            1,
            race_id,
        )
        audit = InputSnapshotAudit(
            "integration-dataset",
            "fixture",
            information_cutoff,
            (
                InputAuditEntry("entry", f"entry/{horse_id}", "fixture", f"entry/{horse_id}", horse_id, observed_at=information_cutoff),
                InputAuditEntry("odds", f"odds/{horse_id}", "fixture", f"odds/{horse_id}", horse_id, observed_at=information_cutoff),
                InputAuditEntry("jockey", f"jockey/{horse_id}", "fixture", f"jockey/{horse_id}", horse_id, observed_at=information_cutoff),
                InputAuditEntry("track", "track", "fixture", "track", None, observed_at=information_cutoff),
                InputAuditEntry("past_race", f"past_race/{horse_id}/none", "fixture", f"past_race/{horse_id}/none", horse_id, observed_at=information_cutoff),
            ),
            True,
        )
        return SimulationRaceInput(
            race_id,
            date(2026, 8, 1),
            scheduled_at,
            information_cutoff,
            pipeline_input,
            audit,
        )

    def plan_identity(self, race_input: SimulationRaceInput) -> SimulationBetPlanIdentity:
        return SimulationBetPlanIdentity(
            run_id=self.run_context.run_id,
            race_id=race_input.race_id,
            strategy_id=self.strategy_identity.strategy_id,
            strategy_config_hash=self.strategy_identity.strategy_config_hash,
            information_cutoff=race_input.information_cutoff,
        )

    def save_snapshot(
        self,
        race_input: SimulationRaceInput,
        *,
        include_bet: bool,
    ):
        recommendations = (
            (
                BetRecommendation(
                    rank=0,
                    bet_type=WIN,
                    horse_ids=(self.horse_id_for(race_input.race_id),),
                    estimated_probability=0.4,
                    expected_value=1.2,
                    combination_score=None,
                    prediction_score=80.0,
                ),
            )
            if include_bet
            else ()
        )
        plan = BetPlan(
            strategy_name=self.strategy_identity.strategy_name,
            recommendations=recommendations,
            candidate_count=len(recommendations),
        )
        budget = BetStakeBudget(total_amount=100 if include_bet else 0)
        allocation_plan = self.allocator.allocate(
            identity=self.plan_identity(race_input),
            policy_identity=self.policy_identity,
            bet_plan=plan,
            budget=budget,
        )
        snapshot = self.plan_builder.build(allocation_plan=allocation_plan)
        self.snapshot_repository.save_snapshot(snapshot=snapshot)
        loaded = self.snapshot_repository.load_snapshot(identity=snapshot.identity)
        self.assertEqual(loaded, snapshot)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.identity, snapshot.identity)
        self.assertEqual(loaded.policy_identity, snapshot.policy_identity)
        self.assertEqual(loaded.budget, snapshot.budget)
        self.assertEqual(loaded.bets, snapshot.bets)
        return snapshot

    def save_complete_race_result(
        self,
        race_id: int,
        *,
        finalized_at: datetime,
    ) -> None:
        self.race_result_repository.save_race_result(
            PersistedRaceResult(
                race_id=race_id,
                result_status=RaceResultStatus.COMPLETE,
                finalized_at=finalized_at,
                observed_at=finalized_at + timedelta(minutes=1),
                source="fixture",
                entries=(
                    PersistedRaceResultEntry(
                        horse_no=1,
                        race_entry_id=self.horse_id_for(race_id),
                        finish_position=1,
                        result_status=RaceResultEntryStatus.CONFIRMED,
                    ),
                ),
            ),
        )

    def save_payout(
        self,
        race_id: int,
        *,
        is_complete: bool,
        finalized_at: datetime | None,
        entries: tuple[PayoutRecord, ...],
    ) -> None:
        observed_at = (
            finalized_at + timedelta(minutes=1)
            if finalized_at is not None
            else datetime(2026, 8, 2, 13, 0, tzinfo=UTC)
        )
        self.payout_repository.save_payout_publication(
            PayoutPublication(
                race_id=race_id,
                bet_type=WIN,
                finalized_at=finalized_at,
                observed_at=observed_at,
                is_complete=is_complete,
                source="fixture",
                entries=entries,
            ),
        )

    def simulator(
        self,
        *,
        run_context: SimulationRunContext | None = None,
        strategy_identity: StrategyIdentity | None = None,
    ) -> tuple[Simulator, PersistedRaceSimulationExecutor]:
        context = self.run_context if run_context is None else run_context
        strategy = self.strategy_identity if strategy_identity is None else strategy_identity
        bet_source = PersistedSimulationBetSource(
            run_context=context,
            snapshot_source=self.snapshot_repository,
        )
        settlement_source = RepositoryBackedPersistedRaceSettlementSource(
            bet_source=bet_source,
            race_result_repository=self.race_result_repository,
            payout_repository=self.payout_repository,
        )
        executor = PersistedRaceSimulationExecutor(
            strategy_identity=strategy,
            settlement_source=settlement_source,
        )
        return Simulator(strategy_identity=strategy, race_executor=executor), executor

    def real_pipeline(
        self,
        *,
        strategy_config: StrategyConfig,
        bet_strategy: BetStrategy | None = None,
    ) -> PredictionPipeline:
        return PredictionPipeline(
            PipelineConfig(
                ability_engine=AbilityEngine(reference_date=REFERENCE_DATE),
                pace_engine=PaceEngine(),
                jockey_engine=JockeyEngine(reference_date=REFERENCE_DATE),
                track_engine=TrackEngine(reference_date=REFERENCE_DATE),
                predictor=Predictor(),
                value_engine=ValueEngine(),
                bet_generator=BetGenerator(),
                bet_strategy=RuleBasedBetStrategy() if bet_strategy is None else bet_strategy,
                strategy_config=strategy_config,
            ),
        )

    def assert_real_pipeline(self, pipeline: PredictionPipeline) -> None:
        self.assertIs(type(pipeline), PredictionPipeline)
        self.assertIs(type(pipeline.config), PipelineConfig)
        self.assertIs(type(pipeline.config.ability_engine), AbilityEngine)
        self.assertIs(type(pipeline.config.pace_engine), PaceEngine)
        self.assertIs(type(pipeline.config.jockey_engine), JockeyEngine)
        self.assertIs(type(pipeline.config.track_engine), TrackEngine)
        self.assertIs(type(pipeline.config.predictor), Predictor)
        self.assertIs(type(pipeline.config.value_engine), ValueEngine)
        self.assertIs(type(pipeline.config.bet_generator), BetGenerator)
        self.assertIs(type(pipeline.config.bet_strategy), RuleBasedBetStrategy)

    def persisted_bet_plan_service(
        self,
        *,
        strategy_identity: StrategyIdentity,
        pipeline: PredictionPipeline,
    ) -> PersistedSimulationBetPlanService:
        return PersistedSimulationBetPlanService(
            run_context=self.run_context,
            strategy_identity=strategy_identity,
            prediction_pipeline=pipeline,
            allocator=FixedStakeBetAllocator(
                policy_config=strategy_identity.strategy_config.allocation_policy,
            ),
            plan_builder=self.plan_builder,
            snapshot_repository=self.snapshot_repository,
        )

    def test_real_prediction_pipeline_persists_settled_plan_to_summary(self) -> None:
        race_input = self.race_input(101)
        strategy_config = StrategyConfig(allocation_policy=self.policy_config)
        strategy_identity = build_strategy_identity(
            "PredictionPersistedIntegrationStrategy",
            strategy_config,
        )
        pipeline = self.real_pipeline(strategy_config=strategy_config)
        self.assert_real_pipeline(pipeline)
        self.assertIs(pipeline.config.strategy_config, strategy_config)
        self.assertEqual(strategy_identity.strategy_config, strategy_config)
        service = self.persisted_bet_plan_service(
            strategy_identity=strategy_identity,
            pipeline=pipeline,
        )
        budget = BetStakeBudget(total_amount=100)

        snapshot = service.build_and_save(race_input=race_input, budget=budget)

        expected_identity = SimulationBetPlanIdentity(
            run_id=self.run_context.run_id,
            race_id=race_input.race_id,
            strategy_id=strategy_identity.strategy_id,
            strategy_config_hash=strategy_identity.strategy_config_hash,
            information_cutoff=race_input.information_cutoff,
        )
        self.assertEqual(snapshot.identity, expected_identity)
        self.assertEqual(snapshot.policy_identity, self.policy_identity)
        self.assertIs(snapshot.budget, budget)
        self.assertEqual(
            (snapshot.budget.total_amount, snapshot.allocated_amount, snapshot.unallocated_amount),
            (100, 100, 0),
        )
        self.assertEqual(len(snapshot.bets), 1)
        bet = snapshot.bets[0]
        self.assertEqual(
            (
                bet.race_id,
                bet.strategy_id,
                bet.bet_type,
                bet.race_entry_ids,
                bet.stake,
                bet.recommendation_rank,
                bet.placed_at_cutoff,
            ),
            (
                race_input.race_id,
                strategy_identity.strategy_id,
                BetGenerator.WIN,
                (self.horse_id_for(race_input.race_id),),
                100,
                1,
                race_input.information_cutoff,
            ),
        )
        self.assertNotEqual(snapshot.identity.information_cutoff, race_input.scheduled_start_at)
        self.assertNotEqual(snapshot.identity.information_cutoff, self.run_context.started_at)
        loaded = self.snapshot_repository.load_snapshot(identity=expected_identity)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded, snapshot)
        self.assertEqual(loaded.identity, expected_identity)
        self.assertEqual(loaded.bets, snapshot.bets)

        self.save_complete_race_result(
            race_input.race_id,
            finalized_at=datetime(2026, 8, 1, 14, 0, tzinfo=UTC),
        )
        self.save_payout(
            race_input.race_id,
            is_complete=True,
            finalized_at=datetime(2026, 8, 1, 14, 10, tzinfo=UTC),
            entries=(
                PayoutRecord(
                    (self.horse_id_for(race_input.race_id),),
                    300,
                    PayoutStatus.WINNING,
                ),
            ),
        )
        simulator, executor = self.simulator(strategy_identity=strategy_identity)

        result = executor(race_input=race_input)
        self.assertEqual(
            (
                result.race_id,
                result.settlement_status,
                result.exclusion_reason,
                result.bets,
                result.planned_investment,
                result.settled_investment,
                result.payout,
                result.profit,
                result.hit_bet_count,
            ),
            (
                race_input.race_id,
                SettlementStatus.SETTLED,
                None,
                snapshot.bets,
                100,
                100,
                300,
                200,
                1,
            ),
        )
        summary = simulator.run(race_inputs=(race_input,))
        self.assertEqual(
            (
                summary.strategy_id,
                summary.strategy_name,
                summary.strategy_config_hash,
            ),
            (
                strategy_identity.strategy_id,
                strategy_identity.strategy_name,
                strategy_identity.strategy_config_hash,
            ),
        )
        self.assertEqual(
            (
                summary.race_count,
                summary.settled_race_count,
                summary.unsettled_race_count,
                summary.no_bet_race_count,
                summary.void_race_count,
                summary.error_race_count,
                summary.unsupported_race_count,
            ),
            (1, 1, 0, 0, 0, 0, 0),
        )
        self.assertEqual(
            (
                summary.bet_count,
                summary.settled_bet_count,
                summary.settled_purchase_race_count,
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
            (1, 1, 1, 1, 1, 100, 300, 200, Decimal("300"), Decimal("100"), Decimal("100"), 0),
        )
        by_type = summary.by_bet_type[BetGenerator.WIN]
        self.assertEqual(
            (
                by_type.bet_count,
                by_type.settled_bet_count,
                by_type.hit_bet_count,
                by_type.investment,
                by_type.payout,
                by_type.profit,
                by_type.roi,
                by_type.bet_hit_rate,
            ),
            (1, 1, 1, 100, 300, 200, Decimal("300"), Decimal("100")),
        )

    def test_real_prediction_pipeline_persists_non_zero_budget_no_bet_to_summary(
        self,
    ) -> None:
        race_input = self.race_input(102)
        strategy_config = StrategyConfig(
            allowed_bet_types=frozenset(),
            allocation_policy=self.policy_config,
        )
        strategy_identity = build_strategy_identity(
            "PredictionPersistedNoBetIntegrationStrategy",
            strategy_config,
        )
        pipeline = self.real_pipeline(strategy_config=strategy_config)
        self.assert_real_pipeline(pipeline)
        self.assertIs(pipeline.config.strategy_config, strategy_config)
        self.assertEqual(strategy_identity.strategy_config, strategy_config)
        service = self.persisted_bet_plan_service(
            strategy_identity=strategy_identity,
            pipeline=pipeline,
        )
        budget = BetStakeBudget(total_amount=500)

        snapshot = service.build_and_save(race_input=race_input, budget=budget)

        expected_identity = SimulationBetPlanIdentity(
            run_id=self.run_context.run_id,
            race_id=race_input.race_id,
            strategy_id=strategy_identity.strategy_id,
            strategy_config_hash=strategy_identity.strategy_config_hash,
            information_cutoff=race_input.information_cutoff,
        )
        self.assertEqual(snapshot.identity, expected_identity)
        self.assertEqual(snapshot.policy_identity, self.policy_identity)
        self.assertIs(snapshot.budget, budget)
        self.assertEqual(
            (
                snapshot.budget.total_amount,
                snapshot.bets,
                snapshot.allocated_amount,
                snapshot.unallocated_amount,
            ),
            (500, (), 0, 500),
        )
        loaded = self.snapshot_repository.load_snapshot(identity=expected_identity)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded, snapshot)
        self.assertEqual(loaded.budget.total_amount, 500)
        self.assertEqual(loaded.bets, ())

        simulator, executor = self.simulator(strategy_identity=strategy_identity)
        result = executor(race_input=race_input)
        self.assertEqual(
            (
                result.race_id,
                result.settlement_status,
                result.exclusion_reason,
                result.bets,
                result.planned_investment,
                result.settled_investment,
                result.payout,
                result.profit,
                result.hit_bet_count,
            ),
            (
                race_input.race_id,
                SettlementStatus.NO_BET,
                None,
                (),
                0,
                None,
                None,
                None,
                0,
            ),
        )
        self.assertEqual(snapshot.budget.total_amount, 500)
        self.assertEqual(result.planned_investment, 0)
        summary = simulator.run(race_inputs=(race_input,))
        self.assertEqual(
            (
                summary.strategy_id,
                summary.strategy_name,
                summary.strategy_config_hash,
            ),
            (
                strategy_identity.strategy_id,
                strategy_identity.strategy_name,
                strategy_identity.strategy_config_hash,
            ),
        )
        self.assertEqual(
            (
                summary.race_count,
                summary.settled_race_count,
                summary.unsettled_race_count,
                summary.no_bet_race_count,
                summary.void_race_count,
                summary.error_race_count,
                summary.unsupported_race_count,
                summary.bet_count,
                summary.settled_bet_count,
                summary.settled_purchase_race_count,
                summary.hit_bet_count,
                summary.hit_race_count,
                summary.investment,
                summary.payout,
                summary.profit,
                summary.roi,
                summary.bet_hit_rate,
                summary.race_hit_rate,
                summary.maximum_drawdown,
                summary.by_bet_type,
            ),
            (1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, None, None, None, 0, {}),
        )

    def test_run_service_persists_mixed_three_race_run_before_simulation(self) -> None:
        race_a = self.race_input(
            101,
            scheduled_start_at=datetime(2026, 8, 1, 11, 0, tzinfo=UTC),
        )
        race_b = self.race_input(
            102,
            scheduled_start_at=datetime(2026, 8, 1, 10, 0, tzinfo=UTC),
        )
        race_c = self.race_input(
            103,
            scheduled_start_at=datetime(2026, 8, 1, 12, 0, tzinfo=UTC),
        )
        pipeline = self.real_pipeline(
            strategy_config=self.strategy_identity.strategy_config,
            bet_strategy=EmptyPlanForHorseBetStrategy(
                empty_horse_id=self.horse_id_for(race_b.race_id),
            ),
        )
        bet_plan_service = self.persisted_bet_plan_service(
            strategy_identity=self.strategy_identity,
            pipeline=pipeline,
        )
        simulator, _executor = self.simulator()
        run_service = PersistedSimulationRunService(
            bet_plan_service=bet_plan_service,
            simulator=simulator,
        )
        budgets = {
            race_a.race_id: BetStakeBudget(total_amount=100),
            race_b.race_id: BetStakeBudget(total_amount=500),
            race_c.race_id: BetStakeBudget(total_amount=100),
        }
        self.save_complete_race_result(
            race_a.race_id,
            finalized_at=datetime(2026, 8, 1, 13, 0, tzinfo=UTC),
        )
        self.save_payout(
            race_a.race_id,
            is_complete=True,
            finalized_at=datetime(2026, 8, 1, 13, 10, tzinfo=UTC),
            entries=(
                PayoutRecord(
                    (self.horse_id_for(race_a.race_id),),
                    300,
                    PayoutStatus.WINNING,
                ),
            ),
        )

        summary = run_service.run(
            race_inputs=(race_c, race_a, race_b),
            budgets_by_race_id=budgets,
        )

        snapshots = tuple(
            self.snapshot_repository.load_snapshot(identity=self.plan_identity(race_input))
            for race_input in (race_a, race_b, race_c)
        )
        self.assertTrue(all(snapshot is not None for snapshot in snapshots))
        self.assertEqual(tuple(len(snapshot.bets) for snapshot in snapshots), (1, 0, 1))
        self.assertEqual(snapshots[1].budget, budgets[race_b.race_id])
        self.assertEqual(
            (
                snapshots[1].budget.total_amount,
                snapshots[1].allocated_amount,
                snapshots[1].unallocated_amount,
            ),
            (500, 0, 500),
        )
        self.assertEqual(
            (
                summary.race_count,
                summary.settled_race_count,
                summary.no_bet_race_count,
                summary.unsettled_race_count,
                summary.settled_purchase_race_count,
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
            (3, 1, 1, 1, 1, 2, 1, 1, 1, 100, 300, 200, Decimal("300"), Decimal("100"), Decimal("100"), 0),
        )
        by_type = summary.by_bet_type[WIN]
        self.assertEqual(
            (
                by_type.bet_count,
                by_type.settled_bet_count,
                by_type.hit_bet_count,
                by_type.investment,
                by_type.payout,
                by_type.profit,
                by_type.roi,
                by_type.bet_hit_rate,
            ),
            (2, 1, 1, 100, 300, 200, Decimal("300"), Decimal("100")),
        )

    def test_multi_race_saved_plan_round_trip_to_summary(self) -> None:
        inputs = (
            self.race_input(101, scheduled_start_at=datetime(2026, 8, 1, 10, 0, tzinfo=UTC)),
            self.race_input(102, scheduled_start_at=datetime(2026, 8, 1, 11, 0, tzinfo=UTC)),
            self.race_input(103, scheduled_start_at=datetime(2026, 8, 1, 12, 0, tzinfo=UTC)),
            self.race_input(104, scheduled_start_at=datetime(2026, 8, 1, 13, 0, tzinfo=UTC)),
        )
        snapshots = (
            self.save_snapshot(inputs[0], include_bet=True),
            self.save_snapshot(inputs[1], include_bet=True),
            self.save_snapshot(inputs[2], include_bet=False),
            self.save_snapshot(inputs[3], include_bet=True),
        )
        self.assertEqual(tuple(len(snapshot.bets) for snapshot in snapshots), (1, 1, 0, 1))

        result_one_finalized_at = datetime(2026, 8, 1, 14, 0, tzinfo=UTC)
        result_two_finalized_at = datetime(2026, 8, 1, 15, 0, tzinfo=UTC)
        result_four_finalized_at = datetime(2026, 8, 1, 16, 0, tzinfo=UTC)
        self.save_complete_race_result(101, finalized_at=result_one_finalized_at)
        self.save_complete_race_result(102, finalized_at=result_two_finalized_at)
        self.save_complete_race_result(104, finalized_at=result_four_finalized_at)
        self.save_payout(
            101,
            is_complete=True,
            finalized_at=datetime(2026, 8, 1, 14, 10, tzinfo=UTC),
            entries=(PayoutRecord((self.horse_id_for(101),), 300, PayoutStatus.WINNING),),
        )
        self.save_payout(
            102,
            is_complete=True,
            finalized_at=datetime(2026, 8, 1, 15, 10, tzinfo=UTC),
            entries=(),
        )
        self.save_payout(104, is_complete=False, finalized_at=None, entries=())

        simulator, executor = self.simulator()
        results = tuple(executor(race_input=race_input) for race_input in inputs)
        summary = simulator.run(race_inputs=inputs)

        first, second, third, fourth = results
        self.assertEqual(
            (
                first.race_id,
                first.settlement_status,
                first.exclusion_reason,
                first.planned_investment,
                first.settled_investment,
                first.payout,
                first.profit,
                first.hit_bet_count,
            ),
            (101, SettlementStatus.SETTLED, None, 100, 100, 300, 200, 1),
        )
        self.assertEqual(
            (
                second.race_id,
                second.settlement_status,
                second.exclusion_reason,
                second.planned_investment,
                second.settled_investment,
                second.payout,
                second.profit,
                second.hit_bet_count,
            ),
            (102, SettlementStatus.SETTLED, None, 100, 100, 0, -100, 0),
        )
        self.assertEqual((third.race_id, third.settlement_status, third.planned_investment), (103, SettlementStatus.NO_BET, 0))
        self.assertEqual(
            (
                fourth.race_id,
                fourth.settlement_status,
                fourth.exclusion_reason,
                fourth.planned_investment,
                fourth.settled_investment,
                fourth.payout,
                fourth.profit,
                fourth.hit_bet_count,
            ),
            (104, SettlementStatus.UNSETTLED, "missing_payout_publication", 100, None, None, None, 0),
        )
        self.assertLess(first.settled_at, second.settled_at)

        self.assertEqual(summary.race_count, 4)
        self.assertEqual(summary.settled_race_count, 2)
        self.assertEqual(summary.no_bet_race_count, 1)
        self.assertEqual(summary.unsettled_race_count, 1)
        self.assertEqual((summary.void_race_count, summary.error_race_count, summary.unsupported_race_count), (0, 0, 0))
        self.assertEqual((summary.settled_purchase_race_count, summary.bet_count, summary.settled_bet_count), (2, 3, 2))
        self.assertEqual((summary.hit_bet_count, summary.hit_race_count), (1, 1))
        self.assertEqual((summary.investment, summary.payout, summary.profit, summary.maximum_drawdown), (200, 300, 100, 100))
        self.assertEqual(summary.roi, Decimal("150"))
        self.assertEqual(summary.bet_hit_rate, Decimal("50"))
        self.assertEqual(summary.race_hit_rate, Decimal("50"))
        by_type = summary.by_bet_type[WIN]
        self.assertEqual(
            (
                by_type.bet_count,
                by_type.settled_bet_count,
                by_type.hit_bet_count,
                by_type.investment,
                by_type.payout,
                by_type.profit,
                by_type.roi,
                by_type.bet_hit_rate,
            ),
            (3, 2, 1, 200, 300, 100, Decimal("150"), Decimal("50")),
        )

    def test_missing_race_result_from_saved_non_empty_snapshot_is_unsettled(self) -> None:
        race_input = self.race_input(105)
        self.save_snapshot(race_input, include_bet=True)
        simulator, _executor = self.simulator()

        summary = simulator.run(race_inputs=(race_input,))

        self.assertEqual(
            (
                summary.race_count,
                summary.unsettled_race_count,
                summary.bet_count,
                summary.settled_bet_count,
                summary.investment,
                summary.payout,
                summary.profit,
            ),
            (1, 1, 1, 0, 0, 0, 0),
        )
        _simulator, executor = self.simulator()
        result = executor(race_input=race_input)
        self.assertEqual(result.settlement_status, SettlementStatus.UNSETTLED)
        self.assertEqual(result.exclusion_reason, "missing_race_result")
        self.assertEqual((result.planned_investment, result.settled_investment, result.payout, result.profit), (100, None, None, None))

    def test_snapshot_natural_identity_mismatch_fails_closed(self) -> None:
        saved_input = self.race_input(101)
        self.save_snapshot(saved_input, include_bet=True)
        different_context = SimulationRunContext(
            run_id="different-integration-run",
            dataset_id=self.run_context.dataset_id,
            started_at=self.run_context.started_at,
            target_commit_id=self.run_context.target_commit_id,
        )
        different_strategy = build_strategy_identity(
            "OtherPersistedIntegrationStrategy",
            StrategyConfig(allocation_policy=self.policy_config),
        )
        cases = (
            ("run_id", different_context, self.strategy_identity, saved_input),
            ("race_id", self.run_context, self.strategy_identity, self.race_input(106)),
            (
                "information_cutoff",
                self.run_context,
                self.strategy_identity,
                self.race_input(
                    101,
                    information_cutoff=INFORMATION_CUTOFF + timedelta(minutes=30),
                    scheduled_start_at=INFORMATION_CUTOFF + timedelta(hours=2),
                ),
            ),
            ("strategy_identity", self.run_context, different_strategy, saved_input),
        )

        for name, context, strategy, requested_input in cases:
            with self.subTest(identity_difference=name):
                simulator, _executor = self.simulator(
                    run_context=context,
                    strategy_identity=strategy,
                )
                with self.assertRaises(SimulationValidationError) as raised:
                    simulator.run(race_inputs=(requested_input,))
                self.assertEqual(raised.exception.input_identifier, "simulation_bet_plan_snapshot")
