# Current Phase

## Status

`DRAFT_FOR_REVIEW`

## Phase

`4C-2d3b1i6d1d5f1c4g1` — Ordered multi-race historical planning orchestration.

Formal base: `45b361e5b6c979c4c85a5c37043d30605aa2d47b`.

Prepare branch:
`review/4c-2d3b1i6d1d5f1c4g1-historical-multi-race-planning-prepare`.

The phase hierarchy is confirmed. C4g0 is formally complete at the formal base and owns
one race's historical prediction and bet-plan persistence. C4g1 is the next ordered
multi-race planning composition. C4g2 remains the later settlement/simulation phase.

## Purpose and Boundary

C4g1 accepts an already-built immutable collection of exact historical snapshots and
delegates each race, in canonical order, to the unchanged c4g0 primitive:

```text
exact snapshot tuple
+ one exact SimulationRunContext
+ one exact RuleBased StrategyIdentity
+ one exact BetStakeBudget per internal race ID
+ one exact SimulationBetPlanSnapshotRepository
-> complete batch preflight
-> canonical race order
-> c4g0 exactly once per race
-> ordered tuple of the exact persisted SimulationBetPlanSnapshot objects
```

C4g1 is planning and persistence orchestration only. It does not load historical
snapshots, choose a latest snapshot, adapt snapshots directly, build prediction
pipelines directly, allocate stakes directly, resolve selection identities directly,
save directly, settle races, call `Simulator`, or calculate a run summary.

`PersistedSimulationRunService` is not used or changed. It combines planning with
post-race simulation/settlement and therefore belongs outside this boundary.

## Public Batch API

Future module:

`scripts/simulation/historical_prediction_bet_plan_batch_execution.py`

Exact module-local public surface:

```python
__all__ = (
    "execute_and_persist_historical_bet_plans",
)
```

No package-root export.

Exact keyword-only API:

```python
def execute_and_persist_historical_bet_plans(
    *,
    snapshots: tuple[HistoricalInputSnapshot, ...],
    run_context: SimulationRunContext,
    strategy_identity: StrategyIdentity,
    budgets_by_race_id: Mapping[int, BetStakeBudget],
    snapshot_repository: SimulationBetPlanSnapshotRepository,
) -> tuple[SimulationBetPlanSnapshot, ...]:
    ...
```

The snapshot collection boundary is deliberately an exact tuple. Require
`type(snapshots) is tuple`; lists and other `Sequence` implementations are rejected.
Every item must satisfy `type(item) is HistoricalInputSnapshot`.

No result dataclass is introduced. On complete success the function returns a tuple in
canonical race order. Every tuple element is the exact object returned by the
corresponding c4g0 call.

## Empty Batch Policy

An exact empty snapshot tuple is valid only with an empty budget mapping. After all
shared public-boundary validation succeeds, it returns `()` without calling c4g0 or the
repository.

This mirrors the established zero-race multi-race semantics while keeping c4g1 free of
simulation summary ownership. A nonempty budget mapping with an empty snapshot tuple is
an exact-key-set error before any c4g0 call.

## Boundary Validation and Defensive Freeze

All facts that can be established statically are validated before the first c4g0 call
and therefore before the first repository save. The exact deterministic order is:

1. require `type(snapshots) is tuple`;
2. require every snapshot item to be exact `HistoricalInputSnapshot`;
3. require exact `SimulationRunContext`;
4. require exact `StrategyIdentity`;
5. require `budgets_by_race_id` to be a `Mapping` and not a type object;
6. copy the mapping exactly once with `dict(budgets_by_race_id)`;
7. require every copied key to be a positive non-`bool` exact `int` and every value to
   be exact `BetStakeBudget`;
8. require `snapshot_repository` not to be a type object and to expose callable
   `save_snapshot`;
9. require `strategy_identity.strategy_name == RuleBasedBetStrategy.__name__`;
10. sort the already-validated exact snapshots by the canonical ordering key;
11. reject duplicate `internal_race_id` values deterministically;
12. require the frozen budget-key set to equal the snapshot internal-race-ID set; and
13. validate every snapshot dataset in canonical order, raising for the first mismatch.

Only after this complete preflight may execution begin. All non-dataset c4g1 boundary
failures are `ValueError`. No broad exception catch, error translation, default, or
fallback is added.

The snapshot tuple is already immutable and is not copied or reread through another
caller-owned collection. The budget mapping is copied once before execution; the
validated copy alone is used for key coverage and every per-race lookup. Caller
mutation during the execution loop cannot alter the batch.

## Canonical Race Order and Duplicate Policy

Canonical ascending order is exactly:

```python
(
    snapshot.race.scheduled_start_at,
    snapshot.internal_race_id,
)
```

The internal race ID is the deterministic tie-break for equal scheduled starts. Caller
tuple order, target race date, information cutoff, captured-at time, horse count, and
external race ID are not ordering inputs.

