# Current Phase

Status: `READY_FOR_REVIEW`

## Identity and scope

- Phase: `4C-2d3b1i6d1d5f1c4i2`
- Name: `Exact SQLite Historical Replay Application Composition`
- Exact formal base/C4i1 formal commit:
  `523a59069a15108bee06347a29c49adb947737c6`
- Formal branch: `feature/ver0.8-simulator`
- Review branch:
  `review/4c-2d3b1i6d1d5f1c4i2-sqlite-historical-replay-application`
- C4i1 status: `FORMALLY_VERIFIED`
- Git setting: `core.autocrlf=true`; C4i2 changes no Git configuration or
  attributes.

Allowed changed files are exactly:

```text
scripts/simulation/historical_replay_request_application.py
scripts/simulation/sqlite_historical_replay_application.py
tests/test_historical_replay_request_application.py
tests/test_sqlite_historical_replay_application.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

C4i2 changes no existing production/test module, package export, legacy application,
CLI, repository, schema, or migration. It performs no HTTP, capture creation, capture
save, or C4i3 work. C4i3a and C4i3b are not started.

## C4i2 purpose and public surface

C4i2 composes the already-formal C4i1, C4g1, C4h4a, and C4h4b boundaries into one
deterministic SQLite historical replay application. It exact-loads all requested
historical snapshots, completes and validates one batch planning call before any
settlement-evidence access, opens only represented official archives read-only,
acquires official facts once per canonical race, and returns the exact final
`SimulationSummary` from one C4h4b call.

The exact two-module public surface is:

```python
# scripts/simulation/historical_replay_request_application.py
run_historical_replay_request(
    *,
    request_path: str | Path,
) -> SimulationSummary

# scripts/simulation/sqlite_historical_replay_application.py
class SQLiteHistoricalReplayApplicationError(ValueError): ...

