"""Pure conversion from historical snapshots to simulation race inputs."""

from __future__ import annotations

from decimal import Decimal
import math
from typing import Literal

from scripts.simulation.historical_input_snapshots import (
    HistoricalInputProvenance,
    HistoricalInputSnapshot,
    HistoricalPastRaceSnapshot,
)
from scripts.simulation.models import (
    ImmutableRacePredictionInput,
    InputAuditEntry,
    InputSnapshotAudit,
    PastRaceSnapshot,
    SimulationRaceInput,
    TrackConditionsSnapshot,
)


__all__ = (
    "HistoricalInputSnapshotSimulationAdapterError",
    "build_simulation_race_input_from_historical_snapshot",
)


class HistoricalInputSnapshotSimulationAdapterError(ValueError):
    """The exact historical snapshot cannot be converted without information loss."""


_DecimalPolicy = Literal["positive", "non_negative", "signed"]


def _decimal_to_float(
    value: object,
    *,
    name: str,
    policy: _DecimalPolicy,
) -> float:
    if type(value) is not Decimal:
        raise HistoricalInputSnapshotSimulationAdapterError(f"{name} must be Decimal")
    if not value.is_finite():
        raise HistoricalInputSnapshotSimulationAdapterError(f"{name} must be finite")
    if policy == "positive" and value <= 0:
        raise HistoricalInputSnapshotSimulationAdapterError(f"{name} must be positive")
    if policy == "non_negative" and value < 0:
        raise HistoricalInputSnapshotSimulationAdapterError(f"{name} must be non-negative")
    try:
        converted = float(value)
    except (OverflowError, ValueError) as error:
        raise HistoricalInputSnapshotSimulationAdapterError(
            f"{name} cannot be represented as float"
        ) from error
    if not math.isfinite(converted):
        raise HistoricalInputSnapshotSimulationAdapterError(
            f"{name} must convert to a finite float"
        )
    if value != 0 and converted == 0.0:
        raise HistoricalInputSnapshotSimulationAdapterError(
            f"{name} underflows to zero"
        )
    if value > 0 and converted <= 0.0:
        raise HistoricalInputSnapshotSimulationAdapterError(
            f"{name} loses its positive sign"
        )
    if value < 0 and converted >= 0.0:
        raise HistoricalInputSnapshotSimulationAdapterError(
            f"{name} loses its negative sign"
        )
    return converted


def _build_past_race_snapshot(
    item: HistoricalPastRaceSnapshot,
) -> PastRaceSnapshot:
    return PastRaceSnapshot(
        horse_id=item.race_entry_id,
        race_date=item.race_date.isoformat(),
        place=item.place,
        race_name=item.race_name,
        race_class=item.race_class,
        distance=item.distance_m,
        track=item.track,
        weather=item.weather,
        track_condition=item.track_condition,
        finish=item.finish,
        time=item.race_time,
        weight=_decimal_to_float(item.weight, name="past_race.weight", policy="non_negative"),
        weight_diff=_decimal_to_float(item.weight_diff, name="past_race.weight_diff", policy="signed"),
        jockey=item.jockey,
        popularity=item.popularity,
        odds=_decimal_to_float(item.odds, name="past_race.odds", policy="non_negative"),
        passing_order=item.passing_order,
        fourth_corner_position=item.fourth_corner_position,
    )


def _build_audit_entry(provenance: HistoricalInputProvenance) -> InputAuditEntry:
    observed_at = max(item.observed_at for item in provenance.evidence)
    if any(item.available_at is None for item in provenance.evidence):
        available_at = None
    else:
        available_at = max(
            item.available_at
            for item in provenance.evidence
            if item.available_at is not None
        )
    return InputAuditEntry(
        input_type=provenance.input_type,
        audit_key=provenance.audit_key,
        source=provenance.source,
        source_id=provenance.source_id,
        race_entry_id=provenance.race_entry_id,
        available_at=available_at,
        observed_at=observed_at,
        past_race_index=provenance.past_race_index,
    )


def build_simulation_race_input_from_historical_snapshot(
    *,
    snapshot: HistoricalInputSnapshot,
) -> SimulationRaceInput:
    """Build one immutable, causally audited simulation input from one exact snapshot."""

    if type(snapshot) is not HistoricalInputSnapshot:
        raise HistoricalInputSnapshotSimulationAdapterError(
            "snapshot must be HistoricalInputSnapshot"
        )

    entries = sorted(snapshot.entries, key=lambda item: item.entry_order)
    provenance_by_audit_key = {
        item.audit_key: item
        for item in snapshot.provenance
    }
    horse_past_races: dict[int, tuple[PastRaceSnapshot, ...]] = {}
    jockey_names_by_horse: dict[int, str] = {}
    odds_by_horse: dict[int, float] = {}
    audit_entries: list[InputAuditEntry] = []

    for entry in entries:
        race_entry_id = entry.race_entry_id
        past_races = sorted(
            (
                item
                for item in snapshot.past_races
                if item.race_entry_id == race_entry_id
            ),
            key=lambda item: item.past_race_index,
        )
        horse_past_races[race_entry_id] = tuple(
            _build_past_race_snapshot(item)
            for item in past_races
        )
        jockey_names_by_horse[race_entry_id] = entry.jockey
        odds_by_horse[race_entry_id] = _decimal_to_float(
            entry.win_odds,
            name="entry.win_odds",
            policy="positive",
        )

        for audit_key in (
            f"entry/{race_entry_id}",
            f"odds/{race_entry_id}",
            f"jockey/{race_entry_id}",
        ):
            audit_entries.append(
                _build_audit_entry(provenance_by_audit_key[audit_key])
            )
        if past_races:
            for item in past_races:
                audit_entries.append(
                    _build_audit_entry(
                        provenance_by_audit_key[
                            f"past_race/{race_entry_id}/{item.past_race_index}"
                        ]
                    )
                )
        else:
            audit_entries.append(
                _build_audit_entry(
                    provenance_by_audit_key[f"past_race/{race_entry_id}/none"]
                )
            )

    immutable_pipeline_input = ImmutableRacePredictionInput(
        horse_past_races=horse_past_races,
        jockey_names_by_horse=jockey_names_by_horse,
        track_conditions=TrackConditionsSnapshot(
            place=snapshot.race.place,
            distance=snapshot.race.distance_m,
            track=snapshot.race.track,
            track_condition=snapshot.race.track_condition,
        ),
        odds_by_horse=odds_by_horse,
        race_horse_count=len(snapshot.entries),
        race_id=snapshot.internal_race_id,
        prediction_time=snapshot.information_cutoff.isoformat(timespec="microseconds"),
    )
    audit_entries.append(_build_audit_entry(provenance_by_audit_key["track"]))
    input_snapshot_audit = InputSnapshotAudit(
        dataset_id=snapshot.identity.dataset_id,
        source=snapshot.identity.source_identity.source_system,
        captured_at=snapshot.identity.captured_at,
        entries=tuple(audit_entries),
        is_complete=True,
    )
    return SimulationRaceInput(
        race_id=snapshot.internal_race_id,
        target_race_date=snapshot.race.target_race_date,
        scheduled_start_at=snapshot.race.scheduled_start_at,
        information_cutoff=snapshot.information_cutoff,
        pipeline_input=immutable_pipeline_input,
        input_snapshot_audit=input_snapshot_audit,
    )
