"""Compose ordered historical settlement into one simulation summary."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

from scripts.prediction.bet_strategy import RuleBasedBetStrategy
from scripts.simulation.bet_plan_snapshot_repository import SimulationBetPlanSnapshotSource
from scripts.simulation.historical_input_snapshot_simulation_adapter import (
    build_simulation_race_input_from_historical_snapshot,
)
from scripts.simulation.historical_input_snapshots import HistoricalInputSnapshot
from scripts.simulation.historical_persisted_race_settlement_source import (
    HistoricalPersistedRaceSettlementSource,
)
from scripts.simulation.models import (
    SimulationRunContext,
    SimulationSummary,
    StrategyIdentity,
)
from scripts.simulation.persisted_executor import PersistedRaceSimulationExecutor
from scripts.simulation.persisted_simulation_bet_source import PersistedSimulationBetSource
from scripts.simulation.repositories.interfaces import PayoutRepository, RaceResultRepository
from scripts.simulation.simulator import Simulator
from scripts.simulation.validation import SimulationValidationError


__all__ = (
    "execute_historical_settlement_simulation",
)


def execute_historical_settlement_simulation(
    *,
    snapshots: tuple[HistoricalInputSnapshot, ...],
    run_context: SimulationRunContext,
    strategy_identity: StrategyIdentity,
    settlement_cutoffs_by_race_id: Mapping[int, datetime],
    bet_plan_snapshot_source: SimulationBetPlanSnapshotSource,
    race_result_repository: RaceResultRepository,
    payout_repository: PayoutRepository,
) -> SimulationSummary:
    """Settle exact persisted historical plans in canonical race order."""

    if type(snapshots) is not tuple:
        raise ValueError("snapshots must be an exact tuple")
    snapshot_types = tuple(type(snapshot) is HistoricalInputSnapshot for snapshot in snapshots)
    if not all(snapshot_types):
        raise ValueError("snapshots must contain exact HistoricalInputSnapshot values")
    if type(run_context) is not SimulationRunContext:
        raise ValueError("run_context must be a SimulationRunContext")
    if type(strategy_identity) is not StrategyIdentity:
        raise ValueError("strategy_identity must be a StrategyIdentity")
    if isinstance(settlement_cutoffs_by_race_id, type) or not isinstance(
        settlement_cutoffs_by_race_id,
        Mapping,
    ):
        raise ValueError("settlement_cutoffs_by_race_id must be a Mapping")

    cutoffs = dict(settlement_cutoffs_by_race_id)
    for race_id, cutoff in cutoffs.items():
        if type(race_id) is not int or race_id <= 0:
            raise ValueError("settlement cutoff race IDs must be positive integers")
        if (
            not isinstance(cutoff, datetime)
            or cutoff.tzinfo is None
            or cutoff.utcoffset() is None
        ):
            raise ValueError("settlement cutoffs must be timezone-aware datetimes")

    if isinstance(bet_plan_snapshot_source, type) or not callable(
        getattr(bet_plan_snapshot_source, "load_snapshot", None)
    ):
        raise ValueError("bet_plan_snapshot_source must provide a callable load_snapshot method")
    if isinstance(race_result_repository, type) or not callable(
        getattr(race_result_repository, "get_race_result", None)
    ):
        raise ValueError(
            "race_result_repository must provide a callable get_race_result method"
        )
    if isinstance(payout_repository, type) or not callable(
        getattr(payout_repository, "get_latest_payout_publication", None)
    ):
        raise ValueError(
            "payout_repository must provide a callable get_latest_payout_publication method"
        )
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
    if set(cutoffs) != race_ids:
        raise ValueError(
            "settlement cutoff race IDs must exactly match snapshot internal race IDs"
        )

    for snapshot in canonical_snapshots:
        if snapshot.identity.dataset_id != run_context.dataset_id:
            raise SimulationValidationError(
                snapshot.internal_race_id,
                "run_context.dataset_id",
                "run_context.dataset_id does not match snapshot.identity.dataset_id",
            )

    race_inputs = tuple(
        build_simulation_race_input_from_historical_snapshot(snapshot=snapshot)
        for snapshot in canonical_snapshots
    )
    bet_source = PersistedSimulationBetSource(
        run_context=run_context,
        snapshot_source=bet_plan_snapshot_source,
    )
    settlement_source = HistoricalPersistedRaceSettlementSource(
        bet_source=bet_source,
        race_result_repository=race_result_repository,
        payout_repository=payout_repository,
        settlement_cutoffs_by_race_id=cutoffs,
    )
    executor = PersistedRaceSimulationExecutor(
        strategy_identity=strategy_identity,
        settlement_source=settlement_source,
    )
    simulator = Simulator(
        strategy_identity=strategy_identity,
        race_executor=executor,
    )
    return simulator.run(race_inputs=race_inputs)
