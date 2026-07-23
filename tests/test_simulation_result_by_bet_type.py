"""SimulationResult per-bet-type settlement aggregate contract."""
from __future__ import annotations

from dataclasses import fields
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import inspect
from types import MappingProxyType
from unittest.mock import patch
import unittest

import scripts.simulation.simulator as simulator
from scripts.simulation.models import BetTypeSummary, SettlementStatus, SimulationBet, SimulationResult
from scripts.simulation.providers.models import CompletenessStatus
from scripts.simulation.repositories.interfaces import PayoutPublication, PayoutRecord, PayoutStatus, RaceResultStatus
from scripts.simulation.simulator import (
    SimulationBetEvaluationError,
    _build_no_bet_simulation_result,
    _build_non_settled_simulation_result,
    _build_settled_simulation_result,
    _build_simulation_result_for_race,
    _evaluate_simulation_race_bets,
)


NOW = datetime(2026, 7, 23, 12, 0, tzinfo=UTC)
SETTLED_AT = NOW + timedelta(minutes=1)


def bet(bet_type: str = "単勝", selection: tuple[int, ...] = (11,), *, stake: int = 100, rank: int = 1) -> SimulationBet:
    return SimulationBet(1, "strategy-a", bet_type, selection, stake, rank, NOW)


def bets_all_types() -> tuple[SimulationBet, ...]:
    return (
        bet(),
        bet("馬連", (11, 12), stake=200),
        bet("ワイド", (11, 12), stake=300),
        bet("3連複", (11, 12, 13), stake=400),
    )


def settled_summaries(items: tuple[SimulationBet, ...], *, multiplier: int = 2) -> dict[str, BetTypeSummary]:
    summaries: dict[str, BetTypeSummary] = {}
    for bet_type in {item.bet_type for item in items}:
        matching = tuple(item for item in items if item.bet_type == bet_type)
        investment = sum(item.stake for item in matching)
        payout = investment * multiplier
        count = len(matching)
        summaries[bet_type] = BetTypeSummary(
            bet_type, count, count, count, investment, payout, payout - investment,
            Decimal(payout) * Decimal("100") / Decimal(investment), Decimal("100"),
        )
    return summaries


def non_settled_summaries(items: tuple[SimulationBet, ...]) -> dict[str, BetTypeSummary]:
    return {
        bet_type: BetTypeSummary(bet_type, len(matching), 0, 0, 0, 0, 0, None, None)
        for bet_type in {item.bet_type for item in items}
        for matching in (tuple(item for item in items if item.bet_type == bet_type),)
    }


def settled_result(items: tuple[SimulationBet, ...] = (bet(),), *, summaries: object | None = None) -> SimulationResult:
    investment = sum(item.stake for item in items)
    payout = investment * 2
    return SimulationResult(
        race_id=1,
        strategy_id="strategy-a",
        bets=items,
        settlement_status=SettlementStatus.SETTLED,
        exclusion_reason=None,
        planned_investment=investment,
        settled_investment=investment,
        payout=payout,
        profit=payout - investment,
        hit_bet_count=len(items),
        settled_at=SETTLED_AT,
        by_bet_type=settled_summaries(items) if summaries is None else summaries,  # type: ignore[arg-type]
    )


def non_settled_result(
    items: tuple[SimulationBet, ...] = (bet(),),
    *,
    status: SettlementStatus = SettlementStatus.UNSETTLED,
    summaries: object | None = None,
) -> SimulationResult:
    return SimulationResult(
        race_id=1,
        strategy_id="strategy-a",
        bets=items,
        settlement_status=status,
        exclusion_reason="unavailable",
        planned_investment=sum(item.stake for item in items),
        by_bet_type=non_settled_summaries(items) if summaries is None else summaries,  # type: ignore[arg-type]
    )


def publications(items: tuple[SimulationBet, ...], *, status: PayoutStatus = PayoutStatus.WINNING) -> dict[str, PayoutPublication]:
    return {
        bet_type: PayoutPublication(
            1, bet_type, NOW, NOW, True, "official",
            tuple(PayoutRecord(item.race_entry_ids, 200, status) for item in items if item.bet_type == bet_type),
        )
        for bet_type in {item.bet_type for item in items}
    }


