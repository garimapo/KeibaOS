# Current Phase

## Status

APPROVED_FOR_CODEX

## Phase

Phase 4C-2d3b1i1 — Prediction-to-snapshot persistence service

## Base Commit

`dafb04d docs: approve prediction immutable input contracts`

## Branch

`feature/ver0.8-simulator`

## Objective

Implement one application service that persists a single race's immutable simulation bet plan:

```text
SimulationRaceInput
→ PredictionPipeline.run(race_input.pipeline_input)
→ PipelineResult.bet_plan
→ BetStakeAllocator.allocate()
→ BetAllocationPlan
→ SimulationBetPlanBuilder.build()
→ SimulationBetPlanSnapshot
→ SimulationBetPlanSnapshotRepository.save_snapshot()
→ exact SimulationBetPlanSnapshot return
```

The Pipeline receives the exact existing `race_input.pipeline_input`. Do not restore a mutable
`RacePredictionInput`; copy, sort, normalize, supplement, or reconstruct Pipeline input; load
DB/Provider data; derive odds/past races; use current time; or change Pipeline stage behavior.

## Formal API

Module: `scripts/simulation/persisted_bet_plan_service.py`

```python
class PersistedSimulationBetPlanService:
    def __init__(
        self,
        *,
        run_context: SimulationRunContext,
        strategy_identity: StrategyIdentity,
        prediction_pipeline: PredictionPipeline,
        allocator: BetStakeAllocator,
        plan_builder: SimulationBetPlanBuilder,
        snapshot_repository: SimulationBetPlanSnapshotRepository,
    ) -> None:
        ...

    def build_and_save(
        self,
        *,
        race_input: SimulationRaceInput,
        budget: BetStakeBudget,
    ) -> SimulationBetPlanSnapshot:
        ...
```

`__slots__` is optional. Do not add a package-root export or a new service-owned Pipeline Protocol.

## Constructor Contract

Require these exact domain/concrete types, otherwise raise `ValueError`:

```text
run_context: SimulationRunContext
strategy_identity: StrategyIdentity
prediction_pipeline: PredictionPipeline
plan_builder: SimulationBetPlanBuilder
```

`allocator` and `snapshot_repository` are structural collaborators. Reject a class object and
require respectively callable `allocate` and callable `save_snapshot`; otherwise raise
`ValueError`. Do not use runtime Protocol `isinstance()`, signature inspection, `Any`, `cast`, or
`type: ignore`.

Keep every injected object by exact object identity; do not copy or wrap it. The constructor calls
no collaborator and does not create/modify run IDs, strategy IDs/hashes, policy identity, plan
identity, budget, or snapshots.

## Direct Arguments

`build_and_save()` requires exact `SimulationRaceInput` and `BetStakeBudget`; an invalid direct
argument raises `ValueError` and calls no collaborator. Do not duplicate validations already owned
by `SimulationRaceInput`, including pipeline input race-ID equality, audit completeness, cutoff,
or input-category validation.

## Strategy and Allocation-policy Contract

The only strategy/Pipeline consistency rule is:

```python
prediction_pipeline.config.strategy_config == strategy_identity.strategy_config
```

Check it immediately before every Pipeline execution, not only in the constructor. First require
that `prediction_pipeline.config` is `PipelineConfig`; otherwise raise:

```python
SimulationValidationError(
    race_input.race_id,
    "prediction_pipeline",
    "config must be a PipelineConfig",
)
```

On config mismatch, raise:

```python
SimulationValidationError(
    race_input.race_id,
    "prediction_pipeline",
    "strategy_config does not match strategy_identity",
)
```

Neither failure calls Pipeline, allocator, Builder, or Repository.

Do **not** compare `PipelineResult.bet_plan.strategy_name` with
`StrategyIdentity.strategy_name`; do not infer BetStrategy class names; do not rewrite strategy
names; and do not regenerate strategy IDs or config hashes. The two names are distinct existing
domain concepts.

The sole policy source is:

```python
policy_config = strategy_identity.strategy_config.allocation_policy
```

If it is `None`, before Pipeline execution raise:

