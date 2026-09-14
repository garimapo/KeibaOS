from __future__ import annotations

import ast
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path

import pytest

from scripts.simulation import nar_race_entry_status_raw_capture as raw_capture
from scripts.simulation import nar_race_entry_status_source_profile_diagnostics as profile_b
from scripts.simulation import nar_race_entry_status_source_profile_profile_a as profile_a
from scripts.simulation import nar_race_entry_status_source_profile_publication_contract as subject


UTC = timezone.utc
TARGET = raw_capture.NARRaceEntryStatusRaceIdentity("21", date(2025, 1, 1), 6)
DEBA_HREF = (
    "/KeibaWeb/TodayRaceInfo/DebaTable?"
    "k_babaCode=21&k_raceDate=2025%2F01%2F01&k_raceNo=6"
)
SAFE_SOURCE = b"<html><body><p>deliberately synthetic safe source</p></body></html>"


def _profile_a_source(number: str = "3") -> bytes:
    return (
        '<html><body><article class="raceCard"><section class="cardTable"><table>'
        f'<tr><td class="horseNum">{number}</td><td><a class="horseName" href="/horse/synthetic">horse</a></td></tr>'
        "</table></section></article></body></html>"
    ).encode("utf-8")


def _profile_b_source(*, status: str = "出走取消") -> bytes:
    return (
        '<html><body><section class="raceTable"><table>'
        f'<tr class="data"><td>6R</td><td><a href="{DEBA_HREF}">entry</a></td></tr>'
        "</table></section><table class=\"changeInfo\">"
        f'<tr class="data"><td>6R</td><td>14</td><td>x</td><td>{status}</td><td>x</td><td>x</td></tr>'
        "</table></body></html>"
    ).encode("utf-8")


def _request(page_kind: raw_capture.NARRaceEntryStatusPageKind) -> raw_capture.NARRaceEntryStatusRequestIdentity:
    return raw_capture.build_nar_race_entry_status_request_identity(
        page_kind=page_kind,
        day_scope=raw_capture.NARRaceEntryStatusDayScope(TARGET.baba_code, TARGET.race_date),
        request_race_no=(TARGET.race_no if page_kind is raw_capture.NARRaceEntryStatusPageKind.DEBA_TABLE else None),
    )


def _capture(
    page_kind: raw_capture.NARRaceEntryStatusPageKind,
    body: bytes,
    second_offset: int,
) -> raw_capture.NARRaceEntryStatusResponseCapture:
    request = _request(page_kind)
    instant = datetime(2026, 9, 15, 1, 2, second_offset, 123456, tzinfo=UTC)
    return raw_capture.NARRaceEntryStatusResponseCapture(
        request_identity=request,
        effective_url=request.canonical_request_url,
        response_body=body,
        charset="UTF-8",
        requested_at=instant,
        observed_at=instant + timedelta(microseconds=1),
        captured_at=instant + timedelta(microseconds=2),
        http_status=200,
        content_type="text/html; charset=UTF-8",
    )


def _bundle() -> raw_capture.NARRaceEntryStatusRawCaptureBundle:
    return raw_capture.NARRaceEntryStatusRawCaptureBundle(
        target_race_identity=TARGET,
        deba_table_capture=_capture(raw_capture.NARRaceEntryStatusPageKind.DEBA_TABLE, _profile_a_source(), 0),
        race_list_capture=_capture(raw_capture.NARRaceEntryStatusPageKind.RACE_LIST, _profile_b_source(), 1),
    )


def _authorities() -> tuple[
    profile_b.CaptureMetadataSummary,
    profile_a.ProfileADiagnostics,
    profile_b.ProfileBDiagnostics,
    subject.RawFixturePublicationSafety,
]:
    bundle = _bundle()
    capture = profile_b.summarize_nar_race_entry_status_capture_bundle(bundle=bundle)
    a = profile_a.diagnose_nar_race_entry_status_profile_a(
        deba_table_bytes=bundle.deba_table_capture.response_body,
        target=TARGET,
    )
    b = profile_b.diagnose_nar_race_entry_status_profile_b(
        race_list_bytes=bundle.race_list_capture.response_body,
        target=TARGET,
    )
    safety = subject.assess_nar_race_entry_status_raw_fixture_publication_safety(
        deba_table_bytes=SAFE_SOURCE,
        race_list_bytes=SAFE_SOURCE,
    )
    return capture, a, b, safety


