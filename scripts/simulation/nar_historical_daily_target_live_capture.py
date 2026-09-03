"""Exact-request live capture for NAR historical daily-target evidence."""

from __future__ import annotations

from collections.abc import Callable as _Callable
from dataclasses import dataclass as _dataclass
from datetime import datetime as _datetime
import re as _re
from typing import Protocol as _Protocol

import requests as _requests
from requests.adapters import HTTPAdapter as _HTTPAdapter

from scripts.simulation.nar_historical_daily_target_capture import (
    NARHistoricalDailyTargetCaptureArchive as _NARHistoricalDailyTargetCaptureArchive,
    NARHistoricalDailyTargetCaptureError as _NARHistoricalDailyTargetCaptureError,
    NARHistoricalDailyTargetCaptureUnsupportedError as _NARHistoricalDailyTargetCaptureUnsupportedError,
    NARHistoricalDailyTargetCaptureValidationError as _NARHistoricalDailyTargetCaptureValidationError,
    NARHistoricalDailyTargetRequestIdentity as _NARHistoricalDailyTargetRequestIdentity,
    NARHistoricalDailyTargetResponseCapture as _NARHistoricalDailyTargetResponseCapture,
)


_CONNECT_TIMEOUT_SECONDS = 10.0
_READ_TIMEOUT_SECONDS = 10.0
_MAX_RESPONSE_BODY_BYTES = 4 * 1024 * 1024
_CONTENT_LENGTH = _re.compile(r"[0-9]+\Z")
_USER_AGENT = "Mozilla/5.0"


class NARHistoricalDailyTargetCaptureTransportError(_NARHistoricalDailyTargetCaptureError):
    """Raised when one exact response entity cannot be captured completely."""


@_dataclass(frozen=True, slots=True)
class _NARHistoricalDailyTargetHTTPResponse:
    effective_url: str
    response_body: bytes
    content_type: str | None
    content_encoding: str | None
    http_date: str | None
    etag: str | None
    last_modified: str | None
    content_length: int | None


class NARHistoricalDailyTargetHTTPTransport(_Protocol):
    """Transport boundary which accepts only an already validated request identity."""

    def fetch(
        self,
        *,
        request_identity: _NARHistoricalDailyTargetRequestIdentity,
    ) -> _NARHistoricalDailyTargetHTTPResponse: ...


class _RequestsNARHistoricalDailyTargetHTTPTransport:
    __slots__ = ("_session",)

    def __init__(self) -> None:
        session = _requests.Session()
        adapter = _HTTPAdapter(max_retries=0)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        session.headers.update({"User-Agent": _USER_AGENT})
        self._session = session

    def fetch(
        self,
        *,
        request_identity: _NARHistoricalDailyTargetRequestIdentity,
    ) -> _NARHistoricalDailyTargetHTTPResponse:
        if type(request_identity) is not _NARHistoricalDailyTargetRequestIdentity:
            raise _NARHistoricalDailyTargetCaptureValidationError(
                "request_identity must be NARHistoricalDailyTargetRequestIdentity"
            )
        response = None
        try:
            response = self._session.get(
                request_identity.resolved_request_url,
                headers={"Accept-Encoding": "identity"},
                stream=True,
                allow_redirects=False,
                verify=True,
                timeout=(_CONNECT_TIMEOUT_SECONDS, _READ_TIMEOUT_SECONDS),
            )
            if response.status_code != 200:
                raise NARHistoricalDailyTargetCaptureTransportError("official NAR response status must be 200")
            if response.url != request_identity.resolved_request_url:
                raise NARHistoricalDailyTargetCaptureTransportError("official NAR effective URL differs")
            content_encoding = self._content_encoding(response.headers.get("Content-Encoding"))
            content_length = self._content_length(response.headers.get("Content-Length"))
            body = self._read_body(response, content_length)
            content_type = response.headers.get("Content-Type")
            if content_type != "text/html; charset=UTF-8":
                raise _NARHistoricalDailyTargetCaptureUnsupportedError(
                    "official NAR daily-target Content-Type is unsupported"
                )
            return _NARHistoricalDailyTargetHTTPResponse(
                effective_url=response.url,
                response_body=body,
                content_type=content_type,
                content_encoding=content_encoding,
                http_date=response.headers.get("Date"),
                etag=response.headers.get("ETag"),
                last_modified=response.headers.get("Last-Modified"),
                content_length=content_length,
            )
        except _requests.RequestException as error:
            raise NARHistoricalDailyTargetCaptureTransportError("official NAR HTTPS acquisition failed") from error
        finally:
            if response is not None:
                response.close()

    @staticmethod
    def _content_encoding(value: object) -> str | None:
        if value is None:
            return None
        if type(value) is str and value == "identity":
            return value
        raise _NARHistoricalDailyTargetCaptureUnsupportedError("official NAR Content-Encoding is unsupported")

    @staticmethod
    def _content_length(value: object) -> int | None:
        if value is None:
            return None
        if type(value) is not str or _CONTENT_LENGTH.fullmatch(value) is None:
            raise NARHistoricalDailyTargetCaptureTransportError("official NAR Content-Length is invalid")
        normalized = value.lstrip("0") or "0"
        maximum = str(_MAX_RESPONSE_BODY_BYTES)
        if len(normalized) > len(maximum) or (len(normalized) == len(maximum) and normalized > maximum):
            raise NARHistoricalDailyTargetCaptureTransportError("official NAR response body is too large")
        return int(normalized)

    @staticmethod
    def _read_body(response: object, content_length: int | None) -> bytes:
        chunks: list[bytes] = []
        size = 0
        for chunk in response.iter_content(chunk_size=64 * 1024):
            if type(chunk) is not bytes:
                raise NARHistoricalDailyTargetCaptureTransportError("official NAR stream yielded non-bytes")
            if not chunk:
                continue
            size += len(chunk)
            if size > _MAX_RESPONSE_BODY_BYTES:
                raise NARHistoricalDailyTargetCaptureTransportError("official NAR response body is too large")
            chunks.append(chunk)
        body = b"".join(chunks)
        if content_length is not None and len(body) != content_length:
            raise NARHistoricalDailyTargetCaptureTransportError(
                "official NAR Content-Length differs from response bytes"
            )
        return body


