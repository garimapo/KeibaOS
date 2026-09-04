# Current Phase

Status: `APPROVED_FOR_COMMIT`

## Identity and authority

- Phase: `POST_V0_8_DAILY_REPLAY_13`
- Name: `NAR Daily Historical Evidence Resolver Design`
- Phase type: `DESIGN_ONLY`
- Base Commit: `7febf5af9cfd8f738dc9e3b4513c073c9db877dd`
- Branch: `feature/post-v0.8-daily-replay`
- Outcome: `IMPLEMENTABLE`
- Implementation, tests, fixtures, staging, commit and push during PREPARE: `NOT_AUTHORIZED`

Authority: AGENTS.md, docs/VER0.8_SIMULATOR_DESIGN.md, the approved Phase 1
resolver/orchestration boundary, Phase 2-6 target contracts and the Phase 12
NAR-only initial-scope decision. Phase 12 was committed, pushed normally and fetched;
local HEAD and origin/feature/post-v0.8-daily-replay both equal the Base Commit.

Review gate R1 is resolved by the explicit nullable-availability decision below.
Outcome is IMPLEMENTABLE as a design assessment; Status is APPROVED_FOR_COMMIT and
implementation is not authorized. The v0.8 causal contract and approved latest-snapshot
policy are unchanged. No production contract is amended by this correction.

## Resolved review gate R1: nullable causal eligibility

The independent review explicitly permits available_at=None as formal unknown provider
availability. Known available_at is not a required eligibility condition. An
unconditional chain requiring available_at for every reference is forbidden.

Freeze the following conditional rules for every prediction evidence reference.
information_cutoff is the snapshot's own formal prediction cutoff; scheduled_start_at
is the exact audited target.scheduled_start_at.

### available_at known

```text
available_at <= observed_at <= captured_at <= information_cutoff <= scheduled_start_at
```

### available_at is None

```text
observed_at <= captured_at <= information_cutoff <= scheduled_start_at
```

- None remains unknown, not inferred availability. Do not fill available_at with
  observed_at, current time, capture/scheduled time, completeness or fixture provenance.
  Inferred or backdated availability is forbidden.
- observed_at must retain the honest evidence observation instant.
- observed_at > captured_at is invalid.
- captured_at > information_cutoff is invalid future evidence.
- information_cutoff > target.scheduled_start_at is invalid for causal eligibility.
- Known available_at > observed_at is invalid.
- available_at=None in existing NAR records can be eligible only when all mandatory
  timestamps above and every other formal identity/schema/causal invariant hold.
  None alone is neither missing prediction evidence nor invalid evidence.
- Reuse the existing v0.8 snapshot/evidence validation and exact repository loads.
  Do not implement a looser resolver-specific causal rule or repair saved provenance.
  Existing global integrity versus target-scoped failure boundaries remain unchanged;
  candidates outside selection bounds cannot become executable.

The existing contract supporting this decision is unchanged:

- historical_input_evidence.py: HistoricalInputEvidenceReference.available_at is
  datetime | None; known available_at <= observed_at is validated.
- historical_input_snapshots.py: provenance observation/capture and snapshot
  capture/cutoff/scheduled-time invariants are validated for the full domain.
- nar_historical_input_source.py deliberately supplies available_at=None, and
  tests/test_nar_historical_input_source.py asserts that formal behavior.

No availability-presence filter, availability-based ranking, fallback to an older
known-availability snapshot, new availability reason code, or repository change is
introduced. LATEST_CAUSAL_IN_DATASET continues to select the unique latest eligible
formal snapshot regardless of whether its provider availability is known or None.

R1 is closed. Outcome is IMPLEMENTABLE, subject to independent design review and a
separately approved implementation phase. All other Phase 13 design remains unchanged.

## Existing components and actual gaps

