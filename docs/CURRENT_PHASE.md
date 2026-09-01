# Current Phase

Status: `APPROVED_FOR_COMMIT`

## Identity and authority

- Phase: `POST_V0_8_DAILY_REPLAY_1`
- Name: `Post-Ver0.8 Daily Historical Replay Orchestration Design`
- Base Commit: `c08bedb5421b44d63a8bac017699efffca2a4b73`
- Branch: `feature/post-v0.8-daily-replay`
- Release baseline: `v0.8.0`
- Phase type: `DESIGN_ONLY`
- Production implementation: `NOT_AUTHORIZED`
- Test implementation: `NOT_AUTHORIZED`
- Stage / commit / push: `AUTHORIZED_FOR_THIS_DESIGN_COMMIT_ONLY`
- Release/tag/history mutation: `FORBIDDEN`

This design is prepared in the fresh clone
`C:\Users\garim\Desktop\KeibaOS-post-v0.8`. The old Ver0.8 working repository is
outside this phase and must remain unchanged.

ChatGPT independent design review approved this phase only after the corrections frozen
below. `APPROVED_FOR_CODEX` approves the design document. It does not authorize any
production code, test, migration, CLI, schema, database, archive, stage, commit, push,
or subsequent phase.

## Verified baseline

Before branch creation the fresh clone passed every required gate:

```text
CURRENT_BRANCH: master
HEAD: c08bedb5421b44d63a8bac017699efffca2a4b73
ORIGIN_MASTER: c08bedb5421b44d63a8bac017699efffca2a4b73
GIT_STATUS_SHORT: CLEAN
GIT_DIFF_CHECK: PASS
V0_8_0_TAG: PRESENT
```

The feature branch was created directly from that exact baseline.

## Objective

Design the boundaries required to replay one audited historical day without changing
the Ver0.8 engine. An eventual daily flow must:

1. receive an audited, complete target set for one exact date and closed provider scope;
2. reconcile each canonical provider race to persisted internal identity;
3. resolve one exact existing prediction snapshot and exact official settlement
   evidence for every executable target;
4. classify every target without silently removing denominator members;
5. generate and freeze one real existing schema-v1 manifest artifact;
6. load that artifact through the existing request loader; and
7. delegate the complete executable projection once to
   `run_sqlite_historical_replay`.

This phase designs those responsibilities and their future decomposition. It implements
none of them.

## Mandatory principles

```text
NO_FUTURE_LEAKAGE
NO_HINDSIGHT
FAIL_CLOSED
NO_SILENT_FALLBACK
NO_HIDDEN_SKIP
NO_CURRENT_CLOCK_CAUSALITY
DETERMINISTIC_ORDERING
EXACT_PROVIDER_AND_RACE_IDENTITY
AUDITED_COMPLETE_TARGET_SET
EXISTING_REPLAY_ENGINE_REUSE
NO_DUPLICATE_PREDICTION_OR_SETTLEMENT_LOGIC
NO_RAW_HTML_REPARSE_WHERE_A_FORMAL_DOMAIN_EXISTS
NO_VER0_8_CONTRACT_CHANGE_FOR_CONVENIENCE
```

`SimulationSummary.race_count` remains the formal Ver0.8 summary field. This design
does not add `target_race_count` to `SimulationSummary` and does not change its
meaning.

## Existing replay boundary

The implemented Ver0.8 flow is:

```text
run_historical_replay_request(request_path)
  -> load_historical_replay_request_document(request_path)
  -> run_sqlite_historical_replay(document)
  -> execute_and_persist_historical_bet_plans(all canonical snapshots)
  -> acquire_and_persist_official_settlement_facts(each canonical race)
  -> execute_final_historical_settlement_simulation(all canonical snapshots)
  -> SimulationSummary
```