def _contract() -> tuple[subject.FixtureSetV2, subject.QualificationV2, subject.SourceProfileManifestV2]:
    capture, a, b, safety = _authorities()
    fixture = subject.build_nar_race_entry_status_fixture_set_v2(target=TARGET, capture_summary=capture)
    qualification = subject.build_nar_race_entry_status_qualification_v2(
        target=TARGET,
        fixture_set=fixture,
        profile_a=a,
        profile_b=b,
    )
    manifest = subject.build_nar_race_entry_status_manifest_v2(
        fixture_set=fixture,
        qualification=qualification,
        publication_safety=safety,
    )
    return fixture, qualification, manifest


def _safety(source: bytes) -> subject.RawFixturePublicationSafety:
    return subject.assess_nar_race_entry_status_raw_fixture_publication_safety(
        deba_table_bytes=source,
        race_list_bytes=SAFE_SOURCE,
    )


def _category(result: subject.RawFixturePublicationSafety, name: str) -> subject.PublicationSafetyOutcome:
    return next(item.outcome for item in result.category_results if item.identifier.value == name)


def test_minimal_sources_are_safe_in_exact_category_order() -> None:
    result = _safety(SAFE_SOURCE)

    assert tuple(item.identifier.value for item in result.category_results) == tuple(subject.PublicationSafetyCategory)
    assert all(item.outcome is subject.PublicationSafetyOutcome.SAFE for item in result.category_results)
    assert result.result is subject.PublicationSafetyOutcome.SAFE
    assert result.raw_fixture_publication_safe is True


@pytest.mark.parametrize(
    ("source", "category"),
    [
        (b'<html><body><input name="authorization" value="sensitive-value"></body></html>', "NO_AUTHENTICATION_MATERIAL"),
        (b'<html><body><input name="session_id" value="sensitive-value"></body></html>', "NO_COOKIE_OR_SESSION_SECRET"),
        (b'<html><body><input name="csrf" value="sensitive-value"></body></html>', "NO_CSRF_OR_SECRET_TOKEN"),
        (b'<html><body><input name="account_id" value="sensitive-value"></body></html>', "NO_USER_ACCOUNT_IDENTIFIER"),
        (b'<html><body><input name="preference" value="sensitive-value"></body></html>', "NO_PERSONALIZATION_IDENTIFIER"),
    ],
)
def test_each_frozen_prohibited_category_is_unsafe_without_secret_echo(source: bytes, category: str) -> None:
    result = _safety(source)

    assert _category(result, category) is subject.PublicationSafetyOutcome.UNSAFE
    assert result.result is subject.PublicationSafetyOutcome.UNSAFE
    assert result.raw_fixture_publication_safe is False
    assert b"sensitive-value" not in result.canonical_bytes()
    assert b"<html" not in result.canonical_bytes()


def test_multiple_categories_and_header_style_lines_fail_closed() -> None:
    source = b"<html><body>\nauthorization: secret\ncookie: secret\n</body></html>"
    result = _safety(source)

    assert _category(result, "NO_AUTHENTICATION_MATERIAL") is subject.PublicationSafetyOutcome.UNSAFE
    assert _category(result, "NO_COOKIE_OR_SESSION_SECRET") is subject.PublicationSafetyOutcome.UNSAFE
    assert result.result is subject.PublicationSafetyOutcome.UNSAFE


