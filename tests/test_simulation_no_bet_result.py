"""Tests for building an empty NO_BET SimulationResult."""
from __future__ import annotations

import inspect
from pathlib import Path
from unittest.mock import patch
import unittest

import scripts.simulation as simulation_package
import scripts.simulation.simulator as simulator
from scripts.simulation.models import SettlementStatus, SimulationResult
from scripts.simulation.simulator import SimulationBetEvaluationError, _build_no_bet_simulation_result


class NoBetSimulationResultTests(unittest.TestCase):
    def build(self, race_id: int = 1, strategy_id: str = "strategy-a") -> SimulationResult:
        return _build_no_bet_simulation_result(race_id, strategy_id)

    def test_builds_simulation_result(self) -> None:
        self.assertIsInstance(self.build(), SimulationResult)

    def test_result_status_is_no_bet(self) -> None:
        self.assertIs(self.build().settlement_status, SettlementStatus.NO_BET)

    def test_preserves_race_id(self) -> None:
        self.assertEqual(self.build(3).race_id, 3)

    def test_preserves_strategy_id(self) -> None:
        self.assertEqual(self.build(strategy_id="strategy-b").strategy_id, "strategy-b")

    def test_result_bets_are_empty(self) -> None:
        self.assertEqual(self.build().bets, ())

    def test_planned_investment_is_zero(self) -> None:
        self.assertEqual(self.build().planned_investment, 0)

    def test_settled_investment_is_none(self) -> None:
        self.assertIsNone(self.build().settled_investment)

    def test_payout_is_none(self) -> None:
        self.assertIsNone(self.build().payout)

    def test_profit_is_none(self) -> None:
        self.assertIsNone(self.build().profit)

    def test_hit_bet_count_is_zero(self) -> None:
        self.assertEqual(self.build().hit_bet_count, 0)

    def test_settled_at_is_none(self) -> None:
        self.assertIsNone(self.build().settled_at)

    def test_exclusion_reason_matches_no_bet_contract(self) -> None:
        self.assertIsNone(self.build().exclusion_reason)

    def test_rejects_zero_race_id(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            self.build(0)

    def test_rejects_negative_race_id(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            self.build(-1)

    def test_rejects_bool_race_id(self) -> None:
        for value in (True, False):
            with self.subTest(value=value), self.assertRaises(SimulationBetEvaluationError):
                self.build(value)  # type: ignore[arg-type]

    def test_rejects_non_integer_race_id(self) -> None:
        for value in (1.0, "1", None):
            with self.subTest(value=value), self.assertRaises(SimulationBetEvaluationError):
                self.build(value)  # type: ignore[arg-type]

    def test_rejects_empty_strategy_id(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError):
            self.build(strategy_id="")

    def test_rejects_non_string_strategy_id(self) -> None:
        for value in (None, 1, [], {}):
            with self.subTest(value=value), self.assertRaises(SimulationBetEvaluationError):
                self.build(strategy_id=value)  # type: ignore[arg-type]

    def test_converts_simulation_result_type_error(self) -> None:
        original = TypeError("constructor type failure")
        with patch.object(simulator, "SimulationResult", side_effect=original):
            with self.assertRaises(SimulationBetEvaluationError) as caught:
                self.build()
        self.assertIs(caught.exception.__cause__, original)

    def test_converts_simulation_result_value_error(self) -> None:
        original = ValueError("constructor value failure")
        with patch.object(simulator, "SimulationResult", side_effect=original):
            with self.assertRaises(SimulationBetEvaluationError) as caught:
                self.build()
        self.assertIs(caught.exception.__cause__, original)

    def test_preserves_exception_cause(self) -> None:
        original = ArithmeticError("calculation failure")
        with patch.object(simulator, "SimulationResult", side_effect=original):
            with self.assertRaises(SimulationBetEvaluationError) as caught:
                self.build()
        self.assertIs(caught.exception.__cause__, original)

    def test_returns_no_partial_result_on_failure(self) -> None:
        with patch.object(simulator, "SimulationResult", side_effect=ValueError("failure")):
            with self.assertRaises(SimulationBetEvaluationError):
                self.build()

    def test_does_not_call_single_bet_evaluation(self) -> None:
        with patch.object(simulator, "_evaluate_simulation_bet", side_effect=AssertionError("must not run")):
            self.assertIsInstance(self.build(), SimulationResult)

    def test_does_not_call_race_bet_evaluation(self) -> None:
        with patch.object(simulator, "_evaluate_simulation_race_bets", side_effect=AssertionError("must not run")):
            self.assertIsInstance(self.build(), SimulationResult)

    def test_does_not_call_settled_result_builder(self) -> None:
        with patch.object(simulator, "_build_settled_simulation_result", side_effect=AssertionError("must not run")):
            self.assertIsInstance(self.build(), SimulationResult)

    def test_does_not_use_current_time(self) -> None:
        source = inspect.getsource(_build_no_bet_simulation_result)
        self.assertNotIn("datetime.now", source)
        self.assertNotIn("datetime.utcnow", source)

    def test_does_not_call_provider_or_repository(self) -> None:
        source = inspect.getsource(_build_no_bet_simulation_result)
        self.assertNotIn("Provider", source)
        self.assertNotIn("Repository", source)

    def test_does_not_access_database_or_network(self) -> None:
        source = Path(inspect.getsourcefile(_build_no_bet_simulation_result)).read_text(encoding="utf-8")
        self.assertNotIn("sqlite3", source)
        self.assertNotIn("requests", source)
        self.assertNotIn("urllib", source)

    def test_does_not_calculate_roi_or_drawdown(self) -> None:
        source = inspect.getsource(_build_no_bet_simulation_result).lower()
        self.assertNotIn("roi", source)
        self.assertNotIn("drawdown", source)

    def test_internal_helper_is_not_exported_from_package_root(self) -> None:
        self.assertNotIn("_build_no_bet_simulation_result", simulation_package.__all__)
        self.assertFalse(hasattr(simulation_package, "_build_no_bet_simulation_result"))


if __name__ == "__main__":
    unittest.main()
