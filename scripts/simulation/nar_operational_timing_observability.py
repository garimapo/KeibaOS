"""Pure, immutable identities for NAR timing campaigns and operation attempts.

Content identity describes semantics, not pre-measurement activation authority.
No value in this module authorizes a prediction cutoff policy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from hashlib import sha256
import json
import re
from unicodedata import normalize


_SHA = re.compile(r"[0-9a-f]{64}\Z")
_COMMIT = re.compile(r"[0-9a-f]{40}\Z")
_CONFIG_ID = re.compile(r"nar-operational-timing-config-v1:[0-9a-f]{64}\Z")


def _utc(value: datetime) -> datetime:
    if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be an exact aware datetime")
    return value.astimezone(timezone.utc)


def _time(value: datetime) -> str:
    return _utc(value).isoformat(timespec="microseconds")


def _parse_time(value: str) -> datetime:
    if type(value) is not str:
        raise ValueError("timestamp must be canonical UTC text")
    result = _utc(datetime.fromisoformat(value))
    if _time(result) != value:
        raise ValueError("timestamp must be canonical UTC text")
    return result


def _text(value: str) -> str:
    if type(value) is not str or not value or normalize("NFC", value) != value:
        raise ValueError("text must be nonempty exact NFC")
    return value


def _digest(value: str) -> str:
    if type(value) is not str or _SHA.fullmatch(value) is None:
        raise ValueError("digest must be lowercase SHA-256")
    return value


def _json_bytes(payload: dict[str, object]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, allow_nan=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def _identity(prefix: str, payload: dict[str, object]) -> str:
    return prefix + sha256(_json_bytes(payload)).hexdigest()


def _read_json(value: str) -> dict[str, object]:
    if type(value) is not str:
        raise ValueError("payload must be JSON text")
    def unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, item in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = item
        return result
    payload = json.loads(value, object_pairs_hook=unique,
                         parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")))
    if type(payload) is not dict or _json_bytes(payload) != value.encode("utf-8"):
        raise ValueError("payload is not canonical JSON")
    return payload


class NARTimingStage(StrEnum):
    SCHEDULER_DISPATCH = "SCHEDULER_DISPATCH"
    BOOTSTRAP_HOME_ACQUISITION = "BOOTSTRAP_HOME_ACQUISITION"
    MONTHLY_ROOT_ACQUISITION = "MONTHLY_ROOT_ACQUISITION"
    LOCATOR_SCRIPT_ACQUISITION = "LOCATOR_SCRIPT_ACQUISITION"
    MONTHLY_SCHEDULE_ACQUISITION = "MONTHLY_SCHEDULE_ACQUISITION"
    RACE_LIST_ACQUISITION = "RACE_LIST_ACQUISITION"
    OFFICIAL_RESPONSE_ACQUISITION = "OFFICIAL_RESPONSE_ACQUISITION"
    MARKET_ODDS_RAW_ACQUISITION = "MARKET_ODDS_RAW_ACQUISITION"
    RAW_CAPTURE_VALIDATION = "RAW_CAPTURE_VALIDATION"
    RAW_CAPTURE_PERSISTENCE = "RAW_CAPTURE_PERSISTENCE"
    PARSING = "PARSING"
    NORMALIZATION = "NORMALIZATION"
    SOURCE_RECORD_CONSTRUCTION = "SOURCE_RECORD_CONSTRUCTION"
    PROVIDER_IDENTITY_BINDING = "PROVIDER_IDENTITY_BINDING"
    SNAPSHOT_CONSTRUCTION = "SNAPSHOT_CONSTRUCTION"
    SNAPSHOT_PERSISTENCE = "SNAPSHOT_PERSISTENCE"
    SNAPSHOT_EXACT_RELOAD_CONFIRMATION = "SNAPSHOT_EXACT_RELOAD_CONFIRMATION"
    SNAPSHOT_ADAPTER = "SNAPSHOT_ADAPTER"
    PREDICTION_PIPELINE = "PREDICTION_PIPELINE"
    ALLOCATION = "ALLOCATION"
    BET_PLAN_CONSTRUCTION = "BET_PLAN_CONSTRUCTION"
    BET_PLAN_PERSISTENCE = "BET_PLAN_PERSISTENCE"
    SHADOW_ARTIFACT_PUBLICATION = "SHADOW_ARTIFACT_PUBLICATION"


class NARTimingStageFamily(StrEnum):
    PRE_C = "PRE_C"
    POST_C = "POST_C"


_POST_C = frozenset(tuple(NARTimingStage)[17:])


def stage_family(stage: NARTimingStage) -> NARTimingStageFamily:
    if type(stage) is not NARTimingStage:
        raise ValueError("stage must be closed NARTimingStage")
    return NARTimingStageFamily.POST_C if stage in _POST_C else NARTimingStageFamily.PRE_C


class NARHTTPTransportKind(StrEnum):
    NAR_BOOTSTRAP_HTTP = "NAR_BOOTSTRAP_HTTP"
    NAR_DAILY_TARGET_HTTP = "NAR_DAILY_TARGET_HTTP"
    NAR_OFFICIAL_RESPONSE_HTTP = "NAR_OFFICIAL_RESPONSE_HTTP"
    NAR_MARKET_ODDS_RAW_HTTP = "NAR_MARKET_ODDS_RAW_HTTP"


_REQUIRED_TRANSPORT = {
    NARTimingStage.BOOTSTRAP_HOME_ACQUISITION: NARHTTPTransportKind.NAR_BOOTSTRAP_HTTP,
    NARTimingStage.MONTHLY_ROOT_ACQUISITION: NARHTTPTransportKind.NAR_BOOTSTRAP_HTTP,
    NARTimingStage.LOCATOR_SCRIPT_ACQUISITION: NARHTTPTransportKind.NAR_BOOTSTRAP_HTTP,
    NARTimingStage.MONTHLY_SCHEDULE_ACQUISITION: NARHTTPTransportKind.NAR_DAILY_TARGET_HTTP,
    NARTimingStage.RACE_LIST_ACQUISITION: NARHTTPTransportKind.NAR_DAILY_TARGET_HTTP,
    NARTimingStage.OFFICIAL_RESPONSE_ACQUISITION: NARHTTPTransportKind.NAR_OFFICIAL_RESPONSE_HTTP,
    NARTimingStage.MARKET_ODDS_RAW_ACQUISITION: NARHTTPTransportKind.NAR_MARKET_ODDS_RAW_HTTP,
}


@dataclass(frozen=True, slots=True)
class NARHTTPTransportProfile:
    kind: NARHTTPTransportKind
    connect_timeout_microseconds: int
    read_timeout_microseconds: int

    def __post_init__(self) -> None:
        if type(self.kind) is not NARHTTPTransportKind:
            raise ValueError("transport kind is unsupported")
        for value in (self.connect_timeout_microseconds, self.read_timeout_microseconds):
            if type(value) is not int or value <= 0:
                raise ValueError("timeouts must be exact positive integer microseconds")


class NARRetryPolicy(StrEnum):
    NO_RETRY = "NO_RETRY"


class NARConcurrencyRegime(StrEnum):
    CONTROLLED_SINGLE_WORKER_SERIAL_V1 = "CONTROLLED_SINGLE_WORKER_SERIAL_V1"


class NARRaceListAcquisitionMode(StrEnum):
    SEQUENTIAL = "SEQUENTIAL"


class NARSampleAdmissionRule(StrEnum):
    OPERATION_STARTED_IN_HALF_OPEN_SESSION_WINDOW = "OPERATION_STARTED_IN_HALF_OPEN_SESSION_WINDOW"


class NARSessionCompletionRule(StrEnum):
    FIXED_WALL_CLOCK_END = "FIXED_WALL_CLOCK_END"


@dataclass(frozen=True, slots=True)
class NAROperationalTimingMeasurementConfiguration:
    software_commit_sha: str
    enabled_stages: tuple[NARTimingStage, ...]
    transport_profiles: tuple[NARHTTPTransportProfile, ...]
    repository_identity: str = "garimapo/KeibaOS"
    organization: str = "NAR"
    source_system: str = "nar_official"
    instrumentation_schema_version: int = 1
    retry_policy: NARRetryPolicy = NARRetryPolicy.NO_RETRY
    max_retries: int = 0
    backoff_microseconds: int = 0
    concurrency_regime: NARConcurrencyRegime = NARConcurrencyRegime.CONTROLLED_SINGLE_WORKER_SERIAL_V1
    max_concurrent_target_workflows: int = 1
    max_concurrent_http_requests: int = 1
    race_list_acquisition_mode: NARRaceListAcquisitionMode = NARRaceListAcquisitionMode.SEQUENTIAL
    sample_admission_semantic_version: int = 1
    schema_version: int = 1
    configuration_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.software_commit_sha) is not str or _COMMIT.fullmatch(self.software_commit_sha) is None:
            raise ValueError("software commit must be lowercase 40-hex Git SHA")
        if self.repository_identity != "garimapo/KeibaOS" or self.organization != "NAR" or self.source_system != "nar_official":
            raise ValueError("unsupported repository or provider scope")
        if any(type(value) is not int or value != 1 for value in
               (self.schema_version, self.instrumentation_schema_version,
                self.sample_admission_semantic_version, self.max_concurrent_target_workflows,
                self.max_concurrent_http_requests)):
            raise ValueError("unsupported configuration version or concurrency count")
        if (type(self.retry_policy) is not NARRetryPolicy or type(self.max_retries) is not int
                or self.max_retries != 0 or type(self.backoff_microseconds) is not int
                or self.backoff_microseconds != 0):
            raise ValueError("v1 supports NO_RETRY with zero retries and backoff")
        if (type(self.concurrency_regime) is not NARConcurrencyRegime or
                type(self.race_list_acquisition_mode) is not NARRaceListAcquisitionMode):
            raise ValueError("unsupported concurrency regime")
        stages = self.enabled_stages
        if type(stages) is not tuple or not stages or any(type(s) is not NARTimingStage for s in stages):
            raise ValueError("enabled stages must be a nonempty closed tuple")
        if len(set(stages)) != len(stages):
            raise ValueError("duplicate enabled stage")
        object.__setattr__(self, "enabled_stages", tuple(s for s in NARTimingStage if s in stages))
        profiles = self.transport_profiles
        if type(profiles) is not tuple or any(type(p) is not NARHTTPTransportProfile for p in profiles):
            raise ValueError("transport profiles must be an exact tuple")
        if len({p.kind for p in profiles}) != len(profiles):
            raise ValueError("duplicate transport profile")
        required = {_REQUIRED_TRANSPORT[s] for s in stages if s in _REQUIRED_TRANSPORT}
        if not required.issubset({p.kind for p in profiles}):
            raise ValueError("enabled transport family lacks a profile")
        object.__setattr__(self, "transport_profiles", tuple(p for k in NARHTTPTransportKind
                                                            for p in profiles if p.kind is k))
        object.__setattr__(self, "configuration_sha256", sha256(self.canonical_bytes()).hexdigest())

    @property
    def configuration_identity(self) -> str:
        return "nar-operational-timing-config-v1:" + self.configuration_sha256

    def payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version, "repository_identity": self.repository_identity,
            "software_commit_sha": self.software_commit_sha, "organization": self.organization,
            "source_system": self.source_system,
            "instrumentation_schema_version": self.instrumentation_schema_version,
            "enabled_stages": [s.value for s in self.enabled_stages],
            "transport_profiles": [{"kind": p.kind.value,
                                    "connect_timeout_microseconds": p.connect_timeout_microseconds,
                                    "read_timeout_microseconds": p.read_timeout_microseconds}
                                   for p in self.transport_profiles],
            "retry_policy": self.retry_policy.value, "max_retries": self.max_retries,
            "backoff_microseconds": self.backoff_microseconds,
            "concurrency_regime": self.concurrency_regime.value,
            "max_concurrent_target_workflows": self.max_concurrent_target_workflows,
            "max_concurrent_http_requests": self.max_concurrent_http_requests,
            "race_list_acquisition_mode": self.race_list_acquisition_mode.value,
            "sample_admission_semantic_version": self.sample_admission_semantic_version,
        }

    def canonical_bytes(self) -> bytes:
        return _json_bytes(self.payload())

    @classmethod
    def from_json(cls, value: str) -> NAROperationalTimingMeasurementConfiguration:
        p = _read_json(value)
        result = cls(
            software_commit_sha=p["software_commit_sha"],
            enabled_stages=tuple(NARTimingStage(s) for s in p["enabled_stages"]),
            transport_profiles=tuple(NARHTTPTransportProfile(NARHTTPTransportKind(x["kind"]),
                x["connect_timeout_microseconds"], x["read_timeout_microseconds"])
                for x in p["transport_profiles"]),
            **{k: p[k] for k in ("repository_identity", "organization", "source_system",
                "instrumentation_schema_version", "max_retries", "backoff_microseconds",
                "max_concurrent_target_workflows", "max_concurrent_http_requests",
                "sample_admission_semantic_version", "schema_version")},
            retry_policy=NARRetryPolicy(p["retry_policy"]),
            concurrency_regime=NARConcurrencyRegime(p["concurrency_regime"]),
            race_list_acquisition_mode=NARRaceListAcquisitionMode(p["race_list_acquisition_mode"]),
        )
        if result.canonical_bytes() != value.encode("utf-8"):
            raise ValueError("configuration JSON is not canonical")
        return result


@dataclass(frozen=True, slots=True)
class NAROperationalTimingMeasurementSession:
    configuration: NAROperationalTimingMeasurementConfiguration
    measurement_start_at: datetime
    measurement_end_at: datetime
    sample_admission_rule: NARSampleAdmissionRule = NARSampleAdmissionRule.OPERATION_STARTED_IN_HALF_OPEN_SESSION_WINDOW
    session_completion_rule: NARSessionCompletionRule = NARSessionCompletionRule.FIXED_WALL_CLOCK_END
    schema_version: int = 1
    session_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.configuration) is not NAROperationalTimingMeasurementConfiguration:
            raise ValueError("session requires exact configuration")
        start, end = _utc(self.measurement_start_at), _utc(self.measurement_end_at)
        if start >= end:
            raise ValueError("session start must precede fixed end")
        if type(self.sample_admission_rule) is not NARSampleAdmissionRule or type(self.session_completion_rule) is not NARSessionCompletionRule or type(self.schema_version) is not int or self.schema_version != 1:
            raise ValueError("unsupported session rule or version")
        object.__setattr__(self, "measurement_start_at", start)
        object.__setattr__(self, "measurement_end_at", end)
        object.__setattr__(self, "session_sha256", sha256(self.canonical_bytes()).hexdigest())

    @property
    def session_identity(self) -> str:
        return "nar-operational-timing-session-v1:" + self.session_sha256

    def admits(self, operation_started_at: datetime) -> bool:
        value = _utc(operation_started_at)
        return self.measurement_start_at <= value < self.measurement_end_at

    def payload(self) -> dict[str, object]:
        return {"schema_version": self.schema_version,
                "measurement_configuration_identity": self.configuration.configuration_identity,
                "measurement_start_at": _time(self.measurement_start_at),
                "measurement_end_at": _time(self.measurement_end_at),
                "sample_admission_rule": self.sample_admission_rule.value,
                "session_completion_rule": self.session_completion_rule.value}

    def canonical_bytes(self) -> bytes:
        return _json_bytes(self.payload())

    @classmethod
    def from_json(cls, value: str, configuration: NAROperationalTimingMeasurementConfiguration) -> NAROperationalTimingMeasurementSession:
        p = _read_json(value)
        if p["measurement_configuration_identity"] != configuration.configuration_identity:
            raise ValueError("session configuration contradicts archive")
        result = cls(configuration, _parse_time(p["measurement_start_at"]),
                     _parse_time(p["measurement_end_at"]),
                     NARSampleAdmissionRule(p["sample_admission_rule"]),
                     NARSessionCompletionRule(p["session_completion_rule"]), p["schema_version"])
        if result.canonical_bytes() != value.encode("utf-8"):
            raise ValueError("session JSON is not canonical")
        return result


class NARTimingCorrelationScope(StrEnum):
    PROVIDER = "PROVIDER"
    TARGET_SET = "TARGET_SET"
    RACE = "RACE"


@dataclass(frozen=True, slots=True)
class NARTimingCorrelation:
    """Provider-scoped immutable join identity, never policy authorization."""

    scope: NARTimingCorrelationScope
    external_race_id: str | None = None
    target_set_sha256: str | None = None
    cutoff_plan_sha256: str | None = None
    cutoff_policy_identity: str | None = None
    correlation_identity: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.scope) is not NARTimingCorrelationScope:
            raise ValueError("correlation scope is unsupported")
        if self.scope is NARTimingCorrelationScope.PROVIDER:
            if any(value is not None for value in (self.external_race_id, self.target_set_sha256,
                                                    self.cutoff_plan_sha256, self.cutoff_policy_identity)):
                raise ValueError("provider-wide correlation has no race or plan")
        if self.scope is NARTimingCorrelationScope.TARGET_SET:
            if self.external_race_id is not None or self.target_set_sha256 is None:
                raise ValueError("target-set correlation requires exact target-set SHA only")
        if self.scope is NARTimingCorrelationScope.RACE and self.external_race_id is None:
            raise ValueError("race correlation requires external race identity")
        if self.external_race_id is not None:
            _text(self.external_race_id)
        if self.target_set_sha256 is not None:
            _digest(self.target_set_sha256)
        if self.cutoff_plan_sha256 is not None:
            _digest(self.cutoff_plan_sha256)
        if self.cutoff_policy_identity is not None:
            if (type(self.cutoff_policy_identity) is not str or
                    re.fullmatch(r"nar-prediction-cutoff-policy-v1:[0-9a-f]{64}", self.cutoff_policy_identity) is None):
                raise ValueError("cutoff policy identity is unsupported")
        if self.cutoff_plan_sha256 is not None and (self.target_set_sha256 is None or self.cutoff_policy_identity is None):
            raise ValueError("plan correlation requires target-set and policy identities")
        object.__setattr__(self, "correlation_identity", _identity("nar-operational-timing-correlation-v1:", self.payload()))

    def payload(self) -> dict[str, object]:
        return {"schema_version": 1, "organization": "NAR", "source_system": "nar_official",
                "scope": self.scope.value, "external_race_id": self.external_race_id,
                "target_set_sha256": self.target_set_sha256,
                "cutoff_plan_sha256": self.cutoff_plan_sha256,
                "cutoff_policy_identity": self.cutoff_policy_identity}

    @classmethod
    def from_payload(cls, payload: object) -> NARTimingCorrelation:
        if type(payload) is not dict or set(payload) != {
            "schema_version", "organization", "source_system", "scope", "external_race_id",
            "target_set_sha256", "cutoff_plan_sha256", "cutoff_policy_identity"
        } or payload["schema_version"] != 1 or type(payload["schema_version"]) is not int or payload["organization"] != "NAR" or payload["source_system"] != "nar_official":
            raise ValueError("correlation payload is invalid")
        result = cls(NARTimingCorrelationScope(payload["scope"]), payload["external_race_id"],
                     payload["target_set_sha256"], payload["cutoff_plan_sha256"],
                     payload["cutoff_policy_identity"])
        if result.payload() != payload:
            raise ValueError("correlation payload is contradictory")
        return result


@dataclass(frozen=True, slots=True)
class NARTimingLoadContext:
    """Closed observed load fields; None means not measured, never assumed zero."""

    active_target_workflows: int | None = None
    active_http_requests: int | None = None
    process_cold_start: bool | None = None

    def __post_init__(self) -> None:
        for value in (self.active_target_workflows, self.active_http_requests):
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError("measured load counts must be nonnegative exact integers")
        if self.process_cold_start is not None and type(self.process_cold_start) is not bool:
            raise ValueError("cold-start classification must be exact bool when measured")

    def payload(self) -> dict[str, object]:
        return {"active_target_workflows": self.active_target_workflows,
                "active_http_requests": self.active_http_requests,
                "process_cold_start": self.process_cold_start}

    @classmethod
    def from_payload(cls, payload: object) -> NARTimingLoadContext:
        if type(payload) is not dict or set(payload) != {
            "active_target_workflows", "active_http_requests", "process_cold_start"
        }:
            raise ValueError("load context payload is invalid")
        return cls(payload["active_target_workflows"], payload["active_http_requests"],
                   payload["process_cold_start"])


@dataclass(frozen=True, slots=True)
class NAROperationalTimingAttempt:
    session: NAROperationalTimingMeasurementSession
    stage: NARTimingStage
    correlation: NARTimingCorrelation
    attempt_sequence: int
    operation_started_at: datetime
    load_context: NARTimingLoadContext = field(default_factory=NARTimingLoadContext)
    attempt_identity: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.session) is not NAROperationalTimingMeasurementSession or type(self.stage) is not NARTimingStage or self.stage not in self.session.configuration.enabled_stages:
            raise ValueError("attempt requires exact enabled stage and session")
        if type(self.correlation) is not NARTimingCorrelation:
            raise ValueError("attempt requires exact provider-scoped correlation")
        if type(self.load_context) is not NARTimingLoadContext:
            raise ValueError("attempt requires exact closed load context")
        if type(self.attempt_sequence) is not int or self.attempt_sequence < 0:
            raise ValueError("attempt sequence must be a nonnegative exact int")
        started = _utc(self.operation_started_at)
        if not self.session.admits(started):
            raise ValueError("attempt starts outside session admission window")
        object.__setattr__(self, "operation_started_at", started)
        object.__setattr__(self, "attempt_identity", _identity("nar-operational-timing-attempt-v1:", self.payload()))

    def payload(self) -> dict[str, object]:
        return {"schema_version": 1, "session_identity": self.session.session_identity,
                "configuration_identity": self.session.configuration.configuration_identity,
                "stage": self.stage.value, "correlation_identity": self.correlation.correlation_identity,
                "correlation": self.correlation.payload(),
                "load_context": self.load_context.payload(),
                "attempt_sequence": self.attempt_sequence,
                "operation_started_at": _time(self.operation_started_at)}

    def canonical_bytes(self) -> bytes:
        return _json_bytes(self.payload())

    @classmethod
    def from_json(cls, value: str, session: NAROperationalTimingMeasurementSession) -> NAROperationalTimingAttempt:
        p = _read_json(value)
        if p["session_identity"] != session.session_identity or p["configuration_identity"] != session.configuration.configuration_identity:
            raise ValueError("attempt session contradicts archive")
        correlation = NARTimingCorrelation.from_payload(p["correlation"])
        if p["correlation_identity"] != correlation.correlation_identity:
            raise ValueError("attempt correlation identity is contradictory")
        result = cls(session, NARTimingStage(p["stage"]), correlation,
                     p["attempt_sequence"], _parse_time(p["operation_started_at"]),
                     NARTimingLoadContext.from_payload(p["load_context"]))
        if result.canonical_bytes() != value.encode("utf-8"):
            raise ValueError("attempt JSON is not canonical")
        return result


class NARTimingTerminalDisposition(StrEnum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    TIMEOUT = "TIMEOUT"
    UNSUPPORTED = "UNSUPPORTED"


class NARTimingFailureClassification(StrEnum):
    TRANSPORT = "TRANSPORT"
    VALIDATION = "VALIDATION"
    PERSISTENCE = "PERSISTENCE"
    TIMEOUT = "TIMEOUT"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True, slots=True)
class NAROperationalTimingTerminalObservation:
    attempt: NAROperationalTimingAttempt
    operation_finished_at: datetime
    elapsed_microseconds: int
    disposition: NARTimingTerminalDisposition
    failure_classification: NARTimingFailureClassification | None = None
    artifact_sha256: str | None = None
    observation_identity: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.attempt) is not NAROperationalTimingAttempt or type(self.disposition) is not NARTimingTerminalDisposition:
            raise ValueError("terminal observation requires exact attempt/disposition")
        finished = _utc(self.operation_finished_at)
        if finished < self.attempt.operation_started_at:
            raise ValueError("terminal wall timestamp precedes attempt")
        if type(self.elapsed_microseconds) is not int or self.elapsed_microseconds < 0:
            raise ValueError("elapsed monotonic duration must be nonnegative exact microseconds")
        if self.disposition is NARTimingTerminalDisposition.SUCCESS:
            if self.failure_classification is not None:
                raise ValueError("success cannot have failure classification")
        elif type(self.failure_classification) is not NARTimingFailureClassification:
            raise ValueError("non-success requires closed failure classification")
        if self.artifact_sha256 is not None:
            _digest(self.artifact_sha256)
        object.__setattr__(self, "operation_finished_at", finished)
        object.__setattr__(self, "observation_identity", _identity("nar-operational-timing-terminal-v1:", self.payload()))

    def payload(self) -> dict[str, object]:
        return {"schema_version": 1, "attempt_identity": self.attempt.attempt_identity,
                "stage": self.attempt.stage.value,
                "operation_started_at": _time(self.attempt.operation_started_at),
                "operation_finished_at": _time(self.operation_finished_at),
                "elapsed_microseconds": self.elapsed_microseconds,
                "disposition": self.disposition.value,
                "failure_classification": None if self.failure_classification is None else self.failure_classification.value,
                "artifact_sha256": self.artifact_sha256}

    def canonical_bytes(self) -> bytes:
        return _json_bytes(self.payload())

    @classmethod
    def from_json(cls, value: str, attempt: NAROperationalTimingAttempt) -> NAROperationalTimingTerminalObservation:
        p = _read_json(value)
        if p["attempt_identity"] != attempt.attempt_identity or p["stage"] != attempt.stage.value or p["operation_started_at"] != _time(attempt.operation_started_at):
            raise ValueError("terminal attempt contradicts archive")
        kind = p["failure_classification"]
        result = cls(attempt, _parse_time(p["operation_finished_at"]), p["elapsed_microseconds"],
                     NARTimingTerminalDisposition(p["disposition"]),
                     None if kind is None else NARTimingFailureClassification(kind), p["artifact_sha256"])
        if result.canonical_bytes() != value.encode("utf-8"):
            raise ValueError("terminal JSON is not canonical")
        return result
