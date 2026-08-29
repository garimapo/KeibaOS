# Current Phase

Status: `READY_FOR_REVIEW`

## Identity and scope

- Phase: `4C-2d3b1i6d1d5f1c4i0`
- Name: `Exact Archived Historical Replay Application Composition PREPARE`
- Phase-family assignment: `C4I`, explicitly assigned by independent architecture
  review after completion of C4H; it is not claimed as a pre-existing hierarchy ID.
- Exact formal base: `8205dd860a61da916f0bd5cd38eb5d26ea0497a6`
- Formal branch: `feature/ver0.8-simulator`
- Review branch:
  `review/4c-2d3b1i6d1d5f1c4i0-historical-replay-application-prepare`
- Git setting: `core.autocrlf=true`; no Git configuration or attributes change is
  authorized.

Allowed changed files are exactly:

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

This phase is design only. It changes no production code, tests, schema, migration,
database, capture, or existing request/CLI behavior; performs no HTTP; and creates no
capture. C4H and the historical snapshot, planning, settlement acquisition, and final
settlement boundaries remain frozen.

## Purpose and frozen causal chain

C4I owns the missing deterministic, no-network application path from exact persisted
historical inputs to the final Ver0.8 settlement summary. The future application must:

1. load and validate the complete replay manifest;
2. exact-load every `HistoricalInputSnapshot` by natural identity;
3. validate complete one-to-one race coverage and freeze canonical order;
4. call `execute_and_persist_historical_bet_plans(...)` exactly once for the complete
   batch;
5. only after the whole planning call succeeds, derive each race's required payout
   types from its frozen returned/persisted plan;
6. call `acquire_and_persist_official_settlement_facts(...)` once per canonical race;
7. only after every acquisition call succeeds, call
   `execute_final_historical_settlement_simulation(...)` exactly once; and
8. return the exact `SimulationSummary` returned by that final boundary.

No settlement capture, result, or payout may be loaded or normalized before C4g1 has
completed for the entire batch. Settlement evidence therefore cannot influence
prediction, strategy, bet generation, allocation, plan persistence, or required
bet-type generation.

## Replay manifest policy

C4I introduces a distinct `HistoricalReplayRequestDocument` with its own
`schema_version=1`. It does not add a version or reinterpret the existing
`PersistedSimulationRequestDocument` schema-v1 `races` field. The legacy
`run_persisted_simulation_request` application and `run_persisted_simulation` CLI keep
their exact behavior.

The root JSON object has exactly these keys and no others:

```text
schema_version
database_path
capture_archives
run_context
strategy
budgets_by_race_id
races
```

There is no `pipeline` key, `track_reference_date`, `PredictionPipeline`, or
`PipelineConfig` in the document. C4g0 remains sole owner of per-race historical
pipeline construction through `build_historical_prediction_pipeline(...)`, using
exactly `snapshot.race.target_race_date` and
`strategy_identity.strategy_config`. C4i1 constructs no pipeline, and C4i2 passes no
caller pipeline to C4g1. The legacy schema-v1 request's existing `pipeline` field is
unchanged.

Exact root value contracts are:

- `schema_version`: exact non-bool integer `1`.
- `database_path`: exact non-empty, NUL-free string path. A relative value resolves
  against the replay manifest parent directory.
- `capture_archives`: exact object with allowed keys only `JRA/jra_official` and
  `NAR/nar_official`; at least one key is required. Each value is an exact non-empty,
  NUL-free path string resolved against the manifest parent when relative. Unused
  configured supported-provider archives are allowed, but every provider represented
  by a race must be configured. Provider is never inferred from path or capture ID.
- `run_context`: exact object with only `run_id`, `dataset_id`, `started_at`, and
  `target_commit_id`. The three IDs are exact non-empty strings; `started_at` is an
  ISO-8601 aware datetime string. Existing formal semantics produce an exact
  `SimulationRunContext`.
- `strategy`: exact existing RuleBased strategy object with only `strategy_name`,
  `allowed_bet_types`, `max_bet_count`, `selection_style`,
  `min_combination_score`, `max_candidates`, `sort_condition`, and
  `allocation_policy`. The allocation object has exactly `policy_name`,
  `policy_version`, and `parameters`; fixed-stake `parameters` has exactly
  `stake_amount`. Formal bet types remain exactly `単勝`, `馬連`, `ワイド`, and
  `3連複`. C4i1 constructs `StrategyConfig` and `AllocationPolicyConfig`, then uses
  the existing public identity builder to construct the exact `StrategyIdentity`.
  `strategy_name` is exactly `RuleBasedBetStrategy`; `allowed_bet_types` is an array
  of unique supported values; count fields are non-bool non-negative integers;
  `selection_style` is `box` or `formation`; `min_combination_score` is finite; and
  `sort_condition` uses the existing four formal values. The allocation policy is
  exactly `fixed_stake_per_recommendation`, version `1`, with a positive non-bool
  `stake_amount` multiple of 100. Settlement facts cannot influence this construction.
