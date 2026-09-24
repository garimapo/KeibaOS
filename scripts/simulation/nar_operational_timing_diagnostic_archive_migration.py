"""Explicit diagnostic-only companion, never part of normal Phase105 bootstrap."""

from __future__ import annotations

import sqlite3

from scripts.simulation import nar_operational_timing_observability_archive_migration as base
from scripts.simulation import nar_operational_timing_activation_archive_migration as activation
from scripts.simulation import nar_operational_timing_v2_authority_archive_migration as v2
from scripts.simulation import nar_operational_timing_runtime_execution_archive_migration as runtime
from scripts.simulation import nar_operational_timing_attempt_archive_migration as attempt
from scripts.simulation.nar_operational_timing_campaign_lock import NAROperationalTimingCampaignLock


VERSION = 1
NAME = "v001_nar_operational_timing_diagnostic_companion"
REGISTRY = "nar_operational_timing_diagnostic_schema_migrations"
FIXTURES = "nar_operational_timing_diagnostic_fixture_bundles"
PLANS = "nar_operational_timing_diagnostic_plans"
NODES = "nar_operational_timing_diagnostic_plan_nodes"
DECLARATIONS = "nar_operational_timing_diagnostic_execution_declarations"

_DDL = {
    REGISTRY: f"CREATE TABLE {REGISTRY} (version INTEGER PRIMARY KEY CHECK(version=1), name TEXT NOT NULL CHECK(name='{NAME}')) WITHOUT ROWID",
    FIXTURES: f"CREATE TABLE {FIXTURES} (identity TEXT PRIMARY KEY, payload_json TEXT NOT NULL) WITHOUT ROWID",
    PLANS: (
        f"CREATE TABLE {PLANS} (identity TEXT PRIMARY KEY, "
        f"fixture_identity TEXT NOT NULL REFERENCES {FIXTURES}(identity) ON UPDATE RESTRICT ON DELETE RESTRICT, "
        f"session_identity TEXT NOT NULL REFERENCES {v2.SESSIONS}(identity) ON UPDATE RESTRICT ON DELETE RESTRICT, "
        f"configuration_identity TEXT NOT NULL REFERENCES {v2.CONFIGS}(identity) ON UPDATE RESTRICT ON DELETE RESTRICT, "
        "payload_json TEXT NOT NULL, UNIQUE(session_identity)) WITHOUT ROWID"
    ),
    NODES: (
        f"CREATE TABLE {NODES} (identity TEXT PRIMARY KEY, "
        f"plan_identity TEXT NOT NULL REFERENCES {PLANS}(identity) ON UPDATE RESTRICT ON DELETE RESTRICT, "
        "node_key TEXT NOT NULL, attempt_sequence INTEGER NOT NULL CHECK(attempt_sequence>=0), "
        "stage TEXT NOT NULL, http_policy TEXT, payload_json TEXT NOT NULL, "
        "UNIQUE(plan_identity,node_key), UNIQUE(plan_identity,attempt_sequence)) WITHOUT ROWID"
    ),
    DECLARATIONS: (
        f"CREATE TABLE {DECLARATIONS} (identity TEXT PRIMARY KEY, "
        f"plan_identity TEXT NOT NULL UNIQUE REFERENCES {PLANS}(identity) ON UPDATE RESTRICT ON DELETE RESTRICT, "
        f"claim_identity TEXT NOT NULL UNIQUE REFERENCES {runtime.CLAIMS}(identity) ON UPDATE RESTRICT ON DELETE RESTRICT, "
        "payload_json TEXT NOT NULL) WITHOUT ROWID"
    ),
}
for _table in (REGISTRY, FIXTURES, PLANS, NODES, DECLARATIONS):
    _DDL[f"trg_{_table}_no_update"] = (
        f"CREATE TRIGGER trg_{_table}_no_update BEFORE UPDATE ON {_table} "
        "BEGIN SELECT RAISE(ABORT, 'immutable diagnostic authority'); END"
    )
    _DDL[f"trg_{_table}_no_delete"] = (
        f"CREATE TRIGGER trg_{_table}_no_delete BEFORE DELETE ON {_table} "
        "BEGIN SELECT RAISE(ABORT, 'immutable diagnostic authority'); END"
    )
