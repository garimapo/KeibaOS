from __future__ import annotations

import ast
from dataclasses import replace
from datetime import UTC, date, datetime
import inspect
from typing import get_type_hints
import unittest
from unittest.mock import patch

import scripts.simulation as simulation_package
import scripts.simulation.historical_prediction_bet_plan_execution as execution_module
from scripts.prediction.allocation_policy import AllocationPolicyConfig
from scripts.prediction.bet_generator import BetGenerator, BetRecommendation
from scripts.prediction.bet_strategy import BetPlan, RuleBasedBetStrategy, StrategyConfig
from scripts.prediction.prediction_pipeline import (
    PipelineConfig,
    PipelineExecutionError,
    PipelineResult,
    PipelineStage,
    PredictionPipeline,
    build_historical_prediction_pipeline,
)
from scripts.simulation.bet_plan_snapshot import SimulationBetPlanSnapshot
from scripts.simulation.bet_plan_snapshot_repository import (
    SimulationBetPlanSnapshotRepository,
)
from scripts.simulation.exact_race_entry_selection_resolver import (
    ExactRaceEntrySelectionResolver,
)
from scripts.simulation.historical_input_snapshot_simulation_adapter import (
    build_simulation_race_input_from_historical_snapshot,
)
from scripts.simulation.historical_input_snapshots import HistoricalInputSnapshot
from scripts.simulation.models import (
    SimulationRaceInput,
    SimulationRunContext,
    StrategyIdentity,
    build_strategy_identity,
)
from scripts.simulation.bet_plan_builder import SimulationBetPlanBuilder
from scripts.simulation.fixed_stake_allocator import FixedStakeBetAllocator
from scripts.simulation.persisted_bet_plan_service import PersistedSimulationBetPlanService
from scripts.simulation.repositories.errors import RepositoryConflictError
from scripts.simulation.stake_allocation import BetStakeBudget
from scripts.simulation.validation import SimulationValidationError
from tests.test_historical_input_snapshot_simulation_adapter import _snapshot


class RecordingSnapshotRepository:
    def __init__(self) -> None:
        self.saved: list[object] = []

    def save_snapshot(self, *, snapshot: object) -> None:
        self.saved.append(snapshot)


class RaisingSnapshotRepository(RecordingSnapshotRepository):
    def __init__(self, error: BaseException) -> None:
        super().__init__()
        self.error = error

    def save_snapshot(self, *, snapshot: object) -> None:
        super().save_snapshot(snapshot=snapshot)
        raise self.error


def _policy() -> AllocationPolicyConfig:
    return AllocationPolicyConfig(
        policy_name="fixed_stake_per_recommendation",
        policy_version="1",
        parameters={"stake_amount": 100},
    )


def _strategy_identity(*, name: str = "RuleBasedBetStrategy", max_bet_count: int = 0) -> StrategyIdentity:
    return build_strategy_identity(
        name,
        StrategyConfig(max_bet_count=max_bet_count, allocation_policy=_policy()),
    )


def _run_context(*, dataset_id: str = "historical-dataset", run_id: str = "historical-run") -> SimulationRunContext:
    return SimulationRunContext(
        run_id=run_id,
        dataset_id=dataset_id,
        started_at=datetime(2026, 8, 6, tzinfo=UTC),
        target_commit_id="historical-commit",
    )


class HistoricalPredictionBetPlanExecutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.snapshot = _snapshot()
        self.run_context = _run_context()
        self.strategy_identity = _strategy_identity()
        self.budget = BetStakeBudget(total_amount=0)
        self.repository = RecordingSnapshotRepository()

    def _call(self, **overrides: object) -> object:
        values: dict[str, object] = {
            "snapshot": self.snapshot,
            "run_context": self.run_context,
            "strategy_identity": self.strategy_identity,
            "budget": self.budget,
            "snapshot_repository": self.repository,
        }
        values.update(overrides)
        return execution_module.execute_and_persist_historical_bet_plan(**values)  # type: ignore[arg-type]

    def test_exact_public_surface_signature_and_annotations(self) -> None:
        self.assertEqual(
            execution_module.__all__,
            ("execute_and_persist_historical_bet_plan",),
        )
        self.assertFalse(
            hasattr(simulation_package, "execute_and_persist_historical_bet_plan")
        )
        signature = inspect.signature(
            execution_module.execute_and_persist_historical_bet_plan
        )
        self.assertEqual(
            tuple(signature.parameters),
            ("snapshot", "run_context", "strategy_identity", "budget", "snapshot_repository"),
        )
        self.assertTrue(
            all(
                parameter.kind is inspect.Parameter.KEYWORD_ONLY
                for parameter in signature.parameters.values()
            )
        )
        hints = get_type_hints(execution_module.execute_and_persist_historical_bet_plan)
        self.assertIs(hints["snapshot"], HistoricalInputSnapshot)
        self.assertIs(hints["run_context"], SimulationRunContext)
        self.assertIs(hints["strategy_identity"], StrategyIdentity)
        self.assertIs(hints["budget"], BetStakeBudget)
        self.assertIs(
            hints["snapshot_repository"],
            SimulationBetPlanSnapshotRepository,
        )
        self.assertIs(hints["return"], SimulationBetPlanSnapshot)

    def test_invalid_boundary_inputs_fail_before_adapter_factory_or_repository(self) -> None:
        invalid = (
            {"snapshot": object()},
            {"run_context": object()},
            {"strategy_identity": object()},
            {"budget": object()},
            {"snapshot_repository": object()},
            {"snapshot_repository": RecordingSnapshotRepository},
        )
        for overrides in invalid:
            with self.subTest(overrides=overrides):
                with patch.object(
                    execution_module,
                    "build_simulation_race_input_from_historical_snapshot",
                ) as adapter, patch.object(
                    execution_module,
                    "build_historical_prediction_pipeline",
                ) as factory:
                    with self.assertRaises(ValueError):
                        self._call(**overrides)
                    adapter.assert_not_called()
                    factory.assert_not_called()
                    self.assertEqual(self.repository.saved, [])

    def test_strategy_name_mismatch_fails_before_all_collaborators(self) -> None:
        other_identity = _strategy_identity(name="OtherStrategy")
        with patch.object(
            execution_module,
            "build_simulation_race_input_from_historical_snapshot",
        ) as adapter, patch.object(
            execution_module,
            "build_historical_prediction_pipeline",
        ) as factory:
            with self.assertRaises(ValueError):
                self._call(strategy_identity=other_identity)
            adapter.assert_not_called()
            factory.assert_not_called()
            self.assertEqual(self.repository.saved, [])

    def test_dataset_mismatch_has_exact_simulation_validation_error_before_collaborators(self) -> None:
        with patch.object(
            execution_module,
            "build_simulation_race_input_from_historical_snapshot",
        ) as adapter, patch.object(
            execution_module,
            "build_historical_prediction_pipeline",
        ) as factory:
            with self.assertRaises(SimulationValidationError) as raised:
                self._call(run_context=_run_context(dataset_id="other-dataset"))
            self.assertEqual(raised.exception.race_id, self.snapshot.internal_race_id)
            self.assertEqual(
                raised.exception.input_identifier,
                "run_context.dataset_id",
            )
            self.assertEqual(
                raised.exception.reason,
                "run_context.dataset_id does not match snapshot.identity.dataset_id",
            )
            adapter.assert_not_called()
            factory.assert_not_called()
            self.assertEqual(self.repository.saved, [])

    def test_success_uses_adapter_and_factory_once_with_exact_identity_objects(self) -> None:
        with patch.object(
            execution_module,
            "build_simulation_race_input_from_historical_snapshot",
            wraps=build_simulation_race_input_from_historical_snapshot,
        ) as adapter, patch.object(
            execution_module,
            "build_historical_prediction_pipeline",
            wraps=build_historical_prediction_pipeline,
        ) as factory:
            result = self._call()

        self.assertEqual(adapter.call_count, 1)
        self.assertIs(adapter.call_args.kwargs["snapshot"], self.snapshot)
        self.assertEqual(factory.call_count, 1)
        self.assertEqual(
            factory.call_args.kwargs["target_race_date"],
            self.snapshot.race.target_race_date,
        )
        self.assertIs(
            factory.call_args.kwargs["strategy_config"],
            self.strategy_identity.strategy_config,
        )
        self.assertEqual(result.bets, ())
        self.assertEqual(result.allocated_amount, 0)
        self.assertEqual(len(self.repository.saved), 1)
        self.assertIs(self.repository.saved[0], result)

    def test_post_factory_checks_fail_without_second_factory_or_save(self) -> None:
        race_input = build_simulation_race_input_from_historical_snapshot(
            snapshot=self.snapshot
        )
        invalid_pipelines = (
            object(),
            PredictionPipeline(config=object()),
            PredictionPipeline(
                config=PipelineConfig(
                    strategy_config=StrategyConfig(allocation_policy=_policy()),
                    bet_strategy=RuleBasedBetStrategy(),
                )
            ),
            PredictionPipeline(
                config=PipelineConfig(
                    strategy_config=self.strategy_identity.strategy_config,
                    bet_strategy=object(),
                )
            ),
        )
        for pipeline in invalid_pipelines:
            with self.subTest(pipeline=type(pipeline).__name__):
                with patch.object(
                    execution_module,
                    "build_simulation_race_input_from_historical_snapshot",
                    return_value=race_input,
                ) as adapter, patch.object(
                    execution_module,
                    "build_historical_prediction_pipeline",
                    return_value=pipeline,
                ) as factory:
                    with self.assertRaises(ValueError):
                        self._call()
                    self.assertEqual(adapter.call_count, 1)
                    self.assertEqual(factory.call_count, 1)
                    self.assertEqual(self.repository.saved, [])

    def test_exact_race_entry_ids_flow_through_existing_service_once(self) -> None:
        recommendation = BetRecommendation(
            rank=0,
            bet_type=BetGenerator.WIN,
            horse_ids=(101,),
            estimated_probability=0.4,
            expected_value=1.2,
            combination_score=None,
            prediction_score=80.0,
        )
        pipeline_result = PipelineResult(
            ability_evaluations={},
            pace_evaluation=None,
            jockey_evaluations={},
            track_evaluations={},
            predictions=(),
            value_evaluations=(),
            recommendations=(recommendation,),
            bet_plan=BetPlan(
                strategy_name="RuleBasedBetStrategy",
                recommendations=(recommendation,),
                candidate_count=1,
            ),
        )
        run_calls: list[object] = []

        def run_once(pipeline: PredictionPipeline, pipeline_input: object) -> PipelineResult:
            run_calls.append(pipeline_input)
            return pipeline_result

        with patch.object(PredictionPipeline, "run", new=run_once):
            result = self._call(budget=BetStakeBudget(total_amount=100))

        self.assertEqual(run_calls, [build_simulation_race_input_from_historical_snapshot(snapshot=self.snapshot).pipeline_input])
        self.assertEqual(len(result.bets), 1)
        self.assertEqual(result.bets[0].race_entry_ids, (101,))
        self.assertEqual(len(self.repository.saved), 1)
        self.assertIs(self.repository.saved[0], result)
        self.assertNotEqual(result.bets[0].race_entry_ids, (9,))

    def test_insufficient_budget_does_not_become_an_empty_plan(self) -> None:
        recommendation = BetRecommendation(
            rank=0,
            bet_type=BetGenerator.WIN,
            horse_ids=(101,),
            estimated_probability=0.4,
            expected_value=1.2,
            combination_score=None,
            prediction_score=80.0,
        )
        pipeline_result = PipelineResult(
            ability_evaluations={},
            pace_evaluation=None,
            jockey_evaluations={},
            track_evaluations={},
            predictions=(),
            value_evaluations=(),
            recommendations=(recommendation,),
            bet_plan=BetPlan(
                strategy_name="RuleBasedBetStrategy",
                recommendations=(recommendation,),
                candidate_count=1,
            ),
        )
        run_calls: list[object] = []

        def return_one_recommendation(
            pipeline: PredictionPipeline,
            pipeline_input: object,
        ) -> PipelineResult:
            run_calls.append(pipeline_input)
            return pipeline_result

        with patch.object(PredictionPipeline, "run", new=return_one_recommendation):
            with self.assertRaises(ValueError):
                self._call(budget=BetStakeBudget(total_amount=0))
        self.assertEqual(len(run_calls), 1)
        self.assertEqual(self.repository.saved, [])

    def test_pipeline_execution_error_propagates_by_identity_without_retry(self) -> None:
        error = PipelineExecutionError(PipelineStage.ABILITY)
        run_calls: list[object] = []

        def raise_exact_error(
            pipeline: PredictionPipeline,
            pipeline_input: object,
        ) -> PipelineResult:
            run_calls.append(pipeline_input)
            raise error

        with patch.object(PredictionPipeline, "run", new=raise_exact_error):
            with self.assertRaises(PipelineExecutionError) as raised:
                self._call()
        self.assertIs(raised.exception, error)
        self.assertEqual(len(run_calls), 1)
        self.assertEqual(self.repository.saved, [])

    def test_downstream_simulation_validation_error_propagates_by_identity(self) -> None:
        error = SimulationValidationError(
            self.snapshot.internal_race_id,
            "downstream",
            "downstream simulation validation failure",
        )
        run_calls: list[object] = []

        def raise_downstream_error(
            pipeline: PredictionPipeline,
            pipeline_input: object,
        ) -> PipelineResult:
            run_calls.append(pipeline_input)
            raise error

        with patch.object(
            execution_module,
            "build_simulation_race_input_from_historical_snapshot",
            wraps=build_simulation_race_input_from_historical_snapshot,
        ) as adapter, patch.object(
            execution_module,
            "build_historical_prediction_pipeline",
            wraps=build_historical_prediction_pipeline,
        ) as factory, patch.object(PredictionPipeline, "run", new=raise_downstream_error):
            with self.assertRaises(SimulationValidationError) as raised:
                self._call()
        self.assertIs(raised.exception, error)
        self.assertEqual(adapter.call_count, 1)
        self.assertEqual(factory.call_count, 1)
        self.assertEqual(len(run_calls), 1)
        self.assertEqual(self.repository.saved, [])

    def test_repository_error_propagates_by_identity_after_exact_single_save(self) -> None:
        error = RepositoryConflictError("repository conflict")
        repository = RaisingSnapshotRepository(error)
        with self.assertRaises(RepositoryConflictError) as raised:
            self._call(snapshot_repository=repository)
        self.assertIs(raised.exception, error)
        self.assertEqual(len(repository.saved), 1)

    def test_existing_service_chain_calls_allocator_builder_service_and_save_once(self) -> None:
        allocation_policy_values: list[object] = []
        allocator_calls: list[object] = []
        builder_calls: list[object] = []
        service_calls: list[object] = []
        original_allocator = FixedStakeBetAllocator
        original_allocate = FixedStakeBetAllocator.allocate
        original_build = SimulationBetPlanBuilder.build
        original_service_call = PersistedSimulationBetPlanService.build_and_save

        def construct_allocator(*, policy_config: object) -> FixedStakeBetAllocator:
            allocation_policy_values.append(policy_config)
            return original_allocator(policy_config=policy_config)  # type: ignore[arg-type]

        def allocate_once(
            allocator: FixedStakeBetAllocator,
            **kwargs: object,
        ) -> object:
            allocator_calls.append(kwargs)
            return original_allocate(allocator, **kwargs)  # type: ignore[arg-type]

        def build_once(
            builder: SimulationBetPlanBuilder,
            **kwargs: object,
        ) -> object:
            builder_calls.append(kwargs)
            return original_build(builder, **kwargs)  # type: ignore[arg-type]

        def service_once(
            service: PersistedSimulationBetPlanService,
            **kwargs: object,
        ) -> object:
            service_calls.append(kwargs)
            return original_service_call(service, **kwargs)  # type: ignore[arg-type]

        with patch.object(
            execution_module,
            "FixedStakeBetAllocator",
            side_effect=construct_allocator,
        ), patch.object(FixedStakeBetAllocator, "allocate", new=allocate_once), patch.object(
            SimulationBetPlanBuilder,
            "build",
            new=build_once,
        ), patch.object(
            PersistedSimulationBetPlanService,
            "build_and_save",
            new=service_once,
        ):
            result = self._call()

        self.assertEqual(
            allocation_policy_values,
            [self.strategy_identity.strategy_config.allocation_policy],
        )
        self.assertEqual(len(service_calls), 1)
        self.assertEqual(len(allocator_calls), 1)
        self.assertEqual(len(builder_calls), 1)
        self.assertEqual(len(self.repository.saved), 1)
        self.assertIs(self.repository.saved[0], result)

    def test_resolver_allowlist_comes_only_from_exact_pipeline_key_order(self) -> None:
        constructor_calls: list[tuple[int, tuple[int, ...]]] = []
        original_resolver = ExactRaceEntrySelectionResolver

        def construct_resolver(
            *,
            race_id: int,
            allowed_race_entry_ids: tuple[int, ...],
        ) -> ExactRaceEntrySelectionResolver:
            constructor_calls.append((race_id, allowed_race_entry_ids))
            return original_resolver(
                race_id=race_id,
                allowed_race_entry_ids=allowed_race_entry_ids,
            )

        expected_race_input = build_simulation_race_input_from_historical_snapshot(
            snapshot=self.snapshot
        )
        expected_allowlist = tuple(
            expected_race_input.pipeline_input.horse_past_races.keys()
        )
        with patch.object(
            execution_module,
            "ExactRaceEntrySelectionResolver",
            side_effect=construct_resolver,
        ):
            self._call()
        self.assertEqual(
            constructor_calls,
            [(expected_race_input.race_id, expected_allowlist)],
        )

    def test_unknown_recommendation_identity_propagates_without_save(self) -> None:
        recommendation = BetRecommendation(
            rank=0,
            bet_type=BetGenerator.WIN,
            horse_ids=(999,),
            estimated_probability=0.4,
            expected_value=1.2,
            combination_score=None,
            prediction_score=80.0,
        )
        pipeline_result = PipelineResult(
            ability_evaluations={},
            pace_evaluation=None,
            jockey_evaluations={},
            track_evaluations={},
            predictions=(),
            value_evaluations=(),
            recommendations=(recommendation,),
            bet_plan=BetPlan(
                strategy_name="RuleBasedBetStrategy",
                recommendations=(recommendation,),
                candidate_count=1,
            ),
        )

        def return_unknown(
            pipeline: PredictionPipeline,
            pipeline_input: object,
        ) -> PipelineResult:
            return pipeline_result

        with patch.object(PredictionPipeline, "run", new=return_unknown):
            with self.assertRaises(ValueError):
                self._call(budget=BetStakeBudget(total_amount=100))
        self.assertEqual(self.repository.saved, [])

    def test_missing_or_unsupported_policy_fails_before_prediction_or_save(self) -> None:
        missing_config = StrategyConfig(allocation_policy=None)
        missing_identity = build_strategy_identity("RuleBasedBetStrategy", missing_config)
        unsupported_config = StrategyConfig(
            allocation_policy=AllocationPolicyConfig(
                policy_name="unsupported",
                policy_version="1",
                parameters={"stake_amount": 100},
            )
        )
        unsupported_identity = build_strategy_identity(
            "RuleBasedBetStrategy", unsupported_config
        )
        for identity in (missing_identity, unsupported_identity):
            with self.subTest(identity=identity.strategy_config.allocation_policy):
                with patch.object(PredictionPipeline, "run") as run:
                    with self.assertRaises(ValueError):
                        self._call(strategy_identity=identity)
                    run.assert_not_called()
                    self.assertEqual(self.repository.saved, [])

    def test_same_inputs_are_deterministic_and_different_run_id_changes_plan_identity(self) -> None:
        first_repository = RecordingSnapshotRepository()
        second_repository = RecordingSnapshotRepository()
        first = self._call(snapshot_repository=first_repository)
        second = self._call(snapshot_repository=second_repository)
        self.assertEqual(first, second)
        changed_run = self._call(
            run_context=_run_context(run_id="historical-run-2"),
            snapshot_repository=RecordingSnapshotRepository(),
        )
        self.assertNotEqual(first.identity, changed_run.identity)

    def test_process_date_defaults_do_not_change_historical_execution(self) -> None:
        class EarlyDate(date):
            @classmethod
            def today(cls) -> "EarlyDate":
                return cls(2000, 1, 1)

        class LateDate(date):
            @classmethod
            def today(cls) -> "LateDate":
                return cls(2099, 12, 31)

        def execute_with(fake_date: type[date]) -> object:
            with (
                patch("scripts.prediction.ability_engine.date", fake_date),
                patch("scripts.prediction.jockey_engine.date", fake_date),
                patch("scripts.prediction.track_engine.date", fake_date),
            ):
                return self._call(snapshot_repository=RecordingSnapshotRepository())

        self.assertEqual(execute_with(EarlyDate), execute_with(LateDate))

    def test_two_target_race_dates_construct_distinct_historical_pipelines(self) -> None:
        second_race = replace(
            self.snapshot.race,
            target_race_date=date(2026, 8, 6),
        )
        second_snapshot = replace(self.snapshot, race=second_race)
        factory_calls: list[dict[str, object]] = []
        constructed_pipelines: list[PredictionPipeline] = []

        def construct_pipeline(**kwargs: object) -> PredictionPipeline:
            factory_calls.append(kwargs)
            pipeline = build_historical_prediction_pipeline(**kwargs)  # type: ignore[arg-type]
            constructed_pipelines.append(pipeline)
            return pipeline

        with patch.object(
            execution_module,
            "build_historical_prediction_pipeline",
            side_effect=construct_pipeline,
        ):
            self._call(snapshot_repository=RecordingSnapshotRepository())
            self._call(
                snapshot=second_snapshot,
                snapshot_repository=RecordingSnapshotRepository(),
            )
        self.assertEqual(len(factory_calls), 2)
        self.assertEqual(
            factory_calls[0]["target_race_date"],
            self.snapshot.race.target_race_date,
        )
        self.assertEqual(
            factory_calls[1]["target_race_date"],
            second_snapshot.race.target_race_date,
        )
        self.assertEqual(len(constructed_pipelines), 2)
        self.assertIsNot(constructed_pipelines[0], constructed_pipelines[1])

    def test_static_scope_has_no_direct_database_current_or_settlement_ownership(self) -> None:
        source = inspect.getsource(execution_module)
        tree = ast.parse(source)
        imports = [
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        ] + [
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        ]
        forbidden = (
            "sqlite3",
            "requests",
            "httpx",
            "pathlib",
            "subprocess",
            "scripts.simulation.repositories",
            "scripts.simulation.persisted_simulation_run_service",
        )
        self.assertFalse(any(name.startswith(forbidden) for name in imports))
        for forbidden_text in (
            "SQLiteRaceEntrySource",
            "RepositoryBackedRaceEntrySelectionResolver",
            "RaceEntrySource",
            "datetime.now",
            "date.today",
            "time.time",
            "except Exception",
            "except BaseException",
        ):
            self.assertNotIn(forbidden_text, source)


if __name__ == "__main__":
    unittest.main()
