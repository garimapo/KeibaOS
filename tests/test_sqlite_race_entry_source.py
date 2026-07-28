"""Tests for the connection-injected SQLiteRaceEntrySource boundary."""

from __future__ import annotations

import ast
import inspect
import sqlite3
from typing import Mapping, Sequence, get_type_hints
import unittest

import scripts.simulation as simulation_package
import scripts.simulation.repositories.sqlite_race_entry_source as source_module
from scripts.simulation.race_entry_source import RaceEntrySource
from scripts.simulation.repositories.errors import (
    RepositoryDataIntegrityError,
    RepositoryValidationError,
)
from scripts.simulation.repositories.sqlite_race_entry_source import SQLiteRaceEntrySource


class _RowsCursor:
    def __init__(self, rows: list[tuple[object, object]]) -> None:
        self._rows = rows

    def fetchall(self) -> list[tuple[object, object]]:
        return self._rows


class _RowsConnection(sqlite3.Connection):
    def __init__(self, rows: list[tuple[object, object]]) -> None:
        super().__init__(":memory:")
        self.rows = rows
        self.source_query_count = 0

    def execute(self, sql: str, parameters: object = ()) -> object:
        if "FROM horses AS h" in sql:
            self.source_query_count += 1
            return _RowsCursor(self.rows)
        return super().execute(sql, parameters)


class _OperationalErrorConnection(sqlite3.Connection):
    def __init__(self, error: sqlite3.OperationalError) -> None:
        super().__init__(":memory:")
        self.error = error

    def execute(self, sql: str, parameters: object = ()) -> object:
        if "FROM horses AS h" in sql:
            raise self.error
        return super().execute(sql, parameters)


def connection_with_horses() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE horses (id INTEGER PRIMARY KEY, race_id INTEGER NOT NULL)")
    connection.executemany(
        "INSERT INTO horses (id, race_id) VALUES (?, ?)",
        ((1, 10), (2, 10), (3, 10), (4, 20)),
    )
    connection.commit()
    return connection


class SQLiteRaceEntrySourceConstructionTests(unittest.TestCase):
    def test_constructor_is_keyword_only_and_keeps_connection_identity(self) -> None:
        connection = connection_with_horses()
        source = SQLiteRaceEntrySource(connection=connection)
        self.assertIs(source._connection, connection)
        with self.assertRaises(TypeError):
            SQLiteRaceEntrySource(connection)  # type: ignore[call-arg]

    def test_rejects_non_sqlite_connection(self) -> None:
        with self.assertRaises(RepositoryValidationError):
            SQLiteRaceEntrySource(connection=object())  # type: ignore[arg-type]

    def test_rejects_closed_sqlite_connection_with_cause(self) -> None:
        connection = connection_with_horses()
        connection.close()
        with self.assertRaises(RepositoryValidationError) as captured:
            SQLiteRaceEntrySource(connection=connection)
        self.assertIsInstance(captured.exception.__cause__, sqlite3.Error)

    def test_enables_foreign_keys_without_changing_connection_configuration(self) -> None:
        connection = connection_with_horses()
        row_factory = sqlite3.Row
        connection.row_factory = row_factory
        isolation_level = connection.isolation_level
        SQLiteRaceEntrySource(connection=connection)
        self.assertEqual(connection.execute("PRAGMA foreign_keys").fetchone()[0], 1)
        self.assertIs(connection.row_factory, row_factory)
        self.assertEqual(connection.isolation_level, isolation_level)

    def test_is_slotted_without_cache_state(self) -> None:
        source = SQLiteRaceEntrySource(connection=connection_with_horses())
        self.assertFalse(hasattr(source, "__dict__"))
        self.assertEqual(SQLiteRaceEntrySource.__slots__, ("_connection",))


class SQLiteRaceEntrySourceRequestValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = SQLiteRaceEntrySource(connection=connection_with_horses())

    def test_rejects_invalid_race_ids(self) -> None:
        for race_id in (True, 0, -1, 1.0, "10", None):
            with self.subTest(race_id=race_id):
                with self.assertRaises(RepositoryValidationError):
                    self.source.load_race_entry_id_map(race_id=race_id, horse_ids=(1,))  # type: ignore[arg-type]

    def test_rejects_non_sequence_or_text_horse_id_collections(self) -> None:
        for horse_ids in ("1", b"1", bytearray(b"1"), {1: 1}, (item for item in (1,)), 1):
            with self.subTest(horse_ids=horse_ids):
                with self.assertRaises(RepositoryValidationError):
                    self.source.load_race_entry_id_map(race_id=10, horse_ids=horse_ids)  # type: ignore[arg-type]

    def test_rejects_empty_horse_ids(self) -> None:
        with self.assertRaises(RepositoryValidationError):
            self.source.load_race_entry_id_map(race_id=10, horse_ids=())

    def test_rejects_invalid_horse_ids(self) -> None:
        for horse_id in (True, 0, -1, 1.0, "1", None):
            with self.subTest(horse_id=horse_id):
                with self.assertRaises(RepositoryValidationError):
                    self.source.load_race_entry_id_map(race_id=10, horse_ids=(horse_id,))  # type: ignore[arg-type]

    def test_rejects_duplicate_horse_ids(self) -> None:
        with self.assertRaises(RepositoryValidationError):
            self.source.load_race_entry_id_map(race_id=10, horse_ids=(1, 1))

    def test_does_not_mutate_input_list(self) -> None:
        horse_ids = [3, 1]
        result = self.source.load_race_entry_id_map(race_id=10, horse_ids=horse_ids)
        self.assertEqual(horse_ids, [3, 1])
        self.assertEqual(result, {3: 3, 1: 1})


class SQLiteRaceEntrySourceResolutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.connection = connection_with_horses()
        self.source = SQLiteRaceEntrySource(connection=self.connection)

    def test_resolves_requested_horse_ids_in_input_order(self) -> None:
        result = self.source.load_race_entry_id_map(race_id=10, horse_ids=(3, 1, 2))
        self.assertEqual(result, {3: 3, 1: 1, 2: 2})
        self.assertEqual(tuple(result), (3, 1, 2))

    def test_returns_partial_mapping_for_missing_requested_id(self) -> None:
        result = self.source.load_race_entry_id_map(race_id=10, horse_ids=(1, 99))
        self.assertEqual(result, {1: 1})

    def test_returns_empty_mapping_for_wrong_race_id(self) -> None:
        result = self.source.load_race_entry_id_map(race_id=10, horse_ids=(4,))
        self.assertEqual(result, {})

    def test_returns_empty_mapping_for_nonexistent_race(self) -> None:
        result = self.source.load_race_entry_id_map(race_id=999, horse_ids=(1,))
        self.assertEqual(result, {})

    def test_uses_one_batch_select_for_a_multi_horse_request(self) -> None:
        traced: list[str] = []
        self.connection.set_trace_callback(traced.append)
        self.source.load_race_entry_id_map(race_id=10, horse_ids=(1, 2, 3))
        selects = [statement for statement in traced if "FROM horses AS h" in statement]
        self.assertEqual(len(selects), 1)
        self.assertIn("h.id IN (1, 2, 3)", selects[0])

    def test_does_not_issue_separate_race_lookup(self) -> None:
        traced: list[str] = []
        self.connection.set_trace_callback(traced.append)
        self.source.load_race_entry_id_map(race_id=10, horse_ids=(1, 2))
        selects = [statement for statement in traced if statement.lstrip().upper().startswith("SELECT")]
        self.assertEqual(len(selects), 1)

    def test_allows_active_caller_transaction_without_settlement(self) -> None:
        self.connection.execute("BEGIN")
        try:
            result = self.source.load_race_entry_id_map(race_id=10, horse_ids=(1,))
            self.assertEqual(result, {1: 1})
            self.assertTrue(self.connection.in_transaction)
        finally:
            self.connection.rollback()

    def test_does_not_close_connection_or_write_data(self) -> None:
        before = self.connection.total_changes
        self.source.load_race_entry_id_map(race_id=10, horse_ids=(1,))
        self.assertEqual(self.connection.total_changes, before)
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM horses").fetchone()[0], 4)


