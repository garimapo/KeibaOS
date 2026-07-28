"""Adapter for loading the immutable persisted bet plan of one simulation race."""

from __future__ import annotations

from .bet_plan_identity import SimulationBetPlanIdentity
from .bet_plan_snapshot import SimulationBetPlanSnapshot
from .bet_plan_snapshot_repository import SimulationBetPlanSnapshotSource
from .bet_source import SimulationBetSource
from .models import SimulationBet, SimulationRaceInput, SimulationRunContext, StrategyIdentity
from .validation import SimulationValidationError


class PersistedSimulationBetSource:
    """Load one already-planned immutable bet tuple through an injected Snapshot Source."""

    __slots__ = ("_run_context", "_snapshot_source")

    def __init__(
        self,
        *,
        run_context: SimulationRunContext,
        snapshot_source: SimulationBetPlanSnapshotSource,
    ) -> None:
        source_method = getattr(snapshot_source, "load_snapshot", None)
        if not isinstance(run_context, SimulationRunContext):
            raise ValueError("run_context must be a SimulationRunContext")
        if not callable(source_method):
            raise ValueError("snapshot_source must provide a callable load_snapshot method")
        self._run_context = run_context
        self._snapshot_source = snapshot_source

    def load_bets(
        self,
        *,
        race_input: SimulationRaceInput,
        strategy_identity: StrategyIdentity,
    ) -> tuple[SimulationBet, ...]:
        if not isinstance(race_input, SimulationRaceInput):
            raise ValueError("race_input must be a SimulationRaceInput")
        if not isinstance(strategy_identity, StrategyIdentity):
            raise ValueError("strategy_identity must be a StrategyIdentity")

        identity = SimulationBetPlanIdentity(
            run_id=self._run_context.run_id,
            race_id=race_input.race_id,
            strategy_id=strategy_identity.strategy_id,
            strategy_config_hash=strategy_identity.strategy_config_hash,
            information_cutoff=race_input.information_cutoff,
        )
        snapshot = self._snapshot_source.load_snapshot(identity=identity)
        if snapshot is None:
            raise SimulationValidationError(
                race_input.race_id,
                "simulation_bet_plan_snapshot",
                "snapshot was not found",
            )
        if not isinstance(snapshot, SimulationBetPlanSnapshot):
            raise SimulationValidationError(
                race_input.race_id,
                "simulation_bet_plan_snapshot",
                "snapshot has an invalid type",
            )
        if snapshot.identity != identity:
            raise SimulationValidationError(
                race_input.race_id,
                "simulation_bet_plan_snapshot",
                "snapshot identity does not match requested identity",
            )
        return snapshot.bets
