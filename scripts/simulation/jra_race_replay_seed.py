"""Immutable provider-specific JRA race replay seed identities."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass, field as _field
from datetime import datetime as _datetime, timezone as _timezone
import hashlib as _hashlib
import json as _json
import re as _re
from unicodedata import normalize as _normalize

from scripts.simulation.jra_official_identity import (
    JRAOfficialIdentityValidationError as _IdentityError,
    build_jra_external_entry_id as _build_entry_id,
    parse_jra_external_horse_id as _parse_horse_id,
    parse_jra_external_race_id as _parse_race_id,
    parse_jra_race_card_url_identity as _parse_card_url,
)


class JRARaceReplaySeedError(ValueError):
    """Base error for immutable JRA replay-seed values."""


class JRARaceReplaySeedValidationError(JRARaceReplaySeedError):
    """Raised when a seed value is not canonical or internally coherent."""


_SHA256 = _re.compile(r"[0-9a-f]{64}\Z")
_V3 = _re.compile(r"jra-capture-v3:[0-9a-f]{64}\Z")
_V4 = _re.compile(r"jra-capture-v4:[0-9a-f]{64}\Z")
_SEED = _re.compile(r"jra-race-replay-seed-v1:[0-9a-f]{64}\Z")
_SCHEMA_VERSION = 1


def _validation(message: str) -> JRARaceReplaySeedValidationError:
    return JRARaceReplaySeedValidationError(message)


def _utc(value: object, name: str) -> _datetime:
    if type(value) is not _datetime:
        raise _validation(f"{name} must be exact datetime")
    try:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError
        return value.astimezone(_timezone.utc)
    except (OverflowError, TypeError, ValueError) as error:
        raise _validation(f"{name} must be timezone-aware") from error


def _datetime_text(value: _datetime) -> str:
    return value.astimezone(_timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")


def _dataset(value: object) -> str:
    if type(value) is not str or not value or _normalize("NFC", value) != value:
        raise _validation("dataset_id must be a non-empty NFC str")
    return value


def _positive(value: object, name: str) -> int:
    if type(value) is not int or value <= 0:
        raise _validation(f"{name} must be a positive exact int")
    return value


@_dataclass(frozen=True, slots=True)
class JRARaceReplaySeedEntry:
    """One exact provider entry to internal race-entry association."""

    entry_order: int
    external_entry_id: str
    external_horse_id: str
    horse_no: int
    internal_race_entry_id: int

    def __post_init__(self) -> None:
        if type(self.entry_order) is not int or self.entry_order < 0:
            raise _validation("entry_order must be a non-negative exact int")
        _positive(self.horse_no, "horse_no")
        _positive(self.internal_race_entry_id, "internal_race_entry_id")
        try:
            _parse_horse_id(self.external_horse_id)
        except _IdentityError as error:
            raise _validation("external_horse_id is invalid") from error
        if type(self.external_entry_id) is not str:
            raise _validation("external_entry_id must be exact str")


@_dataclass(frozen=True, slots=True, init=False)
class JRARaceReplaySeed:
    """One immutable, process-durable JRA target-race replay handoff."""

    seed_id: str = _field(init=False)
    schema_version: int = _field(init=False)
    content_sha256: str = _field(init=False)
    dataset_id: str = _field(init=False)
    external_race_id: str = _field(init=False)
    internal_race_id: int = _field(init=False)
    target_race_selection_capture_id: str = _field(init=False)
    target_race_card_capture_id: str = _field(init=False)
    target_race_card_response_sha256: str = _field(init=False)
    canonical_target_race_card_url: str = _field(init=False)
    captured_at: _datetime = _field(init=False)
    information_cutoff: _datetime = _field(init=False)
    entries: tuple[JRARaceReplaySeedEntry, ...] = _field(init=False)

    def __init__(
        self,
        *,
        dataset_id: str,
        external_race_id: str,
        internal_race_id: int,
        target_race_selection_capture_id: str,
        target_race_card_capture_id: str,
        target_race_card_response_sha256: str,
        canonical_target_race_card_url: str,
        captured_at: _datetime,
        information_cutoff: _datetime,
        entries: tuple[JRARaceReplaySeedEntry, ...],
    ) -> None:
        dataset = _dataset(dataset_id)
        try:
            race = _parse_race_id(external_race_id)
            card_race = _parse_card_url(canonical_target_race_card_url)
        except _IdentityError as error:
            raise _validation("JRA race identity or target-card URL is invalid") from error
        if card_race != race:
            raise _validation("target-card URL disagrees with external_race_id")
        _positive(internal_race_id, "internal_race_id")
        if type(target_race_selection_capture_id) is not str or _V4.fullmatch(target_race_selection_capture_id) is None:
            raise _validation("target_race_selection_capture_id is invalid")
        if type(target_race_card_capture_id) is not str or _V3.fullmatch(target_race_card_capture_id) is None:
            raise _validation("target_race_card_capture_id is invalid")
        if type(target_race_card_response_sha256) is not str or _SHA256.fullmatch(target_race_card_response_sha256) is None:
            raise _validation("target_race_card_response_sha256 is invalid")
        if type(canonical_target_race_card_url) is not str:
            raise _validation("canonical_target_race_card_url must be exact str")
        captured = _utc(captured_at, "captured_at")
        cutoff = _utc(information_cutoff, "information_cutoff")
        if captured > cutoff:
            raise _validation("captured_at must not be after information_cutoff")
        if type(entries) is not tuple or not entries:
            raise _validation("entries must be a non-empty exact tuple")
        previous_horse_no = 0
        external_entries: set[str] = set()
        external_horses: set[str] = set()
        horse_numbers: set[int] = set()
        internal_entries: set[int] = set()
        for expected_order, entry in enumerate(entries):
            if type(entry) is not JRARaceReplaySeedEntry:
                raise _validation("entries must contain exact JRARaceReplaySeedEntry values")
            if entry.entry_order != expected_order or entry.horse_no <= previous_horse_no:
                raise _validation("entries must be contiguous and ascending by horse_no")
            try:
                rebuilt = _build_entry_id(race_identity=race, horse_no=entry.horse_no)
                _parse_horse_id(entry.external_horse_id)
            except _IdentityError as error:
                raise _validation("entry identity is invalid") from error
            if entry.external_entry_id != rebuilt:
                raise _validation("external_entry_id disagrees with race and horse_no")
            if (
                entry.external_entry_id in external_entries
                or entry.external_horse_id in external_horses
                or entry.horse_no in horse_numbers
                or entry.internal_race_entry_id in internal_entries
            ):
                raise _validation("entries contain duplicate identity material")
            previous_horse_no = entry.horse_no
            external_entries.add(entry.external_entry_id)
            external_horses.add(entry.external_horse_id)
            horse_numbers.add(entry.horse_no)
            internal_entries.add(entry.internal_race_entry_id)
        content = _content_material(
            dataset_id=dataset,
            external_race_id=race.external_race_id,
            internal_race_id=internal_race_id,
            target_race_selection_capture_id=target_race_selection_capture_id,
            target_race_card_capture_id=target_race_card_capture_id,
            target_race_card_response_sha256=target_race_card_response_sha256,
            canonical_target_race_card_url=canonical_target_race_card_url,
            captured_at=captured,
            information_cutoff=cutoff,
            entries=entries,
        )
        digest = _hashlib.sha256(
            _json.dumps(content, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        object.__setattr__(self, "seed_id", f"jra-race-replay-seed-v1:{digest}")
        object.__setattr__(self, "schema_version", _SCHEMA_VERSION)
        object.__setattr__(self, "content_sha256", digest)
        object.__setattr__(self, "dataset_id", dataset)
        object.__setattr__(self, "external_race_id", race.external_race_id)
        object.__setattr__(self, "internal_race_id", internal_race_id)
        object.__setattr__(self, "target_race_selection_capture_id", target_race_selection_capture_id)
        object.__setattr__(self, "target_race_card_capture_id", target_race_card_capture_id)
        object.__setattr__(self, "target_race_card_response_sha256", target_race_card_response_sha256)
        object.__setattr__(self, "canonical_target_race_card_url", canonical_target_race_card_url)
        object.__setattr__(self, "captured_at", captured)
        object.__setattr__(self, "information_cutoff", cutoff)
        object.__setattr__(self, "entries", entries)


def _content_material(
    *,
    dataset_id: str,
    external_race_id: str,
    internal_race_id: int,
    target_race_selection_capture_id: str,
    target_race_card_capture_id: str,
    target_race_card_response_sha256: str,
    canonical_target_race_card_url: str,
    captured_at: _datetime,
    information_cutoff: _datetime,
    entries: tuple[JRARaceReplaySeedEntry, ...],
) -> dict[str, object]:
    return {
        "canonical_target_race_card_url": canonical_target_race_card_url,
        "captured_at_utc": _datetime_text(captured_at),
        "dataset_id": dataset_id,
        "entries": [
            {
                "entry_order": entry.entry_order,
                "external_entry_id": entry.external_entry_id,
                "external_horse_id": entry.external_horse_id,
                "horse_no": entry.horse_no,
                "internal_race_entry_id": entry.internal_race_entry_id,
            }
            for entry in entries
        ],
        "external_race_id": external_race_id,
        "information_cutoff_utc": _datetime_text(information_cutoff),
        "internal_race_id": internal_race_id,
        "schema_version": _SCHEMA_VERSION,
        "target_race_card_capture_id": target_race_card_capture_id,
        "target_race_card_response_sha256": target_race_card_response_sha256,
        "target_race_selection_capture_id": target_race_selection_capture_id,
    }


def build_jra_race_replay_seed(
    *,
    dataset_id: str,
    external_race_id: str,
    internal_race_id: int,
    target_race_selection_capture_id: str,
    target_race_card_capture_id: str,
    target_race_card_response_sha256: str,
    canonical_target_race_card_url: str,
    captured_at: _datetime,
    information_cutoff: _datetime,
    entries: tuple[JRARaceReplaySeedEntry, ...],
) -> JRARaceReplaySeed:
    """Build one validated deterministic immutable JRA replay seed."""

    return JRARaceReplaySeed(
        dataset_id=dataset_id,
        external_race_id=external_race_id,
        internal_race_id=internal_race_id,
        target_race_selection_capture_id=target_race_selection_capture_id,
        target_race_card_capture_id=target_race_card_capture_id,
        target_race_card_response_sha256=target_race_card_response_sha256,
        canonical_target_race_card_url=canonical_target_race_card_url,
        captured_at=captured_at,
        information_cutoff=information_cutoff,
        entries=entries,
    )


def is_jra_race_replay_seed_id(value: object) -> bool:
    """Return whether one value has the exact seed-ID grammar."""

    return type(value) is str and _SEED.fullmatch(value) is not None


def jra_race_replay_seed_datetime_text(value: _datetime) -> str:
    """Return one validated seed UTC timestamp storage representation."""

    return _datetime_text(_utc(value, "datetime"))


__all__ = (
    "JRARaceReplaySeedError",
    "JRARaceReplaySeedValidationError",
    "JRARaceReplaySeedEntry",
    "JRARaceReplaySeed",
    "build_jra_race_replay_seed",
    "is_jra_race_replay_seed_id",
    "jra_race_replay_seed_datetime_text",
)
