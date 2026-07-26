"""Contract tests for simulation bet-plan snapshot read and write Protocols."""

from __future__ import annotations

import ast
from dataclasses import fields
from datetime import UTC, datetime
import inspect
from pathlib import Path
import textwrap
from types import ModuleType
from typing import Protocol, get_type_hints
import unittest

import scripts.simulation as simulation_package
import scripts.simulation.bet_plan_snapshot_repository as repository_module
from scripts.prediction.allocation_policy import AllocationPolicyConfig, build_allocation_policy_identity
from scripts.simulation.bet_plan_identity import SimulationBetPlanIdentity
from scripts.simulation.bet_plan_snapshot import SimulationBetPlanSnapshot
from scripts.simulation.bet_plan_snapshot_repository import (
    SimulationBetPlanSnapshotRepository,
    SimulationBetPlanSnapshotSource,
)
from scripts.simulation.stake_allocation import BetStakeBudget


HASH = "a" * 64


class StubSnapshotSource:
    """Test-only structural source implementation."""

    def load_snapshot(
        self,
        *,
        identity: SimulationBetPlanIdentity,
    ) -> SimulationBetPlanSnapshot | None:
        return None


class StubSnapshotRepository:
    """Test-only structural repository implementation."""

    def save_snapshot(
        self,
        *,
        snapshot: SimulationBetPlanSnapshot,
    ) -> None:
        return None


class StubSnapshotStore:
    """Test-only structural implementation of both independent Protocols."""

    def load_snapshot(
        self,
        *,
        identity: SimulationBetPlanIdentity,
    ) -> SimulationBetPlanSnapshot | None:
        return None

    def save_snapshot(
        self,
        *,
        snapshot: SimulationBetPlanSnapshot,
    ) -> None:
        return None


def identity() -> SimulationBetPlanIdentity:
    return SimulationBetPlanIdentity(
        run_id="run-1",
        race_id=101,
        strategy_id="strategy-1",
        strategy_config_hash=HASH,
        information_cutoff=datetime(2026, 7, 26, 9, 0, tzinfo=UTC),
    )


def empty_snapshot() -> SimulationBetPlanSnapshot:
    return SimulationBetPlanSnapshot(
        identity=identity(),
        policy_identity=build_allocation_policy_identity(
            AllocationPolicyConfig("fixed-stake", "1", {"stake": 100})
        ),
        budget=BetStakeBudget(0),
        bets=(),
    )


def public_methods(value: type[Protocol]) -> set[str]:
    return {
        name
        for name, member in value.__dict__.items()
        if inspect.isfunction(member) and not name.startswith("_")
    }


def assert_declaration_only(test_case: unittest.TestCase, method: object) -> None:
    tree = ast.parse(textwrap.dedent(inspect.getsource(method)))
    body = tree.body[0].body
    test_case.assertEqual(len(body), 1)
    test_case.assertIsInstance(body[0], ast.Expr)
    test_case.assertIsInstance(body[0].value, ast.Constant)
    test_case.assertIs(body[0].value.value, Ellipsis)


