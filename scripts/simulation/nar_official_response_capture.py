"""Immutable, supplied-byte NAR official-response capture domain."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass, field as _field
from datetime import date as _date, datetime as _datetime, timezone as _timezone
from enum import StrEnum as _StrEnum
import hashlib as _hashlib
import json as _json
import re as _re
from typing import Protocol as _Protocol
from unicodedata import normalize as _normalize
from urllib.parse import parse_qsl as _parse_qsl, urlsplit as _urlsplit

from scripts.simulation.nar_historical_input_source import (
    NarSuppliedOfficialResponse as _NarSuppliedOfficialResponse,
)


class NAROfficialPageKind(_StrEnum):
    """The closed initial official NAR capture vocabulary."""

    DEBA_TABLE = "deba_table"
    HORSE_MARK_INFO = "horse_mark_info"
    RACE_MARK_TABLE = "race_mark_table"


class NAROfficialResponseCaptureError(Exception):
    """Base error for the trusted NAR capture boundary."""


class NAROfficialResponseCaptureValidationError(NAROfficialResponseCaptureError):
    """Raised when capture-domain input is malformed or contradictory."""


class NAROfficialResponseCaptureUnsupportedError(NAROfficialResponseCaptureError):
    """Raised for a recognizable official state outside initial capture support."""


class NAROfficialResponseCaptureMissingError(NAROfficialResponseCaptureError):
    """Raised when an exact trusted archive evidence tuple is absent."""


_OFFICIAL_HOST = "www.keiba.go.jp"
_HORSE_HOSTS = frozenset({_OFFICIAL_HOST, "www2.keiba.go.jp"})
_RACE_PATHS = {
    "/KeibaWeb/TodayRaceInfo/DebaTable": NAROfficialPageKind.DEBA_TABLE,
    "/KeibaWeb/TodayRaceInfo/RaceMarkTable": NAROfficialPageKind.RACE_MARK_TABLE,
}
_HORSE_PATH = "/KeibaWeb/DataRoom/HorseMarkInfo"
_RACE_KEYS = frozenset({"k_babaCode", "k_raceDate", "k_raceNo"})
_HORSE_KEY = "k_lineageLoginCode"
_POSITIVE_TOKEN = _re.compile(r"[1-9][0-9]*\Z")
_RACE_DATE = _re.compile(r"[0-9]{4}/[0-9]{2}/[0-9]{2}\Z")
_SHA256 = _re.compile(r"[0-9a-f]{64}\Z")
_PERCENT = _re.compile(r"%(?:[0-9A-Fa-f]{2})")


def _validation(message: str) -> NAROfficialResponseCaptureValidationError:
    return NAROfficialResponseCaptureValidationError(message)


def _bad_percent_encoding(value: str) -> bool:
    return any(value[index] == "%" and _PERCENT.match(value, index) is None for index in range(len(value)))


def _positive_token(value: object, name: str) -> str:
    if type(value) is not str or _POSITIVE_TOKEN.fullmatch(value) is None:
        raise _validation(f"{name} must be a positive canonical ASCII decimal token")
    return value


def _canonical_datetime(value: object, name: str) -> _datetime:
    if type(value) is not _datetime:
        raise _validation(f"{name} must be exact datetime")
    try:
        if value.tzinfo is None or value.utcoffset() is None:
            raise _validation(f"{name} must be timezone-aware")
        return value.astimezone(_timezone.utc)
    except NAROfficialResponseCaptureValidationError:
        raise
    except (OverflowError, TypeError, ValueError) as error:
        raise _validation(f"{name} cannot be converted to UTC") from error


def _datetime_text(value: _datetime) -> str:
    return value.astimezone(_timezone.utc).isoformat(timespec="microseconds")


def _header_text(value: object, name: str) -> str | None:
    if value is None:
        return None
    if type(value) is not str:
        raise _validation(f"{name} must be str or None")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise _validation(f"{name} must not contain control characters")
    return value


def canonicalize_nar_official_capture_url(
    response_url: str,
) -> tuple[NAROfficialPageKind, str]:
    """Validate a closed official NAR URL and return its deterministic identity."""

    if type(response_url) is not str or not response_url:
        raise _validation("response_url must be a non-empty str")
    if response_url != _normalize("NFC", response_url) or response_url != response_url.strip():
        raise _validation("response_url must be NFC-normalized without surrounding whitespace")
    if any(character.isspace() or ord(character) < 32 for character in response_url):
        raise _validation("response_url contains whitespace or control characters")
    try:
        parsed = _urlsplit(response_url)
        port = parsed.port
    except ValueError as error:
        raise _validation("response_url is invalid") from error
    if parsed.scheme.lower() != "https":
        raise _validation("response_url must use https")
    if parsed.username is not None or parsed.password is not None or parsed.fragment:
        raise _validation("response_url must not contain credentials or fragment")
    host = (parsed.hostname or "").lower()
    if host not in _HORSE_HOSTS or port not in (None, 443):
        raise _validation("response_url host or port is invalid")
    if "+" in parsed.query or _bad_percent_encoding(parsed.query):
        raise _validation("response_url query encoding is ambiguous or malformed")
    if parsed.path in _RACE_PATHS:
        if host != _OFFICIAL_HOST:
            raise _validation("race response_url host is invalid")
        kind = _RACE_PATHS[parsed.path]
        required_keys = _RACE_KEYS
    elif parsed.path == _HORSE_PATH:
        kind = NAROfficialPageKind.HORSE_MARK_INFO
        required_keys = frozenset({_HORSE_KEY})
    else:
        raise NAROfficialResponseCaptureUnsupportedError("official NAR page kind is unsupported")
    if not parsed.query:
        raise _validation("response_url query is required")
    try:
        pairs = _parse_qsl(parsed.query, keep_blank_values=True, strict_parsing=True, encoding="utf-8", errors="strict")
    except ValueError as error:
        raise _validation("response_url query is invalid") from error
    values: dict[str, str] = {}
    for key, item in pairs:
        if not key or not item or key != _normalize("NFC", key) or item != _normalize("NFC", item):
            raise _validation("response_url query key or value is invalid")
        if key not in required_keys or key in values:
            raise _validation("response_url query keys are invalid")
        values[key] = item
    if set(values) != required_keys:
        raise _validation("response_url query keys are incomplete")
    if kind is NAROfficialPageKind.HORSE_MARK_INFO:
        lineage = _positive_token(values[_HORSE_KEY], _HORSE_KEY)
        return kind, f"https://{host}{_HORSE_PATH}?{_HORSE_KEY}={lineage}"
    race_date_text = values["k_raceDate"]
    if _RACE_DATE.fullmatch(race_date_text) is None:
        raise _validation("k_raceDate must be YYYY/MM/DD")
    try:
        _date.fromisoformat(race_date_text.replace("/", "-"))
    except ValueError as error:
        raise _validation("k_raceDate must be a real date") from error
    baba_code = _positive_token(values["k_babaCode"], "k_babaCode")
    race_no = _positive_token(values["k_raceNo"], "k_raceNo")
    return kind, (
        f"https://{_OFFICIAL_HOST}{parsed.path}?k_babaCode={baba_code}"
        f"&k_raceDate={race_date_text.replace('/', '%2F')}&k_raceNo={race_no}"
    )


@_dataclass(frozen=True, slots=True)
class NAROfficialResponseCapture:
    """One immutable, complete official NAR parser-input observation."""

    canonical_source_url: str
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
    capture_id: str = _field(init=False)
    page_kind: NAROfficialPageKind = _field(init=False)
    response_sha256: str = _field(init=False)

    def __post_init__(self) -> None:
        kind, canonical_url = canonicalize_nar_official_capture_url(self.canonical_source_url)
        if self.canonical_source_url != canonical_url:
            raise _validation("canonical_source_url must already be canonical")
        if type(self.response_body) is not bytes or not self.response_body:
            raise _validation("response_body must be non-empty exact bytes")
        try:
            self.response_body.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise NAROfficialResponseCaptureUnsupportedError("response_body is not strict UTF-8") from error
        if type(self.charset) is not str or self.charset != "utf-8":
            raise _validation("charset must be exact utf-8")
        if self.content_encoding not in (None, "identity"):
            if type(self.content_encoding) is str:
                raise NAROfficialResponseCaptureUnsupportedError("content_encoding is unsupported")
            raise _validation("content_encoding must be str or None")
        if type(self.http_status) is not int or self.http_status != 200:
            raise _validation("http_status must be exact int 200")
        for value, name in (
            (self.content_type, "content_type"), (self.content_encoding, "content_encoding"),
            (self.http_date, "http_date"), (self.etag, "etag"), (self.last_modified, "last_modified"),
        ):
            _header_text(value, name)
        if self.content_length is not None:
            if type(self.content_length) is not int or self.content_length < 0 or self.content_length != len(self.response_body):
                raise _validation("content_length must match response_body length")
        requested = _canonical_datetime(self.requested_at, "requested_at")
        observed = _canonical_datetime(self.observed_at, "observed_at")
        stored = _canonical_datetime(self.stored_at, "stored_at")
        if not requested <= observed <= stored:
            raise _validation("requested_at, observed_at, and stored_at are out of order")
        digest = _hashlib.sha256(self.response_body).hexdigest()
        material = {
            "canonical_source_url": canonical_url,
            "observed_at_utc": _datetime_text(observed),
            "page_kind": kind.value,
            "response_sha256": digest,
            "schema_version": 1,
        }
        capture_id = "nar-capture-v1:" + _hashlib.sha256(
            _json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"),
        ).hexdigest()
        object.__setattr__(self, "canonical_source_url", canonical_url)
        object.__setattr__(self, "requested_at", requested)
        object.__setattr__(self, "observed_at", observed)
        object.__setattr__(self, "stored_at", stored)
        object.__setattr__(self, "page_kind", kind)
        object.__setattr__(self, "response_sha256", digest)
        object.__setattr__(self, "capture_id", capture_id)

    def to_supplied_official_response(self) -> _NarSuppliedOfficialResponse:
        """Reconstruct the existing supplied-response value without transforming bytes."""

        return _NarSuppliedOfficialResponse(
            response_url=self.canonical_source_url,
            response_body=self.response_body,
            charset="utf-8",
            observed_at=self.observed_at,
        )


class NAROfficialResponseCaptureArchive(_Protocol):
    """The intentionally small append-only trusted capture archive boundary."""

    def save_capture(self, *, capture: NAROfficialResponseCapture) -> None: ...

    def load_capture(self, *, capture_id: str) -> NAROfficialResponseCapture | None: ...

    def load_supplied_response_for_evidence(
        self, *, canonical_source_url: str, response_sha256: str, observed_at: _datetime,
    ) -> _NarSuppliedOfficialResponse: ...


if "annotations" in globals():
    del annotations
