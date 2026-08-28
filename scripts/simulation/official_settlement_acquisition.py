"""Compose exact archived official settlement facts for one persisted simulation plan.

This module owns only the application boundary between a historical input snapshot,
its already-persisted immutable bet plan, and provider-specific official settlement
normalizers.  It deliberately does not acquire HTTP responses, discover captures,
read latest repository values, or calculate settlement.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

from scripts.simulation.historical_input_snapshot_simulation_adapter import (
    build_simulation_race_input_from_historical_snapshot,
)
from scripts.simulation.historical_input_snapshots import HistoricalInputSnapshot
from scripts.simulation.bet_plan_snapshot_repository import SimulationBetPlanSnapshotSource
from scripts.simulation.jra_official_response_capture import (
    JRAOfficialPageKind,
    JRAOfficialResponseCapture,
    JRAOfficialResponseCaptureArchive,
)
from scripts.simulation.jra_target_race_payout_persistence import (
    normalize_and_persist_jra_target_race_payout,
)
from scripts.simulation.jra_target_race_result_persistence import (
    normalize_and_persist_jra_target_race_result,
)
from scripts.simulation.models import SimulationRunContext, StrategyIdentity
from scripts.simulation.nar_official_response_capture import (
    NAROfficialPageKind,
    NAROfficialResponseCapture,
    NAROfficialResponseCaptureArchive,
)
from scripts.simulation.nar_target_race_payout_persistence import (
    normalize_and_persist_nar_target_race_payout,
)
from scripts.simulation.nar_target_race_result_persistence import (
    normalize_and_persist_nar_target_race_result,
)
from scripts.simulation.persisted_settlement import PersistedRaceSettlementData
from scripts.simulation.persisted_simulation_bet_source import PersistedSimulationBetSource
from scripts.simulation.repositories.interfaces import (
    BET_TYPES,
    PayoutPublication,
    PayoutRepository,
    PersistedRaceResult,
    RaceResultRepository,
)

__all__ = (
    "OfficialSettlementAcquisitionError",
    "OfficialSettlementAcquisitionValidationError",
    "OfficialSettlementAcquisitionUnavailableError",
    "OfficialSettlementAcquisitionUnsupportedError",
    "acquire_and_persist_official_settlement_facts",
)


class OfficialSettlementAcquisitionError(ValueError):
    """Base error for exact-capture official settlement acquisition."""


class OfficialSettlementAcquisitionValidationError(OfficialSettlementAcquisitionError):
    """Raised when caller input, identity, capture, or cutoff data disagrees."""


class OfficialSettlementAcquisitionUnavailableError(OfficialSettlementAcquisitionError):
    """Raised when required exact official evidence is unavailable."""


class OfficialSettlementAcquisitionUnsupportedError(OfficialSettlementAcquisitionError):
    """Raised for a provider outside the approved exact-capture boundary."""


class _ExactCaptureCache:
    """Read-only exact-ID archive view for already-preloaded captures."""

    __slots__ = ("_captures",)

    def __init__(self, captures: Mapping[str, object]) -> None:
        self._captures = dict(captures)

    def load_capture(self, *, capture_id: str) -> object | None:
        return self._captures.get(capture_id)


def _validation(message: str) -> OfficialSettlementAcquisitionValidationError:
    return OfficialSettlementAcquisitionValidationError(message)


def _unavailable(message: str) -> OfficialSettlementAcquisitionUnavailableError:
    return OfficialSettlementAcquisitionUnavailableError(message)


def _is_aware(value: object) -> bool:
    return isinstance(value, datetime) and value.tzinfo is not None and value.utcoffset() is not None


def _exact_non_empty_string(value: object, name: str) -> str:
    if type(value) is not str or not value:
        raise _validation(f"{name} must be a non-empty exact str")
    return value


def _validate_public_arguments(
    *,
    snapshot: object,
    run_context: object,
    strategy_identity: object,
    settlement_information_cutoff: object,
    bet_plan_snapshot_source: SimulationBetPlanSnapshotSource,
    result_capture_id: object,
    payout_capture_ids_by_bet_type: object,
    capture_archive: object,
    race_result_repository: object,
    payout_repository: object,
) -> dict[str, str]:
    if type(snapshot) is not HistoricalInputSnapshot:
        raise _validation("snapshot must be exact HistoricalInputSnapshot")
    if type(run_context) is not SimulationRunContext:
        raise _validation("run_context must be exact SimulationRunContext")
    if type(strategy_identity) is not StrategyIdentity:
        raise _validation("strategy_identity must be exact StrategyIdentity")
    if not _is_aware(settlement_information_cutoff):
        raise _validation("settlement_information_cutoff must be timezone-aware datetime")
    if isinstance(bet_plan_snapshot_source, type) or not callable(
        getattr(bet_plan_snapshot_source, "load_snapshot", None)
    ):
        raise _validation("bet_plan_snapshot_source must provide callable load_snapshot")
    _exact_non_empty_string(result_capture_id, "result_capture_id")
    if not isinstance(payout_capture_ids_by_bet_type, Mapping):
        raise _validation("payout_capture_ids_by_bet_type must be a Mapping")
    payout_capture_ids = dict(payout_capture_ids_by_bet_type)
    for bet_type, capture_id in payout_capture_ids.items():
        if type(bet_type) is not str or bet_type not in BET_TYPES:
            raise _validation("payout_capture_ids_by_bet_type keys must be supported exact bet types")
        _exact_non_empty_string(capture_id, "payout capture_id")
    if isinstance(capture_archive, type) or not callable(getattr(capture_archive, "load_capture", None)):
        raise _validation("capture_archive must provide callable load_capture")
    if isinstance(race_result_repository, type) or not callable(
        getattr(race_result_repository, "save_race_result", None)
    ):
        raise _validation("race_result_repository must provide callable save_race_result")
    if isinstance(payout_repository, type) or not callable(
        getattr(payout_repository, "save_payout_publication", None)
    ):
        raise _validation("payout_repository must provide callable save_payout_publication")
    return payout_capture_ids


def _required_bet_types(bets: tuple[object, ...]) -> tuple[str, ...]:
    required: list[str] = []
    for bet in bets:
        bet_type = bet.bet_type  # PersistedSimulationBetSource already validates the tuple.
        if bet_type not in required:
            required.append(bet_type)
    return tuple(required)


def _provider_normalizers(snapshot: HistoricalInputSnapshot) -> tuple[object, object, type[object], object]:
    source = snapshot.identity.source_identity
    if source.organization == "JRA" and source.source_system == "jra_official":
        return (
            normalize_and_persist_jra_target_race_result,
            normalize_and_persist_jra_target_race_payout,
            JRAOfficialResponseCapture,
            JRAOfficialPageKind.RACE_RESULT,
        )
    if source.organization == "NAR" and source.source_system == "nar_official":
        return (
            normalize_and_persist_nar_target_race_result,
            normalize_and_persist_nar_target_race_payout,
            NAROfficialResponseCapture,
            NAROfficialPageKind.RACE_MARK_TABLE,
        )
    raise OfficialSettlementAcquisitionUnsupportedError(
        "snapshot source provider is unsupported for official settlement acquisition"
    )


def _capture_ids(result_capture_id: str, required_bet_types: tuple[str, ...], payout_capture_ids: Mapping[str, str]) -> tuple[str, ...]:
    ordered: list[str] = []
    for capture_id in (result_capture_id, *(payout_capture_ids[bet_type] for bet_type in required_bet_types)):
        if capture_id not in ordered:
            ordered.append(capture_id)
    return tuple(ordered)


def _preload_captures(
    *,
    capture_ids: tuple[str, ...],
    capture_archive: object,
    expected_capture_type: type[object],
    expected_page_kind: object,
    settlement_information_cutoff: datetime,
) -> _ExactCaptureCache:
    captures: dict[str, object] = {}
    loader = capture_archive.load_capture
    for capture_id in capture_ids:
        capture = loader(capture_id=capture_id)
        if capture is None:
            raise _unavailable("required exact official capture is unavailable")
        if type(capture) is not expected_capture_type:
            raise _validation("capture archive returned an incompatible capture type")
        if capture.capture_id != capture_id:
            raise _validation("capture archive returned a different exact capture")
        if capture.page_kind is not expected_page_kind:
            raise _validation("capture page_kind is incompatible")
        if not _is_aware(capture.observed_at):
            raise _validation("capture observed_at must be timezone-aware")
        if capture.observed_at > settlement_information_cutoff:
            raise _validation("capture observed_at is after settlement_information_cutoff")
        captures[capture_id] = capture
    return _ExactCaptureCache(captures)


def acquire_and_persist_official_settlement_facts(
    *,
    snapshot: HistoricalInputSnapshot,
    run_context: SimulationRunContext,
    strategy_identity: StrategyIdentity,
    settlement_information_cutoff: datetime,
    bet_plan_snapshot_source: object,
    result_capture_id: str,
    payout_capture_ids_by_bet_type: Mapping[str, str],
    capture_archive: JRAOfficialResponseCaptureArchive | NAROfficialResponseCaptureArchive,
    race_result_repository: RaceResultRepository,
    payout_repository: PayoutRepository,
) -> PersistedRaceSettlementData:
    """Normalize and persist exact official facts needed by one persisted bet plan."""

    payout_capture_ids = _validate_public_arguments(
        snapshot=snapshot,
        run_context=run_context,
        strategy_identity=strategy_identity,
        settlement_information_cutoff=settlement_information_cutoff,
        bet_plan_snapshot_source=bet_plan_snapshot_source,
        result_capture_id=result_capture_id,
        payout_capture_ids_by_bet_type=payout_capture_ids_by_bet_type,
        capture_archive=capture_archive,
        race_result_repository=race_result_repository,
        payout_repository=payout_repository,
    )
    if snapshot.identity.dataset_id != run_context.dataset_id:
        raise _validation("snapshot dataset_id must equal run_context dataset_id")

    race_input = build_simulation_race_input_from_historical_snapshot(snapshot=snapshot)
    bet_source = PersistedSimulationBetSource(
        run_context=run_context,
        snapshot_source=bet_plan_snapshot_source,
    )
    bets = bet_source.load_bets(race_input=race_input, strategy_identity=strategy_identity)
    required_bet_types = _required_bet_types(bets)

    result_normalizer, payout_normalizer, expected_capture_type, expected_page_kind = _provider_normalizers(snapshot)
    if set(payout_capture_ids) != set(required_bet_types):
        raise _validation("payout capture IDs must cover exactly the persisted plan bet types")

    cache = _preload_captures(
        capture_ids=_capture_ids(result_capture_id, required_bet_types, payout_capture_ids),
        capture_archive=capture_archive,
        expected_capture_type=expected_capture_type,
        expected_page_kind=expected_page_kind,
        settlement_information_cutoff=settlement_information_cutoff,
    )

    race_result = result_normalizer(
        capture_id=result_capture_id,
        capture_archive=cache,
        snapshot=snapshot,
        race_result_repository=race_result_repository,
    )
    if type(race_result) is not PersistedRaceResult:
        raise _validation("provider result normalizer returned an invalid result")

    payout_publications: dict[str, PayoutPublication] = {}
    for bet_type in required_bet_types:
        publication = payout_normalizer(
            capture_id=payout_capture_ids[bet_type],
            capture_archive=cache,
            snapshot=snapshot,
            bet_type=bet_type,
            payout_repository=payout_repository,
        )
        if type(publication) is not PayoutPublication:
            raise _validation("provider payout normalizer returned an invalid publication")
        payout_publications[bet_type] = publication

    return PersistedRaceSettlementData(
        race_id=snapshot.internal_race_id,
        bets=bets,
        race_result=race_result,
        payout_publications_by_bet_type=payout_publications,
    )
