"""Immutable captures for NAR historical daily-target source evidence."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass, field as _field
from datetime import date as _date, datetime as _datetime, timezone as _timezone
from enum import StrEnum as _StrEnum
from html import unescape as _html_unescape
import hashlib as _hashlib
import json as _json
import re as _re
from typing import Protocol as _Protocol
from urllib.parse import urlsplit as _urlsplit


_OFFICIAL_ORIGIN = "https://www.keiba.go.jp"
_MONTHLY_PATH = "/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop"
_RACE_LIST_PATH = "/KeibaWeb/TodayRaceInfo/RaceList"
_MONTHLY_RAW = _re.compile(
    rb"/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop\?k_year=([0-9]{4})&k_month=([1-9]|1[0-2])\Z"
)
_RACE_LIST_RAW = _re.compile(
    rb"/KeibaWeb/TodayRaceInfo/RaceList\?k_raceDate=([0-9]{4})%2F([0-9]{2})%2F([0-9]{2})&amp;k_babaCode=([1-9][0-9]*)\Z"
)
_SHA256 = _re.compile(r"[0-9a-f]{64}\Z")


class NARHistoricalDailyTargetPageKind(_StrEnum):
    MONTHLY_CONVENE_INFO = "monthly_convene_info"
    RACE_LIST = "race_list"


class NARHistoricalDailyTargetCaptureError(Exception):
    """Base error for exact NAR daily-target capture operations."""


class NARHistoricalDailyTargetCaptureValidationError(NARHistoricalDailyTargetCaptureError):
    """Raised when supplied capture input is malformed or contradictory."""


class NARHistoricalDailyTargetCaptureUnsupportedError(NARHistoricalDailyTargetCaptureError):
    """Raised for a recognizable request/response outside the approved profile."""


class NARHistoricalDailyTargetCaptureMissingError(NARHistoricalDailyTargetCaptureError):
    """Raised when an exact capture identity is absent."""


def _validation(message: str) -> NARHistoricalDailyTargetCaptureValidationError:
    return NARHistoricalDailyTargetCaptureValidationError(message)


def _text(value: object, name: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise _validation(f"{name} must be an exact non-empty str without surrounding whitespace")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise _validation(f"{name} must not contain control characters")
    return value


def _utc(value: object, name: str) -> _datetime:
    if type(value) is not _datetime:
        raise _validation(f"{name} must be exact datetime")
    try:
        if value.tzinfo is None or value.utcoffset() is None:
            raise _validation(f"{name} must be timezone-aware")
        return value.astimezone(_timezone.utc)
    except NARHistoricalDailyTargetCaptureValidationError:
        raise
    except (OverflowError, TypeError, ValueError) as error:
        raise _validation(f"{name} cannot be converted to UTC") from error


def _datetime_text(value: _datetime) -> str:
    return value.astimezone(_timezone.utc).isoformat(timespec="microseconds")


def _header(value: object, name: str) -> str | None:
    if value is None:
        return None
    value = _text(value, name)
    return value


def _canonical_bytes(payload: dict[str, object]) -> bytes:
    return _json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


@_dataclass(frozen=True, slots=True)
class NARHistoricalDailyTargetRequestIdentity:
    page_kind: NARHistoricalDailyTargetPageKind
    official_supplied_request_material: bytes
    resolved_request_url: str
    supplier_evidence_identity: str
    schema_version: int = _field(init=False, default=1)
    method: str = _field(init=False, default="GET")
    official_origin: str = _field(init=False, default=_OFFICIAL_ORIGIN)
    request_identity_sha256: str = _field(init=False)
    request_identity: str = _field(init=False)
    target_date: _date | None = _field(init=False)
    baba_code: str | None = _field(init=False)
    target_year: int = _field(init=False)
    target_month: int = _field(init=False)

    def __post_init__(self) -> None:
        if type(self.page_kind) is not NARHistoricalDailyTargetPageKind:
            raise _validation("page_kind must be NARHistoricalDailyTargetPageKind")
        if type(self.official_supplied_request_material) is not bytes or not self.official_supplied_request_material:
            raise _validation("official_supplied_request_material must be non-empty exact bytes")
        try:
            raw_text = self.official_supplied_request_material.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise NARHistoricalDailyTargetCaptureUnsupportedError(
                "official supplied request material is not strict UTF-8"
            ) from error
        if any(character.isspace() or ord(character) < 32 for character in raw_text):
            raise _validation("official supplied request material contains whitespace or control characters")
        resolved = _text(self.resolved_request_url, "resolved_request_url")
        supplier = _text(self.supplier_evidence_identity, "supplier_evidence_identity")
        try:
            parsed = _urlsplit(resolved)
            port = parsed.port
        except ValueError as error:
            raise _validation("resolved_request_url is invalid") from error
        if (
            parsed.scheme != "https"
            or parsed.hostname != "www.keiba.go.jp"
            or port not in (None, 443)
            or parsed.username is not None
            or parsed.password is not None
            or parsed.fragment
        ):
            raise _validation("resolved_request_url must use the exact official origin")
        target_date: _date | None
        baba_code: str | None
        if self.page_kind is NARHistoricalDailyTargetPageKind.MONTHLY_CONVENE_INFO:
            match = _MONTHLY_RAW.fullmatch(self.official_supplied_request_material)
            if match is None:
                raise NARHistoricalDailyTargetCaptureUnsupportedError(
                    "MonthlyConveneInfo supplied locator grammar is unsupported"
                )
            year, month = int(match.group(1)), int(match.group(2))
            expected = _OFFICIAL_ORIGIN + raw_text
            target_date = None
            baba_code = None
        else:
            match = _RACE_LIST_RAW.fullmatch(self.official_supplied_request_material)
            if match is None:
                raise NARHistoricalDailyTargetCaptureUnsupportedError("RaceList raw href grammar is unsupported")
            year, month, day = (int(match.group(index)) for index in (1, 2, 3))
            try:
                target_date = _date(year, month, day)
            except ValueError as error:
                raise _validation("RaceList raw href target date is invalid") from error
            baba_code = match.group(4).decode("ascii")
            expected = _OFFICIAL_ORIGIN + _html_unescape(raw_text)
        if resolved != expected:
            raise _validation("resolved_request_url does not exactly resolve supplied request material")
        expected_path = _MONTHLY_PATH if self.page_kind is NARHistoricalDailyTargetPageKind.MONTHLY_CONVENE_INFO else _RACE_LIST_PATH
        if parsed.path != expected_path:
            raise _validation("resolved_request_url path contradicts page_kind")
        payload = {
            "method": "GET",
            "official_origin": _OFFICIAL_ORIGIN,
            "official_supplied_request_material_utf8_hex": self.official_supplied_request_material.hex(),
            "page_kind": self.page_kind.value,
            "resolved_request_url": resolved,
            "schema_version": 1,
            "supplier_evidence_identity": supplier,
        }
        digest = _hashlib.sha256(_canonical_bytes(payload)).hexdigest()
        object.__setattr__(self, "resolved_request_url", resolved)
        object.__setattr__(self, "supplier_evidence_identity", supplier)
        object.__setattr__(self, "request_identity_sha256", digest)
        object.__setattr__(self, "request_identity", f"nar-daily-target-request-v1:{digest}")
        object.__setattr__(self, "target_date", target_date)
        object.__setattr__(self, "baba_code", baba_code)
        object.__setattr__(self, "target_year", year)
        object.__setattr__(self, "target_month", month)


@_dataclass(frozen=True, slots=True)
class NARHistoricalDailyTargetResponseCapture:
    request_identity: NARHistoricalDailyTargetRequestIdentity
    response_body: bytes
    charset: str
    requested_at: _datetime
    observed_at: _datetime
    stored_at: _datetime
    http_status: int
    content_type: str | None = None
    content_encoding: str | None = None
    http_date: str | None = None
    etag: str | None = None
    last_modified: str | None = None
    content_length: int | None = None
    schema_version: int = _field(init=False, default=1)
    response_sha256: str = _field(init=False)
    capture_id: str = _field(init=False)

    def __post_init__(self) -> None:
        if type(self.request_identity) is not NARHistoricalDailyTargetRequestIdentity:
            raise _validation("request_identity must be NARHistoricalDailyTargetRequestIdentity")
        if type(self.response_body) is not bytes or not self.response_body:
            raise _validation("response_body must be non-empty exact bytes")
        try:
            self.response_body.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise NARHistoricalDailyTargetCaptureUnsupportedError("response_body is not strict UTF-8") from error
        if self.charset != "utf-8" or type(self.charset) is not str:
            raise _validation("charset must be exact utf-8")
        if type(self.http_status) is not int or self.http_status != 200:
            raise _validation("http_status must be exact int 200")
        if self.content_encoding not in (None, "identity"):
            if type(self.content_encoding) is str:
                raise NARHistoricalDailyTargetCaptureUnsupportedError("content_encoding is unsupported")
            raise _validation("content_encoding must be str or None")
        for name in ("content_type", "content_encoding", "http_date", "etag", "last_modified"):
            _header(getattr(self, name), name)
        if self.content_length is not None and (
            type(self.content_length) is not int
            or self.content_length < 0
            or self.content_length != len(self.response_body)
        ):
            raise _validation("content_length must match response_body length")
        requested = _utc(self.requested_at, "requested_at")
        observed = _utc(self.observed_at, "observed_at")
        stored = _utc(self.stored_at, "stored_at")
        if not requested <= observed <= stored:
            raise _validation("requested_at, observed_at, and stored_at are out of order")
        response_digest = _hashlib.sha256(self.response_body).hexdigest()
        payload = {
            "observed_at_utc": _datetime_text(observed),
            "page_kind": self.request_identity.page_kind.value,
            "request_identity_sha256": self.request_identity.request_identity_sha256,
            "response_sha256": response_digest,
            "schema_version": 1,
        }
        capture_digest = _hashlib.sha256(_canonical_bytes(payload)).hexdigest()
        object.__setattr__(self, "requested_at", requested)
        object.__setattr__(self, "observed_at", observed)
        object.__setattr__(self, "stored_at", stored)
        object.__setattr__(self, "response_sha256", response_digest)
        object.__setattr__(self, "capture_id", f"nar-daily-target-capture-v1:{capture_digest}")


class NARHistoricalDailyTargetCaptureSource(_Protocol):
    def load_capture(self, *, capture_id: str) -> NARHistoricalDailyTargetResponseCapture | None: ...


class NARHistoricalDailyTargetCaptureArchive(NARHistoricalDailyTargetCaptureSource, _Protocol):
    def save_capture(self, *, capture: NARHistoricalDailyTargetResponseCapture) -> None: ...


if "annotations" in globals():
    del annotations
