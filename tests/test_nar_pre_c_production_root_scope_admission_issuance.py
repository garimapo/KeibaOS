"""Real archived no-network parents; fixture clocks model prospective ordering."""

import ast
import inspect
import sqlite3
from datetime import timedelta, timezone
from types import SimpleNamespace

import pytest

from scripts.simulation import nar_pre_c_production_root_scope_admission_archive_migration as schema
from scripts.simulation.nar_pre_c_production_root_scope_admission import RootScopeAdmissionError as Error
from scripts.simulation.nar_pre_c_production_root_scope_admission_issuance import (
    NARPreCProductionRootScopeAdmissionIssuer as Issuer, _source, _policy_content,
)
from scripts.simulation.sqlite_nar_pre_c_production_root_scope_admission_archive import (
    SQLiteNARPreCProductionRootScopeAdmissionArchive as Archive,
)
from test_nar_pre_c_production_claim_binding_issuance import (
    context as parents_context, arguments, issue as bind, add_claim,
)
from test_nar_trusted_deba_acquisition import T0, environment, acquire
from test_nar_identity_complete_entry_source import BODY
from test_sqlite_nar_production_mapping_repository import persist, publish as map_publish
from test_nar_pre_c_production_prestaged_manifest_issuance import issue as prestage
from scripts.simulation.repositories.sqlite_nar_identity_complete_entry_repository import SQLiteNARIdentityCompleteEntryRepository

OFFSET = 2 * 60 * 60 * 1_000_000


class Clock:
    def __init__(self, connection, value):
        self.connection, self.value, self.samples = connection, value, 0

    def __call__(self):
        assert self.connection.in_transaction  # Second BEGIN IMMEDIATE holds serialization.
        self.samples += 1
        return self.value


@pytest.fixture
def context(parents_context):
    parents = parents_context
    binding = bind(**arguments(parents))
    c = sqlite3.connect(":memory:")
    schema.apply(c)
    archive = Archive(connection=c)
    clock = Clock(c, T0 + timedelta(minutes=2))
    issuer = Issuer(companion_archive=archive, lineage_archive=parents.envs[0].lineage,
                    daily_archive=parents.envs[0].targets, utc_clock=clock)
    value = SimpleNamespace(parents=parents, binding=binding, c=c, archive=archive,
                            clock=clock, issuer=issuer)
    yield value
    c.close()


def policy(ctx, **kwargs):
    return ctx.issuer.publish_policy(anchor_declaration_id=ctx.parents.receipt.phase111_declaration_id,
                                     offset_microseconds=OFFSET, **kwargs)


def upstreams(ctx):
    p = ctx.parents
    return dict(phase113_archive=p.archive, runtime_archive=p.runtime,
                phase112_archive=p.phase112, phase109_repository=p.repo)


def scope(ctx, approval, **kwargs):
    if ctx.clock.value == T0 + timedelta(minutes=2):
        ctx.clock.value = ctx.parents.authority.availability_receipt.available_at + timedelta(seconds=1)
    args = dict(policy_approval_identity=approval.identity, phase113_binding_identity=ctx.binding.identity,
                dataset_id="prospective/test-namespace", **upstreams(ctx))
    args.update(kwargs)
    return ctx.issuer.publish_scope(**args)


def load(ctx, pair):
    return ctx.archive.load_admission(availability_receipt_identity=pair[1].identity,
            expected_phase113_binding_identity=pair[0].phase113_binding_identity, **upstreams(ctx))


def fingerprints(ctx):
    p = ctx.parents
    return tuple(tuple(c.iterdump()) for c in (p.main, p.connection, p.runtime_connection,
                 p.prestaged_connection, *p.envs[0].connections))


def test_exact_two_stage_authority_and_no_upstream_mutation(context, monkeypatch):
    ctx = context
    before = fingerprints(ctx)
    import requests
    monkeypatch.setattr(requests.sessions.Session, "request", lambda *_a, **_k: pytest.fail("network"))
    # The clock sees only already committed, exact-reloaded content.
    trace = []
    ctx.c.set_trace_callback(trace.append)
    content, approval = policy(ctx)
    pair = scope(ctx, approval)
    assert ctx.clock.samples == 2
    assert content.target_set_content_sha256 == ctx.parents.envs[0].target_set.content_sha256
    assert len(__import__("json").loads(content.cutoff_plan_json)["decisions"]) == 33
    assert load(ctx, pair) == pair
    assert policy(ctx) == (content, approval)
    assert scope(ctx, approval) == pair
    assert ctx.clock.samples == 2
    assert fingerprints(ctx) == before
    assert sum(s == "BEGIN IMMEDIATE" for s in trace) == 8
    assert ctx.parents.main.execute("SELECT count(*) FROM nar_identity_complete_denials").fetchone() == (3,)


