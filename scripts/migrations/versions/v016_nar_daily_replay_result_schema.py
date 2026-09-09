"""Append-only NAR daily replay result persistence schema."""

from __future__ import annotations

import sqlite3


VERSION = 16
NAME = "v016_nar_daily_replay_result_schema"

_EXPECTED_MIGRATIONS = {
    8: "v008_simulation_schema",
    9: "v009_simulation_bet_plan_schema",
    10: "v010_historical_input_snapshot_schema",
    11: "v011_historical_past_race_time_difference_schema",
    12: "v012_historical_input_evidence_schema",
    13: "v013_historical_past_race_race_time_domain_schema",
    14: "v014_historical_input_request_identity_schema",
    15: "v015_jra_race_replay_seed_schema",
}

_RESULT_TABLE = "nar_daily_replay_results"
_BET_TYPE_TABLE = "nar_daily_replay_result_bet_type_summaries"
_OBJECTS = {
    _RESULT_TABLE,
    _BET_TYPE_TABLE,
    "nar_daily_replay_results_no_update",
    "nar_daily_replay_results_no_delete",
    "nar_daily_replay_result_bet_types_completed_insert",
    "nar_daily_replay_result_bet_types_no_update",
    "nar_daily_replay_result_bet_types_no_delete",
}


def _quoted_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _require_v015(connection: sqlite3.Connection) -> None:
    if connection.execute("PRAGMA foreign_keys").fetchone() != (1,):
        raise RuntimeError("v016 requires foreign_keys enabled")
    applied = dict(connection.execute("SELECT version,name FROM schema_migrations"))
    if applied != _EXPECTED_MIGRATIONS:
        raise RuntimeError("v016 requires the exact registered v015 application schema")
    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    required = {
        "schema_migrations",
        "races",
        "horses",
        "historical_input_snapshots",
        "simulation_bet_plans",
        "jra_race_replay_seeds",
    }
    if not required <= tables:
        raise RuntimeError("v016 requires the complete registered v015 application schema")
    existing = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE name IN (?,?,?,?,?,?,?)",
            tuple(sorted(_OBJECTS)),
        )
    }
    if existing:
        raise RuntimeError("v016 objects already exist without registered migration")


