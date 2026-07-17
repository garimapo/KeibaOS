"""過去走の通過順位から脚質とレースペースを推定するモジュール。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from statistics import median
from typing import Literal, Mapping, Sequence, TypeAlias

from scripts.models import PastRace


RunningStyle: TypeAlias = Literal["逃げ", "先行", "差し", "追込"]
RacePace: TypeAlias = Literal["スロー", "平均", "ハイ"]


@dataclass(frozen=True)
class PaceEvaluation:
    """出走馬の脚質推定とレース全体のペース予測。"""

    race_pace: RacePace
    running_styles: dict[int, RunningStyle]
    leader_count: int
    evaluated_horse_count: int


class PaceEngine:
    """過去走の4角位置・通過順位から脚質とレースペースを推定する。

    能力指数、騎手、馬場、展開以外の要因は参照しない。
    """

    def evaluate(
        self,
        horse_past_races: Mapping[int, Sequence[PastRace]],
    ) -> PaceEvaluation:
        """各馬の過去走から脚質を推定し、全体ペースを判定する。

        Args:
            horse_past_races: ``horses.id`` ごとの過去走一覧。

        Returns:
            脚質を推定できた馬の内訳と、レース全体のペース評価。
        """

        running_styles: dict[int, RunningStyle] = {}

        for horse_id, past_races in horse_past_races.items():
            style = self._estimate_running_style(past_races)

            if style is not None:
                running_styles[horse_id] = style

        leader_count = sum(
            style == "逃げ"
            for style in running_styles.values()
        )

        return PaceEvaluation(
            race_pace=self._estimate_race_pace(running_styles, leader_count),
            running_styles=running_styles,
            leader_count=leader_count,
            evaluated_horse_count=len(running_styles),
        )

    def _estimate_running_style(
        self,
        past_races: Sequence[PastRace],
    ) -> RunningStyle | None:
        """有効な4角位置の中央値から脚質を推定する。"""

        positions = [
            position
            for past_race in past_races
            if (position := self._fourth_corner_position(past_race)) > 0
        ]

        if not positions:
            return None

        typical_position = median(positions)

        if typical_position <= 2:
            return "逃げ"
        if typical_position <= 5:
            return "先行"
        if typical_position <= 9:
            return "差し"

        return "追込"

    def _estimate_race_pace(
        self,
        running_styles: Mapping[int, RunningStyle],
        leader_count: int,
    ) -> RacePace:
        """逃げ馬数と前方脚質の比率から全体ペースを判定する。"""

        evaluated_count = len(running_styles)

        if evaluated_count == 0:
            return "平均"

        front_runner_count = sum(
            style in ("逃げ", "先行")
            for style in running_styles.values()
        )
        front_runner_ratio = front_runner_count / evaluated_count

        if leader_count >= 2 or (leader_count >= 1 and front_runner_ratio >= 0.75):
            return "ハイ"
        if leader_count == 0 and front_runner_ratio <= 0.25:
            return "スロー"

        return "平均"

    @staticmethod
    def _fourth_corner_position(past_race: PastRace) -> int:
        """4角位置を優先し、未取得時は通過順位から安全に取得する。"""

        if past_race.fourth_corner_position > 0:
            return past_race.fourth_corner_position

        sequence = re.search(
            r"(\d+)\s*[-－ー→>/／]\s*(\d+)\s*[-－ー→>/／]\s*(\d+)"
            r"(?:\s*[-－ー→>/／]\s*(\d+))?",
            past_race.passing_order,
        )

        if sequence is not None:
            return int(sequence.group(4) or sequence.group(3))

        positions = re.findall(r"\d+", past_race.passing_order)

        return int(positions[-1]) if 1 <= len(positions) <= 4 else 0
