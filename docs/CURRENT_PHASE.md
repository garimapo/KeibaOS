# Current Phase

## Status

APPROVED_FOR_CODEX

## Phase

Phase 4C-2d3b1h — Persisted simulation composition and integration

## Base Commit

`46d1d74 docs: approve repository backed persisted settlement source`

## Branch

`feature/ver0.8-simulator`

## Adopted Approach

Adopt approach A: compose existing components directly inside the integration test. Do not add a
production composition root, factory, public API, wrapper, adapter, or package-root export. All
required components already connect through their existing constructors; a factory would enlarge
production responsibility without proving more integration behavior.

## Allowed Files

- `tests/test_persisted_simulation_integration.py`
- `docs/LATEST_CODEX_REPORT.md`

`docs/CURRENT_PHASE.md` is not an implementation target after this approval.

## Forbidden Scope

Do not modify production code, existing tests, Protocols, domain models, Repositories, schema,
migrations, Executor, Simulator, Pipeline, CLI, settings/JSON, or package-root exports. Do not add
a composition factory, test-only production class, current-time behavior, retry, cache, logging,
network/external fetch, Provider, or `target_race_count`. Never use, copy, restore, delete, stage,
or commit `database/keiba.db` or `logs/`.

## SQLite Fixture Contract

Each test or fixture uses an independent `sqlite3.connect(":memory:")` connection only. It must
not use an existing user DB, a copy of one, or an external DB.

Create and seed the following minimal parent schema before migrations, using fixed explicit IDs:

```sql
CREATE TABLE races (
    id INTEGER PRIMARY KEY
);

CREATE TABLE horses (
    id INTEGER PRIMARY KEY,
    race_id INTEGER NOT NULL,
    horse_no INTEGER NOT NULL
);
```

Use ordered setup exactly as follows:

```text
1. create :memory: connection
2. create races/horses parent tables
3. seed the required fixed race and horse rows
4. connection.commit()
5. apply_migrations(connection) exactly once
6. construct existing repositories
```

`apply_migrations()` must run with no active transaction. Do not directly call v008/v009 `apply()`
from the test, inspect/patch/assert migration `applied_at`, or use it as a domain timestamp. Close
every test connection.

Horse IDs are prediction `horse_id` values in `BetRecommendation`; they must be resolved into race
entry IDs through real `SQLiteRaceEntrySource` and
`RepositoryBackedRaceEntrySelectionResolver`, never assumed identical by test shortcuts.

## Fixed Domain Times

Use explicit, fixed timezone-aware `datetime` values only. Keep run `started_at`, prediction
`information_cutoff`, `scheduled_start_at`, RaceResult/Payout `finalized_at`, and repository
`observed_at` separately meaningful. Prediction and settlement cutoffs need not be equal.
`datetime.now()`, current-date behavior, hidden defaults, and cutoff correction are forbidden.

## Required Existing Composition

Use one connection and the real constructors for this exact chain:

```text
SQLiteRaceEntrySource
→ RepositoryBackedRaceEntrySelectionResolver
→ SimulationBetPlanBuilder
→ SQLiteSimulationBetPlanSnapshotRepository
→ PersistedSimulationBetSource
→ RepositoryBackedPersistedRaceSettlementSource
→ PersistedRaceSimulationExecutor
→ Simulator
```

Also use existing `FixedStakeBetAllocator`, `SQLiteRaceResultRepository`, and
`SQLitePayoutRepository`. Do not introduce a wrapper, adapter, factory, fake Repository, or mocked
major integration path.

## Identity and Allocation Contract

Construct in every scenario:

```text
SimulationRunContext
StrategyIdentity
SimulationRaceInput
SimulationBetPlanIdentity
AllocationPolicyConfig
AllocationPolicyIdentity
BetStakeBudget
BetPlan
```

Use fixed stake policy:

```text
policy_name = "fixed_stake_per_recommendation"
policy_version = "1"
parameters = {"stake_amount": 100}
```

Derive `AllocationPolicyIdentity` through the established builder. Construct each plan identity
from exactly the following existing values:

```text
run_id               <- run_context.run_id
race_id              <- race_input.race_id
strategy_id          <- strategy_identity.strategy_id
strategy_config_hash <- strategy_identity.strategy_config_hash
information_cutoff   <- race_input.information_cutoff
```

Do not regenerate run/strategy identity, normalize IDs or strings, recompute policy/budget/stakes,
or substitute current time.

## Snapshot Write and Round-Trip Contract

For non-empty plans, use the full existing path:

```text
BetPlan
→ FixedStakeBetAllocator.allocate()
→ BetAllocationPlan
→ SQLiteRaceEntrySource
→ RepositoryBackedRaceEntrySelectionResolver
→ SimulationBetPlanBuilder.build()
→ SimulationBetPlanSnapshot
→ SQLiteSimulationBetPlanSnapshotRepository.save_snapshot()
```

