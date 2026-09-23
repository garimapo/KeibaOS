"""Exact append-only activation companion on the Phase99 SQLite database."""

from __future__ import annotations

import sqlite3

from scripts.simulation import nar_operational_timing_activation_archive_migration as schema
from scripts.simulation.nar_operational_timing_session_activation import (
    NAROperationalTimingMeasurementSessionActivationDeclaration as Declaration,
    NAROperationalTimingMeasurementSessionActivationVerificationReceipt as Verification,
    _ISSUANCE_MARKER,
)
from scripts.simulation.sqlite_nar_operational_timing_observability_archive import (
    SQLiteNAROperationalTimingObservabilityArchive,
    TimingArchiveConflict, TimingArchiveError,
)


class SQLiteNAROperationalTimingActivationArchive:
    """Caller-owned connection; no migration, clock, or acquisition side effects."""

    __slots__ = ("_connection", "_base")

    def __init__(self, *, connection: sqlite3.Connection) -> None:
        if type(connection) is not sqlite3.Connection or connection.in_transaction:
            raise TimingArchiveError("activation archive requires exact idle SQLite connection")
        schema.require_nar_operational_timing_activation_archive_schema(connection)
        self._connection = connection
        self._base = SQLiteNAROperationalTimingObservabilityArchive(connection=connection)

    def load_configuration(self, *, configuration_identity: str):
        schema.require_nar_operational_timing_activation_archive_schema(self._connection)
        return self._base.load_configuration(configuration_identity=configuration_identity)

    def load_session(self, *, session_identity: str):
        schema.require_nar_operational_timing_activation_archive_schema(self._connection)
        return self._base.load_session(session_identity=session_identity)

    def _row(self, table: str, column: str, identity: str) -> tuple[str, ...] | None:
        schema.require_nar_operational_timing_activation_archive_schema(self._connection)
        try:
            rows = self._connection.execute(
                f"SELECT * FROM {table} WHERE {column}=?", (identity,)
            ).fetchall()
        except sqlite3.Error as error:
            raise TimingArchiveError("activation archive read failed") from error
        if len(rows) > 1:
            raise TimingArchiveError("activation natural identity is duplicated")
        return tuple(rows[0]) if rows else None

    def load_declaration_for_session(self, *, session_identity: str) -> Declaration | None:
        row = self._row(schema.DECLARATIONS, "session_identity", session_identity)
        if row is None:
            return None
        try:
            value = Declaration.from_json(row[3])
            if (value.declaration_identity, value.session_identity,
                value.measurement_configuration_identity) != row[:3]:
                raise ValueError("declaration row contradicts content")
            session = self.load_session(session_identity=value.session_identity)
            if session is None or session.configuration.configuration_identity != value.measurement_configuration_identity:
                raise ValueError("declaration ancestry contradicts archived session")
            return value
        except (KeyError, TypeError, ValueError) as error:
            raise TimingArchiveError("stored activation declaration is corrupt") from error

    def load_verification_for_declaration(self, *, declaration_identity: str) -> Verification | None:
        row = self._row(schema.VERIFICATIONS, "declaration_identity", declaration_identity)
        if row is None:
            return None
        try:
            value = Verification.from_json(row[4])
            if (value.verification_identity, value.declaration_identity,
                value.session_identity, value.measurement_configuration_identity) != row[:4]:
                raise ValueError("verification row contradicts content")
            declaration = self.load_declaration_for_session(session_identity=value.session_identity)
            if (declaration is None or declaration.declaration_identity != value.declaration_identity
                    or declaration.measurement_configuration_identity != value.measurement_configuration_identity):
                raise ValueError("verification ancestry contradicts declaration")
            return value
        except (KeyError, TypeError, ValueError) as error:
            raise TimingArchiveError("stored activation verification is corrupt") from error

    def _save(self, *, table: str, natural_column: str, natural_identity: str,
              row: tuple[str, ...], columns: str) -> None:
        if self._connection.in_transaction:
            raise TimingArchiveError("activation writes require no caller transaction")
        schema.require_nar_operational_timing_activation_archive_schema(self._connection)
        try:
            self._connection.execute("BEGIN IMMEDIATE")
            existing = self._connection.execute(
                f"SELECT * FROM {table} WHERE {natural_column}=? OR identity=?",
                (natural_identity, row[0]),
            ).fetchall()
            if existing:
                if len(existing) != 1 or tuple(existing[0]) != row:
                    raise TimingArchiveConflict("immutable activation identity conflicts")
            else:
                values = ",".join("?" for _ in row)
                self._connection.execute(f"INSERT INTO {table}({columns}) VALUES({values})", row)
                if self._connection.execute(
                    f"SELECT * FROM {table} WHERE identity=?", (row[0],)
                ).fetchone() != row:
                    raise TimingArchiveError("activation insert did not reload exactly")
            self._connection.commit()
        except sqlite3.IntegrityError as error:
            self._connection.rollback()
            raise TimingArchiveConflict("activation parent or identity conflicts") from error
        except BaseException:
            self._connection.rollback()
            raise

    def save_declaration(self, *, declaration: Declaration,
                         _issuance_marker: object = None) -> None:
        if type(declaration) is not Declaration or _issuance_marker is not _ISSUANCE_MARKER:
            raise TimingArchiveError("declaration requires controlled issuance")
        if Declaration.from_json(declaration.canonical_bytes().decode("utf-8")) != declaration:
            raise TimingArchiveError("declaration content identity is contradictory")
        session = self.load_session(session_identity=declaration.session_identity)
        if session is None or session.configuration.configuration_identity != declaration.measurement_configuration_identity:
            raise TimingArchiveError("declaration requires exact archived session and configuration")
        row = (declaration.declaration_identity, declaration.session_identity,
               declaration.measurement_configuration_identity, declaration.canonical_bytes().decode("utf-8"))
        self._save(table=schema.DECLARATIONS, natural_column="session_identity",
                   natural_identity=declaration.session_identity, row=row,
                   columns="identity,session_identity,configuration_identity,payload_json")

    def save_verification_receipt(self, *, receipt: Verification,
                                  _issuance_marker: object = None) -> None:
        if type(receipt) is not Verification or _issuance_marker is not _ISSUANCE_MARKER:
            raise TimingArchiveError("verification requires controlled issuance")
        if Verification.from_json(receipt.canonical_bytes().decode("utf-8")) != receipt:
            raise TimingArchiveError("verification content identity is contradictory")
        declaration = self.load_declaration_for_session(session_identity=receipt.session_identity)
        if (declaration is None or declaration.declaration_identity != receipt.declaration_identity
                or declaration.measurement_configuration_identity != receipt.measurement_configuration_identity):
            raise TimingArchiveError("verification requires exact archived declaration")
        row = (receipt.verification_identity, receipt.declaration_identity, receipt.session_identity,
               receipt.measurement_configuration_identity, receipt.canonical_bytes().decode("utf-8"))
        self._save(table=schema.VERIFICATIONS, natural_column="declaration_identity",
                   natural_identity=receipt.declaration_identity, row=row,
                   columns="identity,declaration_identity,session_identity,configuration_identity,payload_json")
