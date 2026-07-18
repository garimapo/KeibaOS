"""PredictionPipelineの単体テスト。"""

from __future__ import annotations

import unittest

from scripts.models import Prediction
from scripts.prediction.ability_engine import AbilityEvaluation
from scripts.prediction.bet_generator import BetRecommendation
from scripts.prediction.bet_strategy import BetPlan, StrategyConfig
from scripts.prediction.jockey_engine import JockeyEvaluation
from scripts.prediction.pace_engine import PaceEvaluation
from scripts.prediction.prediction_pipeline import (
    PipelineConfig,
    PipelineExecutionError,
    PipelineStage,
    PredictionPipeline,
    RacePredictionInput,
)
from scripts.prediction.track_engine import RaceTrackConditions, TrackEvaluation
from scripts.prediction.value_engine import ValueEvaluation


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


if __name__ == "__main__":
    unittest.main()