- `budgets_by_race_id`: exact object keyed by canonical positive ASCII integer strings.
  Each value is exactly `{"total_amount": value}`, where `value` is a non-bool,
  non-negative integer multiple of 100. The document stores the result as a frozen
  `Mapping[int, BetStakeBudget]`, with exact race-ID coverage.
- `races`: exact non-empty array of exact race objects.

Each race object has exactly:

```text
snapshot_identity
internal_race_id
settlement_information_cutoff
result_capture_id
payout_capture_catalog_by_bet_type
```

`snapshot_identity` is an exact object with only `dataset_id`, `organization`,
`source_system`, `external_race_id`, and `captured_at`. C4i1 constructs the existing
`HistoricalInputSnapshotIdentity`, with `organization/source_system` represented by
its exact source-identity value. Allowed pairs are only `JRA/jra_official` and
`NAR/nar_official`. `internal_race_id`, `source_url`, `information_cutoff`, and
`content_sha256` do not occur inside `snapshot_identity`. Its four text identity
values are exact non-empty strings and `captured_at` is an ISO-8601 aware datetime
string; construction applies the existing formal identity normalization.

`internal_race_id` is an exact non-bool positive integer used only as cross-check and
binding metadata. `settlement_information_cutoff` is an exact ISO-8601 aware datetime
string parsed to an aware `datetime`, with no current-time default. The same value is
later supplied to C4h4a and C4h4b. `result_capture_id` is an exact non-empty string;
C4i1 infers no provider semantics from it.

`payout_capture_catalog_by_bet_type` is an exact object whose only allowed keys are
`単勝`, `馬連`, `ワイド`, and `3連複`, with exact non-empty string values. It may be
empty. Required-type completeness is not checked before planning. Equal capture-ID
values are explicitly allowed: one exact capture may serve result normalization and
one or more payout types, and multiple payout keys may reference the same capture.
Only JSON object keys must remain unique through duplicate-key rejection.

Relative paths resolve against the manifest directory. JSON duplicate keys,
non-finite values, unknown or omitted schema keys, invalid exact types, empty required
identifiers, naive timestamps, duplicate natural snapshot identities, duplicate
internal race IDs, unsupported provider pairs, unsupported payout keys, and incoherent
cross-field coverage fail closed.

The manifest's input race order is not repository or execution identity. After every
snapshot is exact-loaded, the application validates each expected internal race ID
and freezes the existing formal canonical order `(scheduled_start_at,
internal_race_id)`. Budgets, cutoffs, and official evidence must cover exactly that
loaded race set.

## C4i1 public domain surface

Module-local `__all__` contains exactly:

```text
HistoricalReplayRequestValidationError
HistoricalReplayRaceRequest
HistoricalReplayRequestDocument
load_historical_replay_request_document
```

There is no package-root export. `HistoricalReplayRequestValidationError` subclasses
`ValueError` and owns only request JSON, schema, and document-domain validation.
Filesystem `OSError` from reading the request path propagates unchanged; no broad
exception hierarchy is introduced.

`HistoricalReplayRaceRequest` is frozen and slotted, with exactly:

```python
snapshot_identity: HistoricalInputSnapshotIdentity
internal_race_id: int
settlement_information_cutoff: datetime
result_capture_id: str
payout_capture_catalog_by_bet_type: Mapping[str, str]
```

`HistoricalReplayRequestDocument` is frozen and slotted, with exactly:

```python
schema_version: int
source_path: Path
database_path: Path
capture_archive_paths_by_provider: Mapping[str, Path]
run_context: SimulationRunContext
strategy_identity: StrategyIdentity
budgets_by_race_id: Mapping[int, BetStakeBudget]
races: tuple[HistoricalReplayRaceRequest, ...]
```

Both types defensively freeze their mappings and tuple contents. The document contains
no prediction pipeline/config, track-reference date, embedded prediction input,
result/payout domain object, or capture bytes.

Static cross-field validation requires a non-empty race tuple; unique snapshot natural
identities and internal race IDs; exact equality between budget race IDs and manifest
internal race IDs; `run_context.dataset_id` equality with every snapshot dataset ID;
only the two exact supported provider pairs; and an archive for every represented
provider. An unused configured supported archive and an empty payout catalog are
allowed. Capture-ID value reuse is allowed.

