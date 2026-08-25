# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase

`4C-2d3b1i6d1d5f1c4g0` — Single-race historical prediction bet-plan persistence composition.

Formal base: `8ee5440bd7a360c652c3b58f1a67b05c32b682c8`.

Review branch:
`review/4c-2d3b1i6d1d5f1c4g0-historical-prediction-bet-plan-execution-prepare`.

The next parent hierarchy slot after completed c4f1 is c4g, historical prediction
bet-plan execution composition. The work must be split because the formal historical
pipeline is race-date-specific and the existing multi-race run service owns one pipeline
for all races. Therefore the immediately implementable phase is c4g0, followed by c4g1
multi-race planning and c4g2 settlement/simulation.

## Purpose and Exact Boundary

C4g0 is one race only:

```text
exact HistoricalInputSnapshot
-> c4f1 adapter exactly once
-> exact SimulationRaceInput
-> historical pipeline factory exactly once for target_race_date
-> PredictionPipeline.run exactly once through existing service
-> existing allocation
-> exact identity-preserving selection resolution
-> SimulationBetPlanSnapshot save
-> exact saved SimulationBetPlanSnapshot result
```

It does not load a snapshot, select latest evidence, orchestrate several races, execute
settlement, or run the simulator.

Freeze:

```text
EXECUTION_INPUT_DOMAIN: EXACT_HISTORICAL_INPUT_SNAPSHOT
LATEST_SNAPSHOT_LOOKUP: NO
SOURCE_URL_FALLBACK: NO
LEGACY_SNAPSHOT_LOOKUP: NO
RACE_RESULT_READ: NO
PAYOUT_READ: NO
SETTLEMENT: NO
SIMULATOR_RUN: NO
CURRENT_CLOCK: NO
LIVE_HTTP: NO
```

Exact persisted-snapshot loading remains the responsibility of a later application
composition boundary. C4g0 receives the already exact immutable snapshot directly.

## Public Execution API

Create:

```text
scripts/simulation/historical_prediction_bet_plan_execution.py
```

Its intended module-local public surface is exactly:

```python
__all__ = (
    "execute_and_persist_historical_bet_plan",
)

def execute_and_persist_historical_bet_plan(
    *,
    snapshot: HistoricalInputSnapshot,
    run_context: SimulationRunContext,
    strategy_identity: StrategyIdentity,
    budget: BetStakeBudget,
    snapshot_repository: SimulationBetPlanSnapshotRepository,
) -> SimulationBetPlanSnapshot:
    ...
```

No package-root export is required. The function accepts no database connection,
snapshot identity, pipeline, pipeline factory, allocator, selection source, clock,
result source, payout source, simulator, or settlement collaborator.

Require exact domain types for `snapshot`, `run_context`, `strategy_identity`, and
`budget`. Require `snapshot_repository` to be a non-type object with callable
`save_snapshot`. Invalid boundary input raises `ValueError` before adapter, pipeline
factory, prediction, allocation, builder, or repository activity. Before any of those
activities also require the exact strategy execution binding:

```text
strategy_identity.strategy_name == RuleBasedBetStrategy.__name__
strategy_identity.strategy_name == "RuleBasedBetStrategy"
```

A nonmatching strategy name raises `ValueError`. The caller's exact
`StrategyIdentity` remains the formal identity: do not rewrite its name, reconstruct
it, substitute a strategy, or fall back.

No new public execution result or public error hierarchy is needed. Return the exact
`SimulationBetPlanSnapshot` produced and saved by the existing formal service. Existing
`SimulationValidationError`, `PipelineExecutionError`, allocator errors, and repository
validation/conflict/integrity errors propagate unchanged.

## Run Context and Dataset Binding

Before adapter or prediction work require:

```text
if run_context.dataset_id != snapshot.identity.dataset_id:
    raise SimulationValidationError(
        snapshot.internal_race_id,
        "run_context.dataset_id",
        "run_context.dataset_id does not match snapshot.identity.dataset_id",
    )
```

A mismatch raises exactly the shown `SimulationValidationError` for the snapshot's
exact internal race and exact input identifier. It occurs before adapter, pipeline
factory, prediction, allocation, builder, or repository activity and is never converted
to `ValueError`, `NO_BET`, or a repository error.

