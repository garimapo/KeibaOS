"""Append-only SQLite archive for immutable NAR market-odds raw captures."""

from __future__ import annotations

from datetime import date as _date, datetime as _datetime, timezone as _timezone
import hashlib as _hashlib
import re as _re
import sqlite3 as _sqlite3

from scripts.simulation import nar_market_odds_capture_archive_migration as _schema
from scripts.simulation.nar_market_odds_capture import (
    NARMarketOddsCaptureError as _CaptureError,
    NARMarketOddsPageKind as _PageKind,
    NARMarketOddsRaceIdentity as _RaceIdentity,
    NARMarketOddsRequestIdentity as _RequestIdentity,
    NARMarketOddsResponseCapture as _Capture,
)
from scripts.simulation.repositories.errors import (
    RepositoryConflictError as _Conflict,
    RepositoryDataIntegrityError as _Integrity,
    RepositoryValidationError as _Validation,
)


_CAPTURE_ID = _re.compile(r"nar-market-odds-capture-v1:[0-9a-f]{64}\Z")
_SHA256 = _re.compile(r"[0-9a-f]{64}\Z")
_CAPTURE_COLUMNS = """capture_id,schema_version,request_schema_version,request_identity,
request_identity_sha256,page_kind,organization,source_system,request_method,
request_official_origin,request_baba_code,request_race_date,request_race_no,
canonical_request_url,effective_url,response_sha256,charset,requested_at_utc,
observed_at_utc,captured_at_utc,http_status,content_type,content_encoding,http_date,
etag,last_modified,content_length"""


