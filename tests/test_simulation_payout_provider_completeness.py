"""Tests for payout completeness derived from immutable status facts."""

import ast
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
import unittest

import scripts.simulation.providers as providers
from scripts.simulation.providers.errors import ProviderValidationError
from scripts.simulation.providers.models import CompletenessResult, CompletenessStatus
from scripts.simulation.providers.payout_provider import (
    _PayoutPublicationStatusFacts,
    _analyze_payout_publication_status_facts,
    _build_payout_completeness,
)
from scripts.simulation.repositories.interfaces import (
    PayoutPublication,
    PayoutRecord,
    PayoutStatus,
)


NOW = datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc)


class PayoutProviderCompletenessTest(unittest.TestCase):
    def _publication(
        self,
        entries: tuple[PayoutRecord, ...] = (),
        complete: bool = True,
    ) -> PayoutPublication:
        return PayoutPublication(10, "単勝", NOW, NOW, complete, "official", entries)

    def _record(self, entry_id: int, status: PayoutStatus, payout: int | None = None) -> PayoutRecord:
        if payout is None:
            payout = 100 if status is PayoutStatus.WINNING else 0
        return PayoutRecord((entry_id,), payout, status)

    def _facts(self, publication: PayoutPublication) -> _PayoutPublicationStatusFacts:
        return _analyze_payout_publication_status_facts(publication)

    def _build(self, entries: tuple[PayoutRecord, ...] = (), complete: bool = True) -> CompletenessResult:
        publication = self._publication(entries, complete)
        return _build_payout_completeness(publication, self._facts(publication))

    def test_complete_supported_publication_is_complete(self) -> None:
        result = self._build((self._record(11, PayoutStatus.WINNING),), True)
        self.assertEqual(result.status, CompletenessStatus.COMPLETE)

    def test_incomplete_supported_publication_is_incomplete(self) -> None:
        result = self._build((self._record(11, PayoutStatus.WINNING),), False)
        self.assertEqual(result.status, CompletenessStatus.INCOMPLETE)

    def test_complete_unsupported_publication_is_unsupported(self) -> None:
        result = self._build((self._record(11, PayoutStatus.UNSUPPORTED),), True)
        self.assertEqual(result.status, CompletenessStatus.UNSUPPORTED)

    def test_incomplete_unsupported_publication_is_unsupported(self) -> None:
        result = self._build((self._record(11, PayoutStatus.UNSUPPORTED),), False)
        self.assertEqual(result.status, CompletenessStatus.UNSUPPORTED)

    def test_unsupported_has_priority_over_incomplete(self) -> None:
        self.assertEqual(self._build((self._record(11, PayoutStatus.UNSUPPORTED),), False).status, CompletenessStatus.UNSUPPORTED)

    def test_incomplete_has_priority_over_complete(self) -> None:
        self.assertEqual(self._build((self._record(11, PayoutStatus.REFUND),), False).status, CompletenessStatus.INCOMPLETE)

    def test_does_not_generate_invalid_status(self) -> None:
        for entries, complete in (((self._record(11, PayoutStatus.WINNING),), True), ((self._record(11, PayoutStatus.REFUND),), False), ((self._record(11, PayoutStatus.UNSUPPORTED),), True)):
            with self.subTest(complete=complete, status=entries[0].payout_status):
                self.assertNotEqual(self._build(entries, complete).status, CompletenessStatus.INVALID)

    def test_expected_and_actual_counts_equal_observed_count(self) -> None:
        result = self._build((self._record(11, PayoutStatus.WINNING), self._record(12, PayoutStatus.REFUND), self._record(13, PayoutStatus.VOID)))
        self.assertEqual((result.expected_count, result.actual_count), (3, 3))

    def test_counts_include_unsupported_records(self) -> None:
        result = self._build((self._record(11, PayoutStatus.WINNING), self._record(12, PayoutStatus.UNSUPPORTED)))
        self.assertEqual((result.expected_count, result.actual_count), (2, 2))

    def test_complete_has_empty_reasons(self) -> None:
        self.assertEqual(self._build((self._record(11, PayoutStatus.WINNING),), True).reasons, ())

    def test_incomplete_reason_is_added(self) -> None:
        self.assertEqual(self._build((self._record(11, PayoutStatus.WINNING),), False).reasons, ("payout_not_declared_complete",))

    def test_unsupported_reason_is_added(self) -> None:
        self.assertEqual(self._build((self._record(11, PayoutStatus.UNSUPPORTED),), True).reasons, ("unsupported_payout_records",))

    def test_unsupported_and_incomplete_preserve_both_reasons(self) -> None:
        result = self._build((self._record(11, PayoutStatus.UNSUPPORTED),), False)
        self.assertEqual(set(result.reasons), {"unsupported_payout_records", "payout_not_declared_complete"})

    def test_reasons_are_unique_and_deterministic(self) -> None:
        first = self._build((self._record(11, PayoutStatus.UNSUPPORTED),), False)
        second = self._build((self._record(11, PayoutStatus.UNSUPPORTED),), False)
        self.assertEqual(first.reasons, second.reasons)
        self.assertEqual(len(first.reasons), len(set(first.reasons)))

    def test_discrepancy_keys_are_empty(self) -> None:
        result = self._build((self._record(11, PayoutStatus.UNSUPPORTED),), False)
        self.assertEqual((result.missing_keys, result.unexpected_keys, result.duplicate_keys), ((), (), ()))

    def test_unsupported_selections_are_not_discrepancy_keys(self) -> None:
        result = self._build((self._record(11, PayoutStatus.UNSUPPORTED),), True)
        self.assertNotIn("11", result.missing_keys + result.unexpected_keys + result.duplicate_keys)

    def test_winning_refund_void_mix_can_be_complete(self) -> None:
        entries = (self._record(11, PayoutStatus.WINNING), self._record(12, PayoutStatus.REFUND), self._record(13, PayoutStatus.VOID))
        self.assertEqual(self._build(entries, True).status, CompletenessStatus.COMPLETE)

    def test_winning_refund_void_mix_can_be_incomplete(self) -> None:
        entries = (self._record(11, PayoutStatus.WINNING), self._record(12, PayoutStatus.REFUND), self._record(13, PayoutStatus.VOID))
        self.assertEqual(self._build(entries, False).status, CompletenessStatus.INCOMPLETE)

    def test_empty_complete_publication_is_complete(self) -> None:
        result = self._build((), True)
        self.assertEqual((result.status, result.expected_count, result.actual_count, result.reasons), (CompletenessStatus.COMPLETE, 0, 0, ()))

    def test_empty_incomplete_publication_is_incomplete(self) -> None:
        result = self._build((), False)
        self.assertEqual((result.status, result.expected_count, result.actual_count, result.reasons), (CompletenessStatus.INCOMPLETE, 0, 0, ("payout_not_declared_complete",)))

    def test_returns_completeness_result(self) -> None:
        self.assertIsInstance(self._build(), CompletenessResult)

    def test_does_not_return_provider_build_result(self) -> None:
        self.assertNotEqual(type(self._build()).__name__, "ProviderBuildResult")

    def test_rejects_invalid_publication_type(self) -> None:
        facts = self._facts(self._publication())
        for publication in (None, {}, (), object()):
            with self.subTest(publication=type(publication).__name__), self.assertRaises(ProviderValidationError):
                _build_payout_completeness(publication, facts)

    def test_rejects_invalid_facts_type(self) -> None:
        publication = self._publication()
        for facts in (None, {}, (), object()):
            with self.subTest(facts=type(facts).__name__), self.assertRaises(ProviderValidationError):
                _build_payout_completeness(publication, facts)

    def test_converts_model_errors_to_provider_validation_error(self) -> None:
        publication = self._publication()
        with patch("scripts.simulation.providers.payout_provider.CompletenessResult", side_effect=ValueError("bad model")):
            with self.assertRaises(ProviderValidationError) as caught:
                _build_payout_completeness(publication, self._facts(publication))
        self.assertIsInstance(caught.exception.__cause__, ValueError)

    def test_does_not_mutate_publication_or_facts(self) -> None:
        publication = self._publication((self._record(11, PayoutStatus.WINNING),))
        facts = self._facts(publication)
        _build_payout_completeness(publication, facts)
        self.assertEqual(publication, self._publication((self._record(11, PayoutStatus.WINNING),)))
        self.assertEqual(facts, self._facts(publication))

    def test_does_not_reanalyze_status_facts(self) -> None:
        self.assertNotIn("_analyze_payout_publication_status_facts", _build_payout_completeness.__code__.co_names)

    def test_does_not_iterate_publication_entries(self) -> None:
        self.assertNotIn("entries", _build_payout_completeness.__code__.co_names)

    def test_does_not_generate_selection_keys(self) -> None:
        self.assertNotIn("selection_key", _build_payout_completeness.__code__.co_names)

    def test_does_not_call_expected_selections(self) -> None:
        self.assertNotIn("expected_selections", _build_payout_completeness.__code__.co_names)

    def test_does_not_recheck_duplicate_records(self) -> None:
        self.assertNotIn("duplicate", _build_payout_completeness.__code__.co_names)

    def test_does_not_validate_payout_amount(self) -> None:
        self.assertNotIn("parse_payout_per_100", _build_payout_completeness.__code__.co_names)

    def test_has_no_database_repository_save_or_network_dependency(self) -> None:
        tree = ast.parse((Path(__file__).parents[1] / "scripts/simulation/providers/payout_provider.py").read_text(encoding="utf-8"))
        imports = {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
        forbidden = ("sqlite3", "requests", "httpx", "urllib", "selenium", "playwright", "scripts.simulation.repositories.sqlite")
        self.assertFalse(any(name.startswith(forbidden) for name in imports))
        self.assertNotIn("save_payout_publication", _build_payout_completeness.__code__.co_names)

    def test_internal_helper_is_not_exported_from_package_root(self) -> None:
        self.assertFalse(hasattr(providers, "_build_payout_completeness"))
