from __future__ import annotations

import ast
from datetime import date, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
import inspect
from typing import get_type_hints
import unittest

import scripts.simulation as simulation_package
from scripts.simulation.historical_input_evidence import HistoricalInputEvidenceReference
from scripts.simulation.historical_input_snapshot_builder import (
    HistoricalInputSnapshotAssemblyError,
    build_historical_input_snapshot,
)
from scripts.simulation.historical_input_source_records import (
    HistoricalInputSourceConflictError,
    HistoricalInputSourceRecord,
    HistoricalInputSourceValidationError,
)
from scripts.simulation.historical_input_snapshots import HistoricalInputSnapshot


UTC = timezone.utc
OBSERVED = datetime(2026, 8, 5, 9, 0, tzinfo=UTC)
AVAILABLE = OBSERVED - timedelta(minutes=1)
CAPTURED = datetime(2026, 8, 5, 10, 0, tzinfo=UTC)
CUTOFF = datetime(2026, 8, 5, 12, 0, tzinfo=UTC)
START = datetime(2026, 8, 5, 15, 30, tzinfo=UTC)
RACE_DATE = date(2026, 8, 5)
RACE_ID = "nar:20260805:1:1"


class _ValueErrorTimezone(tzinfo):
    def utcoffset(self, value: datetime | None) -> timedelta:
        raise ValueError("malformed timezone")

    def dst(self, value: datetime | None) -> timedelta:
        return timedelta(0)


def _track_values() -> dict[str, object]:
    return {
        "target_race_date": RACE_DATE,
        "scheduled_start_at": START,
        "place": "Tokyo",
        "distance_m": 1600,
        "track": "turf",
        "track_condition": "good",
        "race_name": "Target",
        "race_class": None,
        "weather": "sunny",
    }


def _past_values(race_date: date) -> dict[str, object]:
    return {
        "race_date": race_date,
        "place": "Tokyo",
        "race_name": "Past",
        "race_class": "Open",
        "distance_m": 1600,
        "track": "turf",
        "weather": "sunny",
        "track_condition": "good",
        "finish": 1,
        "reference_time_difference_seconds": Decimal("0"),
        "race_time": "1:32.0",
        "weight": Decimal("480"),
        "weight_diff": Decimal("0"),
        "jockey": "Past Jockey",
        "popularity": 1,
        "odds": Decimal("2.0"),
        "passing_order": "",
        "fourth_corner_position": 1,
    }


def _record(
    kind: str,
    *,
    external_entry_id: str | None = None,
    horse_no: int = 1,
    external_horse_id: str | None = None,
    canonical_source_url: str | None = "https://example.test/track",
    race_date: date = date(2026, 8, 1),
    provider_record_id: str | None = None,
    external_race_id: str = RACE_ID,
    organization: str = "NAR",
    source_system: str = "nar_official",
    absence_target_race_date: date = RACE_DATE,
    observed_at: datetime = OBSERVED,
    available_at: datetime | None = AVAILABLE,
) -> HistoricalInputSourceRecord:
    if kind == "track":
        values = _track_values()
        external_entry_id = None
        provider_record_id = None
    elif kind == "entry":
        assert external_entry_id is not None
        values = {
            "external_entry_id": external_entry_id,
            "external_horse_id": external_horse_id,
            "horse_no": horse_no,
        }
    elif kind == "jockey":
        assert external_entry_id is not None
        values = {"external_entry_id": external_entry_id, "jockey": f"Jockey {horse_no}"}
    elif kind == "odds_win":
        assert external_entry_id is not None
        values = {"external_entry_id": external_entry_id, "horse_no": horse_no, "win_odds": Decimal("2.5")}
    elif kind == "past_race":
        assert external_entry_id is not None
        values = _past_values(race_date)
        if provider_record_id is None:
            provider_record_id = f"past-{external_entry_id}-{race_date.isoformat()}"
    elif kind == "past_race_absence":
        assert external_entry_id is not None
        values = {
            "external_entry_id": external_entry_id,
            "query_scope": {
                "external_entry_id": external_entry_id,
                "target_race_date": absence_target_race_date,
                "strictly_before_target_race": True,
            },
            "result_count": 0,
        }
    else:
        raise AssertionError(kind)
    roles = {
        "track": ("track",),
        "entry": ("entry",),
        "jockey": ("jockey",),
        "odds_win": ("odds_win",),
        "past_race": ("historical_race_context", "historical_race_result"),
        "past_race_absence": ("past_race_absence_query",),
    }[kind]
    evidence = tuple(
        HistoricalInputEvidenceReference(
            evidence_role=role,
            canonical_source_url=canonical_source_url,
            response_sha256=str(index + 1) * 64,
            available_at=available_at,
            observed_at=observed_at,
        )
        for index, role in enumerate(roles)
    )
    return HistoricalInputSourceRecord(
        record_kind=kind,
        organization=organization,
        source_system=source_system,
        external_race_id=external_race_id,
        external_entry_id=external_entry_id,
        provider_record_id=provider_record_id,
        record_values=values,
        evidence=evidence,
    )


