from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3

import pytest

from scripts.simulation import nar_operational_timing_observability_archive_migration as base
from scripts.simulation import nar_operational_timing_activation_archive_migration as activation
from scripts.simulation import nar_operational_timing_v2_authority_archive_migration as v2
from scripts.simulation import nar_operational_timing_runtime_execution_archive_migration as runtime
from scripts.simulation.nar_operational_timing_archive_bootstrap import bootstrap_nar_operational_timing_runtime_archive
from scripts.simulation.nar_operational_timing_campaign_lock import NAROperationalTimingCampaignLock
from scripts.simulation.nar_operational_timing_observability import NARHTTPTransportProfile
from scripts.simulation.nar_operational_timing_observability_v2 import (
    NAROperationalTimingMeasurementConfigurationV2 as Configuration,
    NAROperationalTimingMeasurementSessionV2 as Session,
    NAROperationalTimingStageV2 as Stage,
)
from scripts.simulation.nar_operational_timing_session_activation_v2 import issue_nar_operational_timing_session_activation_v2
from scripts.simulation.nar_operational_timing_runtime_source_provenance import (
    _git_manifest,
)
from scripts.simulation.nar_operational_timing_runtime_profile import (
    derive_runtime_dependency_profile, derive_static_runtime_transport_profile,
)
from scripts.simulation.nar_operational_timing_runtime_execution import (
    NAROperationalTimingRuntimeBinding as Binding,
    NAROperationalTimingCampaignExecutionClaim as Claim,
    NAROperationalTimingCampaignReadinessVerificationReceipt as Readiness,
)
from scripts.simulation.sqlite_nar_operational_timing_runtime_execution_archive import (
    SQLiteNAROperationalTimingRuntimeExecutionArchive as Archive, _ISSUANCE_MARKER,
)
from scripts.simulation.sqlite_nar_operational_timing_observability_archive import (
    SQLiteNAROperationalTimingObservabilityArchive,
)
from scripts.simulation.sqlite_nar_operational_timing_activation_archive import (
    SQLiteNAROperationalTimingActivationArchive,
)


ROOT = Path(__file__).resolve().parents[1]
COMMIT = "1236f1e0db84ce6025d07c052abbb3c7348aab3e"
START = datetime(2030, 1, 1, tzinfo=timezone.utc)


def _open(path: Path):
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def _config():
    profile = derive_static_runtime_transport_profile()
    return Configuration(COMMIT, (Stage.SNAPSHOT_CONSTRUCTION,),
                         tuple(NARHTTPTransportProfile(x.kind, x.connect_timeout_microseconds,
                                                       x.read_timeout_microseconds)
                               for x in profile.descriptors))


def _ready_archive(tmp_path):
    path = tmp_path / "timing.sqlite"
    lock = NAROperationalTimingCampaignLock(archive_path=path)
    lock.acquire()
    connection = _open(path)
    bootstrap_nar_operational_timing_runtime_archive(connection=connection, campaign_lock=lock)
    return lock, connection, Archive(connection=connection)


def _ancestry(archive):
    config = _config()
    session = Session(config, START, START + timedelta(hours=1))
    archive.v2.save_configuration(configuration=config)
    archive.v2.save_session(session=session)
    activation_result = issue_nar_operational_timing_session_activation_v2(
        session=session, archive=archive.v2, utc_clock=lambda: START - timedelta(hours=1))
    bundle, _ = _git_manifest(ROOT, COMMIT)
    dependency = derive_runtime_dependency_profile()
    transport = derive_static_runtime_transport_profile()
    archive.save_bundle(bundle=bundle)
    archive.save_dependency_profile(profile=dependency)
    archive.save_transport_profile(profile=transport)
    binding = Binding(config.configuration_identity, session.session_identity,
                      activation_result.declaration.declaration_identity,
                      activation_result.verification_receipt.verification_identity,
                      bundle.bundle_identity, dependency.profile_identity, transport.profile_identity,
                      "nar-operational-timing-lock-scope-v1:" + "a" * 64)
    return session, bundle, dependency, transport, binding


