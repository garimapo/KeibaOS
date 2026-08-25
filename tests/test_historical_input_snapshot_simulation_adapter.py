from __future__ import annotations

import ast
from dataclasses import fields
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import inspect
from pathlib import Path
from typing import get_type_hints
import unittest

import scripts.simulation as simulation_package
import scripts.simulation.historical_input_snapshot_simulation_adapter as adapter_module
from scripts.simulation.historical_input_evidence import HistoricalInputEvidenceReference
from scripts.simulation.historical_input_snapshot_simulation_adapter import (
    HistoricalInputSnapshotSimulationAdapterError,
    build_simulation_race_input_from_historical_snapshot,
)
from scripts.simulation.historical_input_snapshots import (
    HistoricalExternalEntryIdentity,
    HistoricalExternalRaceIdentity,
    HistoricalInputProvenance,
    HistoricalInputSnapshot,
    HistoricalInputSnapshotIdentity,
    HistoricalPastRaceSnapshot,
    HistoricalRaceEntrySnapshot,
    HistoricalRaceSnapshot,
    HistoricalSourceIdentity,
)
from scripts.simulation.models import (
    ImmutableRacePredictionInput,
    InputSnapshotAudit,
    PastRaceSnapshot,
    SimulationRaceInput,
    TrackConditionsSnapshot,
)
from scripts.simulation.validation import SimulationValidationError


UTC = timezone.utc
CAPTURED = datetime(2026, 8, 5, 12, 0, tzinfo=UTC)
CUTOFF = CAPTURED + timedelta(minutes=30)
START = CUTOFF + timedelta(minutes=30)
TARGET_DATE = date(2026, 8, 5)


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("ascii")).hexdigest()


def _evidence(
    role: str,
    *,
    token: str,
    available_at: datetime | None,
    observed_at: datetime,
) -> HistoricalInputEvidenceReference:
    return HistoricalInputEvidenceReference(
        evidence_role=role,
        canonical_source_url=f"https://example.test/{token}",
        response_sha256=_sha(token),
        available_at=available_at,
        observed_at=observed_at,
    )


def _single_evidence(role: str, token: str) -> tuple[HistoricalInputEvidenceReference, ...]:
    return (
        _evidence(
            role,
            token=token,
            available_at=CAPTURED - timedelta(minutes=10),
            observed_at=CAPTURED - timedelta(minutes=5),
        ),
    )


def _entry(
    *,
    race_entry_id: int,
    horse_no: int,
    jockey: str,
    win_odds: Decimal,
    entry_order: int,
) -> HistoricalRaceEntrySnapshot:
    race_identity = HistoricalExternalRaceIdentity(
        organization="JRA",
        source_system="jra_official",
        external_race_id="jra:20260805:05:01:01",
    )
    return HistoricalRaceEntrySnapshot(
        race_entry_id=race_entry_id,
        external_entry_identity=HistoricalExternalEntryIdentity(
            external_race_identity=race_identity,
            external_entry_id=f"jra-entry-{race_entry_id}",
            external_horse_id=f"jra-horse-{race_entry_id}",
        ),
        horse_no=horse_no,
        jockey=jockey,
        win_odds=win_odds,
        entry_order=entry_order,
    )


def _past_race(
    *,
    race_entry_id: int,
    index: int,
    race_date_value: date,
    weight: Decimal,
    weight_diff: Decimal,
    odds: Decimal,
) -> HistoricalPastRaceSnapshot:
    return HistoricalPastRaceSnapshot(
        race_entry_id=race_entry_id,
        past_race_index=index,
        race_date=race_date_value,
        place=f"Past Place {index}",
        race_name=f"Past Race {index}",
        race_class=f"Class {index}",
        distance_m=1400 + index * 200,
        track="turf",
        weather="sunny",
        track_condition="good",
        finish=index + 1,
        race_time=f"1:3{index}.0",
        weight=weight,
        weight_diff=weight_diff,
        jockey=f"Past Jockey {index}",
        popularity=index,
        odds=odds,
        passing_order=f"{index + 1}-{index + 1}",
        fourth_corner_position=index + 1,
    )


