"""Tests for ordered historical settlement and summary composition."""

from __future__ import annotations

import ast
from collections.abc import Iterator, Mapping
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
import inspect
from typing import get_type_hints
import unittest
from unittest.mock import patch

import scripts.simulation as simulation_package
import scripts.simulation.historical_settlement_simulation as composition_module
from scripts.prediction.allocation_policy import build_allocation_policy_identity
from scripts.simulation.bet_plan_identity import SimulationBetPlanIdentity
from scripts.simulation.bet_plan_snapshot import SimulationBetPlanSnapshot
from scripts.simulation.bet_plan_snapshot_repository import SimulationBetPlanSnapshotSource
from scripts.simulation.historical_input_snapshot_simulation_adapter import (
    HistoricalInputSnapshotSimulationAdapterError,
    build_simulation_race_input_from_historical_snapshot,
)
from scripts.simulation.historical_input_snapshots import HistoricalInputSnapshot
from scripts.simulation.historical_persisted_race_settlement_source import (
    HistoricalPersistedRaceSettlementSource,
)
from scripts.simulation.historical_settlement_simulation import (
    execute_historical_settlement_simulation,
)
from scripts.simulation.models import (
    SettlementStatus,
    SimulationBet,
    SimulationRaceInput,
    SimulationRunContext,
    SimulationSummary,
    StrategyIdentity,
)
from scripts.simulation.persisted_executor import PersistedRaceSimulationExecutor
from scripts.simulation.persisted_simulation_bet_source import PersistedSimulationBetSource
from scripts.simulation.repositories.errors import RepositoryDataIntegrityError
from scripts.simulation.repositories.interfaces import (
    PayoutPublication,
    PayoutRecord,
    PayoutRepository,
    PayoutStatus,
    PersistedRaceResult,
    PersistedRaceResultEntry,
    RaceResultEntryStatus,
    RaceResultRepository,
    RaceResultStatus,
)
from scripts.simulation.simulator import Simulator
from scripts.simulation.stake_allocation import BetStakeBudget
from scripts.simulation.validation import SimulationValidationError
from tests.test_historical_prediction_bet_plan_batch_execution import (
    _historical_snapshot,
    _run_context,
    _strategy_identity,
)


class RecordingPlanSource:
    def __init__(self, responses: Mapping[SimulationBetPlanIdentity, object] | None = None) -> None:
        self.responses = {} if responses is None else dict(responses)
        self.calls: list[SimulationBetPlanIdentity] = []

    def load_snapshot(
        self,
        *,
        identity: SimulationBetPlanIdentity,
    ) -> SimulationBetPlanSnapshot | None:
        self.calls.append(identity)
        response = self.responses.get(identity)
        if isinstance(response, BaseException):
            raise response
        return response  # type: ignore[return-value]


class RecordingResultRepository:
    def __init__(self, responses: Mapping[int, object] | None = None) -> None:
        self.responses = {} if responses is None else dict(responses)
        self.calls: list[int] = []

    def get_race_result(self, race_id: int) -> PersistedRaceResult | None:
        self.calls.append(race_id)
        response = self.responses.get(race_id)
        if isinstance(response, BaseException):
            raise response
        return response  # type: ignore[return-value]


class RecordingPayoutRepository:
    def __init__(
        self,
        responses: Mapping[tuple[int, str], tuple[PayoutPublication, ...]] | None = None,
        *,
        honor_cutoff: bool = True,
    ) -> None:
        self.responses = {} if responses is None else dict(responses)
        self.honor_cutoff = honor_cutoff
        self.calls: list[dict[str, object]] = []

    def get_latest_payout_publication(
        self,
        race_id: int,
        bet_type: str,
        observed_at_lte: datetime | None = None,
        require_complete: bool = True,
    ) -> PayoutPublication | None:
        self.calls.append(
            {
                "race_id": race_id,
                "bet_type": bet_type,
                "observed_at_lte": observed_at_lte,
                "require_complete": require_complete,
            }
        )
        values = self.responses.get((race_id, bet_type), ())
        eligible = values
        if self.honor_cutoff and observed_at_lte is not None:
            eligible = tuple(value for value in values if value.observed_at <= observed_at_lte)
        if require_complete:
            eligible = tuple(value for value in eligible if value.is_complete)
        if not eligible:
            return None
        return max(eligible, key=lambda value: (value.observed_at, value.publication_id or 0))


class CountingCutoffMapping(Mapping[int, datetime]):
    def __init__(self, values: dict[int, datetime]) -> None:
        self.values = values
        self.iterations = 0

    def __getitem__(self, key: int) -> datetime:
        return self.values[key]

    def __iter__(self) -> Iterator[int]:
        self.iterations += 1
        return iter(self.values)

    def __len__(self) -> int:
        return len(self.values)


class SnapshotTuple(tuple[HistoricalInputSnapshot, ...]):
    pass


class MissingMethod:
    pass


class NonCallablePlanSource:
    load_snapshot = None


class NonCallableResultRepository:
    get_race_result = None


class NonCallablePayoutRepository:
    get_latest_payout_publication = None


def plan_identity(
    snapshot: HistoricalInputSnapshot,
    run_context: SimulationRunContext,
    strategy_identity: StrategyIdentity,
) -> SimulationBetPlanIdentity:
    return SimulationBetPlanIdentity(
        run_id=run_context.run_id,
        race_id=snapshot.internal_race_id,
        strategy_id=strategy_identity.strategy_id,
        strategy_config_hash=strategy_identity.strategy_config_hash,
        information_cutoff=snapshot.information_cutoff,
    )


