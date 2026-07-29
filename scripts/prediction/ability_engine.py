"""過去走データから能力指数を算出するモジュール。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import math
from statistics import median
from typing import Sequence
import unicodedata

from scripts.prediction.input_contracts import PastRaceInput


@dataclass(frozen=True)
class AbilityEvaluation:
    """過去走に基づく能力評価結果。"""

    ability_index: float
    race_count: int
    latest_race_date: str | None


class AbilityEngine:
    """着順・人気・着差・距離・クラス・レース日から能力指数を算出する。

    騎手、馬場、展開による補正はこのエンジンの責務に含めない。
    新しいレースほど大きな重みを与える加重平均を採用する。
    """

    _FINISH_WEIGHT = 0.45
    _POPULARITY_WEIGHT = 0.15
    _MARGIN_WEIGHT = 0.15
    _CLASS_WEIGHT = 0.25

    def __init__(
        self,
        recency_half_life_days: int = 120,
        reference_date: date | None = None,
    ) -> None:
        """能力指数エンジンを初期化する。

        Args:
            recency_half_life_days: レース日の重みが半分になる日数。
            reference_date: 未来日付を判定する基準日。省略時は当日。
        """

        self.recency_half_life_days = max(1, recency_half_life_days)
        self.reference_date = reference_date or date.today()

    def evaluate(self, past_races: Sequence[PastRaceInput]) -> AbilityEvaluation:
        """過去走の加重平均から能力評価を返す。

        空の入力では、指数0.0・レース数0の評価を返す。
        """

        if not past_races:
            return AbilityEvaluation(0.0, 0, None)

        eligible_races = [
            (past_race, self._parse_date(past_race.race_date))
            for past_race in past_races
            if self._is_eligible_race(past_race)
        ]

        if not eligible_races:
            return AbilityEvaluation(0.0, 0, None)

        eligible_races = [
            (past_race, race_date)
            for past_race, race_date in eligible_races
            if race_date is None or race_date <= self.reference_date
        ]

        if not eligible_races:
            return AbilityEvaluation(0.0, 0, None)

        race_dates = [race_date for _, race_date in eligible_races]
        latest_date = max(
            (
                race_date
                for race_date in race_dates
                if race_date and race_date <= self.reference_date
            ),
            default=None,
        )
        typical_distance = self._typical_distance(
            [past_race for past_race, _ in eligible_races]
        )

        weighted_score = 0.0
        total_weight = 0.0

        for past_race, race_date in eligible_races:
            weight = (
                self._recency_weight(race_date, latest_date)
                * self._distance_weight(past_race.distance, typical_distance)
            )
            weighted_score += self._race_score(past_race) * weight
            total_weight += weight

        ability_index = weighted_score / total_weight if total_weight else 0.0

        return AbilityEvaluation(
            ability_index=round(self._clamp_score(ability_index), 2),
            race_count=len(eligible_races),
            latest_race_date=latest_date.isoformat() if latest_date else None,
        )

    def _race_score(self, past_race: PastRaceInput) -> float:
        """1走分の能力評価を各要素の加重平均で算出する。"""

        return (
            self._finish_score(past_race.finish) * self._FINISH_WEIGHT
            + self._popularity_score(past_race.popularity) * self._POPULARITY_WEIGHT
            + self._margin_score(past_race.margin) * self._MARGIN_WEIGHT
            + self._class_score(past_race.race_class) * self._CLASS_WEIGHT
        )

    @classmethod
    def _is_eligible_race(cls, past_race: PastRaceInput) -> bool:
        """評価4項目のうち少なくとも1項目が有効なレースか判定する。"""

        return any(
            (
                past_race.finish > 0,
                past_race.popularity > 0,
                cls._is_valid_margin(past_race.margin),
                cls._has_race_class(past_race.race_class),
            )
        )

    @staticmethod
    def _finish_score(finish: int) -> float:
        """着順を0〜100点へ変換する。着順不明は中立評価とする。"""

        if finish <= 0:
            return 50.0

        return max(0.0, 100.0 - (finish - 1) * 10.0)

    @staticmethod
    def _popularity_score(popularity: int) -> float:
        """人気を0〜100点へ変換する。人気不明は中立評価とする。"""

        if popularity <= 0:
            return 50.0

        return max(0.0, 100.0 - (popularity - 1) * 8.0)

    @staticmethod
    def _margin_score(margin: float) -> float:
        """正の着差が小さいほど高く評価し、不明値は中立評価にする。"""

        if not AbilityEngine._is_valid_margin(margin):
            return 50.0

        return max(0.0, 100.0 - margin * 20.0)

    @staticmethod
    def _is_valid_margin(margin: float) -> bool:
        """着差が評価可能な正の有限値か判定する。"""

        return math.isfinite(margin) and margin > 0

    @staticmethod
    def _has_race_class(race_class: str) -> bool:
        """クラス欄に空白以外の値があるか判定する。"""

        return isinstance(race_class, str) and bool(race_class.strip())

    @staticmethod
    def _typical_distance(past_races: Sequence[PastRaceInput]) -> float:
        """有効な過去走距離の中央値を代表距離として返す。"""

        distances = [race.distance for race in past_races if race.distance > 0]

        return float(median(distances)) if distances else 0.0

    @staticmethod
    def _distance_weight(distance: int, typical_distance: float) -> float:
        """代表距離に近いレースの信頼度を0.5〜1.0の重みで返す。"""

        if distance <= 0 or typical_distance <= 0:
            return 0.75

        return max(0.5, 1.0 - abs(distance - typical_distance) / 1000.0)

    @staticmethod
    def _class_score(race_class: str) -> float:
        """レースクラス表記を0〜100点へ変換する。未知の表記は中立評価。"""

        if not isinstance(race_class, str):
            return 50.0

        normalized = unicodedata.normalize("NFKC", race_class).upper().replace(" ", "")

        if "G1" in normalized or "JPN1" in normalized:
            return 100.0
        if "G2" in normalized or "JPN2" in normalized:
            return 95.0
        if "G3" in normalized or "JPN3" in normalized:
            return 90.0
        if "OP" in normalized or "オープン" in normalized:
            return 85.0
        if normalized.startswith("A") or "3勝" in normalized:
            return 80.0
        if normalized.startswith("B") or "2勝" in normalized:
            return 70.0
        if normalized.startswith("C") or "1勝" in normalized:
            return 60.0
        if "未勝利" in normalized or "新馬" in normalized:
            return 50.0

        return 50.0

    def _recency_weight(
        self,
        race_date: date | None,
        latest_date: date | None,
    ) -> float:
        """最新レースからの日数差を指数減衰させた重みを返す。"""

        if (
            race_date is None
            or latest_date is None
            or race_date > self.reference_date
        ):
            return 0.25

        elapsed_days = max(0, (latest_date - race_date).days)

        return 0.5 ** (elapsed_days / self.recency_half_life_days)

    @staticmethod
    def _parse_date(value: str) -> date | None:
        """ISO形式の日付を解析し、解析できない値はNoneとして扱う。"""

        try:
            return date.fromisoformat(value.replace("/", "-"))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _clamp_score(value: float) -> float:
        """非有限値を排除し、能力指数を0〜100の範囲に収める。"""

        if not math.isfinite(value):
            return 0.0

        return min(100.0, max(0.0, value))
