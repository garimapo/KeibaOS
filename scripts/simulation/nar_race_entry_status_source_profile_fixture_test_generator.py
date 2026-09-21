"""Pure deterministic source generator for the V3 source-profile fixture test."""

from __future__ import annotations

from hashlib import sha256
import json

from scripts.simulation.nar_race_entry_status_source_profile_publication_contract import (
    ACQUISITION_SEMANTICS,
    MARKET_ELIGIBILITY,
    FixtureSetV3,
    PublicationSafetyOutcome,
    QualificationV3,
    RawFixturePublicationSafetyV3,
    SourceProfileManifestV3,
    validate_nar_race_entry_status_fixture_set_v3,
    validate_nar_race_entry_status_manifest_v3,
    validate_nar_race_entry_status_qualification_v3,
)
from scripts.simulation.nar_race_entry_status_source_profile_publication_plan import (
    EXPECTED_DEBA_TABLE_PATH_V3,
    EXPECTED_MANIFEST_PATH_V3,
    EXPECTED_RACE_LIST_PATH_V3,
    FUTURE_OFFICIAL_FIXTURE_TEST_REQUIREMENTS_V3,
    SourceProfilePublicationPlanV3,
    validate_nar_race_entry_status_source_profile_publication_plan_v3,
)


MAX_GENERATED_FIXTURE_TEST_BYTES = 65536


class V3FixtureTestGenerationError(ValueError):
    """The requested source is outside the reviewed V3 generation authority."""


def _error(message: str) -> V3FixtureTestGenerationError:
    return V3FixtureTestGenerationError(message)


def _exact_source_bytes(value: object, name: str) -> bytes:
    if type(value) is not bytes:
        raise _error(f"{name} must be exact bytes")
    if not value:
        raise _error(f"{name} must be nonempty")
    try:
        value.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise _error(f"{name} must be strict UTF-8") from error
    return value


