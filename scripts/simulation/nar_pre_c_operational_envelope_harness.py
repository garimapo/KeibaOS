"""Controlled target-root no-network composition using existing production functions.

Worktree tests exercise mechanics only. Real source isolation is checked by the
Phase104 runner in the separately approved final-commit sealed child.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import ast
import os
import sqlite3
from datetime import timedelta, timezone
from pathlib import Path

from scripts.simulation.nar_pre_c_operational_envelope import (
    NARPreCPrestagedInputManifestV1 as Manifest, NARPreCOperationalEnvelopeExecutionPlanV1 as Plan,
    NARPreCOperationalEnvelopeV1 as Root, NARPreCEnvelopeStartEvidenceV1 as Start,
    NARCurrentEntryDiscoveryClosureV1 as Entries, NARPastRaceDiscoveryClosureV1 as History,
    NARPreCEnvelopeCompletionEvidenceV1 as Completion, NARPreCHistoryMode as Mode,
    NARPreCEnvelopeError, source_record_sha, elapsed_microseconds_from_ns, snapshot_identity_bytes,
)
from scripts.simulation.nar_pre_c_operational_envelope_archive_bootstrap import bootstrap_nar_pre_c_operational_envelope_archive
from scripts.simulation.sqlite_nar_pre_c_operational_envelope_archive import SQLiteNARPreCOperationalEnvelopeArchive, _ENVELOPE_ISSUANCE_MARKER
from scripts.simulation.nar_operational_timing_diagnostic_campaign import NAROperationalTimingDiagnosticFixtureBundleV1 as Fixture
from scripts.simulation.nar_operational_timing_diagnostic_harness import NARDiagnosticFakeHTTPAdapter
from scripts.simulation.nar_operational_timing_guarded_session import guarded_session_factory
from scripts.simulation.nar_operational_timing_passive_wrapper import measure_nar_operation
from scripts.simulation.nar_operational_timing_observability import (
    NARHTTPTransportKind, NARTimingCorrelation, NARTimingCorrelationScope, NARTimingLoadContext, _utc, _time, _json_bytes,
)
from scripts.simulation.nar_operational_timing_observability_v2 import NAROperationalTimingStageV2 as Stage
from scripts.simulation.nar_official_response_capture import canonicalize_nar_official_capture_url, NAROfficialPageKind
from scripts.simulation.nar_official_response_live_capture import NAROfficialLiveResponseCaptureService, _RequestsNAROfficialHTTPTransport
from scripts.simulation.nar_historical_input_source import NarSuppliedOfficialResponse, normalize_nar_historical_input_source_records
from scripts.simulation.nar_historical_past_race_discovery import discover_nar_historical_past_race_history, NARHistoricalEventKind
from scripts.simulation.nar_historical_past_race_source import normalize_nar_historical_past_race_source_record
from scripts.simulation.nar_historical_past_race_absence_source import normalize_nar_historical_past_race_absence_source_record
from scripts.simulation.historical_input_snapshot_builder import build_historical_input_snapshot
from scripts.simulation.historical_input_snapshot_freeze_receipt import issue_historical_input_snapshot_freeze_receipt
from scripts.simulation.sqlite_nar_operational_timing_observability_archive import SQLiteNAROperationalTimingObservabilityArchive

_ROOT_CONTEXT_MARKER = object()
FIXTURE_PATHS = (
    "tests/fixtures/nar/deba_table_target_horse_identity.html",
    "tests/fixtures/nar/horse_mark_info_past_race_context.html",
    "tests/fixtures/nar/horse_mark_info_zero_history.html",
    "tests/fixtures/nar/race_mark_table_past_race_result.html",
    "tests/test_nar_historical_input_source.py",
)


def rehearsal_fixture_responses(*, fixture: Fixture, repository_root, current_url):
    """Synthetic lineage pairing from exact Git fixtures, never provider evidence.

    The fixed substitution aligns the committed current fixture with the committed
    history/result pair. It changes only diagnostic bytes; normalizers are unchanged.
    Mapping 101/102 already appears as an explicit fixture mapping in the reviewed
    test source, not generated from horse number, enumeration, or hash.
    """
    if type(fixture) is not Fixture or tuple(m.path for m in fixture.members) != tuple(sorted(FIXTURE_PATHS)):
        raise NARPreCEnvelopeError("exact Phase108 Git fixture bundle required")
    bodies = fixture.read_verified_bytes(repository_root=repository_root)
    current = bodies[FIXTURE_PATHS[0]].replace(b"30036406666", b"30074407776").replace(b"30038401876", b"30055402717")
    return (
        (current_url, current),
        ("https://www.keiba.go.jp/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=30074407776", bodies[FIXTURE_PATHS[1]]),
        ("https://www.keiba.go.jp/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=30055402717", bodies[FIXTURE_PATHS[2]]),
        ("https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceMarkTable?k_babaCode=31&k_raceDate=2026%2F05%2F03&k_raceNo=1", bodies[FIXTURE_PATHS[3]]),
    )


def entry_population(records):
    entries = sorted((r for r in records if r.record_kind == "entry"), key=lambda r: r.record_values["horse_no"])
    return tuple((r.external_entry_id, r.record_values["horse_no"], r.record_values["external_horse_id"],
                  "https://www.keiba.go.jp/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=" + r.record_values["external_horse_id"].rsplit(":", 1)[1]) for r in entries)


def history_events(discovery):
    return tuple((e.event_kind.value, e.race_date.isoformat(), e.provider_event_id,
                  e.canonical_race_result_url if e.event_kind is NARHistoricalEventKind.NAR_ACTUAL_START else None) for e in discovery.events)


def prestaged_rehearsal_history(*, responses, current_url, observed_at):
    """Use canonical discovery/source transforms before dispatch; no provider IO."""
    bodies = dict(responses)
    current = normalize_nar_historical_input_source_records(response=NarSuppliedOfficialResponse(current_url, bodies[current_url], "utf-8", observed_at))
    track = next(r for r in current if r.record_kind == "track")
    result = []
    for entry in (r for r in current if r.record_kind == "entry"):
        url = next(x[3] for x in entry_population(current) if x[0] == entry.external_entry_id)
        horse = NarSuppliedOfficialResponse(url, bodies[url], "utf-8", observed_at)
        discovery = discover_nar_historical_past_race_history(target_track_record=track, target_entry_record=entry, horse_history_response=horse)
        if discovery.proven_zero_history:
            result.append(normalize_nar_historical_past_race_absence_source_record(target_track_record=track, target_entry_record=entry, horse_history_response=horse))
        else:
            for event in discovery.events:
                if event.event_kind is not NARHistoricalEventKind.NAR_ACTUAL_START:
                    raise NARPreCEnvelopeError("fixture history has unsupported source semantics")
                result.append(normalize_nar_historical_past_race_source_record(target_entry_record=entry, horse_history_response=horse,
                    race_result_response=NarSuppliedOfficialResponse(event.canonical_race_result_url, bodies[event.canonical_race_result_url], "utf-8", observed_at)))
    return tuple(result)


def prerequisite_proof(*, root, manifest, current_records, history_records, entries_closure=None, histories=()):
    """Close ALL inputs independently of the snapshot builder's validation."""
    scope = root.scope
    entries = tuple(r for r in current_records if r.record_kind == "entry")
    if not entries or {r.external_entry_id for r in entries} != set(dict(manifest.entry_mapping)):
        raise NARPreCEnvelopeError("stale/incompatible prestaged mapping")
    track = tuple(r for r in current_records if r.record_kind == "track")
    if len(track) != 1 or track[0].external_race_id != scope.external_race_id:
        raise NARPreCEnvelopeError("missing exact track prerequisite")
    for entry in entries:
        for kind in ("entry", "jockey", "odds_win"):
            if sum(r.record_kind == kind and r.external_entry_id == entry.external_entry_id for r in current_records) != 1:
                raise NARPreCEnvelopeError("missing current snapshot prerequisite")
    if any(r.external_race_id != scope.external_race_id for r in current_records + history_records):
        raise NARPreCEnvelopeError("snapshot source target mismatch")
    actual = tuple(sorted((r.external_entry_id, r.record_kind, r.source_id, source_record_sha(r)) for r in history_records))
    if manifest.history_records:
        if actual != manifest.history_records:
            raise NARPreCEnvelopeError("prestaged history authority differs")
    else:
        if entries_closure is None or entries_closure.entries != entry_population(current_records):
            raise NARPreCEnvelopeError("current-entry work population not closed")
        if {h.entry_identity for h in histories} != {r.external_entry_id for r in entries}:
            raise NARPreCEnvelopeError("missing history discovery closure")
        for h in histories:
            records = tuple(r for r in history_records if r.external_entry_id == h.entry_identity)
            if h.proven_zero_history:
                if len(records) != 1 or records[0].record_kind != "past_race_absence":
                    raise NARPreCEnvelopeError("missing proven absence prerequisite")
            elif (len(records) != len(h.request_urls) or any(r.record_kind != "past_race" for r in records)
                    or {r.evidence[1].canonical_source_url for r in records} != set(h.request_urls)
                    or any(e[0] != "nar_actual_start" for e in h.events)):
                raise NARPreCEnvelopeError("required history population incomplete/unsupported")
    if {r.external_entry_id for r in history_records} != {r.external_entry_id for r in entries}:
        raise NARPreCEnvelopeError("missing history snapshot prerequisite")
    pre, generated = "PRESTAGED_AND_AUTHORITY_CLOSED_BEFORE_ROOT", "GENERATED_INSIDE_ROOT_UNDER_EXECUTION_PLAN"
    proof = [("dataset/internal-race/cutoff", pre, sha256(scope.canonical_bytes()).hexdigest()),
             ("entry-mapping", pre, sha256(_json_bytes(manifest.entry_mapping)).hexdigest())]
    proof += [(r.source_id, generated, source_record_sha(r)) for r in current_records]
    proof += [(r.source_id, pre if manifest.history_records else generated, source_record_sha(r)) for r in history_records]
    return tuple(sorted(proof))


