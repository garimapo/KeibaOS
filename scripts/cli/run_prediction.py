"""保存済みの1レースを予測パイプラインで実行するCLI。"""

from __future__ import annotations

import argparse
import logging
from typing import Protocol, Sequence

from scripts import database
from scripts.models import Race
from scripts.prediction.bet_strategy import SelectionStyle, SortCondition, StrategyConfig
from scripts.prediction.prediction_pipeline import (
    PipelineConfig,
    PipelineExecutionError,
    PipelineResult,
    PredictionPipeline,
    RacePredictionInput,
)
from scripts.prediction.track_engine import RaceTrackConditions


class RaceInputProvider(Protocol):
    """CLIがパイプライン入力を取得するための境界。"""

    def load(self, race_id: int) -> RacePredictionInput:
        """指定レースの予測用入力を返す。"""


class DatabaseRaceInputProvider:
    """既存DBを読み取り、パイプライン入力へ変換するアダプター。"""

    def load(self, race_id: int) -> RacePredictionInput:
        """DBに保存済みのレース・出走馬・過去走を入力形式へ変換する。"""

        race = next(
            (race for stored_id, race in database.get_all_races() if stored_id == race_id),
            None,
        )
        if race is None:
            raise ValueError(f"race_id={race_id} was not found")

        horse_past_races = {}
        jockey_names_by_horse = {}
        odds_by_horse = {}
        horses = database.get_horses_by_race(race_id)
        for horse in horses:
            horse_id = database.get_horse_id(race_id, horse.horse_name)
            if horse_id is None:
                raise ValueError(f"horse id was not found: {horse.horse_name}")
            horse_past_races[horse_id] = database.get_past_races(horse_id)
            jockey_names_by_horse[horse_id] = horse.jockey
            odds_by_horse[horse_id] = horse.odds

        return RacePredictionInput(
            horse_past_races=horse_past_races,
            jockey_names_by_horse=jockey_names_by_horse,
            track_conditions=database_to_track_conditions(race),
            odds_by_horse=odds_by_horse,
            race_horse_count=race.horse_count or len(horses),
            race_id=race_id,
            prediction_time=race.race_date,
        )


def database_to_track_conditions(race: Race) -> RaceTrackConditions:
    """DBのRaceモデルをTrackEngine用条件へ変換する。"""

    return RaceTrackConditions(
        place=race.place,
        distance=race.distance,
        track=race.track,
        track_condition=race.track_condition,
    )


class PredictionDisplayFormatter:
    """パイプライン結果をユーザー向けの複数行テキストへ整形する。"""

    def format(self, result: PipelineResult) -> str:
        """総合順位・暫定推定値・推奨買い目を整形する。"""

        values = {item.horse_id: item for item in result.value_evaluations}
        rows = ["予想結果", "順位 | 馬ID | 総合スコア | 暫定推定勝率 | 推定EV"]
        for prediction in result.predictions:
            value = values.get(prediction.horse_id)
            probability = value.estimated_win_probability if value else 0.0
            expected_value = value.expected_value if value else 0.0
            rows.append(
                f"{prediction.rank} | {prediction.horse_id} | {prediction.score:.2f} | "
                f"{probability:.4f} | {expected_value:.4f}"
            )

        rows.append("推奨買い目")
        if not result.bet_plan.recommendations:
            rows.append("候補なし")
        for recommendation in result.bet_plan.recommendations:
            score = (
                recommendation.expected_value
                if recommendation.expected_value is not None
                else recommendation.combination_score or 0.0
            )
            horses = "-".join(str(horse_id) for horse_id in recommendation.horse_ids)
            rows.append(
                f"{recommendation.bet_type} {horses} "
                f"(候補順位={recommendation.rank}, 比較値={score:.4f})"
            )
        return "\n".join(rows)


def build_parser() -> argparse.ArgumentParser:
    """CLI引数パーサーを作成する。"""

    parser = argparse.ArgumentParser(description="1レースの予想と買い目候補を表示します")
    parser.add_argument("race_id", type=int, help="DBに保存済みのレースID")
    parser.add_argument("--bet-types", default="単勝,馬連,ワイド,3連複", help="対象券種をカンマ区切りで指定")
    parser.add_argument("--max-bets", type=int, default=10, help="最大購入点数")
    parser.add_argument("--max-candidates", type=int, default=50, help="戦略で考慮する最大候補数")
    parser.add_argument("--style", choices=[item.value for item in SelectionStyle], default=SelectionStyle.FORMATION.value)
    parser.add_argument("--min-combination-score", type=float, default=0.0, help="組み合わせ比較値の下限")
    parser.add_argument("--sort", choices=[item.value for item in SortCondition], default=SortCondition.GENERATOR_RANK.value)
    return parser


def strategy_config_from_args(args: argparse.Namespace) -> StrategyConfig:
    """CLI引数をStrategyConfigへ変換する。"""

    return StrategyConfig(
        allowed_bet_types=frozenset(
            bet_type.strip() for bet_type in args.bet_types.split(",") if bet_type.strip()
        ),
        max_bet_count=args.max_bets,
        selection_style=SelectionStyle(args.style),
        min_combination_score=args.min_combination_score,
        max_candidates=args.max_candidates,
        sort_condition=SortCondition(args.sort),
    )


def run(
    argv: Sequence[str] | None = None,
    *,
    provider: RaceInputProvider | None = None,
    pipeline: PredictionPipeline | None = None,
    output_logger: logging.Logger | None = None,
) -> int:
    """CLIを実行し、成功時は0、入力・パイプライン失敗時は1を返す。"""

    args = build_parser().parse_args(argv)
    logger = output_logger or logging.getLogger(__name__)
    if not logger.handlers and not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    try:
        strategy_config = strategy_config_from_args(args)
        active_pipeline = pipeline or PredictionPipeline(
            PipelineConfig(strategy_config=strategy_config)
        )
        race_input = (provider or DatabaseRaceInputProvider()).load(args.race_id)
        result = active_pipeline.run(race_input)
    except PipelineExecutionError as error:
        logger.error("予想パイプラインが失敗しました: 段階=%s", error.stage.value)
        return 1
    except (TypeError, ValueError) as error:
        logger.error("予想を実行できません: %s", error)
        return 1

    logger.info("%s", PredictionDisplayFormatter().format(result))
    return 0


def main() -> int:
    """コンソールスクリプト用エントリーポイント。"""

    return run()


if __name__ == "__main__":
    raise SystemExit(main())
