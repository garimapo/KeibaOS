from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError
from datetime import date
from hashlib import sha256
import json
from pathlib import Path
import shutil

import pytest

from scripts.simulation import nar_race_entry_status_raw_capture as raw_capture
from scripts.simulation import nar_race_entry_status_source_profile_fixture_consumer as consumer
from scripts.simulation import nar_race_entry_status_source_profile_publication_plan as publication_plan


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
TARGET = raw_capture.NARRaceEntryStatusRaceIdentity("21", date(2025, 1, 1), 6)
PATHS = (
    publication_plan.EXPECTED_DEBA_TABLE_PATH_V3,
    publication_plan.EXPECTED_RACE_LIST_PATH_V3,
    publication_plan.EXPECTED_MANIFEST_PATH_V3,
)
FROZEN = (
    (313317, "6c9aa3ea614c17e14f0e7a5050190ca923445925d67f8e61e71db95e87c87727"),
    (66307, "1eb363621c7a152929765ff7ffecabea2d7cf15283d45fa9c31036527c0b53a1"),
    (4254, "3ca36ed4cec1002e0440fb02e466f40dd7f4d74ffb7c0bdf7b55be2271af321d"),
)


def _identity(root: Path = REPOSITORY_ROOT) -> tuple[tuple[int, str], ...]:
    return tuple(
        (len(payload), sha256(payload).hexdigest())
        for payload in ((root / relative).read_bytes() for relative in PATHS)
    )


@pytest.fixture(scope="module", autouse=True)
def _preserve_committed_fixture() -> object:
    assert _identity() == FROZEN
    yield
    assert _identity() == FROZEN


def _copy_fixture(tmp_path: Path) -> Path:
    root = (tmp_path / "repository").resolve()
    for relative in PATHS:
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPOSITORY_ROOT / relative, destination)
    return root


def _manifest_path(root: Path) -> Path:
    return root / publication_plan.EXPECTED_MANIFEST_PATH_V3


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _mutate_manifest(root: Path, mutation) -> None:
    path = _manifest_path(root)
    value = json.loads(path.read_text(encoding="utf-8"))
    mutation(value)
    path.write_bytes(_canonical_json(value))


def _load(root: Path = REPOSITORY_ROOT):
    return consumer.load_nar_race_entry_status_source_profile_v3_fixture(
        repository_root=root,
        target=TARGET,
    )


def _classification(root: Path, expected: str) -> None:
    with pytest.raises(consumer.NARRaceEntryStatusSourceProfileFixtureConsumerError) as caught:
        _load(root)
    assert caught.value.classification == expected


def test_loads_committed_fixture_as_exact_immutable_bundle() -> None:
    bundle = _load()
    assert type(bundle) is consumer.NARRaceEntryStatusSourceProfileFixtureBundleV3
    assert bundle.repository_relative_paths == PATHS
    assert type(bundle.repository_relative_paths) is tuple
    assert bundle.manifest.fixture_set.identity == (
        "nar-race-entry-status-source-profile-fixture-set-v3:"
        "11f18aae600df59ab90ce9cd3dd3614ff250698d783bcd96e6917cc38a8ab225"
    )
    assert bundle.manifest.qualification.identity == (
        "nar-race-entry-status-source-profile-qualification-v3:"
        "a7f0ba5ed66a71f9785c80b1ba1b5f556b2328d09ead597839cc068a84b0d3ff"
    )
    with pytest.raises((FrozenInstanceError, AttributeError)):
        bundle.target = TARGET  # type: ignore[misc]


def test_repeated_load_is_deterministic() -> None:
    assert _load() == _load()


@pytest.mark.parametrize(
    "target",
    [
        {"baba_code": "21", "race_date": "2025-01-01", "race_no": 6},
        ("21", date(2025, 1, 1), 6),
        raw_capture.NARRaceEntryStatusRaceIdentity("20", date(2025, 1, 1), 6),
        raw_capture.NARRaceEntryStatusRaceIdentity("21", date(2025, 1, 2), 6),
        raw_capture.NARRaceEntryStatusRaceIdentity("21", date(2025, 1, 1), 7),
    ],
)
def test_rejects_wrong_target_type_or_value(target: object) -> None:
    with pytest.raises(consumer.NARRaceEntryStatusSourceProfileFixtureConsumerError) as caught:
        consumer.load_nar_race_entry_status_source_profile_v3_fixture(
            repository_root=REPOSITORY_ROOT,
            target=target,  # type: ignore[arg-type]
        )
    assert caught.value.classification == "UNSUPPORTED_TARGET"


