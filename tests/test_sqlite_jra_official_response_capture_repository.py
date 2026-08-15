from __future__ import annotations

from datetime import datetime, timedelta, timezone
import sqlite3
import unittest

from scripts.simulation.jra_official_identity import JRAExternalRaceIdentity, JRAOfficialFinalWinOddsRequestLocator
from scripts.simulation.jra_official_response_capture import JRAFinalWinOddsResponseCapture, JRAOfficialResponseCapture, JRAOfficialResponseCaptureMissingError
from scripts.simulation.jra_official_response_capture_migration_runner import apply_jra_capture_schema_migrations
from scripts.simulation.repositories.errors import RepositoryConflictError, RepositoryDataIntegrityError
from scripts.simulation.repositories.sqlite_jra_official_response_capture_repository import SQLiteJRAOfficialResponseCaptureRepository

URL = "https://www.jra.go.jp/JRADB/accessS.html?CNAME=pw01sde0106202504030420250913%2FDC"
BODY = "<meta charset=\"Shift_JIS\">\u30c6\u30b9\u30c8".encode("cp932")
T = datetime(2026, 1, 1, tzinfo=timezone.utc)

def item(**changes):
    values = dict(canonical_source_url=URL, response_body=BODY, charset="cp932", requested_at=T, observed_at=T, stored_at=T, http_status=200, content_type="text/html")
    values.update(changes)
    return JRAOfficialResponseCapture(**values)


def final_item(**changes):
    locator = JRAOfficialFinalWinOddsRequestLocator(
        endpoint_url="https://www.jra.go.jp/JRADB/accessO.html", cname="pw151ou1006202601021220260105Z/2E",
        external_race_identity=JRAExternalRaceIdentity("2026", "06", "01", "02", "12"),
        request_identity_sha256="9c4a4f2dfc7e2c21841f7a2bb3f36ec7397312a34b565ff7e511e74800774ade",
    )
    values = dict(request_locator=locator, response_body=BODY, charset="cp932", requested_at=T, observed_at=T, stored_at=T, http_status=200, content_type="text/html")
    values.update(changes)
    return JRAFinalWinOddsResponseCapture(**values)

class SQLiteJRACaptureTests(unittest.TestCase):
    def repo(self):
        c = sqlite3.connect(":memory:")
        apply_jra_capture_schema_migrations(c)
        return c, SQLiteJRAOfficialResponseCaptureRepository(connection=c)

    def test_exact_replay_dedup_observations_and_no_fallback(self):
        c, r = self.repo(); first = item(); r.save_capture(capture=first); r.save_capture(capture=first)
        self.assertEqual(r.load_supplied_response_for_evidence(canonical_source_url=URL, response_sha256=first.response_sha256, observed_at=T).response_body, BODY)
        second = item(observed_at=T + timedelta(microseconds=1), stored_at=T + timedelta(microseconds=1)); r.save_capture(capture=second)
        self.assertEqual(c.execute("SELECT COUNT(*) FROM jra_official_response_bodies").fetchone()[0], 1)
        self.assertEqual(c.execute("SELECT COUNT(*) FROM jra_official_response_captures").fetchone()[0], 2)
        with self.assertRaises(JRAOfficialResponseCaptureMissingError):
            r.load_supplied_response_for_evidence(canonical_source_url=URL, response_sha256=first.response_sha256, observed_at=T + timedelta(seconds=1))

    def test_conflict_and_corruption_fail_closed_without_repair(self):
        c, r = self.repo(); value = item(); r.save_capture(capture=value)
        with self.assertRaises(RepositoryConflictError): r.save_capture(capture=item(http_date="x"))
        c.execute("PRAGMA foreign_keys=OFF"); c.execute("DELETE FROM jra_official_response_bodies"); c.commit()
        with self.assertRaises(RepositoryDataIntegrityError): r.save_capture(capture=value)
        self.assertIsNone(c.execute("SELECT 1 FROM jra_official_response_bodies").fetchone())
        with self.assertRaises(RepositoryDataIntegrityError): r.load_capture(capture_id=value.capture_id)

    def test_final_odds_exact_lookup_and_cross_family_loads(self):
        _c, r = self.repo(); legacy = item(); final = final_item()
        r.save_capture(capture=legacy); r.save_final_win_odds_capture(capture=final)
        self.assertIsNone(r.load_capture(capture_id=final.capture_id))
        self.assertIsNone(r.load_final_win_odds_capture(capture_id=legacy.capture_id))
        supplied = r.load_final_win_odds_supplied_response_for_evidence(
            canonical_source_url=final.canonical_source_url,
            request_identity_sha256=final.request_locator.request_identity_sha256,
            response_sha256=final.response_sha256, observed_at=T,
        )
        self.assertEqual(supplied.response_body, BODY)
        with self.assertRaises(JRAOfficialResponseCaptureMissingError):
            r.load_final_win_odds_supplied_response_for_evidence(
                canonical_source_url=final.canonical_source_url,
                request_identity_sha256="0" * 64,
                response_sha256=final.response_sha256, observed_at=T,
            )
