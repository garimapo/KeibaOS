"""Tests for pure RawRaceResult aggregate conversion."""

import ast
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch
import unittest

from scripts.simulation.providers.errors import ProviderValidationError
from scripts.simulation.providers.models import (
    ProviderContext,
    RaceEntryUniverse,
    RawRaceResult,
    RawRaceResultEntry,
)
from scripts.simulation.providers.normalization import normalize_result_status
from scripts.simulation.providers.result_provider import (
    _build_persisted_race_result,
    _build_persisted_result_entry,
)
from scripts.simulation.repositories.interfaces import PersistedRaceResult, RaceResultStatus


NOW = datetime(2026, 1, 2, 12, 0, tzinfo=UTC)


class ResultProviderAggregateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.context = ProviderContext(10, NOW, "fixture", None, NOW, NOW)
        self.universe = RaceEntryUniverse(10, {11, 12}, set(), set(), {1: 11, 2: 12})

    def _raw(
        self,
        declared_status: str = "complete",
        finalized_at: datetime | None = NOW,
        entries: tuple[RawRaceResultEntry, ...] | None = None,
    ) -> RawRaceResult:
        return RawRaceResult(
            declared_status,
            finalized_at,
            entries
            if entries is not None
            else (
                RawRaceResultEntry(1, 11, 1, "confirmed"),
                RawRaceResultEntry(2, 12, 2, "confirmed"),
            ),
        )

    def test_builds_complete_race_result(self) -> None:
        result = _build_persisted_race_result(self._raw(), self.context, self.universe)
        self.assertIs(result.result_status, RaceResultStatus.COMPLETE)

    def test_builds_partial_race_result(self) -> None:
        result = _build_persisted_race_result(self._raw("partial", None), self.context, self.universe)
        self.assertIs(result.result_status, RaceResultStatus.PARTIAL)

    def test_builds_void_race_result(self) -> None:
        result = _build_persisted_race_result(self._raw("void", None, ()), self.context, self.universe)
        self.assertIs(result.result_status, RaceResultStatus.VOID)

    def test_builds_unsupported_race_result(self) -> None:
        result = _build_persisted_race_result(self._raw("unsupported", None, ()), self.context, self.universe)
        self.assertIs(result.result_status, RaceResultStatus.UNSUPPORTED)

    def test_returns_persisted_race_result(self) -> None:
        self.assertIsInstance(_build_persisted_race_result(self._raw(), self.context, self.universe), PersistedRaceResult)

    def test_uses_context_race_id(self) -> None:
        self.assertEqual(_build_persisted_race_result(self._raw(), self.context, self.universe).race_id, 10)

    def test_uses_context_observed_at(self) -> None:
        self.assertEqual(_build_persisted_race_result(self._raw(), self.context, self.universe).observed_at, NOW)

    def test_uses_context_source(self) -> None:
        self.assertEqual(_build_persisted_race_result(self._raw(), self.context, self.universe).source, "fixture")

    def test_uses_raw_finalized_at(self) -> None:
        finalized_at = NOW - timedelta(minutes=1)
        self.assertEqual(_build_persisted_race_result(self._raw(finalized_at=finalized_at), self.context, self.universe).finalized_at, finalized_at)

    def test_reuses_normalize_result_status(self) -> None:
        with patch("scripts.simulation.providers.result_provider.normalize_result_status", wraps=normalize_result_status) as normalizer:
            _build_persisted_race_result(self._raw(), self.context, self.universe)
        normalizer.assert_called_once_with("complete")

    def test_reuses_entry_conversion_helper_for_every_entry(self) -> None:
        with patch(
            "scripts.simulation.providers.result_provider._build_persisted_result_entry",
            wraps=_build_persisted_result_entry,
        ) as converter:
            _build_persisted_race_result(self._raw(), self.context, self.universe)
        self.assertEqual(converter.call_count, 2)

    def test_rejects_invalid_raw_type(self) -> None:
        for raw in (None, {}, [], object()):
            with self.subTest(raw=type(raw).__name__), self.assertRaises(ProviderValidationError):
                _build_persisted_race_result(raw, self.context, self.universe)

    def test_rejects_invalid_context_type(self) -> None:
        for context in (None, {}, object()):
            with self.subTest(context=type(context).__name__), self.assertRaises(ProviderValidationError):
                _build_persisted_race_result(self._raw(), context, self.universe)

    def test_rejects_invalid_universe_type(self) -> None:
        for universe in (None, {}, object()):
            with self.subTest(universe=type(universe).__name__), self.assertRaises(ProviderValidationError):
                _build_persisted_race_result(self._raw(), self.context, universe)

    def test_rejects_unknown_declared_status(self) -> None:
        with self.assertRaises(ProviderValidationError):
            _build_persisted_race_result(self._raw("unknown", None), self.context, self.universe)

    def test_fails_entire_aggregate_when_one_entry_is_invalid(self) -> None:
        raw = self._raw(entries=(RawRaceResultEntry(1, 11, 1, "confirmed"), RawRaceResultEntry(2, 12, None, "confirmed")))
        with self.assertRaises(ProviderValidationError):
            _build_persisted_race_result(raw, self.context, self.universe)

    def test_does_not_silently_drop_entries(self) -> None:
        result = _build_persisted_race_result(self._raw(), self.context, self.universe)
        self.assertEqual(len(result.entries), 2)

    def test_does_not_add_universe_entries(self) -> None:
        raw = self._raw(entries=(RawRaceResultEntry(1, 11, 1, "confirmed"),))
        result = _build_persisted_race_result(raw, self.context, self.universe)
        self.assertEqual(tuple(entry.race_entry_id for entry in result.entries), (11,))

    def test_returns_entries_as_tuple(self) -> None:
        self.assertIsInstance(_build_persisted_race_result(self._raw(), self.context, self.universe).entries, tuple)

    def test_entry_order_is_canonical_and_deterministic(self) -> None:
        raw = self._raw(entries=(RawRaceResultEntry(2, 12, 2, "confirmed"), RawRaceResultEntry(1, 11, 1, "confirmed")))
        result = _build_persisted_race_result(raw, self.context, self.universe)
        self.assertEqual(tuple(entry.race_entry_id for entry in result.entries), (11, 12))

    def test_repository_finalized_at_rules_are_preserved(self) -> None:
        with self.assertRaises(ProviderValidationError):
            _build_persisted_race_result(self._raw("complete", None), self.context, self.universe)
        with self.assertRaises(ProviderValidationError):
            _build_persisted_race_result(self._raw(finalized_at=NOW + timedelta(seconds=1)), self.context, self.universe)

    def test_converts_boundary_model_errors_to_provider_validation_error(self) -> None:
        with patch("scripts.simulation.providers.result_provider.normalize_result_status", side_effect=ValueError("bad status")):
            with self.assertRaises(ProviderValidationError) as caught:
                _build_persisted_race_result(self._raw(), self.context, self.universe)
        self.assertIsInstance(caught.exception.__cause__, ValueError)

    def test_does_not_mutate_raw(self) -> None:
        raw = self._raw()
        before = raw
        _build_persisted_race_result(raw, self.context, self.universe)
        self.assertEqual(raw, before)

    def test_does_not_mutate_context(self) -> None:
        before = self.context
        _build_persisted_race_result(self._raw(), self.context, self.universe)
        self.assertEqual(self.context, before)

    def test_does_not_mutate_universe(self) -> None:
        before = self.universe
        _build_persisted_race_result(self._raw(), self.context, self.universe)
        self.assertEqual(self.universe, before)

    def test_has_no_database_repository_or_network_dependency(self) -> None:
        path = Path(__file__).parents[1] / "scripts/simulation/providers/result_provider.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        forbidden_prefixes = ("sqlite3", "requests", "httpx", "urllib", "selenium", "playwright")
        self.assertFalse(any(name.startswith(forbidden_prefixes) for name in imports))
        self.assertNotIn("scripts.simulation.repositories.sqlite", imports)

    def test_does_not_return_provider_build_result(self) -> None:
        result = _build_persisted_race_result(self._raw(), self.context, self.universe)
        self.assertIsInstance(result, PersistedRaceResult)
        self.assertNotEqual(type(result).__name__, "ProviderBuildResult")

    def test_does_not_generate_completeness_result(self) -> None:
        result = _build_persisted_race_result(self._raw(), self.context, self.universe)
        self.assertFalse(hasattr(result, "completeness"))
