"""Immutable local scope store; ordinary load never reopens daily/Phase111 sources."""

from __future__ import annotations

import sqlite3

from scripts.simulation import nar_pre_c_production_root_scope_admission_archive_migration as schema
from scripts.simulation.nar_pre_c_production_root_scope_admission import (
    RootScopeAdmissionError, RootScopeAdmissionConflict, identity,
    POLICY_APPROVAL_PREFIX, AVAILABILITY_PREFIX, BINDING_PREFIX,
    parse_record, validate_policy_pair, validate_scope_pair,
)
from scripts.simulation.sqlite_nar_pre_c_production_claim_binding_archive import SQLiteNARPreCProductionClaimBindingArchive
from scripts.simulation.nar_pre_c_production_claim_binding import NARPreCProductionClaimBindingV1
from scripts.simulation.sqlite_nar_pre_c_production_prestaged_manifest_archive import SQLiteNARPreCProductionPrestagedManifestArchive
from scripts.simulation.repositories.sqlite_nar_production_mapping_repository import SQLiteNARProductionMappingRepository
from scripts.simulation.sqlite_nar_operational_timing_runtime_execution_archive import SQLiteNAROperationalTimingRuntimeExecutionArchive


def require_idle(*repositories):
    for repository in repositories:
        if repository._connection.in_transaction:
            raise RootScopeAdmissionError("committed idle upstream/companion read required")


def load_binding_authority(*, phase113_archive, runtime_archive, phase112_archive,
                           phase109_repository, binding_identity):
    for repository, kind in ((phase113_archive, SQLiteNARPreCProductionClaimBindingArchive),
                             (runtime_archive, SQLiteNAROperationalTimingRuntimeExecutionArchive),
                             (phase112_archive, SQLiteNARPreCProductionPrestagedManifestArchive),
                             (phase109_repository, SQLiteNARProductionMappingRepository)):
        if type(repository) is not kind:
            raise RootScopeAdmissionError("exact injected accepted upstream repositories required")
    require_idle(phase113_archive, runtime_archive, phase112_archive, phase109_repository)
    identity(binding_identity, BINDING_PREFIX)
    binding = phase113_archive.load_binding(
        identity=binding_identity, runtime_archive=runtime_archive,
        phase112_archive=phase112_archive, phase109_repository=phase109_repository)
    if type(binding) is not NARPreCProductionClaimBindingV1 or binding.identity != binding_identity:
        raise RootScopeAdmissionError("exact Phase113 authority required")
    pair = phase112_archive.load_authority(manifest_identity=binding.phase112_manifest_identity,
                                           phase109_repository=phase109_repository)
    mapping = phase109_repository.load_receipt(receipt_id=binding.phase109_receipt_id)
    if (pair is None or mapping is None or pair.manifest.phase109_receipt_id != binding.phase109_receipt_id
            or pair.availability_receipt.identity != binding.phase112_availability_receipt_identity
            or (binding.external_race_id, binding.internal_race_id, binding.prediction_cutoff) !=
               (mapping.external_race_id, mapping.internal_race_id, mapping.prediction_cutoff)):
        raise RootScopeAdmissionError("exact Phase113/112/109 ancestry differs")
    return binding, pair, mapping


