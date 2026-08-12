"""Append-only SQLite archive for trusted JRA parser-input bytes."""

from __future__ import annotations

from datetime import datetime as _datetime, timezone as _timezone
import hashlib as _hashlib
import re as _re
import sqlite3 as _sqlite3

from scripts.simulation.jra_official_response_capture import (
    JRAOfficialResponseCapture as _Capture,
    JRAOfficialResponseCaptureError as _CaptureError,
    JRAOfficialResponseCaptureMissingError as _Missing,
    JRASuppliedOfficialResponse as _Supplied,
    canonicalize_jra_official_capture_url as _canonicalize,
)
from .errors import RepositoryConflictError as _Conflict, RepositoryDataIntegrityError as _Integrity, RepositoryValidationError as _Validation

_CAPTURE = _re.compile(r"jra-capture-v1:[0-9a-f]{64}\Z")
_SHA = _re.compile(r"[0-9a-f]{64}\Z")


class SQLiteJRAOfficialResponseCaptureRepository:
    __slots__ = ("_connection",)

    def __init__(self, *, connection: _sqlite3.Connection) -> None:
        if type(connection) is not _sqlite3.Connection or connection.in_transaction:
            raise _Validation("connection is invalid")
        self._connection = connection
        self._foreign_keys()

    def save_capture(self, *, capture: _Capture) -> None:
        if type(capture) is not _Capture:
            raise _Validation("capture must be exact JRAOfficialResponseCapture")
        if _CAPTURE.fullmatch(capture.capture_id) is None or _SHA.fullmatch(capture.response_sha256) is None or _hashlib.sha256(capture.response_body).hexdigest() != capture.response_sha256:
            raise _Validation("capture identity is invalid")
        if self._connection.in_transaction:
            raise _Validation("repository write requires no active transaction")
        self._foreign_keys()
        try:
            self._connection.execute("BEGIN IMMEDIATE")
            existing = self._by_id(capture.capture_id)
            if existing is not None:
                if existing != capture:
                    raise _Conflict("capture identity conflicts with immutable content")
                self._connection.commit()
                return
            self._require_evidence_absent(capture)
            self._require_body_not_repair(capture)
            self._body(capture)
            self._connection.execute("""INSERT INTO jra_official_response_captures(
                capture_id,schema_version,page_kind,canonical_source_url,response_sha256,charset,requested_at_utc,
                observed_at_utc,stored_at_utc,http_status,content_type,content_encoding,http_date,etag,last_modified,content_length
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
                capture.capture_id, 1, capture.page_kind.value, capture.canonical_source_url, capture.response_sha256,
                capture.charset, self._time(capture.requested_at), self._time(capture.observed_at), self._time(capture.stored_at),
                capture.http_status, capture.content_type, capture.content_encoding, capture.http_date, capture.etag,
                capture.last_modified, capture.content_length,
            ))
            self._connection.commit()
        except (_Conflict, _Integrity, _Validation):
            self._connection.rollback()
            raise
        except _sqlite3.Error as error:
            self._connection.rollback()
            raise _Integrity("JRA capture archive write failed") from error

    def load_capture(self, *, capture_id: str) -> _Capture | None:
        if type(capture_id) is not str or _CAPTURE.fullmatch(capture_id) is None:
            raise _Validation("capture_id is invalid")
        try:
            rows = self._connection.execute("SELECT capture_id,schema_version,page_kind,canonical_source_url,response_sha256,charset,requested_at_utc,observed_at_utc,stored_at_utc,http_status,content_type,content_encoding,http_date,etag,last_modified,content_length FROM jra_official_response_captures WHERE capture_id=?", (capture_id,)).fetchall()
            if not rows:
                return None
            if len(rows) != 1:
                raise _Integrity("capture ID is duplicated")
            return self._reconstruct(rows[0])
        except _Integrity:
            raise
        except _sqlite3.Error as error:
            raise _Integrity("JRA capture archive read failed") from error

    def load_supplied_response_for_evidence(self, *, canonical_source_url: str, response_sha256: str, observed_at: _datetime) -> _Supplied:
        if type(canonical_source_url) is not str or type(response_sha256) is not str or _SHA.fullmatch(response_sha256) is None:
            raise _Validation("evidence identity is invalid")
        try:
            kind = self._kind(canonical_source_url)
            canonical = _canonicalize(page_kind=kind, response_url=canonical_source_url)
            if canonical != canonical_source_url:
                raise _Validation("canonical_source_url is not canonical")
            observed = self._lookup_time(observed_at)
            rows = self._connection.execute("SELECT capture_id,schema_version,page_kind,canonical_source_url,response_sha256,charset,requested_at_utc,observed_at_utc,stored_at_utc,http_status,content_type,content_encoding,http_date,etag,last_modified,content_length FROM jra_official_response_captures WHERE canonical_source_url=? AND response_sha256=? AND observed_at_utc=?", (canonical, response_sha256, self._time(observed))).fetchall()
            if not rows:
                raise _Missing("exact trusted JRA capture evidence is not archived")
            if len(rows) != 1:
                raise _Integrity("capture evidence is duplicated")
            return self._reconstruct(rows[0]).to_supplied_official_response()
        except (_Missing, _Integrity, _Validation):
            raise
        except _sqlite3.Error as error:
            raise _Integrity("JRA capture archive evidence read failed") from error

    def _foreign_keys(self) -> None:
        try:
            self._connection.execute("PRAGMA foreign_keys=ON")
            if self._connection.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
                raise _Validation("foreign_keys cannot be enabled")
        except _sqlite3.Error as error:
            raise _Validation("connection is unusable") from error

    def _body(self, capture: _Capture) -> None:
        rows = self._connection.execute("SELECT response_body,byte_length FROM jra_official_response_bodies WHERE response_sha256=?", (capture.response_sha256,)).fetchall()
        if not rows:
            self._connection.execute("INSERT INTO jra_official_response_bodies(response_sha256,response_body,byte_length) VALUES(?,?,?)", (capture.response_sha256, capture.response_body, len(capture.response_body)))
            return
        if len(rows) != 1:
            raise _Integrity("stored JRA body is duplicated")
        body, length = rows[0]
        if type(body) is not bytes or type(length) is not int or length != len(body) or _hashlib.sha256(body).hexdigest() != capture.response_sha256:
            raise _Integrity("stored JRA body is corrupt")
        if body != capture.response_body:
            raise _Conflict("same JRA body digest has conflicting bytes")

    def _require_body_not_repair(self, capture: _Capture) -> None:
        if self._connection.execute("SELECT 1 FROM jra_official_response_bodies WHERE response_sha256=?", (capture.response_sha256,)).fetchone() is None and self._connection.execute("SELECT 1 FROM jra_official_response_captures WHERE response_sha256=? LIMIT 1", (capture.response_sha256,)).fetchone() is not None:
            raise _Integrity("missing JRA body must not be repaired")

    def _require_evidence_absent(self, capture: _Capture) -> None:
        rows = self._connection.execute("SELECT capture_id FROM jra_official_response_captures WHERE canonical_source_url=? AND response_sha256=? AND observed_at_utc=?", (capture.canonical_source_url, capture.response_sha256, self._time(capture.observed_at))).fetchall()
        if len(rows) > 1:
            raise _Integrity("stored JRA evidence is duplicated")
        if rows:
            raise _Integrity("stored JRA evidence has inconsistent identity")

    def _by_id(self, capture_id: str) -> _Capture | None:
        rows = self._connection.execute("SELECT capture_id,schema_version,page_kind,canonical_source_url,response_sha256,charset,requested_at_utc,observed_at_utc,stored_at_utc,http_status,content_type,content_encoding,http_date,etag,last_modified,content_length FROM jra_official_response_captures WHERE capture_id=?", (capture_id,)).fetchall()
        if not rows:
            return None
        if len(rows) != 1:
            raise _Integrity("capture ID is duplicated")
        return self._reconstruct(rows[0])

    def _reconstruct(self, row: object) -> _Capture:
        try:
            capture_id, version, kind, url, digest, charset, requested, observed, stored, status, content_type, encoding, http_date, etag, last_modified, length = tuple(row)
            body_rows = self._connection.execute("SELECT response_body,byte_length FROM jra_official_response_bodies WHERE response_sha256=?", (digest,)).fetchall()
            if len(body_rows) != 1:
                raise _Integrity("stored JRA body is missing or duplicated")
            body, body_length = body_rows[0]
            if type(body) is not bytes or type(body_length) is not int or body_length != len(body) or _hashlib.sha256(body).hexdigest() != digest:
                raise _Integrity("stored JRA body is corrupt")
            capture = _Capture(canonical_source_url=url, response_body=body, charset=charset, requested_at=self._stored_time(requested), observed_at=self._stored_time(observed), stored_at=self._stored_time(stored), http_status=status, content_type=content_type, content_encoding=encoding, http_date=http_date, etag=etag, last_modified=last_modified, content_length=length)
        except _Integrity:
            raise
        except (_CaptureError, TypeError, ValueError, OverflowError) as error:
            raise _Integrity("stored JRA capture violates domain contract") from error
        if type(kind) is not str or version != 1 or capture.capture_id != capture_id or capture.page_kind.value != kind or capture.response_sha256 != digest:
            raise _Integrity("stored JRA capture identity differs")
        rows = self._connection.execute("SELECT capture_id FROM jra_official_response_captures WHERE canonical_source_url=? AND response_sha256=? AND observed_at_utc=?", (capture.canonical_source_url, capture.response_sha256, self._time(capture.observed_at))).fetchall()
        if len(rows) != 1 or rows[0][0] != capture_id:
            raise _Integrity("stored JRA evidence is not unique")
        return capture

    @staticmethod
    def _kind(url: str):
        from scripts.simulation.jra_official_response_capture import JRAOfficialPageKind
        for kind in (JRAOfficialPageKind.RACE_RESULT, JRAOfficialPageKind.HORSE_PROFILE_HISTORY):
            try:
                if _canonicalize(page_kind=kind, response_url=url) == url:
                    return kind
            except _CaptureError:
                pass
        raise _Validation("canonical_source_url is invalid")

    @staticmethod
    def _time(value: _datetime) -> str:
        return value.astimezone(_timezone.utc).isoformat(timespec="microseconds")

    @staticmethod
    def _lookup_time(value: object) -> _datetime:
        if type(value) is not _datetime or value.tzinfo is None or value.utcoffset() is None:
            raise _Validation("observed_at is invalid")
        return value.astimezone(_timezone.utc)

    @staticmethod
    def _stored_time(value: object) -> _datetime:
        if type(value) is not str or len(value) != 32:
            raise _Integrity("stored UTC timestamp is invalid")
        try:
            parsed = _datetime.fromisoformat(value)
            if parsed.tzinfo is None or parsed.utcoffset() != _timezone.utc.utcoffset(parsed) or parsed.astimezone(_timezone.utc).isoformat(timespec="microseconds") != value:
                raise ValueError
            return parsed.astimezone(_timezone.utc)
        except (TypeError, ValueError, OverflowError) as error:
            raise _Integrity("stored UTC timestamp is invalid") from error


if "annotations" in globals():
    del annotations
