"""Contract tests for the race-entry selection resolver Protocol."""

from __future__ import annotations

import ast
import inspect
from typing import Protocol, Sequence, get_type_hints
import unittest

from scripts.simulation.selection_resolver import RaceEntrySelectionResolver


class StubResolver:
    """Test-only structural implementation; not a production ID mapping."""

    def resolve_race_entry_ids(
        self,
        *,
        race_id: int,
        horse_ids: Sequence[int],
    ) -> tuple[int, ...]:
        return tuple(horse_ids)


class RaceEntrySelectionResolverProtocolTests(unittest.TestCase):
    def test_is_structural_protocol_without_runtime_checkable(self) -> None:
        self.assertTrue(RaceEntrySelectionResolver._is_protocol)
        self.assertFalse(RaceEntrySelectionResolver._is_runtime_protocol)
        self.assertIsNot(RaceEntrySelectionResolver, Protocol)

    def test_has_only_the_resolve_public_method(self) -> None:
        methods = {
            name
            for name, value in inspect.getmembers(RaceEntrySelectionResolver, inspect.isfunction)
            if not name.startswith("_")
        }
        self.assertEqual(methods, {"resolve_race_entry_ids"})

    def test_method_signature_has_exact_parameter_order(self) -> None:
        signature = inspect.signature(RaceEntrySelectionResolver.resolve_race_entry_ids)
        self.assertEqual(tuple(signature.parameters), ("self", "race_id", "horse_ids"))

    def test_method_parameters_are_keyword_only_without_defaults(self) -> None:
        signature = inspect.signature(RaceEntrySelectionResolver.resolve_race_entry_ids)
        parameters = tuple(signature.parameters.values())[1:]
        self.assertTrue(all(item.kind is inspect.Parameter.KEYWORD_ONLY for item in parameters))
        self.assertTrue(all(item.default is inspect.Parameter.empty for item in parameters))

    def test_method_has_no_varargs_or_extra_arguments(self) -> None:
        signature = inspect.signature(RaceEntrySelectionResolver.resolve_race_entry_ids)
        parameter_kinds = tuple(item.kind for item in signature.parameters.values())
        self.assertNotIn(inspect.Parameter.VAR_POSITIONAL, parameter_kinds)
        self.assertNotIn(inspect.Parameter.VAR_KEYWORD, parameter_kinds)

    def test_method_type_hints_match_contract(self) -> None:
        hints = get_type_hints(RaceEntrySelectionResolver.resolve_race_entry_ids)
        self.assertIs(hints["race_id"], int)
        self.assertEqual(hints["horse_ids"], Sequence[int])
        self.assertEqual(hints["return"], tuple[int, ...])

    def test_protocol_method_has_ellipsis_body_without_default_implementation(self) -> None:
        tree = ast.parse(inspect.getsource(RaceEntrySelectionResolver))
        method = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
        self.assertEqual(len(method.body), 2)
        self.assertIsInstance(method.body[-1], ast.Expr)
        self.assertIsInstance(method.body[-1].value, ast.Constant)
        self.assertIs(method.body[-1].value.value, Ellipsis)

    def test_test_only_stub_matches_signature_structurally(self) -> None:
        protocol_signature = inspect.signature(RaceEntrySelectionResolver.resolve_race_entry_ids)
        stub_signature = inspect.signature(StubResolver.resolve_race_entry_ids)
        self.assertEqual(tuple(protocol_signature.parameters), tuple(stub_signature.parameters))
        self.assertEqual(get_type_hints(StubResolver.resolve_race_entry_ids), get_type_hints(RaceEntrySelectionResolver.resolve_race_entry_ids))

    def test_stub_preserves_test_input_order_without_claiming_production_mapping(self) -> None:
        result = StubResolver().resolve_race_entry_ids(race_id=101, horse_ids=(3, 1, 2))
        self.assertEqual(result, (3, 1, 2))

    def test_module_has_no_concrete_resolver_or_external_dependencies(self) -> None:
        import scripts.simulation.selection_resolver as module

        tree = ast.parse(inspect.getsource(module))
        class_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
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
        self.assertEqual(class_names, {"RaceEntrySelectionResolver"})
        self.assertFalse(any(name.startswith(("sqlite3", "requests", "scripts.simulation.repositories")) for name in imports))
        self.assertFalse(any(name.startswith("scripts.prediction") for name in imports))

    def test_simulation_package_does_not_export_resolver_early(self) -> None:
        import scripts.simulation as package

        self.assertFalse(hasattr(package, "RaceEntrySelectionResolver"))

    def test_target_race_count_is_not_added_to_protocol_module(self) -> None:
        import scripts.simulation.selection_resolver as module

        self.assertNotIn("target_race_count", inspect.getsource(module))


if __name__ == "__main__":
    unittest.main()
