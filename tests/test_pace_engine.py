"""PaceEngineの脚質・ペース判定テスト。"""

from __future__ import annotations

import unittest

from scripts.models import PastRace
from scripts.prediction.pace_engine import PaceEngine


def make_race(
    *,
    passing_order: str = "",
    fourth_corner_position: int = 0,
) -> PastRace:
    """通過順位を指定したテスト用過去走を生成する。"""

    return PastRace(
        horse_id=1,
        race_date="2026-07-01",
        place="Tokyo",
        race_name="Test Race",
        race_class="A1",
        distance=1600,
        track="dirt",
        weather="sunny",
        track_condition="good",
        finish=1,
        margin=1.0,
        time="1:36.0",
        weight=480.0,
        weight_diff=0.0,
        jockey="Jockey",
        popularity=1,
        odds=2.0,
        passing_order=passing_order,
        fourth_corner_position=fourth_corner_position,
    )


class PaceEngineTest(unittest.TestCase):
    """4角位置からの脚質とペース判定を検証する。"""

    def setUp(self) -> None:
        self.engine = PaceEngine()

    def test_estimates_all_running_styles(self) -> None:
        """4角位置の中央値から4種類の脚質を推定できる。"""

        evaluation = self.engine.evaluate(
            {
                1: [make_race(fourth_corner_position=2)],
                2: [make_race(fourth_corner_position=5)],
                3: [make_race(fourth_corner_position=9)],
                4: [make_race(fourth_corner_position=10)],
            }
        )

        self.assertEqual(
            evaluation.running_styles,
            {1: "逃げ", 2: "先行", 3: "差し", 4: "追込"},
        )

    def test_uses_passing_order_when_corner_position_is_missing(self) -> None:
        """4角位置がない場合は通過順位の最後の値を使用する。"""

        evaluation = self.engine.evaluate(
            {1: [make_race(passing_order="3-3-2-1")]}
        )

        self.assertEqual(evaluation.running_styles[1], "逃げ")

    def test_ignores_trailing_numbers_in_passing_order(self) -> None:
        """頭数などの補足数値ではなく、通過順位列の4角を使う。"""

        evaluation = self.engine.evaluate(
            {1: [make_race(passing_order="3-3-2-1 (16頭)")]}
        )

        self.assertEqual(evaluation.running_styles[1], "逃げ")

    def test_predicts_high_pace_for_multiple_leaders(self) -> None:
        """逃げ馬が複数いればハイペースと判定する。"""

        evaluation = self.engine.evaluate(
            {
                1: [make_race(fourth_corner_position=1)],
                2: [make_race(fourth_corner_position=2)],
                3: [make_race(fourth_corner_position=5)],
            }
        )

        self.assertEqual(evaluation.race_pace, "ハイ")
        self.assertEqual(evaluation.leader_count, 2)

    def test_predicts_slow_pace_without_front_runners(self) -> None:
        """逃げ・先行がいなければスローペースと判定する。"""

        evaluation = self.engine.evaluate(
            {
                1: [make_race(fourth_corner_position=7)],
                2: [make_race(fourth_corner_position=11)],
            }
        )

        self.assertEqual(evaluation.race_pace, "スロー")

    def test_skips_horses_without_position_data(self) -> None:
        """位置情報がない馬は脚質推定対象から除外する。"""

        evaluation = self.engine.evaluate({1: [make_race()]})

        self.assertEqual(evaluation.running_styles, {})
        self.assertEqual(evaluation.evaluated_horse_count, 0)
        self.assertEqual(evaluation.race_pace, "平均")


if __name__ == "__main__":
    unittest.main()