The adapter-produced audit dataset is necessarily the same snapshot dataset. The
composition does not invent or reparse a dataset. `run_context.target_commit_id` remains
retained formal run metadata, but runtime checkout/commit verification is out of scope:

```text
RUN_CONTEXT_DATASET_MATCH: REQUIRED_BEFORE_ADAPTER_OR_PREDICTION
DATASET_MISMATCH_ERROR: SimulationValidationError
DATASET_MISMATCH_INPUT_IDENTIFIER: run_context.dataset_id
DATASET_MISMATCH_RACE_ID: snapshot.internal_race_id
TARGET_COMMIT_RUNTIME_VERIFICATION: OUT_OF_SCOPE
```

## Strategy Execution Identity

`build_historical_prediction_pipeline(...)` formally constructs exactly
`RuleBasedBetStrategy()`, while `StrategyIdentity` permits other names. C4g0 therefore
owns the explicit execution-to-persistence identity binding before any collaborator
activity:

```text
HISTORICAL_SUPPORTED_STRATEGY_NAME: RuleBasedBetStrategy
STRATEGY_NAME_BINDING: REQUIRED_BEFORE_ADAPTER_OR_PIPELINE
STRATEGY_IDENTITY_EXECUTION_MATCH: EXACT_RULE_BASED_STRATEGY
ARBITRARY_STRATEGY_IDENTITY_NAME: FORBIDDEN
```

The exact supported name is `RuleBasedBetStrategy.__name__`, namely
`"RuleBasedBetStrategy"`. No fallback, rewriting, or reconstructed
`StrategyIdentity` is allowed.

## Historical Pipeline Ownership

`build_historical_prediction_pipeline(...)` binds Ability, Jockey, and Track engines to
one explicit target race date. A pipeline is therefore valid for one race-date context,
not for a heterogeneous historical run.

For each c4g0 invocation call exactly once:

```python
build_historical_prediction_pipeline(
    target_race_date=race_input.target_race_date,
    strategy_config=strategy_identity.strategy_config,
)
```

The exact `strategy_identity.strategy_config` object is passed unchanged. It is not
copied, reconstructed, reparsed, or replaced by an equal configuration. The existing
`PersistedSimulationBetPlanService` retains its strategy-config consistency check.

Immediately after the one factory call, and before
`PersistedSimulationBetPlanService.build_and_save(...)`, require defense in depth:

```text
type(prediction_pipeline) is PredictionPipeline
type(prediction_pipeline.config) is PipelineConfig
prediction_pipeline.config.strategy_config is strategy_identity.strategy_config
type(prediction_pipeline.config.bet_strategy) is RuleBasedBetStrategy
```

Any failure raises `ValueError`. Do not rebuild, substitute, or call the factory a
second time.

Freeze:

```text
HISTORICAL_PIPELINE_LIFETIME: ONE_C4G0_RACE_EXECUTION
PIPELINE_PER_RACE: YES
ONE_HISTORICAL_PIPELINE_ACROSS_DIFFERENT_RACE_DATES: FORBIDDEN
DEFAULT_PIPELINE_FALLBACK: FORBIDDEN
CURRENT_CLOCK_PIPELINE: FORBIDDEN
PIPELINE_FACTORY_CALL_COUNT: EXACTLY_ONE
PIPELINE_RUN_CALL_COUNT_PER_RACE: EXACTLY_ONE
PIPELINE_CONFIG_STRATEGY_CONFIG_IDENTITY: EXACT_CALLER_OBJECT
PIPELINE_BET_STRATEGY_TYPE: EXACT_RULE_BASED_BET_STRATEGY
```

No preflight, logging, or identity-discovery pipeline execution is permitted.

## Identity-Preserving Selection Resolver

C4f1 already makes exact internal `race_entry_id` the prediction entity key. Pipeline
predictions and recommendations therefore carry race-entry IDs despite the legacy
protocol parameter name `horse_ids`.

Create:

```text
scripts/simulation/exact_race_entry_selection_resolver.py
```

with the exact module-local public surface:

```python
__all__ = (
    "ExactRaceEntrySelectionResolver",
)
```

It contains one public frozen/slotted type and no other public symbol:

```python
@dataclass(frozen=True, slots=True)
class ExactRaceEntrySelectionResolver:
    race_id: int
    allowed_race_entry_ids: tuple[int, ...]

    def resolve_race_entry_ids(
        self,
        *,
        race_id: int,
        horse_ids: Sequence[int],
    ) -> tuple[int, ...]:
        ...
```

