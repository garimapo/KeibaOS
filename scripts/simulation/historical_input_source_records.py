"""Immutable validated historical source-record contracts.

This module is deliberately provider-neutral.  Provider-specific URL canonicalization
belongs to later source normalizers; this boundary validates the supplied canonical URL
without transforming it.
"""

from __future__ import annotations

from collections.abc import Mapping as _Mapping, Sequence as _Sequence
from dataclasses import dataclass as _dataclass, field as _field
from datetime import date as _date, datetime as _datetime, timezone as _timezone
from decimal import Decimal as _Decimal
import hashlib as _hashlib
import json as _json
from types import MappingProxyType as _MappingProxyType
from typing import Literal as _Literal
from unicodedata import category as _category, normalize as _normalize
from urllib.parse import urlsplit as _urlsplit

from scripts.simulation.historical_input_evidence import (
    HistoricalInputEvidenceReference as _HistoricalInputEvidenceReference,
)


SourceRecordKind = _Literal[
    "track",
    "entry",
    "jockey",
    "odds_win",
    "past_race",
    "past_race_absence",
]


class HistoricalInputSourceError(ValueError):
    """Base error for the historical source-record boundary."""


class HistoricalInputSourceValidationError(HistoricalInputSourceError):
    """Raised when one supplied source record violates its canonical contract."""


class HistoricalInputSourceConflictError(HistoricalInputSourceError):
    """Raised for duplicate source IDs or conflicting official past-race records."""


_RECORD_KINDS = frozenset({"track", "entry", "jockey", "odds_win", "past_race", "past_race_absence"})
_ENTRY_SCOPED_KINDS = _RECORD_KINDS - {"track"}
_EVIDENCE_ROLES = {
    "track": ("track",),
    "entry": ("entry",),
    "jockey": ("jockey",),
    "odds_win": ("odds_win",),
    "past_race": ("historical_race_context", "historical_race_result"),
    "past_race_absence": ("past_race_absence_query",),
}
_RECORD_VALUE_KEYS = {
    "track": frozenset(
        {
            "target_race_date",
            "scheduled_start_at",
            "place",
            "distance_m",
            "track",
            "track_condition",
            "race_name",
            "race_class",
            "weather",
        }
    ),
    "entry": frozenset({"external_entry_id", "external_horse_id", "horse_no"}),
    "jockey": frozenset({"external_entry_id", "jockey"}),
    "odds_win": frozenset({"external_entry_id", "horse_no", "win_odds"}),
    "past_race": frozenset(
        {
            "race_date",
            "place",
            "race_name",
            "race_class",
            "distance_m",
            "track",
            "weather",
            "track_condition",
            "finish",
            "reference_time_difference_seconds",
            "race_time",
            "weight",
            "weight_diff",
            "jockey",
            "popularity",
            "odds",
            "passing_order",
            "fourth_corner_position",
        }
    ),
    "past_race_absence": frozenset({"external_entry_id", "query_scope", "result_count"}),
}


def _validation_error(message: str) -> HistoricalInputSourceValidationError:
    return HistoricalInputSourceValidationError(message)


def _normalize_required_text(value: object, name: str) -> str:
    if type(value) is not str:
        raise _validation_error(f"{name} must be str")
    normalized = _normalize("NFC", value)
    if not normalized:
        raise _validation_error(f"{name} must not be empty")
    return normalized


def _normalize_text_allow_empty(value: object, name: str) -> str:
    if type(value) is not str:
        raise _validation_error(f"{name} must be str")
    return _normalize("NFC", value)


def _normalize_optional_text(value: object, name: str) -> str | None:
    if value is None:
        return None
    return _normalize_required_text(value, name)


def _require_positive_int(value: object, name: str) -> int:
    if type(value) is not int or value <= 0:
        raise _validation_error(f"{name} must be a positive int")
    return value


def _require_non_negative_int(value: object, name: str) -> int:
    if type(value) is not int or value < 0:
        raise _validation_error(f"{name} must be a non-negative int")
    return value


