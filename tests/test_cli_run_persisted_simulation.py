from __future__ import annotations

import ast
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import fields
from datetime import UTC, datetime
from decimal import Decimal
import inspect
import io
import json
from pathlib import Path
import sqlite3
import tempfile
from typing import get_type_hints
import unittest

from scripts.migrations.runner import apply_migrations
from scripts.cli.run_persisted_simulation import _encode_json, _summary_payload, build_parser, run
from scripts.simulation.models import BetTypeSummary, SimulationSummary
from scripts.simulation.repositories.interfaces import (
    PayoutPublication,
    PayoutRecord,
    PayoutStatus,
    PersistedRaceResult,
    PersistedRaceResultEntry,
    RaceResultEntryStatus,
    RaceResultStatus,
)
from scripts.simulation.repositories.sqlite import (
    SQLitePayoutRepository,
    SQLiteRaceResultRepository,
)


def _request(*, database_path: str = "simulation.db") -> dict[str, object]:
    return {
        "schema_version": 1,
        "database_path": database_path,
        "run_context": {
            "run_id": "cli-run",
            "dataset_id": "cli-dataset",
            "started_at": "2026-08-05T12:30:00+09:00",
            "target_commit_id": "cli-commit",
        },
        "strategy": {
            "strategy_name": "RuleBasedBetStrategy",
            "allowed_bet_types": [],
            "max_bet_count": 3,
            "selection_style": "formation",
            "min_combination_score": 0.0,
            "max_candidates": 5,
            "sort_condition": "generator_rank",
            "allocation_policy": {
                "policy_name": "fixed_stake_per_recommendation",
                "policy_version": "1",
                "parameters": {"stake_amount": 100},
            },
        },
        "pipeline": {"track_reference_date": "2026-08-05"},
        "races": [],
        "budgets_by_race_id": {},
    }


def _stamp(source_id: str) -> dict[str, object]:
    return {
        "source": "fixture",
        "source_id": source_id,
        "available_at": "2026-08-05T12:00:00+09:00",
        "observed_at": "2026-08-05T12:01:00+09:00",
    }


def _settled_request() -> dict[str, object]:
    request = _request()
    request["strategy"] = {
        **request["strategy"],
        "allowed_bet_types": ["単勝"],
    }
    request["races"] = [{
        "race_id": 101,
        "target_race_date": "2026-08-05",
        "scheduled_start_at": "2026-08-05T15:40:00+09:00",
        "information_cutoff": "2026-08-05T15:30:00+09:00",
        "audit": {
            "source": "fixture",
            "captured_at": "2026-08-05T12:10:00+09:00",
            "is_complete": True,
        },
        "track_conditions": {
            "place": "Tokyo",
            "distance": 1600,
            "track": "turf",
            "track_condition": "good",
            "audit": _stamp("track-101"),
        },
        "entries": [{
            "race_entry_id": 1011,
            "jockey_name": "Fixture Jockey",
            "odds": 2.0,
            "past_races": [],
            "audits": {
                "entry": _stamp("entry-1011"),
                "jockey": _stamp("jockey-1011"),
                "odds": _stamp("odds-1011"),
                "past_race_absence": _stamp("absence-1011"),
            },
        }],
    }]
    request["budgets_by_race_id"] = {"101": {"total_amount": 100}}
    return request


def _summary() -> SimulationSummary:
    bet_type = BetTypeSummary(
        bet_type="単勝",
        bet_count=1,
        settled_bet_count=1,
        hit_bet_count=1,
        investment=100,
        payout=300,
        profit=200,
        roi=Decimal("300"),
        bet_hit_rate=Decimal("100"),
    )
    return SimulationSummary(
        strategy_id="strategy-id",
        strategy_name="strategy-name",
        strategy_config_hash="a" * 64,
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
        payout=300,
        profit=200,
        roi=Decimal("300"),
        bet_hit_rate=Decimal("100"),
        race_hit_rate=Decimal("100"),
        maximum_drawdown=0,
        by_bet_type={"単勝": bet_type},
    )