There is no `SQLiteHistoricalReplayApplication` class. The application boundary is
`run_sqlite_historical_replay`. It already exact-loads all manifest snapshots,
canonicalizes by `(scheduled_start_at, internal_race_id)`, performs one multi-race
planning batch, derives required payout types from frozen plans, acquires official
facts, and performs one final settlement pass.

The future daily orchestrator must call `run_sqlite_historical_replay` exactly once
for the complete executable projection. It must not call the prediction pipeline, bet
generator, strategy, allocator, provider normalizers, or settlement engine directly.
It must not run a per-race retry/replay loop.

## Audited daily target-set boundary

### Legacy races table is not completeness evidence

The legacy `races` table is a population of races already persisted in one database.
It contains no day-level evidence proving that all provider races for a requested date
and scope were acquired.

Therefore:

- `races` may be used for persisted candidate lookup and internal race identity
  reconciliation;
- `races` must not be treated as the authoritative complete daily denominator;
- absence of a row must not be interpreted as proof that a provider race did not exist;
- a partial database population must not be presented as a complete daily target set;
  and
- daily ROI or total race count must not be reported as a full-day result unless target
  completeness is independently proven.

The existing `get_all_races()` and `get_race_id(Race)` helpers are also unsuitable
as completeness APIs. They neither carry day-level provenance nor prove provider-wide
coverage.

### DailyHistoricalReplayTargetSet

A new immutable, frozen/slotted domain value is necessary:

```text
DailyHistoricalReplayTargetSet
```

It must contain at least:

```text
target_date
closed provider_scope
canonical target_races, each with formal scheduled_start_at
completeness provenance/evidence identity
deterministic target order
```

The value asserts that its canonical race tuple is the audited complete target
population for the exact date and provider scope. Construction must validate exact
provider/race identity, uniqueness, canonical ordering, and a non-empty formal
completeness evidence identity. It must not infer completeness from local row count,
race-number continuity, venue expectations, current provider pages, or the current
clock.

If no trustworthy complete target set is supplied or its completeness evidence cannot
be validated, the whole daily operation fails closed with:

```text
TARGET_DISCOVERY_INCOMPLETE
```

No partial target tuple, schema-v1 manifest, runner call, `DailyHistoricalReplayResult`,
daily ROI, or full-day total is produced in that state.

Actual provider historical daily race discovery, acquisition of completeness evidence,
and construction/persistence of this target set belong to the separate future phase
`Historical Daily Target Discovery / Completeness`. They are not designed in detail
or implemented by this phase.

### Full-day reporting qualification

An audited complete target set proves the denominator only. If one or more targets are
`MISSING_EVIDENCE`, `UNSUPPORTED`, or `INVALID`, any Ver0.8
`SimulationSummary` covers only the executable projection. It must not be labeled a
complete full-day ROI or complete full-day replay result.

A result may be described as a successful full-day replay only when:

1. the target set is audited complete;
2. every canonical target is `EXECUTABLE`;
3. the one multi-race runner invocation succeeds; and
4. the returned summary covers that exact executable tuple.

Reporting and cumulative metric semantics remain future phases.

## Request document and real schema-v1 artifact

`HistoricalReplayRequestDocument` schema v1 is the unchanged strict execution
contract. It requires a non-empty race tuple, exact snapshot identities, exact internal
race-ID cross-checks, explicit budgets, exact result/payout capture IDs, explicit
settlement cutoffs, and a real `source_path`.

The earlier in-memory-only construction proposal is rejected. A synthetic or
non-existent `source_path` is forbidden.

The formal future flow is:

```text
audited DailyHistoricalReplayTargetSet
  -> identity/evidence resolution and complete outcome classification
  -> executable projection
  -> deterministic existing schema-v1 manifest artifact generation
  -> freeze the real artifact before execution
  -> load_historical_replay_request_document(real manifest path)
  -> run_sqlite_historical_replay(exact loaded document)
```

The generated artifact:

