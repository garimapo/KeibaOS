"""Contract tests for the provider-backed one-race executor."""

from __future__ import annotations

import ast
from datetime import date, datetime, timedelta, timezone
import inspect
from pathlib import Path
import textwrap
from unittest.mock import patch
import unittest

from scripts.prediction.bet_strategy import StrategyConfig
from scripts.prediction.prediction_pipeline import RacePredictionInput
from scripts.prediction.track_engine import RaceTrackConditions
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
import scripts.simulation.provider_backed_executor as executor_module
from scripts.simulation.provider_backed_executor import ProviderBackedRaceSimulationExecutor
from scripts.simulation.providers.interfaces import ProviderBuildResult
from scripts.simulation.providers.models import (
    CompletenessResult,
    CompletenessStatus,
    ProviderContext,
    RaceEntryUniverse,
    RawPayoutPublication,
    RawRaceResult,
)
from scripts.simulation.repositories.interfaces import (
    PayoutPublication,
    PayoutRecord,
    PayoutStatus,
    PersistedRaceResult,
    PersistedRaceResultEntry,
    RaceResultEntryStatus,
    RaceResultStatus,
)
from scripts.simulation.settlement import RaceSettlementData
from scripts.simulation.validation import SimulationValidationError


UTC = timezone.utc
CUTOFF = datetime(2026, 7, 24, 9, 0, tzinfo=UTC)
RESULT_FINALIZED_AT = CUTOFF - timedelta(minutes=2)
PAYOUT_FINALIZED_AT = CUTOFF - timedelta(minutes=1)
BET_CUTOFF = CUTOFF - timedelta(minutes=10)


def strategy_identity() -> StrategyIdentity:
    return build_strategy_identity("ProviderBackedExecutor", StrategyConfig())


def race_input(race_id: int = 101) -> SimulationRaceInput:
    pipeline_input = RacePredictionInput(
        {11: []},
        {11: "Jockey"},
        RaceTrackConditions("Tokyo", 1600, "turf", "firm"),
        {11: 2.0},
        1,
        race_id,
    )
    audit = InputSnapshotAudit(
        "dataset",
        "source",
        CUTOFF,
        (
            InputAuditEntry("entry", "entry/11", "source", "entry/11", 11, observed_at=CUTOFF),
            InputAuditEntry("odds", "odds/11", "source", "odds/11", 11, observed_at=CUTOFF),
            InputAuditEntry("jockey", "jockey/11", "source", "jockey/11", 11, observed_at=CUTOFF),
            InputAuditEntry("track", "track", "source", "track", None, observed_at=CUTOFF),
            InputAuditEntry("past_race", "past_race/11/none", "source", "past_race/11/none", 11, observed_at=CUTOFF),
        ),
        True,
    )
    return SimulationRaceInput(race_id, date(2026, 7, 24), CUTOFF, CUTOFF, pipeline_input, audit)


def universe(*, race_id: int = 101, pair: bool = False) -> RaceEntryUniverse:
    active = frozenset({11, 12}) if pair else frozenset({11})
    mapping = {1: 11, 2: 12} if pair else {1: 11}
    return RaceEntryUniverse(race_id, active, frozenset(), frozenset(), mapping)


def provider_context(
    *,
    race_id: int = 101,
    bet_type: str | None = None,
    observed_at: datetime = CUTOFF,
    captured_at: datetime | None = None,
    cutoff: datetime = CUTOFF,
) -> ProviderContext:
    return ProviderContext(
        race_id,
        observed_at,
        "source",
        None,
        observed_at if captured_at is None else captured_at,
        cutoff,
        bet_type,
    )


def raw_result(*, finalized_at: datetime = RESULT_FINALIZED_AT) -> RawRaceResult:
    return RawRaceResult("確定", finalized_at, ())


def raw_publication(
    bet_type: str = "単勝",
    *,
    finalized_at: datetime = PAYOUT_FINALIZED_AT,
) -> RawPayoutPublication:
    return RawPayoutPublication(bet_type, finalized_at, (), True, True, True)


