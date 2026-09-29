"""Deterministic no-network Phase111 composition, never production DB access."""
from dataclasses import FrozenInstanceError, replace
from datetime import date, datetime, timedelta, timezone
import hashlib
import inspect
from pathlib import Path
import sqlite3
from types import SimpleNamespace

import pytest
import requests

from scripts.simulation import nar_trusted_deba_acquisition as subject
from scripts.simulation.nar_daily_target_evidence_archive_migration import apply_nar_daily_target_evidence_archive_migrations
from scripts.simulation.nar_historical_daily_target_capture import (
    NARHistoricalDailyTargetPageKind, NARHistoricalDailyTargetRequestIdentity,
    NARHistoricalDailyTargetResponseCapture,
)
from scripts.simulation.nar_historical_daily_target_source import (
    normalize_nar_monthly_convene_info, build_nar_historical_daily_replay_target_set,
)
from scripts.simulation.nar_official_response_capture import NAROfficialResponseCapture, NAROfficialResponseCaptureUnsupportedError
from scripts.simulation.nar_official_response_capture_migration_runner import apply_capture_schema_migrations
from scripts.simulation.nar_official_response_live_capture import NAROfficialLiveResponseCaptureService, _NAROfficialHTTPResponse
from scripts.simulation.repositories.sqlite_nar_official_response_capture_repository import SQLiteNAROfficialResponseCaptureRepository
from scripts.simulation.sqlite_nar_daily_target_evidence_archive import SQLiteNARDailyTargetEvidenceArchive
from scripts.simulation.nar_trusted_deba_acquisition_archive_migration import apply_nar_trusted_deba_acquisition_archive_migrations
from scripts.simulation.sqlite_nar_trusted_deba_acquisition_archive import SQLiteNARTrustedDebaAcquisitionArchive
from scripts.simulation.repositories.errors import RepositoryConflictError, RepositoryDataIntegrityError, RepositoryValidationError

T0 = datetime(2025, 1, 1, tzinfo=timezone.utc)
FIXTURES = Path(__file__).parent / "fixtures" / "nar_daily_targets"


def environment(lineage_connection=None):
    """Fixture bytes test parser semantics; fake timestamps model prospective ordering."""
    connections = [sqlite3.connect(":memory:"), sqlite3.connect(":memory:")]
    lc = lineage_connection or sqlite3.connect(":memory:")
    connections.append(lc)
    apply_nar_daily_target_evidence_archive_migrations(connections[0])
    targets = SQLiteNARDailyTargetEvidenceArchive(connection=connections[0])
    apply_capture_schema_migrations(connections[1])
    captures = SQLiteNAROfficialResponseCaptureRepository(connection=connections[1])
    apply_nar_trusted_deba_acquisition_archive_migrations(lc)
    lineage = SQLiteNARTrustedDebaAcquisitionArchive(connection=lc)
    raw = b"/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop?k_year=2025&k_month=1"
    request = NARHistoricalDailyTargetRequestIdentity(
        NARHistoricalDailyTargetPageKind.MONTHLY_CONVENE_INFO, raw,
        "https://www.keiba.go.jp" + raw.decode(), "test-only-prospective-supplier")
    def make_capture(request, body):
        return NARHistoricalDailyTargetResponseCapture(request, body, "utf-8", T0,
            T0 + timedelta(seconds=1), T0 + timedelta(seconds=2), 200)
    monthly = make_capture(request, (FIXTURES / "monthly_convene_info_2025_01.utf8.html").read_bytes())
    envelope = normalize_nar_monthly_convene_info(target_date=T0.date(), capture=monthly)
    paths = ("race_list_2025_01_01_kawasaki_baba21.utf8.html",
             "race_list_2025_01_01_nagoya_baba24.utf8.html",
             "race_list_2025_01_01_kochi_baba31.utf8.html")
    races = tuple(make_capture(loc.request_identity, (FIXTURES / path).read_bytes())
                  for loc, path in zip(envelope.venue_locators, paths))
    for capture in (monthly,) + races:
        targets.save_capture(capture=capture)
    target_set = build_nar_historical_daily_replay_target_set(
        target_date=T0.date(), envelope_capture=monthly, race_list_captures=races)
    authority = dict(target_date=T0.date(), envelope_capture_id=monthly.capture_id,
                     race_list_capture_ids=tuple(r.capture_id for r in races),
                     expected_target_set_sha256=target_set.content_sha256,
                     external_race_id="nar:20250101:21:1",
                     prediction_information_cutoff=T0 + timedelta(minutes=20),
                     issued_at=T0 + timedelta(seconds=10))
    events = []
    transport = FakeTransport(lc, events)
    ticks = iter(T0 + timedelta(seconds=v) for v in range(12, 40))
    service = NAROfficialLiveResponseCaptureService(archive=captures, transport=transport,
                                                    utc_clock=lambda: next(ticks))
    app = subject.NARTrustedDebaAcquisitionApplication(target_archive=targets,
              lineage_archive=lineage, capture_archive=captures, capture_service=service)
    return SimpleNamespace(connections=connections, targets=targets, captures=captures,
              lineage=lineage, app=app, authority=authority, transport=transport,
              events=events, monthly=monthly, races=races, target_set=target_set, service=service)


