"""
KeibaOS Value Score

期待値評価
"""

from scripts.models import Horse, Race


def calc_value(
    horse: Horse,
    race: Race,
) -> float:
    """
    期待値評価

    Ver0.9では仮実装。
    Ver1.0でオッズ・期待値計算を実装する。
    """

    return 70.0