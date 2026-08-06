"""Contract tests for the atomic historical-input snapshot SQLite save path."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import ast
import inspect
import sqlite3
import unittest

import scripts.simulation.repositories as repositories
from scripts.migrations.runner import apply_migrations
from scripts.simulation.historical_input_snapshots import (
    HistoricalExternalEntryIdentity,
    HistoricalExternalRaceIdentity,
    HistoricalInputProvenance,
    HistoricalInputSnapshot,
    HistoricalInputSnapshotIdentity,
    HistoricalPastRaceSnapshot,
    HistoricalRaceEntrySnapshot,
    HistoricalRaceSnapshot,
    HistoricalSourceIdentity,
)
from scripts.simulation.repositories.errors import (
    RepositoryConflictError,
    RepositoryDataIntegrityError,
    RepositoryValidationError,
)
from scripts.simulation.repositories.sqlite_historical_input_snapshot_repository import (
    SQLiteHistoricalInputSnapshotRepository,
)


UTC = timezone.utc
CAPTURED = datetime(2026, 8, 5, 10, 0, 0, 123456, tzinfo=UTC)
CUTOFF = datetime(2026, 8, 5, 10, 30, 0, 654321, tzinfo=UTC)
START = datetime(2026, 8, 5, 12, 0, 0, 111111, tzinfo=UTC)


class SQLiteHistoricalInputSnapshotRepositoryTests(unittest.TestCase):
    def connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(":memory:")
        connection.execute("CREATE TABLE races(id INTEGER PRIMARY KEY)")
        connection.execute("CREATE TABLE horses(id INTEGER PRIMARY KEY, race_id INTEGER NOT NULL)")
        connection.executemany("INSERT INTO races(id) VALUES(?)", ((1,), (2,)))
        connection.executemany(
            "INSERT INTO horses(id,race_id) VALUES(?,?)",
            ((11, 1), (12, 1), (21, 2)),
        )
        connection.commit()
        apply_migrations(connection)
        return connection

    def repository(self) -> tuple[sqlite3.Connection, SQLiteHistoricalInputSnapshotRepository]:
        connection = self.connection()
        return connection, SQLiteHistoricalInputSnapshotRepository(connection=connection)

    def snapshot(
        self,
        *,
        race_id: int = 1,
        entry_id: int = 11,
        external_race_id: str = "race-1",
        external_entry_id: str = "entry-11",
        external_horse_id: str | None = "horse-11",
        captured_at: datetime = CAPTURED,
        cutoff: datetime = CUTOFF,
        source_url: str | None = "https://example.test/race-1",
        include_past_race: bool = True,
    ) -> HistoricalInputSnapshot:
        source = HistoricalSourceIdentity("NAR", "nar_official", external_race_id, source_url)
        identity = HistoricalInputSnapshotIdentity("dataset-1", source, captured_at)
        external_race = HistoricalExternalRaceIdentity("NAR", "nar_official", external_race_id)
        entry = HistoricalRaceEntrySnapshot(
            entry_id,
            HistoricalExternalEntryIdentity(external_race, external_entry_id, external_horse_id),
            1,
            "Jockey",
            Decimal("2.500"),
            0,
        )
        race = HistoricalRaceSnapshot(
            date(2026, 8, 5), START, "Tokyo", 1600, "turf", "good", "Race", "Open", "sunny"
        )
        past_races = ()
        provenance = [
            HistoricalInputProvenance("track", "track", "nar", "track-1", None, observed_at=CAPTURED),
            HistoricalInputProvenance("entry", f"entry/{entry_id}", "nar", "entry-1", entry_id, observed_at=CAPTURED),
            HistoricalInputProvenance("odds", f"odds/{entry_id}", "nar", "odds-1", entry_id, available_at=CAPTURED),
            HistoricalInputProvenance("jockey", f"jockey/{entry_id}", "nar", "jockey-1", entry_id, observed_at=CAPTURED),
        ]
        if include_past_race:
            past_races = (
                HistoricalPastRaceSnapshot(
                    entry_id, 0, date(2026, 8, 4), "Tokyo", "Prior", "Open", 1400, "dirt", "cloudy",
                    "good", 1, Decimal("0.00"), "1:22.2", Decimal("480.0"), Decimal("-2.0"),
                    "Jockey", 0, Decimal("3.40"), "", 0,
                ),
            )
            provenance.append(
                HistoricalInputProvenance(
                    "past_race", f"past_race/{entry_id}/0", "nar", "past-1", entry_id,
                    observed_at=CAPTURED, past_race_index=0,
                )
            )
        else:
            provenance.append(
                HistoricalInputProvenance(
                    "past_race", f"past_race/{entry_id}/none", "nar", "past-none-1", entry_id,
                    observed_at=CAPTURED,
                )
            )
        return HistoricalInputSnapshot(identity, race_id, cutoff, race, (entry,), past_races, tuple(provenance))

    @staticmethod
    def count(connection: sqlite3.Connection, table: str) -> int:
        return connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]

    def assert_no_snapshot(self, connection: sqlite3.Connection) -> None:
        for table in (
            "historical_input_snapshots",
            "historical_input_snapshot_races",
            "historical_input_snapshot_entries",
            "historical_input_snapshot_past_races",
            "historical_input_snapshot_provenance",
        ):
            self.assertEqual(self.count(connection, table), 0, table)

    def test_api_constructor_and_source_boundaries(self) -> None:
        signature = inspect.signature(SQLiteHistoricalInputSnapshotRepository)
        self.assertEqual(tuple(signature.parameters), ("connection",))
        self.assertEqual(signature.parameters["connection"].kind, inspect.Parameter.KEYWORD_ONLY)
        with self.assertRaises(RepositoryValidationError):
            SQLiteHistoricalInputSnapshotRepository(connection=object())
        connection = self.connection()
        repository = SQLiteHistoricalInputSnapshotRepository(connection=connection)
        self.assertEqual(connection.execute("PRAGMA foreign_keys").fetchone()[0], 1)
        self.assertTrue(callable(repository.save_snapshot))
        self.assertFalse(hasattr(repository, "load_latest_snapshot"))
        self.assertFalse(hasattr(repositories, "SQLiteHistoricalInputSnapshotRepository"))
        source = inspect.getsource(inspect.getmodule(SQLiteHistoricalInputSnapshotRepository))
        tree = ast.parse(source)
        self.assertNotIn("sqlite3.connect", source)
        self.assertNotIn("INSERT OR REPLACE", source)
        self.assertNotIn("load_latest_snapshot", source)
        self.assertNotIn("UPDATE historical_input_external", source)
        self.assertFalse(any(isinstance(node, ast.ImportFrom) and node.module and "migration" in node.module for node in ast.walk(tree)))
        self.assertFalse(any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "connect" for node in ast.walk(tree)))

    def test_complete_save_persists_all_eight_tables_canonically(self) -> None:
        connection, repository = self.repository()
        snapshot = self.snapshot()
        repository.save_snapshot(snapshot=snapshot)
        self.assertEqual(
            {table: self.count(connection, table) for table in (
                "historical_input_source_identities", "historical_input_external_races",
                "historical_input_external_entries", "historical_input_snapshots",
                "historical_input_snapshot_races", "historical_input_snapshot_entries",
                "historical_input_snapshot_past_races", "historical_input_snapshot_provenance",
            )},
            {
                "historical_input_source_identities": 1, "historical_input_external_races": 1,
                "historical_input_external_entries": 1, "historical_input_snapshots": 1,
                "historical_input_snapshot_races": 1, "historical_input_snapshot_entries": 1,
                "historical_input_snapshot_past_races": 1, "historical_input_snapshot_provenance": 5,
            },
        )
        header = connection.execute(
            """SELECT dataset_id,organization,source_system,external_race_id,internal_race_id,source_url,
                      captured_at_utc,information_cutoff_utc,content_sha256
               FROM historical_input_snapshots"""
        ).fetchone()
        self.assertEqual(header, ("dataset-1", "NAR", "nar_official", "race-1", 1, "https://example.test/race-1", "2026-08-05T10:00:00.123456+00:00", "2026-08-05T10:30:00.654321+00:00", snapshot.content_sha256))
        self.assertEqual(
            connection.execute(
                """SELECT target_race_date,scheduled_start_at_utc,place,distance_m,track,track_condition,
                          race_name,race_class,weather FROM historical_input_snapshot_races"""
            ).fetchone(),
            ("2026-08-05", "2026-08-05T12:00:00.111111+00:00", "Tokyo", 1600, "turf", "good", "Race", "Open", "sunny"),
        )
        self.assertEqual(
            connection.execute(
                """SELECT race_entry_id,external_entry_id,external_horse_id,horse_no,jockey,win_odds_text,entry_order
                   FROM historical_input_snapshot_entries"""
            ).fetchone(),
            (11, "entry-11", "horse-11", 1, "Jockey", "2.5", 0),
        )
        self.assertEqual(
            connection.execute(
                """SELECT race_entry_id,past_race_index,race_date,place,race_name,race_class,distance_m,track,
                          weather,track_condition,finish,margin_text,race_time,weight_text,weight_diff_text,
                          jockey,popularity,odds_text,passing_order,fourth_corner_position
                   FROM historical_input_snapshot_past_races"""
            ).fetchone(),
            (11, 0, "2026-08-04", "Tokyo", "Prior", "Open", 1400, "dirt", "cloudy", "good", 1, "0", "1:22.2", "480", "-2", "Jockey", 0, "3.4", "", 0),
        )
        self.assertEqual(
            connection.execute(
                """SELECT input_type,audit_key,source,source_id,race_entry_id,available_at_utc,observed_at_utc,past_race_index
                   FROM historical_input_snapshot_provenance ORDER BY audit_key"""
            ).fetchall(),
            [
                ("entry", "entry/11", "nar", "entry-1", 11, None, "2026-08-05T10:00:00.123456+00:00", None),
                ("jockey", "jockey/11", "nar", "jockey-1", 11, None, "2026-08-05T10:00:00.123456+00:00", None),
                ("odds", "odds/11", "nar", "odds-1", 11, "2026-08-05T10:00:00.123456+00:00", None, None),
                ("past_race", "past_race/11/0", "nar", "past-1", 11, None, "2026-08-05T10:00:00.123456+00:00", 0),
                ("track", "track", "nar", "track-1", None, None, "2026-08-05T10:00:00.123456+00:00", None),
            ],
        )

    def test_same_snapshot_is_an_idempotent_no_op(self) -> None:
        connection, repository = self.repository()
        snapshot = self.snapshot()
        repository.save_snapshot(snapshot=snapshot)
        repository.save_snapshot(snapshot=snapshot)
        self.assertEqual(self.count(connection, "historical_input_snapshots"), 1)
        self.assertEqual(self.count(connection, "historical_input_snapshot_entries"), 1)
        self.assertEqual(self.count(connection, "historical_input_snapshot_past_races"), 1)
        self.assertEqual(self.count(connection, "historical_input_snapshot_provenance"), 5)
        self.assertEqual(self.count(connection, "historical_input_external_entries"), 1)

    def test_snapshot_natural_identity_conflict_rolls_back(self) -> None:
        connection, repository = self.repository()
        first = self.snapshot()
        repository.save_snapshot(snapshot=first)
        conflicting = self.snapshot(cutoff=CUTOFF + timedelta(minutes=1), source_url="https://example.test/changed")
        self.assertNotEqual(first.content_sha256, conflicting.content_sha256)
        with self.assertRaises(RepositoryConflictError):
            repository.save_snapshot(snapshot=conflicting)
        self.assertEqual(self.count(connection, "historical_input_snapshots"), 1)
        self.assertEqual(connection.execute("SELECT information_cutoff_utc,source_url FROM historical_input_snapshots").fetchone(), ("2026-08-05T10:30:00.654321+00:00", "https://example.test/race-1"))
        self.assertFalse(connection.in_transaction)
        self.assertEqual(connection.execute("SELECT 1").fetchone(), (1,))

    def test_compatible_mapping_reuse_ignores_source_url_and_external_horse_id(self) -> None:
        connection, repository = self.repository()
        repository.save_snapshot(snapshot=self.snapshot())
        next_snapshot = self.snapshot(
            captured_at=CAPTURED + timedelta(seconds=1),
            source_url="https://example.test/other-url",
            external_horse_id=None,
        )
        repository.save_snapshot(snapshot=next_snapshot)
        self.assertEqual(self.count(connection, "historical_input_source_identities"), 1)
        self.assertEqual(self.count(connection, "historical_input_external_races"), 1)
        self.assertEqual(self.count(connection, "historical_input_external_entries"), 1)
        self.assertEqual(self.count(connection, "historical_input_snapshots"), 2)

    def test_external_race_forward_and_reverse_conflicts_are_repository_conflicts(self) -> None:
        for kind in ("forward", "reverse"):
            with self.subTest(kind=kind):
                connection, repository = self.repository()
                connection.execute("INSERT INTO historical_input_source_identities VALUES('NAR','nar_official')")
                if kind == "forward":
                    connection.execute("INSERT INTO historical_input_external_races VALUES('NAR','nar_official','race-1',2)")
                else:
                    connection.execute("INSERT INTO historical_input_external_races VALUES('NAR','nar_official','different-race',1)")
                connection.commit()
                with self.assertRaises(RepositoryConflictError):
                    repository.save_snapshot(snapshot=self.snapshot())
                self.assert_no_snapshot(connection)
                self.assertEqual(self.count(connection, "historical_input_external_races"), 1)
                self.assertFalse(connection.in_transaction)
                self.assertEqual(connection.execute("SELECT 1").fetchone(), (1,))

    def test_external_entry_forward_and_reverse_conflicts_are_repository_conflicts(self) -> None:
        for kind in ("forward", "reverse"):
            with self.subTest(kind=kind):
                connection, repository = self.repository()
                connection.execute("INSERT INTO historical_input_source_identities VALUES('NAR','nar_official')")
                connection.execute("INSERT INTO historical_input_external_races VALUES('NAR','nar_official','race-1',1)")
                if kind == "forward":
                    connection.execute("INSERT INTO historical_input_external_entries VALUES('NAR','nar_official','race-1','entry-11',1,12)")
                else:
                    connection.execute("INSERT INTO historical_input_external_entries VALUES('NAR','nar_official','race-1','other-entry',1,11)")
                connection.commit()
                with self.assertRaises(RepositoryConflictError):
                    repository.save_snapshot(snapshot=self.snapshot())
                self.assert_no_snapshot(connection)
                self.assertEqual(self.count(connection, "historical_input_external_entries"), 1)
                self.assertFalse(connection.in_transaction)
                self.assertEqual(connection.execute("SELECT 1").fetchone(), (1,))

    def test_real_child_trigger_failure_is_data_integrity_and_rolls_back_everything(self) -> None:
        connection, repository = self.repository()
        connection.execute(
            """CREATE TRIGGER test_fail_historical_provenance_insert
               BEFORE INSERT ON historical_input_snapshot_provenance
               BEGIN SELECT RAISE(ABORT, 'test provenance child failure'); END"""
        )
        connection.commit()
        with self.assertRaises(RepositoryDataIntegrityError) as raised:
            repository.save_snapshot(snapshot=self.snapshot())
        self.assertNotIsInstance(raised.exception, RepositoryConflictError)
        for table in (
            "historical_input_source_identities", "historical_input_external_races",
            "historical_input_external_entries",
        ):
            self.assertEqual(self.count(connection, table), 0)
        self.assert_no_snapshot(connection)
        self.assertFalse(connection.in_transaction)
        connection.execute("DROP TRIGGER test_fail_historical_provenance_insert")
        connection.commit()
        repository.save_snapshot(snapshot=self.snapshot())
        self.assertEqual(self.count(connection, "historical_input_snapshots"), 1)

    def test_active_caller_transaction_is_rejected_without_commit_and_invalid_snapshot_is_rejected(self) -> None:
        connection, repository = self.repository()
        with self.assertRaises(RepositoryValidationError):
            repository.save_snapshot(snapshot=object())
        connection.execute("BEGIN")
        connection.execute("INSERT INTO races(id) VALUES(3)")
        with self.assertRaises(RepositoryValidationError):
            repository.save_snapshot(snapshot=self.snapshot())
        self.assertTrue(connection.in_transaction)
        self.assertEqual(connection.execute("SELECT id FROM races WHERE id=3").fetchone(), (3,))
        connection.rollback()
        self.assertIsNone(connection.execute("SELECT id FROM races WHERE id=3").fetchone())


if __name__ == "__main__":
    unittest.main()
