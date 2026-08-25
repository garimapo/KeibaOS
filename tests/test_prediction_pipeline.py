"""PredictionPipelineの単体テスト。"""

from __future__ import annotations

from datetime import date, datetime
import inspect
from typing import get_type_hints
import unittest
from unittest.mock import DEFAULT, patch

from scripts.models import PastRace, Prediction
from scripts.prediction.ability_engine import AbilityEngine, AbilityEvaluation
from scripts.prediction.bet_generator import BetGenerator, BetRecommendation
from scripts.prediction.bet_strategy import BetPlan, RuleBasedBetStrategy, StrategyConfig
from scripts.prediction.jockey_engine import JockeyEngine, JockeyEvaluation
from scripts.prediction.pace_engine import PaceEngine, PaceEvaluation
from scripts.prediction.prediction_pipeline import (
    PipelineConfig,
    PipelineExecutionError,
    PipelineStage,
    PredictionPipeline,
    RacePredictionInput,
    build_historical_prediction_pipeline,
)
from scripts.prediction.predictor import Predictor
from scripts.prediction.track_engine import RaceTrackConditions, TrackEngine, TrackEvaluation
from scripts.prediction.value_engine import ValueEngine, ValueEvaluation


class _RecordingEngines:
    """呼び出し順とデータフローを確認する注入用スタブ群。"""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def ability(self):
        parent = self

        class Engine:
            def evaluate(self, past_races):
                parent.calls.append("ability")
                return AbilityEvaluation(60.0, len(past_races), None)

        return Engine()

    def pace(self):
        parent = self

        class Engine:
            def evaluate(self, horse_past_races):
                parent.calls.append("pace")
                return PaceEvaluation("平均", {}, 0, 0)

        return Engine()

    def jockey(self):
        parent = self

        class Engine:
            def evaluate(self, jockey_name, past_races):
                parent.calls.append("jockey")
                return JockeyEvaluation(jockey_name, 0, 0.0, 0.0, 0.0, 0.0, 0.0)

        return Engine()

    def track(self):
        parent = self

        class Engine:
            def evaluate(self, target, horse_past_races):
                parent.calls.append("track")
                return {
                    horse_id: TrackEvaluation(horse_id, 0, 50.0, 50.0, 50.0, 50.0, 50.0)
                    for horse_id in horse_past_races
                }

        return Engine()

    def predictor(self):
        parent = self

        class Engine:
            def predict(self, horse_evaluations, **kwargs):
                parent.calls.append("predictor")
                return [
                    Prediction(kwargs["race_id"], kwargs["prediction_time"], "1", 80.0, False, "", horse_id)
                    for horse_id in horse_evaluations
                ]

        return Engine()

    def value(self):
        parent = self

        class Engine:
            def evaluate(self, predictions, odds_by_horse):
                parent.calls.append("value")
                return [ValueEvaluation(item.horse_id, 1.0, 2.0, 2.0, 100.0) for item in predictions]

        return Engine()

    def generator(self):
        parent = self

        class Engine:
            def generate(self, values, predictions, race_horse_count):
                parent.calls.append("bet_generator")
                return [BetRecommendation(1, "単勝", (1,), 1.0, 2.0, None, 80.0)]

        return Engine()

    def strategy(self):
        parent = self

        class Engine:
            def create_plan(self, recommendations, config):
                parent.calls.append("bet_strategy")
                return BetPlan("stub", tuple(recommendations), len(recommendations))

        return Engine()


