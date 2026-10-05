"""Content-addressed Phase112 mapping content and post-commit availability."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from scripts.simulation.nar_production_mapping_authority import (
    NARProductionMappingEntryV1,
    NARProductionMappingReceiptV1,
)


class NARPreCProductionPrestagingError(ValueError):
    """Exact upstream mapping or immutable prestaging evidence differs."""


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def _digest(value: object) -> str:
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _utc(value: datetime) -> datetime:
    if (type(value) is not datetime or value.tzinfo is None
            or value.utcoffset() is None):
        raise NARPreCProductionPrestagingError("aware UTC time required")
    return value.astimezone(timezone.utc)


def _sha(value: str) -> str:
    if (type(value) is not str or len(value) != 64
            or any(c not in "0123456789abcdef" for c in value)):
        raise NARPreCProductionPrestagingError("canonical SHA-256 required")
    return value


def _entries(value: object) -> tuple[NARProductionMappingEntryV1, ...]:
    if (type(value) is not tuple or not value
            or any(type(item) is not NARProductionMappingEntryV1 for item in value)
            or value != tuple(sorted(value, key=lambda item: item.horse_no))):
        raise NARPreCProductionPrestagingError("complete ordered mapping required")
    for field in ("external_entry_id", "race_entry_id", "horse_no"):
        if len({getattr(item, field) for item in value}) != len(value):
            raise NARPreCProductionPrestagingError("mapping is not bijective")
    return value


@dataclass(frozen=True, slots=True)
class NARPreCProductionPrestagedInputManifestV1:
    phase109_receipt_id: str
    external_race_id: str
    internal_race_id: int
    prediction_cutoff: datetime
    phase109_issued_at: datetime
    entries: tuple[NARProductionMappingEntryV1, ...]
    mapping_population_count: int
    mapping_population_sha256: str
    organization: str = "NAR"
    source_system: str = "nar_official"

    def __post_init__(self) -> None:
        _sha(self.phase109_receipt_id)
        _sha(self.mapping_population_sha256)
        if (self.organization != "NAR" or self.source_system != "nar_official"
                or type(self.external_race_id) is not str
                or not self.external_race_id.startswith("nar:")
                or type(self.internal_race_id) is not int or self.internal_race_id <= 0):
            raise NARPreCProductionPrestagingError("exact NAR target required")
        object.__setattr__(self, "prediction_cutoff", _utc(self.prediction_cutoff))
        object.__setattr__(self, "phase109_issued_at", _utc(self.phase109_issued_at))
        entries = _entries(self.entries)
        if (type(self.mapping_population_count) is not int
                or self.mapping_population_count != len(entries)
                or self.mapping_population_sha256 != _digest(
                    [item.payload() for item in entries])):
            raise NARPreCProductionPrestagingError("complete mapping digest/count differs")

    def payload(self) -> dict[str, object]:
        return {
            "schema": "nar-pre-c-production-prestaged-input-manifest-v1",
            "organization": self.organization,
            "source_system": self.source_system,
            "phase109_receipt_id": self.phase109_receipt_id,
            "external_race_id": self.external_race_id,
            "internal_race_id": self.internal_race_id,
            "prediction_cutoff": self.prediction_cutoff.isoformat(),
            "phase109_issued_at": self.phase109_issued_at.isoformat(),
            "entries": [item.payload() for item in self.entries],
            "mapping_population_count": self.mapping_population_count,
            "mapping_population_sha256": self.mapping_population_sha256,
        }

    @property
    def identity(self) -> str:
        return "nar-pre-c-production-prestaged-input-manifest-v1:" + _digest(self.payload())

    def canonical_json(self) -> str:
        return _json(self.payload())


@dataclass(frozen=True, slots=True)
class NARPreCProductionPrestagedAvailabilityReceiptV1:
    manifest_identity: str
    phase109_receipt_id: str
    available_at: datetime

    def __post_init__(self) -> None:
        prefix = "nar-pre-c-production-prestaged-input-manifest-v1:"
        if (type(self.manifest_identity) is not str
                or not self.manifest_identity.startswith(prefix)
                or len(self.manifest_identity) != len(prefix) + 64):
            raise NARPreCProductionPrestagingError("exact manifest identity required")
        _sha(self.manifest_identity[len(prefix):])
        _sha(self.phase109_receipt_id)
        if (type(self.available_at) is not datetime
                or self.available_at.tzinfo is None
                or self.available_at.utcoffset() != timedelta(0)):
            raise NARPreCProductionPrestagingError("controlled aware UTC availability required")
        object.__setattr__(self, "available_at", _utc(self.available_at))

    def payload(self) -> dict[str, object]:
        return {
            "schema": "nar-pre-c-production-prestaged-availability-receipt-v1",
            "manifest_identity": self.manifest_identity,
            "phase109_receipt_id": self.phase109_receipt_id,
            "available_at": self.available_at.isoformat(),
        }

    @property
    def identity(self) -> str:
        return "nar-pre-c-production-prestaged-availability-receipt-v1:" + _digest(self.payload())

    def canonical_json(self) -> str:
        return _json(self.payload())


@dataclass(frozen=True, slots=True)
class NARPreCProductionPrestagedAuthorityV1:
    manifest: NARPreCProductionPrestagedInputManifestV1
    availability_receipt: NARPreCProductionPrestagedAvailabilityReceiptV1

    def __post_init__(self) -> None:
        if (type(self.manifest) is not NARPreCProductionPrestagedInputManifestV1
                or type(self.availability_receipt)
                is not NARPreCProductionPrestagedAvailabilityReceiptV1
                or self.availability_receipt.manifest_identity != self.manifest.identity
                or self.availability_receipt.phase109_receipt_id != self.manifest.phase109_receipt_id
                or self.availability_receipt.available_at < self.manifest.phase109_issued_at):
            raise NARPreCProductionPrestagingError("prestaging pair differs")


def manifest_from_phase109(
    source: NARProductionMappingReceiptV1,
) -> NARPreCProductionPrestagedInputManifestV1:
    if type(source) is not NARProductionMappingReceiptV1:
        raise NARPreCProductionPrestagingError("exact Phase109 receipt required")
    return NARPreCProductionPrestagedInputManifestV1(
        source.receipt_id, source.external_race_id, source.internal_race_id,
        source.prediction_cutoff, source.issued_at, source.entries,
        len(source.entries), source.mapping_population_sha256,
    )


def parse_manifest(value: str, expected_identity: str) -> NARPreCProductionPrestagedInputManifestV1:
    try:
        raw = json.loads(value)
        entries = tuple(NARProductionMappingEntryV1(**item) for item in raw["entries"])
        result = NARPreCProductionPrestagedInputManifestV1(
            raw["phase109_receipt_id"], raw["external_race_id"], raw["internal_race_id"],
            datetime.fromisoformat(raw["prediction_cutoff"]),
            datetime.fromisoformat(raw["phase109_issued_at"]), entries,
            raw["mapping_population_count"], raw["mapping_population_sha256"],
            raw["organization"], raw["source_system"],
        )
        if (type(raw) is not dict or raw != result.payload()
                or value != result.canonical_json() or result.identity != expected_identity):
            raise NARPreCProductionPrestagingError("noncanonical manifest")
        return result
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise NARPreCProductionPrestagingError("manifest content is corrupt") from exc


def parse_availability(
    value: str, expected_identity: str,
) -> NARPreCProductionPrestagedAvailabilityReceiptV1:
    try:
        raw = json.loads(value)
        result = NARPreCProductionPrestagedAvailabilityReceiptV1(
            raw["manifest_identity"], raw["phase109_receipt_id"],
            datetime.fromisoformat(raw["available_at"]),
        )
        if (type(raw) is not dict or raw != result.payload()
                or value != result.canonical_json() or result.identity != expected_identity):
            raise NARPreCProductionPrestagingError("noncanonical availability receipt")
        return result
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise NARPreCProductionPrestagingError("availability receipt is corrupt") from exc
