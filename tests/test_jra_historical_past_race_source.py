from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import ast
import hashlib
import inspect
import json
from pathlib import Path
import unittest

import scripts.simulation.jra_historical_past_race_source as module
from scripts.simulation.historical_input_evidence import HistoricalInputEvidenceReference
from scripts.simulation.historical_input_source_records import HistoricalInputSourceRecord
from scripts.simulation.jra_historical_past_race_source import (
    JRAHistoricalPastRaceSourceError,
    JRAHistoricalPastRaceSourceUnsupportedError,
    JRAHistoricalPastRaceSourceValidationError,
    normalize_jra_historical_past_race_source_record,
)
from scripts.simulation.jra_official_identity import (
    JRAExternalRaceIdentity,
    JRAOfficialFinalWinOddsRequestLocator,
    build_jra_external_entry_id,
)
from scripts.simulation.jra_official_response_capture import (
    JRAFinalWinOddsSuppliedOfficialResponse,
    JRASuppliedOfficialResponse,
)


_S_URL = "https://www.jra.go.jp/JRADB/accessS.html?CNAME=pw01sde0106202601021220260105%2FEC"
_O_URL = "https://www.jra.go.jp/JRADB/accessO.html"
_CNAME = "pw151ou1006202601021220260105Z/2E"
_HORSE_KEY = "2020201029"
_HORSE_ID = f"jra:horse:{_HORSE_KEY}"
_TARGET_RACE = "jra:race:2026:06:02:03:04"
_TARGET_ENTRY = f"{_TARGET_RACE}:entry:9"
_TIME = datetime(2026, 1, 3, tzinfo=timezone.utc)


