"""Temporary SQLite integration for Phase110 atomic identity provenance."""

import sqlite3
from datetime import timedelta

import pytest

from scripts.migrations.runner import apply_migrations
from scripts.simulation.repositories.sqlite_nar_identity_complete_entry_repository import (
    NARIdentityPersistenceError, SQLiteNARIdentityCompleteEntryRepository,
)
from test_nar_identity_complete_entry_source import BODY, close_env, qualified_env
from test_nar_trusted_deba_acquisition import T0


def repository_env(body=BODY, *, parent=True):
    env, result = qualified_env(body)
    connection = sqlite3.connect(":memory:")
    connection.execute("""CREATE TABLE races(id INTEGER PRIMARY KEY AUTOINCREMENT,
                         race_date TEXT,organization TEXT,place TEXT,race_no INTEGER,
                         deba_table_url TEXT)""")
    connection.execute("""CREATE TABLE horses(id INTEGER PRIMARY KEY AUTOINCREMENT,
                         race_id INTEGER,frame_no INTEGER,horse_no INTEGER,horse_name TEXT,
                         horse_detail_url TEXT,jockey TEXT,trainer TEXT,odds REAL,
                         popularity INTEGER,weight REAL)""")
    connection.commit()
    apply_migrations(connection)
    if parent:
        connection.execute("""INSERT INTO races
            (id,race_date,organization,place,race_no,deba_table_url)
            VALUES(1,'2025-01-01','NAR','Kawasaki',1,?)""", (result.canonical_deba_url,))
        connection.commit()
    repo = SQLiteNARIdentityCompleteEntryRepository(connection=connection)
    return env, result, connection, repo


def close_all(env, connection):
    connection.close()
    close_env(env)


def persist(repo, env, result):
    return repo.persist(qualified_result=result, lineage_archive=env.lineage,
                        capture_archive=env.captures, place="Kawasaki",
                        issued_at=T0 + timedelta(minutes=1))


def test_missing_ids_and_origin_denial_are_one_complete_transaction():
    env, result, connection, repo = repository_env()
    try:
        receipt = persist(repo, env, result)
        assert receipt.race_id == 1
        assert [entry.horse_no for entry in receipt.entries] == [1, 2, 3]
        assert [entry.horse_id for entry in receipt.entries] == [1, 2, 3]
        assert all(entry.issuance_disposition == "ISSUED_IDENTITY_ONLY_INTERNAL_ID"
                   for entry in receipt.entries)
        assert receipt == repo.load_receipt(receipt_id=receipt.receipt_id)
        assert connection.execute("SELECT count(*) FROM nar_identity_complete_denials").fetchone() == (3,)
        assert connection.execute("SELECT count(*) FROM horses").fetchone() == (3,)
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert env.transport.urls == [result.canonical_deba_url]
    finally:
        close_all(env, connection)


def test_absent_parent_fails_without_internal_id_issuance():
    env, result, connection, repo = repository_env(parent=False)
    try:
        with pytest.raises(NARIdentityPersistenceError, match="parent"):
            persist(repo, env, result)
        assert connection.execute("SELECT count(*) FROM horses").fetchone() == (0,)
        assert connection.execute("SELECT count(*) FROM nar_identity_complete_receipts").fetchone() == (0,)
    finally:
        close_all(env, connection)


def test_same_canonical_deba_url_under_different_place_is_ambiguous():
    env, result, connection, repo = repository_env()
    try:
        connection.execute("""INSERT INTO races
            (id,race_date,organization,place,race_no,deba_table_url)
            VALUES(2,'2025-01-01','NAR','Other place',1,?)""",
            (result.canonical_deba_url,))
        connection.commit()
        with pytest.raises(NARIdentityPersistenceError, match="ambiguous NAR parent"):
            persist(repo, env, result)
        for table in ("horses", "nar_identity_complete_receipts",
                      "nar_identity_complete_entries", "nar_identity_complete_denials"):
            assert connection.execute(f"SELECT count(*) FROM {table}").fetchone() == (0,)
        assert not connection.in_transaction
    finally:
        close_all(env, connection)


@pytest.mark.parametrize("value", [None, "", "https://example.invalid/deba",
    "https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/DebaTable?k_babaCode=21&k_raceDate=2025%2F01%2F01&k_raceNo=2"])
def test_parent_url_must_equal_exact_phase111_ancestry(value):
    env, result, connection, repo = repository_env()
    try:
        connection.execute("UPDATE races SET deba_table_url=? WHERE id=1", (value,))
        connection.commit()
        with pytest.raises(NARIdentityPersistenceError):
            persist(repo, env, result)
        assert connection.execute("SELECT count(*) FROM horses").fetchone() == (0,)
    finally:
        close_all(env, connection)


