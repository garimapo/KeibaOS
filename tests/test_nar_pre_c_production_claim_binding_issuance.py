"""Real offline upstream authority fixtures; Phase113 performs reads only."""

from dataclasses import replace
from datetime import timedelta
from functools import lru_cache
import inspect
import sqlite3
from types import SimpleNamespace

import pytest

from scripts.simulation import nar_pre_c_production_claim_binding_archive_migration as schema
from scripts.simulation.nar_pre_c_production_claim_binding import NARPreCProductionClaimBindingError as Error
from scripts.simulation.nar_pre_c_production_claim_binding_issuance import issue_nar_pre_c_production_claim_binding as issue
from scripts.simulation.sqlite_nar_pre_c_production_claim_binding_archive import SQLiteNARPreCProductionClaimBindingArchive as Archive
from scripts.simulation.sqlite_nar_operational_timing_runtime_execution_archive import (
    SQLiteNAROperationalTimingRuntimeExecutionArchive as RuntimeArchive, _ISSUANCE_MARKER,
)
from scripts.simulation.nar_operational_timing_runtime_execution import (
    NAROperationalTimingCampaignExecutionClaim as Claim,
    NAROperationalTimingCampaignReadinessVerificationReceipt as Readiness,
)
from scripts.simulation.nar_operational_timing_observability_v2 import NAROperationalTimingMeasurementSessionV2 as Session
from scripts.simulation.nar_operational_timing_session_activation_v2 import issue_nar_operational_timing_session_activation_v2
from scripts.simulation.repositories.sqlite_nar_identity_complete_entry_repository import SQLiteNARIdentityCompleteEntryRepository
from test_nar_operational_timing_runtime_execution_archive import _ready_archive, _config, START, ROOT, COMMIT
from scripts.simulation.nar_operational_timing_runtime_source_provenance import _git_manifest
from scripts.simulation.nar_operational_timing_runtime_profile import derive_runtime_dependency_profile, derive_static_runtime_transport_profile
from scripts.simulation.nar_operational_timing_runtime_execution import NAROperationalTimingRuntimeBinding as Binding
from scripts.simulation.nar_pre_c_production_prestaged_manifest import NARPreCProductionPrestagingError
from test_nar_pre_c_production_prestaged_manifest_issuance import prepared, issue as prestage
from test_sqlite_nar_production_mapping_repository import publish as map_publish, persist
from test_nar_trusted_deba_acquisition import environment, acquire
from test_nar_identity_complete_entry_source import BODY


@lru_cache(maxsize=1)
def reviewed_fixture_bundle():
    # Exact immutable Git-object fixture, reused only to avoid repeating fixture IO.
    # This is not a cache of a Phase113 authoritative reload.
    return _git_manifest(ROOT, COMMIT)[0]


def add_claim(runtime, *, previous=None, offset=0, readiness_offset=0):
    if previous is None:
        config = _config()
        session = Session(config, START, START + timedelta(hours=1))
        runtime.v2.save_configuration(configuration=config)
        runtime.v2.save_session(session=session)
        activation = issue_nar_operational_timing_session_activation_v2(
            session=session, archive=runtime.v2, utc_clock=lambda: START - timedelta(hours=1))
        bundle = reviewed_fixture_bundle()
        dependency, transport = derive_runtime_dependency_profile(), derive_static_runtime_transport_profile()
        runtime.save_bundle(bundle=bundle)
        runtime.save_dependency_profile(profile=dependency)
        runtime.save_transport_profile(profile=transport)
        binding = Binding(config.configuration_identity, session.session_identity,
                          activation.declaration.declaration_identity,
                          activation.verification_receipt.verification_identity,
                          bundle.bundle_identity, dependency.profile_identity, transport.profile_identity,
                          "nar-operational-timing-lock-scope-v1:" + "a" * 64)
    else:
        old_session, old_binding, _, _ = previous
        session = Session(old_session.configuration, START + timedelta(days=offset),
                          START + timedelta(days=offset, hours=1))
        runtime.v2.save_session(session=session)
        activation = issue_nar_operational_timing_session_activation_v2(
            session=session, archive=runtime.v2,
            utc_clock=lambda: session.measurement_start_at - timedelta(hours=1))
        binding = replace(old_binding, session_identity=session.session_identity,
                          declaration_identity=activation.declaration.declaration_identity,
                          verification_identity=activation.verification_receipt.verification_identity)
    runtime.save_binding(binding=binding, _issuance_marker=_ISSUANCE_MARKER)
    claim = Claim(binding.configuration_identity, binding.session_identity, binding.declaration_identity,
                  binding.verification_identity, binding.binding_identity, binding.bundle_identity,
                  binding.lock_scope_identity)
    runtime.save_claim(claim=claim, _issuance_marker=_ISSUANCE_MARKER)
    readiness = Readiness(binding.configuration_identity, binding.session_identity, binding.binding_identity,
                          claim.claim_identity, session.measurement_start_at + timedelta(seconds=readiness_offset))
    runtime.save_readiness(receipt=readiness, _issuance_marker=_ISSUANCE_MARKER)
    return session, binding, claim, readiness