class SQLiteRaceEntrySourceIntegrityTests(unittest.TestCase):
    def test_rejects_missing_horses_table_as_schema_integrity_error(self) -> None:
        source = SQLiteRaceEntrySource(connection=sqlite3.connect(":memory:"))
        with self.assertRaises(RepositoryDataIntegrityError) as captured:
            source.load_race_entry_id_map(race_id=10, horse_ids=(1,))
        self.assertIsInstance(captured.exception.__cause__, sqlite3.OperationalError)

    def test_rejects_type_invalid_horses_row(self) -> None:
        source = SQLiteRaceEntrySource(connection=_RowsConnection(rows=[("one", "one")]))
        with self.assertRaises(RepositoryDataIntegrityError):
            source.load_race_entry_id_map(race_id=10, horse_ids=(1,))

    def test_rejects_duplicate_source_rows(self) -> None:
        connection = _RowsConnection(rows=[(1, 1), (1, 1)])
        source = SQLiteRaceEntrySource(connection=connection)
        with self.assertRaises(RepositoryDataIntegrityError):
            source.load_race_entry_id_map(race_id=10, horse_ids=(1,))
        self.assertEqual(connection.source_query_count, 1)

    def test_rejects_extra_source_row(self) -> None:
        connection = _RowsConnection(rows=[(2, 2)])
        source = SQLiteRaceEntrySource(connection=connection)
        with self.assertRaises(RepositoryDataIntegrityError):
            source.load_race_entry_id_map(race_id=10, horse_ids=(1,))

    def test_rejects_duplicate_race_entry_mapping_value(self) -> None:
        connection = _RowsConnection(rows=[(1, 9), (2, 9)])
        source = SQLiteRaceEntrySource(connection=connection)
        with self.assertRaises(RepositoryDataIntegrityError):
            source.load_race_entry_id_map(race_id=10, horse_ids=(1, 2))

    def test_propagates_unexpected_sqlite_operational_error_unchanged(self) -> None:
        error = sqlite3.OperationalError("database is locked")
        source = SQLiteRaceEntrySource(connection=_OperationalErrorConnection(error))
        with self.assertRaises(sqlite3.OperationalError) as captured:
            source.load_race_entry_id_map(race_id=10, horse_ids=(1,))
        self.assertIs(captured.exception, error)


class SQLiteRaceEntrySourceContractTests(unittest.TestCase):
    def test_matches_race_entry_source_method_signature_and_type_hints(self) -> None:
        self.assertEqual(
            inspect.signature(SQLiteRaceEntrySource.load_race_entry_id_map),
            inspect.signature(RaceEntrySource.load_race_entry_id_map),
        )
        self.assertEqual(
            get_type_hints(SQLiteRaceEntrySource.load_race_entry_id_map),
            get_type_hints(RaceEntrySource.load_race_entry_id_map),
        )

    def test_module_has_only_source_and_repository_boundary_dependencies(self) -> None:
        tree = ast.parse(inspect.getsource(source_module))
        imported_modules = {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        } | {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        self.assertEqual(
            imported_modules,
            {"__future__", "sqlite3", "typing", "scripts.simulation.race_entry_source", "errors"},
        )

    def test_module_does_not_depend_on_composition_or_external_io(self) -> None:
        source = inspect.getsource(source_module)
        for forbidden in (
            "database/keiba.db",
            "sqlite3.connect",
            "RaceEntrySelectionResolver",
            "SimulationBetPlanBuilder",
            "PersistedSimulationBetSource",
            "providers",
            "PredictionPipeline",
            "Simulator",
            "requests",
            "httpx",
            "urllib",
            "socket",
            "datetime.now",
        ):
            self.assertNotIn(forbidden, source)

    def test_module_does_not_manage_transactions_or_cache(self) -> None:
        source = inspect.getsource(source_module)
        for forbidden in ("BEGIN", ".commit(", ".rollback(", ".close(", "cache"):
            self.assertNotIn(forbidden, source)

    def test_is_not_exported_from_simulation_package_root(self) -> None:
        self.assertFalse(hasattr(simulation_package, "SQLiteRaceEntrySource"))

    def test_does_not_add_target_race_count(self) -> None:
        self.assertNotIn("target_race_count", inspect.getsource(source_module))

    def test_no_fixed_database_file_is_referenced(self) -> None:
        self.assertNotIn("keiba.db", inspect.getsource(source_module))


if __name__ == "__main__":
    unittest.main()
