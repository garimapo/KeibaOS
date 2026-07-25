"""Domain and Protocol contracts for stake-allocation planning."""

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields
from datetime import UTC, datetime
import inspect
from typing import Protocol, get_args, get_origin, get_type_hints
import unittest

from scripts.prediction.allocation_policy import (
    AllocationPolicyIdentity,
    build_allocation_policy_identity,
    AllocationPolicyConfig,
)
from scripts.prediction.bet_generator import BetRecommendation
from scripts.prediction.bet_strategy import BetPlan
from scripts.simulation.bet_plan_identity import SimulationBetPlanIdentity
from scripts.simulation.stake_allocation import (
    AllocatedBetRecommendation,
    BetAllocationPlan,
    BetStakeAllocator,
    BetStakeBudget,
)


HASH = "a" * 64


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
        strategy_name="ContractStrategy",
        recommendations=tuple(recommendations),
        candidate_count=len(recommendations),
    )


def identity(**overrides: object) -> SimulationBetPlanIdentity:
    values: dict[str, object] = {
        "run_id": "run-1",
        "race_id": 101,
        "strategy_id": "strategy-1",
        "strategy_config_hash": HASH,
        "information_cutoff": datetime(2026, 7, 25, 9, 0, tzinfo=UTC),
    }
    values.update(overrides)
    return SimulationBetPlanIdentity(**values)  # type: ignore[arg-type]


def policy_identity() -> AllocationPolicyIdentity:
    return build_allocation_policy_identity(
        AllocationPolicyConfig("fixed-stake", "1", {"stake": 100})
    )


def allocation(item: BetRecommendation, order: int, stake: int = 100) -> AllocatedBetRecommendation:
    return AllocatedBetRecommendation(item, order, stake)


def allocation_plan(
    plan: BetPlan,
    allocations: object,
    budget: BetStakeBudget = BetStakeBudget(1000),
    **overrides: object,
) -> BetAllocationPlan:
    values: dict[str, object] = {
        "identity": identity(),
        "policy_identity": policy_identity(),
        "bet_plan": plan,
        "allocations": allocations,
        "budget": budget,
    }
    values.update(overrides)
    return BetAllocationPlan(**values)  # type: ignore[arg-type]


class BetStakeBudgetTests(unittest.TestCase):
    def test_accepts_zero_budget(self) -> None:
        self.assertEqual(BetStakeBudget(0).total_amount, 0)

    def test_accepts_positive_hundred_yen_budget(self) -> None:
        self.assertEqual(BetStakeBudget(1200).total_amount, 1200)

    def test_rejects_invalid_budget_amounts(self) -> None:
        for value in (-100, 50, True, False, 1.0, "100", None):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    BetStakeBudget(value)  # type: ignore[arg-type]

    def test_is_frozen_slotted_and_has_one_field(self) -> None:
        value = BetStakeBudget(100)
        self.assertEqual(tuple(item.name for item in fields(BetStakeBudget)), ("total_amount",))
        with self.assertRaises(FrozenInstanceError):
            value.total_amount = 200  # type: ignore[misc]
        self.assertFalse(hasattr(value, "__dict__"))


class AllocatedBetRecommendationTests(unittest.TestCase):
    def test_preserves_original_recommendation_object(self) -> None:
        source = recommendation(4)
        value = allocation(source, 0, 300)
        self.assertIs(value.recommendation, source)
        self.assertEqual((value.purchase_order, value.stake), (0, 300))

    def test_rejects_wrong_recommendation_type(self) -> None:
        with self.assertRaises(ValueError):
            AllocatedBetRecommendation("recommendation", 0, 100)  # type: ignore[arg-type]

    def test_rejects_invalid_purchase_order(self) -> None:
        for value in (-1, True, 1.0, "0", None):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    AllocatedBetRecommendation(recommendation(1), value, 100)  # type: ignore[arg-type]

    def test_rejects_invalid_stake(self) -> None:
        for value in (0, -100, 50, True, 1.0, "100", None):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    AllocatedBetRecommendation(recommendation(1), 0, value)  # type: ignore[arg-type]

    def test_is_frozen_slotted_and_has_contract_field_order(self) -> None:
        value = allocation(recommendation(1), 0)
        self.assertEqual(
            tuple(item.name for item in fields(AllocatedBetRecommendation)),
            ("recommendation", "purchase_order", "stake"),
        )
        with self.assertRaises(FrozenInstanceError):
            value.stake = 200  # type: ignore[misc]
        self.assertFalse(hasattr(value, "__dict__"))


