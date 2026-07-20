"""Tests for package-internal Result Provider orchestration."""

import ast
from datetime import UTC, datetime
from io import StringIO
from pathlib import Path
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch
import unittest

from scripts.simulation.providers.errors import ProviderValidationError
from scripts.simulation.providers.interfaces import ProviderBuildResult
from scripts.simulation.providers.models import (
    CompletenessResult,
    CompletenessStatus,
    ProviderContext,
    RaceEntryUniverse,
    RawRaceResult,
    RawRaceResultEntry,
)
from scripts.simulation.providers import result_provider
from scripts.simulation.providers.result_provider import _build_race_result_provider_output
from scripts.simulation.repositories.interfaces import PersistedRaceResult


NOW = datetime(2026, 1, 2, 12, 0, tzinfo=UTC)


class ResultProviderOrchestrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.context = ProviderContext(10, NOW, "fixture", None, NOW, NOW)
        self.universe = RaceEntryUniverse(10, {11, 12}, {13}, {14}, {1: 11, 2: 12, 3: 13, 4: 14})

    def _raw(
        self,
        status: str = "complete",
        entries: tuple[RawRaceResultEntry, ...] | None = None,
        finalized_at: datetime | None = NOW,
    ) -> RawRaceResult:
        return RawRaceResult(
            status,
            finalized_at,
            entries if entries is not None else (
                RawRaceResultEntry(1, 11, 1, "confirmed"),
                RawRaceResultEntry(2, 12, 2, "confirmed"),
                RawRaceResultEntry(3, 13, None, "void"),
                RawRaceResultEntry(4, 14, None, "void"),
            ),
        )

    def _build(self, raw: RawRaceResult | None = None):
        return _build_race_result_provider_output(raw or self._raw(), self.context, self.universe)

    def test_builds_provider_build_result(self) -> None:
        self.assertIsInstance(self._build(), ProviderBuildResult)

    def test_output_value_is_persisted_race_result(self) -> None:
        self.assertIsInstance(self._build().value, PersistedRaceResult)

    def test_output_completeness_is_completeness_result(self) -> None:
        self.assertIsInstance(self._build().completeness, CompletenessResult)

    def test_output_uses_aggregate_result_object(self) -> None:
        produced: list[PersistedRaceResult] = []
        original = result_provider._build_persisted_race_result
        def aggregate(*args, **kwargs):
            value = original(*args, **kwargs)
            produced.append(value)
            return value
        with patch.object(
            result_provider,
            "_build_persisted_race_result",
            side_effect=aggregate,
        ) as aggregate:
            output = self._build()
        self.assertIs(output.value, produced[0])
        self.assertEqual(aggregate.call_count, 1)

    def test_complete_valid_result_is_complete(self) -> None:
        self.assertIs(self._build().completeness.status, CompletenessStatus.COMPLETE)

    def test_partial_result_is_incomplete(self) -> None:
        output = self._build(self._raw("partial", finalized_at=None))
        self.assertIs(output.completeness.status, CompletenessStatus.INCOMPLETE)

    def test_missing_result_entries_are_incomplete(self) -> None:
        output = self._build(self._raw(entries=(RawRaceResultEntry(1, 11, 1, "confirmed"),)))
        self.assertIs(output.completeness.status, CompletenessStatus.INCOMPLETE)

    def test_unsupported_result_is_unsupported(self) -> None:
        output = self._build(self._raw("unsupported", (), None))
        self.assertIs(output.completeness.status, CompletenessStatus.UNSUPPORTED)

    def test_unexpected_entry_is_invalid(self) -> None:
        result = PersistedRaceResult(10, result_provider.RaceResultStatus.COMPLETE, NOW, NOW, "fixture", (
            result_provider.PersistedRaceResultEntry(11, 11, 1, result_provider.RaceResultEntryStatus.CONFIRMED),
            result_provider.PersistedRaceResultEntry(19, 99, 2, result_provider.RaceResultEntryStatus.CONFIRMED),
        ))
        with patch.object(result_provider, "_build_persisted_race_result", return_value=result):
            output = self._build()
        self.assertIs(output.completeness.status, CompletenessStatus.INVALID)

    def test_entry_category_issue_is_invalid(self) -> None:
        raw = self._raw(entries=(RawRaceResultEntry(1, 11, None, "void"), RawRaceResultEntry(2, 12, 2, "confirmed")))
        output = self._build(raw)
        self.assertIs(output.completeness.status, CompletenessStatus.INVALID)

    def test_void_race_status_issue_is_invalid(self) -> None:
        raw = self._raw("void", (RawRaceResultEntry(1, 11, 1, "confirmed"),), None)
        self.assertIs(self._build(raw).completeness.status, CompletenessStatus.INVALID)

    def test_unsupported_race_status_issue_is_invalid(self) -> None:
        raw = self._raw("unsupported", (RawRaceResultEntry(1, 11, None, "void"),), None)
        self.assertIs(self._build(raw).completeness.status, CompletenessStatus.INVALID)

    def test_combined_issues_preserve_all_reasons(self) -> None:
        raw = self._raw("void", (RawRaceResultEntry(1, 11, 1, "confirmed"),))
        reasons = self._build(raw).completeness.reasons
        self.assertIn("missing_result_entries", reasons)
        self.assertIn("void_race_non_void_result_entries", reasons)

    def test_combined_issues_preserve_missing_keys(self) -> None:
        raw = self._raw("void", (RawRaceResultEntry(1, 11, 1, "confirmed"),))
        self.assertEqual(
            self._build(raw).completeness.missing_keys,
            ("race_entry_id:12", "race_entry_id:13", "race_entry_id:14"),
        )

    def test_combined_issues_preserve_unexpected_keys(self) -> None:
        result = PersistedRaceResult(10, result_provider.RaceResultStatus.VOID, None, NOW, "fixture", (
            result_provider.PersistedRaceResultEntry(11, 11, 1, result_provider.RaceResultEntryStatus.CONFIRMED),
            result_provider.PersistedRaceResultEntry(19, 99, 2, result_provider.RaceResultEntryStatus.CONFIRMED),
        ))
        with patch.object(result_provider, "_build_persisted_race_result", return_value=result):
            output = self._build()
        self.assertEqual(output.completeness.unexpected_keys, ("race_entry_id:99",))

    def test_counts_are_preserved_through_pipeline(self) -> None:
        output = self._build(self._raw(entries=(RawRaceResultEntry(1, 11, 1, "confirmed"),)))
        self.assertEqual((output.completeness.expected_count, output.completeness.actual_count), (4, 1))

    def test_calls_each_helper_once(self) -> None:
        names = (
            "_build_persisted_race_result",
            "_analyze_result_coverage",
            "_build_result_completeness",
            "_analyze_result_entry_semantics",
            "_apply_result_entry_semantics",
            "_analyze_result_race_status_semantics",
            "_apply_result_race_status_semantics",
        )
        patches = [patch.object(result_provider, name, wraps=getattr(result_provider, name)) for name in names]
        mocks = [item.start() for item in patches]
        try:
            self._build()
        finally:
            for item in reversed(patches):
                item.stop()
        self.assertEqual([mock.call_count for mock in mocks], [1] * len(mocks))

    def test_helpers_are_called_in_expected_order(self) -> None:
        names = (
            "_build_persisted_race_result", "_analyze_result_coverage", "_build_result_completeness",
            "_analyze_result_entry_semantics", "_apply_result_entry_semantics",
            "_analyze_result_race_status_semantics", "_apply_result_race_status_semantics",
        )
        events: list[str] = []
        patches = []
        for name in names:
            original = getattr(result_provider, name)
            def wrapped(*args, _original=original, _name=name, **kwargs):
                events.append(_name)
                return _original(*args, **kwargs)
            patches.append(patch.object(result_provider, name, side_effect=wrapped))
        for item in patches:
            item.start()
        try:
            self._build()
        finally:
            for item in reversed(patches):
                item.stop()
        self.assertEqual(events, list(names))

    def test_fails_without_partial_output_when_aggregate_fails(self) -> None:
        self._assert_stage_failure("_build_persisted_race_result")

    def test_fails_without_partial_output_when_coverage_fails(self) -> None:
        self._assert_stage_failure("_analyze_result_coverage")

    def test_fails_without_partial_output_when_completeness_fails(self) -> None:
        self._assert_stage_failure("_build_result_completeness")

    def test_fails_without_partial_output_when_entry_semantics_fails(self) -> None:
        self._assert_stage_failure("_analyze_result_entry_semantics")

    def test_fails_without_partial_output_when_race_status_semantics_fails(self) -> None:
        self._assert_stage_failure("_analyze_result_race_status_semantics")

    def _assert_stage_failure(self, name: str) -> None:
        with patch.object(result_provider, name, side_effect=ValueError(name)):
            with self.assertRaises(ProviderValidationError) as caught:
                self._build()
        self.assertIsInstance(caught.exception.__cause__, ValueError)

    def test_rejects_invalid_raw_through_existing_boundary(self) -> None:
        with self.assertRaises(ProviderValidationError):
            _build_race_result_provider_output(None, self.context, self.universe)

    def test_rejects_invalid_context_through_existing_boundary(self) -> None:
        with self.assertRaises(ProviderValidationError):
            _build_race_result_provider_output(self._raw(), None, self.universe)

    def test_rejects_invalid_universe_through_existing_boundary(self) -> None:
        with self.assertRaises(ProviderValidationError):
            _build_race_result_provider_output(self._raw(), self.context, None)

    def test_does_not_mutate_raw_context_or_universe(self) -> None:
        raw = self._raw()
        before = (raw, self.context, self.universe)
        self._build(raw)
        self.assertEqual((raw, self.context, self.universe), before)

    def test_does_not_write_stdout_or_stderr(self) -> None:
        stdout, stderr = StringIO(), StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            self._build()
        self.assertEqual((stdout.getvalue(), stderr.getvalue()), ("", ""))

    def test_has_no_database_repository_or_network_dependency(self) -> None:
        path = Path(__file__).parents[1] / "scripts/simulation/providers/result_provider.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
        forbidden = ("sqlite3", "requests", "httpx", "urllib", "selenium", "playwright", "scripts.simulation.repositories.sqlite")
        self.assertFalse(any(name.startswith(forbidden) for name in imports))

    def test_internal_helper_is_not_exposed_from_provider_package(self) -> None:
        import scripts.simulation.providers as providers
        self.assertFalse(hasattr(providers, "_build_race_result_provider_output"))

    def test_does_not_define_concrete_provider_class(self) -> None:
        classes = [node.name for node in ast.walk(ast.parse((Path(__file__).parents[1] / "scripts/simulation/providers/result_provider.py").read_text(encoding="utf-8"))) if isinstance(node, ast.ClassDef)]
        self.assertNotIn("ConcreteRaceResultProvider", classes)
        self.assertNotIn("ResultProvider", classes)

    def test_does_not_save_result(self) -> None:
        names = _build_race_result_provider_output.__code__.co_names
        self.assertFalse(any("save" in name.lower() for name in names))
