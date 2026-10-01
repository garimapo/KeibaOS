"""Legacy writers and Phase110 denial, using only temporary SQLite files."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import sqlite3
from threading import Barrier

import pytest

from scripts import database
from scripts.migrations.runner import apply_migrations
from scripts.models import Horse, Race
from scripts.simulation.nar_trusted_deba_acquisition import canonical_deba_url
from scripts.simulation.repositories.sqlite_nar_identity_complete_entry_repository import (
    NARIdentityPersistenceError, SQLiteNARIdentityCompleteEntryRepository,
)
from scripts.simulation.repositories.sqlite_race_entry_source import SQLiteRaceEntrySource
from test_nar_identity_complete_entry_source import close_env, qualified_env
from test_nar_trusted_deba_acquisition import T0


def race(url=""):
    return Race("2025-01-01", "NAR", "Kawasaki", 1, "Test", "12:00", 1200,
                "dirt", "clear", "good", 3, url)


def horse(number=1, url=""):
    return Horse(1, 1, number, f"Horse {number}", url, "Jockey", "Trainer", 2.0, 1, 480.0)


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    path = tmp_path / "phase110-test.sqlite"
    monkeypatch.setattr(database, "DB_PATH", str(path))
    database.create_tables()
    return path


def migrate(path):
    connection = sqlite3.connect(path)
    apply_migrations(connection)
    connection.close()


def test_v018_absence_preserves_legacy_reader_and_partial_fails_closed(db_path):
    assert database.save_race(race()) == 1
    assert database.save_horse(horse())
    assert len(database.get_horses_by_race(1)) == 1
    assert database.get_phase110_schema_state() == "PHASE110_SCHEMA_NOT_INSTALLED"
    connection = sqlite3.connect(db_path)
    connection.execute("CREATE TABLE nar_identity_complete_denials(x INTEGER)")
    connection.commit()
    connection.close()
    with pytest.raises(RuntimeError, match="schema integrity"):
        database.get_horses_by_race(1)


def test_phase110_denial_survives_legacy_enrichment(db_path):
    env, result = qualified_env()
    try:
        assert database.save_race(race(result.canonical_deba_url)) == 1
        assert database.save_horse(horse(1, "/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=100"))
        migrate(db_path)
        connection = sqlite3.connect(db_path)
        repo = SQLiteNARIdentityCompleteEntryRepository(connection=connection)
        receipt = repo.persist(qualified_result=result, lineage_archive=env.lineage,
                               capture_archive=env.captures, place="Kawasaki",
                               issued_at=T0 + timedelta(minutes=1))
        issued = receipt.entries[1].horse_id
        assert [item.horse_no for item in database.get_horses_by_race(1)] == [1]
        assert database.save_horse(horse(2, "/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=200"))
        assert connection.execute("SELECT id FROM horses WHERE race_id=1 AND horse_no=2").fetchone() == (issued,)
        assert connection.execute("SELECT horse_id FROM nar_identity_complete_denials WHERE horse_id=?", (issued,)).fetchone() == (issued,)
        assert [item.horse_no for item in database.get_horses_by_race(1)] == [1]
        with pytest.raises(ValueError):
            database.save_horse(horse(2, "/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=999"))
        assert repo.load_receipt(receipt_id=receipt.receipt_id) == receipt
        connection.close()
    finally:
        close_env(env)


def test_bound_horse_id_cannot_change_with_foreign_keys_off(db_path):
    env, result = qualified_env()
    try:
        assert database.save_race(race(result.canonical_deba_url)) == 1
        migrate(db_path)
        connection = sqlite3.connect(db_path)
        try:
            repo = SQLiteNARIdentityCompleteEntryRepository(connection=connection)
            receipt = repo.persist(qualified_result=result, lineage_archive=env.lineage,
                                   capture_archive=env.captures, place="Kawasaki",
                                   issued_at=T0 + timedelta(minutes=1))
            issued_id = receipt.entries[0].horse_id
            mutation = sqlite3.connect(db_path)
            try:
                assert mutation.execute("PRAGMA foreign_keys").fetchone() == (0,)
                with pytest.raises(sqlite3.IntegrityError, match="Phase110 horse identity is immutable"):
                    mutation.execute("UPDATE horses SET id=? WHERE id=?", (issued_id + 100, issued_id))
                mutation.rollback()
                assert mutation.execute("PRAGMA foreign_keys").fetchone() == (0,)
            finally:
                mutation.close()
            assert connection.execute("SELECT id FROM horses WHERE horse_no=1").fetchone() == (issued_id,)
            assert connection.execute(
                "SELECT horse_id FROM nar_identity_complete_denials WHERE horse_id=?",
                (issued_id,)).fetchone() == (issued_id,)
            assert database.get_horses_by_race(1) == []
            assert SQLiteRaceEntrySource(connection=connection).load_race_entry_id_map(
                race_id=1, horse_ids=[issued_id]) == {}
        finally:
            connection.close()
    finally:
        close_env(env)


def test_generic_race_writer_one_connection_serializes_natural_key(db_path):
    migrate(db_path)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: database.save_race(race()), range(2)))
    assert sorted(value is None for value in results) == [False, True]
    connection = sqlite3.connect(db_path)
    assert connection.execute("SELECT count(*) FROM races").fetchone() == (1,)
    connection.close()


def test_generic_horse_writer_one_connection_serializes_natural_key(db_path):
    assert database.save_race(race()) == 1
    migrate(db_path)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: database.save_horse(horse()), range(2)))
    assert sorted(results) == [False, True]
    connection = sqlite3.connect(db_path)
    assert connection.execute("SELECT count(*) FROM horses WHERE race_id=1 AND horse_no=1").fetchone() == (1,)
    connection.close()


def test_phase110_issuance_racing_legacy_writer_preserves_one_internal_id(db_path):
    canonical = canonical_deba_url("nar:20250101:21:1")
    assert database.save_race(race(canonical)) == 1
    migrate(db_path)
    barrier = Barrier(2)

    def phase110_writer():
        env, result = qualified_env()
        connection = sqlite3.connect(db_path, timeout=10)
        try:
            repo = SQLiteNARIdentityCompleteEntryRepository(connection=connection)
            barrier.wait()
            return repo.persist(qualified_result=result, lineage_archive=env.lineage,
                                capture_archive=env.captures, place="Kawasaki",
                                issued_at=T0 + timedelta(minutes=1))
        finally:
            connection.close()
            close_env(env)

    def legacy_writer():
        barrier.wait()
        return database.save_horse(horse(
            1, "/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=100"))

    with ThreadPoolExecutor(max_workers=2) as pool:
        future_phase110 = pool.submit(phase110_writer)
        future_legacy = pool.submit(legacy_writer)
        receipt = future_phase110.result(timeout=15)
        assert future_legacy.result(timeout=15)
    connection = sqlite3.connect(db_path)
    assert connection.execute("SELECT count(*) FROM horses WHERE race_id=1 AND horse_no=1").fetchone() == (1,)
    assert receipt.entries[0].horse_id == connection.execute(
        "SELECT id FROM horses WHERE race_id=1 AND horse_no=1").fetchone()[0]
    assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    connection.close()


def test_two_phase110_issuers_publish_only_one_complete_authority(db_path):
    canonical = canonical_deba_url("nar:20250101:21:1")
    assert database.save_race(race(canonical)) == 1
    migrate(db_path)
    barrier = Barrier(2)

    def phase110_writer():
        env, result = qualified_env()
        connection = sqlite3.connect(db_path, timeout=10)
        try:
            repo = SQLiteNARIdentityCompleteEntryRepository(connection=connection)
            barrier.wait()
            try:
                return ("success", repo.persist(
                    qualified_result=result, lineage_archive=env.lineage,
                    capture_archive=env.captures, place="Kawasaki",
                    issued_at=T0 + timedelta(minutes=1)))
            except NARIdentityPersistenceError as error:
                return ("rejected", str(error))
        finally:
            connection.close()
            close_env(env)

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(phase110_writer) for _ in range(2)]
        outcomes = [future.result(timeout=20) for future in futures]
    assert sorted(outcome[0] for outcome in outcomes) == ["rejected", "success"]
    receipt = next(value for kind, value in outcomes if kind == "success")
    connection = sqlite3.connect(db_path)
    try:
        assert connection.execute("SELECT count(*) FROM nar_identity_complete_receipts").fetchone() == (1,)
        assert connection.execute("SELECT count(*) FROM nar_identity_complete_entries").fetchone() == (3,)
        assert connection.execute("SELECT count(*) FROM nar_identity_complete_denials").fetchone() == (3,)
        assert connection.execute("SELECT count(*) FROM horses").fetchone() == (3,)
        assert connection.execute(
            "SELECT race_id,horse_no,count(*) FROM horses GROUP BY race_id,horse_no"
        ).fetchall() == [(1, 1, 1), (1, 2, 1), (1, 3, 1)]
        assert {row[0] for row in connection.execute(
            "SELECT receipt_id FROM nar_identity_complete_denials")} == {receipt.receipt_id}
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        connection.close()
