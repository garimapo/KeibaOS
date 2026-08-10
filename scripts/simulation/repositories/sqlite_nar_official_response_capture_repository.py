"""SQLite archive for immutable NAR official-response captures in a separate DB."""

from __future__ import annotations

from datetime import datetime as _datetime, timezone as _timezone
import hashlib as _hashlib
import re as _re
import sqlite3 as _sqlite3

from scripts.simulation.nar_official_response_capture import (
    NAROfficialResponseCapture as _NAROfficialResponseCapture,
    NAROfficialResponseCaptureError as _NAROfficialResponseCaptureError,
    NAROfficialResponseCaptureMissingError as _NAROfficialResponseCaptureMissingError,
    canonicalize_nar_official_capture_url as _canonicalize_nar_official_capture_url,
)
from scripts.simulation.nar_historical_input_source import (
    NarSuppliedOfficialResponse as _NarSuppliedOfficialResponse,
)

from .errors import (
    RepositoryConflictError as _RepositoryConflictError,
    RepositoryDataIntegrityError as _RepositoryDataIntegrityError,
    RepositoryValidationError as _RepositoryValidationError,
)


_CAPTURE_ID = _re.compile(r"nar-capture-v1:[0-9a-f]{64}\Z")
_SHA256 = _re.compile(r"[0-9a-f]{64}\Z")


