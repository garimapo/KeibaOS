"""DB-backed candidate and race-entry gates; no provider or production DB."""

import sqlite3
from datetime import timedelta

import pytest

from scripts import database
from scripts.cli.run_prediction import DatabaseRaceInputProvider
from scripts.migrations.runner import apply_migrations
from scripts.models import Horse, Race
from scripts.simulation.repositories.sqlite_nar_identity_complete_entry_repository import (
    SQLiteNARIdentityCompleteEntryRepository,
)
from scripts.simulation.repositories.sqlite_race_entry_source import SQLiteRaceEntrySource
from scripts.simulation.repositories.errors import RepositoryDataIntegrityError
from test_nar_identity_complete_entry_source import close_env, qualified_env
from test_nar_trusted_deba_acquisition import T0


def test_issued_identity_remains_denied_for_rows_and_effective_count(tmp_path, monkeypatch):
    path = tmp_path / "phase110-prediction.sqlite"
    monkeypatch.setattr(database, "DB_PATH", str(path))
    env, result = qualified_env()
    try:
        database.create_tables()
        race = Race("2025-01-01", "NAR", "Kawasaki", 1, "Test", "12:00", 1200,
                    "dirt", "clear", "good", 3, result.canonical_deba_url)
        assert database.save_race(race) == 1
        for number, lineage in ((1, "100"), (2, "200")):
            horse = Horse(1, 1, number, f"Horse {number}",
                          f"/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode={lineage}",
                          "Jockey", "Trainer", 2.0, number, 480.0)
            assert database.save_horse(horse)
        connection = sqlite3.connect(path)
        apply_migrations(connection)
        repo = SQLiteNARIdentityCompleteEntryRepository(connection=connection)
        receipt = repo.persist(qualified_result=result, lineage_archive=env.lineage,
                               capture_archive=env.captures, place="Kawasaki",
                               issued_at=T0 + timedelta(minutes=1))
        issued_id = receipt.entries[2].horse_id
        assert database.get_phase110_schema_state() == "PHASE110_SCHEMA_ACTIVE"
        assert [horse.horse_no for horse in database.get_horses_by_race(1)] == [1, 2]
        race_input = DatabaseRaceInputProvider().load(1)
        assert race_input.race_horse_count == 2  # nominal races.horse_count is 3
        assert set(race_input.horse_past_races) == {receipt.entries[0].horse_id,
                                                    receipt.entries[1].horse_id}
        selected = SQLiteRaceEntrySource(connection=connection).load_race_entry_id_map(
            race_id=1, horse_ids=[entry.horse_id for entry in receipt.entries])
        assert selected == {receipt.entries[0].horse_id: receipt.entries[0].horse_id,
                            receipt.entries[1].horse_id: receipt.entries[1].horse_id}
        assert issued_id not in selected
        connection.close()
    finally:
        close_env(env)


def test_race_entry_source_proven_absence_compatible_and_partial_fails_closed():
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE horses(id INTEGER PRIMARY KEY,race_id INTEGER,horse_no INTEGER)")
    connection.execute("INSERT INTO horses VALUES(1,1,1)")
    connection.commit()
    source = SQLiteRaceEntrySource(connection=connection)
    assert source.load_race_entry_id_map(race_id=1, horse_ids=[1]) == {1: 1}
    connection.execute("CREATE TABLE nar_identity_complete_denials(x INTEGER)")
    connection.commit()
    with pytest.raises(RepositoryDataIntegrityError, match="schema integrity"):
        source.load_race_entry_id_map(race_id=1, horse_ids=[1])
    connection.close()
