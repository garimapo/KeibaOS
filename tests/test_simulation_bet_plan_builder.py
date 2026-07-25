"""Contract tests for ``SimulationBetPlanBuilder``."""

from __future__ import annotations

import ast
from datetime import UTC, datetime
import inspect
from typing import Sequence, get_type_hints
import unittest

from scripts.prediction.allocation_policy import (
    AllocationPolicyConfig,
    AllocationPolicyIdentity,
    build_allocation_policy_identity,
)
from scripts.prediction.bet_generator import BetRecommendation
from scripts.prediction.bet_strategy import BetPlan
from scripts.simulation.bet_plan_builder import SimulationBetPlanBuilder
from scripts.simulation.bet_plan_identity import SimulationBetPlanIdentity
from scripts.simulation.bet_plan_snapshot import SimulationBetPlanSnapshot
from scripts.simulation.models import SimulationBet
from scripts.simulation.stake_allocation import (
    AllocatedBetRecommendation,
    BetAllocationPlan,
    BetStakeBudget,
)


HASH = "a" * 64
CUTOFF = datetime(2026, 7, 25, 9, 0, tzinfo=UTC)


class RecordingResolver:
    """Test-only resolver that records exactly what the builder passes to it."""

    def __init__(self, responses: dict[tuple[int, ...], object] | None = None) -> None:
        self.calls: list[tuple[int, tuple[int, ...]]] = []
        self.responses = {} if responses is None else responses

    def resolve_race_entry_ids(
        self,
        *,
        race_id: int,
        horse_ids: Sequence[int],
    ) -> tuple[int, ...]:
        supplied_ids = tuple(horse_ids)
        self.calls.append((race_id, supplied_ids))
        response = self.responses.get(supplied_ids, tuple(identifier + 1000 for identifier in supplied_ids))
        if isinstance(response, BaseException):
            raise response
        return response  # type: ignore[return-value]


class MissingResolverMethod:
    pass


class NonCallableResolverMethod:
    resolve_race_entry_ids = "not-callable"


class DuckAllocationPlan:
    allocations = ()


def policy_identity() -> AllocationPolicyIdentity:
    return build_allocation_policy_identity(
        AllocationPolicyConfig(
            policy_name="fixed_stake_per_recommendation",
            policy_version="1",
            parameters={"stake_amount": 100},
        )
    )


def identity(**overrides: object) -> SimulationBetPlanIdentity:
    values: dict[str, object] = {
        "run_id": "run-builder",
        "race_id": 101,
        "strategy_id": "strategy-builder",
        "strategy_config_hash": HASH,
        "information_cutoff": CUTOFF,
    }
    values.update(overrides)
    return SimulationBetPlanIdentity(**values)  # type: ignore[arg-type]


