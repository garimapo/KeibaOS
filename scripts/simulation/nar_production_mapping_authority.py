"""Content-addressed, status-neutral Phase109 production mapping values."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime

from scripts.simulation.nar_identity_complete_entry_persistence import (
    NARIdentityCompleteReceiptV1,
)


class NARProductionMappingError(ValueError):
    """Required mapping provenance or exact content is absent/contradictory."""


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def _sha(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class NARProductionMappingEntryV1:
    external_entry_id: str
    race_entry_id: int
    horse_no: int

    def __post_init__(self) -> None:
        if (type(self.external_entry_id) is not str or not self.external_entry_id
                or type(self.race_entry_id) is not int or self.race_entry_id <= 0
                or type(self.horse_no) is not int or self.horse_no <= 0):
            raise NARProductionMappingError("exact positive mapping entry required")

    def payload(self) -> dict[str, object]:
        return {"external_entry_id": self.external_entry_id,
                "race_entry_id": self.race_entry_id, "horse_no": self.horse_no}


@dataclass(frozen=True, slots=True)
class NARProductionMappingReceiptV1:
    external_race_id: str
    internal_race_id: int
    canonical_deba_url: str
    phase110_receipt_id: str
    phase110_population_sha256: str
    phase110_population_count: int
    phase110_issued_at: datetime
    phase111_declaration_id: str
    phase111_receipt_id: str
    phase111_capture_id: str
    response_sha256: str
    observed_at: datetime
    prediction_cutoff: datetime
    issued_at: datetime
    entries: tuple[NARProductionMappingEntryV1, ...]

    def __post_init__(self) -> None:
        if type(self.internal_race_id) is not int or self.internal_race_id <= 0:
            raise NARProductionMappingError("positive internal race required")
        for value in (self.external_race_id, self.canonical_deba_url,
                      self.phase110_receipt_id, self.phase111_declaration_id,
                      self.phase111_receipt_id, self.phase111_capture_id):
            if type(value) is not str or not value or value.strip() != value:
                raise NARProductionMappingError("exact lineage text required")
        for value in (self.phase110_population_sha256, self.response_sha256):
            if (type(value) is not str or len(value) != 64
                    or any(c not in "0123456789abcdef" for c in value)):
                raise NARProductionMappingError("exact SHA-256 required")
        for value in (self.phase110_issued_at, self.observed_at,
                      self.prediction_cutoff, self.issued_at):
            if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
                raise NARProductionMappingError("aware chronology required")
        if (self.observed_at > self.prediction_cutoff
                or self.phase110_issued_at > self.issued_at):
            raise NARProductionMappingError("mapping chronology differs")
        if (type(self.entries) is not tuple or not self.entries
                or any(type(item) is not NARProductionMappingEntryV1 for item in self.entries)
                or tuple(sorted(self.entries, key=lambda item: item.horse_no)) != self.entries):
            raise NARProductionMappingError("canonical complete mapping required")
        if type(self.phase110_population_count) is not int or self.phase110_population_count != len(self.entries):
            raise NARProductionMappingError("population count differs")
        for name in ("external_entry_id", "race_entry_id", "horse_no"):
            if len({getattr(item, name) for item in self.entries}) != len(self.entries):
                raise NARProductionMappingError("non-bijective mapping")

    @property
    def mapping_population_sha256(self) -> str:
        return _sha([item.payload() for item in self.entries])

    def payload(self) -> dict[str, object]:
        return {
            "schema": "nar-production-mapping-receipt-v1",
            "organization": "NAR", "source_system": "nar_official",
            "external_race_id": self.external_race_id,
            "internal_race_id": self.internal_race_id,
            "canonical_deba_url": self.canonical_deba_url,
            "phase110_receipt_id": self.phase110_receipt_id,
            "phase110_population_sha256": self.phase110_population_sha256,
            "phase110_population_count": self.phase110_population_count,
            "phase110_issued_at": self.phase110_issued_at.isoformat(),
            "phase111_declaration_id": self.phase111_declaration_id,
            "phase111_receipt_id": self.phase111_receipt_id,
            "phase111_capture_id": self.phase111_capture_id,
            "response_sha256": self.response_sha256,
            "observed_at": self.observed_at.isoformat(),
            "prediction_cutoff": self.prediction_cutoff.isoformat(),
            "mapping_population_sha256": self.mapping_population_sha256,
            "mapping_population_count": len(self.entries),
            "issued_at": self.issued_at.isoformat(),
            "entries": [item.payload() for item in self.entries],
        }

    @property
    def receipt_id(self) -> str:
        return _sha(self.payload())


def receipt_from_phase110(*, source: NARIdentityCompleteReceiptV1,
                          issued_at: datetime) -> NARProductionMappingReceiptV1:
    if type(source) is not NARIdentityCompleteReceiptV1:
        raise NARProductionMappingError("exact Phase110 receipt required")
    entries = tuple(NARProductionMappingEntryV1(
        item.external_entry_id, item.horse_id, item.horse_no) for item in source.entries)
    return NARProductionMappingReceiptV1(
        source.external_race_id, source.race_id, source.canonical_deba_url,
        source.receipt_id, source.population_sha256, len(source.entries),
        source.issued_at, source.phase111_declaration_id,
        source.phase111_receipt_id, source.phase111_capture_id,
        source.response_sha256, source.observed_at, source.prediction_cutoff,
        issued_at, entries)


def parse_mapping_receipt(value: str, expected_id: str) -> NARProductionMappingReceiptV1:
    try:
        raw = json.loads(value)
        entries = tuple(NARProductionMappingEntryV1(**item) for item in raw["entries"])
        result = NARProductionMappingReceiptV1(
            raw["external_race_id"], raw["internal_race_id"], raw["canonical_deba_url"],
            raw["phase110_receipt_id"], raw["phase110_population_sha256"],
            raw["phase110_population_count"], datetime.fromisoformat(raw["phase110_issued_at"]),
            raw["phase111_declaration_id"], raw["phase111_receipt_id"],
            raw["phase111_capture_id"], raw["response_sha256"],
            datetime.fromisoformat(raw["observed_at"]),
            datetime.fromisoformat(raw["prediction_cutoff"]),
            datetime.fromisoformat(raw["issued_at"]), entries)
        if raw != result.payload() or value != _canonical_json(raw) or result.receipt_id != expected_id:
            raise NARProductionMappingError("mapping receipt content differs")
        return result
    except (TypeError, KeyError, ValueError, AttributeError) as error:
        raise NARProductionMappingError("mapping receipt is corrupt") from error
