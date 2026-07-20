"""Tests for immutable payout publication status facts only."""

import ast
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from pathlib import Path
import unittest

import scripts.simulation.providers as providers
from scripts.simulation.providers.errors import ProviderValidationError
from scripts.simulation.providers.payout_provider import (
    _PayoutPublicationStatusFacts,
    _analyze_payout_publication_status_facts,
)
from scripts.simulation.repositories.interfaces import (
    PayoutPublication,
    PayoutRecord,
    PayoutStatus,
)


NOW = datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc)


class PayoutProviderStatusFactsTest(unittest.TestCase):
    def _publication(
        self,
        entries: tuple[PayoutRecord, ...],
        complete: bool = True,
    ) -> PayoutPublication:
        return PayoutPublication(10, "単勝", NOW, NOW, complete, "official", entries)

    def _record(self, entry_id: int, status: PayoutStatus, payout: int | None = None) -> PayoutRecord:
        if payout is None:
            payout = 100 if status is PayoutStatus.WINNING else 0
        return PayoutRecord((entry_id,), payout, status)

    def _facts(self, entries: tuple[PayoutRecord, ...], complete: bool = True) -> _PayoutPublicationStatusFacts:
        return _analyze_payout_publication_status_facts(self._publication(entries, complete))

    def test_analyzes_winning_record(self) -> None:
        self.assertEqual(self._facts((self._record(11, PayoutStatus.WINNING),)).winning_selections, ((11,),))

    def test_analyzes_refund_record(self) -> None:
        self.assertEqual(self._facts((self._record(11, PayoutStatus.REFUND),)).refund_selections, ((11,),))

    def test_analyzes_void_record(self) -> None:
        self.assertEqual(self._facts((self._record(11, PayoutStatus.VOID),)).void_selections, ((11,),))

    def test_analyzes_unsupported_record(self) -> None:
        self.assertEqual(self._facts((self._record(11, PayoutStatus.UNSUPPORTED),)).unsupported_selections, ((11,),))

    def test_analyzes_multiple_winning_records(self) -> None:
        self.assertEqual(self._facts((self._record(13, PayoutStatus.WINNING), self._record(11, PayoutStatus.WINNING))).winning_selections, ((11,), (13,)))

    def test_analyzes_mixed_winning_refund_and_void_records(self) -> None:
        facts = self._facts((self._record(11, PayoutStatus.WINNING), self._record(12, PayoutStatus.REFUND), self._record(13, PayoutStatus.VOID)))
        self.assertEqual((facts.winning_selections, facts.refund_selections, facts.void_selections), (((11,),), ((12,),), ((13,),)))

    def test_allows_supported_and_unsupported_statuses_together(self) -> None:
        facts = self._facts((self._record(11, PayoutStatus.WINNING), self._record(12, PayoutStatus.UNSUPPORTED)))
        self.assertEqual(facts.unsupported_selections, ((12,),))

    def test_observed_contains_all_record_selections(self) -> None:
        self.assertEqual(self._facts((self._record(13, PayoutStatus.VOID), self._record(11, PayoutStatus.WINNING))).observed_selections, ((11,), (13,)))

    def test_status_partitions_are_disjoint(self) -> None:
        facts = self._facts((self._record(11, PayoutStatus.WINNING), self._record(12, PayoutStatus.REFUND), self._record(13, PayoutStatus.VOID)))
        groups = (set(facts.winning_selections), set(facts.refund_selections), set(facts.void_selections), set(facts.unsupported_selections))
        self.assertFalse(any(left & right for index, left in enumerate(groups) for right in groups[index + 1 :]))

    def test_status_partitions_union_equals_observed(self) -> None:
        facts = self._facts((self._record(11, PayoutStatus.WINNING), self._record(12, PayoutStatus.REFUND), self._record(13, PayoutStatus.VOID), self._record(14, PayoutStatus.UNSUPPORTED)))
        union = set().union(facts.winning_selections, facts.refund_selections, facts.void_selections, facts.unsupported_selections)
        self.assertEqual(union, set(facts.observed_selections))

    def test_outputs_are_nested_tuples(self) -> None:
        facts = self._facts((self._record(11, PayoutStatus.WINNING),))
        self.assertIsInstance(facts.observed_selections, tuple)
        self.assertIsInstance(facts.observed_selections[0], tuple)

    def test_outputs_are_sorted_and_deterministic(self) -> None:
        first = self._facts((self._record(13, PayoutStatus.WINNING), self._record(11, PayoutStatus.WINNING)))
        second = self._facts((self._record(11, PayoutStatus.WINNING), self._record(13, PayoutStatus.WINNING)))
        self.assertEqual(first, second)

    def test_counts_match_partition_lengths(self) -> None:
        facts = self._facts((self._record(11, PayoutStatus.WINNING), self._record(12, PayoutStatus.REFUND), self._record(13, PayoutStatus.VOID), self._record(14, PayoutStatus.UNSUPPORTED)))
        self.assertEqual((facts.observed_count, facts.winning_count, facts.refund_count, facts.void_count, facts.unsupported_count), (4, 1, 1, 1, 1))

    def test_has_records_property(self) -> None:
        self.assertTrue(self._facts((self._record(11, PayoutStatus.WINNING),)).has_records)

    def test_has_unsupported_property(self) -> None:
        self.assertTrue(self._facts((self._record(11, PayoutStatus.UNSUPPORTED),)).has_unsupported)

    def test_empty_publication_has_empty_facts(self) -> None:
        facts = self._facts(())
        self.assertEqual((facts.observed_selections, facts.winning_selections, facts.refund_selections, facts.void_selections, facts.unsupported_selections), ((), (), (), (), ()))
        self.assertFalse(facts.has_records)
        self.assertFalse(facts.has_unsupported)

    def test_complete_flag_does_not_change_status_facts(self) -> None:
        entries = (self._record(11, PayoutStatus.WINNING),)
        self.assertEqual(self._facts(entries, True), self._facts(entries, False))

    def test_does_not_include_payout_amount_in_selection_identity(self) -> None:
        first = self._facts((self._record(11, PayoutStatus.WINNING, 100),))
        second = self._facts((self._record(11, PayoutStatus.WINNING, 200),))
        self.assertEqual(first, second)

    def test_does_not_include_bet_type_in_selection_identity(self) -> None:
        entry = self._record(11, PayoutStatus.WINNING)
        single = self._publication((entry,))
        facts = _analyze_payout_publication_status_facts(single)
        self.assertEqual(facts.observed_selections, ((11,),))

    def test_does_not_call_expected_selections(self) -> None:
        self.assertNotIn("expected_selections", _analyze_payout_publication_status_facts.__code__.co_names)

    def test_does_not_reparse_payout_status(self) -> None:
        self.assertNotIn("normalize_payout_status", _analyze_payout_publication_status_facts.__code__.co_names)

    def test_does_not_revalidate_payout_amount(self) -> None:
        self.assertNotIn("parse_payout_per_100", _analyze_payout_publication_status_facts.__code__.co_names)

    def test_returns_internal_status_facts_model(self) -> None:
        self.assertIsInstance(self._facts((self._record(11, PayoutStatus.WINNING),)), _PayoutPublicationStatusFacts)

    def test_status_facts_model_is_frozen(self) -> None:
        facts = self._facts((self._record(11, PayoutStatus.WINNING),))
        with self.assertRaises(FrozenInstanceError):
            facts.observed_selections = ()

    def test_status_facts_rejects_non_tuple_collections(self) -> None:
        with self.assertRaises(ProviderValidationError):
            _PayoutPublicationStatusFacts([(11,)], ((11,),), (), (), ())

    def test_status_facts_rejects_noncanonical_or_duplicate_selections(self) -> None:
        for values in (((12, 11),), ((11, 11),), ((0,),), ((11,), (11,))):
            with self.subTest(values=values), self.assertRaises(ProviderValidationError):
                _PayoutPublicationStatusFacts(values, values, (), (), ())

    def test_status_facts_rejects_overlapping_status_partitions(self) -> None:
        with self.assertRaises(ProviderValidationError):
            _PayoutPublicationStatusFacts(((11,),), ((11,),), ((11,),), (), ())

    def test_status_facts_rejects_partition_union_mismatch(self) -> None:
        with self.assertRaises(ProviderValidationError):
            _PayoutPublicationStatusFacts(((11,),), (), (), (), ())

    def test_status_facts_rejects_partition_selection_not_observed(self) -> None:
        with self.assertRaises(ProviderValidationError):
            _PayoutPublicationStatusFacts(((11,),), ((12,),), (), (), ())

    def test_rejects_invalid_publication_type(self) -> None:
        for publication in (None, {}, (), object()):
            with self.subTest(publication=type(publication).__name__), self.assertRaises(ProviderValidationError):
                _analyze_payout_publication_status_facts(publication)

    def test_does_not_mutate_publication(self) -> None:
        publication = self._publication((self._record(11, PayoutStatus.WINNING),))
        _analyze_payout_publication_status_facts(publication)
        self.assertEqual(publication, self._publication((self._record(11, PayoutStatus.WINNING),)))

    def test_does_not_create_completeness_result(self) -> None:
        self.assertFalse(hasattr(self._facts((self._record(11, PayoutStatus.WINNING),)), "completeness"))

    def test_does_not_create_provider_build_result(self) -> None:
        self.assertNotEqual(type(self._facts((self._record(11, PayoutStatus.WINNING),))).__name__, "ProviderBuildResult")

    def test_does_not_calculate_simulation_return(self) -> None:
        self.assertNotIn("return_rate", _analyze_payout_publication_status_facts.__code__.co_names)

    def test_has_no_database_repository_save_or_network_dependency(self) -> None:
        tree = ast.parse((Path(__file__).parents[1] / "scripts/simulation/providers/payout_provider.py").read_text(encoding="utf-8"))
        imports = {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
        forbidden = ("sqlite3", "requests", "httpx", "urllib", "selenium", "playwright", "scripts.simulation.repositories.sqlite")
        self.assertFalse(any(name.startswith(forbidden) for name in imports))
        self.assertNotIn("save_payout_publication", _analyze_payout_publication_status_facts.__code__.co_names)

    def test_internal_model_and_helper_are_not_exported_from_package_root(self) -> None:
        self.assertFalse(hasattr(providers, "_PayoutPublicationStatusFacts"))
        self.assertFalse(hasattr(providers, "_analyze_payout_publication_status_facts"))
