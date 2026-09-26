"""Deterministic read-only target-root reconciliation; no clocks, repairs or Delta."""
from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
import json
from scripts.simulation.nar_pre_c_operational_envelope import (
    Authority, NARPreCPrestagedInputManifestV1 as Manifest, NARPreCOperationalEnvelopeExecutionPlanV1 as Plan,
    NARPreCOperationalEnvelopeV1 as Root, NARPreCEnvelopeStartEvidenceV1 as Start,
    NARCurrentEntryDiscoveryClosureV1 as Entries, NARPastRaceDiscoveryClosureV1 as History,
    NARPreCEnvelopeCompletionEvidenceV1 as Completion, NARPreCHistoryMode as Mode,
    source_record_sha, elapsed_microseconds_from_ns, snapshot_identity_bytes,
)
from scripts.simulation.nar_pre_c_operational_envelope_harness import entry_population, history_events, prerequisite_proof
from scripts.simulation.nar_historical_input_source import normalize_nar_historical_input_source_records
from scripts.simulation.nar_historical_past_race_discovery import discover_nar_historical_past_race_history
from scripts.simulation.nar_historical_past_race_source import normalize_nar_historical_past_race_source_record
from scripts.simulation.nar_historical_past_race_absence_source import normalize_nar_historical_past_race_absence_source_record
from scripts.simulation.historical_input_snapshot_builder import build_historical_input_snapshot
from scripts.simulation.historical_input_snapshots import compute_historical_input_snapshot_content_sha256
from scripts.simulation.nar_operational_timing_observability import _time
from scripts.simulation.sqlite_nar_operational_timing_observability_archive import SQLiteNAROperationalTimingObservabilityArchive
from scripts.simulation import nar_operational_timing_observability_archive_migration as timing_base_schema


class NARPreCEnvelopeReconciliationState(StrEnum):
    COMPLETE = "COMPLETE_NONOVERLAPPING_MONOTONIC_PRE_C_FREEZE_ENVELOPE"
    TELEMETRY = "INCOMPLETE_TIMING_TELEMETRY"
    PROVIDER = "INCOMPLETE_PROVIDER_FAILURE"
    DISCOVERY = "INCOMPLETE_DISCOVERY_CLOSURE"
    FREEZE = "INCOMPLETE_SNAPSHOT_FREEZE"
    EXECUTION = "INCOMPLETE_ROOT_EXECUTION"
    INTEGRITY = "INCOMPLETE_EXECUTION_INTEGRITY"
    SESSION = "INCOMPLETE_SESSION_WINDOW"
    CUTOFF = "SNAPSHOT_FREEZE_COMPLETED_AFTER_PREDICTION_CUTOFF"


@dataclass(frozen=True, slots=True)
class NARPreCEnvelopeReconciliationV1(Authority):
    prefix = "nar-pre-c-envelope-reconciliation-v1"
    root_identity: str
    target_scope_identity: str
    manifest_identity: str
    plan_identity: str
    start_identity: str | None
    completion_identity: str | None
    state: str
    elapsed_microseconds: int | None
    child_observations: tuple[tuple[str, str, str, str | None], ...]
    errors: tuple[str, ...]
    missing_requests: tuple[str, ...]
    unexpected_attempts: tuple[str, ...]
    overhead_defects: tuple[str, ...]
    semantic_freeze_identity: str | None
    claim_identity: str
    session_identity: str
    current_entry_closure_identity: str | None
    past_race_closure_identities: tuple[str, ...]
    snapshot_prerequisite_proof: tuple[tuple[str, str, str], ...]
    semantic_freeze_result: str
    timing_endpoint_result: str
    provider_request_nodes: tuple[tuple[str, str, str, int], ...]
    closure_request_dependencies: tuple[tuple[str, str, str], ...]
    unsatisfied_closure_dependencies: tuple[tuple[str, str, str], ...]
    classification: str = "DIAGNOSTIC_ONLY_NO_NETWORK"
    critical_path_owner: str = "ROOT_ONLY_NO_ADDITIVE_CHILD_TIMING"

    def __post_init__(self):
        NARPreCEnvelopeReconciliationState(self.state)
        if self.classification != "DIAGNOSTIC_ONLY_NO_NETWORK" or self.critical_path_owner != "ROOT_ONLY_NO_ADDITIVE_CHILD_TIMING":
            raise ValueError("diagnostic root reconciliation cannot promote authority or add child timing")


