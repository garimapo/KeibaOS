from __future__ import annotations

import ast
from datetime import date, datetime, timedelta, timezone
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
from scripts.simulation.jra_historical_past_race_absence_source import (
    JRAHistoricalPastRaceAbsenceSourceValidationError,
    normalize_jra_historical_past_race_absence_source_record,
)
from scripts.simulation.jra_historical_past_race_discovery import (
    JRAHistoricalEventKind,
    JRAHistoricalPastRaceDiscovery,
    discover_jra_historical_past_race_history,
)
from scripts.simulation.jra_official_response_capture import JRASuppliedOfficialResponse


UTC = timezone.utc
RACE_ID = "jra:race:2026:05:01:02:03"
ENTRY_ID = f"{RACE_ID}:entry:7"
HORSE_KEY = "3001234567"
HORSE_ID = f"jra:horse:{HORSE_KEY}"
PROFILE_URL = f"https://www.jra.go.jp/JRADB/accessU.html?CNAME=pw01dud10{HORSE_KEY}%2FAA"
RESULT_URL = "https://www.jra.go.jp/JRADB/accessS.html?CNAME=pw01sde1005202601020320260601%2FAA"
OBSERVED = datetime(2026, 6, 10, 10, tzinfo=UTC)
CAPTURED = datetime(2026, 6, 10, 11, tzinfo=UTC)
CUTOFF = datetime(2026, 6, 10, 12, tzinfo=UTC)
SCHEDULED = datetime(2026, 7, 4, 12, tzinfo=UTC)
HEADINGS = ("年月日", "場", "レース名", "距離", "馬場", "頭数", "人気", "着順", "騎手名", "負担重量", "馬体重", "タイム", "Rt", "1着馬（2着馬）")
AGGREGATE_HEADINGS = ("1着", "2着", "3着", "4着以下", "出走回数", "勝率", "連対率", "3着内率")


def _evidence(role: str, marker: str) -> tuple[HistoricalInputEvidenceReference, ...]:
    return (HistoricalInputEvidenceReference(role, f"https://example.test/{marker}", marker * 64, None, OBSERVED),)


def _track() -> HistoricalInputSourceRecord:
    return HistoricalInputSourceRecord(
        "track", "JRA", "jra_official", RACE_ID, None, None,
        {"target_race_date": date(2026, 7, 4), "scheduled_start_at": SCHEDULED, "place": "東京", "distance_m": 1600, "track": "芝", "track_condition": "良", "race_name": None, "race_class": None, "weather": None},
        _evidence("track", "a"),
    )


def _entry(*, horse_id: str = HORSE_ID) -> HistoricalInputSourceRecord:
    return HistoricalInputSourceRecord(
        "entry", "JRA", "jra_official", RACE_ID, ENTRY_ID, None,
        {"external_entry_id": ENTRY_ID, "external_horse_id": horse_id, "horse_no": 7},
        _evidence("entry", "b"),
    )


def _transfer(*, day: int, name: str = "JRAへ転入") -> str:
    values = (f"2026年{day}月1日", "", name, "", "", "", "", "", "", "", "", "", "", "")
    return "<tr>" + "".join(f"<td>{value}</td>" for value in values) + "</tr>"


def _actual(*, place: str = "東京", finish: str = "1", anchor: str | None = RESULT_URL, name: str = "テスト特別") -> str:
    values = ("2026年6月1日", place, name, "芝1600", "良", "12", "3", finish, "騎手", "56.0", "480", "1:34.5", "", "勝馬")
    cells = []
    for index, value in enumerate(values):
        cells.append(f'<td><a href="{anchor}">{value}</a></td>' if index == 2 and anchor else f"<td>{value}</td>")
    return "<tr>" + "".join(cells) + "</tr>"


