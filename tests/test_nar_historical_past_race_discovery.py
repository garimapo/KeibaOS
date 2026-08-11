from __future__ import annotations

import ast
from dataclasses import is_dataclass
from datetime import date, datetime, timedelta, timezone
import inspect
from pathlib import Path
import unittest

from scripts.simulation.historical_input_evidence import HistoricalInputEvidenceReference
from scripts.simulation.historical_input_source_records import HistoricalInputSourceRecord
from scripts.simulation.nar_historical_input_source import NarSuppliedOfficialResponse
from scripts.simulation.nar_historical_past_race_discovery import (
    NARHistoricalEventKind,
    NARHistoricalPastRaceDiscovery,
    NARHistoricalPastRaceDiscoveryUnsupportedError,
    NARHistoricalPastRaceDiscoveryValidationError,
    NARHistoricalPastRaceReference,
    discover_nar_historical_past_race_history,
)
from scripts.simulation.nar_official_response_capture import canonicalize_nar_official_capture_url


FIXTURES = Path(__file__).parent / "fixtures" / "nar"
HISTORY_BODY = (FIXTURES / "horse_mark_info_history_discovery.html").read_bytes()
ZERO_BODY = (FIXTURES / "horse_mark_info_zero_history.html").read_bytes()
TARGET_RACE = "nar:20260704:19:11"
ENTRY_ID = f"{TARGET_RACE}:entry:7"
LINEAGE = "30074407776"
HORSE_URL = f"https://www.keiba.go.jp/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode={LINEAGE}"
OBSERVED = datetime(2026, 6, 1, 12, tzinfo=timezone.utc)
SCHEDULED = datetime(2026, 7, 4, 12, tzinfo=timezone.utc)


def _evidence(role: str, marker: str) -> tuple[HistoricalInputEvidenceReference, ...]:
    return (HistoricalInputEvidenceReference(role, f"https://example.test/{marker}", f"{marker * 64:.64}", None, OBSERVED),)


def _track(*, scheduled: datetime = SCHEDULED, race_id: str = TARGET_RACE) -> HistoricalInputSourceRecord:
    return HistoricalInputSourceRecord(
        "track", "NAR", "nar_official", race_id, None, None,
        {"target_race_date": date(2026, 7, 4), "scheduled_start_at": scheduled, "place": "船橋", "distance_m": 1200, "track": "ダート", "track_condition": "良", "race_name": None, "race_class": None, "weather": None},
        _evidence("track", "a"),
    )


def _entry(*, lineage: str = LINEAGE, horse_no: int = 7, race_id: str = TARGET_RACE, entry_id: str = ENTRY_ID) -> HistoricalInputSourceRecord:
    return HistoricalInputSourceRecord(
        "entry", "NAR", "nar_official", race_id, entry_id, None,
        {"external_entry_id": entry_id, "external_horse_id": f"nar:horse:{lineage}", "horse_no": horse_no},
        _evidence("entry", "b"),
    )


def _response(*, body: bytes = HISTORY_BODY, url: str = HORSE_URL, observed: datetime = OBSERVED) -> NarSuppliedOfficialResponse:
    return NarSuppliedOfficialResponse(url, body, "utf-8", observed)


def _discover(**changes: object) -> NARHistoricalPastRaceDiscovery:
    track = changes.pop("target_track_record", None)
    entry = changes.pop("target_entry_record", None)
    response = changes.pop("horse_history_response", None)
    return discover_nar_historical_past_race_history(
        target_track_record=_track() if track is None else track,
        target_entry_record=_entry() if entry is None else entry,
        horse_history_response=_response(**changes) if response is None else response,
    )


