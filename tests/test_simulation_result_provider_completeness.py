"""Tests for Result Provider completeness construction from coverage facts."""

import ast
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch
import unittest

from scripts.simulation.providers.errors import ProviderValidationError
from scripts.simulation.providers.models import CompletenessResult, CompletenessStatus, RaceEntryUniverse
from scripts.simulation.providers.result_provider import (
    _analyze_result_coverage,
    _build_result_completeness,
)
from scripts.simulation.repositories.interfaces import (
    PersistedRaceResult,
    PersistedRaceResultEntry,
    RaceResultEntryStatus,
    RaceResultStatus,
)


NOW = datetime(2026, 1, 2, 12, 0, tzinfo=UTC)


class ResultProviderCompletenessTest(unittest.TestCase):
    def setUp(self) -> None:
        self.universe = RaceEntryUniverse(1, {1, 2}, set(), set(), {11: 1, 12: 2})

    def _entry(self, entry_id: int, status: RaceResultEntryStatus = RaceResultEntryStatus.CONFIRMED) -> PersistedRaceResultEntry:
        return PersistedRaceResultEntry(entry_id + 10, entry_id, 1 if status is RaceResultEntryStatus.CONFIRMED else None, status)

    def _result(self, status: RaceResultStatus, entries: tuple[PersistedRaceResultEntry, ...]) -> PersistedRaceResult:
        finalized_at = NOW if status is RaceResultStatus.COMPLETE else None
        return PersistedRaceResult(1, status, finalized_at, NOW, "fixture", entries)

    def _completeness(self, status: RaceResultStatus, entries: tuple[PersistedRaceResultEntry, ...]) -> CompletenessResult:
        result = self._result(status, entries)
        return _build_result_completeness(result, _analyze_result_coverage(result, self.universe))

    def test_complete_result_without_discrepancy_is_complete(self) -> None:
        completeness = self._completeness(RaceResultStatus.COMPLETE, (self._entry(1), self._entry(2)))
        self.assertIs(completeness.status, CompletenessStatus.COMPLETE)

    def test_void_result_without_discrepancy_is_complete(self) -> None:
        completeness = self._completeness(RaceResultStatus.VOID, (self._entry(1), self._entry(2)))
        self.assertIs(completeness.status, CompletenessStatus.COMPLETE)

    def test_partial_result_without_discrepancy_is_incomplete(self) -> None:
        completeness = self._completeness(RaceResultStatus.PARTIAL, (self._entry(1), self._entry(2)))
        self.assertIs(completeness.status, CompletenessStatus.INCOMPLETE)

    def test_missing_entries_are_incomplete(self) -> None:
        completeness = self._completeness(RaceResultStatus.COMPLETE, (self._entry(1),))
        self.assertIs(completeness.status, CompletenessStatus.INCOMPLETE)
        self.assertEqual(completeness.missing_keys, ("race_entry_id:2",))

    def test_unsupported_result_status_is_unsupported(self) -> None:
        completeness = self._completeness(RaceResultStatus.UNSUPPORTED, ())
        self.assertIs(completeness.status, CompletenessStatus.UNSUPPORTED)

    def test_unsupported_entries_are_unsupported(self) -> None:
        completeness = self._completeness(RaceResultStatus.COMPLETE, (self._entry(1, RaceResultEntryStatus.UNSUPPORTED), self._entry(2)))
        self.assertIs(completeness.status, CompletenessStatus.UNSUPPORTED)

    def test_unexpected_entries_are_invalid(self) -> None:
        completeness = self._completeness(RaceResultStatus.COMPLETE, (self._entry(1), self._entry(2), self._entry(99)))
        self.assertIs(completeness.status, CompletenessStatus.INVALID)

    def test_invalid_has_priority_over_unsupported(self) -> None:
        completeness = self._completeness(RaceResultStatus.COMPLETE, (self._entry(99, RaceResultEntryStatus.UNSUPPORTED),))
        self.assertIs(completeness.status, CompletenessStatus.INVALID)

    def test_unsupported_has_priority_over_incomplete(self) -> None:
        completeness = self._completeness(RaceResultStatus.PARTIAL, (self._entry(1, RaceResultEntryStatus.UNSUPPORTED),))
        self.assertIs(completeness.status, CompletenessStatus.UNSUPPORTED)

    def test_incomplete_has_priority_over_complete(self) -> None:
        completeness = self._completeness(RaceResultStatus.COMPLETE, (self._entry(1),))
        self.assertIs(completeness.status, CompletenessStatus.INCOMPLETE)

    def test_expected_and_observed_counts_come_from_coverage(self) -> None:
        completeness = self._completeness(RaceResultStatus.COMPLETE, (self._entry(1),))
        self.assertEqual((completeness.expected_count, completeness.actual_count), (2, 1))

    def test_missing_keys_use_race_entry_id_format(self) -> None:
        completeness = self._completeness(RaceResultStatus.COMPLETE, (self._entry(1),))
        self.assertEqual(completeness.missing_keys, ("race_entry_id:2",))

    def test_unexpected_keys_use_race_entry_id_format(self) -> None:
        completeness = self._completeness(RaceResultStatus.COMPLETE, (self._entry(1), self._entry(2), self._entry(99)))
        self.assertEqual(completeness.unexpected_keys, ("race_entry_id:99",))

    def test_unsupported_keys_use_race_entry_id_format(self) -> None:
        completeness = self._completeness(RaceResultStatus.COMPLETE, (self._entry(1), self._entry(2), self._entry(99, RaceResultEntryStatus.UNSUPPORTED)))
        self.assertEqual(completeness.unexpected_keys, ("race_entry_id:99",))

    def test_unexpected_unsupported_entry_is_not_duplicated_across_categories(self) -> None:
        completeness = self._completeness(RaceResultStatus.COMPLETE, (self._entry(99, RaceResultEntryStatus.UNSUPPORTED),))
        self.assertFalse(set(completeness.missing_keys) & set(completeness.unexpected_keys))
        self.assertEqual(completeness.unexpected_keys, ("race_entry_id:99",))

    def test_unexpected_unsupported_entry_keeps_both_reasons(self) -> None:
        completeness = self._completeness(RaceResultStatus.COMPLETE, (self._entry(99, RaceResultEntryStatus.UNSUPPORTED),))
        self.assertIn("unexpected_result_entries", completeness.reasons)
        self.assertIn("unsupported_result_entries", completeness.reasons)

    def test_combined_discrepancies_preserve_all_reasons(self) -> None:
        completeness = self._completeness(RaceResultStatus.PARTIAL, (self._entry(99, RaceResultEntryStatus.UNSUPPORTED),))
        self.assertEqual(
            completeness.reasons,
            (
                "missing_result_entries",
                "partial_result_status",
                "unexpected_result_entries",
                "unsupported_result_entries",
            ),
        )

    def test_complete_result_has_empty_reasons(self) -> None:
        self.assertEqual(self._completeness(RaceResultStatus.COMPLETE, (self._entry(1), self._entry(2))).reasons, ())

    def test_void_complete_result_has_empty_reasons(self) -> None:
        self.assertEqual(self._completeness(RaceResultStatus.VOID, (self._entry(1), self._entry(2))).reasons, ())

    def test_reasons_are_deterministic_and_unique(self) -> None:
        first = self._completeness(RaceResultStatus.PARTIAL, (self._entry(99, RaceResultEntryStatus.UNSUPPORTED),))
        second = self._completeness(RaceResultStatus.PARTIAL, (self._entry(99, RaceResultEntryStatus.UNSUPPORTED),))
        self.assertEqual(first.reasons, second.reasons)
        self.assertEqual(len(first.reasons), len(set(first.reasons)))

    def test_discrepancy_keys_are_deterministic_and_unique(self) -> None:
        completeness = self._completeness(RaceResultStatus.COMPLETE, (self._entry(99), self._entry(1)))
        self.assertEqual(completeness.missing_keys, ("race_entry_id:2",))
        self.assertEqual(completeness.unexpected_keys, ("race_entry_id:99",))

    def test_returns_completeness_result(self) -> None:
        self.assertIsInstance(self._completeness(RaceResultStatus.COMPLETE, (self._entry(1), self._entry(2))), CompletenessResult)

    def test_does_not_return_provider_build_result(self) -> None:
        result = self._result(RaceResultStatus.COMPLETE, (self._entry(1), self._entry(2)))
        coverage = _analyze_result_coverage(result, self.universe)
        self.assertNotEqual(type(_build_result_completeness(result, coverage)).__name__, "ProviderBuildResult")

    def test_rejects_invalid_result_type(self) -> None:
        result = self._result(RaceResultStatus.COMPLETE, (self._entry(1), self._entry(2)))
        coverage = _analyze_result_coverage(result, self.universe)
        for invalid in (None, {}, (), object()):
            with self.subTest(result=type(invalid).__name__), self.assertRaises(ProviderValidationError):
                _build_result_completeness(invalid, coverage)

    def test_rejects_invalid_coverage_type(self) -> None:
        result = self._result(RaceResultStatus.COMPLETE, (self._entry(1), self._entry(2)))
        for invalid in (None, {}, (), object()):
            with self.subTest(coverage=type(invalid).__name__), self.assertRaises(ProviderValidationError):
                _build_result_completeness(result, invalid)

    def test_converts_model_errors_to_provider_validation_error(self) -> None:
        result = self._result(RaceResultStatus.COMPLETE, (self._entry(1), self._entry(2)))
        coverage = _analyze_result_coverage(result, self.universe)
        with patch("scripts.simulation.providers.result_provider.CompletenessResult", side_effect=ValueError("bad model")):
            with self.assertRaises(ProviderValidationError) as caught:
                _build_result_completeness(result, coverage)
        self.assertIsInstance(caught.exception.__cause__, ValueError)

    def test_does_not_mutate_result(self) -> None:
        result = self._result(RaceResultStatus.COMPLETE, (self._entry(1), self._entry(2)))
        coverage = _analyze_result_coverage(result, self.universe)
        before = result
        _build_result_completeness(result, coverage)
        self.assertEqual(result, before)

    def test_does_not_mutate_coverage(self) -> None:
        result = self._result(RaceResultStatus.COMPLETE, (self._entry(1), self._entry(2)))
        coverage = _analyze_result_coverage(result, self.universe)
        before = coverage
        _build_result_completeness(result, coverage)
        self.assertEqual(coverage, before)

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

    def test_does_not_validate_entry_category_semantics(self) -> None:
        completeness = self._completeness(RaceResultStatus.COMPLETE, (self._entry(1, RaceResultEntryStatus.VOID), self._entry(2)))
        self.assertIs(completeness.status, CompletenessStatus.COMPLETE)
