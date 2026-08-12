"""Pure assembly of complete historical input snapshots from source records."""

from __future__ import annotations

from collections.abc import Mapping as _Mapping
from datetime import datetime as _datetime

from scripts.simulation.historical_input_snapshots import (
    HistoricalExternalEntryIdentity as _HistoricalExternalEntryIdentity,
    HistoricalExternalRaceIdentity as _HistoricalExternalRaceIdentity,
    HistoricalInputProvenance as _HistoricalInputProvenance,
    HistoricalInputSnapshot as _HistoricalInputSnapshot,
    HistoricalInputSnapshotIdentity as _HistoricalInputSnapshotIdentity,
    HistoricalPastRaceSnapshot as _HistoricalPastRaceSnapshot,
    HistoricalRaceEntrySnapshot as _HistoricalRaceEntrySnapshot,
    HistoricalRaceSnapshot as _HistoricalRaceSnapshot,
    HistoricalSourceIdentity as _HistoricalSourceIdentity,
)
from scripts.simulation.historical_input_source_records import (
    HistoricalInputSourceRecord as _HistoricalInputSourceRecord,
    validate_historical_input_source_record_set as _validate_historical_input_source_record_set,
)


class HistoricalInputSnapshotAssemblyError(ValueError):
    """Raised when a supplied source-record set cannot form a complete snapshot."""


def _error(message: str) -> HistoricalInputSnapshotAssemblyError:
    return HistoricalInputSnapshotAssemblyError(message)


def _require_dataset_id(value: object) -> str:
    if type(value) is not str or not value:
        raise _error("dataset_id must be a non-empty str")
    return value


def _require_positive_int(value: object, name: str) -> int:
    if type(value) is not int or value <= 0:
        raise _error(f"{name} must be a positive int")
    return value


def _require_aware_datetime(value: object, name: str) -> _datetime:
    if type(value) is not _datetime:
        raise _error(f"{name} must be datetime")
    try:
        aware = value.tzinfo is not None and value.utcoffset() is not None
    except (TypeError, ValueError, OverflowError) as error:
        raise _error(f"{name} must be timezone-aware") from error
    if not aware:
        raise _error(f"{name} must be timezone-aware")
    return value


def _validate_mapping(value: object) -> dict[str, int]:
    if not isinstance(value, _Mapping):
        raise _error("race_entry_id_by_external_entry_id must be Mapping")
    result: dict[str, int] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise _error("race_entry_id_by_external_entry_id key must be str")
        result[key] = _require_positive_int(item, "race_entry_id_by_external_entry_id value")
    if len(set(result.values())) != len(result):
        raise _error("race_entry_id_by_external_entry_id values must be unique")
    return result


def _validate_temporal_eligibility(
    *,
    records: tuple[_HistoricalInputSourceRecord, ...],
    captured_at: _datetime,
    information_cutoff: _datetime,
    scheduled_start_at: _datetime,
) -> None:
    if captured_at > information_cutoff:
        raise _error("captured_at must not be later than information_cutoff")
    if information_cutoff > scheduled_start_at:
        raise _error("information_cutoff must not be later than scheduled_start_at")
    for record in records:
        for evidence in record.evidence:
            if evidence.observed_at > captured_at or evidence.observed_at > information_cutoff:
                raise _error("source evidence observed_at is not causally eligible")
            if evidence.available_at is not None:
                if evidence.available_at > evidence.observed_at:
                    raise _error("source evidence available_at is later than observed_at")
                if evidence.available_at > captured_at or evidence.available_at > information_cutoff:
                    raise _error("source evidence available_at is not causally eligible")


def _provenance(
    *,
    record: _HistoricalInputSourceRecord,
    race_entry_id: int | None,
    past_race_index: int | None,
) -> _HistoricalInputProvenance:
    if record.record_kind == "track":
        return _HistoricalInputProvenance(
            input_type="track",
            audit_key="track",
            source=record.source_system,
            source_id=record.source_id,
            race_entry_id=None,
            evidence=record.evidence,
        )
    if race_entry_id is None:
        raise _error("entry-scoped provenance requires race_entry_id")
    if record.record_kind == "entry":
        input_type = "entry"
        audit_key = f"entry/{race_entry_id}"
    elif record.record_kind == "jockey":
        input_type = "jockey"
        audit_key = f"jockey/{race_entry_id}"
    elif record.record_kind == "odds_win":
        input_type = "odds"
        audit_key = f"odds/{race_entry_id}"
    elif record.record_kind == "past_race":
        if past_race_index is None:
            raise _error("past_race provenance requires past_race_index")
        input_type = "past_race"
        audit_key = f"past_race/{race_entry_id}/{past_race_index}"
    elif record.record_kind == "past_race_absence":
        input_type = "past_race"
        audit_key = f"past_race/{race_entry_id}/none"
    else:
        raise _error("record_kind is unsupported")
    return _HistoricalInputProvenance(
        input_type=input_type,
        audit_key=audit_key,
        source=record.source_system,
        source_id=record.source_id,
        race_entry_id=race_entry_id,
        evidence=record.evidence,
        past_race_index=past_race_index,
    )


