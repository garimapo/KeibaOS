from __future__ import annotations

import ast
from datetime import date, datetime, timedelta, timezone
import hashlib
import inspect
from pathlib import Path
import unittest

from scripts.simulation.historical_input_evidence import HistoricalInputEvidenceReference
from scripts.simulation.historical_input_source_records import HistoricalInputSourceRecord, validate_historical_input_source_record_set
from scripts.simulation.nar_historical_input_source import NarSuppliedOfficialResponse
from scripts.simulation.nar_historical_past_race_absence_source import (
    NARHistoricalPastRaceAbsenceSourceValidationError,
    normalize_nar_historical_past_race_absence_source_record,
)


FIXTURES = Path(__file__).parent / "fixtures" / "nar"
ZERO_BODY = (FIXTURES / "horse_mark_info_zero_history.html").read_bytes()
HISTORY_BODY = (FIXTURES / "horse_mark_info_history_discovery.html").read_bytes()
RACE_ID = "nar:20260704:19:11"
ENTRY_ID = f"{RACE_ID}:entry:8"
LINEAGE = "30055402717"
URL = f"https://www.keiba.go.jp/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode={LINEAGE}"
OBSERVED = datetime(2026, 6, 1, 12, tzinfo=timezone.utc)
SCHEDULED = datetime(2026, 7, 4, 12, tzinfo=timezone.utc)


def _evidence(role: str, digest: str) -> tuple[HistoricalInputEvidenceReference, ...]:
    return (HistoricalInputEvidenceReference(role, f"https://example.test/{role}", digest * 64, None, OBSERVED),)


def _track(*, scheduled: datetime = SCHEDULED) -> HistoricalInputSourceRecord:
    return HistoricalInputSourceRecord(
        "track", "NAR", "nar_official", RACE_ID, None, None,
        {"target_race_date": date(2026, 7, 4), "scheduled_start_at": scheduled, "place": "船橋", "distance_m": 1200, "track": "ダート", "track_condition": "良", "race_name": None, "race_class": None, "weather": None},
        _evidence("track", "a"),
    )


def _entry(*, lineage: str = LINEAGE) -> HistoricalInputSourceRecord:
    return HistoricalInputSourceRecord(
        "entry", "NAR", "nar_official", RACE_ID, ENTRY_ID, None,
        {"external_entry_id": ENTRY_ID, "external_horse_id": f"nar:horse:{lineage}", "horse_no": 8},
        _evidence("entry", "b"),
    )


def _response(*, body: bytes = ZERO_BODY, url: str = URL, observed: datetime = OBSERVED) -> NarSuppliedOfficialResponse:
    return NarSuppliedOfficialResponse(url, body, "utf-8", observed)


def _normalize(**changes: object) -> HistoricalInputSourceRecord:
    track = changes.pop("target_track_record", None)
    entry = changes.pop("target_entry_record", None)
    response = changes.pop("horse_history_response", None)
    return normalize_nar_historical_past_race_absence_source_record(
        target_track_record=_track() if track is None else track,
        target_entry_record=_entry() if entry is None else entry,
        horse_history_response=_response(**changes) if response is None else response,
    )


class NARHistoricalPastRaceAbsenceSourceTests(unittest.TestCase):
    def test_public_api_and_pure_boundary(self) -> None:
        import scripts.simulation.nar_historical_past_race_absence_source as module

        self.assertEqual(
            {name for name in vars(module) if not name.startswith("_")},
            {"NARHistoricalPastRaceAbsenceSourceError", "NARHistoricalPastRaceAbsenceSourceValidationError", "normalize_nar_historical_past_race_absence_source_record"},
        )
        self.assertEqual(tuple(inspect.signature(normalize_nar_historical_past_race_absence_source_record).parameters), ("target_track_record", "target_entry_record", "horse_history_response"))
        tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
        forbidden = {"requests", "httpx", "sqlite3", "pathlib", "random", "subprocess", "time"}
        self.assertFalse(any((isinstance(node, ast.Import) and any(item.name.split(".")[0] in forbidden for item in node.names)) or (isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] in forbidden) for node in ast.walk(tree)))

    def test_zero_fixture_creates_exact_c1a_absence_record(self) -> None:
        record = _normalize()
        self.assertEqual(validate_historical_input_source_record_set(records=(record,)), (record,))
        self.assertEqual(record.record_kind, "past_race_absence")
        self.assertEqual(record.organization, "NAR")
        self.assertEqual(record.source_system, "nar_official")
        self.assertEqual(record.external_race_id, RACE_ID)
        self.assertEqual(record.external_entry_id, ENTRY_ID)
        self.assertIsNone(record.provider_record_id)
        self.assertEqual(dict(record.record_values), {"external_entry_id": ENTRY_ID, "query_scope": {"external_entry_id": ENTRY_ID, "target_race_date": date(2026, 7, 4), "strictly_before_target_race": True}, "result_count": 0})
        self.assertTrue(record.source_id.startswith("his-v4:past_race_absence:"))
        self.assertEqual(len(record.evidence), 1)
        evidence = record.evidence[0]
        self.assertEqual(evidence.evidence_role, "past_race_absence_query")
        self.assertEqual(evidence.canonical_source_url, URL)
        self.assertEqual(evidence.response_sha256, hashlib.sha256(ZERO_BODY).hexdigest())
        self.assertIsNone(evidence.available_at)
        self.assertEqual(evidence.observed_at, OBSERVED)

    def test_timestamp_does_not_change_source_id_but_bytes_do(self) -> None:
        baseline = _normalize()
        changed_time = _normalize(horse_history_response=_response(observed=OBSERVED + timedelta(minutes=1)))
        changed_bytes = _normalize(body=ZERO_BODY.replace(b"</body>", b"<!-- exact ignored byte change --></body>"))
        self.assertEqual(baseline.source_id, changed_time.source_id)
        self.assertNotEqual(baseline.evidence[0].observed_at, changed_time.evidence[0].observed_at)
        self.assertNotEqual(baseline.source_id, changed_bytes.source_id)

    def test_nonzero_malformed_and_late_evidence_are_rejected(self) -> None:
        with self.assertRaises(NARHistoricalPastRaceAbsenceSourceValidationError):
            _normalize(body=HISTORY_BODY)
        with self.assertRaises(NARHistoricalPastRaceAbsenceSourceValidationError):
            _normalize(body=ZERO_BODY.replace("指定の馬の出走履歴がありません。".encode(), b"no history"))
        with self.assertRaises(NARHistoricalPastRaceAbsenceSourceValidationError):
            _normalize(target_entry_record=_entry(lineage="30055402718"))
        with self.assertRaises(NARHistoricalPastRaceAbsenceSourceValidationError):
            _normalize(horse_history_response=_response(observed=SCHEDULED + timedelta(seconds=1)))
        with self.assertRaises(NARHistoricalPastRaceAbsenceSourceValidationError):
            _normalize(horse_history_response=object())
