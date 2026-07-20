"""Tests for internal Payout Provider orchestration only."""

import ast
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from unittest.mock import patch
import unittest

import scripts.simulation.providers as providers
from scripts.simulation.providers.errors import ProviderValidationError
from scripts.simulation.providers.interfaces import ProviderBuildResult
from scripts.simulation.providers.models import (
    CompletenessResult,
    CompletenessStatus,
    ProviderContext,
    RaceEntryUniverse,
    RawPayoutPublication,
    RawPayoutRecord,
)
from scripts.simulation.providers.payout_provider import (
    _analyze_payout_publication_status_facts,
    _build_payout_completeness,
    _build_payout_provider_output,
    _build_payout_publication,
)
from scripts.simulation.repositories.interfaces import PayoutPublication, PayoutStatus


NOW = datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc)


class PayoutProviderOrchestrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.universe = RaceEntryUniverse(10, {11, 12, 13}, {14}, {15}, {1: 11, 2: 12, 3: 13, 4: 14, 5: 15})
        self.context = ProviderContext(10, NOW, "official", "https://example.test", NOW, NOW)

    def _record(self, entry_id: int = 11, payout: str | int = "100", status: str = "winning") -> RawPayoutRecord:
        return RawPayoutRecord((entry_id,), None, payout, status)

    def _raw(self, entries: tuple[RawPayoutRecord, ...] | None = None, complete: bool = True) -> RawPayoutPublication:
        return RawPayoutPublication("単勝", NOW, entries if entries is not None else (self._record(),), complete, True, True)

    def _build(self, entries: tuple[RawPayoutRecord, ...] | None = None, complete: bool = True) -> ProviderBuildResult[PayoutPublication]:
        return _build_payout_provider_output(self._raw(entries, complete), self.context, self.universe)

    def test_builds_provider_build_result(self) -> None:
        self.assertIsInstance(self._build(), ProviderBuildResult)

    def test_output_value_is_payout_publication(self) -> None:
        self.assertIsInstance(self._build().value, PayoutPublication)

    def test_output_completeness_is_completeness_result(self) -> None:
        self.assertIsInstance(self._build().completeness, CompletenessResult)

    def test_output_uses_publication_helper_object(self) -> None:
        raw = self._raw()
        publication = _build_payout_publication(raw, self.context, self.universe)
        with patch("scripts.simulation.providers.payout_provider._build_payout_publication", return_value=publication):
            self.assertIs(_build_payout_provider_output(raw, self.context, self.universe).value, publication)

    def test_output_uses_completeness_helper_object(self) -> None:
        raw = self._raw()
        publication = _build_payout_publication(raw, self.context, self.universe)
        facts = _analyze_payout_publication_status_facts(publication)
        completeness = _build_payout_completeness(publication, facts)
        with patch("scripts.simulation.providers.payout_provider._build_payout_publication", return_value=publication), patch("scripts.simulation.providers.payout_provider._analyze_payout_publication_status_facts", return_value=facts), patch("scripts.simulation.providers.payout_provider._build_payout_completeness", return_value=completeness):
            self.assertIs(_build_payout_provider_output(raw, self.context, self.universe).completeness, completeness)

    def test_complete_supported_publication_is_complete(self) -> None:
        self.assertEqual(self._build().completeness.status, CompletenessStatus.COMPLETE)

    def test_incomplete_supported_publication_is_incomplete(self) -> None:
        self.assertEqual(self._build(complete=False).completeness.status, CompletenessStatus.INCOMPLETE)

    def test_complete_unsupported_publication_is_unsupported(self) -> None:
        self.assertEqual(self._build((self._record(status="unsupported"),)).completeness.status, CompletenessStatus.UNSUPPORTED)

    def test_incomplete_unsupported_publication_is_unsupported(self) -> None:
        self.assertEqual(self._build((self._record(status="unsupported"),), False).completeness.status, CompletenessStatus.UNSUPPORTED)

    def test_mixed_supported_statuses_can_be_complete(self) -> None:
        entries = (self._record(11, 100, "winning"), self._record(12, 0, "refund"), self._record(13, 0, "void"))
        self.assertEqual(self._build(entries).completeness.status, CompletenessStatus.COMPLETE)

    def test_empty_complete_publication_is_complete(self) -> None:
        result = self._build(())
        self.assertEqual((result.completeness.status, result.completeness.expected_count, result.completeness.actual_count), (CompletenessStatus.COMPLETE, 0, 0))

    def test_counts_reasons_and_discrepancy_keys_are_preserved(self) -> None:
        result = self._build((self._record(status="unsupported"),), False)
        self.assertEqual((result.completeness.expected_count, result.completeness.actual_count), (1, 1))
        self.assertEqual(set(result.completeness.reasons), {"unsupported_payout_records", "payout_not_declared_complete"})
        self.assertEqual((result.completeness.missing_keys, result.completeness.unexpected_keys, result.completeness.duplicate_keys), ((), (), ()))

    def test_calls_publication_helper_once(self) -> None:
        with patch("scripts.simulation.providers.payout_provider._build_payout_publication", wraps=_build_payout_publication) as helper:
            _build_payout_provider_output(self._raw(), self.context, self.universe)
        helper.assert_called_once_with(self._raw(), self.context, self.universe)

    def test_calls_status_facts_helper_once(self) -> None:
        with patch("scripts.simulation.providers.payout_provider._analyze_payout_publication_status_facts", wraps=_analyze_payout_publication_status_facts) as helper:
            _build_payout_provider_output(self._raw(), self.context, self.universe)
        helper.assert_called_once()

    def test_calls_completeness_helper_once(self) -> None:
        with patch("scripts.simulation.providers.payout_provider._build_payout_completeness", wraps=_build_payout_completeness) as helper:
            _build_payout_provider_output(self._raw(), self.context, self.universe)
        helper.assert_called_once()

    def test_calls_helpers_in_expected_order(self) -> None:
        order: list[str] = []
        originals = (_build_payout_publication, _analyze_payout_publication_status_facts, _build_payout_completeness)
        def publication(*args):
            order.append("publication")
            return originals[0](*args)
        def facts(*args):
            order.append("facts")
            return originals[1](*args)
        def completeness(*args):
            order.append("completeness")
            return originals[2](*args)
        with patch("scripts.simulation.providers.payout_provider._build_payout_publication", side_effect=publication), patch("scripts.simulation.providers.payout_provider._analyze_payout_publication_status_facts", side_effect=facts), patch("scripts.simulation.providers.payout_provider._build_payout_completeness", side_effect=completeness):
            _build_payout_provider_output(self._raw(), self.context, self.universe)
        self.assertEqual(order, ["publication", "facts", "completeness"])

    def test_status_facts_and_completeness_receive_same_objects(self) -> None:
        raw = self._raw()
        publication = _build_payout_publication(raw, self.context, self.universe)
        facts = _analyze_payout_publication_status_facts(publication)
        with patch("scripts.simulation.providers.payout_provider._build_payout_publication", return_value=publication), patch("scripts.simulation.providers.payout_provider._analyze_payout_publication_status_facts", return_value=facts) as analyze, patch("scripts.simulation.providers.payout_provider._build_payout_completeness", wraps=_build_payout_completeness) as completeness:
            _build_payout_provider_output(raw, self.context, self.universe)
        analyze.assert_called_once_with(publication)
        completeness.assert_called_once_with(publication, facts)

    def test_fails_without_partial_output_when_a_stage_fails(self) -> None:
        for target in ("_build_payout_publication", "_analyze_payout_publication_status_facts", "_build_payout_completeness"):
            with self.subTest(target=target), patch(f"scripts.simulation.providers.payout_provider.{target}", side_effect=ProviderValidationError("failed")):
                with self.assertRaises(ProviderValidationError):
                    _build_payout_provider_output(self._raw(), self.context, self.universe)

    def test_converts_build_result_errors_to_provider_validation_error(self) -> None:
        with patch("scripts.simulation.providers.payout_provider.ProviderBuildResult", side_effect=ValueError("bad result")):
            with self.assertRaises(ProviderValidationError) as caught:
                self._build()
        self.assertIsInstance(caught.exception.__cause__, ValueError)

    def test_rejects_invalid_raw_context_and_universe_through_existing_boundary(self) -> None:
        for raw, context, universe in ((None, self.context, self.universe), (self._raw(), None, self.universe), (self._raw(), self.context, None)):
            with self.subTest(raw=raw is None, context=context is None, universe=universe is None), self.assertRaises(ProviderValidationError):
                _build_payout_provider_output(raw, context, universe)

    def test_does_not_mutate_inputs(self) -> None:
        raw = self._raw()
        context = self.context
        universe = self.universe
        _build_payout_provider_output(raw, context, universe)
        self.assertEqual(raw, self._raw())
        self.assertEqual(context, self.context)
        self.assertEqual(universe, self.universe)

    def test_does_not_write_stdout_or_stderr(self) -> None:
        stdout, stderr = StringIO(), StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            self._build()
        self.assertEqual((stdout.getvalue(), stderr.getvalue()), ("", ""))

    def test_has_no_database_repository_save_or_network_dependency(self) -> None:
        tree = ast.parse((Path(__file__).parents[1] / "scripts/simulation/providers/payout_provider.py").read_text(encoding="utf-8"))
        imports = {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
        forbidden = ("sqlite3", "requests", "httpx", "urllib", "selenium", "playwright", "scripts.simulation.repositories.sqlite")
        self.assertFalse(any(name.startswith(forbidden) for name in imports))
        self.assertNotIn("save_payout_publication", _build_payout_provider_output.__code__.co_names)

    def test_internal_helper_is_not_exported_from_package_root(self) -> None:
        self.assertFalse(hasattr(providers, "_build_payout_provider_output"))


    def test_does_not_recompute_status_or_completeness_rules(self) -> None:
        names = _build_payout_provider_output.__code__.co_names
        self.assertNotIn("CompletenessStatus", names)
        self.assertNotIn("PayoutStatus", names)

    def test_does_not_call_expected_selections_or_generate_selection_keys(self) -> None:
        names = _build_payout_provider_output.__code__.co_names
        self.assertNotIn("expected_selections", names)
        self.assertNotIn("selection_key", names)