class BetAllocationPlanTests(unittest.TestCase):
    def test_accepts_nonempty_plan_and_exposes_amounts(self) -> None:
        first, second = recommendation(3), recommendation(7, "馬連", (1, 2))
        plan = bet_plan(first, second)
        value = allocation_plan(plan, [allocation(first, 0, 100), allocation(second, 1, 200)], BetStakeBudget(500))
        self.assertEqual(value.allocations, (allocation(first, 0, 100), allocation(second, 1, 200)))
        self.assertEqual(value.allocated_amount, 300)
        self.assertEqual(value.unallocated_amount, 200)

    def test_preserves_all_constructor_object_identities(self) -> None:
        source = recommendation(1)
        plan = bet_plan(source)
        plan_identity = identity()
        policy = policy_identity()
        budget = BetStakeBudget(100)
        item = allocation(source, 0)
        value = allocation_plan(plan, [item], budget, identity=plan_identity, policy_identity=policy)
        self.assertIs(value.identity, plan_identity)
        self.assertIs(value.policy_identity, policy)
        self.assertIs(value.bet_plan, plan)
        self.assertIs(value.budget, budget)
        self.assertIs(value.allocations[0], item)

    def test_freezes_list_allocations_into_tuple_without_mutating_list(self) -> None:
        source = recommendation(1)
        input_allocations = [allocation(source, 0)]
        value = allocation_plan(bet_plan(source), input_allocations)
        input_allocations.append(allocation(source, 1))
        self.assertEqual(value.allocations, (allocation(source, 0),))
        self.assertIsInstance(value.allocations, tuple)

    def test_rejects_string_bytes_and_non_sequence_allocations(self) -> None:
        source = recommendation(1)
        plan = bet_plan(source)
        for value in ("allocation", b"allocation", bytearray(b"allocation"), None, (item for item in ())):
            with self.subTest(value_type=type(value).__name__):
                with self.assertRaises(ValueError):
                    allocation_plan(plan, value)

    def test_rejects_wrong_allocation_element_type(self) -> None:
        source = recommendation(1)
        with self.assertRaises(ValueError):
            allocation_plan(bet_plan(source), ["allocation"])

    def test_rejects_wrong_constructor_types(self) -> None:
        source = recommendation(1)
        valid = [allocation(source, 0)]
        cases = (
            {"identity": "identity"},
            {"policy_identity": "policy"},
            {"bet_plan": "plan"},
            {"budget": 100},
        )
        for overrides in cases:
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    allocation_plan(bet_plan(source), valid, **overrides)

    def test_rejects_non_recommendation_bet_plan_entry(self) -> None:
        invalid_plan = BetPlan("strategy", ("recommendation",), 1)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            allocation_plan(invalid_plan, ())

    def test_rejects_allocation_count_mismatch(self) -> None:
        first, second = recommendation(1), recommendation(2, "馬連", (1, 2))
        with self.assertRaises(ValueError):
            allocation_plan(bet_plan(first, second), [allocation(first, 0)])

    def test_rejects_allocation_order_mismatch(self) -> None:
        source = recommendation(1)
        with self.assertRaises(ValueError):
            allocation_plan(bet_plan(source), [allocation(source, 1)])

    def test_rejects_recommendation_object_identity_mismatch(self) -> None:
        planned = recommendation(1)
        equal_but_distinct = recommendation(1)
        self.assertEqual(planned, equal_but_distinct)
        self.assertIsNot(planned, equal_but_distinct)
        with self.assertRaises(ValueError):
            allocation_plan(bet_plan(planned), [allocation(equal_but_distinct, 0)])

    def test_rejects_duplicate_canonical_recommendation_identity(self) -> None:
        first = recommendation(1, "馬連", (2, 1))
        second = recommendation(2, "馬連", (1, 2))
        with self.assertRaises(ValueError):
            allocation_plan(bet_plan(first, second), [allocation(first, 0), allocation(second, 1)], BetStakeBudget(200))

    def test_allows_same_selection_for_different_bet_types(self) -> None:
        quinella = recommendation(1, "馬連", (2, 1))
        wide = recommendation(2, "ワイド", (1, 2))
        value = allocation_plan(
            bet_plan(quinella, wide),
            [allocation(quinella, 0), allocation(wide, 1)],
            BetStakeBudget(200),
        )
        self.assertEqual(value.allocated_amount, 200)

    def test_does_not_canonicalize_or_modify_recommendation_horse_ids(self) -> None:
        source = recommendation(1, "馬連", (3, 1))
        value = allocation_plan(bet_plan(source), [allocation(source, 0)])
        self.assertIs(value.allocations[0].recommendation, source)
        self.assertEqual(value.allocations[0].recommendation.horse_ids, (3, 1))

    def test_rejects_budget_below_minimum_for_nonempty_plan(self) -> None:
        first, second = recommendation(1), recommendation(2, "馬連", (1, 2))
        with self.assertRaises(ValueError):
            allocation_plan(
                bet_plan(first, second),
                [allocation(first, 0), allocation(second, 1)],
                BetStakeBudget(100),
            )

    def test_rejects_allocated_amount_over_budget(self) -> None:
        source = recommendation(1)
        with self.assertRaises(ValueError):
            allocation_plan(bet_plan(source), [allocation(source, 0, 200)], BetStakeBudget(100))

    def test_accepts_empty_plan_with_zero_budget(self) -> None:
        value = allocation_plan(bet_plan(), [], BetStakeBudget(0))
        self.assertEqual(value.allocations, ())
        self.assertEqual(value.allocated_amount, 0)
        self.assertEqual(value.unallocated_amount, 0)

    def test_accepts_empty_plan_with_unused_budget(self) -> None:
        value = allocation_plan(bet_plan(), (), BetStakeBudget(600))
        self.assertEqual(value.allocated_amount, 0)
        self.assertEqual(value.unallocated_amount, 600)

    def test_rejects_empty_plan_with_allocations(self) -> None:
        source = recommendation(1)
        with self.assertRaises(ValueError):
            allocation_plan(bet_plan(), [allocation(source, 0)])

    def test_is_frozen_slotted_and_has_exact_field_order(self) -> None:
        source = recommendation(1)
        value = allocation_plan(bet_plan(source), [allocation(source, 0)])
        self.assertEqual(
            tuple(item.name for item in fields(BetAllocationPlan)),
            ("identity", "policy_identity", "bet_plan", "allocations", "budget"),
        )
        with self.assertRaises(FrozenInstanceError):
            value.budget = BetStakeBudget(200)  # type: ignore[misc]
        self.assertFalse(hasattr(value, "__dict__"))

    def test_allocation_plan_has_no_mutable_cache_fields(self) -> None:
        source = recommendation(1)
        value = allocation_plan(bet_plan(source), [allocation(source, 0)])
        self.assertEqual(value.allocated_amount, 100)
        self.assertEqual(value.unallocated_amount, 900)
        self.assertFalse(any("cache" in item.name for item in fields(value)))


