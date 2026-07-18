"""Ver0.8 の回収率シミュレーション用ドメインモデル。"""

from .models import (
    BetTypeSummary,
    InputAuditEntry,
    InputSnapshotAudit,
    ImmutableRacePredictionInput,
    PayoutEntry,
    PayoutTable,
    RaceResultEntry,
    RaceResultTable,
    RefundEntry,
    SettlementStatus,
    SimulationBet,
    SimulationRaceInput,
    SimulationReport,
    SimulationResult,
    SimulationRunContext,
    SimulationRunMetadata,
    SimulationSummary,
    StrategyIdentity,
    build_strategy_identity,
    generate_strategy_id,
)
from .validation import SimulationValidationError, validate_simulation_race_input
from .serialization import to_json_compatible

__all__ = [
    "BetTypeSummary", "ImmutableRacePredictionInput", "InputAuditEntry", "InputSnapshotAudit", "PayoutEntry",
    "PayoutTable", "RaceResultEntry", "RaceResultTable", "RefundEntry",
    "SettlementStatus", "SimulationBet", "SimulationRaceInput", "SimulationReport",
    "SimulationResult", "SimulationRunContext", "SimulationRunMetadata",
    "SimulationSummary", "SimulationValidationError", "StrategyIdentity",
    "build_strategy_identity", "generate_strategy_id", "validate_simulation_race_input",
    "to_json_compatible",
]
