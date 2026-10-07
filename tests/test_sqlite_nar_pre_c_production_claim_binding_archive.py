"""Committed authority reload, permanent conflicts, real rollback and SQLite races."""

from dataclasses import replace
import sqlite3
import threading
from types import SimpleNamespace

import pytest

from scripts.simulation import nar_pre_c_production_claim_binding_archive_migration as schema
from scripts.simulation.nar_pre_c_production_claim_binding import (
    NARPreCProductionClaimBindingError as Error, NARPreCProductionClaimBindingConflict as Conflict, binding_row,
)
from scripts.simulation.nar_pre_c_production_claim_binding_issuance import issue_nar_pre_c_production_claim_binding as issue
from scripts.simulation.sqlite_nar_pre_c_production_claim_binding_archive import (
    SQLiteNARPreCProductionClaimBindingArchive as Archive, _upstream_binding,
)
from scripts.simulation.sqlite_nar_operational_timing_runtime_execution_archive import SQLiteNAROperationalTimingRuntimeExecutionArchive as RuntimeArchive
from scripts.simulation.sqlite_nar_pre_c_production_prestaged_manifest_archive import SQLiteNARPreCProductionPrestagedManifestArchive as Phase112Archive
from scripts.simulation.repositories.sqlite_nar_production_mapping_repository import SQLiteNARProductionMappingRepository as Phase109Repository
from scripts.simulation.nar_pre_c_production_prestaged_manifest import NARPreCProductionPrestagingError
from scripts.simulation.sqlite_nar_operational_timing_observability_archive import TimingArchiveError
from test_nar_pre_c_production_claim_binding_issuance import context, arguments, load, add_claim


def count(c):
    return c.execute(f"SELECT count(*) FROM {schema.BINDINGS}").fetchone()[0]


def upstream_connections(ctx):
    return (ctx.runtime_connection, ctx.main, ctx.prestaged_connection)


def test_idempotence_is_durable_and_revalidates_every_upstream(context, monkeypatch):
    value = issue(**arguments(context))
    assert count(context.connection) == 1
    before = context.connection.total_changes
    assert issue(**arguments(context)) == value
    assert context.connection.total_changes == before
    assert load(context, value.identity) == value
    def unavailable(*_args, **_kwargs):
        raise sqlite3.OperationalError("upstream temporarily unavailable")
    monkeypatch.setattr(Phase109Repository, "load_receipt", unavailable)
    with pytest.raises(sqlite3.OperationalError, match="temporarily unavailable"):
        load(context, value.identity)
    with pytest.raises(sqlite3.OperationalError):
        issue(**arguments(context))
    assert count(context.connection) == 1
    assert not context.connection.in_transaction


def test_another_genuine_claim_cannot_ever_rescue_or_rebind_manifest(context):
    winner = issue(**arguments(context))
    other = add_claim(context.runtime, previous=context.parents, offset=1)
    with pytest.raises(Conflict, match="permanent"):
        issue(**arguments(context, parents=other))
    assert count(context.connection) == 1
    assert load(context, winner.identity) == winner
    assert not context.connection.in_transaction


@pytest.mark.parametrize("key", ["external", "internal", "manifest", "availability"])
def test_all_permanent_collision_keys_fail_closed_without_repair(context, key):
    args = arguments(context)
    expected = _upstream_binding(**{k: v for k, v in args.items() if k != "companion_archive"})
    # Deliberately injected contradictory local content is never origin evidence.
    changes = dict(phase112_manifest_identity=expected.phase112_manifest_identity[:-64] + "f" * 64,
                   phase112_availability_receipt_identity=expected.phase112_availability_receipt_identity[:-64] + "f" * 64,
                   internal_race_id=999, external_race_id="nar:20250101:24:1")
    if key == "external":
        changes["external_race_id"] = expected.external_race_id
    if key == "internal":
        changes["internal_race_id"] = expected.internal_race_id
    if key == "manifest":
        changes["phase112_manifest_identity"] = expected.phase112_manifest_identity
    if key == "availability":
        changes["phase112_availability_receipt_identity"] = expected.phase112_availability_receipt_identity
    contradictory = replace(expected, **changes)
    row = binding_row(contradictory)
    context.connection.execute(f"INSERT INTO {schema.BINDINGS} VALUES({','.join('?' for _ in row)})", row)
    context.connection.commit()
    original = tuple(context.connection.iterdump())
    with pytest.raises(Conflict):
        issue(**args)
    assert tuple(context.connection.iterdump()) == original
    assert not context.connection.in_transaction
    with pytest.raises((Error, NARPreCProductionPrestagingError, RuntimeError)):
        load(context, contradictory.identity)


