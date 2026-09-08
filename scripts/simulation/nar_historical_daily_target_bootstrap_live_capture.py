"""Strict live capture of source-owned NAR MonthlyConveneInfo bootstrap evidence."""

from __future__ import annotations

from collections.abc import Callable as _Callable
from dataclasses import dataclass as _dataclass
from datetime import datetime as _datetime
import re as _re
from typing import Protocol as _Protocol

import requests as _requests
from requests.adapters import HTTPAdapter as _HTTPAdapter

from scripts.simulation.nar_historical_daily_target_bootstrap import (
    NARMonthlyConveneInfoLocatorScriptResolution as _ScriptResolution,
    NARMonthlyConveneInfoRootLocator as _RootLocator,
    resolve_nar_monthly_convene_info_locator_script as _resolve_script,
    resolve_nar_monthly_convene_info_request_material as _resolve_material,
    resolve_nar_monthly_convene_info_root_locator as _resolve_root,
)
from scripts.simulation.nar_historical_daily_target_bootstrap_capture import (
    NARMonthlyConveneInfoBootstrapCaptureError as _CaptureError,
    NARMonthlyConveneInfoBootstrapCaptureUnsupportedError as _CaptureUnsupportedError,
    NARMonthlyConveneInfoBootstrapCaptureValidationError as _CaptureValidationError,
    NARMonthlyConveneInfoBootstrapPageKind as _PageKind,
    NARMonthlyConveneInfoBootstrapSupplierCapture as _SupplierCapture,
)


_CONNECT_TIMEOUT_SECONDS = 10.0
_READ_TIMEOUT_SECONDS = 10.0
_MAX_RESPONSE_BODY_BYTES = 4 * 1024 * 1024
_CONTENT_LENGTH = _re.compile(r"[0-9]+\Z")
_USER_AGENT = "Mozilla/5.0"
_URLS = {
    _PageKind.OFFICIAL_HOME: "https://www.keiba.go.jp/",
    _PageKind.MONTHLY_ROOT: (
        "https://www.keiba.go.jp/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop"
    ),
    _PageKind.LOCATOR_SCRIPT: (
        "https://www.keiba.go.jp/KeibaWeb/resources/js/"
        "monthltconveninfo.js?t=20260130_1"
    ),
}
_CONTENT_TYPES = {
    _PageKind.OFFICIAL_HOME: "text/html",
    _PageKind.MONTHLY_ROOT: "text/html; charset=UTF-8",
    _PageKind.LOCATOR_SCRIPT: "application/javascript; charset=UTF-8",
}


class NARMonthlyConveneInfoBootstrapSupplierCaptureArchive(_Protocol):
    """Append-only supplier capture sink; migration belongs to external setup."""

    def save_supplier_capture(self, *, capture: _SupplierCapture) -> None: ...


@_dataclass(frozen=True, slots=True)
class _NARMonthlyConveneInfoBootstrapHTTPResponse:
    effective_url: str
    response_body: bytes
    content_type: str
    content_encoding: str | None
    content_length: int | None


class NARMonthlyConveneInfoBootstrapHTTPTransport(_Protocol):
    """Transport accepting only an exact qualified page-kind/URL pair."""

    def fetch(
        self,
        *,
        page_kind: _PageKind,
        canonical_request_url: str,
    ) -> _NARMonthlyConveneInfoBootstrapHTTPResponse: ...


class NARMonthlyConveneInfoBootstrapTransportError(_CaptureError):
    """Raised when one exact supplier response cannot be captured completely."""


