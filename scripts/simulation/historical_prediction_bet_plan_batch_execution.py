"""Orchestrate ordered historical bet-plan persistence."""

from __future__ import annotations

from collections.abc import Mapping

from scripts.prediction.bet_strategy import RuleBasedBetStrategy
from scripts.simulation.bet_plan_snapshot import SimulationBetPlanSnapshot
from scripts.simulation.bet_plan_snapshot_repository import SimulationBetPlanSnapshotRepository
from scripts.simulation.historical_input_snapshots import HistoricalInputSnapshot
from scripts.simulation.historical_prediction_bet_plan_execution import (
    execute_and_persist_historical_bet_plan,
)
from scripts.simulation.models import SimulationRunContext, StrategyIdentity
from scripts.simulation.stake_allocation import BetStakeBudget
from scripts.simulation.validation import SimulationValidationError


__all__ = (
    "execute_and_persist_historical_bet_plans",
)


def execute_and_persist_historical_bet_plans(
    *,
    snapshots: tuple[HistoricalInputSnapshot, ...],
    run_context: SimulationRunContext,
    strategy_identity: StrategyIdentity,
    budgets_by_race_id: Mapping[int, BetStakeBudget],
    snapshot_repository: SimulationBetPlanSnapshotRepository,
) -> tuple[SimulationBetPlanSnapshot, ...]:
    """Persist one c4g0 plan per exact historical snapshot in canonical order."""

    if type(snapshots) is not tuple:
        raise ValueError("snapshots must be an exact tuple")
    snapshot_types = tuple(type(snapshot) is HistoricalInputSnapshot for snapshot in snapshots)
    if not all(snapshot_types):
        raise ValueError("snapshots must contain exact HistoricalInputSnapshot values")
    if type(run_context) is not SimulationRunContext:
        raise ValueError("run_context must be a SimulationRunContext")
    if type(strategy_identity) is not StrategyIdentity:
        raise ValueError("strategy_identity must be a StrategyIdentity")
    if isinstance(budgets_by_race_id, type) or not isinstance(budgets_by_race_id, Mapping):
        raise ValueError("budgets_by_race_id must be a Mapping")

    budgets = dict(budgets_by_race_id)
    for race_id, budget in budgets.items():
        if type(race_id) is not int or isinstance(race_id, bool) or race_id <= 0:
            raise ValueError("budget race IDs must be positive integers")
        if type(budget) is not BetStakeBudget:
            raise ValueError("budgets_by_race_id must contain exact BetStakeBudget values")

    if isinstance(snapshot_repository, type) or not callable(
        getattr(snapshot_repository, "save_snapshot", None)
    ):
        raise ValueError("snapshot_repository must provide a callable save_snapshot method")
    if strategy_identity.strategy_name != RuleBasedBetStrategy.__name__:
        raise ValueError("strategy_identity.strategy_name must be RuleBasedBetStrategy")

    canonical_snapshots = tuple(
        sorted(
            snapshots,
            key=lambda snapshot: (
                snapshot.race.scheduled_start_at,
                snapshot.internal_race_id,
            ),
        )
    )
    seen_race_ids: set[int] = set()
    for snapshot in canonical_snapshots:
        if snapshot.internal_race_id in seen_race_ids:
            raise ValueError("snapshots must not contain duplicate internal_race_id values")
        seen_race_ids.add(snapshot.internal_race_id)

    race_ids = {snapshot.internal_race_id for snapshot in canonical_snapshots}
    if set(budgets) != race_ids:
        raise ValueError("budget race IDs must exactly match snapshot internal race IDs")

    for snapshot in canonical_snapshots:
        if snapshot.identity.dataset_id != run_context.dataset_id:
            raise SimulationValidationError(
                snapshot.internal_race_id,
                "run_context.dataset_id",
                "run_context.dataset_id does not match snapshot.identity.dataset_id",
            )

    results: list[SimulationBetPlanSnapshot] = []
    for snapshot in canonical_snapshots:
        result = execute_and_persist_historical_bet_plan(
            snapshot=snapshot,
            run_context=run_context,
            strategy_identity=strategy_identity,
            budget=budgets[snapshot.internal_race_id],
            snapshot_repository=snapshot_repository,
        )
        results.append(result)
    return tuple(results)