def test_genuine_post_write_commit_denial_rolls_back_and_leaves_upstreams_identical(context):
    c = context.connection
    changes_before = c.total_changes
    before = [tuple(upstream.iterdump()) for upstream in upstream_connections(context)]
    observed = []
    def authorizer(action, operation, _column, _db, _trigger):
        if action == sqlite3.SQLITE_TRANSACTION and operation == "COMMIT":
            # Executed SQLite changes, not merely authorization to prepare INSERT.
            observed.append(c.total_changes - changes_before)
            assert count(c) == 1
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK
    c.set_authorizer(authorizer)
    try:
        with pytest.raises(sqlite3.DatabaseError, match="not authorized"):
            issue(**arguments(context))
    finally:
        c.set_authorizer(None)
    assert observed == [1]
    assert count(c) == 0
    assert not c.in_transaction
    assert [tuple(upstream.iterdump()) for upstream in upstream_connections(context)] == before
    winner = issue(**arguments(context))
    assert load(context, winner.identity) == winner


def test_post_commit_local_reload_failure_never_returns_success_but_keeps_binding(context, monkeypatch):
    original = Archive.load_binding
    def fail(*_args, **_kwargs):
        assert not context.connection.in_transaction
        assert count(context.connection) == 1
        raise Error("forced post-commit reload failure")
    monkeypatch.setattr(Archive, "load_binding", fail)
    with pytest.raises(Error, match="post-commit"):
        issue(**arguments(context))
    assert count(context.connection) == 1
    assert not context.connection.in_transaction
    monkeypatch.setattr(Archive, "load_binding", original)
    changes = context.connection.total_changes
    value = issue(**arguments(context))
    assert context.connection.total_changes == changes
    assert load(context, value.identity) == value


def test_post_commit_upstream_failure_is_not_cross_store_rollback(context, monkeypatch):
    original = RuntimeArchive.load_claim_for_session
    calls = []
    def fail_on_reread(self, **kwargs):
        calls.append(kwargs)
        if count(context.connection) == 1:
            assert count(context.connection) == 1
            assert not context.connection.in_transaction
            raise Error("upstream reread failed")
        return original(self, **kwargs)
    monkeypatch.setattr(RuntimeArchive, "load_claim_for_session", fail_on_reread)
    with pytest.raises(Error, match="reread failed"):
        issue(**arguments(context))
    # Initial readiness verification itself re-loads the claim. The failure is
    # keyed to actual committed Phase113 state, not a guessed invocation count.
    assert len(calls) >= 3
    assert count(context.connection) == 1
    monkeypatch.setattr(RuntimeArchive, "load_claim_for_session", original)
    assert load(context, issue(**arguments(context)).identity) is not None


@pytest.mark.parametrize("missing", ["load_claim_for_session", "load_binding", "load_readiness_for_claim"])
def test_every_runtime_parent_must_exact_reload(context, monkeypatch, missing):
    monkeypatch.setattr(RuntimeArchive, missing, lambda *_a, **_k: None)
    with pytest.raises((Error, TimingArchiveError)):
        issue(**arguments(context))
    assert count(context.connection) == 0


def test_runtime_ancestry_contradiction_is_not_accepted(context, monkeypatch):
    other = add_claim(context.runtime, previous=context.parents, offset=1)
    monkeypatch.setattr(RuntimeArchive, "load_binding", lambda *_a, **_k: other[1])
    with pytest.raises(TimingArchiveError, match="corrupt"):
        issue(**arguments(context))
    assert count(context.connection) == 0


@pytest.mark.parametrize("version", [18, 19])
def test_upstream_v018_or_v019_corruption_fails_closed(context, version):
    names = context.main.execute("SELECT name FROM sqlite_schema WHERE type='trigger' AND name LIKE ?",
                                 ("nar_identity_complete%" if version == 18 else "nar_production_mapping%",)).fetchall()
    assert names
    context.main.execute(f'DROP TRIGGER "{names[0][0]}"')
    context.main.commit()
    with pytest.raises((RuntimeError, Error)):
        issue(**arguments(context))
    assert count(context.connection) == 0


def test_caller_transaction_not_owned_or_rolled_back(context):
    context.connection.execute("BEGIN")
    with pytest.raises(Error, match="caller transaction"):
        issue(**arguments(context))
    assert context.connection.in_transaction
    context.connection.rollback()