def reconcile_pre_c_evidence(*, root, manifest, plan, start, completion, entry_closure,
                            history_closures, attempts, terminals, environments, overhead,
                            captures, prestaged_history, snapshot, receipt, session, claim, readiness,
                            request_nodes=(), dependency_edges=()):
    """Immutable supplied evidence only. Missing evidence remains missing."""
    errors, missing, extras, overhead_defects, observations = [], [], [], [], []
    expected = [plan.current_url]
    capture_by_id = {c.capture_id: c for c in captures}
    if len(capture_by_id) != len(captures):
        errors.append("DUPLICATE_CAPTURE")
    if (root.scope != manifest.scope or root.scope != plan.scope or root.manifest_identity != manifest.identity
            or root.execution_plan_identity != plan.identity or plan.manifest_identity != manifest.identity
            or claim is None or claim.claim_identity != root.claim_identity or claim.binding_identity != root.binding_identity
            or claim.bundle_identity != root.runtime_bundle_identity or manifest.claim_identity != root.claim_identity
            or session is None or session.session_identity != root.session_identity
            or readiness is None or readiness.claim_identity != root.claim_identity
            or readiness.readiness_verified_at > session.measurement_start_at):
        errors.append("EXECUTION_ANCESTRY_INVALID")
    if start is None or start.root_identity != root.identity:
        errors.append("START_AUTHORITY_MISSING")
    elif manifest.available_at > start.started_at:
        errors.append("PRESTAGED_AVAILABILITY_INVALID")
    terminal_by_attempt = {t.attempt_identity: t for t in terminals}
    environment_by_attempt = {e.attempt_identity: e for e in environments}
    if len(terminal_by_attempt) != len(terminals) or len(environment_by_attempt) != len(environments):
        errors.append("DUPLICATE_CHILD_EVIDENCE")
    if len({a.attempt_identity for a in attempts}) != len(attempts):
        errors.append("DUPLICATE_ATTEMPT")
    current = None
    records, history_records = (), tuple(prestaged_history)
    if entry_closure is not None:
        if start is None or entry_closure.start_identity != start.identity:
            errors.append("ENTRY_CLOSURE_ANCESTRY_INVALID")
        current = capture_by_id.get(entry_closure.parent_capture_identity)
        expected += [x[3] for x in entry_closure.entries]
    if current is None:
        current_matches = [c for c in captures if c.canonical_source_url == plan.current_url]
        if len(current_matches) == 1:
            current = current_matches[0]
    if current is not None:
        try:
            records = normalize_nar_historical_input_source_records(response=current.to_supplied_official_response())
            if entry_closure is not None and (entry_population(records) != entry_closure.entries or
                    tuple(sorted((r.source_id, source_record_sha(r)) for r in records)) != entry_closure.normalized_records):
                errors.append("CURRENT_ENTRY_CLOSURE_CONTENT_INVALID")
        except Exception:
            errors.append("CURRENT_NORMALIZATION_INVALID")
    if plan.history_mode is Mode.GENERATED:
        if current is not None and entry_closure is None:
            errors.append("CURRENT_ENTRY_CLOSURE_MISSING")
        entry_by_id = {r.external_entry_id: r for r in records if r.record_kind == "entry"}
        if len({h.entry_identity for h in history_closures}) != len(history_closures):
            errors.append("DUPLICATE_HISTORY_CLOSURE")
        if any(h.entry_identity not in entry_by_id for h in history_closures):
            errors.append("UNEXPECTED_HISTORY_CLOSURE")
        history_records = []
        for h in history_closures:
            expected += list(h.request_urls)
            horse = capture_by_id.get(h.parent_capture_identity)
            try:
                if entry_closure is None or h.entry_closure_identity != entry_closure.identity or horse is None:
                    raise ValueError("history closure parent missing")
                track = next(r for r in records if r.record_kind == "track")
                entry = entry_by_id[h.entry_identity]
                discovery = discover_nar_historical_past_race_history(target_track_record=track, target_entry_record=entry, horse_history_response=horse.to_supplied_official_response())
                if history_events(discovery) != h.events or discovery.proven_zero_history != h.proven_zero_history or discovery.target_external_horse_id != h.horse_identity:
                    raise ValueError("history closure is partial")
                if h.proven_zero_history:
                    history_records.append(normalize_nar_historical_past_race_absence_source_record(target_track_record=track, target_entry_record=entry, horse_history_response=horse.to_supplied_official_response()))
                else:
                    for url in h.request_urls:
                        matches = [c for c in captures if c.canonical_source_url == url]
                        if len(matches) == 1:
                            history_records.append(normalize_nar_historical_past_race_source_record(target_entry_record=entry,
                                horse_history_response=horse.to_supplied_official_response(), race_result_response=matches[0].to_supplied_official_response()))
            except Exception:
                errors.append("PAST_RACE_CLOSURE_INVALID:" + h.entry_identity)
        history_records = tuple(history_records)
    elif entry_closure is not None or history_closures:
        errors.append("PRESTAGED_ROOT_HAS_UNPLANNED_HISTORY_DISCOVERY")
    attempt_by_url = {}
    for a in sorted(attempts, key=lambda a: a.attempt_sequence):
        t, e = terminal_by_attempt.get(a.attempt_identity), environment_by_attempt.get(a.attempt_identity)
        ancestry_ok = (a.campaign_execution_identity == root.claim_identity and a.session_identity == root.session_identity
            and claim is not None and a.configuration_identity == claim.configuration_identity and a.correlation.external_race_id == root.scope.external_race_id
            and a.correlation.cutoff_plan_sha256 == root.scope.cutoff_plan_sha256
            and a.correlation.target_set_sha256 == root.scope.target_set_sha256
            and a.stage.value == "OFFICIAL_RESPONSE_ACQUISITION"
            and a.expected_http_environment_policy is not None and a.expected_http_environment_policy.value == "DIRECT_REQUEST_ENVIRONMENT_V1"
            and start is not None and a.attempt_admitted_at >= start.started_at and a.attempt_sequence >= start.first_attempt_sequence
            and session is not None and session.admits(a.attempt_admitted_at))
        urls = [url for url in set(expected) if sha256(url.encode()).hexdigest() == a.expected_request_url_sha256]
        if not ancestry_ok:
            errors.append("CHILD_ANCESTRY_INVALID:" + a.attempt_identity)
        if len(urls) != 1:
            extras.append(a.attempt_identity)
        else:
            attempt_by_url.setdefault(urls[0], []).append(a)
        if t is None:
            inner = "UNRESOLVED_ATTEMPT"
            errors.append("UNRESOLVED_ATTEMPT:" + a.attempt_identity)
        elif e is None or e.qualification.value != "QUALIFIED_DIRECT_REQUEST_ENVIRONMENT":
            inner = "NONQUALIFYING_REQUEST_ENVIRONMENT"
        elif not ancestry_ok:
            inner = "EXECUTION_ANCESTRY_INVALID"
        else:
            inner = "QUALIFIED_OPERATIONAL_TIMING_OBSERVATION"
        if e is not None and (e.prepared_url_sha256 != a.expected_request_url_sha256 or not e.expected_url_match):
            errors.append("ENVIRONMENT_CHILD_CONTRADICTION:" + a.attempt_identity)
        observations.append((a.attempt_identity, inner, t.disposition.value if t else "UNRESOLVED", t.failure_classification.value if t and t.failure_classification else None))
        stages = {o.stage.value for o in overhead if o.attempt_identity == a.attempt_identity and o.campaign_execution_identity == root.claim_identity}
        for required in ("ATTEMPT_START_PUBLICATION", "TERMINAL_PUBLICATION"):
            if required not in stages:
                overhead_defects.append(a.attempt_identity + ":" + required)
        if t is not None and t.operation_finished_at < a.attempt_admitted_at:
            errors.append("TERMINAL_CAUSAL_UTC_INVALID")
    if attempts and start is not None and sorted(a.attempt_sequence for a in attempts) != list(range(start.first_attempt_sequence, start.first_attempt_sequence + len(attempts))):
        errors.append("CHILD_SEQUENCE_GAP")
    for url in set(expected):
        if url not in attempt_by_url:
            missing.append(sha256(url.encode()).hexdigest())
        elif len(attempt_by_url[url]) != 1:
            errors.append("REPEATED_PROVIDER_REQUEST:" + sha256(url.encode()).hexdigest())
    # Authority declares a serial entry/event traversal, not merely a URL set.
    # Preserve that order even when one branch causally cannot discover children.
    ordered_population = [plan.current_url]
    if entry_closure is not None:
        for entry_id, _, _, horse_url in entry_closure.entries:
            ordered_population.append(horse_url)
            matching = [h for h in history_closures if h.entry_identity == entry_id]
            if len(matching) == 1:
                ordered_population.extend(matching[0].request_urls)
    admitted_in_order = [a.expected_request_url_sha256 for a in sorted(attempts, key=lambda a: a.attempt_sequence)]
    declared_admitted_order = [sha256(url.encode()).hexdigest() for url in dict.fromkeys(ordered_population) if url in attempt_by_url]
    if admitted_in_order != declared_admitted_order:
        errors.append("CHILD_REQUEST_ORDER_INVALID")
    if entry_closure is not None:
        parent = next((a for a in attempts if a.attempt_identity == entry_closure.parent_attempt_identity), None)
        if parent is None or parent.expected_request_url_sha256 != sha256(plan.current_url.encode()).hexdigest():
            errors.append("ENTRY_PARENT_ATTEMPT_INVALID")
        for _, _, _, url in entry_closure.entries:
            for child in attempt_by_url.get(url, ()):
                if child.attempt_sequence < entry_closure.first_authorized_sequence or child.attempt_admitted_at < entry_closure.closed_at:
                    errors.append("CHILD_BEFORE_ENTRY_CLOSURE")
        for h in history_closures:
            parent = next((a for a in attempts if a.attempt_identity == h.parent_attempt_identity), None)
            horse_url = next((x[3] for x in entry_closure.entries if x[0] == h.entry_identity), None)
            if parent is None or horse_url is None or parent.expected_request_url_sha256 != sha256(horse_url.encode()).hexdigest():
                errors.append("HISTORY_PARENT_ATTEMPT_INVALID")
    # Request nodes own first admission; all later closures own distinct durable
    # dependencies. A later closure never retroactively authorizes the first IO.
    expected_nodes, expected_edges = {}, []
    if start is not None:
        expected_nodes[plan.current_url] = start.first_attempt_sequence
        if entry_closure is not None:
            expected_nodes.update((x[3], entry_closure.first_authorized_sequence) for x in entry_closure.entries)
        for h in history_closures:
            for url in h.request_urls:
                expected_nodes[url] = min(expected_nodes.get(url, h.first_authorized_sequence), h.first_authorized_sequence)
                expected_edges.append((h.identity, start.identity, sha256(url.encode()).hexdigest()))
    exact_nodes = tuple(sorted((start.identity, sha256(url.encode()).hexdigest(), url, seq)
        for url, seq in expected_nodes.items())) if start else ()
    if tuple(sorted(request_nodes)) != exact_nodes or tuple(sorted(dependency_edges)) != tuple(sorted(expected_edges)):
        errors.append("CHILD_REQUEST_GRAPH_INVALID")
    for url, first_sequence in expected_nodes.items():
        if url == plan.current_url or not history_closures:
            continue
        first_closures = [h for h in history_closures if url in h.request_urls and h.first_authorized_sequence == first_sequence]
        for child in attempt_by_url.get(url, ()):
            if first_closures and not any(child.attempt_sequence >= h.first_authorized_sequence and child.attempt_admitted_at >= h.closed_at for h in first_closures):
                errors.append("CHILD_BEFORE_PAST_RACE_CLOSURE")
    unsatisfied_edges = []
    for edge in dependency_edges:
        candidates = [a for a in attempts if a.expected_request_url_sha256 == edge[2]]
        capture_matches = [c for c in captures if sha256(c.canonical_source_url.encode()).hexdigest() == edge[2]]
        if (len(candidates) != 1 or len(capture_matches) != 1
                or not any(o[0] == candidates[0].attempt_identity and o[1:3] == ("QUALIFIED_OPERATIONAL_TIMING_OBSERVATION", "SUCCESS") for o in observations)):
            unsatisfied_edges.append(edge)
    proof = None
    if records:
        try:
            proof = prerequisite_proof(root=root, manifest=manifest, current_records=records, history_records=history_records,
                entries_closure=entry_closure, histories=tuple(history_closures))
        except Exception:
            errors.append("SNAPSHOT_PREREQUISITE_COVERAGE_INCOMPLETE")
    semantic_ok = (snapshot is not None and receipt is not None and receipt.snapshot_identity == snapshot.identity
        and receipt.snapshot_content_sha256 == snapshot.content_sha256
        and compute_historical_input_snapshot_content_sha256(snapshot=snapshot) == snapshot.content_sha256
        and snapshot.identity.source_identity.external_race_id == root.scope.external_race_id
        and snapshot.identity.dataset_id == root.scope.dataset_id and snapshot.internal_race_id == root.scope.internal_race_id
        and snapshot.information_cutoff == root.scope.prediction_information_cutoff)
    if completion is not None:
        if (start is None or completion.start_identity != start.identity or completion.clock_domain != start.clock_domain
                or completion.process_id != start.process_id or completion.monotonic_endpoint_ns < start.monotonic_start_ns
                or completion.elapsed_microseconds != elapsed_microseconds_from_ns(start.monotonic_start_ns, completion.monotonic_endpoint_ns)
                or not semantic_ok or completion.freeze_receipt_identity != receipt.receipt_identity
            or completion.snapshot_content_sha256 != snapshot.content_sha256 or completion.freeze_completed_at != receipt.freeze_completed_at):
            errors.append("COMPLETION_ANCESTRY_OR_CLOCK_INVALID")
        try:
            expected_proof = tuple(sorted(proof + (("captured-at", "GENERATED_INSIDE_ROOT_UNDER_EXECUTION_PLAN", sha256(_time(snapshot.identity.captured_at).encode()).hexdigest()),)))
            if completion.prerequisite_proof != expected_proof:
                raise ValueError("proof differs")
            if completion.snapshot_identity_json != snapshot_identity_bytes(snapshot).decode():
                raise ValueError("snapshot identity differs")
            rebuilt = build_historical_input_snapshot(dataset_id=root.scope.dataset_id, internal_race_id=root.scope.internal_race_id,
                information_cutoff=root.scope.prediction_information_cutoff, captured_at=snapshot.identity.captured_at,
                source_records=records + history_records, race_entry_id_by_external_entry_id=dict(manifest.entry_mapping))
            if rebuilt.content_sha256 != snapshot.content_sha256:
                raise ValueError("snapshot source content differs")
            if len(completion.children) != len(attempts) or {x[1] for x in completion.children} != {a.attempt_identity for a in attempts}:
                raise ValueError("child set differs")
            for url, attempt_id, capture_id in completion.children:
                c = capture_by_id[capture_id]
                if c.canonical_source_url != url or not any(a.attempt_identity == attempt_id for a in attempt_by_url[url]):
                    raise ValueError("capture/attempt relation differs")
        except Exception:
            errors.append("COMPLETION_PREREQUISITE_OR_CHILD_PROOF_INVALID")
    qualified_failure = any(x[1] == "QUALIFIED_OPERATIONAL_TIMING_OBSERVATION" and x[2] in ("FAILURE", "TIMEOUT") for x in observations)
    env_rejected = any(x[1] == "NONQUALIFYING_REQUEST_ENVIRONMENT" for x in observations)
    severe = any(x.startswith(("EXECUTION_", "START_", "CHILD_", "UNRESOLVED_", "COMPLETION_", "ENVIRONMENT_", "DUPLICATE_")) for x in errors)
    if severe or extras:
        state = NARPreCEnvelopeReconciliationState.INTEGRITY
    elif start is not None and (not session.admits(start.started_at) or semantic_ok and receipt.freeze_completed_at >= session.measurement_end_at):
        state = NARPreCEnvelopeReconciliationState.SESSION
    elif semantic_ok and receipt.freeze_completed_at > root.scope.prediction_information_cutoff:
        state = NARPreCEnvelopeReconciliationState.CUTOFF
    elif qualified_failure:
        state = NARPreCEnvelopeReconciliationState.PROVIDER
    elif env_rejected:
        state = NARPreCEnvelopeReconciliationState.EXECUTION
    elif errors or missing or unsatisfied_edges:
        state = NARPreCEnvelopeReconciliationState.DISCOVERY if plan.history_mode is Mode.GENERATED else NARPreCEnvelopeReconciliationState.EXECUTION
    elif not semantic_ok:
        state = NARPreCEnvelopeReconciliationState.FREEZE
    elif completion is None:
        state = NARPreCEnvelopeReconciliationState.TELEMETRY
    elif overhead_defects:
        state = NARPreCEnvelopeReconciliationState.INTEGRITY
    else:
        state = NARPreCEnvelopeReconciliationState.COMPLETE
    return NARPreCEnvelopeReconciliationV1(root.identity, root.scope.identity, manifest.identity, plan.identity,
        start.identity if start else None, completion.identity if completion else None, state.value,
        completion.elapsed_microseconds if completion else None, tuple(observations), tuple(sorted(set(errors))),
        tuple(sorted(missing)), tuple(sorted(extras)), tuple(sorted(overhead_defects)), receipt.receipt_identity if semantic_ok else None,
        root.claim_identity, root.session_identity, entry_closure.identity if entry_closure else None,
        tuple(sorted(h.identity for h in history_closures)), completion.prerequisite_proof if completion else tuple(proof or ()),
        "EXACT_SNAPSHOT_FREEZE_RECEIPT_VERIFIED" if semantic_ok else "MISSING_OR_UNVERIFIED_FREEZE_EVIDENCE",
        "VERIFIED_SAME_PROCESS_ENDPOINT" if completion and not any(x.startswith("COMPLETION_") for x in errors) else "INCOMPLETE_DURABLE_TIMING_ENDPOINT",
        tuple(sorted(request_nodes)), tuple(sorted(dependency_edges)), tuple(sorted(unsatisfied_edges)))