class NARPreCCurrentProcessRootContext:
    """Nonserializable current-process root authority, never recreated from saved ticks."""
    def __init__(self, *, runner, capability, archive, root, manifest, plan, _marker=None):
        if _marker is not _ROOT_CONTEXT_MARKER:
            raise NARPreCEnvelopeError("root context requires controlled fresh issuance")
        self.runner, self.capability, self.archive = runner, capability, archive
        self.root, self.manifest, self.plan = root, manifest, plan
        self._pid, self._timer = os.getpid(), runner.monotonic_timer_ns
        self.start = None
        self.endpoint = None
        self.endpoint_error = False
        self.completion = None
        self._closed = False
        self.children = []
        self._requested_urls = set()
        self.failures = []
        self.entries = None
        self.histories = []
        self.adapter_calls = []
        self.snapshot = None
        self.receipt = None
        self.proof = None

    def require_live(self):
        self.capability.require_current_owner(self.runner)
        if (os.getpid() != self._pid or self.runner.monotonic_timer_ns is not self._timer or self._closed
                or self.capability.claim_identity != self.root.claim_identity
                or self.capability.session_identity != self.root.session_identity):
            raise NARPreCEnvelopeError("root cannot resume across process/clock/capability boundary")

    def require_started(self):
        self.require_live()
        if self.start is None or self.archive.load(kind=Start, identity=self.start.identity) != self.start:
            raise NARPreCEnvelopeError("durable exact-reloaded root start required before causal work")
        if self.endpoint is not None or self.endpoint_error:
            raise NARPreCEnvelopeError("causal work cannot begin after freeze endpoint")

    def publish(self, value):
        self.archive.publish(value=value, runner=self.runner, capability=self.capability,
            _issuance_marker=_ENVELOPE_ISSUANCE_MARKER, _root_context=self)

    def authorize_request(self, url):
        self.require_started()
        kind, canonical = canonicalize_nar_official_capture_url(url)
        if canonical != url or kind not in self.plan.allowed_request_families:
            raise NARPreCEnvelopeError("request outside predeclared target work families")
        if kind is NAROfficialPageKind.DEBA_TABLE:
            allowed = url == self.plan.current_url
        elif kind is NAROfficialPageKind.HORSE_MARK_INFO:
            allowed = (self.entries is not None and self.archive.load(kind=Entries, identity=self.entries.identity) == self.entries
                       and url in {x[3] for x in self.entries.entries})
        else:
            allowed = any(url in h.request_urls and self.archive.load(kind=History, identity=h.identity) == h for h in self.histories)
        if not allowed:
            raise NARPreCEnvelopeError("derived request requires exact reloaded discovery closure")
        if url in self._requested_urls:
            raise NARPreCEnvelopeError("no retry/redundant target request permitted")

    def capture(self, *, url, bodies, capture_archive, failure=None):
        self.authorize_request(url)
        if url not in bodies:
            raise NARPreCEnvelopeError("authorized diagnostic fixture body missing")
        self._requested_urls.add(url)
        adapter = NARDiagnosticFakeHTTPAdapter(body=bodies[url], failure=failure, content_type="text/html; charset=utf-8")
        session_factory = guarded_session_factory(runner=self.runner, capability=self.capability, transport_kind=NARHTTPTransportKind.NAR_OFFICIAL_RESPONSE_HTTP)
        transport = _RequestsNAROfficialHTTPTransport(_session_factory=session_factory, _diagnostic_adapter_factory=lambda: adapter)
        # Measure the actual transport below capture clock/check/save semantics. The
        # enclosing root also covers all capture checks and archive save/reload.
        context = self
        class TimedTransport:
            def fetch(self, *, canonical_source_url):
                return measure_nar_operation(runner=context.runner, capability=context.capability,
                    stage=Stage.OFFICIAL_RESPONSE_ACQUISITION, correlation=context.correlation,
                    load_context=NARTimingLoadContext(1, 1, False), expected_url=canonical_source_url,
                    transport_kind=NARHTTPTransportKind.NAR_OFFICIAL_RESPONSE_HTTP,
                    operation=lambda: transport.fetch(canonical_source_url=canonical_source_url))
        sequence = self.runner._next_attempt_sequence
        try:
            capture = NAROfficialLiveResponseCaptureService(archive=capture_archive, transport=TimedTransport(), utc_clock=self.runner.utc_clock).capture_response(response_url=url)
            if capture_archive.load_capture(capture_id=capture.capture_id) != capture:
                raise NARPreCEnvelopeError("capture did not exact-reload")
            attempt = self._attempt(sequence)
            self.children.append((url, attempt.attempt_identity, capture.capture_id))
            return capture
        finally:
            self.adapter_calls.append((url, adapter.send_count))
            transport._session.close()

    def capture_history_request(self, *, closure, url, bodies, capture_archive, failure=None):
        """Consume a closure dependency, acquiring its unique request at most once."""
        self.require_started()
        if (type(closure) is not History or closure not in self.histories or url not in closure.request_urls
                or self.archive.load(kind=History, identity=closure.identity) != closure):
            raise NARPreCEnvelopeError("shared capture requires this exact reloaded history closure")
        nodes, edges = self.archive.request_graph(start_identity=self.start.identity)
        url_sha = sha256(url.encode()).hexdigest()
        if ((closure.identity, self.start.identity, url_sha) not in edges
                or not any(n[:3] == (self.start.identity, url_sha, url) for n in nodes)):
            raise NARPreCEnvelopeError("exact durable closure/request dependency required")
        if url not in self._requested_urls:
            return self.capture(url=url, bodies=bodies, capture_archive=capture_archive, failure=failure)
        matches = [child for child in self.children if child[0] == url]
        if len(matches) != 1:
            # A failed request has no capture. Never retry or erase its observation.
            raise NARPreCEnvelopeError("shared request has no successful exact capture; no retry")
        _, attempt_id, capture_id = matches[0]
        attempt = self.archive.attempts.load_attempt(attempt_identity=attempt_id)
        terminal = self.archive.attempts.load_terminal_for_attempt(attempt_identity=attempt_id)
        environment = self.archive.attempts.load_environment_for_attempt(attempt_identity=attempt_id)
        capture = capture_archive.load_capture(capture_id=capture_id)
        if (attempt is None or attempt.campaign_execution_identity != self.root.claim_identity
                or attempt.expected_request_url_sha256 != url_sha or terminal is None or terminal.disposition.value != "SUCCESS"
                or environment is None or environment.qualification.value != "QUALIFIED_DIRECT_REQUEST_ENVIRONMENT"
                or capture is None or capture.canonical_source_url != url):
            raise NARPreCEnvelopeError("shared reuse requires exact prior qualified successful capture")
        return capture

    @property
    def correlation(self):
        import json
        p = json.loads(self.root.scope.cutoff_plan_json)
        return NARTimingCorrelation(NARTimingCorrelationScope.RACE, self.root.scope.external_race_id,
            self.root.scope.target_set_sha256, self.root.scope.cutoff_plan_sha256, p["cutoff_policy_identity"])

    def _attempt(self, sequence):
        row = self.runner._connection.execute("SELECT identity FROM nar_operational_timing_v2_attempts WHERE claim_identity=? AND attempt_sequence=?",
            (self.capability.claim_identity, sequence)).fetchone()
        if row is None:
            raise NARPreCEnvelopeError("child attempt publication missing")
        return self.runner.attempt_archive.load_attempt(attempt_identity=row[0])

    def close_entries(self, *, capture, records, attempt):
        self.require_started()
        expected = normalize_nar_historical_input_source_records(response=capture.to_supplied_official_response())
        if tuple(records) != expected or capture.canonical_source_url != self.plan.current_url:
            raise NARPreCEnvelopeError("entry closure must bind complete canonical normalization")
        value = Entries(self.start.identity, capture.capture_id, attempt.attempt_identity,
            tuple(sorted((r.source_id, source_record_sha(r)) for r in records)), entry_population(records),
            self.runner._next_attempt_sequence, _utc(self.runner.utc_clock()))
        self.publish(value)
        self.entries = self.archive.load(kind=Entries, identity=value.identity)
        return self.entries

    def close_history(self, *, capture, track, entry, discovery, attempt):
        self.require_started()
        if self.entries is None:
            raise NARPreCEnvelopeError("entry closure missing")
        exact = discover_nar_historical_past_race_history(target_track_record=track, target_entry_record=entry, horse_history_response=capture.to_supplied_official_response())
        if exact != discovery:
            raise NARPreCEnvelopeError("partial/noncanonical history closure")
        value = History(self.entries.identity, capture.capture_id, attempt.attempt_identity,
            discovery.target_external_entry_id, discovery.target_external_horse_id, history_events(discovery), discovery.proven_zero_history,
            self.runner._next_attempt_sequence, _utc(self.runner.utc_clock()))
        self.publish(value)
        self.histories.append(self.archive.load(kind=History, identity=value.identity))
        return value

    def observe_freeze_endpoint(self, completed):
        # Capture errors locally AND let the ordinary freeze service continue.
        try:
            self.require_live()
            tick = self.runner.monotonic_timer_ns()
            elapsed_microseconds_from_ns(self.start.monotonic_start_ns, tick)
            if self.endpoint is not None or self.endpoint_error:
                raise NARPreCEnvelopeError("endpoint cannot be sampled twice/reconstructed")
            self.endpoint = (_utc(completed), tick)
        except Exception:
            self.endpoint_error = True
            raise

    def run_rehearsal(self, *, capture_archive, snapshot_repository, prestaged_history=(), failures=None):
        self.require_started()
        fixture = Fixture.from_json(self.manifest.fixture_bundle_json)
        bodies = dict(rehearsal_fixture_responses(fixture=fixture, repository_root=self.runner.repository_root, current_url=self.plan.current_url))
        failures = failures or {}
        try:
            current = self.capture(url=self.plan.current_url, bodies=bodies, capture_archive=capture_archive, failure=failures.get(self.plan.current_url))
            records = normalize_nar_historical_input_source_records(response=current.to_supplied_official_response())
            if {r.external_entry_id for r in records if r.record_kind == "entry"} != set(dict(self.manifest.entry_mapping)):
                raise NARPreCEnvelopeError("stale/incompatible prestaged mapping")
            track = next(r for r in records if r.record_kind == "track")
            history_records = list(prestaged_history)
            if self.plan.history_mode is Mode.GENERATED:
                if history_records:
                    raise NARPreCEnvelopeError("unplanned prestaged history")
                entry_closure = self.close_entries(capture=current, records=records, attempt=self._attempt(self.start.first_attempt_sequence))
                for entry_id, _, _, horse_url in entry_closure.entries:
                    entry = next(r for r in records if r.record_kind == "entry" and r.external_entry_id == entry_id)
                    try:
                        horse_sequence = self.runner._next_attempt_sequence
                        horse = self.capture(url=horse_url, bodies=bodies, capture_archive=capture_archive, failure=failures.get(horse_url))
                        discovery = discover_nar_historical_past_race_history(target_track_record=track, target_entry_record=entry, horse_history_response=horse.to_supplied_official_response())
                        closure = self.close_history(capture=horse, track=track, entry=entry, discovery=discovery, attempt=self._attempt(horse_sequence))
                        if closure.proven_zero_history:
                            history_records.append(normalize_nar_historical_past_race_absence_source_record(target_track_record=track, target_entry_record=entry, horse_history_response=horse.to_supplied_official_response()))
                        else:
                            for event in closure.events:
                                if event[0] != "nar_actual_start":
                                    self.failures.append("UNSUPPORTED_HISTORY_SOURCE")
                                    continue
                                try:
                                    race = self.capture_history_request(closure=closure, url=event[3], bodies=bodies, capture_archive=capture_archive, failure=failures.get(event[3]))
                                    history_records.append(normalize_nar_historical_past_race_source_record(target_entry_record=entry,
                                        horse_history_response=horse.to_supplied_official_response(), race_result_response=race.to_supplied_official_response()))
                                except Exception as error:
                                    self.failures.append(type(error).__name__)
                    except Exception as error:
                        self.failures.append(type(error).__name__)
            if self.failures:
                return None
            history_records = tuple(history_records)
            self.proof = prerequisite_proof(root=self.root, manifest=self.manifest, current_records=records,
                history_records=history_records, entries_closure=self.entries, histories=tuple(self.histories))
            captured_at = _utc(self.runner.utc_clock())
            self.proof = tuple(sorted(self.proof + (("captured-at", "GENERATED_INSIDE_ROOT_UNDER_EXECUTION_PLAN", sha256(_time(captured_at).encode()).hexdigest()),)))
            self.require_started()
            self.snapshot = build_historical_input_snapshot(dataset_id=self.root.scope.dataset_id, internal_race_id=self.root.scope.internal_race_id,
                information_cutoff=self.root.scope.prediction_information_cutoff, captured_at=captured_at,
                source_records=records + history_records, race_entry_id_by_external_entry_id=dict(self.manifest.entry_mapping))
            self.receipt = issue_historical_input_snapshot_freeze_receipt(snapshot=self.snapshot, snapshot_repository=snapshot_repository,
                archive=SQLiteNAROperationalTimingObservabilityArchive(connection=self.runner._connection), utc_clock=self.runner.utc_clock,
                _freeze_endpoint_observer=self.observe_freeze_endpoint)
            if self.endpoint is None or self.endpoint_error:
                return self.receipt
            completed, end = self.endpoint
            snapshot_id = snapshot_identity_bytes(self.snapshot).decode()
            value = Completion(self.start.identity, self.start.clock_domain, self._pid, end,
                elapsed_microseconds_from_ns(self.start.monotonic_start_ns, end), self.snapshot.content_sha256,
                snapshot_id, self.receipt.receipt_identity, completed, self.proof, tuple(self.children))
            try:
                self.publish(value)
                self.completion = self.archive.load(kind=Completion, identity=value.identity)
            except Exception:
                self.completion = None  # Semantic freeze survives telemetry publication failure.
            return self.receipt
        except Exception as error:
            self.failures.append(type(error).__name__)
            return None
        finally:
            self._closed = True  # No retry, no endpoint/completion backfill after return.


