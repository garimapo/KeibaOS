"""Expose historical settlement summaries only when every race is final."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

from scripts.simulation.bet_plan_snapshot_repository import SimulationBetPlanSnapshotSource
from scripts.simulation.historical_input_snapshots import HistoricalInputSnapshot
from scripts.simulation.historical_settlement_simulation import (
    execute_historical_settlement_simulation,
)
from scripts.simulation.models import SimulationRunContext, SimulationSummary, StrategyIdentity
from scripts.simulation.repositories.interfaces import PayoutRepository, RaceResultRepository

__all__ = (
    "FinalHistoricalSettlementNotReadyError",
    "execute_final_historical_settlement_simulation",
)


class FinalHistoricalSettlementNotReadyError(ValueError):
    """The delegated historical settlement summary contains non-final race states."""


def execute_final_historical_settlement_simulation(
    *,
    snapshots: tuple[HistoricalInputSnapshot, ...],
    run_context: SimulationRunContext,
    strategy_identity: StrategyIdentity,
    settlement_cutoffs_by_race_id: Mapping[int, datetime],
    bet_plan_snapshot_source: SimulationBetPlanSnapshotSource,
    race_result_repository: RaceResultRepository,
    payout_repository: PayoutRepository,
) -> SimulationSummary:
    """Return the delegated summary only when every canonical race is final."""

    summary = execute_historical_settlement_simulation(
        snapshots=snapshots,
        run_context=run_context,
        strategy_identity=strategy_identity,
        settlement_cutoffs_by_race_id=settlement_cutoffs_by_race_id,
        bet_plan_snapshot_source=bet_plan_snapshot_source,
        race_result_repository=race_result_repository,
        payout_repository=payout_repository,
    )
    if (
        summary.settled_race_count + summary.no_bet_race_count == summary.race_count
        and summary.unsettled_race_count == 0
        and summary.void_race_count == 0
        and summary.error_race_count == 0
        and summary.unsupported_race_count == 0
    ):
        return summary
    raise FinalHistoricalSettlementNotReadyError(
        "historical settlement is not final: "
        f"race_count={summary.race_count}, settled={summary.settled_race_count}, "
        f"no_bet={summary.no_bet_race_count}, unsettled={summary.unsettled_race_count}, "
        f"void={summary.void_race_count}, error={summary.error_race_count}, "
        f"unsupported={summary.unsupported_race_count}"
    )
