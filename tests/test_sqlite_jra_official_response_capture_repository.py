from __future__ import annotations

from datetime import datetime, timedelta, timezone
import sqlite3
import unittest

from scripts.simulation.jra_official_identity import JRAExternalRaceIdentity, JRAOfficialFinalWinOddsRequestLocator, build_jra_final_win_odds_request_locator
from scripts.simulation.jra_official_response_capture import JRAFinalWinOddsResponseCapture, JRAOfficialResponseCapture, JRAOfficialResponseCaptureMissingError, JRAOfficialTargetRaceCardResponseCapture, JRATargetRaceSelectionResponseCapture
from scripts.simulation.jra_official_response_capture_migration_runner import apply_jra_capture_schema_migrations
from scripts.simulation.repositories.errors import RepositoryConflictError, RepositoryDataIntegrityError, RepositoryValidationError
from scripts.simulation.repositories.sqlite_jra_official_response_capture_repository import SQLiteJRAOfficialResponseCaptureRepository
from scripts.simulation.jra_target_race_card_locator import build_jra_target_race_selection_request_locator

URL = "https://www.jra.go.jp/JRADB/accessS.html?CNAME=pw01sde0106202504030420250913%2FDC"
HURL = "https://www.jra.go.jp/JRADB/accessU.html?CNAME=pw01dud001234567890%2FAB"
HURL_OTHER_HORSE = "https://www.jra.go.jp/JRADB/accessU.html?CNAME=pw01dud001234567891%2FAB"
HURL_OTHER_NAVIGATION = "https://www.jra.go.jp/JRADB/accessU.html?CNAME=pw01dud001234567890%2FAC"
BODY = "<meta charset=\"Shift_JIS\">\u30c6\u30b9\u30c8".encode("cp932")
T = datetime(2026, 1, 1, tzinfo=timezone.utc)
DURL = "https://www.jra.go.jp/JRADB/accessD.html?CNAME=pw01dde0106202504030420250913%2FDC"

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

def other_final_locator():
    return build_jra_final_win_odds_request_locator(cname="pw151ou1006202601021220260105Z/2F")

def target_item(**changes):
    values = dict(canonical_source_url=DURL, response_body=BODY, charset="cp932", requested_at=T, observed_at=T, stored_at=T, http_status=200, content_type="text/html")
    values.update(changes)
    return JRAOfficialTargetRaceCardResponseCapture(**values)


def selection_locator():
    return build_jra_target_race_selection_request_locator(cname="pw01drl00062025040320250403/DC")


