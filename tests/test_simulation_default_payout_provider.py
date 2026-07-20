"""Tests for the stateless concrete Payout Provider facade."""

import ast
from contextlib import redirect_stderr, redirect_stdout
from datetime import UTC, datetime
from io import StringIO
import inspect
from pathlib import Path
from typing import get_args, get_origin, get_type_hints
from unittest.mock import patch
import unittest

import scripts.simulation.providers as providers
from scripts.simulation.providers.errors import ProviderValidationError
from scripts.simulation.providers.interfaces import PayoutProvider, ProviderBuildResult
from scripts.simulation.providers.models import CompletenessResult, ProviderContext, RaceEntryUniverse, RawPayoutPublication, RawPayoutRecord
from scripts.simulation.providers import payout_provider
from scripts.simulation.providers.payout_provider import DefaultPayoutProvider
from scripts.simulation.repositories.interfaces import PayoutPublication


NOW = datetime(2026, 1, 2, 12, 0, tzinfo=UTC)


class DefaultPayoutProviderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = DefaultPayoutProvider()
        self.context = ProviderContext(10, NOW, "fixture", None, NOW, NOW)
        self.universe = RaceEntryUniverse(10, {11}, set(), set(), {1: 11})
        self.raw = RawPayoutPublication("単勝", NOW, (RawPayoutRecord((11,), None, "100", "winning"),), True, True, True)

    def test_default_provider_can_be_constructed(self) -> None:
        self.assertIsInstance(self.provider, DefaultPayoutProvider)

    def test_default_provider_is_stateless(self) -> None:
        self.assertFalse(hasattr(self.provider, "__dict__"))

    def test_default_provider_uses_empty_slots(self) -> None:
        self.assertEqual(DefaultPayoutProvider.__slots__, ())

    def test_default_provider_rejects_dynamic_attribute_assignment(self) -> None:
        with self.assertRaises(AttributeError):
            self.provider.cache = object()

    def test_default_provider_is_not_protocol_or_runtime_protocol(self) -> None:
        self.assertFalse(getattr(DefaultPayoutProvider, "_is_protocol", False))
        self.assertFalse(getattr(DefaultPayoutProvider, "_is_runtime_protocol", False))

    def test_build_method_signature_matches_protocol(self) -> None:
        self.assertEqual(list(inspect.signature(DefaultPayoutProvider.build_payout_publication).parameters), list(inspect.signature(PayoutProvider.build_payout_publication).parameters))

    def test_build_method_type_hints_match_protocol(self) -> None:
        self.assertEqual(get_type_hints(DefaultPayoutProvider.build_payout_publication), get_type_hints(PayoutProvider.build_payout_publication))

    def test_return_annotation_uses_payout_publication(self) -> None:
        annotation = get_type_hints(DefaultPayoutProvider.build_payout_publication)["return"]
        self.assertIs(get_origin(annotation), ProviderBuildResult)
        self.assertEqual(get_args(annotation), (PayoutPublication,))

    def test_build_method_returns_provider_build_result(self) -> None:
        self.assertIsInstance(self.provider.build_payout_publication(self.raw, self.context, self.universe), ProviderBuildResult)

    def test_build_method_value_and_completeness_types(self) -> None:
        result = self.provider.build_payout_publication(self.raw, self.context, self.universe)
        self.assertIsInstance(result.value, PayoutPublication)
        self.assertIsInstance(result.completeness, CompletenessResult)

    def test_returns_internal_helper_object_unchanged(self) -> None:
        expected = payout_provider._build_payout_provider_output(self.raw, self.context, self.universe)
        with patch.object(payout_provider, "_build_payout_provider_output", return_value=expected):
            actual = self.provider.build_payout_publication(self.raw, self.context, self.universe)
        self.assertIs(actual, expected)

    def test_delegates_to_internal_helper_once(self) -> None:
        with patch.object(payout_provider, "_build_payout_provider_output", wraps=payout_provider._build_payout_provider_output) as helper:
            self.provider.build_payout_publication(self.raw, self.context, self.universe)
        helper.assert_called_once_with(self.raw, self.context, self.universe)

    def test_propagates_same_provider_validation_error(self) -> None:
        error = ProviderValidationError("invalid")
        with patch.object(payout_provider, "_build_payout_provider_output", side_effect=error):
            with self.assertRaises(ProviderValidationError) as caught:
                self.provider.build_payout_publication(self.raw, self.context, self.universe)
        self.assertIs(caught.exception, error)

    def test_does_not_return_partial_output_on_error(self) -> None:
        with patch.object(payout_provider, "_build_payout_provider_output", side_effect=ProviderValidationError("invalid")):
            with self.assertRaises(ProviderValidationError):
                self.provider.build_payout_publication(self.raw, self.context, self.universe)

    def test_rejects_invalid_raw_context_and_universe_through_pipeline(self) -> None:
        for raw, context, universe in ((None, self.context, self.universe), (self.raw, None, self.universe), (self.raw, self.context, None)):
            with self.subTest(raw=raw is None, context=context is None, universe=universe is None), self.assertRaises(ProviderValidationError):
                self.provider.build_payout_publication(raw, context, universe)

    def test_does_not_mutate_inputs(self) -> None:
        raw, context, universe = self.raw, self.context, self.universe
        self.provider.build_payout_publication(raw, context, universe)
        self.assertEqual((raw, context, universe), (self.raw, self.context, self.universe))

    def test_exposes_no_persistence_or_cache_members(self) -> None:
        forbidden = {"save", "persist", "insert", "update", "delete", "commit", "rollback", "connect", "close", "execute", "cursor", "cache", "repository", "connection", "database", "session"}
        methods = {name for name, value in inspect.getmembers(DefaultPayoutProvider, inspect.isfunction)}
        self.assertFalse(methods & forbidden)

    def test_does_not_write_stdout_or_stderr(self) -> None:
        stdout, stderr = StringIO(), StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            self.provider.build_payout_publication(self.raw, self.context, self.universe)
        self.assertEqual((stdout.getvalue(), stderr.getvalue()), ("", ""))

    def test_has_no_database_repository_save_or_network_dependency(self) -> None:
        tree = ast.parse((Path(__file__).parents[1] / "scripts/simulation/providers/payout_provider.py").read_text(encoding="utf-8"))
        imports = {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
        forbidden = ("sqlite3", "requests", "httpx", "urllib", "selenium", "playwright", "scripts.simulation.repositories.sqlite")
        self.assertFalse(any(name.startswith(forbidden) for name in imports))

    def test_concrete_provider_is_importable_from_payout_provider_module(self) -> None:
        self.assertIs(payout_provider.DefaultPayoutProvider, DefaultPayoutProvider)

    def test_concrete_provider_is_exported_from_package_root(self) -> None:
        self.assertIs(providers.DefaultPayoutProvider, DefaultPayoutProvider)

    def test_build_method_contains_only_thin_delegation(self) -> None:
        tree = ast.parse((Path(__file__).parents[1] / "scripts/simulation/providers/payout_provider.py").read_text(encoding="utf-8"))
        node = next(item for item in ast.walk(tree) if isinstance(item, ast.ClassDef) and item.name == "DefaultPayoutProvider")
        method = next(item for item in node.body if isinstance(item, ast.FunctionDef) and item.name == "build_payout_publication")
        executable = [item for item in method.body if not (isinstance(item, ast.Expr) and isinstance(item.value, ast.Constant) and isinstance(item.value.value, str))]
        self.assertEqual(len(executable), 1)
        self.assertIsInstance(executable[0], ast.Return)
        self.assertEqual(executable[0].value.func.id, "_build_payout_provider_output")

    def test_build_method_does_not_reanalyze_or_rebuild(self) -> None:
        names = DefaultPayoutProvider.build_payout_publication.__code__.co_names
        self.assertNotIn("_analyze_payout_publication_status_facts", names)
        self.assertNotIn("CompletenessResult", names)
        self.assertNotIn("expected_selections", names)

    def test_build_method_does_not_calculate_simulation_return(self) -> None:
        self.assertNotIn("return_rate", DefaultPayoutProvider.build_payout_publication.__code__.co_names)
