"""One-request official NAR market-odds raw acquisition boundary."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass
from datetime import datetime as _datetime
import re as _re
from typing import Protocol as _Protocol

import requests as _requests
from requests.adapters import HTTPAdapter as _HTTPAdapter

from scripts.simulation.nar_market_odds_capture import (
    NARMarketOddsCaptureError as _CaptureError,
    NARMarketOddsCaptureUnsupportedError as _CaptureUnsupportedError,
    NARMarketOddsCaptureValidationError as _CaptureValidationError,
    NARMarketOddsPageKind as _NARMarketOddsPageKind,
    NARMarketOddsRaceIdentity as _NARMarketOddsRaceIdentity,
    NARMarketOddsRequestIdentity,
    NARMarketOddsResponseCapture,
    build_nar_market_odds_request_identity as _build_request_identity,
)


_CONNECT_TIMEOUT_SECONDS = 10.0
_READ_TIMEOUT_SECONDS = 20.0
_MAX_RESPONSE_BODY_BYTES = 4 * 1024 * 1024
_STREAM_CHUNK_BYTES = 64 * 1024
_USER_AGENT = "Mozilla/5.0"
_CONTENT_TYPE = "text/html; charset=UTF-8"
_CONTENT_LENGTH = _re.compile(r"(?:0|[1-9][0-9]*)\Z")
_REQUEST_HEADERS = {
    "User-Agent": _USER_AGENT,
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Encoding": "identity",
}


class NARMarketOddsRawAcquisitionError(Exception):
    """Base error for the official raw acquisition boundary."""


class NARMarketOddsRawAcquisitionValidationError(
    NARMarketOddsRawAcquisitionError,
):
    """Raised for malformed or contradictory acquisition values."""


class NARMarketOddsRawAcquisitionTransportError(
    NARMarketOddsRawAcquisitionError,
):
    """Raised when the one requested response cannot be acquired exactly."""


class NARMarketOddsRawAcquisitionUnsupportedError(
    NARMarketOddsRawAcquisitionError,
):
    """Raised for an official response outside the approved raw profile."""


def _validation(message: str) -> NARMarketOddsRawAcquisitionValidationError:
    return NARMarketOddsRawAcquisitionValidationError(message)


def _canonical_request(value: object) -> NARMarketOddsRequestIdentity:
    if type(value) is not NARMarketOddsRequestIdentity:
        raise _validation("request_identity must be exact NARMarketOddsRequestIdentity")
    try:
        page_kind = value.page_kind
        race_identity = value.race_identity
    except (AttributeError, TypeError) as error:
        raise _validation("request_identity structure is malformed") from error
    if type(page_kind) is not _NARMarketOddsPageKind:
        raise _validation("request_identity page_kind is malformed")
    if type(race_identity) is not _NARMarketOddsRaceIdentity:
        raise _validation("request_identity race_identity is malformed")
    try:
        baba_code = race_identity.baba_code
        race_date = race_identity.race_date
        race_no = race_identity.race_no
    except (AttributeError, TypeError) as error:
        raise _validation("request_identity race fields are malformed") from error
    try:
        expected = _build_request_identity(
            page_kind=page_kind,
            baba_code=baba_code,
            race_date=race_date,
            race_no=race_no,
        )
    except _CaptureError as error:
        raise _validation("request_identity race fields are invalid") from error
    try:
        derived_values = (
            value.schema_version,
            value.organization,
            value.source_system,
            value.method,
            value.official_origin,
            value.canonical_request_url,
            value.request_identity_sha256,
            value.request_identity,
        )
    except (AttributeError, TypeError) as error:
        raise _validation("request_identity derived fields are malformed") from error
    derived_types = (int, str, str, str, str, str, str, str)
    if any(
        type(item) is not expected_type
        for item, expected_type in zip(derived_values, derived_types)
    ):
        raise _validation("request_identity derived field types are malformed")
    try:
        matches_expected = value == expected
    except (AttributeError, TypeError) as error:
        raise _validation("request_identity comparison failed") from error
    if not matches_expected:
        raise _validation("request_identity derived values are contradictory")
    return expected


def _target_request(value: object) -> NARMarketOddsRequestIdentity:
    if type(value) is not NARMarketOddsRawAcquisitionTarget:
        raise _validation("target must be exact NARMarketOddsRawAcquisitionTarget")
    try:
        request_identity = value.request_identity
    except (AttributeError, TypeError) as error:
        raise _validation("target request_identity is malformed") from error
    return _canonical_request(request_identity)


def _clock_sample(clock: object, name: str) -> _datetime:
    try:
        value = clock.now_utc()  # type: ignore[attr-defined]
    except NARMarketOddsRawAcquisitionError:
        raise
    except Exception as error:
        raise _validation(f"{name} clock sampling failed") from error
    if type(value) is not _datetime:
        raise _validation(f"{name} clock sample must be exact datetime")
    try:
        if value.tzinfo is None or value.utcoffset() is None:
            raise _validation(f"{name} clock sample must be timezone-aware")
    except NARMarketOddsRawAcquisitionValidationError:
        raise
    except (OverflowError, TypeError, ValueError) as error:
        raise _validation(f"{name} clock sample is invalid") from error
    return value


@_dataclass(frozen=True, slots=True)
class NARMarketOddsRawAcquisitionTarget:
    request_identity: NARMarketOddsRequestIdentity

    def __post_init__(self) -> None:
        object.__setattr__(self, "request_identity", _canonical_request(self.request_identity))


@_dataclass(frozen=True, slots=True)
class NARMarketOddsRawHTTPResponse:
    effective_url: str
    response_body: bytes
    http_status: int
    content_type: str | None
    content_encoding: str | None
    http_date: str | None
    etag: str | None
    last_modified: str | None
    content_length: int | None


class NARMarketOddsRawAcquisitionTransport(_Protocol):
    def fetch(
        self,
        *,
        request_identity: NARMarketOddsRequestIdentity,
        requested_at: _datetime,
    ) -> NARMarketOddsRawHTTPResponse: ...


class NARMarketOddsRawAcquisitionClock(_Protocol):
    def now_utc(self) -> _datetime: ...


class RequestsNARMarketOddsRawAcquisitionTransport:
    """Bounded no-retry transport for one exact Phase32 canonical request."""

    def fetch(
        self,
        *,
        request_identity: NARMarketOddsRequestIdentity,
        requested_at: _datetime,
    ) -> NARMarketOddsRawHTTPResponse:
        request = _canonical_request(request_identity)
        if type(requested_at) is not _datetime:
            raise _validation("requested_at must be exact datetime")
        try:
            if requested_at.tzinfo is None or requested_at.utcoffset() is None:
                raise _validation("requested_at must be timezone-aware")
        except NARMarketOddsRawAcquisitionValidationError:
            raise
        except (OverflowError, TypeError, ValueError) as error:
            raise _validation("requested_at is invalid") from error

        session = None
        response = None
        try:
            session = _requests.Session()
            session.trust_env = False
            session.headers.clear()
            adapter = _HTTPAdapter(max_retries=0)
            session.mount("https://", adapter)
            response = session.get(
                request.canonical_request_url,
                headers=dict(_REQUEST_HEADERS),
                stream=True,
                allow_redirects=False,
                verify=True,
                timeout=(_CONNECT_TIMEOUT_SECONDS, _READ_TIMEOUT_SECONDS),
            )
            if type(response.status_code) is not int or response.status_code != 200:
                raise NARMarketOddsRawAcquisitionTransportError(
                    "official NAR response status must be exact 200",
                )
            if type(response.url) is not str or response.url != request.canonical_request_url:
                raise NARMarketOddsRawAcquisitionTransportError(
                    "official NAR effective URL differs from the canonical request URL",
                )
            content_type = response.headers.get("Content-Type")
            if content_type != _CONTENT_TYPE:
                raise NARMarketOddsRawAcquisitionUnsupportedError(
                    "official NAR Content-Type is outside the approved raw profile",
                )
            content_encoding = self._content_encoding(response.headers.get("Content-Encoding"))
            content_length = self._content_length(response.headers.get("Content-Length"))
            body = self._read_body(response, content_length)
            return NARMarketOddsRawHTTPResponse(
                effective_url=response.url,
                response_body=body,
                http_status=response.status_code,
                content_type=content_type,
                content_encoding=content_encoding,
                http_date=response.headers.get("Date"),
                etag=response.headers.get("ETag"),
                last_modified=response.headers.get("Last-Modified"),
                content_length=content_length,
            )
        except NARMarketOddsRawAcquisitionError:
            raise
        except _requests.RequestException as error:
            raise NARMarketOddsRawAcquisitionTransportError(
                "official NAR HTTPS acquisition failed",
            ) from error
        except Exception as error:
            raise NARMarketOddsRawAcquisitionTransportError(
                "official NAR response acquisition failed",
            ) from error
        finally:
            if response is not None:
                response.close()
            if session is not None:
                session.close()

    @staticmethod
    def _content_encoding(value: object) -> str | None:
        if value is None:
            return None
        if type(value) is str and value == "identity":
            return value
        raise NARMarketOddsRawAcquisitionUnsupportedError(
            "official NAR Content-Encoding is outside the approved raw profile",
        )

    @staticmethod
    def _content_length(value: object) -> int | None:
        if value is None:
            return None
        if type(value) is not str or _CONTENT_LENGTH.fullmatch(value) is None:
            raise NARMarketOddsRawAcquisitionTransportError(
                "official NAR Content-Length is invalid",
            )
        normalized = value.lstrip("0") or "0"
        maximum = str(_MAX_RESPONSE_BODY_BYTES)
        if len(normalized) > len(maximum) or (
            len(normalized) == len(maximum) and normalized > maximum
        ):
            raise NARMarketOddsRawAcquisitionTransportError(
                "official NAR response body is too large",
            )
        return int(normalized)

    @staticmethod
    def _read_body(response: object, content_length: int | None) -> bytes:
        raw = response.raw  # type: ignore[attr-defined]
        raw.decode_content = False
        chunks: list[bytes] = []
        size = 0
        for chunk in raw.stream(amt=_STREAM_CHUNK_BYTES, decode_content=False):
            if type(chunk) is not bytes:
                raise NARMarketOddsRawAcquisitionTransportError(
                    "official NAR raw stream yielded non-bytes",
                )
            if not chunk:
                continue
            size += len(chunk)
            if size > _MAX_RESPONSE_BODY_BYTES:
                raise NARMarketOddsRawAcquisitionTransportError(
                    "official NAR response body is too large",
                )
            chunks.append(chunk)
        body = b"".join(chunks)
        if content_length is not None and len(body) != content_length:
            raise NARMarketOddsRawAcquisitionTransportError(
                "official NAR Content-Length differs from response bytes",
            )
        return body


def acquire_nar_market_odds_raw_response(
    *,
    target: NARMarketOddsRawAcquisitionTarget,
    transport: NARMarketOddsRawAcquisitionTransport,
    clock: NARMarketOddsRawAcquisitionClock,
) -> NARMarketOddsResponseCapture:
    """Acquire one state-neutral raw response and construct its Phase32 capture."""

    request = _target_request(target)
    requested_at = _clock_sample(clock, "requested_at")
    try:
        response = transport.fetch(
            request_identity=request,
            requested_at=requested_at,
        )
    except NARMarketOddsRawAcquisitionError:
        raise
    except Exception as error:
        raise NARMarketOddsRawAcquisitionTransportError(
            "raw acquisition transport failed",
        ) from error
    if type(response) is not NARMarketOddsRawHTTPResponse:
        raise _validation("transport returned an invalid response value")
    if type(response.http_status) is not int or response.http_status != 200:
        raise NARMarketOddsRawAcquisitionTransportError(
            "transport response status must be exact 200",
        )
    if type(response.effective_url) is not str or response.effective_url != request.canonical_request_url:
        raise NARMarketOddsRawAcquisitionTransportError(
            "transport effective URL differs from the canonical request URL",
        )
    if response.content_type != _CONTENT_TYPE:
        raise NARMarketOddsRawAcquisitionUnsupportedError(
            "transport Content-Type is outside the approved raw profile",
        )
    if response.content_encoding not in (None, "identity"):
        raise NARMarketOddsRawAcquisitionUnsupportedError(
            "transport Content-Encoding is outside the approved raw profile",
        )
    observed_at = _clock_sample(clock, "observed_at")
    captured_at = _clock_sample(clock, "captured_at")
    try:
        return NARMarketOddsResponseCapture(
            request_identity=request,
            effective_url=response.effective_url,
            response_body=response.response_body,
            charset="utf-8",
            requested_at=requested_at,
            observed_at=observed_at,
            captured_at=captured_at,
            http_status=response.http_status,
            content_type=response.content_type,
            content_encoding=response.content_encoding,
            http_date=response.http_date,
            etag=response.etag,
            last_modified=response.last_modified,
            content_length=response.content_length,
        )
    except _CaptureUnsupportedError as error:
        raise NARMarketOddsRawAcquisitionUnsupportedError(
            "Phase32 rejected the official response profile",
        ) from error
    except _CaptureValidationError as error:
        raise NARMarketOddsRawAcquisitionValidationError(
            "Phase32 rejected contradictory acquisition values",
        ) from error
    except _CaptureError as error:
        raise NARMarketOddsRawAcquisitionValidationError(
            "Phase32 capture construction failed",
        ) from error


__all__ = (
    "NARMarketOddsRawAcquisitionClock",
    "NARMarketOddsRawAcquisitionError",
    "NARMarketOddsRawAcquisitionTarget",
    "NARMarketOddsRawAcquisitionTransport",
    "NARMarketOddsRawAcquisitionTransportError",
    "NARMarketOddsRawAcquisitionUnsupportedError",
    "NARMarketOddsRawAcquisitionValidationError",
    "NARMarketOddsRawHTTPResponse",
    "RequestsNARMarketOddsRawAcquisitionTransport",
    "acquire_nar_market_odds_raw_response",
)


if "annotations" in globals():
    del annotations