run_sqlite_historical_replay(
    *,
    document: HistoricalReplayRequestDocument,
) -> SimulationSummary
```

The request module's module-local `__all__` contains only
`run_historical_replay_request`. The SQLite module's module-local `__all__` contains
only `SQLiteHistoricalReplayApplicationError` and
`run_sqlite_historical_replay`. Nothing is exported from the simulation package root.
No third production module, orchestration protocol, or repository protocol is needed:
private, dependency-patchable helpers in the SQLite runner preserve causal testability
without widening the public architecture.

`run_historical_replay_request` calls
`load_historical_replay_request_document(request_path=request_path)` exactly once,
passes that exact returned document once as
`run_sqlite_historical_replay(document=document)`, and returns the exact runner result.
It owns no SQLite/repository/snapshot/planning/capture/settlement logic, clock access,
or exception translation. C4i1 validation errors and native filesystem `OSError`
propagate unchanged. The legacy `run_persisted_simulation_request` path is unchanged.

The SQLite runner validates `type(document) is HistoricalReplayRequestDocument`
before opening a connection. Its sole owned error is
`SQLiteHistoricalReplayApplicationError(ValueError)`. It owns only dynamic
contradictions detected by C4i2 itself: missing or mismatched exact snapshots,
incoherent returned plan coverage, missing required payout-catalog evidence,
unsupported/dynamically contradictory provider binding, and failure of the required
read-only safety verification. A missing snapshot is not assigned a speculative
separate unavailable hierarchy. Request, SQLite open/migration/repository, C4g1,
C4h4a, and C4h4b exceptions propagate unchanged; C4i2 does not broadly catch and
translate collaborator failures.

## Main SQLite ownership and exact snapshot phase

The runner owns exactly one writable main connection opened from
`document.database_path`. It calls `apply_migrations(connection)` exactly once and
closes the connection on every success or failure. It uses no second main connection,
`ATTACH`, global transaction, cross-database transaction, new migration, or repository
change.

After migration, it first constructs on that same connection only:

```text
SQLiteHistoricalInputSnapshotRepository
SQLiteSimulationBetPlanSnapshotRepository
```

The same plan repository object is later supplied as C4g1 `snapshot_repository` and
as the C4h4a/C4h4b `bet_plan_snapshot_source`. Result and payout repository objects
are deliberately not constructed until the complete planning and payout-subset
preflight barrier has succeeded; this makes the no-settlement-access-before-planning
policy physical as well as logical.

For each `HistoricalReplayRaceRequest`, in manifest order, C4i2 calls exactly:

```python
snapshot_repository.load_snapshot_by_identity(
    identity=race_request.snapshot_identity,
)
```

once. It never uses latest, race-only, cutoff, row-order, or provider fallback. It
fails fast before C4g1 if a value is absent or is not an exact
`HistoricalInputSnapshot`, or if its identity, internal race ID, dataset ID, or
uniqueness disagrees with the request/document binding. Specifically, the loaded
identity must equal the requested identity, `snapshot.internal_race_id` must equal the
request cross-check, `snapshot.identity.dataset_id` must equal
`document.run_context.dataset_id`, and loaded internal race IDs must remain unique.
Nothing is repaired or substituted.

Only after every load succeeds, snapshots are sorted exactly by:

```python
(
    snapshot.race.scheduled_start_at,
    snapshot.internal_race_id,
)
```

The runner builds a race-ID keyed mapping from each canonical loaded snapshot to its
exact original race request. Manifest order, provider order, and repository row order
never control execution order.

## Planning barrier, returned plans, and payout subset

Before the complete C4g1 call succeeds, C4i2 does not open an official archive,
construct a capture/result/payout repository, load or inspect a capture, test capture
existence, derive required payout types, call C4h4a/C4h4b, or read settlement facts.
Only the main connection, migrations, exact historical snapshot loads, and plan
persistence infrastructure are available.

C4i2 calls `execute_and_persist_historical_bet_plans(...)` exactly once with:

```text
snapshots = complete canonical loaded tuple
run_context = document.run_context (same object)
strategy_identity = document.strategy_identity (same object)
budgets_by_race_id = document.budgets_by_race_id
snapshot_repository = the one shared SQLite plan repository
```

There is no per-race C4g1 call, pipeline construction, prediction outside C4g1, or
settlement access during planning. A C4g1 exception propagates unchanged, leaves zero
archive opens and zero C4h4a/C4h4b calls, and does not roll back an already-durable
C4g1 prefix.

Before archive opening, C4i2 requires the C4g1 result to be an exact tuple in canonical
race order with one exact `SimulationBetPlanSnapshot` per loaded snapshot. Length,
position, and race coverage must be exact; no duplicate, missing, or extra race is
allowed. For every paired plan/snapshot, the plan identity must equal the expected
formal binding field-by-field:

```text
run_id = document.run_context.run_id
race_id = snapshot.internal_race_id
strategy_id = document.strategy_identity.strategy_id
strategy_config_hash = document.strategy_identity.strategy_config_hash
information_cutoff = snapshot.information_cutoff
```

This is the smallest C4i2 coverage check: the existing
`SimulationBetPlanSnapshot` domain remains owner of its policy, budget, bet, stake,
and internal bet/identity invariants. C4i2 neither reloads nor replaces a returned
plan to repair incoherence. The shared persisted repository remains authoritative to
C4h4a/C4h4b.

Only after the complete returned batch passes does C4i2 derive each race's required
payout types from `plan.bets`, as unique `bet.bet_type` values in first-occurrence
order. Catalog keys, strategy allowed types, archive metadata, capture existence, and
official page content never create a required type.

Before any archive opens, every canonical race is preflighted. Each required type must
exist in that original race request's `payout_capture_catalog_by_bet_type`. C4i2 builds
a new insertion-ordered mapping containing all and only required types. Unused
supported catalog keys are `ALLOWED_BUT_NOT_CONSUMED`. Any missing required entry
raises `SQLiteHistoricalReplayApplicationError` before archive/repository acquisition
and before any settlement write.

A zero-bet plan has an empty required tuple and exact empty payout mapping. It remains
in the acquisition loop and still calls C4h4a with the request's exact result capture.
It is never skipped and settlement evidence never determines `NO_BET`.

## Provider binding and hard read-only archives

Represented providers are determined only from the exact loaded snapshot source pair:

```text
JRA / jra_official -> JRA/jra_official
NAR / nar_official -> NAR/nar_official
```

Capture ID, URL, path, venue, and external-ID shape are forbidden provider sources.
Any unsupported pair or missing matching configured path after exact load is a dynamic
application contradiction. Provider open order is deterministic first occurrence in
canonical race order.

Only after snapshot loading, canonicalization, C4g1 success, returned-plan validation,
and whole-batch payout-subset preflight does C4i2 construct, on the main connection:

```text
SQLiteRaceResultRepository
SQLitePayoutRepository
```

The exact same objects are used by every C4h4a call and the final C4h4b call.

Then all and only represented provider archives are opened successfully before the
first C4h4a call. A configured but unrepresented archive is never opened. For each
stored archive `Path`, C4i2 derives an opening-only URI without changing the document
field:

```python
archive_uri = archive_path.absolute().as_uri() + "?mode=ro"
connection = sqlite3.connect(archive_uri, uri=True)
```

`Path.absolute()` anchors any remaining relative spelling without resolving symlinks;
`Path.as_uri()` supplies the required absolute `file:` form and percent-encodes Windows
drive paths, spaces, `#`, `?`, `%`, and other URI-reserved path characters. The sole
query component is `mode=ro`. SQLite therefore enforces read-only at open time, and a
missing archive fails without creating a file. C4i2 does not mutate the stored `Path`,
open a normal writable fallback, retry another path/provider, or apply archive
migrations.

