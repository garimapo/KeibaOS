"""Controlled no-network diagnostic composition over Phase104/105 authority."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from typing import Callable, Mapping

import requests

from scripts.simulation.nar_operational_timing_diagnostic_campaign import (
    NAROperationalTimingDiagnosticFixtureBundleV1 as Fixture,
    NAROperationalTimingDiagnosticCampaignPlanV1 as Plan,
    NAROperationalTimingDiagnosticExecutionDeclarationV1 as Declaration,
    NARDiagnosticContinuationV1,
)
from scripts.simulation.nar_operational_timing_diagnostic_archive_migration import bootstrap_nar_operational_timing_diagnostic_archive
from scripts.simulation.nar_operational_timing_observability import NARTimingLoadContext
from scripts.simulation.nar_operational_timing_passive_wrapper import measure_nar_operation
from scripts.simulation.nar_operational_timing_guarded_session import guarded_session_factory
from scripts.simulation.sqlite_nar_operational_timing_diagnostic_archive import (
    SQLiteNAROperationalTimingDiagnosticArchive, _DIAGNOSTIC_ISSUANCE_MARKER,
)


class NARDiagnosticFakeHTTPAdapter(requests.adapters.HTTPAdapter):
    """Only deterministic in-process adapter outcomes; no socket operation."""

    def __init__(self, *, body: bytes = b"", failure: str | None = None,
                 content_type: str | None = None) -> None:
        if (type(body) is not bytes or failure not in (None, "CONNECT_TIMEOUT", "READ_TIMEOUT", "TRANSPORT")
                or (content_type is not None and type(content_type) is not str)):
            raise ValueError("closed fake adapter outcome required")
        super().__init__(max_retries=0)
        self.body = body
        self.failure = failure
        self.content_type = content_type
        self.send_count = 0

    def send(self, request, **kwargs):
        self.send_count += 1
        if self.failure == "CONNECT_TIMEOUT":
            raise requests.exceptions.ConnectTimeout("synthetic diagnostic connect timeout")
        if self.failure == "READ_TIMEOUT":
            raise requests.exceptions.ReadTimeout("synthetic diagnostic read timeout")
        if self.failure == "TRANSPORT":
            raise requests.exceptions.ConnectionError("synthetic diagnostic transport failure")
        response = requests.Response()
        response.status_code = 200
        response.url = request.url
        response.raw = BytesIO(self.body)
        response.request = request
        if self.content_type is not None:
            response.headers["Content-Type"] = self.content_type
        return response


@dataclass(frozen=True, slots=True)
class NARDiagnosticOperationV1:
    invoke: Callable[[], object]
    load_context: NARTimingLoadContext
    expected_url: str | None = None
    artifact_sha256: str | None = None


class NAROperationalTimingDiagnosticContext:
    """Requires the same live Phase104 capability for each planned Phase105 call."""

    __slots__ = ("runner", "capability", "archive", "plan", "declaration", "_cursor", "_terminal_status")

    def __init__(self, *, runner: object, capability: object, archive: SQLiteNAROperationalTimingDiagnosticArchive,
                 plan: Plan, declaration: Declaration) -> None:
        capability.require_current_owner(runner)
        if (type(archive) is not SQLiteNAROperationalTimingDiagnosticArchive
                or archive.load_plan(plan_identity=plan.plan_identity) != plan
                or archive.load_declaration_for_claim(claim_identity=capability.claim_identity) != declaration
                or declaration.plan_identity != plan.plan_identity):
            raise RuntimeError("exact predeclared diagnostic authority required")
        self.runner = runner
        self.capability = capability
        self.archive = archive
        self.plan = plan
        self.declaration = declaration
        self._cursor = 0
        self._terminal_status: dict[str, str] = {}

    def _runnable(self, node) -> bool:
        if node.continuation is NARDiagnosticContinuationV1.INDEPENDENT:
            return True
        statuses = tuple(self._terminal_status.get(key) for key in node.predecessors)
        if any(x not in ("SUCCESS", "FAILURE", "TIMEOUT", "UNSUPPORTED") for x in statuses):
            return False
        if node.continuation is NARDiagnosticContinuationV1.REQUIRES_ALL_PREDECESSOR_SUCCESSFUL_OUTPUTS:
            return all(x == "SUCCESS" for x in statuses)
        return True

    def measure_next(self, *, node_key: str, operation: NARDiagnosticOperationV1):
        self.capability.require_current_owner(self.runner)
        if type(operation) is not NARDiagnosticOperationV1:
            raise ValueError("closed diagnostic operation required")
        while self._cursor < len(self.plan.nodes) and not self._runnable(self.plan.nodes[self._cursor]):
            self._terminal_status[self.plan.nodes[self._cursor].key] = "SKIPPED"
            self._cursor += 1
        if self._cursor >= len(self.plan.nodes) or self.plan.nodes[self._cursor].key != node_key:
            raise RuntimeError("next diagnostic operation is not the exact runnable plan node")
        node = self.plan.nodes[self._cursor]
        if (node.transport_kind is None) != (operation.expected_url is None):
            raise ValueError("diagnostic request URL/transport contradicts plan")
        if operation.expected_url is not None and sha256(operation.expected_url.encode("utf-8")).hexdigest() != node.expected_url_sha256:
            raise ValueError("diagnostic request URL digest differs from plan")
        if self.runner._next_attempt_sequence != sum(
                1 for x in self._terminal_status.values() if x in ("SUCCESS", "FAILURE", "TIMEOUT", "UNRESOLVED", "PRECONDITION")):
            raise RuntimeError("diagnostic executed-attempt sequence differs")
        before = self.runner._next_attempt_sequence
        try:
            result = measure_nar_operation(
                runner=self.runner, capability=self.capability, stage=node.stage,
                correlation=node.correlation, load_context=operation.load_context,
                operation=operation.invoke, expected_url=operation.expected_url,
                transport_kind=node.transport_kind, artifact_sha256=operation.artifact_sha256)
        except BaseException:
            attempt = self._attempt_at_sequence(before)
            if attempt is None:
                raise
            terminal = self.archive.attempts.load_terminal_for_attempt(attempt_identity=attempt.attempt_identity)
            environment = self.archive.attempts.load_environment_for_attempt(attempt_identity=attempt.attempt_identity)
            if terminal is None:
                self._terminal_status[node.key] = "UNRESOLVED"
            elif node.transport_kind is not None and (environment is None or environment.qualification.value != "QUALIFIED_DIRECT_REQUEST_ENVIRONMENT"):
                self._terminal_status[node.key] = "PRECONDITION"
            else:
                self._terminal_status[node.key] = terminal.disposition.value
            self._cursor += 1
            raise
        attempt = self._attempt_at_sequence(before)
        terminal = (self.archive.attempts.load_terminal_for_attempt(attempt_identity=attempt.attempt_identity)
                    if attempt is not None else None)
        self._terminal_status[node.key] = terminal.disposition.value if terminal is not None else "UNRESOLVED"
        self._cursor += 1
        return result

    def _attempt_at_sequence(self, sequence: int):
        row = self.archive._connection.execute(
            "SELECT identity FROM nar_operational_timing_v2_attempts WHERE claim_identity=? AND attempt_sequence=?",
            (self.capability.claim_identity, sequence)).fetchone()
        return self.archive.attempts.load_attempt(attempt_identity=row[0]) if row else None

    def run(self, *, operations: Mapping[str, NARDiagnosticOperationV1]) -> dict[str, object]:
        """Execute every runnable declared node once, retaining failures for the DAG."""
        results: dict[str, object] = {}
        for node in self.plan.nodes:
            if not self._runnable(node):
                self._terminal_status[node.key] = "SKIPPED"
                self._cursor += 1
                continue
            if node.key not in operations:
                raise RuntimeError("runnable diagnostic plan node has no operation")
            try:
                results[node.key] = self.measure_next(node_key=node.key, operation=operations[node.key])
            except Exception as error:
                if node.key not in self._terminal_status:
                    raise
                results[node.key] = error
        return results


def issue_diagnostic_execution_context(*, runner: object, capability: object,
                                       fixture: Fixture, plan: Plan) -> NAROperationalTimingDiagnosticContext:
    """Install companion only after normal Phase105 claim/readiness under the same lock."""
    capability.require_current_owner(runner)
    if (type(fixture) is not Fixture or type(plan) is not Plan
            or plan.fixture_bundle_identity != fixture.bundle_identity
            or plan.session_identity != capability.session_identity
            or fixture.commit_sha != runner.bundle.commit_sha):
        raise RuntimeError("diagnostic plan/fixture/runtime ancestry differs")
    fixture.read_verified_bytes(repository_root=runner.repository_root)
    runner._require_isolated_source()
    if runner._connection.execute(
            "SELECT 1 FROM nar_operational_timing_v2_attempts WHERE claim_identity=? LIMIT 1",
            (capability.claim_identity,)).fetchone():
        raise RuntimeError("diagnostic authority must precede first attempt")
    bootstrap_nar_operational_timing_diagnostic_archive(connection=runner._connection, campaign_lock=runner.lock)
    archive = SQLiteNAROperationalTimingDiagnosticArchive(connection=runner._connection)
    archive.save_fixture(fixture=fixture, _issuance_marker=_DIAGNOSTIC_ISSUANCE_MARKER)
    if archive.load_fixture(fixture_identity=fixture.bundle_identity) != fixture:
        raise RuntimeError("diagnostic fixture did not exact-reload")
    archive.save_plan(plan=plan, _issuance_marker=_DIAGNOSTIC_ISSUANCE_MARKER)
    if archive.load_plan(plan_identity=plan.plan_identity) != plan:
        raise RuntimeError("diagnostic plan did not exact-reload")
    declaration = Declaration(plan.plan_identity, capability.claim_identity,
                              plan.configuration_identity, plan.session_identity, fixture.bundle_identity)
    capability.require_current_owner(runner)
    archive.save_declaration(declaration=declaration, _issuance_marker=_DIAGNOSTIC_ISSUANCE_MARKER)
    if archive.load_declaration_for_claim(claim_identity=capability.claim_identity) != declaration:
        raise RuntimeError("diagnostic declaration did not exact-reload")
    return NAROperationalTimingDiagnosticContext(runner=runner, capability=capability,
                                                 archive=archive, plan=plan, declaration=declaration)


def diagnostic_guarded_session_factory(*, runner: object, capability: object, transport_kind,
                                       adapter: NARDiagnosticFakeHTTPAdapter):
    """Use with a transport's private session and adapter factories; never sends a socket."""
    if type(adapter) is not NARDiagnosticFakeHTTPAdapter:
        raise ValueError("exact fake diagnostic adapter required")
    return guarded_session_factory(runner=runner, capability=capability,
                                   transport_kind=transport_kind), lambda: adapter
