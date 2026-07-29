"""Unit contracts for one-race prediction-to-snapshot persistence."""

from __future__ import annotations

import ast
from datetime import UTC, date, datetime, timedelta
import inspect
from typing import get_type_hints
import unittest

import scripts.simulation as simulation_package
from scripts.models import Prediction
from scripts.prediction.allocation_policy import (
    AllocationPolicyConfig,
    build_allocation_policy_identity,
)
from scripts.prediction.bet_generator import BetGenerator, BetRecommendation
from scripts.prediction.bet_strategy import BetPlan, StrategyConfig
from scripts.prediction.prediction_pipeline import (
    PipelineConfig,
    PipelineExecutionError,
    PipelineResult,
    PipelineStage,
    PredictionPipeline,
    RacePredictionInput,
)
from scripts.prediction.track_engine import RaceTrackConditions
from scripts.simulation.bet_plan_builder import SimulationBetPlanBuilder
from scripts.simulation.bet_plan_identity import SimulationBetPlanIdentity
from scripts.simulation.bet_plan_snapshot import SimulationBetPlanSnapshot
from scripts.simulation.bet_plan_snapshot_repository import (
    SimulationBetPlanSnapshotRepository,
)
from scripts.simulation.models import (
    InputAuditEntry,
    InputSnapshotAudit,
    SimulationBet,
    SimulationRaceInput,
    SimulationRunContext,
    StrategyIdentity,
    build_strategy_identity,
)
from scripts.simulation.persisted_bet_plan_service import (
    PersistedSimulationBetPlanService,
)
from scripts.simulation.repositories.errors import (
    RepositoryConflictError,
    RepositoryDataIntegrityError,
    RepositoryValidationError,
)
from scripts.simulation.stake_allocation import (
    AllocatedBetRecommendation,
    BetAllocationPlan,
    BetStakeAllocator,
    BetStakeBudget,
)
from scripts.simulation.validation import SimulationValidationError


RUN_STARTED_AT = datetime(2026, 8, 1, 8, 0, tzinfo=UTC)
INFORMATION_CUTOFF = datetime(2026, 8, 1, 9, 0, tzinfo=UTC)
RACE_ID = 501
RACE_ENTRY_ID = 7001


def _typing_module_aliases(tree: ast.AST) -> set[str]:
    return {
        alias.asname or alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
        if alias.name == "typing"
    }


def _uses_forbidden_typing_attribute(
    tree: ast.AST,
    *,
    names: set[str],
) -> bool:
    aliases = _typing_module_aliases(tree)
    return any(
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id in aliases
        and node.attr in names
        for node in ast.walk(tree)
    )


class RecordingPipeline(PredictionPipeline):
    """Concrete Pipeline subclass used to isolate the service boundary."""

    def __init__(
        self,
        *,
        config: object,
        response: object,
        events: list[str],
        error: BaseException | None = None,
    ) -> None:
        self.config = config
        self.response = response
        self.events = events
        self.error = error
        self.calls: list[object] = []

    def run(self, race_input: object) -> PipelineResult:
        self.events.append("pipeline")
        self.calls.append(race_input)
        if self.error is not None:
            raise self.error
        return self.response


class RecordingAllocator:
    def __init__(
        self,
        *,
        response: object,
        events: list[str],
        error: BaseException | None = None,
    ) -> None:
        self.response = response
        self.events = events
        self.error = error
        self.calls: list[dict[str, object]] = []

    def allocate(
        self,
        *,
        identity: SimulationBetPlanIdentity,
        policy_identity: object,
        bet_plan: BetPlan,
        budget: BetStakeBudget,
    ) -> object:
        self.events.append("allocator")
        self.calls.append(
            {
                "identity": identity,
                "policy_identity": policy_identity,
                "bet_plan": bet_plan,
                "budget": budget,
            }
        )
        if self.error is not None:
            raise self.error
        return self.response


