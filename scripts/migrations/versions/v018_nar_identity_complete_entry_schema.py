"""Add exact NAR entry identity provenance and durable selection denial."""

from __future__ import annotations

import sqlite3

from .v017_nar_daily_replay_prediction_cutoff_schema import require_v017_schema_contract


VERSION = 18
NAME = "v018_nar_identity_complete_entry_schema"

PHASE110_SCHEMA_NOT_INSTALLED = "PHASE110_SCHEMA_NOT_INSTALLED"
PHASE110_SCHEMA_ACTIVE = "PHASE110_SCHEMA_ACTIVE"
PHASE110_SCHEMA_INTEGRITY_FAILURE = "PHASE110_SCHEMA_INTEGRITY_FAILURE"

_EXPECTED_PRIOR = {
    8: "v008_simulation_schema",
    9: "v009_simulation_bet_plan_schema",
    10: "v010_historical_input_snapshot_schema",
    11: "v011_historical_past_race_time_difference_schema",
    12: "v012_historical_input_evidence_schema",
    13: "v013_historical_past_race_race_time_domain_schema",
    14: "v014_historical_input_request_identity_schema",
    15: "v015_jra_race_replay_seed_schema",
    16: "v016_nar_daily_replay_result_schema",
    17: "v017_nar_daily_replay_prediction_cutoff_schema",
}

_TABLES = (
    "nar_identity_complete_receipts",
    "nar_identity_complete_entries",
    "nar_identity_complete_denials",
)
_INDEXES = (
    "nar_identity_complete_unique_race_key",
    "nar_identity_complete_unique_horse_key",
)


