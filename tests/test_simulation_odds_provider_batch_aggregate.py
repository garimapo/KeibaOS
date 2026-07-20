"""Tests for pure RawOddsBatch aggregation and duplicate selection rejection."""

import ast
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch
import unittest

import scripts.simulation.providers as providers
from scripts.simulation.providers.errors import ProviderValidationError
from scripts.simulation.providers.models import ProviderContext, RaceEntryUniverse, RawOddsBatch, RawOddsEntry
from scripts.simulation.providers import odds_provider
from scripts.simulation.providers.odds_provider import _build_odds_snapshot_batch, _build_odds_snapshot_entry
from scripts.simulation.repositories.interfaces import OddsSnapshotBatch


NOW = datetime(2026, 1, 2, 12, 0, tzinfo=UTC)


class OddsProviderBatchAggregateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.context = ProviderContext(10, NOW, "fixture", "https://example.test", NOW, NOW)
        self.universe = RaceEntryUniverse(10, {11, 12, 13}, set(), set(), {1: 11, 2: 12, 3: 13})

    def _batch(self, bet_type: str = "単勝", entries=None, complete: bool = True) -> RawOddsBatch:
        defaults = {
            "単勝": (RawOddsEntry((11,), None, "1.2"),),
            "馬連": (RawOddsEntry((11, 12), None, "2.3"),),
            "ワイド": (RawOddsEntry(None, (1, 2), "3.4"),),
            "3連複": (RawOddsEntry(None, (1, 2, 3), "4.5"),),
        }
        return RawOddsBatch(bet_type, defaults[bet_type] if entries is None else entries, complete)

    def test_builds_win_odds_batch(self) -> None:
        self.assertEqual(_build_odds_snapshot_batch(self._batch(), self.context, self.universe).bet_type, "単勝")

    def test_builds_quinella_odds_batch(self) -> None:
        self.assertEqual(_build_odds_snapshot_batch(self._batch("馬連"), self.context, self.universe).entries[0].race_entry_ids, (11, 12))

    def test_builds_wide_odds_batch(self) -> None:
        self.assertEqual(_build_odds_snapshot_batch(self._batch("ワイド"), self.context, self.universe).entries[0].race_entry_ids, (11, 12))

    def test_builds_trio_odds_batch(self) -> None:
        self.assertEqual(_build_odds_snapshot_batch(self._batch("3連複"), self.context, self.universe).entries[0].race_entry_ids, (11, 12, 13))

    def test_returns_repository_boundary_odds_batch(self) -> None:
        self.assertIsInstance(_build_odds_snapshot_batch(self._batch(), self.context, self.universe), OddsSnapshotBatch)

    def test_uses_context_race_id(self) -> None:
        self.assertEqual(_build_odds_snapshot_batch(self._batch(), self.context, self.universe).race_id, 10)

    def test_uses_context_observed_at(self) -> None:
        self.assertEqual(_build_odds_snapshot_batch(self._batch(), self.context, self.universe).observed_at, NOW)

    def test_uses_context_source(self) -> None:
        self.assertEqual(_build_odds_snapshot_batch(self._batch(), self.context, self.universe).source, "fixture")

    def test_uses_raw_bet_type(self) -> None:
        self.assertEqual(_build_odds_snapshot_batch(self._batch("馬連"), self.context, self.universe).bet_type, "馬連")

    def test_reuses_entry_conversion_helper_for_every_entry(self) -> None:
        raw = self._batch("馬連", (RawOddsEntry((11, 12), None, "2.3"), RawOddsEntry((11, 13), None, "3.4")))
        with patch.object(odds_provider, "_build_odds_snapshot_entry", wraps=_build_odds_snapshot_entry) as helper:
            _build_odds_snapshot_batch(raw, self.context, self.universe)
        self.assertEqual(helper.call_count, 2)

    def test_rejects_invalid_raw_type(self) -> None:
        for raw in (None, {}, [], object()):
            with self.subTest(raw=type(raw).__name__), self.assertRaises(ProviderValidationError): _build_odds_snapshot_batch(raw, self.context, self.universe)

    def test_rejects_invalid_context_type(self) -> None:
        for context in (None, {}, object()):
            with self.subTest(context=type(context).__name__), self.assertRaises(ProviderValidationError): _build_odds_snapshot_batch(self._batch(), context, self.universe)

    def test_rejects_invalid_universe_type(self) -> None:
        for universe in (None, {}, object()):
            with self.subTest(universe=type(universe).__name__), self.assertRaises(ProviderValidationError): _build_odds_snapshot_batch(self._batch(), self.context, universe)

    def test_fails_entire_batch_when_one_entry_is_invalid(self) -> None:
        raw = self._batch("馬連", (RawOddsEntry((11, 12), None, "2.3"), RawOddsEntry((11, 99), None, "3.4")))
        with self.assertRaises(ProviderValidationError): _build_odds_snapshot_batch(raw, self.context, self.universe)

    def test_does_not_silently_drop_entries(self) -> None:
        raw = self._batch("馬連", (RawOddsEntry((11, 12), None, "2.3"), RawOddsEntry((11, 13), None, "3.4")))
        self.assertEqual(len(_build_odds_snapshot_batch(raw, self.context, self.universe).entries), 2)

    def test_does_not_add_entries(self) -> None:
        self.assertEqual(len(_build_odds_snapshot_batch(self._batch(), self.context, self.universe).entries), 1)

    def test_detects_duplicate_normalized_selection(self) -> None:
        raw = self._batch("馬連", (RawOddsEntry((12, 11), None, "2.3"), RawOddsEntry((11, 12), None, "3.4")))
        with self.assertRaises(ProviderValidationError): _build_odds_snapshot_batch(raw, self.context, self.universe)

    def test_detects_duplicate_across_race_entry_and_horse_number_sources(self) -> None:
        raw = self._batch("馬連", (RawOddsEntry((12, 11), None, "2.3"), RawOddsEntry(None, (1, 2), "3.4")))
        with self.assertRaises(ProviderValidationError): _build_odds_snapshot_batch(raw, self.context, self.universe)

    def test_duplicate_is_rejected_even_when_odds_differ(self) -> None:
        raw = self._batch("馬連", (RawOddsEntry((11, 12), None, "2.3"), RawOddsEntry((12, 11), None, "99.9")))
        with self.assertRaises(ProviderValidationError): _build_odds_snapshot_batch(raw, self.context, self.universe)

    def test_does_not_silently_deduplicate(self) -> None:
        raw = self._batch("馬連", (RawOddsEntry((11, 12), None, "2.3"), RawOddsEntry((12, 11), None, "2.3")))
        with self.assertRaises(ProviderValidationError): _build_odds_snapshot_batch(raw, self.context, self.universe)

    def test_accepts_distinct_selections(self) -> None:
        raw = self._batch("馬連", (RawOddsEntry((11, 12), None, "2.3"), RawOddsEntry((11, 13), None, "3.4")))
        self.assertEqual(len(_build_odds_snapshot_batch(raw, self.context, self.universe).entries), 2)

    def test_empty_raw_batch_uses_repository_boundary_rule(self) -> None:
        with self.assertRaises(ProviderValidationError): _build_odds_snapshot_batch(self._batch(entries=()), self.context, self.universe)

    def test_entries_are_tuple(self) -> None:
        self.assertIsInstance(_build_odds_snapshot_batch(self._batch(), self.context, self.universe).entries, tuple)

    def test_entry_order_is_canonical_and_deterministic(self) -> None:
        raw = self._batch("馬連", (RawOddsEntry((12, 13), None, "2.3"), RawOddsEntry((11, 13), None, "3.4")))
        entries = _build_odds_snapshot_batch(raw, self.context, self.universe).entries
        self.assertEqual(tuple(entry.race_entry_ids for entry in entries), ((11, 13), (12, 13)))

    def test_declared_complete_does_not_change_aggregation(self) -> None:
        value = _build_odds_snapshot_batch(self._batch(complete=False), self.context, self.universe)
        self.assertFalse(value.is_complete)

    def test_does_not_call_expected_selections(self) -> None:
        self.assertNotIn("expected_selections", _build_odds_snapshot_batch.__code__.co_names)

    def test_does_not_create_completeness_result(self) -> None:
        self.assertFalse(hasattr(_build_odds_snapshot_batch(self._batch(), self.context, self.universe), "completeness"))

    def test_does_not_create_provider_build_result(self) -> None:
        self.assertNotEqual(type(_build_odds_snapshot_batch(self._batch(), self.context, self.universe)).__name__, "ProviderBuildResult")

    def test_converts_boundary_model_errors_to_provider_validation_error(self) -> None:
        with patch("scripts.simulation.providers.odds_provider.OddsSnapshotBatch", side_effect=ValueError("bad model")):
            with self.assertRaises(ProviderValidationError) as caught: _build_odds_snapshot_batch(self._batch(), self.context, self.universe)
        self.assertIsInstance(caught.exception.__cause__, ValueError)

    def test_does_not_mutate_raw(self) -> None:
        raw = self._batch()
        _build_odds_snapshot_batch(raw, self.context, self.universe)
        self.assertEqual(raw, self._batch())

    def test_does_not_mutate_context(self) -> None:
        before = self.context
        _build_odds_snapshot_batch(self._batch(), self.context, self.universe)
        self.assertEqual(self.context, before)

    def test_does_not_mutate_universe(self) -> None:
        before = self.universe
        _build_odds_snapshot_batch(self._batch(), self.context, self.universe)
        self.assertEqual(self.universe, before)

    def test_has_no_database_repository_save_or_network_dependency(self) -> None:
        tree = ast.parse((Path(__file__).parents[1] / "scripts/simulation/providers/odds_provider.py").read_text(encoding="utf-8"))
        imports = {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
        forbidden = ("sqlite3", "requests", "httpx", "urllib", "selenium", "playwright", "scripts.simulation.repositories.sqlite")
        self.assertFalse(any(name.startswith(forbidden) for name in imports))
        self.assertNotIn("save_odds_batch", _build_odds_snapshot_batch.__code__.co_names)

    def test_internal_helper_is_not_exported_from_package_root(self) -> None:
        self.assertFalse(hasattr(providers, "_build_odds_snapshot_batch"))
