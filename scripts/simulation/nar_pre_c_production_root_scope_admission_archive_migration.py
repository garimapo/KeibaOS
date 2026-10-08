"""Exact standalone version-one companion, never a main simulation migration."""

from __future__ import annotations

import sqlite3

from scripts.simulation.nar_pre_c_production_root_scope_admission import (
    RootScopeAdmissionError, parse_record, validate_policy_pair, validate_scope_pair,
    NARPreCProductionCutoffPolicyApprovalContentV1 as PolicyContent,
    NARPreCProductionCutoffPolicyApprovalV1 as PolicyApproval,
    NARPreCProductionRootScopeAdmissionV1 as Scope,
    NARPreCProductionRootScopeAdmissionAvailabilityReceiptV1 as Availability,
)

VERSION = 1
NAME = "v001_nar_pre_c_production_root_scope_admission_companion"
NOT_INSTALLED = "PHASE114_SCHEMA_NOT_INSTALLED"
ACTIVE = "PHASE114_SCHEMA_ACTIVE"
INTEGRITY_FAILURE = "PHASE114_SCHEMA_INTEGRITY_FAILURE"
REGISTRY = "nar_pre_c_production_root_scope_registry"
POLICY_CONTENTS = "nar_pre_c_production_root_scope_policy_contents"
POLICY_APPROVALS = "nar_pre_c_production_root_scope_policy_approvals"
SCOPES = "nar_pre_c_production_root_scope_contents"
AVAILABILITY = "nar_pre_c_production_root_scope_availability"

# Exact SQL scalar projections; complete canonical content is also verified.
RECORDS = {
    POLICY_CONTENTS: (PolicyContent, ("organization", "source_system", "target_set_content_sha256", "anchor_declaration_id")),
    POLICY_APPROVALS: (PolicyApproval, ("policy_content_identity", "policy_approved_at")),
    SCOPES: (Scope, ("phase113_binding_identity", "policy_approval_identity", "organization", "source_system",
                    "external_race_id", "internal_race_id", "prediction_information_cutoff")),
    AVAILABILITY: (Availability, ("scope_identity", "policy_approval_identity", "phase113_binding_identity", "admitted_at")),
}
_PARENTS = {
    POLICY_APPROVALS: (("policy_content_identity", POLICY_CONTENTS),),
    SCOPES: (("policy_approval_identity", POLICY_APPROVALS),),
    AVAILABILITY: (("scope_identity", SCOPES), ("policy_approval_identity", POLICY_APPROVALS)),
}
_KEYS = {
    "policy_selection": (POLICY_CONTENTS, ("organization", "source_system", "target_set_content_sha256")),
    "policy_approval": (POLICY_APPROVALS, ("policy_content_identity",)),
    "scope_binding": (SCOPES, ("phase113_binding_identity",)),
    "scope_external": (SCOPES, ("organization", "source_system", "external_race_id", "prediction_information_cutoff")),
    "scope_internal": (SCOPES, ("organization", "source_system", "internal_race_id", "prediction_information_cutoff")),
    "scope_availability": (AVAILABILITY, ("scope_identity",)),
}
_DDL = {REGISTRY: f"CREATE TABLE {REGISTRY} (version INTEGER PRIMARY KEY CHECK(version=1), name TEXT NOT NULL CHECK(name='{NAME}')) WITHOUT ROWID"}
for _table, (_kind, _columns) in RECORDS.items():
    _definitions = ["identity TEXT PRIMARY KEY"]
    for _column in _columns:
        _sql_type = "INTEGER" if _column == "internal_race_id" else "TEXT"
        _check = {"organization": " CHECK(organization='NAR')", "source_system": " CHECK(source_system='nar_official')",
                  "internal_race_id": " CHECK(internal_race_id>0)"}.get(_column, "")
        _definitions.append(f"{_column} {_sql_type} NOT NULL{_check}")
    _definitions += ["schema_version INTEGER NOT NULL CHECK(schema_version=1)", "payload_json TEXT NOT NULL"]
    _definitions += [f"FOREIGN KEY({col}) REFERENCES {parent}(identity)" for col, parent in _PARENTS.get(_table, ())]
    _DDL[_table] = f"CREATE TABLE {_table} ({', '.join(_definitions)}) WITHOUT ROWID"
for _suffix, (_table, _columns) in _KEYS.items():
    _name = "nar_pre_c_root_scope_unique_" + _suffix
    _DDL[_name] = f"CREATE UNIQUE INDEX {_name} ON {_table}({','.join(_columns)})"
for _table in (REGISTRY, *RECORDS):
    for _verb in ("UPDATE", "DELETE"):
        _name = f"{_table}_no_{_verb.lower()}"
        _DDL[_name] = (f"CREATE TRIGGER {_name} BEFORE {_verb} ON {_table} "
                       "BEGIN SELECT RAISE(ABORT, 'immutable Phase114 scope evidence'); END")


def record_row(table, value):
    kind, columns = RECORDS[table]
    if type(value) is not kind:
        raise RootScopeAdmissionError("exact persisted semantic required")
    payload = value.payload()
    return (value.identity, *(payload[col] for col in columns), value.schema_version, value.canonical_json())


