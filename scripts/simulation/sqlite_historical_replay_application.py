"""SQLite composition root for exact archived historical replay."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
import sqlite3
import sys

from scripts.migrations.runner import apply_migrations
from scripts.simulation.bet_plan_snapshot import SimulationBetPlanSnapshot
from scripts.simulation.final_historical_settlement_simulation import (
    execute_final_historical_settlement_simulation,
)
from scripts.simulation.historical_input_snapshots import HistoricalInputSnapshot
from scripts.simulation.historical_prediction_bet_plan_batch_execution import (
    execute_and_persist_historical_bet_plans,
)
from scripts.simulation.historical_replay_request_document import (
    HistoricalReplayRaceRequest,
    HistoricalReplayRequestDocument,
)
from scripts.simulation.models import SimulationSummary
from scripts.simulation.official_settlement_acquisition import (
    acquire_and_persist_official_settlement_facts,
)
from scripts.simulation.repositories.sqlite import (
    SQLitePayoutRepository,
    SQLiteRaceResultRepository,
)
from scripts.simulation.repositories.sqlite_bet_plan_snapshot_repository import (
    SQLiteSimulationBetPlanSnapshotRepository,
)
from scripts.simulation.repositories.sqlite_historical_input_snapshot_repository import (
    SQLiteHistoricalInputSnapshotRepository,
)
from scripts.simulation.repositories.sqlite_jra_official_response_capture_repository import (
    SQLiteJRAOfficialResponseCaptureRepository,
)
from scripts.simulation.repositories.sqlite_nar_official_response_capture_repository import (
    SQLiteNAROfficialResponseCaptureRepository,
)


__all__ = (
    "SQLiteHistoricalReplayApplicationError",
    "run_sqlite_historical_replay",
)


_JRA_PROVIDER = ("JRA", "jra_official")
_NAR_PROVIDER = ("NAR", "nar_official")
_JRA_ARCHIVE_KEY = "JRA/jra_official"
_NAR_ARCHIVE_KEY = "NAR/nar_official"


class SQLiteHistoricalReplayApplicationError(ValueError):
    """A dynamic C4i2 replay binding or evidence-catalog contradiction."""


def _error(message: str) -> SQLiteHistoricalReplayApplicationError:
    return SQLiteHistoricalReplayApplicationError(message)


def _provider_archive_key(snapshot: HistoricalInputSnapshot) -> str:
    source = snapshot.identity.source_identity
    provider_pair = (source.organization, source.source_system)
    if provider_pair == _JRA_PROVIDER:
        return _JRA_ARCHIVE_KEY
    if provider_pair == _NAR_PROVIDER:
        return _NAR_ARCHIVE_KEY
    raise _error("loaded snapshot provider is unsupported")


def _validate_loaded_snapshot(
    *,
    snapshot: object,
    race_request: HistoricalReplayRaceRequest,
    document: HistoricalReplayRequestDocument,
    loaded_race_ids: set[int],
) -> HistoricalInputSnapshot:
    if type(snapshot) is not HistoricalInputSnapshot:
        raise _error("exact historical snapshot is unavailable or has an invalid type")
    if snapshot.identity != race_request.snapshot_identity:
        raise _error("loaded snapshot identity does not match the request")
    if snapshot.internal_race_id != race_request.internal_race_id:
        raise _error("loaded snapshot internal race ID does not match the request")
    if snapshot.identity.dataset_id != document.run_context.dataset_id:
        raise _error("loaded snapshot dataset_id does not match run_context.dataset_id")
    if snapshot.internal_race_id in loaded_race_ids:
        raise _error("loaded snapshots have duplicate internal race IDs")
    loaded_race_ids.add(snapshot.internal_race_id)
    return snapshot


def _canonical_snapshots(
    *,
    document: HistoricalReplayRequestDocument,
    snapshot_repository: SQLiteHistoricalInputSnapshotRepository,
) -> tuple[tuple[HistoricalInputSnapshot, ...], Mapping[int, HistoricalReplayRaceRequest]]:
    loaded: list[HistoricalInputSnapshot] = []
    loaded_race_ids: set[int] = set()
    requests_by_race_id: dict[int, HistoricalReplayRaceRequest] = {}
    for race_request in document.races:
        snapshot = snapshot_repository.load_snapshot_by_identity(
            identity=race_request.snapshot_identity,
        )
        if snapshot is None:
            raise _error("requested exact historical snapshot is unavailable")
        loaded.append(
            _validate_loaded_snapshot(
                snapshot=snapshot,
                race_request=race_request,
                document=document,
                loaded_race_ids=loaded_race_ids,
            )
        )
        requests_by_race_id[race_request.internal_race_id] = race_request
    canonical = tuple(
        sorted(
            loaded,
            key=lambda snapshot: (
                snapshot.race.scheduled_start_at,
                snapshot.internal_race_id,
            ),
        )
    )
    return canonical, requests_by_race_id


def _validate_returned_plans(
    *,
    returned_plans: object,
    canonical_snapshots: tuple[HistoricalInputSnapshot, ...],
    document: HistoricalReplayRequestDocument,
) -> tuple[SimulationBetPlanSnapshot, ...]:
    if type(returned_plans) is not tuple:
        raise _error("C4g1 must return an exact tuple of plan snapshots")
    if len(returned_plans) != len(canonical_snapshots):
        raise _error("C4g1 plan batch does not exactly cover loaded snapshots")

    seen_race_ids: set[int] = set()
    plans: list[SimulationBetPlanSnapshot] = []
    for plan, snapshot in zip(returned_plans, canonical_snapshots, strict=True):
        if type(plan) is not SimulationBetPlanSnapshot:
            raise _error("C4g1 returned an invalid plan snapshot type")
        identity = plan.identity
        if (
            identity.run_id != document.run_context.run_id
            or identity.race_id != snapshot.internal_race_id
            or identity.strategy_id != document.strategy_identity.strategy_id
            or identity.strategy_config_hash != document.strategy_identity.strategy_config_hash
            or identity.information_cutoff != snapshot.information_cutoff
        ):
            raise _error("C4g1 plan identity does not match its canonical snapshot binding")
        if identity.race_id in seen_race_ids:
            raise _error("C4g1 returned duplicate plan race IDs")
        seen_race_ids.add(identity.race_id)
        plans.append(plan)
    return tuple(plans)


def _required_bet_types(plan: SimulationBetPlanSnapshot) -> tuple[str, ...]:
    required: list[str] = []
    for bet in plan.bets:
        if bet.bet_type not in required:
            required.append(bet.bet_type)
    return tuple(required)


def _payout_capture_subsets(
    *,
    canonical_snapshots: tuple[HistoricalInputSnapshot, ...],
    plans: tuple[SimulationBetPlanSnapshot, ...],
    requests_by_race_id: Mapping[int, HistoricalReplayRaceRequest],
) -> Mapping[int, dict[str, str]]:
    subsets: dict[int, dict[str, str]] = {}
    for snapshot, plan in zip(canonical_snapshots, plans, strict=True):
        race_request = requests_by_race_id[snapshot.internal_race_id]
        subset: dict[str, str] = {}
        for bet_type in _required_bet_types(plan):
            try:
                subset[bet_type] = race_request.payout_capture_catalog_by_bet_type[bet_type]
            except KeyError as error:
                raise _error("required payout capture is absent from the race catalog") from error
        subsets[snapshot.internal_race_id] = subset
    return subsets


def _read_only_archive_uri(archive_path: Path) -> str:
    return archive_path.absolute().as_uri() + "?mode=ro"


def _open_read_only_archive(
    *,
    archive_path: Path,
    owned_connections: list[sqlite3.Connection],
) -> sqlite3.Connection:
    connection = sqlite3.connect(
        _read_only_archive_uri(archive_path),
        uri=True,
    )
    owned_connections.append(connection)
    connection.execute("PRAGMA query_only=ON")
    if connection.execute("PRAGMA query_only").fetchone() != (1,):
        raise _error("archive query_only verification did not report enabled")
    return connection


def _capture_archives_by_provider(
    *,
    canonical_snapshots: tuple[HistoricalInputSnapshot, ...],
    document: HistoricalReplayRequestDocument,
    owned_connections: list[sqlite3.Connection],
) -> Mapping[str, object]:
    represented_provider_keys: list[str] = []
    for snapshot in canonical_snapshots:
        provider_key = _provider_archive_key(snapshot)
        if provider_key not in represented_provider_keys:
            represented_provider_keys.append(provider_key)

    archives: dict[str, object] = {}
    for provider_key in represented_provider_keys:
        try:
            archive_path = document.capture_archive_paths_by_provider[provider_key]
        except KeyError as error:
            raise _error("loaded snapshot provider has no configured capture archive") from error
        connection = _open_read_only_archive(
            archive_path=archive_path,
            owned_connections=owned_connections,
        )
        if provider_key == _JRA_ARCHIVE_KEY:
            archives[provider_key] = SQLiteJRAOfficialResponseCaptureRepository(
                connection=connection,
            )
        elif provider_key == _NAR_ARCHIVE_KEY:
            archives[provider_key] = SQLiteNAROfficialResponseCaptureRepository(
                connection=connection,
            )
        else:
            raise _error("loaded snapshot provider is unsupported")
    return archives


def _close_owned_connections(owned_connections: list[sqlite3.Connection]) -> None:
    primary_error = sys.exc_info()[1]
    first_close_error: BaseException | None = None
    for connection in reversed(owned_connections):
        try:
            connection.close()
        except BaseException as error:
            if primary_error is None and first_close_error is None:
                first_close_error = error
    if primary_error is None and first_close_error is not None:
        raise first_close_error


def run_sqlite_historical_replay(
    *,
    document: HistoricalReplayRequestDocument,
) -> SimulationSummary:
    """Run one exact C4i1 document through C4g1, C4h4a, then C4h4b."""

    if type(document) is not HistoricalReplayRequestDocument:
        raise _error("document must be an exact HistoricalReplayRequestDocument")

    owned_connections: list[sqlite3.Connection] = []
    main_connection = sqlite3.connect(document.database_path)
    owned_connections.append(main_connection)
    try:
        apply_migrations(main_connection)
        snapshot_repository = SQLiteHistoricalInputSnapshotRepository(
            connection=main_connection,
        )
        plan_repository = SQLiteSimulationBetPlanSnapshotRepository(
            connection=main_connection,
        )
        canonical_snapshots, requests_by_race_id = _canonical_snapshots(
            document=document,
            snapshot_repository=snapshot_repository,
        )

        returned_plans = execute_and_persist_historical_bet_plans(
            snapshots=canonical_snapshots,
            run_context=document.run_context,
            strategy_identity=document.strategy_identity,
            budgets_by_race_id=document.budgets_by_race_id,
            snapshot_repository=plan_repository,
        )
        plans = _validate_returned_plans(
            returned_plans=returned_plans,
            canonical_snapshots=canonical_snapshots,
            document=document,
        )
        payout_subsets_by_race_id = _payout_capture_subsets(
            canonical_snapshots=canonical_snapshots,
            plans=plans,
            requests_by_race_id=requests_by_race_id,
        )

        result_repository = SQLiteRaceResultRepository(main_connection)
        payout_repository = SQLitePayoutRepository(main_connection)
        capture_archives = _capture_archives_by_provider(
            canonical_snapshots=canonical_snapshots,
            document=document,
            owned_connections=owned_connections,
        )

        settlement_cutoffs_by_race_id: dict[int, datetime] = {}
        for snapshot in canonical_snapshots:
            race_request = requests_by_race_id[snapshot.internal_race_id]
            provider_key = _provider_archive_key(snapshot)
            settlement_cutoff = race_request.settlement_information_cutoff
            settlement_cutoffs_by_race_id[snapshot.internal_race_id] = settlement_cutoff
            acquire_and_persist_official_settlement_facts(
                snapshot=snapshot,
                run_context=document.run_context,
                strategy_identity=document.strategy_identity,
                settlement_information_cutoff=settlement_cutoff,
                bet_plan_snapshot_source=plan_repository,
                result_capture_id=race_request.result_capture_id,
                payout_capture_ids_by_bet_type=payout_subsets_by_race_id[
                    snapshot.internal_race_id
                ],
                capture_archive=capture_archives[provider_key],
                race_result_repository=result_repository,
                payout_repository=payout_repository,
            )
        return execute_final_historical_settlement_simulation(
            snapshots=canonical_snapshots,
            run_context=document.run_context,
            strategy_identity=document.strategy_identity,
            settlement_cutoffs_by_race_id=settlement_cutoffs_by_race_id,
            bet_plan_snapshot_source=plan_repository,
            race_result_repository=result_repository,
            payout_repository=payout_repository,
        )
    finally:
        _close_owned_connections(owned_connections)