Immediately after each archive open, C4i2 executes `PRAGMA query_only=ON` and requires
`PRAGMA query_only` to report integer `1` as a secondary defense. This does not replace
`mode=ro`. It then constructs exactly
`SQLiteJRAOfficialResponseCaptureRepository` or
`SQLiteNAROfficialResponseCaptureRepository` for that provider. C4i2 never calls
`load_capture` or any capture save method; C4h4a owns the first capture-byte access.
There is no archive search or cross-provider fallback.

## Acquisition, final settlement, and connection closure

After all represented archive connections and repositories are ready, C4i2 iterates
the canonical races exactly once and calls
`acquire_and_persist_official_settlement_facts(...)` exactly once per race with the
exact snapshot, document run/strategy values, request cutoff/result capture,
required-only payout mapping, provider-selected archive repository, and shared
plan/result/payout repositories. Its return is not used to bypass later repository
reads. C4i2 performs no provider normalization, persistence, or settlement arithmetic.

The first C4h4a failure propagates unchanged, stops all later race acquisition, and
prevents C4h4b. Previously committed immutable facts remain durable; there is no retry,
compensation, deletion, or rollback across calls.

C4i2 creates exactly one insertion-ordered cutoff mapping covering every canonical
internal race ID with the unchanged corresponding
`HistoricalReplayRaceRequest.settlement_information_cutoff`. The same cutoff supplied
to each race's C4h4a is supplied to C4h4b. It is not normalized to another semantic
time or derived from snapshot/capture/race/clock data.

Only after all C4h4a calls succeed, C4i2 calls
`execute_final_historical_settlement_simulation(...)` exactly once with the complete
canonical snapshots, exact document run/strategy values, complete cutoff mapping, and
the same shared plan/result/payout repositories. It returns that exact
`SimulationSummary`; it does not reconstruct metrics, calculate ROI, wrap the result,
or call C4g2b directly as the user-facing final boundary.

Every owned connection is registered in actual open order and closure is attempted in
strict reverse order, so archives close before the main connection. All closes are
attempted on success and failure. When an application/collaborator exception is
already active, cleanup errors are retained only as diagnostic context and cannot
replace that primary exception. When there is no primary error, all closes are still
attempted and the first close error is propagated after cleanup. No caller-owned
connection exists in either public API.

`DURABLE_AUDITABLE_PREFIX_ALLOWED` remains frozen. There is no global transaction over
C4g1 + C4h4a + C4h4b, no rollback or DELETE compensation for committed immutable
facts, no hidden retry, and no summary on failure. An identical later replay relies
only on existing repository idempotence/conflict behavior.

C4i2 uses no current clock (`datetime.now`, `datetime.utcnow`, `time.time`, or
equivalent), creates no `completed_at`, and introduces no C4g2c, run-result table,
manifest persistence, selected-publication persistence, or new audit schema. C4g2c
remains `OPTIONAL_POST_VER0_8`.

## Implemented scope and test policy

C4i2 implementation is limited exactly to:

```text
scripts/simulation/historical_replay_request_application.py
scripts/simulation/sqlite_historical_replay_application.py
tests/test_historical_replay_request_application.py
tests/test_sqlite_historical_replay_application.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

It must not modify C4i1, C4g1, C4h4a, C4h4b, repositories, migrations, legacy
request/application paths, CLI/main, or package exports.

Dedicated tests must pin exact public surfaces/types, request-wrapper call/identity
behavior, one main connection/migration and shared repository identities, exact
snapshot-by-identity loading and fail-fast bindings, canonical order, the complete
planning barrier, returned-plan exact coverage/identity, plan-only required-type
derivation, whole-batch subset preflight, uniform `NO_BET`, provider binding, exact
read-only URI/query-only safety (including Windows paths/reserved characters and
missing-file no-create), all-required-archives-before-acquisition, reverse closure and
primary-error precedence, one C4h4a per canonical race, stop-on-first-failure, one
C4h4b after complete acquisition, exact summary identity, collaborator exception
propagation, durable-prefix behavior, and static ownership exclusions. Tests use
injection/patching and synthetic SQLite state only; they do not claim the later real
mixed-provider official-fixture E2E.

Static checks forbid HTTP, capture save/discovery/latest lookup, `PredictionPipeline`,
bet regeneration, settlement arithmetic, current clock, `ATTACH`, global transaction,
CLI or legacy changes, package export, schema/migration changes, and a third
orchestration module/protocol.

## Future AI signal architecture

```text
FUTURE_AI_SIGNAL_ARCHITECTURE:
OPTIONAL_AUDITABLE_AUGMENTATION_AFTER_VER0_8

