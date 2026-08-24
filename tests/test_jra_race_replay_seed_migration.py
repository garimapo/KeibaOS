from __future__ import annotations

from datetime import datetime, timezone
import sqlite3

import pytest

from scripts.migrations.runner import MIGRATIONS, apply_migrations, get_applied_versions
from scripts.migrations.versions import v015_jra_race_replay_seed_schema as migration
from scripts.simulation.jra_race_replay_seed import JRARaceReplaySeedEntry, build_jra_race_replay_seed


RACE = "jra:race:2025:05:01:01:01"
URL = "https://www.jra.go.jp/JRADB/accessD.html?CNAME=pw01dde0105202501010120250105%2FAB"
UTC = timezone.utc


def _connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE races(id INTEGER PRIMARY KEY)")
    connection.execute("CREATE TABLE horses(id INTEGER PRIMARY KEY, race_id INTEGER)")
    return connection


def _v014() -> sqlite3.Connection:
    connection = _connection()
    apply_migrations(connection, migrations=MIGRATIONS[:-1])
    return connection


def _columns(connection: sqlite3.Connection, table: str) -> tuple[str, ...]:
    return tuple(row[1] for row in connection.execute(f"PRAGMA table_info({table})"))


def test_v015_identity_registration_and_exact_scope() -> None:
    connection = _v014()
    before_tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    source_columns = _columns(connection, "historical_input_source_identities")
    race_columns = _columns(connection, "historical_input_external_races")
    entry_columns = _columns(connection, "historical_input_external_entries")
    apply_migrations(connection)
    after_tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert migration.VERSION == 15
    assert migration.NAME == "v015_jra_race_replay_seed_schema"
    assert tuple(item.VERSION for item in MIGRATIONS).count(15) == 1
    assert MIGRATIONS[-1] is migration
    assert after_tables - before_tables == {"jra_race_replay_seeds", "jra_race_replay_seed_entries"}
    assert _columns(connection, "historical_input_source_identities") == source_columns
    assert _columns(connection, "historical_input_external_races") == race_columns
    assert _columns(connection, "historical_input_external_entries") == entry_columns
    new_indexes = {
        row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE '%exact_mapping%'"
        )
    }
    assert new_indexes == {"ux_historical_input_external_entries_exact_mapping"}
    assert connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='index' AND name LIKE '%external_races%exact%'"
    ).fetchone() is None
    apply_migrations(connection)
    assert get_applied_versions(connection)[15] == migration.NAME


def test_v015_foreign_keys_natural_identity_and_fixed_family_checks() -> None:
    connection = _connection()
    apply_migrations(connection)
    header_sql = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='jra_race_replay_seeds'"
    ).fetchone()[0]
    child_sql = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='jra_race_replay_seed_entries'"
    ).fetchone()[0]
    assert "UNIQUE (\n                schema_version, dataset_id, external_race_id, target_race_selection_capture_id" in header_sql
    assert "organization = 'JRA'" in header_sql and "source_system = 'jra_official'" in header_sql
    assert "organization = 'JRA'" in child_sql and "source_system = 'jra_official'" in child_sql
    header_fks = connection.execute("PRAGMA foreign_key_list(jra_race_replay_seeds)").fetchall()
    child_fks = connection.execute("PRAGMA foreign_key_list(jra_race_replay_seed_entries)").fetchall()
    assert {row[2] for row in header_fks} == {"historical_input_external_races", "races"}
    assert {row[2] for row in child_fks} == {
        "jra_race_replay_seeds", "historical_input_external_entries", "horses"
    }
    assert len([row for row in child_fks if row[2] == "historical_input_external_entries"]) == 6
    assert len([row for row in child_fks if row[2] == "horses"]) == 2


def _valid_state(connection: sqlite3.Connection):
    seed = build_jra_race_replay_seed(
        dataset_id="dataset-1", external_race_id=RACE, internal_race_id=1,
        target_race_selection_capture_id="jra-capture-v4:" + "a" * 64,
        target_race_card_capture_id="jra-capture-v3:" + "b" * 64,
        target_race_card_response_sha256="c" * 64,
        canonical_target_race_card_url=URL,
        captured_at=datetime(2025, 1, 5, 1, tzinfo=UTC),
        information_cutoff=datetime(2025, 1, 5, 2, tzinfo=UTC),
        entries=(JRARaceReplaySeedEntry(0, RACE + ":entry:1", "jra:horse:1234567890", 1, 11),),
    )
    connection.execute("INSERT INTO races(id) VALUES(1)")
    connection.execute("INSERT INTO horses(id,race_id) VALUES(11,1)")
    connection.execute("INSERT INTO historical_input_source_identities VALUES('JRA','jra_official')")
    connection.execute("INSERT INTO historical_input_external_races VALUES('JRA','jra_official',?,1)", (RACE,))
    connection.execute("INSERT INTO historical_input_external_entries VALUES('JRA','jra_official',?,?,1,11)", (RACE, RACE + ":entry:1"))
    return seed


