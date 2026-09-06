# Current Phase

Status: `READY_FOR_REVIEW`

## Identity, authority and authorization

- Phase: `POST_V0_8_DAILY_REPLAY_14`
- Name: `NAR Daily Historical Evidence Resolver Implementation`
- Phase type: `IMPLEMENTATION`
- Base Commit: `0e48e7c795cfec4a10563a1f85234822b8b09c3f`
- Branch: `feature/post-v0.8-daily-replay`
- Preparation assessment: `IMPLEMENTABLE`
- Current authorization: approved EXECUTE completed; review pending, no staging/commit/push.

AGENTS.md, docs/VER0.8_SIMULATOR_DESIGN.md's applicable authoritative contracts and
the approved Phase 13 design at the Base Commit govern this implementation contract.
Phase 13 includes the final nullable available_at decision. Its exact documentation
commit was pushed normally, fetched and verified equal to the remote branch before
this PREPARE. Earlier phase contracts are not rewritten or broadened here.

This phase implements only the approved immutable resolution boundary and read-only
NAR lookup adapter after a later APPROVE_PHASE and EXECUTE_APPROVED_PHASE. The
IMPLEMENTATION phase type is not permission to implement during PREPARE.
No unresolved design blocker was found. Any later conflict requires stopping.

## Exact Allowed Files

### During PREPARE

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

### Only after explicit approved EXECUTE

```text
scripts/simulation/historical_daily_evidence_resolution.py
scripts/simulation/sqlite_nar_daily_evidence_resolver.py
tests/test_historical_daily_evidence_resolution.py
tests/test_sqlite_nar_daily_evidence_resolver.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

The four production/test paths are new files. Existing production/test files are
read/reuse only. No package re-export or __init__.py modification is required.
Private test helpers belong in the two new test modules, not in another helper file.

## Forbidden Files and actions

Every path outside the applicable Allowed Files, including existing shared/NAR/JRA
production, tests, fixtures, AGENTS.md, detailed Ver0.8 design, dependencies, CLI,
schema/migrations, database/**, logs/** and provider archives. database/keiba.db and
logs/ must never be staged or committed. Tags/release history remain unchanged.

No new archive Protocol, migration, schema, durable archive, live acquisition,
fixture materialization, HTML parsing, manifest builder, daily orchestrator, reporting,
ROI aggregation, prediction/bet/settlement logic or JRA support. No stage, commit, push
or next-phase transition is authorized by PREPARE or the future EXECUTE.

## Public API: provider-neutral immutable values

Only the following public definitions belong in
scripts/simulation/historical_daily_evidence_resolution.py. Imports/helpers are private.
Use frozen, slotted dataclasses for the three values and StrEnum for the two enums.
No public builder, serializer, repository, clock or prediction callback is needed.

| Public name | Exact fields / values |
| --- | --- |
| DailyHistoricalReplayEvidenceDisposition | EXECUTABLE, MISSING_PREDICTION_EVIDENCE, MISSING_SETTLEMENT_EVIDENCE, UNSUPPORTED, INVALID_EVIDENCE; string values equal their names |
| DailyHistoricalReplayResolutionState | ALL_TARGETS_RESOLVED, PARTIALLY_RESOLVED, NO_EXECUTABLE_TARGETS; string values equal their names |
| DailyHistoricalReplayCaptureReference | capture_id: str; canonical_source_url: str; response_sha256: str; observed_at: datetime |
| DailyHistoricalReplayTargetOutcome | target: DailyHistoricalReplayTarget; disposition: DailyHistoricalReplayEvidenceDisposition; reason_codes: tuple[str, ...]; internal_race_id: int \| None; snapshot_identity: HistoricalInputSnapshotIdentity \| None; snapshot_content_sha256: str \| None; result_capture_reference: DailyHistoricalReplayCaptureReference \| None; payout_capture_reference: DailyHistoricalReplayCaptureReference \| None |
| DailyHistoricalReplayEvidenceResolution | target_set: DailyHistoricalReplayTargetSet; dataset_id: str; selection_policy: str; settlement_information_cutoff: datetime; outcomes: tuple[DailyHistoricalReplayTargetOutcome, ...] |

DailyHistoricalReplayEvidenceResolution.day_state is a derived read-only property of
type DailyHistoricalReplayResolutionState, not an independently supplied field.
selection_policy must equal LATEST_CAUSAL_IN_DATASET; do not add a policy registry.

Construction invariants:

- Exact existing domain/reference/enum types; reject malformed inputs with ValueError.
  No bool-as-int; internal IDs when present are positive integers. Text must be nonempty
  and already NFC without surrounding whitespace. Digests are lowercase 64-hex strings.
  Datetimes must be aware and normalize to UTC without using current time.
- Capture reference URL validation is provider-neutral HTTPS/no credentials/fragment;
  no NAR URL grammar, capture-ID prefix, native-state or venue assumption in this module.
  Provider-specific binding remains the adapter's responsibility.
- Snapshot identity and snapshot digest are both present or both None. A snapshot
  reference requires internal_race_id and exact provider/external identity agreement
  with the target. Do not invent a snapshot or linkage to fill missing evidence.
- EXECUTABLE requires all resolved references, an exact scheduled_start_at and no
  reason codes. Every non-executable disposition requires at least one reason.
  Valid partial references may remain; a rejected candidate is not a resolved snapshot.
- reason_codes is a tuple of unique nonempty strings, canonicalized lexically;
  reject duplicates rather than silently discarding them. The shared class does not
  encode NAR-specific reason-to-disposition rules.
- Outcomes must cover the original target set exactly once, with matching target
  content. Reject missing, extra, duplicate or contradictory targets. Canonicalize
  outcome order to the original target set's (organization, source_system,
  external_race_id) ordering, not numeric race number or internal ID.
- The resolver forwards each original target object; no target content is rewritten.
  The day result retains the original target_set and its existing content_sha256.
- Require a nonempty target set for this resolution result. An empty set cannot satisfy
  ALL_TARGETS_RESOLVED vacuously or imply a newly supported zero day.
- Cross-check every snapshot's dataset/provider/external identity against the day
  context; any reference observed_at later than settlement_information_cutoff is
  invalid in the day result. Full snapshot causality and capture integrity are checked
  through existing repositories by the adapter, not reconstructed in these values.

No new digest/serialization format is implemented. Retain existing target-set,
snapshot and capture digests, not Python repr/hash, row order, current time or file
metadata. Do not add target_race_count or alter SimulationSummary.race_count.

## Public API: read-only NAR adapter

The sole public definition in scripts/simulation/sqlite_nar_daily_evidence_resolver.py:

```python
def resolve_sqlite_nar_daily_evidence(
    *,
    target_set: DailyHistoricalReplayTargetSet,
    dataset_id: str,
    settlement_information_cutoff: datetime,
    snapshot_connection: sqlite3.Connection,
    capture_connection: sqlite3.Connection,
) -> DailyHistoricalReplayEvidenceResolution:
    ...
