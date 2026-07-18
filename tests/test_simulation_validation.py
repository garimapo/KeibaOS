"""シミュレーション入力の完全監査と Fail Closed 検証テスト。"""

from __future__ import annotations

from datetime import date, datetime, timezone
import unittest

from scripts.models import PastRace
from scripts.prediction.prediction_pipeline import RacePredictionInput
from scripts.prediction.track_engine import RaceTrackConditions
from scripts.simulation.models import InputAuditEntry, InputSnapshotAudit, SimulationRaceInput
from scripts.simulation.validation import SimulationValidationError


UTC = timezone.utc
CUTOFF = datetime(2026, 1, 10, 9, 0, tzinfo=UTC)


def past_race(race_date: str = "2026-01-09") -> PastRace:
    return PastRace(1, race_date, "東京", "レース", "1勝", 1600, "芝", "晴", "良", 1, 0.0, "1:34", 500.0, 0.0, "騎手", 1, 2.0)


def pipeline(past_races: list[PastRace] | None = None) -> RacePredictionInput:
    return RacePredictionInput({1: past_races or []}, {1: "騎手"}, RaceTrackConditions("東京", 1600, "芝", "良"), {1: 2.0}, 1, 99)


def entry(input_type: str, key: str, *, observed_at: datetime | None = CUTOFF, index: int | None = None) -> InputAuditEntry:
    return InputAuditEntry(input_type, key, "source", key, None if input_type == "track" else 1, observed_at=observed_at, past_race_index=index)


def audit(*, past_count: int = 0, observed_at: datetime | None = CUTOFF, complete: bool = True) -> InputSnapshotAudit:
    entries = [entry("entry", "entry/1", observed_at=observed_at), entry("odds", "odds/1", observed_at=observed_at), entry("jockey", "jockey/1", observed_at=observed_at), entry("track", "track", observed_at=observed_at)]
    if past_count:
        entries.extend(entry("past_race", f"past_race/1/{index}", observed_at=observed_at, index=index) for index in range(past_count))
    else:
        entries.append(entry("past_race", "past_race/1/none", observed_at=observed_at))
    return InputSnapshotAudit("dataset", "source", CUTOFF, entries, complete)


def race_input(*, past_races: list[PastRace] | None = None, snapshot: InputSnapshotAudit | None = None, raw: RacePredictionInput | None = None, cutoff: datetime = CUTOFF, start: datetime = CUTOFF) -> SimulationRaceInput:
    races = past_races or []
    return SimulationRaceInput(99, date(2026, 1, 10), start, cutoff, raw or pipeline(races), snapshot or audit(past_count=len(races)))


class SimulationValidationTest(unittest.TestCase):
    def test_cutoff_boundary_and_naive_datetime(self) -> None:
        self.assertEqual(race_input().information_cutoff, CUTOFF)
        with self.assertRaisesRegex(ValueError, "information_cutoff"):
            race_input(start=CUTOFF.replace(hour=8))
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            InputAuditEntry("entry", "entry/1", "source", "id", 1, observed_at=datetime(2026, 1, 1))

    def test_every_pipeline_input_item_requires_exact_audit_key(self) -> None:
        incomplete = InputSnapshotAudit("dataset", "source", CUTOFF, [entry("entry", "entry/1"), entry("odds", "odds/1"), entry("jockey", "jockey/1"), entry("track", "track")], True)
        with self.assertRaisesRegex(SimulationValidationError, "past_race"):
            race_input(snapshot=incomplete)
        wrong = audit()
        wrong_entries = list(wrong.entries) + [entry("odds", "odds/999")]
        with self.assertRaisesRegex(SimulationValidationError, "odds/999"):
            race_input(snapshot=InputSnapshotAudit("dataset", "source", CUTOFF, wrong_entries, True))

    def test_audit_completeness_and_future_information_are_fail_closed(self) -> None:
        with self.assertRaisesRegex(SimulationValidationError, "not complete"):
            race_input(snapshot=audit(complete=False))
        with self.assertRaisesRegex(SimulationValidationError, "entry/1"):
            race_input(snapshot=audit(observed_at=CUTOFF.replace(hour=10)))

    def test_same_day_and_future_past_races_are_rejected(self) -> None:
        for value in ("2026-01-10", "2026-01-11"):
            with self.assertRaises(SimulationValidationError):
                race_input(past_races=[past_race(value)])

    def test_prediction_input_is_defensively_snapshotted(self) -> None:
        raw = pipeline([past_race()])
        value = race_input(raw=raw, snapshot=audit(past_count=1))
        raw.horse_past_races[1].append(past_race("2026-01-08"))
        raw.odds_by_horse[1] = 99.0
        raw.horse_past_races[1][0].race_date = "2099-01-01"
        object.__setattr__(raw.track_conditions, "place", "変更後")
        self.assertEqual(len(value.pipeline_input.horse_past_races[1]), 1)
        self.assertEqual(value.pipeline_input.odds_by_horse[1], 2.0)
        self.assertEqual(value.pipeline_input.horse_past_races[1][0].race_date, "2026-01-09")
        self.assertEqual(value.pipeline_input.track_conditions.place, "東京")
