"""Tests for the deterministic fixed-stake allocation policy."""

from __future__ import annotations

import ast
from datetime import UTC, datetime
import inspect
from types import MappingProxyType
from typing import get_type_hints
import unittest

from scripts.prediction.allocation_policy import (
    AllocationPolicyConfig,
    AllocationPolicyIdentity,
    build_allocation_policy_identity,
)
from scripts.prediction.bet_generator import BetRecommendation
from scripts.prediction.bet_strategy import BetPlan
from scripts.simulation.bet_plan_identity import SimulationBetPlanIdentity
from scripts.simulation.fixed_stake_allocator import (
    FIXED_STAKE_PARAMETER_KEY,
    FIXED_STAKE_POLICY_NAME,
    FIXED_STAKE_POLICY_VERSION,
    FixedStakeBetAllocator,
)
from scripts.simulation.stake_allocation import BetAllocationPlan, BetStakeBudget


HASH = "a" * 64


def fixed_policy_config(stake_amount: object = 100, **overrides: object) -> AllocationPolicyConfig:
    values: dict[str, object] = {
        "policy_name": FIXED_STAKE_POLICY_NAME,
        "policy_version": FIXED_STAKE_POLICY_VERSION,
        "parameters": {FIXED_STAKE_PARAMETER_KEY: stake_amount},
    }
    values.update(overrides)
    return AllocationPolicyConfig(**values)  # type: ignore[arg-type]


def recommendation(
    rank: int,
    bet_type: str = "単勝",
    horse_ids: tuple[int, ...] = (1,),
) -> BetRecommendation:
    return BetRecommendation(
        rank=rank,
        bet_type=bet_type,
        horse_ids=horse_ids,
        estimated_probability=0.2,
        expected_value=1.1,
        combination_score=None,
        prediction_score=50.0,
    )


def bet_plan(*recommendations: BetRecommendation) -> BetPlan:
    return BetPlan(
        strategy_name="FixedStakeTestStrategy",
        recommendations=tuple(recommendations),
        candidate_count=len(recommendations),
    )


def plan_identity() -> SimulationBetPlanIdentity:
    return SimulationBetPlanIdentity(
        run_id="run-fixed-stake",
        race_id=101,
        strategy_id="strategy-fixed-stake",
        strategy_config_hash=HASH,
        information_cutoff=datetime(2026, 7, 25, 9, 0, tzinfo=UTC),
    )


