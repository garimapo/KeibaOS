"""Deterministic whole-day NAR replay orchestration over frozen evidence."""

from __future__ import annotations

from dataclasses import InitVar as _InitVar, dataclass as _dataclass, field as _field
from datetime import datetime as _datetime, timezone as _timezone
from enum import StrEnum as _StrEnum
from hashlib import sha256 as _sha256
import json as _json
import os as _os
from pathlib import Path as _Path
import re as _re
import sqlite3 as _sqlite3
import stat as _stat
from unicodedata import normalize as _normalize

from scripts.simulation.historical_daily_evidence_resolution import (
    DailyHistoricalReplayCaptureReference as _CaptureReference,
    DailyHistoricalReplayEvidenceDisposition as _Disposition,
    DailyHistoricalReplayEvidenceResolution as _Resolution,
    DailyHistoricalReplayResolutionState as _ResolutionState,
)
from scripts.simulation.historical_daily_targets import (
    DailyHistoricalReplayTargetSet as _TargetSet,
)
from scripts.simulation.historical_daily_replay_manifest_projection import (
    DailyHistoricalReplayManifestProjection as _ManifestProjection,
    write_daily_historical_replay_manifest as _write_manifest,
)
from scripts.simulation.models import (
    SimulationRunContext as _RunContext,
    SimulationSummary as _SimulationSummary,
    StrategyIdentity as _StrategyIdentity,
)
from scripts.simulation.nar_daily_target_live_acquisition import (
    NARDailyTargetLiveAcquisitionResult as _AcquisitionResult,
)
from scripts.simulation.sqlite_historical_replay_application import (
    run_sqlite_historical_replay as _run_replay,
)
from scripts.simulation.sqlite_nar_daily_evidence_resolver import (
    resolve_sqlite_nar_daily_evidence as _resolve_evidence,
)
from scripts.simulation.stake_allocation import BetStakeBudget as _BetStakeBudget


__all__ = (
    "NARDailyReplayExecutionState",
    "NARDailyReplayOrchestrationResult",
    "compute_nar_daily_replay_orchestration_audit_sha256",
    "run_nar_daily_replay",
)


_AUDIT_VERSION = "nar-daily-replay-orchestration-audit-v1"
_NAR_PROVIDER = ("NAR", "nar_official")
_SHA256 = _re.compile(r"[0-9a-f]{64}\Z")


class NARDailyReplayExecutionState(_StrEnum):
    FULL_DAY_REPLAY_COMPLETED = "FULL_DAY_REPLAY_COMPLETED"
    NOT_RUN_PARTIAL_RESOLUTION = "NOT_RUN_PARTIAL_RESOLUTION"
    NOT_RUN_NO_EXECUTABLE_TARGETS = "NOT_RUN_NO_EXECUTABLE_TARGETS"


@_dataclass(frozen=True, slots=True)
class _AuditInputs:
    database_path: _Path
    nar_settlement_capture_archive_path: _Path
    run_context: _RunContext
    strategy_identity: _StrategyIdentity
    race_budget: _BetStakeBudget
    manifest_source_path: _Path