def test_empty_sensitive_field_and_malformed_sensitive_query_are_ambiguous() -> None:
    empty = _safety(b'<html><body><input name="csrf" value=""></body></html>')
    malformed = _safety(b'<html><body><a href="/x?csrf=%GG">x</a></body></html>')

    assert _category(empty, "NO_CSRF_OR_SECRET_TOKEN") is subject.PublicationSafetyOutcome.AMBIGUOUS
    assert empty.result is subject.PublicationSafetyOutcome.AMBIGUOUS
    assert _category(malformed, "NO_CSRF_OR_SECRET_TOKEN") is subject.PublicationSafetyOutcome.AMBIGUOUS
    assert malformed.result is subject.PublicationSafetyOutcome.AMBIGUOUS


@pytest.mark.parametrize("source", [b"\xff", b"<html><body><article></body></html>"])
def test_invalid_encoding_or_malformed_source_is_unsupported(source: bytes) -> None:
    result = _safety(source)

    assert all(item.outcome is subject.PublicationSafetyOutcome.UNSUPPORTED for item in result.category_results)
    assert result.result is subject.PublicationSafetyOutcome.UNSUPPORTED
    assert result.raw_fixture_publication_safe is False


def test_safety_is_deterministic_and_retains_no_raw_or_arbitrary_url() -> None:
    marker = "private-visible-marker"
    source = f'<html><body><a href="https://invalid.example/path?csrf={marker}">x</a></body></html>'.encode()
    first = _safety(source)
    second = _safety(source)

    assert first == second
    assert first.canonical_bytes() == second.canonical_bytes()
    assert marker.encode() not in first.canonical_bytes()
    assert b"https://" not in first.canonical_bytes()


