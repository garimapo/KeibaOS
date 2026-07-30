from __future__ import annotations

import ast
from collections.abc import Mapping
from dataclasses import fields
from datetime import datetime, timezone
import inspect
from pathlib import Path
from types import MappingProxyType
from typing import get_type_hints
import unittest

import scripts.simulation as simulation_package
from scripts.prediction.allocation_policy import AllocationPolicyConfig
from scripts.prediction.bet_strategy import RuleBasedBetStrategy, SelectionStyle, SortCondition, StrategyConfig
from scripts.prediction.prediction_pipeline import PipelineConfig, PredictionPipeline
from scripts.prediction.track_engine import TrackEngine
from scripts.simulation.models import SimulationRunContext, StrategyIdentity, build_strategy_identity
from scripts.simulation.persisted_simulation_application_inputs import (
    PersistedSimulationApplicationInputs,
    assemble_persisted_simulation_application_inputs,
)
from scripts.simulation.persisted_simulation_request_document import PersistedSimulationRequestDocument
from scripts.simulation.stake_allocation import BetStakeBudget


def _document(*, started_at: str = "2026-08-05T12:30:00+09:00") -> PersistedSimulationRequestDocument:
    return PersistedSimulationRequestDocument(
        schema_version=1,
        source_path=Path("request.json"),
        database_path=Path("simulation.db"),
        run_context={
            "run_id": "run-1",
            "dataset_id": "dataset-1",
            "started_at": started_at,
            "target_commit_id": "commit-1",
        },
        strategy={
            "strategy_name": "RuleBasedBetStrategy",
            "allowed_bet_types": ["単勝", "馬連"],
            "max_bet_count": 3,
            "selection_style": "formation",
            "min_combination_score": -1.5,
            "max_candidates": 5,
            "sort_condition": "generator_rank",
            "allocation_policy": {
                "policy_name": "fixed_stake_per_recommendation",
                "policy_version": "1",
                "parameters": {"stake_amount": 100},
            },
        },
        pipeline={"track_reference_date": "2026-08-05"},
        races=(),
        budgets_by_race_id={"20": {"total_amount": 200}, "3": {"total_amount": 0}},
    )


