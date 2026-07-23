"""Provider-backed implementation of the one-race simulation executor contract."""

from __future__ import annotations

from datetime import datetime
from typing import NoReturn

from .models import SimulationRaceInput, SimulationResult, StrategyIdentity
from .providers.interfaces import PayoutProvider, ProviderBuildResult, RaceResultProvider
from .providers.models import CompletenessResult, CompletenessStatus
from .repositories.interfaces import PayoutPublication, PayoutStatus, PersistedRaceResult, RaceResultStatus
from .settlement import RaceSettlementData, RaceSettlementSource
from .simulator import _build_simulation_result_for_race
from .validation import SimulationValidationError


def _invalid(race_id: object, reason: str) -> NoReturn:
    """Raise the established input-boundary exception for adapter validation."""
    diagnostic_race_id = race_id if isinstance(race_id, int) and not isinstance(race_id, bool) else 0
    raise SimulationValidationError(diagnostic_race_id, "provider_backed_executor", reason)


class ProviderBackedRaceSimulationExecutor:
    """Connect one settlement source and the existing conversion Providers once."""

    __slots__ = (
        "_strategy_identity",
        "_settlement_source",
        "_race_result_provider",
        "_payout_provider",
    )

    def __init__(
        self,
        *,
        strategy_identity: StrategyIdentity,
        settlement_source: RaceSettlementSource,
        race_result_provider: RaceResultProvider,
        payout_provider: PayoutProvider,
    ) -> None:
        if not isinstance(strategy_identity, StrategyIdentity):
            _invalid(0, "strategy_identity must be a StrategyIdentity")
        if not callable(getattr(settlement_source, "load_settlement_data", None)):
            _invalid(0, "settlement_source must provide callable load_settlement_data")
        if not callable(getattr(race_result_provider, "build_race_result", None)):
            _invalid(0, "race_result_provider must provide callable build_race_result")
        if not callable(getattr(payout_provider, "build_payout_publication", None)):
            _invalid(0, "payout_provider must provide callable build_payout_publication")
        self._strategy_identity = strategy_identity
        self._settlement_source = settlement_source
        self._race_result_provider = race_result_provider
        self._payout_provider = payout_provider

    @property
    def strategy_identity(self) -> StrategyIdentity:
        return self._strategy_identity

    @property
    def settlement_source(self) -> RaceSettlementSource:
        return self._settlement_source

    @property
    def race_result_provider(self) -> RaceResultProvider:
        return self._race_result_provider

    @property
    def payout_provider(self) -> PayoutProvider:
        return self._payout_provider

    def __call__(
        self,
        *,
        race_input: SimulationRaceInput,
    ) -> SimulationResult:
        if not isinstance(race_input, SimulationRaceInput):
            _invalid(0, "race_input must be a SimulationRaceInput")

        settlement_data = self._settlement_source.load_settlement_data(race_input=race_input)
        self._validate_settlement_data(settlement_data, race_input)

        if not settlement_data.bets:
            return self._build_result(
                race_input=race_input,
                settlement_data=settlement_data,
                publications_by_bet_type={},
                settled_at=None,
                completeness_statuses=(),
                race_result_status=None,
                payout_statuses=(),
                missing_payout_bet_types=(),
                missing_race_result=False,
            )

        if settlement_data.raw_race_result is None:
            return self._build_result(
                race_input=race_input,
                settlement_data=settlement_data,
                publications_by_bet_type={},
                settled_at=None,
                completeness_statuses=(),
                race_result_status=None,
                payout_statuses=(),
                missing_payout_bet_types=(),
                missing_race_result=True,
            )

        result_output = self._race_result_provider.build_race_result(
            raw=settlement_data.raw_race_result,
            context=settlement_data.race_result_context,
            universe=settlement_data.universe,
        )
        persisted_result = self._validate_result_provider_output(result_output, race_input)
        result_completeness = result_output.completeness

        if (
            result_completeness.status is not CompletenessStatus.COMPLETE
            or persisted_result.result_status is not RaceResultStatus.COMPLETE
        ):
            return self._build_result(
                race_input=race_input,
                settlement_data=settlement_data,
                publications_by_bet_type={},
                settled_at=None,
                completeness_statuses=(result_completeness.status,),
                race_result_status=persisted_result.result_status,
                payout_statuses=(),
                missing_payout_bet_types=(),
                missing_race_result=False,
            )

        required_bet_types = tuple(dict.fromkeys(bet.bet_type for bet in settlement_data.bets))
        missing_payout_bet_types = tuple(
            bet_type
            for bet_type in required_bet_types
            if bet_type not in settlement_data.raw_payout_publications_by_bet_type
            or bet_type not in settlement_data.payout_contexts_by_bet_type
        )
        if missing_payout_bet_types:
            return self._build_result(
                race_input=race_input,
                settlement_data=settlement_data,
                publications_by_bet_type={},
                settled_at=None,
                completeness_statuses=(result_completeness.status,),
                race_result_status=persisted_result.result_status,
                payout_statuses=(),
                missing_payout_bet_types=missing_payout_bet_types,
                missing_race_result=False,
            )

        publications: dict[str, PayoutPublication] = {}
        completeness_statuses: list[CompletenessStatus] = [result_completeness.status]
        payout_statuses: list[PayoutStatus] = []
        for bet_type in required_bet_types:
            payout_output = self._payout_provider.build_payout_publication(
                raw=settlement_data.raw_payout_publications_by_bet_type[bet_type],
                context=settlement_data.payout_contexts_by_bet_type[bet_type],
                universe=settlement_data.universe,
            )
            publication = self._validate_payout_provider_output(
                payout_output,
                race_input,
                bet_type,
            )
            publications[bet_type] = publication
            completeness_statuses.append(payout_output.completeness.status)
            payout_statuses.extend(record.payout_status for record in publication.entries)
            if payout_output.completeness.status is not CompletenessStatus.COMPLETE:
                return self._build_result(
                    race_input=race_input,
                    settlement_data=settlement_data,
                    publications_by_bet_type=publications,
                    settled_at=None,
                    completeness_statuses=tuple(completeness_statuses),
                    race_result_status=persisted_result.result_status,
                    payout_statuses=tuple(payout_statuses),
                    missing_payout_bet_types=(),
                    missing_race_result=False,
                )

        settled_at = self._settled_at(persisted_result, tuple(publications.values()), race_input.race_id)
        return self._build_result(
            race_input=race_input,
            settlement_data=settlement_data,
            publications_by_bet_type=publications,
            settled_at=settled_at,
            completeness_statuses=tuple(completeness_statuses),
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
        if not isinstance(settlement_data, RaceSettlementData):
            _invalid(race_input.race_id, "settlement_source must return RaceSettlementData")
        if settlement_data.race_id != race_input.race_id:
            _invalid(race_input.race_id, "settlement_data.race_id must match race_input.race_id")
        if any(bet.strategy_id != self._strategy_identity.strategy_id for bet in settlement_data.bets):
            _invalid(race_input.race_id, "settlement_data bets must match strategy_identity.strategy_id")
        contexts = tuple(
            context
            for context in (
                settlement_data.race_result_context,
                *settlement_data.payout_contexts_by_bet_type.values(),
            )
            if context is not None
        )
        if any(context.information_cutoff != race_input.information_cutoff for context in contexts):
            _invalid(race_input.race_id, "provider context information_cutoff must match race_input")

    @staticmethod
    def _validate_result_provider_output(
        value: object,
        race_input: SimulationRaceInput,
    ) -> PersistedRaceResult:
        if not isinstance(value, ProviderBuildResult):
            _invalid(race_input.race_id, "race_result_provider must return ProviderBuildResult")
        if not isinstance(value.completeness, CompletenessResult):
            _invalid(race_input.race_id, "race result completeness must be CompletenessResult")
        if not isinstance(value.value, PersistedRaceResult):
            _invalid(race_input.race_id, "race result value must be PersistedRaceResult")
        if value.value.race_id != race_input.race_id:
            _invalid(race_input.race_id, "persisted race result race_id must match race_input")
        if value.value.observed_at > race_input.information_cutoff:
            _invalid(race_input.race_id, "persisted race result observed_at is after information_cutoff")
        return value.value

    @staticmethod
    def _validate_payout_provider_output(
        value: object,
        race_input: SimulationRaceInput,
        bet_type: str,
    ) -> PayoutPublication:
        if not isinstance(value, ProviderBuildResult):
            _invalid(race_input.race_id, "payout_provider must return ProviderBuildResult")
        if not isinstance(value.completeness, CompletenessResult):
            _invalid(race_input.race_id, "payout completeness must be CompletenessResult")
        if not isinstance(value.value, PayoutPublication):
            _invalid(race_input.race_id, "payout value must be PayoutPublication")
        if value.value.race_id != race_input.race_id:
            _invalid(race_input.race_id, "payout publication race_id must match race_input")
        if value.value.bet_type != bet_type:
            _invalid(race_input.race_id, "payout publication bet_type must match requested bet_type")
        if value.value.observed_at > race_input.information_cutoff:
            _invalid(race_input.race_id, "payout publication observed_at is after information_cutoff")
        return value.value

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
        settlement_data: RaceSettlementData,
        publications_by_bet_type: dict[str, PayoutPublication],
        settled_at: datetime | None,
        completeness_statuses: tuple[CompletenessStatus, ...],
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
            completeness_statuses=completeness_statuses,
            race_result_status=race_result_status,
            payout_statuses=payout_statuses,
            missing_payout_bet_types=missing_payout_bet_types,
            missing_race_result=missing_race_result,
            error_reason=None,
        )
