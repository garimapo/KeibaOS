# Current Phase

## Status

APPROVED_FOR_CODEX

## Phase

Phase 4C-2d3b1i4 — SQLite persisted simulation composition root

## Base Commit

`8b86654 docs: approve persisted simulation run orchestration`

## Branch

`feature/ver0.8-simulator`

## Objective

Build one caller-owned `sqlite3.Connection` into the exact persisted simulation production chain:

```text
PredictionPipeline
-> PersistedSimulationBetPlanService
-> SQLite snapshot write/read
-> SQLite result/payout read
-> PersistedRaceSimulationExecutor
-> Simulator
-> PersistedSimulationRunService
```

The composition root guarantees backend coherence: one exact Snapshot Repository object for writer
and reader, and one exact connection object for Snapshot, race-entry, result, and payout adapters.

## Allowed Files

```text
scripts/simulation/sqlite_persisted_simulation_composition.py
tests/test_sqlite_persisted_simulation_composition.py
docs/LATEST_CODEX_REPORT.md
```

`docs/CURRENT_PHASE.md` is an approved contract, not an implementation target.

## Formal Production API

New module: `scripts/simulation/sqlite_persisted_simulation_composition.py`

```python
from __future__ import annotations

import sqlite3

from scripts.prediction.prediction_pipeline import PredictionPipeline
from scripts.simulation.models import SimulationRunContext, StrategyIdentity
from scripts.simulation.persisted_simulation_run_service import (
    PersistedSimulationRunService,
)


def build_sqlite_persisted_simulation_run_service(
    *,
    connection: sqlite3.Connection,
    run_context: SimulationRunContext,
    strategy_identity: StrategyIdentity,
    prediction_pipeline: PredictionPipeline,
) -> PersistedSimulationRunService:
    ...
```

Return only the exact constructed `PersistedSimulationRunService`. Do not add a class, component
bundle, connection wrapper, context manager, close/run method, CLI adapter, or package-root export.

## Direct Validation

Before component construction or SQLite statements, validate in this order:

1. `isinstance(connection, sqlite3.Connection)`; otherwise
   `ValueError("connection must be sqlite3.Connection")`. Connection subclasses are valid.
2. `type(run_context) is SimulationRunContext`; otherwise
   `ValueError("run_context must be a SimulationRunContext")`.
3. `type(strategy_identity) is StrategyIdentity`; otherwise
   `ValueError("strategy_identity must be a StrategyIdentity")`.
4. `type(prediction_pipeline) is PredictionPipeline`; otherwise
   `ValueError("prediction_pipeline must be a PredictionPipeline")`.
5. `type(prediction_pipeline.config) is PipelineConfig`; otherwise
   `ValueError("prediction_pipeline.config must be a PipelineConfig")`.
6. Require exact identity:
   `prediction_pipeline.config.strategy_config is strategy_identity.strategy_config`; otherwise
   `ValueError("prediction_pipeline.config.strategy_config must be strategy_identity.strategy_config")`.
7. Require `strategy_identity.strategy_config.allocation_policy`. `None` raises
   `ValueError("strategy_identity.strategy_config.allocation_policy is required")`. Require exact
   `AllocationPolicyConfig` type, otherwise `ValueError("allocation_policy must be an AllocationPolicyConfig")`.

Never copy or regenerate the run context, identity, strategy config, PipelineConfig, or allocation
policy. Delegate policy-detail validation and unsupported-policy failures to
`FixedStakeBetAllocator` unchanged.

## Required Construction and Object Coherence

After validation, construct exactly once and wire in this order:

