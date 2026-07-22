"""Tests for the isolated, single-bet simulator settlement core."""
from __future__ import annotations

import ast
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from io import StringIO
import inspect
from pathlib import Path
import unittest

import scripts.simulation as simulation_package
from scripts.simulation.models import SimulationBet
from scripts.simulation.repositories.interfaces import PayoutPublication, PayoutRecord, PayoutStatus
from scripts.simulation.simulator import (
    SimulationBetEvaluationError,
    _EvaluatedSimulationBet,
    _calculate_payout_amount,
    _evaluate_simulation_bet,
)


NOW = datetime(2026, 7, 21, 12, 0, tzinfo=UTC)


def make_bet(
    *,
    race_id: int = 1,
    bet_type: str = "単勝",
    selection: tuple[int, ...] = (11,),
    stake: int = 100,
) -> SimulationBet:
    return SimulationBet(race_id, "strategy-a", bet_type, selection, stake, 1, NOW)


def make_publication(
    entries: tuple[PayoutRecord, ...],
    *,
    race_id: int = 1,
    bet_type: str = "単勝",
    complete: bool = True,
) -> PayoutPublication:
    return PayoutPublication(race_id, bet_type, NOW if complete else None, NOW, complete, "official", entries)


class SingleBetEvaluationTests(unittest.TestCase):
    def test_evaluates_winning_win_bet(self) -> None:
        bet = make_bet(stake=300)
        record = PayoutRecord((11,), 230, PayoutStatus.WINNING)
        result = _evaluate_simulation_bet(bet, make_publication((record,)))
        self.assertEqual(result.payout_amount, 690)
        self.assertEqual(result.profit, 390)
        self.assertTrue(result.hit)

    def test_evaluates_winning_quinella_bet(self) -> None:
        bet = make_bet(bet_type="馬連", selection=(11, 12))
        result = _evaluate_simulation_bet(
            bet, make_publication((PayoutRecord((11, 12), 1250, PayoutStatus.WINNING),), bet_type="馬連")
        )
        self.assertEqual((result.payout_amount, result.profit, result.hit), (1250, 1150, True))

    def test_evaluates_winning_wide_bet(self) -> None:
        bet = make_bet(bet_type="ワイド", selection=(11, 12))
        result = _evaluate_simulation_bet(
            bet, make_publication((PayoutRecord((11, 12), 430, PayoutStatus.WINNING),), bet_type="ワイド")
        )
        self.assertEqual((result.payout_amount, result.profit, result.hit), (430, 330, True))

    def test_evaluates_winning_trio_bet(self) -> None:
        bet = make_bet(bet_type="3連複", selection=(11, 12, 13))
        result = _evaluate_simulation_bet(
            bet, make_publication((PayoutRecord((11, 12, 13), 8420, PayoutStatus.WINNING),), bet_type="3連複")
        )
        self.assertEqual((result.payout_amount, result.profit, result.hit), (8420, 8320, True))

    def test_per_100_formula_for_a_100_yen_stake(self) -> None:
        result = _evaluate_simulation_bet(
            make_bet(stake=100), make_publication((PayoutRecord((11,), 350, PayoutStatus.WINNING),))
        )
        self.assertEqual((result.payout_amount, result.profit), (350, 250))

    def test_per_100_formula_for_a_300_yen_stake(self) -> None:
        result = _evaluate_simulation_bet(
            make_bet(stake=300), make_publication((PayoutRecord((11,), 350, PayoutStatus.WINNING),))
        )
        self.assertEqual((result.payout_amount, result.profit), (1050, 750))

    def test_quinella_payout_uses_the_same_formula(self) -> None:
        bet = make_bet(bet_type="馬連", selection=(11, 12), stake=300)
        result = _evaluate_simulation_bet(
            bet, make_publication((PayoutRecord((11, 12), 1250, PayoutStatus.WINNING),), bet_type="馬連")
        )
        self.assertEqual((result.payout_amount, result.profit), (3750, 3450))

    def test_wide_payout_uses_the_same_formula(self) -> None:
        bet = make_bet(bet_type="ワイド", selection=(11, 12), stake=300)
        result = _evaluate_simulation_bet(
            bet, make_publication((PayoutRecord((11, 12), 430, PayoutStatus.WINNING),), bet_type="ワイド")
        )
        self.assertEqual((result.payout_amount, result.profit), (1290, 990))

    def test_trio_payout_uses_the_same_formula(self) -> None:
        bet = make_bet(bet_type="3連複", selection=(11, 12, 13), stake=300)
        result = _evaluate_simulation_bet(
            bet, make_publication((PayoutRecord((11, 12, 13), 8420, PayoutStatus.WINNING),), bet_type="3連複")
        )
        self.assertEqual((result.payout_amount, result.profit), (25260, 24960))

    def test_matches_by_bet_type_and_canonical_selection(self) -> None:
        bet = make_bet()
        matching = PayoutRecord((11,), 120, PayoutStatus.WINNING)
        unrelated = PayoutRecord((12,), 999, PayoutStatus.WINNING)
        result = _evaluate_simulation_bet(bet, make_publication((unrelated, matching)))
        self.assertEqual(result.matched_record, matching)
        self.assertEqual(result.payout_amount, 120)

    def test_quinella_matches_canonical_selection(self) -> None:
        bet = make_bet(bet_type="馬連", selection=(12, 11))
        result = _evaluate_simulation_bet(
            bet, make_publication((PayoutRecord((11, 12), 220, PayoutStatus.WINNING),), bet_type="馬連")
        )
        self.assertEqual(result.payout_amount, 220)

    def test_wide_matches_canonical_selection(self) -> None:
        bet = make_bet(bet_type="ワイド", selection=(12, 11))
        result = _evaluate_simulation_bet(
            bet, make_publication((PayoutRecord((11, 12), 220, PayoutStatus.WINNING),), bet_type="ワイド")
        )
        self.assertEqual(result.payout_amount, 220)

    def test_trio_matches_canonical_selection(self) -> None:
        bet = make_bet(bet_type="3連複", selection=(13, 11, 12))
        result = _evaluate_simulation_bet(
            bet, make_publication((PayoutRecord((11, 12, 13), 220, PayoutStatus.WINNING),), bet_type="3連複")
        )
        self.assertEqual(result.payout_amount, 220)

    def test_does_not_match_a_different_selection(self) -> None:
        result = _evaluate_simulation_bet(
            make_bet(), make_publication((PayoutRecord((12,), 250, PayoutStatus.WINNING),))
        )
        self.assertIsNone(result.matched_record)
        self.assertEqual(result.payout_amount, 0)

    def test_does_not_match_a_different_bet_type(self) -> None:
        publication = make_publication(
            (PayoutRecord((11, 12), 250, PayoutStatus.WINNING),), bet_type="馬連"
        )
        result = _evaluate_simulation_bet(make_bet(), publication)
        self.assertIsNone(result.matched_record)
        self.assertEqual(result.profit, -100)

    def test_same_pair_with_different_bet_type_does_not_match(self) -> None:
        bet = make_bet(bet_type="馬連", selection=(11, 12))
        publication = make_publication(
            (PayoutRecord((11, 12), 500, PayoutStatus.WINNING),), bet_type="ワイド"
        )
        result = _evaluate_simulation_bet(bet, publication)
        self.assertEqual((result.payout_amount, result.profit, result.hit), (0, -100, False))

    def test_different_quinella_selection_does_not_match(self) -> None:
        bet = make_bet(bet_type="馬連", selection=(11, 12))
        result = _evaluate_simulation_bet(
            bet, make_publication((PayoutRecord((11, 13), 500, PayoutStatus.WINNING),), bet_type="馬連")
        )
        self.assertEqual(result.payout_amount, 0)

    def test_different_wide_selection_does_not_match(self) -> None:
        bet = make_bet(bet_type="ワイド", selection=(11, 12))
        result = _evaluate_simulation_bet(
            bet, make_publication((PayoutRecord((11, 13), 500, PayoutStatus.WINNING),), bet_type="ワイド")
        )
        self.assertEqual(result.payout_amount, 0)

    def test_different_trio_selection_does_not_match(self) -> None:
        bet = make_bet(bet_type="3連複", selection=(11, 12, 13))
        result = _evaluate_simulation_bet(
            bet, make_publication((PayoutRecord((11, 12, 14), 500, PayoutStatus.WINNING),), bet_type="3連複")
        )
        self.assertEqual(result.payout_amount, 0)

    def test_incomplete_wrong_bet_type_fails_closed(self) -> None:
        bet = make_bet(bet_type="馬連", selection=(11, 12))
        with self.assertRaises(SimulationBetEvaluationError):
            _evaluate_simulation_bet(
                bet,
                make_publication((PayoutRecord((11, 12), 500, PayoutStatus.WINNING),), bet_type="ワイド", complete=False),
            )

    def test_returns_an_explicit_private_evaluation_model(self) -> None:
        result = _evaluate_simulation_bet(
            make_bet(), make_publication((PayoutRecord((11,), 100, PayoutStatus.WINNING),))
        )
        self.assertIsInstance(result, _EvaluatedSimulationBet)

    def test_preserves_the_original_bet(self) -> None:
        bet = make_bet(stake=500)
        result = _evaluate_simulation_bet(bet, make_publication((PayoutRecord((11,), 100, PayoutStatus.WINNING),)))
        self.assertIs(result.bet, bet)
        self.assertEqual(result.investment_amount, bet.stake)

    def test_uses_integer_payout_formula(self) -> None:
        result = _evaluate_simulation_bet(
            make_bet(stake=300), make_publication((PayoutRecord((11,), 123, PayoutStatus.WINNING),))
        )
        self.assertEqual(result.payout_amount, 369)
        self.assertIsInstance(result.payout_amount, int)

    def test_calculates_profit_from_payout_minus_investment(self) -> None:
        result = _evaluate_simulation_bet(
            make_bet(stake=400), make_publication((PayoutRecord((11,), 75, PayoutStatus.REFUND),))
        )
        self.assertEqual(result.profit, result.payout_amount - result.investment_amount)
        self.assertEqual(result.profit, -100)

    def test_complete_unmatched_bet_is_a_loss(self) -> None:
        result = _evaluate_simulation_bet(
            make_bet(stake=200), make_publication((PayoutRecord((12,), 100, PayoutStatus.WINNING),))
        )
        self.assertFalse(result.hit)
        self.assertEqual((result.payout_amount, result.profit), (0, -200))
        self.assertIsNone(result.payout_status)

    def test_complete_unmatched_bet_has_zero_payout(self) -> None:
        result = _evaluate_simulation_bet(
            make_bet(), make_publication((PayoutRecord((12,), 100, PayoutStatus.WINNING),))
        )
        self.assertEqual(result.payout_amount, 0)

    def test_complete_unmatched_bet_has_negative_profit(self) -> None:
        result = _evaluate_simulation_bet(
            make_bet(stake=300), make_publication((PayoutRecord((12,), 100, PayoutStatus.WINNING),))
        )
        self.assertEqual(result.profit, -300)

    def test_refund_uses_the_boundary_payout_amount(self) -> None:
        result = _evaluate_simulation_bet(
            make_bet(stake=300), make_publication((PayoutRecord((11,), 100, PayoutStatus.REFUND),))
        )
        self.assertFalse(result.hit)
        self.assertEqual((result.payout_amount, result.profit), (300, 0))

    def test_full_refund_has_zero_profit(self) -> None:
        result = _evaluate_simulation_bet(
            make_bet(stake=500), make_publication((PayoutRecord((11,), 100, PayoutStatus.REFUND),))
        )
        self.assertEqual(result.profit, 0)

    def test_quinella_refund(self) -> None:
        bet = make_bet(bet_type="馬連", selection=(11, 12), stake=300)
        result = _evaluate_simulation_bet(
            bet, make_publication((PayoutRecord((11, 12), 100, PayoutStatus.REFUND),), bet_type="馬連")
        )
        self.assertEqual((result.payout_amount, result.profit, result.hit), (300, 0, False))

    def test_wide_refund(self) -> None:
        bet = make_bet(bet_type="ワイド", selection=(11, 12), stake=300)
        result = _evaluate_simulation_bet(
            bet, make_publication((PayoutRecord((11, 12), 100, PayoutStatus.REFUND),), bet_type="ワイド")
        )
        self.assertEqual((result.payout_amount, result.profit, result.hit), (300, 0, False))

    def test_trio_refund(self) -> None:
        bet = make_bet(bet_type="3連複", selection=(11, 12, 13), stake=300)
        result = _evaluate_simulation_bet(
            bet, make_publication((PayoutRecord((11, 12, 13), 100, PayoutStatus.REFUND),), bet_type="3連複")
        )
        self.assertEqual((result.payout_amount, result.profit, result.hit), (300, 0, False))

    def test_void_uses_the_boundary_payout_amount(self) -> None:
        result = _evaluate_simulation_bet(
            make_bet(stake=200), make_publication((PayoutRecord((11,), 50, PayoutStatus.VOID),))
        )
        self.assertFalse(result.hit)
        self.assertEqual((result.payout_amount, result.profit), (100, -100))

    def test_quinella_void(self) -> None:
        bet = make_bet(bet_type="馬連", selection=(11, 12), stake=300)
        result = _evaluate_simulation_bet(
            bet, make_publication((PayoutRecord((11, 12), 0, PayoutStatus.VOID),), bet_type="馬連")
        )
        self.assertEqual((result.payout_amount, result.profit, result.hit), (0, -300, False))

    def test_wide_void(self) -> None:
        bet = make_bet(bet_type="ワイド", selection=(11, 12), stake=300)
        result = _evaluate_simulation_bet(
            bet, make_publication((PayoutRecord((11, 12), 0, PayoutStatus.VOID),), bet_type="ワイド")
        )
        self.assertEqual((result.payout_amount, result.profit, result.hit), (0, -300, False))

    def test_trio_void(self) -> None:
        bet = make_bet(bet_type="3連複", selection=(11, 12, 13), stake=300)
        result = _evaluate_simulation_bet(
            bet, make_publication((PayoutRecord((11, 12, 13), 0, PayoutStatus.VOID),), bet_type="3連複")
        )
        self.assertEqual((result.payout_amount, result.profit, result.hit), (0, -300, False))

    def test_unsupported_payout_fails_closed(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            _evaluate_simulation_bet(
                make_bet(), make_publication((PayoutRecord((11,), 0, PayoutStatus.UNSUPPORTED),))
            )

    def test_quinella_unsupported_fails_closed(self) -> None:
        bet = make_bet(bet_type="馬連", selection=(11, 12))
        with self.assertRaises(SimulationBetEvaluationError):
            _evaluate_simulation_bet(
                bet, make_publication((PayoutRecord((11, 12), 0, PayoutStatus.UNSUPPORTED),), bet_type="馬連")
            )

    def test_wide_unsupported_fails_closed(self) -> None:
        bet = make_bet(bet_type="ワイド", selection=(11, 12))
        with self.assertRaises(SimulationBetEvaluationError):
            _evaluate_simulation_bet(
                bet, make_publication((PayoutRecord((11, 12), 0, PayoutStatus.UNSUPPORTED),), bet_type="ワイド")
            )

    def test_trio_unsupported_fails_closed(self) -> None:
        bet = make_bet(bet_type="3連複", selection=(11, 12, 13))
        with self.assertRaises(SimulationBetEvaluationError):
            _evaluate_simulation_bet(
                bet, make_publication((PayoutRecord((11, 12, 13), 0, PayoutStatus.UNSUPPORTED),), bet_type="3連複")
            )

    def test_incomplete_unmatched_publication_fails_closed(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            _evaluate_simulation_bet(
                make_bet(), make_publication((PayoutRecord((12,), 100, PayoutStatus.WINNING),), complete=False)
            )

    def test_incomplete_matching_supported_record_is_evaluated(self) -> None:
        result = _evaluate_simulation_bet(
            make_bet(), make_publication((PayoutRecord((11,), 140, PayoutStatus.WINNING),), complete=False)
        )
        self.assertEqual((result.payout_amount, result.profit), (140, 40))

    def test_incomplete_quinella_without_match_fails_closed(self) -> None:
        bet = make_bet(bet_type="馬連", selection=(11, 12))
        with self.assertRaises(SimulationBetEvaluationError):
            _evaluate_simulation_bet(
                bet, make_publication((PayoutRecord((11, 13), 140, PayoutStatus.WINNING),), bet_type="馬連", complete=False)
            )

    def test_incomplete_wide_without_match_fails_closed(self) -> None:
        bet = make_bet(bet_type="ワイド", selection=(11, 12))
        with self.assertRaises(SimulationBetEvaluationError):
            _evaluate_simulation_bet(
                bet, make_publication((PayoutRecord((11, 13), 140, PayoutStatus.WINNING),), bet_type="ワイド", complete=False)
            )

    def test_incomplete_trio_without_match_fails_closed(self) -> None:
        bet = make_bet(bet_type="3連複", selection=(11, 12, 13))
        with self.assertRaises(SimulationBetEvaluationError):
            _evaluate_simulation_bet(
                bet, make_publication((PayoutRecord((11, 12, 14), 140, PayoutStatus.WINNING),), bet_type="3連複", complete=False)
            )

    def test_ignores_unrelated_records(self) -> None:
        result = _evaluate_simulation_bet(
            make_bet(),
            make_publication((
                PayoutRecord((12,), 999, PayoutStatus.WINNING),
                PayoutRecord((11,), 110, PayoutStatus.WINNING),
            )),
        )
        self.assertEqual(result.payout_amount, 110)

    def test_does_not_sum_multiple_unrelated_records(self) -> None:
        result = _evaluate_simulation_bet(
            make_bet(),
            make_publication((
                PayoutRecord((12,), 400, PayoutStatus.WINNING),
                PayoutRecord((13,), 500, PayoutStatus.WINNING),
            )),
        )
        self.assertEqual(result.payout_amount, 0)

    def test_unrelated_multi_type_records_are_not_summed(self) -> None:
        bet = make_bet(bet_type="馬連", selection=(11, 12))
        result = _evaluate_simulation_bet(
            bet,
            make_publication((
                PayoutRecord((11, 13), 700, PayoutStatus.WINNING),
                PayoutRecord((12, 13), 800, PayoutStatus.WINNING),
            ), bet_type="馬連"),
        )
        self.assertEqual((result.payout_amount, result.profit), (0, -100))

    def test_trio_requires_an_exact_three_entry_selection(self) -> None:
        bet = make_bet(bet_type="3連複", selection=(11, 12, 13))
        result = _evaluate_simulation_bet(
            bet, make_publication((PayoutRecord((11, 12, 14), 900, PayoutStatus.WINNING),), bet_type="3連複")
        )
        self.assertIsNone(result.matched_record)

    def test_selection_size_is_not_a_stake_multiplier(self) -> None:
        bet = make_bet(bet_type="3連複", selection=(11, 12, 13), stake=300)
        result = _evaluate_simulation_bet(
            bet, make_publication((PayoutRecord((11, 12, 13), 1250, PayoutStatus.WINNING),), bet_type="3連複")
        )
        self.assertEqual(result.payout_amount, 3750)

    def test_rejects_a_non_simulation_bet(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            _evaluate_simulation_bet("not-a-bet", make_publication(tuple()))  # type: ignore[arg-type]

    def test_rejects_a_non_publication(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            _evaluate_simulation_bet(make_bet(), "not-a-publication")  # type: ignore[arg-type]

    def test_rejects_race_id_mismatch(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            _evaluate_simulation_bet(make_bet(race_id=2), make_publication(tuple(), race_id=1))

    def test_does_not_mutate_publication_entries(self) -> None:
        entries = (PayoutRecord((11,), 150, PayoutStatus.WINNING),)
        publication = make_publication(entries)
        _evaluate_simulation_bet(make_bet(), publication)
        self.assertEqual(publication.entries, entries)

    def test_does_not_mutate_the_bet(self) -> None:
        bet = make_bet(stake=300)
        _evaluate_simulation_bet(bet, make_publication((PayoutRecord((11,), 120, PayoutStatus.WINNING),)))
        self.assertEqual((bet.race_entry_ids, bet.stake, bet.bet_type), ((11,), 300, "単勝"))

    def test_private_result_model_is_frozen(self) -> None:
        result = _evaluate_simulation_bet(
            make_bet(), make_publication((PayoutRecord((11,), 100, PayoutStatus.WINNING),))
        )
        with self.assertRaises(FrozenInstanceError):
            result.payout_amount = 0  # type: ignore[misc]

    def test_helper_has_no_float_or_rounding_operations(self) -> None:
        tree = ast.parse(inspect.getsource(_evaluate_simulation_bet))
        constants = [node.value for node in ast.walk(tree) if isinstance(node, ast.Constant)]
        self.assertNotIn("round", _evaluate_simulation_bet.__code__.co_names)
        self.assertNotIn("quantize", _evaluate_simulation_bet.__code__.co_names)
        self.assertFalse(any(isinstance(value, float) for value in constants))

    def test_rejects_a_fractional_yen_payout_instead_of_truncating(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            _calculate_payout_amount(101, 1)

    def test_exact_payout_calculation_keeps_100_yen_unit_results(self) -> None:
        self.assertEqual(_calculate_payout_amount(300, 350), 1050)

    def test_simulator_has_no_same_name_validation_exception(self) -> None:
        source = Path(inspect.getsourcefile(_evaluate_simulation_bet)).read_text(encoding="utf-8")
        self.assertNotIn("class SimulationValidationError", source)

    def test_module_has_no_database_or_provider_dependency(self) -> None:
        source = Path(inspect.getsourcefile(_evaluate_simulation_bet)).read_text(encoding="utf-8")
        self.assertNotIn("sqlite3", source)
        self.assertNotIn("providers", source)
        self.assertNotIn("repositories.sqlite", source)

    def test_helper_does_not_call_providers(self) -> None:
        source = inspect.getsource(_evaluate_simulation_bet)
        self.assertNotIn("Provider", source)
        self.assertNotIn("provider", source)

    def test_helper_does_not_write_stdout_or_stderr(self) -> None:
        stdout, stderr = StringIO(), StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            _evaluate_simulation_bet(
                make_bet(), make_publication((PayoutRecord((11,), 100, PayoutStatus.WINNING),))
            )
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")

    def test_helper_is_not_exported_from_the_package_root(self) -> None:
        self.assertNotIn("_evaluate_simulation_bet", simulation_package.__all__)
        self.assertFalse(hasattr(simulation_package, "_evaluate_simulation_bet"))

    def test_module_does_not_define_full_simulation_or_roi_components(self) -> None:
        source = Path(inspect.getsourcefile(_evaluate_simulation_bet)).read_text(encoding="utf-8")
        tree = ast.parse(source)
        class_names = {node.name for node in tree.body if isinstance(node, ast.ClassDef)}
        self.assertNotIn("Simulator", class_names)
        self.assertNotIn("SimulationSummary", class_names)
        self.assertNotIn("ROI", source)
        self.assertNotIn("drawdown", source.lower())

    def test_helper_does_not_expand_box_or_formation_candidates(self) -> None:
        source = inspect.getsource(_evaluate_simulation_bet)
        self.assertNotIn("combinations", source)
        self.assertNotIn("formation", source.lower())

    def test_helper_does_not_use_selection_key_or_horse_numbers(self) -> None:
        source = inspect.getsource(_evaluate_simulation_bet)
        self.assertNotIn("selection_key", source)
        self.assertNotIn("horse_number", source)

    def test_result_invariants_reject_inconsistent_private_values(self) -> None:
        bet = make_bet()
        record = PayoutRecord((11,), 100, PayoutStatus.WINNING)
        with self.assertRaises(SimulationBetEvaluationError):
            _EvaluatedSimulationBet(bet, 100, 100, 0, False, PayoutStatus.WINNING, record)


if __name__ == "__main__":
    unittest.main()
