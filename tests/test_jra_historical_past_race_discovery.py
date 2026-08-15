from __future__ import annotations

import ast
from dataclasses import is_dataclass
from datetime import date, datetime, timedelta, timezone
import inspect
from pathlib import Path
import unittest

from scripts.simulation.historical_input_evidence import HistoricalInputEvidenceReference
from scripts.simulation.historical_input_source_records import HistoricalInputSourceRecord
from scripts.simulation.jra_historical_past_race_discovery import (
    JRAHistoricalEventKind,
    JRAHistoricalPastRaceDiscovery,
    JRAHistoricalPastRaceDiscoveryUnsupportedError,
    JRAHistoricalPastRaceDiscoveryValidationError,
    JRAHistoricalPastRaceReference,
    discover_jra_historical_past_race_history,
)
from scripts.simulation.jra_official_response_capture import JRASuppliedOfficialResponse


RACE_ID = "jra:race:2026:05:01:02:03"
ENTRY_ID = f"{RACE_ID}:entry:7"
HORSE_KEY = "3001234567"
HORSE_ID = f"jra:horse:{HORSE_KEY}"
PROFILE_URL = f"https://www.jra.go.jp/JRADB/accessU.html?CNAME=pw01dud10{HORSE_KEY}%2FAA"
RESULT_URL = "https://www.jra.go.jp/JRADB/accessS.html?CNAME=pw01sde1005202601020320260601%2FAA"
OBSERVED = datetime(2026, 6, 10, 10, tzinfo=timezone.utc)
SCHEDULED = datetime(2026, 7, 4, 12, tzinfo=timezone.utc)
HEADINGS = ("年月日", "場", "レース名", "距離", "馬場", "頭数", "人気", "着順", "騎手名", "負担重量", "馬体重", "タイム", "Rt", "1着馬（2着馬）")
AGGREGATE_HEADINGS = ("1着", "2着", "3着", "4着以下", "出走回数", "勝率", "連対率", "3着内率")


def _evidence(role: str, marker: str) -> tuple[HistoricalInputEvidenceReference, ...]:
    return (HistoricalInputEvidenceReference(role, f"https://example.test/{marker}", (marker * 64)[:64], None, OBSERVED),)


def _track(*, race_id: str = RACE_ID, scheduled: datetime = SCHEDULED) -> HistoricalInputSourceRecord:
    return HistoricalInputSourceRecord(
        "track", "JRA", "jra_official", race_id, None, None,
        {"target_race_date": date(2026, 7, 4), "scheduled_start_at": scheduled, "place": "東京", "distance_m": 1600, "track": "芝", "track_condition": "良", "race_name": None, "race_class": None, "weather": None},
        _evidence("track", "a"),
    )


def _entry(*, race_id: str = RACE_ID, entry_id: str = ENTRY_ID, horse_id: str = HORSE_ID, horse_no: int = 7) -> HistoricalInputSourceRecord:
    return HistoricalInputSourceRecord(
        "entry", "JRA", "jra_official", race_id, entry_id, None,
        {"external_entry_id": entry_id, "external_horse_id": horse_id, "horse_no": horse_no},
        _evidence("entry", "b"),
    )


def _actual(*, race_date: str, name: str = "テスト特別", finish: str = "1", anchor: str | None = None, place: str = "東京") -> str:
    values = (race_date, place, name, "芝1600", "良", "12", "3", finish, "騎手", "56.0", "480", "1:34.5", "", "勝馬")
    cells = []
    for index, value in enumerate(values):
        if index == 2 and anchor is not None:
            cells.append(f'<td><a href="{anchor}">{value}</a></td>')
        else:
            cells.append(f"<td>{value}</td>")
    return "<tr>" + "".join(cells) + "</tr>"


def _transfer(*, race_date: str = "2026年4月1日", name: str = "JRAへ転入") -> str:
    values = (race_date, "", name, "", "", "", "", "", "", "", "", "", "", "")
    return "<tr>" + "".join(f"<td>{value}</td>" for value in values) + "</tr>"


