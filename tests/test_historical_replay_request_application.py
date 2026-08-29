from __future__ import annotations

import ast
import inspect
from pathlib import Path
from typing import get_type_hints
import unittest
from unittest.mock import patch

import scripts.simulation as simulation_package
import scripts.simulation.historical_replay_request_application as module
from scripts.simulation.historical_replay_request_document import (
    HistoricalReplayRequestDocument,
)
from scripts.simulation.models import SimulationSummary


class HistoricalReplayRequestApplicationTests(unittest.TestCase):
    def test_public_surface_signature_hints_and_package_boundary_are_exact(self) -> None:
        self.assertEqual(module.__all__, ("run_historical_replay_request",))
        self.assertFalse(hasattr(simulation_package, "run_historical_replay_request"))
        signature = inspect.signature(module.run_historical_replay_request)
        self.assertEqual(tuple(signature.parameters), ("request_path",))
        self.assertTrue(
            all(
                parameter.kind is inspect.Parameter.KEYWORD_ONLY
                for parameter in signature.parameters.values()
            )
        )
        self.assertEqual(
            get_type_hints(module.run_historical_replay_request),
            {
                "request_path": str | Path,
                "return": SimulationSummary,
            },
        )

    def test_loader_and_runner_are_each_called_once_with_exact_identity(self) -> None:
        document = object()
        summary = object()
        request_path = Path("replay.json")
        with (
            patch.object(module, "load_historical_replay_request_document", return_value=document) as loader,
            patch.object(module, "run_sqlite_historical_replay", return_value=summary) as runner,
        ):
            result = module.run_historical_replay_request(request_path=request_path)
        loader.assert_called_once_with(request_path=request_path)
        runner.assert_called_once_with(document=document)
        self.assertIs(result, summary)

    def test_loader_and_runner_exceptions_propagate_unchanged(self) -> None:
        loader_error = RuntimeError("loader")
        with patch.object(
            module,
            "load_historical_replay_request_document",
            side_effect=loader_error,
        ) as loader, patch.object(module, "run_sqlite_historical_replay") as runner:
            with self.assertRaises(RuntimeError) as raised:
                module.run_historical_replay_request(request_path="replay.json")
        self.assertIs(raised.exception, loader_error)
        loader.assert_called_once_with(request_path="replay.json")
        runner.assert_not_called()

        runner_error = RuntimeError("runner")
        document = object()
        with patch.object(
            module,
            "load_historical_replay_request_document",
            return_value=document,
        ) as loader, patch.object(
            module,
            "run_sqlite_historical_replay",
            side_effect=runner_error,
        ) as runner:
            with self.assertRaises(RuntimeError) as raised:
                module.run_historical_replay_request(request_path="replay.json")
        self.assertIs(raised.exception, runner_error)
        loader.assert_called_once_with(request_path="replay.json")
        runner.assert_called_once_with(document=document)

    def test_wrapper_static_ownership_excludes_sqlite_capture_clock_and_settlement_work(self) -> None:
        source = Path(module.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_modules = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        self.assertFalse({"sqlite3", "requests", "httpx", "time"} & imported_modules)
        forbidden = (
            "apply_migrations",
            "load_snapshot_by_identity",
            "execute_and_persist_historical_bet_plans",
            "acquire_and_persist_official_settlement_facts",
            "execute_final_historical_settlement_simulation",
            "datetime.now",
            "datetime.utcnow",
            "time.time",
        )
        for value in forbidden:
            with self.subTest(value=value):
                self.assertNotIn(value, source)

    def test_public_return_annotation_is_not_an_incidental_document_type(self) -> None:
        hints = get_type_hints(module.run_historical_replay_request)
        self.assertIsNot(hints["return"], HistoricalReplayRequestDocument)
