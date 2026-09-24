"""Passive timing composition. Official attempt publication precedes measured work."""

from __future__ import annotations

from contextlib import nullcontext
from hashlib import sha256
import sqlite3
from typing import Callable, TypeVar

import requests

from scripts.simulation.nar_operational_timing_attempt_v2 import (
    NARExpectedRequestEnvironmentPolicy, NAROperationalTimingAttemptV2,
    NAROperationalTimingTerminalV2, NARTimingFailureClassificationV2,
    NARTimingPublicationOverheadV2, NARTimingTerminalDispositionV2,
    elapsed_microseconds_from_ns,
)
from scripts.simulation.nar_operational_timing_guarded_session import (
    NARHTTPAttemptContext, NARRequestEnvironmentRejected,
)
from scripts.simulation.nar_operational_timing_observability import (
    NARTimingCorrelation, NARTimingLoadContext, NARHTTPTransportKind, _utc,
)
from scripts.simulation.nar_operational_timing_observability_v2 import (
    NAROperationalTimingStageV2, _REQUIRED_TRANSPORT,
)


T = TypeVar("T")


def _causal_chain(error: BaseException):
    seen: set[int] = set()
    current: BaseException | None = error
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        yield current
        current = current.__cause__


def classify_timing_failure(error: BaseException) -> tuple[NARTimingTerminalDispositionV2, NARTimingFailureClassificationV2]:
    """Use exact types and explicit causes; never parse error text or implicit context."""
    chain = tuple(_causal_chain(error))
    if any(isinstance(x, requests.exceptions.ConnectTimeout) for x in chain):
        return NARTimingTerminalDispositionV2.TIMEOUT, NARTimingFailureClassificationV2.CONNECT_TIMEOUT
    if any(isinstance(x, requests.exceptions.ReadTimeout) for x in chain):
        return NARTimingTerminalDispositionV2.TIMEOUT, NARTimingFailureClassificationV2.READ_TIMEOUT
    if any(isinstance(x, (NARRequestEnvironmentRejected, NotImplementedError)) for x in chain):
        return NARTimingTerminalDispositionV2.UNSUPPORTED, NARTimingFailureClassificationV2.UNSUPPORTED
    if any(isinstance(x, requests.RequestException) for x in chain):
        return NARTimingTerminalDispositionV2.FAILURE, NARTimingFailureClassificationV2.TRANSPORT
    from scripts.simulation.nar_historical_daily_target_bootstrap_live_capture import NARMonthlyConveneInfoBootstrapTransportError
    from scripts.simulation.nar_historical_daily_target_live_capture import NARHistoricalDailyTargetCaptureTransportError
    from scripts.simulation.nar_official_response_live_capture import NAROfficialResponseCaptureTransportError
    from scripts.simulation.nar_market_odds_raw_acquisition import (
        NARMarketOddsRawAcquisitionTransportError, NARMarketOddsRawAcquisitionValidationError,
        NARMarketOddsRawAcquisitionUnsupportedError,
    )
    if any(isinstance(x, (NARMonthlyConveneInfoBootstrapTransportError,
                          NARHistoricalDailyTargetCaptureTransportError,
                          NAROfficialResponseCaptureTransportError,
                          NARMarketOddsRawAcquisitionTransportError)) for x in chain):
        return NARTimingTerminalDispositionV2.FAILURE, NARTimingFailureClassificationV2.TRANSPORT
    if any(isinstance(x, NARMarketOddsRawAcquisitionUnsupportedError) for x in chain):
        return NARTimingTerminalDispositionV2.UNSUPPORTED, NARTimingFailureClassificationV2.UNSUPPORTED
    if any(isinstance(x, (NARMarketOddsRawAcquisitionValidationError, ValueError, TypeError)) for x in chain):
        return NARTimingTerminalDispositionV2.FAILURE, NARTimingFailureClassificationV2.VALIDATION
    if any(isinstance(x, sqlite3.Error) for x in chain):
        return NARTimingTerminalDispositionV2.FAILURE, NARTimingFailureClassificationV2.PERSISTENCE
    return NARTimingTerminalDispositionV2.FAILURE, NARTimingFailureClassificationV2.INTERNAL