Duplicate `snapshot.internal_race_id` values are forbidden. C4g1 represents at most one
planning snapshot for a race within one run. It does not distinguish duplicates by
cutoff, overwrite one duplicate with another, or use last-write-wins behavior.

## Budget Binding

The frozen budget keys must exactly equal:

```python
{snapshot.internal_race_id for snapshot in snapshots}
```

There is no missing, extra, positional, default, or carried-forward budget. For each
canonical snapshot, c4g1 passes the exact caller-owned budget object retained in the
frozen mapping at `snapshot.internal_race_id`. Mapping insertion order has no effect on
validation, execution order, or output.

## Dataset and Strategy Binding

One exact `SimulationRunContext` and one exact `StrategyIdentity` are shared by every
c4g0 call. Before the first call, every snapshot must satisfy:

```python
snapshot.identity.dataset_id == run_context.dataset_id
```

The first mismatch in canonical race order raises exactly:

```python
SimulationValidationError(
    snapshot.internal_race_id,
    "run_context.dataset_id",
    "run_context.dataset_id does not match snapshot.identity.dataset_id",
)
```

C4g0 repeats this check for each invoked race as defense in depth.

The shared strategy must satisfy, before execution:

```python
strategy_identity.strategy_name == RuleBasedBetStrategy.__name__
```

The exact caller-owned strategy object is passed unchanged to every c4g0 call. There is
no identity rewriting or fallback strategy.

## C4g0 Delegation

For each canonical snapshot call exactly once:

```python
execute_and_persist_historical_bet_plan(
    snapshot=snapshot,
    run_context=run_context,
    strategy_identity=strategy_identity,
    budget=budgets[snapshot.internal_race_id],
    snapshot_repository=snapshot_repository,
)
```

C4g0 is reused unchanged and remains the only per-race execution primitive. C4g1 does
not duplicate or directly invoke the c4f1 adapter, historical pipeline factory,
`PredictionPipeline.run`, `FixedStakeBetAllocator`,
`ExactRaceEntrySelectionResolver`, `SimulationBetPlanBuilder`,
`PersistedSimulationBetPlanService`, snapshot identity construction, or
`save_snapshot`.

The exact same run-context, strategy-identity, and repository objects are passed to all
races. The exact canonical snapshot and exact per-race budget objects are passed to
their corresponding call. Each attempted race receives exactly one c4g0 call; there is
no preflight execution, retry execution, or duplicate execution.

## Persistence, Atomicity, and Failure Semantics

C4g1 makes no direct `save_snapshot` call. Save ownership remains entirely in c4g0 and
the unchanged `PersistedSimulationBetPlanService` chain.

Batch-atomic persistence is not promised. The generic repository protocol exposes only
one-snapshot `save_snapshot`; it has no batch transaction protocol. The current SQLite
implementation rejects an already-active caller transaction and owns one
`BEGIN IMMEDIATE`/commit per snapshot. Therefore:

- c4g1 owns no transaction;
- it does not wrap the batch in a transaction;
- it does not roll back or delete previously persisted races;
- it does not automatically retry; and
- it does not depend on repository-specific retry behavior.

If canonical races are R1, R2, R3, R4 and c4g0 fails for R3, R1 and R2 may already be
durably persisted, the exact R3 failure propagates, R4 is not executed, and c4g1
returns no partial tuple. It neither swallows the error nor returns `(R1, R2)`. A
durable successful prefix is an explicit possible outcome of the per-race persistence
contract, not a batch success.

The generic `SimulationBetPlanSnapshotRepository` is not required to be idempotent
unless that property is later formalized in its protocol. The SQLite repository's
existing acceptance of an equal saved snapshot, and conflict for a differing snapshot,
is an implementation detail. C4g1 correctness and failure handling do not rely on it.

## Result and Empty Plans

Only when all canonical races succeed does c4g1 return the complete tuple. It preserves
each exact c4g0 result object and canonical order.

A legitimate c4g0 result with `bets == ()` is a successful planning snapshot. It stays
in the returned tuple and is not skipped or filtered. C4g1 does not create or interpret
`SettlementStatus.NO_BET`, and no error becomes an empty plan.

## Determinism

For the same exact snapshot tuple contents, `SimulationRunContext`,
`StrategyIdentity`, frozen race-keyed budgets, code revision, and an equivalent
successful repository start state and behavior, c4g1 produces equal canonically ordered
`SimulationBetPlanSnapshot` values independent of caller snapshot tuple permutation,
budget mapping insertion order, and process date. Different `run_context.run_id`
remains an output identity input and may produce different plan identities.

A process restart itself introduces no process-local, clock, random, or environment
dependency. It does not guarantee successful replay when prior execution changed durable
repository state: the generic repository contract does not require equal-snapshot
idempotence. Later external-state independence is therefore not a global guarantee, and
retry after a durable-prefix failure is outside c4g1's generic contract. The current
SQLite equal-snapshot retry behavior remains an implementation detail.

