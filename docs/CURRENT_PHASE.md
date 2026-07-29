# Current Phase

## Status

APPROVED_FOR_CODEX

## Phase

Phase 4C-2d3b1i5a — SQLite persisted simulation application runner

## Base Commit

`dfeb34d docs: approve SQLite persisted simulation composition root`

## Branch

`feature/ver0.8-simulator`

## Objective

Add the application boundary that owns a database path and one SQLite connection lifecycle:

```text
database path
-> sqlite3.connect()
-> apply_migrations()
-> build_sqlite_persisted_simulation_run_service()
-> PersistedSimulationRunService.run()
-> connection.close()
-> SimulationSummary
```

The caller supplies the run context, identity, pipeline, race inputs, and budgets. This phase does
not add CLI, request/config-file parsing, DB-backed race selection, or Summary rendering.

## Allowed Files

```text
scripts/simulation/sqlite_persisted_simulation_application.py
tests/test_sqlite_persisted_simulation_application.py
docs/LATEST_CODEX_REPORT.md
```

`docs/CURRENT_PHASE.md` is approved contract documentation and is not an implementation target.

## Formal Production API

New module: `scripts/simulation/sqlite_persisted_simulation_application.py`

```python
from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from scripts.prediction.prediction_pipeline import PredictionPipeline
from scripts.simulation.models import (
    SimulationRaceInput,
    SimulationRunContext,
    SimulationSummary,
    StrategyIdentity,
)
from scripts.simulation.stake_allocation import BetStakeBudget


def run_sqlite_persisted_simulation(
    *,
    database_path: str | Path,
    run_context: SimulationRunContext,
    strategy_identity: StrategyIdentity,
    prediction_pipeline: PredictionPipeline,
    race_inputs: Sequence[SimulationRaceInput],
    budgets_by_race_id: Mapping[int, BetStakeBudget],
) -> SimulationSummary:
    ...
```

The module contains no class, dataclass, request bundle, connection wrapper, custom repository,
CLI parser, JSON loader, or package-root export.

## Direct Input Validation

Before opening a connection validate, in order:

1. `database_path` is `str` or `pathlib.Path`; validate `str(database_path)` as non-empty,
   non-whitespace, and NUL-free. Reject `None`, bytes, bytearray, int, bool, arbitrary objects,
   empty, whitespace-only, and NUL paths as
   `ValueError("database_path must be a non-empty path")`.
2. `type(run_context) is SimulationRunContext`, otherwise
   `ValueError("run_context must be a SimulationRunContext")`.
3. `type(strategy_identity) is StrategyIdentity`, otherwise
   `ValueError("strategy_identity must be a StrategyIdentity")`.
4. `type(prediction_pipeline) is PredictionPipeline`, otherwise
   `ValueError("prediction_pipeline must be a PredictionPipeline")`.
5. `race_inputs` is a `collections.abc.Sequence`, otherwise
   `ValueError("race_inputs must be a Sequence")`; reject str, bytes, bytearray, mappings,
   generators, and other non-Sequence values.
6. `budgets_by_race_id` is a `collections.abc.Mapping`, otherwise
   `ValueError("budgets_by_race_id must be a Mapping")`.

After container validation, but still before open, take caller-safe snapshots:

```python
race_input_values = tuple(race_inputs)
budget_values = dict(budgets_by_race_id)
```

Do not mutate caller collections. Delegate race-input type, duplicate race ID, budget key/value,
positive-budget key set, and budget coverage validation unchanged to
`PersistedSimulationRunService.run()`. Direct validation failure is `ValueError` with zero open,
migration, composition, or run calls.

## Connection Lifecycle and Migration Readiness

After pre-open validation, own exactly one connection:

```python
connection = sqlite3.connect(database_path_value)
```

Close it exactly once with `finally` or `contextlib.closing` on success and every post-open failure.
Do not use `scripts.database.get_connection`, `scripts.database.DB_PATH`, a global/caller reusable
connection, another connection, or hard-coded `database/keiba.db`. Do not wrap connect errors.

After open and before component construction, call exactly once:

```python
apply_migrations(connection)
```

This phase establishes simulation migration readiness only. Do not call `create_tables`, modify
migration registration/schema SQL, add legacy migration logic, inspect parent race/horse schema, or
duplicate migration-runner logic. Migration errors propagate unchanged; the connection still closes.
The runner itself never begins, commits, or rolls back transactions.

