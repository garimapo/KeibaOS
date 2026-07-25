"""Deterministic allocator that assigns one configured stake to every recommendation."""

from __future__ import annotations

from scripts.prediction.allocation_policy import (
    AllocationPolicyConfig,
    AllocationPolicyIdentity,
    build_allocation_policy_identity,
)
from scripts.prediction.bet_strategy import BetPlan
from scripts.simulation.bet_plan_identity import SimulationBetPlanIdentity
from scripts.simulation.stake_allocation import (
    AllocatedBetRecommendation,
    BetAllocationPlan,
    BetStakeBudget,
)


FIXED_STAKE_POLICY_NAME = "fixed_stake_per_recommendation"
FIXED_STAKE_POLICY_VERSION = "1"
FIXED_STAKE_PARAMETER_KEY = "stake_amount"


class FixedStakeBetAllocator:
    """Assign the configured, identical stake to each ``BetPlan`` recommendation."""

    __slots__ = ("_policy_config", "_policy_identity", "_stake_amount")

    def __init__(self, *, policy_config: AllocationPolicyConfig) -> None:
        if not isinstance(policy_config, AllocationPolicyConfig):
            raise ValueError("policy_config must be an AllocationPolicyConfig")
        if policy_config.policy_name != FIXED_STAKE_POLICY_NAME:
            raise ValueError("policy_config has an unsupported fixed-stake policy name")
        if policy_config.policy_version != FIXED_STAKE_POLICY_VERSION:
            raise ValueError("policy_config has an unsupported fixed-stake policy version")

        parameters = policy_config.parameters
        if set(parameters) != {FIXED_STAKE_PARAMETER_KEY}:
            raise ValueError("policy_config parameters must contain only stake_amount")
        stake_amount = parameters[FIXED_STAKE_PARAMETER_KEY]
        if (
            not isinstance(stake_amount, int)
            or isinstance(stake_amount, bool)
            or stake_amount <= 0
            or stake_amount % 100 != 0
        ):
            raise ValueError("stake_amount must be a positive multiple of 100")

        self._policy_config = policy_config
        self._policy_identity = build_allocation_policy_identity(policy_config)
        self._stake_amount = stake_amount

    def allocate(
        self,
        *,
        identity: SimulationBetPlanIdentity,
        policy_identity: AllocationPolicyIdentity,
        bet_plan: BetPlan,
        budget: BetStakeBudget,
    ) -> BetAllocationPlan:
        if not isinstance(identity, SimulationBetPlanIdentity):
            raise ValueError("identity must be a SimulationBetPlanIdentity")
        if not isinstance(policy_identity, AllocationPolicyIdentity):
            raise ValueError("policy_identity must be an AllocationPolicyIdentity")
        if not isinstance(bet_plan, BetPlan):
            raise ValueError("bet_plan must be a BetPlan")
        if not isinstance(budget, BetStakeBudget):
            raise ValueError("budget must be a BetStakeBudget")
        if policy_identity != self._policy_identity:
            raise ValueError("policy_identity does not match the configured fixed-stake policy")

        recommendations = bet_plan.recommendations
        required_amount = len(recommendations) * self._stake_amount
        if budget.total_amount < required_amount:
            raise ValueError("budget is insufficient for all fixed-stake recommendations")

        allocations = tuple(
            AllocatedBetRecommendation(
                recommendation=recommendation,
                purchase_order=index,
                stake=self._stake_amount,
            )
            for index, recommendation in enumerate(recommendations)
        )
        return BetAllocationPlan(
            identity=identity,
            policy_identity=policy_identity,
            bet_plan=bet_plan,
            allocations=allocations,
            budget=budget,
        )
