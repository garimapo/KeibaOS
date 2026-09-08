"""Append-only SQLite archive for exact NAR daily-target evidence captures."""

from __future__ import annotations

from datetime import datetime as _datetime, timezone as _timezone
import hashlib as _hashlib
import re as _re
import sqlite3 as _sqlite3

from scripts.simulation import nar_daily_target_evidence_archive_migration as _schema
from scripts.simulation.nar_historical_daily_target_bootstrap_capture import (
    NARMonthlyConveneInfoBootstrapCaptureError as _SupplierCaptureError,
    NARMonthlyConveneInfoBootstrapPageKind as _SupplierPageKind,
    NARMonthlyConveneInfoBootstrapSupplierCapture as _SupplierCapture,
)
from scripts.simulation.nar_historical_daily_target_capture import (
    NARHistoricalDailyTargetCaptureError as _DailyCaptureError,
    NARHistoricalDailyTargetPageKind as _DailyPageKind,
    NARHistoricalDailyTargetRequestIdentity as _DailyRequestIdentity,
    NARHistoricalDailyTargetResponseCapture as _DailyCapture,
)
from scripts.simulation.repositories.errors import (
    RepositoryConflictError as _Conflict,
    RepositoryDataIntegrityError as _Integrity,
    RepositoryValidationError as _Validation,
)


_SUPPLIER_ID = _re.compile(r"nar-monthly-bootstrap-capture-v1:[0-9a-f]{64}\Z")
_DAILY_ID = _re.compile(r"nar-daily-target-capture-v1:[0-9a-f]{64}\Z")
_SHA256 = _re.compile(r"[0-9a-f]{64}\Z")
_SUPPLIER_COLUMNS = """capture_id,schema_version,page_kind,canonical_request_url,effective_url,
response_sha256,charset,requested_at_utc,observed_at_utc,stored_at_utc,http_status,
content_type,content_encoding,content_length"""
_DAILY_COLUMNS = """capture_id,schema_version,page_kind,request_schema_version,request_identity,
request_identity_sha256,request_method,request_official_origin,official_supplied_request_material,
resolved_request_url,supplier_evidence_identity,request_target_date,request_baba_code,
request_target_year,request_target_month,response_sha256,charset,requested_at_utc,
observed_at_utc,stored_at_utc,http_status,content_type,content_encoding,http_date,etag,
last_modified,content_length"""


