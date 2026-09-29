from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta
import json
import sqlite3
import threading

import pytest

from test_nar_trusted_deba_acquisition import environment, T0
from scripts.simulation import nar_trusted_deba_acquisition as domain
from scripts.simulation.sqlite_nar_trusted_deba_acquisition_archive import (
    SQLiteNARTrustedDebaAcquisitionArchive, _PHASE111_TERMINAL_ISSUANCE_MARKER,
)
from scripts.simulation.repositories.errors import RepositoryConflictError, RepositoryDataIntegrityError, RepositoryValidationError


@pytest.fixture
def env():
    value = environment()
    yield value
    for connection in value.connections:
        connection.close()


def test_declaration_exact_roundtrip_idempotence_and_claim_exclusive(env):
    declaration = env.app.declare(**env.authority)
    env.lineage.save_declaration(declaration=declaration)
    claim = env.lineage.acquire_claim(declaration_id=declaration.identity, claimed_at=T0 + timedelta(seconds=11))
    assert env.lineage.load_claim(claim_id=claim.identity) == claim
    for claimed_at in (claim.claimed_at, claim.claimed_at + timedelta(seconds=1)):
        with pytest.raises(RepositoryConflictError):
            env.lineage.acquire_claim(declaration_id=declaration.identity, claimed_at=claimed_at)
    assert env.lineage.disposition(declaration_id=declaration.identity) == "UNKNOWN_SEND_OUTCOME"


def test_concurrent_independent_connections_can_claim_only_once(tmp_path):
    path = tmp_path / "lineage.sqlite"
    env = environment(sqlite3.connect(path))
    declaration = env.app.declare(**env.authority)
    for connection in env.connections:
        connection.close()
    barrier = threading.Barrier(2)
    def claimant():
        connection = sqlite3.connect(path, timeout=10)
        try:
            archive = SQLiteNARTrustedDebaAcquisitionArchive(connection=connection)
            barrier.wait(timeout=10)
            try:
                archive.acquire_claim(declaration_id=declaration.identity, claimed_at=T0 + timedelta(seconds=11))
                return "claimed"
            except RepositoryConflictError:
                return "denied"
        finally:
            connection.close()
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(claimant) for _ in range(2)]
        assert sorted(f.result(timeout=20) for f in futures) == ["claimed", "denied"]
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT count(*) FROM phase111_claims").fetchone() == (1,)


@pytest.mark.parametrize("operation", ["UPDATE", "DELETE"])
def test_domain_rows_are_append_only(env, operation):
    declaration = env.app.declare(**env.authority)
    result = env.app.acquire(declaration_id=declaration.identity, claimed_at=T0 + timedelta(seconds=11))
    for table in ("phase111_declarations", "phase111_claims", "phase111_receipts"):
        sql = f"UPDATE {table} SET payload='bad'" if operation == "UPDATE" else f"DELETE FROM {table}"
        with pytest.raises(sqlite3.IntegrityError):
            env.connections[2].execute(sql)
        env.connections[2].rollback()
    assert env.lineage.load_receipt(receipt_id=result.receipt_id) is not None


def test_corrupt_new_row_detected_without_repair(env):
    declaration = env.app.declare(**env.authority)
    identity = "phase111-NARProspectiveDebaAcquisitionDeclarationV1:" + "0" * 64
    env.connections[2].execute("INSERT INTO phase111_declarations VALUES(?,?)", (identity, declaration.canonical_bytes().decode()))
    env.connections[2].commit()
    with pytest.raises(RepositoryDataIntegrityError):
        env.lineage.load_declaration(declaration_id=identity)
    assert env.connections[2].execute("SELECT count(*) FROM phase111_declarations").fetchone() == (2,)


@pytest.mark.parametrize("mode", ["extra", "schema", "duplicate", "noncanonical"])
def test_canonical_loader_rejects_malformed_serialization(env, mode):
    declaration = env.app.declare(**env.authority)
    data = json.loads(declaration.canonical_bytes())
    if mode == "extra":
        data["content"]["official"] = True
    elif mode == "schema":
        data["schema_version"] = True
    elif mode == "duplicate":
        raw = declaration.canonical_bytes().replace(b'"schema_version":1', b'"schema_version":1,"schema_version":1')
        with pytest.raises(domain.AcquisitionIntegrityError):
            domain.record_from_bytes(type(declaration), raw)
        return
    raw = json.dumps(data, sort_keys=True).encode()
    with pytest.raises(domain.AcquisitionIntegrityError):
        domain.record_from_bytes(type(declaration), raw)


def test_active_transaction_write_and_wrong_type_rejected(env):
    declaration = env.app.declare(**env.authority)
    env.connections[2].execute("BEGIN")
    with pytest.raises(RepositoryValidationError):
        env.lineage.save_declaration(declaration=declaration)
    env.connections[2].rollback()
    with pytest.raises(RepositoryValidationError):
        SQLiteNARTrustedDebaAcquisitionArchive(connection=object())


