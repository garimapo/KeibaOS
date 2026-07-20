"""Tests for pure Result Provider category/status semantic analysis."""

import ast
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from pathlib import Path
import unittest

from scripts.simulation.providers.errors import ProviderValidationError
from scripts.simulation.providers.models import RaceEntryUniverse
from scripts.simulation.providers.result_provider import _analyze_result_entry_semantics
from scripts.simulation.repositories.interfaces import (
    PersistedRaceResult,
    PersistedRaceResultEntry,
    RaceResultEntryStatus,
    RaceResultStatus,
)


NOW = datetime(2026, 1, 2, 12, 0, tzinfo=UTC)


class ResultProviderEntrySemanticsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.universe = RaceEntryUniverse(1, {1}, {2}, {3}, {11: 1, 12: 2, 13: 3})

    def _entry(self, entry_id: int, status: RaceResultEntryStatus) -> PersistedRaceResultEntry:
        return PersistedRaceResultEntry(
            horse_no=entry_id + 10,
            race_entry_id=entry_id,
            finish_position=1 if status is RaceResultEntryStatus.CONFIRMED else None,
            result_status=status,
        )

    def _result(
        self,
        entries: tuple[PersistedRaceResultEntry, ...],
        status: RaceResultStatus = RaceResultStatus.PARTIAL,
    ) -> PersistedRaceResult:
        return PersistedRaceResult(1, status, None, NOW, "fixture", entries)

    def _issues(self, entries: tuple[PersistedRaceResultEntry, ...], status: RaceResultStatus = RaceResultStatus.PARTIAL):
        return _analyze_result_entry_semantics(self._result(entries, status), self.universe)

    def test_no_issues_when_active_is_confirmed_and_excluded_cancelled_are_void(self) -> None:
        issues = self._issues((self._entry(1, RaceResultEntryStatus.CONFIRMED), self._entry(2, RaceResultEntryStatus.VOID), self._entry(3, RaceResultEntryStatus.VOID)))
        self.assertFalse(issues.has_issues)
        self.assertEqual(issues.all_issue_entry_ids, ())

    def test_detects_active_void_entry(self) -> None:
        self.assertEqual(self._issues((self._entry(1, RaceResultEntryStatus.VOID),)).active_non_confirmed_entry_ids, (1,))

    def test_detects_active_unsupported_entry(self) -> None:
        self.assertEqual(self._issues((self._entry(1, RaceResultEntryStatus.UNSUPPORTED),)).active_non_confirmed_entry_ids, (1,))

    def test_detects_excluded_confirmed_entry(self) -> None:
        self.assertEqual(self._issues((self._entry(2, RaceResultEntryStatus.CONFIRMED),)).excluded_non_void_entry_ids, (2,))

    def test_detects_excluded_unsupported_entry(self) -> None:
        self.assertEqual(self._issues((self._entry(2, RaceResultEntryStatus.UNSUPPORTED),)).excluded_non_void_entry_ids, (2,))

    def test_detects_cancelled_confirmed_entry(self) -> None:
        self.assertEqual(self._issues((self._entry(3, RaceResultEntryStatus.CONFIRMED),)).cancelled_non_void_entry_ids, (3,))

    def test_detects_cancelled_unsupported_entry(self) -> None:
        self.assertEqual(self._issues((self._entry(3, RaceResultEntryStatus.UNSUPPORTED),)).cancelled_non_void_entry_ids, (3,))

    def test_detects_issues_across_all_categories(self) -> None:
        issues = self._issues((self._entry(1, RaceResultEntryStatus.VOID), self._entry(2, RaceResultEntryStatus.CONFIRMED), self._entry(3, RaceResultEntryStatus.UNSUPPORTED)))
        self.assertEqual(issues.all_issue_entry_ids, (1, 2, 3))

    def test_does_not_report_confirmed_active_entry(self) -> None:
        self.assertEqual(self._issues((self._entry(1, RaceResultEntryStatus.CONFIRMED),)).active_non_confirmed_entry_ids, ())

    def test_does_not_report_void_excluded_entry(self) -> None:
        self.assertEqual(self._issues((self._entry(2, RaceResultEntryStatus.VOID),)).excluded_non_void_entry_ids, ())

    def test_does_not_report_void_cancelled_entry(self) -> None:
        self.assertEqual(self._issues((self._entry(3, RaceResultEntryStatus.VOID),)).cancelled_non_void_entry_ids, ())

    def test_does_not_report_missing_active_entry(self) -> None:
        self.assertFalse(self._issues(()).has_issues)

    def test_does_not_report_missing_excluded_entry(self) -> None:
        self.assertFalse(self._issues(()).has_issues)

    def test_does_not_report_missing_cancelled_entry(self) -> None:
        self.assertFalse(self._issues(()).has_issues)

    def test_does_not_classify_unexpected_entry(self) -> None:
        issues = self._issues((self._entry(99, RaceResultEntryStatus.CONFIRMED),))
        self.assertFalse(issues.has_issues)

    def test_does_not_use_race_status_for_classification(self) -> None:
        entries = (self._entry(1, RaceResultEntryStatus.CONFIRMED), self._entry(2, RaceResultEntryStatus.VOID), self._entry(3, RaceResultEntryStatus.VOID))
        complete_result = PersistedRaceResult(1, RaceResultStatus.COMPLETE, NOW, NOW, "fixture", entries)
        void_result = self._result(entries, RaceResultStatus.VOID)
        self.assertEqual(
            _analyze_result_entry_semantics(complete_result, self.universe),
            _analyze_result_entry_semantics(void_result, self.universe),
        )

    def test_outputs_sorted_tuples(self) -> None:
        issues = self._issues((self._entry(3, RaceResultEntryStatus.CONFIRMED), self._entry(2, RaceResultEntryStatus.CONFIRMED), self._entry(1, RaceResultEntryStatus.VOID)))
        for name in issues.__dataclass_fields__:
            values = getattr(issues, name)
            self.assertIsInstance(values, tuple)
            self.assertEqual(values, tuple(sorted(values)))

    def test_output_is_deterministic_for_different_entry_order(self) -> None:
        entries = (self._entry(1, RaceResultEntryStatus.VOID), self._entry(2, RaceResultEntryStatus.CONFIRMED), self._entry(3, RaceResultEntryStatus.UNSUPPORTED))
        self.assertEqual(self._issues(entries), self._issues(tuple(reversed(entries))))

    def test_issue_categories_are_disjoint(self) -> None:
        issues = self._issues((self._entry(1, RaceResultEntryStatus.VOID), self._entry(2, RaceResultEntryStatus.CONFIRMED), self._entry(3, RaceResultEntryStatus.UNSUPPORTED)))
        sets = [set(getattr(issues, name)) for name in issues.__dataclass_fields__]
        self.assertFalse(sets[0] & sets[1])
        self.assertFalse(sets[0] & sets[2])
        self.assertFalse(sets[1] & sets[2])

    def test_issues_model_is_frozen(self) -> None:
        issues = self._issues(())
        with self.assertRaises(FrozenInstanceError):
            issues.active_non_confirmed_entry_ids = (1,)

    def test_rejects_invalid_result_type(self) -> None:
        for invalid in (None, {}, (), object()):
            with self.subTest(result=type(invalid).__name__), self.assertRaises(ProviderValidationError):
                _analyze_result_entry_semantics(invalid, self.universe)

    def test_rejects_invalid_universe_type(self) -> None:
        result = self._result(())
        for invalid in (None, {}, (), object()):
            with self.subTest(universe=type(invalid).__name__), self.assertRaises(ProviderValidationError):
                _analyze_result_entry_semantics(result, invalid)

    def test_does_not_mutate_result(self) -> None:
        result = self._result((self._entry(1, RaceResultEntryStatus.CONFIRMED),))
        before = result
        _analyze_result_entry_semantics(result, self.universe)
        self.assertEqual(result, before)

    def test_does_not_mutate_universe(self) -> None:
        before = self.universe
        _analyze_result_entry_semantics(self._result(()), self.universe)
        self.assertEqual(self.universe, before)

    def test_does_not_return_completeness_result(self) -> None:
        self.assertNotEqual(type(self._issues(())).__name__, "CompletenessResult")

    def test_does_not_return_provider_build_result(self) -> None:
        self.assertNotEqual(type(self._issues(())).__name__, "ProviderBuildResult")

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

    def test_uses_race_entry_id_not_horse_number(self) -> None:
        issues = self._issues((self._entry(1, RaceResultEntryStatus.VOID),))
        self.assertEqual(issues.active_non_confirmed_entry_ids, (1,))
        self.assertNotIn(11, issues.active_non_confirmed_entry_ids)
