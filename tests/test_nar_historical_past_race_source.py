from __future__ import annotations

import ast
from datetime import date, datetime, timezone
from decimal import Decimal
import hashlib
import inspect
from pathlib import Path
import unittest

from scripts.simulation.historical_input_evidence import HistoricalInputEvidenceReference
from scripts.simulation.historical_input_snapshot_builder import (
    HistoricalInputSnapshotAssemblyError,
    build_historical_input_snapshot,
)
from scripts.simulation.historical_input_source_records import (
    HistoricalInputSourceRecord,
    validate_historical_input_source_record_set,
)
from scripts.simulation.nar_historical_input_source import (
    NarHistoricalInputSourceUnsupportedError,
    NarHistoricalInputSourceValidationError,
    NarSuppliedOfficialResponse,
)
from scripts.simulation.nar_historical_past_race_source import (
    normalize_nar_historical_past_race_source_record,
)


FIXTURES = Path(__file__).parent / "fixtures" / "nar"
HORSE_BODY = (FIXTURES / "horse_mark_info_past_race_context.html").read_bytes()
RACE_BODY = (FIXTURES / "race_mark_table_past_race_result.html").read_bytes()
HORSE_URL = "https://www.keiba.go.jp/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=30074407776"
RACE_URL = (
    "https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceMarkTable?"
    "k_babaCode=31&k_raceDate=2026%2F05%2F03&k_raceNo=1"
)
OBSERVED = datetime(2026, 5, 5, 12, 0, tzinfo=timezone.utc)
TARGET_RACE = "nar:20260704:19:11"
TARGET_ENTRY = f"{TARGET_RACE}:entry:7"
LINEAGE = "nar:horse:30074407776"


def _evidence(role: str, marker: str, observed_at: datetime = OBSERVED) -> tuple[HistoricalInputEvidenceReference, ...]:
    return (
        HistoricalInputEvidenceReference(
            role,
            f"https://example.test/{marker}",
            hashlib.sha256(marker.encode("ascii")).hexdigest(),
            None,
            observed_at,
        ),
    )


def _entry(
    *,
    external_horse_id: str | None = LINEAGE,
    horse_no: int = 7,
    marker: str = "entry-one",
    organization: str = "NAR",
    source_system: str = "nar_official",
) -> HistoricalInputSourceRecord:
    return HistoricalInputSourceRecord(
        record_kind="entry",
        organization=organization,
        source_system=source_system,
        external_race_id=TARGET_RACE,
        external_entry_id=TARGET_ENTRY,
        provider_record_id=None,
        record_values={
            "external_entry_id": TARGET_ENTRY,
            "external_horse_id": external_horse_id,
            "horse_no": horse_no,
        },
        evidence=_evidence("entry", marker),
    )


def _responses(
    *,
    horse_url: str = HORSE_URL,
    race_url: str = RACE_URL,
    horse_body: bytes = HORSE_BODY,
    race_body: bytes = RACE_BODY,
    horse_observed: datetime = OBSERVED,
    race_observed: datetime = OBSERVED,
) -> tuple[NarSuppliedOfficialResponse, NarSuppliedOfficialResponse]:
    return (
        NarSuppliedOfficialResponse(horse_url, horse_body, "utf-8", horse_observed),
        NarSuppliedOfficialResponse(race_url, race_body, "utf-8", race_observed),
    )


def _normalize(**changes: object) -> HistoricalInputSourceRecord:
    entry = changes.pop("target_entry_record", _entry())
    horse, race = _responses(**changes)
    return normalize_nar_historical_past_race_source_record(
        target_entry_record=entry,
        horse_history_response=horse,
        race_result_response=race,
    )


