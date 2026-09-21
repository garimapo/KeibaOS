from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError
from pathlib import Path
import sys

import pytest

from scripts.simulation import nar_race_entry_status_source_profile_fixture_test_generator as generator
from scripts.simulation import nar_race_entry_status_source_profile_fixture_test_preflight as subject


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _case() -> subject.V3FixtureTestCase:
    return subject.build_deterministic_v3_fixture_test_case()


def _source(case: subject.V3FixtureTestCase) -> bytes:
    return generator.render_nar_race_entry_status_source_profile_v3_fixture_test(
        deba_table_bytes=case.deba_table_bytes,
        race_list_bytes=case.race_list_bytes,
        manifest=case.manifest,
        publication_plan=case.publication_plan,
    )


def _execute(
    *,
    tmp_path: Path,
    name: str,
    case: subject.V3FixtureTestCase,
    source: bytes,
    deba: bytes | None = None,
    race_list: bytes | None = None,
    manifest: bytes | None = None,
) -> subject.V3FixtureTestPreflightEvidence:
    root = tmp_path / name
    evidence = subject.execute_generated_v3_fixture_test_in_external_mirror(
        repository_root=REPOSITORY_ROOT,
        external_root=root,
        deba_table_bytes=case.deba_table_bytes if deba is None else deba,
        race_list_bytes=case.race_list_bytes if race_list is None else race_list,
        manifest_bytes=case.manifest.canonical_bytes() if manifest is None else manifest,
        generated_source_bytes=source,
        python_executable=Path(sys.executable),
    )
    assert not root.exists()
    return evidence


def test_deterministic_synthetic_case_has_exact_qualified_shape() -> None:
    first = _case()
    second = _case()

    assert first.deba_table_bytes == second.deba_table_bytes
    assert first.race_list_bytes == second.race_list_bytes
    assert first.manifest.canonical_bytes() == second.manifest.canonical_bytes()
    assert first.manifest.fixture_set.identity == second.manifest.fixture_set.identity
    assert first.manifest.qualification.identity == second.manifest.qualification.identity
    assert (
        first.phase63_candidate_count,
        first.phase66_candidate_count,
        first.phase66_direct_schedule_count,
        first.phase66_change_info_count,
    ) == (2, 2, 1, 1)
    assert first.manifest.qualification.profile_a.overall_result == "QUALIFIED"
    assert first.manifest.qualification.profile_b.overall_result == "QUALIFIED"
    assert first.manifest.publication_safety.raw_fixture_publication_safe is True


def test_actual_isolated_pytest_preflight_passes_and_cleans_external_mirror() -> None:
    evidence = subject.run_nar_race_entry_status_source_profile_v3_fixture_test_preflight(
        repository_root=REPOSITORY_ROOT,
    )

    assert evidence.gate == subject.V3_DEDICATED_FIXTURE_TEST_END_TO_END_PREFLIGHT_PASS
    assert evidence.pytest_return_code == 0
    assert evidence.test_passed is True
    assert evidence.production_import_isolation_result == "PASS"
    assert evidence.generated_source_byte_length < generator.MAX_GENERATED_FIXTURE_TEST_BYTES // 2
    assert evidence.manifest_byte_length < subject.MAX_FAILURE_MANIFEST_BYTES
    assert evidence.stdout.byte_length <= subject.MAX_PROCESS_STREAM_BYTES
    assert evidence.stderr.byte_length <= subject.MAX_PROCESS_STREAM_BYTES
    with pytest.raises(FrozenInstanceError):
        evidence.test_passed = False  # type: ignore[misc]


