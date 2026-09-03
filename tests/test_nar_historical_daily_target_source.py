import hashlib
import inspect
import json
import re
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from scripts.simulation.historical_daily_targets import (
    DailyHistoricalTargetIntegrityError,
    DailyTargetDiscoveryFailureCode,
    TargetDiscoveryIncompleteError,
)
from scripts.simulation.nar_historical_daily_target_capture import (
    NARHistoricalDailyTargetPageKind,
    NARHistoricalDailyTargetRequestIdentity,
    NARHistoricalDailyTargetResponseCapture,
)
from scripts.simulation import nar_historical_daily_target_source as subject


FIXTURES = Path(__file__).parent / "fixtures" / "nar_daily_targets"
ORIGIN = "https://www.keiba.go.jp"
TEST_CLOCK = datetime(2030, 1, 1, tzinfo=timezone.utc)

CASES = {
    date(2025, 1, 1): (
        "monthly_convene_info_2025_01.utf8.html",
        (
            "race_list_2025_01_01_kawasaki_baba21.utf8.html",
            "race_list_2025_01_01_nagoya_baba24.utf8.html",
            "race_list_2025_01_01_kochi_baba31.utf8.html",
        ),
    ),
    date(2025, 12, 26): (
        "monthly_convene_info_2025_12.utf8.html",
        (
            "race_list_2025_12_26_oi_baba20.utf8.html",
            "race_list_2025_12_26_kanazawa_baba22.utf8.html",
            "race_list_2025_12_26_kasamatsu_baba23.utf8.html",
        ),
    ),
    date(2025, 8, 30): (
        "monthly_convene_info_2025_08.utf8.html",
        (
            "race_list_2025_08_30_obihiro_baba3.utf8.html",
            "race_list_2025_08_30_funabashi_baba19.utf8.html",
            "race_list_2025_08_30_saga_baba32.utf8.html",
        ),
    ),
}


def monthly_request(year, month):
    raw = f"/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop?k_year={year}&k_month={month}".encode("ascii")
    return NARHistoricalDailyTargetRequestIdentity(
        NARHistoricalDailyTargetPageKind.MONTHLY_CONVENE_INFO,
        raw,
        ORIGIN + raw.decode("ascii"),
        "test-only-supplied-locator",
    )


def capture(request, body, sequence=0):
    requested = TEST_CLOCK + timedelta(seconds=sequence)
    return NARHistoricalDailyTargetResponseCapture(
        request,
        body,
        "utf-8",
        requested,
        requested + timedelta(microseconds=1),
        requested + timedelta(microseconds=2),
        200,
        "text/html; charset=UTF-8",
    )


def case_captures(target_date):
    monthly_path, race_paths = CASES[target_date]
    envelope_capture = capture(
        monthly_request(target_date.year, target_date.month),
        (FIXTURES / monthly_path).read_bytes(),
    )
    envelope = subject.normalize_nar_monthly_convene_info(
        target_date=target_date, capture=envelope_capture
    )
    race_captures = tuple(
        capture(locator.request_identity, (FIXTURES / path).read_bytes(), index + 1)
        for index, (locator, path) in enumerate(zip(envelope.venue_locators, race_paths))
    )
    return envelope_capture, envelope, race_captures