The constructor requires an exact positive non-bool race ID and an exact nonempty tuple
of unique positive non-bool race-entry IDs. The resolver requires:

- requested race ID equals the bound race ID;
- `horse_ids` is a non-string, non-mapping, nonempty finite `Sequence`;
- every requested value is a positive non-bool integer;
- requested values contain no duplicates; and
- every requested value belongs to the exact allowlist.

It returns `tuple(horse_ids)` unchanged and in the same order. It does not sort, map,
query, infer, or translate identity. This structurally satisfies the existing
`RaceEntrySelectionResolver` without changing `SimulationBetPlanBuilder`.

The c4g0 composition obtains the allowlist only after c4f1 conversion from:

```text
tuple(race_input.pipeline_input.horse_past_races.keys())
```

The immutable pipeline domain already proves exact key equality with
`jockey_names_by_horse` and `odds_by_horse`. No second identity set is loaded.

Freeze:

```text
HISTORICAL_RECOMMENDATION_ID_ALREADY_RACE_ENTRY_ID: YES
HISTORICAL_SELECTION_RESOLVER: ExactRaceEntrySelectionResolver
SELECTION_IDENTITY_TRANSFORMATION: NONE_RETURN_EXACT_REQUEST_ORDER
SELECTION_ALLOWLIST_SOURCE: EXACT_PIPELINE_HORSE_PAST_RACES_KEYS
LEGACY_SELECTION_DB_LOOKUP: NO
HORSES_TABLE_LOOKUP: NO
HORSE_NAME_MAPPING: NO
NUMERIC_COINCIDENCE_MAPPING: NO
EXTERNAL_ID_MAPPING: NO
```

Existing snapshot-repository foreign-key and integrity enforcement remains unchanged;
it is not selection resolution and does not authorize a legacy identity lookup.

C4g0 and the resolver perform no direct SQLite access, `RaceEntrySource` access,
horses-table lookup, database identity lookup, name lookup, or external-ID lookup. The
injected `SimulationBetPlanSnapshotRepository` remains the intentional persistence
boundary. C4g0 calls only its `save_snapshot(...)` contract; a concrete repository may
perform its own integrity or idempotence reads and writes internally. Such internal
storage checks are not selection identity resolution and their results must never
transform recommendation IDs.

Freeze:

```text
COMPOSITION_DIRECT_DATABASE_READ: NO
SELECTION_DATABASE_READ: NO
HORSES_TABLE_SELECTION_LOOKUP: NO
SNAPSHOT_REPOSITORY_IO: ALLOWED_ONLY_THROUGH_SAVE_SNAPSHOT_CONTRACT
SNAPSHOT_REPOSITORY_USED_FOR_SELECTION_IDENTITY: NO
REPOSITORY_READ_RESULT_USED_TO_TRANSFORM_RECOMMENDATION_IDS: NO
```

## Existing Bet-Plan Service Reuse

Construct an exact `SimulationBetPlanBuilder` with the exact resolver, then construct an
exact `PersistedSimulationBetPlanService` with:

- the caller's exact `SimulationRunContext`;
- the caller's exact `StrategyIdentity`;
- the per-race historical `PredictionPipeline`;
- the existing `FixedStakeBetAllocator`;
- the new resolver-backed exact `SimulationBetPlanBuilder`; and
- the caller's snapshot repository.

Call `build_and_save(race_input=race_input, budget=budget)` exactly once and return its
exact result. Reuse without modification preserves:

- one pipeline execution;
- `SimulationBetPlanIdentity` construction from run/race/strategy/cutoff;
- pipeline-result validation;
- allocation policy identity;
- allocator call and plan identity validation;
- bet-plan builder call and snapshot validation;
- snapshot repository save exactly once; and
- repository error propagation.

Freeze:

```text
PERSISTED_BET_PLAN_SERVICE_REUSED: YES_UNCHANGED
PERSISTED_BET_PLAN_SERVICE_CHANGE_REQUIRED: NO
ADAPTER_CALL_COUNT: EXACTLY_ONE
BET_PLAN_SERVICE_BUILD_AND_SAVE_CALL_COUNT: EXACTLY_ONE
ALLOCATOR_CALL_COUNT: EXACTLY_ONE
BET_PLAN_BUILDER_CALL_COUNT: EXACTLY_ONE
SNAPSHOT_SAVE_CALL_COUNT: EXACTLY_ONE
```

