"""Tests for deriving odds completeness from immutable coverage facts."""

import ast
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
import unittest

import scripts.simulation.providers as providers
from scripts.simulation.providers.errors import ProviderValidationError
from scripts.simulation.providers.models import CompletenessResult, CompletenessStatus
from scripts.simulation.providers import odds_provider
from scripts.simulation.providers.odds_provider import _OddsSelectionCoverage, _build_odds_completeness
from scripts.simulation.repositories.interfaces import OddsSnapshotBatch, OddsSnapshotEntry, selection_key


NOW = datetime(2026, 1, 2, 12, 0, tzinfo=UTC)


class OddsProviderCompletenessTest(unittest.TestCase):
    def _batch(self, complete: bool = True, bet_type: str = "単勝") -> OddsSnapshotBatch:
        selection = (11,) if bet_type == "単勝" else (11, 12)
        return OddsSnapshotBatch(10, bet_type, NOW, complete, "fixture", (OddsSnapshotEntry(selection, Decimal("1.2")),))

    def _coverage(self, expected=((11,),), observed=((11,),), missing=(), unexpected=()) -> _OddsSelectionCoverage:
        return _OddsSelectionCoverage(expected, observed, missing, unexpected)

    def test_declared_complete_and_full_coverage_is_complete(self) -> None:
        result = _build_odds_completeness(self._batch(), self._coverage())
        self.assertIs(result.status, CompletenessStatus.COMPLETE)

    def test_declared_incomplete_and_full_coverage_is_incomplete(self) -> None:
        result = _build_odds_completeness(self._batch(False), self._coverage())
        self.assertIs(result.status, CompletenessStatus.INCOMPLETE)

    def test_missing_selection_is_incomplete(self) -> None:
        result = _build_odds_completeness(self._batch(), self._coverage(((11,), (12,)), ((11,),), ((12,),)))
        self.assertIs(result.status, CompletenessStatus.INCOMPLETE)

    def test_missing_and_not_declared_complete_is_incomplete(self) -> None:
        result = _build_odds_completeness(self._batch(False), self._coverage(((11,), (12,)), ((11,),), ((12,),)))
        self.assertIs(result.status, CompletenessStatus.INCOMPLETE)

    def test_unexpected_selection_is_invalid(self) -> None:
        result = _build_odds_completeness(self._batch(), self._coverage(((11,),), ((11,), (12,)), (), ((12,),)))
        self.assertIs(result.status, CompletenessStatus.INVALID)

    def test_invalid_has_priority_over_incomplete(self) -> None:
        coverage = self._coverage(((11,), (12,)), ((11,), (13,)), ((12,),), ((13,),))
        self.assertIs(_build_odds_completeness(self._batch(False), coverage).status, CompletenessStatus.INVALID)

    def test_incomplete_has_priority_over_complete(self) -> None:
        self.assertIs(_build_odds_completeness(self._batch(False), self._coverage()).status, CompletenessStatus.INCOMPLETE)

    def test_expected_count_comes_from_coverage(self) -> None:
        coverage = self._coverage(((11,), (12,)), ((11,),), ((12,),))
        self.assertEqual(_build_odds_completeness(self._batch(), coverage).expected_count, 2)

    def test_actual_count_comes_from_coverage(self) -> None:
        coverage = self._coverage(((11,), (12,)), ((11,),), ((12,),))
        self.assertEqual(_build_odds_completeness(self._batch(), coverage).actual_count, 1)

    def test_missing_keys_use_repository_selection_key(self) -> None:
        coverage = self._coverage(((11,), (12,)), ((11,),), ((12,),))
        result = _build_odds_completeness(self._batch(), coverage)
        self.assertEqual(result.missing_keys, (selection_key((12,), "単勝"),))

    def test_unexpected_keys_use_repository_selection_key(self) -> None:
        coverage = self._coverage(((11,),), ((11,), (12,)), (), ((12,),))
        result = _build_odds_completeness(self._batch(), coverage)
        self.assertEqual(result.unexpected_keys, (selection_key((12,), "単勝"),))

    def test_selection_keys_do_not_include_odds(self) -> None:
        result = _build_odds_completeness(self._batch(), self._coverage(((11,), (12,)), ((11,),), ((12,),)))
        self.assertNotIn("1.2", result.missing_keys[0])

    def test_selection_keys_do_not_use_horse_numbers(self) -> None:
        result = _build_odds_completeness(self._batch(), self._coverage(((11,), (12,)), ((11,),), ((12,),)))
        self.assertEqual(result.missing_keys, ("12",))

    def test_missing_and_unexpected_keys_are_disjoint(self) -> None:
        coverage = self._coverage(((11,), (12,)), ((11,), (13,)), ((12,),), ((13,),))
        result = _build_odds_completeness(self._batch(), coverage)
        self.assertFalse(set(result.missing_keys) & set(result.unexpected_keys))

    def test_duplicate_keys_are_empty(self) -> None:
        self.assertEqual(_build_odds_completeness(self._batch(), self._coverage()).duplicate_keys, ())

    def test_unexpected_reason_is_added(self) -> None:
        result = _build_odds_completeness(self._batch(), self._coverage(((11,),), ((11,), (12,)), (), ((12,),)))
        self.assertIn("unexpected_odds_selections", result.reasons)

    def test_missing_reason_is_added(self) -> None:
        result = _build_odds_completeness(self._batch(), self._coverage(((11,), (12,)), ((11,),), ((12,),)))
        self.assertIn("missing_odds_selections", result.reasons)

    def test_not_declared_complete_reason_is_added(self) -> None:
        self.assertIn("odds_not_declared_complete", _build_odds_completeness(self._batch(False), self._coverage()).reasons)

    def test_combined_facts_preserve_all_reasons(self) -> None:
        coverage = self._coverage(((11,), (12,)), ((11,), (13,)), ((12,),), ((13,),))
        result = _build_odds_completeness(self._batch(False), coverage)
        self.assertEqual(result.reasons, ("missing_odds_selections", "odds_not_declared_complete", "unexpected_odds_selections"))

    def test_complete_has_empty_reasons(self) -> None:
        self.assertEqual(_build_odds_completeness(self._batch(), self._coverage()).reasons, ())

    def test_reasons_are_unique_and_deterministic(self) -> None:
        coverage = self._coverage(((11,), (12,)), ((11,), (13,)), ((12,),), ((13,),))
        first = _build_odds_completeness(self._batch(False), coverage)
        second = _build_odds_completeness(self._batch(False), coverage)
        self.assertEqual(first.reasons, second.reasons)

    def test_discrepancy_keys_are_unique_and_deterministic(self) -> None:
        coverage = self._coverage(((11,), (12,)), ((11,), (13,)), ((12,),), ((13,),))
        result = _build_odds_completeness(self._batch(), coverage)
        self.assertEqual(result.missing_keys, ("12",))
        self.assertEqual(result.unexpected_keys, ("13",))

    def test_empty_complete_coverage_is_complete(self) -> None:
        result = _build_odds_completeness(self._batch(), self._coverage((), (), (), ()))
        self.assertIs(result.status, CompletenessStatus.COMPLETE)

    def test_empty_incomplete_coverage_is_incomplete(self) -> None:
        result = _build_odds_completeness(self._batch(False), self._coverage((), (), (), ()))
        self.assertIs(result.status, CompletenessStatus.INCOMPLETE)

    def test_empty_observed_with_expected_marks_all_missing(self) -> None:
        coverage = self._coverage(((11,), (12,)), (), ((11,), (12,)), ())
        result = _build_odds_completeness(self._batch(), coverage)
        self.assertEqual(result.missing_keys, ("11", "12"))

    def test_returns_completeness_result(self) -> None:
        self.assertIsInstance(_build_odds_completeness(self._batch(), self._coverage()), CompletenessResult)

    def test_does_not_return_provider_build_result(self) -> None:
        self.assertNotEqual(type(_build_odds_completeness(self._batch(), self._coverage())).__name__, "ProviderBuildResult")

    def test_rejects_invalid_batch_type(self) -> None:
        for batch in (None, {}, (), object()):
            with self.subTest(batch=type(batch).__name__), self.assertRaises(ProviderValidationError): _build_odds_completeness(batch, self._coverage())

    def test_rejects_invalid_coverage_type(self) -> None:
        for coverage in (None, {}, (), object()):
            with self.subTest(coverage=type(coverage).__name__), self.assertRaises(ProviderValidationError): _build_odds_completeness(self._batch(), coverage)

    def test_converts_model_errors_to_provider_validation_error(self) -> None:
        with patch("scripts.simulation.providers.odds_provider.CompletenessResult", side_effect=ValueError("bad model")):
            with self.assertRaises(ProviderValidationError) as caught: _build_odds_completeness(self._batch(), self._coverage())
        self.assertIsInstance(caught.exception.__cause__, ValueError)

    def test_does_not_mutate_batch(self) -> None:
        batch = self._batch()
        _build_odds_completeness(batch, self._coverage())
        self.assertEqual(batch, self._batch())

    def test_does_not_mutate_coverage(self) -> None:
        coverage = self._coverage()
        _build_odds_completeness(self._batch(), coverage)
        self.assertEqual(coverage, self._coverage())

    def test_does_not_recompute_expected_selections(self) -> None:
        self.assertNotIn("expected_selections", _build_odds_completeness.__code__.co_names)

    def test_does_not_recheck_duplicate_rows(self) -> None:
        self.assertNotIn("duplicate", _build_odds_completeness.__code__.co_names)

    def test_does_not_generate_unsupported_status(self) -> None:
        result = _build_odds_completeness(self._batch(), self._coverage())
        self.assertIsNot(result.status, CompletenessStatus.UNSUPPORTED)

    def test_has_no_database_repository_save_or_network_dependency(self) -> None:
        tree = ast.parse((Path(__file__).parents[1] / "scripts/simulation/providers/odds_provider.py").read_text(encoding="utf-8"))
        imports = {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
        forbidden = ("sqlite3", "requests", "httpx", "urllib", "selenium", "playwright", "scripts.simulation.repositories.sqlite")
        self.assertFalse(any(name.startswith(forbidden) for name in imports))
        self.assertNotIn("save_odds_batch", _build_odds_completeness.__code__.co_names)

    def test_internal_helper_is_not_exported_from_package_root(self) -> None:
        self.assertFalse(hasattr(providers, "_build_odds_completeness"))
