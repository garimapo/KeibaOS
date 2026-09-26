"""Explicit exact Phase108 rehearsal companion over Phase105, never normal bootstrap."""
from __future__ import annotations
import sqlite3
from scripts.simulation import nar_operational_timing_observability_archive_migration as base
from scripts.simulation import nar_operational_timing_activation_archive_migration as activation
from scripts.simulation import nar_operational_timing_v2_authority_archive_migration as v2
from scripts.simulation import nar_operational_timing_runtime_execution_archive_migration as runtime
from scripts.simulation import nar_operational_timing_attempt_archive_migration as attempt

REGISTRY = "nar_pre_c_envelope_schema_migrations"
NAME = "v001_nar_pre_c_diagnostic_envelope_companion"
VERSION = 1
MANIFESTS = "nar_pre_c_prestaged_manifests"
PLANS = "nar_pre_c_execution_plans"
ROOTS = "nar_pre_c_envelopes"
STARTS = "nar_pre_c_envelope_starts"
ENTRIES = "nar_pre_c_entry_closures"
HISTORIES = "nar_pre_c_history_closures"
COMPLETIONS = "nar_pre_c_envelope_completions"
REQUESTS = "nar_pre_c_authorized_request_projection"
DEPENDENCIES = "nar_pre_c_history_request_dependencies"

def _fk(table):
    return f"REFERENCES {table}(identity) ON UPDATE RESTRICT ON DELETE RESTRICT"

_DDL = {
    REGISTRY: f"CREATE TABLE {REGISTRY} (version INTEGER PRIMARY KEY CHECK(version=1), name TEXT NOT NULL CHECK(name='{NAME}')) WITHOUT ROWID",
    MANIFESTS: f"CREATE TABLE {MANIFESTS} (identity TEXT PRIMARY KEY, claim_identity TEXT NOT NULL {_fk(runtime.CLAIMS)}, scope_identity TEXT NOT NULL, payload_json TEXT NOT NULL, UNIQUE(claim_identity,scope_identity)) WITHOUT ROWID",
    PLANS: f"CREATE TABLE {PLANS} (identity TEXT PRIMARY KEY, manifest_identity TEXT NOT NULL UNIQUE {_fk(MANIFESTS)}, payload_json TEXT NOT NULL) WITHOUT ROWID",
    ROOTS: f"CREATE TABLE {ROOTS} (identity TEXT PRIMARY KEY, claim_identity TEXT NOT NULL {_fk(runtime.CLAIMS)}, manifest_identity TEXT NOT NULL UNIQUE {_fk(MANIFESTS)}, plan_identity TEXT NOT NULL UNIQUE {_fk(PLANS)}, payload_json TEXT NOT NULL) WITHOUT ROWID",
    STARTS: f"CREATE TABLE {STARTS} (identity TEXT PRIMARY KEY, root_identity TEXT NOT NULL UNIQUE {_fk(ROOTS)}, first_sequence INTEGER NOT NULL CHECK(first_sequence>=0), payload_json TEXT NOT NULL) WITHOUT ROWID",
    ENTRIES: f"CREATE TABLE {ENTRIES} (identity TEXT PRIMARY KEY, start_identity TEXT NOT NULL UNIQUE {_fk(STARTS)}, attempt_identity TEXT NOT NULL UNIQUE {_fk(attempt.ATTEMPTS)}, payload_json TEXT NOT NULL) WITHOUT ROWID",
    HISTORIES: f"CREATE TABLE {HISTORIES} (identity TEXT PRIMARY KEY, entry_closure_identity TEXT NOT NULL {_fk(ENTRIES)}, entry_identity TEXT NOT NULL, attempt_identity TEXT NOT NULL UNIQUE {_fk(attempt.ATTEMPTS)}, payload_json TEXT NOT NULL, UNIQUE(entry_closure_identity,entry_identity)) WITHOUT ROWID",
    COMPLETIONS: f"CREATE TABLE {COMPLETIONS} (identity TEXT PRIMARY KEY, start_identity TEXT NOT NULL UNIQUE {_fk(STARTS)}, payload_json TEXT NOT NULL) WITHOUT ROWID",
    REQUESTS: f"CREATE TABLE {REQUESTS} (start_identity TEXT NOT NULL {_fk(STARTS)}, url_sha256 TEXT NOT NULL, canonical_url TEXT NOT NULL, first_sequence INTEGER NOT NULL CHECK(first_sequence>=0), PRIMARY KEY(start_identity,url_sha256), UNIQUE(start_identity,canonical_url)) WITHOUT ROWID",
    DEPENDENCIES: f"CREATE TABLE {DEPENDENCIES} (history_closure_identity TEXT NOT NULL {_fk(HISTORIES)}, start_identity TEXT NOT NULL {_fk(STARTS)}, url_sha256 TEXT NOT NULL, PRIMARY KEY(history_closure_identity,url_sha256), FOREIGN KEY(start_identity,url_sha256) REFERENCES {REQUESTS}(start_identity,url_sha256) ON UPDATE RESTRICT ON DELETE RESTRICT) WITHOUT ROWID",
}
for table in (REGISTRY, MANIFESTS, PLANS, ROOTS, STARTS, ENTRIES, HISTORIES, COMPLETIONS, REQUESTS, DEPENDENCIES):
    for verb in ("UPDATE", "DELETE"):
        key = f"trg_{table}_no_{verb.lower()}"
        _DDL[key] = f"CREATE TRIGGER {key} BEFORE {verb} ON {table} BEGIN SELECT RAISE(ABORT, 'immutable PRE_C evidence'); END"