def measure_nar_operation(
    *, runner: object, capability: object, stage: NAROperationalTimingStageV2,
    correlation: NARTimingCorrelation, load_context: NARTimingLoadContext,
    operation: Callable[[], T], expected_url: str | None = None,
    transport_kind: NARHTTPTransportKind | None = None,
    artifact_sha256: str | None = None,
) -> T:
    """Return/rethrow the underlying operation unchanged after best-effort terminal write.

    Attempt start and exact reload are mandatory; failure there prevents invocation.
    This primitive does not choose a provider operation or mutate its arguments.
    """
    capability.require_current_owner(runner)
    archive = runner.attempt_archive
    session = archive.runtime.v2.load_session(session_identity=capability.session_identity)
    claim = archive.runtime.load_claim_for_session(session_identity=capability.session_identity)
    if (session is None or claim is None or claim.claim_identity != capability.claim_identity
            or claim.binding_identity != capability.binding_identity or stage not in session.configuration.enabled_stages):
        raise RuntimeError("official timing wrapper lacks exact current execution ancestry")
    if type(stage) is not NAROperationalTimingStageV2 or type(correlation) is not NARTimingCorrelation or type(load_context) is not NARTimingLoadContext:
        raise ValueError("closed V2 timing context required")
    is_http = stage in _REQUIRED_TRANSPORT
    if is_http != (expected_url is not None and transport_kind is not None):
        raise ValueError("HTTP stage requires exact request URL and kind; non-HTTP does not")
    if is_http and _REQUIRED_TRANSPORT[stage] is not transport_kind:
        raise ValueError("stage/transport kind contradiction")
    if is_http:
        from scripts.simulation.nar_operational_timing_guarded_session import _require_safe_url
        _require_safe_url(expected_url)
    sequence = runner.next_attempt_sequence(capability)
    admitted_at = _utc(runner.utc_clock())
    if not session.admits(admitted_at):
        raise RuntimeError("attempt is outside fixed half-open measurement window")
    attempt = NAROperationalTimingAttemptV2(
        session.configuration.configuration_identity, session.session_identity, claim.claim_identity,
        stage, correlation, sequence, admitted_at, load_context,
        NARExpectedRequestEnvironmentPolicy.DIRECT_REQUEST_ENVIRONMENT_V1 if is_http else None,
        sha256(expected_url.encode("utf-8")).hexdigest() if is_http else None,
    )
    publication_start_ns = runner.monotonic_timer_ns()
    archive.save_attempt(attempt=attempt)
    if archive.load_attempt(attempt_identity=attempt.attempt_identity) != attempt:
        raise RuntimeError("attempt publication did not exact-reload; operation not invoked")
    publication_finish_ns = runner.monotonic_timer_ns()
    overhead = NARTimingPublicationOverheadV2(
        claim.claim_identity, attempt.attempt_identity, NAROperationalTimingStageV2.ATTEMPT_START_PUBLICATION,
        elapsed_microseconds_from_ns(publication_start_ns, publication_finish_ns),
    )
    archive.save_overhead(overhead=overhead)
    context = (NARHTTPAttemptContext(runner=runner, capability=capability, attempt=attempt,
                                     expected_url=expected_url, transport_kind=transport_kind)
               if is_http else nullcontext())
    start_ns = runner.monotonic_timer_ns()

    def publish(disposition: NARTimingTerminalDispositionV2,
                failure: NARTimingFailureClassificationV2 | None) -> None:
        finish_ns = runner.monotonic_timer_ns()
        finished_at = _utc(runner.utc_clock())
        terminal = NAROperationalTimingTerminalV2(attempt.attempt_identity, finished_at,
                                                  elapsed_microseconds_from_ns(start_ns, finish_ns),
                                                  disposition, failure, artifact_sha256 if failure is None else None)
        terminal_start_ns = runner.monotonic_timer_ns()
        archive.save_terminal(terminal=terminal)
        if archive.load_terminal_for_attempt(attempt_identity=attempt.attempt_identity) != terminal:
            raise RuntimeError("terminal publication did not exact-reload")
        terminal_end_ns = runner.monotonic_timer_ns()
        archive.save_overhead(overhead=NARTimingPublicationOverheadV2(
            claim.claim_identity, attempt.attempt_identity, NAROperationalTimingStageV2.TERMINAL_PUBLICATION,
            elapsed_microseconds_from_ns(terminal_start_ns, terminal_end_ns),
        ))

    try:
        with context:
            result = operation()
    except BaseException as error:
        try:
            disposition, failure = classify_timing_failure(error)
        except Exception:
            disposition, failure = NARTimingTerminalDispositionV2.FAILURE, NARTimingFailureClassificationV2.INTERNAL
        try:
            publish(disposition, failure)
        except Exception:
            pass  # Durable attempt remains unresolved; original production exception wins.
        raise
    try:
        publish(NARTimingTerminalDispositionV2.SUCCESS, None)
    except Exception:
        pass  # Preserve the underlying successful value; reconciliation detects unresolved evidence.
    return result