def test_existing_entry_requires_exact_provider_horse_identity():
    env, result, connection, repo = repository_env()
    try:
        connection.execute("""INSERT INTO horses(id,race_id,horse_no,horse_detail_url)
            VALUES(11,1,1,'/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=100')""")
        connection.commit()
        receipt = persist(repo, env, result)
        assert receipt.entries[0].horse_id == 11
        assert receipt.entries[0].issuance_disposition == "ADOPTED_EXISTING_INTERNAL_ID"
        assert connection.execute("SELECT horse_id FROM nar_identity_complete_denials WHERE horse_id=11").fetchone() is None
        assert connection.execute("SELECT count(*) FROM nar_identity_complete_denials").fetchone() == (2,)
    finally:
        close_all(env, connection)


@pytest.mark.parametrize("stored", [None, "", "/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=999"])
def test_existing_entry_without_exact_horse_identity_is_not_adopted(stored):
    env, result, connection, repo = repository_env()
    try:
        connection.execute("INSERT INTO horses(id,race_id,horse_no,horse_detail_url) VALUES(11,1,1,?)", (stored,))
        connection.commit()
        with pytest.raises(NARIdentityPersistenceError):
            persist(repo, env, result)
        assert connection.execute("SELECT count(*) FROM nar_identity_complete_receipts").fetchone() == (0,)
        assert connection.execute("SELECT count(*) FROM horses").fetchone() == (1,)
    finally:
        close_all(env, connection)


def test_extra_legacy_entry_blocks_complete_population_receipt():
    env, result, connection, repo = repository_env()
    try:
        connection.execute("INSERT INTO horses(id,race_id,horse_no) VALUES(20,1,20)")
        connection.commit()
        with pytest.raises(NARIdentityPersistenceError, match="extra"):
            persist(repo, env, result)
        assert connection.execute("SELECT count(*) FROM nar_identity_complete_receipts").fetchone() == (0,)
    finally:
        close_all(env, connection)


def test_failure_after_id_allocation_rolls_back_horses_and_authority():
    env, result, connection, repo = repository_env()
    try:
        connection.execute("""INSERT INTO horses(id,race_id,horse_no,horse_detail_url)
            VALUES(11,1,1,'/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=100')""")
        connection.commit()
        attempted_inserts = []

        def deny_entry_insert(action, table, _column, _database, _source):
            if action == sqlite3.SQLITE_INSERT:
                attempted_inserts.append(table)
                if table == "nar_identity_complete_entries":
                    return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK

        connection.set_authorizer(deny_entry_insert)
        try:
            with pytest.raises(sqlite3.DatabaseError, match="not authorized"):
                persist(repo, env, result)
        finally:
            connection.set_authorizer(None)
        assert "horses" in attempted_inserts
        assert "nar_identity_complete_receipts" in attempted_inserts
        assert attempted_inserts.index("horses") < attempted_inserts.index("nar_identity_complete_receipts")
        assert "nar_identity_complete_entries" in attempted_inserts
        assert connection.execute("SELECT id,horse_no FROM horses").fetchall() == [(11, 1)]
        for table in ("nar_identity_complete_receipts", "nar_identity_complete_entries",
                      "nar_identity_complete_denials"):
            assert connection.execute(f"SELECT count(*) FROM {table}").fetchone() == (0,)
        assert not connection.in_transaction
    finally:
        close_all(env, connection)


def test_receipt_is_content_addressed_and_republication_cannot_reissue():
    env, result, connection, repo = repository_env()
    try:
        receipt = persist(repo, env, result)
        assert len(receipt.receipt_id) == 64 and len(receipt.population_sha256) == 64
        with pytest.raises(NARIdentityPersistenceError):
            persist(repo, env, result)
        assert connection.execute("SELECT count(*) FROM horses").fetchone() == (3,)
    finally:
        close_all(env, connection)


def test_phase110_bound_horse_identity_cannot_be_mutated_or_deleted():
    env, result, connection, repo = repository_env()
    try:
        receipt = persist(repo, env, result)
        horse_id = receipt.entries[0].horse_id
        for sql in (
            "UPDATE horses SET horse_no=8 WHERE id=?",
            "UPDATE horses SET race_id=8 WHERE id=?",
            "DELETE FROM horses WHERE id=?",
        ):
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(sql, (horse_id,))
        connection.rollback()
        assert repo.load_receipt(receipt_id=receipt.receipt_id) == receipt
    finally:
        close_all(env, connection)