def simulation_bet(
    snapshot: HistoricalInputSnapshot,
    strategy_identity: StrategyIdentity,
    *,
    selection: tuple[int, ...] = (101,),
    rank: int = 0,
) -> SimulationBet:
    return SimulationBet(
        race_id=snapshot.internal_race_id,
        strategy_id=strategy_identity.strategy_id,
        bet_type="単勝",
        race_entry_ids=selection,
        stake=100,
        recommendation_rank=rank,
        placed_at_cutoff=snapshot.information_cutoff,
    )


def plan_snapshot(
    snapshot: HistoricalInputSnapshot,
    run_context: SimulationRunContext,
    strategy_identity: StrategyIdentity,
    *,
    bets: tuple[SimulationBet, ...] = (),
    identity: SimulationBetPlanIdentity | None = None,
) -> SimulationBetPlanSnapshot:
    return SimulationBetPlanSnapshot(
        identity=(
            plan_identity(snapshot, run_context, strategy_identity)
            if identity is None
            else identity
        ),
        policy_identity=build_allocation_policy_identity(
            strategy_identity.strategy_config.allocation_policy
        ),
        budget=BetStakeBudget(total_amount=max(1000, sum(bet.stake for bet in bets))),
        bets=bets,
    )


def persisted_result(
    snapshot: HistoricalInputSnapshot,
    *,
    observed_at: datetime,
    status: RaceResultStatus = RaceResultStatus.COMPLETE,
) -> PersistedRaceResult:
    return PersistedRaceResult(
        race_id=snapshot.internal_race_id,
        result_status=status,
        finalized_at=observed_at if status is RaceResultStatus.COMPLETE else None,
        observed_at=observed_at,
        source="official",
        entries=(
            PersistedRaceResultEntry(
                horse_no=9,
                race_entry_id=101,
                finish_position=1 if status is RaceResultStatus.COMPLETE else None,
                result_status=(
                    RaceResultEntryStatus.CONFIRMED
                    if status is RaceResultStatus.COMPLETE
                    else RaceResultEntryStatus.VOID
                ),
            ),
        ),
    )


def payout_publication(
    snapshot: HistoricalInputSnapshot,
    *,
    observed_at: datetime,
    payout_per_100: int = 250,
    complete: bool = True,
    include_exact_selection: bool = True,
    publication_id: int = 1,
) -> PayoutPublication:
    entries = (
        (
            PayoutRecord(
                race_entry_ids=(101,),
                payout_per_100=payout_per_100,
                payout_status=PayoutStatus.WINNING,
            ),
        )
        if include_exact_selection
        else ()
    )
    return PayoutPublication(
        race_id=snapshot.internal_race_id,
        bet_type="単勝",
        finalized_at=observed_at if complete else None,
        observed_at=observed_at,
        is_complete=complete,
        source="official",
        entries=entries,
        publication_id=publication_id,
    )


class HistoricalSettlementSimulationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.first = _historical_snapshot(race_id=501, start_offset=20)
        self.second = _historical_snapshot(race_id=502, start_offset=10)
        self.third = _historical_snapshot(race_id=503, start_offset=10)
        self.run_context = _run_context()
        self.strategy_identity = _strategy_identity()
        self.cutoffs = {
            snapshot.internal_race_id: snapshot.race.scheduled_start_at + timedelta(hours=2)
            for snapshot in (self.first, self.second, self.third)
        }
        self.plan_source = RecordingPlanSource()
        self.result_repository = RecordingResultRepository()
        self.payout_repository = RecordingPayoutRepository()

    def call(self, **overrides: object) -> SimulationSummary:
        values: dict[str, object] = {
            "snapshots": (self.first, self.second, self.third),
            "run_context": self.run_context,
            "strategy_identity": self.strategy_identity,
            "settlement_cutoffs_by_race_id": self.cutoffs,
            "bet_plan_snapshot_source": self.plan_source,
            "race_result_repository": self.result_repository,
            "payout_repository": self.payout_repository,
        }
        values.update(overrides)
        return execute_historical_settlement_simulation(**values)  # type: ignore[arg-type]

    def no_activity(self) -> None:
        self.assertEqual(self.plan_source.calls, [])
        self.assertEqual(self.result_repository.calls, [])
        self.assertEqual(self.payout_repository.calls, [])

    def install_plans(
        self,
        snapshots: tuple[HistoricalInputSnapshot, ...],
        *,
        empty_race_ids: set[int] | None = None,
    ) -> None:
        empty_ids = set() if empty_race_ids is None else empty_race_ids
        for snapshot in snapshots:
            bets = (
                ()
                if snapshot.internal_race_id in empty_ids
                else (simulation_bet(snapshot, self.strategy_identity),)
            )
            identity = plan_identity(snapshot, self.run_context, self.strategy_identity)
            self.plan_source.responses[identity] = plan_snapshot(
                snapshot,
                self.run_context,
                self.strategy_identity,
                bets=bets,
            )

    def test_exact_public_surface_signature_and_type_hints(self) -> None:
        self.assertEqual(
            composition_module.__all__,
            ("execute_historical_settlement_simulation",),
        )
        self.assertFalse(hasattr(simulation_package, "execute_historical_settlement_simulation"))
        signature = inspect.signature(execute_historical_settlement_simulation)
        self.assertEqual(
            tuple(signature.parameters),
            (
                "snapshots",
                "run_context",
                "strategy_identity",
                "settlement_cutoffs_by_race_id",
                "bet_plan_snapshot_source",
                "race_result_repository",
                "payout_repository",
            ),
        )
        self.assertTrue(
            all(value.kind is inspect.Parameter.KEYWORD_ONLY for value in signature.parameters.values())
        )
        hints = get_type_hints(execute_historical_settlement_simulation)
        self.assertEqual(hints["snapshots"], tuple[HistoricalInputSnapshot, ...])
        self.assertIs(hints["run_context"], SimulationRunContext)
        self.assertIs(hints["strategy_identity"], StrategyIdentity)
        self.assertEqual(hints["settlement_cutoffs_by_race_id"], Mapping[int, datetime])
        self.assertIs(hints["bet_plan_snapshot_source"], SimulationBetPlanSnapshotSource)
        self.assertIs(hints["race_result_repository"], RaceResultRepository)
        self.assertIs(hints["payout_repository"], PayoutRepository)
        self.assertIs(hints["return"], SimulationSummary)

    def test_invalid_snapshot_boundaries_fail_before_adapter_and_io(self) -> None:
        invalid = (
            [self.first],
            SnapshotTuple((self.first,)),
            (object(),),
            (self.first, object()),
        )
        for snapshots in invalid:
            with self.subTest(value_type=type(snapshots).__name__):
                with patch.object(composition_module, "build_simulation_race_input_from_historical_snapshot") as adapter:
                    with self.assertRaises(ValueError):
                        self.call(snapshots=snapshots)
                adapter.assert_not_called()
                self.no_activity()

    def test_invalid_shared_cutoff_and_strategy_boundaries_fail_before_adapter_and_io(self) -> None:
        invalid = (
            {"run_context": object()},
            {"strategy_identity": object()},
            {"settlement_cutoffs_by_race_id": []},
            {"settlement_cutoffs_by_race_id": dict},
            {"settlement_cutoffs_by_race_id": {True: self.cutoffs[501]}},
            {"settlement_cutoffs_by_race_id": {0: self.cutoffs[501]}},
            {"settlement_cutoffs_by_race_id": {-1: self.cutoffs[501]}},
            {"settlement_cutoffs_by_race_id": {"501": self.cutoffs[501]}},
            {"settlement_cutoffs_by_race_id": {501: datetime(2026, 8, 5)}},
            {"strategy_identity": _strategy_identity(name="OtherStrategy")},
        )
        for overrides in invalid:
            with self.subTest(overrides=overrides):
                with patch.object(composition_module, "build_simulation_race_input_from_historical_snapshot") as adapter:
                    with self.assertRaises(ValueError):
                        self.call(**overrides)
                adapter.assert_not_called()
                self.no_activity()

    def test_invalid_structural_collaborators_fail_before_adapter_and_io(self) -> None:
        invalid = (
            {"bet_plan_snapshot_source": RecordingPlanSource},
            {"bet_plan_snapshot_source": MissingMethod()},
            {"bet_plan_snapshot_source": NonCallablePlanSource()},
            {"race_result_repository": RecordingResultRepository},
            {"race_result_repository": MissingMethod()},
            {"race_result_repository": NonCallableResultRepository()},
            {"payout_repository": RecordingPayoutRepository},
            {"payout_repository": MissingMethod()},
            {"payout_repository": NonCallablePayoutRepository()},
        )
        for overrides in invalid:
            with self.subTest(overrides=overrides):
                with patch.object(composition_module, "build_simulation_race_input_from_historical_snapshot") as adapter:
                    with self.assertRaises(ValueError):
                        self.call(**overrides)
                adapter.assert_not_called()
                self.no_activity()

    def test_duplicate_cutoff_coverage_and_dataset_fail_before_adapter_and_io(self) -> None:
        duplicate = replace(self.second, internal_race_id=self.first.internal_race_id)
        mismatched = _historical_snapshot(
            race_id=503,
            start_offset=10,
            dataset_id="different-dataset",
        )
        cases = (
            {
                "snapshots": (self.first, duplicate),
                "settlement_cutoffs_by_race_id": {501: self.cutoffs[501]},
                "error": ValueError,
            },
            {
                "settlement_cutoffs_by_race_id": {501: self.cutoffs[501], 502: self.cutoffs[502]},
                "error": ValueError,
            },
            {
                "settlement_cutoffs_by_race_id": {**self.cutoffs, 999: self.cutoffs[501]},
                "error": ValueError,
            },
            {
                "settlement_cutoffs_by_race_id": {501: self.cutoffs[501], 502: self.cutoffs[502], 999: self.cutoffs[503]},
                "error": ValueError,
            },
            {
                "snapshots": (self.first, self.second, mismatched),
                "error": SimulationValidationError,
            },
        )
        for case in cases:
            overrides = {key: value for key, value in case.items() if key != "error"}
            with self.subTest(overrides=overrides):
                with patch.object(composition_module, "build_simulation_race_input_from_historical_snapshot") as adapter:
                    with self.assertRaises(case["error"]):  # type: ignore[arg-type]
                        self.call(**overrides)
                adapter.assert_not_called()
                self.no_activity()

    def test_first_dataset_mismatch_is_selected_in_canonical_order(self) -> None:
        caller_first = _historical_snapshot(
            race_id=501,
            start_offset=20,
            dataset_id="wrong-one",
        )
        canonical_first = _historical_snapshot(
            race_id=502,
            start_offset=10,
            dataset_id="wrong-two",
        )
        cutoffs = {501: self.cutoffs[501], 502: self.cutoffs[502]}
        with self.assertRaises(SimulationValidationError) as caught:
            self.call(
                snapshots=(caller_first, canonical_first),
                settlement_cutoffs_by_race_id=cutoffs,
            )
        self.assertEqual(caught.exception.race_id, 502)
        self.assertEqual(caught.exception.input_identifier, "run_context.dataset_id")
        self.assertEqual(
            caught.exception.reason,
            "run_context.dataset_id does not match snapshot.identity.dataset_id",
        )
        self.no_activity()

    def test_all_adapters_finish_in_canonical_order_before_any_io_and_wire_exact_objects(self) -> None:
        canonical = (self.second, self.third, self.first)
        race_inputs = {
            snapshot.internal_race_id: build_simulation_race_input_from_historical_snapshot(snapshot=snapshot)
            for snapshot in canonical
        }
        events: list[tuple[str, object]] = []
        summary = Simulator(
            strategy_identity=self.strategy_identity,
            race_executor=lambda *, race_input: (_ for _ in ()).throw(AssertionError(race_input)),
        ).run(race_inputs=())
        constructed: dict[str, object] = {}

        def adapt(*, snapshot: HistoricalInputSnapshot) -> SimulationRaceInput:
            events.append(("adapter", snapshot))
            return race_inputs[snapshot.internal_race_id]

        class BetSourceSpy:
            def __init__(inner_self, *, run_context: object, snapshot_source: object) -> None:
                constructed["bet_source_count"] = int(constructed.get("bet_source_count", 0)) + 1
                constructed["bet_source"] = inner_self
                self.assertIs(run_context, self.run_context)
                self.assertIs(snapshot_source, self.plan_source)

        class SettlementSourceSpy:
            def __init__(
                inner_self,
                *,
                bet_source: object,
                race_result_repository: object,
                payout_repository: object,
                settlement_cutoffs_by_race_id: Mapping[int, datetime],
            ) -> None:
                constructed["settlement_source_count"] = int(
                    constructed.get("settlement_source_count", 0)
                ) + 1
                constructed["settlement_source"] = inner_self
                self.assertIs(bet_source, constructed["bet_source"])
                self.assertIs(race_result_repository, self.result_repository)
                self.assertIs(payout_repository, self.payout_repository)
                self.assertEqual(dict(settlement_cutoffs_by_race_id), self.cutoffs)
                events.append(("settlement_source", None))

        class ExecutorSpy:
            def __init__(inner_self, *, strategy_identity: object, settlement_source: object) -> None:
                constructed["executor_count"] = int(constructed.get("executor_count", 0)) + 1
                constructed["executor"] = inner_self
                self.assertIs(strategy_identity, self.strategy_identity)
                self.assertIs(settlement_source, constructed["settlement_source"])

        class SimulatorSpy:
            def __init__(inner_self, *, strategy_identity: object, race_executor: object) -> None:
                constructed["simulator_count"] = int(constructed.get("simulator_count", 0)) + 1
                constructed["simulator"] = inner_self
                inner_self.calls = 0
                self.assertIs(strategy_identity, self.strategy_identity)
                self.assertIs(race_executor, constructed["executor"])

            def run(inner_self, *, race_inputs: object) -> SimulationSummary:
                inner_self.calls += 1
                constructed["race_inputs"] = race_inputs
                return summary

        with (
            patch.object(composition_module, "build_simulation_race_input_from_historical_snapshot", side_effect=adapt) as adapter,
            patch.object(composition_module, "PersistedSimulationBetSource", BetSourceSpy),
            patch.object(composition_module, "HistoricalPersistedRaceSettlementSource", SettlementSourceSpy),
            patch.object(composition_module, "PersistedRaceSimulationExecutor", ExecutorSpy),
            patch.object(composition_module, "Simulator", SimulatorSpy),
        ):
            returned = self.call(snapshots=(self.first, self.third, self.second))

        self.assertIs(returned, summary)
        self.assertEqual([event[1] for event in events[:3]], list(canonical))
        self.assertEqual(events[3], ("settlement_source", None))
        self.assertEqual(adapter.call_count, 3)
        self.assertEqual(constructed["bet_source_count"], 1)
        self.assertEqual(constructed["settlement_source_count"], 1)
        self.assertEqual(constructed["executor_count"], 1)
        self.assertEqual(constructed["simulator_count"], 1)
        self.assertEqual(constructed["race_inputs"], tuple(race_inputs[item.internal_race_id] for item in canonical))
        self.assertEqual(constructed["simulator"].calls, 1)  # type: ignore[union-attr]

    def test_late_adapter_failure_propagates_before_all_repository_io_and_simulator(self) -> None:
        error = HistoricalInputSnapshotSimulationAdapterError("late adapter failure")
        events: list[int] = []

        def adapt(*, snapshot: HistoricalInputSnapshot) -> SimulationRaceInput:
            events.append(snapshot.internal_race_id)
            if len(events) == 3:
                raise error
            return build_simulation_race_input_from_historical_snapshot(snapshot=snapshot)

        with (
            patch.object(composition_module, "build_simulation_race_input_from_historical_snapshot", side_effect=adapt),
            patch.object(composition_module, "Simulator") as simulator,
        ):
            with self.assertRaises(HistoricalInputSnapshotSimulationAdapterError) as caught:
                self.call(snapshots=(self.first, self.third, self.second))
        self.assertIs(caught.exception, error)
        self.assertEqual(events, [502, 503, 501])
        simulator.assert_not_called()
        self.no_activity()

    def test_all_adapter_events_precede_first_real_plan_load(self) -> None:
        snapshots = (self.first, self.second, self.third)
        self.install_plans(snapshots, empty_race_ids={item.internal_race_id for item in snapshots})
        events: list[tuple[str, int]] = []
        original_load = self.plan_source.load_snapshot

        def adapt(*, snapshot: HistoricalInputSnapshot) -> SimulationRaceInput:
            events.append(("adapter", snapshot.internal_race_id))
            return build_simulation_race_input_from_historical_snapshot(snapshot=snapshot)

        def load(*, identity: SimulationBetPlanIdentity) -> SimulationBetPlanSnapshot | None:
            events.append(("plan", identity.race_id))
            return original_load(identity=identity)

        with (
            patch.object(composition_module, "build_simulation_race_input_from_historical_snapshot", side_effect=adapt),
            patch.object(self.plan_source, "load_snapshot", side_effect=load),
        ):
            self.call(snapshots=tuple(reversed(snapshots)))
        self.assertEqual([kind for kind, _ in events[:3]], ["adapter", "adapter", "adapter"])
        self.assertTrue(all(kind == "plan" for kind, _ in events[3:]))

    def test_cutoff_mapping_is_frozen_once_and_exact_datetime_objects_survive_caller_mutation(self) -> None:
        snapshot = self.first
        exact_cutoff = self.cutoffs[snapshot.internal_race_id]
        caller_values = {snapshot.internal_race_id: exact_cutoff}
        caller_mapping = CountingCutoffMapping(caller_values)
        captured: dict[int, datetime] = {}

        def adapt(*, snapshot: HistoricalInputSnapshot) -> SimulationRaceInput:
            caller_values.clear()
            return build_simulation_race_input_from_historical_snapshot(snapshot=snapshot)

        class SettlementSourceSpy:
            def __init__(inner_self, **kwargs: object) -> None:
                captured.update(kwargs["settlement_cutoffs_by_race_id"])  # type: ignore[arg-type]

        class ExecutorSpy:
            def __init__(inner_self, **kwargs: object) -> None:
                pass

        summary = Simulator(
            strategy_identity=self.strategy_identity,
            race_executor=lambda *, race_input: (_ for _ in ()).throw(AssertionError(race_input)),
        ).run(race_inputs=())

        class SimulatorSpy:
            def __init__(inner_self, **kwargs: object) -> None:
                pass

            def run(inner_self, *, race_inputs: object) -> SimulationSummary:
                return summary

        with (
            patch.object(composition_module, "build_simulation_race_input_from_historical_snapshot", side_effect=adapt),
            patch.object(composition_module, "HistoricalPersistedRaceSettlementSource", SettlementSourceSpy),
            patch.object(composition_module, "PersistedRaceSimulationExecutor", ExecutorSpy),
            patch.object(composition_module, "Simulator", SimulatorSpy),
        ):
            returned = self.call(
                snapshots=(snapshot,),
                settlement_cutoffs_by_race_id=caller_mapping,
            )
        self.assertIs(returned, summary)
        self.assertEqual(caller_mapping.iterations, 1)
        self.assertIs(captured[snapshot.internal_race_id], exact_cutoff)

    def test_empty_batch_flows_through_real_simulator_without_repository_reads(self) -> None:
        summary = self.call(snapshots=(), settlement_cutoffs_by_race_id={})
        self.assertIsInstance(summary, SimulationSummary)
        self.assertEqual(summary.race_count, 0)
        self.assertEqual(summary.bet_count, 0)
        self.assertEqual(summary.investment, 0)
        self.assertIsNone(summary.roi)
        self.no_activity()

    def test_exact_plan_identity_is_loaded_and_missing_or_wrong_identity_fails_closed(self) -> None:
        snapshot = self.first
        expected = plan_identity(snapshot, self.run_context, self.strategy_identity)
        self.plan_source.responses[expected] = plan_snapshot(
            snapshot,
            self.run_context,
            self.strategy_identity,
        )
        summary = self.call(
            snapshots=(snapshot,),
            settlement_cutoffs_by_race_id={snapshot.internal_race_id: self.cutoffs[snapshot.internal_race_id]},
        )
        self.assertEqual(summary.no_bet_race_count, 1)
        self.assertEqual(self.plan_source.calls, [expected])
        actual = self.plan_source.calls[0]
        self.assertEqual(actual.run_id, self.run_context.run_id)
        self.assertEqual(actual.race_id, snapshot.internal_race_id)
        self.assertEqual(actual.strategy_id, self.strategy_identity.strategy_id)
        self.assertEqual(actual.strategy_config_hash, self.strategy_identity.strategy_config_hash)
        self.assertEqual(actual.information_cutoff, snapshot.information_cutoff)

        missing_source = RecordingPlanSource()
        with self.assertRaises(SimulationValidationError) as missing:
            self.call(
                snapshots=(snapshot,),
                settlement_cutoffs_by_race_id={snapshot.internal_race_id: self.cutoffs[snapshot.internal_race_id]},
                bet_plan_snapshot_source=missing_source,
            )
        self.assertEqual(missing.exception.reason, "snapshot was not found")

        wrong_identity = replace(expected, run_id="another-run")
        wrong_source = RecordingPlanSource(
            {
                expected: plan_snapshot(
                    snapshot,
                    self.run_context,
                    self.strategy_identity,
                    identity=wrong_identity,
                )
            }
        )
        with self.assertRaises(SimulationValidationError) as wrong:
            self.call(
                snapshots=(snapshot,),
                settlement_cutoffs_by_race_id={snapshot.internal_race_id: self.cutoffs[snapshot.internal_race_id]},
                bet_plan_snapshot_source=wrong_source,
            )
        self.assertEqual(wrong.exception.reason, "snapshot identity does not match requested identity")

    def test_exact_persisted_empty_plan_is_no_bet_without_official_reads(self) -> None:
        snapshot = self.first
        self.install_plans((snapshot,), empty_race_ids={snapshot.internal_race_id})
        summary = self.call(
            snapshots=(snapshot,),
            settlement_cutoffs_by_race_id={snapshot.internal_race_id: self.cutoffs[snapshot.internal_race_id]},
        )
        self.assertEqual(len(self.plan_source.calls), 1)
        self.assertEqual(summary.race_count, 1)
        self.assertEqual(summary.no_bet_race_count, 1)
        self.assertEqual(summary.bet_count, 0)
        self.assertEqual((summary.investment, summary.payout, summary.profit), (0, 0, 0))
        self.assertIsNone(summary.roi)
        self.assertEqual(self.result_repository.calls, [])
        self.assertEqual(self.payout_repository.calls, [])

    def test_result_cutoff_and_incomplete_payout_integrate_as_unsettled(self) -> None:
        snapshot = self.first
        cutoff = self.cutoffs[snapshot.internal_race_id]
        self.install_plans((snapshot,))
        self.result_repository.responses[snapshot.internal_race_id] = persisted_result(
            snapshot,
            observed_at=cutoff + timedelta(seconds=1),
        )
        summary = self.call(
            snapshots=(snapshot,),
            settlement_cutoffs_by_race_id={snapshot.internal_race_id: cutoff},
        )
        self.assertEqual(summary.unsettled_race_count, 1)
        self.assertEqual((summary.investment, summary.payout, summary.profit), (0, 0, 0))

        at_cutoff_result = persisted_result(snapshot, observed_at=cutoff)
        incomplete = payout_publication(
            snapshot,
            observed_at=cutoff,
            complete=False,
        )
        result_repository = RecordingResultRepository({snapshot.internal_race_id: at_cutoff_result})
        payout_repository = RecordingPayoutRepository(
            {(snapshot.internal_race_id, "単勝"): (incomplete,)}
        )
        summary = self.call(
            snapshots=(snapshot,),
            settlement_cutoffs_by_race_id={snapshot.internal_race_id: cutoff},
            race_result_repository=result_repository,
            payout_repository=payout_repository,
        )
        self.assertEqual(summary.unsettled_race_count, 1)
        self.assertEqual(summary.investment, 0)
        self.assertEqual(len(payout_repository.calls), 1)
        self.assertIs(payout_repository.calls[0]["observed_at_lte"], cutoff)
        self.assertIs(payout_repository.calls[0]["require_complete"], False)

    def test_payout_after_cutoff_collaborator_violation_propagates_exact_c4g2a_error(self) -> None:
        snapshot = self.first
        cutoff = self.cutoffs[snapshot.internal_race_id]
        self.install_plans((snapshot,))
        result_repository = RecordingResultRepository(
            {snapshot.internal_race_id: persisted_result(snapshot, observed_at=cutoff)}
        )
        after = payout_publication(snapshot, observed_at=cutoff + timedelta(seconds=1))
        payout_repository = RecordingPayoutRepository(
            {(snapshot.internal_race_id, "単勝"): (after,)},
            honor_cutoff=False,
        )
        with self.assertRaises(SimulationValidationError) as caught:
            self.call(
                snapshots=(snapshot,),
                settlement_cutoffs_by_race_id={snapshot.internal_race_id: cutoff},
                race_result_repository=result_repository,
                payout_repository=payout_repository,
            )
        self.assertEqual(caught.exception.input_identifier, "payout_repository")
        self.assertEqual(
            caught.exception.reason,
            "payout publication observed_at is after settlement cutoff",
        )

    def test_settled_win_and_complete_publication_loss_use_existing_summary_arithmetic(self) -> None:
        win = self.first
        loss = self.second
        snapshots = (win, loss)
        cutoffs = {item.internal_race_id: self.cutoffs[item.internal_race_id] for item in snapshots}
        self.install_plans(snapshots)
        results = {
            item.internal_race_id: persisted_result(item, observed_at=cutoffs[item.internal_race_id])
            for item in snapshots
        }
        payouts = {
            (win.internal_race_id, "単勝"): (
                payout_publication(win, observed_at=cutoffs[win.internal_race_id], payout_per_100=250),
            ),
            (loss.internal_race_id, "単勝"): (
                payout_publication(
                    loss,
                    observed_at=cutoffs[loss.internal_race_id],
                    include_exact_selection=False,
                ),
            ),
        }
        summary = self.call(
            snapshots=snapshots,
            settlement_cutoffs_by_race_id=cutoffs,
            race_result_repository=RecordingResultRepository(results),
            payout_repository=RecordingPayoutRepository(payouts),
        )
        self.assertEqual(summary.settled_race_count, 2)
        self.assertEqual(summary.settled_bet_count, 2)
        self.assertEqual(summary.hit_bet_count, 1)
        self.assertEqual(summary.hit_race_count, 1)
        self.assertEqual((summary.investment, summary.payout, summary.profit), (200, 250, 50))
        self.assertEqual(summary.roi, Decimal("125"))
        self.assertEqual(summary.bet_hit_rate, Decimal("50"))
        self.assertEqual(summary.race_hit_rate, Decimal("50"))

    def test_mixed_summary_reuses_existing_status_and_financial_semantics(self) -> None:
        snapshots = tuple(
            _historical_snapshot(race_id=600 + index, start_offset=index)
            for index in range(5)
        )
        cutoffs = {
            item.internal_race_id: item.race.scheduled_start_at + timedelta(hours=2)
            for item in snapshots
        }
        empty_id = snapshots[1].internal_race_id
        self.install_plans(snapshots, empty_race_ids={empty_id})
        result_responses: dict[int, object] = {
            snapshots[0].internal_race_id: persisted_result(
                snapshots[0], observed_at=cutoffs[snapshots[0].internal_race_id]
            ),
            snapshots[2].internal_race_id: None,
            snapshots[3].internal_race_id: persisted_result(
                snapshots[3],
                observed_at=cutoffs[snapshots[3].internal_race_id],
                status=RaceResultStatus.VOID,
            ),
            snapshots[4].internal_race_id: persisted_result(
                snapshots[4],
                observed_at=cutoffs[snapshots[4].internal_race_id],
                status=RaceResultStatus.UNSUPPORTED,
            ),
        }
        payout = payout_publication(
            snapshots[0],
            observed_at=cutoffs[snapshots[0].internal_race_id],
        )
        summary = self.call(
            snapshots=tuple(reversed(snapshots)),
            settlement_cutoffs_by_race_id=cutoffs,
            race_result_repository=RecordingResultRepository(result_responses),
            payout_repository=RecordingPayoutRepository(
                {(snapshots[0].internal_race_id, "単勝"): (payout,)}
            ),
        )
        self.assertEqual(summary.race_count, 5)
        self.assertEqual(summary.settled_race_count, 1)
        self.assertEqual(summary.unsettled_race_count, 1)
        self.assertEqual(summary.no_bet_race_count, 1)
        self.assertEqual(summary.void_race_count, 1)
        self.assertEqual(summary.unsupported_race_count, 1)
        self.assertEqual(summary.bet_count, 4)
        self.assertEqual(summary.settled_bet_count, 1)
        self.assertEqual(summary.hit_bet_count, 1)
        self.assertEqual((summary.investment, summary.payout, summary.profit), (100, 250, 150))
        self.assertEqual(summary.roi, Decimal("250"))
        self.assertEqual(summary.by_bet_type["単勝"].bet_count, 4)

    def test_summary_is_as_of_cutoffs_and_unsettled_stake_is_not_roi_loss(self) -> None:
        settled = self.first
        unsettled = self.second
        snapshots = (settled, unsettled)
        cutoffs = {item.internal_race_id: self.cutoffs[item.internal_race_id] for item in snapshots}
        self.install_plans(snapshots)
        results = {
            settled.internal_race_id: persisted_result(
                settled, observed_at=cutoffs[settled.internal_race_id]
            ),
            unsettled.internal_race_id: persisted_result(
                unsettled,
                observed_at=cutoffs[unsettled.internal_race_id] + timedelta(seconds=1),
            ),
        }
        payout = payout_publication(
            settled,
            observed_at=cutoffs[settled.internal_race_id],
            payout_per_100=200,
        )
        summary = self.call(
            snapshots=snapshots,
            settlement_cutoffs_by_race_id=cutoffs,
            race_result_repository=RecordingResultRepository(results),
            payout_repository=RecordingPayoutRepository(
                {(settled.internal_race_id, "単勝"): (payout,)}
            ),
        )
        self.assertEqual(summary.settled_race_count, 1)
        self.assertEqual(summary.unsettled_race_count, 1)
        self.assertEqual(summary.bet_count, 2)
        self.assertEqual(summary.settled_bet_count, 1)
        self.assertEqual((summary.investment, summary.payout, summary.profit), (100, 200, 100))
        self.assertEqual(summary.roi, Decimal("200"))

    def test_mid_batch_failure_propagates_without_retry_or_later_race(self) -> None:
        fourth = _historical_snapshot(race_id=504, start_offset=30)
        snapshots = (self.first, self.second, self.third, fourth)
        cutoffs = {
            item.internal_race_id: item.race.scheduled_start_at + timedelta(hours=2)
            for item in snapshots
        }
        canonical = tuple(sorted(snapshots, key=lambda item: (item.race.scheduled_start_at, item.internal_race_id)))
        error = RepositoryDataIntegrityError("race three plan corruption")
        for index, snapshot in enumerate(canonical):
            identity = plan_identity(snapshot, self.run_context, self.strategy_identity)
            self.plan_source.responses[identity] = (
                error
                if index == 2
                else plan_snapshot(snapshot, self.run_context, self.strategy_identity)
            )
        with self.assertRaises(RepositoryDataIntegrityError) as caught:
            self.call(snapshots=snapshots, settlement_cutoffs_by_race_id=cutoffs)
        self.assertIs(caught.exception, error)
        self.assertEqual([identity.race_id for identity in self.plan_source.calls], [
            canonical[0].internal_race_id,
            canonical[1].internal_race_id,
            canonical[2].internal_race_id,
        ])
        self.assertNotIn(canonical[3].internal_race_id, [identity.race_id for identity in self.plan_source.calls])

    def test_snapshot_and_cutoff_mapping_order_do_not_change_summary(self) -> None:
        snapshots = (self.first, self.second)
        cutoffs = {item.internal_race_id: self.cutoffs[item.internal_race_id] for item in snapshots}
        self.install_plans(snapshots, empty_race_ids={item.internal_race_id for item in snapshots})
        first = self.call(snapshots=snapshots, settlement_cutoffs_by_race_id=cutoffs)
        second = self.call(
            snapshots=tuple(reversed(snapshots)),
            settlement_cutoffs_by_race_id=dict(reversed(tuple(cutoffs.items()))),
        )
        self.assertEqual(first, second)

    def test_process_date_defaults_do_not_change_settlement_summary(self) -> None:
        class EarlyDate(date):
            @classmethod
            def today(cls) -> "EarlyDate":
                return cls(2000, 1, 1)

        class LateDate(date):
            @classmethod
            def today(cls) -> "LateDate":
                return cls(2099, 12, 31)

        snapshot = self.first
        identity = plan_identity(snapshot, self.run_context, self.strategy_identity)
        persisted = plan_snapshot(snapshot, self.run_context, self.strategy_identity)

        def execute_with(fake_date: type[date]) -> SimulationSummary:
            with (
                patch("scripts.prediction.ability_engine.date", fake_date),
                patch("scripts.prediction.jockey_engine.date", fake_date),
                patch("scripts.prediction.track_engine.date", fake_date),
            ):
                return self.call(
                    snapshots=(snapshot,),
                    settlement_cutoffs_by_race_id={snapshot.internal_race_id: self.cutoffs[snapshot.internal_race_id]},
                    bet_plan_snapshot_source=RecordingPlanSource({identity: persisted}),
                )

        self.assertEqual(execute_with(EarlyDate), execute_with(LateDate))

    def test_post_cutoff_publication_does_not_change_older_cutoff_summary(self) -> None:
        snapshot = self.first
        cutoff = self.cutoffs[snapshot.internal_race_id]
        self.install_plans((snapshot,))
        result_repository = RecordingResultRepository(
            {snapshot.internal_race_id: persisted_result(snapshot, observed_at=cutoff)}
        )
        without_later = self.call(
            snapshots=(snapshot,),
            settlement_cutoffs_by_race_id={snapshot.internal_race_id: cutoff},
            race_result_repository=result_repository,
            payout_repository=RecordingPayoutRepository(),
        )
        later = payout_publication(
            snapshot,
            observed_at=cutoff + timedelta(minutes=1),
        )
        with_later = self.call(
            snapshots=(snapshot,),
            settlement_cutoffs_by_race_id={snapshot.internal_race_id: cutoff},
            race_result_repository=RecordingResultRepository(
                {snapshot.internal_race_id: persisted_result(snapshot, observed_at=cutoff)}
            ),
            payout_repository=RecordingPayoutRepository(
                {(snapshot.internal_race_id, "単勝"): (later,)}
            ),
        )
        self.assertEqual(without_later, with_later)
        self.assertEqual(with_later.unsettled_race_count, 1)

    def test_maximum_drawdown_uses_existing_settled_time_then_race_order(self) -> None:
        snapshots = (self.first, self.second, self.third)
        cutoffs = {item.internal_race_id: self.cutoffs[item.internal_race_id] for item in snapshots}
        self.install_plans(snapshots)
        results = {
            item.internal_race_id: persisted_result(item, observed_at=cutoffs[item.internal_race_id])
            for item in snapshots
        }
        payouts = {
            (self.second.internal_race_id, "単勝"): (
                payout_publication(
                    self.second,
                    observed_at=cutoffs[self.second.internal_race_id],
                    payout_per_100=200,
                ),
            ),
            (self.third.internal_race_id, "単勝"): (
                payout_publication(
                    self.third,
                    observed_at=cutoffs[self.third.internal_race_id],
                    include_exact_selection=False,
                ),
            ),
            (self.first.internal_race_id, "単勝"): (
                payout_publication(
                    self.first,
                    observed_at=cutoffs[self.first.internal_race_id],
                    include_exact_selection=False,
                ),
            ),
        }
        summary = self.call(
            snapshots=tuple(reversed(snapshots)),
            settlement_cutoffs_by_race_id=cutoffs,
            race_result_repository=RecordingResultRepository(results),
            payout_repository=RecordingPayoutRepository(payouts),
        )
        self.assertEqual(summary.settled_race_count, 3)
        self.assertEqual(summary.maximum_drawdown, 200)

    def test_static_ownership_has_no_prediction_planning_database_clock_or_broad_catch(self) -> None:
        source = inspect.getsource(composition_module)
        tree = ast.parse(source)
        forbidden = (
            "build_historical_prediction_pipeline",
            "PredictionPipeline",
            "execute_and_persist_historical_bet_plan",
            "execute_and_persist_historical_bet_plans",
            "FixedStakeBetAllocator",
            "SimulationBetPlanBuilder",
            "ExactRaceEntrySelectionResolver",
            "PersistedSimulationRunService",
            "sqlite3",
            "SQLite",
            "requests",
            "httpx",
            "urllib",
            "open(",
            "datetime.now",
            "date.today",
            "time.time",
            "random",
            "os.environ",
            "save_snapshot",
            "commit(",
            "rollback(",
        )
        for value in forbidden:
            self.assertNotIn(value, source)
        self.assertFalse(any(isinstance(node, ast.Try) for node in ast.walk(tree)))
        self.assertEqual(source.count("dict(settlement_cutoffs_by_race_id)"), 1)
        self.assertNotIn("RuleBasedBetStrategy(", source)


if __name__ == "__main__":
    unittest.main()