def _validated_authority(
    *,
    deba_table_bytes: object,
    race_list_bytes: object,
    manifest: object,
    publication_plan: object,
) -> tuple[bytes, bytes, SourceProfileManifestV3, SourceProfilePublicationPlanV3, dict[str, object]]:
    deba = _exact_source_bytes(deba_table_bytes, "deba_table_bytes")
    race_list = _exact_source_bytes(race_list_bytes, "race_list_bytes")
    if type(manifest) is not SourceProfileManifestV3:
        raise _error("manifest must be exact SourceProfileManifestV3")
    if type(publication_plan) is not SourceProfilePublicationPlanV3:
        raise _error("publication_plan must be exact SourceProfilePublicationPlanV3")

    fixture_set = manifest.fixture_set
    qualification = manifest.qualification
    safety = manifest.publication_safety
    if type(fixture_set) is not FixtureSetV3:
        raise _error("manifest fixture_set must be exact FixtureSetV3")
    if type(qualification) is not QualificationV3:
        raise _error("manifest qualification must be exact QualificationV3")
    if type(safety) is not RawFixturePublicationSafetyV3:
        raise _error("manifest safety must be exact RawFixturePublicationSafetyV3")
    try:
        validate_nar_race_entry_status_fixture_set_v3(
            value=fixture_set,
            target=fixture_set.target,
            capture_summary=fixture_set.capture_summary,
        )
        validate_nar_race_entry_status_qualification_v3(
            value=qualification,
            target=fixture_set.target,
            fixture_set=fixture_set,
            profile_a=qualification.profile_a,
            profile_b=qualification.profile_b,
        )
        validate_nar_race_entry_status_manifest_v3(
            manifest_bytes=manifest.canonical_bytes(),
            fixture_set=fixture_set,
            qualification=qualification,
            publication_safety=safety,
        )
        validate_nar_race_entry_status_source_profile_publication_plan_v3(
            value=publication_plan,
            fixture_set=fixture_set,
        )
    except Exception as error:
        raise _error("formal V3 authority validation failed") from error

    payload = manifest.to_canonical_dict()
    if payload.get("acquisition_semantics") != ACQUISITION_SEMANTICS:
        raise _error("manifest acquisition semantics are invalid")
    if payload.get("market_eligibility") != MARKET_ELIGIBILITY or MARKET_ELIGIBILITY != "UNSUPPORTED":
        raise _error("manifest market eligibility is invalid")
    if qualification.profile_a.overall_result != "QUALIFIED":
        raise _error("Profile-A v3 must be QUALIFIED")
    if qualification.profile_b.overall_result != "QUALIFIED":
        raise _error("Profile-B v2 must be QUALIFIED")
    if safety.result is not PublicationSafetyOutcome.SAFE or not safety.raw_fixture_publication_safe:
        raise _error("Safety v3 must be SAFE")
    if (
        type(FUTURE_OFFICIAL_FIXTURE_TEST_REQUIREMENTS_V3) is not tuple
        or len(FUTURE_OFFICIAL_FIXTURE_TEST_REQUIREMENTS_V3) != 21
        or len(set(FUTURE_OFFICIAL_FIXTURE_TEST_REQUIREMENTS_V3)) != 21
        or any(type(item) is not str or not item for item in FUTURE_OFFICIAL_FIXTURE_TEST_REQUIREMENTS_V3)
    ):
        raise _error("frozen V3 fixture-test requirements are invalid")

    documents = payload.get("documents")
    if type(documents) is not list or len(documents) != 2:
        raise _error("manifest must contain exactly two documents")
    expected = (
        ("deba_table", EXPECTED_DEBA_TABLE_PATH_V3, deba),
        ("race_list", EXPECTED_RACE_LIST_PATH_V3, race_list),
    )
    for document, (role, path, raw_bytes) in zip(documents, expected, strict=True):
        if type(document) is not dict:
            raise _error("manifest document must be an exact object")
        if document.get("role") != role or document.get("fixture_relative_path") != path:
            raise _error("manifest document role or path is invalid")
        if document.get("response_sha256") != sha256(raw_bytes).hexdigest():
            raise _error(f"{role} SHA-256 contradicts exact bytes")
        if document.get("response_byte_length") != len(raw_bytes):
            raise _error(f"{role} byte length contradicts exact bytes")
    if publication_plan.future_live_paths[:3] != (
        EXPECTED_DEBA_TABLE_PATH_V3,
        EXPECTED_RACE_LIST_PATH_V3,
        EXPECTED_MANIFEST_PATH_V3,
    ):
        raise _error("publication plan paths contradict manifest authority")
    return deba, race_list, manifest, publication_plan, payload


