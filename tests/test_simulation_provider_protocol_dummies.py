"""Structural contract checks using minimal in-memory provider dummies."""

import contextlib
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal
import inspect
import io
from typing import get_args, get_origin, get_type_hints
import unittest

from scripts.simulation.providers.interfaces import (
    OddsSnapshotProvider,
    PayoutProvider,
    ProviderBuildResult,
    RaceResultProvider,
)
from scripts.simulation.providers.models import (
    CompletenessResult,
    CompletenessStatus,
    ProviderContext,
    RaceEntryUniverse,
    RawOddsBatch,
    RawOddsEntry,
    RawPayoutPublication,
    RawPayoutRecord,
    RawRaceResult,
    RawRaceResultEntry,
)
from scripts.simulation.repositories.interfaces import (
    OddsSnapshotBatch,
    OddsSnapshotEntry,
    PayoutPublication,
    PayoutRecord,
    PayoutStatus,
    PersistedRaceResult,
    PersistedRaceResultEntry,
    RaceResultEntryStatus,
    RaceResultStatus,
)


NOW = datetime(2026, 1, 2, 12, 0, tzinfo=UTC)


def complete() -> CompletenessResult:
    return CompletenessResult(CompletenessStatus.COMPLETE, 1, 1)


class DummyRaceResultProvider:
    def build_race_result(
        self,
        raw: RawRaceResult,
        context: ProviderContext,
        universe: RaceEntryUniverse,
    ) -> ProviderBuildResult[PersistedRaceResult]:
        return ProviderBuildResult(
            PersistedRaceResult(
                race_id=context.race_id,
                result_status=RaceResultStatus.PARTIAL,
                finalized_at=None,
                observed_at=context.observed_at,
                source=context.source,
                entries=(
                    PersistedRaceResultEntry(
                        horse_no=1,
                        race_entry_id=1,
                        finish_position=1,
                        result_status=RaceResultEntryStatus.CONFIRMED,
                    ),
                ),
            ),
            complete(),
        )


class DummyOddsSnapshotProvider:
    def build_odds_batch(
        self,
        raw: RawOddsBatch,
        context: ProviderContext,
        universe: RaceEntryUniverse,
    ) -> ProviderBuildResult[OddsSnapshotBatch]:
        return ProviderBuildResult(
            OddsSnapshotBatch(
                race_id=context.race_id,
                bet_type="単勝",
                observed_at=context.observed_at,
                is_complete=True,
                source=context.source,
                entries=(OddsSnapshotEntry((1,), Decimal("1.2300")),),
            ),
            complete(),
        )


class DummyPayoutProvider:
    def build_payout_publication(
        self,
        raw: RawPayoutPublication,
        context: ProviderContext,
        universe: RaceEntryUniverse,
    ) -> ProviderBuildResult[PayoutPublication]:
        return ProviderBuildResult(
            PayoutPublication(
                race_id=context.race_id,
                bet_type="単勝",
                finalized_at=context.observed_at,
                observed_at=context.observed_at,
                is_complete=True,
                source=context.source,
                entries=(PayoutRecord((1,), 230, PayoutStatus.WINNING),),
            ),
            complete(),
        )


