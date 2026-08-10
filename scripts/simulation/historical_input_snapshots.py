"""Immutable historical prediction-input snapshot domain contracts."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass, field as _field
from datetime import date as _date, datetime as _datetime, timezone as _timezone
from decimal import Decimal as _Decimal
import hashlib as _hashlib
import json as _json
from typing import Protocol as _Protocol
from unicodedata import normalize as _normalize

from scripts.simulation.historical_input_evidence import (
    HistoricalInputEvidenceReference as _HistoricalInputEvidenceReference,
)


def _require_exact(value: object, expected: type[object], name: str) -> object:
    if type(value) is not expected:
        raise ValueError(f"{name} must be {expected.__name__}")
    return value


def _normalize_required_text(value: object, name: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be str")
    normalized = _normalize("NFC", value)
    if not normalized:
        raise ValueError(f"{name} must not be empty")
    return normalized


def _normalize_text_allow_empty(value: object, name: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be str")
    return _normalize("NFC", value)


def _normalize_optional_text(value: object, name: str) -> str | None:
    if value is None:
        return None
    return _normalize_required_text(value, name)


def _normalize_utc_datetime(value: object, name: str) -> _datetime:
    if type(value) is not _datetime:
        raise ValueError(f"{name} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(_timezone.utc)


def _normalize_optional_utc_datetime(value: object, name: str) -> _datetime | None:
    if value is None:
        return None
    return _normalize_utc_datetime(value, name)


def _normalize_date(value: object, name: str) -> _date:
    if type(value) is not _date:
        raise ValueError(f"{name} must be date")
    return value


def _canonical_decimal(value: _Decimal) -> _Decimal:
    if value == 0:
        return _Decimal("0")
    return value.normalize()


def _normalize_decimal(
    value: object,
    name: str,
    *,
    positive: bool = False,
    non_negative: bool = False,
) -> _Decimal:
    if type(value) is not _Decimal:
        raise ValueError(f"{name} must be Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if positive and value <= 0:
        raise ValueError(f"{name} must be positive")
    if non_negative and value < 0:
        raise ValueError(f"{name} must be non-negative")
    return _canonical_decimal(value)


def _positive_int(value: object, name: str) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{name} must be a positive int")
    return value


def _non_negative_int(value: object, name: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a non-negative int")
    return value


def _require_tuple(value: object, name: str) -> tuple[object, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be tuple")
    return value


def _require_unique(values: tuple[object, ...], name: str) -> None:
    if len(set(values)) != len(values):
        raise ValueError(f"{name} must be unique")


@_dataclass(frozen=True, slots=True)
class HistoricalSourceIdentity:
    organization: str
    source_system: str
    external_race_id: str
    source_url: str | None = _field(default=None, compare=False, hash=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "organization", _normalize_required_text(self.organization, "organization"))
        object.__setattr__(self, "source_system", _normalize_required_text(self.source_system, "source_system"))
        object.__setattr__(self, "external_race_id", _normalize_required_text(self.external_race_id, "external_race_id"))
        object.__setattr__(self, "source_url", _normalize_optional_text(self.source_url, "source_url"))


@_dataclass(frozen=True, slots=True)
class HistoricalExternalRaceIdentity:
    organization: str
    source_system: str
    external_race_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "organization", _normalize_required_text(self.organization, "organization"))
        object.__setattr__(self, "source_system", _normalize_required_text(self.source_system, "source_system"))
        object.__setattr__(self, "external_race_id", _normalize_required_text(self.external_race_id, "external_race_id"))


@_dataclass(frozen=True, slots=True)
class HistoricalExternalEntryIdentity:
    external_race_identity: HistoricalExternalRaceIdentity
    external_entry_id: str
    external_horse_id: str | None = _field(default=None, compare=False, hash=False)

    def __post_init__(self) -> None:
        _require_exact(self.external_race_identity, HistoricalExternalRaceIdentity, "external_race_identity")
        object.__setattr__(self, "external_entry_id", _normalize_required_text(self.external_entry_id, "external_entry_id"))
        object.__setattr__(self, "external_horse_id", _normalize_optional_text(self.external_horse_id, "external_horse_id"))


@_dataclass(frozen=True, slots=True)
class HistoricalInputSnapshotIdentity:
    dataset_id: str
    source_identity: HistoricalSourceIdentity
    captured_at: _datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "dataset_id", _normalize_required_text(self.dataset_id, "dataset_id"))
        _require_exact(self.source_identity, HistoricalSourceIdentity, "source_identity")
        object.__setattr__(self, "captured_at", _normalize_utc_datetime(self.captured_at, "captured_at"))


@_dataclass(frozen=True, slots=True)
class HistoricalRaceSnapshot:
    target_race_date: _date
    scheduled_start_at: _datetime
    place: str
    distance_m: int
    track: str
    track_condition: str
    race_name: str | None = None
    race_class: str | None = None
    weather: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "target_race_date", _normalize_date(self.target_race_date, "target_race_date"))
        object.__setattr__(self, "scheduled_start_at", _normalize_utc_datetime(self.scheduled_start_at, "scheduled_start_at"))
        object.__setattr__(self, "place", _normalize_required_text(self.place, "place"))
        object.__setattr__(self, "distance_m", _positive_int(self.distance_m, "distance_m"))
        object.__setattr__(self, "track", _normalize_required_text(self.track, "track"))
        object.__setattr__(self, "track_condition", _normalize_required_text(self.track_condition, "track_condition"))
        object.__setattr__(self, "race_name", _normalize_optional_text(self.race_name, "race_name"))
        object.__setattr__(self, "race_class", _normalize_optional_text(self.race_class, "race_class"))
        object.__setattr__(self, "weather", _normalize_optional_text(self.weather, "weather"))


@_dataclass(frozen=True, slots=True)
class HistoricalRaceEntrySnapshot:
    race_entry_id: int
    external_entry_identity: HistoricalExternalEntryIdentity
    horse_no: int
    jockey: str
    win_odds: _Decimal
    entry_order: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "race_entry_id", _positive_int(self.race_entry_id, "race_entry_id"))
        _require_exact(self.external_entry_identity, HistoricalExternalEntryIdentity, "external_entry_identity")
        object.__setattr__(self, "horse_no", _positive_int(self.horse_no, "horse_no"))
        object.__setattr__(self, "jockey", _normalize_required_text(self.jockey, "jockey"))
        object.__setattr__(self, "win_odds", _normalize_decimal(self.win_odds, "win_odds", positive=True))
        object.__setattr__(self, "entry_order", _non_negative_int(self.entry_order, "entry_order"))


@_dataclass(frozen=True, slots=True)
class HistoricalPastRaceSnapshot:
    race_entry_id: int
    past_race_index: int
    race_date: _date
    place: str
    race_name: str
    race_class: str
    distance_m: int
    track: str
    weather: str
    track_condition: str
    finish: int
    reference_time_difference_seconds: _Decimal
    race_time: str
    weight: _Decimal
    weight_diff: _Decimal
    jockey: str
    popularity: int
    odds: _Decimal
    passing_order: str
    fourth_corner_position: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "race_entry_id", _positive_int(self.race_entry_id, "race_entry_id"))
        object.__setattr__(self, "past_race_index", _non_negative_int(self.past_race_index, "past_race_index"))
        object.__setattr__(self, "race_date", _normalize_date(self.race_date, "race_date"))
        for name in ("place", "race_name", "race_class", "track", "weather", "track_condition", "race_time", "jockey"):
            object.__setattr__(self, name, _normalize_required_text(getattr(self, name), name))
        object.__setattr__(self, "passing_order", _normalize_text_allow_empty(self.passing_order, "passing_order"))
        object.__setattr__(self, "distance_m", _positive_int(self.distance_m, "distance_m"))
        object.__setattr__(self, "finish", _positive_int(self.finish, "finish"))
        object.__setattr__(
            self,
            "reference_time_difference_seconds",
            _normalize_decimal(
                self.reference_time_difference_seconds,
                "reference_time_difference_seconds",
                non_negative=True,
            ),
        )
        object.__setattr__(self, "weight", _normalize_decimal(self.weight, "weight", non_negative=True))
        object.__setattr__(self, "weight_diff", _normalize_decimal(self.weight_diff, "weight_diff"))
        object.__setattr__(self, "popularity", _non_negative_int(self.popularity, "popularity"))
        object.__setattr__(self, "odds", _normalize_decimal(self.odds, "odds", non_negative=True))
        object.__setattr__(self, "fourth_corner_position", _non_negative_int(self.fourth_corner_position, "fourth_corner_position"))


@_dataclass(frozen=True, slots=True)
class HistoricalInputProvenance:
    input_type: str
    audit_key: str
    source: str
    source_id: str
    race_entry_id: int | None
    evidence: tuple[_HistoricalInputEvidenceReference, ...]
    past_race_index: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "input_type", _normalize_required_text(self.input_type, "input_type"))
        object.__setattr__(self, "audit_key", _normalize_required_text(self.audit_key, "audit_key"))
        object.__setattr__(self, "source", _normalize_required_text(self.source, "source"))
        object.__setattr__(self, "source_id", _normalize_required_text(self.source_id, "source_id"))
        if self.race_entry_id is not None:
            object.__setattr__(self, "race_entry_id", _positive_int(self.race_entry_id, "race_entry_id"))
        if self.past_race_index is not None:
            object.__setattr__(self, "past_race_index", _non_negative_int(self.past_race_index, "past_race_index"))
        if type(self.evidence) is not tuple or not self.evidence:
            raise ValueError("provenance evidence must be a non-empty tuple")
        for item in self.evidence:
            _require_exact(item, _HistoricalInputEvidenceReference, "provenance evidence item")
        object.__setattr__(self, "evidence", tuple(sorted(self.evidence, key=lambda item: item.evidence_role)))
        _validate_provenance_shape(self)


def _validate_provenance_shape(provenance: HistoricalInputProvenance) -> None:
    expected_roles = {
        "track": ("track",),
        "entry": ("entry",),
        "odds": ("odds_win",),
        "jockey": ("jockey",),
    }
    if provenance.input_type == "track":
        if provenance.audit_key != "track" or provenance.race_entry_id is not None or provenance.past_race_index is not None:
            raise ValueError("track provenance shape is invalid")
        required = expected_roles["track"]
    elif provenance.race_entry_id is None:
        raise ValueError("race_entry_id is required for non-track provenance")
    elif provenance.input_type in {"entry", "odds", "jockey"}:
        if provenance.past_race_index is not None or provenance.audit_key != f"{provenance.input_type}/{provenance.race_entry_id}":
            raise ValueError("entry provenance shape is invalid")
        required = expected_roles[provenance.input_type]
    elif provenance.input_type != "past_race":
        raise ValueError("input_type is invalid")
    elif provenance.past_race_index is None:
        if provenance.audit_key != f"past_race/{provenance.race_entry_id}/none":
            raise ValueError("past-race absence provenance shape is invalid")
        required = ("past_race_absence_query",)
    else:
        if provenance.audit_key != f"past_race/{provenance.race_entry_id}/{provenance.past_race_index}":
            raise ValueError("past-race provenance shape is invalid")
        required = ("historical_race_context", "historical_race_result")
    roles = tuple(item.evidence_role for item in provenance.evidence)
    if roles != required or len(set(roles)) != len(roles):
        raise ValueError("provenance evidence roles are invalid")
    observations: dict[tuple[str | None, str], tuple[_datetime | None, _datetime]] = {}
    for item in provenance.evidence:
        identity = (item.canonical_source_url, item.response_sha256)
        current = (item.available_at, item.observed_at)
        previous = observations.get(identity)
        if previous is not None and previous != current:
            raise ValueError("provenance same-response timestamps conflict")
        observations[identity] = current
    return


def _validate_snapshot_children(
    *,
    entries: tuple[object, ...],
    past_races: tuple[object, ...],
    provenance: tuple[object, ...],
    race: HistoricalRaceSnapshot,
    identity: HistoricalInputSnapshotIdentity,
    information_cutoff: _datetime,
) -> None:
    if not entries:
        raise ValueError("entries must not be empty")
    for entry in entries:
        _require_exact(entry, HistoricalRaceEntrySnapshot, "entries item")
    for past_race in past_races:
        _require_exact(past_race, HistoricalPastRaceSnapshot, "past_races item")
    for item in provenance:
        _require_exact(item, HistoricalInputProvenance, "provenance item")
    typed_entries = tuple(entries)
    typed_past_races = tuple(past_races)
    typed_provenance = tuple(provenance)
    _require_unique(tuple(entry.race_entry_id for entry in typed_entries), "race_entry_id")
    _require_unique(tuple(entry.horse_no for entry in typed_entries), "horse_no")
    _require_unique(tuple(entry.external_entry_identity for entry in typed_entries), "external_entry_identity")
    _require_unique(tuple(entry.entry_order for entry in typed_entries), "entry_order")
    if tuple(sorted(entry.entry_order for entry in typed_entries)) != tuple(range(len(typed_entries))):
        raise ValueError("entry_order must be contiguous from zero")
    _require_unique(tuple(item.audit_key for item in typed_provenance), "audit_key")
    entry_ids = {entry.race_entry_id for entry in typed_entries}
    expected_race_identity = HistoricalExternalRaceIdentity(
        organization=identity.source_identity.organization,
        source_system=identity.source_identity.source_system,
        external_race_id=identity.source_identity.external_race_id,
    )
    for entry in typed_entries:
        if entry.external_entry_identity.external_race_identity != expected_race_identity:
            raise ValueError("external race identity does not match snapshot source identity")
    _require_unique(tuple((item.race_entry_id, item.past_race_index) for item in typed_past_races), "past race identity")
    for item in typed_past_races:
        if item.race_entry_id not in entry_ids:
            raise ValueError("past race must reference an entry")
        if item.race_date >= race.target_race_date:
            raise ValueError("past race date must precede target race date")
    for entry_id in entry_ids:
        indexes = tuple(sorted(item.past_race_index for item in typed_past_races if item.race_entry_id == entry_id))
        if indexes != tuple(range(len(indexes))):
            raise ValueError("past_race_index must be contiguous from zero")
    if identity.captured_at > information_cutoff or information_cutoff > race.scheduled_start_at:
        raise ValueError("snapshot timestamps are not causal")
    for item in typed_provenance:
        for evidence in item.evidence:
            if evidence.available_at is not None and evidence.available_at > identity.captured_at:
                raise ValueError("available_at must not be later than captured_at")
            if evidence.observed_at > identity.captured_at:
                raise ValueError("observed_at must not be later than captured_at")
    actual_keys = {item.audit_key for item in typed_provenance}
    required_keys = {"track"}
    for entry_id in entry_ids:
        required_keys.update({f"entry/{entry_id}", f"odds/{entry_id}", f"jockey/{entry_id}"})
        past_indexes = tuple(item.past_race_index for item in typed_past_races if item.race_entry_id == entry_id)
        if past_indexes:
            required_keys.update(f"past_race/{entry_id}/{index}" for index in past_indexes)
        else:
            required_keys.add(f"past_race/{entry_id}/none")
    if actual_keys != required_keys:
        raise ValueError("provenance keys are incomplete or incompatible")


def _format_datetime(value: _datetime) -> str:
    return value.isoformat(timespec="microseconds")


def _format_decimal(value: _Decimal) -> str:
    return format(_canonical_decimal(value), "f")


def _build_unchecked_historical_input_snapshot_content_payload(
    *,
    snapshot: HistoricalInputSnapshot,
) -> dict[str, object]:
    source = snapshot.identity.source_identity
    return {
        "schema_version": 3,
        "snapshot_identity": {
            "dataset_id": snapshot.identity.dataset_id,
            "organization": source.organization,
            "source_system": source.source_system,
            "external_race_id": source.external_race_id,
            "captured_at": _format_datetime(snapshot.identity.captured_at),
        },
        "source_identity": {
            "organization": source.organization,
            "source_system": source.source_system,
            "external_race_id": source.external_race_id,
            "source_url": source.source_url,
        },
        "internal_race_id": snapshot.internal_race_id,
        "information_cutoff": _format_datetime(snapshot.information_cutoff),
        "race": {
            "target_race_date": snapshot.race.target_race_date.isoformat(),
            "scheduled_start_at": _format_datetime(snapshot.race.scheduled_start_at),
            "place": snapshot.race.place,
            "distance_m": snapshot.race.distance_m,
            "track": snapshot.race.track,
            "track_condition": snapshot.race.track_condition,
            "race_name": snapshot.race.race_name,
            "race_class": snapshot.race.race_class,
            "weather": snapshot.race.weather,
        },
        "entries": [
            {
                "race_entry_id": entry.race_entry_id,
                "external_entry_identity": {
                    "organization": entry.external_entry_identity.external_race_identity.organization,
                    "source_system": entry.external_entry_identity.external_race_identity.source_system,
                    "external_race_id": entry.external_entry_identity.external_race_identity.external_race_id,
                    "external_entry_id": entry.external_entry_identity.external_entry_id,
                    "external_horse_id": entry.external_entry_identity.external_horse_id,
                },
                "horse_no": entry.horse_no,
                "jockey": entry.jockey,
                "win_odds": _format_decimal(entry.win_odds),
                "entry_order": entry.entry_order,
            }
            for entry in sorted(snapshot.entries, key=lambda item: item.entry_order)
        ],
        "past_races": [
            {
                "race_entry_id": item.race_entry_id,
                "past_race_index": item.past_race_index,
                "race_date": item.race_date.isoformat(),
                "place": item.place,
                "race_name": item.race_name,
                "race_class": item.race_class,
                "distance_m": item.distance_m,
                "track": item.track,
                "weather": item.weather,
                "track_condition": item.track_condition,
                "finish": item.finish,
                "reference_time_difference_seconds": _format_decimal(
                    item.reference_time_difference_seconds
                ),
                "race_time": item.race_time,
                "weight": _format_decimal(item.weight),
                "weight_diff": _format_decimal(item.weight_diff),
                "jockey": item.jockey,
                "popularity": item.popularity,
                "odds": _format_decimal(item.odds),
                "passing_order": item.passing_order,
                "fourth_corner_position": item.fourth_corner_position,
            }
            for item in sorted(snapshot.past_races, key=lambda value: (value.race_entry_id, value.past_race_index))
        ],
        "provenance": [
            {
                "input_type": item.input_type,
                "audit_key": item.audit_key,
                "source": item.source,
                "source_id": item.source_id,
                "race_entry_id": item.race_entry_id,
                "past_race_index": item.past_race_index,
                "evidence": [
                    {
                        "evidence_role": evidence.evidence_role,
                        "canonical_source_url": evidence.canonical_source_url,
                        "response_sha256": evidence.response_sha256,
                        "available_at": None if evidence.available_at is None else _format_datetime(evidence.available_at),
                        "observed_at": _format_datetime(evidence.observed_at),
                    }
                    for evidence in item.evidence
                ],
            }
            for item in sorted(snapshot.provenance, key=lambda value: value.audit_key)
        ],
    }


def _sha256_canonical_payload(payload: dict[str, object]) -> str:
    encoded = _json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _hashlib.sha256(encoded).hexdigest()


@_dataclass(frozen=True, slots=True)
class HistoricalInputSnapshot:
    identity: HistoricalInputSnapshotIdentity
    internal_race_id: int
    information_cutoff: _datetime
    race: HistoricalRaceSnapshot
    entries: tuple[HistoricalRaceEntrySnapshot, ...]
    past_races: tuple[HistoricalPastRaceSnapshot, ...]
    provenance: tuple[HistoricalInputProvenance, ...]
    content_sha256: str = _field(init=False, compare=False, hash=False)

    def __post_init__(self) -> None:
        _require_exact(self.identity, HistoricalInputSnapshotIdentity, "identity")
        object.__setattr__(self, "internal_race_id", _positive_int(self.internal_race_id, "internal_race_id"))
        object.__setattr__(self, "information_cutoff", _normalize_utc_datetime(self.information_cutoff, "information_cutoff"))
        _require_exact(self.race, HistoricalRaceSnapshot, "race")
        entries = _require_tuple(self.entries, "entries")
        past_races = _require_tuple(self.past_races, "past_races")
        provenance = _require_tuple(self.provenance, "provenance")
        _validate_snapshot_children(
            entries=entries,
            past_races=past_races,
            provenance=provenance,
            race=self.race,
            identity=self.identity,
            information_cutoff=self.information_cutoff,
        )
        object.__setattr__(self, "entries", entries)
        object.__setattr__(self, "past_races", past_races)
        object.__setattr__(self, "provenance", provenance)
        object.__setattr__(
            self,
            "content_sha256",
            _sha256_canonical_payload(_build_unchecked_historical_input_snapshot_content_payload(snapshot=self)),
        )


def build_historical_input_snapshot_content_payload(
    *,
    snapshot: HistoricalInputSnapshot,
) -> dict[str, object]:
    _require_exact(snapshot, HistoricalInputSnapshot, "snapshot")
    return _build_unchecked_historical_input_snapshot_content_payload(snapshot=snapshot)


def compute_historical_input_snapshot_content_sha256(
    *,
    snapshot: HistoricalInputSnapshot,
) -> str:
    return _sha256_canonical_payload(build_historical_input_snapshot_content_payload(snapshot=snapshot))


class HistoricalInputSnapshotSource(_Protocol):
    def load_latest_snapshot(
        self,
        *,
        dataset_id: str,
        race_id: int,
        information_cutoff: _datetime,
        source_identity: HistoricalExternalRaceIdentity,
    ) -> HistoricalInputSnapshot | None:
        ...


class HistoricalInputSnapshotRepository(_Protocol):
    def save_snapshot(
        self,
        *,
        snapshot: HistoricalInputSnapshot,
    ) -> None:
        ...
