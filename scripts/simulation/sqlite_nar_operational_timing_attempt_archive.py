"""Connection-injected append-only Phase105 evidence archive; no clocks or network."""

from __future__ import annotations

import sqlite3

from scripts.simulation import nar_operational_timing_attempt_archive_migration as schema
from scripts.simulation.nar_operational_timing_attempt_v2 import (
    NAROperationalTimingAttemptV2, NAROperationalTimingTerminalV2,
    NARRequestEffectiveEnvironmentVerification, NARTimingPublicationOverheadV2,
    NARRequestEnvironmentQualification,
)
from scripts.simulation.sqlite_nar_operational_timing_observability_archive import (
    TimingArchiveError, TimingArchiveConflict,
)
from scripts.simulation.sqlite_nar_operational_timing_runtime_execution_archive import (
    SQLiteNAROperationalTimingRuntimeExecutionArchive,
)


_SEND_VERIFICATION_ISSUANCE_MARKER = object()  # Trusted API discipline, not cryptographic security.
_TIMING_EVIDENCE_ISSUANCE_MARKER = object()  # Wrapper-held current-process authority discipline.


class SQLiteNAROperationalTimingAttemptArchive:
    __slots__ = ("_connection", "runtime")

    def __init__(self, *, connection: sqlite3.Connection) -> None:
        if type(connection) is not sqlite3.Connection or connection.in_transaction:
            raise TimingArchiveError("attempt archive requires exact idle SQLite connection")
        schema.require_nar_operational_timing_attempt_archive_schema(connection)
        self._connection = connection
        self.runtime = SQLiteNAROperationalTimingRuntimeExecutionArchive(connection=connection)

    def _row(self, table: str, column: str, identity: str) -> tuple | None:
        schema.require_nar_operational_timing_attempt_archive_schema(self._connection)
        rows = self._connection.execute(f"SELECT * FROM {table} WHERE {column}=?", (identity,)).fetchall()
        if len(rows) > 1:
            raise TimingArchiveError("attempt natural identity duplicated")
        return tuple(rows[0]) if rows else None

    def _save(self, *, table: str, row: tuple, columns: str, natural_column: str = "identity",
              natural_value: object | None = None) -> bool:
        if self._connection.in_transaction:
            raise TimingArchiveError("attempt evidence write requires idle connection")
        schema.require_nar_operational_timing_attempt_archive_schema(self._connection)
        key = row[0] if natural_value is None else natural_value
        try:
            self._connection.execute("BEGIN IMMEDIATE")
            rows = self._connection.execute(
                f"SELECT * FROM {table} WHERE identity=? OR {natural_column}=?", (row[0], key)
            ).fetchall()
            if rows:
                if len(rows) != 1 or tuple(rows[0]) != row:
                    raise TimingArchiveConflict("immutable attempt evidence conflicts")
                inserted = False
            else:
                self._connection.execute(
                    f"INSERT INTO {table}({columns}) VALUES({','.join('?' for _ in row)})", row
                )
                if tuple(self._connection.execute(f"SELECT * FROM {table} WHERE identity=?", (row[0],)).fetchone()) != row:
                    raise TimingArchiveError("attempt evidence did not exact-reload")
                inserted = True
            self._connection.commit()
            return inserted
        except sqlite3.IntegrityError as error:
            self._connection.rollback()
            raise TimingArchiveConflict("attempt evidence parent or identity conflicts") from error
        except BaseException:
            self._connection.rollback()
            raise

    def _claim(self, attempt: NAROperationalTimingAttemptV2):
        claim = self.runtime.load_claim_for_session(session_identity=attempt.session_identity)
        session = self.runtime.v2.load_session(session_identity=attempt.session_identity)
        if (claim is None or claim.claim_identity != attempt.campaign_execution_identity
                or claim.configuration_identity != attempt.configuration_identity or session is None
                or session.configuration.configuration_identity != attempt.configuration_identity
                or not session.admits(attempt.attempt_admitted_at)
                or attempt.stage not in session.configuration.enabled_stages):
            raise TimingArchiveError("attempt lacks exact admitted execution ancestry")
        readiness = self.runtime.load_readiness_for_claim(claim_identity=claim.claim_identity)
        if readiness is None or readiness.readiness_verified_at > session.measurement_start_at:
            raise TimingArchiveError("attempt lacks qualifying runtime readiness")
        return claim

    def save_attempt(self, *, attempt: NAROperationalTimingAttemptV2,
                     _issuance_marker: object = None) -> bool:
        if (type(attempt) is not NAROperationalTimingAttemptV2
                or _issuance_marker is not _TIMING_EVIDENCE_ISSUANCE_MARKER):
            raise TimingArchiveError("attempt publication requires controlled current-process issuance")
        self._claim(attempt)
        row = (attempt.attempt_identity, attempt.campaign_execution_identity, attempt.session_identity,
               attempt.configuration_identity, attempt.attempt_sequence, attempt.stage.value,
               attempt.expected_http_environment_policy.value if attempt.expected_http_environment_policy else None,
               attempt.canonical_bytes().decode("utf-8"))
        return self._save(table=schema.ATTEMPTS, row=row,
                          columns="identity,claim_identity,session_identity,configuration_identity,attempt_sequence,stage,http_policy,payload_json")

    def load_attempt(self, *, attempt_identity: str) -> NAROperationalTimingAttemptV2 | None:
        row = self._row(schema.ATTEMPTS, "identity", attempt_identity)
        if row is None:
            return None
        try:
            value = NAROperationalTimingAttemptV2.from_json(row[-1])
            if (value.attempt_identity, value.campaign_execution_identity, value.session_identity,
                    value.configuration_identity, value.attempt_sequence, value.stage.value,
                    value.expected_http_environment_policy.value if value.expected_http_environment_policy else None) != row[:-1]:
                raise ValueError("attempt row/content mismatch")
            self._claim(value)
            return value
        except (KeyError, TypeError, ValueError) as error:
            raise TimingArchiveError("stored attempt evidence is corrupt") from error

    def save_environment(self, *, verification: NARRequestEffectiveEnvironmentVerification,
                         _issuance_marker: object = None) -> bool:
        if (type(verification) is not NARRequestEffectiveEnvironmentVerification
                or _issuance_marker is not _SEND_VERIFICATION_ISSUANCE_MARKER):
            raise TimingArchiveError("request environment verification requires controlled pre-send issuance")
        attempt = self.load_attempt(attempt_identity=verification.attempt_identity)
        if attempt is None or attempt.expected_http_environment_policy is None:
            raise TimingArchiveError("environment requires exact HTTP attempt")
        if verification.expected_url_match != (verification.prepared_url_sha256 == attempt.expected_request_url_sha256):
            raise TimingArchiveError("environment URL/attempt ancestry mismatch")
        claim = self._claim(attempt)
        binding = self.runtime.load_binding(binding_identity=claim.binding_identity)
        if binding is None or binding.transport_profile_identity != verification.transport_profile_identity:
            raise TimingArchiveError("environment transport ancestry mismatch")
        row = (verification.verification_identity, attempt.attempt_identity, verification.qualification.value,
               verification.canonical_bytes().decode("utf-8"))
        return self._save(table=schema.ENVIRONMENTS, row=row, columns="identity,attempt_identity,qualification,payload_json",
                          natural_column="attempt_identity", natural_value=attempt.attempt_identity)

    def load_environment_for_attempt(self, *, attempt_identity: str) -> NARRequestEffectiveEnvironmentVerification | None:
        row = self._row(schema.ENVIRONMENTS, "attempt_identity", attempt_identity)
        if row is None:
            return None
        try:
            value = NARRequestEffectiveEnvironmentVerification.from_json(row[-1])
            if (value.verification_identity, value.attempt_identity, value.qualification.value) != row[:-1]:
                raise ValueError("environment row/content mismatch")
            attempt = self.load_attempt(attempt_identity=value.attempt_identity)
            if attempt is None or attempt.expected_http_environment_policy is None:
                raise ValueError("environment has no HTTP attempt")
            if value.expected_url_match != (value.prepared_url_sha256 == attempt.expected_request_url_sha256):
                raise ValueError("environment URL/attempt ancestry mismatch")
            claim = self._claim(attempt)
            binding = self.runtime.load_binding(binding_identity=claim.binding_identity)
            if binding is None or binding.transport_profile_identity != value.transport_profile_identity:
                raise ValueError("environment static transport ancestry mismatch")
            return value
        except (KeyError, TypeError, ValueError) as error:
            raise TimingArchiveError("stored environment evidence is corrupt") from error

    def save_terminal(self, *, terminal: NAROperationalTimingTerminalV2,
                      _issuance_marker: object = None) -> bool:
        if (type(terminal) is not NAROperationalTimingTerminalV2
                or _issuance_marker is not _TIMING_EVIDENCE_ISSUANCE_MARKER):
            raise TimingArchiveError("terminal publication requires controlled current-process issuance")
        attempt = self.load_attempt(attempt_identity=terminal.attempt_identity)
        if attempt is None:
            raise TimingArchiveError("terminal requires exact archived attempt")
        if terminal.operation_finished_at < attempt.attempt_admitted_at:
            raise TimingArchiveError("terminal causal UTC finish precedes attempt admission")
        row = (terminal.terminal_identity, terminal.attempt_identity, terminal.canonical_bytes().decode("utf-8"))
        return self._save(table=schema.TERMINALS, row=row, columns="identity,attempt_identity,payload_json",
                          natural_column="attempt_identity", natural_value=terminal.attempt_identity)

    def load_terminal_for_attempt(self, *, attempt_identity: str) -> NAROperationalTimingTerminalV2 | None:
        row = self._row(schema.TERMINALS, "attempt_identity", attempt_identity)
        if row is None:
            return None
        try:
            value = NAROperationalTimingTerminalV2.from_json(row[-1])
            attempt = self.load_attempt(attempt_identity=value.attempt_identity)
            if ((value.terminal_identity, value.attempt_identity) != row[:-1] or attempt is None
                    or value.operation_finished_at < attempt.attempt_admitted_at):
                raise ValueError("terminal row/content mismatch")
            return value
        except (KeyError, TypeError, ValueError) as error:
            raise TimingArchiveError("stored terminal evidence is corrupt") from error

    def save_overhead(self, *, overhead: NARTimingPublicationOverheadV2,
                      _issuance_marker: object = None) -> bool:
        if (type(overhead) is not NARTimingPublicationOverheadV2
                or _issuance_marker is not _TIMING_EVIDENCE_ISSUANCE_MARKER):
            raise TimingArchiveError("overhead publication requires controlled current-process issuance")
        attempt = self.load_attempt(attempt_identity=overhead.attempt_identity)
        if attempt is None or attempt.campaign_execution_identity != overhead.campaign_execution_identity:
            raise TimingArchiveError("overhead attempt ancestry mismatch")
        row = (overhead.overhead_identity, overhead.campaign_execution_identity, overhead.attempt_identity,
               overhead.stage.value, overhead.canonical_bytes().decode("utf-8"))
        return self._save(table=schema.OVERHEAD, row=row,
                          columns="identity,claim_identity,attempt_identity,stage,payload_json")

    def list_unresolved_attempts(self, *, claim_identity: str) -> tuple[NAROperationalTimingAttemptV2, ...]:
        schema.require_nar_operational_timing_attempt_archive_schema(self._connection)
        rows = self._connection.execute(
            f"SELECT a.identity FROM {schema.ATTEMPTS} a LEFT JOIN {schema.TERMINALS} t "
            "ON t.attempt_identity=a.identity WHERE a.claim_identity=? AND t.identity IS NULL ORDER BY a.attempt_sequence",
            (claim_identity,),
        ).fetchall()
        return tuple(self.load_attempt(attempt_identity=row[0]) for row in rows)

    def list_nonqualifying_http_attempts(self, *, claim_identity: str) -> tuple[NAROperationalTimingAttemptV2, ...]:
        """Future official aggregation must fail closed if this is nonempty."""
        schema.require_nar_operational_timing_attempt_archive_schema(self._connection)
        rows = self._connection.execute(
            f"SELECT a.identity FROM {schema.ATTEMPTS} a LEFT JOIN {schema.ENVIRONMENTS} e "
            "ON e.attempt_identity=a.identity WHERE a.claim_identity=? AND a.http_policy IS NOT NULL "
            "AND (e.identity IS NULL OR e.qualification!=?) ORDER BY a.attempt_sequence",
            (claim_identity, NARRequestEnvironmentQualification.QUALIFIED_DIRECT_REQUEST_ENVIRONMENT.value),
        ).fetchall()
        return tuple(self.load_attempt(attempt_identity=row[0]) for row in rows)
