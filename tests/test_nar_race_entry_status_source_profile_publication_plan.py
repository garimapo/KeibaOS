from __future__ import annotations

import ast
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import subprocess

import pytest

from scripts.simulation import nar_race_entry_status_raw_capture as raw_capture
from scripts.simulation import nar_race_entry_status_source_profile_diagnostics as profile_b
from scripts.simulation import nar_race_entry_status_source_profile_publication_contract as publication_contract
from scripts.simulation import nar_race_entry_status_source_profile_publication_plan as subject


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
UTC = timezone.utc
FROZEN_TARGET = raw_capture.NARRaceEntryStatusRaceIdentity("21", date(2025, 1, 1), 6)


def _request(
    target: raw_capture.NARRaceEntryStatusRaceIdentity,
    page_kind: raw_capture.NARRaceEntryStatusPageKind,
) -> raw_capture.NARRaceEntryStatusRequestIdentity:
    return raw_capture.build_nar_race_entry_status_request_identity(
        page_kind=page_kind,
        day_scope=raw_capture.NARRaceEntryStatusDayScope(target.baba_code, target.race_date),
        request_race_no=(target.race_no if page_kind is raw_capture.NARRaceEntryStatusPageKind.DEBA_TABLE else None),
    )


def _capture(
    target: raw_capture.NARRaceEntryStatusRaceIdentity,
    page_kind: raw_capture.NARRaceEntryStatusPageKind,
    second_offset: int,
) -> raw_capture.NARRaceEntryStatusResponseCapture:
    request = _request(target, page_kind)
    instant = datetime(2026, 9, 16, 1, 2, second_offset, 123456, tzinfo=UTC)
    return raw_capture.NARRaceEntryStatusResponseCapture(
        request_identity=request,
        effective_url=request.canonical_request_url,
        response_body=b"<html><body>synthetic</body></html>",
        charset="UTF-8",
        requested_at=instant,
        observed_at=instant + timedelta(microseconds=1),
        captured_at=instant + timedelta(microseconds=2),
        http_status=200,
        content_type="text/html; charset=UTF-8",
    )


def _fixture_set(
    target: raw_capture.NARRaceEntryStatusRaceIdentity = FROZEN_TARGET,
) -> publication_contract.FixtureSetV2:
    bundle = raw_capture.NARRaceEntryStatusRawCaptureBundle(
        target_race_identity=target,
        deba_table_capture=_capture(target, raw_capture.NARRaceEntryStatusPageKind.DEBA_TABLE, 0),
        race_list_capture=_capture(target, raw_capture.NARRaceEntryStatusPageKind.RACE_LIST, 1),
    )
    capture_summary = profile_b.summarize_nar_race_entry_status_capture_bundle(bundle=bundle)
    return publication_contract.build_nar_race_entry_status_fixture_set_v2(
        target=target,
        capture_summary=capture_summary,
    )


def _plan() -> subject.Phase57PublicationPlan:
    return subject.build_nar_race_entry_status_phase57_publication_plan(fixture_set=_fixture_set())


def _replace_entry(
    plan: subject.Phase57PublicationPlan,
    index: int,
    *,
    path: str | None = None,
    policy: subject.PublicationPathPolicy | None = None,
) -> subject.Phase57PublicationPlan:
    entry = plan.entries[index]
    replacement = replace(
        entry,
        repository_path=entry.repository_path if path is None else path,
        policy=entry.policy if policy is None else policy,
    )
    entries = plan.entries[:index] + (replacement,) + plan.entries[index + 1 :]
    return replace(plan, entries=entries)


def test_module_is_pure_no_network_publication_planning_authority() -> None:
    source_path = REPOSITORY_ROOT / "scripts/simulation/nar_race_entry_status_source_profile_publication_plan.py"
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }

    assert "nar_race_entry_status_raw_capture" not in source
    assert not imports.intersection({"requests", "urllib", "http.client", "socket", "subprocess"})
    assert "open(" not in source
    assert "git " not in source.lower()


def test_frozen_target_builds_and_validates_exact_prospective_plan() -> None:
    fixture_set = _fixture_set()
    plan = subject.build_nar_race_entry_status_phase57_publication_plan(fixture_set=fixture_set)

    assert plan.authority_semantic == subject.AUTHORITY_SEMANTIC
    assert (plan.provider, plan.baba_code, plan.race_date, plan.race_no) == ("NAR", "21", "2025-01-01", 6)
    assert subject.validate_nar_race_entry_status_phase57_publication_plan(
        value=plan,
        fixture_set=fixture_set,
    ) is plan


