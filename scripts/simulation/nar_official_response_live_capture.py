"""Trusted live HTTPS acquisition for one official NAR parser-input response."""

from __future__ import annotations

from collections.abc import Callable as _Callable
from dataclasses import dataclass as _dataclass
from datetime import datetime as _datetime, timezone as _timezone
import re as _re
from typing import Protocol as _Protocol

import requests as _requests
from requests.adapters import HTTPAdapter as _HTTPAdapter

from scripts.simulation.nar_official_response_capture import (
    NAROfficialResponseCapture as _NAROfficialResponseCapture,
    NAROfficialResponseCaptureArchive as _NAROfficialResponseCaptureArchive,
    NAROfficialResponseCaptureError as _NAROfficialResponseCaptureError,
    NAROfficialResponseCaptureUnsupportedError as _NAROfficialResponseCaptureUnsupportedError,
    NAROfficialResponseCaptureValidationError as _NAROfficialResponseCaptureValidationError,
    canonicalize_nar_official_capture_url as _canonicalize_nar_official_capture_url,
)


_CONNECT_TIMEOUT_SECONDS = 10.0
_READ_TIMEOUT_SECONDS = 10.0
_MAX_RESPONSE_BODY_BYTES = 4 * 1024 * 1024
_CONTENT_LENGTH = _re.compile(r"[0-9]+\Z")
_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/138.0 Safari/537.36"


class NAROfficialResponseCaptureTransportError(_NAROfficialResponseCaptureError):
    """A trusted live acquisition could not produce one complete HTTP entity."""


@_dataclass(frozen=True, slots=True)
class _NAROfficialHTTPResponse:
    canonical_source_url: str
    response_body: bytes
    content_type: str | None
    content_encoding: str | None
    http_date: str | None
    etag: str | None
    last_modified: str | None
    content_length: int | None


class _NAROfficialHTTPTransport(_Protocol):
    def fetch(self, *, canonical_source_url: str) -> _NAROfficialHTTPResponse: ...


class _RequestsNAROfficialHTTPTransport:
    """Private requests transport which returns only a fully checked byte entity."""

    __slots__ = ("_session",)

    def __init__(self) -> None:
        session = _requests.Session()
        adapter = _HTTPAdapter(max_retries=0)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        session.headers.update({"User-Agent": _USER_AGENT})
        self._session = session

    def fetch(self, *, canonical_source_url: str) -> _NAROfficialHTTPResponse:
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
                raise NAROfficialResponseCaptureTransportError("official NAR response status must be 200")
            content_encoding = self._content_encoding(response.headers.get("Content-Encoding"))
            content_length = self._content_length(response.headers.get("Content-Length"))
            if content_length is not None and content_length > _MAX_RESPONSE_BODY_BYTES:
                raise NAROfficialResponseCaptureTransportError("official NAR response body is too large")
            try:
                _kind, effective_url = _canonicalize_nar_official_capture_url(response.url)
            except _NAROfficialResponseCaptureError as error:
                raise NAROfficialResponseCaptureTransportError("official NAR effective response URL is invalid") from error
            if effective_url != canonical_source_url:
                raise NAROfficialResponseCaptureTransportError("official NAR effective response URL differs")
            body = self._read_body(response)
            if content_length is not None and len(body) != content_length:
                raise NAROfficialResponseCaptureTransportError("official NAR Content-Length differs from body length")
            return _NAROfficialHTTPResponse(
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
            raise NAROfficialResponseCaptureTransportError("official NAR HTTPS acquisition failed") from error
        finally:
            if response is not None:
                response.close()

    @staticmethod
    def _content_encoding(value: object) -> str | None:
        if value is None:
            return None
        if type(value) is str and value.strip().lower() == "identity":
            return "identity"
        raise _NAROfficialResponseCaptureUnsupportedError("unsupported official NAR Content-Encoding")

    @staticmethod
    def _content_length(value: object) -> int | None:
        if value is None:
            return None
        if type(value) is not str or _CONTENT_LENGTH.fullmatch(value) is None:
            raise NAROfficialResponseCaptureTransportError("official NAR Content-Length is invalid")
        normalized = value.lstrip("0") or "0"
        maximum = str(_MAX_RESPONSE_BODY_BYTES)
        if len(normalized) > len(maximum) or (len(normalized) == len(maximum) and normalized > maximum):
            raise NAROfficialResponseCaptureTransportError("official NAR response body is too large")
        return int(normalized)

    @staticmethod
    def _read_body(response: object) -> bytes:
        chunks: list[bytes] = []
        total = 0
        for chunk in response.iter_content(chunk_size=64 * 1024):
            if type(chunk) is not bytes:
                raise NAROfficialResponseCaptureTransportError("official NAR response stream is not bytes")
            if not chunk:
                continue
            total += len(chunk)
            if total > _MAX_RESPONSE_BODY_BYTES:
                raise NAROfficialResponseCaptureTransportError("official NAR response body is too large")
            chunks.append(chunk)
        return b"".join(chunks)


class NAROfficialLiveResponseCaptureService:
    """Capture one canonical official NAR URL and persist it before returning."""

    __slots__ = ("_archive", "_transport", "_utc_clock")

    def __init__(
        self,
        *,
        archive: _NAROfficialResponseCaptureArchive,
        transport: _NAROfficialHTTPTransport,
        utc_clock: _Callable[[], _datetime],
    ) -> None:
        self._archive = archive
        self._transport = transport
        self._utc_clock = utc_clock

    def capture_response(self, *, response_url: str) -> _NAROfficialResponseCapture:
        """Acquire, validate, archive, then return one exact immutable response capture."""

        _kind, canonical_source_url = _canonicalize_nar_official_capture_url(response_url)
        requested_at = self._clock_sample("requested_at")
        result = self._transport.fetch(canonical_source_url=canonical_source_url)
        if type(result) is not _NAROfficialHTTPResponse or result.canonical_source_url != canonical_source_url:
            raise NAROfficialResponseCaptureTransportError("official NAR transport result is contradictory")
        observed_at = self._clock_sample("observed_at")
        stored_at = self._clock_sample("stored_at")
        capture = _NAROfficialResponseCapture(
            canonical_source_url=canonical_source_url,
            response_body=result.response_body,
            charset="utf-8",
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

    def _clock_sample(self, name: str) -> _datetime:
        value = self._utc_clock()
        if type(value) is not _datetime:
            raise _NAROfficialResponseCaptureValidationError(f"{name} clock sample must be exact datetime")
        try:
            if value.tzinfo is None or value.utcoffset() is None:
                raise _NAROfficialResponseCaptureValidationError(f"{name} clock sample must be timezone-aware")
        except _NAROfficialResponseCaptureValidationError:
            raise
        except (OverflowError, TypeError, ValueError) as error:
            raise _NAROfficialResponseCaptureValidationError(f"{name} clock sample is invalid") from error
        return value


def _utc_now() -> _datetime:
    return _datetime.now(_timezone.utc)


def build_nar_official_live_response_capture_service(
    *,
    archive: _NAROfficialResponseCaptureArchive,
) -> NAROfficialLiveResponseCaptureService:
    """Build the only production composition point for trusted live acquisition."""

    return NAROfficialLiveResponseCaptureService(
        archive=archive,
        transport=_RequestsNAROfficialHTTPTransport(),
        utc_clock=_utc_now,
    )


if "annotations" in globals():
    del annotations
