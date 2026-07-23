"""SimulationBet's multi-type atomic-bet contract."""
from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from datetime import UTC, datetime
import inspect
from pathlib import Path
import subprocess
import sys
import unittest

from scripts.simulation.models import BetTypeSummary, SettlementStatus, SimulationBet, SimulationResult
from scripts.simulation.repositories.interfaces import normalize_selection


NOW = datetime(2026, 7, 21, 12, 0, tzinfo=UTC)


def make_bet(
    bet_type: str = "単勝",
    selection: object = (11,),
    *,
    stake: int = 100,
    rank: int = 1,
) -> SimulationBet:
    return SimulationBet(1, "strategy-a", bet_type, selection, stake, rank, NOW)


class SimulationBetMultiTypeTests(unittest.TestCase):
    def test_constructs_win_bet(self) -> None:
        self.assertEqual(make_bet().race_entry_ids, (11,))

    def test_constructs_quinella_bet(self) -> None:
        self.assertEqual(make_bet("馬連", [3, 1]).race_entry_ids, (1, 3))

    def test_constructs_wide_bet(self) -> None:
        self.assertEqual(make_bet("ワイド", (4, 2)).race_entry_ids, (2, 4))

    def test_constructs_trio_bet(self) -> None:
        self.assertEqual(make_bet("3連複", [5, 1, 3]).race_entry_ids, (1, 3, 5))

    def test_preserves_field_and_constructor_order(self) -> None:
        self.assertEqual(
            tuple(item.name for item in fields(SimulationBet)),
            ("race_id", "strategy_id", "bet_type", "race_entry_ids", "stake", "recommendation_rank", "placed_at_cutoff"),
        )
        signature = inspect.signature(SimulationBet)
        self.assertEqual(tuple(signature.parameters), tuple(item.name for item in fields(SimulationBet)))

    def test_is_frozen(self) -> None:
        bet = make_bet()
        with self.assertRaises(FrozenInstanceError):
            bet.stake = 200  # type: ignore[misc]

    def test_accepts_list_and_tuple_input(self) -> None:
        self.assertEqual(make_bet("馬連", [2, 1]).race_entry_ids, (1, 2))
        self.assertEqual(make_bet("馬連", (2, 1)).race_entry_ids, (1, 2))

    def test_canonicalizes_to_a_tuple(self) -> None:
        self.assertIsInstance(make_bet("3連複", [3, 1, 2]).race_entry_ids, tuple)

    def test_reuses_repository_bet_type_validation(self) -> None:
        self.assertIn("validate_bet_type", SimulationBet.__post_init__.__code__.co_names)
        with self.assertRaisesRegex(ValueError, "unsupported bet_type"):
            make_bet("複勝", (11,))

    def test_reuses_repository_selection_normalization(self) -> None:
        bet = make_bet("3連複", [3, 1, 2])
        self.assertIn("normalize_selection", SimulationBet.__post_init__.__code__.co_names)
        self.assertEqual(bet.race_entry_ids, normalize_selection([3, 1, 2], "3連複"))

    def test_rejects_each_bet_type_selection_count_mismatch(self) -> None:
        cases = (("単勝", (1, 2)), ("馬連", (1,)), ("ワイド", (1,)), ("3連複", (1, 2)))
        for bet_type, selection in cases:
            with self.subTest(bet_type=bet_type, selection=selection), self.assertRaises(ValueError):
                make_bet(bet_type, selection)

    def test_rejects_duplicate_selection_ids(self) -> None:
        with self.assertRaises(ValueError):
            make_bet("馬連", (1, 1))

    def test_rejects_zero_negative_and_bool_selection_ids(self) -> None:
        for selection in ((0,), (-1,), (True,)):
            with self.subTest(selection=selection), self.assertRaises(ValueError):
                make_bet("単勝", selection)

    def test_rejects_non_integer_selection_ids(self) -> None:
        for selection in ((1.0,), ("1",), (None,)):
            with self.subTest(selection=selection), self.assertRaises(ValueError):
                make_bet("単勝", selection)

    def test_rejects_non_100_yen_stake(self) -> None:
        with self.assertRaisesRegex(ValueError, "multiple of 100"):
            make_bet(stake=50)

    def test_rejects_zero_negative_and_bool_stake(self) -> None:
        for stake in (0, -100, True):
            with self.subTest(stake=stake), self.assertRaises(ValueError):
                make_bet(stake=stake)

    def test_rejects_negative_or_bool_recommendation_rank(self) -> None:
        for rank in (-1, True):
            with self.subTest(rank=rank), self.assertRaises(ValueError):
                make_bet(rank=rank)

    def test_rejects_naive_datetime(self) -> None:
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            SimulationBet(1, "strategy-a", "単勝", (11,), 100, 1, datetime(2026, 7, 21, 12, 0))

    def test_does_not_mutate_input_collection(self) -> None:
        selection = [3, 1]
        make_bet("馬連", selection)
        self.assertEqual(selection, [3, 1])

    def test_equality_and_hash_use_canonical_selection(self) -> None:
        first = make_bet("馬連", [3, 1])
        second = make_bet("馬連", (1, 3))
        self.assertEqual(first, second)
        self.assertEqual(hash(first), hash(second))

    def test_simulation_result_rejects_duplicate_identity_despite_stake_or_rank(self) -> None:
        first = make_bet("馬連", (1, 2), stake=100, rank=1)
        second = make_bet("馬連", (2, 1), stake=200, rank=2)
        with self.assertRaisesRegex(ValueError, "duplicate selections"):
            SimulationResult(1, "strategy-a", (first, second), SettlementStatus.UNSETTLED, "pending", 300, by_bet_type={"馬連": BetTypeSummary("馬連", 2, 0, 0, 0, 0, 0, None, None)})

    def test_simulation_result_allows_quinella_and_wide_for_same_pair(self) -> None:
        quinella = make_bet("馬連", (1, 2))
        wide = make_bet("ワイド", (2, 1))
        result = SimulationResult(1, "strategy-a", (quinella, wide), SettlementStatus.UNSETTLED, "pending", 200, by_bet_type={
            "馬連": BetTypeSummary("馬連", 1, 0, 0, 0, 0, 0, None, None),
            "ワイド": BetTypeSummary("ワイド", 1, 0, 0, 0, 0, 0, None, None),
        })
        self.assertEqual(len(result.bets), 2)

    def test_simulation_result_allows_different_selections_for_same_bet_type(self) -> None:
        first = make_bet("馬連", (1, 2))
        second = make_bet("馬連", (1, 3))
        result = SimulationResult(1, "strategy-a", (first, second), SettlementStatus.UNSETTLED, "pending", 200, by_bet_type={"馬連": BetTypeSummary("馬連", 2, 0, 0, 0, 0, 0, None, None)})
        self.assertEqual(tuple(item.race_entry_ids for item in result.bets), ((1, 2), (1, 3)))

    def test_does_not_store_selection_key_odds_or_payout(self) -> None:
        names = {item.name for item in fields(SimulationBet)}
        self.assertNotIn("selection_key", names)
        self.assertNotIn("odds", names)
        self.assertNotIn("payout", names)

    def test_simulation_bet_has_no_provider_database_or_network_dependency(self) -> None:
        source = inspect.getsource(SimulationBet)
        self.assertNotIn("Provider", source)
        self.assertNotIn("sqlite", source.lower())
        self.assertNotIn("requests", source.lower())

    def test_models_and_repository_interfaces_import_in_both_orders(self) -> None:
        commands = (
            "import scripts.simulation.models; import scripts.simulation.repositories.interfaces",
            "import scripts.simulation.repositories.interfaces; import scripts.simulation.models",
        )
        for command in commands:
            with self.subTest(command=command):
                completed = subprocess.run([sys.executable, "-c", command], capture_output=True, text=True, check=False)
                self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_existing_win_constructor_remains_compatible(self) -> None:
        bet = SimulationBet(1, "strategy-a", "単勝", [11], 100, 1, NOW)
        self.assertEqual((bet.bet_type, bet.race_entry_ids, bet.stake), ("単勝", (11,), 100))

    def test_rejects_invalid_race_id_and_empty_strategy(self) -> None:
        with self.assertRaises(ValueError):
            SimulationBet(True, "strategy-a", "単勝", (11,), 100, 1, NOW)
        with self.assertRaises(ValueError):
            SimulationBet(1, "", "単勝", (11,), 100, 1, NOW)


if __name__ == "__main__":
    unittest.main()