def _aggregate_table(caption: str, count: int | None, *, wins: tuple[int, int, int, int] | None = None) -> str:
    if count is None:
        return f'<table class="basic narrow"><caption class="simple"><div class="main">{caption}</div></caption><tbody><tr><td>該当するデータがありません。</td></tr></tbody></table>'
    if wins is None:
        wins = (0, 0, 0, count)
    values = (*wins, count, "0.000", "0.000", "0.000")
    return (
        f'<table class="basic narrow"><caption class="simple"><div class="main">{caption}</div></caption>'
        + "<thead><tr>" + "".join(f"<th>{value}</th>" for value in AGGREGATE_HEADINGS) + "</tr></thead>"
        + "<tbody><tr>" + "".join(f"<td>{value}</td>" for value in values) + "</tr></tbody></table>"
    )


def _body(*, rows: tuple[str, ...] | None = None, flat: int | None = 2, obstacle: int | None = 0, continuation: str = "") -> bytes:
    aggregate = (
        '<li id="result_unit"><div class="contents_header"><h2>レース条件別成績</h2></div>'
        '<div class="race_data mt10"><div class="layout_grid">'
        f'<div class="cell left">{_aggregate_table("平地レース合計", flat)}</div>'
        f'<div class="cell right">{_aggregate_table("障害レース合計", obstacle)}</div>'
        "</div></div></li>"
    )
    if rows is None:
        history = '<div class="race_detail"><p><strong>該当するデータがありません。</strong></p></div>'
    else:
        headings = "".join(f"<th>{value}</th>" for value in HEADINGS)
        history = f'<div class="race_detail"><table class="basic narrow-xy striped"><thead><tr>{headings}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
    return f"<html><body>{history}<ul>{aggregate}</ul>{continuation}</body></html>".encode("cp932")


def _response(*, body: bytes | None = None, url: str = PROFILE_URL, observed: datetime = OBSERVED) -> JRASuppliedOfficialResponse:
    if body is None:
        body = _body(rows=(
            _actual(race_date="2026年6月1日", anchor=RESULT_URL),
            _actual(race_date="2026年5月1日", name="園田競走", place="園田"),
            _transfer(),
        ))
    return JRASuppliedOfficialResponse(url, body, "cp932", observed)


def _discover(**changes: object) -> JRAHistoricalPastRaceDiscovery:
    track = changes.pop("target_track_record", _track())
    entry = changes.pop("target_entry_record", _entry())
    response = changes.pop("horse_history_response", None)
    if response is None:
        response = _response(**changes)
    return discover_jra_historical_past_race_history(
        target_track_record=track,
        target_entry_record=entry,
        horse_history_response=response,
    )


