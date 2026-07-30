"""Assembly boundary for persisted-simulation application inputs."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
import math
from pathlib import Path
import re
from types import MappingProxyType

from scripts.prediction.allocation_policy import AllocationPolicyConfig
from scripts.prediction.bet_strategy import (
    RuleBasedBetStrategy,
    SelectionStyle,
    SortCondition,
    StrategyConfig,
)
from scripts.prediction.prediction_pipeline import PipelineConfig, PredictionPipeline
from scripts.prediction.track_engine import TrackEngine
from scripts.simulation.models import (
    SimulationRunContext,
    StrategyIdentity,
    build_strategy_identity,
)
from scripts.simulation.persisted_simulation_request_document import (
    PersistedSimulationRequestDocument,
)
from scripts.simulation.stake_allocation import BetStakeBudget


_RUN_CONTEXT_KEYS = frozenset({"run_id", "dataset_id", "started_at", "target_commit_id"})
_STRATEGY_KEYS = frozenset(
    {
        "strategy_name",
        "allowed_bet_types",
        "max_bet_count",
        "selection_style",
        "min_combination_score",
        "max_candidates",
        "sort_condition",
        "allocation_policy",
    }
)
_ALLOCATION_POLICY_KEYS = frozenset({"policy_name", "policy_version", "parameters"})
_FIXED_STAKE_KEYS = frozenset({"stake_amount"})
_PIPELINE_KEYS = frozenset({"track_reference_date"})
_BUDGET_KEYS = frozenset({"total_amount"})
_SUPPORTED_BET_TYPES = frozenset({"単勝", "馬連", "ワイド", "3連複"})
_CANONICAL_RACE_ID = re.compile(r"[1-9][0-9]*\Z")

__all__ = [
    "PersistedSimulationApplicationInputs",
    "assemble_persisted_simulation_application_inputs",
]


@dataclass(frozen=True)
class PersistedSimulationApplicationInputs:
    """Immutable application dependencies assembled from a request document."""

    database_path: Path
    run_context: SimulationRunContext
    strategy_identity: StrategyIdentity
    prediction_pipeline: PredictionPipeline
    budgets_by_race_id: Mapping[int, BetStakeBudget]

    def __post_init__(self) -> None:
        if not isinstance(self.database_path, Path):
            raise ValueError("database_path must be a Path")
        if type(self.run_context) is not SimulationRunContext:
            raise ValueError("run_context must be a SimulationRunContext")
        if type(self.strategy_identity) is not StrategyIdentity:
            raise ValueError("strategy_identity must be a StrategyIdentity")
        if type(self.prediction_pipeline) is not PredictionPipeline:
            raise ValueError("prediction_pipeline must be a PredictionPipeline")
        if not isinstance(self.budgets_by_race_id, Mapping):
            raise ValueError("budgets_by_race_id must be a Mapping")

        pipeline_config = self.prediction_pipeline.config
        if type(pipeline_config) is not PipelineConfig:
            raise ValueError("prediction_pipeline.config must be a PipelineConfig")
        if pipeline_config.strategy_config is not self.strategy_identity.strategy_config:
            raise ValueError(
                "prediction_pipeline strategy_config must be strategy_identity.strategy_config"
            )
        if type(self.strategy_identity.strategy_config.allocation_policy) is not AllocationPolicyConfig:
            raise ValueError("strategy_identity allocation_policy must be an AllocationPolicyConfig")

        copied_budgets: dict[int, BetStakeBudget] = {}
        for race_id, budget in self.budgets_by_race_id.items():
            if type(race_id) is not int or race_id <= 0:
                raise ValueError("budgets_by_race_id keys must be positive integers")
            if type(budget) is not BetStakeBudget:
                raise ValueError("budgets_by_race_id values must be BetStakeBudget")
            copied_budgets[race_id] = budget
        object.__setattr__(
            self,
            "budgets_by_race_id",
            MappingProxyType(dict(sorted(copied_budgets.items()))),
        )


def assemble_persisted_simulation_application_inputs(
    *,
    document: PersistedSimulationRequestDocument,
) -> PersistedSimulationApplicationInputs:
    """Build application-level inputs without reading files or running a simulation."""

    if type(document) is not PersistedSimulationRequestDocument:
        raise ValueError("document must be a PersistedSimulationRequestDocument")

    run_context = _assemble_run_context(document.run_context)
    strategy_identity = _assemble_strategy_identity(document.strategy)
    prediction_pipeline = _assemble_prediction_pipeline(
        pipeline=document.pipeline,
        strategy_config=strategy_identity.strategy_config,
    )
    budgets_by_race_id = _assemble_budgets(document.budgets_by_race_id)
    return PersistedSimulationApplicationInputs(
        database_path=document.database_path,
        run_context=run_context,
        strategy_identity=strategy_identity,
        prediction_pipeline=prediction_pipeline,
        budgets_by_race_id=budgets_by_race_id,
    )


def _assemble_run_context(run_context: Mapping[str, object]) -> SimulationRunContext:
    if not isinstance(run_context, Mapping) or set(run_context) != _RUN_CONTEXT_KEYS:
        raise ValueError("run_context keys must exactly match the run context schema")
    run_id = _non_empty_text(run_context["run_id"], "run_context.run_id")
    dataset_id = _non_empty_text(run_context["dataset_id"], "run_context.dataset_id")
    target_commit_id = _non_empty_text(
        run_context["target_commit_id"],
        "run_context.target_commit_id",
    )
    started_at = _parse_aware_datetime(run_context["started_at"])
    return SimulationRunContext(
        run_id=run_id,
        dataset_id=dataset_id,
        started_at=started_at,
        target_commit_id=target_commit_id,
    )


def _assemble_strategy_identity(strategy: Mapping[str, object]) -> StrategyIdentity:
    if not isinstance(strategy, Mapping) or set(strategy) != _STRATEGY_KEYS:
        raise ValueError("strategy keys must exactly match the strategy schema")
    strategy_name = strategy["strategy_name"]
    if type(strategy_name) is not str or strategy_name != "RuleBasedBetStrategy":
        raise ValueError("strategy.strategy_name must be RuleBasedBetStrategy")

    allowed_bet_types = strategy["allowed_bet_types"]
    if type(allowed_bet_types) is not tuple:
        raise ValueError("strategy.allowed_bet_types must be an array")
    if (
        any(type(bet_type) is not str or bet_type not in _SUPPORTED_BET_TYPES for bet_type in allowed_bet_types)
        or len(set(allowed_bet_types)) != len(allowed_bet_types)
    ):
        raise ValueError("strategy.allowed_bet_types must contain unique supported bet types")

    max_bet_count = _non_negative_integer(
        strategy["max_bet_count"],
        "strategy.max_bet_count must be a non-negative integer",
    )
    max_candidates = _non_negative_integer(
        strategy["max_candidates"],
        "strategy.max_candidates must be a non-negative integer",
    )
    selection_style = _selection_style(strategy["selection_style"])
    min_combination_score = _finite_score(strategy["min_combination_score"])
    sort_condition = _sort_condition(strategy["sort_condition"])
    allocation_policy = _assemble_allocation_policy(strategy["allocation_policy"])

    strategy_config = StrategyConfig(
        allowed_bet_types=frozenset(allowed_bet_types),
        max_bet_count=max_bet_count,
        selection_style=selection_style,
        min_combination_score=min_combination_score,
        max_candidates=max_candidates,
        sort_condition=sort_condition,
        allocation_policy=allocation_policy,
    )
    return build_strategy_identity(strategy_name, strategy_config)


def _assemble_allocation_policy(value: object) -> AllocationPolicyConfig:
    if not isinstance(value, Mapping):
        raise ValueError("strategy.allocation_policy must be an object")
    if set(value) != _ALLOCATION_POLICY_KEYS:
        raise ValueError("strategy.allocation_policy keys must exactly match the allocation policy schema")
    if value["policy_name"] != "fixed_stake_per_recommendation":
        raise ValueError("strategy.allocation_policy.policy_name is unsupported")
    if type(value["policy_version"]) is not str or value["policy_version"] != "1":
        raise ValueError("strategy.allocation_policy.policy_version is unsupported")
    parameters = value["parameters"]
    if not isinstance(parameters, Mapping):
        raise ValueError("strategy.allocation_policy.parameters must be an object")
    if set(parameters) != _FIXED_STAKE_KEYS:
        raise ValueError("strategy.allocation_policy.parameters keys must exactly match the fixed stake schema")
    stake_amount = parameters["stake_amount"]
    if type(stake_amount) is not int or stake_amount <= 0 or stake_amount % 100 != 0:
        raise ValueError(
            "strategy.allocation_policy.parameters.stake_amount must be a positive multiple of 100"
        )
    return AllocationPolicyConfig(
        policy_name="fixed_stake_per_recommendation",
        policy_version="1",
        parameters={"stake_amount": stake_amount},
    )


def _assemble_prediction_pipeline(
    *,
    pipeline: Mapping[str, object],
    strategy_config: StrategyConfig,
) -> PredictionPipeline:
    if not isinstance(pipeline, Mapping) or set(pipeline) != _PIPELINE_KEYS:
        raise ValueError("pipeline keys must exactly match the pipeline schema")
    reference_date = _parse_iso_date(pipeline["track_reference_date"])
    track_engine = TrackEngine(reference_date=reference_date)
    pipeline_config = PipelineConfig(
        track_engine=track_engine,
        bet_strategy=RuleBasedBetStrategy(),
        strategy_config=strategy_config,
    )
    return PredictionPipeline(config=pipeline_config)


def _assemble_budgets(budgets: Mapping[str, object]) -> dict[int, BetStakeBudget]:
    if not isinstance(budgets, Mapping):
        raise ValueError("budgets_by_race_id keys must be canonical positive integer strings")
    assembled: dict[int, BetStakeBudget] = {}
    for race_id_text, budget_data in budgets.items():
        if type(race_id_text) is not str or _CANONICAL_RACE_ID.fullmatch(race_id_text) is None:
            raise ValueError("budgets_by_race_id keys must be canonical positive integer strings")
        if not isinstance(budget_data, Mapping):
            raise ValueError("budgets_by_race_id values must be objects")
        if set(budget_data) != _BUDGET_KEYS:
            raise ValueError("budget keys must exactly match the budget schema")
        total_amount = budget_data["total_amount"]
        if type(total_amount) is not int or total_amount < 0 or total_amount % 100 != 0:
            raise ValueError("budget.total_amount must be a non-negative multiple of 100")
        assembled[int(race_id_text)] = BetStakeBudget(total_amount=total_amount)
    return assembled


def _non_empty_text(value: object, field_name: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _parse_aware_datetime(value: object) -> datetime:
    error_message = "run_context.started_at must be an ISO 8601 timezone-aware datetime"
    if type(value) is not str:
        raise ValueError(error_message)
    source_value = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(source_value)
    except ValueError as error:
        raise ValueError(error_message) from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(error_message)
    return parsed


def _non_negative_integer(value: object, error_message: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(error_message)
    return value


def _selection_style(value: object) -> SelectionStyle:
    if type(value) is not str or value not in {"box", "formation"}:
        raise ValueError("strategy.selection_style must be box or formation")
    return SelectionStyle(value)


def _finite_score(value: object) -> float:
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("strategy.min_combination_score must be finite")
    return float(value)


def _sort_condition(value: object) -> SortCondition:
    if type(value) is not str or value not in {
        "generator_rank",
        "combination_score",
        "prediction_score",
        "estimated_probability",
    }:
        raise ValueError("strategy.sort_condition is unsupported")
    return SortCondition(value)


def _parse_iso_date(value: object) -> date:
    error_message = "pipeline.track_reference_date must be an ISO date"
    if type(value) is not str:
        raise ValueError(error_message)
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(error_message) from error
