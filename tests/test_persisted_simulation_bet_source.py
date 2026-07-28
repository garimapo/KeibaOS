"""Tests for the persisted immutable simulation bet-plan Source adapter."""

from __future__ import annotations

import ast
from datetime import UTC, date, datetime
import inspect
from pathlib import Path
from typing import get_type_hints
import unittest

import scripts.simulation as simulation_package
import scripts.simulation.persisted_simulation_bet_source as adapter_module
from scripts.prediction.allocation_policy import AllocationPolicyConfig, build_allocation_policy_identity
from scripts.prediction.bet_strategy import StrategyConfig
from scripts.prediction.prediction_pipeline import RacePredictionInput
from scripts.prediction.track_engine import RaceTrackConditions
from scripts.simulation.bet_plan_identity import SimulationBetPlanIdentity
from scripts.simulation.bet_plan_snapshot import SimulationBetPlanSnapshot
from scripts.simulation.bet_plan_snapshot_repository import SimulationBetPlanSnapshotSource
from scripts.simulation.bet_source import SimulationBetSource
from scripts.simulation.models import (
    InputAuditEntry,
    InputSnapshotAudit,
    SimulationBet,
    SimulationRaceInput,
    SimulationRunContext,
    StrategyIdentity,
    build_strategy_identity,
)
from scripts.simulation.persisted_simulation_bet_source import PersistedSimulationBetSource
from scripts.simulation.repositories.errors import (
    RepositoryConflictError,
    RepositoryDataIntegrityError,
    RepositoryValidationError,
)
from scripts.simulation.stake_allocation import BetStakeBudget
from scripts.simulation.validation import SimulationValidationError


UTC_CUTOFF = datetime(2026, 7, 27, 9, 0, tzinfo=UTC)


def run_context() -> SimulationRunContext:
    return SimulationRunContext(
        run_id="run-persisted-source",
        dataset_id="dataset-1",
        started_at=UTC_CUTOFF,
        target_commit_id="commit-1",
    )


def strategy_identity() -> StrategyIdentity:
    return build_strategy_identity("PersistedBetSource", StrategyConfig())


def race_input(race_id: int = 101) -> SimulationRaceInput:
    pipeline_input = RacePredictionInput(
        {1: []},
        {1: "Jockey"},
        RaceTrackConditions("Tokyo", 1600, "turf", "firm"),
        {1: 2.0},
        1,
        race_id,
    )
    audit = InputSnapshotAudit(
        "dataset-1",
        "source",
        UTC_CUTOFF,
        (
            InputAuditEntry("entry", "entry/1", "source", "entry/1", 1, observed_at=UTC_CUTOFF),
            InputAuditEntry("odds", "odds/1", "source", "odds/1", 1, observed_at=UTC_CUTOFF),
            InputAuditEntry("jockey", "jockey/1", "source", "jockey/1", 1, observed_at=UTC_CUTOFF),
            InputAuditEntry("track", "track", "source", "track", None, observed_at=UTC_CUTOFF),
            InputAuditEntry(
                "past_race",
                "past_race/1/none",
                "source",
                "past_race/1/none",
                1,
                observed_at=UTC_CUTOFF,
            ),
        ),
        True,
    )
    return SimulationRaceInput(race_id, date(2026, 7, 27), UTC_CUTOFF, UTC_CUTOFF, pipeline_input, audit)


def identity(
    *,
    context: SimulationRunContext | None = None,
    race: SimulationRaceInput | None = None,
    strategy: StrategyIdentity | None = None,
    **overrides: object,
) -> SimulationBetPlanIdentity:
    selected_context = run_context() if context is None else context
    selected_race = race_input() if race is None else race
    selected_strategy = strategy_identity() if strategy is None else strategy
    values: dict[str, object] = {
        "run_id": selected_context.run_id,
        "race_id": selected_race.race_id,
        "strategy_id": selected_strategy.strategy_id,
        "strategy_config_hash": selected_strategy.strategy_config_hash,
        "information_cutoff": selected_race.information_cutoff,
    }
    values.update(overrides)
    return SimulationBetPlanIdentity(**values)  # type: ignore[arg-type]