class SQLiteNARPreCProductionRootScopeAdmissionArchive:
    def __init__(self, *, connection: sqlite3.Connection):
        schema.require_phase114_schema(connection)
        if connection.in_transaction:
            raise RootScopeAdmissionError("idle injected companion required")
        self._connection = connection

    def _load(self, table, record_identity):
        schema.require_phase114_schema(self._connection)
        kind, _ = schema.RECORDS[table]
        identity(record_identity, kind.prefix)
        row = self._connection.execute(f"SELECT * FROM {table} WHERE identity=?", (record_identity,)).fetchone()
        if row is None:
            return None
        value = parse_record(kind, row[-1], record_identity)
        if tuple(row) != schema.record_row(table, value):
            raise RootScopeAdmissionError("exact local SQL projection required")
        return value

    def _receipt_for(self, table, parent_column, parent_identity):
        schema.require_phase114_schema(self._connection)
        row = self._connection.execute(f"SELECT identity FROM {table} WHERE {parent_column}=?", (parent_identity,)).fetchone()
        return None if row is None else self._load(table, row[0])

    def load_policy(self, *, approval_identity):
        require_idle(self)
        identity(approval_identity, POLICY_APPROVAL_PREFIX)
        approval = self._load(schema.POLICY_APPROVALS, approval_identity)
        if approval is None:
            raise RootScopeAdmissionError("exact completed policy approval required")
        content = self._load(schema.POLICY_CONTENTS, approval.policy_content_identity)
        if content is None:
            raise RootScopeAdmissionError("exact committed policy content required")
        validate_policy_pair(content, approval)
        return content, approval

    def load_admission(self, *, availability_receipt_identity, expected_phase113_binding_identity,
                       phase113_archive, runtime_archive, phase112_archive, phase109_repository):
        """Accepted immutable handoff, no source archives, clock, root or capability."""
        require_idle(self)
        identity(availability_receipt_identity, AVAILABILITY_PREFIX)
        identity(expected_phase113_binding_identity, BINDING_PREFIX)
        receipt = self._load(schema.AVAILABILITY, availability_receipt_identity)
        if receipt is None:
            raise RootScopeAdmissionError("exact completed scope availability required")
        scope = self._load(schema.SCOPES, receipt.scope_identity)
        if scope is None or scope.phase113_binding_identity != expected_phase113_binding_identity:
            raise RootScopeAdmissionError("exact expected Phase113 binding differs")
        content, approval = self.load_policy(approval_identity=scope.policy_approval_identity)
        validate_scope_pair(scope, receipt, content, approval)
        binding, pair, mapping = load_binding_authority(
            phase113_archive=phase113_archive, runtime_archive=runtime_archive,
            phase112_archive=phase112_archive, phase109_repository=phase109_repository,
            binding_identity=scope.phase113_binding_identity)
        if ((scope.external_race_id, scope.internal_race_id, scope.prediction_information_cutoff) !=
                (binding.external_race_id, binding.internal_race_id, binding.prediction_cutoff)
                or scope.target_declaration_id != mapping.phase111_declaration_id
                or receipt.admitted_at < pair.availability_receipt.available_at):
            raise RootScopeAdmissionError("scope/upstream binding or availability differs")
        return scope, receipt

    def _stage_content(self, table, value):
        """Stage A only. Private controlled issuer primitive, not caller authority."""
        require_idle(self)
        c = self._connection
        schema.require_phase114_schema(c)
        c.execute("BEGIN IMMEDIATE")
        try:
            schema.require_phase114_schema(c)
            row = schema.record_row(table, value)
            payload = value.payload()
            clauses, arguments = ["identity=?"], [value.identity]
            for target_table, columns in schema._KEYS.values():
                if target_table == table:
                    clauses.append("(" + " AND ".join(f"{column}=?" for column in columns) + ")")
                    arguments.extend(payload[column] for column in columns)
            rows = c.execute(f"SELECT identity FROM {table} WHERE " + " OR ".join(clauses), arguments).fetchall()
            if rows:
                if len(rows) != 1 or rows[0][0] != value.identity or self._load(table, value.identity) != value:
                    raise RootScopeAdmissionConflict("permanent target-set/binding/forward/reverse reservation conflict")
            else:
                c.execute(f"INSERT INTO {table} VALUES({','.join('?' for _ in row)})", row)
            schema.require_phase114_schema(c)
            c.commit()
        except BaseException:
            c.rollback()
            raise
        reloaded = self._load(table, value.identity)
        if reloaded != value:
            raise RootScopeAdmissionError("committed content did not exact-reload")
        return reloaded

    def _stage_receipt(self, table, parent_column, parent_identity, first_receipt):
        """Stage B: inspect winner before calling the controlled clock factory."""
        require_idle(self)
        c = self._connection
        schema.require_phase114_schema(c)
        c.execute("BEGIN IMMEDIATE")
        try:
            schema.require_phase114_schema(c)
            receipt = self._receipt_for(table, parent_column, parent_identity)
            if receipt is None:
                receipt = first_receipt()
                row = schema.record_row(table, receipt)
                c.execute(f"INSERT INTO {table} VALUES({','.join('?' for _ in row)})", row)
            schema.require_phase114_schema(c)
            c.commit()
        except BaseException:
            c.rollback()
            raise
        reloaded = self._load(table, receipt.identity)
        if reloaded != receipt:
            raise RootScopeAdmissionError("committed receipt did not exact-reload")
        return reloaded
