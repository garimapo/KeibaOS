"""Explicit-selection, read-only NAR daily replay aggregation tests."""

from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import FrozenInstanceError, fields, replace
from datetime import date
from decimal import Decimal
from hashlib import sha256
import inspect
import json
from pathlib import Path
import sqlite3
import tempfile
from typing import get_type_hints
import unittest
from unittest.mock import patch

import scripts.simulation.nar_daily_replay_aggregation as subject
from scripts.migrations.runner import apply_migrations
from scripts.simulation.models import BetTypeSummary, SimulationSummary
from scripts.simulation.nar_daily_replay_orchestrator import NARDailyReplayExecutionState
from scripts.simulation.repositories.errors import RepositoryValidationError
from scripts.simulation.repositories.sqlite_nar_daily_replay_result_repository import (
    SQLiteNARDailyReplayResultRepository,
)
from tests.test_nar_daily_replay_result_persistence import build_record


def _audit(label: str) -> str:
    return sha256(label.encode("utf-8")).hexdigest()


def _bet(
    bet_type: str,
    *,
    bet_count: int,
    hit_count: int,
    investment: int,
    payout: int,
) -> BetTypeSummary:
    return BetTypeSummary(
        bet_type=bet_type,
        bet_count=bet_count,
        settled_bet_count=bet_count,
        hit_bet_count=hit_count,
        investment=investment,
        payout=payout,
        profit=payout - investment,
        roi=None if investment == 0 else Decimal(payout) * Decimal("100") / Decimal(investment),
        bet_hit_rate=None if bet_count == 0 else Decimal(hit_count) * Decimal("100") / Decimal(bet_count),
    )


def _summary(
    record,
    values: tuple[BetTypeSummary, ...],
    *,
    drawdown: int,
    race_count: int = 1,
    hit_race_count: int | None = None,
) -> SimulationSummary:
    by_type = {value.bet_type: value for value in values}
    bet_count = sum(value.bet_count for value in values)
    hit_bet_count = sum(value.hit_bet_count for value in values)
    investment = sum(value.investment for value in values)
    payout = sum(value.payout for value in values)
    if hit_race_count is None:
        hit_race_count = 1 if hit_bet_count else 0
    return SimulationSummary(
        strategy_id=record.strategy_id,
        strategy_name=record.strategy_name,
        strategy_config_hash=record.strategy_config_hash,
        race_count=race_count,
        settled_race_count=race_count,
        unsettled_race_count=0,
        no_bet_race_count=0,
        void_race_count=0,
        error_race_count=0,
        unsupported_race_count=0,
        bet_count=bet_count,
        settled_bet_count=bet_count,
        settled_purchase_race_count=race_count,
        hit_bet_count=hit_bet_count,
        hit_race_count=hit_race_count,
        investment=investment,
        payout=payout,
        profit=payout - investment,
        roi=Decimal(payout) * Decimal("100") / Decimal(investment),
        bet_hit_rate=Decimal(hit_bet_count) * Decimal("100") / Decimal(bet_count),
        race_hit_rate=(
            Decimal(hit_race_count) * Decimal("100") / Decimal(race_count)
        ),
        maximum_drawdown=drawdown,
        by_bet_type=by_type,
    )


def _target_count_changes(record, count: int) -> dict[str, object]:
    source = json.loads(record.resolution_outcomes_json)[0]
    outcomes = []
    for race_number in range(1, count + 1):
        outcome = deepcopy(source)
        external_race_id = f"nar:20250101:01:{race_number:02d}"
        outcome["internal_race_id"] = race_number
        outcome["target_key"][2] = external_race_id
        outcome["snapshot_identity"]["external_race_id"] = external_race_id
        for key in ("result_capture_reference", "payout_capture_reference"):
            reference = outcome[key]
            reference["canonical_source_url"] = (
                "https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/"
                f"RaceMarkTable?k_raceNo={race_number}"
            )
            reference["capture_id"] = f"settlement-{race_number}"
            reference["response_sha256"] = str(race_number) * 64
        outcomes.append(outcome)
    return {
        "target_set_content_sha256": _audit(f"targets-{count}-{record.run_id}"),
        "canonical_target_count": count,
        "executable_count": count,
        "resolution_outcomes_json": json.dumps(
            outcomes,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ),
        "race_list_capture_ids": tuple(
            f"race-list-{race_number}" for race_number in range(1, count + 1)
        ),
    }


class NARDailyReplayAggregationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        seed = build_record(
            self.root, NARDailyReplayExecutionState.FULL_DAY_REPLAY_COMPLETED
        )
        self.connection = sqlite3.connect(seed.database_path)
        self.addCleanup(self.connection.close)
        apply_migrations(self.connection)
        self.serial = 0
        self.repository = SQLiteNARDailyReplayResultRepository(
            connection=self.connection,
            database_path=seed.database_path,
        )

    def _record(
        self,
        day: int,
        state: NARDailyReplayExecutionState,
        *,
        label: str | None = None,
        summary: SimulationSummary | None = None,
        completed_no_bet: bool = False,
    ):
        self.serial += 1
        tag = label or f"{state.value}-{day}-{self.serial}"
        record = build_record(
            self.root,
            state,
            run_id=f"run-{tag}",
            manifest_name=f"manifest-{tag}.json",
            completed_no_bet=completed_no_bet,
        )
        changes = {
            "target_date": date(2025, 1, day),
            "orchestration_audit_sha256": _audit(f"audit-{tag}"),
        }
        if summary is not None:
            changes["summary"] = summary
        return replace(record, **changes)

    def _completed(self, day: int, *, second: bool = False):
        record = self._record(day, NARDailyReplayExecutionState.FULL_DAY_REPLAY_COMPLETED)
        values = (
            (
                _bet("単勝", bet_count=3, hit_count=0, investment=300, payout=0),
                _bet("ワイド", bet_count=6, hit_count=3, investment=600, payout=1200),
            )
            if second
            else (_bet("単勝", bet_count=1, hit_count=1, investment=100, payout=300),)
        )
        changes = _target_count_changes(record, 4) if second else {}
        changes["summary"] = _summary(
            record,
            values,
            drawdown=40 if second else 25,
            race_count=4 if second else 1,
            hit_race_count=1,
        )
        return replace(record, **changes)

    def _save(self, *records) -> subject.NARDailyReplayAggregationSelection:
        for record in records:
            self.repository.save_result(record=record)
        return subject.NARDailyReplayAggregationSelection(
            schema_version=1,
            persisted_content_sha256s=tuple(
                record.persisted_content_sha256 for record in records
            ),
        )

    def _aggregate(self, *records):
        return subject.aggregate_nar_daily_replay_selection(
            selection=self._save(*records), repository=self.repository
        )

    def test_public_surface_signatures_and_frozen_values(self) -> None:
        self.assertEqual(
            subject.__all__,
            (
                "NARDailyReplayAggregationSelection",
                "NARDailyReplayAggregationResult",
                "aggregate_nar_daily_replay_selection",
            ),
        )
        self.assertEqual(
            {name for name in vars(subject) if not name.startswith("_")},
            set(subject.__all__),
        )
        self.assertEqual(
            tuple(inspect.signature(subject.aggregate_nar_daily_replay_selection).parameters),
            ("selection", "repository"),
        )
        self.assertIs(
            get_type_hints(subject.aggregate_nar_daily_replay_selection)["repository"],
            SQLiteNARDailyReplayResultRepository,
        )
        selection = self._save(self._completed(1))
        with self.assertRaises(FrozenInstanceError):
            selection.schema_version = 2

    def test_public_application_rejects_structural_repository_substitute(self) -> None:
        class FakeRepository:
            def load_result(self, *, persisted_content_sha256: str):
                return None

        selection = subject.NARDailyReplayAggregationSelection(1, ("a" * 64,))
        with self.assertRaisesRegex(RepositoryValidationError, "exact SQLite"):
            subject.aggregate_nar_daily_replay_selection(
                selection=selection, repository=FakeRepository()
            )

    def test_empty_malformed_and_duplicate_selection_rejected(self) -> None:
        with self.assertRaises(RepositoryValidationError):
            subject.NARDailyReplayAggregationSelection(1, ())
        with self.assertRaises(RepositoryValidationError):
            subject.NARDailyReplayAggregationSelection(1, ("A" * 64,))
        digest = "a" * 64
        with self.assertRaises(RepositoryValidationError):
            subject.NARDailyReplayAggregationSelection(1, (digest, digest))

    def test_missing_exact_identity_fails_closed(self) -> None:
        selection = subject.NARDailyReplayAggregationSelection(1, ("a" * 64,))
        with self.assertRaisesRegex(RepositoryValidationError, "does not exist"):
            subject.aggregate_nar_daily_replay_selection(
                selection=selection, repository=self.repository
            )

    def test_single_completed_record(self) -> None:
        record = self._completed(1)
        result = self._aggregate(record)
        self.assertEqual((result.selected_record_count, result.completed_day_count), (1, 1))
        self.assertEqual((result.first_target_date, result.last_target_date), (record.target_date,) * 2)
        self.assertEqual((result.investment, result.payout, result.profit), (100, 300, 200))

    def test_public_result_constructor_rejects_forged_date_coverage(self) -> None:
        result = self._aggregate(self._completed(1), self._completed(2, second=True))
        constructor_values = {
            item.name: getattr(result, item.name)
            for item in fields(result)
            if item.init
        }
        constructor_values.update(
            first_target_date=date(2000, 1, 1),
            last_target_date=date(2000, 1, 2),
        )
        with self.assertRaisesRegex(
            RepositoryValidationError, "must be produced by aggregate"
        ):
            subject.NARDailyReplayAggregationResult(**constructor_values)
        with self.assertRaises(RepositoryValidationError):
            replace(result, first_target_date=date(2000, 1, 1))

    def test_public_result_constructor_rejects_forged_state_counts(self) -> None:
        result = self._aggregate(
            self._completed(1),
            self._record(2, NARDailyReplayExecutionState.NOT_RUN_PARTIAL_RESOLUTION),
        )
        constructor_values = {
            item.name: getattr(result, item.name)
            for item in fields(result)
            if item.init
        }
        constructor_values.update(
            completed_day_count=2,
            partial_resolution_diagnostic_day_count=0,
        )
        with self.assertRaisesRegex(
            RepositoryValidationError, "must be produced by aggregate"
        ):
            subject.NARDailyReplayAggregationResult(**constructor_values)
        self.assertEqual(
            (
                result.first_target_date,
                result.last_target_date,
                result.completed_day_count,
                result.partial_resolution_diagnostic_day_count,
                result.no_executable_diagnostic_day_count,
            ),
            (date(2025, 1, 1), date(2025, 1, 2), 1, 1, 0),
        )

    def test_multiple_completed_totals_rates_and_bet_types(self) -> None:
        result = self._aggregate(self._completed(1), self._completed(2, second=True))
        self.assertEqual((result.race_count, result.bet_count, result.settled_bet_count), (5, 10, 10))
        self.assertEqual((result.hit_bet_count, result.investment, result.payout, result.profit), (4, 1000, 1500, 500))
        self.assertEqual(
            (
                result.settled_purchase_race_count,
                result.hit_race_count,
                result.roi,
                result.bet_hit_rate,
                result.race_hit_rate,
            ),
            (5, 2, Decimal("150"), Decimal("40"), Decimal("40")),
        )
        self.assertEqual(tuple(result.by_bet_type), ("ワイド", "単勝"))
        win = result.by_bet_type["単勝"]
        self.assertEqual((win.bet_count, win.hit_bet_count, win.investment, win.payout), (4, 1, 400, 300))
        self.assertEqual((win.roi, win.bet_hit_rate), (Decimal("75"), Decimal("25")))
        wide = result.by_bet_type["ワイド"]
        self.assertEqual((wide.bet_count, wide.roi, wide.bet_hit_rate), (6, Decimal("200"), Decimal("50")))
        self.assertNotEqual(result.roi, (Decimal("300") + Decimal(1200) * 100 / 900) / 2)
        self.assertNotEqual(
            result.race_hit_rate, (Decimal("100") + Decimal("25")) / 2
        )

    def test_mixed_diagnostics_remain_counted_but_financially_absent(self) -> None:
        completed = self._completed(1)
        partial = self._record(2, NARDailyReplayExecutionState.NOT_RUN_PARTIAL_RESOLUTION)
        zero = self._record(3, NARDailyReplayExecutionState.NOT_RUN_NO_EXECUTABLE_TARGETS)
        result = self._aggregate(completed, partial, zero)
        self.assertEqual(
            (
                result.selected_record_count,
                result.completed_day_count,
                result.partial_resolution_diagnostic_day_count,
                result.no_executable_diagnostic_day_count,
            ),
            (3, 1, 1, 1),
        )
        self.assertEqual((result.race_count, result.investment, result.payout), (1, 100, 300))
        self.assertEqual((result.first_target_date, result.last_target_date), (date(2025, 1, 1), date(2025, 1, 3)))

    def test_diagnostic_only_selection_has_exact_empty_completed_semantics(self) -> None:
        result = self._aggregate(
            self._record(1, NARDailyReplayExecutionState.NOT_RUN_PARTIAL_RESOLUTION),
            self._record(2, NARDailyReplayExecutionState.NOT_RUN_NO_EXECUTABLE_TARGETS),
        )
        self.assertEqual((result.selected_record_count, result.completed_day_count), (2, 0))
        self.assertEqual((result.race_count, result.bet_count, result.investment, result.payout, result.profit), (0, 0, 0, 0, 0))
        self.assertEqual((result.roi, result.bet_hit_rate, result.race_hit_rate), (None, None, None))
        self.assertEqual(dict(result.by_bet_type), {})
        self.assertIsNone(result.max_single_day_maximum_drawdown)

    def test_completed_no_bet_is_not_diagnostic(self) -> None:
        record = self._record(
            1,
            NARDailyReplayExecutionState.FULL_DAY_REPLAY_COMPLETED,
            completed_no_bet=True,
        )
        result = self._aggregate(record)
        self.assertEqual((result.completed_day_count, result.no_bet_race_count), (1, 1))
        self.assertEqual((result.roi, result.bet_hit_rate, result.race_hit_rate), (None, None, None))
        self.assertEqual(result.max_single_day_maximum_drawdown, 0)

    def test_descending_and_duplicate_target_dates_rejected_without_sorting(self) -> None:
        later, earlier = self._completed(2), self._completed(1)
        with self.assertRaisesRegex(RepositoryValidationError, "ascending"):
            self._aggregate(later, earlier)
        first = self._completed(1)
        second = replace(first, orchestration_audit_sha256=_audit("same-date-second"), run_id="same-date-second")
        with self.assertRaisesRegex(RepositoryValidationError, "duplicate target_date"):
            self._aggregate(first, second)

    def test_compatibility_mismatch_rejected_and_different_run_ids_allowed(self) -> None:
        first, second = self._completed(1), self._completed(2)
        accepted = self._aggregate(first, replace(second, run_id="different-run"))
        self.assertEqual(accepted.selected_record_count, 2)
        incompatible = replace(
            second,
            orchestration_audit_sha256=_audit("different-commit-audit"),
            target_commit_id="different-commit",
        )
        with self.assertRaisesRegex(RepositoryValidationError, "incompatible"):
            self._aggregate(first, incompatible)

    def test_compatibility_key_is_exact_frozen_predicate(self) -> None:
        record = self._completed(1)
        self.assertEqual(
            subject._compatibility(record),
            (
                record.schema_version,
                record.organization,
                record.source_system,
                record.dataset_id,
                record.selection_policy,
                record.settlement_information_cutoff,
                record.strategy_id,
                record.strategy_name,
                record.strategy_config_hash,
                record.target_commit_id,
                record.race_budget_total_amount,
            ),
        )

    def test_zero_denominator_rate_semantics(self) -> None:
        no_bet = self._record(
            1,
            NARDailyReplayExecutionState.FULL_DAY_REPLAY_COMPLETED,
            completed_no_bet=True,
        )
        result = self._aggregate(no_bet)
        self.assertIsNone(result.roi)
        self.assertIsNone(result.bet_hit_rate)
        self.assertIsNone(result.race_hit_rate)

    def test_drawdown_is_max_single_day_only(self) -> None:
        result = self._aggregate(self._completed(1), self._completed(2, second=True))
        self.assertEqual(result.max_single_day_maximum_drawdown, 40)
        self.assertNotEqual(result.max_single_day_maximum_drawdown, 65)
        self.assertNotIn("maximum_drawdown", {item.name for item in fields(result)})

    def test_selection_and_result_identities_are_deterministic(self) -> None:
        first, second = self._completed(1), self._completed(2, second=True)
        selection = self._save(first, second)
        one = subject.aggregate_nar_daily_replay_selection(selection=selection, repository=self.repository)
        two = subject.aggregate_nar_daily_replay_selection(selection=selection, repository=self.repository)
        self.assertEqual(one, two)
        self.assertEqual(one.selection_sha256, selection.selection_sha256)
        self.assertRegex(one.aggregate_content_sha256, r"^[0-9a-f]{64}$")
        other = self._record(3, NARDailyReplayExecutionState.NOT_RUN_PARTIAL_RESOLUTION)
        changed = self._aggregate(first, second, other)
        self.assertNotEqual(changed.selection_sha256, one.selection_sha256)
        self.assertNotEqual(changed.aggregate_content_sha256, one.aggregate_content_sha256)

    def test_database_insert_order_does_not_control_selection(self) -> None:
        first, second = self._completed(1), self._completed(2, second=True)
        self.repository.save_result(record=second)
        self.repository.save_result(record=first)
        selection = subject.NARDailyReplayAggregationSelection(
            1, (first.persisted_content_sha256, second.persisted_content_sha256)
        )
        result = subject.aggregate_nar_daily_replay_selection(
            selection=selection, repository=self.repository
        )
        self.assertEqual((result.first_target_date, result.last_target_date), (first.target_date, second.target_date))

    def test_read_only_exact_id_calls_and_transaction_state(self) -> None:
        first, second = self._completed(1), self._completed(2, second=True)
        selection = self._save(first, second)
        changes = self.connection.total_changes
        original = SQLiteNARDailyReplayResultRepository.load_result
        with patch.object(
            SQLiteNARDailyReplayResultRepository,
            "load_result",
            autospec=True,
            side_effect=original,
        ) as load:
            subject.aggregate_nar_daily_replay_selection(
                selection=selection, repository=self.repository
            )
        self.assertEqual(load.call_count, 2)
        self.assertEqual(
            [call.kwargs["persisted_content_sha256"] for call in load.call_args_list],
            list(selection.persisted_content_sha256s),
        )
        self.assertEqual(self.connection.total_changes, changes)
        self.assertFalse(self.connection.in_transaction)

    def test_static_boundary_has_no_sql_write_clock_replay_or_latest(self) -> None:
        source = inspect.getsource(subject)
        tree = ast.parse(source)
        imports = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        self.assertFalse(
            imports
            & {
                "sqlite3",
                "requests",
                "httpx",
                "urllib",
                "random",
                "uuid",
                "pickle",
            }
        )
        for forbidden in (
            "datetime.now",
            "datetime.utcnow",
            "time.time",
            "run_nar_daily_replay",
            "write_daily_historical_replay_manifest",
            "apply_migrations",
            "save_result(",
            "load_latest",
            "load_by_date",
            "INSERT ",
            "UPDATE ",
            "DELETE ",
        ):
            self.assertNotIn(forbidden, source)
        self.assertIn("repository.load_result", source)
        self.assertNotIn("sorted(records", source)


if __name__ == "__main__":
    unittest.main()
