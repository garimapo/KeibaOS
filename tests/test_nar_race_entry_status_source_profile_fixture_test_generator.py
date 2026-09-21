from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.simulation import nar_race_entry_status_source_profile_diagnostics as profile_b
from scripts.simulation import nar_race_entry_status_source_profile_fixture_test_generator as subject
from scripts.simulation import nar_race_entry_status_source_profile_fixture_test_preflight as preflight
from scripts.simulation import nar_race_entry_status_source_profile_profile_a as profile_a
from scripts.simulation import nar_race_entry_status_source_profile_publication_contract as contract
from scripts.simulation import nar_race_entry_status_source_profile_publication_plan as plan


def _case() -> preflight.V3FixtureTestCase:
    return preflight.build_deterministic_v3_fixture_test_case()


def _render(case: preflight.V3FixtureTestCase) -> bytes:
    return subject.render_nar_race_entry_status_source_profile_v3_fixture_test(
        deba_table_bytes=case.deba_table_bytes,
        race_list_bytes=case.race_list_bytes,
        manifest=case.manifest,
        publication_plan=case.publication_plan,
    )


def test_renderer_is_deterministic_canonical_compilable_and_bounded() -> None:
    case = _case()
    first = _render(case)
    second = _render(case)

    assert first == second
    assert first.decode("utf-8", errors="strict").encode("utf-8") == first
    assert not first.startswith(b"\xef\xbb\xbf")
    assert b"\r" not in first
    assert 0 < len(first) < subject.MAX_GENERATED_FIXTURE_TEST_BYTES
    compile(first, "<test-generated-v3-fixture-test>", "exec")
    text = first.decode("utf-8")
    assert str(Path.cwd()) not in text
    assert "<html" not in text
    assert "EXPECTED_DEBA_SHA256" in text
    assert repr(plan.FUTURE_OFFICIAL_FIXTURE_TEST_REQUIREMENTS_V3) in text


@pytest.mark.parametrize("name", ["deba_table_bytes", "race_list_bytes"])
def test_renderer_requires_exact_bytes_and_rejects_subclasses(name: str) -> None:
    class BytesSubclass(bytes):
        pass

    case = _case()
    values = {
        "deba_table_bytes": case.deba_table_bytes,
        "race_list_bytes": case.race_list_bytes,
        "manifest": case.manifest,
        "publication_plan": case.publication_plan,
    }
    values[name] = BytesSubclass(values[name])
    with pytest.raises(subject.V3FixtureTestGenerationError, match="exact bytes"):
        subject.render_nar_race_entry_status_source_profile_v3_fixture_test(**values)


@pytest.mark.parametrize(
    ("field", "wrong_value"),
    [
        ("manifest", {}),
        ("manifest", SimpleNamespace(fixture_set=None)),
        ("publication_plan", {}),
        ("publication_plan", SimpleNamespace(future_live_paths=())),
    ],
)
def test_renderer_rejects_dicts_and_duck_types(field: str, wrong_value: object) -> None:
    case = _case()
    values = {
        "deba_table_bytes": case.deba_table_bytes,
        "race_list_bytes": case.race_list_bytes,
        "manifest": case.manifest,
        "publication_plan": case.publication_plan,
    }
    values[field] = wrong_value
    with pytest.raises(subject.V3FixtureTestGenerationError):
        subject.render_nar_race_entry_status_source_profile_v3_fixture_test(**values)


