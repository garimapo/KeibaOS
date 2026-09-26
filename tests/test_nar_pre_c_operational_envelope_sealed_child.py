"""Post-commit/pre-push verification. Deliberately deferred in uncommitted execution.

Set KEIBAOS_PHASE108_REVIEWED_COMMIT only after explicit local commit approval.
No worktree implementation is ever represented as sealed Git-object authority.
"""
from pathlib import Path
import os
import subprocess
import sys
import pytest

from scripts.simulation.nar_operational_timing_runtime_source_provenance import materialize_sealed_git_source_bundle

ROOT = Path(__file__).resolve().parents[1]
REVIEWED_COMMIT = os.environ.get("KEIBAOS_PHASE108_REVIEWED_COMMIT")
_CHILD = r'''
import sys, socket
from pathlib import Path
sealed, repository, temporary = map(Path, sys.argv[1:4])
commit, mode = sys.argv[4:6]
assert sys.flags.isolated and sys.dont_write_bytecode
sys.path.insert(0, str(sealed))
import scripts
assert tuple(Path(x).resolve() for x in scripts.__path__) == (sealed / "scripts",)
from scripts.simulation.nar_pre_c_operational_envelope import NARPreCHistoryMode
from scripts.simulation.nar_pre_c_operational_envelope_harness import run_phase108_no_network_rehearsal
def reject_socket(*args, **kwargs):
    raise AssertionError("provider network is forbidden in sealed diagnostic rehearsal")
socket.socket = reject_socket
result, calls = run_phase108_no_network_rehearsal(repository_root=repository, bundle_root=sealed,
    commit_sha=commit, temporary_root=temporary, history_mode=NARPreCHistoryMode(mode))
assert result.state == "COMPLETE_NONOVERLAPPING_MONOTONIC_PRE_C_FREEZE_ENVELOPE", result
assert result.classification == "DIAGNOSTIC_ONLY_NO_NETWORK"
for name, module in tuple(sys.modules.items()):
    if name.startswith("scripts.") and getattr(module, "__file__", None):
        assert sealed in Path(module.__file__).resolve().parents, (name, module.__file__)
assert len(calls) == (1 if mode == "PRESTAGED_HISTORY" else 4)
print("FINAL_COMMIT_SEALED_PHASE108_REHEARSAL_PASS:" + mode + ":" + result.identity)
'''


@pytest.mark.skipif(REVIEWED_COMMIT is None, reason="FINAL_COMMIT_SEALED_SOURCE_VERIFICATION = PENDING_EXPLICIT_COMMIT_APPROVAL")
@pytest.mark.parametrize("mode", ("PRESTAGED_HISTORY", "ROOT_GENERATED_HISTORY"))
def test_final_commit_sealed_phase108_rehearsal(tmp_path, mode):
    bundle, sealed = materialize_sealed_git_source_bundle(repository_root=ROOT, commit_sha=REVIEWED_COMMIT, destination_parent=tmp_path)
    assert bundle.commit_sha == REVIEWED_COMMIT
    assert (sealed / "scripts/simulation/nar_pre_c_operational_envelope_harness.py").is_file()
    env = os.environ.copy()
    for key in ("HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY", "NO_PROXY", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE"):
        env.pop(key, None)
        env.pop(key.lower(), None)
    env["NETRC"] = str(tmp_path / "absent-netrc")
    env["PYTHONPATH"] = str(ROOT)  # Real -I must ignore worktree shadow.
    completed = subprocess.run([sys.executable, "-I", "-B", "-c", _CHILD, str(sealed), str(ROOT),
        str(tmp_path), REVIEWED_COMMIT, mode], cwd=ROOT, env=env, capture_output=True, text=True, timeout=180)
    assert completed.returncode == 0, completed.stderr + completed.stdout
    assert "FINAL_COMMIT_SEALED_PHASE108_REHEARSAL_PASS:" + mode in completed.stdout
