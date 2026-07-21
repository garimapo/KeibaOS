"""シミュレーション用ドメインモデルの不変条件テスト。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
import unittest

from scripts.prediction.bet_strategy import StrategyConfig
from scripts.simulation.models import (
    BetTypeSummary, PayoutEntry, PayoutTable, RefundEntry, SettlementStatus,
    SimulationBet, SimulationReport, SimulationResult, SimulationRunContext,
    SimulationRunMetadata, SimulationSummary, build_strategy_identity,
)
from scripts.simulation.serialization import to_json_compatible


UTC = timezone.utc
NOW = datetime(2026, 1, 10, 9, 0, tzinfo=UTC)


def identity():
    return build_strategy_identity("Rule", StrategyConfig())


def bet(strategy_id: str) -> SimulationBet:
    return SimulationBet(1, strategy_id, "単勝", [1], 100, 1, NOW)


def summary(strategy_id: str, *, status: SettlementStatus = SettlementStatus.SETTLED) -> SimulationSummary:
    settled = int(status is SettlementStatus.SETTLED)
    error = int(status is SettlementStatus.ERROR)
    by_type = {} if not settled else {"単勝": BetTypeSummary("単勝", 1, 1, 1, 100, 220, 120, Decimal("220"), Decimal("100"))}
    return SimulationSummary(
        strategy_id=strategy_id, strategy_name="Rule", strategy_config_hash=identity().strategy_config_hash, race_count=1,
        settled_race_count=settled, unsettled_race_count=0, no_bet_race_count=0,
        void_race_count=0, error_race_count=error, unsupported_race_count=0,
        bet_count=1 if settled else 0, settled_bet_count=1 if settled else 0,
        settled_purchase_race_count=1 if settled else 0,
        hit_bet_count=1 if settled else 0, hit_race_count=1 if settled else 0,
        investment=100 if settled else 0, payout=220 if settled else 0,
        profit=120 if settled else 0, roi=Decimal("220") if settled else None,
        bet_hit_rate=Decimal("100") if settled else None,
        race_hit_rate=Decimal("100") if settled else None, maximum_drawdown=0, by_bet_type=by_type,
    )


class SimulationModelTest(unittest.TestCase):
    def test_strategy_hash_is_deterministic_and_sensitive_to_config(self) -> None:
        first = identity()
        same = build_strategy_identity("Rule", StrategyConfig(allowed_bet_types=frozenset({"3連複", "馬連", "単勝", "ワイド"})))
        changed = build_strategy_identity("Rule", StrategyConfig(max_bet_count=11))
        self.assertEqual(first.strategy_config_hash, same.strategy_config_hash)
        self.assertNotEqual(first.strategy_config_hash, changed.strategy_config_hash)

    def test_bet_constraints_and_normalization(self) -> None:
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            SimulationBet(1, "s", "単勝", [1], 100, 1, datetime(2026, 1, 1))
        with self.assertRaisesRegex(ValueError, "multiple of 100"):
            SimulationBet(1, "s", "単勝", [1], 50, 1, NOW)
        with self.assertRaisesRegex(ValueError, "requires 1 unique"):
            SimulationBet(1, "s", "単勝", [1, 2], 100, 1, NOW)
        with self.assertRaisesRegex(ValueError, "requires 1 unique"):
            SimulationBet(1, "s", "単勝", [1, 1], 100, 1, NOW)

    def test_settlement_money_and_status_invariants(self) -> None:
        item = bet("s")
        settled = SimulationResult(1, "s", [item], SettlementStatus.SETTLED, None, 100, 100, 220, 120, 1, NOW)
        self.assertEqual(settled.profit, 120)
        for status in (SettlementStatus.UNSETTLED, SettlementStatus.VOID, SettlementStatus.ERROR, SettlementStatus.UNSUPPORTED):
            reason = "reason"
            result = SimulationResult(1, "s", [item], status, reason, 100)
            self.assertIsNone(result.payout)
        with self.assertRaisesRegex(ValueError, "settled_investment"):
            SimulationResult(1, "s", [item], SettlementStatus.SETTLED, None, 100, 50, 220, 170, 1, NOW)
        with self.assertRaisesRegex(ValueError, "non-SETTLED"):
            SimulationResult(1, "s", [item], SettlementStatus.UNSETTLED, "reason", 100, payout=0)

    def test_refund_is_not_winning_and_payout_table_prevents_duplicates(self) -> None:
        table = PayoutTable(1, "単勝", True, NOW, NOW, "JRA", [PayoutEntry([1], 220)], [RefundEntry([2], 100, "cancelled")])
        self.assertEqual(table.refunds[0].payout_status, "refund")
        with self.assertRaisesRegex(ValueError, "overlap"):
            PayoutTable(1, "単勝", True, NOW, NOW, "JRA", [PayoutEntry([1], 220)], [RefundEntry([1], 100, "cancelled")])

    def test_context_metadata_and_report_consistency(self) -> None:
        context = SimulationRunContext("run", "dataset", NOW, "commit")
        self.assertFalse(hasattr(context, "completed_at"))
        item = identity()
        metadata = SimulationRunMetadata("run", "dataset", NOW, NOW + timedelta(seconds=1), "commit")
        result = SimulationResult(1, item.strategy_id, [bet(item.strategy_id)], SettlementStatus.SETTLED, None, 100, 100, 220, 120, 1, NOW)
        report = SimulationReport(metadata, [item], [result], {item.strategy_id: summary(item.strategy_id)}, True)
        self.assertTrue(report.official_roi_valid)
        error = SimulationResult(2, item.strategy_id, [], SettlementStatus.ERROR, "future", 0)
        with self.assertRaisesRegex(ValueError, "official_roi_valid"):
            SimulationReport(metadata, [item], [error], {item.strategy_id: summary(item.strategy_id, status=SettlementStatus.ERROR)}, True, ["future"])

    def test_summary_rates_and_decimal_precision_are_verified(self) -> None:
        item = identity()
        self.assertEqual(summary(item.strategy_id).roi, Decimal("220"))
        with self.assertRaisesRegex(ValueError, "rates"):
            SimulationSummary(
                strategy_id=item.strategy_id, strategy_name="Rule", strategy_config_hash=item.strategy_config_hash, race_count=0,
                settled_race_count=0, unsettled_race_count=0, no_bet_race_count=0,
                void_race_count=0, error_race_count=0, unsupported_race_count=0,
                bet_count=0, settled_bet_count=0, settled_purchase_race_count=0,
                hit_bet_count=0, hit_race_count=0, investment=0, payout=0, profit=0,
                roi=Decimal("0"), bet_hit_rate=None, race_hit_rate=None,
                maximum_drawdown=0,
            )

    def test_json_serializer_preserves_decimal_and_datetime(self) -> None:
        value = to_json_compatible({"amount": Decimal("1.2300"), "time": NOW, "status": SettlementStatus.SETTLED})
        self.assertEqual(value["amount"], "1.2300")
        self.assertEqual(value["time"], NOW.isoformat())
        self.assertEqual(value["status"], "settled")
        json.dumps(value)

    def test_bet_type_summary_rates_are_recalculated(self) -> None:
        with self.assertRaisesRegex(ValueError, "rates"):
            BetTypeSummary("単勝", 1, 1, 1, 100, 200, 100, Decimal("100"), Decimal("100"))
        with self.assertRaisesRegex(ValueError, "rates"):
            BetTypeSummary("単勝", 1, 1, 1, 100, 200, 100, Decimal("200"), Decimal("0"))
        with self.assertRaisesRegex(ValueError, "rates"):
            BetTypeSummary("単勝", 1, 0, 0, 0, 0, 0, Decimal("0"), Decimal("0"))
        with self.assertRaisesRegex(ValueError, "rates"):
            BetTypeSummary("単勝", 0, 0, 0, 0, 0, 0, None, Decimal("0"))

    def test_bet_type_summary_uses_settled_bet_denominator(self) -> None:
        value = BetTypeSummary("単勝", 2, 1, 1, 100, 200, 100, Decimal("200"), Decimal("100"))
        self.assertEqual(value.bet_hit_rate, Decimal("100"))
        with self.assertRaisesRegex(ValueError, "rates"):
            BetTypeSummary("単勝", 2, 1, 1, 100, 200, 100, Decimal("200"), Decimal("50"))
        with self.assertRaises(ValueError):
            BetTypeSummary("単勝", 1, 2, 1, 100, 200, 100, Decimal("200"), Decimal("50"))
        with self.assertRaises(ValueError):
            BetTypeSummary("単勝", 1, 1, 2, 100, 200, 100, Decimal("200"), Decimal("200"))

    def test_settlement_money_requires_settled_bets_and_100_yen_units(self) -> None:
        with self.assertRaises(ValueError):
            BetTypeSummary("単勝", 1, 1, 0, 0, 0, 0, None, None)
        with self.assertRaises(ValueError):
            BetTypeSummary("単勝", 0, 0, 0, 0, 100, 100, None, None)
        with self.assertRaises(ValueError):
            BetTypeSummary("単勝", 1, 1, 0, 50, 50, 0, Decimal("100"), None)

    def test_strict_settlement_numeric_types_and_time(self) -> None:
        item = bet("s")
        for invalid in (Decimal("100"), 100.0, "100", True):
            with self.assertRaises(TypeError):
                SimulationResult(1, "s", [item], SettlementStatus.SETTLED, None, 100, invalid, 220, 120, 1, NOW)
        with self.assertRaises(TypeError):
            SimulationResult(1, "s", [item], SettlementStatus.SETTLED, None, 100, 100, 220, 120, True, NOW)
        with self.assertRaises((TypeError, ValueError)):
            SimulationResult(1, "s", [item], SettlementStatus.SETTLED, None, 100, 100, -1, -101, 1, NOW)
        with self.assertRaises(ValueError):
            SimulationResult(1, "s", [item], SettlementStatus.SETTLED, None, 100, 100, 220, 120, 1, NOW - timedelta(seconds=1))

    def test_report_and_strategy_config_are_json_compatible(self) -> None:
        item = identity()
        metadata = SimulationRunMetadata("run", "dataset", NOW, NOW, "commit")
        result = SimulationResult(1, item.strategy_id, [bet(item.strategy_id)], SettlementStatus.SETTLED, None, 100, 100, 220, 120, 1, NOW)
        report = SimulationReport(metadata, [item], [result], {item.strategy_id: summary(item.strategy_id)}, True)
        encoded = to_json_compatible(report)
        self.assertEqual(encoded["strategy_identities"][0]["strategy_config"]["allowed_bet_types"], sorted(encoded["strategy_identities"][0]["strategy_config"]["allowed_bet_types"]))
        json.dumps(encoded)
