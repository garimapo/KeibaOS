from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import inspect
from typing import get_type_hints
import unittest

import scripts.simulation as simulation_package
from scripts.simulation.historical_input_snapshots import (
    HistoricalExternalEntryIdentity,
    HistoricalExternalRaceIdentity,
    HistoricalInputProvenance,
    HistoricalInputSnapshot,
    HistoricalInputSnapshotIdentity,
    HistoricalInputSnapshotRepository,
    HistoricalInputSnapshotSource,
    HistoricalPastRaceSnapshot,
    HistoricalRaceEntrySnapshot,
    HistoricalRaceSnapshot,
    HistoricalSourceIdentity,
    build_historical_input_snapshot_content_payload,
    compute_historical_input_snapshot_content_sha256,
)
from scripts.simulation.models import InputAuditEntry


UTC = timezone.utc
CAPTURED = datetime(2026, 8, 5, 12, 0, tzinfo=UTC)
CUTOFF = CAPTURED + timedelta(minutes=30)
START = CUTOFF + timedelta(minutes=30)


def _source(*, source_url: str | None = "https://example.test/race") -> HistoricalSourceIdentity:
    return HistoricalSourceIdentity("NAR", "nar_official", "nar:20260805:1:1", source_url)


def _entry(
    *,
    race_entry_id: int = 10,
    horse_no: int = 1,
    entry_order: int = 0,
    external_horse_id: str | None = "horse-1",
) -> HistoricalRaceEntrySnapshot:
    source = _source()
    return HistoricalRaceEntrySnapshot(
        race_entry_id=race_entry_id,
        external_entry_identity=HistoricalExternalEntryIdentity(
            HistoricalExternalRaceIdentity(
                source.organization,
                source.source_system,
                source.external_race_id,
            ),
            f"entry-{race_entry_id}",
            external_horse_id,
        ),
        horse_no=horse_no,
        jockey="Jockey",
        win_odds=Decimal("2.00"),
        entry_order=entry_order,
    )


def _past(*, race_entry_id: int = 10, index: int = 0, passing_order: str = "1-1-1-1") -> HistoricalPastRaceSnapshot:
    return HistoricalPastRaceSnapshot(
        race_entry_id=race_entry_id,
        past_race_index=index,
        race_date=date(2026, 8, 4),
        place="Tokyo",
        race_name="Prior Race",
        race_class="Open",
        distance_m=1600,
        track="turf",
        weather="sunny",
        track_condition="good",
        finish=1,
        margin=Decimal("0.00"),
        race_time="1:32.0",
        weight=Decimal("480.0"),
        weight_diff=Decimal("0.0"),
        jockey="Jockey",
        popularity=0,
        odds=Decimal("2.0"),
        passing_order=passing_order,
        fourth_corner_position=0,
    )


def _provenance(*, entry_id: int = 10, past: bool = True) -> tuple[HistoricalInputProvenance, ...]:
    observed = CAPTURED - timedelta(minutes=1)
    result = [
        HistoricalInputProvenance("track", "track", "nar_official", "track-1", None, observed_at=observed),
        HistoricalInputProvenance("entry", f"entry/{entry_id}", "nar_official", "entry-1", entry_id, observed_at=observed),
        HistoricalInputProvenance("odds", f"odds/{entry_id}", "nar_official", "odds-1", entry_id, observed_at=observed),
        HistoricalInputProvenance("jockey", f"jockey/{entry_id}", "nar_official", "jockey-1", entry_id, observed_at=observed),
    ]
    if past:
        result.append(HistoricalInputProvenance("past_race", f"past_race/{entry_id}/0", "nar_official", "past-1", entry_id, observed_at=observed, past_race_index=0))
    else:
        result.append(HistoricalInputProvenance("past_race", f"past_race/{entry_id}/none", "nar_official", "absence-1", entry_id, observed_at=observed))
    return tuple(result)


def _snapshot(
    *,
    source_url: str | None = "https://example.test/race",
    external_horse_id: str | None = "horse-1",
    information_cutoff: datetime = CUTOFF,
    passing_order: str = "1-1-1-1",
    with_past: bool = True,
) -> HistoricalInputSnapshot:
    source = _source(source_url=source_url)
    return HistoricalInputSnapshot(
        identity=HistoricalInputSnapshotIdentity("dataset-1", source, CAPTURED),
        internal_race_id=100,
        information_cutoff=information_cutoff,
        race=HistoricalRaceSnapshot(date(2026, 8, 5), START, "Tokyo", 1600, "turf", "good"),
        entries=(_entry(external_horse_id=external_horse_id),),
        past_races=(_past(passing_order=passing_order),) if with_past else (),
        provenance=_provenance(past=with_past),
    )


