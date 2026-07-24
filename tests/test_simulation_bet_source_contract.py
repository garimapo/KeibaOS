"""Contract tests for the simulation purchase-plan source protocol."""

from __future__ import annotations

import ast
import contextlib
import importlib
import inspect
import io
from pathlib import Path
import textwrap
from types import ModuleType
from typing import get_args, get_origin, get_type_hints
import unittest

import scripts.simulation as simulation_package
from scripts.simulation.bet_source import SimulationBetSource
import scripts.simulation.bet_source as bet_source_module
from scripts.simulation.models import SimulationBet, SimulationRaceInput, StrategyIdentity


MODULE = "scripts.simulation.bet_source"


class SimulationBetSourceProtocolTests(unittest.TestCase):
    def test_is_protocol(self) -> None:
        self.assertTrue(SimulationBetSource._is_protocol)

    def test_is_not_runtime_checkable(self) -> None:
        self.assertFalse(SimulationBetSource._is_runtime_protocol)

    def test_has_only_load_bets_method(self) -> None:
        methods = [
            name
            for name, value in SimulationBetSource.__dict__.items()
            if inspect.isfunction(value) and name != "__init__"
        ]
        self.assertEqual(methods, ["load_bets"])

    def test_load_bets_signature_has_exact_parameters(self) -> None:
        signature = inspect.signature(SimulationBetSource.load_bets)
        self.assertEqual(tuple(signature.parameters), ("self", "race_input", "strategy_identity"))

    def test_load_bets_parameters_are_keyword_only(self) -> None:
        signature = inspect.signature(SimulationBetSource.load_bets)
        self.assertIs(signature.parameters["race_input"].kind, inspect.Parameter.KEYWORD_ONLY)
        self.assertIs(signature.parameters["strategy_identity"].kind, inspect.Parameter.KEYWORD_ONLY)

    def test_load_bets_has_no_extra_parameters(self) -> None:
        signature = inspect.signature(SimulationBetSource.load_bets)
        kinds = {parameter.kind for parameter in signature.parameters.values()}
        self.assertNotIn(inspect.Parameter.VAR_POSITIONAL, kinds)
        self.assertNotIn(inspect.Parameter.VAR_KEYWORD, kinds)

    def test_load_bets_type_hints_use_simulation_boundary_models(self) -> None:
        hints = get_type_hints(SimulationBetSource.load_bets)
        self.assertIs(hints["race_input"], SimulationRaceInput)
        self.assertIs(hints["strategy_identity"], StrategyIdentity)

    def test_load_bets_return_hint_is_tuple_of_simulation_bets(self) -> None:
        return_hint = get_type_hints(SimulationBetSource.load_bets)["return"]
        self.assertIs(get_origin(return_hint), tuple)
        self.assertEqual(get_args(return_hint), (SimulationBet, Ellipsis))

    def test_protocol_method_is_declaration_only(self) -> None:
        tree = ast.parse(textwrap.dedent(inspect.getsource(SimulationBetSource.load_bets)))
        expression = tree.body[0].body[0]
        self.assertIsInstance(expression, ast.Expr)
        self.assertIsInstance(expression.value, ast.Constant)
        self.assertIs(expression.value.value, Ellipsis)

    def test_protocol_is_not_a_concrete_source(self) -> None:
        tree = ast.parse(inspect.getsource(bet_source_module))
        classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
        self.assertEqual([node.name for node in classes], ["SimulationBetSource"])
        self.assertTrue(any(base.id == "Protocol" for base in classes[0].bases if isinstance(base, ast.Name)))

    def test_module_imports_without_error(self) -> None:
        module = importlib.import_module(MODULE)
        self.assertIsInstance(module, ModuleType)

    def test_module_import_has_no_stdout_or_stderr(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            module = importlib.import_module(MODULE)
        self.assertIsInstance(module, ModuleType)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")

    def test_import_order_with_models_succeeds(self) -> None:
        models_module = importlib.import_module("scripts.simulation.models")
        source_module = importlib.import_module(MODULE)
        self.assertIsInstance(models_module, ModuleType)
        self.assertIsInstance(source_module, ModuleType)

    def test_reverse_import_order_with_models_succeeds(self) -> None:
        source_module = importlib.import_module(MODULE)
        models_module = importlib.import_module("scripts.simulation.models")
        self.assertIsInstance(source_module, ModuleType)
        self.assertIsInstance(models_module, ModuleType)

    def test_module_has_no_provider_dependencies(self) -> None:
        source = inspect.getsource(bet_source_module)
        for forbidden in ("providers", "result_provider", "payout_provider", "odds_provider"):
            self.assertNotIn(forbidden, source)

    def test_module_has_no_repository_or_database_dependencies(self) -> None:
        path = Path(__file__).parents[1] / "scripts/simulation/bet_source.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        } | {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        forbidden_prefixes = (
            "sqlite3",
            "scripts.simulation.repositories",
            "scripts.migrations",
        )
        self.assertFalse(any(name.startswith(forbidden_prefixes) for name in imports))

    def test_module_has_no_external_io_dependencies(self) -> None:
        source = inspect.getsource(bet_source_module)
        for forbidden in ("requests", "httpx", "urllib", "socket", "subprocess", "logging"):
            self.assertNotIn(forbidden, source)

    def test_module_has_no_raw_or_persisted_settlement_dependencies(self) -> None:
        source = inspect.getsource(bet_source_module)
        for forbidden in (
            "RaceSettlementData",
            "RaceSettlementSource",
            "PersistedRaceSettlementData",
            "PersistedRaceSettlementSource",
        ):
            self.assertNotIn(forbidden, source)

    def test_module_has_no_executor_or_builder_dependencies(self) -> None:
        source = inspect.getsource(bet_source_module)
        for forbidden in (
            "ProviderBackedRaceSimulationExecutor",
            "PersistedRaceSimulationExecutor",
            "_build_simulation_result_for_race",
            "_build_simulation_summary",
            "Simulator",
        ):
            self.assertNotIn(forbidden, source)

    def test_module_has_no_prediction_cutoff_logic(self) -> None:
        source = inspect.getsource(bet_source_module)
        self.assertNotIn("information_cutoff", source)
        self.assertNotIn("datetime.now", source)

    def test_module_has_no_validation_or_exception_wrapping_logic(self) -> None:
        tree = ast.parse(inspect.getsource(bet_source_module))
        self.assertFalse(any(isinstance(node, ast.Raise) for node in ast.walk(tree)))
        self.assertFalse(any(isinstance(node, ast.Try) for node in ast.walk(tree)))

    def test_module_does_not_construct_or_normalize_bets(self) -> None:
        source = inspect.getsource(bet_source_module)
        for forbidden in ("SimulationBet(", "tuple(", "normalize_selection", "validate_bet_type"):
            self.assertNotIn(forbidden, source)

    def test_protocol_is_not_exported_from_package_root(self) -> None:
        self.assertFalse(hasattr(simulation_package, "SimulationBetSource"))

    def test_models_remain_outside_bet_source_module(self) -> None:
        self.assertEqual(SimulationBet.__module__, "scripts.simulation.models")
        self.assertEqual(SimulationRaceInput.__module__, "scripts.simulation.models")
        self.assertFalse(hasattr(SimulationBetSource, "target_race_count"))


if __name__ == "__main__":
    unittest.main()
