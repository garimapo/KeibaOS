"""Replace scalar historical provenance timestamps with nested evidence."""

from __future__ import annotations

import sqlite3


VERSION = 12
NAME = "v012_historical_input_evidence_schema"


def apply(connection: sqlite3.Connection) -> None:
    if connection.execute("SELECT COUNT(*) FROM historical_input_snapshots").fetchone()[0] != 0:
        raise RuntimeError("cannot migrate nonempty historical input snapshot store to evidence semantics")
    connection.execute("ALTER TABLE historical_input_snapshot_provenance RENAME TO historical_input_snapshot_provenance_v2")
    connection.execute(
        """CREATE TABLE historical_input_snapshot_provenance (
            snapshot_id INTEGER NOT NULL,
            input_type TEXT NOT NULL CHECK (input_type IN ('track', 'entry', 'odds', 'jockey', 'past_race')),
            audit_key TEXT NOT NULL CHECK (typeof(audit_key) = 'text' AND audit_key <> ''),
            source TEXT NOT NULL CHECK (typeof(source) = 'text' AND source <> ''),
            source_id TEXT NOT NULL CHECK (typeof(source_id) = 'text' AND source_id <> ''),
            race_entry_id INTEGER NULL CHECK (
                race_entry_id IS NULL OR (typeof(race_entry_id) = 'integer' AND race_entry_id > 0)
            ),
            past_race_index INTEGER NULL CHECK (
                past_race_index IS NULL OR (typeof(past_race_index) = 'integer' AND past_race_index >= 0)
            ),
            PRIMARY KEY (snapshot_id, audit_key),
            CHECK (
                (input_type = 'track' AND race_entry_id IS NULL AND past_race_index IS NULL)
                OR (input_type IN ('entry', 'odds', 'jockey') AND race_entry_id IS NOT NULL AND past_race_index IS NULL)
                OR (input_type = 'past_race' AND race_entry_id IS NOT NULL)
            ),
            FOREIGN KEY (snapshot_id) REFERENCES historical_input_snapshots (snapshot_id)
                ON DELETE RESTRICT ON UPDATE RESTRICT,
            FOREIGN KEY (snapshot_id, race_entry_id)
                REFERENCES historical_input_snapshot_entries (snapshot_id, race_entry_id)
                ON DELETE RESTRICT ON UPDATE RESTRICT,
            FOREIGN KEY (snapshot_id, race_entry_id, past_race_index)
                REFERENCES historical_input_snapshot_past_races (snapshot_id, race_entry_id, past_race_index)
                ON DELETE RESTRICT ON UPDATE RESTRICT
        ) WITHOUT ROWID"""
    )
    connection.execute("DROP TABLE historical_input_snapshot_provenance_v2")
    connection.execute(
        """CREATE TABLE historical_input_snapshot_provenance_evidence (
            snapshot_id INTEGER NOT NULL,
            audit_key TEXT NOT NULL CHECK (typeof(audit_key) = 'text' AND audit_key <> ''),
            evidence_order INTEGER NOT NULL CHECK (typeof(evidence_order) = 'integer' AND evidence_order >= 0),
            evidence_role TEXT NOT NULL CHECK (typeof(evidence_role) = 'text' AND evidence_role <> ''),
            canonical_source_url TEXT NULL CHECK (
                canonical_source_url IS NULL OR (typeof(canonical_source_url) = 'text' AND canonical_source_url <> '')
            ),
            response_sha256 TEXT NOT NULL CHECK (
                typeof(response_sha256) = 'text' AND length(response_sha256) = 64
                AND response_sha256 NOT GLOB '*[^0-9a-f]*'
            ),
            available_at_utc TEXT NULL CHECK (
                available_at_utc IS NULL OR (
                    typeof(available_at_utc) = 'text' AND length(available_at_utc) = 32
                    AND substr(available_at_utc, 11, 1) = 'T'
                    AND substr(available_at_utc, 20, 1) = '.'
                    AND substr(available_at_utc, -6) = '+00:00'
                    AND available_at_utc GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]+00:00'
                )
            ),
            observed_at_utc TEXT NOT NULL CHECK (
                typeof(observed_at_utc) = 'text' AND length(observed_at_utc) = 32
                AND substr(observed_at_utc, 11, 1) = 'T'
                AND substr(observed_at_utc, 20, 1) = '.'
                AND substr(observed_at_utc, -6) = '+00:00'
                AND observed_at_utc GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]+00:00'
            ),
            CHECK (available_at_utc IS NULL OR available_at_utc <= observed_at_utc),
            PRIMARY KEY (snapshot_id, audit_key, evidence_order),
            UNIQUE (snapshot_id, audit_key, evidence_role),
            FOREIGN KEY (snapshot_id, audit_key)
                REFERENCES historical_input_snapshot_provenance (snapshot_id, audit_key)
                ON DELETE RESTRICT ON UPDATE RESTRICT
        ) WITHOUT ROWID"""
    )
