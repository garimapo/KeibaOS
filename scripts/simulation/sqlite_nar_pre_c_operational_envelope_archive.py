"""Append-only Phase108 archive with live controlled publication and unrestricted reads."""
from __future__ import annotations
import sqlite3
from hashlib import sha256
from scripts.simulation import nar_pre_c_operational_envelope_archive_migration as schema
from scripts.simulation.nar_pre_c_operational_envelope import (
    NARPreCPrestagedInputManifestV1 as Manifest, NARPreCOperationalEnvelopeExecutionPlanV1 as Plan,
    NARPreCOperationalEnvelopeV1 as Root, NARPreCEnvelopeStartEvidenceV1 as Start,
    NARCurrentEntryDiscoveryClosureV1 as Entries, NARPastRaceDiscoveryClosureV1 as History,
    NARPreCEnvelopeCompletionEvidenceV1 as Completion, NARPreCEnvelopeError,
    elapsed_microseconds_from_ns,
)
from scripts.simulation.sqlite_nar_operational_timing_attempt_archive import SQLiteNAROperationalTimingAttemptArchive

_ENVELOPE_ISSUANCE_MARKER = object()  # Trusted composition discipline, not cryptography.
_TABLES = {Manifest: schema.MANIFESTS, Plan: schema.PLANS, Root: schema.ROOTS, Start: schema.STARTS,
           Entries: schema.ENTRIES, History: schema.HISTORIES, Completion: schema.COMPLETIONS}


