"""Tests for the repository-backed persisted settlement Source."""

from __future__ import annotations

import ast
from datetime import UTC, date, datetime
import inspect
from typing import get_type_hints
import unittest
from unittest.mock import patch

import scripts.simulation as simulation_package
import scripts.simulation.repository_backed_persisted_settlement_source as source_module
from scripts.prediction.bet_strategy import StrategyConfig
from scripts.prediction.prediction_pipeline import RacePredictionInput
from scripts.prediction.track_engine import RaceTrackConditions
from scripts.simulation.bet_source import SimulationBetSource
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
from scripts.simulation.repository_backed_persisted_settlement_source import (
    RepositoryBackedPersistedRaceSettlementSource,
)
from scripts.simulation.repositories.errors import (
    RepositoryConflictError,
    RepositoryDataIntegrityError,
    RepositoryValidationError,
)
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


CUTOFF = datetime(2026, 7, 28, 9, 0, tzinfo=UTC)


def strategy_identity() -> StrategyIdentity:
    return build_strategy_identity("RepositorySettlement", StrategyConfig())


def race_input(race_id: int = 101) -> SimulationRaceInput:
    pipeline = RacePredictionInput(
        {1: [], 2: []},
        {1: "Jockey A", 2: "Jockey B"},
        RaceTrackConditions("Tokyo", 1600, "turf", "firm"),
        {1: 2.0, 2: 4.0},
        2,
        race_id,
    )
    audit = InputSnapshotAudit(
        "dataset",
        "source",
        CUTOFF,
        (
            InputAuditEntry("entry", "entry/1", "source", "entry/1", 1, observed_at=CUTOFF),
            InputAuditEntry("entry", "entry/2", "source", "entry/2", 2, observed_at=CUTOFF),
            InputAuditEntry("odds", "odds/1", "source", "odds/1", 1, observed_at=CUTOFF),
            InputAuditEntry("odds", "odds/2", "source", "odds/2", 2, observed_at=CUTOFF),
            InputAuditEntry("jockey", "jockey/1", "source", "jockey/1", 1, observed_at=CUTOFF),
            InputAuditEntry("jockey", "jockey/2", "source", "jockey/2", 2, observed_at=CUTOFF),
            InputAuditEntry("track", "track", "source", "track", None, observed_at=CUTOFF),
            InputAuditEntry("past_race", "past_race/1/none", "source", "past_race/1/none", 1, observed_at=CUTOFF),
            InputAuditEntry("past_race", "past_race/2/none", "source", "past_race/2/none", 2, observed_at=CUTOFF),
        ),
        True,
    )
    return SimulationRaceInput(race_id, date(2026, 7, 28), CUTOFF, CUTOFF, pipeline, audit)


