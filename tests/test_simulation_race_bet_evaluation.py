"""Tests for private, one-race atomic-bet evaluation."""
from __future__ import annotations

from datetime import UTC, datetime
import inspect
from pathlib import Path
from unittest.mock import patch
import unittest

import scripts.simulation as simulation_package
import scripts.simulation.simulator as simulator
from scripts.simulation.models import SimulationBet
from scripts.simulation.repositories.interfaces import PayoutPublication, PayoutRecord, PayoutStatus
from scripts.simulation.simulator import (
    SimulationBetEvaluationError,
    _EvaluatedSimulationRaceBets,
    _evaluate_simulation_race_bets,
)


NOW = datetime(2026, 7, 22, 12, 0, tzinfo=UTC)


def bet(bet_type: str, selection: tuple[int, ...], *, stake: int = 100, strategy: str = "strategy-a") -> SimulationBet:
    return SimulationBet(1, strategy, bet_type, selection, stake, 1, NOW)


def publication(
    bet_type: str,
    entries: tuple[PayoutRecord, ...],
    *,
    race_id: int = 1,
    complete: bool = True,
) -> PayoutPublication:
    return PayoutPublication(race_id, bet_type, NOW if complete else None, NOW, complete, "official", entries)


def winning_publication(item: SimulationBet, payout_per_100: int = 200) -> PayoutPublication:
    return publication(item.bet_type, (PayoutRecord(item.race_entry_ids, payout_per_100, PayoutStatus.WINNING),))


