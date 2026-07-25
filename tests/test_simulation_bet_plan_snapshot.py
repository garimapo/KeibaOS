"""Contract tests for immutable simulation bet-plan snapshots."""

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields
from datetime import UTC, datetime, timedelta, timezone
import inspect
from types import MappingProxyType
import unittest

from scripts.prediction.allocation_policy import (
    AllocationPolicyConfig,
    AllocationPolicyIdentity,
    build_allocation_policy_identity,
)
from scripts.simulation.bet_plan_identity import SimulationBetPlanIdentity
from scripts.simulation.bet_plan_snapshot import SimulationBetPlanSnapshot
from scripts.simulation.models import SimulationBet
from scripts.simulation.stake_allocation import BetStakeBudget


HASH = "a" * 64
CUTOFF = datetime(2026, 7, 25, 9, 0, tzinfo=UTC)


def snapshot_identity(**overrides: object) -> SimulationBetPlanIdentity:
    values: dict[str, object] = {
        "run_id": "run-snapshot",
        "race_id": 101,
        "strategy_id": "strategy-snapshot",
        "strategy_config_hash": HASH,
        "information_cutoff": CUTOFF,
    }
    values.update(overrides)
    return SimulationBetPlanIdentity(**values)  # type: ignore[arg-type]


def policy_identity() -> AllocationPolicyIdentity:
    return build_allocation_policy_identity(
        AllocationPolicyConfig(
            policy_name="fixed_stake_per_recommendation",
            policy_version="1",
            parameters={"stake_amount": 100},
        )
    )


def bet(
    *,
    race_id: int = 101,
    strategy_id: str = "strategy-snapshot",
    bet_type: str = "単勝",
    race_entry_ids: tuple[int, ...] = (1,),
    stake: int = 100,
    recommendation_rank: int = 0,
    placed_at_cutoff: datetime = CUTOFF,
) -> SimulationBet:
    return SimulationBet(
        race_id=race_id,
        strategy_id=strategy_id,
        bet_type=bet_type,
        race_entry_ids=race_entry_ids,
        stake=stake,
        recommendation_rank=recommendation_rank,
        placed_at_cutoff=placed_at_cutoff,
    )


def snapshot(
    bets: object = (),
    *,
    identity: SimulationBetPlanIdentity | object | None = None,
    policy: AllocationPolicyIdentity | object | None = None,
    budget: BetStakeBudget | object | None = None,
) -> SimulationBetPlanSnapshot:
    return SimulationBetPlanSnapshot(
        identity=snapshot_identity() if identity is None else identity,  # type: ignore[arg-type]
        policy_identity=policy_identity() if policy is None else policy,  # type: ignore[arg-type]
        budget=BetStakeBudget(1000) if budget is None else budget,  # type: ignore[arg-type]
        bets=bets,  # type: ignore[arg-type]
    )


class SimulationBetPlanSnapshotConstructionTests(unittest.TestCase):
    def test_creates_snapshot_with_all_contract_fields(self) -> None:
        item = bet()
        value = snapshot((item,))
        self.assertIsInstance(value, SimulationBetPlanSnapshot)
        self.assertEqual(value.bets, (item,))

    def test_has_exact_field_order(self) -> None:
        self.assertEqual(
            tuple(field.name for field in fields(SimulationBetPlanSnapshot)),
            ("identity", "policy_identity", "budget", "bets"),
        )

    def test_preserves_identity_policy_and_budget_object_identities(self) -> None:
        identity = snapshot_identity()
        policy = policy_identity()
        budget = BetStakeBudget(100)
        value = snapshot((bet(),), identity=identity, policy=policy, budget=budget)
        self.assertIs(value.identity, identity)
        self.assertIs(value.policy_identity, policy)
        self.assertIs(value.budget, budget)

    def test_preserves_bet_object_identity(self) -> None:
        item = bet()
        value = snapshot((item,))
        self.assertIs(value.bets[0], item)

    def test_preserves_tuple_bets_object(self) -> None:
        values = (bet(),)
        value = snapshot(values)
        self.assertIs(value.bets, values)

    def test_freezes_list_bets_without_mutating_input(self) -> None:
        values = [bet()]
        value = snapshot(values)
        values.append(bet(race_entry_ids=(2,)))
        self.assertEqual(value.bets, (values[0],))
        self.assertIsInstance(value.bets, tuple)

    def test_accepts_generator_once_as_bets_iterable(self) -> None:
        item = bet()
        value = snapshot((candidate for candidate in (item,)))
        self.assertEqual(value.bets, (item,))

    def test_preserves_input_order_without_rank_sorting(self) -> None:
        first = bet(recommendation_rank=9, race_entry_ids=(3,))
        second = bet(recommendation_rank=1, race_entry_ids=(1,))
        value = snapshot((first, second))
        self.assertEqual(value.bets, (first, second))

    def test_preserves_input_order_without_selection_sorting(self) -> None:
        first = bet(race_entry_ids=(3,))
        second = bet(race_entry_ids=(1,))
        value = snapshot((first, second))
        self.assertEqual(value.bets, (first, second))

    def test_is_frozen_slotted_and_has_no_dict(self) -> None:
        value = snapshot()
        with self.assertRaises(FrozenInstanceError):
            value.budget = BetStakeBudget(200)  # type: ignore[misc]
        self.assertFalse(hasattr(value, "__dict__"))