def _insert_header(connection: sqlite3.Connection, seed, **changes: object) -> None:
    values = {
        "seed_id": seed.seed_id, "schema_version": 1, "content_sha256": seed.content_sha256,
        "dataset_id": seed.dataset_id, "organization": "JRA", "source_system": "jra_official",
        "external_race_id": seed.external_race_id, "internal_race_id": seed.internal_race_id,
        "v4": seed.target_race_selection_capture_id, "v3": seed.target_race_card_capture_id,
        "sha": seed.target_race_card_response_sha256, "url": seed.canonical_target_race_card_url,
        "captured": "2025-01-05T01:00:00.000000+00:00", "cutoff": "2025-01-05T02:00:00.000000+00:00",
    }
    values.update(changes)
    connection.execute(
        "INSERT INTO jra_race_replay_seeds VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        tuple(values[key] for key in ("seed_id","schema_version","content_sha256","dataset_id","organization","source_system","external_race_id","internal_race_id","v4","v3","sha","url","captured","cutoff")),
    )


def test_v015_accepts_valid_exact_mapping_and_rejects_bad_children() -> None:
    connection = _connection()
    apply_migrations(connection)
    seed = _valid_state(connection)
    _insert_header(connection, seed)
    connection.execute(
        "INSERT INTO jra_race_replay_seed_entries VALUES(?,?,?,?,?,?,?,?,?,?)",
        (seed.seed_id, "JRA", "jra_official", RACE, 1, 0, RACE + ":entry:1", "jra:horse:1234567890", 1, 11),
    )
    assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO jra_race_replay_seed_entries VALUES(?,?,?,?,?,?,?,?,?,?)",
            (seed.seed_id, "JRA", "jra_official", RACE, 1, 1, RACE + ":entry:2", "jra:horse:1234567891", 2, 99),
        )


@pytest.mark.parametrize("changes", [
    {"seed_id": "bad"},
    {"v4": "jra-capture-v4:" + "A" * 64},
    {"v3": "jra-capture-v2:" + "b" * 64},
    {"sha": "x" * 64},
    {"captured": "2025-01-05T01:00:00+00:00"},
    {"captured": "2025-01-05T03:00:00.000000+00:00"},
    {"internal_race_id": 99},
])
def test_v015_rejects_malformed_header_or_foreign_mapping(changes: dict[str, object]) -> None:
    connection = _connection()
    apply_migrations(connection)
    seed = _valid_state(connection)
    with pytest.raises(sqlite3.IntegrityError):
        _insert_header(connection, seed, **changes)


def test_registered_v014_without_request_identity_column_fails_before_mutation() -> None:
    connection = _connection()
    apply_migrations(connection, migrations=MIGRATIONS[:-2])
    connection.execute(
        "INSERT INTO schema_migrations VALUES(14,'v014_historical_input_request_identity_schema','2025-01-01T00:00:00+00:00')"
    )
    connection.commit()
    with pytest.raises(RuntimeError, match="v014 provenance evidence"):
        apply_migrations(connection)
    assert get_applied_versions(connection).get(15) is None
    assert connection.execute("SELECT 1 FROM sqlite_master WHERE name='jra_race_replay_seeds'").fetchone() is None


def test_malformed_mapping_key_or_fk_prerequisite_fails_before_mutation() -> None:
    connection = _v014()
    connection.execute("PRAGMA foreign_keys=OFF")
    connection.execute("ALTER TABLE historical_input_source_identities RENAME TO bad_source_identities")
    connection.execute("CREATE TABLE historical_input_source_identities(organization TEXT, source_system TEXT)")
    connection.commit()
    connection.execute("PRAGMA foreign_keys=ON")
    with pytest.raises(RuntimeError):
        apply_migrations(connection)
    assert get_applied_versions(connection).get(15) is None
    assert connection.execute("SELECT 1 FROM sqlite_master WHERE name='jra_race_replay_seeds'").fetchone() is None


def test_preexisting_partial_v015_object_is_not_adopted() -> None:
    connection = _v014()
    connection.execute("CREATE TABLE jra_race_replay_seeds(fake TEXT)")
    connection.commit()
    with pytest.raises(RuntimeError, match="already exist"):
        apply_migrations(connection)
    assert get_applied_versions(connection).get(15) is None
    assert _columns(connection, "jra_race_replay_seeds") == ("fake",)
    assert connection.execute("SELECT 1 FROM sqlite_master WHERE name='jra_race_replay_seed_entries'").fetchone() is None
