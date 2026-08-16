from __future__ import annotations

import ast
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import inspect
from pathlib import Path
from unittest.mock import Mock, patch
import unittest

from scripts.simulation.historical_input_evidence import HistoricalInputEvidenceReference
from scripts.simulation.historical_input_source_records import (
    HistoricalInputSourceConflictError,
    HistoricalInputSourceRecord,
)
from scripts.simulation.jra_historical_input_source_collection import (
    JRAHistoricalSourceCollection,
    JRAHistoricalSourceCollectionUnsupportedError,
    JRAHistoricalSourceCollectionValidationError,
    collect_jra_historical_input_source_records,
)
from scripts.simulation.jra_historical_past_race_absence_source import (
    JRAHistoricalPastRaceAbsenceSourceValidationError,
)
from scripts.simulation.jra_historical_past_race_discovery import (
    JRAHistoricalEventKind,
    JRAHistoricalPastRaceDiscovery,
    JRAHistoricalPastRaceDiscoveryUnsupportedError,
    JRAHistoricalPastRaceDiscoveryValidationError,
    JRAHistoricalPastRaceReference,
)
from scripts.simulation.jra_historical_past_race_source import (
    JRAHistoricalPastRaceSourceUnsupportedError,
    JRAHistoricalPastRaceSourceValidationError,
)
from scripts.simulation.jra_official_identity import (
    build_jra_final_win_odds_request_locator,
    parse_jra_external_race_id,
)
from scripts.simulation.jra_official_response_capture import (
    JRAFinalWinOddsSuppliedOfficialResponse,
    JRASuppliedOfficialResponse,
)


UTC = timezone.utc
RACE_ID = "jra:race:2026:06:01:02:12"
ENTRY_ID = f"{RACE_ID}:entry:7"
HORSE_ID = "jra:horse:3001234567"
OBSERVED = datetime(2026, 6, 1, 10, tzinfo=UTC)
SCHEDULED = datetime(2026, 7, 1, 12, tzinfo=UTC)
PROFILE_URL = "https://www.jra.go.jp/JRADB/accessU.html?CNAME=pw01dud103001234567%2FAA"
RESULT_URL = "https://www.jra.go.jp/JRADB/accessS.html?CNAME=pw01sde1005202601020320260601%2FAA"
LOCATOR = build_jra_final_win_odds_request_locator(cname="pw151ou1006202601021220260105Z/2E")


def _evidence(role: str, marker: str) -> tuple[HistoricalInputEvidenceReference, ...]:
    return (HistoricalInputEvidenceReference(role, f"https://example.test/{marker}", marker * 64, None, OBSERVED),)


def _track() -> HistoricalInputSourceRecord:
    return HistoricalInputSourceRecord(
        "track", "JRA", "jra_official", RACE_ID, None, None,
        {"target_race_date": date(2026, 7, 1), "scheduled_start_at": SCHEDULED, "place": "東京", "distance_m": 1600, "track": "芝", "track_condition": "良", "race_name": None, "race_class": None, "weather": None},
        _evidence("track", "a"),
    )


def _entry() -> HistoricalInputSourceRecord:
    return HistoricalInputSourceRecord(
        "entry", "JRA", "jra_official", RACE_ID, ENTRY_ID, None,
        {"external_entry_id": ENTRY_ID, "external_horse_id": HORSE_ID, "horse_no": 7}, _evidence("entry", "b"),
    )


def _horse_response() -> JRASuppliedOfficialResponse:
    return JRASuppliedOfficialResponse(PROFILE_URL, b"x", "cp932", OBSERVED)


def _reference(*, kind: JRAHistoricalEventKind = JRAHistoricalEventKind.JRA_ACTUAL_START, day: int = 1) -> JRAHistoricalPastRaceReference:
    if kind is JRAHistoricalEventKind.JRA_ACTUAL_START:
        identity = LOCATOR.external_race_identity
        return JRAHistoricalPastRaceReference(kind, date(2026, 6, day), f"jra:event:{day}", identity, RESULT_URL)
    return JRAHistoricalPastRaceReference(kind, date(2026, 6, day), f"event:{day}", None, None)


