"""Pure, single-bet settlement primitives for the Ver0.8 simulator.

This module deliberately has no database, provider, or pipeline dependency.
Higher-level race settlement and aggregate metrics are introduced separately.
"""
from __future__ import annotations

from dataclasses import dataclass

from .models import SimulationBet
from .repositories.interfaces import PayoutPublication, PayoutRecord, PayoutStatus


class SimulationBetEvaluationError(ValueError):
    """Raised when a single-bet settlement input cannot be safely evaluated."""


@dataclass(frozen=True)
class _EvaluatedSimulationBet:
    """Private immutable result of evaluating one already-created simulation bet."""

    bet: SimulationBet
    investment_amount: int
    payout_amount: int
    profit: int
    hit: bool
    payout_status: PayoutStatus | None
    matched_record: PayoutRecord | None

    def __post_init__(self) -> None:
        if not isinstance(self.bet, SimulationBet):
            raise SimulationBetEvaluationError("bet must be a SimulationBet")
        for value, name, allow_negative in (
            (self.investment_amount, "investment_amount", False),
            (self.payout_amount, "payout_amount", False),
            (self.profit, "profit", True),
        ):
            if not isinstance(value, int) or isinstance(value, bool):
                raise SimulationBetEvaluationError(f"{name} must be an int")
            if not allow_negative and value < 0:
                raise SimulationBetEvaluationError(f"{name} must be non-negative")
        if self.investment_amount != self.bet.stake:
            raise SimulationBetEvaluationError("investment_amount must equal bet.stake")
        if self.profit != self.payout_amount - self.investment_amount:
            raise SimulationBetEvaluationError("profit must equal payout_amount minus investment_amount")
        if not isinstance(self.hit, bool):
            raise SimulationBetEvaluationError("hit must be bool")
        if (self.payout_status is None) != (self.matched_record is None):
            raise SimulationBetEvaluationError("payout status and matched record must both be present or absent")
        if self.matched_record is None:
            if self.hit or self.payout_amount != 0:
                raise SimulationBetEvaluationError("an unmatched bet must be a non-hit with zero payout")
            return
        if not isinstance(self.matched_record, PayoutRecord):
            raise SimulationBetEvaluationError("matched_record must be a PayoutRecord")
        if not isinstance(self.payout_status, PayoutStatus):
            raise SimulationBetEvaluationError("payout_status must be PayoutStatus or None")
        if self.matched_record.payout_status is not self.payout_status:
            raise SimulationBetEvaluationError("payout_status must match matched_record")
        if self.payout_status is PayoutStatus.UNSUPPORTED:
            raise SimulationBetEvaluationError("unsupported payouts cannot be evaluated")
        if self.hit != (self.payout_status is PayoutStatus.WINNING):
            raise SimulationBetEvaluationError("only a winning payout may be a hit")


def _calculate_payout_amount(stake: int, payout_per_100: int) -> int:
    """Calculate an exact payout without silently truncating a fractional yen."""
    if not isinstance(stake, int) or isinstance(stake, bool) or stake < 0:
        raise SimulationBetEvaluationError("stake must be a non-negative int")
    if not isinstance(payout_per_100, int) or isinstance(payout_per_100, bool) or payout_per_100 < 0:
        raise SimulationBetEvaluationError("payout_per_100 must be a non-negative int")
    numerator = stake * payout_per_100
    if numerator % 100 != 0:
        raise SimulationBetEvaluationError("payout calculation must produce an exact yen amount")
    return numerator // 100


def _evaluate_simulation_bet(
    bet: SimulationBet,
    publication: PayoutPublication,
) -> _EvaluatedSimulationBet:
    """Evaluate exactly one bet from a payout publication without external I/O.

    A record is identified solely by the publication's bet type and the canonical
    ``race_entry_ids`` selection.  Missing records mean a loss only for complete
    publications; incomplete tables fail closed because absence is ambiguous.
    """
    try:
        if not isinstance(bet, SimulationBet):
            raise SimulationBetEvaluationError("bet must be a SimulationBet")
        if not isinstance(publication, PayoutPublication):
            raise SimulationBetEvaluationError("publication must be a PayoutPublication")
        if bet.race_id != publication.race_id:
            raise SimulationBetEvaluationError("bet and publication race_id must match")

        matches = tuple(
            record
            for record in publication.entries
            if publication.bet_type == bet.bet_type
            and record.race_entry_ids == bet.race_entry_ids
        )
        if len(matches) > 1:
            raise SimulationBetEvaluationError("multiple payout records match one bet")
        if not matches:
            if not publication.is_complete:
                raise SimulationBetEvaluationError("cannot settle an unmatched bet from an incomplete publication")
            return _EvaluatedSimulationBet(
                bet=bet,
                investment_amount=bet.stake,
                payout_amount=0,
                profit=-bet.stake,
                hit=False,
                payout_status=None,
                matched_record=None,
            )

        record = matches[0]
        if record.payout_status is PayoutStatus.UNSUPPORTED:
            raise SimulationBetEvaluationError("unsupported payout status cannot be settled")
        payout_amount = _calculate_payout_amount(bet.stake, record.payout_per_100)
        return _EvaluatedSimulationBet(
            bet=bet,
            investment_amount=bet.stake,
            payout_amount=payout_amount,
            profit=payout_amount - bet.stake,
            hit=record.payout_status is PayoutStatus.WINNING,
            payout_status=record.payout_status,
            matched_record=record,
        )
    except SimulationBetEvaluationError:
        raise
    except (TypeError, ValueError, KeyError, AttributeError, ArithmeticError) as exc:
        raise SimulationBetEvaluationError("invalid single-bet settlement input") from exc
