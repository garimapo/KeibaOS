"""AbilityEngineの境界値テスト。"""

from __future__ import annotations

from dataclasses import fields
from datetime import date
import math
from typing import get_type_hints
import unittest

from scripts.models import PastRace
from scripts.prediction.ability_engine import AbilityEngine, AbilityEvaluation
from scripts.simulation.models import PastRaceSnapshot


def make_race(
    *,
    race_date: str = "2026-07-17",
    finish: int = 1,
    popularity: int = 1,
    margin: float = 1.0,
    distance: int = 1600,
    race_class: str = "A1",
) -> PastRace:
    """テスト用PastRaceを生成する。"""

    return PastRace(
        horse_id=1,
        race_date=race_date,
        place="Tokyo",
        race_name="Test Race",
        race_class=race_class,
        distance=distance,
        track="dirt",
        weather="sunny",
        track_condition="good",
        finish=finish,
        margin=margin,
        time="1:36.0",
        weight=480.0,
        weight_diff=0.0,
        jockey="Jockey",
        popularity=popularity,
        odds=2.0,
    )


class AbilityEngineTest(unittest.TestCase):
    """能力指数の値域・境界値を検証する。"""

    def setUp(self) -> None:
        self.engine = AbilityEngine(
            recency_half_life_days=120,
            reference_date=date(2026, 7, 17),
        )

    def test_past_race_fields_match_engine_inputs(self) -> None:
        """エンジンが参照するPastRaceフィールドが実モデルに存在する。"""

        self.assertEqual(
            [field.name for field in fields(AbilityEvaluation)],
            ["ability_index", "race_count", "latest_race_date"],
        )
        self.assertEqual(
            get_type_hints(AbilityEvaluation),
            {
                "ability_index": float,
                "race_count": int,
                "latest_race_date": str | None,
            },
        )
        self.assertEqual(
            get_type_hints(PastRace),
            {
                "horse_id": int,
                "race_date": str,
                "place": str,
                "race_name": str,
                "race_class": str,
                "distance": int,
                "track": str,
                "weather": str,
                "track_condition": str,
                "finish": int,
                "margin": float,
                "time": str,
                "weight": float,
                "weight_diff": float,
                "jockey": str,
                "popularity": int,
                "odds": float,
                "passing_order": str,
                "fourth_corner_position": int,
            },
        )

    def test_empty_and_all_missing_inputs_are_excluded(self) -> None:
        """空入力と全項目欠損は能力計算の対象にならない。"""

        self.assertEqual(self.engine.evaluate([]), AbilityEvaluation(0.0, 0, None))

        missing = make_race(
            race_date="invalid",
            finish=0,
            popularity=0,
            margin=0.0,
            distance=0,
            race_class="",
        )
        evaluation = self.engine.evaluate([missing])

        self.assertEqual(evaluation.ability_index, 0.0)
        self.assertEqual(evaluation.race_count, 0)
        self.assertIsNone(evaluation.latest_race_date)

    def test_missing_race_is_excluded_from_mixed_input(self) -> None:
        """全項目欠損のレースは正常レースと混在しても除外される。"""

        valid = make_race(margin=1.0)
        missing = make_race(
            race_date="invalid",
            finish=0,
            popularity=0,
            margin=0.0,
            distance=0,
            race_class="",
        )

        self.assertEqual(
            self.engine.evaluate([valid, missing]),
            self.engine.evaluate([valid]),
        )

    def test_partial_missing_values_are_eligible(self) -> None:
        """一部の評価項目が欠損していても、有効項目があれば計算する。"""

        partial = make_race(
            finish=1,
            popularity=0,
            margin=0.0,
            distance=0,
            race_class="",
        )
        evaluation = self.engine.evaluate([partial])

        self.assertEqual(evaluation.race_count, 1)
        self.assertGreater(evaluation.ability_index, 50.0)

    def test_each_retained_component_independently_makes_a_race_eligible(self) -> None:
        """着順・人気・クラスはそれぞれ単独で評価対象を成立させる。"""

        cases = (
            make_race(finish=1, popularity=0, race_class="", margin=0.0),
            make_race(finish=0, popularity=1, race_class="", margin=0.0),
            make_race(finish=0, popularity=0, race_class="G1", margin=0.0),
        )

        for race in cases:
            with self.subTest(race=race):
                self.assertEqual(self.engine.evaluate([race]).race_count, 1)

    def test_date_only_race_is_excluded(self) -> None:
        """日付以外の評価項目が全欠損なら計算対象外となる。"""

        date_only = make_race(
            finish=0,
            popularity=0,
            margin=0.0,
            distance=1600,
            race_class="",
        )
        evaluation = self.engine.evaluate([date_only])

        self.assertEqual(evaluation, AbilityEvaluation(0.0, 0, None))

    def test_distance_and_legacy_margin_alone_do_not_make_a_race_eligible(self) -> None:
        """距離・日付・legacy着差だけのレースは評価対象外となる。"""

        race = make_race(
            finish=0,
            popularity=0,
            margin=0.1,
            distance=3200,
            race_class="",
        )

        self.assertEqual(self.engine.evaluate([race]), AbilityEvaluation(0.0, 0, None))

    def test_all_future_dates_are_excluded(self) -> None:
        """全レースが未来日付なら能力計算の対象外となる。"""

        future_good = make_race(race_date="2026-08-01", margin=1.0)
        evaluation = self.engine.evaluate([future_good])

        self.assertEqual(evaluation, AbilityEvaluation(0.0, 0, None))

    def test_same_date_uses_equal_recency_weight(self) -> None:
        """同一日付のレースは順位によらず同じ日時重みを使う。"""

        good = make_race(margin=1.0)
        poor = make_race(finish=10, popularity=10, margin=5.0, race_class="C1")

        expected = (
            self.engine.evaluate([good]).ability_index
            + self.engine.evaluate([poor]).ability_index
        ) / 2

        self.assertEqual(self.engine.evaluate([good, poor]).ability_index, expected)

    def test_legacy_margin_values_have_no_effect(self) -> None:
        """legacy着差の値だけを変えても正式な能力指数は変化しない。"""

        expected = self.engine.evaluate([make_race(margin=0.1)])
        for margin in (1_000_000.0, float("nan"), float("inf"), float("-inf")):
            evaluation = self.engine.evaluate([make_race(margin=margin)])

            self.assertEqual(evaluation, expected)
            self.assertTrue(math.isfinite(evaluation.ability_index))
            self.assertGreaterEqual(evaluation.ability_index, 0.0)
            self.assertLessEqual(evaluation.ability_index, 100.0)

    def test_marginless_structural_input_is_accepted(self) -> None:
        """正式な入力はmargin属性を持たなくても能力評価できる。"""

        race = PastRaceSnapshot.from_past_race(make_race())

        self.assertFalse(hasattr(race, "margin"))
        self.assertEqual(self.engine.evaluate([race]).race_count, 1)

    def test_component_weights_are_exactly_nine_three_five(self) -> None:
        """着順・人気・クラスの正規化比率を9:3:5で固定する。"""

        self.assertEqual(
            (
                AbilityEngine._FINISH_WEIGHT,
                AbilityEngine._POPULARITY_WEIGHT,
                AbilityEngine._CLASS_WEIGHT,
                AbilityEngine._COMPONENT_WEIGHT_TOTAL,
            ),
            (9, 3, 5, 17),
        )
        cases = (
            (make_race(finish=1, popularity=0, race_class="", margin=99.0), (100.0 * 9 + 50.0 * 3 + 50.0 * 5) / 17),
            (make_race(finish=0, popularity=1, race_class="", margin=0.0), (50.0 * 9 + 100.0 * 3 + 50.0 * 5) / 17),
            (make_race(finish=0, popularity=0, race_class="G1", margin=-99.0), (50.0 * 9 + 50.0 * 3 + 100.0 * 5) / 17),
        )
        for race, expected in cases:
            with self.subTest(race=race):
                self.assertEqual(
                    self.engine.evaluate([race]).ability_index,
                    round(expected, 2),
                )

    def test_margin_implementation_symbols_are_absent(self) -> None:
        """AbilityEngineに旧着差ロジックを残さない。"""

        self.assertFalse(hasattr(AbilityEngine, "_MARGIN_WEIGHT"))
        self.assertFalse(hasattr(AbilityEngine, "_margin_score"))
        self.assertFalse(hasattr(AbilityEngine, "_is_valid_margin"))

    def test_zero_values_are_neutral_when_other_field_is_valid(self) -> None:
        """着順0・人気0・距離0でも、他項目が有効なら中立評価で計算する。"""

        evaluation = self.engine.evaluate(
            [make_race(finish=0, popularity=0, margin=0.0, distance=0, race_class="A1")]
        )

        self.assertEqual(evaluation.race_count, 1)
        self.assertGreater(evaluation.ability_index, 50.0)

    def test_single_and_duplicate_races_have_consistent_index(self) -> None:
        """同一レースを複数与えても加重平均の指数は変わらない。"""

        race = make_race(margin=1.0)

        self.assertEqual(
            self.engine.evaluate([race]).ability_index,
            self.engine.evaluate([race, race]).ability_index,
        )

    def test_non_positive_half_life_is_corrected(self) -> None:
        """半減期0以下は安全な最小値1日へ補正される。"""

        self.assertEqual(AbilityEngine(0).recency_half_life_days, 1)
        self.assertEqual(AbilityEngine(-10).recency_half_life_days, 1)


if __name__ == "__main__":
    unittest.main()