```python
snapshot_repository = SQLiteSimulationBetPlanSnapshotRepository(connection=connection)
race_entry_source = SQLiteRaceEntrySource(connection=connection)
selection_resolver = RepositoryBackedRaceEntrySelectionResolver(
    race_entry_source=race_entry_source,
)
plan_builder = SimulationBetPlanBuilder(selection_resolver=selection_resolver)
allocator = FixedStakeBetAllocator(policy_config=policy_config)
bet_plan_service = PersistedSimulationBetPlanService(
    run_context=run_context,
    strategy_identity=strategy_identity,
    prediction_pipeline=prediction_pipeline,
    allocator=allocator,
    plan_builder=plan_builder,
    snapshot_repository=snapshot_repository,
)
bet_source = PersistedSimulationBetSource(
    run_context=run_context,
    snapshot_source=snapshot_repository,
)
race_result_repository = SQLiteRaceResultRepository(connection=connection)
payout_repository = SQLitePayoutRepository(connection=connection)
settlement_source = RepositoryBackedPersistedRaceSettlementSource(
    bet_source=bet_source,
    race_result_repository=race_result_repository,
    payout_repository=payout_repository,
)
executor = PersistedRaceSimulationExecutor(
    strategy_identity=strategy_identity,
    settlement_source=settlement_source,
)
simulator = Simulator(strategy_identity=strategy_identity, race_executor=executor)
return PersistedSimulationRunService(
    bet_plan_service=bet_plan_service,
    simulator=simulator,
)
```

Planning and Simulator receive the same `StrategyIdentity` object; planning and bet reader receive
the same `SimulationRunContext` object; writer and reader receive the same Snapshot Repository
object; every SQLite adapter receives the same exact connection. Do not create another connection
or Snapshot Repository. Leave final persisted-chain identity validation to the returned run-service
constructor.

## Caller-Owned Connection and Construction-Only Semantics

The caller creates, prepares, commits/rolls back, and closes the connection. The factory must not
open/close/commit/rollback a connection, begin a transaction, know a DB path, apply migrations, or
duplicate schema-readiness validation. Missing schema fails closed only when an existing adapter is
actually used.

Allowed constructor work is existing SQLite adapter constructor validation, including its existing
foreign-key PRAGMA check. The factory must not call Pipeline, allocator, builder, Snapshot save/load,
result/payout lookup, executor, Simulator, or run service. It must not use current time, network,
logging, print, retry, fallback, cleanup, or compensation.

Direct validation failures construct no component and issue no SQLite statement. Existing component
constructor exceptions propagate as the same object, without wrapping, retry, fallback, rollback, or
connection lifecycle intervention.

## Required Tests

Add `tests/test_sqlite_persisted_simulation_composition.py` covering:

- API import/name, keyword-only signature/type hints, and absence of new class/bundle;
- all direct validation cases, with a trace callback proving zero statements for pure validation;
- one exact connection / one exact Snapshot Repository wiring proof (test-only private inspection);
- construction-only behavior: no save/load/lookups/Pipeline work, no transaction start, and caller
  connection remains usable/open;
- source checks excluding lifecycle, migration, path, clock, network, logging, print, and export
  patterns; and
- one in-memory end-to-end route using real `PredictionPipeline`, fixed stake 100, migrations only
  in test setup, complete race result plus win payout 300, and a settled one-race Summary with
  investment 100, payout 300, profit 200, ROI 300, maximum drawdown 0. Verify entry resolution,
  Snapshot writer/reader round trip, result/payout internal reads, and caller connection usability.

Run the dedicated test, relevant contracts, full `pytest`, forbidden-pattern search,
`git diff --check`, and `git status --short`. Record exact outcomes.

## Forbidden Files and Patterns

Do not modify existing production components, repositories, models, Protocols, prediction modules,
migrations, schema, `scripts/database.py`, `main.py`, CLI, README, or package `__init__` files.
Never add `target_race_count`.

Forbidden production patterns include `Any`, `cast`, `type: ignore`, runtime Protocol checks, broad
`except`, `sqlite3.connect`, `get_connection`, `DB_PATH`, `database/keiba.db`, migrations, current
time, network, requests, logging, print, argparse, JSON output, package-root export, or connection
lifecycle calls. New tests may use only `sqlite3.connect(":memory:")` and `apply_migrations` for
test setup; they may not patch the factory or component constructors.

Never stage or commit `database/keiba.db`, `logs/`, or its contents.

## Stop Condition

After implementation and all required verification, update `docs/LATEST_CODEX_REPORT.md` to
`READY_FOR_REVIEW` and stop. Do not stage, commit, push, create a review branch, start Phase
4C-2d3b1i5, or introduce DB-path/CLI ownership.

blocker: none