| Existing component | Reuse and limitation |
| --- | --- |
| historical_daily_targets.py | Reuse DailyHistoricalReplayTargetSet, original targets, exact provider identity, native disposition reference, canonical ordering and content_sha256 unchanged |
| nar_historical_daily_target_source.py | Consume the audited Phase 6 output; do not repeat Monthly/RaceList parsing, navigation coverage, source acquisition or completeness discovery |
| historical_input_snapshots.py | Reuse HistoricalExternalRaceIdentity, HistoricalSourceIdentity, HistoricalInputSnapshotIdentity, HistoricalInputSnapshot and their provenance/causal validation |
| SQLiteHistoricalInputSnapshotRepository | Reuse load_latest_snapshot and load_snapshot_by_identity; reconstruct children, mappings and content digest only through this repository |
| v010 historical_input_external_races | Read exact external-to-internal reconciliation; no public existing lookup returns this mapping independently of a snapshot |
| NAROfficialResponseCapture / NAROfficialResponseCaptureArchive | Reuse immutable capture identity/body integrity and exact load_capture; the archive also supports exact URL/digest/observed evidence lookup, not latest-by-race enumeration |
| SQLiteNAROfficialResponseCaptureRepository | Reuse exact load_capture and its byte length, digest, capture-ID, canonical URL and timestamp validation |
| canonicalize_nar_official_capture_url | Reuse for stored v0.8 RaceMarkTable identity only; never apply it to Phase 6 raw Monthly/RaceList locators |
| HistoricalReplayRaceRequest | Existing executable race shape for later schema-v1 projection; cannot represent a missing-evidence target |
| load_historical_replay_request_document / run_sqlite_historical_replay | Future manifest loading and exactly one multi-race execution; neither is called by this resolver |
| official_settlement_acquisition.py and NAR result/payout persistence normalizers | Retain body interpretation, finality, purchased-type checks and settlement-fact persistence in the existing runner |

There is no SQLiteHistoricalReplayApplication class to instantiate; the application
entry is run_sqlite_historical_replay. The resolver needs only read-only metadata lookup
glue for identity reconciliation and candidate selection, plus immutable outcomes.
It does not need a new snapshot domain, capture domain, prediction/settlement engine,
generic archive Protocol, or changes to an existing repository API.

## Proposed inputs and ownership

Proposed later public entry:

```text
resolve_sqlite_nar_daily_evidence(
    *, target_set: DailyHistoricalReplayTargetSet,
    dataset_id: str,
    settlement_information_cutoff: datetime,
    snapshot_connection: sqlite3.Connection,
    capture_connection: sqlite3.Connection,
) -> DailyHistoricalReplayEvidenceResolution
```

- Accept an already audited Phase 6 target set for exactly
  {HistoricalDailyProviderIdentity("NAR", "nar_official")}. Neither a list of database
  races nor a hand-invented target set is a substitute for the audited source boundary.
- Validate target-set/provider/date/identity consistency; reject a JRA or mixed-provider
  request globally without projecting a reduced NAR scope.
- An incomplete discovery request still fails as TARGET_DISCOVERY_INCOMPLETE before
  resolution. A zero-target day is not supported by the initial NAR source contract;
  an empty list cannot be promoted into a proven zero day by this resolver.
- dataset_id is one exact caller-supplied dataset for the entire operation.
- settlement_information_cutoff is one explicit aware datetime, retained unchanged as
  an instant for every target and eventual executable request. It is not derived from
  prediction cutoff, date, run start, current time, archive stored_at or latest evidence.
- No strategy, budget, prediction callback, network client or live-acquisition fallback
  is accepted. The later daily layer still owns one race_budget projected identically
  to executable targets; this resolver does not allocate it.
- Caller opens existing databases read-only. The adapter uses query-only connections
  and stable read views; it neither owns database creation nor migration application.
  Require no caller-owned active transaction at entry, initialize existing repositories
  before beginning resolver-owned read transactions, and release only those read views.
  Do not close caller-owned connections or commit their work.
