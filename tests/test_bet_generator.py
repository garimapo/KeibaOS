"""BetGeneratorの単体テスト。"""

from __future__ import annotations

import unittest

from scripts.models import Prediction
from scripts.prediction.bet_generator import BetGenerator
from scripts.prediction.value_engine import ValueEvaluation


def value(horse_id: int, probability: float, expected_value: float) -> ValueEvaluation:
    """テスト用の価値評価を作成する。"""

    return ValueEvaluation(horse_id, probability, 3.0, expected_value, 50.0)


def prediction(horse_id: int, score: float) -> Prediction:
    """テスト用の総合予測を作成する。"""

    return Prediction(1, "", "", score, False, "", horse_id)


class BetGeneratorTest(unittest.TestCase):
    """券種候補の生成規則を検証する。"""

    def setUp(self) -> None:
        self.generator = BetGenerator()

    def test_generates_all_supported_bet_types_with_ranks(self) -> None:
        recommendations = self.generator.generate(
            [value(1, 0.5, 2.0), value(2, 0.3, 1.5), value(3, 0.2, 1.2)],
            [prediction(1, 90.0), prediction(2, 80.0), prediction(3, 70.0)],
            3,
        )

        self.assertEqual(
            {item.bet_type for item in recommendations},
            {"単勝", "馬連", "ワイド", "3連複"},
        )
        self.assertEqual([item.rank for item in recommendations], list(range(1, len(recommendations) + 1)))
        self.assertTrue(all(item.expected_value is None for item in recommendations if len(item.horse_ids) > 1))
        self.assertTrue(all(item.combination_score is not None for item in recommendations if len(item.horse_ids) > 1))

    def test_combinations_are_unique_and_never_repeat_a_horse(self) -> None:
        recommendations = self.generator.generate(
            [value(1, 0.4, 2.0), value(2, 0.35, 1.8), value(3, 0.25, 1.2)],
            [prediction(1, 90.0), prediction(2, 80.0), prediction(3, 70.0)],
            3,
        )

        combinations = [item for item in recommendations if len(item.horse_ids) > 1]
        self.assertTrue(all(len(item.horse_ids) == len(set(item.horse_ids)) for item in combinations))
        self.assertEqual(
            len({(item.bet_type, item.horse_ids) for item in combinations}),
            len(combinations),
        )

    def test_empty_and_insufficient_inputs_return_no_candidates(self) -> None:
        self.assertEqual(self.generator.generate([], [], 0), [])
        recommendations = self.generator.generate(
            [value(1, 1.0, 2.0)], [prediction(1, 80.0)], 1
        )
        self.assertEqual([item.bet_type for item in recommendations], ["単勝"])

    def test_all_horses_are_candidates_regardless_of_expected_value(self) -> None:
        recommendations = self.generator.generate(
            [value(1, 1.0, 0.99)], [prediction(1, 80.0)], 1
        )
        self.assertEqual(len(recommendations), 1)
        self.assertEqual(recommendations[0].horse_ids, (1,))

    def test_all_eligible_horses_are_used_without_fixed_candidate_limit(self) -> None:
        evaluations = [value(horse_id, 0.1, 1.0) for horse_id in range(1, 7)]
        predictions = [prediction(horse_id, 50.0) for horse_id in range(1, 7)]

        recommendations = self.generator.generate(evaluations, predictions, 6)

        self.assertEqual(len([item for item in recommendations if item.bet_type == "単勝"]), 6)
        self.assertEqual(len([item for item in recommendations if item.bet_type == "馬連"]), 15)
        self.assertEqual(len([item for item in recommendations if item.bet_type == "ワイド"]), 15)
        self.assertEqual(len([item for item in recommendations if item.bet_type == "3連複"]), 20)

    def test_duplicate_horse_id_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.generator.generate(
                [value(1, 0.5, 2.0), value(1, 0.5, 1.5)],
                [prediction(1, 80.0)],
                2,
            )
        with self.assertRaises(ValueError):
            self.generator.generate(
                [value(1, 1.0, 2.0)],
                [prediction(1, 80.0), prediction(1, 70.0)],
                2,
            )

    def test_non_finite_values_are_safe(self) -> None:
        recommendations = self.generator.generate(
            [value(1, float("inf"), float("inf")), value(2, float("nan"), 2.0)],
            [prediction(1, float("inf")), prediction(2, float("nan"))],
            2,
        )
        self.assertTrue(all(item.estimated_probability <= 1.0 for item in recommendations))
        self.assertTrue(
            all(
                item.expected_value is None or item.expected_value >= 0.0
                for item in recommendations
            )
        )
        self.assertTrue(
            all(
                item.combination_score is None or item.combination_score >= 0.0
                for item in recommendations
            )
        )


if __name__ == "__main__":
    unittest.main()
