"""JockeyEngineの集計・境界値テスト。"""

from __future__ import annotations

from datetime import date
import math
import unittest

from scripts.models import PastRace
from scripts.prediction.jockey_engine import JockeyEngine, JockeyEvaluation


def make_race(
    *,
    jockey: str = "騎手A",
    race_date: str = "2026-07-17",
    finish: object = 1,
) -> PastRace:
    """テスト用の過去走を生成する。"""

    return PastRace(
        horse_id=1,
        race_date=race_date,
        place="Tokyo",
        race_name="Test Race",
        race_class="A1",
        distance=1600,
        track="dirt",
        weather="sunny",
        track_condition="good",
        finish=finish,  # type: ignore[arg-type]
        margin=1.0,
        time="1:36.0",
        weight=480.0,
        weight_diff=0.0,
        jockey=jockey,
        popularity=1,
        odds=2.0,
    )


class JockeyEngineTest(unittest.TestCase):
    """騎手評価式と不正データの扱いを検証する。"""

    def setUp(self) -> None:
        self.engine = JockeyEngine(reference_date=date(2026, 7, 17))

    def test_calculates_rates_and_score(self) -> None:
        """勝率・連対率・複勝率を正しく集計する。"""

        evaluation = self.engine.evaluate(
            "騎手A",
            [
                make_race(finish=1),
                make_race(finish=2),
                make_race(finish=4),
                make_race(jockey="騎手B", finish=1),
            ],
        )

        self.assertEqual(evaluation.race_count, 3)
        self.assertEqual(evaluation.win_rate, 0.3333)
        self.assertEqual(evaluation.quinella_rate, 0.6667)
        self.assertEqual(evaluation.show_rate, 0.6667)
        self.assertGreaterEqual(evaluation.score, 0.0)
        self.assertLessEqual(evaluation.score, 100.0)

    def test_empty_and_missing_data_return_zero_evaluation(self) -> None:
        """空入力や不正着順だけの入力を安全にゼロ評価へする。"""

        expected = JockeyEvaluation("騎手A", 0, 0.0, 0.0, 0.0, 0.0, 0.0)

        self.assertEqual(self.engine.evaluate("騎手A", []), expected)
        self.assertEqual(self.engine.evaluate("騎手A", [make_race(finish=0)]), expected)

    def test_future_dates_are_excluded(self) -> None:
        """未来日付のレースは高成績でも評価対象にしない。"""

        evaluation = self.engine.evaluate(
            "騎手A",
            [make_race(race_date="2026-08-01", finish=1)],
        )

        self.assertEqual(evaluation.race_count, 0)
        self.assertEqual(evaluation.score, 0.0)

    def test_small_sample_is_shrunk_toward_neutral(self) -> None:
        """1走1着でも少数サンプルのスコアは過度に高くならない。"""

        evaluation = self.engine.evaluate("騎手A", [make_race(finish=1)])

        self.assertLess(evaluation.score, 60.0)
        self.assertGreater(evaluation.score, 50.0)

    def test_nan_and_infinite_finish_are_excluded(self) -> None:
        """NaN・infの着順を含んでも例外や非有限スコアを発生させない。"""

        evaluation = self.engine.evaluate(
            "騎手A",
            [make_race(finish=float("nan")), make_race(finish=float("inf"))],
        )

        self.assertEqual(evaluation.race_count, 0)
        self.assertTrue(math.isfinite(evaluation.score))
        self.assertEqual(evaluation.score, 0.0)

    def test_recent_results_prioritize_newer_races(self) -> None:
        """新しい好走が古い不振より直近成績へ強く反映される。"""

        evaluation = self.engine.evaluate(
            "騎手A",
            [
                make_race(race_date="2026-06-01", finish=10),
                make_race(race_date="2026-07-17", finish=1),
            ],
        )

        self.assertGreater(evaluation.recent_score, 50.0)


if __name__ == "__main__":
    unittest.main()
