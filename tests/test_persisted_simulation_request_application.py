from __future__ import annotations

import ast
import inspect
import json
from pathlib import Path
import sqlite3
import tempfile
from typing import get_type_hints
import unittest

import scripts.simulation as simulation_package
from scripts.simulation.models import SimulationSummary
from scripts.simulation.persisted_simulation_request_application import (
    run_persisted_simulation_request,
)


def _request(*, database_path: str = "simulation.db") -> dict[str, object]:
    return {
        "schema_version": 1,
        "database_path": database_path,
        "run_context": {
            "run_id": "request-application-run",
            "dataset_id": "request-application-dataset",
            "started_at": "2026-08-05T12:30:00+09:00",
            "target_commit_id": "request-application-commit",
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


class PersistedSimulationRequestApplicationTests(unittest.TestCase):
    def test_public_api_and_source_boundary(self) -> None:
        module = inspect.getmodule(run_persisted_simulation_request)
        self.assertIsNotNone(module)
        self.assertEqual(
            run_persisted_simulation_request.__module__,
            "scripts.simulation.persisted_simulation_request_application",
        )
        signature = inspect.signature(run_persisted_simulation_request)
        self.assertEqual(tuple(signature.parameters), ("request_path",))
        self.assertIs(
            signature.parameters["request_path"].kind,
            inspect.Parameter.KEYWORD_ONLY,
        )
        hints = get_type_hints(run_persisted_simulation_request)
        self.assertEqual(hints["request_path"], str | Path)
        self.assertIs(hints["return"], SimulationSummary)
        self.assertFalse(hasattr(simulation_package, "run_persisted_simulation_request"))

        source = inspect.getsource(module)
        tree = ast.parse(source)
        self.assertEqual([node.name for node in tree.body if isinstance(node, ast.FunctionDef)], ["run_persisted_simulation_request"])
        self.assertEqual([node for node in tree.body if isinstance(node, ast.ClassDef)], [])
        self.assertFalse(any(isinstance(node, (ast.Try, ast.ExceptHandler)) for node in ast.walk(tree)))
        forbidden = (
            "argparse", "json", "sys", "logging", "sqlite3", "apply_migrations", "repository",
            "datetime.now", "datetime.utcnow", "date.today", "print(", "cache", "retry",
            "subprocess", "requests", "main.py", "config/settings.json", "os.environ",
            "sorted(", "list(", "tuple(", "copy(", "deepcopy(",
        )
        self.assertFalse(any(fragment in source for fragment in forbidden))
        calls = [
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        ]
        self.assertEqual(calls.count("load_persisted_simulation_request_document"), 1)
        self.assertEqual(calls.count("assemble_persisted_simulation_application_inputs"), 1)
        self.assertEqual(calls.count("assemble_persisted_simulation_race_inputs"), 1)
        self.assertEqual(calls.count("run_sqlite_persisted_simulation"), 1)

        function = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "run_persisted_simulation_request"
        )
        body = function.body[1:] if ast.get_docstring(function) is not None else function.body
        self.assertEqual(len(body), 4)
        self.assertTrue(all(isinstance(node, ast.Assign) for node in body[:3]))
        self.assertIsInstance(body[3], ast.Return)
        self.assertEqual([node.targets[0].id for node in body[:3]], [
            "document", "application_inputs", "race_inputs",
        ])
        calls_by_statement = [
            next(node.value for node in ast.walk(statement) if isinstance(node, ast.Assign))
            for statement in body[:3]
        ]
        self.assertEqual(
            [call.func.id for call in calls_by_statement if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)],
            [
                "load_persisted_simulation_request_document",
                "assemble_persisted_simulation_application_inputs",
                "assemble_persisted_simulation_race_inputs",
            ],
        )
        self.assertEqual(
            [{keyword.arg: ast.unparse(keyword.value) for keyword in call.keywords} for call in calls_by_statement],
            [
                {"request_path": "request_path"},
                {"document": "document"},
                {"document": "document", "application_inputs": "application_inputs"},
            ],
        )
        self.assertIsInstance(body[3].value, ast.Call)
        runner_call = body[3].value
        self.assertIsInstance(runner_call.func, ast.Name)
        self.assertEqual(runner_call.func.id, "run_sqlite_persisted_simulation")
        self.assertEqual(
            {keyword.arg: ast.unparse(keyword.value) for keyword in runner_call.keywords},
            {
                "database_path": "application_inputs.database_path",
                "run_context": "application_inputs.run_context",
                "strategy_identity": "application_inputs.strategy_identity",
                "prediction_pipeline": "application_inputs.prediction_pipeline",
                "race_inputs": "race_inputs",
                "budgets_by_race_id": "application_inputs.budgets_by_race_id",
            },
        )

    def test_empty_file_backed_request_runs_the_real_chain(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            request_path = directory / "request.json"
            request_path.write_text(json.dumps(_request()), encoding="utf-8")

            summary = run_persisted_simulation_request(request_path=request_path)

            self.assertIsInstance(summary, SimulationSummary)
            self.assertEqual(
                (
                    summary.race_count, summary.settled_race_count,
                    summary.unsettled_race_count, summary.no_bet_race_count,
                    summary.void_race_count, summary.error_race_count,
                    summary.unsupported_race_count, summary.bet_count,
                    summary.settled_bet_count, summary.settled_purchase_race_count,
                    summary.hit_bet_count, summary.hit_race_count, summary.investment,
                    summary.payout, summary.profit, summary.roi, summary.bet_hit_rate,
                    summary.race_hit_rate, summary.maximum_drawdown, summary.by_bet_type,
                ),
                (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, None, None, None, 0, {}),
            )
            database_path = directory / "simulation.db"
            self.assertTrue(database_path.is_file())
            connection = sqlite3.connect(database_path)
            try:
                self.assertIsNotNone(
                    connection.execute(
                        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_migrations'",
                    ).fetchone(),
                )
                self.assertIsNotNone(
                    connection.execute(
                        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='simulation_bet_plans'",
                    ).fetchone(),
                )
                self.assertEqual(connection.execute("SELECT 1").fetchone(), (1,))
            finally:
                connection.close()

    def test_loader_errors_propagate_without_translation(self) -> None:
        with self.assertRaises(FileNotFoundError):
            run_persisted_simulation_request(request_path=Path("missing-request.json"))


if __name__ == "__main__":
    unittest.main()