class FakeTransport:
    def __init__(self, connection, events):
        self.connection = connection
        self.events = events
        self.urls = []
        self.error = None
        self.body = b"<html><table><tr><td>exact same bytes</td></tr></table></html>"

    def fetch(self, *, canonical_source_url):
        assert not self.connection.in_transaction
        assert self.connection.execute("SELECT count(*) FROM phase111_claims").fetchone()[0] >= 1
        self.events.append("send")
        self.urls.append(canonical_source_url)
        if self.error is not None:
            raise self.error
        return _NAROfficialHTTPResponse(canonical_source_url, self.body, "text/html", "identity",
                                      None, None, None, len(self.body))


@pytest.fixture
def env():
    value = environment()
    yield value
    for connection in value.connections:
        connection.close()


def acquire(env):
    declaration = env.app.declare(**env.authority)
    result = env.app.acquire(declaration_id=declaration.identity, claimed_at=T0 + timedelta(seconds=11))
    return declaration, result


def test_complete_trusted_service_and_archive_composition(env):
    declaration, result = acquire(env)
    assert env.transport.urls == [declaration.canonical_deba_url]
    assert env.lineage.disposition(declaration_id=declaration.identity) == "RECEIPT_COMPLETE"
    receipt = env.lineage.load_receipt(receipt_id=result.receipt_id)
    capture = env.captures.load_capture(capture_id=result.capture_id)
    assert receipt.response_sha256 == hashlib.sha256(capture.response_body).hexdigest()
    assert receipt.claim_id == result.claim_id
    assert receipt.observed_at == result.observed_at
    assert receipt.external_race_id == declaration.external_race_id
    assert receipt.prediction_information_cutoff == declaration.prediction_information_cutoff
    assert receipt.requested_at == capture.requested_at
    assert receipt.stored_at == capture.stored_at
    for _ in range(2):
        assert subject.read_qualified_deba_bytes(result=result, lineage_archive=env.lineage,
                                                capture_archive=env.captures) == env.transport.body
    assert len(env.transport.urls) == 1
    assert not any(hasattr(result, name) for name in ("fetch", "retry", "provider", "transport", "refresh"))


def test_target_reconstruction_deterministic_and_canonical(env):
    a = env.app.declare(**env.authority)
    b = env.app.declare(**{**env.authority, "race_list_capture_ids": tuple(reversed(env.authority["race_list_capture_ids"]))})
    assert a == b and a.identity == b.identity
    assert a.canonical_deba_url == "https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/DebaTable?k_babaCode=21&k_raceDate=2025%2F01%2F01&k_raceNo=1"
    assert a.disposition_evidence.exact_capture_or_reference_identity in a.race_list_capture_ids


@pytest.mark.parametrize("change", [
    {"external_race_id": "nar:20250101:99:1"},
    {"external_race_id": "jra:20250101:21:1"},
    {"expected_target_set_sha256": "0" * 64},
    {"race_list_capture_ids": ()},
    {"envelope_capture_id": "missing"},
    {"issued_at": T0},
])
def test_detached_or_wrong_ancestry_never_sends(env, change):
    with pytest.raises(Exception):
        env.app.declare(**{**env.authority, **change})
    assert env.transport.urls == []


def test_immutable_content_identity_changes_with_refresh(env):
    declaration = env.app.declare(**env.authority)
    with pytest.raises(FrozenInstanceError):
        declaration.issued_at = T0
    refreshed = replace(declaration, issued_at=declaration.issued_at + timedelta(seconds=1))
    assert declaration.identity != refreshed.identity
    assert subject.record_from_bytes(type(declaration), declaration.canonical_bytes()) == declaration


