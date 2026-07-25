"""Allocation-policy configuration contracts and deterministic identities."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
from types import MappingProxyType
from typing import TypeAlias


JsonScalar: TypeAlias = str | int | bool | None
JsonValue: TypeAlias = (
    JsonScalar
    | list["JsonValue"]
    | tuple["JsonValue", ...]
    | Mapping[str, "JsonValue"]
)
FrozenJsonValue: TypeAlias = JsonScalar | tuple["FrozenJsonValue", ...] | Mapping[str, "FrozenJsonValue"]

_POLICY_SCHEMA_VERSION = 1
_SHA256_HEX = frozenset("0123456789abcdef")


def _validate_text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _freeze_json_value(value: object, active_container_ids: set[int]) -> FrozenJsonValue:
    if isinstance(value, bool):
        return value
    if isinstance(value, str) or value is None:
        return value
    if isinstance(value, int):
        return value

    if isinstance(value, Mapping):
        container_id = id(value)
        if container_id in active_container_ids:
            raise ValueError("parameters must not contain circular containers")
        active_container_ids.add(container_id)
        try:
            copied: dict[str, FrozenJsonValue] = {}
            keys = tuple(value)
            if not all(isinstance(key, str) for key in keys):
                raise ValueError("parameter mapping keys must be strings")
            for key in sorted(keys):
                copied[key] = _freeze_json_value(value[key], active_container_ids)
            return MappingProxyType(copied)
        finally:
            active_container_ids.remove(container_id)

    if isinstance(value, list | tuple):
        container_id = id(value)
        if container_id in active_container_ids:
            raise ValueError("parameters must not contain circular containers")
        active_container_ids.add(container_id)
        try:
            return tuple(_freeze_json_value(item, active_container_ids) for item in value)
        finally:
            active_container_ids.remove(container_id)

    raise ValueError("parameters must contain only supported JSON values")


def _plain_json_value(value: object, active_container_ids: set[int]) -> object:
    if isinstance(value, bool):
        return value
    if isinstance(value, str) or value is None:
        return value
    if isinstance(value, int):
        return value

    if isinstance(value, Mapping):
        container_id = id(value)
        if container_id in active_container_ids:
            raise ValueError("parameters must not contain circular containers")
        active_container_ids.add(container_id)
        try:
            result: dict[str, object] = {}
            keys = tuple(value)
            if not all(isinstance(key, str) for key in keys):
                raise ValueError("parameter mapping keys must be strings")
            for key in sorted(keys):
                result[key] = _plain_json_value(value[key], active_container_ids)
            return result
        finally:
            active_container_ids.remove(container_id)

    if isinstance(value, list | tuple):
        container_id = id(value)
        if container_id in active_container_ids:
            raise ValueError("parameters must not contain circular containers")
        active_container_ids.add(container_id)
        try:
            return [_plain_json_value(item, active_container_ids) for item in value]
        finally:
            active_container_ids.remove(container_id)

    raise ValueError("parameters must contain only supported JSON values")


@dataclass(frozen=True, slots=True)
class AllocationPolicyConfig:
    """Immutable policy name, version, and JSON-compatible parameters."""

    policy_name: str
    policy_version: str
    parameters: Mapping[str, JsonValue]

    def __post_init__(self) -> None:
        _validate_text(self.policy_name, "policy_name")
        _validate_text(self.policy_version, "policy_version")
        if not isinstance(self.parameters, Mapping):
            raise ValueError("parameters must be a Mapping")
        object.__setattr__(self, "parameters", _freeze_json_value(self.parameters, set()))


@dataclass(frozen=True, slots=True)
class AllocationPolicyIdentity:
    """Derived, reproducible identifier for an allocation-policy configuration."""

    policy_name: str
    policy_version: str
    policy_config_hash: str

    def __post_init__(self) -> None:
        _validate_text(self.policy_name, "policy_name")
        _validate_text(self.policy_version, "policy_version")
        if (
            not isinstance(self.policy_config_hash, str)
            or len(self.policy_config_hash) != 64
            or any(character not in _SHA256_HEX for character in self.policy_config_hash)
        ):
            raise ValueError("policy_config_hash must be a lowercase SHA-256 digest")


def canonicalize_allocation_policy_parameters(
    parameters: Mapping[str, JsonValue],
) -> dict[str, object]:
    """Return a deterministic plain JSON tree without mutating ``parameters``."""
    if not isinstance(parameters, Mapping):
        raise ValueError("parameters must be a Mapping")
    normalized = _plain_json_value(parameters, set())
    if not isinstance(normalized, dict):  # Defensive: Mapping inputs always normalize to dict.
        raise ValueError("parameters must normalize to a JSON object")
    return normalized


def allocation_policy_config_payload(config: AllocationPolicyConfig) -> dict[str, object]:
    """Build the fixed-schema plain JSON payload for a policy configuration."""
    if not isinstance(config, AllocationPolicyConfig):
        raise ValueError("config must be an AllocationPolicyConfig")
    return {
        "schema_version": _POLICY_SCHEMA_VERSION,
        "policy_name": config.policy_name,
        "policy_version": config.policy_version,
        "parameters": canonicalize_allocation_policy_parameters(config.parameters),
    }


def allocation_policy_config_hash(config: AllocationPolicyConfig) -> str:
    """Return the SHA-256 digest of the canonical policy payload."""
    payload = allocation_policy_config_payload(config)
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_allocation_policy_identity(config: AllocationPolicyConfig) -> AllocationPolicyIdentity:
    """Derive an identity solely from an ``AllocationPolicyConfig``."""
    if not isinstance(config, AllocationPolicyConfig):
        raise ValueError("config must be an AllocationPolicyConfig")
    return AllocationPolicyIdentity(
        policy_name=config.policy_name,
        policy_version=config.policy_version,
        policy_config_hash=allocation_policy_config_hash(config),
    )
