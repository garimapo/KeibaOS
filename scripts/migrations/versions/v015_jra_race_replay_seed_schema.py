"""Durable provider-specific JRA replay-seed identity schema."""

from __future__ import annotations

import sqlite3


VERSION = 15
NAME = "v015_jra_race_replay_seed_schema"

_UTC_CHECK = """typeof(%s) = 'text' AND length(%s) = 32
    AND substr(%s, 11, 1) = 'T' AND substr(%s, 20, 1) = '.' AND substr(%s, -6) = '+00:00'
    AND %s GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]+00:00'"""

_EXPECTED_MIGRATIONS = {
    8: "v008_simulation_schema",
    9: "v009_simulation_bet_plan_schema",
    10: "v010_historical_input_snapshot_schema",
    11: "v011_historical_past_race_time_difference_schema",
    12: "v012_historical_input_evidence_schema",
    13: "v013_historical_past_race_race_time_domain_schema",
    14: "v014_historical_input_request_identity_schema",
}


def _columns(connection: sqlite3.Connection, table: str) -> tuple[str, ...]:
    return tuple(row[1] for row in connection.execute(f"PRAGMA table_info({table})"))


def _has_unique_parent_key(connection: sqlite3.Connection, table: str, columns: tuple[str, ...]) -> bool:
    for index in connection.execute(f"PRAGMA index_list({table})"):
        if index[2] != 1:
            continue
        name = index[1]
        if tuple(row[2] for row in connection.execute(f"PRAGMA index_info({name})")) == columns:
            return True
    return False


