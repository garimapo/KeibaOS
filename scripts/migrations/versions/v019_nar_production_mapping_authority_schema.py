"""V019: immutable NAR production mapping authority, separate from V010 rows."""

from __future__ import annotations

import sqlite3

from .v010_historical_input_snapshot_schema import apply as create_v010
from .v018_nar_identity_complete_entry_schema import (
    _create_schema_objects as create_v018,
    require_phase110_schema,
)

VERSION = 19
NAME = "v019_nar_production_mapping_authority_schema"

PHASE109_SCHEMA_NOT_INSTALLED = "PHASE109_SCHEMA_NOT_INSTALLED"
PHASE109_SCHEMA_ACTIVE = "PHASE109_SCHEMA_ACTIVE"
PHASE109_SCHEMA_INTEGRITY_FAILURE = "PHASE109_SCHEMA_INTEGRITY_FAILURE"

_PRIOR = {
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
    18: "v018_nar_identity_complete_entry_schema",
}

_TABLES = ("nar_production_mapping_receipts", "nar_production_mapping_entries")
_V010_MAPPING_TABLES = (
    "historical_input_source_identities",
    "historical_input_external_races",
    "historical_input_external_entries",
)


def _create_schema_objects(connection: sqlite3.Connection) -> None:
    connection.execute("""CREATE TABLE nar_production_mapping_receipts (
        receipt_id TEXT PRIMARY KEY NOT NULL,
        phase110_receipt_id TEXT NOT NULL UNIQUE,
        organization TEXT NOT NULL CHECK(organization='NAR'),
        source_system TEXT NOT NULL CHECK(source_system='nar_official'),
        external_race_id TEXT NOT NULL UNIQUE,
        internal_race_id INTEGER NOT NULL UNIQUE
            CHECK(typeof(internal_race_id)='integer' AND internal_race_id>0),
        phase110_population_sha256 TEXT NOT NULL CHECK(length(phase110_population_sha256)=64),
        phase110_population_count INTEGER NOT NULL CHECK(phase110_population_count>0),
        phase110_issued_at TEXT NOT NULL,
        phase111_declaration_id TEXT NOT NULL,
        phase111_receipt_id TEXT NOT NULL,
        phase111_capture_id TEXT NOT NULL,
        response_sha256 TEXT NOT NULL CHECK(length(response_sha256)=64),
        observed_at TEXT NOT NULL,
        prediction_cutoff TEXT NOT NULL,
        mapping_population_sha256 TEXT NOT NULL CHECK(length(mapping_population_sha256)=64),
        mapping_population_count INTEGER NOT NULL CHECK(mapping_population_count>0),
        issued_at TEXT NOT NULL,
        receipt_json TEXT NOT NULL,
        UNIQUE(receipt_id,phase110_receipt_id,external_race_id,internal_race_id),
        FOREIGN KEY(phase110_receipt_id,internal_race_id)
            REFERENCES nar_identity_complete_receipts(receipt_id,race_id)
            ON UPDATE RESTRICT ON DELETE RESTRICT,
        FOREIGN KEY(organization,source_system,external_race_id,internal_race_id)
            REFERENCES historical_input_external_races
                (organization,source_system,external_race_id,internal_race_id)
            ON UPDATE RESTRICT ON DELETE RESTRICT
    ) WITHOUT ROWID""")
    connection.execute("""CREATE TABLE nar_production_mapping_entries (
        receipt_id TEXT NOT NULL,
        phase110_receipt_id TEXT NOT NULL,
        organization TEXT NOT NULL CHECK(organization='NAR'),
        source_system TEXT NOT NULL CHECK(source_system='nar_official'),
        external_race_id TEXT NOT NULL,
        external_entry_id TEXT NOT NULL,
        internal_race_id INTEGER NOT NULL,
        race_entry_id INTEGER NOT NULL CHECK(typeof(race_entry_id)='integer' AND race_entry_id>0),
        horse_no INTEGER NOT NULL CHECK(typeof(horse_no)='integer' AND horse_no>0),
        PRIMARY KEY(receipt_id,external_entry_id),
        UNIQUE(receipt_id,race_entry_id),
        UNIQUE(receipt_id,horse_no),
        FOREIGN KEY(receipt_id,phase110_receipt_id,external_race_id,internal_race_id)
            REFERENCES nar_production_mapping_receipts
                (receipt_id,phase110_receipt_id,external_race_id,internal_race_id)
            ON UPDATE RESTRICT ON DELETE RESTRICT,
        FOREIGN KEY(phase110_receipt_id,external_entry_id,internal_race_id,race_entry_id)
            REFERENCES nar_identity_complete_entries
                (receipt_id,external_entry_id,race_id,horse_id)
            ON UPDATE RESTRICT ON DELETE RESTRICT,
        FOREIGN KEY(organization,source_system,external_race_id,external_entry_id)
            REFERENCES historical_input_external_entries
                (organization,source_system,external_race_id,external_entry_id)
            ON UPDATE RESTRICT ON DELETE RESTRICT
    ) WITHOUT ROWID""")
    # The V010 entry external ID is unique only within source/race, so the
    # composite V010 FK below uses its actual primary key instead of one column.
    for table in _TABLES:
        for action in ("UPDATE", "DELETE"):
            connection.execute(
                f"CREATE TRIGGER {table}_no_{action.lower()} BEFORE {action} ON {table} "
                "BEGIN SELECT RAISE(ABORT, 'Phase109 mapping authority is immutable'); END"
            )
    connection.execute("""CREATE TRIGGER nar_production_mapping_v010_race_no_update
        BEFORE UPDATE ON historical_input_external_races
        WHEN EXISTS (SELECT 1 FROM nar_production_mapping_receipts r
            WHERE r.organization=OLD.organization AND r.source_system=OLD.source_system
              AND (r.external_race_id=OLD.external_race_id
                   OR r.internal_race_id=OLD.internal_race_id))
          OR EXISTS (SELECT 1 FROM nar_production_mapping_receipts r
            WHERE r.organization=NEW.organization AND r.source_system=NEW.source_system
              AND (r.external_race_id=NEW.external_race_id
                   OR r.internal_race_id=NEW.internal_race_id))
        BEGIN SELECT RAISE(ABORT, 'Phase109-covered race mapping is immutable'); END""")
    connection.execute("""CREATE TRIGGER nar_production_mapping_v010_race_no_delete
        BEFORE DELETE ON historical_input_external_races
        WHEN EXISTS (SELECT 1 FROM nar_production_mapping_receipts r
            WHERE r.organization=OLD.organization AND r.source_system=OLD.source_system
              AND (r.external_race_id=OLD.external_race_id
                   OR r.internal_race_id=OLD.internal_race_id))
        BEGIN SELECT RAISE(ABORT, 'Phase109-covered race mapping is immutable'); END""")
    connection.execute("""CREATE TRIGGER nar_production_mapping_v010_entry_no_update
        BEFORE UPDATE ON historical_input_external_entries
        WHEN EXISTS (SELECT 1 FROM nar_production_mapping_receipts r
            WHERE r.organization=OLD.organization AND r.source_system=OLD.source_system
              AND (r.external_race_id=OLD.external_race_id
                   OR r.internal_race_id=OLD.internal_race_id))
          OR EXISTS (SELECT 1 FROM nar_production_mapping_receipts r
            WHERE r.organization=NEW.organization AND r.source_system=NEW.source_system
              AND (r.external_race_id=NEW.external_race_id
                   OR r.internal_race_id=NEW.internal_race_id))
        BEGIN SELECT RAISE(ABORT, 'Phase109-covered entry mapping is immutable'); END""")
    connection.execute("""CREATE TRIGGER nar_production_mapping_v010_entry_no_delete
        BEFORE DELETE ON historical_input_external_entries
        WHEN EXISTS (SELECT 1 FROM nar_production_mapping_receipts r
            WHERE r.organization=OLD.organization AND r.source_system=OLD.source_system
              AND (r.external_race_id=OLD.external_race_id
                   OR r.internal_race_id=OLD.internal_race_id))
        BEGIN SELECT RAISE(ABORT, 'Phase109-covered entry mapping is immutable'); END""")
    connection.execute("""CREATE TRIGGER nar_production_mapping_v010_entry_no_extra
        BEFORE INSERT ON historical_input_external_entries
        WHEN EXISTS (SELECT 1 FROM nar_production_mapping_receipts r
            WHERE r.organization=NEW.organization AND r.source_system=NEW.source_system
              AND (r.external_race_id=NEW.external_race_id
                   OR r.internal_race_id=NEW.internal_race_id))
        BEGIN SELECT RAISE(ABORT, 'Phase109-covered entry set is immutable'); END""")