@pytest.mark.parametrize(
    "mutation_name",
    [
        "deba_byte",
        "race_list_byte",
        "manifest_byte",
        "expected_deba_sha",
        "expected_race_list_length",
        "target_race_number",
        "fixture_set_identity",
        "qualification_identity",
        "market_eligibility",
    ],
)
def test_actual_pytest_fails_for_each_independent_mutation(
    mutation_name: str,
    tmp_path: Path,
) -> None:
    case = _case()
    source = _source(case)
    deba = case.deba_table_bytes
    race_list = case.race_list_bytes
    manifest = case.manifest.canonical_bytes()
    text = source.decode("utf-8")
    if mutation_name == "deba_byte":
        deba = deba[:-1] + b" "
    elif mutation_name == "race_list_byte":
        race_list = race_list[:-1] + b" "
    elif mutation_name == "manifest_byte":
        manifest = manifest.replace(b'"provider":"NAR"', b'"provider":"XXX"', 1)
    elif mutation_name == "expected_deba_sha":
        text = text.replace(
            case.manifest.fixture_set.capture_summary.deba_table.response_sha256,
            "0" * 64,
            1,
        )
    elif mutation_name == "expected_race_list_length":
        text = text.replace(
            "EXPECTED_RACELIST_BYTE_LENGTH = "
            + str(case.manifest.fixture_set.capture_summary.race_list.response_byte_length),
            "EXPECTED_RACELIST_BYTE_LENGTH = 1",
            1,
        )
    elif mutation_name == "target_race_number":
        text = text.replace(
            '"race_date":"2025-01-01","race_no":6',
            '"race_date":"2025-01-01","race_no":7',
            1,
        )
    elif mutation_name == "fixture_set_identity":
        text = text.replace(case.manifest.fixture_set.identity, "fixture-set-mutated", 1)
    elif mutation_name == "qualification_identity":
        text = text.replace(case.manifest.qualification.identity, "qualification-mutated", 1)
    else:
        text = text.replace(
            'EXPECTED_MARKET_ELIGIBILITY = "UNSUPPORTED"',
            'EXPECTED_MARKET_ELIGIBILITY = "SUPPORTED"',
            1,
        )
    mutated_source = text.encode("utf-8")
    compile(mutated_source, "<mutated-generated-test>", "exec")

    evidence = _execute(
        tmp_path=tmp_path,
        name=mutation_name,
        case=case,
        source=mutated_source,
        deba=deba,
        race_list=race_list,
        manifest=manifest,
    )

    assert evidence.pytest_return_code != 0
    assert evidence.test_passed is False
    assert evidence.production_import_isolation_result == "PASS"
    assert evidence.pytest_failure_nodes


def test_import_isolation_accepts_only_exact_namespace_and_module_origins() -> None:
    scripts_root = REPOSITORY_ROOT / "scripts"
    origins = (
        REPOSITORY_ROOT
        / "scripts/simulation/nar_race_entry_status_source_profile_fixture_test_generator.py",
        REPOSITORY_ROOT
        / "scripts/simulation/nar_race_entry_status_source_profile_fixture_test_preflight.py",
    )
    assert subject.validate_nar_race_entry_status_fixture_test_import_isolation(
        repository_root=REPOSITORY_ROOT,
        namespace_locations=(scripts_root,),
        module_origins=origins,
    ) == "PASS"