- Keep candidate metadata reads and subsequent exact loads in the same read view for
  each database. Do not claim an atomic snapshot spanning two SQLite databases or
  invent an acquisition-time cutoff from transaction start.

Determinism is relative to the same immutable target set, dataset, explicit cutoff and
database read views. Future archive ingestion may change a new latest selection; exact
references frozen in a returned value remain the basis for reproducible later replay.

## Exact identity reconciliation

Phase 6 normalizer and the v0.8 NAR source both use:

```text
organization = NAR
source_system = nar_official
external_race_id = nar:YYYYMMDD:babaCode:raceNo
```

The validated official date and canonical positive babaCode/raceNo tokens own that
identity. Do not create an identity from display venue names, place/race_no alone,
legacy SQLite IDs, row order or a guessed URL.

Read historical_input_external_races using all three exact provider/external fields.
v010 has a primary key for those fields and a unique provider/internal-race mapping.
Verify the persisted internal reference and relevant schema constraints. Missing mapping
is a retained MISSING_PREDICTION_EVIDENCE / INTERNAL_RACE_MAPPING_MISSING outcome, not
an absent race. Duplicate mappings, broken foreign keys, or conflicting persisted
identities are global RepositoryDataIntegrityError failures; never repair them.

Legacy races may cross-check the referenced stored race, but cannot prove daily
completeness or substitute a fuzzy mapping. Archive-side capture lookup can still
record settlement availability for a target whose internal mapping/snapshot is missing.

## Snapshot selection and exact repository boundary

Policy remains LATEST_CAUSAL_IN_DATASET, not a fixed lead-time policy.

For a normal replay-candidate target with a formal exact scheduled_start_at:

```text
selection_upper_bound = audited_target.scheduled_start_at
```

Eligible selection metadata must match exact dataset, provider, external race and
reconciled internal race, with captured_at <= selection_upper_bound and snapshot
information_cutoff <= selection_upper_bound. Both bounds are inclusive. The selected
formal domain must also match target_set.target_date and the audited scheduled instant,
and satisfy all existing child/schema/causal invariants, including the frozen conditional
nullable rules above. No known-availability eligibility requirement is added.

1. Read exact-key metadata in a stable read view and validate the selection fields.
   Records after either causal bound are ineligible, not silently backdated.
2. Require a unique greatest eligible captured_at; never use row ID, insertion order,
   source URL, digest or current time to break a tie.
3. Call existing load_latest_snapshot with information_cutoff=selection_upper_bound
   and the exact dataset/race/source identity. Verify agreement with metadata selection.
4. Exact-load the selected HistoricalInputSnapshotIdentity through
   load_snapshot_by_identity. Require exact identity, internal race, date, audited
   scheduled instant and matching content_sha256; retain the repository's formal value.
5. A selected row disappearing, a reconstruction failure, corrupt digest or violated
   persisted invariant is a global integrity failure. Do not scan backwards for an
   older snapshot or reconstruct the snapshot from raw rows.
6. A valid loaded domain contradicting the audited target date/start is retained as
   INVALID_EVIDENCE / SNAPSHOT_TARGET_MISMATCH, without older-snapshot fallback.
   No eligible snapshot is retained as MISSING_PREDICTION_EVIDENCE.

The v010 UNIQUE(dataset_id, organization, source_system, external_race_id,
captured_at_utc) already excludes a legal same-key latest tie. Metadata uniqueness
validation plus exact load makes the repository's ORDER BY captured_at DESC LIMIT 1
safe under that schema. A duplicate created by corrupt/incompatible storage is global
integrity failure, not an arbitrary selected race outcome. This requires no repository
contract change; nullable availability adds no selection filter or fallback.

Only exact-load domain provenance supplies causal fields. Every reference must satisfy
the frozen known/None causal rule, with information_cutoff meaning the snapshot's own
formal prediction cutoff. Settlement and daily completeness
observation times never enter it. scheduled_start_at=None targets are retained but are
never passed to load_latest_snapshot or assigned a replacement upper bound.

