"""Real Git-object sealed diagnostic rehearsal in an isolated no-network child."""

from pathlib import Path
import os
import shutil
import subprocess
import sys

from scripts.simulation.nar_operational_timing_runtime_source_provenance import materialize_sealed_git_source_bundle


ROOT = Path(__file__).resolve().parents[1]
_CHANGED_SOURCE = (
    "scripts/simulation/nar_operational_timing_diagnostic_campaign.py",
    "scripts/simulation/nar_operational_timing_diagnostic_archive_migration.py",
    "scripts/simulation/sqlite_nar_operational_timing_diagnostic_archive.py",
    "scripts/simulation/nar_operational_timing_campaign_reconciliation.py",
    "scripts/simulation/nar_operational_timing_diagnostic_harness.py",
    "scripts/simulation/nar_operational_timing_attempt_archive_migration.py",
    "scripts/simulation/sqlite_nar_operational_timing_attempt_archive.py",
    "scripts/simulation/nar_operational_timing_runtime_execution_archive_migration.py",
    "scripts/simulation/nar_historical_daily_target_bootstrap_live_capture.py",
    "scripts/simulation/nar_historical_daily_target_live_capture.py",
    "scripts/simulation/nar_official_response_live_capture.py",
    "scripts/simulation/nar_market_odds_raw_acquisition.py",
)

_CHILD = r'''
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from hashlib import sha256
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
from scripts.simulation.nar_operational_timing_observability import (
    NARHTTPTransportProfile, NARHTTPTransportKind, NARTimingCorrelation,
    NARTimingCorrelationScope, NARTimingLoadContext,
)
from scripts.simulation.nar_operational_timing_observability_v2 import (
    NAROperationalTimingMeasurementConfigurationV2 as Configuration,
    NAROperationalTimingMeasurementSessionV2 as Session,
    NAROperationalTimingStageV2 as Stage,
)
from scripts.simulation.nar_operational_timing_session_activation_v2 import issue_nar_operational_timing_session_activation_v2
from scripts.simulation.nar_operational_timing_campaign_runner import NAROperationalTimingCampaignRunner
from scripts.simulation.nar_operational_timing_diagnostic_campaign import (
    NAROperationalTimingDiagnosticFixtureBundleV1 as Fixture,
    NAROperationalTimingDiagnosticCampaignPlanV1 as Plan,
    NARDiagnosticPlanNodeSpecV1 as Node,
    NARDiagnosticContinuationV1 as Continuation,
    NARDiagnosticCompositionV1 as Composition,
)
from scripts.simulation.nar_operational_timing_diagnostic_harness import (
    NARDiagnosticFakeHTTPAdapter, NARDiagnosticOperationV1,
    issue_diagnostic_execution_context, diagnostic_guarded_session_factory,
)
from scripts.simulation.nar_operational_timing_campaign_reconciliation import reconcile_diagnostic_archive
from scripts.simulation.nar_historical_daily_target_bootstrap_live_capture import (
    RequestsNARMonthlyConveneInfoBootstrapHTTPTransport as Transport,
    NARMonthlyConveneInfoBootstrapLiveCaptureService as CaptureService,
    _PageKind, _URLS, _CONTENT_TYPES,
)
from scripts.simulation.nar_historical_daily_target_bootstrap import resolve_nar_monthly_convene_info_root_locator
bundle, _ = _git_manifest(root, commit)
profile = derive_static_runtime_transport_profile()
stages = (Stage.BOOTSTRAP_HOME_ACQUISITION, Stage.NORMALIZATION)
config = Configuration(commit, stages, tuple(
    NARHTTPTransportProfile(x.kind, x.connect_timeout_microseconds, x.read_timeout_microseconds)
    for x in profile.descriptors))
start = datetime(2030, 1, 1, tzinfo=timezone.utc)
session = Session(config, start, start + timedelta(hours=1))
fixture_path = "tests/fixtures/nar_daily_target_bootstrap/nar_home_supplier.utf8.html"
fixture = Fixture.from_git(repository_root=root, repository_identity="garimapo/KeibaOS",
                           commit_sha=commit, paths=(fixture_path,))
url = _URLS[_PageKind.OFFICIAL_HOME]
url_sha = sha256(url.encode("utf-8")).hexdigest()
correlation = NARTimingCorrelation(NARTimingCorrelationScope.PROVIDER)
nodes = (
    Node("home", Stage.BOOTSTRAP_HOME_ACQUISITION, 0, "request-url-sha256:" + url_sha,
         correlation, (), Continuation.INDEPENDENT, Composition.EXCLUSIVE_LEAF,
         fixture_path, NARHTTPTransportKind.NAR_BOOTSTRAP_HTTP, url_sha),
    Node("normalize", Stage.NORMALIZATION, 1, "correlation:" + correlation.correlation_identity,
         correlation, ("home",), Continuation.REQUIRES_ALL_PREDECESSOR_SUCCESSFUL_OUTPUTS,
         Composition.EXCLUSIVE_LEAF),
)
plan = Plan("garimapo/KeibaOS", commit, config.configuration_identity,
            session.session_identity, fixture.bundle_identity, nodes, "home-fixture")
times = iter((start - timedelta(seconds=2), start - timedelta(seconds=1),
              *(start + timedelta(seconds=i) for i in range(1, 30))))
ticks = iter(range(0, 100_000_000, 100_000))
runner = NAROperationalTimingCampaignRunner(
    archive_path=archive_path, repository_root=root, bundle_root=sealed, bundle=bundle,
    session_identity=session.session_identity, utc_clock=lambda: next(times),
    monotonic_timer_ns=lambda: next(ticks), enable_attempt_archive=True)
with runner:
    authority = runner.attempt_archive.runtime.v2
    authority.save_configuration(configuration=config)
    authority.save_session(session=session)
    issue_nar_operational_timing_session_activation_v2(
        session=session, archive=authority, utc_clock=lambda: start - timedelta(minutes=1))
    capability = runner.issue_current_process_execution()
    context = issue_diagnostic_execution_context(runner=runner, capability=capability,
                                                 fixture=fixture, plan=plan)
    adapter = NARDiagnosticFakeHTTPAdapter(
        body=fixture.read_verified_bytes(repository_root=root)[fixture_path],
        content_type=_CONTENT_TYPES[_PageKind.OFFICIAL_HOME])
    session_factory, adapter_factory = diagnostic_guarded_session_factory(
        runner=runner, capability=capability, transport_kind=NARHTTPTransportKind.NAR_BOOTSTRAP_HTTP,
        adapter=adapter)
    transport = Transport(_session_factory=session_factory,
                          _diagnostic_adapter_factory=adapter_factory)
    class Sink:
        def save_supplier_capture(self, *, capture):
            pass
    service = CaptureService(archive=Sink(), transport=transport, utc_clock=lambda: start)
    captures = {}
    def home():
        captures["home"] = service.capture_official_home()
        return captures["home"]
    load = NARTimingLoadContext(1, 1, False)
    results = context.run(operations={
        "home": NARDiagnosticOperationV1(home, load, expected_url=url),
        "normalize": NARDiagnosticOperationV1(
            lambda: resolve_nar_monthly_convene_info_root_locator(homepage_capture=captures["home"]),
            NARTimingLoadContext(1, 0, False)),
    })
    assert not isinstance(results["home"], Exception), results["home"]
    assert not isinstance(results["normalize"], Exception), results["normalize"]
    assert adapter.send_count == 1
    report = reconcile_diagnostic_archive(archive=context.archive, declaration=context.declaration)
    assert report.completeness == "COMPLETE_AS_PREDECLARED_DIAGNOSTIC_PLAN", report.payload()
    assert all(x.state.value == "OBSERVED_AS_PLANNED" for x in report.nodes)
    assert report.payload()["official_eligibility"] == "DIAGNOSTIC_ONLY"
    print("SEALED_DIAGNOSTIC_REHEARSAL_OK:" + report.reconciliation_identity)
'''


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args],
                            capture_output=True, text=True, check=True)
    return result.stdout.strip()


