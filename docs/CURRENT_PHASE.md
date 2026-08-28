# Current Phase

Status: `DRAFT_FOR_REVIEW`

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

The new immutable manifest contains only direct consumers:

- `schema_version`;
- main simulation `database_path`;
- provider-keyed capture archive paths for `JRA/jra_official` and/or
  `NAR/nar_official`;
- `run_context`, `strategy`, and `pipeline` configuration material;
- `budgets_by_race_id`;
- an ordered non-empty race array, each item containing:
  - exact natural `snapshot_identity`: `dataset_id`, `organization`,
    `source_system`, `external_race_id`, and aware `captured_at`;
  - expected `internal_race_id` as a mandatory cross-check and binding key, never as
    a replacement lookup identity;
  - one aware `settlement_information_cutoff`;
  - one exact `result_capture_id`; and
  - a provider bet-type-to-exact-capture-ID payout evidence catalog.

Relative paths resolve against the manifest directory. JSON duplicate keys,
non-finite values, unknown root/race keys, empty identifiers, naive timestamps,
duplicate natural snapshot identities, duplicate internal race IDs, unsupported
provider identities, duplicate payout keys, and incoherent coverage fail closed.

The manifest's input race order is not repository or execution identity. After every
snapshot is exact-loaded, the application validates each expected internal race ID
and freezes the existing formal canonical order `(scheduled_start_at,
internal_race_id)`. Budgets, cutoffs, and official evidence must cover exactly that
loaded race set.

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
and does not claim global atomicity. Owned manifest/application validation uses a
narrow C4I error hierarchy; collaborator errors propagate unchanged. A later identical
retry may rely only on existing repository idempotence/conflict contracts.

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

## C4I implementation split

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
