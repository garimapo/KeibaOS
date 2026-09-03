import dataclasses
import inspect
import unittest
from datetime import date, datetime, timezone

from scripts.simulation import historical_daily_targets as subject


class HistoricalDailyTargetsTest(unittest.TestCase):
    def setUp(self):
        self.provider = subject.HistoricalDailyProviderIdentity("ORG", "source")
        self.scope = subject.DailyHistoricalReplayProviderScope((self.provider,))
        self.disposition = subject.ProviderNativeDispositionEvidenceReference(
            "kind-v1", "capture-1", "1" * 64, "row:1", "2" * 64
        )
        self.evidence = subject.DailyHistoricalReplayCompletenessEvidence(
            self.provider,
            "evidence-v1",
            "capture-1",
            "request-1",
            "3" * 64,
            datetime(2030, 1, 1, tzinfo=timezone.utc),
            None,
            "coverage-1",
        )
        self.a = subject.DailyHistoricalReplayTarget(
            self.provider,
            "race-a",
            datetime(2025, 1, 1, tzinfo=timezone.utc),
            self.disposition,
        )
        self.b = subject.DailyHistoricalReplayTarget(
            self.provider, "race-b", None, self.disposition
        )

    def bundle(self, targets=None):
        return subject.HistoricalDailyTargetEvidenceBundle(
            self.provider,
            date(2025, 1, 1),
            (self.b, self.a) if targets is None else targets,
            (self.evidence,),
        )

    def test_values_are_frozen_validated_and_canonical(self):
        bundle = self.bundle()
        self.assertEqual(["race-a", "race-b"], [item.external_race_id for item in bundle.target_races])
        with self.assertRaises(dataclasses.FrozenInstanceError):
            bundle.target_date = date(2025, 1, 2)
        with self.assertRaises(subject.DailyHistoricalTargetValidationError):
            subject.HistoricalDailyProviderIdentity(" ORG", "source")
        with self.assertRaises(subject.DailyHistoricalTargetValidationError):
            subject.DailyHistoricalReplayCompletenessEvidence(
                self.provider, "e", "c", "r", "A" * 64,
                datetime.now(timezone.utc), None, "coverage"
            )

    def test_closed_scope_and_duplicate_boundaries_fail_closed(self):
        other = subject.HistoricalDailyProviderIdentity("OTHER", "source")
        with self.assertRaises(subject.TargetDiscoveryIncompleteError) as caught:
            subject.build_daily_historical_replay_target_set(
                target_date=date(2025, 1, 1),
                provider_scope=subject.DailyHistoricalReplayProviderScope((self.provider, other)),
                evidence_bundles=(self.bundle(),),
            )
        self.assertEqual(subject.DailyTargetDiscoveryFailureCode.MISSING_ENVELOPE_EVIDENCE, caught.exception.code)
        with self.assertRaises(subject.DailyHistoricalTargetValidationError):
            self.bundle((self.a, self.a))

    def test_digest_known_vector_is_order_independent_and_nullable_time_is_retained(self):
        first = subject.build_daily_historical_replay_target_set(
            target_date=date(2025, 1, 1), provider_scope=self.scope,
            evidence_bundles=(self.bundle(),),
        )
        second = subject.build_daily_historical_replay_target_set(
            target_date=date(2025, 1, 1), provider_scope=self.scope,
            evidence_bundles=(self.bundle((self.a, self.b)),),
        )
        self.assertEqual("f0aa6e38920f2b5e6aa71026d4b154e1ddb260ac6152207dce1e7a1d59fcbb5d", first.content_sha256)
        self.assertEqual(first, second)
        self.assertIsNone(first.target_races[1].scheduled_start_at)
        self.assertEqual("capture-1", first.target_races[1].provider_disposition_evidence.exact_capture_or_reference_identity)

    def test_bundle_date_contradiction_and_out_of_scope_content_are_rejected(self):
        wrong_date = subject.HistoricalDailyTargetEvidenceBundle(
            self.provider, date(2025, 1, 2), (self.a,), (self.evidence,)
        )
        with self.assertRaises(subject.TargetDiscoveryIncompleteError) as caught:
            subject.build_daily_historical_replay_target_set(
                target_date=date(2025, 1, 1), provider_scope=self.scope,
                evidence_bundles=(wrong_date,),
            )
        self.assertEqual(subject.DailyTargetDiscoveryFailureCode.CONTRADICTORY_EVIDENCE, caught.exception.code)

    def test_shared_module_is_provider_neutral(self):
        source = inspect.getsource(subject).lower()
        for forbidden in ("nar", "jra", "requests", "sqlite", "url"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