def test_rejects_repository_root_type_relative_and_missing(tmp_path: Path) -> None:
    for root in (str(REPOSITORY_ROOT), Path("."), (tmp_path / "missing").resolve()):
        with pytest.raises(consumer.NARRaceEntryStatusSourceProfileFixtureConsumerError) as caught:
            consumer.load_nar_race_entry_status_source_profile_v3_fixture(
                repository_root=root,  # type: ignore[arg-type]
                target=TARGET,
            )
        assert caught.value.classification in {"FILESYSTEM_VIOLATION", "MISSING_FIXTURE"}


@pytest.mark.parametrize("index", [0, 1, 2])
def test_rejects_each_missing_fixture(tmp_path: Path, index: int) -> None:
    root = _copy_fixture(tmp_path)
    (root / PATHS[index]).unlink()
    _classification(root, "MISSING_FIXTURE")


@pytest.mark.parametrize("kind", ["file", "directory"])
def test_rejects_unexpected_fixture_directory_content(tmp_path: Path, kind: str) -> None:
    root = _copy_fixture(tmp_path)
    extra = (root / PATHS[0]).parent / "unexpected"
    extra.write_bytes(b"x") if kind == "file" else extra.mkdir()
    _classification(root, "UNEXPECTED_FIXTURE_DIRECTORY_CONTENT")


def test_does_not_fall_back_to_v1_or_v2(tmp_path: Path) -> None:
    root = (tmp_path / "repository").resolve()
    legacy = root / "tests/fixtures/nar_race_entry_status/source_profiles/v2/legacy"
    legacy.mkdir(parents=True)
    (legacy / "manifest.json").write_text("{}", encoding="utf-8")
    _classification(root, "MISSING_FIXTURE")


def test_rejects_artifact_symlink_when_supported(tmp_path: Path) -> None:
    root = _copy_fixture(tmp_path)
    path = root / PATHS[0]
    target = path.with_name("outside.html")
    target.write_bytes(path.read_bytes())
    path.unlink()
    try:
        path.symlink_to(target)
    except OSError:
        pytest.skip("artifact symlink creation is unavailable")
    _classification(root, "FILESYSTEM_VIOLATION")


def test_rejects_fixture_directory_symlink_when_supported(tmp_path: Path) -> None:
    root = _copy_fixture(tmp_path)
    directory = (root / PATHS[0]).parent
    moved = directory.with_name("moved")
    directory.rename(moved)
    try:
        directory.symlink_to(moved, target_is_directory=True)
    except OSError:
        moved.rename(directory)
        pytest.skip("directory symlink creation is unavailable")
    _classification(root, "FILESYSTEM_VIOLATION")