def test_fixture_set_v2_exact_payload_canonical_identity_and_validation() -> None:
    capture, _, _, _ = _authorities()
    fixture = subject.build_nar_race_entry_status_fixture_set_v2(target=TARGET, capture_summary=capture)
    payload = fixture.to_canonical_dict()
    expected = {
        "schema": subject.FIXTURE_SET_SCHEMA,
        "schema_version": 2,
        "provider": "NAR",
        "target": {"baba_code": "21", "race_date": "2025-01-01", "race_no": 6},
        "documents": [
            {
                "role": role,
                "fixture_relative_path": (
                    "tests/fixtures/nar_race_entry_status/source_profiles/v2/"
                    f"baba_21__2025-01-01__race_06/{filename}"
                ),
                "request_identity": document.request_identity,
                "capture_identity": document.capture_identity,
                "response_sha256": document.response_sha256,
                "response_byte_length": document.response_byte_length,
                "requested_at": document.requested_at,
                "observed_at": document.observed_at,
                "captured_at": document.captured_at,
                "effective_url_matches_canonical": True,
            }
            for role, filename, document in (
                ("deba_table", "deba_table.html", capture.deba_table),
                ("race_list", "race_list.html", capture.race_list),
            )
        ],
        "closed_bundle_identity": capture.closed_bundle_identity,
    }

    assert payload == expected
    assert fixture.canonical_bytes() == json.dumps(expected, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    assert fixture.identity.startswith(subject.FIXTURE_ID_PREFIX)
    assert fixture.identity == subject.build_nar_race_entry_status_fixture_set_v2(target=TARGET, capture_summary=capture).identity
    assert subject.validate_nar_race_entry_status_fixture_set_v2(
        value=fixture,
        target=TARGET,
        capture_summary=capture,
    ) is fixture


@pytest.mark.parametrize("field", ["response_sha256", "response_byte_length", "capture_identity"])
def test_changed_formal_capture_evidence_changes_fixture_identity(field: str) -> None:
    capture, _, _, _ = _authorities()
    fixture = subject.build_nar_race_entry_status_fixture_set_v2(target=TARGET, capture_summary=capture)
    changes: dict[str, object] = {
        "response_sha256": "f" * 64,
        "response_byte_length": capture.deba_table.response_byte_length + 1,
        "capture_identity": "nar-race-entry-status-capture-v1:" + "f" * 64,
    }
    changed_document = replace(capture.deba_table, **{field: changes[field]})
    changed_capture = replace(capture, deba_table=changed_document)
    changed = subject.build_nar_race_entry_status_fixture_set_v2(target=TARGET, capture_summary=changed_capture)

    assert changed.identity != fixture.identity
    with pytest.raises(subject.SourceProfilePublicationContractError):
        subject.validate_nar_race_entry_status_fixture_set_v2(
            value=fixture,
            target=TARGET,
            capture_summary=changed_capture,
        )


def test_capture_request_identity_must_match_exact_target() -> None:
    capture, _, _, _ = _authorities()
    other_target = raw_capture.NARRaceEntryStatusRaceIdentity("22", TARGET.race_date, TARGET.race_no)

    with pytest.raises(subject.SourceProfilePublicationContractError, match="does not match target"):
        subject.build_nar_race_entry_status_fixture_set_v2(target=other_target, capture_summary=capture)


def test_operational_metadata_and_raw_source_are_absent_from_identity_payloads() -> None:
    fixture, qualification, _ = _contract()
    combined = fixture.canonical_bytes() + qualification.canonical_bytes()

    assert b"run_id" not in combined
    assert b"temp_path" not in combined
    assert b"repository_path" not in combined
    assert b"<html" not in combined
    assert b"synthetic safe source" not in combined


def test_qualification_v2_exact_payload_identity_and_phase53_interoperability() -> None:
    capture, a, b, _ = _authorities()
    fixture = subject.build_nar_race_entry_status_fixture_set_v2(target=TARGET, capture_summary=capture)
    qualification = subject.build_nar_race_entry_status_qualification_v2(
        target=TARGET,
        fixture_set=fixture,
        profile_a=a,
        profile_b=b,
    )
    payload = qualification.to_canonical_dict()

    assert payload == {
        "schema": subject.QUALIFICATION_SCHEMA,
        "schema_version": 2,
        "provider": "NAR",
        "target": {"baba_code": "21", "race_date": "2025-01-01", "race_no": 6},
        "fixture_set_identity": fixture.identity,
        "profile_a": a.to_canonical_dict(),
        "profile_b": b.to_canonical_dict(),
        "market_eligibility": "UNSUPPORTED",
    }
    assert qualification.identity.startswith(subject.QUALIFICATION_ID_PREFIX)
    assert payload["profile_b"]["terminal_semantic"] == "EXPLICIT_WITHDRAWAL_PRESENT"  # type: ignore[index]
    assert len(payload["profile_b"]["predicate_results"]) == 6  # type: ignore[index]
    assert subject.validate_nar_race_entry_status_qualification_v2(
        value=qualification,
        target=TARGET,
        fixture_set=fixture,
        profile_a=a,
        profile_b=b,
    ) is qualification


def test_profile_a_or_profile_b_semantic_change_changes_qualification_identity() -> None:
    capture, a, b, _ = _authorities()
    fixture = subject.build_nar_race_entry_status_fixture_set_v2(target=TARGET, capture_summary=capture)
    baseline = subject.build_nar_race_entry_status_qualification_v2(
        target=TARGET, fixture_set=fixture, profile_a=a, profile_b=b
    )
    blocked_a = profile_a.diagnose_nar_race_entry_status_profile_a(
        deba_table_bytes=_profile_a_source("14"), target=TARGET
    )
    blocked_b = profile_b.diagnose_nar_race_entry_status_profile_b(
        race_list_bytes=_profile_b_source(status="出走"), target=TARGET
    )

    changed_a = subject.build_nar_race_entry_status_qualification_v2(
        target=TARGET, fixture_set=fixture, profile_a=blocked_a, profile_b=b
    )
    changed_b = subject.build_nar_race_entry_status_qualification_v2(
        target=TARGET, fixture_set=fixture, profile_a=a, profile_b=blocked_b
    )
    assert changed_a.identity != baseline.identity
    assert changed_b.identity != baseline.identity


def test_manifest_v2_closed_schema_canonical_build_and_independent_validation(tmp_path: Path) -> None:
    fixture, qualification, manifest = _contract()
    canonical = manifest.canonical_bytes()
    path = tmp_path / "manifest.json"
    path.write_bytes(canonical)

    payload = manifest.to_canonical_dict()
    assert set(payload) == {
        "manifest_schema",
        "manifest_schema_version",
        "acquisition_semantics",
        "provider",
        "target",
        "documents",
        "closed_bundle_identity",
        "fixture_set_identity",
        "qualification_identity",
        "publication_safety",
        "profile_a",
        "profile_b",
        "market_eligibility",
    }
    assert payload["manifest_schema_version"] == 2
    assert payload["market_eligibility"] == "UNSUPPORTED"
    assert canonical == json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    assert subject.validate_nar_race_entry_status_manifest_v2(
        manifest_bytes=path.read_bytes(),
        fixture_set=fixture,
        qualification=qualification,
        publication_safety=manifest.publication_safety,
    ).canonical_bytes() == canonical


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: p.__setitem__("manifest_schema_version", 1),
        lambda p: p.pop("provider"),
        lambda p: p.__setitem__("run_id", "operational"),
        lambda p: p.__setitem__("fixture_set_identity", "wrong"),
        lambda p: p.__setitem__("qualification_identity", "wrong"),
        lambda p: p["documents"][0].__setitem__("response_sha256", "f" * 64),
        lambda p: p["documents"][0].__setitem__("response_byte_length", 1),
        lambda p: p.__setitem__("market_eligibility", "MARKET_ELIGIBLE"),
    ],
)
def test_manifest_rejects_schema_provenance_identity_and_disclaimer_tampering(mutate: object) -> None:
    fixture, qualification, manifest = _contract()
    payload = manifest.to_canonical_dict()
    mutate(payload)  # type: ignore[operator]
    tampered = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()

    with pytest.raises(subject.SourceProfilePublicationContractError):
        subject.validate_nar_race_entry_status_manifest_v2(
            manifest_bytes=tampered,
            fixture_set=fixture,
            qualification=qualification,
            publication_safety=manifest.publication_safety,
        )


