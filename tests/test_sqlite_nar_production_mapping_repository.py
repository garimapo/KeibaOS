"""Offline exact Phase111 -> Phase110 -> V010/V019 authority tests."""

import sqlite3
import threading
from datetime import timedelta

import pytest

from scripts.migrations.versions.v019_nar_production_mapping_authority_schema import (
    PHASE109_SCHEMA_ACTIVE, phase109_schema_state,
)
from scripts.simulation.nar_production_mapping_authority import (
    NARProductionMappingError, receipt_from_phase110,
)
from scripts.simulation.repositories.sqlite_nar_production_mapping_repository import (
    SQLiteNARProductionMappingRepository,
)
from scripts.simulation.repositories.sqlite_nar_identity_complete_entry_repository import (
    SQLiteNARIdentityCompleteEntryRepository,
)
from scripts.simulation.sqlite_nar_trusted_deba_acquisition_archive import (
    SQLiteNARTrustedDebaAcquisitionArchive,
)
from scripts.simulation.repositories.sqlite_nar_official_response_capture_repository import (
    SQLiteNAROfficialResponseCaptureRepository,
)
from test_sqlite_nar_identity_complete_entry_repository import close_all, persist, repository_env


def ready():
    env, result, connection, phase110_repo = repository_env()
    source = persist(phase110_repo, env, result)
    repository = SQLiteNARProductionMappingRepository(connection=connection)
    return env, connection, source, repository


def publish(repo, env, source):
    return repo.publish(phase110_receipt_id=source.receipt_id,
                        lineage_archive=env.lineage, capture_archive=env.captures,
                        expected_external_race_id=source.external_race_id,
                        expected_prediction_cutoff=source.prediction_cutoff)


def counts(connection):
    return tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                 for table in ("historical_input_external_races",
                               "historical_input_external_entries",
                               "nar_production_mapping_receipts",
                               "nar_production_mapping_entries"))


def test_publish_full_denied_population_and_exact_idempotent_reload():
    env, connection, source, repo = ready()
    try:
        receipt = publish(repo, env, source)
        assert receipt.phase110_receipt_id == source.receipt_id
        assert [(e.external_entry_id, e.race_entry_id, e.horse_no) for e in receipt.entries] == [
            (e.external_entry_id, e.horse_id, e.horse_no) for e in source.entries]
        assert repo.load_receipt(receipt_id=receipt.receipt_id) == receipt
        assert publish(repo, env, source) == receipt
        assert counts(connection) == (1, 3, 1, 3)
        assert connection.execute("SELECT count(*) FROM nar_identity_complete_denials").fetchone() == (3,)
        assert connection.execute("SELECT count(*) FROM horses").fetchone() == (3,)
        assert connection.execute("SELECT count(*) FROM races").fetchone() == (1,)
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert env.transport.urls == [source.canonical_deba_url]
    finally:
        close_all(env, connection)


def test_real_but_unrelated_phase111_archive_cannot_supply_ancestry():
    env, connection, source, repo = ready()
    other_env, _, other_connection, _ = repository_env(body=b"<html>different capture</html>")
    try:
        with pytest.raises(NARProductionMappingError, match="Phase111 receipt"):
            repo.publish(phase110_receipt_id=source.receipt_id,
                         lineage_archive=other_env.lineage,
                         capture_archive=other_env.captures,
                         expected_external_race_id=source.external_race_id,
                         expected_prediction_cutoff=source.prediction_cutoff)
        assert counts(connection) == (0, 0, 0, 0)
    finally:
        close_all(other_env, other_connection)
        close_all(env, connection)


def test_corrupt_phase110_schema_blocks_mapping_before_v010_write():
    env, connection, source, repo = ready()
    try:
        connection.execute("DROP TRIGGER nar_identity_complete_entries_no_update")
        connection.commit()
        with pytest.raises(RuntimeError, match="V018"):
            publish(repo, env, source)
        assert counts(connection) == (0, 0, 0, 0)
    finally:
        close_all(env, connection)


