"""Immutable persisted projection of one valid NAR daily replay outcome."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass, field as _field
from datetime import date as _date, datetime as _datetime, timezone as _timezone
from decimal import Decimal as _Decimal, InvalidOperation as _InvalidOperation
from hashlib import sha256 as _sha256
import json as _json
from pathlib import Path as _Path
import re as _re
from unicodedata import normalize as _normalize

from scripts.simulation.historical_daily_evidence_resolution import (
    DailyHistoricalReplayEvidenceDisposition as _Disposition,
    DailyHistoricalReplayResolutionState as _ResolutionState,
)
from scripts.simulation.models import (
    BetTypeSummary as _BetTypeSummary,
    SimulationRunContext as _RunContext,
    SimulationSummary as _SimulationSummary,
    StrategyIdentity as _StrategyIdentity,
)
from scripts.simulation.nar_daily_replay_orchestrator import (
    NARDailyReplayExecutionState as _ExecutionState,
    NARDailyReplayOrchestrationResult as _OrchestrationResult,
    compute_nar_daily_replay_orchestration_audit_sha256 as _compute_audit_sha256,
)
from scripts.simulation.repositories.errors import (
    RepositoryDataIntegrityError as _RepositoryDataIntegrityError,
    RepositoryValidationError as _RepositoryValidationError,
)
from scripts.simulation.stake_allocation import BetStakeBudget as _BetStakeBudget


__all__ = (
    "NARDailyReplayResultPersistenceRequest",
    "PersistedNARDailyReplayResult",
    "persist_nar_daily_replay_result",
)


_CONTENT_VERSION = "nar-daily-replay-persisted-result-v1"
_SHA256 = _re.compile(r"[0-9a-f]{64}\Z")
_NAR = ("NAR", "nar_official")


def _text(value: object, name: str) -> str:
    if (
        type(value) is not str
        or not value
        or value != value.strip()
        or value != _normalize("NFC", value)
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise _RepositoryValidationError(f"{name} must be nonempty exact NFC text")
    return value


def _digest(value: object, name: str) -> str:
    value = _text(value, name)
    if _SHA256.fullmatch(value) is None:
        raise _RepositoryValidationError(f"{name} must be lowercase SHA-256")
    return value


def _absolute_path(value: object, name: str) -> _Path:
    if not isinstance(value, _Path):
        raise _RepositoryValidationError(f"{name} must be an exact Path")
    text = str(value)
    if not text or "\x00" in text or not value.is_absolute():
        raise _RepositoryValidationError(f"{name} must be absolute, nonempty and NUL-free")
    if text != _normalize("NFC", text):
        raise _RepositoryValidationError(f"{name} must be NFC path text")
    return value


def _utc(value: object, name: str) -> _datetime:
    if type(value) is not _datetime or value.tzinfo is None or value.utcoffset() is None:
        raise _RepositoryValidationError(f"{name} must be an exact aware datetime")
    return value.astimezone(_timezone.utc)


def _datetime_text(value: _datetime) -> str:
    return value.astimezone(_timezone.utc).isoformat(timespec="microseconds")


def _decimal_text(value: _Decimal | None) -> str | None:
    if value is None:
        return None
    if type(value) is not _Decimal or not value.is_finite():
        raise _RepositoryValidationError("summary rate must be a finite Decimal or None")
    return "0" if value == 0 else format(value.normalize(), "f")


def _decimal_from_text(value: object, name: str) -> _Decimal | None:
    if value is None:
        return None
    if type(value) is not str:
        raise _RepositoryDataIntegrityError(f"stored {name} must be canonical Decimal text")
    try:
        parsed = _Decimal(value)
    except _InvalidOperation as error:
        raise _RepositoryDataIntegrityError(f"stored {name} is not Decimal") from error
    if not parsed.is_finite() or _decimal_text(parsed) != value:
        raise _RepositoryDataIntegrityError(f"stored {name} is not canonical Decimal text")
    return parsed


def _validate_json_text(value: object, name: str) -> object:
    if type(value) is not str or not value:
        raise _RepositoryValidationError(f"{name} must be nonempty canonical JSON text")
    try:
        parsed = _json.loads(value)
    except (_json.JSONDecodeError, UnicodeError) as error:
        raise _RepositoryValidationError(f"{name} must be valid JSON") from error
    if _canonical_json(parsed) != value:
        raise _RepositoryValidationError(f"{name} must use canonical JSON encoding")
    return parsed


def _validate_payload_text(value: object) -> None:
    if type(value) is str:
        _text(value, "canonical payload text")
    elif type(value) is list:
        for item in value:
            _validate_payload_text(item)
    elif type(value) is dict:
        for key, item in value.items():
            _text(key, "canonical payload key")
            _validate_payload_text(item)


def _canonical_json(value: object) -> str:
    _validate_payload_text(value)
    try:
        return _json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError, UnicodeError) as error:
        raise _RepositoryValidationError("persisted payload is not canonicalizable") from error


def _capture_payload(value: object | None) -> dict[str, object] | None:
    if value is None:
        return None
    return {
        "canonical_source_url": value.canonical_source_url,
        "capture_id": value.capture_id,
        "observed_at_utc": _datetime_text(value.observed_at),
        "response_sha256": value.response_sha256,
    }


def _outcomes_json(result: _OrchestrationResult) -> str:
    payload: list[dict[str, object]] = []
    for outcome in result.resolution.outcomes:
        snapshot = outcome.snapshot_identity
        source = None if snapshot is None else snapshot.source_identity
        payload.append(
            {
                "disposition": outcome.disposition.value,
                "internal_race_id": outcome.internal_race_id,
                "payout_capture_reference": _capture_payload(
                    outcome.payout_capture_reference
                ),
                "reason_codes": list(outcome.reason_codes),
                "result_capture_reference": _capture_payload(
                    outcome.result_capture_reference
                ),
                "snapshot_content_sha256": outcome.snapshot_content_sha256,
                "snapshot_identity": None
                if snapshot is None
                else {
                    "captured_at_utc": _datetime_text(snapshot.captured_at),
                    "dataset_id": snapshot.dataset_id,
                    "external_race_id": source.external_race_id,
                    "organization": source.organization,
                    "source_system": source.source_system,
                    "source_url": source.source_url,
                },
                "target_key": [
                    outcome.target.provider_identity.organization,
                    outcome.target.provider_identity.source_system,
                    outcome.target.external_race_id,
                ],
            }
        )
    return _canonical_json(payload)


def _require_outcomes(
    value: str,
    *,
    dataset_id: str,
    cutoff: _datetime,
    canonical_target_count: int,
    executable_count: int,
) -> None:
    parsed = _validate_json_text(value, "resolution_outcomes_json")
    if type(parsed) is not list or len(parsed) != canonical_target_count:
        raise _RepositoryValidationError("resolution outcomes must cover the denominator")
    expected_keys = {
        "disposition", "internal_race_id", "payout_capture_reference", "reason_codes",
        "result_capture_reference", "snapshot_content_sha256", "snapshot_identity", "target_key",
    }
    keys: list[tuple[str, str, str]] = []
    observed_executable = 0
    for item in parsed:
        if type(item) is not dict or set(item) != expected_keys:
            raise _RepositoryValidationError("resolution outcome has an invalid shape")
        try:
            disposition = _Disposition(item["disposition"])
        except (TypeError, ValueError) as error:
            raise _RepositoryValidationError("resolution disposition is invalid") from error
        target_key = item["target_key"]
        if (
            type(target_key) is not list
            or len(target_key) != 3
            or tuple(target_key[:2]) != _NAR
        ):
            raise _RepositoryValidationError("resolution target key is invalid")
        key = tuple(_text(part, "resolution target key") for part in target_key)
        keys.append(key)
        reasons = item["reason_codes"]
        if type(reasons) is not list or reasons != sorted(set(reasons)):
            raise _RepositoryValidationError("resolution reasons must be sorted unique text")
        for reason in reasons:
            _text(reason, "resolution reason")
        internal_race_id = item["internal_race_id"]
        if internal_race_id is not None and (
            type(internal_race_id) is not int or internal_race_id <= 0
        ):
            raise _RepositoryValidationError("internal_race_id is invalid")
        snapshot = item["snapshot_identity"]
        snapshot_sha = item["snapshot_content_sha256"]
        if (snapshot is None) != (snapshot_sha is None):
            raise _RepositoryValidationError("snapshot identity/digest presence differs")
        if snapshot is not None:
            if type(snapshot) is not dict or set(snapshot) != {
                "captured_at_utc", "dataset_id", "external_race_id", "organization",
                "source_system", "source_url",
            }:
                raise _RepositoryValidationError("snapshot identity is malformed")
            if (
                snapshot["dataset_id"] != dataset_id
                or (snapshot["organization"], snapshot["source_system"], snapshot["external_race_id"])
                != key
            ):
                raise _RepositoryValidationError("snapshot identity disagrees with result")
            _parse_utc_text(snapshot["captured_at_utc"], "snapshot captured_at")
            if snapshot["source_url"] is not None:
                _text(snapshot["source_url"], "snapshot source_url")
            _digest(snapshot_sha, "snapshot_content_sha256")
        captures = []
        for name in ("result_capture_reference", "payout_capture_reference"):
            reference = item[name]
            if reference is not None:
                if type(reference) is not dict or set(reference) != {
                    "canonical_source_url", "capture_id", "observed_at_utc", "response_sha256"
                }:
                    raise _RepositoryValidationError("capture reference is malformed")
                _text(reference["canonical_source_url"], "capture URL")
                _text(reference["capture_id"], "capture ID")
                _digest(reference["response_sha256"], "capture response SHA")
                observed = _parse_utc_text(reference["observed_at_utc"], "capture observed_at")
                if observed > cutoff:
                    raise _RepositoryValidationError("capture exceeds settlement cutoff")
                captures.append(reference)
        if disposition is _Disposition.EXECUTABLE:
            observed_executable += 1
            if reasons or snapshot is None or internal_race_id is None or len(captures) != 2:
                raise _RepositoryValidationError("executable outcome references are incomplete")
        elif not reasons:
            raise _RepositoryValidationError("non-executable outcome requires a reason")
    if keys != sorted(keys) or len(set(keys)) != len(keys):
        raise _RepositoryValidationError("resolution outcome order/identity is invalid")
    if observed_executable != executable_count:
        raise _RepositoryValidationError("executable count disagrees with outcomes")


def _parse_utc_text(value: object, name: str) -> _datetime:
    if type(value) is not str:
        raise _RepositoryValidationError(f"{name} must be canonical UTC text")
    try:
        parsed = _datetime.fromisoformat(value)
    except ValueError as error:
        raise _RepositoryValidationError(f"{name} is invalid") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise _RepositoryValidationError(f"{name} must be aware")
    utc = parsed.astimezone(_timezone.utc)
    if _datetime_text(utc) != value:
        raise _RepositoryValidationError(f"{name} must be canonical UTC microsecond text")
    return utc


def _bet_type_payload(value: _BetTypeSummary) -> dict[str, object]:
    return {
        "bet_count": value.bet_count,
        "bet_hit_rate": _decimal_text(value.bet_hit_rate),
        "bet_type": value.bet_type,
        "hit_bet_count": value.hit_bet_count,
        "investment": value.investment,
        "payout": value.payout,
        "profit": value.profit,
        "roi": _decimal_text(value.roi),
        "settled_bet_count": value.settled_bet_count,
    }


def _summary_payload(value: _SimulationSummary | None) -> dict[str, object] | None:
    if value is None:
        return None
    return {
        "bet_count": value.bet_count,
        "bet_hit_rate": _decimal_text(value.bet_hit_rate),
        "by_bet_type": [
            _bet_type_payload(value.by_bet_type[key]) for key in sorted(value.by_bet_type)
        ],
        "error_race_count": value.error_race_count,
        "hit_bet_count": value.hit_bet_count,
        "hit_race_count": value.hit_race_count,
        "investment": value.investment,
        "maximum_drawdown": value.maximum_drawdown,
        "no_bet_race_count": value.no_bet_race_count,
        "payout": value.payout,
        "profit": value.profit,
        "race_count": value.race_count,
        "race_hit_rate": _decimal_text(value.race_hit_rate),
        "roi": _decimal_text(value.roi),
        "settled_bet_count": value.settled_bet_count,
        "settled_purchase_race_count": value.settled_purchase_race_count,
        "settled_race_count": value.settled_race_count,
        "strategy_config_hash": value.strategy_config_hash,
        "strategy_id": value.strategy_id,
        "strategy_name": value.strategy_name,
        "unsettled_race_count": value.unsettled_race_count,
        "unsupported_race_count": value.unsupported_race_count,
        "void_race_count": value.void_race_count,
    }


def _summary_from_storage(
    values: tuple[object, ...],
    by_bet_type: dict[str, _BetTypeSummary],
) -> _SimulationSummary:
    if len(values) != 22 or any(value is None for value in values[:18] + values[21:]):
        raise _RepositoryDataIntegrityError("stored completed summary is incomplete")
    try:
        return _SimulationSummary(
            strategy_id=values[0],
            strategy_name=values[1],
            strategy_config_hash=values[2],
            race_count=values[3],
            settled_race_count=values[4],
            unsettled_race_count=values[5],
            no_bet_race_count=values[6],
            void_race_count=values[7],
            error_race_count=values[8],
            unsupported_race_count=values[9],
            bet_count=values[10],
            settled_bet_count=values[11],
            settled_purchase_race_count=values[12],
            hit_bet_count=values[13],
            hit_race_count=values[14],
            investment=values[15],
            payout=values[16],
            profit=values[17],
            roi=_decimal_from_text(values[18], "summary roi"),
            bet_hit_rate=_decimal_from_text(values[19], "summary bet hit rate"),
            race_hit_rate=_decimal_from_text(values[20], "summary race hit rate"),
            maximum_drawdown=values[21],
            by_bet_type=by_bet_type,
        )
    except _RepositoryDataIntegrityError:
        raise
    except (TypeError, ValueError) as error:
        raise _RepositoryDataIntegrityError("stored summary violates domain invariants") from error


@_dataclass(frozen=True, slots=True)
class PersistedNARDailyReplayResult:
    schema_version: int
    orchestration_audit_sha256: str
    target_date: _date
    organization: str
    source_system: str
    execution_state: _ExecutionState
    resolution_state: _ResolutionState
    target_set_content_sha256: str
    supplier_evidence_identity: str
    homepage_supplier_capture_id: str
    monthly_root_supplier_capture_id: str
    locator_script_supplier_capture_id: str
    monthly_capture_id: str
    race_list_capture_ids: tuple[str, ...]
    dataset_id: str
    selection_policy: str
    settlement_information_cutoff: _datetime
    canonical_target_count: int
    executable_count: int
    resolution_outcomes_json: str
    run_id: str
    run_started_at: _datetime
    target_commit_id: str
    strategy_id: str
    strategy_name: str
    strategy_config_hash: str
    race_budget_total_amount: int
    database_path: _Path
    nar_settlement_capture_archive_path: _Path
    configured_manifest_source_path: _Path
    published_manifest_path: _Path | None
    manifest_sha256: str | None
    summary: _SimulationSummary | None
    persisted_content_sha256: str = _field(init=False)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise _RepositoryValidationError("schema_version must be exact version 1")
        _digest(self.orchestration_audit_sha256, "orchestration_audit_sha256")
        if type(self.target_date) is not _date:
            raise _RepositoryValidationError("target_date must be exact date")
        if (self.organization, self.source_system) != _NAR:
            raise _RepositoryValidationError("provider must be exact NAR/nar_official")
        if type(self.execution_state) is not _ExecutionState:
            raise _RepositoryValidationError("execution_state is invalid")
        if type(self.resolution_state) is not _ResolutionState:
            raise _RepositoryValidationError("resolution_state is invalid")
        expected = {
            _ExecutionState.FULL_DAY_REPLAY_COMPLETED: _ResolutionState.ALL_TARGETS_RESOLVED,
            _ExecutionState.NOT_RUN_PARTIAL_RESOLUTION: _ResolutionState.PARTIALLY_RESOLVED,
            _ExecutionState.NOT_RUN_NO_EXECUTABLE_TARGETS: _ResolutionState.NO_EXECUTABLE_TARGETS,
        }[self.execution_state]
        if self.resolution_state is not expected:
            raise _RepositoryValidationError("execution and resolution states disagree")
        _digest(self.target_set_content_sha256, "target_set_content_sha256")
        for name in (
            "supplier_evidence_identity", "homepage_supplier_capture_id",
            "monthly_root_supplier_capture_id", "locator_script_supplier_capture_id",
            "monthly_capture_id", "dataset_id", "selection_policy", "run_id",
            "target_commit_id", "strategy_id", "strategy_name",
        ):
            _text(getattr(self, name), name)
        _digest(self.strategy_config_hash, "strategy_config_hash")
        if type(self.race_list_capture_ids) is not tuple or not self.race_list_capture_ids:
            raise _RepositoryValidationError("race_list_capture_ids must be a nonempty tuple")
        for value in self.race_list_capture_ids:
            _text(value, "race_list_capture_ids item")
        if len(set(self.race_list_capture_ids)) != len(self.race_list_capture_ids):
            raise _RepositoryValidationError("race-list capture IDs must be unique")
        cutoff = _utc(self.settlement_information_cutoff, "settlement_information_cutoff")
        started = _utc(self.run_started_at, "run_started_at")
        object.__setattr__(self, "settlement_information_cutoff", cutoff)
        object.__setattr__(self, "run_started_at", started)
        if self.selection_policy != "LATEST_CAUSAL_IN_DATASET":
            raise _RepositoryValidationError("selection_policy is unsupported")
        if (
            type(self.canonical_target_count) is not int
            or self.canonical_target_count <= 0
            or type(self.executable_count) is not int
            or not 0 <= self.executable_count <= self.canonical_target_count
        ):
            raise _RepositoryValidationError("target counts are invalid")
        if (
            type(self.race_budget_total_amount) is not int
            or self.race_budget_total_amount < 0
            or self.race_budget_total_amount % 100
        ):
            raise _RepositoryValidationError("race budget is invalid")
        for name in (
            "database_path", "nar_settlement_capture_archive_path",
            "configured_manifest_source_path",
        ):
            _absolute_path(getattr(self, name), name)
        _require_outcomes(
            self.resolution_outcomes_json,
            dataset_id=self.dataset_id,
            cutoff=cutoff,
            canonical_target_count=self.canonical_target_count,
            executable_count=self.executable_count,
        )
        completed = self.execution_state is _ExecutionState.FULL_DAY_REPLAY_COMPLETED
        if completed:
            if (
                not isinstance(self.published_manifest_path, _Path)
                or self.published_manifest_path != self.configured_manifest_source_path
                or type(self.summary) is not _SimulationSummary
                or self.executable_count != self.canonical_target_count
            ):
                raise _RepositoryValidationError("completed record artifact/summary is invalid")
            _absolute_path(self.published_manifest_path, "published_manifest_path")
            _digest(self.manifest_sha256, "manifest_sha256")
            if (
                self.summary.strategy_id != self.strategy_id
                or self.summary.strategy_name != self.strategy_name
                or self.summary.strategy_config_hash != self.strategy_config_hash
                or self.summary.race_count != self.canonical_target_count
            ):
                raise _RepositoryValidationError("summary identity/count is contradictory")
        elif any(
            value is not None
            for value in (self.published_manifest_path, self.manifest_sha256, self.summary)
        ):
            raise _RepositoryValidationError("diagnostic record must be summary/artifact-less")
        object.__setattr__(self, "persisted_content_sha256", _content_digest(self))


def _content_payload(value: PersistedNARDailyReplayResult) -> dict[str, object]:
    return {
        "acquisition": {
            "homepage_supplier_capture_id": value.homepage_supplier_capture_id,
            "locator_script_supplier_capture_id": value.locator_script_supplier_capture_id,
            "monthly_capture_id": value.monthly_capture_id,
            "monthly_root_supplier_capture_id": value.monthly_root_supplier_capture_id,
            "race_list_capture_ids": list(value.race_list_capture_ids),
            "supplier_evidence_identity": value.supplier_evidence_identity,
            "target_set_content_sha256": value.target_set_content_sha256,
        },
        "configuration": {
            "configured_manifest_source_path": str(value.configured_manifest_source_path),
            "database_path": str(value.database_path),
            "dataset_id": value.dataset_id,
            "nar_settlement_capture_archive_path": str(
                value.nar_settlement_capture_archive_path
            ),
            "race_budget_total_amount": value.race_budget_total_amount,
            "run_context": {
                "run_id": value.run_id,
                "started_at_utc": _datetime_text(value.run_started_at),
                "target_commit_id": value.target_commit_id,
            },
            "strategy": {
                "strategy_config_hash": value.strategy_config_hash,
                "strategy_id": value.strategy_id,
                "strategy_name": value.strategy_name,
            },
        },
        "execution_state": value.execution_state.value,
        "manifest": None
        if value.published_manifest_path is None
        else {
            "manifest_sha256": value.manifest_sha256,
            "published_manifest_path": str(value.published_manifest_path),
        },
        "orchestration_audit_sha256": value.orchestration_audit_sha256,
        "organization": value.organization,
        "resolution": {
            "canonical_target_count": value.canonical_target_count,
            "executable_count": value.executable_count,
            "outcomes": _json.loads(value.resolution_outcomes_json),
            "selection_policy": value.selection_policy,
            "settlement_information_cutoff_utc": _datetime_text(
                value.settlement_information_cutoff
            ),
            "state": value.resolution_state.value,
        },
        "schema_version": value.schema_version,
        "source_system": value.source_system,
        "summary": _summary_payload(value.summary),
        "target_date": value.target_date.isoformat(),
        "version": _CONTENT_VERSION,
    }


def _content_digest(value: PersistedNARDailyReplayResult) -> str:
    return _sha256(_canonical_json(_content_payload(value)).encode("utf-8")).hexdigest()


@_dataclass(frozen=True, slots=True)
class NARDailyReplayResultPersistenceRequest:
    orchestration_result: _OrchestrationResult
    database_path: _Path
    nar_settlement_capture_archive_path: _Path
    run_context: _RunContext
    strategy_identity: _StrategyIdentity
    race_budget: _BetStakeBudget
    manifest_source_path: _Path

    def __post_init__(self) -> None:
        if type(self.orchestration_result) is not _OrchestrationResult:
            raise _RepositoryValidationError(
                "orchestration_result must be exact NARDailyReplayOrchestrationResult"
            )
        for name in (
            "database_path", "nar_settlement_capture_archive_path", "manifest_source_path"
        ):
            _absolute_path(getattr(self, name), name)
        if type(self.run_context) is not _RunContext:
            raise _RepositoryValidationError("run_context must be exact SimulationRunContext")
        if type(self.strategy_identity) is not _StrategyIdentity:
            raise _RepositoryValidationError("strategy_identity must be exact StrategyIdentity")
        if type(self.race_budget) is not _BetStakeBudget:
            raise _RepositoryValidationError("race_budget must be exact BetStakeBudget")
        computed = _compute_audit_sha256(
            acquisition_result=self.orchestration_result.acquisition_result,
            resolution=self.orchestration_result.resolution,
            execution_state=self.orchestration_result.execution_state,
            manifest_sha256=self.orchestration_result.manifest_sha256,
            database_path=self.database_path,
            nar_settlement_capture_archive_path=self.nar_settlement_capture_archive_path,
            run_context=self.run_context,
            strategy_identity=self.strategy_identity,
            race_budget=self.race_budget,
            manifest_source_path=self.manifest_source_path,
        )
        if computed != self.orchestration_result.orchestration_audit_sha256:
            raise _RepositoryValidationError("Phase 25 orchestration audit identity mismatch")


def _build_record(request: NARDailyReplayResultPersistenceRequest) -> PersistedNARDailyReplayResult:
    result = request.orchestration_result
    acquisition = result.acquisition_result
    resolution = result.resolution
    published_path = None
    if result.manifest_projection is not None:
        published_path = result.manifest_projection.document.source_path
    return PersistedNARDailyReplayResult(
        schema_version=1,
        orchestration_audit_sha256=result.orchestration_audit_sha256,
        target_date=acquisition.target_date,
        organization="NAR",
        source_system="nar_official",
        execution_state=result.execution_state,
        resolution_state=resolution.day_state,
        target_set_content_sha256=acquisition.target_set.content_sha256,
        supplier_evidence_identity=acquisition.supplier_evidence_identity,
        homepage_supplier_capture_id=acquisition.homepage_supplier_capture_id,
        monthly_root_supplier_capture_id=acquisition.monthly_root_supplier_capture_id,
        locator_script_supplier_capture_id=acquisition.locator_script_supplier_capture_id,
        monthly_capture_id=acquisition.monthly_capture_id,
        race_list_capture_ids=acquisition.race_list_capture_ids,
        dataset_id=resolution.dataset_id,
        selection_policy=resolution.selection_policy,
        settlement_information_cutoff=resolution.settlement_information_cutoff,
        canonical_target_count=result.canonical_target_count,
        executable_count=result.executable_count,
        resolution_outcomes_json=_outcomes_json(result),
        run_id=request.run_context.run_id,
        run_started_at=request.run_context.started_at,
        target_commit_id=request.run_context.target_commit_id,
        strategy_id=request.strategy_identity.strategy_id,
        strategy_name=request.strategy_identity.strategy_name,
        strategy_config_hash=request.strategy_identity.strategy_config_hash,
        race_budget_total_amount=request.race_budget.total_amount,
        database_path=request.database_path,
        nar_settlement_capture_archive_path=request.nar_settlement_capture_archive_path,
        configured_manifest_source_path=request.manifest_source_path,
        published_manifest_path=published_path,
        manifest_sha256=result.manifest_sha256,
        summary=result.summary,
    )


from scripts.simulation.repositories.sqlite_nar_daily_replay_result_repository import (
    SQLiteNARDailyReplayResultRepository as _SQLiteNARDailyReplayResultRepository,
)


def persist_nar_daily_replay_result(
    *,
    request: NARDailyReplayResultPersistenceRequest,
    repository: _SQLiteNARDailyReplayResultRepository,
) -> PersistedNARDailyReplayResult:
    """Publish and exact-reload one already validated orchestration result."""

    if type(request) is not NARDailyReplayResultPersistenceRequest:
        raise _RepositoryValidationError(
            "request must be exact NARDailyReplayResultPersistenceRequest"
        )
    if type(repository) is not _SQLiteNARDailyReplayResultRepository:
        raise _RepositoryValidationError(
            "repository must be exact SQLiteNARDailyReplayResultRepository"
        )
    # Rebuild the request so publication cannot bypass its audit verification.
    NARDailyReplayResultPersistenceRequest(
        orchestration_result=request.orchestration_result,
        database_path=request.database_path,
        nar_settlement_capture_archive_path=request.nar_settlement_capture_archive_path,
        run_context=request.run_context,
        strategy_identity=request.strategy_identity,
        race_budget=request.race_budget,
        manifest_source_path=request.manifest_source_path,
    )
    record = _build_record(request)
    repository.save_result(record=record)
    loaded = repository.load_result(
        persisted_content_sha256=record.persisted_content_sha256
    )
    if loaded is None or loaded != record:
        raise _RepositoryDataIntegrityError("persisted daily replay result failed exact reload")
    return loaded


if "annotations" in globals():
    del annotations