def _fingerprint(cname: str) -> str:
    return hashlib.sha256(
        json.dumps(
            {"endpoint_url": _O_URL, "form": {"cname": cname}, "method": "POST", "schema_version": 1},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
    ).hexdigest()


def _locator(cname: str = _CNAME) -> JRAOfficialFinalWinOddsRequestLocator:
    return JRAOfficialFinalWinOddsRequestLocator(
        endpoint_url=_O_URL,
        cname=cname,
        external_race_identity=JRAExternalRaceIdentity("2026", "06", "01", "02", "12"),
        request_identity_sha256=_fingerprint(cname),
    )


def _evidence(role: str, suffix: str) -> HistoricalInputEvidenceReference:
    return HistoricalInputEvidenceReference(role, f"https://evidence.example/{suffix}", "a" * 64, None, _TIME)


def _track(**changes: object) -> HistoricalInputSourceRecord:
    values: dict[str, object] = {
        "target_race_date": date(2026, 2, 1),
        "scheduled_start_at": _TIME,
        "place": "中山",
        "distance_m": 1200,
        "track": "ダート",
        "track_condition": "良",
        "race_name": "target",
        "race_class": "1勝クラス",
        "weather": "晴",
    }
    values.update(changes)
    return HistoricalInputSourceRecord(
        record_kind="track", organization="JRA", source_system="jra_official", external_race_id=_TARGET_RACE,
        external_entry_id=None, provider_record_id=None, record_values=values, evidence=(_evidence("track", "track"),)
    )


def _entry(**changes: object) -> HistoricalInputSourceRecord:
    external_race_id = changes.pop("_external_race_id", _TARGET_RACE)
    external_entry_id = changes.pop("_external_entry_id", _TARGET_ENTRY)
    organization = changes.pop("_organization", "JRA")
    source_system = changes.pop("_source_system", "jra_official")
    values: dict[str, object] = {"external_entry_id": _TARGET_ENTRY, "external_horse_id": _HORSE_ID, "horse_no": 9}
    values.update(changes)
    return HistoricalInputSourceRecord(
        record_kind="entry", organization=organization, source_system=source_system,
        external_race_id=external_race_id, external_entry_id=external_entry_id, provider_record_id=None,
        record_values=values, evidence=(_evidence("entry", "entry"),)
    )


def _header(*, access_s: bool, race_name: str = "4歳以上1勝クラス", venue: str = "中山", meeting: str = "1", meeting_day: str = "2", race: str = "12", day: str = "5") -> str:
    number = f'<img alt="{race}R">' if access_s else f"{race}R"
    return f'''<div class="race_header">
<div class="cell date">2026年1月{day}日(月) {meeting}回{venue}{meeting_day}日</div>
<div class="race_number">{number}</div><div class="race_name">{race_name}</div>
<div class="type"><div class="cell class">1勝クラス</div><div class="cell course">コース：1,200 メートル（ダート・右）</div></div>
<div class="baba">ダート<ul><li><span class="txt">不良</span></li></ul></div>
<li class="weather"><span class="txt">雨</span></li></div>'''


def _result_html(**changes: str) -> str:
    heading = _header(access_s=True, **{key[7:]: value for key, value in changes.items() if key.startswith("header_")})
    body_weight = changes.get("body_weight", "495(+1)")
    finish = changes.get("finish", "2")
    race_time = changes.get("race_time", "1:12.3")
    popularity = changes.get("popularity", "3")
    horse_number = changes.get("horse_number", "7")
    href = changes.get("href", f"/JRADB/accessU.html?CNAME=pw01dud00{_HORSE_KEY}%2F22")
    horse_name = changes.get("horse_name", "対象馬")
    corners = changes.get("corners", "<li title=\"1コーナー通過順位\">8</li><li title=\"2コーナー通過順位\">8</li><li title=\"3コーナー通過順位\">6</li><li title=\"4コーナー通過順位\">5</li>")
    extra_row = changes.get("extra_row", "")
    return f'''<html><body><div id="race_result">{heading}
<table><thead><tr><th>着順</th><th>枠</th><th>馬番</th><th>馬名</th><th>性齢</th><th>負担重量</th><th>騎手名</th><th>タイム</th><th>着差</th><th>コーナー通過順位</th><th>馬体重（増減）</th><th>調教師名</th><th>単勝人気</th></tr></thead>
<tbody><tr><td class="place">{finish}</td><td class="num">{horse_number}</td><td class="horse"><a href="{href}">{horse_name}</a></td><td class="weight">56</td><td class="jockey">☆騎手 太郎</td><td class="time">{race_time}</td><td class="h_weight">{body_weight}</td><td class="pop">{popularity}</td><td class="corner">{corners}</td></tr>{extra_row}</tbody></table></div></body></html>'''


def _odds_html(**changes: str) -> str:
    heading = _header(access_s=False, **{key[7:]: value for key, value in changes.items() if key.startswith("header_")})
    horse_number = changes.get("horse_number", "7")
    odds = changes.get("odds", "12.5")
    extra_table = changes.get("extra_table", "")
    extra_row = changes.get("extra_row", "")
    return f'''<html><body>{heading}<table class="tanpuku"><thead><tr><th>馬番</th><th>馬名</th><th>単勝</th></tr></thead>
<tbody><tr><td class="num">{horse_number}</td><td class="horse">別の名前</td><td class="odds_tan">{odds}</td></tr>{extra_row}</tbody></table>{extra_table}</body></html>'''


def _result_response(html: str | None = None, *, observed_at: datetime = _TIME, url: str = _S_URL) -> JRASuppliedOfficialResponse:
    return JRASuppliedOfficialResponse(response_url=url, response_body=(html or _result_html()).encode("cp932"), observed_at=observed_at)


def _odds_response(html: str | None = None, *, observed_at: datetime = _TIME, locator: JRAOfficialFinalWinOddsRequestLocator | None = None) -> JRAFinalWinOddsSuppliedOfficialResponse:
    return JRAFinalWinOddsSuppliedOfficialResponse(request_locator=locator or _locator(), response_body=(html or _odds_html()).encode("cp932"), observed_at=observed_at)


def _normalize(**changes: object) -> HistoricalInputSourceRecord:
    return normalize_jra_historical_past_race_source_record(
        target_track_record=changes.get("track", _track()),
        target_entry_record=changes.get("entry", _entry()),
        race_result_response=changes.get("result", _result_response()),
        final_win_odds_response=changes.get("odds", _odds_response()),
    )


class JRAHistoricalPastRaceSourceTests(unittest.TestCase):
    def test_public_surface_signature_and_purity(self):
        self.assertEqual({name for name in vars(module) if not name.startswith("_")}, {
            "JRAHistoricalPastRaceSourceError", "JRAHistoricalPastRaceSourceValidationError",
            "JRAHistoricalPastRaceSourceUnsupportedError", "normalize_jra_historical_past_race_source_record",
        })
        self.assertEqual(tuple(inspect.signature(normalize_jra_historical_past_race_source_record).parameters), (
            "target_track_record", "target_entry_record", "race_result_response", "final_win_odds_response",
        ))
        source = Path(module.__file__).read_text(encoding="utf-8")
        for forbidden in ("requests", "sqlite3", "pathlib", "open(", "datetime.now", "subprocess", "random"):
            self.assertNotIn(forbidden, source)
        tree = ast.parse(source)
        self.assertFalse(any(isinstance(node, ast.ImportFrom) and node.module == "scripts.simulation.nar_historical_past_race_source" for node in ast.walk(tree)))

    def test_happy_path_all_values_identity_evidence_and_target_horse_number_independence(self):
        record = _normalize()
        self.assertIs(type(record), HistoricalInputSourceRecord)
        self.assertEqual(record.schema_version, 4)
        self.assertEqual((record.external_race_id, record.external_entry_id), (_TARGET_RACE, _TARGET_ENTRY))
        self.assertEqual(record.provider_record_id, "jra:result:2026:06:01:02:12:horse:2020201029")
        self.assertEqual(record.record_values, {
            "race_date": date(2026, 1, 5), "place": "中山", "race_name": "4歳以上1勝クラス",
            "race_class": "1勝クラス", "distance_m": 1200, "track": "ダート", "weather": "雨",
            "track_condition": "不良", "finish": 2, "race_time": "1:12.3", "weight": Decimal("495"),
            "weight_diff": Decimal("1"), "jockey": "☆騎手 太郎", "popularity": 3, "odds": Decimal("12.5"),
            "passing_order": "8-8-6-5", "fourth_corner_position": 5,
        })
        self.assertEqual(tuple(item.evidence_role for item in record.evidence), (
            "historical_race_context", "historical_race_final_odds", "historical_race_result",
        ))
        context, final_odds, result = record.evidence
        self.assertEqual((context.canonical_source_url, context.response_sha256, context.available_at, context.observed_at), (result.canonical_source_url, result.response_sha256, None, _TIME))
        self.assertIsNone(context.request_identity_sha256)
        self.assertEqual(final_odds.canonical_source_url, _O_URL)
        self.assertEqual(final_odds.request_identity_sha256, _locator().request_identity_sha256)
        self.assertEqual(context.response_sha256, hashlib.sha256(_result_response().response_body).hexdigest())
        self.assertEqual(final_odds.response_sha256, hashlib.sha256(_odds_response().response_body).hexdigest())

    def test_target_boundary_rejects_incoherent_or_incompatible_records(self):
        with self.assertRaises(JRAHistoricalPastRaceSourceValidationError):
            _normalize(track=object())
        for entry in (
            _entry(_organization="NAR"),
            _entry(_source_system="other"),
            _entry(_external_race_id="jra:race:2026:06:02:03:05"),
            _entry(external_horse_id=None),
            _entry(external_horse_id="jra:horse:not-ten-digits"),
            _entry(_external_entry_id=f"{_TARGET_RACE}:entry:8", external_entry_id=f"{_TARGET_RACE}:entry:8"),
            _entry(horse_no=8),
        ):
            with self.subTest(entry=entry), self.assertRaises(JRAHistoricalPastRaceSourceValidationError):
                _normalize(entry=entry)
        with self.assertRaises(JRAHistoricalPastRaceSourceValidationError):
            _normalize(track=_track(target_race_date=date(2026, 1, 5)))

        wrong_kind = HistoricalInputSourceRecord(
            record_kind="jockey", organization="JRA", source_system="jra_official", external_race_id=_TARGET_RACE,
            external_entry_id=_TARGET_ENTRY, provider_record_id=None,
            record_values={"external_entry_id": _TARGET_ENTRY, "jockey": "騎手"}, evidence=(_evidence("jockey", "wrong-kind"),)
        )
        with self.assertRaises(JRAHistoricalPastRaceSourceValidationError):
            _normalize(entry=wrong_kind)

    def test_access_s_identity_and_horse_link_fail_closed(self):
        with self.assertRaises(JRAHistoricalPastRaceSourceValidationError):
            _normalize(result=object())
        access_u = JRASuppliedOfficialResponse(
            response_url="https://www.jra.go.jp/JRADB/accessU.html?CNAME=pw01dud002020201029%2F22",
            response_body=_result_html().encode("cp932"), observed_at=_TIME,
        )
        with self.assertRaises(JRAHistoricalPastRaceSourceValidationError):
            _normalize(result=access_u)
        invalid_date = _result_response()
        object.__setattr__(invalid_date, "response_url", _S_URL.replace("20260105", "20260230"))
        with self.assertRaises(JRAHistoricalPastRaceSourceValidationError):
            _normalize(result=invalid_date)
        for html in (
            _result_html(header_venue="東京"),
            _result_html(header_meeting="2"),
            _result_html(header_meeting_day="3"),
            _result_html(header_race="11"),
            _result_html(header_day="6"),
            _result_html(href="/JRADB/accessU.html?CNAME=bad"),
            _result_html(href="/JRADB/accessU.html?CNAME=pw01dud002020201028%2F22", horse_name="対象馬"),
        ):
            with self.subTest(html=html[:80]), self.assertRaises(JRAHistoricalPastRaceSourceValidationError):
                _normalize(result=_result_response(html))
        duplicate = _result_html(extra_row='<tr><td class="place">3</td><td class="num">8</td><td class="horse"><a href="/JRADB/accessU.html?CNAME=pw01dud002020201029%2F22">重複</a></td><td class="weight">56</td><td class="jockey">騎手</td><td class="time">1:12.4</td><td class="h_weight">496(0)</td><td class="pop">4</td><td class="corner"><li title="1コーナー通過順位">8</li><li title="2コーナー通過順位">8</li><li title="3コーナー通過順位">7</li><li title="4コーナー通過順位">6</li></td></tr>')
        with self.assertRaises(JRAHistoricalPastRaceSourceValidationError):
            _normalize(result=_result_response(duplicate))
        with self.assertRaises(JRAHistoricalPastRaceSourceValidationError):
            _normalize(result=_result_response(_result_html().replace("<table>", '<div class="race_header"></div><table>')))

    def test_access_s_direct_fields_and_corners_fail_closed(self):
        unsupported = (
            _result_html(body_weight="計不"), _result_html(race_time=""), _result_html(finish="0"),
            _result_html(popularity=""), _result_html(header_race_name=""),
            _result_html(corners='<li title="1コーナー通過順位">8</li><li title="3コーナー通過順位">6</li>'),
            _result_html(corners='<li title="1コーナー通過順位">8</li><li title="4コーナー通過順位">6</li><li title="4コーナー通過順位">5</li>'),
            _result_html(corners='<li title="2コーナー通過順位">8</li><li title="1コーナー通過順位">6</li><li title="4コーナー通過順位">5</li>'),
            _result_html(corners='<li title="1コーナー通過順位">0</li><li title="4コーナー通過順位">5</li>'),
        )
        for html in unsupported:
            with self.subTest(html=html[:80]), self.assertRaises(JRAHistoricalPastRaceSourceUnsupportedError):
                _normalize(result=_result_response(html))
        no_body_weight = _result_html().replace('<td class="h_weight">495(+1)</td>', '<td class="weight">56</td>')
        with self.assertRaises(JRAHistoricalPastRaceSourceValidationError):
            _normalize(result=_result_response(no_body_weight))

    def test_access_o_identity_tables_join_and_odds_fail_closed(self):
        with self.assertRaises(JRAHistoricalPastRaceSourceValidationError):
            _normalize(odds=object())
        for html in (
            _odds_html(header_venue="東京"),
            _odds_html(horse_number="8"),
            _odds_html(odds="0"),
            _odds_html(odds="-"),
            _odds_html(extra_table='<table class="tanpuku"><tbody></tbody></table>'),
            _odds_html(extra_row='<tr><td class="num">7</td><td class="horse">重複</td><td class="odds_tan">4.0</td></tr>'),
        ):
            with self.subTest(html=html[:80]), self.assertRaises((JRAHistoricalPastRaceSourceValidationError, JRAHistoricalPastRaceSourceUnsupportedError)):
                _normalize(odds=_odds_response(html))
        changed_cname = "pw151ou1006202601021120260105Z/2F"
        changed_locator = JRAOfficialFinalWinOddsRequestLocator(
            endpoint_url=_O_URL,
            cname=changed_cname,
            external_race_identity=JRAExternalRaceIdentity("2026", "06", "01", "02", "11"),
            request_identity_sha256=_fingerprint(changed_cname),
        )
        with self.assertRaises(JRAHistoricalPastRaceSourceValidationError):
            _normalize(odds=_odds_response(locator=changed_locator))
        with self.assertRaises(JRAHistoricalPastRaceSourceValidationError):
            _normalize(odds=_odds_response(_odds_html().replace('<table class="tanpuku">', '<div class="race_header"></div><table class="tanpuku">')))

    def test_evidence_identity_raw_bytes_request_fingerprint_and_timestamps(self):
        baseline = _normalize()
        changed_body = _normalize(result=_result_response(_result_html() + " "))
        self.assertNotEqual(baseline.source_id, changed_body.source_id)
        changed_request = _normalize(odds=_odds_response(locator=_locator("pw151ou1006202601021220260105Z/2F")))
        self.assertNotEqual(baseline.source_id, changed_request.source_id)
        shifted = _normalize(
            result=_result_response(observed_at=_TIME + timedelta(minutes=1)),
            odds=_odds_response(observed_at=_TIME + timedelta(minutes=2)),
        )
        self.assertEqual(baseline.source_id, shifted.source_id)
        self.assertEqual(tuple(item.observed_at for item in shifted.evidence), (
            _TIME + timedelta(minutes=1), _TIME + timedelta(minutes=2), _TIME + timedelta(minutes=1),
        ))
        self.assertTrue(all(item.available_at is None for item in shifted.evidence))

    def test_errors_are_specific_normalizer_errors(self):
        self.assertTrue(issubclass(JRAHistoricalPastRaceSourceValidationError, JRAHistoricalPastRaceSourceError))
        self.assertTrue(issubclass(JRAHistoricalPastRaceSourceUnsupportedError, JRAHistoricalPastRaceSourceError))
        with self.assertRaises(JRAHistoricalPastRaceSourceValidationError):
            _normalize(result=_result_response(_result_html().replace('<div id="race_result">', '<div>')))


if __name__ == "__main__":
    unittest.main()
