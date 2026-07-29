"""競馬場・距離・馬場適性を評価するモジュール。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import math
import unicodedata
from typing import Mapping, Sequence

from scripts.prediction.input_contracts import PastRaceInput, RaceTrackConditionsInput


@dataclass(frozen=True)
class RaceTrackConditions:
    """適性評価の対象となるレース条件。"""

    place: str
    distance: int
    track: str
    track_condition: str


@dataclass(frozen=True)
class TrackEvaluation:
    """1頭分の競馬場・距離・馬場適性評価。"""

    horse_id: int
    race_count: int
    place_score: float
    distance_score: float
    track_score: float
    track_condition_score: float
    score: float


class TrackEngine:
    """対象レース条件と過去走を比較し、馬ごとの適性を評価する。"""

    PLACE_WEIGHT = 0.30
    DISTANCE_WEIGHT = 0.30
    TRACK_WEIGHT = 0.20
    TRACK_CONDITION_WEIGHT = 0.20

    NEUTRAL_SCORE = 50.0
    SAMPLE_SIZE_FOR_CONFIDENCE = 10
    MAX_DISTANCE_DIFFERENCE = 600.0

    def __init__(self, reference_date: date | None = None) -> None:
        """適性評価エンジンを初期化する。

        Args:
            reference_date: 未来日付の過去走を除外する基準日。省略時は当日。
        """

        self.reference_date = reference_date or date.today()

    def evaluate(
        self,
        target: RaceTrackConditionsInput,
        horse_past_races: Mapping[int, Sequence[PastRaceInput]],
    ) -> dict[int, TrackEvaluation]:
        """対象レースに対する馬ごとの適性評価を返す。"""

        return {
            horse_id: self._evaluate_horse(horse_id, target, past_races)
            for horse_id, past_races in horse_past_races.items()
        }

    def _evaluate_horse(
        self,
        horse_id: int,
        target: RaceTrackConditionsInput,
        past_races: Sequence[PastRaceInput],
    ) -> TrackEvaluation:
        """1頭分の有効過去走を集計して適性を評価する。"""

        eligible_races = [
            past_race
            for past_race in past_races
            if self._is_eligible_race(past_race)
        ]
        place_score = self._place_score(target.place, eligible_races)
        distance_score = self._distance_score(target.distance, eligible_races)
        track_score = self._track_score(target.track, eligible_races)
        track_condition_score = self._track_condition_score(
            target.track_condition,
            eligible_races,
        )
        score = (
            place_score * self.PLACE_WEIGHT
            + distance_score * self.DISTANCE_WEIGHT
            + track_score * self.TRACK_WEIGHT
            + track_condition_score * self.TRACK_CONDITION_WEIGHT
        )

        return TrackEvaluation(
            horse_id=horse_id,
            race_count=len(eligible_races),
            place_score=round(place_score, 2),
            distance_score=round(distance_score, 2),
            track_score=round(track_score, 2),
            track_condition_score=round(track_condition_score, 2),
            score=round(self._clamp_score(score), 2),
        )

    def _place_score(
        self,
        target_place: str,
        past_races: Sequence[PastRaceInput],
    ) -> float:
        """同一競馬場での基礎成績点を評価する。"""

        normalized_target = self._normalize_text(target_place)

        if not normalized_target:
            return self.NEUTRAL_SCORE

        values = [
            (self._base_performance_score(race.finish), 1.0)
            for race in past_races
            if self._normalize_text(race.place) == normalized_target
        ]

        return self._adjust_component_score(values)

    def _distance_score(
        self,
        target_distance: int,
        past_races: Sequence[PastRaceInput],
    ) -> float:
        """対象距離に近いレースの基礎成績点を距離差で重み付けする。"""

        if not self._is_valid_distance(target_distance):
            return self.NEUTRAL_SCORE

        values = [
            (
                self._base_performance_score(race.finish),
                1.0 - abs(race.distance - target_distance) / self.MAX_DISTANCE_DIFFERENCE,
            )
            for race in past_races
            if self._is_valid_distance(race.distance)
            and abs(race.distance - target_distance) < self.MAX_DISTANCE_DIFFERENCE
        ]

        return self._adjust_component_score(values)

    def _track_score(
        self,
        target_track: str,
        past_races: Sequence[PastRaceInput],
    ) -> float:
        """同じ芝・ダート等での基礎成績点を評価する。"""

        normalized_target = self._normalize_track(target_track)

        if not normalized_target:
            return self.NEUTRAL_SCORE

        values = [
            (self._base_performance_score(race.finish), 1.0)
            for race in past_races
            if self._normalize_track(race.track) == normalized_target
        ]

        return self._adjust_component_score(values)

    def _track_condition_score(
        self,
        target_condition: str,
        past_races: Sequence[PastRaceInput],
    ) -> float:
        """同じ馬場状態での基礎成績点を評価する。"""

        normalized_target = self._normalize_track_condition(target_condition)

        if not normalized_target:
            return self.NEUTRAL_SCORE

        values = [
            (self._base_performance_score(race.finish), 1.0)
            for race in past_races
            if self._normalize_track_condition(race.track_condition) == normalized_target
        ]

        return self._adjust_component_score(values)

    def _adjust_component_score(
        self,
        values: Sequence[tuple[float, float]],
    ) -> float:
        """項目ごとの実績を少数サンプル補正して0〜100へ収める。"""

        if not values:
            return self.NEUTRAL_SCORE

        total_weight = sum(weight for _, weight in values)

        if total_weight <= 0:
            return self.NEUTRAL_SCORE

        raw_score = sum(score * weight for score, weight in values) / total_weight
        confidence = total_weight / (total_weight + self.SAMPLE_SIZE_FOR_CONFIDENCE)

        return self._clamp_score(
            self.NEUTRAL_SCORE
            + (self._clamp_score(raw_score) - self.NEUTRAL_SCORE) * confidence
        )

    def _is_eligible_race(self, past_race: PastRaceInput) -> bool:
        """成績評価可能かつ未来日付でない過去走を対象として扱う。"""

        race_date = self._parse_date(past_race.race_date)

        return (
            self._is_valid_finish(past_race.finish)
            and (race_date is None or race_date <= self.reference_date)
        )

    @staticmethod
    def _base_performance_score(finish: int) -> float:
        """着順を0〜100点の基礎成績点に変換する。"""

        return max(0.0, 100.0 - (finish - 1) * 15.0)

    @staticmethod
    def _normalize_text(value: str) -> str:
        """全半角・前後空白を正規化し、不正値は空文字にする。"""

        if not isinstance(value, str):
            return ""

        return "".join(unicodedata.normalize("NFKC", value).split()).casefold()

    @classmethod
    def _normalize_track(cls, value: str) -> str:
        """芝・ダート等の表記ゆれを統一する。"""

        normalized = cls._normalize_text(value)

        if "ダ" in normalized or "dirt" in normalized:
            return "dirt"
        if "芝" in normalized or "turf" in normalized:
            return "turf"
        if "障" in normalized or "obstacle" in normalized:
            return "obstacle"

        return normalized

    @classmethod
    def _normalize_track_condition(cls, value: str) -> str:
        """馬場状態の日本語・英語表記を統一する。"""

        normalized = cls._normalize_text(value)
        aliases = {
            "良": "good",
            "good": "good",
            "稍重": "yielding",
            "yielding": "yielding",
            "重": "heavy",
            "heavy": "heavy",
            "不良": "sloppy",
            "sloppy": "sloppy",
        }

        return aliases.get(normalized, normalized)

    @staticmethod
    def _is_valid_distance(value: object) -> bool:
        """距離が正の有限値か判定する。"""

        return (
            isinstance(value, (int, float))
            and math.isfinite(value)
            and value > 0
        )

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
        """非有限値を排除し、スコアを0〜100へ制限する。"""

        if not math.isfinite(value):
            return 0.0

        return min(100.0, max(0.0, value))