def _required_text(value: object, name: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise ValueError(f"{name} must be nonempty exact text")
    if value != _normalize("NFC", value):
        raise ValueError(f"{name} must be NFC text")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ValueError(f"{name} must not contain control characters")
    return value


def _absolute_path(value: object, name: str) -> _Path:
    if not isinstance(value, _Path):
        raise ValueError(f"{name} must be a Path")
    text = str(value)
    if not text or "\x00" in text or not value.is_absolute():
        raise ValueError(f"{name} must be an absolute nonempty NUL-free Path")
    if text != _normalize("NFC", text):
        raise ValueError(f"{name} must have NFC path text")
    return value


def _aware_datetime(value: object, name: str) -> _datetime:
    if type(value) is not _datetime or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be an exact aware datetime")
    return value


def _datetime_text(value: _datetime) -> str:
    return value.astimezone(_timezone.utc).isoformat(timespec="microseconds")


def _digest(value: object, name: str) -> str:
    if type(value) is not str or _SHA256.fullmatch(value) is None:
        raise ValueError(f"{name} must be lowercase SHA-256")
    return value


def _validate_acquisition_result(value: object) -> _AcquisitionResult:
    if type(value) is not _AcquisitionResult:
        raise ValueError("acquisition_result must be an exact NARDailyTargetLiveAcquisitionResult")
    target_set = value.target_set
    if type(target_set) is not _TargetSet:
        raise ValueError("acquisition_result must contain an exact target set")
    rebuilt_target_set = _TargetSet(
        target_date=target_set.target_date,
        provider_scope=target_set.provider_scope,
        target_races=target_set.target_races,
        completeness_evidence=target_set.completeness_evidence,
    )
    if rebuilt_target_set != target_set:
        raise ValueError("acquisition target-set content identity is contradictory")
    rebuilt = _AcquisitionResult(
        target_date=value.target_date,
        homepage_supplier_capture_id=value.homepage_supplier_capture_id,
        monthly_root_supplier_capture_id=value.monthly_root_supplier_capture_id,
        locator_script_supplier_capture_id=value.locator_script_supplier_capture_id,
        supplier_evidence_identity=value.supplier_evidence_identity,
        monthly_capture_id=value.monthly_capture_id,
        race_list_capture_ids=value.race_list_capture_ids,
        target_set=target_set,
    )
    if rebuilt != value:
        raise ValueError("acquisition result violates its immutable domain invariants")
    return value


def _require_connection_path_binding(
    connection: _sqlite3.Connection,
    expected_path: _Path,
    name: str,
) -> None:
    """Prove one caller-owned SQLite main binding without reading application data."""

    if type(connection) is not _sqlite3.Connection:
        raise ValueError(f"{name} connection must be an exact sqlite3.Connection")
    expected_path = _absolute_path(expected_path, f"{name} path")
    if connection.in_transaction:
        raise ValueError(f"{name} connection must be transaction-free")
    if not expected_path.exists() or not expected_path.is_file():
        raise ValueError(f"{name} path must identify an existing filesystem file")

    rows = tuple(connection.execute("PRAGMA database_list"))
    if connection.in_transaction:
        raise ValueError(f"{name} binding query changed transaction state")
    if len(rows) != 1:
        raise ValueError(f"{name} connection must contain only one main database")
    row = rows[0]
    if type(row) not in (tuple, _sqlite3.Row) or len(row) != 3:
        raise ValueError(f"{name} database binding row has an unexpected shape")
    sequence, schema_name, filename = row
    if type(sequence) is not int or sequence != 0 or schema_name != "main":
        raise ValueError(f"{name} database binding is not the unique main database")
    if type(filename) is not str or not filename or filename == ":memory:" or "\x00" in filename:
        raise ValueError(f"{name} main database must have an exact filesystem filename")
    reported_path = _Path(filename)
    if not reported_path.is_absolute() or not reported_path.exists() or not reported_path.is_file():
        raise ValueError(f"{name} SQLite main database is not an existing filesystem file")
    try:
        same_file = expected_path.samefile(reported_path)
    except OSError as error:
        raise ValueError(f"{name} database filesystem identity cannot be verified") from error
    if not same_file:
        raise ValueError(f"{name} connection and supplied path identify different files")


def _file_identity(value: _os.stat_result) -> tuple[int, int]:
    return value.st_dev, value.st_ino


def _manifest_digest(path: _Path) -> tuple[str, tuple[int, int]]:
    try:
        before = path.stat(follow_symlinks=False)
        if not _stat.S_ISREG(before.st_mode):
            raise ValueError("manifest path must identify a regular file")
        with path.open("rb") as stream:
            opened = _os.fstat(stream.fileno())
            if _file_identity(opened) != _file_identity(before):
                raise ValueError("manifest path changed while opening")
            body = stream.read()
        after = path.stat(follow_symlinks=False)
    except (OSError, ValueError) as error:
        raise ValueError("manifest bytes cannot be read with stable file identity") from error
    identity = _file_identity(before)
    if _file_identity(after) != identity:
        raise ValueError("manifest path changed while reading")
    return _sha256(body).hexdigest(), identity


def _capture_payload(value: _CaptureReference | None) -> dict[str, object] | None:
    if value is None:
        return None
    return {
        "canonical_source_url": value.canonical_source_url,
        "capture_id": value.capture_id,
        "observed_at": _datetime_text(value.observed_at),
        "response_sha256": value.response_sha256,
    }


def _outcome_payload(outcome: object) -> dict[str, object]:
    target = outcome.target
    snapshot = outcome.snapshot_identity
    snapshot_payload = None
    if snapshot is not None:
        source = snapshot.source_identity
        snapshot_payload = {
            "captured_at": _datetime_text(snapshot.captured_at),
            "dataset_id": snapshot.dataset_id,
            "external_race_id": source.external_race_id,
            "organization": source.organization,
            "source_url": source.source_url,
            "source_system": source.source_system,
        }
    return {
        "disposition": outcome.disposition.value,
        "internal_race_id": outcome.internal_race_id,
        "payout_capture_reference": _capture_payload(outcome.payout_capture_reference),
        "reason_codes": list(outcome.reason_codes),
        "result_capture_reference": _capture_payload(outcome.result_capture_reference),
        "snapshot_content_sha256": outcome.snapshot_content_sha256,
        "snapshot_identity": snapshot_payload,
        "target_key": [
            target.provider_identity.organization,
            target.provider_identity.source_system,
            target.external_race_id,
        ],
    }


def _validate_payload_text(value: object) -> None:
    if type(value) is str:
        _required_text(value, "audit text")
    elif type(value) is list:
        for item in value:
            _validate_payload_text(item)
    elif type(value) is dict:
        for key, item in value.items():
            _required_text(key, "audit object key")
            _validate_payload_text(item)


def _audit_digest(
    *,
    acquisition_result: _AcquisitionResult,
    resolution: _Resolution,
    execution_state: NARDailyReplayExecutionState,
    manifest_sha256: str | None,
    audit_inputs: _AuditInputs,
) -> str:
    target_set = acquisition_result.target_set
    payload: dict[str, object] = {
        "acquisition": {
            "homepage_supplier_capture_id": acquisition_result.homepage_supplier_capture_id,
            "locator_script_supplier_capture_id": acquisition_result.locator_script_supplier_capture_id,
            "monthly_capture_id": acquisition_result.monthly_capture_id,
            "monthly_root_supplier_capture_id": acquisition_result.monthly_root_supplier_capture_id,
            "race_list_capture_ids": list(acquisition_result.race_list_capture_ids),
            "supplier_evidence_identity": acquisition_result.supplier_evidence_identity,
            "target_date": acquisition_result.target_date.isoformat(),
            "target_set_content_sha256": target_set.content_sha256,
        },
        "execution_state": execution_state.value,
        "inputs": {
            "database_path": str(audit_inputs.database_path),
            "manifest_source_path": str(audit_inputs.manifest_source_path),
            "nar_settlement_capture_archive_path": str(
                audit_inputs.nar_settlement_capture_archive_path
            ),
            "race_budget_total_amount": audit_inputs.race_budget.total_amount,
            "run_context": {
                "dataset_id": audit_inputs.run_context.dataset_id,
                "run_id": audit_inputs.run_context.run_id,
                "started_at": _datetime_text(audit_inputs.run_context.started_at),
                "target_commit_id": audit_inputs.run_context.target_commit_id,
            },
            "strategy": {
                "strategy_config_hash": audit_inputs.strategy_identity.strategy_config_hash,
                "strategy_id": audit_inputs.strategy_identity.strategy_id,
                "strategy_name": audit_inputs.strategy_identity.strategy_name,
            },
        },
        "manifest_sha256": manifest_sha256,
        "resolution": {
            "dataset_id": resolution.dataset_id,
            "day_state": resolution.day_state.value,
            "outcomes": [_outcome_payload(item) for item in resolution.outcomes],
            "selection_policy": resolution.selection_policy,
            "settlement_information_cutoff": _datetime_text(
                resolution.settlement_information_cutoff
            ),
        },
        "version": _AUDIT_VERSION,
    }
    _validate_payload_text(payload)
    try:
        canonical = _json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as error:
        raise ValueError("orchestration audit payload is not canonicalizable") from error
    return _sha256(canonical).hexdigest()


def compute_nar_daily_replay_orchestration_audit_sha256(
    *,
    acquisition_result: _AcquisitionResult,
    resolution: _Resolution,
    execution_state: NARDailyReplayExecutionState,
    manifest_sha256: str | None,
    database_path: _Path,
    nar_settlement_capture_archive_path: _Path,
    run_context: _RunContext,
    strategy_identity: _StrategyIdentity,
    race_budget: _BetStakeBudget,
    manifest_source_path: _Path,
) -> str:
    """Compute the frozen Phase 25 audit identity from exact public inputs."""

    acquisition = _validate_acquisition_result(acquisition_result)
    if type(resolution) is not _Resolution or resolution.target_set is not acquisition.target_set:
        raise ValueError("resolution must retain the exact acquisition target set")
    if type(execution_state) is not NARDailyReplayExecutionState:
        raise ValueError("execution_state must be an exact NARDailyReplayExecutionState")
    expected_state = {
        _ResolutionState.ALL_TARGETS_RESOLVED: NARDailyReplayExecutionState.FULL_DAY_REPLAY_COMPLETED,
        _ResolutionState.PARTIALLY_RESOLVED: NARDailyReplayExecutionState.NOT_RUN_PARTIAL_RESOLUTION,
        _ResolutionState.NO_EXECUTABLE_TARGETS: NARDailyReplayExecutionState.NOT_RUN_NO_EXECUTABLE_TARGETS,
    }[resolution.day_state]
    if execution_state is not expected_state:
        raise ValueError("execution_state disagrees with resolution state")
    if execution_state is NARDailyReplayExecutionState.FULL_DAY_REPLAY_COMPLETED:
        manifest_digest = _digest(manifest_sha256, "manifest_sha256")
    elif manifest_sha256 is not None:
        raise ValueError("diagnostic audit must not contain manifest_sha256")
    else:
        manifest_digest = None
    database = _absolute_path(database_path, "database_path")
    archive = _absolute_path(
        nar_settlement_capture_archive_path,
        "nar_settlement_capture_archive_path",
    )
    manifest = _absolute_path(manifest_source_path, "manifest_source_path")
    if type(run_context) is not _RunContext:
        raise ValueError("run_context must be an exact SimulationRunContext")
    if type(strategy_identity) is not _StrategyIdentity:
        raise ValueError("strategy_identity must be an exact StrategyIdentity")
    if type(race_budget) is not _BetStakeBudget:
        raise ValueError("race_budget must be an exact BetStakeBudget")
    return _audit_digest(
        acquisition_result=acquisition,
        resolution=resolution,
        execution_state=execution_state,
        manifest_sha256=manifest_digest,
        audit_inputs=_AuditInputs(
            database,
            archive,
            run_context,
            strategy_identity,
            race_budget,
            manifest,
        ),
    )


@_dataclass(frozen=True, slots=True)
class NARDailyReplayOrchestrationResult:
    acquisition_result: _AcquisitionResult
    resolution: _Resolution
    execution_state: NARDailyReplayExecutionState
    manifest_projection: _ManifestProjection | None
    manifest_sha256: str | None
    summary: _SimulationSummary | None
    _audit_inputs: _InitVar[_AuditInputs]
    orchestration_audit_sha256: str = _field(init=False)

    def __post_init__(self, _audit_inputs: _AuditInputs) -> None:
        if type(self.acquisition_result) is not _AcquisitionResult:
            raise ValueError("acquisition_result must be an exact NARDailyTargetLiveAcquisitionResult")
        if type(self.resolution) is not _Resolution:
            raise ValueError("resolution must be an exact DailyHistoricalReplayEvidenceResolution")
        if self.resolution.target_set is not self.acquisition_result.target_set:
            raise ValueError("resolution must retain the exact acquisition target set")
        if type(self.execution_state) is not NARDailyReplayExecutionState:
            raise ValueError("execution_state must be an exact NARDailyReplayExecutionState")
        if type(_audit_inputs) is not _AuditInputs:
            raise ValueError("result requires exact private audit inputs")

        day_state = self.resolution.day_state
        executable = self.executable_count
        target_count = self.canonical_target_count
        if day_state is _ResolutionState.ALL_TARGETS_RESOLVED:
            if (
                self.execution_state is not NARDailyReplayExecutionState.FULL_DAY_REPLAY_COMPLETED
                or executable != target_count
                or target_count == 0
                or type(self.manifest_projection) is not _ManifestProjection
                or self.manifest_projection.resolution is not self.resolution
                or self.manifest_projection.document is None
                or type(self.summary) is not _SimulationSummary
            ):
                raise ValueError("completed orchestration result is contradictory")
            _digest(self.manifest_sha256, "manifest_sha256")
            if self.summary.race_count != target_count:
                raise ValueError("summary race_count does not cover the full denominator")
            strategy = _audit_inputs.strategy_identity
            if (
                self.summary.strategy_id != strategy.strategy_id
                or self.summary.strategy_name != strategy.strategy_name
                or self.summary.strategy_config_hash != strategy.strategy_config_hash
            ):
                raise ValueError("summary strategy identity is contradictory")
        else:
            expected_state = (
                NARDailyReplayExecutionState.NOT_RUN_PARTIAL_RESOLUTION
                if day_state is _ResolutionState.PARTIALLY_RESOLVED
                else NARDailyReplayExecutionState.NOT_RUN_NO_EXECUTABLE_TARGETS
            )
            if (
                self.execution_state is not expected_state
                or self.manifest_projection is not None
                or self.manifest_sha256 is not None
                or self.summary is not None
            ):
                raise ValueError("diagnostic orchestration result is contradictory")

        object.__setattr__(
            self,
            "orchestration_audit_sha256",
            compute_nar_daily_replay_orchestration_audit_sha256(
                acquisition_result=self.acquisition_result,
                resolution=self.resolution,
                execution_state=self.execution_state,
                manifest_sha256=self.manifest_sha256,
                database_path=_audit_inputs.database_path,
                nar_settlement_capture_archive_path=(
                    _audit_inputs.nar_settlement_capture_archive_path
                ),
                run_context=_audit_inputs.run_context,
                strategy_identity=_audit_inputs.strategy_identity,
                race_budget=_audit_inputs.race_budget,
                manifest_source_path=_audit_inputs.manifest_source_path,
            ),
        )

    @property
    def canonical_target_count(self) -> int:
        return len(self.acquisition_result.target_set.target_races)

    @property
    def executable_count(self) -> int:
        return sum(
            outcome.disposition is _Disposition.EXECUTABLE
            for outcome in self.resolution.outcomes
        )


def _validate_projection(
    projection: object,
    *,
    resolution: _Resolution,
    database_path: _Path,
    archive_path: _Path,
    manifest_path: _Path,
    run_context: _RunContext,
    strategy_identity: _StrategyIdentity,
    race_budget: _BetStakeBudget,
) -> _ManifestProjection:
    if type(projection) is not _ManifestProjection or projection.resolution is not resolution:
        raise ValueError("Phase 16 projection must retain the exact resolution")
    document = projection.document
    if document is None:
        raise ValueError("full-day projection must contain a document")
    expected_outcomes = tuple(
        item for item in resolution.outcomes if item.disposition is _Disposition.EXECUTABLE
    )
    expected_races = tuple(
        (item.snapshot_identity, item.internal_race_id) for item in expected_outcomes
    )
    document_races = tuple(
        (item.snapshot_identity, item.internal_race_id) for item in document.races
    )
    expected_race_ids = {item.internal_race_id for item in expected_outcomes}
    if (
        document.source_path != manifest_path
        or document.database_path != database_path
        or dict(document.capture_archive_paths_by_provider)
        != {"NAR/nar_official": archive_path}
        or document.run_context != run_context
        or document.strategy_identity != strategy_identity
        or len(document.races) != len(resolution.target_set.target_races)
        or document_races != expected_races
        or set(document.budgets_by_race_id) != expected_race_ids
        or any(value != race_budget for value in document.budgets_by_race_id.values())
    ):
        raise ValueError("Phase 16 document disagrees with exact orchestration inputs")
    return projection


def run_nar_daily_replay(
    *,
    acquisition_result: _AcquisitionResult,
    dataset_id: str,
    settlement_information_cutoff: _datetime,
    snapshot_connection: _sqlite3.Connection,
    capture_connection: _sqlite3.Connection,
    database_path: _Path,
    nar_settlement_capture_archive_path: _Path,
    run_context: _RunContext,
    strategy_identity: _StrategyIdentity,
    race_budget: _BetStakeBudget,
    manifest_source_path: _Path,
) -> NARDailyReplayOrchestrationResult:
    """Resolve and, only for a complete executable day, run one exact replay."""

    acquisition_result = _validate_acquisition_result(acquisition_result)
    target_set = acquisition_result.target_set
    providers = target_set.provider_scope.providers
    if not target_set.target_races or len(providers) != 1 or (
        providers[0].organization,
        providers[0].source_system,
    ) != _NAR_PROVIDER:
        raise ValueError("acquisition target scope must be nonempty NAR/nar_official")
    dataset_id = _required_text(dataset_id, "dataset_id")
    cutoff = _aware_datetime(settlement_information_cutoff, "settlement_information_cutoff")
    if type(run_context) is not _RunContext or run_context.dataset_id != dataset_id:
        raise ValueError("run_context must be exact and match dataset_id")
    _required_text(run_context.run_id, "run_context.run_id")
    _required_text(run_context.dataset_id, "run_context.dataset_id")
    _required_text(run_context.target_commit_id, "run_context.target_commit_id")
    _aware_datetime(run_context.started_at, "run_context.started_at")
    if _RunContext(
        run_context.run_id,
        run_context.dataset_id,
        run_context.started_at,
        run_context.target_commit_id,
    ) != run_context:
        raise ValueError("run_context violates its immutable domain invariants")
    if type(strategy_identity) is not _StrategyIdentity:
        raise ValueError("strategy_identity must be an exact StrategyIdentity")
    _required_text(strategy_identity.strategy_id, "strategy_identity.strategy_id")
    _required_text(strategy_identity.strategy_name, "strategy_identity.strategy_name")
    _digest(strategy_identity.strategy_config_hash, "strategy_identity.strategy_config_hash")
    if _StrategyIdentity(
        strategy_identity.strategy_id,
        strategy_identity.strategy_name,
        strategy_identity.strategy_config,
        strategy_identity.strategy_config_hash,
    ) != strategy_identity:
        raise ValueError("strategy_identity violates its immutable domain invariants")
    if type(race_budget) is not _BetStakeBudget:
        raise ValueError("race_budget must be an exact BetStakeBudget")
    if _BetStakeBudget(race_budget.total_amount) != race_budget:
        raise ValueError("race_budget violates its immutable domain invariants")
    for name in (
        "homepage_supplier_capture_id",
        "monthly_root_supplier_capture_id",
        "locator_script_supplier_capture_id",
        "supplier_evidence_identity",
        "monthly_capture_id",
    ):
        _required_text(getattr(acquisition_result, name), f"acquisition_result.{name}")
    for value in acquisition_result.race_list_capture_ids:
        _required_text(value, "acquisition_result.race_list_capture_ids item")
    _digest(target_set.content_sha256, "target_set.content_sha256")
    database = _absolute_path(database_path, "database_path")
    archive = _absolute_path(
        nar_settlement_capture_archive_path,
        "nar_settlement_capture_archive_path",
    )
    manifest = _absolute_path(manifest_source_path, "manifest_source_path")
    if type(snapshot_connection) is not _sqlite3.Connection or type(capture_connection) is not _sqlite3.Connection:
        raise ValueError("snapshot and capture connections must be exact sqlite3.Connection values")
    if snapshot_connection is capture_connection:
        raise ValueError("snapshot and capture connections must be distinct")

    _require_connection_path_binding(snapshot_connection, database, "snapshot")
    _require_connection_path_binding(capture_connection, archive, "capture")
    try:
        if database.samefile(archive):
            raise ValueError("snapshot and settlement archive paths must identify distinct files")
    except OSError as error:
        raise ValueError("snapshot/archive filesystem identity cannot be verified") from error

    resolution = _resolve_evidence(
        target_set=target_set,
        dataset_id=dataset_id,
        settlement_information_cutoff=cutoff,
        snapshot_connection=snapshot_connection,
        capture_connection=capture_connection,
    )
    if type(resolution) is not _Resolution or resolution.target_set is not target_set:
        raise ValueError("Phase 14 resolution did not retain the exact target set")
    if _Resolution(
        resolution.target_set,
        resolution.dataset_id,
        resolution.selection_policy,
        resolution.settlement_information_cutoff,
        resolution.outcomes,
    ) != resolution:
        raise ValueError("Phase 14 resolution violates immutable domain invariants")
    if resolution.dataset_id != dataset_id or resolution.settlement_information_cutoff != cutoff:
        raise ValueError("Phase 14 resolution disagrees with exact inputs")
    if snapshot_connection.in_transaction or capture_connection.in_transaction:
        raise ValueError("Phase 14 resolution changed caller transaction state")

    audit_inputs = _AuditInputs(
        database,
        archive,
        run_context,
        strategy_identity,
        race_budget,
        manifest,
    )
    if resolution.day_state is _ResolutionState.PARTIALLY_RESOLVED:
        return NARDailyReplayOrchestrationResult(
            acquisition_result,
            resolution,
            NARDailyReplayExecutionState.NOT_RUN_PARTIAL_RESOLUTION,
            None,
            None,
            None,
            audit_inputs,
        )
    if resolution.day_state is _ResolutionState.NO_EXECUTABLE_TARGETS:
        return NARDailyReplayOrchestrationResult(
            acquisition_result,
            resolution,
            NARDailyReplayExecutionState.NOT_RUN_NO_EXECUTABLE_TARGETS,
            None,
            None,
            None,
            audit_inputs,
        )
    if resolution.day_state is not _ResolutionState.ALL_TARGETS_RESOLVED or any(
        item.disposition is not _Disposition.EXECUTABLE for item in resolution.outcomes
    ):
        raise ValueError("whole-day resolution state is contradictory")

    projection = _write_manifest(
        resolution=resolution,
        database_path=database,
        nar_capture_archive_path=archive,
        run_context=run_context,
        strategy_identity=strategy_identity,
        race_budget=race_budget,
        manifest_source_path=manifest,
    )
    projection = _validate_projection(
        projection,
        resolution=resolution,
        database_path=database,
        archive_path=archive,
        manifest_path=manifest,
        run_context=run_context,
        strategy_identity=strategy_identity,
        race_budget=race_budget,
    )
    manifest_sha256, manifest_identity = _manifest_digest(manifest)
    summary = _run_replay(document=projection.document)
    if type(summary) is not _SimulationSummary:
        raise ValueError("runner must return an exact SimulationSummary")
    after_sha256, after_identity = _manifest_digest(manifest)
    if after_identity != manifest_identity or after_sha256 != manifest_sha256:
        raise ValueError("manifest changed during replay execution")
    return NARDailyReplayOrchestrationResult(
        acquisition_result,
        resolution,
        NARDailyReplayExecutionState.FULL_DAY_REPLAY_COMPLETED,
        projection,
        manifest_sha256,
        summary,
        audit_inputs,
    )


if "annotations" in globals():
    del annotations
