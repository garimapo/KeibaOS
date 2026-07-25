"""Immutable, persistence-ready simulation bet-plan snapshot contract."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from scripts.prediction.allocation_policy import AllocationPolicyIdentity
from scripts.simulation.bet_plan_identity import SimulationBetPlanIdentity
from scripts.simulation.models import SimulationBet
from scripts.simulation.stake_allocation import BetStakeBudget


@dataclass(frozen=True, slots=True)
class SimulationBetPlanSnapshot:
    """The fixed immutable bet plan for one run, race, strategy, and cutoff."""

    identity: SimulationBetPlanIdentity
    policy_identity: AllocationPolicyIdentity
    budget: BetStakeBudget
    bets: tuple[SimulationBet, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.identity, SimulationBetPlanIdentity):
            raise ValueError("identity must be a SimulationBetPlanIdentity")
        if not isinstance(self.policy_identity, AllocationPolicyIdentity):
            raise ValueError("policy_identity must be an AllocationPolicyIdentity")
        if not isinstance(self.budget, BetStakeBudget):
            raise ValueError("budget must be a BetStakeBudget")
        bets = self._normalize_bets(self.bets)
        for bet in bets:
            if (
                bet.race_id != self.identity.race_id
                or bet.strategy_id != self.identity.strategy_id
                or bet.placed_at_cutoff != self.identity.information_cutoff
            ):
                raise ValueError("bet must match the snapshot identity")
        if sum(bet.stake for bet in bets) > self.budget.total_amount:
            raise ValueError("bet stakes must not exceed the snapshot budget")
        identities = tuple((bet.bet_type, bet.race_entry_ids) for bet in bets)
        if len(set(identities)) != len(identities):
            raise ValueError("bets must have unique bet_type and race_entry_ids identities")
        object.__setattr__(self, "bets", bets)

    @staticmethod
    def _normalize_bets(value: object) -> tuple[SimulationBet, ...]:
        if isinstance(value, str | bytes | bytearray | Mapping) or not isinstance(value, Iterable):
            raise ValueError("bets must be a non-string, non-mapping iterable")
        try:
            bets = tuple(value)
        except TypeError as exc:
            raise ValueError("bets must be iterable") from exc
        if not all(isinstance(bet, SimulationBet) for bet in bets):
            raise ValueError("bets must contain SimulationBet values")
        return bets

    @property
    def allocated_amount(self) -> int:
        """Return the total stake of the immutable bet tuple."""
        return sum(bet.stake for bet in self.bets)

    @property
    def unallocated_amount(self) -> int:
        """Return the budget intentionally unused by this plan."""
        return self.budget.total_amount - self.allocated_amount
