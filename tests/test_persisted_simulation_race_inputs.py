from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import FrozenInstanceError, fields
from decimal import Decimal
from datetime import datetime
import inspect
from pathlib import Path
from types import MappingProxyType
from typing import get_type_hints
import unittest

import scripts.simulation as simulation_package
from scripts.simulation.models import SimulationRaceInput
from scripts.simulation.persisted_simulation_application_inputs import (
    PersistedSimulationApplicationInputs,
    assemble_persisted_simulation_application_inputs,
)
from scripts.simulation.persisted_simulation_race_inputs import (
    assemble_persisted_simulation_race_inputs,
)
from scripts.simulation.persisted_simulation_request_document import (
    PersistedSimulationRequestDocument,
)
from scripts.simulation.validation import SimulationValidationError


def _stamp(source_id: str) -> dict[str, object]:
    return {
        "source": "official",
        "source_id": source_id,
        "available_at": "2026-08-05T12:00:00+09:00",
        "observed_at": "2026-08-05T12:01:00+09:00",
    }


def _past_race() -> dict[str, object]:
    return {
        "race_date": "2026-08-01",
        "place": "Tokyo",
        "race_name": "Test race",
        "race_class": "G3",
        "distance": 1600,
        "track": "turf",
        "weather": "sunny",
        "track_condition": "good",
        "finish": 1,
        "margin": 0.0,
        "time": "1:32.0",
        "weight": 480.0,
        "weight_diff": 0.0,
        "jockey": "Rider A",
        "popularity": 1,
        "odds": 2.5,
        "passing_order": "1-1-1-1",
        "fourth_corner_position": 1,
        "audit": _stamp("past-1"),
    }


def _entry(
    entry_id: int,
    *,
    past_count: int = 0,
    with_past_race: bool | None = None,
) -> dict[str, object]:
    if with_past_race is not None:
        past_count = 1 if with_past_race else 0
    past_races = [_past_race() for _ in range(past_count)]
    for index, past_race in enumerate(past_races):
        past_race["race_date"] = "2026-08-01" if index == 0 else "2026-07-31"
        past_race["race_name"] = f"Test race {index}"
        past_race["finish"] = index + 1
        past_race["margin"] = float(index) / 2
        past_race["weight"] = 480.0 + index
        past_race["weight_diff"] = -float(index)
        past_race["popularity"] = index
        past_race["odds"] = 2.5 + index
        past_race["passing_order"] = f"{index + 1}-1-1-1"
        past_race["fourth_corner_position"] = index
        past_race["audit"] = _stamp(f"past-{entry_id}-{index}")
    return {
        "race_entry_id": entry_id,
        "jockey_name": f"Rider {entry_id}",
        "odds": 2.0,
        "past_races": past_races,
        "audits": {
            "entry": _stamp(f"entry-{entry_id}"),
            "jockey": _stamp(f"jockey-{entry_id}"),
            "odds": _stamp(f"odds-{entry_id}"),
            "past_race_absence": None if past_count else _stamp(f"absence-{entry_id}"),
        },
    }


def _race(race_id: int, *, scheduled_at: str, entries: list[dict[str, object]]) -> dict[str, object]:
    return {
        "race_id": race_id,
        "target_race_date": "2026-08-05",
        "scheduled_start_at": scheduled_at,
        "information_cutoff": "2026-08-05T15:30:00+09:00",
        "audit": {
            "source": "official",
            "captured_at": "2026-08-05T12:10:00+09:00",
            "is_complete": True,
        },
        "track_conditions": {
            "place": "Tokyo",
            "distance": 1600,
            "track": "turf",
            "track_condition": "good",
            "audit": _stamp(f"track-{race_id}"),
        },
        "entries": entries,
    }


def _document(
    *,
    races: list[dict[str, object]] | None = None,
    budgets_by_race_id: dict[str, object] | None = None,
    database_path: Path | None = None,
) -> PersistedSimulationRequestDocument:
    return PersistedSimulationRequestDocument(
        schema_version=1,
        source_path=Path("request.json"),
        database_path=database_path if database_path is not None else Path("simulation.db"),
        run_context={
            "run_id": "run-1",
            "dataset_id": "dataset-1",
            "started_at": "2026-08-05T12:30:00+09:00",
            "target_commit_id": "commit-1",
        },
        strategy={
            "strategy_name": "RuleBasedBetStrategy",
            "allowed_bet_types": [],
            "max_bet_count": 3,
            "selection_style": "formation",
            "min_combination_score": 0.0,
            "max_candidates": 5,
            "sort_condition": "generator_rank",
            "allocation_policy": {
                "policy_name": "fixed_stake_per_recommendation",
                "policy_version": "1",
                "parameters": {"stake_amount": 100},
            },
        },
        pipeline={"track_reference_date": "2026-08-05"},
        races=tuple(races if races is not None else []),
        budgets_by_race_id=(
            budgets_by_race_id
            if budgets_by_race_id is not None
            else {"10": {"total_amount": 100}, "20": {"total_amount": 200}}
        ),
    )


def _application_inputs(document: PersistedSimulationRequestDocument) -> PersistedSimulationApplicationInputs:
    return assemble_persisted_simulation_application_inputs(document=document)


def _corrupt_document(
    document: PersistedSimulationRequestDocument,
    **changes: object,
) -> PersistedSimulationRequestDocument:
    result = object.__new__(PersistedSimulationRequestDocument)
    for field in fields(PersistedSimulationRequestDocument):
        object.__setattr__(result, field.name, getattr(document, field.name))
    for name, value in changes.items():
        object.__setattr__(result, name, value)
    return result


def _raw_document(races: list[dict[str, object]]) -> PersistedSimulationRequestDocument:
    """Keep exact document type while bypassing the loader's JSON-value freeze for boundary tests."""
    document = _document(races=_valid_races())
    return _corrupt_document(document, races=_freeze_raw(races))


def _freeze_raw(value: object) -> object:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze_raw(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze_raw(item) for item in value)
    return value