```

All metadata/schema/identity helpers are private. Reuse the existing concrete
repositories directly; do not add an archive Protocol or expose SQL helpers for tests.

Input and connection boundary:

- Require the already audited Phase 6 NAR target set; exact singleton scope
  {HistoricalDailyProviderIdentity("NAR", "nar_official")}. Generic value construction
  alone does not prove source completeness. Do not rediscover or reacquire evidence.
- Reject mixed/JRA scope or an unsupported empty discovery set as whole-request
  TargetDiscoveryIncompleteError with existing UNSUPPORTED_ENVELOPE_STATE code.
  Malformed API values use ValueError; unusable connections/active caller transactions
  use existing RepositoryValidationError. Do not fabricate a new discovery enum.
- dataset_id is exact and settlement_information_cutoff is caller-supplied aware time.
  No budget, strategy, network client, current clock or acquisition fallback.
- Require two distinct usable caller-owned SQLite connections with no active
  transaction. Caller opens disk databases with mode=ro; isolated in-memory databases
  may be used by tests. Enforce/verify query_only and foreign_keys on both connections.
- Initialize existing repositories before starting read transactions (the NAR
  repository rejects construction during an active transaction). Use explicit
  resolver-owned read views; metadata and exact loads share each database's view.
- Release only resolver-owned read transactions in finally, on success and failure.
  Do not close connections, commit caller work or roll back a transaction present
  before entry. query_only/foreign_keys remain enabled; no persistent write is allowed.
- No cross-database atomicity promise. No file opens, ATTACH, DDL, migration/save calls,
  raw official response acquisition, parser execution or replay execution.

## Required existing schema and exact reuse points

Read/reuse these unchanged modules at the Base Commit:

| Module / symbol | Responsibility retained |
| --- | --- |
| historical_daily_targets.py | Audited target/domain identity, ordering, digest and native reference |
| historical_input_snapshots.py / historical_input_evidence.py | Formal identity, snapshot, complete child/provenance validation and nullable causal invariants |
| SQLiteHistoricalInputSnapshotRepository.load_latest_snapshot | Inclusive upper-bounded exact dataset/provider/external/internal selection and full-domain reconstruction |
| SQLiteHistoricalInputSnapshotRepository.load_snapshot_by_identity | Exact identity reload and digest/integrity verification |
| canonicalize_nar_official_capture_url / NAROfficialPageKind | Formal v0.8 capture URL/page identity; not a Phase 6 raw-locator canonicalizer |
| SQLiteNAROfficialResponseCaptureRepository.load_capture | Exact capture/body length/SHA/ID reconstruction |
| Existing NAR result/payout normalizers / official_settlement_acquisition.py | Body interpretation/finality/purchased bet types and settlement-fact persistence, called only by the future existing runner |
| HistoricalReplayRaceRequest / schema-v1 loader / run_sqlite_historical_replay | Later projection/real-artifact loading and execution, never called by this adapter |

Schema inspection must reflect current repositories, not just the original v010 header
schema. Main dependencies are existing v010 snapshot/mapping tables plus the existing
v011-v014 evolution: in particular v012 historical_input_snapshot_provenance_evidence
and v014 request_identity_sha256. Requiring these existing columns is not a migration
proposal. v015 JRA seed functionality is not used. NAR archive uses its existing v001
capture/body schema. Do not run migration discovery/application as a side effect.

Private preflight uses read-only table/column/key/index/FK inspection against the
consumed Base Commit contracts. Required relations include races/horse linkage,
historical_input_source_identities, historical_input_external_races,
historical_input_external_entries, historical_input_snapshots and its race/entry/
past-race/provenance/evidence children, plus nar_official_response_captures and
nar_official_response_bodies. Missing/incompatible schema raises
RepositoryDataIntegrityError, even if no target would produce an executable snapshot.
No automatic repair or fallback to legacy columns.

Validate the existing unique snapshot natural key and external/internal mapping
constraints; archive uniqueness is (canonical_source_url, response_sha256,
observed_at_utc). Stored UTC selection timestamps must be real canonical microsecond
ISO instants with +00:00, not merely strings accepted by a coarse SQLite CHECK.
Metadata decoding is allowed; rebuilding a snapshot from raw rows is forbidden.

## Exact target and prediction resolution

1. Process all targets in the canonical target order. Validate the provider/external
   tuple against the approved nar:YYYYMMDD:babaCode:raceNo grammar and target date.
   No display-place matching or URL generation. Safely target-bound malformed identity
   is INVALID_EVIDENCE / TARGET_EVIDENCE_IDENTITY_MISMATCH.
2. Preserve native membership. The existing nar-race-list-target-row-v1 kind is the
   normal replay-candidate boundary; missing exact time is INVALID_EVIDENCE with
   SCHEDULED_START_UNAVAILABLE. The approved
   nar-race-list-whole-meeting-cancelled-no-substitute-v1 kind is UNSUPPORTED with
   NATIVE_NON_RUN, even when a time is present. Unknown native kind is UNSUPPORTED with
   UNKNOWN_NATIVE_DISPOSITION. None time never gets a replacement bound.
   For targets blocked by native eligibility, retain the outcome without pretending
   that evidence lookup ran or adding unestablished missing-evidence reasons.
3. For an otherwise normal target, reconcile exact organization/source/external
   identity through historical_input_external_races. Missing mapping adds
   INTERNAL_RACE_MAPPING_MISSING. Duplicate/conflicting mappings, missing referenced
   internal race or persisted linkage corruption raise globally.
4. Read snapshot metadata for the exact dataset/provider/external identity, validate
   internal mapping and timestamp fields, then retain candidates satisfying BOTH
   captured_at <= target.scheduled_start_at and
   information_cutoff <= target.scheduled_start_at.
   No rows gives SNAPSHOT_MISSING; only out-of-bound rows gives
   SNAPSHOT_AFTER_SELECTION_BOUND. With missing mapping do not invent an internal ID.
5. Select unique greatest captured_at. Natural-key duplication or incompatible UNIQUE
   schema is global integrity failure, not a row-ID tie-break. Call
   load_latest_snapshot(dataset_id=..., race_id=..., source_identity=exact
   HistoricalExternalRaceIdentity(...), information_cutoff=target.scheduled_start_at).
   Require agreement with metadata, including not-found agreement.
6. For a candidate, call load_snapshot_by_identity(identity=latest.identity). Require
   matching formal domain and explicitly matching content_sha256, identity/linkage,
   dataset, target date and audited scheduled instant. Never rely on dataclass equality
   alone for digest comparison (the existing snapshot digest excludes comparison).
7. Repository reconstruction/invariant/digest failure or a selected identity disappearing
   raises globally. A valid loaded snapshot contradicting audited date/start yields
   SNAPSHOT_TARGET_MISMATCH / INVALID_EVIDENCE with no resolved snapshot reference.
   Neither case retries an older snapshot.

The policy name remains LATEST_CAUSAL_IN_DATASET. For each exact-loaded evidence
reference the approved causal rules are:

```text
known available_at:
  available_at <= observed_at <= captured_at <= information_cutoff <= audited scheduled_start_at