@pytest.mark.parametrize("seconds", [9, 10, 1200, 1201, 100000])
def test_whole_plan_temporal_boundary_no_historical_rescue(context, seconds):
    context.clock.value = T0 + timedelta(seconds=seconds)
    if 10 <= seconds <= 1200:
        _, approval = policy(context)
        assert approval.policy_approved_at == context.clock.value
    else:
        with pytest.raises(Error, match="approval window"):
            policy(context)
        assert context.c.execute(f"SELECT count(*) FROM {schema.POLICY_CONTENTS}").fetchone() == (1,)
        assert context.c.execute(f"SELECT count(*) FROM {schema.POLICY_APPROVALS}").fetchone() == (0,)
        context.clock.value = T0 + timedelta(days=20)
        with pytest.raises(Error):
            policy(context)
        assert context.c.execute(f"SELECT count(*) FROM {schema.POLICY_CONTENTS}").fetchone() == (1,)


@pytest.mark.parametrize("invalid", [None, T0.replace(tzinfo=None), T0.astimezone(timezone(timedelta(hours=9)))])
def test_invalid_clock_is_not_silently_normalized(context, invalid):
    context.clock.value = invalid
    with pytest.raises(Error):
        policy(context)
    assert not context.c.in_transaction
    assert context.c.execute(f"SELECT count(*) FROM {schema.POLICY_APPROVALS}").fetchone() == (0,)


@pytest.mark.parametrize("key", ["policy_approved_at", "issued_at", "target_set", "plan_json", "entry_mapping", "internal_race_id"])
def test_policy_api_rejects_caller_authority(context, key):
    assert key not in inspect.signature(Issuer.publish_policy).parameters
    with pytest.raises(TypeError):
        policy(context, **{key: object()})


@pytest.mark.parametrize("key", ["admitted_at", "available_at", "entry_mapping", "root", "capability", "claim"])
def test_scope_api_rejects_timestamp_or_execution(context, key):
    _, approval = policy(context)
    with pytest.raises(TypeError):
        scope(context, approval, **{key: object()})


def test_scope_after_cutoff_allowed_and_completed_timestamp_reused(context):
    _, approval = policy(context)
    context.clock.value = context.parents.authority.availability_receipt.available_at + timedelta(days=1)
    pair = scope(context, approval)
    assert pair[1].admitted_at > pair[0].prediction_information_cutoff
    context.clock.value = None
    assert scope(context, approval) == pair
    assert context.clock.samples == 2


def test_admission_floor_leaves_inert_scope(context):
    _, approval = policy(context)
    context.clock.value = T0 + timedelta(seconds=61)
    with pytest.raises(Error):
        scope(context, approval)
    assert context.c.execute(f"SELECT count(*) FROM {schema.SCOPES}").fetchone() == (1,)
    assert context.c.execute(f"SELECT count(*) FROM {schema.AVAILABILITY}").fetchone() == (0,)
    context.clock.value = context.parents.authority.availability_receipt.available_at + timedelta(seconds=1)
    pair = scope(context, approval)
    assert load(context, pair) == pair


def test_source_reconstruction_and_missing_or_forged_population_fail(context, monkeypatch):
    ctx = context
    p = ctx.parents.envs[0]
    for target in (None, p.monthly):
        with monkeypatch.context() as m:
            m.setattr(type(p.targets), "load_capture", lambda *_a, **_k: target)
            with pytest.raises((Error, RuntimeError, ValueError)):
                policy(ctx)
    assert ctx.clock.samples == 0
    assert ctx.c.execute(f"SELECT count(*) FROM {schema.POLICY_CONTENTS}").fetchone() == (0,)


def test_anchor_cutoff_must_equal_policy_plan(context):
    with pytest.raises(Error, match="anchor cutoff"):
        context.issuer.publish_policy(anchor_declaration_id=context.parents.receipt.phase111_declaration_id,
                                     offset_microseconds=OFFSET + 1)
    assert context.clock.samples == 0


def test_one_real_claim_two_target_bindings_same_dataset_same_complete_plan(context):
    ctx = context
    _, approval = policy(ctx)
    first = scope(ctx, approval)
    env = environment()
    ctx.parents.envs.append(env)
    env.authority["external_race_id"] = "nar:20250101:21:2"
    env.authority["prediction_information_cutoff"] = T0 + timedelta(minutes=50)
    env.transport.body = BODY
    _, result = acquire(env)  # Existing test-only fake transport; no real provider HTTP.
    c = ctx.parents.main
    c.execute("INSERT INTO races(id,race_date,organization,place,race_no,deba_table_url) "
              "VALUES(2,'2025-01-01','NAR','Kawasaki',2,?)", (result.canonical_deba_url,))
    c.commit()
    phase110 = persist(SQLiteNARIdentityCompleteEntryRepository(connection=c), env, result)
    mapping = map_publish(ctx.parents.repo, env, phase110)
    pair112 = prestage(ctx.parents.repo, mapping, ctx.parents.phase112)
    second_binding = bind(**arguments(ctx.parents, authority=pair112))
    # Distinct declaration, SAME archived complete source population; publication
    # must find the target declaration in the injected lineage archive.
    declaration = env.lineage.load_declaration(declaration_id=mapping.phase111_declaration_id)
    ctx.parents.envs[0].lineage.save_declaration(declaration=declaration)
    ctx.clock.value = pair112.availability_receipt.available_at + timedelta(seconds=1)
    second = scope(ctx, approval, phase113_binding_identity=second_binding.identity)
    assert first[0].external_race_id != second[0].external_race_id
    assert first[0].internal_race_id != second[0].internal_race_id
    assert first[0].cutoff_plan_json == second[0].cutoff_plan_json
    assert first[0].dataset_id == second[0].dataset_id
    for field in ("claim_identity", "session_identity", "runtime_binding_identity", "campaign_readiness_receipt_identity"):
        assert getattr(ctx.binding, field) == getattr(second_binding, field)
    assert load(ctx, first) == first and load(ctx, second) == second
    assert ctx.c.execute(f"SELECT count(*) FROM {schema.SCOPES}").fetchone() == (2,)


