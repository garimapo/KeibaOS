"""Tests for one-row RawPayoutRecord conversion."""

import ast
from pathlib import Path
from unittest.mock import patch
import unittest

import scripts.simulation.providers as providers
from scripts.simulation.providers.errors import ProviderValidationError
from scripts.simulation.providers.models import RaceEntryUniverse, RawPayoutRecord
from scripts.simulation.providers.normalization import (
    normalize_payout_status,
    parse_payout_per_100,
    resolve_selection,
)
from scripts.simulation.providers.payout_provider import _build_payout_record
from scripts.simulation.repositories.interfaces import PayoutRecord, PayoutStatus


class PayoutProviderRecordConversionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.universe = RaceEntryUniverse(
            10,
            {11, 12, 13},
            {14},
            {15},
            {1: 11, 2: 12, 3: 13, 4: 14, 5: 15},
        )

    def _raw_ids(
        self,
        values: tuple[int, ...] = (11,),
        payout: str | int = "1,230",
        status: str = "winning",
    ) -> RawPayoutRecord:
        return RawPayoutRecord(values, None, payout, status)

    def _raw_horses(
        self,
        values: tuple[int, ...] = (1,),
        payout: str | int = "1,230",
        status: str = "winning",
    ) -> RawPayoutRecord:
        return RawPayoutRecord(None, values, payout, status)

    def test_builds_win_payout_record_from_race_entry_ids(self) -> None:
        value = _build_payout_record(self._raw_ids((11,)), "単勝", self.universe)
        self.assertEqual(value.race_entry_ids, (11,))
        self.assertEqual(value.payout_status, PayoutStatus.WINNING)

    def test_builds_quinella_payout_record_from_race_entry_ids(self) -> None:
        value = _build_payout_record(self._raw_ids((12, 11)), "馬連", self.universe)
        self.assertEqual(value.race_entry_ids, (11, 12))

    def test_builds_wide_payout_record_from_horse_numbers(self) -> None:
        value = _build_payout_record(self._raw_horses((2, 1)), "ワイド", self.universe)
        self.assertEqual(value.race_entry_ids, (11, 12))

    def test_builds_trio_payout_record_from_horse_numbers(self) -> None:
        value = _build_payout_record(self._raw_horses((3, 1, 2)), "3連複", self.universe)
        self.assertEqual(value.race_entry_ids, (11, 12, 13))

    def test_returns_repository_boundary_payout_record(self) -> None:
        self.assertIsInstance(_build_payout_record(self._raw_ids(), "単勝", self.universe), PayoutRecord)

    def test_selection_is_sorted_and_canonical(self) -> None:
        value = _build_payout_record(self._raw_ids((13, 11, 12)), "3連複", self.universe)
        self.assertEqual(value.race_entry_ids, (11, 12, 13))

    def test_payout_amount_uses_repository_required_type(self) -> None:
        value = _build_payout_record(self._raw_ids(payout="1,230"), "単勝", self.universe)
        self.assertIsInstance(value.payout_per_100, int)

    def test_preserves_valid_payout_integer_value(self) -> None:
        value = _build_payout_record(self._raw_ids(payout=1230), "単勝", self.universe)
        self.assertEqual(value.payout_per_100, 1230)

    def test_reuses_existing_selection_resolver(self) -> None:
        with patch("scripts.simulation.providers.payout_provider.resolve_selection", wraps=resolve_selection) as resolver:
            _build_payout_record(self._raw_ids(), "単勝", self.universe)
        resolver.assert_called_once_with((11,), None, "単勝", self.universe)

    def test_reuses_existing_payout_amount_parser(self) -> None:
        with patch("scripts.simulation.providers.payout_provider.parse_payout_per_100", wraps=parse_payout_per_100) as parser:
            _build_payout_record(self._raw_ids(payout="1,230"), "単勝", self.universe)
        parser.assert_called_once_with("1,230")

    def test_reuses_existing_payout_status_normalizer(self) -> None:
        with patch("scripts.simulation.providers.payout_provider.normalize_payout_status", wraps=normalize_payout_status) as normalizer:
            _build_payout_record(self._raw_ids(status="winning"), "単勝", self.universe)
        normalizer.assert_called_once_with("winning")

    def test_rejects_invalid_raw_type(self) -> None:
        for raw in (None, {}, (), object()):
            with self.subTest(raw=type(raw).__name__), self.assertRaises(ProviderValidationError):
                _build_payout_record(raw, "単勝", self.universe)

    def test_rejects_invalid_universe_type(self) -> None:
        for universe in (None, {}, (), object()):
            with self.subTest(universe=type(universe).__name__), self.assertRaises(ProviderValidationError):
                _build_payout_record(self._raw_ids(), "単勝", universe)

    def test_rejects_unsupported_bet_type(self) -> None:
        for bet_type in (None, True, "", "unsupported"):
            with self.subTest(bet_type=repr(bet_type)), self.assertRaises(ProviderValidationError):
                _build_payout_record(self._raw_ids(), bet_type, self.universe)

    def test_rejects_both_selection_sources_at_raw_boundary(self) -> None:
        with self.assertRaises(ProviderValidationError):
            RawPayoutRecord((11,), (1,), "1,230", "winning")

    def test_rejects_missing_selection_sources_at_raw_boundary(self) -> None:
        with self.assertRaises(ProviderValidationError):
            RawPayoutRecord(None, None, "1,230", "winning")

    def test_rejects_unknown_entry(self) -> None:
        with self.assertRaises(ProviderValidationError):
            _build_payout_record(self._raw_ids((99,)), "単勝", self.universe)

    def test_rejects_excluded_entry(self) -> None:
        with self.assertRaises(ProviderValidationError):
            _build_payout_record(self._raw_ids((14,)), "単勝", self.universe)

    def test_rejects_cancelled_entry(self) -> None:
        with self.assertRaises(ProviderValidationError):
            _build_payout_record(self._raw_ids((15,)), "単勝", self.universe)

    def test_rejects_wrong_selection_count(self) -> None:
        with self.assertRaises(ProviderValidationError):
            _build_payout_record(self._raw_ids((11, 12)), "単勝", self.universe)

    def test_rejects_duplicate_selection_ids_at_raw_boundary(self) -> None:
        with self.assertRaises(ProviderValidationError):
            RawPayoutRecord((11, 11), None, "1,230", "winning")

    def test_rejects_invalid_payout_text(self) -> None:
        for value in ("", "-", "1,2", "1E2"):
            with self.subTest(value=value), self.assertRaises(ProviderValidationError):
                _build_payout_record(self._raw_ids(payout=value), "単勝", self.universe)

    def test_rejects_negative_payout(self) -> None:
        with self.assertRaises(ProviderValidationError):
            _build_payout_record(self._raw_ids(payout="-1"), "単勝", self.universe)

    def test_zero_payout_follows_boundary_contract(self) -> None:
        value = _build_payout_record(self._raw_ids(payout=0, status="refund"), "単勝", self.universe)
        self.assertEqual(value.payout_per_100, 0)
        self.assertEqual(value.payout_status, PayoutStatus.REFUND)

    def test_rejects_nonfinite_or_float_payout(self) -> None:
        for value in (1.0, float("inf"), float("nan")):
            with self.subTest(value=repr(value)), self.assertRaises(ProviderValidationError):
                _build_payout_record(self._raw_ids(payout=value), "単勝", self.universe)

    def test_converts_boundary_model_errors_to_provider_validation_error(self) -> None:
        with patch("scripts.simulation.providers.payout_provider.PayoutRecord", side_effect=ValueError("bad model")):
            with self.assertRaises(ProviderValidationError) as caught:
                _build_payout_record(self._raw_ids(), "単勝", self.universe)
        self.assertIsInstance(caught.exception.__cause__, ValueError)

    def test_does_not_mutate_raw_record(self) -> None:
        raw = self._raw_ids((11,))
        _build_payout_record(raw, "単勝", self.universe)
        self.assertEqual(raw, self._raw_ids((11,)))

    def test_does_not_mutate_universe(self) -> None:
        before = self.universe
        _build_payout_record(self._raw_ids(), "単勝", self.universe)
        self.assertEqual(self.universe, before)

    def test_does_not_detect_duplicate_publication_records(self) -> None:
        self.assertNotIn("duplicate", _build_payout_record.__code__.co_names)

    def test_does_not_create_completeness_result(self) -> None:
        value = _build_payout_record(self._raw_ids(), "単勝", self.universe)
        self.assertFalse(hasattr(value, "completeness"))

    def test_does_not_create_provider_build_result(self) -> None:
        value = _build_payout_record(self._raw_ids(), "単勝", self.universe)
        self.assertNotEqual(type(value).__name__, "ProviderBuildResult")

    def test_does_not_calculate_simulation_return(self) -> None:
        self.assertNotIn("return_rate", _build_payout_record.__code__.co_names)

    def test_has_no_database_repository_save_or_network_dependency(self) -> None:
        tree = ast.parse((Path(__file__).parents[1] / "scripts/simulation/providers/payout_provider.py").read_text(encoding="utf-8"))
        imports = {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
        forbidden = ("sqlite3", "requests", "httpx", "urllib", "selenium", "playwright", "scripts.simulation.repositories.sqlite")
        self.assertFalse(any(name.startswith(forbidden) for name in imports))
        self.assertNotIn("save_payout_publication", _build_payout_record.__code__.co_names)

    def test_internal_helper_is_not_exported_from_package_root(self) -> None:
        self.assertFalse(hasattr(providers, "_build_payout_record"))