AI_SIGNAL_USAGE:
DISABLED

AI_SIGNAL_USAGE_BASELINE:
DISABLED

CURRENT_C4I2_AI_EFFECT:
NONE
```

The deterministic KeibaOS baseline remains executable with AI signal usage disabled.
Any future AI/LLM layer is an optional external prediction signal, never an
authoritative replacement for the deterministic prediction/replay pipeline. A future
controlled comparison must retain both a deterministic-only `BASELINE` and an
`AI_AUGMENTED` path using that same deterministic prediction plus explicitly enabled
signals.

Future signals must be independently auditable, eventually recording provider, model
identity/version where available, prompt/config identity, exact causal input identity,
generated/observed timestamp, and prediction/evaluation output. They must obey no
future information, no hindsight, and no backdated AI output. A signal receives
non-zero prediction influence only after separate historical and out-of-sample
validation demonstrates useful incremental performance, never merely because an output
appears plausible. AI usage must remain explicitly switchable so deterministic replay
is reproducible without external AI/API availability.

This is future extensibility documentation only. C4i2 adds no OpenAI/LLM/API client,
prompt, model setting, external prediction call, AI schema/migration/persistence,
weighting, or AI fixture.

## C4i2/C4i3 boundary and disposition

C4i2 closes `DETERMINISTIC_FULL_RERUN` application composition at the Python boundary
and `APPLICATION_COMPOSITION`. It does not close
`FORMAL_HISTORICAL_REPLAY_EXECUTABLE_PATH` (C4i3b CLI) or
`FULL_NO_NETWORK_OFFICIAL_SETTLEMENT_E2E` (portable fixture evidence in C4i3a and
mixed-provider acceptance in C4i3b).

C4i3a remains evidence/provenance freeze only for portable derived official fixtures.
C4i3b remains the separate CLI plus mixed-provider full no-network E2E. Neither is
started here.

```text
C4I1:
FORMALLY_VERIFIED

C4I2_PUBLIC_SURFACE:
run_historical_replay_request; SQLiteHistoricalReplayApplicationError; run_sqlite_historical_replay

C4I2_MODULE_SPLIT:
TWO_MODULE_REQUEST_WRAPPER_AND_SQLITE_RUNNER_NO_THIRD_ORCHESTRATION_MODULE

REQUEST_WRAPPER_POLICY:
ONE_C4I1_LOAD_ONE_SQLITE_RUNNER_CALL_EXACT_DOCUMENT_AND_SUMMARY_IDENTITY

MAIN_SQLITE_CONNECTION_POLICY:
ONE_RUNNER_OWNED_WRITABLE_CONNECTION_CLOSED_ON_ALL_PATHS

MAIN_MIGRATION_POLICY:
APPLY_EXISTING_MIGRATIONS_EXACTLY_ONCE

MAIN_REPOSITORY_COMPOSITION:
ONE_SHARED_SNAPSHOT_REPOSITORY_ONE_SHARED_PLAN_REPOSITORY_THEN_POST_BARRIER_SHARED_RESULT_AND_PAYOUT_REPOSITORIES

EXACT_SNAPSHOT_LOAD_POLICY:
ONE_LOAD_BY_EXACT_NATURAL_IDENTITY_PER_REQUEST_NO_LATEST_OR_FALLBACK

DYNAMIC_SNAPSHOT_BINDING_VALIDATION:
EXACT_TYPE_IDENTITY_INTERNAL_RACE_DATASET_AND_UNIQUENESS_FAIL_FAST

CANONICAL_ORDER_POLICY:
SCHEDULED_START_AT_THEN_INTERNAL_RACE_ID_AFTER_ALL_EXACT_LOADS

PLANNING_BARRIER_POLICY:
NO_SETTLEMENT_REPOSITORY_OR_ARCHIVE_ACCESS_BEFORE_COMPLETE_C4G1_SUCCESS_AND_PLAN_PREFLIGHT

C4G1_CALL_POLICY:
ONE_COMPLETE_CANONICAL_BATCH_CALL

PLAN_BATCH_COVERAGE_POLICY:
EXACT_TUPLE_CANONICAL_POSITION_AND_RUN_RACE_STRATEGY_HASH_INFORMATION_CUTOFF_IDENTITY