```text
DETERMINISM_REPOSITORY_PRECONDITION:
EQUIVALENT_START_STATE_AND_SUCCESSFUL_BEHAVIOR

PROCESS_RESTART_SEMANTICS:
NO_PROCESS_LOCAL_STATE_DEPENDENCY

PROCESS_RESTART_WITH_CHANGED_DURABLE_REPOSITORY_STATE:
NOT_GUARANTEED

LATER_EXTERNAL_STATE_INDEPENDENCE:
NO_GLOBAL_GUARANTEE

RETRY_AFTER_DURABLE_PREFIX:
NOT_GUARANTEED_BY_C4G1
```

## Excluded Ownership

C4g1 performs no direct:

- snapshot repository save or load;
- SQLite or other database query;
- historical snapshot loading or latest selection;
- replay seed load or JRA replay;
- adapter, pipeline, allocator, resolver, or builder construction;
- race-result, finish-order, payout, refund, settlement, profit, ROI, or hit-rate read or
  calculation;
- `Simulator` or `PersistedSimulationRunService` call;
- HTTP, source acquisition, filesystem, current clock, or random access; or
- broad `Exception`/`BaseException` catch.

The exact snapshots are the entire historical fact input. There is no live/current,
legacy, name, external-ID, or mutable-data fallback. C4g2 settlement/simulation remains
unstarted.

## Implementation Scope

Future production:

- `scripts/simulation/historical_prediction_bet_plan_batch_execution.py` (new)

Future dedicated test:

- `tests/test_historical_prediction_bet_plan_batch_execution.py` (new)

Implementation review docs:

- `docs/CURRENT_PHASE.md`
- `docs/LATEST_CODEX_REPORT.md`

No existing production file is required. C4g0, c4f0, c4f1, repository protocols, the
SQLite repository, schemas, migrations, package roots, and generic services remain
unchanged.

## Future Test Contract

The implementation review must pin:

- exact one-symbol `__all__`, keyword-only API, type hints, and no package-root export;
- exact tuple snapshot boundary and exact snapshot item types;
- exact run-context, strategy-identity, budget, and structural repository validation;
- every invalid static batch fact failing before the first c4g0 call/save;
- exact `RuleBasedBetStrategy` name required before execution;
- valid empty batch plus empty budgets returning `()` with no c4g0/repository call;
- nonempty budgets for an empty batch failing before execution;
- one-race and multi-race success;
- reversed/permuted input yielding canonical call and result order;
- equal scheduled-start tie broken by internal race ID;
- duplicate race ID rejection before execution;
- exact budget-key coverage, missing/extra rejection, insertion-order independence, and
  exact budget object identity;
- preflight of all datasets before execution, including a later caller-position
  mismatch preventing earlier persistence;
- first dataset mismatch selected in canonical order with the exact
  `SimulationValidationError` fields;
- c4g0 exactly once per attempted race with exact snapshot, shared run context, shared
  strategy identity, per-race budget, and shared repository objects;
- no direct adapter, factory, pipeline, allocator, resolver, builder, or save call;
- successful output tuple in canonical order with exact c4g0 object identities;
- an empty-bets race retained in the result;
- exact mid-batch error propagation, no partial return, no later race, no rollback or
  retry, and a possible already-persisted successful prefix;
- deterministic equality across snapshot permutation, budget mapping insertion order,
  and process date for equivalent fresh/recording repository start state and successful
  behavior, plus run-ID identity distinction;
- no process-local state retained between invocations and no clock/random dependency;
- no generic guarantee of retry after a durable-prefix failure or after a changed durable
  repository state; and
- defensive budget mapping freeze against caller mutation; and
- static exclusion of simulator, persisted run service, settlement/result/payout,
  SQLite, HTTP, current clock, random, broad catches, package-root changes, and direct
  c4g0/c4f0/c4f1 or repository-protocol changes.

## Readiness

```text
IMPLEMENTATION_READY:
YES_AFTER_INDEPENDENT_APPROVAL

BLOCKERS:
NONE
```

## Allowed Files for This PREPARE

- `docs/CURRENT_PHASE.md`
- `docs/LATEST_CODEX_REPORT.md`

## Forbidden Files for This PREPARE

All production files, tests, schemas, migrations, package roots, databases, and logs.

## Verification

Required for this docs-only PREPARE:

- `git diff --check`
- changed-file scope check
- final `git status --short`
- formal remote remains `45b361e5b6c979c4c85a5c37043d30605aa2d47b`

Pytest is intentionally not rerun. No live HTTP or trusted capture is allowed.

## Stop Condition

After one docs-only commit is pushed to the PREPARE review branch, stop for independent
architecture review. Do not implement c4g1, begin c4g2, or modify the formal branch.
