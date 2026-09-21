"""No-network external pytest preflight and bounded V3 failure evidence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from types import MappingProxyType
from typing import Mapping

from scripts.simulation import nar_race_entry_status_raw_capture as raw_capture
from scripts.simulation import nar_race_entry_status_source_profile_diagnostics as profile_b
from scripts.simulation import nar_race_entry_status_source_profile_profile_a as profile_a
from scripts.simulation import nar_race_entry_status_source_profile_recovery_diagnostics as phase63
from scripts.simulation import nar_race_entry_status_source_profile_structural_recovery_diagnostics as phase66
from scripts.simulation.nar_race_entry_status_reacquisition_observability import (
    MAX_PROCESS_STREAM_BYTES,
    SanitizedProcessStream,
    sanitize_process_stream,
)
from scripts.simulation.nar_race_entry_status_source_profile_fixture_test_generator import (
    MAX_GENERATED_FIXTURE_TEST_BYTES,
    render_nar_race_entry_status_source_profile_v3_fixture_test,
)
from scripts.simulation.nar_race_entry_status_source_profile_publication_contract import (
    FixtureSetV3,
    QualificationV3,
    RawFixturePublicationSafetyV3,
    SourceProfileManifestV3,
    assess_nar_race_entry_status_raw_fixture_publication_safety_v3,
    build_nar_race_entry_status_fixture_set_v3,
    build_nar_race_entry_status_manifest_v3,
    build_nar_race_entry_status_qualification_v3,
    validate_nar_race_entry_status_manifest_v3,
)
from scripts.simulation.nar_race_entry_status_source_profile_publication_plan import (
    EXPECTED_DEBA_TABLE_PATH_V3,
    EXPECTED_DEDICATED_FIXTURE_TEST_PATH_V3,
    EXPECTED_MANIFEST_PATH_V3,
    EXPECTED_RACE_LIST_PATH_V3,
    SourceProfilePublicationPlanV3,
    build_nar_race_entry_status_source_profile_publication_plan_v3,
)


MAX_FAILURE_MANIFEST_BYTES = 32768
V3_DEDICATED_FIXTURE_TEST_END_TO_END_PREFLIGHT_PASS = (
    "V3_DEDICATED_FIXTURE_TEST_END_TO_END_PREFLIGHT_PASS"
)
_IMPORT_ISOLATION_TOKEN = "PHASE79_IMPORT_ISOLATION_PASS"
_PREFLIGHT_FAIL_CLOSED = "V3_DEDICATED_FIXTURE_TEST_END_TO_END_PREFLIGHT_FAIL_CLOSED"
_AUTHORIZED_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_FIXED_INSTANT = datetime(2026, 9, 20, 1, 2, 3, 123456, tzinfo=timezone.utc)
_FAILURE_NODE = re.compile(
    r"^FAILED tests[\\/]test_nar_race_entry_status_source_profile_v3_fixtures\.py::"
    r"([A-Za-z_][A-Za-z0-9_]*)\r?$",
    flags=re.MULTILINE,
)


class V3FixtureTestPreflightError(RuntimeError):
    """The deterministic external preflight could not be completed safely."""


def _error(message: str) -> V3FixtureTestPreflightError:
    return V3FixtureTestPreflightError(message)


@dataclass(frozen=True, slots=True)
class V3FixtureTestCase:
    deba_table_bytes: bytes
    race_list_bytes: bytes
    manifest: SourceProfileManifestV3
    publication_plan: SourceProfilePublicationPlanV3
    phase63_candidate_count: int
    phase66_candidate_count: int
    phase66_direct_schedule_count: int
    phase66_change_info_count: int

    def __post_init__(self) -> None:
        if type(self.deba_table_bytes) is not bytes or not self.deba_table_bytes:
            raise _error("synthetic Deba bytes are invalid")
        if type(self.race_list_bytes) is not bytes or not self.race_list_bytes:
            raise _error("synthetic RaceList bytes are invalid")
        if type(self.manifest) is not SourceProfileManifestV3:
            raise _error("synthetic manifest has the wrong type")
        if type(self.publication_plan) is not SourceProfilePublicationPlanV3:
            raise _error("synthetic publication plan has the wrong type")
        counts = (
            self.phase63_candidate_count,
            self.phase66_candidate_count,
            self.phase66_direct_schedule_count,
            self.phase66_change_info_count,
        )
        if any(type(value) is not int or value < 0 for value in counts):
            raise _error("synthetic diagnostic count is invalid")


@dataclass(frozen=True, slots=True)
class V3FixtureTestPreflightEvidence:
    gate: str
    generated_source_sha256: str
    generated_source_byte_length: int
    manifest_sha256: str
    manifest_byte_length: int
    pytest_command_identity: str
    pytest_return_code: int
    stdout: SanitizedProcessStream
    stderr: SanitizedProcessStream
    pytest_failure_nodes: tuple[str, ...]
    test_passed: bool
    external_mirror_root: str
    production_import_isolation_result: str

    def __post_init__(self) -> None:
        if self.gate not in {
            V3_DEDICATED_FIXTURE_TEST_END_TO_END_PREFLIGHT_PASS,
            _PREFLIGHT_FAIL_CLOSED,
        }:
            raise _error("preflight gate name is invalid")
        for name, value in (
            ("generated_source_sha256", self.generated_source_sha256),
            ("manifest_sha256", self.manifest_sha256),
        ):
            if type(value) is not str or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
                raise _error(f"{name} is invalid")
        if type(self.generated_source_byte_length) is not int or not 0 < self.generated_source_byte_length <= MAX_GENERATED_FIXTURE_TEST_BYTES:
            raise _error("generated source length is invalid")
        if type(self.manifest_byte_length) is not int or self.manifest_byte_length <= 0:
            raise _error("manifest length is invalid")
        if type(self.pytest_command_identity) is not str or not self.pytest_command_identity.startswith("phase79-pytest-command-v1:"):
            raise _error("pytest command identity is invalid")
        if type(self.pytest_return_code) is not int:
            raise _error("pytest return code is invalid")
        if type(self.stdout) is not SanitizedProcessStream or type(self.stderr) is not SanitizedProcessStream:
            raise _error("process stream evidence has the wrong type")
        if (
            type(self.pytest_failure_nodes) is not tuple
            or len(self.pytest_failure_nodes) > 16
            or any(
                type(node) is not str
                or len(node.encode("utf-8")) > 512
                or not node.startswith(
                    "tests/test_nar_race_entry_status_source_profile_v3_fixtures.py::test_"
                )
                for node in self.pytest_failure_nodes
            )
        ):
            raise _error("pytest failure-node evidence is invalid")
        if type(self.test_passed) is not bool:
            raise _error("preflight pass state must be exact bool")
        if type(self.external_mirror_root) is not str or not self.external_mirror_root:
            raise _error("external mirror root is invalid")
        if self.production_import_isolation_result not in {"PASS", "FAIL"}:
            raise _error("import-isolation result is invalid")
        if self.test_passed != (
            self.pytest_return_code == 0 and self.production_import_isolation_result == "PASS"
        ):
            raise _error("preflight pass state is contradictory")
        expected_gate = (
            V3_DEDICATED_FIXTURE_TEST_END_TO_END_PREFLIGHT_PASS
            if self.test_passed
            else _PREFLIGHT_FAIL_CLOSED
        )
        if self.gate != expected_gate:
            raise _error("preflight gate contradicts pass state")


@dataclass(frozen=True, slots=True)
class V3FixtureTestFailureEvidence:
    generated_source_bytes: bytes
    generated_source_sha256: str
    generated_source_byte_length: int
    retained_manifest_bytes: bytes | None
    manifest_sha256: str
    manifest_byte_length: int
    manifest_safe_projection: Mapping[str, object]
    fixture_set_identity: str
    qualification_identity: str
    deba_sha256: str
    deba_byte_length: int
    race_list_sha256: str
    race_list_byte_length: int
    pytest_command_identity: str
    pytest_return_code: int
    stdout: SanitizedProcessStream
    stderr: SanitizedProcessStream
    pytest_failure_nodes: tuple[str, ...]
    evidence_ready_before_rollback: bool

    def __post_init__(self) -> None:
        if type(self.generated_source_bytes) is not bytes or not self.generated_source_bytes:
            raise _error("retained generated source must be exact nonempty bytes")
        if sha256(self.generated_source_bytes).hexdigest() != self.generated_source_sha256:
            raise _error("retained generated source digest is contradictory")
        if len(self.generated_source_bytes) != self.generated_source_byte_length:
            raise _error("retained generated source length is contradictory")
        if not 0 < self.generated_source_byte_length <= MAX_GENERATED_FIXTURE_TEST_BYTES:
            raise _error("retained generated source exceeds its evidence bound")
        if type(self.manifest_byte_length) is not int or self.manifest_byte_length <= 0:
            raise _error("manifest byte length is invalid")
        if self.retained_manifest_bytes is not None and type(self.retained_manifest_bytes) is not bytes:
            raise _error("retained manifest must be exact bytes or None")
        if self.retained_manifest_bytes is not None:
            if len(self.retained_manifest_bytes) > MAX_FAILURE_MANIFEST_BYTES:
                raise _error("retained manifest exceeds its evidence bound")
            if len(self.retained_manifest_bytes) != self.manifest_byte_length:
                raise _error("retained manifest length is contradictory")
            if sha256(self.retained_manifest_bytes).hexdigest() != self.manifest_sha256:
                raise _error("retained manifest digest is contradictory")
        if type(self.manifest_safe_projection) is not MappingProxyType:
            raise _error("manifest safe projection must be immutable")
        if type(self.stdout) is not SanitizedProcessStream or type(self.stderr) is not SanitizedProcessStream:
            raise _error("failure process evidence has the wrong type")
        if type(self.pytest_failure_nodes) is not tuple or len(self.pytest_failure_nodes) > 16:
            raise _error("failure-node evidence is invalid")
        if self.evidence_ready_before_rollback is not True:
            raise _error("failure evidence must be finalized before rollback")

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "generated_source_utf8": self.generated_source_bytes.decode("utf-8", errors="strict"),
            "generated_source_sha256": self.generated_source_sha256,
            "generated_source_byte_length": self.generated_source_byte_length,
            "retained_manifest_utf8": (
                None
                if self.retained_manifest_bytes is None
                else self.retained_manifest_bytes.decode("utf-8", errors="strict")
            ),
            "manifest_sha256": self.manifest_sha256,
            "manifest_byte_length": self.manifest_byte_length,
            "manifest_safe_projection": dict(self.manifest_safe_projection),
            "fixture_set_identity": self.fixture_set_identity,
            "qualification_identity": self.qualification_identity,
            "deba_sha256": self.deba_sha256,
            "deba_byte_length": self.deba_byte_length,
            "race_list_sha256": self.race_list_sha256,
            "race_list_byte_length": self.race_list_byte_length,
            "pytest_command_identity": self.pytest_command_identity,
            "pytest_return_code": self.pytest_return_code,
            "stdout": {
                "classification": self.stdout.classification,
                "present": self.stdout.present,
                "byte_length": self.stdout.byte_length,
                "sha256": self.stdout.sha256,
                "safe_text": self.stdout.safe_text,
            },
            "stderr": {
                "classification": self.stderr.classification,
                "present": self.stderr.present,
                "byte_length": self.stderr.byte_length,
                "sha256": self.stderr.sha256,
                "safe_text": self.stderr.safe_text,
            },
            "pytest_failure_nodes": list(self.pytest_failure_nodes),
            "evidence_ready_before_rollback": self.evidence_ready_before_rollback,
        }

    def canonical_bytes(self) -> bytes:
        return json.dumps(
            self.to_canonical_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")


@dataclass(frozen=True, slots=True)
class DurableV3FixtureTestFailureEvidenceReceipt:
    evidence_path: str
    evidence_sha256: str
    evidence_byte_length: int
    flush_completed: bool
    fsync_completed: bool
    readback_validated: bool

    def __post_init__(self) -> None:
        if type(self.evidence_path) is not str or not self.evidence_path:
            raise _error("durable evidence path is invalid")
        if (
            type(self.evidence_sha256) is not str
            or len(self.evidence_sha256) != 64
            or any(char not in "0123456789abcdef" for char in self.evidence_sha256)
        ):
            raise _error("durable evidence digest is invalid")
        if type(self.evidence_byte_length) is not int or self.evidence_byte_length <= 0:
            raise _error("durable evidence length is invalid")
        if (self.flush_completed, self.fsync_completed, self.readback_validated) != (True, True, True):
            raise _error("durable evidence receipt is incomplete")


def _request(page_kind: raw_capture.NARRaceEntryStatusPageKind) -> raw_capture.NARRaceEntryStatusRequestIdentity:
    target = raw_capture.NARRaceEntryStatusRaceIdentity("21", date(2025, 1, 1), 6)
    return raw_capture.build_nar_race_entry_status_request_identity(
        page_kind=page_kind,
        day_scope=raw_capture.NARRaceEntryStatusDayScope(target.baba_code, target.race_date),
        request_race_no=(target.race_no if page_kind is raw_capture.NARRaceEntryStatusPageKind.DEBA_TABLE else None),
    )


def _capture(
    page_kind: raw_capture.NARRaceEntryStatusPageKind,
    body: bytes,
    second_offset: int,
) -> raw_capture.NARRaceEntryStatusResponseCapture:
    request = _request(page_kind)
    instant = _FIXED_INSTANT + timedelta(seconds=second_offset)
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


def build_deterministic_v3_fixture_test_case() -> V3FixtureTestCase:
    """Build fixed, provider-free V3 authority for the external pytest rehearsal."""

    target = raw_capture.NARRaceEntryStatusRaceIdentity("21", date(2025, 1, 1), 6)
    deba = (
        '<html><body><article class="raceCard"><section class="cardTable"><table>'
        '<tr><td class="horseNum">3</td><td><a class="horseName" '
        'href="/horse/synthetic">synthetic</a></td></tr>'
        "</table></section></article></body></html>"
    ).encode("utf-8")
    race_list = (
        '<html><body><section class="raceTable"><table>'
        '<tr class="data"><td>6R</td><td><a href="/KeibaWeb/TodayRaceInfo/DebaTable?'
        'k_babaCode=21&amp;k_raceDate=2025%2F01%2F01&amp;k_raceNo=6">entry</a></td></tr>'
        '</table><table class="changeInfo">'
        '<tr class="data"><td>6R</td><td>14</td><td>x</td><td>出走取消</td><td>x</td><td>x</td></tr>'
        "</table></section></body></html>"
    ).encode("utf-8")
    bundle = raw_capture.NARRaceEntryStatusRawCaptureBundle(
        target_race_identity=target,
        deba_table_capture=_capture(raw_capture.NARRaceEntryStatusPageKind.DEBA_TABLE, deba, 0),
        race_list_capture=_capture(raw_capture.NARRaceEntryStatusPageKind.RACE_LIST, race_list, 1),
    )
    capture_summary = profile_b.summarize_nar_race_entry_status_capture_bundle(bundle=bundle)
    profile_a_result = profile_a.diagnose_nar_race_entry_status_profile_a_v3(
        deba_table_bytes=deba,
        target=target,
    )
    profile_b_result = profile_b.diagnose_nar_race_entry_status_profile_b_v2(
        race_list_bytes=race_list,
        target=target,
    )
    safety = assess_nar_race_entry_status_raw_fixture_publication_safety_v3(
        deba_table_bytes=deba,
        race_list_bytes=race_list,
    )
    recovery = phase63.diagnose_nar_race_entry_status_profile_b_recovery(
        race_list_bytes=race_list,
        target=target,
    )
    ancestry = phase66.diagnose_nar_race_entry_status_profile_b_candidate_ancestry_recovery(
        race_list_bytes=race_list,
        target=target,
    )
    fixture_set = build_nar_race_entry_status_fixture_set_v3(
        target=target,
        capture_summary=capture_summary,
    )
    qualification = build_nar_race_entry_status_qualification_v3(
        target=target,
        fixture_set=fixture_set,
        profile_a=profile_a_result,
        profile_b=profile_b_result,
    )
    manifest = build_nar_race_entry_status_manifest_v3(
        fixture_set=fixture_set,
        qualification=qualification,
        publication_safety=safety,
    )
    plan = build_nar_race_entry_status_source_profile_publication_plan_v3(fixture_set=fixture_set)
    direct = sum(item.direct_schedule_table_descendant for item in ancestry.candidate_results)
    changes = sum(item.inside_change_info_table for item in ancestry.candidate_results)
    case = V3FixtureTestCase(
        deba,
        race_list,
        manifest,
        plan,
        recovery.target_candidate_count,
        ancestry.target_candidate_count,
        direct,
        changes,
    )
    if (
        profile_a_result.overall_result != "QUALIFIED"
        or profile_b_result.overall_result != "QUALIFIED"
        or not safety.raw_fixture_publication_safe
        or (
            case.phase63_candidate_count,
            case.phase66_candidate_count,
            case.phase66_direct_schedule_count,
            case.phase66_change_info_count,
        )
        != (2, 2, 1, 1)
    ):
        raise _error("deterministic synthetic case is not fully qualified")
    return case


def validate_nar_race_entry_status_fixture_test_import_isolation(
    *,
    repository_root: Path,
    namespace_locations: tuple[Path, ...],
    module_origins: tuple[Path, ...],
) -> str:
    """Validate exact PEP 420 and production-module origin authority."""

    if not isinstance(repository_root, Path):
        raise _error("repository_root must be a Path")
    try:
        resolved_repository = repository_root.resolve(strict=True)
        own_repository = _AUTHORIZED_REPOSITORY_ROOT.resolve(strict=True)
    except OSError as error:
        raise _error("authorized repository root is unavailable") from error
    if resolved_repository != own_repository:
        raise _error("repository root is not the reviewed module worktree")
    expected_scripts = (resolved_repository / "scripts").resolve(strict=True)
    expected_simulation = (expected_scripts / "simulation").resolve(strict=True)
    if type(namespace_locations) is not tuple or any(not isinstance(item, Path) for item in namespace_locations):
        raise _error("namespace locations must be an exact Path tuple")
    resolved_locations = tuple(item.resolve(strict=True) for item in namespace_locations)
    if resolved_locations != (expected_scripts,):
        raise _error("scripts namespace has an unexpected portion")
    if type(module_origins) is not tuple or not module_origins or any(
        not isinstance(item, Path) for item in module_origins
    ):
        raise _error("module origins must be a nonempty exact Path tuple")
    for origin in module_origins:
        resolved = origin.resolve(strict=True)
        if expected_simulation not in resolved.parents:
            raise _error("production module resolved outside authorized simulation support")
    return "PASS"


_LAUNCHER = r'''import importlib
from pathlib import Path
import sys

repository_root = Path(sys.argv[1]).resolve(strict=True)
test_path = Path(sys.argv[2]).resolve(strict=True)
sys.path.insert(0, str(repository_root))
import scripts

module_names = (
    "scripts.simulation.nar_race_entry_status_raw_capture",
    "scripts.simulation.nar_race_entry_status_source_profile_diagnostics",
    "scripts.simulation.nar_race_entry_status_source_profile_profile_a",
    "scripts.simulation.nar_race_entry_status_source_profile_publication_contract",
    "scripts.simulation.nar_race_entry_status_source_profile_publication_plan",
    "scripts.simulation.nar_race_entry_status_source_profile_structural_recovery_diagnostics",
    "scripts.simulation.nar_race_entry_status_source_profile_fixture_test_generator",
    "scripts.simulation.nar_race_entry_status_source_profile_fixture_test_preflight",
)
modules = tuple(importlib.import_module(name) for name in module_names)
preflight = modules[-1]
preflight.validate_nar_race_entry_status_fixture_test_import_isolation(
    repository_root=repository_root,
    namespace_locations=tuple(Path(item) for item in scripts.__path__),
    module_origins=tuple(Path(module.__file__) for module in modules),
)
print("PHASE79_IMPORT_ISOLATION_PASS", flush=True)
import pytest
raise SystemExit(pytest.main([
    "-q",
    "--import-mode=importlib",
    "-p",
    "no:cacheprovider",
    str(test_path),
]))
'''


def _validated_external_root(repository_root: Path, external_root: Path) -> tuple[Path, Path]:
    if not isinstance(repository_root, Path) or not isinstance(external_root, Path):
        raise _error("repository and external roots must be Path values")
    try:
        repository = repository_root.resolve(strict=True)
    except OSError as error:
        raise _error("authorized repository root is missing") from error
    if repository != _AUTHORIZED_REPOSITORY_ROOT.resolve(strict=True):
        raise _error("alternate repository root is forbidden")
    external = external_root.resolve(strict=False)
    if external == repository or repository in external.parents or external in repository.parents:
        raise _error("external mirror must be outside the repository")
    if external.exists():
        if not external.is_dir():
            raise _error("external mirror root must be a directory")
        if (external / "scripts").exists():
            raise _error("external mirror contains a competing scripts package")
        if any(external.iterdir()):
            raise _error("external mirror root must be empty")
    return repository, external


def _safe_pytest_failure_nodes(value: bytes) -> tuple[str, ...]:
    if type(value) is not bytes or not value or len(value) > MAX_PROCESS_STREAM_BYTES:
        return ()
    try:
        text = value.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return ()
    results: list[str] = []
    for match in _FAILURE_NODE.finditer(text):
        node = (
            "tests/test_nar_race_entry_status_source_profile_v3_fixtures.py::"
            + match.group(1)
        )
        if node not in results:
            results.append(node)
        if len(results) == 16:
            break
    return tuple(results)


def execute_generated_v3_fixture_test_in_external_mirror(
    *,
    repository_root: Path,
    external_root: Path,
    deba_table_bytes: bytes,
    race_list_bytes: bytes,
    manifest_bytes: bytes,
    generated_source_bytes: bytes,
    python_executable: Path,
) -> V3FixtureTestPreflightEvidence:
    """Materialize one external mirror, run isolated pytest, and always clean it."""

    repository, external = _validated_external_root(repository_root, external_root)
    if not isinstance(python_executable, Path):
        raise _error("python_executable must be a Path")
    python = python_executable.resolve(strict=True)
    values = (deba_table_bytes, race_list_bytes, manifest_bytes, generated_source_bytes)
    if any(type(value) is not bytes or not value for value in values):
        raise _error("mirror artifacts must be exact nonempty bytes")
    if len(generated_source_bytes) > MAX_GENERATED_FIXTURE_TEST_BYTES:
        raise _error("generated source exceeds the reviewed bound")
    try:
        generated_source_bytes.decode("utf-8", errors="strict")
        manifest_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise _error("mirror source and manifest must be strict UTF-8") from error
    external.mkdir(parents=True, exist_ok=False) if not external.exists() else None
    try:
        test_path = external / EXPECTED_DEDICATED_FIXTURE_TEST_PATH_V3
        deba_path = external / EXPECTED_DEBA_TABLE_PATH_V3
        race_path = external / EXPECTED_RACE_LIST_PATH_V3
        manifest_path = external / EXPECTED_MANIFEST_PATH_V3
        for path in (test_path, deba_path, race_path, manifest_path):
            path.parent.mkdir(parents=True, exist_ok=True)
        test_path.write_bytes(generated_source_bytes)
        deba_path.write_bytes(deba_table_bytes)
        race_path.write_bytes(race_list_bytes)
        manifest_path.write_bytes(manifest_bytes)
        command_payload = {
            "python_name": python.name,
            "flags": ["-I", "-B"],
            "launcher_sha256": sha256(_LAUNCHER.encode("utf-8")).hexdigest(),
            "pytest_args": ["-q", "--import-mode=importlib", "-p", "no:cacheprovider"],
        }
        command_identity = "phase79-pytest-command-v1:" + sha256(
            json.dumps(
                command_payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
        ).hexdigest()
        environment = dict(os.environ)
        environment.pop("PYTHONPATH", None)
        environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
        environment["PYTHONIOENCODING"] = "utf-8"
        completed = subprocess.run(
            [
                str(python),
                "-I",
                "-B",
                "-c",
                _LAUNCHER,
                str(repository),
                str(test_path),
            ],
            cwd=external,
            env=environment,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=False,
            timeout=120,
        )
        isolation = (
            "PASS"
            if _IMPORT_ISOLATION_TOKEN.encode("utf-8") in completed.stdout.splitlines()
            else "FAIL"
        )
        stdout = sanitize_process_stream(completed.stdout)
        stderr = sanitize_process_stream(completed.stderr)
        passed = completed.returncode == 0 and isolation == "PASS"
        return V3FixtureTestPreflightEvidence(
            gate=(
                V3_DEDICATED_FIXTURE_TEST_END_TO_END_PREFLIGHT_PASS
                if passed
                else _PREFLIGHT_FAIL_CLOSED
            ),
            generated_source_sha256=sha256(generated_source_bytes).hexdigest(),
            generated_source_byte_length=len(generated_source_bytes),
            manifest_sha256=sha256(manifest_bytes).hexdigest(),
            manifest_byte_length=len(manifest_bytes),
            pytest_command_identity=command_identity,
            pytest_return_code=completed.returncode,
            stdout=stdout,
            stderr=stderr,
            pytest_failure_nodes=_safe_pytest_failure_nodes(completed.stdout),
            test_passed=passed,
            external_mirror_root=str(external),
            production_import_isolation_result=isolation,
        )
    except subprocess.TimeoutExpired as error:
        raise _error("external pytest exceeded the reviewed timeout") from error
    finally:
        if external.exists():
            shutil.rmtree(external)


def run_nar_race_entry_status_source_profile_v3_fixture_test_preflight(
    *,
    repository_root: Path,
    python_executable: Path | None = None,
) -> V3FixtureTestPreflightEvidence:
    """Run the approved provider-free end-to-end gate in a temporary mirror."""

    case = build_deterministic_v3_fixture_test_case()
    source = render_nar_race_entry_status_source_profile_v3_fixture_test(
        deba_table_bytes=case.deba_table_bytes,
        race_list_bytes=case.race_list_bytes,
        manifest=case.manifest,
        publication_plan=case.publication_plan,
    )
    manifest_bytes = case.manifest.canonical_bytes()
    selected_python = Path(sys.executable) if python_executable is None else python_executable
    with tempfile.TemporaryDirectory(prefix="keiba-phase79-v3-fixture-preflight-") as temporary:
        root = Path(temporary)
        evidence = execute_generated_v3_fixture_test_in_external_mirror(
            repository_root=repository_root,
            external_root=root,
            deba_table_bytes=case.deba_table_bytes,
            race_list_bytes=case.race_list_bytes,
            manifest_bytes=manifest_bytes,
            generated_source_bytes=source,
            python_executable=selected_python,
        )
    if not evidence.test_passed:
        raise _error("V3 dedicated fixture-test end-to-end preflight failed")
    return evidence


def build_v3_fixture_test_failure_evidence(
    *,
    deba_table_bytes: bytes,
    race_list_bytes: bytes,
    manifest: SourceProfileManifestV3,
    publication_plan: SourceProfilePublicationPlanV3,
    generated_source_bytes: bytes,
    pytest_command_identity: str,
    pytest_return_code: int,
    stdout: bytes,
    stderr: bytes,
) -> V3FixtureTestFailureEvidence:
    """Finalize bounded safe evidence before a future rollback can begin."""

    expected_source = render_nar_race_entry_status_source_profile_v3_fixture_test(
        deba_table_bytes=deba_table_bytes,
        race_list_bytes=race_list_bytes,
        manifest=manifest,
        publication_plan=publication_plan,
    )
    if type(generated_source_bytes) is not bytes or generated_source_bytes != expected_source:
        raise _error("generated source does not match reviewed renderer output")
    if type(pytest_command_identity) is not str or not pytest_command_identity.startswith(
        "phase79-pytest-command-v1:"
    ):
        raise _error("pytest command identity is invalid")
    if type(pytest_return_code) is not int:
        raise _error("pytest return code must be exact int")
    if type(stdout) is not bytes or type(stderr) is not bytes:
        raise _error("process streams must be exact bytes")
    manifest_bytes = manifest.canonical_bytes()
    validate_nar_race_entry_status_manifest_v3(
        manifest_bytes=manifest_bytes,
        fixture_set=manifest.fixture_set,
        qualification=manifest.qualification,
        publication_safety=manifest.publication_safety,
    )
    payload = manifest.to_canonical_dict()
    documents = payload["documents"]
    projection = MappingProxyType(
        {
            "manifest_schema": payload["manifest_schema"],
            "manifest_schema_version": payload["manifest_schema_version"],
            "acquisition_semantics": payload["acquisition_semantics"],
            "provider": payload["provider"],
            "target": payload["target"],
            "documents": tuple(
                {
                    "role": item["role"],
                    "fixture_relative_path": item["fixture_relative_path"],
                    "response_sha256": item["response_sha256"],
                    "response_byte_length": item["response_byte_length"],
                }
                for item in documents
            ),
            "fixture_set_identity": payload["fixture_set_identity"],
            "qualification_identity": payload["qualification_identity"],
            "market_eligibility": payload["market_eligibility"],
        }
    )
    retained = manifest_bytes if len(manifest_bytes) <= MAX_FAILURE_MANIFEST_BYTES else None
    return V3FixtureTestFailureEvidence(
        generated_source_bytes=generated_source_bytes,
        generated_source_sha256=sha256(generated_source_bytes).hexdigest(),
        generated_source_byte_length=len(generated_source_bytes),
        retained_manifest_bytes=retained,
        manifest_sha256=sha256(manifest_bytes).hexdigest(),
        manifest_byte_length=len(manifest_bytes),
        manifest_safe_projection=projection,
        fixture_set_identity=manifest.fixture_set.identity,
        qualification_identity=manifest.qualification.identity,
        deba_sha256=sha256(deba_table_bytes).hexdigest(),
        deba_byte_length=len(deba_table_bytes),
        race_list_sha256=sha256(race_list_bytes).hexdigest(),
        race_list_byte_length=len(race_list_bytes),
        pytest_command_identity=pytest_command_identity,
        pytest_return_code=pytest_return_code,
        stdout=sanitize_process_stream(stdout),
        stderr=sanitize_process_stream(stderr),
        pytest_failure_nodes=_safe_pytest_failure_nodes(stdout),
        evidence_ready_before_rollback=True,
    )


def retain_v3_fixture_test_failure_evidence_durably(
    *,
    evidence: V3FixtureTestFailureEvidence,
    evidence_path: Path,
) -> DurableV3FixtureTestFailureEvidenceReceipt:
    """Exclusively persist, fsync, and byte-validate bounded evidence before rollback."""

    if type(evidence) is not V3FixtureTestFailureEvidence:
        raise _error("failure evidence must be exact V3FixtureTestFailureEvidence")
    if not isinstance(evidence_path, Path) or not evidence_path.is_absolute():
        raise _error("failure evidence path must be absolute Path")
    try:
        repository = _AUTHORIZED_REPOSITORY_ROOT.resolve(strict=True)
        parent = evidence_path.parent.resolve(strict=True)
    except OSError as error:
        raise _error("failure evidence parent is unavailable") from error
    resolved = (parent / evidence_path.name).resolve(strict=False)
    if resolved == repository or repository in resolved.parents:
        raise _error("failure evidence must remain outside the repository")
    if resolved.exists():
        raise _error("failure evidence path must not already exist")
    payload = evidence.canonical_bytes()
    try:
        with resolved.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        readback = resolved.read_bytes()
    except OSError as error:
        raise _error("failure evidence durability operation failed") from error
    if readback != payload:
        raise _error("failure evidence durable readback is contradictory")
    return DurableV3FixtureTestFailureEvidenceReceipt(
        evidence_path=str(resolved),
        evidence_sha256=sha256(payload).hexdigest(),
        evidence_byte_length=len(payload),
        flush_completed=True,
        fsync_completed=True,
        readback_validated=True,
    )


__all__ = (
    "MAX_FAILURE_MANIFEST_BYTES",
    "MAX_PROCESS_STREAM_BYTES",
    "DurableV3FixtureTestFailureEvidenceReceipt",
    "V3_DEDICATED_FIXTURE_TEST_END_TO_END_PREFLIGHT_PASS",
    "V3FixtureTestCase",
    "V3FixtureTestFailureEvidence",
    "V3FixtureTestPreflightError",
    "V3FixtureTestPreflightEvidence",
    "build_deterministic_v3_fixture_test_case",
    "build_v3_fixture_test_failure_evidence",
    "execute_generated_v3_fixture_test_in_external_mirror",
    "run_nar_race_entry_status_source_profile_v3_fixture_test_preflight",
    "retain_v3_fixture_test_failure_evidence_durably",
    "validate_nar_race_entry_status_fixture_test_import_isolation",
)
