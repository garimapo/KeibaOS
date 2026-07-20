"""Tests for integrating entry semantic issues into completeness facts."""

import ast
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch
import unittest

from scripts.simulation.providers.errors import ProviderValidationError
from scripts.simulation.providers.models import CompletenessResult, CompletenessStatus, RaceEntryUniverse
from scripts.simulation.providers.result_provider import (
    _analyze_result_entry_semantics,
    _apply_result_entry_semantics,
)
from scripts.simulation.repositories.interfaces import (
    PersistedRaceResult,
    PersistedRaceResultEntry,
    RaceResultEntryStatus,
    RaceResultStatus,
)


NOW = datetime(2026, 1, 2, 12, 0, tzinfo=UTC)


class ResultProviderSemanticCompletenessTest(unittest.TestCase):
    def setUp(self) -> None:
        self.universe = RaceEntryUniverse(1, {1}, {2}, {3}, {11: 1, 12: 2, 13: 3})

    def _entry(self, entry_id: int, status: RaceResultEntryStatus) -> PersistedRaceResultEntry:
        return PersistedRaceResultEntry(entry_id + 10, entry_id, 1 if status is RaceResultEntryStatus.CONFIRMED else None, status)

    def _issues(self, entries: tuple[PersistedRaceResultEntry, ...]):
        result = PersistedRaceResult(1, RaceResultStatus.PARTIAL, None, NOW, "fixture", entries)
        return _analyze_result_entry_semantics(result, self.universe)

    def _complete(self) -> CompletenessResult:
        return CompletenessResult(CompletenessStatus.COMPLETE, 3, 3)

    def _incomplete(self) -> CompletenessResult:
        return CompletenessResult(CompletenessStatus.INCOMPLETE, 3, 2, missing_keys=("race_entry_id:3",), reasons=("missing_result_entries",))

    def _unsupported(self) -> CompletenessResult:
        return CompletenessResult(CompletenessStatus.UNSUPPORTED, 3, 0, reasons=("unsupported_result_status",))

    def _invalid(self) -> CompletenessResult:
        return CompletenessResult(CompletenessStatus.INVALID, 3, 3, unexpected_keys=("race_entry_id:9",), reasons=("unexpected_result_entries",))

    def test_no_issues_preserves_complete_completeness(self) -> None:
        completeness = self._complete()
        self.assertIs(_apply_result_entry_semantics(completeness, self._issues(())), completeness)

    def test_no_issues_preserves_incomplete_completeness(self) -> None:
        completeness = self._incomplete()
        self.assertIs(_apply_result_entry_semantics(completeness, self._issues(())), completeness)

    def test_no_issues_preserves_unsupported_completeness(self) -> None:
        completeness = self._unsupported()
        self.assertIs(_apply_result_entry_semantics(completeness, self._issues(())), completeness)

    def test_no_issues_preserves_invalid_completeness(self) -> None:
        completeness = self._invalid()
        self.assertIs(_apply_result_entry_semantics(completeness, self._issues(())), completeness)

    def test_active_issue_promotes_complete_to_invalid(self) -> None:
        result = _apply_result_entry_semantics(self._complete(), self._issues((self._entry(1, RaceResultEntryStatus.VOID),)))
        self.assertIs(result.status, CompletenessStatus.INVALID)

    def test_excluded_issue_promotes_complete_to_invalid(self) -> None:
        result = _apply_result_entry_semantics(self._complete(), self._issues((self._entry(2, RaceResultEntryStatus.CONFIRMED),)))
        self.assertIs(result.status, CompletenessStatus.INVALID)

    def test_cancelled_issue_promotes_complete_to_invalid(self) -> None:
        result = _apply_result_entry_semantics(self._complete(), self._issues((self._entry(3, RaceResultEntryStatus.CONFIRMED),)))
        self.assertIs(result.status, CompletenessStatus.INVALID)

    def test_semantic_issue_promotes_incomplete_to_invalid(self) -> None:
        result = _apply_result_entry_semantics(self._incomplete(), self._issues((self._entry(1, RaceResultEntryStatus.VOID),)))
        self.assertIs(result.status, CompletenessStatus.INVALID)

    def test_semantic_issue_promotes_unsupported_to_invalid(self) -> None:
        result = _apply_result_entry_semantics(self._unsupported(), self._issues((self._entry(1, RaceResultEntryStatus.VOID),)))
        self.assertIs(result.status, CompletenessStatus.INVALID)

    def test_semantic_issue_keeps_invalid_status(self) -> None:
        result = _apply_result_entry_semantics(self._invalid(), self._issues((self._entry(1, RaceResultEntryStatus.VOID),)))
        self.assertIs(result.status, CompletenessStatus.INVALID)

    def test_active_reason_is_added(self) -> None:
        result = _apply_result_entry_semantics(self._complete(), self._issues((self._entry(1, RaceResultEntryStatus.VOID),)))
        self.assertIn("active_non_confirmed_result_entries", result.reasons)

    def test_excluded_reason_is_added(self) -> None:
        result = _apply_result_entry_semantics(self._complete(), self._issues((self._entry(2, RaceResultEntryStatus.CONFIRMED),)))
        self.assertIn("excluded_non_void_result_entries", result.reasons)

    def test_cancelled_reason_is_added(self) -> None:
        result = _apply_result_entry_semantics(self._complete(), self._issues((self._entry(3, RaceResultEntryStatus.CONFIRMED),)))
        self.assertIn("cancelled_non_void_result_entries", result.reasons)

    def test_multiple_semantic_reasons_are_added(self) -> None:
        result = _apply_result_entry_semantics(self._complete(), self._issues((self._entry(1, RaceResultEntryStatus.VOID), self._entry(2, RaceResultEntryStatus.CONFIRMED), self._entry(3, RaceResultEntryStatus.UNSUPPORTED))))
        self.assertEqual(
            result.reasons,
            (
                "active_non_confirmed_result_entries",
                "cancelled_non_void_result_entries",
                "excluded_non_void_result_entries",
            ),
        )

    def test_existing_reasons_are_preserved(self) -> None:
        result = _apply_result_entry_semantics(self._incomplete(), self._issues((self._entry(1, RaceResultEntryStatus.VOID),)))
        self.assertIn("missing_result_entries", result.reasons)

    def test_missing_keys_are_preserved(self) -> None:
        result = _apply_result_entry_semantics(self._incomplete(), self._issues((self._entry(1, RaceResultEntryStatus.VOID),)))
        self.assertEqual(result.missing_keys, ("race_entry_id:3",))

    def test_unexpected_keys_are_preserved(self) -> None:
        result = _apply_result_entry_semantics(self._invalid(), self._issues((self._entry(1, RaceResultEntryStatus.VOID),)))
        self.assertEqual(result.unexpected_keys, ("race_entry_id:9",))

    def test_semantic_ids_are_not_added_to_missing_keys(self) -> None:
        result = _apply_result_entry_semantics(self._complete(), self._issues((self._entry(1, RaceResultEntryStatus.VOID),)))
        self.assertEqual(result.missing_keys, ())

    def test_semantic_ids_are_not_added_to_unexpected_keys(self) -> None:
        result = _apply_result_entry_semantics(self._complete(), self._issues((self._entry(1, RaceResultEntryStatus.VOID),)))
        self.assertEqual(result.unexpected_keys, ())

    def test_counts_are_preserved(self) -> None:
        completeness = self._incomplete()
        result = _apply_result_entry_semantics(completeness, self._issues((self._entry(1, RaceResultEntryStatus.VOID),)))
        self.assertEqual((result.expected_count, result.actual_count), (completeness.expected_count, completeness.actual_count))

    def test_reasons_are_unique_and_deterministic(self) -> None:
        issues = self._issues((self._entry(1, RaceResultEntryStatus.VOID), self._entry(2, RaceResultEntryStatus.CONFIRMED)))
        first = _apply_result_entry_semantics(self._incomplete(), issues)
        second = _apply_result_entry_semantics(self._incomplete(), issues)
        self.assertEqual(first.reasons, second.reasons)
        self.assertEqual(len(first.reasons), len(set(first.reasons)))

    def test_returns_completeness_result(self) -> None:
        self.assertIsInstance(_apply_result_entry_semantics(self._complete(), self._issues(())), CompletenessResult)

    def test_does_not_return_provider_build_result(self) -> None:
        self.assertNotEqual(type(_apply_result_entry_semantics(self._complete(), self._issues(()))).__name__, "ProviderBuildResult")

    def test_rejects_invalid_completeness_type(self) -> None:
        issues = self._issues(())
        for invalid in (None, {}, (), object()):
            with self.subTest(completeness=type(invalid).__name__), self.assertRaises(ProviderValidationError):
                _apply_result_entry_semantics(invalid, issues)

    def test_rejects_invalid_issues_type(self) -> None:
        completeness = self._complete()
        for invalid in (None, {}, (), object()):
            with self.subTest(issues=type(invalid).__name__), self.assertRaises(ProviderValidationError):
                _apply_result_entry_semantics(completeness, invalid)

    def test_converts_model_errors_to_provider_validation_error(self) -> None:
        with patch("scripts.simulation.providers.result_provider.CompletenessResult", side_effect=ValueError("bad model")):
            with self.assertRaises(ProviderValidationError) as caught:
                _apply_result_entry_semantics(self._complete(), self._issues((self._entry(1, RaceResultEntryStatus.VOID),)))
        self.assertIsInstance(caught.exception.__cause__, ValueError)

    def test_does_not_mutate_completeness(self) -> None:
        completeness = self._incomplete()
        before = completeness
        _apply_result_entry_semantics(completeness, self._issues((self._entry(1, RaceResultEntryStatus.VOID),)))
        self.assertEqual(completeness, before)

    def test_does_not_mutate_issues(self) -> None:
        issues = self._issues((self._entry(1, RaceResultEntryStatus.VOID),))
        before = issues
        _apply_result_entry_semantics(self._complete(), issues)
        self.assertEqual(issues, before)

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

    def test_does_not_evaluate_race_status_semantics(self) -> None:
        result = _apply_result_entry_semantics(self._complete(), self._issues((self._entry(1, RaceResultEntryStatus.VOID),)))
        self.assertIs(result.status, CompletenessStatus.INVALID)