@pytest.mark.parametrize(
    "target",
    [
        raw_capture.NARRaceEntryStatusRaceIdentity("22", date(2025, 1, 1), 6),
        raw_capture.NARRaceEntryStatusRaceIdentity("21", date(2025, 1, 2), 6),
        raw_capture.NARRaceEntryStatusRaceIdentity("21", date(2025, 1, 1), 7),
    ],
)
def test_wrong_target_is_rejected_fail_closed(target: raw_capture.NARRaceEntryStatusRaceIdentity) -> None:
    with pytest.raises(subject.PublicationPlanError, match="frozen Phase57 target"):
        subject.build_nar_race_entry_status_phase57_publication_plan(fixture_set=_fixture_set(target))


def test_raw_fixture_paths_are_taken_from_phase56_formal_authority() -> None:
    fixture_set = _fixture_set()
    documents = fixture_set.to_canonical_dict()["documents"]
    plan = subject.build_nar_race_entry_status_phase57_publication_plan(fixture_set=fixture_set)

    assert plan.entries[0].repository_path == documents[0]["fixture_relative_path"] == subject.EXPECTED_DEBA_TABLE_PATH
    assert plan.entries[1].repository_path == documents[1]["fixture_relative_path"] == subject.EXPECTED_RACE_LIST_PATH


def test_exact_six_role_order_paths_and_policies_are_frozen() -> None:
    plan = _plan()

    assert tuple(entry.role for entry in plan.entries) == tuple(subject.PublicationRole)
    assert tuple(entry.role.value for entry in plan.entries) == (
        "DEBA_TABLE_FIXTURE",
        "RACE_LIST_FIXTURE",
        "MANIFEST",
        "DEDICATED_FIXTURE_TEST",
        "CURRENT_PHASE_DOC",
        "LATEST_CODEX_REPORT",
    )
    assert plan.future_live_paths == (
        subject.EXPECTED_DEBA_TABLE_PATH,
        subject.EXPECTED_RACE_LIST_PATH,
        subject.EXPECTED_MANIFEST_PATH,
        subject.EXPECTED_DEDICATED_FIXTURE_TEST_PATH,
        subject.EXPECTED_CURRENT_PHASE_DOC_PATH,
        subject.EXPECTED_LATEST_CODEX_REPORT_PATH,
    )
    assert len(plan.entries) == len(set(entry.role for entry in plan.entries)) == len(set(plan.future_live_paths)) == 6
    assert tuple(entry.policy for entry in plan.entries[:4]) == (subject.PublicationPathPolicy.CREATE_ONLY,) * 4
    assert tuple(entry.policy for entry in plan.entries[4:]) == (subject.PublicationPathPolicy.MODIFY_EXISTING,) * 2
    assert plan.gitattributes_policy is subject.PublicationPathPolicy.VALIDATE_ONLY


@pytest.mark.parametrize(
    "invalid_path",
    [
        "/tests/fixture.html",
        "C:tests/fixture.html",
        "C:/tests/fixture.html",
        "./tests/fixture.html",
        "../tests/fixture.html",
        "tests/../fixture.html",
        "tests//fixture.html",
        "tests\\fixture.html",
        "tests/fixture\x00.html",
        "tests/fixture\x1f.html",
        "tests/fixture\ud800.html",
    ],
)
def test_noncanonical_or_unsafe_repository_path_is_rejected(invalid_path: str) -> None:
    with pytest.raises(subject.PublicationPlanError):
        subject.PublicationPlanEntry(
            role=subject.PublicationRole.DEBA_TABLE_FIXTURE,
            repository_path=invalid_path,
            policy=subject.PublicationPathPolicy.CREATE_ONLY,
        )


@pytest.mark.parametrize(
    ("entry_index", "wrong_path"),
    [
        (0, "tests/fixtures/another_source/v2/deba_table.html"),
        (1, "tests/fixtures/nar_race_entry_status/source_profiles/v2/other/race_list.html"),
        (2, "tests/fixtures/nar_race_entry_status/source_profiles/v2/manifest.json"),
        (3, "tests/test_arbitrary.py"),
        (4, "docs/OTHER.md"),
        (5, "docs/OTHER.md"),
    ],
)
def test_role_paths_are_closed_against_subtree_or_filename_substitution(entry_index: int, wrong_path: str) -> None:
    with pytest.raises(subject.PublicationPlanError, match="outside the closed authority"):
        _replace_entry(_plan(), entry_index, path=wrong_path)


