"""Pure aggregation contract for SimulationSummary."""
from __future__ import annotations

from dataclasses import fields
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import inspect
from types import MappingProxyType
from unittest.mock import patch
import unittest

import scripts.simulation.simulator as simulator
from scripts.simulation.models import SettlementStatus, SimulationBet, SimulationResult, SimulationSummary
from scripts.simulation.repositories.interfaces import PayoutPublication, PayoutRecord, PayoutStatus
from scripts.simulation.simulator import (
    SimulationBetEvaluationError,
    _build_no_bet_simulation_result,
    _build_non_settled_simulation_result,
    _build_settled_simulation_result,
    _build_simulation_summary,
    _evaluate_simulation_race_bets,
)


NOW = datetime(2026, 7, 24, 12, 0, tzinfo=UTC)
HASH = "a" * 64


def bet(
    race_id: int,
    *,
    bet_type: str = "単勝",
    selection: tuple[int, ...] = (11,),
    stake: int = 100,
) -> SimulationBet:
    return SimulationBet(race_id, "strategy-a", bet_type, selection, stake, 1, NOW)


def settled(
    race_id: int,
    *,
    payout_per_100: int = 200,
    settled_at: datetime | None = None,
    bet_type: str = "単勝",
    selection: tuple[int, ...] = (11,),
    stake: int = 100,
    strategy_id: str = "strategy-a",
) -> SimulationResult:
    item = SimulationBet(race_id, strategy_id, bet_type, selection, stake, 1, NOW)
    publication = PayoutPublication(
        race_id, bet_type, NOW, NOW, True, "official",
        (
            PayoutRecord(
                item.race_entry_ids,
                payout_per_100,
                PayoutStatus.WINNING if payout_per_100 > 0 else PayoutStatus.VOID,
            ),
        ),
    )
    evaluated = _evaluate_simulation_race_bets(race_id, strategy_id, (item,), {bet_type: publication})
    return _build_settled_simulation_result(evaluated, settled_at or NOW + timedelta(minutes=race_id))


def non_settled(
    race_id: int,
    *,
    status: SettlementStatus = SettlementStatus.UNSETTLED,
    bet_type: str = "単勝",
    selection: tuple[int, ...] = (11,),
    stake: int = 100,
) -> SimulationResult:
    return _build_non_settled_simulation_result(
        race_id=race_id,
        strategy_id="strategy-a",
        bets=(bet(race_id, bet_type=bet_type, selection=selection, stake=stake),),
        settlement_status=status,
        exclusion_reason="unavailable",
    )


def no_bet(race_id: int) -> SimulationResult:
    return _build_no_bet_simulation_result(race_id, "strategy-a")


def summary(results: object = ()) -> SimulationSummary:
    return _build_simulation_summary(
        strategy_id="strategy-a",
        strategy_name="Strategy A",
        strategy_config_hash=HASH,
        results=results,  # type: ignore[arg-type]
    )