def test_publicly_constructed_declaration_cannot_self_authorize(env):
    genuine = env.app.declare(**env.authority)
    forged = replace(genuine, target_set_sha256="0" * 64)
    env.lineage.save_declaration(declaration=forged)
    with pytest.raises(subject.AcquisitionIntegrityError):
        env.app.acquire(declaration_id=forged.identity, claimed_at=T0 + timedelta(seconds=11))
    assert env.transport.urls == []
    assert env.lineage.disposition(declaration_id=forged.identity) == "DECLARED_NOT_CLAIMED"


def test_target_capture_replacement_and_declaration_reload_rejected(env, monkeypatch):
    declaration = env.app.declare(**env.authority)
    monkeypatch.setattr(type(env.targets), "load_capture", lambda self, **kw: env.monthly)
    with pytest.raises(subject.AcquisitionIntegrityError):
        env.app.acquire(declaration_id=declaration.identity, claimed_at=T0 + timedelta(seconds=11))
    assert env.transport.urls == []


def test_declaration_publication_failure_blocks_claim_and_transport(env, monkeypatch):
    monkeypatch.setattr(env.lineage, "load_declaration", lambda **kw: None)
    with pytest.raises(subject.AcquisitionIntegrityError):
        env.app.declare(**env.authority)
    assert env.transport.urls == []
    assert env.connections[2].execute("SELECT count(*) FROM phase111_claims").fetchone()[0] == 0


def test_claim_is_consumed_and_restart_never_resumes(env):
    declaration = env.app.declare(**env.authority)
    env.lineage.acquire_claim(declaration_id=declaration.identity, claimed_at=T0 + timedelta(seconds=11))
    assert env.lineage.disposition(declaration_id=declaration.identity) == "UNKNOWN_SEND_OUTCOME"
    restarted = subject.NARTrustedDebaAcquisitionApplication(target_archive=env.targets,
        lineage_archive=SQLiteNARTrustedDebaAcquisitionArchive(connection=env.connections[2]),
        capture_archive=env.captures, capture_service=env.service)
    with pytest.raises(RepositoryConflictError):
        restarted.acquire(declaration_id=declaration.identity, claimed_at=T0 + timedelta(seconds=12))
    assert env.transport.urls == []


@pytest.mark.parametrize("error,disposition", [
    (requests.ConnectTimeout("fake"), "CONNECT_TIMEOUT"),
    (requests.ReadTimeout("fake"), "READ_TIMEOUT"),
    (RuntimeError("fake transport failure"), "TRANSPORT_FAILURE"),
])
def test_terminal_failure_is_retained_and_never_retried(env, error, disposition):
    declaration = env.app.declare(**env.authority)
    env.transport.error = error
    with pytest.raises(type(error)):
        env.app.acquire(declaration_id=declaration.identity, claimed_at=T0 + timedelta(seconds=11))
    assert env.lineage.disposition(declaration_id=declaration.identity) == "SEND_TERMINAL_FAILURE"
    row = env.connections[2].execute("SELECT identity FROM phase111_failures").fetchone()
    assert env.lineage.load_failure(failure_id=row[0]).disposition == disposition
    with pytest.raises(RepositoryConflictError):
        env.app.acquire(declaration_id=declaration.identity, claimed_at=T0 + timedelta(seconds=12))
    assert len(env.transport.urls) == 1


def test_failure_publication_failure_remains_unknown(env, monkeypatch):
    declaration = env.app.declare(**env.authority)
    env.transport.error = RuntimeError("transport failed")
    def fail(**kw):
        raise RuntimeError("publication failed")
    monkeypatch.setattr(env.lineage, "_publish_failure", fail)
    with pytest.raises(RuntimeError):
        env.app.acquire(declaration_id=declaration.identity, claimed_at=T0 + timedelta(seconds=11))
    assert env.lineage.disposition(declaration_id=declaration.identity) == "UNKNOWN_SEND_OUTCOME"


@pytest.mark.parametrize("boundary", ["capture", "receipt"])
def test_archive_publication_failure_is_not_transport_failure_and_never_retries(env, monkeypatch, boundary):
    declaration = env.app.declare(**env.authority)
    def fail(*args, **kwargs):
        raise RepositoryDataIntegrityError("fake archive publication failure")
    if boundary == "capture":
        monkeypatch.setattr(type(env.captures), "save_capture", fail)
    else:
        monkeypatch.setattr(env.lineage, "_publish_receipt", fail)
    with pytest.raises(RepositoryDataIntegrityError):
        env.app.acquire(declaration_id=declaration.identity, claimed_at=T0 + timedelta(seconds=11))
    row = env.connections[2].execute("SELECT identity FROM phase111_failures").fetchone()
    assert env.lineage.load_failure(failure_id=row[0]).disposition == "CAPTURE_OR_RECEIPT_PUBLICATION_FAILURE"
    assert env.lineage.disposition(declaration_id=declaration.identity) == "SEND_TERMINAL_FAILURE"
    with pytest.raises(RepositoryConflictError):
        env.app.acquire(declaration_id=declaration.identity, claimed_at=T0 + timedelta(seconds=12))
    assert len(env.transport.urls) == 1
    assert env.connections[2].execute("SELECT count(*) FROM phase111_receipts").fetchone() == (0,)


