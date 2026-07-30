from __future__ import annotations

import ast
import argparse
from collections.abc import Sequence
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
from typing import TextIO, get_type_hints
import unittest

from scripts.migrations.runner import apply_migrations
import scripts.cli as cli_package
from scripts.cli.run_persisted_simulation import _encode_json, _summary_payload, build_parser, main, run
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


def _empty_summary() -> SimulationSummary:
    return SimulationSummary(
        strategy_id="empty-strategy-id",
        strategy_name="empty-strategy-name",
        strategy_config_hash="b" * 64,
        race_count=0,
        settled_race_count=0,
        unsettled_race_count=0,
        no_bet_race_count=0,
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
        by_bet_type={},
    )


def _assert_exact_json_line(test_case: unittest.TestCase, output: str) -> None:
    test_case.assertEqual(output.count("\n"), 1)
    test_case.assertTrue(output.endswith("\n"))
    test_case.assertFalse(output.endswith("\n\n"))
    test_case.assertEqual(output.splitlines(), [output.rstrip("\n")])


def _two_bet_type_summary() -> SimulationSummary:
    first = BetTypeSummary("ワイド", 1, 1, 0, 100, 0, -100, Decimal("0"), Decimal("0"))
    second = BetTypeSummary("単勝", 1, 1, 1, 100, 300, 200, Decimal("300"), Decimal("100"))
    return SimulationSummary(
        strategy_id="ordered-strategy-id", strategy_name="ordered-strategy-name",
        strategy_config_hash="c" * 64, race_count=1, settled_race_count=1,
        unsettled_race_count=0, no_bet_race_count=0, void_race_count=0,
        error_race_count=0, unsupported_race_count=0, bet_count=2, settled_bet_count=2,
        settled_purchase_race_count=1, hit_bet_count=1, hit_race_count=1,
        investment=200, payout=300, profit=100, roi=Decimal("150"),
        bet_hit_rate=Decimal("50"), race_hit_rate=Decimal("100"), maximum_drawdown=100,
        by_bet_type={"ワイド": first, "単勝": second},
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
        self.assertIs(signature.parameters["argv"].kind, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        self.assertIsNone(signature.parameters["argv"].default)
        self.assertTrue(all(
            signature.parameters[name].kind is inspect.Parameter.KEYWORD_ONLY
            and signature.parameters[name].default is None
            for name in ("stdout", "stderr")
        ))
        hints = get_type_hints(run)
        self.assertEqual(hints["argv"], Sequence[str] | None)
        self.assertEqual(hints["stdout"], TextIO | None)
        self.assertEqual(hints["stderr"], TextIO | None)
        self.assertEqual(hints["return"], int)
        module = inspect.getmodule(run)
        self.assertIsNotNone(module)
        source = inspect.getsource(module)
        tree = ast.parse(source)
        self.assertEqual(
            [node.name for node in tree.body if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")],
            ["build_parser", "run", "main"],
        )
        self.assertEqual([node for node in tree.body if isinstance(node, ast.ClassDef)], [])
        self.assertFalse(hasattr(cli_package, "run"))
        self.assertFalse(hasattr(cli_package, "build_parser"))
        self.assertFalse(hasattr(cli_package, "main"))
        self.assertEqual(inspect.signature(build_parser).parameters, {})
        self.assertEqual(get_type_hints(build_parser)["return"], argparse.ArgumentParser)
        self.assertEqual(inspect.signature(main).parameters, {})
        self.assertEqual(get_type_hints(main)["return"], int)
        handlers = [node for node in ast.walk(tree) if isinstance(node, ast.ExceptHandler)]
        self.assertEqual(len(handlers), 1)
        self.assertEqual(
            ast.unparse(handlers[0].type),
            "(OSError, RuntimeError, TypeError, ValueError, sqlite3.Error)",
        )
        self.assertNotIn("apply_migrations", source)
        self.assertNotIn("sqlite3.connect", source)
        self.assertNotIn("load_persisted_simulation_request_document", source)
        self.assertNotIn("build_sqlite_persisted_simulation_run_service", source)
        self.assertFalse(any(
            isinstance(node, ast.Name)
            and node.id in {"Any", "cast", "runtime_checkable"}
            for node in ast.walk(tree)
        ))
        self.assertNotIn("# type: ignore", source)
        self.assertEqual(ast.parse(source, type_comments=True).type_ignores, [])
        forbidden_calls = {
            "load_persisted_simulation_request_document",
            "assemble_persisted_simulation_application_inputs",
            "assemble_persisted_simulation_race_inputs",
            "run_sqlite_persisted_simulation",
            "apply_migrations",
        }
        direct_calls = {
            node.func.id for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertFalse(forbidden_calls & direct_calls)
        application_calls = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id == "run_persisted_simulation_request"
        ]
        self.assertEqual(len(application_calls), 1)
        self.assertEqual(len([node for node in ast.walk(tree) if isinstance(node, ast.Try)]), 1)
        main_node = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
        main_body = main_node.body[1:] if ast.get_docstring(main_node) is not None else main_node.body
        self.assertEqual(len(main_body), 1)
        self.assertIsInstance(main_body[0], ast.Return)
        self.assertEqual(ast.unparse(main_body[0].value), "run()")

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

    def test_serializer_null_rates_order_and_compact_json(self) -> None:
        payload = _summary_payload(_summary())
        encoded_first = _encode_json({"schema_version": 1, "status": "ok", "summary": payload})
        encoded_second = _encode_json({"schema_version": 1, "status": "ok", "summary": payload})
        decoded = json.loads(encoded_first)
        self.assertEqual(encoded_first, encoded_second)
        self.assertNotIn("\\u", encoded_first)
        self.assertNotIn(": ", encoded_first)
        self.assertNotIn(", ", encoded_first)
        self.assertEqual(
            list(decoded["summary"]["by_bet_type"]),
            sorted(decoded["summary"]["by_bet_type"]),
        )
        empty_payload = _summary_payload(_empty_summary())
        self.assertIsNone(empty_payload["roi"])
        self.assertIsNone(empty_payload["bet_hit_rate"])
        self.assertIsNone(empty_payload["race_hit_rate"])

    def test_multi_bet_type_summary_uses_sorted_payload_keys(self) -> None:
        payload = _summary_payload(_two_bet_type_summary())
        self.assertEqual(list(payload["by_bet_type"]), ["ワイド", "単勝"])
        self.assertEqual(list(payload["by_bet_type"]), sorted(payload["by_bet_type"]))
        for key, value in payload["by_bet_type"].items():
            self.assertEqual(set(value), {field.name for field in fields(BetTypeSummary)})
            self.assertEqual(value["bet_type"], key)
            self.assertIsInstance(value["roi"], str)
            self.assertIsInstance(value["bet_hit_rate"], str)

    def test_empty_file_backed_request_writes_success_to_stdout_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            request_path = directory / "request.json"
            request_path.write_text(json.dumps(_request()), encoding="utf-8")
            stdout, stderr = io.StringIO(), io.StringIO()
            self.assertEqual(run([str(request_path)], stdout=stdout, stderr=stderr), 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(stderr.getvalue(), "")
            _assert_exact_json_line(self, stdout.getvalue())
            self.assertTrue(stdout.getvalue().endswith("\n"))
            self.assertEqual(
                (
                    payload["summary"]["race_count"], payload["summary"]["settled_race_count"],
                    payload["summary"]["unsettled_race_count"], payload["summary"]["no_bet_race_count"],
                    payload["summary"]["void_race_count"], payload["summary"]["error_race_count"],
                    payload["summary"]["unsupported_race_count"], payload["summary"]["bet_count"],
                    payload["summary"]["settled_bet_count"], payload["summary"]["settled_purchase_race_count"],
                    payload["summary"]["hit_bet_count"], payload["summary"]["hit_race_count"],
                    payload["summary"]["investment"], payload["summary"]["payout"], payload["summary"]["profit"],
                    payload["summary"]["roi"], payload["summary"]["bet_hit_rate"], payload["summary"]["race_hit_rate"],
                    payload["summary"]["maximum_drawdown"], payload["summary"]["by_bet_type"],
                ),
                (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, None, None, None, 0, {}),
            )
            self.assertTrue((directory / "simulation.db").is_file())
            connection = sqlite3.connect(directory / "simulation.db")
            try:
                self.assertIsNotNone(connection.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_migrations'",
                ).fetchone())
                self.assertIsNotNone(connection.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='simulation_bet_plans'",
                ).fetchone())
                self.assertEqual(connection.execute("SELECT 1").fetchone(), (1,))
            finally:
                connection.close()

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

    def test_settled_summary_contains_complete_approved_values(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            database_path = directory / "simulation.db"
            connection = sqlite3.connect(database_path)
            try:
                connection.execute("CREATE TABLE races (id INTEGER PRIMARY KEY)")
                connection.execute("CREATE TABLE horses (id INTEGER PRIMARY KEY, race_id INTEGER NOT NULL, horse_no INTEGER NOT NULL)")
                connection.execute("INSERT INTO races (id) VALUES (101)")
                connection.execute("INSERT INTO horses (id, race_id, horse_no) VALUES (1011, 101, 1)")
                connection.commit()
                apply_migrations(connection)
                SQLiteRaceResultRepository(connection).save_race_result(PersistedRaceResult(
                    race_id=101, result_status=RaceResultStatus.COMPLETE,
                    finalized_at=datetime(2026, 8, 5, 14, 0, tzinfo=UTC),
                    observed_at=datetime(2026, 8, 5, 14, 1, tzinfo=UTC), source="fixture",
                    entries=(PersistedRaceResultEntry(1, 1011, 1, RaceResultEntryStatus.CONFIRMED),),
                ))
                SQLitePayoutRepository(connection).save_payout_publication(PayoutPublication(
                    race_id=101, bet_type="単勝", is_complete=True,
                    finalized_at=datetime(2026, 8, 5, 14, 10, tzinfo=UTC),
                    observed_at=datetime(2026, 8, 5, 14, 11, tzinfo=UTC), source="fixture",
                    entries=(PayoutRecord((1011,), 300, PayoutStatus.WINNING),),
                ))
                connection.commit()
            finally:
                connection.close()
            request_path = directory / "request.json"
            request_path.write_text(json.dumps(_settled_request()), encoding="utf-8")
            stdout, stderr = io.StringIO(), io.StringIO()
            self.assertEqual(run([str(request_path)], stdout=stdout, stderr=stderr), 0)
            self.assertEqual(stderr.getvalue(), "")
            summary = json.loads(stdout.getvalue())["summary"]
            self.assertEqual(
                (
                    summary["race_count"], summary["settled_race_count"], summary["unsettled_race_count"],
                    summary["no_bet_race_count"], summary["void_race_count"], summary["error_race_count"],
                    summary["unsupported_race_count"], summary["bet_count"], summary["settled_bet_count"],
                    summary["settled_purchase_race_count"], summary["hit_bet_count"], summary["hit_race_count"],
                    summary["investment"], summary["payout"], summary["profit"], summary["roi"],
                    summary["bet_hit_rate"], summary["race_hit_rate"], summary["maximum_drawdown"],
                ),
                (1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 100, 300, 200, "300", "100", "100", 0),
            )
            self.assertEqual(set(summary["by_bet_type"]), {"単勝"})
            bet_type = summary["by_bet_type"]["単勝"]
            self.assertEqual(bet_type["bet_type"], "単勝")
            self.assertEqual(set(bet_type), {field.name for field in fields(BetTypeSummary)})
            self.assertEqual(
                (
                    bet_type["bet_count"], bet_type["settled_bet_count"], bet_type["hit_bet_count"],
                    bet_type["investment"], bet_type["payout"], bet_type["profit"], bet_type["roi"], bet_type["bet_hit_rate"],
                ),
                (1, 1, 1, 100, 300, 200, "300", "100"),
            )
            verification = sqlite3.connect(database_path)
            try:
                self.assertEqual(verification.execute("SELECT COUNT(*) FROM simulation_bet_plans").fetchone(), (1,))
                self.assertEqual(verification.execute("SELECT 1").fetchone(), (1,))
            finally:
                verification.close()

    def test_expected_errors_are_stderr_json_only(self) -> None:
        stdout, stderr = io.StringIO(), io.StringIO()
        self.assertEqual(run(["missing-request.json"], stdout=stdout, stderr=stderr), 1)
        self.assertEqual(stdout.getvalue(), "")
        _assert_exact_json_line(self, stderr.getvalue())
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
                    _assert_exact_json_line(self, stderr.getvalue())
                    payload = json.loads(stderr.getvalue())
                    self.assertEqual((payload["schema_version"], payload["status"]), (1, "error"))
                    self.assertEqual(payload["error"]["type"], exception_name)
                    self.assertTrue(payload["error"]["message"])
                    self.assertNotIn("traceback", stderr.getvalue().lower())
                    self.assertNotIn("stack trace", stderr.getvalue().lower())

            reopened = sqlite3.connect(future_database)
            try:
                self.assertEqual(reopened.execute("SELECT 1").fetchone(), (1,))
            finally:
                reopened.close()

    def test_native_argparse_help_and_argument_errors_remain_system_exit(self) -> None:
        with self.assertRaises(SystemExit) as missing:
            with redirect_stderr(io.StringIO()):
                run([])
        self.assertEqual(missing.exception.code, 2)
        with self.assertRaises(SystemExit) as extra:
            with redirect_stderr(io.StringIO()):
                run(["request.json", "extra"])
        self.assertEqual(extra.exception.code, 2)
        with self.assertRaises(SystemExit) as help_exit:
            with redirect_stdout(io.StringIO()):
                run(["--help"])
        self.assertEqual(help_exit.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
