"""SQLite v016 immutable NAR daily replay result repository tests."""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path
import sqlite3
import tempfile
import unittest

from scripts.migrations.runner import MIGRATIONS, apply_migrations, get_applied_versions
from scripts.migrations.versions import v016_nar_daily_replay_result_schema as migration
from scripts.simulation.nar_daily_replay_orchestrator import NARDailyReplayExecutionState
from scripts.simulation.nar_daily_replay_result_persistence import (
    persist_nar_daily_replay_result,
)
from scripts.simulation.repositories.errors import (
    RepositoryConflictError,
    RepositoryDataIntegrityError,
    RepositoryValidationError,
)
from scripts.simulation.repositories.sqlite_nar_daily_replay_result_repository import (
    SQLiteNARDailyReplayResultRepository,
)
from tests.test_nar_daily_replay_result_persistence import build_record, build_request


def _restore_header_update_trigger(connection: sqlite3.Connection) -> None:
    connection.execute(
        """CREATE TRIGGER nar_daily_replay_results_no_update
           BEFORE UPDATE ON nar_daily_replay_results
           BEGIN SELECT RAISE(ABORT,'nar daily replay results are immutable'); END"""
    )


def _restore_child_update_trigger(connection: sqlite3.Connection) -> None:
    connection.execute(
        """CREATE TRIGGER nar_daily_replay_result_bet_types_no_update
           BEFORE UPDATE ON nar_daily_replay_result_bet_type_summaries
           BEGIN SELECT RAISE(ABORT,'nar daily replay bet-type summaries are immutable'); END"""
    )


class SQLiteNARDailyReplayResultRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.record = build_record(
            self.root, NARDailyReplayExecutionState.FULL_DAY_REPLAY_COMPLETED
        )
        self.connection = sqlite3.connect(self.record.database_path)
        self.addCleanup(self.connection.close)
        apply_migrations(self.connection)
        self.repository = SQLiteNARDailyReplayResultRepository(
            connection=self.connection,
            database_path=self.record.database_path,
        )

    def _assert_table_schema_mutation_rejected(
        self,
        *,
        name: str,
        table_name: str,
        replacements: tuple[tuple[str, str], ...],
    ) -> None:
        path = self.root / f"malformed-{name}.sqlite3"
        connection = sqlite3.connect(path)
        try:
            connection.execute("CREATE TABLE races(id INTEGER PRIMARY KEY)")
            connection.execute("CREATE TABLE horses(id INTEGER PRIMARY KEY,race_id INTEGER)")
            connection.commit()
            apply_migrations(connection)
            original = connection.execute(
                "SELECT sql FROM sqlite_schema WHERE type='table' AND name=?",
                (table_name,),
            ).fetchone()[0]
            mutated = original
            for old, new in replacements:
                self.assertIn(old, mutated)
                mutated = mutated.replace(old, new, 1)
            self.assertNotEqual(mutated, original)
            connection.execute("PRAGMA writable_schema=ON")
            connection.execute(
                "UPDATE sqlite_schema SET sql=? WHERE type='table' AND name=?",
                (mutated, table_name),
            )
            connection.execute("PRAGMA writable_schema=OFF")
            connection.commit()
        finally:
            connection.close()

        malformed = sqlite3.connect(path)
        self.addCleanup(malformed.close)
        with self.assertRaises(RepositoryDataIntegrityError):
            SQLiteNARDailyReplayResultRepository(
                connection=malformed,
                database_path=path,
            )

    def test_v016_identity_registration_schema_and_idempotent_runner(self) -> None:
        self.assertEqual(migration.VERSION, 16)
        self.assertEqual(migration.NAME, "v016_nar_daily_replay_result_schema")
        self.assertEqual(tuple(item.VERSION for item in MIGRATIONS)[-2:], (15, 16))
        self.assertEqual(tuple(item for item in MIGRATIONS if item.VERSION == 16), (migration,))
        self.assertEqual(get_applied_versions(self.connection)[16], migration.NAME)

    def test_v016_rejects_preexisting_partial_object_before_mutation(self) -> None:
        path = self.root / "partial.sqlite3"
        connection = sqlite3.connect(path)
        self.addCleanup(connection.close)
        connection.execute("CREATE TABLE races(id INTEGER PRIMARY KEY)")
        connection.execute("CREATE TABLE horses(id INTEGER PRIMARY KEY,race_id INTEGER)")
        connection.commit()
        through_v015 = tuple(item for item in MIGRATIONS if item.VERSION <= 15)
        apply_migrations(connection, migrations=through_v015)
        connection.execute("CREATE TABLE nar_daily_replay_results(fake TEXT)")
        connection.commit()
        with self.assertRaisesRegex(RuntimeError, "already exist"):
            apply_migrations(connection)
        self.assertNotIn(16, get_applied_versions(connection))
        self.assertEqual(
            tuple(
                row[1]
                for row in connection.execute(
                    "PRAGMA table_info(nar_daily_replay_results)"
                )
            ),
            ("fake",),
        )
        self.assertFalse(connection.in_transaction)
        names = {
            row[0]
            for row in self.connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        self.assertTrue(
            {
                "nar_daily_replay_results",
                "nar_daily_replay_result_bet_type_summaries",
            }
            <= names
        )
        self.assertEqual(
            self.connection.execute("SELECT count(*) FROM nar_daily_replay_results").fetchone(),
            (0,),
        )
        apply_migrations(self.connection)
        self.assertEqual(get_applied_versions(self.connection)[16], migration.NAME)

    def test_constructor_never_migrates_and_rejects_absent_or_malformed_schema(self) -> None:
        path = self.root / "unmigrated.sqlite3"
        connection = sqlite3.connect(path)
        self.addCleanup(connection.close)
        connection.execute("CREATE TABLE races(id INTEGER PRIMARY KEY)")
        connection.execute("CREATE TABLE horses(id INTEGER PRIMARY KEY,race_id INTEGER)")
        connection.commit()
        with self.assertRaises(RepositoryDataIntegrityError):
            SQLiteNARDailyReplayResultRepository(connection=connection, database_path=path)
        self.assertIsNone(
            connection.execute(
                "SELECT 1 FROM sqlite_master WHERE name='schema_migrations'"
            ).fetchone()
        )

        self.connection.execute("DROP TRIGGER nar_daily_replay_results_no_update")
        with self.assertRaises(RepositoryDataIntegrityError):
            SQLiteNARDailyReplayResultRepository(
                connection=self.connection, database_path=self.record.database_path
            )

    def test_constructor_rejects_semantically_malformed_table_contracts(self) -> None:
        cases = (
            (
                "missing-primary-key",
                "nar_daily_replay_results",
                (
                    ("persisted_content_sha256 TEXT PRIMARY KEY CHECK", "persisted_content_sha256 TEXT CHECK"),
                    (") WITHOUT ROWID", ")"),
                ),
            ),
            (
                "missing-unique",
                "nar_daily_replay_results",
                (("orchestration_audit_sha256 TEXT NOT NULL UNIQUE CHECK", "orchestration_audit_sha256 TEXT NOT NULL CHECK"),),
            ),
            (
                "changed-check",
                "nar_daily_replay_results",
                (("typeof(schema_version)='integer' AND schema_version=1", "typeof(schema_version)='integer' AND schema_version>=1"),),
            ),
            (
                "changed-foreign-key-action",
                "nar_daily_replay_result_bet_type_summaries",
                (("ON DELETE RESTRICT ON UPDATE RESTRICT", "ON DELETE NO ACTION ON UPDATE NO ACTION"),),
            ),
            (
                "missing-without-rowid",
                "nar_daily_replay_result_bet_type_summaries",
                ((") WITHOUT ROWID", ")"),),
            ),
        )
        for name, table_name, replacements in cases:
            with self.subTest(name=name):
                self._assert_table_schema_mutation_rejected(
                    name=name,
                    table_name=table_name,
                    replacements=replacements,
                )

    def test_constructor_rejects_correct_trigger_name_with_wrong_body(self) -> None:
        self.connection.execute("DROP TRIGGER nar_daily_replay_results_no_update")
        self.connection.execute(
            """CREATE TRIGGER nar_daily_replay_results_no_update
               BEFORE UPDATE ON nar_daily_replay_results
               BEGIN SELECT 1; END"""
        )
        self.connection.commit()
        with self.assertRaises(RepositoryDataIntegrityError):
            SQLiteNARDailyReplayResultRepository(
                connection=self.connection,
                database_path=self.record.database_path,
            )

    def test_constructor_rejects_wrong_index_uniqueness_and_column_order(self) -> None:
        self._assert_table_schema_mutation_rejected(
            name="wrong-unique-index-order",
            table_name="nar_daily_replay_results",
            replacements=(
                (
                    "orchestration_audit_sha256 TEXT NOT NULL UNIQUE CHECK",
                    "orchestration_audit_sha256 TEXT NOT NULL CHECK",
                ),
                (
                    ") WITHOUT ROWID",
                    ", UNIQUE(target_date,orchestration_audit_sha256)\n        ) WITHOUT ROWID",
                ),
            ),
        )

    def test_constructor_requires_exact_connection_path_and_clean_transaction(self) -> None:
        with self.assertRaises(RepositoryValidationError):
            SQLiteNARDailyReplayResultRepository(
                connection=object(), database_path=self.record.database_path
            )
        other = self.root / "other.sqlite3"
        sqlite3.connect(other).close()
        with self.assertRaises(RepositoryValidationError):
            SQLiteNARDailyReplayResultRepository(
                connection=self.connection, database_path=other
            )
        self.connection.execute("BEGIN")
        with self.assertRaises(RepositoryValidationError):
            SQLiteNARDailyReplayResultRepository(
                connection=self.connection, database_path=self.record.database_path
            )
        self.connection.rollback()

    def test_all_three_states_exact_round_trip(self) -> None:
        records = (
            self.record,
            build_record(
                self.root,
                NARDailyReplayExecutionState.NOT_RUN_PARTIAL_RESOLUTION,
                run_id="partial-run",
                manifest_name="partial.json",
            ),
            build_record(
                self.root,
                NARDailyReplayExecutionState.NOT_RUN_NO_EXECUTABLE_TARGETS,
                run_id="none-run",
                manifest_name="none.json",
            ),
        )
        for record in records:
            with self.subTest(state=record.execution_state):
                self.repository.save_result(record=record)
                loaded = self.repository.load_result(
                    persisted_content_sha256=record.persisted_content_sha256
                )
                self.assertEqual(loaded, record)
                self.assertIsNone(loaded.summary) if record.summary is None else self.assertEqual(
                    loaded.summary, record.summary
                )
        self.assertFalse(self.connection.in_transaction)

    def test_completed_summary_and_by_bet_type_round_trip_without_float(self) -> None:
        self.repository.save_result(record=self.record)
        loaded = self.repository.load_result(
            persisted_content_sha256=self.record.persisted_content_sha256
        )
        self.assertEqual(loaded.summary, self.record.summary)
        self.assertEqual(dict(loaded.summary.by_bet_type), dict(self.record.summary.by_bet_type))
        self.assertNotIsInstance(loaded.summary.roi, float)
        self.assertNotIsInstance(loaded.summary.by_bet_type["単勝"].roi, float)

    def test_completed_no_bet_summary_round_trips_distinct_from_diagnostic(self) -> None:
        completed = build_record(
            self.root,
            NARDailyReplayExecutionState.FULL_DAY_REPLAY_COMPLETED,
            run_id="no-bet-run",
            manifest_name="no-bet.json",
            completed_no_bet=True,
        )
        diagnostic = build_record(
            self.root,
            NARDailyReplayExecutionState.NOT_RUN_NO_EXECUTABLE_TARGETS,
            run_id="diagnostic-run",
            manifest_name="diagnostic.json",
        )
        self.repository.save_result(record=completed)
        self.repository.save_result(record=diagnostic)
        loaded_completed = self.repository.load_result(
            persisted_content_sha256=completed.persisted_content_sha256
        )
        loaded_diagnostic = self.repository.load_result(
            persisted_content_sha256=diagnostic.persisted_content_sha256
        )
        self.assertIsNotNone(loaded_completed.summary)
        self.assertEqual(loaded_completed.summary.investment, 0)
        self.assertIsNone(loaded_completed.summary.roi)
        self.assertIsNone(loaded_diagnostic.summary)

    def test_application_publishes_and_returns_exact_repository_reload(self) -> None:
        request = build_request(
            self.root,
            NARDailyReplayExecutionState.NOT_RUN_PARTIAL_RESOLUTION,
            run_id="application-run",
            manifest_name="application.json",
        )
        loaded = persist_nar_daily_replay_result(
            request=request, repository=self.repository
        )
        self.assertEqual(
            loaded,
            self.repository.load_result(
                persisted_content_sha256=loaded.persisted_content_sha256
            ),
        )

    def test_exact_duplicate_is_idempotent_without_row_changes(self) -> None:
        self.repository.save_result(record=self.record)
        changes = self.connection.total_changes
        self.repository.save_result(record=self.record)
        self.assertEqual(self.connection.total_changes, changes)
        self.assertEqual(
            self.connection.execute("SELECT count(*) FROM nar_daily_replay_results").fetchone(),
            (1,),
        )
        self.assertFalse(self.connection.in_transaction)

    def test_same_audit_identity_with_different_summary_or_metadata_conflicts(self) -> None:
        self.repository.save_result(record=self.record)
        cases = (
            replace(
                self.record,
                summary=replace(self.record.summary, maximum_drawdown=26),
            ),
            replace(self.record, race_budget_total_amount=1100),
        )
        for changed in cases:
            with self.subTest(digest=changed.persisted_content_sha256):
                self.assertNotEqual(
                    changed.persisted_content_sha256, self.record.persisted_content_sha256
                )
                with self.assertRaises(RepositoryConflictError):
                    self.repository.save_result(record=changed)
                self.assertFalse(self.connection.in_transaction)
        self.assertEqual(
            self.connection.execute("SELECT count(*) FROM nar_daily_replay_results").fetchone(),
            (1,),
        )

    def test_different_attempts_on_same_target_date_are_allowed(self) -> None:
        second = build_record(
            self.root,
            NARDailyReplayExecutionState.FULL_DAY_REPLAY_COMPLETED,
            run_id="second-run",
            manifest_name="second.json",
        )
        self.assertEqual(second.target_date, self.record.target_date)
        self.assertNotEqual(
            second.orchestration_audit_sha256, self.record.orchestration_audit_sha256
        )
        self.repository.save_result(record=self.record)
        self.repository.save_result(record=second)
        self.assertEqual(
            self.connection.execute("SELECT count(*) FROM nar_daily_replay_results").fetchone(),
            (2,),
        )

    def test_missing_and_invalid_exact_identity_behavior(self) -> None:
        self.assertIsNone(
            self.repository.load_result(persisted_content_sha256="f" * 64)
        )
        for value in ("bad", "A" * 64, None):
            with self.subTest(value=value), self.assertRaises(RepositoryValidationError):
                self.repository.load_result(persisted_content_sha256=value)
        self.assertFalse(hasattr(self.repository, "load_latest"))
        self.assertFalse(hasattr(self.repository, "load_by_date"))
        self.assertFalse(hasattr(self.repository, "update_result"))
        self.assertFalse(hasattr(self.repository, "delete_result"))

    def test_invalid_caller_content_digest_is_rejected(self) -> None:
        object.__setattr__(self.record, "persisted_content_sha256", "f" * 64)
        with self.assertRaises(RepositoryValidationError):
            self.repository.save_result(record=self.record)
        self.assertFalse(self.connection.in_transaction)

    def test_corrupt_header_digest_and_noncanonical_json_fail_closed(self) -> None:
        for column, value in (
            ("target_set_content_sha256", "e" * 64),
            ("resolution_outcomes_json", " []"),
        ):
            with self.subTest(column=column):
                record = build_record(
                    self.root,
                    NARDailyReplayExecutionState.NOT_RUN_NO_EXECUTABLE_TARGETS,
                    run_id=f"corrupt-{column}",
                    manifest_name=f"corrupt-{column}.json",
                )
                self.repository.save_result(record=record)
                self.connection.execute("DROP TRIGGER nar_daily_replay_results_no_update")
                self.connection.execute(
                    f"UPDATE nar_daily_replay_results SET {column}=? WHERE persisted_content_sha256=?",
                    (value, record.persisted_content_sha256),
                )
                _restore_header_update_trigger(self.connection)
                self.connection.commit()
                with self.assertRaises(RepositoryDataIntegrityError):
                    self.repository.load_result(
                        persisted_content_sha256=record.persisted_content_sha256
                    )

    def test_corrupt_child_decimal_fails_closed(self) -> None:
        self.repository.save_result(record=self.record)
        self.connection.execute(
            "DROP TRIGGER nar_daily_replay_result_bet_types_no_update"
        )
        self.connection.execute(
            """UPDATE nar_daily_replay_result_bet_type_summaries
               SET roi_text='250.0' WHERE persisted_content_sha256=?""",
            (self.record.persisted_content_sha256,),
        )
        _restore_child_update_trigger(self.connection)
        self.connection.commit()
        with self.assertRaises(RepositoryDataIntegrityError):
            self.repository.load_result(
                persisted_content_sha256=self.record.persisted_content_sha256
            )

    def test_invalid_stored_state_and_summary_contradiction_fail_closed(self) -> None:
        record = build_record(
            self.root,
            NARDailyReplayExecutionState.NOT_RUN_NO_EXECUTABLE_TARGETS,
            run_id="bad-state",
            manifest_name="bad-state.json",
        )
        self.repository.save_result(record=record)
        self.connection.execute("DROP TRIGGER nar_daily_replay_results_no_update")
        self.connection.execute("PRAGMA ignore_check_constraints=ON")
        self.connection.execute(
            """UPDATE nar_daily_replay_results SET summary_race_count=0
               WHERE persisted_content_sha256=?""",
            (record.persisted_content_sha256,),
        )
        self.connection.execute("PRAGMA ignore_check_constraints=OFF")
        _restore_header_update_trigger(self.connection)
        self.connection.commit()
        with self.assertRaises(RepositoryDataIntegrityError):
            self.repository.load_result(
                persisted_content_sha256=record.persisted_content_sha256
            )

    def test_database_immutability_triggers_reject_update_and_delete(self) -> None:
        self.repository.save_result(record=self.record)
        statements = (
            (
                "UPDATE nar_daily_replay_results SET run_id='changed' "
                "WHERE persisted_content_sha256=?",
                (self.record.persisted_content_sha256,),
            ),
            (
                "DELETE FROM nar_daily_replay_results WHERE persisted_content_sha256=?",
                (self.record.persisted_content_sha256,),
            ),
            (
                "UPDATE nar_daily_replay_result_bet_type_summaries SET payout=0 "
                "WHERE persisted_content_sha256=?",
                (self.record.persisted_content_sha256,),
            ),
            (
                "DELETE FROM nar_daily_replay_result_bet_type_summaries "
                "WHERE persisted_content_sha256=?",
                (self.record.persisted_content_sha256,),
            ),
        )
        for statement, parameters in statements:
            with self.subTest(statement=statement), self.assertRaises(sqlite3.IntegrityError):
                self.connection.execute(statement, parameters)
            self.connection.rollback()
        self.assertEqual(
            self.repository.load_result(
                persisted_content_sha256=self.record.persisted_content_sha256
            ),
            self.record,
        )

    def test_conflict_rolls_back_and_preserves_caller_transaction_state(self) -> None:
        self.repository.save_result(record=self.record)
        changed = replace(self.record, race_budget_total_amount=1200)
        before = self.connection.total_changes
        with self.assertRaises(RepositoryConflictError):
            self.repository.save_result(record=changed)
        self.assertEqual(self.connection.total_changes, before)
        self.assertFalse(self.connection.in_transaction)
        self.connection.execute("BEGIN")
        with self.assertRaises(RepositoryValidationError):
            self.repository.save_result(record=self.record)
        self.assertTrue(self.connection.in_transaction)
        self.connection.rollback()

    def test_static_boundary_has_no_network_clock_repair_or_aggregation(self) -> None:
        paths = (
            Path(migration.__file__),
            Path(__import__(
                "scripts.simulation.repositories.sqlite_nar_daily_replay_result_repository",
                fromlist=["x"],
            ).__file__),
        )
        for path in paths:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            imported = {
                alias.name
                for node in ast.walk(tree)
                if isinstance(node, (ast.Import, ast.ImportFrom))
                for alias in node.names
            }
            self.assertTrue(imported.isdisjoint({"requests", "httpx", "urllib"}))
            self.assertFalse(
                any(
                    isinstance(node, ast.Attribute)
                    and node.attr in {"now", "utcnow"}
                    for node in ast.walk(tree)
                )
            )
            self.assertNotIn("INSERT OR REPLACE", source.upper())
            self.assertNotIn("datetime.now", source)
            self.assertNotIn("time.time", source)


if __name__ == "__main__":
    unittest.main()
