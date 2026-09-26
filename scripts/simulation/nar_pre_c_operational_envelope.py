"""Immutable target PRE_C authorities. Phase108 is diagnostic, never live permission.

The root owns elapsed duration; Phase105 children are nonadditive observations.
All raw ticks are process-local evidence and cannot authorize process resumption.
"""
from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from hashlib import sha256
from collections.abc import Mapping
import json
import re
from typing import ClassVar

from scripts.simulation.nar_operational_timing_observability import _utc, _time, _parse_time, _json_bytes
from scripts.simulation.nar_operational_timing_attempt_v2 import elapsed_microseconds_from_ns
from scripts.simulation.nar_historical_replay_prediction_cutoff import validate_nar_historical_replay_prediction_cutoff_plan_json
from scripts.simulation.nar_official_response_capture import canonicalize_nar_official_capture_url, NAROfficialPageKind
from scripts.simulation.historical_input_source_records import HistoricalInputSourceRecord


class NARPreCEnvelopeError(ValueError):
    """Missing, noncanonical or contradictory target envelope authority."""


class NARPreCHistoryMode(StrEnum):
    PRESTAGED = "PRESTAGED_HISTORY"
    GENERATED = "ROOT_GENERATED_HISTORY"


def digest(value):
    if type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise NARPreCEnvelopeError("exact SHA256 required")


def identity(value, prefix):
    if type(value) is not str or re.fullmatch(re.escape(prefix) + r":[0-9a-f]{64}", value) is None:
        raise NARPreCEnvelopeError("exact versioned identity required: " + prefix)


def _int(value, minimum=0):
    if type(value) is not int or value < minimum:
        raise NARPreCEnvelopeError("exact nonnegative integer required")


def _encode(value):
    if isinstance(value, Authority):
        return {"type": type(value).__name__, "value": value.payload()}
    if type(value) is datetime:
        return {"utc": _time(_utc(value))}
    if type(value) is date:
        return {"date": value.isoformat()}
    if type(value) is Decimal:
        return {"decimal": str(value)}
    if isinstance(value, StrEnum):
        return value.value
    if type(value) is tuple:
        return [_encode(x) for x in value]
    if isinstance(value, Mapping):
        return {key: _encode(item) for key, item in value.items()}
    if value is None or type(value) in (str, int, bool):
        return value
    raise NARPreCEnvelopeError("unsupported immutable content")


def source_record_bytes(record):
    """Bind complete record values AND causal evidence timestamps, not source_id alone."""
    if type(record) is not HistoricalInputSourceRecord:
        raise NARPreCEnvelopeError("exact source record required")
    return _json_bytes({
        "record": {f.name: _encode(getattr(record, f.name)) for f in fields(record) if f.name != "evidence"},
        "evidence": [{f.name: _encode(getattr(e, f.name)) for f in fields(e)} for e in record.evidence],
    })


def source_record_sha(record):
    return sha256(source_record_bytes(record)).hexdigest()


def snapshot_identity_bytes(snapshot):
    source = snapshot.identity.source_identity
    return _json_bytes({"dataset_id": snapshot.identity.dataset_id, "internal_race_id": snapshot.internal_race_id,
        "captured_at": _time(snapshot.identity.captured_at), "source_identity": {
            "organization": source.organization, "source_system": source.source_system,
            "external_race_id": source.external_race_id, "source_url": source.source_url}})


def _decode(value):
    if type(value) is list:
        return tuple(_decode(x) for x in value)
    if type(value) is dict:
        if set(value) == {"utc"}:
            return _parse_time(value["utc"])
        if set(value) == {"type", "value"}:
            kind = _TYPES.get(value["type"])
            if kind is None:
                raise NARPreCEnvelopeError("unknown authority type")
            return kind.from_payload(value["value"])
    return value