Input race order is preserved in the C4i1 document. C4i1 cannot sort by
`scheduled_start_at` because it does not load snapshots. Canonical execution order is
C4i2 responsibility after all exact snapshot loads.

C4i1 performs static request validation only. It does not open the main database or
capture archives, inspect capture existence/bytes, derive purchased bet types,
determine `NO_BET`, load snapshots, run planning or settlement, or consult a clock.
Capture availability and required payout-subset validation remain post-planning C4i2
responsibilities.

## Exact snapshot and plan policies

Every snapshot is loaded only through
`SQLiteHistoricalInputSnapshotRepository.load_snapshot_by_identity(identity=...)`.
`load_latest_snapshot`, race-only/cutoff-only lookup, database row order, and any
current-state/provider fallback are forbidden. A missing snapshot, returned identity
mismatch, duplicate loaded race, dataset/run-context mismatch, or internal-race-ID
cross-check mismatch fails before planning.

C4g1 receives the complete canonical snapshot tuple and exact budget mapping in one
call. Its returned `SimulationBetPlanSnapshot` values must have exact mutual race
coverage and identity with the loaded batch. Only those frozen plans determine
required payout types. C4I does not predict, regenerate, mutate, or independently
persist bets.

## Payout evidence catalog and NO_BET

The manifest catalog exists before planning and may contain supported payout capture
IDs that the final plan does not require. Such entries are
`ALLOWED_BUT_NOT_CONSUMED`: they are neither preloaded nor passed to C4h4a. After
planning, C4I takes the unique formal bet types from each frozen plan, requires every
one in that race's catalog, and constructs an exact required-type-only mapping.
Missing required evidence fails closed; capture availability never adds or removes a
required type.

An empty persisted plan still follows the uniform race path: C4h4a is called with the
exact result capture and an empty payout mapping. It performs no payout normalization.
Settlement evidence never decides `NO_BET`.

## Cutoff, provider, and archive ownership

Each race has exactly one aware settlement cutoff. The identical value is passed to
C4h4a as `settlement_information_cutoff` and to C4h4b in
`settlement_cutoffs_by_race_id`. It is never inferred from a clock, race time,
snapshot cutoff, capture metadata, or finalization time.

Provider dispatch comes only from the exact loaded snapshot pair:

```text
JRA / jra_official -> configured JRA archive
NAR / nar_official -> configured NAR archive
```

Capture ID prefixes, URLs, venue text, external-ID patterns, and archive searching are
not provider identity. Every provider represented in the loaded batch must have one
configured archive path. A configured supported-provider archive unused by the batch
is allowed but is not opened.

The future SQLite application runner owns:

- one writable main simulation connection;
- existing main-database migration application;
- the historical snapshot, plan snapshot/source, result, and payout repositories on
  that connection;
- at most one read-only JRA capture connection and one read-only NAR capture
  connection, opened only for represented providers;
- exact provider capture repository construction; and
- closing every connection it opens in reverse order in `finally`.

Capture archives must already carry their approved dedicated schemas. Replay opens
them read-only and does not apply capture migrations or write captures. The main and
archive databases are never joined with `ATTACH` and have no cross-database
transaction. The old SQLite composition root cannot be reused because it consumes
embedded race inputs and assumes settlement facts already exist; its lower-level
formal repositories and boundaries are reused instead.

## Failure, durability, and final output

`DURABLE_AUDITABLE_PREFIX_ALLOWED`: C4g1 plans and C4h4a results/publications already
committed before a later failure remain immutable and auditable. C4I stops immediately,
returns no final summary, performs no hidden retry or compensation, deletes nothing,
and does not claim global atomicity. C4i1 owns only its single request-validation
error; later application validation must remain narrow, and collaborator errors
propagate unchanged. A later identical retry may rely only on existing repository
idempotence/conflict contracts.

The user-facing result comes only from one successful C4h4b call after all
acquisition. C4I returns its exact `SimulationSummary` object and never exposes a
partial/as-of C4g2b summary as final. `SimulationResult` or selected-publication
run-audit persistence remains `OPTIONAL_POST_VER0_8`; C4g2c is not introduced.

## CLI and portable acceptance policy

C4I adds a separate `run_historical_replay` CLI and application entry point. The new
CLI owns only request-path argument handling, deterministic summary serialization,
stdout/stderr, and exit codes. It owns no snapshot selection, prediction, capture
selection/parsing, repository composition, or settlement. The existing schema-v1 CLI
and request path remain unchanged.

