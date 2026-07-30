from __future__ import annotations

import ast
from dataclasses import fields
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
        self.assertEqual(
            [node.name for node in tree.body if isinstance(node, ast.FunctionDef)],
            ["run_persisted_simulation_request"],
        )
        self.assertEqual([node for node in tree.body if isinstance(node, ast.ClassDef)], [])
        self.assertFalse(any(isinstance(node, (ast.Try, ast.ExceptHandler)) for node in ast.walk(tree)))
        forbidden = (
            "argparse", "json", "sqlite3", "apply_migrations", "repository",
            "datetime.now", "date.today", "print(", "logging", "cache", "retry",
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

    def test_empty_file_backed_request_runs_the_real_chain(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            request_path = directory / "request.json"
            request_path.write_text(json.dumps(_request()), encoding="utf-8")

            summary = run_persisted_simulation_request(request_path=request_path)

            self.assertIsInstance(summary, SimulationSummary)
            self.assertEqual(
                {field.name for field in fields(SimulationSummary)} - {"by_bet_type"},
                set(summary.__dataclass_fields__) - {"by_bet_type"},
            )
            self.assertEqual(
                (summary.race_count, summary.bet_count, summary.investment, summary.payout),
                (0, 0, 0, 0),
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
            finally:
                connection.close()

    def test_loader_errors_propagate_without_translation(self) -> None:
        with self.assertRaises(FileNotFoundError):
            run_persisted_simulation_request(request_path=Path("missing-request.json"))


if __name__ == "__main__":
    unittest.main()