def bet(identity: StrategyIdentity, *, race_id: int = 101, bet_type: str = "単勝") -> SimulationBet:
    selection = (11, 12) if bet_type == "馬連" else (11,)
    return SimulationBet(race_id, identity.strategy_id, bet_type, selection, 100, 0, BET_CUTOFF)


def data(
    identity: StrategyIdentity,
    *,
    race_id: int = 101,
    bets: tuple[SimulationBet, ...] | None = None,
    include_result: bool = True,
    publications: dict[str, RawPayoutPublication] | None = None,
    contexts: dict[str, ProviderContext] | None = None,
    race_universe: RaceEntryUniverse | None = None,
) -> RaceSettlementData:
    selected_bets = (bet(identity, race_id=race_id),) if bets is None else bets
    selected_publications = {"単勝": raw_publication()} if publications is None else publications
    selected_contexts = {key: provider_context(race_id=race_id, bet_type=key) for key in selected_publications} if contexts is None else contexts
    return RaceSettlementData(
        race_id=race_id,
        bets=selected_bets,
        raw_race_result=raw_result() if include_result else None,
        race_result_context=provider_context(race_id=race_id) if include_result else None,
        raw_payout_publications_by_bet_type=selected_publications,
        payout_contexts_by_bet_type=selected_contexts,
        universe=universe(race_id=race_id, pair=any(item.bet_type == "馬連" for item in selected_bets)) if race_universe is None else race_universe,
    )


def persisted_result(
    race_id: int = 101,
    *,
    finalized_at: datetime = RESULT_FINALIZED_AT,
    observed_at: datetime = CUTOFF,
) -> PersistedRaceResult:
    return PersistedRaceResult(
        race_id,
        RaceResultStatus.COMPLETE,
        finalized_at,
        observed_at,
        "source",
        (PersistedRaceResultEntry(1, 11, 1, RaceResultEntryStatus.CONFIRMED),),
    )


def publication(
    *,
    race_id: int = 101,
    bet_type: str = "単勝",
    finalized_at: datetime = PAYOUT_FINALIZED_AT,
    observed_at: datetime = CUTOFF,
) -> PayoutPublication:
    selection = (11, 12) if bet_type == "馬連" else (11,)
    return PayoutPublication(
        race_id,
        bet_type,
        finalized_at,
        observed_at,
        True,
        "source",
        (PayoutRecord(selection, 200, PayoutStatus.WINNING),),
    )


def complete_result_output(
    race_id: int = 101,
    *,
    finalized_at: datetime = RESULT_FINALIZED_AT,
    observed_at: datetime = CUTOFF,
) -> ProviderBuildResult[PersistedRaceResult]:
    return ProviderBuildResult(
        persisted_result(race_id, finalized_at=finalized_at, observed_at=observed_at),
        CompletenessResult(CompletenessStatus.COMPLETE, 1, 1),
    )


def complete_payout_output(
    *,
    race_id: int = 101,
    bet_type: str = "単勝",
    finalized_at: datetime = PAYOUT_FINALIZED_AT,
    observed_at: datetime = CUTOFF,
) -> ProviderBuildResult[PayoutPublication]:
    return ProviderBuildResult(
        publication(
            race_id=race_id,
            bet_type=bet_type,
            finalized_at=finalized_at,
            observed_at=observed_at,
        ),
        CompletenessResult(CompletenessStatus.COMPLETE, 1, 1),
    )


def incomplete_result_output(race_id: int = 101) -> ProviderBuildResult[PersistedRaceResult]:
    return ProviderBuildResult(
        persisted_result(race_id),
        CompletenessResult(CompletenessStatus.INCOMPLETE, 1, 1, reasons=("incomplete",)),
    )


def incomplete_payout_output() -> ProviderBuildResult[PayoutPublication]:
    return ProviderBuildResult(
        publication(),
        CompletenessResult(CompletenessStatus.INCOMPLETE, 1, 1, reasons=("incomplete",)),
    )


