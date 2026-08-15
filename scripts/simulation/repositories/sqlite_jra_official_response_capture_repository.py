"""Append-only SQLite archive for trusted JRA parser-input bytes."""

from __future__ import annotations

from datetime import datetime as _datetime, timezone as _timezone
import hashlib as _hashlib
import re as _re
import sqlite3 as _sqlite3

from scripts.simulation.jra_official_response_capture import (
    JRAFinalWinOddsResponseCapture as _FinalCapture,
    JRAFinalWinOddsSuppliedOfficialResponse as _FinalSupplied,
    JRAOfficialPageKind as _PageKind,
    JRAOfficialResponseCapture as _Capture,
    JRAOfficialResponseCaptureError as _CaptureError,
    JRAOfficialResponseCaptureMissingError as _Missing,
    JRASuppliedOfficialResponse as _Supplied,
    canonicalize_jra_official_capture_url as _canonicalize,
)
from .errors import RepositoryConflictError as _Conflict, RepositoryDataIntegrityError as _Integrity, RepositoryValidationError as _Validation

_V1_CAPTURE = _re.compile(r"jra-capture-v1:[0-9a-f]{64}\Z")
_V2_CAPTURE = _re.compile(r"jra-capture-v2:[0-9a-f]{64}\Z")
_SHA = _re.compile(r"[0-9a-f]{64}\Z")
_COLUMNS = "capture_id,schema_version,page_kind,canonical_source_url,response_sha256,charset,requested_at_utc,observed_at_utc,stored_at_utc,http_status,content_type,content_encoding,http_date,etag,last_modified,content_length,request_method,request_identity_sha256,request_cname"


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
        self._save(capture=capture, final=False)

    def save_final_win_odds_capture(self, *, capture: _FinalCapture) -> None:
        if type(capture) is not _FinalCapture:
            raise _Validation("capture must be exact JRAFinalWinOddsResponseCapture")
        self._save(capture=capture, final=True)

    def load_capture(self, *, capture_id: str) -> _Capture | None:
        if type(capture_id) is not str or _V1_CAPTURE.fullmatch(capture_id) is None:
            if type(capture_id) is str and _V2_CAPTURE.fullmatch(capture_id) is not None:
                return None
            raise _Validation("capture_id is invalid")
        item = self._load_by_id(capture_id)
        if item is None:
            return None
        if type(item) is not _Capture:
            raise _Integrity("stored JRA capture family differs")
        return item

    def load_final_win_odds_capture(self, *, capture_id: str) -> _FinalCapture | None:
        if type(capture_id) is not str or _V2_CAPTURE.fullmatch(capture_id) is None:
            if type(capture_id) is str and _V1_CAPTURE.fullmatch(capture_id) is not None:
                return None
            raise _Validation("capture_id is invalid")
        item = self._load_by_id(capture_id)
        if item is None:
            return None
        if type(item) is not _FinalCapture:
            raise _Integrity("stored JRA capture family differs")
        return item

    def load_supplied_response_for_evidence(self, *, canonical_source_url: str, response_sha256: str, observed_at: _datetime) -> _Supplied:
        if type(canonical_source_url) is not str or type(response_sha256) is not str or _SHA.fullmatch(response_sha256) is None:
            raise _Validation("evidence identity is invalid")
        try:
            kind = self._kind(canonical_source_url)
            canonical = _canonicalize(page_kind=kind, response_url=canonical_source_url)
            if canonical != canonical_source_url:
                raise _Validation("canonical_source_url is not canonical")
            rows = self._connection.execute(
                f"SELECT {_COLUMNS} FROM jra_official_response_captures WHERE canonical_source_url=? AND response_sha256=? AND observed_at_utc=? AND request_identity_sha256 IS NULL",
                (canonical, response_sha256, self._time(self._lookup_time(observed_at))),
            ).fetchall()
            if not rows:
                raise _Missing("exact trusted JRA capture evidence is not archived")
            if len(rows) != 1:
                raise _Integrity("capture evidence is duplicated")
            item = self._reconstruct(rows[0])
            if type(item) is not _Capture:
                raise _Integrity("stored JRA evidence family differs")
            return item.to_supplied_official_response()
        except (_Missing, _Integrity, _Validation):
            raise
        except _sqlite3.Error as error:
            raise _Integrity("JRA capture archive evidence read failed") from error

    def load_final_win_odds_supplied_response_for_evidence(self, *, canonical_source_url: str, request_identity_sha256: str, response_sha256: str, observed_at: _datetime) -> _FinalSupplied:
        if canonical_source_url != "https://www.jra.go.jp/JRADB/accessO.html" or type(request_identity_sha256) is not str or _SHA.fullmatch(request_identity_sha256) is None or type(response_sha256) is not str or _SHA.fullmatch(response_sha256) is None:
            raise _Validation("final odds evidence identity is invalid")
        try:
            rows = self._connection.execute(
                f"SELECT {_COLUMNS} FROM jra_official_response_captures WHERE canonical_source_url=? AND request_identity_sha256=? AND response_sha256=? AND observed_at_utc=?",
                (canonical_source_url, request_identity_sha256, response_sha256, self._time(self._lookup_time(observed_at))),
            ).fetchall()
            if not rows:
                raise _Missing("exact trusted JRA final odds evidence is not archived")
            if len(rows) != 1:
                raise _Integrity("final odds capture evidence is duplicated")
            item = self._reconstruct(rows[0])
            if type(item) is not _FinalCapture:
                raise _Integrity("stored JRA evidence family differs")
            return item.to_supplied_official_response()
        except (_Missing, _Integrity, _Validation):
            raise
        except _sqlite3.Error as error:
            raise _Integrity("JRA final odds archive evidence read failed") from error

    def _save(self, *, capture: _Capture | _FinalCapture, final: bool) -> None:
        pattern = _V2_CAPTURE if final else _V1_CAPTURE
        if pattern.fullmatch(capture.capture_id) is None or _SHA.fullmatch(capture.response_sha256) is None or _hashlib.sha256(capture.response_body).hexdigest() != capture.response_sha256:
            raise _Validation("capture identity is invalid")
        if self._connection.in_transaction:
            raise _Validation("repository write requires no active transaction")
        self._foreign_keys()
        try:
            self._connection.execute("BEGIN IMMEDIATE")
            existing = self._load_by_id(capture.capture_id)
            if existing is not None:
                if existing != capture:
                    raise _Conflict("capture identity conflicts with immutable content")
                self._connection.commit()
                return
            self._require_evidence_absent(capture=capture, final=final)
            self._require_body_not_repair(capture.response_sha256)
            self._body(capture.response_sha256, capture.response_body)
            if final:
                assert type(capture) is _FinalCapture
                values = (capture.capture_id, 2, _PageKind.FINAL_WIN_ODDS.value, capture.canonical_source_url, capture.response_sha256, capture.charset, self._time(capture.requested_at), self._time(capture.observed_at), self._time(capture.stored_at), capture.http_status, capture.content_type, capture.content_encoding, capture.http_date, capture.etag, capture.last_modified, capture.content_length, "POST", capture.request_locator.request_identity_sha256, capture.request_locator.cname)
            else:
                assert type(capture) is _Capture
                values = (capture.capture_id, 1, capture.page_kind.value, capture.canonical_source_url, capture.response_sha256, capture.charset, self._time(capture.requested_at), self._time(capture.observed_at), self._time(capture.stored_at), capture.http_status, capture.content_type, capture.content_encoding, capture.http_date, capture.etag, capture.last_modified, capture.content_length, "GET", None, None)
            self._connection.execute(f"INSERT INTO jra_official_response_captures({_COLUMNS}) VALUES({','.join('?' for _ in range(19))})", values)
            self._connection.commit()
        except (_Conflict, _Integrity, _Validation):
            self._connection.rollback()
            raise
        except _sqlite3.Error as error:
            self._connection.rollback()
            raise _Integrity("JRA capture archive write failed") from error

    def _load_by_id(self, capture_id: str) -> _Capture | _FinalCapture | None:
        try:
            rows = self._connection.execute(f"SELECT {_COLUMNS} FROM jra_official_response_captures WHERE capture_id=?", (capture_id,)).fetchall()
            if not rows:
                return None
            if len(rows) != 1:
                raise _Integrity("capture ID is duplicated")
            return self._reconstruct(rows[0])
        except _Integrity:
            raise
        except _sqlite3.Error as error:
            raise _Integrity("JRA capture archive read failed") from error

    def _reconstruct(self, row: object) -> _Capture | _FinalCapture:
        try:
            capture_id, version, kind, url, digest, charset, requested, observed, stored, status, content_type, encoding, http_date, etag, last_modified, length, method, request_digest, cname = tuple(row)
            body_rows = self._connection.execute("SELECT response_body,byte_length FROM jra_official_response_bodies WHERE response_sha256=?", (digest,)).fetchall()
            if len(body_rows) != 1:
                raise _Integrity("stored JRA body is missing or duplicated")
            body, body_length = body_rows[0]
            if type(body) is not bytes or type(body_length) is not int or body_length != len(body) or _hashlib.sha256(body).hexdigest() != digest:
                raise _Integrity("stored JRA body is corrupt")
            if version == 1:
                if method != "GET" or request_digest is not None or cname is not None:
                    raise _Integrity("stored legacy JRA request family is invalid")
                capture: _Capture | _FinalCapture = _Capture(canonical_source_url=url, response_body=body, charset=charset, requested_at=self._stored_time(requested), observed_at=self._stored_time(observed), stored_at=self._stored_time(stored), http_status=status, content_type=content_type, content_encoding=encoding, http_date=http_date, etag=etag, last_modified=last_modified, content_length=length)
            elif version == 2:
                if method != "POST" or type(cname) is not str or type(request_digest) is not str:
                    raise _Integrity("stored final odds request family is invalid")
                from scripts.simulation.jra_official_identity import JRAExternalRaceIdentity, JRAOfficialFinalWinOddsRequestLocator
                locator = JRAOfficialFinalWinOddsRequestLocator(
                    endpoint_url=url,
                    cname=cname,
                    external_race_identity=JRAExternalRaceIdentity(cname[11:15], cname[9:11], cname[15:17], cname[17:19], cname[19:21]),
                    request_identity_sha256=request_digest,
                )
                capture = _FinalCapture(request_locator=locator, response_body=body, charset=charset, requested_at=self._stored_time(requested), observed_at=self._stored_time(observed), stored_at=self._stored_time(stored), http_status=status, content_type=content_type, content_encoding=encoding, http_date=http_date, etag=etag, last_modified=last_modified, content_length=length)
            else:
                raise _Integrity("stored JRA capture schema version is invalid")
        except _Integrity:
            raise
        except (_CaptureError, TypeError, ValueError, OverflowError) as error:
            raise _Integrity("stored JRA capture violates domain contract") from error
        if type(kind) is not str or capture.capture_id != capture_id or capture.page_kind.value != kind or capture.response_sha256 != digest:
            raise _Integrity("stored JRA capture identity differs")
        if type(capture) is _Capture:
            if _V1_CAPTURE.fullmatch(capture_id) is None:
                raise _Integrity("stored legacy JRA capture ID is invalid")
        elif _V2_CAPTURE.fullmatch(capture_id) is None:
            raise _Integrity("stored final odds JRA capture ID is invalid")
        return capture

    def _require_evidence_absent(self, *, capture: _Capture | _FinalCapture, final: bool) -> None:
        if final:
            assert type(capture) is _FinalCapture
            rows = self._connection.execute("SELECT capture_id FROM jra_official_response_captures WHERE canonical_source_url=? AND request_identity_sha256=? AND response_sha256=? AND observed_at_utc=?", (capture.canonical_source_url, capture.request_locator.request_identity_sha256, capture.response_sha256, self._time(capture.observed_at))).fetchall()
        else:
            rows = self._connection.execute("SELECT capture_id FROM jra_official_response_captures WHERE canonical_source_url=? AND response_sha256=? AND observed_at_utc=? AND request_identity_sha256 IS NULL", (capture.canonical_source_url, capture.response_sha256, self._time(capture.observed_at))).fetchall()
        if len(rows) > 1:
            raise _Integrity("stored JRA evidence is duplicated")
        if rows:
            raise _Integrity("stored JRA evidence has inconsistent identity")

    def _foreign_keys(self) -> None:
        try:
            self._connection.execute("PRAGMA foreign_keys=ON")
            if self._connection.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
                raise _Validation("foreign_keys cannot be enabled")
        except _sqlite3.Error as error:
            raise _Validation("connection is unusable") from error

    def _body(self, digest: str, body: bytes) -> None:
        rows = self._connection.execute("SELECT response_body,byte_length FROM jra_official_response_bodies WHERE response_sha256=?", (digest,)).fetchall()
        if not rows:
            self._connection.execute("INSERT INTO jra_official_response_bodies(response_sha256,response_body,byte_length) VALUES(?,?,?)", (digest, body, len(body)))
            return
        if len(rows) != 1:
            raise _Integrity("stored JRA body is duplicated")
        stored, length = rows[0]
        if type(stored) is not bytes or type(length) is not int or length != len(stored) or _hashlib.sha256(stored).hexdigest() != digest:
            raise _Integrity("stored JRA body is corrupt")
        if stored != body:
            raise _Conflict("same JRA body digest has conflicting bytes")

    def _require_body_not_repair(self, digest: str) -> None:
        if self._connection.execute("SELECT 1 FROM jra_official_response_bodies WHERE response_sha256=?", (digest,)).fetchone() is None and self._connection.execute("SELECT 1 FROM jra_official_response_captures WHERE response_sha256=? LIMIT 1", (digest,)).fetchone() is not None:
            raise _Integrity("missing JRA body must not be repaired")

    @staticmethod
    def _kind(url: str) -> _PageKind:
        for kind in (_PageKind.RACE_RESULT, _PageKind.HORSE_PROFILE_HISTORY):
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
