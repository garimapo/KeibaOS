"""Trusted live HTTPS acquisition for one official JRA parser-input response."""

from __future__ import annotations

from collections.abc import Callable as _Callable
from dataclasses import dataclass as _dataclass
from datetime import datetime as _datetime, timezone as _timezone
import re as _re
from typing import Protocol as _Protocol

import requests as _requests
from requests.adapters import HTTPAdapter as _HTTPAdapter
from urllib3.exceptions import HTTPError as _HTTPError

from scripts.simulation.jra_official_response_capture import (
    JRAFinalWinOddsResponseCapture as _JRAFinalWinOddsResponseCapture,
    JRAFinalWinOddsSuppliedOfficialResponse as _JRAFinalWinOddsSuppliedOfficialResponse,
    JRAOfficialPageKind as _JRAOfficialPageKind,
    JRAOfficialResponseCapture as _JRAOfficialResponseCapture,
    JRAOfficialResponseCaptureArchive as _JRAOfficialResponseCaptureArchive,
    JRAOfficialResponseCaptureError as _JRAOfficialResponseCaptureError,
    JRAOfficialResponseCaptureUnsupportedError as _JRAOfficialResponseCaptureUnsupportedError,
    JRAOfficialResponseCaptureValidationError as _JRAOfficialResponseCaptureValidationError,
    JRAOfficialTargetRaceCardResponseCapture as _JRAOfficialTargetRaceCardResponseCapture,
    JRATargetRaceSelectionResponseCapture as _JRATargetRaceSelectionResponseCapture,
    _content_type as _capture_content_type,
    _canonical_target_race_card_url as _canonical_target_race_card_url,
    canonicalize_jra_official_capture_url as _canonicalize_jra_official_capture_url,
)
from scripts.simulation.jra_official_identity import (
    JRAOfficialFinalWinOddsRequestLocator as _JRAOfficialFinalWinOddsRequestLocator,
    parse_jra_external_race_id as _parse_jra_external_race_id,
)
from scripts.simulation.jra_target_race_card_discovery import (
    JRATargetRaceCardDiscovery as _JRATargetRaceCardDiscovery,
    JRATargetRaceSelectionSuppliedOfficialResponse as _JRATargetRaceSelectionSuppliedOfficialResponse,
    discover_jra_target_race_card_locator as _discover_jra_target_race_card_locator,
)
from scripts.simulation.jra_target_race_card_locator import (
    JRAOfficialTargetNavigationMenuSuppliedResponse as _JRAOfficialTargetNavigationMenuSuppliedResponse,
    JRATargetMeetingSelectionRequestLocator as _JRATargetMeetingSelectionRequestLocator,
    JRATargetMeetingSelectionSuppliedOfficialResponse as _JRATargetMeetingSelectionSuppliedOfficialResponse,
    JRATargetRaceSelectionRequestLocator as _JRATargetRaceSelectionRequestLocator,
    discover_jra_target_meeting_selection_request_locator as _discover_jra_target_meeting_selection_request_locator,
    discover_jra_target_race_selection_request_locator as _discover_jra_target_race_selection_request_locator,
)


_CONNECT_TIMEOUT_SECONDS = 10.0
_READ_TIMEOUT_SECONDS = 10.0
_MAX_RESPONSE_BODY_BYTES = 4 * 1024 * 1024
_CONTENT_LENGTH = _re.compile(r"(?:0|[1-9][0-9]*)\Z")
_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/138.0 Safari/537.36"
_TARGET_NAVIGATION_ROOT_URL = "https://www.jra.go.jp/"


class JRAOfficialResponseCaptureTransportError(_JRAOfficialResponseCaptureError):
    """A trusted live acquisition could not produce one complete HTTP entity."""