@pytest.fixture
def context(tmp_path):
    env, main, repo, receipt, prestaged_connection, phase112 = prepared()
    authority = prestage(repo, receipt, phase112)
    lock, runtime_connection, runtime = _ready_archive(tmp_path)
    parents = add_claim(runtime)
    # Phase113 consumes durable records after the setup owner's lock is gone.
    lock.release()
    connection = sqlite3.connect(":memory:")
    schema.apply(connection)
    value = SimpleNamespace(envs=[env], main=main, repo=repo, receipt=receipt,
                            prestaged_connection=prestaged_connection, phase112=phase112,
                            authority=authority, runtime_connection=runtime_connection, runtime=runtime,
                            parents=parents, connection=connection, archive=Archive(connection=connection))
    try:
        yield value
    finally:
        for c in (connection, runtime_connection, prestaged_connection, main):
            c.close()
        for e in value.envs:
            for c in e.connections:
                c.close()


def arguments(ctx, *, parents=None, authority=None):
    session, _, claim, _ = parents or ctx.parents
    pair = authority or ctx.authority
    return dict(companion_archive=ctx.archive, runtime_archive=ctx.runtime,
                phase112_archive=ctx.phase112, phase109_repository=ctx.repo,
                session_identity=session.session_identity, expected_claim_identity=claim.claim_identity,
                phase112_manifest_identity=pair.manifest.identity,
                expected_availability_receipt_identity=pair.availability_receipt.identity)


def load(ctx, identity):
    return ctx.archive.load_binding(identity=identity, runtime_archive=ctx.runtime,
                                    phase112_archive=ctx.phase112, phase109_repository=ctx.repo)


def second_target(ctx):
    # This is a real second target in the frozen Kawasaki RaceList fixture.
    env = environment()
    ctx.envs.append(env)
    env.authority["external_race_id"] = "nar:20250101:21:2"
    env.transport.body = BODY
    _, result = acquire(env)
    ctx.main.execute("INSERT INTO races(id,race_date,organization,place,race_no,deba_table_url) "
                     "VALUES(2,'2025-01-01','NAR','Kawasaki',2,?)", (result.canonical_deba_url,))
    ctx.main.commit()
    source = persist(SQLiteNARIdentityCompleteEntryRepository(connection=ctx.main), env, result)
    receipt = map_publish(ctx.repo, env, source)
    return prestage(ctx.repo, receipt, ctx.phase112)


def test_exact_complete_authority_only_and_upstreams_read_only(context):
    ctx = context
    upstreams = (ctx.main, ctx.runtime_connection, ctx.prestaged_connection)
    before = [tuple(c.iterdump()) for c in upstreams]
    urls = tuple(ctx.envs[0].transport.urls)
    def readonly(action, _a, _b, _db, _trigger):
        return sqlite3.SQLITE_DENY if action in (sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE) else sqlite3.SQLITE_OK
    for c in upstreams:
        c.set_authorizer(readonly)
    try:
        value = issue(**arguments(ctx))
        assert load(ctx, value.identity) == value
        assert issue(**arguments(ctx)) == value
    finally:
        for c in upstreams:
            c.set_authorizer(None)
    assert [tuple(c.iterdump()) for c in upstreams] == before
    assert tuple(ctx.envs[0].transport.urls) == urls
    assert ctx.main.execute("SELECT count(*) FROM nar_identity_complete_denials").fetchone() == (3,)
    assert (value.internal_race_id, value.external_race_id) == (1, "nar:20250101:21:1")


