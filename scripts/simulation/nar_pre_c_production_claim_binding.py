"""Canonical durable binding content, never process capability or root permission."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, fields
from datetime import date, datetime, timezone


class NARPreCProductionClaimBindingError(ValueError):
    """Missing, contradictory or noncanonical binding authority."""


class NARPreCProductionClaimBindingConflict(NARPreCProductionClaimBindingError):
    """An immutable prestaged authority has already been bound differently."""


PREFIX = "nar-pre-c-production-claim-binding-v1:"
_PREFIXES = {
    "claim_identity": "nar-operational-timing-campaign-execution-v1:",
    "runtime_binding_identity": "nar-operational-timing-runtime-binding-v1:",
    "session_identity": "nar-operational-timing-session-v2:",
    "campaign_readiness_receipt_identity": "nar-operational-timing-campaign-readiness-v1:",
    "phase112_manifest_identity": "nar-pre-c-production-prestaged-input-manifest-v1:",
    "phase112_availability_receipt_identity": "nar-pre-c-production-prestaged-availability-receipt-v1:",
    "phase109_receipt_id": "",
}


def require_identity(value: str, prefix: str) -> None:
    if (type(value) is not str
            or re.fullmatch(re.escape(prefix) + r"[0-9a-f]{64}", value, re.ASCII) is None):
        raise NARPreCProductionClaimBindingError("exact canonical identity required")


def _utc(value: datetime) -> datetime:
    if (type(value) is not datetime or value.tzinfo is None
            or value.utcoffset() is None):
        raise NARPreCProductionClaimBindingError("aware prediction cutoff required")
    return value.astimezone(timezone.utc)


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


@dataclass(frozen=True, slots=True)
class NARPreCProductionClaimBindingV1:
    claim_identity: str
    runtime_binding_identity: str
    session_identity: str
    campaign_readiness_receipt_identity: str
    phase112_manifest_identity: str
    phase112_availability_receipt_identity: str
    phase109_receipt_id: str
    organization: str
    source_system: str
    external_race_id: str
    internal_race_id: int
    prediction_cutoff: datetime
    schema_version: int = 1

    def __post_init__(self) -> None:
        for name, prefix in _PREFIXES.items():
            require_identity(getattr(self, name), prefix)
        if (type(self.organization) is not str or self.organization != "NAR"
                or type(self.source_system) is not str or self.source_system != "nar_official"
                or type(self.schema_version) is not int or self.schema_version != 1
                or type(self.internal_race_id) is not int or self.internal_race_id <= 0):
            raise NARPreCProductionClaimBindingError("exact NAR binding scope required")
        match = (re.fullmatch(r"nar:([0-9]{8}):[1-9][0-9]*:[1-9][0-9]*",
                             self.external_race_id, re.ASCII)
                 if type(self.external_race_id) is str else None)
        if match is None:
            raise NARPreCProductionClaimBindingError("canonical external race required")
        day = match[1]
        try:
            date.fromisoformat(f"{day[:4]}-{day[4:6]}-{day[6:]}")
        except ValueError as exc:
            raise NARPreCProductionClaimBindingError("invalid external race date") from exc
        object.__setattr__(self, "prediction_cutoff", _utc(self.prediction_cutoff))

    def payload(self) -> dict[str, object]:
        result = {field.name: getattr(self, field.name) for field in fields(self)}
        result["prediction_cutoff"] = self.prediction_cutoff.isoformat()
        return result

    def canonical_json(self) -> str:
        return _json(self.payload())

    @property
    def identity(self) -> str:
        return PREFIX + hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


def parse_binding(value: str, expected_identity: str) -> NARPreCProductionClaimBindingV1:
    """Parse content only; archive authoritative load must revalidate upstreams."""
    require_identity(expected_identity, PREFIX)
    try:
        raw = json.loads(value)
        if type(raw) is not dict or set(raw) != {field.name for field in fields(NARPreCProductionClaimBindingV1)}:
            raise NARPreCProductionClaimBindingError("exact binding field set required")
        arguments = dict(raw)
        arguments["prediction_cutoff"] = datetime.fromisoformat(raw["prediction_cutoff"])
        result = NARPreCProductionClaimBindingV1(**arguments)
        if (raw != result.payload() or value != result.canonical_json()
                or result.identity != expected_identity):
            raise NARPreCProductionClaimBindingError("noncanonical binding content")
        return result
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise NARPreCProductionClaimBindingError("binding content is corrupt") from exc


def binding_row(value: NARPreCProductionClaimBindingV1) -> tuple[object, ...]:
    return (value.identity, value.claim_identity, value.runtime_binding_identity,
            value.session_identity, value.campaign_readiness_receipt_identity,
            value.phase112_manifest_identity, value.phase112_availability_receipt_identity,
            value.phase109_receipt_id, value.organization, value.source_system,
            value.external_race_id, value.internal_race_id,
            value.prediction_cutoff.isoformat(), value.schema_version, value.canonical_json())