- uses existing schema version integer `1` without adding or changing JSON keys;
- is a real UTF-8 file retained for audit and exact rerun;
- deterministically serializes the frozen inputs and executable order;
- exists before the request loader is called;
- is not mutated after freeze; and
- yields a document whose `source_path` points to that exact existing file.

The future manifest builder must not bypass
`load_historical_replay_request_document`, and the orchestrator must pass the exact
loaded document to `run_sqlite_historical_replay`.

If the executable projection is empty, no manifest is generated, the loader is not
called, and the runner is not called. The complete classified target outcome tuple is
still retained in the successful zero-executable daily result.

Manifest-builder path policy, immutable write/conflict semantics, and exact
serialization tests belong to the separate future
`Existing Schema-v1 Manifest Builder` phase. No new JSON schema is authorized.

## HistoricalInputSnapshot resolution

### Existing capability

`HistoricalInputSnapshotSource.load_latest_snapshot` accepts exact dataset, race,
provider identity, and caller cutoff. The SQLite repository also provides
`load_snapshot_by_identity`, which reconstructs and validates the exact formal domain
required by schema v1. Neither API owns audited daily target discovery.

The formal snapshot domain already proves:

```text
captured_at <= prediction information_cutoff <= scheduled_start_at
```

and validates target entries plus provenance observation/availability causality.

### Initial policy: LATEST_CAUSAL_IN_DATASET

The initial daily snapshot-selection policy is explicitly named:

```text
LATEST_CAUSAL_IN_DATASET
```

Its explicit selection upper bound is the formal scheduled start retained by the
audited target:

```text
selection_upper_bound = audited_target.scheduled_start_at
```

Only candidates satisfying all of the following are eligible:

- exact `dataset_id`;
- exact provider identity;
- exact canonical provider race identity;
- exact reconciled internal race identity;
- snapshot `target_race_date == DailyHistoricalReplayTargetSet.target_date`;
- `captured_at <= selection_upper_bound`;
- snapshot `information_cutoff <= selection_upper_bound`; and
- all formal snapshot causal and schema invariants.

Among eligible candidates, choose the unique greatest `captured_at`. An equal greatest
capture instant is ambiguous and must not be broken by row ID, digest, insertion order,
or implicit SQLite order.

Current time, daily run `started_at`, settlement cutoff, database insertion time,
archive observation/storage time, and any unbounded-latest query are forbidden as the
snapshot selection upper bound.

Metadata may identify the candidate natural identity, but after selection the resolver
must call the existing repository's exact-identity loader. The returned exact
`HistoricalInputSnapshot` domain value must be revalidated against target set,
provider, dataset, race, date, and selected identity. Raw SQLite rows must never be used
to reimplement or partially reconstruct the snapshot domain.

The selected exact `HistoricalInputSnapshotIdentity` is frozen into the generated
schema-v1 manifest.

`LATEST_CAUSAL_IN_DATASET` means only the latest causal snapshot in the exact dataset
which existed no later than the audited `scheduled_start_at`. It is not a fixed
lead-time prediction policy. A future policy such as
`scheduled_start_at - N minutes` requires a separate formal design phase, causal
contract, and approval.

The future Evidence Resolver phase must verify that this policy is compatible with the
existing
`load_latest_snapshot(..., information_cutoff=selection_upper_bound, ...)` contract,
including its two inclusive cutoff predicates. It must not bypass that repository
merely to reconstruct a snapshot from raw rows. If unique-greatest ambiguity detection
cannot be reconciled with the existing repository contract, that phase must stop and
return to ChatGPT review; it must not guess or change the repository contract.

Missing eligible snapshot is target-scoped `MISSING_EVIDENCE` only when identity and
repository integrity remain trustworthy. Schema corruption, invariant violations, or
contradictions which cannot be attributed safely to one target are global integrity
failures; they must not be downgraded casually to a race-level `INVALID`.

## Official result and payout evidence resolution

