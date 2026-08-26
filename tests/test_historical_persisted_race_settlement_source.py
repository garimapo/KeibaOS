"""Tests for cutoff-aware historical persisted settlement facts."""

from __future__ import annotations

import ast
from collections.abc import Iterator, Mapping
from datetime import UTC, date, datetime, timedelta
import inspect
from typing import get_type_hints
import unittest

import scripts.simulation as simulation_package
import scripts.simulation.historical_persisted_race_settlement_source as source_module
from scripts.prediction.bet_strategy import StrategyConfig
from scripts.prediction.prediction_pipeline import RacePredictionInput
from scripts.prediction.track_engine import RaceTrackConditions
from scripts.simulation.bet_source import SimulationBetSource
from scripts.simulation.historical_persisted_race_settlement_source import (
    HistoricalPersistedRaceSettlementSource,
)
from scripts.simulation.models import (
    InputAuditEntry,
    InputSnapshotAudit,
    SimulationBet,
    SimulationRaceInput,
    StrategyIdentity,
    build_strategy_identity,
)
from scripts.simulation.persisted_settlement import (
    PersistedRaceSettlementData,
    PersistedRaceSettlementSource,
)
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
from scripts.simulation.validation import SimulationValidationError


CUTOFF = datetime(2026, 7, 28, 12, 0, tzinfo=UTC)


def strategy_identity(name: str = "HistoricalSettlement") -> StrategyIdentity:
    return build_strategy_identity(name, StrategyConfig())


def race_input(race_id: int = 101) -> SimulationRaceInput:
    pipeline = RacePredictionInput(
        {1: [], 2: [], 3: []},
        {1: "Jockey A", 2: "Jockey B", 3: "Jockey C"},
        RaceTrackConditions("Tokyo", 1600, "turf", "firm"),
        {1: 2.0, 2: 4.0, 3: 8.0},
        3,
        race_id,
    )
    audit = InputSnapshotAudit(
        "dataset",
        "source",
        CUTOFF - timedelta(hours=4),
        tuple(
            InputAuditEntry(kind, key, "source", key, entry_id, observed_at=CUTOFF - timedelta(hours=4))
            for kind, key, entry_id in (
                ("entry", "entry/1", 1),
                ("entry", "entry/2", 2),
                ("entry", "entry/3", 3),
                ("odds", "odds/1", 1),
                ("odds", "odds/2", 2),
                ("odds", "odds/3", 3),
                ("jockey", "jockey/1", 1),
                ("jockey", "jockey/2", 2),
                ("jockey", "jockey/3", 3),
                ("track", "track", None),
                ("past_race", "past_race/1/none", 1),
                ("past_race", "past_race/2/none", 2),
                ("past_race", "past_race/3/none", 3),
            )
        ),
        True,
    )
    return SimulationRaceInput(
        race_id,
        date(2026, 7, 28),
        CUTOFF - timedelta(hours=3),
        CUTOFF - timedelta(hours=4),
        pipeline,
        audit,
    )


def bet(
    race: SimulationRaceInput,
    strategy: StrategyIdentity,
    *,
    bet_type: str = "単勝",
    selection: tuple[int, ...] = (1,),
    rank: int = 0,
) -> SimulationBet:
    return SimulationBet(
        race_id=race.race_id,
        strategy_id=strategy.strategy_id,
        bet_type=bet_type,
        race_entry_ids=selection,
        stake=100,
        recommendation_rank=rank,
        placed_at_cutoff=race.information_cutoff,
    )


def persisted_result(
    *,
    race_id: int = 101,
    observed_at: datetime = CUTOFF,
) -> PersistedRaceResult:
    return PersistedRaceResult(
        race_id=race_id,
        result_status=RaceResultStatus.COMPLETE,
        finalized_at=observed_at,
        observed_at=observed_at,
        source="official",
        entries=(PersistedRaceResultEntry(1, 1, 1, RaceResultEntryStatus.CONFIRMED),),
    )


