# Latest Codex Report

## Status

APPROVED_FOR_COMMIT

## Current Phase

Phase 4C-2d3b1i4 — SQLite persisted simulation composition root

Base commit: `8b86654 docs: approve persisted simulation run orchestration`

Base branch: `feature/ver0.8-simulator`

Review branch: `review/4c-2d3b1i4-sqlite-composition-root`

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
専用: 8 passed, 30 subtests passed
関連: 304 passed, 253 subtests passed
全体: 2304 passed, 2 skipped, 782 subtests passed
禁止パターン検索: 該当なし
git diff --check: 成功
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

## GitHub Review Approval

GitHub上の実装レビューは完了し、review commit
`32f9785 review: add SQLite persisted simulation composition root` を確認済みです。review
branchはoriginへcommit・push済みであり、production implementationとtest coverageは承認されました。
production correction・test correctionは不要で、blockerはありません。base branch integrationは未実施です。

承認済みのproduction契約は、`build_sqlite_persisted_simulation_run_service`がkeyword-onlyの
4引数を受け、caller-ownedの`sqlite3.Connection`を使うことです。direct input validation、exact
`PipelineConfig`、Pipelineの`StrategyConfig`へのexact object identity、required exact
`AllocationPolicyConfig`を検証します。unsupported fixed-stake policyはallocatorへ委譲します。
Snapshot Repositoryは1個だけを構築し、writerとreaderが同一objectを共有します。すべてのSQLite
adapterは同一connection object、構成要素は同一`SimulationRunContext`と同一`StrategyIdentity`を
共有します。factoryはconstruction-onlyで、migration/schema、connection open/close/commit/rollbackを
担わず、component constructor例外をwrapせず、exactな`PersistedSimulationRunService`を返します。

承認済みtest coverageは、正式module/factory API/type hints、factory以外のfunction/classなし、connection
subclass許可、run context・strategy identity・pipeline subclass拒否、invalid `PipelineConfig`、equal-value
別`StrategyConfig`拒否、allocation policyのNone/不正型拒否、unsupported policy name/version/parameter、
direct validation failure時のSQL statement 0、single connectionとshared Snapshot Repositoryのprivate
wiring、construction時のPRAGMAのみ、lifecycle/migration/runtime禁止パターン、in-memory SQLite end-to-end、
Snapshot writer-to-reader round trip、race-entry解決、Result/Payout読込み、100円投資・300円払戻のSETTLED
Summary、run後のconnection利用可能、transactionなしです。

上記の検証結果はCodexローカル実行結果であり、GitHub CIによる独立実行結果ではありません。

Phase 4C-2d3b1i5以降は未着手です。DB path、connection lifecycle、migration readiness、CLIは1i5の責務です。
migration、schema、`scripts/database.py`、`main.py`、CLI、package-rootは変更していません。
`database/keiba.db`と`logs/`は対象外です。

blocker: none