@_dataclass(frozen=True, slots=True, init=False)
class JRATargetRaceNavigationCaptureResult:
    """Durable race-selection provenance plus one exact discovered target-card locator."""

    discovery: _JRATargetRaceCardDiscovery
    target_race_selection_capture_id: str

    def __init__(
        self,
        *,
        discovery: _JRATargetRaceCardDiscovery,
        capture: _JRATargetRaceSelectionResponseCapture,
    ) -> None:
        if type(discovery) is not _JRATargetRaceCardDiscovery:
            raise _JRAOfficialResponseCaptureValidationError("discovery must be exact JRATargetRaceCardDiscovery")
        if type(capture) is not _JRATargetRaceSelectionResponseCapture:
            raise _JRAOfficialResponseCaptureValidationError(
                "capture must be exact JRATargetRaceSelectionResponseCapture"
            )
        if (
            capture.request_locator != discovery.navigation_request_locator
            or capture.response_sha256 != discovery.navigation_response_sha256
            or capture.observed_at != discovery.navigation_observed_at
        ):
            raise _JRAOfficialResponseCaptureValidationError("capture and discovery provenance must agree")
        object.__setattr__(self, "discovery", discovery)
        object.__setattr__(self, "target_race_selection_capture_id", capture.capture_id)


@_dataclass(frozen=True, slots=True)
class _JRAOfficialHTTPResponse:
    canonical_source_url: str
    response_body: bytes
    content_type: str | None
    content_encoding: str | None
    http_date: str | None
    etag: str | None
    last_modified: str | None
    content_length: int | None


class _JRAOfficialHTTPTransport(_Protocol):
    def fetch(self, *, canonical_source_url: str) -> _JRAOfficialHTTPResponse: ...

    def fetch_final_win_odds(
        self,
        *,
        request_locator: _JRAOfficialFinalWinOddsRequestLocator,
    ) -> _JRAOfficialHTTPResponse: ...

    def fetch_target_navigation_root(self) -> _JRAOfficialHTTPResponse: ...

    def fetch_target_meeting_selection(
        self,
        *,
        request_locator: _JRATargetMeetingSelectionRequestLocator,
    ) -> _JRAOfficialHTTPResponse: ...

    def fetch_target_race_selection(
        self,
        *,
        request_locator: _JRATargetRaceSelectionRequestLocator,
    ) -> _JRAOfficialHTTPResponse: ...


