"""Immutable Phase105 evidence. An attempt is not, by itself, an official sample."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from hashlib import sha256
import re

from scripts.simulation.nar_operational_timing_observability import (
    NARTimingCorrelation, NARTimingLoadContext, _digest, _json_bytes, _parse_time,
    _read_json, _time, _utc,
)
from scripts.simulation.nar_operational_timing_observability_v2 import (
    NAROperationalTimingStageV2, _REQUIRED_TRANSPORT,
)


_CONFIG = re.compile(r"nar-operational-timing-config-v2:[0-9a-f]{64}\Z")
_SESSION = re.compile(r"nar-operational-timing-session-v2:[0-9a-f]{64}\Z")
_CLAIM = re.compile(r"nar-operational-timing-campaign-execution-v1:[0-9a-f]{64}\Z")
_ATTEMPT = re.compile(r"nar-operational-timing-attempt-v2:[0-9a-f]{64}\Z")


def _require_identity(value: str, pattern: re.Pattern[str]) -> None:
    if type(value) is not str or pattern.fullmatch(value) is None:
        raise ValueError("unsupported timing authority identity")


class NARExpectedRequestEnvironmentPolicy(StrEnum):
    DIRECT_REQUEST_ENVIRONMENT_V1 = "DIRECT_REQUEST_ENVIRONMENT_V1"


class NARTimingTerminalDispositionV2(StrEnum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    TIMEOUT = "TIMEOUT"
    UNSUPPORTED = "UNSUPPORTED"


class NARTimingFailureClassificationV2(StrEnum):
    CONNECT_TIMEOUT = "CONNECT_TIMEOUT"
    READ_TIMEOUT = "READ_TIMEOUT"
    TRANSPORT = "TRANSPORT"
    VALIDATION = "VALIDATION"
    PERSISTENCE = "PERSISTENCE"
    UNSUPPORTED = "UNSUPPORTED"
    INTERNAL = "INTERNAL"


class NARRequestEnvironmentQualification(StrEnum):
    QUALIFIED_DIRECT_REQUEST_ENVIRONMENT = "QUALIFIED_DIRECT_REQUEST_ENVIRONMENT"
    NONQUALIFYING_REQUEST_ENVIRONMENT = "NONQUALIFYING_REQUEST_ENVIRONMENT"


class NARSafeSendSetting(StrEnum):
    DIRECT = "DIRECT"
    NONEMPTY = "NONEMPTY"
    TRUE = "TRUE"
    OTHER = "OTHER"
    ABSENT = "ABSENT"
    PRESENT = "PRESENT"


@dataclass(frozen=True, slots=True)
class NAROperationalTimingAttemptV2:
    configuration_identity: str
    session_identity: str
    campaign_execution_identity: str
    stage: NAROperationalTimingStageV2
    correlation: NARTimingCorrelation
    attempt_sequence: int
    attempt_admitted_at: datetime
    load_context: NARTimingLoadContext
    expected_http_environment_policy: NARExpectedRequestEnvironmentPolicy | None = None
    expected_request_url_sha256: str | None = None
    schema_version: int = 2
    attempt_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        _require_identity(self.configuration_identity, _CONFIG)
        _require_identity(self.session_identity, _SESSION)
        _require_identity(self.campaign_execution_identity, _CLAIM)
        if type(self.stage) is not NAROperationalTimingStageV2:
            raise ValueError("exact V2 stage required")
        if type(self.correlation) is not NARTimingCorrelation or type(self.load_context) is not NARTimingLoadContext:
            raise ValueError("exact correlation and load context required")
        if type(self.attempt_sequence) is not int or self.attempt_sequence < 0 or type(self.schema_version) is not int or self.schema_version != 2:
            raise ValueError("invalid attempt sequence or version")
        if self.stage in _REQUIRED_TRANSPORT:
            if type(self.expected_http_environment_policy) is not NARExpectedRequestEnvironmentPolicy:
                raise ValueError("HTTP stage requires a closed expected environment policy")
            _digest(self.expected_request_url_sha256)
        elif self.expected_http_environment_policy is not None or self.expected_request_url_sha256 is not None:
            raise ValueError("non-HTTP stage cannot assert HTTP policy or URL")
        object.__setattr__(self, "attempt_admitted_at", _utc(self.attempt_admitted_at))
        object.__setattr__(self, "attempt_sha256", sha256(self.canonical_bytes()).hexdigest())

    @property
    def attempt_identity(self) -> str:
        return "nar-operational-timing-attempt-v2:" + self.attempt_sha256

    def payload(self) -> dict[str, object]:
        return {"schema_version": self.schema_version, "configuration_identity": self.configuration_identity,
                "session_identity": self.session_identity, "campaign_execution_identity": self.campaign_execution_identity,
                "stage": self.stage.value, "correlation": self.correlation.payload(),
                "attempt_sequence": self.attempt_sequence, "attempt_admitted_at": _time(self.attempt_admitted_at),
                "load_context": self.load_context.payload(),
                "expected_http_environment_policy": self.expected_http_environment_policy.value if self.expected_http_environment_policy else None,
                "expected_request_url_sha256": self.expected_request_url_sha256}

    def canonical_bytes(self) -> bytes:
        return _json_bytes(self.payload())

    @classmethod
    def from_json(cls, value: str) -> NAROperationalTimingAttemptV2:
        p = _read_json(value)
        if set(p) != {"schema_version", "configuration_identity", "session_identity", "campaign_execution_identity", "stage",
                      "correlation", "attempt_sequence", "attempt_admitted_at", "load_context", "expected_http_environment_policy",
                      "expected_request_url_sha256"}:
            raise ValueError("attempt payload fields are invalid")
        policy = p["expected_http_environment_policy"]
        result = cls(p["configuration_identity"], p["session_identity"], p["campaign_execution_identity"],
                     NAROperationalTimingStageV2(p["stage"]), NARTimingCorrelation.from_payload(p["correlation"]),
                     p["attempt_sequence"], _parse_time(p["attempt_admitted_at"]),
                     NARTimingLoadContext.from_payload(p["load_context"]),
                     NARExpectedRequestEnvironmentPolicy(policy) if policy is not None else None,
                     p["expected_request_url_sha256"],
                     p["schema_version"])
        if result.payload() != p:
            raise ValueError("attempt payload is contradictory")
        return result


@dataclass(frozen=True, slots=True)
class NAROperationalTimingTerminalV2:
    attempt_identity: str
    operation_finished_at: datetime
    elapsed_microseconds: int
    disposition: NARTimingTerminalDispositionV2
    failure_classification: NARTimingFailureClassificationV2 | None = None
    artifact_sha256: str | None = None
    schema_version: int = 2
    terminal_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        _require_identity(self.attempt_identity, _ATTEMPT)
        object.__setattr__(self, "operation_finished_at", _utc(self.operation_finished_at))
        if type(self.elapsed_microseconds) is not int or self.elapsed_microseconds < 0 or type(self.schema_version) is not int or self.schema_version != 2:
            raise ValueError("terminal duration/version must be exact")
        if type(self.disposition) is not NARTimingTerminalDispositionV2:
            raise ValueError("closed terminal disposition required")
        if self.disposition is NARTimingTerminalDispositionV2.SUCCESS:
            if self.failure_classification is not None:
                raise ValueError("success has no failure classification")
        elif type(self.failure_classification) is not NARTimingFailureClassificationV2:
            raise ValueError("non-success requires exact failure classification")
        elif ((self.disposition is NARTimingTerminalDispositionV2.TIMEOUT) !=
              (self.failure_classification in (NARTimingFailureClassificationV2.CONNECT_TIMEOUT,
                                               NARTimingFailureClassificationV2.READ_TIMEOUT))):
            raise ValueError("timeout disposition/classification contradict")
        if self.disposition is NARTimingTerminalDispositionV2.UNSUPPORTED and self.failure_classification is not NARTimingFailureClassificationV2.UNSUPPORTED:
            raise ValueError("unsupported disposition/classification contradict")
        if self.disposition is NARTimingTerminalDispositionV2.FAILURE and self.failure_classification is NARTimingFailureClassificationV2.UNSUPPORTED:
            raise ValueError("unsupported failure requires unsupported disposition")
        if self.artifact_sha256 is not None:
            _digest(self.artifact_sha256)
        object.__setattr__(self, "terminal_sha256", sha256(self.canonical_bytes()).hexdigest())

    @property
    def terminal_identity(self) -> str:
        return "nar-operational-timing-terminal-v2:" + self.terminal_sha256

    def payload(self) -> dict[str, object]:
        return {"schema_version": self.schema_version, "attempt_identity": self.attempt_identity,
                "operation_finished_at": _time(self.operation_finished_at), "elapsed_microseconds": self.elapsed_microseconds,
                "disposition": self.disposition.value,
                "failure_classification": self.failure_classification.value if self.failure_classification else None,
                "artifact_sha256": self.artifact_sha256}

    def canonical_bytes(self) -> bytes:
        return _json_bytes(self.payload())

    @classmethod
    def from_json(cls, value: str) -> NAROperationalTimingTerminalV2:
        p = _read_json(value)
        if set(p) != {"schema_version", "attempt_identity", "operation_finished_at", "elapsed_microseconds", "disposition", "failure_classification", "artifact_sha256"}:
            raise ValueError("terminal payload fields are invalid")
        classification = p["failure_classification"]
        result = cls(p["attempt_identity"], _parse_time(p["operation_finished_at"]), p["elapsed_microseconds"],
                     NARTimingTerminalDispositionV2(p["disposition"]),
                     NARTimingFailureClassificationV2(classification) if classification is not None else None,
                     p["artifact_sha256"], p["schema_version"])
        if result.payload() != p:
            raise ValueError("terminal payload is contradictory")
        return result


@dataclass(frozen=True, slots=True)
class NARRequestEffectiveEnvironmentVerification:
    attempt_identity: str
    prepared_url_sha256: str
    transport_profile_identity: str
    trust_env: bool
    proxy_state: NARSafeSendSetting
    verify_state: NARSafeSendSetting
    cert_state: NARSafeSendSetting
    authorization_state: NARSafeSendSetting
    proxy_authorization_state: NARSafeSendSetting
    expected_url_match: bool
    static_profile_match: bool
    qualification: NARRequestEnvironmentQualification
    direct_policy: NARExpectedRequestEnvironmentPolicy = NARExpectedRequestEnvironmentPolicy.DIRECT_REQUEST_ENVIRONMENT_V1
    schema_version: int = 1
    verification_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        _require_identity(self.attempt_identity, _ATTEMPT)
        _digest(self.prepared_url_sha256)
        if type(self.transport_profile_identity) is not str or re.fullmatch(r"nar-static-runtime-transport-profile-v1:[0-9a-f]{64}", self.transport_profile_identity) is None:
            raise ValueError("exact static transport profile identity required")
        if type(self.trust_env) is not bool or type(self.schema_version) is not int or self.schema_version != 1:
            raise ValueError("environment verification version/trust mode invalid")
        for setting in (self.proxy_state, self.verify_state, self.cert_state, self.authorization_state, self.proxy_authorization_state):
            if type(setting) is not NARSafeSendSetting:
                raise ValueError("environment material must use closed safe states")
        if type(self.expected_url_match) is not bool or type(self.static_profile_match) is not bool:
            raise ValueError("environment ancestry checks must be exact booleans")
        if type(self.direct_policy) is not NARExpectedRequestEnvironmentPolicy or type(self.qualification) is not NARRequestEnvironmentQualification:
            raise ValueError("closed request policy/qualification required")
        direct = (self.proxy_state is NARSafeSendSetting.DIRECT and self.verify_state is NARSafeSendSetting.TRUE
                  and self.cert_state is NARSafeSendSetting.ABSENT
                  and self.authorization_state is NARSafeSendSetting.ABSENT
                  and self.proxy_authorization_state is NARSafeSendSetting.ABSENT
                  and self.expected_url_match and self.static_profile_match)
        if (self.qualification is NARRequestEnvironmentQualification.QUALIFIED_DIRECT_REQUEST_ENVIRONMENT) != direct:
            raise ValueError("direct qualification contradicts observed safe states")
        object.__setattr__(self, "verification_sha256", sha256(self.canonical_bytes()).hexdigest())

    @property
    def verification_identity(self) -> str:
        return "nar-request-effective-environment-verification-v1:" + self.verification_sha256

    def payload(self) -> dict[str, object]:
        return {"schema_version": self.schema_version, "attempt_identity": self.attempt_identity,
                "prepared_url_sha256": self.prepared_url_sha256, "transport_profile_identity": self.transport_profile_identity,
                "trust_env": self.trust_env, "proxy_state": self.proxy_state.value, "verify_state": self.verify_state.value,
                "cert_state": self.cert_state.value, "authorization_state": self.authorization_state.value,
                "proxy_authorization_state": self.proxy_authorization_state.value,
                "expected_url_match": self.expected_url_match, "static_profile_match": self.static_profile_match,
                "qualification": self.qualification.value, "direct_policy": self.direct_policy.value}

    def canonical_bytes(self) -> bytes:
        return _json_bytes(self.payload())

    @classmethod
    def from_json(cls, value: str) -> NARRequestEffectiveEnvironmentVerification:
        p = _read_json(value)
        if set(p) != {"schema_version", "attempt_identity", "prepared_url_sha256", "transport_profile_identity", "trust_env", "proxy_state", "verify_state", "cert_state", "authorization_state", "proxy_authorization_state", "expected_url_match", "static_profile_match", "qualification", "direct_policy"}:
            raise ValueError("environment payload fields are invalid")
        result = cls(p["attempt_identity"], p["prepared_url_sha256"], p["transport_profile_identity"], p["trust_env"],
                     NARSafeSendSetting(p["proxy_state"]), NARSafeSendSetting(p["verify_state"]),
                     NARSafeSendSetting(p["cert_state"]), NARSafeSendSetting(p["authorization_state"]),
                     NARSafeSendSetting(p["proxy_authorization_state"]),
                     p["expected_url_match"], p["static_profile_match"],
                     NARRequestEnvironmentQualification(p["qualification"]),
                     NARExpectedRequestEnvironmentPolicy(p["direct_policy"]), p["schema_version"])
        if result.payload() != p:
            raise ValueError("environment payload is contradictory")
        return result


def elapsed_microseconds_from_ns(start_ns: int, finish_ns: int) -> int:
    if type(start_ns) is not int or type(finish_ns) is not int or finish_ns < start_ns:
        raise ValueError("monotonic endpoints must be ordered exact integers")
    return (finish_ns - start_ns) // 1000


@dataclass(frozen=True, slots=True)
class NARTimingPublicationOverheadV2:
    """Nonrecursive publication cost; never another operation attempt."""

    campaign_execution_identity: str
    attempt_identity: str
    stage: NAROperationalTimingStageV2
    elapsed_microseconds: int
    schema_version: int = 1
    overhead_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        _require_identity(self.campaign_execution_identity, _CLAIM)
        _require_identity(self.attempt_identity, _ATTEMPT)
        if type(self.stage) is not NAROperationalTimingStageV2 or self.stage not in (NAROperationalTimingStageV2.ATTEMPT_START_PUBLICATION,
                              NAROperationalTimingStageV2.TERMINAL_PUBLICATION):
            raise ValueError("only closed nonrecursive publication overhead stages are supported")
        if (type(self.elapsed_microseconds) is not int or self.elapsed_microseconds < 0
                or type(self.schema_version) is not int or self.schema_version != 1):
            raise ValueError("invalid exact publication overhead")
        object.__setattr__(self, "overhead_sha256", sha256(self.canonical_bytes()).hexdigest())

    @property
    def overhead_identity(self) -> str:
        return "nar-operational-timing-publication-overhead-v1:" + self.overhead_sha256

    def payload(self) -> dict[str, object]:
        return {"schema_version": self.schema_version, "campaign_execution_identity": self.campaign_execution_identity,
                "attempt_identity": self.attempt_identity, "stage": self.stage.value,
                "elapsed_microseconds": self.elapsed_microseconds}

    def canonical_bytes(self) -> bytes:
        return _json_bytes(self.payload())

    @classmethod
    def from_json(cls, value: str) -> NARTimingPublicationOverheadV2:
        p = _read_json(value)
        if set(p) != {"schema_version", "campaign_execution_identity", "attempt_identity", "stage", "elapsed_microseconds"}:
            raise ValueError("publication overhead payload fields are invalid")
        result = cls(p["campaign_execution_identity"], p["attempt_identity"],
                     NAROperationalTimingStageV2(p["stage"]), p["elapsed_microseconds"], p["schema_version"])
        if result.payload() != p:
            raise ValueError("publication overhead payload is contradictory")
        return result
