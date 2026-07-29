"""1レース分の予測から買い目候補までをつなぐ統合パイプライン。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import logging
from typing import Callable, Mapping, Sequence, TypeVar

from scripts.models import PastRace, Prediction
from scripts.prediction.ability_engine import AbilityEngine, AbilityEvaluation
from scripts.prediction.bet_generator import BetGenerator, BetRecommendation
from scripts.prediction.bet_strategy import BetPlan, BetStrategy, RuleBasedBetStrategy, StrategyConfig
from scripts.prediction.input_contracts import PredictionPipelineInput
from scripts.prediction.jockey_engine import JockeyEngine, JockeyEvaluation
from scripts.prediction.pace_engine import PaceEngine, PaceEvaluation
from scripts.prediction.predictor import HorseEvaluationResults, Predictor
from scripts.prediction.track_engine import RaceTrackConditions, TrackEngine, TrackEvaluation
from scripts.prediction.value_engine import ValueEngine, ValueEvaluation


logger = logging.getLogger(__name__)
_ResultType = TypeVar("_ResultType")


class PipelineStage(str, Enum):
    """統合パイプラインの実行段階。"""

    ABILITY = "ability"
    PACE = "pace"
    JOCKEY = "jockey"
    TRACK = "track"
    PREDICTOR = "predictor"
    VALUE = "value"
    BET_GENERATOR = "bet_generator"
    BET_STRATEGY = "bet_strategy"


class PipelineExecutionError(RuntimeError):
    """段階名を保持してパイプライン失敗を通知する例外。"""

    def __init__(self, stage: PipelineStage) -> None:
        super().__init__(f"prediction pipeline failed at stage: {stage.value}")
        self.stage = stage


@dataclass(frozen=True)
class RacePredictionInput:
    """通信・DBから切り離した、1レース分のパイプライン入力。"""

    horse_past_races: Mapping[int, Sequence[PastRace]]
    jockey_names_by_horse: Mapping[int, str]
    track_conditions: RaceTrackConditions
    odds_by_horse: Mapping[int, float]
    race_horse_count: int
    race_id: int = 0
    prediction_time: str = ""


@dataclass(frozen=True)
class PipelineConfig:
    """各エンジンと戦略設定を注入するためのパイプライン構成。"""

    ability_engine: AbilityEngine = field(default_factory=AbilityEngine)
    pace_engine: PaceEngine = field(default_factory=PaceEngine)
    jockey_engine: JockeyEngine = field(default_factory=JockeyEngine)
    track_engine: TrackEngine = field(default_factory=TrackEngine)
    predictor: Predictor = field(default_factory=Predictor)
    value_engine: ValueEngine = field(default_factory=ValueEngine)
    bet_generator: BetGenerator = field(default_factory=BetGenerator)
    bet_strategy: BetStrategy = field(default_factory=RuleBasedBetStrategy)
    strategy_config: StrategyConfig = field(default_factory=StrategyConfig)


@dataclass(frozen=True)
class PipelineResult:
    """実行段階ごとの中間結果と最終購入計画。"""

    ability_evaluations: Mapping[int, AbilityEvaluation]
    pace_evaluation: PaceEvaluation
    jockey_evaluations: Mapping[int, JockeyEvaluation]
    track_evaluations: Mapping[int, TrackEvaluation]
    predictions: tuple[Prediction, ...]
    value_evaluations: tuple[ValueEvaluation, ...]
    recommendations: tuple[BetRecommendation, ...]
    bet_plan: BetPlan


class PredictionPipeline:
    """既存の予測・候補・戦略モジュールを順番に実行する。"""

    def __init__(self, config: PipelineConfig | None = None) -> None:
        self.config = config or PipelineConfig()

    def run(self, race_input: PredictionPipelineInput) -> PipelineResult:
        """入力済みの1レースを評価し、購入対象候補まで生成する。"""

        horse_past_races = race_input.horse_past_races
        ability_evaluations = self._run_stage(
            PipelineStage.ABILITY,
            lambda: {
                horse_id: self.config.ability_engine.evaluate(past_races)
                for horse_id, past_races in horse_past_races.items()
            },
        )
        pace_evaluation = self._run_stage(
            PipelineStage.PACE,
            lambda: self.config.pace_engine.evaluate(horse_past_races),
        )
        jockey_evaluations = self._run_stage(
            PipelineStage.JOCKEY,
            lambda: {
                horse_id: self.config.jockey_engine.evaluate(
                    race_input.jockey_names_by_horse.get(horse_id, ""), past_races
                )
                for horse_id, past_races in horse_past_races.items()
            },
        )
        track_evaluations = self._run_stage(
            PipelineStage.TRACK,
            lambda: self.config.track_engine.evaluate(
                race_input.track_conditions, horse_past_races
            ),
        )
        predictions = self._run_stage(
            PipelineStage.PREDICTOR,
            lambda: self.config.predictor.predict(
                {
                    horse_id: HorseEvaluationResults(
                        ability=ability_evaluations[horse_id],
                        pace=pace_evaluation,
                        jockey=jockey_evaluations[horse_id],
                        track=track_evaluations.get(horse_id),
                    )
                    for horse_id in horse_past_races
                },
                race_id=race_input.race_id,
                prediction_time=race_input.prediction_time,
            ),
        )
        value_evaluations = self._run_stage(
            PipelineStage.VALUE,
            lambda: self.config.value_engine.evaluate(predictions, race_input.odds_by_horse),
        )
        recommendations = self._run_stage(
            PipelineStage.BET_GENERATOR,
            lambda: self.config.bet_generator.generate(
                value_evaluations, predictions, race_input.race_horse_count
            ),
        )
        bet_plan = self._run_stage(
            PipelineStage.BET_STRATEGY,
            lambda: self.config.bet_strategy.create_plan(
                recommendations, self.config.strategy_config
            ),
        )
        return PipelineResult(
            ability_evaluations=ability_evaluations,
            pace_evaluation=pace_evaluation,
            jockey_evaluations=jockey_evaluations,
            track_evaluations=track_evaluations,
            predictions=tuple(predictions),
            value_evaluations=tuple(value_evaluations),
            recommendations=tuple(recommendations),
            bet_plan=bet_plan,
        )

    @staticmethod
    def _run_stage(stage: PipelineStage, operation: Callable[[], _ResultType]) -> _ResultType:
        """段階別にログを残し、失敗を段階名付きの例外へ変換する。"""

        try:
            return operation()
        except Exception as error:
            logger.exception("Prediction pipeline failed at stage '%s'", stage.value)
            raise PipelineExecutionError(stage) from error