class _RequestsJRAOfficialHTTPTransport:
    """Private requests transport which returns only a fully checked byte entity."""

    __slots__ = ("_session",)

    def __init__(self) -> None:
        session = _requests.Session()
        adapter = _HTTPAdapter(max_retries=0)
        session.mount("https://", adapter)
        session.headers.update({"User-Agent": _USER_AGENT})
        self._session = session

    def fetch(self, *, canonical_source_url: str) -> _JRAOfficialHTTPResponse:
        response = None
        try:
            response = self._session.get(
                canonical_source_url,
                headers={"Accept-Encoding": "identity"},
                stream=True,
                allow_redirects=False,
                verify=True,
                timeout=(_CONNECT_TIMEOUT_SECONDS, _READ_TIMEOUT_SECONDS),
            )
            if response.status_code != 200:
                raise JRAOfficialResponseCaptureTransportError("official JRA response status must be 200")
            content_encoding = self._content_encoding(response.headers.get("Content-Encoding"))
            content_length = self._content_length(response.headers.get("Content-Length"))
            if content_length is not None and content_length > _MAX_RESPONSE_BODY_BYTES:
                raise JRAOfficialResponseCaptureTransportError("official JRA response body is too large")
            if response.url != canonical_source_url:
                raise JRAOfficialResponseCaptureTransportError("official JRA effective response URL differs")
            body = self._read_body(response)
            if content_length is not None and len(body) != content_length:
                raise JRAOfficialResponseCaptureTransportError("official JRA Content-Length differs from body length")
            return _JRAOfficialHTTPResponse(
                canonical_source_url=canonical_source_url,
                response_body=body,
                content_type=response.headers.get("Content-Type"),
                content_encoding=content_encoding,
                http_date=response.headers.get("Date"),
                etag=response.headers.get("ETag"),
                last_modified=response.headers.get("Last-Modified"),
                content_length=content_length,
            )
        except _requests.RequestException as error:
            raise JRAOfficialResponseCaptureTransportError("official JRA HTTPS acquisition failed") from error
        except (_HTTPError, OSError) as error:
            raise JRAOfficialResponseCaptureTransportError("official JRA HTTPS stream failed") from error
        finally:
            if response is not None:
                response.close()

    def fetch_final_win_odds(
        self,
        *,
        request_locator: _JRAOfficialFinalWinOddsRequestLocator,
    ) -> _JRAOfficialHTTPResponse:
        """POST one cookie-free final-odds request and retain its exact bytes."""

        if type(request_locator) is not _JRAOfficialFinalWinOddsRequestLocator:
            raise _JRAOfficialResponseCaptureValidationError(
                "request_locator must be exact JRAOfficialFinalWinOddsRequestLocator"
            )
        request = self._prepared_cookie_free_request(
            method="POST",
            url=request_locator.endpoint_url,
            data={"cname": request_locator.cname},
        )
        return self._send_prepared(request=request, canonical_source_url=request_locator.endpoint_url)

    def fetch_target_navigation_root(self) -> _JRAOfficialHTTPResponse:
        request = self._prepared_cookie_free_request(method="GET", url=_TARGET_NAVIGATION_ROOT_URL)
        return self._send_prepared(request=request, canonical_source_url=_TARGET_NAVIGATION_ROOT_URL)

    def fetch_target_meeting_selection(
        self,
        *,
        request_locator: _JRATargetMeetingSelectionRequestLocator,
    ) -> _JRAOfficialHTTPResponse:
        if type(request_locator) is not _JRATargetMeetingSelectionRequestLocator:
            raise _JRAOfficialResponseCaptureValidationError(
                "request_locator must be exact JRATargetMeetingSelectionRequestLocator"
            )
        return self._fetch_target_navigation_post(
            endpoint_url=request_locator.endpoint_url,
            cname=request_locator.cname,
        )

    def fetch_target_race_selection(
        self,
        *,
        request_locator: _JRATargetRaceSelectionRequestLocator,
    ) -> _JRAOfficialHTTPResponse:
        if type(request_locator) is not _JRATargetRaceSelectionRequestLocator:
            raise _JRAOfficialResponseCaptureValidationError(
                "request_locator must be exact JRATargetRaceSelectionRequestLocator"
            )
        return self._fetch_target_navigation_post(
            endpoint_url=request_locator.endpoint_url,
            cname=request_locator.cname,
        )

    def _fetch_target_navigation_post(self, *, endpoint_url: str, cname: str) -> _JRAOfficialHTTPResponse:
        request = self._prepared_cookie_free_request(method="POST", url=endpoint_url, data={"cname": cname})
        return self._send_prepared(request=request, canonical_source_url=endpoint_url)

    @staticmethod
    def _prepared_cookie_free_request(
        *,
        method: str,
        url: str,
        data: dict[str, str] | None = None,
    ) -> _requests.PreparedRequest:
        headers = {"Accept-Encoding": "identity", "User-Agent": _USER_AGENT}
        if method == "POST":
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        request = _requests.Request(method=method, url=url, data=data, headers=headers).prepare()
        request.headers.pop("Cookie", None)
        request.headers.pop("Referer", None)
        request.headers.pop("Origin", None)
        return request

    def _send_prepared(
        self,
        *,
        request: _requests.PreparedRequest,
        canonical_source_url: str,
    ) -> _JRAOfficialHTTPResponse:
        response = None
        try:
            response = self._session.send(
                request,
                stream=True,
                allow_redirects=False,
                verify=True,
                timeout=(_CONNECT_TIMEOUT_SECONDS, _READ_TIMEOUT_SECONDS),
            )
            return self._complete_response(response=response, canonical_source_url=canonical_source_url)
        except _requests.RequestException as error:
            raise JRAOfficialResponseCaptureTransportError("official JRA HTTPS acquisition failed") from error
        except (_HTTPError, OSError) as error:
            raise JRAOfficialResponseCaptureTransportError("official JRA HTTPS stream failed") from error
        finally:
            if response is not None:
                response.close()

    def _complete_response(
        self,
        *,
        response: object,
        canonical_source_url: str,
    ) -> _JRAOfficialHTTPResponse:
        if response.status_code != 200:
            raise JRAOfficialResponseCaptureTransportError("official JRA response status must be 200")
        content_encoding = self._content_encoding(response.headers.get("Content-Encoding"))
        content_length = self._content_length(response.headers.get("Content-Length"))
        if content_length is not None and content_length > _MAX_RESPONSE_BODY_BYTES:
            raise JRAOfficialResponseCaptureTransportError("official JRA response body is too large")
        if response.url != canonical_source_url:
            raise JRAOfficialResponseCaptureTransportError("official JRA effective response URL differs")
        body = self._read_body(response)
        if content_length is not None and len(body) != content_length:
            raise JRAOfficialResponseCaptureTransportError("official JRA Content-Length differs from body length")
        return _JRAOfficialHTTPResponse(
            canonical_source_url=canonical_source_url,
            response_body=body,
            content_type=response.headers.get("Content-Type"),
            content_encoding=content_encoding,
            http_date=response.headers.get("Date"),
            etag=response.headers.get("ETag"),
            last_modified=response.headers.get("Last-Modified"),
            content_length=content_length,
        )

    @staticmethod
    def _content_encoding(value: object) -> str | None:
        if value is None:
            return None
        if type(value) is str and value.strip().lower() == "identity":
            return "identity"
        raise _JRAOfficialResponseCaptureUnsupportedError("unsupported official JRA Content-Encoding")

    @staticmethod
    def _content_length(value: object) -> int | None:
        if value is None:
            return None
        if type(value) is not str or _CONTENT_LENGTH.fullmatch(value) is None:
            raise JRAOfficialResponseCaptureTransportError("official JRA Content-Length is invalid")
        if len(value) > len(str(_MAX_RESPONSE_BODY_BYTES)) or (len(value) == len(str(_MAX_RESPONSE_BODY_BYTES)) and value > str(_MAX_RESPONSE_BODY_BYTES)):
            raise JRAOfficialResponseCaptureTransportError("official JRA response body is too large")
        return int(value)

    @staticmethod
    def _read_body(response: object) -> bytes:
        raw = response.raw
        raw.decode_content = False
        chunks: list[bytes] = []
        total = 0
        for chunk in raw.stream(amt=64 * 1024, decode_content=False):
            if type(chunk) is not bytes:
                raise JRAOfficialResponseCaptureTransportError("official JRA response stream is not bytes")
            if not chunk:
                continue
            total += len(chunk)
            if total > _MAX_RESPONSE_BODY_BYTES:
                raise JRAOfficialResponseCaptureTransportError("official JRA response body is too large")
            chunks.append(chunk)
        return b"".join(chunks)


