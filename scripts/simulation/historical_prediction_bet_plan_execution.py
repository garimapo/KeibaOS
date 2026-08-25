"""Execute and persist one causally complete historical prediction bet plan."""

from __future__ import annotations

from scripts.prediction.bet_strategy import RuleBasedBetStrategy
from scripts.prediction.prediction_pipeline import (
    PipelineConfig,
    PredictionPipeline,
    build_historical_prediction_pipeline,
)
from scripts.simulation.bet_plan_builder import SimulationBetPlanBuilder
from scripts.simulation.bet_plan_snapshot import SimulationBetPlanSnapshot
from scripts.simulation.bet_plan_snapshot_repository import SimulationBetPlanSnapshotRepository
from scripts.simulation.exact_race_entry_selection_resolver import (
    ExactRaceEntrySelectionResolver,
)
from scripts.simulation.fixed_stake_allocator import FixedStakeBetAllocator
from scripts.simulation.historical_input_snapshot_simulation_adapter import (
    build_simulation_race_input_from_historical_snapshot,
)
from scripts.simulation.historical_input_snapshots import HistoricalInputSnapshot
from scripts.simulation.models import SimulationRunContext, StrategyIdentity
from scripts.simulation.persisted_bet_plan_service import PersistedSimulationBetPlanService
from scripts.simulation.stake_allocation import BetStakeBudget
from scripts.simulation.validation import SimulationValidationError


__all__ = (
    "execute_and_persist_historical_bet_plan",
)


def execute_and_persist_historical_bet_plan(
    *,
    snapshot: HistoricalInputSnapshot,
    run_context: SimulationRunContext,
    strategy_identity: StrategyIdentity,
    budget: BetStakeBudget,
    snapshot_repository: SimulationBetPlanSnapshotRepository,
) -> SimulationBetPlanSnapshot:
    """Build and save one race's exact historical bet-plan snapshot."""

    if type(snapshot) is not HistoricalInputSnapshot:
        raise ValueError("snapshot must be a HistoricalInputSnapshot")
    if type(run_context) is not SimulationRunContext:
        raise ValueError("run_context must be a SimulationRunContext")
    if type(strategy_identity) is not StrategyIdentity:
        raise ValueError("strategy_identity must be a StrategyIdentity")
    if type(budget) is not BetStakeBudget:
        raise ValueError("budget must be a BetStakeBudget")
    if isinstance(snapshot_repository, type) or not callable(
        getattr(snapshot_repository, "save_snapshot", None)
    ):
        raise ValueError("snapshot_repository must provide a callable save_snapshot method")
    if strategy_identity.strategy_name != RuleBasedBetStrategy.__name__:
        raise ValueError("strategy_identity.strategy_name must be RuleBasedBetStrategy")
    if run_context.dataset_id != snapshot.identity.dataset_id:
        raise SimulationValidationError(
            snapshot.internal_race_id,
            "run_context.dataset_id",
            "run_context.dataset_id does not match snapshot.identity.dataset_id",
        )

    race_input = build_simulation_race_input_from_historical_snapshot(snapshot=snapshot)
    prediction_pipeline = build_historical_prediction_pipeline(
        target_race_date=race_input.target_race_date,
        strategy_config=strategy_identity.strategy_config,
    )
    if type(prediction_pipeline) is not PredictionPipeline:
        raise ValueError("historical prediction pipeline must be a PredictionPipeline")
    if type(prediction_pipeline.config) is not PipelineConfig:
        raise ValueError("historical prediction pipeline config must be a PipelineConfig")
    if prediction_pipeline.config.strategy_config is not strategy_identity.strategy_config:
        raise ValueError("historical prediction pipeline strategy_config identity mismatch")
    if type(prediction_pipeline.config.bet_strategy) is not RuleBasedBetStrategy:
        raise ValueError("historical prediction pipeline must use RuleBasedBetStrategy")

    allocator = FixedStakeBetAllocator(
        policy_config=strategy_identity.strategy_config.allocation_policy
    )
    selection_resolver = ExactRaceEntrySelectionResolver(
        race_id=race_input.race_id,
        allowed_race_entry_ids=tuple(race_input.pipeline_input.horse_past_races.keys()),
    )
    plan_builder = SimulationBetPlanBuilder(selection_resolver=selection_resolver)
    service = PersistedSimulationBetPlanService(
        run_context=run_context,
        strategy_identity=strategy_identity,
        prediction_pipeline=prediction_pipeline,
        allocator=allocator,
        plan_builder=plan_builder,
        snapshot_repository=snapshot_repository,
    )
    return service.build_and_save(race_input=race_input, budget=budget)