class SimulationResultByBetTypeModelTests(unittest.TestCase):
    def test_by_bet_type_is_trailing_field(self) -> None:
        self.assertEqual(fields(SimulationResult)[-1].name, "by_bet_type")

    def test_no_bet_defaults_to_empty_mapping(self) -> None:
        result = SimulationResult(1, "strategy-a", (), SettlementStatus.NO_BET, None, 0)
        self.assertEqual(dict(result.by_bet_type), {})

    def test_by_bet_type_is_mapping_proxy(self) -> None:
        self.assertIsInstance(settled_result().by_bet_type, MappingProxyType)

    def test_by_bet_type_defensively_copies_input_mapping(self) -> None:
        source = settled_summaries((bet(),))
        result = settled_result(summaries=source)
        source.clear()
        self.assertEqual(tuple(result.by_bet_type), ("単勝",))

    def test_rejects_list_by_bet_type(self) -> None:
        with self.assertRaises(TypeError):
            settled_result(summaries=[])

    def test_rejects_string_by_bet_type(self) -> None:
        with self.assertRaises(TypeError):
            settled_result(summaries="単勝")

    def test_rejects_empty_bet_type_key(self) -> None:
        with self.assertRaises(TypeError):
            settled_result(summaries={"": settled_summaries((bet(),))["単勝"]})

    def test_rejects_unsupported_bet_type_key(self) -> None:
        with self.assertRaises(ValueError):
            settled_result(summaries={"複勝": settled_summaries((bet(),))["単勝"]})

    def test_rejects_non_summary_mapping_value(self) -> None:
        with self.assertRaises(TypeError):
            settled_result(summaries={"単勝": object()})

    def test_rejects_mapping_key_value_bet_type_mismatch(self) -> None:
        with self.assertRaises(ValueError):
            settled_result(summaries={"単勝": BetTypeSummary("馬連", 1, 1, 1, 100, 200, 100, Decimal("200"), Decimal("100"))})

    def test_mapping_order_is_deterministic(self) -> None:
        items = bets_all_types()
        result = settled_result(items, summaries=dict(reversed(tuple(settled_summaries(items).items()))))
        self.assertEqual(tuple(result.by_bet_type), tuple(sorted(result.by_bet_type)))

    def test_settled_requires_non_empty_mapping(self) -> None:
        with self.assertRaisesRegex(ValueError, "by_bet_type"):
            settled_result(summaries={})

    def test_settled_requires_exact_bet_type_keys(self) -> None:
        first, second = bet(), bet("馬連", (11, 12))
        with self.assertRaisesRegex(ValueError, "keys"):
            settled_result((first, second), summaries=settled_summaries((first,)))

    def test_settled_rejects_bet_count_total_mismatch(self) -> None:
        source = settled_summaries((bet(),))
        source["単勝"] = BetTypeSummary("単勝", 2, 2, 2, 100, 200, 100, Decimal("200"), Decimal("100"))
        with self.assertRaisesRegex(ValueError, "totals"):
            settled_result(summaries=source)

    def test_settled_rejects_settled_count_total_mismatch(self) -> None:
        source = settled_summaries((bet(),))
        source["単勝"] = BetTypeSummary("単勝", 1, 0, 0, 0, 0, 0, None, None)
        with self.assertRaisesRegex(ValueError, "totals"):
            settled_result(summaries=source)

    def test_settled_rejects_hit_total_mismatch(self) -> None:
        source = settled_summaries((bet(),))
        source["単勝"] = BetTypeSummary("単勝", 1, 1, 0, 100, 200, 100, Decimal("200"), Decimal("0"))
        with self.assertRaisesRegex(ValueError, "totals"):
            settled_result(summaries=source)

    def test_settled_rejects_investment_total_mismatch(self) -> None:
        source = settled_summaries((bet(),))
        source["単勝"] = BetTypeSummary("単勝", 1, 1, 1, 200, 200, 0, Decimal("100"), Decimal("100"))
        with self.assertRaisesRegex(ValueError, "totals"):
            settled_result(summaries=source)

    def test_settled_rejects_payout_total_mismatch(self) -> None:
        source = settled_summaries((bet(),))
        source["単勝"] = BetTypeSummary("単勝", 1, 1, 1, 100, 100, 0, Decimal("100"), Decimal("100"))
        with self.assertRaisesRegex(ValueError, "totals"):
            settled_result(summaries=source)

    def test_settled_rejects_profit_total_mismatch(self) -> None:
        source = settled_summaries((bet(),))
        source["単勝"] = BetTypeSummary("単勝", 1, 1, 1, 100, 300, 200, Decimal("300"), Decimal("100"))
        with self.assertRaisesRegex(ValueError, "totals"):
            settled_result(summaries=source)

    def test_settled_rejects_per_type_bet_count_mismatch(self) -> None:
        first, second = bet(), bet("馬連", (11, 12))
        source = settled_summaries((first, second))
        source["単勝"] = BetTypeSummary("単勝", 2, 2, 2, 200, 400, 200, Decimal("200"), Decimal("100"))
        source["馬連"] = BetTypeSummary("馬連", 0, 0, 0, 0, 0, 0, None, None)
        with self.assertRaisesRegex(ValueError, "entries"):
            settled_result((first, second), summaries=source)

    def test_settled_rejects_per_type_stake_mismatch(self) -> None:
        source = settled_summaries((bet(),))
        source["単勝"] = BetTypeSummary("単勝", 1, 1, 1, 200, 200, 0, Decimal("100"), Decimal("100"))
        with self.assertRaisesRegex(ValueError, "totals|entries"):
            settled_result(summaries=source)

    def test_no_bet_rejects_non_empty_mapping(self) -> None:
        with self.assertRaisesRegex(ValueError, "NO_BET"):
            SimulationResult(1, "strategy-a", (), SettlementStatus.NO_BET, None, 0, by_bet_type=non_settled_summaries((bet(),)))

    def test_non_settled_requires_mapping_for_bets(self) -> None:
        with self.assertRaisesRegex(ValueError, "keys"):
            non_settled_result(summaries={})

    def test_non_settled_rejects_settled_count(self) -> None:
        with self.assertRaisesRegex(ValueError, "zero-money"):
            non_settled_result(summaries={"単勝": BetTypeSummary("単勝", 1, 1, 0, 100, 0, -100, Decimal("0"), Decimal("0"))})

    def test_non_settled_zero_money_summary_is_accepted(self) -> None:
        result = non_settled_result(summaries={"単勝": BetTypeSummary("単勝", 1, 0, 0, 0, 0, 0, None, None)})
        self.assertEqual((result.by_bet_type["単勝"].investment, result.by_bet_type["単勝"].payout), (0, 0))

    def test_non_settled_summary_rates_are_none(self) -> None:
        result = non_settled_result()
        self.assertIsNone(result.by_bet_type["単勝"].roi)
        self.assertIsNone(result.by_bet_type["単勝"].bet_hit_rate)

    def test_empty_error_allows_empty_mapping(self) -> None:
        result = SimulationResult(1, "strategy-a", (), SettlementStatus.ERROR, "provider", 0)
        self.assertEqual(dict(result.by_bet_type), {})

    def test_empty_non_error_non_settled_result_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "non-ERROR"):
            SimulationResult(1, "strategy-a", (), SettlementStatus.UNSETTLED, "pending", 0)

    def test_empty_non_settled_rejects_non_empty_mapping(self) -> None:
        with self.assertRaisesRegex(ValueError, "empty non-SETTLED"):
            SimulationResult(1, "strategy-a", (), SettlementStatus.ERROR, "provider", 0, by_bet_type=non_settled_summaries((bet(),)))

    def test_same_pair_quinella_and_wide_have_separate_summaries(self) -> None:
        result = non_settled_result((bet("馬連", (11, 12)), bet("ワイド", (11, 12))))
        self.assertEqual(set(result.by_bet_type), {"馬連", "ワイド"})