class JRAOfficialLiveResponseCaptureService:
    """Capture one canonical official JRA URL and persist it before returning."""

    __slots__ = ("_archive", "_transport", "_utc_clock")

    def __init__(
        self,
        *,
        archive: _JRAOfficialResponseCaptureArchive,
        transport: _JRAOfficialHTTPTransport,
        utc_clock: _Callable[[], _datetime],
    ) -> None:
        self._archive = archive
        self._transport = transport
        self._utc_clock = utc_clock

    def capture_response(
        self,
        *,
        page_kind: _JRAOfficialPageKind,
        response_url: str,
    ) -> _JRAOfficialResponseCapture:
        """Acquire, validate, archive, then return one exact immutable response capture."""

        canonical_source_url = _canonicalize_jra_official_capture_url(
            page_kind=page_kind,
            response_url=response_url,
        )
        requested_at = self._clock_sample("requested_at")
        result = self._transport.fetch(canonical_source_url=canonical_source_url)
        if type(result) is not _JRAOfficialHTTPResponse or result.canonical_source_url != canonical_source_url:
            raise JRAOfficialResponseCaptureTransportError("official JRA transport result is contradictory")
        observed_at = self._clock_sample("observed_at")
        stored_at = self._clock_sample("stored_at")
        capture = _JRAOfficialResponseCapture(
            canonical_source_url=canonical_source_url,
            response_body=result.response_body,
            charset="cp932",
            requested_at=requested_at,
            observed_at=observed_at,
            stored_at=stored_at,
            http_status=200,
            content_type=result.content_type,
            content_encoding=result.content_encoding,
            http_date=result.http_date,
            etag=result.etag,
            last_modified=result.last_modified,
            content_length=result.content_length,
        )
        self._archive.save_capture(capture=capture)
        return capture

    def capture_target_race_card_response(
        self,
        *,
        response_url: str,
    ) -> _JRAOfficialTargetRaceCardResponseCapture:
        """Acquire, validate, archive, then return one exact schema-v3 accessD capture."""

        canonical_source_url = _canonical_target_race_card_url(response_url, "response_url")
        requested_at = self._clock_sample("requested_at")
        result = self._transport.fetch(canonical_source_url=canonical_source_url)
        if type(result) is not _JRAOfficialHTTPResponse or result.canonical_source_url != canonical_source_url:
            raise JRAOfficialResponseCaptureTransportError("official JRA transport result is contradictory")
        observed_at = self._clock_sample("observed_at")
        stored_at = self._clock_sample("stored_at")
        capture = _JRAOfficialTargetRaceCardResponseCapture(
            canonical_source_url=canonical_source_url,
            response_body=result.response_body,
            charset="cp932",
            requested_at=requested_at,
            observed_at=observed_at,
            stored_at=stored_at,
            http_status=200,
            content_type=result.content_type,
            content_encoding=result.content_encoding,
            http_date=result.http_date,
            etag=result.etag,
            last_modified=result.last_modified,
            content_length=result.content_length,
        )
        self._archive.save_target_race_card_capture(capture=capture)
        return capture

    def capture_target_race_navigation(
        self,
        *,
        external_race_id: str,
    ) -> JRATargetRaceNavigationCaptureResult:
        """Durably capture target navigation evidence, then discover one exact card locator."""

        _parse_jra_external_race_id(external_race_id)

        root_result = self._transport.fetch_target_navigation_root()
        self._require_navigation_result(root_result, _TARGET_NAVIGATION_ROOT_URL)
        _capture_content_type(root_result.content_type)
        root_response = _JRAOfficialTargetNavigationMenuSuppliedResponse(
            response_body=root_result.response_body,
            charset="cp932",
            observed_at=self._clock_sample("root_observed_at"),
        )
        meeting_locator = _discover_jra_target_meeting_selection_request_locator(
            navigation_menu_response=root_response
        )

        meeting_result = self._transport.fetch_target_meeting_selection(request_locator=meeting_locator)
        self._require_navigation_result(meeting_result, meeting_locator.endpoint_url)
        _capture_content_type(meeting_result.content_type)
        meeting_response = _JRATargetMeetingSelectionSuppliedOfficialResponse(
            request_locator=meeting_locator,
            response_body=meeting_result.response_body,
            charset="cp932",
            observed_at=self._clock_sample("meeting_observed_at"),
        )
        race_locator = _discover_jra_target_race_selection_request_locator(
            external_race_id=external_race_id,
            meeting_selection_response=meeting_response,
        )

        requested_at = self._clock_sample("race_selection_requested_at")
        race_result = self._transport.fetch_target_race_selection(request_locator=race_locator)
        self._require_navigation_result(race_result, race_locator.endpoint_url)
        observed_at = self._clock_sample("race_selection_observed_at")
        race_response = _JRATargetRaceSelectionSuppliedOfficialResponse(
            request_locator=race_locator,
            response_body=race_result.response_body,
            charset="cp932",
            observed_at=observed_at,
        )
        stored_at = self._clock_sample("race_selection_stored_at")
        capture = _JRATargetRaceSelectionResponseCapture(
            request_locator=race_locator,
            response_body=race_response.response_body,
            charset="cp932",
            requested_at=requested_at,
            observed_at=observed_at,
            stored_at=stored_at,
            http_status=200,
            content_type=race_result.content_type,
            content_encoding=race_result.content_encoding,
            http_date=race_result.http_date,
            etag=race_result.etag,
            last_modified=race_result.last_modified,
            content_length=race_result.content_length,
        )
        self._archive.save_target_race_selection_capture(capture=capture)
        discovery = _discover_jra_target_race_card_locator(
            external_race_id=external_race_id,
            navigation_response=capture.to_supplied_official_response(),
        )
        return JRATargetRaceNavigationCaptureResult(discovery=discovery, capture=capture)

    def capture_final_win_odds_response(
        self,
        *,
        request_locator: _JRAOfficialFinalWinOddsRequestLocator,
    ) -> _JRAFinalWinOddsSuppliedOfficialResponse:
        """Acquire, validate, archive, then return one final-win-odds supplied response."""

        if type(request_locator) is not _JRAOfficialFinalWinOddsRequestLocator:
            raise _JRAOfficialResponseCaptureValidationError(
                "request_locator must be exact JRAOfficialFinalWinOddsRequestLocator"
            )
        requested_at = self._clock_sample("requested_at")
        result = self._transport.fetch_final_win_odds(request_locator=request_locator)
        if type(result) is not _JRAOfficialHTTPResponse or result.canonical_source_url != request_locator.endpoint_url:
            raise JRAOfficialResponseCaptureTransportError("official JRA transport result is contradictory")
        observed_at = self._clock_sample("observed_at")
        stored_at = self._clock_sample("stored_at")
        capture = _JRAFinalWinOddsResponseCapture(
            request_locator=request_locator,
            response_body=result.response_body,
            charset="cp932",
            requested_at=requested_at,
            observed_at=observed_at,
            stored_at=stored_at,
            http_status=200,
            content_type=result.content_type,
            content_encoding=result.content_encoding,
            http_date=result.http_date,
            etag=result.etag,
            last_modified=result.last_modified,
            content_length=result.content_length,
        )
        self._archive.save_final_win_odds_capture(capture=capture)
        return capture.to_supplied_official_response()

    @staticmethod
    def _require_navigation_result(result: object, expected_source_url: str) -> None:
        if type(result) is not _JRAOfficialHTTPResponse or result.canonical_source_url != expected_source_url:
            raise JRAOfficialResponseCaptureTransportError("official JRA transport result is contradictory")

    def _clock_sample(self, name: str) -> _datetime:
        value = self._utc_clock()
        if type(value) is not _datetime:
            raise _JRAOfficialResponseCaptureValidationError(f"{name} clock sample must be exact datetime")
        try:
            if value.tzinfo is None or value.utcoffset() is None:
                raise _JRAOfficialResponseCaptureValidationError(f"{name} clock sample must be timezone-aware")
        except _JRAOfficialResponseCaptureValidationError:
            raise
        except (OverflowError, TypeError, ValueError) as error:
            raise _JRAOfficialResponseCaptureValidationError(f"{name} clock sample is invalid") from error
        return value


def _utc_now() -> _datetime:
    return _datetime.now(_timezone.utc)


def build_jra_official_live_response_capture_service(
    *,
    archive: _JRAOfficialResponseCaptureArchive,
) -> JRAOfficialLiveResponseCaptureService:
    """Build the only production composition point for trusted live acquisition."""

    return JRAOfficialLiveResponseCaptureService(
        archive=archive,
        transport=_RequestsJRAOfficialHTTPTransport(),
        utc_clock=_utc_now,
    )


if "annotations" in globals():
    del annotations