class PersistedSimulationCliTests(unittest.TestCase):
    def test_public_api_parser_and_source_boundary(self) -> None:
        parser = build_parser()
        self.assertEqual(len(parser._actions), 2)
        action = parser._actions[-1]
        self.assertEqual((action.dest, action.type, action.help), (
            "request_path", Path, "Persisted simulation request JSON path",
        ))
        signature = inspect.signature(run)
        self.assertEqual(tuple(signature.parameters), ("argv", "stdout", "stderr"))
        hints = get_type_hints(run)
        self.assertEqual(hints["return"], int)
        module = inspect.getmodule(run)
        self.assertIsNotNone(module)
        source = inspect.getsource(module)
        tree = ast.parse(source)
        handlers = [node for node in ast.walk(tree) if isinstance(node, ast.ExceptHandler)]
        self.assertEqual(len(handlers), 1)
        self.assertEqual(
            ast.unparse(handlers[0].type),
            "(OSError, RuntimeError, TypeError, ValueError, sqlite3.Error)",
        )
        self.assertNotIn("apply_migrations", source)
        self.assertNotIn("load_persisted_simulation_request_document", source)
        self.assertNotIn("build_sqlite_persisted_simulation_run_service", source)

    def test_success_serializer_is_compact_deterministic_and_preserves_decimals(self) -> None:
        envelope = {
            "schema_version": 1,
            "status": "ok",
            "summary": _summary_payload(_summary()),
        }
        first = _encode_json(envelope)
        second = _encode_json(envelope)
        self.assertEqual(first, second)
        payload = json.loads(first)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(set(payload["summary"]), {field.name for field in fields(SimulationSummary)})
        self.assertEqual(
            set(payload["summary"]["by_bet_type"]["単勝"]),
            {field.name for field in fields(BetTypeSummary)},
        )
        self.assertEqual(payload["summary"]["roi"], "300")
        self.assertEqual(payload["summary"]["by_bet_type"]["単勝"]["roi"], "300")

    def test_empty_file_backed_request_writes_success_to_stdout_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            request_path = directory / "request.json"
            request_path.write_text(json.dumps(_request()), encoding="utf-8")
            stdout, stderr = io.StringIO(), io.StringIO()
            self.assertEqual(run([str(request_path)], stdout=stdout, stderr=stderr), 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(stderr.getvalue(), "")
            self.assertEqual((payload["summary"]["race_count"], payload["summary"]["bet_count"]), (0, 0))
            self.assertTrue((directory / "simulation.db").is_file())

    def test_settled_file_backed_request_persists_snapshot_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            database_path = directory / "simulation.db"
            connection = sqlite3.connect(database_path)
            try:
                connection.execute("CREATE TABLE races (id INTEGER PRIMARY KEY)")
                connection.execute(
                    "CREATE TABLE horses ("
                    "id INTEGER PRIMARY KEY, race_id INTEGER NOT NULL, horse_no INTEGER NOT NULL)",
                )
                connection.execute("INSERT INTO races (id) VALUES (101)")
                connection.execute(
                    "INSERT INTO horses (id, race_id, horse_no) VALUES (1011, 101, 1)",
                )
                connection.commit()
                apply_migrations(connection)
                SQLiteRaceResultRepository(connection).save_race_result(
                    PersistedRaceResult(
                        race_id=101,
                        result_status=RaceResultStatus.COMPLETE,
                        finalized_at=datetime(2026, 8, 5, 14, 0, tzinfo=UTC),
                        observed_at=datetime(2026, 8, 5, 14, 1, tzinfo=UTC),
                        source="fixture",
                        entries=(PersistedRaceResultEntry(
                            horse_no=1,
                            race_entry_id=1011,
                            finish_position=1,
                            result_status=RaceResultEntryStatus.CONFIRMED,
                        ),),
                    ),
                )
                SQLitePayoutRepository(connection).save_payout_publication(
                    PayoutPublication(
                        race_id=101,
                        bet_type="単勝",
                        finalized_at=datetime(2026, 8, 5, 14, 10, tzinfo=UTC),
                        observed_at=datetime(2026, 8, 5, 14, 11, tzinfo=UTC),
                        is_complete=True,
                        source="fixture",
                        entries=(PayoutRecord((1011,), 300, PayoutStatus.WINNING),),
                    ),
                )
                connection.commit()
            finally:
                connection.close()

            request_path = directory / "request.json"
            request_path.write_text(json.dumps(_settled_request()), encoding="utf-8")
            stdout, stderr = io.StringIO(), io.StringIO()
            self.assertEqual(run([str(request_path)], stdout=stdout, stderr=stderr), 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(stderr.getvalue(), "")
            self.assertEqual(
                (payload["summary"]["race_count"], payload["summary"]["investment"], payload["summary"]["payout"], payload["summary"]["profit"]),
                (1, 100, 300, 200),
            )
            self.assertEqual(payload["summary"]["by_bet_type"]["単勝"]["roi"], "300")
            verification = sqlite3.connect(database_path)
            try:
                self.assertEqual(
                    verification.execute("SELECT COUNT(*) FROM simulation_bet_plans").fetchone(),
                    (1,),
                )
            finally:
                verification.close()

    def test_expected_errors_are_stderr_json_only(self) -> None:
        stdout, stderr = io.StringIO(), io.StringIO()
        self.assertEqual(run(["missing-request.json"], stdout=stdout, stderr=stderr), 1)
        self.assertEqual(stdout.getvalue(), "")
        payload = json.loads(stderr.getvalue())
        self.assertEqual((payload["schema_version"], payload["status"]), (1, "error"))
        self.assertEqual(payload["error"]["type"], "FileNotFoundError")

    def test_loader_assembler_database_and_migration_errors_are_stderr_json_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            cases: list[tuple[str, Path, str]] = []
            malformed = directory / "malformed.json"
            malformed.write_text("{", encoding="utf-8")
            cases.append(("malformed", malformed, "ValueError"))
            root = directory / "root.json"
            root.write_text("[]", encoding="utf-8")
            cases.append(("root", root, "ValueError"))
            application = directory / "application.json"
            invalid_application = _request()
            invalid_application["strategy"] = {}
            application.write_text(json.dumps(invalid_application), encoding="utf-8")
            cases.append(("application", application, "ValueError"))
            race_audit = directory / "race-audit.json"
            invalid_race = _settled_request()
            invalid_race["races"][0]["audit"]["is_complete"] = False
            race_audit.write_text(json.dumps(invalid_race), encoding="utf-8")
            cases.append(("race-audit", race_audit, "SimulationValidationError"))
            directory_path = directory / "database-directory"
            directory_path.mkdir()
            database_open = directory / "database-open.json"
            database_open.write_text(
                json.dumps(_request(database_path="database-directory")),
                encoding="utf-8",
            )
            cases.append(("database-open", database_open, "OperationalError"))
            future_database = directory / "future.db"
            future_connection = sqlite3.connect(future_database)
            try:
                future_connection.execute(
                    "CREATE TABLE schema_migrations ("
                    "version INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_at TEXT NOT NULL)",
                )
                future_connection.execute(
                    "INSERT INTO schema_migrations (version, name, applied_at) "
                    "VALUES (999, 'future_migration', '2026-08-05T00:00:00+00:00')",
                )
                future_connection.commit()
            finally:
                future_connection.close()
            future = directory / "future.json"
            future.write_text(json.dumps(_request(database_path="future.db")), encoding="utf-8")
            cases.append(("future-migration", future, "RuntimeError"))

            for name, request_path, exception_name in cases:
                with self.subTest(name=name):
                    stdout, stderr = io.StringIO(), io.StringIO()
                    self.assertEqual(run([str(request_path)], stdout=stdout, stderr=stderr), 1)
                    self.assertEqual(stdout.getvalue(), "")
                    payload = json.loads(stderr.getvalue())
                    self.assertEqual(payload["status"], "error")
                    self.assertEqual(payload["error"]["type"], exception_name)

    def test_native_argparse_help_and_argument_errors_remain_system_exit(self) -> None:
        with self.assertRaises(SystemExit) as missing:
            with redirect_stderr(io.StringIO()):
                run([])
        self.assertEqual(missing.exception.code, 2)
        with self.assertRaises(SystemExit) as help_exit:
            with redirect_stdout(io.StringIO()):
                run(["--help"])
        self.assertEqual(help_exit.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
