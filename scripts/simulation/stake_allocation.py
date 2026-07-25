"""Immutable contracts for one race's simulation bet stake allocation."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from scripts.prediction.allocation_policy import AllocationPolicyIdentity
from scripts.prediction.bet_generator import BetRecommendation
from scripts.prediction.bet_strategy import BetPlan
from scripts.simulation.bet_plan_identity import SimulationBetPlanIdentity


def _is_non_bool_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _validate_non_empty_stake(value: object, name: str) -> int:
    if not _is_non_bool_int(value) or value <= 0 or value % 100 != 0:
        raise ValueError(f"{name} must be a positive multiple of 100")
    return value


def _canonical_recommendation_identity(recommendation: BetRecommendation) -> tuple[str, tuple[int, ...]]:
    try:
        horse_ids = tuple(sorted(recommendation.horse_ids))
    except TypeError as exc:
        raise ValueError("recommendation horse_ids must be sortable") from exc
    return recommendation.bet_type, horse_ids


@dataclass(frozen=True, slots=True)
class BetStakeBudget:
    """One race-plan's explicit stake budget, expressed in 100-yen units."""

    total_amount: int

    def __post_init__(self) -> None:
        if not _is_non_bool_int(self.total_amount) or self.total_amount < 0 or self.total_amount % 100 != 0:
            raise ValueError("total_amount must be a non-negative multiple of 100")


@dataclass(frozen=True, slots=True)
class AllocatedBetRecommendation:
    """One original recommendation with its allocated stake and purchase order."""

    recommendation: BetRecommendation
    purchase_order: int
    stake: int

    def __post_init__(self) -> None:
        if not isinstance(self.recommendation, BetRecommendation):
            raise ValueError("recommendation must be a BetRecommendation")
        if not _is_non_bool_int(self.purchase_order) or self.purchase_order < 0:
            raise ValueError("purchase_order must be a non-negative integer")
        _validate_non_empty_stake(self.stake, "stake")


@dataclass(frozen=True, slots=True)
class BetAllocationPlan:
    """Immutable, budget-bounded allocation result for one original ``BetPlan``."""

    identity: SimulationBetPlanIdentity
    policy_identity: AllocationPolicyIdentity
    bet_plan: BetPlan
    allocations: tuple[AllocatedBetRecommendation, ...]
    budget: BetStakeBudget

    def __post_init__(self) -> None:
        if not isinstance(self.identity, SimulationBetPlanIdentity):
            raise ValueError("identity must be a SimulationBetPlanIdentity")
        if not isinstance(self.policy_identity, AllocationPolicyIdentity):
            raise ValueError("policy_identity must be an AllocationPolicyIdentity")
        if not isinstance(self.bet_plan, BetPlan):
            raise ValueError("bet_plan must be a BetPlan")
        if not isinstance(self.budget, BetStakeBudget):
            raise ValueError("budget must be a BetStakeBudget")
        allocations = self._normalize_allocations(self.allocations)
        recommendations = tuple(self.bet_plan.recommendations)
        if not all(isinstance(recommendation, BetRecommendation) for recommendation in recommendations):
            raise ValueError("bet_plan recommendations must be BetRecommendation values")
        if len(allocations) != len(recommendations):
            raise ValueError("allocations must match bet_plan recommendation count")
        self._validate_plan_identities(recommendations)
        for index, (allocation, recommendation) in enumerate(zip(allocations, recommendations, strict=True)):
            if allocation.purchase_order != index:
                raise ValueError("allocation purchase_order must match the recommendation index")
            if allocation.recommendation is not recommendation:
                raise ValueError("allocation recommendation must preserve BetPlan object identity")
        if recommendations and self.budget.total_amount < len(recommendations) * 100:
            raise ValueError("budget must provide at least 100 yen per recommendation")
        if sum(allocation.stake for allocation in allocations) > self.budget.total_amount:
            raise ValueError("allocated amount must not exceed budget")
        object.__setattr__(self, "allocations", allocations)

    @staticmethod
    def _normalize_allocations(value: object) -> tuple[AllocatedBetRecommendation, ...]:
        if isinstance(value, str | bytes | bytearray) or not isinstance(value, Sequence):
            raise ValueError("allocations must be a finite sequence")
        allocations = tuple(value)
        if not all(isinstance(allocation, AllocatedBetRecommendation) for allocation in allocations):
            raise ValueError("allocations must contain AllocatedBetRecommendation values")
        return allocations

    @staticmethod
    def _validate_plan_identities(recommendations: tuple[BetRecommendation, ...]) -> None:
        identities = tuple(_canonical_recommendation_identity(recommendation) for recommendation in recommendations)
        if len(set(identities)) != len(identities):
            raise ValueError("bet_plan recommendations must have unique canonical identities")

    @property
    def allocated_amount(self) -> int:
        """Total stake allocated to the original recommendations."""
        return sum(allocation.stake for allocation in self.allocations)

    @property
    def unallocated_amount(self) -> int:
        """Budget amount intentionally left unallocated by the allocator."""
        return self.budget.total_amount - self.allocated_amount


class BetStakeAllocator(Protocol):
    """Contract for a deterministic allocator; no allocation algorithm is defined here."""

    def allocate(
        self,
        *,
        identity: SimulationBetPlanIdentity,
        policy_identity: AllocationPolicyIdentity,
        bet_plan: BetPlan,
        budget: BetStakeBudget,
    ) -> BetAllocationPlan:
        ...
