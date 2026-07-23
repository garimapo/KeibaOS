"""Pure, single-bet settlement primitives for the Ver0.8 simulator.

This module deliberately has no database, provider, or pipeline dependency.
Higher-level race settlement and aggregate metrics are introduced separately.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from .models import BetTypeSummary, SettlementStatus, SimulationBet, SimulationResult
from .providers.models import CompletenessStatus
from .repositories.interfaces import PayoutPublication, PayoutRecord, PayoutStatus, RaceResultStatus, validate_bet_type


class SimulationBetEvaluationError(ValueError):
    """Raised when a single-bet settlement input cannot be safely evaluated."""


@dataclass(frozen=True)
class _NonSettledStatusDecision:
    """Private immutable status and reason selected from non-settlement facts."""

    settlement_status: SettlementStatus
    exclusion_reason: str

    def __post_init__(self) -> None:
        allowed_statuses = {
            SettlementStatus.UNSETTLED,
            SettlementStatus.VOID,
            SettlementStatus.ERROR,
            SettlementStatus.UNSUPPORTED,
        }
        if not isinstance(self.settlement_status, SettlementStatus) or self.settlement_status not in allowed_statuses:
            raise SimulationBetEvaluationError("settlement_status must be a supported non-settled status")
        if not isinstance(self.exclusion_reason, str) or not self.exclusion_reason.strip():
            raise SimulationBetEvaluationError("exclusion_reason must be a non-empty str")


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


@dataclass(frozen=True)
class _EvaluatedSimulationRaceBets:
    """Private immutable evaluation of all atomic bets for one race and strategy."""

    race_id: int
    strategy_id: str
    bets: tuple[SimulationBet, ...]
    evaluations: tuple[_EvaluatedSimulationBet, ...]
    investment: int
    payout: int
    profit: int
    hit_bet_count: int

    def __post_init__(self) -> None:
        if not isinstance(self.race_id, int) or isinstance(self.race_id, bool) or self.race_id <= 0:
            raise SimulationBetEvaluationError("race_id must be a positive int")
        if not isinstance(self.strategy_id, str) or not self.strategy_id:
            raise SimulationBetEvaluationError("strategy_id must be a non-empty str")
        if not isinstance(self.bets, tuple) or not self.bets:
            raise SimulationBetEvaluationError("bets must be a non-empty tuple")
        if not isinstance(self.evaluations, tuple) or len(self.evaluations) != len(self.bets):
            raise SimulationBetEvaluationError("evaluations must align with bets")
        if not all(isinstance(bet, SimulationBet) for bet in self.bets):
            raise SimulationBetEvaluationError("bets must contain SimulationBet values")
        if not all(isinstance(value, _EvaluatedSimulationBet) for value in self.evaluations):
            raise SimulationBetEvaluationError("evaluations must contain _EvaluatedSimulationBet values")
        if any(bet.race_id != self.race_id or bet.strategy_id != self.strategy_id for bet in self.bets):
            raise SimulationBetEvaluationError("all bets must belong to race_id and strategy_id")
        if any(value.bet is not bet for bet, value in zip(self.bets, self.evaluations, strict=True)):
            raise SimulationBetEvaluationError("evaluations must preserve the corresponding bet objects")
        identities = {(bet.bet_type, bet.race_entry_ids) for bet in self.bets}
        if len(identities) != len(self.bets):
            raise SimulationBetEvaluationError("bets must not contain duplicate identities")
        for value, name, positive in (
            (self.investment, "investment", True),
            (self.payout, "payout", False),
            (self.profit, "profit", False),
            (self.hit_bet_count, "hit_bet_count", False),
        ):
            if not isinstance(value, int) or isinstance(value, bool):
                raise SimulationBetEvaluationError(f"{name} must be an int")
            if positive and value <= 0:
                raise SimulationBetEvaluationError(f"{name} must be positive")
            if not positive and name != "profit" and value < 0:
                raise SimulationBetEvaluationError(f"{name} must be non-negative")
        if self.investment != sum(bet.stake for bet in self.bets):
            raise SimulationBetEvaluationError("investment must equal the sum of bet stakes")
        if self.investment != sum(value.investment_amount for value in self.evaluations):
            raise SimulationBetEvaluationError("investment must equal the sum of evaluation investments")
        if self.payout != sum(value.payout_amount for value in self.evaluations):
            raise SimulationBetEvaluationError("payout must equal the sum of evaluation payouts")
        if self.profit != sum(value.profit for value in self.evaluations):
            raise SimulationBetEvaluationError("profit must equal the sum of evaluation profits")
        if self.profit != self.payout - self.investment:
            raise SimulationBetEvaluationError("profit must equal payout minus investment")
        if self.hit_bet_count != sum(value.hit for value in self.evaluations):
            raise SimulationBetEvaluationError("hit_bet_count must equal the number of hit evaluations")
        if not 0 <= self.hit_bet_count <= len(self.bets):
            raise SimulationBetEvaluationError("hit_bet_count must be within the bet count")


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


def _evaluate_simulation_race_bets(
    race_id: int,
    strategy_id: str,
    bets: Sequence[SimulationBet],
    publications_by_bet_type: Mapping[str, PayoutPublication],
) -> _EvaluatedSimulationRaceBets:
    """Evaluate all atomic bets for exactly one race and one strategy without I/O."""
    try:
        if not isinstance(race_id, int) or isinstance(race_id, bool) or race_id <= 0:
            raise SimulationBetEvaluationError("race_id must be a positive int")
        if not isinstance(strategy_id, str) or not strategy_id:
            raise SimulationBetEvaluationError("strategy_id must be a non-empty str")
        if not isinstance(bets, Sequence) or isinstance(bets, (str, bytes, bytearray)):
            raise SimulationBetEvaluationError("bets must be a Sequence")
        ordered_bets = tuple(bets)
        if not ordered_bets:
            raise SimulationBetEvaluationError("bets must not be empty")
        if not all(isinstance(bet, SimulationBet) for bet in ordered_bets):
            raise SimulationBetEvaluationError("bets must contain SimulationBet values")
        if any(bet.race_id != race_id for bet in ordered_bets):
            raise SimulationBetEvaluationError("all bets must match race_id")
        if any(bet.strategy_id != strategy_id for bet in ordered_bets):
            raise SimulationBetEvaluationError("all bets must match strategy_id")
        if len({(bet.bet_type, bet.race_entry_ids) for bet in ordered_bets}) != len(ordered_bets):
            raise SimulationBetEvaluationError("bets must not contain duplicate identities")
        if not isinstance(publications_by_bet_type, Mapping):
            raise SimulationBetEvaluationError("publications_by_bet_type must be a Mapping")
        publications = dict(publications_by_bet_type)
        for key, publication in publications.items():
            kind = validate_bet_type(key)
            if not isinstance(publication, PayoutPublication):
                raise SimulationBetEvaluationError("mapping values must be PayoutPublication")
            if publication.bet_type != kind:
                raise SimulationBetEvaluationError("publication bet_type must match its mapping key")
            if publication.race_id != race_id:
                raise SimulationBetEvaluationError("publication race_id must match race_id")
        expected_types = {bet.bet_type for bet in ordered_bets}
        if set(publications) != expected_types:
            raise SimulationBetEvaluationError("publication mapping keys must exactly match bet types")
        evaluations = tuple(
            _evaluate_simulation_bet(bet, publications[bet.bet_type])
            for bet in ordered_bets
        )
        investment = sum(value.investment_amount for value in evaluations)
        payout = sum(value.payout_amount for value in evaluations)
        profit = sum(value.profit for value in evaluations)
        hit_bet_count = sum(value.hit for value in evaluations)
        return _EvaluatedSimulationRaceBets(
            race_id=race_id,
            strategy_id=strategy_id,
            bets=ordered_bets,
            evaluations=evaluations,
            investment=investment,
            payout=payout,
            profit=profit,
            hit_bet_count=hit_bet_count,
        )
    except SimulationBetEvaluationError:
        raise
    except (TypeError, ValueError, KeyError, AttributeError, ArithmeticError) as exc:
        raise SimulationBetEvaluationError("invalid race-bet settlement input") from exc


def _build_settled_simulation_result(
    evaluation: _EvaluatedSimulationRaceBets,
    settled_at: datetime,
) -> SimulationResult:
    """Convert one successful internal race evaluation into a SETTLED result."""
    try:
        if not isinstance(evaluation, _EvaluatedSimulationRaceBets):
            raise SimulationBetEvaluationError("evaluation must be _EvaluatedSimulationRaceBets")
        if not isinstance(settled_at, datetime) or settled_at.tzinfo is None or settled_at.utcoffset() is None:
            raise SimulationBetEvaluationError("settled_at must be a timezone-aware datetime")
        if any(settled_at < bet.placed_at_cutoff for bet in evaluation.bets):
            raise SimulationBetEvaluationError("settled_at must not precede a bet placed_at_cutoff")
        by_bet_type = _build_settled_bet_type_summaries(evaluation.evaluations)
        return SimulationResult(
            race_id=evaluation.race_id,
            strategy_id=evaluation.strategy_id,
            bets=evaluation.bets,
            settlement_status=SettlementStatus.SETTLED,
            exclusion_reason=None,
            planned_investment=evaluation.investment,
            settled_investment=evaluation.investment,
            payout=evaluation.payout,
            profit=evaluation.profit,
            hit_bet_count=evaluation.hit_bet_count,
            settled_at=settled_at,
            by_bet_type=by_bet_type,
        )
    except SimulationBetEvaluationError:
        raise
    except (TypeError, ValueError, KeyError, AttributeError, ArithmeticError) as exc:
        raise SimulationBetEvaluationError("invalid settled-result conversion input") from exc


def _build_no_bet_simulation_result(
    race_id: int,
    strategy_id: str,
) -> SimulationResult:
    """Build an empty NO_BET result without evaluating bets or consulting data sources."""
    try:
        if not isinstance(race_id, int) or isinstance(race_id, bool) or race_id <= 0:
            raise SimulationBetEvaluationError("race_id must be a positive int")
        if not isinstance(strategy_id, str) or not strategy_id:
            raise SimulationBetEvaluationError("strategy_id must be a non-empty str")
        return SimulationResult(
            race_id=race_id,
            strategy_id=strategy_id,
            bets=(),
            settlement_status=SettlementStatus.NO_BET,
            exclusion_reason=None,
            planned_investment=0,
            settled_investment=None,
            payout=None,
            profit=None,
            hit_bet_count=0,
            settled_at=None,
            by_bet_type={},
        )
    except SimulationBetEvaluationError:
        raise
    except (TypeError, ValueError, KeyError, AttributeError, ArithmeticError) as exc:
        raise SimulationBetEvaluationError("invalid no-bet result input") from exc


def _build_non_settled_simulation_result(
    *,
    race_id: int,
    strategy_id: str,
    bets: Sequence[SimulationBet],
    settlement_status: SettlementStatus,
    exclusion_reason: str,
) -> SimulationResult:
    """Build a non-settled result without evaluating bets or external data."""
    try:
        if not isinstance(race_id, int) or isinstance(race_id, bool) or race_id <= 0:
            raise SimulationBetEvaluationError("race_id must be a positive int")
        if not isinstance(strategy_id, str) or not strategy_id:
            raise SimulationBetEvaluationError("strategy_id must be a non-empty str")
        if not isinstance(bets, Sequence) or isinstance(bets, (str, bytes, bytearray)):
            raise SimulationBetEvaluationError("bets must be a Sequence")
        ordered_bets = tuple(bets)
        if not all(isinstance(bet, SimulationBet) for bet in ordered_bets):
            raise SimulationBetEvaluationError("bets must contain SimulationBet values")
        if any(bet.race_id != race_id or bet.strategy_id != strategy_id for bet in ordered_bets):
            raise SimulationBetEvaluationError("bets must belong to race_id and strategy_id")
        if len({(bet.bet_type, bet.race_entry_ids) for bet in ordered_bets}) != len(ordered_bets):
            raise SimulationBetEvaluationError("bets must not contain duplicate identities")
        allowed_statuses = {
            SettlementStatus.UNSETTLED,
            SettlementStatus.VOID,
            SettlementStatus.ERROR,
            SettlementStatus.UNSUPPORTED,
        }
        if not isinstance(settlement_status, SettlementStatus) or settlement_status not in allowed_statuses:
            raise SimulationBetEvaluationError("settlement_status must be a supported non-settled status")
        if settlement_status is not SettlementStatus.ERROR and not ordered_bets:
            raise SimulationBetEvaluationError("non-ERROR non-settled results require at least one bet")
        if not isinstance(exclusion_reason, str) or not exclusion_reason.strip():
            raise SimulationBetEvaluationError("exclusion_reason must be a non-empty str")
        by_bet_type = _build_non_settled_bet_type_summaries(ordered_bets)
        return SimulationResult(
            race_id=race_id,
            strategy_id=strategy_id,
            bets=ordered_bets,
            settlement_status=settlement_status,
            exclusion_reason=exclusion_reason,
            planned_investment=sum(bet.stake for bet in ordered_bets),
            settled_investment=None,
            payout=None,
            profit=None,
            hit_bet_count=0,
            settled_at=None,
            by_bet_type=by_bet_type,
        )
    except SimulationBetEvaluationError:
        raise
    except (TypeError, ValueError, KeyError, AttributeError, ArithmeticError) as exc:
        raise SimulationBetEvaluationError("invalid non-settled result input") from exc


def _build_settled_bet_type_summaries(
    evaluations: Sequence[_EvaluatedSimulationBet],
) -> Mapping[str, BetTypeSummary]:
    """Aggregate already-evaluated atomic bets once per supported bet type."""
    grouped: dict[str, list[_EvaluatedSimulationBet]] = {}
    for evaluation in evaluations:
        grouped.setdefault(evaluation.bet.bet_type, []).append(evaluation)
    summaries: dict[str, BetTypeSummary] = {}
    for bet_type in sorted(grouped):
        values = grouped[bet_type]
        investment = sum(value.investment_amount for value in values)
        payout = sum(value.payout_amount for value in values)
        hit_bet_count = sum(value.hit for value in values)
        summaries[bet_type] = BetTypeSummary(
            bet_type=bet_type,
            bet_count=len(values),
            settled_bet_count=len(values),
            hit_bet_count=hit_bet_count,
            investment=investment,
            payout=payout,
            profit=payout - investment,
            roi=Decimal(payout) * Decimal("100") / Decimal(investment),
            bet_hit_rate=Decimal(hit_bet_count) * Decimal("100") / Decimal(len(values)),
        )
    return summaries


def _build_non_settled_bet_type_summaries(
    bets: Sequence[SimulationBet],
) -> Mapping[str, BetTypeSummary]:
    """Represent planned, non-settled bets without attributing settlement money."""
    counts: dict[str, int] = {}
    for bet in bets:
        counts[bet.bet_type] = counts.get(bet.bet_type, 0) + 1
    return {
        bet_type: BetTypeSummary(
            bet_type=bet_type,
            bet_count=count,
            settled_bet_count=0,
            hit_bet_count=0,
            investment=0,
            payout=0,
            profit=0,
            roi=None,
            bet_hit_rate=None,
        )
        for bet_type, count in sorted(counts.items())
    }


def _decide_non_settled_status(
    *,
    completeness_statuses: Sequence[CompletenessStatus],
    race_result_status: RaceResultStatus | None,
    payout_statuses: Sequence[PayoutStatus],
    missing_payout_bet_types: Sequence[str],
    missing_race_result: bool,
    error_reason: str | None,
) -> _NonSettledStatusDecision | None:
    """Classify already-known non-settlement facts without constructing results."""
    try:
        if not isinstance(completeness_statuses, Sequence) or isinstance(completeness_statuses, (str, bytes, bytearray)):
            raise SimulationBetEvaluationError("completeness_statuses must be a Sequence")
        normalized_completeness = tuple(completeness_statuses)
        if not all(isinstance(status, CompletenessStatus) for status in normalized_completeness):
            raise SimulationBetEvaluationError("completeness_statuses must contain CompletenessStatus values")
        if race_result_status is not None and not isinstance(race_result_status, RaceResultStatus):
            raise SimulationBetEvaluationError("race_result_status must be RaceResultStatus or None")
        if not isinstance(payout_statuses, Sequence) or isinstance(payout_statuses, (str, bytes, bytearray)):
            raise SimulationBetEvaluationError("payout_statuses must be a Sequence")
        normalized_payouts = tuple(payout_statuses)
        if not all(isinstance(status, PayoutStatus) for status in normalized_payouts):
            raise SimulationBetEvaluationError("payout_statuses must contain PayoutStatus values")
        if not isinstance(missing_payout_bet_types, Sequence) or isinstance(missing_payout_bet_types, (str, bytes, bytearray)):
            raise SimulationBetEvaluationError("missing_payout_bet_types must be a Sequence")
        missing_types = tuple(sorted({validate_bet_type(value) for value in missing_payout_bet_types}))
        if not isinstance(missing_race_result, bool):
            raise SimulationBetEvaluationError("missing_race_result must be bool")
        if error_reason is not None and (not isinstance(error_reason, str) or not error_reason.strip()):
            raise SimulationBetEvaluationError("error_reason must be a non-empty str or None")

        if error_reason is not None:
            return _NonSettledStatusDecision(SettlementStatus.ERROR, error_reason)
        if CompletenessStatus.INVALID in normalized_completeness:
            return _NonSettledStatusDecision(SettlementStatus.ERROR, "invalid_provider_completeness")
        if race_result_status is RaceResultStatus.VOID:
            return _NonSettledStatusDecision(SettlementStatus.VOID, "official_race_void")
        if CompletenessStatus.UNSUPPORTED in normalized_completeness:
            return _NonSettledStatusDecision(SettlementStatus.UNSUPPORTED, "unsupported_provider_completeness")
        if race_result_status is RaceResultStatus.UNSUPPORTED:
            return _NonSettledStatusDecision(SettlementStatus.UNSUPPORTED, "unsupported_race_result")
        if PayoutStatus.UNSUPPORTED in normalized_payouts:
            return _NonSettledStatusDecision(SettlementStatus.UNSUPPORTED, "unsupported_payout_status")
        if missing_types:
            return _NonSettledStatusDecision(SettlementStatus.UNSETTLED, "missing_payout_publication")
        if missing_race_result:
            return _NonSettledStatusDecision(SettlementStatus.UNSETTLED, "missing_race_result")
        if CompletenessStatus.INCOMPLETE in normalized_completeness:
            return _NonSettledStatusDecision(SettlementStatus.UNSETTLED, "incomplete_provider_data")
        if race_result_status is RaceResultStatus.PARTIAL:
            return _NonSettledStatusDecision(SettlementStatus.UNSETTLED, "incomplete_race_result")
        return None
    except SimulationBetEvaluationError:
        raise
    except (TypeError, ValueError, KeyError, AttributeError, ArithmeticError) as exc:
        raise SimulationBetEvaluationError("invalid non-settled status decision input") from exc


def _build_simulation_result_for_race(
    *,
    race_id: int,
    strategy_id: str,
    bets: Sequence[SimulationBet],
    publications_by_bet_type: Mapping[str, PayoutPublication],
    settled_at: datetime,
    completeness_statuses: Sequence[CompletenessStatus],
    race_result_status: RaceResultStatus | None,
    payout_statuses: Sequence[PayoutStatus],
    missing_payout_bet_types: Sequence[str],
    missing_race_result: bool,
    error_reason: str | None,
) -> SimulationResult:
    """Orchestrate one race into exactly one final ``SimulationResult`` without I/O."""
    if isinstance(bets, Sequence) and not isinstance(bets, (str, bytes, bytearray)) and not bets:
        return _build_no_bet_simulation_result(race_id, strategy_id)

    evaluation = _evaluate_simulation_race_bets(
        race_id,
        strategy_id,
        bets,
        publications_by_bet_type,
    )
    decision = _decide_non_settled_status(
        completeness_statuses=completeness_statuses,
        race_result_status=race_result_status,
        payout_statuses=payout_statuses,
        missing_payout_bet_types=missing_payout_bet_types,
        missing_race_result=missing_race_result,
        error_reason=error_reason,
    )
    if decision is None:
        return _build_settled_simulation_result(evaluation, settled_at)
    return _build_non_settled_simulation_result(
        race_id=race_id,
        strategy_id=strategy_id,
        bets=evaluation.bets,
        settlement_status=decision.settlement_status,
        exclusion_reason=decision.exclusion_reason,
    )
