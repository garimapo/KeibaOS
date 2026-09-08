"""Immutable supplied captures for the NAR MonthlyConveneInfo bootstrap."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass, field as _field
from datetime import datetime as _datetime, timezone as _timezone
from enum import StrEnum as _StrEnum
import hashlib as _hashlib
import json as _json


class NARMonthlyConveneInfoBootstrapPageKind(_StrEnum):
    OFFICIAL_HOME = "official_home"
    MONTHLY_ROOT = "monthly_root"
    LOCATOR_SCRIPT = "locator_script"


class NARMonthlyConveneInfoBootstrapCaptureError(Exception):
    """Base error for immutable bootstrap supplier captures."""


class NARMonthlyConveneInfoBootstrapCaptureValidationError(
    NARMonthlyConveneInfoBootstrapCaptureError
):
    """Raised when supplied capture material is invalid."""


class NARMonthlyConveneInfoBootstrapCaptureUnsupportedError(
    NARMonthlyConveneInfoBootstrapCaptureError
):
    """Raised when supplied official material is outside the qualified profile."""


_URLS = {
    NARMonthlyConveneInfoBootstrapPageKind.OFFICIAL_HOME: "https://www.keiba.go.jp/",
    NARMonthlyConveneInfoBootstrapPageKind.MONTHLY_ROOT: (
        "https://www.keiba.go.jp/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop"
    ),
    NARMonthlyConveneInfoBootstrapPageKind.LOCATOR_SCRIPT: (
        "https://www.keiba.go.jp/KeibaWeb/resources/js/"
        "monthltconveninfo.js?t=20260130_1"
    ),
}
_CONTENT_TYPES = {
    NARMonthlyConveneInfoBootstrapPageKind.OFFICIAL_HOME: "text/html",
    NARMonthlyConveneInfoBootstrapPageKind.MONTHLY_ROOT: "text/html; charset=UTF-8",
    NARMonthlyConveneInfoBootstrapPageKind.LOCATOR_SCRIPT: (
        "application/javascript; charset=UTF-8"
    ),
}


def _validation(message: str) -> NARMonthlyConveneInfoBootstrapCaptureValidationError:
    return NARMonthlyConveneInfoBootstrapCaptureValidationError(message)


def _utc(value: object, name: str) -> _datetime:
    if type(value) is not _datetime:
        raise _validation(f"{name} must be exact datetime")
    try:
        if value.tzinfo is None or value.utcoffset() is None:
            raise _validation(f"{name} must be timezone-aware")
        return value.astimezone(_timezone.utc)
    except NARMonthlyConveneInfoBootstrapCaptureValidationError:
        raise
    except (OverflowError, TypeError, ValueError) as error:
        raise _validation(f"{name} cannot be converted to UTC") from error


def _datetime_text(value: _datetime) -> str:
    return value.astimezone(_timezone.utc).isoformat(timespec="microseconds")


def _canonical_bytes(payload: dict[str, object]) -> bytes:
    return _json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


@_dataclass(frozen=True, slots=True)
class NARMonthlyConveneInfoBootstrapSupplierCapture:
    page_kind: NARMonthlyConveneInfoBootstrapPageKind
    canonical_request_url: str
    effective_url: str
    response_body: bytes
    charset: str
    requested_at: _datetime
    observed_at: _datetime
    stored_at: _datetime
    http_status: int
    content_type: str
    content_encoding: str | None = None
    content_length: int | None = None
    schema_version: int = _field(init=False, default=1)
    response_sha256: str = _field(init=False)
    capture_id: str = _field(init=False)

    def __post_init__(self) -> None:
        if type(self.page_kind) is not NARMonthlyConveneInfoBootstrapPageKind:
            raise _validation("page_kind must be NARMonthlyConveneInfoBootstrapPageKind")
        expected_url = _URLS[self.page_kind]
        if type(self.canonical_request_url) is not str or self.canonical_request_url != expected_url:
            raise _validation("canonical_request_url is not the exact qualified URL")
        if type(self.effective_url) is not str or self.effective_url != expected_url:
            raise _validation("effective_url differs from the exact request URL")
        if type(self.response_body) is not bytes or not self.response_body:
            raise _validation("response_body must be non-empty exact bytes")
        try:
            self.response_body.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise NARMonthlyConveneInfoBootstrapCaptureUnsupportedError(
                "response_body is not strict UTF-8"
            ) from error
        if type(self.charset) is not str or self.charset != "utf-8":
            raise _validation("charset must be exact utf-8")
        if type(self.http_status) is not int or self.http_status != 200:
            raise _validation("http_status must be exact int 200")
        expected_content_type = _CONTENT_TYPES[self.page_kind]
        if type(self.content_type) is not str or self.content_type != expected_content_type:
            raise NARMonthlyConveneInfoBootstrapCaptureUnsupportedError(
                "content_type is outside the qualified profile"
            )
        if self.content_encoding not in (None, "identity"):
            if type(self.content_encoding) is str:
                raise NARMonthlyConveneInfoBootstrapCaptureUnsupportedError(
                    "content_encoding is outside the qualified profile"
                )
            raise _validation("content_encoding must be str or None")
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
        identity_payload = {
            "canonical_request_url": expected_url,
            "observed_at_utc": _datetime_text(observed),
            "page_kind": self.page_kind.value,
            "response_sha256": response_digest,
            "schema_version": 1,
        }
        capture_digest = _hashlib.sha256(_canonical_bytes(identity_payload)).hexdigest()
        object.__setattr__(self, "canonical_request_url", expected_url)
        object.__setattr__(self, "effective_url", expected_url)
        object.__setattr__(self, "requested_at", requested)
        object.__setattr__(self, "observed_at", observed)
        object.__setattr__(self, "stored_at", stored)
        object.__setattr__(self, "response_sha256", response_digest)
        object.__setattr__(
            self,
            "capture_id",
            f"nar-monthly-bootstrap-capture-v1:{capture_digest}",
        )


if "annotations" in globals():
    del annotations
