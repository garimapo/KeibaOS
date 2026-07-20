"""Tests for package-internal Odds Provider orchestration."""

import ast
from contextlib import redirect_stderr, redirect_stdout
from datetime import UTC, datetime
from decimal import Decimal
from io import StringIO
from pathlib import Path
from unittest.mock import patch
import unittest

import scripts.simulation.providers as providers
from scripts.simulation.providers.errors import ProviderValidationError
from scripts.simulation.providers.interfaces import ProviderBuildResult
from scripts.simulation.providers.models import CompletenessResult, CompletenessStatus, ProviderContext, RaceEntryUniverse, RawOddsBatch, RawOddsEntry
from scripts.simulation.providers import odds_provider
from scripts.simulation.providers.odds_provider import _build_odds_provider_output
from scripts.simulation.repositories.interfaces import OddsSnapshotBatch, OddsSnapshotEntry


NOW = datetime(2026, 1, 2, 12, 0, tzinfo=UTC)


class OddsProviderOrchestrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.context = ProviderContext(10, NOW, "fixture", None, NOW, NOW)
        self.universe = RaceEntryUniverse(10, {11, 12}, set(), set(), {1: 11, 2: 12})

    def _raw(self, entries=None, complete: bool = True) -> RawOddsBatch:
        return RawOddsBatch("単勝", entries if entries is not None else (RawOddsEntry((11,), None, "1.2"), RawOddsEntry((12,), None, "2.3")), complete)

    def _build(self, raw=None):
        return _build_odds_provider_output(raw or self._raw(), self.context, self.universe)

    def test_builds_provider_build_result(self) -> None:
        self.assertIsInstance(self._build(), ProviderBuildResult)

    def test_output_value_is_odds_snapshot_batch(self) -> None:
        self.assertIsInstance(self._build().value, OddsSnapshotBatch)

    def test_output_completeness_is_completeness_result(self) -> None:
        self.assertIsInstance(self._build().completeness, CompletenessResult)

    def test_output_uses_batch_helper_object(self) -> None:
        created = []
        original = odds_provider._build_odds_snapshot_batch
        def wrapped(*args, **kwargs):
            value = original(*args, **kwargs)
            created.append(value)
            return value
        with patch.object(odds_provider, "_build_odds_snapshot_batch", side_effect=wrapped):
            output = self._build()
        self.assertIs(output.value, created[0])

    def test_output_uses_completeness_helper_object(self) -> None:
        created = []
        original = odds_provider._build_odds_completeness
        def wrapped(*args, **kwargs):
            value = original(*args, **kwargs)
            created.append(value)
            return value
        with patch.object(odds_provider, "_build_odds_completeness", side_effect=wrapped):
            output = self._build()
        self.assertIs(output.completeness, created[0])

    def test_complete_odds_are_complete(self) -> None:
        self.assertIs(self._build().completeness.status, CompletenessStatus.COMPLETE)

    def test_not_declared_complete_odds_are_incomplete(self) -> None:
        self.assertIs(self._build(self._raw(complete=False)).completeness.status, CompletenessStatus.INCOMPLETE)

    def test_missing_selections_are_incomplete(self) -> None:
        output = self._build(self._raw((RawOddsEntry((11,), None, "1.2"),)))
        self.assertIs(output.completeness.status, CompletenessStatus.INCOMPLETE)

    def _unexpected_batch(self, complete: bool = True) -> OddsSnapshotBatch:
        return OddsSnapshotBatch(10, "単勝", NOW, complete, "fixture", (OddsSnapshotEntry((11,), Decimal("1.2")), OddsSnapshotEntry((99,), Decimal("2.3"))))

    def test_unexpected_selections_are_invalid(self) -> None:
        with patch.object(odds_provider, "_build_odds_snapshot_batch", return_value=self._unexpected_batch(False)):
            self.assertIs(self._build().completeness.status, CompletenessStatus.INVALID)

    def test_combined_discrepancies_preserve_all_reasons(self) -> None:
        with patch.object(odds_provider, "_build_odds_snapshot_batch", return_value=self._unexpected_batch(False)):
            reasons = self._build(self._raw(complete=False)).completeness.reasons
        self.assertEqual(reasons, ("missing_odds_selections", "odds_not_declared_complete", "unexpected_odds_selections"))

    def test_combined_discrepancies_preserve_missing_keys(self) -> None:
        with patch.object(odds_provider, "_build_odds_snapshot_batch", return_value=self._unexpected_batch()):
            self.assertEqual(self._build().completeness.missing_keys, ("12",))

    def test_combined_discrepancies_preserve_unexpected_keys(self) -> None:
        with patch.object(odds_provider, "_build_odds_snapshot_batch", return_value=self._unexpected_batch()):
            self.assertEqual(self._build().completeness.unexpected_keys, ("99",))

    def test_counts_are_preserved_through_pipeline(self) -> None:
        output = self._build(self._raw((RawOddsEntry((11,), None, "1.2"),)))
        self.assertEqual((output.completeness.expected_count, output.completeness.actual_count), (2, 1))

    def test_calls_batch_helper_once(self) -> None:
        with patch.object(odds_provider, "_build_odds_snapshot_batch", wraps=odds_provider._build_odds_snapshot_batch) as helper:
            self._build()
        helper.assert_called_once()

    def test_calls_coverage_helper_once(self) -> None:
        with patch.object(odds_provider, "_analyze_odds_selection_coverage", wraps=odds_provider._analyze_odds_selection_coverage) as helper:
            self._build()
        helper.assert_called_once()

    def test_calls_completeness_helper_once(self) -> None:
        with patch.object(odds_provider, "_build_odds_completeness", wraps=odds_provider._build_odds_completeness) as helper:
            self._build()
        helper.assert_called_once()

    def test_calls_helpers_in_expected_order(self) -> None:
        names = ("_build_odds_snapshot_batch", "_analyze_odds_selection_coverage", "_build_odds_completeness")
        events = []
        patches = []
        for name in names:
            original = getattr(odds_provider, name)
            def wrapped(*args, _name=name, _original=original, **kwargs):
                events.append(_name)
                return _original(*args, **kwargs)
            patches.append(patch.object(odds_provider, name, side_effect=wrapped))
        for item in patches: item.start()
        try: self._build()
        finally:
            for item in reversed(patches): item.stop()
        self.assertEqual(events, list(names))

    def test_coverage_receives_same_batch_and_universe(self) -> None:
        with patch.object(odds_provider, "_analyze_odds_selection_coverage", wraps=odds_provider._analyze_odds_selection_coverage) as helper:
            output = self._build()
        self.assertIs(helper.call_args.args[0], output.value)
        self.assertIs(helper.call_args.args[1], self.universe)

    def test_completeness_receives_same_batch_and_coverage(self) -> None:
        produced = []
        analyzer_original = odds_provider._analyze_odds_selection_coverage
        def analyzer(*args, **kwargs):
            value = analyzer_original(*args, **kwargs)
            produced.append(value)
            return value
        with patch.object(odds_provider, "_analyze_odds_selection_coverage", side_effect=analyzer), patch.object(odds_provider, "_build_odds_completeness", wraps=odds_provider._build_odds_completeness) as builder:
            output = self._build()
        self.assertIs(builder.call_args.args[0], output.value)
        self.assertIs(builder.call_args.args[1], produced[0])

    def _assert_stage_failure(self, name: str) -> None:
        with patch.object(odds_provider, name, side_effect=ValueError(name)):
            with self.assertRaises(ProviderValidationError) as caught: self._build()
        self.assertIsInstance(caught.exception.__cause__, ValueError)

    def test_fails_without_partial_output_when_batch_build_fails(self) -> None: self._assert_stage_failure("_build_odds_snapshot_batch")
    def test_fails_without_partial_output_when_coverage_fails(self) -> None: self._assert_stage_failure("_analyze_odds_selection_coverage")
    def test_fails_without_partial_output_when_completeness_fails(self) -> None: self._assert_stage_failure("_build_odds_completeness")

    def test_converts_build_result_errors_to_provider_validation_error(self) -> None:
        with patch.object(odds_provider, "ProviderBuildResult", side_effect=ValueError("bad result")):
            with self.assertRaises(ProviderValidationError) as caught: self._build()
        self.assertIsInstance(caught.exception.__cause__, ValueError)

    def test_rejects_invalid_raw_through_existing_boundary(self) -> None:
        with self.assertRaises(ProviderValidationError): _build_odds_provider_output(None, self.context, self.universe)

    def test_rejects_invalid_context_through_existing_boundary(self) -> None:
        with self.assertRaises(ProviderValidationError): _build_odds_provider_output(self._raw(), None, self.universe)

    def test_rejects_invalid_universe_through_existing_boundary(self) -> None:
        with self.assertRaises(ProviderValidationError): _build_odds_provider_output(self._raw(), self.context, None)

    def test_does_not_mutate_raw_context_or_universe(self) -> None:
        raw = self._raw(); before = (raw, self.context, self.universe)
        self._build(raw)
        self.assertEqual((raw, self.context, self.universe), before)

    def test_does_not_write_stdout_or_stderr(self) -> None:
        stdout, stderr = StringIO(), StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr): self._build()
        self.assertEqual((stdout.getvalue(), stderr.getvalue()), ("", ""))

    def test_has_no_database_repository_save_or_network_dependency(self) -> None:
        tree = ast.parse((Path(__file__).parents[1] / "scripts/simulation/providers/odds_provider.py").read_text(encoding="utf-8"))
        imports = {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
        forbidden = ("sqlite3", "requests", "httpx", "urllib", "selenium", "playwright", "scripts.simulation.repositories.sqlite")
        self.assertFalse(any(name.startswith(forbidden) for name in imports))

    def test_internal_helper_is_not_exported_from_package_root(self) -> None:
        self.assertFalse(hasattr(providers, "_build_odds_provider_output"))

    def test_does_not_define_unrelated_concrete_odds_provider(self) -> None:
        classes = [node.name for node in ast.walk(ast.parse((Path(__file__).parents[1] / "scripts/simulation/providers/odds_provider.py").read_text(encoding="utf-8"))) if isinstance(node, ast.ClassDef)]
        self.assertNotIn("ConcreteOddsSnapshotProvider", classes)

    def test_does_not_save_batch(self) -> None:
        self.assertFalse(any("save" in name.lower() for name in _build_odds_provider_output.__code__.co_names))

    def test_does_not_recompute_coverage_or_completeness_rules(self) -> None:
        names = _build_odds_provider_output.__code__.co_names
        self.assertNotIn("expected_selections", names)
        self.assertNotIn("selection_key", names)