@pytest.mark.parametrize("mode", ["missing", "different"])
def test_capture_exact_reload_failure_blocks_receipt(env, monkeypatch, mode):
    declaration = env.app.declare(**env.authority)
    original = env.captures.load_capture
    def mismatch(self, **kw):
        capture = original(**kw)
        return None if mode == "missing" else replace(capture, response_body=b"different", content_length=9)
    monkeypatch.setattr(type(env.captures), "load_capture", mismatch)
    with pytest.raises(subject.AcquisitionIntegrityError):
        env.app.acquire(declaration_id=declaration.identity, claimed_at=T0 + timedelta(seconds=11))
    assert env.connections[2].execute("SELECT count(*) FROM phase111_receipts").fetchone()[0] == 0


def test_post_cutoff_capture_retains_raw_evidence_without_qualified_receipt(env):
    declaration = env.app.declare(**{**env.authority, "prediction_information_cutoff": T0 + timedelta(seconds=11)})
    with pytest.raises(subject.AcquisitionIntegrityError):
        env.app.acquire(declaration_id=declaration.identity, claimed_at=T0 + timedelta(seconds=11))
    assert env.connections[1].execute("SELECT count(*) FROM nar_official_response_captures").fetchone()[0] == 1
    assert env.connections[2].execute("SELECT count(*) FROM phase111_receipts").fetchone()[0] == 0


def test_non_utf8_is_unsupported_without_fallback(env):
    declaration = env.app.declare(**env.authority)
    env.transport.body = b"\xff"
    with pytest.raises(NAROfficialResponseCaptureUnsupportedError):
        env.app.acquire(declaration_id=declaration.identity, claimed_at=T0 + timedelta(seconds=11))
    assert env.lineage.disposition(declaration_id=declaration.identity) == "SEND_TERMINAL_FAILURE"
    assert len(env.transport.urls) == 1


def test_separately_authorized_refresh_may_send_once(env):
    old, _ = acquire(env)
    new = env.app.declare(**{**env.authority, "issued_at": T0 + timedelta(seconds=15)})
    result = env.app.acquire(declaration_id=new.identity, claimed_at=T0 + timedelta(seconds=15))
    assert old.identity != new.identity
    assert result.declaration_id == new.identity
    assert len(env.transport.urls) == 2


def test_manually_constructed_capture_and_forged_result_cannot_substitute(env):
    capture = NAROfficialResponseCapture(subject.canonical_deba_url("nar:20250101:21:1"), b"exact", "utf-8", T0, T0, T0, 200)
    env.captures.save_capture(capture=capture)
    result = subject.NARQualifiedDebaResultV1("unknown", "unknown", "phase111-NARProspectiveDebaAcquisitionReceiptV1:" + "0" * 64,
                                             capture.capture_id, capture.canonical_source_url, capture.response_sha256, T0)
    with pytest.raises(subject.AcquisitionIntegrityError):
        subject.read_qualified_deba_bytes(result=result, lineage_archive=env.lineage, capture_archive=env.captures)
    assert "capture" not in inspect.signature(env.app.acquire).parameters


