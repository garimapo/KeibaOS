"""Schema-v1 daily manifest projection and publication contract tests."""

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import date, datetime, timedelta, timezone
import inspect
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import scripts.simulation.historical_daily_replay_manifest_projection as subject
from scripts.prediction.allocation_policy import AllocationPolicyConfig
from scripts.prediction.bet_strategy import SelectionStyle, SortCondition, StrategyConfig
from scripts.simulation.historical_daily_evidence_resolution import (
    DailyHistoricalReplayCaptureReference,
    DailyHistoricalReplayEvidenceDisposition,
    DailyHistoricalReplayEvidenceResolution,
    DailyHistoricalReplayTargetOutcome,
)
from scripts.simulation.historical_daily_targets import (
    DailyHistoricalReplayCompletenessEvidence,
    DailyHistoricalReplayProviderScope,
    DailyHistoricalReplayTarget,
    DailyHistoricalReplayTargetSet,
    HistoricalDailyProviderIdentity,
    ProviderNativeDispositionEvidenceReference,
)
from scripts.simulation.historical_input_snapshots import (
    HistoricalInputSnapshotIdentity,
    HistoricalSourceIdentity,
)
from scripts.simulation.historical_replay_request_document import (
    HistoricalReplayRequestDocument,
    load_historical_replay_request_document,
)
from scripts.simulation.models import SimulationRunContext, StrategyIdentity, build_strategy_identity
from scripts.simulation.stake_allocation import BetStakeBudget


_UTC = timezone.utc
_NAR = HistoricalDailyProviderIdentity("NAR", "nar_official")
_DATE = date(2025, 1, 1)
_START = datetime(2025, 1, 1, 4, 5, 6, 123456, tzinfo=_UTC)
_SETTLEMENT = datetime(2025, 1, 2, 3, 4, 5, 654321, tzinfo=_UTC)


def _strategy(*, name: str = "RuleBasedBetStrategy", allocation: AllocationPolicyConfig | None = None) -> StrategyIdentity:
    if allocation is None:
        allocation = AllocationPolicyConfig(
            policy_name="fixed_stake_per_recommendation",
            policy_version="1",
            parameters={"stake_amount": 100},
        )
    config = StrategyConfig(
        allowed_bet_types=frozenset({"単勝", "馬連", "ワイド", "3連複"}),
        max_bet_count=4,
        selection_style=SelectionStyle.FORMATION,
        min_combination_score=1.25,
        max_candidates=8,
        sort_condition=SortCondition.GENERATOR_RANK,
        allocation_policy=allocation,
    )
    return build_strategy_identity(name, config)


def _target(
    race_no: str,
    *,
    provider: HistoricalDailyProviderIdentity = _NAR,
) -> DailyHistoricalReplayTarget:
    external = f"nar:20250101:01:{race_no}"
    return DailyHistoricalReplayTarget(
        provider_identity=provider,
        external_race_id=external,
        scheduled_start_at=_START + timedelta(minutes=int(race_no)),
        provider_disposition_evidence=ProviderNativeDispositionEvidenceReference(
            evidence_kind_and_version="nar-race-list-target-row-v1",
            exact_capture_or_reference_identity=f"race-list-{race_no}",
            content_sha256="a" * 64,
            structural_locator=f"row-{race_no}",
            native_value_sha256="b" * 64,
        ),
    )


def _target_set(
    *targets: DailyHistoricalReplayTarget,
    provider: HistoricalDailyProviderIdentity = _NAR,
) -> DailyHistoricalReplayTargetSet:
    evidence = DailyHistoricalReplayCompletenessEvidence(
        provider_identity=provider,
        evidence_kind_and_version="nar-daily-complete-v1",
        exact_capture_or_reference_identity="complete-capture",
        canonical_source_or_request_identity="complete-request",
        content_sha256="c" * 64,
        observed_at=datetime(2026, 9, 1, tzinfo=_UTC),
        provider_available_at=None,
        coverage_identity="provider-day",
    )
    return DailyHistoricalReplayTargetSet(
        target_date=_DATE,
        provider_scope=DailyHistoricalReplayProviderScope((provider,)),
        target_races=targets,
        completeness_evidence=(evidence,),
    )