## Settlement selection and exact archive boundary

The eligible v0.8 NAR source is the formal RACE_MARK_TABLE capture, not the Phase 6
RaceList capture. Use metadata only, followed by existing exact load:

1. Read stored capture metadata with the existing NAR archive schema. Validate page
   kind, canonical URL and formal observation timestamps before relying on filters.
   Derive the existing external identity only from the query of the URL validated by
   canonicalize_nar_official_capture_url; require canonical equality and exact target
   date/babaCode/raceNo. Do not reconstruct an acquisition URL.
2. Restrict eligible candidates to the exact target and observed_at <= explicit
   settlement_information_cutoff. requested_at/stored_at are validated capture metadata,
   not ranking keys or substitutes for observed_at.
3. Choose unique greatest observed_at. Different captures at that greatest instant
   give INVALID_EVIDENCE / SETTLEMENT_CAPTURE_AMBIGUOUS. Neither digest, capture_id,
   stored_at nor query order breaks the tie. A duplicate of the same persisted unique
   evidence identity is storage corruption and fails globally.
4. Call SQLiteNAROfficialResponseCaptureRepository.load_capture(capture_id=...).
   Recheck exact provider/page/URL/race/time and metadata agreement. The existing
   repository validates body length, body SHA-256, capture ID and formal domain.
   Missing selected body/capture or corrupt evidence is global integrity failure.
5. Retain the selected capture reference for both result and payout. The same exact
   RACE_MARK_TABLE capture ID can populate result_capture_id and the existing supported
   payout catalog keys (単勝, 馬連, ワイド, 3連複). This is an evidence catalog, not a bet
   plan or an assertion that a payout for every type is present.
6. No eligible capture yields retained MISSING_SETTLEMENT_EVIDENCE, with both result
   and payout reference absent. Do not use a current page, another race/date/provider,
   a capture after settlement cutoff, or a legacy unarchived result as fallback.

NAR v001 stores a unique (canonical_source_url, response_sha256, observed_at_utc)
evidence tuple, not a unique (race, observed_at) selection key. Two different bodies
at the same observation instant can therefore be a genuine selection ambiguity.
Different observation instants are archive history; different digests alone do not
prove either contradiction or equivalence. The approved policy selects the latest
eligible instant, not an arbitrary latest tie.

EXECUTABLE means exact references and pre-resolution checks succeeded, not that a
body-level final result/payout has already been normalized. Existing result/payout
normalizers remain the sole owners of visible identity, malformed/duplicate rows,
unsupported result state and payout/body contradiction checks. This resolver never
parses HTML, invokes a persistence normalizer with a dummy repository, or adds new
normalization logic. There is no public existing pure dry-run settlement validator
that can be reused to guarantee successful settlement here.

A contradiction already established in target-bound metadata is INVALID_EVIDENCE;
unattributable malformed metadata/schema corruption is global failure. Later body-level
unsupported/malformed/contradictory evidence must propagate from the existing runner.
Do not describe an unexamined body as semantically valid or infer cross-version
agreement by comparing hashes. Requiring cross-version body reconciliation before
execution would be a separate reviewed contract, not part of this metadata resolver.

Settlement may legitimately be observed after the race and after prediction cutoff.
Its sole selection upper bound is the explicit settlement cutoff, never the snapshot
cutoff. No result/payout bytes or metadata are passed into prediction inputs.

## Immutable output proposal and necessity

Existing target sets do not express evidence eligibility. HistoricalReplayRaceRequest
requires executable references, and SimulationSummary describes execution, not missing
targets. Therefore propose a small provider-neutral resolution boundary in a new module;
do not extend the Phase 6 shared domain or introduce another replay request schema.

