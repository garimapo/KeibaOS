"""Contract tests for the persisted one-race simulation executor."""

from __future__ import annotations

import ast
from datetime import date, datetime, timedelta, timezone
import inspect
from pathlib import Path
from unittest.mock import patch
import unittest

from scripts.prediction.bet_strategy import StrategyConfig
from scripts.prediction.prediction_pipeline import RacePredictionInput
from scripts.prediction.track_engine import RaceTrackConditions
import scripts.simulation as simulation_package
from scripts.simulation.models import (
    InputAuditEntry,
    InputSnapshotAudit,
    SettlementStatus,
    SimulationBet,
    SimulationRaceInput,
    SimulationResult,
    StrategyIdentity,
    build_strategy_identity,
)
import scripts.simulation.persisted_executor as executor_module
from scripts.simulation.persisted_executor import PersistedRaceSimulationExecutor
from scripts.simulation.persisted_settlement import PersistedRaceSettlementData
from scripts.simulation.repositories.interfaces import (
    PayoutPublication,
    PayoutRecord,
    PayoutStatus,
    PersistedRaceResult,
    PersistedRaceResultEntry,
    RaceResultEntryStatus,
    RaceResultStatus,
)
from scripts.simulation.validation import SimulationValidationError


UTC = timezone.utc
CUTOFF = datetime(2026, 7, 24, 9, 0, tzinfo=UTC)
RESULT_FINALIZED_AT = CUTOFF - timedelta(minutes=2)
PAYOUT_FINALIZED_AT = CUTOFF - timedelta(minutes=1)
BET_CUTOFF = CUTOFF - timedelta(minutes=10)
_UNSET = object()


def strategy_identity() -> StrategyIdentity:
    return build_strategy_identity("PersistedExecutor", StrategyConfig())


def race_input(race_id: int = 101) -> SimulationRaceInput:
    pipeline_input = RacePredictionInput(
        {11: [], 12: []},
        {11: "Jockey A", 12: "Jockey B"},
        RaceTrackConditions("Tokyo", 1600, "turf", "firm"),
        {11: 2.0, 12: 4.0},
        2,
        race_id,
    )
    audit = InputSnapshotAudit(
        "dataset",
        "source",
        CUTOFF,
        (
            InputAuditEntry("entry", "entry/11", "source", "entry/11", 11, observed_at=CUTOFF),
            InputAuditEntry("entry", "entry/12", "source", "entry/12", 12, observed_at=CUTOFF),
            InputAuditEntry("odds", "odds/11", "source", "odds/11", 11, observed_at=CUTOFF),
            InputAuditEntry("odds", "odds/12", "source", "odds/12", 12, observed_at=CUTOFF),
            InputAuditEntry("jockey", "jockey/11", "source", "jockey/11", 11, observed_at=CUTOFF),
            InputAuditEntry("jockey", "jockey/12", "source", "jockey/12", 12, observed_at=CUTOFF),
            InputAuditEntry("track", "track", "source", "track", None, observed_at=CUTOFF),
            InputAuditEntry("past_race", "past_race/11/none", "source", "past_race/11/none", 11, observed_at=CUTOFF),
            InputAuditEntry("past_race", "past_race/12/none", "source", "past_race/12/none", 12, observed_at=CUTOFF),
        ),
        True,
    )
    return SimulationRaceInput(race_id, date(2026, 7, 24), CUTOFF, CUTOFF, pipeline_input, audit)


def bet(identity: StrategyIdentity, *, race_id: int = 101, bet_type: str = "単勝") -> SimulationBet:
    selection = (11, 12) if bet_type in {"馬連", "ワイド"} else (11,)
    return SimulationBet(race_id, identity.strategy_id, bet_type, selection, 100, 0, BET_CUTOFF)


def persisted_result(
    *,
    race_id: int = 101,
    result_status: RaceResultStatus = RaceResultStatus.COMPLETE,
    finalized_at: datetime | None = RESULT_FINALIZED_AT,
    observed_at: datetime = CUTOFF,
) -> PersistedRaceResult:
    return PersistedRaceResult(
        race_id,
        result_status,
        finalized_at,
        observed_at,
        "source",
        (PersistedRaceResultEntry(1, 11, 1, RaceResultEntryStatus.CONFIRMED),),
    )


