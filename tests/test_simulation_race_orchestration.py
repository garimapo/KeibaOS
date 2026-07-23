"""Tests for pure, one-race simulation-result orchestration."""
from __future__ import annotations

import ast
from datetime import UTC, datetime, timedelta
import inspect
from unittest.mock import patch
import unittest

import scripts.simulation as simulation_package
import scripts.simulation.simulator as simulator
from scripts.simulation.models import SettlementStatus, SimulationBet, SimulationResult
from scripts.simulation.providers.models import CompletenessStatus
from scripts.simulation.repositories.interfaces import PayoutPublication, PayoutRecord, PayoutStatus, RaceResultStatus
from scripts.simulation.simulator import (
    SimulationBetEvaluationError,
    _NonSettledStatusDecision,
    _build_simulation_result_for_race,
    _evaluate_simulation_race_bets,
)


NOW = datetime(2026, 7, 23, 12, 0, tzinfo=UTC)


def make_bet(*, race_id: int = 1, strategy_id: str = "strategy-a") -> SimulationBet:
    return SimulationBet(race_id, strategy_id, "単勝", (11,), 100, 1, NOW)


def make_publication(*, race_id: int = 1, payout_status: PayoutStatus = PayoutStatus.WINNING) -> PayoutPublication:
    amount = 200 if payout_status is PayoutStatus.WINNING else 0
    return PayoutPublication(
        race_id,
        "単勝",
        NOW,
        NOW,
        True,
        "test",
        (PayoutRecord((11,), amount, payout_status),),
    )