@pytest.mark.parametrize("offset", [-1, 0, 1])
def test_readiness_before_or_equal_session_start_only(tmp_path, offset):
    lock, c, archive = _ready_archive(tmp_path)
    try:
        parents = add_claim(archive, readiness_offset=offset)
        assert archive.load_readiness_for_claim(claim_identity=parents[2].claim_identity) == parents[3]
        # The persisted late record is genuine but does not qualify downstream.
        from scripts.simulation.sqlite_nar_pre_c_production_claim_binding_archive import _upstream_binding
        from test_nar_pre_c_production_prestaged_manifest_issuance import prepared, issue as prestage
        env, main, repo, receipt, pc, phase112 = prepared()
        try:
            pair = prestage(repo, receipt, phase112)
            args = dict(runtime_archive=archive, phase112_archive=phase112, phase109_repository=repo,
                        session_identity=parents[0].session_identity, expected_claim_identity=parents[2].claim_identity,
                        phase112_manifest_identity=pair.manifest.identity,
                        expected_availability_receipt_identity=pair.availability_receipt.identity)
            if offset > 0:
                with pytest.raises(Error, match="readiness"):
                    _upstream_binding(**args)
            else:
                assert _upstream_binding(**args).campaign_readiness_receipt_identity == parents[3].receipt_identity
        finally:
            pc.close(); main.close()
            for ec in env.connections:
                ec.close()
    finally:
        c.close(); lock.release()


def test_same_claim_really_binds_two_distinct_valid_targets(context):
    first = issue(**arguments(context))
    second = issue(**arguments(context, authority=second_target(context)))
    assert first.external_race_id != second.external_race_id
    assert first.internal_race_id != second.internal_race_id
    for name in ("claim_identity", "runtime_binding_identity", "session_identity", "campaign_readiness_receipt_identity"):
        assert getattr(first, name) == getattr(second, name)
    assert load(context, first.identity) == first
    assert load(context, second.identity) == second
    assert context.connection.execute(f"SELECT count(*) FROM {schema.BINDINGS}").fetchone() == (2,)


@pytest.mark.parametrize("key", ["expected_claim_identity", "session_identity", "phase112_manifest_identity",
                                  "expected_availability_receipt_identity", "expected_external_race_id", "expected_prediction_cutoff"])
def test_expected_identity_or_target_mismatch_never_publishes(context, key):
    args = arguments(context)
    if key == "expected_prediction_cutoff":
        args[key] = context.receipt.prediction_cutoff + timedelta(seconds=1)
    elif key == "expected_external_race_id":
        args[key] = "nar:20250101:21:2"
    else:
        args[key] = args[key].split(":")[0] + ":" + "f" * 64
    with pytest.raises((Error, NARPreCProductionPrestagingError, RuntimeError)):
        issue(**args)
    assert context.connection.execute(f"SELECT count(*) FROM {schema.BINDINGS}").fetchone() == (0,)


@pytest.mark.parametrize("argument", ["entry_mapping", "horse_ids", "available_at", "utc_clock", "phase111_archive", "capability"])
def test_issuer_exposes_no_authoritative_mapping_clock_lineage_or_execution_input(context, argument):
    assert argument not in inspect.signature(issue).parameters
    with pytest.raises(TypeError):
        issue(**arguments(context), **{argument: object()})


def test_uncommitted_upstream_is_not_authority(context):
    context.main.execute("BEGIN")
    with pytest.raises(Error, match="committed upstream"):
        issue(**arguments(context))
    context.main.rollback()


def test_inert_phase112_manifest_does_not_qualify(context):
    from scripts.simulation.nar_pre_c_production_prestaged_manifest import manifest_from_phase109
    from scripts.simulation import nar_pre_c_production_prestaged_manifest_archive_migration as p112
    other = sqlite3.connect(":memory:")
    p112.apply(other)
    try:
        manifest = manifest_from_phase109(context.receipt)
        # An exact committed manifest still cannot provide an availability pair.
        from scripts.simulation.sqlite_nar_pre_c_production_prestaged_manifest_archive import SQLiteNARPreCProductionPrestagedManifestArchive
        inert = SQLiteNARPreCProductionPrestagedManifestArchive(connection=other)
        inert._stage_manifest(manifest)
        assert inert.load_manifest(identity=manifest.identity) == manifest
        assert inert.load_availability(manifest_identity=manifest.identity) is None
        args = arguments(context)
        args["phase112_archive"] = inert
        assert manifest.identity == args["phase112_manifest_identity"]
        with pytest.raises(NARPreCProductionPrestagingError, match="no availability authority"):
            issue(**args)
    finally:
        other.close()