def _normalize_date(value: object, name: str) -> _date:
    if type(value) is not _date:
        raise _validation_error(f"{name} must be date")
    return value


def _normalize_utc_datetime(value: object, name: str) -> _datetime:
    if type(value) is not _datetime:
        raise _validation_error(f"{name} must be datetime")
    try:
        if value.tzinfo is None or value.utcoffset() is None:
            raise _validation_error(f"{name} must be timezone-aware")
        return value.astimezone(_timezone.utc)
    except HistoricalInputSourceValidationError:
        raise
    except (TypeError, ValueError, OverflowError) as error:
        raise _validation_error(f"{name} must be timezone-aware") from error


def _normalize_optional_utc_datetime(value: object, name: str) -> _datetime | None:
    if value is None:
        return None
    return _normalize_utc_datetime(value, name)


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
        raise _validation_error(f"{name} must be Decimal")
    if not value.is_finite():
        raise _validation_error(f"{name} must be finite")
    if positive and value <= 0:
        raise _validation_error(f"{name} must be positive")
    if non_negative and value < 0:
        raise _validation_error(f"{name} must be non-negative")
    return _canonical_decimal(value)


def _validate_canonical_source_url(value: object) -> str | None:
    if value is None:
        return None
    if type(value) is not str:
        raise _validation_error("canonical_source_url must be str or None")
    if not value:
        raise _validation_error("canonical_source_url must not be empty")
    if value != _normalize("NFC", value):
        raise _validation_error("canonical_source_url must already be NFC-normalized")
    if value != value.strip():
        raise _validation_error("canonical_source_url must not have leading or trailing whitespace")
    if any(_category(character) == "Cc" for character in value):
        raise _validation_error("canonical_source_url must not contain control characters")
    try:
        parsed = _urlsplit(value)
        host = parsed.hostname
        _ = parsed.port
    except ValueError as error:
        raise _validation_error("canonical_source_url is invalid") from error
    if parsed.scheme != "https" or not parsed.netloc or not host:
        raise _validation_error("canonical_source_url must be an absolute https URL with host")
    if parsed.username is not None or parsed.password is not None:
        raise _validation_error("canonical_source_url must not contain credentials")
    if parsed.fragment:
        raise _validation_error("canonical_source_url must not contain fragment")
    return value


def _require_mapping(value: object, name: str) -> _Mapping[str, object]:
    if not isinstance(value, _Mapping):
        raise _validation_error(f"{name} must be Mapping")
    return value


def _validated_key_set(value: _Mapping[str, object], expected: frozenset[str], name: str) -> None:
    if set(value) != expected:
        raise _validation_error(f"{name} keys are invalid")


def _validate_duplicate_external_entry(
    value: object,
    external_entry_id: str,
    name: str = "record_values.external_entry_id",
) -> str:
    normalized = _normalize_required_text(value, name)
    if normalized != external_entry_id:
        raise _validation_error(f"{name} must equal external_entry_id")
    return normalized


def _freeze_mapping(value: _Mapping[str, object]) -> _MappingProxyType:
    return _MappingProxyType({key: _freeze_value(item) for key, item in value.items()})


def _freeze_value(value: object) -> object:
    if isinstance(value, _Mapping):
        return _freeze_mapping(value)
    if type(value) is tuple:
        return tuple(_freeze_value(item) for item in value)
    return value


def _validate_track_values(values: _Mapping[str, object]) -> dict[str, object]:
    _validated_key_set(values, _RECORD_VALUE_KEYS["track"], "record_values")
    return {
        "target_race_date": _normalize_date(values["target_race_date"], "target_race_date"),
        "scheduled_start_at": _normalize_utc_datetime(values["scheduled_start_at"], "scheduled_start_at"),
        "place": _normalize_required_text(values["place"], "place"),
        "distance_m": _require_positive_int(values["distance_m"], "distance_m"),
        "track": _normalize_required_text(values["track"], "track"),
        "track_condition": _normalize_required_text(values["track_condition"], "track_condition"),
        "race_name": _normalize_optional_text(values["race_name"], "race_name"),
        "race_class": _normalize_optional_text(values["race_class"], "race_class"),
        "weather": _normalize_optional_text(values["weather"], "weather"),
    }