def issue_target_pre_c_root(*, runner, capability, manifest, plan):
    """All prework checks precede start sample; publication itself is inside root."""
    capability.require_current_owner(runner)
    if type(manifest) is not Manifest or type(plan) is not Plan or plan.manifest_identity != manifest.identity or manifest.claim_identity != capability.claim_identity:
        raise NARPreCEnvelopeError("exact prospective root plan/manifest required")
    fixture = Fixture.from_json(manifest.fixture_bundle_json)
    fixture_bytes = fixture.read_verified_bytes(repository_root=runner.repository_root)
    if fixture.commit_sha != runner.bundle.commit_sha:
        raise NARPreCEnvelopeError("fixture/source ancestry mismatch")
    if manifest.mapping_content_authority != next(m.sha256_hex for m in fixture.members if m.path == FIXTURE_PATHS[4]):
        raise NARPreCEnvelopeError("mapping content authority does not name the reviewed mapping fixture")
    # Use an existing explicit fixture mapping; never synthesize internal IDs.
    reviewed_mappings = []
    for node in ast.walk(ast.parse(fixture_bytes[FIXTURE_PATHS[4]].decode("utf-8"))):
        if isinstance(node, ast.keyword) and node.arg == "race_entry_id_by_external_entry_id" and isinstance(node.value, ast.Dict):
            try:
                reviewed_mappings.append(tuple(sorted(ast.literal_eval(node.value).items())))
            except (ValueError, TypeError):
                pass
    if manifest.entry_mapping not in reviewed_mappings:
        raise NARPreCEnvelopeError("mapping has no exact reviewed prestaged fixture authority")
    if plan.history_mode is Mode.PRESTAGED:
        exact_history = prestaged_rehearsal_history(responses=rehearsal_fixture_responses(fixture=fixture,
            repository_root=runner.repository_root, current_url=plan.current_url), current_url=plan.current_url, observed_at=manifest.available_at)
        if tuple(sorted((r.external_entry_id, r.record_kind, r.source_id, source_record_sha(r)) for r in exact_history)) != manifest.history_records:
            raise NARPreCEnvelopeError("prestaged history was not available under exact Git fixture authority")
    bootstrap_nar_pre_c_operational_envelope_archive(runner=runner, capability=capability)
    archive = SQLiteNARPreCOperationalEnvelopeArchive(connection=runner._connection)
    for value in (manifest, plan):
        archive.publish(value=value, runner=runner, capability=capability, _issuance_marker=_ENVELOPE_ISSUANCE_MARKER)
        if archive.load(kind=type(value), identity=value.identity) != value:
            raise NARPreCEnvelopeError("prestart authority exact reload failed")
    claim = runner.attempt_archive.runtime.load_claim_for_session(session_identity=capability.session_identity)
    root = Root(claim.claim_identity, claim.binding_identity, claim.session_identity, claim.bundle_identity,
        manifest.identity, plan.identity, plan.scope)
    archive.publish(value=root, runner=runner, capability=capability, _issuance_marker=_ENVELOPE_ISSUANCE_MARKER)
    if archive.load(kind=Root, identity=root.identity) != root:
        raise NARPreCEnvelopeError("root exact reload failed")
    context = NARPreCCurrentProcessRootContext(runner=runner, capability=capability, archive=archive,
        root=root, manifest=manifest, plan=plan, _marker=_ROOT_CONTEXT_MARKER)
    context.require_live()
    started_at = _utc(runner.utc_clock())
    session = runner.attempt_archive.runtime.v2.load_session(session_identity=capability.session_identity)
    if not session.admits(started_at) or manifest.available_at > started_at:
        raise NARPreCEnvelopeError("root admission/prestaged availability invalid")
    tick = runner.monotonic_timer_ns()
    domain = sha256((root.identity + ":" + str(context._pid) + ":" + str(tick)).encode()).hexdigest()
    start = Start(root.identity, domain, context._pid, tick, started_at, runner._next_attempt_sequence)
    context.publish(start)
    if archive.load(kind=Start, identity=start.identity) != start:
        raise NARPreCEnvelopeError("start publication failed; causal work prohibited")
    context.start = start
    return context


