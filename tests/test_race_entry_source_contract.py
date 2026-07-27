"""Contract tests for the RaceEntrySource Protocol."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
import textwrap
from typing import Mapping, Protocol, Sequence, get_type_hints
import unittest

import scripts.simulation as simulation_package
import scripts.simulation.race_entry_source as source_module
from scripts.simulation.race_entry_source import RaceEntrySource


class StubRaceEntrySource:
    """Test-only structural implementation; not a production ID mapping."""

    def load_race_entry_id_map(
        self,
        *,
        race_id: int,
        horse_ids: Sequence[int],
    ) -> Mapping[int, int]:
        return {horse_id: horse_id for horse_id in horse_ids}


def assert_declaration_only(test_case: unittest.TestCase, method: object) -> None:
    tree = ast.parse(textwrap.dedent(inspect.getsource(method)))
    body = tree.body[0].body
    test_case.assertEqual(len(body), 1)
    test_case.assertIsInstance(body[0], ast.Expr)
    test_case.assertIsInstance(body[0].value, ast.Constant)
    test_case.assertIs(body[0].value.value, Ellipsis)


class RaceEntrySourceProtocolTests(unittest.TestCase):
    def test_is_structural_protocol_without_runtime_checkable(self) -> None:
        self.assertTrue(RaceEntrySource._is_protocol)
        self.assertFalse(RaceEntrySource._is_runtime_protocol)
        self.assertIsNot(RaceEntrySource, Protocol)

    def test_cannot_be_instantiated_as_a_concrete_class(self) -> None:
        with self.assertRaises(TypeError):
            RaceEntrySource()

    def test_has_only_the_load_race_entry_id_map_public_method(self) -> None:
        methods = {
            name
            for name, value in RaceEntrySource.__dict__.items()
            if inspect.isfunction(value) and not name.startswith("_")
        }
        self.assertEqual(methods, {"load_race_entry_id_map"})

    def test_method_signature_has_exact_parameter_order(self) -> None:
        signature = inspect.signature(RaceEntrySource.load_race_entry_id_map)
        self.assertEqual(tuple(signature.parameters), ("self", "race_id", "horse_ids"))

    def test_method_parameters_are_keyword_only_without_defaults(self) -> None:
        signature = inspect.signature(RaceEntrySource.load_race_entry_id_map)
        parameters = tuple(signature.parameters.values())[1:]
        self.assertTrue(all(item.kind is inspect.Parameter.KEYWORD_ONLY for item in parameters))
        self.assertTrue(all(item.default is inspect.Parameter.empty for item in parameters))

    def test_method_has_no_varargs_or_async_contract(self) -> None:
        signature = inspect.signature(RaceEntrySource.load_race_entry_id_map)
        kinds = {parameter.kind for parameter in signature.parameters.values()}
        self.assertNotIn(inspect.Parameter.VAR_POSITIONAL, kinds)
        self.assertNotIn(inspect.Parameter.VAR_KEYWORD, kinds)
        self.assertFalse(inspect.iscoroutinefunction(RaceEntrySource.load_race_entry_id_map))

    def test_method_type_hints_match_contract(self) -> None:
        hints = get_type_hints(RaceEntrySource.load_race_entry_id_map)
        self.assertIs(hints["race_id"], int)
        self.assertEqual(hints["horse_ids"], Sequence[int])
        self.assertEqual(hints["return"], Mapping[int, int])

    def test_method_is_a_declaration_only(self) -> None:
        assert_declaration_only(self, RaceEntrySource.load_race_entry_id_map)

    def test_test_only_stub_matches_signature_structurally(self) -> None:
        self.assertEqual(
            inspect.signature(StubRaceEntrySource.load_race_entry_id_map),
            inspect.signature(RaceEntrySource.load_race_entry_id_map),
        )
        self.assertEqual(
            get_type_hints(StubRaceEntrySource.load_race_entry_id_map),
            get_type_hints(RaceEntrySource.load_race_entry_id_map),
        )

    def test_test_only_stub_returns_a_mapping_for_requested_horse_ids(self) -> None:
        mapping = StubRaceEntrySource().load_race_entry_id_map(
            race_id=101,
            horse_ids=(3, 1, 2),
        )
        self.assertEqual(mapping, {3: 3, 1: 1, 2: 2})


class RaceEntrySourceProtocolModuleTests(unittest.TestCase):
    def test_module_uses_future_annotations_and_defines_only_the_protocol(self) -> None:
        tree = ast.parse(inspect.getsource(source_module))
        future_imports = [
            node
            for node in tree.body
            if isinstance(node, ast.ImportFrom) and node.module == "__future__"
        ]
        self.assertEqual(len(future_imports), 1)
        self.assertEqual([alias.name for alias in future_imports[0].names], ["annotations"])
        classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
        self.assertEqual([node.name for node in classes], ["RaceEntrySource"])

    def test_module_imports_only_typing_dependencies(self) -> None:
        path = Path(__file__).parents[1] / "scripts/simulation/race_entry_source.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported_modules = {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        } | {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        self.assertEqual(imported_modules, {"__future__", "typing"})

    def test_module_has_no_concrete_storage_validation_or_external_behavior(self) -> None:
        tree = ast.parse(inspect.getsource(source_module))
        self.assertFalse(any(isinstance(node, (ast.Assign, ast.AnnAssign, ast.Raise, ast.Try)) for node in ast.walk(tree)))
        self.assertFalse(any(isinstance(node, ast.Call) for node in ast.walk(tree)))

    def test_module_has_no_sql_repository_or_runtime_dependencies(self) -> None:
        source = inspect.getsource(source_module)
        for forbidden in (
            "sqlite3",
            "Repository",
            "RaceEntrySelectionResolver",
            "SimulationBetPlanBuilder",
            "Snapshot",
            "providers",
            "PredictionPipeline",
            "Simulator",
            "SimulationResult",
            "SimulationSummary",
            "requests",
            "httpx",
            "urllib",
            "socket",
            "datetime.now",
        ):
            self.assertNotIn(forbidden, source)

    def test_protocol_is_not_exported_from_simulation_package_root(self) -> None:
        self.assertFalse(hasattr(simulation_package, "RaceEntrySource"))

    def test_target_race_count_is_not_added_to_protocol_module(self) -> None:
        self.assertNotIn("target_race_count", inspect.getsource(source_module))


if __name__ == "__main__":
    unittest.main()