def publication(
    *,
    race_id: int = 101,
    bet_type: str = "単勝",
    observed_at: datetime = CUTOFF,
    complete: bool = True,
) -> PayoutPublication:
    selection = {"単勝": (1,), "ワイド": (1, 2), "馬連": (1, 3)}[bet_type]
    return PayoutPublication(
        race_id=race_id,
        bet_type=bet_type,
        finalized_at=observed_at if complete else None,
        observed_at=observed_at,
        is_complete=complete,
        source="official",
        entries=(PayoutRecord(selection, 200, PayoutStatus.WINNING),),
    )


class RecordingBetSource:
    def __init__(self, response: object) -> None:
        self.response = response
        self.calls: list[tuple[object, object]] = []

    def load_bets(
        self,
        *,
        race_input: SimulationRaceInput,
        strategy_identity: StrategyIdentity,
    ) -> tuple[SimulationBet, ...]:
        self.calls.append((race_input, strategy_identity))
        if isinstance(self.response, BaseException):
            raise self.response
        return self.response  # type: ignore[return-value]


class RecordingRaceResultRepository:
    def __init__(self, response: object) -> None:
        self.response = response
        self.calls: list[int] = []

    def get_race_result(self, race_id: int) -> PersistedRaceResult | None:
        self.calls.append(race_id)
        if isinstance(self.response, BaseException):
            raise self.response
        return self.response  # type: ignore[return-value]


class RecordingPayoutRepository:
    def __init__(self, responses: Mapping[str, object]) -> None:
        self.responses = dict(responses)
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
        response = self.responses.get(bet_type)
        if isinstance(response, BaseException):
            raise response
        return response  # type: ignore[return-value]


class CountingMapping(Mapping[int, datetime]):
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


class TupleSubclass(tuple[SimulationBet, ...]):
    pass


class MissingMethod:
    pass


class NonCallableBetSource:
    load_bets = None


