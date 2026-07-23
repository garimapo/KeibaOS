"""Constructor-only contract for the future multi-race Simulator."""
from __future__ import annotations

import ast
from datetime import date, datetime, timezone
import inspect
import textwrap
from typing import Protocol, get_type_hints
from unittest.mock import patch
import unittest

from scripts.prediction.bet_strategy import StrategyConfig
from scripts.prediction.prediction_pipeline import RacePredictionInput
from scripts.prediction.track_engine import RaceTrackConditions
import scripts.simulation.simulator as simulator_module
from scripts.simulation.models import (
    InputAuditEntry,
    InputSnapshotAudit,
    SettlementStatus,
    SimulationRaceInput,
    SimulationResult,
    SimulationSummary,
    StrategyIdentity,
    build_strategy_identity,
)
from scripts.simulation.simulator import (
    RaceSimulationExecutor,
    SimulationBetEvaluationError,
    Simulator,
    _build_simulation_summary,
)


def executor(*, race_input: SimulationRaceInput) -> SimulationResult:
    raise AssertionError("constructor must not invoke the race executor")


class CallableExecutor:
    def __init__(self) -> None:
        self.calls: list[object] = []

    def __call__(self, *, race_input: SimulationRaceInput) -> SimulationResult:
        self.calls.append(race_input)
        raise AssertionError("constructor must not invoke the race executor")


def identity() -> StrategyIdentity:
    return build_strategy_identity("SimulatorContract", StrategyConfig())


UTC = timezone.utc
CUTOFF = datetime(2026, 7, 24, 9, 0, tzinfo=UTC)


def race_input(race_id: int) -> SimulationRaceInput:
    pipeline_input = RacePredictionInput(
        {1: []},
        {1: "Jockey"},
        RaceTrackConditions("Tokyo", 1600, "turf", "firm"),
        {1: 2.0},
        1,
        race_id,
    )
    audit = InputSnapshotAudit(
        "dataset",
        "source",
        CUTOFF,
        (
            InputAuditEntry("entry", "entry/1", "source", "entry/1", 1, observed_at=CUTOFF),
            InputAuditEntry("odds", "odds/1", "source", "odds/1", 1, observed_at=CUTOFF),
            InputAuditEntry("jockey", "jockey/1", "source", "jockey/1", 1, observed_at=CUTOFF),
            InputAuditEntry("track", "track", "source", "track", None, observed_at=CUTOFF),
            InputAuditEntry("past_race", "past_race/1/none", "source", "past_race/1/none", 1, observed_at=CUTOFF),
        ),
        True,
    )
    return SimulationRaceInput(race_id, date(2026, 7, 24), CUTOFF, CUTOFF, pipeline_input, audit)


def no_bet_result(race_id: int, strategy_id: str) -> SimulationResult:
    return SimulationResult(
        race_id,
        strategy_id,
        (),
        SettlementStatus.NO_BET,
        None,
        0,
    )


def empty_summary(value: StrategyIdentity) -> SimulationSummary:
    return _build_simulation_summary(
        strategy_id=value.strategy_id,
        strategy_name=value.strategy_name,
        strategy_config_hash=value.strategy_config_hash,
        results=(),
    )


