"""Tests for pure non-settled status decisions."""
from __future__ import annotations

from dataclasses import FrozenInstanceError
from enum import Enum
import inspect
from pathlib import Path
from unittest.mock import patch
import unittest

import scripts.simulation as simulation_package
import scripts.simulation.simulator as simulator
from scripts.simulation.models import SettlementStatus
from scripts.simulation.providers.models import CompletenessStatus
from scripts.simulation.repositories.interfaces import PayoutStatus, RaceResultStatus
from scripts.simulation.simulator import (
    SimulationBetEvaluationError,
    _NonSettledStatusDecision,
    _decide_non_settled_status,
)


class OtherEnum(Enum):
    VALUE = "value"


class NonSettledStatusDecisionTests(unittest.TestCase):
    def decide(
        self,
        *,
        completeness=(),
        race_status=None,
        payouts=(),
        missing_types=(),
        missing_race=False,
        error=None,
    ):
        return _decide_non_settled_status(
            completeness_statuses=completeness,
            race_result_status=race_status,
            payout_statuses=payouts,
            missing_payout_bet_types=missing_types,
            missing_race_result=missing_race,
            error_reason=error,
        )

    def assert_decision(self, decision, status: SettlementStatus, reason: str) -> None:
        self.assertIsInstance(decision, _NonSettledStatusDecision)
        self.assertIs(decision.settlement_status, status)
        self.assertEqual(decision.exclusion_reason, reason)

    def test_returns_none_when_all_facts_are_neutral(self) -> None:
        self.assertIsNone(self.decide())

    def test_complete_completeness_is_neutral(self) -> None:
        self.assertIsNone(self.decide(completeness=(CompletenessStatus.COMPLETE,)))

    def test_complete_race_result_is_neutral(self) -> None:
        self.assertIsNone(self.decide(race_status=RaceResultStatus.COMPLETE))

    def test_winning_payout_is_neutral(self) -> None:
        self.assertIsNone(self.decide(payouts=(PayoutStatus.WINNING,)))

    def test_refund_payout_is_neutral(self) -> None:
        self.assertIsNone(self.decide(payouts=(PayoutStatus.REFUND,)))

    def test_void_payout_is_neutral(self) -> None:
        self.assertIsNone(self.decide(payouts=(PayoutStatus.VOID,)))

    def test_none_race_status_without_missing_flag_is_neutral(self) -> None:
        self.assertIsNone(self.decide(race_status=None, missing_race=False))

    def test_explicit_error_reason_decides_error(self) -> None:
        self.assert_decision(self.decide(error="internal_evaluation_error"), SettlementStatus.ERROR, "internal_evaluation_error")

    def test_invalid_completeness_decides_error(self) -> None:
        self.assert_decision(self.decide(completeness=(CompletenessStatus.INVALID,)), SettlementStatus.ERROR, "invalid_provider_completeness")

    def test_error_has_highest_priority(self) -> None:
        self.assert_decision(self.decide(error="internal_evaluation_error", completeness=(CompletenessStatus.INVALID,)), SettlementStatus.ERROR, "internal_evaluation_error")

    def test_error_overrides_official_void(self) -> None:
        self.assert_decision(self.decide(error="internal_evaluation_error", race_status=RaceResultStatus.VOID), SettlementStatus.ERROR, "internal_evaluation_error")

    def test_error_overrides_unsupported(self) -> None:
        self.assert_decision(self.decide(completeness=(CompletenessStatus.INVALID, CompletenessStatus.UNSUPPORTED)), SettlementStatus.ERROR, "invalid_provider_completeness")

    def test_error_overrides_unsettled(self) -> None:
        self.assert_decision(self.decide(completeness=(CompletenessStatus.INVALID, CompletenessStatus.INCOMPLETE), missing_types=("単勝",)), SettlementStatus.ERROR, "invalid_provider_completeness")

    def test_preserves_explicit_error_reason(self) -> None:
        self.assertEqual(self.decide(error="custom_reason").exclusion_reason, "custom_reason")

    def test_official_race_void_decides_void(self) -> None:
        self.assert_decision(self.decide(race_status=RaceResultStatus.VOID), SettlementStatus.VOID, "official_race_void")

    def test_void_overrides_unsupported(self) -> None:
        self.assert_decision(self.decide(race_status=RaceResultStatus.VOID, payouts=(PayoutStatus.UNSUPPORTED,)), SettlementStatus.VOID, "official_race_void")

    def test_void_overrides_unsettled(self) -> None:
        self.assert_decision(self.decide(race_status=RaceResultStatus.VOID, missing_types=("単勝",)), SettlementStatus.VOID, "official_race_void")

    def test_payout_void_does_not_decide_race_void(self) -> None:
        self.assertIsNone(self.decide(payouts=(PayoutStatus.VOID,)))

    def test_unsupported_completeness_decides_unsupported(self) -> None:
        self.assert_decision(self.decide(completeness=(CompletenessStatus.UNSUPPORTED,)), SettlementStatus.UNSUPPORTED, "unsupported_provider_completeness")

    def test_unsupported_race_result_decides_unsupported(self) -> None:
        self.assert_decision(self.decide(race_status=RaceResultStatus.UNSUPPORTED), SettlementStatus.UNSUPPORTED, "unsupported_race_result")

    def test_unsupported_payout_decides_unsupported(self) -> None:
        self.assert_decision(self.decide(payouts=(PayoutStatus.UNSUPPORTED,)), SettlementStatus.UNSUPPORTED, "unsupported_payout_status")

    def test_unsupported_overrides_incomplete(self) -> None:
        self.assert_decision(self.decide(completeness=(CompletenessStatus.INCOMPLETE, CompletenessStatus.UNSUPPORTED)), SettlementStatus.UNSUPPORTED, "unsupported_provider_completeness")

    def test_unsupported_overrides_missing_publication(self) -> None:
        self.assert_decision(self.decide(payouts=(PayoutStatus.UNSUPPORTED,), missing_types=("単勝",)), SettlementStatus.UNSUPPORTED, "unsupported_payout_status")

    def test_single_unsupported_payout_is_sufficient(self) -> None:
        self.assert_decision(self.decide(payouts=(PayoutStatus.WINNING, PayoutStatus.UNSUPPORTED)), SettlementStatus.UNSUPPORTED, "unsupported_payout_status")

    def test_missing_publication_decides_unsettled(self) -> None:
        self.assert_decision(self.decide(missing_types=("単勝",)), SettlementStatus.UNSETTLED, "missing_payout_publication")

    def test_missing_race_result_decides_unsettled(self) -> None:
        self.assert_decision(self.decide(missing_race=True), SettlementStatus.UNSETTLED, "missing_race_result")

    def test_incomplete_completeness_decides_unsettled(self) -> None:
        self.assert_decision(self.decide(completeness=(CompletenessStatus.INCOMPLETE,)), SettlementStatus.UNSETTLED, "incomplete_provider_data")

    def test_partial_race_result_decides_unsettled(self) -> None:
        self.assert_decision(self.decide(race_status=RaceResultStatus.PARTIAL), SettlementStatus.UNSETTLED, "incomplete_race_result")

    def test_multiple_unsettled_facts_use_deterministic_reason(self) -> None:
        self.assert_decision(self.decide(completeness=(CompletenessStatus.INCOMPLETE,), race_status=RaceResultStatus.PARTIAL, missing_types=("単勝",), missing_race=True), SettlementStatus.UNSETTLED, "missing_payout_publication")

    def test_missing_bet_type_order_does_not_change_decision(self) -> None:
        first = self.decide(missing_types=("馬連", "単勝"))
        second = self.decide(missing_types=("単勝", "馬連"))
        self.assertEqual(first, second)

    def test_duplicate_missing_bet_types_do_not_change_decision(self) -> None:
        self.assertEqual(self.decide(missing_types=("単勝", "単勝")), self.decide(missing_types=("単勝",)))

    def test_rejects_non_sequence_completeness(self) -> None:
        for value in (None, 1, {}):
            with self.subTest(value=value), self.assertRaises(SimulationBetEvaluationError): self.decide(completeness=value)

    def test_rejects_string_completeness(self) -> None:
        for value in ("complete", b"complete", bytearray(b"complete")):
            with self.subTest(value=value), self.assertRaises(SimulationBetEvaluationError): self.decide(completeness=value)

    def test_rejects_invalid_completeness_item(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError): self.decide(completeness=("complete",))

    def test_rejects_invalid_race_result_status(self) -> None:
        for value in ("complete", OtherEnum.VALUE, 1):
            with self.subTest(value=value), self.assertRaises(SimulationBetEvaluationError): self.decide(race_status=value)

    def test_rejects_non_sequence_payout_statuses(self) -> None:
        for value in (None, 1, {}):
            with self.subTest(value=value), self.assertRaises(SimulationBetEvaluationError): self.decide(payouts=value)

    def test_rejects_string_payout_statuses(self) -> None:
        for value in ("winning", b"winning", bytearray(b"winning")):
            with self.subTest(value=value), self.assertRaises(SimulationBetEvaluationError): self.decide(payouts=value)

    def test_rejects_invalid_payout_status_item(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError): self.decide(payouts=("winning",))

    def test_rejects_non_sequence_missing_bet_types(self) -> None:
        for value in (None, 1, {}):
            with self.subTest(value=value), self.assertRaises(SimulationBetEvaluationError): self.decide(missing_types=value)

    def test_rejects_string_missing_bet_types(self) -> None:
        for value in ("単勝", b"x", bytearray(b"x")):
            with self.subTest(value=value), self.assertRaises(SimulationBetEvaluationError): self.decide(missing_types=value)

    def test_rejects_invalid_missing_bet_type(self) -> None:
        for value in (("未知",), (1,), (True,)):
            with self.subTest(value=value), self.assertRaises(SimulationBetEvaluationError): self.decide(missing_types=value)

    def test_rejects_non_bool_missing_race_result(self) -> None:
        for value in (0, 1, None, "false"):
            with self.subTest(value=value), self.assertRaises(SimulationBetEvaluationError): self.decide(missing_race=value)

    def test_rejects_non_string_error_reason(self) -> None:
        for value in (1, [], {}):
            with self.subTest(value=value), self.assertRaises(SimulationBetEvaluationError): self.decide(error=value)

    def test_rejects_empty_error_reason(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError): self.decide(error="")

    def test_rejects_whitespace_error_reason(self) -> None:
        with self.assertRaises(SimulationBetEvaluationError): self.decide(error="   ")

    def test_returns_internal_decision_model(self) -> None:
        self.assertIsInstance(self.decide(missing_race=True), _NonSettledStatusDecision)

    def test_decision_model_is_frozen(self) -> None:
        decision = self.decide(missing_race=True)
        with self.assertRaises(FrozenInstanceError): decision.exclusion_reason = "changed"  # type: ignore[misc]

    def test_does_not_mutate_completeness_input(self) -> None:
        values = [CompletenessStatus.INCOMPLETE]; self.decide(completeness=values); self.assertEqual(values, [CompletenessStatus.INCOMPLETE])

    def test_does_not_mutate_payout_input(self) -> None:
        values = [PayoutStatus.UNSUPPORTED]; self.decide(payouts=values); self.assertEqual(values, [PayoutStatus.UNSUPPORTED])

    def test_does_not_mutate_missing_bet_type_input(self) -> None:
        values = ["馬連", "単勝"]; self.decide(missing_types=values); self.assertEqual(values, ["馬連", "単勝"])

    def test_does_not_build_simulation_result(self) -> None:
        with patch.object(simulator, "SimulationResult", side_effect=AssertionError("must not run")):
            self.assertIsNotNone(self.decide(missing_race=True))

    def test_does_not_call_any_result_builder(self) -> None:
        with patch.object(simulator, "_build_settled_simulation_result", side_effect=AssertionError("must not run")), patch.object(simulator, "_build_no_bet_simulation_result", side_effect=AssertionError("must not run")), patch.object(simulator, "_build_non_settled_simulation_result", side_effect=AssertionError("must not run")):
            self.assertIsNotNone(self.decide(missing_race=True))

    def test_does_not_call_evaluation_helpers(self) -> None:
        with patch.object(simulator, "_evaluate_simulation_bet", side_effect=AssertionError("must not run")), patch.object(simulator, "_evaluate_simulation_race_bets", side_effect=AssertionError("must not run")):
            self.assertIsNotNone(self.decide(missing_race=True))

    def test_does_not_call_provider_or_repository(self) -> None:
        source = inspect.getsource(_decide_non_settled_status)
        self.assertNotIn("providers.", source)
        self.assertNotIn("repositories.", source)

    def test_does_not_access_database_or_network(self) -> None:
        source = Path(inspect.getsourcefile(_decide_non_settled_status)).read_text(encoding="utf-8")
        self.assertNotIn("sqlite3", source); self.assertNotIn("requests", source); self.assertNotIn("urllib", source)

    def test_does_not_use_current_time(self) -> None:
        source = inspect.getsource(_decide_non_settled_status)
        self.assertNotIn("datetime.now", source); self.assertNotIn("datetime.utcnow", source)

    def test_internal_helper_is_not_exported_from_package_root(self) -> None:
        self.assertNotIn("_decide_non_settled_status", simulation_package.__all__)
        self.assertFalse(hasattr(simulation_package, "_decide_non_settled_status"))

    def test_internal_decision_model_is_not_exported_from_package_root(self) -> None:
        self.assertNotIn("_NonSettledStatusDecision", simulation_package.__all__)
        self.assertFalse(hasattr(simulation_package, "_NonSettledStatusDecision"))


if __name__ == "__main__":
    unittest.main()