def _complete_records(*, track_url: str | None = "https://example.test/target") -> tuple[HistoricalInputSourceRecord, ...]:
    first = "entry-a"
    second = "entry-b"
    return (
        _record("odds_win", external_entry_id=first, horse_no=2, canonical_source_url="https://example.test/odds-a"),
        _record("past_race", external_entry_id=first, horse_no=2, race_date=date(2026, 7, 1), canonical_source_url="https://example.test/past-a-1"),
        _record("track", canonical_source_url=track_url),
        _record("jockey", external_entry_id=second, horse_no=1, canonical_source_url="https://example.test/jockey-b"),
        _record("entry", external_entry_id=first, horse_no=2, external_horse_id="horse-a", canonical_source_url="https://example.test/entry-a"),
        _record("past_race", external_entry_id=second, horse_no=1, race_date=date(2026, 8, 1), canonical_source_url="https://example.test/past-b"),
        _record("odds_win", external_entry_id=second, horse_no=1, canonical_source_url="https://example.test/odds-b"),
        _record("past_race", external_entry_id=first, horse_no=2, race_date=date(2026, 8, 2), canonical_source_url="https://example.test/past-a-2"),
        _record("jockey", external_entry_id=first, horse_no=2, canonical_source_url="https://example.test/jockey-a"),
        _record("entry", external_entry_id=second, horse_no=1, external_horse_id="horse-b", canonical_source_url="https://example.test/entry-b"),
    )


def _build(
    records: tuple[HistoricalInputSourceRecord, ...] | None = None,
    mapping: dict[str, int] | None = None,
    **overrides: object,
) -> HistoricalInputSnapshot:
    return build_historical_input_snapshot(
        dataset_id=overrides.get("dataset_id", "dataset-1"),
        internal_race_id=overrides.get("internal_race_id", 100),
        information_cutoff=overrides.get("information_cutoff", CUTOFF),
        captured_at=overrides.get("captured_at", CAPTURED),
        source_records=_complete_records() if records is None else records,
        race_entry_id_by_external_entry_id={"entry-a": 20, "entry-b": 10} if mapping is None else mapping,
    )