def prepare_rehearsal_plan(*, runner, capability, history_mode):
    """Diagnostic control plane from exact Git objects, completed before root dispatch."""
    from scripts.simulation.historical_daily_targets import (
        HistoricalDailyProviderIdentity, DailyHistoricalReplayProviderScope,
        DailyHistoricalReplayTarget, DailyHistoricalReplayTargetSet,
        DailyHistoricalReplayCompletenessEvidence, ProviderNativeDispositionEvidenceReference,
    )
    from scripts.simulation.nar_historical_replay_prediction_cutoff import NARHistoricalReplayPredictionCutoffPlan, NARHistoricalReplayPredictionCutoffDecision
    from scripts.simulation.nar_pre_c_operational_envelope import NARPreCTargetScopeV1
    capability.require_current_owner(runner)
    fixture = Fixture.from_git(repository_root=runner.repository_root, repository_identity="garimapo/KeibaOS",
        commit_sha=runner.bundle.commit_sha, paths=FIXTURE_PATHS)
    current_url = "https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/DebaTable?k_babaCode=19&k_raceDate=2026%2F07%2F04&k_raceNo=11"
    responses = rehearsal_fixture_responses(fixture=fixture, repository_root=runner.repository_root, current_url=current_url)
    available = _utc(runner.utc_clock())  # Prospective campaign-owned prework sample.
    preview = normalize_nar_historical_input_source_records(response=NarSuppliedOfficialResponse(current_url, dict(responses)[current_url], "utf-8", available))
    track = next(r for r in preview if r.record_kind == "track")
    provider = HistoricalDailyProviderIdentity("NAR", "nar_official")
    content = sha256(dict(responses)[current_url]).hexdigest()
    target = DailyHistoricalReplayTarget(provider, track.external_race_id, track.record_values["scheduled_start_at"],
        ProviderNativeDispositionEvidenceReference("phase108-synthetic-target-v1", fixture.bundle_identity, content, "reviewed-current-track", content))
    targets = DailyHistoricalReplayTargetSet(track.record_values["target_race_date"], DailyHistoricalReplayProviderScope((provider,)), (target,),
        (DailyHistoricalReplayCompletenessEvidence(provider, "phase108-synthetic-control-plane-v1", fixture.bundle_identity,
            current_url, content, available, None, "one-reviewed-fixture-target"),))
    cutoff = datetime(2026, 7, 4, 11, tzinfo=timezone.utc)
    cutoff_plan = NARHistoricalReplayPredictionCutoffPlan(targets, "nar-prediction-cutoff-policy-v1:" + sha256(b"phase108-diagnostic-policy-no-concrete-delta").hexdigest(),
        (NARHistoricalReplayPredictionCutoffDecision(target, cutoff),))
    scope = NARPreCTargetScopeV1(target.external_race_id, targets.content_sha256, cutoff_plan.plan_sha256,
        cutoff_plan.canonical_bytes().decode(), cutoff, "fixture-dataset", 1)
    historical = prestaged_rehearsal_history(responses=responses, current_url=current_url, observed_at=available) if history_mode is Mode.PRESTAGED else ()
    mapping = ((target.external_race_id + ":entry:1", 101), (target.external_race_id + ":entry:2", 102))
    authority = next(m.sha256_hex for m in fixture.members if m.path == FIXTURE_PATHS[4])
    manifest = Manifest(capability.claim_identity, scope, fixture.canonical_bytes().decode(), available, mapping, authority,
        tuple(sorted((r.external_entry_id, r.record_kind, r.source_id, source_record_sha(r)) for r in historical)))
    plan = Plan(manifest.identity, scope, history_mode, current_url)
    return manifest, plan, historical