def _discovery(*, events: tuple[JRAHistoricalPastRaceReference, ...] = ()) -> JRAHistoricalPastRaceDiscovery:
    response = _horse_response()
    return JRAHistoricalPastRaceDiscovery(
        RACE_ID, ENTRY_ID, HORSE_ID, date(2026, 7, 1), events, events == (),
        response.response_url, hashlib.sha256(response.response_body).hexdigest(), response.observed_at,
    )


def _absence() -> HistoricalInputSourceRecord:
    return HistoricalInputSourceRecord(
        "past_race_absence", "JRA", "jra_official", RACE_ID, ENTRY_ID, None,
        {"external_entry_id": ENTRY_ID, "query_scope": {"external_entry_id": ENTRY_ID, "target_race_date": date(2026, 7, 1), "strictly_before_target_race": True}, "result_count": 0},
        _evidence("past_race_absence_query", "c"),
    )


def _past(marker: str, race_date: date = date(2026, 6, 1)) -> HistoricalInputSourceRecord:
    values = {"race_date": race_date, "place": "東京", "race_name": "過去", "race_class": "1勝", "distance_m": 1600, "track": "芝", "weather": "晴", "track_condition": "良", "finish": 1, "race_time": "1:34.5", "weight": Decimal("480"), "weight_diff": Decimal("0"), "jockey": "騎手", "popularity": 1, "odds": Decimal("2.0"), "passing_order": "1-1", "fourth_corner_position": 1}
    evidence = (
        HistoricalInputEvidenceReference("historical_race_context", f"https://example.test/{marker}", "d" * 64, None, OBSERVED),
        HistoricalInputEvidenceReference("historical_race_result", f"https://example.test/{marker}", "e" * 64, None, OBSERVED),
    )
    return HistoricalInputSourceRecord("past_race", "JRA", "jra_official", RACE_ID, ENTRY_ID, f"jra:result:{marker}", values, evidence)


def _result(observed: datetime = OBSERVED) -> JRASuppliedOfficialResponse:
    return JRASuppliedOfficialResponse(RESULT_URL, b"x", "cp932", observed)


def _odds(observed: datetime = OBSERVED) -> JRAFinalWinOddsSuppliedOfficialResponse:
    return JRAFinalWinOddsSuppliedOfficialResponse(LOCATOR, b"x", "cp932", observed)


