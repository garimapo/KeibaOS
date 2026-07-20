"""Tests for one-row RawOddsEntry conversion."""

import ast
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
import unittest

import scripts.simulation.providers as providers
from scripts.simulation.providers.errors import ProviderValidationError
from scripts.simulation.providers.models import RaceEntryUniverse, RawOddsEntry
from scripts.simulation.providers.normalization import parse_decimal_odds, resolve_selection
from scripts.simulation.providers.odds_provider import _build_odds_snapshot_entry
from scripts.simulation.repositories.interfaces import OddsSnapshotEntry


class OddsProviderEntryConversionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.universe = RaceEntryUniverse(
            10,
            {11, 12, 13},
            {14},
            {15},
            {1: 11, 2: 12, 3: 13, 4: 14, 5: 15},
        )

    def _raw_ids(self, values=(11,), odds: str | Decimal = "1.2300") -> RawOddsEntry:
        return RawOddsEntry(values, None, odds)

    def _raw_horses(self, values=(1,), odds: str | Decimal = "1.2300") -> RawOddsEntry:
        return RawOddsEntry(None, values, odds)

    def test_builds_win_entry_from_race_entry_ids(self) -> None:
        value = _build_odds_snapshot_entry(self._raw_ids((11,)), "単勝", self.universe)
        self.assertEqual(value.race_entry_ids, (11,))

    def test_builds_quinella_entry_from_race_entry_ids(self) -> None:
        value = _build_odds_snapshot_entry(self._raw_ids((12, 11)), "馬連", self.universe)
        self.assertEqual(value.race_entry_ids, (11, 12))

    def test_builds_wide_entry_from_horse_numbers(self) -> None:
        value = _build_odds_snapshot_entry(self._raw_horses((2, 1)), "ワイド", self.universe)
        self.assertEqual(value.race_entry_ids, (11, 12))

    def test_builds_trio_entry_from_horse_numbers(self) -> None:
        value = _build_odds_snapshot_entry(self._raw_horses((3, 1, 2)), "3連複", self.universe)
        self.assertEqual(value.race_entry_ids, (11, 12, 13))

    def test_returns_repository_boundary_odds_entry(self) -> None:
        self.assertIsInstance(_build_odds_snapshot_entry(self._raw_ids(), "単勝", self.universe), OddsSnapshotEntry)

    def test_selection_is_sorted_and_canonical(self) -> None:
        value = _build_odds_snapshot_entry(self._raw_ids((13, 11, 12)), "3連複", self.universe)
        self.assertEqual(value.race_entry_ids, (11, 12, 13))

    def test_odds_is_decimal(self) -> None:
        self.assertIsInstance(_build_odds_snapshot_entry(self._raw_ids(), "単勝", self.universe).odds, Decimal)

    def test_preserves_decimal_trailing_zero_precision(self) -> None:
        value = _build_odds_snapshot_entry(self._raw_ids(odds=Decimal("1.2300")), "単勝", self.universe)
        self.assertEqual(value.odds.as_tuple(), Decimal("1.2300").as_tuple())

    def test_reuses_resolve_selection(self) -> None:
        with patch("scripts.simulation.providers.odds_provider.resolve_selection", wraps=resolve_selection) as resolver:
            _build_odds_snapshot_entry(self._raw_ids(), "単勝", self.universe)
        resolver.assert_called_once_with((11,), None, "単勝", self.universe)

    def test_reuses_parse_decimal_odds(self) -> None:
        with patch("scripts.simulation.providers.odds_provider.parse_decimal_odds", wraps=parse_decimal_odds) as parser:
            _build_odds_snapshot_entry(self._raw_ids(odds="1.2300"), "単勝", self.universe)
        parser.assert_called_once_with("1.2300")

    def test_rejects_invalid_raw_type(self) -> None:
        for raw in (None, {}, (), object()):
            with self.subTest(raw=type(raw).__name__), self.assertRaises(ProviderValidationError):
                _build_odds_snapshot_entry(raw, "単勝", self.universe)

    def test_rejects_invalid_universe_type(self) -> None:
        for universe in (None, {}, (), object()):
            with self.subTest(universe=type(universe).__name__), self.assertRaises(ProviderValidationError):
                _build_odds_snapshot_entry(self._raw_ids(), "単勝", universe)

    def test_rejects_unsupported_bet_type(self) -> None:
        for bet_type in (None, True, "", "unsupported"):
            with self.subTest(bet_type=repr(bet_type)), self.assertRaises(ProviderValidationError):
                _build_odds_snapshot_entry(self._raw_ids(), bet_type, self.universe)

    def test_rejects_both_selection_sources_at_raw_boundary(self) -> None:
        with self.assertRaises(ProviderValidationError):
            RawOddsEntry((11,), (1,), "1.2")

    def test_rejects_missing_selection_sources_at_raw_boundary(self) -> None:
        with self.assertRaises(ProviderValidationError):
            RawOddsEntry(None, None, "1.2")

    def test_rejects_active_external_entry(self) -> None:
        with self.assertRaises(ProviderValidationError):
            _build_odds_snapshot_entry(self._raw_ids((99,)), "単勝", self.universe)

    def test_rejects_excluded_entry(self) -> None:
        with self.assertRaises(ProviderValidationError):
            _build_odds_snapshot_entry(self._raw_ids((14,)), "単勝", self.universe)

    def test_rejects_cancelled_entry(self) -> None:
        with self.assertRaises(ProviderValidationError):
            _build_odds_snapshot_entry(self._raw_ids((15,)), "単勝", self.universe)

    def test_rejects_wrong_selection_count(self) -> None:
        with self.assertRaises(ProviderValidationError):
            _build_odds_snapshot_entry(self._raw_ids((11, 12)), "単勝", self.universe)

    def test_rejects_duplicate_selection_ids_at_raw_boundary(self) -> None:
        with self.assertRaises(ProviderValidationError):
            RawOddsEntry((11, 11), None, "1.2")

    def test_rejects_invalid_odds_text(self) -> None:
        for value in ("", "-", "発売なし", "1,2", "1E2"):
            with self.subTest(value=value), self.assertRaises(ProviderValidationError):
                _build_odds_snapshot_entry(self._raw_ids(odds=value), "単勝", self.universe)

    def test_rejects_zero_and_negative_odds(self) -> None:
        for value in ("0", "-1"):
            with self.subTest(value=value), self.assertRaises(ProviderValidationError):
                _build_odds_snapshot_entry(self._raw_ids(odds=value), "単勝", self.universe)

    def test_rejects_nonfinite_odds(self) -> None:
        for value in (Decimal("NaN"), Decimal("Infinity")):
            with self.subTest(value=str(value)), self.assertRaises(ProviderValidationError):
                _build_odds_snapshot_entry(self._raw_ids(odds=value), "単勝", self.universe)

    def test_converts_boundary_model_errors_to_provider_validation_error(self) -> None:
        with patch("scripts.simulation.providers.odds_provider.OddsSnapshotEntry", side_effect=ValueError("bad model")):
            with self.assertRaises(ProviderValidationError) as caught:
                _build_odds_snapshot_entry(self._raw_ids(), "単勝", self.universe)
        self.assertIsInstance(caught.exception.__cause__, ValueError)

    def test_does_not_mutate_raw_entry(self) -> None:
        raw = self._raw_ids((11,))
        _build_odds_snapshot_entry(raw, "単勝", self.universe)
        self.assertEqual(raw, self._raw_ids((11,)))

    def test_does_not_mutate_universe(self) -> None:
        before = self.universe
        _build_odds_snapshot_entry(self._raw_ids(), "単勝", self.universe)
        self.assertEqual(self.universe, before)

    def test_does_not_create_completeness_result(self) -> None:
        value = _build_odds_snapshot_entry(self._raw_ids(), "単勝", self.universe)
        self.assertFalse(hasattr(value, "completeness"))

    def test_does_not_create_provider_build_result(self) -> None:
        self.assertNotEqual(type(_build_odds_snapshot_entry(self._raw_ids(), "単勝", self.universe)).__name__, "ProviderBuildResult")

    def test_does_not_detect_duplicate_rows(self) -> None:
        self.assertNotIn("duplicate", _build_odds_snapshot_entry.__code__.co_names)

    def test_has_no_database_repository_save_or_network_dependency(self) -> None:
        tree = ast.parse((Path(__file__).parents[1] / "scripts/simulation/providers/odds_provider.py").read_text(encoding="utf-8"))
        imports = {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
        forbidden = ("sqlite3", "requests", "httpx", "urllib", "selenium", "playwright", "scripts.simulation.repositories.sqlite")
        self.assertFalse(any(name.startswith(forbidden) for name in imports))
        self.assertNotIn("save_odds_batch", _build_odds_snapshot_entry.__code__.co_names)

    def test_internal_helper_is_not_exported_from_package_root(self) -> None:
        self.assertFalse(hasattr(providers, "_build_odds_snapshot_entry"))