class ProviderProtocolDummiesTest(unittest.TestCase):
    """Exercise structural compatibility without runtime Protocol checks."""

    def setUp(self) -> None:
        self.context = ProviderContext(1, NOW, "fixture", None, NOW, NOW)
        self.universe = RaceEntryUniverse(1, {1, 2, 3}, set(), set(), {1: 1, 2: 2, 3: 3})
        self.raw_result = RawRaceResult(
            "partial", None, (RawRaceResultEntry(1, 1, "1", "confirmed"),)
        )
        self.raw_odds = RawOddsBatch("単勝", (RawOddsEntry((1,), None, "1.23"),), True)
        self.raw_payout = RawPayoutPublication(
            "単勝", NOW, (RawPayoutRecord((1,), None, "230", "winning"),), True, True, True
        )

    def _assert_signature_matches(self, dummy_type: type[object], protocol: type[object], method: str) -> None:
        self.assertEqual(
            list(inspect.signature(getattr(dummy_type, method)).parameters),
            list(inspect.signature(getattr(protocol, method)).parameters),
        )

    def _assert_hints_match(self, dummy_type: type[object], protocol: type[object], method: str) -> None:
        self.assertEqual(get_type_hints(getattr(dummy_type, method)), get_type_hints(getattr(protocol, method)))

    def test_race_dummy_has_expected_method(self) -> None:
        self.assertTrue(callable(DummyRaceResultProvider().build_race_result))

    def test_odds_dummy_has_expected_method(self) -> None:
        self.assertTrue(callable(DummyOddsSnapshotProvider().build_odds_batch))

    def test_payout_dummy_has_expected_method(self) -> None:
        self.assertTrue(callable(DummyPayoutProvider().build_payout_publication))

    def test_race_dummy_signature_matches_protocol(self) -> None:
        self._assert_signature_matches(DummyRaceResultProvider, RaceResultProvider, "build_race_result")

    def test_odds_dummy_signature_matches_protocol(self) -> None:
        self._assert_signature_matches(DummyOddsSnapshotProvider, OddsSnapshotProvider, "build_odds_batch")

    def test_payout_dummy_signature_matches_protocol(self) -> None:
        self._assert_signature_matches(DummyPayoutProvider, PayoutProvider, "build_payout_publication")

    def test_race_dummy_type_hints_match_protocol(self) -> None:
        self._assert_hints_match(DummyRaceResultProvider, RaceResultProvider, "build_race_result")

    def test_odds_dummy_type_hints_match_protocol(self) -> None:
        self._assert_hints_match(DummyOddsSnapshotProvider, OddsSnapshotProvider, "build_odds_batch")

    def test_payout_dummy_type_hints_match_protocol(self) -> None:
        self._assert_hints_match(DummyPayoutProvider, PayoutProvider, "build_payout_publication")

    def test_race_dummy_returns_provider_build_result(self) -> None:
        result = DummyRaceResultProvider().build_race_result(self.raw_result, self.context, self.universe)
        self.assertIsInstance(result, ProviderBuildResult)

    def test_odds_dummy_returns_provider_build_result(self) -> None:
        result = DummyOddsSnapshotProvider().build_odds_batch(self.raw_odds, self.context, self.universe)
        self.assertIsInstance(result, ProviderBuildResult)

    def test_payout_dummy_returns_provider_build_result(self) -> None:
        result = DummyPayoutProvider().build_payout_publication(self.raw_payout, self.context, self.universe)
        self.assertIsInstance(result, ProviderBuildResult)

    def test_race_dummy_returns_persisted_race_result(self) -> None:
        value = DummyRaceResultProvider().build_race_result(self.raw_result, self.context, self.universe).value
        self.assertIsInstance(value, PersistedRaceResult)
        self.assertIs(value.result_status, RaceResultStatus.PARTIAL)
        self.assertIsInstance(value.entries, tuple)
        self.assertIsNotNone(value.observed_at.tzinfo)

    def test_odds_dummy_returns_single_odds_batch(self) -> None:
        value = DummyOddsSnapshotProvider().build_odds_batch(self.raw_odds, self.context, self.universe).value
        self.assertIsInstance(value, OddsSnapshotBatch)
        self.assertEqual(value.entries, (OddsSnapshotEntry((1,), Decimal("1.2300")),))

    def test_payout_dummy_returns_single_publication(self) -> None:
        value = DummyPayoutProvider().build_payout_publication(self.raw_payout, self.context, self.universe).value
        self.assertIsInstance(value, PayoutPublication)
        self.assertEqual(value.entries, (PayoutRecord((1,), 230, PayoutStatus.WINNING),))
        self.assertEqual(value.finalized_at, NOW)

    def test_dummy_results_include_completeness(self) -> None:
        results = (
            DummyRaceResultProvider().build_race_result(self.raw_result, self.context, self.universe),
            DummyOddsSnapshotProvider().build_odds_batch(self.raw_odds, self.context, self.universe),
            DummyPayoutProvider().build_payout_publication(self.raw_payout, self.context, self.universe),
        )
        self.assertTrue(all(isinstance(result.completeness, CompletenessResult) for result in results))
        self.assertTrue(all(result.completeness.status is CompletenessStatus.COMPLETE for result in results))

    def test_dummy_providers_do_not_expose_persistence_members(self) -> None:
        forbidden = {
            "save", "persist", "insert", "update", "delete", "commit", "rollback", "connect",
            "close", "execute", "cursor", "repository", "connection", "database", "session",
        }
        for provider in (DummyRaceResultProvider(), DummyOddsSnapshotProvider(), DummyPayoutProvider()):
            self.assertFalse(forbidden.intersection(vars(provider)))
            self.assertFalse(forbidden.intersection(vars(type(provider))))

    def test_dummy_calls_do_not_mutate_inputs(self) -> None:
        before = (self.raw_result, self.raw_odds, self.raw_payout, self.context, self.universe)
        DummyRaceResultProvider().build_race_result(self.raw_result, self.context, self.universe)
        DummyOddsSnapshotProvider().build_odds_batch(self.raw_odds, self.context, self.universe)
        DummyPayoutProvider().build_payout_publication(self.raw_payout, self.context, self.universe)
        self.assertEqual((self.raw_result, self.raw_odds, self.raw_payout, self.context, self.universe), before)

    def test_dummy_calls_do_not_write_stdout_or_stderr(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            DummyRaceResultProvider().build_race_result(self.raw_result, self.context, self.universe)
            DummyOddsSnapshotProvider().build_odds_batch(self.raw_odds, self.context, self.universe)
            DummyPayoutProvider().build_payout_publication(self.raw_payout, self.context, self.universe)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")

    def test_provider_build_results_are_frozen(self) -> None:
        result = DummyRaceResultProvider().build_race_result(self.raw_result, self.context, self.universe)
        with self.assertRaises(FrozenInstanceError):
            result.value = None

    def test_dummy_return_annotations_use_repository_boundary_models(self) -> None:
        methods = (
            (DummyRaceResultProvider, "build_race_result", PersistedRaceResult),
            (DummyOddsSnapshotProvider, "build_odds_batch", OddsSnapshotBatch),
            (DummyPayoutProvider, "build_payout_publication", PayoutPublication),
        )
        for dummy_type, method, value_type in methods:
            annotation = get_type_hints(getattr(dummy_type, method))["return"]
            self.assertIs(get_origin(annotation), ProviderBuildResult)
            self.assertEqual(get_args(annotation), (value_type,))
