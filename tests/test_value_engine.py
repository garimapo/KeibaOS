"""ValueEngineの単体テスト。"""

from __future__ import annotations

import math
import unittest

from scripts.models import Prediction
from scripts.prediction.value_engine import ValueEngine


def prediction(horse_id: int, score: object) -> Prediction:
    """テスト用Predictionを作成する。"""

    return Prediction(1, "", "", score, False, "", horse_id)  # type: ignore[arg-type]


class ValueEngineTest(unittest.TestCase):
    """暫定推定確率と推定期待値を検証する。"""

    def test_softmax_probabilities_sum_to_one_and_calculate_ev(self) -> None:
        """温度付きsoftmaxの出力と推定EVを検証する。"""

        engine = ValueEngine(temperature=10.0)
        evaluations = engine.evaluate(
            [prediction(1, 60.0), prediction(2, 40.0)], {1: 2.0, 2: 5.0}
        )

        self.assertAlmostEqual(
            sum(item.estimated_win_probability for item in evaluations), 1.0
        )
        self.assertAlmostEqual(evaluations[0].estimated_win_probability, 0.88079708)
        self.assertAlmostEqual(evaluations[1].estimated_win_probability, 0.11920292)
        self.assertAlmostEqual(evaluations[0].expected_value, 1.76159416)
        self.assertAlmostEqual(evaluations[1].expected_value, 0.5960146)

    def test_empty_input_returns_empty_list(self) -> None:
        self.assertEqual(ValueEngine().evaluate([], {}), [])

    def test_one_horse_is_assigned_probability_one(self) -> None:
        evaluation = ValueEngine().evaluate([prediction(1, 50.0)], {1: 2.0})[0]
        self.assertEqual(evaluation.estimated_win_probability, 1.0)
        self.assertEqual(evaluation.expected_value, 2.0)

    def test_equal_scores_fall_back_to_uniform_probability(self) -> None:
        evaluations = ValueEngine().evaluate(
            [prediction(1, 10.0), prediction(2, 10.0), prediction(3, 10.0)], {}
        )
        self.assertTrue(
            all(item.estimated_win_probability == 1.0 / 3.0 for item in evaluations)
        )

    def test_extreme_score_gap_is_finite_and_favors_higher_score(self) -> None:
        evaluations = ValueEngine(temperature=0.1).evaluate(
            [prediction(1, 1_000_000.0), prediction(2, 0.0)], {1: 2.0, 2: 2.0}
        )
        self.assertEqual(evaluations[0].estimated_win_probability, 1.0)
        self.assertEqual(evaluations[1].estimated_win_probability, 0.0)

    def test_invalid_temperature_is_rejected(self) -> None:
        for temperature in (0.0, -1.0, float("nan"), float("inf")):
            with self.subTest(temperature=temperature):
                with self.assertRaises(ValueError):
                    ValueEngine(temperature=temperature)

    def test_invalid_values_and_odds_are_safe(self) -> None:
        evaluations = ValueEngine().evaluate(
            [prediction(1, float("nan")), prediction(2, float("inf"))],
            {1: float("nan"), 2: float("inf")},
        )
        self.assertTrue(
            all(item.estimated_win_probability == 0.5 for item in evaluations)
        )
        for item in evaluations:
            self.assertEqual(item.odds, 0.0)
            self.assertEqual(item.expected_value, 0.0)
            self.assertEqual(item.value_score, 0.0)

    def test_duplicate_horse_id_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ValueEngine().evaluate([prediction(1, 10.0), prediction(1, 20.0)], {})

    def test_all_outputs_are_finite_and_value_score_is_bounded(self) -> None:
        evaluation = ValueEngine().evaluate(
            [prediction(1, float("inf")), prediction(2, 10.0)],
            {1: float("inf"), 2: 1_000_000.0},
        )
        for item in evaluation:
            self.assertTrue(math.isfinite(item.estimated_win_probability))
            self.assertTrue(math.isfinite(item.expected_value))
            self.assertTrue(math.isfinite(item.value_score))
            self.assertGreaterEqual(item.value_score, 0.0)
            self.assertLessEqual(item.value_score, 100.0)


if __name__ == "__main__":
    unittest.main()