_TEST_TEMPLATE = '''from __future__ import annotations

import ast
from datetime import date
from hashlib import sha256
import json
from pathlib import Path

from scripts.simulation import nar_race_entry_status_raw_capture as raw_capture
from scripts.simulation import nar_race_entry_status_source_profile_diagnostics as profile_b
from scripts.simulation import nar_race_entry_status_source_profile_profile_a as profile_a
from scripts.simulation import nar_race_entry_status_source_profile_publication_contract as contract
from scripts.simulation import nar_race_entry_status_source_profile_publication_plan as publication_plan
from scripts.simulation import nar_race_entry_status_source_profile_structural_recovery_diagnostics as phase66


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEBA_RELATIVE_PATH = @@DEBA_PATH@@
RACE_LIST_RELATIVE_PATH = @@RACE_PATH@@
MANIFEST_RELATIVE_PATH = @@MANIFEST_PATH@@
DEBA_PATH = REPOSITORY_ROOT / DEBA_RELATIVE_PATH
RACE_LIST_PATH = REPOSITORY_ROOT / RACE_LIST_RELATIVE_PATH
MANIFEST_PATH = REPOSITORY_ROOT / MANIFEST_RELATIVE_PATH
EXPECTED_DEBA_SHA256 = @@DEBA_SHA@@
EXPECTED_DEBA_BYTE_LENGTH = @@DEBA_LENGTH@@
EXPECTED_RACELIST_SHA256 = @@RACE_SHA@@
EXPECTED_RACELIST_BYTE_LENGTH = @@RACE_LENGTH@@
EXPECTED_MANIFEST_SHA256 = @@MANIFEST_SHA@@
EXPECTED_MANIFEST_BYTE_LENGTH = @@MANIFEST_LENGTH@@
EXPECTED_FIXTURE_SET_IDENTITY = @@FIXTURE_ID@@
EXPECTED_QUALIFICATION_IDENTITY = @@QUALIFICATION_ID@@
EXPECTED_TARGET = @@TARGET@@
EXPECTED_MARKET_ELIGIBILITY = @@MARKET@@
EXPECTED_ACQUISITION_SEMANTICS = @@SEMANTICS@@
EXPECTED_REQUIREMENTS = @@REQUIREMENTS@@


def _document_metadata(document: dict[str, object], role: str) -> profile_b.CaptureDocumentMetadata:
    assert document["role"] == role
    return profile_b.CaptureDocumentMetadata(
        document_role=role,
        request_identity=document["request_identity"],
        capture_identity=document["capture_identity"],
        response_sha256=document["response_sha256"],
        response_byte_length=document["response_byte_length"],
        requested_at=document["requested_at"],
        observed_at=document["observed_at"],
        captured_at=document["captured_at"],
        effective_url_matches_canonical=document["effective_url_matches_canonical"],
    )


def _recompute() -> dict[str, object]:
    deba = DEBA_PATH.read_bytes()
    race_list = RACE_LIST_PATH.read_bytes()
    manifest_bytes = MANIFEST_PATH.read_bytes()
    assert sha256(deba).hexdigest() == EXPECTED_DEBA_SHA256
    assert len(deba) == EXPECTED_DEBA_BYTE_LENGTH
    assert sha256(race_list).hexdigest() == EXPECTED_RACELIST_SHA256
    assert len(race_list) == EXPECTED_RACELIST_BYTE_LENGTH
    assert sha256(manifest_bytes).hexdigest() == EXPECTED_MANIFEST_SHA256
    assert len(manifest_bytes) == EXPECTED_MANIFEST_BYTE_LENGTH
    payload = json.loads(manifest_bytes.decode("utf-8", errors="strict"))
    assert payload["target"] == EXPECTED_TARGET
    assert payload["provider"] == "NAR"
    assert payload["market_eligibility"] == EXPECTED_MARKET_ELIGIBILITY
    assert payload["acquisition_semantics"] == EXPECTED_ACQUISITION_SEMANTICS
    documents = payload["documents"]
    assert [item["role"] for item in documents] == ["deba_table", "race_list"]
    assert [item["fixture_relative_path"] for item in documents] == [
        DEBA_RELATIVE_PATH,
        RACE_LIST_RELATIVE_PATH,
    ]
    target = raw_capture.NARRaceEntryStatusRaceIdentity(
        EXPECTED_TARGET["baba_code"],
        date.fromisoformat(EXPECTED_TARGET["race_date"]),
        EXPECTED_TARGET["race_no"],
    )
    capture_summary = profile_b.CaptureMetadataSummary(
        deba_table=_document_metadata(documents[0], "deba_table"),
        race_list=_document_metadata(documents[1], "race_list"),
        closed_bundle_identity=payload["closed_bundle_identity"],
    )
    profile_a_result = profile_a.diagnose_nar_race_entry_status_profile_a_v3(
        deba_table_bytes=deba,
        target=target,
    )
    profile_b_result = profile_b.diagnose_nar_race_entry_status_profile_b_v2(
        race_list_bytes=race_list,
        target=target,
    )
    safety = contract.assess_nar_race_entry_status_raw_fixture_publication_safety_v3(
        deba_table_bytes=deba,
        race_list_bytes=race_list,
    )
    fixture_set = contract.build_nar_race_entry_status_fixture_set_v3(
        target=target,
        capture_summary=capture_summary,
    )
    qualification = contract.build_nar_race_entry_status_qualification_v3(
        target=target,
        fixture_set=fixture_set,
        profile_a=profile_a_result,
        profile_b=profile_b_result,
    )
    manifest = contract.build_nar_race_entry_status_manifest_v3(
        fixture_set=fixture_set,
        qualification=qualification,
        publication_safety=safety,
    )
    plan = publication_plan.build_nar_race_entry_status_source_profile_publication_plan_v3(
        fixture_set=fixture_set,
    )
    ancestry = phase66.diagnose_nar_race_entry_status_profile_b_candidate_ancestry_recovery(
        race_list_bytes=race_list,
        target=target,
    )
    return {
        "deba": deba,
        "race_list": race_list,
        "manifest_bytes": manifest_bytes,
        "payload": payload,
        "profile_a": profile_a_result,
        "profile_b": profile_b_result,
        "safety": safety,
        "fixture_set": fixture_set,
        "qualification": qualification,
        "manifest": manifest,
        "plan": plan,
        "ancestry": ancestry,
    }


def test_exact_documents_target_and_role_order() -> None:
    result = _recompute()
    assert result["payload"]["target"] == EXPECTED_TARGET
    assert sha256(result["deba"]).hexdigest() == EXPECTED_DEBA_SHA256
    assert len(result["deba"]) == EXPECTED_DEBA_BYTE_LENGTH
    assert sha256(result["race_list"]).hexdigest() == EXPECTED_RACELIST_SHA256
    assert len(result["race_list"]) == EXPECTED_RACELIST_BYTE_LENGTH


def test_v3_authority_recomputation_and_manifest_validation() -> None:
    result = _recompute()
    fixture_set = result["fixture_set"]
    qualification = result["qualification"]
    manifest = result["manifest"]
    assert fixture_set.identity == EXPECTED_FIXTURE_SET_IDENTITY
    assert qualification.identity == EXPECTED_QUALIFICATION_IDENTITY
    assert result["payload"]["fixture_set_identity"] == EXPECTED_FIXTURE_SET_IDENTITY
    assert result["payload"]["qualification_identity"] == EXPECTED_QUALIFICATION_IDENTITY
    assert manifest.canonical_bytes() == result["manifest_bytes"]
    assert contract.validate_nar_race_entry_status_manifest_v3(
        manifest_bytes=result["manifest_bytes"],
        fixture_set=fixture_set,
        qualification=qualification,
        publication_safety=result["safety"],
    ) == manifest
    assert publication_plan.validate_nar_race_entry_status_source_profile_publication_plan_v3(
        value=result["plan"],
        fixture_set=fixture_set,
    ) == result["plan"]


def test_v3_safety_profile_a_profile_b_and_structural_consistency() -> None:
    result = _recompute()
    profile_a_result = result["profile_a"]
    profile_b_result = result["profile_b"]
    safety = result["safety"]
    ancestry = result["ancestry"]
    assert safety.result is contract.PublicationSafetyOutcome.SAFE
    assert safety.raw_fixture_publication_safe is True
    assert all(item.outcome is contract.PublicationSafetyOutcome.SAFE for item in safety.category_results)
    assert profile_a_result.overall_result == "QUALIFIED"
    assert len(profile_a_result.predicate_results) == 3
    assert all(item.outcome.value == "PASS" for item in profile_a_result.predicate_results)
    assert profile_b_result.overall_result == "QUALIFIED"
    assert len(profile_b_result.predicate_results) == 6
    assert all(item.outcome.value == "PASS" for item in profile_b_result.predicate_results)
    profile_b_schedule_count = profile_b_result.predicate_results[1].safe_fields["target_6r_row_count"]
    direct_schedule_count = sum(
        item.direct_schedule_table_descendant for item in ancestry.candidate_results
    )
    change_info_count = sum(item.inside_change_info_table for item in ancestry.candidate_results)
    assert profile_b_schedule_count == 1
    assert ancestry.target_candidate_count == 2
    assert direct_schedule_count == 1
    assert change_info_count == 1
    assert profile_b_schedule_count == direct_schedule_count
    assert profile_b_result.to_canonical_dict()["terminal_semantic"] == "EXPLICIT_WITHDRAWAL_PRESENT"


def test_frozen_requirements_and_generated_test_are_no_network() -> None:
    assert publication_plan.FUTURE_OFFICIAL_FIXTURE_TEST_REQUIREMENTS_V3 == EXPECTED_REQUIREMENTS
    assert len(EXPECTED_REQUIREMENTS) == 21
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    forbidden_imports = {"requests", "httpx", "urllib", "socket", "subprocess"}
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported.isdisjoint(forbidden_imports)
'''


