from __future__ import annotations

import ast
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
import inspect
from pathlib import Path
from types import SimpleNamespace
from typing import get_type_hints
import unittest
from unittest.mock import patch

import scripts.simulation as simulation_package
import scripts.simulation.final_historical_settlement_simulation as module
from scripts.simulation.bet_plan_snapshot_repository import SimulationBetPlanSnapshotSource
from scripts.simulation.historical_input_snapshots import HistoricalInputSnapshot
from scripts.simulation.models import SimulationRunContext, SimulationSummary, StrategyIdentity
from scripts.simulation.repositories.interfaces import PayoutRepository, RaceResultRepository, RaceResultStatus
from tests.test_historical_settlement_simulation import (
    HistoricalSettlementSimulationTests,
    payout_publication,
    persisted_result,
)
from tests.test_simulation_summary_builder import no_bet, non_settled, settled, summary


NOW = datetime(2026, 8, 28, 12, tzinfo=UTC)


def _summary_for(*states: object) -> SimulationSummary:
    return summary(states)


class FinalHistoricalSettlementSimulationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.snapshots = (object(), object())
        self.run_context = object()
        self.strategy_identity = object()
        self.cutoffs = {101: NOW, 102: NOW}
        self.plan_source = object()
        self.result_repository = object()
        self.payout_repository = object()

    def _values(self) -> dict[str, object]:
        return {
            "snapshots": self.snapshots,
            "run_context": self.run_context,
            "strategy_identity": self.strategy_identity,
            "settlement_cutoffs_by_race_id": self.cutoffs,
            "bet_plan_snapshot_source": self.plan_source,
            "race_result_repository": self.result_repository,
            "payout_repository": self.payout_repository,
        }

    def _call_with(self, delegated: object) -> object:
        with patch.object(module, "execute_historical_settlement_simulation", return_value=delegated) as delegate:
            result = module.execute_final_historical_settlement_simulation(**self._values())  # type: ignore[arg-type]
        delegate.assert_called_once_with(**self._values())
        return result

    def _assert_blocked(self, delegated: SimulationSummary) -> None:
        with patch.object(module, "execute_historical_settlement_simulation", return_value=delegated) as delegate:
            with self.assertRaises(module.FinalHistoricalSettlementNotReadyError):
                module.execute_final_historical_settlement_simulation(**self._values())  # type: ignore[arg-type]
        delegate.assert_called_once_with(**self._values())

    def test_public_surface_signature_hints_and_error_hierarchy_are_exact(self) -> None:
        self.assertEqual(module.__all__, ("FinalHistoricalSettlementNotReadyError", "execute_final_historical_settlement_simulation"))
        self.assertFalse(hasattr(simulation_package, "execute_final_historical_settlement_simulation"))
        signature = inspect.signature(module.execute_final_historical_settlement_simulation)
        self.assertEqual(tuple(signature.parameters), ("snapshots", "run_context", "strategy_identity", "settlement_cutoffs_by_race_id", "bet_plan_snapshot_source", "race_result_repository", "payout_repository"))
        self.assertTrue(all(value.kind is inspect.Parameter.KEYWORD_ONLY for value in signature.parameters.values()))
        self.assertEqual(get_type_hints(module.execute_final_historical_settlement_simulation), {
            "snapshots": tuple[HistoricalInputSnapshot, ...],
            "run_context": SimulationRunContext,
            "strategy_identity": StrategyIdentity,
            "settlement_cutoffs_by_race_id": Mapping[int, datetime],
            "bet_plan_snapshot_source": SimulationBetPlanSnapshotSource,
            "race_result_repository": RaceResultRepository,
            "payout_repository": PayoutRepository,
            "return": SimulationSummary,
        })
        self.assertTrue(issubclass(module.FinalHistoricalSettlementNotReadyError, ValueError))

    def test_exact_delegation_passes_every_object_through_once_without_mutation(self) -> None:
        delegated = _summary_for(settled(101), no_bet(102))
        snapshots_before = self.snapshots
        cutoffs_before = dict(self.cutoffs)
        self.assertIs(self._call_with(delegated), delegated)
        self.assertIs(self.snapshots, snapshots_before)
        self.assertEqual(self.cutoffs, cutoffs_before)

    def test_all_settled_all_no_bet_and_mixed_final_summaries_return_exact_delegate_object(self) -> None:
        for delegated in (
            _summary_for(settled(101), settled(102)),
            _summary_for(no_bet(101), no_bet(102)),
            _summary_for(settled(101), no_bet(102)),
        ):
            with self.subTest(summary=delegated):
                self.assertIs(self._call_with(delegated), delegated)

    def test_unsettled_void_error_and_unsupported_states_each_block_final_return(self) -> None:
        from scripts.simulation.models import SettlementStatus

        for status in (
            SettlementStatus.UNSETTLED,
            SettlementStatus.VOID,
            SettlementStatus.ERROR,
            SettlementStatus.UNSUPPORTED,
        ):
            with self.subTest(status=status):
                self._assert_blocked(_summary_for(non_settled(101, status=status), no_bet(102)))

    def test_multiple_blocking_states_raise_one_not_ready_error(self) -> None:
        from scripts.simulation.models import SettlementStatus

        self._assert_blocked(_summary_for(
            non_settled(101, status=SettlementStatus.UNSETTLED),
            non_settled(102, status=SettlementStatus.UNSUPPORTED),
        ))

    def test_explicit_final_count_equality_predicate_rejects_synthetic_mismatch(self) -> None:
        delegated = SimpleNamespace(
            race_count=2,
            settled_race_count=1,
            no_bet_race_count=0,
            unsettled_race_count=0,
            void_race_count=0,
            error_race_count=0,
            unsupported_race_count=0,
        )
        with patch.object(module, "execute_historical_settlement_simulation", return_value=delegated) as delegate:
            with self.assertRaisesRegex(module.FinalHistoricalSettlementNotReadyError, "race_count=2"):
                module.execute_final_historical_settlement_simulation(**self._values())  # type: ignore[arg-type]
        self.assertEqual(delegate.call_count, 1)

    def test_delegate_exception_propagates_unchanged_without_retry(self) -> None:
        error = RuntimeError("delegate failure")
        with patch.object(module, "execute_historical_settlement_simulation", side_effect=error) as delegate:
            with self.assertRaises(RuntimeError) as raised:
                module.execute_final_historical_settlement_simulation(**self._values())  # type: ignore[arg-type]
        self.assertIs(raised.exception, error)
        self.assertEqual(delegate.call_count, 1)

    def _historical_values(self, case: HistoricalSettlementSimulationTests) -> dict[str, object]:
        return {
            "snapshots": (case.first, case.second, case.third),
            "run_context": case.run_context,
            "strategy_identity": case.strategy_identity,
            "settlement_cutoffs_by_race_id": case.cutoffs,
            "bet_plan_snapshot_source": case.plan_source,
            "race_result_repository": case.result_repository,
            "payout_repository": case.payout_repository,
        }

    def _install_complete_facts(self, case: HistoricalSettlementSimulationTests, *, complete_payout: bool = True) -> None:
        for snapshot in (case.first, case.second, case.third):
            observed_at = case.cutoffs[snapshot.internal_race_id] - timedelta(minutes=1)
            case.result_repository.responses[snapshot.internal_race_id] = persisted_result(
                snapshot,
                observed_at=observed_at,
            )
            case.payout_repository.responses[(snapshot.internal_race_id, "単勝")] = (
                payout_publication(snapshot, observed_at=observed_at, complete=complete_payout),
            )

    def test_real_c4g2b_missing_result_missing_payout_and_incomplete_payout_cannot_escape_finality(self) -> None:
        for condition in ("missing_result", "missing_payout", "incomplete_payout"):
            with self.subTest(condition=condition):
                case = HistoricalSettlementSimulationTests()
                case.setUp()
                case.install_plans((case.first, case.second, case.third))
                if condition != "missing_result":
                    self._install_complete_facts(case, complete_payout=condition != "incomplete_payout")
                    if condition == "missing_payout":
                        case.payout_repository.responses.pop((case.first.internal_race_id, "単勝"))
                with self.assertRaises(module.FinalHistoricalSettlementNotReadyError):
                    module.execute_final_historical_settlement_simulation(**self._historical_values(case))  # type: ignore[arg-type]

    def test_real_c4g2b_unsupported_and_after_cutoff_states_cannot_escape_finality(self) -> None:
        for condition in ("unsupported", "after_cutoff"):
            with self.subTest(condition=condition):
                case = HistoricalSettlementSimulationTests()
                case.setUp()
                case.install_plans((case.first, case.second, case.third))
                self._install_complete_facts(case)
                target = case.first
                observed_at = case.cutoffs[target.internal_race_id] - timedelta(minutes=1)
                if condition == "unsupported":
                    case.result_repository.responses[target.internal_race_id] = persisted_result(
                        target,
                        observed_at=observed_at,
                        status=RaceResultStatus.UNSUPPORTED,
                    )
                else:
                    case.result_repository.responses[target.internal_race_id] = persisted_result(
                        target,
                        observed_at=case.cutoffs[target.internal_race_id] + timedelta(microseconds=1),
                    )
                with self.assertRaises(module.FinalHistoricalSettlementNotReadyError):
                    module.execute_final_historical_settlement_simulation(**self._historical_values(case))  # type: ignore[arg-type]

    def test_static_ownership_contract_remains_a_thin_finality_wrapper(self) -> None:
        source = Path(module.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        forbidden = (
            "requests", "httpx", "sqlite", "BeautifulSoup", "official_settlement_acquisition",
            "HistoricalPersistedRaceSettlementSource", "PersistedRaceSimulationExecutor", "Simulator",
            "datetime.now", "get_race_result", "get_latest_payout_publication", "save_race_result",
            "save_payout_publication",
        )
        self.assertFalse(any(value in source for value in forbidden))
        self.assertFalse(any(
            isinstance(node, ast.ExceptHandler)
            and (node.type is None or isinstance(node.type, ast.Name) and node.type.id in {"Exception", "BaseException"})
            for node in ast.walk(tree)
        ))


if __name__ == "__main__":
    unittest.main()
