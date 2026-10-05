"""Phase112 archive rollback, exact reload, immutability, and concurrency."""

import sqlite3
import threading
from dataclasses import replace
from datetime import timedelta

import pytest

from scripts.simulation import nar_pre_c_production_prestaged_manifest_archive_migration as schema
from scripts.simulation.nar_pre_c_production_prestaged_manifest import (
    NARPreCProductionPrestagingError, manifest_from_phase109,
)
from scripts.simulation.repositories.sqlite_nar_production_mapping_repository import (
    SQLiteNARProductionMappingRepository,
)
from scripts.simulation.sqlite_nar_pre_c_production_prestaged_manifest_archive import (
    SQLiteNARPreCProductionPrestagedManifestArchive,
)
from test_sqlite_nar_production_mapping_repository import close_all, publish, ready


def prepared():
    env, main, source, repo = ready()
    upstream = publish(repo, env, source)
    companion = sqlite3.connect(":memory:")
    schema.apply(companion)
    archive = SQLiteNARPreCProductionPrestagedManifestArchive(connection=companion)
    return env, main, repo, upstream, companion, archive


def issue(archive, repo, upstream, clock):
    return archive.publish(
        phase109_repository=repo, phase109_receipt_id=upstream.receipt_id,
        expected_external_race_id=upstream.external_race_id,
        expected_prediction_cutoff=upstream.prediction_cutoff, utc_clock=clock,
    )


def counts(connection):
    return (connection.execute(f"SELECT count(*) FROM {schema.MANIFESTS}").fetchone()[0],
            connection.execute(f"SELECT count(*) FROM {schema.AVAILABILITY}").fetchone()[0])


def test_exact_authority_and_repeat_preserve_original_clock_and_main_db():
    env, main, repo, upstream, companion, archive = prepared()
    try:
        before = main.total_changes
        calls = []
        def clock():
            calls.append(1)
            return upstream.issued_at + timedelta(seconds=1)
        first = issue(archive, repo, upstream, clock)
        assert counts(companion) == (1, 1)
        assert len(calls) == 1
        assert archive.load_authority(manifest_identity=first.manifest.identity,
                                      phase109_repository=repo) == first
        assert issue(archive, repo, upstream, clock) == first
        assert len(calls) == 1
        assert main.total_changes == before
        assert main.execute("SELECT count(*) FROM nar_identity_complete_denials").fetchone() == (3,)
        assert not companion.in_transaction
    finally:
        companion.close()
        close_all(env, main)


def test_stage_a_real_insert_failure_rolls_back_completely():
    env, main, repo, upstream, companion, archive = prepared()
    calls = []
    def deny_manifest(action, table, *_args):
        if action == sqlite3.SQLITE_INSERT and table == schema.MANIFESTS:
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK
    try:
        companion.set_authorizer(deny_manifest)
        with pytest.raises(sqlite3.DatabaseError):
            issue(archive, repo, upstream, lambda: calls.append(1))
        companion.set_authorizer(None)
        assert counts(companion) == (0, 0)
        assert calls == []
        assert not companion.in_transaction
    finally:
        companion.close()
        close_all(env, main)


def test_stage_a_successful_insert_then_denied_commit_rolls_back():
    env, main, repo, upstream, companion, archive = prepared()
    baseline = companion.total_changes
    observed = []
    clock_calls = []

    def deny_commit_after_manifest_insert(action, argument, *_args):
        if action == sqlite3.SQLITE_INSERT and argument == schema.MANIFESTS:
            observed.append("manifest insert reached")
        if action == sqlite3.SQLITE_TRANSACTION and argument == "COMMIT" and observed:
            observed.append(("commit denied after write", companion.total_changes - baseline))
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    try:
        companion.set_authorizer(deny_commit_after_manifest_insert)
        with pytest.raises(sqlite3.DatabaseError, match="not authorized"):
            issue(archive, repo, upstream, lambda: clock_calls.append(1))
        companion.set_authorizer(None)
        assert observed == ["manifest insert reached", ("commit denied after write", 1)]
        assert companion.total_changes - baseline == 1
        assert counts(companion) == (0, 0)
        assert not companion.in_transaction
        assert clock_calls == []
    finally:
        companion.set_authorizer(None)
        companion.close()
        close_all(env, main)