class SimulationBetPlanSnapshotSourceProtocolTests(unittest.TestCase):
    def test_source_is_a_structural_protocol_without_runtime_checkable(self) -> None:
        self.assertTrue(SimulationBetPlanSnapshotSource._is_protocol)
        self.assertFalse(SimulationBetPlanSnapshotSource._is_runtime_protocol)
        self.assertIsNot(SimulationBetPlanSnapshotSource, Protocol)

    def test_source_cannot_be_instantiated_as_a_concrete_class(self) -> None:
        with self.assertRaises(TypeError):
            SimulationBetPlanSnapshotSource()

    def test_source_has_only_load_snapshot_public_method(self) -> None:
        self.assertEqual(public_methods(SimulationBetPlanSnapshotSource), {"load_snapshot"})

    def test_load_snapshot_has_exact_keyword_only_signature(self) -> None:
        signature = inspect.signature(SimulationBetPlanSnapshotSource.load_snapshot)
        self.assertEqual(tuple(signature.parameters), ("self", "identity"))
        parameter = signature.parameters["identity"]
        self.assertIs(parameter.kind, inspect.Parameter.KEYWORD_ONLY)
        self.assertIs(parameter.default, inspect.Parameter.empty)

    def test_load_snapshot_has_no_varargs_or_async_contract(self) -> None:
        signature = inspect.signature(SimulationBetPlanSnapshotSource.load_snapshot)
        kinds = {parameter.kind for parameter in signature.parameters.values()}
        self.assertNotIn(inspect.Parameter.VAR_POSITIONAL, kinds)
        self.assertNotIn(inspect.Parameter.VAR_KEYWORD, kinds)
        self.assertFalse(inspect.iscoroutinefunction(SimulationBetPlanSnapshotSource.load_snapshot))

    def test_load_snapshot_type_hints_match_snapshot_boundary(self) -> None:
        hints = get_type_hints(SimulationBetPlanSnapshotSource.load_snapshot)
        self.assertIs(hints["identity"], SimulationBetPlanIdentity)
        self.assertEqual(hints["return"], SimulationBetPlanSnapshot | None)

    def test_load_snapshot_is_a_declaration_only(self) -> None:
        assert_declaration_only(self, SimulationBetPlanSnapshotSource.load_snapshot)

    def test_not_found_is_none_while_an_empty_plan_remains_a_snapshot(self) -> None:
        self.assertIsNone(StubSnapshotSource().load_snapshot(identity=identity()))
        snapshot = empty_snapshot()
        self.assertIsInstance(snapshot, SimulationBetPlanSnapshot)
        self.assertEqual(snapshot.bets, ())


class SimulationBetPlanSnapshotRepositoryProtocolTests(unittest.TestCase):
    def test_repository_is_a_structural_protocol_without_runtime_checkable(self) -> None:
        self.assertTrue(SimulationBetPlanSnapshotRepository._is_protocol)
        self.assertFalse(SimulationBetPlanSnapshotRepository._is_runtime_protocol)
        self.assertIsNot(SimulationBetPlanSnapshotRepository, Protocol)

    def test_repository_cannot_be_instantiated_as_a_concrete_class(self) -> None:
        with self.assertRaises(TypeError):
            SimulationBetPlanSnapshotRepository()

    def test_repository_has_only_save_snapshot_public_method(self) -> None:
        self.assertEqual(public_methods(SimulationBetPlanSnapshotRepository), {"save_snapshot"})

    def test_save_snapshot_has_exact_keyword_only_signature(self) -> None:
        signature = inspect.signature(SimulationBetPlanSnapshotRepository.save_snapshot)
        self.assertEqual(tuple(signature.parameters), ("self", "snapshot"))
        parameter = signature.parameters["snapshot"]
        self.assertIs(parameter.kind, inspect.Parameter.KEYWORD_ONLY)
        self.assertIs(parameter.default, inspect.Parameter.empty)

    def test_save_snapshot_has_no_varargs_or_async_contract(self) -> None:
        signature = inspect.signature(SimulationBetPlanSnapshotRepository.save_snapshot)
        kinds = {parameter.kind for parameter in signature.parameters.values()}
        self.assertNotIn(inspect.Parameter.VAR_POSITIONAL, kinds)
        self.assertNotIn(inspect.Parameter.VAR_KEYWORD, kinds)
        self.assertFalse(inspect.iscoroutinefunction(SimulationBetPlanSnapshotRepository.save_snapshot))

    def test_save_snapshot_type_hints_match_snapshot_boundary(self) -> None:
        hints = get_type_hints(SimulationBetPlanSnapshotRepository.save_snapshot)
        self.assertIs(hints["snapshot"], SimulationBetPlanSnapshot)
        self.assertIs(hints["return"], type(None))

    def test_save_snapshot_is_a_declaration_only(self) -> None:
        assert_declaration_only(self, SimulationBetPlanSnapshotRepository.save_snapshot)