class RecordingBuilder(SimulationBetPlanBuilder):
    """Concrete Builder subclass which deliberately does not resolve selections."""

    def __init__(
        self,
        *,
        response: object,
        events: list[str],
        error: BaseException | None = None,
    ) -> None:
        self.response = response
        self.events = events
        self.error = error
        self.calls: list[object] = []

    def build(self, *, allocation_plan: BetAllocationPlan) -> SimulationBetPlanSnapshot:
        self.events.append("builder")
        self.calls.append(allocation_plan)
        if self.error is not None:
            raise self.error
        return self.response


class RecordingRepository:
    def __init__(self, *, events: list[str], error: BaseException | None = None) -> None:
        self.events = events
        self.error = error
        self.calls: list[object] = []

    def save_snapshot(self, *, snapshot: SimulationBetPlanSnapshot) -> None:
        self.events.append("repository")
        self.calls.append(snapshot)
        if self.error is not None:
            raise self.error


class MissingAllocate:
    pass


class NonCallableAllocate:
    allocate = "not callable"


class MissingSaveSnapshot:
    pass


class NonCallableSaveSnapshot:
    save_snapshot = "not callable"


class PersistedSimulationBetPlanServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.events: list[str] = []
        self.policy_config = AllocationPolicyConfig(
            policy_name="fixed_stake_per_recommendation",
            policy_version="1",
            parameters={"stake_amount": 100},
        )
        self.strategy_config = StrategyConfig(allocation_policy=self.policy_config)
        self.strategy_identity = build_strategy_identity("CallerStrategy", self.strategy_config)
        self.run_context = SimulationRunContext(
            run_id="service-run",
            dataset_id="dataset-not-an-identity-field",
            started_at=RUN_STARTED_AT,
            target_commit_id="commit-not-an-identity-field",
        )
        self.race_input = self._race_input()
        self.budget = BetStakeBudget(total_amount=100)
        self.recommendation = BetRecommendation(
            rank=0,
            bet_type=BetGenerator.WIN,
            horse_ids=(RACE_ENTRY_ID,),
            estimated_probability=0.4,
            expected_value=1.2,
            combination_score=None,
            prediction_score=80.0,
        )
        self.bet_plan = BetPlan(
            strategy_name="PipelineStrategyNameIsIndependent",
            recommendations=(self.recommendation,),
            candidate_count=1,
        )
        self.pipeline_result = self._pipeline_result(self.bet_plan)
        self.identity = self._identity()
        self.policy_identity = build_allocation_policy_identity(self.policy_config)
        self.allocation_plan = BetAllocationPlan(
            identity=self.identity,
            policy_identity=self.policy_identity,
            bet_plan=self.bet_plan,
            allocations=(
                AllocatedBetRecommendation(
                    recommendation=self.recommendation,
                    purchase_order=0,
                    stake=100,
                ),
            ),
            budget=self.budget,
        )
        self.snapshot = SimulationBetPlanSnapshot(
            identity=self.identity,
            policy_identity=self.policy_identity,
            budget=self.budget,
            bets=(
                SimulationBet(
                    race_id=RACE_ID,
                    strategy_id=self.strategy_identity.strategy_id,
                    bet_type=BetGenerator.WIN,
                    race_entry_ids=(RACE_ENTRY_ID,),
                    stake=100,
                    recommendation_rank=0,
                    placed_at_cutoff=INFORMATION_CUTOFF,
                ),
            ),
        )

    def _race_input(self) -> SimulationRaceInput:
        pipeline_input = RacePredictionInput(
            horse_past_races={RACE_ENTRY_ID: []},
            jockey_names_by_horse={RACE_ENTRY_ID: "Fixture Jockey"},
            track_conditions=RaceTrackConditions("Tokyo", 1600, "turf", "firm"),
            odds_by_horse={RACE_ENTRY_ID: 2.0},
            race_horse_count=1,
            race_id=RACE_ID,
            prediction_time="pipeline-time-not-an-identity-field",
        )
        audit = InputSnapshotAudit(
            dataset_id="fixture-dataset",
            source="fixture",
            captured_at=INFORMATION_CUTOFF,
            entries=(
                InputAuditEntry("entry", f"entry/{RACE_ENTRY_ID}", "fixture", f"entry/{RACE_ENTRY_ID}", RACE_ENTRY_ID, observed_at=INFORMATION_CUTOFF),
                InputAuditEntry("odds", f"odds/{RACE_ENTRY_ID}", "fixture", f"odds/{RACE_ENTRY_ID}", RACE_ENTRY_ID, observed_at=INFORMATION_CUTOFF),
                InputAuditEntry("jockey", f"jockey/{RACE_ENTRY_ID}", "fixture", f"jockey/{RACE_ENTRY_ID}", RACE_ENTRY_ID, observed_at=INFORMATION_CUTOFF),
                InputAuditEntry("track", "track", "fixture", "track", None, observed_at=INFORMATION_CUTOFF),
                InputAuditEntry("past_race", f"past_race/{RACE_ENTRY_ID}/none", "fixture", f"past_race/{RACE_ENTRY_ID}/none", RACE_ENTRY_ID, observed_at=INFORMATION_CUTOFF),
            ),
            is_complete=True,
        )
        return SimulationRaceInput(
            race_id=RACE_ID,
            target_race_date=date(2026, 8, 1),
            scheduled_start_at=INFORMATION_CUTOFF + timedelta(hours=1),
            information_cutoff=INFORMATION_CUTOFF,
            pipeline_input=pipeline_input,
            input_snapshot_audit=audit,
        )

    def _identity(self) -> SimulationBetPlanIdentity:
        return SimulationBetPlanIdentity(
            run_id=self.run_context.run_id,
            race_id=self.race_input.race_id,
            strategy_id=self.strategy_identity.strategy_id,
            strategy_config_hash=self.strategy_identity.strategy_config_hash,
            information_cutoff=self.race_input.information_cutoff,
        )

    def _pipeline_result(self, bet_plan: BetPlan) -> PipelineResult:
        return PipelineResult(
            ability_evaluations={},
            pace_evaluation=None,
            jockey_evaluations={},
            track_evaluations={},
            predictions=(
                Prediction(
                    race_id=RACE_ID,
                    prediction_time="result-time-not-an-identity-field",
                    rank="A",
                    score=90.0,
                    buy_flag=True,
                    comment="fixture",
                    horse_id=RACE_ENTRY_ID,
                ),
            ),
            value_evaluations=(),
            recommendations=(),
            bet_plan=bet_plan,
        )

    def _service(
        self,
        *,
        pipeline_response: object | None = None,
        allocation_response: object | None = None,
        builder_response: object | None = None,
        pipeline_config: object | None = None,
        pipeline_error: BaseException | None = None,
        allocator_error: BaseException | None = None,
        builder_error: BaseException | None = None,
        repository_error: BaseException | None = None,
    ) -> tuple[
        PersistedSimulationBetPlanService,
        RecordingPipeline,
        RecordingAllocator,
        RecordingBuilder,
        RecordingRepository,
    ]:
        pipeline = RecordingPipeline(
            config=PipelineConfig(strategy_config=self.strategy_config)
            if pipeline_config is None
            else pipeline_config,
            response=self.pipeline_result if pipeline_response is None else pipeline_response,
            events=self.events,
            error=pipeline_error,
        )
        allocator = RecordingAllocator(
            response=self.allocation_plan if allocation_response is None else allocation_response,
            events=self.events,
            error=allocator_error,
        )
        builder = RecordingBuilder(
            response=self.snapshot if builder_response is None else builder_response,
            events=self.events,
            error=builder_error,
        )
        repository = RecordingRepository(events=self.events, error=repository_error)
        return (
            PersistedSimulationBetPlanService(
                run_context=self.run_context,
                strategy_identity=self.strategy_identity,
                prediction_pipeline=pipeline,
                allocator=allocator,
                plan_builder=builder,
                snapshot_repository=repository,
            ),
            pipeline,
            allocator,
            builder,
            repository,
        )

    def _assert_validation(
        self,
        raised: unittest.case._AssertRaisesContext[SimulationValidationError],
        identifier: str,
        reason: str,
    ) -> None:
        self.assertEqual(raised.exception.race_id, RACE_ID)
        self.assertEqual(raised.exception.input_identifier, identifier)
        self.assertEqual(raised.exception.reason, reason)

    def test_constructor_signature_and_type_hints_match_contract(self) -> None:
        signature = inspect.signature(PersistedSimulationBetPlanService.__init__)
        self.assertEqual(
            tuple(signature.parameters),
            (
                "self",
                "run_context",
                "strategy_identity",
                "prediction_pipeline",
                "allocator",
                "plan_builder",
                "snapshot_repository",
            ),
        )
        self.assertTrue(
            all(
                parameter.kind is inspect.Parameter.KEYWORD_ONLY
                for name, parameter in signature.parameters.items()
                if name != "self"
            )
        )
        hints = get_type_hints(PersistedSimulationBetPlanService.__init__)
        self.assertIs(hints["run_context"], SimulationRunContext)
        self.assertIs(hints["strategy_identity"], StrategyIdentity)
        self.assertIs(hints["prediction_pipeline"], PredictionPipeline)
        self.assertIs(hints["allocator"], BetStakeAllocator)
        self.assertIs(hints["plan_builder"], SimulationBetPlanBuilder)
        self.assertIs(hints["snapshot_repository"], SimulationBetPlanSnapshotRepository)

    def test_build_signature_and_type_hints_match_contract(self) -> None:
        signature = inspect.signature(PersistedSimulationBetPlanService.build_and_save)
        self.assertEqual(tuple(signature.parameters), ("self", "race_input", "budget"))
        self.assertIs(signature.parameters["race_input"].kind, inspect.Parameter.KEYWORD_ONLY)
        self.assertIs(signature.parameters["budget"].kind, inspect.Parameter.KEYWORD_ONLY)
        hints = get_type_hints(PersistedSimulationBetPlanService.build_and_save)
        self.assertIs(hints["race_input"], SimulationRaceInput)
        self.assertIs(hints["budget"], BetStakeBudget)
        self.assertIs(hints["return"], SimulationBetPlanSnapshot)

    def test_constructor_keeps_exact_dependencies_and_calls_nothing(self) -> None:
        service, pipeline, allocator, builder, repository = self._service()
        self.assertIs(service._run_context, self.run_context)
        self.assertIs(service._strategy_identity, self.strategy_identity)
        self.assertIs(service._prediction_pipeline, pipeline)
        self.assertIs(service._allocator, allocator)
        self.assertIs(service._plan_builder, builder)
        self.assertIs(service._snapshot_repository, repository)
        self.assertEqual(self.events, [])

    def test_constructor_rejects_invalid_concrete_and_structural_dependencies(self) -> None:
        service, pipeline, allocator, builder, repository = self._service()
        invalid_cases = (
            (None, self.strategy_identity, pipeline, allocator, builder, repository),
            (self.run_context, None, pipeline, allocator, builder, repository),
            (self.run_context, self.strategy_identity, None, allocator, builder, repository),
            (self.run_context, self.strategy_identity, pipeline, MissingAllocate(), builder, repository),
            (self.run_context, self.strategy_identity, pipeline, NonCallableAllocate(), builder, repository),
            (self.run_context, self.strategy_identity, pipeline, RecordingAllocator, builder, repository),
            (self.run_context, self.strategy_identity, pipeline, allocator, None, repository),
            (self.run_context, self.strategy_identity, pipeline, allocator, builder, MissingSaveSnapshot()),
            (self.run_context, self.strategy_identity, pipeline, allocator, builder, NonCallableSaveSnapshot()),
            (self.run_context, self.strategy_identity, pipeline, allocator, builder, RecordingRepository),
        )
        for dependencies in invalid_cases:
            with self.subTest(dependencies=dependencies):
                with self.assertRaises(ValueError):
                    PersistedSimulationBetPlanService(
                        run_context=dependencies[0],
                        strategy_identity=dependencies[1],
                        prediction_pipeline=dependencies[2],
                        allocator=dependencies[3],
                        plan_builder=dependencies[4],
                        snapshot_repository=dependencies[5],
                    )
        self.assertEqual(self.events, [])
        self.assertIsNotNone(service)

    def test_invalid_direct_arguments_fail_before_all_collaborators(self) -> None:
        service, pipeline, allocator, builder, repository = self._service()
        for race_input, budget in ((None, self.budget), (self.race_input, None)):
            with self.subTest(race_input=race_input, budget=budget):
                with self.assertRaises(ValueError):
                    service.build_and_save(race_input=race_input, budget=budget)
        self.assertEqual(self.events, [])
        self.assertEqual((pipeline.calls, allocator.calls, builder.calls, repository.calls), ([], [], [], []))

    def test_non_empty_path_uses_exact_inputs_once_and_returns_exact_snapshot(self) -> None:
        service, pipeline, allocator, builder, repository = self._service()

        returned = service.build_and_save(race_input=self.race_input, budget=self.budget)

        self.assertIs(returned, self.snapshot)
        self.assertEqual(self.events, ["pipeline", "allocator", "builder", "repository"])
        self.assertEqual(pipeline.calls, [self.race_input.pipeline_input])
        self.assertIs(pipeline.calls[0], self.race_input.pipeline_input)
        self.assertEqual(len(allocator.calls), 1)
        call = allocator.calls[0]
        self.assertEqual(call["identity"], self.identity)
        self.assertEqual(call["policy_identity"], self.policy_identity)
        self.assertIs(call["bet_plan"], self.bet_plan)
        self.assertIs(call["budget"], self.budget)
        self.assertEqual(builder.calls, [self.allocation_plan])
        self.assertIs(builder.calls[0], self.allocation_plan)
        self.assertEqual(repository.calls, [self.snapshot])
        self.assertIs(repository.calls[0], self.snapshot)
        self.assertNotEqual(self.strategy_identity.strategy_name, self.bet_plan.strategy_name)

    def test_identity_uses_only_the_formal_five_fields(self) -> None:
        service, _pipeline, allocator, _builder, _repository = self._service()

        service.build_and_save(race_input=self.race_input, budget=self.budget)

        identity = allocator.calls[0]["identity"]
        self.assertIsInstance(identity, SimulationBetPlanIdentity)
        self.assertEqual(identity.run_id, self.run_context.run_id)
        self.assertEqual(identity.race_id, self.race_input.race_id)
        self.assertEqual(identity.strategy_id, self.strategy_identity.strategy_id)
        self.assertEqual(identity.strategy_config_hash, self.strategy_identity.strategy_config_hash)
        self.assertEqual(identity.information_cutoff, self.race_input.information_cutoff)
        self.assertNotEqual(self.run_context.started_at, identity.information_cutoff)
        self.assertNotEqual(self.race_input.scheduled_start_at, identity.information_cutoff)

    def test_pipeline_config_is_revalidated_for_each_call(self) -> None:
        service, pipeline, allocator, builder, repository = self._service()
        pipeline.config = object()
        with self.assertRaises(SimulationValidationError) as raised:
            service.build_and_save(race_input=self.race_input, budget=self.budget)
        self._assert_validation(raised, "prediction_pipeline", "config must be a PipelineConfig")
        self.assertEqual((pipeline.calls, allocator.calls, builder.calls, repository.calls), ([], [], [], []))

    def test_strategy_config_mismatch_fails_before_pipeline(self) -> None:
        mismatched_config = PipelineConfig(strategy_config=StrategyConfig())
        service, pipeline, allocator, builder, repository = self._service(pipeline_config=mismatched_config)
        with self.assertRaises(SimulationValidationError) as raised:
            service.build_and_save(race_input=self.race_input, budget=self.budget)
        self._assert_validation(raised, "prediction_pipeline", "strategy_config does not match strategy_identity")
        self.assertEqual((pipeline.calls, allocator.calls, builder.calls, repository.calls), ([], [], [], []))

    def test_missing_allocation_policy_fails_before_pipeline(self) -> None:
        no_policy_strategy = build_strategy_identity("NoPolicy", StrategyConfig())
        pipeline = RecordingPipeline(
            config=PipelineConfig(strategy_config=no_policy_strategy.strategy_config),
            response=self.pipeline_result,
            events=self.events,
        )
        allocator = RecordingAllocator(response=self.allocation_plan, events=self.events)
        builder = RecordingBuilder(response=self.snapshot, events=self.events)
        repository = RecordingRepository(events=self.events)
        service = PersistedSimulationBetPlanService(
            run_context=self.run_context,
            strategy_identity=no_policy_strategy,
            prediction_pipeline=pipeline,
            allocator=allocator,
            plan_builder=builder,
            snapshot_repository=repository,
        )
        with self.assertRaises(SimulationValidationError) as raised:
            service.build_and_save(race_input=self.race_input, budget=self.budget)
        self._assert_validation(
            raised,
            "allocation_policy",
            "strategy_identity.strategy_config.allocation_policy is required",
        )
        self.assertEqual((pipeline.calls, allocator.calls, builder.calls, repository.calls), ([], [], [], []))

    def test_malformed_pipeline_responses_fail_closed(self) -> None:
        malformed_results = (
            (object(), "result must be a PipelineResult"),
            (self._pipeline_result(object()), "bet_plan must be a BetPlan"),
            (
                PipelineResult({}, None, {}, {}, {"bad": "mapping"}, (), (), self.bet_plan),
                "predictions must contain Prediction values",
            ),
            (
                PipelineResult({}, None, {}, {}, ("bad",), (), (), self.bet_plan),
                "predictions must contain Prediction values",
            ),
            (
                PipelineResult(
                    {},
                    None,
                    {},
                    {},
                    (Prediction(999, "other", "A", 1.0, True, "other", RACE_ENTRY_ID),),
                    (),
                    (),
                    self.bet_plan,
                ),
                "prediction race_id does not match race_input",
            ),
        )
        for response, reason in malformed_results:
            with self.subTest(reason=reason):
                self.events.clear()
                service, pipeline, allocator, builder, repository = self._service(pipeline_response=response)
                with self.assertRaises(SimulationValidationError) as raised:
                    service.build_and_save(race_input=self.race_input, budget=self.budget)
                self._assert_validation(raised, "prediction_pipeline", reason)
                self.assertEqual(pipeline.calls, [self.race_input.pipeline_input])
                self.assertEqual((allocator.calls, builder.calls, repository.calls), ([], [], []))

    def test_malformed_allocator_responses_fail_closed(self) -> None:
        alternative_identity = SimulationBetPlanIdentity(
            run_id=self.run_context.run_id,
            race_id=RACE_ID + 1,
            strategy_id=self.strategy_identity.strategy_id,
            strategy_config_hash=self.strategy_identity.strategy_config_hash,
            information_cutoff=INFORMATION_CUTOFF,
        )
        alternative_policy = build_allocation_policy_identity(
            AllocationPolicyConfig("different", "1", {"stake_amount": 100}),
        )
        alternative_plan = BetPlan("another", (self.recommendation,), 1)
        alternative_budget = BetStakeBudget(200)
        cases = (
            (object(), "result must be a BetAllocationPlan"),
            (
                BetAllocationPlan(alternative_identity, self.policy_identity, self.bet_plan, self.allocation_plan.allocations, self.budget),
                "identity does not match",
            ),
            (
                BetAllocationPlan(self.identity, alternative_policy, self.bet_plan, self.allocation_plan.allocations, self.budget),
                "policy_identity does not match",
            ),
            (
                BetAllocationPlan(self.identity, self.policy_identity, alternative_plan, self.allocation_plan.allocations, self.budget),
                "bet_plan object does not match",
            ),
            (
                BetAllocationPlan(self.identity, self.policy_identity, self.bet_plan, self.allocation_plan.allocations, alternative_budget),
                "budget does not match",
            ),
        )
        for response, reason in cases:
            with self.subTest(reason=reason):
                self.events.clear()
                service, _pipeline, allocator, builder, repository = self._service(allocation_response=response)
                with self.assertRaises(SimulationValidationError) as raised:
                    service.build_and_save(race_input=self.race_input, budget=self.budget)
                self._assert_validation(raised, "bet_stake_allocator", reason)
                self.assertEqual(len(allocator.calls), 1)
                self.assertEqual((builder.calls, repository.calls), ([], []))

    def test_malformed_builder_responses_fail_closed(self) -> None:
        alternative_identity = SimulationBetPlanIdentity(
            self.identity.run_id,
            self.identity.race_id + 1,
            self.identity.strategy_id,
            self.identity.strategy_config_hash,
            self.identity.information_cutoff,
        )
        alternative_policy = build_allocation_policy_identity(
            AllocationPolicyConfig("different", "1", {"stake_amount": 100}),
        )
        alternative_budget = BetStakeBudget(200)
        cases = (
            (object(), "result must be a SimulationBetPlanSnapshot"),
            (
                SimulationBetPlanSnapshot(alternative_identity, self.policy_identity, self.budget, ()),
                "identity does not match",
            ),
            (
                SimulationBetPlanSnapshot(self.identity, alternative_policy, self.budget, ()),
                "policy_identity does not match",
            ),
            (
                SimulationBetPlanSnapshot(self.identity, self.policy_identity, alternative_budget, ()),
                "budget does not match",
            ),
        )
        for response, reason in cases:
            with self.subTest(reason=reason):
                self.events.clear()
                service, _pipeline, _allocator, builder, repository = self._service(builder_response=response)
                with self.assertRaises(SimulationValidationError) as raised:
                    service.build_and_save(race_input=self.race_input, budget=self.budget)
                self._assert_validation(raised, "simulation_bet_plan_builder", reason)
                self.assertEqual(len(builder.calls), 1)
                self.assertEqual(repository.calls, [])

    def test_no_bet_still_allocates_builds_and_saves_the_empty_snapshot(self) -> None:
        empty_plan = BetPlan("NoBetPlan", (), 0)
        empty_result = self._pipeline_result(empty_plan)
        empty_budget = BetStakeBudget(500)
        empty_allocation = BetAllocationPlan(
            identity=self.identity,
            policy_identity=self.policy_identity,
            bet_plan=empty_plan,
            allocations=(),
            budget=empty_budget,
        )
        empty_snapshot = SimulationBetPlanSnapshot(
            identity=self.identity,
            policy_identity=self.policy_identity,
            budget=empty_budget,
            bets=(),
        )
        service, _pipeline, allocator, builder, repository = self._service(
            pipeline_response=empty_result,
            allocation_response=empty_allocation,
            builder_response=empty_snapshot,
        )

        returned = service.build_and_save(race_input=self.race_input, budget=empty_budget)

        self.assertIs(returned, empty_snapshot)
        self.assertEqual(self.events, ["pipeline", "allocator", "builder", "repository"])
        self.assertIs(allocator.calls[0]["budget"], empty_budget)
        self.assertIs(empty_allocation.budget, empty_budget)
        self.assertIs(builder.calls[0], empty_allocation)
        self.assertIs(empty_snapshot.budget, empty_budget)
        self.assertEqual(empty_snapshot.bets, ())
        self.assertEqual(empty_snapshot.allocated_amount, 0)
        self.assertEqual(empty_snapshot.unallocated_amount, 500)
        self.assertIs(repository.calls[0], empty_snapshot)

    def test_collaborator_exceptions_propagate_by_object_identity_without_retry(self) -> None:
        errors = (
            ("pipeline", PipelineExecutionError(PipelineStage.ABILITY)),
            ("allocator", RuntimeError("allocator failure")),
            ("builder", RuntimeError("builder failure")),
            ("repository", RuntimeError("repository failure")),
        )
        for stage, error in errors:
            with self.subTest(stage=stage):
                self.events.clear()
                arguments: dict[str, BaseException] = {f"{stage}_error": error}
                service, pipeline, allocator, builder, repository = self._service(**arguments)
                with self.assertRaises(type(error)) as raised:
                    service.build_and_save(race_input=self.race_input, budget=self.budget)
                self.assertIs(raised.exception, error)
                counts = (len(pipeline.calls), len(allocator.calls), len(builder.calls), len(repository.calls))
                expected = {
                    "pipeline": (1, 0, 0, 0),
                    "allocator": (1, 1, 0, 0),
                    "builder": (1, 1, 1, 0),
                    "repository": (1, 1, 1, 1),
                }[stage]
                self.assertEqual(counts, expected)

    def test_repository_exceptions_propagate_by_object_identity_without_retry(self) -> None:
        errors = (
            RepositoryValidationError("validation failure"),
            RepositoryConflictError("conflict failure"),
            RepositoryDataIntegrityError("integrity failure"),
        )
        for error in errors:
            with self.subTest(error_type=type(error).__name__):
                self.events.clear()
                service, pipeline, allocator, builder, repository = self._service(
                    repository_error=error,
                )
                with self.assertRaises(type(error)) as raised:
                    service.build_and_save(race_input=self.race_input, budget=self.budget)
                self.assertIs(raised.exception, error)
                self.assertEqual(
                    (len(pipeline.calls), len(allocator.calls), len(builder.calls), len(repository.calls)),
                    (1, 1, 1, 1),
                )
                self.assertEqual(self.events, ["pipeline", "allocator", "builder", "repository"])

    def test_module_has_no_forbidden_dependencies_or_runtime_protocol_checks(self) -> None:
        module = inspect.getmodule(PersistedSimulationBetPlanService)
        self.assertIsNotNone(module)
        source = inspect.getsource(module)
        tree = ast.parse(source)
        self.assertIn("class PersistedSimulationBetPlanService", source)
        self.assertIn("from scripts.simulation", source)
        imported_modules = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imported_from_modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        imported_names = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
        }
        self.assertNotIn("sqlite3", imported_modules)
        self.assertFalse(
            any(module_name.startswith("scripts.simulation.repositories.sqlite") for module_name in imported_from_modules),
        )
        self.assertNotIn("Any", imported_names)
        self.assertNotIn("cast", imported_names)
        self.assertFalse(
            _uses_forbidden_typing_attribute(tree, names={"Any"}),
        )
        self.assertFalse(
            _uses_forbidden_typing_attribute(tree, names={"cast"}),
        )
        self.assertNotIn("sqlite", source.lower())
        self.assertNotIn("# type: ignore", source)
        self.assertNotIn("runtime_checkable", source)
        forbidden_calls = {
            (node.func.value.id, node.func.attr)
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
        }
        self.assertNotIn(("datetime", "now"), forbidden_calls)
        self.assertNotIn(("date", "today"), forbidden_calls)
        self.assertNotIn("isinstance(allocator, BetStakeAllocator)", source)
        self.assertNotIn(
            "isinstance(snapshot_repository, SimulationBetPlanSnapshotRepository)",
            source,
        )
        package_source = inspect.getsource(simulation_package)
        self.assertNotIn("PersistedSimulationBetPlanService", package_source)

    def test_typing_module_attribute_helper_detects_direct_and_aliased_imports(self) -> None:
        direct_tree = ast.parse(
            """
import typing
value: typing.Any = typing.cast(object, 1)
""",
        )
        aliased_tree = ast.parse(
            """
import typing as t
value: t.Any = t.cast(object, 1)
""",
        )
        clean_tree = ast.parse(
            """
from typing import Protocol
class Example(Protocol):
    pass
""",
        )

        for tree in (direct_tree, aliased_tree):
            with self.subTest(tree=tree):
                self.assertTrue(_uses_forbidden_typing_attribute(tree, names={"Any"}))
                self.assertTrue(_uses_forbidden_typing_attribute(tree, names={"cast"}))
        self.assertFalse(_uses_forbidden_typing_attribute(clean_tree, names={"Any", "cast"}))