class Authority:
    prefix: ClassVar[str]

    @property
    def identity(self):
        return self.prefix + ":" + sha256(self.canonical_bytes()).hexdigest()

    def payload(self):
        return {"schema_version": 1, "semantic": self.prefix,
                **{f.name: _encode(getattr(self, f.name)) for f in fields(self)}}

    def canonical_bytes(self):
        return _json_bytes(self.payload())

    @classmethod
    def from_payload(cls, value):
        names = {f.name for f in fields(cls)}
        if (type(value) is not dict or set(value) != names | {"schema_version", "semantic"}
                or type(value["schema_version"]) is not int or value["schema_version"] != 1
                or value["semantic"] != cls.prefix):
            raise NARPreCEnvelopeError("noncanonical authority shape")
        args = {key: _decode(value[key]) for key in names}
        if cls is NARPreCOperationalEnvelopeExecutionPlanV1:
            args["history_mode"] = NARPreCHistoryMode(args["history_mode"])
        return cls(**args)

    @classmethod
    def from_json(cls, value):
        result = cls.from_payload(json.loads(value))
        if result.canonical_bytes() != value.encode("utf-8"):
            raise NARPreCEnvelopeError("noncanonical authority JSON")
        return result


@dataclass(frozen=True, slots=True)
class NARPreCTargetScopeV1(Authority):
    prefix = "nar-pre-c-target-scope-v1"
    external_race_id: str
    target_set_sha256: str
    cutoff_plan_sha256: str
    cutoff_plan_json: str
    prediction_information_cutoff: datetime
    dataset_id: str
    internal_race_id: int

    def __post_init__(self):
        if type(self.external_race_id) is not str or re.fullmatch(r"nar:[0-9]{8}:[1-9][0-9]*:[1-9][0-9]*", self.external_race_id) is None:
            raise NARPreCEnvelopeError("exact NAR target required")
        digest(self.target_set_sha256)
        digest(self.cutoff_plan_sha256)
        p = validate_nar_historical_replay_prediction_cutoff_plan_json(
            canonical_json=self.cutoff_plan_json, plan_sha256=self.cutoff_plan_sha256,
            target_set_content_sha256=self.target_set_sha256)
        cutoff = _utc(self.prediction_information_cutoff)
        decisions = [x for x in p["decisions"] if x["external_race_id"] == self.external_race_id]
        if len(decisions) != 1 or _parse_time(decisions[0]["prediction_information_cutoff"]) != cutoff:
            raise NARPreCEnvelopeError("target/cutoff decision mismatch")
        object.__setattr__(self, "prediction_information_cutoff", cutoff)
        if type(self.dataset_id) is not str or not self.dataset_id.strip():
            raise NARPreCEnvelopeError("dataset identity required")
        _int(self.internal_race_id, 1)


@dataclass(frozen=True, slots=True)
class NARPreCPrestagedInputManifestV1(Authority):
    prefix = "nar-pre-c-prestaged-input-manifest-v1"
    claim_identity: str
    scope: NARPreCTargetScopeV1
    fixture_bundle_json: str
    available_at: datetime
    entry_mapping: tuple[tuple[str, int], ...]
    mapping_content_authority: str
    history_records: tuple[tuple[str, str, str, str], ...]  # entry, kind, source id, full SHA

    def __post_init__(self):
        identity(self.claim_identity, "nar-operational-timing-campaign-execution-v1")
        if type(self.scope) is not NARPreCTargetScopeV1:
            raise NARPreCEnvelopeError("exact scope required")
        from scripts.simulation.nar_operational_timing_diagnostic_campaign import NAROperationalTimingDiagnosticFixtureBundleV1
        fixture = NAROperationalTimingDiagnosticFixtureBundleV1.from_json(self.fixture_bundle_json)
        if self.mapping_content_authority not in {m.sha256_hex for m in fixture.members}:
            raise NARPreCEnvelopeError("mapping requires exact immutable fixture content authority")
        object.__setattr__(self, "available_at", _utc(self.available_at))
        if type(self.entry_mapping) is not tuple or not self.entry_mapping or self.entry_mapping != tuple(sorted(self.entry_mapping)):
            raise NARPreCEnvelopeError("mapping must be canonically ordered")
        if len({x[0] for x in self.entry_mapping}) != len(self.entry_mapping) or len({x[1] for x in self.entry_mapping}) != len(self.entry_mapping):
            raise NARPreCEnvelopeError("mapping identity duplicated")
        for entry, internal in self.entry_mapping:
            if type(entry) is not str or not entry.startswith(self.scope.external_race_id + ":entry:"):
                raise NARPreCEnvelopeError("mapping target mismatch")
            _int(internal, 1)
        if type(self.history_records) is not tuple or self.history_records != tuple(sorted(self.history_records)) or len(set(self.history_records)) != len(self.history_records):
            raise NARPreCEnvelopeError("noncanonical prestaged history")
        for entry, kind, source_id, content in self.history_records:
            if entry not in dict(self.entry_mapping) or kind not in ("past_race", "past_race_absence") or type(source_id) is not str or not source_id:
                raise NARPreCEnvelopeError("prestaged history ancestry mismatch")
            digest(content)