def _protocol_method_node(protocol: type[object], method_name: str) -> ast.FunctionDef:
    module = inspect.getmodule(protocol)
    if module is None:
        raise AssertionError("protocol module is unavailable")
    tree = ast.parse(inspect.getsource(module))
    protocol_node = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == protocol.__name__
    )
    return next(
        node
        for node in protocol_node.body
        if isinstance(node, ast.FunctionDef) and node.name == method_name
    )


class HistoricalInputSnapshotsTest(unittest.TestCase):
    def test_public_surface_and_dataclass_contracts(self) -> None:
        import scripts.simulation.historical_input_snapshots as module

        dataclasses = (
            HistoricalSourceIdentity,
            HistoricalExternalRaceIdentity,
            HistoricalExternalEntryIdentity,
            HistoricalInputSnapshotIdentity,
            HistoricalRaceSnapshot,
            HistoricalRaceEntrySnapshot,
            HistoricalPastRaceSnapshot,
            HistoricalInputProvenance,
            HistoricalInputSnapshot,
        )
        expected_fields = {
            HistoricalSourceIdentity: ("organization", "source_system", "external_race_id", "source_url"),
            HistoricalExternalRaceIdentity: ("organization", "source_system", "external_race_id"),
            HistoricalExternalEntryIdentity: ("external_race_identity", "external_entry_id", "external_horse_id"),
            HistoricalInputSnapshotIdentity: ("dataset_id", "source_identity", "captured_at"),
            HistoricalRaceSnapshot: ("target_race_date", "scheduled_start_at", "place", "distance_m", "track", "track_condition", "race_name", "race_class", "weather"),
            HistoricalRaceEntrySnapshot: ("race_entry_id", "external_entry_identity", "horse_no", "jockey", "win_odds", "entry_order"),
            HistoricalPastRaceSnapshot: ("race_entry_id", "past_race_index", "race_date", "place", "race_name", "race_class", "distance_m", "track", "weather", "track_condition", "finish", "margin", "race_time", "weight", "weight_diff", "jockey", "popularity", "odds", "passing_order", "fourth_corner_position"),
            HistoricalInputProvenance: ("input_type", "audit_key", "source", "source_id", "race_entry_id", "available_at", "observed_at", "past_race_index"),
            HistoricalInputSnapshot: ("identity", "internal_race_id", "information_cutoff", "race", "entries", "past_races", "provenance", "content_sha256"),
        }
        for value in dataclasses:
            self.assertTrue(hasattr(value, "__slots__"))
            self.assertEqual(tuple(item.name for item in fields(value)), expected_fields[value])
        self.assertFalse(fields(HistoricalSourceIdentity)[3].compare)
        self.assertFalse(fields(HistoricalSourceIdentity)[3].hash)
        self.assertFalse(fields(HistoricalExternalEntryIdentity)[2].compare)
        self.assertFalse(fields(HistoricalExternalEntryIdentity)[2].hash)
        digest = fields(HistoricalInputSnapshot)[-1]
        self.assertFalse(digest.init); self.assertFalse(digest.compare); self.assertFalse(digest.hash)
        provenance_fields = {item.name: item for item in fields(HistoricalInputProvenance)}
        self.assertIsNone(provenance_fields["available_at"].default)
        self.assertIsNone(provenance_fields["observed_at"].default)
        self.assertIsNone(provenance_fields["past_race_index"].default)
        self.assertIsNone(HistoricalSourceIdentity("NAR", "system", "race").source_url)
        self.assertIsNone(
            HistoricalExternalEntryIdentity(
                HistoricalExternalRaceIdentity("NAR", "system", "race"),
                "entry",
            ).external_horse_id
        )
        default_race = HistoricalRaceSnapshot(date(2026, 8, 5), START, "Tokyo", 1600, "turf", "good")
        self.assertIsNone(default_race.race_name)
        self.assertIsNone(default_race.race_class)
        self.assertIsNone(default_race.weather)
        default_provenance = HistoricalInputProvenance("track", "track", "source", "id", None, observed_at=CAPTURED)
        self.assertIsNone(default_provenance.available_at)
        self.assertEqual(default_provenance.observed_at, CAPTURED)
        self.assertIsNone(default_provenance.past_race_index)
        public_classes = {name for name, value in inspect.getmembers(module, inspect.isclass) if not name.startswith("_")}
        public_functions = {name for name, value in inspect.getmembers(module, inspect.isfunction) if not name.startswith("_")}
        self.assertEqual(public_classes, {value.__name__ for value in dataclasses} | {"HistoricalInputSnapshotSource", "HistoricalInputSnapshotRepository"})
        self.assertEqual(public_functions, {"build_historical_input_snapshot_content_payload", "compute_historical_input_snapshot_content_sha256"})
        for name in (
            "HistoricalSourceIdentity",
            "HistoricalExternalRaceIdentity",
            "HistoricalExternalEntryIdentity",
            "HistoricalInputSnapshotIdentity",
            "HistoricalRaceSnapshot",
            "HistoricalRaceEntrySnapshot",
            "HistoricalPastRaceSnapshot",
            "HistoricalInputProvenance",
            "HistoricalInputSnapshot",
            "HistoricalInputSnapshotSource",
            "HistoricalInputSnapshotRepository",
            "build_historical_input_snapshot_content_payload",
            "compute_historical_input_snapshot_content_sha256",
        ):
            self.assertFalse(hasattr(simulation_package, name))

    def test_frozen_slots_identity_metadata_and_normalization(self) -> None:
        source_one = _source(source_url="https://one.test")
        source_two = _source(source_url="https://two.test")
        self.assertEqual(source_one, source_two); self.assertEqual(hash(source_one), hash(source_two))
        entry_one = _entry(external_horse_id="one")
        entry_two = _entry(external_horse_id="two")
        self.assertEqual(entry_one.external_entry_identity, entry_two.external_entry_identity)
        self.assertEqual(hash(entry_one.external_entry_identity), hash(entry_two.external_entry_identity))
        normalized = HistoricalSourceIdentity("N\u0301AR", "system", "race")
        self.assertEqual(normalized.organization, "ŃAR")
        value = _snapshot()
        self.assertFalse(hasattr(value, "__dict__"))
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            value.internal_race_id = 99
        self.assertEqual(value.identity.captured_at.tzinfo, UTC)

    def test_strict_constructor_validation_and_decimal_rules(self) -> None:
        with self.assertRaises(ValueError): HistoricalSourceIdentity("", "system", "race")
        with self.assertRaises(ValueError): HistoricalRaceSnapshot(datetime(2026, 8, 5), START, "Tokyo", 1600, "turf", "good")
        with self.assertRaises(ValueError): HistoricalRaceEntrySnapshot(True, _entry().external_entry_identity, 1, "J", Decimal("2"), 0)
        with self.assertRaises(ValueError): HistoricalRaceEntrySnapshot(1, _entry().external_entry_identity, 1, "J", Decimal("NaN"), 0)
        with self.assertRaises(ValueError): HistoricalRaceEntrySnapshot(1, _entry().external_entry_identity, 1, "J", Decimal("0"), 0)
        with self.assertRaises(ValueError): HistoricalRaceEntrySnapshot(1, _entry().external_entry_identity, 1, "J", 2, 0)
        with self.assertRaises(ValueError): HistoricalInputSnapshot(_snapshot().identity, 1, CUTOFF, _snapshot().race, [], (), ())
        self.assertEqual(_entry().win_odds, Decimal("2"))
        past = _past(passing_order="")
        self.assertEqual(past.passing_order, "")
        self.assertEqual(past.margin, Decimal("0"))
        self.assertEqual(past.weight, Decimal("480"))

    def test_provenance_shape_timestamp_and_input_audit_compatibility(self) -> None:
        item = _provenance()[0]
        copied = InputAuditEntry(
            input_type=item.input_type, audit_key=item.audit_key, source=item.source, source_id=item.source_id,
            race_entry_id=item.race_entry_id, available_at=item.available_at, observed_at=item.observed_at,
            past_race_index=item.past_race_index,
        )
        self.assertEqual(copied.audit_key, "track")
        with self.assertRaises(ValueError): HistoricalInputProvenance("odds_win", "odds/10", "s", "id", 10, observed_at=CAPTURED)
        with self.assertRaises(ValueError): HistoricalInputProvenance("past_race", "past_race/10/none", "s", "id", 10, observed_at=CAPTURED, past_race_index=0)
        with self.assertRaises(ValueError): HistoricalInputProvenance("track", "track", "s", "id", None)
        with self.assertRaises(ValueError): HistoricalInputProvenance("track", "track", "s", "id", None, available_at=CAPTURED, observed_at=CAPTURED - timedelta(seconds=1))

    def test_snapshot_structural_and_audit_requirements(self) -> None:
        snapshot = _snapshot()
        with self.assertRaises(ValueError):
            HistoricalInputSnapshot(snapshot.identity, 100, CUTOFF, snapshot.race, (), (), ())
        duplicate_entry = replace(snapshot.entries[0], horse_no=2, entry_order=1)
        with self.assertRaises(ValueError):
            HistoricalInputSnapshot(snapshot.identity, 100, CUTOFF, snapshot.race, (snapshot.entries[0], duplicate_entry), snapshot.past_races, snapshot.provenance)
        with self.assertRaises(ValueError):
            HistoricalInputSnapshot(snapshot.identity, 100, CUTOFF, snapshot.race, snapshot.entries, snapshot.past_races, snapshot.provenance[:-1])
        foreign_entry = replace(snapshot.entries[0], external_entry_identity=HistoricalExternalEntryIdentity(HistoricalExternalRaceIdentity("JRA", "other", "r"), "entry-10"))
        with self.assertRaises(ValueError):
            HistoricalInputSnapshot(snapshot.identity, 100, CUTOFF, snapshot.race, (foreign_entry,), snapshot.past_races, snapshot.provenance)
        after_target = replace(snapshot.past_races[0], race_date=date(2026, 8, 5))
        with self.assertRaises(ValueError):
            HistoricalInputSnapshot(snapshot.identity, 100, CUTOFF, snapshot.race, snapshot.entries, (after_target,), snapshot.provenance)
        no_past = _snapshot(with_past=False)
        self.assertEqual(no_past.past_races, ())

    def test_contiguity_duplicates_and_causal_timestamps(self) -> None:
        snapshot = _snapshot()
        bad_entry = replace(snapshot.entries[0], entry_order=1)
        with self.assertRaises(ValueError): HistoricalInputSnapshot(snapshot.identity, 100, CUTOFF, snapshot.race, (bad_entry,), snapshot.past_races, snapshot.provenance)
        past_one = replace(snapshot.past_races[0], past_race_index=1)
        provenance = tuple(replace(item, audit_key="past_race/10/1", past_race_index=1) if item.input_type == "past_race" else item for item in snapshot.provenance)
        with self.assertRaises(ValueError): HistoricalInputSnapshot(snapshot.identity, 100, CUTOFF, snapshot.race, snapshot.entries, (past_one,), provenance)
        late = tuple(replace(item, observed_at=CAPTURED + timedelta(seconds=1)) for item in snapshot.provenance)
        with self.assertRaises(ValueError): HistoricalInputSnapshot(snapshot.identity, 100, CUTOFF, snapshot.race, snapshot.entries, snapshot.past_races, late)
        with self.assertRaises(ValueError): HistoricalInputSnapshot(snapshot.identity, 100, START + timedelta(seconds=1), snapshot.race, snapshot.entries, snapshot.past_races, snapshot.provenance)

    def test_each_duplicate_child_invariant_fails_closed(self) -> None:
        snapshot = _snapshot()
        original = snapshot.entries[0]
        for label, changed in (
            ("race_entry_id", replace(original, race_entry_id=10, horse_no=2, entry_order=1)),
            ("horse_no", replace(original, race_entry_id=20, horse_no=1, entry_order=1)),
            ("external_identity", replace(original, race_entry_id=20, horse_no=2, entry_order=1)),
        ):
            with self.subTest(label=label), self.assertRaises(ValueError):
                HistoricalInputSnapshot(snapshot.identity, 100, CUTOFF, snapshot.race, (original, changed), snapshot.past_races, snapshot.provenance)
        duplicate_audit = snapshot.provenance + (replace(snapshot.provenance[0], source_id="another"),)
        with self.assertRaises(ValueError):
            HistoricalInputSnapshot(snapshot.identity, 100, CUTOFF, snapshot.race, snapshot.entries, snapshot.past_races, duplicate_audit)

    def test_duplicate_entry_order_and_past_race_identity_fail_closed(self) -> None:
        snapshot = _snapshot(with_past=False)
        first = _entry(race_entry_id=10, horse_no=1, entry_order=0, external_horse_id="horse-1")
        same_order = _entry(race_entry_id=20, horse_no=2, entry_order=0, external_horse_id="horse-2")
        two_entry_provenance = _provenance(entry_id=10, past=False) + _provenance(entry_id=20, past=False)[1:]
        with self.assertRaises(ValueError):
            HistoricalInputSnapshot(
                snapshot.identity,
                100,
                CUTOFF,
                snapshot.race,
                (first, same_order),
                (),
                two_entry_provenance,
            )
        first_past = _past(index=0)
        same_past_identity = replace(first_past, race_name="Different prior race")
        with self.assertRaises(ValueError):
            HistoricalInputSnapshot(
                snapshot.identity,
                100,
                CUTOFF,
                snapshot.race,
                snapshot.entries,
                (first_past, same_past_identity),
                _provenance(),
            )

    def test_past_race_and_absence_audits_are_exclusive(self) -> None:
        with_past = _snapshot()
        none_audit = HistoricalInputProvenance(
            "past_race",
            "past_race/10/none",
            "nar_official",
            "absence-1",
            10,
            observed_at=CAPTURED - timedelta(minutes=1),
        )
        with self.assertRaises(ValueError):
            HistoricalInputSnapshot(
                with_past.identity,
                100,
                CUTOFF,
                with_past.race,
                with_past.entries,
                with_past.past_races,
                with_past.provenance + (none_audit,),
            )
        without_past = _snapshot(with_past=False)
        numbered_audits = tuple(
            replace(item, audit_key="past_race/10/0", past_race_index=0)
            if item.input_type == "past_race"
            else item
            for item in without_past.provenance
        )
        with self.assertRaises(ValueError):
            HistoricalInputSnapshot(
                without_past.identity,
                100,
                CUTOFF,
                without_past.race,
                without_past.entries,
                (),
                numbered_audits,
            )

    def test_tuple_order_is_canonicalized_only_for_payload(self) -> None:
        source = _source()
        first = _entry(race_entry_id=10, horse_no=1, entry_order=0)
        second = _entry(race_entry_id=20, horse_no=2, entry_order=1, external_horse_id="horse-2")
        provenance = (_provenance(entry_id=10, past=False)[0],) + _provenance(entry_id=10, past=False)[1:] + _provenance(entry_id=20, past=False)[1:]
        identity = HistoricalInputSnapshotIdentity("dataset-1", source, CAPTURED)
        race = HistoricalRaceSnapshot(date(2026, 8, 5), START, "Tokyo", 1600, "turf", "good")
        first_order = HistoricalInputSnapshot(identity, 100, CUTOFF, race, (first, second), (), provenance)
        second_order = HistoricalInputSnapshot(identity, 100, CUTOFF, race, (second, first), (), provenance)
        self.assertEqual(first_order.content_sha256, second_order.content_sha256)
        payload = build_historical_input_snapshot_content_payload(snapshot=second_order)
        self.assertEqual([entry["race_entry_id"] for entry in payload["entries"]], [10, 20])

    def test_past_race_and_provenance_orders_are_canonicalized_only_for_payload(self) -> None:
        snapshot = _snapshot()
        first_entry = _entry(race_entry_id=10, horse_no=1, entry_order=0, external_horse_id="horse-1")
        second_entry = _entry(race_entry_id=20, horse_no=2, entry_order=1, external_horse_id="horse-2")
        first_past = _past(race_entry_id=10, index=0)
        second_past = replace(
            _past(race_entry_id=10, index=1),
            race_name="Older prior race",
        )
        third_past = replace(
            _past(race_entry_id=20, index=0),
            race_name="Second entry prior race",
        )
        second_past_audit = HistoricalInputProvenance(
            "past_race",
            "past_race/10/1",
            "nar_official",
            "past-2",
            10,
            observed_at=CAPTURED - timedelta(minutes=1),
            past_race_index=1,
        )
        supplied_past_races = (third_past, second_past, first_past)
        complete_provenance = (
            _provenance(entry_id=10, past=True)
            + (second_past_audit,)
            + _provenance(entry_id=20, past=True)[1:]
        )
        supplied_provenance = tuple(reversed(complete_provenance))
        ordered = HistoricalInputSnapshot(
            snapshot.identity,
            100,
            CUTOFF,
            snapshot.race,
            (first_entry, second_entry),
            supplied_past_races,
            supplied_provenance,
        )
        self.assertIs(ordered.past_races, supplied_past_races)
        self.assertIs(ordered.provenance, supplied_provenance)
        self.assertEqual(
            [(item.race_entry_id, item.past_race_index) for item in ordered.past_races],
            [(20, 0), (10, 1), (10, 0)],
        )
        self.assertEqual(
            [item.audit_key for item in ordered.provenance],
            list(reversed([item.audit_key for item in complete_provenance])),
        )
        payload = build_historical_input_snapshot_content_payload(snapshot=ordered)
        self.assertEqual(
            [
                (item["race_entry_id"], item["past_race_index"])
                for item in payload["past_races"]
            ],
            [(10, 0), (10, 1), (20, 0)],
        )
        self.assertEqual([item["audit_key"] for item in payload["provenance"]], sorted(item.audit_key for item in supplied_provenance))

    def test_optional_text_and_public_digest_type_rules(self) -> None:
        race = HistoricalRaceSnapshot(date(2026, 8, 5), START, "Tokyo", 1600, "turf", "good")
        self.assertIsNone(race.race_name); self.assertIsNone(race.race_class); self.assertIsNone(race.weather)
        with self.assertRaises(ValueError): HistoricalRaceSnapshot(date(2026, 8, 5), START, "Tokyo", 1600, "turf", "good", race_name="")
        with self.assertRaises(ValueError): compute_historical_input_snapshot_content_sha256(snapshot=object())

    def test_snapshot_init_does_not_call_public_builder_or_digest(self) -> None:
        import scripts.simulation.historical_input_snapshots as module

        source = inspect.getsource(HistoricalInputSnapshot.__post_init__)
        self.assertNotIn("build_historical_input_snapshot_content_payload", source)
        self.assertNotIn("compute_historical_input_snapshot_content_sha256", source)
        self.assertIn("_build_unchecked_historical_input_snapshot_content_payload", source)
        self.assertIs(module.compute_historical_input_snapshot_content_sha256, compute_historical_input_snapshot_content_sha256)

    def test_payload_digest_ordering_and_sensitivity(self) -> None:
        snapshot = _snapshot()
        payload = build_historical_input_snapshot_content_payload(snapshot=snapshot)
        self.assertEqual(tuple(payload), ("schema_version", "snapshot_identity", "source_identity", "internal_race_id", "information_cutoff", "race", "entries", "past_races", "provenance"))
        self.assertNotIn("content_sha256", payload)
        self.assertEqual(tuple(payload["snapshot_identity"]), ("dataset_id", "organization", "source_system", "external_race_id", "captured_at"))
        self.assertEqual(tuple(payload["source_identity"]), ("organization", "source_system", "external_race_id", "source_url"))
        self.assertEqual(tuple(payload["race"]), ("target_race_date", "scheduled_start_at", "place", "distance_m", "track", "track_condition", "race_name", "race_class", "weather"))
        self.assertEqual(tuple(payload["entries"][0]), ("race_entry_id", "external_entry_identity", "horse_no", "jockey", "win_odds", "entry_order"))
        self.assertEqual(tuple(payload["entries"][0]["external_entry_identity"]), ("organization", "source_system", "external_race_id", "external_entry_id", "external_horse_id"))
        self.assertEqual(tuple(payload["past_races"][0]), ("race_entry_id", "past_race_index", "race_date", "place", "race_name", "race_class", "distance_m", "track", "weather", "track_condition", "finish", "margin", "race_time", "weight", "weight_diff", "jockey", "popularity", "odds", "passing_order", "fourth_corner_position"))
        self.assertEqual(tuple(payload["provenance"][0]), ("input_type", "audit_key", "source", "source_id", "available_at", "observed_at", "race_entry_id", "past_race_index"))
        self.assertEqual(payload["entries"][0]["win_odds"], "2")
        self.assertEqual(payload["past_races"][0]["margin"], "0")
        self.assertEqual(compute_historical_input_snapshot_content_sha256(snapshot=snapshot), snapshot.content_sha256)
        self.assertEqual(snapshot.content_sha256, _snapshot().content_sha256)
        changed_url = _snapshot(source_url="https://changed.test")
        self.assertEqual(snapshot.identity, changed_url.identity); self.assertNotEqual(snapshot.content_sha256, changed_url.content_sha256)
        changed_horse = _snapshot(external_horse_id="horse-2")
        self.assertEqual(snapshot.entries[0].external_entry_identity, changed_horse.entries[0].external_entry_identity)
        self.assertNotEqual(snapshot.content_sha256, changed_horse.content_sha256)
        changed_cutoff = _snapshot(information_cutoff=CUTOFF + timedelta(seconds=1))
        self.assertEqual(snapshot.identity, changed_cutoff.identity); self.assertNotEqual(snapshot.content_sha256, changed_cutoff.content_sha256)
        empty = _snapshot(passing_order="")
        self.assertEqual(build_historical_input_snapshot_content_payload(snapshot=empty)["past_races"][0]["passing_order"], "")
        with self.assertRaises(ValueError): build_historical_input_snapshot_content_payload(snapshot=object())

    def test_protocol_signatures_and_ellipsis_bodies(self) -> None:
        source_signature = inspect.signature(HistoricalInputSnapshotSource.load_latest_snapshot)
        repository_signature = inspect.signature(HistoricalInputSnapshotRepository.save_snapshot)
        self.assertEqual(tuple(source_signature.parameters), ("self", "dataset_id", "race_id", "information_cutoff", "source_identity"))
        self.assertTrue(all(parameter.kind is inspect.Parameter.KEYWORD_ONLY for parameter in tuple(source_signature.parameters.values())[1:]))
        self.assertEqual(tuple(repository_signature.parameters), ("self", "snapshot"))
        self.assertTrue(repository_signature.parameters["snapshot"].kind is inspect.Parameter.KEYWORD_ONLY)
        self.assertTrue(all(parameter.default is inspect.Parameter.empty for parameter in tuple(source_signature.parameters.values())[1:]))
        self.assertIs(repository_signature.parameters["snapshot"].default, inspect.Parameter.empty)
        source_hints = get_type_hints(HistoricalInputSnapshotSource.load_latest_snapshot)
        self.assertIs(source_hints["dataset_id"], str)
        self.assertIs(source_hints["race_id"], int)
        self.assertIs(source_hints["information_cutoff"], datetime)
        self.assertIs(source_hints["source_identity"], HistoricalExternalRaceIdentity)
        self.assertEqual(source_hints["return"], HistoricalInputSnapshot | None)
        repository_hints = get_type_hints(HistoricalInputSnapshotRepository.save_snapshot)
        self.assertIs(repository_hints["snapshot"], HistoricalInputSnapshot)
        self.assertIs(repository_hints["return"], type(None))
        for protocol, method_name in (
            (HistoricalInputSnapshotSource, "load_latest_snapshot"),
            (HistoricalInputSnapshotRepository, "save_snapshot"),
        ):
            method = _protocol_method_node(protocol, method_name)
            self.assertEqual(len(method.body), 1)
            self.assertIsInstance(method.body[0], ast.Expr)
            self.assertIsInstance(method.body[0].value, ast.Constant)
            self.assertIs(method.body[0].value.value, Ellipsis)
        self.assertFalse(getattr(HistoricalInputSnapshotSource, "_is_runtime_protocol", False))

    def test_source_ast_boundary(self) -> None:
        import scripts.simulation.historical_input_snapshots as module

        source = inspect.getsource(module)
        tree = ast.parse(source, type_comments=True)
        self.assertEqual(tree.type_ignores, [])
        self.assertNotIn("# type: ignore", source)
        self.assertNotIn("runtime_checkable", source)
        for forbidden in ("sqlite3", "requests", "pathlib", "subprocess", "datetime.now", "date.today", "random", "argparse", "provider", "migration"):
            self.assertNotIn(forbidden, source)
        imported = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
        self.assertFalse({"sqlite3", "requests", "subprocess", "random"} & imported)


if __name__ == "__main__":
    unittest.main()
