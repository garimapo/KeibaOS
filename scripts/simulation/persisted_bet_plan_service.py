"""Application service for building and persisting one immutable bet-plan snapshot."""

from __future__ import annotations

from collections.abc import Sequence

from scripts.models import Prediction
from scripts.prediction.allocation_policy import (
    AllocationPolicyIdentity,
    build_allocation_policy_identity,
)
from scripts.prediction.bet_strategy import BetPlan
from scripts.prediction.prediction_pipeline import (
    PipelineConfig,
    PipelineResult,
    PredictionPipeline,
)
from scripts.simulation.bet_plan_builder import SimulationBetPlanBuilder
from scripts.simulation.bet_plan_identity import SimulationBetPlanIdentity
from scripts.simulation.bet_plan_snapshot import SimulationBetPlanSnapshot
from scripts.simulation.bet_plan_snapshot_repository import SimulationBetPlanSnapshotRepository
from scripts.simulation.models import (
    SimulationRaceInput,
    SimulationRunContext,
    StrategyIdentity,
)
from scripts.simulation.stake_allocation import (
    BetAllocationPlan,
    BetStakeAllocator,
    BetStakeBudget,
)
from scripts.simulation.validation import SimulationValidationError


class PersistedSimulationBetPlanService:
    """Build and save the fixed simulation bet plan for one validated race input."""

    __slots__ = (
        "_run_context",
        "_strategy_identity",
        "_prediction_pipeline",
        "_allocator",
        "_plan_builder",
        "_snapshot_repository",
    )

    def __init__(
        self,
        *,
        run_context: SimulationRunContext,
        strategy_identity: StrategyIdentity,
        prediction_pipeline: PredictionPipeline,
        allocator: BetStakeAllocator,
        plan_builder: SimulationBetPlanBuilder,
        snapshot_repository: SimulationBetPlanSnapshotRepository,
    ) -> None:
        if not isinstance(run_context, SimulationRunContext):
            raise ValueError("run_context must be a SimulationRunContext")
        if not isinstance(strategy_identity, StrategyIdentity):
            raise ValueError("strategy_identity must be a StrategyIdentity")
        if not isinstance(prediction_pipeline, PredictionPipeline):
            raise ValueError("prediction_pipeline must be a PredictionPipeline")
        if not isinstance(plan_builder, SimulationBetPlanBuilder):
            raise ValueError("plan_builder must be a SimulationBetPlanBuilder")
        self._validate_collaborator(allocator, "allocate", "allocator")
        self._validate_collaborator(
            snapshot_repository,
            "save_snapshot",
            "snapshot_repository",
        )
        self._run_context = run_context
        self._strategy_identity = strategy_identity
        self._prediction_pipeline = prediction_pipeline
        self._allocator = allocator
        self._plan_builder = plan_builder
        self._snapshot_repository = snapshot_repository

    def build_and_save(
        self,
        *,
        race_input: SimulationRaceInput,
        budget: BetStakeBudget,
    ) -> SimulationBetPlanSnapshot:
        if not isinstance(race_input, SimulationRaceInput):
            raise ValueError("race_input must be a SimulationRaceInput")
        if not isinstance(budget, BetStakeBudget):
            raise ValueError("budget must be a BetStakeBudget")

        config = self._prediction_pipeline.config
        if not isinstance(config, PipelineConfig):
            self._fail(race_input, "prediction_pipeline", "config must be a PipelineConfig")
        if config.strategy_config != self._strategy_identity.strategy_config:
            self._fail(
                race_input,
                "prediction_pipeline",
                "strategy_config does not match strategy_identity",
            )

        policy_config = self._strategy_identity.strategy_config.allocation_policy
        if policy_config is None:
            self._fail(
                race_input,
                "allocation_policy",
                "strategy_identity.strategy_config.allocation_policy is required",
            )
        policy_identity = build_allocation_policy_identity(policy_config)
        identity = SimulationBetPlanIdentity(
            run_id=self._run_context.run_id,
            race_id=race_input.race_id,
            strategy_id=self._strategy_identity.strategy_id,
            strategy_config_hash=self._strategy_identity.strategy_config_hash,
            information_cutoff=race_input.information_cutoff,
        )

        pipeline_result = self._prediction_pipeline.run(race_input.pipeline_input)
        self._validate_pipeline_result(race_input, pipeline_result)

        allocation_plan = self._allocator.allocate(
            identity=identity,
            policy_identity=policy_identity,
            bet_plan=pipeline_result.bet_plan,
            budget=budget,
        )
        self._validate_allocation_plan(
            race_input,
            allocation_plan,
            identity,
            policy_identity,
            pipeline_result.bet_plan,
            budget,
        )

        snapshot = self._plan_builder.build(allocation_plan=allocation_plan)
        self._validate_snapshot(
            race_input,
            snapshot,
            identity,
            policy_identity,
            budget,
        )
        self._snapshot_repository.save_snapshot(snapshot=snapshot)
        return snapshot

    @staticmethod
    def _validate_collaborator(
        collaborator: object,
        method_name: str,
        name: str,
    ) -> None:
        if isinstance(collaborator, type) or not callable(
            getattr(collaborator, method_name, None)
        ):
            raise ValueError(f"{name} must provide a callable {method_name} method")

    @staticmethod
    def _fail(
        race_input: SimulationRaceInput,
        identifier: str,
        reason: str,
    ) -> None:
        raise SimulationValidationError(race_input.race_id, identifier, reason)

    def _validate_pipeline_result(
        self,
        race_input: SimulationRaceInput,
        result: object,
    ) -> None:
        if not isinstance(result, PipelineResult):
            self._fail(race_input, "prediction_pipeline", "result must be a PipelineResult")
        if not isinstance(result.bet_plan, BetPlan):
            self._fail(race_input, "prediction_pipeline", "bet_plan must be a BetPlan")
        predictions = result.predictions
        if isinstance(predictions, str | bytes | bytearray) or not isinstance(
            predictions,
            Sequence,
        ):
            self._fail(
                race_input,
                "prediction_pipeline",
                "predictions must contain Prediction values",
            )
        if not all(isinstance(prediction, Prediction) for prediction in predictions):
            self._fail(
                race_input,
                "prediction_pipeline",
                "predictions must contain Prediction values",
            )
        if any(prediction.race_id != race_input.race_id for prediction in predictions):
            self._fail(
                race_input,
                "prediction_pipeline",
                "prediction race_id does not match race_input",
            )

    def _validate_allocation_plan(
        self,
        race_input: SimulationRaceInput,
        allocation_plan: object,
        identity: SimulationBetPlanIdentity,
        policy_identity: AllocationPolicyIdentity,
        bet_plan: BetPlan,
        budget: BetStakeBudget,
    ) -> None:
        if not isinstance(allocation_plan, BetAllocationPlan):
            self._fail(
                race_input,
                "bet_stake_allocator",
                "result must be a BetAllocationPlan",
            )
        if allocation_plan.identity != identity:
            self._fail(race_input, "bet_stake_allocator", "identity does not match")
        if allocation_plan.policy_identity != policy_identity:
            self._fail(
                race_input,
                "bet_stake_allocator",
                "policy_identity does not match",
            )
        if allocation_plan.bet_plan is not bet_plan:
            self._fail(
                race_input,
                "bet_stake_allocator",
                "bet_plan object does not match",
            )
        if allocation_plan.budget != budget:
            self._fail(race_input, "bet_stake_allocator", "budget does not match")

    def _validate_snapshot(
        self,
        race_input: SimulationRaceInput,
        snapshot: object,
        identity: SimulationBetPlanIdentity,
        policy_identity: AllocationPolicyIdentity,
        budget: BetStakeBudget,
    ) -> None:
        if not isinstance(snapshot, SimulationBetPlanSnapshot):
            self._fail(
                race_input,
                "simulation_bet_plan_builder",
                "result must be a SimulationBetPlanSnapshot",
            )
        if snapshot.identity != identity:
            self._fail(
                race_input,
                "simulation_bet_plan_builder",
                "identity does not match",
            )
        if snapshot.policy_identity != policy_identity:
            self._fail(
                race_input,
                "simulation_bet_plan_builder",
                "policy_identity does not match",
            )
        if snapshot.budget != budget:
            self._fail(
                race_input,
                "simulation_bet_plan_builder",
                "budget does not match",
            )