class NARHistoricalDailyTargetSourceTest(unittest.TestCase):
    def assertIncomplete(self, expected_code, callback):
        with self.assertRaises(TargetDiscoveryIncompleteError) as caught:
            callback()
        self.assertEqual(expected_code, caught.exception.code)
        return caught.exception

    def test_provenance_and_every_fixture_sha_are_verified_before_parsing(self):
        provenance = json.loads((FIXTURES / "provenance.json").read_text(encoding="utf-8"))
        self.assertEqual("parser_source_contract_test_evidence_only", provenance["fixture_boundary"])
        self.assertNotEqual("2025", provenance["records"][0]["observed_at"][:4])
        for record in provenance["records"]:
            body = (FIXTURES / record["path"]).read_bytes()
            self.assertEqual(record["sha256"], hashlib.sha256(body).hexdigest())
            body.decode("utf-8", errors="strict")

    def test_ordinary_day_yields_exact_venues_targets_times_and_deterministic_set(self):
        target_date = date(2025, 1, 1)
        envelope_capture, envelope, race_captures = case_captures(target_date)
        self.assertEqual(
            [("川崎", "21"), ("名古屋", "24"), ("高知", "31")],
            [(item.venue_identity.display_name, item.venue_identity.baba_code) for item in envelope.venue_locators],
        )
        raw = envelope.venue_locators[0].raw_href
        self.assertIn(b"&amp;k_babaCode=21", raw)
        self.assertEqual(raw, envelope.venue_locators[0].request_identity.official_supplied_request_material)
        bundle = subject.build_nar_historical_daily_target_evidence_bundle(
            target_date=target_date,
            envelope_capture=envelope_capture,
            race_list_captures=race_captures,
        )
        target_set = subject.build_nar_historical_daily_replay_target_set(
            target_date=target_date,
            envelope_capture=envelope_capture,
            race_list_captures=tuple(reversed(race_captures)),
        )
        self.assertEqual(33, len(bundle.target_races))
        self.assertEqual(bundle.target_races, target_set.target_races)
        self.assertEqual(
            sorted(item.external_race_id for item in target_set.target_races),
            [item.external_race_id for item in target_set.target_races],
        )
        self.assertEqual("nar:20250101:21:1", target_set.target_races[0].external_race_id)
        self.assertEqual(
            datetime(2025, 1, 1, 2, 20, tzinfo=timezone.utc),
            target_set.target_races[0].scheduled_start_at,
        )
        self.assertTrue(all(item.scheduled_start_at is not None for item in target_set.target_races))
        self.assertTrue(all(item.scheduled_start_at.tzinfo == timezone.utc for item in target_set.target_races))
        self.assertTrue(all(item.observed_at.year == 2030 for item in target_set.completeness_evidence))
        again = subject.build_nar_historical_daily_replay_target_set(
            target_date=target_date,
            envelope_capture=envelope_capture,
            race_list_captures=race_captures,
        )
        self.assertEqual(target_set.content_sha256, again.content_sha256)

    def test_kanazawa_whole_meeting_cancellation_retains_all_rows_and_exact_native_evidence(self):
        target_date = date(2025, 12, 26)
        envelope_capture, _, race_captures = case_captures(target_date)
        target_set = subject.build_nar_historical_daily_replay_target_set(
            target_date=target_date,
            envelope_capture=envelope_capture,
            race_list_captures=race_captures,
        )
        self.assertEqual(33, len(target_set.target_races))
        kanazawa = [item for item in target_set.target_races if ":22:" in item.external_race_id]
        self.assertEqual(12, len(kanazawa))
        self.assertEqual(
            {"nar-race-list-whole-meeting-cancelled-no-substitute-v1"},
            {item.provider_disposition_evidence.evidence_kind_and_version for item in kanazawa},
        )
        self.assertEqual(
            {"07b9b53a5a75e6b0630c03a15bf10461a3b33be9a71294acb1d7930edcee26ea"},
            {item.provider_disposition_evidence.native_value_sha256 for item in kanazawa},
        )
        ordinary = [item for item in target_set.target_races if ":22:" not in item.external_race_id]
        self.assertEqual({"nar-race-list-target-row-v1"}, {item.provider_disposition_evidence.evidence_kind_and_version for item in ordinary})

    def test_blank_triangle_and_partial_cancellation_fail_closed(self):
        blank_date = date(2020, 3, 9)
        blank_capture = capture(monthly_request(2020, 3), (FIXTURES / "monthly_convene_info_2020_03.utf8.html").read_bytes())
        self.assertIncomplete(
            DailyTargetDiscoveryFailureCode.UNSUPPORTED_ENVELOPE_STATE,
            lambda: subject.normalize_nar_monthly_convene_info(target_date=blank_date, capture=blank_capture),
        )
        triangle_date = date(2017, 12, 19)
        triangle_capture = capture(monthly_request(2017, 12), (FIXTURES / "monthly_convene_info_2017_12.utf8.html").read_bytes())
        self.assertIncomplete(
            DailyTargetDiscoveryFailureCode.UNSUPPORTED_ENVELOPE_STATE,
            lambda: subject.normalize_nar_monthly_convene_info(target_date=triangle_date, capture=triangle_capture),
        )
        envelope_capture, _, race_captures = case_captures(date(2025, 8, 30))
        self.assertIncomplete(
            DailyTargetDiscoveryFailureCode.UNSUPPORTED_NATIVE_DISPOSITION,
            lambda: subject.build_nar_historical_daily_target_evidence_bundle(
                target_date=date(2025, 8, 30),
                envelope_capture=envelope_capture,
                race_list_captures=race_captures,
            ),
        )

    def test_missing_extra_and_duplicate_fragments_fail_the_whole_day(self):
        target_date = date(2025, 1, 1)
        envelope_capture, _, captures = case_captures(target_date)
        self.assertIncomplete(
            DailyTargetDiscoveryFailureCode.MISSING_PARTITION_EVIDENCE,
            lambda: subject.build_nar_historical_daily_target_evidence_bundle(
                target_date=target_date, envelope_capture=envelope_capture, race_list_captures=captures[:-1]
            ),
        )
        extra_request = NARHistoricalDailyTargetRequestIdentity(
            NARHistoricalDailyTargetPageKind.RACE_LIST,
            b"/KeibaWeb/TodayRaceInfo/RaceList?k_raceDate=2025%2F01%2F01&amp;k_babaCode=22",
            ORIGIN + "/KeibaWeb/TodayRaceInfo/RaceList?k_raceDate=2025%2F01%2F01&k_babaCode=22",
            envelope_capture.capture_id,
        )
        extra = capture(extra_request, captures[0].response_body, 9)
        self.assertIncomplete(
            DailyTargetDiscoveryFailureCode.COVERAGE_SET_MISMATCH,
            lambda: subject.build_nar_historical_daily_target_evidence_bundle(
                target_date=target_date, envelope_capture=envelope_capture, race_list_captures=captures + (extra,)
            ),
        )
        self.assertIncomplete(
            DailyTargetDiscoveryFailureCode.DUPLICATE_EVIDENCE,
            lambda: subject.build_nar_historical_daily_target_evidence_bundle(
                target_date=target_date, envelope_capture=envelope_capture, race_list_captures=captures + (captures[0],)
            ),
        )

    def test_malformed_row_time_identity_table_and_unknown_warning_never_skip(self):
        target_date = date(2025, 1, 1)
        envelope_capture, envelope, captures = case_captures(target_date)
        original = captures[0]
        mutations = []
        mutations.append((re.sub(br">\s*11:20\s*</td>", b">--:--</td>", original.response_body, count=1), DailyTargetDiscoveryFailureCode.MALFORMED_OFFICIAL_EVIDENCE))
        mutations.append((original.response_body.replace(b"k_raceNo=1&amp;k_babaCode=21", b"k_raceNo=2&amp;k_babaCode=21", 1), DailyTargetDiscoveryFailureCode.MALFORMED_OFFICIAL_EVIDENCE))
        mutations.append((original.response_body.replace(b'<section class="raceTable">', b'<section class="notRaceTable">', 1), DailyTargetDiscoveryFailureCode.MALFORMED_OFFICIAL_EVIDENCE))
        row = re.search(br'<tr class="data">.*?</tr>', original.response_body, re.DOTALL).group(0)
        mutations.append((original.response_body.replace(row, row + row, 1), DailyTargetDiscoveryFailureCode.DUPLICATE_EVIDENCE))
        for body, expected_code in mutations:
            changed = capture(original.request_identity, body, 10)
            candidate = (changed,) + captures[1:]
            self.assertIncomplete(
                expected_code,
                lambda candidate=candidate: subject.build_nar_historical_daily_target_evidence_bundle(
                    target_date=target_date, envelope_capture=envelope_capture, race_list_captures=candidate
                ),
            )
        dec_date = date(2025, 12, 26)
        dec_envelope_capture, _, dec_captures = case_captures(dec_date)
        unknown = dec_captures[1].response_body.replace("降雪".encode(), "強風".encode(), 1)
        changed = capture(dec_captures[1].request_identity, unknown, 10)
        self.assertIncomplete(
            DailyTargetDiscoveryFailureCode.UNSUPPORTED_NATIVE_DISPOSITION,
            lambda: subject.build_nar_historical_daily_target_evidence_bundle(
                target_date=dec_date,
                envelope_capture=dec_envelope_capture,
                race_list_captures=(dec_captures[0], changed, dec_captures[2]),
            ),
        )

    def test_wrong_request_and_navigation_set_mismatch_fail(self):
        target_date = date(2025, 1, 1)
        envelope_capture, envelope, captures = case_captures(target_date)
        wrong_body = captures[0].response_body.replace(
            b"k_babaCode=24 class=\"courseBtn\"",
            b"k_babaCode=22 class=\"courseBtn\"",
            1,
        )
        changed = capture(captures[0].request_identity, wrong_body, 20)
        self.assertIncomplete(
            DailyTargetDiscoveryFailureCode.COVERAGE_SET_MISMATCH,
            lambda: subject.build_nar_historical_daily_target_evidence_bundle(
                target_date=target_date,
                envelope_capture=envelope_capture,
                race_list_captures=(changed,) + captures[1:],
            ),
        )
        self.assertIncomplete(
            DailyTargetDiscoveryFailureCode.INVALID_OFFICIAL_REQUEST_IDENTITY,
            lambda: subject.normalize_nar_race_list(
                target_date=target_date,
                expected_venue=envelope.venue_locators[0].venue_identity,
                expected_request=envelope.venue_locators[1].request_identity,
                capture=captures[0],
            ),
        )

    def test_unknown_mark_duplicate_locator_malformed_envelope_and_wrong_heading_fail(self):
        target_date = date(2025, 1, 1)
        envelope_capture, envelope, captures = case_captures(target_date)
        unknown_mark = envelope_capture.response_body
        locator_offset = unknown_mark.index(b"k_raceDate=2025%2F01%2F01&amp;k_babaCode=21")
        mark_offset = unknown_mark.index("●".encode(), locator_offset)
        unknown_mark = unknown_mark[:mark_offset] + "×".encode() + unknown_mark[mark_offset + len("●".encode()):]
        monthly_bodies = (
            unknown_mark,
            envelope_capture.response_body.replace(
                b"k_raceDate=2025%2F01%2F01&amp;k_babaCode=24\"",
                b"k_raceDate=2025%2F01%2F01&amp;k_babaCode=21\"",
                1,
            ),
            envelope_capture.response_body.replace(b'<table class="schedule">', b'<table class="other">', 1),
        )
        expected = (
            DailyTargetDiscoveryFailureCode.UNSUPPORTED_ENVELOPE_STATE,
            DailyTargetDiscoveryFailureCode.DUPLICATE_EVIDENCE,
            DailyTargetDiscoveryFailureCode.MALFORMED_OFFICIAL_EVIDENCE,
        )
        for body, code in zip(monthly_bodies, expected):
            changed = capture(envelope_capture.request_identity, body, 30)
            self.assertIncomplete(
                code,
                lambda changed=changed: subject.normalize_nar_monthly_convene_info(
                    target_date=target_date, capture=changed
                ),
            )
        wrong_heading = captures[0].response_body.replace("川崎競馬　当日メニュー".encode(), "船橋競馬　当日メニュー".encode(), 1)
        changed_race = capture(captures[0].request_identity, wrong_heading, 31)
        self.assertIncomplete(
            DailyTargetDiscoveryFailureCode.MALFORMED_OFFICIAL_EVIDENCE,
            lambda: subject.normalize_nar_race_list(
                target_date=target_date,
                expected_venue=envelope.venue_locators[0].venue_identity,
                expected_request=envelope.venue_locators[0].request_identity,
                capture=changed_race,
            ),
        )

    def test_target_table_scoping_excludes_change_info_and_all_builders_are_no_network(self):
        target_date = date(2025, 1, 1)
        envelope_capture, _, captures = case_captures(target_date)
        bundle = subject.build_nar_historical_daily_target_evidence_bundle(
            target_date=target_date, envelope_capture=envelope_capture, race_list_captures=captures
        )
        self.assertEqual(33, len(bundle.target_races))
        source = inspect.getsource(subject).lower()
        for forbidden in (
            "import requests", "urllib", "http.client", "socket", "nar_provider",
            "nar_parser", "sqlite", "jra", "snapshot", "manifest", "settlement",
            "target_race_count",
        ):
            self.assertNotIn(forbidden, source)
        for function in (
            subject.build_nar_historical_daily_target_evidence_bundle,
            subject.build_nar_historical_daily_replay_target_set,
        ):
            self.assertEqual(
                ["target_date", "envelope_capture", "race_list_captures"],
                list(inspect.signature(function).parameters),
            )

    def test_corrupt_loaded_capture_digest_is_global_integrity_failure(self):
        target_date = date(2025, 1, 1)
        envelope_capture, _, captures = case_captures(target_date)
        object.__setattr__(captures[0], "response_sha256", "0" * 64)
        with self.assertRaises(DailyHistoricalTargetIntegrityError):
            subject.build_nar_historical_daily_target_evidence_bundle(
                target_date=target_date,
                envelope_capture=envelope_capture,
                race_list_captures=captures,
            )


if __name__ == "__main__":
    unittest.main()
