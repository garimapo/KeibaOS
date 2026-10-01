"""Canonical, status-neutral Phase110 population receipt values."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime

from scripts.simulation.nar_identity_complete_entry_source import (
    NARIdentityCompleteSourceV1, nar_entry_v1,
)
from scripts.simulation.nar_trusted_deba_acquisition import canonical_deba_url


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def content_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class NARIdentityPersistedEntryV1:
    external_entry_id: str
    horse_id: int
    horse_no: int
    external_horse_id: str | None
    issuance_disposition: str

    def payload(self) -> dict[str, object]:
        return {
            "external_entry_id": self.external_entry_id,
            "horse_id": self.horse_id,
            "horse_no": self.horse_no,
            "external_horse_id": self.external_horse_id,
            "issuance_disposition": self.issuance_disposition,
        }


@dataclass(frozen=True, slots=True)
class NARIdentityCompleteReceiptV1:
    external_race_id: str
    race_id: int
    canonical_deba_url: str
    phase111_declaration_id: str
    phase111_receipt_id: str
    phase111_capture_id: str
    response_sha256: str
    observed_at: datetime
    prediction_cutoff: datetime
    issued_at: datetime
    entries: tuple[NARIdentityPersistedEntryV1, ...]

    def __post_init__(self) -> None:
        if type(self.race_id) is not int or self.race_id <= 0:
            raise ValueError("positive internal parent required")
        if canonical_deba_url(self.external_race_id) != self.canonical_deba_url:
            raise ValueError("receipt race/URL ancestry contradiction")
        if not self.entries or any(type(item) is not NARIdentityPersistedEntryV1 for item in self.entries):
            raise ValueError("complete population required")
        if tuple(sorted(self.entries, key=lambda item: item.horse_no)) != self.entries:
            raise ValueError("canonical horse-number ordering required")
        for key in ("external_entry_id", "horse_id", "horse_no"):
            if len({getattr(item, key) for item in self.entries}) != len(self.entries):
                raise ValueError("non-bijective population")
        for entry in self.entries:
            if (type(entry.horse_id) is not int or entry.horse_id <= 0
                    or entry.external_entry_id != nar_entry_v1(self.external_race_id, entry.horse_no)
                    or entry.issuance_disposition not in (
                        "ADOPTED_EXISTING_INTERNAL_ID", "ISSUED_IDENTITY_ONLY_INTERNAL_ID")
                    or (entry.external_horse_id is not None and
                        (type(entry.external_horse_id) is not str
                         or not entry.external_horse_id.startswith("nar:horse:")))):
                raise ValueError("invalid complete-population binding")
        if any(type(value) is not datetime or value.tzinfo is None
               for value in (self.observed_at, self.prediction_cutoff, self.issued_at)):
            raise ValueError("aware receipt timestamps required")
        if self.observed_at > self.prediction_cutoff:
            raise ValueError("post-cutoff capture cannot qualify")

    @property
    def population_sha256(self) -> str:
        return content_sha256([item.payload() for item in self.entries])

    def payload(self) -> dict[str, object]:
        return {
            "schema": "nar-identity-complete-receipt-v1",
            "organization": "NAR",
            "source_system": "nar_official",
            "external_race_id": self.external_race_id,
            "race_id": self.race_id,
            "canonical_deba_url": self.canonical_deba_url,
            "phase111_declaration_id": self.phase111_declaration_id,
            "phase111_receipt_id": self.phase111_receipt_id,
            "phase111_capture_id": self.phase111_capture_id,
            "response_sha256": self.response_sha256,
            "observed_at": self.observed_at.isoformat(),
            "prediction_cutoff": self.prediction_cutoff.isoformat(),
            "issued_at": self.issued_at.isoformat(),
            "population_count": len(self.entries),
            "population_sha256": self.population_sha256,
            "entries": [item.payload() for item in self.entries],
        }

    @property
    def receipt_id(self) -> str:
        return content_sha256(self.payload())


def create_receipt(*, source: NARIdentityCompleteSourceV1, race_id: int,
                   issued_at: datetime, entries: tuple[NARIdentityPersistedEntryV1, ...]) -> NARIdentityCompleteReceiptV1:
    if type(source) is not NARIdentityCompleteSourceV1:
        raise ValueError("exact Phase110 extracted source required")
    return NARIdentityCompleteReceiptV1(
        source.external_race_id, race_id, source.canonical_deba_url,
        source.phase111_declaration_id, source.phase111_receipt_id,
        source.phase111_capture_id, source.response_sha256,
        source.observed_at, source.prediction_cutoff, issued_at, entries)


def parse_receipt(payload_json: str, expected_id: str) -> NARIdentityCompleteReceiptV1:
    payload = json.loads(payload_json)
    entries = tuple(NARIdentityPersistedEntryV1(**item) for item in payload["entries"])
    receipt = NARIdentityCompleteReceiptV1(
        payload["external_race_id"], payload["race_id"], payload["canonical_deba_url"],
        payload["phase111_declaration_id"], payload["phase111_receipt_id"],
        payload["phase111_capture_id"], payload["response_sha256"],
        datetime.fromisoformat(payload["observed_at"]),
        datetime.fromisoformat(payload["prediction_cutoff"]),
        datetime.fromisoformat(payload["issued_at"]), entries)
    if payload != receipt.payload() or canonical_json(payload) != payload_json or receipt.receipt_id != expected_id:
        raise ValueError("Phase110 receipt integrity failure")
    return receipt
