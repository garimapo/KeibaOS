"""Strict immutable request document for exact archived historical replay."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
import json
import math
from pathlib import Path
import re
from types import MappingProxyType
from typing import Callable, TypeVar

from scripts.prediction.allocation_policy import AllocationPolicyConfig
from scripts.prediction.bet_strategy import SelectionStyle, SortCondition, StrategyConfig
from scripts.simulation.historical_input_snapshots import (
    HistoricalInputSnapshotIdentity,
    HistoricalSourceIdentity,
)
from scripts.simulation.models import SimulationRunContext, StrategyIdentity, build_strategy_identity
from scripts.simulation.stake_allocation import BetStakeBudget


__all__ = (
    "HistoricalReplayRequestValidationError",
    "HistoricalReplayRaceRequest",
    "HistoricalReplayRequestDocument",
    "load_historical_replay_request_document",
)


_ROOT_KEYS = frozenset(
    {
        "schema_version",
        "database_path",
        "capture_archives",
        "run_context",
        "strategy",
        "budgets_by_race_id",
        "races",
    }
)
_RUN_CONTEXT_KEYS = frozenset({"run_id", "dataset_id", "started_at", "target_commit_id"})
_STRATEGY_KEYS = frozenset(
    {
        "strategy_name",
        "allowed_bet_types",
        "max_bet_count",
        "selection_style",
        "min_combination_score",
        "max_candidates",
        "sort_condition",
        "allocation_policy",
    }
)
_ALLOCATION_POLICY_KEYS = frozenset({"policy_name", "policy_version", "parameters"})
_FIXED_STAKE_KEYS = frozenset({"stake_amount"})
_BUDGET_KEYS = frozenset({"total_amount"})
_RACE_KEYS = frozenset(
    {
        "snapshot_identity",
        "internal_race_id",
        "settlement_information_cutoff",
        "result_capture_id",
        "payout_capture_catalog_by_bet_type",
    }
)
_SNAPSHOT_IDENTITY_KEYS = frozenset(
    {"dataset_id", "organization", "source_system", "external_race_id", "captured_at"}
)
_SUPPORTED_BET_TYPES = frozenset({"単勝", "馬連", "ワイド", "3連複"})
_PROVIDER_BY_SOURCE = {
    ("JRA", "jra_official"): "JRA/jra_official",
    ("NAR", "nar_official"): "NAR/nar_official",
}
_SUPPORTED_PROVIDER_KEYS = frozenset(_PROVIDER_BY_SOURCE.values())
_CANONICAL_RACE_ID = re.compile(r"[1-9][0-9]*\Z")
_MAX_FINITE_FLOAT = float.fromhex("0x1.fffffffffffffp+1023")
_T = TypeVar("_T")


class HistoricalReplayRequestValidationError(ValueError):
    """Request JSON, schema, or immutable request-domain validation failed."""


def _fail(message: str) -> HistoricalReplayRequestValidationError:
    return HistoricalReplayRequestValidationError(message)


def _non_empty_text(value: object, name: str) -> str:
    if type(value) is not str or not value.strip():
        raise _fail(f"{name} must be a non-empty string")
    return value


def _aware_datetime(value: object, name: str) -> datetime:
    if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
        raise _fail(f"{name} must be a timezone-aware datetime")
    return value


def _provider_key(identity: HistoricalInputSnapshotIdentity) -> str:
    pair = (identity.source_identity.organization, identity.source_identity.source_system)
    try:
        return _PROVIDER_BY_SOURCE[pair]
    except KeyError as error:
        raise _fail("snapshot identity provider pair is unsupported") from error


@dataclass(frozen=True, slots=True)
class HistoricalReplayRaceRequest:
    snapshot_identity: HistoricalInputSnapshotIdentity
    internal_race_id: int
    settlement_information_cutoff: datetime
    result_capture_id: str
    payout_capture_catalog_by_bet_type: Mapping[str, str]

    def __post_init__(self) -> None:
        if type(self.snapshot_identity) is not HistoricalInputSnapshotIdentity:
            raise _fail("snapshot_identity must be HistoricalInputSnapshotIdentity")
        _provider_key(self.snapshot_identity)
        if type(self.internal_race_id) is not int or self.internal_race_id <= 0:
            raise _fail("internal_race_id must be a positive integer")
        _aware_datetime(self.settlement_information_cutoff, "settlement_information_cutoff")
        _non_empty_text(self.result_capture_id, "result_capture_id")
        if isinstance(self.payout_capture_catalog_by_bet_type, type) or not isinstance(
            self.payout_capture_catalog_by_bet_type, Mapping
        ):
            raise _fail("payout_capture_catalog_by_bet_type must be a Mapping")
        copied: dict[str, str] = {}
        for bet_type, capture_id in self.payout_capture_catalog_by_bet_type.items():
            if type(bet_type) is not str or bet_type not in _SUPPORTED_BET_TYPES:
                raise _fail("payout catalog key is unsupported")
            copied[bet_type] = _non_empty_text(capture_id, "payout capture ID")
        object.__setattr__(self, "payout_capture_catalog_by_bet_type", MappingProxyType(copied))


@dataclass(frozen=True, slots=True)
class HistoricalReplayRequestDocument:
    schema_version: int
    source_path: Path
    database_path: Path
    capture_archive_paths_by_provider: Mapping[str, Path]
    run_context: SimulationRunContext
    strategy_identity: StrategyIdentity
    budgets_by_race_id: Mapping[int, BetStakeBudget]
    races: tuple[HistoricalReplayRaceRequest, ...]

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise _fail("schema_version must be 1")
        if not isinstance(self.source_path, Path):
            raise _fail("source_path must be a Path")
        if not isinstance(self.database_path, Path):
            raise _fail("database_path must be a Path")
        if isinstance(self.capture_archive_paths_by_provider, type) or not isinstance(
            self.capture_archive_paths_by_provider, Mapping
        ):
            raise _fail("capture_archive_paths_by_provider must be a Mapping")
        archives: dict[str, Path] = {}
        for provider, path in self.capture_archive_paths_by_provider.items():
            if type(provider) is not str or provider not in _SUPPORTED_PROVIDER_KEYS:
                raise _fail("capture archive provider is unsupported")
            if not isinstance(path, Path):
                raise _fail("capture archive path must be a Path")
            archives[provider] = path
        if not archives:
            raise _fail("at least one capture archive is required")
        if type(self.run_context) is not SimulationRunContext:
            raise _fail("run_context must be SimulationRunContext")
        if type(self.strategy_identity) is not StrategyIdentity:
            raise _fail("strategy_identity must be StrategyIdentity")
        if isinstance(self.budgets_by_race_id, type) or not isinstance(self.budgets_by_race_id, Mapping):
            raise _fail("budgets_by_race_id must be a Mapping")
        budgets: dict[int, BetStakeBudget] = {}
        for race_id, budget in self.budgets_by_race_id.items():
            if type(race_id) is not int or race_id <= 0:
                raise _fail("budget race IDs must be positive integers")
            if type(budget) is not BetStakeBudget:
                raise _fail("budget values must be BetStakeBudget")
            budgets[race_id] = budget
        if type(self.races) is not tuple or not self.races:
            raise _fail("races must be a non-empty tuple")
        if any(type(race) is not HistoricalReplayRaceRequest for race in self.races):
            raise _fail("races must contain HistoricalReplayRaceRequest values")

        snapshot_identities = tuple(race.snapshot_identity for race in self.races)
        if len(set(snapshot_identities)) != len(snapshot_identities):
            raise _fail("snapshot identities must be unique")
        race_ids = tuple(race.internal_race_id for race in self.races)
        if len(set(race_ids)) != len(race_ids):
            raise _fail("internal race IDs must be unique")
        if set(budgets) != set(race_ids):
            raise _fail("budget race IDs must exactly cover manifest race IDs")
        represented_providers: set[str] = set()
        for race in self.races:
            if race.snapshot_identity.dataset_id != self.run_context.dataset_id:
                raise _fail("snapshot dataset_id must equal run_context.dataset_id")
            represented_providers.add(_provider_key(race.snapshot_identity))
        if not represented_providers.issubset(archives):
            raise _fail("every represented provider must have a capture archive")

        object.__setattr__(self, "capture_archive_paths_by_provider", MappingProxyType(archives))
        object.__setattr__(self, "budgets_by_race_id", MappingProxyType(dict(sorted(budgets.items()))))


def load_historical_replay_request_document(
    *,
    request_path: str | Path,
) -> HistoricalReplayRequestDocument:
    """Read one UTF-8 manifest and construct exact immutable replay request values."""

    source_path = _request_path(request_path)
    try:
        request_text = source_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise _fail("request file must be UTF-8") from error

    root = _parse_json(request_text)
    _exact_object(root, _ROOT_KEYS, "request root")
    if type(root["schema_version"]) is not int or root["schema_version"] != 1:
        raise _fail("schema_version must be 1")

    database_path = _anchored_path(root["database_path"], source_path, "database_path")
    archive_paths = _capture_archive_paths(root["capture_archives"], source_path)
    run_context = _run_context(root["run_context"])
    strategy_identity = _strategy_identity(root["strategy"])
    budgets = _budgets(root["budgets_by_race_id"])
    races = _races(root["races"])
    return HistoricalReplayRequestDocument(
        schema_version=1,
        source_path=source_path,
        database_path=database_path,
        capture_archive_paths_by_provider=archive_paths,
        run_context=run_context,
        strategy_identity=strategy_identity,
        budgets_by_race_id=budgets,
        races=races,
    )


def _request_path(value: object) -> Path:
    if not isinstance(value, (str, Path)):
        raise _fail("request_path must be a non-empty path")
    text = str(value)
    if not text.strip() or "\x00" in text:
        raise _fail("request_path must be a non-empty path")
    return Path(value)


def _parse_json(text: str) -> dict[str, object]:
    try:
        value = json.loads(
            text,
            object_pairs_hook=_object_without_duplicate_keys,
            parse_constant=_reject_non_finite_constant,
        )
    except HistoricalReplayRequestValidationError:
        raise
    except json.JSONDecodeError as error:
        raise _fail("request file must contain valid JSON") from error
    _finite_numbers(value)
    if type(value) is not dict:
        raise _fail("request root must be an object")
    return value


def _object_without_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _fail("request JSON must not contain duplicate object keys")
        result[key] = value
    return result


def _reject_non_finite_constant(value: str) -> object:
    raise _fail("request JSON must not contain non-finite numbers")


def _finite_numbers(value: object) -> None:
    if type(value) is float:
        if not math.isfinite(value):
            raise _fail("request JSON must not contain non-finite numbers")
        return
    if type(value) is dict:
        for nested in value.values():
            _finite_numbers(nested)
        return
    if type(value) is list:
        for nested in value:
            _finite_numbers(nested)


def _exact_object(value: object, keys: frozenset[str], name: str) -> dict[str, object]:
    if type(value) is not dict or set(value) != keys:
        raise _fail(f"{name} keys must exactly match its schema")
    return value


def _anchored_path(value: object, source_path: Path, name: str) -> Path:
    text = _non_empty_text(value, name)
    if "\x00" in text:
        raise _fail(f"{name} must not contain NUL")
    path = Path(text)
    return path if path.is_absolute() else source_path.parent / path


def _capture_archive_paths(value: object, source_path: Path) -> Mapping[str, Path]:
    if type(value) is not dict or not value or not set(value).issubset(_SUPPORTED_PROVIDER_KEYS):
        raise _fail("capture_archives keys are invalid")
    return {
        provider: _anchored_path(path, source_path, f"capture_archives.{provider}")
        for provider, path in value.items()
    }


def _parsed_aware_datetime(value: object, name: str) -> datetime:
    if type(value) is not str:
        raise _fail(f"{name} must be an ISO-8601 timezone-aware datetime")
    source = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(source)
    except ValueError as error:
        raise _fail(f"{name} must be an ISO-8601 timezone-aware datetime") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise _fail(f"{name} must be an ISO-8601 timezone-aware datetime")
    return parsed


def _construct(factory: Callable[[], _T], name: str) -> _T:
    try:
        return factory()
    except HistoricalReplayRequestValidationError:
        raise
    except (TypeError, ValueError, OverflowError) as error:
        raise _fail(f"{name} is invalid") from error


def _run_context(value: object) -> SimulationRunContext:
    data = _exact_object(value, _RUN_CONTEXT_KEYS, "run_context")
    run_id = _non_empty_text(data["run_id"], "run_context.run_id")
    dataset_id = _non_empty_text(data["dataset_id"], "run_context.dataset_id")
    target_commit_id = _non_empty_text(data["target_commit_id"], "run_context.target_commit_id")
    started_at = _parsed_aware_datetime(data["started_at"], "run_context.started_at")
    return _construct(
        lambda: SimulationRunContext(
            run_id=run_id,
            dataset_id=dataset_id,
            started_at=started_at,
            target_commit_id=target_commit_id,
        ),
        "run_context",
    )


def _strategy_identity(value: object) -> StrategyIdentity:
    data = _exact_object(value, _STRATEGY_KEYS, "strategy")
    if data["strategy_name"] != "RuleBasedBetStrategy":
        raise _fail("strategy.strategy_name is unsupported")
    allowed = data["allowed_bet_types"]
    if type(allowed) is not list:
        raise _fail("strategy.allowed_bet_types must be an array")
    if any(type(item) is not str or item not in _SUPPORTED_BET_TYPES for item in allowed):
        raise _fail("strategy.allowed_bet_types contains an unsupported value")
    if len(set(allowed)) != len(allowed):
        raise _fail("strategy.allowed_bet_types must be unique")
    max_bet_count = _non_negative_int(data["max_bet_count"], "strategy.max_bet_count")
    max_candidates = _non_negative_int(data["max_candidates"], "strategy.max_candidates")
    try:
        selection_style = SelectionStyle(data["selection_style"])
        sort_condition = SortCondition(data["sort_condition"])
    except (TypeError, ValueError) as error:
        raise _fail("strategy enum value is unsupported") from error
    score = _finite_score(data["min_combination_score"])
    allocation = _allocation_policy(data["allocation_policy"])
    config = _construct(
        lambda: StrategyConfig(
            allowed_bet_types=frozenset(allowed),
            max_bet_count=max_bet_count,
            selection_style=selection_style,
            min_combination_score=score,
            max_candidates=max_candidates,
            sort_condition=sort_condition,
            allocation_policy=allocation,
        ),
        "strategy configuration",
    )
    return _construct(
        lambda: build_strategy_identity("RuleBasedBetStrategy", config),
        "strategy identity",
    )


def _non_negative_int(value: object, name: str) -> int:
    if type(value) is not int or value < 0:
        raise _fail(f"{name} must be a non-negative integer")
    return value


def _finite_score(value: object) -> float:
    if type(value) is int:
        if abs(value) > _MAX_FINITE_FLOAT:
            raise _fail("strategy.min_combination_score must be finite")
        return float(value)
    if type(value) is float and math.isfinite(value):
        return value
    raise _fail("strategy.min_combination_score must be finite")


def _allocation_policy(value: object) -> AllocationPolicyConfig:
    data = _exact_object(value, _ALLOCATION_POLICY_KEYS, "strategy.allocation_policy")
    if data["policy_name"] != "fixed_stake_per_recommendation":
        raise _fail("allocation policy name is unsupported")
    if type(data["policy_version"]) is not str or data["policy_version"] != "1":
        raise _fail("allocation policy version is unsupported")
    parameters = _exact_object(data["parameters"], _FIXED_STAKE_KEYS, "allocation parameters")
    stake = parameters["stake_amount"]
    if type(stake) is not int or stake <= 0 or stake % 100 != 0:
        raise _fail("stake_amount must be a positive multiple of 100")
    return _construct(
        lambda: AllocationPolicyConfig(
            policy_name="fixed_stake_per_recommendation",
            policy_version="1",
            parameters={"stake_amount": stake},
        ),
        "allocation policy",
    )


def _budgets(value: object) -> Mapping[int, BetStakeBudget]:
    if type(value) is not dict:
        raise _fail("budgets_by_race_id must be an object")
    result: dict[int, BetStakeBudget] = {}
    for race_id_text, raw_budget in value.items():
        if type(race_id_text) is not str or _CANONICAL_RACE_ID.fullmatch(race_id_text) is None:
            raise _fail("budget race IDs must be canonical positive integer strings")
        data = _exact_object(raw_budget, _BUDGET_KEYS, "budget")
        total = data["total_amount"]
        if type(total) is not int or total < 0 or total % 100 != 0:
            raise _fail("budget total_amount must be a non-negative multiple of 100")
        result[int(race_id_text)] = _construct(
            lambda total=total: BetStakeBudget(total_amount=total),
            "budget",
        )
    return result


def _races(value: object) -> tuple[HistoricalReplayRaceRequest, ...]:
    if type(value) is not list or not value:
        raise _fail("races must be a non-empty array")
    return tuple(_race(item) for item in value)


def _race(value: object) -> HistoricalReplayRaceRequest:
    data = _exact_object(value, _RACE_KEYS, "race")
    snapshot_identity = _snapshot_identity(data["snapshot_identity"])
    race_id = data["internal_race_id"]
    if type(race_id) is not int or race_id <= 0:
        raise _fail("internal_race_id must be a positive integer")
    cutoff = _parsed_aware_datetime(
        data["settlement_information_cutoff"],
        "settlement_information_cutoff",
    )
    result_capture_id = _non_empty_text(data["result_capture_id"], "result_capture_id")
    catalog = _payout_catalog(data["payout_capture_catalog_by_bet_type"])
    return HistoricalReplayRaceRequest(
        snapshot_identity=snapshot_identity,
        internal_race_id=race_id,
        settlement_information_cutoff=cutoff,
        result_capture_id=result_capture_id,
        payout_capture_catalog_by_bet_type=catalog,
    )


def _snapshot_identity(value: object) -> HistoricalInputSnapshotIdentity:
    data = _exact_object(value, _SNAPSHOT_IDENTITY_KEYS, "snapshot_identity")
    dataset_id = _non_empty_text(data["dataset_id"], "snapshot_identity.dataset_id")
    organization = _non_empty_text(data["organization"], "snapshot_identity.organization")
    source_system = _non_empty_text(data["source_system"], "snapshot_identity.source_system")
    external_race_id = _non_empty_text(data["external_race_id"], "snapshot_identity.external_race_id")
    if (organization, source_system) not in _PROVIDER_BY_SOURCE:
        raise _fail("snapshot identity provider pair is unsupported")
    captured_at = _parsed_aware_datetime(data["captured_at"], "snapshot_identity.captured_at")
    source_identity = _construct(
        lambda: HistoricalSourceIdentity(
            organization=organization,
            source_system=source_system,
            external_race_id=external_race_id,
            source_url=None,
        ),
        "snapshot source identity",
    )
    return _construct(
        lambda: HistoricalInputSnapshotIdentity(
            dataset_id=dataset_id,
            source_identity=source_identity,
            captured_at=captured_at,
        ),
        "snapshot identity",
    )


def _payout_catalog(value: object) -> Mapping[str, str]:
    if type(value) is not dict:
        raise _fail("payout_capture_catalog_by_bet_type must be an object")
    result: dict[str, str] = {}
    for bet_type, capture_id in value.items():
        if type(bet_type) is not str or bet_type not in _SUPPORTED_BET_TYPES:
            raise _fail("payout catalog key is unsupported")
        result[bet_type] = _non_empty_text(capture_id, "payout capture ID")
    return result