def _create_schema_objects(connection: sqlite3.Connection) -> None:
    """Create the schema objects from the single authoritative v016 DDL."""

    connection.execute(
        """CREATE TABLE nar_daily_replay_results (
            persisted_content_sha256 TEXT PRIMARY KEY CHECK (
                typeof(persisted_content_sha256)='text'
                AND length(persisted_content_sha256)=64
                AND persisted_content_sha256 NOT GLOB '*[^0-9a-f]*'
            ),
            schema_version INTEGER NOT NULL CHECK (
                typeof(schema_version)='integer' AND schema_version=1
            ),
            orchestration_audit_sha256 TEXT NOT NULL UNIQUE CHECK (
                length(orchestration_audit_sha256)=64
                AND orchestration_audit_sha256 NOT GLOB '*[^0-9a-f]*'
            ),
            target_date TEXT NOT NULL CHECK (
                length(target_date)=10 AND target_date GLOB
                '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
            ),
            organization TEXT NOT NULL CHECK (organization='NAR'),
            source_system TEXT NOT NULL CHECK (source_system='nar_official'),
            execution_state TEXT NOT NULL CHECK (execution_state IN (
                'FULL_DAY_REPLAY_COMPLETED',
                'NOT_RUN_PARTIAL_RESOLUTION',
                'NOT_RUN_NO_EXECUTABLE_TARGETS'
            )),
            resolution_state TEXT NOT NULL CHECK (resolution_state IN (
                'ALL_TARGETS_RESOLVED','PARTIALLY_RESOLVED','NO_EXECUTABLE_TARGETS'
            )),
            target_set_content_sha256 TEXT NOT NULL CHECK (
                length(target_set_content_sha256)=64
                AND target_set_content_sha256 NOT GLOB '*[^0-9a-f]*'
            ),
            supplier_evidence_identity TEXT NOT NULL CHECK (supplier_evidence_identity<>''),
            homepage_supplier_capture_id TEXT NOT NULL CHECK (homepage_supplier_capture_id<>''),
            monthly_root_supplier_capture_id TEXT NOT NULL CHECK (monthly_root_supplier_capture_id<>''),
            locator_script_supplier_capture_id TEXT NOT NULL CHECK (locator_script_supplier_capture_id<>''),
            monthly_capture_id TEXT NOT NULL CHECK (monthly_capture_id<>''),
            race_list_capture_ids_json TEXT NOT NULL CHECK (race_list_capture_ids_json<>''),
            dataset_id TEXT NOT NULL CHECK (dataset_id<>''),
            selection_policy TEXT NOT NULL CHECK (selection_policy='LATEST_CAUSAL_IN_DATASET'),
            settlement_information_cutoff_utc TEXT NOT NULL CHECK (
                length(settlement_information_cutoff_utc)=32
                AND substr(settlement_information_cutoff_utc,-6)='+00:00'
            ),
            canonical_target_count INTEGER NOT NULL CHECK (
                typeof(canonical_target_count)='integer' AND canonical_target_count>0
            ),
            executable_count INTEGER NOT NULL CHECK (
                typeof(executable_count)='integer' AND executable_count>=0
                AND executable_count<=canonical_target_count
            ),
            resolution_outcomes_json TEXT NOT NULL CHECK (resolution_outcomes_json<>''),
            run_id TEXT NOT NULL CHECK (run_id<>''),
            run_started_at_utc TEXT NOT NULL CHECK (
                length(run_started_at_utc)=32 AND substr(run_started_at_utc,-6)='+00:00'
            ),
            target_commit_id TEXT NOT NULL CHECK (target_commit_id<>''),
            strategy_id TEXT NOT NULL CHECK (strategy_id<>''),
            strategy_name TEXT NOT NULL CHECK (strategy_name<>''),
            strategy_config_hash TEXT NOT NULL CHECK (
                length(strategy_config_hash)=64
                AND strategy_config_hash NOT GLOB '*[^0-9a-f]*'
            ),
            race_budget_total_amount INTEGER NOT NULL CHECK (
                typeof(race_budget_total_amount)='integer'
                AND race_budget_total_amount>=0 AND race_budget_total_amount%100=0
            ),
            database_path TEXT NOT NULL CHECK (database_path<>''),
            nar_settlement_capture_archive_path TEXT NOT NULL CHECK (
                nar_settlement_capture_archive_path<>''
            ),
            configured_manifest_source_path TEXT NOT NULL CHECK (
                configured_manifest_source_path<>''
            ),
            published_manifest_path TEXT,
            manifest_sha256 TEXT CHECK (
                manifest_sha256 IS NULL OR (
                    length(manifest_sha256)=64
                    AND manifest_sha256 NOT GLOB '*[^0-9a-f]*'
                )
            ),
            summary_strategy_id TEXT,
            summary_strategy_name TEXT,
            summary_strategy_config_hash TEXT,
            summary_race_count INTEGER,
            summary_settled_race_count INTEGER,
            summary_unsettled_race_count INTEGER,
            summary_no_bet_race_count INTEGER,
            summary_void_race_count INTEGER,
            summary_error_race_count INTEGER,
            summary_unsupported_race_count INTEGER,
            summary_bet_count INTEGER,
            summary_settled_bet_count INTEGER,
            summary_settled_purchase_race_count INTEGER,
            summary_hit_bet_count INTEGER,
            summary_hit_race_count INTEGER,
            summary_investment INTEGER,
            summary_payout INTEGER,
            summary_profit INTEGER,
            summary_roi_text TEXT,
            summary_bet_hit_rate_text TEXT,
            summary_race_hit_rate_text TEXT,
            summary_maximum_drawdown INTEGER,
            CHECK (
                (execution_state='FULL_DAY_REPLAY_COMPLETED'
                 AND resolution_state='ALL_TARGETS_RESOLVED'
                 AND executable_count=canonical_target_count
                 AND published_manifest_path IS NOT NULL
                 AND manifest_sha256 IS NOT NULL
                 AND summary_strategy_id IS NOT NULL
                 AND summary_strategy_name IS NOT NULL
                 AND summary_strategy_config_hash IS NOT NULL
                 AND summary_race_count IS NOT NULL
                 AND summary_settled_race_count IS NOT NULL
                 AND summary_unsettled_race_count IS NOT NULL
                 AND summary_no_bet_race_count IS NOT NULL
                 AND summary_void_race_count IS NOT NULL
                 AND summary_error_race_count IS NOT NULL
                 AND summary_unsupported_race_count IS NOT NULL
                 AND summary_bet_count IS NOT NULL
                 AND summary_settled_bet_count IS NOT NULL
                 AND summary_settled_purchase_race_count IS NOT NULL
                 AND summary_hit_bet_count IS NOT NULL
                 AND summary_hit_race_count IS NOT NULL
                 AND summary_investment IS NOT NULL
                 AND summary_payout IS NOT NULL
                 AND summary_profit IS NOT NULL
                 AND summary_maximum_drawdown IS NOT NULL)
                OR
                (execution_state IN (
                    'NOT_RUN_PARTIAL_RESOLUTION','NOT_RUN_NO_EXECUTABLE_TARGETS'
                 )
                 AND ((execution_state='NOT_RUN_PARTIAL_RESOLUTION'
                       AND resolution_state='PARTIALLY_RESOLVED')
                      OR (execution_state='NOT_RUN_NO_EXECUTABLE_TARGETS'
                          AND resolution_state='NO_EXECUTABLE_TARGETS'))
                 AND published_manifest_path IS NULL AND manifest_sha256 IS NULL
                 AND summary_strategy_id IS NULL AND summary_strategy_name IS NULL
                 AND summary_strategy_config_hash IS NULL AND summary_race_count IS NULL
                 AND summary_settled_race_count IS NULL
                 AND summary_unsettled_race_count IS NULL
                 AND summary_no_bet_race_count IS NULL AND summary_void_race_count IS NULL
                 AND summary_error_race_count IS NULL
                 AND summary_unsupported_race_count IS NULL
                 AND summary_bet_count IS NULL AND summary_settled_bet_count IS NULL
                 AND summary_settled_purchase_race_count IS NULL
                 AND summary_hit_bet_count IS NULL AND summary_hit_race_count IS NULL
                 AND summary_investment IS NULL AND summary_payout IS NULL
                 AND summary_profit IS NULL AND summary_roi_text IS NULL
                 AND summary_bet_hit_rate_text IS NULL
                 AND summary_race_hit_rate_text IS NULL
                 AND summary_maximum_drawdown IS NULL)
            )
        ) WITHOUT ROWID"""
    )
    connection.execute(
        """CREATE TABLE nar_daily_replay_result_bet_type_summaries (
            persisted_content_sha256 TEXT NOT NULL,
            bet_type TEXT NOT NULL CHECK (bet_type<>''),
            bet_count INTEGER NOT NULL CHECK (typeof(bet_count)='integer' AND bet_count>=0),
            settled_bet_count INTEGER NOT NULL CHECK (
                typeof(settled_bet_count)='integer' AND settled_bet_count>=0
                AND settled_bet_count<=bet_count
            ),
            hit_bet_count INTEGER NOT NULL CHECK (
                typeof(hit_bet_count)='integer' AND hit_bet_count>=0
                AND hit_bet_count<=settled_bet_count
            ),
            investment INTEGER NOT NULL CHECK (typeof(investment)='integer' AND investment>=0),
            payout INTEGER NOT NULL CHECK (typeof(payout)='integer' AND payout>=0),
            profit INTEGER NOT NULL CHECK (typeof(profit)='integer'),
            roi_text TEXT,
            bet_hit_rate_text TEXT,
            PRIMARY KEY (persisted_content_sha256,bet_type),
            FOREIGN KEY (persisted_content_sha256)
                REFERENCES nar_daily_replay_results(persisted_content_sha256)
                ON DELETE RESTRICT ON UPDATE RESTRICT,
            CHECK (profit=payout-investment)
        ) WITHOUT ROWID"""
    )
    connection.execute(
        """CREATE TRIGGER nar_daily_replay_results_no_update
           BEFORE UPDATE ON nar_daily_replay_results
           BEGIN SELECT RAISE(ABORT,'nar daily replay results are immutable'); END"""
    )
    connection.execute(
        """CREATE TRIGGER nar_daily_replay_results_no_delete
           BEFORE DELETE ON nar_daily_replay_results
           BEGIN SELECT RAISE(ABORT,'nar daily replay results are immutable'); END"""
    )
    connection.execute(
        """CREATE TRIGGER nar_daily_replay_result_bet_types_completed_insert
           BEFORE INSERT ON nar_daily_replay_result_bet_type_summaries
           WHEN NOT EXISTS (
               SELECT 1 FROM nar_daily_replay_results
               WHERE persisted_content_sha256=NEW.persisted_content_sha256
                 AND execution_state='FULL_DAY_REPLAY_COMPLETED'
           )
           BEGIN SELECT RAISE(ABORT,'bet-type summaries require completed result'); END"""
    )
    connection.execute(
        """CREATE TRIGGER nar_daily_replay_result_bet_types_no_update
           BEFORE UPDATE ON nar_daily_replay_result_bet_type_summaries
           BEGIN SELECT RAISE(ABORT,'nar daily replay bet-type summaries are immutable'); END"""
    )
    connection.execute(
        """CREATE TRIGGER nar_daily_replay_result_bet_types_no_delete
           BEFORE DELETE ON nar_daily_replay_result_bet_type_summaries
           BEGIN SELECT RAISE(ABORT,'nar daily replay bet-type summaries are immutable'); END"""
    )


