"""Exact standalone topology and immutable local projections, including FK OFF."""

import sqlite3

import pytest

from scripts.simulation import nar_pre_c_production_root_scope_admission_archive_migration as schema
from scripts.simulation.nar_pre_c_production_root_scope_admission import RootScopeAdmissionError
from test_nar_pre_c_production_root_scope_admission_issuance import context, parents_context, policy, scope


def test_empty_active_and_legal_sqlite_wildcard_object():
    c = sqlite3.connect(":memory:")
    try:
        assert schema.phase114_schema_state(c) == schema.NOT_INSTALLED
        schema.apply(c)
        assert schema.phase114_schema_state(c) == schema.ACTIVE
        schema.apply(c)
        assert schema._objects(c) == schema._expected()
        c.execute("CREATE TABLE sqliteXunreviewed(value TEXT)")
        assert c.execute("SELECT name FROM sqlite_schema WHERE name='sqliteXunreviewed'").fetchone() == ("sqliteXunreviewed",)
        assert schema.phase114_schema_state(c) == schema.INTEGRITY_FAILURE
        with pytest.raises(RuntimeError):
            schema.apply(c)
    finally:
        c.close()


@pytest.mark.parametrize("name", list(schema._DDL))
def test_every_missing_object_is_corrupt_not_absent(name):
    c = sqlite3.connect(":memory:")
    try:
        schema.apply(c)
        kind = schema._expected()[name][0]
        c.execute(f"DROP {kind.upper()} {name}")
        c.commit()
        assert schema.phase114_schema_state(c) == schema.INTEGRITY_FAILURE
    finally:
        c.close()


@pytest.mark.parametrize("table", [schema.REGISTRY, *schema.RECORDS])
@pytest.mark.parametrize("verb", ["UPDATE", "DELETE"])
def test_all_immutable_update_delete_guards_fk_off(context, table, verb):
    _, approval = policy(context)
    scope(context, approval)
    c = context.c
    c.execute("PRAGMA foreign_keys=OFF")
    assert c.execute("PRAGMA foreign_keys").fetchone() == (0,)
    before = list(c.execute(f"SELECT * FROM {table}"))
    sql = f"DELETE FROM {table}" if verb == "DELETE" else f"UPDATE {table} SET " + ("name=name" if table == schema.REGISTRY else "payload_json=payload_json")
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        c.execute(sql)
    c.rollback()
    assert list(c.execute(f"SELECT * FROM {table}")) == before
    assert schema.phase114_schema_state(c) == schema.ACTIVE


@pytest.mark.parametrize("table", list(schema.RECORDS))
def test_corrupt_projection_detected_after_guard_restored(context, table):
    _, approval = policy(context)
    scope(context, approval)
    c = context.c
    guard = table + "_no_update"
    c.execute(f"DROP TRIGGER {guard}")
    c.execute(f"UPDATE {table} SET payload_json='{{}}'")
    c.execute(schema._DDL[guard])
    c.commit()
    assert schema.phase114_schema_state(c) == schema.INTEGRITY_FAILURE


def test_no_global_claim_or_dataset_cardinality():
    ddl = "\n".join(schema._DDL.values())
    for name in ("claim_identity", "session_identity", "runtime_binding_identity", "readiness_identity", "dataset_id"):
        assert name not in ddl
    assert schema.VERSION == 1
    assert schema.NAME == "v001_nar_pre_c_production_root_scope_admission_companion"
    assert "v020" not in ddl


def test_unexpected_operational_errors_propagate():
    class Locked(sqlite3.Connection):
        def execute(self, *_a, **_k):
            raise sqlite3.OperationalError("database is locked")
    c = sqlite3.connect(":memory:", factory=Locked)
    try:
        with pytest.raises(sqlite3.OperationalError, match="locked"):
            schema.phase114_schema_state(c)
    finally:
        c.close()