def _validate_entry_values(values: _Mapping[str, object], external_entry_id: str) -> dict[str, object]:
    _validated_key_set(values, _RECORD_VALUE_KEYS["entry"], "record_values")
    return {
        "external_entry_id": _validate_duplicate_external_entry(values["external_entry_id"], external_entry_id),
        "external_horse_id": _normalize_optional_text(values["external_horse_id"], "external_horse_id"),
        "horse_no": _require_positive_int(values["horse_no"], "horse_no"),
    }


def _validate_jockey_values(values: _Mapping[str, object], external_entry_id: str) -> dict[str, object]:
    _validated_key_set(values, _RECORD_VALUE_KEYS["jockey"], "record_values")
    return {
        "external_entry_id": _validate_duplicate_external_entry(values["external_entry_id"], external_entry_id),
        "jockey": _normalize_required_text(values["jockey"], "jockey"),
    }


def _validate_odds_values(values: _Mapping[str, object], external_entry_id: str) -> dict[str, object]:
    _validated_key_set(values, _RECORD_VALUE_KEYS["odds_win"], "record_values")
    return {
        "external_entry_id": _validate_duplicate_external_entry(values["external_entry_id"], external_entry_id),
        "horse_no": _require_positive_int(values["horse_no"], "horse_no"),
        "win_odds": _normalize_decimal(values["win_odds"], "win_odds", positive=True),
    }


def _validate_past_race_values(values: _Mapping[str, object]) -> dict[str, object]:
    _validated_key_set(values, _RECORD_VALUE_KEYS["past_race"], "record_values")
    return {
        "race_date": _normalize_date(values["race_date"], "race_date"),
        "place": _normalize_required_text(values["place"], "place"),
        "race_name": _normalize_required_text(values["race_name"], "race_name"),
        "race_class": _normalize_required_text(values["race_class"], "race_class"),
        "distance_m": _require_positive_int(values["distance_m"], "distance_m"),
        "track": _normalize_required_text(values["track"], "track"),
        "weather": _normalize_required_text(values["weather"], "weather"),
        "track_condition": _normalize_required_text(values["track_condition"], "track_condition"),
        "finish": _require_positive_int(values["finish"], "finish"),
        "reference_time_difference_seconds": _normalize_decimal(
            values["reference_time_difference_seconds"],
            "reference_time_difference_seconds",
            non_negative=True,
        ),
        "race_time": _normalize_required_text(values["race_time"], "race_time"),
        "weight": _normalize_decimal(values["weight"], "weight", non_negative=True),
        "weight_diff": _normalize_decimal(values["weight_diff"], "weight_diff"),
        "jockey": _normalize_required_text(values["jockey"], "jockey"),
        "popularity": _require_non_negative_int(values["popularity"], "popularity"),
        "odds": _normalize_decimal(values["odds"], "odds", non_negative=True),
        "passing_order": _normalize_text_allow_empty(values["passing_order"], "passing_order"),
        "fourth_corner_position": _require_non_negative_int(
            values["fourth_corner_position"], "fourth_corner_position"
        ),
    }


def _validate_absence_values(values: _Mapping[str, object], external_entry_id: str) -> dict[str, object]:
    _validated_key_set(values, _RECORD_VALUE_KEYS["past_race_absence"], "record_values")
    scope = _require_mapping(values["query_scope"], "query_scope")
    _validated_key_set(scope, frozenset({"external_entry_id", "target_race_date", "strictly_before_target_race"}), "query_scope")
    scope_entry_id = _validate_duplicate_external_entry(scope["external_entry_id"], external_entry_id, "query_scope.external_entry_id")
    strictly_before = scope["strictly_before_target_race"]
    if type(strictly_before) is not bool or strictly_before is not True:
        raise _validation_error("query_scope.strictly_before_target_race must be True")
    result_count = values["result_count"]
    if type(result_count) is not int or result_count != 0:
        raise _validation_error("result_count must be exact int 0")
    return {
        "external_entry_id": _validate_duplicate_external_entry(values["external_entry_id"], external_entry_id),
        "query_scope": {
            "external_entry_id": scope_entry_id,
            "target_race_date": _normalize_date(scope["target_race_date"], "query_scope.target_race_date"),
            "strictly_before_target_race": True,
        },
        "result_count": 0,
    }


