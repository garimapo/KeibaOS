"""Contract for loading the purchase plan of one simulated race.

The protocol intentionally contains no concrete source, repository, persistence,
validation, or prediction-cutoff logic.
"""

from __future__ import annotations

from typing import Protocol

from .models import SimulationBet, SimulationRaceInput, StrategyIdentity


class SimulationBetSource(Protocol):
    """Loads the already-planned atomic bets for one race and strategy."""

    def load_bets(
        self,
        *,
        race_input: SimulationRaceInput,
        strategy_identity: StrategyIdentity,
    ) -> tuple[SimulationBet, ...]:
        ...