class NARHistoricalDailyTargetLiveCaptureService:
    """Capture and archive one exact supplied request without discovering a locator."""

    __slots__ = ("_archive", "_transport", "_utc_clock")

    def __init__(
        self,
        *,
        archive: _NARHistoricalDailyTargetCaptureArchive,
        transport: NARHistoricalDailyTargetHTTPTransport,
        utc_clock: _Callable[[], _datetime],
    ) -> None:
        self._archive = archive
        self._transport = transport
        self._utc_clock = utc_clock

    def capture_supplied_response(
        self,
        *,
        request_identity: _NARHistoricalDailyTargetRequestIdentity,
    ) -> _NARHistoricalDailyTargetResponseCapture:
        if type(request_identity) is not _NARHistoricalDailyTargetRequestIdentity:
            raise _NARHistoricalDailyTargetCaptureValidationError(
                "request_identity must be NARHistoricalDailyTargetRequestIdentity"
            )
        requested_at = self._clock("requested_at")
        response = self._transport.fetch(request_identity=request_identity)
        if type(response) is not _NARHistoricalDailyTargetHTTPResponse:
            raise NARHistoricalDailyTargetCaptureTransportError("transport returned an invalid response value")
        if response.effective_url != request_identity.resolved_request_url:
            raise NARHistoricalDailyTargetCaptureTransportError("transport response identity is contradictory")
        observed_at = self._clock("observed_at")
        stored_at = self._clock("stored_at")
        capture = _NARHistoricalDailyTargetResponseCapture(
            request_identity=request_identity,
            response_body=response.response_body,
            charset="utf-8",
            requested_at=requested_at,
            observed_at=observed_at,
            stored_at=stored_at,
            http_status=200,
            content_type=response.content_type,
            content_encoding=response.content_encoding,
            http_date=response.http_date,
            etag=response.etag,
            last_modified=response.last_modified,
            content_length=response.content_length,
        )
        self._archive.save_capture(capture=capture)
        return capture

    def _clock(self, name: str) -> _datetime:
        value = self._utc_clock()
        if type(value) is not _datetime:
            raise _NARHistoricalDailyTargetCaptureValidationError(f"{name} clock sample must be exact datetime")
        try:
            if value.tzinfo is None or value.utcoffset() is None:
                raise _NARHistoricalDailyTargetCaptureValidationError(
                    f"{name} clock sample must be timezone-aware"
                )
        except _NARHistoricalDailyTargetCaptureValidationError:
            raise
        except (OverflowError, TypeError, ValueError) as error:
            raise _NARHistoricalDailyTargetCaptureValidationError(f"{name} clock sample is invalid") from error
        return value


if "annotations" in globals():
    del annotations