class SimulatorContractTests(unittest.TestCase):
    def make(self, *, executor_value: RaceSimulationExecutor = executor) -> Simulator:
        return Simulator(strategy_identity=identity(), race_executor=executor_value)

    def test_simulator_exists(self) -> None:
        self.assertTrue(inspect.isclass(Simulator))

    def test_simulator_is_importable_from_simulator_module(self) -> None:
        self.assertEqual(Simulator.__module__, "scripts.simulation.simulator")

    def test_simulator_is_concrete(self) -> None:
        self.assertFalse(inspect.isabstract(Simulator))

    def test_simulator_has_no_unnecessary_base_class(self) -> None:
        self.assertEqual(Simulator.__bases__, (object,))

    def test_race_executor_is_protocol(self) -> None:
        self.assertTrue(RaceSimulationExecutor._is_protocol)

    def test_race_executor_is_not_runtime_checkable(self) -> None:
        self.assertFalse(RaceSimulationExecutor._is_runtime_protocol)

    def test_constructor_is_keyword_only(self) -> None:
        signature = inspect.signature(Simulator)
        self.assertEqual(tuple(signature.parameters), ("strategy_identity", "race_executor"))
        self.assertTrue(all(parameter.kind is inspect.Parameter.KEYWORD_ONLY for parameter in signature.parameters.values()))

    def test_constructor_rejects_positional_arguments(self) -> None:
        with self.assertRaises(TypeError):
            Simulator(identity(), executor)  # type: ignore[call-arg]

    def test_constructor_requires_strategy_identity(self) -> None:
        with self.assertRaises(TypeError):
            Simulator(race_executor=executor)  # type: ignore[call-arg]

    def test_constructor_requires_race_executor(self) -> None:
        with self.assertRaises(TypeError):
            Simulator(strategy_identity=identity())  # type: ignore[call-arg]

    def test_constructor_rejects_extra_argument(self) -> None:
        with self.assertRaises(TypeError):
            Simulator(strategy_identity=identity(), race_executor=executor, extra=True)  # type: ignore[call-arg]

    def test_constructor_accepts_strategy_identity(self) -> None:
        self.assertIsInstance(self.make().strategy_identity, StrategyIdentity)

    def test_constructor_rejects_non_identity(self) -> None:
        for value in (None, "identity", 1, object()):
            with self.subTest(value=value), self.assertRaises(SimulationBetEvaluationError):
                Simulator(strategy_identity=value, race_executor=executor)  # type: ignore[arg-type]

    def test_constructor_rejects_identity_mapping(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            Simulator(strategy_identity={}, race_executor=executor)  # type: ignore[arg-type]

    def test_constructor_rejects_identity_tuple(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            Simulator(strategy_identity=(), race_executor=executor)  # type: ignore[arg-type]

    def test_constructor_preserves_identity_object(self) -> None:
        value = identity()
        self.assertIs(Simulator(strategy_identity=value, race_executor=executor).strategy_identity, value)

    def test_constructor_exposes_identity_strategy_id(self) -> None:
        value = identity()
        self.assertEqual(Simulator(strategy_identity=value, race_executor=executor).strategy_identity.strategy_id, value.strategy_id)

    def test_constructor_exposes_identity_strategy_name(self) -> None:
        value = identity()
        self.assertEqual(Simulator(strategy_identity=value, race_executor=executor).strategy_identity.strategy_name, value.strategy_name)

    def test_constructor_exposes_identity_config_hash(self) -> None:
        value = identity()
        self.assertEqual(
            Simulator(strategy_identity=value, race_executor=executor).strategy_identity.strategy_config_hash,
            value.strategy_config_hash,
        )

    def test_constructor_does_not_change_identity(self) -> None:
        value = identity()
        before = (value.strategy_id, value.strategy_name, value.strategy_config_hash, value.strategy_config)
        Simulator(strategy_identity=value, race_executor=executor)
        self.assertEqual((value.strategy_id, value.strategy_name, value.strategy_config_hash, value.strategy_config), before)

    def test_constructor_accepts_function_executor(self) -> None:
        self.assertIs(self.make().race_executor, executor)

    def test_constructor_accepts_lambda_executor(self) -> None:
        value = lambda *, race_input: executor(race_input=race_input)
        self.assertIs(Simulator(strategy_identity=identity(), race_executor=value).race_executor, value)

    def test_constructor_accepts_callable_object(self) -> None:
        value = CallableExecutor()
        self.assertIs(Simulator(strategy_identity=identity(), race_executor=value).race_executor, value)

    def test_constructor_rejects_none_executor(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            Simulator(strategy_identity=identity(), race_executor=None)  # type: ignore[arg-type]

    def test_constructor_rejects_integer_executor(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            Simulator(strategy_identity=identity(), race_executor=1)  # type: ignore[arg-type]

    def test_constructor_rejects_string_executor(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            Simulator(strategy_identity=identity(), race_executor="executor")  # type: ignore[arg-type]

    def test_constructor_rejects_list_executor(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            Simulator(strategy_identity=identity(), race_executor=[])  # type: ignore[arg-type]

    def test_constructor_does_not_call_executor(self) -> None:
        value = CallableExecutor()
        Simulator(strategy_identity=identity(), race_executor=value)
        self.assertEqual(value.calls, [])

    def test_constructor_keeps_executor_unwrapped(self) -> None:
        value = CallableExecutor()
        self.assertIs(Simulator(strategy_identity=identity(), race_executor=value).race_executor, value)

    def test_identity_property_has_no_setter(self) -> None:
        self.assertIsNone(Simulator.strategy_identity.fset)

    def test_executor_property_has_no_setter(self) -> None:
        self.assertIsNone(Simulator.race_executor.fset)

    def test_public_identity_reassignment_is_rejected(self) -> None:
        simulator = self.make()
        with self.assertRaises(AttributeError):
            simulator.strategy_identity = identity()  # type: ignore[misc]

    def test_public_executor_reassignment_is_rejected(self) -> None:
        simulator = self.make()
        with self.assertRaises(AttributeError):
            simulator.race_executor = executor  # type: ignore[misc]

    def test_simulator_has_no_instance_dictionary(self) -> None:
        self.assertFalse(hasattr(self.make(), "__dict__"))

    def test_simulator_uses_only_private_storage_slots(self) -> None:
        self.assertEqual(Simulator.__slots__, ("_strategy_identity", "_race_executor"))

    def test_future_run_can_read_identity_for_summary(self) -> None:
        value = self.make().strategy_identity
        self.assertEqual(
            (value.strategy_id, value.strategy_name, value.strategy_config_hash),
            (identity().strategy_id, identity().strategy_name, identity().strategy_config_hash),
        )

    def test_executor_protocol_signature_is_keyword_only(self) -> None:
        signature = inspect.signature(RaceSimulationExecutor.__call__)
        self.assertEqual(tuple(signature.parameters), ("self", "race_input"))
        self.assertIs(signature.parameters["race_input"].kind, inspect.Parameter.KEYWORD_ONLY)

    def test_executor_protocol_type_hints_are_boundary_models(self) -> None:
        hints = get_type_hints(RaceSimulationExecutor.__call__)
        self.assertIs(hints["race_input"], SimulationRaceInput)
        self.assertIs(hints["return"], SimulationResult)

    def test_executor_function_matches_boundary_signature(self) -> None:
        signature = inspect.signature(executor)
        self.assertEqual(tuple(signature.parameters), ("race_input",))
        self.assertIs(signature.parameters["race_input"].kind, inspect.Parameter.KEYWORD_ONLY)

    def test_run_is_keyword_only(self) -> None:
        signature = inspect.signature(Simulator.run)
        self.assertEqual(tuple(signature.parameters), ("self", "race_inputs"))
        self.assertIs(signature.parameters["race_inputs"].kind, inspect.Parameter.KEYWORD_ONLY)

    def test_run_returns_simulation_summary(self) -> None:
        self.assertIs(get_type_hints(Simulator.run)["return"], SimulationSummary)

    def test_constructor_does_not_define_other_execution_api(self) -> None:
        self.assertFalse({"simulate", "simulate_race", "execute", "build_summary"} & set(Simulator.__dict__))

    def test_constructor_source_has_no_provider_or_repository_call(self) -> None:
        source = inspect.getsource(Simulator.__init__)
        self.assertNotIn("Provider", source)
        self.assertNotIn("Repository", source)
        self.assertNotIn("sqlite", source.lower())

    def test_constructor_source_has_no_external_io_or_current_time(self) -> None:
        source = inspect.getsource(Simulator.__init__)
        for forbidden in ("datetime.now", "datetime.utcnow", "logging", "print(", "open(", "requests"):
            self.assertNotIn(forbidden, source)

    def test_constructor_source_has_no_existing_settlement_helper_call(self) -> None:
        tree = ast.parse(textwrap.dedent(inspect.getsource(Simulator.__init__)))
        calls = {node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
        forbidden = {
            "_build_simulation_result_for_race",
            "_build_simulation_summary",
            "_build_settled_simulation_result",
            "_build_non_settled_simulation_result",
            "_build_no_bet_simulation_result",
            "_evaluate_simulation_race_bets",
            "_evaluate_simulation_bet",
            "_decide_non_settled_status",
        }
        self.assertFalse(calls & forbidden)

    def test_constructor_does_not_use_broad_exception_handling(self) -> None:
        tree = ast.parse(textwrap.dedent(inspect.getsource(Simulator.__init__)))
        self.assertFalse(any(isinstance(node, ast.ExceptHandler) and node.type is None for node in ast.walk(tree)))

    def test_constructor_uses_existing_simulation_exception(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            Simulator(strategy_identity=object(), race_executor=executor)  # type: ignore[arg-type]

    def test_constructor_does_not_expose_results_container(self) -> None:
        self.assertFalse(hasattr(self.make(), "results"))

    def test_models_are_not_changed_by_constructor_contract(self) -> None:
        self.assertEqual(SimulationResult.__module__, "scripts.simulation.models")


class SimulatorRunTests(unittest.TestCase):
    def setUp(self) -> None:
        self.identity = identity()
        self.calls: list[SimulationRaceInput] = []

        def tracked_executor(*, race_input: SimulationRaceInput) -> SimulationResult:
            self.calls.append(race_input)
            return no_bet_result(race_input.race_id, self.identity.strategy_id)

        self.simulator = Simulator(
            strategy_identity=self.identity,
            race_executor=tracked_executor,
        )

    def test_run_accepts_multiple_race_inputs(self) -> None:
        inputs = (race_input(1), race_input(2))
        value = self.simulator.run(race_inputs=inputs)
        self.assertIsInstance(value, SimulationSummary)
        self.assertEqual(value.race_count, 2)

    def test_run_calls_executor_once_per_input(self) -> None:
        inputs = (race_input(1), race_input(2), race_input(3))
        self.simulator.run(race_inputs=inputs)
        self.assertEqual(len(self.calls), 3)

    def test_run_calls_executor_in_input_order(self) -> None:
        inputs = (race_input(3), race_input(1), race_input(2))
        self.simulator.run(race_inputs=inputs)
        self.assertEqual(self.calls, list(inputs))

    def test_run_passes_original_race_input_objects_to_executor(self) -> None:
        item = race_input(1)
        self.simulator.run(race_inputs=(item,))
        self.assertIs(self.calls[0], item)

    def test_run_passes_results_to_summary_builder_in_input_order(self) -> None:
        inputs = (race_input(3), race_input(1), race_input(2))
        expected = empty_summary(self.identity)
        with patch.object(simulator_module, "_build_simulation_summary", return_value=expected) as builder:
            self.simulator.run(race_inputs=inputs)
        self.assertEqual(
            builder.call_args.kwargs["results"],
            tuple(no_bet_result(item.race_id, self.identity.strategy_id) for item in inputs),
        )

    def test_run_passes_the_exact_executor_result_objects_to_summary_builder(self) -> None:
        inputs = (race_input(1), race_input(2))
        returned = tuple(no_bet_result(item.race_id, self.identity.strategy_id) for item in inputs)

        def fixed_executor(*, race_input: SimulationRaceInput) -> SimulationResult:
            return returned[race_input.race_id - 1]

        simulator = Simulator(strategy_identity=self.identity, race_executor=fixed_executor)
        expected = empty_summary(self.identity)
        with patch.object(simulator_module, "_build_simulation_summary", return_value=expected) as builder:
            simulator.run(race_inputs=inputs)
        results = builder.call_args.kwargs["results"]
        self.assertIs(results[0], returned[0])
        self.assertIs(results[1], returned[1])

    def test_run_calls_summary_builder_exactly_once(self) -> None:
        expected = empty_summary(self.identity)
        with patch.object(simulator_module, "_build_simulation_summary", return_value=expected) as builder:
            self.simulator.run(race_inputs=(race_input(1), race_input(2)))
        builder.assert_called_once()

    def test_run_calls_summary_builder_after_all_executors(self) -> None:
        events: list[str] = []

        def ordered_executor(*, race_input: SimulationRaceInput) -> SimulationResult:
            events.append(f"executor:{race_input.race_id}")
            return no_bet_result(race_input.race_id, self.identity.strategy_id)

        simulator = Simulator(strategy_identity=self.identity, race_executor=ordered_executor)
        expected = empty_summary(self.identity)
        with patch.object(
            simulator_module,
            "_build_simulation_summary",
            side_effect=lambda **kwargs: events.append("summary") or expected,
        ):
            simulator.run(race_inputs=(race_input(2), race_input(1)))
        self.assertEqual(events, ["executor:2", "executor:1", "summary"])

    def test_run_returns_the_exact_summary_builder_object(self) -> None:
        expected = empty_summary(self.identity)
        with patch.object(simulator_module, "_build_simulation_summary", return_value=expected):
            actual = self.simulator.run(race_inputs=(race_input(1),))
        self.assertIs(actual, expected)

    def test_run_passes_identity_to_summary_builder(self) -> None:
        expected = empty_summary(self.identity)
        with patch.object(simulator_module, "_build_simulation_summary", return_value=expected) as builder:
            self.simulator.run(race_inputs=())
        self.assertEqual(builder.call_args.kwargs["strategy_id"], self.identity.strategy_id)
        self.assertEqual(builder.call_args.kwargs["strategy_name"], self.identity.strategy_name)
        self.assertEqual(builder.call_args.kwargs["strategy_config_hash"], self.identity.strategy_config_hash)

    def test_run_accepts_empty_input(self) -> None:
        value = self.simulator.run(race_inputs=())
        self.assertEqual(value.race_count, 0)

    def test_empty_run_does_not_call_executor(self) -> None:
        self.simulator.run(race_inputs=())
        self.assertEqual(self.calls, [])

    def test_empty_run_calls_summary_builder_with_empty_results(self) -> None:
        expected = empty_summary(self.identity)
        with patch.object(simulator_module, "_build_simulation_summary", return_value=expected) as builder:
            self.simulator.run(race_inputs=())
        self.assertEqual(builder.call_args.kwargs["results"], ())

    def test_empty_run_returns_empty_summary_contract(self) -> None:
        value = self.simulator.run(race_inputs=())
        self.assertEqual((value.race_count, value.bet_count, value.investment, value.payout, value.profit), (0, 0, 0, 0, 0))
        self.assertEqual((value.roi, value.race_hit_rate, value.maximum_drawdown, dict(value.by_bet_type)), (None, None, 0, {}))

    def test_run_rejects_non_sequence_before_executor(self) -> None:
        for value in (None, 1, {}, object()):
            with self.subTest(value=value), self.assertRaises(SimulationBetEvaluationError):
                self.simulator.run(race_inputs=value)  # type: ignore[arg-type]
        self.assertEqual(self.calls, [])

    def test_run_rejects_string_before_executor(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            self.simulator.run(race_inputs="input")  # type: ignore[arg-type]
        self.assertEqual(self.calls, [])

    def test_run_rejects_bytes_before_executor(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            self.simulator.run(race_inputs=b"input")  # type: ignore[arg-type]
        self.assertEqual(self.calls, [])

    def test_run_rejects_invalid_element_before_executor(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            self.simulator.run(race_inputs=(race_input(1), object()))  # type: ignore[arg-type]
        self.assertEqual(self.calls, [])

    def test_run_rejects_duplicate_race_before_executor(self) -> None:
        first = race_input(1)
        duplicate = race_input(1)
        with self.assertRaises(SimulationBetEvaluationError):
            self.simulator.run(race_inputs=(first, duplicate))
        self.assertEqual(self.calls, [])

    def test_run_does_not_mutate_input_list(self) -> None:
        inputs = [race_input(2), race_input(1)]
        before = tuple(inputs)
        self.simulator.run(race_inputs=inputs)
        self.assertEqual(tuple(inputs), before)

    def test_run_does_not_mutate_input_tuple(self) -> None:
        inputs = (race_input(2), race_input(1))
        self.simulator.run(race_inputs=inputs)
        self.assertEqual(inputs, (inputs[0], inputs[1]))

    def test_run_does_not_mutate_race_input(self) -> None:
        item = race_input(1)
        before = (
            item.race_id,
            item.target_race_date,
            item.scheduled_start_at,
            item.information_cutoff,
            item.pipeline_input,
            item.input_snapshot_audit,
        )
        self.simulator.run(race_inputs=(item,))
        self.assertEqual(
            (item.race_id, item.target_race_date, item.scheduled_start_at, item.information_cutoff, item.pipeline_input, item.input_snapshot_audit),
            before,
        )

    def test_run_propagates_executor_exception_identity(self) -> None:
        failure = SimulationBetEvaluationError("executor failure")

        def failing_executor(*, race_input: SimulationRaceInput) -> SimulationResult:
            raise failure

        simulator = Simulator(strategy_identity=self.identity, race_executor=failing_executor)
        with self.assertRaises(SimulationBetEvaluationError) as caught:
            simulator.run(race_inputs=(race_input(1),))
        self.assertIs(caught.exception, failure)

    def test_executor_failure_stops_later_races(self) -> None:
        calls: list[int] = []
        failure = SimulationBetEvaluationError("executor failure")

        def failing_executor(*, race_input: SimulationRaceInput) -> SimulationResult:
            calls.append(race_input.race_id)
            if race_input.race_id == 2:
                raise failure
            return no_bet_result(race_input.race_id, self.identity.strategy_id)

        simulator = Simulator(strategy_identity=self.identity, race_executor=failing_executor)
        with self.assertRaises(SimulationBetEvaluationError):
            simulator.run(race_inputs=(race_input(1), race_input(2), race_input(3)))
        self.assertEqual(calls, [1, 2])

    def test_executor_failure_does_not_call_summary_builder(self) -> None:
        failure = SimulationBetEvaluationError("executor failure")

        def failing_executor(*, race_input: SimulationRaceInput) -> SimulationResult:
            raise failure

        simulator = Simulator(strategy_identity=self.identity, race_executor=failing_executor)
        with patch.object(simulator_module, "_build_simulation_summary", side_effect=AssertionError("must not build")):
            with self.assertRaises(SimulationBetEvaluationError):
                simulator.run(race_inputs=(race_input(1),))

    def test_summary_builder_exception_is_propagated(self) -> None:
        failure = SimulationBetEvaluationError("summary failure")
        with patch.object(simulator_module, "_build_simulation_summary", side_effect=failure):
            with self.assertRaises(SimulationBetEvaluationError) as caught:
                self.simulator.run(race_inputs=(race_input(1),))
        self.assertIs(caught.exception, failure)

    def test_run_rejects_positional_race_inputs(self) -> None:
        with self.assertRaises(TypeError):
            self.simulator.run(())  # type: ignore[call-arg]

    def test_run_preserves_race_count_contract(self) -> None:
        value = self.simulator.run(race_inputs=(race_input(1), race_input(2)))
        self.assertEqual(value.race_count, 2)

    def test_run_does_not_add_target_race_count(self) -> None:
        self.assertFalse(hasattr(self.simulator.run(race_inputs=()), "target_race_count"))

    def test_run_source_delegates_only_to_executor_and_summary_builder(self) -> None:
        tree = ast.parse(textwrap.dedent(inspect.getsource(Simulator.run)))
        calls = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        forbidden = {
            "_build_simulation_result_for_race",
            "_build_settled_simulation_result",
            "_build_non_settled_simulation_result",
            "_build_no_bet_simulation_result",
            "_evaluate_simulation_race_bets",
            "_evaluate_simulation_bet",
            "_decide_non_settled_status",
        }
        self.assertIn("_build_simulation_summary", calls)
        self.assertFalse(calls & forbidden)

    def test_run_source_has_no_external_io_or_current_time(self) -> None:
        source = inspect.getsource(Simulator.run)
        for forbidden in ("datetime.now", "datetime.utcnow", "logging", "print(", "open(", "requests", "sqlite"):
            self.assertNotIn(forbidden, source)

    def test_run_source_does_not_sort_or_filter_statuses(self) -> None:
        source = inspect.getsource(Simulator.run)
        self.assertNotIn("sorted(", source)
        self.assertNotIn("settlement_status", source)

    def test_run_has_no_broad_exception_handler(self) -> None:
        tree = ast.parse(textwrap.dedent(inspect.getsource(Simulator.run)))
        self.assertFalse(any(isinstance(node, ast.ExceptHandler) for node in ast.walk(tree)))

    def test_run_returns_only_summary_not_results_pair(self) -> None:
        value = self.simulator.run(race_inputs=(race_input(1),))
        self.assertIsInstance(value, SimulationSummary)
        self.assertNotIsInstance(value, tuple)

    def test_models_remain_unchanged_for_run_contract(self) -> None:
        self.assertEqual(SimulationRaceInput.__module__, "scripts.simulation.models")
        self.assertEqual(SimulationSummary.__module__, "scripts.simulation.models")


if __name__ == "__main__":
    unittest.main()
