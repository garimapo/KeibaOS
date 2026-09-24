"""V2 archive exact roundtrip, immutable conflicts, and controlled issuance."""

from datetime import timedelta
import sqlite3

import pytest

from scripts.simulation import nar_operational_timing_observability_archive_migration as base
from scripts.simulation import nar_operational_timing_activation_archive_migration as activation
from scripts.simulation import nar_operational_timing_v2_authority_archive_migration as v2
from scripts.simulation.nar_operational_timing_session_activation_v2 import (
    NAROperationalTimingMeasurementSessionActivationDeclarationV2 as Declaration,
    issue_nar_operational_timing_session_activation_v2 as issue,
)
from scripts.simulation.sqlite_nar_operational_timing_observability_archive import TimingArchiveConflict, TimingArchiveError
from scripts.simulation.sqlite_nar_operational_timing_v2_authority_archive import SQLiteNAROperationalTimingV2AuthorityArchive as Archive
from tests.test_nar_operational_timing_observability_v2 import START, config, session


def prepared():
    connection = sqlite3.connect(":memory:")
    base.apply_nar_operational_timing_observability_archive_migrations(connection)
    activation.apply_nar_operational_timing_activation_archive_migrations(connection)
    v2.apply_nar_operational_timing_v2_authority_archive_migrations(connection)
    archive = Archive(connection=connection)
    campaign = session()
    archive.save_configuration(configuration=campaign.configuration)
    archive.save_session(session=campaign)
    return connection, archive, campaign


def test_constructor_never_migrates_and_exact_chain_roundtrips():
    empty = sqlite3.connect(":memory:")
    with pytest.raises(RuntimeError):
        Archive(connection=empty)
    assert base._objects(empty) == {}
    connection, archive, campaign = prepared()
    assert archive.load_configuration(configuration_identity=campaign.configuration.configuration_identity) == campaign.configuration
    assert archive.load_session(session_identity=campaign.session_identity) == campaign
    first = issue(session=campaign, archive=archive, utc_clock=lambda: START - timedelta(seconds=1))
    assert archive.load_declaration_for_session(session_identity=campaign.session_identity) == first.declaration
    assert archive.load_verification_for_declaration(declaration_identity=first.declaration.declaration_identity) == first.verification_receipt
    archive.save_configuration(configuration=campaign.configuration)
    archive.save_session(session=campaign)
    assert issue(session=campaign, archive=archive,
                 utc_clock=lambda: (_ for _ in ()).throw(AssertionError("clock resampled"))) == first
    assert connection.execute(f"SELECT count(*) FROM {v2.DECLARATIONS}").fetchone() == (1,)
    assert connection.execute(f"SELECT count(*) FROM {v2.VERIFICATIONS}").fetchone() == (1,)


def test_missing_parent_conflict_and_controlled_publication():
    _, archive, campaign = prepared()
    other = session(configuration=config(software_commit_sha="b" * 40))
    with pytest.raises(TimingArchiveError):
        archive.save_session(session=other)
    declaration = Declaration(campaign.session_identity, campaign.configuration.configuration_identity)
    with pytest.raises(TimingArchiveError):
        archive.save_declaration(declaration=declaration)
    with pytest.raises(TimingArchiveError):
        archive.save_configuration(configuration="wrong")
    with pytest.raises(TimingArchiveConflict):
        archive._save(table=v2.CONFIGS, natural_column="identity",
                      natural_identity=campaign.configuration.configuration_identity,
                      row=(campaign.configuration.configuration_identity, "{}"),
                      columns="identity,payload_json")


def test_corruption_is_detected_on_exact_reload():
    connection, archive, campaign = prepared()
    # Simulate external corruption while restoring the exact schema before reload.
    connection.execute(f"DROP TRIGGER trg_{v2.CONFIGS}_no_update")
    connection.execute(f"UPDATE {v2.CONFIGS} SET payload_json='{{}}'")
    connection.execute(v2._DDL[f"trg_{v2.CONFIGS}_no_update"])
    connection.commit()
    with pytest.raises(TimingArchiveError, match="corrupt"):
        archive.load_configuration(configuration_identity=campaign.configuration.configuration_identity)