def test_manifest_rejects_noncanonical_bytes_and_nonqualified_or_unsafe_authority() -> None:
    fixture, qualification, manifest = _contract()
    noncanonical = json.dumps(manifest.to_canonical_dict(), ensure_ascii=False, indent=2).encode()
    with pytest.raises(subject.SourceProfilePublicationContractError, match="noncanonical"):
        subject.validate_nar_race_entry_status_manifest_v2(
            manifest_bytes=noncanonical,
            fixture_set=fixture,
            qualification=qualification,
            publication_safety=manifest.publication_safety,
        )

    unsafe = _safety(b'<html><body><input name="csrf" value="secret"></body></html>')
    with pytest.raises(subject.SourceProfilePublicationContractError, match="publication-safe"):
        subject.build_nar_race_entry_status_manifest_v2(
            fixture_set=fixture,
            qualification=qualification,
            publication_safety=unsafe,
        )


def test_mapping_insertion_order_does_not_change_canonical_manifest_bytes() -> None:
    _, _, manifest = _contract()
    payload = manifest.to_canonical_dict()
    reversed_mapping = dict(reversed(tuple(payload.items())))

    assert json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode() == json.dumps(
        reversed_mapping, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()


def test_programmer_type_violations_fail_closed() -> None:
    capture, _, _, _ = _authorities()
    with pytest.raises(subject.SourceProfilePublicationContractError):
        subject.build_nar_race_entry_status_fixture_set_v2(target=object(), capture_summary=capture)  # type: ignore[arg-type]
    with pytest.raises(subject.SourceProfilePublicationContractError):
        subject.assess_nar_race_entry_status_raw_fixture_publication_safety(
            deba_table_bytes=bytearray(b"x"), race_list_bytes=b"x"  # type: ignore[arg-type]
        )


def test_module_has_no_network_process_database_clock_or_filesystem_write_path() -> None:
    tree = ast.parse(Path(subject.__file__).read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr)

    assert imported_roots.isdisjoint({"requests", "urllib3", "socket", "subprocess", "sqlite3"})
    assert calls.isdisjoint({"open", "write_bytes", "write_text", "now", "utcnow", "time"})