## Composition and Run

After migration succeeds, call the Phase 4C-2d3b1i4 factory once with the one connection and exact
run-context, identity, and pipeline objects. Then call its returned service once:

```python
summary = service.run(
    race_inputs=race_input_values,
    budgets_by_race_id=budget_values,
)
return summary
```

Return the exact Summary. Do not copy/rebuild/inspect it, construct individual collaborators,
reload snapshots, query settlement, calculate metrics, retry, fallback, resume, compensate, update,
or delete.

## Failure Semantics

- Invalid direct input: `ValueError`; zero open/migration/factory/run calls.
- Connect failure: propagate the original exception; no retry/fallback.
- Migration, factory, or run failure: propagate the same exception object; no Summary; close the
  owned connection once.
- No wrapping/translation, retry, fallback, rollback, compensation, or extra transaction handling.

## Allowed and Forbidden Runtime Operations

Allowed production operations are only `sqlite3.connect`, `apply_migrations`, the Phase 4C-2d3b1i4
factory, `PersistedSimulationRunService.run`, and connection close. Do not use current time, UUID or
run/dataset/git ID generation, network, logging, print, argparse, JSON/config-file reading, race DB
queries to create inputs, or package-root exports.

## Required Tests

Add `tests/test_sqlite_persisted_simulation_application.py` covering:

- sole module/function API, exact keyword-only six-argument signature/type hints, return type, and
  no class/request bundle/package export;
- all invalid direct values before open, including exact production types and invalid containers,
  proving zero temporary-file/SQLite side effects;
- caller list/tuple/mapping non-mutation, tuple/dict snapshot forwarding, exact race-input/budget
  object identity, and delegation of detailed collection validation to the run service;
- file-backed end-to-end execution: setup creates parent race/horse schema, applies migrations,
  inserts fixture/result/complete WIN payout 300, commits and closes; the runner reapplies migrations
  idempotently and returns the one-race settled Summary with investment 100, payout 300, profit 200,
  ROI 300, and maximum drawdown 0;
- fresh-connection verification of persisted Snapshot, budget 100, one bet, race-entry resolution,
  migration versions v008/v009, and database usability;
- failure-close tests using a real SQLite file and the existing migration runner, without mocks or
  patches. For migration failure, the fixture creates `schema_migrations`, records unknown future
  version `999` named `future_migration` with `2026-08-05T00:00:00+00:00`, commits, and closes
  before the runner opens the file. Confirm that `apply_migrations()` raises its unknown-future-
  version error without wrapping, composition and run do not occur, the runner-owned connection
  closes, and the same file can be opened again. For run failure, use a normally migrated database
  and one representative existing run-service validation failure (for example duplicate `race_id`,
  missing/extra budget key, or invalid budget value). Confirm migration and composition succeed,
  run fails without wrapping, the runner-owned connection closes, and the same file is reusable; and
- source checks banning `get_connection`, `DB_PATH`, `database/keiba.db`, `create_tables`, clocks,
  UUID, network, logging, print, argparse, JSON, file open, broad except, runtime Protocol checks,
  `Any`, `cast`, `type: ignore`, and package-root export. The intentional `sqlite3.connect`,
  `apply_migrations`, close, and `finally`/closing are allowed.

Run the dedicated test, relevant application/composition/run-service/persisted-integration tests,
the full suite, required source searches, `git diff --check`, and `git status --short`.

## Forbidden Files and Future Scope

Do not modify existing production/tests, the 1i4 composition root, migrations, schema,
`scripts/database.py`, `main.py`, CLI, models, Protocols, repositories, prediction code, or package
`__init__` files. Never add `target_race_count`. Never stage/commit `database/keiba.db`, `logs/`, or
its contents.

Future phases are separate:

```text
Phase 4C-2d3b1i5b — persisted simulation request/config loading
Phase 4C-2d3b1i5c — persisted simulation CLI and summary output
```

## Stop Condition

After implementation and verification, set the report to `READY_FOR_REVIEW` and stop. Do not stage,
commit, push, create a review branch, start 1i5b/1i5c, or introduce CLI/request-loading behavior.

blocker: none