```python
SimulationValidationError(
    race_input.race_id,
    "allocation_policy",
    "strategy_identity.strategy_config.allocation_policy is required",
)
```

No hidden default, fixed-100-yen policy generation, or substitution from Pipeline config is
allowed. For a valid policy, call `build_allocation_policy_identity(policy_config)` exactly once
per `build_and_save()`; do not inject policy identity separately. Unsupported policy and budget
insufficiency remain allocator exceptions and propagate unchanged.

## Identity and Processing Order

Construct exactly one identity per valid call:

```python
identity = SimulationBetPlanIdentity(
    run_id=run_context.run_id,
    race_id=race_input.race_id,
    strategy_id=strategy_identity.strategy_id,
    strategy_config_hash=strategy_identity.strategy_config_hash,
    information_cutoff=race_input.information_cutoff,
)
```

Do not use/recompute/normalize run ID, strategy ID, hash, current time, scheduled start,
`pipeline_input.prediction_time`, DB/Repository values, whitespace, case, or timezone display.

The formal order is:

```text
1. Constructor dependency validation.
2. build_and_save race_input/budget validation.
3. Validate prediction_pipeline.config is PipelineConfig.
4. Validate Pipeline config equals StrategyIdentity config.
5. Confirm allocation policy exists.
6. Build AllocationPolicyIdentity once.
7. Build SimulationBetPlanIdentity once.
8. Call PredictionPipeline.run(race_input.pipeline_input) once.
9. Validate PipelineResult boundary.
10. Call allocator.allocate(...) once.
11. Validate BetAllocationPlan boundary.
12. Call plan_builder.build(allocation_plan=...) once.
13. Validate Snapshot boundary.
14. Call snapshot_repository.save_snapshot(snapshot=snapshot) once.
15. Return the exact Builder Snapshot object.
```

## Pipeline-result Boundary

The valid response is `PipelineResult`. Validate only:

```text
response is PipelineResult
response.bet_plan is BetPlan
all response.predictions are Prediction
every Prediction.race_id equals race_input.race_id
```

Do not validate or reconstruct strategy name, strategy class, race-entry conversion,
recommendation sorting/filtering, or `PipelineResult.recommendations` versus `BetPlan`.
Allocator/`BetAllocationPlan` own recommendation/allocation order and budget contracts; Builder
and Snapshot own final bet contracts.

Malformed response failures are `SimulationValidationError` with identifier
`prediction_pipeline` and distinct reasons:

```text
result must be a PipelineResult
bet_plan must be a BetPlan
predictions must contain Prediction values
prediction race_id does not match race_input
```

No downstream collaborator is called. A real `PipelineExecutionError` propagates as the identical
exception object.

## Allocator and Builder Boundaries

Call exactly once:

```python
allocation_plan = allocator.allocate(
    identity=identity,
    policy_identity=policy_identity,
    bet_plan=pipeline_result.bet_plan,
    budget=budget,
)
```

Valid allocator response is `BetAllocationPlan`; validate:

```python
allocation_plan.identity == identity
allocation_plan.policy_identity == policy_identity
allocation_plan.bet_plan is pipeline_result.bet_plan
allocation_plan.budget == budget
```

Malformed responses are `SimulationValidationError` with identifier `bet_stake_allocator` and
reasons `result must be a BetAllocationPlan`, `identity does not match`,
`policy_identity does not match`, `bet_plan object does not match`, or `budget does not match`.
Do not call Builder/Repository then. Delegate recommendation type/order, purchase order, stake
unit, and allocation budget rules to existing `BetAllocationPlan`. Real allocator exceptions
propagate unchanged.

Call exactly once:

```python
snapshot = plan_builder.build(allocation_plan=allocation_plan)
```

Valid Builder response is `SimulationBetPlanSnapshot`; validate identity, policy identity, and
budget equality. Malformed responses are `SimulationValidationError` with identifier
`simulation_bet_plan_builder` and reasons `result must be a SimulationBetPlanSnapshot`,
`identity does not match`, `policy_identity does not match`, or `budget does not match`. Do not
call Repository then. Delegate bet race/strategy/cutoff/stake/selection/duplicate/budget invariants
to the Snapshot model. Real Builder exceptions propagate unchanged.