class SimulationResultByBetTypeBuilderTests(unittest.TestCase):
    def test_settled_builder_creates_single_type_summary(self) -> None:
        item = bet()
        result = _build_settled_simulation_result(_evaluate_simulation_race_bets(1, "strategy-a", (item,), publications((item,))), SETTLED_AT)
        self.assertEqual(tuple(result.by_bet_type), ("単勝",))

    def test_settled_builder_uses_evaluation_bet_count(self) -> None:
        item = bet()
        result = _build_settled_simulation_result(_evaluate_simulation_race_bets(1, "strategy-a", (item,), publications((item,))), SETTLED_AT)
        self.assertEqual(result.by_bet_type["単勝"].bet_count, 1)

    def test_settled_builder_marks_all_bets_settled(self) -> None:
        item = bet()
        result = _build_settled_simulation_result(_evaluate_simulation_race_bets(1, "strategy-a", (item,), publications((item,))), SETTLED_AT)
        self.assertEqual(result.by_bet_type["単勝"].settled_bet_count, 1)

    def test_settled_builder_uses_evaluation_money(self) -> None:
        item = bet(stake=300)
        result = _build_settled_simulation_result(_evaluate_simulation_race_bets(1, "strategy-a", (item,), publications((item,))), SETTLED_AT)
        self.assertEqual((result.by_bet_type["単勝"].investment, result.by_bet_type["単勝"].payout), (300, 600))

    def test_settled_builder_uses_decimal_rates(self) -> None:
        item = bet()
        result = _build_settled_simulation_result(_evaluate_simulation_race_bets(1, "strategy-a", (item,), publications((item,))), SETTLED_AT)
        self.assertEqual((result.by_bet_type["単勝"].roi, result.by_bet_type["単勝"].bet_hit_rate), (Decimal("200"), Decimal("100")))

    def test_settled_builder_groups_all_four_types(self) -> None:
        items = bets_all_types()
        result = _build_settled_simulation_result(_evaluate_simulation_race_bets(1, "strategy-a", items, publications(items)), SETTLED_AT)
        self.assertEqual(set(result.by_bet_type), {"単勝", "馬連", "ワイド", "3連複"})

    def test_settled_builder_groups_same_bet_type(self) -> None:
        first, second = bet("馬連", (11, 12)), bet("馬連", (11, 13), stake=200)
        result = _build_settled_simulation_result(_evaluate_simulation_race_bets(1, "strategy-a", (first, second), publications((first, second))), SETTLED_AT)
        self.assertEqual((result.by_bet_type["馬連"].bet_count, result.by_bet_type["馬連"].investment), (2, 300))

    def test_settled_builder_counts_only_winning_hits(self) -> None:
        item = bet()
        result = _build_settled_simulation_result(
            _evaluate_simulation_race_bets(1, "strategy-a", (item,), publications((item,), status=PayoutStatus.REFUND)), SETTLED_AT,
        )
        self.assertEqual(result.by_bet_type["単勝"].hit_bet_count, 0)

    def test_settled_builder_preserves_bet_objects(self) -> None:
        item = bet()
        result = _build_settled_simulation_result(_evaluate_simulation_race_bets(1, "strategy-a", (item,), publications((item,))), SETTLED_AT)
        self.assertIs(result.bets[0], item)

    def test_settled_builder_does_not_re_evaluate_bets(self) -> None:
        item = bet()
        evaluation = _evaluate_simulation_race_bets(1, "strategy-a", (item,), publications((item,)))
        with patch.object(simulator, "_evaluate_simulation_bet", side_effect=AssertionError("must not evaluate")):
            self.assertEqual(_build_settled_simulation_result(evaluation, SETTLED_AT).by_bet_type["単勝"].bet_count, 1)

    def test_no_bet_builder_sets_empty_mapping(self) -> None:
        self.assertEqual(dict(_build_no_bet_simulation_result(1, "strategy-a").by_bet_type), {})

    def test_non_settled_builder_creates_zero_summary(self) -> None:
        result = _build_non_settled_simulation_result(race_id=1, strategy_id="strategy-a", bets=(bet(),), settlement_status=SettlementStatus.UNSETTLED, exclusion_reason="pending")
        self.assertEqual((result.by_bet_type["単勝"].investment, result.by_bet_type["単勝"].payout, result.by_bet_type["単勝"].profit), (0, 0, 0))

    def test_non_settled_builder_preserves_planned_investment(self) -> None:
        item = bet(stake=300)
        result = _build_non_settled_simulation_result(race_id=1, strategy_id="strategy-a", bets=(item,), settlement_status=SettlementStatus.UNSETTLED, exclusion_reason="pending")
        self.assertEqual((result.planned_investment, result.by_bet_type["単勝"].investment), (300, 0))

    def test_non_settled_builder_groups_all_bet_types(self) -> None:
        items = bets_all_types()
        result = _build_non_settled_simulation_result(race_id=1, strategy_id="strategy-a", bets=items, settlement_status=SettlementStatus.VOID, exclusion_reason="void")
        self.assertEqual(set(result.by_bet_type), {"単勝", "馬連", "ワイド", "3連複"})

    def test_non_settled_builder_error_empty_has_empty_mapping(self) -> None:
        result = _build_non_settled_simulation_result(race_id=1, strategy_id="strategy-a", bets=(), settlement_status=SettlementStatus.ERROR, exclusion_reason="provider")
        self.assertEqual(dict(result.by_bet_type), {})

    def test_non_settled_builder_does_not_evaluate_bets(self) -> None:
        with patch.object(simulator, "_evaluate_simulation_bet", side_effect=AssertionError("must not evaluate")):
            result = _build_non_settled_simulation_result(race_id=1, strategy_id="strategy-a", bets=(bet(),), settlement_status=SettlementStatus.UNSUPPORTED, exclusion_reason="unsupported")
        self.assertEqual(result.by_bet_type["単勝"].settled_bet_count, 0)

    def test_settled_builder_converts_summary_constructor_errors(self) -> None:
        item = bet()
        source = _evaluate_simulation_race_bets(1, "strategy-a", (item,), publications((item,)))
        original = ValueError("summary failure")
        with patch.object(simulator, "BetTypeSummary", side_effect=original):
            with self.assertRaises(SimulationBetEvaluationError) as caught:
                _build_settled_simulation_result(source, SETTLED_AT)
        self.assertIs(caught.exception.__cause__, original)

    def test_non_settled_builder_converts_summary_constructor_errors(self) -> None:
        original = TypeError("summary failure")
        with patch.object(simulator, "BetTypeSummary", side_effect=original):
            with self.assertRaises(SimulationBetEvaluationError) as caught:
                _build_non_settled_simulation_result(race_id=1, strategy_id="strategy-a", bets=(bet(),), settlement_status=SettlementStatus.UNSETTLED, exclusion_reason="pending")
        self.assertIs(caught.exception.__cause__, original)