class SQLiteNARDailyTargetEvidenceArchive:
    """Connection-injected exact-ID archive for the two approved capture families."""

    __slots__ = ("_connection",)

    def __init__(self, *, connection: _sqlite3.Connection) -> None:
        if type(connection) is not _sqlite3.Connection:
            raise _Validation("connection must be exact sqlite3.Connection")
        if connection.in_transaction:
            raise _Validation("repository construction requires no active transaction")
        self._connection = connection
        self._foreign_keys()
        self._schema_gate()

    def save_supplier_capture(self, *, capture: _SupplierCapture) -> None:
        """Atomically insert one immutable bootstrap supplier capture."""

        if type(capture) is not _SupplierCapture:
            raise _Validation("capture must be exact NARMonthlyConveneInfoBootstrapSupplierCapture")
        self._require_input_identity(capture.capture_id, _SUPPLIER_ID, capture.response_sha256, capture.response_body)
        self._save(capture=capture, supplier=True)

    def load_supplier_capture(self, *, capture_id: str) -> _SupplierCapture | None:
        """Load one exact supplier capture ID; None means only exact-key absence."""

        self._require_lookup_id(capture_id, _SUPPLIER_ID)
        self._schema_gate()
        try:
            return self._supplier_by_id(capture_id)
        except _Integrity:
            raise
        except _sqlite3.Error as error:
            raise _Integrity("daily-target supplier archive read failed") from error

    def save_capture(self, *, capture: _DailyCapture) -> None:
        """Atomically insert one immutable MonthlyConveneInfo or RaceList capture."""

        if type(capture) is not _DailyCapture:
            raise _Validation("capture must be exact NARHistoricalDailyTargetResponseCapture")
        self._require_input_identity(capture.capture_id, _DAILY_ID, capture.response_sha256, capture.response_body)
        self._save(capture=capture, supplier=False)

    def load_capture(self, *, capture_id: str) -> _DailyCapture | None:
        """Load one exact daily-target capture ID; None means only exact-key absence."""

        self._require_lookup_id(capture_id, _DAILY_ID)
        self._schema_gate()
        try:
            return self._daily_by_id(capture_id)
        except _Integrity:
            raise
        except _sqlite3.Error as error:
            raise _Integrity("daily-target response archive read failed") from error

    def _save(self, *, capture: _SupplierCapture | _DailyCapture, supplier: bool) -> None:
        if self._connection.in_transaction:
            raise _Validation("repository writes require no active transaction")
        self._foreign_keys()
        self._schema_gate()
        try:
            self._connection.execute("BEGIN IMMEDIATE")
            existing = (
                self._supplier_by_id(capture.capture_id)
                if supplier
                else self._daily_by_id(capture.capture_id)
            )
            if existing is not None:
                if existing != capture:
                    raise _Conflict("capture identity already has different immutable content")
                self._connection.commit()
                return
            if supplier:
                assert type(capture) is _SupplierCapture
                self._validate_supplier_input(capture)
                self._require_supplier_evidence_absent(capture)
            else:
                assert type(capture) is _DailyCapture
                self._validate_daily_input(capture)
                self._require_daily_evidence_absent(capture)
            self._require_body_insert_is_not_repair(capture.response_sha256)
            self._ensure_body(capture.response_sha256, capture.response_body)
            if supplier:
                self._insert_supplier(capture)
            else:
                self._insert_daily(capture)
            self._connection.commit()
        except (_Conflict, _Integrity, _Validation):
            self._connection.rollback()
            raise
        except _sqlite3.Error as error:
            self._connection.rollback()
            raise _Integrity("daily-target evidence archive write failed") from error
        except BaseException:
            self._connection.rollback()
            raise

    def _insert_supplier(self, capture: _SupplierCapture) -> None:
        self._connection.execute(
            f"INSERT INTO nar_daily_target_supplier_captures({_SUPPLIER_COLUMNS}) VALUES({','.join('?' for _ in range(14))})",
            self._supplier_values(capture),
        )

    def _insert_daily(self, capture: _DailyCapture) -> None:
        self._connection.execute(
            f"INSERT INTO nar_daily_target_response_captures({_DAILY_COLUMNS}) VALUES({','.join('?' for _ in range(27))})",
            self._daily_values(capture),
        )

    def _supplier_by_id(self, capture_id: str) -> _SupplierCapture | None:
        rows = self._connection.execute(
            f"SELECT {_SUPPLIER_COLUMNS} FROM nar_daily_target_supplier_captures WHERE capture_id=?",
            (capture_id,),
        ).fetchall()
        if not rows:
            return None
        if len(rows) != 1:
            raise _Integrity("supplier capture ID is duplicated")
        return self._reconstruct_supplier(rows[0])

    def _daily_by_id(self, capture_id: str) -> _DailyCapture | None:
        rows = self._connection.execute(
            f"SELECT {_DAILY_COLUMNS} FROM nar_daily_target_response_captures WHERE capture_id=?",
            (capture_id,),
        ).fetchall()
        if not rows:
            return None
        if len(rows) != 1:
            raise _Integrity("daily-target capture ID is duplicated")
        return self._reconstruct_daily(rows[0])

    def _reconstruct_supplier(self, row: object) -> _SupplierCapture:
        try:
            values = tuple(row)
            if len(values) != 14:
                raise ValueError("wrong column count")
            (
                capture_id, version, kind, canonical_url, effective_url, digest, charset,
                requested, observed, stored, status, content_type, encoding, content_length,
            ) = values
            body = self._body(digest)
            capture = _SupplierCapture(
                page_kind=_SupplierPageKind(kind),
                canonical_request_url=canonical_url,
                effective_url=effective_url,
                response_body=body,
                charset=charset,
                requested_at=self._stored_time(requested),
                observed_at=self._stored_time(observed),
                stored_at=self._stored_time(stored),
                http_status=status,
                content_type=content_type,
                content_encoding=self._stored_optional_text(encoding, "content_encoding"),
                content_length=self._stored_length(content_length, body),
            )
        except _Integrity:
            raise
        except (_SupplierCaptureError, TypeError, ValueError, OverflowError) as error:
            raise _Integrity("stored supplier capture violates its domain contract") from error
        if self._supplier_values(capture) != values:
            raise _Integrity("stored supplier capture metadata or derived identity differs")
        self._require_supplier_evidence_unique(capture)
        return capture

    def _reconstruct_daily(self, row: object) -> _DailyCapture:
        try:
            values = tuple(row)
            if len(values) != 27:
                raise ValueError("wrong column count")
            (
                capture_id, version, kind, request_version, request_identity, request_digest,
                method, origin, raw_material, resolved_url, supplier_identity, target_date,
                baba_code, target_year, target_month, response_digest, charset, requested,
                observed, stored, status, content_type, encoding, http_date, etag,
                last_modified, content_length,
            ) = values
            if type(raw_material) is not bytes:
                raise ValueError("request material is not BLOB")
            request = _DailyRequestIdentity(
                page_kind=_DailyPageKind(kind),
                official_supplied_request_material=raw_material,
                resolved_request_url=resolved_url,
                supplier_evidence_identity=supplier_identity,
            )
            body = self._body(response_digest)
            capture = _DailyCapture(
                request_identity=request,
                response_body=body,
                charset=charset,
                requested_at=self._stored_time(requested),
                observed_at=self._stored_time(observed),
                stored_at=self._stored_time(stored),
                http_status=status,
                content_type=self._stored_optional_text(content_type, "content_type"),
                content_encoding=self._stored_optional_text(encoding, "content_encoding"),
                http_date=self._stored_optional_text(http_date, "http_date"),
                etag=self._stored_optional_text(etag, "etag"),
                last_modified=self._stored_optional_text(last_modified, "last_modified"),
                content_length=self._stored_length(content_length, body),
            )
        except _Integrity:
            raise
        except (_DailyCaptureError, TypeError, ValueError, OverflowError) as error:
            raise _Integrity("stored daily-target capture violates its domain contract") from error
        if self._daily_values(capture) != values:
            raise _Integrity("stored daily-target capture metadata or derived identity differs")
        self._require_daily_evidence_unique(capture)
        return capture

    def _body(self, digest: object) -> bytes:
        if type(digest) is not str or _SHA256.fullmatch(digest) is None:
            raise _Integrity("stored response digest is invalid")
        rows = self._connection.execute(
            "SELECT response_body,byte_length FROM nar_daily_target_evidence_bodies WHERE response_sha256=?",
            (digest,),
        ).fetchall()
        if len(rows) != 1:
            raise _Integrity("stored response body is missing or duplicated")
        body, length = rows[0]
        if type(body) is not bytes or type(length) is not int or length != len(body) or not body:
            raise _Integrity("stored response body length or type is invalid")
        if _hashlib.sha256(body).hexdigest() != digest:
            raise _Integrity("stored response body digest is invalid")
        return body

    def _ensure_body(self, digest: str, body: bytes) -> None:
        rows = self._connection.execute(
            "SELECT response_body,byte_length FROM nar_daily_target_evidence_bodies WHERE response_sha256=?",
            (digest,),
        ).fetchall()
        if not rows:
            self._connection.execute(
                "INSERT INTO nar_daily_target_evidence_bodies(response_sha256,response_body,byte_length) VALUES(?,?,?)",
                (digest, body, len(body)),
            )
            return
        if len(rows) != 1:
            raise _Integrity("stored response body identity is duplicated")
        stored, length = rows[0]
        if type(stored) is not bytes or type(length) is not int or length != len(stored):
            raise _Integrity("stored response body is corrupt")
        if _hashlib.sha256(stored).hexdigest() != digest:
            raise _Integrity("stored response body digest is corrupt")
        if stored != body:
            raise _Conflict("response digest has conflicting body bytes")

    def _require_body_insert_is_not_repair(self, digest: str) -> None:
        if self._connection.execute(
            "SELECT 1 FROM nar_daily_target_evidence_bodies WHERE response_sha256=?", (digest,)
        ).fetchone() is not None:
            return
        supplier = self._connection.execute(
            "SELECT 1 FROM nar_daily_target_supplier_captures WHERE response_sha256=? LIMIT 1", (digest,)
        ).fetchone()
        daily = self._connection.execute(
            "SELECT 1 FROM nar_daily_target_response_captures WHERE response_sha256=? LIMIT 1", (digest,)
        ).fetchone()
        if supplier is not None or daily is not None:
            raise _Integrity("missing referenced response body must not be repaired")

    def _require_supplier_evidence_absent(self, capture: _SupplierCapture) -> None:
        rows = self._supplier_evidence_rows(capture)
        if len(rows) > 1:
            raise _Integrity("supplier evidence tuple is duplicated")
        if rows:
            raise _Integrity("supplier evidence tuple has an inconsistent capture identity")

    def _require_supplier_evidence_unique(self, capture: _SupplierCapture) -> None:
        rows = self._supplier_evidence_rows(capture)
        if len(rows) != 1 or rows[0][0] != capture.capture_id:
            raise _Integrity("supplier evidence tuple is not uniquely coherent")

    def _supplier_evidence_rows(self, capture: _SupplierCapture) -> list[object]:
        return self._connection.execute(
            """SELECT capture_id FROM nar_daily_target_supplier_captures
               WHERE page_kind=? AND canonical_request_url=? AND response_sha256=? AND observed_at_utc=?""",
            (
                capture.page_kind.value,
                capture.canonical_request_url,
                capture.response_sha256,
                self._time(capture.observed_at),
            ),
        ).fetchall()

    def _require_daily_evidence_absent(self, capture: _DailyCapture) -> None:
        rows = self._daily_evidence_rows(capture)
        if len(rows) > 1:
            raise _Integrity("daily-target evidence tuple is duplicated")
        if rows:
            raise _Integrity("daily-target evidence tuple has an inconsistent capture identity")

    def _require_daily_evidence_unique(self, capture: _DailyCapture) -> None:
        rows = self._daily_evidence_rows(capture)
        if len(rows) != 1 or rows[0][0] != capture.capture_id:
            raise _Integrity("daily-target evidence tuple is not uniquely coherent")

    def _daily_evidence_rows(self, capture: _DailyCapture) -> list[object]:
        return self._connection.execute(
            """SELECT capture_id FROM nar_daily_target_response_captures
               WHERE request_identity_sha256=? AND response_sha256=? AND observed_at_utc=?""",
            (
                capture.request_identity.request_identity_sha256,
                capture.response_sha256,
                self._time(capture.observed_at),
            ),
        ).fetchall()

    def _validate_supplier_input(self, capture: _SupplierCapture) -> None:
        try:
            rebuilt = _SupplierCapture(
                page_kind=capture.page_kind,
                canonical_request_url=capture.canonical_request_url,
                effective_url=capture.effective_url,
                response_body=capture.response_body,
                charset=capture.charset,
                requested_at=capture.requested_at,
                observed_at=capture.observed_at,
                stored_at=capture.stored_at,
                http_status=capture.http_status,
                content_type=capture.content_type,
                content_encoding=capture.content_encoding,
                content_length=capture.content_length,
            )
        except _SupplierCaptureError as error:
            raise _Validation("supplier capture violates its domain contract") from error
        if rebuilt != capture:
            raise _Validation("supplier capture derived identity is inconsistent")

    def _validate_daily_input(self, capture: _DailyCapture) -> None:
        try:
            request = _DailyRequestIdentity(
                page_kind=capture.request_identity.page_kind,
                official_supplied_request_material=capture.request_identity.official_supplied_request_material,
                resolved_request_url=capture.request_identity.resolved_request_url,
                supplier_evidence_identity=capture.request_identity.supplier_evidence_identity,
            )
            rebuilt = _DailyCapture(
                request_identity=request,
                response_body=capture.response_body,
                charset=capture.charset,
                requested_at=capture.requested_at,
                observed_at=capture.observed_at,
                stored_at=capture.stored_at,
                http_status=capture.http_status,
                content_type=capture.content_type,
                content_encoding=capture.content_encoding,
                http_date=capture.http_date,
                etag=capture.etag,
                last_modified=capture.last_modified,
                content_length=capture.content_length,
            )
        except _DailyCaptureError as error:
            raise _Validation("daily-target capture violates its domain contract") from error
        if rebuilt != capture:
            raise _Validation("daily-target capture derived identity is inconsistent")

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
            _schema.require_nar_daily_target_evidence_archive_schema(self._connection)
        except (RuntimeError, _sqlite3.Error) as error:
            raise _Integrity("daily-target evidence archive schema is missing or incompatible") from error

    @staticmethod
    def _require_lookup_id(value: object, pattern: _re.Pattern[str]) -> None:
        if type(value) is not str or pattern.fullmatch(value) is None:
            raise _Validation("capture_id is invalid")

    @staticmethod
    def _require_input_identity(capture_id: object, pattern: _re.Pattern[str], digest: object, body: object) -> None:
        if type(capture_id) is not str or pattern.fullmatch(capture_id) is None:
            raise _Validation("capture identity is invalid")
        if type(digest) is not str or _SHA256.fullmatch(digest) is None:
            raise _Validation("response digest is invalid")
        if type(body) is not bytes or not body or _hashlib.sha256(body).hexdigest() != digest:
            raise _Validation("capture response_body digest is invalid")

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
    def _supplier_values(cls, capture: _SupplierCapture) -> tuple[object, ...]:
        return (
            capture.capture_id,
            capture.schema_version,
            capture.page_kind.value,
            capture.canonical_request_url,
            capture.effective_url,
            capture.response_sha256,
            capture.charset,
            cls._time(capture.requested_at),
            cls._time(capture.observed_at),
            cls._time(capture.stored_at),
            capture.http_status,
            capture.content_type,
            capture.content_encoding,
            capture.content_length,
        )

    @classmethod
    def _daily_values(cls, capture: _DailyCapture) -> tuple[object, ...]:
        request = capture.request_identity
        return (
            capture.capture_id,
            capture.schema_version,
            request.page_kind.value,
            request.schema_version,
            request.request_identity,
            request.request_identity_sha256,
            request.method,
            request.official_origin,
            request.official_supplied_request_material,
            request.resolved_request_url,
            request.supplier_evidence_identity,
            request.target_date.isoformat() if request.target_date is not None else None,
            request.baba_code,
            request.target_year,
            request.target_month,
            capture.response_sha256,
            capture.charset,
            cls._time(capture.requested_at),
            cls._time(capture.observed_at),
            cls._time(capture.stored_at),
            capture.http_status,
            capture.content_type,
            capture.content_encoding,
            capture.http_date,
            capture.etag,
            capture.last_modified,
            capture.content_length,
        )


if "annotations" in globals():
    del annotations