_DDL[f"trg_{PLANS}_parent_match"] = (
    f"CREATE TRIGGER trg_{PLANS}_parent_match BEFORE INSERT ON {PLANS} WHEN "
    f"(SELECT configuration_identity FROM {v2.SESSIONS} WHERE identity=NEW.session_identity) IS NOT NEW.configuration_identity "
    "BEGIN SELECT RAISE(ABORT, 'diagnostic plan parent contradiction'); END"
)
_DDL[f"trg_{DECLARATIONS}_parent_match"] = (
    f"CREATE TRIGGER trg_{DECLARATIONS}_parent_match BEFORE INSERT ON {DECLARATIONS} WHEN "
    f"(SELECT session_identity FROM {runtime.CLAIMS} WHERE identity=NEW.claim_identity) IS NOT "
    f"(SELECT session_identity FROM {PLANS} WHERE identity=NEW.plan_identity) OR "
    f"(SELECT configuration_identity FROM {runtime.CLAIMS} WHERE identity=NEW.claim_identity) IS NOT "
    f"(SELECT configuration_identity FROM {PLANS} WHERE identity=NEW.plan_identity) OR "
    f"EXISTS(SELECT 1 FROM {attempt.ATTEMPTS} WHERE claim_identity=NEW.claim_identity) "
    "BEGIN SELECT RAISE(ABORT, 'diagnostic declaration parent or causal order contradiction'); END"
)
_DDL[f"trg_{attempt.ATTEMPTS}_diagnostic_plan_gate"] = (
    f"CREATE TRIGGER trg_{attempt.ATTEMPTS}_diagnostic_plan_gate BEFORE INSERT ON {attempt.ATTEMPTS} WHEN "
    f"NOT EXISTS(SELECT 1 FROM {DECLARATIONS} d JOIN {NODES} n ON n.plan_identity=d.plan_identity "
    f"WHERE d.claim_identity=NEW.claim_identity AND n.stage=NEW.stage "
    f"AND n.http_policy IS NEW.http_policy AND n.attempt_sequence>=NEW.attempt_sequence) "
    "BEGIN SELECT RAISE(ABORT, 'diagnostic attempt is undeclared or mismatched'); END"
)


def require_nar_operational_timing_diagnostic_archive_schema(connection: sqlite3.Connection) -> None:
    connection = base._connection(connection)
    if base._objects(connection) != base._DDL | activation._DDL | v2._DDL | runtime._DDL | attempt._DDL | _DDL:
        raise RuntimeError("diagnostic archive topology is not the exact known union")
    for table, version, name in ((base.REGISTRY, base.VERSION, base.NAME),
                                 (activation.REGISTRY, activation.VERSION, activation.NAME),
                                 (v2.REGISTRY, v2.VERSION, v2.NAME),
                                 (runtime.REGISTRY, runtime.VERSION, runtime.NAME),
                                 (attempt.REGISTRY, attempt.VERSION, attempt.NAME),
                                 (REGISTRY, VERSION, NAME)):
        if connection.execute(f"SELECT version,name FROM {table}").fetchall() != [(version, name)]:
            raise RuntimeError("diagnostic archive migration registry differs")
    if connection.execute("PRAGMA foreign_key_check").fetchall():
        raise RuntimeError("diagnostic archive foreign key integrity failed")


def bootstrap_nar_operational_timing_diagnostic_archive(
    *, connection: sqlite3.Connection, campaign_lock: NAROperationalTimingCampaignLock,
) -> None:
    connection = base._connection(connection)
    if (connection.in_transaction or type(campaign_lock) is not NAROperationalTimingCampaignLock
            or not campaign_lock.held_by_current_process):
        raise RuntimeError("diagnostic companion needs idle connection and held campaign lock")
    connection.execute("BEGIN IMMEDIATE")
    try:
        objects = base._objects(connection)
        if objects == base._DDL | activation._DDL | v2._DDL | runtime._DDL | attempt._DDL:
            attempt.require_nar_operational_timing_attempt_archive_schema(connection)
            for statement in _DDL.values():
                connection.execute(statement)
            connection.execute(f"INSERT INTO {REGISTRY}(version,name) VALUES(?,?)", (VERSION, NAME))
        elif objects != base._DDL | activation._DDL | v2._DDL | runtime._DDL | attempt._DDL | _DDL:
            raise RuntimeError("diagnostic bootstrap requires exact Phase105 parent or exact diagnostic union")
        require_nar_operational_timing_diagnostic_archive_schema(connection)
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
