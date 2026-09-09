"""Whole-day NAR replay orchestrator contract tests."""

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import datetime, timezone
import inspect
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import scripts.simulation.nar_daily_replay_orchestrator as subject
from scripts.simulation.historical_daily_evidence_resolution import (
    DailyHistoricalReplayEvidenceDisposition,
    DailyHistoricalReplayEvidenceResolution,
)
from scripts.simulation.models import SimulationSummary
from scripts.simulation.nar_daily_target_live_acquisition import (
    NARDailyTargetLiveAcquisitionResult,
)
from scripts.simulation.stake_allocation import BetStakeBudget
from tests.test_historical_daily_replay_manifest_projection import (
    _outcome,
    _resolution,
    _run_context,
    _strategy,
    _target,
)


def _acquisition(resolution: DailyHistoricalReplayEvidenceResolution) -> NARDailyTargetLiveAcquisitionResult:
    return NARDailyTargetLiveAcquisitionResult(
        target_date=resolution.target_set.target_date,
        homepage_supplier_capture_id="supplier-home",
        monthly_root_supplier_capture_id="supplier-root",
        locator_script_supplier_capture_id="supplier-script",
        supplier_evidence_identity="supplier-evidence",
        monthly_capture_id="monthly-capture",
        race_list_capture_ids=("race-list-1",),
        target_set=resolution.target_set,
    )


def _summary(count: int, strategy: object) -> SimulationSummary:
    return SimulationSummary(
        strategy_id=strategy.strategy_id,
        strategy_name=strategy.strategy_name,
        strategy_config_hash=strategy.strategy_config_hash,
        race_count=count,
        settled_race_count=0,
        unsettled_race_count=0,
        no_bet_race_count=count,
        void_race_count=0,
        error_race_count=0,
        unsupported_race_count=0,
        bet_count=0,
        settled_bet_count=0,
        settled_purchase_race_count=0,
        hit_bet_count=0,
        hit_race_count=0,
        investment=0,
        payout=0,
        profit=0,
        roi=None,
        bet_hit_rate=None,
        race_hit_rate=None,
        maximum_drawdown=0,
    )


class NARDailyReplayOrchestratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.database_path = self.root / "main.sqlite3"
        self.archive_path = self.root / "settlement.sqlite3"
        self.snapshot_connection = sqlite3.connect(self.database_path)
        self.capture_connection = sqlite3.connect(self.archive_path)
        self.addCleanup(self.snapshot_connection.close)
        self.addCleanup(self.capture_connection.close)
        self.strategy = _strategy()
        self.run_context = _run_context()
        self.cutoff = datetime(2025, 1, 2, 3, 4, 5, 654321, tzinfo=timezone.utc)
        self.budget = BetStakeBudget(total_amount=1000)
        self.manifest_path = self.root / "daily.json"

    def _values(self, resolution: DailyHistoricalReplayEvidenceResolution) -> dict[str, object]:
        return {
            "acquisition_result": _acquisition(resolution),
            "dataset_id": "dataset-1",
            "settlement_information_cutoff": self.cutoff,
            "snapshot_connection": self.snapshot_connection,
            "capture_connection": self.capture_connection,
            "database_path": self.database_path,
            "nar_settlement_capture_archive_path": self.archive_path,
            "run_context": self.run_context,
            "strategy_identity": self.strategy,
            "race_budget": self.budget,
            "manifest_source_path": self.manifest_path,
        }

    def _all_resolution(self, count: int = 2) -> DailyHistoricalReplayEvidenceResolution:
        targets = tuple(_target(f"{index:02d}") for index in range(1, count + 1))
        return _resolution(
            targets,
            tuple(_outcome(target, index) for index, target in enumerate(targets, 1)),
        )

    def _partial_resolution(self) -> DailyHistoricalReplayEvidenceResolution:
        first, second = _target("01"), _target("02")
        return _resolution(
            (first, second),
            (_outcome(first, 1), _outcome(second, 2, executable=False)),
        )

    def _none_resolution(self) -> DailyHistoricalReplayEvidenceResolution:
        first, second = _target("01"), _target("02")
        return _resolution(
            (first, second),
            (
                _outcome(first, 1, executable=False),
                _outcome(second, 2, executable=False),
            ),
        )

    def test_public_surface_signature_fields_and_immutability(self) -> None:
        self.assertEqual(subject.__all__, (
            "NARDailyReplayExecutionState",
            "NARDailyReplayOrchestrationResult",
            "compute_nar_daily_replay_orchestration_audit_sha256",
            "run_nar_daily_replay",
        ))
        self.assertEqual(
            {name for name in vars(subject) if not name.startswith("_")},
            set(subject.__all__),
        )
        self.assertEqual(
            tuple(field.name for field in fields(subject.NARDailyReplayOrchestrationResult)),
            (
                "acquisition_result",
                "resolution",
                "execution_state",
                "manifest_projection",
                "manifest_sha256",
                "summary",
                "orchestration_audit_sha256",
            ),
        )
        signature = inspect.signature(subject.run_nar_daily_replay)
        self.assertEqual(tuple(signature.parameters), (
            "acquisition_result", "dataset_id", "settlement_information_cutoff",
            "snapshot_connection", "capture_connection", "database_path",
            "nar_settlement_capture_archive_path", "run_context", "strategy_identity",
            "race_budget", "manifest_source_path",
        ))
        self.assertTrue(all(
            value.kind is inspect.Parameter.KEYWORD_ONLY
            for value in signature.parameters.values()
        ))

    def test_public_audit_verifier_reuses_exact_phase25_identity(self) -> None:
        resolution = self._partial_resolution()
        values = self._values(resolution)
        with patch.object(subject, "_resolve_evidence", return_value=resolution):
            result = subject.run_nar_daily_replay(**values)
        audit = subject.compute_nar_daily_replay_orchestration_audit_sha256(
            acquisition_result=result.acquisition_result,
            resolution=result.resolution,
            execution_state=result.execution_state,
            manifest_sha256=result.manifest_sha256,
            database_path=values["database_path"],
            nar_settlement_capture_archive_path=values[
                "nar_settlement_capture_archive_path"
            ],
            run_context=values["run_context"],
            strategy_identity=values["strategy_identity"],
            race_budget=values["race_budget"],
            manifest_source_path=values["manifest_source_path"],
        )
        self.assertEqual(audit, result.orchestration_audit_sha256)
        changed = subject.compute_nar_daily_replay_orchestration_audit_sha256(
            acquisition_result=result.acquisition_result,
            resolution=result.resolution,
            execution_state=result.execution_state,
            manifest_sha256=result.manifest_sha256,
            database_path=values["database_path"],
            nar_settlement_capture_archive_path=values[
                "nar_settlement_capture_archive_path"
            ],
            run_context=values["run_context"],
            strategy_identity=values["strategy_identity"],
            race_budget=values["race_budget"],
            manifest_source_path=self.root / "changed.json",
        )
        self.assertNotEqual(changed, audit)

    def test_full_day_reuses_exact_components_document_and_paths_once(self) -> None:
        resolution = self._all_resolution()
        values = self._values(resolution)
        expected_summary = _summary(2, self.strategy)
        original_writer = subject._write_manifest
        with (
            patch.object(subject, "_resolve_evidence", return_value=resolution) as resolver,
            patch.object(subject, "_write_manifest", wraps=original_writer) as writer,
            patch.object(subject, "_run_replay", return_value=expected_summary) as runner,
        ):
            result = subject.run_nar_daily_replay(**values)

        self.assertEqual(result.execution_state, subject.NARDailyReplayExecutionState.FULL_DAY_REPLAY_COMPLETED)
        self.assertIs(result.acquisition_result, values["acquisition_result"])
        self.assertIs(result.resolution, resolution)
        self.assertEqual(result.summary, expected_summary)
        self.assertEqual(result.canonical_target_count, 2)
        self.assertEqual(result.executable_count, 2)
        self.assertRegex(result.manifest_sha256, r"[0-9a-f]{64}\Z")
        self.assertTrue(self.manifest_path.is_file())
        resolver.assert_called_once_with(
            target_set=values["acquisition_result"].target_set,
            dataset_id=values["dataset_id"],
            settlement_information_cutoff=values["settlement_information_cutoff"],
            snapshot_connection=self.snapshot_connection,
            capture_connection=self.capture_connection,
        )
        writer.assert_called_once_with(
            resolution=resolution,
            database_path=self.database_path,
            nar_capture_archive_path=self.archive_path,
            run_context=self.run_context,
            strategy_identity=self.strategy,
            race_budget=self.budget,
            manifest_source_path=self.manifest_path,
        )
        runner.assert_called_once_with(document=result.manifest_projection.document)
        self.assertIs(runner.call_args.kwargs["document"], result.manifest_projection.document)

    def test_partial_and_none_are_diagnostic_only(self) -> None:
        for resolution, state in (
            (self._partial_resolution(), subject.NARDailyReplayExecutionState.NOT_RUN_PARTIAL_RESOLUTION),
            (self._none_resolution(), subject.NARDailyReplayExecutionState.NOT_RUN_NO_EXECUTABLE_TARGETS),
        ):
            with self.subTest(state=state):
                with (
                    patch.object(subject, "_resolve_evidence", return_value=resolution),
                    patch.object(subject, "_write_manifest") as writer,
                    patch.object(subject, "_run_replay") as runner,
                ):
                    result = subject.run_nar_daily_replay(**self._values(resolution))
                    self.assertEqual(result.execution_state, state)
                    self.assertIsNone(result.manifest_projection)
                    self.assertIsNone(result.manifest_sha256)
                    self.assertIsNone(result.summary)
                    self.assertFalse(self.manifest_path.exists())
                    writer.assert_not_called()
                    runner.assert_not_called()

    def test_correct_bindings_and_same_file_alias_pass_without_transaction(self) -> None:
        resolution = self._none_resolution()
        alias_parent = self.root / "alias"
        alias_parent.mkdir()
        database_alias = alias_parent / ".." / self.database_path.name
        values = self._values(resolution)
        values["database_path"] = database_alias
        with patch.object(subject, "_resolve_evidence", return_value=resolution):
            result = subject.run_nar_daily_replay(**values)
        self.assertEqual(result.execution_state, subject.NARDailyReplayExecutionState.NOT_RUN_NO_EXECUTABLE_TARGETS)
        self.assertFalse(self.snapshot_connection.in_transaction)
        self.assertFalse(self.capture_connection.in_transaction)

    def test_wrong_binding_fails_before_any_component(self) -> None:
        resolution = self._none_resolution()
        other = self.root / "other.sqlite3"
        sqlite3.connect(other).close()
        values = self._values(resolution)
        values["database_path"] = other
        with (
            patch.object(subject, "_resolve_evidence") as resolver,
            patch.object(subject, "_write_manifest") as writer,
            patch.object(subject, "_run_replay") as runner,
            self.assertRaises(ValueError),
        ):
            subject.run_nar_daily_replay(**values)
        resolver.assert_not_called()
        writer.assert_not_called()
        runner.assert_not_called()

    def test_wrong_archive_binding_fails_closed(self) -> None:
        resolution = self._none_resolution()
        values = self._values(resolution)
        values["nar_settlement_capture_archive_path"] = self.database_path
        with patch.object(subject, "_resolve_evidence") as resolver, self.assertRaises(ValueError):
            subject.run_nar_daily_replay(**values)
        resolver.assert_not_called()

    def test_attached_in_memory_missing_and_active_transaction_are_rejected(self) -> None:
        resolution = self._none_resolution()
        attached = self.root / "attached.sqlite3"
        self.snapshot_connection.execute("ATTACH DATABASE ? AS attached", (str(attached),))
        with patch.object(subject, "_resolve_evidence") as resolver, self.assertRaises(ValueError):
            subject.run_nar_daily_replay(**self._values(resolution))
        resolver.assert_not_called()
        self.snapshot_connection.execute("DETACH DATABASE attached")

        memory = sqlite3.connect(":memory:")
        self.addCleanup(memory.close)
        values = self._values(resolution)
        values["snapshot_connection"] = memory
        with patch.object(subject, "_resolve_evidence") as resolver, self.assertRaises(ValueError):
            subject.run_nar_daily_replay(**values)
        resolver.assert_not_called()

        values = self._values(resolution)
        values["database_path"] = self.root / "missing.sqlite3"
        with self.assertRaises(ValueError):
            subject.run_nar_daily_replay(**values)

        self.snapshot_connection.execute("BEGIN")
        with patch.object(subject, "_resolve_evidence") as resolver, self.assertRaises(ValueError):
            subject.run_nar_daily_replay(**self._values(resolution))
        resolver.assert_not_called()
        self.snapshot_connection.rollback()

    def test_pragma_failure_propagates_before_resolution(self) -> None:
        resolution = self._none_resolution()
        self.snapshot_connection.set_authorizer(
            lambda action, *_: sqlite3.SQLITE_DENY
            if action == sqlite3.SQLITE_PRAGMA
            else sqlite3.SQLITE_OK
        )
        with patch.object(subject, "_resolve_evidence") as resolver, self.assertRaises(sqlite3.DatabaseError):
            subject.run_nar_daily_replay(**self._values(resolution))
        resolver.assert_not_called()

    def test_empty_sqlite_filename_and_non_file_expected_path_are_rejected(self) -> None:
        resolution = self._none_resolution()
        temporary_database = sqlite3.connect("")
        self.addCleanup(temporary_database.close)
        values = self._values(resolution)
        values["snapshot_connection"] = temporary_database
        with patch.object(subject, "_resolve_evidence") as resolver, self.assertRaises(ValueError):
            subject.run_nar_daily_replay(**values)
        resolver.assert_not_called()

        values = self._values(resolution)
        values["database_path"] = self.root
        with self.assertRaises(ValueError):
            subject.run_nar_daily_replay(**values)

    def test_manifest_mutation_and_runner_failure_leave_manifest(self) -> None:
        resolution = self._all_resolution(1)
        values = self._values(resolution)
        original_writer = subject._write_manifest

        def mutate(*, document: object) -> SimulationSummary:
            self.manifest_path.write_bytes(self.manifest_path.read_bytes() + b" ")
            return _summary(1, self.strategy)

        with (
            patch.object(subject, "_resolve_evidence", return_value=resolution),
            patch.object(subject, "_write_manifest", wraps=original_writer),
            patch.object(subject, "_run_replay", side_effect=mutate),
            self.assertRaises(ValueError),
        ):
            subject.run_nar_daily_replay(**values)
        self.assertTrue(self.manifest_path.exists())

        self.manifest_path.unlink()
        original_bytes: bytes | None = None

        def replace_path(*, document: object) -> SimulationSummary:
            nonlocal original_bytes
            original_bytes = self.manifest_path.read_bytes()
            self.manifest_path.unlink()
            self.manifest_path.write_bytes(original_bytes)
            return _summary(1, self.strategy)

        with (
            patch.object(subject, "_resolve_evidence", return_value=resolution),
            patch.object(subject, "_write_manifest", wraps=original_writer),
            patch.object(subject, "_run_replay", side_effect=replace_path),
            self.assertRaises(ValueError),
        ):
            subject.run_nar_daily_replay(**values)
        self.assertEqual(self.manifest_path.read_bytes(), original_bytes)

        self.manifest_path.unlink()
        error = RuntimeError("runner failed")
        with (
            patch.object(subject, "_resolve_evidence", return_value=resolution),
            patch.object(subject, "_write_manifest", wraps=original_writer),
            patch.object(subject, "_run_replay", side_effect=error),
            self.assertRaisesRegex(RuntimeError, "runner failed"),
        ):
            subject.run_nar_daily_replay(**values)
        self.assertTrue(self.manifest_path.exists())

    def test_invalid_summary_type_count_and_strategy_fail_closed(self) -> None:
        resolution = self._all_resolution(1)
        original_writer = subject._write_manifest
        invalid_values = (
            object(),
            _summary(2, self.strategy),
            replace(_summary(1, self.strategy), strategy_name="different"),
        )
        for index, invalid in enumerate(invalid_values):
            with self.subTest(index=index):
                path = self.root / f"invalid-{index}.json"
                values = self._values(resolution)
                values["manifest_source_path"] = path
                with (
                    patch.object(subject, "_resolve_evidence", return_value=resolution),
                    patch.object(subject, "_write_manifest", wraps=original_writer),
                    patch.object(subject, "_run_replay", return_value=invalid),
                    self.assertRaises(ValueError),
                ):
                    subject.run_nar_daily_replay(**values)
                self.assertTrue(path.exists())

    def test_diagnostic_audit_digest_is_deterministic_and_binds_semantics(self) -> None:
        resolution = self._partial_resolution()
        values = self._values(resolution)
        with patch.object(subject, "_resolve_evidence", return_value=resolution):
            first = subject.run_nar_daily_replay(**values)
            second = subject.run_nar_daily_replay(**values)
            changed_values = dict(values)
            changed_values["manifest_source_path"] = self.root / "other-manifest.json"
            changed = subject.run_nar_daily_replay(**changed_values)
        self.assertEqual(first.orchestration_audit_sha256, second.orchestration_audit_sha256)
        self.assertNotEqual(first.orchestration_audit_sha256, changed.orchestration_audit_sha256)
        self.assertRegex(first.orchestration_audit_sha256, r"[0-9a-f]{64}\Z")
        with self.assertRaises(FrozenInstanceError):
            first.summary = object()

    def test_acquisition_semantic_change_changes_audit_digest(self) -> None:
        resolution = self._none_resolution()
        values = self._values(resolution)
        with patch.object(subject, "_resolve_evidence", return_value=resolution):
            first = subject.run_nar_daily_replay(**values)
            values["acquisition_result"] = replace(
                values["acquisition_result"],
                monthly_capture_id="monthly-capture-changed",
            )
            second = subject.run_nar_daily_replay(**values)
        self.assertNotEqual(first.orchestration_audit_sha256, second.orchestration_audit_sha256)

    def test_input_validation_occurs_before_resolution(self) -> None:
        resolution = self._none_resolution()
        cases = (
            ("dataset_id", "other"),
            ("settlement_information_cutoff", datetime(2025, 1, 2)),
            ("database_path", Path("relative.sqlite3")),
            ("manifest_source_path", Path("relative.json")),
            ("strategy_identity", object()),
            ("race_budget", object()),
        )
        for name, value in cases:
            with self.subTest(name=name):
                values = self._values(resolution)
                values[name] = value
                with patch.object(subject, "_resolve_evidence") as resolver, self.assertRaises(ValueError):
                    subject.run_nar_daily_replay(**values)
                resolver.assert_not_called()

    def test_distinct_connections_are_required(self) -> None:
        resolution = self._none_resolution()
        values = self._values(resolution)
        values["capture_connection"] = self.snapshot_connection
        values["nar_settlement_capture_archive_path"] = self.database_path
        with patch.object(subject, "_resolve_evidence") as resolver, self.assertRaises(ValueError):
            subject.run_nar_daily_replay(**values)
        resolver.assert_not_called()

        second_connection = sqlite3.connect(self.database_path)
        self.addCleanup(second_connection.close)
        values = self._values(resolution)
        values["capture_connection"] = second_connection
        values["nar_settlement_capture_archive_path"] = self.database_path
        with patch.object(subject, "_resolve_evidence") as resolver, self.assertRaises(ValueError):
            subject.run_nar_daily_replay(**values)
        resolver.assert_not_called()

    def test_exact_caller_alias_path_reaches_phase16_without_rewrite(self) -> None:
        resolution = self._all_resolution(1)
        alias_parent = self.root / "alias-for-phase16"
        alias_parent.mkdir()
        alias = alias_parent / ".." / self.database_path.name
        values = self._values(resolution)
        values["database_path"] = alias
        original_writer = subject._write_manifest
        with (
            patch.object(subject, "_resolve_evidence", return_value=resolution),
            patch.object(subject, "_write_manifest", wraps=original_writer) as writer,
            patch.object(subject, "_run_replay", return_value=_summary(1, self.strategy)),
        ):
            result = subject.run_nar_daily_replay(**values)
        self.assertEqual(result.manifest_projection.document.database_path, alias)
        self.assertEqual(writer.call_args.kwargs["database_path"], alias)

    def test_phase14_transaction_change_fails_before_manifest_and_runner(self) -> None:
        resolution = self._none_resolution()

        def alter_transaction(**_: object) -> DailyHistoricalReplayEvidenceResolution:
            self.snapshot_connection.execute("BEGIN")
            return resolution

        with (
            patch.object(subject, "_resolve_evidence", side_effect=alter_transaction),
            patch.object(subject, "_write_manifest") as writer,
            patch.object(subject, "_run_replay") as runner,
            self.assertRaises(ValueError),
        ):
            subject.run_nar_daily_replay(**self._values(resolution))
        writer.assert_not_called()
        runner.assert_not_called()
        self.snapshot_connection.rollback()

    def test_resolution_must_retain_exact_target_set_and_inputs(self) -> None:
        resolution = self._none_resolution()
        other = self._none_resolution()
        values = self._values(resolution)
        with patch.object(subject, "_resolve_evidence", return_value=other), self.assertRaises(ValueError):
            subject.run_nar_daily_replay(**values)

    def test_projection_document_must_retain_exact_full_day_inputs(self) -> None:
        resolution = self._all_resolution(1)
        values = self._values(resolution)
        original_writer = subject._write_manifest

        def contradictory(**kwargs: object) -> object:
            projection = original_writer(**kwargs)
            return replace(projection, resolution=self._all_resolution(1))

        with (
            patch.object(subject, "_resolve_evidence", return_value=resolution),
            patch.object(subject, "_write_manifest", side_effect=contradictory),
            patch.object(subject, "_run_replay") as runner,
            self.assertRaises(ValueError),
        ):
            subject.run_nar_daily_replay(**values)
        runner.assert_not_called()

    def test_static_boundary_has_only_approved_pragma_and_no_forbidden_calls(self) -> None:
        path = Path(subject.__file__)
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        execute_calls = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "execute"
        ]
        self.assertEqual(len(execute_calls), 1)
        self.assertEqual(ast.literal_eval(execute_calls[0].args[0]), "PRAGMA database_list")
        forbidden_attributes = {"executemany", "executescript", "acquire", "now", "utcnow"}
        self.assertFalse(any(
            isinstance(node, ast.Attribute) and node.attr in forbidden_attributes
            for node in ast.walk(tree)
        ))
        forbidden_imports = {
            "requests", "httpx", "urllib", "urllib.request",
        }
        imported = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        self.assertTrue(imported.isdisjoint(forbidden_imports))
        self.assertNotIn("apply_migrations", source)
        self.assertNotIn("NARDailyTargetLiveAcquisitionApplication", source)


if __name__ == "__main__":
    unittest.main()
