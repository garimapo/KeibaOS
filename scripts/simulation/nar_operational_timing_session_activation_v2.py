"""Controlled two-artifact activation of an archived V2 measurement session."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from hashlib import sha256
import re
from typing import Callable, Protocol

from scripts.simulation.nar_operational_timing_observability import (
    _json_bytes, _parse_time, _read_json, _time, _utc,
)
from scripts.simulation.nar_operational_timing_observability_v2 import (
    NAROperationalTimingMeasurementConfigurationV2 as Configuration,
    NAROperationalTimingMeasurementSessionV2 as Session,
)


class TimingActivationV2Error(ValueError):
    """Exact archived V2 activation ancestry is unavailable or contradictory."""


_ISSUANCE_MARKER = object()  # Trusted API discipline, not cryptographic authority.
_SESSION_ID = re.compile(r"nar-operational-timing-session-v2:[0-9a-f]{64}\Z")
_CONFIG_ID = re.compile(r"nar-operational-timing-config-v2:[0-9a-f]{64}\Z")
_DECLARATION_ID = re.compile(r"nar-operational-timing-activation-declaration-v2:[0-9a-f]{64}\Z")


class NARTimingActivationDeclarationSemanticV2(StrEnum):
    INTENDED_PROSPECTIVE_MEASUREMENT_CAMPAIGN = "INTENDED_PROSPECTIVE_MEASUREMENT_CAMPAIGN"


class NARTimingActivationVerificationSemanticV2(StrEnum):
    DECLARATION_COMMITTED_AND_EXACT_RELOAD_VERIFIED = "DECLARATION_COMMITTED_AND_EXACT_RELOAD_VERIFIED"


@dataclass(frozen=True, slots=True)
class NAROperationalTimingMeasurementSessionActivationDeclarationV2:
    session_identity: str
    measurement_configuration_identity: str
    semantic: NARTimingActivationDeclarationSemanticV2 = NARTimingActivationDeclarationSemanticV2.INTENDED_PROSPECTIVE_MEASUREMENT_CAMPAIGN
    schema_version: int = 2
    declaration_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if (type(self.session_identity) is not str or _SESSION_ID.fullmatch(self.session_identity) is None
                or type(self.measurement_configuration_identity) is not str
                or _CONFIG_ID.fullmatch(self.measurement_configuration_identity) is None
                or type(self.semantic) is not NARTimingActivationDeclarationSemanticV2
                or type(self.schema_version) is not int or self.schema_version != 2):
            raise TimingActivationV2Error("V2 declaration identity, semantic, or version is invalid")
        object.__setattr__(self, "declaration_sha256", sha256(self.canonical_bytes()).hexdigest())

    @property
    def declaration_identity(self) -> str:
        return "nar-operational-timing-activation-declaration-v2:" + self.declaration_sha256

    def payload(self) -> dict[str, object]:
        return {"schema_version": self.schema_version, "session_identity": self.session_identity,
                "measurement_configuration_identity": self.measurement_configuration_identity,
                "semantic": self.semantic.value}

    def canonical_bytes(self) -> bytes:
        return _json_bytes(self.payload())

    @classmethod
    def from_json(cls, value: str) -> NAROperationalTimingMeasurementSessionActivationDeclarationV2:
        p = _read_json(value)
        result = cls(p["session_identity"], p["measurement_configuration_identity"],
                     NARTimingActivationDeclarationSemanticV2(p["semantic"]), p["schema_version"])
        if result.canonical_bytes() != value.encode("utf-8"):
            raise TimingActivationV2Error("V2 declaration JSON is not canonical")
        return result


@dataclass(frozen=True, slots=True)
class NAROperationalTimingMeasurementSessionActivationVerificationReceiptV2:
    declaration_identity: str
    session_identity: str
    measurement_configuration_identity: str
    activation_verified_at: datetime
    semantic: NARTimingActivationVerificationSemanticV2 = NARTimingActivationVerificationSemanticV2.DECLARATION_COMMITTED_AND_EXACT_RELOAD_VERIFIED
    schema_version: int = 2
    verification_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if (type(self.declaration_identity) is not str or _DECLARATION_ID.fullmatch(self.declaration_identity) is None
                or type(self.session_identity) is not str or _SESSION_ID.fullmatch(self.session_identity) is None
                or type(self.measurement_configuration_identity) is not str
                or _CONFIG_ID.fullmatch(self.measurement_configuration_identity) is None
                or type(self.semantic) is not NARTimingActivationVerificationSemanticV2
                or type(self.schema_version) is not int or self.schema_version != 2):
            raise TimingActivationV2Error("V2 verification identity, semantic, or version is invalid")
        try:
            verified = _utc(self.activation_verified_at)
        except (TypeError, ValueError, OverflowError) as error:
            raise TimingActivationV2Error("V2 verification requires aware UTC-compatible time") from error
        object.__setattr__(self, "activation_verified_at", verified)
        object.__setattr__(self, "verification_sha256", sha256(self.canonical_bytes()).hexdigest())

    @property
    def verification_identity(self) -> str:
        return "nar-operational-timing-activation-verification-v2:" + self.verification_sha256

    def payload(self) -> dict[str, object]:
        return {"schema_version": self.schema_version, "declaration_identity": self.declaration_identity,
                "session_identity": self.session_identity,
                "measurement_configuration_identity": self.measurement_configuration_identity,
                "semantic": self.semantic.value, "activation_verified_at": _time(self.activation_verified_at)}

    def canonical_bytes(self) -> bytes:
        return _json_bytes(self.payload())

    @classmethod
    def from_json(cls, value: str) -> NAROperationalTimingMeasurementSessionActivationVerificationReceiptV2:
        p = _read_json(value)
        result = cls(p["declaration_identity"], p["session_identity"],
                     p["measurement_configuration_identity"], _parse_time(p["activation_verified_at"]),
                     NARTimingActivationVerificationSemanticV2(p["semantic"]), p["schema_version"])
        if result.canonical_bytes() != value.encode("utf-8"):
            raise TimingActivationV2Error("V2 verification JSON is not canonical")
        return result


class NARTimingSessionActivationQualificationStateV2(StrEnum):
    OFFICIAL_PREDECLARED_MEASUREMENT_SESSION = "OFFICIAL_PREDECLARED_MEASUREMENT_SESSION"
    ACTIVATION_VERIFIED_AFTER_MEASUREMENT_START = "ACTIVATION_VERIFIED_AFTER_MEASUREMENT_START"
    ACTIVATION_PROVENANCE_UNAVAILABLE = "ACTIVATION_PROVENANCE_UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class NARTimingSessionActivationQualificationV2:
    session: Session
    declaration: NAROperationalTimingMeasurementSessionActivationDeclarationV2 | None
    verification_receipt: NAROperationalTimingMeasurementSessionActivationVerificationReceiptV2 | None
    state: NARTimingSessionActivationQualificationStateV2


class _ActivationArchiveV2(Protocol):
    def load_configuration(self, *, configuration_identity: str) -> Configuration | None: ...
    def load_session(self, *, session_identity: str) -> Session | None: ...
    def load_declaration_for_session(self, *, session_identity: str) -> NAROperationalTimingMeasurementSessionActivationDeclarationV2 | None: ...
    def load_verification_for_declaration(self, *, declaration_identity: str) -> NAROperationalTimingMeasurementSessionActivationVerificationReceiptV2 | None: ...
    def save_declaration(self, *, declaration: NAROperationalTimingMeasurementSessionActivationDeclarationV2, _issuance_marker: object = None) -> None: ...
    def save_verification_receipt(self, *, receipt: NAROperationalTimingMeasurementSessionActivationVerificationReceiptV2, _issuance_marker: object = None) -> None: ...


def _require_archived_session(session: Session, archive: _ActivationArchiveV2) -> None:
    if type(session) is not Session:
        raise TimingActivationV2Error("exact V2 session is required")
    if archive.load_configuration(configuration_identity=session.configuration.configuration_identity) != session.configuration:
        raise TimingActivationV2Error("V2 configuration is not archived exactly")
    if archive.load_session(session_identity=session.session_identity) != session:
        raise TimingActivationV2Error("V2 session is not archived exactly")


def qualify_nar_operational_timing_session_activation_v2(
    *, session: Session, archive: _ActivationArchiveV2,
) -> NARTimingSessionActivationQualificationV2:
    _require_archived_session(session, archive)
    declaration = archive.load_declaration_for_session(session_identity=session.session_identity)
    if declaration is None:
        return NARTimingSessionActivationQualificationV2(session, None, None,
            NARTimingSessionActivationQualificationStateV2.ACTIVATION_PROVENANCE_UNAVAILABLE)
    expected = NAROperationalTimingMeasurementSessionActivationDeclarationV2(
        session.session_identity, session.configuration.configuration_identity)
    if type(declaration) is not type(expected) or declaration != expected:
        raise TimingActivationV2Error("archived V2 declaration contradicts session")
    receipt = archive.load_verification_for_declaration(declaration_identity=declaration.declaration_identity)
    if receipt is None:
        return NARTimingSessionActivationQualificationV2(session, declaration, None,
            NARTimingSessionActivationQualificationStateV2.ACTIVATION_PROVENANCE_UNAVAILABLE)
    if (type(receipt) is not NAROperationalTimingMeasurementSessionActivationVerificationReceiptV2
            or (receipt.declaration_identity, receipt.session_identity,
                receipt.measurement_configuration_identity) !=
               (declaration.declaration_identity, session.session_identity,
                session.configuration.configuration_identity)):
        raise TimingActivationV2Error("archived V2 verification contradicts declaration")
    state = (NARTimingSessionActivationQualificationStateV2.OFFICIAL_PREDECLARED_MEASUREMENT_SESSION
             if receipt.activation_verified_at <= session.measurement_start_at else
             NARTimingSessionActivationQualificationStateV2.ACTIVATION_VERIFIED_AFTER_MEASUREMENT_START)
    return NARTimingSessionActivationQualificationV2(session, declaration, receipt, state)


def issue_nar_operational_timing_session_activation_v2(
    *, session: Session, archive: _ActivationArchiveV2, utc_clock: Callable[[], datetime],
) -> NARTimingSessionActivationQualificationV2:
    """Commit/reload declaration before the service-owned verification time sample."""
    _require_archived_session(session, archive)
    declaration = NAROperationalTimingMeasurementSessionActivationDeclarationV2(
        session.session_identity, session.configuration.configuration_identity)
    existing = archive.load_declaration_for_session(session_identity=session.session_identity)
    if existing is not None and existing != declaration:
        raise TimingActivationV2Error("V2 session has conflicting declaration")
    if existing is None:
        archive.save_declaration(declaration=declaration, _issuance_marker=_ISSUANCE_MARKER)
    if archive.load_declaration_for_session(session_identity=session.session_identity) != declaration:
        raise TimingActivationV2Error("V2 declaration did not reload exactly")
    existing_receipt = archive.load_verification_for_declaration(declaration_identity=declaration.declaration_identity)
    if existing_receipt is not None:
        return qualify_nar_operational_timing_session_activation_v2(session=session, archive=archive)
    receipt = NAROperationalTimingMeasurementSessionActivationVerificationReceiptV2(
        declaration.declaration_identity, session.session_identity,
        session.configuration.configuration_identity, _utc(utc_clock()))
    archive.save_verification_receipt(receipt=receipt, _issuance_marker=_ISSUANCE_MARKER)
    if archive.load_verification_for_declaration(declaration_identity=declaration.declaration_identity) != receipt:
        raise TimingActivationV2Error("V2 verification did not reload exactly")
    return qualify_nar_operational_timing_session_activation_v2(session=session, archive=archive)
