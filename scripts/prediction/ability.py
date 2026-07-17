"""
KeibaOS Ability Score

能力評価
"""

from scripts.models import Horse, Race


def calc_ability(
    horse: Horse,
    race: Race,
) -> float:
    """
    能力評価

    Ver0.9では仮実装。
    Ver1.0で過去走データを用いて実装する。
    """

    return 70.0