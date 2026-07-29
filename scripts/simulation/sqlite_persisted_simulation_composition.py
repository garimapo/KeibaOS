"""Caller-owned SQLite composition for one persisted simulation run."""

from __future__ import annotations

import sqlite3

from scripts.prediction.allocation_policy import AllocationPolicyConfig
from scripts.prediction.prediction_pipeline import PipelineConfig, PredictionPipeline
from scripts.simulation.bet_plan_builder import SimulationBetPlanBuilder
from scripts.simulation.fixed_stake_allocator import FixedStakeBetAllocator
from scripts.simulation.models import SimulationRunContext, StrategyIdentity
from scripts.simulation.persisted_bet_plan_service import PersistedSimulationBetPlanService
from scripts.simulation.persisted_executor import PersistedRaceSimulationExecutor
from scripts.simulation.persisted_simulation_bet_source import PersistedSimulationBetSource
from scripts.simulation.persisted_simulation_run_service import (
    PersistedSimulationRunService,
)
from scripts.simulation.repositories.sqlite import (
    SQLitePayoutRepository,
    SQLiteRaceResultRepository,
)
from scripts.simulation.repositories.sqlite_bet_plan_snapshot_repository import (
    SQLiteSimulationBetPlanSnapshotRepository,
)
from scripts.simulation.repositories.sqlite_race_entry_source import SQLiteRaceEntrySource
from scripts.simulation.repository_backed_persisted_settlement_source import (
    RepositoryBackedPersistedRaceSettlementSource,
)
from scripts.simulation.repository_backed_selection_resolver import (
    RepositoryBackedRaceEntrySelectionResolver,
)
from scripts.simulation.simulator import Simulator


def build_sqlite_persisted_simulation_run_service(
    *,
    connection: sqlite3.Connection,
    run_context: SimulationRunContext,
    strategy_identity: StrategyIdentity,
    prediction_pipeline: PredictionPipeline,
) -> PersistedSimulationRunService:
    """Construct the coherent persisted simulation chain on one caller connection."""
    if not isinstance(connection, sqlite3.Connection):
        raise ValueError("connection must be sqlite3.Connection")
    if type(run_context) is not SimulationRunContext:
        raise ValueError("run_context must be a SimulationRunContext")
    if type(strategy_identity) is not StrategyIdentity:
        raise ValueError("strategy_identity must be a StrategyIdentity")
    if type(prediction_pipeline) is not PredictionPipeline:
        raise ValueError("prediction_pipeline must be a PredictionPipeline")

    config = prediction_pipeline.config
    if type(config) is not PipelineConfig:
        raise ValueError("prediction_pipeline.config must be a PipelineConfig")
    if config.strategy_config is not strategy_identity.strategy_config:
        raise ValueError(
            "prediction_pipeline.config.strategy_config "
            "must be strategy_identity.strategy_config"
        )
    policy_config = strategy_identity.strategy_config.allocation_policy
    if policy_config is None:
        raise ValueError(
            "strategy_identity.strategy_config.allocation_policy is required"
        )
    if type(policy_config) is not AllocationPolicyConfig:
        raise ValueError("allocation_policy must be an AllocationPolicyConfig")

    snapshot_repository = SQLiteSimulationBetPlanSnapshotRepository(
        connection=connection,
    )
    race_entry_source = SQLiteRaceEntrySource(connection=connection)
    selection_resolver = RepositoryBackedRaceEntrySelectionResolver(
        race_entry_source=race_entry_source,
    )
    plan_builder = SimulationBetPlanBuilder(selection_resolver=selection_resolver)
    allocator = FixedStakeBetAllocator(policy_config=policy_config)
    bet_plan_service = PersistedSimulationBetPlanService(
        run_context=run_context,
        strategy_identity=strategy_identity,
        prediction_pipeline=prediction_pipeline,
        allocator=allocator,
        plan_builder=plan_builder,
        snapshot_repository=snapshot_repository,
    )
    bet_source = PersistedSimulationBetSource(
        run_context=run_context,
        snapshot_source=snapshot_repository,
    )
    race_result_repository = SQLiteRaceResultRepository(connection)
    payout_repository = SQLitePayoutRepository(connection)
    settlement_source = RepositoryBackedPersistedRaceSettlementSource(
        bet_source=bet_source,
        race_result_repository=race_result_repository,
        payout_repository=payout_repository,
    )
    executor = PersistedRaceSimulationExecutor(
        strategy_identity=strategy_identity,
        settlement_source=settlement_source,
    )
    simulator = Simulator(
        strategy_identity=strategy_identity,
        race_executor=executor,
    )
    return PersistedSimulationRunService(
        bet_plan_service=bet_plan_service,
        simulator=simulator,
    )
