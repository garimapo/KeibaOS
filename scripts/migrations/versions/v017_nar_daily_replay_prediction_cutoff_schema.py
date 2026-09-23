"""Append-only prediction-cutoff provenance beside immutable v016 results."""

from __future__ import annotations

import sqlite3

from .v016_nar_daily_replay_result_schema import require_v016_schema_contract


VERSION = 17
NAME = "v017_nar_daily_replay_prediction_cutoff_schema"

_EXPECTED_PRIOR = {
    8: "v008_simulation_schema", 9: "v009_simulation_bet_plan_schema",
    10: "v010_historical_input_snapshot_schema",
    11: "v011_historical_past_race_time_difference_schema",
    12: "v012_historical_input_evidence_schema",
    13: "v013_historical_past_race_race_time_domain_schema",
    14: "v014_historical_input_request_identity_schema",
    15: "v015_jra_race_replay_seed_schema",
    16: "v016_nar_daily_replay_result_schema",
}
_TABLE = "nar_daily_replay_prediction_cutoff_plans"
_OBJECTS = (_TABLE, "nar_daily_replay_prediction_cutoff_plans_no_update",
            "nar_daily_replay_prediction_cutoff_plans_no_delete")


def _create_schema_objects(connection: sqlite3.Connection) -> None:
    connection.execute(
        """CREATE TABLE nar_daily_replay_prediction_cutoff_plans (
            persisted_content_sha256 TEXT PRIMARY KEY,
            prediction_cutoff_plan_sha256 TEXT NOT NULL CHECK (
                length(prediction_cutoff_plan_sha256)=64
                AND prediction_cutoff_plan_sha256 NOT GLOB '*[^0-9a-f]*'
            ),
            prediction_cutoff_plan_json TEXT NOT NULL CHECK (prediction_cutoff_plan_json<>''),
            FOREIGN KEY (persisted_content_sha256)
                REFERENCES nar_daily_replay_results(persisted_content_sha256)
                ON DELETE RESTRICT ON UPDATE RESTRICT
        ) WITHOUT ROWID"""
    )
    connection.execute(
        """CREATE TRIGGER nar_daily_replay_prediction_cutoff_plans_no_update
           BEFORE UPDATE ON nar_daily_replay_prediction_cutoff_plans
           BEGIN SELECT RAISE(ABORT,'prediction cutoff plans are immutable'); END"""
    )
    connection.execute(
        """CREATE TRIGGER nar_daily_replay_prediction_cutoff_plans_no_delete
           BEFORE DELETE ON nar_daily_replay_prediction_cutoff_plans
           BEGIN SELECT RAISE(ABORT,'prediction cutoff plans are immutable'); END"""
    )


def _schema_contract(connection: sqlite3.Connection) -> tuple[object, ...]:
    return (
        tuple(connection.execute(
            "SELECT type,name,tbl_name,sql FROM sqlite_schema WHERE tbl_name=? ORDER BY type,name",
            (_TABLE,),
        )),
        tuple(connection.execute(f"PRAGMA table_xinfo({_TABLE})")),
        tuple(connection.execute(f"PRAGMA foreign_key_list({_TABLE})")),
        tuple(connection.execute(f"PRAGMA index_list({_TABLE})")),
        tuple(row for row in connection.execute("PRAGMA table_list") if row[1] == _TABLE),
    )


def require_v017_schema_contract(connection: sqlite3.Connection) -> None:
    if type(connection) is not sqlite3.Connection or connection.execute("PRAGMA foreign_keys").fetchone() != (1,):
        raise RuntimeError("v017 requires exact connection with foreign keys")
    reference = sqlite3.connect(":memory:")
    try:
        reference.execute("PRAGMA foreign_keys=ON")
        _create_schema_objects(reference)
        expected = _schema_contract(reference)
    finally:
        reference.close()
    if _schema_contract(connection) != expected:
        raise RuntimeError("v017 cutoff companion schema contract is incompatible")


def apply(connection: sqlite3.Connection) -> None:
    if type(connection) is not sqlite3.Connection or connection.execute("PRAGMA foreign_keys").fetchone() != (1,):
        raise RuntimeError("v017 requires foreign keys enabled")
    if dict(connection.execute("SELECT version,name FROM schema_migrations")) != _EXPECTED_PRIOR:
        raise RuntimeError("v017 requires exact registered v016 schema")
    require_v016_schema_contract(connection)
    if any(connection.execute("SELECT 1 FROM sqlite_schema WHERE name=?", (name,)).fetchone()
           for name in _OBJECTS):
        raise RuntimeError("v017 companion objects already exist without migration")
    _create_schema_objects(connection)
    require_v016_schema_contract(connection)
    require_v017_schema_contract(connection)