class SimulationResultByBetTypeOrchestrationTests(unittest.TestCase):
    def kwargs(self, **overrides: object) -> dict[str, object]:
        values: dict[str, object] = {
            "race_id": 1, "strategy_id": "strategy-a", "bets": (bet(),),
            "publications_by_bet_type": publications((bet(),)), "settled_at": SETTLED_AT,
            "completeness_statuses": (), "race_result_status": None, "payout_statuses": (),
            "missing_payout_bet_types": (), "missing_race_result": False, "error_reason": None,
        }
        values.update(overrides)
        return values

    def test_orchestration_settled_result_has_summary(self) -> None:
        self.assertEqual(_build_simulation_result_for_race(**self.kwargs()).by_bet_type["単勝"].settled_bet_count, 1)  # type: ignore[arg-type]

    def test_orchestration_no_bet_result_has_empty_mapping(self) -> None:
        self.assertEqual(dict(_build_simulation_result_for_race(**self.kwargs(bets=(), publications_by_bet_type={})).by_bet_type), {})  # type: ignore[arg-type]

    def test_orchestration_unsettled_result_has_zero_summary(self) -> None:
        result = _build_simulation_result_for_race(**self.kwargs(missing_payout_bet_types=("単勝",)))  # type: ignore[arg-type]
        self.assertEqual((result.settlement_status, result.by_bet_type["単勝"].investment), (SettlementStatus.UNSETTLED, 0))

    def test_orchestration_void_result_has_zero_summary(self) -> None:
        result = _build_simulation_result_for_race(**self.kwargs(race_result_status=RaceResultStatus.VOID))  # type: ignore[arg-type]
        self.assertEqual((result.settlement_status, result.by_bet_type["単勝"].settled_bet_count), (SettlementStatus.VOID, 0))

    def test_orchestration_unsupported_result_has_zero_summary(self) -> None:
        result = _build_simulation_result_for_race(**self.kwargs(completeness_statuses=(CompletenessStatus.UNSUPPORTED,)))  # type: ignore[arg-type]
        self.assertEqual((result.settlement_status, result.by_bet_type["単勝"].payout), (SettlementStatus.UNSUPPORTED, 0))

    def test_orchestration_error_result_has_zero_summary(self) -> None:
        result = _build_simulation_result_for_race(**self.kwargs(error_reason="provider"))  # type: ignore[arg-type]
        self.assertEqual((result.settlement_status, result.by_bet_type["単勝"].profit), (SettlementStatus.ERROR, 0))

    def test_result_contains_no_atomic_evaluation_fields(self) -> None:
        names = {item.name for item in fields(SimulationResult)}
        self.assertFalse({"payout_status", "matched_record", "odds", "selection_key"} & names)

    def test_result_builder_helpers_remain_private(self) -> None:
        self.assertTrue(_build_settled_simulation_result.__name__.startswith("_"))

    def test_result_mapping_does_not_add_provider_or_repository_arguments(self) -> None:
        self.assertEqual(tuple(inspect.signature(_build_settled_simulation_result).parameters), ("evaluation", "settled_at"))


if __name__ == "__main__":
    unittest.main()
