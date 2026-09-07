"""Deterministic schema-v1 manifest projection for resolved daily evidence."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass
from datetime import datetime as _datetime, timezone as _timezone
import json as _json
import math as _math
import os as _os
from pathlib import Path as _Path

from scripts.prediction.allocation_policy import AllocationPolicyConfig as _AllocationPolicyConfig
from scripts.prediction.bet_strategy import (
    SelectionStyle as _SelectionStyle,
    SortCondition as _SortCondition,
    StrategyConfig as _StrategyConfig,
)
from scripts.simulation.historical_daily_evidence_resolution import (
    DailyHistoricalReplayEvidenceDisposition as _Disposition,
    DailyHistoricalReplayEvidenceResolution as _Resolution,
    DailyHistoricalReplayResolutionState as _ResolutionState,
)
from scripts.simulation.historical_replay_request_document import (
    HistoricalReplayRaceRequest as _RaceRequest,
    HistoricalReplayRequestDocument as _RequestDocument,
    load_historical_replay_request_document as _load_request_document,
)
from scripts.simulation.models import (
    SimulationRunContext as _RunContext,
    StrategyIdentity as _StrategyIdentity,
    build_strategy_identity as _build_strategy_identity,
)
from scripts.simulation.stake_allocation import BetStakeBudget as _BetStakeBudget


__all__ = (
    "DailyHistoricalReplayManifestProjection",
    "write_daily_historical_replay_manifest",
)


_NAR_ORGANIZATION = "NAR"
_NAR_SOURCE_SYSTEM = "nar_official"
_NAR_ARCHIVE_KEY = "NAR/nar_official"
_STRATEGY_NAME = "RuleBasedBetStrategy"
_ALLOCATION_POLICY_NAME = "fixed_stake_per_recommendation"
_ALLOCATION_POLICY_VERSION = "1"
_PAYOUT_BET_TYPES = frozenset({"単勝", "馬連", "ワイド", "3連複"})


def _executable_outcomes(resolution: _Resolution) -> tuple[object, ...]:
    return tuple(
        outcome
        for outcome in resolution.outcomes
        if outcome.disposition is _Disposition.EXECUTABLE
    )


@_dataclass(frozen=True, slots=True)
class DailyHistoricalReplayManifestProjection:
    resolution: _Resolution
    document: _RequestDocument | None

    def __post_init__(self) -> None:
        if type(self.resolution) is not _Resolution:
            raise ValueError("resolution must be an exact DailyHistoricalReplayEvidenceResolution")
        if self.document is not None and type(self.document) is not _RequestDocument:
            raise ValueError("document must be an exact HistoricalReplayRequestDocument or None")

        executable = _executable_outcomes(self.resolution)
        state = self.resolution.day_state
        if state is _ResolutionState.NO_EXECUTABLE_TARGETS:
            if executable or self.document is not None:
                raise ValueError("no-executable projection must not contain a document")
            return
        if not executable or self.document is None:
            raise ValueError("an executable projection requires a document")

        expected_keys = tuple(
            (outcome.snapshot_identity, outcome.internal_race_id)
            for outcome in executable
        )
        document_keys = tuple(
            (race.snapshot_identity, race.internal_race_id)
            for race in self.document.races
        )
        if document_keys != expected_keys:
            raise ValueError("document races do not exactly represent executable outcomes")
        for outcome, race in zip(executable, self.document.races, strict=True):
            if race.settlement_information_cutoff != self.resolution.settlement_information_cutoff:
                raise ValueError("document settlement cutoff disagrees with resolution")
            result_reference = outcome.result_capture_reference
            payout_reference = outcome.payout_capture_reference
            if result_reference is None or payout_reference is None:
                raise ValueError("executable outcome lost a required capture reference")
            if race.result_capture_id != result_reference.capture_id:
                raise ValueError("document result capture disagrees with resolution")
            expected_catalog = {
                bet_type: payout_reference.capture_id
                for bet_type in _PAYOUT_BET_TYPES
            }
            if dict(race.payout_capture_catalog_by_bet_type) != expected_catalog:
                raise ValueError("document payout catalog disagrees with resolution")
        if self.document.run_context.dataset_id != self.resolution.dataset_id:
            raise ValueError("document dataset disagrees with resolution")
        if set(self.document.capture_archive_paths_by_provider) != {_NAR_ARCHIVE_KEY}:
            raise ValueError("document capture archive scope must be exactly NAR/nar_official")
        budgets = tuple(self.document.budgets_by_race_id.values())
        if not budgets or any(budget != budgets[0] for budget in budgets[1:]):
            raise ValueError("document race budgets must be uniform")


def _absolute_path(value: object, name: str) -> _Path:
    if not isinstance(value, _Path):
        raise ValueError(f"{name} must be a Path")
    text = str(value)
    if not text or "\x00" in text or not value.is_absolute():
        raise ValueError(f"{name} must be an absolute Path")
    return value


def _strategy_payload(identity: object) -> dict[str, object]:
    if type(identity) is not _StrategyIdentity:
        raise ValueError("strategy_identity must be an exact StrategyIdentity")
    if identity.strategy_name != _STRATEGY_NAME:
        raise ValueError("strategy_identity strategy_name is unsupported")
    config = identity.strategy_config
    if type(config) is not _StrategyConfig:
        raise ValueError("strategy_identity must contain an exact StrategyConfig")
    if _build_strategy_identity(identity.strategy_name, config) != identity:
        raise ValueError("strategy_identity violates existing identity invariants")

    allowed = config.allowed_bet_types
    if type(allowed) is not frozenset or any(
        type(item) is not str or item not in _PAYOUT_BET_TYPES for item in allowed
    ):
        raise ValueError("strategy allowed_bet_types are unsupported")
    for value, name in (
        (config.max_bet_count, "max_bet_count"),
        (config.max_candidates, "max_candidates"),
    ):
        if type(value) is not int or value < 0:
            raise ValueError(f"strategy {name} must be a non-negative integer")
    if type(config.selection_style) is not _SelectionStyle:
        raise ValueError("strategy selection_style is unsupported")
    if type(config.sort_condition) is not _SortCondition:
        raise ValueError("strategy sort_condition is unsupported")
    if type(config.min_combination_score) is not float or not _math.isfinite(
        config.min_combination_score
    ):
        raise ValueError("strategy min_combination_score must be a finite float")

    allocation = config.allocation_policy
    if type(allocation) is not _AllocationPolicyConfig:
        raise ValueError("strategy allocation_policy is unsupported")
    if (
        allocation.policy_name != _ALLOCATION_POLICY_NAME
        or allocation.policy_version != _ALLOCATION_POLICY_VERSION
        or set(allocation.parameters) != {"stake_amount"}
    ):
        raise ValueError("strategy allocation_policy is unsupported")
    stake_amount = allocation.parameters["stake_amount"]
    if type(stake_amount) is not int or stake_amount <= 0 or stake_amount % 100 != 0:
        raise ValueError("strategy stake_amount must be a positive multiple of 100")

    return {
        "strategy_name": identity.strategy_name,
        "allowed_bet_types": sorted(allowed),
        "max_bet_count": config.max_bet_count,
        "selection_style": config.selection_style.value,
        "min_combination_score": config.min_combination_score,
        "max_candidates": config.max_candidates,
        "sort_condition": config.sort_condition.value,
        "allocation_policy": {
            "policy_name": allocation.policy_name,
            "policy_version": allocation.policy_version,
            "parameters": {"stake_amount": stake_amount},
        },
    }


def _validate_inputs(
    *,
    resolution: object,
    database_path: object,
    nar_capture_archive_path: object,
    run_context: object,
    strategy_identity: object,
    race_budget: object,
    manifest_source_path: object,
) -> tuple[_Resolution, _Path, _Path, _RunContext, _StrategyIdentity, _BetStakeBudget, _Path, dict[str, object]]:
    if type(resolution) is not _Resolution:
        raise ValueError("resolution must be an exact DailyHistoricalReplayEvidenceResolution")
    database = _absolute_path(database_path, "database_path")
    archive = _absolute_path(nar_capture_archive_path, "nar_capture_archive_path")
    source = _absolute_path(manifest_source_path, "manifest_source_path")
    if type(run_context) is not _RunContext:
        raise ValueError("run_context must be an exact SimulationRunContext")
    if resolution.dataset_id != run_context.dataset_id:
        raise ValueError("resolution dataset_id must equal run_context dataset_id")
    providers = resolution.target_set.provider_scope.providers
    if len(providers) != 1 or (
        providers[0].organization,
        providers[0].source_system,
    ) != (_NAR_ORGANIZATION, _NAR_SOURCE_SYSTEM):
        raise ValueError("resolution provider scope must be exactly NAR/nar_official")
    if type(race_budget) is not _BetStakeBudget:
        raise ValueError("race_budget must be an exact BetStakeBudget")
    strategy = _strategy_payload(strategy_identity)
    return resolution, database, archive, run_context, strategy_identity, race_budget, source, strategy


def _project_races(resolution: _Resolution) -> tuple[_RaceRequest, ...]:
    races: list[_RaceRequest] = []
    snapshot_identities: set[object] = set()
    internal_race_ids: set[int] = set()
    for outcome in _executable_outcomes(resolution):
        snapshot = outcome.snapshot_identity
        race_id = outcome.internal_race_id
        result_reference = outcome.result_capture_reference
        payout_reference = outcome.payout_capture_reference
        if snapshot is None or race_id is None or result_reference is None or payout_reference is None:
            raise ValueError("executable outcome is missing a required reference")
        target = outcome.target
        source = snapshot.source_identity
        if (
            snapshot.dataset_id != resolution.dataset_id
            or (source.organization, source.source_system, source.external_race_id)
            != (
                target.provider_identity.organization,
                target.provider_identity.source_system,
                target.external_race_id,
            )
            or (source.organization, source.source_system)
            != (_NAR_ORGANIZATION, _NAR_SOURCE_SYSTEM)
        ):
            raise ValueError("executable snapshot identity is contradictory")
        if snapshot in snapshot_identities:
            raise ValueError("executable snapshot identities must be unique")
        if race_id in internal_race_ids:
            raise ValueError("executable internal race IDs must be unique")
        if result_reference != payout_reference:
            raise ValueError("result and payout references must identify the same selected capture")
        snapshot_identities.add(snapshot)
        internal_race_ids.add(race_id)
        payout_catalog = {
            bet_type: payout_reference.capture_id
            for bet_type in sorted(_PAYOUT_BET_TYPES)
        }
        races.append(
            _RaceRequest(
                snapshot_identity=snapshot,
                internal_race_id=race_id,
                settlement_information_cutoff=resolution.settlement_information_cutoff,
                result_capture_id=result_reference.capture_id,
                payout_capture_catalog_by_bet_type=payout_catalog,
            )
        )
    return tuple(races)


def _datetime_text(value: _datetime) -> str:
    return value.astimezone(_timezone.utc).isoformat(timespec="microseconds")


def _document_payload(document: _RequestDocument, strategy: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": 1,
        "database_path": str(document.database_path),
        "capture_archives": {
            provider: str(path)
            for provider, path in document.capture_archive_paths_by_provider.items()
        },
        "run_context": {
            "run_id": document.run_context.run_id,
            "dataset_id": document.run_context.dataset_id,
            "started_at": _datetime_text(document.run_context.started_at),
            "target_commit_id": document.run_context.target_commit_id,
        },
        "strategy": strategy,
        "budgets_by_race_id": {
            str(race_id): {"total_amount": budget.total_amount}
            for race_id, budget in document.budgets_by_race_id.items()
        },
        "races": [
            {
                "snapshot_identity": {
                    "dataset_id": race.snapshot_identity.dataset_id,
                    "organization": race.snapshot_identity.source_identity.organization,
                    "source_system": race.snapshot_identity.source_identity.source_system,
                    "external_race_id": race.snapshot_identity.source_identity.external_race_id,
                    "captured_at": _datetime_text(race.snapshot_identity.captured_at),
                },
                "internal_race_id": race.internal_race_id,
                "settlement_information_cutoff": _datetime_text(
                    race.settlement_information_cutoff
                ),
                "result_capture_id": race.result_capture_id,
                "payout_capture_catalog_by_bet_type": {
                    bet_type: capture_id
                    for bet_type, capture_id in sorted(
                        race.payout_capture_catalog_by_bet_type.items()
                    )
                },
            }
            for race in document.races
        ],
    }


def _canonical_bytes(payload: dict[str, object]) -> bytes:
    return (
        _json.dumps(
            payload,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _file_identity(stat_result: _os.stat_result) -> tuple[int, int]:
    return stat_result.st_dev, stat_result.st_ino


def _cleanup_created_file(
    *,
    path: _Path,
    created_identity: tuple[int, int],
    original_error: BaseException,
) -> None:
    try:
        current = path.stat(follow_symlinks=False)
    except FileNotFoundError:
        return
    except OSError as cleanup_error:
        original_error.add_note(f"created manifest cleanup stat failed: {cleanup_error}")
        return
    if _file_identity(current) != created_identity:
        original_error.add_note("created manifest path identity changed; foreign path was not removed")
        return
    try:
        path.unlink()
    except OSError as cleanup_error:
        original_error.add_note(f"created manifest cleanup failed: {cleanup_error}")


def _publish_and_reload(
    *,
    source_path: _Path,
    expected: _RequestDocument,
    canonical_bytes: bytes,
) -> _RequestDocument:
    if not source_path.parent.is_dir():
        raise ValueError("manifest_source_path parent must be an existing directory")
    created_identity: tuple[int, int] | None = None
    try:
        with source_path.open("xb") as stream:
            created_identity = _file_identity(_os.fstat(stream.fileno()))
            written = stream.write(canonical_bytes)
            if written != len(canonical_bytes):
                raise OSError("manifest write was incomplete")
            stream.flush()
            _os.fsync(stream.fileno())
        loaded = _load_request_document(request_path=source_path)
        if source_path.read_bytes() != canonical_bytes:
            raise ValueError("written manifest bytes changed before validation")
        if loaded != expected:
            raise ValueError("reloaded manifest document differs from expected document")
        return loaded
    except BaseException as error:
        if created_identity is not None:
            _cleanup_created_file(
                path=source_path,
                created_identity=created_identity,
                original_error=error,
            )
        raise


def write_daily_historical_replay_manifest(
    *,
    resolution: _Resolution,
    database_path: _Path,
    nar_capture_archive_path: _Path,
    run_context: _RunContext,
    strategy_identity: _StrategyIdentity,
    race_budget: _BetStakeBudget,
    manifest_source_path: _Path,
) -> DailyHistoricalReplayManifestProjection:
    """Write and reload one exact executable schema-v1 projection, or no file."""

    (
        resolution,
        database_path,
        nar_capture_archive_path,
        run_context,
        strategy_identity,
        race_budget,
        manifest_source_path,
        strategy_payload,
    ) = _validate_inputs(
        resolution=resolution,
        database_path=database_path,
        nar_capture_archive_path=nar_capture_archive_path,
        run_context=run_context,
        strategy_identity=strategy_identity,
        race_budget=race_budget,
        manifest_source_path=manifest_source_path,
    )
    races = _project_races(resolution)
    if not races:
        if resolution.day_state is not _ResolutionState.NO_EXECUTABLE_TARGETS:
            raise ValueError("resolution state contradicts its executable outcomes")
        return DailyHistoricalReplayManifestProjection(resolution=resolution, document=None)

    expected = _RequestDocument(
        schema_version=1,
        source_path=manifest_source_path,
        database_path=database_path,
        capture_archive_paths_by_provider={_NAR_ARCHIVE_KEY: nar_capture_archive_path},
        run_context=run_context,
        strategy_identity=strategy_identity,
        budgets_by_race_id={race.internal_race_id: race_budget for race in races},
        races=races,
    )
    canonical_bytes = _canonical_bytes(_document_payload(expected, strategy_payload))
    loaded = _publish_and_reload(
        source_path=manifest_source_path,
        expected=expected,
        canonical_bytes=canonical_bytes,
    )
    return DailyHistoricalReplayManifestProjection(resolution=resolution, document=loaded)


if "annotations" in globals():
    del annotations