def no_bet_result(race_id: int, strategy_id: str) -> SimulationResult:
    return SimulationResult(race_id, strategy_id, (), SettlementStatus.NO_BET, None, 0)


class TrackingSource:
    def __init__(self, value: RaceSettlementData | Exception) -> None:
        self.value = value
        self.calls: list[SimulationRaceInput] = []

    def load_settlement_data(self, *, race_input: SimulationRaceInput) -> RaceSettlementData:
        self.calls.append(race_input)
        if isinstance(self.value, Exception):
            raise self.value
        return self.value


class TrackingRaceResultProvider:
    def __init__(self, value: object) -> None:
        self.value = value
        self.calls: list[tuple[object, object, object]] = []

    def build_race_result(self, *, raw: object, context: object, universe: object) -> object:
        self.calls.append((raw, context, universe))
        if isinstance(self.value, Exception):
            raise self.value
        return self.value


class TrackingPayoutProvider:
    def __init__(self, values: dict[str, object]) -> None:
        self.values = values
        self.calls: list[tuple[object, object, object]] = []

    def build_payout_publication(self, *, raw: RawPayoutPublication, context: object, universe: object) -> object:
        self.calls.append((raw, context, universe))
        value = self.values[raw.bet_type]
        if isinstance(value, Exception):
            raise value
        return value


