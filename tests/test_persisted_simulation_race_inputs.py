from __future__ import annotations

import ast
from datetime import datetime
import inspect
from pathlib import Path
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


def _entry(entry_id: int, *, with_past_race: bool) -> dict[str, object]:
    past_races = [_past_race()] if with_past_race else []
    return {
        "race_entry_id": entry_id,
        "jockey_name": f"Rider {entry_id}",
        "odds": 2.0,
        "past_races": past_races,
        "audits": {
            "entry": _stamp(f"entry-{entry_id}"),
            "jockey": _stamp(f"jockey-{entry_id}"),
            "odds": _stamp(f"odds-{entry_id}"),
            "past_race_absence": None if with_past_race else _stamp(f"absence-{entry_id}"),
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


def _document(*, races: list[dict[str, object]] | None = None) -> PersistedSimulationRequestDocument:
    return PersistedSimulationRequestDocument(
        schema_version=1,
        source_path=Path("request.json"),
        database_path=Path("simulation.db"),
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
        budgets_by_race_id={"10": {"total_amount": 100}, "20": {"total_amount": 200}},
    )


class PersistedSimulationRaceInputsTest(unittest.TestCase):
    def test_formal_api_and_valid_sorted_assembly(self) -> None:
        signature = inspect.signature(assemble_persisted_simulation_race_inputs)
        self.assertEqual(tuple(signature.parameters), ("document", "application_inputs"))
        self.assertTrue(all(parameter.kind is inspect.Parameter.KEYWORD_ONLY for parameter in signature.parameters.values()))
        hints = get_type_hints(assemble_persisted_simulation_race_inputs)
        self.assertIs(hints["document"], PersistedSimulationRequestDocument)
        self.assertIs(hints["application_inputs"], PersistedSimulationApplicationInputs)
        self.assertEqual(hints["return"], tuple[SimulationRaceInput, ...])
        self.assertNotIn("assemble_persisted_simulation_race_inputs", getattr(simulation_package, "__all__", ()))

        document = _document(races=[
            _race(20, scheduled_at="2026-08-05T16:10:00+09:00", entries=[_entry(202, with_past_race=False)]),
            _race(10, scheduled_at="2026-08-05T15:40:00+09:00", entries=[_entry(102, with_past_race=True), _entry(101, with_past_race=False)]),
        ])
        application_inputs = assemble_persisted_simulation_application_inputs(document=document)
        result = assemble_persisted_simulation_race_inputs(document=document, application_inputs=application_inputs)

        self.assertEqual([item.race_id for item in result], [10, 20])
        self.assertIs(type(result[0]), SimulationRaceInput)
        self.assertEqual(list(result[0].pipeline_input.horse_past_races), [101, 102])
        self.assertEqual(
            type(result[0].pipeline_input.horse_past_races[102][0]).__name__,
            "PastRaceSnapshot",
        )
        self.assertEqual(result[0].pipeline_input.horse_past_races[102][0].horse_id, 102)
        self.assertEqual(
            [entry.audit_key for entry in result[0].input_snapshot_audit.entries],
            ["entry/101", "odds/101", "jockey/101", "past_race/101/none", "entry/102", "odds/102", "jockey/102", "past_race/102/0", "track"],
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

    def test_existing_validation_remains_fail_closed(self) -> None:
        race = _race(10, scheduled_at="2026-08-05T15:40:00+09:00", entries=[_entry(101, with_past_race=True)])
        race["audit"]["is_complete"] = False
        other = _race(20, scheduled_at="2026-08-05T16:10:00+09:00", entries=[_entry(202, with_past_race=False)])
        document = _document(races=[race, other])
        application_inputs = assemble_persisted_simulation_application_inputs(document=document)
        with self.assertRaisesRegex(SimulationValidationError, "audit is not complete"):
            assemble_persisted_simulation_race_inputs(document=document, application_inputs=application_inputs)

    def test_source_contract_has_only_the_two_allowed_exception_handlers(self) -> None:
        module = inspect.getmodule(assemble_persisted_simulation_race_inputs)
        self.assertIsNotNone(module)
        source = inspect.getsource(module)
        tree = ast.parse(source, type_comments=True)
        self.assertEqual(tree.type_ignores, [])
        self.assertNotIn("# type: ignore", source)
        handlers = [node for node in ast.walk(tree) if isinstance(node, ast.ExceptHandler)]
        self.assertEqual(len(handlers), 2)
        owners = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
            and any(isinstance(child, ast.ExceptHandler) for child in ast.walk(node))
        }
        self.assertEqual(owners, {"_parse_canonical_iso_date", "_parse_aware_datetime"})
        self.assertNotIn("sqlite3", source)
        self.assertNotIn("json.loads", source)
        self.assertNotIn("datetime.now", source)
