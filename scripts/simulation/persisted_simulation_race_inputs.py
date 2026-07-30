"""Race and audit assembly boundary for persisted simulation requests."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime
import math

from scripts.models import PastRace
from scripts.prediction.prediction_pipeline import RacePredictionInput
from scripts.prediction.track_engine import RaceTrackConditions
from scripts.simulation.models import InputAuditEntry, InputSnapshotAudit, SimulationRaceInput
from scripts.simulation.persisted_simulation_application_inputs import (
    PersistedSimulationApplicationInputs,
)
from scripts.simulation.persisted_simulation_request_document import (
    PersistedSimulationRequestDocument,
)


_MAX_FINITE_FLOAT = float.fromhex("0x1.fffffffffffffp+1023")
_RACE_KEYS = frozenset({"race_id", "target_race_date", "scheduled_start_at", "information_cutoff", "audit", "track_conditions", "entries"})
_RACE_AUDIT_KEYS = frozenset({"source", "captured_at", "is_complete"})
_STAMP_KEYS = frozenset({"source", "source_id", "available_at", "observed_at"})
_TRACK_KEYS = frozenset({"place", "distance", "track", "track_condition", "audit"})
_ENTRY_KEYS = frozenset({"race_entry_id", "jockey_name", "odds", "past_races", "audits"})
_ENTRY_AUDIT_KEYS = frozenset({"entry", "jockey", "odds", "past_race_absence"})
_PAST_KEYS = frozenset({"race_date", "place", "race_name", "race_class", "distance", "track", "weather", "track_condition", "finish", "margin", "time", "weight", "weight_diff", "jockey", "popularity", "odds", "passing_order", "fourth_corner_position", "audit"})

__all__ = ["assemble_persisted_simulation_race_inputs"]


def assemble_persisted_simulation_race_inputs(
    *,
    document: PersistedSimulationRequestDocument,
    application_inputs: PersistedSimulationApplicationInputs,
) -> tuple[SimulationRaceInput, ...]:
    if type(document) is not PersistedSimulationRequestDocument:
        raise ValueError("document must be a PersistedSimulationRequestDocument")
    if type(application_inputs) is not PersistedSimulationApplicationInputs:
        raise ValueError("application_inputs must be a PersistedSimulationApplicationInputs")
    if application_inputs.database_path is not document.database_path:
        raise ValueError("application_inputs.database_path must be document.database_path")
    if type(document.races) is not tuple:
        raise ValueError("document.races must be an array")
    _prevalidate_races(document.races, application_inputs.budgets_by_race_id)
    return tuple(sorted((_assemble_race(race, application_inputs) for race in document.races), key=lambda value: (value.scheduled_start_at, value.race_id)))


def _prevalidate_races(races: tuple[Mapping[str, object], ...], budgets: Mapping[int, object]) -> None:
    race_ids: list[int] = []
    for race in races:
        if not isinstance(race, Mapping):
            raise ValueError("document.races must contain objects")
        if set(race) != _RACE_KEYS:
            raise ValueError("race keys must exactly match the race schema")
        race_id = race["race_id"]
        if type(race_id) is not int or race_id <= 0:
            raise ValueError("race.race_id must be a positive integer")
        race_ids.append(race_id)
    if len(set(race_ids)) != len(race_ids):
        raise ValueError("document.races must not contain duplicate race_id values")
    if set(race_ids) != set(budgets):
        raise ValueError("race IDs must exactly match application budget race IDs")


def _assemble_race(race: Mapping[str, object], inputs: PersistedSimulationApplicationInputs) -> SimulationRaceInput:
    race_id = race["race_id"]
    target_date = _parse_canonical_iso_date(race["target_race_date"], "race.target_race_date")
    scheduled = _parse_aware_datetime(race["scheduled_start_at"], "race.scheduled_start_at must be an ISO 8601 timezone-aware datetime")
    cutoff = _parse_aware_datetime(race["information_cutoff"], "race.information_cutoff must be an ISO 8601 timezone-aware datetime")
    if cutoff > scheduled:
        raise ValueError("race.information_cutoff must be earlier than or equal to race.scheduled_start_at")
    audit_source, captured_at, is_complete = _race_audit(race["audit"])
    track, track_entry = _track(race["track_conditions"])
    entries = _entries(race["entries"], target_date)
    audit_entries: list[InputAuditEntry] = []
    horse_past_races: dict[int, tuple[PastRace, ...]] = {}
    jockeys: dict[int, str] = {}
    odds: dict[int, float] = {}
    for entry_id, jockey, entry_odds, past_races, entry_audits in entries:
        horse_past_races[entry_id] = past_races
        jockeys[entry_id] = jockey
        odds[entry_id] = entry_odds
        audit_entries.extend(entry_audits)
    audit_entries.append(track_entry)
    pipeline_input = RacePredictionInput(
        horse_past_races=horse_past_races,
        jockey_names_by_horse=jockeys,
        track_conditions=track,
        odds_by_horse=odds,
        race_horse_count=len(entries),
        race_id=race_id,
        prediction_time=cutoff.isoformat(),
    )
    snapshot_audit = InputSnapshotAudit(
        dataset_id=inputs.run_context.dataset_id,
        source=audit_source,
        captured_at=captured_at,
        entries=tuple(audit_entries),
        is_complete=is_complete,
    )
    return SimulationRaceInput(race_id, target_date, scheduled, cutoff, pipeline_input, snapshot_audit)


def _race_audit(value: object) -> tuple[str, datetime, bool]:
    if not isinstance(value, Mapping):
        raise ValueError("race.audit must be an object")
    if set(value) != _RACE_AUDIT_KEYS:
        raise ValueError("race.audit keys must exactly match the race audit schema")
    source = _text(value["source"], "race.audit.source")
    captured = _parse_aware_datetime(value["captured_at"], "race.audit.captured_at must be an ISO 8601 timezone-aware datetime")
    if type(value["is_complete"]) is not bool:
        raise ValueError("race.audit.is_complete must be a boolean")
    return source, captured, value["is_complete"]


def _track(value: object) -> tuple[RaceTrackConditions, InputAuditEntry]:
    if not isinstance(value, Mapping):
        raise ValueError("race.track_conditions must be an object")
    if set(value) != _TRACK_KEYS:
        raise ValueError("race.track_conditions keys must exactly match the track conditions schema")
    distance = value["distance"]
    if type(distance) is not int or distance <= 0:
        raise ValueError("race.track_conditions.distance must be a positive integer")
    track = RaceTrackConditions(
        _text(value["place"], "race.track_conditions.place"), distance,
        _text(value["track"], "race.track_conditions.track"),
        _text(value["track_condition"], "race.track_conditions.track_condition"),
    )
    return track, _stamp(value["audit"], "track_conditions.audit", "track", "track", None, None)


def _entries(value: object, target_date: date) -> list[tuple[int, str, float, tuple[PastRace, ...], tuple[InputAuditEntry, ...]]]:
    if type(value) is not tuple or not value:
        raise ValueError("race.entries must be a non-empty array")
    prepared: list[tuple[int, Mapping[str, object]]] = []
    for entry in value:
        if not isinstance(entry, Mapping):
            raise ValueError("race.entries must contain objects")
        if set(entry) != _ENTRY_KEYS:
            raise ValueError("entry keys must exactly match the entry schema")
        entry_id = entry["race_entry_id"]
        if type(entry_id) is not int or entry_id <= 0:
            raise ValueError("entry.race_entry_id must be a positive integer")
        prepared.append((entry_id, entry))
    if len({entry_id for entry_id, _ in prepared}) != len(prepared):
        raise ValueError("race.entries must not contain duplicate race_entry_id values")
    return [_entry(entry_id, entry, target_date) for entry_id, entry in sorted(prepared)]


def _entry(entry_id: int, entry: Mapping[str, object], target_date: date) -> tuple[int, str, float, tuple[PastRace, ...], tuple[InputAuditEntry, ...]]:
    jockey = _text(entry["jockey_name"], "entry.jockey_name")
    odds = _positive_number(entry["odds"], "entry.odds must be a positive finite number")
    if not isinstance(entry["audits"], Mapping):
        raise ValueError("entry.audits must be an object")
    audits = entry["audits"]
    if set(audits) != _ENTRY_AUDIT_KEYS:
        raise ValueError("entry.audits keys must exactly match the entry audits schema")
    past_value = entry["past_races"]
    if type(past_value) is not tuple:
        raise ValueError("entry.past_races must be an array")
    audit_entries = [
        _stamp(audits["entry"], "entry.audits.entry", "entry", f"entry/{entry_id}", entry_id, None),
        _stamp(audits["odds"], "entry.audits.odds", "odds", f"odds/{entry_id}", entry_id, None),
        _stamp(audits["jockey"], "entry.audits.jockey", "jockey", f"jockey/{entry_id}", entry_id, None),
    ]
    if not past_value:
        if not isinstance(audits["past_race_absence"], Mapping):
            raise ValueError("entry.audits.past_race_absence is required when past_races is empty")
        audit_entries.append(_stamp(audits["past_race_absence"], "entry.audits.past_race_absence", "past_race", f"past_race/{entry_id}/none", entry_id, None))
        return entry_id, jockey, odds, (), tuple(audit_entries)
    if audits["past_race_absence"] is not None:
        raise ValueError("entry.audits.past_race_absence must be null when past_races is not empty")
    past_races: list[PastRace] = []
    for index, past in enumerate(past_value):
        past_races.append(_past_race(past, entry_id, target_date))
        audit_entries.append(_stamp(past["audit"], "past_race.audit", "past_race", f"past_race/{entry_id}/{index}", entry_id, index))
    return entry_id, jockey, odds, tuple(past_races), tuple(audit_entries)


def _past_race(value: object, entry_id: int, target_date: date) -> PastRace:
    if not isinstance(value, Mapping):
        raise ValueError("entry.past_races must contain objects")
    if set(value) != _PAST_KEYS:
        raise ValueError("past_race keys must exactly match the past race schema")
    race_date = _parse_canonical_iso_date(value["race_date"], "past_race.race_date")
    strings = {name: _string(value[name], f"past_race.{name}") for name in ("place", "race_name", "race_class", "track", "weather", "track_condition", "time", "jockey", "passing_order")}
    return PastRace(
        horse_id=entry_id, race_date=value["race_date"], place=strings["place"], race_name=strings["race_name"], race_class=strings["race_class"],
        distance=_positive_int(value["distance"], "past_race.distance"), track=strings["track"], weather=strings["weather"], track_condition=strings["track_condition"],
        finish=_positive_int(value["finish"], "past_race.finish"), margin=_finite(value["margin"], "past_race.margin must be finite"), time=strings["time"],
        weight=_nonnegative_number(value["weight"], "past_race.weight must be a non-negative finite number"), weight_diff=_finite(value["weight_diff"], "past_race.weight_diff must be finite"),
        jockey=strings["jockey"], popularity=_nonnegative_int(value["popularity"], "past_race.popularity"), odds=_nonnegative_number(value["odds"], "past_race.odds must be a non-negative finite number"),
        passing_order=strings["passing_order"], fourth_corner_position=_nonnegative_int(value["fourth_corner_position"], "past_race.fourth_corner_position"),
    )


def _stamp(value: object, path: str, input_type: str, key: str, entry_id: int | None, index: int | None) -> InputAuditEntry:
    if not isinstance(value, Mapping):
        raise ValueError(f"{path} must be an object")
    if set(value) != _STAMP_KEYS:
        raise ValueError(f"{path} keys must exactly match the audit stamp schema")
    available = _parse_optional_aware_datetime(value["available_at"], f"{path}.available_at")
    observed = _parse_optional_aware_datetime(value["observed_at"], f"{path}.observed_at")
    if available is None and observed is None:
        raise ValueError(f"{path} requires available_at or observed_at")
    return InputAuditEntry(input_type, key, _text(value["source"], f"{path}.source"), _text(value["source_id"], f"{path}.source_id"), entry_id, available, observed, index)


def _parse_canonical_iso_date(value: object, path: str) -> date:
    message = f"{path} must be a canonical ISO date"
    if type(value) is not str:
        raise ValueError(message)
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(message) from error
    if value != parsed.isoformat():
        raise ValueError(message)
    return parsed


def _parse_aware_datetime(value: object, message: str) -> datetime:
    if type(value) is not str:
        raise ValueError(message)
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    except ValueError as error:
        raise ValueError(message) from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(message)
    return parsed


def _parse_optional_aware_datetime(value: object, path: str) -> datetime | None:
    if value is None:
        return None
    return _parse_aware_datetime(
        value,
        f"{path} must be an ISO 8601 timezone-aware datetime or null",
    )


def _text(value: object, path: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{path} must be a non-empty string")
    return value


def _string(value: object, path: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{path} must be a string")
    return value


def _positive_int(value: object, path: str) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{path} must be a positive integer")
    return value


def _nonnegative_int(value: object, path: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{path} must be a non-negative integer")
    return value


def _finite(value: object, message: str) -> float:
    if type(value) is int:
        if abs(value) > _MAX_FINITE_FLOAT:
            raise ValueError(message)
        return float(value)
    if type(value) is float and math.isfinite(value):
        return value
    raise ValueError(message)


def _positive_number(value: object, message: str) -> float:
    result = _finite(value, message)
    if result <= 0:
        raise ValueError(message)
    return result


def _nonnegative_number(value: object, message: str) -> float:
    result = _finite(value, message)
    if result < 0:
        raise ValueError(message)
    return result
