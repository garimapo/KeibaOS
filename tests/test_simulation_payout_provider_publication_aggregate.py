"""Tests for RawPayoutPublication aggregation without completeness rules."""

import ast
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
import unittest

import scripts.simulation.providers as providers
from scripts.simulation.providers.errors import ProviderValidationError
from scripts.simulation.providers.models import (
    ProviderContext,
    RaceEntryUniverse,
    RawPayoutPublication,
    RawPayoutRecord,
)
from scripts.simulation.providers.payout_provider import (
    _build_payout_publication,
    _build_payout_record,
)
from scripts.simulation.repositories.interfaces import (
    PayoutPublication,
    PayoutRecord,
    PayoutStatus,
)


NOW = datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc)


class PayoutProviderPublicationAggregateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.universe = RaceEntryUniverse(
            10,
            {11, 12, 13, 16},
            {14},
            {15},
            {1: 11, 2: 12, 3: 13, 4: 14, 5: 15, 6: 16},
        )
        self.context = ProviderContext(10, NOW, "official", "https://example.test", NOW, NOW)

    def _record(
        self,
        ids: tuple[int, ...] | None = (11,),
        horses: tuple[int, ...] | None = None,
        payout: str | int = "1,230",
        status: str = "winning",
    ) -> RawPayoutRecord:
        return RawPayoutRecord(ids, horses, payout, status)

    def _raw(
        self,
        bet_type: str = "単勝",
        entries: tuple[RawPayoutRecord, ...] | None = None,
        complete: bool = True,
    ) -> RawPayoutPublication:
        return RawPayoutPublication(
            bet_type,
            NOW,
            entries if entries is not None else (self._record(),),
            complete,
            True,
            True,
        )

    def test_builds_payout_publication(self) -> None:
        value = _build_payout_publication(self._raw(), self.context, self.universe)
        self.assertEqual(value.race_id, 10)
        self.assertEqual(value.bet_type, "単勝")

    def test_returns_repository_boundary_publication(self) -> None:
        self.assertIsInstance(_build_payout_publication(self._raw(), self.context, self.universe), PayoutPublication)

    def test_converts_all_raw_records(self) -> None:
        raw = self._raw(entries=(self._record((11,), payout=100), self._record((12,), payout=0, status="refund")))
        value = _build_payout_publication(raw, self.context, self.universe)
        self.assertEqual(len(value.entries), 2)
        self.assertEqual({entry.payout_status for entry in value.entries}, {PayoutStatus.WINNING, PayoutStatus.REFUND})

    def test_reuses_record_conversion_helper_for_every_record(self) -> None:
        raw = self._raw(entries=(self._record((11,)), self._record((12,), payout=0, status="refund")))
        with patch("scripts.simulation.providers.payout_provider._build_payout_record", wraps=_build_payout_record) as builder:
            _build_payout_publication(raw, self.context, self.universe)
        self.assertEqual(builder.call_count, 2)
        self.assertEqual(builder.call_args_list[0].args, (raw.entries[0], "単勝", self.universe))
        self.assertEqual(builder.call_args_list[1].args, (raw.entries[1], "単勝", self.universe))

    def test_uses_context_race_id(self) -> None:
        self.assertEqual(_build_payout_publication(self._raw(), self.context, self.universe).race_id, self.context.race_id)

    def test_uses_context_observed_at(self) -> None:
        self.assertEqual(_build_payout_publication(self._raw(), self.context, self.universe).observed_at, self.context.observed_at)

    def test_uses_context_source_and_url(self) -> None:
        value = _build_payout_publication(self._raw(), self.context, self.universe)
        self.assertEqual((value.source, value.source_url), (self.context.source, self.context.source_url))

    def test_uses_raw_finalized_at(self) -> None:
        self.assertEqual(_build_payout_publication(self._raw(), self.context, self.universe).finalized_at, NOW)

    def test_preserves_record_status_and_payout_amount(self) -> None:
        value = _build_payout_publication(
            self._raw(entries=(self._record((11,), payout=100, status="winning"),)),
            self.context,
            self.universe,
        )
        self.assertEqual(value.entries, (PayoutRecord((11,), 100, PayoutStatus.WINNING),))

    def test_rejects_invalid_raw_type(self) -> None:
        for raw in (None, {}, (), object()):
            with self.subTest(raw=type(raw).__name__), self.assertRaises(ProviderValidationError):
                _build_payout_publication(raw, self.context, self.universe)

    def test_rejects_invalid_context_type(self) -> None:
        for context in (None, {}, (), object()):
            with self.subTest(context=type(context).__name__), self.assertRaises(ProviderValidationError):
                _build_payout_publication(self._raw(), context, self.universe)

    def test_rejects_invalid_universe_type(self) -> None:
        for universe in (None, {}, (), object()):
            with self.subTest(universe=type(universe).__name__), self.assertRaises(ProviderValidationError):
                _build_payout_publication(self._raw(), self.context, universe)

    def test_fails_entire_publication_when_one_record_is_invalid(self) -> None:
        raw = self._raw(entries=(self._record((11,)), self._record((14,))))
        with self.assertRaises(ProviderValidationError):
            _build_payout_publication(raw, self.context, self.universe)

    def test_does_not_silently_drop_records(self) -> None:
        raw = self._raw(entries=(self._record((11,)), self._record((12,), payout=0, status="refund")))
        self.assertEqual(len(_build_payout_publication(raw, self.context, self.universe).entries), len(raw.entries))

    def test_does_not_add_records(self) -> None:
        raw = self._raw(entries=(self._record((11,)),))
        self.assertEqual(len(_build_payout_publication(raw, self.context, self.universe).entries), 1)

    def test_detects_duplicate_normalized_bet_type_and_selection(self) -> None:
        raw = self._raw("馬連", (self._record((12, 11)), self._record((11, 12))))
        with self.assertRaises(ProviderValidationError):
            _build_payout_publication(raw, self.context, self.universe)

    def test_detects_duplicate_across_race_entry_and_horse_number_sources(self) -> None:
        raw = self._raw("馬連", (self._record((11, 12)), self._record(None, (1, 2))))
        with self.assertRaises(ProviderValidationError):
            _build_payout_publication(raw, self.context, self.universe)

    def test_duplicate_is_rejected_even_when_payout_differs(self) -> None:
        raw = self._raw("馬連", (self._record((11, 12), payout=100), self._record((12, 11), payout=200)))
        with self.assertRaises(ProviderValidationError):
            _build_payout_publication(raw, self.context, self.universe)

    def test_duplicate_is_rejected_even_when_status_differs(self) -> None:
        raw = self._raw("馬連", (self._record((11, 12), status="winning"), self._record((12, 11), payout=0, status="refund")))
        with self.assertRaises(ProviderValidationError):
            _build_payout_publication(raw, self.context, self.universe)

    def test_does_not_silently_deduplicate(self) -> None:
        raw = self._raw("馬連", (self._record((11, 12)), self._record((12, 11))))
        with self.assertRaises(ProviderValidationError):
            _build_payout_publication(raw, self.context, self.universe)

    def test_allows_different_selections_for_same_bet_type(self) -> None:
        raw = self._raw("馬連", (self._record((11, 12)), self._record((11, 13))))
        self.assertEqual(len(_build_payout_publication(raw, self.context, self.universe).entries), 2)

    def test_allows_multiple_wide_records(self) -> None:
        raw = self._raw("ワイド", (self._record((11, 12)), self._record((11, 13))))
        self.assertEqual(len(_build_payout_publication(raw, self.context, self.universe).entries), 2)

    def test_empty_publication_follows_repository_boundary_rule(self) -> None:
        value = _build_payout_publication(self._raw(entries=()), self.context, self.universe)
        self.assertEqual(value.entries, ())

    def test_records_are_tuple(self) -> None:
        self.assertIsInstance(_build_payout_publication(self._raw(), self.context, self.universe).entries, tuple)

    def test_record_order_is_canonical_and_deterministic(self) -> None:
        raw = self._raw("馬連", (self._record((12, 13)), self._record((11, 12))))
        value = _build_payout_publication(raw, self.context, self.universe)
        self.assertEqual(tuple(entry.race_entry_ids for entry in value.entries), ((11, 12), (12, 13)))

    def test_does_not_reparse_payout_amount(self) -> None:
        self.assertNotIn("parse_payout_per_100", _build_payout_publication.__code__.co_names)

    def test_does_not_renormalize_payout_status(self) -> None:
        self.assertNotIn("normalize_payout_status", _build_payout_publication.__code__.co_names)

    def test_does_not_create_completeness_result(self) -> None:
        value = _build_payout_publication(self._raw(), self.context, self.universe)
        self.assertFalse(hasattr(value, "completeness"))

    def test_does_not_create_provider_build_result(self) -> None:
        value = _build_payout_publication(self._raw(), self.context, self.universe)
        self.assertNotEqual(type(value).__name__, "ProviderBuildResult")

    def test_does_not_calculate_simulation_return(self) -> None:
        self.assertNotIn("return_rate", _build_payout_publication.__code__.co_names)

    def test_converts_publication_model_errors_to_provider_validation_error(self) -> None:
        with patch("scripts.simulation.providers.payout_provider.PayoutPublication", side_effect=ValueError("bad model")):
            with self.assertRaises(ProviderValidationError) as caught:
                _build_payout_publication(self._raw(), self.context, self.universe)
        self.assertIsInstance(caught.exception.__cause__, ValueError)

    def test_does_not_mutate_raw(self) -> None:
        raw = self._raw()
        _build_payout_publication(raw, self.context, self.universe)
        self.assertEqual(raw, self._raw())

    def test_does_not_mutate_context(self) -> None:
        before = self.context
        _build_payout_publication(self._raw(), self.context, self.universe)
        self.assertEqual(self.context, before)

    def test_does_not_mutate_universe(self) -> None:
        before = self.universe
        _build_payout_publication(self._raw(), self.context, self.universe)
        self.assertEqual(self.universe, before)

    def test_has_no_database_repository_save_or_network_dependency(self) -> None:
        tree = ast.parse((Path(__file__).parents[1] / "scripts/simulation/providers/payout_provider.py").read_text(encoding="utf-8"))
        imports = {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
        forbidden = ("sqlite3", "requests", "httpx", "urllib", "selenium", "playwright", "scripts.simulation.repositories.sqlite")
        self.assertFalse(any(name.startswith(forbidden) for name in imports))
        self.assertNotIn("save_payout_publication", _build_payout_publication.__code__.co_names)

    def test_internal_helper_is_not_exported_from_package_root(self) -> None:
        self.assertFalse(hasattr(providers, "_build_payout_publication"))