Portable acceptance uses committed, minimized, provenance-bound derived JRA and NAR
official structural capture fixtures, not developer-machine archive paths and not
manually inserted settlement-domain facts. Each fixture has deterministic extraction
metadata binding its source capture ID, canonical URL, original response SHA-256 and
observation time, extraction boundary/method, derived bytes SHA-256, encoding, and an
explicit derived-not-original statement. The derived bytes must retain every structure
used by the production result and payout normalizers and are loaded through the real
capture domains and SQLite archives.

Final acceptance requires one mixed-provider two-race replay containing at least one
complete JRA and one complete NAR race. It must prove exact snapshot persistence/load,
batch planning before any acquisition, frozen-plan consumption, provider-normalizer
creation of official result/payout facts, one shared per-race cutoff across write/read,
only `SETTLED`/`NO_BET` final states, exact investment/payout/profit/ROI, deterministic
equal summaries from equivalent fresh repository states, and fail-closed cases for a
missing snapshot, missing capture, after-cutoff capture, missing required payout
evidence, non-final settlement, and silent race skipping. Tests perform no network and
do not manually insert `PersistedRaceResult`, `PayoutPublication`, or `PayoutRecord`.

## Frozen decision matrix

```text
C4I_FAMILY_ASSIGNMENT:
EXPLICITLY_ASSIGNED_AFTER_C4H_COMPLETION

C4I_PURPOSE:
EXACT_ARCHIVED_HISTORICAL_REPLAY_APPLICATION_COMPOSITION

REPLAY_REQUEST_OR_MANIFEST_POLICY:
NEW_DISTINCT_HISTORICAL_REPLAY_REQUEST_DOCUMENT_SCHEMA_V1

EXISTING_SCHEMA_V1_COMPATIBILITY_POLICY:
LEGACY_PERSISTED_SIMULATION_REQUEST_AND_CLI_UNCHANGED

HISTORICAL_REPLAY_PIPELINE_POLICY:
NO_MANIFEST_PIPELINE_FIELD_C4G0_SOLE_HISTORICAL_PIPELINE_OWNER

ROOT_SCHEMA_KEYS:
schema_version; database_path; capture_archives; run_context; strategy; budgets_by_race_id; races

RACE_SCHEMA_KEYS:
snapshot_identity; internal_race_id; settlement_information_cutoff; result_capture_id; payout_capture_catalog_by_bet_type

C4I1_PUBLIC_SURFACE:
HistoricalReplayRequestValidationError; HistoricalReplayRaceRequest; HistoricalReplayRequestDocument; load_historical_replay_request_document

CAPTURE_ID_VALUE_REUSE_POLICY:
ALLOWED

EXACT_SNAPSHOT_IDENTITY_POLICY:
DATASET_ORGANIZATION_SOURCE_EXTERNAL_RACE_CAPTURED_AT_NATURAL_IDENTITY_WITH_INTERNAL_RACE_ID_CROSS_CHECK

SNAPSHOT_LOAD_POLICY:
EXACT_LOAD_ALL_BY_IDENTITY_BEFORE_PLANNING_NO_LATEST_OR_FALLBACK

PLANNING_BEFORE_SETTLEMENT_POLICY:
ONE_COMPLETE_C4G1_BATCH_MUST_SUCCEED_BEFORE_ANY_C4H4A_CALL

PAYOUT_EVIDENCE_CATALOG_POLICY:
PREPLANNING_CATALOG_UNUSED_SUPPORTED_ENTRIES_ALLOWED_BUT_NOT_CONSUMED

REQUIRED_PAYOUT_SUBSET_POLICY:
DERIVE_ONLY_FROM_FROZEN_PLANS_REQUIRE_COMPLETE_SUBSET_PASS_NO_EXTRA_KEYS

NO_BET_APPLICATION_POLICY:
CALL_C4H4A_WITH_EXACT_RESULT_CAPTURE_AND_EMPTY_PAYOUT_MAPPING

SETTLEMENT_CUTOFF_POLICY:
ONE_EXPLICIT_AWARE_CUTOFF_PER_RACE_IDENTICAL_FOR_C4H4A_AND_C4H4B

PROVIDER_DISPATCH_POLICY:
EXACT_LOADED_SNAPSHOT_SOURCE_IDENTITY_ONLY

JRA_ARCHIVE_OWNERSHIP:
RUNNER_OWNED_READ_ONLY_CONNECTION_OPENED_ONLY_WHEN_JRA_IS_REPRESENTED

NAR_ARCHIVE_OWNERSHIP:
RUNNER_OWNED_READ_ONLY_CONNECTION_OPENED_ONLY_WHEN_NAR_IS_REPRESENTED

MAIN_DATABASE_OWNERSHIP:
RUNNER_OWNED_WRITABLE_CONNECTION_WITH_EXISTING_MAIN_MIGRATIONS_AND_FORMAL_REPOSITORIES

CONNECTION_LIFETIME_POLICY:
APPLICATION_SCOPE_CLOSE_ALL_OWNED_CONNECTIONS_IN_REVERSE_ORDER_IN_FINALLY

DURABLE_PREFIX_POLICY:
DURABLE_AUDITABLE_PREFIX_ALLOWED_NO_GLOBAL_TRANSACTION_OR_COMPENSATION

ERROR_PROPAGATION_POLICY:
OWNED_VALIDATION_ERRORS_NARROW_COLLABORATOR_ERRORS_UNCHANGED_STOP_IMMEDIATELY

FINAL_SUMMARY_POLICY:
ONE_C4H4B_CALL_AFTER_ALL_ACQUISITION_RETURN_EXACT_FINAL_SIMULATION_SUMMARY_ONLY

CLI_APPLICATION_SPLIT:
SEPARATE_HISTORICAL_REPLAY_APPLICATION_AND_CLI_LEGACY_PATH_UNCHANGED

PORTABLE_CAPTURE_FIXTURE_POLICY:
MINIMIZED_PROVENANCE_BOUND_DERIVED_JRA_AND_NAR_STRUCTURAL_FIXTURES_AFTER_EVIDENCE_APPROVAL

FINAL_PROVIDER_ACCEPTANCE_COVERAGE:
ONE_MIXED_PROVIDER_TWO_RACE_REPLAY_WITH_AT_LEAST_ONE_COMPLETE_JRA_AND_ONE_COMPLETE_NAR_RACE

SIMULATION_RESULT_AUDIT_PERSISTENCE_STATUS:
OPTIONAL_POST_VER0_8

C4I0_ARCHITECTURE_STATUS:
READY_FOR_REVIEW

C4I1_IMPLEMENTATION_AUTHORIZATION:
NOT_YET_APPROVED

VER0_8_REMAINING_OPEN_CRITERIA:
DETERMINISTIC_FULL_RERUN; APPLICATION_COMPOSITION; FORMAL_HISTORICAL_REPLAY_EXECUTABLE_PATH; FULL_NO_NETWORK_OFFICIAL_SETTLEMENT_E2E
```