def _aggregate_table(caption: str, count: int | None) -> str:
    if count is None:
        return f'<table class="basic narrow"><caption class="simple"><div class="main">{caption}</div></caption><tbody><tr><td>該当するデータがありません。</td></tr></tbody></table>'
    values = ("0", "0", "0", str(count), str(count), "0.000", "0.000", "0.000")
    return (
        f'<table class="basic narrow"><caption class="simple"><div class="main">{caption}</div></caption><thead><tr>'
        + "".join(f"<th>{heading}</th>" for heading in AGGREGATE_HEADINGS)
        + "</tr></thead><tbody><tr>" + "".join(f"<td>{value}</td>" for value in values) + "</tr></tbody></table>"
    )


def _body(*, rows: tuple[str, ...] | None, flat: int | None, obstacle: int | None, continuation: str = "") -> bytes:
    aggregate = (
        '<li id="result_unit"><div class="contents_header"><h2>レース条件別成績</h2></div><div class="race_data mt10"><div class="layout_grid">'
        f'<div class="cell left">{_aggregate_table("平地レース合計", flat)}</div>'
        f'<div class="cell right">{_aggregate_table("障害レース合計", obstacle)}</div>'
        "</div></div></li>"
    )
    if rows is None:
        history = '<div class="race_detail"><p><strong>該当するデータがありません。</strong></p></div>'
    else:
        history = '<div class="race_detail"><table class="basic narrow-xy striped"><thead><tr>' + "".join(f"<th>{heading}</th>" for heading in HEADINGS) + "</tr></thead><tbody>" + "".join(rows) + "</tbody></table></div>"
    return f"<html><body>{history}<ul>{aggregate}</ul>{continuation}</body></html>".encode("cp932")


def _response(*, body: bytes, observed: datetime = OBSERVED, url: str = PROFILE_URL) -> JRASuppliedOfficialResponse:
    return JRASuppliedOfficialResponse(url, body, "cp932", observed)


def _malformed_response() -> JRASuppliedOfficialResponse:
    response = object.__new__(JRASuppliedOfficialResponse)
    object.__setattr__(response, "response_url", PROFILE_URL)
    object.__setattr__(response, "response_body", b"\x81")
    object.__setattr__(response, "charset", "cp932")
    object.__setattr__(response, "observed_at", OBSERVED)
    return response


def _normalize(*, body: bytes, observed: datetime = OBSERVED, entry: HistoricalInputSourceRecord | None = None) -> HistoricalInputSourceRecord:
    return normalize_jra_historical_past_race_absence_source_record(
        target_track_record=_track(),
        target_entry_record=_entry() if entry is None else entry,
        horse_history_response=_response(body=body, observed=observed),
    )


def _target_record(kind: str, absence: HistoricalInputSourceRecord | None = None) -> HistoricalInputSourceRecord:
    if kind == "jockey":
        values = {"external_entry_id": ENTRY_ID, "jockey": "騎手"}
        role, marker = "jockey", "c"
    elif kind == "odds_win":
        values = {"external_entry_id": ENTRY_ID, "horse_no": 7, "win_odds": Decimal("2.5")}
        role, marker = "odds_win", "d"
    elif kind == "past_race":
        values = {"race_date": date(2026, 6, 1), "place": "東京", "race_name": "過去", "race_class": "1勝", "distance_m": 1600, "track": "芝", "weather": "晴", "track_condition": "良", "finish": 1, "race_time": "1:34.5", "weight": Decimal("480"), "weight_diff": Decimal("0"), "jockey": "騎手", "popularity": 1, "odds": Decimal("2.0"), "passing_order": "1-1", "fourth_corner_position": 1}
        role, marker = "historical_race_context", "e"
        evidence = (
            HistoricalInputEvidenceReference("historical_race_context", "https://example.test/past", marker * 64, None, OBSERVED),
            HistoricalInputEvidenceReference("historical_race_result", "https://example.test/past", "f" * 64, None, OBSERVED),
        )
        return HistoricalInputSourceRecord(kind, "JRA", "jra_official", RACE_ID, ENTRY_ID, "jra:result:past", values, evidence)
    else:
        raise AssertionError(kind)
    return HistoricalInputSourceRecord(kind, "JRA", "jra_official", RACE_ID, ENTRY_ID, None, values, _evidence(role, marker))


