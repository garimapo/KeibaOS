"""Tests for converting a successful race evaluation into SETTLED SimulationResult."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
import inspect
from unittest.mock import patch
import unittest

import scripts.simulation as simulation_package
import scripts.simulation.simulator as simulator
from scripts.simulation.models import SettlementStatus, SimulationBet, SimulationResult
from scripts.simulation.repositories.interfaces import PayoutPublication, PayoutRecord, PayoutStatus
from scripts.simulation.simulator import (
    SimulationBetEvaluationError,
    _build_settled_simulation_result,
    _evaluate_simulation_race_bets,
)


NOW = datetime(2026, 7, 22, 12, 0, tzinfo=UTC)
SETTLED_AT = NOW + timedelta(minutes=1)


def bet(bet_type: str = "単勝", selection: tuple[int, ...] = (11,), *, stake: int = 100) -> SimulationBet:
    return SimulationBet(1, "strategy-a", bet_type, selection, stake, 1, NOW)


def publication(item: SimulationBet, payout_per_100: int = 200, status: PayoutStatus = PayoutStatus.WINNING) -> PayoutPublication:
    return PayoutPublication(1, item.bet_type, NOW, NOW, True, "official", (
        PayoutRecord(item.race_entry_ids, payout_per_100, status),
    ))


def evaluation(items: tuple[SimulationBet, ...], publications: dict[str, PayoutPublication] | None = None):
    mapping = publications if publications is not None else {item.bet_type: publication(item) for item in items}
    return _evaluate_simulation_race_bets(1, "strategy-a", items, mapping)


class SettledSimulationResultConversionTests(unittest.TestCase):
    def build(self, items: tuple[SimulationBet, ...] = (bet(),), *, settled_at: datetime = SETTLED_AT, publications=None):
        return _build_settled_simulation_result(evaluation(items, publications), settled_at)

    def test_builds_simulation_result(self) -> None:
        self.assertIsInstance(self.build(), SimulationResult)

    def test_result_status_is_settled_and_reason_is_none(self) -> None:
        result = self.build()
        self.assertIs(result.settlement_status, SettlementStatus.SETTLED)
        self.assertIsNone(result.exclusion_reason)

    def test_preserves_race_id(self) -> None:
        self.assertEqual(self.build().race_id, 1)

    def test_preserves_strategy_id(self) -> None:
        self.assertEqual(self.build().strategy_id, "strategy-a")

    def test_preserves_bet_order(self) -> None:
        win, quinella = bet(), bet("馬連", (11, 12))
        self.assertEqual(self.build((win, quinella)).bets, (win, quinella))

    def test_preserves_race_strategy_bet_order_and_objects(self) -> None:
        win, quinella = bet(), bet("馬連", (11, 12))
        result = self.build((win, quinella))
        self.assertEqual((result.race_id, result.strategy_id, result.bets), (1, "strategy-a", (win, quinella)))
        self.assertIs(result.bets[0], win)
        self.assertIs(result.bets[1], quinella)

    def test_preserves_evaluation_monetary_values_and_hits(self) -> None:
        win, quinella = bet(stake=100), bet("馬連", (11, 12), stake=300)
        source = evaluation((win, quinella), {"単勝": publication(win, 200), "馬連": publication(quinella, 1250)})
        result = _build_settled_simulation_result(source, SETTLED_AT)
        self.assertEqual(result.planned_investment, source.investment)
        self.assertEqual(result.settled_investment, source.investment)
        self.assertEqual((result.payout, result.profit, result.hit_bet_count), (source.payout, source.profit, source.hit_bet_count))

    def test_planned_and_settled_investment_equal_evaluation_investment(self) -> None:
        source = evaluation((bet(),))
        result = _build_settled_simulation_result(source, SETTLED_AT)
        self.assertEqual((result.planned_investment, result.settled_investment), (source.investment, source.investment))

    def test_preserves_payout_profit_and_hit_bet_count_individually(self) -> None:
        source = evaluation((bet(),))
        result = _build_settled_simulation_result(source, SETTLED_AT)
        self.assertEqual(result.payout, source.payout)
        self.assertEqual(result.profit, source.profit)
        self.assertEqual(result.hit_bet_count, source.hit_bet_count)

    def test_preserves_supplied_settled_at_object(self) -> None:
        result = self.build()
        self.assertIs(result.settled_at, SETTLED_AT)

    def test_settled_result_contains_non_empty_evaluated_bets(self) -> None:
        self.assertEqual(len(self.build().bets), 1)

    def test_settled_at_is_not_before_any_bet_cutoff(self) -> None:
        result = self.build((bet(), bet("馬連", (11, 12))))
        self.assertTrue(all(result.settled_at >= item.placed_at_cutoff for item in result.bets))

    def test_builds_single_multiple_and_all_four_bet_type_results(self) -> None:
        single = self.build()
        multiple = self.build((bet(), bet("馬連", (11, 12))))
        four = self.build((bet(), bet("馬連", (11, 12)), bet("ワイド", (11, 12)), bet("3連複", (11, 12, 13))))
        self.assertEqual((len(single.bets), len(multiple.bets), len(four.bets)), (1, 2, 4))

    def test_builds_zero_hit_negative_and_positive_profit_results(self) -> None:
        losing = bet("馬連", (11, 12), stake=200)
        zero_hit = self.build((losing,), publications={"馬連": PayoutPublication(1, "馬連", NOW, NOW, True, "official", (PayoutRecord((11, 13), 200, PayoutStatus.WINNING),))})
        refund = bet("単勝", (11,), stake=100)
        non_positive = self.build((refund,), publications={"単勝": publication(refund, 0, PayoutStatus.VOID)})
        positive = self.build()
        self.assertEqual((zero_hit.hit_bet_count, zero_hit.profit), (0, -200))
        self.assertEqual((non_positive.hit_bet_count, non_positive.profit), (0, -100))
        self.assertGreater(positive.profit, 0)

    def test_settled_result_keeps_profit_constructor_invariant(self) -> None:
        result = self.build()
        self.assertEqual(result.profit, result.payout - result.settled_investment)

    def test_rejects_invalid_evaluation_type(self) -> None:
        for value in (None, {}, (), [], bet(), SimulationResult):
            with self.subTest(value=value), self.assertRaises(SimulationBetEvaluationError):
                _build_settled_simulation_result(value, SETTLED_AT)  # type: ignore[arg-type]

    def test_rejects_missing_naive_and_non_datetime_settled_at(self) -> None:
        source = evaluation((bet(),))
        for value in (None, datetime(2026, 7, 22, 12, 1), "time", True):
            with self.subTest(value=value), self.assertRaises(SimulationBetEvaluationError):
                _build_settled_simulation_result(source, value)  # type: ignore[arg-type]

    def test_rejects_settled_at_before_bet_cutoff(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            self.build(settled_at=NOW - timedelta(seconds=1))

    def test_converts_simulation_result_type_error_and_preserves_cause(self) -> None:
        source = evaluation((bet(),))
        original = TypeError("constructor type failure")
        with patch.object(simulator, "SimulationResult", side_effect=original):
            with self.assertRaises(SimulationBetEvaluationError) as caught:
                _build_settled_simulation_result(source, SETTLED_AT)
        self.assertIs(caught.exception.__cause__, original)

    def test_converts_simulation_result_value_error_and_returns_no_partial_result(self) -> None:
        source = evaluation((bet(),))
        original = ValueError("constructor value failure")
        with patch.object(simulator, "SimulationResult", side_effect=original):
            with self.assertRaises(SimulationBetEvaluationError) as caught:
                _build_settled_simulation_result(source, SETTLED_AT)
        self.assertIs(caught.exception.__cause__, original)

    def test_does_not_re_evaluate_or_mutate_inputs(self) -> None:
        source = evaluation((bet(),))
        with patch.object(simulator, "_evaluate_simulation_bet", side_effect=AssertionError("must not run")), patch.object(simulator, "_evaluate_simulation_race_bets", side_effect=AssertionError("must not run")):
            result = _build_settled_simulation_result(source, SETTLED_AT)
        self.assertIs(result.bets[0], source.bets[0])
        self.assertEqual(source.evaluations[0].bet, source.bets[0])

    def test_does_not_use_current_time_or_create_no_bet_result(self) -> None:
        source = inspect.getsource(_build_settled_simulation_result)
        self.assertNotIn("datetime.now", source)
        self.assertNotIn("datetime.utcnow", source)
        self.assertNotIn("NO_BET", source)

    def test_settled_builder_does_not_call_provider_or_repository(self) -> None:
        signature = inspect.signature(_build_settled_simulation_result)
        self.assertEqual(tuple(signature.parameters), ("evaluation", "settled_at"))
        helper_source = inspect.getsource(_build_settled_simulation_result)
        self.assertNotIn("PayoutPublication", helper_source)
        self.assertNotIn("Provider", helper_source)
        self.assertNotIn("Repository", helper_source)
        self.assertNotIn("_evaluate_simulation_bet", helper_source)
        self.assertNotIn("_evaluate_simulation_race_bets", helper_source)
        self.assertNotIn("sqlite", helper_source.lower())
        self.assertNotIn("requests", helper_source)
        self.assertNotIn("roi", helper_source.lower())
        self.assertNotIn("drawdown", helper_source.lower())

    def test_internal_helper_is_not_exported_from_package_root(self) -> None:
        self.assertNotIn("_build_settled_simulation_result", simulation_package.__all__)
        self.assertFalse(hasattr(simulation_package, "_build_settled_simulation_result"))


if __name__ == "__main__":
    unittest.main()