## C4I implementation split

The smallest reviewable sequence is:

1. `4C-2d3b1i6d1d5f1c4i1` — historical replay request document/domain and strict
   loader only.
   Prospective allowed files:
   `scripts/simulation/historical_replay_request_document.py`,
   `tests/test_historical_replay_request_document.py`, and the two phase docs.
2. `4C-2d3b1i6d1d5f1c4i2` — exact SQLite historical replay application composition,
   input assembly, connection/archive ownership, and the frozen C4g1 -> C4h4a -> C4h4b
   orchestration. Exact file scope must be prepared after C4i1 fixes the manifest type.
3. `4C-2d3b1i6d1d5f1c4i3a` — evidence-only freeze of portable derived JRA/NAR capture
   fixtures and manifests; no production implementation.
4. `4C-2d3b1i6d1d5f1c4i3b` — separate historical replay CLI plus mixed-provider
   no-network end-to-end acceptance closure using the approved portable fixtures.

The evidence-only step is separate because provenance-minimized official fixtures
must be independently approved before application acceptance code treats them as the
portable proof boundary.

## Gate disposition and next phase

Existing generic CLI availability is `PASS`. C4I must close the currently open:

```text
DETERMINISTIC_FULL_RERUN
APPLICATION_COMPOSITION
FORMAL_HISTORICAL_REPLAY_EXECUTABLE_PATH
FULL_NO_NETWORK_OFFICIAL_SETTLEMENT_E2E
```

There is no implementation blocker for the narrow C4i1 manifest/loader after
independent architecture approval. Portable derived fixture provenance remains a
later C4i3a approval gate, not a blocker to C4i1.

Recommended next phase:
`4C-2d3b1i6d1d5f1c4i1_HISTORICAL_REPLAY_REQUEST_DOCUMENT_AND_LOADER`.

Its allowed files should be exactly:

```text
scripts/simulation/historical_replay_request_document.py
tests/test_historical_replay_request_document.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Verification and stop condition

No pytest is required because only docs change. Verify exact formal remote head,
two-file scope, `git diff --check`, review branch ahead one/behind zero after commit,
and clean final status. Push only the review branch and stop for independent
architecture review. Do not implement C4i1.