class NARHistoricalPastRaceDiscoveryTests(unittest.TestCase):
    def test_public_api_and_pure_boundary(self) -> None:
        import scripts.simulation.nar_historical_past_race_discovery as module

        self.assertEqual(
            {name for name in vars(module) if not name.startswith("_")},
            {
                "NARHistoricalEventKind", "NARHistoricalPastRaceReference", "NARHistoricalPastRaceDiscovery",
                "NARHistoricalPastRaceDiscoveryError", "NARHistoricalPastRaceDiscoveryValidationError",
                "NARHistoricalPastRaceDiscoveryUnsupportedError", "discover_nar_historical_past_race_history",
            },
        )
        self.assertEqual(tuple(inspect.signature(discover_nar_historical_past_race_history).parameters), ("target_track_record", "target_entry_record", "horse_history_response"))
        self.assertTrue(is_dataclass(NARHistoricalPastRaceReference) and NARHistoricalPastRaceReference.__dataclass_params__.frozen)
        self.assertTrue(is_dataclass(NARHistoricalPastRaceDiscovery) and NARHistoricalPastRaceDiscovery.__dataclass_params__.frozen)
        self.assertEqual(tuple(NARHistoricalEventKind), (NARHistoricalEventKind.NAR_ACTUAL_START, NARHistoricalEventKind.JRA_ACTUAL_START, NARHistoricalEventKind.PROVEN_NON_START, NARHistoricalEventKind.UNSUPPORTED_ACTUAL_START))
        tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
        forbidden = {"requests", "httpx", "sqlite3", "pathlib", "random", "subprocess", "time"}
        self.assertFalse(any((isinstance(node, ast.Import) and any(item.name.split(".")[0] in forbidden for item in node.names)) or (isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] in forbidden) for node in ast.walk(tree)))
        source = Path(module.__file__).read_text(encoding="utf-8")
        self.assertNotIn("open(", source)
        self.assertNotIn("datetime.now", source)

    def test_complete_official_order_has_no_filter_or_truncation(self) -> None:
        discovery = _discover()
        self.assertFalse(discovery.proven_zero_history)
        self.assertEqual(discovery.target_external_race_id, TARGET_RACE)
        self.assertEqual(discovery.target_external_entry_id, ENTRY_ID)
        self.assertEqual(discovery.target_external_horse_id, f"nar:horse:{LINEAGE}")
        self.assertEqual(discovery.target_race_date, date(2026, 7, 4))
        self.assertEqual(tuple(event.event_kind for event in discovery.events), (NARHistoricalEventKind.NAR_ACTUAL_START, NARHistoricalEventKind.NAR_ACTUAL_START, NARHistoricalEventKind.PROVEN_NON_START, NARHistoricalEventKind.JRA_ACTUAL_START))
        self.assertEqual(tuple(event.race_date for event in discovery.events), (date(2026, 5, 3), date(2026, 4, 19), date(2025, 11, 27), date(2025, 9, 13)))
        self.assertEqual(discovery.events[0].provider_event_id, "nar:event:20260503:31:1")
        self.assertEqual(discovery.events[2].provider_event_id, "nar:event:20251127:18:3")
        self.assertEqual(discovery.events[3].provider_event_id, "jra:event:20250913:Ｊ中山:4")
        self.assertIsNone(discovery.events[3].canonical_race_result_url)
        self.assertEqual(canonicalize_nar_official_capture_url(discovery.events[0].canonical_race_result_url), canonicalize_nar_official_capture_url("https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceMarkTable?k_babaCode=31&k_raceDate=2026%2F05%2F03&k_raceNo=1"))
        self.assertIsNotNone(discovery.events[2].canonical_race_result_url)
        stopped = _discover(body=HISTORY_BODY.replace("取消".encode(), "取止".encode(), 1))
        self.assertEqual(stopped.events[2].event_kind, NARHistoricalEventKind.PROVEN_NON_START)
        abnormal = _discover(body=HISTORY_BODY.replace(b"<td>9</td><td>1:32.4</td>", "<td>中止</td><td>1:32.4</td>".encode(), 1))
        self.assertEqual(abnormal.events[0].event_kind, NARHistoricalEventKind.UNSUPPORTED_ACTUAL_START)

    def test_zero_history_is_distinct_complete_state(self) -> None:
        zero_lineage = "30055402717"
        zero_entry_id = f"{TARGET_RACE}:entry:8"
        discovery = _discover(
            target_entry_record=_entry(lineage=zero_lineage, horse_no=8, entry_id=zero_entry_id),
            horse_history_response=_response(body=ZERO_BODY, url=f"https://www.keiba.go.jp/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode={zero_lineage}"),
        )
        self.assertEqual(discovery.events, ())
        self.assertTrue(discovery.proven_zero_history)

    def test_target_response_and_causality_validation(self) -> None:
        with self.assertRaises(NARHistoricalPastRaceDiscoveryValidationError):
            _discover(target_track_record=object())
        with self.assertRaises(NARHistoricalPastRaceDiscoveryValidationError):
            _discover(target_entry_record=object())
        with self.assertRaises(NARHistoricalPastRaceDiscoveryValidationError):
            _discover(horse_history_response=object())
        with self.assertRaises(NARHistoricalPastRaceDiscoveryValidationError):
            _discover(target_entry_record=_entry(lineage="30074407777"))
        with self.assertRaises(NARHistoricalPastRaceDiscoveryValidationError):
            _discover(horse_history_response=_response(observed=SCHEDULED + timedelta(seconds=1)))
        with self.assertRaises(NARHistoricalPastRaceDiscoveryValidationError):
            _discover(horse_history_response=_response(url=HORSE_URL.replace("https://", "http://")))
        alias = _discover(horse_history_response=_response(url=HORSE_URL.replace("www.", "www2.")))
        self.assertEqual(alias.target_external_horse_id, f"nar:horse:{LINEAGE}")

    def test_complete_structure_rejects_ambiguity_and_post_target_rows(self) -> None:
        with self.assertRaises(NARHistoricalPastRaceDiscoveryValidationError):
            _discover(body=HISTORY_BODY.replace(b"</body>", b'<a class="historyNext" href="?page=2">next</a></body>'))
        with self.assertRaises(NARHistoricalPastRaceDiscoveryValidationError):
            _discover(body=HISTORY_BODY.replace(b"</body>", HISTORY_BODY[HISTORY_BODY.index(b"<table"):HISTORY_BODY.index(b"</table>") + 8] + b"</body>"))
        with self.assertRaises(NARHistoricalPastRaceDiscoveryValidationError):
            _discover(body=HISTORY_BODY.replace(b"2026/04/19", b"2026/06/01", 1))
        with self.assertRaises(NARHistoricalPastRaceDiscoveryValidationError):
            _discover(body=HISTORY_BODY.replace(b"2025/09/13", b"2026/07/04", 1))
        with self.assertRaises(NARHistoricalPastRaceDiscoveryValidationError):
            _discover(body=HISTORY_BODY.replace(b"<td>502</td>", b"", 1))
        with self.assertRaises(NARHistoricalPastRaceDiscoveryValidationError):
            _discover(body=HISTORY_BODY.replace(b"<td>2026/04/19</td>", b"<td>2026/05/03</td>", 1).replace(b"k_raceDate=2026%2F04%2F19", b"k_raceDate=2026%2F05%2F03", 1).replace(b"k_raceNo=2", b"k_raceNo=1", 1))

    def test_history_table_schema_is_exact_and_body_has_exactly_23_cells(self) -> None:
        mutations = (
            HISTORY_BODY.replace("<th>年月日</th>".encode(), "<th>年月日</th><th>未知列</th>".encode(), 1),
            HISTORY_BODY.replace("<th>人気</th>".encode(), "<th>人気</th><th>人気</th>".encode(), 1),
            HISTORY_BODY.replace("<th>人気</th><th>着順</th>".encode(), "<th>着順</th><th>人気</th>".encode(), 1),
            HISTORY_BODY.replace("<th>上3F</th>".encode(), b"", 1),
            HISTORY_BODY.replace(b'colspan="3"', b'colspan="2"', 1),
            HISTORY_BODY.replace(b'colspan="3"', b'colspan="three"', 1),
            HISTORY_BODY.replace(b' colspan="3"', b"", 1),
            HISTORY_BODY.replace("<th>人気</th>".encode(), "<th colspan=\"2\">人気</th>".encode(), 1),
            HISTORY_BODY.replace(b"<td>40.1</td>", b"", 1),
            HISTORY_BODY.replace("<td>妹尾浩 (高知)</td>".encode(), "<td>extra</td><td>妹尾浩 (高知)</td>".encode(), 1),
        )
        for body in mutations:
            with self.subTest(body=body[:80]), self.assertRaises(NARHistoricalPastRaceDiscoveryValidationError):
                _discover(body=body)

    def test_zero_conflict_unknown_and_unapproved_states_fail_closed(self) -> None:
        with self.assertRaises(NARHistoricalPastRaceDiscoveryValidationError):
            _discover(body=ZERO_BODY.replace(b"</body>", b'<table class="HorseMarkInfo_table"></table></body>'))
        with self.assertRaises(NARHistoricalPastRaceDiscoveryValidationError):
            _discover(body=ZERO_BODY.replace("指定の馬の出走履歴がありません。".encode(), "履歴なし".encode()))
        with self.assertRaises(NARHistoricalPastRaceDiscoveryValidationError):
            _discover(body=HISTORY_BODY.replace("取消".encode(), "除外".encode(), 1))
        with self.assertRaises(NARHistoricalPastRaceDiscoveryUnsupportedError):
            _discover(body=HISTORY_BODY.replace("Ｊ中山".encode(), "Ｊ".encode(), 1))