class FixedStakeBetAllocatorConstructorTests(unittest.TestCase):
    def test_accepts_hundred_yen_stake(self) -> None:
        allocator = FixedStakeBetAllocator(policy_config=fixed_policy_config(100))
        self.assertIsInstance(allocator, FixedStakeBetAllocator)

    def test_accepts_five_hundred_yen_stake(self) -> None:
        allocator = FixedStakeBetAllocator(policy_config=fixed_policy_config(500))
        self.assertEqual(allocator._stake_amount, 500)

    def test_preserves_policy_config_object_identity(self) -> None:
        config = fixed_policy_config(300)
        allocator = FixedStakeBetAllocator(policy_config=config)
        self.assertIs(allocator._policy_config, config)

    def test_derives_expected_policy_identity_with_existing_helper(self) -> None:
        config = fixed_policy_config(300)
        allocator = FixedStakeBetAllocator(policy_config=config)
        self.assertEqual(allocator._policy_identity, build_allocation_policy_identity(config))

    def test_does_not_modify_policy_config(self) -> None:
        config = fixed_policy_config(300)
        parameters_before = config.parameters
        FixedStakeBetAllocator(policy_config=config)
        self.assertIs(config.parameters, parameters_before)
        self.assertEqual(config.parameters, MappingProxyType({"stake_amount": 300}))

    def test_rejects_non_policy_config(self) -> None:
        for value in (None, "config", {"stake_amount": 100}, object()):
            with self.subTest(value_type=type(value).__name__):
                with self.assertRaises(ValueError):
                    FixedStakeBetAllocator(policy_config=value)  # type: ignore[arg-type]

    def test_rejects_wrong_policy_name(self) -> None:
        with self.assertRaises(ValueError):
            FixedStakeBetAllocator(policy_config=fixed_policy_config(policy_name="other"))

    def test_rejects_policy_name_case_difference(self) -> None:
        with self.assertRaises(ValueError):
            FixedStakeBetAllocator(policy_config=fixed_policy_config(policy_name=FIXED_STAKE_POLICY_NAME.upper()))

    def test_rejects_policy_name_whitespace_difference(self) -> None:
        with self.assertRaises(ValueError):
            FixedStakeBetAllocator(policy_config=fixed_policy_config(policy_name=f" {FIXED_STAKE_POLICY_NAME} "))

    def test_rejects_wrong_policy_version(self) -> None:
        with self.assertRaises(ValueError):
            FixedStakeBetAllocator(policy_config=fixed_policy_config(policy_version="2"))

    def test_rejects_missing_parameter(self) -> None:
        with self.assertRaises(ValueError):
            FixedStakeBetAllocator(policy_config=fixed_policy_config(parameters={}))

    def test_rejects_extra_parameter(self) -> None:
        with self.assertRaises(ValueError):
            FixedStakeBetAllocator(policy_config=fixed_policy_config(parameters={"stake_amount": 100, "extra": 1}))

    def test_rejects_parameter_alias(self) -> None:
        with self.assertRaises(ValueError):
            FixedStakeBetAllocator(policy_config=fixed_policy_config(parameters={"stake": 100}))

    def test_rejects_invalid_stake_values(self) -> None:
        invalid_values: tuple[object, ...] = (0, -100, True, False, 100.0, "100", None, 150)
        for value in invalid_values:
            with self.subTest(value=repr(value)):
                with self.assertRaises(ValueError):
                    FixedStakeBetAllocator(policy_config=fixed_policy_config(value))

    def test_rejects_collection_stake_values(self) -> None:
        for value in ([100], (100,), {"amount": 100}):
            with self.subTest(value_type=type(value).__name__):
                with self.assertRaises(ValueError):
                    FixedStakeBetAllocator(policy_config=fixed_policy_config(value))


class FixedStakeBetAllocatorAllocationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = fixed_policy_config(100)
        self.allocator = FixedStakeBetAllocator(policy_config=self.config)
        self.identity = plan_identity()
        self.policy_identity = build_allocation_policy_identity(self.config)

    def allocate(self, plan: BetPlan, budget: BetStakeBudget) -> BetAllocationPlan:
        return self.allocator.allocate(
            identity=self.identity,
            policy_identity=self.policy_identity,
            bet_plan=plan,
            budget=budget,
        )

    def test_allocates_one_recommendation(self) -> None:
        item = recommendation(1)
        result = self.allocate(bet_plan(item), BetStakeBudget(100))
        self.assertEqual(result.allocated_amount, 100)
        self.assertEqual(result.unallocated_amount, 0)
        self.assertEqual(result.allocations[0].stake, 100)

    def test_allocates_multiple_recommendations_at_same_stake(self) -> None:
        first = recommendation(1)
        second = recommendation(2, "馬連", (1, 2))
        third = recommendation(3, "ワイド", (2, 3))
        result = self.allocate(bet_plan(first, second, third), BetStakeBudget(300))
        self.assertEqual(tuple(item.stake for item in result.allocations), (100, 100, 100))

    def test_preserves_recommendation_order_and_identity(self) -> None:
        first = recommendation(9, "馬連", (3, 1))
        second = recommendation(1, "単勝", (2,))
        result = self.allocate(bet_plan(first, second), BetStakeBudget(200))
        self.assertIs(result.allocations[0].recommendation, first)
        self.assertIs(result.allocations[1].recommendation, second)
        self.assertEqual(tuple(item.purchase_order for item in result.allocations), (0, 1))

    def test_preserves_all_constructor_input_objects(self) -> None:
        item = recommendation(1)
        plan = bet_plan(item)
        budget = BetStakeBudget(100)
        result = self.allocate(plan, budget)
        self.assertIs(result.identity, self.identity)
        self.assertIs(result.policy_identity, self.policy_identity)
        self.assertIs(result.bet_plan, plan)
        self.assertIs(result.budget, budget)

    def test_returns_bet_allocation_plan(self) -> None:
        self.assertIsInstance(self.allocate(bet_plan(recommendation(1)), BetStakeBudget(100)), BetAllocationPlan)

    def test_accepts_exact_budget(self) -> None:
        result = self.allocate(bet_plan(recommendation(1), recommendation(2, "馬連", (1, 2))), BetStakeBudget(200))
        self.assertEqual((result.allocated_amount, result.unallocated_amount), (200, 0))

    def test_allows_unused_budget_without_reallocation(self) -> None:
        result = self.allocate(bet_plan(recommendation(1), recommendation(2, "馬連", (1, 2))), BetStakeBudget(500))
        self.assertEqual(tuple(item.stake for item in result.allocations), (100, 100))
        self.assertEqual((result.allocated_amount, result.unallocated_amount), (200, 300))

    def test_is_deterministic_for_same_input(self) -> None:
        plan = bet_plan(recommendation(1), recommendation(2, "馬連", (1, 2)))
        budget = BetStakeBudget(300)
        first = self.allocate(plan, budget)
        second = self.allocate(plan, budget)
        self.assertEqual(first, second)
        self.assertIs(first.allocations[0].recommendation, second.allocations[0].recommendation)

    def test_accepts_empty_plan_with_zero_budget(self) -> None:
        result = self.allocate(bet_plan(), BetStakeBudget(0))
        self.assertEqual(result.allocations, ())
        self.assertEqual((result.allocated_amount, result.unallocated_amount), (0, 0))

    def test_accepts_empty_plan_with_unused_budget(self) -> None:
        result = self.allocate(bet_plan(), BetStakeBudget(600))
        self.assertEqual(result.allocations, ())
        self.assertEqual((result.allocated_amount, result.unallocated_amount), (0, 600))

    def test_rejects_budget_shortage_for_one_recommendation(self) -> None:
        with self.assertRaises(ValueError):
            self.allocate(bet_plan(recommendation(1)), BetStakeBudget(0))

    def test_rejects_budget_shortage_for_two_recommendations(self) -> None:
        plan = bet_plan(recommendation(1), recommendation(2, "馬連", (1, 2)))
        with self.assertRaises(ValueError):
            self.allocate(plan, BetStakeBudget(100))

    def test_rejects_budget_shortage_without_partial_result(self) -> None:
        allocator = FixedStakeBetAllocator(policy_config=fixed_policy_config(500))
        plan = bet_plan(recommendation(1), recommendation(2, "馬連", (1, 2)))
        with self.assertRaises(ValueError):
            allocator.allocate(
                identity=self.identity,
                policy_identity=build_allocation_policy_identity(fixed_policy_config(500)),
                bet_plan=plan,
                budget=BetStakeBudget(900),
            )

    def test_rejects_identity_type(self) -> None:
        with self.assertRaises(ValueError):
            self.allocator.allocate(identity="identity", policy_identity=self.policy_identity, bet_plan=bet_plan(), budget=BetStakeBudget(0))  # type: ignore[arg-type]

    def test_rejects_policy_identity_type(self) -> None:
        with self.assertRaises(ValueError):
            self.allocator.allocate(identity=self.identity, policy_identity="policy", bet_plan=bet_plan(), budget=BetStakeBudget(0))  # type: ignore[arg-type]

    def test_rejects_bet_plan_type(self) -> None:
        with self.assertRaises(ValueError):
            self.allocator.allocate(identity=self.identity, policy_identity=self.policy_identity, bet_plan="plan", budget=BetStakeBudget(0))  # type: ignore[arg-type]

    def test_rejects_budget_type(self) -> None:
        with self.assertRaises(ValueError):
            self.allocator.allocate(identity=self.identity, policy_identity=self.policy_identity, bet_plan=bet_plan(), budget=0)  # type: ignore[arg-type]

    def test_rejects_policy_identity_name_mismatch(self) -> None:
        mismatched = AllocationPolicyIdentity("different", "1", self.policy_identity.policy_config_hash)
        with self.assertRaises(ValueError):
            self.allocator.allocate(identity=self.identity, policy_identity=mismatched, bet_plan=bet_plan(), budget=BetStakeBudget(0))

    def test_rejects_policy_identity_version_mismatch(self) -> None:
        mismatched = AllocationPolicyIdentity(FIXED_STAKE_POLICY_NAME, "2", self.policy_identity.policy_config_hash)
        with self.assertRaises(ValueError):
            self.allocator.allocate(identity=self.identity, policy_identity=mismatched, bet_plan=bet_plan(), budget=BetStakeBudget(0))

    def test_rejects_policy_identity_hash_mismatch(self) -> None:
        mismatched = AllocationPolicyIdentity(FIXED_STAKE_POLICY_NAME, FIXED_STAKE_POLICY_VERSION, "b" * 64)
        with self.assertRaises(ValueError):
            self.allocator.allocate(identity=self.identity, policy_identity=mismatched, bet_plan=bet_plan(), budget=BetStakeBudget(0))

    def test_rejects_policy_identity_from_different_stake_amount(self) -> None:
        different_stake_identity = build_allocation_policy_identity(fixed_policy_config(500))
        with self.assertRaises(ValueError):
            self.allocator.allocate(identity=self.identity, policy_identity=different_stake_identity, bet_plan=bet_plan(), budget=BetStakeBudget(0))

    def test_delegates_duplicate_recommendation_validation_to_allocation_plan(self) -> None:
        first = recommendation(1, "馬連", (2, 1))
        duplicate = recommendation(2, "馬連", (1, 2))
        with self.assertRaises(ValueError):
            self.allocate(bet_plan(first, duplicate), BetStakeBudget(200))