def _outcome(
    target: DailyHistoricalReplayTarget,
    race_id: int,
    *,
    executable: bool = True,
    capture_id: str | None = None,
) -> DailyHistoricalReplayTargetOutcome:
    if not executable:
        return DailyHistoricalReplayTargetOutcome(
            target=target,
            disposition=DailyHistoricalReplayEvidenceDisposition.UNSUPPORTED,
            reason_codes=("NATIVE_NON_RUN",),
            internal_race_id=None,
            snapshot_identity=None,
            snapshot_content_sha256=None,
            result_capture_reference=None,
            payout_capture_reference=None,
        )
    capture_id = capture_id or f"settlement-{race_id}"
    capture = DailyHistoricalReplayCaptureReference(
        capture_id=capture_id,
        canonical_source_url=f"https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceMarkTable?k_raceNo={race_id}",
        response_sha256=f"{race_id % 10}" * 64,
        observed_at=_SETTLEMENT - timedelta(hours=1),
    )
    snapshot = HistoricalInputSnapshotIdentity(
        dataset_id="dataset-1",
        source_identity=HistoricalSourceIdentity(
            organization=target.provider_identity.organization,
            source_system=target.provider_identity.source_system,
            external_race_id=target.external_race_id,
            source_url=None,
        ),
        captured_at=target.scheduled_start_at - timedelta(hours=1),
    )
    return DailyHistoricalReplayTargetOutcome(
        target=target,
        disposition=DailyHistoricalReplayEvidenceDisposition.EXECUTABLE,
        reason_codes=(),
        internal_race_id=race_id,
        snapshot_identity=snapshot,
        snapshot_content_sha256="d" * 64,
        result_capture_reference=capture,
        payout_capture_reference=capture,
    )


def _resolution(
    targets: tuple[DailyHistoricalReplayTarget, ...],
    outcomes: tuple[DailyHistoricalReplayTargetOutcome, ...],
    *,
    provider: HistoricalDailyProviderIdentity = _NAR,
) -> DailyHistoricalReplayEvidenceResolution:
    return DailyHistoricalReplayEvidenceResolution(
        target_set=_target_set(*targets, provider=provider),
        dataset_id="dataset-1",
        selection_policy="LATEST_CAUSAL_IN_DATASET",
        settlement_information_cutoff=_SETTLEMENT,
        outcomes=outcomes,
    )


def _run_context(*, dataset_id: str = "dataset-1") -> SimulationRunContext:
    return SimulationRunContext(
        run_id="daily-run-1",
        dataset_id=dataset_id,
        started_at=datetime(2026, 9, 7, 12, 34, 56, 111222, tzinfo=timezone(timedelta(hours=9))),
        target_commit_id="commit-1",
    )


def _paths(root: Path, name: str = "manifest.json") -> dict[str, object]:
    return {
        "database_path": root / "main.sqlite3",
        "nar_capture_archive_path": root / "nar-archive.sqlite3",
        "run_context": _run_context(),
        "strategy_identity": _strategy(),
        "race_budget": BetStakeBudget(total_amount=1000),
        "manifest_source_path": root / name,
    }


def _write(root: Path, resolution: DailyHistoricalReplayEvidenceResolution, name: str = "manifest.json"):
    values = _paths(root, name)
    return subject.write_daily_historical_replay_manifest(resolution=resolution, **values)


