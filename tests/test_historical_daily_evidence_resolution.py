"""Provider-neutral resolution value and complete-denominator contracts."""

from dataclasses import FrozenInstanceError, fields, replace
from datetime import date, datetime, timedelta, timezone
import inspect
import unittest

from scripts.simulation import historical_daily_evidence_resolution as subject
from scripts.simulation.historical_daily_targets import (
    DailyHistoricalReplayTarget, DailyHistoricalReplayTargetSet, DailyHistoricalReplayProviderScope,
    HistoricalDailyProviderIdentity, DailyHistoricalReplayCompletenessEvidence,
    ProviderNativeDispositionEvidenceReference,
)
from scripts.simulation.historical_input_snapshots import HistoricalSourceIdentity, HistoricalInputSnapshotIdentity


_UTC = timezone.utc
_START = datetime(2025, 1, 1, 5, tzinfo=_UTC)
_SETTLEMENT = _START + timedelta(hours=5)
_PROVIDER = HistoricalDailyProviderIdentity("ORG", "source")


def _target(external="race-a", start=_START):
    return DailyHistoricalReplayTarget(_PROVIDER, external, start,
        ProviderNativeDispositionEvidenceReference("native-v1", "capture", "a" * 64, "row", "b" * 64))


def _targets(*targets):
    return DailyHistoricalReplayTargetSet(date(2025, 1, 1), DailyHistoricalReplayProviderScope((_PROVIDER,)), targets,
        (DailyHistoricalReplayCompletenessEvidence(_PROVIDER, "complete-v1", "capture", "request", "c" * 64,
            datetime(2026, 9, 1, tzinfo=_UTC), None, "day"),))


def _outcome(target, executable=True):
    reference = subject.DailyHistoricalReplayCaptureReference("provider-capture", "https://official.test/result", "d" * 64, _SETTLEMENT)
    return subject.DailyHistoricalReplayTargetOutcome(target,
        subject.DailyHistoricalReplayEvidenceDisposition.EXECUTABLE if executable else subject.DailyHistoricalReplayEvidenceDisposition.UNSUPPORTED,
        () if executable else ("NATIVE_NON_RUN",),
        1 if executable else None,
        HistoricalInputSnapshotIdentity("dataset", HistoricalSourceIdentity("ORG", "source", target.external_race_id, None), _START)
        if executable else None,
        "e" * 64 if executable else None, reference if executable else None, reference if executable else None)


def _resolution(targets, outcomes):
    return subject.DailyHistoricalReplayEvidenceResolution(targets, "dataset", "LATEST_CAUSAL_IN_DATASET", _SETTLEMENT, outcomes)


