"""Post-write failure injection, permanent reservations and independent races."""

import sqlite3
import threading
from dataclasses import replace
from datetime import timedelta

import pytest

from scripts.simulation import nar_pre_c_production_root_scope_admission_archive_migration as schema
from scripts.simulation.nar_pre_c_production_root_scope_admission import RootScopeAdmissionConflict as Conflict, RootScopeAdmissionError as Error
from scripts.simulation.nar_pre_c_production_root_scope_admission_issuance import NARPreCProductionRootScopeAdmissionIssuer as Issuer, _policy_content, _source
from scripts.simulation.sqlite_nar_pre_c_production_root_scope_admission_archive import SQLiteNARPreCProductionRootScopeAdmissionArchive as Archive
from scripts.simulation.sqlite_nar_trusted_deba_acquisition_archive import SQLiteNARTrustedDebaAcquisitionArchive
from scripts.simulation.sqlite_nar_daily_target_evidence_archive import SQLiteNARDailyTargetEvidenceArchive
from scripts.simulation.sqlite_nar_pre_c_production_claim_binding_archive import SQLiteNARPreCProductionClaimBindingArchive
from scripts.simulation.sqlite_nar_pre_c_production_prestaged_manifest_archive import SQLiteNARPreCProductionPrestagedManifestArchive
from scripts.simulation.sqlite_nar_operational_timing_runtime_execution_archive import SQLiteNAROperationalTimingRuntimeExecutionArchive
from scripts.simulation.repositories.sqlite_nar_production_mapping_repository import SQLiteNARProductionMappingRepository
from test_nar_pre_c_production_root_scope_admission_issuance import (
    context, parents_context, policy, scope, load, upstreams, fingerprints, Clock, OFFSET, T0,
)


def counts(c):
    return tuple(c.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in schema.RECORDS)


@pytest.mark.parametrize("table", list(schema.RECORDS))
def test_genuine_observed_post_write_commit_failure_each_stage(context, table):
    ctx = context
    approval = None
    if table in (schema.SCOPES, schema.AVAILABILITY):
        _, approval = policy(ctx)
    before = fingerprints(ctx)
    before_samples = ctx.clock.samples
    reached = []
    def authorizer(action, arg1, _arg2, _database, _trigger):
        if action == sqlite3.SQLITE_INSERT and arg1 == table:
            reached.append("INSERT_AUTHORIZED")
        if action == sqlite3.SQLITE_TRANSACTION and arg1 == "COMMIT" and reached:
            # Not just a pre-write authorizer event: observe the actual inserted
            # row in this transaction BEFORE denying COMMIT, proving post-write.
            assert ctx.c.execute(f"SELECT count(*) FROM {table}").fetchone() == (1,)
            reached.append("ROW_VISIBLE_BEFORE_DENIED_COMMIT")
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK
    ctx.c.set_authorizer(authorizer)
    try:
        with pytest.raises(sqlite3.DatabaseError, match="authorized"):
            policy(ctx) if approval is None else scope(ctx, approval)
    finally:
        ctx.c.set_authorizer(None)
    assert reached == ["INSERT_AUTHORIZED", "ROW_VISIBLE_BEFORE_DENIED_COMMIT"]
    assert not ctx.c.in_transaction
    expected = {schema.POLICY_CONTENTS: (0, 0, 0, 0), schema.POLICY_APPROVALS: (1, 0, 0, 0),
                schema.SCOPES: (1, 1, 0, 0), schema.AVAILABILITY: (1, 1, 1, 0)}[table]
    assert counts(ctx.c) == expected
    assert ctx.clock.samples - before_samples == (1 if table in (schema.POLICY_APPROVALS, schema.AVAILABILITY) else 0)
    assert fingerprints(ctx) == before  # No cross-store rollback/mutation.
    inert_before = tuple(ctx.c.execute(f"SELECT * FROM {schema.POLICY_CONTENTS if approval is None else schema.SCOPES}"))
    if approval is None:
        result = policy(ctx)
        assert policy(ctx) == result
    else:
        result = scope(ctx, approval)
        assert scope(ctx, approval) == result
    samples = ctx.clock.samples
    ctx.clock.value = None
    assert (policy(ctx) if approval is None else scope(ctx, approval)) == result
    assert ctx.clock.samples == samples
    if inert_before:
        assert tuple(ctx.c.execute(f"SELECT * FROM {schema.POLICY_CONTENTS if approval is None else schema.SCOPES}")) == inert_before