def snapshot(
    *,
    context: SimulationRunContext | None = None,
    race: SimulationRaceInput | None = None,
    strategy: StrategyIdentity | None = None,
    snapshot_identity: SimulationBetPlanIdentity | None = None,
    bets: tuple[SimulationBet, ...] = (),
) -> SimulationBetPlanSnapshot:
    selected_identity = (
        identity(context=context, race=race, strategy=strategy)
        if snapshot_identity is None
        else snapshot_identity
    )
    return SimulationBetPlanSnapshot(
        identity=selected_identity,
        policy_identity=build_allocation_policy_identity(
            AllocationPolicyConfig("fixed-stake", "1", {"stake": 100})
        ),
        budget=BetStakeBudget(1000),
        bets=bets,
    )


def bet(race: SimulationRaceInput, strategy: StrategyIdentity, *, rank: int = 0) -> SimulationBet:
    return SimulationBet(
        race_id=race.race_id,
        strategy_id=strategy.strategy_id,
        bet_type="\u5358\u52dd",
        race_entry_ids=(1,),
        stake=100,
        recommendation_rank=rank,
        placed_at_cutoff=race.information_cutoff,
    )


class RecordingSnapshotSource:
    def __init__(self, response: object) -> None:
        self.response = response
        self.calls: list[SimulationBetPlanIdentity] = []

    def load_snapshot(self, *, identity: SimulationBetPlanIdentity) -> SimulationBetPlanSnapshot | None:
        self.calls.append(identity)
        if isinstance(self.response, BaseException):
            raise self.response
        return self.response  # type: ignore[return-value]


class MissingMethodSource:
    pass


class NonCallableMethodSource:
    load_snapshot = None