def test_missing_phase110_receipt_and_phase111_ancestry_fail_before_v010_write():
    env, connection, source, repo = ready()
    try:
        with pytest.raises(Exception):
            repo.publish(phase110_receipt_id="missing", lineage_archive=env.lineage,
                         capture_archive=env.captures,
                         expected_external_race_id=source.external_race_id,
                         expected_prediction_cutoff=source.prediction_cutoff)
        class MissingLineage:
            def load_receipt(self, **_kwargs):
                return None
        with pytest.raises(NARProductionMappingError, match="exact persisted Phase111 archives"):
            repo.publish(phase110_receipt_id=source.receipt_id,
                         lineage_archive=MissingLineage(), capture_archive=env.captures,
                         expected_external_race_id=source.external_race_id,
                         expected_prediction_cutoff=source.prediction_cutoff)
        class ArchiveSubclass(SQLiteNARTrustedDebaAcquisitionArchive):
            pass
        with pytest.raises(NARProductionMappingError, match="exact persisted Phase111 archives"):
            repo.publish(phase110_receipt_id=source.receipt_id,
                         lineage_archive=ArchiveSubclass(connection=env.connections[2]),
                         capture_archive=env.captures,
                         expected_external_race_id=source.external_race_id,
                         expected_prediction_cutoff=source.prediction_cutoff)
        assert counts(connection) == (0, 0, 0, 0)
    finally:
        close_all(env, connection)


def test_publicly_constructed_receipt_cannot_bypass_controlled_issuance():
    env, connection, source, repo = ready()
    try:
        manually_constructed = receipt_from_phase110(
            source=source, issued_at=source.issued_at + timedelta(seconds=1))
        with pytest.raises(NARProductionMappingError, match="controlled publication"):
            repo._insert_receipt(manually_constructed)
        assert counts(connection) == (0, 0, 0, 0)
        assert not connection.in_transaction
    finally:
        close_all(env, connection)


def test_exact_snapshot_style_v010_rows_are_consistency_only():
    env, connection, source, repo = ready()
    try:
        connection.execute("INSERT INTO historical_input_source_identities VALUES('NAR','nar_official')")
        connection.execute("INSERT INTO historical_input_external_races VALUES('NAR','nar_official',?,?)",
                           (source.external_race_id, source.race_id))
        first = source.entries[0]
        connection.execute("INSERT INTO historical_input_external_entries VALUES('NAR','nar_official',?,?,?,?)",
                           (source.external_race_id, first.external_entry_id, source.race_id, first.horse_id))
        connection.commit()
        assert counts(connection) == (1, 1, 0, 0)  # V010 rows alone have no authority.
        receipt = publish(repo, env, source)
        assert receipt.receipt_id
        assert counts(connection) == (1, 3, 1, 3)
    finally:
        close_all(env, connection)


@pytest.mark.parametrize("kind", ["forward", "reverse", "race_forward", "entry_reverse", "extra"])
def test_v010_conflicts_and_extra_entries_fail_closed(kind):
    env, connection, source, repo = ready()
    try:
        connection.execute("INSERT INTO historical_input_source_identities VALUES('NAR','nar_official')")
        if kind == "reverse":
            connection.execute("INSERT INTO races(id) VALUES(2)")
            connection.execute("INSERT INTO historical_input_external_races VALUES('NAR','nar_official','other',?)",
                               (source.race_id,))
        elif kind == "race_forward":
            connection.execute("INSERT INTO races(id) VALUES(2)")
            connection.execute("INSERT INTO historical_input_external_races VALUES('NAR','nar_official',?,2)",
                               (source.external_race_id,))
        else:
            connection.execute("INSERT INTO historical_input_external_races VALUES('NAR','nar_official',?,?)",
                               (source.external_race_id, source.race_id))
            if kind == "forward":
                connection.execute("INSERT INTO horses(id,race_id,horse_no) VALUES(10,1,10)")
                entry = source.entries[0]
                connection.execute("INSERT INTO historical_input_external_entries VALUES('NAR','nar_official',?,?,?,?)",
                                   (source.external_race_id, entry.external_entry_id, 1, 10))
            elif kind == "entry_reverse":
                entry = source.entries[0]
                connection.execute("INSERT INTO historical_input_external_entries VALUES('NAR','nar_official',?,?,?,?)",
                                   (source.external_race_id, 'other-entry', 1, entry.horse_id))
            else:
                connection.execute("INSERT INTO horses(id,race_id,horse_no) VALUES(10,1,10)")
                connection.execute("INSERT INTO historical_input_external_entries VALUES('NAR','nar_official',?,?,?,?)",
                                   (source.external_race_id, 'extra', 1, 10))
        connection.commit()
        before = counts(connection)
        with pytest.raises(NARProductionMappingError):
            publish(repo, env, source)
        assert counts(connection) == before
        assert not connection.in_transaction
    finally:
        close_all(env, connection)


