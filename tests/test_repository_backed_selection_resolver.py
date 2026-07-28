"""Tests for the concrete race-entry selection Resolver boundary."""

from __future__ import annotations

import ast
from collections.abc import Mapping as AbstractMapping
import inspect
from typing import Mapping, Sequence, get_type_hints
import unittest

import scripts.simulation as simulation_package
import scripts.simulation.repository_backed_selection_resolver as resolver_module
from scripts.simulation.race_entry_source import RaceEntrySource
from scripts.simulation.repository_backed_selection_resolver import (
    RepositoryBackedRaceEntrySelectionResolver,
)
from scripts.simulation.repositories.errors import (
    RepositoryConflictError,
    RepositoryDataIntegrityError,
    RepositoryValidationError,
)
from scripts.simulation.selection_resolver import RaceEntrySelectionResolver


class RecordingSource:
    def __init__(self, response: object) -> None:
        self._response = response
        self.calls: list[tuple[int, Sequence[int]]] = []

    def load_race_entry_id_map(
        self,
        *,
        race_id: int,
        horse_ids: Sequence[int],
    ) -> Mapping[int, int]:
        self.calls.append((race_id, horse_ids))
        if isinstance(self._response, BaseException):
            raise self._response
        return self._response  # type: ignore[return-value]


class MissingMethodSource:
    pass


class NonCallableMethodSource:
    load_race_entry_id_map = 1


class StaticMethodSource:
    calls: list[tuple[int, Sequence[int]]] = []

    @staticmethod
    def load_race_entry_id_map(
        *,
        race_id: int,
        horse_ids: Sequence[int],
    ) -> Mapping[int, int]:
        StaticMethodSource.calls.append((race_id, horse_ids))
        return {horse_id: horse_id + 100 for horse_id in horse_ids}


class ValueAccessCountingMapping(AbstractMapping[int, int]):
    def __init__(self, values: Mapping[int, int]) -> None:
        self._values = dict(values)
        self.value_accesses: list[int] = []

    def __getitem__(self, horse_id: int) -> int:
        self.value_accesses.append(horse_id)
        return self._values[horse_id]

    def __iter__(self):
        return iter(self._values)

    def __len__(self) -> int:
        return len(self._values)