def test_stage_b_failure_leaves_inert_manifest_then_retry_samples_once():
    env, main, repo, upstream, companion, archive = prepared()
    calls = []
    def clock():
        calls.append(1)
        return upstream.issued_at + timedelta(seconds=len(calls))
    def deny_availability(action, table, *_args):
        if action == sqlite3.SQLITE_INSERT and table == schema.AVAILABILITY:
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK
    try:
        companion.set_authorizer(deny_availability)
        with pytest.raises(sqlite3.DatabaseError):
            issue(archive, repo, upstream, clock)
        companion.set_authorizer(None)
        assert counts(companion) == (1, 0)
        assert len(calls) == 1
        assert not companion.in_transaction
        with pytest.raises(NARPreCProductionPrestagingError, match="no availability"):
            archive.load_authority(
                manifest_identity=manifest_from_phase109(upstream).identity,
                phase109_repository=repo)
        completed = issue(archive, repo, upstream, clock)
        assert len(calls) == 2
        assert completed.availability_receipt.available_at == upstream.issued_at + timedelta(seconds=2)
        assert counts(companion) == (1, 1)
        assert issue(archive, repo, upstream, clock) == completed
        assert len(calls) == 2
    finally:
        companion.close()
        close_all(env, main)


def test_stage_b_successful_insert_then_denied_commit_preserves_inert_manifest():
    env, main, repo, upstream, companion, archive = prepared()
    manifest = manifest_from_phase109(upstream)
    clock_calls = []

    def clock():
        clock_calls.append(1)
        return upstream.issued_at + timedelta(seconds=len(clock_calls))

    try:
        archive._stage_manifest(manifest)
        original_row = companion.execute(
            f"SELECT * FROM {schema.MANIFESTS} WHERE identity=?", (manifest.identity,),
        ).fetchone()
        assert original_row is not None
        assert counts(companion) == (1, 0)
        baseline = companion.total_changes
        observed = []

        def deny_commit_after_availability_insert(action, argument, *_args):
            if action == sqlite3.SQLITE_INSERT and argument == schema.AVAILABILITY:
                observed.append("availability insert reached")
            if action == sqlite3.SQLITE_TRANSACTION and argument == "COMMIT" and observed:
                observed.append(("commit denied after write", companion.total_changes - baseline))
                return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK

        companion.set_authorizer(deny_commit_after_availability_insert)
        with pytest.raises(sqlite3.DatabaseError, match="not authorized"):
            issue(archive, repo, upstream, clock)
        companion.set_authorizer(None)
        assert observed == ["availability insert reached", ("commit denied after write", 1)]
        assert companion.total_changes - baseline == 1
        assert counts(companion) == (1, 0)
        assert companion.execute(
            f"SELECT * FROM {schema.MANIFESTS} WHERE identity=?", (manifest.identity,),
        ).fetchone() == original_row
        assert not companion.in_transaction
        assert len(clock_calls) == 1

        completed = issue(archive, repo, upstream, clock)
        assert counts(companion) == (1, 1)
        assert len(clock_calls) == 2
        assert completed.availability_receipt.available_at == upstream.issued_at + timedelta(seconds=2)
        assert issue(archive, repo, upstream, clock) == completed
        assert len(clock_calls) == 2
    finally:
        companion.set_authorizer(None)
        companion.close()
        close_all(env, main)


def test_post_manifest_commit_reload_failure_cannot_sample_or_succeed(monkeypatch):
    env, main, repo, upstream, companion, archive = prepared()
    calls = []
    try:
        original = archive.load_manifest
        def fail_after_commit(*, identity):
            if not companion.in_transaction:
                raise NARPreCProductionPrestagingError("forced postcommit reload failure")
            return original(identity=identity)
        monkeypatch.setattr(archive, "load_manifest", fail_after_commit)
        with pytest.raises(NARPreCProductionPrestagingError, match="forced postcommit"):
            issue(archive, repo, upstream, lambda: calls.append(1))
        monkeypatch.setattr(archive, "load_manifest", original)
        assert counts(companion) == (1, 0)
        assert calls == []
        assert not companion.in_transaction
    finally:
        companion.close()
        close_all(env, main)


def test_post_availability_commit_reload_failure_returns_no_authority(monkeypatch):
    env, main, repo, upstream, companion, archive = prepared()
    calls = []
    def clock():
        calls.append(1)
        return upstream.issued_at + timedelta(seconds=1)
    try:
        original = archive.load_authority
        def fail_reload(**_kwargs):
            raise NARPreCProductionPrestagingError("forced final reload failure")
        monkeypatch.setattr(archive, "load_authority", fail_reload)
        with pytest.raises(NARPreCProductionPrestagingError, match="forced final"):
            issue(archive, repo, upstream, clock)
        monkeypatch.setattr(archive, "load_authority", original)
        assert counts(companion) == (1, 1)
        assert not companion.in_transaction
        assert len(calls) == 1
        assert issue(archive, repo, upstream, clock) == original(
            manifest_identity=manifest_from_phase109(upstream).identity,
            phase109_repository=repo)
        assert len(calls) == 1
    finally:
        companion.close()
        close_all(env, main)


