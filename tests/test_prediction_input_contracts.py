"""Structural immutable-input contracts for the prediction pipeline."""

from __future__ import annotations

from dataclasses import fields, replace
from datetime import date
import inspect
from typing import Mapping, Sequence, get_args, get_type_hints
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
from scripts.simulation.models import ImmutableRacePredictionInput, PastRaceSnapshot


REFERENCE_DATE = date(2026, 8, 1)


def _annotation_contains(annotation: object, target: object) -> bool:
    if annotation is target:
        return True
    return any(
        _annotation_contains(argument, target)
        for argument in get_args(annotation)
    )


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

    def test_formal_and_immutable_past_race_fields_are_exactly_marginless(self) -> None:
        expected = (
            "horse_id",
            "race_date",
            "place",
            "race_name",
            "race_class",
            "distance",
            "track",
            "weather",
            "track_condition",
            "finish",
            "time",
            "weight",
            "weight_diff",
            "jockey",
            "popularity",
            "odds",
            "passing_order",
            "fourth_corner_position",
        )
        protocol_properties = tuple(
            name
            for name, value in PastRaceInput.__dict__.items()
            if isinstance(value, property)
        )

        self.assertEqual(protocol_properties, expected)
        self.assertEqual(tuple(field.name for field in fields(PastRaceSnapshot)), expected)
        self.assertIn("margin", get_type_hints(PastRace))

    def test_engine_past_race_annotations_do_not_reference_concrete_model(self) -> None:
        engines = (AbilityEngine, PaceEngine, JockeyEngine, TrackEngine)
        for engine in engines:
            for _, method in inspect.getmembers(engine, inspect.isfunction):
                hints = get_type_hints(method)
                for parameter in inspect.signature(method).parameters:
                    self.assertFalse(
                        _annotation_contains(hints.get(parameter), PastRace),
                        f"{engine.__name__}.{method.__name__}.{parameter}",
                    )

    def test_annotation_contains_detects_nested_concrete_past_race(self) -> None:
        self.assertTrue(_annotation_contains(Sequence[PastRace], PastRace))
        self.assertTrue(
            _annotation_contains(
                Mapping[int, Sequence[PastRace]],
                PastRace,
            )
        )
        self.assertFalse(_annotation_contains(Sequence[PastRaceInput], PastRace))

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

    def test_immutable_conversion_discards_legacy_margin(self) -> None:
        first = self._race_input()
        second = replace(
            first,
            horse_past_races={
                horse_id: [replace(race, margin=99.0) for race in past_races]
                for horse_id, past_races in first.horse_past_races.items()
            },
        )

        first_immutable = ImmutableRacePredictionInput.from_race_prediction_input(first)
        second_immutable = ImmutableRacePredictionInput.from_race_prediction_input(second)

        self.assertEqual(first_immutable, second_immutable)
        self.assertFalse(hasattr(first_immutable.horse_past_races[101][0], "margin"))
        pipeline = self._pipeline()
        self.assertEqual(
            pipeline.run(first).ability_evaluations,
            pipeline.run(second).ability_evaluations,
        )


if __name__ == "__main__":
    unittest.main()