- DailyHistoricalReplayEvidenceDisposition: EXECUTABLE,
  MISSING_PREDICTION_EVIDENCE, MISSING_SETTLEMENT_EVIDENCE, UNSUPPORTED,
  INVALID_EVIDENCE. These are resolver-only names, not provider-native race statuses.
  They refine Phase 1's MISSING_EVIDENCE/INVALID categories; no existing production
  disposition enum is renamed.
- DailyHistoricalReplayCaptureReference: capture_id, canonical_source_url,
  response_sha256, observed_at. Exact provider/race binding is supplied and validated
  through its owning target outcome. This deliberately contains no body, storage ID
  or invented provider_available_at. HistoricalInputEvidenceReference is not reused
  as a settlement reference because it owns prediction-provenance semantics and lacks
  the exact archive capture ID.
- DailyHistoricalReplayTargetOutcome: original target, disposition, ordered reason_codes,
  internal_race_id | None, snapshot_identity | None, snapshot_content_sha256 | None,
  result_capture_reference | None, payout_capture_reference | None. Reuse existing
  HistoricalInputSnapshotIdentity and the same selected capture reference for both
  settlement roles. Valid partial references may be retained on non-executable outcomes.
- DailyHistoricalReplayEvidenceResolution: original target_set, dataset_id,
  selection_policy, explicit settlement_information_cutoff, complete ordered outcomes.
  Day-level resolution state is derived, not an independently mutable assertion.

All proposed values are immutable. EXECUTABLE requires all references, correct exact
binding, no failure reasons and a supported normal target; no missing reference is
replaced by a synthetic ID. A rejected candidate is never recorded as a resolved
snapshot. available_at=None alone does not remove eligibility or create a failure reason;
the frozen mandatory timestamps and all other eligibility checks still apply.

For a non-executable target preserve every established reason, not just one problem.
Primary disposition precedence is INVALID_EVIDENCE, UNSUPPORTED,
MISSING_PREDICTION_EVIDENCE, MISSING_SETTLEMENT_EVIDENCE; EXECUTABLE is the all-clear
case. Thus a target missing both sides retains both reasons even though one primary
disposition must be selected.

Initial reason vocabulary for the later design: INTERNAL_RACE_MAPPING_MISSING,
SNAPSHOT_MISSING, SNAPSHOT_AFTER_SELECTION_BOUND, SNAPSHOT_TARGET_MISMATCH,
RESULT_CAPTURE_MISSING, PAYOUT_CAPTURE_MISSING, SETTLEMENT_CAPTURE_AMBIGUOUS,
TARGET_EVIDENCE_IDENTITY_MISMATCH, NATIVE_NON_RUN, UNKNOWN_NATIVE_DISPOSITION,
SCHEDULED_START_UNAVAILABLE. No missing/invalid-availability reason is introduced for
available_at=None alone. Never downgrade repository corruption to these reason codes.

Consume existing native disposition evidence:
nar-race-list-target-row-v1 identifies the approved normal row boundary;
nar-race-list-whole-meeting-cancelled-no-substitute-v1 remains UNSUPPORTED for replay
while its targets stay in the denominator, even when an exact scheduled time exists.
Unknown native semantics never fall back to normal. A normal target missing an exact
scheduled instant is INVALID_EVIDENCE; exceptional/unknown targets without it remain
UNSUPPORTED. No neutral cancellation enum or expanded support is introduced.

## Day-level state, ordering and digest boundary

Require outcomes to correspond one-for-one to the original canonical targets, without
duplicates, additions or omissions. Preserve canonical order
(organization, source_system, external_race_id), including its lexical external-ID
ordering; do not substitute numeric race order, scheduled time or internal IDs.

Derived resolution states:

| State | Predicate and permitted claim |
| --- | --- |
| ALL_TARGETS_RESOLVED | Nonempty original set, every outcome EXECUTABLE; evidence resolution only, not replay success |
| PARTIALLY_RESOLVED | At least one EXECUTABLE and at least one non-executable target; never full-day replay success |
| NO_EXECUTABLE_TARGETS | Original targets retained, none executable; no manifest and no runner invocation |

