"""Concrete repository-backed Source for one persisted race settlement."""

from __future__ import annotations

from .bet_source import SimulationBetSource
from .models import SimulationBet, SimulationRaceInput, StrategyIdentity
from .persisted_settlement import PersistedRaceSettlementData, PersistedRaceSettlementSource
from .repositories.interfaces import (
    PayoutPublication,
    PayoutRepository,
    PersistedRaceResult,
    RaceResultRepository,
)
from .validation import SimulationValidationError


class RepositoryBackedPersistedRaceSettlementSource:
    """Load persisted bets and official settlement facts for one race."""

    __slots__ = ("_bet_source", "_race_result_repository", "_payout_repository")

    def __init__(
        self,
        *,
        bet_source: SimulationBetSource,
        race_result_repository: RaceResultRepository,
        payout_repository: PayoutRepository,
    ) -> None:
        if not callable(getattr(bet_source, "load_bets", None)):
            raise ValueError("bet_source must provide a callable load_bets method")
        if not callable(getattr(race_result_repository, "get_race_result", None)):
            raise ValueError("race_result_repository must provide a callable get_race_result method")
        if not callable(getattr(payout_repository, "get_latest_payout_publication", None)):
            raise ValueError(
                "payout_repository must provide a callable get_latest_payout_publication method"
            )
        self._bet_source = bet_source
        self._race_result_repository = race_result_repository
        self._payout_repository = payout_repository

    @property
    def bet_source(self) -> SimulationBetSource:
        """Return the exact bet source supplied at construction."""
        return self._bet_source

    def load_settlement_data(
        self,
        *,
        race_input: SimulationRaceInput,
        strategy_identity: StrategyIdentity,
    ) -> PersistedRaceSettlementData:
        if not isinstance(race_input, SimulationRaceInput):
            raise ValueError("race_input must be a SimulationRaceInput")
        if not isinstance(strategy_identity, StrategyIdentity):
            raise ValueError("strategy_identity must be a StrategyIdentity")

        bets = self._bet_source.load_bets(
            race_input=race_input,
            strategy_identity=strategy_identity,
        )
        self._validate_bets(bets, race_input, strategy_identity)
        if not bets:
            return PersistedRaceSettlementData(
                race_id=race_input.race_id,
                bets=bets,
                race_result=None,
                payout_publications_by_bet_type={},
            )

        race_result = self._race_result_repository.get_race_result(race_input.race_id)
        self._validate_race_result(race_result, race_input)

        publications: dict[str, PayoutPublication] = {}
        for bet_type in tuple(dict.fromkeys(bet.bet_type for bet in bets)):
            publication = self._payout_repository.get_latest_payout_publication(
                race_id=race_input.race_id,
                bet_type=bet_type,
                observed_at_lte=None,
                require_complete=False,
            )
            self._validate_payout_publication(publication, race_input, bet_type)
            if publication is not None and publication.is_complete:
                publications[bet_type] = publication

        return PersistedRaceSettlementData(
            race_id=race_input.race_id,
            bets=bets,
            race_result=race_result,
            payout_publications_by_bet_type=publications,
        )

    @staticmethod
    def _validate_bets(
        bets: object,
        race_input: SimulationRaceInput,
        strategy_identity: StrategyIdentity,
    ) -> None:
        if type(bets) is not tuple:
            RepositoryBackedPersistedRaceSettlementSource._invalid(
                race_input,
                "bet source must return a tuple of SimulationBet values",
            )
        if not all(isinstance(bet, SimulationBet) for bet in bets):
            RepositoryBackedPersistedRaceSettlementSource._invalid(
                race_input,
                "bet source must return only SimulationBet values",
            )
        if any(bet.race_id != race_input.race_id for bet in bets):
            RepositoryBackedPersistedRaceSettlementSource._invalid(
                race_input,
                "bet source bets must match race_input.race_id",
            )
        if any(bet.strategy_id != strategy_identity.strategy_id for bet in bets):
            RepositoryBackedPersistedRaceSettlementSource._invalid(
                race_input,
                "bet source bets must match strategy_identity.strategy_id",
            )
        identities = tuple((bet.bet_type, bet.race_entry_ids) for bet in bets)
        if len(set(identities)) != len(identities):
            RepositoryBackedPersistedRaceSettlementSource._invalid(
                race_input,
                "bet source bets must have unique bet identities",
            )

    @staticmethod
    def _validate_race_result(
        race_result: object,
        race_input: SimulationRaceInput,
    ) -> None:
        if race_result is None:
            return
        if not isinstance(race_result, PersistedRaceResult):
            raise SimulationValidationError(
                race_input.race_id,
                "race_result_repository",
                "race result repository returned an invalid type",
            )
        if race_result.race_id != race_input.race_id:
            raise SimulationValidationError(
                race_input.race_id,
                "race_result_repository",
                "race result repository returned a different race",
            )

    @staticmethod
    def _validate_payout_publication(
        publication: object,
        race_input: SimulationRaceInput,
        bet_type: str,
    ) -> None:
        if publication is None:
            return
        if not isinstance(publication, PayoutPublication):
            raise SimulationValidationError(
                race_input.race_id,
                "payout_repository",
                "payout repository returned an invalid type",
            )
        if publication.race_id != race_input.race_id:
            raise SimulationValidationError(
                race_input.race_id,
                "payout_repository",
                "payout repository returned a different race",
            )
        if publication.bet_type != bet_type:
            raise SimulationValidationError(
                race_input.race_id,
                "payout_repository",
                "payout repository returned a different bet type",
            )

    @staticmethod
    def _invalid(race_input: SimulationRaceInput, reason: str) -> None:
        raise SimulationValidationError(race_input.race_id, "simulation_bet_source", reason)