@pytest.mark.parametrize("persist_manual_capture", [False, True])
def test_manual_receipt_cannot_publish_acquisition_authority(env, persist_manual_capture):
    declaration = env.app.declare(**env.authority)
    claim = env.lineage.acquire_claim(declaration_id=declaration.identity, claimed_at=T0 + timedelta(seconds=11))
    capture = NAROfficialResponseCapture(
        declaration.canonical_deba_url, b"manually supplied bytes", "utf-8",
        T0 + timedelta(seconds=12), T0 + timedelta(seconds=13),
        T0 + timedelta(seconds=14), 200)
    if persist_manual_capture:
        env.captures.save_capture(capture=capture)
        assert env.captures.load_capture(capture_id=capture.capture_id) == capture
    receipt = subject.NARProspectiveDebaAcquisitionReceiptV1(
        declaration.identity, claim.identity, declaration.external_race_id,
        declaration.canonical_deba_url, capture.capture_id, capture.response_sha256,
        capture.requested_at, capture.observed_at, capture.stored_at,
        declaration.prediction_information_cutoff)
    with pytest.raises(RepositoryValidationError, match="controlled current-process issuance"):
        env.lineage._publish_receipt(receipt=receipt)
    assert env.lineage.load_receipt(receipt_id=receipt.identity) is None
    assert env.connections[2].execute("SELECT count(*) FROM phase111_receipts").fetchone() == (0,)
    assert env.lineage.disposition(declaration_id=declaration.identity) == "UNKNOWN_SEND_OUTCOME"
    result = subject.NARQualifiedDebaResultV1(
        receipt.declaration_id, receipt.claim_id, receipt.identity, receipt.capture_id,
        receipt.canonical_deba_url, receipt.response_sha256, receipt.observed_at)
    with pytest.raises(subject.AcquisitionIntegrityError):
        subject.read_qualified_deba_bytes(result=result, lineage_archive=env.lineage, capture_archive=env.captures)
    assert env.transport.urls == []


def test_arbitrary_capture_response_service_is_rejected(env):
    class CustomCaptureService:
        def capture_response(self, **kwargs):
            pytest.fail("unreviewed service must never be invoked")
    with pytest.raises(subject.AcquisitionIntegrityError, match="exact reviewed live capture service"):
        subject.NARTrustedDebaAcquisitionApplication(
            target_archive=env.targets, lineage_archive=env.lineage,
            capture_archive=env.captures, capture_service=CustomCaptureService())
    assert env.transport.urls == []


def test_capture_service_subclass_is_rejected(env):
    class CustomCaptureService(NAROfficialLiveResponseCaptureService):
        def capture_response(self, **kwargs):
            pytest.fail("overridden service must never be invoked")
    service = CustomCaptureService(archive=env.captures, transport=env.transport, utc_clock=lambda: T0)
    with pytest.raises(subject.AcquisitionIntegrityError, match="exact reviewed live capture service"):
        subject.NARTrustedDebaAcquisitionApplication(
            target_archive=env.targets, lineage_archive=env.lineage,
            capture_archive=env.captures, capture_service=service)
    assert env.transport.urls == []


def test_same_bytes_parser_fanout_and_no_body_or_core_tables(env, monkeypatch):
    from scripts.parsers.horse_parser import HorseParser
    declaration, result = acquire(env)
    body = subject.read_qualified_deba_bytes(result=result, lineage_archive=env.lineage, capture_archive=env.captures)
    seen = []
    original = HorseParser.parse
    def spy(self, html, race_id):
        seen.append(html.encode("utf-8"))
        return original(self, html, race_id)
    monkeypatch.setattr(HorseParser, "parse", spy)
    HorseParser().parse(body.decode("utf-8", errors="strict"), 1)
    assert seen == [env.transport.body]
    tables = {r[0] for r in env.connections[2].execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert not tables & {"races", "horses", "historical_input_external_entries"}
    for table in tables:
        assert "response_body" not in {r[1] for r in env.connections[2].execute(f"PRAGMA table_info({table})")}
    assert env.transport.body.decode() not in str(env.connections[2].execute("SELECT payload FROM phase111_receipts").fetchall())


def test_declaration_and_capture_reload_order_is_observed(env, monkeypatch):
    events = env.events
    load_decl = env.lineage.load_declaration
    claim = env.lineage.acquire_claim
    load_capture = env.captures.load_capture
    publish = env.lineage._publish_receipt
    def decl(**kw):
        events.append("declaration_reload")
        return load_decl(**kw)
    def claimed(**kw):
        result = claim(**kw)
        events.append("claim_committed")
        return result
    def captured(self, **kw):
        events.append("capture_reload")
        return load_capture(**kw)
    def receipt(**kw):
        events.append("receipt")
        return publish(**kw)
    monkeypatch.setattr(env.lineage, "load_declaration", decl)
    monkeypatch.setattr(env.lineage, "acquire_claim", claimed)
    monkeypatch.setattr(type(env.captures), "load_capture", captured)
    monkeypatch.setattr(env.lineage, "_publish_receipt", receipt)
    acquire(env)
    assert events.index("declaration_reload") < events.index("claim_committed") < events.index("send")
    assert events.index("send") < events.index("capture_reload") < events.index("receipt")