Both provider archives support exact `load_capture(capture_id)`. JRA additionally
has a latest supplied-response lookup which neither returns a capture ID nor supplies
the cross-provider boundary needed here. NAR has no comparable latest-by-race API.

A future evidence resolver reads formal capture metadata only. For each exact target it:

1. restricts provider and page kind to `JRA RACE_RESULT` or
   `NAR RACE_MARK_TABLE`;
2. restricts `observed_at <= explicit settlement_information_cutoff`;
3. derives and validates exact race identity from the canonical URL domain;
4. selects the greatest eligible `observed_at`;
5. requires exactly one candidate at that instant; and
6. exact-loads the selected capture through the existing repository and validates its
   type, ID, provider, page kind, URL identity, and time.

JRA reuses public `parse_jra_result_url_identity`. NAR reuses
`canonicalize_nar_official_capture_url` and derives the already-formal
`nar:YYYYMMDD:babaCode:raceNo` identity from the validated canonical query. Response
bodies and raw HTML are not parsed during selection.

If different captures share the greatest eligible observation instant, evidence is
ambiguous. Capture ID, digest, row ID, stored time, or query order must not break the
tie.

The formal JRA/NAR result page may serve both result and payout normalizers. The same
selected capture ID may therefore populate `result_capture_id` and every supported
payout catalog key when the existing normalizers support that page. Schema v1 already
permits capture-ID reuse. Only frozen plan bet types are consumed later by the existing
runner.

The daily layer never parses body content to predict purchased bet types, finality,
completeness, or exceptional-state support. Existing provider normalizers remain the
sole owners of those validations.

## Settlement-information-cutoff responsibility

The caller supplies one explicit timezone-aware
`settlement_information_cutoff` for the daily operation. The evidence resolver uses
it as the inclusive capture-selection bound, and the exact same instant is written to
every executable schema-v1 race request.

It must not be derived from current time, run start, target date, file time, database
insertion time, archive storage time, an unbounded latest query, or the prediction
cutoff. Prediction and settlement cutoffs remain separate responsibilities.

## Budget contract

The initial daily API accepts exactly one existing value:

```text
race_budget: BetStakeBudget
```

The manifest builder projects that exact same immutable budget to every
`EXECUTABLE` target, keyed by its reconciled internal race ID. Budget coverage must
then satisfy the unchanged schema-v1 exact-coverage contract.

Per-race, confidence-based, venue-based, portfolio, bankroll, or other differentiated
budget policy is not part of the initial daily orchestration and requires a separate
future design phase.

## Migration and schema responsibility

The main database currently uses migrations v008-v015. Provider capture archives use
their own JRA v001-v004 and NAR v001 histories. No daily-run or daily-result schema
exists.

Daily target discovery and evidence resolution must not run
`apply_migrations`, archive migration runners, DDL, schema repair, or compatibility
fallback. They are read-only consumers of the required existing formal schemas.

`run_sqlite_historical_replay` remains the sole owner of main-database migration
application within the existing replay execution path. The daily layer must not
duplicate or preempt that responsibility.

If discovery/resolution requires a table, column, index contract, or archive schema
which is missing, unknown, or inconsistent, preparation fails globally and closed. It
must not create or upgrade schema and must not turn schema absence into a target-level
missing-evidence classification.

This design phase adds no schema, migration, or index.

## Complete outcome classification

After an audited complete target set is validated, every canonical target receives
exactly one preparation classification:

```text
EXECUTABLE
MISSING_EVIDENCE
UNSUPPORTED
INVALID
```

Every non-executable outcome has a stable machine-readable reason code. The reason
domain must distinguish at least missing internal identity reconciliation, missing
snapshot, missing result capture, unsupported provider/page, ambiguous internal
mapping, ambiguous latest snapshot/capture, and safely target-attributable malformed
identity/evidence.

