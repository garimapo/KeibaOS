"""Phase111 prospective Deba authority; transport is an injected trusted boundary.

Record construction proves content, not issuance. Only the application reconstructs
target ancestry and consumes a fresh durable claim before calling capture_response.
No persisted claim can be used to resume a send or manufacture a success receipt.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from datetime import date, datetime, timezone
from enum import StrEnum
import hashlib
import json
import re

from scripts.simulation.historical_daily_targets import ProviderNativeDispositionEvidenceReference
from scripts.simulation.nar_historical_daily_target_capture import NARHistoricalDailyTargetResponseCapture
from scripts.simulation.nar_historical_daily_target_source import build_nar_historical_daily_replay_target_set
from scripts.simulation.nar_official_response_capture import (
    NAROfficialPageKind, NAROfficialResponseCapture, NAROfficialResponseCaptureUnsupportedError,
    canonicalize_nar_official_capture_url,
)
from scripts.simulation.nar_official_response_live_capture import NAROfficialLiveResponseCaptureService
from scripts.simulation.repositories.errors import SimulationRepositoryError


class AcquisitionIntegrityError(ValueError):
    """Exact authority, content or temporal ancestry is missing/contradictory."""


class FailureDisposition(StrEnum):
    CONNECT_TIMEOUT = "CONNECT_TIMEOUT"
    READ_TIMEOUT = "READ_TIMEOUT"
    TRANSPORT_FAILURE = "TRANSPORT_FAILURE"
    UNSUPPORTED_RESPONSE = "UNSUPPORTED_RESPONSE"
    CAPTURE_OR_RECEIPT_PUBLICATION_FAILURE = "CAPTURE_OR_RECEIPT_PUBLICATION_FAILURE"
    CAPTURE_INTEGRITY_FAILURE = "CAPTURE_INTEGRITY_FAILURE"


def _time(value):
    if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
        raise AcquisitionIntegrityError("aware exact datetime required")
    return value.astimezone(timezone.utc)


def _text(value):
    if type(value) is not str or not value or value.strip() != value:
        raise AcquisitionIntegrityError("exact nonempty text required")
    return value


def _digest(value):
    if type(value) is not str or re.fullmatch("[0-9a-f]{64}", value) is None:
        raise AcquisitionIntegrityError("exact SHA-256 required")
    return value


def canonical_deba_url(external_race_id: str) -> str:
    """Derive from a reconstructed target, never parse/reinterpret provider HTML."""
    match = re.fullmatch(r"nar:([0-9]{8}):([1-9][0-9]*):([1-9][0-9]*)", _text(external_race_id))
    if match is None:
        raise AcquisitionIntegrityError("canonical NAR race identity required")
    day, baba, number = match.groups()
    date.fromisoformat(f"{day[:4]}-{day[4:6]}-{day[6:]}")
    candidate = ("https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/DebaTable?"
                 f"k_babaCode={baba}&k_raceDate={day[:4]}%2F{day[4:6]}%2F{day[6:]}&k_raceNo={number}")
    kind, url = canonicalize_nar_official_capture_url(candidate)
    if kind is not NAROfficialPageKind.DEBA_TABLE or url != candidate:
        raise AcquisitionIntegrityError("canonical Deba derivation differs")
    return url


def _json_value(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat(timespec="microseconds") if type(value) is datetime else value.isoformat()
    if isinstance(value, dict):
        return {k: _json_value(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_value(v) for v in value]
    return value


class _Record:
    __slots__ = ()

    def canonical_bytes(self) -> bytes:
        return json.dumps({"semantic": type(self).__name__, "schema_version": 1,
                           "content": _json_value(asdict(self))}, ensure_ascii=False,
                          sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")

    @property
    def identity(self) -> str:
        return "phase111-" + type(self).__name__ + ":" + hashlib.sha256(self.canonical_bytes()).hexdigest()


@dataclass(frozen=True, slots=True)
class NARProspectiveDebaAcquisitionDeclarationV1(_Record):
    target_date: date
    envelope_capture_id: str
    race_list_capture_ids: tuple[str, ...]
    target_set_sha256: str
    external_race_id: str
    scheduled_start_at: datetime | None
    disposition_evidence: ProviderNativeDispositionEvidenceReference
    canonical_deba_url: str
    prediction_information_cutoff: datetime
    issued_at: datetime
    organization: str = "NAR"
    source_system: str = "nar_official"
    purpose: str = "PROSPECTIVE_RACE_DAY_INGESTION_V1"

    def __post_init__(self):
        if type(self.target_date) is not date:
            raise AcquisitionIntegrityError("target_date must be exact date")
        if (self.organization, self.source_system, self.purpose) != (
                "NAR", "nar_official", "PROSPECTIVE_RACE_DAY_INGESTION_V1"):
            raise AcquisitionIntegrityError("unsupported provider/purpose")
        _text(self.envelope_capture_id)
        if (type(self.race_list_capture_ids) is not tuple or not self.race_list_capture_ids
                or any(type(v) is not str for v in self.race_list_capture_ids)
                or tuple(sorted(set(self.race_list_capture_ids))) != self.race_list_capture_ids):
            raise AcquisitionIntegrityError("canonical unique RaceList capture references required")
        for value in self.race_list_capture_ids:
            _text(value)
        _digest(self.target_set_sha256)
        if type(self.disposition_evidence) is not ProviderNativeDispositionEvidenceReference:
            raise AcquisitionIntegrityError("exact disposition evidence required")
        if self.canonical_deba_url != canonical_deba_url(self.external_race_id):
            raise AcquisitionIntegrityError("target/URL contradiction")
        if self.external_race_id.split(":")[1] != self.target_date.strftime("%Y%m%d"):
            raise AcquisitionIntegrityError("target date contradiction")
        for name in ("issued_at", "prediction_information_cutoff", "scheduled_start_at"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _time(value))
        if self.issued_at > self.prediction_information_cutoff:
            raise AcquisitionIntegrityError("declaration is after cutoff")
        if self.scheduled_start_at is not None and self.prediction_information_cutoff > self.scheduled_start_at:
            raise AcquisitionIntegrityError("cutoff exceeds target scheduled start")


@dataclass(frozen=True, slots=True)
class NARProspectiveDebaSendClaimV1(_Record):
    declaration_id: str
    claimed_at: datetime

    def __post_init__(self):
        _text(self.declaration_id)
        object.__setattr__(self, "claimed_at", _time(self.claimed_at))


@dataclass(frozen=True, slots=True)
class NARProspectiveDebaFailureV1(_Record):
    declaration_id: str
    claim_id: str
    disposition: FailureDisposition

    def __post_init__(self):
        _text(self.declaration_id)
        _text(self.claim_id)
        if type(self.disposition) is not FailureDisposition:
            raise AcquisitionIntegrityError("closed failure disposition required")


@dataclass(frozen=True, slots=True)
class NARProspectiveDebaAcquisitionReceiptV1(_Record):
    declaration_id: str
    claim_id: str
    external_race_id: str
    canonical_deba_url: str
    capture_id: str
    response_sha256: str
    requested_at: datetime
    observed_at: datetime
    stored_at: datetime
    prediction_information_cutoff: datetime
    organization: str = "NAR"
    source_system: str = "nar_official"
    terminal_disposition: str = "SUCCESS"

    def __post_init__(self):
        for name in ("declaration_id", "claim_id", "capture_id"):
            _text(getattr(self, name))
        _digest(self.response_sha256)
        if self.canonical_deba_url != canonical_deba_url(self.external_race_id):
            raise AcquisitionIntegrityError("receipt target/URL mismatch")
        if (self.organization, self.source_system, self.terminal_disposition) != ("NAR", "nar_official", "SUCCESS"):
            raise AcquisitionIntegrityError("receipt provider/terminal mismatch")
        for name in ("requested_at", "observed_at", "stored_at", "prediction_information_cutoff"):
            object.__setattr__(self, name, _time(getattr(self, name)))
        if not self.requested_at <= self.observed_at <= self.stored_at:
            raise AcquisitionIntegrityError("receipt times out of order")
        if self.observed_at > self.prediction_information_cutoff:
            raise AcquisitionIntegrityError("post-cutoff capture cannot qualify")


RECORD_TYPES = (NARProspectiveDebaAcquisitionDeclarationV1, NARProspectiveDebaSendClaimV1,
                NARProspectiveDebaFailureV1, NARProspectiveDebaAcquisitionReceiptV1)


def record_from_bytes(record_type, value: bytes):
    """Exact canonical reconstruction rejects missing/extra content and schema drift."""
    if record_type not in RECORD_TYPES or type(value) is not bytes:
        raise AcquisitionIntegrityError("unsupported record")
    def unique_pairs(pairs):
        out = {}
        for key, val in pairs:
            if key in out:
                raise AcquisitionIntegrityError("duplicate JSON key")
            out[key] = val
        return out
    payload = json.loads(value.decode("utf-8"), object_pairs_hook=unique_pairs)
    if set(payload) != {"semantic", "schema_version", "content"} or payload["semantic"] != record_type.__name__ or type(payload["schema_version"]) is not int or payload["schema_version"] != 1:
        raise AcquisitionIntegrityError("unsupported schema")
    data = payload["content"]
    if type(data) is not dict or set(data) != {f.name for f in fields(record_type)}:
        raise AcquisitionIntegrityError("record fields differ")
    for name in ("issued_at", "claimed_at", "requested_at", "observed_at", "stored_at", "prediction_information_cutoff", "scheduled_start_at"):
        if name in data and data[name] is not None:
            data[name] = datetime.fromisoformat(data[name])
    if record_type is NARProspectiveDebaAcquisitionDeclarationV1:
        data["target_date"] = date.fromisoformat(data["target_date"])
        data["race_list_capture_ids"] = tuple(data["race_list_capture_ids"])
        data["disposition_evidence"] = ProviderNativeDispositionEvidenceReference(**data["disposition_evidence"])
    if record_type is NARProspectiveDebaFailureV1:
        data["disposition"] = FailureDisposition(data["disposition"])
    result = record_type(**data)
    if result.canonical_bytes() != value:
        raise AcquisitionIntegrityError("noncanonical record bytes")
    return result


def reconstruct_declaration(*, target_archive, target_date, envelope_capture_id,
                            race_list_capture_ids, expected_target_set_sha256,
                            external_race_id, prediction_information_cutoff, issued_at):
    """Load exact upstream captures; caller target objects/digests alone have no power."""
    if type(race_list_capture_ids) is not tuple or not race_list_capture_ids:
        raise AcquisitionIntegrityError("exact capture references required")
    ids = tuple(sorted(race_list_capture_ids))
    if len(set(ids)) != len(ids):
        raise AcquisitionIntegrityError("duplicate capture references")
    captures = tuple(target_archive.load_capture(capture_id=v) for v in (envelope_capture_id,) + ids)
    if any(type(c) is not NARHistoricalDailyTargetResponseCapture for c in captures):
        raise AcquisitionIntegrityError("missing exact daily-target evidence")
    if tuple(c.capture_id for c in captures) != (envelope_capture_id,) + ids:
        raise AcquisitionIntegrityError("daily-target reload identity mismatch")
    if any(c.stored_at > _time(issued_at) for c in captures):
        raise AcquisitionIntegrityError("target evidence must preexist declaration")
    target_set = build_nar_historical_daily_replay_target_set(
        target_date=target_date, envelope_capture=captures[0], race_list_captures=captures[1:])
    if target_set.content_sha256 != _digest(expected_target_set_sha256):
        raise AcquisitionIntegrityError("reconstructed target-set hash differs")
    matches = tuple(t for t in target_set.target_races if t.external_race_id == external_race_id)
    if len(matches) != 1 or (matches[0].provider_identity.organization, matches[0].provider_identity.source_system) != ("NAR", "nar_official"):
        raise AcquisitionIntegrityError("exact NAR target membership required")
    target = matches[0]
    evidence = target.provider_disposition_evidence
    if evidence.exact_capture_or_reference_identity not in ids:
        raise AcquisitionIntegrityError("RaceList disposition ancestry is missing")
    parent = next(c for c in captures[1:] if c.capture_id == evidence.exact_capture_or_reference_identity)
    if parent.response_sha256 != evidence.content_sha256:
        raise AcquisitionIntegrityError("RaceList disposition digest differs")
    return NARProspectiveDebaAcquisitionDeclarationV1(
        target_date, envelope_capture_id, ids, target_set.content_sha256, target.external_race_id,
        target.scheduled_start_at, evidence, canonical_deba_url(target.external_race_id),
        prediction_information_cutoff, issued_at)


@dataclass(frozen=True, slots=True)
class NARQualifiedDebaResultV1:
    declaration_id: str
    claim_id: str
    receipt_id: str
    capture_id: str
    canonical_deba_url: str
    response_sha256: str
    observed_at: datetime


def _result(receipt):
    return NARQualifiedDebaResultV1(receipt.declaration_id, receipt.claim_id, receipt.identity,
                                  receipt.capture_id, receipt.canonical_deba_url,
                                  receipt.response_sha256, receipt.observed_at)


def _verify_capture(capture, declaration, claim):
    if type(capture) is not NAROfficialResponseCapture:
        raise AcquisitionIntegrityError("exact capture missing")
    if capture.page_kind is not NAROfficialPageKind.DEBA_TABLE or capture.canonical_source_url != declaration.canonical_deba_url:
        raise AcquisitionIntegrityError("capture target/URL differs")
    if not claim.claimed_at <= capture.requested_at <= capture.observed_at <= declaration.prediction_information_cutoff:
        raise AcquisitionIntegrityError("capture outside authorized observation window")
    capture.response_body.decode("utf-8", errors="strict")


class NARTrustedDebaAcquisitionApplication:
    """Trusted composition. Injected service must be the reviewed capture boundary.

    Production and deterministic tests use the exact reviewed service type; tests
    inject fake transport beneath that service. A supplied capture is never an input
    to issuance. The application has no restart/resume-send API.
    """
    def __init__(self, *, target_archive, lineage_archive, capture_archive,
                 capture_service: NAROfficialLiveResponseCaptureService):
        if type(capture_service) is not NAROfficialLiveResponseCaptureService:
            raise AcquisitionIntegrityError("exact reviewed live capture service required")
        self._targets = target_archive
        self._lineage = lineage_archive
        self._captures = capture_archive
        self._service = capture_service

    def declare(self, **authority):
        declaration = reconstruct_declaration(target_archive=self._targets, **authority)
        self._lineage.save_declaration(declaration=declaration)
        loaded = self._lineage.load_declaration(declaration_id=declaration.identity)
        if loaded != declaration:
            raise AcquisitionIntegrityError("declaration publication/reload differs")
        return loaded

    def acquire(self, *, declaration_id: str, claimed_at: datetime) -> NARQualifiedDebaResultV1:
        # Local import preserves the archive's domain dependency direction.
        from scripts.simulation.sqlite_nar_trusted_deba_acquisition_archive import _PHASE111_TERMINAL_ISSUANCE_MARKER

        declaration = self._lineage.load_declaration(declaration_id=declaration_id)
        if type(declaration) is not NARProspectiveDebaAcquisitionDeclarationV1:
            raise AcquisitionIntegrityError("exact persisted declaration required")
        rebuilt = reconstruct_declaration(
            target_archive=self._targets, target_date=declaration.target_date,
            envelope_capture_id=declaration.envelope_capture_id,
            race_list_capture_ids=declaration.race_list_capture_ids,
            expected_target_set_sha256=declaration.target_set_sha256,
            external_race_id=declaration.external_race_id,
            prediction_information_cutoff=declaration.prediction_information_cutoff,
            issued_at=declaration.issued_at)
        if rebuilt != declaration:
            raise AcquisitionIntegrityError("declaration ancestry changed")
        claim = self._lineage.acquire_claim(declaration_id=declaration_id, claimed_at=claimed_at)
        # Claim is committed before this invocation. BaseException leaves it UNKNOWN.
        stage = "transport"
        try:
            returned = self._service.capture_response(response_url=declaration.canonical_deba_url)
            stage = "capture_reload"
            if type(returned) is not NAROfficialResponseCapture:
                raise AcquisitionIntegrityError("capture boundary returned an invalid value")
            capture = self._captures.load_capture(capture_id=returned.capture_id)
            if capture != returned:
                raise AcquisitionIntegrityError("capture archive exact reload differs")
            _verify_capture(capture, declaration, claim)
            receipt = NARProspectiveDebaAcquisitionReceiptV1(
                declaration.identity, claim.identity, declaration.external_race_id,
                declaration.canonical_deba_url, capture.capture_id, capture.response_sha256,
                capture.requested_at, capture.observed_at, capture.stored_at,
                declaration.prediction_information_cutoff)
            stage = "receipt"
            self._lineage._publish_receipt(
                receipt=receipt, _issuance_marker=_PHASE111_TERMINAL_ISSUANCE_MARKER)
            if self._lineage.load_receipt(receipt_id=receipt.identity) != receipt:
                raise AcquisitionIntegrityError("receipt exact reload differs")
            return _result(receipt)
        except Exception as error:
            disposition = _failure_disposition(error, stage)
            try:
                self._lineage._publish_failure(failure=NARProspectiveDebaFailureV1(
                    declaration.identity, claim.identity, disposition),
                    _issuance_marker=_PHASE111_TERMINAL_ISSUANCE_MARKER)
            except Exception:
                pass  # Durable claim remains consumed; no second invocation is possible.
            raise


def _failure_disposition(error, stage):
    if isinstance(error, NAROfficialResponseCaptureUnsupportedError):
        return FailureDisposition.UNSUPPORTED_RESPONSE
    if stage == "capture_reload":
        return FailureDisposition.CAPTURE_INTEGRITY_FAILURE
    if stage == "receipt":
        return FailureDisposition.CAPTURE_OR_RECEIPT_PUBLICATION_FAILURE
    if isinstance(error, SimulationRepositoryError):
        return FailureDisposition.CAPTURE_OR_RECEIPT_PUBLICATION_FAILURE
    # Existing trusted transport chains requests failures without exposing a new API.
    cause = error
    while cause is not None:
        if type(cause).__name__ == "ConnectTimeout":
            return FailureDisposition.CONNECT_TIMEOUT
        if type(cause).__name__ == "ReadTimeout":
            return FailureDisposition.READ_TIMEOUT
        cause = cause.__cause__
    return FailureDisposition.TRANSPORT_FAILURE


def read_qualified_deba_bytes(*, result, lineage_archive, capture_archive) -> bytes:
    """Read exact archive-backed bytes; this function has no transport dependency."""
    if type(result) is not NARQualifiedDebaResultV1:
        raise AcquisitionIntegrityError("qualified result required")
    receipt = lineage_archive.load_receipt(receipt_id=result.receipt_id)
    if type(receipt) is not NARProspectiveDebaAcquisitionReceiptV1 or _result(receipt) != result:
        raise AcquisitionIntegrityError("qualified result/receipt contradiction")
    declaration = lineage_archive.load_declaration(declaration_id=receipt.declaration_id)
    claim = lineage_archive.load_claim(claim_id=receipt.claim_id)
    capture = capture_archive.load_capture(capture_id=receipt.capture_id)
    _verify_capture(capture, declaration, claim)
    expected = NARProspectiveDebaAcquisitionReceiptV1(
        declaration.identity, claim.identity, declaration.external_race_id,
        declaration.canonical_deba_url, capture.capture_id, capture.response_sha256,
        capture.requested_at, capture.observed_at, capture.stored_at,
        declaration.prediction_information_cutoff)
    if expected != receipt:
        raise AcquisitionIntegrityError("receipt/capture contradiction")
    return capture.response_body
