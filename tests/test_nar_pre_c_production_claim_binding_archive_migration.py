"""Exact standalone topology, literal reserved names and immutable registry."""

import sqlite3

import pytest

from scripts.simulation import nar_pre_c_production_claim_binding_archive_migration as schema
from scripts.simulation.nar_pre_c_production_claim_binding import binding_row
from test_nar_pre_c_production_claim_binding import content


def test_absent_active_exact_registry_idempotent_installation():
    with sqlite3.connect(":memory:") as c:
        assert schema.phase113_schema_state(c) == schema.NOT_INSTALLED
        with pytest.raises(RuntimeError, match="NOT_INSTALLED"):
            schema.require_phase113_schema(c)
        schema.apply(c)
        original = tuple(c.iterdump())
        schema.apply(c)
        assert tuple(c.iterdump()) == original
        assert schema.phase113_schema_state(c) == schema.ACTIVE
        assert c.execute(f"SELECT * FROM {schema.REGISTRY}").fetchall() == [(1, schema.NAME)]
        assert c.execute(f"PRAGMA foreign_key_list({schema.BINDINGS})").fetchall() == []
        assert len(schema._objects(c)) == 6


@pytest.mark.parametrize("drift", ["sqliteXunreviewed", "sqliteAunreviewed", "missing_trigger", "unexpected_index", "partial"])
def test_exact_topology_corruption_is_not_absence_and_never_repaired(drift):
    with sqlite3.connect(":memory:") as c:
        schema.apply(c)
        if drift.startswith("sqlite"):
            c.execute(f"CREATE TABLE {drift}(id INTEGER)")
            assert c.execute("SELECT name FROM sqlite_schema WHERE name=?", (drift,)).fetchone() == (drift,)
        elif drift == "missing_trigger":
            c.execute(f"DROP TRIGGER {schema.BINDINGS}_no_update")
        elif drift == "unexpected_index":
            c.execute(f"CREATE INDEX unreviewed ON {schema.BINDINGS}(claim_identity)")
        else:
            c.execute(f"DROP TABLE {schema.BINDINGS}")
        c.commit()
        original = tuple(c.iterdump())
        assert schema.phase113_schema_state(c) == schema.INTEGRITY_FAILURE
        with pytest.raises(RuntimeError):
            schema.apply(c)
        assert tuple(c.iterdump()) == original


@pytest.mark.parametrize("table", [schema.REGISTRY, schema.BINDINGS])
@pytest.mark.parametrize("verb", ["UPDATE", "DELETE"])
def test_registry_and_binding_immutable_even_without_foreign_keys(table, verb):
    with sqlite3.connect(":memory:") as c:
        schema.apply(c)
        row = binding_row(content())
        c.execute(f"INSERT INTO {schema.BINDINGS} VALUES({','.join('?' for _ in row)})", row)
        c.commit()
        c.execute("PRAGMA foreign_keys=OFF")
        assert c.execute("PRAGMA foreign_keys").fetchone() == (0,)
        original = tuple(c.iterdump())
        sql = f"DELETE FROM {table}" if verb == "DELETE" else f"UPDATE {table} SET {'name=name' if table == schema.REGISTRY else 'identity=identity'}"
        with pytest.raises(sqlite3.IntegrityError, match="immutable Phase113"):
            c.execute(sql)
        c.rollback()
        assert tuple(c.iterdump()) == original
        assert schema.phase113_schema_state(c) == schema.ACTIVE


def test_campaign_columns_nonunique_and_only_reviewed_uniqueness_indexes_present():
    with sqlite3.connect(":memory:") as c:
        schema.apply(c)
        keys = [tuple(row[2] for row in c.execute(f"PRAGMA index_info('{index[1]}')"))
                for index in c.execute(f"PRAGMA index_list({schema.BINDINGS})") if index[2]]
        assert set(keys) == {
            ("identity",), ("phase112_manifest_identity",), ("phase112_availability_receipt_identity",),
            ("organization", "source_system", "external_race_id", "prediction_cutoff"),
            ("organization", "source_system", "internal_race_id", "prediction_cutoff")}


def test_schema_operational_lock_errors_propagate(tmp_path):
    path = tmp_path / "companion.sqlite"
    owner = sqlite3.connect(path)
    reader = sqlite3.connect(path, timeout=0)
    try:
        schema.apply(owner)
        owner.execute("BEGIN EXCLUSIVE")
        with pytest.raises(sqlite3.OperationalError, match="locked"):
            schema.phase113_schema_state(reader)
        with pytest.raises(sqlite3.OperationalError, match="locked"):
            schema.apply(reader)
    finally:
        owner.rollback(); owner.close(); reader.close()


def test_schema_install_failure_rolls_back_every_object():
    c = sqlite3.connect(":memory:")
    try:
        def deny_registry(action, table, _column, _db, _trigger):
            return sqlite3.SQLITE_DENY if action == sqlite3.SQLITE_INSERT and table == schema.REGISTRY else sqlite3.SQLITE_OK
        c.set_authorizer(deny_registry)
        with pytest.raises(sqlite3.DatabaseError):
            schema.apply(c)
        c.set_authorizer(None)
        assert schema.phase113_schema_state(c) == schema.NOT_INSTALLED
        assert not c.in_transaction
    finally:
        c.close()


def test_binding_projection_and_content_corruption_is_integrity_failure():
    with sqlite3.connect(":memory:") as c:
        schema.apply(c)
        row = binding_row(content())
        c.execute(f"INSERT INTO {schema.BINDINGS} VALUES({','.join('?' for _ in row)})", row)
        c.commit()
        guard = f"{schema.BINDINGS}_no_update"
        c.execute(f"DROP TRIGGER {guard}")
        c.execute(f"UPDATE {schema.BINDINGS} SET internal_race_id=999")
        c.execute(schema._DDL[guard]); c.commit()
        assert schema.phase113_schema_state(c) == schema.INTEGRITY_FAILURE
        with pytest.raises(RuntimeError, match="INTEGRITY_FAILURE"):
            schema.require_phase113_schema(c)
