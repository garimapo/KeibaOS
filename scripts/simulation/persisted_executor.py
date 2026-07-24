"""Persisted-data implementation of the one-race simulation executor contract."""

from __future__ import annotations

from datetime import datetime
from typing import NoReturn

from .models import SimulationRaceInput, SimulationResult, StrategyIdentity
from .persisted_settlement import PersistedRaceSettlementData, PersistedRaceSettlementSource
from .repositories.interfaces import PayoutPublication, PayoutStatus, PersistedRaceResult, RaceResultStatus
from .simulator import _build_simulation_result_for_race
from .validation import SimulationValidationError


def _invalid(race_id: object, reason: str) -> NoReturn:
    """Raise the established simulation-boundary exception consistently."""
    diagnostic_race_id = race_id if isinstance(race_id, int) and not isinstance(race_id, bool) else 0
    raise SimulationValidationError(diagnostic_race_id, "persisted_race_simulation_executor", reason)


class PersistedRaceSimulationExecutor:
    """Build one final result from already-persisted settlement values."""

    __slots__ = ("_strategy_identity", "_settlement_source")

    def __init__(
        self,
        *,
        strategy_identity: StrategyIdentity,
        settlement_source: PersistedRaceSettlementSource,
    ) -> None:
        if not isinstance(strategy_identity, StrategyIdentity):
            _invalid(0, "strategy_identity must be a StrategyIdentity")
        if not callable(getattr(settlement_source, "load_settlement_data", None)):
            _invalid(0, "settlement_source must provide callable load_settlement_data")
        self._strategy_identity = strategy_identity
        self._settlement_source = settlement_source

    @property
    def strategy_identity(self) -> StrategyIdentity:
        return self._strategy_identity

    @property
    def settlement_source(self) -> PersistedRaceSettlementSource:
        return self._settlement_source

    def __call__(
        self,
        *,
        race_input: SimulationRaceInput,
    ) -> SimulationResult:
        if not isinstance(race_input, SimulationRaceInput):
            _invalid(0, "race_input must be a SimulationRaceInput")

        settlement_data = self._settlement_source.load_settlement_data(
            race_input=race_input,
            strategy_identity=self._strategy_identity,
        )
        self._validate_settlement_data(settlement_data, race_input)

        if not settlement_data.bets:
            return self._build_result(
                race_input=race_input,
                settlement_data=settlement_data,
                publications_by_bet_type={},
                settled_at=None,
                race_result_status=None,
                payout_statuses=(),
                missing_payout_bet_types=(),
                missing_race_result=False,
            )

        persisted_result = settlement_data.race_result
        if persisted_result is None:
            return self._build_result(
                race_input=race_input,
                settlement_data=settlement_data,
                publications_by_bet_type={},
                settled_at=None,
                race_result_status=None,
                payout_statuses=(),
                missing_payout_bet_types=(),
                missing_race_result=True,
            )

        if persisted_result.result_status is not RaceResultStatus.COMPLETE:
            return self._build_result(
                race_input=race_input,
                settlement_data=settlement_data,
                publications_by_bet_type={},
                settled_at=None,
                race_result_status=persisted_result.result_status,
                payout_statuses=(),
                missing_payout_bet_types=(),
                missing_race_result=False,
            )

        required_bet_types = tuple(dict.fromkeys(bet.bet_type for bet in settlement_data.bets))
        missing_payout_bet_types = tuple(
            bet_type
            for bet_type in required_bet_types
            if bet_type not in settlement_data.payout_publications_by_bet_type
        )
        if missing_payout_bet_types:
            return self._build_result(
                race_input=race_input,
                settlement_data=settlement_data,
                publications_by_bet_type={},
                settled_at=None,
                race_result_status=persisted_result.result_status,
                payout_statuses=(),
                missing_payout_bet_types=missing_payout_bet_types,
                missing_race_result=False,
            )

        publications: dict[str, PayoutPublication] = {}
        payout_statuses: list[PayoutStatus] = []
        for bet_type in required_bet_types:
            publication = settlement_data.payout_publications_by_bet_type[bet_type]
            publications[bet_type] = publication
            payout_statuses.extend(record.payout_status for record in publication.entries)

        settled_at = self._settled_at(persisted_result, tuple(publications.values()), race_input.race_id)
        return self._build_result(
            race_input=race_input,
            settlement_data=settlement_data,
            publications_by_bet_type=publications,
            settled_at=settled_at,
            race_result_status=persisted_result.result_status,
            payout_statuses=tuple(payout_statuses),
            missing_payout_bet_types=(),
            missing_race_result=False,
        )

    def _validate_settlement_data(
        self,
        settlement_data: object,
        race_input: SimulationRaceInput,
    ) -> None:
        if not isinstance(settlement_data, PersistedRaceSettlementData):
            _invalid(race_input.race_id, "settlement_source must return PersistedRaceSettlementData")
        if settlement_data.race_id != race_input.race_id:
            _invalid(race_input.race_id, "settlement_data.race_id must match race_input.race_id")
        if any(bet.strategy_id != self._strategy_identity.strategy_id for bet in settlement_data.bets):
            _invalid(race_input.race_id, "settlement_data bets must match strategy_identity.strategy_id")

    @staticmethod
    def _settled_at(
        persisted_result: PersistedRaceResult,
        publications: tuple[PayoutPublication, ...],
        race_id: int,
    ) -> datetime:
        finalized_at = (persisted_result.finalized_at, *(publication.finalized_at for publication in publications))
        if any(not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None for value in finalized_at):
            _invalid(race_id, "complete settlement values require finalized_at")
        return max(finalized_at)

    def _build_result(
        self,
        *,
        race_input: SimulationRaceInput,
        settlement_data: PersistedRaceSettlementData,
        publications_by_bet_type: dict[str, PayoutPublication],
        settled_at: datetime | None,
        race_result_status: RaceResultStatus | None,
        payout_statuses: tuple[PayoutStatus, ...],
        missing_payout_bet_types: tuple[str, ...],
        missing_race_result: bool,
    ) -> SimulationResult:
        return _build_simulation_result_for_race(
            race_id=race_input.race_id,
            strategy_id=self._strategy_identity.strategy_id,
            bets=settlement_data.bets,
            publications_by_bet_type=publications_by_bet_type,
            settled_at=settled_at,
            completeness_statuses=(),
            race_result_status=race_result_status,
            payout_statuses=payout_statuses,
            missing_payout_bet_types=missing_payout_bet_types,
            missing_race_result=missing_race_result,
            error_reason=None,
        )