@pytest.mark.parametrize("state", [0, 1, 2, 3, 4])
def test_bootstrap_exact_known_states_and_historical_strict_gates(tmp_path, state):
    path = tmp_path / "timing.sqlite"
    lock = NAROperationalTimingCampaignLock(archive_path=path)
    with lock:
        connection = _open(path)
        if state >= 1:
            base.apply_nar_operational_timing_observability_archive_migrations(connection)
        if state >= 2:
            activation.apply_nar_operational_timing_activation_archive_migrations(connection)
        if state >= 3:
            v2.apply_nar_operational_timing_v2_authority_archive_migrations(connection)
        if state >= 4:
            runtime.apply_nar_operational_timing_runtime_execution_archive_migrations(connection)
        bootstrap_nar_operational_timing_runtime_archive(connection=connection, campaign_lock=lock)
        runtime.require_nar_operational_timing_runtime_execution_archive_schema(connection)
        bootstrap_nar_operational_timing_runtime_archive(connection=connection, campaign_lock=lock)
        assert SQLiteNAROperationalTimingObservabilityArchive(
            connection=connection).load_configuration(configuration_identity="missing") is None
        assert SQLiteNAROperationalTimingActivationArchive(
            connection=connection).load_session(session_identity="missing") is None
        assert Archive(connection=connection).v2.load_session(session_identity="missing") is None
        with pytest.raises(RuntimeError):
            base.require_nar_operational_timing_observability_archive_schema(connection)
        with pytest.raises(RuntimeError):
            v2.require_nar_operational_timing_v2_authority_archive_schema(connection)
        assert connection.execute(f"SELECT COUNT(*) FROM {runtime.CLAIMS}").fetchone()[0] == 0
        connection.close()


def test_runtime_parent_archive_one_claim_and_readiness(tmp_path):
    lock, connection, archive = _ready_archive(tmp_path)
    try:
        session, bundle, dependency, transport, binding = _ancestry(archive)
        archive.save_binding(binding=binding, _issuance_marker=_ISSUANCE_MARKER)
        assert archive.load_binding(binding_identity=binding.binding_identity) == binding
        assert archive.load_bundle(bundle_identity=bundle.bundle_identity) == bundle
        assert archive.load_dependency_profile(profile_identity=dependency.profile_identity) == dependency
        assert archive.load_transport_profile(profile_identity=transport.profile_identity) == transport
        claim = Claim(binding.configuration_identity, binding.session_identity,
                      binding.declaration_identity, binding.verification_identity,
                      binding.binding_identity, binding.bundle_identity, binding.lock_scope_identity)
        assert archive.save_claim(claim=claim, _issuance_marker=_ISSUANCE_MARKER) is True
        assert archive.save_claim(claim=claim, _issuance_marker=_ISSUANCE_MARKER) is False
        assert archive.load_claim_for_session(session_identity=session.session_identity) == claim
        receipt = Readiness(binding.configuration_identity, session.session_identity,
                            binding.binding_identity, claim.claim_identity, START)
        archive.save_readiness(receipt=receipt, _issuance_marker=_ISSUANCE_MARKER)
        assert archive.load_readiness_for_claim(claim_identity=claim.claim_identity) == receipt
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(f"UPDATE {runtime.CLAIMS} SET identity='x'")
        connection.rollback()
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(f"DELETE FROM {runtime.CLAIMS}")
        connection.rollback()
        assert connection.execute(f"SELECT COUNT(*) FROM {runtime.CLAIMS}").fetchone()[0] == 1
    finally:
        connection.close()
        lock.release()


def test_partial_unknown_schema_rejected_and_constructor_does_not_migrate(tmp_path):
    path = tmp_path / "timing.sqlite"
    connection = _open(path)
    with pytest.raises(RuntimeError):
        Archive(connection=connection)
    connection.close()
    lock, connection, archive = _ready_archive(tmp_path)
    try:
        connection.execute("CREATE TABLE unexpected_extra(x INTEGER)")
        connection.commit()
        with pytest.raises(RuntimeError):
            runtime.require_nar_operational_timing_runtime_execution_archive_schema(connection)
        with pytest.raises(RuntimeError):
            bootstrap_nar_operational_timing_runtime_archive(connection=connection, campaign_lock=lock)
    finally:
        connection.close()
        lock.release()