def _objects(connection):
    return {name: (kind, table, sql) for kind, name, table, sql in connection.execute(
        "SELECT type,name,tbl_name,sql FROM sqlite_schema WHERE name NOT GLOB 'sqlite_*'")}


def _expected():
    result = {}
    for name, ddl in _DDL.items():
        if name in (REGISTRY, *RECORDS):
            result[name] = ("table", name, ddl)
        elif " BEFORE " in ddl:
            result[name] = ("trigger", name.rsplit("_no_", 1)[0], ddl)
        else:
            result[name] = ("index", ddl.split(" ON ")[1].split("(")[0], ddl)
    return result


def _read_records(connection):
    result = {}
    for table, (kind, _) in RECORDS.items():
        result[table] = {}
        for row in connection.execute(f"SELECT * FROM {table}"):
            value = parse_record(kind, row[-1], row[0])
            if tuple(row) != record_row(table, value):
                raise RootScopeAdmissionError("SQL projection differs")
            result[table][value.identity] = value
    for approval in result[POLICY_APPROVALS].values():
        content = result[POLICY_CONTENTS].get(approval.policy_content_identity)
        if content is None:
            raise RootScopeAdmissionError("missing immutable policy content")
        validate_policy_pair(content, approval)
    for scope in result[SCOPES].values():
        approval = result[POLICY_APPROVALS].get(scope.policy_approval_identity)
        if approval is None:
            raise RootScopeAdmissionError("scope lacks approved policy")
        content = result[POLICY_CONTENTS][approval.policy_content_identity]
        # Check full scope-policy agreement even for an inert content reservation.
        validate_scope_pair(scope, Availability(scope.identity, approval.identity,
                            scope.phase113_binding_identity, approval.policy_approved_at), content, approval)
    for receipt in result[AVAILABILITY].values():
        scope = result[SCOPES].get(receipt.scope_identity)
        if scope is None:
            raise RootScopeAdmissionError("missing immutable scope content")
        approval = result[POLICY_APPROVALS][scope.policy_approval_identity]
        validate_scope_pair(scope, receipt, result[POLICY_CONTENTS][approval.policy_content_identity], approval)
    return result


def phase114_schema_state(connection):
    if not isinstance(connection, sqlite3.Connection):
        return INTEGRITY_FAILURE
    try:
        objects = _objects(connection)
        if not objects:
            return NOT_INSTALLED
        if objects != _expected():
            return INTEGRITY_FAILURE
        if connection.execute(f"SELECT version,name FROM {REGISTRY}").fetchall() != [(VERSION, NAME)]:
            return INTEGRITY_FAILURE
        for table in (REGISTRY, *RECORDS):
            expected = [(i, 0, parent, col, "identity", "NO ACTION", "NO ACTION", "NONE")
                        for i, (col, parent) in enumerate(reversed(_PARENTS.get(table, ())))]
            if connection.execute(f"PRAGMA foreign_key_list({table})").fetchall() != expected:
                return INTEGRITY_FAILURE
        for suffix, (table, columns) in _KEYS.items():
            name = "nar_pre_c_root_scope_unique_" + suffix
            if [r[2] for r in connection.execute(f"PRAGMA index_info({name})")] != list(columns):
                return INTEGRITY_FAILURE
            if not any(r[1] == name and r[2] == 1 and r[4] == 0 for r in connection.execute(f"PRAGMA index_list({table})")):
                return INTEGRITY_FAILURE
        if connection.execute("PRAGMA foreign_key_check").fetchall():
            return INTEGRITY_FAILURE
        _read_records(connection)
        return ACTIVE
    except (RootScopeAdmissionError, ValueError):
        return INTEGRITY_FAILURE
    except sqlite3.OperationalError as exc:
        if str(exc).lower().startswith(("no such table:", "no such column:", "malformed database schema")):
            return INTEGRITY_FAILURE
        raise


def require_phase114_schema(connection):
    state = phase114_schema_state(connection)
    if state != ACTIVE:
        raise RuntimeError(f"exact active Phase114 companion required: {state}")


def apply(connection):
    if not isinstance(connection, sqlite3.Connection) or connection.in_transaction:
        raise RuntimeError("idle injected companion connection required")
    connection.execute("PRAGMA foreign_keys=ON")
    if connection.execute("PRAGMA foreign_keys").fetchone() != (1,):
        raise RuntimeError("companion installation requires foreign keys")
    state = phase114_schema_state(connection)
    if state == ACTIVE:
        return
    if state != NOT_INSTALLED:
        raise RuntimeError("contradictory Phase114 companion schema")
    connection.execute("BEGIN IMMEDIATE")
    try:
        state = phase114_schema_state(connection)
        if state == NOT_INSTALLED:
            for ddl in _DDL.values():
                connection.execute(ddl)
            connection.execute(f"INSERT INTO {REGISTRY} VALUES(?,?)", (VERSION, NAME))
        require_phase114_schema(connection)
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