INITIAL_OPERATIONS = ("CURRENT_DEBA_TABLE", "CURRENT_NORMALIZATION", "SNAPSHOT_PREREQUISITE_PROOF", "SNAPSHOT_BUILD", "SNAPSHOT_SAVE_EXACT_RELOAD_FREEZE")
DISCOVERY_ALGORITHMS = ("discover_nar_historical_past_race_history:c1", "normalize_nar_historical_past_race_absence_source_record:c1a")
# Reviewed V1 authority, deliberately independent of future enum membership.
REQUEST_FAMILIES_V1 = ("deba_table", "horse_mark_info", "race_mark_table")


@dataclass(frozen=True, slots=True)
class NARPreCOperationalEnvelopeExecutionPlanV1(Authority):
    prefix = "nar-pre-c-execution-plan-v1"
    manifest_identity: str
    scope: NARPreCTargetScopeV1
    history_mode: NARPreCHistoryMode
    current_url: str
    request_families: tuple[str, ...] = REQUEST_FAMILIES_V1
    initial_operations: tuple[str, ...] = INITIAL_OPERATIONS
    discovery_algorithms: tuple[str, ...] = DISCOVERY_ALGORITHMS
    continuation: str = "CONTINUE_AUTHORIZED_SIBLINGS_FAIL_ROOT_ON_ANY_REQUIRED_FAILURE"
    composition: str = "ROOT_SOLE_ADDITIVE_OWNER_CHILDREN_CONTAINED"
    max_retries: int = 0
    terminal_condition: str = "EXACT_SNAPSHOT_RELOAD_THEN_UTC_THEN_MONOTONIC_ENDPOINT"

    def __post_init__(self):
        identity(self.manifest_identity, NARPreCPrestagedInputManifestV1.prefix)
        if type(self.scope) is not NARPreCTargetScopeV1 or type(self.history_mode) is not NARPreCHistoryMode:
            raise NARPreCEnvelopeError("closed plan scope/mode required")
        kind, url = canonicalize_nar_official_capture_url(self.current_url)
        parts = self.scope.external_race_id.split(":")
        if kind is not NAROfficialPageKind.DEBA_TABLE or url != self.current_url or not (
                "k_babaCode=" + parts[2] + "&k_raceDate=" + parts[1][:4] + "%2F" + parts[1][4:6] + "%2F" + parts[1][6:] + "&k_raceNo=" + parts[3] in url):
            raise NARPreCEnvelopeError("current request contradicts exact target")
        if (type(self.request_families) is not tuple or self.request_families != REQUEST_FAMILIES_V1
                or self.initial_operations != INITIAL_OPERATIONS or self.discovery_algorithms != DISCOVERY_ALGORITHMS
                or self.continuation != "CONTINUE_AUTHORIZED_SIBLINGS_FAIL_ROOT_ON_ANY_REQUIRED_FAILURE"
                or self.composition != "ROOT_SOLE_ADDITIVE_OWNER_CHILDREN_CONTAINED"
                or type(self.max_retries) is not int or self.max_retries != 0
                or self.terminal_condition != "EXACT_SNAPSHOT_RELOAD_THEN_UTC_THEN_MONOTONIC_ENDPOINT"):
            raise NARPreCEnvelopeError("unreviewed execution semantics")

    @property
    def allowed_request_families(self):
        return (NAROfficialPageKind.DEBA_TABLE,) if self.history_mode is NARPreCHistoryMode.PRESTAGED else tuple(
            NAROfficialPageKind(value) for value in self.request_families)


