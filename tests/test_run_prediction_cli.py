"""run_prediction CLIのE2Eテスト。"""

from __future__ import annotations

import logging
import unittest

from scripts.models import Prediction
from scripts.cli.run_prediction import run
from scripts.prediction.ability_engine import AbilityEvaluation
from scripts.prediction.bet_generator import BetRecommendation
from scripts.prediction.bet_strategy import BetPlan
from scripts.prediction.jockey_engine import JockeyEvaluation
from scripts.prediction.pace_engine import PaceEvaluation
from scripts.prediction.prediction_pipeline import (
    PipelineExecutionError,
    PipelineResult,
    PipelineStage,
    RacePredictionInput,
)
from scripts.prediction.track_engine import RaceTrackConditions, TrackEvaluation
from scripts.prediction.value_engine import ValueEvaluation


class _Messages(logging.Handler):
    """表示ログを検証するためのメモリハンドラー。"""

    def __init__(self) -> None:
        super().__init__()
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(record.getMessage())


class _Provider:
    def load(self, race_id: int) -> RacePredictionInput:
        return RacePredictionInput(
            horse_past_races={},
            jockey_names_by_horse={},
            track_conditions=RaceTrackConditions("東京", 1600, "芝", "良"),
            odds_by_horse={},
            race_horse_count=1,
            race_id=race_id,
        )


class _Pipeline:
    def run(self, race_input: RacePredictionInput) -> PipelineResult:
        prediction = Prediction(race_input.race_id, "", "1", 80.0, False, "", 10)
        recommendation = BetRecommendation(1, "単勝", (10,), 0.6, 1.2, None, 80.0)
        return PipelineResult(
            ability_evaluations={10: AbilityEvaluation(60.0, 1, None)},
            pace_evaluation=PaceEvaluation("平均", {}, 0, 0),
            jockey_evaluations={10: JockeyEvaluation("騎手", 0, 0.0, 0.0, 0.0, 0.0, 0.0)},
            track_evaluations={10: TrackEvaluation(10, 0, 50.0, 50.0, 50.0, 50.0, 50.0)},
            predictions=(prediction,),
            value_evaluations=(ValueEvaluation(10, 0.6, 2.0, 1.2, 60.0),),
            recommendations=(recommendation,),
            bet_plan=BetPlan("stub", (recommendation,), 1),
        )


class _FailingPipeline:
    def run(self, race_input: RacePredictionInput) -> PipelineResult:
        raise PipelineExecutionError(PipelineStage.VALUE)


class RunPredictionCliTest(unittest.TestCase):
    """引数解析、パイプライン呼び出し、表示までをE2Eで検証する。"""

    def setUp(self) -> None:
        self.logger = logging.getLogger(f"test.run_prediction.{self.id()}")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
        self.messages = _Messages()
        self.logger.addHandler(self.messages)

    def test_displays_prediction_and_bet_plan_from_pipeline(self) -> None:
        status = run(
            ["123", "--max-bets", "3", "--style", "box"],
            provider=_Provider(),
            pipeline=_Pipeline(),  # type: ignore[arg-type]
            output_logger=self.logger,
        )

        self.assertEqual(status, 0)
        self.assertIn("総合スコア", self.messages.messages[0])
        self.assertIn("0.6000", self.messages.messages[0])
        self.assertIn("単勝 10", self.messages.messages[0])

    def test_displays_pipeline_stage_on_failure(self) -> None:
        status = run(
            ["123"],
            provider=_Provider(),
            pipeline=_FailingPipeline(),  # type: ignore[arg-type]
            output_logger=self.logger,
        )

        self.assertEqual(status, 1)
        self.assertIn("段階=value", self.messages.messages[0])


if __name__ == "__main__":
    unittest.main()