def test_rejects_repository_escape_in_path_authority(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _copy_fixture(tmp_path)
    monkeypatch.setattr(consumer, "EXPECTED_MANIFEST_PATH_V3", "../manifest.json")
    _classification(root, "FILESYSTEM_VIOLATION")


def test_rejects_unstable_read_identity(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _copy_fixture(tmp_path)
    original = consumer._stat_identity
    calls = 0

    def unstable(value):
        nonlocal calls
        calls += 1
        identity = original(value)
        return (*identity[:-1], identity[-1] + 1) if calls == 3 else identity

    monkeypatch.setattr(consumer, "_stat_identity", unstable)
    _classification(root, "FILESYSTEM_VIOLATION")


def test_rejects_manifest_invalid_utf8_and_noncanonical_json(tmp_path: Path) -> None:
    root = _copy_fixture(tmp_path)
    _manifest_path(root).write_bytes(b"\xff")
    _classification(root, "MANIFEST_INVALID")
    root = _copy_fixture(tmp_path / "second")
    _manifest_path(root).write_bytes(_manifest_path(root).read_bytes() + b"\n")
    _classification(root, "MANIFEST_INVALID")


def test_rejects_duplicate_manifest_key(tmp_path: Path) -> None:
    root = _copy_fixture(tmp_path)
    path = _manifest_path(root)
    path.write_bytes(path.read_bytes().replace(b"{", b'{"provider":"NAR",', 1))
    _classification(root, "MANIFEST_INVALID")


@pytest.mark.parametrize("constant", [b"NaN", b"Infinity", b"-Infinity"])
def test_rejects_nonfinite_manifest_values(tmp_path: Path, constant: bytes) -> None:
    root = _copy_fixture(tmp_path)
    path = _manifest_path(root)
    path.write_bytes(path.read_bytes().replace(b"{", b'{"nonfinite":' + constant + b",", 1))
    _classification(root, "MANIFEST_INVALID")


@pytest.mark.parametrize(
    ("mutation", "classification"),
    [
        (lambda value: value.__setitem__("manifest_schema_version", 2), "MANIFEST_INVALID"),
        (lambda value: value["target"].__setitem__("race_no", 7), "TARGET_OR_PATH_CONTRADICTION"),
        (lambda value: value["documents"].reverse(), "TARGET_OR_PATH_CONTRADICTION"),
        (
            lambda value: value["documents"][0].__setitem__("fixture_relative_path", "wrong.html"),
            "TARGET_OR_PATH_CONTRADICTION",
        ),
        (
            lambda value: value["documents"][0].__setitem__("response_sha256", "0" * 64),
            "DOCUMENT_IDENTITY_MISMATCH",
        ),
        (
            lambda value: value["documents"][1].__setitem__("response_byte_length", 1),
            "DOCUMENT_IDENTITY_MISMATCH",
        ),
        (lambda value: value.__setitem__("market_eligibility", "SUPPORTED"), "TARGET_OR_PATH_CONTRADICTION"),
        (
            lambda value: value.__setitem__("acquisition_semantics", "HISTORICAL"),
            "TARGET_OR_PATH_CONTRADICTION",
        ),
        (lambda value: value.__setitem__("fixture_set_identity", "changed"), "FORMAL_AUTHORITY_VALIDATION_FAILURE"),
        (lambda value: value.__setitem__("qualification_identity", "changed"), "FORMAL_AUTHORITY_VALIDATION_FAILURE"),
    ],
)
def test_rejects_manifest_mutations(tmp_path: Path, mutation, classification: str) -> None:
    root = _copy_fixture(tmp_path)
    _mutate_manifest(root, mutation)
    _classification(root, classification)


@pytest.mark.parametrize("index", [0, 1])
def test_rejects_raw_document_mutation(tmp_path: Path, index: int) -> None:
    root = _copy_fixture(tmp_path)
    path = root / PATHS[index]
    payload = path.read_bytes()
    path.write_bytes(bytes([payload[0] ^ 1]) + payload[1:])
    _classification(root, "DOCUMENT_IDENTITY_MISMATCH")


@pytest.mark.parametrize(
    ("owner", "name"),
    [
        (consumer._profile_a, "diagnose_nar_race_entry_status_profile_a_v3"),
        (consumer._profile_b, "diagnose_nar_race_entry_status_profile_b_v2"),
        (consumer._contract, "assess_nar_race_entry_status_raw_fixture_publication_safety_v3"),
        (consumer._phase66, "diagnose_nar_race_entry_status_profile_b_candidate_ancestry_recovery"),
    ],
)
def test_formal_authority_failures_are_reached_and_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    owner: object,
    name: str,
) -> None:
    def fail(**_kwargs):
        raise RuntimeError("isolated formal gate")

    monkeypatch.setattr(owner, name, fail)
    _classification(REPOSITORY_ROOT, "FORMAL_AUTHORITY_VALIDATION_FAILURE")


def test_rejects_self_consistent_fixture_when_frozen_phase83_identity_differs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(consumer, "_FROZEN_MANIFEST_SHA256", "0" * 64)
    _classification(REPOSITORY_ROOT, "FROZEN_PHASE83_IDENTITY_MISMATCH")


def test_loader_is_independent_of_current_working_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    assert _load().target == TARGET


def test_production_module_has_no_network_database_subprocess_or_replay_authority() -> None:
    source_path = Path(consumer.__file__).resolve()
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    forbidden_imports = {"requests", "httpx", "urllib.request", "socket", "subprocess", "sqlite3"}
    assert forbidden_imports.isdisjoint(imported)
    for forbidden_name in (
        "normalize_nar_historical_input_source_records",
        "build_historical_input_snapshot",
        "resolve_sqlite_nar_daily_evidence",
        "run_nar_daily_replay",
        "Path.cwd",
        ".glob(",
        ".rglob(",
    ):
        assert forbidden_name not in source