def _json_literal(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def render_nar_race_entry_status_source_profile_v3_fixture_test(
    *,
    deba_table_bytes: bytes,
    race_list_bytes: bytes,
    manifest: SourceProfileManifestV3,
    publication_plan: SourceProfilePublicationPlanV3,
) -> bytes:
    """Render the exact portable V3 fixture regression test."""

    deba, race_list, canonical_manifest, _plan, payload = _validated_authority(
        deba_table_bytes=deba_table_bytes,
        race_list_bytes=race_list_bytes,
        manifest=manifest,
        publication_plan=publication_plan,
    )
    manifest_bytes = canonical_manifest.canonical_bytes()
    replacements = {
        "@@DEBA_PATH@@": _json_literal(EXPECTED_DEBA_TABLE_PATH_V3),
        "@@RACE_PATH@@": _json_literal(EXPECTED_RACE_LIST_PATH_V3),
        "@@MANIFEST_PATH@@": _json_literal(EXPECTED_MANIFEST_PATH_V3),
        "@@DEBA_SHA@@": _json_literal(sha256(deba).hexdigest()),
        "@@DEBA_LENGTH@@": str(len(deba)),
        "@@RACE_SHA@@": _json_literal(sha256(race_list).hexdigest()),
        "@@RACE_LENGTH@@": str(len(race_list)),
        "@@MANIFEST_SHA@@": _json_literal(sha256(manifest_bytes).hexdigest()),
        "@@MANIFEST_LENGTH@@": str(len(manifest_bytes)),
        "@@FIXTURE_ID@@": _json_literal(canonical_manifest.fixture_set.identity),
        "@@QUALIFICATION_ID@@": _json_literal(canonical_manifest.qualification.identity),
        "@@TARGET@@": _json_literal(payload["target"]),
        "@@MARKET@@": _json_literal(MARKET_ELIGIBILITY),
        "@@SEMANTICS@@": _json_literal(ACQUISITION_SEMANTICS),
        "@@REQUIREMENTS@@": repr(FUTURE_OFFICIAL_FIXTURE_TEST_REQUIREMENTS_V3),
    }
    source = _TEST_TEMPLATE
    for marker, value in replacements.items():
        if source.count(marker) != 1:
            raise _error("internal generated-source marker is invalid")
        source = source.replace(marker, value)
    if "@@" in source:
        raise _error("generated source contains an unresolved marker")
    try:
        encoded = source.encode("utf-8", errors="strict")
        encoded.decode("utf-8", errors="strict")
        compile(encoded, "<generated-v3-fixture-test>", "exec")
    except (UnicodeError, SyntaxError) as error:
        raise _error("generated source is not canonical compilable UTF-8") from error
    if encoded.startswith(b"\xef\xbb\xbf") or b"\r" in encoded:
        raise _error("generated source must be BOM-free LF-only bytes")
    if len(encoded) > MAX_GENERATED_FIXTURE_TEST_BYTES:
        raise _error("generated source exceeds the reviewed byte limit")
    return encoded


__all__ = (
    "MAX_GENERATED_FIXTURE_TEST_BYTES",
    "V3FixtureTestGenerationError",
    "render_nar_race_entry_status_source_profile_v3_fixture_test",
)
