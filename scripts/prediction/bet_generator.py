"""予測評価から購入候補だけを生成する純粋ロジック。"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
import math
from typing import Sequence

from scripts.models import Prediction
from scripts.prediction.value_engine import ValueEvaluation


@dataclass(frozen=True)
class BetRecommendation:
    """券種ごとの候補。

    ``expected_value`` は単勝候補だけに設定する単勝の推定期待値である。
    組み合わせ券種では実オッズがないため期待値を算出せず、構成馬の単勝推定
    期待値の平均を候補比較用 ``combination_score`` として保持する。
    """

    rank: int
    bet_type: str
    horse_ids: tuple[int, ...]
    estimated_probability: float
    expected_value: float | None
    combination_score: float | None
    prediction_score: float


@dataclass(frozen=True)
class _HorseCandidate:
    """組み合わせ候補を作るために正規化した馬単位の入力。"""

    horse_id: int
    estimated_probability: float
    expected_value: float
    score: float


class BetGenerator:
    """価値評価・総合スコアから券種別の候補を生成する。"""

    WIN = "単勝"
    QUINELLA = "馬連"
    WIDE = "ワイド"
    TRIO = "3連複"

    def generate(
        self,
        value_evaluations: Sequence[ValueEvaluation],
        predictions: Sequence[Prediction],
        race_horse_count: int,
    ) -> list[BetRecommendation]:
        """単勝・馬連・ワイド・3連複の全候補を順位付きで返す。

        入力の同一horse_idは対応付けを曖昧にするため ``ValueError`` として拒否する。
        馬連等の組み合わせオッズはまだ扱わないため、組み合わせの ``expected_value``
        は設定しない。候補の採否・購入頭数・資金配分は、このモジュールでは決めず、
        将来のStrategyモジュールが順位付き候補を入力として決定する。
        """

        if race_horse_count <= 0:
            return []
        self._reject_duplicate_ids(value_evaluations, "value_evaluations")
        self._reject_duplicate_ids(predictions, "predictions")

        candidates = self._eligible_horses(value_evaluations, predictions)
        if not candidates:
            return []

        recommendations = self._win_recommendations(candidates)
        if race_horse_count >= 2:
            recommendations.extend(
                self._combination_recommendations(
                    self.QUINELLA, candidates, 2
                )
            )
            recommendations.extend(self._combination_recommendations(self.WIDE, candidates, 2))
        if race_horse_count >= 3:
            recommendations.extend(self._combination_recommendations(self.TRIO, candidates, 3))

        ordered = sorted(
            recommendations,
            key=lambda item: (
                -self._recommendation_score(item),
                -item.prediction_score,
                -item.estimated_probability,
                item.bet_type,
                item.horse_ids,
            ),
        )
        return [
            BetRecommendation(
                rank=index,
                bet_type=item.bet_type,
                horse_ids=item.horse_ids,
                estimated_probability=item.estimated_probability,
                expected_value=item.expected_value,
                combination_score=item.combination_score,
                prediction_score=item.prediction_score,
            )
            for index, item in enumerate(ordered, start=1)
        ]

    def _eligible_horses(
        self,
        value_evaluations: Sequence[ValueEvaluation],
        predictions: Sequence[Prediction],
    ) -> list[_HorseCandidate]:
        """両方の評価がある全馬を候補用の優先順に返す。"""

        scores = {
            prediction.horse_id: self._safe_score(prediction.score)
            for prediction in predictions
        }
        candidates = [
            _HorseCandidate(
                horse_id=evaluation.horse_id,
                estimated_probability=self._safe_probability(
                    evaluation.estimated_win_probability
                ),
                expected_value=self._safe_non_negative(evaluation.expected_value),
                score=scores[evaluation.horse_id],
            )
            for evaluation in value_evaluations
            if evaluation.horse_id in scores
        ]
        return sorted(
            candidates,
            key=lambda item: (
                -item.expected_value,
                -item.score,
                -item.estimated_probability,
                item.horse_id,
            ),
        )

    def _win_recommendations(
        self, candidates: Sequence[_HorseCandidate]
    ) -> list[BetRecommendation]:
        """全馬について単勝候補を生成する。"""

        return [
            BetRecommendation(
                rank=0,
                bet_type=self.WIN,
                horse_ids=(candidate.horse_id,),
                estimated_probability=candidate.estimated_probability,
                expected_value=candidate.expected_value,
                combination_score=None,
                prediction_score=candidate.score,
            )
            for candidate in candidates
        ]

    def _combination_recommendations(
        self,
        bet_type: str,
        candidates: Sequence[_HorseCandidate],
        size: int,
    ) -> list[BetRecommendation]:
        """重複のない馬番組み合わせ候補を生成する。"""

        return [
            self._build_combination(bet_type, combination)
            for combination in combinations(candidates, size)
        ]

    def _build_combination(
        self,
        bet_type: str,
        combination: Sequence[_HorseCandidate],
    ) -> BetRecommendation:
        """組み合わせの比較指標を計算する。"""

        size = len(combination)
        probability = math.factorial(size) * math.prod(
            candidate.estimated_probability for candidate in combination
        )
        return BetRecommendation(
            rank=0,
            bet_type=bet_type,
            horse_ids=tuple(sorted(candidate.horse_id for candidate in combination)),
            estimated_probability=min(1.0, self._safe_non_negative(probability)),
            expected_value=None,
            combination_score=sum(candidate.expected_value for candidate in combination)
            / size,
            prediction_score=sum(candidate.score for candidate in combination) / size,
        )

    @staticmethod
    def _recommendation_score(recommendation: BetRecommendation) -> float:
        """単勝EVまたは組み合わせ比較スコアをソート用に返す。"""

        if recommendation.expected_value is not None:
            return recommendation.expected_value
        return recommendation.combination_score or 0.0

    @staticmethod
    def _reject_duplicate_ids(items: Sequence[object], name: str) -> None:
        """horse_idの重複を検出して拒否する。"""

        horse_ids = [getattr(item, "horse_id") for item in items]
        if len(set(horse_ids)) != len(horse_ids):
            raise ValueError(f"{name} must not contain duplicate horse_id values")

    @staticmethod
    def _safe_non_negative(value: object) -> float:
        """非有限値・負値を0.0へ正規化する。"""

        if not isinstance(value, (int, float)) or not math.isfinite(value):
            return 0.0
        return max(0.0, float(value))

    @classmethod
    def _safe_score(cls, value: object) -> float:
        """総合スコアを0〜100へ正規化する。"""

        return min(100.0, cls._safe_non_negative(value))

    @classmethod
    def _safe_probability(cls, value: object) -> float:
        """推定確率を0〜1へ正規化する。"""

        return min(1.0, cls._safe_non_negative(value))