@pytest.mark.parametrize("conflict", ["external", "internal", "receipt"])
def test_forward_reverse_or_receipt_conflict_fails_closed(conflict):
    env, main, repo, upstream, companion, archive = prepared()
    try:
        original = manifest_from_phase109(upstream)
        if conflict == "external":
            forged = replace(original, phase109_receipt_id="1" * 64,
                             internal_race_id=original.internal_race_id + 1)
        elif conflict == "internal":
            forged = replace(original, phase109_receipt_id="1" * 64,
                             external_race_id=original.external_race_id + ":other")
        else:
            forged = replace(original, external_race_id=original.external_race_id + ":other",
                             internal_race_id=original.internal_race_id + 1)
        companion.execute(
            f"INSERT INTO {schema.MANIFESTS} VALUES({','.join('?' for _ in archive._manifest_row(forged))})",
            archive._manifest_row(forged))
        companion.commit()
        with pytest.raises(NARPreCProductionPrestagingError, match="contradictory"):
            issue(archive, repo, upstream, lambda: upstream.issued_at)
        assert counts(companion) == (1, 0)
        assert not companion.in_transaction
    finally:
        companion.close()
        close_all(env, main)


def test_append_only_triggers_work_without_foreign_keys():
    env, main, repo, upstream, companion, archive = prepared()
    try:
        authority = issue(archive, repo, upstream, lambda: upstream.issued_at)
        companion.execute("PRAGMA foreign_keys=OFF")
        assert companion.execute("PRAGMA foreign_keys").fetchone() == (0,)
        for table in (schema.MANIFESTS, schema.AVAILABILITY):
            with pytest.raises(sqlite3.IntegrityError, match="immutable"):
                companion.execute(f"UPDATE {table} SET identity='different'")
            with pytest.raises(sqlite3.IntegrityError, match="immutable"):
                companion.execute(f"DELETE FROM {table}")
        companion.rollback()
        assert archive.load_authority(manifest_identity=authority.manifest.identity,
                                      phase109_repository=repo) == authority
        assert counts(companion) == (1, 1)
    finally:
        companion.close()
        close_all(env, main)


def test_two_independent_publishers_share_one_receipt_and_time(tmp_path):
    env, main, repo, upstream, companion, _archive = prepared()
    main_path = tmp_path / "main-copy.sqlite"
    archive_path = tmp_path / "phase112.sqlite"
    copied = sqlite3.connect(main_path)
    try:
        main.backup(copied)
        copied.close()
        destination = sqlite3.connect(archive_path)
        try:
            schema.apply(destination)
        finally:
            destination.close()
        barrier = threading.Barrier(2)
        results = []
        failures = []
        clock_calls = []
        def worker():
            main_connection = sqlite3.connect(main_path, timeout=10)
            archive_connection = sqlite3.connect(archive_path, timeout=10)
            try:
                local_repo = SQLiteNARProductionMappingRepository(connection=main_connection)
                local_archive = SQLiteNARPreCProductionPrestagedManifestArchive(
                    connection=archive_connection)
                barrier.wait(timeout=10)
                def clock():
                    clock_calls.append(1)
                    return upstream.issued_at + timedelta(seconds=len(clock_calls))
                results.append(issue(local_archive, local_repo, upstream, clock))
            except BaseException as exc:
                failures.append(exc)
            finally:
                archive_connection.close()
                main_connection.close()
        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=20)
        assert all(not thread.is_alive() for thread in threads)
        assert not failures
        assert len(results) == 2 and results[0] == results[1]
        assert len(clock_calls) == 1
        checker = sqlite3.connect(archive_path)
        try:
            assert counts(checker) == (1, 1)
            assert checker.execute("PRAGMA foreign_key_check").fetchall() == []
        finally:
            checker.close()
    finally:
        companion.close()
        close_all(env, main)


def test_locked_companion_operational_error_propagates(tmp_path):
    env, main, repo, upstream, companion, _archive = prepared()
    archive_path = tmp_path / "locked.sqlite"
    owner = sqlite3.connect(archive_path)
    contender = sqlite3.connect(archive_path, timeout=0)
    try:
        schema.apply(owner)
        archive = SQLiteNARPreCProductionPrestagedManifestArchive(connection=contender)
        owner.execute("BEGIN EXCLUSIVE")
        with pytest.raises(sqlite3.OperationalError, match="locked"):
            issue(archive, repo, upstream, lambda: upstream.issued_at)
    finally:
        owner.rollback()
        owner.close()
        contender.close()
        companion.close()
        close_all(env, main)