class RepositoryBackedRaceEntrySelectionResolverTests(unittest.TestCase):
    def test_constructor_is_keyword_only(self) -> None:
        signature = inspect.signature(RepositoryBackedRaceEntrySelectionResolver)
        parameter = signature.parameters["race_entry_source"]
        self.assertEqual(parameter.kind, inspect.Parameter.KEYWORD_ONLY)
        self.assertEqual(tuple(signature.parameters), ("race_entry_source",))

    def test_constructor_type_hint_matches_source_protocol(self) -> None:
        hints = get_type_hints(RepositoryBackedRaceEntrySelectionResolver.__init__)
        self.assertIs(hints["race_entry_source"], RaceEntrySource)
        self.assertIs(hints["return"], type(None))

    def test_resolve_signature_matches_selection_resolver_protocol(self) -> None:
        self.assertEqual(
            inspect.signature(RepositoryBackedRaceEntrySelectionResolver.resolve_race_entry_ids),
            inspect.signature(RaceEntrySelectionResolver.resolve_race_entry_ids),
        )
        self.assertEqual(
            get_type_hints(RepositoryBackedRaceEntrySelectionResolver.resolve_race_entry_ids),
            get_type_hints(RaceEntrySelectionResolver.resolve_race_entry_ids),
        )

    def test_constructor_rejects_missing_source_method(self) -> None:
        with self.assertRaises(ValueError):
            RepositoryBackedRaceEntrySelectionResolver(race_entry_source=MissingMethodSource())

    def test_constructor_rejects_non_callable_source_method(self) -> None:
        with self.assertRaises(ValueError):
            RepositoryBackedRaceEntrySelectionResolver(race_entry_source=NonCallableMethodSource())

    def test_constructor_accepts_class_with_static_callable_source_method(self) -> None:
        StaticMethodSource.calls = []
        resolver = RepositoryBackedRaceEntrySelectionResolver(race_entry_source=StaticMethodSource)

        resolved = resolver.resolve_race_entry_ids(race_id=10, horse_ids=(3, 1))

        self.assertEqual(resolved, (103, 101))
        self.assertEqual(StaticMethodSource.calls, [(10, (3, 1))])

    def test_constructor_does_not_call_source(self) -> None:
        source = RecordingSource({1: 101})
        RepositoryBackedRaceEntrySelectionResolver(race_entry_source=source)
        self.assertEqual(source.calls, [])

    def test_valid_call_calls_source_exactly_once(self) -> None:
        source = RecordingSource({1: 101, 2: 102})
        resolver = RepositoryBackedRaceEntrySelectionResolver(race_entry_source=source)

        self.assertEqual(resolver.resolve_race_entry_ids(race_id=10, horse_ids=(1, 2)), (101, 102))
        self.assertEqual(source.calls, [(10, (1, 2))])

    def test_valid_call_passes_defensive_tuple_copy_to_source(self) -> None:
        source = RecordingSource({3: 103, 1: 101})
        resolver = RepositoryBackedRaceEntrySelectionResolver(race_entry_source=source)
        horse_ids = [3, 1]

        resolver.resolve_race_entry_ids(race_id=10, horse_ids=horse_ids)

        passed_horse_ids = source.calls[0][1]
        self.assertIsInstance(passed_horse_ids, tuple)
        self.assertEqual(passed_horse_ids, (3, 1))
        self.assertIsNot(passed_horse_ids, horse_ids)

    def test_does_not_mutate_caller_input(self) -> None:
        source = RecordingSource({3: 103, 1: 101, 2: 102})
        resolver = RepositoryBackedRaceEntrySelectionResolver(race_entry_source=source)
        horse_ids = [3, 1, 2]

        resolver.resolve_race_entry_ids(race_id=10, horse_ids=horse_ids)

        self.assertEqual(horse_ids, [3, 1, 2])

    def test_reconstructs_result_in_original_horse_id_order(self) -> None:
        source = RecordingSource({3: 103, 7: 107, 9: 109})
        resolver = RepositoryBackedRaceEntrySelectionResolver(race_entry_source=source)

        resolved = resolver.resolve_race_entry_ids(race_id=10, horse_ids=(9, 3, 7))

        self.assertEqual(resolved, (109, 103, 107))

    def test_reads_each_mapping_value_once_for_a_successful_result(self) -> None:
        mapping = ValueAccessCountingMapping({3: 103, 1: 101, 2: 102})
        source = RecordingSource(mapping)
        resolver = RepositoryBackedRaceEntrySelectionResolver(race_entry_source=source)

        resolved = resolver.resolve_race_entry_ids(race_id=10, horse_ids=(3, 1, 2))

        self.assertEqual(resolved, (103, 101, 102))
        self.assertEqual(mapping.value_accesses, [3, 1, 2])
        self.assertEqual(len(source.calls), 1)

    def test_does_not_sort_requested_horse_ids(self) -> None:
        source = RecordingSource({3: 203, 1: 201})
        resolver = RepositoryBackedRaceEntrySelectionResolver(race_entry_source=source)

        resolved = resolver.resolve_race_entry_ids(race_id=10, horse_ids=(3, 1))

        self.assertEqual(resolved, (203, 201))
        self.assertEqual(source.calls, [(10, (3, 1))])

    def test_does_not_use_identity_mapping_shortcut(self) -> None:
        source = RecordingSource({1: 1001, 2: 1002})
        resolver = RepositoryBackedRaceEntrySelectionResolver(race_entry_source=source)

        resolved = resolver.resolve_race_entry_ids(race_id=10, horse_ids=(1, 2))

        self.assertEqual(resolved, (1001, 1002))
        self.assertEqual(len(source.calls), 1)

    def test_rejects_invalid_race_ids_without_calling_source(self) -> None:
        for race_id in (True, 0, -1, 1.5, "1", None):
            with self.subTest(race_id=race_id):
                source = RecordingSource({1: 101})
                resolver = RepositoryBackedRaceEntrySelectionResolver(race_entry_source=source)
                with self.assertRaises(ValueError):
                    resolver.resolve_race_entry_ids(race_id=race_id, horse_ids=(1,))
                self.assertEqual(source.calls, [])

    def test_rejects_non_sequence_horse_collections_without_calling_source(self) -> None:
        for horse_ids in ("1", b"1", bytearray(b"1"), {1: 1}, (item for item in (1,)), 1, None):
            with self.subTest(horse_ids=horse_ids):
                source = RecordingSource({1: 101})
                resolver = RepositoryBackedRaceEntrySelectionResolver(race_entry_source=source)
                with self.assertRaises(ValueError):
                    resolver.resolve_race_entry_ids(race_id=10, horse_ids=horse_ids)
                self.assertEqual(source.calls, [])

    def test_rejects_empty_horse_ids_without_calling_source(self) -> None:
        source = RecordingSource({})
        resolver = RepositoryBackedRaceEntrySelectionResolver(race_entry_source=source)

        with self.assertRaises(ValueError):
            resolver.resolve_race_entry_ids(race_id=10, horse_ids=())

        self.assertEqual(source.calls, [])

    def test_rejects_invalid_horse_ids_without_calling_source(self) -> None:
        for horse_ids in ((True,), (0,), (-1,), (1.5,), ("1",), (None,)):
            with self.subTest(horse_ids=horse_ids):
                source = RecordingSource({1: 101})
                resolver = RepositoryBackedRaceEntrySelectionResolver(race_entry_source=source)
                with self.assertRaises(ValueError):
                    resolver.resolve_race_entry_ids(race_id=10, horse_ids=horse_ids)
                self.assertEqual(source.calls, [])

    def test_rejects_duplicate_horse_ids_without_calling_source(self) -> None:
        source = RecordingSource({1: 101})
        resolver = RepositoryBackedRaceEntrySelectionResolver(race_entry_source=source)

        with self.assertRaises(ValueError):
            resolver.resolve_race_entry_ids(race_id=10, horse_ids=(1, 1))

        self.assertEqual(source.calls, [])

    def test_rejects_non_mapping_source_response(self) -> None:
        source = RecordingSource(((1, 101),))
        resolver = RepositoryBackedRaceEntrySelectionResolver(race_entry_source=source)

        with self.assertRaises(ValueError):
            resolver.resolve_race_entry_ids(race_id=10, horse_ids=(1,))

        self.assertEqual(len(source.calls), 1)

    def test_rejects_missing_requested_key(self) -> None:
        source = RecordingSource({1: 101})
        resolver = RepositoryBackedRaceEntrySelectionResolver(race_entry_source=source)

        with self.assertRaises(ValueError):
            resolver.resolve_race_entry_ids(race_id=10, horse_ids=(1, 2))

    def test_rejects_empty_mapping_as_unresolved_selection(self) -> None:
        source = RecordingSource({})
        resolver = RepositoryBackedRaceEntrySelectionResolver(race_entry_source=source)

        with self.assertRaises(ValueError):
            resolver.resolve_race_entry_ids(race_id=10, horse_ids=(1,))

    def test_rejects_extra_source_key(self) -> None:
        source = RecordingSource({1: 101, 2: 102})
        resolver = RepositoryBackedRaceEntrySelectionResolver(race_entry_source=source)

        with self.assertRaises(ValueError):
            resolver.resolve_race_entry_ids(race_id=10, horse_ids=(1,))

    def test_rejects_invalid_source_keys(self) -> None:
        for mapping in ({True: 101}, {0: 101}, {-1: 101}, {1.5: 101}, {"1": 101}, {None: 101}):
            with self.subTest(mapping=mapping):
                source = RecordingSource(mapping)
                resolver = RepositoryBackedRaceEntrySelectionResolver(race_entry_source=source)
                with self.assertRaises(ValueError):
                    resolver.resolve_race_entry_ids(race_id=10, horse_ids=(1,))

    def test_rejects_invalid_source_values(self) -> None:
        for mapping in ({1: True}, {1: 0}, {1: -1}, {1: 1.5}, {1: "101"}, {1: None}):
            with self.subTest(mapping=mapping):
                source = RecordingSource(mapping)
                resolver = RepositoryBackedRaceEntrySelectionResolver(race_entry_source=source)
                with self.assertRaises(ValueError):
                    resolver.resolve_race_entry_ids(race_id=10, horse_ids=(1,))

    def test_rejects_duplicate_race_entry_ids(self) -> None:
        source = RecordingSource({1: 101, 2: 101})
        resolver = RepositoryBackedRaceEntrySelectionResolver(race_entry_source=source)

        with self.assertRaises(ValueError):
            resolver.resolve_race_entry_ids(race_id=10, horse_ids=(1, 2))

    def test_propagates_repository_validation_error_identity(self) -> None:
        error = RepositoryValidationError("source validation")
        self._assert_source_error_identity(error)

    def test_propagates_repository_data_integrity_error_identity(self) -> None:
        error = RepositoryDataIntegrityError("source integrity")
        self._assert_source_error_identity(error)

    def test_propagates_repository_conflict_error_identity(self) -> None:
        error = RepositoryConflictError("source conflict")
        self._assert_source_error_identity(error)

    def test_propagates_unexpected_source_error_identity(self) -> None:
        error = RuntimeError("source failure")
        self._assert_source_error_identity(error)

    def test_module_has_no_repository_exception_imports(self) -> None:
        tree = ast.parse(inspect.getsource(resolver_module))
        imports = [
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        ] + [
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        ]
        self.assertFalse(any("repositories.errors" in name for name in imports))

    def test_module_has_no_sqlite_builder_or_composition_dependencies(self) -> None:
        source = inspect.getsource(resolver_module)
        for forbidden in (
            "sqlite3",
            "SQLiteRaceEntrySource",
            "SimulationBetPlanBuilder",
            "PersistedSimulationBetSource",
            "database/keiba.db",
            "datetime.now",
            "requests",
            "httpx",
            "cache",
        ):
            self.assertNotIn(forbidden, source)

    def test_module_does_not_runtime_check_source_protocol(self) -> None:
        source = inspect.getsource(RepositoryBackedRaceEntrySelectionResolver.__init__)
        self.assertNotIn("isinstance(race_entry_source, RaceEntrySource)", source)

    def test_simulation_package_does_not_export_concrete_resolver(self) -> None:
        self.assertFalse(hasattr(simulation_package, "RepositoryBackedRaceEntrySelectionResolver"))

    def test_module_does_not_add_target_race_count(self) -> None:
        self.assertNotIn("target_race_count", inspect.getsource(resolver_module))

    def _assert_source_error_identity(self, error: BaseException) -> None:
        source = RecordingSource(error)
        resolver = RepositoryBackedRaceEntrySelectionResolver(race_entry_source=source)

        with self.assertRaises(type(error)) as caught:
            resolver.resolve_race_entry_ids(race_id=10, horse_ids=(1,))

        self.assertIs(caught.exception, error)
        self.assertEqual(len(source.calls), 1)


if __name__ == "__main__":
    unittest.main()
