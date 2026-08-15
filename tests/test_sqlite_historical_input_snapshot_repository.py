"""Contract tests for the atomic historical-input snapshot SQLite save path."""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
import ast
import inspect
import sqlite3
from typing import get_type_hints
import unittest

import scripts.simulation.repositories as repositories
from scripts.migrations.runner import apply_migrations
from scripts.simulation.historical_input_evidence import HistoricalInputEvidenceReference
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
    @staticmethod
    def evidence(*roles: str, available_at: datetime | None = None, observed_at: datetime = CAPTURED) -> tuple[HistoricalInputEvidenceReference, ...]:
        return tuple(
            HistoricalInputEvidenceReference(role, "https://example.test/evidence", str(index + 1) * 64, available_at, observed_at)
            for index, role in enumerate(roles)
        )

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
            HistoricalInputProvenance("track", "track", "nar", "track-1", None, self.evidence("track")),
            HistoricalInputProvenance("entry", f"entry/{entry_id}", "nar", "entry-1", entry_id, self.evidence("entry")),
            HistoricalInputProvenance("odds", f"odds/{entry_id}", "nar", "odds-1", entry_id, self.evidence("odds_win", available_at=CAPTURED)),
            HistoricalInputProvenance("jockey", f"jockey/{entry_id}", "nar", "jockey-1", entry_id, self.evidence("jockey")),
        ]
        if include_past_race:
            past_races = (
                HistoricalPastRaceSnapshot(
                    entry_id, 0, date(2026, 8, 4), "Tokyo", "Prior", "Open", 1400, "dirt", "cloudy",
                    "good", 1, "1:22.2", Decimal("480.0"), Decimal("-2.0"),
                    "Jockey", 0, Decimal("3.40"), "", 0,
                ),
            )
            provenance.append(
                HistoricalInputProvenance(
                    "past_race", f"past_race/{entry_id}/0", "nar", "past-1", entry_id,
                    evidence=self.evidence("historical_race_context", "historical_race_result"), past_race_index=0,
                )
            )
        else:
            provenance.append(
                HistoricalInputProvenance(
                    "past_race", f"past_race/{entry_id}/none", "nar", "past-none-1", entry_id,
                    evidence=self.evidence("past_race_absence_query"),
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
        self.assertTrue(callable(repository.load_latest_snapshot))
        load_signature = inspect.signature(repository.load_latest_snapshot)
        self.assertEqual(
            tuple(load_signature.parameters),
            ("dataset_id", "race_id", "information_cutoff", "source_identity"),
        )
        self.assertTrue(all(parameter.kind is inspect.Parameter.KEYWORD_ONLY for parameter in load_signature.parameters.values()))
        load_hints = get_type_hints(SQLiteHistoricalInputSnapshotRepository.load_latest_snapshot)
        self.assertIs(load_hints["dataset_id"], str)
        self.assertIs(load_hints["race_id"], int)
        self.assertIs(load_hints["information_cutoff"], datetime)
        self.assertIs(load_hints["source_identity"], HistoricalExternalRaceIdentity)
        self.assertEqual(load_hints["return"], HistoricalInputSnapshot | None)
        self.assertFalse(hasattr(repositories, "SQLiteHistoricalInputSnapshotRepository"))
        source = inspect.getsource(inspect.getmodule(SQLiteHistoricalInputSnapshotRepository))
        tree = ast.parse(source)
        self.assertNotIn("sqlite3.connect", source)
        self.assertNotIn("INSERT OR REPLACE", source)
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
                          weather,track_condition,finish,race_time,weight_text,weight_diff_text,
                          jockey,popularity,odds_text,passing_order,fourth_corner_position
                   FROM historical_input_snapshot_past_races"""
            ).fetchone(),
            (11, 0, "2026-08-04", "Tokyo", "Prior", "Open", 1400, "dirt", "cloudy", "good", 1, "1:22.2", "480", "-2", "Jockey", 0, "3.4", "", 0),
        )
        self.assertEqual(
            connection.execute(
                """SELECT input_type,audit_key,source,source_id,race_entry_id,past_race_index
                   FROM historical_input_snapshot_provenance ORDER BY audit_key"""
            ).fetchall(),
            [
                ("entry", "entry/11", "nar", "entry-1", 11, None),
                ("jockey", "jockey/11", "nar", "jockey-1", 11, None),
                ("odds", "odds/11", "nar", "odds-1", 11, None),
                ("past_race", "past_race/11/0", "nar", "past-1", 11, 0),
                ("track", "track", "nar", "track-1", None, None),
            ],
        )
        self.assertEqual(self.count(connection, "historical_input_snapshot_provenance_evidence"), 6)

    def test_same_response_may_bind_both_generic_past_race_roles(self) -> None:
        connection, repository = self.repository()
        snapshot = self.snapshot()
        provenance = tuple(sorted((
            replace(
                item,
                evidence=(
                    item.evidence[0],
                    replace(item.evidence[1], response_sha256=item.evidence[0].response_sha256),
                ),
            )
            if item.audit_key == "past_race/11/0"
            else item
            for item in snapshot.provenance
        ), key=lambda item: item.audit_key))
        same_response = HistoricalInputSnapshot(
            snapshot.identity, snapshot.internal_race_id, snapshot.information_cutoff, snapshot.race,
            snapshot.entries, snapshot.past_races, provenance,
        )
        repository.save_snapshot(snapshot=same_response)
        rows = connection.execute(
            """SELECT evidence_role,canonical_source_url,response_sha256
               FROM historical_input_snapshot_provenance_evidence
               WHERE audit_key='past_race/11/0' ORDER BY evidence_order"""
        ).fetchall()
        self.assertEqual(rows[0][1:], rows[1][1:])
        self.assertEqual(repository.load_latest_snapshot(
            dataset_id="dataset-1", race_id=1, information_cutoff=CUTOFF,
            source_identity=HistoricalExternalRaceIdentity("NAR", "nar_official", "race-1"),
        ), same_response)

    def test_request_identity_round_trips_and_corruption_fails_closed(self) -> None:
        connection, repository = self.repository()
        legacy = self.snapshot()
        repository.save_snapshot(snapshot=legacy)
        self.assertEqual(
            connection.execute(
                "SELECT request_identity_sha256 FROM historical_input_snapshot_provenance_evidence"
            ).fetchall(),
            [(None,)] * 6,
        )
        request_aware_provenance = tuple(
            replace(
                item,
                evidence=tuple(replace(evidence, request_identity_sha256="a" * 64) for evidence in item.evidence),
            )
            for item in legacy.provenance
        )
        request_aware = HistoricalInputSnapshot(
            HistoricalInputSnapshotIdentity("dataset-2", legacy.identity.source_identity, CAPTURED + timedelta(seconds=1)),
            legacy.internal_race_id, legacy.information_cutoff, legacy.race, legacy.entries, legacy.past_races,
            request_aware_provenance,
        )
        repository.save_snapshot(snapshot=request_aware)
        self.assertEqual(
            connection.execute(
                "SELECT request_identity_sha256 FROM historical_input_snapshot_provenance_evidence WHERE snapshot_id=2"
            ).fetchall(),
            [("a" * 64,)] * 6,
        )
        loaded = repository.load_latest_snapshot(
            dataset_id="dataset-2", race_id=1, information_cutoff=CUTOFF,
            source_identity=HistoricalExternalRaceIdentity("NAR", "nar_official", "race-1"),
        )
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.content_sha256, request_aware.content_sha256)
        self.assertEqual(
            {evidence.request_identity_sha256 for item in loaded.provenance for evidence in item.evidence},
            {"a" * 64},
        )
        connection.execute("PRAGMA ignore_check_constraints=ON")
        connection.execute(
            "UPDATE historical_input_snapshot_provenance_evidence SET request_identity_sha256=? WHERE snapshot_id=2 AND evidence_order=0",
            ("A" * 64,),
        )
        connection.execute("PRAGMA ignore_check_constraints=OFF")
        with self.assertRaises(RepositoryDataIntegrityError):
            repository.load_latest_snapshot(
                dataset_id="dataset-2", race_id=1, information_cutoff=CUTOFF,
                source_identity=HistoricalExternalRaceIdentity("NAR", "nar_official", "race-1"),
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

    @staticmethod
    def lookup_source(*, external_race_id: str = "race-1") -> HistoricalExternalRaceIdentity:
        return HistoricalExternalRaceIdentity("NAR", "nar_official", external_race_id)

    def load(
        self,
        repository: SQLiteHistoricalInputSnapshotRepository,
        *,
        dataset_id: str = "dataset-1",
        race_id: int = 1,
        cutoff: datetime = CUTOFF,
        external_race_id: str = "race-1",
    ) -> HistoricalInputSnapshot | None:
        return repository.load_latest_snapshot(
            dataset_id=dataset_id,
            race_id=race_id,
            information_cutoff=cutoff,
            source_identity=self.lookup_source(external_race_id=external_race_id),
        )

    def save_older_and_newer(
        self,
        repository: SQLiteHistoricalInputSnapshotRepository,
    ) -> tuple[HistoricalInputSnapshot, HistoricalInputSnapshot]:
        older = self.snapshot(captured_at=CAPTURED, source_url="https://example.test/older")
        newer = self.snapshot(
            captured_at=CAPTURED + timedelta(seconds=1),
            source_url="https://example.test/newer",
        )
        repository.save_snapshot(snapshot=older)
        repository.save_snapshot(snapshot=newer)
        return older, newer

    def snapshot_id_for(self, connection: sqlite3.Connection, captured_at: datetime) -> int:
        return connection.execute(
            "SELECT snapshot_id FROM historical_input_snapshots WHERE captured_at_utc=?",
            (captured_at.isoformat(timespec="microseconds"),),
        ).fetchone()[0]

    def test_load_returns_none_and_validates_exact_callers(self) -> None:
        connection, repository = self.repository()
        self.assertIsNone(self.load(repository))
        invalid_cases = (
            {"dataset_id": ""},
            {"dataset_id": 1},
            {"race_id": True},
            {"race_id": 0},
            {"cutoff": datetime(2026, 8, 5, 10, 30)},
            {"external_race_id": "other"},
        )
        for values in invalid_cases[:-1]:
            with self.subTest(values=values), self.assertRaises(RepositoryValidationError):
                self.load(repository, **values)
        with self.assertRaises(RepositoryValidationError):
            repository.load_latest_snapshot(
                dataset_id="dataset-1",
                race_id=1,
                information_cutoff=CUTOFF,
                source_identity=object(),
            )
        self.assertFalse(connection.in_transaction)

    def test_load_validates_failing_timezone_and_accepts_non_utc_cutoff(self) -> None:
        class FailingTimezone(tzinfo):
            def utcoffset(self, dt: datetime | None) -> timedelta | None:
                raise ValueError("invalid timezone offset")

            def dst(self, dt: datetime | None) -> timedelta | None:
                return None

            def tzname(self, dt: datetime | None) -> str | None:
                return "failing"

        connection, repository = self.repository()
        saved = self.snapshot()
        repository.save_snapshot(snapshot=saved)
        queried: list[str] = []
        connection.set_trace_callback(queried.append)
        bad_cutoff = datetime(2026, 8, 5, 10, 30, tzinfo=FailingTimezone())
        with self.assertRaises(RepositoryValidationError):
            self.load(repository, cutoff=bad_cutoff)
        connection.set_trace_callback(None)
        self.assertEqual(queried, [])

        tokyo_cutoff = CUTOFF.astimezone(timezone(timedelta(hours=9)))
        loaded = self.load(repository, cutoff=tokyo_cutoff)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.identity.captured_at, saved.identity.captured_at)

    def test_load_selects_only_latest_dual_eligible_header_with_exact_isolation(self) -> None:
        connection, repository = self.repository()
        older, newer = self.save_older_and_newer(repository)
        self.assertEqual(self.load(repository, cutoff=CUTOFF).identity.captured_at, newer.identity.captured_at)
        self.assertIsNone(self.load(repository, dataset_id="other"))
        self.assertIsNone(self.load(repository, race_id=2))
        self.assertIsNone(self.load(repository, external_race_id="other"))
        future_cutoff = self.snapshot(captured_at=CAPTURED, cutoff=CUTOFF + timedelta(seconds=1))
        connection2, repository2 = self.repository()
        repository2.save_snapshot(snapshot=future_cutoff)
        self.assertIsNone(self.load(repository2, cutoff=CUTOFF))
        future_capture = self.snapshot(captured_at=CUTOFF + timedelta(seconds=1), cutoff=CUTOFF + timedelta(seconds=2))
        connection3, repository3 = self.repository()
        repository3.save_snapshot(snapshot=future_capture)
        self.assertIsNone(self.load(repository3, cutoff=CUTOFF))
        self.assertEqual(connection.execute("SELECT count(*) FROM historical_input_snapshots").fetchone(), (2,))
        self.assertEqual(older.identity.captured_at, CAPTURED)

    def test_load_fully_reconstructs_canonical_snapshot(self) -> None:
        connection, repository = self.repository()
        saved = self.snapshot()
        repository.save_snapshot(snapshot=saved)
        loaded = self.load(repository)
        self.assertEqual(loaded.content_sha256, saved.content_sha256)
        self.assertEqual(loaded.identity, saved.identity)
        self.assertEqual(loaded.race, saved.race)
        self.assertEqual(loaded.entries, saved.entries)
        self.assertEqual(loaded.past_races, saved.past_races)
        self.assertEqual(
            tuple(item.audit_key for item in loaded.provenance),
            (
                "entry/11",
                "jockey/11",
                "odds/11",
                "past_race/11/0",
                "track",
            ),
        )
        self.assertEqual(loaded.identity.source_identity.source_url, "https://example.test/race-1")
        self.assertEqual(loaded.entries[0].external_entry_identity.external_horse_id, "horse-11")
        self.assertEqual(loaded.entries[0].win_odds, Decimal("2.5"))
        self.assertEqual(loaded.past_races[0].race_time, "1:22.2")
        self.assertEqual(loaded.past_races[0].passing_order, "")
        self.assertEqual(loaded.provenance[0].audit_key, "entry/11")
        self.assertEqual(loaded.provenance[-1].audit_key, "track")
        self.assertEqual(loaded.identity.captured_at, CAPTURED)
        self.assertEqual(loaded.information_cutoff, CUTOFF)
        self.assertFalse(connection.in_transaction)

    def test_load_reconstructs_entries_past_races_and_provenance_in_canonical_order(self) -> None:
        connection, repository = self.repository()
        base = self.snapshot()
        entry_11 = base.entries[0]
        entry_12 = HistoricalRaceEntrySnapshot(
            12,
            HistoricalExternalEntryIdentity(
                entry_11.external_entry_identity.external_race_identity,
                "entry-12",
                "horse-12",
            ),
            2,
            "Second Jockey",
            Decimal("3"),
            1,
        )
        past_11_0 = base.past_races[0]
        past_11_1 = replace(past_11_0, past_race_index=1, race_date=date(2026, 8, 3))
        past_12_0 = replace(past_11_0, race_entry_id=12)
        provenance = (
            HistoricalInputProvenance("track", "track", "nar", "track-1", None, self.evidence("track")),
            HistoricalInputProvenance("entry", "entry/12", "nar", "entry-12", 12, self.evidence("entry")),
            HistoricalInputProvenance("odds", "odds/12", "nar", "odds-12", 12, self.evidence("odds_win", available_at=CAPTURED)),
            HistoricalInputProvenance("jockey", "jockey/12", "nar", "jockey-12", 12, self.evidence("jockey")),
            HistoricalInputProvenance("past_race", "past_race/12/0", "nar", "past-12-0", 12, self.evidence("historical_race_context", "historical_race_result"), 0),
            HistoricalInputProvenance("entry", "entry/11", "nar", "entry-11", 11, self.evidence("entry")),
            HistoricalInputProvenance("odds", "odds/11", "nar", "odds-11", 11, self.evidence("odds_win", available_at=CAPTURED)),
            HistoricalInputProvenance("jockey", "jockey/11", "nar", "jockey-11", 11, self.evidence("jockey")),
            HistoricalInputProvenance("past_race", "past_race/11/1", "nar", "past-11-1", 11, self.evidence("historical_race_context", "historical_race_result"), 1),
            HistoricalInputProvenance("past_race", "past_race/11/0", "nar", "past-11-0", 11, self.evidence("historical_race_context", "historical_race_result"), 0),
        )
        saved = HistoricalInputSnapshot(
            base.identity,
            base.internal_race_id,
            base.information_cutoff,
            base.race,
            (entry_12, entry_11),
            (past_12_0, past_11_1, past_11_0),
            provenance,
        )
        repository.save_snapshot(snapshot=saved)

        loaded = self.load(repository)
        self.assertEqual(tuple(item.race_entry_id for item in loaded.entries), (11, 12))
        self.assertEqual(
            tuple((item.race_entry_id, item.past_race_index) for item in loaded.past_races),
            ((11, 0), (11, 1), (12, 0)),
        )
        self.assertEqual(
            tuple(item.audit_key for item in loaded.provenance),
            tuple(sorted(item.audit_key for item in provenance)),
        )
        self.assertEqual(loaded.content_sha256, saved.content_sha256)

    def test_load_rejects_malformed_selected_values_and_digest_without_fallback(self) -> None:
        for table, column, value in (
            ("historical_input_snapshot_races", "scheduled_start_at_utc", "2026-08-05T12:00:00+00:00"),
            ("historical_input_snapshot_races", "target_race_date", "20260805"),
            ("historical_input_snapshot_entries", "win_odds_text", "2.50"),
            ("historical_input_snapshots", "content_sha256", "0" * 64),
        ):
            with self.subTest(table=table, column=column):
                connection, repository = self.repository()
                older, newer = self.save_older_and_newer(repository)
                snapshot_id = self.snapshot_id_for(connection, newer.identity.captured_at)
                connection.execute("PRAGMA ignore_check_constraints=ON")
                connection.execute(f"UPDATE {table} SET {column}=? WHERE snapshot_id=?", (value, snapshot_id))
                connection.commit()
                connection.execute("PRAGMA ignore_check_constraints=OFF")
                with self.assertRaises(RepositoryDataIntegrityError):
                    self.load(repository)
                self.assertEqual(older.identity.captured_at, CAPTURED)

    def test_selected_evidence_corruption_is_fail_closed_without_fallback(self) -> None:
        def mutate(connection: sqlite3.Connection, snapshot_id: int, case: str) -> None:
            audit_key = "past_race/11/0"
            if case == "missing":
                connection.execute(
                    "DELETE FROM historical_input_snapshot_provenance_evidence WHERE snapshot_id=? AND audit_key=? AND evidence_order=0",
                    (snapshot_id, audit_key),
                )
            elif case == "wrong_role":
                connection.execute(
                    "UPDATE historical_input_snapshot_provenance_evidence SET evidence_role='wrong' WHERE snapshot_id=? AND audit_key=? AND evidence_order=0",
                    (snapshot_id, audit_key),
                )
            elif case == "order":
                connection.execute(
                    "UPDATE historical_input_snapshot_provenance_evidence SET evidence_order=3 WHERE snapshot_id=? AND audit_key=? AND evidence_order=0",
                    (snapshot_id, audit_key),
                )
            elif case == "invalid_sha":
                connection.execute("PRAGMA ignore_check_constraints=ON")
                connection.execute(
                    "UPDATE historical_input_snapshot_provenance_evidence SET response_sha256='invalid' WHERE snapshot_id=? AND audit_key=? AND evidence_order=0",
                    (snapshot_id, audit_key),
                )
                connection.execute("PRAGMA ignore_check_constraints=OFF")
            elif case == "invalid_observed":
                connection.execute("PRAGMA ignore_check_constraints=ON")
                connection.execute(
                    "UPDATE historical_input_snapshot_provenance_evidence SET observed_at_utc='invalid' WHERE snapshot_id=? AND audit_key=? AND evidence_order=0",
                    (snapshot_id, audit_key),
                )
                connection.execute("PRAGMA ignore_check_constraints=OFF")
            elif case == "late_observed":
                connection.execute(
                    "UPDATE historical_input_snapshot_provenance_evidence SET observed_at_utc=? WHERE snapshot_id=? AND audit_key=? AND evidence_order=0",
                    ((CAPTURED + timedelta(seconds=3)).isoformat(timespec="microseconds"), snapshot_id, audit_key),
                )
            elif case in {"observed_mismatch", "available_mismatch"}:
                row = connection.execute(
                    """SELECT canonical_source_url,response_sha256,observed_at_utc
                       FROM historical_input_snapshot_provenance_evidence
                       WHERE snapshot_id=? AND audit_key=? AND evidence_order=0""",
                    (snapshot_id, audit_key),
                ).fetchone()
                column, value = (
                    ("observed_at_utc", (CAPTURED + timedelta(seconds=1)).isoformat(timespec="microseconds"))
                    if case == "observed_mismatch"
                    else ("available_at_utc", row[2])
                )
                connection.execute(
                    f"""UPDATE historical_input_snapshot_provenance_evidence
                        SET canonical_source_url=?, response_sha256=?, {column}=?
                        WHERE snapshot_id=? AND audit_key=? AND evidence_order=1""",
                    (row[0], row[1], value, snapshot_id, audit_key),
                )
            elif case == "orphan":
                connection.execute("PRAGMA foreign_keys=OFF")
                connection.execute(
                    """INSERT INTO historical_input_snapshot_provenance_evidence(
                        snapshot_id,audit_key,evidence_order,evidence_role,canonical_source_url,response_sha256,
                        available_at_utc,observed_at_utc
                    ) VALUES(?,?,?,?,?,?,?,?)""",
                    (snapshot_id, "orphan", 0, "track", "https://example.test/orphan", "a" * 64, None, CAPTURED.isoformat(timespec="microseconds")),
                )
                connection.commit()
                connection.execute("PRAGMA foreign_keys=ON")
            else:
                raise AssertionError(case)

        for case in (
            "missing", "wrong_role", "order", "invalid_sha", "invalid_observed", "late_observed",
            "observed_mismatch", "available_mismatch", "orphan",
        ):
            with self.subTest(case=case):
                connection, repository = self.repository()
                older, newer = self.save_older_and_newer(repository)
                mutate(connection, self.snapshot_id_for(connection, newer.identity.captured_at), case)
                connection.commit()
                with self.assertRaises(RepositoryDataIntegrityError):
                    self.load(repository)
                self.assertEqual(older.identity.captured_at, CAPTURED)

    def test_load_latest_incomplete_or_mapping_corruption_never_falls_back(self) -> None:
        connection, repository = self.repository()
        _older, newer = self.save_older_and_newer(repository)
        snapshot_id = self.snapshot_id_for(connection, newer.identity.captured_at)
        connection.execute("PRAGMA foreign_keys=OFF")
        connection.execute("DELETE FROM historical_input_snapshot_races WHERE snapshot_id=?", (snapshot_id,))
        connection.commit()
        connection.execute("PRAGMA foreign_keys=ON")
        with self.assertRaises(RepositoryDataIntegrityError):
            self.load(repository)

        connection, repository = self.repository()
        older = self.snapshot(captured_at=CAPTURED)
        newer = self.snapshot(
            entry_id=12,
            external_entry_id="entry-12",
            external_horse_id="horse-12",
            captured_at=CAPTURED + timedelta(seconds=1),
        )
        repository.save_snapshot(snapshot=older)
        repository.save_snapshot(snapshot=newer)
        snapshot_id = self.snapshot_id_for(connection, newer.identity.captured_at)
        connection.execute("DROP TRIGGER trg_his_external_entry_referenced_delete")
        connection.execute("PRAGMA foreign_keys=OFF")
        connection.execute(
            "DELETE FROM historical_input_external_entries WHERE external_entry_id=?",
            ("entry-12",),
        )
        connection.commit()
        connection.execute("PRAGMA foreign_keys=ON")
        with self.assertRaises(RepositoryDataIntegrityError):
            self.load(repository)

    def test_load_preserves_active_caller_transaction_without_writes_or_rollback(self) -> None:
        connection, repository = self.repository()
        repository.save_snapshot(snapshot=self.snapshot())
        connection.execute("BEGIN")
        connection.execute("INSERT INTO races(id) VALUES(3)")
        loaded = self.load(repository)
        self.assertIsNotNone(loaded)
        self.assertTrue(connection.in_transaction)
        self.assertEqual(connection.execute("SELECT id FROM races WHERE id=3").fetchone(), (3,))
        connection.rollback()
        self.assertIsNone(connection.execute("SELECT id FROM races WHERE id=3").fetchone())

        repository.save_snapshot(snapshot=self.snapshot(captured_at=CAPTURED + timedelta(seconds=1)))
        newest_id = self.snapshot_id_for(connection, CAPTURED + timedelta(seconds=1))
        connection.execute("UPDATE historical_input_snapshots SET content_sha256=? WHERE snapshot_id=?", ("0" * 64, newest_id))
        connection.commit()
        connection.execute("BEGIN")
        connection.execute("INSERT INTO races(id) VALUES(4)")
        with self.assertRaises(RepositoryDataIntegrityError):
            self.load(repository)
        self.assertTrue(connection.in_transaction)
        self.assertEqual(connection.execute("SELECT id FROM races WHERE id=4").fetchone(), (4,))
        connection.rollback()

    def test_load_source_has_no_transaction_or_bootstrap_behavior(self) -> None:
        source = inspect.getsource(SQLiteHistoricalInputSnapshotRepository.load_latest_snapshot)
        self.assertNotIn("BEGIN", source)
        self.assertNotIn("commit", source)
        self.assertNotIn("rollback", source)
        self.assertNotIn("PRAGMA", source)
        self.assertNotIn("apply_migrations", source)
        self.assertNotIn("sqlite3.connect", source)


if __name__ == "__main__":
    unittest.main()
