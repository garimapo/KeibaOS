"""SQLite schema tests for the v010 historical-input snapshot migration (:memory: only)."""

from __future__ import annotations

import ast
import inspect
import sqlite3
import unittest

from scripts.migrations.runner import MIGRATIONS, apply_migrations, get_applied_versions
from scripts.migrations.versions import (
    v008_simulation_schema,
    v009_simulation_bet_plan_schema,
    v010_historical_input_snapshot_schema,
    v011_historical_past_race_time_difference_schema,
    v012_historical_input_evidence_schema,
    v013_historical_past_race_race_time_domain_schema,
    v014_historical_input_request_identity_schema,
    v015_jra_race_replay_seed_schema,
)


HISTORICAL_TABLES = {
    "historical_input_source_identities",
    "historical_input_external_races",
    "historical_input_external_entries",
    "historical_input_snapshots",
    "historical_input_snapshot_races",
    "historical_input_snapshot_entries",
    "historical_input_snapshot_past_races",
    "historical_input_snapshot_provenance",
    "historical_input_snapshot_provenance_evidence",
}
V010_INDEXES = {
    "ux_horses_race_id_id",
    "idx_his_external_races_internal",
    "idx_his_external_entries_internal",
    "idx_his_snapshots_latest_eligible",
}
V010_TRIGGERS = {
    "trg_his_snapshot_entry_mapping_insert",
    "trg_his_snapshot_entry_mapping_update",
    "trg_his_snapshot_header_mapping_update",
    "trg_his_external_entry_referenced_update",
    "trg_his_external_entry_referenced_delete",
}
UTC = "2026-08-05T12:00:00.000000+00:00"
CUTOFF = "2026-08-05T12:30:00.000000+00:00"
HASH = "a" * 64


