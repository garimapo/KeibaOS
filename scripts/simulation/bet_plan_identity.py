"""Immutable identity for one simulation run's race-level bet plan."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class SimulationBetPlanIdentity:
    """Immutable bet plan identity for one simulation run, race, strategy, and cutoff."""

    run_id: str
    race_id: int
    strategy_id: str
    strategy_config_hash: str
    information_cutoff: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.run_id, str) or not self.run_id.strip():
            raise ValueError("run_id must be a non-empty string")
        if not isinstance(self.race_id, int) or isinstance(self.race_id, bool) or self.race_id <= 0:
            raise ValueError("race_id must be a positive integer")
        if not isinstance(self.strategy_id, str) or not self.strategy_id.strip():
            raise ValueError("strategy_id must be a non-empty string")
        if (
            not isinstance(self.strategy_config_hash, str)
            or len(self.strategy_config_hash) != 64
            or any(character not in "0123456789abcdef" for character in self.strategy_config_hash)
        ):
            raise ValueError("strategy_config_hash must be a lowercase SHA-256 digest")
        if (
            not isinstance(self.information_cutoff, datetime)
            or self.information_cutoff.tzinfo is None
            or self.information_cutoff.utcoffset() is None
        ):
            raise ValueError("information_cutoff must be a timezone-aware datetime")
