from __future__ import annotations

import ast
from collections.abc import Mapping
from dataclasses import replace
from datetime import UTC, datetime, timedelta
import inspect
from typing import get_type_hints
import unittest
from unittest.mock import patch

import scripts.simulation as simulation_package
import scripts.simulation.historical_prediction_bet_plan_batch_execution as batch_module
from scripts.prediction.allocation_policy import (
    AllocationPolicyConfig,
    build_allocation_policy_identity,
)
from scripts.prediction.bet_strategy import StrategyConfig
from scripts.simulation.bet_plan_identity import SimulationBetPlanIdentity
from scripts.simulation.bet_plan_snapshot import SimulationBetPlanSnapshot
from scripts.simulation.bet_plan_snapshot_repository import (
    SimulationBetPlanSnapshotRepository,
)
from scripts.simulation.historical_input_snapshots import HistoricalInputSnapshot
from scripts.simulation.models import (
    SimulationRunContext,
    StrategyIdentity,
    build_strategy_identity,
)
from scripts.simulation.stake_allocation import BetStakeBudget
from scripts.simulation.validation import SimulationValidationError
from tests.test_historical_input_snapshot_simulation_adapter import _snapshot


class RecordingSnapshotRepository:
    def __init__(self) -> None:
        self.saved: list[SimulationBetPlanSnapshot] = []

    def save_snapshot(self, *, snapshot: SimulationBetPlanSnapshot) -> None:
        self.saved.append(snapshot)


def _strategy_identity(*, name: str = "RuleBasedBetStrategy") -> StrategyIdentity:
    return build_strategy_identity(
        name,
        StrategyConfig(
            max_bet_count=0,
            allocation_policy=AllocationPolicyConfig(
                policy_name="fixed_stake_per_recommendation",
                policy_version="1",
                parameters={"stake_amount": 100},
            ),
        ),
    )


def _run_context(*, dataset_id: str = "historical-dataset", run_id: str = "run") -> SimulationRunContext:
    return SimulationRunContext(
        run_id=run_id,
        dataset_id=dataset_id,
        started_at=datetime(2026, 8, 6, tzinfo=UTC),
        target_commit_id="commit",
    )


def _historical_snapshot(
    *,
    race_id: int,
    start_offset: int,
    dataset_id: str = "historical-dataset",
) -> HistoricalInputSnapshot:
    base = _snapshot()
    identity = replace(base.identity, dataset_id=dataset_id)
    race = replace(
        base.race,
        scheduled_start_at=base.race.scheduled_start_at + timedelta(minutes=start_offset),
    )
    return replace(base, identity=identity, internal_race_id=race_id, race=race)


def _result(
    *,
    snapshot: HistoricalInputSnapshot,
    run_context: SimulationRunContext,
    strategy_identity: StrategyIdentity,
    budget: BetStakeBudget,
) -> SimulationBetPlanSnapshot:
    return SimulationBetPlanSnapshot(
        identity=SimulationBetPlanIdentity(
            run_id=run_context.run_id,
            race_id=snapshot.internal_race_id,
            strategy_id=strategy_identity.strategy_id,
            strategy_config_hash=strategy_identity.strategy_config_hash,
            information_cutoff=snapshot.information_cutoff,
        ),
        policy_identity=build_allocation_policy_identity(
            strategy_identity.strategy_config.allocation_policy
        ),
        budget=budget,
        bets=(),
    )


class HistoricalPredictionBetPlanBatchExecutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.first = _historical_snapshot(race_id=101, start_offset=20)
        self.second = _historical_snapshot(race_id=102, start_offset=10)
        self.third = _historical_snapshot(race_id=103, start_offset=10)
        self.run_context = _run_context()
        self.strategy_identity = _strategy_identity()
        self.budgets = {
            101: BetStakeBudget(total_amount=0),
            102: BetStakeBudget(total_amount=0),
            103: BetStakeBudget(total_amount=0),
        }
        self.repository = RecordingSnapshotRepository()

    def _call(self, **overrides: object) -> tuple[SimulationBetPlanSnapshot, ...]:
        values: dict[str, object] = {
            "snapshots": (self.first, self.second, self.third),
            "run_context": self.run_context,
            "strategy_identity": self.strategy_identity,
            "budgets_by_race_id": self.budgets,
            "snapshot_repository": self.repository,
        }
        values.update(overrides)
        return batch_module.execute_and_persist_historical_bet_plans(**values)  # type: ignore[arg-type]

    def _recording_c4g0(
        self,
        calls: list[dict[str, object]],
        *,
        side_effect: object | None = None,
    ) -> object:
        def execute(**kwargs: object) -> SimulationBetPlanSnapshot:
            calls.append(kwargs)
            if isinstance(side_effect, BaseException):
                if len(calls) == 3:
                    raise side_effect
            snapshot = kwargs["snapshot"]
            run_context = kwargs["run_context"]
            strategy_identity = kwargs["strategy_identity"]
            budget = kwargs["budget"]
            repository = kwargs["snapshot_repository"]
            assert type(snapshot) is HistoricalInputSnapshot
            assert type(run_context) is SimulationRunContext
            assert type(strategy_identity) is StrategyIdentity
            assert type(budget) is BetStakeBudget
            result = _result(
                snapshot=snapshot,
                run_context=run_context,
                strategy_identity=strategy_identity,
                budget=budget,
            )
            if isinstance(repository, RecordingSnapshotRepository):
                repository.save_snapshot(snapshot=result)
            return result

        return execute

    def test_exact_public_surface_signature_and_annotations(self) -> None:
        self.assertEqual(
            batch_module.__all__,
            ("execute_and_persist_historical_bet_plans",),
        )
        self.assertFalse(
            hasattr(simulation_package, "execute_and_persist_historical_bet_plans")
        )
        signature = inspect.signature(
            batch_module.execute_and_persist_historical_bet_plans
        )
        self.assertEqual(
            tuple(signature.parameters),
            (
                "snapshots",
                "run_context",
                "strategy_identity",
                "budgets_by_race_id",
                "snapshot_repository",
            ),
        )
        self.assertTrue(
            all(
                parameter.kind is inspect.Parameter.KEYWORD_ONLY
                for parameter in signature.parameters.values()
            )
        )
        hints = get_type_hints(batch_module.execute_and_persist_historical_bet_plans)
        self.assertEqual(hints["snapshots"], tuple[HistoricalInputSnapshot, ...])
        self.assertIs(hints["run_context"], SimulationRunContext)
        self.assertIs(hints["strategy_identity"], StrategyIdentity)
        self.assertEqual(hints["budgets_by_race_id"], Mapping[int, BetStakeBudget])
        self.assertIs(
            hints["snapshot_repository"], SimulationBetPlanSnapshotRepository
        )
        self.assertEqual(hints["return"], tuple[SimulationBetPlanSnapshot, ...])

    def test_invalid_snapshot_boundaries_fail_before_c4g0(self) -> None:
        class SnapshotTuple(tuple[HistoricalInputSnapshot, ...]):
            pass

        invalid_values = (
            [self.first],
            SnapshotTuple((self.first,)),
            (object(),),
            (self.first, object()),
        )
        for snapshots in invalid_values:
            with self.subTest(snapshots=type(snapshots).__name__):
                calls: list[dict[str, object]] = []
                with patch.object(
                    batch_module,
                    "execute_and_persist_historical_bet_plan",
                    side_effect=self._recording_c4g0(calls),
                ):
                    with self.assertRaises(ValueError):
                        self._call(snapshots=snapshots)
                self.assertEqual(calls, [])
                self.assertEqual(self.repository.saved, [])

    def test_invalid_shared_boundaries_and_strategy_fail_before_c4g0(self) -> None:
        invalid = (
            {"run_context": object()},
            {"strategy_identity": object()},
            {"budgets_by_race_id": []},
            {"budgets_by_race_id": dict},
            {"snapshot_repository": object()},
            {"snapshot_repository": RecordingSnapshotRepository},
            {"strategy_identity": _strategy_identity(name="OtherStrategy")},
        )
        for overrides in invalid:
            with self.subTest(overrides=overrides):
                calls: list[dict[str, object]] = []
                with patch.object(
                    batch_module,
                    "execute_and_persist_historical_bet_plan",
                    side_effect=self._recording_c4g0(calls),
                ):
                    with self.assertRaises(ValueError):
                        self._call(**overrides)
                self.assertEqual(calls, [])
                self.assertEqual(self.repository.saved, [])

    def test_invalid_budget_items_fail_before_c4g0(self) -> None:
        invalid_mappings = (
            {True: BetStakeBudget(0)},
            {0: BetStakeBudget(0)},
            {-1: BetStakeBudget(0)},
            {"101": BetStakeBudget(0)},
            {101: object()},
        )
        for budgets in invalid_mappings:
            with self.subTest(budgets=repr(budgets)):
                calls: list[dict[str, object]] = []
                with patch.object(
                    batch_module,
                    "execute_and_persist_historical_bet_plan",
                    side_effect=self._recording_c4g0(calls),
                ):
                    with self.assertRaises(ValueError):
                        self._call(snapshots=(self.first,), budgets_by_race_id=budgets)
                self.assertEqual(calls, [])
                self.assertEqual(self.repository.saved, [])

    def test_empty_batch_requires_empty_budgets_and_has_no_execution(self) -> None:
        calls: list[dict[str, object]] = []
        with patch.object(
            batch_module,
            "execute_and_persist_historical_bet_plan",
            side_effect=self._recording_c4g0(calls),
        ):
            self.assertEqual(self._call(snapshots=(), budgets_by_race_id={}), ())
            with self.assertRaises(ValueError):
                self._call(
                    snapshots=(),
                    budgets_by_race_id={101: BetStakeBudget(0)},
                )
        self.assertEqual(calls, [])
        self.assertEqual(self.repository.saved, [])

    def test_canonical_order_tie_break_and_exact_delegation_identity(self) -> None:
        calls: list[dict[str, object]] = []
        with patch.object(
            batch_module,
            "execute_and_persist_historical_bet_plan",
            side_effect=self._recording_c4g0(calls),
        ):
            result = self._call(snapshots=(self.first, self.third, self.second))

        self.assertEqual(
            [call["snapshot"].internal_race_id for call in calls],  # type: ignore[union-attr]
            [102, 103, 101],
        )
        self.assertEqual([item.identity.race_id for item in result], [102, 103, 101])
        self.assertEqual(len(calls), 3)
        for call, expected_snapshot in zip(
            calls,
            (self.second, self.third, self.first),
            strict=True,
        ):
            self.assertIs(call["snapshot"], expected_snapshot)
            self.assertIs(call["run_context"], self.run_context)
            self.assertIs(call["strategy_identity"], self.strategy_identity)
            self.assertIs(call["snapshot_repository"], self.repository)
            self.assertIs(
                call["budget"],
                self.budgets[expected_snapshot.internal_race_id],
            )
        self.assertEqual(len(self.repository.saved), 3)
        for saved, returned in zip(self.repository.saved, result, strict=True):
            self.assertIs(saved, returned)

    def test_snapshot_permutation_and_budget_mapping_order_do_not_change_results(self) -> None:
        first_calls: list[dict[str, object]] = []
        second_calls: list[dict[str, object]] = []
        first_repository = RecordingSnapshotRepository()
        second_repository = RecordingSnapshotRepository()
        reversed_budgets = {
            103: self.budgets[103],
            101: self.budgets[101],
            102: self.budgets[102],
        }
        with patch.object(
            batch_module,
            "execute_and_persist_historical_bet_plan",
            side_effect=self._recording_c4g0(first_calls),
        ):
            first = self._call(
                snapshots=(self.first, self.third, self.second),
                snapshot_repository=first_repository,
            )
        with patch.object(
            batch_module,
            "execute_and_persist_historical_bet_plan",
            side_effect=self._recording_c4g0(second_calls),
        ):
            second = self._call(
                snapshots=(self.second, self.first, self.third),
                budgets_by_race_id=reversed_budgets,
                snapshot_repository=second_repository,
            )
        self.assertEqual(first, second)
        self.assertEqual(
            [call["snapshot"].internal_race_id for call in first_calls],  # type: ignore[union-attr]
            [102, 103, 101],
        )
        self.assertEqual(
            [call["snapshot"].internal_race_id for call in second_calls],  # type: ignore[union-attr]
            [102, 103, 101],
        )

    def test_duplicate_race_and_budget_coverage_fail_before_c4g0(self) -> None:
        duplicate = _historical_snapshot(race_id=101, start_offset=0)
        invalid_cases = (
            ((self.first, duplicate), {101: BetStakeBudget(0)}),
            ((self.first, self.second), {101: BetStakeBudget(0)}),
            ((self.first,), {101: BetStakeBudget(0), 999: BetStakeBudget(0)}),
            ((self.first,), {999: BetStakeBudget(0)}),
        )
        for snapshots, budgets in invalid_cases:
            with self.subTest(snapshots=tuple(item.internal_race_id for item in snapshots)):
                calls: list[dict[str, object]] = []
                with patch.object(
                    batch_module,
                    "execute_and_persist_historical_bet_plan",
                    side_effect=self._recording_c4g0(calls),
                ):
                    with self.assertRaises(ValueError):
                        self._call(snapshots=snapshots, budgets_by_race_id=budgets)
                self.assertEqual(calls, [])
                self.assertEqual(self.repository.saved, [])

    def test_budget_mapping_is_frozen_before_execution(self) -> None:
        original = {
            101: self.budgets[101],
            102: self.budgets[102],
        }
        calls: list[dict[str, object]] = []

        def mutate_then_return(**kwargs: object) -> SimulationBetPlanSnapshot:
            calls.append(kwargs)
            if len(calls) == 1:
                original[102] = BetStakeBudget(100)
                original[999] = BetStakeBudget(0)
            snapshot = kwargs["snapshot"]
            run_context = kwargs["run_context"]
            strategy_identity = kwargs["strategy_identity"]
            budget = kwargs["budget"]
            assert type(snapshot) is HistoricalInputSnapshot
            assert type(run_context) is SimulationRunContext
            assert type(strategy_identity) is StrategyIdentity
            assert type(budget) is BetStakeBudget
            return _result(
                snapshot=snapshot,
                run_context=run_context,
                strategy_identity=strategy_identity,
                budget=budget,
            )

        with patch.object(
            batch_module,
            "execute_and_persist_historical_bet_plan",
            side_effect=mutate_then_return,
        ):
            self._call(snapshots=(self.first, self.second), budgets_by_race_id=original)
        self.assertIs(calls[0]["budget"], self.budgets[102])
        self.assertIs(calls[1]["budget"], self.budgets[101])
        self.assertIsNot(calls[1]["budget"], original[102])
        self.assertNotIn(999, {call["snapshot"].internal_race_id for call in calls})  # type: ignore[union-attr]

    def test_all_dataset_mismatches_are_preflighted_in_canonical_order(self) -> None:
        mismatch_first = _historical_snapshot(
            race_id=300,
            start_offset=0,
            dataset_id="other-a",
        )
        mismatch_second = _historical_snapshot(
            race_id=200,
            start_offset=10,
            dataset_id="other-b",
        )
        calls: list[dict[str, object]] = []
        with patch.object(
            batch_module,
            "execute_and_persist_historical_bet_plan",
            side_effect=self._recording_c4g0(calls),
        ):
            with self.assertRaises(SimulationValidationError) as raised:
                self._call(
                    snapshots=(self.first, mismatch_second, mismatch_first),
                    budgets_by_race_id={
                        101: BetStakeBudget(0),
                        200: BetStakeBudget(0),
                        300: BetStakeBudget(0),
                    },
                )
        self.assertEqual(raised.exception.race_id, 300)
        self.assertEqual(raised.exception.input_identifier, "run_context.dataset_id")
        self.assertEqual(
            raised.exception.reason,
            "run_context.dataset_id does not match snapshot.identity.dataset_id",
        )
        self.assertEqual(calls, [])
        self.assertEqual(self.repository.saved, [])

    def test_mid_batch_failure_propagates_without_partial_return_or_later_execution(self) -> None:
        error = RuntimeError("race three failed")
        calls: list[dict[str, object]] = []
        completed: list[int] = []

        def execute(**kwargs: object) -> SimulationBetPlanSnapshot:
            calls.append(kwargs)
            snapshot = kwargs["snapshot"]
            assert type(snapshot) is HistoricalInputSnapshot
            if snapshot.internal_race_id == 103:
                raise error
            completed.append(snapshot.internal_race_id)
            run_context = kwargs["run_context"]
            strategy_identity = kwargs["strategy_identity"]
            budget = kwargs["budget"]
            assert type(run_context) is SimulationRunContext
            assert type(strategy_identity) is StrategyIdentity
            assert type(budget) is BetStakeBudget
            return _result(
                snapshot=snapshot,
                run_context=run_context,
                strategy_identity=strategy_identity,
                budget=budget,
            )

        race_one = _historical_snapshot(race_id=101, start_offset=0)
        race_two = _historical_snapshot(race_id=102, start_offset=10)
        race_three = _historical_snapshot(race_id=103, start_offset=20)
        race_four = _historical_snapshot(race_id=104, start_offset=30)
        budgets = {
            101: BetStakeBudget(0),
            102: BetStakeBudget(0),
            103: BetStakeBudget(0),
            104: BetStakeBudget(0),
        }
        with patch.object(
            batch_module,
            "execute_and_persist_historical_bet_plan",
            side_effect=execute,
        ):
            with self.assertRaises(RuntimeError) as raised:
                self._call(
                    snapshots=(race_four, race_one, race_three, race_two),
                    budgets_by_race_id=budgets,
                )
        self.assertIs(raised.exception, error)
        self.assertEqual(
            [call["snapshot"].internal_race_id for call in calls],  # type: ignore[union-attr]
            [101, 102, 103],
        )
        self.assertEqual(completed, [101, 102])

    def test_determinism_has_no_process_local_state_and_preserves_run_context_identity(self) -> None:
        first_calls: list[dict[str, object]] = []
        second_calls: list[dict[str, object]] = []
        with patch.object(
            batch_module,
            "execute_and_persist_historical_bet_plan",
            side_effect=self._recording_c4g0(first_calls),
        ):
            first = self._call(snapshot_repository=RecordingSnapshotRepository())
        with patch.object(
            batch_module,
            "execute_and_persist_historical_bet_plan",
            side_effect=self._recording_c4g0(second_calls),
        ):
            second = self._call(snapshot_repository=RecordingSnapshotRepository())
        self.assertEqual(first, second)
        changed_context = _run_context(run_id="other-run")
        changed_calls: list[dict[str, object]] = []
        with patch.object(
            batch_module,
            "execute_and_persist_historical_bet_plan",
            side_effect=self._recording_c4g0(changed_calls),
        ):
            changed = self._call(
                run_context=changed_context,
                snapshot_repository=RecordingSnapshotRepository(),
            )
        self.assertNotEqual(first[0].identity, changed[0].identity)
        self.assertTrue(all(call["run_context"] is changed_context for call in changed_calls))

    def test_static_scope_contains_only_batch_orchestration_dependencies(self) -> None:
        source = inspect.getsource(batch_module)
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
        forbidden_imports = (
            "sqlite3",
            "requests",
            "httpx",
            "pathlib",
            "subprocess",
            "scripts.simulation.historical_input_snapshot_simulation_adapter",
            "scripts.prediction.prediction_pipeline",
            "scripts.simulation.fixed_stake_allocator",
            "scripts.simulation.exact_race_entry_selection_resolver",
            "scripts.simulation.bet_plan_builder",
            "scripts.simulation.persisted_bet_plan_service",
            "scripts.simulation.persisted_simulation_run_service",
            "scripts.simulation.simulator",
            "scripts.simulation.repositories",
        )
        self.assertFalse(any(name.startswith(forbidden_imports) for name in imports))
        for forbidden_text in (
            "save_snapshot(",
            "datetime.now",
            "date.today",
            "time.time",
            "random",
            "except Exception",
            "except BaseException",
            "Simulator",
            "settlement",
        ):
            self.assertNotIn(forbidden_text, source)
