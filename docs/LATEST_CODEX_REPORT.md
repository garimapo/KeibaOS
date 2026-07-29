# Latest Codex Report

## Status

APPROVED_FOR_COMMIT

## Current Phase

Phase 4C-2d3b1i3a — Persisted simulation identity accessors

Base commit: `74d2443 docs: approve prediction persisted integration`

## Phase Split and Approval

Phase 4C-2d3b1i2 is formally complete. Its real Pipeline-to-persisted-simulation integration
remains the verified single-race write/read path.

The original Phase 4C-2d3b1i3 was split into:

```text
Phase 4C-2d3b1i3a — Persisted simulation identity accessors
Phase 4C-2d3b1i3b — Multi-race persisted simulation run orchestration
```

Phase 4C-2d3b1i3a is `APPROVED_FOR_COMMIT`. It is a narrow, behavior-preserving prerequisite that
adds public readonly accessors only. Phase 4C-2d3b1i3b remains unstarted.

## Identity Coherence Reassessment

The prior blocker was correctly identified but incomplete: exposing only
`PersistedSimulationBetPlanService.run_context` and `.strategy_identity` is insufficient to prove
the complete persisted simulation path before planning. The future traversal is:

```text
PersistedSimulationBetPlanService
  → run_context / strategy_identity
Simulator
  → strategy_identity / race_executor
PersistedRaceSimulationExecutor
  → strategy_identity / settlement_source
RepositoryBackedPersistedRaceSettlementSource
  → bet_source
PersistedSimulationBetSource
  → run_context
```

Already-public accessors are `Simulator.strategy_identity`, `Simulator.race_executor`,
`PersistedRaceSimulationExecutor.strategy_identity`, and
`PersistedRaceSimulationExecutor.settlement_source`.

The approved additions are four readonly properties in three production modules:

```text
PersistedSimulationBetPlanService.run_context -> SimulationRunContext
PersistedSimulationBetPlanService.strategy_identity -> StrategyIdentity
PersistedSimulationBetSource.run_context -> SimulationRunContext
RepositoryBackedPersistedRaceSettlementSource.bet_source -> SimulationBetSource
```

Every property returns the exact injected object, without copy, re-creation, collaborator calls,
SQLite, time, setter, validation, or runtime-behavior changes. `snapshot_source`, race-result
Repository, and payout Repository accessors are not added.

The blocker is therefore resolvable by 1i3a. Once it completes, 1i3b can prevalidate through public
APIs only:

```python
executor = simulator.race_executor
settlement_source = executor.settlement_source
bet_source = settlement_source.bet_source

bet_plan_service.strategy_identity is simulator.strategy_identity
simulator.strategy_identity is executor.strategy_identity
bet_plan_service.run_context is bet_source.run_context
```

Object identity, not matching values, is the proposed formal coherence contract. Private attributes,
strategy ID/hash/run-ID-only comparison, identity/context regeneration, and
`BetPlan.strategy_name` comparison remain forbidden.

## 1i3a Scope and Tests

Allowed production files are the three accessor modules. Tests extend only:

```text
tests/test_persisted_bet_plan_service.py
tests/test_persisted_simulation_bet_source.py
tests/test_repository_backed_persisted_settlement_source.py
```

Each new accessor test verifies property/type-hint contract, exact object identity on repeated
reads, zero collaborator calls while read, absence of setter/`AttributeError` on assignment, and
existing constructor/runtime behavior. No new test file is proposed.

No changes are approved for Simulator, executor, models, Protocol definitions, schema, migration,
SQLite repositories, Prediction Pipeline, CLI, `main.py`, package exports, `database/keiba.db`, or
`logs/`. `Any`, `cast`, `type: ignore`, runtime Protocol checks, copy/reconstruction, and behavior
changes are prohibited.

## Preserved 1i3b Design Draft

The later orchestration design is retained, not discarded:

```text
service: PersistedSimulationRunService
module: scripts/simulation/persisted_simulation_run_service.py
budget: budgets_by_race_id
input: prevalidate all races and all budgets before side effects
order: (scheduled_start_at, race_id)
execution: complete all Planning before one Simulator.run()
return: SimulationSummary
failure: no run-level rollback, retry, fallback, or delete compensation
persistence: successful immutable Snapshots remain; idempotent equal save/no-op, conflict fail-closed
exceptions: collaborator exception objects propagate unchanged
coverage: mixed SETTLED / NO_BET / UNSETTLED
scope: no schema, migration, or CLI
```

The adopted budget candidate remains an exact `Mapping[int, BetStakeBudget]`; common budget and a
budget-source Protocol are not selected. The run service will preserve exact input/budget objects,
not mutate caller collections, accept empty input only with an empty map, and leave settlement,
ROI, and drawdown to existing Executor/Summary behavior.

## Implementation, Verification, and Review Approval

The approved three production modules now expose only the four public readonly accessors:

```text
PersistedSimulationBetPlanService.run_context
PersistedSimulationBetPlanService.strategy_identity
PersistedSimulationBetSource.run_context
RepositoryBackedPersistedRaceSettlementSource.bet_source
```

Each accessor returns the exact constructor-injected object on repeated reads. The extended existing
test files verify the property descriptor and return type hints, identity preservation, no setter and
`AttributeError` on assignment, and zero collaborator calls while each property is read. Existing
constructor behavior, `__slots__`, and runtime methods remain unchanged; no other accessor was added.

Verification completed with the bundled Python runtime:

```text
Dedicated accessors: 57 passed, 74 subtests passed
Related persisted executor / Simulator: 135 passed, 12 subtests passed
Full suite: 2283 passed, 2 skipped, 701 subtests passed
Forbidden-dependency search in changed production and test code: no matches
git diff --check: success
```

GitHub implementation review approved review commit `fbf8afa review: add persisted simulation identity
accessors`; it is committed and pushed on
`review/4c-2d3b1i3a-identity-accessors`. The production diff is limited to the four readonly
properties listed above. Review found no production or test correction required.

The properties return their exact constructor-injected objects without copy or re-creation; they
have no setter and make no collaborator call. `__slots__`, constructor signatures, runtime methods,
validation, and exception behavior are unchanged. No migration, schema, Protocol, SQLite Repository,
or package-root export changed.

This permits Phase 4C-2d3b1i3b to prevalidate the full traversal through public APIs only:

```python
executor = simulator.race_executor
settlement_source = executor.settlement_source
bet_source = settlement_source.bet_source

bet_plan_service.strategy_identity is simulator.strategy_identity
simulator.strategy_identity is executor.strategy_identity
bet_plan_service.run_context is bet_source.run_context
```

Private-attribute access is no longer needed for that coherence validation. Phase 4C-2d3b1i3b and
1i4 onward remain unstarted; base-branch integration is pending. `database/keiba.db` and `logs/`
remain outside scope.
