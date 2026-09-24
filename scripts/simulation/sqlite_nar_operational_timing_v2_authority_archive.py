"""Connection-injected append-only V2 timing authority archive."""

from __future__ import annotations

import sqlite3

from scripts.simulation import nar_operational_timing_v2_authority_archive_migration as schema
from scripts.simulation.nar_operational_timing_observability_v2 import (
    NAROperationalTimingMeasurementConfigurationV2 as Configuration,
    NAROperationalTimingMeasurementSessionV2 as Session,
)
from scripts.simulation.nar_operational_timing_session_activation_v2 import (
    NAROperationalTimingMeasurementSessionActivationDeclarationV2 as Declaration,
    NAROperationalTimingMeasurementSessionActivationVerificationReceiptV2 as Verification,
    _ISSUANCE_MARKER,
)
from scripts.simulation.sqlite_nar_operational_timing_observability_archive import (
    TimingArchiveConflict, TimingArchiveError,
)


class SQLiteNAROperationalTimingV2AuthorityArchive:
    """Never migrates, samples a clock, or publishes execution/observation rows."""

    __slots__ = ("_connection",)

    def __init__(self, *, connection: sqlite3.Connection) -> None:
        if type(connection) is not sqlite3.Connection or connection.in_transaction:
            raise TimingArchiveError("V2 archive requires exact idle caller-owned connection")
        schema.require_nar_operational_timing_v2_authority_archive_compatible_schema(connection)
        self._connection = connection

    def _row(self, table: str, column: str, identity: str) -> tuple[str, ...] | None:
        schema.require_nar_operational_timing_v2_authority_archive_compatible_schema(self._connection)
        try:
            rows = self._connection.execute(
                f"SELECT * FROM {table} WHERE {column}=?", (identity,)
            ).fetchall()
        except sqlite3.Error as error:
            raise TimingArchiveError("V2 authority read failed") from error
        if len(rows) > 1:
            raise TimingArchiveError("V2 authority natural identity is duplicated")
        return tuple(rows[0]) if rows else None

    def _save(self, *, table: str, natural_column: str, natural_identity: str,
              row: tuple[str, ...], columns: str) -> None:
        if self._connection.in_transaction:
            raise TimingArchiveError("V2 authority writes require no caller transaction")
        schema.require_nar_operational_timing_v2_authority_archive_compatible_schema(self._connection)
        try:
            self._connection.execute("BEGIN IMMEDIATE")
            existing = self._connection.execute(
                f"SELECT * FROM {table} WHERE {natural_column}=? OR identity=?",
                (natural_identity, row[0]),
            ).fetchall()
            if existing:
                if len(existing) != 1 or tuple(existing[0]) != row:
                    raise TimingArchiveConflict("immutable V2 authority identity conflicts")
            else:
                values = ",".join("?" for _ in row)
                self._connection.execute(f"INSERT INTO {table}({columns}) VALUES({values})", row)
                if tuple(self._connection.execute(
                    f"SELECT * FROM {table} WHERE identity=?", (row[0],)
                ).fetchone()) != row:
                    raise TimingArchiveError("V2 authority insert did not reload exactly")
            self._connection.commit()
        except sqlite3.IntegrityError as error:
            self._connection.rollback()
            raise TimingArchiveConflict("V2 authority parent or identity conflicts") from error
        except BaseException:
            self._connection.rollback()
            raise

    def save_configuration(self, *, configuration: Configuration) -> None:
        if type(configuration) is not Configuration or Configuration.from_json(
            configuration.canonical_bytes().decode("utf-8")) != configuration:
            raise TimingArchiveError("V2 configuration content is contradictory")
        row = (configuration.configuration_identity, configuration.canonical_bytes().decode("utf-8"))
        self._save(table=schema.CONFIGS, natural_column="identity", natural_identity=row[0],
                   row=row, columns="identity,payload_json")

    def load_configuration(self, *, configuration_identity: str) -> Configuration | None:
        row = self._row(schema.CONFIGS, "identity", configuration_identity)
        if row is None:
            return None
        try:
            result = Configuration.from_json(row[1])
            if result.configuration_identity != row[0]:
                raise ValueError("V2 configuration identity differs")
            return result
        except (KeyError, TypeError, ValueError) as error:
            raise TimingArchiveError("stored V2 configuration is corrupt") from error

    def save_session(self, *, session: Session) -> None:
        if type(session) is not Session or Session.from_json(
            session.canonical_bytes().decode("utf-8"), session.configuration) != session:
            raise TimingArchiveError("V2 session content is contradictory")
        if self.load_configuration(configuration_identity=session.configuration.configuration_identity) != session.configuration:
            raise TimingArchiveError("V2 session configuration is not archived exactly")
        row = (session.session_identity, session.configuration.configuration_identity,
               session.canonical_bytes().decode("utf-8"))
        self._save(table=schema.SESSIONS, natural_column="identity", natural_identity=row[0],
                   row=row, columns="identity,configuration_identity,payload_json")

    def load_session(self, *, session_identity: str) -> Session | None:
        row = self._row(schema.SESSIONS, "identity", session_identity)
        if row is None:
            return None
        configuration = self.load_configuration(configuration_identity=row[1])
        if configuration is None:
            raise TimingArchiveError("V2 session configuration is absent")
        try:
            result = Session.from_json(row[2], configuration)
            if result.session_identity != row[0]:
                raise ValueError("V2 session identity differs")
            return result
        except (KeyError, TypeError, ValueError) as error:
            raise TimingArchiveError("stored V2 session is corrupt") from error

    def save_declaration(self, *, declaration: Declaration, _issuance_marker: object = None) -> None:
        if type(declaration) is not Declaration or _issuance_marker is not _ISSUANCE_MARKER:
            raise TimingArchiveError("V2 declaration requires controlled issuance")
        if Declaration.from_json(declaration.canonical_bytes().decode("utf-8")) != declaration:
            raise TimingArchiveError("V2 declaration content is contradictory")
        session = self.load_session(session_identity=declaration.session_identity)
        if session is None or session.configuration.configuration_identity != declaration.measurement_configuration_identity:
            raise TimingArchiveError("V2 declaration requires exact archived session")
        row = (declaration.declaration_identity, declaration.session_identity,
               declaration.measurement_configuration_identity, declaration.canonical_bytes().decode("utf-8"))
        self._save(table=schema.DECLARATIONS, natural_column="session_identity",
                   natural_identity=declaration.session_identity, row=row,
                   columns="identity,session_identity,configuration_identity,payload_json")

    def load_declaration_for_session(self, *, session_identity: str) -> Declaration | None:
        row = self._row(schema.DECLARATIONS, "session_identity", session_identity)
        if row is None:
            return None
        try:
            result = Declaration.from_json(row[3])
            if (result.declaration_identity, result.session_identity,
                    result.measurement_configuration_identity) != row[:3]:
                raise ValueError("V2 declaration row contradicts content")
            session = self.load_session(session_identity=result.session_identity)
            if session is None or session.configuration.configuration_identity != result.measurement_configuration_identity:
                raise ValueError("V2 declaration ancestry contradicts session")
            return result
        except (KeyError, TypeError, ValueError) as error:
            raise TimingArchiveError("stored V2 declaration is corrupt") from error

    def save_verification_receipt(self, *, receipt: Verification, _issuance_marker: object = None) -> None:
        if type(receipt) is not Verification or _issuance_marker is not _ISSUANCE_MARKER:
            raise TimingArchiveError("V2 verification requires controlled issuance")
        if Verification.from_json(receipt.canonical_bytes().decode("utf-8")) != receipt:
            raise TimingArchiveError("V2 verification content is contradictory")
        declaration = self.load_declaration_for_session(session_identity=receipt.session_identity)
        if (declaration is None or declaration.declaration_identity != receipt.declaration_identity
                or declaration.measurement_configuration_identity != receipt.measurement_configuration_identity):
            raise TimingArchiveError("V2 verification requires exact archived declaration")
        row = (receipt.verification_identity, receipt.declaration_identity, receipt.session_identity,
               receipt.measurement_configuration_identity, receipt.canonical_bytes().decode("utf-8"))
        self._save(table=schema.VERIFICATIONS, natural_column="declaration_identity",
                   natural_identity=receipt.declaration_identity, row=row,
                   columns="identity,declaration_identity,session_identity,configuration_identity,payload_json")

    def load_verification_for_declaration(self, *, declaration_identity: str) -> Verification | None:
        row = self._row(schema.VERIFICATIONS, "declaration_identity", declaration_identity)
        if row is None:
            return None
        try:
            result = Verification.from_json(row[4])
            if (result.verification_identity, result.declaration_identity,
                    result.session_identity, result.measurement_configuration_identity) != row[:4]:
                raise ValueError("V2 verification row contradicts content")
            declaration = self.load_declaration_for_session(session_identity=result.session_identity)
            if (declaration is None or declaration.declaration_identity != result.declaration_identity
                    or declaration.measurement_configuration_identity != result.measurement_configuration_identity):
                raise ValueError("V2 verification ancestry contradicts declaration")
            return result
        except (KeyError, TypeError, ValueError) as error:
            raise TimingArchiveError("stored V2 verification is corrupt") from error
