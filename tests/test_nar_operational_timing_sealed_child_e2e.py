"""Real Phase104 capability success from the reviewed Git-object sealed child; no HTTP."""

from pathlib import Path
import os
import subprocess
import sys

from scripts.simulation.nar_operational_timing_runtime_source_provenance import materialize_sealed_git_source_bundle


ROOT = Path(__file__).resolve().parents[1]
COMMIT = "8d6411f7d886caf70db44e1e92ccd1f5bd6711d8"

_CHILD = r'''
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
sealed = Path(sys.argv[1]).resolve(strict=True)
root = Path(sys.argv[2]).resolve(strict=True)
archive_path = Path(sys.argv[3])
commit = sys.argv[4]
assert sys.flags.isolated and sys.dont_write_bytecode
assert str(sealed) not in sys.path
sys.path.insert(0, str(sealed))
import scripts
assert tuple(Path(p).resolve(strict=True) for p in scripts.__path__) == (sealed / "scripts",)
from scripts.simulation.nar_operational_timing_runtime_source_provenance import _git_manifest
from scripts.simulation.nar_operational_timing_runtime_profile import derive_static_runtime_transport_profile
from scripts.simulation.nar_operational_timing_observability import NARHTTPTransportProfile
from scripts.simulation.nar_operational_timing_observability_v2 import (
    NAROperationalTimingMeasurementConfigurationV2 as Configuration,
    NAROperationalTimingMeasurementSessionV2 as Session,
    NAROperationalTimingStageV2 as Stage,
)
from scripts.simulation.nar_operational_timing_session_activation_v2 import issue_nar_operational_timing_session_activation_v2
from scripts.simulation.nar_operational_timing_campaign_runner import NAROperationalTimingCampaignRunner
from scripts.simulation.sqlite_nar_operational_timing_runtime_execution_archive import SQLiteNAROperationalTimingRuntimeExecutionArchive
bundle, _ = _git_manifest(root, commit)
profile = derive_static_runtime_transport_profile()
config = Configuration(commit, (Stage.SNAPSHOT_CONSTRUCTION,), tuple(
    NARHTTPTransportProfile(x.kind, x.connect_timeout_microseconds, x.read_timeout_microseconds)
    for x in profile.descriptors))
start = datetime(2030, 1, 1, tzinfo=timezone.utc)
session = Session(config, start, start + timedelta(hours=1))
times = iter((start - timedelta(seconds=2), start - timedelta(seconds=1)))
runner = NAROperationalTimingCampaignRunner(
    archive_path=archive_path, repository_root=root, bundle_root=sealed,
    bundle=bundle, session_identity=session.session_identity, utc_clock=lambda: next(times))
with runner:
    authority = SQLiteNAROperationalTimingRuntimeExecutionArchive(connection=runner._connection)
    authority.v2.save_configuration(configuration=config)
    authority.v2.save_session(session=session)
    issue_nar_operational_timing_session_activation_v2(
        session=session, archive=authority.v2, utc_clock=lambda: start - timedelta(minutes=1))
    capability = runner.issue_current_process_execution()
    capability.require_current_owner(runner)
    print("SEALED_CHILD_CAPABILITY_OK:" + capability.claim_identity)
'''


def test_real_isolated_sealed_child_issues_capability_without_network(tmp_path):
    _, sealed = materialize_sealed_git_source_bundle(
        repository_root=ROOT, commit_sha=COMMIT, destination_parent=tmp_path)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)  # -I must ignore this mutable-worktree shadow route.
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", _CHILD, str(sealed), str(ROOT),
         str(tmp_path / "child-archive.sqlite"), COMMIT],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, result.stderr
    assert "SEALED_CHILD_CAPABILITY_OK:nar-operational-timing-campaign-execution-v1:" in result.stdout
