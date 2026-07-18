"""RuleBasedBetStrategyの単体テスト。"""

from __future__ import annotations

import unittest

from scripts.prediction.bet_generator import BetRecommendation
from scripts.prediction.bet_strategy import (
    RuleBasedBetStrategy,
    SelectionStyle,
    SortCondition,
    StrategyConfig,
)


def recommendation(
    rank: int,
    bet_type: str,
    horse_ids: tuple[int, ...],
    *,
    combination_score: float | None = None,
    prediction_score: float = 50.0,
    probability: float = 0.2,
) -> BetRecommendation:
    """テスト用候補を作成する。"""

    return BetRecommendation(
        rank=rank,
        bet_type=bet_type,
        horse_ids=horse_ids,
        estimated_probability=probability,
        expected_value=1.2 if bet_type == "単勝" else None,
        combination_score=combination_score,
        prediction_score=prediction_score,
    )


class RuleBasedBetStrategyTest(unittest.TestCase):
    """候補の抽出・優先順位付けを検証する。"""

    def setUp(self) -> None:
        self.strategy = RuleBasedBetStrategy()

    def test_empty_input_returns_empty_plan(self) -> None:
        plan = self.strategy.create_plan([], StrategyConfig())
        self.assertEqual(plan.recommendations, ())
        self.assertEqual(plan.candidate_count, 0)

    def test_filters_bet_type_and_combination_score(self) -> None:
        plan = self.strategy.create_plan(
            [
                recommendation(1, "単勝", (1,)),
                recommendation(2, "馬連", (1, 2), combination_score=1.1),
                recommendation(3, "ワイド", (1, 3), combination_score=0.9),
            ],
            StrategyConfig(
                allowed_bet_types=frozenset({"単勝", "馬連", "ワイド"}),
                min_combination_score=1.0,
            ),
        )
        self.assertEqual([item.bet_type for item in plan.recommendations], ["単勝", "馬連"])

    def test_maximums_apply_after_filtering_and_deduplication(self) -> None:
        plan = self.strategy.create_plan(
            [
                recommendation(2, "単勝", (1,)),
                recommendation(1, "単勝", (1,)),
                recommendation(3, "単勝", (2,)),
                recommendation(4, "単勝", (3,)),
            ],
            StrategyConfig(max_candidates=2, max_bet_count=1),
        )
        self.assertEqual(plan.candidate_count, 2)
        self.assertEqual([item.horse_ids for item in plan.recommendations], [(1,)])

    def test_box_and_formation_styles_change_only_priority(self) -> None:
        recommendations = [
            recommendation(1, "単勝", (1,)),
            recommendation(2, "馬連", (1, 2), combination_score=1.2),
        ]
        box_plan = self.strategy.create_plan(
            recommendations,
            StrategyConfig(selection_style=SelectionStyle.BOX),
        )
        formation_plan = self.strategy.create_plan(
            recommendations,
            StrategyConfig(selection_style=SelectionStyle.FORMATION),
        )
        self.assertEqual(box_plan.recommendations[0].bet_type, "馬連")
        self.assertEqual(formation_plan.recommendations[0].bet_type, "単勝")
        self.assertEqual(set(box_plan.recommendations), set(formation_plan.recommendations))

    def test_sort_condition_is_configurable(self) -> None:
        plan = self.strategy.create_plan(
            [
                recommendation(2, "単勝", (1,), prediction_score=90.0),
                recommendation(1, "単勝", (2,), prediction_score=70.0),
            ],
            StrategyConfig(sort_condition=SortCondition.PREDICTION_SCORE),
        )
        self.assertEqual(plan.recommendations[0].horse_ids, (1,))

    def test_invalid_config_is_rejected(self) -> None:
        for config in (
            StrategyConfig(max_bet_count=-1),
            StrategyConfig(max_candidates=-1),
            StrategyConfig(min_combination_score=float("nan")),
        ):
            with self.subTest(config=config):
                with self.assertRaises(ValueError):
                    self.strategy.create_plan([], config)


if __name__ == "__main__":
    unittest.main()
