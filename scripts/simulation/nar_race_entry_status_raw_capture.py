"""State-neutral raw capture bundle for official NAR entry/status pages."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass, field as _field
from datetime import date as _date, datetime as _datetime, timezone as _timezone
from enum import StrEnum as _StrEnum
import hashlib as _hashlib
import json as _json
import re as _re
import sys as _sys
from typing import Protocol as _Protocol

import requests as _requests
from requests.adapters import HTTPAdapter as _HTTPAdapter
import urllib3 as _urllib3


_OFFICIAL_ORIGIN = "https://www.keiba.go.jp"
_SOURCE_SYSTEM = "keiba.go.jp"
_DEBA_TABLE_PATH = "/KeibaWeb/TodayRaceInfo/DebaTable"
_RACE_LIST_PATH = "/KeibaWeb/TodayRaceInfo/RaceList"
_REQUEST_PREFIX = "nar-race-entry-status-request-v1:"
_CAPTURE_PREFIX = "nar-race-entry-status-capture-v1:"
_BUNDLE_PREFIX = "nar-race-entry-status-raw-bundle-v1:"
_BUNDLE_ALGORITHM_NAME = "nar-race-entry-status-raw-bundle"
_BUNDLE_ALGORITHM_VERSION = "v1"
_BABA_CODE = _re.compile(r"[1-9][0-9]*\Z", flags=_re.ASCII)
_CONTENT_LENGTH = _re.compile(r"(?:0|[1-9][0-9]*)\Z", flags=_re.ASCII)
_LOWER_HEX_64 = _re.compile(r"[0-9a-f]{64}\Z", flags=_re.ASCII)
_CONTENT_TYPE = "text/html; charset=UTF-8"
_CONNECT_TIMEOUT_SECONDS = 10.0
_READ_TIMEOUT_SECONDS = 20.0
_MAX_RESPONSE_BODY_BYTES = 4 * 1024 * 1024
_STREAM_CHUNK_BYTES = 64 * 1024
_REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Encoding": "identity",
}

_CLOSE_FAILURE_TYPES = (
    _requests.RequestException,
    _urllib3.exceptions.HTTPError,
    AttributeError,
    KeyError,
    IndexError,
    TypeError,
    ValueError,
    OverflowError,
    RuntimeError,
    OSError,
)


class NARRaceEntryStatusRawCaptureError(Exception):
    """Base error for the NAR entry/status raw-capture boundary."""


class NARRaceEntryStatusRawCaptureValidationError(NARRaceEntryStatusRawCaptureError):
    """Raised for malformed or contradictory caller/capture values."""


class NARRaceEntryStatusRawCaptureTransportError(NARRaceEntryStatusRawCaptureError):
    """Raised when an exact raw HTTP entity cannot be acquired."""


class NARRaceEntryStatusRawCaptureUnsupportedResponseError(NARRaceEntryStatusRawCaptureError):
    """Raised when an HTTP entity is outside the approved response profile."""


class NARRaceEntryStatusRawCaptureBundleIntegrityError(NARRaceEntryStatusRawCaptureError):
    """Raised when two otherwise valid captures cannot form one closed bundle."""


def _validation(message: str) -> NARRaceEntryStatusRawCaptureValidationError:
    return NARRaceEntryStatusRawCaptureValidationError(message)


def _unsupported(message: str) -> NARRaceEntryStatusRawCaptureUnsupportedResponseError:
    return NARRaceEntryStatusRawCaptureUnsupportedResponseError(message)


def _canonical_json_bytes(payload: object) -> bytes:
    try:
        return _json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, OverflowError) as error:
        raise _validation("canonical identity payload is invalid") from error


def _sha256_bytes(value: bytes) -> str:
    digest = _hashlib.sha256(value).hexdigest()
    if _LOWER_HEX_64.fullmatch(digest) is None:  # defensive invariant
        raise _validation("SHA-256 implementation returned a noncanonical digest")
    return digest


def _datetime_utc(value: object, name: str) -> _datetime:
    if type(value) is not _datetime:
        raise _validation(f"{name} must be exact datetime")
    try:
        if value.tzinfo is None or value.utcoffset() is None:
            raise _validation(f"{name} must be timezone-aware")
        normalized = value.astimezone(_timezone.utc)
    except NARRaceEntryStatusRawCaptureValidationError:
        raise
    except (OverflowError, TypeError, ValueError) as error:
        raise _validation(f"{name} cannot be normalized to UTC") from error
    return normalized


def _datetime_text(value: _datetime) -> str:
    return value.astimezone(_timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _metadata_value(value: object, name: str) -> str | None:
    if value is None:
        return None
    if type(value) is not str:
        raise _validation(f"{name} must be exact str or None")
    return value


def _content_encoding_value(value: object) -> str | None:
    if value is None:
        return None
    if type(value) is str and value == "identity":
        return value
    raise _unsupported("Content-Encoding is outside the approved response profile")


def _content_length_value(value: object, body_length: int) -> int | None:
    if value is None:
        return None
    if type(value) is not int or isinstance(value, bool) or value < 0:
        raise _validation("content_length must be exact non-negative int or None")
    if value != body_length:
        raise _unsupported("Content-Length differs from raw response bytes")
    return value


def _close_failure(resource: object) -> Exception | None:
    try:
        resource.close()  # type: ignore[attr-defined]
    except _CLOSE_FAILURE_TYPES as error:
        return error
    return None


def _validate_baba_code(value: object, name: str = "baba_code") -> str:
    if type(value) is not str or _BABA_CODE.fullmatch(value) is None:
        raise _validation(f"{name} must be a canonical positive ASCII provider code")
    return value


def _validate_date(value: object, name: str = "race_date") -> _date:
    if type(value) is not _date:
        raise _validation(f"{name} must be exact date")
    return value


def _validate_race_no(value: object, name: str = "race_no") -> int:
    if type(value) is not int or isinstance(value, bool) or value <= 0:
        raise _validation(f"{name} must be exact positive int")
    return value


@_dataclass(frozen=True, slots=True)
class NARRaceEntryStatusDayScope:
    baba_code: str
    race_date: _date

    def __post_init__(self) -> None:
        _validate_baba_code(self.baba_code)
        _validate_date(self.race_date)


@_dataclass(frozen=True, slots=True)
class NARRaceEntryStatusRaceIdentity:
    baba_code: str
    race_date: _date
    race_no: int

    def __post_init__(self) -> None:
        _validate_baba_code(self.baba_code)
        _validate_date(self.race_date)
        _validate_race_no(self.race_no)


def _canonical_day_scope(value: object) -> NARRaceEntryStatusDayScope:
    if type(value) is not NARRaceEntryStatusDayScope:
        raise _validation("day_scope must be exact NARRaceEntryStatusDayScope")
    try:
        return NARRaceEntryStatusDayScope(
            baba_code=value.baba_code,
            race_date=value.race_date,
        )
    except (AttributeError, TypeError) as error:
        raise _validation("day_scope structure is malformed") from error


def _canonical_race_identity(value: object) -> NARRaceEntryStatusRaceIdentity:
    if type(value) is not NARRaceEntryStatusRaceIdentity:
        raise _validation("target must be exact NARRaceEntryStatusRaceIdentity")
    try:
        return NARRaceEntryStatusRaceIdentity(
            baba_code=value.baba_code,
            race_date=value.race_date,
            race_no=value.race_no,
        )
    except (AttributeError, TypeError) as error:
        raise _validation("target race identity structure is malformed") from error


class NARRaceEntryStatusPageKind(_StrEnum):
    DEBA_TABLE = "deba_table"
    RACE_LIST = "race_list"


@_dataclass(frozen=True, slots=True)
class NARRaceEntryStatusRequestIdentity:
    page_kind: NARRaceEntryStatusPageKind
    day_scope: NARRaceEntryStatusDayScope
    request_race_no: int | None
    canonical_request_url: str = _field(init=False)
    request_identity_sha256: str = _field(init=False)
    request_identity: str = _field(init=False)

    def __post_init__(self) -> None:
        if type(self.page_kind) is not NARRaceEntryStatusPageKind:
            raise _validation("page_kind must be exact NARRaceEntryStatusPageKind")
        day_scope = _canonical_day_scope(self.day_scope)
        encoded_date = day_scope.race_date.isoformat().replace("-", "%2F")
        if self.page_kind is NARRaceEntryStatusPageKind.DEBA_TABLE:
            request_race_no = _validate_race_no(self.request_race_no, "request_race_no")
            canonical_url = (
                f"{_OFFICIAL_ORIGIN}{_DEBA_TABLE_PATH}?k_babaCode={day_scope.baba_code}"
                f"&k_raceDate={encoded_date}&k_raceNo={request_race_no}"
            )
            request_scope: dict[str, object] = {
                "baba_code": day_scope.baba_code,
                "race_date": day_scope.race_date.isoformat(),
                "race_no": request_race_no,
                "scope_kind": "race",
            }
        else:
            if self.request_race_no is not None:
                raise _validation("RaceList request_race_no must be None")
            request_race_no = None
            canonical_url = (
                f"{_OFFICIAL_ORIGIN}{_RACE_LIST_PATH}?k_raceDate={encoded_date}"
                f"&k_babaCode={day_scope.baba_code}"
            )
            request_scope = {
                "baba_code": day_scope.baba_code,
                "race_date": day_scope.race_date.isoformat(),
                "scope_kind": "venue_day",
            }
        payload = {
            "canonical_request_url": canonical_url,
            "http_method": "GET",
            "organization": "NAR",
            "page_kind": self.page_kind.value,
            "request_scope": request_scope,
            "schema_version": 1,
            "source_system": _SOURCE_SYSTEM,
        }
        digest = _sha256_bytes(_canonical_json_bytes(payload))
        object.__setattr__(self, "day_scope", day_scope)
        object.__setattr__(self, "request_race_no", request_race_no)
        object.__setattr__(self, "canonical_request_url", canonical_url)
        object.__setattr__(self, "request_identity_sha256", digest)
        object.__setattr__(self, "request_identity", _REQUEST_PREFIX + digest)


def build_nar_race_entry_status_request_identity(
    *,
    page_kind: NARRaceEntryStatusPageKind,
    day_scope: NARRaceEntryStatusDayScope,
    request_race_no: int | None,
) -> NARRaceEntryStatusRequestIdentity:
    return NARRaceEntryStatusRequestIdentity(
        page_kind=page_kind,
        day_scope=day_scope,
        request_race_no=request_race_no,
    )


def _canonical_request(value: object) -> NARRaceEntryStatusRequestIdentity:
    if type(value) is not NARRaceEntryStatusRequestIdentity:
        raise _validation("request_identity must be exact NARRaceEntryStatusRequestIdentity")
    try:
        page_kind = value.page_kind
        day_scope = value.day_scope
        request_race_no = value.request_race_no
    except (AttributeError, TypeError) as error:
        raise _validation("request_identity structure is malformed") from error
    try:
        expected = build_nar_race_entry_status_request_identity(
            page_kind=page_kind,
            day_scope=day_scope,
            request_race_no=request_race_no,
        )
    except NARRaceEntryStatusRawCaptureError:
        raise
    except (AttributeError, TypeError, ValueError) as error:
        raise _validation("request_identity source fields are malformed") from error
    try:
        derived = (
            value.canonical_request_url,
            value.request_identity_sha256,
            value.request_identity,
        )
    except (AttributeError, TypeError) as error:
        raise _validation("request_identity derived fields are malformed") from error
    if any(type(item) is not str for item in derived):
        raise _validation("request_identity derived field types are malformed")
    if derived != (
        expected.canonical_request_url,
        expected.request_identity_sha256,
        expected.request_identity,
    ):
        raise _validation("request_identity derived values are contradictory")
    return expected


@_dataclass(frozen=True, slots=True)
class NARRaceEntryStatusRawHTTPResponse:
    effective_url: str
    response_body: bytes
    http_status: int
    content_type: str | None
    content_encoding: str | None
    http_date: str | None
    etag: str | None
    last_modified: str | None
    content_length: int | None


def _validated_raw_response(
    value: object,
    request: NARRaceEntryStatusRequestIdentity,
) -> NARRaceEntryStatusRawHTTPResponse:
    if type(value) is not NARRaceEntryStatusRawHTTPResponse:
        raise _validation("transport response must be exact NARRaceEntryStatusRawHTTPResponse")
    try:
        effective_url = value.effective_url
        response_body = value.response_body
        http_status = value.http_status
        content_type = value.content_type
        content_encoding = value.content_encoding
        http_date = value.http_date
        etag = value.etag
        last_modified = value.last_modified
        content_length = value.content_length
    except (AttributeError, TypeError) as error:
        raise _validation("transport response structure is malformed") from error
    if type(http_status) is not int or isinstance(http_status, bool) or http_status != 200:
        raise _unsupported("HTTP status must be exact 200")
    if type(effective_url) is not str or effective_url != request.canonical_request_url:
        raise _unsupported("effective URL differs from the canonical request URL")
    if content_type != _CONTENT_TYPE:
        raise _unsupported("Content-Type is outside the approved response profile")
    encoding = _content_encoding_value(content_encoding)
    if type(response_body) is not bytes:
        raise _validation("response_body must be exact bytes")
    if not response_body:
        raise _unsupported("response body must be nonempty")
    if len(response_body) > _MAX_RESPONSE_BODY_BYTES:
        raise _unsupported("response body exceeds the per-document limit")
    try:
        response_body.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise _unsupported("response body is not strict UTF-8") from error
    length = _content_length_value(content_length, len(response_body))
    date_header = _metadata_value(http_date, "http_date")
    etag_header = _metadata_value(etag, "etag")
    modified_header = _metadata_value(last_modified, "last_modified")
    return NARRaceEntryStatusRawHTTPResponse(
        effective_url=effective_url,
        response_body=response_body,
        http_status=http_status,
        content_type=_CONTENT_TYPE,
        content_encoding=encoding,
        http_date=date_header,
        etag=etag_header,
        last_modified=modified_header,
        content_length=length,
    )


@_dataclass(frozen=True, slots=True)
class NARRaceEntryStatusResponseCapture:
    request_identity: NARRaceEntryStatusRequestIdentity
    effective_url: str
    response_body: bytes
    charset: str
    requested_at: _datetime
    observed_at: _datetime
    captured_at: _datetime
    http_status: int
    content_type: str | None = None
    content_encoding: str | None = None
    http_date: str | None = None
    etag: str | None = None
    last_modified: str | None = None
    content_length: int | None = None
    response_sha256: str = _field(init=False)
    byte_length: int = _field(init=False)
    capture_sha256: str = _field(init=False)
    capture_id: str = _field(init=False)

    def __post_init__(self) -> None:
        request = _canonical_request(self.request_identity)
        raw = _validated_raw_response(
            NARRaceEntryStatusRawHTTPResponse(
                effective_url=self.effective_url,
                response_body=self.response_body,
                http_status=self.http_status,
                content_type=self.content_type,
                content_encoding=self.content_encoding,
                http_date=self.http_date,
                etag=self.etag,
                last_modified=self.last_modified,
                content_length=self.content_length,
            ),
            request,
        )
        if type(self.charset) is not str or self.charset != "UTF-8":
            raise _unsupported("charset must be exact UTF-8")
        requested = _datetime_utc(self.requested_at, "requested_at")
        observed = _datetime_utc(self.observed_at, "observed_at")
        captured = _datetime_utc(self.captured_at, "captured_at")
        if not requested <= observed <= captured:
            raise _validation("capture timestamps are out of order")
        response_digest = _sha256_bytes(raw.response_body)
        byte_length = len(raw.response_body)
        payload = {
            "captured_at": _datetime_text(captured),
            "charset": "UTF-8",
            "effective_url": raw.effective_url,
            "http_status": 200,
            "observed_at": _datetime_text(observed),
            "organization": "NAR",
            "request_identity": request.request_identity,
            "request_identity_sha256": request.request_identity_sha256,
            "requested_at": _datetime_text(requested),
            "response_byte_length": byte_length,
            "response_sha256": response_digest,
            "retained_http_metadata": {
                "content_encoding": raw.content_encoding,
                "content_length": raw.content_length,
                "content_type": raw.content_type,
                "date": raw.http_date,
                "etag": raw.etag,
                "last_modified": raw.last_modified,
            },
            "schema_version": 1,
            "source_system": _SOURCE_SYSTEM,
        }
        capture_digest = _sha256_bytes(_canonical_json_bytes(payload))
        object.__setattr__(self, "request_identity", request)
        object.__setattr__(self, "effective_url", raw.effective_url)
        object.__setattr__(self, "response_body", raw.response_body)
        object.__setattr__(self, "charset", "UTF-8")
        object.__setattr__(self, "requested_at", requested)
        object.__setattr__(self, "observed_at", observed)
        object.__setattr__(self, "captured_at", captured)
        object.__setattr__(self, "http_status", 200)
        object.__setattr__(self, "content_type", raw.content_type)
        object.__setattr__(self, "content_encoding", raw.content_encoding)
        object.__setattr__(self, "http_date", raw.http_date)
        object.__setattr__(self, "etag", raw.etag)
        object.__setattr__(self, "last_modified", raw.last_modified)
        object.__setattr__(self, "content_length", raw.content_length)
        object.__setattr__(self, "response_sha256", response_digest)
        object.__setattr__(self, "byte_length", byte_length)
        object.__setattr__(self, "capture_sha256", capture_digest)
        object.__setattr__(self, "capture_id", _CAPTURE_PREFIX + capture_digest)


def _canonical_capture(value: object) -> NARRaceEntryStatusResponseCapture:
    if type(value) is not NARRaceEntryStatusResponseCapture:
        raise _validation("capture must be exact NARRaceEntryStatusResponseCapture")
    try:
        expected = NARRaceEntryStatusResponseCapture(
            request_identity=value.request_identity,
            effective_url=value.effective_url,
            response_body=value.response_body,
            charset=value.charset,
            requested_at=value.requested_at,
            observed_at=value.observed_at,
            captured_at=value.captured_at,
            http_status=value.http_status,
            content_type=value.content_type,
            content_encoding=value.content_encoding,
            http_date=value.http_date,
            etag=value.etag,
            last_modified=value.last_modified,
            content_length=value.content_length,
        )
        derived = (
            value.response_sha256,
            value.byte_length,
            value.capture_sha256,
            value.capture_id,
        )
    except NARRaceEntryStatusRawCaptureError:
        raise
    except (AttributeError, TypeError, ValueError) as error:
        raise _validation("capture structure is malformed") from error
    if type(derived[0]) is not str or type(derived[1]) is not int or any(
        type(item) is not str for item in derived[2:]
    ):
        raise _validation("capture derived field types are malformed")
    if derived != (
        expected.response_sha256,
        expected.byte_length,
        expected.capture_sha256,
        expected.capture_id,
    ):
        raise _validation("capture derived values are contradictory")
    return expected


@_dataclass(frozen=True, slots=True)
class NARRaceEntryStatusRawCaptureBundle:
    target_race_identity: NARRaceEntryStatusRaceIdentity
    deba_table_capture: NARRaceEntryStatusResponseCapture
    race_list_capture: NARRaceEntryStatusResponseCapture
    bundle_sha256: str = _field(init=False)
    bundle_id: str = _field(init=False)

    def __post_init__(self) -> None:
        try:
            deba = _canonical_capture(self.deba_table_capture)
            race_list = _canonical_capture(self.race_list_capture)
        except NARRaceEntryStatusRawCaptureError:
            raise
        if deba.request_identity.page_kind is not NARRaceEntryStatusPageKind.DEBA_TABLE:
            raise NARRaceEntryStatusRawCaptureBundleIntegrityError(
                "deba_table_capture has the wrong page kind",
            )
        if race_list.request_identity.page_kind is not NARRaceEntryStatusPageKind.RACE_LIST:
            raise NARRaceEntryStatusRawCaptureBundleIntegrityError(
                "race_list_capture has the wrong page kind",
            )
        target = _canonical_race_identity(self.target_race_identity)
        target_day = NARRaceEntryStatusDayScope(target.baba_code, target.race_date)
        if (
            deba.request_identity.day_scope != target_day
            or deba.request_identity.request_race_no != target.race_no
        ):
            raise NARRaceEntryStatusRawCaptureBundleIntegrityError(
                "DebaTable request scope differs from the target race",
            )
        if (
            race_list.request_identity.day_scope != target_day
            or race_list.request_identity.request_race_no is not None
        ):
            raise NARRaceEntryStatusRawCaptureBundleIntegrityError(
                "RaceList request scope differs from the target venue-day",
            )
        if not (
            deba.requested_at
            <= deba.observed_at
            <= deba.captured_at
            <= race_list.requested_at
            <= race_list.observed_at
            <= race_list.captured_at
        ):
            raise NARRaceEntryStatusRawCaptureBundleIntegrityError(
                "bundle capture timestamps are out of sequential order",
            )
        payload = {
            "acquisition_algorithm": {
                "name": _BUNDLE_ALGORITHM_NAME,
                "order": ["deba_table", "race_list"],
                "version": _BUNDLE_ALGORITHM_VERSION,
            },
            "deba_table": {
                "capture_id": deba.capture_id,
                "captured_at": _datetime_text(deba.captured_at),
                "observed_at": _datetime_text(deba.observed_at),
                "request_identity_sha256": deba.request_identity.request_identity_sha256,
                "requested_at": _datetime_text(deba.requested_at),
                "response_sha256": deba.response_sha256,
            },
            "organization": "NAR",
            "race_list": {
                "capture_id": race_list.capture_id,
                "captured_at": _datetime_text(race_list.captured_at),
                "observed_at": _datetime_text(race_list.observed_at),
                "request_identity_sha256": race_list.request_identity.request_identity_sha256,
                "requested_at": _datetime_text(race_list.requested_at),
                "response_sha256": race_list.response_sha256,
            },
            "schema_version": 1,
            "source_system": _SOURCE_SYSTEM,
            "target_race": {
                "baba_code": target.baba_code,
                "race_date": target.race_date.isoformat(),
                "race_no": target.race_no,
            },
        }
        digest = _sha256_bytes(_canonical_json_bytes(payload))
        object.__setattr__(self, "target_race_identity", target)
        object.__setattr__(self, "deba_table_capture", deba)
        object.__setattr__(self, "race_list_capture", race_list)
        object.__setattr__(self, "bundle_sha256", digest)
        object.__setattr__(self, "bundle_id", _BUNDLE_PREFIX + digest)


class NARRaceEntryStatusRawCaptureTransport(_Protocol):
    def fetch(
        self,
        *,
        request_identity: NARRaceEntryStatusRequestIdentity,
    ) -> NARRaceEntryStatusRawHTTPResponse: ...


class NARRaceEntryStatusRawCaptureClock(_Protocol):
    def now_utc(self) -> _datetime: ...


class RequestsNARRaceEntryStatusRawCaptureTransport:
    """One-shot exact-byte transport with a fresh session per document."""

    def fetch(
        self,
        *,
        request_identity: NARRaceEntryStatusRequestIdentity,
    ) -> NARRaceEntryStatusRawHTTPResponse:
        request = _canonical_request(request_identity)
        session = None
        response = None
        try:
            session = _requests.Session()
            session.trust_env = False
            session.headers.clear()
            session.mount("https://", _HTTPAdapter(max_retries=0))
            response = session.get(
                request.canonical_request_url,
                headers=dict(_REQUEST_HEADERS),
                stream=True,
                allow_redirects=False,
                verify=True,
                timeout=(_CONNECT_TIMEOUT_SECONDS, _READ_TIMEOUT_SECONDS),
            )
            status = response.status_code
            if type(status) is not int or isinstance(status, bool) or status != 200:
                raise _unsupported("official NAR response status must be exact 200")
            effective_url = response.url
            if type(effective_url) is not str or effective_url != request.canonical_request_url:
                raise _unsupported("official NAR effective URL differs from canonical request URL")
            content_type = response.headers.get("Content-Type")
            if content_type != _CONTENT_TYPE:
                raise _unsupported("official NAR Content-Type is unsupported")
            content_encoding = _content_encoding_value(response.headers.get("Content-Encoding"))
            raw = response.raw
            raw_headers = raw.headers
            getlist = raw_headers.getlist
            if not callable(getlist):
                raise NARRaceEntryStatusRawCaptureTransportError(
                    "raw response headers do not expose reliable getlist semantics",
                )
            raw_lengths = getlist("Content-Length")
            if type(raw_lengths) is not list:
                raise NARRaceEntryStatusRawCaptureTransportError(
                    "raw Content-Length multiplicity is not list-like",
                )
            if len(raw_lengths) > 1:
                raise _unsupported("duplicate Content-Length headers are unsupported")
            content_length = self._parse_content_length(
                None if not raw_lengths else raw_lengths[0],
            )
            raw.decode_content = False
            body = self._read_raw_body(raw, content_length)
            return NARRaceEntryStatusRawHTTPResponse(
                effective_url=effective_url,
                response_body=body,
                http_status=status,
                content_type=content_type,
                content_encoding=content_encoding,
                http_date=_metadata_value(response.headers.get("Date"), "http_date"),
                etag=_metadata_value(response.headers.get("ETag"), "etag"),
                last_modified=_metadata_value(
                    response.headers.get("Last-Modified"),
                    "last_modified",
                ),
                content_length=content_length,
            )
        except NARRaceEntryStatusRawCaptureError:
            raise
        except _requests.RequestException as error:
            raise NARRaceEntryStatusRawCaptureTransportError(
                "official NAR HTTPS request failed",
            ) from error
        except _urllib3.exceptions.HTTPError as error:
            raise NARRaceEntryStatusRawCaptureTransportError(
                "official NAR raw HTTP stream failed",
            ) from error
        except (
            AttributeError,
            KeyError,
            IndexError,
            TypeError,
            ValueError,
            OverflowError,
            RuntimeError,
            OSError,
        ) as error:
            raise NARRaceEntryStatusRawCaptureTransportError(
                "official NAR transport structure failed",
            ) from error
        finally:
            active_failure = _sys.exc_info()[0] is not None
            close_failure = None
            if response is not None:
                close_failure = _close_failure(response)
            if session is not None:
                session_close_failure = _close_failure(session)
                if close_failure is None:
                    close_failure = session_close_failure
            if close_failure is not None and not active_failure:
                raise NARRaceEntryStatusRawCaptureTransportError(
                    "official NAR transport cleanup failed",
                ) from close_failure

    @staticmethod
    def _parse_content_length(value: object) -> int | None:
        if value is None:
            return None
        if type(value) is not str or _CONTENT_LENGTH.fullmatch(value) is None:
            raise _unsupported("official NAR Content-Length is noncanonical")
        normalized = value.lstrip("0") or "0"
        maximum = str(_MAX_RESPONSE_BODY_BYTES)
        if len(normalized) > len(maximum) or (
            len(normalized) == len(maximum) and normalized > maximum
        ):
            raise _unsupported("official NAR response exceeds the per-document limit")
        return int(value)

    @staticmethod
    def _read_raw_body(raw: object, content_length: int | None) -> bytes:
        chunks: list[bytes] = []
        size = 0
        for chunk in raw.stream(amt=_STREAM_CHUNK_BYTES, decode_content=False):  # type: ignore[attr-defined]
            if type(chunk) is not bytes:
                raise NARRaceEntryStatusRawCaptureTransportError(
                    "official NAR raw stream yielded non-bytes",
                )
            if not chunk:
                continue
            size += len(chunk)
            if size > _MAX_RESPONSE_BODY_BYTES:
                raise _unsupported("official NAR response exceeds the per-document limit")
            chunks.append(chunk)
        body = b"".join(chunks)
        if not body:
            raise _unsupported("official NAR response body must be nonempty")
        if content_length is not None and len(body) != content_length:
            raise _unsupported("official NAR Content-Length differs from raw body")
        return body


def _clock_sample(clock: object, name: str) -> _datetime:
    try:
        value = clock.now_utc()  # type: ignore[attr-defined]
    except NARRaceEntryStatusRawCaptureError:
        raise
    except (AttributeError, KeyError, IndexError, TypeError, ValueError, OverflowError, RuntimeError) as error:
        raise _validation(f"{name} clock sampling failed") from error
    return _datetime_utc(value, name)


def _transport_fetch(
    transport: object,
    request: NARRaceEntryStatusRequestIdentity,
) -> object:
    try:
        return transport.fetch(request_identity=request)  # type: ignore[attr-defined]
    except NARRaceEntryStatusRawCaptureError:
        raise
    except _requests.RequestException as error:
        raise NARRaceEntryStatusRawCaptureTransportError("raw transport failed") from error
    except _urllib3.exceptions.HTTPError as error:
        raise NARRaceEntryStatusRawCaptureTransportError("raw transport failed") from error
    except (
        AttributeError,
        KeyError,
        IndexError,
        TypeError,
        ValueError,
        OverflowError,
        RuntimeError,
        OSError,
    ) as error:
        raise NARRaceEntryStatusRawCaptureTransportError("raw transport failed") from error


def _capture_document(
    *,
    request: NARRaceEntryStatusRequestIdentity,
    transport: NARRaceEntryStatusRawCaptureTransport,
    clock: NARRaceEntryStatusRawCaptureClock,
    requested_name: str,
    observed_name: str,
    captured_name: str,
) -> NARRaceEntryStatusResponseCapture:
    requested_at = _clock_sample(clock, requested_name)
    response_value = _transport_fetch(transport, request)
    observed_at = _clock_sample(clock, observed_name)
    response = _validated_raw_response(response_value, request)
    captured_at = _clock_sample(clock, captured_name)
    return NARRaceEntryStatusResponseCapture(
        request_identity=request,
        effective_url=response.effective_url,
        response_body=response.response_body,
        charset="UTF-8",
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


def acquire_nar_race_entry_status_raw_capture_bundle(
    *,
    target: NARRaceEntryStatusRaceIdentity,
    transport: NARRaceEntryStatusRawCaptureTransport,
    clock: NARRaceEntryStatusRawCaptureClock,
) -> NARRaceEntryStatusRawCaptureBundle:
    """Acquire DebaTable then RaceList and return one closed in-memory bundle."""

    canonical_target = _canonical_race_identity(target)
    day_scope = NARRaceEntryStatusDayScope(
        baba_code=canonical_target.baba_code,
        race_date=canonical_target.race_date,
    )
    deba_request = build_nar_race_entry_status_request_identity(
        page_kind=NARRaceEntryStatusPageKind.DEBA_TABLE,
        day_scope=day_scope,
        request_race_no=canonical_target.race_no,
    )
    race_list_request = build_nar_race_entry_status_request_identity(
        page_kind=NARRaceEntryStatusPageKind.RACE_LIST,
        day_scope=day_scope,
        request_race_no=None,
    )
    deba_capture = _capture_document(
        request=deba_request,
        transport=transport,
        clock=clock,
        requested_name="deba_table_requested_at",
        observed_name="deba_table_observed_at",
        captured_name="deba_table_captured_at",
    )
    race_list_capture = _capture_document(
        request=race_list_request,
        transport=transport,
        clock=clock,
        requested_name="race_list_requested_at",
        observed_name="race_list_observed_at",
        captured_name="race_list_captured_at",
    )
    return NARRaceEntryStatusRawCaptureBundle(
        target_race_identity=canonical_target,
        deba_table_capture=deba_capture,
        race_list_capture=race_list_capture,
    )


__all__ = (
    "NARRaceEntryStatusDayScope",
    "NARRaceEntryStatusPageKind",
    "NARRaceEntryStatusRaceIdentity",
    "NARRaceEntryStatusRawCaptureBundle",
    "NARRaceEntryStatusRawCaptureBundleIntegrityError",
    "NARRaceEntryStatusRawCaptureClock",
    "NARRaceEntryStatusRawCaptureError",
    "NARRaceEntryStatusRawCaptureTransport",
    "NARRaceEntryStatusRawCaptureTransportError",
    "NARRaceEntryStatusRawCaptureUnsupportedResponseError",
    "NARRaceEntryStatusRawCaptureValidationError",
    "NARRaceEntryStatusRawHTTPResponse",
    "NARRaceEntryStatusRequestIdentity",
    "NARRaceEntryStatusResponseCapture",
    "RequestsNARRaceEntryStatusRawCaptureTransport",
    "acquire_nar_race_entry_status_raw_capture_bundle",
    "build_nar_race_entry_status_request_identity",
)