class HistoricalDailyReplayManifestProjectionTests(unittest.TestCase):
    def test_public_surface_signature_fields_and_immutability(self) -> None:
        self.assertEqual(subject.__all__, (
            "DailyHistoricalReplayManifestProjection",
            "write_daily_historical_replay_manifest",
        ))
        self.assertEqual(
            {name for name in vars(subject) if not name.startswith("_")},
            {"DailyHistoricalReplayManifestProjection", "write_daily_historical_replay_manifest"},
        )
        self.assertEqual(
            tuple(field.name for field in fields(subject.DailyHistoricalReplayManifestProjection)),
            ("resolution", "document"),
        )
        signature = inspect.signature(subject.write_daily_historical_replay_manifest)
        self.assertEqual(tuple(signature.parameters), (
            "resolution", "database_path", "nar_capture_archive_path", "run_context",
            "strategy_identity", "race_budget", "manifest_source_path",
        ))
        self.assertTrue(all(
            parameter.kind is inspect.Parameter.KEYWORD_ONLY
            for parameter in signature.parameters.values()
        ))

        target = _target("01")
        resolution = _resolution((target,), (_outcome(target, 1, executable=False),))
        projection = subject.DailyHistoricalReplayManifestProjection(resolution, None)
        with self.assertRaises(FrozenInstanceError):
            projection.document = object()
        self.assertFalse(hasattr(projection, "__dict__"))
        with self.assertRaises(ValueError):
            subject.DailyHistoricalReplayManifestProjection(resolution, object())

    def test_full_projection_round_trips_exact_schema_v1(self) -> None:
        first, second = _target("10"), _target("02")
        resolution = _resolution(
            (first, second),
            (_outcome(first, 10), _outcome(second, 2)),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inputs = _paths(root)
            projection = subject.write_daily_historical_replay_manifest(
                resolution=resolution,
                **inputs,
            )
            document = projection.document
            self.assertIs(projection.resolution, resolution)
            self.assertIsInstance(document, HistoricalReplayRequestDocument)
            self.assertEqual(document.schema_version, 1)
            self.assertEqual(document.source_path, inputs["manifest_source_path"])
            self.assertEqual(document.database_path, inputs["database_path"])
            self.assertEqual(
                dict(document.capture_archive_paths_by_provider),
                {"NAR/nar_official": inputs["nar_capture_archive_path"]},
            )
            self.assertEqual(document.run_context, inputs["run_context"])
            self.assertEqual(document.strategy_identity, inputs["strategy_identity"])
            self.assertEqual(
                [race.snapshot_identity.source_identity.external_race_id for race in document.races],
                [second.external_race_id, first.external_race_id],
            )
            self.assertEqual([race.internal_race_id for race in document.races], [2, 10])
            self.assertEqual(set(document.budgets_by_race_id), {2, 10})
            self.assertTrue(all(
                budget == inputs["race_budget"]
                for budget in document.budgets_by_race_id.values()
            ))
            self.assertEqual(
                load_historical_replay_request_document(
                    request_path=inputs["manifest_source_path"]
                ),
                document,
            )

    def test_result_payout_cutoff_and_catalog_are_exact(self) -> None:
        target = _target("03")
        outcome = _outcome(target, 3, capture_id="exact-selected-capture")
        resolution = _resolution((target,), (outcome,))
        with tempfile.TemporaryDirectory() as directory:
            document = _write(Path(directory), resolution).document
            race = document.races[0]
            self.assertEqual(race.snapshot_identity, outcome.snapshot_identity)
            self.assertEqual(race.internal_race_id, outcome.internal_race_id)
            self.assertEqual(race.settlement_information_cutoff, _SETTLEMENT)
            self.assertEqual(race.result_capture_id, "exact-selected-capture")
            self.assertEqual(
                dict(race.payout_capture_catalog_by_bet_type),
                {bet_type: "exact-selected-capture" for bet_type in {"単勝", "馬連", "ワイド", "3連複"}},
            )

    def test_partial_projection_preserves_denominator_and_is_not_full(self) -> None:
        executable, unsupported = _target("01"), _target("02")
        resolution = _resolution(
            (executable, unsupported),
            (_outcome(executable, 1), _outcome(unsupported, 2, executable=False)),
        )
        with tempfile.TemporaryDirectory() as directory:
            projection = _write(Path(directory), resolution)
            self.assertEqual(resolution.day_state.value, "PARTIALLY_RESOLVED")
            self.assertIs(projection.resolution, resolution)
            self.assertEqual(len(projection.resolution.outcomes), 2)
            self.assertEqual(len(projection.document.races), 1)
            self.assertEqual(projection.document.races[0].internal_race_id, 1)
            self.assertFalse(hasattr(projection, "full_day_success"))

    def test_zero_executable_creates_no_manifest_and_does_not_inspect_parent(self) -> None:
        target = _target("01")
        resolution = _resolution((target,), (_outcome(target, 1, executable=False),))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            absent_parent = root / "absent"
            inputs = _paths(absent_parent)
            with patch.object(Path, "is_dir", side_effect=AssertionError("filesystem inspection")):
                projection = subject.write_daily_historical_replay_manifest(
                    resolution=resolution,
                    **inputs,
                )
            self.assertIs(projection.resolution, resolution)
            self.assertIsNone(projection.document)
            self.assertFalse(absent_parent.exists())

    def test_deterministic_compact_utf8_one_lf_and_exact_paths(self) -> None:
        first, second = _target("10"), _target("02")
        resolution_a = _resolution(
            (first, second),
            (_outcome(first, 10), _outcome(second, 2)),
        )
        resolution_b = _resolution(
            (second, first),
            (_outcome(second, 2), _outcome(first, 10)),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first_inputs = _paths(root, "a.json")
            second_inputs = _paths(root, "b.json")
            subject.write_daily_historical_replay_manifest(resolution=resolution_a, **first_inputs)
            subject.write_daily_historical_replay_manifest(resolution=resolution_b, **second_inputs)
            first_bytes = first_inputs["manifest_source_path"].read_bytes()
            second_bytes = second_inputs["manifest_source_path"].read_bytes()
            self.assertEqual(first_bytes, second_bytes)
            self.assertTrue(first_bytes.endswith(b"\n"))
            self.assertFalse(first_bytes.endswith(b"\n\n"))
            self.assertEqual(first_bytes.count(b"\n"), 1)
            payload = json.loads(first_bytes.decode("utf-8"))
            canonical = (json.dumps(
                payload, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":")
            ) + "\n").encode("utf-8")
            self.assertEqual(first_bytes, canonical)
            self.assertEqual(payload["database_path"], str(first_inputs["database_path"]))
            self.assertEqual(
                payload["capture_archives"]["NAR/nar_official"],
                str(first_inputs["nar_capture_archive_path"]),
            )
            self.assertEqual(payload["run_context"]["started_at"], "2026-09-07T03:34:56.111222+00:00")
            self.assertEqual(
                payload["races"][0]["settlement_information_cutoff"],
                "2025-01-02T03:04:05.654321+00:00",
            )

    def test_strategy_identity_is_sole_authority_and_round_trips(self) -> None:
        target = _target("01")
        resolution = _resolution((target,), (_outcome(target, 1),))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inputs = _paths(root)
            signature = inspect.signature(subject.write_daily_historical_replay_manifest)
            self.assertNotIn("strategy_config", signature.parameters)
            projection = subject.write_daily_historical_replay_manifest(
                resolution=resolution,
                **inputs,
            )
            self.assertEqual(projection.document.strategy_identity, inputs["strategy_identity"])

            for index, strategy in enumerate((
                _strategy(name="OtherStrategy"),
                _strategy(allocation=AllocationPolicyConfig("other", "1", {"stake_amount": 100})),
            )):
                invalid = _paths(root, f"invalid-{index}.json")
                invalid["strategy_identity"] = strategy
                with self.subTest(strategy=strategy.strategy_name), self.assertRaises(ValueError):
                    subject.write_daily_historical_replay_manifest(
                        resolution=resolution,
                        **invalid,
                    )
                self.assertFalse(invalid["manifest_source_path"].exists())

            corrupted = _strategy()
            object.__setattr__(corrupted, "strategy_config_hash", "f" * 64)
            invalid = _paths(root, "corrupted.json")
            invalid["strategy_identity"] = corrupted
            with self.assertRaises(ValueError):
                subject.write_daily_historical_replay_manifest(resolution=resolution, **invalid)
            self.assertFalse(invalid["manifest_source_path"].exists())

    def test_relative_paths_are_rejected_without_cwd_resolution(self) -> None:
        target = _target("01")
        resolution = _resolution((target,), (_outcome(target, 1),))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for field in ("manifest_source_path", "database_path", "nar_capture_archive_path"):
                inputs = _paths(root, f"{field}.json")
                inputs[field] = Path("relative") / f"{field}.value"
                with self.subTest(field=field), self.assertRaises(ValueError):
                    subject.write_daily_historical_replay_manifest(
                        resolution=resolution,
                        **inputs,
                    )
            source = inspect.getsource(subject)
            self.assertNotIn(".resolve(", source)
            self.assertNotIn("getcwd", source)
            self.assertNotIn("Path.cwd", source)

    def test_existing_file_is_untouched_and_parent_is_not_created(self) -> None:
        target = _target("01")
        resolution = _resolution((target,), (_outcome(target, 1),))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            existing_inputs = _paths(root, "existing.json")
            original = b"pre-existing\r\nbytes\x00"
            existing_inputs["manifest_source_path"].write_bytes(original)
            with self.assertRaises(FileExistsError):
                subject.write_daily_historical_replay_manifest(
                    resolution=resolution,
                    **existing_inputs,
                )
            self.assertEqual(existing_inputs["manifest_source_path"].read_bytes(), original)

            missing_parent = root / "missing-parent"
            missing_inputs = _paths(missing_parent)
            with self.assertRaisesRegex(ValueError, "parent"):
                subject.write_daily_historical_replay_manifest(
                    resolution=resolution,
                    **missing_inputs,
                )
            self.assertFalse(missing_parent.exists())

    def test_expected_document_validation_precedes_file_creation(self) -> None:
        target = _target("01")
        resolution = _resolution((target,), (_outcome(target, 1),))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inputs = _paths(root)
            with patch.object(subject, "_RequestDocument", side_effect=ValueError("expected-invalid")):
                with self.assertRaisesRegex(ValueError, "expected-invalid"):
                    subject.write_daily_historical_replay_manifest(
                        resolution=resolution,
                        **inputs,
                    )
            self.assertFalse(inputs["manifest_source_path"].exists())

    def test_reload_failure_removes_only_newly_created_manifest(self) -> None:
        target = _target("01")
        resolution = _resolution((target,), (_outcome(target, 1),))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            adjacent = root / "adjacent.txt"
            adjacent.write_bytes(b"keep")
            inputs = _paths(root)
            with patch.object(subject, "_load_request_document", side_effect=RuntimeError("reload-failed")):
                with self.assertRaisesRegex(RuntimeError, "reload-failed"):
                    subject.write_daily_historical_replay_manifest(
                        resolution=resolution,
                        **inputs,
                    )
            self.assertFalse(inputs["manifest_source_path"].exists())
            self.assertEqual(adjacent.read_bytes(), b"keep")

    def test_replaced_non_owned_path_is_not_removed_on_reload_failure(self) -> None:
        target = _target("01")
        resolution = _resolution((target,), (_outcome(target, 1),))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inputs = _paths(root)
            replacement = root / "replacement.tmp"
            replacement.write_bytes(b"foreign replacement")

            def replace_then_fail(*, request_path: Path):
                os.replace(replacement, request_path)
                raise RuntimeError("reload-failed-after-replacement")

            with patch.object(subject, "_load_request_document", side_effect=replace_then_fail):
                with self.assertRaisesRegex(RuntimeError, "reload-failed-after-replacement") as raised:
                    subject.write_daily_historical_replay_manifest(
                        resolution=resolution,
                        **inputs,
                    )
            self.assertEqual(inputs["manifest_source_path"].read_bytes(), b"foreign replacement")
            self.assertTrue(any("foreign path was not removed" in note for note in raised.exception.__notes__))

    def test_cleanup_failure_keeps_original_exception_and_fails_closed(self) -> None:
        target = _target("01")
        resolution = _resolution((target,), (_outcome(target, 1),))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inputs = _paths(root)
            with patch.object(subject, "_load_request_document", side_effect=RuntimeError("original-reload")):
                with patch.object(Path, "unlink", side_effect=PermissionError("cleanup-blocked")):
                    with self.assertRaisesRegex(RuntimeError, "original-reload") as raised:
                        subject.write_daily_historical_replay_manifest(
                            resolution=resolution,
                            **inputs,
                        )
            self.assertTrue(inputs["manifest_source_path"].exists())
            self.assertTrue(any("cleanup failed" in note for note in raised.exception.__notes__))
            inputs["manifest_source_path"].unlink()

    def test_dataset_and_provider_mismatches_fail_before_publication(self) -> None:
        target = _target("01")
        resolution = _resolution((target,), (_outcome(target, 1),))
        jra = HistoricalDailyProviderIdentity("JRA", "jra_official")
        jra_target = _target("01", provider=jra)
        jra_resolution = _resolution(
            (jra_target,),
            (_outcome(jra_target, 1),),
            provider=jra,
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index, (candidate, context) in enumerate((
                (resolution, _run_context(dataset_id="other")),
                (jra_resolution, _run_context()),
            )):
                inputs = _paths(root, f"invalid-{index}.json")
                inputs["run_context"] = context
                with self.assertRaises(ValueError):
                    subject.write_daily_historical_replay_manifest(
                        resolution=candidate,
                        **inputs,
                    )
                self.assertFalse(inputs["manifest_source_path"].exists())

    def test_duplicate_ids_and_snapshot_contradiction_fail_before_publication(self) -> None:
        first, second = _target("01"), _target("02")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            duplicate_ids = _resolution(
                (first, second),
                (_outcome(first, 1), _outcome(second, 1)),
            )
            with self.assertRaisesRegex(ValueError, "internal race IDs"):
                subject.write_daily_historical_replay_manifest(
                    resolution=duplicate_ids,
                    **_paths(root, "duplicate-id.json"),
                )

            first_outcome, second_outcome = _outcome(first, 1), _outcome(second, 2)
            object.__setattr__(second_outcome, "snapshot_identity", first_outcome.snapshot_identity)
            contradictory = _resolution((first, second), (first_outcome, second_outcome))
            with self.assertRaisesRegex(ValueError, "snapshot identity"):
                subject.write_daily_historical_replay_manifest(
                    resolution=contradictory,
                    **_paths(root, "duplicate-snapshot.json"),
                )
            self.assertEqual(list(root.glob("*.json")), [])

    def test_missing_or_distinct_executable_references_fail_closed(self) -> None:
        target = _target("01")
        base = _outcome(target, 1)
        other = replace(
            base.result_capture_reference,
            capture_id="different-payout",
            response_sha256="e" * 64,
        )
        distinct = replace(base, payout_capture_reference=other)
        missing = _outcome(target, 1)
        object.__setattr__(missing, "result_capture_reference", None)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index, outcome in enumerate((distinct, missing)):
                resolution = _resolution((target,), (outcome,))
                with self.subTest(index=index), self.assertRaises(ValueError):
                    subject.write_daily_historical_replay_manifest(
                        resolution=resolution,
                        **_paths(root, f"invalid-{index}.json"),
                    )
                self.assertFalse((root / f"invalid-{index}.json").exists())

    def test_roundtrip_and_byte_mismatch_return_no_success_and_cleanup(self) -> None:
        target = _target("01")
        resolution = _resolution((target,), (_outcome(target, 1),))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inputs = _paths(root)

            def mutate_after_load(*, request_path: Path):
                loaded = load_historical_replay_request_document(request_path=request_path)
                request_path.write_bytes(request_path.read_bytes() + b" ")
                return loaded

            with patch.object(subject, "_load_request_document", side_effect=mutate_after_load):
                with self.assertRaisesRegex(ValueError, "bytes changed"):
                    subject.write_daily_historical_replay_manifest(
                        resolution=resolution,
                        **inputs,
                    )
            self.assertFalse(inputs["manifest_source_path"].exists())

    def test_reloaded_document_equality_failure_cleans_new_manifest(self) -> None:
        target = _target("01")
        resolution = _resolution((target,), (_outcome(target, 1),))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inputs = _paths(root)

            def return_mismatched_document(*, request_path: Path):
                loaded = load_historical_replay_request_document(request_path=request_path)
                return replace(loaded, database_path=root / "different.sqlite3")

            with patch.object(subject, "_load_request_document", side_effect=return_mismatched_document):
                with self.assertRaisesRegex(ValueError, "differs from expected"):
                    subject.write_daily_historical_replay_manifest(
                        resolution=resolution,
                        **inputs,
                    )
            self.assertFalse(inputs["manifest_source_path"].exists())

    def test_no_clock_network_sqlite_migration_runner_or_body_parser_dependency(self) -> None:
        source = inspect.getsource(subject)
        tree = ast.parse(source)
        imported_roots = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        self.assertTrue({"requests", "httpx", "urllib", "socket", "sqlite3"}.isdisjoint(imported_roots))
        for forbidden in (
            "datetime.now", "datetime.today", "utcnow", "time.time", "Path.resolve",
            "apply_migrations", "run_sqlite_historical_replay", "BeautifulSoup",
            "normalize", "target_race_count",
        ):
            self.assertNotIn(forbidden, source)

    def test_projection_value_rejects_state_document_contradictions(self) -> None:
        target = _target("01")
        full_resolution = _resolution((target,), (_outcome(target, 1),))
        none_resolution = _resolution((target,), (_outcome(target, 1, executable=False),))
        with self.assertRaises(ValueError):
            subject.DailyHistoricalReplayManifestProjection(full_resolution, None)
        with tempfile.TemporaryDirectory() as directory:
            document = _write(Path(directory), full_resolution).document
            with self.assertRaises(ValueError):
                subject.DailyHistoricalReplayManifestProjection(none_resolution, document)


if __name__ == "__main__":
    unittest.main()
