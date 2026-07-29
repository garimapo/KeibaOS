# Latest Codex Report

## Status

READY_FOR_REVIEW

## Current Phase

Phase 4C-2d3b1i5a — SQLite persisted simulation application runner

Base commit: `dfeb34d docs: approve SQLite persisted simulation composition root`

Branch: `feature/ver0.8-simulator`

## Implementation

Added `scripts/simulation/sqlite_persisted_simulation_application.py` with the sole public API:

```python
run_sqlite_persisted_simulation(
    *,
    database_path: str | Path,
    run_context: SimulationRunContext,
    strategy_identity: StrategyIdentity,
    prediction_pipeline: PredictionPipeline,
    race_inputs: Sequence[SimulationRaceInput],
    budgets_by_race_id: Mapping[int, BetStakeBudget],
) -> SimulationSummary
```

The runner validates the database path, exact production object types, and input container types
before any SQLite side effect. It preserves the original database-path text after validation, takes
one tuple/dict snapshot of caller collections without copying their race-input or budget objects,
then delegates detailed race/budget validation to the existing run service.

After pre-open validation it opens exactly one `sqlite3.connect()` connection, calls
`apply_migrations(connection)` once, calls the Phase 4C-2d3b1i4 composition factory once, calls
the returned service once, returns that exact Summary, and closes the runner-owned connection in a
`try/finally`. It adds no `except`, retry, fallback, transaction handling, manual component
construction, Snapshot handling, or metric calculation. Connect, migration, composition, and run
exceptions remain unwrapped.

## Test Coverage

Added `tests/test_sqlite_persisted_simulation_application.py`.

- API/type-hint and AST checks prove the production module has only the formal function, one
  connect/migration/factory/run/close call site, a `try/finally`, and no `except` handler.
- Pre-open tests cover all required invalid path, exact production object, and container inputs,
  proving no SQLite file is created.
- The pending-migration test starts with only parent `races`/`horses`, lets the runner apply v008/v009,
  and verifies an empty Summary plus migration registry and tables after reopening the DB.
- The file-backed real-component integration persists a 100-yen WIN plan, reads complete result and
  payout 300, and returns the required settled Summary: investment 100, payout 300, profit 200,
  ROI 300, hit rates 100, and maximum drawdown 0. It also verifies caller collection non-mutation,
  persisted Snapshot/budget/bet/entry data, migration versions, and database usability.
- The migration failure fixture is the approved unknown future version `999/future_migration`.
  `apply_migrations()` fails before composition/run; the runner does not wrap the error and the file
  is reconnectable afterward.
- The run-failure fixture uses duplicate `race_id`; migrations and composition complete, the existing
  run-service validation fails without wrapping, no Snapshot is saved, and the file is reconnectable.

## Verification

These are Codex local results, not GitHub CI results. The bundled Codex Python runtime was used
because `python` is not present on PATH.

```text
Dedicated: 8 passed, 49 subtests passed
Related: 334 passed, 312 subtests passed
Full suite: 2312 passed, 2 skipped, 831 subtests passed
Production forbidden-pattern search: 0 matches
New-test forbidden-pattern search: 0 matches
git diff --check: success
```

The requested `tests/test_migration_runner.py` does not exist; the related suite used the existing
`tests/test_simulation_migrations.py` instead.

Only these new implementation files were added:

```text
scripts/simulation/sqlite_persisted_simulation_application.py
tests/test_sqlite_persisted_simulation_application.py
```

Existing production/tests, the 1i4 composition root, migrations, schema, `scripts/database.py`,
`main.py`, CLI, and package-root exports are unchanged. Phase 4C-2d3b1i5b/1i5c remain unstarted.
`database/keiba.db` and `logs/` are outside scope.

No file has been staged, committed, pushed, or placed on a review branch for Phase 4C-2d3b1i5a.

blocker: none