## Repository, Budget, and NO_BET

Call exactly once:

```python
snapshot_repository.save_snapshot(snapshot=snapshot)
```

Ignore its return value; do not reload, retry, fallback, update, delete, or re-run Pipeline on a
conflict. On success return the same Builder Snapshot object. Propagate
`RepositoryValidationError`, `RepositoryConflictError`, and `RepositoryDataIntegrityError` as the
identical exception object.

Budget is an explicit race-level keyword-only `BetStakeBudget`. Never generate it, infer it from
recommendations, default it to 100 yen, partially buy, auto-reduce it, or obtain it from settings
or environment.

An empty `BetPlan` is a valid NO_BET path:

```text
Pipeline → allocator → empty BetAllocationPlan → Builder → empty Snapshot
→ Repository save → exact empty Snapshot return
```

Do not skip allocator/Builder/Repository, treat it as a missing snapshot, or change the supplied
budget.

## Exception Policy

| Situation | Contract |
| --- | --- |
| invalid constructor dependency | `ValueError` |
| invalid race_input/budget | `ValueError` |
| invalid Pipeline config or config mismatch | `SimulationValidationError`, `prediction_pipeline` |
| missing allocation policy | `SimulationValidationError`, `allocation_policy` |
| PipelineExecutionError | same object propagates |
| malformed Pipeline response | `SimulationValidationError`, `prediction_pipeline` |
| allocator error | same object propagates |
| malformed allocation response | `SimulationValidationError`, `bet_stake_allocator` |
| Builder error | same object propagates |
| malformed Snapshot response | `SimulationValidationError`, `simulation_bet_plan_builder` |
| Repository errors | same object propagates |

Do not add an exception class.

## Allowed Files During Implementation

- `scripts/simulation/persisted_bet_plan_service.py`
- `tests/test_persisted_bet_plan_service.py`
- `docs/LATEST_CODEX_REPORT.md`

`docs/CURRENT_PHASE.md` is not an implementation target.

## Forbidden Files and Scope

Do not change prediction modules, simulation models/validation, allocator, Builder, Snapshot,
Repository, settlement source, executor, Simulator, Summary, schema/migration, CLI, `main.py`,
settings, DB path, package exports, `database/keiba.db`, or `logs/`. Do not start Phase 4C-2d3b1i2.

## Required Tests

Add `tests/test_persisted_bet_plan_service.py` for service-unit contracts only:

- constructor type/callable/class-object rejection, injected identity, and no calls;
- direct argument failure before calls;
- normal non-empty exact immutable Pipeline input, call order/count, five-field identity, policy,
  explicit budget, `BetPlan` object identity, and exact Snapshot return;
- unequal caller strategy name versus non-empty/class-name BetPlan name succeeds, while config
  mismatch fails before Pipeline;
- missing policy fails with identifier `allocation_policy` before Pipeline;
- malformed Pipeline/allocator/Builder responses and downstream non-calls;
- NO_BET still calls allocator/Builder/Repository once and preserves budget;
- same-object propagation/no retry for Pipeline, allocator, Builder, and Repository errors;
- no forbidden dependencies/runtime Protocol checks/package export.

Run the dedicated test, relevant existing Prediction Pipeline, StrategyIdentity, allocation policy,
FixedStake allocator, allocation plan, Builder, Snapshot, Snapshot Repository Protocol, and
persisted-simulation integration tests actually present; then full pytest, source searches,
`git diff --check`, and `git status --short`.

Phase 4C-2d3b1i2 alone owns the real Pipeline + SQLite Repository + persisted settlement +
Simulator integration path. Do not change existing
`tests/test_persisted_simulation_integration.py` in this phase.

## Stop Condition

Implement only the Allowed Files. Stop on an out-of-scope need, unexpected Git change, test failure
outside scope, or missing commit approval. No stage, commit, push, review branch, or Phase 1i2 work
without a later explicit instruction.
