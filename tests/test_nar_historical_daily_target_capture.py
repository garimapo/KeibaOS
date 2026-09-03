import dataclasses
import hashlib
import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.simulation.nar_historical_daily_target_capture import (
    NARHistoricalDailyTargetCaptureUnsupportedError,
    NARHistoricalDailyTargetCaptureValidationError,
    NARHistoricalDailyTargetPageKind,
    NARHistoricalDailyTargetRequestIdentity,
    NARHistoricalDailyTargetResponseCapture,
)


FIXTURES = Path(__file__).parent / "fixtures" / "nar_daily_targets"
ORIGIN = "https://www.keiba.go.jp"


class NARHistoricalDailyTargetCaptureTest(unittest.TestCase):
    def monthly(self, raw=None, resolved=None):
        raw = raw or b"/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop?k_year=2025&k_month=1"
        return NARHistoricalDailyTargetRequestIdentity(
            NARHistoricalDailyTargetPageKind.MONTHLY_CONVENE_INFO,
            raw,
            resolved or ORIGIN + raw.decode("ascii"),
            "supplier:exact",
        )

    def race(self, raw=None, resolved=None):
        raw = raw or b"/KeibaWeb/TodayRaceInfo/RaceList?k_raceDate=2025%2F01%2F01&amp;k_babaCode=21"
        return NARHistoricalDailyTargetRequestIdentity(
            NARHistoricalDailyTargetPageKind.RACE_LIST,
            raw,
            resolved or ORIGIN + raw.decode("ascii").replace("&amp;", "&"),
            "envelope:capture",
        )

    def test_frozen_fixture_bytes_and_provenance_match_exactly(self):
        provenance = json.loads((FIXTURES / "provenance.json").read_text(encoding="utf-8"))
        self.assertEqual(1, provenance["schema_version"])
        self.assertEqual("parser_source_contract_test_evidence_only", provenance["fixture_boundary"])
        self.assertEqual(15, len(provenance["records"]))
        for record in provenance["records"]:
            body = (FIXTURES / record["path"]).read_bytes()
            self.assertEqual(record["byte_length"], len(body), record["path"])
            self.assertEqual(record["sha256"], hashlib.sha256(body).hexdigest(), record["path"])
            self.assertEqual(body, body.decode("utf-8", errors="strict").encode("utf-8"))
            self.assertEqual(record["requested_url"], record["effective_url"])
            self.assertLessEqual(datetime.fromisoformat(record["requested_at"]), datetime.fromisoformat(record["observed_at"]))
            self.assertIsNone(provenance["provider_available_at"])

    def test_raw_race_href_is_authority_and_literal_amp_is_preserved(self):
        identity = self.race()
        self.assertEqual(
            b"/KeibaWeb/TodayRaceInfo/RaceList?k_raceDate=2025%2F01%2F01&amp;k_babaCode=21",
            identity.official_supplied_request_material,
        )
        self.assertEqual("2025-01-01", identity.target_date.isoformat())
        self.assertEqual("21", identity.baba_code)
        self.assertEqual("b04de0a7859ca4ec52812a7c049f6e9b7b8d203c5b94b717fa97151874713f8b", identity.request_identity_sha256)
        self.assertEqual(identity, self.race())
        with self.assertRaises(dataclasses.FrozenInstanceError):
            identity.baba_code = "22"

    def test_no_reconstructed_or_nonexact_request_variants_are_accepted(self):
        invalid = (
            b"/KeibaWeb/TodayRaceInfo/RaceList?k_babaCode=21&amp;k_raceDate=2025%2F01%2F01",
            b"/KeibaWeb/TodayRaceInfo/RaceList?k_raceDate=2025/01/01&amp;k_babaCode=21",
            b"/KeibaWeb/TodayRaceInfo/RaceList?k_raceDate=2025%2f01%2f01&amp;k_babaCode=21",
            b"/KeibaWeb/TodayRaceInfo/RaceList?k_raceDate=2025%2F01%2F01&k_babaCode=21",
            b"/KeibaWeb/TodayRaceInfo/RaceList?k_raceDate=2025%2F01%2F01&amp;k_babaCode=021",
            b"/KeibaWeb/TodayRaceInfo/RaceList?k_raceDate=2025%2F01%2F01&amp;k_babaCode=21&amp;x=1",
        )
        for raw in invalid:
            with self.subTest(raw=raw), self.assertRaises(NARHistoricalDailyTargetCaptureUnsupportedError):
                self.race(raw=raw, resolved=ORIGIN + raw.decode("ascii").replace("&amp;", "&"))
        monthly_invalid = (
            b"/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop?k_month=1&k_year=2025",
            b"/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop?k_year=2025&k_month=01",
            b"/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop?k_year=2025&k_month=1&x=1",
        )
        for raw in monthly_invalid:
            with self.subTest(raw=raw), self.assertRaises(NARHistoricalDailyTargetCaptureUnsupportedError):
                self.monthly(raw=raw, resolved=ORIGIN + raw.decode("ascii"))

    def test_effective_url_alias_redirect_and_origin_mismatch_fail(self):
        for resolved in (
            ORIGIN + "/KeibaWeb/TodayRaceInfo/RaceList?k_raceDate=2025%2F01%2F01&k_babaCode=22",
            "http://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceList?k_raceDate=2025%2F01%2F01&k_babaCode=21",
            "https://keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceList?k_raceDate=2025%2F01%2F01&k_babaCode=21",
        ):
            with self.subTest(resolved=resolved), self.assertRaises(NARHistoricalDailyTargetCaptureValidationError):
                self.race(resolved=resolved)

    def test_response_capture_freezes_bytes_times_and_digest(self):
        request = self.monthly()
        self.assertEqual("554281aaf3cc9508ea61d09a53c7679df45bdfd10979f3de63b1633405c3619d", request.request_identity_sha256)
        start = datetime(2030, 1, 1, tzinfo=timezone.utc)
        body = b"<html></html>"
        capture = NARHistoricalDailyTargetResponseCapture(
            request, body, "utf-8", start, start + timedelta(seconds=1),
            start + timedelta(seconds=2), 200, "text/html; charset=UTF-8", None,
            "date", None, None, len(body)
        )
        self.assertEqual(hashlib.sha256(body).hexdigest(), capture.response_sha256)
        self.assertEqual("nar-daily-target-capture-v1:ef5102cf40bd6c4271cefb4ca81c5d29a3ec352102eef9379678433ef9914e3c", capture.capture_id)
        with self.assertRaises(NARHistoricalDailyTargetCaptureValidationError):
            NARHistoricalDailyTargetResponseCapture(
                request, body, "utf-8", start + timedelta(seconds=2), start, start, 200
            )
        with self.assertRaises(NARHistoricalDailyTargetCaptureUnsupportedError):
            NARHistoricalDailyTargetResponseCapture(request, b"\xff", "utf-8", start, start, start, 200)
        with self.assertRaises(NARHistoricalDailyTargetCaptureUnsupportedError):
            NARHistoricalDailyTargetResponseCapture(request, body, "utf-8", start, start, start, 200, content_encoding="gzip")

    def test_exact_id_archive_has_no_latest_or_fallback_surface(self):
        class Archive:
            def __init__(self):
                self.values = {}
            def save_capture(self, *, capture):
                if capture.capture_id in self.values:
                    raise RuntimeError("immutable duplicate")
                self.values[capture.capture_id] = capture
            def load_capture(self, *, capture_id):
                return self.values.get(capture_id)
        archive = Archive()
        self.assertFalse(hasattr(archive, "load_latest"))
        self.assertIsNone(archive.load_capture(capture_id="missing"))


if __name__ == "__main__":
    unittest.main()
