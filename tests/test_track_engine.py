"""TrackEngineの適性評価テスト。"""

from __future__ import annotations

from datetime import date
import math
import unittest

from scripts.models import PastRace
from scripts.prediction.track_engine import RaceTrackConditions, TrackEngine


TARGET = RaceTrackConditions("大井", 1600, "ダート", "良")


def make_race(
    *,
    place: str = "大井",
    distance: object = 1600,
    track: str = "dirt",
    track_condition: str = "good",
    race_date: str = "2026-07-17",
    finish: object = 1,
) -> PastRace:
    """テスト用の過去走を生成する。"""

    return PastRace(
        horse_id=1,
        race_date=race_date,
        place=place,
        race_name="Test Race",
        race_class="A1",
        distance=distance,  # type: ignore[arg-type]
        track=track,
        weather="sunny",
        track_condition=track_condition,
        finish=finish,  # type: ignore[arg-type]
        margin=1.0,
        time="1:36.0",
        weight=480.0,
        weight_diff=0.0,
        jockey="Jockey",
        popularity=1,
        odds=2.0,
    )


class TrackEngineTest(unittest.TestCase):
    """競馬場・距離・馬場適性と境界値を検証する。"""

    def setUp(self) -> None:
        self.engine = TrackEngine(reference_date=date(2026, 7, 17))

    def test_empty_history_returns_neutral_score(self) -> None:
        """過去走なしの馬は中立50点を返す。"""

        evaluation = self.engine.evaluate(TARGET, {1: []})[1]

        self.assertEqual(evaluation.race_count, 0)
        self.assertEqual(evaluation.score, 50.0)

    def test_normalizes_matching_conditions(self) -> None:
        """日本語・英語の表記ゆれを同一条件として扱う。"""

        evaluation = self.engine.evaluate(
            TARGET,
            {1: [make_race(place=" 大井 ", track="ダ", track_condition="良")]},
        )[1]

        self.assertGreater(evaluation.score, 50.0)
        self.assertLess(evaluation.score, 60.0)

    def test_many_matches_increase_score_without_exceeding_range(self) -> None:
        """十分な一致実績は高評価になるが100点を超えない。"""

        evaluation = self.engine.evaluate(
            TARGET,
            {1: [make_race() for _ in range(20)]},
        )[1]

        self.assertGreater(evaluation.score, 80.0)
        self.assertLessEqual(evaluation.score, 100.0)

    def test_no_matching_conditions_return_neutral_score(self) -> None:
        """条件一致実績がない項目は中立50点となる。"""

        evaluation = self.engine.evaluate(
            TARGET,
            {
                1: [
                    make_race(
                        place="浦和",
                        distance=2500,
                        track="turf",
                        track_condition="heavy",
                    )
                    for _ in range(20)
                ]
            },
        )[1]

        self.assertEqual(evaluation.place_score, 50.0)
        self.assertEqual(evaluation.distance_score, 50.0)
        self.assertEqual(evaluation.track_score, 50.0)
        self.assertEqual(evaluation.track_condition_score, 50.0)
        self.assertEqual(evaluation.score, 50.0)

    def test_poor_results_in_matching_conditions_are_not_highly_rated(self) -> None:
        """同条件での凡走だけでは高い適性点にならない。"""

        evaluation = self.engine.evaluate(
            TARGET,
            {1: [make_race(finish=10) for _ in range(10)]},
        )[1]

        self.assertLess(evaluation.score, 50.0)

    def test_good_results_outrank_poor_results_in_matching_conditions(self) -> None:
        """同条件での好走馬は凡走馬より高く評価される。"""

        good = self.engine.evaluate(
            TARGET,
            {1: [make_race(finish=1) for _ in range(10)]},
        )[1]
        poor = self.engine.evaluate(
            TARGET,
            {1: [make_race(finish=10) for _ in range(10)]},
        )[1]

        self.assertGreater(good.score, poor.score)

    def test_nearby_distance_with_poor_result_is_not_highly_rated(self) -> None:
        """距離が近くても凡走なら距離適性は高くならない。"""

        evaluation = self.engine.evaluate(
            TARGET,
            {1: [make_race(distance=1650, finish=10) for _ in range(10)]},
        )[1]

        self.assertLess(evaluation.distance_score, 50.0)

    def test_partial_condition_history_uses_neutral_for_missing_components(self) -> None:
        """一部条件だけ実績がある場合、他の項目は中立点として扱う。"""

        evaluation = self.engine.evaluate(
            TARGET,
            {
                1: [
                    make_race(
                        place="大井",
                        distance=2500,
                        track="turf",
                        track_condition="heavy",
                        finish=1,
                    )
                ]
            },
        )[1]

        self.assertGreater(evaluation.place_score, 50.0)
        self.assertEqual(evaluation.distance_score, 50.0)
        self.assertEqual(evaluation.track_score, 50.0)
        self.assertEqual(evaluation.track_condition_score, 50.0)

    def test_future_dates_are_excluded(self) -> None:
        """未来日付の一致実績は評価対象にしない。"""

        evaluation = self.engine.evaluate(
            TARGET,
            {1: [make_race(race_date="2026-08-01")]},
        )[1]

        self.assertEqual(evaluation.race_count, 0)
        self.assertEqual(evaluation.score, 50.0)

    def test_zero_and_non_finite_distances_are_safe(self) -> None:
        """距離0・NaN・infを含んでもスコアは有限範囲に収まる。"""

        for distance in (0, float("nan"), float("inf")):
            evaluation = self.engine.evaluate(TARGET, {1: [make_race(distance=distance)]})[1]

            self.assertTrue(math.isfinite(evaluation.score))
            self.assertGreaterEqual(evaluation.score, 0.0)
            self.assertLessEqual(evaluation.score, 100.0)

    def test_invalid_target_distance_is_neutral_component(self) -> None:
        """対象距離0は距離項目を中立点として扱う。"""

        target = RaceTrackConditions("大井", 0, "ダート", "良")
        evaluation = self.engine.evaluate(target, {1: [make_race()]})[1]

        self.assertEqual(evaluation.distance_score, 50.0)

    def test_invalid_finish_is_excluded(self) -> None:
        """着順不明・無効な過去走は成績評価へ使用しない。"""

        evaluation = self.engine.evaluate(TARGET, {1: [make_race(finish=0)]})[1]

        self.assertEqual(evaluation.race_count, 0)
        self.assertEqual(evaluation.score, 50.0)


if __name__ == "__main__":
    unittest.main()
