"""Connection-injected append-only archive for Phase99 timing and freeze proof."""

from __future__ import annotations

import sqlite3

from scripts.simulation import nar_operational_timing_observability_archive_migration as schema
from scripts.simulation.nar_operational_timing_activation_archive_migration import (
    require_nar_operational_timing_archive_compatible_schema,
)
from scripts.simulation.historical_input_snapshot_freeze_receipt import (
    HistoricalInputSnapshotFreezeReceipt, _ISSUANCE_MARKER,
)
from scripts.simulation.nar_operational_timing_observability import (
    NAROperationalTimingAttempt, NAROperationalTimingMeasurementConfiguration,
    NAROperationalTimingMeasurementSession, NAROperationalTimingTerminalObservation,
)


class TimingArchiveError(ValueError):
    """Archive schema, content, reference, or publication is invalid."""


class TimingArchiveConflict(TimingArchiveError):
    """An immutable natural identity already has different content."""


class SQLiteNAROperationalTimingObservabilityArchive:
    __slots__ = ("_connection",)

    def __init__(self, *, connection: sqlite3.Connection) -> None:
        if type(connection) is not sqlite3.Connection or connection.in_transaction:
            raise TimingArchiveError("archive requires exact idle caller-owned SQLite connection")
        self._connection = connection
        require_nar_operational_timing_archive_compatible_schema(connection)

    def _read(self, table: str, identity: str) -> tuple[object, ...] | None:
        require_nar_operational_timing_archive_compatible_schema(self._connection)
        try:
            rows = self._connection.execute(f"SELECT * FROM {table} WHERE identity=?", (identity,)).fetchall()
        except sqlite3.Error as error:
            raise TimingArchiveError("archive read failed") from error
        if len(rows) > 1:
            raise TimingArchiveError("archive identity is duplicated")
        return tuple(rows[0]) if rows else None

    def _save(self, table: str, identity: str, payload: bytes,
              parent_column: str | None = None, parent_identity: str | None = None) -> None:
        if self._connection.in_transaction:
            raise TimingArchiveError("archive writes require no caller transaction")
        require_nar_operational_timing_archive_compatible_schema(self._connection)
        encoded = payload.decode("utf-8")
        try:
            self._connection.execute("BEGIN IMMEDIATE")
            existing = self._connection.execute(f"SELECT * FROM {table} WHERE identity=?", (identity,)).fetchone()
            expected = (identity, encoded) if parent_column is None else (identity, parent_identity, encoded)
            if existing is not None:
                if tuple(existing) != expected:
                    raise TimingArchiveConflict("immutable identity has conflicting content")
            else:
                if parent_column is None:
                    self._connection.execute(f"INSERT INTO {table}(identity,payload_json) VALUES(?,?)", expected)
                else:
                    self._connection.execute(
                        f"INSERT INTO {table}(identity,{parent_column},payload_json) VALUES(?,?,?)", expected)
                if tuple(self._connection.execute(f"SELECT * FROM {table} WHERE identity=?", (identity,)).fetchone()) != expected:
                    raise TimingArchiveError("archive insert could not reload exactly")
            self._connection.commit()
        except sqlite3.IntegrityError as error:
            self._connection.rollback()
            raise TimingArchiveConflict("archive natural identity or parent conflicts") from error
        except BaseException:
            self._connection.rollback()
            raise

    def save_configuration(self, *, configuration: NAROperationalTimingMeasurementConfiguration) -> None:
        if type(configuration) is not NAROperationalTimingMeasurementConfiguration:
            raise TimingArchiveError("configuration type is invalid")
        if NAROperationalTimingMeasurementConfiguration.from_json(configuration.canonical_bytes().decode()) != configuration:
            raise TimingArchiveError("configuration content identity is contradictory")
        self._save(schema.CONFIGS, configuration.configuration_identity, configuration.canonical_bytes())

    def load_configuration(self, *, configuration_identity: str) -> NAROperationalTimingMeasurementConfiguration | None:
        row = self._read(schema.CONFIGS, configuration_identity)
        if row is None:
            return None
        try:
            result = NAROperationalTimingMeasurementConfiguration.from_json(row[1])
            if result.configuration_identity != row[0]:
                raise ValueError("configuration identity differs")
            return result
        except (KeyError, TypeError, ValueError) as error:
            raise TimingArchiveError("stored configuration is corrupt") from error

    def save_session(self, *, session: NAROperationalTimingMeasurementSession) -> None:
        if type(session) is not NAROperationalTimingMeasurementSession:
            raise TimingArchiveError("session type is invalid")
        if NAROperationalTimingMeasurementSession.from_json(session.canonical_bytes().decode(), session.configuration) != session:
            raise TimingArchiveError("session content identity is contradictory")
        if self.load_configuration(configuration_identity=session.configuration.configuration_identity) != session.configuration:
            raise TimingArchiveError("session configuration is not archived exactly")
        self._save(schema.SESSIONS, session.session_identity, session.canonical_bytes(),
                   "configuration_identity", session.configuration.configuration_identity)

    def load_session(self, *, session_identity: str) -> NAROperationalTimingMeasurementSession | None:
        row = self._read(schema.SESSIONS, session_identity)
        if row is None:
            return None
        configuration = self.load_configuration(configuration_identity=row[1])
        if configuration is None:
            raise TimingArchiveError("session configuration is absent")
        try:
            result = NAROperationalTimingMeasurementSession.from_json(row[2], configuration)
            if result.session_identity != row[0]:
                raise ValueError("session identity differs")
            return result
        except (KeyError, TypeError, ValueError) as error:
            raise TimingArchiveError("stored session is corrupt") from error

    def save_attempt(self, *, attempt: NAROperationalTimingAttempt) -> None:
        if type(attempt) is not NAROperationalTimingAttempt:
            raise TimingArchiveError("attempt type is invalid")
        if NAROperationalTimingAttempt.from_json(attempt.canonical_bytes().decode(), attempt.session) != attempt:
            raise TimingArchiveError("attempt content identity is contradictory")
        if self.load_session(session_identity=attempt.session.session_identity) != attempt.session:
            raise TimingArchiveError("attempt session is not archived exactly")
        self._save(schema.ATTEMPTS, attempt.attempt_identity, attempt.canonical_bytes(),
                   "session_identity", attempt.session.session_identity)

    def load_attempt(self, *, attempt_identity: str) -> NAROperationalTimingAttempt | None:
        row = self._read(schema.ATTEMPTS, attempt_identity)
        if row is None:
            return None
        session = self.load_session(session_identity=row[1])
        if session is None:
            raise TimingArchiveError("attempt session is absent")
        try:
            result = NAROperationalTimingAttempt.from_json(row[2], session)
            if result.attempt_identity != row[0]:
                raise ValueError("attempt identity differs")
            return result
        except (KeyError, TypeError, ValueError) as error:
            raise TimingArchiveError("stored attempt is corrupt") from error

    def save_terminal(self, *, observation: NAROperationalTimingTerminalObservation) -> None:
        if type(observation) is not NAROperationalTimingTerminalObservation:
            raise TimingArchiveError("terminal type is invalid")
        if NAROperationalTimingTerminalObservation.from_json(observation.canonical_bytes().decode(), observation.attempt) != observation:
            raise TimingArchiveError("terminal content identity is contradictory")
        if self.load_attempt(attempt_identity=observation.attempt.attempt_identity) != observation.attempt:
            raise TimingArchiveError("terminal attempt has no exact archived start")
        self._save(schema.TERMINALS, observation.observation_identity, observation.canonical_bytes(),
                   "attempt_identity", observation.attempt.attempt_identity)

    def load_terminal(self, *, observation_identity: str) -> NAROperationalTimingTerminalObservation | None:
        row = self._read(schema.TERMINALS, observation_identity)
        if row is None:
            return None
        attempt = self.load_attempt(attempt_identity=row[1])
        if attempt is None:
            raise TimingArchiveError("terminal attempt start is absent")
        try:
            result = NAROperationalTimingTerminalObservation.from_json(row[2], attempt)
            if result.observation_identity != row[0]:
                raise ValueError("terminal identity differs")
            return result
        except (KeyError, TypeError, ValueError) as error:
            raise TimingArchiveError("stored terminal is corrupt") from error

    def list_unresolved_attempts(self, *, session_identity: str) -> tuple[NAROperationalTimingAttempt, ...]:
        if self.load_session(session_identity=session_identity) is None:
            raise TimingArchiveError("session is absent")
        rows = self._connection.execute(
            f"SELECT a.identity FROM {schema.ATTEMPTS} a LEFT JOIN {schema.TERMINALS} t "
            "ON t.attempt_identity=a.identity WHERE a.session_identity=? AND t.identity IS NULL ORDER BY a.identity",
            (session_identity,),
        ).fetchall()
        result = tuple(self.load_attempt(attempt_identity=row[0]) for row in rows)
        if any(item is None for item in result):
            raise TimingArchiveError("unresolved attempt disappeared")
        return result

    def save_freeze_receipt(self, *, receipt: HistoricalInputSnapshotFreezeReceipt,
                            _issuance_marker: object = None) -> None:
        if type(receipt) is not HistoricalInputSnapshotFreezeReceipt or _issuance_marker is not _ISSUANCE_MARKER:
            raise TimingArchiveError("receipt requires controlled save/reload issuance")
        if HistoricalInputSnapshotFreezeReceipt.from_json(receipt.canonical_bytes().decode()) != receipt:
            raise TimingArchiveError("receipt content identity is contradictory")
        self._save(schema.RECEIPTS, receipt.receipt_identity, receipt.canonical_bytes())

    def load_freeze_receipt(self, *, receipt_identity: str) -> HistoricalInputSnapshotFreezeReceipt | None:
        row = self._read(schema.RECEIPTS, receipt_identity)
        if row is None:
            return None
        try:
            result = HistoricalInputSnapshotFreezeReceipt.from_json(row[1])
            if result.receipt_identity != row[0]:
                raise ValueError("receipt identity differs")
            return result
        except (KeyError, TypeError, ValueError) as error:
            raise TimingArchiveError("stored freeze receipt is corrupt") from error