REQUIRED_PAYOUT_TYPE_POLICY:
UNIQUE_FIRST_OCCURRENCE_FROM_RETURNED_FROZEN_PLAN_BETS_ONLY

PAYOUT_SUBSET_PREFLIGHT_POLICY:
ALL_RACES_REQUIRED_ONLY_SUBSETS_COMPLETE_BEFORE_ANY_ARCHIVE_OPEN_UNUSED_KEYS_NOT_CONSUMED

NO_BET_POLICY:
C4H4A_STILL_CALLED_WITH_EXACT_RESULT_CAPTURE_AND_EMPTY_PAYOUT_MAPPING

ARCHIVE_OPEN_TIMING_POLICY:
ALL_REPRESENTED_ARCHIVES_AFTER_PLANNING_PREFLIGHT_AND_BEFORE_FIRST_C4H4A

ARCHIVE_READ_ONLY_OPEN_POLICY:
PATH_ABSOLUTE_AS_URI_PLUS_MODE_RO_URI_TRUE_WITH_VERIFIED_QUERY_ONLY_SECONDARY_DEFENSE

QUERY_ONLY_POLICY:
VERIFIED_SECONDARY_DEFENSE

JRA_ARCHIVE_REPOSITORY_POLICY:
ONE_SQLITE_JRA_CAPTURE_REPOSITORY_ON_REPRESENTED_READ_ONLY_CONNECTION

NAR_ARCHIVE_REPOSITORY_POLICY:
ONE_SQLITE_NAR_CAPTURE_REPOSITORY_ON_REPRESENTED_READ_ONLY_CONNECTION

PROVIDER_BINDING_POLICY:
EXACT_LOADED_SNAPSHOT_SOURCE_PAIR_ONLY_NO_CAPTURE_PATH_OR_ID_INFERENCE

C4H4A_CALL_POLICY:
EXACTLY_ONCE_PER_CANONICAL_RACE_STOP_ON_FIRST_FAILURE

SETTLEMENT_CUTOFF_MAP_POLICY:
EXACT_COMPLETE_REQUEST_CUTOFF_MAPPING_SHARED_WITH_C4H4A_AND_C4H4B

C4H4B_CALL_POLICY:
EXACTLY_ONCE_AFTER_ALL_ACQUISITION_RETURN_EXACT_SUMMARY

CONNECTION_CLOSE_POLICY:
ATTEMPT_ALL_IN_REVERSE_OPEN_ORDER_PRIMARY_ERROR_WINS_OTHERWISE_FIRST_CLOSE_ERROR

DURABLE_PREFIX_POLICY:
DURABLE_AUDITABLE_PREFIX_ALLOWED_NO_GLOBAL_TRANSACTION_COMPENSATION_OR_RETRY

C4I2_ERROR_SURFACE:
SQLITE_HISTORICAL_REPLAY_APPLICATION_ERROR_VALUE_ERROR_SINGLE_OWNED_DYNAMIC_CONTRADICTION_TYPE

COLLABORATOR_ERROR_PROPAGATION:
UNCHANGED

CURRENT_CLOCK_POLICY:
FORBIDDEN

C4G2C_STATUS:
OPTIONAL_POST_VER0_8

C4I2_TEST_POLICY:
INJECTED_ORCHESTRATION_AND_SQLITE_OWNERSHIP_TESTS_NO_REAL_OFFICIAL_FIXTURE_E2E

C4I2_IMPLEMENTATION_ALLOWED_FILES:
scripts/simulation/historical_replay_request_application.py; scripts/simulation/sqlite_historical_replay_application.py; tests/test_historical_replay_request_application.py; tests/test_sqlite_historical_replay_application.py; docs/CURRENT_PHASE.md; docs/LATEST_CODEX_REPORT.md

C4I3A_BOUNDARY:
PORTABLE_DERIVED_OFFICIAL_FIXTURE_EVIDENCE_AND_PROVENANCE_ONLY

C4I3B_BOUNDARY:
SEPARATE_CLI_AND_MIXED_PROVIDER_FULL_NO_NETWORK_E2E

IMPLEMENTATION_BLOCKERS:
NONE

RECOMMENDED_NEXT_PHASE:
INDEPENDENT_C4I2_IMPLEMENTATION_REVIEW_THEN_C4I3A_PORTABLE_FIXTURE_EVIDENCE_PREPARE

C4I2_IMPLEMENTATION_STATUS:
READY_FOR_REVIEW
```

Stop for independent ChatGPT implementation review. Do not formal-integrate or begin
C4i3a/C4i3b.