def publication(
    *,
    race_id: int = 101,
    bet_type: str = "単勝",
    finalized_at: datetime | None = PAYOUT_FINALIZED_AT,
    observed_at: datetime = CUTOFF,
    payout_status: PayoutStatus = PayoutStatus.WINNING,
) -> PayoutPublication:
    selection = (11, 12) if bet_type in {"馬連", "ワイド"} else (11,)
    payout_per_100 = 200 if payout_status is PayoutStatus.WINNING else 0
    return PayoutPublication(
        race_id,
        bet_type,
        finalized_at,
        observed_at,
        True,
        "source",
        (PayoutRecord(selection, payout_per_100, payout_status),),
    )


def settlement_data(
    identity: StrategyIdentity,
    *,
    race_id: int = 101,
    bets: object = _UNSET,
    race_result: object = _UNSET,
    publications: object = _UNSET,
) -> PersistedRaceSettlementData:
    selected_bets = (bet(identity, race_id=race_id),) if bets is _UNSET else bets
    selected_result = persisted_result(race_id=race_id) if race_result is _UNSET else race_result
    selected_publications = {"単勝": publication(race_id=race_id)} if publications is _UNSET else publications
    return PersistedRaceSettlementData(
        race_id,
        selected_bets,  # type: ignore[arg-type]
        selected_result,  # type: ignore[arg-type]
        selected_publications,  # type: ignore[arg-type]
    )


def no_bet_result(race_id: int, strategy_id: str) -> SimulationResult:
    return SimulationResult(race_id, strategy_id, (), SettlementStatus.NO_BET, None, 0)


class TrackingSource:
    def __init__(self, value: object) -> None:
        self.value = value
        self.calls: list[tuple[object, object]] = []

    def load_settlement_data(
        self,
        *,
        race_input: SimulationRaceInput,
        strategy_identity: StrategyIdentity,
    ) -> object:
        self.calls.append((race_input, strategy_identity))
        if isinstance(self.value, Exception):
            raise self.value
        return self.value


