"""
KeibaOS Score Models

AI予想で使用する
スコアモデルを定義する。
"""

from dataclasses import dataclass

from scripts.models import Horse


@dataclass
class HorseScore:
    """
    出走馬スコア
    """

    horse: Horse

    ability: float = 0.0
    pace: float = 0.0
    jockey: float = 0.0
    frame: float = 0.0
    track: float = 0.0
    value: float = 0.0

    @property
    def total(self) -> float:
        """
        総合スコア
        """

        return round(

            self.ability * 0.35 +
            self.pace * 0.25 +
            self.jockey * 0.15 +
            self.frame * 0.10 +
            self.track * 0.10 +
            self.value * 0.05,

            2,
        )