class PredictionPipelineTest(unittest.TestCase):
    """段階順序、中間結果、例外変換を検証する。"""

    def _input(self) -> RacePredictionInput:
        return RacePredictionInput(
            horse_past_races={1: []},
            jockey_names_by_horse={1: "騎手"},
            track_conditions=RaceTrackConditions("東京", 1600, "芝", "良"),
            odds_by_horse={1: 2.0},
            race_horse_count=1,
            race_id=10,
            prediction_time="2026-07-18T12:00:00",
        )

    def test_orchestrates_stages_in_required_order_and_keeps_results(self) -> None:
        engines = _RecordingEngines()
        pipeline = PredictionPipeline(
            PipelineConfig(
                ability_engine=engines.ability(),  # type: ignore[arg-type]
                pace_engine=engines.pace(),  # type: ignore[arg-type]
                jockey_engine=engines.jockey(),  # type: ignore[arg-type]
                track_engine=engines.track(),  # type: ignore[arg-type]
                predictor=engines.predictor(),  # type: ignore[arg-type]
                value_engine=engines.value(),  # type: ignore[arg-type]
                bet_generator=engines.generator(),  # type: ignore[arg-type]
                bet_strategy=engines.strategy(),
                strategy_config=StrategyConfig(),
            )
        )

        result = pipeline.run(self._input())

        self.assertEqual(
            engines.calls,
            ["ability", "pace", "jockey", "track", "predictor", "value", "bet_generator", "bet_strategy"],
        )
        self.assertEqual(result.predictions[0].race_id, 10)
        self.assertEqual(result.value_evaluations[0].horse_id, 1)
        self.assertEqual(result.bet_plan.strategy_name, "stub")

    def test_stage_failure_is_wrapped_with_stage_name(self) -> None:
        class FailingPaceEngine:
            def evaluate(self, horse_past_races):
                raise RuntimeError("broken pace")

        pipeline = PredictionPipeline(
            PipelineConfig(pace_engine=FailingPaceEngine())  # type: ignore[arg-type]
        )

        with self.assertRaises(PipelineExecutionError) as context:
            pipeline.run(self._input())

        self.assertEqual(context.exception.stage, PipelineStage.PACE)
        self.assertIsInstance(context.exception.__cause__, RuntimeError)

    def test_historical_factory_has_exact_public_signature_and_components(self) -> None:
        signature = inspect.signature(build_historical_prediction_pipeline)
        self.assertEqual(tuple(signature.parameters), ("target_race_date", "strategy_config"))
        self.assertTrue(
            all(
                parameter.kind is inspect.Parameter.KEYWORD_ONLY
                for parameter in signature.parameters.values()
            )
        )
        hints = get_type_hints(build_historical_prediction_pipeline)
        self.assertEqual(
            hints,
            {
                "target_race_date": date,
                "strategy_config": StrategyConfig,
                "return": PredictionPipeline,
            },
        )

        target_race_date = date(2026, 8, 5)
        strategy_config = StrategyConfig(allowed_bet_types=frozenset())
        pipeline = build_historical_prediction_pipeline(
            target_race_date=target_race_date,
            strategy_config=strategy_config,
        )

        self.assertIs(type(pipeline), PredictionPipeline)
        self.assertIs(type(pipeline.config), PipelineConfig)
        self.assertIs(type(pipeline.config.ability_engine), AbilityEngine)
        self.assertIs(type(pipeline.config.pace_engine), PaceEngine)
        self.assertIs(type(pipeline.config.jockey_engine), JockeyEngine)
        self.assertIs(type(pipeline.config.track_engine), TrackEngine)
        self.assertIs(type(pipeline.config.predictor), Predictor)
        self.assertIs(type(pipeline.config.value_engine), ValueEngine)
        self.assertIs(type(pipeline.config.bet_generator), BetGenerator)
        self.assertIs(type(pipeline.config.bet_strategy), RuleBasedBetStrategy)
        self.assertIs(pipeline.config.strategy_config, strategy_config)
        self.assertIs(pipeline.config.ability_engine.reference_date, target_race_date)
        self.assertIs(pipeline.config.jockey_engine.reference_date, target_race_date)
        self.assertIs(pipeline.config.track_engine.reference_date, target_race_date)

    def test_historical_factory_validates_before_constructing_collaborators(self) -> None:
        replacements = {
            name: DEFAULT
            for name in (
                "AbilityEngine",
                "PaceEngine",
                "JockeyEngine",
                "TrackEngine",
                "Predictor",
                "ValueEngine",
                "BetGenerator",
                "RuleBasedBetStrategy",
            )
        }
        with patch.multiple(
            "scripts.prediction.prediction_pipeline",
            **replacements,
        ) as constructors:
            with self.assertRaisesRegex(TypeError, "target_race_date must be a date"):
                build_historical_prediction_pipeline(
                    target_race_date=datetime(2026, 8, 5),
                    strategy_config=StrategyConfig(),
                )
            for constructor in constructors.values():
                constructor.assert_not_called()

            with self.assertRaisesRegex(TypeError, "strategy_config must be a StrategyConfig"):
                build_historical_prediction_pipeline(
                    target_race_date=date(2026, 8, 5),
                    strategy_config=object(),  # type: ignore[arg-type]
                )
            for constructor in constructors.values():
                constructor.assert_not_called()

    def test_historical_factory_does_not_use_current_date_defaults(self) -> None:
        class EarlyDate(date):
            @classmethod
            def today(cls) -> "EarlyDate":
                return cls(2000, 1, 1)

        class LateDate(date):
            @classmethod
            def today(cls) -> "LateDate":
                return cls(2099, 12, 31)

        race_input = RacePredictionInput(
            horse_past_races={
                1: [
                    PastRace(
                        horse_id=1,
                        race_date="2026-08-01",
                        place="東京",
                        race_name="Test",
                        race_class="G1",
                        distance=1600,
                        track="芝",
                        weather="晴",
                        track_condition="良",
                        finish=1,
                        margin=0.1,
                        time="1:32.0",
                        weight=480.0,
                        weight_diff=0.0,
                        jockey="騎手",
                        popularity=1,
                        odds=2.0,
                    )
                ]
            },
            jockey_names_by_horse={1: "騎手"},
            track_conditions=RaceTrackConditions("東京", 1600, "芝", "良"),
            odds_by_horse={1: 2.0},
            race_horse_count=1,
            race_id=10,
            prediction_time="2026-08-05T12:00:00+09:00",
        )
        strategy_config = StrategyConfig(allowed_bet_types=frozenset())

        def run_with(fake_date: type[date]):
            with (
                patch("scripts.prediction.ability_engine.date", fake_date),
                patch("scripts.prediction.jockey_engine.date", fake_date),
                patch("scripts.prediction.track_engine.date", fake_date),
            ):
                pipeline = build_historical_prediction_pipeline(
                    target_race_date=date(2026, 8, 5),
                    strategy_config=strategy_config,
                )
                return pipeline.run(race_input)

        self.assertEqual(run_with(EarlyDate), run_with(LateDate))

        source = inspect.getsource(build_historical_prediction_pipeline)
        self.assertNotIn("date.today", source)
        self.assertNotIn("datetime.now", source)
        self.assertNotIn("PipelineConfig()", source)
        self.assertNotIn("PredictionPipeline()", source)


if __name__ == "__main__":
    unittest.main()