def test_ordinary_load_never_reopens_original_source_archives(context, monkeypatch):
    _, approval = policy(context)
    pair = scope(context, approval)
    for parent, method in ((context.parents.envs[0].lineage, "load_declaration"),
                           (context.parents.envs[0].targets, "load_capture")):
        monkeypatch.setattr(type(parent), method, lambda *_a, **_k: pytest.fail("ordinary source reopen"))
    assert load(context, pair) == pair
    assert "lineage_archive" not in inspect.signature(Archive.load_admission).parameters
    assert "daily_archive" not in inspect.signature(Archive.load_admission).parameters


@pytest.mark.parametrize("store", ["main", "connection", "runtime_connection", "prestaged_connection"])
def test_active_upstream_transaction_is_not_authority(context, store):
    _, approval = policy(context)
    c = getattr(context.parents, store)
    c.execute("BEGIN")
    try:
        with pytest.raises((Error, ValueError), match="committed"):
            scope(context, approval)
    finally:
        c.rollback()


def test_static_import_and_api_boundary():
    from pathlib import Path
    paths = sorted(Path("scripts/simulation").glob("*production_root_scope_admission*.py"))
    assert len(paths) == 4
    forbidden = {"requests", "urllib", "httpx", "aiohttp", "bs4"}
    for path in paths:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
        for node in imports:
            modules = [node.module] if isinstance(node, ast.ImportFrom) else [a.name for a in node.names]
            assert not any(m and m.split(".")[0] in forbidden for m in modules)
        for forbidden_call in ("sqlite3.connect", "datetime.now", "utcnow", "lastrowid", "INSERT OR REPLACE",
                               "INSERT INTO races", "INSERT INTO horses", "HorseParser", "capture_response(", "fetch_deba("):
            assert forbidden_call not in source


def test_content_committed_exact_reload_and_source_proof_before_each_clock(context, monkeypatch):
    ctx = context
    reloaded = set()
    original = Archive._load
    def observed(self, table, record_identity):
        value = original(self, table, record_identity)
        if value is not None and not self._connection.in_transaction:
            reloaded.add(table)
        return value
    monkeypatch.setattr(Archive, "_load", observed)
    samples = []
    def controlled_clock():
        assert ctx.c.in_transaction
        if not samples:
            assert schema.POLICY_CONTENTS in reloaded
            assert ctx.c.execute(f"SELECT count(*) FROM {schema.POLICY_APPROVALS}").fetchone() == (0,)
            samples.append("policy")
            return T0 + timedelta(minutes=2)
        assert schema.SCOPES in reloaded
        assert ctx.c.execute(f"SELECT count(*) FROM {schema.AVAILABILITY}").fetchone() == (0,)
        samples.append("scope")
        return ctx.parents.authority.availability_receipt.available_at + timedelta(seconds=1)
    ctx.issuer._clock = controlled_clock
    content, approval = policy(ctx)
    pair = scope(ctx, approval)
    assert policy(ctx) == (content, approval)
    assert scope(ctx, approval) == pair
    assert samples == ["policy", "scope"]


def test_missing_policy_binding_or_expected_handoff_fails(context):
    from scripts.simulation.nar_pre_c_production_root_scope_admission import POLICY_APPROVAL_PREFIX, BINDING_PREFIX
    with pytest.raises(Error, match="approval"):
        context.archive.load_policy(approval_identity=POLICY_APPROVAL_PREFIX + "f" * 64)
    _, approval = policy(context)
    with pytest.raises(Error, match="Phase113"):
        scope(context, approval, phase113_binding_identity=BINDING_PREFIX + "f" * 64)
    pair = scope(context, approval)
    with pytest.raises(Error, match="expected Phase113"):
        context.archive.load_admission(availability_receipt_identity=pair[1].identity,
            expected_phase113_binding_identity=BINDING_PREFIX + "f" * 64, **upstreams(context))


@pytest.mark.parametrize("store", ["lineage", "targets"])
def test_active_source_transaction_rejected(context, store):
    c = getattr(context.parents.envs[0], store)._connection
    c.execute("BEGIN")
    try:
        with pytest.raises(Error, match="committed idle"):
            policy(context)
    finally:
        c.rollback()
    assert context.clock.samples == 0
