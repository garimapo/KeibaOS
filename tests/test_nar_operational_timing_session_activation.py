"""Two-artifact activation proof and conservative controlled clock ordering."""

from dataclasses import FrozenInstanceError, replace
from datetime import timedelta, timezone
from inspect import signature
import sqlite3

import pytest

from scripts.simulation.nar_operational_timing_observability_archive_migration import (
    apply_nar_operational_timing_observability_archive_migrations as base_migrate,
)
from scripts.simulation.nar_operational_timing_activation_archive_migration import (
    apply_nar_operational_timing_activation_archive_migrations as activation_migrate,
)
from scripts.simulation.nar_operational_timing_session_activation import (
    NAROperationalTimingMeasurementSessionActivationDeclaration as Declaration,
    NAROperationalTimingMeasurementSessionActivationVerificationReceipt as Verification,
    NARTimingSessionActivationQualificationState as State,
    TimingActivationError, issue_nar_operational_timing_session_activation as issue,
    qualify_nar_operational_timing_session_activation as qualify,
)
from scripts.simulation.sqlite_nar_operational_timing_observability_archive import (
    SQLiteNAROperationalTimingObservabilityArchive,
)
from scripts.simulation.sqlite_nar_operational_timing_activation_archive import (
    SQLiteNAROperationalTimingActivationArchive,
)
from tests.test_nar_operational_timing_observability import START, session


def _archives():
    connection = sqlite3.connect(":memory:")
    base_migrate(connection)
    activation_migrate(connection)
    base = SQLiteNAROperationalTimingObservabilityArchive(connection=connection)
    activation = SQLiteNAROperationalTimingActivationArchive(connection=connection)
    campaign = session()
    base.save_configuration(configuration=campaign.configuration)
    base.save_session(session=campaign)
    return connection, base, activation, campaign


def test_canonical_immutable_content_and_no_caller_time_in_issuer():
    campaign = session()
    declaration = Declaration(campaign.session_identity, campaign.configuration.configuration_identity)
    assert Declaration.from_json(declaration.canonical_bytes().decode()) == declaration
    assert declaration.declaration_identity.endswith(declaration.declaration_sha256)
    with pytest.raises(FrozenInstanceError):
        declaration.session_identity = "x"
    receipt = Verification(declaration.declaration_identity, campaign.session_identity,
                           campaign.configuration.configuration_identity, START)
    assert Verification.from_json(receipt.canonical_bytes().decode()) == receipt
    assert receipt.verification_identity.endswith(receipt.verification_sha256)
    assert "activation_verified_at" not in signature(issue).parameters
    assert "activated_at" not in signature(Declaration).parameters
    with pytest.raises(TimingActivationError):
        Declaration("wrong", campaign.configuration.configuration_identity)
    with pytest.raises(TimingActivationError):
        Verification(declaration.declaration_identity, campaign.session_identity,
                     campaign.configuration.configuration_identity, START.replace(tzinfo=None))
    assert "result" not in declaration.payload()
    assert "payout" not in receipt.payload()


@pytest.mark.parametrize("offset,expected", [
    (-1, State.OFFICIAL_PREDECLARED_MEASUREMENT_SESSION),
    (0, State.OFFICIAL_PREDECLARED_MEASUREMENT_SESSION),
    (1, State.ACTIVATION_VERIFIED_AFTER_MEASUREMENT_START),
])
def test_before_equal_after_and_exact_retry(offset, expected):
    _, _, archive, campaign = _archives()
    samples = []
    def clock():
        samples.append(True)
        return START + timedelta(microseconds=offset)
    first = issue(session=campaign, archive=archive, utc_clock=clock)
    assert first.state is expected
    assert len(samples) == 1
    assert first.declaration is not None and first.verification_receipt is not None
    second = issue(session=campaign, archive=archive,
                   utc_clock=lambda: (_ for _ in ()).throw(AssertionError("retry sampled clock")))
    assert second == first
    assert qualify(session=campaign, archive=archive) == first


def test_reload_happens_before_clock_and_missing_chain_fails_closed():
    _, base, archive, campaign = _archives()
    assert qualify(session=campaign, archive=archive).state is State.ACTIVATION_PROVENANCE_UNAVAILABLE
    class OrderingArchive:
        def __getattr__(self, name):
            return getattr(archive, name)
        def load_declaration_for_session(self, *, session_identity):
            return archive.load_declaration_for_session(session_identity=session_identity)
    wrapped = OrderingArchive()
    def clock():
        declaration = archive.load_declaration_for_session(session_identity=campaign.session_identity)
        assert declaration is not None
        assert archive.load_verification_for_declaration(
            declaration_identity=declaration.declaration_identity) is None
        return START
    result = issue(session=campaign, archive=wrapped, utc_clock=clock)
    assert result.state is State.OFFICIAL_PREDECLARED_MEASUREMENT_SESSION
    altered = replace(campaign, measurement_end_at=campaign.measurement_end_at + timedelta(seconds=1))
    with pytest.raises(TimingActivationError, match="archived exactly"):
        qualify(session=altered, archive=archive)
    other = session(configuration=campaign.configuration,
                    measurement_start_at=START + timedelta(days=1),
                    measurement_end_at=START + timedelta(days=1, minutes=1))
    with pytest.raises(TimingActivationError):
        issue(session=other, archive=archive, utc_clock=lambda: START)


def test_declaration_only_retry_uses_current_clock_without_backdating():
    _, _, archive, campaign = _archives()
    class FailingReceiptArchive:
        def __getattr__(self, name):
            return getattr(archive, name)
        def save_verification_receipt(self, **kwargs):
            raise TimingActivationError("simulated receipt publication failure")
    with pytest.raises(TimingActivationError):
        issue(session=campaign, archive=FailingReceiptArchive(), utc_clock=lambda: START - timedelta(seconds=1))
    assert qualify(session=campaign, archive=archive).state is State.ACTIVATION_PROVENANCE_UNAVAILABLE
    later = issue(session=campaign, archive=archive, utc_clock=lambda: START + timedelta(seconds=1))
    assert later.state is State.ACTIVATION_VERIFIED_AFTER_MEASUREMENT_START
    assert later.verification_receipt.activation_verified_at == START + timedelta(seconds=1)


def test_failed_declaration_reload_never_samples_clock():
    _, _, archive, campaign = _archives()
    class MissingReloadArchive:
        def __init__(self):
            self.saved = False
        def __getattr__(self, name):
            return getattr(archive, name)
        def save_declaration(self, **kwargs):
            archive.save_declaration(**kwargs)
            self.saved = True
        def load_declaration_for_session(self, *, session_identity):
            if self.saved:
                return None
            return archive.load_declaration_for_session(session_identity=session_identity)
    with pytest.raises(TimingActivationError, match="reload"):
        issue(session=campaign, archive=MissingReloadArchive(),
              utc_clock=lambda: (_ for _ in ()).throw(AssertionError("clock sampled early")))
    assert qualify(session=campaign, archive=archive).state is State.ACTIVATION_PROVENANCE_UNAVAILABLE
