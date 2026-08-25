"""Persist one exact seed-bound JRA historical replay snapshot."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass
import re as _re
from typing import Protocol as _Protocol

from scripts.simulation.historical_input_snapshots import (
    HistoricalInputSnapshot as _Snapshot,
    HistoricalInputSnapshotIdentity as _SnapshotIdentity,
)
from scripts.simulation.jra_historical_input_source_collection import (
    JRAHistoricalFinalWinOddsResponseProvider as _FinalOddsProvider,
    JRAHistoricalRaceResultResponseProvider as _RaceResultProvider,
)
from scripts.simulation.jra_official_response_capture import (
    JRAOfficialTargetRaceCardResponseCapture as _TargetCapture,
)
from scripts.simulation.jra_race_historical_replay import (
    JRARaceHistoricalReplayResult as _ReplayResult,
    JRARaceHistoricalReplayUnavailableError as _ReplayUnavailable,
    JRARaceHistoricalReplayUnsupportedError as _ReplayUnsupported,
    JRARaceHistoricalReplayValidationError as _ReplayValidation,
    build_jra_race_historical_replay as _build_replay,
)
from scripts.simulation.jra_race_replay_seed import (
    JRARaceReplaySeed as _Seed,
    is_jra_race_replay_seed_id as _is_seed_id,
)
from scripts.simulation.jra_target_horse_history_resolution import (
    JRATargetHorseHistoryResponseProvider as _HorseHistoryProvider,
)
from scripts.simulation.jra_target_race_card_resolution import (
    JRATargetRaceSelectionCaptureProvider as _SelectionProvider,
)


class JRARaceHistoricalSnapshotPersistenceError(ValueError):
    """Base error for exact JRA historical snapshot persistence."""


class JRARaceHistoricalSnapshotPersistenceValidationError(
    JRARaceHistoricalSnapshotPersistenceError
):
    """Raised when caller input or returned domain state is invalid."""


class JRARaceHistoricalSnapshotPersistenceUnavailableError(
    JRARaceHistoricalSnapshotPersistenceError
):
    """Raised when an exact seed or persisted snapshot is unavailable."""


class JRARaceHistoricalSnapshotPersistenceUnsupportedError(
    JRARaceHistoricalSnapshotPersistenceError
):
    """Raised when replay evidence is outside the supported envelope."""


class _JRARaceReplaySeedByIdProvider(_Protocol):
    def __call__(
        self,
        *,
        seed_id: str,
    ) -> _Seed | None: ...


class _HistoricalInputSnapshotPersistence(_Protocol):
    def save_snapshot(
        self,
        *,
        snapshot: _Snapshot,
    ) -> None: ...

    def load_snapshot_by_identity(
        self,
        *,
        identity: _SnapshotIdentity,
    ) -> _Snapshot | None: ...


class _JRATargetRaceCardCaptureByIdProvider(_Protocol):
    def __call__(
        self,
        *,
        capture_id: str,
    ) -> _TargetCapture | None: ...


def _validation(message: str) -> JRARaceHistoricalSnapshotPersistenceValidationError:
    return JRARaceHistoricalSnapshotPersistenceValidationError(message)


_SHA256 = _re.compile(r"[0-9a-f]{64}\Z")


@_dataclass(frozen=True, slots=True)
class JRAPersistedHistoricalSnapshotReference:
    """Compact immutable reference to one exact persisted replay snapshot."""

    seed_id: str
    snapshot_identity: _SnapshotIdentity
    content_sha256: str

    def __post_init__(self) -> None:
        if not _is_seed_id(self.seed_id):
            raise _validation("seed_id must be a canonical JRA replay seed ID")
        if type(self.snapshot_identity) is not _SnapshotIdentity:
            raise _validation("snapshot_identity must be exact HistoricalInputSnapshotIdentity")
        if type(self.content_sha256) is not str or _SHA256.fullmatch(self.content_sha256) is None:
            raise _validation("content_sha256 must be lowercase SHA-256")


def persist_jra_race_historical_snapshot(
    *,
    seed_id: str,
    seed_provider: _JRARaceReplaySeedByIdProvider,
    target_race_selection_capture_provider: _SelectionProvider,
    target_race_card_capture_by_id_provider: _JRATargetRaceCardCaptureByIdProvider,
    horse_history_response_provider: _HorseHistoryProvider,
    race_result_response_provider: _RaceResultProvider,
    final_win_odds_response_provider: _FinalOddsProvider,
    snapshot_persistence: _HistoricalInputSnapshotPersistence,
) -> JRAPersistedHistoricalSnapshotReference:
    """Build, save, and exact-reload one seed-bound historical snapshot."""

    providers = (
        seed_provider,
        target_race_selection_capture_provider,
        target_race_card_capture_by_id_provider,
        horse_history_response_provider,
        race_result_response_provider,
        final_win_odds_response_provider,
    )
    if not _is_seed_id(seed_id):
        raise _validation("seed_id must be a canonical JRA replay seed ID")
    if any(not callable(provider) for provider in providers):
        raise _validation("all seed and replay providers must be callable")
    try:
        save_snapshot = snapshot_persistence.save_snapshot
        load_snapshot_by_identity = snapshot_persistence.load_snapshot_by_identity
    except AttributeError as error:
        raise _validation("snapshot_persistence must expose exact save and load methods") from error
    if not callable(save_snapshot) or not callable(load_snapshot_by_identity):
        raise _validation("snapshot_persistence must expose callable save and load methods")

    loaded_seed = seed_provider(seed_id=seed_id)
    if loaded_seed is None:
        raise JRARaceHistoricalSnapshotPersistenceUnavailableError(
            "exact JRA replay seed is unavailable"
        )
    if type(loaded_seed) is not _Seed or loaded_seed.seed_id != seed_id:
        raise _validation("loaded replay seed is invalid or contradicts seed_id")

    try:
        result = _build_replay(
            seed=loaded_seed,
            target_race_selection_capture_provider=target_race_selection_capture_provider,
            target_race_card_capture_by_id_provider=target_race_card_capture_by_id_provider,
            horse_history_response_provider=horse_history_response_provider,
            race_result_response_provider=race_result_response_provider,
            final_win_odds_response_provider=final_win_odds_response_provider,
        )
    except _ReplayValidation as error:
        raise _validation("JRA historical replay is invalid") from error
    except _ReplayUnavailable as error:
        raise JRARaceHistoricalSnapshotPersistenceUnavailableError(
            "JRA historical replay evidence is unavailable"
        ) from error
    except _ReplayUnsupported as error:
        raise JRARaceHistoricalSnapshotPersistenceUnsupportedError(
            "JRA historical replay evidence is unsupported"
        ) from error

    if type(result) is not _ReplayResult:
        raise _validation("historical replay result must be exact JRARaceHistoricalReplayResult")
    if result.seed is not loaded_seed or type(result.snapshot) is not _Snapshot:
        raise _validation("historical replay result does not retain the exact seed and snapshot")

    replay_snapshot = result.snapshot
    save_snapshot(snapshot=replay_snapshot)
    reloaded = load_snapshot_by_identity(identity=replay_snapshot.identity)
    if reloaded is None:
        raise JRARaceHistoricalSnapshotPersistenceUnavailableError(
            "exact persisted historical snapshot is unavailable"
        )
    if type(reloaded) is not _Snapshot:
        raise _validation("exact persisted snapshot loader returned an invalid object")

    expected_identity = replay_snapshot.identity
    actual_identity = reloaded.identity
    expected_source = expected_identity.source_identity
    actual_source = actual_identity.source_identity
    if (
        actual_identity.dataset_id != expected_identity.dataset_id
        or actual_source.organization != expected_source.organization
        or actual_source.source_system != expected_source.source_system
        or actual_source.external_race_id != expected_source.external_race_id
        or actual_identity.captured_at != expected_identity.captured_at
        or actual_source.source_url != expected_source.source_url
        or reloaded.content_sha256 != replay_snapshot.content_sha256
    ):
        raise _validation("exact persisted snapshot content contradicts replay snapshot")

    return JRAPersistedHistoricalSnapshotReference(
        seed_id=loaded_seed.seed_id,
        snapshot_identity=reloaded.identity,
        content_sha256=reloaded.content_sha256,
    )


__all__ = (
    "JRARaceHistoricalSnapshotPersistenceError",
    "JRARaceHistoricalSnapshotPersistenceValidationError",
    "JRARaceHistoricalSnapshotPersistenceUnavailableError",
    "JRARaceHistoricalSnapshotPersistenceUnsupportedError",
    "JRAPersistedHistoricalSnapshotReference",
    "persist_jra_race_historical_snapshot",
)


if "annotations" in globals():
    del annotations
