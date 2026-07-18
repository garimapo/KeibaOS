"""予測スコアと単勝オッズから暫定的な価値評価を作成する。"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Sequence

from scripts.models import Prediction


@dataclass(frozen=True)
class ValueEvaluation:
    """1頭分の単勝期待値評価。

    ``estimated_win_probability`` は予測スコアをsoftmax変換した校正前の
    暫定推定値であり、実績データで校正された勝率ではない。
    """

    horse_id: int
    estimated_win_probability: float
    odds: float
    expected_value: float
    value_score: float


class ValueEngine:
    """予測スコアを暫定確率へ変換し、単勝の推定期待値を評価する。"""

    DEFAULT_TEMPERATURE = 10.0
    VALUE_SCORE_EV_AT_MAX = 2.0

    def __init__(self, temperature: float = DEFAULT_TEMPERATURE) -> None:
        """温度係数を検証して初期化する。

        Args:
            temperature: softmaxの温度係数。正の有限値のみ許可する。

        Raises:
            ValueError: temperatureが正の有限値ではない場合。
        """

        if not self._is_positive_finite(temperature):
            raise ValueError("temperature must be a positive finite number")
        self.temperature = float(temperature)

    def evaluate(
        self,
        predictions: Sequence[Prediction],
        odds_by_horse: Mapping[int, float],
    ) -> list[ValueEvaluation]:
        """全馬の推定勝率と単勝の推定期待値を返す。

        推定勝率は、校正前の総合スコアを温度係数付きsoftmaxで正規化した
        暫定値である。推定期待値はこの暫定推定値と単勝オッズの積であり、
        実績に基づき校正された収益期待値を意味しない。

        同一horse_idを複数含む入力は、オッズとの対応が曖昧になるため拒否する。
        """

        if not predictions:
            return []

        horse_ids = [prediction.horse_id for prediction in predictions]
        if len(set(horse_ids)) != len(horse_ids):
            raise ValueError("predictions must not contain duplicate horse_id values")

        scores = [self._valid_score(prediction.score) for prediction in predictions]
        probabilities = self._softmax(scores)

        return [
            self._build_evaluation(
                prediction.horse_id,
                probability,
                odds_by_horse.get(prediction.horse_id),
            )
            for prediction, probability in zip(predictions, probabilities)
        ]

    def _softmax(self, scores: Sequence[float]) -> list[float]:
        """最大値を差し引いた安定化softmaxで暫定確率を計算する。"""

        if not scores:
            return []
        if len(set(scores)) == 1:
            return [1.0 / len(scores)] * len(scores)

        maximum = max(scores)
        weights = [math.exp((score - maximum) / self.temperature) for score in scores]
        total_weight = sum(weights)
        if not math.isfinite(total_weight) or total_weight <= 0:
            return [1.0 / len(scores)] * len(scores)
        return [weight / total_weight for weight in weights]

    def _build_evaluation(
        self,
        horse_id: int,
        estimated_win_probability: float,
        odds: object,
    ) -> ValueEvaluation:
        """安全なオッズを用いて1頭分の推定期待値評価を組み立てる。"""

        safe_odds = self._valid_odds(odds)
        expected_value = self._clamp_non_negative(
            estimated_win_probability * safe_odds
        )
        value_score = self._clamp_score(
            expected_value / self.VALUE_SCORE_EV_AT_MAX * 100.0
        )
        return ValueEvaluation(
            horse_id=horse_id,
            estimated_win_probability=estimated_win_probability,
            odds=safe_odds,
            expected_value=expected_value,
            value_score=value_score,
        )

    @staticmethod
    def _valid_score(value: object) -> float:
        """softmax入力に使える有限スコアへ正規化する。"""

        if not isinstance(value, (int, float)) or not math.isfinite(value):
            return 0.0
        return max(0.0, float(value))

    @staticmethod
    def _valid_odds(value: object) -> float:
        """正の有限オッズ以外を0.0として扱う。"""

        if not isinstance(value, (int, float)) or not math.isfinite(value):
            return 0.0
        return float(value) if value > 0 else 0.0

    @staticmethod
    def _is_positive_finite(value: object) -> bool:
        """値が正の有限数か判定する。"""

        return isinstance(value, (int, float)) and math.isfinite(value) and value > 0

    @staticmethod
    def _clamp_non_negative(value: float) -> float:
        """非有限値を0.0へ、負値を0.0以上へ制限する。"""

        if not math.isfinite(value):
            return 0.0
        return max(0.0, value)

    @staticmethod
    def _clamp_score(value: float) -> float:
        """参考スコアを0〜100に制限する。"""

        if not math.isfinite(value):
            return 0.0
        return min(100.0, max(0.0, value))