class SQLiteNAROfficialResponseCaptureRepository:
    """Connection-injected, append-only archive for trusted parser-input bytes."""

    __slots__ = ("_connection",)

    def __init__(self, *, connection: _sqlite3.Connection) -> None:
        if type(connection) is not _sqlite3.Connection:
            raise _RepositoryValidationError("connection must be exact sqlite3.Connection")
        if connection.in_transaction:
            raise _RepositoryValidationError("repository construction requires no active transaction")
        self._connection = connection
        self._ensure_foreign_keys()

    def save_capture(self, *, capture: _NAROfficialResponseCapture) -> None:
        """Atomically persist one immutable observation and its content-addressed body."""

        if type(capture) is not _NAROfficialResponseCapture:
            raise _RepositoryValidationError("capture must be exact NAROfficialResponseCapture")
        if _CAPTURE_ID.fullmatch(capture.capture_id) is None or _SHA256.fullmatch(capture.response_sha256) is None:
            raise _RepositoryValidationError("capture identity is invalid")
        if _hashlib.sha256(capture.response_body).hexdigest() != capture.response_sha256:
            raise _RepositoryValidationError("capture response_body digest is invalid")
        if self._connection.in_transaction:
            raise _RepositoryValidationError("repository writes require no active transaction")
        self._ensure_foreign_keys()
        try:
            self._connection.execute("BEGIN IMMEDIATE")
            self._ensure_body(capture)
            existing = self._capture_by_id(capture.capture_id)
            if existing is not None:
                if existing != capture:
                    raise _RepositoryConflictError("capture identity already has different immutable content")
                self._connection.commit()
                return
            tuple_rows = self._connection.execute(
                """SELECT capture_id FROM nar_official_response_captures
                   WHERE canonical_source_url=? AND response_sha256=? AND observed_at_utc=?""",
                (capture.canonical_source_url, capture.response_sha256, self._datetime_text(capture.observed_at)),
            ).fetchall()
            if len(tuple_rows) > 1:
                raise _RepositoryDataIntegrityError("stored evidence tuple is duplicated")
            if tuple_rows:
                raise _RepositoryDataIntegrityError("stored evidence tuple has impossible capture identity")
            self._connection.execute(
                """INSERT INTO nar_official_response_captures(
                    capture_id,schema_version,page_kind,canonical_source_url,response_sha256,charset,
                    requested_at_utc,observed_at_utc,stored_at_utc,http_status,content_type,content_encoding,
                    http_date,etag,last_modified,content_length
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    capture.capture_id, capture.schema_version, capture.page_kind.value, capture.canonical_source_url,
                    capture.response_sha256, capture.charset, self._datetime_text(capture.requested_at),
                    self._datetime_text(capture.observed_at), self._datetime_text(capture.stored_at), capture.http_status,
                    capture.content_type, capture.content_encoding, capture.http_date, capture.etag,
                    capture.last_modified, capture.content_length,
                ),
            )
            self._connection.commit()
        except (_RepositoryConflictError, _RepositoryDataIntegrityError, _RepositoryValidationError):
            self._connection.rollback()
            raise
        except _sqlite3.Error as error:
            self._connection.rollback()
            raise _RepositoryDataIntegrityError("capture archive SQLite write failed") from error

    def load_capture(self, *, capture_id: str) -> _NAROfficialResponseCapture | None:
        """Load exactly one capture ID, returning None only for a valid absent ID."""

        if type(capture_id) is not str or _CAPTURE_ID.fullmatch(capture_id) is None:
            raise _RepositoryValidationError("capture_id is invalid")
        try:
            rows = self._connection.execute(
                """SELECT capture_id,schema_version,page_kind,canonical_source_url,response_sha256,charset,
                          requested_at_utc,observed_at_utc,stored_at_utc,http_status,content_type,content_encoding,
                          http_date,etag,last_modified,content_length
                   FROM nar_official_response_captures WHERE capture_id=?""",
                (capture_id,),
            ).fetchall()
        except _sqlite3.Error as error:
            raise _RepositoryDataIntegrityError("capture archive SQLite read failed") from error
        if not rows:
            return None
        if len(rows) != 1:
            raise _RepositoryDataIntegrityError("capture ID is duplicated")
        return self._reconstruct(rows[0])

    def load_supplied_response_for_evidence(
        self,
        *,
        canonical_source_url: str,
        response_sha256: str,
        observed_at: _datetime,
    ) -> _NarSuppliedOfficialResponse:
        """Reconstruct only an exact archived evidence tuple; never select a nearby capture."""

        try:
            _kind, canonical = _canonicalize_nar_official_capture_url(canonical_source_url)
        except _NAROfficialResponseCaptureError as error:
            raise _RepositoryValidationError("canonical_source_url is invalid") from error
        if canonical_source_url != canonical:
            raise _RepositoryValidationError("canonical_source_url must already be canonical")
        if type(response_sha256) is not str or _SHA256.fullmatch(response_sha256) is None:
            raise _RepositoryValidationError("response_sha256 is invalid")
        observed = self._lookup_datetime(observed_at, "observed_at")
        try:
            rows = self._connection.execute(
                """SELECT capture_id,schema_version,page_kind,canonical_source_url,response_sha256,charset,
                          requested_at_utc,observed_at_utc,stored_at_utc,http_status,content_type,content_encoding,
                          http_date,etag,last_modified,content_length
                   FROM nar_official_response_captures
                   WHERE canonical_source_url=? AND response_sha256=? AND observed_at_utc=?""",
                (canonical, response_sha256, self._datetime_text(observed)),
            ).fetchall()
        except _sqlite3.Error as error:
            raise _RepositoryDataIntegrityError("capture archive SQLite evidence read failed") from error
        if not rows:
            raise _NAROfficialResponseCaptureMissingError("exact trusted capture evidence is not archived")
        if len(rows) != 1:
            raise _RepositoryDataIntegrityError("stored evidence tuple is duplicated")
        return self._reconstruct(rows[0]).to_supplied_official_response()

    def _ensure_foreign_keys(self) -> None:
        try:
            self._connection.execute("PRAGMA foreign_keys = ON")
            enabled = self._connection.execute("PRAGMA foreign_keys").fetchone()
        except _sqlite3.Error as error:
            raise _RepositoryValidationError("connection is not usable") from error
        if enabled is None or enabled[0] != 1:
            raise _RepositoryValidationError("foreign_keys could not be enabled")

    def _ensure_body(self, capture: _NAROfficialResponseCapture) -> None:
        rows = self._connection.execute(
            "SELECT response_body,byte_length FROM nar_official_response_bodies WHERE response_sha256=?",
            (capture.response_sha256,),
        ).fetchall()
        if not rows:
            self._connection.execute(
                "INSERT INTO nar_official_response_bodies(response_sha256,response_body,byte_length) VALUES(?,?,?)",
                (capture.response_sha256, capture.response_body, len(capture.response_body)),
            )
            return
        if len(rows) != 1:
            raise _RepositoryDataIntegrityError("stored response body identity is duplicated")
        body, byte_length = rows[0]
        if type(body) is not bytes or type(byte_length) is not int or byte_length != len(body):
            raise _RepositoryDataIntegrityError("stored response body length is invalid")
        if _hashlib.sha256(body).hexdigest() != capture.response_sha256:
            raise _RepositoryDataIntegrityError("stored response body digest is invalid")
        if body != capture.response_body:
            raise _RepositoryConflictError("response digest has conflicting body bytes")

    def _capture_by_id(self, capture_id: str) -> _NAROfficialResponseCapture | None:
        rows = self._connection.execute(
            """SELECT capture_id,schema_version,page_kind,canonical_source_url,response_sha256,charset,
                      requested_at_utc,observed_at_utc,stored_at_utc,http_status,content_type,content_encoding,
                      http_date,etag,last_modified,content_length
               FROM nar_official_response_captures WHERE capture_id=?""",
            (capture_id,),
        ).fetchall()
        if not rows:
            return None
        if len(rows) != 1:
            raise _RepositoryDataIntegrityError("capture ID is duplicated")
        return self._reconstruct(rows[0])

    def _reconstruct(self, row: object) -> _NAROfficialResponseCapture:
        try:
            (
                capture_id, schema_version, page_kind, canonical_url, response_sha256, charset,
                requested, observed, stored, http_status, content_type, content_encoding,
                http_date, etag, last_modified, content_length,
            ) = tuple(row)
        except (TypeError, ValueError) as error:
            raise _RepositoryDataIntegrityError("stored capture row is malformed") from error
        if type(capture_id) is not str or _CAPTURE_ID.fullmatch(capture_id) is None:
            raise _RepositoryDataIntegrityError("stored capture_id is invalid")
        if type(schema_version) is not int or schema_version != 1 or type(page_kind) is not str:
            raise _RepositoryDataIntegrityError("stored capture identity is invalid")
        if type(canonical_url) is not str or type(response_sha256) is not str or _SHA256.fullmatch(response_sha256) is None:
            raise _RepositoryDataIntegrityError("stored capture URL or digest is invalid")
        body_rows = self._connection.execute(
            "SELECT response_body,byte_length FROM nar_official_response_bodies WHERE response_sha256=?",
            (response_sha256,),
        ).fetchall()
        if len(body_rows) != 1:
            raise _RepositoryDataIntegrityError("stored capture body is missing or duplicated")
        body, byte_length = body_rows[0]
        if type(body) is not bytes or type(byte_length) is not int or byte_length != len(body):
            raise _RepositoryDataIntegrityError("stored capture body length is invalid")
        if _hashlib.sha256(body).hexdigest() != response_sha256:
            raise _RepositoryDataIntegrityError("stored capture body digest is invalid")
        try:
            capture = _NAROfficialResponseCapture(
                canonical_source_url=canonical_url,
                response_body=body,
                charset=charset,
                requested_at=self._stored_datetime(requested, "requested_at_utc"),
                observed_at=self._stored_datetime(observed, "observed_at_utc"),
                stored_at=self._stored_datetime(stored, "stored_at_utc"),
                http_status=http_status,
                content_type=self._stored_header(content_type, "content_type"),
                content_encoding=self._stored_header(content_encoding, "content_encoding"),
                http_date=self._stored_header(http_date, "http_date"),
                etag=self._stored_header(etag, "etag"),
                last_modified=self._stored_header(last_modified, "last_modified"),
                content_length=self._stored_content_length(content_length, body),
            )
        except _NAROfficialResponseCaptureError as error:
            raise _RepositoryDataIntegrityError("stored capture violates domain invariants") from error
        if capture.capture_id != capture_id or capture.schema_version != schema_version:
            raise _RepositoryDataIntegrityError("stored capture derived identity differs")
        if capture.page_kind.value != page_kind or capture.response_sha256 != response_sha256:
            raise _RepositoryDataIntegrityError("stored capture derived values differ")
        return capture

    @staticmethod
    def _stored_header(value: object, name: str) -> str | None:
        if value is None:
            return None
        if type(value) is not str:
            raise _RepositoryDataIntegrityError(f"stored {name} is invalid")
        return value

    @staticmethod
    def _stored_content_length(value: object, body: bytes) -> int | None:
        if value is None:
            return None
        if type(value) is not int or value < 0 or value != len(body):
            raise _RepositoryDataIntegrityError("stored content_length is invalid")
        return value

    @staticmethod
    def _stored_datetime(value: object, name: str) -> _datetime:
        if type(value) is not str or len(value) != 32:
            raise _RepositoryDataIntegrityError(f"stored {name} is invalid")
        try:
            parsed = _datetime.fromisoformat(value)
            if parsed.tzinfo is None or parsed.utcoffset() != _timezone.utc.utcoffset(parsed):
                raise ValueError("not UTC")
            canonical = parsed.astimezone(_timezone.utc).isoformat(timespec="microseconds")
        except (TypeError, ValueError, OverflowError) as error:
            raise _RepositoryDataIntegrityError(f"stored {name} is invalid") from error
        if canonical != value:
            raise _RepositoryDataIntegrityError(f"stored {name} is not canonical UTC")
        return parsed.astimezone(_timezone.utc)

    @staticmethod
    def _lookup_datetime(value: object, name: str) -> _datetime:
        if type(value) is not _datetime:
            raise _RepositoryValidationError(f"{name} must be exact aware datetime")
        try:
            if value.tzinfo is None or value.utcoffset() is None:
                raise _RepositoryValidationError(f"{name} must be exact aware datetime")
            return value.astimezone(_timezone.utc)
        except _RepositoryValidationError:
            raise
        except (TypeError, ValueError, OverflowError) as error:
            raise _RepositoryValidationError(f"{name} is invalid") from error

    @staticmethod
    def _datetime_text(value: _datetime) -> str:
        return value.astimezone(_timezone.utc).isoformat(timespec="microseconds")


if "annotations" in globals():
    del annotations
