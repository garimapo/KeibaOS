from __future__ import annotations

import sqlite3
import unittest
from datetime import datetime, timezone

from scripts.simulation.jra_official_response_capture_migration import NAME, VERSION, apply
from scripts.simulation.jra_official_response_capture_migration_v002 import NAME as NAME_V2, VERSION as VERSION_V2
from scripts.simulation.jra_official_response_capture_migration_v003 import NAME as NAME_V3, VERSION as VERSION_V3
from scripts.simulation.jra_official_response_capture_migration_v004 import NAME as NAME_V4, VERSION as VERSION_V4
from scripts.simulation.jra_official_response_capture_migration_runner import apply_jra_capture_schema_migrations, get_applied_jra_capture_schema_versions
from scripts.simulation.jra_official_response_capture import JRAFinalWinOddsResponseCapture, JRAOfficialResponseCapture, JRAOfficialTargetRaceCardResponseCapture, JRATargetRaceSelectionResponseCapture
from scripts.simulation.jra_official_identity import build_jra_final_win_odds_request_locator
from scripts.simulation.jra_target_race_card_locator import build_jra_target_race_selection_request_locator
from scripts.simulation.repositories.sqlite_jra_official_response_capture_repository import SQLiteJRAOfficialResponseCaptureRepository


class JRAMigrationTests(unittest.TestCase):
    _REGISTRY = "jra_official_response_capture_schema_migrations"

    def _replace_fixture_sql_once(self, sql: str, change: tuple[str, str]) -> str:
        old, new = change
        self.assertGreaterEqual(sql.count(old), 1)
        return sql.replace(old, new, 1)

    def _assert_constructed_fixture_schema(
        self,
        connection: sqlite3.Connection,
        *,
        body_sql: str,
        capture_sql: str,
        evidence_index_sql: str,
        request_index_sql: str | None = None,
    ) -> None:
        expected = {
            "jra_official_response_bodies": body_sql,
            "jra_official_response_captures": capture_sql,
            "ux_jra_official_response_captures_evidence": evidence_index_sql,
        }
        if request_index_sql is not None:
            expected["ux_jra_official_response_captures_request_evidence"] = request_index_sql
        for name, sql in expected.items():
            row = connection.execute(
                "SELECT sql FROM sqlite_master WHERE name=?", (name,)
            ).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], sql)
        self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone(), ("ok",))
        self.assertFalse(connection.in_transaction)

    def _v003_connection(self, *, capture_change: tuple[str, str] | None = None) -> sqlite3.Connection:
        source = sqlite3.connect(":memory:")
        apply(source)
        from scripts.simulation.jra_official_response_capture_migration_v002 import apply as apply_v002
        from scripts.simulation.jra_official_response_capture_migration_v003 import apply as apply_v003
        source.execute("PRAGMA foreign_keys=ON")
        source.execute("BEGIN IMMEDIATE")
        apply_v002(source)
        apply_v003(source)
        source.commit()
        body_sql = source.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='jra_official_response_bodies'").fetchone()[0]
        capture_sql = source.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='jra_official_response_captures'").fetchone()[0]
        index_one = source.execute("SELECT sql FROM sqlite_master WHERE type='index' AND name='ux_jra_official_response_captures_evidence'").fetchone()[0]
        index_two = source.execute("SELECT sql FROM sqlite_master WHERE type='index' AND name='ux_jra_official_response_captures_request_evidence'").fetchone()[0]
        if capture_change is not None:
            capture_sql = self._replace_fixture_sql_once(capture_sql, capture_change)
        c = sqlite3.connect(":memory:")
        c.execute("""CREATE TABLE jra_official_response_capture_schema_migrations (
            version INTEGER PRIMARY KEY CHECK(typeof(version)='integer' AND version>0),
            name TEXT NOT NULL UNIQUE CHECK(typeof(name)='text' AND length(name)>0)
        ) WITHOUT ROWID""")
        c.executemany(
            "INSERT INTO jra_official_response_capture_schema_migrations(version,name) VALUES(?,?)",
            ((VERSION, NAME), (VERSION_V2, NAME_V2), (VERSION_V3, NAME_V3)),
        )
        c.execute(body_sql); c.execute(capture_sql); c.execute(index_one); c.execute(index_two); c.commit()
        self._assert_constructed_fixture_schema(
            c,
            body_sql=body_sql,
            capture_sql=capture_sql,
            evidence_index_sql=index_one,
            request_index_sql=index_two,
        )
        return c

    def _weakened_v002_connection(self, *, body_change: tuple[str, str] | None = None, capture_change: tuple[str, str] | None = None, evidence_sql: str | None = None, request_sql: str | None = None) -> sqlite3.Connection:
        source = sqlite3.connect(":memory:")
        apply(source)
        from scripts.simulation.jra_official_response_capture_migration_v002 import apply as apply_v002
        source.execute("PRAGMA foreign_keys=ON"); source.execute("BEGIN IMMEDIATE"); apply_v002(source); source.commit()
        body_sql = source.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='jra_official_response_bodies'").fetchone()[0]
        capture_sql = source.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='jra_official_response_captures'").fetchone()[0]
        index_one = source.execute("SELECT sql FROM sqlite_master WHERE type='index' AND name='ux_jra_official_response_captures_evidence'").fetchone()[0]
        index_two = source.execute("SELECT sql FROM sqlite_master WHERE type='index' AND name='ux_jra_official_response_captures_request_evidence'").fetchone()[0]
        if body_change is not None:
            body_sql = self._replace_fixture_sql_once(body_sql, body_change)
        if capture_change is not None:
            capture_sql = self._replace_fixture_sql_once(capture_sql, capture_change)
        c = sqlite3.connect(":memory:")
        c.execute("""CREATE TABLE jra_official_response_capture_schema_migrations (
            version INTEGER PRIMARY KEY CHECK(typeof(version)='integer' AND version>0),
            name TEXT NOT NULL UNIQUE CHECK(typeof(name)='text' AND length(name)>0)
        ) WITHOUT ROWID""")
        c.executemany("INSERT INTO jra_official_response_capture_schema_migrations(version,name) VALUES(?,?)", ((VERSION, NAME), (VERSION_V2, NAME_V2)))
        selected_evidence_sql = evidence_sql or index_one
        selected_request_sql = request_sql or index_two
        c.execute(body_sql); c.execute(capture_sql); c.execute(selected_evidence_sql); c.execute(selected_request_sql); c.commit()
        self._assert_constructed_fixture_schema(
            c,
            body_sql=body_sql,
            capture_sql=capture_sql,
            evidence_index_sql=selected_evidence_sql,
            request_index_sql=selected_request_sql,
        )
        return c

    def _weakened_v001_connection(self, *, body_change: tuple[str, str] | None = None, capture_change: tuple[str, str] | None = None, index_sql: str | None = None) -> sqlite3.Connection:
        source = sqlite3.connect(":memory:")
        apply(source)
        body_sql = source.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='jra_official_response_bodies'").fetchone()[0]
        capture_sql = source.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='jra_official_response_captures'").fetchone()[0]
        default_index = source.execute("SELECT sql FROM sqlite_master WHERE type='index' AND name='ux_jra_official_response_captures_evidence'").fetchone()[0]
        if body_change is not None:
            body_sql = body_sql.replace(*body_change)
        if capture_change is not None:
            capture_sql = capture_sql.replace(*capture_change)
        c = sqlite3.connect(":memory:")
        c.execute("""CREATE TABLE jra_official_response_capture_schema_migrations (
            version INTEGER PRIMARY KEY CHECK(typeof(version)='integer' AND version>0),
            name TEXT NOT NULL UNIQUE CHECK(typeof(name)='text' AND length(name)>0)
        ) WITHOUT ROWID""")
        c.execute("INSERT INTO jra_official_response_capture_schema_migrations(version,name) VALUES(?,?)", (VERSION, NAME))
        c.execute(body_sql); c.execute(capture_sql); c.execute(default_index if index_sql is None else index_sql)
        c.commit()
        return c

    def _reject_registry(self, ddl: str) -> None:
        c = sqlite3.connect(":memory:")
        c.execute(ddl)
        c.commit()
        with self.assertRaises(RuntimeError):
            apply_jra_capture_schema_migrations(c)
        self.assertFalse(c.in_transaction)
        self.assertIsNone(c.execute("SELECT 1 FROM sqlite_master WHERE name='jra_official_response_bodies'").fetchone())

    def test_dedicated_v001_fresh_and_idempotent(self):
        c = sqlite3.connect(":memory:")
        apply_jra_capture_schema_migrations(c)
        self.assertEqual(get_applied_jra_capture_schema_versions(c), {VERSION: NAME, VERSION_V2: NAME_V2, VERSION_V3: NAME_V3, VERSION_V4: NAME_V4})
        self.assertEqual({r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}, {"jra_official_response_capture_schema_migrations", "jra_official_response_bodies", "jra_official_response_captures"})
        apply_jra_capture_schema_migrations(c)
        self.assertFalse(c.in_transaction)
        self.assertIsNone(c.execute("SELECT 1 FROM sqlite_master WHERE name='schema_migrations'").fetchone())

    def test_apply_is_transaction_neutral_and_bad_registry_fails(self):
        c = sqlite3.connect(":memory:")
        apply(c)
        self.assertFalse(c.in_transaction)
        c2 = sqlite3.connect(":memory:")
        c2.execute("CREATE TABLE jra_official_response_capture_schema_migrations(version INTEGER, name TEXT)")
        with self.assertRaises(RuntimeError):
            apply_jra_capture_schema_migrations(c2)
        self.assertIsNone(c2.execute("SELECT 1 FROM sqlite_master WHERE name='jra_official_response_bodies'").fetchone())

    def test_exact_preexisting_registry_is_accepted(self):
        c = sqlite3.connect(":memory:")
        c.execute("""CREATE TABLE jra_official_response_capture_schema_migrations (
            version INTEGER PRIMARY KEY CHECK(typeof(version)='integer' AND version>0),
            name TEXT NOT NULL UNIQUE CHECK(typeof(name)='text' AND length(name)>0)
        ) WITHOUT ROWID""")
        c.commit()
        apply_jra_capture_schema_migrations(c)
        self.assertEqual(get_applied_jra_capture_schema_versions(c), {1: NAME, VERSION_V2: NAME_V2, VERSION_V3: NAME_V3, VERSION_V4: NAME_V4})

    def test_constraint_probes_rollback_without_changing_registered_rows(self):
        c = sqlite3.connect(":memory:")
        c.execute("""CREATE TABLE jra_official_response_capture_schema_migrations (
            version INTEGER PRIMARY KEY CHECK(typeof(version)='integer' AND version>0),
            name TEXT NOT NULL UNIQUE CHECK(typeof(name)='text' AND length(name)>0)
        ) WITHOUT ROWID""")
        c.execute("INSERT INTO jra_official_response_capture_schema_migrations(version,name) VALUES(?,?)", (VERSION, NAME))
        c.commit()
        before = c.execute("SELECT version,name FROM jra_official_response_capture_schema_migrations").fetchall()
        self.assertEqual(get_applied_jra_capture_schema_versions(c), {VERSION: NAME})
        self.assertEqual(c.execute("SELECT version,name FROM jra_official_response_capture_schema_migrations").fetchall(), before)
        self.assertFalse(c.in_transaction)

    def test_weakened_registry_constraints_and_extra_columns_fail_closed(self):
        variants = (
            "CREATE TABLE jra_official_response_capture_schema_migrations(version INTEGER PRIMARY KEY CHECK(typeof(version)='integer'),name TEXT NOT NULL UNIQUE CHECK(typeof(name)='text' AND length(name)>0)) WITHOUT ROWID",
            "CREATE TABLE jra_official_response_capture_schema_migrations(version INTEGER PRIMARY KEY CHECK(version>0),name TEXT NOT NULL UNIQUE CHECK(typeof(name)='text' AND length(name)>0)) WITHOUT ROWID",
            "CREATE TABLE jra_official_response_capture_schema_migrations(version INTEGER PRIMARY KEY CHECK(typeof(version)='integer' AND version>0),name TEXT NOT NULL CHECK(typeof(name)='text' AND length(name)>0)) WITHOUT ROWID",
            "CREATE TABLE jra_official_response_capture_schema_migrations(version INTEGER PRIMARY KEY CHECK(typeof(version)='integer' AND version>0),name TEXT NOT NULL UNIQUE CHECK(typeof(name)='text')) WITHOUT ROWID",
            "CREATE TABLE jra_official_response_capture_schema_migrations(version INTEGER PRIMARY KEY CHECK(typeof(version)='integer' AND version>0),name TEXT NOT NULL UNIQUE CHECK(length(name)>0)) WITHOUT ROWID",
            "CREATE TABLE jra_official_response_capture_schema_migrations(version INTEGER PRIMARY KEY CHECK(typeof(version)='integer' AND version>0),name TEXT NOT NULL UNIQUE CHECK(typeof(name)='text' AND length(name)>0),extra TEXT) WITHOUT ROWID",
            "CREATE TABLE jra_official_response_capture_schema_migrations(version INTEGER PRIMARY KEY CHECK(typeof(version)='integer' AND version>0),name TEXT NOT NULL UNIQUE CHECK(typeof(name)='text' AND length(name)>0))",
            "CREATE TABLE jra_official_response_capture_schema_migrations(version INTEGER PRIMARY KEY,name TEXT NOT NULL UNIQUE) WITHOUT ROWID /* CHECK(typeof(version)='integer' AND version>0) CHECK(typeof(name)='text' AND length(name)>0) */",
        )
        for ddl in variants:
            with self.subTest(ddl=ddl):
                self._reject_registry(ddl)

    def test_registered_version_name_and_malformed_rows_fail_closed(self):
        for version, name, ignore in ((1, "wrong", False), (2, "future", False), (0, NAME, True), (1, "", True)):
            with self.subTest(version=version, name=name):
                c = sqlite3.connect(":memory:")
                apply_jra_capture_schema_migrations(c)
                if ignore:
                    c.execute("PRAGMA ignore_check_constraints=ON")
                c.execute("DELETE FROM jra_official_response_capture_schema_migrations")
                c.execute("INSERT INTO jra_official_response_capture_schema_migrations(version,name) VALUES(?,?)", (version, name))
                c.commit()
                if ignore:
                    c.execute("PRAGMA ignore_check_constraints=OFF")
                with self.assertRaises(RuntimeError):
                    apply_jra_capture_schema_migrations(c)
                self.assertFalse(c.in_transaction)

    def test_unregistered_capture_tables_are_not_adopted_or_repaired(self):
        for table in ("jra_official_response_bodies", "jra_official_response_captures"):
            with self.subTest(table=table):
                c = sqlite3.connect(":memory:")
                c.execute(f"CREATE TABLE {table}(value TEXT)")
                c.commit()
                with self.assertRaises(RuntimeError):
                    apply_jra_capture_schema_migrations(c)
                self.assertFalse(c.in_transaction)
                self.assertIsNotNone(c.execute("SELECT 1 FROM sqlite_master WHERE name=?", (table,)).fetchone())
                self.assertIsNone(c.execute("SELECT 1 FROM sqlite_master WHERE name=?", (self._REGISTRY,)).fetchone())

    def test_v002_rebuild_preserves_nonempty_v001_capture_and_body(self):
        c = sqlite3.connect(":memory:")
        apply(c)
        body = "<meta charset=\"Shift_JIS\">テスト".encode("cp932")
        capture = JRAOfficialResponseCapture(
            canonical_source_url="https://www.jra.go.jp/JRADB/accessS.html?CNAME=pw01sde0106202504030420250913%2FDC",
            response_body=body, charset="cp932", requested_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            observed_at=datetime(2026, 1, 1, tzinfo=timezone.utc), stored_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            http_status=200, content_type="text/html",
        )
        c.execute("INSERT INTO jra_official_response_bodies(response_sha256,response_body,byte_length) VALUES(?,?,?)", (capture.response_sha256, body, len(body)))
        c.execute("""INSERT INTO jra_official_response_captures(
            capture_id,schema_version,page_kind,canonical_source_url,response_sha256,charset,requested_at_utc,observed_at_utc,stored_at_utc,http_status,content_type,content_encoding,http_date,etag,last_modified,content_length
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            capture.capture_id, 1, capture.page_kind.value, capture.canonical_source_url, capture.response_sha256, "cp932",
            "2026-01-01T00:00:00.000000+00:00", "2026-01-01T00:00:00.000000+00:00", "2026-01-01T00:00:00.000000+00:00", 200, "text/html", None, None, None, None, None,
        ))
        c.commit(); c.execute("PRAGMA foreign_keys=ON"); c.execute("BEGIN IMMEDIATE")
        from scripts.simulation.jra_official_response_capture_migration_v002 import apply as apply_v002
        apply_v002(c); c.commit()
        row = c.execute("SELECT capture_id,request_method,request_identity_sha256,request_cname FROM jra_official_response_captures").fetchone()
        self.assertEqual(row, (capture.capture_id, "GET", None, None))
        self.assertEqual(c.execute("SELECT response_body FROM jra_official_response_bodies").fetchone()[0], body)

    def test_v002_rejects_weakened_v001_schema_before_mutation(self):
        variants = (
            ("missing_schema_version", None, (" AND schema_version=1", ""), None),
            ("missing_page_kind", None, (" CHECK(page_kind IN ('race_result','horse_profile_history'))", ""), None),
            ("missing_charset", None, (" CHECK(charset='cp932')", ""), None),
            ("missing_http_status", None, (" CHECK(typeof(http_status)='integer' AND http_status=200)", ""), None),
            ("missing_timestamp_order", None, (",\n        CHECK(requested_at_utc<=observed_at_utc AND observed_at_utc<=stored_at_utc)", ""), None),
            ("missing_foreign_key", None, (" REFERENCES jra_official_response_bodies(response_sha256) ON UPDATE RESTRICT ON DELETE RESTRICT", ""), None),
            ("missing_content_length", None, (" CHECK(content_length IS NULL OR (typeof(content_length)='integer' AND content_length>=0))", ""), None),
            ("missing_body_sha", (" AND response_sha256 NOT GLOB '*[^0-9a-f]*'", ""), None, None),
            ("missing_body_length", (" AND byte_length=length(response_body)", ""), None, None),
            ("nonunique_index", None, None, "CREATE INDEX ux_jra_official_response_captures_evidence ON jra_official_response_captures(canonical_source_url,response_sha256,observed_at_utc)"),
            ("partial_index", None, None, "CREATE UNIQUE INDEX ux_jra_official_response_captures_evidence ON jra_official_response_captures(canonical_source_url,response_sha256,observed_at_utc) WHERE 1"),
            ("wrong_index_order", None, None, "CREATE UNIQUE INDEX ux_jra_official_response_captures_evidence ON jra_official_response_captures(response_sha256,canonical_source_url,observed_at_utc)"),
            ("extra_capture_column", None, (",\n        CHECK(requested_at_utc<=observed_at_utc AND observed_at_utc<=stored_at_utc)", ", extra TEXT,\n        CHECK(requested_at_utc<=observed_at_utc AND observed_at_utc<=stored_at_utc)"), None),
            ("extra_body_column", (",\n        byte_length INTEGER", ", extra TEXT,\n        byte_length INTEGER"), None, None),
        )
        for name, body_change, capture_change, index_sql in variants:
            with self.subTest(name=name):
                c = self._weakened_v001_connection(body_change=body_change, capture_change=capture_change, index_sql=index_sql)
                before = c.execute("SELECT type,name,sql FROM sqlite_master WHERE name IN ('jra_official_response_bodies','jra_official_response_captures','ux_jra_official_response_captures_evidence') ORDER BY name").fetchall()
                with self.assertRaises(RuntimeError):
                    apply_jra_capture_schema_migrations(c)
                self.assertEqual(c.execute("SELECT type,name,sql FROM sqlite_master WHERE name IN ('jra_official_response_bodies','jra_official_response_captures','ux_jra_official_response_captures_evidence') ORDER BY name").fetchall(), before)
                self.assertEqual(get_applied_jra_capture_schema_versions(c), {VERSION: NAME})
                self.assertIsNone(c.execute("SELECT 1 FROM sqlite_master WHERE name='jra_official_response_captures_v001'").fetchone())
                self.assertFalse(c.in_transaction)

    def test_v003_rejects_weakened_v002_schema_before_mutation(self):
        variants = (
            ("schema", None, ("schema_version IN (1,2)", "schema_version IN (1,2,3)"), None, None),
            ("page", None, ("'final_win_odds'", "'final_win_odds','other'"), None, None),
            ("timestamps", None, (",\n        CHECK(requested_at_utc<=observed_at_utc AND observed_at_utc<=stored_at_utc)", ""), None, None),
            ("family", None, ("request_method='POST'", "request_method IN ('POST','GET')"), None, None),
            ("foreign", None, (" REFERENCES jra_official_response_bodies(response_sha256) ON UPDATE RESTRICT ON DELETE RESTRICT", ""), None, None),
            ("first_nonunique", None, None, "CREATE INDEX ux_jra_official_response_captures_evidence ON jra_official_response_captures(canonical_source_url,response_sha256,observed_at_utc) WHERE request_identity_sha256 IS NULL", None),
            ("first_predicate", None, None, "CREATE UNIQUE INDEX ux_jra_official_response_captures_evidence ON jra_official_response_captures(canonical_source_url,response_sha256,observed_at_utc) WHERE 1", None),
            ("first_order", None, None, "CREATE UNIQUE INDEX ux_jra_official_response_captures_evidence ON jra_official_response_captures(response_sha256,canonical_source_url,observed_at_utc) WHERE request_identity_sha256 IS NULL", None),
            ("request_nonunique", None, None, None, "CREATE INDEX ux_jra_official_response_captures_request_evidence ON jra_official_response_captures(canonical_source_url,request_identity_sha256,response_sha256,observed_at_utc) WHERE request_identity_sha256 IS NOT NULL"),
            ("request_predicate", None, None, None, "CREATE UNIQUE INDEX ux_jra_official_response_captures_request_evidence ON jra_official_response_captures(canonical_source_url,request_identity_sha256,response_sha256,observed_at_utc) WHERE 1"),
            ("request_order", None, None, None, "CREATE UNIQUE INDEX ux_jra_official_response_captures_request_evidence ON jra_official_response_captures(response_sha256,request_identity_sha256,canonical_source_url,observed_at_utc) WHERE request_identity_sha256 IS NOT NULL"),
            ("extra_capture", None, (",\n        CHECK(requested_at_utc<=observed_at_utc AND observed_at_utc<=stored_at_utc)", ", extra TEXT,\n        CHECK(requested_at_utc<=observed_at_utc AND observed_at_utc<=stored_at_utc)"), None, None),
            ("extra_body", (",\n        byte_length INTEGER", ", extra TEXT,\n        byte_length INTEGER"), None, None, None),
            ("body_check", (" AND byte_length=length(response_body)", ""), None, None, None),
            ("removed_request_identity_check", None, ("request_identity_sha256 TEXT NULL CHECK(request_identity_sha256 IS NULL OR (typeof(request_identity_sha256)='text' AND length(request_identity_sha256)=64 AND request_identity_sha256 NOT GLOB '*[^0-9a-f]*')),", "request_identity_sha256 TEXT NULL,"), None, None),
            ("weakened_request_identity_check", None, ("length(request_identity_sha256)=64", "length(request_identity_sha256)>=0"), None, None),
            ("removed_request_cname_check", None, ("request_cname TEXT NULL CHECK(request_cname IS NULL OR (typeof(request_cname)='text' AND length(request_cname)>0)),", "request_cname TEXT NULL,"), None, None),
            ("weakened_request_cname_check", None, ("length(request_cname)>0", "length(request_cname)>=0"), None, None),
            ("removed_request_method_check", None, ("request_method TEXT NOT NULL CHECK(request_method IN ('GET','POST')),", "request_method TEXT NOT NULL,"), None, None),
            ("extra_harmless_check", None, (",\n        CHECK(requested_at_utc<=observed_at_utc AND observed_at_utc<=stored_at_utc),", ",\n        CHECK(requested_at_utc<=observed_at_utc AND observed_at_utc<=stored_at_utc),\n        CHECK(1),"), None, None),
        )
        for name, body_change, capture_change, evidence_sql, request_sql in variants:
            with self.subTest(name=name):
                c = self._weakened_v002_connection(body_change=body_change, capture_change=capture_change, evidence_sql=evidence_sql, request_sql=request_sql)
                before = c.execute("SELECT type,name,sql FROM sqlite_master WHERE name LIKE 'jra_official_response_%' OR name LIKE 'ux_jra_official_response_captures_%' ORDER BY name").fetchall()
                with self.assertRaises(RuntimeError): apply_jra_capture_schema_migrations(c)
                self.assertEqual(c.execute("SELECT type,name,sql FROM sqlite_master WHERE name LIKE 'jra_official_response_%' OR name LIKE 'ux_jra_official_response_captures_%' ORDER BY name").fetchall(), before)
                self.assertEqual(get_applied_jra_capture_schema_versions(c), {VERSION: NAME, VERSION_V2: NAME_V2})
                self.assertIsNone(c.execute("SELECT 1 FROM sqlite_master WHERE name='jra_official_response_captures_v002'").fetchone())
                self.assertFalse(c.in_transaction)

    def test_v004_rebuild_preserves_populated_v003_rows_bodies_and_indexes(self):
        c = self._v003_connection()
        r = SQLiteJRAOfficialResponseCaptureRepository(connection=c)
        body = "<meta charset=\"Shift_JIS\">テスト".encode("cp932")
        timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)
        legacy = JRAOfficialResponseCapture(
            canonical_source_url="https://www.jra.go.jp/JRADB/accessS.html?CNAME=pw01sde0106202504030420250913%2FDC",
            response_body=body, charset="cp932", requested_at=timestamp, observed_at=timestamp,
            stored_at=timestamp, http_status=200, content_type="text/html",
        )
        final = JRAFinalWinOddsResponseCapture(
            request_locator=build_jra_final_win_odds_request_locator(cname="pw151ou1006202601021220260105Z/2E"),
            response_body=body, charset="cp932", requested_at=timestamp, observed_at=timestamp,
            stored_at=timestamp, http_status=200, content_type="text/html",
        )
        target = JRAOfficialTargetRaceCardResponseCapture(
            canonical_source_url="https://www.jra.go.jp/JRADB/accessD.html?CNAME=pw01dde0106202504030420250913%2FDC",
            response_body=body, charset="cp932", requested_at=timestamp, observed_at=timestamp,
            stored_at=timestamp, http_status=200, content_type="text/html",
        )
        r.save_capture(capture=legacy)
        r.save_final_win_odds_capture(capture=final)
        r.save_target_race_card_capture(capture=target)
        before_rows = c.execute("SELECT capture_id,schema_version,page_kind,canonical_source_url,response_sha256,charset,requested_at_utc,observed_at_utc,stored_at_utc,http_status,content_type,content_encoding,http_date,etag,last_modified,content_length,request_method,request_identity_sha256,request_cname FROM jra_official_response_captures ORDER BY capture_id").fetchall()
        before_bodies = c.execute("SELECT response_sha256,response_body,byte_length FROM jra_official_response_bodies ORDER BY response_sha256").fetchall()
        before_indexes = c.execute("SELECT name,sql FROM sqlite_master WHERE type='index' AND name LIKE 'ux_jra_official_response_captures_%' ORDER BY name").fetchall()
        apply_jra_capture_schema_migrations(c)
        self.assertEqual(get_applied_jra_capture_schema_versions(c), {VERSION: NAME, VERSION_V2: NAME_V2, VERSION_V3: NAME_V3, VERSION_V4: NAME_V4})
        self.assertEqual(c.execute("SELECT capture_id,schema_version,page_kind,canonical_source_url,response_sha256,charset,requested_at_utc,observed_at_utc,stored_at_utc,http_status,content_type,content_encoding,http_date,etag,last_modified,content_length,request_method,request_identity_sha256,request_cname FROM jra_official_response_captures ORDER BY capture_id").fetchall(), before_rows)
        self.assertEqual(c.execute("SELECT response_sha256,response_body,byte_length FROM jra_official_response_bodies ORDER BY response_sha256").fetchall(), before_bodies)
        self.assertEqual(c.execute("SELECT name,sql FROM sqlite_master WHERE type='index' AND name LIKE 'ux_jra_official_response_captures_%' ORDER BY name").fetchall(), before_indexes)
        self.assertEqual(c.execute("PRAGMA foreign_key_list(jra_official_response_captures)").fetchall(), [(0, 0, "jra_official_response_bodies", "response_sha256", "response_sha256", "RESTRICT", "RESTRICT", "NONE")])
        self.assertEqual([row for row in c.execute("PRAGMA table_list") if row[1] == "jra_official_response_captures"], [("main", "jra_official_response_captures", "table", 19, 1, 0)])
        selection = JRATargetRaceSelectionResponseCapture(
            request_locator=build_jra_target_race_selection_request_locator(cname="pw01drl00062025040320250403/DC"),
            response_body=body, charset="cp932", requested_at=timestamp, observed_at=timestamp,
            stored_at=timestamp, http_status=200, content_type="text/html",
        )
        r.save_target_race_selection_capture(capture=selection)
        self.assertEqual(r.load_target_race_selection_capture(capture_id=selection.capture_id), selection)
        template = list(c.execute("SELECT capture_id,schema_version,page_kind,canonical_source_url,response_sha256,charset,requested_at_utc,observed_at_utc,stored_at_utc,http_status,content_type,content_encoding,http_date,etag,last_modified,content_length,request_method,request_identity_sha256,request_cname FROM jra_official_response_captures WHERE capture_id=?", (selection.capture_id,)).fetchone())
        for label, updates in (
            ("v4_get", {16: "GET"}),
            ("v4_wrong_page", {2: "target_race_card"}),
            ("v4_null_request_identity", {17: None}),
            ("v4_null_cname", {18: None}),
            ("v3_target_selection", {1: 3}),
            ("v2_target_selection", {1: 2}),
        ):
            with self.subTest(label=label), self.assertRaises(sqlite3.IntegrityError):
                values = list(template)
                values[0] = f"__invalid_{label}__"
                values[6] = values[7] = values[8] = "2026-01-01T00:00:00.000001+00:00"
                for index, value in updates.items():
                    values[index] = value
                c.execute("INSERT INTO jra_official_response_captures(capture_id,schema_version,page_kind,canonical_source_url,response_sha256,charset,requested_at_utc,observed_at_utc,stored_at_utc,http_status,content_type,content_encoding,http_date,etag,last_modified,content_length,request_method,request_identity_sha256,request_cname) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", values)
        c.rollback()
        apply_jra_capture_schema_migrations(c)
        self.assertFalse(c.in_transaction)

    def test_v004_rejects_lookalike_v003_before_mutation_and_rolls_back_failure(self):
        variants = (
            ("version", ("schema_version IN (1,2,3)", "schema_version IN (1,2,3,4)")),
            ("page", ("'target_race_card'", "'target_race_card','other'")),
            ("family", ("page_kind='target_race_card' AND request_method='GET'", "page_kind='target_race_card' AND request_method IN ('GET','POST')")),
            ("extra_check", (",\n        CHECK(requested_at_utc<=observed_at_utc AND observed_at_utc<=stored_at_utc),", ",\n        CHECK(requested_at_utc<=observed_at_utc AND observed_at_utc<=stored_at_utc),\n        CHECK(1),")),
        )
        for label, change in variants:
            with self.subTest(label=label):
                c = self._v003_connection(capture_change=change)
                before = c.execute("SELECT type,name,sql FROM sqlite_master WHERE name LIKE 'jra_official_response_%' OR name LIKE 'ux_jra_official_response_captures_%' ORDER BY name").fetchall()
                with self.assertRaises(RuntimeError):
                    apply_jra_capture_schema_migrations(c)
                self.assertEqual(c.execute("SELECT type,name,sql FROM sqlite_master WHERE name LIKE 'jra_official_response_%' OR name LIKE 'ux_jra_official_response_captures_%' ORDER BY name").fetchall(), before)
                self.assertEqual(get_applied_jra_capture_schema_versions(c), {VERSION: NAME, VERSION_V2: NAME_V2, VERSION_V3: NAME_V3})
                self.assertIsNone(c.execute("SELECT 1 FROM sqlite_master WHERE name='jra_official_response_captures_v003'").fetchone())
                self.assertFalse(c.in_transaction)
        c = self._v003_connection()
        before_sql = c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='jra_official_response_captures'").fetchone()[0]
        before_registry = c.execute("SELECT version,name FROM jra_official_response_capture_schema_migrations ORDER BY version").fetchall()
        def reject_old_capture_drop(action, arg1, _arg2, _database, _source):
            return sqlite3.SQLITE_DENY if action == sqlite3.SQLITE_DROP_TABLE and arg1 == "jra_official_response_captures_v003" else sqlite3.SQLITE_OK
        c.set_authorizer(reject_old_capture_drop)
        try:
            with self.assertRaises(sqlite3.DatabaseError):
                apply_jra_capture_schema_migrations(c)
        finally:
            c.set_authorizer(None)
        self.assertEqual(c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='jra_official_response_captures'").fetchone()[0], before_sql)
        self.assertEqual(c.execute("SELECT version,name FROM jra_official_response_capture_schema_migrations ORDER BY version").fetchall(), before_registry)
        self.assertIsNone(c.execute("SELECT 1 FROM sqlite_master WHERE name='jra_official_response_captures_v003'").fetchone())
        self.assertFalse(c.in_transaction)
