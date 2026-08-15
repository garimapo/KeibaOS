"""Immutable provider-neutral references to supplied historical evidence."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass
from datetime import datetime as _datetime, timezone as _timezone
import re as _re
from unicodedata import category as _category, normalize as _normalize
from urllib.parse import urlsplit as _urlsplit


_SHA256 = _re.compile(r"[0-9a-f]{64}\Z")


def _text(value: object, name: str) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{name} must be a non-empty str")
    normalized = _normalize("NFC", value)
    if normalized != value:
        raise ValueError(f"{name} must already be NFC-normalized")
    return value


def _url(value: object) -> str | None:
    if value is None:
        return None
    result = _text(value, "canonical_source_url")
    if result != result.strip() or any(_category(char) == "Cc" for char in result):
        raise ValueError("canonical_source_url is invalid")
    try:
        parsed = _urlsplit(result)
        host = parsed.hostname
        _ = parsed.port
    except ValueError as error:
        raise ValueError("canonical_source_url is invalid") from error
    if parsed.scheme != "https" or not parsed.netloc or not host:
        raise ValueError("canonical_source_url must be an absolute https URL with host")
    if parsed.username is not None or parsed.password is not None or parsed.fragment:
        raise ValueError("canonical_source_url is invalid")
    return result


def _normalize_datetime(value: object, name: str) -> _datetime:
    if type(value) is not _datetime:
        raise ValueError(f"{name} must be datetime")
    try:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{name} must be timezone-aware")
        return value.astimezone(_timezone.utc)
    except ValueError:
        raise
    except (TypeError, OverflowError) as error:
        raise ValueError(f"{name} must be timezone-aware") from error


@_dataclass(frozen=True, slots=True)
class HistoricalInputEvidenceReference:
    """One semantic role binding to one immutable supplied response."""

    evidence_role: str
    canonical_source_url: str | None
    response_sha256: str
    available_at: _datetime | None
    observed_at: _datetime
    request_identity_sha256: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_role", _text(self.evidence_role, "evidence_role"))
        object.__setattr__(self, "canonical_source_url", _url(self.canonical_source_url))
        if type(self.response_sha256) is not str or _SHA256.fullmatch(self.response_sha256) is None:
            raise ValueError("response_sha256 must be lowercase SHA-256 hex")
        if self.request_identity_sha256 is not None:
            if type(self.request_identity_sha256) is not str or _SHA256.fullmatch(self.request_identity_sha256) is None:
                raise ValueError("request_identity_sha256 must be lowercase SHA-256 hex or None")
            if self.canonical_source_url is None:
                raise ValueError("request_identity_sha256 requires canonical_source_url")
        available = None if self.available_at is None else _normalize_datetime(self.available_at, "available_at")
        observed = _normalize_datetime(self.observed_at, "observed_at")
        if available is not None and available > observed:
            raise ValueError("available_at must not be later than observed_at")
        object.__setattr__(self, "available_at", available)
        object.__setattr__(self, "observed_at", observed)


if "annotations" in globals():
    del annotations
