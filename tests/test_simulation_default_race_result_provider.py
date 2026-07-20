"""Tests for the stateless concrete Result Provider facade."""

import ast
from contextlib import redirect_stderr, redirect_stdout
from datetime import UTC, datetime
from io import StringIO
import inspect
from pathlib import Path
from typing import get_args, get_origin, get_type_hints
from unittest.mock import patch
import unittest

from scripts.simulation.providers.errors import ProviderValidationError
from scripts.simulation.providers.interfaces import ProviderBuildResult, RaceResultProvider
from scripts.simulation.providers.models import (
    CompletenessResult,
    ProviderContext,
    RaceEntryUniverse,
    RawRaceResult,
    RawRaceResultEntry,
)
from scripts.simulation.providers import result_provider
from scripts.simulation.providers.result_provider import DefaultRaceResultProvider
from scripts.simulation.repositories.interfaces import PersistedRaceResult


NOW = datetime(2026, 1, 2, 12, 0, tzinfo=UTC)


class DefaultRaceResultProviderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = DefaultRaceResultProvider()
        self.context = ProviderContext(10, NOW, "fixture", None, NOW, NOW)
        self.universe = RaceEntryUniverse(10, {11}, set(), set(), {1: 11})
        self.raw = RawRaceResult("complete", NOW, (RawRaceResultEntry(1, 11, 1, "confirmed"),))

    def test_default_provider_can_be_constructed(self) -> None:
        self.assertIsInstance(self.provider, DefaultRaceResultProvider)

    def test_default_provider_is_stateless(self) -> None:
        self.assertFalse(hasattr(self.provider, "__dict__"))

    def test_default_provider_uses_empty_slots(self) -> None:
        self.assertEqual(DefaultRaceResultProvider.__slots__, ())

    def test_default_provider_is_not_protocol(self) -> None:
        self.assertFalse(getattr(DefaultRaceResultProvider, "_is_protocol", False))

    def test_default_provider_is_not_runtime_protocol(self) -> None:
        self.assertFalse(getattr(DefaultRaceResultProvider, "_is_runtime_protocol", False))

    def test_build_race_result_signature_matches_protocol(self) -> None:
        concrete = list(inspect.signature(DefaultRaceResultProvider.build_race_result).parameters)
        protocol = list(inspect.signature(RaceResultProvider.build_race_result).parameters)
        self.assertEqual(concrete, protocol)

    def test_build_race_result_type_hints_match_protocol(self) -> None:
        self.assertEqual(
            get_type_hints(DefaultRaceResultProvider.build_race_result),
            get_type_hints(RaceResultProvider.build_race_result),
        )

    def test_build_race_result_returns_provider_build_result(self) -> None:
        self.assertIsInstance(self.provider.build_race_result(self.raw, self.context, self.universe), ProviderBuildResult)

    def test_build_race_result_value_is_persisted_race_result(self) -> None:
        output = self.provider.build_race_result(self.raw, self.context, self.universe)
        self.assertIsInstance(output.value, PersistedRaceResult)

    def test_build_race_result_completeness_is_completeness_result(self) -> None:
        output = self.provider.build_race_result(self.raw, self.context, self.universe)
        self.assertIsInstance(output.completeness, CompletenessResult)

    def test_build_race_result_return_annotation_is_repository_boundary_model(self) -> None:
        annotation = get_type_hints(DefaultRaceResultProvider.build_race_result)["return"]
        self.assertIs(get_origin(annotation), ProviderBuildResult)
        self.assertEqual(get_args(annotation), (PersistedRaceResult,))

    def test_build_race_result_returns_internal_helper_object_unchanged(self) -> None:
        expected = result_provider._build_race_result_provider_output(self.raw, self.context, self.universe)
        with patch.object(result_provider, "_build_race_result_provider_output", return_value=expected):
            actual = self.provider.build_race_result(self.raw, self.context, self.universe)
        self.assertIs(actual, expected)

    def test_delegates_to_internal_helper_once(self) -> None:
        with patch.object(
            result_provider,
            "_build_race_result_provider_output",
            wraps=result_provider._build_race_result_provider_output,
        ) as helper:
            self.provider.build_race_result(self.raw, self.context, self.universe)
        helper.assert_called_once()

    def test_delegates_with_same_raw_context_and_universe_objects(self) -> None:
        with patch.object(
            result_provider,
            "_build_race_result_provider_output",
            wraps=result_provider._build_race_result_provider_output,
        ) as helper:
            self.provider.build_race_result(self.raw, self.context, self.universe)
        self.assertEqual(helper.call_args.args, (self.raw, self.context, self.universe))
        self.assertIs(helper.call_args.args[0], self.raw)
        self.assertIs(helper.call_args.args[1], self.context)
        self.assertIs(helper.call_args.args[2], self.universe)

    def test_propagates_provider_validation_error(self) -> None:
        error = ProviderValidationError("invalid")
        with patch.object(result_provider, "_build_race_result_provider_output", side_effect=error):
            with self.assertRaises(ProviderValidationError) as caught:
                self.provider.build_race_result(self.raw, self.context, self.universe)
        self.assertIs(caught.exception, error)

    def test_does_not_return_partial_output_on_error(self) -> None:
        with patch.object(result_provider, "_build_race_result_provider_output", side_effect=ProviderValidationError("invalid")):
            with self.assertRaises(ProviderValidationError):
                self.provider.build_race_result(self.raw, self.context, self.universe)

    def test_rejects_invalid_raw_through_internal_pipeline(self) -> None:
        with self.assertRaises(ProviderValidationError):
            self.provider.build_race_result(None, self.context, self.universe)

    def test_rejects_invalid_context_through_internal_pipeline(self) -> None:
        with self.assertRaises(ProviderValidationError):
            self.provider.build_race_result(self.raw, None, self.universe)

    def test_rejects_invalid_universe_through_internal_pipeline(self) -> None:
        with self.assertRaises(ProviderValidationError):
            self.provider.build_race_result(self.raw, self.context, None)

    def test_does_not_mutate_raw(self) -> None:
        before = self.raw
        self.provider.build_race_result(self.raw, self.context, self.universe)
        self.assertEqual(self.raw, before)

    def test_does_not_mutate_context(self) -> None:
        before = self.context
        self.provider.build_race_result(self.raw, self.context, self.universe)
        self.assertEqual(self.context, before)

    def test_does_not_mutate_universe(self) -> None:
        before = self.universe
        self.provider.build_race_result(self.raw, self.context, self.universe)
        self.assertEqual(self.universe, before)

    def test_exposes_no_persistence_methods(self) -> None:
        forbidden = {"save", "persist", "insert", "update", "delete", "commit", "rollback", "connect", "close", "execute", "cursor"}
        methods = {name for name, value in inspect.getmembers(DefaultRaceResultProvider, inspect.isfunction)}
        self.assertFalse(methods & forbidden)

    def test_does_not_write_stdout_or_stderr(self) -> None:
        stdout, stderr = StringIO(), StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            self.provider.build_race_result(self.raw, self.context, self.universe)
        self.assertEqual((stdout.getvalue(), stderr.getvalue()), ("", ""))

    def test_has_no_database_repository_or_network_dependency(self) -> None:
        tree = ast.parse((Path(__file__).parents[1] / "scripts/simulation/providers/result_provider.py").read_text(encoding="utf-8"))
        imports = {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
        forbidden = ("sqlite3", "requests", "httpx", "urllib", "selenium", "playwright", "scripts.simulation.repositories.sqlite")
        self.assertFalse(any(name.startswith(forbidden) for name in imports))

    def test_concrete_provider_is_importable_from_result_provider_module(self) -> None:
        self.assertIs(result_provider.DefaultRaceResultProvider, DefaultRaceResultProvider)

    def test_concrete_provider_is_exported_from_package_root(self) -> None:
        import scripts.simulation.providers as providers
        self.assertIs(providers.DefaultRaceResultProvider, DefaultRaceResultProvider)

    def test_build_method_contains_only_thin_delegation(self) -> None:
        tree = ast.parse((Path(__file__).parents[1] / "scripts/simulation/providers/result_provider.py").read_text(encoding="utf-8"))
        node = next(item for item in ast.walk(tree) if isinstance(item, ast.ClassDef) and item.name == "DefaultRaceResultProvider")
        method = next(item for item in node.body if isinstance(item, ast.FunctionDef) and item.name == "build_race_result")
        executable = [item for item in method.body if not (isinstance(item, ast.Expr) and isinstance(item.value, ast.Constant) and isinstance(item.value.value, str))]
        self.assertEqual(len(executable), 1)
        self.assertIsInstance(executable[0], ast.Return)
        self.assertIsInstance(executable[0].value, ast.Call)
        self.assertEqual(executable[0].value.func.id, "_build_race_result_provider_output")

    def test_instance_rejects_dynamic_attribute_assignment(self) -> None:
        with self.assertRaises(AttributeError):
            self.provider.cache = object()