def _owned_schema(connection: sqlite3.Connection) -> tuple[object, ...]:
    objects = tuple(connection.execute("""SELECT type,name,tbl_name,sql FROM sqlite_schema
        WHERE name GLOB 'nar_production_mapping_*'
           OR tbl_name IN ('nar_production_mapping_receipts','nar_production_mapping_entries')
        ORDER BY type,name"""))
    topology = tuple((table,
        tuple(connection.execute(f"PRAGMA table_xinfo('{table}')")),
        tuple(connection.execute(f"PRAGMA foreign_key_list('{table}')")),
        tuple(connection.execute(f"PRAGMA index_list('{table}')"))) for table in _TABLES)
    return objects, topology


def _v010_mapping_schema(connection: sqlite3.Connection) -> tuple[object, ...]:
    return tuple((name,
        connection.execute("SELECT sql FROM sqlite_schema WHERE type='table' AND name=?", (name,)).fetchone(),
        tuple(connection.execute(f"PRAGMA table_xinfo('{name}')")),
        tuple(connection.execute(f"PRAGMA foreign_key_list('{name}')")),
        tuple(connection.execute(f"PRAGMA index_list('{name}')")),
        tuple((index[1], tuple(connection.execute(f"PRAGMA index_xinfo('{index[1]}')")))
              for index in connection.execute(f"PRAGMA index_list('{name}')")))
        for name in _V010_MAPPING_TABLES)