class SimulationBetPlanSnapshotTypeValidationTests(unittest.TestCase):
    def test_rejects_invalid_identity_type(self) -> None:
        with self.assertRaises(ValueError):
            snapshot(identity="identity")

    def test_rejects_invalid_policy_identity_type(self) -> None:
        with self.assertRaises(ValueError):
            snapshot(policy="policy")

    def test_rejects_invalid_budget_type(self) -> None:
        with self.assertRaises(ValueError):
            snapshot(budget=100)

    def test_rejects_non_iterable_bets(self) -> None:
        for values in (None, 1, object()):
            with self.subTest(value_type=type(values).__name__):
                with self.assertRaises(ValueError):
                    snapshot(values)

    def test_rejects_text_and_mapping_bet_iterables(self) -> None:
        for values in ("bets", b"bets", bytearray(b"bets"), {"bet": bet()}):
            with self.subTest(value_type=type(values).__name__):
                with self.assertRaises(ValueError):
                    snapshot(values)

    def test_rejects_invalid_bet_element_types(self) -> None:
        for value in (None, {}, (), 1, "bet", object()):
            with self.subTest(value_type=type(value).__name__):
                with self.assertRaises(ValueError):
                    snapshot((value,))

    def test_rejects_mixed_valid_and_invalid_bets(self) -> None:
        with self.assertRaises(ValueError):
            snapshot((bet(), "not-a-bet"))


class SimulationBetPlanSnapshotIdentityTests(unittest.TestCase):
    def test_accepts_matching_race_strategy_and_cutoff(self) -> None:
        value = snapshot((bet(),))
        self.assertEqual(value.bets[0].race_id, value.identity.race_id)

    def test_rejects_race_id_mismatch(self) -> None:
        with self.assertRaises(ValueError):
            snapshot((bet(race_id=102),))

    def test_rejects_strategy_id_mismatch(self) -> None:
        with self.assertRaises(ValueError):
            snapshot((bet(strategy_id="other-strategy"),))

    def test_rejects_cutoff_mismatch(self) -> None:
        with self.assertRaises(ValueError):
            snapshot((bet(placed_at_cutoff=datetime(2026, 7, 25, 10, 0, tzinfo=UTC)),))

    def test_accepts_equal_cutoff_with_different_timezone_representation(self) -> None:
        same_instant = datetime(2026, 7, 25, 18, 0, tzinfo=timezone(timedelta(hours=9)))
        value = snapshot((bet(placed_at_cutoff=same_instant),))
        self.assertEqual(value.bets[0].placed_at_cutoff, value.identity.information_cutoff)

    def test_does_not_compare_run_id_with_bets(self) -> None:
        value = snapshot((bet(),), identity=snapshot_identity(run_id="another-run"))
        self.assertEqual(value.identity.run_id, "another-run")

    def test_does_not_compare_strategy_config_hash_with_bets(self) -> None:
        value = snapshot((bet(),), identity=snapshot_identity(strategy_config_hash="b" * 64))
        self.assertEqual(value.identity.strategy_config_hash, "b" * 64)