class BetStakeAllocatorProtocolTests(unittest.TestCase):
    def test_is_a_structural_protocol_without_runtime_checkable(self) -> None:
        self.assertTrue(BetStakeAllocator._is_protocol)
        self.assertFalse(BetStakeAllocator._is_runtime_protocol)
        self.assertIsNot(BetStakeAllocator, Protocol)

    def test_allocate_signature_is_keyword_only_and_exact(self) -> None:
        signature = inspect.signature(BetStakeAllocator.allocate)
        self.assertEqual(tuple(signature.parameters), ("self", "identity", "policy_identity", "bet_plan", "budget"))
        self.assertTrue(all(parameter.kind is inspect.Parameter.KEYWORD_ONLY for parameter in tuple(signature.parameters.values())[1:]))

    def test_allocate_type_hints_match_contract(self) -> None:
        hints = get_type_hints(BetStakeAllocator.allocate)
        self.assertIs(hints["identity"], SimulationBetPlanIdentity)
        self.assertIs(hints["policy_identity"], AllocationPolicyIdentity)
        self.assertIs(hints["bet_plan"], BetPlan)
        self.assertIs(hints["budget"], BetStakeBudget)
        self.assertIs(hints["return"], BetAllocationPlan)

    def test_module_has_no_allocator_implementation_or_external_dependencies(self) -> None:
        import scripts.simulation.stake_allocation as module

        tree = ast.parse(inspect.getsource(module))
        class_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
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
        self.assertEqual(class_names, {"BetStakeBudget", "AllocatedBetRecommendation", "BetAllocationPlan", "BetStakeAllocator"})
        self.assertFalse(any(name.startswith(("sqlite3", "requests", "scripts.simulation.repositories")) for name in imports))

    def test_simulation_package_does_not_export_contracts_early(self) -> None:
        import scripts.simulation as package

        self.assertFalse(hasattr(package, "BetStakeBudget"))
        self.assertFalse(hasattr(package, "BetStakeAllocator"))

    def test_target_race_count_is_not_added_to_production_contract(self) -> None:
        import scripts.simulation.stake_allocation as module

        self.assertNotIn("target_race_count", inspect.getsource(module))


if __name__ == "__main__":
    unittest.main()