@dataclass(frozen=True, slots=True)
class NARPreCOperationalEnvelopeV1(Authority):
    prefix = "nar-pre-c-operational-envelope-v1"
    claim_identity: str
    binding_identity: str
    session_identity: str
    runtime_bundle_identity: str
    manifest_identity: str
    execution_plan_identity: str
    scope: NARPreCTargetScopeV1
    classification: str = "DIAGNOSTIC_ONLY_NO_NETWORK"

    def __post_init__(self):
        for field, prefix in (("claim_identity", "nar-operational-timing-campaign-execution-v1"), ("binding_identity", "nar-operational-timing-runtime-binding-v1"), ("session_identity", "nar-operational-timing-session-v2"), ("runtime_bundle_identity", "nar-runtime-source-bundle-v1"), ("manifest_identity", NARPreCPrestagedInputManifestV1.prefix), ("execution_plan_identity", NARPreCOperationalEnvelopeExecutionPlanV1.prefix)):
            identity(getattr(self, field), prefix)
        if type(self.scope) is not NARPreCTargetScopeV1 or self.classification != "DIAGNOSTIC_ONLY_NO_NETWORK":
            raise NARPreCEnvelopeError("Phase108 does not authorize live execution")


@dataclass(frozen=True, slots=True)
class NARPreCEnvelopeStartEvidenceV1(Authority):
    prefix = "nar-pre-c-envelope-start-v1"
    root_identity: str
    clock_domain: str
    process_id: int
    monotonic_start_ns: int
    started_at: datetime
    first_attempt_sequence: int

    def __post_init__(self):
        identity(self.root_identity, NARPreCOperationalEnvelopeV1.prefix)
        digest(self.clock_domain)
        _int(self.process_id, 1)
        _int(self.monotonic_start_ns)
        _int(self.first_attempt_sequence)
        object.__setattr__(self, "started_at", _utc(self.started_at))


@dataclass(frozen=True, slots=True)
class NARCurrentEntryDiscoveryClosureV1(Authority):
    prefix = "nar-pre-c-current-entry-closure-v1"
    start_identity: str
    parent_capture_identity: str
    parent_attempt_identity: str
    normalized_records: tuple[tuple[str, str], ...]
    entries: tuple[tuple[str, int, str, str], ...]
    first_authorized_sequence: int
    closed_at: datetime

    def __post_init__(self):
        identity(self.start_identity, NARPreCEnvelopeStartEvidenceV1.prefix)
        identity(self.parent_capture_identity, "nar-capture-v1")
        identity(self.parent_attempt_identity, "nar-operational-timing-attempt-v2")
        _int(self.first_authorized_sequence)
        object.__setattr__(self, "closed_at", _utc(self.closed_at))
        if type(self.entries) is not tuple or not self.entries or tuple(x[1] for x in self.entries) != tuple(sorted(x[1] for x in self.entries)) or len({x[0] for x in self.entries}) != len(self.entries):
            raise NARPreCEnvelopeError("current entries are partial or noncanonical")
        for entry, number, horse, url in self.entries:
            _int(number, 1)
            if not entry.endswith(":entry:" + str(number)) or re.fullmatch(r"nar:horse:[1-9][0-9]*", horse) is None:
                raise NARPreCEnvelopeError("entry/horse ancestry mismatch")
            kind, canonical = canonicalize_nar_official_capture_url(url)
            if kind is not NAROfficialPageKind.HORSE_MARK_INFO or canonical != url or url.rsplit("=", 1)[1] != horse.rsplit(":", 1)[1]:
                raise NARPreCEnvelopeError("entry request identity mismatch")
        if type(self.normalized_records) is not tuple or not self.normalized_records or self.normalized_records != tuple(sorted(self.normalized_records)) or len({x[0] for x in self.normalized_records}) != len(self.normalized_records):
            raise NARPreCEnvelopeError("normalized content authority invalid")
        for source, content in self.normalized_records:
            digest(content)