def bet(
    race: SimulationRaceInput,
    strategy: StrategyIdentity,
    *,
    bet_type: str = "\u5358\u52dd",
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


def persisted_result(race_id: int = 101) -> PersistedRaceResult:
    return PersistedRaceResult(
        race_id=race_id,
        result_status=RaceResultStatus.COMPLETE,
        finalized_at=CUTOFF,
        observed_at=CUTOFF,
        source="official",
        entries=(PersistedRaceResultEntry(1, 1, 1, RaceResultEntryStatus.CONFIRMED),),
    )


def publication(
    *,
    race_id: int = 101,
    bet_type: str = "\u5358\u52dd",
    complete: bool = True,
) -> PayoutPublication:
    selection = (1, 2) if bet_type == "\u99ac\u9023" else (1,)
    return PayoutPublication(
        race_id=race_id,
        bet_type=bet_type,
        finalized_at=CUTOFF if complete else None,
        observed_at=CUTOFF,
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
    def __init__(self, responses: dict[str, object]) -> None:
        self.responses = responses
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
        response = self.responses[bet_type]
        if isinstance(response, BaseException):
            raise response
        return response  # type: ignore[return-value]


class MissingMethod:
    pass


class NonCallableBetSource:
    load_bets = None


class RepositoryBackedPersistedSettlementSourceTests(unittest.TestCase):
    def make(
        self,
        *,
        bets: object = (),
        race_result: object = None,
        publications: dict[str, object] | None = None,
    ) -> tuple[
        RepositoryBackedPersistedRaceSettlementSource,
        RecordingBetSource,
        RecordingRaceResultRepository,
        RecordingPayoutRepository,
    ]:
        bet_source = RecordingBetSource(bets)
        race_repository = RecordingRaceResultRepository(race_result)
        payout_repository = RecordingPayoutRepository({} if publications is None else publications)
        return (
            RepositoryBackedPersistedRaceSettlementSource(
                bet_source=bet_source,
                race_result_repository=race_repository,
                payout_repository=payout_repository,
            ),
            bet_source,
            race_repository,
            payout_repository,
        )

    def test_constructor_is_keyword_only_and_has_formal_hints(self) -> None:
        signature = inspect.signature(RepositoryBackedPersistedRaceSettlementSource)
        self.assertEqual(tuple(signature.parameters), ("bet_source", "race_result_repository", "payout_repository"))
        self.assertTrue(all(item.kind is inspect.Parameter.KEYWORD_ONLY for item in signature.parameters.values()))
        hints = get_type_hints(RepositoryBackedPersistedRaceSettlementSource.__init__)
        self.assertIs(hints["bet_source"], SimulationBetSource)
        self.assertIs(hints["race_result_repository"], RaceResultRepository)
        self.assertIs(hints["payout_repository"], PayoutRepository)

    def test_load_signature_matches_persisted_settlement_source_protocol(self) -> None:
        self.assertEqual(
            inspect.signature(RepositoryBackedPersistedRaceSettlementSource.load_settlement_data),
            inspect.signature(PersistedRaceSettlementSource.load_settlement_data),
        )
        self.assertEqual(
            get_type_hints(RepositoryBackedPersistedRaceSettlementSource.load_settlement_data),
            get_type_hints(PersistedRaceSettlementSource.load_settlement_data),
        )

    def test_constructor_retains_dependency_identity_and_makes_no_calls(self) -> None:
        source, bet_source, race_repository, payout_repository = self.make()
        self.assertIs(source._bet_source, bet_source)
        self.assertIs(source._race_result_repository, race_repository)
        self.assertIs(source._payout_repository, payout_repository)
        self.assertEqual((bet_source.calls, race_repository.calls, payout_repository.calls), ([], [], []))

    def test_bet_source_accessor_preserves_identity_and_does_not_call_collaborators(self) -> None:
        source, bet_source, race_repository, payout_repository = self.make()

        descriptor = RepositoryBackedPersistedRaceSettlementSource.bet_source
        self.assertIsInstance(descriptor, property)
        self.assertIsNotNone(descriptor.fget)
        self.assertIs(get_type_hints(descriptor.fget)["return"], SimulationBetSource)
        self.assertIs(source.bet_source, bet_source)
        self.assertIs(source.bet_source, bet_source)
        self.assertIsNone(descriptor.fset)
        with self.assertRaises(AttributeError):
            source.bet_source = bet_source
        self.assertEqual((bet_source.calls, race_repository.calls, payout_repository.calls), ([], [], []))

    def test_constructor_rejects_missing_or_non_callable_methods(self) -> None:
        valid_bet = RecordingBetSource(())
        valid_race = RecordingRaceResultRepository(None)
        valid_payout = RecordingPayoutRepository({})
        cases = (
            (MissingMethod(), valid_race, valid_payout),
            (NonCallableBetSource(), valid_race, valid_payout),
            (valid_bet, MissingMethod(), valid_payout),
            (valid_bet, valid_race, MissingMethod()),
        )
        for bet_source, race_repository, payout_repository in cases:
            with self.subTest(value_types=tuple(type(item).__name__ for item in (bet_source, race_repository, payout_repository))):
                with self.assertRaises(ValueError):
                    RepositoryBackedPersistedRaceSettlementSource(
                        bet_source=bet_source,  # type: ignore[arg-type]
                        race_result_repository=race_repository,  # type: ignore[arg-type]
                        payout_repository=payout_repository,  # type: ignore[arg-type]
                    )

    def test_invalid_direct_input_makes_zero_dependency_calls(self) -> None:
        source, bet_source, race_repository, payout_repository = self.make()
        for invalid_race, invalid_strategy in ((None, strategy_identity()), (race_input(), None), ("race", "strategy")):
            with self.subTest(race=type(invalid_race).__name__, strategy=type(invalid_strategy).__name__), self.assertRaises(ValueError):
                source.load_settlement_data(
                    race_input=invalid_race,  # type: ignore[arg-type]
                    strategy_identity=invalid_strategy,  # type: ignore[arg-type]
                )
        self.assertEqual((bet_source.calls, race_repository.calls, payout_repository.calls), ([], [], []))

    def test_bet_source_is_called_once_with_original_objects(self) -> None:
        race = race_input()
        strategy = strategy_identity()
        values = (bet(race, strategy),)
        source, bet_source, race_repository, payout_repository = self.make(
            bets=values,
            race_result=persisted_result(),
            publications={"\u5358\u52dd": publication()},
        )
        data = source.load_settlement_data(race_input=race, strategy_identity=strategy)
        self.assertIs(bet_source.calls[0][0], race)
        self.assertIs(bet_source.calls[0][1], strategy)
        self.assertEqual(len(bet_source.calls), 1)
        self.assertEqual(race_repository.calls, [race.race_id])
        self.assertEqual(len(payout_repository.calls), 1)
        self.assertIs(data.bets, values)
        self.assertIs(data.bets[0], values[0])

    def test_malformed_bet_source_responses_fail_closed_before_repositories(self) -> None:
        race = race_input()
        strategy = strategy_identity()
        other_strategy = build_strategy_identity("Other", StrategyConfig())
        valid = bet(race, strategy)
        malformed = (
            [valid],
            (object(),),
            (bet(race_input(102), strategy),),
            (bet(race, other_strategy),),
            (valid, bet(race, strategy, rank=1)),
        )
        for response in malformed:
            with self.subTest(response_type=type(response).__name__):
                source, _, race_repository, payout_repository = self.make(bets=response)
                with self.assertRaises(SimulationValidationError) as caught:
                    source.load_settlement_data(race_input=race, strategy_identity=strategy)
                self.assertEqual(caught.exception.input_identifier, "simulation_bet_source")
                self.assertEqual((race_repository.calls, payout_repository.calls), ([], []))

    def test_no_bet_returns_bundle_without_repository_calls(self) -> None:
        race = race_input()
        strategy = strategy_identity()
        source, bet_source, race_repository, payout_repository = self.make(bets=())
        data = source.load_settlement_data(race_input=race, strategy_identity=strategy)
        self.assertEqual(data.bets, ())
        self.assertIsNone(data.race_result)
        self.assertEqual(dict(data.payout_publications_by_bet_type), {})
        self.assertEqual(len(bet_source.calls), 1)
        self.assertEqual((race_repository.calls, payout_repository.calls), ([], []))

    def test_race_result_none_is_retained_as_a_fact(self) -> None:
        race = race_input()
        strategy = strategy_identity()
        source, _, race_repository, payout_repository = self.make(
            bets=(bet(race, strategy),),
            race_result=None,
            publications={"\u5358\u52dd": publication()},
        )
        data = source.load_settlement_data(race_input=race, strategy_identity=strategy)
        self.assertIsNone(data.race_result)
        self.assertEqual(race_repository.calls, [race.race_id])
        self.assertEqual(payout_repository.calls[0]["require_complete"], False)

    def test_rejects_invalid_or_wrong_race_result_response(self) -> None:
        race = race_input()
        strategy = strategy_identity()
        for response in (object(), persisted_result(102)):
            with self.subTest(response_type=type(response).__name__):
                source, _, _, payout_repository = self.make(bets=(bet(race, strategy),), race_result=response)
                with self.assertRaises(SimulationValidationError) as caught:
                    source.load_settlement_data(race_input=race, strategy_identity=strategy)
                self.assertEqual(caught.exception.input_identifier, "race_result_repository")
                self.assertEqual(payout_repository.calls, [])

    def test_payout_queries_use_first_occurrence_distinct_type_order(self) -> None:
        race = race_input()
        strategy = strategy_identity()
        values = (
            bet(race, strategy, bet_type="\u99ac\u9023", selection=(1, 2), rank=5),
            bet(race, strategy, bet_type="\u5358\u52dd", rank=1),
            bet(race, strategy, bet_type="\u99ac\u9023", selection=(1, 2), rank=2),
        )
        # The final item deliberately duplicates the plan identity, so use two distinct types only.
        values = values[:2]
        source, _, _, payout_repository = self.make(
            bets=values,
            race_result=persisted_result(),
            publications={"\u99ac\u9023": publication(bet_type="\u99ac\u9023"), "\u5358\u52dd": publication()},
        )
        data = source.load_settlement_data(race_input=race, strategy_identity=strategy)
        self.assertEqual([item["bet_type"] for item in payout_repository.calls], ["\u99ac\u9023", "\u5358\u52dd"])
        self.assertTrue(all(item["observed_at_lte"] is None and item["require_complete"] is False for item in payout_repository.calls))
        self.assertEqual(tuple(data.payout_publications_by_bet_type), ("\u99ac\u9023", "\u5358\u52dd"))

    def test_none_and_incomplete_payouts_are_omitted_without_fallback(self) -> None:
        race = race_input()
        strategy = strategy_identity()
        values = (
            bet(race, strategy, bet_type="\u5358\u52dd"),
            bet(race, strategy, bet_type="\u99ac\u9023", selection=(1, 2), rank=1),
        )
        source, _, _, payout_repository = self.make(
            bets=values,
            race_result=persisted_result(),
            publications={"\u5358\u52dd": publication(complete=False), "\u99ac\u9023": None},
        )
        data = source.load_settlement_data(race_input=race, strategy_identity=strategy)
        self.assertEqual(dict(data.payout_publications_by_bet_type), {})
        self.assertEqual(len(payout_repository.calls), 2)

    def test_rejects_invalid_wrong_race_or_wrong_type_payout_response(self) -> None:
        race = race_input()
        strategy = strategy_identity()
        cases = (object(), publication(race_id=102), publication(bet_type="\u99ac\u9023"))
        for response in cases:
            with self.subTest(response_type=type(response).__name__):
                source, _, _, payout_repository = self.make(
                    bets=(bet(race, strategy),),
                    race_result=persisted_result(),
                    publications={"\u5358\u52dd": response},
                )
                with self.assertRaises(SimulationValidationError) as caught:
                    source.load_settlement_data(race_input=race, strategy_identity=strategy)
                self.assertEqual(caught.exception.input_identifier, "payout_repository")
                self.assertEqual(len(payout_repository.calls), 1)

    def test_dependency_exceptions_propagate_as_same_object(self) -> None:
        race = race_input()
        strategy = strategy_identity()
        cases = (
            (RepositoryValidationError("bet"), "bet"),
            (RepositoryDataIntegrityError("result"), "result"),
            (RepositoryConflictError("payout"), "payout"),
            (RuntimeError("unexpected"), "payout"),
        )
        for error, origin in cases:
            with self.subTest(origin=origin, error_type=type(error).__name__):
                if origin == "bet":
                    source, _, _, _ = self.make(bets=error)
                elif origin == "result":
                    source, _, _, _ = self.make(bets=(bet(race, strategy),), race_result=error)
                else:
                    source, _, _, _ = self.make(
                        bets=(bet(race, strategy),),
                        race_result=persisted_result(),
                        publications={"\u5358\u52dd": error},
                    )
                with self.assertRaises(type(error)) as caught:
                    source.load_settlement_data(race_input=race, strategy_identity=strategy)
                self.assertIs(caught.exception, error)

    def test_bundle_constructor_exception_is_not_wrapped(self) -> None:
        race = race_input()
        strategy = strategy_identity()
        error = SimulationValidationError(race.race_id, "bundle", "failure")
        source, _, _, _ = self.make(
            bets=(bet(race, strategy),),
            race_result=persisted_result(),
            publications={"\u5358\u52dd": publication()},
        )
        with patch.object(source_module, "PersistedRaceSettlementData", side_effect=error):
            with self.assertRaises(SimulationValidationError) as caught:
                source.load_settlement_data(race_input=race, strategy_identity=strategy)
        self.assertIs(caught.exception, error)

    def test_module_has_no_runtime_protocol_database_or_composition_dependencies(self) -> None:
        source = inspect.getsource(source_module)
        for forbidden in (
            "sqlite3",
            "SQLite",
            "Provider",
            "Raw",
            "SimulationBetPlanBuilder",
            "RepositoryBackedRaceEntrySelectionResolver",
            "PersistedRaceSimulationExecutor",
            "Simulator",
            "datetime.now",
            "requests",
            "httpx",
            "cache",
            "retry",
            "target_race_count",
        ):
            self.assertNotIn(forbidden, source)
        tree = ast.parse(source)
        self.assertFalse(any(isinstance(node, ast.Try) for node in ast.walk(tree)))
        self.assertNotIn("isinstance(bet_source, SimulationBetSource)", source)
        self.assertFalse(hasattr(simulation_package, "RepositoryBackedPersistedRaceSettlementSource"))


if __name__ == "__main__":
    unittest.main()