def selection_item(**changes):
    values = dict(request_locator=selection_locator(), response_body=BODY, charset="cp932", requested_at=T, observed_at=T, stored_at=T, http_status=200, content_type="text/html")
    values.update(changes)
    return JRATargetRaceSelectionResponseCapture(**values)

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

    def test_target_card_family_is_exact_and_cross_family_closed(self):
        _c, r = self.repo(); legacy, final, target = item(), final_item(), target_item()
        r.save_capture(capture=legacy); r.save_final_win_odds_capture(capture=final); r.save_target_race_card_capture(capture=target)
        self.assertEqual(r.load_target_race_card_capture(capture_id=target.capture_id), target)
        self.assertIsNone(r.load_capture(capture_id=target.capture_id))
        self.assertIsNone(r.load_final_win_odds_capture(capture_id=target.capture_id))
        self.assertIsNone(r.load_target_race_card_capture(capture_id=legacy.capture_id))
        self.assertIsNone(r.load_target_race_card_capture(capture_id=final.capture_id))
        self.assertEqual(r.load_target_race_card_supplied_response_for_evidence(canonical_source_url=DURL, response_sha256=target.response_sha256, observed_at=T).response_body, BODY)

    def test_latest_target_card_lookup_is_exact_observation_bounded_and_fail_closed(self):
        c, r = self.repo()
        early = target_item(observed_at=T, stored_at=T + timedelta(hours=2))
        future = target_item(
            response_body=b'<meta charset="Shift_JIS">future',
            observed_at=T + timedelta(hours=2),
            stored_at=T + timedelta(hours=3),
        )
        other_url = DURL.replace("%2FDC", "%2FDD")
        other = target_item(canonical_source_url=other_url, response_body=b'<meta charset="Shift_JIS">other')
        r.save_target_race_card_capture(capture=early)
        r.save_target_race_card_capture(capture=future)
        r.save_target_race_card_capture(capture=other)
        self.assertEqual(
            r.load_latest_target_race_card_capture(
                canonical_target_race_card_url=DURL,
                observed_at_not_after=T,
            ),
            early,
        )
        self.assertEqual(
            r.load_latest_target_race_card_capture(
                canonical_target_race_card_url=DURL,
                observed_at_not_after=T + timedelta(hours=1),
            ),
            early,
        )
        self.assertEqual(
            r.load_latest_target_race_card_capture(
                canonical_target_race_card_url=DURL,
                observed_at_not_after=T + timedelta(hours=2),
            ),
            future,
        )
        self.assertIsNone(
            r.load_latest_target_race_card_capture(
                canonical_target_race_card_url=DURL,
                observed_at_not_after=T - timedelta(microseconds=1),
            )
        )
        self.assertIsNone(
            r.load_latest_target_race_card_capture(
                canonical_target_race_card_url=other_url,
                observed_at_not_after=T - timedelta(microseconds=1),
            )
        )
        for invalid in (URL, HURL, "https://www.jra.go.jp/JRADB/accessO.html", DURL.replace("%2F", "/")):
            with self.subTest(invalid=invalid), self.assertRaises(RepositoryValidationError):
                r.load_latest_target_race_card_capture(
                    canonical_target_race_card_url=invalid,
                    observed_at_not_after=T,
                )
        with self.assertRaises(RepositoryValidationError):
            r.load_latest_target_race_card_capture(
                canonical_target_race_card_url=DURL,
                observed_at_not_after=datetime(2026, 1, 1),
            )
        conflict_connection, conflict_repo = self.repo()
        conflict_repo.save_target_race_card_capture(capture=early)
        conflict_repo.save_target_race_card_capture(
            capture=target_item(response_body=b'<meta charset="Shift_JIS">same-time', stored_at=T + timedelta(hours=2))
        )
        with self.assertRaises(RepositoryDataIntegrityError):
            conflict_repo.load_latest_target_race_card_capture(
                canonical_target_race_card_url=DURL,
                observed_at_not_after=T,
            )
        corrupt_connection, corrupt_repo = self.repo()
        corrupt = target_item()
        corrupt_repo.save_target_race_card_capture(capture=corrupt)
        corrupt_connection.execute("PRAGMA ignore_check_constraints=ON")
        corrupt_connection.execute(
            "UPDATE jra_official_response_captures SET request_method='POST' WHERE capture_id=?",
            (corrupt.capture_id,),
        )
        corrupt_connection.execute("PRAGMA ignore_check_constraints=OFF")
        corrupt_connection.commit()
        with self.assertRaises(RepositoryDataIntegrityError):
            corrupt_repo.load_latest_target_race_card_capture(
                canonical_target_race_card_url=DURL,
                observed_at_not_after=T,
            )

    def test_target_race_selection_family_save_load_evidence_and_cross_family_closure(self):
        _c, r = self.repo(); legacy, final, target, selection = item(), final_item(), target_item(), selection_item()
        r.save_capture(capture=legacy); r.save_final_win_odds_capture(capture=final); r.save_target_race_card_capture(capture=target)
        r.save_target_race_selection_capture(capture=selection)
        r.save_target_race_selection_capture(capture=selection)
        self.assertEqual(r.load_target_race_selection_capture(capture_id=selection.capture_id), selection)
        self.assertEqual(
            _c.execute(
                "SELECT schema_version,page_kind,canonical_source_url,request_method,request_identity_sha256,request_cname FROM jra_official_response_captures WHERE capture_id=?",
                (selection.capture_id,),
            ).fetchone(),
            (4, "target_race_selection", selection.request_locator.endpoint_url, "POST", selection.request_locator.request_identity_sha256, selection.request_locator.cname),
        )
        self.assertIsNone(r.load_capture(capture_id=selection.capture_id))
        self.assertIsNone(r.load_final_win_odds_capture(capture_id=selection.capture_id))
        self.assertIsNone(r.load_target_race_card_capture(capture_id=selection.capture_id))
        self.assertIsNone(r.load_target_race_selection_capture(capture_id=legacy.capture_id))
        self.assertIsNone(r.load_target_race_selection_capture(capture_id=final.capture_id))
        self.assertIsNone(r.load_target_race_selection_capture(capture_id=target.capture_id))
        supplied = r.load_target_race_selection_supplied_response_for_evidence(
            request_locator=selection.request_locator,
            response_sha256=selection.response_sha256,
            observed_at=T,
        )
        self.assertEqual(supplied.response_body, BODY)
        with self.assertRaises(JRAOfficialResponseCaptureMissingError):
            r.load_target_race_selection_supplied_response_for_evidence(
                request_locator=selection.request_locator,
                response_sha256="0" * 64,
                observed_at=T,
            )
        with self.assertRaises(JRAOfficialResponseCaptureMissingError):
            r.load_target_race_selection_supplied_response_for_evidence(
                request_locator=build_jra_target_race_selection_request_locator(cname="pw01drl00062025040320250403/DD"),
                response_sha256=selection.response_sha256,
                observed_at=T,
            )
        with self.assertRaises(RepositoryValidationError):
            r.load_target_race_selection_capture(capture_id="jra-capture-v4:not-a-digest")
        with self.assertRaises(RepositoryValidationError):
            r.save_capture(capture=selection)
        with self.assertRaises(RepositoryValidationError):
            r.save_final_win_odds_capture(capture=selection)
        with self.assertRaises(RepositoryValidationError):
            r.save_target_race_card_capture(capture=selection)
        with self.assertRaises(RepositoryValidationError):
            r.save_target_race_selection_capture(capture=legacy)

    def test_target_race_selection_conflict_and_corrupt_selected_evidence_fail_closed(self):
        c, r = self.repo(); selection = selection_item(); r.save_target_race_selection_capture(capture=selection)
        with self.assertRaises(RepositoryConflictError):
            r.save_target_race_selection_capture(capture=selection_item(http_date="x"))
        c.execute("PRAGMA ignore_check_constraints=ON")
        c.execute("UPDATE jra_official_response_captures SET page_kind='target_race_card' WHERE capture_id=?", (selection.capture_id,))
        c.execute("PRAGMA ignore_check_constraints=OFF")
        c.commit()
        with self.assertRaises(RepositoryDataIntegrityError):
            r.load_target_race_selection_capture(capture_id=selection.capture_id)
        with self.assertRaises(RepositoryDataIntegrityError):
            r.load_target_race_selection_supplied_response_for_evidence(
                request_locator=selection.request_locator,
                response_sha256=selection.response_sha256,
                observed_at=T,
            )
        c.execute("PRAGMA foreign_keys=OFF")
        c.execute("DELETE FROM jra_official_response_bodies WHERE response_sha256=?", (selection.response_sha256,))
        c.commit()
        with self.assertRaises(RepositoryDataIntegrityError):
            r.save_target_race_selection_capture(capture=selection)
        c2, r2 = self.repo(); selection2 = selection_item(); r2.save_target_race_selection_capture(capture=selection2)
        c2.execute("DROP INDEX ux_jra_official_response_captures_request_evidence")
        c2.execute("""INSERT INTO jra_official_response_captures(
            capture_id,schema_version,page_kind,canonical_source_url,response_sha256,charset,requested_at_utc,observed_at_utc,stored_at_utc,http_status,content_type,content_encoding,http_date,etag,last_modified,content_length,request_method,request_identity_sha256,request_cname
        ) SELECT ?,schema_version,page_kind,canonical_source_url,response_sha256,charset,requested_at_utc,observed_at_utc,stored_at_utc,http_status,content_type,content_encoding,http_date,etag,last_modified,content_length,request_method,request_identity_sha256,request_cname FROM jra_official_response_captures WHERE capture_id=?""", ("jra-capture-v4:" + "f" * 64, selection2.capture_id))
        c2.commit()
        with self.assertRaises(RepositoryDataIntegrityError):
            r2.load_target_race_selection_supplied_response_for_evidence(
                request_locator=selection2.request_locator,
                response_sha256=selection2.response_sha256,
                observed_at=T,
            )

    def test_latest_horse_history_lookup_is_exact_inclusive_and_fail_closed(self):
        c, r = self.repo()
        earlier = item(canonical_source_url=HURL, observed_at=T, stored_at=T)
        later = item(canonical_source_url=HURL, response_body=b"<meta charset=\"Shift_JIS\">later", observed_at=T + timedelta(hours=2), stored_at=T + timedelta(hours=2))
        r.save_capture(capture=earlier); r.save_capture(capture=later)
        self.assertEqual(
            r.load_latest_horse_profile_history_supplied_response(
                canonical_horse_history_url=HURL, observed_at_not_after=T + timedelta(hours=1)
            ).response_body,
            BODY,
        )
        self.assertEqual(
            r.load_latest_horse_profile_history_supplied_response(canonical_horse_history_url=HURL, observed_at_not_after=T).response_body,
            BODY,
        )
        self.assertIsNone(r.load_latest_horse_profile_history_supplied_response(canonical_horse_history_url=HURL, observed_at_not_after=T - timedelta(microseconds=1)))
        with self.assertRaises(RepositoryValidationError):
            r.load_latest_horse_profile_history_supplied_response(canonical_horse_history_url=URL, observed_at_not_after=T)
        with self.assertRaises(RepositoryValidationError):
            r.load_latest_horse_profile_history_supplied_response(canonical_horse_history_url=DURL, observed_at_not_after=T)
        with self.assertRaises(RepositoryValidationError):
            r.load_latest_horse_profile_history_supplied_response(canonical_horse_history_url="https://www.jra.go.jp/JRADB/accessO.html", observed_at_not_after=T)
        with self.assertRaises(RepositoryValidationError):
            r.load_latest_horse_profile_history_supplied_response(canonical_horse_history_url=HURL.replace("%2F", "/"), observed_at_not_after=T)
        with self.assertRaises(RepositoryValidationError):
            r.load_latest_horse_profile_history_supplied_response(canonical_horse_history_url=HURL, observed_at_not_after=datetime(2026, 1, 1))
        r.save_capture(capture=item(canonical_source_url=HURL, response_body=b"<meta charset=\"Shift_JIS\">conflict", observed_at=T + timedelta(hours=2), stored_at=T + timedelta(hours=2)))
        with self.assertRaises(RepositoryDataIntegrityError):
            r.load_latest_horse_profile_history_supplied_response(canonical_horse_history_url=HURL, observed_at_not_after=T + timedelta(hours=2))
        c.execute("DELETE FROM jra_official_response_captures WHERE observed_at_utc=?", ((T + timedelta(hours=2)).isoformat(timespec="microseconds"),)); c.commit()
        r.save_capture(capture=later)
        c.execute("PRAGMA foreign_keys=OFF"); c.execute("DELETE FROM jra_official_response_bodies WHERE response_sha256=?", (later.response_sha256,)); c.commit()
        with self.assertRaises(RepositoryDataIntegrityError):
            r.load_latest_horse_profile_history_supplied_response(canonical_horse_history_url=HURL, observed_at_not_after=T + timedelta(hours=2))

    def test_latest_horse_history_lookup_excludes_other_urls_and_corrupt_metadata(self):
        c, r = self.repo()
        value = item(canonical_source_url=HURL)
        r.save_capture(capture=value)
        self.assertIsNone(r.load_latest_horse_profile_history_supplied_response(canonical_horse_history_url=HURL_OTHER_HORSE, observed_at_not_after=T))
        self.assertIsNone(r.load_latest_horse_profile_history_supplied_response(canonical_horse_history_url=HURL_OTHER_NAVIGATION, observed_at_not_after=T))
        c.execute("PRAGMA ignore_check_constraints=ON")
        c.execute("UPDATE jra_official_response_captures SET request_method='POST' WHERE capture_id=?", (value.capture_id,))
        c.execute("PRAGMA ignore_check_constraints=OFF")
        c.commit()
        with self.assertRaises(RepositoryDataIntegrityError):
            r.load_latest_horse_profile_history_supplied_response(canonical_horse_history_url=HURL, observed_at_not_after=T)

    def test_latest_race_result_lookup_is_exact_inclusive_and_integrity_checked(self):
        c, r = self.repo()
        early = item()
        late = item(response_body=b"<meta charset=\"Shift_JIS\">late", observed_at=T + timedelta(hours=2), stored_at=T + timedelta(hours=2))
        r.save_capture(capture=early)
        r.save_capture(capture=late)
        self.assertEqual(r.load_latest_race_result_supplied_response(canonical_race_result_url=URL, observed_at_not_after=T).response_body, BODY)
        self.assertEqual(r.load_latest_race_result_supplied_response(canonical_race_result_url=URL, observed_at_not_after=T + timedelta(hours=1)).response_body, BODY)
        self.assertIsNone(r.load_latest_race_result_supplied_response(canonical_race_result_url=URL, observed_at_not_after=T - timedelta(microseconds=1)))
        for invalid in (HURL, DURL, "https://www.jra.go.jp/JRADB/accessO.html", URL.replace("%2F", "/")):
            with self.subTest(invalid=invalid), self.assertRaises(RepositoryValidationError):
                r.load_latest_race_result_supplied_response(canonical_race_result_url=invalid, observed_at_not_after=T)
        with self.assertRaises(RepositoryValidationError):
            r.load_latest_race_result_supplied_response(canonical_race_result_url=URL, observed_at_not_after=datetime(2026, 1, 1))
        r.save_capture(capture=item(response_body=b"<meta charset=\"Shift_JIS\">tie", observed_at=T + timedelta(hours=2), stored_at=T + timedelta(hours=2)))
        with self.assertRaises(RepositoryDataIntegrityError):
            r.load_latest_race_result_supplied_response(canonical_race_result_url=URL, observed_at_not_after=T + timedelta(hours=2))
        c.execute("DELETE FROM jra_official_response_captures WHERE observed_at_utc=?", ((T + timedelta(hours=2)).isoformat(timespec="microseconds"),))
        c.commit()
        r.save_capture(capture=late)
        c.execute("PRAGMA foreign_keys=OFF")
        c.execute("DELETE FROM jra_official_response_bodies WHERE response_sha256=?", (late.response_sha256,))
        c.commit()
        with self.assertRaises(RepositoryDataIntegrityError):
            r.load_latest_race_result_supplied_response(canonical_race_result_url=URL, observed_at_not_after=T + timedelta(hours=2))

    def test_latest_race_result_metadata_corruption_is_not_hidden_by_lookup(self):
        corruptions = (
            ("schema_version", 2),
            ("page_kind", "horse_profile_history"),
            ("request_method", "POST"),
            ("request_identity_sha256", "0" * 64),
            ("request_cname", "pw151ou1006202601021220260105Z/2E"),
        )
        for column, value in corruptions:
            with self.subTest(column=column):
                c, r = self.repo()
                saved = item()
                r.save_capture(capture=saved)
                c.execute("PRAGMA ignore_check_constraints=ON")
                c.execute(f"UPDATE jra_official_response_captures SET {column}=? WHERE capture_id=?", (value, saved.capture_id))
                c.execute("PRAGMA ignore_check_constraints=OFF")
                c.commit()
                with self.assertRaises(RepositoryDataIntegrityError):
                    r.load_latest_race_result_supplied_response(canonical_race_result_url=URL, observed_at_not_after=T)

    def test_latest_final_odds_lookup_is_exact_inclusive_and_integrity_checked(self):
        c, r = self.repo()
        early = final_item()
        late = final_item(response_body=b"<meta charset=\"Shift_JIS\">late", observed_at=T + timedelta(hours=2), stored_at=T + timedelta(hours=2))
        other = final_item(request_locator=other_final_locator(), response_body=b"<meta charset=\"Shift_JIS\">other")
        r.save_final_win_odds_capture(capture=early)
        r.save_final_win_odds_capture(capture=late)
        r.save_final_win_odds_capture(capture=other)
        self.assertEqual(r.load_latest_final_win_odds_supplied_response(request_locator=early.request_locator, observed_at_not_after=T).response_body, BODY)
        self.assertEqual(r.load_latest_final_win_odds_supplied_response(request_locator=early.request_locator, observed_at_not_after=T + timedelta(hours=1)).response_body, BODY)
        self.assertIsNone(r.load_latest_final_win_odds_supplied_response(request_locator=early.request_locator, observed_at_not_after=T - timedelta(microseconds=1)))
        self.assertIsNone(r.load_latest_final_win_odds_supplied_response(request_locator=other_final_locator(), observed_at_not_after=T - timedelta(microseconds=1)))
        with self.assertRaises(RepositoryValidationError):
            r.load_latest_final_win_odds_supplied_response(request_locator=object(), observed_at_not_after=T)
        with self.assertRaises(RepositoryValidationError):
            r.load_latest_final_win_odds_supplied_response(request_locator=early.request_locator, observed_at_not_after=datetime(2026, 1, 1))
        r.save_final_win_odds_capture(capture=final_item(response_body=b"<meta charset=\"Shift_JIS\">tie", observed_at=T + timedelta(hours=2), stored_at=T + timedelta(hours=2)))
        with self.assertRaises(RepositoryDataIntegrityError):
            r.load_latest_final_win_odds_supplied_response(request_locator=early.request_locator, observed_at_not_after=T + timedelta(hours=2))
        c.execute("DELETE FROM jra_official_response_captures WHERE observed_at_utc=?", ((T + timedelta(hours=2)).isoformat(timespec="microseconds"),))
        c.commit()
        r.save_final_win_odds_capture(capture=late)
        c.execute("PRAGMA foreign_keys=OFF")
        c.execute("DELETE FROM jra_official_response_bodies WHERE response_sha256=?", (late.response_sha256,))
        c.commit()
        with self.assertRaises(RepositoryDataIntegrityError):
            r.load_latest_final_win_odds_supplied_response(request_locator=early.request_locator, observed_at_not_after=T + timedelta(hours=2))

    def test_latest_final_odds_metadata_corruption_is_not_hidden_by_lookup(self):
        corruptions = (
            ("schema_version", 1),
            ("page_kind", "race_result"),
            ("request_method", "GET"),
            ("request_cname", "pw151ou1006202601021220260105Z/2F"),
        )
        for column, value in corruptions:
            with self.subTest(column=column):
                c, r = self.repo()
                saved = final_item()
                r.save_final_win_odds_capture(capture=saved)
                c.execute("PRAGMA ignore_check_constraints=ON")
                c.execute(f"UPDATE jra_official_response_captures SET {column}=? WHERE capture_id=?", (value, saved.capture_id))
                c.execute("PRAGMA ignore_check_constraints=OFF")
                c.commit()
                with self.assertRaises(RepositoryDataIntegrityError):
                    r.load_latest_final_win_odds_supplied_response(request_locator=saved.request_locator, observed_at_not_after=T)
