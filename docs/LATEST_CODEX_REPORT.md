# Latest Codex Report

## Status

READY_FOR_REVIEW

## Current Phase

Phase 4C-2d3b1i4 — SQLite persisted simulation composition root

Base commit: `8b86654 docs: approve persisted simulation run orchestration`

Branch: `feature/ver0.8-simulator`

## Implementation

Added `scripts/simulation/sqlite_persisted_simulation_composition.py` with the sole public
factory:

```python
build_sqlite_persisted_simulation_run_service(
    *,
    connection: sqlite3.Connection,
    run_context: SimulationRunContext,
    strategy_identity: StrategyIdentity,
    prediction_pipeline: PredictionPipeline,
) -> PersistedSimulationRunService
```

The factory is caller-connection-owned: it neither opens, closes, commits, rolls back, begins a
transaction, knows a DB path, applies migrations, nor duplicates schema readiness. It first
validates the connection, exact run context/strategy identity/pipeline/PipelineConfig, exact
Pipeline StrategyConfig identity, the required allocation policy, and exact allocation-policy type.

The composition uses one exact Snapshot Repository for the planning writer and persisted bet reader,
and supplies one exact connection to Snapshot, race-entry, race-result, and payout adapters. It
constructs the existing resolver, plan builder, fixed-stake allocator, planning service, bet source,
settlement source, executor, Simulator, and final run service without copying or regenerating
identity/configuration objects.

Construction remains construction-only: no Pipeline, allocation, builder, Snapshot persistence/load,
settlement lookup, Simulator, or service run occurs. Direct validation failures are `ValueError` with
zero SQLite statements; component constructor failures remain unwrapped, with no retry, fallback,
cleanup, rollback, or connection lifecycle intervention.

## Test Coverage

Added `tests/test_sqlite_persisted_simulation_composition.py`. It covers the factory API/type hints,
invalid direct inputs and subclasses, PipelineConfig/StrategyConfig identity, allocation-policy
requirements and fixed-stake failures, exact private wiring inspection, single connection and shared
Snapshot Repository, construction-only behavior, and forbidden production lifecycle/runtime patterns.

The in-memory end-to-end scenario uses a single caller connection, real `PredictionPipeline`, real
fixed-stake allocator, real resolver and SQLite repositories. It seeds parent race/horse data and
applies migrations in test setup only; it then saves a Snapshot solely through
`PersistedSimulationRunService.run()`. A complete one-race result plus single-win payout of 300
returns a SETTLED Summary:

```text
race_count = 1
settled_race_count = 1
no_bet_race_count = 0
unsettled_race_count = 0
settled_purchase_race_count = 1
bet_count = 1
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

The test confirms race-entry resolution, Snapshot writer-to-reader round trip, internal result and
payout reads, a 100 budget with one bet, and a usable caller connection with no active transaction
after the run. Private inspection is used only in this composition test.

## Verification

These are Codex local results, not GitHub CI results.

```text
Dedicated: 8 passed, 30 subtests passed
Related: 304 passed, 253 subtests passed
Full suite: 2304 passed, 2 skipped, 782 subtests passed
Production forbidden-pattern search: no matches
New-test diff forbidden-pattern search: no matches
git diff --check: success
```

The related executor test was `tests/test_persisted_race_simulation_executor.py`. Existing
production/tests, `docs/CURRENT_PHASE.md`, migrations, schema, `scripts/database.py`, `main.py`,
CLI, and package-root exports are unchanged.

Production change candidate:

```text
scripts/simulation/sqlite_persisted_simulation_composition.py
```

Test change candidate:

```text
tests/test_sqlite_persisted_simulation_composition.py
```

Phase 4C-2d3b1i5 and later phases remain unstarted. `database/keiba.db` and `logs/` are outside
scope.

blocker: none