@pytest.mark.parametrize("table", list(schema.RECORDS))
def test_postcommit_reload_failure_never_returns_success_retains_row(context, monkeypatch, table):
    ctx = context
    approval = None
    if table in (schema.SCOPES, schema.AVAILABILITY):
        _, approval = policy(ctx)
    original = Archive._load
    def fail(self, t, record_identity):
        if t == table and not self._connection.in_transaction:
            assert self._connection.execute(f"SELECT count(*) FROM {t}").fetchone() == (1,)
            raise RuntimeError("forced postcommit exact reload failure")
        return original(self, t, record_identity)
    with monkeypatch.context() as m:
        m.setattr(Archive, "_load", fail)
        with pytest.raises(RuntimeError, match="forced postcommit"):
            policy(ctx) if approval is None else scope(ctx, approval)
    assert ctx.c.execute(f"SELECT count(*) FROM {table}").fetchone() == (1,)
    assert not ctx.c.in_transaction
    if approval is None:
        result = policy(ctx)
        assert policy(ctx) == result
    else:
        result = scope(ctx, approval)
        assert load(ctx, result) == result


def test_postcommit_upstream_failure_retains_scope_and_retry_revalidates(context, monkeypatch):
    _, approval = policy(context)
    original = type(context.parents.archive).load_binding
    def fail(self, **args):
        if context.c.execute(f"SELECT count(*) FROM {schema.AVAILABILITY}").fetchone() == (1,):
            raise RuntimeError("postcommit upstream failure")
        return original(self, **args)
    with monkeypatch.context() as m:
        m.setattr(type(context.parents.archive), "load_binding", fail)
        with pytest.raises(RuntimeError, match="upstream failure"):
            scope(context, approval)
    assert counts(context.c) == (1, 1, 1, 1)
    samples = context.clock.samples
    pair = scope(context, approval)
    assert load(context, pair) == pair
    assert context.clock.samples == samples


def test_publication_source_reread_failure_retains_receipt(context, monkeypatch):
    from scripts.simulation import nar_pre_c_production_root_scope_admission_issuance as issuance
    original = issuance._verify_policy_source
    def fail(content, **args):
        if context.c.execute(f"SELECT count(*) FROM {schema.POLICY_APPROVALS}").fetchone() == (1,):
            raise RuntimeError("postcommit source failure")
        return original(content, **args)
    with monkeypatch.context() as m:
        m.setattr(issuance, "_verify_policy_source", fail)
        with pytest.raises(RuntimeError, match="source failure"):
            policy(context)
    assert counts(context.c) == (1, 1, 0, 0)
    samples = context.clock.samples
    policy(context)
    assert context.clock.samples == samples


@pytest.mark.parametrize("completed", [False, True])
def test_permanent_scope_dataset_conflict_including_orphan(context, completed):
    _, approval = policy(context)
    if not completed:
        context.clock.value = None
        with pytest.raises(Error):
            scope(context, approval)
    else:
        scope(context, approval)
    before = tuple(context.c.iterdump())
    with pytest.raises(Conflict):
        scope(context, approval, dataset_id="contradictory")
    assert tuple(context.c.iterdump()) == before


@pytest.mark.parametrize("direction", ["external", "internal"])
def test_forward_reverse_scope_conflict_precedes_insert(context, direction):
    _, approval = policy(context)
    value, _ = scope(context, approval)
    row = list(schema.record_row(schema.SCOPES, value))
    columns = ("identity", *schema.RECORDS[schema.SCOPES][1], "schema_version", "payload_json")
    row[columns.index("identity")] = value.identity[:-64] + "f" * 64
    row[columns.index("phase113_binding_identity")] = value.phase113_binding_identity[:-64] + "f" * 64
    if direction == "external":
        row[columns.index("internal_race_id")] = 999
    else:
        row[columns.index("external_race_id")] = "nar:20250101:21:2"
    # Isolate each SQL protection (the other target key is distinct). This
    # attempted raw row is NOT a qualified value/publication and cannot survive.
    with pytest.raises(sqlite3.IntegrityError, match=f"{direction}_race_id"):
        context.c.execute(f"INSERT INTO {schema.SCOPES} VALUES({','.join('?' for _ in row)})", row)
    context.c.rollback()
    assert counts(context.c) == (1, 1, 1, 1)