Resolution annotates the complete canonical tuple; it never filters the target set in
place. Only `EXECUTABLE` outcomes are projected into schema v1. The full outcome tuple
remains in `DailyHistoricalReplayResult`, so the projection is not a hidden skip.

`TARGET_DISCOVERY_INCOMPLETE` is not a target classification. It is a whole-operation
failure before outcomes are accepted because there is no trustworthy denominator.
Global schema/repository/archive integrity failures likewise remain whole-operation
failures.

## Necessary and reused models

Reuse exact existing values:

```text
date
timezone-aware datetime
Path
SimulationRunContext
StrategyIdentity
BetStakeBudget
HistoricalInputSnapshotIdentity
HistoricalReplayRaceRequest
HistoricalReplayRequestDocument
SimulationSummary
```

The necessary new immutable daily domain is:

```text
DailyHistoricalReplayTargetSet
DailyHistoricalReplayTargetClassification
DailyHistoricalReplayTargetOutcome
DailyHistoricalReplayResult
```

`DailyHistoricalReplayTargetSet` owns audited completeness and canonical target order.
An outcome binds one canonical target to reconciliation/evidence status and exact
resolved identities when executable. The result retains the exact target set, complete
ordered outcomes, optional real manifest artifact identity/path, and optional exact
`SimulationSummary`.

Any denominator accessor is named `discovered_race_count` or
`canonical_target_count` on the daily domain. It does not change or shadow
`SimulationSummary.race_count`, and no `target_race_count` is added to that model.

The initial future orchestrator inputs reuse existing values and include the audited
target set, database/archive paths, manifest output identity/path, explicit run context,
strategy identity, one `race_budget`, and settlement cutoff. No new input JSON schema
is approved.

## Formal future orchestration sequence

```text
validate audited DailyHistoricalReplayTargetSet and completeness evidence
  -> fail TARGET_DISCOVERY_INCOMPLETE if completeness is unproven
  -> read-only reconcile provider race identities to persisted internal candidates
  -> resolve LATEST_CAUSAL_IN_DATASET through metadata selection plus exact repository load
  -> open only required provider archives read-only/query-only
  -> resolve exact official captures by metadata, identity, and explicit settlement cutoff
  -> freeze complete target outcome classification
  -> if zero executable, return without manifest/loader/runner
  -> project the same race_budget to every executable target
  -> generate and freeze one real deterministic existing schema-v1 manifest artifact
  -> load_historical_replay_request_document(real manifest path)
  -> call run_sqlite_historical_replay(exact loaded document) exactly once
  -> return complete outcomes and the exact returned SimulationSummary
```

Daily discovery/resolution performs no migration. The existing runner retains its own
main migration behavior after the real manifest has been loaded.

## Runner failure semantics

A target classified `EXECUTABLE` during metadata preparation may still contain
body-level unsupported, incomplete, exceptional, or malformed official evidence which
only the formal provider normalizer can determine.

Once `run_sqlite_historical_replay` begins, any exception must:

- propagate according to the existing runner/collaborator contract;
- produce no partial `SimulationSummary`;
- never be converted into a successful `DailyHistoricalReplayResult`;
- trigger no retry;
- trigger no target removal and reduced-manifest rerun; and
- trigger no per-race replay fallback.

The existing replay application's documented durable immutable prefix may remain after
failure. The daily layer does not compensate, delete, or misreport it.

A future persistence phase may record a state such as `BATCH_FAILED` together with
the frozen target set, outcomes, manifest identity, and exception classification. This
design phase implements no failure or result persistence.

## Future daily-result persistence boundary

Future persistence belongs to a separate immutable daily-run repository and migration.
It may retain target-set evidence identity, canonical target order, every outcome,
frozen manifest identity, and final summary or batch failure.

It must not alter `SimulationSummary`, overload result/payout/plan/snapshot tables,
repair evidence, erase failed targets, or claim an atomic transaction spanning
read-only provider archives. It must respect the replay runner's durable-prefix
semantics.

