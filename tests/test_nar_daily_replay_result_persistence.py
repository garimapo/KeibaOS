"""Immutable Phase 25 result projection and publication contract tests."""

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import datetime, timezone
from decimal import Decimal
import inspect
from pathlib import Path
import sqlite3
import tempfile
from typing import get_type_hints
import unittest
from unittest.mock import patch

import scripts.simulation.nar_daily_replay_orchestrator as orchestrator
import scripts.simulation.nar_daily_replay_result_persistence as subject
from scripts.migrations.runner import apply_migrations
from scripts.simulation.models import BetTypeSummary, SimulationSummary
from scripts.simulation.nar_daily_replay_orchestrator import NARDailyReplayExecutionState
from scripts.simulation.repositories.errors import (
    RepositoryDataIntegrityError,
    RepositoryValidationError,
)
from scripts.simulation.repositories.sqlite_nar_daily_replay_result_repository import (
    SQLiteNARDailyReplayResultRepository,
)
from scripts.simulation.stake_allocation import BetStakeBudget
from tests.test_historical_daily_replay_manifest_projection import (
    _outcome,
    _resolution,
    _run_context,
    _strategy,
    _target,
)
from tests.test_nar_daily_replay_orchestrator import _acquisition


UTC = timezone.utc


class _MemoryRepository:
    def __init__(self) -> None:
        self.record = None
        self.save_count = 0

    def save_result(self, *, record: subject.PersistedNARDailyReplayResult) -> None:
        self.save_count += 1
        self.record = record

    def load_result(self, *, persisted_content_sha256: str):
        if self.record is None or self.record.persisted_content_sha256 != persisted_content_sha256:
            return None
        return self.record


def _bet_summary() -> BetTypeSummary:
    return BetTypeSummary(
        bet_type="単勝",
        bet_count=1,
        settled_bet_count=1,
        hit_bet_count=1,
        investment=100,
        payout=250,
        profit=150,
        roi=Decimal("250"),
        bet_hit_rate=Decimal("100"),
    )


def _completed_summary(strategy: object, *, maximum_drawdown: int = 25) -> SimulationSummary:
    bet = _bet_summary()
    return SimulationSummary(
        strategy_id=strategy.strategy_id,
        strategy_name=strategy.strategy_name,
        strategy_config_hash=strategy.strategy_config_hash,
        race_count=1,
        settled_race_count=1,
        unsettled_race_count=0,
        no_bet_race_count=0,
        void_race_count=0,
        error_race_count=0,
        unsupported_race_count=0,
        bet_count=1,
        settled_bet_count=1,
        settled_purchase_race_count=1,
        hit_bet_count=1,
        hit_race_count=1,
        investment=100,
        payout=250,
        profit=150,
        roi=Decimal("250"),
        bet_hit_rate=Decimal("100"),
        race_hit_rate=Decimal("100"),
        maximum_drawdown=maximum_drawdown,
        by_bet_type={"単勝": bet},
    )


