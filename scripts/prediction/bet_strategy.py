"""購入候補から購入対象を選ぶための純粋な戦略ロジック。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Sequence

from scripts.prediction.bet_generator import BetRecommendation


class SelectionStyle(str, Enum):
    """組み合わせ候補と単勝候補の優先方針。"""

    BOX = "box"
    FORMATION = "formation"


class SortCondition(str, Enum):
    """候補の主ソート条件。"""

    GENERATOR_RANK = "generator_rank"
    COMBINATION_SCORE = "combination_score"
    PREDICTION_SCORE = "prediction_score"
    ESTIMATED_PROBABILITY = "estimated_probability"


@dataclass(frozen=True)
class StrategyConfig:
    """ルールベース戦略の設定値。"""

    allowed_bet_types: frozenset[str] = field(
        default_factory=lambda: frozenset({"単勝", "馬連", "ワイド", "3連複"})
    )
    max_bet_count: int = 10
    selection_style: SelectionStyle = SelectionStyle.FORMATION
    min_combination_score: float = 0.0
    max_candidates: int = 50
    sort_condition: SortCondition = SortCondition.GENERATOR_RANK


@dataclass(frozen=True)
class BetPlan:
    """戦略によって購入対象として抽出された、順序付きの候補一覧。"""

    strategy_name: str
    recommendations: tuple[BetRecommendation, ...]
    candidate_count: int


class BetStrategy(ABC):
    """異なる購入戦略を追加するためのインターフェース。"""

    @abstractmethod
    def create_plan(
        self,
        recommendations: Sequence[BetRecommendation],
        config: StrategyConfig,
    ) -> BetPlan:
        """候補を抽出・優先順位付けし、購入対象の計画を返す。"""


class RuleBasedBetStrategy(BetStrategy):
    """設定値だけで候補を抽出する標準戦略。

    BOX優先では組み合わせ券種を単勝より前に、フォーメーション優先では単勝を
    組み合わせ券種より前に配置する。候補の組み替えや評価値の変更は行わない。
    """

    _COMBINATION_TYPES = frozenset({"馬連", "ワイド", "3連複"})

    def create_plan(
        self,
        recommendations: Sequence[BetRecommendation],
        config: StrategyConfig,
    ) -> BetPlan:
        """設定に従ってフィルタ・重複排除・優先順位付けを行う。"""

        self._validate_config(config)
        filtered = [
            recommendation
            for recommendation in recommendations
            if self._is_eligible(recommendation, config)
        ]
        ordered = sorted(filtered, key=lambda item: self._sort_key(item, config))
        unique = self._deduplicate(ordered)
        limited_candidates = unique[: config.max_candidates]
        selected = limited_candidates[: config.max_bet_count]
        return BetPlan(
            strategy_name=self.__class__.__name__,
            recommendations=tuple(selected),
            candidate_count=len(limited_candidates),
        )

    def _is_eligible(
        self,
        recommendation: BetRecommendation,
        config: StrategyConfig,
    ) -> bool:
        """券種と組み合わせスコアの条件を満たす候補か判定する。"""

        if recommendation.bet_type not in config.allowed_bet_types:
            return False
        if recommendation.bet_type not in self._COMBINATION_TYPES:
            return True
        return self._safe_score(recommendation.combination_score) >= config.min_combination_score

    def _sort_key(
        self,
        recommendation: BetRecommendation,
        config: StrategyConfig,
    ) -> tuple[float, float, float, float, int, tuple[int, ...]]:
        """評価値を変えずに安定した優先順位用キーを返す。"""

        style_priority = self._style_priority(recommendation, config.selection_style)
        primary = self._primary_value(recommendation, config.sort_condition)
        return (
            style_priority,
            -primary,
            -self._safe_score(recommendation.prediction_score),
            -self._safe_probability(recommendation.estimated_probability),
            recommendation.rank,
            recommendation.horse_ids,
        )

    def _style_priority(
        self,
        recommendation: BetRecommendation,
        selection_style: SelectionStyle,
    ) -> float:
        """BOX/フォーメーションの券種優先順を返す。"""

        is_combination = recommendation.bet_type in self._COMBINATION_TYPES
        if selection_style is SelectionStyle.BOX:
            return 0.0 if is_combination else 1.0
        return 1.0 if is_combination else 0.0

    def _primary_value(
        self,
        recommendation: BetRecommendation,
        sort_condition: SortCondition,
    ) -> float:
        """設定された主ソート値を安全に取り出す。"""

        if sort_condition is SortCondition.GENERATOR_RANK:
            return -float(max(0, recommendation.rank))
        if sort_condition is SortCondition.COMBINATION_SCORE:
            return self._safe_score(
                recommendation.combination_score
                if recommendation.combination_score is not None
                else recommendation.expected_value
            )
        if sort_condition is SortCondition.PREDICTION_SCORE:
            return self._safe_score(recommendation.prediction_score)
        return self._safe_probability(recommendation.estimated_probability)

    @staticmethod
    def _deduplicate(
        recommendations: Sequence[BetRecommendation],
    ) -> list[BetRecommendation]:
        """同一券種・同一馬組の候補は優先順位上位の1件だけを残す。"""

        unique: list[BetRecommendation] = []
        seen: set[tuple[str, tuple[int, ...]]] = set()
        for recommendation in recommendations:
            key = (recommendation.bet_type, recommendation.horse_ids)
            if key not in seen:
                seen.add(key)
                unique.append(recommendation)
        return unique

    @staticmethod
    def _validate_config(config: StrategyConfig) -> None:
        """安全に解釈できない設定を拒否する。"""

        if config.max_bet_count < 0:
            raise ValueError("max_bet_count must be non-negative")
        if config.max_candidates < 0:
            raise ValueError("max_candidates must be non-negative")
        if not isinstance(config.min_combination_score, (int, float)) or not math.isfinite(
            config.min_combination_score
        ):
            raise ValueError("min_combination_score must be finite")
        if not isinstance(config.selection_style, SelectionStyle):
            raise ValueError("selection_style must be a SelectionStyle")
        if not isinstance(config.sort_condition, SortCondition):
            raise ValueError("sort_condition must be a SortCondition")

    @staticmethod
    def _safe_score(value: object) -> float:
        """スコアを0以上の有限値へ正規化する。"""

        if not isinstance(value, (int, float)) or not math.isfinite(value):
            return 0.0
        return max(0.0, float(value))

    @classmethod
    def _safe_probability(cls, value: object) -> float:
        """推定確率を0〜1の有限値へ正規化する。"""

        return min(1.0, cls._safe_score(value))
