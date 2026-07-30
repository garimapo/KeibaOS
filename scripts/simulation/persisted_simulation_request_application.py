"""Thin application boundary for persisted simulation request documents."""

from __future__ import annotations

from pathlib import Path

from scripts.simulation.models import SimulationSummary
from scripts.simulation.persisted_simulation_application_inputs import (
    assemble_persisted_simulation_application_inputs,
)
from scripts.simulation.persisted_simulation_race_inputs import (
    assemble_persisted_simulation_race_inputs,
)
from scripts.simulation.persisted_simulation_request_document import (
    load_persisted_simulation_request_document,
)
from scripts.simulation.sqlite_persisted_simulation_application import (
    run_sqlite_persisted_simulation,
)


def run_persisted_simulation_request(
    *,
    request_path: str | Path,
) -> SimulationSummary:
    """Execute the approved persisted-simulation request call chain."""
    document = load_persisted_simulation_request_document(
        request_path=request_path,
    )
    application_inputs = assemble_persisted_simulation_application_inputs(
        document=document,
    )
    race_inputs = assemble_persisted_simulation_race_inputs(
        document=document,
        application_inputs=application_inputs,
    )
    return run_sqlite_persisted_simulation(
        database_path=application_inputs.database_path,
        run_context=application_inputs.run_context,
        strategy_identity=application_inputs.strategy_identity,
        prediction_pipeline=application_inputs.prediction_pipeline,
        race_inputs=race_inputs,
        budgets_by_race_id=application_inputs.budgets_by_race_id,
    )
