"""Immutable runtime, one-shot execution, and causal readiness values."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from hashlib import sha256
import re

from scripts.simulation.nar_operational_timing_observability import _json_bytes, _read_json, _parse_time, _time, _utc


_PREFIXES = {
    "configuration_identity": "nar-operational-timing-config-v2:",
    "session_identity": "nar-operational-timing-session-v2:",
    "declaration_identity": "nar-operational-timing-activation-declaration-v2:",
    "verification_identity": "nar-operational-timing-activation-verification-v2:",
    "bundle_identity": "nar-runtime-source-bundle-v1:",
    "dependency_profile_identity": "nar-runtime-dependency-profile-v1:",
    "transport_profile_identity": "nar-static-runtime-transport-profile-v1:",
    "binding_identity": "nar-operational-timing-runtime-binding-v1:",
    "claim_identity": "nar-operational-timing-campaign-execution-v1:",
    "lock_scope_identity": "nar-operational-timing-lock-scope-v1:",
}


def _identity(name: str, value: str) -> None:
    prefix = _PREFIXES[name]
    if type(value) is not str or re.fullmatch(re.escape(prefix) + r"[0-9a-f]{64}", value) is None:
        raise ValueError(f"invalid {name}")


@dataclass(frozen=True, slots=True)
class NAROperationalTimingRuntimeBinding:
    configuration_identity: str
    session_identity: str
    declaration_identity: str
    verification_identity: str
    bundle_identity: str
    dependency_profile_identity: str
    transport_profile_identity: str
    lock_scope_identity: str
    concurrency_semantic: str = "CONTROLLED_SINGLE_WORKER_SERIAL_V1"
    instrumentation_schema_version: int = 2
    schema_version: int = 1
    binding_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        for name in _PREFIXES.keys() & self.__dataclass_fields__.keys():
            _identity(name, getattr(self, name))
        if (type(self.concurrency_semantic) is not str
                or self.concurrency_semantic != "CONTROLLED_SINGLE_WORKER_SERIAL_V1"
                or type(self.instrumentation_schema_version) is not int
                or self.instrumentation_schema_version != 2
                or type(self.schema_version) is not int or self.schema_version != 1):
            raise ValueError("unsupported runtime binding semantic")
        object.__setattr__(self, "binding_sha256", sha256(self.canonical_bytes()).hexdigest())

    @property
    def binding_identity(self) -> str:
        return "nar-operational-timing-runtime-binding-v1:" + self.binding_sha256

    def payload(self) -> dict[str, object]:
        names = ("configuration_identity", "session_identity", "declaration_identity",
                 "verification_identity", "bundle_identity", "dependency_profile_identity",
                 "transport_profile_identity", "lock_scope_identity", "concurrency_semantic",
                 "instrumentation_schema_version", "schema_version")
        return {name: getattr(self, name) for name in names}

    def canonical_bytes(self) -> bytes:
        return _json_bytes(self.payload())

    @classmethod
    def from_json(cls, value: str) -> NAROperationalTimingRuntimeBinding:
        result = cls(**_read_json(value))
        if result.canonical_bytes() != value.encode("utf-8"):
            raise ValueError("runtime binding JSON is not canonical")
        return result


@dataclass(frozen=True, slots=True)
class NAROperationalTimingCampaignExecutionClaim:
    configuration_identity: str
    session_identity: str
    declaration_identity: str
    verification_identity: str
    binding_identity: str
    bundle_identity: str
    lock_scope_identity: str
    runner_semantic: str = "CONTROLLED_ONE_SHOT_CAMPAIGN_RUNNER_V1"
    instrumentation_schema_version: int = 2
    schema_version: int = 1
    claim_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        for name in _PREFIXES.keys() & self.__dataclass_fields__.keys():
            _identity(name, getattr(self, name))
        if (type(self.runner_semantic) is not str
                or self.runner_semantic != "CONTROLLED_ONE_SHOT_CAMPAIGN_RUNNER_V1"
                or type(self.instrumentation_schema_version) is not int
                or self.instrumentation_schema_version != 2
                or type(self.schema_version) is not int or self.schema_version != 1):
            raise ValueError("unsupported execution claim semantic")
        object.__setattr__(self, "claim_sha256", sha256(self.canonical_bytes()).hexdigest())

    @property
    def claim_identity(self) -> str:
        return "nar-operational-timing-campaign-execution-v1:" + self.claim_sha256

    def payload(self) -> dict[str, object]:
        names = ("configuration_identity", "session_identity", "declaration_identity",
                 "verification_identity", "binding_identity", "bundle_identity",
                 "lock_scope_identity", "runner_semantic", "instrumentation_schema_version",
                 "schema_version")
        return {name: getattr(self, name) for name in names}

    def canonical_bytes(self) -> bytes:
        return _json_bytes(self.payload())

    @classmethod
    def from_json(cls, value: str) -> NAROperationalTimingCampaignExecutionClaim:
        result = cls(**_read_json(value))
        if result.canonical_bytes() != value.encode("utf-8"):
            raise ValueError("execution claim JSON is not canonical")
        return result


class NARCampaignReadinessState(StrEnum):
    OFFICIAL_PRESTART_RUNTIME_READY = "OFFICIAL_PRESTART_RUNTIME_READY"
    RUNTIME_READY_AFTER_SESSION_START = "RUNTIME_READY_AFTER_SESSION_START"


@dataclass(frozen=True, slots=True)
class NAROperationalTimingCampaignReadinessVerificationReceipt:
    configuration_identity: str
    session_identity: str
    binding_identity: str
    claim_identity: str
    readiness_verified_at: datetime
    semantic: str = "BINDING_AND_CLAIM_COMMITTED_AND_EXACT_RELOAD_VERIFIED"
    schema_version: int = 1
    receipt_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        for name in _PREFIXES.keys() & self.__dataclass_fields__.keys():
            _identity(name, getattr(self, name))
        if (type(self.semantic) is not str
                or self.semantic != "BINDING_AND_CLAIM_COMMITTED_AND_EXACT_RELOAD_VERIFIED"
                or type(self.schema_version) is not int or self.schema_version != 1):
            raise ValueError("unsupported readiness semantic")
        object.__setattr__(self, "readiness_verified_at", _utc(self.readiness_verified_at))
        object.__setattr__(self, "receipt_sha256", sha256(self.canonical_bytes()).hexdigest())

    @property
    def receipt_identity(self) -> str:
        return "nar-operational-timing-campaign-readiness-v1:" + self.receipt_sha256

    def payload(self) -> dict[str, object]:
        return {"configuration_identity": self.configuration_identity,
                "session_identity": self.session_identity,
                "binding_identity": self.binding_identity,
                "claim_identity": self.claim_identity,
                "readiness_verified_at": _time(self.readiness_verified_at),
                "semantic": self.semantic, "schema_version": self.schema_version}

    def canonical_bytes(self) -> bytes:
        return _json_bytes(self.payload())

    @classmethod
    def from_json(cls, value: str) -> NAROperationalTimingCampaignReadinessVerificationReceipt:
        p = _read_json(value)
        result = cls(p["configuration_identity"], p["session_identity"], p["binding_identity"],
                     p["claim_identity"], _parse_time(p["readiness_verified_at"]),
                     p["semantic"], p["schema_version"])
        if result.canonical_bytes() != value.encode("utf-8"):
            raise ValueError("readiness JSON is not canonical")
        return result