## Allocation and NO_BET

Use `FixedStakeBetAllocator` unchanged, constructed from the exact
`strategy_identity.strategy_config.allocation_policy` object. The existing allocator
supports only its exact formal fixed-stake policy name, version, and parameter contract.
Missing or unsupported policy fails closed before prediction execution; no alternate
algorithm or default stake is introduced.

The budget is the caller's exact `BetStakeBudget`. A genuine empty strategy `BetPlan`
is the only `NO_BET` path: existing allocation and builder produce and persist a valid
zero-bet `SimulationBetPlanSnapshot`. Validation failure, pipeline failure, insufficient
budget, unknown selection, or repository failure never becomes `NO_BET`.

```text
ALLOCATION_POLICY: EXISTING_FIXED_STAKE_ALLOCATOR_FROM_EXACT_STRATEGY_POLICY
NO_BET_POLICY: PERSIST_EXACT_EMPTY_FORMAL_PLAN_ONLY
```

## Prediction Visibility and Persistence

The existing service validates `PipelineResult` internally and persists only the final
bet-plan snapshot. C4g0 does not need public prediction/value/recommendation output for
the current reproducible ROI path:

```text
PUBLIC_EXECUTION_RESULT: EXACT_SAVED_SIMULATION_BET_PLAN_SNAPSHOT
PIPELINE_RESULT_PUBLICLY_REQUIRED: NO
PREDICTION_PERSISTENCE_REQUIRED: NO
```

If prediction-result persistence becomes necessary, it requires a separate phase and
must not widen this service implicitly.

## Future-Information and Failure Boundary

The historical pipeline reads only `race_input.pipeline_input`. The bet-plan identity
uses the exact information cutoff. Selection uses only formal race-entry IDs. Allocation
uses only the formal plan, policy, and budget. Persistence receives only the validated
snapshot.

Prohibited:

```text
DIRECT_SQLITE_OR_DATABASE_IDENTITY_READ_BY_COMPOSITION
SELECTION_DATABASE_READ
CURRENT_RACE_OR_HORSE_STATE
POST_CUTOFF_ODDS
TARGET_RACE_RESULTS_OR_FINISH_ORDER
PAYOUTS
SETTLEMENT
CURRENT_TIME
LIVE_OR_DEFAULT_FALLBACK
```

No broad `Exception` or `BaseException` catch is allowed. Existing
`PipelineExecutionError`, `SimulationValidationError`, and repository-owned errors
propagate unchanged.

Determinism is defined over every formal identity-bearing input, including the run
context:

```text
DETERMINISM_INPUTS: SNAPSHOT_PLUS_RUN_CONTEXT_PLUS_STRATEGY_IDENTITY_PLUS_BUDGET_PLUS_CODE_REVISION
RUN_ID_IS_OUTPUT_IDENTITY_INPUT: YES
```

The same exact snapshot, run context, strategy identity, budget, and code revision
produce an equal `SimulationBetPlanSnapshot`, assuming the same successful repository
contract/state. A different `run_context.run_id` may and normally will produce a
different `SimulationBetPlanIdentity`.

## Phase Split

The exact hierarchy is:

```text
4C-2d3b1i6d1d5f1c4g0
    single-race historical prediction -> persisted bet plan

4C-2d3b1i6d1d5f1c4g1
    ordered multi-race historical planning orchestration;
    invoke c4g0 once per exact snapshot and construct one pipeline per race

4C-2d3b1i6d1d5f1c4g2
    historical result/payout settlement, simulator execution, and summary
```

C4g0 does not modify or call `PersistedSimulationRunService`. C4g1 must not reuse one
historical pipeline across different race dates. C4g2 alone may introduce post-race
facts after independent review.

## Future Implementation Scope

Production:

```text
scripts/simulation/exact_race_entry_selection_resolver.py
scripts/simulation/historical_prediction_bet_plan_execution.py
```

Tests:

```text
tests/test_exact_race_entry_selection_resolver.py
tests/test_historical_prediction_bet_plan_execution.py
```

Docs:

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

No existing production file should change. In particular, c4f0, c4f1,
`PersistedSimulationBetPlanService`, `SimulationBetPlanBuilder`, simulation validation,
snapshot domains/repositories, prediction engines, ValueEngine, schemas, and migrations
remain bit-for-bit unchanged.