class PersistedRaceSimulationExecutorTests(unittest.TestCase):
    def make(
        self,
        *,
        identity: StrategyIdentity | None = None,
        source_value: object = _UNSET,
    ) -> tuple[PersistedRaceSimulationExecutor, StrategyIdentity, TrackingSource]:
        actual_identity = identity or strategy_identity()
        value = settlement_data(actual_identity) if source_value is _UNSET else source_value
        source = TrackingSource(value)
        return (
            PersistedRaceSimulationExecutor(
                strategy_identity=actual_identity,
                settlement_source=source,
            ),
            actual_identity,
            source,
        )

    def test_constructor_has_keyword_only_dependencies(self) -> None:
        signature = inspect.signature(PersistedRaceSimulationExecutor)
        self.assertEqual(tuple(signature.parameters), ("strategy_identity", "settlement_source"))
        self.assertTrue(all(value.kind is inspect.Parameter.KEYWORD_ONLY for value in signature.parameters.values()))

    def test_call_has_keyword_only_race_input(self) -> None:
        signature = inspect.signature(PersistedRaceSimulationExecutor.__call__)
        self.assertEqual(tuple(signature.parameters), ("self", "race_input"))
        self.assertIs(signature.parameters["race_input"].kind, inspect.Parameter.KEYWORD_ONLY)

    def test_constructor_preserves_dependency_identity(self) -> None:
        executor, identity, source = self.make()
        self.assertIs(executor.strategy_identity, identity)
        self.assertIs(executor.settlement_source, source)

    def test_constructor_uses_slots(self) -> None:
        executor, *_ = self.make()
        self.assertEqual(PersistedRaceSimulationExecutor.__slots__, ("_strategy_identity", "_settlement_source"))
        self.assertFalse(hasattr(executor, "__dict__"))

    def test_properties_are_read_only(self) -> None:
        executor, identity, source = self.make()
        with self.assertRaises(AttributeError):
            executor.strategy_identity = identity  # type: ignore[misc]
        with self.assertRaises(AttributeError):
            executor.settlement_source = source  # type: ignore[misc]

    def test_constructor_rejects_invalid_strategy_identity(self) -> None:
        with self.assertRaises(SimulationValidationError):
            PersistedRaceSimulationExecutor(strategy_identity=object(), settlement_source=TrackingSource(object()))  # type: ignore[arg-type]

    def test_constructor_rejects_source_without_callable_load_method(self) -> None:
        with self.assertRaises(SimulationValidationError):
            PersistedRaceSimulationExecutor(strategy_identity=strategy_identity(), settlement_source=object())  # type: ignore[arg-type]

    def test_constructor_rejects_non_callable_load_method(self) -> None:
        class InvalidSource:
            load_settlement_data = object()

        with self.assertRaises(SimulationValidationError):
            PersistedRaceSimulationExecutor(strategy_identity=strategy_identity(), settlement_source=InvalidSource())  # type: ignore[arg-type]

    def test_constructor_does_not_call_source_or_builder(self) -> None:
        identity = strategy_identity()
        source = TrackingSource(settlement_data(identity))
        with patch.object(executor_module, "_build_simulation_result_for_race", side_effect=AssertionError("builder must not run")):
            PersistedRaceSimulationExecutor(strategy_identity=identity, settlement_source=source)
        self.assertEqual(source.calls, [])

    def test_rejects_invalid_race_input_without_calling_source(self) -> None:
        executor, _, source = self.make()
        with self.assertRaises(SimulationValidationError):
            executor(race_input=object())  # type: ignore[arg-type]
        self.assertEqual(source.calls, [])

    def test_calls_source_once_with_original_keyword_only_objects(self) -> None:
        executor, identity, source = self.make()
        expected = no_bet_result(101, identity.strategy_id)
        current_input = race_input()
        with patch.object(executor_module, "_build_simulation_result_for_race", return_value=expected):
            actual = executor(race_input=current_input)
        self.assertIs(actual, expected)
        self.assertEqual(len(source.calls), 1)
        self.assertIs(source.calls[0][0], current_input)
        self.assertIs(source.calls[0][1], identity)

    def test_source_exception_is_propagated_by_identity(self) -> None:
        failure = SimulationValidationError(101, "source", "failure")
        executor, _, source = self.make(source_value=failure)
        with patch.object(executor_module, "_build_simulation_result_for_race", side_effect=AssertionError("builder must not run")):
            with self.assertRaises(SimulationValidationError) as caught:
                executor(race_input=race_input())
        self.assertIs(caught.exception, failure)
        self.assertEqual(len(source.calls), 1)

    def test_rejects_wrong_source_return_type_before_builder(self) -> None:
        executor, _, source = self.make(source_value=object())
        with patch.object(executor_module, "_build_simulation_result_for_race", side_effect=AssertionError("builder must not run")):
            with self.assertRaises(SimulationValidationError):
                executor(race_input=race_input())
        self.assertEqual(len(source.calls), 1)

    def test_rejects_bundle_race_mismatch_before_builder(self) -> None:
        identity = strategy_identity()
        executor, _, _ = self.make(identity=identity, source_value=settlement_data(identity, race_id=102))
        with patch.object(executor_module, "_build_simulation_result_for_race", side_effect=AssertionError("builder must not run")):
            with self.assertRaises(SimulationValidationError):
                executor(race_input=race_input())

    def test_rejects_strategy_mismatch_before_builder(self) -> None:
        identity = strategy_identity()
        other = build_strategy_identity("other", StrategyConfig())
        mismatched = settlement_data(identity, bets=(bet(other),))
        executor, _, _ = self.make(identity=identity, source_value=mismatched)
        with patch.object(executor_module, "_build_simulation_result_for_race", side_effect=AssertionError("builder must not run")):
            with self.assertRaises(SimulationValidationError):
                executor(race_input=race_input())

    def test_no_bet_calls_source_and_builder_once(self) -> None:
        identity = strategy_identity()
        bundle = settlement_data(identity, bets=())
        executor, _, source = self.make(identity=identity, source_value=bundle)
        expected = no_bet_result(101, identity.strategy_id)
        with patch.object(executor_module, "_build_simulation_result_for_race", return_value=expected) as builder:
            actual = executor(race_input=race_input())
        self.assertIs(actual, expected)
        self.assertEqual(len(source.calls), 1)
        builder.assert_called_once()
        self.assertEqual(builder.call_args.kwargs["bets"], ())
        self.assertEqual(builder.call_args.kwargs["publications_by_bet_type"], {})
        self.assertIsNone(builder.call_args.kwargs["settled_at"])

    def test_no_bet_ignores_persisted_result_and_payout_values(self) -> None:
        identity = strategy_identity()
        after_cutoff = CUTOFF + timedelta(minutes=1)
        bundle = settlement_data(
            identity,
            bets=(),
            race_result=persisted_result(finalized_at=after_cutoff, observed_at=after_cutoff),
            publications={"単勝": publication(finalized_at=after_cutoff, observed_at=after_cutoff)},
        )
        executor, _, _ = self.make(identity=identity, source_value=bundle)
        actual = executor(race_input=race_input())
        self.assertEqual(actual.settlement_status, SettlementStatus.NO_BET)

    def test_missing_race_result_calls_builder_with_unsettled_facts(self) -> None:
        identity = strategy_identity()
        executor, _, _ = self.make(identity=identity, source_value=settlement_data(identity, race_result=None))
        expected = no_bet_result(101, identity.strategy_id)
        with patch.object(executor_module, "_build_simulation_result_for_race", return_value=expected) as builder:
            actual = executor(race_input=race_input())
        self.assertIs(actual, expected)
        builder.assert_called_once()
        self.assertTrue(builder.call_args.kwargs["missing_race_result"])
        self.assertIsNone(builder.call_args.kwargs["settled_at"])

    def test_missing_race_result_ignores_payout_values(self) -> None:
        identity = strategy_identity()
        after_cutoff = CUTOFF + timedelta(minutes=1)
        bundle = settlement_data(
            identity,
            race_result=None,
            publications={"単勝": publication(finalized_at=after_cutoff, observed_at=after_cutoff)},
        )
        executor, _, _ = self.make(identity=identity, source_value=bundle)
        actual = executor(race_input=race_input())
        self.assertEqual(actual.settlement_status, SettlementStatus.UNSETTLED)
        self.assertEqual(actual.exclusion_reason, "missing_race_result")

    def test_non_complete_race_result_is_forwarded_without_payout_access(self) -> None:
        identity = strategy_identity()
        partial = persisted_result(result_status=RaceResultStatus.PARTIAL, finalized_at=None)
        bundle = settlement_data(identity, race_result=partial)
        executor, _, _ = self.make(identity=identity, source_value=bundle)
        expected = no_bet_result(101, identity.strategy_id)
        with patch.object(executor_module, "_build_simulation_result_for_race", return_value=expected) as builder:
            actual = executor(race_input=race_input())
        self.assertIs(actual, expected)
        self.assertIs(builder.call_args.kwargs["race_result_status"], RaceResultStatus.PARTIAL)
        self.assertEqual(builder.call_args.kwargs["publications_by_bet_type"], {})

    def test_partial_race_result_produces_unsettled_result(self) -> None:
        identity = strategy_identity()
        partial = persisted_result(result_status=RaceResultStatus.PARTIAL, finalized_at=None)
        executor, _, _ = self.make(identity=identity, source_value=settlement_data(identity, race_result=partial))
        actual = executor(race_input=race_input())
        self.assertEqual(actual.settlement_status, SettlementStatus.UNSETTLED)
        self.assertEqual(actual.exclusion_reason, "incomplete_race_result")

    def test_void_race_result_produces_void_result(self) -> None:
        identity = strategy_identity()
        void = persisted_result(result_status=RaceResultStatus.VOID, finalized_at=None)
        executor, _, _ = self.make(identity=identity, source_value=settlement_data(identity, race_result=void))
        actual = executor(race_input=race_input())
        self.assertEqual(actual.settlement_status, SettlementStatus.VOID)
        self.assertEqual(actual.exclusion_reason, "official_race_void")

    def test_unsupported_race_result_produces_unsupported_result(self) -> None:
        identity = strategy_identity()
        unsupported = persisted_result(result_status=RaceResultStatus.UNSUPPORTED, finalized_at=None)
        executor, _, _ = self.make(identity=identity, source_value=settlement_data(identity, race_result=unsupported))
        actual = executor(race_input=race_input())
        self.assertEqual(actual.settlement_status, SettlementStatus.UNSUPPORTED)
        self.assertEqual(actual.exclusion_reason, "unsupported_race_result")

    def test_accepts_race_result_observed_after_prediction_cutoff(self) -> None:
        identity = strategy_identity()
        after_cutoff = CUTOFF + timedelta(minutes=1)
        delayed = persisted_result(finalized_at=CUTOFF, observed_at=after_cutoff)
        executor, _, _ = self.make(identity=identity, source_value=settlement_data(identity, race_result=delayed))
        actual = executor(race_input=race_input())
        self.assertEqual(actual.settlement_status, SettlementStatus.SETTLED)
        self.assertEqual(actual.settled_at, CUTOFF)

    def test_accepts_race_result_finalized_after_prediction_cutoff(self) -> None:
        identity = strategy_identity()
        after_cutoff = CUTOFF + timedelta(minutes=1)
        delayed = persisted_result(finalized_at=after_cutoff, observed_at=after_cutoff)
        executor, _, _ = self.make(identity=identity, source_value=settlement_data(identity, race_result=delayed))
        actual = executor(race_input=race_input())
        self.assertEqual(actual.settlement_status, SettlementStatus.SETTLED)
        self.assertEqual(actual.settled_at, after_cutoff)

    def test_missing_required_payouts_are_forwarded_to_builder(self) -> None:
        identity = strategy_identity()
        executor, _, _ = self.make(identity=identity, source_value=settlement_data(identity, publications={}))
        expected = no_bet_result(101, identity.strategy_id)
        with patch.object(executor_module, "_build_simulation_result_for_race", return_value=expected) as builder:
            actual = executor(race_input=race_input())
        self.assertIs(actual, expected)
        self.assertEqual(builder.call_args.kwargs["missing_payout_bet_types"], ("単勝",))
        self.assertEqual(builder.call_args.kwargs["publications_by_bet_type"], {})
        self.assertIsNone(builder.call_args.kwargs["settled_at"])

    def test_missing_required_payout_produces_unsettled_result(self) -> None:
        identity = strategy_identity()
        executor, _, _ = self.make(identity=identity, source_value=settlement_data(identity, publications={}))
        actual = executor(race_input=race_input())
        self.assertEqual(actual.settlement_status, SettlementStatus.UNSETTLED)
        self.assertEqual(actual.exclusion_reason, "missing_payout_publication")

    def test_uses_only_required_payout_publications(self) -> None:
        identity = strategy_identity()
        extra_after_cutoff = CUTOFF + timedelta(minutes=1)
        bundle = settlement_data(
            identity,
            publications={
                "単勝": publication(),
                "馬連": publication(bet_type="馬連", finalized_at=extra_after_cutoff, observed_at=extra_after_cutoff),
            },
        )
        executor, _, _ = self.make(identity=identity, source_value=bundle)
        expected = no_bet_result(101, identity.strategy_id)
        with patch.object(executor_module, "_build_simulation_result_for_race", return_value=expected) as builder:
            actual = executor(race_input=race_input())
        self.assertIs(actual, expected)
        self.assertEqual(tuple(builder.call_args.kwargs["publications_by_bet_type"]), ("単勝",))

    def test_required_payout_order_follows_bet_input_order(self) -> None:
        identity = strategy_identity()
        quinella = bet(identity, bet_type="馬連")
        win = bet(identity, bet_type="単勝")
        first_publication = publication(bet_type="馬連")
        second_publication = publication(bet_type="単勝")
        bundle = settlement_data(
            identity,
            bets=(quinella, win),
            publications={"単勝": second_publication, "馬連": first_publication},
        )
        executor, _, _ = self.make(identity=identity, source_value=bundle)
        expected = no_bet_result(101, identity.strategy_id)
        with patch.object(executor_module, "_build_simulation_result_for_race", return_value=expected) as builder:
            executor(race_input=race_input())
        publications = builder.call_args.kwargs["publications_by_bet_type"]
        self.assertEqual(tuple(publications), ("馬連", "単勝"))
        self.assertIs(publications["馬連"], first_publication)
        self.assertIs(publications["単勝"], second_publication)

    def test_required_payout_publication_is_passed_by_identity(self) -> None:
        identity = strategy_identity()
        original = publication()
        executor, _, _ = self.make(
            identity=identity,
            source_value=settlement_data(identity, publications={"単勝": original}),
        )
        expected = no_bet_result(101, identity.strategy_id)
        with patch.object(executor_module, "_build_simulation_result_for_race", return_value=expected) as builder:
            executor(race_input=race_input())
        self.assertIs(builder.call_args.kwargs["publications_by_bet_type"]["単勝"], original)

    def test_accepts_required_payout_observed_after_prediction_cutoff(self) -> None:
        identity = strategy_identity()
        after_cutoff = CUTOFF + timedelta(minutes=1)
        delayed = publication(finalized_at=CUTOFF, observed_at=after_cutoff)
        executor, _, _ = self.make(identity=identity, source_value=settlement_data(identity, publications={"単勝": delayed}))
        actual = executor(race_input=race_input())
        self.assertEqual(actual.settlement_status, SettlementStatus.SETTLED)
        self.assertEqual(actual.settled_at, CUTOFF)

    def test_accepts_required_payout_finalized_after_prediction_cutoff(self) -> None:
        identity = strategy_identity()
        after_cutoff = CUTOFF + timedelta(minutes=1)
        delayed = publication(finalized_at=after_cutoff, observed_at=after_cutoff)
        executor, _, _ = self.make(identity=identity, source_value=settlement_data(identity, publications={"単勝": delayed}))
        actual = executor(race_input=race_input())
        self.assertEqual(actual.settlement_status, SettlementStatus.SETTLED)
        self.assertEqual(actual.settled_at, after_cutoff)

    def test_accepts_all_settlement_times_after_prediction_cutoff(self) -> None:
        identity = strategy_identity()
        result_finalized_at = CUTOFF + timedelta(minutes=1)
        result_observed_at = CUTOFF + timedelta(minutes=2)
        payout_finalized_at = CUTOFF + timedelta(minutes=3)
        payout_observed_at = CUTOFF + timedelta(minutes=4)
        bundle = settlement_data(
            identity,
            race_result=persisted_result(
                finalized_at=result_finalized_at,
                observed_at=result_observed_at,
            ),
            publications={
                "単勝": publication(
                    finalized_at=payout_finalized_at,
                    observed_at=payout_observed_at,
                )
            },
        )
        executor, _, _ = self.make(identity=identity, source_value=bundle)
        actual = executor(race_input=race_input())
        self.assertEqual(actual.settlement_status, SettlementStatus.SETTLED)
        self.assertEqual(actual.settled_at, payout_finalized_at)

    def test_settled_at_is_maximum_of_required_finalized_times(self) -> None:
        identity = strategy_identity()
        later = CUTOFF - timedelta(seconds=1)
        later_publication = publication(finalized_at=later, observed_at=CUTOFF)
        executor, _, _ = self.make(identity=identity, source_value=settlement_data(identity, publications={"単勝": later_publication}))
        expected = no_bet_result(101, identity.strategy_id)
        with patch.object(executor_module, "_build_simulation_result_for_race", return_value=expected) as builder:
            executor(race_input=race_input())
        self.assertEqual(builder.call_args.kwargs["settled_at"], later)

    def test_real_builder_produces_settled_result(self) -> None:
        executor, identity, _ = self.make()
        actual = executor(race_input=race_input())
        self.assertEqual(actual.settlement_status, SettlementStatus.SETTLED)
        self.assertEqual(actual.strategy_id, identity.strategy_id)
        self.assertEqual(actual.settled_at, PAYOUT_FINALIZED_AT)

    def test_payout_statuses_are_forwarded_to_builder(self) -> None:
        identity = strategy_identity()
        payout = publication(payout_status=PayoutStatus.UNSUPPORTED)
        executor, _, _ = self.make(identity=identity, source_value=settlement_data(identity, publications={"単勝": payout}))
        expected = no_bet_result(101, identity.strategy_id)
        with patch.object(executor_module, "_build_simulation_result_for_race", return_value=expected) as builder:
            executor(race_input=race_input())
        self.assertEqual(builder.call_args.kwargs["payout_statuses"], (PayoutStatus.UNSUPPORTED,))

    def test_unsupported_payout_status_produces_unsupported_result(self) -> None:
        identity = strategy_identity()
        payout = publication(payout_status=PayoutStatus.UNSUPPORTED)
        executor, _, _ = self.make(identity=identity, source_value=settlement_data(identity, publications={"単勝": payout}))
        actual = executor(race_input=race_input())
        self.assertEqual(actual.settlement_status, SettlementStatus.UNSUPPORTED)
        self.assertEqual(actual.exclusion_reason, "unsupported_payout_status")

    def test_result_builder_receives_exact_transformed_arguments(self) -> None:
        executor, identity, source = self.make()
        expected = no_bet_result(101, identity.strategy_id)
        with patch.object(executor_module, "_build_simulation_result_for_race", return_value=expected) as builder:
            actual = executor(race_input=race_input())
        self.assertIs(actual, expected)
        self.assertEqual(builder.call_args.kwargs["race_id"], 101)
        self.assertEqual(builder.call_args.kwargs["strategy_id"], identity.strategy_id)
        self.assertIs(builder.call_args.kwargs["bets"], source.value.bets)
        self.assertEqual(builder.call_args.kwargs["completeness_statuses"], ())
        self.assertIs(builder.call_args.kwargs["race_result_status"], RaceResultStatus.COMPLETE)
        self.assertEqual(builder.call_args.kwargs["missing_payout_bet_types"], ())
        self.assertFalse(builder.call_args.kwargs["missing_race_result"])
        self.assertIsNone(builder.call_args.kwargs["error_reason"])

    def test_result_builder_exception_is_propagated_by_identity(self) -> None:
        executor, _, _ = self.make()
        failure = SimulationValidationError(101, "builder", "failure")
        with patch.object(executor_module, "_build_simulation_result_for_race", side_effect=failure):
            with self.assertRaises(SimulationValidationError) as caught:
                executor(race_input=race_input())
        self.assertIs(caught.exception, failure)

    def test_builder_is_called_once_per_executor_call(self) -> None:
        executor, identity, _ = self.make()
        expected = no_bet_result(101, identity.strategy_id)
        with patch.object(executor_module, "_build_simulation_result_for_race", return_value=expected) as builder:
            executor(race_input=race_input())
        builder.assert_called_once()

    def test_executor_uses_only_integrated_result_builder(self) -> None:
        tree = ast.parse(Path(executor_module.__file__).read_text(encoding="utf-8"))
        calls = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertIn("_build_simulation_result_for_race", calls)
        self.assertFalse(calls & {
            "_build_settled_simulation_result",
            "_build_non_settled_simulation_result",
            "_build_no_bet_simulation_result",
            "_evaluate_simulation_race_bets",
            "_evaluate_simulation_bet",
            "_build_simulation_summary",
        })

    def test_executor_has_no_provider_raw_or_bet_source_dependency(self) -> None:
        source = Path(executor_module.__file__).read_text(encoding="utf-8")
        for forbidden in (
            "RaceResultProvider",
            "PayoutProvider",
            "RawRaceResult",
            "RawPayoutPublication",
            "ProviderContext",
            "RaceEntryUniverse",
            "SimulationBetSource",
        ):
            self.assertNotIn(forbidden, source)

    def test_executor_is_not_exported_from_package_root(self) -> None:
        self.assertFalse(hasattr(simulation_package, "PersistedRaceSimulationExecutor"))

    def test_executor_has_no_repository_database_network_or_current_time_dependency(self) -> None:
        source = Path(executor_module.__file__).read_text(encoding="utf-8")
        for forbidden in (
            "sqlite3",
            "connect(",
            "SQLite",
            "requests",
            "httpx",
            "datetime.now",
            "datetime.utcnow",
            "logging",
            "print(",
        ):
            self.assertNotIn(forbidden, source)

    def test_executor_does_not_compare_settlement_times_to_prediction_cutoff(self) -> None:
        source = Path(executor_module.__file__).read_text(encoding="utf-8")
        self.assertNotIn("information_cutoff", source)
        self.assertNotIn("_validate_prediction_cutoff", source)

    def test_existing_contract_modules_and_race_count_remain_unchanged(self) -> None:
        from scripts.simulation.models import SimulationSummary
        from scripts.simulation.persisted_settlement import PersistedRaceSettlementSource
        from scripts.simulation.settlement import RaceSettlementSource

        self.assertEqual(SimulationSummary.__module__, "scripts.simulation.models")
        self.assertTrue(PersistedRaceSettlementSource._is_protocol)
        self.assertTrue(RaceSettlementSource._is_protocol)
        self.assertFalse(hasattr(SimulationSummary, "target_race_count"))


if __name__ == "__main__":
    unittest.main()