def _validate_record_values(
    *,
    record_kind: str,
    value: object,
    external_entry_id: str | None,
) -> _MappingProxyType:
    values = _require_mapping(value, "record_values")
    if record_kind == "track":
        return _freeze_mapping(_validate_track_values(values))
    if external_entry_id is None:
        raise _validation_error("external_entry_id is required for entry-scoped record")
    if record_kind == "entry":
        return _freeze_mapping(_validate_entry_values(values, external_entry_id))
    if record_kind == "jockey":
        return _freeze_mapping(_validate_jockey_values(values, external_entry_id))
    if record_kind == "odds_win":
        return _freeze_mapping(_validate_odds_values(values, external_entry_id))
    if record_kind == "past_race":
        return _freeze_mapping(_validate_past_race_values(values))
    return _freeze_mapping(_validate_absence_values(values, external_entry_id))


def _json_value(value: object) -> object:
    if type(value) is _date:
        return value.isoformat()
    if type(value) is _datetime:
        return value.isoformat(timespec="microseconds")
    if type(value) is _Decimal:
        return format(_canonical_decimal(value), "f")
    if isinstance(value, _Mapping):
        return {key: _json_value(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_json_value(item) for item in value]
    return value


def _canonical_evidence(
    value: object,
    *,
    record_kind: str,
) -> tuple[_HistoricalInputEvidenceReference, ...]:
    if type(value) is not tuple:
        raise _validation_error("evidence must be tuple")
    if not value:
        raise _validation_error("evidence must not be empty")
    for item in value:
        if type(item) is not _HistoricalInputEvidenceReference:
            raise _validation_error("evidence item must be HistoricalInputEvidenceReference")
    ordered = tuple(sorted(value, key=lambda item: item.evidence_role))
    roles = tuple(item.evidence_role for item in ordered)
    if roles != _EVIDENCE_ROLES[record_kind] or len(set(roles)) != len(roles):
        raise _validation_error("evidence roles are invalid")
    observations: dict[tuple[str | None, str], tuple[_datetime | None, _datetime]] = {}
    for item in ordered:
        identity = (item.canonical_source_url, item.response_sha256)
        previous = observations.get(identity)
        times = (item.available_at, item.observed_at)
        if previous is not None and previous != times:
            raise _validation_error("same response evidence timestamps conflict")
        observations[identity] = times
    if record_kind == "past_race_absence" and ordered[0].canonical_source_url is None:
        raise _validation_error("canonical_source_url is required for past_race_absence")
    return ordered


def _evidence_payload(
    evidence: tuple[_HistoricalInputEvidenceReference, ...],
) -> list[dict[str, object]]:
    return [
        {
            "evidence_role": item.evidence_role,
            "canonical_source_url": item.canonical_source_url,
            "response_sha256": item.response_sha256,
        }
        for item in evidence
    ]


def _unchecked_payload(record: HistoricalInputSourceRecord) -> dict[str, object]:
    return {
        "schema_version": record.schema_version,
        "source_system": record.source_system,
        "record_kind": record.record_kind,
        "organization": record.organization,
        "external_race_id": record.external_race_id,
        "external_entry_id": record.external_entry_id,
        "provider_record_id": record.provider_record_id,
        "record_values": _json_value(record.record_values),
        "evidence": _evidence_payload(record.evidence),
    }


def _source_id_from_payload(*, record_kind: str, payload: dict[str, object]) -> str:
    encoded = _json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return f"his-v3:{record_kind}:{_hashlib.sha256(encoded).hexdigest()}"


@_dataclass(frozen=True, slots=True)
class HistoricalInputSourceRecord:
    schema_version: int = _field(default=3, init=False)
    record_kind: SourceRecordKind
    organization: str
    source_system: str
    external_race_id: str
    external_entry_id: str | None
    provider_record_id: str | None
    record_values: _Mapping[str, object]
    evidence: tuple[_HistoricalInputEvidenceReference, ...]
    source_id: str = _field(init=False)

    def __post_init__(self) -> None:
        if type(self.record_kind) is not str or self.record_kind not in _RECORD_KINDS:
            raise _validation_error("record_kind is invalid")
        object.__setattr__(self, "organization", _normalize_required_text(self.organization, "organization"))
        object.__setattr__(self, "source_system", _normalize_required_text(self.source_system, "source_system"))
        object.__setattr__(self, "external_race_id", _normalize_required_text(self.external_race_id, "external_race_id"))
        external_entry_id = _normalize_optional_text(self.external_entry_id, "external_entry_id")
        if self.record_kind == "track":
            if external_entry_id is not None:
                raise _validation_error("external_entry_id must be None for track")
        elif external_entry_id is None:
            raise _validation_error("external_entry_id is required for entry-scoped record")
        object.__setattr__(self, "external_entry_id", external_entry_id)
        provider_record_id = _normalize_optional_text(self.provider_record_id, "provider_record_id")
        if self.record_kind == "past_race" and provider_record_id is None:
            raise _validation_error("provider_record_id is required for past_race")
        object.__setattr__(self, "provider_record_id", provider_record_id)
        record_values = _validate_record_values(
            record_kind=self.record_kind,
            value=self.record_values,
            external_entry_id=external_entry_id,
        )
        object.__setattr__(self, "record_values", record_values)
        object.__setattr__(self, "evidence", _canonical_evidence(self.evidence, record_kind=self.record_kind))
        object.__setattr__(self, "source_id", _source_id_from_payload(record_kind=self.record_kind, payload=_unchecked_payload(self)))


def canonical_historical_input_source_payload(
    *,
    record: HistoricalInputSourceRecord,
) -> dict[str, object]:
    if type(record) is not HistoricalInputSourceRecord:
        raise _validation_error("record must be HistoricalInputSourceRecord")
    return _unchecked_payload(record)


def build_historical_input_source_id(
    *,
    record: HistoricalInputSourceRecord,
) -> str:
    payload = canonical_historical_input_source_payload(record=record)
    return _source_id_from_payload(record_kind=record.record_kind, payload=payload)


def validate_historical_input_source_record_set(
    *,
    records: _Sequence[HistoricalInputSourceRecord],
) -> tuple[HistoricalInputSourceRecord, ...]:
    if not isinstance(records, _Sequence) or isinstance(records, (str, bytes, bytearray)):
        raise _validation_error("records must be a sequence")
    result = tuple(records)
    source_ids: set[str] = set()
    past_race_payloads: dict[tuple[str, str, str, str], str] = {}
    for record in result:
        if type(record) is not HistoricalInputSourceRecord:
            raise _validation_error("records item must be HistoricalInputSourceRecord")
        if record.source_id in source_ids:
            raise HistoricalInputSourceConflictError("duplicate source_id")
        source_ids.add(record.source_id)
        if record.record_kind != "past_race":
            continue
        if record.external_entry_id is None or record.provider_record_id is None:
            raise _validation_error("past_race identity is incomplete")
        identity = (
            record.source_system,
            record.external_race_id,
            record.external_entry_id,
            record.provider_record_id,
        )
        existing_source_id = past_race_payloads.get(identity)
        if existing_source_id is not None and existing_source_id != record.source_id:
            raise HistoricalInputSourceConflictError("conflicting official past-race record")
        past_race_payloads[identity] = record.source_id
    return result