def _schema_contract(connection: sqlite3.Connection) -> tuple[object, ...]:
    object_rows = tuple(
        connection.execute(
            """SELECT type,name,tbl_name,sql
               FROM sqlite_schema
               WHERE tbl_name IN (?,?)
               ORDER BY type,name""",
            (_RESULT_TABLE, _BET_TYPE_TABLE),
        )
    )
    table_contracts = []
    for table_name in (_RESULT_TABLE, _BET_TYPE_TABLE):
        columns = tuple(connection.execute(f"PRAGMA table_xinfo({table_name})"))
        foreign_keys = tuple(connection.execute(f"PRAGMA foreign_key_list({table_name})"))
        indexes = tuple(
            sorted(
                (row[1], row[2], row[3], row[4])
                for row in connection.execute(f"PRAGMA index_list({table_name})")
            )
        )
        index_columns = tuple(
            (
                index_name,
                tuple(
                    connection.execute(
                        f"PRAGMA index_xinfo({_quoted_identifier(index_name)})"
                    )
                ),
            )
            for index_name, *_ in indexes
        )
        table_list = tuple(
            row
            for row in connection.execute("PRAGMA table_list")
            if row[1] == table_name
        )
        table_contracts.append(
            (table_name, columns, foreign_keys, indexes, index_columns, table_list)
        )
    return object_rows, tuple(table_contracts)


def require_v016_schema_contract(connection: sqlite3.Connection) -> None:
    """Fail unless ``connection`` has the exact schema created by this migration."""

    if type(connection) is not sqlite3.Connection:
        raise RuntimeError("v016 schema verification requires exact sqlite3.Connection")
    if connection.execute("PRAGMA foreign_keys").fetchone() != (1,):
        raise RuntimeError("v016 schema verification requires foreign_keys enabled")
    reference = sqlite3.connect(":memory:")
    try:
        reference.execute("PRAGMA foreign_keys=ON")
        _create_schema_objects(reference)
        expected = _schema_contract(reference)
    finally:
        reference.close()
    if _schema_contract(connection) != expected:
        raise RuntimeError("v016 daily replay result schema contract is incompatible")


def apply(connection: sqlite3.Connection) -> None:
    """Create immutable daily result records without owning transaction boundaries."""

    _require_v015(connection)
    _create_schema_objects(connection)
