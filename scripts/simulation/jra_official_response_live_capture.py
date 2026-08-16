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
    _canonical_target_race_card_url as _canonical_target_race_card_url,
    canonicalize_jra_official_capture_url as _canonicalize_jra_official_capture_url,
)
from scripts.simulation.jra_official_identity import (
    JRAOfficialFinalWinOddsRequestLocator as _JRAOfficialFinalWinOddsRequestLocator,
)


_CONNECT_TIMEOUT_SECONDS = 10.0
_READ_TIMEOUT_SECONDS = 10.0
_MAX_RESPONSE_BODY_BYTES = 4 * 1024 * 1024
_CONTENT_LENGTH = _re.compile(r"(?:0|[1-9][0-9]*)\Z")
_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/138.0 Safari/537.36"


class JRAOfficialResponseCaptureTransportError(_JRAOfficialResponseCaptureError):
    """A trusted live acquisition could not produce one complete HTTP entity."""


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
        request = _requests.Request(
            method="POST",
            url=request_locator.endpoint_url,
            data={"cname": request_locator.cname},
            headers={
                "Accept-Encoding": "identity",
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": _USER_AGENT,
            },
        ).prepare()
        request.headers.pop("Cookie", None)
        request.headers.pop("Referer", None)
        request.headers.pop("Origin", None)
        response = None
        try:
            response = self._session.send(
                request,
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
            if response.url != request_locator.endpoint_url:
                raise JRAOfficialResponseCaptureTransportError("official JRA effective response URL differs")
            body = self._read_body(response)
            if content_length is not None and len(body) != content_length:
                raise JRAOfficialResponseCaptureTransportError("official JRA Content-Length differs from body length")
            return _JRAOfficialHTTPResponse(
                canonical_source_url=request_locator.endpoint_url,
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