class RequestsNARMonthlyConveneInfoBootstrapHTTPTransport:
    """requests transport closed to the three qualified supplier resources."""

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
        page_kind: _PageKind,
        canonical_request_url: str,
    ) -> _NARMonthlyConveneInfoBootstrapHTTPResponse:
        self._validate_request(page_kind, canonical_request_url)
        response = None
        try:
            response = self._session.get(
                canonical_request_url,
                headers={"Accept-Encoding": "identity"},
                stream=True,
                allow_redirects=False,
                verify=True,
                timeout=(_CONNECT_TIMEOUT_SECONDS, _READ_TIMEOUT_SECONDS),
            )
            if response.status_code != 200:
                raise NARMonthlyConveneInfoBootstrapTransportError(
                    "official NAR supplier response status must be 200"
                )
            if response.url != canonical_request_url:
                raise NARMonthlyConveneInfoBootstrapTransportError(
                    "official NAR supplier effective URL differs"
                )
            content_encoding = self._content_encoding(response.headers.get("Content-Encoding"))
            content_length = self._content_length(response.headers.get("Content-Length"))
            body = self._read_body(response, content_length)
            content_type = response.headers.get("Content-Type")
            if content_type != _CONTENT_TYPES[page_kind]:
                raise _CaptureUnsupportedError(
                    "official NAR supplier Content-Type is unsupported"
                )
            if not body:
                raise NARMonthlyConveneInfoBootstrapTransportError(
                    "official NAR supplier response body is empty"
                )
            return _NARMonthlyConveneInfoBootstrapHTTPResponse(
                effective_url=response.url,
                response_body=body,
                content_type=content_type,
                content_encoding=content_encoding,
                content_length=content_length,
            )
        except _requests.RequestException as error:
            raise NARMonthlyConveneInfoBootstrapTransportError(
                "official NAR supplier HTTPS acquisition failed"
            ) from error
        finally:
            if response is not None:
                response.close()

    @staticmethod
    def _validate_request(page_kind: object, canonical_request_url: object) -> None:
        if type(page_kind) is not _PageKind:
            raise _CaptureValidationError(
                "page_kind must be NARMonthlyConveneInfoBootstrapPageKind"
            )
        if type(canonical_request_url) is not str or canonical_request_url != _URLS[page_kind]:
            raise _CaptureValidationError(
                "canonical_request_url is not the exact qualified URL for page_kind"
            )

    @staticmethod
    def _content_encoding(value: object) -> str | None:
        if value is None:
            return None
        if type(value) is str and value == "identity":
            return value
        raise _CaptureUnsupportedError(
            "official NAR supplier Content-Encoding is unsupported"
        )

    @staticmethod
    def _content_length(value: object) -> int | None:
        if value is None:
            return None
        if type(value) is not str or _CONTENT_LENGTH.fullmatch(value) is None:
            raise NARMonthlyConveneInfoBootstrapTransportError(
                "official NAR supplier Content-Length is invalid"
            )
        normalized = value.lstrip("0") or "0"
        maximum = str(_MAX_RESPONSE_BODY_BYTES)
        if len(normalized) > len(maximum) or (
            len(normalized) == len(maximum) and normalized > maximum
        ):
            raise NARMonthlyConveneInfoBootstrapTransportError(
                "official NAR supplier response body is too large"
            )
        return int(normalized)

    @staticmethod
    def _read_body(response: object, content_length: int | None) -> bytes:
        chunks: list[bytes] = []
        size = 0
        for chunk in response.iter_content(chunk_size=64 * 1024):
            if type(chunk) is not bytes:
                raise NARMonthlyConveneInfoBootstrapTransportError(
                    "official NAR supplier stream yielded non-bytes"
                )
            if not chunk:
                continue
            size += len(chunk)
            if size > _MAX_RESPONSE_BODY_BYTES:
                raise NARMonthlyConveneInfoBootstrapTransportError(
                    "official NAR supplier response body is too large"
                )
            chunks.append(chunk)
        body = b"".join(chunks)
        if content_length is not None and len(body) != content_length:
            raise NARMonthlyConveneInfoBootstrapTransportError(
                "official NAR supplier Content-Length differs from response bytes"
            )
        return body


