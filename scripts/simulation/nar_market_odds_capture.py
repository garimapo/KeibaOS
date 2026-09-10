"""Immutable raw capture domain for prediction-time NAR market-odds pages."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass, field as _field
from datetime import date as _date, datetime as _datetime, timezone as _timezone
from enum import StrEnum as _StrEnum
import hashlib as _hashlib
import json as _json
import re as _re
from typing import Protocol as _Protocol


class NARMarketOddsPageKind(_StrEnum):
    ODDS_TAN_FUKU = "odds_tan_fuku"
    ODDS_UM_LEN_FUKU = "odds_um_len_fuku"
    ODDS_WIDE = "odds_wide"
    ODDS_3_LEN_FUKU = "odds_3_len_fuku"


class NARMarketOddsCaptureError(Exception):
    """Base error for the NAR market-odds raw-capture boundary."""


class NARMarketOddsCaptureValidationError(NARMarketOddsCaptureError):
    """Raised for malformed or contradictory caller input."""


class NARMarketOddsCaptureUnsupportedError(NARMarketOddsCaptureError):
    """Raised for a recognizable response profile outside Phase 32 support."""


_OFFICIAL_ORIGIN = "https://www.keiba.go.jp"
_REQUEST_PREFIX = "nar-market-odds-request-v1:"
_CAPTURE_PREFIX = "nar-market-odds-capture-v1:"
_POSITIVE_TOKEN = _re.compile(r"[1-9][0-9]*\Z")
_PATHS = {
    NARMarketOddsPageKind.ODDS_TAN_FUKU: "/KeibaWeb/TodayRaceInfo/OddsTanFuku",
    NARMarketOddsPageKind.ODDS_UM_LEN_FUKU: "/KeibaWeb/TodayRaceInfo/OddsUmLenFuku",
    NARMarketOddsPageKind.ODDS_WIDE: "/KeibaWeb/TodayRaceInfo/OddsWide",
    NARMarketOddsPageKind.ODDS_3_LEN_FUKU: "/KeibaWeb/TodayRaceInfo/Odds3LenFuku",
}


def _validation(message: str) -> NARMarketOddsCaptureValidationError:
    return NARMarketOddsCaptureValidationError(message)


def _canonical_json_bytes(payload: object) -> bytes:
    return _json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _utc_datetime(value: object, name: str) -> _datetime:
    if type(value) is not _datetime:
        raise _validation(f"{name} must be exact datetime")
    try:
        if value.tzinfo is None or value.utcoffset() is None:
            raise _validation(f"{name} must be timezone-aware")
        return value.astimezone(_timezone.utc)
    except NARMarketOddsCaptureValidationError:
        raise
    except (OverflowError, TypeError, ValueError) as error:
        raise _validation(f"{name} cannot be converted to UTC") from error


def _datetime_text(value: _datetime) -> str:
    return value.astimezone(_timezone.utc).isoformat(timespec="microseconds")


def _optional_header(value: object, name: str) -> str | None:
    if value is None:
        return None
    if type(value) is not str:
        raise _validation(f"{name} must be exact str or None")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise _validation(f"{name} must not contain control characters")
    return value


@_dataclass(frozen=True, slots=True)
class NARMarketOddsRaceIdentity:
    baba_code: str
    race_date: _date
    race_no: int

    def __post_init__(self) -> None:
        if type(self.baba_code) is not str or _POSITIVE_TOKEN.fullmatch(self.baba_code) is None:
            raise _validation("baba_code must be a positive canonical ASCII decimal token")
        if type(self.race_date) is not _date:
            raise _validation("race_date must be exact date")
        if type(self.race_no) is not int or self.race_no <= 0:
            raise _validation("race_no must be an exact positive int")


@_dataclass(frozen=True, slots=True)
class NARMarketOddsRequestIdentity:
    page_kind: NARMarketOddsPageKind
    race_identity: NARMarketOddsRaceIdentity
    schema_version: int = _field(init=False, default=1)
    organization: str = _field(init=False, default="NAR")
    source_system: str = _field(init=False, default="keiba.go.jp")
    method: str = _field(init=False, default="GET")
    official_origin: str = _field(init=False, default=_OFFICIAL_ORIGIN)
    canonical_request_url: str = _field(init=False)
    request_identity_sha256: str = _field(init=False)
    request_identity: str = _field(init=False)

    def __post_init__(self) -> None:
        if type(self.page_kind) is not NARMarketOddsPageKind:
            raise _validation("page_kind must be exact NARMarketOddsPageKind")
        if type(self.race_identity) is not NARMarketOddsRaceIdentity:
            raise _validation("race_identity must be exact NARMarketOddsRaceIdentity")
        race = NARMarketOddsRaceIdentity(
            baba_code=self.race_identity.baba_code,
            race_date=self.race_identity.race_date,
            race_no=self.race_identity.race_no,
        )
        path = _PATHS[self.page_kind]
        encoded_date = race.race_date.isoformat().replace("-", "%2F")
        canonical_url = (
            f"{_OFFICIAL_ORIGIN}{path}?k_babaCode={race.baba_code}"
            f"&k_raceDate={encoded_date}&k_raceNo={race.race_no}"
        )
        payload = {
            "baba_code": race.baba_code,
            "canonical_request_url": canonical_url,
            "method": "GET",
            "official_origin": _OFFICIAL_ORIGIN,
            "organization": "NAR",
            "page_kind": self.page_kind.value,
            "race_date": race.race_date.isoformat(),
            "race_no": race.race_no,
            "schema_version": 1,
            "source_system": "keiba.go.jp",
        }
        digest = _hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()
        object.__setattr__(self, "race_identity", race)
        object.__setattr__(self, "canonical_request_url", canonical_url)
        object.__setattr__(self, "request_identity_sha256", digest)
        object.__setattr__(self, "request_identity", _REQUEST_PREFIX + digest)


def build_nar_market_odds_request_identity(
    *,
    page_kind: NARMarketOddsPageKind,
    baba_code: str,
    race_date: _date,
    race_no: int,
) -> NARMarketOddsRequestIdentity:
    """Build one canonical, provider-race-scoped NAR market request identity."""

    return NARMarketOddsRequestIdentity(
        page_kind=page_kind,
        race_identity=NARMarketOddsRaceIdentity(
            baba_code=baba_code,
            race_date=race_date,
            race_no=race_no,
        ),
    )


@_dataclass(frozen=True, slots=True)
class NARMarketOddsResponseCapture:
    request_identity: NARMarketOddsRequestIdentity
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
    schema_version: int = _field(init=False, default=1)
    response_sha256: str = _field(init=False)
    byte_length: int = _field(init=False)
    capture_id: str = _field(init=False)

    def __post_init__(self) -> None:
        if type(self.request_identity) is not NARMarketOddsRequestIdentity:
            raise _validation("request_identity must be exact NARMarketOddsRequestIdentity")
        expected_request = NARMarketOddsRequestIdentity(
            page_kind=self.request_identity.page_kind,
            race_identity=self.request_identity.race_identity,
        )
        if self.request_identity != expected_request:
            raise _validation("request_identity derived values are contradictory")
        if type(self.effective_url) is not str or not self.effective_url:
            raise _validation("effective_url must be an exact non-empty str")
        if self.effective_url != expected_request.canonical_request_url:
            raise _validation("effective_url must equal the canonical request URL")
        if type(self.response_body) is not bytes or not self.response_body:
            raise _validation("response_body must be non-empty exact bytes")
        if type(self.charset) is not str:
            raise _validation("charset must be exact str")
        if self.charset != "utf-8":
            raise NARMarketOddsCaptureUnsupportedError("charset is outside the Phase32 profile")
        try:
            self.response_body.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise NARMarketOddsCaptureUnsupportedError(
                "response_body is not strict UTF-8",
            ) from error
        if type(self.http_status) is not int or self.http_status != 200:
            raise _validation("http_status must be exact int 200")
        if self.content_encoding is not None:
            if type(self.content_encoding) is not str:
                raise _validation("content_encoding must be exact str or None")
            if self.content_encoding != "identity":
                raise NARMarketOddsCaptureUnsupportedError(
                    "content_encoding is outside the Phase32 profile",
                )
        for value, name in (
            (self.content_type, "content_type"),
            (self.content_encoding, "content_encoding"),
            (self.http_date, "http_date"),
            (self.etag, "etag"),
            (self.last_modified, "last_modified"),
        ):
            _optional_header(value, name)
        byte_length = len(self.response_body)
        if self.content_length is not None:
            if type(self.content_length) is not int or self.content_length < 0:
                raise _validation("content_length must be an exact nonnegative int or None")
            if self.content_length != byte_length:
                raise _validation("content_length must equal response byte length")
        requested = _utc_datetime(self.requested_at, "requested_at")
        observed = _utc_datetime(self.observed_at, "observed_at")
        captured = _utc_datetime(self.captured_at, "captured_at")
        if not requested <= observed <= captured:
            raise _validation("requested_at, observed_at, and captured_at are out of order")
        response_digest = _hashlib.sha256(self.response_body).hexdigest()
        payload = {
            "captured_at_utc": _datetime_text(captured),
            "charset": "utf-8",
            "content_encoding": self.content_encoding,
            "content_length": self.content_length,
            "content_type": self.content_type,
            "effective_url": self.effective_url,
            "etag": self.etag,
            "http_date": self.http_date,
            "http_status": 200,
            "last_modified": self.last_modified,
            "observed_at_utc": _datetime_text(observed),
            "request_identity_sha256": expected_request.request_identity_sha256,
            "requested_at_utc": _datetime_text(requested),
            "response_sha256": response_digest,
            "schema_version": 1,
        }
        capture_digest = _hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()
        object.__setattr__(self, "request_identity", expected_request)
        object.__setattr__(self, "requested_at", requested)
        object.__setattr__(self, "observed_at", observed)
        object.__setattr__(self, "captured_at", captured)
        object.__setattr__(self, "response_sha256", response_digest)
        object.__setattr__(self, "byte_length", byte_length)
        object.__setattr__(self, "capture_id", _CAPTURE_PREFIX + capture_digest)


class NARMarketOddsCaptureSource(_Protocol):
    def load_capture(
        self,
        *,
        capture_id: str,
    ) -> NARMarketOddsResponseCapture | None: ...


class NARMarketOddsCaptureArchive(NARMarketOddsCaptureSource, _Protocol):
    def save_capture(
        self,
        *,
        capture: NARMarketOddsResponseCapture,
    ) -> None: ...


__all__ = (
    "NARMarketOddsCaptureArchive",
    "NARMarketOddsCaptureError",
    "NARMarketOddsCaptureSource",
    "NARMarketOddsCaptureUnsupportedError",
    "NARMarketOddsCaptureValidationError",
    "NARMarketOddsPageKind",
    "NARMarketOddsRaceIdentity",
    "NARMarketOddsRequestIdentity",
    "NARMarketOddsResponseCapture",
    "build_nar_market_odds_request_identity",
)


if "annotations" in globals():
    del annotations