## Future candidate phases

No production or test module is an execution target of
`POST_V0_8_DAILY_REPLAY_1`. The following are conceptual future phases only:

### A. Historical Daily Target Discovery / Completeness

Design and implement provider historical day discovery, completeness evidence capture,
canonical race identity, and immutable `DailyHistoricalReplayTargetSet` creation.

### B. Evidence Resolver

Design and implement read-only internal identity reconciliation,
`LATEST_CAUSAL_IN_DATASET` snapshot resolution bounded by each audited target's
formal `scheduled_start_at`, compatibility verification against the existing
`load_latest_snapshot` contract, and metadata-only exact official capture resolution.
Any unresolved repository-contract/unique-greatest conflict is a mandatory stop for
ChatGPT review.

### C. Existing Schema-v1 Manifest Builder

Design and implement deterministic generation, freeze, audit identity, and exact reload
of a real existing schema-v1 manifest artifact. No new schema.

### D. Daily Replay Orchestrator

Design and implement complete classification, zero-executable handling, one-budget
projection, one manifest load, and exactly one multi-race existing runner invocation.

### E. Daily Result Persistence

Design immutable daily result/batch-failure persistence and migrations without changing
Ver0.8 result, payout, plan, snapshot, or summary contracts.

### F. Reporting / cumulative metrics

Design explicit completeness-qualified daily and cumulative reporting. Never label an
executable subset as a full-day result.

### G. Strategy Comparison

Design comparable strategy runs over identical audited target sets, evidence,
cutoffs, budgets, and manifests.

Each phase requires its own `PREPARE_PHASE`, ChatGPT independent review,
`APPROVE_PHASE`, explicit execution authorization, tests, and stop condition. No
future phase is automatically authorized or advanced by approval of this design.

Candidate modules previously mentioned for daily orchestration and tests belong only to
these future phases after their own approved file contracts. They are not Allowed Files
or implementation targets now.

## Preserved approved contracts

The corrected design preserves:

- no future leakage, hindsight, silent fallback, or hidden skip;
- fail-closed behavior and no current-clock causality;
- explicit settlement cutoff;
- exact provider/race identity;
- metadata-only capture selection followed by exact repository load;
- unique greatest `observed_at` with no arbitrary tie-break;
- reuse of one formal result-page capture ID for result/payout catalog where supported;
- complete outcome classification after audited target-set validation;
- zero-executable no-manifest/no-run behavior;
- exactly one multi-race `run_sqlite_historical_replay` invocation;
- no per-race retry/replay loop;
- unchanged `SimulationSummary.race_count` and no `target_race_count`;
- no direct prediction, bet, normalizer, or settlement reimplementation; and
- no `v0.8.0` tag or release-history mutation.

## Current phase Allowed Files

Allowed Files for `POST_V0_8_DAILY_REPLAY_1` are exactly:

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

Every other path is Forbidden, including:

```text
scripts/**
tests/**
tests/fixtures/**
scripts/migrations/**
scripts/cli/**
examples/**
database/**
logs/**
.github/**
README.md
docs/ARCHITECTURE.md
docs/HISTORICAL_REPLAY.md
docs/VER0.8_SIMULATOR_DESIGN.md
docs/VER0.8_RELEASE_NOTES.md
```

Production code, tests, migrations, CLI, JSON schema, database, archive, release tag,
release history, stage, commit, and push remain unauthorized.

## Required checks

```text
git diff --check
git diff --name-only
git status --short
```

No pytest is required because this phase is design-only and changes no production code
or tests.

## Stop condition

Stop at `APPROVED_FOR_CODEX` after applying only the independent design-review
corrections to the two Allowed Files and running the required Git checks. Do not execute
`EXECUTE_APPROVED_PHASE`, implement any future candidate phase, add tests, stage,
commit, push, modify `v0.8.0`, or advance automatically.