class NarHistoricalPastRaceSourceTests(unittest.TestCase):
    def test_public_api_signature_and_dependency_boundary(self) -> None:
        import scripts.simulation.nar_historical_past_race_source as module

        self.assertEqual(
            {name for name in vars(module) if not name.startswith("_")},
            {"normalize_nar_historical_past_race_source_record"},
        )
        self.assertEqual(
            tuple(inspect.signature(normalize_nar_historical_past_race_source_record).parameters),
            ("target_entry_record", "horse_history_response", "race_result_response"),
        )
        source = Path(module.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        forbidden = {"requests", "httpx", "sqlite3", "socket", "pathlib", "random", "subprocess", "logging"}
        self.assertFalse(
            any(
                (isinstance(node, ast.Import) and any(alias.name.split(".")[0] in forbidden for alias in node.names))
                or (isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] in forbidden)
                for node in ast.walk(tree)
            ),
        )
        self.assertNotIn("nar_historical_input_source import _", source)
        self.assertNotIn("datetime.now", source)
        self.assertNotIn("open(", source)

    def test_authentic_pair_maps_every_field_and_two_raw_evidence_responses(self) -> None:
        record = _normalize()
        self.assertEqual(record.schema_version, 3)
        self.assertEqual(validate_historical_input_source_record_set(records=(record,)), (record,))
        self.assertTrue(record.source_id.startswith("his-v3:past_race:"))
        self.assertEqual(record.external_race_id, TARGET_RACE)
        self.assertEqual(record.external_entry_id, TARGET_ENTRY)
        self.assertEqual(record.provider_record_id, "nar:result:20260503:31:1:horse:30074407776")
        self.assertEqual(
            dict(record.record_values),
            {
                "race_date": date(2026, 5, 3), "place": "高知", "race_name": "Ｃ２－８", "race_class": "Ｃ２",
                "distance_m": 1400, "track": "ダート", "weather": "雨", "track_condition": "不良", "finish": 9,
                "reference_time_difference_seconds": Decimal("2.6"), "race_time": "1:32.4", "weight": Decimal("495"),
                "weight_diff": Decimal("1"), "jockey": "妹尾浩", "popularity": 8, "odds": Decimal("42.5"),
                "passing_order": "9-9-9-11", "fourth_corner_position": 11,
            },
        )
        self.assertEqual(tuple(item.evidence_role for item in record.evidence), ("historical_race_context", "historical_race_result"))
        self.assertEqual(record.evidence[0].canonical_source_url, HORSE_URL)
        self.assertEqual(record.evidence[1].canonical_source_url, RACE_URL)
        self.assertEqual(record.evidence[0].response_sha256, hashlib.sha256(HORSE_BODY).hexdigest())
        self.assertEqual(record.evidence[1].response_sha256, hashlib.sha256(RACE_BODY).hexdigest())
        self.assertNotEqual(
            (record.evidence[0].canonical_source_url, record.evidence[0].response_sha256),
            (record.evidence[1].canonical_source_url, record.evidence[1].response_sha256),
        )

    def test_target_entry_binding_is_exact_and_horse_number_is_not_historical_identity(self) -> None:
        with self.assertRaises(NarHistoricalInputSourceValidationError):
            _normalize(target_entry_record=object())
        track = HistoricalInputSourceRecord(
            record_kind="track", organization="NAR", source_system="nar_official", external_race_id=TARGET_RACE,
            external_entry_id=None, provider_record_id=None,
            record_values={"target_race_date": date(2026, 7, 4), "scheduled_start_at": datetime(2026, 7, 4, 10, tzinfo=timezone.utc), "place": "船橋", "distance_m": 1200, "track": "ダート", "track_condition": "良", "race_name": None, "race_class": None, "weather": None},
            evidence=_evidence("track", "track"),
        )
        with self.assertRaises(NarHistoricalInputSourceValidationError):
            _normalize(target_entry_record=track)
        with self.assertRaises(NarHistoricalInputSourceValidationError):
            _normalize(target_entry_record=_entry(external_horse_id=None))
        with self.assertRaises(NarHistoricalInputSourceValidationError):
            _normalize(target_entry_record=_entry(external_horse_id="nar:horse:030074407776"))
        with self.assertRaises(NarHistoricalInputSourceValidationError):
            _normalize(target_entry_record=_entry(organization="JRA"))
        with self.assertRaises(NarHistoricalInputSourceValidationError):
            _normalize(target_entry_record=_entry(source_system="other"))
        self.assertEqual(_normalize(target_entry_record=_entry(horse_no=99)).external_entry_id, TARGET_ENTRY)
        with self.assertRaises(NarHistoricalInputSourceValidationError):
            _normalize(horse_url=HORSE_URL.replace("30074407776", "30074407777"))
        with self.assertRaises(NarHistoricalInputSourceValidationError):
            _normalize(race_body=RACE_BODY.replace(b"30074407776", b"30074407777", 1))

    def test_urls_are_strict_and_horsemark_host_alias_is_preserved(self) -> None:
        record = _normalize(horse_url=HORSE_URL.replace("www.", "www2."))
        self.assertEqual(record.evidence[0].canonical_source_url, HORSE_URL.replace("www.", "www2."))
        invalid_horse_urls = (
            HORSE_URL.replace("https://", "http://"), HORSE_URL.replace("www.keiba.go.jp", "other.example"),
            HORSE_URL + "&extra=1", HORSE_URL.replace("=300", "=0300"), HORSE_URL + "#x",
        )
        for url in invalid_horse_urls:
            with self.subTest(url=url), self.assertRaises(NarHistoricalInputSourceValidationError):
                _normalize(horse_url=url)
        for url in (RACE_URL.replace("www.keiba.go.jp", "www2.keiba.go.jp"), RACE_URL.replace("https://", "http://"), RACE_URL + "&x=1"):
            with self.subTest(url=url), self.assertRaises(NarHistoricalInputSourceValidationError):
                _normalize(race_url=url)
        with self.assertRaises(NarHistoricalInputSourceValidationError):
            normalize_nar_historical_past_race_source_record(
                target_entry_record=_entry(), horse_history_response=object(), race_result_response=_responses()[1]
            )

    def test_direct_difference_and_racemark_margin_are_separate(self) -> None:
        normal = _normalize()
        changed_margin = _normalize(race_body=RACE_BODY.replace(b"1.1/2", b"\xe3\x82\xaf\xe3\x83\x93", 1))
        self.assertEqual(normal.record_values["reference_time_difference_seconds"], Decimal("2.6"))
        self.assertEqual(changed_margin.record_values["reference_time_difference_seconds"], Decimal("2.6"))
        zero = _normalize(horse_body=HORSE_BODY.replace(b">2.6</td>", b">0</td>", 1))
        self.assertEqual(zero.record_values["reference_time_difference_seconds"], Decimal("0"))

    def test_weight_jockey_and_result_state_contracts(self) -> None:
        for display, weight, change in ((b"495<span>(1)", Decimal("495"), Decimal("1")), (b"495<span>(-2)", Decimal("495"), Decimal("-2")), (b"495<span>(+3)", Decimal("495"), Decimal("3")), (b"495<span>(0)", Decimal("495"), Decimal("0"))):
            body = RACE_BODY.replace(b"495<span>(1)", display, 1)
            result = _normalize(race_body=body)
            self.assertEqual((result.record_values["weight"], result.record_values["weight_diff"]), (weight, change))
        allowance = _normalize(race_body=RACE_BODY.replace("妹尾浩".encode(), "☆城野慈".encode(), 1), horse_body=HORSE_BODY.replace("妹尾浩".encode(), "☆城野慈".encode(), 1))
        self.assertEqual(allowance.record_values["jockey"], "☆城野慈")
        for old, new in ((b"495<span>(1)", b"495"), (b"1:32.4", b""), (b">42.5</td>", b">0</td>"), (b'<td class="a">9</td>', "<td class=\"a\">取消</td>".encode())):
            with self.subTest(old=old), self.assertRaises(NarHistoricalInputSourceUnsupportedError):
                _normalize(race_body=RACE_BODY.replace(old, new, 1))
        with self.assertRaises(NarHistoricalInputSourceUnsupportedError):
            _normalize(horse_body=HORSE_BODY.replace("Ｃ２</td>".encode(), b"</td>", 1))
        with self.assertRaises(NarHistoricalInputSourceUnsupportedError):
            _normalize(horse_body=HORSE_BODY.replace(b">2.6</td>", b"></td>", 1))

    def test_corner_labels_are_positional_and_fail_closed(self) -> None:
        four = _normalize(race_body=RACE_BODY.replace(b"9-9-9-11", b"8-8-6-5", 1))
        self.assertEqual((four.record_values["passing_order"], four.record_values["fourth_corner_position"]), ("8-8-6-5", 5))
        short = RACE_BODY.replace("１コーナー".encode(), b"2X", 1).replace("２コーナー".encode(), "２角".encode(), 1).replace("３コーナー".encode(), "３角".encode(), 1).replace("４コーナー".encode(), "４角".encode(), 1).replace(b"9-9-9-11", b"4-4-5", 1)
        short = short.replace(b"<tr><td>2X</td><td>( 6 , 8 )</td></tr>", b"", 1)
        three = _normalize(race_body=short)
        self.assertEqual((three.record_values["passing_order"], three.record_values["fourth_corner_position"]), ("4-4-5", 5))
        for body in (
            RACE_BODY.replace("４コーナー".encode(), "３コーナー".encode(), 1),
            RACE_BODY.replace("４コーナー".encode(), "５角".encode(), 1),
            RACE_BODY.replace(b"9-9-9-11", b"9-9-9", 1),
            RACE_BODY.replace(b"9-9-9-11", b"9-9-x-11", 1),
        ):
            with self.subTest(), self.assertRaises(NarHistoricalInputSourceUnsupportedError):
                _normalize(race_body=body)

    def test_multiplicity_and_name_fallback_fail_closed(self) -> None:
        duplicate_table = HORSE_BODY.replace(b"</table>", b"</table>" + HORSE_BODY.split(b"<table", 1)[1].split(b"</table>", 1)[0].join((b"<table", b"</table>")), 1)
        with self.assertRaises(NarHistoricalInputSourceValidationError):
            _normalize(horse_body=duplicate_table)
        duplicate_row = RACE_BODY.replace(b"</tbody></table>", RACE_BODY.split(b'<tr class="tBorder">', 1)[1].split(b"</tr>", 1)[0].join((b'<tr class="tBorder">', b"</tr>")) + b"</tbody></table>", 1)
        with self.assertRaises(NarHistoricalInputSourceValidationError):
            _normalize(race_body=duplicate_row)
        changed_name = _normalize(race_body=RACE_BODY.replace("エコロマーベリック".encode(), "別名馬".encode(), 1))
        self.assertEqual(changed_name.provider_record_id, "nar:result:20260503:31:1:horse:30074407776")

    def test_recognized_jra_and_banei_states_are_unsupported(self) -> None:
        jra_history = HORSE_BODY.replace(
            b"/KeibaWeb/TodayRaceInfo/RaceMarkTable", b"/JRA/Result", 1
        ).replace(b"<body>", b"<body>JRA", 1)
        with self.assertRaises(NarHistoricalInputSourceUnsupportedError):
            _normalize(horse_body=jra_history)
        with self.assertRaises(NarHistoricalInputSourceUnsupportedError):
            _normalize(race_body=RACE_BODY.replace("ダート".encode(), "ばんえい".encode(), 1))

    def test_raw_bytes_and_observation_timestamps_have_the_frozen_source_id_behavior(self) -> None:
        baseline = _normalize()
        changed = _normalize(race_body=RACE_BODY.replace(b"\n", b"\n\n", 1))
        self.assertEqual(dict(baseline.record_values), dict(changed.record_values))
        self.assertNotEqual(baseline.source_id, changed.source_id)
        timestamp_changed = _normalize(race_observed=datetime(2026, 5, 6, 12, tzinfo=timezone.utc))
        self.assertEqual(baseline.source_id, timestamp_changed.source_id)
        self.assertNotEqual(baseline.evidence[1].observed_at, timestamp_changed.evidence[1].observed_at)
        independent = _normalize(target_entry_record=_entry(marker="entry-two"))
        self.assertEqual(baseline.source_id, independent.source_id)

    def test_c1c_compatibility_and_causality_remain_builder_owned(self) -> None:
        entry = _entry()
        past = _normalize(target_entry_record=entry)
        track = HistoricalInputSourceRecord(
            record_kind="track", organization="NAR", source_system="nar_official", external_race_id=TARGET_RACE,
            external_entry_id=None, provider_record_id=None,
            record_values={"target_race_date": date(2026, 7, 4), "scheduled_start_at": datetime(2026, 7, 4, 12, tzinfo=timezone.utc), "place": "船橋", "distance_m": 1200, "track": "ダート", "track_condition": "良", "race_name": "target", "race_class": None, "weather": "晴"},
            evidence=_evidence("track", "target-track"),
        )
        jockey = HistoricalInputSourceRecord(record_kind="jockey", organization="NAR", source_system="nar_official", external_race_id=TARGET_RACE, external_entry_id=TARGET_ENTRY, provider_record_id=None, record_values={"external_entry_id": TARGET_ENTRY, "jockey": "騎手"}, evidence=_evidence("jockey", "target-jockey"))
        odds = HistoricalInputSourceRecord(record_kind="odds_win", organization="NAR", source_system="nar_official", external_race_id=TARGET_RACE, external_entry_id=TARGET_ENTRY, provider_record_id=None, record_values={"external_entry_id": TARGET_ENTRY, "horse_no": 7, "win_odds": Decimal("3.5")}, evidence=_evidence("odds_win", "target-odds"))
        snapshot = build_historical_input_snapshot(dataset_id="dataset", internal_race_id=1, captured_at=datetime(2026, 6, 1, tzinfo=timezone.utc), information_cutoff=datetime(2026, 6, 2, tzinfo=timezone.utc), source_records=(track, entry, jockey, odds, past), race_entry_id_by_external_entry_id={TARGET_ENTRY: 99})
        self.assertEqual(snapshot.entries[0].external_entry_identity.external_horse_id, LINEAGE)
        self.assertEqual((snapshot.past_races[0].race_entry_id, snapshot.past_races[0].reference_time_difference_seconds), (99, Decimal("2.6")))
        late_horse, race = _responses(horse_observed=datetime(2026, 6, 3, tzinfo=timezone.utc))
        late = normalize_nar_historical_past_race_source_record(target_entry_record=entry, horse_history_response=late_horse, race_result_response=race)
        with self.assertRaises(HistoricalInputSnapshotAssemblyError):
            build_historical_input_snapshot(dataset_id="dataset", internal_race_id=1, captured_at=datetime(2026, 6, 1, tzinfo=timezone.utc), information_cutoff=datetime(2026, 6, 2, tzinfo=timezone.utc), source_records=(track, entry, jockey, odds, late), race_entry_id_by_external_entry_id={TARGET_ENTRY: 99})


if __name__ == "__main__":
    unittest.main()