def test_renderer_rejects_v2_authority_types() -> None:
    case = _case()
    capture = case.manifest.fixture_set.capture_summary
    v2_fixture = contract.build_nar_race_entry_status_fixture_set_v2(
        target=case.manifest.fixture_set.target,
        capture_summary=capture,
    )
    v2_a = profile_a.diagnose_nar_race_entry_status_profile_a(
        deba_table_bytes=case.deba_table_bytes,
        target=case.manifest.fixture_set.target,
    )
    v2_b_source = case.race_list_bytes.replace(
        b'<table class="changeInfo">',
        b'</section><table class="changeInfo">',
    ).replace(b"</table></section></body>", b"</table></body>")
    v2_b = profile_b.diagnose_nar_race_entry_status_profile_b(
        race_list_bytes=v2_b_source,
        target=case.manifest.fixture_set.target,
    )
    v2_qualification = contract.build_nar_race_entry_status_qualification_v2(
        target=case.manifest.fixture_set.target,
        fixture_set=v2_fixture,
        profile_a=v2_a,
        profile_b=v2_b,
    )
    v2_safety = contract.assess_nar_race_entry_status_raw_fixture_publication_safety(
        deba_table_bytes=case.deba_table_bytes,
        race_list_bytes=v2_b_source,
    )
    v2_manifest = contract.build_nar_race_entry_status_manifest_v2(
        fixture_set=v2_fixture,
        qualification=v2_qualification,
        publication_safety=v2_safety,
    )
    v2_plan = plan.build_nar_race_entry_status_phase57_publication_plan(fixture_set=v2_fixture)

    for wrong_manifest in (v2_fixture, v2_qualification, v2_manifest):
        with pytest.raises(subject.V3FixtureTestGenerationError):
            subject.render_nar_race_entry_status_source_profile_v3_fixture_test(
                deba_table_bytes=case.deba_table_bytes,
                race_list_bytes=case.race_list_bytes,
                manifest=wrong_manifest,  # type: ignore[arg-type]
                publication_plan=case.publication_plan,
            )
    with pytest.raises(subject.V3FixtureTestGenerationError):
        subject.render_nar_race_entry_status_source_profile_v3_fixture_test(
            deba_table_bytes=case.deba_table_bytes,
            race_list_bytes=case.race_list_bytes,
            manifest=case.manifest,
            publication_plan=v2_plan,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    ("field", "mutation"),
    [
        ("deba_table_bytes", lambda value: value[:-1] + b" "),
        ("race_list_bytes", lambda value: value[:-1] + b" "),
        ("deba_table_bytes", lambda value: value + b" "),
        ("race_list_bytes", lambda value: value + b" "),
    ],
)
def test_renderer_rejects_raw_hash_or_length_contradictions(field: str, mutation: object) -> None:
    case = _case()
    values = {
        "deba_table_bytes": case.deba_table_bytes,
        "race_list_bytes": case.race_list_bytes,
        "manifest": case.manifest,
        "publication_plan": case.publication_plan,
    }
    values[field] = mutation(values[field])  # type: ignore[operator]
    with pytest.raises(subject.V3FixtureTestGenerationError, match="contradicts exact bytes"):
        subject.render_nar_race_entry_status_source_profile_v3_fixture_test(**values)


def test_renderer_rejects_wrong_target_or_mismatched_exact_plan() -> None:
    case = _case()
    wrong_plan = replace(case.publication_plan)
    object.__setattr__(wrong_plan, "race_no", 7)
    with pytest.raises(subject.V3FixtureTestGenerationError, match="formal V3 authority"):
        subject.render_nar_race_entry_status_source_profile_v3_fixture_test(
            deba_table_bytes=case.deba_table_bytes,
            race_list_bytes=case.race_list_bytes,
            manifest=case.manifest,
            publication_plan=wrong_plan,
        )


@pytest.mark.parametrize("kind", ["profile_a", "profile_b", "safety"])
def test_renderer_rejects_nonqualified_or_non_safe_formal_authority(kind: str) -> None:
    case = _case()
    target = case.manifest.fixture_set.target
    fixture = case.manifest.fixture_set
    qualification = case.manifest.qualification
    safety = case.manifest.publication_safety
    if kind == "profile_a":
        blocked_a = profile_a.diagnose_nar_race_entry_status_profile_a_v3(
            deba_table_bytes=b"<html><body></body></html>",
            target=target,
        )
        qualification = contract.build_nar_race_entry_status_qualification_v3(
            target=target,
            fixture_set=fixture,
            profile_a=blocked_a,
            profile_b=qualification.profile_b,
        )
    elif kind == "profile_b":
        blocked_b = profile_b.diagnose_nar_race_entry_status_profile_b_v2(
            race_list_bytes=b"<html><body></body></html>",
            target=target,
        )
        qualification = contract.build_nar_race_entry_status_qualification_v3(
            target=target,
            fixture_set=fixture,
            profile_a=qualification.profile_a,
            profile_b=blocked_b,
        )
    else:
        safety = contract.assess_nar_race_entry_status_raw_fixture_publication_safety_v3(
            deba_table_bytes=b'<input name="authorization" value="secret">',
            race_list_bytes=case.race_list_bytes,
        )
    invalid_manifest = replace(case.manifest)
    object.__setattr__(invalid_manifest, "qualification", qualification)
    object.__setattr__(invalid_manifest, "publication_safety", safety)
    with pytest.raises(subject.V3FixtureTestGenerationError):
        subject.render_nar_race_entry_status_source_profile_v3_fixture_test(
            deba_table_bytes=case.deba_table_bytes,
            race_list_bytes=case.race_list_bytes,
            manifest=invalid_manifest,
            publication_plan=case.publication_plan,
        )


def test_generator_static_purity_contract() -> None:
    source_path = Path(subject.__file__).resolve()
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imported: set[str] = set()
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr)
    assert imported.isdisjoint(
        {"requests", "httpx", "urllib", "socket", "subprocess", "os", "time", "random", "pathlib"}
    )
    assert calls.isdisjoint(
        {"open", "write_bytes", "write_text", "run", "Popen", "system", "getenv"}
    )
