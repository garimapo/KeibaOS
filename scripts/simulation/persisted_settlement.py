"""Immutable persisted-settlement contract for one simulation race.

This module defines only the boundary for settlement values already loaded from
repositories.  It deliberately contains no repository implementation, database,
provider, or external-I/O dependency.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import NoReturn, Protocol

from .models import SimulationBet, SimulationRaceInput, StrategyIdentity
from .repositories.interfaces import PayoutPublication, PersistedRaceResult, validate_bet_type
from .validation import SimulationValidationError


def _invalid(race_id: object, reason: str) -> NoReturn:
    """Raise the established simulation-boundary validation error."""
    diagnostic_race_id = race_id if isinstance(race_id, int) and not isinstance(race_id, bool) else 0
    raise SimulationValidationError(diagnostic_race_id, "persisted_race_settlement_data", reason)


def _copy_mapping(value: object, name: str, race_id: object) -> dict[object, object]:
    if not isinstance(value, Mapping):
        _invalid(race_id, f"{name} must be a Mapping")
    return dict(value)


@dataclass(frozen=True, slots=True)
class PersistedRaceSettlementData:
    """Already-loaded persisted settlement values and purchase plan for one race."""

    race_id: int
    bets: tuple[SimulationBet, ...]
    race_result: PersistedRaceResult | None
    payout_publications_by_bet_type: Mapping[str, PayoutPublication]

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

            if self.race_result is not None:
                if not isinstance(self.race_result, PersistedRaceResult):
                    _invalid(self.race_id, "race_result must be a PersistedRaceResult or None")
                if self.race_result.race_id != self.race_id:
                    _invalid(self.race_id, "race_result.race_id must match race_id")

            publications = _copy_mapping(
                self.payout_publications_by_bet_type,
                "payout_publications_by_bet_type",
                self.race_id,
            )
            for bet_type, publication in publications.items():
                try:
                    normalized_bet_type = validate_bet_type(bet_type)
                except (TypeError, ValueError, AttributeError) as exc:
                    raise SimulationValidationError(
                        self.race_id,
                        "persisted_race_settlement_data",
                        "payout publication mapping keys must be supported bet types",
                    ) from exc
                if not isinstance(publication, PayoutPublication):
                    _invalid(self.race_id, "payout publication mapping values must be PayoutPublication")
                if publication.race_id != self.race_id:
                    _invalid(self.race_id, "payout publication race_id must match race_id")
                if publication.bet_type != normalized_bet_type:
                    _invalid(self.race_id, "payout publication bet_type must match its mapping key")

            object.__setattr__(self, "bets", bets)
            object.__setattr__(self, "payout_publications_by_bet_type", MappingProxyType(publications))
        except SimulationValidationError:
            raise
        except (TypeError, ValueError, KeyError, AttributeError) as exc:
            _invalid(self.race_id, "invalid persisted race settlement data")


class PersistedRaceSettlementSource(Protocol):
    """Loads persisted settlement values for one simulation race and strategy."""

    def load_settlement_data(
        self,
        *,
        race_input: SimulationRaceInput,
        strategy_identity: StrategyIdentity,
    ) -> PersistedRaceSettlementData:
        ...
