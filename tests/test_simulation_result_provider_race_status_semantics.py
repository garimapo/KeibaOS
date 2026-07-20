"""Tests for pure race-status versus entry-status semantic analysis."""

import ast
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from pathlib import Path
import unittest

from scripts.simulation.providers.errors import ProviderValidationError
from scripts.simulation.providers.result_provider import _analyze_result_race_status_semantics
from scripts.simulation.repositories.interfaces import PersistedRaceResult, PersistedRaceResultEntry, RaceResultEntryStatus, RaceResultStatus

NOW = datetime(2026, 1, 2, 12, tzinfo=UTC)


class RaceStatusSemanticsTest(unittest.TestCase):
    def _entry(self, entry_id: int, status: RaceResultEntryStatus) -> PersistedRaceResultEntry:
        return PersistedRaceResultEntry(entry_id + 10, entry_id, 1 if status is RaceResultEntryStatus.CONFIRMED else None, status)

    def _result(self, status: RaceResultStatus, entries=()) -> PersistedRaceResult:
        return PersistedRaceResult(1, status, NOW if status is RaceResultStatus.COMPLETE else None, NOW, "fixture", entries)

    def _issues(self, status: RaceResultStatus, entries=()):
        return _analyze_result_race_status_semantics(self._result(status, entries))

    def test_complete_race_adds_no_race_status_issues(self): self.assertFalse(self._issues(RaceResultStatus.COMPLETE, (self._entry(1, RaceResultEntryStatus.VOID),)).has_issues)
    def test_partial_race_adds_no_race_status_issues(self): self.assertFalse(self._issues(RaceResultStatus.PARTIAL, (self._entry(1, RaceResultEntryStatus.CONFIRMED),)).has_issues)
    def test_void_race_with_only_void_entries_has_no_issues(self): self.assertFalse(self._issues(RaceResultStatus.VOID, (self._entry(1, RaceResultEntryStatus.VOID),)).has_issues)
    def test_void_race_detects_confirmed_entry(self): self.assertEqual(self._issues(RaceResultStatus.VOID, (self._entry(1, RaceResultEntryStatus.CONFIRMED),)).void_race_non_void_entry_ids, (1,))
    def test_void_race_detects_unsupported_entry(self): self.assertEqual(self._issues(RaceResultStatus.VOID, (self._entry(1, RaceResultEntryStatus.UNSUPPORTED),)).void_race_non_void_entry_ids, (1,))
    def test_void_race_detects_multiple_non_void_entries(self): self.assertEqual(self._issues(RaceResultStatus.VOID, (self._entry(3, RaceResultEntryStatus.CONFIRMED), self._entry(1, RaceResultEntryStatus.UNSUPPORTED))).all_issue_entry_ids, (1, 3))
    def test_unsupported_race_with_only_unsupported_entries_has_no_issues(self): self.assertFalse(self._issues(RaceResultStatus.UNSUPPORTED, (self._entry(1, RaceResultEntryStatus.UNSUPPORTED),)).has_issues)
    def test_unsupported_race_detects_confirmed_entry(self): self.assertEqual(self._issues(RaceResultStatus.UNSUPPORTED, (self._entry(1, RaceResultEntryStatus.CONFIRMED),)).unsupported_race_non_unsupported_entry_ids, (1,))
    def test_unsupported_race_detects_void_entry(self): self.assertEqual(self._issues(RaceResultStatus.UNSUPPORTED, (self._entry(1, RaceResultEntryStatus.VOID),)).unsupported_race_non_unsupported_entry_ids, (1,))
    def test_unsupported_race_detects_multiple_non_unsupported_entries(self): self.assertEqual(self._issues(RaceResultStatus.UNSUPPORTED, (self._entry(3, RaceResultEntryStatus.CONFIRMED), self._entry(1, RaceResultEntryStatus.VOID))).all_issue_entry_ids, (1, 3))
    def test_empty_statuses_have_no_issues(self):
        for status in RaceResultStatus:
            with self.subTest(status=status): self.assertFalse(self._issues(status).has_issues)
    def test_outputs_sorted_tuples(self):
        issues = self._issues(RaceResultStatus.VOID, (self._entry(3, RaceResultEntryStatus.CONFIRMED), self._entry(1, RaceResultEntryStatus.UNSUPPORTED)))
        self.assertEqual(issues.void_race_non_void_entry_ids, (1, 3))
    def test_output_is_deterministic_for_different_entry_order(self):
        entries=(self._entry(1, RaceResultEntryStatus.CONFIRMED),self._entry(2, RaceResultEntryStatus.UNSUPPORTED))
        self.assertEqual(self._issues(RaceResultStatus.VOID, entries), self._issues(RaceResultStatus.VOID, tuple(reversed(entries))))
    def test_issue_categories_are_disjoint(self):
        issues=self._issues(RaceResultStatus.VOID,(self._entry(1,RaceResultEntryStatus.CONFIRMED),))
        self.assertFalse(set(issues.void_race_non_void_entry_ids)&set(issues.unsupported_race_non_unsupported_entry_ids))
    def test_issues_model_is_frozen(self):
        with self.assertRaises(FrozenInstanceError): self._issues(RaceResultStatus.COMPLETE).void_race_non_void_entry_ids=(1,)
    def test_has_issues_property(self): self.assertTrue(self._issues(RaceResultStatus.VOID,(self._entry(1,RaceResultEntryStatus.CONFIRMED),)).has_issues)
    def test_all_issue_entry_ids_property(self): self.assertEqual(self._issues(RaceResultStatus.UNSUPPORTED,(self._entry(2,RaceResultEntryStatus.VOID),)).all_issue_entry_ids,(2,))
    def test_rejects_invalid_result_type(self):
        for invalid in (None,{},(),[],object()):
            with self.subTest(value=type(invalid).__name__), self.assertRaises(ProviderValidationError): _analyze_result_race_status_semantics(invalid)
    def test_does_not_mutate_result(self):
        result=self._result(RaceResultStatus.VOID,(self._entry(1,RaceResultEntryStatus.CONFIRMED),)); before=result; _analyze_result_race_status_semantics(result); self.assertEqual(result,before)
    def test_does_not_return_completeness_or_build_result(self):
        issues=self._issues(RaceResultStatus.COMPLETE); self.assertNotEqual(type(issues).__name__,"CompletenessResult"); self.assertNotEqual(type(issues).__name__,"ProviderBuildResult")
    def test_helper_does_not_accept_or_use_universe(self):
        self.assertEqual(list(_analyze_result_race_status_semantics.__annotations__), ["result", "return"])
    def test_has_no_database_repository_or_network_dependency(self):
        tree=ast.parse((Path(__file__).parents[1]/"scripts/simulation/providers/result_provider.py").read_text(encoding="utf-8")); imports={a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names}|{n.module or "" for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)}
        self.assertFalse(any(name.startswith(("sqlite3","requests","httpx","urllib","selenium","playwright")) for name in imports)); self.assertNotIn("scripts.simulation.repositories.sqlite",imports)
    def test_uses_race_entry_id_not_horse_number(self): self.assertEqual(self._issues(RaceResultStatus.VOID,(self._entry(1,RaceResultEntryStatus.CONFIRMED),)).all_issue_entry_ids,(1,))
