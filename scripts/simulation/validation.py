"""シミュレーション入力の時点監査と Fail Closed 検証。"""

from __future__ import annotations

from datetime import date
from typing import AbstractSet

from .models import SimulationRaceInput


REQUIRED_INPUT_TYPES = frozenset({"entry", "odds", "past_race", "jockey", "track"})


def _entry_key(race_entry_id: int) -> str:
    return f"entry/{race_entry_id}"


def _odds_key(race_entry_id: int) -> str:
    return f"odds/{race_entry_id}"


def _jockey_key(race_entry_id: int) -> str:
    return f"jockey/{race_entry_id}"


def _past_race_key(race_entry_id: int, index: int | None) -> str:
    suffix = "none" if index is None else str(index)
    return f"past_race/{race_entry_id}/{suffix}"


class SimulationValidationError(ValueError):
    """監査不能または未来情報を含むシミュレーション入力を拒否する例外。"""

    def __init__(self, race_id: int, input_identifier: str, reason: str) -> None:
        self.race_id = race_id
        self.input_identifier = input_identifier
        self.reason = reason
        super().__init__(f"simulation validation failed: race_id={race_id}, input={input_identifier}, reason={reason}")


def _fail(race_input: SimulationRaceInput, identifier: str, reason: str) -> None:
    raise SimulationValidationError(race_input.race_id, identifier, reason)


def _race_date(value: str, race_input: SimulationRaceInput, identifier: str) -> date:
    try:
        return date.fromisoformat(value.replace("/", "-"))
    except (AttributeError, ValueError):
        _fail(race_input, identifier, "past_race.race_date is invalid")
        raise AssertionError("unreachable")


def validate_simulation_race_input(
    race_input: SimulationRaceInput,
    *,
    required_input_types: AbstractSet[str] = REQUIRED_INPUT_TYPES,
) -> None:
    """時点監査、必須カテゴリ、過去走日付を Fail Closed で検証する。"""
    audit = race_input.input_snapshot_audit
    cutoff = race_input.information_cutoff
    if race_input.race_id != race_input.pipeline_input.race_id:
        _fail(race_input, "pipeline_input.race_id", "pipeline_input.race_id does not match race_id")
    if audit.captured_at > cutoff:
        _fail(race_input, "audit.captured_at", "captured_at is after information_cutoff")
    if not audit.is_complete:
        _fail(race_input, "input_snapshot_audit", "audit is not complete")
    present = {entry.input_type for entry in audit.entries}
    missing = sorted(set(required_input_types) - present)
    if missing:
        _fail(race_input, "input_snapshot_audit", f"required input categories are missing: {', '.join(missing)}")
    expected: dict[str, tuple[str, int, int | None]] = {}
    snapshot = race_input.pipeline_input
    for race_entry_id, past_races in snapshot.horse_past_races.items():
        expected[_entry_key(race_entry_id)] = ("entry", race_entry_id, None)
        expected[_odds_key(race_entry_id)] = ("odds", race_entry_id, None)
        expected[_jockey_key(race_entry_id)] = ("jockey", race_entry_id, None)
        if not past_races:
            expected[_past_race_key(race_entry_id, None)] = ("past_race", race_entry_id, None)
        for index, past_race in enumerate(past_races):
            key = _past_race_key(race_entry_id, index)
            expected[key] = ("past_race", race_entry_id, index)
            identifier = key
            if _race_date(past_race.race_date, race_input, identifier) >= race_input.target_race_date:
                _fail(race_input, identifier, "past_race.race_date must be before target_race_date")
    expected["track"] = ("track", None, None)

    actual = {entry.audit_key: entry for entry in audit.entries}
    missing_keys = sorted(set(expected) - set(actual))
    if missing_keys:
        _fail(race_input, missing_keys[0], "required pipeline_input audit entry is missing")
    unknown_keys = sorted(set(actual) - set(expected))
    if unknown_keys:
        _fail(race_input, unknown_keys[0], "audit entry does not map to pipeline_input")
    for key, entry in actual.items():
        expected_type, expected_race_entry_id, expected_index = expected[key]
        if (entry.input_type, entry.race_entry_id, entry.past_race_index) != (
            expected_type,
            expected_race_entry_id,
            expected_index,
        ):
            _fail(race_input, key, "audit key metadata does not match pipeline_input")
        for field_name, value in (("available_at", entry.available_at), ("observed_at", entry.observed_at)):
            if value is not None and value > cutoff:
                _fail(race_input, key, f"{field_name} is after information_cutoff")
