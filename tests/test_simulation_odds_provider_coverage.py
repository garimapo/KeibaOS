"""Tests for immutable expected-versus-observed odds selection coverage."""

import ast
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
import unittest

import scripts.simulation.providers as providers
from scripts.simulation.providers.errors import ProviderValidationError
from scripts.simulation.providers.models import RaceEntryUniverse, expected_selections
from scripts.simulation.providers import odds_provider
from scripts.simulation.providers.odds_provider import _OddsSelectionCoverage, _analyze_odds_selection_coverage
from scripts.simulation.repositories.interfaces import OddsSnapshotBatch, OddsSnapshotEntry


NOW = datetime(2026, 1, 2, 12, 0, tzinfo=UTC)


class OddsProviderCoverageTest(unittest.TestCase):
    def setUp(self) -> None:
        self.universe = RaceEntryUniverse(10, {11, 12, 13}, {14}, {15}, {1: 11, 2: 12, 3: 13, 4: 14, 5: 15})

    def _batch(self, bet_type: str, selections, complete: bool = True) -> OddsSnapshotBatch:
        entries = tuple(OddsSnapshotEntry(selection, Decimal("1.20")) for selection in selections)
        return OddsSnapshotBatch(10, bet_type, NOW, complete, "fixture", entries)

    def test_complete_win_selection_coverage(self) -> None:
        coverage = _analyze_odds_selection_coverage(self._batch("単勝", ((11,), (12,), (13,))), self.universe)
        self.assertEqual(coverage.missing_selections, ())
        self.assertEqual(coverage.unexpected_selections, ())

    def test_complete_quinella_selection_coverage(self) -> None:
        selections = ((11, 12), (11, 13), (12, 13))
        coverage = _analyze_odds_selection_coverage(self._batch("馬連", selections), self.universe)
        self.assertEqual(coverage.expected_selections, selections)

    def test_complete_wide_selection_coverage(self) -> None:
        selections = ((11, 12), (11, 13), (12, 13))
        coverage = _analyze_odds_selection_coverage(self._batch("ワイド", selections), self.universe)
        self.assertEqual(coverage.observed_selections, selections)

    def test_complete_trio_selection_coverage(self) -> None:
        coverage = _analyze_odds_selection_coverage(self._batch("3連複", ((11, 12, 13),)), self.universe)
        self.assertEqual(coverage.expected_selections, ((11, 12, 13),))

    def test_expected_selections_use_active_entries_only(self) -> None:
        coverage = _analyze_odds_selection_coverage(self._batch("単勝", ((11,),)), self.universe)
        self.assertEqual(coverage.expected_selections, ((11,), (12,), (13,)))

    def test_excluded_entries_are_not_expected(self) -> None:
        coverage = _analyze_odds_selection_coverage(self._batch("単勝", ((11,),)), self.universe)
        self.assertNotIn((14,), coverage.expected_selections)

    def test_cancelled_entries_are_not_expected(self) -> None:
        coverage = _analyze_odds_selection_coverage(self._batch("単勝", ((11,),)), self.universe)
        self.assertNotIn((15,), coverage.expected_selections)

    def test_observed_selections_come_from_batch_entries(self) -> None:
        coverage = _analyze_odds_selection_coverage(self._batch("馬連", ((11, 13),)), self.universe)
        self.assertEqual(coverage.observed_selections, ((11, 13),))

    def test_detects_missing_selection(self) -> None:
        coverage = _analyze_odds_selection_coverage(self._batch("単勝", ((11,), (12,))), self.universe)
        self.assertEqual(coverage.missing_selections, ((13,),))

    def test_detects_multiple_missing_selections(self) -> None:
        coverage = _analyze_odds_selection_coverage(self._batch("馬連", ((11, 12),)), self.universe)
        self.assertEqual(coverage.missing_selections, ((11, 13), (12, 13)))

    def test_detects_unexpected_selection(self) -> None:
        coverage = _analyze_odds_selection_coverage(self._batch("単勝", ((11,), (14,))), self.universe)
        self.assertEqual(coverage.unexpected_selections, ((14,),))

    def test_detects_missing_and_unexpected_together(self) -> None:
        coverage = _analyze_odds_selection_coverage(self._batch("単勝", ((11,), (14,))), self.universe)
        self.assertEqual(coverage.missing_selections, ((12,), (13,)))
        self.assertEqual(coverage.unexpected_selections, ((14,),))

    def test_empty_universe_with_observation_is_unexpected(self) -> None:
        universe = RaceEntryUniverse(10, set(), set(), set(), {})
        coverage = _analyze_odds_selection_coverage(self._batch("単勝", ((11,),)), universe)
        self.assertEqual((coverage.expected_selections, coverage.unexpected_selections), ((), ((11,),)))

    def test_insufficient_active_entries_produce_no_expected_selections(self) -> None:
        universe = RaceEntryUniverse(10, {11}, set(), set(), {1: 11})
        coverage = _analyze_odds_selection_coverage(self._batch("馬連", ((11, 12),)), universe)
        self.assertEqual(coverage.expected_selections, ())

    def test_observed_with_no_expected_selections_are_unexpected(self) -> None:
        universe = RaceEntryUniverse(10, {11}, set(), set(), {1: 11})
        coverage = _analyze_odds_selection_coverage(self._batch("馬連", ((11, 12),)), universe)
        self.assertEqual(coverage.unexpected_selections, ((11, 12),))

    def test_declared_complete_does_not_change_coverage(self) -> None:
        complete = _analyze_odds_selection_coverage(self._batch("単勝", ((11,),), True), self.universe)
        incomplete = _analyze_odds_selection_coverage(self._batch("単勝", ((11,),), False), self.universe)
        self.assertEqual(complete, incomplete)

    def test_reuses_expected_selections_once(self) -> None:
        with patch.object(odds_provider, "expected_selections", wraps=expected_selections) as helper:
            _analyze_odds_selection_coverage(self._batch("単勝", ((11,),)), self.universe)
        helper.assert_called_once_with(self.universe.active_entries, "単勝")

    def test_does_not_use_horse_numbers_as_selection_identity(self) -> None:
        coverage = _analyze_odds_selection_coverage(self._batch("単勝", ((11,),)), self.universe)
        self.assertNotIn("horse", _analyze_odds_selection_coverage.__code__.co_names)
        self.assertEqual(coverage.observed_selections, ((11,),))

    def test_does_not_include_odds_in_selection_identity(self) -> None:
        first = _analyze_odds_selection_coverage(self._batch("単勝", ((11,),)), self.universe)
        alternate = OddsSnapshotBatch(10, "単勝", NOW, True, "fixture", (OddsSnapshotEntry((11,), Decimal("99.9")),))
        second = _analyze_odds_selection_coverage(alternate, self.universe)
        self.assertEqual(first, second)

    def test_outputs_are_nested_tuples(self) -> None:
        coverage = _analyze_odds_selection_coverage(self._batch("馬連", ((11, 12),)), self.universe)
        self.assertTrue(all(isinstance(values, tuple) and all(isinstance(item, tuple) for item in values) for values in (coverage.expected_selections, coverage.observed_selections, coverage.missing_selections, coverage.unexpected_selections)))

    def test_outputs_are_sorted_and_deterministic(self) -> None:
        coverage = _analyze_odds_selection_coverage(self._batch("馬連", ((12, 13), (11, 13))), self.universe)
        self.assertEqual(coverage.observed_selections, ((11, 13), (12, 13)))

    def test_missing_and_unexpected_are_disjoint(self) -> None:
        coverage = _analyze_odds_selection_coverage(self._batch("単勝", ((11,), (14,))), self.universe)
        self.assertFalse(set(coverage.missing_selections) & set(coverage.unexpected_selections))

    def test_missing_is_subset_of_expected(self) -> None:
        coverage = _analyze_odds_selection_coverage(self._batch("単勝", ((11,),)), self.universe)
        self.assertTrue(set(coverage.missing_selections) <= set(coverage.expected_selections))

    def test_unexpected_is_subset_of_observed(self) -> None:
        coverage = _analyze_odds_selection_coverage(self._batch("単勝", ((11,), (14,))), self.universe)
        self.assertTrue(set(coverage.unexpected_selections) <= set(coverage.observed_selections))

    def test_coverage_model_is_frozen(self) -> None:
        coverage = _analyze_odds_selection_coverage(self._batch("単勝", ((11,),)), self.universe)
        with self.assertRaises(FrozenInstanceError): coverage.expected_selections = ()

    def test_coverage_counts_and_flags(self) -> None:
        coverage = _analyze_odds_selection_coverage(self._batch("単勝", ((11,),)), self.universe)
        self.assertEqual((coverage.expected_count, coverage.observed_count), (3, 1))
        self.assertTrue(coverage.has_missing)
        self.assertFalse(coverage.has_unexpected)

    def test_coverage_model_rejects_inconsistent_discrepancies(self) -> None:
        with self.assertRaises(ProviderValidationError):
            _OddsSelectionCoverage(((11,),), ((11,),), ((11,),), ())

    def test_rejects_invalid_batch_type(self) -> None:
        for batch in (None, {}, (), object()):
            with self.subTest(batch=type(batch).__name__), self.assertRaises(ProviderValidationError): _analyze_odds_selection_coverage(batch, self.universe)

    def test_rejects_invalid_universe_type(self) -> None:
        batch = self._batch("単勝", ((11,),))
        for universe in (None, {}, (), object()):
            with self.subTest(universe=type(universe).__name__), self.assertRaises(ProviderValidationError): _analyze_odds_selection_coverage(batch, universe)

    def test_does_not_mutate_batch(self) -> None:
        batch = self._batch("単勝", ((11,),))
        _analyze_odds_selection_coverage(batch, self.universe)
        self.assertEqual(batch, self._batch("単勝", ((11,),)))

    def test_does_not_mutate_universe(self) -> None:
        before = self.universe
        _analyze_odds_selection_coverage(self._batch("単勝", ((11,),)), self.universe)
        self.assertEqual(self.universe, before)

    def test_does_not_create_completeness_result(self) -> None:
        self.assertNotEqual(type(_analyze_odds_selection_coverage(self._batch("単勝", ((11,),)), self.universe)).__name__, "CompletenessResult")

    def test_does_not_create_provider_build_result(self) -> None:
        self.assertNotEqual(type(_analyze_odds_selection_coverage(self._batch("単勝", ((11,),)), self.universe)).__name__, "ProviderBuildResult")

    def test_does_not_generate_string_selection_keys(self) -> None:
        coverage = _analyze_odds_selection_coverage(self._batch("馬連", ((11, 12),)), self.universe)
        self.assertFalse(any(isinstance(selection, str) for selection in coverage.expected_selections))

    def test_has_no_database_repository_save_or_network_dependency(self) -> None:
        tree = ast.parse((Path(__file__).parents[1] / "scripts/simulation/providers/odds_provider.py").read_text(encoding="utf-8"))
        imports = {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
        forbidden = ("sqlite3", "requests", "httpx", "urllib", "selenium", "playwright", "scripts.simulation.repositories.sqlite")
        self.assertFalse(any(name.startswith(forbidden) for name in imports))
        self.assertNotIn("save_odds_batch", _analyze_odds_selection_coverage.__code__.co_names)

    def test_internal_model_and_helper_are_not_exported_from_package_root(self) -> None:
        self.assertFalse(hasattr(providers, "_OddsSelectionCoverage"))
        self.assertFalse(hasattr(providers, "_analyze_odds_selection_coverage"))