def test_import_isolation_rejects_missing_and_alternate_repository_roots(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    alternate = tmp_path / "alternate"
    alternate.mkdir()
    with pytest.raises(subject.V3FixtureTestPreflightError, match="unavailable"):
        subject.validate_nar_race_entry_status_fixture_test_import_isolation(
            repository_root=missing,
            namespace_locations=(),
            module_origins=(),
        )
    with pytest.raises(subject.V3FixtureTestPreflightError, match="reviewed module worktree"):
        subject.validate_nar_race_entry_status_fixture_test_import_isolation(
            repository_root=alternate,
            namespace_locations=(),
            module_origins=(),
        )


def test_import_isolation_rejects_second_namespace_and_outside_module(tmp_path: Path) -> None:
    extra_scripts = tmp_path / "scripts"
    extra_scripts.mkdir()
    outside_module = tmp_path / "outside.py"
    outside_module.write_text("# outside\n", encoding="utf-8")
    with pytest.raises(subject.V3FixtureTestPreflightError, match="unexpected portion"):
        subject.validate_nar_race_entry_status_fixture_test_import_isolation(
            repository_root=REPOSITORY_ROOT,
            namespace_locations=(REPOSITORY_ROOT / "scripts", extra_scripts),
            module_origins=(Path(subject.__file__),),
        )
    with pytest.raises(subject.V3FixtureTestPreflightError, match="outside authorized"):
        subject.validate_nar_race_entry_status_fixture_test_import_isolation(
            repository_root=REPOSITORY_ROOT,
            namespace_locations=(REPOSITORY_ROOT / "scripts",),
            module_origins=(outside_module,),
        )


def test_external_mirror_rejects_competing_scripts_package(tmp_path: Path) -> None:
    case = _case()
    mirror = tmp_path / "competing"
    (mirror / "scripts").mkdir(parents=True)
    with pytest.raises(subject.V3FixtureTestPreflightError, match="competing scripts"):
        subject.execute_generated_v3_fixture_test_in_external_mirror(
            repository_root=REPOSITORY_ROOT,
            external_root=mirror,
            deba_table_bytes=case.deba_table_bytes,
            race_list_bytes=case.race_list_bytes,
            manifest_bytes=case.manifest.canonical_bytes(),
            generated_source_bytes=_source(case),
            python_executable=Path(sys.executable),
        )


def test_failure_evidence_is_bounded_safe_and_ready_before_rollback(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    case = _case()
    source = _source(case)
    command = "phase79-pytest-command-v1:" + "a" * 64
    stdout = b"x" * (subject.MAX_PROCESS_STREAM_BYTES + 1)
    evidence = subject.build_v3_fixture_test_failure_evidence(
        deba_table_bytes=case.deba_table_bytes,
        race_list_bytes=case.race_list_bytes,
        manifest=case.manifest,
        publication_plan=case.publication_plan,
        generated_source_bytes=source,
        pytest_command_identity=command,
        pytest_return_code=1,
        stdout=stdout,
        stderr=b"synthetic pytest failure",
    )

    assert evidence.generated_source_bytes == source
    assert evidence.retained_manifest_bytes == case.manifest.canonical_bytes()
    assert evidence.stdout.classification == "OVERSIZED_REDACTED"
    assert evidence.stdout.safe_text is None
    assert evidence.stderr.classification == "UNCONTROLLED_OUTPUT_REDACTED"
    assert evidence.evidence_ready_before_rollback is True
    canonical = evidence.canonical_bytes()
    assert b"<html" not in canonical
    assert case.deba_table_bytes not in canonical
    assert case.race_list_bytes not in canonical
    durable_path = (tmp_path / "phase79-failure-evidence.json").resolve()
    receipt = subject.retain_v3_fixture_test_failure_evidence_durably(
        evidence=evidence,
        evidence_path=durable_path,
    )
    assert receipt.flush_completed is True
    assert receipt.fsync_completed is True
    assert receipt.readback_validated is True
    assert durable_path.read_bytes() == canonical

    monkeypatch.setattr(subject, "MAX_FAILURE_MANIFEST_BYTES", 1)
    projected = subject.build_v3_fixture_test_failure_evidence(
        deba_table_bytes=case.deba_table_bytes,
        race_list_bytes=case.race_list_bytes,
        manifest=case.manifest,
        publication_plan=case.publication_plan,
        generated_source_bytes=source,
        pytest_command_identity=command,
        pytest_return_code=1,
        stdout=b"",
        stderr=b"",
    )
    assert projected.retained_manifest_bytes is None
    assert projected.manifest_safe_projection["market_eligibility"] == "UNSUPPORTED"


def test_preflight_module_static_scope_has_no_provider_network_authority() -> None:
    tree = ast.parse(Path(subject.__file__).read_text(encoding="utf-8"))
    imported: set[str] = set()
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            calls.add(node.func.attr)
    assert imported.isdisjoint({"requests", "httpx", "urllib", "socket"})
    assert "fetch" not in calls
    assert "acquire_nar_race_entry_status_raw_bundle" not in calls