def test_v010_and_v019_rollback_after_real_v010_and_receipt_writes():
    env, connection, source, repo = ready()
    try:
        assert connection.execute("""SELECT count(*) FROM historical_input_source_identities
            WHERE organization='NAR' AND source_system='nar_official'""").fetchone() == (0,)
        inserted = []
        def deny_entry(action, table, _column, _database, _source):
            if action == sqlite3.SQLITE_INSERT:
                inserted.append(table)
                if table == "nar_production_mapping_entries":
                    return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK
        connection.set_authorizer(deny_entry)
        try:
            with pytest.raises(sqlite3.DatabaseError, match="not authorized"):
                publish(repo, env, source)
        finally:
            connection.set_authorizer(None)
        assert "historical_input_source_identities" in inserted
        assert "historical_input_external_entries" in inserted
        assert "nar_production_mapping_receipts" in inserted
        assert "nar_production_mapping_entries" in inserted
        assert counts(connection) == (0, 0, 0, 0)
        assert connection.execute("""SELECT count(*) FROM historical_input_source_identities
            WHERE organization='NAR' AND source_system='nar_official'""").fetchone() == (0,)
        assert not connection.in_transaction
    finally:
        close_all(env, connection)


def test_v019_and_covered_v010_cannot_mutate_with_foreign_keys_off():
    env, connection, source, repo = ready()
    try:
        receipt = publish(repo, env, source)
        connection.execute("PRAGMA foreign_keys=OFF")
        assert connection.execute("PRAGMA foreign_keys").fetchone() == (0,)
        statements = (
            "UPDATE nar_production_mapping_receipts SET issued_at='x'",
            "DELETE FROM nar_production_mapping_receipts",
            "UPDATE nar_production_mapping_entries SET horse_no=9",
            "DELETE FROM nar_production_mapping_entries",
            "UPDATE historical_input_external_races SET internal_race_id=2",
            "DELETE FROM historical_input_external_races",
            "UPDATE historical_input_external_entries SET race_entry_id=9",
            "DELETE FROM historical_input_external_entries",
        )
        for statement in statements:
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(statement)
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO historical_input_external_entries VALUES('NAR','nar_official',?,?,?,?)",
                               (source.external_race_id, "extra", source.race_id, 999))
        connection.execute("INSERT INTO races(id) VALUES(2)")
        connection.execute("INSERT INTO horses(id,race_id,horse_no) VALUES(20,2,20)")
        connection.execute("INSERT INTO historical_input_external_races VALUES('NAR','nar_official','other',2)")
        connection.execute("INSERT INTO historical_input_external_entries VALUES('NAR','nar_official','other','other-entry',2,20)")
        with pytest.raises(sqlite3.IntegrityError, match="Phase109-covered"):
            connection.execute("""UPDATE historical_input_external_entries
                SET external_race_id=? WHERE external_race_id='other'""",
                (source.external_race_id,))
        assert repo.load_receipt(receipt_id=receipt.receipt_id) == receipt
        assert counts(connection) == (2, 4, 1, 3)
    finally:
        close_all(env, connection)


def test_reverse_side_insert_and_update_are_trigger_blocked_with_foreign_keys_off():
    env, connection, source, repo = ready()
    try:
        receipt = publish(repo, env, source)
        connection.execute("PRAGMA foreign_keys=OFF")
        assert connection.execute("PRAGMA foreign_keys").fetchone() == (0,)
        connection.execute("INSERT INTO races(id) VALUES(2)")
        connection.execute("INSERT INTO horses(id,race_id,horse_no) VALUES(20,2,20)")
        connection.execute("INSERT INTO historical_input_external_races VALUES('NAR','nar_official','other',2)")
        with pytest.raises(sqlite3.IntegrityError, match="Phase109-covered race mapping"):
            connection.execute("""UPDATE historical_input_external_races
                SET internal_race_id=? WHERE external_race_id='other'""",
                (source.race_id,))

        with pytest.raises(sqlite3.IntegrityError, match="Phase109-covered entry set"):
            connection.execute("""INSERT INTO historical_input_external_entries
                VALUES('NAR','nar_official','other','new-reverse-entry',?,999)""",
                (source.race_id,))

        connection.execute("""INSERT INTO historical_input_external_entries
            VALUES('NAR','nar_official','other','other-entry',2,20)""")
        with pytest.raises(sqlite3.IntegrityError, match="Phase109-covered entry mapping"):
            connection.execute("""UPDATE historical_input_external_entries
                SET internal_race_id=? WHERE external_race_id='other'""",
                (source.race_id,))
        assert connection.execute("""SELECT internal_race_id FROM historical_input_external_entries
            WHERE external_race_id='other'""").fetchone() == (2,)
        connection.commit()
        assert repo.load_receipt(receipt_id=receipt.receipt_id) == receipt
    finally:
        close_all(env, connection)


