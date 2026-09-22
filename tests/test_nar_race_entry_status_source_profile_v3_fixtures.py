from __future__ import annotations

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
DEBA_RELATIVE_PATH = "tests/fixtures/nar_race_entry_status/source_profiles/v3/baba_21__2025-01-01__race_06/deba_table.html"
RACE_LIST_RELATIVE_PATH = "tests/fixtures/nar_race_entry_status/source_profiles/v3/baba_21__2025-01-01__race_06/race_list.html"
MANIFEST_RELATIVE_PATH = "tests/fixtures/nar_race_entry_status/source_profiles/v3/baba_21__2025-01-01__race_06/manifest.json"
DEBA_PATH = REPOSITORY_ROOT / DEBA_RELATIVE_PATH
RACE_LIST_PATH = REPOSITORY_ROOT / RACE_LIST_RELATIVE_PATH
MANIFEST_PATH = REPOSITORY_ROOT / MANIFEST_RELATIVE_PATH
EXPECTED_DEBA_SHA256 = "6c9aa3ea614c17e14f0e7a5050190ca923445925d67f8e61e71db95e87c87727"
EXPECTED_DEBA_BYTE_LENGTH = 313317
EXPECTED_RACELIST_SHA256 = "1eb363621c7a152929765ff7ffecabea2d7cf15283d45fa9c31036527c0b53a1"
EXPECTED_RACELIST_BYTE_LENGTH = 66307
EXPECTED_MANIFEST_SHA256 = "3ca36ed4cec1002e0440fb02e466f40dd7f4d74ffb7c0bdf7b55be2271af321d"
EXPECTED_MANIFEST_BYTE_LENGTH = 4254
EXPECTED_FIXTURE_SET_IDENTITY = "nar-race-entry-status-source-profile-fixture-set-v3:11f18aae600df59ab90ce9cd3dd3614ff250698d783bcd96e6917cc38a8ab225"
EXPECTED_QUALIFICATION_IDENTITY = "nar-race-entry-status-source-profile-qualification-v3:a7f0ba5ed66a71f9785c80b1ba1b5f556b2328d09ead597839cc068a84b0d3ff"
EXPECTED_TARGET = {"baba_code":"21","race_date":"2025-01-01","race_no":6}
EXPECTED_MARKET_ELIGIBILITY = "UNSUPPORTED"
EXPECTED_ACQUISITION_SEMANTICS = "CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET"
EXPECTED_REQUIREMENTS = ('EXACT_DEBA_SHA256', 'EXACT_DEBA_BYTE_LENGTH', 'EXACT_RACELIST_SHA256', 'EXACT_RACELIST_BYTE_LENGTH', 'EXACT_TARGET', 'DOCUMENT_ROLE_ORDER', 'FIXTURE_SET_V3_RECOMPUTATION', 'QUALIFICATION_V3_RECOMPUTATION', 'MANIFEST_V3_CANONICAL_SERIALIZATION', 'MANIFEST_V3_VALIDATION', 'PUBLICATION_SAFETY_V3_SAFE', 'PROFILE_A_V3_QUALIFIED', 'PROFILE_B_V2_QUALIFIED', 'PROFILE_B_ALL_SIX_PREDICATES_PASS', 'PROFILE_B_TARGET_SCHEDULE_COUNT_ONE', 'PHASE66_DIRECT_SCHEDULE_COUNT_ONE', 'PROFILE_B_PHASE66_STRUCTURAL_CONSISTENCY', 'PROFILE_B_EXPLICIT_WITHDRAWAL_PRESENT', 'CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET', 'MARKET_ELIGIBILITY_UNSUPPORTED', 'NO_NETWORK')


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
