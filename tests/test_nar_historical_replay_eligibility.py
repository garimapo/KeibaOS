"""Pure historical NAR entry-status eligibility contract."""

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import timedelta
from pathlib import Path
import unittest

import scripts.simulation.nar_historical_replay_eligibility as subject
from tests.test_historical_daily_replay_manifest_projection import _target, _target_set
from tests.test_nar_historical_replay_prediction_cutoff import _plan, POLICY
from scripts.simulation.nar_historical_replay_prediction_cutoff import (
    NARHistoricalReplayPredictionCutoffDecision, NARHistoricalReplayPredictionCutoffPlan,
)


def _authority(target, **changes):
    values = {
        "target": target,
        "authority_identity": "reviewed-status-authority-1",
        "canonical_source_identity": "nar-official-status-document-1",
        "response_sha256": "a" * 64,
        "availability_proof_identity": "independent-archive-capture-1",
        "timestamp_provenance": subject.NARHistoricalEntryStatusTimestampProvenance.INDEPENDENT_ARCHIVE_OBSERVATION,
        "available_at": target.scheduled_start_at - timedelta(minutes=1),
        "observed_at": target.scheduled_start_at - timedelta(minutes=1),
        "coverage_semantic": subject.NARHistoricalEntryStatusCoverage.COMPLETE_PRE_CUTOFF_ENTRY_STATUS_UNIVERSE,
        "entry_universe_identity": "complete-race-entry-universe-1",
        "covered_entry_universe_identity": "complete-race-entry-universe-1",
    }
    values.update(changes)
    return subject.NARHistoricalEntryStatusAuthority(**values)


