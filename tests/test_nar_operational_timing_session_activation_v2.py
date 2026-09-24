"""V2 activation proves archived predeclaration, not runtime authorization."""

from dataclasses import FrozenInstanceError
from datetime import timedelta
from inspect import signature
import sqlite3

import pytest

from scripts.simulation.nar_operational_timing_observability_archive_migration import (
    apply_nar_operational_timing_observability_archive_migrations as base_migrate,
)
from scripts.simulation.nar_operational_timing_activation_archive_migration import (
    apply_nar_operational_timing_activation_archive_migrations as activation_migrate,
)
from scripts.simulation.nar_operational_timing_v2_authority_archive_migration import (
    apply_nar_operational_timing_v2_authority_archive_migrations as v2_migrate,
)
from scripts.simulation.nar_operational_timing_session_activation_v2 import (
    NAROperationalTimingMeasurementSessionActivationDeclarationV2 as Declaration,
    NAROperationalTimingMeasurementSessionActivationVerificationReceiptV2 as Verification,
    NARTimingSessionActivationQualificationStateV2 as State,
    TimingActivationV2Error,
    issue_nar_operational_timing_session_activation_v2 as issue,
    qualify_nar_operational_timing_session_activation_v2 as qualify,
)
from scripts.simulation.sqlite_nar_operational_timing_v2_authority_archive import (
    SQLiteNAROperationalTimingV2AuthorityArchive as Archive,
)
from tests.test_nar_operational_timing_observability_v2 import START, session


def archive_session():
    connection = sqlite3.connect(":memory:")
    base_migrate(connection)
    activation_migrate(connection)
    v2_migrate(connection)
    archive = Archive(connection=connection)
    campaign = session()
    archive.save_configuration(configuration=campaign.configuration)
    archive.save_session(session=campaign)
    return connection, archive, campaign


def test_v2_activation_content_and_cross_version_rejection():
    campaign = session()
    declaration = Declaration(campaign.session_identity, campaign.configuration.configuration_identity)
    assert Declaration.from_json(declaration.canonical_bytes().decode()) == declaration
    assert declaration.declaration_identity.startswith("nar-operational-timing-activation-declaration-v2:")
    assert "activation_verified_at" not in declaration.payload()
    assert "activated_at" not in signature(issue).parameters
    receipt = Verification(declaration.declaration_identity, campaign.session_identity,
                           campaign.configuration.configuration_identity, START)
    assert Verification.from_json(receipt.canonical_bytes().decode()) == receipt
    assert receipt.verification_identity.startswith("nar-operational-timing-activation-verification-v2:")
    with pytest.raises(FrozenInstanceError):
        declaration.session_identity = "x"
    with pytest.raises(TimingActivationV2Error):
        Declaration("nar-operational-timing-session-v1:" + "a" * 64,
                    campaign.configuration.configuration_identity)
    with pytest.raises(TimingActivationV2Error):
        Declaration(campaign.session_identity, "nar-operational-timing-config-v1:" + "a" * 64)
    with pytest.raises(TimingActivationV2Error):
        Verification("nar-operational-timing-activation-declaration-v1:" + "a" * 64,
                     campaign.session_identity, campaign.configuration.configuration_identity, START)
    with pytest.raises(TimingActivationV2Error):
        Verification(declaration.declaration_identity, campaign.session_identity,
                     campaign.configuration.configuration_identity, START.replace(tzinfo=None))


@pytest.mark.parametrize("offset,state", [
    (-1, State.OFFICIAL_PREDECLARED_MEASUREMENT_SESSION),
    (0, State.OFFICIAL_PREDECLARED_MEASUREMENT_SESSION),
    (1, State.ACTIVATION_VERIFIED_AFTER_MEASUREMENT_START),
])
def test_before_equal_after_and_retry(offset, state):
    _, archive, campaign = archive_session()
    calls = []
    def clock():
        calls.append(True)
        declaration = archive.load_declaration_for_session(session_identity=campaign.session_identity)
        assert declaration is not None  # Exact archive reload precedes service clock.
        return START + timedelta(microseconds=offset)
    first = issue(session=campaign, archive=archive, utc_clock=clock)
    assert first.state is state and len(calls) == 1
    assert qualify(session=campaign, archive=archive) == first
    second = issue(session=campaign, archive=archive,
                   utc_clock=lambda: (_ for _ in ()).throw(AssertionError("clock resampled")))
    assert second == first


def test_missing_or_declaration_only_uses_current_clock():
    _, archive, campaign = archive_session()
    assert qualify(session=campaign, archive=archive).state is State.ACTIVATION_PROVENANCE_UNAVAILABLE
    declaration = Declaration(campaign.session_identity, campaign.configuration.configuration_identity)
    from scripts.simulation.nar_operational_timing_session_activation_v2 import _ISSUANCE_MARKER
    archive.save_declaration(declaration=declaration, _issuance_marker=_ISSUANCE_MARKER)
    assert qualify(session=campaign, archive=archive).state is State.ACTIVATION_PROVENANCE_UNAVAILABLE
    result = issue(session=campaign, archive=archive, utc_clock=lambda: START + timedelta(seconds=1))
    assert result.state is State.ACTIVATION_VERIFIED_AFTER_MEASUREMENT_START
    with pytest.raises(TimingActivationV2Error):
        qualify(session=session(measurement_end_at=START + timedelta(minutes=2)), archive=archive)