class RaceOrchestrationTests(unittest.TestCase):
    def kwargs(self, **overrides: object) -> dict[str, object]:
        values: dict[str, object] = {
            "race_id": 1,
            "strategy_id": "strategy-a",
            "bets": (make_bet(),),
            "publications_by_bet_type": {"単勝": make_publication()},
            "settled_at": NOW + timedelta(minutes=1),
            "completeness_statuses": (),
            "race_result_status": None,
            "payout_statuses": (),
            "missing_payout_bet_types": (),
            "missing_race_result": False,
            "error_reason": None,
        }
        values.update(overrides)
        return values

    def invoke(self, **overrides: object) -> SimulationResult:
        return _build_simulation_result_for_race(**self.kwargs(**overrides))  # type: ignore[arg-type]

    def evaluation(self):
        values = self.kwargs()
        return _evaluate_simulation_race_bets(
            values["race_id"], values["strategy_id"], values["bets"], values["publications_by_bet_type"]
        )

    def decision(self, status: SettlementStatus, reason: str) -> _NonSettledStatusDecision:
        return _NonSettledStatusDecision(status, reason)

    def test_builds_settled_result_when_decision_is_none(self) -> None:
        result = self.invoke()
        self.assertEqual(result.settlement_status, SettlementStatus.SETTLED)

    def test_settled_result_preserves_evaluated_bet(self) -> None:
        bet = make_bet()
        result = self.invoke(bets=(bet,))
        self.assertIs(result.bets[0], bet)

    def test_settled_result_uses_supplied_settled_at(self) -> None:
        settled_at = NOW + timedelta(hours=1)
        self.assertEqual(self.invoke(settled_at=settled_at).settled_at, settled_at)

    def test_settled_result_uses_evaluation_amounts(self) -> None:
        result = self.invoke()
        self.assertEqual((result.planned_investment, result.payout, result.profit), (100, 200, 100))

    def test_no_bet_builds_no_bet_result(self) -> None:
        result = self.invoke(bets=(), publications_by_bet_type={})
        self.assertEqual(result.settlement_status, SettlementStatus.NO_BET)

    def test_no_bet_has_no_bets(self) -> None:
        self.assertEqual(self.invoke(bets=(), publications_by_bet_type={}).bets, ())

    def test_no_bet_accepts_none_settled_at(self) -> None:
        result = self.invoke(bets=(), publications_by_bet_type={}, settled_at=None)
        self.assertIsNone(result.settled_at)

    def test_error_decision_builds_error_result(self) -> None:
        self.assertEqual(self.invoke(error_reason="provider_error").settlement_status, SettlementStatus.ERROR)

    def test_void_decision_builds_void_result(self) -> None:
        self.assertEqual(self.invoke(race_result_status=RaceResultStatus.VOID).settlement_status, SettlementStatus.VOID)

    def test_unsupported_decision_builds_unsupported_result(self) -> None:
        self.assertEqual(self.invoke(payout_statuses=(PayoutStatus.UNSUPPORTED,)).settlement_status, SettlementStatus.UNSUPPORTED)

    def test_unsettled_decision_builds_unsettled_result(self) -> None:
        self.assertEqual(self.invoke(missing_race_result=True).settlement_status, SettlementStatus.UNSETTLED)

    def test_error_reason_is_preserved_verbatim(self) -> None:
        self.assertEqual(self.invoke(error_reason="upstream_failure").exclusion_reason, "upstream_failure")

    def test_void_reason_is_preserved_verbatim(self) -> None:
        self.assertEqual(self.invoke(race_result_status=RaceResultStatus.VOID).exclusion_reason, "official_race_void")

    def test_unsupported_reason_is_preserved_verbatim(self) -> None:
        self.assertEqual(self.invoke(payout_statuses=(PayoutStatus.UNSUPPORTED,)).exclusion_reason, "unsupported_payout_status")

    def test_unsettled_reason_is_preserved_verbatim(self) -> None:
        self.assertEqual(self.invoke(missing_payout_bet_types=("単勝",)).exclusion_reason, "missing_payout_publication")

    def test_settled_dispatch_calls_only_settled_builder(self) -> None:
        evaluation, marker = self.evaluation(), object()
        with patch.object(simulator, "_evaluate_simulation_race_bets", return_value=evaluation), patch.object(simulator, "_decide_non_settled_status", return_value=None), patch.object(simulator, "_build_settled_simulation_result", return_value=marker) as settled, patch.object(simulator, "_build_no_bet_simulation_result") as no_bet, patch.object(simulator, "_build_non_settled_simulation_result") as non_settled:
            self.assertIs(self.invoke(), marker)
        settled.assert_called_once(); no_bet.assert_not_called(); non_settled.assert_not_called()

    def test_no_bet_dispatch_calls_only_no_bet_builder(self) -> None:
        marker = object()
        with patch.object(simulator, "_evaluate_simulation_race_bets") as evaluate, patch.object(simulator, "_decide_non_settled_status") as decide, patch.object(simulator, "_build_no_bet_simulation_result", return_value=marker) as no_bet, patch.object(simulator, "_build_settled_simulation_result") as settled, patch.object(simulator, "_build_non_settled_simulation_result") as non_settled:
            self.assertIs(self.invoke(bets=(), publications_by_bet_type={}), marker)
        evaluate.assert_not_called(); decide.assert_not_called(); no_bet.assert_called_once_with(1, "strategy-a"); settled.assert_not_called(); non_settled.assert_not_called()

    def test_error_dispatch_calls_only_non_settled_builder(self) -> None:
        self.assert_non_settled_dispatch(SettlementStatus.ERROR, "error")

    def test_void_dispatch_calls_only_non_settled_builder(self) -> None:
        self.assert_non_settled_dispatch(SettlementStatus.VOID, "void")

    def test_unsupported_dispatch_calls_only_non_settled_builder(self) -> None:
        self.assert_non_settled_dispatch(SettlementStatus.UNSUPPORTED, "unsupported")

    def test_unsettled_dispatch_calls_only_non_settled_builder(self) -> None:
        self.assert_non_settled_dispatch(SettlementStatus.UNSETTLED, "unsettled")

    def assert_non_settled_dispatch(self, status: SettlementStatus, reason: str) -> None:
        marker = object()
        bets = (make_bet(),)
        with patch.object(simulator, "_evaluate_simulation_race_bets") as evaluate, patch.object(simulator, "_decide_non_settled_status", return_value=self.decision(status, reason)), patch.object(simulator, "_build_non_settled_simulation_result", return_value=marker) as non_settled, patch.object(simulator, "_build_settled_simulation_result") as settled, patch.object(simulator, "_build_no_bet_simulation_result") as no_bet:
            self.assertIs(self.invoke(bets=bets), marker)
        non_settled.assert_called_once_with(race_id=1, strategy_id="strategy-a", bets=bets, settlement_status=status, exclusion_reason=reason)
        evaluate.assert_not_called()
        settled.assert_not_called(); no_bet.assert_not_called()

    def test_decision_precedes_evaluation_for_settled_result(self) -> None:
        events: list[str] = []
        evaluation = self.evaluation()
        with patch.object(simulator, "_decide_non_settled_status", side_effect=lambda **kwargs: events.append("decision")), patch.object(simulator, "_evaluate_simulation_race_bets", side_effect=lambda *args: events.append("evaluate") or evaluation), patch.object(simulator, "_build_settled_simulation_result", side_effect=lambda *args: events.append("settled") or object()):
            self.invoke()
        self.assertEqual(events, ["decision", "evaluate", "settled"])

    def test_non_settled_decision_precedes_non_settled_builder_without_evaluation(self) -> None:
        events: list[str] = []
        decision = self.decision(SettlementStatus.UNSETTLED, "missing")
        with patch.object(simulator, "_evaluate_simulation_race_bets", side_effect=lambda *args: events.append("evaluate")), patch.object(simulator, "_decide_non_settled_status", side_effect=lambda **kwargs: events.append("decision") or decision), patch.object(simulator, "_build_non_settled_simulation_result", side_effect=lambda **kwargs: events.append("non_settled") or object()):
            self.invoke()
        self.assertEqual(events, ["decision", "non_settled"])

    def test_no_bet_skips_decision(self) -> None:
        with patch.object(simulator, "_decide_non_settled_status") as decide:
            self.invoke(bets=(), publications_by_bet_type={})
        decide.assert_not_called()

    def test_evaluation_is_called_once(self) -> None:
        evaluation = self.evaluation()
        with patch.object(simulator, "_evaluate_simulation_race_bets", return_value=evaluation) as evaluate:
            self.invoke()
        evaluate.assert_called_once()

    def test_decision_is_called_once_for_non_empty_bets(self) -> None:
        with patch.object(simulator, "_decide_non_settled_status", return_value=None) as decide:
            self.invoke()
        decide.assert_called_once()

    def test_settled_builder_receives_evaluation_and_time(self) -> None:
        evaluation, settled_at = self.evaluation(), NOW + timedelta(minutes=2)
        with patch.object(simulator, "_evaluate_simulation_race_bets", return_value=evaluation), patch.object(simulator, "_decide_non_settled_status", return_value=None), patch.object(simulator, "_build_settled_simulation_result", return_value=object()) as settled:
            self.invoke(settled_at=settled_at)
        settled.assert_called_once_with(evaluation, settled_at)

    def test_settled_none_time_is_rejected_before_evaluation(self) -> None:
        with patch.object(simulator, "_evaluate_simulation_race_bets") as evaluate:
            with self.assertRaises(SimulationBetEvaluationError):
                self.invoke(settled_at=None)
        evaluate.assert_not_called()

    def test_non_settled_accepts_none_time_without_evaluation(self) -> None:
        decision = self.decision(SettlementStatus.UNSETTLED, "missing")
        with patch.object(simulator, "_evaluate_simulation_race_bets") as evaluate, patch.object(simulator, "_decide_non_settled_status", return_value=decision):
            result = self.invoke(settled_at=None)
        self.assertEqual(result.settlement_status, SettlementStatus.UNSETTLED)
        evaluate.assert_not_called()

    def test_missing_publication_becomes_unsettled_without_evaluation(self) -> None:
        with patch.object(simulator, "_evaluate_simulation_race_bets") as evaluate:
            result = self.invoke(
                publications_by_bet_type={},
                settled_at=None,
                missing_payout_bet_types=("単勝",),
            )
        self.assertEqual(result.settlement_status, SettlementStatus.UNSETTLED)
        self.assertEqual(result.exclusion_reason, "missing_payout_publication")
        evaluate.assert_not_called()

    def test_decision_receives_completeness_statuses(self) -> None:
        statuses = (CompletenessStatus.INCOMPLETE,)
        with patch.object(simulator, "_decide_non_settled_status", return_value=self.decision(SettlementStatus.UNSETTLED, "x")) as decide:
            self.invoke(completeness_statuses=statuses)
        self.assertIs(decide.call_args.kwargs["completeness_statuses"], statuses)

    def test_decision_receives_race_result_status(self) -> None:
        with patch.object(simulator, "_decide_non_settled_status", return_value=self.decision(SettlementStatus.UNSETTLED, "x")) as decide:
            self.invoke(race_result_status=RaceResultStatus.PARTIAL)
        self.assertIs(decide.call_args.kwargs["race_result_status"], RaceResultStatus.PARTIAL)

    def test_decision_receives_payout_statuses(self) -> None:
        statuses = (PayoutStatus.VOID,)
        with patch.object(simulator, "_decide_non_settled_status", return_value=self.decision(SettlementStatus.UNSETTLED, "x")) as decide:
            self.invoke(payout_statuses=statuses)
        self.assertIs(decide.call_args.kwargs["payout_statuses"], statuses)

    def test_decision_receives_missing_bet_types(self) -> None:
        values = ("単勝",)
        with patch.object(simulator, "_decide_non_settled_status", return_value=self.decision(SettlementStatus.UNSETTLED, "x")) as decide:
            self.invoke(missing_payout_bet_types=values)
        self.assertIs(decide.call_args.kwargs["missing_payout_bet_types"], values)

    def test_decision_receives_missing_race_flag(self) -> None:
        with patch.object(simulator, "_decide_non_settled_status", return_value=self.decision(SettlementStatus.UNSETTLED, "x")) as decide:
            self.invoke(missing_race_result=True)
        self.assertTrue(decide.call_args.kwargs["missing_race_result"])

    def test_decision_receives_error_reason(self) -> None:
        with patch.object(simulator, "_decide_non_settled_status", return_value=self.decision(SettlementStatus.ERROR, "x")) as decide:
            self.invoke(error_reason="upstream")
        self.assertEqual(decide.call_args.kwargs["error_reason"], "upstream")

    def test_evaluation_exception_is_propagated_unchanged(self) -> None:
        expected = SimulationBetEvaluationError("evaluation")
        with patch.object(simulator, "_evaluate_simulation_race_bets", side_effect=expected):
            with self.assertRaises(SimulationBetEvaluationError) as caught: self.invoke()
        self.assertIs(caught.exception, expected)

    def test_decision_exception_is_propagated_unchanged(self) -> None:
        expected = SimulationBetEvaluationError("decision")
        with patch.object(simulator, "_decide_non_settled_status", side_effect=expected):
            with self.assertRaises(SimulationBetEvaluationError) as caught: self.invoke()
        self.assertIs(caught.exception, expected)

    def test_settled_builder_exception_is_propagated_unchanged(self) -> None:
        expected = SimulationBetEvaluationError("settled")
        with patch.object(simulator, "_decide_non_settled_status", return_value=None), patch.object(simulator, "_build_settled_simulation_result", side_effect=expected):
            with self.assertRaises(SimulationBetEvaluationError) as caught: self.invoke()
        self.assertIs(caught.exception, expected)

    def test_non_settled_builder_exception_is_propagated_unchanged(self) -> None:
        expected = SimulationBetEvaluationError("non_settled")
        with patch.object(simulator, "_decide_non_settled_status", return_value=self.decision(SettlementStatus.ERROR, "x")), patch.object(simulator, "_build_non_settled_simulation_result", side_effect=expected):
            with self.assertRaises(SimulationBetEvaluationError) as caught: self.invoke()
        self.assertIs(caught.exception, expected)

    def test_no_bet_builder_exception_is_propagated_unchanged(self) -> None:
        expected = SimulationBetEvaluationError("no_bet")
        with patch.object(simulator, "_build_no_bet_simulation_result", side_effect=expected):
            with self.assertRaises(SimulationBetEvaluationError) as caught: self.invoke(bets=(), publications_by_bet_type={})
        self.assertIs(caught.exception, expected)

    def test_does_not_mutate_bets_input(self) -> None:
        bets = [make_bet()]
        self.invoke(bets=bets)
        self.assertEqual(bets, [bets[0]])

    def test_does_not_mutate_publications_mapping(self) -> None:
        publications = {"単勝": make_publication()}
        self.invoke(publications_by_bet_type=publications)
        self.assertEqual(publications, {"単勝": publications["単勝"]})

    def test_does_not_mutate_completeness_input(self) -> None:
        statuses = [CompletenessStatus.COMPLETE]
        self.invoke(completeness_statuses=statuses)
        self.assertEqual(statuses, [CompletenessStatus.COMPLETE])

    def test_does_not_mutate_payout_status_input(self) -> None:
        statuses = [PayoutStatus.WINNING]
        self.invoke(payout_statuses=statuses)
        self.assertEqual(statuses, [PayoutStatus.WINNING])

    def test_does_not_mutate_missing_bet_type_input(self) -> None:
        values = ["単勝"]
        self.invoke(missing_payout_bet_types=values)
        self.assertEqual(values, ["単勝"])

    def test_helper_is_keyword_only(self) -> None:
        signature = inspect.signature(_build_simulation_result_for_race)
        self.assertTrue(all(item.kind is inspect.Parameter.KEYWORD_ONLY for item in signature.parameters.values()))

    def test_helper_is_not_exported_from_package_root(self) -> None:
        self.assertNotIn("_build_simulation_result_for_race", simulation_package.__all__)
        self.assertFalse(hasattr(simulation_package, "_build_simulation_result_for_race"))

    def test_helper_does_not_call_provider_or_repository(self) -> None:
        source = inspect.getsource(_build_simulation_result_for_race)
        self.assertNotIn("providers.", source)
        self.assertNotIn("repositories.", source)

    def test_helper_does_not_access_database_or_network(self) -> None:
        source = inspect.getsource(_build_simulation_result_for_race).lower()
        for forbidden in ("sqlite", "requests", "urllib", "socket", "http"):
            self.assertNotIn(forbidden, source)

    def test_helper_does_not_use_current_time_or_logging(self) -> None:
        source = inspect.getsource(_build_simulation_result_for_race).lower()
        self.assertNotIn("datetime.now", source)
        self.assertNotIn("datetime.utcnow", source)
        self.assertNotIn("logging", source)

    def test_helper_does_not_create_summary_or_metrics(self) -> None:
        source = inspect.getsource(_build_simulation_result_for_race).lower()
        for forbidden in ("summary", "roi", "drawdown", "hit_rate", "csv", "cli"):
            self.assertNotIn(forbidden, source)

    def test_helper_has_no_async_or_threading(self) -> None:
        source = inspect.getsource(_build_simulation_result_for_race).lower()
        for forbidden in ("async", "await", "thread", "multiprocessing"):
            self.assertNotIn(forbidden, source)

    def test_helper_calls_only_the_approved_internal_helpers(self) -> None:
        tree = ast.parse(inspect.getsource(_build_simulation_result_for_race))
        calls = {node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
        self.assertTrue({"_evaluate_simulation_race_bets", "_decide_non_settled_status", "_build_settled_simulation_result", "_build_non_settled_simulation_result", "_build_no_bet_simulation_result"} >= (calls & {name for name in calls if name.startswith("_")}))

    def test_non_settled_builder_receives_original_bets(self) -> None:
        bets = (make_bet(),)
        decision = self.decision(SettlementStatus.UNSETTLED, "missing")
        with patch.object(simulator, "_evaluate_simulation_race_bets") as evaluate, patch.object(simulator, "_decide_non_settled_status", return_value=decision), patch.object(simulator, "_build_non_settled_simulation_result", return_value=object()) as builder:
            self.invoke(bets=bets)
        self.assertIs(builder.call_args.kwargs["bets"], bets)
        evaluate.assert_not_called()

    def test_non_settled_builder_receives_decision_identity(self) -> None:
        decision = self.decision(SettlementStatus.ERROR, "exact_reason")
        with patch.object(simulator, "_decide_non_settled_status", return_value=decision), patch.object(simulator, "_build_non_settled_simulation_result", return_value=object()) as builder:
            self.invoke()
        self.assertIs(builder.call_args.kwargs["settlement_status"], decision.settlement_status)
        self.assertIs(builder.call_args.kwargs["exclusion_reason"], decision.exclusion_reason)

    def test_empty_bets_do_not_require_publication_facts(self) -> None:
        result = self.invoke(bets=(), publications_by_bet_type={}, completeness_statuses="invalid")
        self.assertEqual(result.settlement_status, SettlementStatus.NO_BET)

    def test_non_empty_settled_bets_require_decision_before_evaluation(self) -> None:
        events: list[str] = []
        evaluation = self.evaluation()
        with patch.object(simulator, "_decide_non_settled_status", side_effect=lambda **kwargs: events.append("decision")), patch.object(simulator, "_evaluate_simulation_race_bets", side_effect=lambda *args: events.append("evaluate") or evaluation), patch.object(simulator, "_build_settled_simulation_result", side_effect=lambda *args: events.append("settled") or object()):
            self.invoke()
        self.assertEqual(events, ["decision", "evaluate", "settled"])


if __name__ == "__main__":
    unittest.main()
