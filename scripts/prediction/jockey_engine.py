"""騎手の過去成績から騎手評価を算出するモジュール。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import math
from typing import Sequence

from scripts.models import PastRace


@dataclass(frozen=True)
class JockeyEvaluation:
    """騎手の過去成績に基づく評価結果。"""

    jockey_name: str
    race_count: int
    win_rate: float
    quinella_rate: float
    show_rate: float
    recent_score: float
    score: float


class JockeyEngine:
    """勝率・連対率・複勝率・直近成績から騎手スコアを算出する。"""

    WIN_RATE_WEIGHT = 0.35
    QUINELLA_RATE_WEIGHT = 0.25
    SHOW_RATE_WEIGHT = 0.20
    RECENT_SCORE_WEIGHT = 0.20

    NEUTRAL_SCORE = 50.0
    SAMPLE_SIZE_FOR_CONFIDENCE = 10
    RECENT_RACE_LIMIT = 5

    def __init__(self, reference_date: date | None = None) -> None:
        """騎手評価エンジンを初期化する。

        Args:
            reference_date: 未来日付を除外するための基準日。省略時は当日。
        """

        self.reference_date = reference_date or date.today()

    def evaluate(
        self,
        jockey_name: str,
        past_races: Sequence[PastRace],
    ) -> JockeyEvaluation:
        """指定騎手の有効な過去走を集計して評価を返す。

        騎手名不一致、未来日付、不正な着順のレースは評価対象から除外する。
        """

        normalized_name = self._normalize_name(jockey_name)

        if not normalized_name:
            return self._empty_evaluation(jockey_name)

        eligible_races = [
            past_race
            for past_race in past_races
            if self._is_eligible_race(past_race, normalized_name)
        ]

        if not eligible_races:
            return self._empty_evaluation(jockey_name)

        race_count = len(eligible_races)
        win_rate = self._rate(eligible_races, max_finish=1)
        quinella_rate = self._rate(eligible_races, max_finish=2)
        show_rate = self._rate(eligible_races, max_finish=3)
        recent_score = self._recent_score(eligible_races)
        raw_score = (
            win_rate * 100.0 * self.WIN_RATE_WEIGHT
            + quinella_rate * 100.0 * self.QUINELLA_RATE_WEIGHT
            + show_rate * 100.0 * self.SHOW_RATE_WEIGHT
            + recent_score * self.RECENT_SCORE_WEIGHT
        )

        return JockeyEvaluation(
            jockey_name=jockey_name,
            race_count=race_count,
            win_rate=round(win_rate, 4),
            quinella_rate=round(quinella_rate, 4),
            show_rate=round(show_rate, 4),
            recent_score=round(recent_score, 2),
            score=round(self._apply_sample_adjustment(raw_score, race_count), 2),
        )

    def _is_eligible_race(
        self,
        past_race: PastRace,
        jockey_name: str,
    ) -> bool:
        """騎手名・着順・日付が評価に利用できるか判定する。"""

        race_date = self._parse_date(past_race.race_date)

        return (
            self._normalize_name(past_race.jockey) == jockey_name
            and self._is_valid_finish(past_race.finish)
            and (race_date is None or race_date <= self.reference_date)
        )

    @staticmethod
    def _rate(
        past_races: Sequence[PastRace],
        max_finish: int,
    ) -> float:
        """指定着順以内の割合を0.0〜1.0で返す。"""

        return sum(race.finish <= max_finish for race in past_races) / len(past_races)

    def _recent_score(self, past_races: Sequence[PastRace]) -> float:
        """新しい最大5走の着順を重み付き平均して直近成績を算出する。"""

        sorted_races = sorted(
            past_races,
            key=lambda race: self._parse_date(race.race_date) or date.min,
            reverse=True,
        )[:self.RECENT_RACE_LIMIT]
        weights = range(len(sorted_races), 0, -1)
        total_weight = sum(weights)

        return sum(
            self._finish_score(race.finish) * weight
            for race, weight in zip(sorted_races, weights)
        ) / total_weight

    def _apply_sample_adjustment(self, raw_score: float, race_count: int) -> float:
        """少数サンプルのスコアを中立値へ縮小し、0〜100に収める。"""

        confidence = race_count / (race_count + self.SAMPLE_SIZE_FOR_CONFIDENCE)
        adjusted_score = (
            self.NEUTRAL_SCORE
            + (self._clamp_score(raw_score) - self.NEUTRAL_SCORE) * confidence
        )

        return self._clamp_score(adjusted_score)

    @staticmethod
    def _finish_score(finish: int) -> float:
        """着順を0〜100点の直近成績用スコアへ変換する。"""

        return max(0.0, 100.0 - (finish - 1) * 15.0)

    @staticmethod
    def _normalize_name(value: str) -> str:
        """騎手名の前後空白を除去する。不正値は空文字として扱う。"""

        return value.strip() if isinstance(value, str) else ""

    @staticmethod
    def _is_valid_finish(value: object) -> bool:
        """着順が正の有限整数か判定する。"""

        return (
            isinstance(value, (int, float))
            and math.isfinite(value)
            and value > 0
            and float(value).is_integer()
        )

    @staticmethod
    def _parse_date(value: str) -> date | None:
        """日付を解析し、不正値はNoneとして扱う。"""

        try:
            return date.fromisoformat(value.replace("/", "-"))
        except (AttributeError, TypeError, ValueError):
            return None

    @staticmethod
    def _clamp_score(value: float) -> float:
        """非有限値を排除し、スコアを0〜100に制限する。"""

        if not math.isfinite(value):
            return 0.0

        return min(100.0, max(0.0, value))

    @classmethod
    def _empty_evaluation(cls, jockey_name: str) -> JockeyEvaluation:
        """有効データがない場合のゼロ評価を返す。"""

        return JockeyEvaluation(
            jockey_name=jockey_name,
            race_count=0,
            win_rate=0.0,
            quinella_rate=0.0,
            show_rate=0.0,
            recent_score=0.0,
            score=0.0,
        )