class HistoricalInputSnapshotBuilderTests(unittest.TestCase):
    def test_public_api_is_exact_keyword_only_and_not_exported(self) -> None:
        import scripts.simulation.historical_input_snapshot_builder as module

        public = {
            name
            for name, value in vars(module).items()
            if not name.startswith("_") and (inspect.isclass(value) or inspect.isfunction(value))
        }
        self.assertEqual(public, {"HistoricalInputSnapshotAssemblyError", "build_historical_input_snapshot"})
        signature = inspect.signature(build_historical_input_snapshot)
        self.assertTrue(all(parameter.kind is inspect.Parameter.KEYWORD_ONLY for parameter in signature.parameters.values()))
        hints = get_type_hints(build_historical_input_snapshot)
        self.assertIs(hints["return"], HistoricalInputSnapshot)
        self.assertFalse(hasattr(simulation_package, "build_historical_input_snapshot"))

    def test_complete_assembly_maps_fields_urls_provenance_and_orders(self) -> None:
        records = _complete_records()
        snapshot = _build(records)
        self.assertEqual(snapshot.identity.source_identity.source_url, "https://example.test/target")
        self.assertEqual(snapshot.race.target_race_date, RACE_DATE)
        self.assertEqual(snapshot.race.scheduled_start_at, START)
        self.assertEqual([(item.horse_no, item.entry_order) for item in snapshot.entries], [(1, 0), (2, 1)])
        self.assertEqual(snapshot.entries[0].race_entry_id, 10)
        self.assertEqual(snapshot.entries[0].external_entry_identity.external_horse_id, "horse-b")
        self.assertEqual(snapshot.entries[0].jockey, "Jockey 1")
        self.assertEqual(snapshot.entries[0].win_odds, Decimal("2.5"))
        self.assertEqual(
            [(item.race_entry_id, item.past_race_index) for item in snapshot.past_races],
            [(10, 0), (20, 0), (20, 1)],
        )
        self.assertEqual(
            [item.audit_key for item in snapshot.provenance],
            sorted(item.audit_key for item in snapshot.provenance),
        )
        records_by_id = {record.source_id: record for record in records}
        for item in snapshot.provenance:
            self.assertIs(item.source_id, records_by_id[item.source_id].source_id)
            self.assertEqual(item.source, "nar_official")
            self.assertEqual(item.evidence[0].available_at, AVAILABLE)
            self.assertEqual(item.evidence[0].observed_at, OBSERVED)

    def test_source_url_none_and_non_track_urls_do_not_change_selection(self) -> None:
        self.assertIs(_build(_complete_records(track_url=None)).identity.source_identity.source_url, None)
        first = _build(_complete_records(track_url="https://example.test/target"))
        changed = tuple(
            _record(
                record.record_kind,
                external_entry_id=record.external_entry_id,
                horse_no=record.record_values.get("horse_no", 1),
                external_horse_id=record.record_values.get("external_horse_id"),
                canonical_source_url=(
                    record.evidence[0].canonical_source_url
                    if record.record_kind == "track"
                    else "https://different.example.test/non-track"
                ),
                race_date=record.record_values.get("race_date", date(2026, 8, 1)),
                provider_record_id=record.provider_record_id,
            )
            for record in _complete_records(track_url="https://example.test/target")
        )
        self.assertEqual(changed[0].record_kind, "odds_win")
        self.assertEqual(_build(changed).identity.source_identity.source_url, first.identity.source_identity.source_url)

    def test_exact_tuple_c1a_error_and_top_level_validation(self) -> None:
        records = _complete_records()
        with self.assertRaises(HistoricalInputSnapshotAssemblyError):
            build_historical_input_snapshot(
                dataset_id="dataset", internal_race_id=1, information_cutoff=CUTOFF, captured_at=CAPTURED,
                source_records=list(records), race_entry_id_by_external_entry_id={"entry-a": 20, "entry-b": 10},
            )
        with self.assertRaises(HistoricalInputSourceConflictError):
            _build((records[0], records[0]))
        for name, value in (("dataset_id", ""), ("internal_race_id", True), ("captured_at", datetime(2026, 8, 5))):
            with self.subTest(name=name):
                with self.assertRaises(HistoricalInputSnapshotAssemblyError):
                    _build(**{name: value})
        with self.assertRaises(HistoricalInputSnapshotAssemblyError):
            _build(mapping={"entry-a": True, "entry-b": 10})
        for mapping in (
            "not-a-mapping",
            {1: 20, "entry-b": 10},
            {"entry-a": 0, "entry-b": 10},
            {"entry-a": -1, "entry-b": 10},
        ):
            with self.subTest(mapping=mapping):
                with self.assertRaises(HistoricalInputSnapshotAssemblyError):
                    _build(mapping=mapping)
        bad = tuple(object() if index == 0 else record for index, record in enumerate(records))
        with self.assertRaises(HistoricalInputSourceValidationError):
            build_historical_input_snapshot(
                dataset_id="dataset",
                internal_race_id=1,
                information_cutoff=CUTOFF,
                captured_at=CAPTURED,
                source_records=bad,
                race_entry_id_by_external_entry_id={"entry-a": 20, "entry-b": 10},
            )

    def test_malformed_timezone_is_assembler_error_for_both_caller_timestamps(self) -> None:
        malformed = datetime(2026, 8, 5, 10, 0, tzinfo=_ValueErrorTimezone())
        for name in ("captured_at", "information_cutoff"):
            with self.subTest(name=name):
                with self.assertRaises(HistoricalInputSnapshotAssemblyError) as context:
                    _build(**{name: malformed})
                self.assertIs(type(context.exception), HistoricalInputSnapshotAssemblyError)

    def test_grouping_mapping_and_horse_number_fail_closed(self) -> None:
        records = _complete_records()
        cases: list[tuple[str, tuple[HistoricalInputSourceRecord, ...], dict[str, int]]] = [
            ("missing mapping", records, {"entry-a": 20}),
            ("extra mapping", records, {"entry-a": 20, "entry-b": 10, "entry-c": 30}),
            ("duplicate local id", records, {"entry-a": 10, "entry-b": 10}),
            ("missing jockey", tuple(record for record in records if record.record_kind != "jockey" or record.external_entry_id != "entry-a"), {"entry-a": 20, "entry-b": 10}),
            ("orphan odds", records + (_record("odds_win", external_entry_id="orphan", horse_no=3),), {"entry-a": 20, "entry-b": 10}),
            ("duplicate entry", records + (_record("entry", external_entry_id="entry-a", horse_no=2, external_horse_id="other"),), {"entry-a": 20, "entry-b": 10}),
        ]
        for label, candidate, mapping in cases:
            with self.subTest(label=label):
                with self.assertRaises(HistoricalInputSnapshotAssemblyError):
                    _build(candidate, mapping)
        mismatch = tuple(
            _record("odds_win", external_entry_id="entry-a", horse_no=3) if record.record_kind == "odds_win" and record.external_entry_id == "entry-a" else record
            for record in records
        )
        with self.assertRaises(HistoricalInputSnapshotAssemblyError):
            _build(mismatch)

    def test_track_family_and_duplicate_horse_boundaries_fail_closed(self) -> None:
        records = _complete_records()
        with self.assertRaises(HistoricalInputSnapshotAssemblyError):
            _build(tuple(record for record in records if record.record_kind != "track"))
        two_tracks = records + (_record("track", canonical_source_url="https://example.test/second-track"),)
        with self.assertRaises(HistoricalInputSnapshotAssemblyError):
            _build(two_tracks)
        foreign = tuple(
            _record("track", external_race_id="nar:other") if record.record_kind == "track" else record
            for record in records
        )
        with self.assertRaises(HistoricalInputSnapshotAssemblyError):
            _build(foreign)
        duplicate_horse = tuple(
            _record("entry", external_entry_id="entry-b", horse_no=2, external_horse_id="horse-b")
            if record.record_kind == "entry" and record.external_entry_id == "entry-b"
            else _record("odds_win", external_entry_id="entry-b", horse_no=2)
            if record.record_kind == "odds_win" and record.external_entry_id == "entry-b"
            else record
            for record in records
        )
        with self.assertRaises(HistoricalInputSnapshotAssemblyError):
            _build(duplicate_horse)

    def test_temporal_past_evidence_and_absence_rules_fail_closed(self) -> None:
        with self.assertRaises(HistoricalInputSnapshotAssemblyError):
            _build(information_cutoff=CAPTURED - timedelta(seconds=1))
        with self.assertRaises(HistoricalInputSnapshotAssemblyError):
            _build(information_cutoff=START + timedelta(seconds=1))
        late = tuple(
            _record(
                record.record_kind,
                external_entry_id=record.external_entry_id,
                horse_no=record.record_values.get("horse_no", 1),
                external_horse_id=record.record_values.get("external_horse_id"),
                canonical_source_url=record.evidence[0].canonical_source_url,
                race_date=record.record_values.get("race_date", date(2026, 8, 1)),
                provider_record_id=record.provider_record_id,
                observed_at=CAPTURED + timedelta(seconds=1),
            )
            if record.record_kind == "track"
            else record
            for record in _complete_records()
        )
        with self.assertRaises(HistoricalInputSnapshotAssemblyError):
            _build(late)
        no_past = tuple(record for record in _complete_records() if record.record_kind != "past_race")
        with self.assertRaises(HistoricalInputSnapshotAssemblyError):
            _build(no_past)
        conflict = _complete_records() + (_record("past_race_absence", external_entry_id="entry-a"),)
        with self.assertRaises(HistoricalInputSnapshotAssemblyError):
            _build(conflict)
        absence_records = tuple(record for record in _complete_records() if record.external_entry_id != "entry-b") + (
            _record("entry", external_entry_id="entry-b", horse_no=1, external_horse_id="horse-b"),
            _record("jockey", external_entry_id="entry-b", horse_no=1),
            _record("odds_win", external_entry_id="entry-b", horse_no=1),
            _record("past_race_absence", external_entry_id="entry-b"),
        )
        snapshot = _build(absence_records)
        self.assertIn("past_race/10/none", {item.audit_key for item in snapshot.provenance})
        wrong_absence_date = tuple(
            _record(
                "past_race_absence",
                external_entry_id="entry-b",
                absence_target_race_date=date(2026, 8, 4),
            )
            if record.record_kind == "past_race_absence" else record
            for record in absence_records
        )
        with self.assertRaises(HistoricalInputSnapshotAssemblyError):
            _build(wrong_absence_date)

    def test_c1b_shaped_records_without_past_evidence_are_rejected(self) -> None:
        c1b_only = tuple(
            record for record in _complete_records() if record.record_kind in {"track", "entry", "jockey", "odds_win"}
        )
        with self.assertRaises(HistoricalInputSnapshotAssemblyError):
            _build(c1b_only)

    def test_past_date_and_same_date_ambiguity_fail_closed(self) -> None:
        target_date = tuple(
            _record("past_race", external_entry_id="entry-a", horse_no=2, race_date=RACE_DATE, provider_record_id="at-target")
            if (
                record.record_kind == "past_race"
                and record.external_entry_id == "entry-a"
                and record.record_values["race_date"] == date(2026, 7, 1)
            )
            else record
            for record in _complete_records()
        )
        with self.assertRaises(HistoricalInputSnapshotAssemblyError):
            _build(target_date)
        ambiguous = _complete_records() + (
            _record("past_race", external_entry_id="entry-a", horse_no=2, race_date=date(2026, 8, 2), provider_record_id="same-date-different-provider"),
        )
        with self.assertRaises(HistoricalInputSnapshotAssemblyError):
            _build(ambiguous)

    def test_source_tuple_permutation_produces_equal_snapshot_and_digest(self) -> None:
        records = _complete_records()
        first = _build(records)
        second = _build(tuple(reversed(records)))
        self.assertEqual(first, second)
        self.assertEqual(first.content_sha256, second.content_sha256)
        self.assertEqual([item.entry_order for item in first.entries], list(range(len(first.entries))))
        self.assertEqual(
            [(item.race_entry_id, item.past_race_index) for item in first.past_races],
            sorted((item.race_entry_id, item.past_race_index) for item in first.past_races),
        )
        self.assertEqual([item.audit_key for item in first.provenance], sorted(item.audit_key for item in first.provenance))

    def test_source_ast_has_only_pure_domain_dependencies(self) -> None:
        import scripts.simulation.historical_input_snapshot_builder as module

        source = inspect.getsource(module)
        tree = ast.parse(source, type_comments=True)
        self.assertEqual(tree.type_ignores, [])
        forbidden = {
            "sqlite3", "requests", "urllib.request", "pathlib", "open(", "datetime.now", "datetime.utcnow",
            "random", "uuid", "nar_provider", "horse_parser", "nar_historical_input_source", "SimulationRaceInput",
        }
        for fragment in forbidden:
            self.assertNotIn(fragment, source)
        handlers = [node for node in ast.walk(tree) if isinstance(node, ast.ExceptHandler)]
        self.assertEqual(len(handlers), 1)
        self.assertIsInstance(handlers[0].type, ast.Tuple)
        self.assertEqual(
            {item.id for item in handlers[0].type.elts if isinstance(item, ast.Name)},
            {"TypeError", "ValueError", "OverflowError"},
        )


if __name__ == "__main__":
    unittest.main()
