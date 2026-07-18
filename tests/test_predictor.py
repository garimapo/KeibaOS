"""Predictorの総合評価統合テスト。"""

from __future__ import annotations

import math
import unittest

from scripts.prediction.ability_engine import AbilityEvaluation
from scripts.prediction.jockey_engine import JockeyEvaluation
from scripts.prediction.pace_engine import PaceEvaluation
from scripts.prediction.predictor import HorseEvaluationResults, Predictor
from scripts.prediction.track_engine import TrackEvaluation


def ability(score: float, race_count: int = 1) -> AbilityEvaluation:
    """テスト用能力評価を生成する。"""

    return AbilityEvaluation(score, race_count, "2026-07-17")


def jockey(score: float, race_count: int = 1) -> JockeyEvaluation:
    """テスト用騎手評価を生成する。"""

    return JockeyEvaluation("騎手", race_count, 0.0, 0.0, 0.0, 50.0, score)


def track(horse_id: int, score: float) -> TrackEvaluation:
    """テスト用コース適性評価を生成する。"""

    return TrackEvaluation(horse_id, 1, 50.0, 50.0, 50.0, 50.0, score)


class PredictorTest(unittest.TestCase):
    """各エンジン評価を総合スコアへ統合する処理を検証する。"""

    def setUp(self) -> None:
        self.predictor = Predictor()
        self.pace = PaceEvaluation("ハイ", {1: "差し", 2: "逃げ"}, 1, 2)

    def test_integrates_evaluations_and_ranks_horses(self) -> None:
        """評価を重み付き統合し、スコア順に順位を付与する。"""

        predictions = self.predictor.predict(
            {
                1: HorseEvaluationResults(ability(80.0), self.pace, jockey(70.0), track(1, 90.0)),
                2: HorseEvaluationResults(ability(70.0), self.pace, jockey(60.0), track(2, 80.0)),
            },
            race_id=10,
            prediction_time="2026-07-18T12:00:00",
        )

        self.assertEqual([prediction.horse_id for prediction in predictions], [1, 2])
        self.assertEqual([prediction.rank for prediction in predictions], ["1", "2"])
        self.assertEqual(predictions[0].score, 80.0)
        self.assertEqual(predictions[0].race_id, 10)

    def test_missing_evaluations_are_neutral(self) -> None:
        """評価が欠損していても中立点で安全に予測できる。"""

        prediction = self.predictor.predict({1: HorseEvaluationResults()})[0]

        self.assertEqual(prediction.score, 50.0)
        self.assertEqual(prediction.rank, "1")

    def test_empty_engine_results_are_neutral(self) -> None:
        """実績件数0の能力・騎手評価は中立点として扱う。"""

        prediction = self.predictor.predict(
            {
                1: HorseEvaluationResults(
                    ability(0.0, race_count=0),
                    None,
                    jockey(0.0, race_count=0),
                    track(1, 50.0),
                )
            }
        )[0]

        self.assertEqual(prediction.score, 50.0)

    def test_non_finite_and_out_of_range_scores_are_safe(self) -> None:
        """NaN・inf・異常値が最終スコアを非有限値にしない。"""

        prediction = self.predictor.predict(
            {
                1: HorseEvaluationResults(
                    ability(float("nan")),
                    self.pace,
                    jockey(float("inf")),
                    track(1, -100.0),
                )
            }
        )[0]

        self.assertTrue(math.isfinite(prediction.score))
        self.assertGreaterEqual(prediction.score, 0.0)
        self.assertLessEqual(prediction.score, 100.0)
        self.assertEqual(prediction.score, 46.0)

    def test_unknown_pace_style_is_neutral(self) -> None:
        """脚質が取得できない馬の展開評価は中立点となる。"""

        prediction = self.predictor.predict(
            {3: HorseEvaluationResults(ability(50.0), self.pace, jockey(50.0), track(3, 50.0))}
        )[0]

        self.assertEqual(prediction.score, 50.0)


if __name__ == "__main__":
    unittest.main()