class NARHistoricalReplayEligibilityTests(unittest.TestCase):
    def setUp(self):
        self.first, self.second = _target("01"), _target("02")
        self.targets = _target_set(self.first, self.second)

    def _resolve(self, *authorities):
        authority_set = subject.NARHistoricalEntryStatusAuthoritySet(self.targets, authorities)
        return subject.resolve_nar_historical_replay_eligibility(
            target_set=self.targets,
            historical_entry_status_authorities=authority_set,
            prediction_cutoff_plan=_plan(self.targets),
        )

    def test_public_surface_and_frozen_exact_values(self):
        self.assertEqual(tuple(subject.__all__), tuple(sorted(subject.__all__)))
        self.assertEqual(tuple(item.value for item in subject.NARHistoricalReplayEligibilityState), (
            "ELIGIBLE_WITH_PRE_CUTOFF_ENTRY_STATUS_AUTHORITY",
            "BLOCKED_ENTRY_STATUS_AUTHORITY_UNAVAILABLE",
        ))
        authority = _authority(self.first)
        with self.assertRaises(FrozenInstanceError):
            authority.authority_identity = "changed"
        self.assertEqual(tuple(field.name for field in fields(subject.NARHistoricalReplayEligibilityDecision)), (
            "target", "eligibility", "blocker_classification", "missing_authority", "causal_reason",
        ))
        self.assertFalse(hasattr(authority, "__dict__"))

    def test_valid_authorities_are_canonical_and_deterministic(self):
        first, second = _authority(self.first), _authority(self.second)
        forward = self._resolve(first, second)
        reversed_value = self._resolve(second, first)
        self.assertEqual(forward, reversed_value)
        self.assertIs(forward.target_set, self.targets)
        self.assertEqual(tuple(item.target for item in forward.decisions), self.targets.target_races)
        self.assertTrue(forward.all_eligible)
        self.assertTrue(all(item.blocker_classification is None for item in forward.decisions))

    def test_at_cutoff_is_eligible_and_after_cutoff_is_blocked(self):
        at_cutoff = _authority(
            self.first, available_at=self.first.scheduled_start_at - timedelta(minutes=1),
            observed_at=self.first.scheduled_start_at - timedelta(minutes=1),
        )
        after = _authority(
            self.second, available_at=self.second.scheduled_start_at + timedelta(microseconds=1),
            observed_at=self.second.scheduled_start_at + timedelta(microseconds=1),
        )
        result = self._resolve(at_cutoff, after)
        self.assertEqual(result.decisions[0].eligibility, subject.NARHistoricalReplayEligibilityState.ELIGIBLE_WITH_PRE_CUTOFF_ENTRY_STATUS_AUTHORITY)
        self.assertEqual(result.decisions[1].eligibility, subject.NARHistoricalReplayEligibilityState.BLOCKED_ENTRY_STATUS_AUTHORITY_UNAVAILABLE)
        self.assertEqual(result.decisions[1].causal_reason, "ENTRY_STATUS_AUTHORITY_AFTER_PREDICTION_CUTOFF")

    def test_capture_time_does_not_prove_later_prediction_cutoff(self):
        earlier = _authority(
            self.first,
            available_at=self.first.scheduled_start_at - timedelta(minutes=2),
            observed_at=self.first.scheduled_start_at - timedelta(minutes=2),
        )
        blocked = self._resolve(earlier, _authority(self.second))
        self.assertFalse(blocked.all_eligible)
        self.assertEqual(blocked.decisions[0].causal_reason,
                         "ENTRY_STATUS_AUTHORITY_NOT_VALID_THROUGH_PREDICTION_CUTOFF")
        reviewed = replace(
            earlier,
            temporal_coverage=subject.NARHistoricalEntryStatusTemporalCoverage.STATUS_VALID_THROUGH_PREDICTION_CUTOFF,
            valid_through_at=self.first.scheduled_start_at - timedelta(minutes=1),
            validity_proof_identity="reviewed-valid-through-cutoff-proof",
        )
        self.assertTrue(self._resolve(reviewed, _authority(self.second)).all_eligible)

    def test_missing_authority_and_missing_start_fail_closed(self):
        missing = self._resolve(_authority(self.first))
        self.assertFalse(missing.all_eligible)
        self.assertEqual(missing.decisions[1].causal_reason, "ENTRY_STATUS_AUTHORITY_MISSING")
        self.assertEqual(missing.decisions[1].blocker_classification, "HISTORICAL_REPLAY_BLOCKED_ENTRY_STATUS_AUTHORITY_UNAVAILABLE")
        no_start = replace(self.first, scheduled_start_at=None)
        with self.assertRaises(ValueError):
            NARHistoricalReplayPredictionCutoffPlan(
                _target_set(no_start), POLICY,
                (NARHistoricalReplayPredictionCutoffDecision(no_start, self.first.scheduled_start_at),),
            )

    def test_duplicate_foreign_and_forged_target_set_fail_closed(self):
        authority = _authority(self.first)
        with self.assertRaises(ValueError):
            subject.NARHistoricalEntryStatusAuthoritySet(self.targets, (authority, authority))
        with self.assertRaises(ValueError):
            subject.NARHistoricalEntryStatusAuthoritySet(self.targets, (_authority(_target("03")),))
        another_set = _target_set(self.first, self.second)
        with self.assertRaises(ValueError):
            subject.resolve_nar_historical_replay_eligibility(
                target_set=self.targets,
                historical_entry_status_authorities=subject.NARHistoricalEntryStatusAuthoritySet(another_set, ()),
                prediction_cutoff_plan=_plan(self.targets),
            )

    def test_malformed_and_incomplete_authority_cannot_become_eligible(self):
        invalid = (
            {"response_sha256": "A" * 64},
            {"timestamp_provenance": "CURRENT_PAGE_OBSERVATION"},
            {"coverage_semantic": "SINGLE_WITHDRAWAL_FACT"},
            {"covered_entry_universe_identity": "only-horse-14"},
            {"available_at": self.first.scheduled_start_at, "observed_at": self.first.scheduled_start_at - timedelta(seconds=1)},
        )
        for change in invalid:
            with self.subTest(change=change), self.assertRaises(ValueError):
                _authority(self.first, **change)
        with self.assertRaises(ValueError):
            subject.resolve_nar_historical_replay_eligibility(
                target_set=self.targets,
                historical_entry_status_authorities=object(),
                prediction_cutoff_plan=_plan(self.targets),
            )

    def test_no_io_or_current_status_dependencies(self):
        tree = ast.parse(Path(subject.__file__).read_text(encoding="utf-8"))
        imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        imports.extend(alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names)
        source = Path(subject.__file__).read_text(encoding="utf-8")
        for forbidden in (
            "sqlite3", "socket", "requests", "httpx", "urllib.request", "subprocess",
            "nar_race_entry_status_interpretation", "open(", "Path.cwd(",
        ):
            self.assertNotIn(forbidden, " ".join(imports) + source)


if __name__ == "__main__":
    unittest.main()