def _expected_topology() -> tuple[tuple[object, ...], tuple[object, ...]]:
    reference = sqlite3.connect(":memory:")
    try:
        reference.execute("PRAGMA foreign_keys=ON")
        reference.execute("CREATE TABLE races(id INTEGER PRIMARY KEY, race_date TEXT, organization TEXT, place TEXT, race_no INTEGER)")
        reference.execute("CREATE TABLE horses(id INTEGER PRIMARY KEY, race_id INTEGER, horse_no INTEGER)")
        create_v010(reference)
        create_v018(reference)
        # V015 adds this exact V010 entry-mapping index in the standard prior
        # migration chain; the reference must include it before comparison.
        reference.execute("""CREATE UNIQUE INDEX ux_historical_input_external_entries_exact_mapping
            ON historical_input_external_entries(
                organization, source_system, external_race_id, external_entry_id,
                internal_race_id, race_entry_id
            )""")
        expected_v010 = _v010_mapping_schema(reference)
        _create_schema_objects(reference)
        return expected_v010, _owned_schema(reference)
    finally:
        reference.close()


def phase109_schema_state(connection: sqlite3.Connection) -> str:
    if not isinstance(connection, sqlite3.Connection):
        return PHASE109_SCHEMA_INTEGRITY_FAILURE
    try:
        registry = connection.execute("""SELECT 1 FROM sqlite_schema
            WHERE type='table' AND name='schema_migrations'""").fetchone() is not None
        registered = () if not registry else tuple(connection.execute(
            "SELECT name FROM schema_migrations WHERE version=19"))
        owned = connection.execute("""SELECT 1 FROM sqlite_schema
            WHERE name GLOB 'nar_production_mapping_*' LIMIT 1""").fetchone() is not None
        if not registered and not owned:
            return PHASE109_SCHEMA_NOT_INSTALLED
        if registered != ((NAME,),) or not owned:
            return PHASE109_SCHEMA_INTEGRITY_FAILURE
        if dict(connection.execute("SELECT version,name FROM schema_migrations WHERE version BETWEEN 8 AND 18")) != _PRIOR:
            return PHASE109_SCHEMA_INTEGRITY_FAILURE
        expected_v010, expected = _expected_topology()
        return (PHASE109_SCHEMA_ACTIVE if (_owned_schema(connection) == expected
                and _v010_mapping_schema(connection) == expected_v010)
                else PHASE109_SCHEMA_INTEGRITY_FAILURE)
    except sqlite3.OperationalError as exc:
        if str(exc).lower().startswith(("no such table:", "no such column:", "malformed database schema")):
            return PHASE109_SCHEMA_INTEGRITY_FAILURE
        raise


def require_phase109_schema(connection: sqlite3.Connection) -> None:
    if phase109_schema_state(connection) != PHASE109_SCHEMA_ACTIVE:
        raise RuntimeError("exact active V019 Phase109 schema required")


def apply(connection: sqlite3.Connection) -> None:
    if type(connection) is not sqlite3.Connection or not connection.in_transaction:
        raise RuntimeError("V019 requires runner-owned write transaction")
    if connection.execute("PRAGMA foreign_keys").fetchone() != (1,):
        raise RuntimeError("V019 requires foreign keys")
    if dict(connection.execute("SELECT version,name FROM schema_migrations")) != _PRIOR:
        raise RuntimeError("V019 requires exact registered V018 schema")
    require_phase110_schema(connection)
    if phase109_schema_state(connection) != PHASE109_SCHEMA_NOT_INSTALLED:
        raise RuntimeError("V019 objects already exist or are inconsistent")
    expected_v010, _ = _expected_topology()
    if _v010_mapping_schema(connection) != expected_v010:
        raise RuntimeError("V019 requires exact V010 mapping topology before installation")
    _create_schema_objects(connection)