class JRAHistoricalPastRaceDiscoveryTests(unittest.TestCase):
    def test_public_surface_domain_and_purity(self) -> None:
        import scripts.simulation.jra_historical_past_race_discovery as module

        self.assertEqual(
            {name for name in vars(module) if not name.startswith("_")},
            {"JRAHistoricalEventKind", "JRAHistoricalPastRaceReference", "JRAHistoricalPastRaceDiscovery", "JRAHistoricalPastRaceDiscoveryError", "JRAHistoricalPastRaceDiscoveryValidationError", "JRAHistoricalPastRaceDiscoveryUnsupportedError", "discover_jra_historical_past_race_history"},
        )
        self.assertEqual(tuple(inspect.signature(discover_jra_historical_past_race_history).parameters), ("target_track_record", "target_entry_record", "horse_history_response"))
        self.assertEqual(tuple(JRAHistoricalEventKind), (JRAHistoricalEventKind.JRA_ACTUAL_START, JRAHistoricalEventKind.NON_JRA_ACTUAL_START, JRAHistoricalEventKind.PROVEN_NON_START, JRAHistoricalEventKind.UNSUPPORTED_ACTUAL_START))
        self.assertTrue(is_dataclass(JRAHistoricalPastRaceReference) and JRAHistoricalPastRaceReference.__dataclass_params__.frozen)
        self.assertTrue(is_dataclass(JRAHistoricalPastRaceDiscovery) and JRAHistoricalPastRaceDiscovery.__dataclass_params__.frozen)
        tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
        forbidden = {"requests", "httpx", "sqlite3", "pathlib", "random", "subprocess", "time"}
        self.assertFalse(any((isinstance(node, ast.Import) and any(item.name.split(".")[0] in forbidden for item in node.names)) or (isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] in forbidden) for node in ast.walk(tree)))

    def test_complete_mixed_history_retains_non_jra_and_excludes_transfer(self) -> None:
        result = _discover()
        self.assertFalse(result.proven_zero_history)
        self.assertEqual(result.target_external_race_id, RACE_ID)
        self.assertEqual(result.target_external_entry_id, ENTRY_ID)
        self.assertEqual(result.target_external_horse_id, HORSE_ID)
        self.assertEqual(tuple(event.event_kind for event in result.events), (JRAHistoricalEventKind.JRA_ACTUAL_START, JRAHistoricalEventKind.NON_JRA_ACTUAL_START, JRAHistoricalEventKind.PROVEN_NON_START))
        self.assertEqual(result.events[0].race_identity.external_race_id, RACE_ID)
        self.assertEqual(result.events[0].canonical_race_result_url, RESULT_URL)
        self.assertIsNone(result.events[1].race_identity)
        self.assertIsNone(result.events[1].canonical_race_result_url)
        self.assertNotEqual(result.events[1].provider_event_id, result.events[2].provider_event_id)
        self.assertEqual(_discover(), result)

    def test_aggregate_equality_truncation_and_mixed_surface(self) -> None:
        rows = tuple(_actual(race_date=f"2026年6月{day}日", anchor=RESULT_URL.replace("20260601", f"2026060{day}") if day == 1 else None, place="園田" if day != 1 else "東京") for day in (4, 3, 2, 1))
        with self.assertRaises(JRAHistoricalPastRaceDiscoveryValidationError):
            _discover(body=_body(rows=rows, flat=10, obstacle=0))
        complete = _discover(body=_body(rows=rows, flat=2, obstacle=2))
        self.assertEqual(len(complete.events), 4)
        with self.assertRaises(JRAHistoricalPastRaceDiscoveryValidationError):
            _discover(body=_body(rows=rows, flat=2, obstacle=2, continuation='<a class="next" href="?page=2">next</a>'))
        with self.assertRaises(JRAHistoricalPastRaceDiscoveryValidationError):
            _discover(body=_body(rows=rows, flat=2, obstacle=2).replace("<td>0</td><td>0</td><td>0</td><td>2</td><td>2</td>".encode("cp932"), "<td>0</td><td>0</td><td>0</td><td>1</td><td>2</td>".encode("cp932"), 1))

    def test_zero_history_requires_same_response_aggregate_proof(self) -> None:
        zero = _discover(body=_body(rows=None, flat=None, obstacle=None))
        self.assertTrue(zero.proven_zero_history)
        self.assertEqual(zero.events, ())
        with self.assertRaises(JRAHistoricalPastRaceDiscoveryValidationError):
            _discover(body=_body(rows=None, flat=1, obstacle=0))
        with self.assertRaises(JRAHistoricalPastRaceDiscoveryValidationError):
            _discover(body=_body(rows=(), flat=0, obstacle=0))
        with self.assertRaises(JRAHistoricalPastRaceDiscoveryValidationError):
            _discover(body=_body(rows=None, flat=None, obstacle=None, continuation='<a href="?page=2">next</a>'))

    def test_jra_anchor_identity_and_duplicate_safety(self) -> None:
        with self.assertRaises(JRAHistoricalPastRaceDiscoveryValidationError):
            _discover(body=_body(rows=(_actual(race_date="2026年6月1日"),), flat=1, obstacle=0))
        duplicate = _actual(race_date="2026年6月1日", anchor=RESULT_URL).replace("</td>", f'<a href="{RESULT_URL}">duplicate</a></td>', 1)
        with self.assertRaises(JRAHistoricalPastRaceDiscoveryValidationError):
            _discover(body=_body(rows=(duplicate,), flat=1, obstacle=0))
        bad_date = _actual(race_date="2026年6月2日", anchor=RESULT_URL)
        with self.assertRaises(JRAHistoricalPastRaceDiscoveryValidationError):
            _discover(body=_body(rows=(bad_date,), flat=1, obstacle=0))
        duplicate_events = (_actual(race_date="2026年6月1日", anchor=RESULT_URL), _actual(race_date="2026年5月1日", anchor=RESULT_URL))
        with self.assertRaises(JRAHistoricalPastRaceDiscoveryValidationError):
            _discover(body=_body(rows=duplicate_events, flat=2, obstacle=0))

    def test_non_start_unsupported_and_unknown_rows_fail_closed_as_required(self) -> None:
        unsupported = _actual(race_date="2026年6月1日", finish="中止", anchor=RESULT_URL)
        event = _discover(body=_body(rows=(unsupported,), flat=1, obstacle=0)).events[0]
        self.assertEqual(event.event_kind, JRAHistoricalEventKind.UNSUPPORTED_ACTUAL_START)
        conflicting = _transfer().replace("<td></td>", "<td>12</td>", 1)
        with self.assertRaises(JRAHistoricalPastRaceDiscoveryValidationError):
            _discover(body=_body(rows=(conflicting,), flat=0, obstacle=0))
        unknown = _actual(race_date="2026年6月1日", finish="謎")
        with self.assertRaises(JRAHistoricalPastRaceDiscoveryValidationError):
            _discover(body=_body(rows=(unknown,), flat=1, obstacle=0))

    def test_target_response_cutoff_and_structure_validation(self) -> None:
        for value in (object(),):
            with self.subTest(value=value), self.assertRaises(JRAHistoricalPastRaceDiscoveryValidationError):
                _discover(target_track_record=value)
        with self.assertRaises(JRAHistoricalPastRaceDiscoveryValidationError):
            _discover(target_entry_record=object())
        with self.assertRaises(JRAHistoricalPastRaceDiscoveryValidationError):
            _discover(horse_history_response=object())
        with self.assertRaises(JRAHistoricalPastRaceDiscoveryValidationError):
            _discover(target_entry_record=_entry(horse_id="jra:horse:3001234568"))
        with self.assertRaises(JRAHistoricalPastRaceDiscoveryValidationError):
            _discover(horse_history_response=_response(observed=SCHEDULED + timedelta(seconds=1)))
        with self.assertRaises(JRAHistoricalPastRaceDiscoveryValidationError):
            _discover(body=_body(rows=(_actual(race_date="2026年7月4日", anchor=RESULT_URL),), flat=1, obstacle=0))
        with self.assertRaises(JRAHistoricalPastRaceDiscoveryValidationError):
            _discover(body=_body(rows=(_actual(race_date="2026年6月1日", anchor=RESULT_URL),), flat=1, obstacle=0).replace("<th>年月日</th>".encode("cp932"), "<th>日付</th>".encode("cp932"), 1))

    def test_noncanonical_counts_and_non_jra_row_prevent_false_zero(self) -> None:
        local = _actual(race_date="2026年6月1日", name="地方", place="園田")
        result = _discover(body=_body(rows=(local,), flat=1, obstacle=0))
        self.assertEqual(result.events[0].event_kind, JRAHistoricalEventKind.NON_JRA_ACTUAL_START)
        with self.assertRaises(JRAHistoricalPastRaceDiscoveryValidationError):
            _discover(body=_body(rows=(local,), flat=1, obstacle=0).replace(b"<td>1</td><td>0.000", b"<td>01</td><td>0.000", 1))
