# Current Phase

## Status

APPROVED_FOR_CODEX

## Phase

Phase 4C-2d3b1i3b - Multi-race persisted simulation run orchestration

## Base Commit

`0d2d8cd docs: approve persisted simulation identity accessors`

## Branch

`feature/ver0.8-simulator`

## Objective

Add an application service that prevalidates every `SimulationRaceInput`, every supplied budget,
and the persisted component composition before side effects. It fixes the official order by
`(scheduled_start_at, race_id)`, saves every race's Snapshot through the existing planning service,
then calls the existing `Simulator` exactly once and returns its exact `SimulationSummary`.

```text
validate all input, budgets, and composition
-> order by (scheduled_start_at, race_id)
-> save all race Snapshots
-> call Simulator.run() once after all Planning succeeds
-> return the exact SimulationSummary
```

## Formal Production API

New module: `scripts/simulation/persisted_simulation_run_service.py`

```python
class PersistedSimulationRunService:
    __slots__ = ("_bet_plan_service", "_simulator")

    def __init__(
        self,
        *,
        bet_plan_service: PersistedSimulationBetPlanService,
        simulator: Simulator,
    ) -> None:
        ...

    def run(
        self,
        *,
        race_inputs: Sequence[SimulationRaceInput],
        budgets_by_race_id: Mapping[int, BetStakeBudget],
    ) -> SimulationSummary:
        ...
```

The constructor retains the exact two injected objects. It adds no domain result model, run-context
or strategy-identity argument, budget-source Protocol, common budget, Repository/Pipeline/allocator
construction, public property, or package-root export.

## Constructor and Composition Contract

Require exact concrete types and raise `ValueError` for any violation:

```text
type(bet_plan_service) is PersistedSimulationBetPlanService
type(simulator) is Simulator
type(simulator.race_executor) is PersistedRaceSimulationExecutor
type(executor.settlement_source) is RepositoryBackedPersistedRaceSettlementSource
type(settlement_source.bet_source) is PersistedSimulationBetSource
```

Inspect the chain only through public APIs:

```python
executor = simulator.race_executor
settlement_source = executor.settlement_source
bet_source = settlement_source.bet_source

bet_plan_service.strategy_identity is simulator.strategy_identity
simulator.strategy_identity is executor.strategy_identity
bet_plan_service.run_context is bet_source.run_context
```

The three identity checks use `is`, not value equality. Recommended `ValueError` reasons are:

```text
bet_plan_service must be a PersistedSimulationBetPlanService
simulator must be a Simulator
simulator.race_executor must be a PersistedRaceSimulationExecutor
executor.settlement_source must be a RepositoryBackedPersistedRaceSettlementSource
settlement_source.bet_source must be a PersistedSimulationBetSource
bet_plan_service.strategy_identity must be simulator.strategy_identity
simulator.strategy_identity must be executor.strategy_identity
bet_plan_service.run_context must be bet_source.run_context
```

The constructor makes no Pipeline, Repository, Source, or Executor call. `run()` repeats the full
composition-coherence check before Planning; a later broken composition raises `ValueError` before
any Snapshot save. Private attributes, regenerated identities or contexts, and value-only identity
comparisons are forbidden.

## Input Contract and Validation Order

`race_inputs` accepts only `collections.abc.Sequence`, excluding `str`, `bytes`, `bytearray`,
generators, `Mapping`, and other non-Sequences. Snapshot it once as a tuple without mutating the
caller collection. Before collaborator calls, every element must be a `SimulationRaceInput` and
race IDs must be unique. Empty sequences, mixed target dates, shared information cutoffs, lists,
and tuples are valid. Do not reimplement `SimulationRaceInput`'s own date, audit, or Pipeline-input
validation.

`budgets_by_race_id` must be a `collections.abc.Mapping`. It may be snapshotted once to an ordinary
dict, but each exact `BetStakeBudget` object is preserved. Keys are positive non-bool `int`; values
are `BetStakeBudget`; and its key set exactly equals the input race-ID set. Missing, extra, bool,
non-int, zero/negative keys, and non-budget values are rejected. An empty input is valid only with
an empty budget mapping.

Complete the following before the first `build_and_save()`:

```text
1. race_inputs container validation
2. race_inputs tuple snapshot
3. all element validation
4. duplicate race-ID validation
5. budget mapping validation
6. all key/value validation
7. exact race-ID-set match
8. composition coherence revalidation
9. official sort
```

Every service-detected constructor or direct-input violation is `ValueError`.

## Official Ordering and Processing

```python
ordered_inputs = tuple(
    sorted(
        race_inputs,
        key=lambda race_input: (
            race_input.scheduled_start_at,
            race_input.race_id,
        ),
    )
)
```

Snapshot saves and the tuple supplied to `Simulator` use this same order. Equal starts use ascending
race ID. Caller order is not execution order; caller collections are not mutated; each original
`SimulationRaceInput` object is forwarded by exact identity. Datetime comparison is delegated to
the existing model. Summary settlement ordering, ROI, hit rates, and maximum drawdown remain
existing Summary responsibilities.

### Phase A - Planning

For every ordered race, call exactly once:

```python
bet_plan_service.build_and_save(
    race_input=race_input,
    budget=budgets[race_input.race_id],
)
```

Forward the exact race and budget objects. Save a Snapshot even for NO_BET. Do not separately run
the Pipeline, reload a Repository, retain Snapshots in this service, return Snapshots, or repeat
existing Snapshot identity/policy/budget validation.

### Phase B - Simulation

Only after all Planning succeeds, call exactly once:

```python
return simulator.run(race_inputs=ordered_inputs)
```

