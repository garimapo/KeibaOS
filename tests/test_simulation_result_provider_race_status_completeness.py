"""Tests for integrating race-status semantic issues into completeness."""

import ast
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch
import unittest

from scripts.simulation.providers.errors import ProviderValidationError
from scripts.simulation.providers.models import CompletenessResult, CompletenessStatus
from scripts.simulation.providers.result_provider import _analyze_result_race_status_semantics, _apply_result_race_status_semantics
from scripts.simulation.repositories.interfaces import PersistedRaceResult, PersistedRaceResultEntry, RaceResultEntryStatus, RaceResultStatus

NOW=datetime(2026,1,2,12,tzinfo=UTC)

class RaceStatusCompletenessTest(unittest.TestCase):
 def _entry(self,id,status): return PersistedRaceResultEntry(id+10,id,1 if status is RaceResultEntryStatus.CONFIRMED else None,status)
 def _issues(self,status,entries=()): return _analyze_result_race_status_semantics(PersistedRaceResult(1,status,NOW if status is RaceResultStatus.COMPLETE else None,NOW,"fixture",entries))
 def _complete(self): return CompletenessResult(CompletenessStatus.COMPLETE,2,2)
 def _incomplete(self): return CompletenessResult(CompletenessStatus.INCOMPLETE,2,1,missing_keys=("race_entry_id:2",),reasons=("missing_result_entries",))
 def _unsupported(self): return CompletenessResult(CompletenessStatus.UNSUPPORTED,2,0,reasons=("unsupported_result_status",))
 def _invalid(self): return CompletenessResult(CompletenessStatus.INVALID,2,2,unexpected_keys=("race_entry_id:9",),reasons=("unexpected_result_entries",))
 def test_no_issues_preserve_all_statuses(self):
  issues=self._issues(RaceResultStatus.COMPLETE)
  for completeness in (self._complete(),self._incomplete(),self._unsupported(),self._invalid()):
   with self.subTest(status=completeness.status): self.assertIs(_apply_result_race_status_semantics(completeness,issues),completeness)
 def test_void_issue_promotes_complete_to_invalid(self): self.assertIs(_apply_result_race_status_semantics(self._complete(),self._issues(RaceResultStatus.VOID,(self._entry(1,RaceResultEntryStatus.CONFIRMED),))).status,CompletenessStatus.INVALID)
 def test_unsupported_race_issue_promotes_complete_to_invalid(self): self.assertIs(_apply_result_race_status_semantics(self._complete(),self._issues(RaceResultStatus.UNSUPPORTED,(self._entry(1,RaceResultEntryStatus.VOID),))).status,CompletenessStatus.INVALID)
 def test_void_issue_promotes_incomplete_to_invalid(self): self.assertIs(_apply_result_race_status_semantics(self._incomplete(),self._issues(RaceResultStatus.VOID,(self._entry(1,RaceResultEntryStatus.CONFIRMED),))).status,CompletenessStatus.INVALID)
 def test_unsupported_race_issue_promotes_unsupported_to_invalid(self): self.assertIs(_apply_result_race_status_semantics(self._unsupported(),self._issues(RaceResultStatus.UNSUPPORTED,(self._entry(1,RaceResultEntryStatus.VOID),))).status,CompletenessStatus.INVALID)
 def test_issue_keeps_existing_invalid_status(self): self.assertIs(_apply_result_race_status_semantics(self._invalid(),self._issues(RaceResultStatus.VOID,(self._entry(1,RaceResultEntryStatus.CONFIRMED),))).status,CompletenessStatus.INVALID)
 def test_void_reason_is_added(self): self.assertIn("void_race_non_void_result_entries",_apply_result_race_status_semantics(self._complete(),self._issues(RaceResultStatus.VOID,(self._entry(1,RaceResultEntryStatus.CONFIRMED),))).reasons)
 def test_unsupported_race_reason_is_added(self): self.assertIn("unsupported_race_non_unsupported_result_entries",_apply_result_race_status_semantics(self._complete(),self._issues(RaceResultStatus.UNSUPPORTED,(self._entry(1,RaceResultEntryStatus.VOID),))).reasons)
 def test_existing_reasons_and_keys_are_preserved(self):
  result=_apply_result_race_status_semantics(self._invalid(),self._issues(RaceResultStatus.VOID,(self._entry(1,RaceResultEntryStatus.CONFIRMED),)))
  self.assertIn("unexpected_result_entries",result.reasons); self.assertEqual(result.unexpected_keys,("race_entry_id:9",)); self.assertEqual(result.duplicate_keys,())
 def test_semantic_ids_are_not_added_to_discrepancy_keys(self):
  result=_apply_result_race_status_semantics(self._complete(),self._issues(RaceResultStatus.VOID,(self._entry(1,RaceResultEntryStatus.CONFIRMED),)))
  self.assertEqual((result.missing_keys,result.unexpected_keys,result.duplicate_keys),((),(),()))
 def test_counts_are_preserved(self):
  value=self._incomplete(); result=_apply_result_race_status_semantics(value,self._issues(RaceResultStatus.VOID,(self._entry(1,RaceResultEntryStatus.CONFIRMED),))); self.assertEqual((result.expected_count,result.actual_count),(value.expected_count,value.actual_count))
 def test_reasons_are_unique_and_deterministic(self):
  issues=self._issues(RaceResultStatus.VOID,(self._entry(1,RaceResultEntryStatus.CONFIRMED),self._entry(2,RaceResultEntryStatus.UNSUPPORTED))); first=_apply_result_race_status_semantics(self._incomplete(),issues); second=_apply_result_race_status_semantics(self._incomplete(),issues); self.assertEqual(first.reasons,second.reasons); self.assertEqual(len(first.reasons),len(set(first.reasons)))
 def test_returns_completeness_not_build_result(self):
  value=_apply_result_race_status_semantics(self._complete(),self._issues(RaceResultStatus.COMPLETE)); self.assertIsInstance(value,CompletenessResult); self.assertNotEqual(type(value).__name__,"ProviderBuildResult")
 def test_rejects_invalid_inputs(self):
  issues=self._issues(RaceResultStatus.COMPLETE)
  for invalid in (None,{},(),object()):
   with self.subTest(value=type(invalid).__name__), self.assertRaises(ProviderValidationError): _apply_result_race_status_semantics(invalid,issues)
  for invalid in (None,{},(),object()):
   with self.subTest(issue=type(invalid).__name__), self.assertRaises(ProviderValidationError): _apply_result_race_status_semantics(self._complete(),invalid)
 def test_converts_model_errors_to_provider_validation_error(self):
  with patch("scripts.simulation.providers.result_provider.CompletenessResult",side_effect=ValueError("bad model")):
   with self.assertRaises(ProviderValidationError) as caught: _apply_result_race_status_semantics(self._complete(),self._issues(RaceResultStatus.VOID,(self._entry(1,RaceResultEntryStatus.CONFIRMED),)))
  self.assertIsInstance(caught.exception.__cause__,ValueError)
 def test_does_not_mutate_inputs(self):
  value=self._incomplete(); issues=self._issues(RaceResultStatus.VOID,(self._entry(1,RaceResultEntryStatus.CONFIRMED),)); _apply_result_race_status_semantics(value,issues); self.assertEqual(value,self._incomplete()); self.assertEqual(issues,self._issues(RaceResultStatus.VOID,(self._entry(1,RaceResultEntryStatus.CONFIRMED),)))
 def test_does_not_reanalyze_result_entries(self): self.assertNotIn("PersistedRaceResultEntry",_apply_result_race_status_semantics.__code__.co_names)
 def test_has_no_database_repository_or_network_dependency(self):
  tree=ast.parse((Path(__file__).parents[1]/"scripts/simulation/providers/result_provider.py").read_text(encoding="utf-8")); imports={a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names}|{n.module or "" for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)}; self.assertFalse(any(x.startswith(("sqlite3","requests","httpx","urllib","selenium","playwright")) for x in imports)); self.assertNotIn("scripts.simulation.repositories.sqlite",imports)
 def test_does_not_use_nonexistent_discrepancy_fields(self): self.assertNotIn("unsupported_keys",_apply_result_race_status_semantics.__code__.co_names)
