"""Thin live acquisition application for one complete NAR historical target day."""

from __future__ import annotations

from collections.abc import Callable as _Callable
from dataclasses import dataclass as _dataclass
from datetime import date as _date, datetime as _datetime
from typing import Protocol as _Protocol

from scripts.simulation.historical_daily_targets import (
    DailyHistoricalReplayTargetSet as _DailyHistoricalReplayTargetSet,
)
from scripts.simulation.nar_historical_daily_target_bootstrap import (
    NARMonthlyConveneInfoBootstrapEvidence as _BootstrapEvidence,
    resolve_nar_monthly_convene_info_locator_script as _resolve_script,
    resolve_nar_monthly_convene_info_request_identity as _resolve_monthly_request,
    resolve_nar_monthly_convene_info_root_locator as _resolve_root,
)
from scripts.simulation.nar_historical_daily_target_bootstrap_capture import (
    NARMonthlyConveneInfoBootstrapSupplierCapture as _SupplierCapture,
)
from scripts.simulation.nar_historical_daily_target_bootstrap_live_capture import (
    NARMonthlyConveneInfoBootstrapHTTPTransport as _SupplierTransport,
    NARMonthlyConveneInfoBootstrapLiveCaptureService as _SupplierService,
)
from scripts.simulation.nar_historical_daily_target_capture import (
    NARHistoricalDailyTargetResponseCapture as _DailyTargetCapture,
)
from scripts.simulation.nar_historical_daily_target_live_capture import (
    NARHistoricalDailyTargetHTTPTransport as _DailyTargetTransport,
    NARHistoricalDailyTargetLiveCaptureService as _DailyTargetService,
)
from scripts.simulation.nar_historical_daily_target_source import (
    NARHistoricalDailyTargetSourceValidationError as _SourceValidationError,
    build_nar_historical_daily_replay_target_set as _build_target_set,
    normalize_nar_monthly_convene_info as _normalize_monthly,
)


def _required_text(value: object, name: str) -> str:
    if type(value) is not str or not value:
        raise _SourceValidationError(f"{name} must be non-empty exact str")
    return value


class _NARDailyTargetLiveAcquisitionArchive(_Protocol):
    def save_supplier_capture(self, *, capture: _SupplierCapture) -> None: ...

    def save_capture(self, *, capture: _DailyTargetCapture) -> None: ...


@_dataclass(frozen=True, slots=True)
class NARDailyTargetLiveAcquisitionResult:
    target_date: _date
    homepage_supplier_capture_id: str
    monthly_root_supplier_capture_id: str
    locator_script_supplier_capture_id: str
    supplier_evidence_identity: str
    monthly_capture_id: str
    race_list_capture_ids: tuple[str, ...]
    target_set: _DailyHistoricalReplayTargetSet

    def __post_init__(self) -> None:
        if type(self.target_date) is not _date:
            raise _SourceValidationError("target_date must be exact date")
        supplier_ids = (
            _required_text(
                self.homepage_supplier_capture_id,
                "homepage_supplier_capture_id",
            ),
            _required_text(
                self.monthly_root_supplier_capture_id,
                "monthly_root_supplier_capture_id",
            ),
            _required_text(
                self.locator_script_supplier_capture_id,
                "locator_script_supplier_capture_id",
            ),
        )
        if len(set(supplier_ids)) != len(supplier_ids):
            raise _SourceValidationError("supplier capture IDs must be unique")
        _required_text(self.supplier_evidence_identity, "supplier_evidence_identity")
        _required_text(self.monthly_capture_id, "monthly_capture_id")
        if type(self.race_list_capture_ids) is not tuple or not self.race_list_capture_ids:
            raise _SourceValidationError(
                "race_list_capture_ids must be a non-empty exact tuple"
            )
        race_list_ids = tuple(
            _required_text(value, "race_list_capture_ids item")
            for value in self.race_list_capture_ids
        )
        if len(set(race_list_ids)) != len(race_list_ids):
            raise _SourceValidationError("race_list_capture_ids must be unique")
        if type(self.target_set) is not _DailyHistoricalReplayTargetSet:
            raise _SourceValidationError(
                "target_set must be DailyHistoricalReplayTargetSet"
            )
        if self.target_set.target_date != self.target_date:
            raise _SourceValidationError(
                "target_set target_date differs from acquisition target_date"
            )


class NARDailyTargetLiveAcquisitionApplication:
    """Compose existing strict capture and normalization boundaries for one NAR day."""

    __slots__ = ("_daily_target_service", "_supplier_service")

    def __init__(
        self,
        *,
        archive: _NARDailyTargetLiveAcquisitionArchive,
        supplier_transport: _SupplierTransport,
        daily_target_transport: _DailyTargetTransport,
        utc_clock: _Callable[[], _datetime],
    ) -> None:
        self._supplier_service = _SupplierService(
            archive=archive,
            transport=supplier_transport,
            utc_clock=utc_clock,
        )
        self._daily_target_service = _DailyTargetService(
            archive=archive,
            transport=daily_target_transport,
            utc_clock=utc_clock,
        )

    def acquire(self, *, target_date: _date) -> NARDailyTargetLiveAcquisitionResult:
        if type(target_date) is not _date:
            raise _SourceValidationError("target_date must be exact date")

        homepage_capture = self._supplier_service.capture_official_home()
        root_locator = _resolve_root(homepage_capture=homepage_capture)
        monthly_root_capture = self._supplier_service.capture_monthly_root(
            homepage_capture=homepage_capture,
            root_locator=root_locator,
        )
        script_resolution = _resolve_script(
            target_date=target_date,
            root_locator=root_locator,
            monthly_root_capture=monthly_root_capture,
        )
        locator_script_capture = self._supplier_service.capture_locator_script(
            monthly_root_capture=monthly_root_capture,
            locator_script_resolution=script_resolution,
        )
        supplier_evidence = _BootstrapEvidence(
            homepage_capture=homepage_capture,
            monthly_root_capture=monthly_root_capture,
            locator_script_capture=locator_script_capture,
        )
        monthly_request = _resolve_monthly_request(
            target_date=target_date,
            supplier_evidence=supplier_evidence,
        )
        monthly_capture = self._daily_target_service.capture_supplied_response(
            request_identity=monthly_request
        )
        envelope = _normalize_monthly(
            target_date=target_date,
            capture=monthly_capture,
        )
        race_list_captures = tuple(
            self._daily_target_service.capture_supplied_response(
                request_identity=locator.request_identity
            )
            for locator in envelope.venue_locators
        )
        target_set = _build_target_set(
            target_date=target_date,
            envelope_capture=monthly_capture,
            race_list_captures=race_list_captures,
        )
        return NARDailyTargetLiveAcquisitionResult(
            target_date=target_date,
            homepage_supplier_capture_id=homepage_capture.capture_id,
            monthly_root_supplier_capture_id=monthly_root_capture.capture_id,
            locator_script_supplier_capture_id=locator_script_capture.capture_id,
            supplier_evidence_identity=supplier_evidence.supplier_evidence_identity,
            monthly_capture_id=monthly_capture.capture_id,
            race_list_capture_ids=tuple(
                capture.capture_id for capture in race_list_captures
            ),
            target_set=target_set,
        )


if "annotations" in globals():
    del annotations
