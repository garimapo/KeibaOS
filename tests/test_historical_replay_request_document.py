from __future__ import annotations

import ast
import copy
import inspect
import json
import math
import tempfile
import unittest
from collections.abc import Mapping
from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timezone
from pathlib import Path
from types import MappingProxyType
from typing import get_type_hints

import scripts.simulation as simulation_package
import scripts.simulation.historical_replay_request_document as request_module
from scripts.prediction.allocation_policy import AllocationPolicyConfig
from scripts.prediction.bet_strategy import SelectionStyle, SortCondition, StrategyConfig
from scripts.simulation.historical_input_snapshots import (
    HistoricalInputSnapshotIdentity,
    HistoricalSourceIdentity,
)
from scripts.simulation.historical_replay_request_document import (
    HistoricalReplayRaceRequest,
    HistoricalReplayRequestDocument,
    HistoricalReplayRequestValidationError,
    load_historical_replay_request_document,
)
from scripts.simulation.models import SimulationRunContext, StrategyIdentity, build_strategy_identity
from scripts.simulation.stake_allocation import BetStakeBudget


class HistoricalReplayRequestDocumentTests(unittest.TestCase):
    def _valid_strategy(self) -> dict[str, object]:
        return {
            "strategy_name": "RuleBasedBetStrategy",
            "allowed_bet_types": ["単勝", "馬連", "ワイド", "3連複"],
            "max_bet_count": 4,
            "selection_style": "formation",
            "min_combination_score": 1.25,
            "max_candidates": 8,
            "sort_condition": "generator_rank",
            "allocation_policy": {
                "policy_name": "fixed_stake_per_recommendation",
                "policy_version": "1",
                "parameters": {"stake_amount": 100},
            },
        }

    def _race(
        self,
        *,
        organization: str,
        source_system: str,
        external_race_id: str,
        internal_race_id: int,
        captured_at: str,
        cutoff: str,
        result_capture_id: str,
        catalog: dict[str, str],
    ) -> dict[str, object]:
        return {
            "snapshot_identity": {
                "dataset_id": "dataset-1",
                "organization": organization,
                "source_system": source_system,
                "external_race_id": external_race_id,
                "captured_at": captured_at,
            },
            "internal_race_id": internal_race_id,
            "settlement_information_cutoff": cutoff,
            "result_capture_id": result_capture_id,
            "payout_capture_catalog_by_bet_type": catalog,
        }

    def _valid_manifest(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "database_path": "database/replay.db",
            "capture_archives": {
                "JRA/jra_official": "archives/jra.db",
                "NAR/nar_official": "archives/nar.db",
            },
            "run_context": {
                "run_id": "run-1",
                "dataset_id": "dataset-1",
                "started_at": "2026-08-29T10:00:00+09:00",
                "target_commit_id": "commit-1",
            },
            "strategy": self._valid_strategy(),
            "budgets_by_race_id": {
                "20": {"total_amount": 400},
                "10": {"total_amount": 300},
            },
            "races": [
                self._race(
                    organization="JRA",
                    source_system="jra_official",
                    external_race_id="jra-race-20",
                    internal_race_id=20,
                    captured_at="2026-08-28T15:00:00+09:00",
                    cutoff="2026-08-29T12:00:00+09:00",
                    result_capture_id="shared-jra-capture",
                    catalog={"単勝": "shared-jra-capture", "馬連": "shared-jra-capture"},
                ),
                self._race(
                    organization="NAR",
                    source_system="nar_official",
                    external_race_id="nar-race-10",
                    internal_race_id=10,
                    captured_at="2026-08-28T08:00:00Z",
                    cutoff="2026-08-29T03:00:00Z",
                    result_capture_id="nar-result",
                    catalog={"ワイド": "nar-payout", "3連複": "nar-payout"},
                ),
            ],
        }

    def _write(self, directory: Path, value: object, name: str = "replay.json") -> Path:
        path = directory / name
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        return path

    def _write_raw(self, directory: Path, value: bytes, name: str) -> Path:
        path = directory / name
        path.write_bytes(value)
        return path

    def _load(self, directory: Path, value: object | None = None) -> HistoricalReplayRequestDocument:
        manifest = self._valid_manifest() if value is None else value
        return load_historical_replay_request_document(request_path=self._write(directory, manifest))

    def _assert_invalid(self, directory: Path, value: object) -> None:
        with self.assertRaises(HistoricalReplayRequestValidationError):
            self._load(directory, value)

    def _expected_strategy_identity(self) -> StrategyIdentity:
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
        return build_strategy_identity("RuleBasedBetStrategy", config)

    def _identity(
        self,
        organization: str = "JRA",
        source_system: str = "jra_official",
        external_race_id: str = "race-1",
    ) -> HistoricalInputSnapshotIdentity:
        return HistoricalInputSnapshotIdentity(
            dataset_id="dataset-1",
            source_identity=HistoricalSourceIdentity(
                organization=organization,
                source_system=source_system,
                external_race_id=external_race_id,
                source_url=None,
            ),
            captured_at=datetime(2026, 8, 28, tzinfo=timezone.utc),
        )

    def _direct_race(self, **changes: object) -> HistoricalReplayRaceRequest:
        values: dict[str, object] = {
            "snapshot_identity": self._identity(),
            "internal_race_id": 1,
            "settlement_information_cutoff": datetime(2026, 8, 29, tzinfo=timezone.utc),
            "result_capture_id": "capture",
            "payout_capture_catalog_by_bet_type": {"単勝": "capture"},
        }
        values.update(changes)
        return HistoricalReplayRaceRequest(**values)

    def _direct_document(self, **changes: object) -> HistoricalReplayRequestDocument:
        race = self._direct_race()
        values: dict[str, object] = {
            "schema_version": 1,
            "source_path": Path("replay.json"),
            "database_path": Path("database.db"),
            "capture_archive_paths_by_provider": {"JRA/jra_official": Path("jra.db")},
            "run_context": SimulationRunContext(
                run_id="run-1",
                dataset_id="dataset-1",
                started_at=datetime(2026, 8, 29, tzinfo=timezone.utc),
                target_commit_id="commit-1",
            ),
            "strategy_identity": self._expected_strategy_identity(),
            "budgets_by_race_id": {1: BetStakeBudget(total_amount=100)},
            "races": (race,),
        }
        values.update(changes)
        return HistoricalReplayRequestDocument(**values)

    def test_public_surface_types_signature_and_field_order_are_exact(self) -> None:
        self.assertEqual(
            request_module.__all__,
            (
                "HistoricalReplayRequestValidationError",
                "HistoricalReplayRaceRequest",
                "HistoricalReplayRequestDocument",
                "load_historical_replay_request_document",
            ),
        )
        self.assertTrue(issubclass(HistoricalReplayRequestValidationError, ValueError))
        self.assertEqual(
            [field.name for field in fields(HistoricalReplayRaceRequest)],
            [
                "snapshot_identity",
                "internal_race_id",
                "settlement_information_cutoff",
                "result_capture_id",
                "payout_capture_catalog_by_bet_type",
            ],
        )
        self.assertEqual(
            get_type_hints(HistoricalReplayRaceRequest),
            {
                "snapshot_identity": HistoricalInputSnapshotIdentity,
                "internal_race_id": int,
                "settlement_information_cutoff": datetime,
                "result_capture_id": str,
                "payout_capture_catalog_by_bet_type": Mapping[str, str],
            },
        )
        self.assertEqual(
            [field.name for field in fields(HistoricalReplayRequestDocument)],
            [
                "schema_version",
                "source_path",
                "database_path",
                "capture_archive_paths_by_provider",
                "run_context",
                "strategy_identity",
                "budgets_by_race_id",
                "races",
            ],
        )
        self.assertEqual(
            get_type_hints(HistoricalReplayRequestDocument),
            {
                "schema_version": int,
                "source_path": Path,
                "database_path": Path,
                "capture_archive_paths_by_provider": Mapping[str, Path],
                "run_context": SimulationRunContext,
                "strategy_identity": StrategyIdentity,
                "budgets_by_race_id": Mapping[int, BetStakeBudget],
                "races": tuple[HistoricalReplayRaceRequest, ...],
            },
        )
        for domain_type in (HistoricalReplayRaceRequest, HistoricalReplayRequestDocument):
            self.assertTrue(domain_type.__dataclass_params__.frozen)
            self.assertIn("__slots__", domain_type.__dict__)
        signature = inspect.signature(load_historical_replay_request_document)
        self.assertEqual(list(signature.parameters), ["request_path"])
        self.assertEqual(signature.parameters["request_path"].kind, inspect.Parameter.KEYWORD_ONLY)
        self.assertEqual(
            get_type_hints(load_historical_replay_request_document),
            {"request_path": str | Path, "return": HistoricalReplayRequestDocument},
        )
        for name in request_module.__all__:
            self.assertFalse(hasattr(simulation_package, name))

    def test_valid_mixed_provider_manifest_constructs_exact_immutable_domain(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            request_path = self._write(directory, self._valid_manifest())
            document = load_historical_replay_request_document(request_path=request_path)

            self.assertIs(type(document), HistoricalReplayRequestDocument)
            self.assertEqual(document.schema_version, 1)
            self.assertEqual(document.source_path, request_path)
            self.assertEqual(document.database_path, directory / "database/replay.db")
            self.assertEqual(
                dict(document.capture_archive_paths_by_provider),
                {
                    "JRA/jra_official": directory / "archives/jra.db",
                    "NAR/nar_official": directory / "archives/nar.db",
                },
            )
            self.assertEqual(
                document.run_context,
                SimulationRunContext(
                    run_id="run-1",
                    dataset_id="dataset-1",
                    started_at=datetime.fromisoformat("2026-08-29T10:00:00+09:00"),
                    target_commit_id="commit-1",
                ),
            )
            self.assertEqual(document.strategy_identity, self._expected_strategy_identity())
            self.assertEqual(dict(document.budgets_by_race_id), {10: BetStakeBudget(300), 20: BetStakeBudget(400)})
            self.assertEqual([race.internal_race_id for race in document.races], [20, 10])
            self.assertEqual(document.races[0].snapshot_identity.captured_at, datetime(2026, 8, 28, 6, tzinfo=timezone.utc))
            self.assertEqual(document.races[0].settlement_information_cutoff.utcoffset().total_seconds(), 9 * 3600)
            self.assertIsInstance(document.capture_archive_paths_by_provider, MappingProxyType)
            self.assertIsInstance(document.budgets_by_race_id, MappingProxyType)
            self.assertIsInstance(document.races[0].payout_capture_catalog_by_bet_type, MappingProxyType)
            self.assertEqual(document.races[0].result_capture_id, document.races[0].payout_capture_catalog_by_bet_type["単勝"])
            self.assertEqual(
                document.races[0].payout_capture_catalog_by_bet_type["単勝"],
                document.races[0].payout_capture_catalog_by_bet_type["馬連"],
            )

    def test_pipeline_and_track_reference_date_are_not_manifest_concepts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for key, value in (("pipeline", {}), ("track_reference_date", "2026-01-01")):
                manifest = self._valid_manifest()
                manifest[key] = value
                with self.subTest(key=key):
                    self._assert_invalid(directory, manifest)
            document = self._load(directory)
            self.assertFalse(hasattr(document, "pipeline"))
            self.assertFalse(hasattr(document, "track_reference_date"))

    def test_root_scalar_and_collection_types_are_exact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for schema_version in (True, 0, 2, "1"):
                manifest = self._valid_manifest()
                manifest["schema_version"] = schema_version
                with self.subTest(schema_version=repr(schema_version)):
                    self._assert_invalid(directory, manifest)
            for field, value in (
                ("capture_archives", []),
                ("run_context", []),
                ("strategy", []),
                ("budgets_by_race_id", []),
                ("races", {}),
                ("races", []),
            ):
                manifest = self._valid_manifest()
                manifest[field] = value
                with self.subTest(field=field, value=repr(value)):
                    self._assert_invalid(directory, manifest)

    def test_every_schema_object_rejects_missing_and_extra_keys(self) -> None:
        paths_and_keys = (
            ((), "schema_version"),
            (("capture_archives",), "JRA/jra_official"),
            (("run_context",), "run_id"),
            (("strategy",), "strategy_name"),
            (("strategy", "allocation_policy"), "policy_name"),
            (("strategy", "allocation_policy", "parameters"), "stake_amount"),
            (("budgets_by_race_id", "20"), "total_amount"),
            (("races", 0), "result_capture_id"),
            (("races", 0, "snapshot_identity"), "external_race_id"),
        )
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for path, key in paths_and_keys:
                missing = self._valid_manifest()
                target: object = missing
                for part in path:
                    target = target[part]
                del target[key]
                with self.subTest(path=path, missing=key):
                    self._assert_invalid(directory, missing)

                extra = self._valid_manifest()
                target = extra
                for part in path:
                    target = target[part]
                target["unexpected"] = 1
                with self.subTest(path=path, extra=True):
                    self._assert_invalid(directory, extra)

    def test_json_safety_and_utf8_validation_are_owned(self) -> None:
        raw_cases = {
            "duplicate-root.json": b'{"schema_version":1,"schema_version":1}',
            "duplicate-nested.json": b'{"x":{"a":1,"a":2}}',
            "nan.json": b'{"x":NaN}',
            "infinity.json": b'{"x":Infinity}',
            "negative-infinity.json": b'{"x":-Infinity}',
            "overflow.json": b'{"x":1e400}',
            "malformed.json": b'{',
            "non-object.json": b'[]',
            "trailing.json": b'{} trailing',
            "invalid-utf8.json": b'\xff',
        }
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for name, raw in raw_cases.items():
                with self.subTest(name=name):
                    path = self._write_raw(directory, raw, name)
                    with self.assertRaises(HistoricalReplayRequestValidationError):
                        load_historical_replay_request_document(request_path=path)

    def test_filesystem_oserror_propagates_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            with self.assertRaises(FileNotFoundError):
                load_historical_replay_request_document(request_path=directory / "missing.json")
            with self.assertRaises(OSError) as context:
                load_historical_replay_request_document(request_path=directory)
            self.assertNotIsInstance(context.exception, HistoricalReplayRequestValidationError)

    def test_request_and_database_path_validation_and_anchoring(self) -> None:
        for value in (None, 1, True, b"x", "", "   ", "bad\x00path", Path("bad\x00path")):
            with self.subTest(request_path=repr(value)):
                with self.assertRaises(HistoricalReplayRequestValidationError):
                    load_historical_replay_request_document(request_path=value)

        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for value in (None, 1, True, "", "   ", "bad\x00path"):
                manifest = self._valid_manifest()
                manifest["database_path"] = value
                with self.subTest(database_path=repr(value)):
                    self._assert_invalid(directory, manifest)
            absolute = directory / "absolute.db"
            manifest = self._valid_manifest()
            manifest["database_path"] = str(absolute)
            self.assertEqual(self._load(directory, manifest).database_path, absolute)

    def test_capture_archive_paths_and_provider_coverage_are_exact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            jra_only = self._valid_manifest()
            jra_only["races"] = [jra_only["races"][0]]
            jra_only["budgets_by_race_id"] = {"20": {"total_amount": 400}}
            jra_only["capture_archives"] = {"JRA/jra_official": "missing-but-allowed.db"}
            self.assertEqual(len(self._load(directory, jra_only).races), 1)

            nar_only = self._valid_manifest()
            nar_only["races"] = [nar_only["races"][1]]
            nar_only["budgets_by_race_id"] = {"10": {"total_amount": 300}}
            nar_only["capture_archives"] = {"NAR/nar_official": "nar.db"}
            self.assertEqual(len(self._load(directory, nar_only).races), 1)

            unused = copy.deepcopy(jra_only)
            unused["capture_archives"]["NAR/nar_official"] = "same.db"
            unused["capture_archives"]["JRA/jra_official"] = "same.db"
            self.assertEqual(len(self._load(directory, unused).capture_archive_paths_by_provider), 2)

            absolute = directory / "absolute-archive.db"
            absolute_manifest = copy.deepcopy(jra_only)
            absolute_manifest["capture_archives"] = {"JRA/jra_official": str(absolute)}
            self.assertEqual(
                self._load(directory, absolute_manifest).capture_archive_paths_by_provider["JRA/jra_official"],
                absolute,
            )

            for change in (
                {},
                {"JRA/jra_official": "jra.db"},
                {"NAR/nar_official": "nar.db"},
                {"OTHER/provider": "other.db"},
                {"JRA/jra_official": ""},
                {"JRA/jra_official": "bad\x00path", "NAR/nar_official": "nar.db"},
            ):
                manifest = self._valid_manifest()
                manifest["capture_archives"] = change
                with self.subTest(archives=repr(change)):
                    self._assert_invalid(directory, manifest)

    def test_run_context_values_aware_times_and_dataset_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for field, value in (
                ("run_id", ""),
                ("dataset_id", "   "),
                ("target_commit_id", 1),
                ("started_at", "2026-08-29T00:00:00"),
                ("started_at", True),
            ):
                manifest = self._valid_manifest()
                manifest["run_context"][field] = value
                with self.subTest(field=field, value=repr(value)):
                    self._assert_invalid(directory, manifest)

            for value in ("2026-08-29T00:00:00Z", "2026-08-29T09:00:00+09:00"):
                manifest = self._valid_manifest()
                manifest["run_context"]["started_at"] = value
                self.assertIsNotNone(self._load(directory, manifest).run_context.started_at.utcoffset())

            mismatch = self._valid_manifest()
            mismatch["races"][1]["snapshot_identity"]["dataset_id"] = "other"
            self._assert_invalid(directory, mismatch)

    def test_strategy_contract_matches_public_formal_identity_builder(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.assertEqual(self._load(directory).strategy_identity, self._expected_strategy_identity())
            cases = (
                ("strategy_name", "Other"),
                ("allowed_bet_types", ["単勝", "単勝"]),
                ("allowed_bet_types", ["複勝"]),
                ("max_bet_count", True),
                ("max_bet_count", -1),
                ("max_candidates", True),
                ("max_candidates", -1),
                ("selection_style", "other"),
                ("min_combination_score", True),
                ("min_combination_score", 10**400),
                ("sort_condition", "other"),
            )
            for field, value in cases:
                manifest = self._valid_manifest()
                manifest["strategy"][field] = value
                with self.subTest(field=field, value=repr(value)):
                    self._assert_invalid(directory, manifest)

            allocation_cases = (
                ("policy_name", "other"),
                ("policy_version", 1),
                ("policy_version", "2"),
            )
            for field, value in allocation_cases:
                manifest = self._valid_manifest()
                manifest["strategy"]["allocation_policy"][field] = value
                with self.subTest(allocation=field, value=repr(value)):
                    self._assert_invalid(directory, manifest)
            for stake in (0, -100, 50, True, "100"):
                manifest = self._valid_manifest()
                manifest["strategy"]["allocation_policy"]["parameters"]["stake_amount"] = stake
                with self.subTest(stake=repr(stake)):
                    self._assert_invalid(directory, manifest)

    def test_non_finite_strategy_scores_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for value in (math.nan, math.inf, -math.inf):
                manifest = self._valid_manifest()
                manifest["strategy"]["min_combination_score"] = value
                with self.subTest(score=repr(value)):
                    self._assert_invalid(directory, manifest)

    def test_budget_key_value_and_exact_race_coverage_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for valid_key in ("1", "12"):
                manifest = self._valid_manifest()
                manifest["races"] = [manifest["races"][0]]
                manifest["races"][0]["internal_race_id"] = int(valid_key)
                manifest["budgets_by_race_id"] = {valid_key: {"total_amount": 0}}
                self.assertIn(int(valid_key), self._load(directory, manifest).budgets_by_race_id)
            for invalid_key in ("0", "01", "+1", "-1", " 1", "1 ", "１"):
                manifest = self._valid_manifest()
                manifest["budgets_by_race_id"] = {invalid_key: {"total_amount": 100}}
                with self.subTest(key=invalid_key):
                    self._assert_invalid(directory, manifest)
            for total in (True, -100, 50, "100"):
                manifest = self._valid_manifest()
                manifest["budgets_by_race_id"]["20"]["total_amount"] = total
                with self.subTest(total=repr(total)):
                    self._assert_invalid(directory, manifest)
            for budgets in (
                {"20": {"total_amount": 400}},
                {**self._valid_manifest()["budgets_by_race_id"], "30": {"total_amount": 100}},
            ):
                manifest = self._valid_manifest()
                manifest["budgets_by_race_id"] = budgets
                self._assert_invalid(directory, manifest)

    def test_race_identity_uniqueness_provider_pair_and_input_order_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            duplicate_snapshot = self._valid_manifest()
            duplicate_snapshot["races"][1]["snapshot_identity"] = copy.deepcopy(
                duplicate_snapshot["races"][0]["snapshot_identity"]
            )
            self._assert_invalid(directory, duplicate_snapshot)

            duplicate_race_id = self._valid_manifest()
            duplicate_race_id["races"][1]["internal_race_id"] = 20
            duplicate_race_id["budgets_by_race_id"] = {"20": {"total_amount": 400}}
            self._assert_invalid(directory, duplicate_race_id)

            for race_id in (True, 0, -1):
                manifest = self._valid_manifest()
                manifest["races"][0]["internal_race_id"] = race_id
                with self.subTest(race_id=repr(race_id)):
                    self._assert_invalid(directory, manifest)

            for organization, source_system in (
                ("jra", "jra_official"),
                ("JRA", "JRA_OFFICIAL"),
                ("JRA", "nar_official"),
                ("NAR", "jra_official"),
            ):
                manifest = self._valid_manifest()
                manifest["races"][0]["snapshot_identity"]["organization"] = organization
                manifest["races"][0]["snapshot_identity"]["source_system"] = source_system
                with self.subTest(provider=(organization, source_system)):
                    self._assert_invalid(directory, manifest)

            for field, value in (
                ("dataset_id", ""),
                ("organization", "   "),
                ("source_system", 1),
                ("external_race_id", ""),
            ):
                manifest = self._valid_manifest()
                manifest["races"][0]["snapshot_identity"][field] = value
                with self.subTest(identity_field=field, value=repr(value)):
                    self._assert_invalid(directory, manifest)

            for extra in ("source_url", "internal_race_id"):
                manifest = self._valid_manifest()
                manifest["races"][0]["snapshot_identity"][extra] = "forbidden"
                with self.subTest(extra=extra):
                    self._assert_invalid(directory, manifest)
            self.assertEqual([race.internal_race_id for race in self._load(directory).races], [20, 10])

    def test_captured_at_and_settlement_cutoff_require_aware_iso_values(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for field_path in (("snapshot_identity", "captured_at"), (None, "settlement_information_cutoff")):
                for value in ("2026-08-29T00:00:00", True, "not-a-date"):
                    manifest = self._valid_manifest()
                    target = manifest["races"][0]
                    if field_path[0] is not None:
                        target = target[field_path[0]]
                    target[field_path[1]] = value
                    with self.subTest(field=field_path, value=repr(value)):
                        self._assert_invalid(directory, manifest)
            for field_path in (("snapshot_identity", "captured_at"), (None, "settlement_information_cutoff")):
                manifest = self._valid_manifest()
                target = manifest["races"][0]
                if field_path[0] is not None:
                    target = target[field_path[0]]
                target[field_path[1]] = "2026-08-29T00:00:00Z"
                self.assertIsNotNone(self._load(directory, manifest).races[0].settlement_information_cutoff.utcoffset())

    def test_result_capture_and_payout_catalog_contract_including_value_reuse(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            manifest = self._valid_manifest()
            manifest["races"][0]["payout_capture_catalog_by_bet_type"] = {}
            self.assertEqual(dict(self._load(directory, manifest).races[0].payout_capture_catalog_by_bet_type), {})

            manifest = self._valid_manifest()
            shared = "same-capture"
            manifest["races"][0]["result_capture_id"] = shared
            manifest["races"][0]["payout_capture_catalog_by_bet_type"] = {
                bet_type: shared for bet_type in ("単勝", "馬連", "ワイド", "3連複")
            }
            race = self._load(directory, manifest).races[0]
            self.assertEqual({race.result_capture_id, *race.payout_capture_catalog_by_bet_type.values()}, {shared})

            for result_id in (None, 1, True, "", "   "):
                manifest = self._valid_manifest()
                manifest["races"][0]["result_capture_id"] = result_id
                with self.subTest(result_id=repr(result_id)):
                    self._assert_invalid(directory, manifest)
            for key, value in (("複勝", "capture"), ("単勝", None), ("単勝", ""), ("単勝", "   ")):
                manifest = self._valid_manifest()
                manifest["races"][0]["payout_capture_catalog_by_bet_type"] = {key: value}
                with self.subTest(catalog=(key, value)):
                    self._assert_invalid(directory, manifest)

            raw = json.dumps(self._valid_manifest(), ensure_ascii=False)
            raw = raw.replace('"単勝": "shared-jra-capture"', '"単勝":"one","単勝":"two"', 1)
            path = self._write_raw(directory, raw.encode("utf-8"), "duplicate-payout.json")
            with self.assertRaises(HistoricalReplayRequestValidationError):
                load_historical_replay_request_document(request_path=path)

    def test_direct_public_domains_validate_and_defensively_freeze(self) -> None:
        catalog = {"単勝": "capture"}
        race = self._direct_race(payout_capture_catalog_by_bet_type=catalog)
        catalog["単勝"] = "changed"
        self.assertEqual(race.payout_capture_catalog_by_bet_type["単勝"], "capture")
        with self.assertRaises(TypeError):
            race.payout_capture_catalog_by_bet_type["単勝"] = "changed"
        with self.assertRaises(FrozenInstanceError):
            race.internal_race_id = 2

        archives = {"JRA/jra_official": Path("jra.db")}
        budgets = {1: BetStakeBudget(total_amount=100)}
        document = self._direct_document(
            capture_archive_paths_by_provider=archives,
            budgets_by_race_id=budgets,
            races=(race,),
        )
        archives["JRA/jra_official"] = Path("changed.db")
        budgets[1] = BetStakeBudget(total_amount=200)
        self.assertEqual(document.capture_archive_paths_by_provider["JRA/jra_official"], Path("jra.db"))
        self.assertEqual(document.budgets_by_race_id[1], BetStakeBudget(total_amount=100))
        self.assertEqual(document.races, (race,))
        with self.assertRaises(TypeError):
            document.budgets_by_race_id[1] = BetStakeBudget(total_amount=200)
        with self.assertRaises(FrozenInstanceError):
            document.database_path = Path("changed.db")

    def test_direct_public_domains_use_owned_validation_error(self) -> None:
        race_cases = (
            {"snapshot_identity": object()},
            {"internal_race_id": True},
            {"internal_race_id": 0},
            {"settlement_information_cutoff": datetime(2026, 8, 29)},
            {"result_capture_id": "   "},
            {"payout_capture_catalog_by_bet_type": []},
            {"payout_capture_catalog_by_bet_type": {"複勝": "capture"}},
            {"payout_capture_catalog_by_bet_type": {"単勝": ""}},
        )
        for changes in race_cases:
            with self.subTest(race=changes):
                with self.assertRaises(HistoricalReplayRequestValidationError):
                    self._direct_race(**changes)

        document_cases = (
            {"schema_version": True},
            {"source_path": "request.json"},
            {"database_path": "database.db"},
            {"capture_archive_paths_by_provider": {}},
            {"capture_archive_paths_by_provider": {"OTHER": Path("x")}},
            {"run_context": object()},
            {"strategy_identity": object()},
            {"budgets_by_race_id": {True: BetStakeBudget(100)}},
            {"races": ()},
        )
        for changes in document_cases:
            with self.subTest(document=changes):
                with self.assertRaises(HistoricalReplayRequestValidationError):
                    self._direct_document(**changes)

    def test_static_source_has_only_request_file_read_side_effect(self) -> None:
        source = Path(request_module.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_roots = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imported_modules = {
            (node.module or "").split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        self.assertTrue({"sqlite3", "requests", "httpx"}.isdisjoint(imported_roots | imported_modules))
        self.assertNotIn("PredictionPipeline", source)
        self.assertNotIn("track_reference_date", source)
        self.assertNotIn("datetime.now", source)
        self.assertNotIn("datetime.utcnow", source)
        self.assertNotIn("load_snapshot", source)
        self.assertNotIn("load_capture", source)
        self.assertNotIn("execute_and_persist", source)
        self.assertNotIn("acquire_and_persist", source)
        self.assertNotIn("execute_final", source)


if __name__ == "__main__":
    unittest.main()