def _snapshot(*, absence: HistoricalInputSourceRecord, include_past: bool = False):
    records = (_track(), _entry(), _target_record("jockey"), _target_record("odds_win"), absence)
    if include_past:
        records += (_target_record("past_race"),)
    return build_historical_input_snapshot(
        dataset_id="dataset", internal_race_id=1, information_cutoff=CUTOFF, captured_at=CAPTURED,
        source_records=records, race_entry_id_by_external_entry_id={ENTRY_ID: 11},
    )


class JRAHistoricalPastRaceAbsenceSourceTests(unittest.TestCase):
    def test_public_surface_signature_and_purity(self) -> None:
        import scripts.simulation as package
        import scripts.simulation.jra_historical_past_race_absence_source as module

        self.assertEqual(
            {name for name in vars(module) if not name.startswith("_")},
            {"JRAHistoricalPastRaceAbsenceSourceError", "JRAHistoricalPastRaceAbsenceSourceValidationError", "normalize_jra_historical_past_race_absence_source_record"},
        )
        self.assertEqual(tuple(inspect.signature(normalize_jra_historical_past_race_absence_source_record).parameters), ("target_track_record", "target_entry_record", "horse_history_response"))
        self.assertFalse(hasattr(package, "normalize_jra_historical_past_race_absence_source_record"))
        tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
        forbidden = {"requests", "httpx", "sqlite3", "pathlib", "random", "subprocess", "time", "urllib"}
        self.assertFalse(any((isinstance(node, ast.Import) and any(item.name.split(".")[0] in forbidden for item in node.names)) or (isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] in forbidden) for node in ast.walk(tree)))

    def test_empty_history_creates_exact_neutral_absence_record(self) -> None:
        body = _body(rows=None, flat=None, obstacle=None)
        record = _normalize(body=body)
        self.assertEqual(validate_historical_input_source_record_set(records=(record,)), (record,))
        self.assertEqual((record.record_kind, record.organization, record.source_system, record.external_race_id, record.external_entry_id, record.provider_record_id), ("past_race_absence", "JRA", "jra_official", RACE_ID, ENTRY_ID, None))
        self.assertEqual(dict(record.record_values), {"external_entry_id": ENTRY_ID, "query_scope": {"external_entry_id": ENTRY_ID, "target_race_date": date(2026, 7, 4), "strictly_before_target_race": True}, "result_count": 0})
        self.assertEqual(len(record.evidence), 1)
        evidence = record.evidence[0]
        self.assertEqual(evidence.evidence_role, "past_race_absence_query")
        self.assertEqual(evidence.canonical_source_url, PROFILE_URL)
        self.assertEqual(evidence.response_sha256, hashlib.sha256(body).hexdigest())
        self.assertIsNone(evidence.available_at)
        self.assertEqual(evidence.observed_at, OBSERVED)
        self.assertIsNone(evidence.request_identity_sha256)

    def test_transfer_only_nonempty_history_proves_zero_actual_starts(self) -> None:
        one = _body(rows=(_transfer(day=6),), flat=0, obstacle=0)
        discovery = discover_jra_historical_past_race_history(target_track_record=_track(), target_entry_record=_entry(), horse_history_response=_response(body=one))
        self.assertFalse(discovery.proven_zero_history)
        self.assertEqual(tuple(event.event_kind for event in discovery.events), (JRAHistoricalEventKind.PROVEN_NON_START,))
        self.assertEqual(_normalize(body=one).record_values["result_count"], 0)
        multiple = _body(rows=(_transfer(day=6), _transfer(day=5, name="JRAより転出")), flat=0, obstacle=0)
        self.assertEqual(_normalize(body=multiple).record_kind, "past_race_absence")

    def test_actual_start_kinds_always_prevent_absence(self) -> None:
        cases = (
            (_actual(), 1),
            (_actual(place="園田", anchor=None), 1),
            (_actual(finish="中止"), 1),
            (_transfer(day=6) + _actual(), 1),
            (_transfer(day=6) + _actual(place="園田", anchor=None), 1),
            (_transfer(day=6) + _actual(finish="中止"), 1),
        )
        for rows, count in cases:
            with self.subTest(rows=rows), self.assertRaises(JRAHistoricalPastRaceAbsenceSourceValidationError):
                _normalize(body=_body(rows=(rows,) if isinstance(rows, str) and rows.startswith("<tr>") else (), flat=count, obstacle=0))

    def test_discovery_failures_are_translated(self) -> None:
        with self.assertRaises(JRAHistoricalPastRaceAbsenceSourceValidationError):
            _normalize(body=_body(rows=(_transfer(day=6),), flat=1, obstacle=0))
        with self.assertRaises(JRAHistoricalPastRaceAbsenceSourceValidationError):
            _normalize(body=_body(rows=None, flat=None, obstacle=None, continuation='<a class="next" href="?page=2">next</a>'))
        with self.assertRaises(JRAHistoricalPastRaceAbsenceSourceValidationError):
            normalize_jra_historical_past_race_absence_source_record(
                target_track_record=_track(), target_entry_record=_entry(), horse_history_response=_malformed_response(),
            )
        with self.assertRaises(JRAHistoricalPastRaceAbsenceSourceValidationError):
            _normalize(body=_body(rows=None, flat=None, obstacle=None), observed=SCHEDULED + timedelta(seconds=1))
        with self.assertRaises(JRAHistoricalPastRaceAbsenceSourceValidationError):
            _normalize(body=_body(rows=None, flat=None, obstacle=None), entry=_entry(horse_id="jra:horse:3001234568"))

    def test_calls_formal_discovery_once(self) -> None:
        import scripts.simulation.jra_historical_past_race_absence_source as module
        from unittest.mock import patch

        body = _body(rows=None, flat=None, obstacle=None)
        response = _response(body=body)
        discovery = JRAHistoricalPastRaceDiscovery(RACE_ID, ENTRY_ID, HORSE_ID, date(2026, 7, 4), (), True)
        with patch.object(module, "_discover_jra_historical_past_race_history", return_value=discovery) as discover:
            record = normalize_jra_historical_past_race_absence_source_record(
                target_track_record=_track(), target_entry_record=_entry(), horse_history_response=response,
            )
        discover.assert_called_once_with(target_track_record=_track(), target_entry_record=_entry(), horse_history_response=response)
        self.assertEqual(record.record_kind, "past_race_absence")

    def test_source_id_follows_raw_bytes_not_timestamps(self) -> None:
        body = _body(rows=None, flat=None, obstacle=None)
        baseline = _normalize(body=body)
        changed_time = _normalize(body=body, observed=OBSERVED + timedelta(minutes=1))
        changed_bytes = _normalize(body=body.replace(b"</body>", b"<!-- raw change --></body>"))
        self.assertEqual(baseline.source_id, changed_time.source_id)
        self.assertNotEqual(baseline.source_id, changed_bytes.source_id)

    def test_snapshot_accepts_empty_and_transfer_only_absences_and_xor_rejects(self) -> None:
        empty = _normalize(body=_body(rows=None, flat=None, obstacle=None))
        transfer = _normalize(body=_body(rows=(_transfer(day=6),), flat=0, obstacle=0))
        for absence in (empty, transfer):
            snapshot = _snapshot(absence=absence)
            self.assertEqual(snapshot.past_races, ())
            self.assertTrue(any(item.audit_key == "past_race/11/none" for item in snapshot.provenance))
        with self.assertRaises(HistoricalInputSnapshotAssemblyError):
            _snapshot(absence=empty, include_past=True)