def _create_schema_objects(connection: sqlite3.Connection) -> None:
    connection.execute(
        """CREATE UNIQUE INDEX nar_identity_complete_unique_race_key
           ON races(race_date, organization, place, race_no)
           WHERE race_date IS NOT NULL AND organization IS NOT NULL
             AND place IS NOT NULL AND race_no IS NOT NULL"""
    )
    connection.execute(
        """CREATE UNIQUE INDEX nar_identity_complete_unique_horse_key
           ON horses(race_id, horse_no)
           WHERE race_id IS NOT NULL AND horse_no IS NOT NULL"""
    )
    connection.execute(
        """CREATE TABLE nar_identity_complete_receipts (
            receipt_id TEXT PRIMARY KEY NOT NULL,
            external_race_id TEXT NOT NULL UNIQUE,
            race_id INTEGER NOT NULL UNIQUE CHECK(typeof(race_id)='integer' AND race_id>0),
            canonical_deba_url TEXT NOT NULL,
            phase111_declaration_id TEXT NOT NULL,
            phase111_receipt_id TEXT NOT NULL,
            phase111_capture_id TEXT NOT NULL,
            response_sha256 TEXT NOT NULL CHECK(length(response_sha256)=64),
            observed_at TEXT NOT NULL,
            prediction_cutoff TEXT NOT NULL,
            population_sha256 TEXT NOT NULL CHECK(length(population_sha256)=64),
            population_count INTEGER NOT NULL CHECK(population_count>0),
            receipt_json TEXT NOT NULL,
            UNIQUE(receipt_id, race_id),
            FOREIGN KEY(race_id) REFERENCES races(id)
                ON DELETE RESTRICT ON UPDATE RESTRICT
        ) WITHOUT ROWID"""
    )
    connection.execute(
        """CREATE TABLE nar_identity_complete_entries (
            receipt_id TEXT NOT NULL,
            external_entry_id TEXT NOT NULL,
            race_id INTEGER NOT NULL,
            horse_id INTEGER NOT NULL CHECK(typeof(horse_id)='integer' AND horse_id>0),
            horse_no INTEGER NOT NULL CHECK(typeof(horse_no)='integer' AND horse_no>0),
            external_horse_id TEXT,
            issuance_disposition TEXT NOT NULL CHECK(issuance_disposition IN
                ('ADOPTED_EXISTING_INTERNAL_ID','ISSUED_IDENTITY_ONLY_INTERNAL_ID')),
            PRIMARY KEY(receipt_id, external_entry_id),
            UNIQUE(receipt_id, horse_id),
            UNIQUE(receipt_id, horse_no),
            UNIQUE(receipt_id, external_entry_id, race_id, horse_id),
            FOREIGN KEY(receipt_id, race_id)
                REFERENCES nar_identity_complete_receipts(receipt_id, race_id)
                ON DELETE RESTRICT ON UPDATE RESTRICT,
            FOREIGN KEY(race_id, horse_id) REFERENCES horses(race_id, id)
                ON DELETE RESTRICT ON UPDATE RESTRICT
        ) WITHOUT ROWID"""
    )
    connection.execute(
        """CREATE TABLE nar_identity_complete_denials (
            horse_id INTEGER PRIMARY KEY NOT NULL,
            receipt_id TEXT NOT NULL,
            external_entry_id TEXT NOT NULL,
            race_id INTEGER NOT NULL,
            denial_reason TEXT NOT NULL CHECK(denial_reason='PHASE110_ISSUED_IDENTITY_ONLY'),
            FOREIGN KEY(receipt_id, external_entry_id, race_id, horse_id)
                REFERENCES nar_identity_complete_entries
                    (receipt_id, external_entry_id, race_id, horse_id)
                ON DELETE RESTRICT ON UPDATE RESTRICT
        ) WITHOUT ROWID"""
    )
    connection.execute(
        """CREATE TRIGGER nar_identity_complete_entries_issue_denial
           AFTER INSERT ON nar_identity_complete_entries
           WHEN NEW.issuance_disposition='ISSUED_IDENTITY_ONLY_INTERNAL_ID'
           BEGIN
               INSERT INTO nar_identity_complete_denials
                   (horse_id, receipt_id, external_entry_id, race_id, denial_reason)
               VALUES (NEW.horse_id, NEW.receipt_id, NEW.external_entry_id,
                       NEW.race_id, 'PHASE110_ISSUED_IDENTITY_ONLY');
           END"""
    )
    connection.execute(
        """CREATE TRIGGER nar_identity_complete_horse_identity_update
           BEFORE UPDATE OF id, race_id, horse_no ON horses
           WHEN (OLD.id IS NOT NEW.id OR OLD.race_id IS NOT NEW.race_id
                 OR OLD.horse_no IS NOT NEW.horse_no)
            AND EXISTS (SELECT 1 FROM nar_identity_complete_entries WHERE horse_id=OLD.id)
           BEGIN SELECT RAISE(ABORT, 'Phase110 horse identity is immutable'); END"""
    )
    connection.execute(
        """CREATE TRIGGER nar_identity_complete_horse_identity_delete
           BEFORE DELETE ON horses
           WHEN EXISTS (SELECT 1 FROM nar_identity_complete_entries WHERE horse_id=OLD.id)
           BEGIN SELECT RAISE(ABORT, 'Phase110 horse identity is immutable'); END"""
    )
    for table in _TABLES:
        connection.execute(
            f"""CREATE TRIGGER {table}_no_update BEFORE UPDATE ON {table}
                BEGIN SELECT RAISE(ABORT, 'Phase110 provenance is immutable'); END"""
        )
        connection.execute(
            f"""CREATE TRIGGER {table}_no_delete BEFORE DELETE ON {table}
                BEGIN SELECT RAISE(ABORT, 'Phase110 provenance is immutable'); END"""
        )


def _owned_schema(connection: sqlite3.Connection) -> tuple[object, ...]:
    objects = tuple(connection.execute(
        """SELECT type, name, tbl_name, sql FROM sqlite_schema
           WHERE name GLOB 'nar_identity_complete_*'
              OR tbl_name IN ('nar_identity_complete_receipts',
                              'nar_identity_complete_entries',
                              'nar_identity_complete_denials')
           ORDER BY type, name"""
    ))
    topology = tuple(
        (
            table,
            tuple(connection.execute(f"PRAGMA table_xinfo('{table}')")),
            tuple(connection.execute(f"PRAGMA foreign_key_list('{table}')")),
            tuple(connection.execute(f"PRAGMA index_list('{table}')")),
        )
        for table in _TABLES
    )
    index_topology = tuple(
        (name, tuple((row[0], row[2], row[3], row[4], row[5])
                     for row in connection.execute(f"PRAGMA index_xinfo('{name}')")))
        for name in _INDEXES
    )
    return objects, topology, index_topology