def test_policy_orphan_selection_provenance_is_permanent(context):
    context.clock.value = None
    with pytest.raises(Error):
        policy(context)
    content = context.archive._load(schema.POLICY_CONTENTS,
        context.c.execute(f"SELECT identity FROM {schema.POLICY_CONTENTS}").fetchone()[0])
    other = replace(content, anchor_declaration_id=content.anchor_declaration_id[:-64] + "f" * 64)
    with pytest.raises(Conflict):
        context.archive._stage_content(schema.POLICY_CONTENTS, other)
    assert counts(context.c) == (1, 0, 0, 0)


def _clone_sources(ctx, tmp_path):
    p = ctx.parents
    sources = {"main": p.main, "phase113": p.connection, "runtime": p.runtime_connection,
               "phase112": p.prestaged_connection, "lineage": p.envs[0].connections[2],
               "daily": p.envs[0].connections[0], "companion": ctx.c}
    paths = {}
    for name, source in sources.items():
        path = tmp_path / (name + ".sqlite")
        dest = sqlite3.connect(path)
        source.backup(dest)
        dest.close()
        paths[name] = path
    return paths


@pytest.mark.parametrize("publication", ["policy", "scope"])
@pytest.mark.parametrize("contradictory", [False, True])
def test_two_independent_file_backed_publishers(context, tmp_path, publication, contradictory):
    ctx = context
    approval = policy(ctx)[1] if publication == "scope" else None
    anchor_ids = [ctx.parents.receipt.phase111_declaration_id] * 2
    if publication == "policy" and contradictory:
        original = ctx.parents.envs[0].lineage.load_declaration(declaration_id=anchor_ids[0])
        other = replace(original, issued_at=original.issued_at + timedelta(seconds=1))
        ctx.parents.envs[0].lineage.save_declaration(declaration=other)
        anchor_ids[1] = other.identity
    paths = _clone_sources(ctx, tmp_path)
    barrier = threading.Barrier(2)
    results, errors, sample_counts = [], [], []
    def worker(index):
        connections = {name: sqlite3.connect(path, timeout=10) for name, path in paths.items()}
        try:
            archive = Archive(connection=connections["companion"])
            now = (T0 + timedelta(minutes=2) if publication == "policy"
                   else ctx.parents.authority.availability_receipt.available_at + timedelta(seconds=1))
            clock = Clock(connections["companion"], now + timedelta(seconds=index))
            issuer = Issuer(companion_archive=archive,
                            lineage_archive=SQLiteNARTrustedDebaAcquisitionArchive(connection=connections["lineage"]),
                            daily_archive=SQLiteNARDailyTargetEvidenceArchive(connection=connections["daily"]), utc_clock=clock)
            barrier.wait(timeout=10)
            try:
                if publication == "policy":
                    result = issuer.publish_policy(anchor_declaration_id=anchor_ids[index], offset_microseconds=OFFSET)
                else:
                    result = issuer.publish_scope(policy_approval_identity=approval.identity,
                        phase113_binding_identity=ctx.binding.identity, dataset_id="different" if contradictory and index else "shared",
                        phase113_archive=SQLiteNARPreCProductionClaimBindingArchive(connection=connections["phase113"]),
                        runtime_archive=SQLiteNAROperationalTimingRuntimeExecutionArchive(connection=connections["runtime"]),
                        phase112_archive=SQLiteNARPreCProductionPrestagedManifestArchive(connection=connections["phase112"]),
                        phase109_repository=SQLiteNARProductionMappingRepository(connection=connections["main"]))
                results.append(result)
            except Conflict as exc:
                errors.append(exc)
            sample_counts.append(clock.samples)
        except BaseException as exc:
            errors.append(exc)
        finally:
            for c in connections.values():
                c.close()
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
        assert not thread.is_alive()
    if contradictory:
        assert len(results) == 1 and len(errors) == 1 and isinstance(errors[0], Conflict), errors
    else:
        assert not errors
        assert len(results) == 2 and results[0] == results[1]
    assert sum(sample_counts) == 1
    c = sqlite3.connect(paths["companion"])
    try:
        assert counts(c) == ((1, 1, 0, 0) if publication == "policy" else (1, 1, 1, 1))
        assert c.execute("PRAGMA foreign_key_check").fetchall() == []
        assert schema.phase114_schema_state(c) == schema.ACTIVE
    finally:
        c.close()