def build_historical_input_snapshot(
    *,
    dataset_id: str,
    internal_race_id: int,
    information_cutoff: _datetime,
    captured_at: _datetime,
    source_records: tuple[_HistoricalInputSourceRecord, ...],
    race_entry_id_by_external_entry_id: _Mapping[str, int],
) -> _HistoricalInputSnapshot:
    """Build one complete immutable snapshot from caller-supplied source records."""
    normalized_dataset_id = _require_dataset_id(dataset_id)
    normalized_internal_race_id = _require_positive_int(internal_race_id, "internal_race_id")
    normalized_information_cutoff = _require_aware_datetime(information_cutoff, "information_cutoff")
    normalized_captured_at = _require_aware_datetime(captured_at, "captured_at")
    if type(source_records) is not tuple:
        raise _error("source_records must be tuple")
    validated_records = _validate_historical_input_source_record_set(records=source_records)
    normalized_mapping = _validate_mapping(race_entry_id_by_external_entry_id)
    if not validated_records:
        raise _error("source_records must not be empty")

    first = validated_records[0]
    family = (first.organization, first.source_system, first.external_race_id)
    tracks: list[_HistoricalInputSourceRecord] = []
    groups: dict[str, dict[str, list[_HistoricalInputSourceRecord]]] = {}
    for record in validated_records:
        if (record.organization, record.source_system, record.external_race_id) != family:
            raise _error("source records must share one source family and external race")
        if record.record_kind == "track":
            tracks.append(record)
            continue
        external_entry_id = record.external_entry_id
        if external_entry_id is None:
            raise _error("entry-scoped record requires external_entry_id")
        group = groups.setdefault(
            external_entry_id,
            {"entry": [], "jockey": [], "odds_win": [], "past_race": [], "past_race_absence": []},
        )
        group[record.record_kind].append(record)
    if len(tracks) != 1:
        raise _error("source records require exactly one track")
    track = tracks[0]

    entry_ids = {
        external_entry_id
        for external_entry_id, group in groups.items()
        if group["entry"]
    }
    if not entry_ids:
        raise _error("source records require at least one entry")
    if set(normalized_mapping) != entry_ids:
        raise _error("race_entry_id_by_external_entry_id keys are incomplete or incompatible")
    for external_entry_id, group in groups.items():
        if external_entry_id not in entry_ids:
            raise _error("entry-scoped source record is orphaned")
        for record_kind in ("entry", "jockey", "odds_win"):
            if len(group[record_kind]) != 1:
                raise _error(f"external entry requires exactly one {record_kind} record")
        past_count = len(group["past_race"])
        absence_count = len(group["past_race_absence"])
        if (past_count == 0 and absence_count == 0) or (past_count > 0 and absence_count > 0):
            raise _error("external entry requires exactly one form of past evidence")
        if absence_count > 1:
            raise _error("external entry requires exactly one past_race_absence record")

    track_values = track.record_values
    race = _HistoricalRaceSnapshot(
        target_race_date=track_values["target_race_date"],
        scheduled_start_at=track_values["scheduled_start_at"],
        place=track_values["place"],
        distance_m=track_values["distance_m"],
        track=track_values["track"],
        track_condition=track_values["track_condition"],
        race_name=track_values["race_name"],
        race_class=track_values["race_class"],
        weather=track_values["weather"],
    )
    _validate_temporal_eligibility(
        records=validated_records,
        captured_at=normalized_captured_at,
        information_cutoff=normalized_information_cutoff,
        scheduled_start_at=race.scheduled_start_at,
    )
    organization, source_system, external_race_id = family
    source_identity = _HistoricalSourceIdentity(
        organization=organization,
        source_system=source_system,
        external_race_id=external_race_id,
        source_url=track.evidence[0].canonical_source_url,
    )
    external_race_identity = _HistoricalExternalRaceIdentity(
        organization=organization,
        source_system=source_system,
        external_race_id=external_race_id,
    )
    identity = _HistoricalInputSnapshotIdentity(
        dataset_id=normalized_dataset_id,
        source_identity=source_identity,
        captured_at=normalized_captured_at,
    )

    entry_records = tuple(groups[external_entry_id]["entry"][0] for external_entry_id in entry_ids)
    horse_numbers = tuple(record.record_values["horse_no"] for record in entry_records)
    if len(set(horse_numbers)) != len(horse_numbers):
        raise _error("target entry horse_no values must be unique")
    ordered_entry_records = tuple(sorted(entry_records, key=lambda record: record.record_values["horse_no"]))
    entries: list[_HistoricalRaceEntrySnapshot] = []
    past_races: list[_HistoricalPastRaceSnapshot] = []
    past_race_indexes: dict[str, int] = {}
    for entry_order, entry_record in enumerate(ordered_entry_records):
        external_entry_id = entry_record.external_entry_id
        if external_entry_id is None:
            raise _error("entry record requires external_entry_id")
        group = groups[external_entry_id]
        jockey_record = group["jockey"][0]
        odds_record = group["odds_win"][0]
        entry_values = entry_record.record_values
        odds_values = odds_record.record_values
        if entry_values["horse_no"] != odds_values["horse_no"]:
            raise _error("entry and odds_win horse_no must agree")
        race_entry_id = normalized_mapping[external_entry_id]
        entries.append(
            _HistoricalRaceEntrySnapshot(
                race_entry_id=race_entry_id,
                external_entry_identity=_HistoricalExternalEntryIdentity(
                    external_race_identity=external_race_identity,
                    external_entry_id=external_entry_id,
                    external_horse_id=entry_values["external_horse_id"],
                ),
                horse_no=entry_values["horse_no"],
                jockey=jockey_record.record_values["jockey"],
                win_odds=odds_values["win_odds"],
                entry_order=entry_order,
            )
        )
        past_records = group["past_race"]
        if past_records:
            past_dates = tuple(record.record_values["race_date"] for record in past_records)
            if len(set(past_dates)) != len(past_dates):
                raise _error("past_race dates are ambiguous")
            ordered_past_records = tuple(
                sorted(past_records, key=lambda record: record.record_values["race_date"], reverse=True)
            )
            for past_race_index, past_record in enumerate(ordered_past_records):
                values = past_record.record_values
                if values["race_date"] >= race.target_race_date:
                    raise _error("past_race must precede target race")
                past_races.append(
                    _HistoricalPastRaceSnapshot(
                        race_entry_id=race_entry_id,
                        past_race_index=past_race_index,
                        race_date=values["race_date"],
                        place=values["place"],
                        race_name=values["race_name"],
                        race_class=values["race_class"],
                        distance_m=values["distance_m"],
                        track=values["track"],
                        weather=values["weather"],
                        track_condition=values["track_condition"],
                        finish=values["finish"],
                        race_time=values["race_time"],
                        weight=values["weight"],
                        weight_diff=values["weight_diff"],
                        jockey=values["jockey"],
                        popularity=values["popularity"],
                        odds=values["odds"],
                        passing_order=values["passing_order"],
                        fourth_corner_position=values["fourth_corner_position"],
                    )
                )
                past_race_indexes[past_record.source_id] = past_race_index
        else:
            absence_record = group["past_race_absence"][0]
            query_scope = absence_record.record_values["query_scope"]
            if query_scope["target_race_date"] != race.target_race_date:
                raise _error("past_race_absence target_race_date is incompatible")

    provenance: list[_HistoricalInputProvenance] = []
    for record in validated_records:
        if record.record_kind == "track":
            race_entry_id = None
        else:
            external_entry_id = record.external_entry_id
            if external_entry_id is None:
                raise _error("entry-scoped record requires external_entry_id")
            race_entry_id = normalized_mapping[external_entry_id]
        provenance.append(
            _provenance(
                record=record,
                race_entry_id=race_entry_id,
                past_race_index=past_race_indexes.get(record.source_id),
            )
        )
    return _HistoricalInputSnapshot(
        identity=identity,
        internal_race_id=normalized_internal_race_id,
        information_cutoff=normalized_information_cutoff,
        race=race,
        entries=tuple(entries),
        past_races=tuple(sorted(past_races, key=lambda item: (item.race_entry_id, item.past_race_index))),
        provenance=tuple(sorted(provenance, key=lambda item: item.audit_key)),
    )