class FixedStakeBetAllocatorContractTests(unittest.TestCase):
    def test_policy_constants_are_fixed_contract_values(self) -> None:
        self.assertEqual(FIXED_STAKE_POLICY_NAME, "fixed_stake_per_recommendation")
        self.assertEqual(FIXED_STAKE_POLICY_VERSION, "1")
        self.assertEqual(FIXED_STAKE_PARAMETER_KEY, "stake_amount")

    def test_constructor_signature_is_keyword_only(self) -> None:
        signature = inspect.signature(FixedStakeBetAllocator)
        self.assertEqual(tuple(signature.parameters), ("policy_config",))
        self.assertIs(signature.parameters["policy_config"].kind, inspect.Parameter.KEYWORD_ONLY)

    def test_allocate_signature_and_type_hints_match_protocol(self) -> None:
        signature = inspect.signature(FixedStakeBetAllocator.allocate)
        self.assertEqual(tuple(signature.parameters), ("self", "identity", "policy_identity", "bet_plan", "budget"))
        self.assertTrue(all(item.kind is inspect.Parameter.KEYWORD_ONLY for item in tuple(signature.parameters.values())[1:]))
        hints = get_type_hints(FixedStakeBetAllocator.allocate)
        self.assertIs(hints["identity"], SimulationBetPlanIdentity)
        self.assertIs(hints["policy_identity"], AllocationPolicyIdentity)
        self.assertIs(hints["bet_plan"], BetPlan)
        self.assertIs(hints["budget"], BetStakeBudget)
        self.assertIs(hints["return"], BetAllocationPlan)

    def test_has_no_extra_public_allocation_method(self) -> None:
        public_methods = {
            name
            for name, value in inspect.getmembers(FixedStakeBetAllocator, inspect.isfunction)
            if not name.startswith("_")
        }
        self.assertEqual(public_methods, {"allocate"})

    def test_module_has_no_database_network_or_runtime_checkable_dependency(self) -> None:
        import scripts.simulation.fixed_stake_allocator as module

        tree = ast.parse(inspect.getsource(module))
        imports = [
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        ] + [
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        ]
        source = inspect.getsource(module)
        self.assertFalse(any(name.startswith(("sqlite3", "requests", "random")) for name in imports))
        self.assertNotIn("runtime_checkable", source)
        self.assertNotIn("datetime.now", source)

    def test_simulation_package_does_not_export_allocator_early(self) -> None:
        import scripts.simulation as package

        self.assertFalse(hasattr(package, "FixedStakeBetAllocator"))


if __name__ == "__main__":
    unittest.main()