class HistoricalPersistedRaceSettlementSourceTests(unittest.TestCase):
    def make(
        self,
        *,
        bets: object = (),
        race_result: object = None,
        publications: Mapping[str, object] | None = None,
        cutoffs: Mapping[int, datetime] | None = None,
    ) -> tuple[
        HistoricalPersistedRaceSettlementSource,
        RecordingBetSource,
        RecordingRaceResultRepository,
        RecordingPayoutRepository,
    ]:
        bet_source = RecordingBetSource(bets)
        result_repository = RecordingRaceResultRepository(race_result)
        payout_repository = RecordingPayoutRepository({} if publications is None else publications)
        source = HistoricalPersistedRaceSettlementSource(
            bet_source=bet_source,
            race_result_repository=result_repository,
            payout_repository=payout_repository,
            settlement_cutoffs_by_race_id={101: CUTOFF} if cutoffs is None else cutoffs,
        )
        return source, bet_source, result_repository, payout_repository

    def assert_error(
        self,
        error: SimulationValidationError,
        *,
        identifier: str,
        reason: str,
        race_id: int = 101,
    ) -> None:
        self.assertEqual(error.race_id, race_id)
        self.assertEqual(error.input_identifier, identifier)
        self.assertEqual(error.reason, reason)

    def test_public_surface_constructor_and_protocol_signature(self) -> None:
        self.assertEqual(source_module.__all__, ("HistoricalPersistedRaceSettlementSource",))
        self.assertFalse(hasattr(simulation_package, "HistoricalPersistedRaceSettlementSource"))
        signature = inspect.signature(HistoricalPersistedRaceSettlementSource)
        self.assertEqual(
            tuple(signature.parameters),
            (
                "bet_source",
                "race_result_repository",
                "payout_repository",
                "settlement_cutoffs_by_race_id",
            ),
        )
        self.assertTrue(
            all(value.kind is inspect.Parameter.KEYWORD_ONLY for value in signature.parameters.values())
        )
        hints = get_type_hints(HistoricalPersistedRaceSettlementSource.__init__)
        self.assertIs(hints["bet_source"], SimulationBetSource)
        self.assertIs(hints["race_result_repository"], RaceResultRepository)
        self.assertIs(hints["payout_repository"], PayoutRepository)
        self.assertEqual(hints["settlement_cutoffs_by_race_id"], Mapping[int, datetime])
        self.assertEqual(
            inspect.signature(HistoricalPersistedRaceSettlementSource.load_settlement_data),
            inspect.signature(PersistedRaceSettlementSource.load_settlement_data),
        )
        self.assertEqual(
            get_type_hints(HistoricalPersistedRaceSettlementSource.load_settlement_data),
            get_type_hints(PersistedRaceSettlementSource.load_settlement_data),
        )

    def test_constructor_rejects_missing_or_noncallable_collaborator_methods(self) -> None:
        valid_bet = RecordingBetSource(())
        valid_result = RecordingRaceResultRepository(None)
        valid_payout = RecordingPayoutRepository({})
        cases = (
            (MissingMethod(), valid_result, valid_payout),
            (NonCallableBetSource(), valid_result, valid_payout),
            (valid_bet, MissingMethod(), valid_payout),
            (valid_bet, valid_result, MissingMethod()),
        )
        for bet_source, result_repository, payout_repository in cases:
            with self.subTest(types=tuple(type(value).__name__ for value in cases)):
                with self.assertRaises(ValueError):
                    HistoricalPersistedRaceSettlementSource(
                        bet_source=bet_source,  # type: ignore[arg-type]
                        race_result_repository=result_repository,  # type: ignore[arg-type]
                        payout_repository=payout_repository,  # type: ignore[arg-type]
                        settlement_cutoffs_by_race_id={},
                    )

    def test_constructor_validates_and_defensively_freezes_cutoff_mapping(self) -> None:
        aware = datetime(2026, 7, 28, 12, 0, tzinfo=UTC)
        invalid_mappings: tuple[object, ...] = (
            [],
            {True: aware},
            {0: aware},
            {-1: aware},
            {"101": aware},
            {101: datetime(2026, 7, 28, 12, 0)},
        )
        for value in invalid_mappings:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.make(cutoffs=value)  # type: ignore[arg-type]

        caller_values = {101: aware}
        counting = CountingMapping(caller_values)
        source, bet_source, result_repository, payout_repository = self.make(cutoffs=counting)
        self.assertEqual(counting.iterations, 1)
        self.assertIs(source._settlement_cutoffs_by_race_id[101], aware)
        caller_values.clear()
        self.assertIs(source._settlement_cutoffs_by_race_id[101], aware)
        self.assertEqual((bet_source.calls, result_repository.calls, payout_repository.calls), ([], [], []))
        empty_source, *_ = self.make(cutoffs={})
        self.assertEqual(empty_source._settlement_cutoffs_by_race_id, {})

    def test_load_boundary_and_missing_cutoff_fail_before_all_collaborators(self) -> None:
        source, bet_source, result_repository, payout_repository = self.make(cutoffs={})
        strategy = strategy_identity()
        for invalid_race, invalid_strategy in ((None, strategy), (race_input(), None)):
            with self.subTest(value=(invalid_race, invalid_strategy)), self.assertRaises(ValueError):
                source.load_settlement_data(
                    race_input=invalid_race,  # type: ignore[arg-type]
                    strategy_identity=invalid_strategy,  # type: ignore[arg-type]
                )
        with self.assertRaises(SimulationValidationError) as caught:
            source.load_settlement_data(race_input=race_input(), strategy_identity=strategy)
        self.assert_error(
            caught.exception,
            identifier="settlement_cutoffs_by_race_id",
            reason="settlement cutoff was not provided for race_id",
        )
        self.assertEqual((bet_source.calls, result_repository.calls, payout_repository.calls), ([], [], []))

    def test_bet_source_called_once_and_malformed_outputs_fail_before_official_io(self) -> None:
        race = race_input()
        strategy = strategy_identity()
        valid = bet(race, strategy)
        other_strategy = strategy_identity("Other")
        cases = (
            ([valid], "bet source must return a tuple of SimulationBet values"),
            (TupleSubclass((valid,)), "bet source must return a tuple of SimulationBet values"),
            ((object(),), "bet source must return only SimulationBet values"),
            ((bet(race_input(102), strategy),), "bet source bets must match race_input.race_id"),
            ((bet(race, other_strategy),), "bet source bets must match strategy_identity.strategy_id"),
            ((valid, bet(race, strategy, rank=1)), "bet source bets must have unique bet identities"),
        )
        for response, reason in cases:
            with self.subTest(reason=reason):
                source, bet_source, result_repository, payout_repository = self.make(bets=response)
                with self.assertRaises(SimulationValidationError) as caught:
                    source.load_settlement_data(race_input=race, strategy_identity=strategy)
                self.assert_error(
                    caught.exception,
                    identifier="simulation_bet_source",
                    reason=reason,
                )
                self.assertEqual(len(bet_source.calls), 1)
                self.assertIs(bet_source.calls[0][0], race)
                self.assertIs(bet_source.calls[0][1], strategy)
                self.assertEqual((result_repository.calls, payout_repository.calls), ([], []))

        distinct = (
            bet(race, strategy, selection=(1,), rank=0),
            bet(race, strategy, selection=(2,), rank=1),
        )
        source, *_ = self.make(
            bets=distinct,
            race_result=None,
            publications={"単勝": None},
        )
        self.assertEqual(
            source.load_settlement_data(race_input=race, strategy_identity=strategy).bets,
            distinct,
        )

    def test_bet_source_exception_propagates_exactly_without_retry(self) -> None:
        error = RepositoryDataIntegrityError("bad persisted bets")
        source, bet_source, result_repository, payout_repository = self.make(bets=error)
        with self.assertRaises(RepositoryDataIntegrityError) as caught:
            source.load_settlement_data(race_input=race_input(), strategy_identity=strategy_identity())
        self.assertIs(caught.exception, error)
        self.assertEqual(len(bet_source.calls), 1)
        self.assertEqual((result_repository.calls, payout_repository.calls), ([], []))

    def test_empty_tuple_short_circuits_all_official_post_race_io(self) -> None:
        race = race_input()
        strategy = strategy_identity()
        source, bet_source, result_repository, payout_repository = self.make(bets=())
        data = source.load_settlement_data(race_input=race, strategy_identity=strategy)
        self.assertIsInstance(data, PersistedRaceSettlementData)
        self.assertEqual(data.race_id, race.race_id)
        self.assertEqual(data.bets, ())
        self.assertIsNone(data.race_result)
        self.assertEqual(dict(data.payout_publications_by_bet_type), {})
        self.assertEqual(len(bet_source.calls), 1)
        self.assertEqual((result_repository.calls, payout_repository.calls), ([], []))

    def test_race_result_cutoff_screening_includes_before_and_at_but_hides_after(self) -> None:
        race = race_input()
        strategy = strategy_identity()
        values = (bet(race, strategy),)
        for offset, included in ((-1, True), (0, True), (1, False)):
            result = persisted_result(observed_at=CUTOFF + timedelta(seconds=offset))
            source, _, result_repository, payout_repository = self.make(
                bets=values,
                race_result=result,
                publications={"単勝": None},
            )
            data = source.load_settlement_data(race_input=race, strategy_identity=strategy)
            if included:
                self.assertIs(data.race_result, result)
            else:
                self.assertIsNone(data.race_result)
            self.assertEqual(result_repository.calls, [race.race_id])
            self.assertEqual(len(payout_repository.calls), 1)

    def test_race_result_invalid_wrong_race_and_exception_fail_closed(self) -> None:
        race = race_input()
        strategy = strategy_identity()
        values = (bet(race, strategy),)
        cases = (
            (object(), "race result repository returned an invalid type"),
            (persisted_result(race_id=102), "race result repository returned a different race"),
        )
        for response, reason in cases:
            with self.subTest(reason=reason):
                source, _, result_repository, payout_repository = self.make(
                    bets=values,
                    race_result=response,
                )
                with self.assertRaises(SimulationValidationError) as caught:
                    source.load_settlement_data(race_input=race, strategy_identity=strategy)
                self.assert_error(caught.exception, identifier="race_result_repository", reason=reason)
                self.assertEqual(result_repository.calls, [race.race_id])
                self.assertEqual(payout_repository.calls, [])

        error = RepositoryDataIntegrityError("bad result")
        source, _, result_repository, payout_repository = self.make(bets=values, race_result=error)
        with self.assertRaises(RepositoryDataIntegrityError) as caught:
            source.load_settlement_data(race_input=race, strategy_identity=strategy)
        self.assertIs(caught.exception, error)
        self.assertEqual(result_repository.calls, [race.race_id])
        self.assertEqual(payout_repository.calls, [])

    def test_payout_lookup_is_bounded_once_per_type_in_first_occurrence_order(self) -> None:
        race = race_input()
        strategy = strategy_identity()
        values = (
            bet(race, strategy, bet_type="単勝", selection=(1,), rank=0),
            bet(race, strategy, bet_type="ワイド", selection=(1, 2), rank=1),
            bet(race, strategy, bet_type="単勝", selection=(2,), rank=2),
            bet(race, strategy, bet_type="馬連", selection=(1, 3), rank=3),
        )
        responses = {
            "単勝": publication(bet_type="単勝"),
            "ワイド": publication(bet_type="ワイド"),
            "馬連": publication(bet_type="馬連"),
        }
        source, _, result_repository, payout_repository = self.make(
            bets=values,
            race_result=persisted_result(),
            publications=responses,
        )
        data = source.load_settlement_data(race_input=race, strategy_identity=strategy)
        self.assertEqual(result_repository.calls, [race.race_id])
        self.assertEqual([call["bet_type"] for call in payout_repository.calls], ["単勝", "ワイド", "馬連"])
        for call in payout_repository.calls:
            self.assertEqual(call["race_id"], race.race_id)
            self.assertIs(call["observed_at_lte"], CUTOFF)
            self.assertIs(call["require_complete"], False)
        self.assertEqual(tuple(data.payout_publications_by_bet_type), ("単勝", "ワイド", "馬連"))
        for bet_type, value in responses.items():
            self.assertIs(data.payout_publications_by_bet_type[bet_type], value)

    def test_payout_cutoff_accepts_before_and_at_and_rejects_after(self) -> None:
        race = race_input()
        strategy = strategy_identity()
        values = (bet(race, strategy),)
        for offset in (-1, 0):
            value = publication(observed_at=CUTOFF + timedelta(seconds=offset))
            source, _, _, payout_repository = self.make(
                bets=values,
                race_result=None,
                publications={"単勝": value},
            )
            data = source.load_settlement_data(race_input=race, strategy_identity=strategy)
            self.assertIs(data.payout_publications_by_bet_type["単勝"], value)
            self.assertIs(payout_repository.calls[0]["observed_at_lte"], CUTOFF)

        after = publication(observed_at=CUTOFF + timedelta(seconds=1))
        source, _, _, payout_repository = self.make(
            bets=values,
            race_result=None,
            publications={"単勝": after},
        )
        with self.assertRaises(SimulationValidationError) as caught:
            source.load_settlement_data(race_input=race, strategy_identity=strategy)
        self.assert_error(
            caught.exception,
            identifier="payout_repository",
            reason="payout publication observed_at is after settlement cutoff",
        )
        self.assertEqual(len(payout_repository.calls), 1)

    def test_latest_incomplete_and_none_are_omitted_without_fallback(self) -> None:
        race = race_input()
        strategy = strategy_identity()
        values = (
            bet(race, strategy, bet_type="単勝", rank=0),
            bet(race, strategy, bet_type="ワイド", selection=(1, 2), rank=1),
        )
        incomplete = publication(bet_type="単勝", complete=False)
        source, _, _, payout_repository = self.make(
            bets=values,
            race_result=persisted_result(),
            publications={"単勝": incomplete, "ワイド": None},
        )
        data = source.load_settlement_data(race_input=race, strategy_identity=strategy)
        self.assertEqual(dict(data.payout_publications_by_bet_type), {})
        self.assertEqual(len(payout_repository.calls), 2)
        self.assertTrue(all(call["require_complete"] is False for call in payout_repository.calls))

    def test_payout_invalid_wrong_race_wrong_type_and_exception_fail_closed(self) -> None:
        race = race_input()
        strategy = strategy_identity()
        values = (bet(race, strategy),)
        cases = (
            (object(), "payout repository returned an invalid type"),
            (publication(race_id=102), "payout repository returned a different race"),
            (publication(bet_type="ワイド"), "payout repository returned a different bet type"),
        )
        for response, reason in cases:
            with self.subTest(reason=reason):
                source, _, _, payout_repository = self.make(
                    bets=values,
                    race_result=None,
                    publications={"単勝": response},
                )
                with self.assertRaises(SimulationValidationError) as caught:
                    source.load_settlement_data(race_input=race, strategy_identity=strategy)
                self.assert_error(caught.exception, identifier="payout_repository", reason=reason)
                self.assertEqual(len(payout_repository.calls), 1)

        error = RepositoryDataIntegrityError("bad payout")
        source, _, _, payout_repository = self.make(
            bets=values,
            race_result=None,
            publications={"単勝": error},
        )
        with self.assertRaises(RepositoryDataIntegrityError) as caught:
            source.load_settlement_data(race_input=race, strategy_identity=strategy)
        self.assertIs(caught.exception, error)
        self.assertEqual(len(payout_repository.calls), 1)

    def test_equal_inputs_and_eligible_state_produce_equal_data_after_caller_mapping_mutation(self) -> None:
        race = race_input()
        strategy = strategy_identity()
        values = (bet(race, strategy),)
        result = persisted_result()
        payout = publication()
        caller_cutoffs = {race.race_id: CUTOFF}
        first, *_ = self.make(
            bets=values,
            race_result=result,
            publications={"単勝": payout},
            cutoffs=caller_cutoffs,
        )
        caller_cutoffs[race.race_id] = CUTOFF + timedelta(days=30)
        second, *_ = self.make(
            bets=values,
            race_result=result,
            publications={"単勝": payout},
            cutoffs={race.race_id: CUTOFF},
        )
        first_data = first.load_settlement_data(race_input=race, strategy_identity=strategy)
        second_data = second.load_settlement_data(race_input=race, strategy_identity=strategy)
        self.assertEqual(first_data, second_data)
        self.assertIs(first._settlement_cutoffs_by_race_id[race.race_id], CUTOFF)

    def test_static_ownership_and_bounded_lookup_contract(self) -> None:
        source = inspect.getsource(source_module)
        tree = ast.parse(source)
        forbidden = (
            "PersistedSimulationBetSource",
            "SimulationRunContext",
            "SimulationBetPlanIdentity",
            "SimulationBetPlanSnapshotSource",
            "HistoricalInputSnapshot",
            "PredictionPipeline",
            "RuleBasedBetStrategy",
            "FixedStakeBetAllocator",
            "ExactRaceEntrySelectionResolver",
            "SimulationBetPlanBuilder",
            "PersistedRaceSimulationExecutor",
            "Simulator",
            "ProviderBackedRaceSimulationExecutor",
            "ProviderContext",
            "RawRaceResult",
            "RawPayoutPublication",
            "sqlite3",
            "SQLite",
            "requests",
            "httpx",
            "urllib",
            "datetime.now",
            "date.today",
            "time.time",
            "random",
            "os.environ",
            "observed_at_lte=None",
        )
        for value in forbidden:
            self.assertNotIn(value, source)
        self.assertFalse(any(isinstance(node, ast.Try) for node in ast.walk(tree)))
        self.assertEqual(source.count("dict(settlement_cutoffs_by_race_id)"), 1)
        self.assertFalse(
            any(
                isinstance(node, ast.FunctionDef)
                and node.name.startswith(("save", "write", "commit", "rollback"))
                for node in ast.walk(tree)
            )
        )


if __name__ == "__main__":
    unittest.main()