_DDL["trg_nar_pre_c_root_parent_match"] = (
    f"CREATE TRIGGER trg_nar_pre_c_root_parent_match BEFORE INSERT ON {ROOTS} WHEN "
    f"(SELECT claim_identity FROM {MANIFESTS} WHERE identity=NEW.manifest_identity) IS NOT NEW.claim_identity OR "
    f"(SELECT manifest_identity FROM {PLANS} WHERE identity=NEW.plan_identity) IS NOT NEW.manifest_identity "
    "BEGIN SELECT RAISE(ABORT, 'PRE_C root parent mismatch'); END")
_DDL["trg_nar_pre_c_dependency_parent_match"] = (
    f"CREATE TRIGGER trg_nar_pre_c_dependency_parent_match BEFORE INSERT ON {DEPENDENCIES} WHEN "
    f"NOT EXISTS(SELECT 1 FROM {HISTORIES} h JOIN {ENTRIES} e ON e.identity=h.entry_closure_identity "
    f"JOIN {REQUESTS} q ON q.start_identity=e.start_identity "
    "WHERE h.identity=NEW.history_closure_identity AND e.start_identity=NEW.start_identity "
    "AND q.url_sha256=NEW.url_sha256 "
    "AND q.first_sequence<=json_extract(h.payload_json,'$.first_authorized_sequence') "
    "AND EXISTS(SELECT 1 FROM json_each(h.payload_json,'$.events') event "
    "WHERE json_extract(event.value,'$[0]')='nar_actual_start' "
    "AND json_extract(event.value,'$[3]')=q.canonical_url)) "
    "BEGIN SELECT RAISE(ABORT, 'PRE_C dependency parent mismatch'); END")
_DDL["trg_nar_pre_c_start_no_backfill"] = (
    f"CREATE TRIGGER trg_nar_pre_c_start_no_backfill BEFORE INSERT ON {STARTS} WHEN "
    f"EXISTS(SELECT 1 FROM {attempt.ATTEMPTS} a JOIN {ROOTS} r ON r.claim_identity=a.claim_identity "
    "WHERE r.identity=NEW.root_identity AND a.attempt_sequence>=NEW.first_sequence) "
    "BEGIN SELECT RAISE(ABORT, 'PRE_C start cannot be backfilled'); END")
_DDL["trg_nar_pre_c_attempt_start_gate"] = (
    f"CREATE TRIGGER trg_nar_pre_c_attempt_start_gate BEFORE INSERT ON {attempt.ATTEMPTS} WHEN "
    f"NOT EXISTS(SELECT 1 FROM {STARTS} s JOIN {ROOTS} r ON r.identity=s.root_identity JOIN {REQUESTS} q ON q.start_identity=s.identity "
    "WHERE r.claim_identity=NEW.claim_identity AND q.first_sequence<=NEW.attempt_sequence "
    "AND NEW.stage='OFFICIAL_RESPONSE_ACQUISITION' AND NEW.http_policy='DIRECT_REQUEST_ENVIRONMENT_V1' "
    "AND q.url_sha256=json_extract(NEW.payload_json,'$.expected_request_url_sha256') "
    "AND json_extract(r.payload_json,'$.scope.value.external_race_id')=json_extract(NEW.payload_json,'$.correlation.external_race_id') "
    "AND json_extract(r.payload_json,'$.scope.value.cutoff_plan_sha256')=json_extract(NEW.payload_json,'$.correlation.cutoff_plan_sha256') "
    "AND json_extract(r.payload_json,'$.scope.value.target_set_sha256')=json_extract(NEW.payload_json,'$.correlation.target_set_sha256')) OR "
    f"EXISTS(SELECT 1 FROM {attempt.ATTEMPTS} a WHERE a.claim_identity=NEW.claim_identity "
    "AND json_extract(a.payload_json,'$.expected_request_url_sha256')=json_extract(NEW.payload_json,'$.expected_request_url_sha256') "
    "AND json_extract(a.payload_json,'$.correlation.external_race_id')=json_extract(NEW.payload_json,'$.correlation.external_race_id')) "
    "BEGIN SELECT RAISE(ABORT, 'PRE_C request is unauthorized or repeated'); END")

def parent_ddl():
    return base._DDL | activation._DDL | v2._DDL | runtime._DDL | attempt._DDL

def require_nar_pre_c_operational_envelope_archive_schema(connection: sqlite3.Connection):
    connection = base._connection(connection)
    if base._objects(connection) != parent_ddl() | _DDL:
        raise RuntimeError("Phase108 topology is not the exact approved union")
    for module in (base, activation, v2, runtime, attempt):
        if connection.execute(f"SELECT version,name FROM {module.REGISTRY}").fetchall() != [(module.VERSION, module.NAME)]:
            raise RuntimeError("Phase108 parent registry differs")
    if connection.execute(f"SELECT version,name FROM {REGISTRY}").fetchall() != [(VERSION, NAME)]:
        raise RuntimeError("Phase108 registry differs")
    if connection.execute("PRAGMA foreign_key_check").fetchall():
        raise RuntimeError("Phase108 restrictive ancestry integrity failed")
