"""Immutable supplied-byte capture domain for official JRA responses."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass, field as _field
from datetime import datetime as _datetime, timezone as _timezone
from enum import StrEnum as _StrEnum
import hashlib as _hashlib
import json as _json
import re as _re
from typing import Protocol as _Protocol
from urllib.parse import urlsplit as _urlsplit

from scripts.simulation.jra_official_identity import (
    JRAOfficialFinalWinOddsRequestLocator as _FinalLocator,
    JRAOfficialIdentityValidationError as _IdentityValidationError,
    parse_jra_horse_profile_url_identity as _parse_profile,
    parse_jra_race_card_url_identity as _parse_card,
    parse_jra_result_url_identity as _parse_result,
)


class JRAOfficialPageKind(_StrEnum):
    RACE_RESULT = "race_result"
    HORSE_PROFILE_HISTORY = "horse_profile_history"
    FINAL_WIN_ODDS = "final_win_odds"
    TARGET_RACE_CARD = "target_race_card"


class JRAOfficialResponseCaptureError(Exception):
    """Base error for the JRA trusted-capture boundary."""


class JRAOfficialResponseCaptureValidationError(JRAOfficialResponseCaptureError):
    """Raised for malformed or contradictory capture input."""


class JRAOfficialResponseCaptureUnsupportedError(JRAOfficialResponseCaptureError):
    """Raised for a recognized unsupported response representation."""


class JRAOfficialResponseCaptureMissingError(JRAOfficialResponseCaptureError):
    """Raised when an exact archived JRA evidence tuple is absent."""


_SHA = _re.compile(r"[0-9a-f]{64}\Z")
_CONTROL = _re.compile(r"[\x00-\x1f\x7f]")
_UTC = _timezone.utc


def _validation(message: str) -> JRAOfficialResponseCaptureValidationError:
    return JRAOfficialResponseCaptureValidationError(message)


def _utc(value: object, name: str) -> _datetime:
    if type(value) is not _datetime:
        raise _validation(f"{name} must be exact datetime")
    try:
        if value.tzinfo is None or value.utcoffset() is None:
            raise _validation(f"{name} must be aware")
        return value.astimezone(_UTC)
    except JRAOfficialResponseCaptureValidationError:
        raise
    except (TypeError, ValueError, OverflowError) as error:
        raise _validation(f"{name} is invalid") from error


def _datetime_text(value: _datetime) -> str:
    return value.astimezone(_UTC).isoformat(timespec="microseconds")


def _strict_cp932(body: object) -> bytes:
    if type(body) is not bytes or not body:
        raise _validation("response_body must be non-empty exact bytes")
    try:
        body.decode("cp932", errors="strict")
    except UnicodeDecodeError as error:
        raise JRAOfficialResponseCaptureUnsupportedError("response_body is not strict cp932") from error
    return body


def _page_for_url(value: str) -> JRAOfficialPageKind:
    try:
        _parse_result(value)
        return JRAOfficialPageKind.RACE_RESULT
    except _IdentityValidationError:
        try:
            _parse_profile(value)
            return JRAOfficialPageKind.HORSE_PROFILE_HISTORY
        except _IdentityValidationError as error:
            raise _validation("response_url is not a supported JRA capture URL") from error


def _supplied_page_for_url(value: str) -> JRAOfficialPageKind:
    """Recognize supplied GET evidence without widening the v1 capture family."""

    try:
        return _page_for_url(value)
    except JRAOfficialResponseCaptureValidationError:
        try:
            _parse_card(value)
            return JRAOfficialPageKind.TARGET_RACE_CARD
        except _IdentityValidationError as error:
            raise _validation("response_url is not a supported JRA supplied URL") from error


def canonicalize_jra_official_capture_url(*, page_kind: JRAOfficialPageKind, response_url: str) -> str:
    """Validate one approved resolved JRA URL and canonicalize only its delimiter."""

    if type(page_kind) is not JRAOfficialPageKind or type(response_url) is not str:
        raise _validation("page_kind and response_url are invalid")
    try:
        if page_kind is JRAOfficialPageKind.RACE_RESULT:
            _parse_result(response_url)
            path = "/JRADB/accessS.html"
        elif page_kind is JRAOfficialPageKind.HORSE_PROFILE_HISTORY:
            _parse_profile(response_url)
            path = "/JRADB/accessU.html"
        else:
            raise _validation("final win odds is a POST-only capture family")
    except _IdentityValidationError as error:
        raise _validation("response_url does not match page_kind") from error
    parsed = _urlsplit(response_url)
    raw = parsed.query.split("=", 1)[1]
    cname = raw.replace("%2F", "/")
    if cname.count("/") != 1:
        raise _validation("response_url CNAME delimiter is invalid")
    return f"https://www.jra.go.jp{path}?CNAME={cname.replace('/', '%2F')}"


def _canonical_target_race_card_url(value: object, name: str) -> str:
    if type(value) is not str:
        raise _validation(f"{name} must be exact str")
    try:
        _parse_card(value)
    except _IdentityValidationError as error:
        raise _validation(f"{name} is not an approved accessD URL") from error
    parsed = _urlsplit(value)
    raw = parsed.query.split("=", 1)[1]
    cname = raw.replace("%2F", "/")
    canonical = f"https://www.jra.go.jp/JRADB/accessD.html?CNAME={cname.replace('/', '%2F')}"
    if value != canonical:
        raise _validation(f"{name} must already be canonical")
    return canonical


def _canonical_supported_url(value: object, name: str) -> tuple[JRAOfficialPageKind, str]:
    if type(value) is not str:
        raise _validation(f"{name} must be exact str")
    kind = _page_for_url(value)
    canonical = canonicalize_jra_official_capture_url(page_kind=kind, response_url=value)
    if value != canonical:
        raise _validation(f"{name} must already be canonical")
    return kind, canonical


def _canonical_supplied_url(value: object, name: str) -> tuple[JRAOfficialPageKind, str]:
    if type(value) is not str:
        raise _validation(f"{name} must be exact str")
    kind = _supplied_page_for_url(value)
    if kind is JRAOfficialPageKind.TARGET_RACE_CARD:
        return kind, _canonical_target_race_card_url(value, name)
    canonical = canonicalize_jra_official_capture_url(page_kind=kind, response_url=value)
    if value != canonical:
        raise _validation(f"{name} must already be canonical")
    return kind, canonical


def _content_type(value: object) -> str:
    if type(value) is not str or _CONTROL.search(value) is not None or any(ord(c) > 127 for c in value):
        raise _validation("content_type is invalid")
    parts = [part.strip().lower() for part in value.split(";")]
    if not parts or parts[0] != "text/html":
        raise JRAOfficialResponseCaptureUnsupportedError("content_type is unsupported")
    if len(parts) == 1:
        return "text/html"
    if len(parts) != 2 or not parts[1].startswith("charset="):
        raise JRAOfficialResponseCaptureUnsupportedError("content_type parameters are unsupported")
    charset = parts[1][8:].strip().strip('"')
    if charset not in {"shift_jis", "cp932"}:
        raise JRAOfficialResponseCaptureUnsupportedError("content_type charset is unsupported")
    return f"text/html; charset={charset}"


def _header(value: object, name: str) -> str | None:
    if value is None:
        return None
    if type(value) is not str or _CONTROL.search(value) is not None:
        raise _validation(f"{name} is invalid")
    return value


@_dataclass(frozen=True, slots=True)
class JRASuppliedOfficialResponse:
    response_url: str
    response_body: bytes
    charset: str = "cp932"
    observed_at: _datetime = _field(default=None)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        _kind, canonical = _canonical_supplied_url(self.response_url, "response_url")
        body = _strict_cp932(self.response_body)
        if type(self.charset) is not str or self.charset != "cp932":
            raise _validation("charset must be exact cp932")
        object.__setattr__(self, "response_url", canonical)
        object.__setattr__(self, "response_body", body)
        object.__setattr__(self, "observed_at", _utc(self.observed_at, "observed_at"))


@_dataclass(frozen=True, slots=True)
class JRAFinalWinOddsSuppliedOfficialResponse:
    """Exact supplied POST response for one final-win-odds request locator."""

    request_locator: _FinalLocator
    response_body: bytes
    charset: str = "cp932"
    observed_at: _datetime = _field(default=None)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if type(self.request_locator) is not _FinalLocator:
            raise _validation("request_locator must be exact JRAOfficialFinalWinOddsRequestLocator")
        object.__setattr__(self, "response_body", _strict_cp932(self.response_body))
        if type(self.charset) is not str or self.charset != "cp932":
            raise _validation("charset must be exact cp932")
        object.__setattr__(self, "observed_at", _utc(self.observed_at, "observed_at"))


@_dataclass(frozen=True, slots=True)
class JRAOfficialResponseCapture:
    canonical_source_url: str
    response_body: bytes
    charset: str
    requested_at: _datetime
    observed_at: _datetime
    stored_at: _datetime
    http_status: int
    content_type: str
    content_encoding: str | None = None
    http_date: str | None = None
    etag: str | None = None
    last_modified: str | None = None
    content_length: int | None = None
    schema_version: int = _field(init=False, default=1)
    page_kind: JRAOfficialPageKind = _field(init=False)
    response_sha256: str = _field(init=False)
    capture_id: str = _field(init=False)

    def __post_init__(self) -> None:
        kind, canonical = _canonical_supported_url(self.canonical_source_url, "canonical_source_url")
        body = _strict_cp932(self.response_body)
        if type(self.charset) is not str or self.charset != "cp932":
            raise _validation("charset must be exact cp932")
        if type(self.http_status) is not int or self.http_status != 200:
            raise _validation("http_status must be exact int 200")
        content_type = _content_type(self.content_type)
        if self.content_encoding not in (None, "identity"):
            if type(self.content_encoding) is str:
                raise JRAOfficialResponseCaptureUnsupportedError("content_encoding is unsupported")
            raise _validation("content_encoding is invalid")
        for value, name in ((self.http_date, "http_date"), (self.etag, "etag"), (self.last_modified, "last_modified")):
            _header(value, name)
        if self.content_length is not None and (type(self.content_length) is not int or self.content_length < 0 or self.content_length != len(body)):
            raise _validation("content_length must exactly match response_body")
        requested, observed, stored = (_utc(self.requested_at, "requested_at"), _utc(self.observed_at, "observed_at"), _utc(self.stored_at, "stored_at"))
        if not requested <= observed <= stored:
            raise _validation("capture timestamps are out of order")
        digest = _hashlib.sha256(body).hexdigest()
        material = {"canonical_source_url": canonical, "observed_at_utc": _datetime_text(observed), "page_kind": kind.value, "response_sha256": digest, "schema_version": 1}
        capture_id = "jra-capture-v1:" + _hashlib.sha256(_json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()
        for name, value in (("canonical_source_url", canonical), ("response_body", body), ("content_type", content_type), ("requested_at", requested), ("observed_at", observed), ("stored_at", stored), ("page_kind", kind), ("response_sha256", digest), ("capture_id", capture_id)):
            object.__setattr__(self, name, value)

    def to_supplied_official_response(self) -> JRASuppliedOfficialResponse:
        return JRASuppliedOfficialResponse(response_url=self.canonical_source_url, response_body=self.response_body, charset="cp932", observed_at=self.observed_at)


@_dataclass(frozen=True, slots=True)
class JRAFinalWinOddsResponseCapture:
    """Immutable trusted final-win-odds POST capture."""

    request_locator: _FinalLocator
    response_body: bytes
    charset: str
    requested_at: _datetime
    observed_at: _datetime
    stored_at: _datetime
    http_status: int
    content_type: str
    content_encoding: str | None = None
    http_date: str | None = None
    etag: str | None = None
    last_modified: str | None = None
    content_length: int | None = None
    schema_version: int = _field(init=False, default=2)
    page_kind: JRAOfficialPageKind = _field(init=False, default=JRAOfficialPageKind.FINAL_WIN_ODDS)
    request_method: str = _field(init=False, default="POST")
    response_sha256: str = _field(init=False)
    capture_id: str = _field(init=False)

    def __post_init__(self) -> None:
        if type(self.request_locator) is not _FinalLocator:
            raise _validation("request_locator must be exact JRAOfficialFinalWinOddsRequestLocator")
        body = _strict_cp932(self.response_body)
        if type(self.charset) is not str or self.charset != "cp932":
            raise _validation("charset must be exact cp932")
        if type(self.http_status) is not int or self.http_status != 200:
            raise _validation("http_status must be exact int 200")
        content_type = _content_type(self.content_type)
        if self.content_encoding not in (None, "identity"):
            if type(self.content_encoding) is str:
                raise JRAOfficialResponseCaptureUnsupportedError("content_encoding is unsupported")
            raise _validation("content_encoding is invalid")
        for value, name in ((self.http_date, "http_date"), (self.etag, "etag"), (self.last_modified, "last_modified")):
            _header(value, name)
        if self.content_length is not None and (type(self.content_length) is not int or self.content_length < 0 or self.content_length != len(body)):
            raise _validation("content_length must exactly match response_body")
        requested, observed, stored = (_utc(self.requested_at, "requested_at"), _utc(self.observed_at, "observed_at"), _utc(self.stored_at, "stored_at"))
        if not requested <= observed <= stored:
            raise _validation("capture timestamps are out of order")
        digest = _hashlib.sha256(body).hexdigest()
        material = {
            "canonical_source_url": self.request_locator.endpoint_url,
            "observed_at_utc": _datetime_text(observed),
            "page_kind": JRAOfficialPageKind.FINAL_WIN_ODDS.value,
            "request_identity_sha256": self.request_locator.request_identity_sha256,
            "request_method": "POST",
            "response_sha256": digest,
            "schema_version": 2,
        }
        capture_id = "jra-capture-v2:" + _hashlib.sha256(
            _json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        for name, value in (("response_body", body), ("content_type", content_type), ("requested_at", requested), ("observed_at", observed), ("stored_at", stored), ("response_sha256", digest), ("capture_id", capture_id)):
            object.__setattr__(self, name, value)

    @property
    def canonical_source_url(self) -> str:
        return self.request_locator.endpoint_url

    def to_supplied_official_response(self) -> JRAFinalWinOddsSuppliedOfficialResponse:
        return JRAFinalWinOddsSuppliedOfficialResponse(request_locator=self.request_locator, response_body=self.response_body, charset="cp932", observed_at=self.observed_at)


@_dataclass(frozen=True, slots=True)
class JRAOfficialTargetRaceCardResponseCapture:
    """Immutable schema-v3 GET capture for an official accessD target card."""

    canonical_source_url: str
    response_body: bytes
    charset: str
    requested_at: _datetime
    observed_at: _datetime
    stored_at: _datetime
    http_status: int
    content_type: str
    content_encoding: str | None = None
    http_date: str | None = None
    etag: str | None = None
    last_modified: str | None = None
    content_length: int | None = None
    schema_version: int = _field(init=False, default=3)
    page_kind: JRAOfficialPageKind = _field(init=False, default=JRAOfficialPageKind.TARGET_RACE_CARD)
    request_method: str = _field(init=False, default="GET")
    response_sha256: str = _field(init=False)
    capture_id: str = _field(init=False)

    def __post_init__(self) -> None:
        canonical = _canonical_target_race_card_url(self.canonical_source_url, "canonical_source_url")
        body = _strict_cp932(self.response_body)
        if type(self.charset) is not str or self.charset != "cp932":
            raise _validation("charset must be exact cp932")
        if type(self.http_status) is not int or self.http_status != 200:
            raise _validation("http_status must be exact int 200")
        content_type = _content_type(self.content_type)
        if self.content_encoding not in (None, "identity"):
            if type(self.content_encoding) is str:
                raise JRAOfficialResponseCaptureUnsupportedError("content_encoding is unsupported")
            raise _validation("content_encoding is invalid")
        for value, name in ((self.http_date, "http_date"), (self.etag, "etag"), (self.last_modified, "last_modified")):
            _header(value, name)
        if self.content_length is not None and (type(self.content_length) is not int or self.content_length < 0 or self.content_length != len(body)):
            raise _validation("content_length must exactly match response_body")
        requested, observed, stored = (_utc(self.requested_at, "requested_at"), _utc(self.observed_at, "observed_at"), _utc(self.stored_at, "stored_at"))
        if not requested <= observed <= stored:
            raise _validation("capture timestamps are out of order")
        digest = _hashlib.sha256(body).hexdigest()
        material = {"canonical_source_url": canonical, "observed_at_utc": _datetime_text(observed), "page_kind": JRAOfficialPageKind.TARGET_RACE_CARD.value, "response_sha256": digest, "schema_version": 3}
        capture_id = "jra-capture-v3:" + _hashlib.sha256(_json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()
        for name, value in (("canonical_source_url", canonical), ("response_body", body), ("content_type", content_type), ("requested_at", requested), ("observed_at", observed), ("stored_at", stored), ("response_sha256", digest), ("capture_id", capture_id)):
            object.__setattr__(self, name, value)

    def to_supplied_official_response(self) -> JRASuppliedOfficialResponse:
        return JRASuppliedOfficialResponse(response_url=self.canonical_source_url, response_body=self.response_body, charset="cp932", observed_at=self.observed_at)


class JRAOfficialResponseCaptureArchive(_Protocol):
    def save_capture(self, *, capture: JRAOfficialResponseCapture) -> None: ...
    def load_capture(self, *, capture_id: str) -> JRAOfficialResponseCapture | None: ...
    def load_supplied_response_for_evidence(self, *, canonical_source_url: str, response_sha256: str, observed_at: _datetime) -> JRASuppliedOfficialResponse: ...
    def save_final_win_odds_capture(self, *, capture: JRAFinalWinOddsResponseCapture) -> None: ...
    def load_final_win_odds_capture(self, *, capture_id: str) -> JRAFinalWinOddsResponseCapture | None: ...
    def load_final_win_odds_supplied_response_for_evidence(self, *, canonical_source_url: str, request_identity_sha256: str, response_sha256: str, observed_at: _datetime) -> JRAFinalWinOddsSuppliedOfficialResponse: ...
    def save_target_race_card_capture(self, *, capture: JRAOfficialTargetRaceCardResponseCapture) -> None: ...
    def load_target_race_card_capture(self, *, capture_id: str) -> JRAOfficialTargetRaceCardResponseCapture | None: ...
    def load_target_race_card_supplied_response_for_evidence(self, *, canonical_source_url: str, response_sha256: str, observed_at: _datetime) -> JRASuppliedOfficialResponse: ...


if "annotations" in globals():
    del annotations