class ResolutionValuesTests(unittest.TestCase):
    def test_exact_public_surface_and_fields(self):
        self.assertEqual({name for name in vars(subject) if not name.startswith("_")}, {
            "DailyHistoricalReplayEvidenceDisposition", "DailyHistoricalReplayResolutionState",
            "DailyHistoricalReplayCaptureReference", "DailyHistoricalReplayTargetOutcome", "DailyHistoricalReplayEvidenceResolution"})
        self.assertEqual(tuple(field.name for field in fields(subject.DailyHistoricalReplayTargetOutcome)),
            ("target", "disposition", "reason_codes", "internal_race_id", "snapshot_identity", "snapshot_content_sha256",
             "result_capture_reference", "payout_capture_reference"))
        self.assertNotIn("day_state", inspect.signature(subject.DailyHistoricalReplayEvidenceResolution).parameters)

    def test_nonempty_all_executable_predicate_and_all_three_states(self):
        a, b = _target(), _target("race-b")
        targets = _targets(a, b)
        for flags, expected in (((True, True), "ALL_TARGETS_RESOLVED"), ((True, False), "PARTIALLY_RESOLVED"),
                                ((False, True), "PARTIALLY_RESOLVED"), ((False, False), "NO_EXECUTABLE_TARGETS")):
            with self.subTest(flags=flags):
                result = _resolution(targets, (_outcome(a, flags[0]), _outcome(b, flags[1])))
                self.assertEqual(result.day_state.value, expected)
                self.assertEqual(len(result.outcomes), 2)
                self.assertIs(result.target_set, targets)
        with self.assertRaises(ValueError):
            _resolution(_targets(), ())

    def test_immutable_canonical_order_original_target_and_digest(self):
        a, b = _target("race-2"), _target("race-10")
        targets = _targets(a, b)
        result = _resolution(targets, (_outcome(a), _outcome(b)))
        self.assertEqual([o.target.external_race_id for o in result.outcomes], ["race-10", "race-2"])
        self.assertEqual(result, _resolution(targets, tuple(reversed(result.outcomes))))
        self.assertIs(result.outcomes[0].target, b)
        self.assertEqual(result.target_set.content_sha256, targets.content_sha256)
        for value, name in ((result, "dataset_id"), (result.outcomes[0], "reason_codes"),
                            (result.outcomes[0].result_capture_reference, "capture_id")):
            with self.assertRaises(FrozenInstanceError):
                setattr(value, name, "changed")
            self.assertFalse(hasattr(value, "__dict__"))

    def test_missing_extra_duplicate_and_contradictory_outcomes_rejected(self):
        a, b = _target(), _target("race-b")
        targets = _targets(a, b)
        for outcomes in ((_outcome(a),), (_outcome(a), _outcome(a)),
                         (_outcome(a), _outcome(b), _outcome(_target("race-c"))),
                         (_outcome(replace(a, scheduled_start_at=_START + timedelta(minutes=1))), _outcome(b))):
            with self.subTest(outcomes=outcomes), self.assertRaises(ValueError):
                _resolution(targets, outcomes)

    def test_partial_references_and_lexical_reasons_are_retained(self):
        original = _outcome(_target())
        outcome = replace(original, disposition=subject.DailyHistoricalReplayEvidenceDisposition.MISSING_SETTLEMENT_EVIDENCE,
            reason_codes=("RESULT_CAPTURE_MISSING", "PAYOUT_CAPTURE_MISSING"), result_capture_reference=None, payout_capture_reference=None)
        self.assertEqual(outcome.reason_codes, ("PAYOUT_CAPTURE_MISSING", "RESULT_CAPTURE_MISSING"))
        self.assertIs(outcome.snapshot_identity, original.snapshot_identity)
        self.assertEqual(_resolution(_targets(original.target), (outcome,)).day_state.value, "NO_EXECUTABLE_TARGETS")

    def test_invalid_outcome_structure(self):
        base = _outcome(_target())
        cases = ({"internal_race_id": True}, {"internal_race_id": 0}, {"disposition": "EXECUTABLE"},
            {"reason_codes": ["x"]}, {"reason_codes": ("x", "x")}, {"reason_codes": (" x",)},
            {"snapshot_content_sha256": None}, {"snapshot_content_sha256": "A" * 64},
            {"snapshot_identity": None}, {"internal_race_id": None}, {"payout_capture_reference": None},
            {"target": replace(base.target, scheduled_start_at=None)},
            {"disposition": subject.DailyHistoricalReplayEvidenceDisposition.UNSUPPORTED},
            {"snapshot_identity": HistoricalInputSnapshotIdentity("dataset", HistoricalSourceIdentity("ORG", "source", "wrong", None), _START)})
        for changes in cases:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(base, **changes)

    def test_generic_capture_reference_validation_and_utc_equality(self):
        ref = _outcome(_target()).result_capture_reference
        self.assertEqual(ref, replace(ref, observed_at=_SETTLEMENT.astimezone(timezone(timedelta(hours=9)))))
        self.assertEqual(ref.observed_at.tzinfo, _UTC)
        for changes in ({"capture_id": ""}, {"response_sha256": "x"}, {"observed_at": _SETTLEMENT.replace(tzinfo=None)},
                        *({"canonical_source_url": url} for url in ("http://official.test", "https://u:p@official.test", "https://official.test/#x", "https://official.test:bad", "https://official.test/\n"))):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(ref, **changes)

    def test_day_context_dataset_cutoff_and_types(self):
        a = _target()
        base = _resolution(_targets(a), (_outcome(a),))
        for changes in ({"dataset_id": "other"}, {"dataset_id": " dataset"}, {"selection_policy": "LATEST"},
                        {"settlement_information_cutoff": _SETTLEMENT - timedelta(microseconds=1)},
                        {"settlement_information_cutoff": _SETTLEMENT.replace(tzinfo=None)},
                        {"outcomes": list(base.outcomes)}, {"target_set": object()}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(base, **changes)
        self.assertEqual(base, replace(base, settlement_information_cutoff=_SETTLEMENT.astimezone(timezone(timedelta(hours=9)))))


if __name__ == "__main__":
    unittest.main()