def test_reverse_side_preexisting_extra_rejects_publication_without_authority():
    env, connection, source, repo = ready()
    try:
        connection.execute("PRAGMA foreign_keys=OFF")
        connection.execute("INSERT INTO historical_input_source_identities VALUES('NAR','nar_official')")
        connection.execute("INSERT INTO historical_input_external_races VALUES('NAR','nar_official','other',2)")
        connection.execute("""INSERT INTO historical_input_external_entries
            VALUES('NAR','nar_official','other','reverse-extra',?,999)""",
            (source.race_id,))
        connection.commit()
        connection.execute("PRAGMA foreign_keys=ON")
        before = counts(connection)

        with pytest.raises(NARProductionMappingError, match="forward/reverse target"):
            publish(repo, env, source)

        assert counts(connection) == before == (1, 1, 0, 0)
        assert connection.execute("""SELECT count(*) FROM historical_input_external_races
            WHERE external_race_id=?""", (source.external_race_id,)).fetchone() == (0,)
        assert not connection.in_transaction
    finally:
        close_all(env, connection)


def test_exact_reload_rejects_reverse_side_extra_even_with_valid_v019_topology():
    env, connection, source, repo = ready()
    try:
        receipt = publish(repo, env, source)
        connection.execute("PRAGMA foreign_keys=OFF")
        guard = "nar_production_mapping_v010_entry_no_extra"
        guard_sql = connection.execute("SELECT sql FROM sqlite_schema WHERE name=?",
                                       (guard,)).fetchone()[0]
        # Simulate an external write that bypassed the guard, then restore exact DDL.
        connection.execute(f"DROP TRIGGER {guard}")
        connection.execute("""INSERT INTO historical_input_external_entries
            VALUES('NAR','nar_official','other','reverse-drift',?,999)""",
            (source.race_id,))
        connection.execute(guard_sql)
        connection.commit()
        assert phase109_schema_state(connection) == PHASE109_SCHEMA_ACTIVE

        with pytest.raises(NARProductionMappingError, match="forward/reverse entry mapping drift"):
            repo.load_receipt(receipt_id=receipt.receipt_id)
    finally:
        close_all(env, connection)


def test_two_independent_phase109_publishers_share_one_authority(tmp_path):
    env, original, source, _ = ready()
    main_path = tmp_path / "main.sqlite"
    lineage_path = tmp_path / "lineage.sqlite"
    captures_path = tmp_path / "captures.sqlite"
    for connection, path in ((original, main_path), (env.connections[2], lineage_path),
                             (env.connections[1], captures_path)):
        destination = sqlite3.connect(path)
        connection.backup(destination)
        destination.close()
    barrier = threading.Barrier(2)
    outcomes = []
    lock = threading.Lock()

    def worker():
        main = sqlite3.connect(main_path, timeout=10)
        lineage_c = sqlite3.connect(lineage_path)
        capture_c = sqlite3.connect(captures_path)
        try:
            repository = SQLiteNARProductionMappingRepository(connection=main)
            lineage = SQLiteNARTrustedDebaAcquisitionArchive(connection=lineage_c)
            captures = SQLiteNAROfficialResponseCaptureRepository(connection=capture_c)
            barrier.wait(timeout=10)
            receipt = repository.publish(
                phase110_receipt_id=source.receipt_id, lineage_archive=lineage,
                capture_archive=captures, expected_external_race_id=source.external_race_id,
                expected_prediction_cutoff=source.prediction_cutoff)
            with lock:
                outcomes.append(receipt.receipt_id)
        finally:
            main.close(); lineage_c.close(); capture_c.close()

    threads = [threading.Thread(target=worker) for _ in range(2)]
    try:
        for thread in threads: thread.start()
        for thread in threads: thread.join(timeout=20)
        assert all(not thread.is_alive() for thread in threads)
        assert len(outcomes) == 2 and outcomes[0] == outcomes[1]
        check = sqlite3.connect(main_path)
        try:
            assert counts(check) == (1, 3, 1, 3)
            check.execute("PRAGMA foreign_keys=ON")
            assert check.execute("PRAGMA foreign_key_check").fetchall() == []
        finally:
            check.close()
    finally:
        close_all(env, original)
