"""Controlled pre-measurement declaration and verification provenance.

Content identity is not activation authority. Only the archived declaration and
verification chain issued by the controlled service can qualify a session.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from hashlib import sha256
import re
from typing import Callable, Protocol

from scripts.simulation.nar_operational_timing_observability import (
    NAROperationalTimingMeasurementConfiguration,
    NAROperationalTimingMeasurementSession,
    _json_bytes, _parse_time, _read_json, _time, _utc,
)


class TimingActivationError(ValueError):
    """Exact archived activation ancestry or controlled issuance is unavailable."""


_ISSUANCE_MARKER = object()  # API discipline in trusted composition, not cryptography.
_SESSION_ID = re.compile(r"nar-operational-timing-session-v1:[0-9a-f]{64}\Z")
_CONFIG_ID = re.compile(r"nar-operational-timing-config-v1:[0-9a-f]{64}\Z")
_DECLARATION_ID = re.compile(r"nar-operational-timing-activation-declaration-v1:[0-9a-f]{64}\Z")


class NARTimingActivationDeclarationSemantic(StrEnum):
    INTENDED_PROSPECTIVE_MEASUREMENT_CAMPAIGN = "INTENDED_PROSPECTIVE_MEASUREMENT_CAMPAIGN"


class NARTimingActivationVerificationSemantic(StrEnum):
    DECLARATION_COMMITTED_AND_EXACT_RELOAD_VERIFIED = "DECLARATION_COMMITTED_AND_EXACT_RELOAD_VERIFIED"


@dataclass(frozen=True, slots=True)
class NAROperationalTimingMeasurementSessionActivationDeclaration:
    session_identity: str
    measurement_configuration_identity: str
    semantic: NARTimingActivationDeclarationSemantic = (
        NARTimingActivationDeclarationSemantic.INTENDED_PROSPECTIVE_MEASUREMENT_CAMPAIGN
    )
    schema_version: int = 1
    declaration_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if (type(self.session_identity) is not str or _SESSION_ID.fullmatch(self.session_identity) is None
                or type(self.measurement_configuration_identity) is not str
                or _CONFIG_ID.fullmatch(self.measurement_configuration_identity) is None
                or type(self.semantic) is not NARTimingActivationDeclarationSemantic
                or type(self.schema_version) is not int or self.schema_version != 1):
            raise TimingActivationError("declaration identity, semantic, or version is invalid")
        object.__setattr__(self, "declaration_sha256", sha256(self.canonical_bytes()).hexdigest())

    @property
    def declaration_identity(self) -> str:
        return "nar-operational-timing-activation-declaration-v1:" + self.declaration_sha256

    def payload(self) -> dict[str, object]:
        return {"schema_version": self.schema_version,
                "session_identity": self.session_identity,
                "measurement_configuration_identity": self.measurement_configuration_identity,
                "semantic": self.semantic.value}

    def canonical_bytes(self) -> bytes:
        return _json_bytes(self.payload())

    @classmethod
    def from_json(cls, value: str) -> NAROperationalTimingMeasurementSessionActivationDeclaration:
        p = _read_json(value)
        result = cls(p["session_identity"], p["measurement_configuration_identity"],
                     NARTimingActivationDeclarationSemantic(p["semantic"]), p["schema_version"])
        if result.canonical_bytes() != value.encode("utf-8"):
            raise TimingActivationError("declaration JSON is not canonical")
        return result


@dataclass(frozen=True, slots=True)
class NAROperationalTimingMeasurementSessionActivationVerificationReceipt:
    declaration_identity: str
    session_identity: str
    measurement_configuration_identity: str
    activation_verified_at: datetime
    semantic: NARTimingActivationVerificationSemantic = (
        NARTimingActivationVerificationSemantic.DECLARATION_COMMITTED_AND_EXACT_RELOAD_VERIFIED
    )
    schema_version: int = 1
    verification_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if (type(self.declaration_identity) is not str
                or _DECLARATION_ID.fullmatch(self.declaration_identity) is None
                or type(self.session_identity) is not str or _SESSION_ID.fullmatch(self.session_identity) is None
                or type(self.measurement_configuration_identity) is not str
                or _CONFIG_ID.fullmatch(self.measurement_configuration_identity) is None
                or type(self.semantic) is not NARTimingActivationVerificationSemantic
                or type(self.schema_version) is not int or self.schema_version != 1):
            raise TimingActivationError("verification identity, semantic, or version is invalid")
        try:
            verified = _utc(self.activation_verified_at)
        except ValueError as error:
            raise TimingActivationError("verification requires aware UTC-compatible time") from error
        object.__setattr__(self, "activation_verified_at", verified)
        object.__setattr__(self, "verification_sha256", sha256(self.canonical_bytes()).hexdigest())

    @property
    def verification_identity(self) -> str:
        return "nar-operational-timing-activation-verification-v1:" + self.verification_sha256

    def payload(self) -> dict[str, object]:
        return {"schema_version": self.schema_version,
                "declaration_identity": self.declaration_identity,
                "session_identity": self.session_identity,
                "measurement_configuration_identity": self.measurement_configuration_identity,
                "semantic": self.semantic.value,
                "activation_verified_at": _time(self.activation_verified_at)}

    def canonical_bytes(self) -> bytes:
        return _json_bytes(self.payload())

    @classmethod
    def from_json(cls, value: str) -> NAROperationalTimingMeasurementSessionActivationVerificationReceipt:
        p = _read_json(value)
        result = cls(p["declaration_identity"], p["session_identity"],
                     p["measurement_configuration_identity"], _parse_time(p["activation_verified_at"]),
                     NARTimingActivationVerificationSemantic(p["semantic"]), p["schema_version"])
        if result.canonical_bytes() != value.encode("utf-8"):
            raise TimingActivationError("verification JSON is not canonical")
        return result


class NARTimingSessionActivationQualificationState(StrEnum):
    OFFICIAL_PREDECLARED_MEASUREMENT_SESSION = "OFFICIAL_PREDECLARED_MEASUREMENT_SESSION"
    ACTIVATION_VERIFIED_AFTER_MEASUREMENT_START = "ACTIVATION_VERIFIED_AFTER_MEASUREMENT_START"
    ACTIVATION_PROVENANCE_UNAVAILABLE = "ACTIVATION_PROVENANCE_UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class NARTimingSessionActivationQualification:
    session: NAROperationalTimingMeasurementSession
    declaration: NAROperationalTimingMeasurementSessionActivationDeclaration | None
    verification_receipt: NAROperationalTimingMeasurementSessionActivationVerificationReceipt | None
    state: NARTimingSessionActivationQualificationState


class _ActivationArchive(Protocol):
    def load_configuration(self, *, configuration_identity: str) -> NAROperationalTimingMeasurementConfiguration | None: ...
    def load_session(self, *, session_identity: str) -> NAROperationalTimingMeasurementSession | None: ...
    def load_declaration_for_session(self, *, session_identity: str) -> NAROperationalTimingMeasurementSessionActivationDeclaration | None: ...
    def load_verification_for_declaration(self, *, declaration_identity: str) -> NAROperationalTimingMeasurementSessionActivationVerificationReceipt | None: ...
    def save_declaration(self, *, declaration: NAROperationalTimingMeasurementSessionActivationDeclaration,
                         _issuance_marker: object = None) -> None: ...
    def save_verification_receipt(self, *, receipt: NAROperationalTimingMeasurementSessionActivationVerificationReceipt,
                                  _issuance_marker: object = None) -> None: ...


def _require_archived_session(
    session: NAROperationalTimingMeasurementSession, archive: _ActivationArchive,
) -> None:
    if type(session) is not NAROperationalTimingMeasurementSession:
        raise TimingActivationError("exact measurement session is required")
    if archive.load_configuration(configuration_identity=session.configuration.configuration_identity) != session.configuration:
        raise TimingActivationError("configuration is not archived exactly")
    if archive.load_session(session_identity=session.session_identity) != session:
        raise TimingActivationError("session is not archived exactly")


def qualify_nar_operational_timing_session_activation(
    *, session: NAROperationalTimingMeasurementSession, archive: _ActivationArchive,
) -> NARTimingSessionActivationQualification:
    """Qualify only an exact archived declaration and verification chain."""
    _require_archived_session(session, archive)
    declaration = archive.load_declaration_for_session(session_identity=session.session_identity)
    if declaration is None:
        return NARTimingSessionActivationQualification(session, None, None,
            NARTimingSessionActivationQualificationState.ACTIVATION_PROVENANCE_UNAVAILABLE)
    expected = NAROperationalTimingMeasurementSessionActivationDeclaration(
        session.session_identity, session.configuration.configuration_identity)
    if type(declaration) is not type(expected) or declaration != expected:
        raise TimingActivationError("archived declaration contradicts session")
    receipt = archive.load_verification_for_declaration(declaration_identity=declaration.declaration_identity)
    if receipt is None:
        return NARTimingSessionActivationQualification(session, declaration, None,
            NARTimingSessionActivationQualificationState.ACTIVATION_PROVENANCE_UNAVAILABLE)
    if (type(receipt) is not NAROperationalTimingMeasurementSessionActivationVerificationReceipt
            or (receipt.declaration_identity, receipt.session_identity,
                receipt.measurement_configuration_identity) !=
               (declaration.declaration_identity, session.session_identity,
                session.configuration.configuration_identity)):
        raise TimingActivationError("archived verification contradicts declaration")
    state = (NARTimingSessionActivationQualificationState.OFFICIAL_PREDECLARED_MEASUREMENT_SESSION
             if receipt.activation_verified_at <= session.measurement_start_at else
             NARTimingSessionActivationQualificationState.ACTIVATION_VERIFIED_AFTER_MEASUREMENT_START)
    return NARTimingSessionActivationQualification(session, declaration, receipt, state)


def issue_nar_operational_timing_session_activation(
    *, session: NAROperationalTimingMeasurementSession, archive: _ActivationArchive,
    utc_clock: Callable[[], datetime],
) -> NARTimingSessionActivationQualification:
    """Commit/reload declaration, sample UTC, then commit/reload verification.

    The sample proves declaration availability, not receipt publication time or
    crash durability. An exact existing verification is reused without resampling.
    """
    _require_archived_session(session, archive)
    declaration = NAROperationalTimingMeasurementSessionActivationDeclaration(
        session.session_identity, session.configuration.configuration_identity)
    existing = archive.load_declaration_for_session(session_identity=session.session_identity)
    if existing is not None and existing != declaration:
        raise TimingActivationError("session has a conflicting declaration")
    if existing is None:
        archive.save_declaration(declaration=declaration, _issuance_marker=_ISSUANCE_MARKER)
    if archive.load_declaration_for_session(session_identity=session.session_identity) != declaration:
        raise TimingActivationError("committed declaration did not reload exactly")
    existing_receipt = archive.load_verification_for_declaration(
        declaration_identity=declaration.declaration_identity)
    if existing_receipt is not None:
        return qualify_nar_operational_timing_session_activation(session=session, archive=archive)
    receipt = NAROperationalTimingMeasurementSessionActivationVerificationReceipt(
        declaration.declaration_identity, session.session_identity,
        session.configuration.configuration_identity, _utc(utc_clock()))
    archive.save_verification_receipt(receipt=receipt, _issuance_marker=_ISSUANCE_MARKER)
    if archive.load_verification_for_declaration(declaration_identity=declaration.declaration_identity) != receipt:
        raise TimingActivationError("committed verification did not reload exactly")
    return qualify_nar_operational_timing_session_activation(session=session, archive=archive)