def _no_bet_summary(strategy: object) -> SimulationSummary:
    return SimulationSummary(
        strategy_id=strategy.strategy_id,
        strategy_name=strategy.strategy_name,
        strategy_config_hash=strategy.strategy_config_hash,
        race_count=1,
        settled_race_count=0,
        unsettled_race_count=0,
        no_bet_race_count=1,
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


def _ensure_database_files(root: Path) -> tuple[Path, Path]:
    database_path = root / "main.sqlite3"
    archive_path = root / "settlement.sqlite3"
    connection = sqlite3.connect(database_path)
    try:
        connection.execute("CREATE TABLE IF NOT EXISTS races(id INTEGER PRIMARY KEY)")
        connection.execute(
            "CREATE TABLE IF NOT EXISTS horses(id INTEGER PRIMARY KEY,race_id INTEGER)"
        )
        connection.commit()
    finally:
        connection.close()
    archive = sqlite3.connect(archive_path)
    archive.close()
    return database_path, archive_path


def build_request(
    root: Path,
    state: NARDailyReplayExecutionState,
    *,
    run_id: str = "daily-run-1",
    manifest_name: str = "manifest.json",
    completed_no_bet: bool = False,
) -> subject.NARDailyReplayResultPersistenceRequest:
    database_path, archive_path = _ensure_database_files(root)
    strategy = _strategy()
    run_context = replace(_run_context(), run_id=run_id)
    cutoff = datetime(2025, 1, 2, 3, 4, 5, 654321, tzinfo=UTC)
    budget = BetStakeBudget(total_amount=1000)
    manifest_path = root / manifest_name
    if state is NARDailyReplayExecutionState.FULL_DAY_REPLAY_COMPLETED:
        target = _target("01")
        resolution = _resolution((target,), (_outcome(target, 1),))
        summary = _no_bet_summary(strategy) if completed_no_bet else _completed_summary(strategy)
    elif state is NARDailyReplayExecutionState.NOT_RUN_PARTIAL_RESOLUTION:
        first, second = _target("01"), _target("02")
        resolution = _resolution(
            (first, second),
            (_outcome(first, 1), _outcome(second, 2, executable=False)),
        )
        summary = None
    else:
        target = _target("01")
        resolution = _resolution((target,), (_outcome(target, 1, executable=False),))
        summary = None
    acquisition = _acquisition(resolution)
    snapshot_connection = sqlite3.connect(database_path)
    capture_connection = sqlite3.connect(archive_path)
    try:
        with (
            patch.object(orchestrator, "_resolve_evidence", return_value=resolution),
            patch.object(orchestrator, "_run_replay", return_value=summary),
        ):
            result = orchestrator.run_nar_daily_replay(
                acquisition_result=acquisition,
                dataset_id="dataset-1",
                settlement_information_cutoff=cutoff,
                snapshot_connection=snapshot_connection,
                capture_connection=capture_connection,
                database_path=database_path,
                nar_settlement_capture_archive_path=archive_path,
                run_context=run_context,
                strategy_identity=strategy,
                race_budget=budget,
                manifest_source_path=manifest_path,
            )
    finally:
        snapshot_connection.close()
        capture_connection.close()
    return subject.NARDailyReplayResultPersistenceRequest(
        orchestration_result=result,
        database_path=database_path,
        nar_settlement_capture_archive_path=archive_path,
        run_context=run_context,
        strategy_identity=strategy,
        race_budget=budget,
        manifest_source_path=manifest_path,
    )


def build_record(
    root: Path,
    state: NARDailyReplayExecutionState,
    *,
    run_id: str = "daily-run-1",
    manifest_name: str = "manifest.json",
    completed_no_bet: bool = False,
) -> subject.PersistedNARDailyReplayResult:
    request = build_request(
        root,
        state,
        run_id=run_id,
        manifest_name=manifest_name,
        completed_no_bet=completed_no_bet,
    )
    return subject._build_record(request)


class NARDailyReplayResultPersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def test_public_surface_request_record_and_immutability(self) -> None:
        self.assertEqual(
            subject.__all__,
            (
                "NARDailyReplayResultPersistenceRequest",
                "PersistedNARDailyReplayResult",
                "persist_nar_daily_replay_result",
            ),
        )
        self.assertEqual(
            {name for name in vars(subject) if not name.startswith("_")},
            set(subject.__all__),
        )
        signature = inspect.signature(subject.persist_nar_daily_replay_result)
        self.assertEqual(tuple(signature.parameters), ("request", "repository"))
        self.assertTrue(
            all(item.kind is inspect.Parameter.KEYWORD_ONLY for item in signature.parameters.values())
        )
        self.assertIs(
            get_type_hints(subject.persist_nar_daily_replay_result)["repository"],
            SQLiteNARDailyReplayResultRepository,
        )
        record = build_record(
            self.root, NARDailyReplayExecutionState.NOT_RUN_NO_EXECUTABLE_TARGETS
        )
        self.assertEqual(fields(record)[-1].name, "persisted_content_sha256")
        with self.assertRaises(FrozenInstanceError):
            record.summary = object()

    def test_public_phase25_verifier_matches_completed_and_diagnostic_results(self) -> None:
        for index, state in enumerate(NARDailyReplayExecutionState):
            with self.subTest(state=state):
                request = build_request(
                    self.root,
                    state,
                    run_id=f"run-{index}",
                    manifest_name=f"manifest-{index}.json",
                )
                result = request.orchestration_result
                computed = orchestrator.compute_nar_daily_replay_orchestration_audit_sha256(
                    acquisition_result=result.acquisition_result,
                    resolution=result.resolution,
                    execution_state=result.execution_state,
                    manifest_sha256=result.manifest_sha256,
                    database_path=request.database_path,
                    nar_settlement_capture_archive_path=request.nar_settlement_capture_archive_path,
                    run_context=request.run_context,
                    strategy_identity=request.strategy_identity,
                    race_budget=request.race_budget,
                    manifest_source_path=request.manifest_source_path,
                )
                self.assertEqual(computed, result.orchestration_audit_sha256)

    def test_request_rejects_every_changed_authoritative_audit_input(self) -> None:
        request = build_request(
            self.root, NARDailyReplayExecutionState.NOT_RUN_PARTIAL_RESOLUTION
        )
        cases = {
            "database_path": self.root / "changed-main.sqlite3",
            "nar_settlement_capture_archive_path": self.root / "changed-archive.sqlite3",
            "run_context": replace(request.run_context, run_id="changed-run"),
            "strategy_identity": _strategy(name="ChangedStrategy"),
            "race_budget": BetStakeBudget(total_amount=2000),
            "manifest_source_path": self.root / "changed-manifest.json",
        }
        for name, value in cases.items():
            with self.subTest(name=name), self.assertRaises(RepositoryValidationError):
                replace(request, **{name: value})

    def test_all_three_states_project_with_exact_artifact_and_summary_rules(self) -> None:
        for index, state in enumerate(NARDailyReplayExecutionState):
            with self.subTest(state=state):
                record = build_record(
                    self.root,
                    state,
                    run_id=f"state-{index}",
                    manifest_name=f"state-{index}.json",
                )
                self.assertEqual(record.execution_state, state)
                if state is NARDailyReplayExecutionState.FULL_DAY_REPLAY_COMPLETED:
                    self.assertIsNotNone(record.summary)
                    self.assertEqual(record.published_manifest_path, record.configured_manifest_source_path)
                    self.assertRegex(record.manifest_sha256, r"[0-9a-f]{64}\Z")
                else:
                    self.assertIsNone(record.summary)
                    self.assertIsNone(record.published_manifest_path)
                    self.assertIsNone(record.manifest_sha256)

    def test_completed_summary_decimal_and_bet_type_content_remain_exact(self) -> None:
        record = build_record(
            self.root, NARDailyReplayExecutionState.FULL_DAY_REPLAY_COMPLETED
        )
        self.assertEqual(record.summary.roi, Decimal("250"))
        self.assertEqual(record.summary.bet_hit_rate, Decimal("100"))
        self.assertEqual(record.summary.race_hit_rate, Decimal("100"))
        self.assertEqual(record.summary.maximum_drawdown, 25)
        self.assertEqual(record.summary.by_bet_type["単勝"], _bet_summary())
        self.assertNotIsInstance(record.summary.roi, float)

    def test_completed_no_bet_is_distinct_from_diagnostic_absence(self) -> None:
        request = build_request(
            self.root,
            NARDailyReplayExecutionState.FULL_DAY_REPLAY_COMPLETED,
            manifest_name="no-bet.json",
            completed_no_bet=True,
        )
        record = subject._build_record(request)
        self.assertIsNotNone(record.summary)
        self.assertEqual(record.summary.investment, 0)
        diagnostic = build_record(
            self.root,
            NARDailyReplayExecutionState.NOT_RUN_NO_EXECUTABLE_TARGETS,
            run_id="diagnostic-run",
            manifest_name="diagnostic.json",
        )
        self.assertIsNone(diagnostic.summary)

    def test_content_sha_is_deterministic_and_binds_summary_and_metadata(self) -> None:
        record = build_record(
            self.root, NARDailyReplayExecutionState.FULL_DAY_REPLAY_COMPLETED
        )
        duplicate = replace(record)
        changed_summary = replace(record.summary, maximum_drawdown=26)
        changed = replace(record, summary=changed_summary)
        changed_metadata = replace(record, race_budget_total_amount=1100)
        self.assertEqual(duplicate.persisted_content_sha256, record.persisted_content_sha256)
        self.assertNotEqual(changed.persisted_content_sha256, record.persisted_content_sha256)
        self.assertNotEqual(
            changed_metadata.persisted_content_sha256, record.persisted_content_sha256
        )

    def test_publication_exact_reloads_and_rejects_missing_or_different_reload(self) -> None:
        request = build_request(
            self.root, NARDailyReplayExecutionState.NOT_RUN_NO_EXECUTABLE_TARGETS
        )
        connection = sqlite3.connect(request.database_path)
        self.addCleanup(connection.close)
        apply_migrations(connection)
        repository = SQLiteNARDailyReplayResultRepository(
            connection=connection,
            database_path=request.database_path,
        )
        loaded = subject.persist_nar_daily_replay_result(
            request=request, repository=repository
        )
        self.assertEqual(
            repository.load_result(
                persisted_content_sha256=loaded.persisted_content_sha256
            ),
            loaded,
        )
        with patch.object(
            SQLiteNARDailyReplayResultRepository,
            "load_result",
            return_value=None,
        ):
            with self.assertRaises(RepositoryDataIntegrityError):
                subject.persist_nar_daily_replay_result(
                    request=request,
                    repository=repository,
                )

    def test_invalid_request_and_repository_fail_closed(self) -> None:
        request = build_request(
            self.root, NARDailyReplayExecutionState.NOT_RUN_NO_EXECUTABLE_TARGETS
        )
        with self.assertRaises(RepositoryValidationError):
            subject.persist_nar_daily_replay_result(request=object(), repository=_MemoryRepository())
        with self.assertRaises(RepositoryValidationError):
            subject.persist_nar_daily_replay_result(
                request=request,
                repository=_MemoryRepository(),
            )
        with self.assertRaises(RepositoryValidationError):
            subject.persist_nar_daily_replay_result(request=request, repository=object())

    def test_static_boundaries_use_public_verifier_and_no_execution_or_clock(self) -> None:
        source = Path(subject.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        self.assertNotIn("_AuditInputs", imported)
        self.assertNotIn("_audit_digest", imported)
        self.assertNotIn("run_nar_daily_replay", imported)
        self.assertNotIn("run_sqlite_historical_replay", imported)
        self.assertFalse(
            any(
                isinstance(node, ast.Attribute)
                and node.attr in {"now", "utcnow", "acquire"}
                for node in ast.walk(tree)
            )
        )
        self.assertNotIn("time.time", source)


if __name__ == "__main__":
    unittest.main()
