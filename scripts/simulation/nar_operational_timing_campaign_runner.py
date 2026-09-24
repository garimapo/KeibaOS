"""Controlled no-network Phase104 execution-authority composition.

This module does not schedule races or publish timing attempts. Phase105 must
consume the returned process-local capability in a separately reviewed wrapper.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import importlib
import re
import sqlite3
import sys
import time
from typing import Callable

from scripts.simulation.nar_operational_timing_archive_bootstrap import bootstrap_nar_operational_timing_runtime_archive
from scripts.simulation.nar_operational_timing_attempt_archive_bootstrap import bootstrap_nar_operational_timing_attempt_archive
from scripts.simulation.nar_operational_timing_campaign_lock import NAROperationalTimingCampaignLock
from scripts.simulation.nar_operational_timing_runtime_source_provenance import (
    NARRuntimeSourceBundle, require_sealed_module_origins, verify_bundle_against_git_objects,
)
from scripts.simulation.nar_operational_timing_runtime_profile import (
    derive_runtime_dependency_profile, derive_static_runtime_transport_profile,
)
from scripts.simulation.nar_operational_timing_runtime_execution import (
    NAROperationalTimingRuntimeBinding, NAROperationalTimingCampaignExecutionClaim,
    NAROperationalTimingCampaignReadinessVerificationReceipt,
)
from scripts.simulation.nar_operational_timing_session_activation_v2 import (
    qualify_nar_operational_timing_session_activation_v2,
    NARTimingSessionActivationQualificationStateV2,
)
from scripts.simulation.nar_operational_timing_observability import _utc
from scripts.simulation.sqlite_nar_operational_timing_runtime_execution_archive import (
    SQLiteNAROperationalTimingRuntimeExecutionArchive, _ISSUANCE_MARKER,
)


_CRITICAL_MODULES = (
    "scripts.simulation.nar_operational_timing_observability",
    "scripts.simulation.nar_operational_timing_observability_v2",
    "scripts.simulation.nar_operational_timing_session_activation_v2",
    "scripts.simulation.nar_operational_timing_runtime_execution",
    "scripts.simulation.nar_operational_timing_campaign_runner",
    "scripts.simulation.nar_historical_daily_target_bootstrap_live_capture",
    "scripts.simulation.nar_historical_daily_target_live_capture",
    "scripts.simulation.nar_official_response_live_capture",
    "scripts.simulation.nar_market_odds_raw_acquisition",
    "scripts.simulation.historical_input_snapshot_builder",
    "scripts.simulation.historical_input_snapshot_freeze_receipt",
    "scripts.simulation.historical_prediction_bet_plan_execution",
    "scripts.simulation.persisted_bet_plan_service",
)


class NARCurrentProcessExecutionCapability:
    """Nonpersistent trusted API discipline; never reconstruct from archive row."""

    __slots__ = ("claim_identity", "binding_identity", "session_identity", "_owner")

    def __init__(self, *, claim_identity: str, binding_identity: str,
                 session_identity: str, _owner: object) -> None:
        if _owner is None:
            raise RuntimeError("capability requires controlled runner")
        self.claim_identity = claim_identity
        self.binding_identity = binding_identity
        self.session_identity = session_identity
        self._owner = _owner

    def require_current_owner(self, runner: NAROperationalTimingCampaignRunner) -> None:
        if (runner is not self._owner or not runner.lock.held_by_current_process
                or runner._active_claim_identity != self.claim_identity):
            raise RuntimeError("execution capability is not owned by this locked process")


class NAROperationalTimingCampaignRunner:
    """Holds one archive lock across bootstrap and one claim; no provider operation."""

    __slots__ = ("lock", "repository_root", "bundle_root", "bundle", "utc_clock",
                 "session_identity", "_connection", "_archive", "_attempted", "_active_claim_identity",
                 "_attempt_archive", "_enable_attempt_archive", "monotonic_timer_ns", "_next_attempt_sequence")

    def __init__(self, *, archive_path: Path, repository_root: Path,
                 bundle_root: Path, bundle: NARRuntimeSourceBundle, session_identity: str,
                 utc_clock: Callable[[], datetime] | None = None,
                 monotonic_timer_ns: Callable[[], int] | None = None,
                 enable_attempt_archive: bool = False) -> None:
        self.lock = NAROperationalTimingCampaignLock(archive_path=archive_path)
        self.repository_root = repository_root.resolve(strict=True)
        self.bundle_root = bundle_root.resolve(strict=True)
        if type(bundle) is not NARRuntimeSourceBundle:
            raise ValueError("exact sealed bundle authority required")
        self.bundle = bundle
        if (type(session_identity) is not str or re.fullmatch(
                r"nar-operational-timing-session-v2:[0-9a-f]{64}", session_identity) is None):
            raise ValueError("runner requires one exact V2 session identity")
        self.session_identity = session_identity
        self.utc_clock = utc_clock or (lambda: datetime.now(timezone.utc))
        if type(enable_attempt_archive) is not bool:
            raise ValueError("attempt archive option must be exact bool")
        self._enable_attempt_archive = enable_attempt_archive
        self.monotonic_timer_ns = monotonic_timer_ns or time.perf_counter_ns
        self._next_attempt_sequence = 0
        self._connection = None
        self._archive = None
        self._attempted = False
        self._active_claim_identity = None
        self._attempt_archive = None

    def __enter__(self) -> NAROperationalTimingCampaignRunner:
        self.lock.acquire()
        try:
            connection = sqlite3.connect(self.lock.archive_path)
            self._connection = connection
            connection.execute("PRAGMA foreign_keys=ON")
            if self._enable_attempt_archive:
                bootstrap_nar_operational_timing_attempt_archive(connection=connection, campaign_lock=self.lock)
            else:
                bootstrap_nar_operational_timing_runtime_archive(connection=connection, campaign_lock=self.lock)
            self._archive = SQLiteNAROperationalTimingRuntimeExecutionArchive(connection=connection)
            if self._enable_attempt_archive:
                from scripts.simulation.sqlite_nar_operational_timing_attempt_archive import SQLiteNAROperationalTimingAttemptArchive
                self._attempt_archive = SQLiteNAROperationalTimingAttemptArchive(connection=connection)
            return self
        except BaseException:
            if self._connection is not None:
                self._connection.close()
                self._connection = None
            self.lock.release()
            raise

    def __exit__(self, *_: object) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None
            self._archive = None
            self._attempt_archive = None
        self._active_claim_identity = None
        self.lock.release()

    @property
    def attempt_archive(self):
        if not self._enable_attempt_archive or self._attempt_archive is None or not self.lock.held_by_current_process:
            raise RuntimeError("Phase105 attempt archive requires current locked runner")
        return self._attempt_archive

    def next_attempt_sequence(self, capability: NARCurrentProcessExecutionCapability) -> int:
        capability.require_current_owner(self)
        if self._attempt_archive is None:
            raise RuntimeError("Phase105 attempt archive is not active")
        sequence = self._next_attempt_sequence
        self._next_attempt_sequence += 1
        return sequence

    def _require_isolated_source(self) -> None:
        if not sys.flags.isolated or not sys.dont_write_bytecode:
            raise RuntimeError("official source requires isolated no-bytecode child")
        verify_bundle_against_git_objects(repository_root=self.repository_root, bundle=self.bundle)
        import scripts
        tuple(importlib.import_module(name) for name in _CRITICAL_MODULES)
        if self._enable_attempt_archive:
            tuple(importlib.import_module(name) for name in (
                "scripts.simulation.nar_operational_timing_attempt_v2",
                "scripts.simulation.nar_operational_timing_guarded_session",
                "scripts.simulation.nar_operational_timing_passive_wrapper",
                "scripts.simulation.sqlite_nar_operational_timing_attempt_archive",
            ))
        modules = tuple(module for name, module in sys.modules.items()
                        if name.startswith("scripts.") and getattr(module, "__file__", None))
        for name, module in tuple(sys.modules.items()):
            if name == "scripts" or not name.startswith("scripts.") or getattr(module, "__file__", None):
                continue
            portions = getattr(module, "__path__", None)
            if portions is None or not tuple(portions) or not all(
                self.bundle_root in Path(part).resolve(strict=True).parents for part in portions
            ):
                raise RuntimeError("KeibaOS namespace portion escapes sealed bundle")
        require_sealed_module_origins(
            bundle=self.bundle, bundle_root=self.bundle_root,
            scripts_namespace_locations=tuple(Path(x) for x in scripts.__path__),
            module_origins=tuple(Path(x.__file__) for x in modules),
        )

    def issue_current_process_execution(self) -> NARCurrentProcessExecutionCapability:
        if self._archive is None or not self.lock.held_by_current_process or self._attempted:
            raise RuntimeError("one held campaign runner may issue only one execution")
        self._attempted = True
        self._require_isolated_source()
        archive = self._archive
        session = archive.v2.load_session(session_identity=self.session_identity)
        if session is None:
            raise RuntimeError("exact V2 measurement session is not archived")
        activation = qualify_nar_operational_timing_session_activation_v2(
            session=session, archive=archive.v2)
        if activation.state is not NARTimingSessionActivationQualificationStateV2.OFFICIAL_PREDECLARED_MEASUREMENT_SESSION:
            raise RuntimeError("V2 session was not prospectively activated")
        if self.bundle.commit_sha != session.configuration.software_commit_sha:
            raise RuntimeError("runtime Git source differs from declared software commit")
        dependency = derive_runtime_dependency_profile()
        transport = derive_static_runtime_transport_profile()
        transport.require_matches_declared(session.configuration)
        archive.save_bundle(bundle=self.bundle)
        archive.save_dependency_profile(profile=dependency)
        archive.save_transport_profile(profile=transport)
        binding = NAROperationalTimingRuntimeBinding(
            session.configuration.configuration_identity, session.session_identity,
            activation.declaration.declaration_identity,
            activation.verification_receipt.verification_identity,
            self.bundle.bundle_identity, dependency.profile_identity,
            transport.profile_identity, self.lock.scope_identity,
        )
        archive.save_binding(binding=binding, _issuance_marker=_ISSUANCE_MARKER)
        if archive.load_binding(binding_identity=binding.binding_identity) != binding:
            raise RuntimeError("runtime binding did not exact-reload")
        if archive.load_claim_for_session(session_identity=session.session_identity) is not None:
            raise RuntimeError("this measurement session is permanently consumed")
        claim = NAROperationalTimingCampaignExecutionClaim(
            session.configuration.configuration_identity, session.session_identity,
            activation.declaration.declaration_identity,
            activation.verification_receipt.verification_identity,
            binding.binding_identity, self.bundle.bundle_identity, self.lock.scope_identity,
        )
        inserted = archive.save_claim(claim=claim, _issuance_marker=_ISSUANCE_MARKER)
        if not inserted or archive.load_claim_for_session(session_identity=session.session_identity) != claim:
            raise RuntimeError("execution claim did not newly publish and exact-reload")
        verified_at = self.utc_clock()
        receipt = NAROperationalTimingCampaignReadinessVerificationReceipt(
            session.configuration.configuration_identity, session.session_identity,
            binding.binding_identity, claim.claim_identity, verified_at,
        )
        archive.save_readiness(receipt=receipt, _issuance_marker=_ISSUANCE_MARKER)
        if archive.load_readiness_for_claim(claim_identity=claim.claim_identity) != receipt:
            raise RuntimeError("campaign readiness did not exact-reload")
        if (receipt.readiness_verified_at > session.measurement_start_at
                or _utc(self.utc_clock()) > session.measurement_start_at):
            raise RuntimeError("campaign readiness completed after fixed session start")
        self._active_claim_identity = claim.claim_identity
        return NARCurrentProcessExecutionCapability(
            claim_identity=claim.claim_identity, binding_identity=binding.binding_identity,
            session_identity=session.session_identity, _owner=self,
        )
