"""各評価エンジンの結果を統合して総合評価を算出するモジュール。"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping

from scripts.models import Horse, Prediction, Race
from scripts.prediction.ability_engine import AbilityEvaluation
from scripts.prediction.jockey_engine import JockeyEvaluation
from scripts.prediction.pace_engine import PaceEvaluation
from scripts.prediction.track_engine import TrackEvaluation
from scripts.prediction.scorer import score_horse
from scripts.score_models import HorseScore


@dataclass(frozen=True)
class HorseEvaluationResults:
    """1頭分の各評価エンジン出力をまとめる入力DTO。"""

    ability: AbilityEvaluation | None = None
    pace: PaceEvaluation | None = None
    jockey: JockeyEvaluation | None = None
    track: TrackEvaluation | None = None


class Predictor:
    """能力・展開・騎手・コース適性を統合して総合評価を算出する。"""

    ABILITY_WEIGHT = 0.40
    PACE_WEIGHT = 0.20
    JOCKEY_WEIGHT = 0.20
    TRACK_WEIGHT = 0.20
    NEUTRAL_SCORE = 50.0

    _PACE_STYLE_SCORES = {
        "ハイ": {"逃げ": 35.0, "先行": 50.0, "差し": 80.0, "追込": 75.0},
        "平均": {"逃げ": 50.0, "先行": 50.0, "差し": 50.0, "追込": 50.0},
        "スロー": {"逃げ": 80.0, "先行": 75.0, "差し": 50.0, "追込": 35.0},
    }

    def predict(
        self,
        horse_evaluations: Mapping[int, HorseEvaluationResults],
        *,
        race_id: int = 0,
        prediction_time: str = "",
    ) -> list[Prediction]:
        """馬ごとの評価結果を統合し、総合スコア順の予測を返す。

        欠損した評価は50点の中立値として扱う。勝率予測や購入判定は行わない。
        """

        scored_predictions = [
            self._build_prediction(
                horse_id,
                evaluations,
                race_id,
                prediction_time,
            )
            for horse_id, evaluations in horse_evaluations.items()
        ]
        scored_predictions.sort(key=lambda prediction: prediction.score, reverse=True)

        return [
            Prediction(
                race_id=prediction.race_id,
                prediction_time=prediction.prediction_time,
                rank=str(index),
                score=prediction.score,
                buy_flag=False,
                comment=prediction.comment,
                horse_id=prediction.horse_id,
            )
            for index, prediction in enumerate(scored_predictions, start=1)
        ]

    def _build_prediction(
        self,
        horse_id: int,
        evaluations: HorseEvaluationResults,
        race_id: int,
        prediction_time: str,
    ) -> Prediction:
        """1頭分の評価を統合した順位未設定Predictionを生成する。"""

        ability_score = self._ability_score(evaluations.ability)
        pace_score = self._pace_score(horse_id, evaluations.pace)
        jockey_score = self._jockey_score(evaluations.jockey)
        track_score = self._track_score(evaluations.track)
        score = self._clamp_score(
            ability_score * self.ABILITY_WEIGHT
            + pace_score * self.PACE_WEIGHT
            + jockey_score * self.JOCKEY_WEIGHT
            + track_score * self.TRACK_WEIGHT
        )

        return Prediction(
            race_id=race_id,
            prediction_time=prediction_time,
            rank="",
            score=round(score, 2),
            buy_flag=False,
            comment=(
                f"ability={ability_score:.1f}, pace={pace_score:.1f}, "
                f"jockey={jockey_score:.1f}, track={track_score:.1f}"
            ),
            horse_id=horse_id,
        )

    def _ability_score(self, evaluation: AbilityEvaluation | None) -> float:
        """能力評価がない、または実績なしなら中立点を返す。"""

        if evaluation is None or evaluation.race_count <= 0:
            return self.NEUTRAL_SCORE

        return self._safe_score(evaluation.ability_index)

    def _pace_score(
        self,
        horse_id: int,
        evaluation: PaceEvaluation | None,
    ) -> float:
        """予測ペースと推定脚質の組合せから展開適合点を返す。"""

        if evaluation is None:
            return self.NEUTRAL_SCORE

        style = evaluation.running_styles.get(horse_id)
        pace_scores = self._PACE_STYLE_SCORES.get(evaluation.race_pace, {})

        return self._safe_score(pace_scores.get(style, self.NEUTRAL_SCORE))

    def _jockey_score(self, evaluation: JockeyEvaluation | None) -> float:
        """騎手評価がない、または実績なしなら中立点を返す。"""

        if evaluation is None or evaluation.race_count <= 0:
            return self.NEUTRAL_SCORE

        return self._safe_score(evaluation.score)

    def _track_score(self, evaluation: TrackEvaluation | None) -> float:
        """コース適性評価がない場合は中立点を返す。"""

        if evaluation is None:
            return self.NEUTRAL_SCORE

        return self._safe_score(evaluation.score)

    def _safe_score(self, value: object) -> float:
        """欠損・非有限・範囲外の値を安全な0〜100点へ変換する。"""

        if not isinstance(value, (int, float)) or not math.isfinite(value):
            return self.NEUTRAL_SCORE

        return self._clamp_score(float(value))

    @staticmethod
    def _clamp_score(value: float) -> float:
        """スコアを0〜100の範囲へ制限する。"""

        return min(100.0, max(0.0, value))


def predict(
    horse_evaluations: Mapping[int, HorseEvaluationResults] | Race,
    horses: list[Horse] | None = None,
    *,
    race_id: int = 0,
    prediction_time: str = "",
) -> list[Prediction] | list[HorseScore]:
    """総合評価を算出する便利関数。

    評価結果のマッピングを渡す新形式では ``Prediction`` を返す。
    ``predict(race, horses)`` の旧形式は互換性のため ``HorseScore`` を返す。
    """

    if isinstance(horse_evaluations, Race):
        if horses is None:
            raise ValueError("horses is required when passing a Race")

        scores = [score_horse(horse, horse_evaluations) for horse in horses]
        scores.sort(key=lambda score: score.total, reverse=True)

        return scores

    return Predictor().predict(
        horse_evaluations,
        race_id=race_id,
        prediction_time=prediction_time,
    )