def test_no_phase111_reload_or_transport_after_upstream_publication(context, monkeypatch):
    import requests
    def forbidden(*_args, **_kwargs):
        pytest.fail("Phase113 attempted provider/Phase111 work")
    monkeypatch.setattr(requests.sessions.Session, "request", forbidden)
    monkeypatch.setattr(type(context.envs[0].lineage), "load_receipt", forbidden)
    monkeypatch.setattr(type(context.envs[0].captures), "load_capture", forbidden)
    value = issue(**arguments(context))
    assert load(context, value.identity) == value


def test_readiness_all_scalar_ancestry_agreements_are_checked(context, monkeypatch):
    from dataclasses import replace
    original = context.parents[3]
    for name in ("configuration_identity", "session_identity", "binding_identity", "claim_identity"):
        identity = getattr(original, name)
        contradictory = replace(original, **{name: identity[:-64] + "f" * 64})
        monkeypatch.setattr(RuntimeArchive, "load_readiness_for_claim", lambda *_a, receipt=contradictory, **_k: receipt)
        with pytest.raises(Error, match="readiness"):
            issue(**arguments(context))
        assert context.connection.execute(f"SELECT count(*) FROM {schema.BINDINGS}").fetchone() == (0,)


def test_real_runtime_parent_payload_corruption_fails_closed(context):
    from scripts.simulation import nar_operational_timing_runtime_execution_archive_migration as runtime_schema
    from scripts.simulation import nar_operational_timing_v2_authority_archive_migration as v2_schema
    from scripts.simulation.sqlite_nar_operational_timing_observability_archive import TimingArchiveError
    c = context.runtime_connection
    for table, ddl in ((table, runtime_schema._DDL) for table in (
        runtime_schema.CLAIMS, runtime_schema.BINDINGS, runtime_schema.READINESS,
        runtime_schema.BUNDLES, runtime_schema.DEPENDENCIES, runtime_schema.TRANSPORTS)):
        row = c.execute(f"SELECT identity,payload_json FROM {table}").fetchone()
        guard = f"trg_{table}_no_update"
        c.execute(f"DROP TRIGGER {guard}")
        c.execute(f"UPDATE {table} SET payload_json='{{}}' WHERE identity=?", (row[0],))
        c.execute(ddl[guard]); c.commit()
        with pytest.raises((Error, TimingArchiveError, RuntimeError, ValueError)):
            issue(**arguments(context))
        assert context.connection.execute(f"SELECT count(*) FROM {schema.BINDINGS}").fetchone() == (0,)
        c.execute(f"DROP TRIGGER {guard}")
        c.execute(f"UPDATE {table} SET payload_json=? WHERE identity=?", (row[1], row[0]))
        c.execute(ddl[guard]); c.commit()
    # Real config/session/activation verification ancestry, not caller mocks.
    for table in (v2_schema.CONFIGS, v2_schema.SESSIONS, v2_schema.DECLARATIONS, v2_schema.VERIFICATIONS):
        guard = f"trg_{table}_no_update"
        row = c.execute(f"SELECT identity,payload_json FROM {table}").fetchone()
        c.execute(f"DROP TRIGGER {guard}")
        c.execute(f"UPDATE {table} SET payload_json='{{}}' WHERE identity=?", (row[0],))
        c.execute(v2_schema._DDL[guard]); c.commit()
        with pytest.raises((Error, TimingArchiveError, RuntimeError, ValueError)):
            issue(**arguments(context))
        assert context.connection.execute(f"SELECT count(*) FROM {schema.BINDINGS}").fetchone() == (0,)
        c.execute(f"DROP TRIGGER {guard}")
        c.execute(f"UPDATE {table} SET payload_json=? WHERE identity=?", (row[1], row[0]))
        c.execute(v2_schema._DDL[guard]); c.commit()
    assert issue(**arguments(context)) is not None