def _provenance(
    *,
    entries: tuple[HistoricalRaceEntrySnapshot, ...],
    past_races: tuple[HistoricalPastRaceSnapshot, ...],
    multi_evidence: tuple[HistoricalInputEvidenceReference, ...] | None = None,
) -> tuple[HistoricalInputProvenance, ...]:
    result = [
        HistoricalInputProvenance(
            input_type="track",
            audit_key="track",
            source="jra_official",
            source_id="track-source",
            race_entry_id=None,
            evidence=_single_evidence("track", "track"),
        )
    ]
    for entry in entries:
        race_entry_id = entry.race_entry_id
        result.extend(
            (
                HistoricalInputProvenance(
                    "entry",
                    f"entry/{race_entry_id}",
                    "jra_official",
                    f"entry-source-{race_entry_id}",
                    race_entry_id,
                    _single_evidence("entry", f"entry-{race_entry_id}"),
                ),
                HistoricalInputProvenance(
                    "odds",
                    f"odds/{race_entry_id}",
                    "jra_official",
                    f"odds-source-{race_entry_id}",
                    race_entry_id,
                    _single_evidence("odds_win", f"odds-{race_entry_id}"),
                ),
                HistoricalInputProvenance(
                    "jockey",
                    f"jockey/{race_entry_id}",
                    "jra_official",
                    f"jockey-source-{race_entry_id}",
                    race_entry_id,
                    _single_evidence("jockey", f"jockey-{race_entry_id}"),
                ),
            )
        )
        history = sorted(
            (item for item in past_races if item.race_entry_id == race_entry_id),
            key=lambda item: item.past_race_index,
        )
        if not history:
            result.append(
                HistoricalInputProvenance(
                    "past_race",
                    f"past_race/{race_entry_id}/none",
                    "jra_official",
                    f"absence-source-{race_entry_id}",
                    race_entry_id,
                    _single_evidence(
                        "past_race_absence_query",
                        f"absence-{race_entry_id}",
                    ),
                )
            )
            continue
        for item in history:
            evidence = (
                multi_evidence
                if item.race_entry_id == 101 and item.past_race_index == 0 and multi_evidence is not None
                else (
                    _evidence(
                        "historical_race_context",
                        token=f"context-{race_entry_id}-{item.past_race_index}",
                        available_at=CAPTURED - timedelta(minutes=15),
                        observed_at=CAPTURED - timedelta(minutes=10),
                    ),
                    _evidence(
                        "historical_race_result",
                        token=f"result-{race_entry_id}-{item.past_race_index}",
                        available_at=CAPTURED - timedelta(minutes=8),
                        observed_at=CAPTURED - timedelta(minutes=3),
                    ),
                )
            )
            result.append(
                HistoricalInputProvenance(
                    "past_race",
                    f"past_race/{race_entry_id}/{item.past_race_index}",
                    "jra_official",
                    f"past-source-{race_entry_id}-{item.past_race_index}",
                    race_entry_id,
                    evidence,
                    item.past_race_index,
                )
            )
    return tuple(result)


def _snapshot(
    *,
    reverse_entries: bool = False,
    reverse_past_races: bool = False,
    reverse_provenance: bool = False,
    include_second_entry: bool = True,
    multi_evidence: tuple[HistoricalInputEvidenceReference, ...] | None = None,
) -> HistoricalInputSnapshot:
    first = _entry(
        race_entry_id=101,
        horse_no=9,
        jockey="Target Jockey A",
        win_odds=Decimal("2.5"),
        entry_order=0,
    )
    second = _entry(
        race_entry_id=202,
        horse_no=3,
        jockey="Target Jockey B",
        win_odds=Decimal("4.2"),
        entry_order=1,
    )
    entries = (first, second) if include_second_entry else (first,)
    past_races = (
        _past_race(
            race_entry_id=101,
            index=0,
            race_date_value=date(2026, 8, 1),
            weight=Decimal("480.5"),
            weight_diff=Decimal("2.3"),
            odds=Decimal("2.3"),
        ),
        _past_race(
            race_entry_id=101,
            index=1,
            race_date_value=date(2026, 7, 20),
            weight=Decimal("0"),
            weight_diff=Decimal("-1.5"),
            odds=Decimal("0"),
        ),
    )
    provenance = _provenance(
        entries=entries,
        past_races=past_races,
        multi_evidence=multi_evidence,
    )
    if reverse_entries:
        entries = tuple(reversed(entries))
    if reverse_past_races:
        past_races = tuple(reversed(past_races))
    if reverse_provenance:
        provenance = tuple(reversed(provenance))
    return HistoricalInputSnapshot(
        identity=HistoricalInputSnapshotIdentity(
            dataset_id="historical-dataset",
            source_identity=HistoricalSourceIdentity(
                organization="JRA",
                source_system="jra_official",
                external_race_id="jra:20260805:05:01:01",
                source_url="https://www.jra.go.jp/JRADB/accessD.html?example",
            ),
            captured_at=CAPTURED,
        ),
        internal_race_id=777,
        information_cutoff=CUTOFF,
        race=HistoricalRaceSnapshot(
            target_race_date=TARGET_DATE,
            scheduled_start_at=START,
            place="Tokyo",
            distance_m=1600,
            track="turf",
            track_condition="good",
            race_name="Target Race",
            race_class="Open",
            weather="sunny",
        ),
        entries=entries,
        past_races=past_races,
        provenance=provenance,
    )


