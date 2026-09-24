"""Append-only diagnostic companion on one locked Phase105 SQLite archive."""

from __future__ import annotations

import sqlite3

from scripts.simulation import nar_operational_timing_diagnostic_archive_migration as schema
from scripts.simulation.nar_operational_timing_diagnostic_campaign import (
    NAROperationalTimingDiagnosticFixtureBundleV1 as Fixture,
    NAROperationalTimingDiagnosticCampaignPlanV1 as Plan,
    NAROperationalTimingDiagnosticExecutionDeclarationV1 as Declaration,
)
from scripts.simulation.sqlite_nar_operational_timing_attempt_archive import SQLiteNAROperationalTimingAttemptArchive
from scripts.simulation.sqlite_nar_operational_timing_observability_archive import TimingArchiveError, TimingArchiveConflict
from scripts.simulation.nar_operational_timing_observability import _json_bytes


_DIAGNOSTIC_ISSUANCE_MARKER = object()  # Trusted composition discipline, not cryptography.


class SQLiteNAROperationalTimingDiagnosticArchive:
    __slots__ = ("_connection", "attempts")

    def __init__(self, *, connection: sqlite3.Connection) -> None:
        if type(connection) is not sqlite3.Connection or connection.in_transaction:
            raise TimingArchiveError("diagnostic archive requires exact idle connection")
        schema.require_nar_operational_timing_diagnostic_archive_schema(connection)
        self._connection = connection
        self.attempts = SQLiteNAROperationalTimingAttemptArchive(connection=connection)

    def _row(self, table: str, column: str, identity: str):
        schema.require_nar_operational_timing_diagnostic_archive_schema(self._connection)
        rows = self._connection.execute(f"SELECT * FROM {table} WHERE {column}=?", (identity,)).fetchall()
        if len(rows) > 1:
            raise TimingArchiveError("diagnostic natural identity duplicated")
        return tuple(rows[0]) if rows else None

    def _publish(self, table: str, row: tuple, columns: str, *, natural_column: str = "identity",
                 natural_value: str | None = None, node_rows: tuple[tuple, ...] = ()) -> bool:
        if self._connection.in_transaction:
            raise TimingArchiveError("diagnostic publication requires idle connection")
        schema.require_nar_operational_timing_diagnostic_archive_schema(self._connection)
        key = row[0] if natural_value is None else natural_value
        try:
            self._connection.execute("BEGIN IMMEDIATE")
            rows = self._connection.execute(
                f"SELECT * FROM {table} WHERE identity=? OR {natural_column}=?", (row[0], key)).fetchall()
            if rows:
                if len(rows) != 1 or tuple(rows[0]) != row:
                    raise TimingArchiveConflict("immutable diagnostic authority conflicts")
                if node_rows:
                    existing_nodes = tuple(tuple(x) for x in self._connection.execute(
                        f"SELECT identity,plan_identity,node_key,attempt_sequence,stage,http_policy,payload_json "
                        f"FROM {schema.NODES} WHERE plan_identity=? ORDER BY attempt_sequence", (row[0],)))
                    if existing_nodes != node_rows:
                        raise TimingArchiveConflict("immutable diagnostic plan nodes conflict")
                inserted = False
            else:
                self._connection.execute(
                    f"INSERT INTO {table}({columns}) VALUES({','.join('?' for _ in row)})", row)
                for node_row in node_rows:
                    self._connection.execute(
                        f"INSERT INTO {schema.NODES}(identity,plan_identity,node_key,attempt_sequence,stage,http_policy,payload_json) "
                        "VALUES(?,?,?,?,?,?,?)", node_row)
                inserted = True
            if tuple(self._connection.execute(f"SELECT * FROM {table} WHERE identity=?", (row[0],)).fetchone()) != row:
                raise TimingArchiveError("diagnostic authority did not exact-reload")
            self._connection.commit()
            return inserted
        except sqlite3.IntegrityError as error:
            self._connection.rollback()
            raise TimingArchiveConflict("diagnostic identity or parent conflicts") from error
        except BaseException:
            self._connection.rollback()
            raise

    def save_fixture(self, *, fixture: Fixture, _issuance_marker: object = None) -> bool:
        if type(fixture) is not Fixture or _issuance_marker is not _DIAGNOSTIC_ISSUANCE_MARKER:
            raise TimingArchiveError("diagnostic fixture publication requires controlled issuance")
        row = (fixture.bundle_identity, fixture.canonical_bytes().decode("utf-8"))
        return self._publish(schema.FIXTURES, row, "identity,payload_json")

    def load_fixture(self, *, fixture_identity: str) -> Fixture | None:
        row = self._row(schema.FIXTURES, "identity", fixture_identity)
        if row is None:
            return None
        try:
            value = Fixture.from_json(row[1])
            if value.bundle_identity != row[0]:
                raise ValueError("fixture identity differs")
            return value
        except (ValueError, KeyError, TypeError) as error:
            raise TimingArchiveError("diagnostic fixture is corrupt") from error

    def save_plan(self, *, plan: Plan, _issuance_marker: object = None) -> bool:
        if type(plan) is not Plan or _issuance_marker is not _DIAGNOSTIC_ISSUANCE_MARKER:
            raise TimingArchiveError("diagnostic plan publication requires controlled issuance")
        fixture = self.load_fixture(fixture_identity=plan.fixture_bundle_identity)
        session = self.attempts.runtime.v2.load_session(session_identity=plan.session_identity)
        if (fixture is None or session is None
                or session.configuration.configuration_identity != plan.configuration_identity
                or session.configuration.repository_identity != plan.repository_identity
                or session.configuration.software_commit_sha != plan.commit_sha
                or fixture.repository_identity != plan.repository_identity
                or fixture.commit_sha != plan.commit_sha
                or any(node.stage not in session.configuration.enabled_stages for node in plan.nodes)
                or any(node.fixture_path is not None and node.fixture_path not in {x.path for x in fixture.members}
                       for node in plan.nodes)):
            raise TimingArchiveError("diagnostic plan fixture/session ancestry differs")
        row = (plan.plan_identity, plan.fixture_bundle_identity, plan.session_identity,
               plan.configuration_identity, plan.canonical_bytes().decode("utf-8"))
        node_rows = tuple((plan.node_identity(node.key), plan.plan_identity, node.key, node.sequence,
                           node.stage.value, "DIRECT_REQUEST_ENVIRONMENT_V1" if node.transport_kind else None,
                           _json_bytes(node.payload()).decode("utf-8"))
                          for node in plan.nodes)
        return self._publish(schema.PLANS, row,
                             "identity,fixture_identity,session_identity,configuration_identity,payload_json",
                             natural_column="session_identity", natural_value=plan.session_identity, node_rows=node_rows)

    def load_plan(self, *, plan_identity: str) -> Plan | None:
        row = self._row(schema.PLANS, "identity", plan_identity)
        if row is None:
            return None
        try:
            value = Plan.from_json(row[4])
            if (value.plan_identity, value.fixture_bundle_identity, value.session_identity,
                    value.configuration_identity) != row[:4]:
                raise ValueError("diagnostic plan row differs")
            fixture = self.load_fixture(fixture_identity=value.fixture_bundle_identity)
            session = self.attempts.runtime.v2.load_session(session_identity=value.session_identity)
            if (fixture is None or session is None
                    or session.configuration.configuration_identity != value.configuration_identity
                    or session.configuration.repository_identity != value.repository_identity
                    or session.configuration.software_commit_sha != value.commit_sha
                    or any(node.stage not in session.configuration.enabled_stages for node in value.nodes)
                    or fixture.repository_identity != value.repository_identity or fixture.commit_sha != value.commit_sha):
                raise ValueError("diagnostic plan ancestry differs")
            nodes = self._connection.execute(
                f"SELECT identity,plan_identity,node_key,attempt_sequence,stage,http_policy,payload_json "
                f"FROM {schema.NODES} WHERE plan_identity=? ORDER BY attempt_sequence", (plan_identity,)).fetchall()
            expected = [(value.node_identity(node.key), value.plan_identity, node.key, node.sequence,
                         node.stage.value, "DIRECT_REQUEST_ENVIRONMENT_V1" if node.transport_kind else None,
                         _json_bytes(node.payload()).decode("utf-8")) for node in value.nodes]
            if [tuple(x) for x in nodes] != expected:
                raise ValueError("diagnostic plan node rows differ")
            return value
        except (ValueError, KeyError, TypeError) as error:
            raise TimingArchiveError("diagnostic plan is corrupt") from error

    def save_declaration(self, *, declaration: Declaration, _issuance_marker: object = None) -> bool:
        if type(declaration) is not Declaration or _issuance_marker is not _DIAGNOSTIC_ISSUANCE_MARKER:
            raise TimingArchiveError("diagnostic declaration publication requires controlled issuance")
        plan = self.load_plan(plan_identity=declaration.plan_identity)
        claim = self.attempts.runtime.load_claim_for_session(session_identity=declaration.session_identity)
        if (plan is None or claim is None or claim.claim_identity != declaration.claim_identity
                or plan.session_identity != declaration.session_identity
                or plan.configuration_identity != declaration.configuration_identity
                or plan.fixture_bundle_identity != declaration.fixture_bundle_identity
                or claim.configuration_identity != declaration.configuration_identity):
            raise TimingArchiveError("diagnostic declaration parent differs")
        if self._connection.execute(
                f"SELECT 1 FROM {schema.attempt.ATTEMPTS} WHERE claim_identity=? LIMIT 1",
                (claim.claim_identity,)).fetchone():
            raise TimingArchiveError("diagnostic declaration cannot backfill after attempts")
        row = (declaration.declaration_identity, declaration.plan_identity,
               declaration.claim_identity, declaration.canonical_bytes().decode("utf-8"))
        return self._publish(schema.DECLARATIONS, row, "identity,plan_identity,claim_identity,payload_json",
                             natural_column="claim_identity", natural_value=claim.claim_identity)

    def load_declaration_for_claim(self, *, claim_identity: str) -> Declaration | None:
        row = self._row(schema.DECLARATIONS, "claim_identity", claim_identity)
        if row is None:
            return None
        try:
            value = Declaration.from_json(row[3])
            if (value.declaration_identity, value.plan_identity, value.claim_identity) != row[:3]:
                raise ValueError("diagnostic declaration row differs")
            plan = self.load_plan(plan_identity=value.plan_identity)
            claim = self.attempts.runtime.load_claim_for_session(session_identity=value.session_identity)
            if (plan is None or claim is None or claim.claim_identity != value.claim_identity
                    or plan.configuration_identity != value.configuration_identity
                    or plan.fixture_bundle_identity != value.fixture_bundle_identity):
                raise ValueError("diagnostic declaration ancestry differs")
            return value
        except (ValueError, KeyError, TypeError) as error:
            raise TimingArchiveError("diagnostic declaration is corrupt") from error