def _mutable_nested_document(races: list[dict[str, object]]) -> PersistedSimulationRequestDocument:
    """Exact document with required tuple containers but deliberately mutable nested mappings."""
    for race in races:
        entries = race["entries"]
        for entry in entries:
            entry["past_races"] = tuple(entry["past_races"])
        race["entries"] = tuple(entries)
    base = _document(races=_valid_races())
    return _corrupt_document(base, races=tuple(races))


def _valid_races() -> list[dict[str, object]]:
    return [
        _race(10, scheduled_at="2026-08-05T15:40:00+09:00", entries=[_entry(101, past_count=2), _entry(102)]),
        _race(20, scheduled_at="2026-08-05T16:10:00+09:00", entries=[_entry(201)]),
    ]


class PersistedSimulationRaceInputsTest(unittest.TestCase):
    def test_formal_api_and_valid_sorted_assembly(self) -> None:
        signature = inspect.signature(assemble_persisted_simulation_race_inputs)
        self.assertEqual(tuple(signature.parameters), ("document", "application_inputs"))
        self.assertTrue(all(parameter.kind is inspect.Parameter.KEYWORD_ONLY for parameter in signature.parameters.values()))
        hints = get_type_hints(assemble_persisted_simulation_race_inputs)
        self.assertIs(hints["document"], PersistedSimulationRequestDocument)
        self.assertIs(hints["application_inputs"], PersistedSimulationApplicationInputs)
        self.assertEqual(hints["return"], tuple[SimulationRaceInput, ...])
        module = inspect.getmodule(assemble_persisted_simulation_race_inputs)
        self.assertIsNotNone(module)
        members = inspect.getmembers(module)
        self.assertEqual(
            [name for name, value in members if inspect.isfunction(value) and value.__module__ == module.__name__ and not name.startswith("_")],
            ["assemble_persisted_simulation_race_inputs"],
        )
        self.assertEqual(
            [name for name, value in members if inspect.isclass(value) and value.__module__ == module.__name__],
            [],
        )
        self.assertEqual(module.__all__, ["assemble_persisted_simulation_race_inputs"])
        self.assertFalse(hasattr(simulation_package, "assemble_persisted_simulation_race_inputs"))
        self.assertNotIn("assemble_persisted_simulation_race_inputs", getattr(simulation_package, "__all__", ()))

        document = _document(races=[
            _race(20, scheduled_at="2026-08-05T16:10:00+09:00", entries=[_entry(202, with_past_race=False)]),
            _race(10, scheduled_at="2026-08-05T15:40:00+09:00", entries=[_entry(102, past_count=2), _entry(101, with_past_race=False)]),
        ])
        application_inputs = _application_inputs(document)
        result = assemble_persisted_simulation_race_inputs(document=document, application_inputs=application_inputs)

        self.assertIs(type(result), tuple)
        self.assertEqual([item.race_id for item in result], [10, 20])
        self.assertTrue(all(type(item) is SimulationRaceInput for item in result))
        self.assertEqual(result[0].target_race_date.isoformat(), "2026-08-05")
        self.assertEqual(result[0].scheduled_start_at.isoformat(), "2026-08-05T15:40:00+09:00")
        self.assertEqual(result[0].information_cutoff.isoformat(), "2026-08-05T15:30:00+09:00")
        self.assertEqual(type(result[0].pipeline_input).__name__, "ImmutableRacePredictionInput")
        self.assertEqual(result[0].pipeline_input.prediction_time, result[0].information_cutoff.isoformat())
        self.assertEqual(result[0].pipeline_input.race_horse_count, 2)
        self.assertEqual(result[0].pipeline_input.race_id, 10)
        self.assertEqual(list(result[0].pipeline_input.horse_past_races), [101, 102])
        self.assertEqual(list(result[0].pipeline_input.jockey_names_by_horse), [101, 102])
        self.assertEqual(list(result[0].pipeline_input.odds_by_horse), [101, 102])
        track_snapshot = result[0].pipeline_input.track_conditions
        self.assertEqual(
            {field.name: getattr(track_snapshot, field.name) for field in fields(track_snapshot)},
            {"place": "Tokyo", "distance": 1600, "track": "turf", "track_condition": "good"},
        )
        self.assertEqual(
            type(result[0].pipeline_input.horse_past_races[102][0]).__name__,
            "PastRaceSnapshot",
        )
        snapshots = result[0].pipeline_input.horse_past_races[102]
        self.assertEqual(len(snapshots), 2)
        expected_pasts = (
            {"horse_id": 102, "race_date": "2026-08-01", "place": "Tokyo", "race_name": "Test race 0", "race_class": "G3", "distance": 1600, "track": "turf", "weather": "sunny", "track_condition": "good", "finish": 1, "margin": 0.0, "time": "1:32.0", "weight": 480.0, "weight_diff": 0.0, "jockey": "Rider A", "popularity": 0, "odds": 2.5, "passing_order": "1-1-1-1", "fourth_corner_position": 0},
            {"horse_id": 102, "race_date": "2026-07-31", "place": "Tokyo", "race_name": "Test race 1", "race_class": "G3", "distance": 1600, "track": "turf", "weather": "sunny", "track_condition": "good", "finish": 2, "margin": 0.5, "time": "1:32.0", "weight": 481.0, "weight_diff": -1.0, "jockey": "Rider A", "popularity": 1, "odds": 3.5, "passing_order": "2-1-1-1", "fourth_corner_position": 1},
        )
        self.assertEqual(
            [{field.name: getattr(snapshot, field.name) for field in fields(snapshot)} for snapshot in snapshots],
            list(expected_pasts),
        )
        self.assertEqual(
            [entry.audit_key for entry in result[0].input_snapshot_audit.entries],
            ["entry/101", "odds/101", "jockey/101", "past_race/101/none", "entry/102", "odds/102", "jockey/102", "past_race/102/0", "past_race/102/1", "track"],
        )
        audit = result[0].input_snapshot_audit
        self.assertEqual((audit.dataset_id, audit.source, audit.captured_at.isoformat(), audit.is_complete), ("dataset-1", "official", "2026-08-05T12:10:00+09:00", True))
        self.assertEqual(audit.entries[-1].audit_key, "track")
        self.assertEqual(audit.entries[-1].race_entry_id, None)
        self.assertEqual(audit.entries[8].past_race_index, 1)
        self.assertTrue(all(entry.available_at is not None or entry.observed_at is not None for entry in audit.entries))
        self.assertEqual(
            [
                (entry.input_type, entry.audit_key, entry.source, entry.source_id, entry.race_entry_id, entry.available_at.isoformat() if entry.available_at else None, entry.observed_at.isoformat() if entry.observed_at else None, entry.past_race_index)
                for entry in audit.entries
            ],
            [
                ("entry", "entry/101", "official", "entry-101", 101, "2026-08-05T12:00:00+09:00", "2026-08-05T12:01:00+09:00", None),
                ("odds", "odds/101", "official", "odds-101", 101, "2026-08-05T12:00:00+09:00", "2026-08-05T12:01:00+09:00", None),
                ("jockey", "jockey/101", "official", "jockey-101", 101, "2026-08-05T12:00:00+09:00", "2026-08-05T12:01:00+09:00", None),
                ("past_race", "past_race/101/none", "official", "absence-101", 101, "2026-08-05T12:00:00+09:00", "2026-08-05T12:01:00+09:00", None),
                ("entry", "entry/102", "official", "entry-102", 102, "2026-08-05T12:00:00+09:00", "2026-08-05T12:01:00+09:00", None),
                ("odds", "odds/102", "official", "odds-102", 102, "2026-08-05T12:00:00+09:00", "2026-08-05T12:01:00+09:00", None),
                ("jockey", "jockey/102", "official", "jockey-102", 102, "2026-08-05T12:00:00+09:00", "2026-08-05T12:01:00+09:00", None),
                ("past_race", "past_race/102/0", "official", "past-102-0", 102, "2026-08-05T12:00:00+09:00", "2026-08-05T12:01:00+09:00", 0),
                ("past_race", "past_race/102/1", "official", "past-102-1", 102, "2026-08-05T12:00:00+09:00", "2026-08-05T12:01:00+09:00", 1),
                ("track", "track", "official", "track-10", None, "2026-08-05T12:00:00+09:00", "2026-08-05T12:01:00+09:00", None),
            ],
        )
        self.assertEqual(result[0].information_cutoff, datetime.fromisoformat("2026-08-05T15:30:00+09:00"))

    def test_prevalidation_and_direct_input_fail_closed(self) -> None:
        document = _document(races=[])
        application_inputs = assemble_persisted_simulation_application_inputs(document=document)
        with self.assertRaisesRegex(ValueError, "document must be a PersistedSimulationRequestDocument"):
            assemble_persisted_simulation_race_inputs(document=object(), application_inputs=application_inputs)
        with self.assertRaisesRegex(ValueError, "application_inputs must be a PersistedSimulationApplicationInputs"):
            assemble_persisted_simulation_race_inputs(document=document, application_inputs=object())
        with self.assertRaisesRegex(ValueError, "race IDs must exactly match application budget race IDs"):
            assemble_persisted_simulation_race_inputs(document=document, application_inputs=application_inputs)

        duplicate = _document(races=[
            _race(10, scheduled_at="2026-08-05T15:40:00+09:00", entries=[_entry(101, with_past_race=False)]),
            _race(10, scheduled_at="2026-08-05T16:10:00+09:00", entries=[_entry(102, with_past_race=False)]),
        ])
        duplicate_inputs = assemble_persisted_simulation_application_inputs(document=duplicate)
        with self.assertRaisesRegex(ValueError, "document.races must not contain duplicate race_id values"):
            assemble_persisted_simulation_race_inputs(document=duplicate, application_inputs=duplicate_inputs)

    def test_exact_input_types_and_database_path_identity(self) -> None:
        document = _document(races=_valid_races())
        inputs = _application_inputs(document)

        class DocumentSubclass(PersistedSimulationRequestDocument):
            pass

        class InputsSubclass(PersistedSimulationApplicationInputs):
            pass

        with self.assertRaises(ValueError):
            assemble_persisted_simulation_race_inputs(
                document=object(), application_inputs=inputs,
            )
        with self.assertRaises(ValueError):
            assemble_persisted_simulation_race_inputs(
                document=object.__new__(DocumentSubclass), application_inputs=inputs,
            )
        with self.assertRaises(ValueError):
            assemble_persisted_simulation_race_inputs(
                document=document, application_inputs=object(),
            )
        with self.assertRaises(ValueError):
            assemble_persisted_simulation_race_inputs(
                document=document, application_inputs=object.__new__(InputsSubclass),
            )
        other_path = Path(str(document.database_path))
        self.assertEqual(other_path, document.database_path)
        self.assertIsNot(other_path, document.database_path)
        other_inputs = PersistedSimulationApplicationInputs(
            database_path=other_path,
            run_context=inputs.run_context,
            strategy_identity=inputs.strategy_identity,
            prediction_pipeline=inputs.prediction_pipeline,
            budgets_by_race_id=inputs.budgets_by_race_id,
        )
        with self.assertRaisesRegex(ValueError, "application_inputs.database_path must be document.database_path"):
            assemble_persisted_simulation_race_inputs(document=document, application_inputs=other_inputs)

    def test_empty_and_budget_set_cases(self) -> None:
        empty_document = _document(races=[], budgets_by_race_id={})
        self.assertEqual(
            assemble_persisted_simulation_race_inputs(
                document=empty_document, application_inputs=_application_inputs(empty_document),
            ),
            (),
        )
        for races, budgets in (
            ([_valid_races()[0]], {}),
            ([], {"10": {"total_amount": 100}}),
            (_valid_races(), {"10": {"total_amount": 100}}),
            (_valid_races(), {"10": {"total_amount": 100}, "20": {"total_amount": 100}, "30": {"total_amount": 100}}),
        ):
            with self.subTest(races=len(races), budgets=len(budgets)):
                document = _document(races=races, budgets_by_race_id=budgets)
                with self.assertRaisesRegex(ValueError, "race IDs must exactly match application budget race IDs"):
                    assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))

    def test_race_container_schema_id_and_pre_scan_order(self) -> None:
        document = _document(races=_valid_races())
        inputs = _application_inputs(document)
        with self.assertRaisesRegex(ValueError, "document.races must be an array"):
            assemble_persisted_simulation_race_inputs(document=_corrupt_document(document, races=[]), application_inputs=inputs)
        for value, error in (("wrong", "document.races must contain objects"),):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, error):
                assemble_persisted_simulation_race_inputs(document=_corrupt_document(document, races=(value,)), application_inputs=inputs)
        for mutate, error in (
            (lambda races: races[0].pop("entries"), "race keys must exactly match the race schema"),
            (lambda races: races[0].__setitem__("extra", 1), "race keys must exactly match the race schema"),
            (lambda races: races[0].__setitem__("race_id", True), "race.race_id must be a positive integer"),
            (lambda races: races[0].__setitem__("race_id", 0), "race.race_id must be a positive integer"),
            (lambda races: races[0].__setitem__("race_id", -1), "race.race_id must be a positive integer"),
            (lambda races: races[0].__setitem__("race_id", 1.0), "race.race_id must be a positive integer"),
            (lambda races: races[0].__setitem__("race_id", "10"), "race.race_id must be a positive integer"),
            (lambda races: races[1].__setitem__("race_id", 10), "document.races must not contain duplicate race_id values"),
        ):
            races = deepcopy(_valid_races())
            mutate(races)
            invalid = _document(races=races)
            with self.subTest(error=error), self.assertRaisesRegex(ValueError, error):
                assemble_persisted_simulation_race_inputs(document=invalid, application_inputs=_application_inputs(invalid))
        races = deepcopy(_valid_races())
        races[0]["race_id"] = 0
        races[1].pop("entries")
        invalid = _document(races=races)
        with self.assertRaisesRegex(ValueError, "race keys must exactly match the race schema"):
            assemble_persisted_simulation_race_inputs(document=invalid, application_inputs=_application_inputs(invalid))

    def test_dates_required_datetimes_and_race_audit_matrix(self) -> None:
        for value in ("20260805", "2026-W32-3", "2026/08/05", "2026-8-5", "2026-08-05T00:00:00", "", " ", 1, True, None):
            races = _valid_races()
            races[0]["target_race_date"] = value
            document = _document(races=races)
            with self.subTest(date=value), self.assertRaisesRegex(ValueError, "race.target_race_date must be a canonical ISO date"):
                assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))
        for field in ("scheduled_start_at", "information_cutoff"):
            for value in (True, "broken", "2026-08-05", "2026-08-05T12:00:00"):
                races = _valid_races()
                races[0][field] = value
                document = _raw_document(races)
                with self.subTest(field=field, value=value), self.assertRaisesRegex(ValueError, f"race.{field} must be an ISO 8601 timezone-aware datetime"):
                    assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))
        for value in ("2026-08-05T15:40:00Z", "2026-08-05T15:40:00+09:00"):
            races = _valid_races()
            races[0]["scheduled_start_at"] = value
            races[0]["information_cutoff"] = value
            document = _document(races=races)
            self.assertEqual(len(assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))), 2)
        races = _valid_races()
        races[0]["information_cutoff"] = "2026-08-05T15:41:00+09:00"
        document = _document(races=races)
        with self.assertRaisesRegex(ValueError, "race.information_cutoff must be earlier than or equal to race.scheduled_start_at"):
            assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))
        for value in ({}, {"source": "x", "captured_at": "2026-08-05T12:00:00+09:00"}, {"source": "x", "captured_at": "2026-08-05T12:00:00+09:00", "is_complete": True, "x": 1},):
            races = _valid_races(); races[0]["audit"] = value
            document = _document(races=races)
            with self.subTest(audit=value), self.assertRaises(ValueError):
                assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))
        for value in (0, 1, "true", None):
            races = _valid_races(); races[0]["audit"]["is_complete"] = value
            document = _document(races=races)
            with self.subTest(complete=value), self.assertRaisesRegex(ValueError, "race.audit.is_complete must be a boolean"):
                assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))

    def test_generic_audit_track_and_entry_matrices(self) -> None:
        paths = (
            ("track_conditions", "audit"),
            ("entries", 0, "audits", "entry"),
            ("entries", 0, "audits", "jockey"),
            ("entries", 0, "audits", "odds"),
            ("entries", 1, "audits", "past_race_absence"),
            ("entries", 0, "past_races", 0, "audit"),
        )
        for path in paths:
            races = _valid_races()
            target: object = races[0]
            for item in path:
                target = target[item]  # type: ignore[index]
            self.assertIsInstance(target, dict)
            invalid_races = deepcopy(_valid_races())
            item: object = invalid_races[0]
            for segment in path:
                item = item[segment]  # type: ignore[index]
            item["available_at"] = None  # type: ignore[index]
            item["observed_at"] = None  # type: ignore[index]
            document = _document(races=invalid_races)
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, "requires available_at or observed_at"):
                assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))
        races = _valid_races()
        races[0]["track_conditions"] = "bad"
        document = _document(races=races)
        with self.assertRaisesRegex(ValueError, "race.track_conditions must be an object"):
            assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))
        for field, values, error in (
            ("place", (True, "", " "), "race.track_conditions.place must be a non-empty string"),
            ("distance", (True, 0, -1, 1.5), "race.track_conditions.distance must be a positive integer"),
            ("track", (True, "", " "), "race.track_conditions.track must be a non-empty string"),
            ("track_condition", (True, "", " "), "race.track_conditions.track_condition must be a non-empty string"),
        ):
            for value in values:
                races = _valid_races(); races[0]["track_conditions"][field] = value
                document = _raw_document(races)
                with self.subTest(field=field, value=value), self.assertRaisesRegex(ValueError, error):
                    assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))
        for mutate, error in (
            (lambda entries: entries.__setitem__(slice(None), []), "race.entries must be a non-empty array"),
            (lambda entries: entries.__setitem__(slice(None), ["bad"]), "race.entries must contain objects"),
        ):
            document = _document(races=_valid_races())
            invalid = _corrupt_document(document, races=(dict(document.races[0], entries=[]), document.races[1]))
            if error.endswith("objects"):
                invalid = _corrupt_document(document, races=(dict(document.races[0], entries=("bad",)), document.races[1]))
            with self.subTest(error=error), self.assertRaisesRegex(ValueError, error):
                assemble_persisted_simulation_race_inputs(document=invalid, application_inputs=_application_inputs(document))
        for field, values, error in (
            ("race_entry_id", (True, 0, -1, 1.5), "entry.race_entry_id must be a positive integer"),
            ("jockey_name", (True, "", " "), "entry.jockey_name must be a non-empty string"),
            ("odds", (True, 0, -1, float("nan"), float("inf"), float("-inf"), Decimal("2"), "2", 10**10000, -(10**10000)), "entry.odds must be a positive finite number"),
        ):
            for value in values:
                races = _valid_races(); races[0]["entries"][0][field] = value
                document = _raw_document(races)
                with self.subTest(field=field, value=type(value).__name__), self.assertRaisesRegex(ValueError, error):
                    assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))

    def test_past_race_absence_schema_numeric_temporal_and_immutability(self) -> None:
        for past_count, absence, error in (
            (0, None, "past_race_absence is required"),
            (0, "bad", "past_race_absence is required"),
            (1, _stamp("unexpected"), "past_race_absence must be null"),
        ):
            races = _valid_races(); races[0]["entries"][0] = _entry(101, past_count=past_count)
            races[0]["entries"][0]["audits"]["past_race_absence"] = absence
            document = _document(races=races)
            with self.subTest(past_count=past_count), self.assertRaisesRegex(ValueError, error):
                assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))
        for field in ("place", "race_name", "race_class", "track", "weather", "track_condition", "time", "jockey", "passing_order"):
            races = _valid_races(); races[0]["entries"][0]["past_races"][0][field] = True
            document = _document(races=races)
            with self.subTest(string=field), self.assertRaisesRegex(ValueError, f"past_race.{field} must be a string"):
                assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))
        for field, values, error in (
            ("distance", (True, 0, -1, 1.5), "past_race.distance must be a positive integer"),
            ("finish", (True, 0, -1, 1.5), "past_race.finish must be a positive integer"),
            ("popularity", (True, -1), "past_race.popularity must be a non-negative integer"),
            ("fourth_corner_position", (True, -1), "past_race.fourth_corner_position must be a non-negative integer"),
        ):
            for value in values:
                races = _valid_races(); races[0]["entries"][0]["past_races"][0][field] = value
                document = _raw_document(races)
                with self.subTest(field=field, value=value), self.assertRaisesRegex(ValueError, error):
                    assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))
        for field, error, values in (
            ("margin", "past_race.margin must be finite", (True, Decimal("1"), "1", float("nan"), float("inf"), 10**10000, -(10**10000))),
            ("weight_diff", "past_race.weight_diff must be finite", (True, Decimal("1"), "1", float("nan"), float("inf"), 10**10000, -(10**10000))),
            ("weight", "past_race.weight must be a non-negative finite number", (True, Decimal("1"), "1", -1, float("nan"), float("inf"), 10**10000)),
            ("odds", "past_race.odds must be a non-negative finite number", (True, Decimal("1"), "1", -1, float("nan"), float("inf"), 10**10000)),
        ):
            for value in values:
                races = _valid_races(); races[0]["entries"][0]["past_races"][0][field] = value
                document = _raw_document(races)
                with self.subTest(field=field, value=type(value).__name__), self.assertRaisesRegex(ValueError, error):
                    assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))
        for date_text in ("2026-08-05", "2026-08-06"):
            races = _valid_races(); races[0]["entries"][0]["past_races"][0]["race_date"] = date_text
            document = _document(races=races)
            with self.subTest(date=date_text), self.assertRaises(SimulationValidationError):
                assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))
        raw = _valid_races(); document = _document(races=raw); result = assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))
        snapshot = result[0]
        with self.assertRaises((TypeError, AttributeError)):
            snapshot.pipeline_input.odds_by_horse.__setitem__(101, 1.0)
        with self.assertRaises((TypeError, FrozenInstanceError)):
            setattr(snapshot.pipeline_input.track_conditions, "place", "Changed")
        self.assertIs(type(snapshot.input_snapshot_audit.entries), tuple)

    def test_existing_validation_remains_fail_closed(self) -> None:
        race = _race(10, scheduled_at="2026-08-05T15:40:00+09:00", entries=[_entry(101, with_past_race=True)])
        race["audit"]["is_complete"] = False
        other = _race(20, scheduled_at="2026-08-05T16:10:00+09:00", entries=[_entry(202, with_past_race=False)])
        document = _document(races=[race, other])
        application_inputs = assemble_persisted_simulation_application_inputs(document=document)
        with self.assertRaisesRegex(SimulationValidationError, "audit is not complete"):
            assemble_persisted_simulation_race_inputs(document=document, application_inputs=application_inputs)

    def test_audit_cutoff_determinism_and_validation_compatibility(self) -> None:
        paths = (
            ("audit", "captured_at"),
            ("track_conditions", "audit", "available_at"),
            ("entries", 0, "audits", "entry", "observed_at"),
            ("entries", 0, "audits", "odds", "available_at"),
            ("entries", 0, "audits", "jockey", "available_at"),
            ("entries", 1, "audits", "past_race_absence", "available_at"),
            ("entries", 0, "past_races", 0, "audit", "available_at"),
        )
        for path in paths:
            races = _valid_races()
            item: object = races[0]
            for segment in path[:-1]:
                item = item[segment]  # type: ignore[index]
            item[path[-1]] = "2026-08-05T15:31:00+09:00"  # type: ignore[index]
            document = _document(races=races)
            with self.subTest(path=path), self.assertRaises(SimulationValidationError):
                assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))
        document = _document(races=_valid_races())
        inputs = _application_inputs(document)
        first = assemble_persisted_simulation_race_inputs(document=document, application_inputs=inputs)
        second = assemble_persisted_simulation_race_inputs(document=document, application_inputs=inputs)
        self.assertEqual(first, second)
        self.assertEqual(
            [entry.audit_key for entry in first[0].input_snapshot_audit.entries],
            [entry.audit_key for entry in second[0].input_snapshot_audit.entries],
        )
        self.assertEqual(first[0].pipeline_input, second[0].pipeline_input)

    def test_race_and_generic_audit_complete_schema_matrices(self) -> None:
        for value, error in (
            ("bad", "race.audit must be an object"),
            ({"source": "official"}, "race.audit keys must exactly match the race audit schema"),
            ({"source": "official", "captured_at": "2026-08-05T12:00:00+09:00", "is_complete": True, "extra": 1}, "race.audit keys must exactly match the race audit schema"),
        ):
            races = _valid_races(); races[0]["audit"] = value
            document = _document(races=races)
            with self.subTest(race_audit=value), self.assertRaisesRegex(ValueError, error):
                assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))
        for field, values, error in (
            ("source", (True, "", " "), "race.audit.source must be a non-empty string"),
            ("captured_at", (True, "broken", "2026-08-05", "2026-08-05T12:00:00"), "race.audit.captured_at must be an ISO 8601 timezone-aware datetime"),
        ):
            for value in values:
                races = _valid_races(); races[0]["audit"][field] = value
                document = _raw_document(races)
                with self.subTest(field=field, value=type(value).__name__), self.assertRaisesRegex(ValueError, error):
                    assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))
        for value in (0, 1, "yes", None):
            races = _valid_races(); races[0]["audit"]["is_complete"] = value
            document = _document(races=races)
            with self.subTest(is_complete=value), self.assertRaisesRegex(ValueError, "race.audit.is_complete must be a boolean"):
                assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))
        for field in ("captured_at",):
            races = _valid_races(); races[0]["audit"][field] = "2026-08-05T15:31:00+09:00"
            document = _document(races=races)
            with self.assertRaises(SimulationValidationError):
                assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))
        races = _valid_races(); races[0]["audit"]["captured_at"] = "2026-08-05T03:10:00Z"
        document = _document(races=races)
        self.assertEqual(assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))[0].input_snapshot_audit.captured_at.utcoffset().total_seconds(), 0)

        for value, error in (
            ("bad", "entry.audits.entry must be an object"),
            ({"source": "x"}, "entry.audits.entry keys must exactly match the audit stamp schema"),
            ({"source": "x", "source_id": "id", "available_at": None, "observed_at": None, "x": 1}, "entry.audits.entry keys must exactly match the audit stamp schema"),
        ):
            races = _valid_races(); races[0]["entries"][0]["audits"]["entry"] = value
            document = _document(races=races)
            with self.subTest(stamp=value), self.assertRaisesRegex(ValueError, error):
                assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))
        for field, values, error in (
            ("source", (True, "", " "), "entry.audits.entry.source must be a non-empty string"),
            ("source_id", (True, "", " "), "entry.audits.entry.source_id must be a non-empty string"),
            ("available_at", (True, "bad", "2026-08-05T12:00:00"), "entry.audits.entry.available_at must be an ISO 8601 timezone-aware datetime or null"),
            ("observed_at", (True, "bad", "2026-08-05T12:00:00"), "entry.audits.entry.observed_at must be an ISO 8601 timezone-aware datetime or null"),
        ):
            for value in values:
                races = _valid_races(); races[0]["entries"][0]["audits"]["entry"][field] = value
                document = _raw_document(races)
                with self.subTest(stamp_field=field, value=type(value).__name__), self.assertRaisesRegex(ValueError, error):
                    assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))
        for available, observed in (("2026-08-05T03:00:00Z", None), (None, "2026-08-05T03:00:00Z"), ("2026-08-05T12:00:00+09:00", "2026-08-05T12:01:00+09:00")):
            races = _valid_races(); stamp = races[0]["entries"][0]["audits"]["entry"]; stamp["available_at"] = available; stamp["observed_at"] = observed
            document = _document(races=races)
            self.assertEqual(len(assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))), 2)

    def test_track_entry_and_past_schema_date_and_normal_numeric_boundaries(self) -> None:
        for mutate, error in (
            (lambda value: value.pop("place"), "race.track_conditions keys must exactly match the track conditions schema"),
            (lambda value: value.__setitem__("extra", 1), "race.track_conditions keys must exactly match the track conditions schema"),
            (lambda value: value.__setitem__("audit", "bad"), "track_conditions.audit must be an object"),
        ):
            races = _valid_races(); mutate(races[0]["track_conditions"])
            document = _document(races=races)
            with self.subTest(track_error=error), self.assertRaisesRegex(ValueError, error):
                assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))
        for mutate, error in (
            (lambda value: value.pop("jockey_name"), "entry keys must exactly match the entry schema"),
            (lambda value: value.__setitem__("extra", 1), "entry keys must exactly match the entry schema"),
            (lambda value: value.__setitem__("audits", "bad"), "entry.audits must be an object"),
            (lambda value: value["audits"].pop("odds"), "entry.audits keys must exactly match the entry audits schema"),
        ):
            races = _valid_races(); mutate(races[0]["entries"][0])
            document = _document(races=races)
            with self.subTest(entry_error=error), self.assertRaisesRegex(ValueError, error):
                assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))
        races = _valid_races(); races[0]["entries"][1]["race_entry_id"] = 101
        document = _document(races=races)
        with self.assertRaisesRegex(ValueError, "race.entries must not contain duplicate race_entry_id values"):
            assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))
        for date_text in ("20260801", "2026-W31-6", "2026/08/01", "2026-8-1", "2026-08-01T00:00:00", True):
            races = _valid_races(); races[0]["entries"][0]["past_races"][0]["race_date"] = date_text
            document = _raw_document(races)
            with self.subTest(past_date=type(date_text).__name__), self.assertRaisesRegex(ValueError, "past_race.race_date must be a canonical ISO date"):
                assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))
        races = _valid_races(); past = races[0]["entries"][0]["past_races"][0]
        past.update({"margin": -1, "weight_diff": -2, "weight": 0, "odds": 0, "popularity": 0, "fourth_corner_position": 0})
        document = _document(races=races)
        output = assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))[0].pipeline_input.horse_past_races[101][0]
        self.assertEqual((output.margin, output.weight_diff, output.weight, output.odds, output.popularity, output.fourth_corner_position), (-1.0, -2.0, 0.0, 0.0, 0, 0))

    def test_every_generic_audit_location_has_the_complete_stamp_matrix(self) -> None:
        def stamp_at(races: list[dict[str, object]], location: str) -> dict[str, object]:
            entry = races[0]["entries"][0]
            if location == "track_conditions.audit":
                return races[0]["track_conditions"]["audit"]
            if location == "past_race.audit":
                return entry["past_races"][0]["audit"]
            return entry["audits"][location]

        locations = (
            "track_conditions.audit",
            "entry",
            "jockey",
            "odds",
            "past_race_absence",
            "past_race.audit",
        )
        for location in locations:
            for replacement, error in (
                ("not-a-mapping", "must be an object"),
                ({"source": "official"}, "keys must exactly match the audit stamp schema"),
                ({**_stamp("id"), "extra": 1}, "keys must exactly match the audit stamp schema"),
            ):
                races = _valid_races()
                if location == "past_race_absence":
                    entry = races[0]["entries"][1]
                    entry["audits"]["past_race_absence"] = replacement
                else:
                    stamp_at(races, location).clear()
                    if isinstance(replacement, dict):
                        stamp_at(races, location).update(replacement)
                    else:
                        if location == "track_conditions.audit":
                            races[0]["track_conditions"]["audit"] = replacement
                        elif location == "past_race.audit":
                            races[0]["entries"][0]["past_races"][0]["audit"] = replacement
                        else:
                            races[0]["entries"][0]["audits"][location] = replacement
                document = _raw_document(races)
                expected_error = "past_race_absence is required" if location == "past_race_absence" and not isinstance(replacement, dict) else error
                with self.subTest(location=location, replacement=type(replacement).__name__), self.assertRaisesRegex(ValueError, expected_error):
                    assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))

            for field, values in (
                ("source", (True, "", " ")),
                ("source_id", (True, "", " ")),
                ("available_at", (True, "broken", "2026-08-05", "2026-08-05T12:00:00")),
                ("observed_at", (True, "broken", "2026-08-05", "2026-08-05T12:00:00")),
            ):
                for value in values:
                    races = _valid_races()
                    target = races[0]["entries"][1]["audits"]["past_race_absence"] if location == "past_race_absence" else stamp_at(races, location)
                    target[field] = value
                    document = _raw_document(races)
                    with self.subTest(location=location, field=field, value=repr(value)), self.assertRaises(ValueError):
                        assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))

            for available_at, observed_at in (
                (None, None),
                ("2026-08-05T03:00:00Z", None),
                (None, "2026-08-05T03:00:00Z"),
                ("2026-08-05T03:00:00Z", "2026-08-05T03:01:00Z"),
            ):
                races = _valid_races()
                target = races[0]["entries"][1]["audits"]["past_race_absence"] if location == "past_race_absence" else stamp_at(races, location)
                target["available_at"] = available_at
                target["observed_at"] = observed_at
                document = _raw_document(races)
                if available_at is None and observed_at is None:
                    with self.subTest(location=location, availability="none"), self.assertRaises(ValueError):
                        assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))
                else:
                    with self.subTest(location=location, availability="valid"):
                        self.assertEqual(len(assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))), 2)

    def test_track_entry_and_past_complete_schema_matrices(self) -> None:
        for field, values, error in (
            ("place", (True, "", " "), "race.track_conditions.place must be a non-empty string"),
            ("distance", (True, 0, -1, 1.5), "race.track_conditions.distance must be a positive integer"),
            ("track", (True, "", " "), "race.track_conditions.track must be a non-empty string"),
            ("track_condition", (True, "", " "), "race.track_conditions.track_condition must be a non-empty string"),
        ):
            for value in values:
                races = _valid_races(); races[0]["track_conditions"][field] = value
                document = _raw_document(races)
                with self.subTest(track_field=field, value=repr(value)), self.assertRaisesRegex(ValueError, error):
                    assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))
        for value in ([], "not-a-tuple", (), ("not-a-mapping",)):
            document = _corrupt_document(_document(races=_valid_races()), races=value)
            with self.subTest(entries_container=type(value).__name__), self.assertRaises(ValueError):
                assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))
        for value in (True, 0, -1, 1.5):
            races = _valid_races(); races[0]["entries"][0]["race_entry_id"] = value
            document = _raw_document(races)
            with self.subTest(entry_id=repr(value)), self.assertRaisesRegex(ValueError, "entry.race_entry_id must be a positive integer"):
                assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))
        for odds, expected in ((2, 2.0), (2.5, 2.5)):
            races = _valid_races(); races[0]["entries"][0]["odds"] = odds
            document = _document(races=races)
            output = assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))
            self.assertEqual(output[0].pipeline_input.odds_by_horse[101], expected)
        for past_value, error in (([], "entry.past_races must be an array"), (("not-a-mapping",), "entry.past_races must contain objects")):
            races = _valid_races(); races[0]["entries"][0]["past_races"] = past_value
            races[0]["entries"] = tuple(races[0]["entries"])
            document = _corrupt_document(_document(races=_valid_races()), races=tuple(races))
            with self.subTest(past_container=type(past_value).__name__), self.assertRaisesRegex(ValueError, error):
                assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))
        for label, mutate in (
            ("missing", lambda past: past.pop("place")),
            ("extra", lambda past: past.__setitem__("extra", 1)),
        ):
            races = _valid_races(); mutate(races[0]["entries"][0]["past_races"][0])
            document = _raw_document(races)
            with self.subTest(past_schema=label), self.assertRaisesRegex(ValueError, "past_race keys must exactly match the past race schema"):
                assemble_persisted_simulation_race_inputs(document=document, application_inputs=_application_inputs(document))

    def test_exact_error_messages_and_full_determinism(self) -> None:
        document = _document(races=_valid_races())
        inputs = _application_inputs(document)
        for supplied_document, supplied_inputs, message in (
            (object(), inputs, "document must be a PersistedSimulationRequestDocument"),
            (document, object(), "application_inputs must be a PersistedSimulationApplicationInputs"),
        ):
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, f"^{message}$"):
                assemble_persisted_simulation_race_inputs(document=supplied_document, application_inputs=supplied_inputs)
        other_path = Path(str(document.database_path))
        wrong_inputs = PersistedSimulationApplicationInputs(
            database_path=other_path,
            run_context=inputs.run_context,
            strategy_identity=inputs.strategy_identity,
            prediction_pipeline=inputs.prediction_pipeline,
            budgets_by_race_id=inputs.budgets_by_race_id,
        )
        with self.assertRaisesRegex(ValueError, "^application_inputs.database_path must be document.database_path$"):
            assemble_persisted_simulation_race_inputs(document=document, application_inputs=wrong_inputs)
        first = assemble_persisted_simulation_race_inputs(document=document, application_inputs=inputs)
        second = assemble_persisted_simulation_race_inputs(document=document, application_inputs=inputs)
        self.assertEqual(first, second)
        for initial, repeated in zip(first, second, strict=True):
            self.assertEqual(initial.race_id, repeated.race_id)
            self.assertEqual(initial.scheduled_start_at, repeated.scheduled_start_at)
            self.assertEqual(initial.pipeline_input, repeated.pipeline_input)
            self.assertEqual(initial.pipeline_input.track_conditions, repeated.pipeline_input.track_conditions)
            self.assertEqual(initial.pipeline_input.horse_past_races, repeated.pipeline_input.horse_past_races)
            self.assertEqual(initial.input_snapshot_audit.entries, repeated.input_snapshot_audit.entries)
            self.assertEqual(
                tuple(entry.audit_key for entry in initial.input_snapshot_audit.entries),
                tuple(entry.audit_key for entry in repeated.input_snapshot_audit.entries),
            )
            self.assertEqual(initial.pipeline_input.prediction_time, repeated.pipeline_input.prediction_time)
            self.assertEqual(initial.input_snapshot_audit.dataset_id, repeated.input_snapshot_audit.dataset_id)

    def test_mutable_source_is_snapshotted_and_outputs_are_immutable(self) -> None:
        races = _valid_races()
        document = _mutable_nested_document(races)
        inputs = _application_inputs(_document(races=_valid_races()))
        object.__setattr__(document, "database_path", inputs.database_path)
        self.assertIs(document.database_path, inputs.database_path)
        result = assemble_persisted_simulation_race_inputs(document=document, application_inputs=inputs)
        snapshot = result[0]
        entry = races[0]["entries"][0]
        entry["jockey_name"] = "Changed"
        entry["odds"] = 99.0
        races[0]["track_conditions"]["place"] = "Changed"
        races[0]["track_conditions"]["track_condition"] = "bad"
        past = entry["past_races"][0]
        past["race_date"] = "2020-01-01"
        past["race_name"] = "Changed"
        past["margin"] = 99.0
        past["audit"]["source_id"] = "changed"
        races.append(_race(99, scheduled_at="2026-08-05T17:00:00+09:00", entries=[_entry(999)]))
        self.assertEqual(snapshot.pipeline_input.jockey_names_by_horse[101], "Rider 101")
        self.assertEqual(snapshot.pipeline_input.odds_by_horse[101], 2.0)
        self.assertEqual(snapshot.pipeline_input.track_conditions.place, "Tokyo")
        self.assertEqual(snapshot.pipeline_input.track_conditions.track_condition, "good")
        self.assertEqual(snapshot.pipeline_input.horse_past_races[101][0].race_name, "Test race 0")
        self.assertEqual(snapshot.input_snapshot_audit.entries[3].source_id, "past-101-0")
        for mapping in (
            snapshot.pipeline_input.horse_past_races,
            snapshot.pipeline_input.jockey_names_by_horse,
            snapshot.pipeline_input.odds_by_horse,
        ):
            with self.assertRaises((AttributeError, TypeError)):
                mapping.__setitem__(1, object())
        with self.assertRaises((AttributeError, TypeError)):
            snapshot.pipeline_input.horse_past_races[101].__setitem__(0, object())
        with self.assertRaises((TypeError, FrozenInstanceError)):
            setattr(snapshot.pipeline_input.horse_past_races[101][0], "race_name", "Changed")
        with self.assertRaises((TypeError, FrozenInstanceError)):
            setattr(snapshot.pipeline_input.track_conditions, "place", "Changed")
        with self.assertRaises((AttributeError, TypeError)):
            snapshot.input_snapshot_audit.entries.__setitem__(0, object())

    def test_source_contract_has_only_the_two_allowed_exception_handlers(self) -> None:
        module = inspect.getmodule(assemble_persisted_simulation_race_inputs)
        self.assertIsNotNone(module)
        source = inspect.getsource(module)
        tree = ast.parse(source, type_comments=True)
        self.assertEqual(tree.type_ignores, [])
        self.assertNotIn("# type: ignore", source)
        imported_from_typing = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module == "typing"
            for alias in node.names
        }
        named_identifiers = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        self.assertFalse({"Any", "cast", "runtime_checkable"} & imported_from_typing)
        self.assertFalse({"Any", "cast", "runtime_checkable"} & named_identifiers)
        handled = [
            (function.name, ast.unparse(handler.type))
            for function in tree.body
            if isinstance(function, ast.FunctionDef)
            for handler in ast.walk(function)
            if isinstance(handler, ast.ExceptHandler)
        ]
        self.assertEqual(handled, [
            ("_parse_canonical_iso_date", "ValueError"),
            ("_parse_aware_datetime", "ValueError"),
        ])
        self.assertFalse(
            any(
                name in {"Exception", "BaseException", "OverflowError", "SimulationValidationError"}
                for _, name in handled
            )
        )
        for forbidden in (
            "Path.read_text", "json.loads", "sqlite3", "apply_migrations",
            "run_sqlite_persisted_simulation", "build_sqlite_persisted_simulation_run_service",
            "PersistedSimulationRunService", "repository", "subprocess",
            "logging", "print(", "argparse", "stdout", "stderr", "datetime.now",
            "datetime.utcnow", "date.today", "uuid", "os.environ", "config/settings.json", "main.py",
        ):
            self.assertNotIn(forbidden, source)
        imported_modules = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        self.assertFalse({"requests", "sqlite3", "subprocess", "logging", "argparse"} & imported_modules)
