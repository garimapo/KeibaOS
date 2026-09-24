"""Deterministic, read-only diagnostic evidence classification; no Delta arithmetic."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from hashlib import sha256

from scripts.simulation.nar_operational_timing_attempt_v2 import (
    NAROperationalTimingAttemptV2 as Attempt, NAROperationalTimingTerminalV2 as Terminal,
    NARRequestEffectiveEnvironmentVerification as Environment,
    NARTimingPublicationOverheadV2 as Overhead,
    NARRequestEnvironmentQualification, NARTimingTerminalDispositionV2,
)
from scripts.simulation.nar_operational_timing_diagnostic_campaign import (
    NAROperationalTimingDiagnosticCampaignPlanV1 as Plan,
    NAROperationalTimingDiagnosticExecutionDeclarationV1 as Declaration,
    NARDiagnosticContinuationV1,
)
from scripts.simulation.nar_operational_timing_observability import _json_bytes
from scripts.simulation.nar_operational_timing_observability_v2 import NAROperationalTimingStageV2 as Stage
from scripts.simulation import nar_operational_timing_attempt_archive_migration as attempt_schema
from scripts.simulation import nar_operational_timing_diagnostic_archive_migration as schema
from scripts.simulation.sqlite_nar_operational_timing_diagnostic_archive import SQLiteNAROperationalTimingDiagnosticArchive


class NARDiagnosticObservationQualification(StrEnum):
    QUALIFIED_OPERATIONAL_TIMING_OBSERVATION = "QUALIFIED_OPERATIONAL_TIMING_OBSERVATION"
    NONQUALIFYING_REQUEST_ENVIRONMENT = "NONQUALIFYING_REQUEST_ENVIRONMENT"
    UNRESOLVED_ATTEMPT = "UNRESOLVED_ATTEMPT"
    EXECUTION_ANCESTRY_INVALID = "EXECUTION_ANCESTRY_INVALID"
    DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"


class NARDiagnosticPlanNodeState(StrEnum):
    OBSERVED_AS_PLANNED = "OBSERVED_AS_PLANNED"
    EXPECTED_NOT_EXECUTABLE_DUE_TO_UPSTREAM_FAILURE = "EXPECTED_NOT_EXECUTABLE_DUE_TO_UPSTREAM_FAILURE"
    BLOCKED_BY_UNRESOLVED_PREDECESSOR = "BLOCKED_BY_UNRESOLVED_PREDECESSOR"
    PRECONDITION_BLOCKED = "PRECONDITION_BLOCKED"
    MISSING_UNEXPLAINED = "MISSING_UNEXPLAINED"
    EVIDENCE_INTEGRITY_FAILURE = "EVIDENCE_INTEGRITY_FAILURE"


@dataclass(frozen=True, slots=True)
class NARDiagnosticNodeReconciliationV1:
    node_key: str
    node_identity: str
    state: NARDiagnosticPlanNodeState
    attempt_identity: str | None
    actual_attempt_sequence: int | None
    inner_observation: NARDiagnosticObservationQualification | None
    terminal_disposition: NARTimingTerminalDispositionV2 | None
    missing_publication_overhead: tuple[str, ...]
    composition: str
    predecessors: tuple[str, ...]

    def payload(self) -> dict[str, object]:
        return {"node_key": self.node_key, "node_identity": self.node_identity,
                "state": self.state.value, "attempt_identity": self.attempt_identity,
                "actual_attempt_sequence": self.actual_attempt_sequence,
                "inner_observation": self.inner_observation.value if self.inner_observation else None,
                "official_eligibility": "DIAGNOSTIC_ONLY",
                "terminal_disposition": self.terminal_disposition.value if self.terminal_disposition else None,
                "missing_publication_overhead": list(self.missing_publication_overhead),
                "composition": self.composition, "predecessors": list(self.predecessors)}


@dataclass(frozen=True, slots=True)
class NARDiagnosticCampaignReconciliationV1:
    plan_identity: str
    declaration_identity: str
    claim_identity: str
    nodes: tuple[NARDiagnosticNodeReconciliationV1, ...]
    extra_attempt_identities: tuple[str, ...]
    sequence_errors: tuple[int, ...]
    ancestry_errors: tuple[str, ...]
    completeness: str
    schema_version: int = 1
    reconciliation_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "reconciliation_sha256", sha256(self.canonical_bytes()).hexdigest())

    @property
    def reconciliation_identity(self) -> str:
        return "nar-operational-timing-diagnostic-reconciliation-v1:" + self.reconciliation_sha256

    def payload(self) -> dict[str, object]:
        return {"schema_version": self.schema_version, "plan_identity": self.plan_identity,
                "declaration_identity": self.declaration_identity, "claim_identity": self.claim_identity,
                "planned_node_count": len(self.nodes), "nodes": [x.payload() for x in self.nodes],
                "extra_attempt_identities": list(self.extra_attempt_identities),
                "sequence_errors": list(self.sequence_errors), "ancestry_errors": list(self.ancestry_errors),
                "official_eligibility": "DIAGNOSTIC_ONLY", "completeness": self.completeness,
                "critical_path_rule": "DAG_COMPOSITION_REQUIRED_NO_DURATION_SUM_OR_DELTA"}

    def canonical_bytes(self) -> bytes:
        return _json_bytes(self.payload())


def _matches(node, attempt: Attempt, plan: Plan, claim_identity: str) -> bool:
    return (attempt.campaign_execution_identity == claim_identity
            and attempt.configuration_identity == plan.configuration_identity
            and attempt.session_identity == plan.session_identity
            and attempt.stage is node.stage and attempt.correlation == node.correlation
            and attempt.expected_request_url_sha256 == node.expected_url_sha256
            and (attempt.expected_http_environment_policy.value if attempt.expected_http_environment_policy else None)
            == ("DIRECT_REQUEST_ENVIRONMENT_V1" if node.transport_kind else None))


def reconcile_diagnostic_evidence(
    *, plan: Plan, declaration: Declaration, attempts: tuple[Attempt, ...],
    terminals: tuple[Terminal, ...], environments: tuple[Environment, ...],
    overhead: tuple[Overhead, ...], ancestry_errors: tuple[str, ...] = (),
) -> NARDiagnosticCampaignReconciliationV1:
    """Pure evidence derivation. Planned slots map to dense executed attempt sequences."""
    if (type(plan) is not Plan or type(declaration) is not Declaration
            or declaration.plan_identity != plan.plan_identity
            or declaration.session_identity != plan.session_identity
            or declaration.configuration_identity != plan.configuration_identity
            or declaration.fixture_bundle_identity != plan.fixture_bundle_identity):
        raise ValueError("diagnostic reconciliation requires exact plan/declaration ancestry")
    if any(type(x) is not Attempt for x in attempts) or any(type(x) is not Terminal for x in terminals):
        raise ValueError("diagnostic evidence types differ")
    if any(type(x) is not Environment for x in environments) or any(type(x) is not Overhead for x in overhead):
        raise ValueError("diagnostic child evidence types differ")
    ordered = tuple(sorted(attempts, key=lambda x: (x.attempt_sequence, x.attempt_identity)))
    by_sequence = {x.attempt_sequence: x for x in ordered}
    actual_sequences = tuple(x.attempt_sequence for x in ordered)
    sequence_errors = tuple(sorted(
        {x for x in actual_sequences if actual_sequences.count(x) != 1}
        | (set(range(len(ordered))) - set(actual_sequences))))
    terminal_by_attempt = {x.attempt_identity: x for x in terminals}
    environment_by_attempt = {x.attempt_identity: x for x in environments}
    overhead_pairs = {(x.attempt_identity, x.stage) for x in overhead}
    evidence_errors = list(ancestry_errors)
    attempt_ids = {x.attempt_identity for x in attempts}
    if len(terminal_by_attempt) != len(terminals):
        evidence_errors.append("DUPLICATE_TERMINAL")
    if len(environment_by_attempt) != len(environments):
        evidence_errors.append("DUPLICATE_REQUEST_ENVIRONMENT")
    if len(overhead_pairs) != len(overhead):
        evidence_errors.append("DUPLICATE_PUBLICATION_OVERHEAD")
    if (any(x.attempt_identity not in attempt_ids for x in terminals + environments)
            or any(x.attempt_identity not in attempt_ids or x.campaign_execution_identity != declaration.claim_identity
                   for x in overhead)):
        evidence_errors.append("ORPHAN_OR_CROSS_EXECUTION_CHILD_EVIDENCE")
    used: set[str] = set()
    results: list[NARDiagnosticNodeReconciliationV1] = []
    by_key: dict[str, NARDiagnosticNodeReconciliationV1] = {}
    next_sequence = 0
    for node in plan.nodes:
        parents = tuple(by_key[key] for key in node.predecessors)
        blocked = None
        if any(p.state in (NARDiagnosticPlanNodeState.EVIDENCE_INTEGRITY_FAILURE,
                           NARDiagnosticPlanNodeState.BLOCKED_BY_UNRESOLVED_PREDECESSOR)
               or p.inner_observation is NARDiagnosticObservationQualification.UNRESOLVED_ATTEMPT for p in parents):
            blocked = NARDiagnosticPlanNodeState.BLOCKED_BY_UNRESOLVED_PREDECESSOR
        elif any(p.state is NARDiagnosticPlanNodeState.PRECONDITION_BLOCKED for p in parents):
            blocked = NARDiagnosticPlanNodeState.PRECONDITION_BLOCKED
        elif any(p.state is NARDiagnosticPlanNodeState.EXPECTED_NOT_EXECUTABLE_DUE_TO_UPSTREAM_FAILURE for p in parents):
            blocked = NARDiagnosticPlanNodeState.EXPECTED_NOT_EXECUTABLE_DUE_TO_UPSTREAM_FAILURE
        elif (node.continuation is NARDiagnosticContinuationV1.REQUIRES_ALL_PREDECESSOR_SUCCESSFUL_OUTPUTS
              and any(p.state is NARDiagnosticPlanNodeState.OBSERVED_AS_PLANNED
                      and p.terminal_disposition is not NARTimingTerminalDispositionV2.SUCCESS
                      for p in parents)):
            blocked = NARDiagnosticPlanNodeState.EXPECTED_NOT_EXECUTABLE_DUE_TO_UPSTREAM_FAILURE
        elif any(p.state is NARDiagnosticPlanNodeState.MISSING_UNEXPLAINED for p in parents):
            blocked = NARDiagnosticPlanNodeState.MISSING_UNEXPLAINED

        candidate = by_sequence.get(next_sequence)
        if blocked is not None:
            state, attempt, terminal, inner, missing = blocked, None, None, None, ()
        elif candidate is None or not _matches(node, candidate, plan, declaration.claim_identity):
            state, attempt, terminal, inner, missing = NARDiagnosticPlanNodeState.MISSING_UNEXPLAINED, None, None, None, ()
        else:
            attempt = candidate
            used.add(attempt.attempt_identity)
            next_sequence += 1
            terminal = terminal_by_attempt.get(attempt.attempt_identity)
            environment = environment_by_attempt.get(attempt.attempt_identity)
            missing = tuple(stage.value for stage in (Stage.ATTEMPT_START_PUBLICATION, Stage.TERMINAL_PUBLICATION)
                            if (attempt.attempt_identity, stage) not in overhead_pairs
                            and (stage is Stage.ATTEMPT_START_PUBLICATION or terminal is not None))
            if terminal is None:
                state, inner = NARDiagnosticPlanNodeState.EVIDENCE_INTEGRITY_FAILURE, NARDiagnosticObservationQualification.UNRESOLVED_ATTEMPT
            elif node.transport_kind is not None and (environment is None or environment.qualification is not NARRequestEnvironmentQualification.QUALIFIED_DIRECT_REQUEST_ENVIRONMENT):
                state, inner = NARDiagnosticPlanNodeState.PRECONDITION_BLOCKED, NARDiagnosticObservationQualification.NONQUALIFYING_REQUEST_ENVIRONMENT
            elif terminal.attempt_identity != attempt.attempt_identity:
                state, inner = NARDiagnosticPlanNodeState.EVIDENCE_INTEGRITY_FAILURE, NARDiagnosticObservationQualification.EXECUTION_ANCESTRY_INVALID
            else:
                state, inner = NARDiagnosticPlanNodeState.OBSERVED_AS_PLANNED, NARDiagnosticObservationQualification.QUALIFIED_OPERATIONAL_TIMING_OBSERVATION
        result = NARDiagnosticNodeReconciliationV1(
            node.key, plan.node_identity(node.key), state,
            attempt.attempt_identity if attempt else None,
            attempt.attempt_sequence if attempt else None, inner,
            terminal.disposition if terminal else None, missing,
            node.composition.value, node.predecessors)
        results.append(result)
        by_key[node.key] = result
    extras = tuple(sorted(x.attempt_identity for x in attempts if x.attempt_identity not in used))
    defects = extras or sequence_errors or evidence_errors or any(
        x.state in (NARDiagnosticPlanNodeState.MISSING_UNEXPLAINED,
                    NARDiagnosticPlanNodeState.EVIDENCE_INTEGRITY_FAILURE,
                    NARDiagnosticPlanNodeState.BLOCKED_BY_UNRESOLVED_PREDECESSOR)
        or x.missing_publication_overhead for x in results)
    return NARDiagnosticCampaignReconciliationV1(
        plan.plan_identity, declaration.declaration_identity, declaration.claim_identity,
        tuple(results), extras, sequence_errors, tuple(sorted(set(evidence_errors))),
        "EVIDENCE_INCOMPLETE" if defects else "COMPLETE_AS_PREDECLARED_DIAGNOSTIC_PLAN")


def reconcile_diagnostic_archive(*, archive: SQLiteNAROperationalTimingDiagnosticArchive,
                                 declaration: Declaration) -> NARDiagnosticCampaignReconciliationV1:
    """Read and verify immutable rows, then perform the same pure derivation."""
    if type(archive) is not SQLiteNAROperationalTimingDiagnosticArchive or type(declaration) is not Declaration:
        raise ValueError("exact diagnostic archive/declaration required")
    schema.require_nar_operational_timing_diagnostic_archive_schema(archive._connection)
    if archive.load_declaration_for_claim(claim_identity=declaration.claim_identity) != declaration:
        raise ValueError("diagnostic declaration is not archived exactly")
    plan = archive.load_plan(plan_identity=declaration.plan_identity)
    if plan is None:
        raise ValueError("diagnostic plan is unavailable")
    connection = archive._connection
    attempt_ids = tuple(x[0] for x in connection.execute(
        f"SELECT identity FROM {attempt_schema.ATTEMPTS} WHERE claim_identity=? ORDER BY attempt_sequence,identity",
        (declaration.claim_identity,)))
    attempts = tuple(archive.attempts.load_attempt(attempt_identity=x) for x in attempt_ids)
    terminals = tuple(value for x in attempts if (value := archive.attempts.load_terminal_for_attempt(
        attempt_identity=x.attempt_identity)) is not None)
    environments = tuple(value for x in attempts if (value := archive.attempts.load_environment_for_attempt(
        attempt_identity=x.attempt_identity)) is not None)
    overhead_rows = tuple(connection.execute(
        f"SELECT identity,attempt_identity,claim_identity,payload_json FROM {attempt_schema.OVERHEAD} WHERE claim_identity=? ORDER BY identity",
        (declaration.claim_identity,)))
    overhead = tuple(Overhead.from_json(x[3]) for x in overhead_rows)
    for row, value in zip(overhead_rows, overhead):
        if (row[0] != value.overhead_identity or row[1] != value.attempt_identity
                or row[2] != value.campaign_execution_identity):
            raise ValueError("archived diagnostic publication overhead contradicts canonical row")
    return reconcile_diagnostic_evidence(plan=plan, declaration=declaration,
                                         attempts=attempts, terminals=terminals,
                                         environments=environments, overhead=overhead)