def run_phase108_no_network_rehearsal(*, repository_root, bundle_root, commit_sha, temporary_root, history_mode):
    """Both precommit mechanics and later sealed-source callers use this composition.

    No bypass flag exists. The normal Phase104 issuer enforces real source isolation.
    Precommit tests explicitly isolate that source-only dependency in their test setup;
    final sealed children must run it unmodified against the exact approved commit.
    """
    from scripts.simulation.nar_operational_timing_campaign_runner import NAROperationalTimingCampaignRunner
    from scripts.simulation.nar_operational_timing_runtime_source_provenance import _git_manifest
    from scripts.simulation.nar_operational_timing_runtime_profile import derive_static_runtime_transport_profile
    from scripts.simulation.nar_operational_timing_observability import NARHTTPTransportProfile
    from scripts.simulation.nar_operational_timing_observability_v2 import NAROperationalTimingMeasurementConfigurationV2, NAROperationalTimingMeasurementSessionV2
    from scripts.simulation.nar_operational_timing_session_activation_v2 import issue_nar_operational_timing_session_activation_v2
    from scripts.simulation.nar_official_response_capture_migration_runner import apply_capture_schema_migrations
    from scripts.simulation.repositories.sqlite_nar_official_response_capture_repository import SQLiteNAROfficialResponseCaptureRepository
    from scripts.simulation.repositories.sqlite_historical_input_snapshot_repository import SQLiteHistoricalInputSnapshotRepository
    from scripts.migrations.runner import apply_migrations
    from scripts.simulation.nar_pre_c_operational_envelope_reconciliation import reconcile_pre_c_archive
    bundle, _ = _git_manifest(Path(repository_root), commit_sha)
    profile = derive_static_runtime_transport_profile()
    configuration = NAROperationalTimingMeasurementConfigurationV2(commit_sha, (Stage.OFFICIAL_RESPONSE_ACQUISITION,), tuple(
        NARHTTPTransportProfile(x.kind, x.connect_timeout_microseconds, x.read_timeout_microseconds) for x in profile.descriptors))
    session_start = datetime(2026, 7, 4, 10, tzinfo=timezone.utc)
    session = NAROperationalTimingMeasurementSessionV2(configuration, session_start, session_start + timedelta(hours=1))
    samples = iter((session_start - timedelta(seconds=2), session_start - timedelta(seconds=1),
        *(session_start + timedelta(seconds=i) for i in range(240))))
    temp = Path(temporary_root)
    runner = NAROperationalTimingCampaignRunner(archive_path=temp / "timing.sqlite", repository_root=Path(repository_root),
        bundle_root=Path(bundle_root), bundle=bundle, session_identity=session.session_identity,
        utc_clock=lambda: next(samples), enable_attempt_archive=True)
    capture_connection = sqlite3.connect(temp / "captures.sqlite")
    snapshot_connection = sqlite3.connect(temp / "snapshots.sqlite")
    try:
        apply_capture_schema_migrations(capture_connection)
        capture_archive = SQLiteNAROfficialResponseCaptureRepository(connection=capture_connection)
        # Explicit fixture DB identities match the exact predeclared fixture mapping.
        snapshot_connection.execute(
            "CREATE TABLE races(id INTEGER PRIMARY KEY, race_date TEXT, organization TEXT, "
            "place TEXT, race_no INTEGER, deba_table_url TEXT)"
        )
        snapshot_connection.execute(
            "CREATE TABLE horses(id INTEGER PRIMARY KEY, race_id INTEGER NOT NULL, horse_no INTEGER)"
        )
        snapshot_connection.execute(
            "INSERT INTO races VALUES(1, '2026-07-04', 'NAR', '川崎', 11, "
            "'https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/DebaTable?"
            "k_babaCode=19&k_raceDate=2026%2F07%2F04&k_raceNo=11')"
        )
        snapshot_connection.executemany(
            "INSERT INTO horses VALUES(?, 1, ?)", ((101, 1), (102, 2))
        )
        snapshot_connection.commit()
        apply_migrations(snapshot_connection)
        snapshot_repository = SQLiteHistoricalInputSnapshotRepository(connection=snapshot_connection)
        with runner:
            authority = runner.attempt_archive.runtime.v2
            authority.save_configuration(configuration=configuration)
            authority.save_session(session=session)
            issue_nar_operational_timing_session_activation_v2(session=session, archive=authority, utc_clock=lambda: session_start - timedelta(minutes=1))
            capability = runner.issue_current_process_execution()
            manifest, plan, historical = prepare_rehearsal_plan(runner=runner, capability=capability, history_mode=history_mode)
            context = issue_target_pre_c_root(runner=runner, capability=capability, manifest=manifest, plan=plan)
            context.run_rehearsal(capture_archive=capture_archive, snapshot_repository=snapshot_repository, prestaged_history=historical)
            result = reconcile_pre_c_archive(context=context, capture_archive=capture_archive, snapshot_repository=snapshot_repository, prestaged_history=historical)
            return result, tuple(context.adapter_calls)
    finally:
        capture_connection.close()
        snapshot_connection.close()