def test_duplicate_path_role_reorder_and_wrong_policy_are_rejected() -> None:
    plan = _plan()
    duplicate = replace(plan.entries[1], repository_path=plan.entries[0].repository_path)
    reordered = plan.entries[1::-1] + plan.entries[2:]

    with pytest.raises(subject.PublicationPlanError):
        replace(plan, entries=plan.entries[:1] + (duplicate,) + plan.entries[2:])
    with pytest.raises(subject.PublicationPlanError, match="out of order"):
        replace(plan, entries=reordered)
    with pytest.raises(subject.PublicationPlanError, match="policy is invalid"):
        _replace_entry(plan, 0, policy=subject.PublicationPathPolicy.MODIFY_EXISTING)


def test_binary_rule_is_exact_additive_unique_and_preserves_existing_rules() -> None:
    attributes = (REPOSITORY_ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines()

    assert subject.REQUIRED_GITATTRIBUTES_RULE == (
        "tests/fixtures/nar_race_entry_status/source_profiles/v2/**/*.html -text -diff"
    )
    assert attributes.count(subject.REQUIRED_GITATTRIBUTES_RULE) == 1
    for existing in (
        "tests/fixtures/historical_replay/official/jra/race_result_20250913_nakayama_04.cp932.html -text -diff",
        "tests/fixtures/historical_replay/official/nar/race_mark_table_20260503_31_01.utf8.html -text -diff",
        "tests/fixtures/nar_daily_target_bootstrap/nar_home_supplier.utf8.html -text -diff",
        "tests/fixtures/nar_daily_target_bootstrap/monthly_convene_info_root_supplier.utf8.html -text -diff",
        "tests/fixtures/nar_market_odds/source_profiles/v1/** -text -diff",
    ):
        assert existing in attributes


def test_git_resolves_binary_attributes_for_both_future_raw_paths() -> None:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(REPOSITORY_ROOT),
            "check-attr",
            "text",
            "diff",
            "--",
            subject.EXPECTED_DEBA_TABLE_PATH,
            subject.EXPECTED_RACE_LIST_PATH,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    lines = result.stdout.splitlines()

    for path in (subject.EXPECTED_DEBA_TABLE_PATH, subject.EXPECTED_RACE_LIST_PATH):
        assert f"{path}: text: unset" in lines
        assert f"{path}: diff: unset" in lines


def test_no_publication_plan_identity_and_rollback_scope_is_exact_live_delta() -> None:
    plan = _plan()

    assert not hasattr(plan, "identity")
    assert plan.rollback_paths == plan.future_live_paths
    assert ".gitattributes" not in plan.rollback_paths
    assert all("publication_plan.py" not in path for path in plan.rollback_paths)


def test_future_fixture_test_contract_freezes_semantics_without_provider_values() -> None:
    assert subject.FUTURE_OFFICIAL_FIXTURE_TEST_REQUIREMENTS == (
        "EXACT_DEBA_SHA256",
        "EXACT_DEBA_BYTE_LENGTH",
        "EXACT_RACELIST_SHA256",
        "EXACT_RACELIST_BYTE_LENGTH",
        "EXACT_TARGET",
        "DOCUMENT_ROLE_ORDER",
        "FIXTURE_SET_V2_RECOMPUTATION",
        "QUALIFICATION_V2_RECOMPUTATION",
        "MANIFEST_CANONICAL_SERIALIZATION",
        "MANIFEST_VALIDATION",
        "PUBLICATION_SAFETY_SAFE",
        "PROFILE_A_QUALIFIED",
        "PROFILE_B_QUALIFIED",
        "PROFILE_B_EXPLICIT_WITHDRAWAL_PRESENT",
        "CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET",
        "MARKET_ELIGIBILITY_UNSUPPORTED",
        "NO_NETWORK",
    )
    assert not any("SHA256:" in item or "BYTE_LENGTH:" in item for item in subject.FUTURE_OFFICIAL_FIXTURE_TEST_REQUIREMENTS)
