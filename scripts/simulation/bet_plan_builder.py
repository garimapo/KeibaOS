"""Transform allocated recommendations into a persistence-ready bet-plan snapshot."""

from __future__ import annotations

from scripts.simulation.bet_plan_snapshot import SimulationBetPlanSnapshot
from scripts.simulation.models import SimulationBet
from scripts.simulation.selection_resolver import RaceEntrySelectionResolver
from scripts.simulation.stake_allocation import BetAllocationPlan


class SimulationBetPlanBuilder:
    """Transform allocated recommendations into a ``SimulationBetPlanSnapshot``."""

    __slots__ = ("_selection_resolver",)

    def __init__(self, *, selection_resolver: RaceEntrySelectionResolver) -> None:
        resolver_method = getattr(selection_resolver, "resolve_race_entry_ids", None)
        if isinstance(selection_resolver, type) or not callable(resolver_method):
            raise ValueError("selection_resolver must provide a callable resolve_race_entry_ids method")
        self._selection_resolver = selection_resolver

    def build(self, *, allocation_plan: BetAllocationPlan) -> SimulationBetPlanSnapshot:
        """Transform allocated recommendations into a persistence-ready bet-plan snapshot."""
        if not isinstance(allocation_plan, BetAllocationPlan):
            raise ValueError("allocation_plan must be a BetAllocationPlan")

        simulation_bets: list[SimulationBet] = []
        for allocation in allocation_plan.allocations:
            recommendation = allocation.recommendation
            race_entry_ids = self._selection_resolver.resolve_race_entry_ids(
                race_id=allocation_plan.identity.race_id,
                horse_ids=recommendation.horse_ids,
            )
            if not isinstance(race_entry_ids, tuple):
                raise ValueError("selection_resolver must return a tuple")
            if len(race_entry_ids) != len(recommendation.horse_ids):
                raise ValueError("resolved race_entry_ids must match horse_ids count")
            simulation_bets.append(
                SimulationBet(
                    race_id=allocation_plan.identity.race_id,
                    strategy_id=allocation_plan.identity.strategy_id,
                    bet_type=recommendation.bet_type,
                    race_entry_ids=race_entry_ids,
                    stake=allocation.stake,
                    recommendation_rank=recommendation.rank,
                    placed_at_cutoff=allocation_plan.identity.information_cutoff,
                )
            )

        return SimulationBetPlanSnapshot(
            identity=allocation_plan.identity,
            policy_identity=allocation_plan.policy_identity,
            budget=allocation_plan.budget,
            bets=tuple(simulation_bets),
        )