available_at=None:
  observed_at <= captured_at <= information_cutoff <= audited scheduled_start_at
```

Use the existing full snapshot/evidence validation, not a weaker local reconstruction.
None is legitimate unknown availability and does not create a failure reason, filter
or ranking preference. No substitution, inference, backdating or current-clock usage.
The latest eligible None snapshot wins over an older known-availability snapshot.
Records beyond selection bounds cannot execute; formal stored causal violations are
global integrity errors. No fixed lead-time policy is introduced.

## Exact settlement resolution

For otherwise normal targets, perform this independent lookup even if prediction
mapping/snapshot is missing, so all established shortages and partial references survive.

1. Read formal NAR capture metadata, validate kind/canonical URL/selection fields, and
   derive exact date/babaCode/raceNo only from the query validated by the existing
   canonicalizer. No raw HTML parsing, generated capture URL or reused RaceList body.
   Only RACE_MARK_TABLE is eligible. Valid unrelated records are not candidates;
   malformed/unattributable stored metadata is a global integrity error, not skipped.
2. Apply observed_at <= explicit settlement_information_cutoff inclusively, and choose
   unique greatest observed_at for the exact target. requested_at/stored_at must meet
   capture invariants but never rank candidates. Different captures at the greatest
   instant produce SETTLEMENT_CAPTURE_AMBIGUOUS / INVALID_EVIDENCE.
   A duplicate persisted unique evidence identity is global storage corruption.
3. Exact-load the chosen capture through load_capture(capture_id=...). Verify formal
   capture type, page, URL/race, ID/digest/time and agreement with selected metadata;
   existing repository validates exact bytes/length/digest/ID. Missing selected
   body/capture, corrupt digest or read-view disagreement raises globally.
4. No eligible capture gives both RESULT_CAPTURE_MISSING and PAYOUT_CAPTURE_MISSING.
   Retain the target, prediction reference if available and MISSING_SETTLEMENT_EVIDENCE.
5. Use the same immutable selected reference for result and payout. A later schema-v1
   projection may reuse that ID for the existing four payout catalog keys. Do not
   predict purchased types or guarantee body-level payout completeness here.

Different observation instants remain archive history; differing digests alone do not
establish semantic contradiction or agreement. No arbitrary same-instant tie-break,
latest-body reconciliation, current-page fallback or prediction cutoff substitution.
Honest post-race settlement observation is allowed within the explicit settlement cutoff.
Neither settlement nor completeness/fixture provenance flows into prediction.

EXECUTABLE is pre-resolution reference readiness, not validated successful settlement.
Existing NAR normalizers own body-level identity/duplicate/malformed/unsupported checks
during later execution. They are not invoked by this read-only resolver. The future
runner must propagate their errors without partial success, retry or reduced replay.

## Exact failure and whole-day result semantics

Adapter reason mapping is closed to the approved vocabulary:

| Primary disposition | Reasons |
| --- | --- |
| INVALID_EVIDENCE | SNAPSHOT_TARGET_MISMATCH, SETTLEMENT_CAPTURE_AMBIGUOUS, TARGET_EVIDENCE_IDENTITY_MISMATCH; SCHEDULED_START_UNAVAILABLE for a normal row |
| UNSUPPORTED | NATIVE_NON_RUN, UNKNOWN_NATIVE_DISPOSITION; SCHEDULED_START_UNAVAILABLE may accompany an exceptional/unknown target |
| MISSING_PREDICTION_EVIDENCE | INTERNAL_RACE_MAPPING_MISSING, SNAPSHOT_MISSING, SNAPSHOT_AFTER_SELECTION_BOUND |
| MISSING_SETTLEMENT_EVIDENCE | RESULT_CAPTURE_MISSING, PAYOUT_CAPTURE_MISSING |
| EXECUTABLE | Empty reason tuple, all required references validated |

Retain all established reasons, sorted lexically. If several categories occur, primary
precedence is INVALID_EVIDENCE > UNSUPPORTED > MISSING_PREDICTION_EVIDENCE >
MISSING_SETTLEMENT_EVIDENCE; never suppress a second established shortage.

Global RepositoryDataIntegrityError (including existing repository errors) returns
no partial resolution result and is never translated into a local disposition.
Private SQL/read failures use that existing exception with the cause retained.
API ValueError/RepositoryValidationError and existing discovery failures also propagate.
No new broad catch-and-continue or generic success sentinel. Failure while resolving
a later race cannot return the earlier outcomes as a successful day.

Day state is derived exactly:

| State | Predicate |
| --- | --- |
| ALL_TARGETS_RESOLVED | Nonempty denominator; every outcome EXECUTABLE |
| PARTIALLY_RESOLVED | At least one EXECUTABLE and at least one non-executable |
| NO_EXECUTABLE_TARGETS | Nonempty denominator; no outcome EXECUTABLE |

No state is a full-day replay-success/ROI assertion. In particular PARTIALLY_RESOLVED
is never complete replay. No executable means no future manifest/runner; this phase
never calls either in any state. All targets, including non-run/missing/invalid, remain
one-for-one in the result. Canonical order is unchanged and no count field is added.

## Required tests during EXECUTE

The following acceptance matrix is mandatory; tests belong only in the two Allowed
test files. Do not freeze a test count in place of these behaviors.

| # | Required case / assertion |
| --- | --- |
| 1 | Exact target -> dataset/provider/external/internal mapping -> selected snapshot; mismatched identity/date/start cannot match |
| 2 | Unique latest causal selection, both inclusive cutoff boundaries, metadata/latest/exact loader agreement |
| 3 | Future captured/cutoff candidates excluded; no backdating and no malformed-selected-candidate fallback |
| 4 | Ambiguous latest snapshot or removed uniqueness constraint raises global integrity error |
| 5 | available_at=None eligible under all mandatory timestamps; latest None not replaced by older known availability |
| 6 | Known available_at > observed_at rejected; also observation/capture/cutoff/start violations and no timestamp substitution |
| 7 | Missing mapping/snapshot stays in denominator with correct reason; valid settlement reference retained |
| 8 | Exact RaceMarkTable selection and result/payout reference reuse; wrong race/provider/page cannot match |
| 9 | Settlement cutoff inclusive equality and exclusion of later captures; requested/stored times never rank |
| 10 | Missing settlement retained with both result/payout missing reasons; both-side missing preserves all reasons |
| 11 | Same-time ambiguous settlement is INVALID_EVIDENCE; duplicate stored identity or corrupt capture ID/digest/bytes/body linkage raises globally |
| 12 | Settlement after race/prediction cutoff allowed within settlement cutoff; prediction/completeness/fixture timestamps kept separate |
| 13 | Immutable values, exact public surface, canonical tuple/reason ordering, timezone-equivalent equality, shuffled insertion order; duplicate/missing/extra outcomes rejected |
| 14 | No network/acquisition/parser/runner calls; read-only views and connection ownership; no writes, schema application or repairs |
| 15 | No current-clock dependency: fixed inputs, static source inspection and call traps; no availability/current-time fallback |
| 16 | All three day states, partial != complete, retained non-run/None/unknown targets, no executable != empty denominator |
| 17 | Late global failure raises without returning partial result; missing/incompatible schema and corrupt selected children fail closed |

Test setup may construct formal snapshots/captures with fixed synthetic bytes and
honest test constants, seed isolated temporary databases using existing migrations/save
APIs, then reopen mode=ro before invoking the resolver. Such writes belong only to
setup, never the resolver. No official fixture, external response or formal dataset is
created. Deliberately corrupt copies for negative cases; never mutate repository DBs.
Reuse existing test patterns by reading them, not changing/importing TestCase subclasses
to inflate test discovery. New private helper functions live in the two new test files.

No-network/no-clock tests must fail if those dependencies are called, not merely assert
that a result exists. Inspect new production source for forbidden imports/calls and
use mocks/SQLite trace or authorizer checks around the actual resolver. Allow its
read transactions and connection-only query_only/foreign_keys PRAGMAs; reject DML/DDL,
migration, save, normalizer or runner execution. Every test remains offline.

### Exact verification commands (only during EXECUTE)

Dedicated:

```text
python -m unittest tests.test_historical_daily_evidence_resolution tests.test_sqlite_nar_daily_evidence_resolver
```

Related regression checks:

```text
python -m unittest tests.test_historical_daily_targets tests.test_nar_historical_daily_target_source tests.test_historical_input_snapshots tests.test_sqlite_historical_input_snapshot_repository tests.test_nar_historical_input_source tests.test_nar_official_response_capture tests.test_sqlite_nar_official_response_capture_repository
python -m unittest tests.test_nar_target_race_result_persistence tests.test_nar_target_race_payout_persistence tests.test_official_settlement_acquisition tests.test_historical_replay_request_document tests.test_historical_replay_request_application tests.test_sqlite_historical_replay_application
```

Full suite:

```text
python -m unittest discover -s tests -p "test_*.py"
```

Static boundary search (inspect every hit; a no-match exit from rg is expected):

```text
rg -n "requests|httpx|urllib.request|socket|datetime.now|datetime.today|utcnow|time.time|apply_migrations|apply_capture_schema_migrations|save_snapshot|save_capture|run_sqlite_historical_replay|normalize_and_persist|BeautifulSoup|target_race_count" scripts/simulation/historical_daily_evidence_resolution.py scripts/simulation/sqlite_nar_daily_evidence_resolver.py
```

Required Git checks at PREPARE and EXECUTE completion:

```text
git diff --check
git diff --name-only
git status --short
git diff --cached --name-only
```

Account for untracked files in git status: git diff --name-only alone does not cover
new production/tests. Do not stage to make them visible to diff. Report dedicated,
related and full suite results separately; no skipped/relaxed failing assertions or
out-of-scope regression fixes. Warnings must be reported with evidence, not dismissed.

## EXECUTE_APPROVED_PHASE gate and stop condition

Before any implementation, verify Status APPROVED_FOR_CODEX, exact Phase/Branch/Base,
no unexpected tracked/untracked changes, empty index and the Allowed/Forbidden/
Required Tests/Stop Condition above. User requests GPT-5.6 Sol for the later EXECUTE;
this PREPARE does not execute or initiate that separate instruction.

On authorized implementation success only: all dedicated/related/full tests pass,
all boundary searches are reviewed, only the six exact EXECUTE paths changed,
git diff --check succeeds and cached is empty. Update Status to READY_FOR_REVIEW and
append implementation/test/check results to LATEST_CODEX_REPORT; then stop.
Do not stage, commit, push or advance phases.

On failure, contract conflict, need to edit any existing production/test module,
migration/archive Protocol requirement, unexpected file or unresolved ambiguity:
stop and report without guessing, repairing storage, adding a fallback or weakening
tests. Do not claim READY_FOR_REVIEW.

PREPARE completed at DRAFT_FOR_REVIEW with docs-only changes. The user subsequently
approved execution, including the explicit all-executable day predicate, metadata/latest/
exact snapshot agreement and distinct settlement ambiguity/storage-integrity semantics.
Status was set to APPROVED_FOR_CODEX and the exact Base/Branch/Allowed Files gate passed
before implementation.

## Execution completion

Implemented only the four new production/test paths above and updated the two docs.
Dedicated: 34 tests PASS. Related: 90 + 86 tests PASS. Full suite: 2,967 tests PASS.
No tests were skipped or assertions relaxed. Initial negative-test setup was corrected
to disable protective triggers only in deliberately corrupted isolated test databases;
production storage/validation was not changed to accommodate those tests.

The frozen static boundary search has no matches. Runtime no-network/clock/dependency
traps, SQLite authorizer/write checks, mode=ro byte-preservation checks and caller
connection-ownership tests pass. Existing unrelated tests emit unclosed-SQLite
ResourceWarnings, including when run in the related-only process; the new dedicated
process emits none. No warning suppression or existing-test modification was added.

git diff --check passes; all six changed/untracked paths are exactly Allowed Files and
the index is empty. The four untracked files were additionally whitespace-checked
without staging. No fixture/schema/migration/archive or existing production changes.
READY_FOR_REVIEW; no blockers, staging, commit, push or phase advancement.
