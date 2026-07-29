"""Structural immutable-input contracts for the prediction pipeline."""

from __future__ import annotations

from datetime import date
import inspect
from typing import Mapping, Sequence, get_type_hints
import unittest

from scripts.models import PastRace
from scripts.prediction.ability_engine import AbilityEngine
from scripts.prediction.bet_generator import BetGenerator
from scripts.prediction.bet_strategy import RuleBasedBetStrategy, StrategyConfig
from scripts.prediction.input_contracts import (
    PastRaceInput,
    PredictionPipelineInput,
    RaceTrackConditionsInput,
)
from scripts.prediction.jockey_engine import JockeyEngine
from scripts.prediction.pace_engine import PaceEngine
from scripts.prediction.prediction_pipeline import (
    PipelineConfig,
    PredictionPipeline,
    RacePredictionInput,
)
from scripts.prediction.predictor import Predictor
from scripts.prediction.track_engine import RaceTrackConditions, TrackEngine
from scripts.prediction.value_engine import ValueEngine
from scripts.simulation.models import ImmutableRacePredictionInput


REFERENCE_DATE = date(2026, 8, 1)


def _past_race(*, horse_id: int, finish: int, jockey: str) -> PastRace:
    return PastRace(
        horse_id=horse_id,
        race_date="2026-07-15",
        place="Tokyo",
        race_name="Example Stakes",
        race_class="Open",
        distance=1600,
        track="turf",
        weather="sunny",
        track_condition="good",
        finish=finish,
        margin=0.2,
        time="1:34.0",
        weight=480.0,
        weight_diff=2.0,
        jockey=jockey,
        popularity=finish,
        odds=2.0 + finish,
        passing_order="2-2-2-2",
        fourth_corner_position=2,
    )


class PredictionInputContractsTest(unittest.TestCase):
    def _pipeline(self) -> PredictionPipeline:
        return PredictionPipeline(
            PipelineConfig(
                ability_engine=AbilityEngine(reference_date=REFERENCE_DATE),
                pace_engine=PaceEngine(),
                jockey_engine=JockeyEngine(reference_date=REFERENCE_DATE),
                track_engine=TrackEngine(reference_date=REFERENCE_DATE),
                predictor=Predictor(),
                value_engine=ValueEngine(),
                bet_generator=BetGenerator(),
                bet_strategy=RuleBasedBetStrategy(),
                strategy_config=StrategyConfig(),
            )
        )

    def _race_input(self) -> RacePredictionInput:
        return RacePredictionInput(
            horse_past_races={
                101: [_past_race(horse_id=101, finish=1, jockey="A")],
                202: [_past_race(horse_id=202, finish=2, jockey="B")],
            },
            jockey_names_by_horse={101: "A", 202: "B"},
            track_conditions=RaceTrackConditions("Tokyo", 1600, "turf", "good"),
            odds_by_horse={101: 2.5, 202: 4.0},
            race_horse_count=2,
            race_id=12345,
            prediction_time="2026-08-01T09:00:00+00:00",
        )

    def test_public_evaluation_annotations_use_readonly_protocols(self) -> None:
        pipeline_hints = get_type_hints(PredictionPipeline.run)
        ability_hints = get_type_hints(AbilityEngine.evaluate)
        pace_hints = get_type_hints(PaceEngine.evaluate)
        jockey_hints = get_type_hints(JockeyEngine.evaluate)
        track_hints = get_type_hints(TrackEngine.evaluate)
        value_hints = get_type_hints(ValueEngine.evaluate)

        self.assertIs(pipeline_hints["race_input"], PredictionPipelineInput)
        self.assertEqual(ability_hints["past_races"], Sequence[PastRaceInput])
        self.assertEqual(pace_hints["horse_past_races"], Mapping[int, Sequence[PastRaceInput]])
        self.assertEqual(jockey_hints["past_races"], Sequence[PastRaceInput])
        self.assertIs(track_hints["target"], RaceTrackConditionsInput)
        self.assertEqual(track_hints["horse_past_races"], Mapping[int, Sequence[PastRaceInput]])
        self.assertEqual(value_hints["odds_by_horse"], Mapping[int, object])

    def test_engine_past_race_annotations_do_not_reference_concrete_model(self) -> None:
        engines = (AbilityEngine, PaceEngine, JockeyEngine, TrackEngine)
        for engine in engines:
            for _, method in inspect.getmembers(engine, inspect.isfunction):
                hints = get_type_hints(method)
                self.assertNotIn(PastRace, hints.values())

    def test_mutable_and_immutable_inputs_produce_equal_results_without_mutation(self) -> None:
        race_input = self._race_input()
        before_horse_past_races = {
            horse_id: list(past_races)
            for horse_id, past_races in race_input.horse_past_races.items()
        }
        before_jockey_names = dict(race_input.jockey_names_by_horse)
        before_odds = dict(race_input.odds_by_horse)
        immutable_input = ImmutableRacePredictionInput.from_race_prediction_input(race_input)
        pipeline = self._pipeline()

        mutable_result = pipeline.run(race_input)
        immutable_result = pipeline.run(immutable_input)

        self.assertEqual(mutable_result, immutable_result)
        self.assertEqual(mutable_result.predictions, immutable_result.predictions)
        self.assertEqual(mutable_result.bet_plan, immutable_result.bet_plan)
        self.assertEqual(
            tuple(prediction.horse_id for prediction in mutable_result.predictions),
            tuple(prediction.horse_id for prediction in immutable_result.predictions),
        )
        self.assertEqual(race_input.horse_past_races, before_horse_past_races)
        self.assertEqual(race_input.jockey_names_by_horse, before_jockey_names)
        self.assertEqual(race_input.odds_by_horse, before_odds)


if __name__ == "__main__":
    unittest.main()
