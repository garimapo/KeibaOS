"""Constructor-only contract for the future multi-race Simulator."""
from __future__ import annotations

import ast
import inspect
import textwrap
from typing import Protocol, get_type_hints
import unittest

from scripts.prediction.bet_strategy import StrategyConfig
from scripts.simulation.models import (
    SimulationRaceInput,
    SimulationResult,
    StrategyIdentity,
    build_strategy_identity,
)
from scripts.simulation.simulator import (
    RaceSimulationExecutor,
    SimulationBetEvaluationError,
    Simulator,
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

    def test_constructor_does_not_define_run_yet(self) -> None:
        self.assertFalse(hasattr(Simulator, "run"))

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


if __name__ == "__main__":
    unittest.main()
