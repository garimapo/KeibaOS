"""
KeibaOS Predictor

レース全体の予想を実行する。
"""

from scripts.models import Horse, Race
from scripts.prediction.scorer import score_horse
from scripts.score_models import HorseScore


def predict(
    race: Race,
    horses: list[Horse],
) -> list[HorseScore]:
    """
    レース予想を実行する。

    Args:
        race:
            レース情報

        horses:
            出走馬一覧

    Returns:
        HorseScore一覧（総合点順）
    """

    scores: list[HorseScore] = []

    for horse in horses:

        score = score_horse(
            horse,
            race,
        )

        scores.append(score)

    scores.sort(
        key=lambda score: score.total,
        reverse=True,
    )

    return scores