Empty plans use the same allocator/builder path, producing and saving an empty snapshot header;
do not hand-build an empty snapshot. Immediately reload every saved snapshot using its identity and
assert `loaded == snapshot`. Assert snapshot identity, policy identity, budget, count, bet tuple
order, bet type, stake, recommendation rank, race-entry selection, and cutoff by value. Do not
assert SQLite surrogate IDs, SQL, private methods, query counts, row factory, or object identity
across the SQLite round trip.

## Read and Settlement Contract

After saving, use only:

```text
SQLiteSimulationBetPlanSnapshotRepository
→ PersistedSimulationBetSource
→ RepositoryBackedPersistedRaceSettlementSource
→ PersistedRaceSimulationExecutor
→ Simulator
```

Pass the same `SimulationRunContext` and `StrategyIdentity` through all applicable boundaries. Do
not inject a snapshot directly into the executor.

## Required Integration Tests

### 1. Multi-race full round trip

Create/save snapshots through the formal path for at least four races and call `Simulator.run()`
once. Supply its inputs in explicit `(scheduled_start_at, race_id)` order:

```text
Race 101: SETTLED, winning
Race 102: SETTLED, losing
Race 103: NO_BET, using a saved empty snapshot
Race 104: UNSETTLED, because the latest Payout is incomplete
```

For Race 104, save a complete RaceResult and only an `is_complete=False` latest Payout. Do not seed
a complete fallback publication or make any fallback/retry lookup. Verify through final results and
summary that the settlement Source omits that Payout mapping and the executor produces UNSETTLED.

Use the following amounts and ensure Race 101 settles before Race 102:

```text
Race 101: stake 100, payout_per_100 300, profit +200
Race 102: stake 100, complete publication with no purchased selection, payout 0, profit -100
Race 103: NO_BET
Race 104: planned stake 100; no settled investment, payout, or profit
```

Assert formal summary values, including `Decimal` comparisons rather than float:

```text
race_count = 4
settled_race_count = 2
no_bet_race_count = 1
unsettled_race_count = 1
settled_purchase_race_count = 2

bet_count = 3
settled_bet_count = 2
hit_bet_count = 1
hit_race_count = 1

investment = 200
payout = 300
profit = 100
roi = 150
bet_hit_rate = 50
race_hit_rate = 50
maximum_drawdown = 100
```

Also assert the purchased bet type's `by_bet_type` bet count, settled bet count, investment,
payout, profit, and hit count. Drawdown expectations must use existing `(settled_at, race_id)`
order; do not add production sorting behavior.

### 2. Missing RaceResult

Save a non-empty snapshot but do not save its RaceResult. The composed path must produce
`SettlementStatus.UNSETTLED` with `exclusion_reason == "missing_race_result"`; planned investment
is retained while settled investment, payout, and profit remain undetermined.

### 3. Snapshot natural-identity mismatch

Verify the composed lookup path fails closed, rather than treating a missing snapshot as NO_BET,
for representative valid identity differences: different run ID, different race ID, different
information cutoff, and a different valid StrategyIdentity (strategy ID/config hash together).
Expect `SimulationValidationError` with
`input_identifier == "simulation_bet_plan_snapshot"`. Do not duplicate every unit-level
single-field corruption case.

## Deliberate Non-Duplication

Do not exhaustively repeat unit contracts for constructor invalid values, Repository corruption,
purchase-order gaps/duplicates, malformed resolver mappings, all VOID/PARTIAL/UNSUPPORTED states,
mocked Repository call counts, Payout response type violations, or artificial identity corruption.
This phase proves real components compose.

## Required Verification

Run at least:

```text
python -m pytest tests/test_persisted_simulation_integration.py -q
python -m pytest -q
git diff --check
git status --short
```

Before choosing the related regression command, inspect actual test file names and include tests
covering FixedStakeBetAllocator/BetAllocationPlan, Builder, SQLite RaceEntrySource, concrete
Resolver, SQLite Snapshot Repository, Persisted Bet Source, repository-backed settlement Source,
Persisted Executor, Simulator/Summary, SQLite RaceResult/Payout repositories, and v008/v009
migration runner. Search the new test for fake/mocked core repositories, production factories,
real DB paths, current time, cache/retry/logging, external I/O, package exports, and
`target_race_count`.

## Stop Condition

Stop and report if the test needs a production, Protocol, model, Repository, schema, migration,
Executor, Simulator, Pipeline, or CLI change; if an existing contract makes an expected scenario
impossible; if an out-of-scope test fails; or if Git has unexpected changes. Do not stage, commit,
push, create a review branch, or begin another phase without explicit approval.