class PersistedSimulationBetSourceTests(unittest.TestCase):
    def make(self, *, source_response: object = None) -> tuple[PersistedSimulationBetSource, RecordingSnapshotSource]:
        source = RecordingSnapshotSource(source_response)
        return PersistedSimulationBetSource(run_context=run_context(), snapshot_source=source), source

    def test_constructor_is_keyword_only(self) -> None:
        signature = inspect.signature(PersistedSimulationBetSource)
        self.assertEqual(tuple(signature.parameters), ("run_context", "snapshot_source"))
        self.assertTrue(all(item.kind is inspect.Parameter.KEYWORD_ONLY for item in signature.parameters.values()))

    def test_constructor_type_hints_match_contracts(self) -> None:
        hints = get_type_hints(PersistedSimulationBetSource.__init__)
        self.assertIs(hints["run_context"], SimulationRunContext)
        self.assertIs(hints["snapshot_source"], SimulationBetPlanSnapshotSource)
        self.assertIs(hints["return"], type(None))

    def test_load_bets_signature_and_hints_match_source_protocol(self) -> None:
        self.assertEqual(
            inspect.signature(PersistedSimulationBetSource.load_bets),
            inspect.signature(SimulationBetSource.load_bets),
        )
        self.assertEqual(
            get_type_hints(PersistedSimulationBetSource.load_bets),
            get_type_hints(SimulationBetSource.load_bets),
        )

    def test_constructor_retains_injected_object_identities(self) -> None:
        context = run_context()
        source = RecordingSnapshotSource(None)
        adapter = PersistedSimulationBetSource(run_context=context, snapshot_source=source)
        self.assertIs(adapter._run_context, context)
        self.assertIs(adapter._snapshot_source, source)

    def test_constructor_does_not_call_source(self) -> None:
        source = RecordingSnapshotSource(None)
        PersistedSimulationBetSource(run_context=run_context(), snapshot_source=source)
        self.assertEqual(source.calls, [])

    def test_constructor_rejects_invalid_run_context(self) -> None:
        source = RecordingSnapshotSource(None)
        for value in (None, "context", object()):
            with self.subTest(value_type=type(value).__name__), self.assertRaises(ValueError):
                PersistedSimulationBetSource(run_context=value, snapshot_source=source)  # type: ignore[arg-type]
        self.assertEqual(source.calls, [])

    def test_constructor_rejects_missing_or_non_callable_source_method(self) -> None:
        for value in (MissingMethodSource(), NonCallableMethodSource(), None):
            with self.subTest(value_type=type(value).__name__), self.assertRaises(ValueError):
                PersistedSimulationBetSource(run_context=run_context(), snapshot_source=value)  # type: ignore[arg-type]

    def test_invalid_direct_inputs_raise_value_error_without_source_call(self) -> None:
        adapter, source = self.make()
        valid_race = race_input()
        valid_strategy = strategy_identity()
        for invalid_race, invalid_strategy in ((None, valid_strategy), (valid_race, None), ("race", "strategy")):
            with self.subTest(race=type(invalid_race).__name__, strategy=type(invalid_strategy).__name__), self.assertRaises(ValueError):
                adapter.load_bets(race_input=invalid_race, strategy_identity=invalid_strategy)  # type: ignore[arg-type]
        self.assertEqual(source.calls, [])

    def test_valid_call_constructs_requested_identity_and_calls_source_once(self) -> None:
        context = run_context()
        race = race_input(222)
        strategy = strategy_identity()
        expected = identity(context=context, race=race, strategy=strategy)
        source = RecordingSnapshotSource(snapshot(snapshot_identity=expected))
        adapter = PersistedSimulationBetSource(run_context=context, snapshot_source=source)

        returned = adapter.load_bets(race_input=race, strategy_identity=strategy)

        self.assertEqual(returned, ())
        self.assertEqual(source.calls, [expected])
        actual = source.calls[0]
        self.assertEqual(actual.run_id, context.run_id)
        self.assertEqual(actual.race_id, race.race_id)
        self.assertEqual(actual.strategy_id, strategy.strategy_id)
        self.assertEqual(actual.strategy_config_hash, strategy.strategy_config_hash)
        self.assertEqual(actual.information_cutoff, race.information_cutoff)

    def test_returns_exact_persisted_bets_tuple_and_bet_objects(self) -> None:
        context = run_context()
        race = race_input()
        strategy = strategy_identity()
        values = (bet(race, strategy),)
        stored = snapshot(context=context, race=race, strategy=strategy, bets=values)
        source = RecordingSnapshotSource(stored)
        adapter = PersistedSimulationBetSource(run_context=context, snapshot_source=source)

        returned = adapter.load_bets(race_input=race, strategy_identity=strategy)

        self.assertIs(returned, stored.bets)
        self.assertIs(returned, values)
        self.assertIs(returned[0], values[0])
        self.assertEqual(len(source.calls), 1)

    def test_stored_empty_snapshot_returns_its_exact_empty_tuple(self) -> None:
        context = run_context()
        race = race_input()
        strategy = strategy_identity()
        stored = snapshot(context=context, race=race, strategy=strategy)
        source = RecordingSnapshotSource(stored)
        adapter = PersistedSimulationBetSource(run_context=context, snapshot_source=source)

        returned = adapter.load_bets(race_input=race, strategy_identity=strategy)

        self.assertIs(returned, stored.bets)
        self.assertEqual(returned, ())

    def test_missing_snapshot_is_validation_error_with_required_metadata(self) -> None:
        adapter, source = self.make()
        race = race_input()
        with self.assertRaises(SimulationValidationError) as caught:
            adapter.load_bets(race_input=race, strategy_identity=strategy_identity())
        self.assertEqual(caught.exception.race_id, race.race_id)
        self.assertEqual(caught.exception.input_identifier, "simulation_bet_plan_snapshot")
        self.assertIn("not found", caught.exception.reason)
        self.assertEqual(len(source.calls), 1)

    def test_rejects_invalid_snapshot_type_with_validation_error(self) -> None:
        adapter, source = self.make(source_response=object())
        race = race_input()
        with self.assertRaises(SimulationValidationError) as caught:
            adapter.load_bets(race_input=race, strategy_identity=strategy_identity())
        self.assertEqual(caught.exception.race_id, race.race_id)
        self.assertEqual(caught.exception.input_identifier, "simulation_bet_plan_snapshot")
        self.assertIn("invalid type", caught.exception.reason)
        self.assertEqual(len(source.calls), 1)

    def test_rejects_each_identity_mismatch_with_validation_error(self) -> None:
        context = run_context()
        race = race_input()
        strategy = strategy_identity()
        mismatches = {
            "run_id": "other-run",
            "race_id": 102,
            "strategy_id": "other-strategy",
            "strategy_config_hash": "b" * 64,
            "information_cutoff": datetime(2026, 7, 27, 10, 0, tzinfo=UTC),
        }
        for field, value in mismatches.items():
            with self.subTest(field=field):
                mismatched_identity = identity(context=context, race=race, strategy=strategy, **{field: value})
                source = RecordingSnapshotSource(snapshot(snapshot_identity=mismatched_identity))
                adapter = PersistedSimulationBetSource(run_context=context, snapshot_source=source)
                with self.assertRaises(SimulationValidationError) as caught:
                    adapter.load_bets(race_input=race, strategy_identity=strategy)
                self.assertEqual(caught.exception.race_id, race.race_id)
                self.assertEqual(caught.exception.input_identifier, "simulation_bet_plan_snapshot")
                self.assertIn("identity", caught.exception.reason)
                self.assertEqual(len(source.calls), 1)

    def test_source_exceptions_propagate_as_same_object(self) -> None:
        for error in (
            RepositoryValidationError("validation"),
            RepositoryDataIntegrityError("integrity"),
            RepositoryConflictError("conflict"),
            RuntimeError("unexpected"),
        ):
            with self.subTest(error_type=type(error).__name__):
                adapter, source = self.make(source_response=error)
                with self.assertRaises(type(error)) as caught:
                    adapter.load_bets(race_input=race_input(), strategy_identity=strategy_identity())
                self.assertIs(caught.exception, error)
                self.assertEqual(len(source.calls), 1)

    def test_module_does_not_runtime_check_snapshot_source_protocol(self) -> None:
        source = inspect.getsource(PersistedSimulationBetSource.__init__)
        self.assertNotIn("isinstance(snapshot_source, SimulationBetPlanSnapshotSource)", source)

    def test_module_has_no_forbidden_dependencies_or_exception_wrapping(self) -> None:
        source = inspect.getsource(adapter_module)
        for forbidden in (
            "sqlite3",
            "SQLite",
            "SimulationBetPlanBuilder",
            "RepositoryBackedRaceEntrySelectionResolver",
            "PersistedRaceSimulationExecutor",
            "Provider",
            "PredictionPipeline",
            "Simulator",
            "datetime.now",
            "requests",
            "httpx",
            "cache",
            "retry",
        ):
            self.assertNotIn(forbidden, source)
        tree = ast.parse(source)
        self.assertFalse(any(isinstance(node, ast.Try) for node in ast.walk(tree)))

    def test_module_has_no_repository_exception_import_or_package_export(self) -> None:
        tree = ast.parse(inspect.getsource(adapter_module))
        imported = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        self.assertFalse(any("repositories.errors" in item for item in imported))
        self.assertFalse(hasattr(simulation_package, "PersistedSimulationBetSource"))

    def test_module_does_not_add_target_race_count_or_direct_database_path(self) -> None:
        source = inspect.getsource(adapter_module)
        self.assertNotIn("target_race_count", source)
        self.assertNotIn("database/keiba.db", source)

    def test_only_allowed_production_module_is_created(self) -> None:
        self.assertTrue((Path(__file__).parents[1] / "scripts/simulation/persisted_simulation_bet_source.py").is_file())


if __name__ == "__main__":
    unittest.main()