def _require_v014(connection: sqlite3.Connection) -> None:
    names = {
        row[0]
        for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    required_tables = {
        "schema_migrations",
        "races",
        "horses",
        "historical_input_source_identities",
        "historical_input_external_races",
        "historical_input_external_entries",
        "historical_input_snapshot_provenance_evidence",
    }
    if not required_tables <= names:
        raise RuntimeError("v015 requires the complete registered v014 application schema")
    applied = dict(connection.execute("SELECT version,name FROM schema_migrations"))
    if applied != _EXPECTED_MIGRATIONS:
        raise RuntimeError("v015 requires the exact registered v014 application schema")
    if _columns(connection, "historical_input_source_identities") != ("organization", "source_system"):
        raise RuntimeError("v015 source identity schema is invalid")
    if _columns(connection, "historical_input_external_races") != (
        "organization", "source_system", "external_race_id", "internal_race_id"
    ):
        raise RuntimeError("v015 external race mapping schema is invalid")
    if _columns(connection, "historical_input_external_entries") != (
        "organization", "source_system", "external_race_id", "external_entry_id", "internal_race_id", "race_entry_id"
    ):
        raise RuntimeError("v015 external entry mapping schema is invalid")
    if not _has_unique_parent_key(
        connection,
        "historical_input_external_races",
        ("organization", "source_system", "external_race_id", "internal_race_id"),
    ):
        raise RuntimeError("v015 requires the v010 exact external race mapping key")
    if not _has_unique_parent_key(connection, "horses", ("race_id", "id")):
        raise RuntimeError("v015 requires the v010 horses race-membership key")


def apply(connection: sqlite3.Connection) -> None:
    """Add immutable JRA replay seeds without owning transaction boundaries."""

    _require_v014(connection)
    connection.execute(
        """CREATE UNIQUE INDEX ux_historical_input_external_entries_exact_mapping
           ON historical_input_external_entries(
               organization, source_system, external_race_id, external_entry_id,
               internal_race_id, race_entry_id
           )"""
    )
    connection.execute(
        f"""CREATE TABLE jra_race_replay_seeds (
            seed_id TEXT PRIMARY KEY CHECK (
                typeof(seed_id) = 'text' AND length(seed_id) = 88
                AND substr(seed_id, 1, 24) = 'jra-race-replay-seed-v1:'
                AND substr(seed_id, 25) NOT GLOB '*[^0-9a-f]*'
            ),
            schema_version INTEGER NOT NULL CHECK (typeof(schema_version) = 'integer' AND schema_version = 1),
            content_sha256 TEXT NOT NULL CHECK (
                typeof(content_sha256) = 'text' AND length(content_sha256) = 64
                AND content_sha256 NOT GLOB '*[^0-9a-f]*'
            ),
            dataset_id TEXT NOT NULL CHECK (typeof(dataset_id) = 'text' AND dataset_id <> ''),
            organization TEXT NOT NULL CHECK (organization = 'JRA'),
            source_system TEXT NOT NULL CHECK (source_system = 'jra_official'),
            external_race_id TEXT NOT NULL CHECK (typeof(external_race_id) = 'text' AND external_race_id <> ''),
            internal_race_id INTEGER NOT NULL CHECK (typeof(internal_race_id) = 'integer' AND internal_race_id > 0),
            target_race_selection_capture_id TEXT NOT NULL CHECK (
                typeof(target_race_selection_capture_id) = 'text' AND length(target_race_selection_capture_id) = 79
                AND substr(target_race_selection_capture_id, 1, 15) = 'jra-capture-v4:'
                AND substr(target_race_selection_capture_id, 16) NOT GLOB '*[^0-9a-f]*'
            ),
            target_race_card_capture_id TEXT NOT NULL CHECK (
                typeof(target_race_card_capture_id) = 'text' AND length(target_race_card_capture_id) = 79
                AND substr(target_race_card_capture_id, 1, 15) = 'jra-capture-v3:'
                AND substr(target_race_card_capture_id, 16) NOT GLOB '*[^0-9a-f]*'
            ),
            target_race_card_response_sha256 TEXT NOT NULL CHECK (
                typeof(target_race_card_response_sha256) = 'text' AND length(target_race_card_response_sha256) = 64
                AND target_race_card_response_sha256 NOT GLOB '*[^0-9a-f]*'
            ),
            canonical_target_race_card_url TEXT NOT NULL CHECK (
                typeof(canonical_target_race_card_url) = 'text' AND canonical_target_race_card_url <> ''
            ),
            captured_at_utc TEXT NOT NULL CHECK ({_UTC_CHECK % ("captured_at_utc", "captured_at_utc", "captured_at_utc", "captured_at_utc", "captured_at_utc", "captured_at_utc")}),
            information_cutoff_utc TEXT NOT NULL CHECK ({_UTC_CHECK % ("information_cutoff_utc", "information_cutoff_utc", "information_cutoff_utc", "information_cutoff_utc", "information_cutoff_utc", "information_cutoff_utc")}),
            CHECK (captured_at_utc <= information_cutoff_utc),
            CHECK (substr(seed_id, 25) = content_sha256),
            UNIQUE (
                schema_version, dataset_id, external_race_id, target_race_selection_capture_id,
                captured_at_utc, information_cutoff_utc
            ),
            FOREIGN KEY (organization, source_system, external_race_id, internal_race_id)
                REFERENCES historical_input_external_races(
                    organization, source_system, external_race_id, internal_race_id
                ) ON DELETE RESTRICT ON UPDATE RESTRICT,
            FOREIGN KEY (internal_race_id) REFERENCES races(id) ON DELETE RESTRICT ON UPDATE RESTRICT
        ) WITHOUT ROWID"""
    )
    connection.execute(
        """CREATE TABLE jra_race_replay_seed_entries (
            seed_id TEXT NOT NULL,
            organization TEXT NOT NULL CHECK (organization = 'JRA'),
            source_system TEXT NOT NULL CHECK (source_system = 'jra_official'),
            external_race_id TEXT NOT NULL CHECK (typeof(external_race_id) = 'text' AND external_race_id <> ''),
            internal_race_id INTEGER NOT NULL CHECK (typeof(internal_race_id) = 'integer' AND internal_race_id > 0),
            entry_order INTEGER NOT NULL CHECK (typeof(entry_order) = 'integer' AND entry_order >= 0),
            external_entry_id TEXT NOT NULL CHECK (typeof(external_entry_id) = 'text' AND external_entry_id <> ''),
            external_horse_id TEXT NOT NULL CHECK (typeof(external_horse_id) = 'text' AND external_horse_id <> ''),
            horse_no INTEGER NOT NULL CHECK (typeof(horse_no) = 'integer' AND horse_no > 0),
            internal_race_entry_id INTEGER NOT NULL CHECK (
                typeof(internal_race_entry_id) = 'integer' AND internal_race_entry_id > 0
            ),
            PRIMARY KEY (seed_id, entry_order),
            UNIQUE (seed_id, external_entry_id),
            UNIQUE (seed_id, external_horse_id),
            UNIQUE (seed_id, horse_no),
            UNIQUE (seed_id, internal_race_entry_id),
            FOREIGN KEY (seed_id) REFERENCES jra_race_replay_seeds(seed_id)
                ON DELETE RESTRICT ON UPDATE RESTRICT,
            FOREIGN KEY (
                organization, source_system, external_race_id, external_entry_id,
                internal_race_id, internal_race_entry_id
            ) REFERENCES historical_input_external_entries(
                organization, source_system, external_race_id, external_entry_id,
                internal_race_id, race_entry_id
            ) ON DELETE RESTRICT ON UPDATE RESTRICT,
            FOREIGN KEY (internal_race_id, internal_race_entry_id)
                REFERENCES horses(race_id, id) ON DELETE RESTRICT ON UPDATE RESTRICT
        ) WITHOUT ROWID"""
    )