class SQLiteNARMarketOddsCaptureArchive:
    """Connection-injected exact-ID archive for raw NAR market-odds captures."""

    __slots__ = ("_connection",)

    def __init__(self, *, connection: _sqlite3.Connection) -> None:
        if type(connection) is not _sqlite3.Connection:
            raise _Validation("connection must be exact sqlite3.Connection")
        if connection.in_transaction:
            raise _Validation("repository construction requires no active transaction")
        self._connection = connection
        self._foreign_keys()
        self._schema_gate()

    def save_capture(self, *, capture: _Capture) -> None:
        """Atomically publish one immutable capture or accept its exact duplicate."""

        if type(capture) is not _Capture:
            raise _Validation("capture must be exact NARMarketOddsResponseCapture")
        self._require_capture_id(capture.capture_id)
        if self._connection.in_transaction:
            raise _Validation("repository writes require no active transaction")
        self._foreign_keys()
        self._schema_gate()
        try:
            self._connection.execute("BEGIN IMMEDIATE")
            existing = self._capture_by_id(capture.capture_id)
            if existing is not None:
                if existing != capture:
                    raise _Conflict("capture identity already has different immutable content")
                self._connection.commit()
                return
            self._validate_input(capture)
            self._require_evidence_absent(capture)
            self._require_body_insert_is_not_repair(capture.response_sha256)
            self._ensure_body(capture.response_sha256, capture.response_body)
            self._connection.execute(
                "INSERT INTO nar_market_odds_response_captures("
                f"{_CAPTURE_COLUMNS}) VALUES({','.join('?' for _ in range(27))})",
                self._capture_values(capture),
            )
            loaded = self._capture_by_id(capture.capture_id)
            if loaded != capture:
                raise _Integrity("published capture could not be reloaded exactly")
            self._connection.commit()
        except (_Conflict, _Integrity, _Validation):
            self._connection.rollback()
            raise
        except _sqlite3.Error as error:
            self._connection.rollback()
            raise _Integrity("market-odds capture archive write failed") from error
        except BaseException:
            self._connection.rollback()
            raise

    def load_capture(self, *, capture_id: str) -> _Capture | None:
        """Load one exact capture ID; None means only exact-key absence."""

        self._require_capture_id(capture_id)
        self._schema_gate()
        try:
            return self._capture_by_id(capture_id)
        except _Integrity:
            raise
        except _sqlite3.Error as error:
            raise _Integrity("market-odds capture archive read failed") from error

    def _capture_by_id(self, capture_id: str) -> _Capture | None:
        rows = self._connection.execute(
            f"SELECT {_CAPTURE_COLUMNS} FROM nar_market_odds_response_captures "
            "WHERE capture_id=?",
            (capture_id,),
        ).fetchall()
        if not rows:
            return None
        if len(rows) != 1:
            raise _Integrity("market-odds capture ID is duplicated")
        return self._reconstruct(rows[0])

    def _reconstruct(self, row: object) -> _Capture:
        try:
            values = tuple(row)
            if len(values) != 27:
                raise ValueError("wrong column count")
            (
                capture_id,
                schema_version,
                request_schema_version,
                request_identity,
                request_digest,
                page_kind,
                organization,
                source_system,
                method,
                origin,
                baba_code,
                race_date,
                race_no,
                canonical_url,
                effective_url,
                response_digest,
                charset,
                requested,
                observed,
                captured,
                status,
                content_type,
                content_encoding,
                http_date,
                etag,
                last_modified,
                content_length,
            ) = values
            if type(race_date) is not str:
                raise ValueError("race date is not text")
            request = _RequestIdentity(
                page_kind=_PageKind(page_kind),
                race_identity=_RaceIdentity(
                    baba_code=baba_code,
                    race_date=_date.fromisoformat(race_date),
                    race_no=race_no,
                ),
            )
            body = self._body(response_digest)
            capture_object = _Capture(
                request_identity=request,
                effective_url=effective_url,
                response_body=body,
                charset=charset,
                requested_at=self._stored_time(requested),
                observed_at=self._stored_time(observed),
                captured_at=self._stored_time(captured),
                http_status=status,
                content_type=self._stored_optional_text(content_type, "content_type"),
                content_encoding=self._stored_optional_text(
                    content_encoding,
                    "content_encoding",
                ),
                http_date=self._stored_optional_text(http_date, "http_date"),
                etag=self._stored_optional_text(etag, "etag"),
                last_modified=self._stored_optional_text(last_modified, "last_modified"),
                content_length=self._stored_length(content_length, body),
            )
        except _Integrity:
            raise
        except (_CaptureError, TypeError, ValueError, OverflowError) as error:
            raise _Integrity("stored market-odds capture violates its domain contract") from error
        if self._capture_values(capture_object) != values:
            raise _Integrity("stored market-odds metadata or derived identity differs")
        self._require_evidence_unique(capture_object)
        return capture_object

    def _body(self, digest: object) -> bytes:
        if type(digest) is not str or _SHA256.fullmatch(digest) is None:
            raise _Integrity("stored response digest is invalid")
        rows = self._connection.execute(
            "SELECT response_body,byte_length FROM nar_market_odds_response_bodies "
            "WHERE response_sha256=?",
            (digest,),
        ).fetchall()
        if len(rows) != 1:
            raise _Integrity("stored response body is missing or duplicated")
        body, byte_length = rows[0]
        if (
            type(body) is not bytes
            or not body
            or type(byte_length) is not int
            or byte_length != len(body)
        ):
            raise _Integrity("stored response body length or type is invalid")
        if _hashlib.sha256(body).hexdigest() != digest:
            raise _Integrity("stored response body digest is invalid")
        return body

    def _ensure_body(self, digest: str, body: bytes) -> None:
        rows = self._connection.execute(
            "SELECT response_body,byte_length FROM nar_market_odds_response_bodies "
            "WHERE response_sha256=?",
            (digest,),
        ).fetchall()
        if not rows:
            self._connection.execute(
                "INSERT INTO nar_market_odds_response_bodies("
                "response_sha256,response_body,byte_length) VALUES(?,?,?)",
                (digest, body, len(body)),
            )
            return
        if len(rows) != 1:
            raise _Integrity("stored response body identity is duplicated")
        stored, byte_length = rows[0]
        if (
            type(stored) is not bytes
            or not stored
            or type(byte_length) is not int
            or byte_length != len(stored)
        ):
            raise _Integrity("stored response body is corrupt")
        if _hashlib.sha256(stored).hexdigest() != digest:
            raise _Integrity("stored response body digest is corrupt")
        if stored != body:
            raise _Conflict("response digest has conflicting body bytes")

    def _require_body_insert_is_not_repair(self, digest: str) -> None:
        if self._connection.execute(
            "SELECT 1 FROM nar_market_odds_response_bodies WHERE response_sha256=?",
            (digest,),
        ).fetchone() is not None:
            return
        reference = self._connection.execute(
            "SELECT 1 FROM nar_market_odds_response_captures "
            "WHERE response_sha256=? LIMIT 1",
            (digest,),
        ).fetchone()
        if reference is not None:
            raise _Integrity("missing referenced response body must not be repaired")

    def _require_evidence_absent(self, capture: _Capture) -> None:
        rows = self._evidence_rows(capture)
        if len(rows) > 1:
            raise _Integrity("market-odds evidence tuple is duplicated")
        if rows:
            raise _Conflict("market-odds evidence tuple has a conflicting capture identity")

    def _require_evidence_unique(self, capture: _Capture) -> None:
        rows = self._evidence_rows(capture)
        if len(rows) != 1 or rows[0][0] != capture.capture_id:
            raise _Integrity("market-odds evidence tuple is not uniquely coherent")

    def _evidence_rows(self, capture: _Capture) -> list[object]:
        return self._connection.execute(
            """SELECT capture_id FROM nar_market_odds_response_captures
               WHERE request_identity_sha256=? AND response_sha256=?
               AND requested_at_utc=? AND observed_at_utc=? AND captured_at_utc=?""",
            (
                capture.request_identity.request_identity_sha256,
                capture.response_sha256,
                self._time(capture.requested_at),
                self._time(capture.observed_at),
                self._time(capture.captured_at),
            ),
        ).fetchall()

    def _validate_input(self, capture: _Capture) -> None:
        try:
            request = _RequestIdentity(
                page_kind=capture.request_identity.page_kind,
                race_identity=_RaceIdentity(
                    baba_code=capture.request_identity.race_identity.baba_code,
                    race_date=capture.request_identity.race_identity.race_date,
                    race_no=capture.request_identity.race_identity.race_no,
                ),
            )
            rebuilt = _Capture(
                request_identity=request,
                effective_url=capture.effective_url,
                response_body=capture.response_body,
                charset=capture.charset,
                requested_at=capture.requested_at,
                observed_at=capture.observed_at,
                captured_at=capture.captured_at,
                http_status=capture.http_status,
                content_type=capture.content_type,
                content_encoding=capture.content_encoding,
                http_date=capture.http_date,
                etag=capture.etag,
                last_modified=capture.last_modified,
                content_length=capture.content_length,
            )
        except _CaptureError as error:
            raise _Validation("capture violates its domain contract") from error
        if rebuilt != capture:
            raise _Validation("capture derived identity is inconsistent")

    def _foreign_keys(self) -> None:
        try:
            self._connection.execute("PRAGMA foreign_keys = ON")
            row = self._connection.execute("PRAGMA foreign_keys").fetchone()
        except _sqlite3.Error as error:
            raise _Validation("connection is not usable") from error
        if row is None or row[0] != 1:
            raise _Validation("foreign_keys could not be enabled")

    def _schema_gate(self) -> None:
        try:
            _schema.require_nar_market_odds_capture_archive_schema(self._connection)
        except (RuntimeError, _sqlite3.Error) as error:
            raise _Integrity("market-odds archive schema is missing or incompatible") from error

    @staticmethod
    def _require_capture_id(value: object) -> None:
        if type(value) is not str or _CAPTURE_ID.fullmatch(value) is None:
            raise _Validation("capture_id is invalid")

    @staticmethod
    def _time(value: _datetime) -> str:
        return value.astimezone(_timezone.utc).isoformat(timespec="microseconds")

    @staticmethod
    def _stored_time(value: object) -> _datetime:
        if type(value) is not str or len(value) != 32:
            raise _Integrity("stored UTC timestamp is invalid")
        try:
            parsed = _datetime.fromisoformat(value)
            if (
                parsed.tzinfo is None
                or parsed.utcoffset() != _timezone.utc.utcoffset(parsed)
                or parsed.astimezone(_timezone.utc).isoformat(timespec="microseconds") != value
            ):
                raise ValueError("timestamp is not canonical UTC")
        except (TypeError, ValueError, OverflowError) as error:
            raise _Integrity("stored UTC timestamp is invalid") from error
        return parsed.astimezone(_timezone.utc)

    @staticmethod
    def _stored_optional_text(value: object, name: str) -> str | None:
        if value is None:
            return None
        if type(value) is not str:
            raise _Integrity(f"stored {name} is invalid")
        return value

    @staticmethod
    def _stored_length(value: object, body: bytes) -> int | None:
        if value is None:
            return None
        if type(value) is not int or value < 0 or value != len(body):
            raise _Integrity("stored content_length is invalid")
        return value

    @classmethod
    def _capture_values(cls, capture: _Capture) -> tuple[object, ...]:
        request = capture.request_identity
        race = request.race_identity
        return (
            capture.capture_id,
            capture.schema_version,
            request.schema_version,
            request.request_identity,
            request.request_identity_sha256,
            request.page_kind.value,
            request.organization,
            request.source_system,
            request.method,
            request.official_origin,
            race.baba_code,
            race.race_date.isoformat(),
            race.race_no,
            request.canonical_request_url,
            capture.effective_url,
            capture.response_sha256,
            capture.charset,
            cls._time(capture.requested_at),
            cls._time(capture.observed_at),
            cls._time(capture.captured_at),
            capture.http_status,
            capture.content_type,
            capture.content_encoding,
            capture.http_date,
            capture.etag,
            capture.last_modified,
            capture.content_length,
        )


__all__ = ("SQLiteNARMarketOddsCaptureArchive",)


if "annotations" in globals():
    del annotations