@pytest.mark.parametrize("contradictory", [False, True])
def test_two_independent_publishers_have_one_immutable_winner(context, tmp_path, contradictory):
    ctx = context
    other = add_claim(ctx.runtime, previous=ctx.parents, offset=1) if contradictory else ctx.parents
    paths = []
    for name, source in zip(("runtime", "main", "phase112", "binding"), (*upstream_connections(ctx), ctx.connection)):
        path = tmp_path / (name + ".sqlite")
        target = sqlite3.connect(path)
        source.backup(target)
        target.close()
        paths.append(path)
    barrier = threading.Barrier(2)
    results, errors = [], []
    def worker(parents):
        connections = [sqlite3.connect(path, timeout=10) for path in paths]
        try:
            rt, main, prestaged, local = connections
            thread_ctx = SimpleNamespace(runtime=RuntimeArchive(connection=rt),
                                         repo=Phase109Repository(connection=main),
                                         phase112=Phase112Archive(connection=prestaged),
                                         archive=Archive(connection=local), parents=parents,
                                         authority=ctx.authority)
            barrier.wait(timeout=10)
            results.append(issue(**arguments(thread_ctx)))
        except BaseException as exc:
            errors.append(exc)
        finally:
            for c in connections:
                c.close()
    workers = [threading.Thread(target=worker, args=(parents,)) for parents in (ctx.parents, other)]
    for t in workers:
        t.start()
    for t in workers:
        t.join(timeout=25)
        assert not t.is_alive()
    if contradictory:
        assert len(results) == 1
        assert len(errors) == 1 and isinstance(errors[0], Conflict)
    else:
        assert not errors
        assert len(results) == 2 and results[0] == results[1]
    with sqlite3.connect(paths[-1]) as c:
        assert count(c) == 1
        assert c.execute(f"SELECT identity FROM {schema.BINDINGS}").fetchone() == (results[0].identity,)
        assert c.execute("PRAGMA foreign_key_check").fetchall() == []
        assert schema.phase113_schema_state(c) == schema.ACTIVE


def test_publication_operational_write_lock_propagates_without_false_corruption(context, tmp_path):
    path = tmp_path / "locked.sqlite"
    c = sqlite3.connect(path, timeout=0)
    owner = sqlite3.connect(path)
    try:
        schema.apply(c)
        archive = Archive(connection=c)
        owner.execute("BEGIN IMMEDIATE")
        args = arguments(context)
        args["companion_archive"] = archive
        with pytest.raises(sqlite3.OperationalError, match="locked"):
            issue(**args)
        assert schema.phase113_schema_state(c) == schema.ACTIVE
        assert count(c) == 0
        assert not c.in_transaction
    finally:
        owner.rollback(); owner.close(); c.close()


def test_manual_canonical_content_cannot_bypass_upstream_exact_equality(context):
    winner = issue(**arguments(context))
    c = context.connection
    c.execute(f"DROP TRIGGER {schema.BINDINGS}_no_update")
    forged = replace(winner, phase109_receipt_id="f" * 64)
    # Simulate bypassed guards, then restore exact topology. Content must still fail.
    columns = [row[1] for row in c.execute(f"PRAGMA table_info({schema.BINDINGS})")]
    c.execute(f"UPDATE {schema.BINDINGS} SET {','.join(name + '=?' for name in columns)}", binding_row(forged))
    c.execute(schema._DDL[f"{schema.BINDINGS}_no_update"])
    c.commit()
    assert schema.phase113_schema_state(c) == schema.ACTIVE
    with pytest.raises(Error, match="projection differs"):
        load(context, forged.identity)


def test_corrupt_phase112_topology_cannot_qualify(context):
    context.prestaged_connection.execute("CREATE TABLE sqliteXunreviewed(id INTEGER)")
    context.prestaged_connection.commit()
    with pytest.raises(RuntimeError):
        issue(**arguments(context))
    assert count(context.connection) == 0


def test_v010_drift_cannot_qualify_even_if_v019_rows_remain(context):
    c = context.main
    # Simulate external corruption by bypassing guard; never a production repair.
    guards = c.execute("SELECT name,sql FROM sqlite_schema WHERE type='trigger' AND tbl_name='historical_input_external_entries'").fetchall()
    for name, _ in guards:
        c.execute(f'DROP TRIGGER "{name}"')
    c.execute("PRAGMA foreign_keys=OFF")
    c.execute("DELETE FROM historical_input_external_entries")
    for _, sql in guards:
        c.execute(sql)
    c.commit()
    with pytest.raises((RuntimeError, ValueError)):
        issue(**arguments(context))
    assert count(context.connection) == 0