class SimulationRaceBetEvaluationTests(unittest.TestCase):
    def evaluate(self, items: tuple[SimulationBet, ...], mapping: dict[str, PayoutPublication] | None = None):
        publications = mapping if mapping is not None else {item.bet_type: winning_publication(item) for item in items}
        return _evaluate_simulation_race_bets(1, "strategy-a", items, publications)

    def test_evaluates_single_bet_race(self) -> None:
        item = bet("単勝", (11,))
        result = self.evaluate((item,))
        self.assertEqual((result.investment, result.payout, result.profit, result.hit_bet_count), (100, 200, 100, 1))

    def test_evaluates_multiple_bets_same_type(self) -> None:
        first, second = bet("馬連", (11, 12)), bet("馬連", (11, 13), stake=200)
        result = self.evaluate((first, second), {"馬連": publication("馬連", (
            PayoutRecord((11, 12), 200, PayoutStatus.WINNING),
            PayoutRecord((11, 13), 300, PayoutStatus.WINNING),
        ))})
        self.assertEqual((result.investment, result.payout, result.profit), (300, 800, 500))

    def test_evaluates_all_four_bet_types(self) -> None:
        items = (bet("単勝", (11,)), bet("馬連", (11, 12)), bet("ワイド", (11, 12)), bet("3連複", (11, 12, 13)))
        result = self.evaluate(items)
        self.assertEqual(result.hit_bet_count, 4)
        self.assertEqual(len(result.evaluations), 4)

    def test_returns_internal_race_evaluation_model(self) -> None:
        self.assertIsInstance(self.evaluate((bet("単勝", (11,)),)), _EvaluatedSimulationRaceBets)

    def test_preserves_bet_input_order(self) -> None:
        items = (bet("ワイド", (11, 12)), bet("単勝", (11,)), bet("馬連", (11, 12)))
        self.assertEqual(self.evaluate(items).bets, items)

    def test_preserves_original_bet_objects(self) -> None:
        items = (bet("単勝", (11,)), bet("馬連", (11, 12)))
        result = self.evaluate(items)
        self.assertIs(result.bets[0], items[0])
        self.assertIs(result.bets[1], items[1])

    def test_preserves_single_evaluation_objects(self) -> None:
        item = bet("単勝", (11,))
        result = self.evaluate((item,))
        self.assertIs(result.evaluations[0].bet, item)

    def test_calls_single_bet_helper_once_per_bet(self) -> None:
        items = (bet("単勝", (11,)), bet("馬連", (11, 12)))
        with patch.object(simulator, "_evaluate_simulation_bet", wraps=simulator._evaluate_simulation_bet) as helper:
            self.evaluate(items)
        self.assertEqual(helper.call_count, 2)

    def test_calls_single_bet_helper_in_input_order(self) -> None:
        items = (bet("ワイド", (11, 12)), bet("単勝", (11,)))
        with patch.object(simulator, "_evaluate_simulation_bet", wraps=simulator._evaluate_simulation_bet) as helper:
            self.evaluate(items)
        self.assertEqual(tuple(call.args[0] for call in helper.call_args_list), items)

    def test_routes_each_bet_to_matching_publication(self) -> None:
        win, quinella = bet("単勝", (11,)), bet("馬連", (11, 12))
        mapping = {"単勝": winning_publication(win), "馬連": winning_publication(quinella)}
        with patch.object(simulator, "_evaluate_simulation_bet", wraps=simulator._evaluate_simulation_bet) as helper:
            self.evaluate((win, quinella), mapping)
        self.assertIs(helper.call_args_list[0].args[1], mapping["単勝"])
        self.assertIs(helper.call_args_list[1].args[1], mapping["馬連"])

    def test_reuses_same_publication_for_same_bet_type(self) -> None:
        first, second = bet("馬連", (11, 12)), bet("馬連", (11, 13))
        shared = publication("馬連", (
            PayoutRecord((11, 12), 200, PayoutStatus.WINNING), PayoutRecord((11, 13), 200, PayoutStatus.WINNING),
        ))
        with patch.object(simulator, "_evaluate_simulation_bet", wraps=simulator._evaluate_simulation_bet) as helper:
            self.evaluate((first, second), {"馬連": shared})
        self.assertIs(helper.call_args_list[0].args[1], shared)
        self.assertIs(helper.call_args_list[1].args[1], shared)

    def test_sums_investment_payout_and_profit(self) -> None:
        win, quinella = bet("単勝", (11,), stake=100), bet("馬連", (11, 12), stake=300)
        result = self.evaluate((win, quinella), {"単勝": winning_publication(win, 200), "馬連": winning_publication(quinella, 1250)})
        self.assertEqual((result.investment, result.payout, result.profit), (400, 3950, 3550))

    def test_profit_equals_payout_minus_investment(self) -> None:
        result = self.evaluate((bet("単勝", (11,)),))
        self.assertEqual(result.profit, result.payout - result.investment)

    def test_counts_hit_bets(self) -> None:
        win, refund = bet("単勝", (11,)), bet("馬連", (11, 12))
        result = self.evaluate((win, refund), {"単勝": winning_publication(win), "馬連": publication("馬連", (PayoutRecord((11, 12), 100, PayoutStatus.REFUND),))})
        self.assertEqual(result.hit_bet_count, 1)

    def test_refund_and_void_hit_semantics_are_not_reinterpreted(self) -> None:
        refund, void = bet("馬連", (11, 12)), bet("ワイド", (11, 12))
        result = self.evaluate((refund, void), {
            "馬連": publication("馬連", (PayoutRecord((11, 12), 100, PayoutStatus.REFUND),)),
            "ワイド": publication("ワイド", (PayoutRecord((11, 12), 0, PayoutStatus.VOID),)),
        })
        self.assertEqual((result.hit_bet_count, result.payout, result.profit), (0, 100, -100))

    def test_complete_losing_bets_are_aggregated(self) -> None:
        item = bet("馬連", (11, 12), stake=200)
        result = self.evaluate((item,), {"馬連": publication("馬連", (PayoutRecord((11, 13), 200, PayoutStatus.WINNING),))})
        self.assertEqual((result.payout, result.profit, result.hit_bet_count), (0, -200, 0))

    def test_rejects_invalid_race_id(self) -> None:
        for race_id in (0, -1, True, "1"):
            with self.subTest(race_id=race_id), self.assertRaises(SimulationBetEvaluationError):
                _evaluate_simulation_race_bets(race_id, "strategy-a", (bet("単勝", (11,)),), {"単勝": winning_publication(bet("単勝", (11,)))})

    def test_rejects_invalid_strategy_id(self) -> None:
        for strategy in ("", None, 1):
            with self.subTest(strategy=strategy), self.assertRaises(SimulationBetEvaluationError):
                _evaluate_simulation_race_bets(1, strategy, (bet("単勝", (11,)),), {"単勝": winning_publication(bet("単勝", (11,)))})

    def test_rejects_empty_bets(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            _evaluate_simulation_race_bets(1, "strategy-a", tuple(), {})

    def test_rejects_non_simulation_bet_item(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            _evaluate_simulation_race_bets(1, "strategy-a", ("not-a-bet",), {})  # type: ignore[arg-type]

    def test_rejects_bet_race_and_strategy_mismatch(self) -> None:
        other_race = SimulationBet(2, "strategy-a", "単勝", (11,), 100, 1, NOW)
        other_strategy = bet("単勝", (11,), strategy="other")
        for item in (other_race, other_strategy):
            with self.subTest(item=item), self.assertRaises(SimulationBetEvaluationError):
                _evaluate_simulation_race_bets(1, "strategy-a", (item,), {"単勝": winning_publication(item)})

    def test_rejects_duplicate_identity_ignoring_stake_difference(self) -> None:
        first, second = bet("馬連", (11, 12), stake=100), bet("馬連", (12, 11), stake=200)
        with self.assertRaises(SimulationBetEvaluationError):
            _evaluate_simulation_race_bets(1, "strategy-a", (first, second), {"馬連": winning_publication(first)})

    def test_allows_same_pair_for_quinella_and_wide(self) -> None:
        quinella, wide = bet("馬連", (11, 12)), bet("ワイド", (11, 12))
        self.assertEqual(len(self.evaluate((quinella, wide)).bets), 2)

    def test_rejects_non_mapping_publications(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            _evaluate_simulation_race_bets(1, "strategy-a", (bet("単勝", (11,)),), [])  # type: ignore[arg-type]

    def test_rejects_invalid_publication_key(self) -> None:
        item = bet("単勝", (11,))
        with self.assertRaises(SimulationBetEvaluationError):
            _evaluate_simulation_race_bets(1, "strategy-a", (item,), {"複勝": winning_publication(item)})

    def test_rejects_non_publication_value(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            _evaluate_simulation_race_bets(1, "strategy-a", (bet("単勝", (11,)),), {"単勝": "not-a-publication"})  # type: ignore[arg-type]

    def test_rejects_key_publication_bet_type_mismatch(self) -> None:
        wrong = publication("馬連", (PayoutRecord((11, 12), 200, PayoutStatus.WINNING),))
        with self.assertRaises(SimulationBetEvaluationError):
            _evaluate_simulation_race_bets(1, "strategy-a", (bet("単勝", (11,)),), {"単勝": wrong})

    def test_rejects_publication_race_mismatch(self) -> None:
        item = bet("単勝", (11,))
        wrong = publication("単勝", (PayoutRecord((11,), 200, PayoutStatus.WINNING),), race_id=2)
        with self.assertRaises(SimulationBetEvaluationError):
            _evaluate_simulation_race_bets(1, "strategy-a", (item,), {"単勝": wrong})

    def test_rejects_missing_and_extra_publications(self) -> None:
        win, quinella = bet("単勝", (11,)), bet("馬連", (11, 12))
        with self.assertRaises(SimulationBetEvaluationError):
            self.evaluate((win, quinella), {"単勝": winning_publication(win)})
        with self.assertRaises(SimulationBetEvaluationError):
            self.evaluate((win,), {"単勝": winning_publication(win), "馬連": winning_publication(quinella)})

    def test_fails_closed_when_one_bet_is_unsupported(self) -> None:
        win, quinella = bet("単勝", (11,)), bet("馬連", (11, 12))
        mapping = {
            "単勝": winning_publication(win),
            "馬連": publication("馬連", (PayoutRecord((11, 12), 0, PayoutStatus.UNSUPPORTED),)),
        }
        with self.assertRaises(SimulationBetEvaluationError):
            self.evaluate((win, quinella), mapping)

    def test_fails_closed_when_one_publication_is_incomplete_without_match(self) -> None:
        win, quinella = bet("単勝", (11,)), bet("馬連", (11, 12))
        mapping = {
            "単勝": winning_publication(win),
            "馬連": publication("馬連", (PayoutRecord((11, 13), 100, PayoutStatus.WINNING),), complete=False),
        }
        with self.assertRaises(SimulationBetEvaluationError):
            self.evaluate((win, quinella), mapping)

    def test_propagates_same_single_bet_evaluation_error(self) -> None:
        item = bet("単勝", (11,))
        expected = SimulationBetEvaluationError("single failure")
        with patch.object(simulator, "_evaluate_simulation_bet", side_effect=expected):
            with self.assertRaises(SimulationBetEvaluationError) as caught:
                self.evaluate((item,))
        self.assertIs(caught.exception, expected)

    def test_does_not_mutate_bets_input_or_publications_mapping(self) -> None:
        items = [bet("単勝", (11,))]
        mapping = {"単勝": winning_publication(items[0])}
        _evaluate_simulation_race_bets(1, "strategy-a", items, mapping)
        self.assertEqual(items, [items[0]])
        self.assertEqual(mapping, {"単勝": mapping["単勝"]})

    def test_has_no_provider_repository_database_or_network_dependency(self) -> None:
        source = Path(inspect.getsourcefile(_evaluate_simulation_race_bets)).read_text(encoding="utf-8")
        self.assertNotIn("sqlite3", source)
        self.assertNotIn("providers", source)
        self.assertNotIn("repositories.sqlite", source)
        self.assertNotIn("requests", source)

    def test_does_not_create_simulation_result_or_calculate_roi_or_drawdown(self) -> None:
        source = inspect.getsource(_evaluate_simulation_race_bets)
        self.assertNotIn("SimulationResult", source)
        self.assertNotIn("roi", source.lower())
        self.assertNotIn("drawdown", source.lower())

    def test_internal_helpers_are_not_exported_from_package_root(self) -> None:
        self.assertNotIn("_evaluate_simulation_race_bets", simulation_package.__all__)
        self.assertFalse(hasattr(simulation_package, "_evaluate_simulation_race_bets"))
        self.assertNotIn("_EvaluatedSimulationRaceBets", simulation_package.__all__)


if __name__ == "__main__":
    unittest.main()
