"""Immutable settlement-source contract for one simulation race.

This module defines only the data boundary consumed by the future provider-backed
race executor.  It deliberately has no provider implementation, repository,
database, or external-I/O dependency.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import NoReturn, Protocol

from .models import SimulationBet, SimulationRaceInput
from .providers.models import (
    ProviderContext,
    RaceEntryUniverse,
    RawPayoutPublication,
    RawRaceResult,
)
from .validation import SimulationValidationError


def _invalid(race_id: object, reason: str) -> NoReturn:
    """Raise the established simulation-input validation error consistently."""
    diagnostic_race_id = race_id if isinstance(race_id, int) and not isinstance(race_id, bool) else 0
    raise SimulationValidationError(diagnostic_race_id, "race_settlement_data", reason)


def _copy_mapping(value: object, name: str, race_id: object) -> dict[object, object]:
    if not isinstance(value, Mapping):
        _invalid(race_id, f"{name} must be a Mapping")
    return dict(value)


@dataclass(frozen=True, slots=True)
class RaceSettlementData:
    """Already-fetched raw settlement data and purchase plan for exactly one race."""

    race_id: int
    bets: tuple[SimulationBet, ...]
    raw_race_result: RawRaceResult | None
    race_result_context: ProviderContext | None
    raw_payout_publications_by_bet_type: Mapping[str, RawPayoutPublication]
    payout_contexts_by_bet_type: Mapping[str, ProviderContext]
    universe: RaceEntryUniverse

    def __post_init__(self) -> None:
        try:
            if not isinstance(self.race_id, int) or isinstance(self.race_id, bool) or self.race_id <= 0:
                _invalid(self.race_id, "race_id must be a positive int")

            if not isinstance(self.bets, Sequence) or isinstance(self.bets, (str, bytes, bytearray, Mapping)):
                _invalid(self.race_id, "bets must be a Sequence")
            bets = tuple(self.bets)
            if not all(isinstance(bet, SimulationBet) for bet in bets):
                _invalid(self.race_id, "bets must contain SimulationBet values")
            if any(bet.race_id != self.race_id for bet in bets):
                _invalid(self.race_id, "bets must match race_id")

            if not isinstance(self.universe, RaceEntryUniverse):
                _invalid(self.race_id, "universe must be a RaceEntryUniverse")
            if self.universe.race_id != self.race_id:
                _invalid(self.race_id, "universe.race_id must match race_id")

            if (self.raw_race_result is None) != (self.race_result_context is None):
                _invalid(self.race_id, "raw_race_result and race_result_context must be supplied together")
            if self.raw_race_result is not None:
                if not isinstance(self.raw_race_result, RawRaceResult):
                    _invalid(self.race_id, "raw_race_result must be a RawRaceResult or None")
                if not isinstance(self.race_result_context, ProviderContext):
                    _invalid(self.race_id, "race_result_context must be a ProviderContext or None")
                if self.race_result_context.race_id != self.race_id:
                    _invalid(self.race_id, "race_result_context.race_id must match race_id")

            raw_publications = _copy_mapping(
                self.raw_payout_publications_by_bet_type,
                "raw_payout_publications_by_bet_type",
                self.race_id,
            )
            payout_contexts = _copy_mapping(
                self.payout_contexts_by_bet_type,
                "payout_contexts_by_bet_type",
                self.race_id,
            )
            if set(raw_publications) != set(payout_contexts):
                _invalid(self.race_id, "payout publication and context keys must match")

            contexts: list[ProviderContext] = []
            if self.race_result_context is not None:
                contexts.append(self.race_result_context)
            for key, publication in raw_publications.items():
                if not isinstance(key, str) or not key:
                    _invalid(self.race_id, "payout mapping keys must be non-empty str bet types")
                if not isinstance(publication, RawPayoutPublication):
                    _invalid(self.race_id, "payout publication mapping values must be RawPayoutPublication")
                if publication.bet_type != key:
                    _invalid(self.race_id, "payout publication bet_type must match its mapping key")

                context = payout_contexts[key]
                if not isinstance(context, ProviderContext):
                    _invalid(self.race_id, "payout context mapping values must be ProviderContext")
                if context.race_id != self.race_id:
                    _invalid(self.race_id, "payout context race_id must match race_id")
                if context.bet_type is not None and context.bet_type != key:
                    _invalid(self.race_id, "payout context bet_type must match its mapping key")
                contexts.append(context)

            if contexts and any(context.information_cutoff != contexts[0].information_cutoff for context in contexts[1:]):
                _invalid(self.race_id, "all provider contexts must share information_cutoff")

            object.__setattr__(self, "bets", bets)
            object.__setattr__(
                self,
                "raw_payout_publications_by_bet_type",
                MappingProxyType(dict(raw_publications)),
            )
            object.__setattr__(
                self,
                "payout_contexts_by_bet_type",
                MappingProxyType(dict(payout_contexts)),
            )
        except SimulationValidationError:
            raise
        except (TypeError, ValueError, KeyError, AttributeError) as exc:
            _invalid(self.race_id, "invalid race settlement data")


class RaceSettlementSource(Protocol):
    """Loads the already-fetched settlement data for one simulation race."""

    def load_settlement_data(
        self,
        *,
        race_input: SimulationRaceInput,
    ) -> RaceSettlementData:
        ...