def test_wrong_claim_window_and_parent_rejected(env):
    declaration = env.app.declare(**env.authority)
    with pytest.raises(domain.AcquisitionIntegrityError):
        env.lineage.acquire_claim(declaration_id=declaration.identity, claimed_at=T0)
    with pytest.raises(domain.AcquisitionIntegrityError):
        env.lineage.acquire_claim(declaration_id="phase111-NARProspectiveDebaAcquisitionDeclarationV1:" + "0" * 64,
                                  claimed_at=T0 + timedelta(seconds=11))


def test_conflicting_success_and_failure_terminal_rejected(env):
    declaration = env.app.declare(**env.authority)
    result = env.app.acquire(declaration_id=declaration.identity, claimed_at=T0 + timedelta(seconds=11))
    with pytest.raises(RepositoryConflictError):
        env.lineage._publish_failure(failure=domain.NARProspectiveDebaFailureV1(
            declaration.identity, result.claim_id, domain.FailureDisposition.TRANSPORT_FAILURE),
            _issuance_marker=_PHASE111_TERMINAL_ISSUANCE_MARKER)
    assert env.lineage.disposition(declaration_id=declaration.identity) == "RECEIPT_COMPLETE"


def test_terminal_failure_roundtrip_and_immutable(env):
    declaration = env.app.declare(**env.authority)
    claim = env.lineage.acquire_claim(declaration_id=declaration.identity, claimed_at=T0 + timedelta(seconds=11))
    failure = domain.NARProspectiveDebaFailureV1(declaration.identity, claim.identity, domain.FailureDisposition.READ_TIMEOUT)
    # Controlled fixture publication for repository round-trip/conflict checks.
    env.lineage._publish_failure(failure=failure, _issuance_marker=_PHASE111_TERMINAL_ISSUANCE_MARKER)
    assert env.lineage.load_failure(failure_id=failure.identity) == failure
    with pytest.raises(RepositoryConflictError):
        env.lineage._publish_failure(
            failure=replace(failure, disposition=domain.FailureDisposition.CONNECT_TIMEOUT),
            _issuance_marker=_PHASE111_TERMINAL_ISSUANCE_MARKER)
    with pytest.raises(sqlite3.IntegrityError):
        env.connections[2].execute("DELETE FROM phase111_failures")
    env.connections[2].rollback()


@pytest.mark.parametrize("marker", [None, object()])
def test_uncontrolled_failure_publication_rejected_before_storage(env, monkeypatch, marker):
    declaration = env.app.declare(**env.authority)
    claim = env.lineage.acquire_claim(declaration_id=declaration.identity, claimed_at=T0 + timedelta(seconds=11))
    failure = domain.NARProspectiveDebaFailureV1(
        declaration.identity, claim.identity, domain.FailureDisposition.READ_TIMEOUT)
    def forbidden_ancestry(record):
        pytest.fail("uncontrolled terminal must be rejected before ancestry validation")
    with monkeypatch.context() as guard:
        guard.setattr(env.lineage, "_validate_ancestry", forbidden_ancestry)
        with pytest.raises(RepositoryValidationError, match="controlled current-process issuance"):
            env.lineage._publish_failure(failure=failure, _issuance_marker=marker)
    assert env.lineage.load_failure(failure_id=failure.identity) is None
    assert env.lineage.disposition(declaration_id=declaration.identity) == "UNKNOWN_SEND_OUTCOME"
    assert env.transport.urls == []


@pytest.mark.parametrize("terminal", ["receipt", "failure"])
@pytest.mark.parametrize("marker", [None, object()])
def test_exact_duplicate_terminal_still_requires_controlled_marker(env, monkeypatch, terminal, marker):
    declaration = env.app.declare(**env.authority)
    if terminal == "receipt":
        result = env.app.acquire(declaration_id=declaration.identity, claimed_at=T0 + timedelta(seconds=11))
        record = env.lineage.load_receipt(receipt_id=result.receipt_id)
        publish = env.lineage._publish_receipt
        disposition = "RECEIPT_COMPLETE"
    else:
        claim = env.lineage.acquire_claim(declaration_id=declaration.identity, claimed_at=T0 + timedelta(seconds=11))
        record = domain.NARProspectiveDebaFailureV1(
            declaration.identity, claim.identity, domain.FailureDisposition.READ_TIMEOUT)
        publish = env.lineage._publish_failure
        # Explicitly controlled repository fixture, not an application bypass.
        publish(failure=record, _issuance_marker=_PHASE111_TERMINAL_ISSUANCE_MARKER)
        disposition = "SEND_TERMINAL_FAILURE"
    publish(**{terminal: record}, _issuance_marker=_PHASE111_TERMINAL_ISSUANCE_MARKER)
    def forbidden_ancestry(record):
        pytest.fail("duplicate content must not bypass the issuance gate")
    with monkeypatch.context() as guard:
        guard.setattr(env.lineage, "_validate_ancestry", forbidden_ancestry)
        with pytest.raises(RepositoryValidationError, match="controlled current-process issuance"):
            publish(**{terminal: record}, _issuance_marker=marker)
    assert env.lineage.disposition(declaration_id=declaration.identity) == disposition