class PersistedSimulationApplicationInputsTest(unittest.TestCase):
    def test_formal_api_and_valid_assembly(self) -> None:
        signature = inspect.signature(assemble_persisted_simulation_application_inputs)
        self.assertEqual(tuple(signature.parameters), ("document",))
        self.assertEqual(signature.parameters["document"].kind, inspect.Parameter.KEYWORD_ONLY)
        self.assertTrue(getattr(PersistedSimulationApplicationInputs, "__dataclass_params__").frozen)
        self.assertEqual(
            [field.name for field in fields(PersistedSimulationApplicationInputs)],
            ["database_path", "run_context", "strategy_identity", "prediction_pipeline", "budgets_by_race_id"],
        )
        self.assertEqual(
            get_type_hints(PersistedSimulationApplicationInputs),
            {
                "database_path": Path,
                "run_context": SimulationRunContext,
                "strategy_identity": StrategyIdentity,
                "prediction_pipeline": PredictionPipeline,
                "budgets_by_race_id": Mapping[int, BetStakeBudget],
            },
        )
        assembler_hints = get_type_hints(assemble_persisted_simulation_application_inputs)
        self.assertEqual(assembler_hints["document"], PersistedSimulationRequestDocument)
        self.assertIs(assembler_hints["return"], PersistedSimulationApplicationInputs)

        result = assemble_persisted_simulation_application_inputs(document=_document())

        self.assertEqual(result.database_path, Path("simulation.db"))
        self.assertEqual(result.run_context.run_id, "run-1")
        self.assertEqual(result.run_context.dataset_id, "dataset-1")
        self.assertEqual(result.run_context.started_at.utcoffset().total_seconds(), 9 * 60 * 60)
        self.assertEqual(result.run_context.target_commit_id, "commit-1")
        self.assertEqual(result.strategy_identity.strategy_name, "RuleBasedBetStrategy")
        self.assertEqual(result.strategy_identity.strategy_config.allowed_bet_types, frozenset({"単勝", "馬連"}))
        self.assertEqual(result.strategy_identity.strategy_config.max_bet_count, 3)
        self.assertEqual(result.strategy_identity.strategy_config.selection_style, SelectionStyle.FORMATION)
        self.assertIs(type(result.strategy_identity.strategy_config.min_combination_score), float)
        self.assertEqual(result.strategy_identity.strategy_config.min_combination_score, -1.5)
        self.assertEqual(result.strategy_identity.strategy_config.max_candidates, 5)
        self.assertEqual(result.strategy_identity.strategy_config.sort_condition, SortCondition.GENERATOR_RANK)
        self.assertIs(type(result.strategy_identity.strategy_config.allocation_policy), AllocationPolicyConfig)
        self.assertEqual(result.strategy_identity.strategy_config.allocation_policy.policy_name, "fixed_stake_per_recommendation")
        self.assertEqual(result.strategy_identity.strategy_config.allocation_policy.policy_version, "1")
        self.assertEqual(result.strategy_identity.strategy_config.allocation_policy.parameters["stake_amount"], 100)
        self.assertIs(type(result.prediction_pipeline), PredictionPipeline)
        self.assertIs(type(result.prediction_pipeline.config), PipelineConfig)
        self.assertIs(result.prediction_pipeline.config.strategy_config, result.strategy_identity.strategy_config)
        self.assertIs(type(result.prediction_pipeline.config.bet_strategy), RuleBasedBetStrategy)
        self.assertIs(type(result.prediction_pipeline.config.track_engine), TrackEngine)
        self.assertEqual(result.prediction_pipeline.config.track_engine.reference_date.isoformat(), "2026-08-05")
        self.assertEqual(list(result.budgets_by_race_id), [3, 20])
        self.assertIs(type(result.budgets_by_race_id), MappingProxyType)
        self.assertEqual(result.budgets_by_race_id[20], BetStakeBudget(200))
        with self.assertRaises(TypeError):
            result.budgets_by_race_id[1] = BetStakeBudget(100)  # type: ignore[index]

    def test_z_datetime_and_deterministic_double_assembly(self) -> None:
        document = _document(started_at="2026-08-05T03:30:00Z")
        first = assemble_persisted_simulation_application_inputs(document=document)
        second = assemble_persisted_simulation_application_inputs(document=document)
        self.assertEqual(first.run_context.started_at, datetime(2026, 8, 5, 3, 30, tzinfo=timezone.utc))
        self.assertEqual(first.run_context, second.run_context)
        self.assertEqual(first.strategy_identity.strategy_id, second.strategy_identity.strategy_id)
        self.assertEqual(first.strategy_identity.strategy_config_hash, second.strategy_identity.strategy_config_hash)
        self.assertEqual(first.strategy_identity.strategy_config, second.strategy_identity.strategy_config)
        self.assertEqual(
            first.strategy_identity.strategy_config.allocation_policy,
            second.strategy_identity.strategy_config.allocation_policy,
        )
        self.assertEqual(
            first.prediction_pipeline.config.track_engine.reference_date,
            second.prediction_pipeline.config.track_engine.reference_date,
        )
        self.assertIs(type(first.prediction_pipeline.config.bet_strategy), RuleBasedBetStrategy)
        self.assertEqual(list(first.budgets_by_race_id), list(second.budgets_by_race_id))
        self.assertEqual(first.budgets_by_race_id, second.budgets_by_race_id)
        self.assertEqual(first.database_path, second.database_path)
        self.assertIsNot(first.prediction_pipeline, second.prediction_pipeline)

    def test_document_and_run_context_validation(self) -> None:
        with self.assertRaisesRegex(ValueError, "document must be a PersistedSimulationRequestDocument"):
            assemble_persisted_simulation_application_inputs(document=object())
        document = _document()
        for key, value, error in (
            ("run_id", " ", "run_context.run_id must be a non-empty string"),
            ("dataset_id", True, "run_context.dataset_id must be a non-empty string"),
            ("target_commit_id", "", "run_context.target_commit_id must be a non-empty string"),
            ("started_at", "2026-08-05", "run_context.started_at must be an ISO 8601 timezone-aware datetime"),
        ):
            payload = dict(document.run_context)
            payload[key] = value
            invalid = _replace_document(document, run_context=payload)
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, error):
                assemble_persisted_simulation_application_inputs(document=invalid)
        with self.assertRaisesRegex(ValueError, "run_context keys must exactly match the run context schema"):
            assemble_persisted_simulation_application_inputs(
                document=_replace_document(document, run_context={"run_id": "x"})
            )

    def test_started_at_invalid_values_and_empty_allowed_bet_types(self) -> None:
        document = _document()
        for started_at in (True, "not-a-datetime", "2026-08-05", "2026-08-05T12:00:00"):
            run_context = dict(document.run_context)
            run_context["started_at"] = started_at
            with self.subTest(started_at=started_at), self.assertRaisesRegex(
                ValueError,
                "run_context.started_at must be an ISO 8601 timezone-aware datetime",
            ):
                assemble_persisted_simulation_application_inputs(
                    document=_replace_document(document, run_context=run_context)
                )
        strategy = dict(document.strategy)
        strategy["allowed_bet_types"] = []
        result = assemble_persisted_simulation_application_inputs(
            document=_replace_document(document, strategy=strategy)
        )
        self.assertEqual(result.strategy_identity.strategy_config.allowed_bet_types, frozenset())

    def test_run_context_non_mapping_and_schema_matrix(self) -> None:
        document = _document()
        cases = (
            "not-a-mapping",
            {},
            {**document.run_context, "extra": "value"},
        )
        for run_context in cases:
            with self.subTest(run_context=run_context), self.assertRaisesRegex(
                ValueError,
                "run_context keys must exactly match the run context schema",
            ):
                assemble_persisted_simulation_application_inputs(
                    document=_corrupt_document(document, run_context=run_context)
                )

    def test_strategy_and_policy_validation(self) -> None:
        document = _document()
        cases = (
            ("strategy_name", "wrong", "strategy.strategy_name must be RuleBasedBetStrategy"),
            ("allowed_bet_types", ("単勝", "単勝"), "strategy.allowed_bet_types must contain unique supported bet types"),
            ("max_bet_count", True, "strategy.max_bet_count must be a non-negative integer"),
            ("selection_style", "other", "strategy.selection_style must be box or formation"),
            ("sort_condition", "other", "strategy.sort_condition is unsupported"),
        )
        for key, value, error in cases:
            strategy = dict(document.strategy)
            strategy[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, error):
                assemble_persisted_simulation_application_inputs(
                    document=_replace_document(document, strategy=strategy)
                )
        strategy = dict(document.strategy)
        strategy["allocation_policy"] = {"policy_name": "other", "policy_version": "1", "parameters": {"stake_amount": 100}}
        with self.assertRaisesRegex(ValueError, "strategy.allocation_policy.policy_name is unsupported"):
            assemble_persisted_simulation_application_inputs(document=_replace_document(document, strategy=strategy))

    def test_strategy_policy_schema_and_stake_matrix(self) -> None:
        document = _document()
        with self.assertRaisesRegex(ValueError, "strategy keys must exactly match the strategy schema"):
            assemble_persisted_simulation_application_inputs(
                document=_replace_document(document, strategy={"strategy_name": "RuleBasedBetStrategy"})
            )
        cases = (
            ({"policy_name": "fixed_stake_per_recommendation"}, "strategy.allocation_policy keys must exactly match the allocation policy schema"),
            ({"policy_name": "fixed_stake_per_recommendation", "policy_version": 1, "parameters": {"stake_amount": 100}}, "strategy.allocation_policy.policy_version is unsupported"),
            ({"policy_name": "fixed_stake_per_recommendation", "policy_version": "1", "parameters": {"other": 100}}, "strategy.allocation_policy.parameters keys must exactly match the fixed stake schema"),
        )
        for policy, error in cases:
            strategy = dict(document.strategy)
            strategy["allocation_policy"] = policy
            with self.subTest(policy=policy), self.assertRaisesRegex(ValueError, error):
                assemble_persisted_simulation_application_inputs(
                    document=_replace_document(document, strategy=strategy)
                )

    def test_corrupt_strategy_scalar_and_mapping_matrix(self) -> None:
        document = _document()
        cases = (
            ("not-a-mapping", "strategy keys must exactly match the strategy schema"),
            ({}, "strategy keys must exactly match the strategy schema"),
        )
        for strategy, error in cases:
            with self.subTest(strategy=strategy), self.assertRaisesRegex(ValueError, error):
                assemble_persisted_simulation_application_inputs(
                    document=_corrupt_document(document, strategy=strategy)
                )
        scalar_cases = (
            ("allowed_bet_types", ["単勝"], "strategy.allowed_bet_types must be an array"),
            ("allowed_bet_types", (1,), "strategy.allowed_bet_types must contain unique supported bet types"),
            ("allowed_bet_types", ("unsupported",), "strategy.allowed_bet_types must contain unique supported bet types"),
            ("max_bet_count", -1, "strategy.max_bet_count must be a non-negative integer"),
            ("max_candidates", True, "strategy.max_candidates must be a non-negative integer"),
            ("max_candidates", -1, "strategy.max_candidates must be a non-negative integer"),
            ("min_combination_score", True, "strategy.min_combination_score must be finite"),
            ("min_combination_score", float("nan"), "strategy.min_combination_score must be finite"),
            ("min_combination_score", float("inf"), "strategy.min_combination_score must be finite"),
            ("allocation_policy", None, "strategy.allocation_policy must be an object"),
        )
        for key, value, error in scalar_cases:
            strategy = dict(document.strategy)
            strategy[key] = value
            with self.subTest(key=key, value=value), self.assertRaisesRegex(ValueError, error):
                assemble_persisted_simulation_application_inputs(
                    document=_corrupt_document(document, strategy=strategy)
                )
        strategy = dict(document.strategy)
        strategy["allocation_policy"] = {
            "policy_name": "fixed_stake_per_recommendation",
            "policy_version": "1",
            "parameters": None,
        }
        with self.assertRaisesRegex(ValueError, "strategy.allocation_policy.parameters must be an object"):
            assemble_persisted_simulation_application_inputs(
                document=_corrupt_document(document, strategy=strategy)
            )
        for amount in (True, 0, -100, 50):
            strategy = dict(document.strategy)
            strategy["allocation_policy"] = {
                "policy_name": "fixed_stake_per_recommendation",
                "policy_version": "1",
                "parameters": {"stake_amount": amount},
            }
            with self.subTest(amount=amount), self.assertRaisesRegex(
                ValueError,
                "strategy.allocation_policy.parameters.stake_amount must be a positive multiple of 100",
            ):
                assemble_persisted_simulation_application_inputs(
                    document=_replace_document(document, strategy=strategy)
                )

    def test_finite_score_huge_integer_and_valid_value_matrix(self) -> None:
        document = _document()
        for score in (10**1000, -(10**1000)):
            strategy = dict(document.strategy)
            strategy["min_combination_score"] = score
            with self.subTest(score=score > 0), self.assertRaisesRegex(
                ValueError,
                "strategy.min_combination_score must be finite",
            ):
                assemble_persisted_simulation_application_inputs(
                    document=_corrupt_document(document, strategy=strategy)
                )
        for score in (-1, 0, 1, -1.5, 0.0, 1.5):
            strategy = dict(document.strategy)
            strategy["min_combination_score"] = score
            result = assemble_persisted_simulation_application_inputs(
                document=_replace_document(document, strategy=strategy)
            )
            with self.subTest(score=score):
                self.assertIs(type(result.strategy_identity.strategy_config.min_combination_score), float)
                self.assertEqual(result.strategy_identity.strategy_config.min_combination_score, float(score))

    def test_pipeline_and_budget_validation(self) -> None:
        document = _document()
        with self.assertRaisesRegex(ValueError, "pipeline.track_reference_date must be an ISO date"):
            assemble_persisted_simulation_application_inputs(
                document=_replace_document(document, pipeline={"track_reference_date": "not-a-date"})
            )
        invalid_budgets = (
            ({"01": {"total_amount": 100}}, "budgets_by_race_id keys must be canonical positive integer strings"),
            ({"1": 100}, "budgets_by_race_id values must be objects"),
            ({"1": {"other": 100}}, "budget keys must exactly match the budget schema"),
            ({"1": {"total_amount": 50}}, "budget.total_amount must be a non-negative multiple of 100"),
        )
        for budgets, error in invalid_budgets:
            with self.subTest(budgets=budgets), self.assertRaisesRegex(ValueError, error):
                assemble_persisted_simulation_application_inputs(
                    document=_replace_document(document, budgets_by_race_id=budgets)
                )

    def test_track_reference_date_must_be_canonical_iso_date(self) -> None:
        document = _document()
        valid = assemble_persisted_simulation_application_inputs(document=document)
        self.assertEqual(valid.prediction_pipeline.config.track_engine.reference_date.isoformat(), "2026-08-05")
        for value in (
            "20260805",
            "2026-W32-3",
            "2026/08/05",
            "2026-8-5",
            "2026-08-05T00:00:00",
            "",
            " ",
            1,
            True,
            None,
        ):
            with self.subTest(value=value), self.assertRaisesRegex(
                ValueError,
                "pipeline.track_reference_date must be an ISO date",
            ):
                assemble_persisted_simulation_application_inputs(
                    document=_corrupt_document(document, pipeline={"track_reference_date": value})
                )

    def test_pipeline_and_budget_schema_matrices(self) -> None:
        document = _document()
        for pipeline in ({}, {"track_reference_date": "2026-08-05", "extra": 1}):
            with self.subTest(pipeline=pipeline), self.assertRaisesRegex(
                ValueError,
                "pipeline keys must exactly match the pipeline schema",
            ):
                assemble_persisted_simulation_application_inputs(
                    document=_replace_document(document, pipeline=pipeline)
                )
        for key in ("0", "-1", "+1", "01", "1.0", " 1", "1 "):
            with self.subTest(key=key), self.assertRaisesRegex(
                ValueError,
                "budgets_by_race_id keys must be canonical positive integer strings",
            ):
                assemble_persisted_simulation_application_inputs(
                    document=_replace_document(document, budgets_by_race_id={key: {"total_amount": 100}})
                )
        empty = assemble_persisted_simulation_application_inputs(
            document=_replace_document(document, budgets_by_race_id={})
        )
        self.assertEqual(dict(empty.budgets_by_race_id), {})

    def test_corrupt_pipeline_and_budget_container_matrix(self) -> None:
        document = _document()
        for pipeline, error in (
            (None, "pipeline keys must exactly match the pipeline schema"),
            ({"track_reference_date": 1}, "pipeline.track_reference_date must be an ISO date"),
            ({"track_reference_date": "2026/08/05"}, "pipeline.track_reference_date must be an ISO date"),
        ):
            with self.subTest(pipeline=pipeline), self.assertRaisesRegex(ValueError, error):
                assemble_persisted_simulation_application_inputs(
                    document=_corrupt_document(document, pipeline=pipeline)
                )
        with self.assertRaisesRegex(
            ValueError,
            "budgets_by_race_id keys must be canonical positive integer strings",
        ):
            assemble_persisted_simulation_application_inputs(
                document=_corrupt_document(document, budgets_by_race_id=None)
            )
        for budget in ({"total_amount": True}, {"total_amount": -100}, {"total_amount": 50}):
            with self.subTest(budget=budget), self.assertRaisesRegex(
                ValueError,
                "budget.total_amount must be a non-negative multiple of 100",
            ):
                assemble_persisted_simulation_application_inputs(
                    document=_corrupt_document(document, budgets_by_race_id={"1": budget})
                )

    def test_direct_output_validation_and_defensive_copy(self) -> None:
        policy = AllocationPolicyConfig("fixed_stake_per_recommendation", "1", {"stake_amount": 100})
        config = StrategyConfig(allocation_policy=policy)
        identity = build_strategy_identity("RuleBasedBetStrategy", config)
        pipeline = PredictionPipeline(PipelineConfig(strategy_config=config))
        supplied = {2: BetStakeBudget(100)}
        output = PersistedSimulationApplicationInputs(Path("db"), SimulationRunContext("run", "dataset", datetime(2026, 8, 5, tzinfo=timezone.utc), "commit"), identity, pipeline, supplied)
        supplied[1] = BetStakeBudget(100)
        supplied[2] = BetStakeBudget(200)
        self.assertEqual(list(output.budgets_by_race_id), [2])
        self.assertEqual(output.budgets_by_race_id[2], BetStakeBudget(100))
        with self.assertRaisesRegex(ValueError, "budgets_by_race_id keys must be positive integers"):
            PersistedSimulationApplicationInputs(Path("db"), output.run_context, identity, pipeline, {True: BetStakeBudget(100)})
        with self.assertRaisesRegex(ValueError, "prediction_pipeline strategy_config must be strategy_identity.strategy_config"):
            PersistedSimulationApplicationInputs(Path("db"), output.run_context, identity, PredictionPipeline(), {})
        for value, error in (
            ("db", "database_path must be a Path"),
            (object(), "run_context must be a SimulationRunContext"),
            (object(), "strategy_identity must be a StrategyIdentity"),
            (object(), "prediction_pipeline must be a PredictionPipeline"),
        ):
            arguments = [Path("db"), output.run_context, identity, pipeline, {}]
            arguments[("database_path", "run_context", "strategy_identity", "prediction_pipeline").index(
                error.split(" must be ")[0]
            )] = value
            with self.subTest(error=error), self.assertRaisesRegex(ValueError, error):
                PersistedSimulationApplicationInputs(*arguments)

    def test_direct_output_exact_type_and_precondition_matrix(self) -> None:
        policy = AllocationPolicyConfig("fixed_stake_per_recommendation", "1", {"stake_amount": 100})
        config = StrategyConfig(allocation_policy=policy)
        identity = build_strategy_identity("RuleBasedBetStrategy", config)
        run_context = SimulationRunContext("run", "dataset", datetime(2026, 8, 5, tzinfo=timezone.utc), "commit")
        pipeline = PredictionPipeline(PipelineConfig(strategy_config=config))

        class RunContextSubclass(SimulationRunContext):
            pass

        class IdentitySubclass(StrategyIdentity):
            pass

        class PipelineSubclass(PredictionPipeline):
            pass

        subclass_cases = (
            (RunContextSubclass("run", "dataset", datetime(2026, 8, 5, tzinfo=timezone.utc), "commit"), identity, pipeline, "run_context must be a SimulationRunContext"),
            (run_context, IdentitySubclass(identity.strategy_id, identity.strategy_name, config, identity.strategy_config_hash), pipeline, "strategy_identity must be a StrategyIdentity"),
            (run_context, identity, PipelineSubclass(PipelineConfig(strategy_config=config)), "prediction_pipeline must be a PredictionPipeline"),
        )
        for supplied_context, supplied_identity, supplied_pipeline, error in subclass_cases:
            with self.subTest(error=error), self.assertRaisesRegex(ValueError, error):
                PersistedSimulationApplicationInputs(Path("db"), supplied_context, supplied_identity, supplied_pipeline, {})
        with self.assertRaisesRegex(ValueError, "budgets_by_race_id must be a Mapping"):
            PersistedSimulationApplicationInputs(Path("db"), run_context, identity, pipeline, object())
        for race_id in (True, 0, -1):
            with self.subTest(race_id=race_id), self.assertRaisesRegex(ValueError, "budgets_by_race_id keys must be positive integers"):
                PersistedSimulationApplicationInputs(Path("db"), run_context, identity, pipeline, {race_id: BetStakeBudget(100)})
        with self.assertRaisesRegex(ValueError, "budgets_by_race_id values must be BetStakeBudget"):
            PersistedSimulationApplicationInputs(Path("db"), run_context, identity, pipeline, {1: object()})
        pipeline.config = object()
        with self.assertRaisesRegex(ValueError, "prediction_pipeline.config must be a PipelineConfig"):
            PersistedSimulationApplicationInputs(Path("db"), run_context, identity, pipeline, {})
        no_policy_config = StrategyConfig(allocation_policy=None)
        no_policy_identity = build_strategy_identity("RuleBasedBetStrategy", no_policy_config)
        no_policy_pipeline = PredictionPipeline(PipelineConfig(strategy_config=no_policy_config))
        with self.assertRaisesRegex(ValueError, "strategy_identity allocation_policy must be an AllocationPolicyConfig"):
            PersistedSimulationApplicationInputs(Path("db"), run_context, no_policy_identity, no_policy_pipeline, {})

        class AllocationPolicySubclass(AllocationPolicyConfig):
            pass

        subclass_policy = AllocationPolicySubclass(
            "fixed_stake_per_recommendation",
            "1",
            {"stake_amount": 100},
        )
        subclass_config = StrategyConfig(allocation_policy=subclass_policy)
        subclass_identity = build_strategy_identity("RuleBasedBetStrategy", subclass_config)
        subclass_pipeline = PredictionPipeline(PipelineConfig(strategy_config=subclass_config))
        with self.assertRaisesRegex(ValueError, "strategy_identity allocation_policy must be an AllocationPolicyConfig"):
            PersistedSimulationApplicationInputs(
                Path("db"),
                run_context,
                subclass_identity,
                subclass_pipeline,
                {},
            )

    def test_source_responsibility_boundary(self) -> None:
        module = inspect.getmodule(assemble_persisted_simulation_application_inputs)
        self.assertIsNotNone(module)
        source = inspect.getsource(module)
        self.assertIn("class PersistedSimulationApplicationInputs", source)
        forbidden_fragments = (
            "Path.read_text", "json.loads", "sqlite3", "apply_migrations", "run_sqlite_persisted_simulation",
            "build_sqlite_persisted_simulation_run_service", "SimulationRaceInput", "RacePredictionInput",
            "ImmutableRacePredictionInput", "PastRace", "RaceTrackConditions", "InputAuditEntry",
            "InputSnapshotAudit", "repository", "subprocess", "requests", "logging", "print(", "argparse",
            "stdout", "stderr", "datetime.now", "datetime.utcnow", "date.today", "uuid", "os.environ",
            "config/settings.json", "main.py",
        )
        for fragment in forbidden_fragments:
            self.assertNotIn(fragment, source)
        tree = ast.parse(source)
        self.assertEqual(tree.type_ignores, [])
        imported_names = {
            alias.asname or alias.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        self.assertNotIn("Any", imported_names)
        self.assertNotIn("cast", imported_names)
        self.assertNotIn("runtime_checkable", imported_names)
        named_identifiers = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        self.assertNotIn("Any", named_identifiers)
        self.assertNotIn("cast", named_identifiers)
        handled = [
            (function.name, ast.unparse(handler.type))
            for function in tree.body
            if isinstance(function, ast.FunctionDef)
            for handler in ast.walk(function)
            if isinstance(handler, ast.ExceptHandler)
        ]
        self.assertEqual(
            handled,
            [
                ("_parse_aware_datetime", "ValueError"),
                ("_parse_iso_date", "ValueError"),
            ],
        )
        self.assertFalse(any(name in {"Exception", "BaseException", "OverflowError"} for _, name in handled))

    def test_public_definitions_and_package_root_non_export(self) -> None:
        module = inspect.getmodule(assemble_persisted_simulation_application_inputs)
        self.assertIsNotNone(module)
        public_definitions = {
            name
            for name, value in inspect.getmembers(module)
            if (inspect.isclass(value) or inspect.isfunction(value))
            and value.__module__ == module.__name__
            and not name.startswith("_")
        }
        self.assertEqual(
            public_definitions,
            {
                "PersistedSimulationApplicationInputs",
                "assemble_persisted_simulation_application_inputs",
            },
        )
        self.assertFalse(hasattr(simulation_package, "PersistedSimulationApplicationInputs"))
        self.assertFalse(hasattr(simulation_package, "assemble_persisted_simulation_application_inputs"))


def _replace_document(
    document: PersistedSimulationRequestDocument,
    *,
    run_context: object | None = None,
    strategy: object | None = None,
    pipeline: object | None = None,
    budgets_by_race_id: object | None = None,
) -> PersistedSimulationRequestDocument:
    return PersistedSimulationRequestDocument(
        schema_version=1,
        source_path=document.source_path,
        database_path=document.database_path,
        run_context=document.run_context if run_context is None else run_context,
        strategy=document.strategy if strategy is None else strategy,
        pipeline=document.pipeline if pipeline is None else pipeline,
        races=document.races,
        budgets_by_race_id=document.budgets_by_race_id if budgets_by_race_id is None else budgets_by_race_id,
    )


def _corrupt_document(
    document: PersistedSimulationRequestDocument,
    **overrides: object,
) -> PersistedSimulationRequestDocument:
    """Create an exact document type with malformed nested content for boundary tests."""

    corrupt = object.__new__(PersistedSimulationRequestDocument)
    for field in fields(PersistedSimulationRequestDocument):
        object.__setattr__(corrupt, field.name, overrides.get(field.name, getattr(document, field.name)))
    return corrupt
