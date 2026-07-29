"""Application runner for a file-backed persisted SQLite simulation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
import sqlite3

from scripts.migrations.runner import apply_migrations
from scripts.prediction.prediction_pipeline import PredictionPipeline
from scripts.simulation.models import (
    SimulationRaceInput,
    SimulationRunContext,
    SimulationSummary,
    StrategyIdentity,
)
from scripts.simulation.sqlite_persisted_simulation_composition import (
    build_sqlite_persisted_simulation_run_service,
)
from scripts.simulation.stake_allocation import BetStakeBudget


def run_sqlite_persisted_simulation(
    *,
    database_path: str | Path,
    run_context: SimulationRunContext,
    strategy_identity: StrategyIdentity,
    prediction_pipeline: PredictionPipeline,
    race_inputs: Sequence[SimulationRaceInput],
    budgets_by_race_id: Mapping[int, BetStakeBudget],
) -> SimulationSummary:
    """Run one persisted simulation on one runner-owned SQLite connection."""
    if not isinstance(database_path, (str, Path)):
        raise ValueError("database_path must be a non-empty path")
    database_path_value = str(database_path)
    if not database_path_value.strip() or "\x00" in database_path_value:
        raise ValueError("database_path must be a non-empty path")
    if type(run_context) is not SimulationRunContext:
        raise ValueError("run_context must be a SimulationRunContext")
    if type(strategy_identity) is not StrategyIdentity:
        raise ValueError("strategy_identity must be a StrategyIdentity")
    if type(prediction_pipeline) is not PredictionPipeline:
        raise ValueError("prediction_pipeline must be a PredictionPipeline")
    if (
        isinstance(race_inputs, (str, bytes, bytearray, Mapping))
        or not isinstance(race_inputs, Sequence)
    ):
        raise ValueError("race_inputs must be a Sequence")
    if not isinstance(budgets_by_race_id, Mapping):
        raise ValueError("budgets_by_race_id must be a Mapping")

    race_input_values = tuple(race_inputs)
    budget_values = dict(budgets_by_race_id)

    connection = sqlite3.connect(database_path_value)
    try:
        apply_migrations(connection)
        service = build_sqlite_persisted_simulation_run_service(
            connection=connection,
            run_context=run_context,
            strategy_identity=strategy_identity,
            prediction_pipeline=prediction_pipeline,
        )
        return service.run(
            race_inputs=race_input_values,
            budgets_by_race_id=budget_values,
        )
    finally:
        connection.close()
