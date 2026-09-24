from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.simulation.nar_operational_timing_campaign_lock import NAROperationalTimingCampaignLock
from scripts.simulation.nar_operational_timing_runtime_source_provenance import (
    materialize_sealed_git_source_bundle, require_sealed_module_origins,
    verify_bundle_against_git_objects, verify_sealed_bundle,
)
from scripts.simulation.nar_operational_timing_runtime_profile import (
    NARStaticRuntimeTransportProfile, derive_runtime_dependency_profile,
    derive_static_runtime_transport_profile,
)
from scripts.simulation.nar_operational_timing_observability import (
    NARHTTPTransportKind, NARHTTPTransportProfile,
)
from scripts.simulation.nar_operational_timing_observability_v2 import (
    NAROperationalTimingMeasurementConfigurationV2 as Configuration,
    NAROperationalTimingStageV2 as Stage,
)


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def test_git_object_bundle_ignores_mutable_worktree_and_rejects_corruption(tmp_path):
    root, parent = tmp_path / "repo", tmp_path / "bundle"
    root.mkdir()
    parent.mkdir()
    _git(root, "init")
    _git(root, "remote", "add", "origin", "https://github.com/garimapo/KeibaOS.git")
    (root / "scripts" / "simulation").mkdir(parents=True)
    source = root / "scripts" / "simulation" / "sample.py"
    source.write_text("VALUE = 1\n", encoding="utf-8")
    (root / "main.py").write_text("pass\n", encoding="utf-8")
    _git(root, "add", "scripts/simulation/sample.py", "main.py")
    subprocess.run(["git", "-C", str(root), "-c", "user.name=Test", "-c",
                    "user.email=test@example.invalid", "commit", "-m", "fixture"],
                   check=True, capture_output=True)
    commit = _git(root, "rev-parse", "HEAD")
    bundle, output = materialize_sealed_git_source_bundle(
        repository_root=root, commit_sha=commit, destination_parent=parent)
    assert bundle.commit_sha == commit
    assert bundle.tree_sha == _git(root, "rev-parse", "HEAD^{tree}")
    assert bundle.bundle_identity.endswith(bundle.manifest_sha256)
    source.write_text("VALUE = 999\n", encoding="utf-8")
    verify_bundle_against_git_objects(repository_root=root, bundle=bundle)
    verify_sealed_bundle(bundle=bundle, bundle_root=output)
    assert (output / "scripts" / "simulation" / "sample.py").read_text() == "VALUE = 1\n"
    require_sealed_module_origins(bundle=bundle, bundle_root=output,
        scripts_namespace_locations=(output / "scripts",),
        module_origins=(output / "scripts" / "simulation" / "sample.py",))
    with pytest.raises(ValueError):
        require_sealed_module_origins(bundle=bundle, bundle_root=output,
            scripts_namespace_locations=(root / "scripts",),
            module_origins=(output / "scripts" / "simulation" / "sample.py",))
    with pytest.raises(ValueError):
        require_sealed_module_origins(bundle=bundle, bundle_root=output,
            scripts_namespace_locations=(output / "scripts",), module_origins=(source,))
    (output / "scripts" / "simulation" / "sample.py").write_text("corrupt\n")
    with pytest.raises(ValueError):
        verify_sealed_bundle(bundle=bundle, bundle_root=output)


def test_runtime_dependency_and_static_transport_profiles_are_content_addressed():
    dependency = derive_runtime_dependency_profile()
    assert dependency.from_json(dependency.canonical_bytes().decode()) == dependency
    assert replace(dependency, requests_version="999").profile_identity != dependency.profile_identity
    transport = derive_static_runtime_transport_profile()
    assert transport.from_json(transport.canonical_bytes().decode()) == transport
    by_kind = {x.kind: x for x in transport.descriptors}
    assert [(x.connect_timeout_microseconds, x.read_timeout_microseconds)
            for x in transport.descriptors] == [(10_000_000, 10_000_000)] * 3 + [(10_000_000, 20_000_000)]
    assert by_kind[NARHTTPTransportKind.NAR_MARKET_ODDS_RAW_HTTP].trust_env is False
    assert all(by_kind[k].trust_env for k in NARHTTPTransportKind
               if k is not NARHTTPTransportKind.NAR_MARKET_ODDS_RAW_HTTP)
    assert all(x.adapter_retry_total == 0 and x.adapter_retry_read is False
               and x.allow_redirects is False and x.verify_tls and x.stream
               and x.accept_encoding == "identity" for x in transport.descriptors)
    assert replace(transport.descriptors[0], connect_timeout_microseconds=11_000_000) != transport.descriptors[0]
    declared = Configuration("a" * 40, (Stage.SNAPSHOT_CONSTRUCTION,),
                             tuple(NARHTTPTransportProfile(x.kind, x.connect_timeout_microseconds,
                                                           x.read_timeout_microseconds)
                                   for x in transport.descriptors))
    transport.require_matches_declared(declared)
    different = NARStaticRuntimeTransportProfile((
        replace(transport.descriptors[0], connect_timeout_microseconds=11_000_000),
        *transport.descriptors[1:],
    ))
    assert different.profile_identity != transport.profile_identity
    with pytest.raises(ValueError, match="timeout mismatch"):
        different.require_matches_declared(declared)
    with pytest.raises(ValueError):
        replace(transport.descriptors[0], adapter_retry_total=1)


def test_local_lock_excludes_second_owner_and_releases_without_consuming_session(tmp_path):
    archive = tmp_path / "timing.sqlite"
    first = NAROperationalTimingCampaignLock(archive_path=archive)
    second = NAROperationalTimingCampaignLock(archive_path=archive)
    assert first.scope_identity == second.scope_identity
    with first:
        assert first.held_by_current_process
        with pytest.raises(RuntimeError):
            second.acquire()
    with second:
        assert second.held_by_current_process
    assert not second.held_by_current_process


def test_os_lock_excludes_second_process(tmp_path):
    archive = tmp_path / "timing.sqlite"
    script = ("from pathlib import Path\n"
              "from scripts.simulation.nar_operational_timing_campaign_lock import NAROperationalTimingCampaignLock\n"
              "import sys\n"
              "with NAROperationalTimingCampaignLock(archive_path=Path(sys.argv[1])):\n"
              " print('READY', flush=True)\n"
              " sys.stdin.readline()\n")
    child = subprocess.Popen([sys.executable, "-B", "-c", script, str(archive)],
                             cwd=Path(__file__).resolve().parents[1],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True)
    try:
        assert child.stdout.readline().strip() == "READY"
        with pytest.raises((OSError, RuntimeError)):
            NAROperationalTimingCampaignLock(archive_path=archive).acquire()
    finally:
        child.stdin.write("\n")
        child.stdin.flush()
        assert child.wait(timeout=10) == 0