def test_real_sealed_child_rehearses_production_capture_and_normalization_without_network(tmp_path):
    final_commit = os.environ.get("KEIBAOS_PHASE106_SEALED_COMMIT_SMOKE")
    if final_commit is None:
        # A local throwaway Git object tree includes pending source before the
        # final repository commit exists. It never represents official source.
        clone = tmp_path / "source-parent" / "reviewed-source"
        clone.parent.mkdir()
        subprocess.run(["git", "clone", "--quiet", "--no-hardlinks", str(ROOT), str(clone)],
                       check=True, capture_output=True)
        _git(clone, "remote", "set-url", "origin", "https://github.com/garimapo/KeibaOS.git")
        for relative in _CHANGED_SOURCE:
            destination = clone / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, destination)
        _git(clone, "add", *_CHANGED_SOURCE)
        _git(clone, "-c", "user.name=Diagnostic Test", "-c", "user.email=diagnostic@example.invalid",
             "commit", "-qm", "temporary sealed diagnostic test tree")
        commit = _git(clone, "rev-parse", "HEAD")
    else:
        clone = ROOT
        commit = final_commit
        assert _git(ROOT, "rev-parse", "HEAD") == commit
    bundle_parent = tmp_path / "bundle-parent"
    bundle_parent.mkdir()
    _, sealed = materialize_sealed_git_source_bundle(
        repository_root=clone, commit_sha=commit, destination_parent=bundle_parent)
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT)
    for key in ("HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE"):
        environment.pop(key, None)
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", _CHILD, str(sealed), str(clone),
         str(tmp_path / "diagnostic-child.sqlite"), commit],
        cwd=ROOT, env=environment, capture_output=True, text=True, timeout=180)
    assert result.returncode == 0, result.stderr
    assert "SEALED_DIAGNOSTIC_REHEARSAL_OK:" in result.stdout