class NARMonthlyConveneInfoBootstrapLiveCaptureService:
    """Fresh staged supplier acquisition with immediate append-only archive save."""

    __slots__ = ("_archive", "_transport", "_utc_clock")

    def __init__(
        self,
        *,
        archive: NARMonthlyConveneInfoBootstrapSupplierCaptureArchive,
        transport: NARMonthlyConveneInfoBootstrapHTTPTransport,
        utc_clock: _Callable[[], _datetime],
    ) -> None:
        self._archive = archive
        self._transport = transport
        self._utc_clock = utc_clock

    def capture_official_home(self) -> _SupplierCapture:
        return self._capture(
            page_kind=_PageKind.OFFICIAL_HOME,
            canonical_request_url=_URLS[_PageKind.OFFICIAL_HOME],
        )

    def capture_monthly_root(
        self,
        *,
        homepage_capture: _SupplierCapture,
        root_locator: _RootLocator,
    ) -> _SupplierCapture:
        expected = _resolve_root(homepage_capture=homepage_capture)
        if type(root_locator) is not _RootLocator or root_locator != expected:
            raise _CaptureValidationError(
                "root_locator is not bound to the supplied homepage capture"
            )
        return self._capture(
            page_kind=_PageKind.MONTHLY_ROOT,
            canonical_request_url=expected.resolved_url,
        )

    def capture_locator_script(
        self,
        *,
        monthly_root_capture: _SupplierCapture,
        locator_script_resolution: _ScriptResolution,
    ) -> _SupplierCapture:
        if type(locator_script_resolution) is not _ScriptResolution:
            raise _CaptureValidationError(
                "locator_script_resolution has the wrong type"
            )
        expected = _resolve_script(
            target_date=locator_script_resolution.target_date,
            root_locator=locator_script_resolution.root_locator,
            monthly_root_capture=monthly_root_capture,
        )
        if locator_script_resolution != expected:
            raise _CaptureValidationError(
                "locator_script_resolution is not bound to the supplied Monthly root capture"
            )
        capture = self._capture_value(
            page_kind=_PageKind.LOCATOR_SCRIPT,
            canonical_request_url=expected.resolved_script_url,
        )
        _resolve_material(
            locator_script_resolution=expected,
            locator_script_capture=capture,
        )
        self._archive.save_supplier_capture(capture=capture)
        return capture

    def _capture(self, *, page_kind: _PageKind, canonical_request_url: str) -> _SupplierCapture:
        capture = self._capture_value(
            page_kind=page_kind,
            canonical_request_url=canonical_request_url,
        )
        self._archive.save_supplier_capture(capture=capture)
        return capture

    def _capture_value(
        self,
        *,
        page_kind: _PageKind,
        canonical_request_url: str,
    ) -> _SupplierCapture:
        requested_at = self._clock("requested_at")
        response = self._transport.fetch(
            page_kind=page_kind,
            canonical_request_url=canonical_request_url,
        )
        if type(response) is not _NARMonthlyConveneInfoBootstrapHTTPResponse:
            raise NARMonthlyConveneInfoBootstrapTransportError(
                "transport returned an invalid response value"
            )
        if response.effective_url != canonical_request_url:
            raise NARMonthlyConveneInfoBootstrapTransportError(
                "transport response identity is contradictory"
            )
        observed_at = self._clock("observed_at")
        stored_at = self._clock("stored_at")
        return _SupplierCapture(
            page_kind=page_kind,
            canonical_request_url=canonical_request_url,
            effective_url=response.effective_url,
            response_body=response.response_body,
            charset="utf-8",
            requested_at=requested_at,
            observed_at=observed_at,
            stored_at=stored_at,
            http_status=200,
            content_type=response.content_type,
            content_encoding=response.content_encoding,
            content_length=response.content_length,
        )

    def _clock(self, name: str) -> _datetime:
        value = self._utc_clock()
        if type(value) is not _datetime:
            raise _CaptureValidationError(f"{name} clock sample must be exact datetime")
        try:
            if value.tzinfo is None or value.utcoffset() is None:
                raise _CaptureValidationError(f"{name} clock sample must be timezone-aware")
        except _CaptureValidationError:
            raise
        except (OverflowError, TypeError, ValueError) as error:
            raise _CaptureValidationError(f"{name} clock sample is invalid") from error
        return value


if "annotations" in globals():
    del annotations