def reconcile_pre_c_archive(*, context, capture_archive, snapshot_repository, prestaged_history=()):
    """Read immutable rows; the current root context is only a selector, not proof."""
    archive, root = context.archive, context.root
    manifest = archive.load(kind=Manifest, identity=root.manifest_identity)
    plan = archive.load(kind=Plan, identity=root.execution_plan_identity)
    starts = tuple(s for s in archive.all(kind=Start) if s.root_identity == root.identity)
    start = starts[0] if len(starts) == 1 else None
    entries = tuple(e for e in archive.all(kind=Entries) if start and e.start_identity == start.identity)
    entry = entries[0] if len(entries) == 1 else None
    histories = tuple(h for h in archive.all(kind=History) if entry and h.entry_closure_identity == entry.identity)
    completions = tuple(c for c in archive.all(kind=Completion) if start and c.start_identity == start.identity)
    completion = completions[0] if len(completions) == 1 else None
    rows = archive._connection.execute("SELECT identity FROM nar_operational_timing_v2_attempts WHERE claim_identity=? ORDER BY attempt_sequence", (root.claim_identity,)).fetchall()
    all_attempts = tuple(archive.attempts.load_attempt(attempt_identity=r[0]) for r in rows)
    # Each target root has an exact correlation. Other targets are never merged.
    attempts = tuple(a for a in all_attempts if a.correlation.external_race_id == root.scope.external_race_id and a.correlation.cutoff_plan_sha256 == root.scope.cutoff_plan_sha256)
    terminals = tuple(t for a in attempts if (t := archive.attempts.load_terminal_for_attempt(attempt_identity=a.attempt_identity)) is not None)
    environments = tuple(e for a in attempts if (e := archive.attempts.load_environment_for_attempt(attempt_identity=a.attempt_identity)) is not None)
    overhead = tuple(o for a in attempts for o in archive.attempts.load_overhead_for_attempt(attempt_identity=a.attempt_identity))
    # Derive evidence exclusively from immutable repositories; in-memory execution
    # outcomes/children are deliberately not reconciliation authority.
    capture_rows = capture_archive._connection.execute("SELECT capture_id FROM nar_official_response_captures ORDER BY capture_id").fetchall()
    all_captures = tuple(capture_archive.load_capture(capture_id=r[0]) for r in capture_rows)
    authorized_digests = {a.expected_request_url_sha256 for a in attempts}
    captures = tuple(c for c in all_captures if start and c.requested_at >= start.started_at and sha256(c.canonical_source_url.encode()).hexdigest() in authorized_digests)
    freeze_archive = SQLiteNAROperationalTimingObservabilityArchive(connection=archive._connection)
    receipt_rows = archive._connection.execute(f"SELECT identity FROM {timing_base_schema.RECEIPTS} ORDER BY identity").fetchall()
    all_receipts = tuple(freeze_archive.load_freeze_receipt(receipt_identity=r[0]) for r in receipt_rows)
    root_receipts = tuple(r for r in all_receipts if start and r.freeze_completed_at >= start.started_at
        and r.snapshot_identity.source_identity.external_race_id == root.scope.external_race_id
        and r.snapshot_information_cutoff == root.scope.prediction_information_cutoff
        and r.internal_race_id == root.scope.internal_race_id and r.snapshot_identity.dataset_id == root.scope.dataset_id)
    receipt = root_receipts[0] if len(root_receipts) == 1 else None
    snapshot = snapshot_repository.load_snapshot_by_identity(identity=receipt.snapshot_identity) if receipt else None
    session = archive.attempts.runtime.v2.load_session(session_identity=root.session_identity)
    claim = archive.attempts.runtime.load_claim_for_session(session_identity=root.session_identity)
    readiness = archive.attempts.runtime.load_readiness_for_claim(claim_identity=root.claim_identity)
    nodes, edges = archive.request_graph(start_identity=start.identity) if start else ((), ())
    return reconcile_pre_c_evidence(root=root, manifest=manifest, plan=plan, start=start, completion=completion,
        entry_closure=entry, history_closures=histories, attempts=attempts, terminals=terminals, environments=environments,
        overhead=overhead, captures=captures, prestaged_history=prestaged_history, snapshot=snapshot, receipt=receipt,
        session=session, claim=claim, readiness=readiness, request_nodes=nodes, dependency_edges=edges)