class SimulationBetPlanSnapshotProtocolIndependenceTests(unittest.TestCase):
    def test_protocols_have_no_inheritance_relationship(self) -> None:
        self.assertEqual(SimulationBetPlanSnapshotSource.__bases__, (Protocol,))
        self.assertEqual(SimulationBetPlanSnapshotRepository.__bases__, (Protocol,))

    def test_source_does_not_expose_repository_method(self) -> None:
        self.assertNotIn("save_snapshot", SimulationBetPlanSnapshotSource.__dict__)

    def test_repository_does_not_expose_source_method(self) -> None:
        self.assertNotIn("load_snapshot", SimulationBetPlanSnapshotRepository.__dict__)

    def test_source_only_stub_matches_source_signature(self) -> None:
        self.assertEqual(
            inspect.signature(StubSnapshotSource.load_snapshot),
            inspect.signature(SimulationBetPlanSnapshotSource.load_snapshot),
        )
        self.assertEqual(
            get_type_hints(StubSnapshotSource.load_snapshot),
            get_type_hints(SimulationBetPlanSnapshotSource.load_snapshot),
        )

    def test_repository_only_stub_matches_repository_signature(self) -> None:
        self.assertEqual(
            inspect.signature(StubSnapshotRepository.save_snapshot),
            inspect.signature(SimulationBetPlanSnapshotRepository.save_snapshot),
        )
        self.assertEqual(
            get_type_hints(StubSnapshotRepository.save_snapshot),
            get_type_hints(SimulationBetPlanSnapshotRepository.save_snapshot),
        )

    def test_combined_stub_can_implement_both_boundaries(self) -> None:
        self.assertEqual(
            inspect.signature(StubSnapshotStore.load_snapshot),
            inspect.signature(SimulationBetPlanSnapshotSource.load_snapshot),
        )
        self.assertEqual(
            inspect.signature(StubSnapshotStore.save_snapshot),
            inspect.signature(SimulationBetPlanSnapshotRepository.save_snapshot),
        )


class SimulationBetPlanSnapshotProtocolModuleTests(unittest.TestCase):
    def test_module_uses_future_annotations_and_defines_only_two_protocols(self) -> None:
        tree = ast.parse(inspect.getsource(repository_module))
        future_imports = [
            node
            for node in tree.body
            if isinstance(node, ast.ImportFrom) and node.module == "__future__"
        ]
        self.assertEqual(len(future_imports), 1)
        self.assertEqual([alias.name for alias in future_imports[0].names], ["annotations"])
        classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
        self.assertEqual([node.name for node in classes], [
            "SimulationBetPlanSnapshotSource",
            "SimulationBetPlanSnapshotRepository",
        ])

    def test_module_imports_only_protocol_and_snapshot_boundary_models(self) -> None:
        path = Path(__file__).parents[1] / "scripts/simulation/bet_plan_snapshot_repository.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported_modules = {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        } | {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        self.assertEqual(
            imported_modules,
            {"__future__", "typing", "bet_plan_identity", "bet_plan_snapshot"},
        )

    def test_module_has_no_concrete_persistence_or_exception_logic(self) -> None:
        tree = ast.parse(inspect.getsource(repository_module))
        self.assertFalse(any(isinstance(node, (ast.Raise, ast.Try)) for node in ast.walk(tree)))
        self.assertFalse(any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open" for node in ast.walk(tree)))
        source = inspect.getsource(repository_module)
        for forbidden in ("sqlite3", "BEGIN IMMEDIATE", "RepositoryValidationError", "RepositoryConflictError", "RepositoryDataIntegrityError"):
            self.assertNotIn(forbidden, source)

    def test_module_has_no_pipeline_executor_or_network_dependencies(self) -> None:
        source = inspect.getsource(repository_module)
        for forbidden in (
            "providers",
            "Resolver",
            "Builder",
            "PredictionPipeline",
            "Simulator",
            "requests",
            "httpx",
            "urllib",
            "socket",
            "datetime.now",
        ):
            self.assertNotIn(forbidden, source)

    def test_protocols_are_not_exported_from_simulation_package_root(self) -> None:
        self.assertFalse(hasattr(simulation_package, "SimulationBetPlanSnapshotSource"))
        self.assertFalse(hasattr(simulation_package, "SimulationBetPlanSnapshotRepository"))

    def test_existing_snapshot_and_identity_contracts_remain_in_their_modules(self) -> None:
        self.assertEqual(SimulationBetPlanIdentity.__module__, "scripts.simulation.bet_plan_identity")
        self.assertEqual(SimulationBetPlanSnapshot.__module__, "scripts.simulation.bet_plan_snapshot")
        self.assertEqual(tuple(field.name for field in fields(SimulationBetPlanSnapshot)), ("identity", "policy_identity", "budget", "bets"))

    def test_target_race_count_is_not_added_to_protocol_module(self) -> None:
        self.assertNotIn("target_race_count", inspect.getsource(repository_module))


if __name__ == "__main__":
    unittest.main()
