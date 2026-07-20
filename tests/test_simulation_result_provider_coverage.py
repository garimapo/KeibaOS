"""Tests for immutable Result Provider entry-ID coverage facts."""

import ast
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from pathlib import Path
import unittest

from scripts.simulation.providers.errors import ProviderValidationError
from scripts.simulation.providers.models import RaceEntryUniverse
from scripts.simulation.providers.result_provider import _analyze_result_coverage
from scripts.simulation.repositories.interfaces import (
    PersistedRaceResult,
    PersistedRaceResultEntry,
    RaceResultEntryStatus,
    RaceResultStatus,
)


NOW = datetime(2026, 1, 2, 12, 0, tzinfo=UTC)


class ResultProviderCoverageTest(unittest.TestCase):
    def setUp(self) -> None:
        self.universe = RaceEntryUniverse(1, {1, 2}, {3}, {4}, {11: 1, 12: 2, 13: 3, 14: 4})

    def _entry(self, race_entry_id: int, status: RaceResultEntryStatus = RaceResultEntryStatus.CONFIRMED) -> PersistedRaceResultEntry:
        return PersistedRaceResultEntry(
            horse_no=race_entry_id + 10,
            race_entry_id=race_entry_id,
            finish_position=None if status is not RaceResultEntryStatus.CONFIRMED else 1,
            result_status=status,
        )

    def _result(self, entries: tuple[PersistedRaceResultEntry, ...]) -> PersistedRaceResult:
        return PersistedRaceResult(1, RaceResultStatus.PARTIAL, None, NOW, "fixture", entries)

    def test_builds_empty_coverage(self) -> None:
        coverage = _analyze_result_coverage(self._result(()), self.universe)
        self.assertEqual(coverage.observed_entry_ids, ())
        self.assertEqual(coverage.missing_entry_ids, (1, 2, 3, 4))

    def test_expected_ids_include_all_universe_categories(self) -> None:
        coverage = _analyze_result_coverage(self._result(()), self.universe)
        self.assertEqual(coverage.expected_entry_ids, (1, 2, 3, 4))

    def test_observed_ids_come_from_result_entries(self) -> None:
        coverage = _analyze_result_coverage(self._result((self._entry(2), self._entry(1))), self.universe)
        self.assertEqual(coverage.observed_entry_ids, (1, 2))

    def test_detects_missing_active_entries(self) -> None:
        coverage = _analyze_result_coverage(self._result((self._entry(1),)), self.universe)
        self.assertEqual(coverage.missing_active_entry_ids, (2,))

    def test_detects_missing_excluded_entries(self) -> None:
        coverage = _analyze_result_coverage(self._result((self._entry(1), self._entry(2))), self.universe)
        self.assertEqual(coverage.missing_excluded_entry_ids, (3,))

    def test_detects_missing_cancelled_entries(self) -> None:
        coverage = _analyze_result_coverage(self._result((self._entry(1), self._entry(2), self._entry(3))), self.universe)
        self.assertEqual(coverage.missing_cancelled_entry_ids, (4,))

    def test_detects_multiple_missing_categories(self) -> None:
        coverage = _analyze_result_coverage(self._result((self._entry(1),)), self.universe)
        self.assertEqual(coverage.missing_entry_ids, (2, 3, 4))

    def test_detects_unexpected_entries(self) -> None:
        coverage = _analyze_result_coverage(self._result((self._entry(99),)), self.universe)
        self.assertEqual(coverage.unexpected_entry_ids, (99,))

    def test_detects_unsupported_entries(self) -> None:
        coverage = _analyze_result_coverage(self._result((self._entry(1, RaceResultEntryStatus.UNSUPPORTED),)), self.universe)
        self.assertEqual(coverage.unsupported_entry_ids, (1,))

    def test_unsupported_entry_is_not_missing_when_observed(self) -> None:
        coverage = _analyze_result_coverage(self._result((self._entry(1, RaceResultEntryStatus.UNSUPPORTED),)), self.universe)
        self.assertNotIn(1, coverage.missing_entry_ids)

    def test_unsupported_unexpected_entry_appears_in_both_axes(self) -> None:
        coverage = _analyze_result_coverage(self._result((self._entry(99, RaceResultEntryStatus.UNSUPPORTED),)), self.universe)
        self.assertEqual(coverage.unexpected_entry_ids, (99,))
        self.assertEqual(coverage.unsupported_entry_ids, (99,))

    def test_outputs_are_sorted_tuples(self) -> None:
        coverage = _analyze_result_coverage(self._result((self._entry(99), self._entry(2), self._entry(1))), self.universe)
        for name in coverage.__dataclass_fields__:
            values = getattr(coverage, name)
            self.assertIsInstance(values, tuple)
            self.assertEqual(values, tuple(sorted(values)))

    def test_outputs_have_no_duplicates(self) -> None:
        coverage = _analyze_result_coverage(self._result((self._entry(1), self._entry(2))), self.universe)
        for name in coverage.__dataclass_fields__:
            values = getattr(coverage, name)
            self.assertEqual(len(values), len(set(values)))

    def test_missing_category_union_matches_missing_entries(self) -> None:
        coverage = _analyze_result_coverage(self._result((self._entry(1),)), self.universe)
        categories = set(coverage.missing_active_entry_ids) | set(coverage.missing_excluded_entry_ids) | set(coverage.missing_cancelled_entry_ids)
        self.assertEqual(categories, set(coverage.missing_entry_ids))

    def test_missing_and_unexpected_are_disjoint(self) -> None:
        coverage = _analyze_result_coverage(self._result((self._entry(99),)), self.universe)
        self.assertFalse(set(coverage.missing_entry_ids) & set(coverage.unexpected_entry_ids))

    def test_unsupported_is_subset_of_observed(self) -> None:
        coverage = _analyze_result_coverage(self._result((self._entry(1, RaceResultEntryStatus.UNSUPPORTED),)), self.universe)
        self.assertTrue(set(coverage.unsupported_entry_ids).issubset(coverage.observed_entry_ids))

    def test_rejects_invalid_result_type(self) -> None:
        for result in (None, {}, (), object()):
            with self.subTest(result=type(result).__name__), self.assertRaises(ProviderValidationError):
                _analyze_result_coverage(result, self.universe)

    def test_rejects_invalid_universe_type(self) -> None:
        for universe in (None, {}, (), object()):
            with self.subTest(universe=type(universe).__name__), self.assertRaises(ProviderValidationError):
                _analyze_result_coverage(self._result(()), universe)

    def test_does_not_mutate_result(self) -> None:
        result = self._result((self._entry(1),))
        before = result
        _analyze_result_coverage(result, self.universe)
        self.assertEqual(result, before)

    def test_does_not_mutate_universe(self) -> None:
        before = self.universe
        _analyze_result_coverage(self._result(()), self.universe)
        self.assertEqual(self.universe, before)

    def test_coverage_is_frozen(self) -> None:
        coverage = _analyze_result_coverage(self._result(()), self.universe)
        with self.assertRaises(FrozenInstanceError):
            coverage.expected_entry_ids = ()

    def test_does_not_return_completeness_result(self) -> None:
        coverage = _analyze_result_coverage(self._result(()), self.universe)
        self.assertNotEqual(type(coverage).__name__, "CompletenessResult")

    def test_does_not_return_provider_build_result(self) -> None:
        coverage = _analyze_result_coverage(self._result(()), self.universe)
        self.assertNotEqual(type(coverage).__name__, "ProviderBuildResult")

    def test_has_no_database_repository_or_network_dependency(self) -> None:
        path = Path(__file__).parents[1] / "scripts/simulation/providers/result_provider.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        forbidden_prefixes = ("sqlite3", "requests", "httpx", "urllib", "selenium", "playwright")
        self.assertFalse(any(name.startswith(forbidden_prefixes) for name in imports))
        self.assertNotIn("scripts.simulation.repositories.sqlite", imports)

    def test_does_not_use_horse_number_as_coverage_key(self) -> None:
        coverage = _analyze_result_coverage(self._result((self._entry(1),)), self.universe)
        self.assertIn(1, coverage.observed_entry_ids)
        self.assertNotIn(11, coverage.observed_entry_ids)
