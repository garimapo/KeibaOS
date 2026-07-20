"""Tests for pure RawRaceResultEntry conversion."""

import ast
from pathlib import Path
from unittest.mock import patch
import unittest

from scripts.simulation.providers.errors import ProviderValidationError
from scripts.simulation.providers.models import RaceEntryUniverse, RawRaceResultEntry
from scripts.simulation.providers.normalization import (
    normalize_result_entry_status,
    parse_finish_position,
)
from scripts.simulation.providers.result_provider import _build_persisted_result_entry
from scripts.simulation.repositories.interfaces import (
    PersistedRaceResultEntry,
    RaceResultEntryStatus,
)


class ResultProviderEntryConversionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.universe = RaceEntryUniverse(1, {11}, {12}, {13}, {1: 11, 2: 12, 3: 13})

    def _raw(self, horse_no: int = 1, race_entry_id: int = 11, finish: str | int | None = 1, status: str = "confirmed") -> RawRaceResultEntry:
        return RawRaceResultEntry(horse_no, race_entry_id, finish, status)

    def test_builds_confirmed_entry_from_integer_finish(self) -> None:
        entry = _build_persisted_result_entry(self._raw(finish=1), self.universe)
        self.assertEqual(entry.finish_position, 1)
        self.assertIs(entry.result_status, RaceResultEntryStatus.CONFIRMED)

    def test_builds_confirmed_entry_from_string_finish(self) -> None:
        entry = _build_persisted_result_entry(self._raw(finish="2"), self.universe)
        self.assertEqual(entry.finish_position, 2)

    def test_builds_void_entry_with_none_finish(self) -> None:
        entry = _build_persisted_result_entry(self._raw(finish="取消", status="void"), self.universe)
        self.assertIsNone(entry.finish_position)
        self.assertIs(entry.result_status, RaceResultEntryStatus.VOID)

    def test_builds_unsupported_entry_with_none_finish(self) -> None:
        entry = _build_persisted_result_entry(self._raw(finish=None, status="unsupported"), self.universe)
        self.assertIs(entry.result_status, RaceResultEntryStatus.UNSUPPORTED)

    def test_returns_repository_boundary_entry(self) -> None:
        self.assertIsInstance(_build_persisted_result_entry(self._raw(), self.universe), PersistedRaceResultEntry)

    def test_reuses_parse_finish_position(self) -> None:
        with patch("scripts.simulation.providers.result_provider.parse_finish_position", wraps=parse_finish_position) as parser:
            _build_persisted_result_entry(self._raw(), self.universe)
        parser.assert_called_once_with(1)

    def test_reuses_normalize_result_entry_status(self) -> None:
        with patch("scripts.simulation.providers.result_provider.normalize_result_entry_status", wraps=normalize_result_entry_status) as normalizer:
            _build_persisted_result_entry(self._raw(), self.universe)
        normalizer.assert_called_once_with("confirmed")

    def test_rejects_invalid_raw_type(self) -> None:
        for raw in (None, {"horse_no": 1}, object()):
            with self.subTest(raw=type(raw).__name__), self.assertRaises(ProviderValidationError):
                _build_persisted_result_entry(raw, self.universe)

    def test_rejects_invalid_universe_type(self) -> None:
        for universe in (None, {"active": {11}}, object()):
            with self.subTest(universe=type(universe).__name__), self.assertRaises(ProviderValidationError):
                _build_persisted_result_entry(self._raw(), universe)

    def test_rejects_unknown_horse_number(self) -> None:
        raw = self._raw(horse_no=4, race_entry_id=11)
        with self.assertRaises(ProviderValidationError):
            _build_persisted_result_entry(raw, self.universe)

    def test_rejects_unknown_race_entry_id(self) -> None:
        raw = self._raw(race_entry_id=99)
        with self.assertRaises(ProviderValidationError):
            _build_persisted_result_entry(raw, self.universe)

    def test_rejects_horse_number_entry_id_mismatch(self) -> None:
        raw = self._raw(race_entry_id=12)
        with self.assertRaises(ProviderValidationError):
            _build_persisted_result_entry(raw, self.universe)

    def test_accepts_known_active_entry(self) -> None:
        self.assertEqual(_build_persisted_result_entry(self._raw(), self.universe).race_entry_id, 11)

    def test_accepts_known_excluded_entry(self) -> None:
        raw = self._raw(horse_no=2, race_entry_id=12, finish="取消", status="void")
        self.assertEqual(_build_persisted_result_entry(raw, self.universe).race_entry_id, 12)

    def test_accepts_known_cancelled_entry(self) -> None:
        raw = self._raw(horse_no=3, race_entry_id=13, finish="取消", status="void")
        self.assertEqual(_build_persisted_result_entry(raw, self.universe).race_entry_id, 13)

    def test_rejects_confirmed_entry_without_finish(self) -> None:
        with self.assertRaises(ProviderValidationError):
            _build_persisted_result_entry(self._raw(finish=None), self.universe)

    def test_rejects_void_entry_with_finish(self) -> None:
        with self.assertRaises(ProviderValidationError):
            _build_persisted_result_entry(self._raw(finish=1, status="void"), self.universe)

    def test_rejects_unsupported_entry_with_finish(self) -> None:
        with self.assertRaises(ProviderValidationError):
            _build_persisted_result_entry(self._raw(finish=1, status="unsupported"), self.universe)

    def test_converts_low_level_errors_to_provider_validation_error(self) -> None:
        with patch("scripts.simulation.providers.result_provider.parse_finish_position", side_effect=ValueError("bad finish")):
            with self.assertRaises(ProviderValidationError) as caught:
                _build_persisted_result_entry(self._raw(), self.universe)
        self.assertIsInstance(caught.exception.__cause__, ValueError)

    def test_does_not_mutate_raw_entry(self) -> None:
        raw = self._raw(finish=" 1 ", status=" confirmed ")
        before = raw
        _build_persisted_result_entry(raw, self.universe)
        self.assertEqual(raw, before)

    def test_does_not_mutate_universe(self) -> None:
        before = self.universe
        _build_persisted_result_entry(self._raw(), self.universe)
        self.assertEqual(self.universe, before)

    def test_has_no_database_or_network_dependency(self) -> None:
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
