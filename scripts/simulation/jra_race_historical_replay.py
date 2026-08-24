"""Pure seed-bound orchestration of one complete JRA historical replay."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass
from datetime import datetime as _datetime
from typing import Protocol as _Protocol

from scripts.simulation.historical_input_snapshot_builder import (
    HistoricalInputSnapshotAssemblyError as _SnapshotAssemblyError,
    build_historical_input_snapshot as _build_snapshot,
)
from scripts.simulation.historical_input_snapshots import HistoricalInputSnapshot as _Snapshot
from scripts.simulation.historical_input_source_records import HistoricalInputSourceRecord as _Record
from scripts.simulation.jra_historical_input_source_collection import (
    JRAHistoricalFinalWinOddsResponseProvider as _FinalOddsProvider,
    JRAHistoricalRaceResultResponseProvider as _RaceResultProvider,
    JRAHistoricalSourceCollection as _HistoricalCollection,
    JRAHistoricalSourceCollectionUnavailableError as _HistoricalUnavailable,
    JRAHistoricalSourceCollectionUnsupportedError as _HistoricalUnsupported,
    JRAHistoricalSourceCollectionValidationError as _HistoricalValidation,
    collect_jra_historical_input_source_records as _collect_history,
)
from scripts.simulation.jra_official_identity import (
    JRAOfficialIdentityValidationError as _IdentityError,
    parse_jra_external_race_id as _parse_race_id,
    parse_jra_race_card_url_identity as _parse_card_url,
)
from scripts.simulation.jra_official_response_capture import (
    JRAOfficialTargetRaceCardResponseCapture as _TargetCapture,
)
from scripts.simulation.jra_race_replay_seed import JRARaceReplaySeed as _Seed
from scripts.simulation.jra_target_horse_history_resolution import (
    JRATargetHorseHistoryResolutionUnavailableError as _HorseHistoryUnavailable,
    JRATargetHorseHistoryResolutionValidationError as _HorseHistoryValidation,
    JRATargetHorseHistoryResponseProvider as _HorseHistoryProvider,
    resolve_jra_target_horse_history_response as _resolve_horse_history,
)
from scripts.simulation.jra_target_race_card_locator import JRATargetRaceCardLocator as _TargetLocator
from scripts.simulation.jra_target_race_card_resolution import (
    JRATargetRaceCardResolution as _TargetResolution,
    JRATargetRaceCardResolutionUnavailableError as _TargetUnavailable,
    JRATargetRaceCardResolutionValidationError as _TargetValidation,
    JRATargetRaceSelectionCaptureProvider as _SelectionProvider,
    resolve_jra_target_race_card_response as _resolve_target,
)
from scripts.simulation.jra_target_race_input_source import (
    JRATargetHorseHistoryLocator as _HorseHistoryLocator,
    JRATargetRaceSourceCollection as _TargetSources,
    JRATargetRaceSourceUnsupportedError as _TargetSourceUnsupported,
    JRATargetRaceSourceValidationError as _TargetSourceValidation,
    normalize_jra_target_race_input_source_records as _normalize_target,
)


class JRARaceHistoricalReplayError(ValueError):
    """Base error for one seed-bound JRA historical replay."""


class JRARaceHistoricalReplayValidationError(JRARaceHistoricalReplayError):
    """Raised when replay input, provenance, or assembled evidence contradicts."""


class JRARaceHistoricalReplayUnavailableError(JRARaceHistoricalReplayError):
    """Raised when exact required causally eligible evidence is unavailable."""


class JRARaceHistoricalReplayUnsupportedError(JRARaceHistoricalReplayError):
    """Raised when official evidence is outside the supported replay envelope."""


class _JRATargetRaceCardCaptureByIdProvider(_Protocol):
    def __call__(
        self,
        *,
        capture_id: str,
    ) -> _TargetCapture | None: ...


def _validation(message: str) -> JRARaceHistoricalReplayValidationError:
    return JRARaceHistoricalReplayValidationError(message)


@_dataclass(frozen=True, slots=True)
class JRARaceHistoricalReplayResult:
    """One complete snapshot retaining its exact immutable JRA replay seed."""

    seed: _Seed
    snapshot: _Snapshot

    def __post_init__(self) -> None:
        if type(self.seed) is not _Seed or type(self.snapshot) is not _Snapshot:
            raise _validation("result requires exact seed and snapshot")
        seed = self.seed
        snapshot = self.snapshot
        source = snapshot.identity.source_identity
        if (
            snapshot.identity.dataset_id != seed.dataset_id
            or source.organization != "JRA"
            or source.source_system != "jra_official"
            or source.external_race_id != seed.external_race_id
            or snapshot.identity.captured_at != seed.captured_at
            or snapshot.internal_race_id != seed.internal_race_id
            or snapshot.information_cutoff != seed.information_cutoff
            or len(snapshot.entries) != len(seed.entries)
        ):
            raise _validation("snapshot provenance disagrees with replay seed")
        for snapshot_entry, seed_entry in zip(snapshot.entries, seed.entries, strict=True):
            if (
                snapshot_entry.entry_order != seed_entry.entry_order
                or snapshot_entry.external_entry_identity.external_entry_id
                != seed_entry.external_entry_id
                or snapshot_entry.external_entry_identity.external_horse_id
                != seed_entry.external_horse_id
                or snapshot_entry.horse_no != seed_entry.horse_no
                or snapshot_entry.race_entry_id != seed_entry.internal_race_entry_id
            ):
                raise _validation("snapshot entry identity disagrees with replay seed")


class _SeedBoundTargetRaceCardCaptureProvider:
    __slots__ = ("_provider", "_seed")

    def __init__(
        self,
        *,
        seed: _Seed,
        provider: _JRATargetRaceCardCaptureByIdProvider,
    ) -> None:
        self._seed = seed
        self._provider = provider

    def __call__(
        self,
        *,
        locator: _TargetLocator,
        observed_at_not_after: _datetime,
    ) -> _TargetCapture | None:
        seed = self._seed
        if type(locator) is not _TargetLocator:
            raise _validation("target-card locator must be exact JRATargetRaceCardLocator")
        if (
            locator.external_race_id != seed.external_race_id
            or locator.canonical_target_race_card_url != seed.canonical_target_race_card_url
        ):
            raise _validation("target-card locator disagrees with replay seed")
        if observed_at_not_after != seed.captured_at:
            raise _validation("target-card observation bound disagrees with replay seed")
        capture = self._provider(capture_id=seed.target_race_card_capture_id)
        if capture is None:
            return None
        if type(capture) is not _TargetCapture:
            raise _validation("exact target-card provider response is invalid")
        if (
            capture.capture_id != seed.target_race_card_capture_id
            or capture.response_sha256 != seed.target_race_card_response_sha256
            or capture.canonical_source_url != seed.canonical_target_race_card_url
            or capture.observed_at > seed.captured_at
        ):
            raise _validation("exact target-card capture disagrees with replay seed")
        try:
            if _parse_card_url(capture.canonical_source_url) != _parse_race_id(seed.external_race_id):
                raise ValueError
        except (_IdentityError, TypeError, ValueError) as error:
            raise _validation("exact target-card capture race identity disagrees with replay seed") from error
        return capture


def _resolve_seed_target(
    *,
    seed: _Seed,
    target_race_selection_capture_provider: _SelectionProvider,
    target_race_card_capture_by_id_provider: _JRATargetRaceCardCaptureByIdProvider,
) -> _TargetResolution:
    adapter = _SeedBoundTargetRaceCardCaptureProvider(
        seed=seed,
        provider=target_race_card_capture_by_id_provider,
    )
    try:
        resolution = _resolve_target(
            external_race_id=seed.external_race_id,
            target_race_selection_capture_id=seed.target_race_selection_capture_id,
            captured_at=seed.captured_at,
            target_race_selection_capture_provider=target_race_selection_capture_provider,
            target_race_card_capture_provider=adapter,
        )
    except _TargetValidation as error:
        raise _validation("target-card resolution is invalid") from error
    except _TargetUnavailable as error:
        raise JRARaceHistoricalReplayUnavailableError(
            "required target-card evidence is unavailable"
        ) from error
    if type(resolution) is not _TargetResolution:
        raise _validation("target-card resolution result is invalid")
    if (
        resolution.target_race_selection_capture_id
        != seed.target_race_selection_capture_id
        or resolution.target_race_card_capture_id != seed.target_race_card_capture_id
        or resolution.target_race_card_response_sha256
        != seed.target_race_card_response_sha256
        or resolution.discovery.locator.external_race_id != seed.external_race_id
        or resolution.discovery.locator.canonical_target_race_card_url
        != seed.canonical_target_race_card_url
        or resolution.response.response_url != seed.canonical_target_race_card_url
        or resolution.captured_at != seed.captured_at
    ):
        raise _validation("target-card resolution provenance disagrees with replay seed")
    return resolution


def _normalize_seed_target(*, seed: _Seed, resolution: _TargetResolution) -> _TargetSources:
    try:
        target_sources = _normalize_target(response=resolution.response)
    except _TargetSourceValidation as error:
        raise _validation("target source evidence is invalid") from error
    except _TargetSourceUnsupported as error:
        raise JRARaceHistoricalReplayUnsupportedError(
            "target source evidence is unsupported"
        ) from error
    if type(target_sources) is not _TargetSources:
        raise _validation("target source result is invalid")
    if (
        type(target_sources.target_track_record) is not _Record
        or target_sources.target_track_record.external_race_id != seed.external_race_id
    ):
        raise _validation("target track identity disagrees with replay seed")
    if (
        len(target_sources.target_entry_records) != len(seed.entries)
        or len(target_sources.target_horse_history_locators) != len(seed.entries)
    ):
        raise _validation("target entry count disagrees with replay seed")
    for target_entry, locator, seed_entry in zip(
        target_sources.target_entry_records,
        target_sources.target_horse_history_locators,
        seed.entries,
        strict=True,
    ):
        if type(target_entry) is not _Record or type(locator) is not _HorseHistoryLocator:
            raise _validation("target entry or horse-history locator type is invalid")
        values = target_entry.record_values
        if (
            target_entry.external_entry_id != seed_entry.external_entry_id
            or values.get("external_entry_id") != seed_entry.external_entry_id
            or values.get("external_horse_id") != seed_entry.external_horse_id
            or values.get("horse_no") != seed_entry.horse_no
            or locator.external_race_id != seed.external_race_id
            or locator.external_entry_id != seed_entry.external_entry_id
            or locator.external_horse_id != seed_entry.external_horse_id
        ):
            raise _validation("target entry or horse-history locator disagrees with replay seed")
    try:
        scheduled_start_at = target_sources.target_track_record.record_values[
            "scheduled_start_at"
        ]
    except KeyError as error:
        raise _validation("target scheduled start is missing") from error
    if type(scheduled_start_at) is not _datetime:
        raise _validation("target scheduled start must be exact datetime")
    try:
        if scheduled_start_at.tzinfo is None or scheduled_start_at.utcoffset() is None:
            raise ValueError
    except (OverflowError, TypeError, ValueError) as error:
        raise _validation("target scheduled start must be timezone-aware") from error
    if not seed.captured_at <= seed.information_cutoff <= scheduled_start_at:
        raise _validation("replay seed times exceed target scheduled start")
    return target_sources


def _collect_seed_history(
    *,
    seed: _Seed,
    target_sources: _TargetSources,
    horse_history_response_provider: _HorseHistoryProvider,
    race_result_response_provider: _RaceResultProvider,
    final_win_odds_response_provider: _FinalOddsProvider,
) -> tuple[_HistoricalCollection, ...]:
    collections: list[_HistoricalCollection] = []
    track = target_sources.target_track_record
    for target_entry, locator, seed_entry in zip(
        target_sources.target_entry_records,
        target_sources.target_horse_history_locators,
        seed.entries,
        strict=True,
    ):
        try:
            horse_history = _resolve_horse_history(
                target_track_record=track,
                target_entry_record=target_entry,
                locator=locator,
                observed_at_not_after=seed.captured_at,
                horse_history_response_provider=horse_history_response_provider,
            )
        except _HorseHistoryValidation as error:
            raise _validation("target horse-history resolution is invalid") from error
        except _HorseHistoryUnavailable as error:
            raise JRARaceHistoricalReplayUnavailableError(
                "required target horse-history evidence is unavailable"
            ) from error
        try:
            collection = _collect_history(
                target_track_record=track,
                target_entry_record=target_entry,
                horse_history_response=horse_history,
                observed_at_not_after=seed.captured_at,
                race_result_response_provider=race_result_response_provider,
                final_win_odds_response_provider=final_win_odds_response_provider,
            )
        except _HistoricalValidation as error:
            raise _validation("historical source collection is invalid") from error
        except _HistoricalUnavailable as error:
            raise JRARaceHistoricalReplayUnavailableError(
                "required historical evidence is unavailable"
            ) from error
        except _HistoricalUnsupported as error:
            raise JRARaceHistoricalReplayUnsupportedError(
                "historical evidence is unsupported"
            ) from error
        if type(collection) is not _HistoricalCollection:
            raise _validation("historical source collection result is invalid")
        if (
            collection.target_external_race_id != seed.external_race_id
            or collection.target_external_entry_id != seed_entry.external_entry_id
        ):
            raise _validation("historical source collection disagrees with replay seed")
        collections.append(collection)
    return tuple(collections)


def _source_union(
    *,
    target_sources: _TargetSources,
    collections: tuple[_HistoricalCollection, ...],
) -> tuple[_Record, ...]:
    records = tuple(target_sources.source_records) + tuple(
        record for collection in collections for record in collection.source_records
    )
    if any(type(record) is not _Record for record in records):
        raise _validation("source union contains an invalid record")
    source_ids = tuple(record.source_id for record in records)
    if len(set(source_ids)) != len(source_ids):
        raise _validation("source union contains duplicate source IDs")
    return records


def build_jra_race_historical_replay(
    *,
    seed: _Seed,
    target_race_selection_capture_provider: _SelectionProvider,
    target_race_card_capture_by_id_provider: _JRATargetRaceCardCaptureByIdProvider,
    horse_history_response_provider: _HorseHistoryProvider,
    race_result_response_provider: _RaceResultProvider,
    final_win_odds_response_provider: _FinalOddsProvider,
) -> JRARaceHistoricalReplayResult:
    """Build one complete deterministic JRA snapshot from exact retained evidence."""

    providers = (
        target_race_selection_capture_provider,
        target_race_card_capture_by_id_provider,
        horse_history_response_provider,
        race_result_response_provider,
        final_win_odds_response_provider,
    )
    if type(seed) is not _Seed:
        raise _validation("seed must be exact JRARaceReplaySeed")
    if any(not callable(provider) for provider in providers):
        raise _validation("all replay evidence providers must be callable")
    resolution = _resolve_seed_target(
        seed=seed,
        target_race_selection_capture_provider=target_race_selection_capture_provider,
        target_race_card_capture_by_id_provider=target_race_card_capture_by_id_provider,
    )
    target_sources = _normalize_seed_target(seed=seed, resolution=resolution)
    collections = _collect_seed_history(
        seed=seed,
        target_sources=target_sources,
        horse_history_response_provider=horse_history_response_provider,
        race_result_response_provider=race_result_response_provider,
        final_win_odds_response_provider=final_win_odds_response_provider,
    )
    records = _source_union(target_sources=target_sources, collections=collections)
    mapping = {
        entry.external_entry_id: entry.internal_race_entry_id for entry in seed.entries
    }
    if set(mapping) != {
        record.external_entry_id for record in target_sources.target_entry_records
    }:
        raise _validation("snapshot entry mapping disagrees with normalized target entries")
    try:
        snapshot = _build_snapshot(
            dataset_id=seed.dataset_id,
            internal_race_id=seed.internal_race_id,
            captured_at=seed.captured_at,
            information_cutoff=seed.information_cutoff,
            source_records=records,
            race_entry_id_by_external_entry_id=mapping,
        )
    except (_SnapshotAssemblyError, ValueError) as error:
        raise _validation("historical snapshot assembly is invalid") from error
    return JRARaceHistoricalReplayResult(seed=seed, snapshot=snapshot)


__all__ = (
    "JRARaceHistoricalReplayError",
    "JRARaceHistoricalReplayValidationError",
    "JRARaceHistoricalReplayUnavailableError",
    "JRARaceHistoricalReplayUnsupportedError",
    "JRARaceHistoricalReplayResult",
    "build_jra_race_historical_replay",
)


if "annotations" in globals():
    del annotations
