"""Tests for the shared non-settled SimulationResult builder."""
from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
import inspect
from pathlib import Path
from unittest.mock import patch
import unittest

import scripts.simulation as simulation_package
import scripts.simulation.simulator as simulator
from scripts.simulation.models import SettlementStatus, SimulationBet, SimulationResult
from scripts.simulation.simulator import SimulationBetEvaluationError, _build_non_settled_simulation_result


NOW = datetime(2026, 7, 22, 12, 0, tzinfo=UTC)


def bet(
    bet_type: str = "単勝",
    selection: tuple[int, ...] = (11,),
    *,
    stake: int = 100,
    rank: int = 1,
) -> SimulationBet:
    return SimulationBet(1, "strategy-a", bet_type, selection, stake, rank, NOW)


class OtherStatus(Enum):
    UNKNOWN = "unknown"


class NonSettledSimulationResultBuilderTests(unittest.TestCase):
    def build(
        self,
        *,
        status: SettlementStatus = SettlementStatus.UNSETTLED,
        items=(bet(),),
        reason: str = "missing_payout_publication",
        race_id: int = 1,
        strategy_id: str = "strategy-a",
    ) -> SimulationResult:
        return _build_non_settled_simulation_result(
            race_id=race_id,
            strategy_id=strategy_id,
            bets=items,
            settlement_status=status,
            exclusion_reason=reason,
        )

    def test_builds_unsettled_result(self) -> None:
        self.assertIs(self.build().settlement_status, SettlementStatus.UNSETTLED)

    def test_builds_void_result(self) -> None:
        self.assertIs(self.build(status=SettlementStatus.VOID).settlement_status, SettlementStatus.VOID)

    def test_builds_error_result_with_bets(self) -> None:
        self.assertIs(self.build(status=SettlementStatus.ERROR).settlement_status, SettlementStatus.ERROR)

    def test_builds_unsupported_result(self) -> None:
        self.assertIs(self.build(status=SettlementStatus.UNSUPPORTED).settlement_status, SettlementStatus.UNSUPPORTED)

    def test_error_allows_empty_bets(self) -> None:
        result = self.build(status=SettlementStatus.ERROR, items=())
        self.assertEqual((result.bets, result.planned_investment), ((), 0))

    def test_unsettled_rejects_empty_bets(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            self.build(status=SettlementStatus.UNSETTLED, items=())

    def test_void_rejects_empty_bets(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            self.build(status=SettlementStatus.VOID, items=())

    def test_unsupported_rejects_empty_bets(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            self.build(status=SettlementStatus.UNSUPPORTED, items=())

    def test_planned_investment_is_sum_of_stakes(self) -> None:
        result = self.build(items=(bet(stake=100), bet("馬連", (11, 12), stake=300)))
        self.assertEqual(result.planned_investment, 400)

    def test_non_settlement_money_fields_are_none(self) -> None:
        result = self.build()
        self.assertIsNone(result.settled_investment)
        self.assertIsNone(result.payout)
        self.assertIsNone(result.profit)

    def test_non_settlement_hit_count_and_time_contract(self) -> None:
        result = self.build()
        self.assertEqual(result.hit_bet_count, 0)
        self.assertIsNone(result.settled_at)

    def test_preserves_exclusion_reason(self) -> None:
        self.assertEqual(self.build(reason="incomplete_payout_publication").exclusion_reason, "incomplete_payout_publication")

    def test_preserves_bet_order(self) -> None:
        first, second = bet(), bet("馬連", (11, 12))
        self.assertEqual(self.build(items=(first, second)).bets, (first, second))

    def test_preserves_bet_object_identity(self) -> None:
        first, second = bet(), bet("馬連", (11, 12))
        result = self.build(items=(first, second))
        self.assertIs(result.bets[0], first)
        self.assertIs(result.bets[1], second)

    def test_input_list_is_not_mutated(self) -> None:
        values = [bet(), bet("馬連", (11, 12))]
        before = list(values)
        self.build(items=values)
        self.assertEqual(values, before)

    def test_result_bets_are_a_tuple(self) -> None:
        self.assertIsInstance(self.build(items=[bet()]).bets, tuple)

    def test_rejects_duplicate_bet_identity(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            self.build(items=(bet(stake=100), bet(stake=200, rank=2)))

    def test_allows_quinella_and_wide_for_same_pair(self) -> None:
        result = self.build(items=(bet("馬連", (11, 12)), bet("ワイド", (11, 12))))
        self.assertEqual(tuple(item.bet_type for item in result.bets), ("馬連", "ワイド"))

    def test_rejects_race_mismatch(self) -> None:
        other = SimulationBet(2, "strategy-a", "単勝", (11,), 100, 1, NOW)
        with self.assertRaises(SimulationBetEvaluationError):
            self.build(items=(other,))

    def test_rejects_strategy_mismatch(self) -> None:
        other = SimulationBet(1, "strategy-b", "単勝", (11,), 100, 1, NOW)
        with self.assertRaises(SimulationBetEvaluationError):
            self.build(items=(other,))

    def test_rejects_settled_status(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            self.build(status=SettlementStatus.SETTLED)

    def test_rejects_no_bet_status(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            self.build(status=SettlementStatus.NO_BET)

    def test_rejects_string_none_and_other_enum_status(self) -> None:
        for value in ("unsettled", None, OtherStatus.UNKNOWN):
            with self.subTest(value=value), self.assertRaises(SimulationBetEvaluationError):
                self.build(status=value)  # type: ignore[arg-type]

    def test_rejects_zero_negative_bool_and_wrong_type_race_id(self) -> None:
        for value in (0, -1, True, False, 1.0, "1", None):
            with self.subTest(value=value), self.assertRaises(SimulationBetEvaluationError):
                self.build(race_id=value)  # type: ignore[arg-type]

    def test_rejects_empty_and_non_string_strategy_id(self) -> None:
        for value in ("", None, 1, [], {}):
            with self.subTest(value=value), self.assertRaises(SimulationBetEvaluationError):
                self.build(strategy_id=value)  # type: ignore[arg-type]

    def test_rejects_empty_whitespace_and_non_string_reason(self) -> None:
        for value in ("", "   ", None, 1, [], {}):
            with self.subTest(value=value), self.assertRaises(SimulationBetEvaluationError):
                self.build(reason=value)  # type: ignore[arg-type]

    def test_rejects_non_sequence_and_text_bets(self) -> None:
        for value in (None, 1, "bets", b"bets", bytearray(b"bets")):
            with self.subTest(value=value), self.assertRaises(SimulationBetEvaluationError):
                self.build(items=value)  # type: ignore[arg-type]

    def test_rejects_non_bet_values(self) -> None:
        for value in ((None,), ("bet",), ({},)):
            with self.subTest(value=value), self.assertRaises(SimulationBetEvaluationError):
                self.build(items=value)  # type: ignore[arg-type]

    def test_converts_simulation_result_type_error_and_preserves_cause(self) -> None:
        original = TypeError("constructor type failure")
        with patch.object(simulator, "SimulationResult", side_effect=original):
            with self.assertRaises(SimulationBetEvaluationError) as caught:
                self.build()
        self.assertIs(caught.exception.__cause__, original)

    def test_converts_simulation_result_value_error_and_preserves_cause(self) -> None:
        original = ValueError("constructor value failure")
        with patch.object(simulator, "SimulationResult", side_effect=original):
            with self.assertRaises(SimulationBetEvaluationError) as caught:
                self.build()
        self.assertIs(caught.exception.__cause__, original)

    def test_returns_no_partial_result_on_constructor_failure(self) -> None:
        with patch.object(simulator, "SimulationResult", side_effect=ValueError("failure")):
            with self.assertRaises(SimulationBetEvaluationError):
                self.build()

    def test_does_not_call_evaluation_helpers(self) -> None:
        with patch.object(simulator, "_evaluate_simulation_bet", side_effect=AssertionError("must not run")), patch.object(simulator, "_evaluate_simulation_race_bets", side_effect=AssertionError("must not run")):
            self.assertIsInstance(self.build(), SimulationResult)

    def test_does_not_call_settled_or_no_bet_builders(self) -> None:
        with patch.object(simulator, "_build_settled_simulation_result", side_effect=AssertionError("must not run")), patch.object(simulator, "_build_no_bet_simulation_result", side_effect=AssertionError("must not run")):
            self.assertIsInstance(self.build(), SimulationResult)

    def test_does_not_use_current_time(self) -> None:
        source = inspect.getsource(_build_non_settled_simulation_result)
        self.assertNotIn("datetime.now", source)
        self.assertNotIn("datetime.utcnow", source)

    def test_has_no_provider_repository_database_network_or_metrics_dependency(self) -> None:
        source = inspect.getsource(_build_non_settled_simulation_result)
        lower = source.lower()
        self.assertNotIn("provider", lower)
        self.assertNotIn("repository", lower)
        self.assertNotIn("sqlite", lower)
        self.assertNotIn("roi", lower)
        self.assertNotIn("drawdown", lower)
        module_source = Path(inspect.getsourcefile(_build_non_settled_simulation_result)).read_text(encoding="utf-8")
        self.assertNotIn("requests", module_source)

    def test_internal_helper_is_not_exported_from_package_root(self) -> None:
        self.assertNotIn("_build_non_settled_simulation_result", simulation_package.__all__)
        self.assertFalse(hasattr(simulation_package, "_build_non_settled_simulation_result"))


if __name__ == "__main__":
    unittest.main()