class SimulationSummaryBuilderTests(unittest.TestCase):
    def test_signature_is_keyword_only(self) -> None:
        signature = inspect.signature(_build_simulation_summary)
        self.assertEqual(tuple(signature.parameters), ("strategy_id", "strategy_name", "strategy_config_hash", "results"))
        self.assertTrue(all(item.kind is inspect.Parameter.KEYWORD_ONLY for item in signature.parameters.values()))

    def test_returns_simulation_summary(self) -> None:
        self.assertIsInstance(summary(), SimulationSummary)

    def test_empty_results_has_zero_race_count(self) -> None:
        self.assertEqual(summary().race_count, 0)

    def test_empty_results_has_zero_money(self) -> None:
        self.assertEqual((summary().investment, summary().payout, summary().profit), (0, 0, 0))

    def test_empty_results_has_none_rates(self) -> None:
        result = summary()
        self.assertEqual((result.roi, result.bet_hit_rate, result.race_hit_rate), (None, None, None))

    def test_empty_results_has_zero_drawdown(self) -> None:
        self.assertEqual(summary().maximum_drawdown, 0)

    def test_empty_results_has_empty_immutable_mapping(self) -> None:
        result = summary()
        self.assertIsInstance(result.by_bet_type, MappingProxyType)
        self.assertEqual(dict(result.by_bet_type), {})

    def test_preserves_strategy_id(self) -> None:
        self.assertEqual(summary().strategy_id, "strategy-a")

    def test_preserves_strategy_name(self) -> None:
        self.assertEqual(summary().strategy_name, "Strategy A")

    def test_preserves_strategy_config_hash(self) -> None:
        self.assertEqual(summary().strategy_config_hash, HASH)

    def test_rejects_non_sequence_results(self) -> None:
        for value in (None, 1, {}, object()):
            with self.subTest(value=value), self.assertRaises(SimulationBetEvaluationError):
                summary(value)

    def test_rejects_string_results(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            summary("results")

    def test_rejects_bytes_results(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            summary(b"results")

    def test_rejects_non_result_element(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            summary((object(),))

    def test_rejects_empty_strategy_id(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            _build_simulation_summary(strategy_id="", strategy_name="Strategy A", strategy_config_hash=HASH, results=())

    def test_rejects_whitespace_strategy_id(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            _build_simulation_summary(strategy_id="   ", strategy_name="Strategy A", strategy_config_hash=HASH, results=())

    def test_rejects_non_string_strategy_id(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            _build_simulation_summary(strategy_id=1, strategy_name="Strategy A", strategy_config_hash=HASH, results=())  # type: ignore[arg-type]

    def test_rejects_empty_strategy_name(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            _build_simulation_summary(strategy_id="strategy-a", strategy_name="", strategy_config_hash=HASH, results=())

    def test_rejects_whitespace_strategy_name(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            _build_simulation_summary(strategy_id="strategy-a", strategy_name="   ", strategy_config_hash=HASH, results=())

    def test_rejects_non_string_strategy_name(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            _build_simulation_summary(strategy_id="strategy-a", strategy_name=1, strategy_config_hash=HASH, results=())  # type: ignore[arg-type]

    def test_rejects_empty_hash(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            _build_simulation_summary(strategy_id="strategy-a", strategy_name="Strategy A", strategy_config_hash="", results=())

    def test_rejects_malformed_hash(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            _build_simulation_summary(strategy_id="strategy-a", strategy_name="Strategy A", strategy_config_hash="A" * 64, results=())

    def test_rejects_non_string_hash(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            _build_simulation_summary(strategy_id="strategy-a", strategy_name="Strategy A", strategy_config_hash=1, results=())  # type: ignore[arg-type]

    def test_rejects_result_strategy_mismatch(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            summary((settled(1, strategy_id="other"),))

    def test_rejects_duplicate_race_ids(self) -> None:
        first, second = settled(1), non_settled(1)
        with self.assertRaises(SimulationBetEvaluationError):
            summary((first, second))

    def test_counts_settled_status(self) -> None:
        self.assertEqual(summary((settled(1),)).settled_race_count, 1)

    def test_counts_no_bet_status(self) -> None:
        self.assertEqual(summary((no_bet(1),)).no_bet_race_count, 1)

    def test_counts_unsettled_status(self) -> None:
        self.assertEqual(summary((non_settled(1),)).unsettled_race_count, 1)

    def test_counts_void_status(self) -> None:
        self.assertEqual(summary((non_settled(1, status=SettlementStatus.VOID),)).void_race_count, 1)

    def test_counts_error_status(self) -> None:
        self.assertEqual(summary((non_settled(1, status=SettlementStatus.ERROR),)).error_race_count, 1)

    def test_counts_unsupported_status(self) -> None:
        self.assertEqual(summary((non_settled(1, status=SettlementStatus.UNSUPPORTED),)).unsupported_race_count, 1)

    def test_counts_all_statuses_in_race_count(self) -> None:
        results = (settled(1), no_bet(2), non_settled(3), non_settled(4, status=SettlementStatus.VOID), non_settled(5, status=SettlementStatus.ERROR), non_settled(6, status=SettlementStatus.UNSUPPORTED))
        self.assertEqual(summary(results).race_count, 6)

    def test_settled_purchase_count_includes_settled_purchase_only(self) -> None:
        self.assertEqual(summary((settled(1), no_bet(2), non_settled(3))).settled_purchase_race_count, 1)

    def test_bet_count_includes_non_settled_bets(self) -> None:
        self.assertEqual(summary((settled(1), non_settled(2))).bet_count, 2)

    def test_settled_bet_count_excludes_non_settled_bets(self) -> None:
        self.assertEqual(summary((settled(1), non_settled(2))).settled_bet_count, 1)

    def test_money_uses_settled_results_only(self) -> None:
        result = summary((settled(1, payout_per_100=200), non_settled(2, stake=300)))
        self.assertEqual((result.investment, result.payout, result.profit), (100, 200, 100))

    def test_profit_equals_payout_minus_investment(self) -> None:
        result = summary((settled(1),))
        self.assertEqual(result.profit, result.payout - result.investment)

    def test_roi_is_decimal_percentage(self) -> None:
        self.assertEqual(summary((settled(1, payout_per_100=125),)).roi, Decimal("125"))

    def test_roi_is_none_with_no_settled_investment(self) -> None:
        self.assertIsNone(summary((no_bet(1), non_settled(2))).roi)

    def test_hit_race_count_uses_settled_winning_races(self) -> None:
        self.assertEqual(summary((settled(1), settled(2, payout_per_100=0))).hit_race_count, 1)

    def test_race_hit_rate_is_decimal_percentage(self) -> None:
        self.assertEqual(summary((settled(1), settled(2, payout_per_100=0))).race_hit_rate, Decimal("50"))

    def test_race_hit_rate_is_none_without_settled_purchase(self) -> None:
        self.assertIsNone(summary((no_bet(1),)).race_hit_rate)

    def test_bet_hit_rate_is_decimal_percentage(self) -> None:
        self.assertEqual(summary((settled(1), settled(2, payout_per_100=0))).bet_hit_rate, Decimal("50"))

    def test_bet_hit_rate_is_none_without_settled_bets(self) -> None:
        self.assertIsNone(summary((non_settled(1),)).bet_hit_rate)

    def test_drawdown_is_zero_for_empty_results(self) -> None:
        self.assertEqual(summary().maximum_drawdown, 0)

    def test_drawdown_is_zero_for_all_winning_results(self) -> None:
        self.assertEqual(summary((settled(1), settled(2))).maximum_drawdown, 0)

    def test_drawdown_counts_initial_loss(self) -> None:
        self.assertEqual(summary((settled(1, payout_per_100=0),)).maximum_drawdown, 100)

    def test_drawdown_ignores_no_bet_and_non_settled_results(self) -> None:
        value = summary((settled(1, payout_per_100=0), no_bet(2), non_settled(3))).maximum_drawdown
        self.assertEqual(value, 100)

    def test_drawdown_sorts_by_settled_at(self) -> None:
        later = settled(1, payout_per_100=0, settled_at=NOW + timedelta(hours=2))
        earlier = settled(2, payout_per_100=200, settled_at=NOW + timedelta(hours=1))
        self.assertEqual(summary((later, earlier)).maximum_drawdown, 100)

    def test_drawdown_uses_race_id_for_equal_settled_at(self) -> None:
        same_time = NOW + timedelta(hours=1)
        first = settled(1, payout_per_100=200, settled_at=same_time)
        second = settled(2, payout_per_100=0, settled_at=same_time)
        self.assertEqual(summary((second, first)).maximum_drawdown, 100)

    def test_drawdown_is_independent_of_input_order(self) -> None:
        results = (settled(1, payout_per_100=0), settled(2, payout_per_100=200), settled(3, payout_per_100=0))
        self.assertEqual(summary(results).maximum_drawdown, summary(tuple(reversed(results))).maximum_drawdown)

    def test_drawdown_does_not_mutate_input_list(self) -> None:
        results = [settled(2), settled(1, payout_per_100=0)]
        before = tuple(results)
        summary(results)
        self.assertEqual(tuple(results), before)

    def test_by_bet_type_aggregates_all_four_types(self) -> None:
        results = (
            settled(1), settled(2, bet_type="馬連", selection=(11, 12)),
            settled(3, bet_type="ワイド", selection=(11, 12)),
            settled(4, bet_type="3連複", selection=(11, 12, 13)),
        )
        self.assertEqual(set(summary(results).by_bet_type), {"単勝", "馬連", "ワイド", "3連複"})

    def test_by_bet_type_includes_non_settled_bet_count(self) -> None:
        self.assertEqual(summary((settled(1), non_settled(2))).by_bet_type["単勝"].bet_count, 2)

    def test_by_bet_type_excludes_non_settled_money(self) -> None:
        self.assertEqual(summary((settled(1), non_settled(2, stake=300))).by_bet_type["単勝"].investment, 100)

    def test_by_bet_type_uses_decimal_roi(self) -> None:
        self.assertEqual(summary((settled(1, payout_per_100=125),)).by_bet_type["単勝"].roi, Decimal("125"))

    def test_by_bet_type_uses_none_rates_without_settlement(self) -> None:
        item = summary((non_settled(1),)).by_bet_type["単勝"]
        self.assertEqual((item.roi, item.bet_hit_rate), (None, None))

    def test_by_bet_type_mapping_order_is_deterministic(self) -> None:
        results = (settled(1, bet_type="馬連", selection=(11, 12)), settled(2))
        result = summary(tuple(reversed(results)))
        self.assertEqual(tuple(result.by_bet_type), tuple(sorted(result.by_bet_type)))

    def test_by_bet_type_mapping_is_immutable(self) -> None:
        with self.assertRaises(TypeError):
            summary((settled(1),)).by_bet_type["馬連"] = object()  # type: ignore[index]

    def test_by_bet_type_totals_match_summary(self) -> None:
        result = summary((settled(1), non_settled(2, bet_type="馬連", selection=(11, 12))))
        self.assertEqual(sum(item.bet_count for item in result.by_bet_type.values()), result.bet_count)

    def test_summary_constructor_errors_are_converted(self) -> None:
        original = ValueError("summary failure")
        with patch.object(simulator, "SimulationSummary", side_effect=original):
            with self.assertRaises(SimulationBetEvaluationError) as caught:
                summary(())
        self.assertIs(caught.exception.__cause__, original)

    def test_helper_does_not_call_atomic_evaluation(self) -> None:
        result = settled(1)
        with patch.object(simulator, "_evaluate_simulation_bet", side_effect=AssertionError("must not evaluate")):
            self.assertEqual(summary((result,)).race_count, 1)

    def test_helper_does_not_call_race_orchestration(self) -> None:
        result = settled(1)
        with patch.object(simulator, "_build_simulation_result_for_race", side_effect=AssertionError("must not orchestrate")):
            self.assertEqual(summary((result,)).race_count, 1)

    def test_helper_does_not_call_result_builders(self) -> None:
        result = settled(1)
        with patch.object(simulator, "_build_settled_simulation_result", side_effect=AssertionError("must not build")):
            self.assertEqual(summary((result,)).race_count, 1)

    def test_helper_source_has_no_provider_or_repository_dependency(self) -> None:
        source = inspect.getsource(_build_simulation_summary)
        self.assertNotIn("Provider", source)
        self.assertNotIn("Repository", source)
        self.assertNotIn("sqlite", source.lower())
        self.assertNotIn("requests", source)

    def test_helper_source_does_not_use_current_time_or_logging(self) -> None:
        source = inspect.getsource(_build_simulation_summary)
        self.assertNotIn("datetime.now", source)
        self.assertNotIn("logging", source.lower())

    def test_summary_builder_formally_handles_drawdown(self) -> None:
        source = inspect.getsource(_build_simulation_summary)
        self.assertIn("_maximum_drawdown", source)
        self.assertNotIn("_evaluate_simulation_bet", source)

    def test_summary_has_no_atomic_evaluation_fields(self) -> None:
        names = {item.name for item in fields(SimulationSummary)}
        self.assertFalse({"matched_record", "payout_status", "odds", "selection_key"} & names)


if __name__ == "__main__":
    unittest.main()