## Future Test Matrix

Future resolver tests must pin:

- exact `__all__ == ("ExactRaceEntrySelectionResolver",)`, no other public symbol,
  frozen/slotted type, fields, and method signature;
- exact constructor race ID and allowlist validation;
- exact requested race match;
- sequence validation, positive IDs, uniqueness, and allowlist membership;
- exact unchanged tuple and recommendation order;
- unknown/unallowed ID and wrong race fail closed;
- structural `RaceEntrySelectionResolver` compatibility;
- no SQLite, repository, `RaceEntrySource`, `horses` table, name, or external mapping;
- no clock, HTTP, filesystem, or broad catch; and
- no package-root export.

Future execution tests must pin:

- exact public API and exact input types;
- all input validation and dataset match before adapter/pipeline/repository activity;
- non-`RuleBasedBetStrategy` strategy identity name fails before adapter, historical
  pipeline factory, or repository activity;
- exact `"RuleBasedBetStrategy"` identity is accepted without identity rewriting;
- adapter exactly once with the same snapshot;
- historical pipeline factory exactly once;
- exact target race date and exact strategy-config object identity;
- returned pipeline has exact `PredictionPipeline` and `PipelineConfig` types, retains
  the same strategy-config object, and has exact `RuleBasedBetStrategy` type;
- pipeline run exactly once with the exact immutable pipeline input;
- exact allowlist derived only from pipeline past-race mapping keys;
- recommendation IDs remain exact race-entry IDs and order is preserved;
- unknown selection and wrong race fail closed;
- dataset mismatch has exact `SimulationValidationError`, snapshot internal race ID,
  and `run_context.dataset_id` input identifier;
- no direct SQLite, `RaceEntrySource`, horses-table, database identity, name, or
  external-ID lookup in either new production module;
- the injected snapshot repository remains allowed only as the persistence boundary;
- existing fixed-stake allocator exactly once with exact formal policy and budget;
- missing/unsupported allocation policy fails closed without prediction;
- existing bet-plan builder exactly once;
- existing service `build_and_save` and repository save exactly once;
- exact returned object is the saved `SimulationBetPlanSnapshot`;
- legitimate empty plan is persisted as zero-bet `NO_BET`;
- `PipelineExecutionError`, `SimulationValidationError`, and repository errors propagate;
- no current clock, result, payout, settlement, simulator, or fallback;
- identical snapshot, run context, strategy identity, budget, and code revision are
  deterministic under the same successful repository contract/state;
- a different run ID produces a different plan identity;
- process date does not affect output;
- two different target race dates use distinct correctly dated pipelines in separate
  c4g0 invocations;
- no latest snapshot selection or persisted snapshot loading;
- no public pipeline-result/prediction persistence;
- c4f0/c4f1 and all existing generic services remain bit-for-bit unchanged; and
- no schema or migration change.

## Readiness

```text
PUBLIC_EXECUTION_API_READY: YES
PER_RACE_PIPELINE_OWNERSHIP_READY: YES
SELECTION_IDENTITY_READY: YES
DATASET_BINDING_READY: YES
SERVICE_REUSE_READY: YES
ALLOCATION_READY: YES_FIXED_STAKE_ONLY
STRATEGY_EXECUTION_IDENTITY_READY: YES_EXACT_RULE_BASED_STRATEGY
PIPELINE_POSTCONSTRUCTION_PROOF_READY: YES
RESOLVER_PUBLIC_SURFACE_READY: YES_EXACT
REPOSITORY_BOUNDARY_WORDING_READY: YES
FAILURE_POLICY_READY: YES
IMPLEMENTATION_READY: YES_AFTER_INDEPENDENT_APPROVAL
BLOCKERS: NONE
```

## Allowed Files for This PREPARE

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Forbidden Files for This PREPARE

All production, tests, schema, migration, repositories, prediction engines, c4f0, c4f1,
multi-race orchestration, settlement, simulator, CLI, JRA/NAR acquisition, and package
root files.

## Required PREPARE Checks

```text
git diff --check
git status --short
changed-file scope == the two allowed docs
```

No pytest or HTTP is required.

## Stop Condition

Commit and push the single docs-only PREPARE review commit, then stop for independent
review. Do not implement c4g0, c4g1, or c4g2 and do not modify the formal branch.