Discovery completeness and replay evidence completeness are different properties.
The resolver returns the full outcome tuple even for PARTIALLY_RESOLVED or
NO_EXECUTABLE_TARGETS. It returns no partial day value if a global integrity/DB failure
interrupts processing. Target-scoped failures never change membership.

A later executable projection may be replayed once under Phase 1, but must remain
labelled partial if any original target is non-executable. It must not claim full-day
ROI or all-target replay success. ALL_TARGETS_RESOLVED also cannot claim replay success
until the existing runner completes successfully. Any runner exception propagates:
no partial SimulationSummary, successful daily result conversion, retry or reduced-
manifest rerun. Existing durable-prefix semantics are not changed.

Reuse target_set.content_sha256, exact snapshot digest and existing capture digest/ID.
No new resolver digest, JSON schema, serialization format or durable storage is needed.
Reason codes have unique lexical ordering; payout projection uses the existing closed
bet-type keys deterministically. Datetime equality uses aware instants normalized to
UTC; no current-time field is introduced. A future artifact/persistence phase must
separately freeze any new canonical bytes rather than hashing repr, unordered mappings,
SQLite IDs or filesystem metadata.

## Future flow and schema responsibility

```text
audited NAR target set + exact dataset + explicit settlement cutoff
  -> validate scope and existing schemas; open stable read views
  -> annotate every original target's native replay eligibility
  -> exact internal identity mapping
  -> bounded snapshot metadata + existing latest/exact repository loads
  -> bounded RaceMarkTable metadata + existing exact archive load
  -> immutable complete target outcomes + derived resolution state
  -> return; no network, manifest, normalizer, prediction or settlement execution
```

No migration is needed for the proposed read-only lookup: main v010 tables already
hold mapping/snapshot metadata and children; NAR archive v001 holds metadata and bodies.
Validate required table/column/key/index contracts and stored identity/time invariants;
missing or incompatible schema fails globally. Resolver must not apply main migrations,
archive migrations, DDL, save_snapshot, save_capture or a repair operation.
run_sqlite_historical_replay retains main migration ownership.

A new archive Protocol is not justified: existing concrete repositories supply exact
loads, while private read-only SQL helpers provide the missing enumeration. Do not
expose those helpers as production repository APIs merely for testing.

Only a later manifest phase projects executable outcomes to existing
HistoricalReplayRaceRequest fields and freezes a real schema-v1 file, which is then
loaded through load_historical_replay_request_document. No synthetic source_path or
new request schema. The later orchestrator calls run_sqlite_historical_replay exactly
once for a nonempty projection. SimulationSummary.race_count remains unchanged; no
target_race_count, reporting aggregation or persistence is added.

## Proposed later files, not current Allowed Files

| Candidate file | Proposed ownership |
| --- | --- |
| scripts/simulation/historical_daily_evidence_resolution.py | Provider-neutral immutable reference/outcome/day result and resolver dispositions; no NAR parser assumptions, DB or network |
| scripts/simulation/sqlite_nar_daily_evidence_resolver.py | resolve_sqlite_nar_daily_evidence; NAR identity/native eligibility and read-only SQLite selection glue using existing repositories |
| tests/test_historical_daily_evidence_resolution.py | Immutable output, denominator, disposition/day state and deterministic order validation |
| tests/test_sqlite_nar_daily_evidence_resolver.py | Exact lookup, causality, archive integrity, no-network/read-only behavior and integration with existing formal values |

These remain proposals for a separately approved implementation phase; R1 is resolved.
No existing NAR/shared/snapshot/normalizer/runner module modification is proposed.
No new official-byte fixture acquisition, archive Protocol, schema, migration, CLI or
dependency is justified. Tests can use constructed formal values and temporary databases
under existing test helpers; test setup migration is not resolver migration authority.

## Required design tests for a later implementation phase

