"""
KeibaOS Scorer

出走馬を評価し、
HorseScoreを生成する。
"""

from scripts.models import Horse, Race
from scripts.score_models import HorseScore

from scripts.prediction.config import (
    ABILITY_WEIGHT,
    PACE_WEIGHT,
    JOCKEY_WEIGHT,
    FRAME_WEIGHT,
    TRACK_WEIGHT,
    VALUE_WEIGHT,
)

from scripts.prediction.ability import calc_ability
from scripts.prediction.value import calc_value


def score_horse(
    horse: Horse,
    race: Race,
) -> HorseScore:
    """
    1頭のスコアを計算する。
    """

    score = HorseScore(
        horse=horse,
    )

    # =====================================
    # Ability
    # =====================================

    score.ability = calc_ability(
        horse,
        race,
    )

    # =====================================
    # Pace
    # =====================================

    score.pace = 70.0

    # =====================================
    # Jockey
    # =====================================

    score.jockey = 70.0

    # =====================================
    # Frame
    # =====================================

    score.frame = 70.0

    # =====================================
    # Track
    # =====================================

    score.track = 70.0

    # =====================================
    # Value
    # =====================================

    score.value = calc_value(
        horse,
        race,
    )

 
    return score