def recommendation(
    *,
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


def allocation_plan(
    *recommendations: BetRecommendation,
    stakes: tuple[int, ...] | None = None,
    plan_identity: SimulationBetPlanIdentity | None = None,
    budget: BetStakeBudget | None = None,
) -> BetAllocationPlan:
    selected_identity = identity() if plan_identity is None else plan_identity
    selected_stakes = (100,) * len(recommendations) if stakes is None else stakes
    return BetAllocationPlan(
        identity=selected_identity,
        policy_identity=policy_identity(),
        bet_plan=BetPlan(
            strategy_name="BuilderTestStrategy",
            recommendations=tuple(recommendations),
            candidate_count=len(recommendations),
        ),
        allocations=tuple(
            AllocatedBetRecommendation(
                recommendation=item,
                purchase_order=index,
                stake=selected_stakes[index],
            )
            for index, item in enumerate(recommendations)
        ),
        budget=BetStakeBudget(sum(selected_stakes)) if budget is None else budget,
    )


class SimulationBetPlanBuilderConstructorTests(unittest.TestCase):
    def test_accepts_callable_resolver(self) -> None:
        self.assertIsInstance(SimulationBetPlanBuilder(selection_resolver=RecordingResolver()), SimulationBetPlanBuilder)

    def test_preserves_resolver_object_identity(self) -> None:
        resolver = RecordingResolver()
        builder = SimulationBetPlanBuilder(selection_resolver=resolver)
        self.assertIs(builder._selection_resolver, resolver)

    def test_rejects_none_resolver(self) -> None:
        with self.assertRaises(ValueError):
            SimulationBetPlanBuilder(selection_resolver=None)  # type: ignore[arg-type]

    def test_rejects_resolver_without_method(self) -> None:
        with self.assertRaises(ValueError):
            SimulationBetPlanBuilder(selection_resolver=MissingResolverMethod())  # type: ignore[arg-type]

    def test_rejects_resolver_with_non_callable_method(self) -> None:
        with self.assertRaises(ValueError):
            SimulationBetPlanBuilder(selection_resolver=NonCallableResolverMethod())  # type: ignore[arg-type]

    def test_rejects_resolver_class_instead_of_instance(self) -> None:
        with self.assertRaises(ValueError):
            SimulationBetPlanBuilder(selection_resolver=RecordingResolver)  # type: ignore[arg-type]

    def test_constructor_is_keyword_only(self) -> None:
        with self.assertRaises(TypeError):
            SimulationBetPlanBuilder(RecordingResolver())  # type: ignore[call-arg]

    def test_constructor_does_not_call_resolver(self) -> None:
        resolver = RecordingResolver()
        SimulationBetPlanBuilder(selection_resolver=resolver)
        self.assertEqual(resolver.calls, [])

    def test_constructor_does_not_runtime_check_protocol(self) -> None:
        source = inspect.getsource(SimulationBetPlanBuilder.__init__)
        self.assertNotIn("isinstance(selection_resolver, RaceEntrySelectionResolver)", source)

    def test_is_slotted_without_public_resolver_property(self) -> None:
        builder = SimulationBetPlanBuilder(selection_resolver=RecordingResolver())
        self.assertFalse(hasattr(builder, "__dict__"))
        self.assertFalse(hasattr(type(builder), "selection_resolver"))


class SimulationBetPlanBuilderSignatureTests(unittest.TestCase):
    def test_build_signature_is_keyword_only(self) -> None:
        signature = inspect.signature(SimulationBetPlanBuilder.build)
        self.assertEqual(tuple(signature.parameters), ("self", "allocation_plan"))
        self.assertIs(signature.parameters["allocation_plan"].kind, inspect.Parameter.KEYWORD_ONLY)
        self.assertIs(signature.parameters["allocation_plan"].default, inspect.Parameter.empty)

    def test_build_has_no_varargs_or_extra_public_build_methods(self) -> None:
        signature = inspect.signature(SimulationBetPlanBuilder.build)
        kinds = tuple(parameter.kind for parameter in signature.parameters.values())
        self.assertNotIn(inspect.Parameter.VAR_POSITIONAL, kinds)
        self.assertNotIn(inspect.Parameter.VAR_KEYWORD, kinds)
        public_methods = {
            name
            for name, value in inspect.getmembers(SimulationBetPlanBuilder, inspect.isfunction)
            if not name.startswith("_")
        }
        self.assertEqual(public_methods, {"build"})

    def test_build_type_hints_match_contract(self) -> None:
        hints = get_type_hints(SimulationBetPlanBuilder.build)
        self.assertIs(hints["allocation_plan"], BetAllocationPlan)
        self.assertIs(hints["return"], SimulationBetPlanSnapshot)

    def test_build_rejects_positional_plan(self) -> None:
        builder = SimulationBetPlanBuilder(selection_resolver=RecordingResolver())
        with self.assertRaises(TypeError):
            builder.build(allocation_plan())  # type: ignore[call-arg]


class SimulationBetPlanBuilderInputValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.builder = SimulationBetPlanBuilder(selection_resolver=RecordingResolver())

    def test_rejects_none_allocation_plan(self) -> None:
        with self.assertRaises(ValueError):
            self.builder.build(allocation_plan=None)  # type: ignore[arg-type]

    def test_rejects_mapping_allocation_plan(self) -> None:
        with self.assertRaises(ValueError):
            self.builder.build(allocation_plan={})  # type: ignore[arg-type]

    def test_rejects_tuple_allocation_plan(self) -> None:
        with self.assertRaises(ValueError):
            self.builder.build(allocation_plan=())  # type: ignore[arg-type]

    def test_rejects_plain_object_allocation_plan(self) -> None:
        with self.assertRaises(ValueError):
            self.builder.build(allocation_plan=object())  # type: ignore[arg-type]

    def test_rejects_bet_plan_as_allocation_plan(self) -> None:
        with self.assertRaises(ValueError):
            self.builder.build(allocation_plan=BetPlan("strategy", (), 0))  # type: ignore[arg-type]

    def test_rejects_snapshot_as_allocation_plan(self) -> None:
        snapshot = SimulationBetPlanSnapshot(identity=identity(), policy_identity=policy_identity(), budget=BetStakeBudget(0), bets=())
        with self.assertRaises(ValueError):
            self.builder.build(allocation_plan=snapshot)  # type: ignore[arg-type]

    def test_rejects_duck_typed_allocation_plan(self) -> None:
        with self.assertRaises(ValueError):
            self.builder.build(allocation_plan=DuckAllocationPlan())  # type: ignore[arg-type]


class SimulationBetPlanBuilderBuildTests(unittest.TestCase):
    def test_builds_one_allocation_with_full_field_mapping(self) -> None:
        item = recommendation(rank=7, horse_ids=(3,))
        plan = allocation_plan(item, stakes=(300,))
        resolver = RecordingResolver({(3,): (103,)})

        result = SimulationBetPlanBuilder(selection_resolver=resolver).build(allocation_plan=plan)

        self.assertIsInstance(result, SimulationBetPlanSnapshot)
        self.assertEqual(resolver.calls, [(101, (3,))])
        self.assertEqual(len(result.bets), 1)
        bet = result.bets[0]
        self.assertEqual(bet.race_id, plan.identity.race_id)
        self.assertEqual(bet.strategy_id, plan.identity.strategy_id)
        self.assertEqual(bet.bet_type, item.bet_type)
        self.assertEqual(bet.race_entry_ids, (103,))
        self.assertEqual(bet.stake, 300)
        self.assertEqual(bet.recommendation_rank, item.rank)
        self.assertEqual(bet.placed_at_cutoff, plan.identity.information_cutoff)

    def test_passes_recommendation_horse_ids_in_original_order(self) -> None:
        item = recommendation(rank=1, bet_type="馬連", horse_ids=(3, 1))
        resolver = RecordingResolver({(3, 1): (103, 101)})
        SimulationBetPlanBuilder(selection_resolver=resolver).build(allocation_plan=allocation_plan(item))
        self.assertEqual(resolver.calls, [(101, (3, 1))])

    def test_preserves_allocation_order_without_rank_sorting(self) -> None:
        first = recommendation(rank=9, horse_ids=(3,))
        second = recommendation(rank=1, bet_type="馬連", horse_ids=(2, 1))
        resolver = RecordingResolver()
        result = SimulationBetPlanBuilder(selection_resolver=resolver).build(allocation_plan=allocation_plan(first, second))
        self.assertEqual(tuple(bet.recommendation_rank for bet in result.bets), (9, 1))
        self.assertEqual(resolver.calls, [(101, (3,)), (101, (2, 1))])

    def test_preserves_allocation_order_without_bet_type_or_stake_sorting(self) -> None:
        first = recommendation(rank=3, bet_type="ワイド", horse_ids=(4, 2))
        second = recommendation(rank=2, bet_type="単勝", horse_ids=(1,))
        plan = allocation_plan(first, second, stakes=(300, 100))
        result = SimulationBetPlanBuilder(selection_resolver=RecordingResolver()).build(allocation_plan=plan)
        self.assertEqual(tuple(bet.bet_type for bet in result.bets), ("ワイド", "単勝"))
        self.assertEqual(tuple(bet.stake for bet in result.bets), (300, 100))

    def test_calls_resolver_once_per_allocation_in_tuple_order(self) -> None:
        entries = (
            recommendation(rank=4, horse_ids=(3,)),
            recommendation(rank=3, bet_type="馬連", horse_ids=(4, 1)),
            recommendation(rank=2, bet_type="ワイド", horse_ids=(5, 2)),
            recommendation(rank=1, bet_type="3連複", horse_ids=(6, 3, 1)),
        )
        resolver = RecordingResolver()
        result = SimulationBetPlanBuilder(selection_resolver=resolver).build(allocation_plan=allocation_plan(*entries))
        self.assertEqual(len(resolver.calls), 4)
        self.assertEqual(tuple(call[1] for call in resolver.calls), tuple(item.horse_ids for item in entries))
        self.assertEqual(tuple(bet.bet_type for bet in result.bets), tuple(item.bet_type for item in entries))

    def test_does_not_cache_same_selection_for_different_bet_types(self) -> None:
        quinella = recommendation(rank=1, bet_type="馬連", horse_ids=(3, 1))
        wide = recommendation(rank=2, bet_type="ワイド", horse_ids=(3, 1))
        resolver = RecordingResolver({(3, 1): (103, 101)})
        result = SimulationBetPlanBuilder(selection_resolver=resolver).build(allocation_plan=allocation_plan(quinella, wide))
        self.assertEqual(resolver.calls, [(101, (3, 1)), (101, (3, 1))])
        self.assertEqual(tuple(bet.bet_type for bet in result.bets), ("馬連", "ワイド"))

    def test_keeps_recommendation_rank_without_reindexing(self) -> None:
        item = recommendation(rank=12, horse_ids=(1,))
        result = SimulationBetPlanBuilder(selection_resolver=RecordingResolver()).build(allocation_plan=allocation_plan(item))
        self.assertEqual(result.bets[0].recommendation_rank, 12)

    def test_allows_duplicate_ranks_when_bet_identities_differ(self) -> None:
        first = recommendation(rank=1, horse_ids=(1,))
        second = recommendation(rank=1, bet_type="馬連", horse_ids=(2, 1))
        result = SimulationBetPlanBuilder(selection_resolver=RecordingResolver()).build(allocation_plan=allocation_plan(first, second))
        self.assertEqual(tuple(bet.recommendation_rank for bet in result.bets), (1, 1))

    def test_maps_all_supported_bet_types_without_conversion(self) -> None:
        entries = (
            recommendation(rank=1, bet_type="単勝", horse_ids=(1,)),
            recommendation(rank=2, bet_type="馬連", horse_ids=(2, 1)),
            recommendation(rank=3, bet_type="ワイド", horse_ids=(3, 1)),
            recommendation(rank=4, bet_type="3連複", horse_ids=(4, 2, 1)),
        )
        result = SimulationBetPlanBuilder(selection_resolver=RecordingResolver()).build(allocation_plan=allocation_plan(*entries))
        self.assertEqual(tuple(bet.bet_type for bet in result.bets), tuple(item.bet_type for item in entries))

    def test_preserves_snapshot_identity_policy_and_budget_object_identities(self) -> None:
        item = recommendation(rank=1, horse_ids=(1,))
        plan = allocation_plan(item)
        result = SimulationBetPlanBuilder(selection_resolver=RecordingResolver()).build(allocation_plan=plan)
        self.assertIs(result.identity, plan.identity)
        self.assertIs(result.policy_identity, plan.policy_identity)
        self.assertIs(result.budget, plan.budget)

    def test_creates_new_simulation_bet_not_recommendation_or_allocation(self) -> None:
        item = recommendation(rank=1, horse_ids=(1,))
        plan = allocation_plan(item)
        result = SimulationBetPlanBuilder(selection_resolver=RecordingResolver()).build(allocation_plan=plan)
        self.assertIsInstance(result.bets[0], SimulationBet)
        self.assertIsNot(result.bets[0], plan.allocations[0])
        self.assertIsNot(result.bets[0], item)

    def test_empty_allocation_plan_returns_empty_snapshot_without_resolver_call(self) -> None:
        plan = allocation_plan()
        resolver = RecordingResolver()
        result = SimulationBetPlanBuilder(selection_resolver=resolver).build(allocation_plan=plan)
        self.assertEqual(resolver.calls, [])
        self.assertEqual(result.bets, ())
        self.assertIs(result.identity, plan.identity)
        self.assertIs(result.policy_identity, plan.policy_identity)
        self.assertIs(result.budget, plan.budget)
        self.assertEqual(result.allocated_amount, 0)
        self.assertEqual(result.unallocated_amount, plan.budget.total_amount)


class SimulationBetPlanBuilderResolverValidationTests(unittest.TestCase):
    def _build_with_response(self, response: object) -> None:
        item = recommendation(rank=1, horse_ids=(1,))
        resolver = RecordingResolver({(1,): response})
        SimulationBetPlanBuilder(selection_resolver=resolver).build(allocation_plan=allocation_plan(item))

    def test_accepts_tuple_response(self) -> None:
        self._build_with_response((101,))

    def test_rejects_list_response_without_coercion(self) -> None:
        with self.assertRaises(ValueError):
            self._build_with_response([101])

    def test_rejects_generator_response_without_coercion(self) -> None:
        with self.assertRaises(ValueError):
            self._build_with_response((value for value in (101,)))

    def test_rejects_set_response_without_coercion(self) -> None:
        with self.assertRaises(ValueError):
            self._build_with_response({101})

    def test_rejects_mapping_response_without_coercion(self) -> None:
        with self.assertRaises(ValueError):
            self._build_with_response({"entry": 101})

    def test_rejects_text_response_without_coercion(self) -> None:
        with self.assertRaises(ValueError):
            self._build_with_response("101")

    def test_rejects_bytes_response_without_coercion(self) -> None:
        with self.assertRaises(ValueError):
            self._build_with_response(b"101")

    def test_rejects_none_response_without_coercion(self) -> None:
        with self.assertRaises(ValueError):
            self._build_with_response(None)

    def test_rejects_too_short_tuple_response(self) -> None:
        item = recommendation(rank=1, bet_type="馬連", horse_ids=(1, 2))
        resolver = RecordingResolver({(1, 2): (101,)})
        with self.assertRaises(ValueError):
            SimulationBetPlanBuilder(selection_resolver=resolver).build(allocation_plan=allocation_plan(item))

    def test_rejects_too_long_tuple_response(self) -> None:
        item = recommendation(rank=1, horse_ids=(1,))
        resolver = RecordingResolver({(1,): (101, 102)})
        with self.assertRaises(ValueError):
            SimulationBetPlanBuilder(selection_resolver=resolver).build(allocation_plan=allocation_plan(item))

    def test_rejects_empty_response_for_non_empty_horse_ids(self) -> None:
        with self.assertRaises(ValueError):
            self._build_with_response(())

    def test_delegates_invalid_tuple_elements_to_simulation_bet(self) -> None:
        with self.assertRaises(ValueError):
            self._build_with_response((True,))

    def test_delegates_duplicate_race_entry_ids_to_simulation_bet(self) -> None:
        item = recommendation(rank=1, bet_type="馬連", horse_ids=(1, 2))
        resolver = RecordingResolver({(1, 2): (101, 101)})
        with self.assertRaises(ValueError):
            SimulationBetPlanBuilder(selection_resolver=resolver).build(allocation_plan=allocation_plan(item))

    def test_delegates_wrong_selection_count_to_simulation_bet(self) -> None:
        item = recommendation(rank=1, bet_type="馬連", horse_ids=(1,))
        with self.assertRaises(ValueError):
            SimulationBetPlanBuilder(selection_resolver=RecordingResolver({(1,): (101,)})).build(allocation_plan=allocation_plan(item))


class SimulationBetPlanBuilderFailurePropagationTests(unittest.TestCase):
    def test_propagates_resolver_value_error_unchanged(self) -> None:
        error = ValueError("resolver failed")
        resolver = RecordingResolver({(1,): error})
        builder = SimulationBetPlanBuilder(selection_resolver=resolver)
        with self.assertRaises(ValueError) as raised:
            builder.build(allocation_plan=allocation_plan(recommendation(rank=1, horse_ids=(1,))))
        self.assertIs(raised.exception, error)

    def test_propagates_arbitrary_resolver_exception_unchanged(self) -> None:
        error = RuntimeError("repository boundary failure")
        resolver = RecordingResolver({(1,): error})
        builder = SimulationBetPlanBuilder(selection_resolver=resolver)
        with self.assertRaises(RuntimeError) as raised:
            builder.build(allocation_plan=allocation_plan(recommendation(rank=1, horse_ids=(1,))))
        self.assertIs(raised.exception, error)

    def test_stops_processing_after_second_resolver_failure(self) -> None:
        first = recommendation(rank=1, horse_ids=(1,))
        second = recommendation(rank=2, bet_type="馬連", horse_ids=(2, 3))
        third = recommendation(rank=3, bet_type="ワイド", horse_ids=(4, 5))
        error = ValueError("second fails")
        resolver = RecordingResolver({(2, 3): error})
        with self.assertRaises(ValueError):
            SimulationBetPlanBuilder(selection_resolver=resolver).build(allocation_plan=allocation_plan(first, second, third))
        self.assertEqual(resolver.calls, [(101, (1,)), (101, (2, 3))])

    def test_propagates_simulation_bet_validation_error(self) -> None:
        item = recommendation(rank=1, bet_type="unknown", horse_ids=(1,))
        with self.assertRaises(ValueError):
            SimulationBetPlanBuilder(selection_resolver=RecordingResolver()).build(allocation_plan=allocation_plan(item))

    def test_delegates_duplicate_snapshot_bets_to_snapshot_constructor(self) -> None:
        first = recommendation(rank=1, horse_ids=(1,))
        second = recommendation(rank=2, horse_ids=(2,))
        resolver = RecordingResolver({(1,): (101,), (2,): (101,)})
        with self.assertRaises(ValueError):
            SimulationBetPlanBuilder(selection_resolver=resolver).build(allocation_plan=allocation_plan(first, second))
        self.assertEqual(resolver.calls, [(101, (1,)), (101, (2,))])


class SimulationBetPlanBuilderDependencyTests(unittest.TestCase):
    def test_production_module_has_only_contract_dependencies(self) -> None:
        import scripts.simulation.bet_plan_builder as module

        tree = ast.parse(inspect.getsource(module))
        imports = [
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        ]
        self.assertEqual(
            imports,
            [
                "__future__",
                "scripts.simulation.bet_plan_snapshot",
                "scripts.simulation.models",
                "scripts.simulation.selection_resolver",
                "scripts.simulation.stake_allocation",
            ],
        )

    def test_production_module_does_not_define_concrete_resolver_or_external_access(self) -> None:
        import scripts.simulation.bet_plan_builder as module

        source = inspect.getsource(module)
        tree = ast.parse(source)
        class_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
        self.assertEqual(class_names, {"SimulationBetPlanBuilder"})
        forbidden = ("sqlite3", "repository", "provider", "requests", "urllib", "datetime.now", "random")
        self.assertFalse(any(value in source.lower() for value in forbidden))

    def test_package_does_not_export_builder_early(self) -> None:
        import scripts.simulation as package

        self.assertFalse(hasattr(package, "SimulationBetPlanBuilder"))

    def test_does_not_add_target_race_count(self) -> None:
        import scripts.simulation.bet_plan_builder as module

        self.assertNotIn("target_race_count", inspect.getsource(module))


if __name__ == "__main__":
    unittest.main()