class SimulationBetPlanSnapshotBudgetTests(unittest.TestCase):
    def test_accepts_budget_with_unused_amount(self) -> None:
        value = snapshot((bet(),), budget=BetStakeBudget(500))
        self.assertEqual((value.allocated_amount, value.unallocated_amount), (100, 400))

    def test_accepts_budget_used_exactly(self) -> None:
        values = (bet(race_entry_ids=(1,)), bet(race_entry_ids=(2,), stake=200))
        value = snapshot(values, budget=BetStakeBudget(300))
        self.assertEqual((value.allocated_amount, value.unallocated_amount), (300, 0))

    def test_rejects_budget_exceeded_without_modifying_bets(self) -> None:
        values = (bet(race_entry_ids=(1,), stake=100), bet(race_entry_ids=(2,), stake=200))
        with self.assertRaises(ValueError):
            snapshot(values, budget=BetStakeBudget(200))
        self.assertEqual(tuple(item.stake for item in values), (100, 200))

    def test_empty_snapshot_accepts_zero_budget(self) -> None:
        value = snapshot((), budget=BetStakeBudget(0))
        self.assertEqual((value.allocated_amount, value.unallocated_amount), (0, 0))

    def test_empty_snapshot_accepts_positive_budget(self) -> None:
        value = snapshot((), budget=BetStakeBudget(600))
        self.assertEqual((value.allocated_amount, value.unallocated_amount), (0, 600))


class SimulationBetPlanSnapshotDuplicateTests(unittest.TestCase):
    def test_rejects_same_type_and_selection(self) -> None:
        with self.assertRaises(ValueError):
            snapshot((bet(stake=100), bet(stake=200, recommendation_rank=1)), budget=BetStakeBudget(300))

    def test_rejects_canonical_selection_duplicate_with_input_order_reversed(self) -> None:
        first = bet(bet_type="馬連", race_entry_ids=(1, 2))
        second = bet(bet_type="馬連", race_entry_ids=(2, 1), recommendation_rank=1)
        with self.assertRaises(ValueError):
            snapshot((first, second), budget=BetStakeBudget(200))

    def test_allows_same_selection_for_different_bet_types(self) -> None:
        quinella = bet(bet_type="馬連", race_entry_ids=(1, 2))
        wide = bet(bet_type="ワイド", race_entry_ids=(1, 2), recommendation_rank=1)
        value = snapshot((quinella, wide), budget=BetStakeBudget(200))
        self.assertEqual(value.bets, (quinella, wide))

    def test_allows_different_selection_for_same_bet_type(self) -> None:
        first = bet(bet_type="馬連", race_entry_ids=(1, 2))
        second = bet(bet_type="馬連", race_entry_ids=(1, 3), recommendation_rank=1)
        value = snapshot((first, second), budget=BetStakeBudget(200))
        self.assertEqual(value.bets, (first, second))

    def test_allows_duplicate_recommendation_ranks_when_identities_differ(self) -> None:
        first = bet(race_entry_ids=(1,), recommendation_rank=0)
        second = bet(race_entry_ids=(2,), recommendation_rank=0)
        value = snapshot((first, second), budget=BetStakeBudget(200))
        self.assertEqual(tuple(item.recommendation_rank for item in value.bets), (0, 0))


class SimulationBetPlanSnapshotPropertyAndBoundaryTests(unittest.TestCase):
    def test_properties_are_read_only_and_not_dataclass_fields(self) -> None:
        value = snapshot((bet(),), budget=BetStakeBudget(200))
        field_names = tuple(field.name for field in fields(SimulationBetPlanSnapshot))
        self.assertNotIn("allocated_amount", field_names)
        self.assertNotIn("unallocated_amount", field_names)
        self.assertIsInstance(type(value).allocated_amount, property)
        self.assertIsInstance(type(value).unallocated_amount, property)
        self.assertIsNone(type(value).allocated_amount.fset)
        self.assertIsNone(type(value).unallocated_amount.fset)

    def test_property_access_is_repeatable_without_state_change(self) -> None:
        value = snapshot((bet(),), budget=BetStakeBudget(200))
        self.assertEqual((value.allocated_amount, value.unallocated_amount), (100, 100))
        self.assertEqual((value.allocated_amount, value.unallocated_amount), (100, 100))

    def test_does_not_recalculate_or_compare_policy_identity(self) -> None:
        alternate_policy = build_allocation_policy_identity(
            AllocationPolicyConfig("another-policy", "2", {"amount": 500})
        )
        value = snapshot((bet(),), policy=alternate_policy)
        self.assertIs(value.policy_identity, alternate_policy)

    def test_module_has_no_external_io_or_time_dependency(self) -> None:
        import scripts.simulation.bet_plan_snapshot as module

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
        self.assertNotIn("datetime.now", source)
        self.assertNotIn("Repository", source)

    def test_simulation_package_does_not_export_snapshot_early(self) -> None:
        import scripts.simulation as package

        self.assertFalse(hasattr(package, "SimulationBetPlanSnapshot"))


if __name__ == "__main__":
    unittest.main()