def phase110_schema_state(connection: sqlite3.Connection) -> str:
    """Classify proven absence, exact V018 topology, or fail-closed corruption."""
    if not isinstance(connection, sqlite3.Connection):
        return PHASE110_SCHEMA_INTEGRITY_FAILURE
    try:
        registry_exists = connection.execute(
            "SELECT 1 FROM sqlite_schema WHERE type='table' AND name='schema_migrations'"
        ).fetchone() is not None
        registered = () if not registry_exists else tuple(connection.execute(
            "SELECT name FROM schema_migrations WHERE version=18"
        ))
        owned = connection.execute(
            "SELECT 1 FROM sqlite_schema WHERE name GLOB 'nar_identity_complete_*' LIMIT 1"
        ).fetchone() is not None
        if not registered and not owned:
            return PHASE110_SCHEMA_NOT_INSTALLED
        if registered != ((NAME,),) or not owned:
            return PHASE110_SCHEMA_INTEGRITY_FAILURE
        prior = dict(connection.execute(
            "SELECT version,name FROM schema_migrations WHERE version BETWEEN 8 AND 17"
        ))
        if prior != _EXPECTED_PRIOR:
            return PHASE110_SCHEMA_INTEGRITY_FAILURE
        reference = sqlite3.connect(":memory:")
        try:
            reference.execute("PRAGMA foreign_keys=ON")
            reference.execute("CREATE TABLE races(id INTEGER PRIMARY KEY, race_date TEXT, organization TEXT, place TEXT, race_no INTEGER)")
            reference.execute("CREATE TABLE horses(id INTEGER PRIMARY KEY, race_id INTEGER, horse_no INTEGER)")
            reference.execute("CREATE UNIQUE INDEX reference_horse_parent ON horses(race_id,id)")
            _create_schema_objects(reference)
            expected = _owned_schema(reference)
        finally:
            reference.close()
        return (PHASE110_SCHEMA_ACTIVE if _owned_schema(connection) == expected
                else PHASE110_SCHEMA_INTEGRITY_FAILURE)
    except sqlite3.OperationalError as exc:
        # A missing registry column or table is a schema contradiction. Locking and
        # other operational failures are not evidence about schema topology.
        if str(exc).lower().startswith(("no such table:", "no such column:",
                                        "malformed database schema")):
            return PHASE110_SCHEMA_INTEGRITY_FAILURE
        raise


def require_phase110_schema(connection: sqlite3.Connection) -> None:
    if phase110_schema_state(connection) != PHASE110_SCHEMA_ACTIVE:
        raise RuntimeError("exact active V018 Phase110 schema required")


def _preflight_duplicates(connection: sqlite3.Connection) -> None:
    for table, columns, condition in (
        ("races", "race_date, organization, place, race_no",
         "race_date IS NOT NULL AND organization IS NOT NULL AND place IS NOT NULL AND race_no IS NOT NULL"),
        ("horses", "race_id, horse_no", "race_id IS NOT NULL AND horse_no IS NOT NULL"),
    ):
        if connection.execute(
            f"SELECT 1 FROM {table} WHERE {condition} GROUP BY {columns} HAVING count(*)>1 LIMIT 1"
        ).fetchone() is not None:
            raise RuntimeError(f"V018 duplicate natural key in {table}")


def apply(connection: sqlite3.Connection) -> None:
    if type(connection) is not sqlite3.Connection or not connection.in_transaction:
        raise RuntimeError("V018 requires runner-owned write transaction")
    if connection.execute("PRAGMA foreign_keys").fetchone() != (1,):
        raise RuntimeError("V018 requires foreign keys")
    if dict(connection.execute("SELECT version,name FROM schema_migrations")) != _EXPECTED_PRIOR:
        raise RuntimeError("V018 requires exact registered V017 schema")
    require_v017_schema_contract(connection)
    if phase110_schema_state(connection) != PHASE110_SCHEMA_NOT_INSTALLED:
        raise RuntimeError("V018 objects already exist or are inconsistent")
    _preflight_duplicates(connection)
    _create_schema_objects(connection)
