"""Immutable V2 timing campaign semantics; no execution or policy authority."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from hashlib import sha256
import re

from scripts.simulation.nar_operational_timing_observability import (
    NARConcurrencyRegime, NARHTTPTransportKind, NARHTTPTransportProfile,
    NARRaceListAcquisitionMode, NARRetryPolicy, NARSessionCompletionRule,
    _json_bytes, _parse_time, _read_json, _time, _utc,
)


_COMMIT = re.compile(r"[0-9a-f]{40}\Z")
_CONFIG_ID = re.compile(r"nar-operational-timing-config-v2:[0-9a-f]{64}\Z")


class NAROperationalTimingStageV2(StrEnum):
    CAMPAIGN_EXECUTION_PREPARATION = "CAMPAIGN_EXECUTION_PREPARATION"
    RUNTIME_BINDING_READINESS = "RUNTIME_BINDING_READINESS"
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
    FREEZE_RECEIPT_CONSTRUCTION = "FREEZE_RECEIPT_CONSTRUCTION"
    FREEZE_RECEIPT_PUBLICATION = "FREEZE_RECEIPT_PUBLICATION"
    FREEZE_RECEIPT_EXACT_RELOAD = "FREEZE_RECEIPT_EXACT_RELOAD"
    ATTEMPT_START_PUBLICATION = "ATTEMPT_START_PUBLICATION"
    TERMINAL_PUBLICATION = "TERMINAL_PUBLICATION"
    SNAPSHOT_ADAPTER = "SNAPSHOT_ADAPTER"
    PREDICTION_PIPELINE = "PREDICTION_PIPELINE"
    ALLOCATION = "ALLOCATION"
    BET_PLAN_CONSTRUCTION = "BET_PLAN_CONSTRUCTION"
    BET_PLAN_PERSISTENCE = "BET_PLAN_PERSISTENCE"
    SHADOW_ARTIFACT_PUBLICATION = "SHADOW_ARTIFACT_PUBLICATION"


class NARTimingBudgetRoleV2(StrEnum):
    PRE_C_FREEZE = "PRE_C_FREEZE"
    FREEZE_PROVENANCE = "FREEZE_PROVENANCE"
    OBSERVABILITY_OVERHEAD = "OBSERVABILITY_OVERHEAD"
    POST_C_COMPUTE = "POST_C_COMPUTE"
    CAMPAIGN_CONTROL = "CAMPAIGN_CONTROL"


_ROLE_STAGES = {
    NARTimingBudgetRoleV2.CAMPAIGN_CONTROL: frozenset({
        NAROperationalTimingStageV2.CAMPAIGN_EXECUTION_PREPARATION,
        NAROperationalTimingStageV2.RUNTIME_BINDING_READINESS,
    }),
    NARTimingBudgetRoleV2.FREEZE_PROVENANCE: frozenset({
        NAROperationalTimingStageV2.FREEZE_RECEIPT_CONSTRUCTION,
        NAROperationalTimingStageV2.FREEZE_RECEIPT_PUBLICATION,
        NAROperationalTimingStageV2.FREEZE_RECEIPT_EXACT_RELOAD,
    }),
    NARTimingBudgetRoleV2.OBSERVABILITY_OVERHEAD: frozenset({
        NAROperationalTimingStageV2.ATTEMPT_START_PUBLICATION,
        NAROperationalTimingStageV2.TERMINAL_PUBLICATION,
    }),
    NARTimingBudgetRoleV2.POST_C_COMPUTE: frozenset({
        NAROperationalTimingStageV2.SNAPSHOT_ADAPTER,
        NAROperationalTimingStageV2.PREDICTION_PIPELINE,
        NAROperationalTimingStageV2.ALLOCATION,
        NAROperationalTimingStageV2.BET_PLAN_CONSTRUCTION,
        NAROperationalTimingStageV2.BET_PLAN_PERSISTENCE,
        NAROperationalTimingStageV2.SHADOW_ARTIFACT_PUBLICATION,
    }),
    NARTimingBudgetRoleV2.PRE_C_FREEZE: frozenset({
        NAROperationalTimingStageV2.SCHEDULER_DISPATCH,
        NAROperationalTimingStageV2.BOOTSTRAP_HOME_ACQUISITION,
        NAROperationalTimingStageV2.MONTHLY_ROOT_ACQUISITION,
        NAROperationalTimingStageV2.LOCATOR_SCRIPT_ACQUISITION,
        NAROperationalTimingStageV2.MONTHLY_SCHEDULE_ACQUISITION,
        NAROperationalTimingStageV2.RACE_LIST_ACQUISITION,
        NAROperationalTimingStageV2.OFFICIAL_RESPONSE_ACQUISITION,
        NAROperationalTimingStageV2.MARKET_ODDS_RAW_ACQUISITION,
        NAROperationalTimingStageV2.RAW_CAPTURE_VALIDATION,
        NAROperationalTimingStageV2.RAW_CAPTURE_PERSISTENCE,
        NAROperationalTimingStageV2.PARSING,
        NAROperationalTimingStageV2.NORMALIZATION,
        NAROperationalTimingStageV2.SOURCE_RECORD_CONSTRUCTION,
        NAROperationalTimingStageV2.PROVIDER_IDENTITY_BINDING,
        NAROperationalTimingStageV2.SNAPSHOT_CONSTRUCTION,
        NAROperationalTimingStageV2.SNAPSHOT_PERSISTENCE,
        NAROperationalTimingStageV2.SNAPSHOT_EXACT_RELOAD_CONFIRMATION,
    }),
}


def budget_role_v2(stage: NAROperationalTimingStageV2) -> NARTimingBudgetRoleV2:
    if type(stage) is not NAROperationalTimingStageV2:
        raise ValueError("stage must be exact V2 enum")
    return next(role for role, stages in _ROLE_STAGES.items() if stage in stages)


_REQUIRED_TRANSPORT = {
    NAROperationalTimingStageV2.BOOTSTRAP_HOME_ACQUISITION: NARHTTPTransportKind.NAR_BOOTSTRAP_HTTP,
    NAROperationalTimingStageV2.MONTHLY_ROOT_ACQUISITION: NARHTTPTransportKind.NAR_BOOTSTRAP_HTTP,
    NAROperationalTimingStageV2.LOCATOR_SCRIPT_ACQUISITION: NARHTTPTransportKind.NAR_BOOTSTRAP_HTTP,
    NAROperationalTimingStageV2.MONTHLY_SCHEDULE_ACQUISITION: NARHTTPTransportKind.NAR_DAILY_TARGET_HTTP,
    NAROperationalTimingStageV2.RACE_LIST_ACQUISITION: NARHTTPTransportKind.NAR_DAILY_TARGET_HTTP,
    NAROperationalTimingStageV2.OFFICIAL_RESPONSE_ACQUISITION: NARHTTPTransportKind.NAR_OFFICIAL_RESPONSE_HTTP,
    NAROperationalTimingStageV2.MARKET_ODDS_RAW_ACQUISITION: NARHTTPTransportKind.NAR_MARKET_ODDS_RAW_HTTP,
}


class NARSampleAdmissionRuleV2(StrEnum):
    ATTEMPT_ADMITTED_IN_HALF_OPEN_SESSION_WINDOW = "ATTEMPT_ADMITTED_IN_HALF_OPEN_SESSION_WINDOW"


@dataclass(frozen=True, slots=True)
class NAROperationalTimingMeasurementConfigurationV2:
    software_commit_sha: str
    enabled_stages: tuple[NAROperationalTimingStageV2, ...]
    transport_profiles: tuple[NARHTTPTransportProfile, ...]
    repository_identity: str = "garimapo/KeibaOS"
    organization: str = "NAR"
    source_system: str = "nar_official"
    instrumentation_schema_version: int = 2
    retry_policy: NARRetryPolicy = NARRetryPolicy.NO_RETRY
    max_retries: int = 0
    backoff_microseconds: int = 0
    concurrency_regime: NARConcurrencyRegime = NARConcurrencyRegime.CONTROLLED_SINGLE_WORKER_SERIAL_V1
    max_concurrent_target_workflows: int = 1
    max_concurrent_http_requests: int = 1
    race_list_acquisition_mode: NARRaceListAcquisitionMode = NARRaceListAcquisitionMode.SEQUENTIAL
    sample_admission_semantic_version: int = 2
    execution_authority_semantic_version: int = 1
    schema_version: int = 2
    configuration_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.software_commit_sha) is not str or _COMMIT.fullmatch(self.software_commit_sha) is None:
            raise ValueError("software commit must be lowercase 40-hex Git SHA")
        if (type(self.repository_identity) is not str or self.repository_identity != "garimapo/KeibaOS"
                or type(self.organization) is not str or self.organization != "NAR"
                or type(self.source_system) is not str or self.source_system != "nar_official"):
            raise ValueError("unsupported repository or provider scope")
        expected = (2, 2, 2, 1, 1, 1)
        values = (self.schema_version, self.instrumentation_schema_version,
                  self.sample_admission_semantic_version, self.execution_authority_semantic_version,
                  self.max_concurrent_target_workflows, self.max_concurrent_http_requests)
        if any(type(v) is not int or v != e for v, e in zip(values, expected)):
            raise ValueError("unsupported V2 version or concurrency count")
        if (type(self.retry_policy) is not NARRetryPolicy or type(self.max_retries) is not int
                or self.max_retries != 0 or type(self.backoff_microseconds) is not int
                or self.backoff_microseconds != 0):
            raise ValueError("V2 supports NO_RETRY with zero retries and backoff")
        if (type(self.concurrency_regime) is not NARConcurrencyRegime or
                type(self.race_list_acquisition_mode) is not NARRaceListAcquisitionMode):
            raise ValueError("unsupported declared concurrency regime")
        stages = self.enabled_stages
        if type(stages) is not tuple or not stages or any(type(s) is not NAROperationalTimingStageV2 for s in stages):
            raise ValueError("enabled stages must be nonempty exact V2 tuple")
        if len(set(stages)) != len(stages):
            raise ValueError("duplicate V2 stage")
        object.__setattr__(self, "enabled_stages", tuple(s for s in NAROperationalTimingStageV2 if s in stages))
        profiles = self.transport_profiles
        if type(profiles) is not tuple or any(type(p) is not NARHTTPTransportProfile for p in profiles):
            raise ValueError("transport profiles must be exact tuple")
        if len({p.kind for p in profiles}) != len(profiles):
            raise ValueError("duplicate transport profile")
        required = {_REQUIRED_TRANSPORT[s] for s in stages if s in _REQUIRED_TRANSPORT}
        if not required.issubset({p.kind for p in profiles}):
            raise ValueError("enabled transport family lacks a profile")
        object.__setattr__(self, "transport_profiles", tuple(p for kind in NARHTTPTransportKind
                                                              for p in profiles if p.kind is kind))
        object.__setattr__(self, "configuration_sha256", sha256(self.canonical_bytes()).hexdigest())

    @property
    def configuration_identity(self) -> str:
        return "nar-operational-timing-config-v2:" + self.configuration_sha256

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
            "execution_authority_semantic_version": self.execution_authority_semantic_version,
        }

    def canonical_bytes(self) -> bytes:
        return _json_bytes(self.payload())

    @classmethod
    def from_json(cls, value: str) -> NAROperationalTimingMeasurementConfigurationV2:
        p = _read_json(value)
        result = cls(
            software_commit_sha=p["software_commit_sha"],
            enabled_stages=tuple(NAROperationalTimingStageV2(s) for s in p["enabled_stages"]),
            transport_profiles=tuple(NARHTTPTransportProfile(NARHTTPTransportKind(x["kind"]),
                x["connect_timeout_microseconds"], x["read_timeout_microseconds"])
                for x in p["transport_profiles"]),
            **{k: p[k] for k in ("repository_identity", "organization", "source_system",
                "instrumentation_schema_version", "max_retries", "backoff_microseconds",
                "max_concurrent_target_workflows", "max_concurrent_http_requests",
                "sample_admission_semantic_version", "execution_authority_semantic_version",
                "schema_version")},
            retry_policy=NARRetryPolicy(p["retry_policy"]),
            concurrency_regime=NARConcurrencyRegime(p["concurrency_regime"]),
            race_list_acquisition_mode=NARRaceListAcquisitionMode(p["race_list_acquisition_mode"]),
        )
        if result.canonical_bytes() != value.encode("utf-8"):
            raise ValueError("V2 configuration JSON is not canonical")
        return result


@dataclass(frozen=True, slots=True)
class NAROperationalTimingMeasurementSessionV2:
    configuration: NAROperationalTimingMeasurementConfigurationV2
    measurement_start_at: datetime
    measurement_end_at: datetime
    sample_admission_rule: NARSampleAdmissionRuleV2 = NARSampleAdmissionRuleV2.ATTEMPT_ADMITTED_IN_HALF_OPEN_SESSION_WINDOW
    session_completion_rule: NARSessionCompletionRule = NARSessionCompletionRule.FIXED_WALL_CLOCK_END
    schema_version: int = 2
    session_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.configuration) is not NAROperationalTimingMeasurementConfigurationV2:
            raise ValueError("V2 session requires exact V2 configuration")
        start, end = _utc(self.measurement_start_at), _utc(self.measurement_end_at)
        if start >= end:
            raise ValueError("V2 session start must precede fixed end")
        if (type(self.sample_admission_rule) is not NARSampleAdmissionRuleV2
                or type(self.session_completion_rule) is not NARSessionCompletionRule
                or type(self.schema_version) is not int or self.schema_version != 2):
            raise ValueError("unsupported V2 session rule or version")
        object.__setattr__(self, "measurement_start_at", start)
        object.__setattr__(self, "measurement_end_at", end)
        object.__setattr__(self, "session_sha256", sha256(self.canonical_bytes()).hexdigest())

    @property
    def session_identity(self) -> str:
        return "nar-operational-timing-session-v2:" + self.session_sha256

    def admits(self, attempt_admitted_at: datetime) -> bool:
        value = _utc(attempt_admitted_at)
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
    def from_json(cls, value: str, configuration: NAROperationalTimingMeasurementConfigurationV2) -> NAROperationalTimingMeasurementSessionV2:
        p = _read_json(value)
        if p["measurement_configuration_identity"] != configuration.configuration_identity:
            raise ValueError("V2 session configuration contradicts archive")
        result = cls(configuration, _parse_time(p["measurement_start_at"]),
                     _parse_time(p["measurement_end_at"]),
                     NARSampleAdmissionRuleV2(p["sample_admission_rule"]),
                     NARSessionCompletionRule(p["session_completion_rule"]), p["schema_version"])
        if result.canonical_bytes() != value.encode("utf-8"):
            raise ValueError("V2 session JSON is not canonical")
        return result
