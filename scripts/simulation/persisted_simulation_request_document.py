from __future__ import annotations

import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType


_DUPLICATE_KEY_ERROR = "request JSON must not contain duplicate object keys"
_NON_FINITE_NUMBER_ERROR = "request JSON must not contain non-finite numbers"


@dataclass(frozen=True)
class PersistedSimulationRequestDocument:
    schema_version: int
    source_path: Path
    database_path: Path
    run_context: Mapping[str, object]
    strategy: Mapping[str, object]
    pipeline: Mapping[str, object]
    races: tuple[Mapping[str, object], ...]
    budgets_by_race_id: Mapping[str, object]

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ValueError("schema_version must be 1")
        if not isinstance(self.source_path, Path):
            raise TypeError("source_path must be a Path")
        if not isinstance(self.database_path, Path):
            raise TypeError("database_path must be a Path")
        for field_name in (
            "run_context",
            "strategy",
            "pipeline",
            "budgets_by_race_id",
        ):
            if not isinstance(getattr(self, field_name), Mapping):
                raise TypeError(f"{field_name} must be a Mapping")
        if type(self.races) is not tuple:
            raise TypeError("races must be a tuple")
        if not all(isinstance(race, Mapping) for race in self.races):
            raise TypeError("races must contain Mapping values")

        object.__setattr__(self, "run_context", _freeze_value(self.run_context))
        object.__setattr__(self, "strategy", _freeze_value(self.strategy))
        object.__setattr__(self, "pipeline", _freeze_value(self.pipeline))
        object.__setattr__(self, "races", _freeze_value(self.races))
        object.__setattr__(
            self,
            "budgets_by_race_id",
            _freeze_value(self.budgets_by_race_id),
        )


def load_persisted_simulation_request_document(
    *,
    request_path: str | Path,
) -> PersistedSimulationRequestDocument:
    source_path = _validate_request_path(request_path)
    try:
        request_text = source_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("request file must be UTF-8") from error

    request_data = _parse_request_json(request_text)
    _validate_request_root(request_data)

    database_path_text = request_data["database_path"]
    database_path = Path(database_path_text)
    if not database_path.is_absolute():
        database_path = source_path.parent / database_path

    return PersistedSimulationRequestDocument(
        schema_version=request_data["schema_version"],
        source_path=source_path,
        database_path=database_path,
        run_context=request_data["run_context"],
        strategy=request_data["strategy"],
        pipeline=request_data["pipeline"],
        races=tuple(request_data["races"]),
        budgets_by_race_id=request_data["budgets_by_race_id"],
    )


def _validate_request_path(request_path: str | Path) -> Path:
    if not isinstance(request_path, (str, Path)):
        raise ValueError("request_path must be a non-empty path")

    request_path_text = str(request_path)
    if not request_path_text.strip() or "\x00" in request_path_text:
        raise ValueError("request_path must be a non-empty path")

    return Path(request_path)


def _parse_request_json(request_text: str) -> object:
    try:
        request_data = json.loads(
            request_text,
            object_pairs_hook=_build_object_without_duplicate_keys,
            parse_constant=_reject_non_finite_constant,
        )
    except json.JSONDecodeError as error:
        raise ValueError("request file must contain valid JSON") from error

    _validate_finite_numbers(request_data)
    return request_data


def _build_object_without_duplicate_keys(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(_DUPLICATE_KEY_ERROR)
        result[key] = value
    return result


def _reject_non_finite_constant(value: str) -> object:
    raise ValueError(_NON_FINITE_NUMBER_ERROR)


def _validate_finite_numbers(value: object) -> None:
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(_NON_FINITE_NUMBER_ERROR)
        return
    if isinstance(value, Mapping):
        for nested_value in value.values():
            _validate_finite_numbers(nested_value)
        return
    if isinstance(value, (list, tuple)):
        for nested_value in value:
            _validate_finite_numbers(nested_value)


def _validate_request_root(request_data: object) -> None:
    if type(request_data) is not dict:
        raise ValueError("request JSON root must be an object")

    expected_keys = {
        "schema_version",
        "database_path",
        "run_context",
        "strategy",
        "pipeline",
        "races",
        "budgets_by_race_id",
    }
    if set(request_data) != expected_keys:
        raise ValueError("request JSON keys must exactly match the request schema")

    if type(request_data["schema_version"]) is not int or request_data["schema_version"] != 1:
        raise ValueError("schema_version must be 1")

    database_path = request_data["database_path"]
    if (
        type(database_path) is not str
        or not database_path.strip()
        or "\x00" in database_path
    ):
        raise ValueError("database_path must be a non-empty string")

    for field_name in ("run_context", "strategy", "pipeline", "budgets_by_race_id"):
        if type(request_data[field_name]) is not dict:
            raise ValueError(f"{field_name} must be an object")

    races = request_data["races"]
    if type(races) is not list:
        raise ValueError("races must be an array")
    if any(type(race) is not dict for race in races):
        raise ValueError("races must contain objects")


def _freeze_value(value: object) -> object:
    if isinstance(value, Mapping):
        copied: dict[str, object] = {}
        for key, nested_value in value.items():
            if not isinstance(key, str):
                raise TypeError("request document mappings must have string keys")
            copied[key] = _freeze_value(nested_value)
        return MappingProxyType(copied)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_value(nested_value) for nested_value in value)
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError(_NON_FINITE_NUMBER_ERROR)
        return value
    if value is None or type(value) in (str, int, bool):
        return value
    raise TypeError("request document values must be JSON-compatible")
