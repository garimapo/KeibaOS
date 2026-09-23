"""Controlled snapshot commit/reload receipt and NAR cutoff qualification.

The receipt clock is sampled only after exact reload. It proves verified SQLite
availability under the existing repository contract, not crash durability.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from hashlib import sha256
from typing import Callable, Protocol

from scripts.simulation.historical_input_snapshots import (
    HistoricalInputSnapshot, HistoricalInputSnapshotIdentity, HistoricalSourceIdentity,
    compute_historical_input_snapshot_content_sha256,
)
from scripts.simulation.historical_daily_targets import DailyHistoricalReplayTarget
from scripts.simulation.nar_historical_replay_prediction_cutoff import (
    NARHistoricalReplayPredictionCutoffPlan,
)
from scripts.simulation.nar_operational_timing_observability import (
    _digest, _json_bytes, _parse_time, _read_json, _time, _utc,
)


class SnapshotFreezeError(ValueError):
    """The controlled freeze or its exact provenance cannot be verified."""


_ISSUANCE_MARKER = object()


class SnapshotFreezeSemantic(StrEnum):
    COMMITTED_AND_EXACT_RELOAD_VERIFIED = "COMMITTED_AND_EXACT_RELOAD_VERIFIED"


@dataclass(frozen=True, slots=True)
class HistoricalInputSnapshotFreezeReceipt:
    snapshot_identity: HistoricalInputSnapshotIdentity
    internal_race_id: int
    snapshot_content_sha256: str
    snapshot_information_cutoff: datetime
    freeze_completed_at: datetime
    freeze_semantic: SnapshotFreezeSemantic = SnapshotFreezeSemantic.COMMITTED_AND_EXACT_RELOAD_VERIFIED
    schema_version: int = 1
    receipt_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.snapshot_identity) is not HistoricalInputSnapshotIdentity:
            raise SnapshotFreezeError("receipt requires exact snapshot identity")
        if type(self.internal_race_id) is not int or self.internal_race_id <= 0:
            raise SnapshotFreezeError("receipt requires positive internal race ID")
        _digest(self.snapshot_content_sha256)
        if type(self.freeze_semantic) is not SnapshotFreezeSemantic or type(self.schema_version) is not int or self.schema_version != 1:
            raise SnapshotFreezeError("receipt semantic or version is unsupported")
        cutoff, completed = _utc(self.snapshot_information_cutoff), _utc(self.freeze_completed_at)
        if completed < self.snapshot_identity.captured_at:
            raise SnapshotFreezeError("freeze verification precedes declared capture")
        object.__setattr__(self, "snapshot_information_cutoff", cutoff)
        object.__setattr__(self, "freeze_completed_at", completed)
        object.__setattr__(self, "receipt_sha256", sha256(self.canonical_bytes()).hexdigest())

    @property
    def receipt_identity(self) -> str:
        return "historical-input-snapshot-freeze-v1:" + self.receipt_sha256

    def payload(self) -> dict[str, object]:
        identity = self.snapshot_identity
        source = identity.source_identity
        return {"schema_version": self.schema_version, "dataset_id": identity.dataset_id,
                "organization": source.organization, "source_system": source.source_system,
                "external_race_id": source.external_race_id, "source_url": source.source_url,
                "internal_race_id": self.internal_race_id,
                "snapshot_captured_at": _time(identity.captured_at),
                "snapshot_content_sha256": self.snapshot_content_sha256,
                "snapshot_information_cutoff": _time(self.snapshot_information_cutoff),
                "freeze_semantic": self.freeze_semantic.value,
                "freeze_completed_at": _time(self.freeze_completed_at)}

    def canonical_bytes(self) -> bytes:
        return _json_bytes(self.payload())

    @classmethod
    def from_json(cls, value: str) -> HistoricalInputSnapshotFreezeReceipt:
        p = _read_json(value)
        result = cls(HistoricalInputSnapshotIdentity(p["dataset_id"],
                     HistoricalSourceIdentity(p["organization"], p["source_system"],
                                              p["external_race_id"], p["source_url"]),
                     _parse_time(p["snapshot_captured_at"])),
                     p["internal_race_id"], p["snapshot_content_sha256"],
                     _parse_time(p["snapshot_information_cutoff"]),
                     _parse_time(p["freeze_completed_at"]),
                     SnapshotFreezeSemantic(p["freeze_semantic"]), p["schema_version"])
        if result.canonical_bytes() != value.encode("utf-8"):
            raise SnapshotFreezeError("receipt JSON is noncanonical")
        return result


class _SnapshotRepository(Protocol):
    def save_snapshot(self, *, snapshot: HistoricalInputSnapshot) -> None: ...
    def load_snapshot_by_identity(self, *, identity: HistoricalInputSnapshotIdentity) -> HistoricalInputSnapshot | None: ...


class _ReceiptArchive(Protocol):
    def save_freeze_receipt(self, *, receipt: HistoricalInputSnapshotFreezeReceipt,
                            _issuance_marker: object) -> None: ...
    def load_freeze_receipt(self, *, receipt_identity: str) -> HistoricalInputSnapshotFreezeReceipt | None: ...


def issue_historical_input_snapshot_freeze_receipt(
    *, snapshot: HistoricalInputSnapshot, snapshot_repository: _SnapshotRepository,
    archive: _ReceiptArchive, utc_clock: Callable[[], datetime],
) -> HistoricalInputSnapshotFreezeReceipt:
    """Save, exactly reload, sample the service clock, then durably archive proof.

    A duplicate existing snapshot without a receipt receives the current verification
    time. This never reconstructs an earlier completion from snapshot metadata.
    """
    if type(snapshot) is not HistoricalInputSnapshot or compute_historical_input_snapshot_content_sha256(snapshot=snapshot) != snapshot.content_sha256:
        raise SnapshotFreezeError("snapshot is not exact immutable content")
    snapshot_repository.save_snapshot(snapshot=snapshot)
    loaded = snapshot_repository.load_snapshot_by_identity(identity=snapshot.identity)
    if (type(loaded) is not HistoricalInputSnapshot or loaded.identity != snapshot.identity
            or loaded.identity.source_identity.source_url != snapshot.identity.source_identity.source_url
            or loaded.internal_race_id != snapshot.internal_race_id
            or loaded.information_cutoff != snapshot.information_cutoff
            or loaded.content_sha256 != snapshot.content_sha256
            or compute_historical_input_snapshot_content_sha256(snapshot=loaded) != snapshot.content_sha256):
        raise SnapshotFreezeError("committed snapshot did not reload exactly")
    completed = _utc(utc_clock())
    receipt = HistoricalInputSnapshotFreezeReceipt(
        snapshot.identity, snapshot.internal_race_id, snapshot.content_sha256,
        snapshot.information_cutoff, completed)
    archive.save_freeze_receipt(receipt=receipt, _issuance_marker=_ISSUANCE_MARKER)
    reloaded = archive.load_freeze_receipt(receipt_identity=receipt.receipt_identity)
    if type(reloaded) is not HistoricalInputSnapshotFreezeReceipt or reloaded != receipt or reloaded.receipt_sha256 != receipt.receipt_sha256:
        raise SnapshotFreezeError("freeze receipt did not reload exactly")
    return receipt


class NARSnapshotFreezeQualificationState(StrEnum):
    SNAPSHOT_FROZEN_BY_PREDICTION_CUTOFF = "SNAPSHOT_FROZEN_BY_PREDICTION_CUTOFF"
    SNAPSHOT_FREEZE_COMPLETED_AFTER_PREDICTION_CUTOFF = "SNAPSHOT_FREEZE_COMPLETED_AFTER_PREDICTION_CUTOFF"


@dataclass(frozen=True, slots=True)
class NARSnapshotFreezeQualification:
    receipt: HistoricalInputSnapshotFreezeReceipt
    target: DailyHistoricalReplayTarget
    cutoff_plan_sha256: str
    cutoff_policy_identity: str
    target_set_content_sha256: str
    prediction_information_cutoff: datetime
    state: NARSnapshotFreezeQualificationState


def qualify_nar_snapshot_freeze(
    *, receipt: HistoricalInputSnapshotFreezeReceipt, archive: _ReceiptArchive,
    target: DailyHistoricalReplayTarget, cutoff_plan: NARHistoricalReplayPredictionCutoffPlan,
) -> NARSnapshotFreezeQualification:
    """Qualify only a receipt that is independently reloadable from the archive."""
    if type(receipt) is not HistoricalInputSnapshotFreezeReceipt or type(target) is not DailyHistoricalReplayTarget or type(cutoff_plan) is not NARHistoricalReplayPredictionCutoffPlan:
        raise SnapshotFreezeError("qualification input types are unsupported")
    archived = archive.load_freeze_receipt(receipt_identity=receipt.receipt_identity)
    if archived != receipt or type(archived) is not HistoricalInputSnapshotFreezeReceipt:
        raise SnapshotFreezeError("receipt lacks exact archived provenance")
    source = receipt.snapshot_identity.source_identity
    if (source.organization, source.source_system, source.external_race_id) != (
        target.provider_identity.organization, target.provider_identity.source_system,
        target.external_race_id):
        raise SnapshotFreezeError("receipt target contradicts cutoff target")
    decisions = tuple(d for d in cutoff_plan.decisions if d.target == target)
    if len(decisions) != 1 or target not in cutoff_plan.target_set.target_races:
        raise SnapshotFreezeError("target is absent or duplicated in cutoff plan")
    cutoff = decisions[0].prediction_information_cutoff
    if receipt.snapshot_identity.captured_at > cutoff or receipt.snapshot_information_cutoff > cutoff:
        raise SnapshotFreezeError("snapshot violates prediction cutoff semantics")
    state = (NARSnapshotFreezeQualificationState.SNAPSHOT_FROZEN_BY_PREDICTION_CUTOFF
             if receipt.freeze_completed_at <= cutoff else
             NARSnapshotFreezeQualificationState.SNAPSHOT_FREEZE_COMPLETED_AFTER_PREDICTION_CUTOFF)
    return NARSnapshotFreezeQualification(receipt, target, cutoff_plan.plan_sha256,
        cutoff_plan.cutoff_policy_identity, cutoff_plan.target_set_content_sha256, cutoff, state)
