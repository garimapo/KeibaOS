"""Contracts for the persisted multi-race simulation run service."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
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
    def __init__(self, *, events: list[str] | None = None) -> None:
        self.saved: dict[SimulationBetPlanIdentity, SimulationBetPlanSnapshot] = {}
        self.save_calls: list[SimulationBetPlanSnapshot] = []
        self.load_calls: list[SimulationBetPlanIdentity] = []
        self._events = events

    def save_snapshot(self, *, snapshot: SimulationBetPlanSnapshot) -> None:
        self.save_calls.append(snapshot)
        self.saved[snapshot.identity] = snapshot
        if self._events is not None:
            self._events.append(f"plan:{snapshot.identity.race_id}")

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
    def __init__(self, *, events: list[str] | None = None) -> None:
        self.calls: list[int] = []
        self.error: BaseException | None = None
        self.error_by_race_id: dict[int, BaseException] = {}
        self._events = events

    def get_race_result(self, race_id: int) -> PersistedRaceResult | None:
        self.calls.append(race_id)
        if self._events is not None:
            self._events.append(f"settle:{race_id}")
        race_error = self.error_by_race_id.get(race_id)
        if race_error is not None:
            raise race_error
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


class PersistedSimulationBetPlanServiceSubclass(PersistedSimulationBetPlanService):
    pass


class SimulatorSubclass(Simulator):
    pass


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

    def _components(
        self,
        *,
        events: list[str] | None = None,
    ) -> tuple[
        PersistedSimulationRunService,
        MemorySnapshotRepository,
        RecordingAllocator,
        RecordingRaceResultRepository,
        RecordingPayoutRepository,
        PersistedRaceSimulationExecutor,
        PersistedSimulationBetPlanService,
        Simulator,
        PersistedSimulationBetSource,
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
        snapshots = MemorySnapshotRepository(events=events)
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
        race_results = RecordingRaceResultRepository(events=events)
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
            bet_plan_service,
            simulator,
            bet_source,
        )

    def _assert_no_activity(
        self,
        *,
        snapshots: MemorySnapshotRepository,
        allocator: RecordingAllocator,
        race_results: RecordingRaceResultRepository,
        payouts: RecordingPayoutRepository,
    ) -> None:
        self.assertEqual(snapshots.save_calls, [])
        self.assertEqual(allocator.calls, [])
        self.assertEqual(race_results.calls, [])
        self.assertEqual(payouts.calls, [])

    def _other_run_context(self) -> SimulationRunContext:
        return SimulationRunContext(
            run_id="other-run-service-contract",
            dataset_id="fixture-dataset",
            started_at=STARTED_AT,
            target_commit_id="fixture-commit",
        )

    def test_public_api_slots_and_constructor_make_no_collaborator_calls(self) -> None:
        self.assertEqual(
            PersistedSimulationRunService.__module__,
            "scripts.simulation.persisted_simulation_run_service",
        )
        self.assertTrue(inspect.isclass(PersistedSimulationRunService))
        self.assertEqual(PersistedSimulationRunService.__bases__, (object,))
        signature = inspect.signature(PersistedSimulationRunService.__init__)
        self.assertEqual(tuple(signature.parameters), ("self", "bet_plan_service", "simulator"))
        self.assertTrue(all(parameter.kind is inspect.Parameter.KEYWORD_ONLY for name, parameter in signature.parameters.items() if name != "self"))
        constructor_hints = get_type_hints(PersistedSimulationRunService.__init__)
        self.assertIs(
            constructor_hints["bet_plan_service"],
            PersistedSimulationBetPlanService,
        )
        self.assertIs(constructor_hints["simulator"], Simulator)
        self.assertIs(constructor_hints["return"], type(None))
        run_signature = inspect.signature(PersistedSimulationRunService.run)
        self.assertEqual(tuple(run_signature.parameters), ("self", "race_inputs", "budgets_by_race_id"))
        self.assertTrue(
            all(
                parameter.kind is inspect.Parameter.KEYWORD_ONLY
                for name, parameter in run_signature.parameters.items()
                if name != "self"
            )
        )
        run_hints = get_type_hints(PersistedSimulationRunService.run)
        self.assertEqual(run_hints["race_inputs"], Sequence[SimulationRaceInput])
        self.assertEqual(run_hints["budgets_by_race_id"], Mapping[int, BetStakeBudget])
        self.assertIs(run_hints["return"], SimulationSummary)
        self.assertEqual(PersistedSimulationRunService.__slots__, ("_bet_plan_service", "_simulator"))

        service, snapshots, allocator, race_results, payouts, _executor, *_ = self._components()
        self.assertFalse(hasattr(service, "__dict__"))
        self.assertEqual(snapshots.save_calls, [])
        self.assertEqual(allocator.calls, [])
        self.assertEqual(race_results.calls, [])
        self.assertEqual(payouts.calls, [])

    def test_constructor_rejects_non_exact_top_level_dependencies_without_calls(self) -> None:
        cases = (
            (
                "bet-plan-service subclass",
                lambda bet_plan_service, simulator: (
                    PersistedSimulationBetPlanServiceSubclass.__new__(
                        PersistedSimulationBetPlanServiceSubclass
                    ),
                    simulator,
                ),
                "bet_plan_service must be a PersistedSimulationBetPlanService",
            ),
            (
                "simulator subclass",
                lambda bet_plan_service, simulator: (
                    bet_plan_service,
                    SimulatorSubclass.__new__(SimulatorSubclass),
                ),
                "simulator must be a Simulator",
            ),
            (
                "none bet-plan-service",
                lambda _bet_plan_service, simulator: (None, simulator),
                "bet_plan_service must be a PersistedSimulationBetPlanService",
            ),
            (
                "object bet-plan-service",
                lambda _bet_plan_service, simulator: (object(), simulator),
                "bet_plan_service must be a PersistedSimulationBetPlanService",
            ),
            (
                "none simulator",
                lambda bet_plan_service, _simulator: (bet_plan_service, None),
                "simulator must be a Simulator",
            ),
            (
                "object simulator",
                lambda bet_plan_service, _simulator: (bet_plan_service, object()),
                "simulator must be a Simulator",
            ),
        )
        for name, build_arguments, reason in cases:
            with self.subTest(name=name):
                (
                    _service,
                    snapshots,
                    allocator,
                    race_results,
                    payouts,
                    _executor,
                    bet_plan_service,
                    simulator,
                    _bet_source,
                ) = self._components()
                invalid_bet_plan_service, invalid_simulator = build_arguments(
                    bet_plan_service,
                    simulator,
                )
                with self.assertRaisesRegex(ValueError, reason):
                    PersistedSimulationRunService(
                        bet_plan_service=invalid_bet_plan_service,
                        simulator=invalid_simulator,
                    )
                self._assert_no_activity(
                    snapshots=snapshots,
                    allocator=allocator,
                    race_results=race_results,
                    payouts=payouts,
                )

    def test_constructor_rejects_persisted_component_chain_miswiring_without_calls(self) -> None:
        cases = (
            (
                "executor",
                lambda simulator, _executor, _settlement_source: object.__setattr__(
                    simulator,
                    "_race_executor",
                    object(),
                ),
                "simulator.race_executor must be a PersistedRaceSimulationExecutor",
            ),
            (
                "settlement source",
                lambda _simulator, executor, _settlement_source: object.__setattr__(
                    executor,
                    "_settlement_source",
                    object(),
                ),
                "executor.settlement_source must be a RepositoryBackedPersistedRaceSettlementSource",
            ),
            (
                "bet source",
                lambda _simulator, _executor, settlement_source: object.__setattr__(
                    settlement_source,
                    "_bet_source",
                    object(),
                ),
                "settlement_source.bet_source must be a PersistedSimulationBetSource",
            ),
        )
        for name, break_chain, reason in cases:
            with self.subTest(name=name):
                (
                    _service,
                    snapshots,
                    allocator,
                    race_results,
                    payouts,
                    executor,
                    bet_plan_service,
                    simulator,
                    _bet_source,
                ) = self._components()
                settlement_source = executor.settlement_source
                break_chain(simulator, executor, settlement_source)
                with self.assertRaisesRegex(ValueError, reason):
                    PersistedSimulationRunService(
                        bet_plan_service=bet_plan_service,
                        simulator=simulator,
                    )
                self._assert_no_activity(
                    snapshots=snapshots,
                    allocator=allocator,
                    race_results=race_results,
                    payouts=payouts,
                )

    def test_constructor_rejects_each_identity_mismatch_without_calls(self) -> None:
        cases = (
            (
                "plan-service and simulator strategy",
                lambda bet_plan_service, _simulator, _executor, _bet_source: object.__setattr__(
                    bet_plan_service,
                    "_strategy_identity",
                    build_strategy_identity("Other", self.strategy_config),
                ),
                "bet_plan_service.strategy_identity must be simulator.strategy_identity",
            ),
            (
                "simulator and executor strategy",
                lambda _bet_plan_service, _simulator, executor, _bet_source: object.__setattr__(
                    executor,
                    "_strategy_identity",
                    build_strategy_identity("Other", self.strategy_config),
                ),
                "simulator.strategy_identity must be executor.strategy_identity",
            ),
            (
                "plan-service and bet-source run context",
                lambda _bet_plan_service, _simulator, _executor, bet_source: object.__setattr__(
                    bet_source,
                    "_run_context",
                    self._other_run_context(),
                ),
                "bet_plan_service.run_context must be bet_source.run_context",
            ),
        )
        for name, break_identity, reason in cases:
            with self.subTest(name=name):
                (
                    _service,
                    snapshots,
                    allocator,
                    race_results,
                    payouts,
                    executor,
                    bet_plan_service,
                    simulator,
                    bet_source,
                ) = self._components()
                break_identity(bet_plan_service, simulator, executor, bet_source)
                with self.assertRaisesRegex(ValueError, reason):
                    PersistedSimulationRunService(
                        bet_plan_service=bet_plan_service,
                        simulator=simulator,
                    )
                self._assert_no_activity(
                    snapshots=snapshots,
                    allocator=allocator,
                    race_results=race_results,
                    payouts=payouts,
                )

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
                service, snapshots, allocator, race_results, payouts, _executor, *_ = self._components()
                with self.assertRaises(ValueError):
                    service.run(race_inputs=race_inputs, budgets_by_race_id=budgets)
                self.assertEqual(snapshots.save_calls, [])
                self.assertEqual(allocator.calls, [])
                self.assertEqual(race_results.calls, [])
                self.assertEqual(payouts.calls, [])

    def test_race_input_container_validation_is_fail_closed_and_non_mutating(self) -> None:
        valid_race = self._race_input(101, scheduled_start_at=CUTOFF + timedelta(hours=2))
        valid_budget = BetStakeBudget(100)
        invalid_containers = (
            None,
            1,
            object(),
            "race-inputs",
            b"race-inputs",
            bytearray(b"race-inputs"),
            {101: valid_race},
            (race_input for race_input in (valid_race,)),
        )
        for race_inputs in invalid_containers:
            with self.subTest(container_type=type(race_inputs).__name__):
                service, snapshots, allocator, race_results, payouts, _executor, *_ = self._components()
                with self.assertRaisesRegex(ValueError, "race_inputs must be a Sequence"):
                    service.run(
                        race_inputs=race_inputs,
                        budgets_by_race_id={101: valid_budget},
                    )
                self._assert_no_activity(
                    snapshots=snapshots,
                    allocator=allocator,
                    race_results=race_results,
                    payouts=payouts,
                )

        list_inputs = [valid_race]
        tuple_inputs = (valid_race,)
        for race_inputs in (list_inputs, tuple_inputs):
            with self.subTest(valid_container_type=type(race_inputs).__name__):
                before = tuple(race_inputs)
                service, _snapshots, _allocator, _race_results, _payouts, _executor, *_ = self._components()
                service.run(
                    race_inputs=race_inputs,
                    budgets_by_race_id={101: valid_budget},
                )
                self.assertEqual(tuple(race_inputs), before)

    def test_budget_validation_is_fail_closed_before_planning_or_settlement(self) -> None:
        valid_race = self._race_input(101, scheduled_start_at=CUTOFF + timedelta(hours=2))
        valid_budget = BetStakeBudget(100)
        invalid_budget_mappings = (
            None,
            [(101, valid_budget)],
            ((101, valid_budget),),
            ((pair for pair in ((101, valid_budget),))),
            object(),
            {True: valid_budget},
            {False: valid_budget},
            {0: valid_budget},
            {-1: valid_budget},
            {1.0: valid_budget},
            {"101": valid_budget},
            {object(): valid_budget},
            {101: None},
            {101: 100},
            {101: object()},
            {},
            {101: valid_budget, 102: BetStakeBudget(100)},
        )
        for budgets in invalid_budget_mappings:
            with self.subTest(budgets_type=type(budgets).__name__, budgets=repr(budgets)):
                service, snapshots, allocator, race_results, payouts, _executor, *_ = self._components()
                with self.assertRaises(ValueError):
                    service.run(race_inputs=(valid_race,), budgets_by_race_id=budgets)
                self._assert_no_activity(
                    snapshots=snapshots,
                    allocator=allocator,
                    race_results=race_results,
                    payouts=payouts,
                )

        service, snapshots, allocator, race_results, payouts, _executor, *_ = self._components()
        with self.assertRaises(ValueError):
            service.run(race_inputs=(), budgets_by_race_id={101: valid_budget})
        self._assert_no_activity(
            snapshots=snapshots,
            allocator=allocator,
            race_results=race_results,
            payouts=payouts,
        )

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
        events: list[str] = []
        service, snapshots, allocator, race_results, _payouts, _executor, *_ = self._components(events=events)

        summary = service.run(race_inputs=caller_inputs, budgets_by_race_id=budgets)

        self.assertEqual(caller_inputs, [first, third, second])
        self.assertEqual([snapshot.identity.race_id for snapshot in snapshots.save_calls], [102, 103, 101])
        self.assertEqual([call["identity"].race_id for call in allocator.calls], [102, 103, 101])
        self.assertIs(allocator.calls[0]["budget"], budgets[102])
        self.assertIs(allocator.calls[1]["budget"], budgets[103])
        self.assertIs(allocator.calls[2]["budget"], budgets[101])
        self.assertEqual(race_results.calls, [102, 103, 101])
        self.assertEqual(
            events,
            ["plan:102", "plan:103", "plan:101", "settle:102", "settle:103", "settle:101"],
        )
        self.assertIs(type(summary), SimulationSummary)
        self.assertEqual(summary.race_count, 3)

    def test_empty_run_calls_simulator_once_after_zero_planning(self) -> None:
        service, snapshots, allocator, race_results, payouts, _executor, *_ = self._components()

        summary = service.run(race_inputs=(), budgets_by_race_id={})

        self.assertEqual(snapshots.save_calls, [])
        self.assertEqual(allocator.calls, [])
        self.assertEqual(race_results.calls, [])
        self.assertEqual(payouts.calls, [])
        self.assertEqual(summary.race_count, 0)
        self.assertEqual(summary.bet_count, 0)
        self.assertEqual(summary.investment, 0)
        self.assertEqual(summary.payout, 0)
        self.assertEqual(summary.profit, 0)
        self.assertIsNone(summary.roi)
        self.assertIsNone(summary.race_hit_rate)
        self.assertEqual(summary.maximum_drawdown, 0)
        self.assertEqual(dict(summary.by_bet_type), {})

    def test_planning_failure_preserves_prior_snapshot_and_skips_simulation(self) -> None:
        first = self._race_input(101, scheduled_start_at=CUTOFF + timedelta(hours=1))
        second = self._race_input(102, scheduled_start_at=CUTOFF + timedelta(hours=2))
        third = self._race_input(103, scheduled_start_at=CUTOFF + timedelta(hours=3))
        error = RuntimeError("allocator failure")
        service, snapshots, allocator, race_results, payouts, _executor, *_ = self._components()
        allocator.error_by_race_id[102] = error

        with self.assertRaises(RuntimeError) as raised:
            service.run(
                race_inputs=(third, second, first),
                budgets_by_race_id={
                    101: BetStakeBudget(100),
                    102: BetStakeBudget(100),
                    103: BetStakeBudget(100),
                },
            )

        self.assertIs(raised.exception, error)
        self.assertEqual([snapshot.identity.race_id for snapshot in snapshots.save_calls], [101])
        self.assertEqual([call["identity"].race_id for call in allocator.calls], [101, 102])
        self.assertEqual(race_results.calls, [])
        self.assertEqual(payouts.calls, [])

    def test_simulator_failure_propagates_after_all_snapshots_are_saved(self) -> None:
        first = self._race_input(101, scheduled_start_at=CUTOFF + timedelta(hours=1))
        second = self._race_input(102, scheduled_start_at=CUTOFF + timedelta(hours=2))
        third = self._race_input(103, scheduled_start_at=CUTOFF + timedelta(hours=3))
        error = RuntimeError("settlement failure")
        service, snapshots, _allocator, race_results, _payouts, _executor, *_ = self._components()
        race_results.error_by_race_id[102] = error

        with self.assertRaises(RuntimeError) as raised:
            service.run(
                race_inputs=(third, second, first),
                budgets_by_race_id={
                    101: BetStakeBudget(100),
                    102: BetStakeBudget(100),
                    103: BetStakeBudget(100),
                },
            )

        self.assertIs(raised.exception, error)
        self.assertEqual(
            [snapshot.identity.race_id for snapshot in snapshots.save_calls],
            [101, 102, 103],
        )
        self.assertEqual(race_results.calls, [101, 102])

    def test_run_revalidates_each_identity_relationship_before_planning(self) -> None:
        race_input = self._race_input(101, scheduled_start_at=CUTOFF + timedelta(hours=1))
        cases = (
            (
                "plan-service and simulator strategy",
                lambda bet_plan_service, _executor, _bet_source: object.__setattr__(
                    bet_plan_service,
                    "_strategy_identity",
                    build_strategy_identity("Other", self.strategy_config),
                ),
                "bet_plan_service.strategy_identity must be simulator.strategy_identity",
            ),
            (
                "simulator and executor strategy",
                lambda _bet_plan_service, executor, _bet_source: object.__setattr__(
                    executor,
                    "_strategy_identity",
                    build_strategy_identity("Other", self.strategy_config),
                ),
                "simulator.strategy_identity must be executor.strategy_identity",
            ),
            (
                "plan-service and bet-source run context",
                lambda _bet_plan_service, _executor, bet_source: object.__setattr__(
                    bet_source,
                    "_run_context",
                    self._other_run_context(),
                ),
                "bet_plan_service.run_context must be bet_source.run_context",
            ),
        )
        for name, break_identity, reason in cases:
            with self.subTest(name=name):
                (
                    service,
                    snapshots,
                    allocator,
                    race_results,
                    payouts,
                    executor,
                    bet_plan_service,
                    _simulator,
                    bet_source,
                ) = self._components()
                break_identity(bet_plan_service, executor, bet_source)
                with self.assertRaisesRegex(ValueError, reason):
                    service.run(
                        race_inputs=(race_input,),
                        budgets_by_race_id={101: BetStakeBudget(100)},
                    )
                self._assert_no_activity(
                    snapshots=snapshots,
                    allocator=allocator,
                    race_results=race_results,
                    payouts=payouts,
                )