class HistoricalInputSnapshotMigrationTests(unittest.TestCase):
    def db(self) -> sqlite3.Connection:
        connection = sqlite3.connect(":memory:")
        connection.execute("CREATE TABLE races(id INTEGER PRIMARY KEY)")
        connection.execute("CREATE TABLE horses(id INTEGER PRIMARY KEY, race_id INTEGER NOT NULL)")
        connection.executemany("INSERT INTO races(id) VALUES(?)", ((1,), (2,)))
        connection.executemany("INSERT INTO horses(id, race_id) VALUES(?, ?)", ((11, 1), (12, 1), (21, 2)))
        connection.commit()
        return connection

    def migrated(self) -> sqlite3.Connection:
        connection = self.db()
        apply_migrations(connection)
        return connection

    def source_and_external_mapping(self, connection: sqlite3.Connection, *, race_id: int = 1, external_race_id: str = "race-1", external_entry_id: str = "entry-11", race_entry_id: int = 11) -> None:
        connection.execute(
            "INSERT OR IGNORE INTO historical_input_source_identities VALUES(?, ?)",
            ("NAR", "nar_official"),
        )
        connection.execute(
            "INSERT INTO historical_input_external_races VALUES(?, ?, ?, ?)",
            ("NAR", "nar_official", external_race_id, race_id),
        )
        connection.execute(
            "INSERT INTO historical_input_external_entries VALUES(?, ?, ?, ?, ?, ?)",
            ("NAR", "nar_official", external_race_id, external_entry_id, race_id, race_entry_id),
        )

    def header(self, connection: sqlite3.Connection, *, snapshot_id: int = 1, race_id: int = 1, external_race_id: str = "race-1", captured_at: str = UTC, cutoff: str = CUTOFF, digest: str = HASH, source_url: str | None = "https://example.test/race") -> None:
        connection.execute(
            """INSERT INTO historical_input_snapshots(
                snapshot_id, dataset_id, organization, source_system, external_race_id,
                internal_race_id, source_url, captured_at_utc, information_cutoff_utc, content_sha256
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (snapshot_id, "dataset-1", "NAR", "nar_official", external_race_id, race_id, source_url, captured_at, cutoff, digest),
        )

    def entry(self, connection: sqlite3.Connection, *, snapshot_id: int = 1, race_entry_id: int = 11, external_entry_id: str = "entry-11", horse_no: int = 1, entry_order: int = 0, external_horse_id: str | None = "horse-11") -> None:
        connection.execute(
            """INSERT INTO historical_input_snapshot_entries(
                snapshot_id, race_entry_id, external_entry_id, external_horse_id,
                horse_no, jockey, win_odds_text, entry_order
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?)""",
            (snapshot_id, race_entry_id, external_entry_id, external_horse_id, horse_no, "Jockey", "2", entry_order),
        )

    def past_race(self, connection: sqlite3.Connection, *, snapshot_id: int = 1, race_entry_id: int = 11, index: int = 0, finish: int = 1, passing_order: str | None = "") -> None:
        connection.execute(
            """INSERT INTO historical_input_snapshot_past_races(
                snapshot_id, race_entry_id, past_race_index, race_date, place, race_name, race_class,
                distance_m, track, weather, track_condition, finish, race_time, weight_text,
                weight_diff_text, jockey, popularity, odds_text, passing_order, fourth_corner_position
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (snapshot_id, race_entry_id, index, "2026-08-04", "Tokyo", "Prior", "Open", 1600, "turf", "sunny", "good", finish, "1:32.0", "480", "0", "Jockey", 0, "2", passing_order, 0),
        )

    def provenance(self, connection: sqlite3.Connection, *, input_type: str, audit_key: str, race_entry_id: int | None, past_race_index: int | None = None) -> None:
        connection.execute(
            """INSERT INTO historical_input_snapshot_provenance(
                snapshot_id, input_type, audit_key, source, source_id, race_entry_id, past_race_index
            ) VALUES(?, ?, ?, ?, ?, ?, ?)""",
            (1, input_type, audit_key, "nar_official", f"source-{audit_key}", race_entry_id, past_race_index),
        )
        role = {
            "track": "track", "entry": "entry", "odds": "odds_win", "jockey": "jockey",
        }.get(input_type, "past_race_absence_query" if past_race_index is None else "historical_race_context")
        connection.execute(
            """INSERT INTO historical_input_snapshot_provenance_evidence(
                snapshot_id,audit_key,evidence_order,evidence_role,canonical_source_url,response_sha256,available_at_utc,observed_at_utc
            ) VALUES(?,?,?,?,?,?,?,?)""",
            (1, audit_key, 0, role, "https://example.test/evidence", HASH, None, UTC),
        )

    def test_identity_registration_schema_objects_and_no_backfill(self) -> None:
        connection = self.migrated()
        self.assertEqual(v010_historical_input_snapshot_schema.VERSION, 10)
        self.assertEqual(v010_historical_input_snapshot_schema.NAME, "v010_historical_input_snapshot_schema")
        self.assertEqual(v011_historical_past_race_time_difference_schema.VERSION, 11)
        self.assertEqual(v011_historical_past_race_time_difference_schema.NAME, "v011_historical_past_race_time_difference_schema")
        self.assertEqual(v012_historical_input_evidence_schema.VERSION, 12)
        self.assertEqual(v012_historical_input_evidence_schema.NAME, "v012_historical_input_evidence_schema")
        self.assertEqual(v013_historical_past_race_race_time_domain_schema.VERSION, 13)
        self.assertEqual(v013_historical_past_race_race_time_domain_schema.NAME, "v013_historical_past_race_race_time_domain_schema")
        self.assertEqual(v014_historical_input_request_identity_schema.VERSION, 14)
        self.assertEqual(v014_historical_input_request_identity_schema.NAME, "v014_historical_input_request_identity_schema")
        self.assertEqual(v015_jra_race_replay_seed_schema.VERSION, 15)
        self.assertEqual(v015_jra_race_replay_seed_schema.NAME, "v015_jra_race_replay_seed_schema")
        self.assertEqual(tuple(item.VERSION for item in MIGRATIONS), (8, 9, 10, 11, 12, 13, 14, 15))
        self.assertEqual(
            get_applied_versions(connection),
            {8: "v008_simulation_schema", 9: "v009_simulation_bet_plan_schema", 10: "v010_historical_input_snapshot_schema", 11: "v011_historical_past_race_time_difference_schema", 12: "v012_historical_input_evidence_schema", 13: "v013_historical_past_race_race_time_domain_schema", 14: "v014_historical_input_request_identity_schema", 15: "v015_jra_race_replay_seed_schema"},
        )
        self.assertEqual(
            {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'historical_input_%'")},
            HISTORICAL_TABLES,
        )
        self.assertEqual(
            {
                row[0]
                for row in connection.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE '%his%'")
                if not row[0].startswith("sqlite_autoindex")
            }
            | {"ux_horses_race_id_id"},
            V010_INDEXES | {"ux_historical_input_external_entries_exact_mapping"},
        )
        self.assertEqual(
            {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE 'trg_his_%'")},
            V010_TRIGGERS,
        )
        self.assertEqual(connection.execute("PRAGMA foreign_keys").fetchone()[0], 1)
        self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
        apply_migrations(connection)
        self.assertEqual(
            connection.execute("SELECT version FROM schema_migrations ORDER BY version").fetchall(),
            [(8,), (9,), (10,), (11,), (12,), (13,), (14,), (15,)],
        )
        self.assertEqual(connection.execute("SELECT count(*) FROM historical_input_snapshots").fetchone()[0], 0)
        for table in HISTORICAL_TABLES:
            self.assertEqual(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0], 0)
        index_columns = tuple(row[2] for row in connection.execute("PRAGMA index_info(ux_horses_race_id_id)"))
        self.assertEqual(index_columns, ("race_id", "id"))
        self.assertEqual(connection.execute("PRAGMA index_list(horses)").fetchone()[2], 1)

    def test_v014_adds_nullable_request_identity_without_rewriting_nonempty_store(self) -> None:
        connection = self.db()
        apply_migrations(connection, migrations=MIGRATIONS[:-2])
        self.source_and_external_mapping(connection)
        self.header(connection)
        self.entry(connection)
        self.provenance(connection, input_type="track", audit_key="track", race_entry_id=None)
        connection.commit()
        v014_historical_input_request_identity_schema.apply(connection)
        self.assertEqual(
            connection.execute(
                "SELECT request_identity_sha256 FROM historical_input_snapshot_provenance_evidence"
            ).fetchone(),
            (None,),
        )
        connection.commit()
        with self.assertRaises(sqlite3.IntegrityError):
            connection.execute(
                "UPDATE historical_input_snapshot_provenance_evidence SET request_identity_sha256='A'"
            )
        self.assertTrue(connection.in_transaction)
        connection.rollback()
        self.assertEqual(connection.execute("SELECT count(*) FROM historical_input_snapshots").fetchone(), (1,))

    def test_apply_is_transaction_neutral(self) -> None:
        connection = self.db()
        connection.execute("BEGIN")
        v010_historical_input_snapshot_schema.apply(connection)
        self.assertTrue(connection.in_transaction)
        connection.rollback()
        self.assertIsNone(connection.execute("SELECT 1 FROM sqlite_master WHERE name='historical_input_snapshots'").fetchone())
        function = next(node for node in ast.parse(inspect.getsource(v010_historical_input_snapshot_schema)).body if isinstance(node, ast.FunctionDef) and node.name == "apply")
        calls = [node for node in ast.walk(function) if isinstance(node, ast.Call)]
        self.assertEqual(len(calls), 1)
        self.assertIsInstance(calls[0].func, ast.Attribute)
        self.assertEqual(calls[0].func.attr, "execute")

    def test_utc_suffix_clauses_match_approved_ddl(self) -> None:
        source = inspect.getsource(v010_historical_input_snapshot_schema)
        for field in (
            "captured_at_utc",
            "information_cutoff_utc",
            "scheduled_start_at_utc",
            "available_at_utc",
            "observed_at_utc",
        ):
            self.assertIn(f"substr({field}, -6) = '+00:00'", source)

    def test_identity_foreign_keys_and_restrict_linkage(self) -> None:
        connection = self.migrated()
        self.source_and_external_mapping(connection)
        self.header(connection)
        with self.assertRaises(sqlite3.IntegrityError):
            self.header(connection, snapshot_id=2, cutoff="2026-08-05T12:31:00.000000+00:00")
        with self.assertRaises(sqlite3.IntegrityError):
            self.header(connection, snapshot_id=3, digest="b" * 64)
        self.header(connection, snapshot_id=4, captured_at="2026-08-05T12:00:01.000000+00:00")
        with self.assertRaises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO historical_input_external_races VALUES('NAR', 'other', 'missing', 999)")
        with self.assertRaises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO historical_input_external_entries VALUES('NAR', 'nar_official', 'race-1', 'missing', 1, 999)")
        self.entry(connection)
        with self.assertRaises(sqlite3.IntegrityError):
            connection.execute("DELETE FROM races WHERE id=1")
        with self.assertRaises(sqlite3.IntegrityError):
            connection.execute("UPDATE horses SET race_id=2 WHERE id=11")
        with self.assertRaises(sqlite3.IntegrityError):
            self.entry(connection, external_entry_id="not-mapped")
        with self.assertRaises(sqlite3.IntegrityError):
            connection.execute("UPDATE historical_input_snapshot_entries SET external_entry_id='not-mapped' WHERE snapshot_id=1 AND race_entry_id=11")
        self.source_and_external_mapping(connection, race_id=2, external_race_id="race-2", external_entry_id="entry-21", race_entry_id=21)
        with self.assertRaises(sqlite3.IntegrityError):
            connection.execute("UPDATE historical_input_snapshots SET external_race_id='race-2', internal_race_id=2 WHERE snapshot_id=1")
        with self.assertRaises(sqlite3.IntegrityError):
            connection.execute("UPDATE historical_input_external_entries SET external_entry_id='changed' WHERE organization='NAR' AND source_system='nar_official' AND external_race_id='race-1' AND external_entry_id='entry-11'")
        with self.assertRaises(sqlite3.IntegrityError):
            connection.execute("DELETE FROM historical_input_external_entries WHERE organization='NAR' AND source_system='nar_official' AND external_race_id='race-1' AND external_entry_id='entry-11'")

    def test_storage_checks_past_and_provenance_shapes(self) -> None:
        connection = self.migrated()
        self.source_and_external_mapping(connection)
        self.header(connection)
        self.entry(connection, entry_order=0, external_horse_id="horse-11")
        self.past_race(connection, passing_order="")
        self.provenance(connection, input_type="track", audit_key="track", race_entry_id=None)
        self.provenance(connection, input_type="entry", audit_key="entry/11", race_entry_id=11)
        self.provenance(connection, input_type="odds", audit_key="odds/11", race_entry_id=11)
        self.provenance(connection, input_type="jockey", audit_key="jockey/11", race_entry_id=11)
        self.provenance(connection, input_type="past_race", audit_key="past_race/11/0", race_entry_id=11, past_race_index=0)
        self.provenance(connection, input_type="past_race", audit_key="past_race/11/none", race_entry_id=11)
        self.assertEqual(connection.execute("SELECT source_url FROM historical_input_snapshots WHERE snapshot_id=1").fetchone()[0], "https://example.test/race")
        self.assertEqual(connection.execute("SELECT external_horse_id FROM historical_input_snapshot_entries WHERE snapshot_id=1 AND race_entry_id=11").fetchone()[0], "horse-11")
        self.assertEqual(connection.execute("SELECT passing_order, popularity, fourth_corner_position FROM historical_input_snapshot_past_races").fetchone(), ("", 0, 0))
        self.assertEqual(connection.execute("SELECT entry_order FROM historical_input_snapshot_entries").fetchone()[0], 0)
        self.assertEqual(connection.execute("SELECT past_race_index FROM historical_input_snapshot_past_races").fetchone()[0], 0)
        with self.assertRaises(sqlite3.IntegrityError):
            self.past_race(connection, index=1, passing_order=None)
        connection.execute(
            "INSERT INTO historical_input_external_entries VALUES('NAR', 'nar_official', 'race-1', 'entry-12', 1, 12)"
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.entry(connection, race_entry_id=12, external_entry_id="entry-12", entry_order=-1)
        with self.assertRaises(sqlite3.IntegrityError):
            self.entry(connection, race_entry_id=12, external_entry_id="entry-12", entry_order=1, external_horse_id="",)
        with self.assertRaises(sqlite3.IntegrityError):
            self.entry(connection, race_entry_id=12, external_entry_id="entry-12", horse_no=0, entry_order=1)
        with self.assertRaises(sqlite3.IntegrityError):
            self.past_race(connection, index=2, finish=0)
        with self.assertRaises(sqlite3.IntegrityError):
            self.provenance(connection, input_type="odds_win", audit_key="bad", race_entry_id=11)
        with self.assertRaises(sqlite3.IntegrityError):
            self.provenance(connection, input_type="track", audit_key="track/11", race_entry_id=11)
        with self.assertRaises(sqlite3.IntegrityError):
            self.provenance(connection, input_type="entry", audit_key="entry/none", race_entry_id=None)
        types = {row[1]: row[2] for row in connection.execute("PRAGMA table_info(historical_input_snapshot_entries)")}
        self.assertEqual(types["win_odds_text"], "TEXT")
        past_types = {row[1]: row[2] for row in connection.execute("PRAGMA table_info(historical_input_snapshot_past_races)")}
        self.assertEqual({past_types[name] for name in ("weight_text", "weight_diff_text", "odds_text")}, {"TEXT"})
        self.assertNotIn("reference_time_difference_seconds_text", past_types)

    def test_v011_keeps_identity_linkage_rows_when_snapshot_store_is_empty(self) -> None:
        connection = self.db()
        apply_migrations(connection, MIGRATIONS[:4])
        self.source_and_external_mapping(connection)
        connection.commit()
        columns = {row[1] for row in connection.execute("PRAGMA table_info(historical_input_snapshot_past_races)")}
        self.assertNotIn("margin_text", columns)
        self.assertIn("reference_time_difference_seconds_text", columns)
        self.assertEqual(connection.execute("SELECT COUNT(*) FROM historical_input_snapshots").fetchone()[0], 0)
        self.assertEqual(connection.execute("SELECT COUNT(*) FROM historical_input_source_identities").fetchone()[0], 1)
        self.assertEqual(connection.execute("SELECT COUNT(*) FROM historical_input_external_races").fetchone()[0], 1)
        self.assertEqual(connection.execute("SELECT COUNT(*) FROM historical_input_external_entries").fetchone()[0], 1)
        self.assertEqual(get_applied_versions(connection)[11], "v011_historical_past_race_time_difference_schema")

    def test_v012_rejects_nonempty_snapshot_store_atomically(self) -> None:
        connection = self.db()
        apply_migrations(connection, MIGRATIONS[:4])
        self.source_and_external_mapping(connection)
        self.header(connection)
        connection.commit()
        with self.assertRaisesRegex(RuntimeError, "nonempty historical input snapshot store"):
            apply_migrations(connection)
        columns = {row[1] for row in connection.execute("PRAGMA table_info(historical_input_snapshot_past_races)")}
        self.assertNotIn("margin_text", columns)
        self.assertIn("reference_time_difference_seconds_text", columns)
        self.assertNotIn(12, get_applied_versions(connection))
        self.assertEqual(connection.execute("SELECT COUNT(*) FROM historical_input_snapshots").fetchone()[0], 1)
        provenance_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(historical_input_snapshot_provenance)")
        }
        self.assertIn("available_at_utc", provenance_columns)
        self.assertIn("observed_at_utc", provenance_columns)
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertNotIn("historical_input_snapshot_provenance_evidence", tables)
        self.assertNotIn("historical_input_snapshot_provenance_v2", tables)
        self.assertFalse(connection.in_transaction)

    def test_v013_removes_obsolete_column_from_empty_store_and_preserves_linkage(self) -> None:
        connection = self.db()
        apply_migrations(connection, MIGRATIONS[:5])
        self.source_and_external_mapping(connection)
        connection.commit()
        before = {row[1] for row in connection.execute("PRAGMA table_info(historical_input_snapshot_past_races)")}
        self.assertIn("reference_time_difference_seconds_text", before)
        apply_migrations(connection)
        after = {row[1] for row in connection.execute("PRAGMA table_info(historical_input_snapshot_past_races)")}
        self.assertNotIn("reference_time_difference_seconds_text", after)
        self.assertEqual(get_applied_versions(connection)[13], "v013_historical_past_race_race_time_domain_schema")
        self.assertEqual(connection.execute("SELECT COUNT(*) FROM historical_input_snapshots").fetchone()[0], 0)
        self.assertEqual(connection.execute("SELECT COUNT(*) FROM historical_input_source_identities").fetchone()[0], 1)
        self.assertEqual(connection.execute("SELECT COUNT(*) FROM historical_input_external_races").fetchone()[0], 1)
        self.assertEqual(connection.execute("SELECT COUNT(*) FROM historical_input_external_entries").fetchone()[0], 1)

    def test_v013_rejects_nonempty_snapshot_store_before_schema_mutation(self) -> None:
        connection = self.db()
        apply_migrations(connection, MIGRATIONS[:5])
        self.source_and_external_mapping(connection)
        self.header(connection)
        connection.commit()
        with self.assertRaisesRegex(RuntimeError, "nonempty historical input snapshot store"):
            apply_migrations(connection)
        columns = {row[1] for row in connection.execute("PRAGMA table_info(historical_input_snapshot_past_races)")}
        self.assertIn("reference_time_difference_seconds_text", columns)
        self.assertNotIn(13, get_applied_versions(connection))
        self.assertEqual(connection.execute("SELECT COUNT(*) FROM historical_input_snapshots").fetchone()[0], 1)
        self.assertFalse(connection.in_transaction)

    def test_date_datetime_and_nonempty_text_checks_do_not_trim(self) -> None:
        connection = self.migrated()
        connection.execute("INSERT INTO historical_input_source_identities VALUES(' ', 'whitespace')")
        self.source_and_external_mapping(connection)
        with self.assertRaises(sqlite3.IntegrityError):
            self.header(connection, captured_at="2026-08-05T12:00:00+00:00")
        with self.assertRaises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO historical_input_external_races VALUES('NAR', 'nar_official', '', 1)")
        self.header(connection)
        with self.assertRaises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO historical_input_snapshot_races VALUES(1, '2026-08-05', ?, 'Tokyo', 0, 'turf', 'good', NULL, NULL, NULL)",
                (UTC,),
            )
        with self.assertRaises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO historical_input_snapshot_races VALUES(1, '20260805', ?, 'Tokyo', 1600, 'turf', 'good', NULL, NULL, NULL)", (UTC,))


if __name__ == "__main__":
    unittest.main()