class JRAHistoricalInputSourceCollectionTests(unittest.TestCase):
    def test_public_surface_and_purity(self) -> None:
        import scripts.simulation as package
        import scripts.simulation.jra_historical_input_source_collection as module

        self.assertEqual({name for name in vars(module) if not name.startswith("_")}, {"JRAHistoricalRaceResultResponseProvider", "JRAHistoricalFinalWinOddsResponseProvider", "JRAHistoricalSourceCollection", "JRAHistoricalSourceCollectionError", "JRAHistoricalSourceCollectionValidationError", "JRAHistoricalSourceCollectionUnsupportedError", "collect_jra_historical_input_source_records"})
        self.assertEqual(tuple(inspect.signature(collect_jra_historical_input_source_records).parameters), ("target_track_record", "target_entry_record", "horse_history_response", "race_result_response_provider", "final_win_odds_response_provider"))
        self.assertTrue(JRAHistoricalSourceCollection.__dataclass_params__.frozen)
        self.assertTrue(hasattr(JRAHistoricalSourceCollection, "__slots__"))
        self.assertFalse(hasattr(package, "collect_jra_historical_input_source_records"))
        tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
        forbidden = {"requests", "httpx", "sqlite3", "pathlib", "random", "subprocess", "time", "urllib", "bs4"}
        self.assertFalse(any((isinstance(node, ast.Import) and any(item.name.split(".")[0] in forbidden for item in node.names)) or (isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] in forbidden) for node in ast.walk(tree)))

    def test_direct_constructor_validates_target_lineage_and_record_binding(self) -> None:
        record = _past("valid")
        self.assertEqual(JRAHistoricalSourceCollection(RACE_ID, ENTRY_ID, (record,)).source_records, (record,))
        invalid = (("not-a-race", ENTRY_ID), ("nar:race:2026:06:01:02:12", ENTRY_ID), (RACE_ID, "jra:race:2026:06:01:02:11:entry:7"), (RACE_ID, f"{RACE_ID}:entry:07"), (RACE_ID, f"{RACE_ID}:entry:0"), (RACE_ID, f"{RACE_ID}:entry:+7"), (RACE_ID, f"{RACE_ID}:entry:7:x"))
        for race_id, entry_id in invalid:
            with self.subTest(race_id=race_id, entry_id=entry_id), self.assertRaises(JRAHistoricalSourceCollectionValidationError):
                JRAHistoricalSourceCollection(race_id, entry_id, (record,))
        wrong = HistoricalInputSourceRecord("past_race", "JRA", "jra_official", RACE_ID, f"{RACE_ID}:entry:8", "jra:result:wrong", dict(record.record_values), record.evidence)
        with self.assertRaises(JRAHistoricalSourceCollectionValidationError):
            JRAHistoricalSourceCollection(RACE_ID, ENTRY_ID, (wrong,))

    def test_zero_and_transfer_only_project_without_provider_calls_or_rediscovery(self) -> None:
        for discovery in (_discovery(), _discovery(events=(_reference(kind=JRAHistoricalEventKind.PROVEN_NON_START),))):
            result_provider, odds_provider = Mock(), Mock()
            with patch("scripts.simulation.jra_historical_input_source_collection._discover", return_value=discovery) as discover, patch("scripts.simulation.jra_historical_input_source_collection._project_absence", return_value=_absence()) as project:
                output = collect_jra_historical_input_source_records(target_track_record=_track(), target_entry_record=_entry(), horse_history_response=_horse_response(), race_result_response_provider=result_provider, final_win_odds_response_provider=odds_provider)
            self.assertEqual(output.source_records, (_absence(),))
            self.assertEqual(discover.call_count, 1)
            self.assertEqual(project.call_count, 1)
            result_provider.assert_not_called()
            odds_provider.assert_not_called()

    def test_actual_start_order_dedup_and_final_validation(self) -> None:
        discovery = _discovery(events=(_reference(day=2), _reference(day=1)))
        result_provider = Mock(return_value=_result())
        odds_provider = Mock(return_value=_odds())
        with patch("scripts.simulation.jra_historical_input_source_collection._discover", return_value=discovery), patch("scripts.simulation.jra_historical_input_source_collection._result_response", side_effect=lambda **kwargs: kwargs["response"]), patch("scripts.simulation.jra_historical_input_source_collection._extract_locator", return_value=LOCATOR), patch("scripts.simulation.jra_historical_input_source_collection._odds_response", side_effect=lambda **kwargs: kwargs["response"]), patch("scripts.simulation.jra_historical_input_source_collection._normalize_past_race", side_effect=(_past("new", date(2026, 6, 2)), _past("old", date(2026, 6, 1)))) as normalize, patch("scripts.simulation.jra_historical_input_source_collection._validate_historical_input_source_record_set", side_effect=lambda *, records: records) as validate:
            output = collect_jra_historical_input_source_records(target_track_record=_track(), target_entry_record=_entry(), horse_history_response=_horse_response(), race_result_response_provider=result_provider, final_win_odds_response_provider=odds_provider)
        self.assertEqual(tuple(record.provider_record_id for record in output.source_records), ("jra:result:new", "jra:result:old"))
        self.assertEqual(result_provider.call_count, 1)
        self.assertEqual(odds_provider.call_count, 1)
        self.assertEqual(normalize.call_count, 2)
        self.assertEqual(validate.call_count, 1)

    def test_mixed_events_reject_before_provider_calls_and_late_evidence_rejects(self) -> None:
        for kind in (JRAHistoricalEventKind.NON_JRA_ACTUAL_START, JRAHistoricalEventKind.UNSUPPORTED_ACTUAL_START):
            with patch("scripts.simulation.jra_historical_input_source_collection._discover", return_value=_discovery(events=(_reference(kind=kind),))):
                provider = Mock()
                with self.assertRaises(JRAHistoricalSourceCollectionUnsupportedError):
                    collect_jra_historical_input_source_records(target_track_record=_track(), target_entry_record=_entry(), horse_history_response=_horse_response(), race_result_response_provider=provider, final_win_odds_response_provider=provider)
                provider.assert_not_called()
        with patch("scripts.simulation.jra_historical_input_source_collection._discover", return_value=_discovery(events=(_reference(),))):
            with self.assertRaises(JRAHistoricalSourceCollectionValidationError):
                collect_jra_historical_input_source_records(target_track_record=_track(), target_entry_record=_entry(), horse_history_response=_horse_response(), race_result_response_provider=lambda **_: _result(SCHEDULED + timedelta(seconds=1)), final_win_odds_response_provider=lambda **_: _odds())

    def test_exception_translation_and_provider_propagation(self) -> None:
        common = dict(target_track_record=_track(), target_entry_record=_entry(), horse_history_response=_horse_response(), race_result_response_provider=lambda **_: _result(), final_win_odds_response_provider=lambda **_: _odds())
        with patch("scripts.simulation.jra_historical_input_source_collection._discover", side_effect=JRAHistoricalPastRaceDiscoveryValidationError("bad")):
            with self.assertRaises(JRAHistoricalSourceCollectionValidationError): collect_jra_historical_input_source_records(**common)
        with patch("scripts.simulation.jra_historical_input_source_collection._discover", side_effect=JRAHistoricalPastRaceDiscoveryUnsupportedError("bad")):
            with self.assertRaises(JRAHistoricalSourceCollectionUnsupportedError): collect_jra_historical_input_source_records(**common)
        discovery = _discovery(events=(_reference(),))
        with patch("scripts.simulation.jra_historical_input_source_collection._discover", return_value=discovery), patch("scripts.simulation.jra_historical_input_source_collection._result_response", side_effect=lambda **kwargs: kwargs["response"]), patch("scripts.simulation.jra_historical_input_source_collection._extract_locator", return_value=LOCATOR), patch("scripts.simulation.jra_historical_input_source_collection._odds_response", side_effect=lambda **kwargs: kwargs["response"]), patch("scripts.simulation.jra_historical_input_source_collection._normalize_past_race", side_effect=JRAHistoricalPastRaceSourceUnsupportedError("bad")):
            with self.assertRaises(JRAHistoricalSourceCollectionUnsupportedError): collect_jra_historical_input_source_records(**common)
        marker = RuntimeError("provider")
        with patch("scripts.simulation.jra_historical_input_source_collection._discover", return_value=discovery):
            with self.assertRaisesRegex(RuntimeError, "provider"):
                collect_jra_historical_input_source_records(target_track_record=_track(), target_entry_record=_entry(), horse_history_response=_horse_response(), race_result_response_provider=lambda **_: (_ for _ in ()).throw(marker), final_win_odds_response_provider=lambda **_: _odds())

    def test_no_partial_return_when_later_normalization_fails(self) -> None:
        discovery = _discovery(events=(_reference(day=2), _reference(day=1)))
        with patch("scripts.simulation.jra_historical_input_source_collection._discover", return_value=discovery), patch("scripts.simulation.jra_historical_input_source_collection._result_response", side_effect=lambda **kwargs: kwargs["response"]), patch("scripts.simulation.jra_historical_input_source_collection._extract_locator", return_value=LOCATOR), patch("scripts.simulation.jra_historical_input_source_collection._odds_response", side_effect=lambda **kwargs: kwargs["response"]), patch("scripts.simulation.jra_historical_input_source_collection._normalize_past_race", side_effect=(_past("first"), JRAHistoricalPastRaceSourceValidationError("bad"))):
            with self.assertRaises(JRAHistoricalSourceCollectionValidationError):
                collect_jra_historical_input_source_records(target_track_record=_track(), target_entry_record=_entry(), horse_history_response=_horse_response(), race_result_response_provider=lambda **_: _result(), final_win_odds_response_provider=lambda **_: _odds())
