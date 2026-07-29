from __future__ import annotations

import ast
import inspect
import json
import tempfile
import unittest
from collections.abc import Mapping
from dataclasses import FrozenInstanceError, fields
from pathlib import Path
from types import MappingProxyType
from typing import get_type_hints

import scripts.simulation as simulation_package
from scripts.simulation.persisted_simulation_request_document import (
    PersistedSimulationRequestDocument,
    load_persisted_simulation_request_document,
)


class PersistedSimulationRequestDocumentContractTests(unittest.TestCase):
    def _write_request(
        self,
        directory: Path,
        value: object,
        *,
        name: str = "request.json",
    ) -> Path:
        request_path = directory / name
        request_path.write_text(json.dumps(value), encoding="utf-8")
        return request_path

    def _write_raw_request(self, directory: Path, text: str, *, name: str) -> Path:
        request_path = directory / name
        request_path.write_text(text, encoding="utf-8")
        return request_path

    def _valid_request(self, **changes: object) -> dict[str, object]:
        value: dict[str, object] = {
            "schema_version": 1,
            "database_path": "database/simulation.db",
            "run_context": {"run_id": "run-1", "nested": {"labels": ["a", "b"]}},
            "strategy": {"name": "strategy"},
            "pipeline": {"components": ["ability"]},
            "races": [{"race_id": 101, "entries": [{"horse_id": 10}]}],
            "budgets_by_race_id": {"101": {"amount": 100}},
        }
        value.update(changes)
        return value

    def _direct_document(self, **changes: object) -> PersistedSimulationRequestDocument:
        value: dict[str, object] = {
            "schema_version": 1,
            "source_path": Path("request.json"),
            "database_path": Path("database.db"),
            "run_context": {"nested": {"values": [1]}},
            "strategy": {"name": "strategy"},
            "pipeline": {"components": ["ability"]},
            "races": ({"race_id": 1, "entries": [{"horse_id": 2}]},),
            "budgets_by_race_id": {"1": {"amount": 100}},
        }
        value.update(changes)
        return PersistedSimulationRequestDocument(**value)

    def test_public_api_signature_type_hints_and_frozen_field_order(self) -> None:
        self.assertEqual(
            [field.name for field in fields(PersistedSimulationRequestDocument)],
            [
                "schema_version",
                "source_path",
                "database_path",
                "run_context",
                "strategy",
                "pipeline",
                "races",
                "budgets_by_race_id",
            ],
        )
        self.assertTrue(PersistedSimulationRequestDocument.__dataclass_params__.frozen)
        self.assertEqual(
            get_type_hints(PersistedSimulationRequestDocument),
            {
                "schema_version": int,
                "source_path": Path,
                "database_path": Path,
                "run_context": Mapping[str, object],
                "strategy": Mapping[str, object],
                "pipeline": Mapping[str, object],
                "races": tuple[Mapping[str, object], ...],
                "budgets_by_race_id": Mapping[str, object],
            },
        )
        signature = inspect.signature(load_persisted_simulation_request_document)
        self.assertEqual(list(signature.parameters), ["request_path"])
        self.assertEqual(signature.parameters["request_path"].kind, inspect.Parameter.KEYWORD_ONLY)
        hints = get_type_hints(load_persisted_simulation_request_document)
        self.assertEqual(hints["request_path"], str | Path)
        self.assertIs(hints["return"], PersistedSimulationRequestDocument)

    def test_module_has_only_approved_public_definitions_and_no_package_export(self) -> None:
        module = inspect.getmodule(PersistedSimulationRequestDocument)
        self.assertIsNotNone(module)
        public_classes = [
            name
            for name, value in inspect.getmembers(module, inspect.isclass)
            if value.__module__ == module.__name__ and not name.startswith("_")
        ]
        public_functions = [
            name
            for name, value in inspect.getmembers(module, inspect.isfunction)
            if value.__module__ == module.__name__ and not name.startswith("_")
        ]
        self.assertEqual(public_classes, ["PersistedSimulationRequestDocument"])
        self.assertEqual(public_functions, ["load_persisted_simulation_request_document"])
        self.assertFalse(hasattr(simulation_package, "PersistedSimulationRequestDocument"))
        self.assertFalse(hasattr(simulation_package, "load_persisted_simulation_request_document"))

    def test_valid_document_anchors_path_and_is_deeply_immutable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            request_path = self._write_request(Path(temporary_directory), self._valid_request())
            document = load_persisted_simulation_request_document(request_path=request_path)

            self.assertEqual(document.source_path, request_path)
            self.assertEqual(
                document.database_path,
                request_path.parent / Path("database/simulation.db"),
            )
            self.assertIsInstance(document.run_context, MappingProxyType)
            self.assertIsInstance(document.run_context["nested"], MappingProxyType)
            self.assertIsInstance(document.run_context["nested"]["labels"], tuple)
            self.assertIsInstance(document.races, tuple)
            self.assertIsInstance(document.races[0], MappingProxyType)
            self.assertIsInstance(document.races[0]["entries"], tuple)
            self.assertIsInstance(document.budgets_by_race_id, MappingProxyType)

            with self.assertRaises(TypeError):
                document.run_context["another"] = "value"
            with self.assertRaises(TypeError):
                document.run_context["nested"]["labels"] = ()
            with self.assertRaises(TypeError):
                document.run_context["nested"]["labels"][0] = "changed"
            with self.assertRaises(TypeError):
                document.races[0] = document.races[0]
            with self.assertRaises(TypeError):
                document.races[0]["race_id"] = 2
            with self.assertRaises(TypeError):
                document.budgets_by_race_id["101"]["amount"] = 200
            with self.assertRaises(FrozenInstanceError):
                document.database_path = Path("other.db")

    def test_absolute_path_and_empty_collections_are_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            absolute_database_path = directory / "simulation.db"
            request_path = self._write_request(
                directory,
                self._valid_request(
                    database_path=str(absolute_database_path),
                    races=[],
                    budgets_by_race_id={},
                ),
            )
            document = load_persisted_simulation_request_document(request_path=request_path)

            self.assertEqual(document.database_path, absolute_database_path)
            self.assertEqual(document.races, ())
            self.assertEqual(dict(document.budgets_by_race_id), {})

    def test_direct_constructor_defensively_freezes_valid_json_compatible_values(self) -> None:
        run_context = {"nested": {"values": [1]}}
        races = ({"race_id": 1, "entries": [{"horse_id": 2}]},)
        document = self._direct_document(run_context=run_context, races=races)
        run_context["nested"]["values"].append(2)
        races[0]["entries"][0]["horse_id"] = 3

        self.assertEqual(document.run_context["nested"]["values"], (1,))
        self.assertEqual(document.races[0]["entries"][0]["horse_id"], 2)
        self.assertIsInstance(document.run_context, MappingProxyType)
        self.assertIsInstance(document.races, tuple)

    def test_direct_constructor_validates_schema_paths_mapping_fields_and_races(self) -> None:
        for value in (True, 0, 2, "1"):
            with self.subTest(schema_version=repr(value)):
                with self.assertRaisesRegex(ValueError, "^schema_version must be 1$"):
                    self._direct_document(schema_version=value)

        path_cases = (
            ("source_path", "request.json", "source_path must be a Path"),
            ("source_path", None, "source_path must be a Path"),
            ("database_path", "database.db", "database_path must be a Path"),
            ("database_path", None, "database_path must be a Path"),
        )
        for field_name, value, message in path_cases:
            with self.subTest(field_name=field_name, value=repr(value)):
                with self.assertRaisesRegex(TypeError, f"^{message}$"):
                    self._direct_document(**{field_name: value})

        for field_name in ("run_context", "strategy", "pipeline", "budgets_by_race_id"):
            with self.subTest(field_name=field_name):
                with self.assertRaisesRegex(TypeError, f"^{field_name} must be a Mapping$"):
                    self._direct_document(**{field_name: []})

        for value, message in (([], "races must be a tuple"), ({}, "races must be a tuple"), ((1,), "races must contain Mapping values")):
            with self.subTest(races=repr(value)):
                with self.assertRaisesRegex(TypeError, f"^{message}$"):
                    self._direct_document(races=value)

    def test_direct_constructor_rejects_non_json_mapping_keys_and_values(self) -> None:
        cases = (
            ({1: "invalid"}, "request document mappings must have string keys", TypeError),
            ({"nested": {2: "invalid"}}, "request document mappings must have string keys", TypeError),
            ({"nested": float("inf")}, "request JSON must not contain non-finite numbers", ValueError),
            ({"nested": float("nan")}, "request JSON must not contain non-finite numbers", ValueError),
            ({"nested": object()}, "request document values must be JSON-compatible", TypeError),
        )
        for run_context, message, exception_type in cases:
            with self.subTest(run_context=repr(run_context)):
                with self.assertRaisesRegex(exception_type, f"^{message}$"):
                    self._direct_document(run_context=run_context)

    def test_loader_rejects_invalid_request_paths_before_file_read(self) -> None:
        invalid_values = (
            None,
            b"request.json",
            bytearray(b"request.json"),
            1,
            True,
            object(),
            "",
            "   ",
            "bad\x00path",
            Path("bad\x00path"),
        )
        for invalid_value in invalid_values:
            with self.subTest(value=repr(invalid_value)):
                with self.assertRaisesRegex(ValueError, "^request_path must be a non-empty path$"):
                    load_persisted_simulation_request_document(request_path=invalid_value)

    def test_file_and_encoding_failures_preserve_required_exception_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            with self.assertRaises(FileNotFoundError):
                load_persisted_simulation_request_document(request_path=directory / "missing.json")
            with self.assertRaises(OSError):
                load_persisted_simulation_request_document(request_path=directory)

            invalid_encoding_path = directory / "invalid-encoding.json"
            invalid_encoding_path.write_bytes(b"\xff")
            with self.assertRaisesRegex(ValueError, "^request file must be UTF-8$"):
                load_persisted_simulation_request_document(request_path=invalid_encoding_path)

    def test_invalid_or_malformed_json_has_stable_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            for name, text in (("empty.json", ""), ("broken.json", "{"), ("bom.json", "\ufeff{}")):
                with self.subTest(name=name):
                    path = self._write_raw_request(directory, text, name=name)
                    with self.assertRaisesRegex(ValueError, "^request file must contain valid JSON$"):
                        load_persisted_simulation_request_document(request_path=path)

    def test_duplicate_keys_are_rejected_at_every_object_level(self) -> None:
        documents = (
            '{"schema_version":1,"schema_version":1,"database_path":"x","run_context":{},"strategy":{},"pipeline":{},"races":[],"budgets_by_race_id":{}}',
            '{"schema_version":1,"database_path":"x","run_context":{"x":1,"x":2},"strategy":{},"pipeline":{},"races":[],"budgets_by_race_id":{}}',
            '{"schema_version":1,"database_path":"x","run_context":{},"strategy":{},"pipeline":{},"races":[{"race_id":1,"race_id":2}],"budgets_by_race_id":{}}',
            '{"schema_version":1,"database_path":"x","run_context":{},"strategy":{},"pipeline":{},"races":[],"budgets_by_race_id":{"101":{"amount":100,"amount":200}}}',
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            for index, text in enumerate(documents):
                with self.subTest(index=index):
                    path = self._write_raw_request(directory, text, name=f"duplicate-{index}.json")
                    with self.assertRaisesRegex(ValueError, "^request JSON must not contain duplicate object keys$"):
                        load_persisted_simulation_request_document(request_path=path)

    def test_non_finite_json_numbers_win_over_root_validation(self) -> None:
        documents = (
            '{"schema_version":1,"database_path":"x","run_context":{"x":NaN},"strategy":{},"pipeline":{},"races":[],"budgets_by_race_id":{}}',
            '{"schema_version":1,"database_path":"x","run_context":{},"strategy":{"x":Infinity},"pipeline":{},"races":[],"budgets_by_race_id":{}}',
            '{"schema_version":1,"database_path":"x","run_context":{},"strategy":{},"pipeline":{"x":-Infinity},"races":[],"budgets_by_race_id":{}}',
            '{"schema_version":1,"database_path":"x","run_context":{},"strategy":{},"pipeline":{},"races":[{"x":1e999}],"budgets_by_race_id":{}}',
            "1e999",
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            for index, text in enumerate(documents):
                with self.subTest(index=index):
                    path = self._write_raw_request(directory, text, name=f"non-finite-{index}.json")
                    with self.assertRaisesRegex(ValueError, "^request JSON must not contain non-finite numbers$"):
                        load_persisted_simulation_request_document(request_path=path)

    def test_root_key_schema_and_field_validation_are_strict(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            cases = (
                (None, "request JSON root must be an object"),
                ([], "request JSON root must be an object"),
                ("string", "request JSON root must be an object"),
                (1, "request JSON root must be an object"),
                (True, "request JSON root must be an object"),
                ({}, "request JSON keys must exactly match the request schema"),
                (self._valid_request(extra=True), "request JSON keys must exactly match the request schema"),
                (self._valid_request(schema_version=True), "schema_version must be 1"),
                (self._valid_request(schema_version=0), "schema_version must be 1"),
                (self._valid_request(schema_version=2), "schema_version must be 1"),
                (self._valid_request(schema_version="1"), "schema_version must be 1"),
                (self._valid_request(database_path=None), "database_path must be a non-empty string"),
                (self._valid_request(database_path=1), "database_path must be a non-empty string"),
                (self._valid_request(database_path=True), "database_path must be a non-empty string"),
                (self._valid_request(database_path=[]), "database_path must be a non-empty string"),
                (self._valid_request(database_path={}), "database_path must be a non-empty string"),
                (self._valid_request(database_path=""), "database_path must be a non-empty string"),
                (self._valid_request(database_path="   "), "database_path must be a non-empty string"),
                (self._valid_request(database_path="bad\x00path"), "database_path must be a non-empty string"),
                (self._valid_request(run_context=[]), "run_context must be an object"),
                (self._valid_request(strategy=[]), "strategy must be an object"),
                (self._valid_request(pipeline=[]), "pipeline must be an object"),
                (self._valid_request(budgets_by_race_id=[]), "budgets_by_race_id must be an object"),
                (self._valid_request(races={}), "races must be an array"),
                (self._valid_request(races=[1]), "races must contain objects"),
            )
            for index, (value, message) in enumerate(cases):
                with self.subTest(index=index, message=message):
                    request_path = self._write_request(directory, value, name=f"invalid-{index}.json")
                    with self.assertRaisesRegex(ValueError, f"^{message}$"):
                        load_persisted_simulation_request_document(request_path=request_path)

    def test_reloads_are_independent_at_every_nested_container_level(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            request_path = self._write_request(directory, self._valid_request())
            first_document = load_persisted_simulation_request_document(request_path=request_path)
            self._write_request(directory, self._valid_request(run_context={"run_id": "run-2", "nested": {"labels": ["c"]}}))
            second_document = load_persisted_simulation_request_document(request_path=request_path)

            self.assertEqual(first_document.run_context["run_id"], "run-1")
            self.assertEqual(second_document.run_context["run_id"], "run-2")
            self.assertIsNot(first_document.races, second_document.races)
            self.assertIsNot(first_document.races[0], second_document.races[0])
            self.assertIsNot(first_document.run_context["nested"], second_document.run_context["nested"])
            self.assertIsNot(first_document.pipeline["components"], second_document.pipeline["components"])
            self.assertIsNot(first_document.budgets_by_race_id, second_document.budgets_by_race_id)

    def test_source_stays_within_document_loader_boundary(self) -> None:
        module = inspect.getmodule(PersistedSimulationRequestDocument)
        self.assertIsNotNone(module)
        source = inspect.getsource(module)
        tree = ast.parse(source)
        self.assertNotIn("# type: ignore", source)
        self.assertFalse(tree.type_ignores)
        self.assertIn("class PersistedSimulationRequestDocument", source)
        self.assertIn("def load_persisted_simulation_request_document", source)

        forbidden_fragments = (
            "sqlite3",
            "apply_migrations",
            "run_sqlite_persisted_simulation",
            "build_sqlite_persisted_simulation_run_service",
            "SimulationRunContext",
            "StrategyConfig",
            "StrategyIdentity",
            "PredictionPipeline",
            "SimulationRaceInput",
            "InputSnapshotAudit",
            "PastRace",
            "BetStakeBudget",
            "SimulationSummary",
            "datetime.now",
            "datetime.utcnow",
            "date.today",
            "uuid",
            "subprocess",
            "requests",
            "logging",
            "print(",
            "argparse",
            "os.environ",
            "config/settings.json",
            "main.py",
        )
        self.assertFalse(any(fragment in source for fragment in forbidden_fragments))

        imported_from_typing = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module == "typing"
            for alias in node.names
        }
        self.assertFalse({"Any", "cast", "runtime_checkable"} & imported_from_typing)
        self.assertFalse(
            any(
                isinstance(node, ast.Name)
                and node.id in {"Any", "cast", "runtime_checkable"}
                for node in ast.walk(tree)
            )
        )
        handled_exceptions = [
            ast.unparse(node.type)
            for node in ast.walk(tree)
            if isinstance(node, ast.ExceptHandler) and node.type is not None
        ]
        self.assertEqual(handled_exceptions, ["UnicodeDecodeError", "json.JSONDecodeError"])


if __name__ == "__main__":
    unittest.main()