- Exact audited target -> provider/external/internal identity -> dataset snapshot;
  wrong provider, external token, date, dataset or internal mapping cannot match.
- Unique latest causal candidate; both inclusive boundary equalities; captured_at or
  information_cutoff after audited scheduled time rejected with no backdating.
- Snapshot target date/start cross-check; no scheduled bound for None; known non-run
  target retained without a snapshot lookup.
- Nullable causality tests: existing NAR available_at=None can be eligible when all
  mandatory timestamps hold; known availability must also be <= observed_at.
  Reject observed_at > captured_at, captured_at > information_cutoff and
  information_cutoff > audited scheduled_start_at for either availability branch.
  Verify honest observed_at, no inferred/backdated/current-time availability, and no
  substitution of available_at=observed_at. A latest eligible None snapshot must not
  be rejected or replaced by an older known-availability snapshot. Reuse existing
  formal validation and load_latest_snapshot; do not alter a fixture to hide None.
- Duplicate greatest snapshot metadata or removed UNIQUE constraint fails globally;
  corrupt selected snapshot/children/digest does not fall back to an older snapshot.
- Missing mapping/snapshot retained in denominator; both prediction and settlement
  missing reasons retained; unknown/native non-run not changed into a normal race.
- Exact NAR RaceMarkTable result/payout reference reuse; correct canonical query binding;
  foreign provider/race/page rejected; no URL acquisition/reconstruction.
- Unique greatest observed_at under explicit settlement cutoff, including equality;
  later observations ineligible, same-greatest different captures fail closed.
- Duplicate persisted evidence identity, corrupt capture ID/body SHA/length, broken
  body reference and selected-capture disappearance fail globally, not as missing.
- Missing settlement references retained; malformed/unattributable metadata fails
  globally; safely target-bound identity contradictions yield INVALID_EVIDENCE.
- Settlement observed after race/prediction cutoff but before settlement cutoff is
  allowed; no settlement/completeness/fixture timestamp enters snapshot causality.
- No network, clock, acquisition, save, migration, HTML parsing or replay invocation;
  test with those dependencies failing if called; read-only database contents unchanged.
- Stable output for permuted insertion/query order and timezone-equivalent instants;
  original target membership and lexical canonical order preserved.
- Partial day is never ALL_TARGETS_RESOLVED or full-day replay success; none executable
  retains all targets and cannot build a manifest or call a runner.
- Existing runner tests retain body-level malformed/unsupported failure propagation;
  this resolver cannot catch those future exceptions, retry or drop-and-rerun.

Later implementation verification must run the two proposed dedicated modules, related
snapshot/archive/request/application/daily-source tests and the full unittest suite.
Exact executable test commands and any test helper changes belong in that later
implementation PREPARE. R1 is resolved; this DESIGN_ONLY phase adds/runs no tests;
source and related existing tests were inspected read-only.

## Allowed Files

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Forbidden Files and actions

All other files, including production, tests, fixtures, schemas, migrations, database,
logs, archives, CLI, dependencies, AGENTS.md and release/tag history. No live acquisition,
fixture materialization, JRA implementation, shared-domain modification, new prediction/
bet/settlement logic, manifest implementation, daily orchestration or ROI reporting.

No staging, commit, push, EXECUTE_APPROVED_PHASE or next-phase start is authorized during
this PREPARE. The Phase 12 commit authorization does not extend to Phase 13.

## Required PREPARE checks and stop condition

```text
git diff --check
git diff --name-only
git status --short
git diff --cached --name-only
```

Require exactly the two Allowed Files modified, no staged files and HEAD unchanged from
the verified Base Commit. Stop at DRAFT_FOR_REVIEW / IMPLEMENTABLE for ChatGPT review.
R1 is resolved, but implementation remains unauthorized; no availability fallback
or known-availability-only eligibility may be introduced.
Any unexpected file, schema-ownership expansion or additional contract conflict also
requires stopping rather than speculative repair.