class SQLiteNARPreCOperationalEnvelopeArchive:
    def __init__(self, *, connection):
        schema.require_nar_pre_c_operational_envelope_archive_schema(connection)
        self._connection = connection
        self.attempts = SQLiteNAROperationalTimingAttemptArchive(connection=connection)

    def load(self, *, kind, identity):
        schema.require_nar_pre_c_operational_envelope_archive_schema(self._connection)
        if kind not in _TABLES:
            raise NARPreCEnvelopeError("unknown Phase108 authority family")
        row = self._connection.execute(f"SELECT * FROM {_TABLES[kind]} WHERE identity=?", (identity,)).fetchone()
        if row is None:
            return None
        value = kind.from_json(row[-1])
        if value.identity != identity or self._row(value) != tuple(row):
            raise NARPreCEnvelopeError("Phase108 row/canonical content mismatch")
        self._parents(value)
        self._verify_requests(value)
        return value

    def _verify_requests(self, value):
        for expected in self._request_projection(value):
            actual = self._connection.execute(f"SELECT * FROM {schema.REQUESTS} WHERE start_identity=? AND url_sha256=?", expected[:2]).fetchone()
            # A later closure references the first immutable request node; its
            # own admission boundary does not replace that node's first boundary.
            if (actual is None or tuple(actual[:3]) != expected[:3] or actual[3] > expected[3]
                    or type(value) is not History and tuple(actual) != expected):
                raise NARPreCEnvelopeError("stored closure request projection is corrupt")
        if type(value) is History:
            expected_edges = self._dependency_projection(value)
            actual_edges = tuple(self._connection.execute(
                f"SELECT * FROM {schema.DEPENDENCIES} WHERE history_closure_identity=? ORDER BY url_sha256", (value.identity,)).fetchall())
            if actual_edges != tuple(sorted(expected_edges, key=lambda edge: edge[2])):
                raise NARPreCEnvelopeError("stored closure dependency projection is corrupt")

    def all(self, *, kind):
        schema.require_nar_pre_c_operational_envelope_archive_schema(self._connection)
        return tuple(self.load(kind=kind, identity=row[0]) for row in self._connection.execute(
            f"SELECT identity FROM {_TABLES[kind]} ORDER BY identity").fetchall())

    @staticmethod
    def _row(value):
        p = value.canonical_bytes().decode("utf-8")
        if type(value) is Manifest:
            return (value.identity, value.claim_identity, value.scope.identity, p)
        if type(value) is Plan:
            return (value.identity, value.manifest_identity, p)
        if type(value) is Root:
            return (value.identity, value.claim_identity, value.manifest_identity, value.execution_plan_identity, p)
        if type(value) is Start:
            return (value.identity, value.root_identity, value.first_attempt_sequence, p)
        if type(value) is Entries:
            return (value.identity, value.start_identity, value.parent_attempt_identity, p)
        if type(value) is History:
            return (value.identity, value.entry_closure_identity, value.entry_identity, value.parent_attempt_identity, p)
        if type(value) is Completion:
            return (value.identity, value.start_identity, p)
        raise NARPreCEnvelopeError("unsupported Phase108 publication")

    def _required(self, kind, ident):
        value = self.load(kind=kind, identity=ident)
        if value is None:
            raise NARPreCEnvelopeError("missing exact Phase108 parent")
        return value

    def _root_for(self, value):
        if type(value) is Root:
            return value
        if type(value) is Start:
            return self._required(Root, value.root_identity)
        if type(value) in (Entries, Completion):
            return self._root_for(self._required(Start, value.start_identity))
        if type(value) is History:
            return self._root_for(self._required(Entries, value.entry_closure_identity))
        return None

    def _parents(self, value):
        if type(value) is Manifest:
            claim_row = self._connection.execute(f"SELECT session_identity FROM {schema.runtime.CLAIMS} WHERE identity=?", (value.claim_identity,)).fetchone()
            if claim_row is None:
                raise NARPreCEnvelopeError("manifest has no exact execution claim")
            return
        if type(value) is Plan:
            manifest = self._required(Manifest, value.manifest_identity)
            if manifest.scope != value.scope:
                raise NARPreCEnvelopeError("plan scope differs from prestaged authority")
            if (value.history_mode.value == "PRESTAGED_HISTORY") != bool(manifest.history_records):
                raise NARPreCEnvelopeError("plan history mode contradicts manifest")
            return
        root = self._root_for(value)
        manifest = self._required(Manifest, root.manifest_identity)
        plan = self._required(Plan, root.execution_plan_identity)
        claim = self.attempts.runtime.load_claim_for_session(session_identity=root.session_identity)
        if (claim is None or root.claim_identity != claim.claim_identity or root.binding_identity != claim.binding_identity
                or root.runtime_bundle_identity != claim.bundle_identity or manifest.claim_identity != root.claim_identity
                or plan.manifest_identity != manifest.identity or plan.scope != root.scope or manifest.scope != root.scope):
            raise NARPreCEnvelopeError("root has contradictory exact execution ancestry")
        if type(value) is Start:
            session = self.attempts.runtime.v2.load_session(session_identity=root.session_identity)
            if not session.admits(value.started_at) or manifest.available_at > value.started_at:
                raise NARPreCEnvelopeError("start admission/prestaged availability invalid")
        if type(value) in (Entries, History):
            attempt = self.attempts.load_attempt(attempt_identity=value.parent_attempt_identity)
            if (attempt is None or attempt.campaign_execution_identity != root.claim_identity
                    or attempt.correlation.external_race_id != root.scope.external_race_id
                    or attempt.correlation.cutoff_plan_sha256 != root.scope.cutoff_plan_sha256):
                raise NARPreCEnvelopeError("closure parent attempt differs from target root")
            if attempt.attempt_sequence >= value.first_authorized_sequence or value.closed_at < attempt.attempt_admitted_at:
                raise NARPreCEnvelopeError("closure causal sequence/UTC invalid")
            if type(value) is History:
                entry = self._required(Entries, value.entry_closure_identity)
                if not any(x[0] == value.entry_identity and x[2] == value.horse_identity for x in entry.entries):
                    raise NARPreCEnvelopeError("history is outside entry closure")
        if type(value) is Completion:
            start = self._required(Start, value.start_identity)
            if (value.clock_domain != start.clock_domain or value.process_id != start.process_id
                    or value.elapsed_microseconds != elapsed_microseconds_from_ns(start.monotonic_start_ns, value.monotonic_endpoint_ns)
                    or value.freeze_completed_at < start.started_at):
                raise NARPreCEnvelopeError("completion crosses process/clock or causal boundary")

    def _request_projection(self, value):
        if type(value) is Start:
            root = self._required(Root, value.root_identity)
            plan = self._required(Plan, root.execution_plan_identity)
            return ((value.identity, sha256(plan.current_url.encode()).hexdigest(), plan.current_url, value.first_attempt_sequence),)
        if type(value) is Entries:
            return tuple((value.start_identity, sha256(x[3].encode()).hexdigest(), x[3], value.first_authorized_sequence) for x in value.entries)
        if type(value) is History:
            entry = self._required(Entries, value.entry_closure_identity)
            return tuple((entry.start_identity, sha256(url.encode()).hexdigest(), url, value.first_authorized_sequence) for url in value.request_urls)
        return ()

    def _dependency_projection(self, value):
        if type(value) is not History:
            return ()
        entry = self._required(Entries, value.entry_closure_identity)
        return tuple((value.identity, entry.start_identity, sha256(url.encode()).hexdigest()) for url in value.request_urls)

    def request_graph(self, *, start_identity):
        """Read the immutable provider-node and closure-edge populations separately."""
        schema.require_nar_pre_c_operational_envelope_archive_schema(self._connection)
        nodes = tuple(self._connection.execute(f"SELECT * FROM {schema.REQUESTS} WHERE start_identity=? ORDER BY url_sha256", (start_identity,)).fetchall())
        edges = tuple(self._connection.execute(f"SELECT * FROM {schema.DEPENDENCIES} WHERE start_identity=? ORDER BY history_closure_identity,url_sha256", (start_identity,)).fetchall())
        return nodes, edges

    def publish(self, *, value, runner, capability, _issuance_marker=None, _root_context=None):
        # Check before duplicate/idempotent logic: a saved row is never issuance permission.
        if type(value) not in _TABLES or _issuance_marker is not _ENVELOPE_ISSUANCE_MARKER:
            raise NARPreCEnvelopeError("controlled current-process issuance required")
        capability.require_current_owner(runner)
        if self._connection is not runner._connection or runner._connection.in_transaction:
            raise NARPreCEnvelopeError("publication requires this live runner's idle archive")
        schema.require_nar_pre_c_operational_envelope_archive_schema(self._connection)
        self._parents(value)
        root = self._root_for(value)
        expected_claim = value.claim_identity if type(value) is Manifest else (
            self._required(Manifest, value.manifest_identity).claim_identity if type(value) is Plan else root.claim_identity)
        if expected_claim != capability.claim_identity:
            raise NARPreCEnvelopeError("publication capability claim mismatch")
        if type(value) in (Start, Entries, History, Completion):
            if _root_context is None:
                raise NARPreCEnvelopeError("live root context required")
            _root_context.require_live()
            if _root_context.root != root:
                raise NARPreCEnvelopeError("root context ancestry differs")
        if type(value) in (Manifest, Plan, Root):
            scope = value.scope
            existing = self._connection.execute(
                f"SELECT 1 FROM {schema.STARTS} s JOIN {schema.ROOTS} r ON r.identity=s.root_identity "
                f"JOIN {schema.MANIFESTS} m ON m.identity=r.manifest_identity WHERE r.claim_identity=? AND m.scope_identity=?",
                (expected_claim, scope.identity)).fetchone()
            if existing:
                raise NARPreCEnvelopeError("prestaged/plan authority cannot be issued after root start")
        if type(value) is Completion and (_root_context.endpoint != (value.freeze_completed_at, value.monotonic_endpoint_ns)
                or _root_context.start.identity != value.start_identity):
            raise NARPreCEnvelopeError("completion requires captured current-process endpoint")
        row = self._row(value)
        table = _TABLES[type(value)]
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            existing = self._connection.execute(f"SELECT * FROM {table} WHERE identity=?", (value.identity,)).fetchone()
            if existing is None:
                self._connection.execute(f"INSERT INTO {table} VALUES({','.join('?' for _ in row)})", row)
                for request in self._request_projection(value):
                    prior = self._connection.execute(f"SELECT * FROM {schema.REQUESTS} WHERE start_identity=? AND url_sha256=?", request[:2]).fetchone()
                    if prior is None:
                        self._connection.execute(f"INSERT INTO {schema.REQUESTS} VALUES(?,?,?,?)", request)
                    elif (type(value) is not History or tuple(prior[:3]) != request[:3] or prior[3] > request[3]):
                        raise NARPreCEnvelopeError("immutable request authority conflicts")
                for edge in self._dependency_projection(value):
                    self._connection.execute(f"INSERT INTO {schema.DEPENDENCIES} VALUES(?,?,?)", edge)
            elif tuple(existing) != row:
                raise NARPreCEnvelopeError("immutable Phase108 evidence conflicts")
            self._connection.commit()
        except BaseException:
            self._connection.rollback()
            raise
        if self.load(kind=type(value), identity=value.identity) != value:
            raise NARPreCEnvelopeError("Phase108 evidence did not exact-reload")
        self._verify_requests(value)