@dataclass(frozen=True, slots=True)
class NARPastRaceDiscoveryClosureV1(Authority):
    prefix = "nar-pre-c-past-race-closure-v1"
    entry_closure_identity: str
    parent_capture_identity: str
    parent_attempt_identity: str
    entry_identity: str
    horse_identity: str
    events: tuple[tuple[str, str, str, str | None], ...]
    proven_zero_history: bool
    first_authorized_sequence: int
    closed_at: datetime
    algorithm: str = "discover_nar_historical_past_race_history:c1"

    def __post_init__(self):
        identity(self.entry_closure_identity, NARCurrentEntryDiscoveryClosureV1.prefix)
        identity(self.parent_capture_identity, "nar-capture-v1")
        identity(self.parent_attempt_identity, "nar-operational-timing-attempt-v2")
        _int(self.first_authorized_sequence)
        object.__setattr__(self, "closed_at", _utc(self.closed_at))
        if type(self.events) is not tuple or type(self.proven_zero_history) is not bool or self.proven_zero_history != (self.events == ()) or self.algorithm != DISCOVERY_ALGORITHMS[0]:
            raise NARPreCEnvelopeError("history completeness/zero proof invalid")
        from scripts.simulation.nar_historical_past_race_discovery import NARHistoricalEventKind
        if len({x[2] for x in self.events}) != len(self.events) or tuple(x[1] for x in self.events) != tuple(sorted((x[1] for x in self.events), reverse=True)):
            raise NARPreCEnvelopeError("partial or unordered history")
        for kind, day, event, url in self.events:
            parsed = NARHistoricalEventKind(kind)
            date.fromisoformat(day)
            if parsed is NARHistoricalEventKind.NAR_ACTUAL_START:
                actual, canonical = canonicalize_nar_official_capture_url(url)
                if actual is not NAROfficialPageKind.RACE_MARK_TABLE or canonical != url:
                    raise NARPreCEnvelopeError("result request not canonical")
            elif url is not None:
                raise NARPreCEnvelopeError("non-request event cannot authorize a provider request")

    @property
    def request_urls(self):
        return tuple(x[3] for x in self.events if x[0] == "nar_actual_start")


@dataclass(frozen=True, slots=True)
class NARPreCEnvelopeCompletionEvidenceV1(Authority):
    prefix = "nar-pre-c-envelope-completion-v1"
    start_identity: str
    clock_domain: str
    process_id: int
    monotonic_endpoint_ns: int
    elapsed_microseconds: int
    snapshot_content_sha256: str
    snapshot_identity_json: str
    freeze_receipt_identity: str
    freeze_completed_at: datetime
    prerequisite_proof: tuple[tuple[str, str, str], ...]
    children: tuple[tuple[str, str, str], ...]  # URL, attempt identity, capture identity

    def __post_init__(self):
        identity(self.start_identity, NARPreCEnvelopeStartEvidenceV1.prefix)
        digest(self.clock_domain)
        digest(self.snapshot_content_sha256)
        identity(self.freeze_receipt_identity, "historical-input-snapshot-freeze-v1")
        _int(self.process_id, 1)
        _int(self.monotonic_endpoint_ns)
        _int(self.elapsed_microseconds)
        object.__setattr__(self, "freeze_completed_at", _utc(self.freeze_completed_at))
        if type(self.snapshot_identity_json) is not str or _json_bytes(json.loads(self.snapshot_identity_json)) != self.snapshot_identity_json.encode():
            raise NARPreCEnvelopeError("snapshot identity must be canonical")
        if type(self.prerequisite_proof) is not tuple or not self.prerequisite_proof or self.prerequisite_proof != tuple(sorted(self.prerequisite_proof)) or len({x[0] for x in self.prerequisite_proof}) != len(self.prerequisite_proof):
            raise NARPreCEnvelopeError("snapshot prerequisites missing/duplicated")
        for name, disposition, content in self.prerequisite_proof:
            if disposition not in ("PRESTAGED_AND_AUTHORITY_CLOSED_BEFORE_ROOT", "GENERATED_INSIDE_ROOT_UNDER_EXECUTION_PLAN"):
                raise NARPreCEnvelopeError("implicit prerequisite forbidden")
            digest(content)
        if type(self.children) is not tuple or len({x[1] for x in self.children}) != len(self.children):
            raise NARPreCEnvelopeError("child identity duplicated")
        for url, attempt, capture in self.children:
            kind, canonical = canonicalize_nar_official_capture_url(url)
            if url != canonical:
                raise NARPreCEnvelopeError("noncanonical child")
            identity(attempt, "nar-operational-timing-attempt-v2")
            identity(capture, "nar-capture-v1")


_TYPES = {x.__name__: x for x in (NARPreCTargetScopeV1, NARPreCPrestagedInputManifestV1,
    NARPreCOperationalEnvelopeExecutionPlanV1, NARPreCOperationalEnvelopeV1,
    NARPreCEnvelopeStartEvidenceV1, NARCurrentEntryDiscoveryClosureV1,
    NARPastRaceDiscoveryClosureV1, NARPreCEnvelopeCompletionEvidenceV1)}