Forward the exact ordered tuple and exact returned `SimulationSummary`. Do not copy, wrap, rebuild,
or independently validate Summary data; do not recalculate settlement status, ROI, hit rates, or
drawdown.

For `race_inputs=()` and `budgets_by_race_id={}`, make zero Planning calls and call
`Simulator.run(race_inputs=())` once. A non-empty budget mapping with empty inputs is rejected
before side effects.

## Failure and Persistence Semantics

If Planning for race N raises, Snapshots for successful races 1 through N-1 remain immutable; do
not plan subsequent races, call `Simulator.run`, wrap the exception, roll back, delete Snapshots,
compensate, retry, or use a fallback. Propagate the identical exception object.

If `Simulator.run` raises after all saves, persisted Snapshots remain, no Summary is returned, and
the same exception object propagates with no retry. A caller may rerun from the beginning; existing
same-identity/same-content persistence remains an idempotent no-op, and differing content remains
`RepositoryConflictError`. No resume API is introduced.

This phase checks only the run-context object, strategy-identity object, and concrete persisted
component chain. It does not check write-Repository/read-Source object identity, SQLite connection,
database path, or transaction domain; those are Phase 4C-2d3b1i4 composition-root responsibilities.
Do not add Repository or connection accessors.

## Mixed Run Integration Contract

Add one three-race in-memory SQLite scenario using one `StrategyIdentity` and one `StrategyConfig`:

```text
race A: one purchase, SETTLED
race B: non-zero budget, empty Snapshot, NO_BET
race C: one purchase, missing result, UNSETTLED
```

All three Snapshots must be created through `PersistedSimulationRunService.run()`. The NO_BET
Snapshot retains its budget and requires no result/payout lookup. The UNSETTLED bet remains in
`bet_count`; settlement investment and ROI are settled-only. The service does not recalculate
statuses or Summary fields. Use the real persisted components and in-memory SQLite. Do not manually
save a Snapshot or `BetAllocationPlan` in the new scenario; existing manual integration and 1i2
real-Pipeline scenarios stay unchanged. Deterministic collaborators inside the exact
`PredictionPipeline` are allowed, but a Pipeline subclass, `Pipeline.run` patch, prebuilt
`PipelineResult`, per-race StrategyConfig, and per-race StrategyIdentity are forbidden.

Expected summary:

```text
race_count = 3
settled_race_count = 1
no_bet_race_count = 1
unsettled_race_count = 1
settled_purchase_race_count = 1
bet_count = 2
settled_bet_count = 1
hit_bet_count = 1
hit_race_count = 1
investment = 100
payout = 300
profit = 200
roi = Decimal("300")
bet_hit_rate = Decimal("100")
race_hit_rate = Decimal("100")
maximum_drawdown = 0
```

The single Win `by_bet_type` summary is likewise: bet count 2, settled/hit bet count 1,
investment 100, payout 300, profit 200, ROI 300, and bet hit rate 100. If an existing fixture or
Summary rule conflicts, report a blocker instead of changing production behavior.

## Allowed Files

```text
scripts/simulation/persisted_simulation_run_service.py
tests/test_persisted_simulation_run_service.py
tests/test_persisted_simulation_integration.py
docs/LATEST_CODEX_REPORT.md
```

`docs/CURRENT_PHASE.md` is not an implementation target.

## Forbidden Files and Patterns

Do not modify existing simulation production modules, models, Protocols, migrations, schema, SQLite
Repositories, Prediction production modules, CLI, `main.py`, README, package `__init__`,
`database/keiba.db`, or `logs/`.

Do not add `Any`, `cast`, `type: ignore`, `runtime_checkable`, runtime Protocol `isinstance`, broad
`except`, `datetime.now`, `date.today`, network, `sqlite3`, Repository/connection construction,
migration execution, printing, logging, argparse, JSON output, or package-root exports. Ordinary
`collections.abc.Mapping` and `Sequence` `isinstance` checks are allowed.

Tests must not subclass or fake these five concrete production components:

```text
PersistedSimulationBetPlanService
Simulator
PersistedRaceSimulationExecutor
RepositoryBackedPersistedRaceSettlementSource
PersistedSimulationBetSource
```

Use exact production objects and inject Recording fixtures only into their existing structural
collaborators. Do not subclass this run service, patch `build_and_save` or `Simulator.run`, access
private fields for identity validation, or manually save test Snapshots.

## Required Tests and Checks

```powershell
python -m pytest tests/test_persisted_simulation_run_service.py -q
python -m pytest tests/test_persisted_simulation_integration.py -q
python -m pytest tests/test_persisted_bet_plan_service.py tests/test_persisted_simulation_bet_source.py tests/test_repository_backed_persisted_settlement_source.py tests/test_persisted_race_simulation_executor.py tests/test_simulator_contract.py tests/test_persisted_simulation_run_service.py tests/test_persisted_simulation_integration.py -q
python -m pytest -q
git diff --check
git status --short
```

The unit contract covers signature/type hints, keyword-only APIs, slots, exact dependency identity,
zero constructor calls, all concrete-chain and identity failures, run-time revalidation, all input
and budget validation, empty runs, non-mutation, official order, exact forwarding, one Planning call
per race, two-pass ordering, Planning/Simulator failure stop behavior and exception identity, and no
Snapshot/Summary reconstruction.

## Stop Condition

Stop rather than implementing if a required behavior needs an out-of-scope file, an existing
contract conflicts, a required test fails outside scope, an unexpected Git change appears, or a
commit/review approval is required. Do not stage, commit, push, or create a review branch without
later explicit approval.