class ProviderBackedExecutorTests(unittest.TestCase):
    def make(
        self,
        *,
        identity: StrategyIdentity | None = None,
        settlement_data: RaceSettlementData | Exception | None = None,
        result_output: object | None = None,
        payout_outputs: dict[str, object] | None = None,
    ) -> tuple[
        ProviderBackedRaceSimulationExecutor,
        StrategyIdentity,
        TrackingSource,
        TrackingRaceResultProvider,
        TrackingPayoutProvider,
    ]:
        actual_identity = identity or strategy_identity_factory()
        source = TrackingSource(settlement_data or data(actual_identity))
        result_provider = TrackingRaceResultProvider(result_output or complete_result_output())
        payout_provider = TrackingPayoutProvider(payout_outputs or {"単勝": complete_payout_output()})
        return (
            ProviderBackedRaceSimulationExecutor(
                strategy_identity=actual_identity,
                settlement_source=source,
                race_result_provider=result_provider,
                payout_provider=payout_provider,
            ),
            actual_identity,
            source,
            result_provider,
            payout_provider,
        )

    def test_constructor_preserves_dependency_identity(self) -> None:
        executor, identity, source, result_provider, payout_provider = self.make()
        self.assertIs(executor.strategy_identity, identity)
        self.assertIs(executor.settlement_source, source)
        self.assertIs(executor.race_result_provider, result_provider)
        self.assertIs(executor.payout_provider, payout_provider)

    def test_constructor_is_keyword_only(self) -> None:
        signature = inspect.signature(ProviderBackedRaceSimulationExecutor)
        self.assertEqual(tuple(signature.parameters), ("strategy_identity", "settlement_source", "race_result_provider", "payout_provider"))
        self.assertTrue(all(value.kind is inspect.Parameter.KEYWORD_ONLY for value in signature.parameters.values()))

    def test_constructor_rejects_invalid_dependencies(self) -> None:
        identity = strategy_identity_factory()
        source = TrackingSource(data(identity))
        result_provider = TrackingRaceResultProvider(complete_result_output())
        payout_provider = TrackingPayoutProvider({"単勝": complete_payout_output()})
        cases = (
            (object(), source, result_provider, payout_provider),
            (identity, object(), result_provider, payout_provider),
            (identity, source, object(), payout_provider),
            (identity, source, result_provider, object()),
        )
        for actual_identity, actual_source, actual_result, actual_payout in cases:
            with self.subTest(value=(actual_identity, actual_source, actual_result, actual_payout)), self.assertRaises(SimulationValidationError):
                ProviderBackedRaceSimulationExecutor(
                    strategy_identity=actual_identity,  # type: ignore[arg-type]
                    settlement_source=actual_source,  # type: ignore[arg-type]
                    race_result_provider=actual_result,  # type: ignore[arg-type]
                    payout_provider=actual_payout,  # type: ignore[arg-type]
                )

    def test_constructor_does_not_execute_dependencies(self) -> None:
        executor, _, source, result_provider, payout_provider = self.make()
        self.assertIsInstance(executor, ProviderBackedRaceSimulationExecutor)
        self.assertEqual(source.calls, [])
        self.assertEqual(result_provider.calls, [])
        self.assertEqual(payout_provider.calls, [])

    def test_constructor_does_not_call_result_builder(self) -> None:
        tree = ast.parse(textwrap.dedent(inspect.getsource(ProviderBackedRaceSimulationExecutor.__init__)))
        calls = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertNotIn("_build_simulation_result_for_race", calls)

    def test_slots_prevent_extra_attributes(self) -> None:
        executor, *_ = self.make()
        with self.assertRaises(AttributeError):
            executor.unexpected = "value"  # type: ignore[attr-defined]

    def test_properties_are_read_only(self) -> None:
        executor, *_ = self.make()
        with self.assertRaises(AttributeError):
            executor.strategy_identity = strategy_identity_factory()  # type: ignore[misc]

    def test_call_is_keyword_only(self) -> None:
        executor, *_ = self.make()
        with self.assertRaises(TypeError):
            executor(race_input())  # type: ignore[call-arg]

    def test_rejects_invalid_race_input_before_source(self) -> None:
        executor, _, source, result_provider, payout_provider = self.make()
        with self.assertRaises(SimulationValidationError):
            executor(race_input=object())  # type: ignore[arg-type]
        self.assertEqual(source.calls, [])
        self.assertEqual(result_provider.calls, [])
        self.assertEqual(payout_provider.calls, [])

    def test_source_is_called_once_with_original_keyword_object(self) -> None:
        executor, _, source, *_ = self.make()
        item = race_input()
        with patch.object(executor_module, "_build_simulation_result_for_race", return_value=no_bet_result(101, executor.strategy_identity.strategy_id)):
            executor(race_input=item)
        self.assertEqual(source.calls, [item])
        self.assertIs(source.calls[0], item)

    def test_source_wrong_return_type_stops_providers_and_builder(self) -> None:
        executor, _, source, result_provider, payout_provider = self.make(settlement_data=object())  # type: ignore[arg-type]
        with patch.object(executor_module, "_build_simulation_result_for_race", side_effect=AssertionError("builder must not run")):
            with self.assertRaises(SimulationValidationError):
                executor(race_input=race_input())
        self.assertEqual(len(source.calls), 1)
        self.assertEqual(result_provider.calls, [])
        self.assertEqual(payout_provider.calls, [])

    def test_bundle_race_mismatch_stops_providers_and_builder(self) -> None:
        identity = strategy_identity_factory()
        mismatched = data(identity, race_id=102)
        executor, _, _, result_provider, payout_provider = self.make(identity=identity, settlement_data=mismatched)
        with patch.object(executor_module, "_build_simulation_result_for_race", side_effect=AssertionError("builder must not run")):
            with self.assertRaises(SimulationValidationError):
                executor(race_input=race_input(101))
        self.assertEqual(result_provider.calls, [])
        self.assertEqual(payout_provider.calls, [])

    def test_strategy_mismatch_stops_providers_and_builder(self) -> None:
        identity = strategy_identity_factory()
        other_identity = build_strategy_identity("Other", StrategyConfig())
        mismatched = data(identity, bets=(bet(other_identity),))
        executor, _, _, result_provider, payout_provider = self.make(identity=identity, settlement_data=mismatched)
        with patch.object(executor_module, "_build_simulation_result_for_race", side_effect=AssertionError("builder must not run")):
            with self.assertRaises(SimulationValidationError):
                executor(race_input=race_input())
        self.assertEqual(result_provider.calls, [])
        self.assertEqual(payout_provider.calls, [])

    def test_settlement_contexts_after_prediction_cutoff_are_accepted(self) -> None:
        identity = strategy_identity_factory()
        observed_at = CUTOFF + timedelta(minutes=1)
        source_cutoff = CUTOFF + timedelta(minutes=2)
        bundle = RaceSettlementData(
            race_id=101,
            bets=(bet(identity),),
            raw_race_result=raw_result(),
            race_result_context=provider_context(
                observed_at=observed_at,
                captured_at=observed_at,
                cutoff=source_cutoff,
            ),
            raw_payout_publications_by_bet_type={"単勝": raw_publication()},
            payout_contexts_by_bet_type={
                "単勝": provider_context(
                    bet_type="単勝",
                    observed_at=observed_at,
                    captured_at=observed_at,
                    cutoff=source_cutoff,
                )
            },
            universe=universe(),
        )
        executor, _, _, result_provider, payout_provider = self.make(identity=identity, settlement_data=bundle)
        executor(race_input=race_input())
        self.assertEqual(len(result_provider.calls), 1)
        self.assertEqual(len(payout_provider.calls), 1)
        self.assertIs(result_provider.calls[0][1], bundle.race_result_context)
        self.assertIs(payout_provider.calls[0][1], bundle.payout_contexts_by_bet_type["単勝"])

    def test_provider_context_rejects_times_after_its_own_information_cutoff(self) -> None:
        after_cutoff = CUTOFF + timedelta(minutes=1)
        for name, values in (
            ("observed_at", {"observed_at": after_cutoff, "captured_at": CUTOFF}),
            ("captured_at", {"observed_at": CUTOFF, "captured_at": after_cutoff}),
        ):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    provider_context(cutoff=CUTOFF, **values)

    def test_source_exception_is_propagated_by_identity(self) -> None:
        failure = SimulationValidationError(101, "source", "failure")
        identity = strategy_identity_factory()
        executor, _, _, result_provider, payout_provider = self.make(identity=identity, settlement_data=failure)
        with patch.object(executor_module, "_build_simulation_result_for_race", side_effect=AssertionError("builder must not run")):
            with self.assertRaises(SimulationValidationError) as caught:
                executor(race_input=race_input())
        self.assertIs(caught.exception, failure)
        self.assertEqual(result_provider.calls, [])
        self.assertEqual(payout_provider.calls, [])

    def test_no_bet_skips_providers_and_calls_builder_once(self) -> None:
        identity = strategy_identity_factory()
        bundle = data(identity, bets=())
        executor, _, source, result_provider, payout_provider = self.make(identity=identity, settlement_data=bundle)
        expected = no_bet_result(101, identity.strategy_id)
        with patch.object(executor_module, "_build_simulation_result_for_race", return_value=expected) as builder:
            actual = executor(race_input=race_input())
        self.assertIs(actual, expected)
        self.assertEqual(len(source.calls), 1)
        self.assertEqual(result_provider.calls, [])
        self.assertEqual(payout_provider.calls, [])
        builder.assert_called_once()
        self.assertIsNone(builder.call_args.kwargs["settled_at"])

    def test_missing_raw_result_skips_providers_and_marks_missing_result(self) -> None:
        identity = strategy_identity_factory()
        bundle = data(identity, include_result=False)
        executor, _, _, result_provider, payout_provider = self.make(identity=identity, settlement_data=bundle)
        expected = no_bet_result(101, identity.strategy_id)
        with patch.object(executor_module, "_build_simulation_result_for_race", return_value=expected) as builder:
            executor(race_input=race_input())
        self.assertEqual(result_provider.calls, [])
        self.assertEqual(payout_provider.calls, [])
        self.assertTrue(builder.call_args.kwargs["missing_race_result"])
        self.assertIsNone(builder.call_args.kwargs["settled_at"])

    def test_result_provider_receives_original_raw_context_and_universe(self) -> None:
        executor, _, source, result_provider, _ = self.make()
        with patch.object(executor_module, "_build_simulation_result_for_race", return_value=no_bet_result(101, executor.strategy_identity.strategy_id)):
            executor(race_input=race_input())
        self.assertEqual(len(result_provider.calls), 1)
        raw, context_value, universe_value = result_provider.calls[0]
        self.assertIs(raw, source.value.raw_race_result)  # type: ignore[union-attr]
        self.assertIs(context_value, source.value.race_result_context)  # type: ignore[union-attr]
        self.assertIs(universe_value, source.value.universe)  # type: ignore[union-attr]

    def test_invalid_result_provider_output_stops_payout_and_builder(self) -> None:
        executor, _, _, _, payout_provider = self.make(result_output=object())
        with patch.object(executor_module, "_build_simulation_result_for_race", side_effect=AssertionError("builder must not run")):
            with self.assertRaises(SimulationValidationError):
                executor(race_input=race_input())
        self.assertEqual(payout_provider.calls, [])

    def test_provider_outputs_after_prediction_cutoff_are_accepted(self) -> None:
        result_finalized_at = CUTOFF + timedelta(minutes=30)
        result_observed_at = CUTOFF + timedelta(minutes=40)
        payout_finalized_at = CUTOFF + timedelta(minutes=50)
        payout_observed_at = CUTOFF + timedelta(minutes=60)
        source_cutoff = CUTOFF + timedelta(minutes=70)
        identity = strategy_identity_factory()
        bundle = RaceSettlementData(
            race_id=101,
            bets=(bet(identity),),
            raw_race_result=raw_result(finalized_at=result_finalized_at),
            race_result_context=provider_context(
                observed_at=result_observed_at,
                captured_at=result_observed_at,
                cutoff=source_cutoff,
            ),
            raw_payout_publications_by_bet_type={
                "単勝": raw_publication(finalized_at=payout_finalized_at)
            },
            payout_contexts_by_bet_type={
                "単勝": provider_context(
                    bet_type="単勝",
                    observed_at=payout_observed_at,
                    captured_at=payout_observed_at,
                    cutoff=source_cutoff,
                )
            },
            universe=universe(),
        )
        executor, _, _, result_provider, payout_provider = self.make(
            identity=identity,
            settlement_data=bundle,
            result_output=complete_result_output(
                finalized_at=result_finalized_at,
                observed_at=result_observed_at,
            ),
            payout_outputs={
                "単勝": complete_payout_output(
                    finalized_at=payout_finalized_at,
                    observed_at=payout_observed_at,
                )
            },
        )
        actual = executor(race_input=race_input())
        self.assertEqual(actual.settlement_status, SettlementStatus.SETTLED)
        self.assertEqual(actual.settled_at, payout_finalized_at)
        self.assertEqual(len(result_provider.calls), 1)
        self.assertEqual(len(payout_provider.calls), 1)

    def test_incomplete_result_skips_payout_and_calls_builder_once(self) -> None:
        executor, _, _, _, payout_provider = self.make(result_output=incomplete_result_output())
        expected = no_bet_result(101, executor.strategy_identity.strategy_id)
        with patch.object(executor_module, "_build_simulation_result_for_race", return_value=expected) as builder:
            executor(race_input=race_input())
        self.assertEqual(payout_provider.calls, [])
        builder.assert_called_once()
        self.assertEqual(builder.call_args.kwargs["completeness_statuses"], (CompletenessStatus.INCOMPLETE,))
        self.assertIsNone(builder.call_args.kwargs["settled_at"])

    def test_result_provider_exception_is_propagated_and_stops_builder(self) -> None:
        failure = SimulationValidationError(101, "result_provider", "failure")
        executor, _, _, _, payout_provider = self.make(result_output=failure)
        with patch.object(executor_module, "_build_simulation_result_for_race", side_effect=AssertionError("builder must not run")):
            with self.assertRaises(SimulationValidationError) as caught:
                executor(race_input=race_input())
        self.assertIs(caught.exception, failure)
        self.assertEqual(payout_provider.calls, [])

    def test_missing_required_payouts_skip_all_payout_calls(self) -> None:
        identity = strategy_identity_factory()
        bundle = data(identity, publications={}, contexts={})
        executor, _, _, _, payout_provider = self.make(identity=identity, settlement_data=bundle)
        expected = no_bet_result(101, identity.strategy_id)
        with patch.object(executor_module, "_build_simulation_result_for_race", return_value=expected) as builder:
            executor(race_input=race_input())
        self.assertEqual(payout_provider.calls, [])
        self.assertEqual(builder.call_args.kwargs["missing_payout_bet_types"], ("単勝",))
        self.assertIsNone(builder.call_args.kwargs["settled_at"])

    def test_payout_provider_uses_only_required_bet_type(self) -> None:
        identity = strategy_identity_factory()
        bundle = data(
            identity,
            publications={"単勝": raw_publication("単勝"), "馬連": raw_publication("馬連")},
            contexts={"単勝": provider_context(bet_type="単勝"), "馬連": provider_context(bet_type="馬連")},
        )
        executor, _, _, _, payout_provider = self.make(
            identity=identity,
            settlement_data=bundle,
            payout_outputs={"単勝": complete_payout_output(), "馬連": complete_payout_output(bet_type="馬連")},
        )
        with patch.object(executor_module, "_build_simulation_result_for_race", return_value=no_bet_result(101, identity.strategy_id)):
            executor(race_input=race_input())
        self.assertEqual([value[0].bet_type for value in payout_provider.calls], ["単勝"])

    def test_payout_provider_preserves_required_bet_type_order(self) -> None:
        identity = strategy_identity_factory()
        first = bet(identity, bet_type="単勝")
        second = bet(identity, bet_type="馬連")
        bundle = data(
            identity,
            bets=(second, first),
            publications={"単勝": raw_publication("単勝"), "馬連": raw_publication("馬連")},
            contexts={"単勝": provider_context(bet_type="単勝"), "馬連": provider_context(bet_type="馬連")},
            race_universe=universe(pair=True),
        )
        executor, _, _, _, payout_provider = self.make(
            identity=identity,
            settlement_data=bundle,
            payout_outputs={"単勝": complete_payout_output(), "馬連": complete_payout_output(bet_type="馬連")},
        )
        with patch.object(executor_module, "_build_simulation_result_for_race", return_value=no_bet_result(101, identity.strategy_id)):
            executor(race_input=race_input())
        self.assertEqual([value[0].bet_type for value in payout_provider.calls], ["馬連", "単勝"])

    def test_payout_provider_receives_original_raw_context_and_universe(self) -> None:
        executor, _, source, _, payout_provider = self.make()
        with patch.object(executor_module, "_build_simulation_result_for_race", return_value=no_bet_result(101, executor.strategy_identity.strategy_id)):
            executor(race_input=race_input())
        raw, context_value, universe_value = payout_provider.calls[0]
        self.assertIs(raw, source.value.raw_payout_publications_by_bet_type["単勝"])  # type: ignore[union-attr]
        self.assertIs(context_value, source.value.payout_contexts_by_bet_type["単勝"])  # type: ignore[union-attr]
        self.assertIs(universe_value, source.value.universe)  # type: ignore[union-attr]

    def test_incomplete_payout_stops_later_payout_provider_calls(self) -> None:
        identity = strategy_identity_factory()
        bundle = data(
            identity,
            bets=(bet(identity), bet(identity, bet_type="馬連")),
            publications={"単勝": raw_publication(), "馬連": raw_publication("馬連")},
            contexts={"単勝": provider_context(bet_type="単勝"), "馬連": provider_context(bet_type="馬連")},
            race_universe=universe(pair=True),
        )
        executor, _, _, _, payout_provider = self.make(
            identity=identity,
            settlement_data=bundle,
            payout_outputs={"単勝": incomplete_payout_output(), "馬連": complete_payout_output(bet_type="馬連")},
        )
        with patch.object(executor_module, "_build_simulation_result_for_race", return_value=no_bet_result(101, identity.strategy_id)) as builder:
            executor(race_input=race_input())
        self.assertEqual([value[0].bet_type for value in payout_provider.calls], ["単勝"])
        builder.assert_called_once()
        self.assertIsNone(builder.call_args.kwargs["settled_at"])

    def test_payout_provider_exception_is_propagated_and_stops_builder(self) -> None:
        failure = SimulationValidationError(101, "payout_provider", "failure")
        executor, _, _, _, _ = self.make(payout_outputs={"単勝": failure})
        with patch.object(executor_module, "_build_simulation_result_for_race", side_effect=AssertionError("builder must not run")):
            with self.assertRaises(SimulationValidationError) as caught:
                executor(race_input=race_input())
        self.assertIs(caught.exception, failure)

    def test_settled_at_uses_result_and_required_publication_maximum(self) -> None:
        executor, _, _, _, _ = self.make()
        expected = no_bet_result(101, executor.strategy_identity.strategy_id)
        with patch.object(executor_module, "_build_simulation_result_for_race", return_value=expected) as builder:
            executor(race_input=race_input())
        self.assertEqual(builder.call_args.kwargs["settled_at"], PAYOUT_FINALIZED_AT)

    def test_result_builder_receives_transformed_values_and_preserves_return_identity(self) -> None:
        executor, identity, source, _, _ = self.make()
        expected = no_bet_result(101, identity.strategy_id)
        with patch.object(executor_module, "_build_simulation_result_for_race", return_value=expected) as builder:
            actual = executor(race_input=race_input())
        self.assertIs(actual, expected)
        self.assertEqual(builder.call_args.kwargs["bets"], source.value.bets)  # type: ignore[union-attr]
        self.assertIs(builder.call_args.kwargs["publications_by_bet_type"]["単勝"].entries[0].payout_status, PayoutStatus.WINNING)
        self.assertEqual(builder.call_args.kwargs["race_result_status"], RaceResultStatus.COMPLETE)
        self.assertEqual(builder.call_args.kwargs["completeness_statuses"], (CompletenessStatus.COMPLETE, CompletenessStatus.COMPLETE))

    def test_result_builder_exception_is_propagated_by_identity(self) -> None:
        executor, _, _, _, _ = self.make()
        failure = SimulationValidationError(101, "builder", "failure")
        with patch.object(executor_module, "_build_simulation_result_for_race", side_effect=failure):
            with self.assertRaises(SimulationValidationError) as caught:
                executor(race_input=race_input())
        self.assertIs(caught.exception, failure)

    def test_real_result_builder_produces_settled_result(self) -> None:
        executor, identity, *_ = self.make()
        result = executor(race_input=race_input())
        self.assertEqual(result.settlement_status, SettlementStatus.SETTLED)
        self.assertEqual(result.strategy_id, identity.strategy_id)
        self.assertEqual(result.settled_at, PAYOUT_FINALIZED_AT)

    def test_adapter_source_calls_only_integrated_result_builder(self) -> None:
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
        })

    def test_adapter_has_no_database_network_or_current_time_dependency(self) -> None:
        source = Path(executor_module.__file__).read_text(encoding="utf-8")
        for forbidden in ("sqlite3", "connect(", "requests", "httpx", "datetime.now", "datetime.utcnow", "logging", "print("):
            self.assertNotIn(forbidden, source)

    def test_existing_contract_modules_and_race_count_remain_unchanged(self) -> None:
        from scripts.simulation.models import SimulationSummary
        from scripts.simulation.settlement import RaceSettlementSource

        self.assertEqual(SimulationSummary.__module__, "scripts.simulation.models")
        self.assertTrue(RaceSettlementSource._is_protocol)
        self.assertFalse(hasattr(SimulationSummary, "target_race_count"))


def strategy_identity_factory() -> StrategyIdentity:
    return strategy_identity()


if __name__ == "__main__":
    unittest.main()