class HistoricalInputSnapshotSimulationAdapterTest(unittest.TestCase):
    def test_exact_public_surface_signature_and_input_type(self) -> None:
        self.assertEqual(
            adapter_module.__all__,
            (
                "HistoricalInputSnapshotSimulationAdapterError",
                "build_simulation_race_input_from_historical_snapshot",
            ),
        )
        self.assertTrue(issubclass(HistoricalInputSnapshotSimulationAdapterError, ValueError))
        signature = inspect.signature(build_simulation_race_input_from_historical_snapshot)
        self.assertEqual(tuple(signature.parameters), ("snapshot",))
        self.assertIs(signature.parameters["snapshot"].kind, inspect.Parameter.KEYWORD_ONLY)
        hints = get_type_hints(build_simulation_race_input_from_historical_snapshot)
        self.assertIs(hints["snapshot"], HistoricalInputSnapshot)
        self.assertIs(hints["return"], SimulationRaceInput)
        with self.assertRaises(HistoricalInputSnapshotSimulationAdapterError):
            build_simulation_race_input_from_historical_snapshot(snapshot=object())
        self.assertFalse(hasattr(simulation_package, "build_simulation_race_input_from_historical_snapshot"))

    def test_complete_mapping_uses_internal_entry_identity_and_canonical_orders(self) -> None:
        snapshot = _snapshot(
            reverse_entries=True,
            reverse_past_races=True,
            reverse_provenance=True,
        )
        result = build_simulation_race_input_from_historical_snapshot(snapshot=snapshot)
        self.assertIs(type(result), SimulationRaceInput)
        self.assertIs(type(result.pipeline_input), ImmutableRacePredictionInput)
        pipeline = result.pipeline_input
        self.assertEqual(tuple(pipeline.horse_past_races), (101, 202))
        self.assertEqual(tuple(pipeline.jockey_names_by_horse), (101, 202))
        self.assertEqual(tuple(pipeline.odds_by_horse), (101, 202))
        self.assertNotIn(9, pipeline.horse_past_races)
        self.assertNotIn(3, pipeline.horse_past_races)
        self.assertEqual(
            tuple(item.horse_id for item in pipeline.horse_past_races[101]),
            (101, 101),
        )
        self.assertEqual(
            tuple(item.race_date for item in pipeline.horse_past_races[101]),
            ("2026-08-01", "2026-07-20"),
        )
        self.assertEqual(pipeline.horse_past_races[202], ())

    def test_one_entry_snapshot_maps_without_synthetic_entities(self) -> None:
        snapshot = _snapshot(include_second_entry=False)
        result = build_simulation_race_input_from_historical_snapshot(snapshot=snapshot)
        self.assertEqual(tuple(result.pipeline_input.horse_past_races), (101,))
        self.assertEqual(result.pipeline_input.race_horse_count, 1)
        self.assertEqual(
            tuple(item.audit_key for item in result.input_snapshot_audit.entries),
            (
                "entry/101", "odds/101", "jockey/101",
                "past_race/101/0", "past_race/101/1", "track",
            ),
        )

    def test_past_race_field_mapping_is_exact_and_marginless(self) -> None:
        result = build_simulation_race_input_from_historical_snapshot(snapshot=_snapshot())
        item = result.pipeline_input.horse_past_races[101][0]
        self.assertEqual(
            tuple(field.name for field in fields(PastRaceSnapshot)),
            (
                "horse_id", "race_date", "place", "race_name", "race_class",
                "distance", "track", "weather", "track_condition", "finish",
                "time", "weight", "weight_diff", "jockey", "popularity", "odds",
                "passing_order", "fourth_corner_position",
            ),
        )
        self.assertEqual(
            item,
            PastRaceSnapshot(
                horse_id=101,
                race_date="2026-08-01",
                place="Past Place 0",
                race_name="Past Race 0",
                race_class="Class 0",
                distance=1400,
                track="turf",
                weather="sunny",
                track_condition="good",
                finish=1,
                time="1:30.0",
                weight=float(Decimal("480.5")),
                weight_diff=float(Decimal("2.3")),
                jockey="Past Jockey 0",
                popularity=0,
                odds=float(Decimal("2.3")),
                passing_order="1-1",
                fourth_corner_position=1,
            ),
        )
        self.assertFalse(hasattr(item, "margin"))

    def test_track_jockey_odds_count_and_race_fields_are_exact(self) -> None:
        snapshot = _snapshot()
        result = build_simulation_race_input_from_historical_snapshot(snapshot=snapshot)
        pipeline = result.pipeline_input
        self.assertEqual(
            pipeline.track_conditions,
            TrackConditionsSnapshot("Tokyo", 1600, "turf", "good"),
        )
        self.assertEqual(dict(pipeline.jockey_names_by_horse), {101: "Target Jockey A", 202: "Target Jockey B"})
        self.assertEqual(dict(pipeline.odds_by_horse), {101: 2.5, 202: 4.2})
        self.assertEqual(pipeline.race_horse_count, 2)
        self.assertEqual(pipeline.race_id, snapshot.internal_race_id)
        self.assertEqual(pipeline.prediction_time, "2026-08-05T12:30:00.000000+00:00")
        self.assertEqual(result.race_id, snapshot.internal_race_id)
        self.assertEqual(result.target_race_date, snapshot.race.target_race_date)
        self.assertEqual(result.scheduled_start_at, snapshot.race.scheduled_start_at)
        self.assertEqual(result.information_cutoff, snapshot.information_cutoff)

    def test_normal_binary_float_approximation_and_zero_policies(self) -> None:
        result = build_simulation_race_input_from_historical_snapshot(snapshot=_snapshot())
        first, second = result.pipeline_input.horse_past_races[101]
        self.assertEqual(first.odds, float(Decimal("2.3")))
        self.assertEqual(first.weight_diff, float(Decimal("2.3")))
        self.assertEqual(second.odds, 0.0)
        self.assertEqual(second.weight, 0.0)
        self.assertEqual(second.weight_diff, -1.5)
        snapshot = _snapshot()
        object.__setattr__(snapshot.past_races[0], "weight_diff", Decimal("0"))
        zero = build_simulation_race_input_from_historical_snapshot(snapshot=snapshot)
        self.assertEqual(zero.pipeline_input.horse_past_races[101][0].weight_diff, 0.0)
        snapshot = _snapshot()
        object.__setattr__(snapshot.entries[0], "win_odds", Decimal("2.3"))
        nonexact = build_simulation_race_input_from_historical_snapshot(snapshot=snapshot)
        self.assertEqual(nonexact.pipeline_input.odds_by_horse[101], float(Decimal("2.3")))

    def test_decimal_overflow_and_positive_underflow_fail_closed(self) -> None:
        for value in (Decimal("1e999999"), Decimal("1e-999999")):
            with self.subTest(value=value):
                snapshot = _snapshot()
                object.__setattr__(snapshot.entries[0], "win_odds", value)
                with self.assertRaises(HistoricalInputSnapshotSimulationAdapterError):
                    build_simulation_race_input_from_historical_snapshot(snapshot=snapshot)

    def test_negative_underflow_and_wrong_decimal_type_fail_closed(self) -> None:
        snapshot = _snapshot()
        object.__setattr__(snapshot.past_races[0], "weight_diff", Decimal("-1e-999999"))
        with self.assertRaises(HistoricalInputSnapshotSimulationAdapterError):
            build_simulation_race_input_from_historical_snapshot(snapshot=snapshot)
        snapshot = _snapshot()
        object.__setattr__(snapshot.entries[0], "win_odds", 2.5)
        with self.assertRaises(HistoricalInputSnapshotSimulationAdapterError):
            build_simulation_race_input_from_historical_snapshot(snapshot=snapshot)

    def test_single_evidence_and_audit_header_are_exact(self) -> None:
        snapshot = _snapshot()
        result = build_simulation_race_input_from_historical_snapshot(snapshot=snapshot)
        audit = result.input_snapshot_audit
        self.assertIs(type(audit), InputSnapshotAudit)
        self.assertEqual(audit.dataset_id, snapshot.identity.dataset_id)
        self.assertEqual(audit.source, snapshot.identity.source_identity.source_system)
        self.assertEqual(audit.captured_at, snapshot.identity.captured_at)
        self.assertIs(audit.is_complete, True)
        track = audit.entries[-1]
        evidence = next(item for item in snapshot.provenance if item.audit_key == "track").evidence[0]
        self.assertEqual(track.available_at, evidence.available_at)
        self.assertEqual(track.observed_at, evidence.observed_at)

    def test_multi_evidence_reduces_to_maximum_known_timestamps(self) -> None:
        first = _evidence(
            "historical_race_context",
            token="multi-context",
            available_at=CAPTURED - timedelta(minutes=20),
            observed_at=CAPTURED - timedelta(minutes=10),
        )
        second = _evidence(
            "historical_race_result",
            token="multi-result",
            available_at=CAPTURED - timedelta(minutes=7),
            observed_at=CAPTURED - timedelta(minutes=2),
        )
        result = build_simulation_race_input_from_historical_snapshot(
            snapshot=_snapshot(multi_evidence=(second, first))
        )
        audit = next(item for item in result.input_snapshot_audit.entries if item.audit_key == "past_race/101/0")
        self.assertEqual(audit.available_at, second.available_at)
        self.assertEqual(audit.observed_at, second.observed_at)
        reordered = build_simulation_race_input_from_historical_snapshot(
            snapshot=_snapshot(multi_evidence=(first, second))
        )
        self.assertEqual(result, reordered)

    def test_any_unknown_availability_reduces_to_none(self) -> None:
        first = _evidence(
            "historical_race_context",
            token="unknown-context",
            available_at=None,
            observed_at=CAPTURED - timedelta(minutes=10),
        )
        second = _evidence(
            "historical_race_result",
            token="known-result",
            available_at=CAPTURED - timedelta(minutes=7),
            observed_at=CAPTURED - timedelta(minutes=2),
        )
        result = build_simulation_race_input_from_historical_snapshot(
            snapshot=_snapshot(multi_evidence=(first, second))
        )
        audit = next(item for item in result.input_snapshot_audit.entries if item.audit_key == "past_race/101/0")
        self.assertIsNone(audit.available_at)
        self.assertEqual(audit.observed_at, second.observed_at)

    def test_audit_metadata_and_canonical_order_are_exact(self) -> None:
        result = build_simulation_race_input_from_historical_snapshot(
            snapshot=_snapshot(reverse_provenance=True)
        )
        audit = result.input_snapshot_audit
        self.assertEqual(
            tuple(item.audit_key for item in audit.entries),
            (
                "entry/101", "odds/101", "jockey/101",
                "past_race/101/0", "past_race/101/1",
                "entry/202", "odds/202", "jockey/202", "past_race/202/none",
                "track",
            ),
        )
        for item in audit.entries:
            source = next(provenance for provenance in _snapshot().provenance if provenance.audit_key == item.audit_key)
            self.assertEqual(
                (item.input_type, item.audit_key, item.source, item.source_id, item.race_entry_id, item.past_race_index),
                (source.input_type, source.audit_key, source.source, source.source_id, source.race_entry_id, source.past_race_index),
            )

    def test_equivalent_reordered_snapshots_produce_equal_output(self) -> None:
        canonical = _snapshot()
        reordered = _snapshot(
            reverse_entries=True,
            reverse_past_races=True,
            reverse_provenance=True,
        )
        self.assertEqual(
            build_simulation_race_input_from_historical_snapshot(snapshot=canonical),
            build_simulation_race_input_from_historical_snapshot(snapshot=reordered),
        )

    def test_destination_validation_error_propagates_unchanged(self) -> None:
        snapshot = _snapshot()
        object.__setattr__(snapshot.past_races[0], "race_date", TARGET_DATE)
        with self.assertRaises(SimulationValidationError) as raised:
            build_simulation_race_input_from_historical_snapshot(snapshot=snapshot)
        self.assertIs(type(raised.exception), SimulationValidationError)

    def test_pure_static_boundary_and_no_broad_catch(self) -> None:
        source = inspect.getsource(adapter_module)
        tree = ast.parse(source)
        imported_modules = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        for forbidden in (
            "sqlite3", "requests", "httpx", "urllib", "pathlib", "subprocess",
            "random", "repository", "migration", "scripts.models",
        ):
            self.assertFalse(any(forbidden in name for name in imported_modules), forbidden)
        call_names = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertFalse(
            {
                "open", "now", "today", "time", "RacePredictionInput",
                "PredictionPipeline", "build_historical_prediction_pipeline",
                "validate_simulation_race_input",
            }
            & call_names
        )
        for handler in (node for node in ast.walk(tree) if isinstance(node, ast.ExceptHandler)):
            caught = handler.type
            names = (
                {caught.id}
                if isinstance(caught, ast.Name)
                else {
                    item.id
                    for item in caught.elts
                    if isinstance(item, ast.Name)
                }
                if isinstance(caught, ast.Tuple)
                else set()
            )
            self.assertFalse({"Exception", "BaseException"} & names)
        self.assertNotIn("historical_input_snapshot_simulation_adapter", Path("scripts/simulation/__init__.py").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
