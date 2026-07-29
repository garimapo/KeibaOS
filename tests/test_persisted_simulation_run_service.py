"""Contracts for the persisted multi-race simulation run service."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
import inspect
from typing import get_type_hints
import unittest

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
from scripts.simulation.bet_plan_builder import SimulationBetPlanBuilder
from scripts.simulation.bet_plan_identity import SimulationBetPlanIdentity
from scripts.simulation.bet_plan_snapshot import SimulationBetPlanSnapshot
from scripts.simulation.fixed_stake_allocator import FixedStakeBetAllocator
from scripts.simulation.models import (
    InputAuditEntry,
    InputSnapshotAudit,
    SimulationRaceInput,
    SimulationRunContext,
    SimulationSummary,
    StrategyIdentity,
    build_strategy_identity,
)
from scripts.simulation.persisted_bet_plan_service import PersistedSimulationBetPlanService
from scripts.simulation.persisted_executor import PersistedRaceSimulationExecutor
from scripts.simulation.persisted_simulation_bet_source import PersistedSimulationBetSource
from scripts.simulation.persisted_simulation_run_service import PersistedSimulationRunService
from scripts.simulation.repositories.interfaces import PayoutPublication, PersistedRaceResult
from scripts.simulation.repository_backed_persisted_settlement_source import (
    RepositoryBackedPersistedRaceSettlementSource,
)
from scripts.simulation.simulator import Simulator
from scripts.simulation.stake_allocation import BetStakeBudget


STARTED_AT = datetime(2026, 8, 3, 8, 0, tzinfo=UTC)
CUTOFF = datetime(2026, 8, 3, 9, 0, tzinfo=UTC)


class MemorySnapshotRepository:
    def __init__(self) -> None:
        self.saved: dict[SimulationBetPlanIdentity, SimulationBetPlanSnapshot] = {}
        self.save_calls: list[SimulationBetPlanSnapshot] = []
        self.load_calls: list[SimulationBetPlanIdentity] = []

    def save_snapshot(self, *, snapshot: SimulationBetPlanSnapshot) -> None:
        self.save_calls.append(snapshot)
        self.saved[snapshot.identity] = snapshot

    def load_snapshot(
        self,
        *,
        identity: SimulationBetPlanIdentity,
    ) -> SimulationBetPlanSnapshot | None:
        self.load_calls.append(identity)
        return self.saved.get(identity)


class IdentitySelectionResolver:
    def __init__(self) -> None:
        self.calls: list[tuple[int, tuple[int, ...]]] = []

    def resolve_race_entry_ids(
        self,
        *,
        race_id: int,
        horse_ids: Sequence[int],
    ) -> tuple[int, ...]:
        values = tuple(horse_ids)
        self.calls.append((race_id, values))
        return values


class RecordingAllocator:
    def __init__(self, *, policy_config: AllocationPolicyConfig) -> None:
        self._allocator = FixedStakeBetAllocator(policy_config=policy_config)
        self.calls: list[dict[str, object]] = []
        self.error_by_race_id: dict[int, BaseException] = {}

    def allocate(self, *, identity: SimulationBetPlanIdentity, policy_identity: object, bet_plan: object, budget: BetStakeBudget) -> object:
        self.calls.append({"identity": identity, "budget": budget})
        error = self.error_by_race_id.get(identity.race_id)
        if error is not None:
            raise error
        return self._allocator.allocate(
            identity=identity,
            policy_identity=policy_identity,
            bet_plan=bet_plan,
            budget=budget,
        )


class RecordingRaceResultRepository:
    def __init__(self) -> None:
        self.calls: list[int] = []
        self.error: BaseException | None = None

    def get_race_result(self, race_id: int) -> PersistedRaceResult | None:
        self.calls.append(race_id)
        if self.error is not None:
            raise self.error
        return None


class RecordingPayoutRepository:
    def __init__(self) -> None:
        self.calls: list[tuple[int, str, datetime | None, bool]] = []

    def get_latest_payout_publication(
        self,
        race_id: int,
        bet_type: str,
        observed_at_lte: datetime | None = None,
        require_complete: bool = True,
    ) -> PayoutPublication | None:
        self.calls.append((race_id, bet_type, observed_at_lte, require_complete))
        return None


class PersistedSimulationRunServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy_config = AllocationPolicyConfig(
            policy_name="fixed_stake_per_recommendation",
            policy_version="1",
            parameters={"stake_amount": 100},
        )
        self.strategy_config = StrategyConfig(allocation_policy=self.policy_config)
        self.strategy_identity = build_strategy_identity(
            "PersistedRunService",
            self.strategy_config,
        )
        self.run_context = SimulationRunContext(
            run_id="run-service-contract",
            dataset_id="fixture-dataset",
            started_at=STARTED_AT,
            target_commit_id="fixture-commit",
        )

    def _race_input(
        self,
        race_id: int,
        *,
        scheduled_start_at: datetime,
    ) -> SimulationRaceInput:
        horse_id = race_id * 10 + 1
        pipeline_input = RacePredictionInput(
            {horse_id: []},
            {horse_id: f"Jockey {race_id}"},
            RaceTrackConditions("Tokyo", 1600, "turf", "firm"),
            {horse_id: 2.0},
            1,
            race_id,
            "fixture-prediction-time",
        )
        audit = InputSnapshotAudit(
            "fixture-dataset",
            "fixture",
            CUTOFF,
            (
                InputAuditEntry("entry", f"entry/{horse_id}", "fixture", f"entry/{horse_id}", horse_id, observed_at=CUTOFF),
                InputAuditEntry("odds", f"odds/{horse_id}", "fixture", f"odds/{horse_id}", horse_id, observed_at=CUTOFF),
                InputAuditEntry("jockey", f"jockey/{horse_id}", "fixture", f"jockey/{horse_id}", horse_id, observed_at=CUTOFF),
                InputAuditEntry("track", "track", "fixture", "track", None, observed_at=CUTOFF),
                InputAuditEntry("past_race", f"past_race/{horse_id}/none", "fixture", f"past_race/{horse_id}/none", horse_id, observed_at=CUTOFF),
            ),
            True,
        )
        return SimulationRaceInput(
            race_id,
            date(2026, 8, 3),
            scheduled_start_at,
            CUTOFF,
            pipeline_input,
            audit,
        )

    def _components(self) -> tuple[
        PersistedSimulationRunService,
        MemorySnapshotRepository,
        RecordingAllocator,
        RecordingRaceResultRepository,
        RecordingPayoutRepository,
        PersistedRaceSimulationExecutor,
    ]:
        pipeline = PredictionPipeline(
            PipelineConfig(
                ability_engine=AbilityEngine(reference_date=date(2026, 8, 3)),
                pace_engine=PaceEngine(),
                jockey_engine=JockeyEngine(reference_date=date(2026, 8, 3)),
                track_engine=TrackEngine(reference_date=date(2026, 8, 3)),
                predictor=Predictor(),
                value_engine=ValueEngine(),
                bet_generator=BetGenerator(),
                bet_strategy=RuleBasedBetStrategy(),
                strategy_config=self.strategy_config,
            )
        )
        snapshots = MemorySnapshotRepository()
        allocator = RecordingAllocator(policy_config=self.policy_config)
        plan_builder = SimulationBetPlanBuilder(
            selection_resolver=IdentitySelectionResolver(),
        )
        bet_plan_service = PersistedSimulationBetPlanService(
            run_context=self.run_context,
            strategy_identity=self.strategy_identity,
            prediction_pipeline=pipeline,
            allocator=allocator,
            plan_builder=plan_builder,
            snapshot_repository=snapshots,
        )
        bet_source = PersistedSimulationBetSource(
            run_context=self.run_context,
            snapshot_source=snapshots,
        )
        race_results = RecordingRaceResultRepository()
        payouts = RecordingPayoutRepository()
        settlement_source = RepositoryBackedPersistedRaceSettlementSource(
            bet_source=bet_source,
            race_result_repository=race_results,
            payout_repository=payouts,
        )
        executor = PersistedRaceSimulationExecutor(
            strategy_identity=self.strategy_identity,
            settlement_source=settlement_source,
        )
        simulator = Simulator(
            strategy_identity=self.strategy_identity,
            race_executor=executor,
        )
        return (
            PersistedSimulationRunService(
                bet_plan_service=bet_plan_service,
                simulator=simulator,
            ),
            snapshots,
            allocator,
            race_results,
            payouts,
            executor,
        )

    def test_public_api_slots_and_constructor_make_no_collaborator_calls(self) -> None:
        signature = inspect.signature(PersistedSimulationRunService.__init__)
        self.assertEqual(tuple(signature.parameters), ("self", "bet_plan_service", "simulator"))
        self.assertTrue(all(parameter.kind is inspect.Parameter.KEYWORD_ONLY for name, parameter in signature.parameters.items() if name != "self"))
        self.assertEqual(tuple(inspect.signature(PersistedSimulationRunService.run).parameters), ("self", "race_inputs", "budgets_by_race_id"))
        hints = get_type_hints(PersistedSimulationRunService.run)
        self.assertIs(hints["return"], SimulationSummary)
        self.assertEqual(PersistedSimulationRunService.__slots__, ("_bet_plan_service", "_simulator"))

        service, snapshots, allocator, race_results, payouts, _executor = self._components()
        self.assertFalse(hasattr(service, "__dict__"))
        self.assertEqual(snapshots.save_calls, [])
        self.assertEqual(allocator.calls, [])
        self.assertEqual(race_results.calls, [])
        self.assertEqual(payouts.calls, [])

    def test_validation_failures_have_no_side_effects(self) -> None:
        valid_race = self._race_input(101, scheduled_start_at=CUTOFF + timedelta(hours=2))
        valid_budget = BetStakeBudget(100)
        invalid_cases = (
            ("text", {101: valid_budget}),
            ({101: valid_race}, {101: valid_budget}),
            ((valid_race, object()), {101: valid_budget}),
            ((valid_race, valid_race), {101: valid_budget}),
            ((valid_race,), [(101, valid_budget)]),
            ((valid_race,), {True: valid_budget}),
            ((valid_race,), {101: object()}),
            ((valid_race,), {}),
            ((), {101: valid_budget}),
        )
        for race_inputs, budgets in invalid_cases:
            with self.subTest(race_inputs_type=type(race_inputs).__name__):
                service, snapshots, allocator, race_results, payouts, _executor = self._components()
                with self.assertRaises(ValueError):
                    service.run(race_inputs=race_inputs, budgets_by_race_id=budgets)
                self.assertEqual(snapshots.save_calls, [])
                self.assertEqual(allocator.calls, [])
                self.assertEqual(race_results.calls, [])
                self.assertEqual(payouts.calls, [])

    def test_orders_planning_and_simulation_and_preserves_exact_input_objects(self) -> None:
        first = self._race_input(101, scheduled_start_at=CUTOFF + timedelta(hours=3))
        second = self._race_input(102, scheduled_start_at=CUTOFF + timedelta(hours=1))
        third = self._race_input(103, scheduled_start_at=CUTOFF + timedelta(hours=1))
        caller_inputs = [first, third, second]
        budgets = {
            101: BetStakeBudget(100),
            102: BetStakeBudget(100),
            103: BetStakeBudget(100),
        }
        service, snapshots, allocator, race_results, _payouts, _executor = self._components()

        summary = service.run(race_inputs=caller_inputs, budgets_by_race_id=budgets)

        self.assertEqual(caller_inputs, [first, third, second])
        self.assertEqual([snapshot.identity.race_id for snapshot in snapshots.save_calls], [102, 103, 101])
        self.assertEqual([call["identity"].race_id for call in allocator.calls], [102, 103, 101])
        self.assertIs(allocator.calls[0]["budget"], budgets[102])
        self.assertIs(allocator.calls[1]["budget"], budgets[103])
        self.assertIs(allocator.calls[2]["budget"], budgets[101])
        self.assertEqual(race_results.calls, [102, 103, 101])
        self.assertIs(type(summary), SimulationSummary)
        self.assertEqual(summary.race_count, 3)

    def test_empty_run_calls_simulator_once_after_zero_planning(self) -> None:
        service, snapshots, allocator, race_results, payouts, _executor = self._components()

        summary = service.run(race_inputs=(), budgets_by_race_id={})

        self.assertEqual(snapshots.save_calls, [])
        self.assertEqual(allocator.calls, [])
        self.assertEqual(race_results.calls, [])
        self.assertEqual(payouts.calls, [])
        self.assertEqual(summary.race_count, 0)

    def test_planning_failure_preserves_prior_snapshot_and_skips_simulation(self) -> None:
        first = self._race_input(101, scheduled_start_at=CUTOFF + timedelta(hours=1))
        second = self._race_input(102, scheduled_start_at=CUTOFF + timedelta(hours=2))
        error = RuntimeError("allocator failure")
        service, snapshots, allocator, race_results, _payouts, _executor = self._components()
        allocator.error_by_race_id[102] = error

        with self.assertRaises(RuntimeError) as raised:
            service.run(
                race_inputs=(second, first),
                budgets_by_race_id={101: BetStakeBudget(100), 102: BetStakeBudget(100)},
            )

        self.assertIs(raised.exception, error)
        self.assertEqual([snapshot.identity.race_id for snapshot in snapshots.save_calls], [101])
        self.assertEqual(race_results.calls, [])

    def test_simulator_failure_propagates_after_all_snapshots_are_saved(self) -> None:
        race_input = self._race_input(101, scheduled_start_at=CUTOFF + timedelta(hours=1))
        error = RuntimeError("settlement failure")
        service, snapshots, _allocator, race_results, _payouts, _executor = self._components()
        race_results.error = error

        with self.assertRaises(RuntimeError) as raised:
            service.run(race_inputs=(race_input,), budgets_by_race_id={101: BetStakeBudget(100)})

        self.assertIs(raised.exception, error)
        self.assertEqual([snapshot.identity.race_id for snapshot in snapshots.save_calls], [101])
        self.assertEqual(race_results.calls, [101])

    def test_run_revalidates_composition_before_planning(self) -> None:
        race_input = self._race_input(101, scheduled_start_at=CUTOFF + timedelta(hours=1))
        service, snapshots, allocator, race_results, _payouts, executor = self._components()
        other_identity = build_strategy_identity("Other", self.strategy_config)
        object.__setattr__(executor, "_strategy_identity", other_identity)

        with self.assertRaisesRegex(
            ValueError,
            "simulator.strategy_identity must be executor.strategy_identity",
        ):
            service.run(race_inputs=(race_input,), budgets_by_race_id={101: BetStakeBudget(100)})
        self.assertEqual(snapshots.save_calls, [])
        self.assertEqual(allocator.calls, [])
        self.assertEqual(race_results.calls, [])
