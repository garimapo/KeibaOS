# Latest Codex Report

## Status

APPROVED_FOR_COMMIT

## Completed Phase

Phase 4C-2d3b1h — Persisted simulation composition and integration

Base commit: `46d1d74 docs: approve repository backed persisted settlement source`

## Changed Files

- `tests/test_persisted_simulation_integration.py` (new)
- `docs/LATEST_CODEX_REPORT.md`

No production file, existing test, schema, migration, Protocol, model, Repository, Executor,
Simulator, Pipeline, CLI, composition factory, or package-root export was changed.
`docs/CURRENT_PHASE.md` was not changed during implementation.

## Integration Fixture

Each test creates and closes its own `sqlite3.connect(":memory:")` connection. It creates only the
approved parent `races` and `horses` schema, seeds fixed race/horse IDs, commits, invokes the
registered `apply_migrations(connection)` exactly once with no active transaction, then constructs
the existing SQLite components over that same connection. The migration audit timestamp is neither
patched nor asserted.

All simulation-domain times are fixed and timezone-aware. The fixture keeps run start, prediction
cutoff, scheduled start, result/payout finalized times, and repository observed times distinct.
It does not use `datetime.now()`, `date.today()`, a real DB, a copied user DB, external I/O, or a
mock/fake core Repository.

## Real Component Composition

The test composes the approved existing path directly:

```text
FixedStakeBetAllocator
→ SQLiteRaceEntrySource
→ RepositoryBackedRaceEntrySelectionResolver
→ SimulationBetPlanBuilder
→ SQLiteSimulationBetPlanSnapshotRepository
→ PersistedSimulationBetSource
→ RepositoryBackedPersistedRaceSettlementSource
→ PersistedRaceSimulationExecutor
→ Simulator.run()
→ SimulationSummary
```

Each plan identity uses only the run context run ID, race input race ID and information cutoff, and
strategy identity strategy ID/config hash. Fixed-stake allocation uses the approved policy
`fixed_stake_per_recommendation` version `1` with a 100-yen stake. Prediction horse IDs are passed
through the real SQLite Source and concrete Resolver before snapshot construction.

Every snapshot, including the NO_BET case, follows the formal `BetPlan → Allocator → Builder →
save_snapshot()` path. The test immediately reloads it and verifies equality by value: identity,
policy identity, budget, bet count/order/type/stake/rank/selection, and cutoff. It intentionally
does not assert object identity across a SQLite round trip.

## Covered Outcomes

One four-race `Simulator.run()` proves the full persisted path:

| Race | Persisted facts | Result |
| --- | --- | --- |
| 101 | Saved one-bet plan, complete result, complete winning payout of 300 per 100 | `SETTLED`, investment 100, payout 300, profit 200, one hit |
| 102 | Saved one-bet plan, complete result, complete payout table without the purchased selection | `SETTLED`, investment 100, payout 0, profit -100, no hit |
| 103 | Saved empty plan header | `NO_BET` without result/payout data |
| 104 | Saved one-bet plan, complete result, latest payout publication incomplete | `UNSETTLED` with `missing_payout_publication` |

The incomplete Race 104 publication has no complete fallback and receives no re-query. The
repository-backed settlement Source omits it from the mapping; the existing executor produces the
UNSETTLED result.

The resulting summary confirms `race_count=4`, settled/no-bet/unsettled counts `2/1/1`, three
planned bets, two settled bets, one hit bet/race, investment 200, payout 300, profit 100,
`Decimal("150")` ROI, `Decimal("50")` bet/race hit rates, and maximum drawdown 100 using the
existing `(settled_at, race_id)` order. The used bet type summary confirms its count, settled
count, hit count, investment, payout, profit, ROI, and hit rate.

The suite also covers a saved non-empty snapshot with no RaceResult, yielding `UNSETTLED` with
`missing_race_result`, retained planned investment, and unset settled amounts. Finally, it confirms
that valid differences in run ID, race ID, information cutoff, or StrategyIdentity fail closed as
`SimulationValidationError(input_identifier="simulation_bet_plan_snapshot")`, rather than
silently becoming NO_BET.

## Verification

| Check | Result |
| --- | --- |
| Dedicated integration test | `3 passed, 4 subtests passed` |
| Related component, SQLite Repository, migration, executor, Simulator, and Summary regressions | `507 passed, 228 subtests passed` |
| Full pytest suite | `2256 passed, 2 skipped, 666 subtests passed` |
| Forbidden-pattern search in new integration test | `0 matches` |
| `git diff --check` | passed |

The related command covered FixedStakeBetAllocator/BetAllocationPlan, Builder, SQLiteRaceEntrySource,
the concrete Resolver, SQLite Snapshot Repository, Persisted Bet Source, repository-backed
settlement Source, Persisted Executor, Simulator/Summary, SQLite RaceResult/Payout repositories,
and migration runner tests.

## Excluded Scope

No production composition API, factory, wrapper, cache, retry, logging, Provider, network,
Pipeline, CLI, settings JSON, schema/migration change, package-root export, or
`target_race_count` was added. `database/keiba.db` and `logs/` remain outside this phase.

## Git and Handoff

Review branch `review/4c-2d3b1h-persisted-simulation-integration` was pushed to origin with
review commit `eb01cfb review: add persisted simulation integration tests`. GitHub implementation
review approved the change with no requested code correction.

The approved outcome confirms that production remains unchanged, direct composition inside the
integration test is the adopted approach, and only `:memory:` SQLite is used. The real path reaches
`SimulationSummary` through FixedStakeBetAllocator, SQLiteRaceEntrySource,
RepositoryBackedRaceEntrySelectionResolver, SimulationBetPlanBuilder,
SQLiteSimulationBetPlanSnapshotRepository, PersistedSimulationBetSource,
RepositoryBackedPersistedRaceSettlementSource, PersistedRaceSimulationExecutor, and
`Simulator.run()`.

Approval covers the saved NO_BET snapshot path, settled winning and losing paths, incomplete Payout
to `missing_payout_publication` UNSETTLED, missing RaceResult to `missing_race_result` UNSETTLED,
and natural identity mismatch fail-closed as
`SimulationValidationError(input_identifier="simulation_bet_plan_snapshot")`. The approved
four-race summary values are: `race_count=4`, `settled_race_count=2`,
`no_bet_race_count=1`, `unsettled_race_count=1`, `void_race_count=0`, `error_race_count=0`,
`unsupported_race_count=0`, `settled_purchase_race_count=2`, `bet_count=3`,
`settled_bet_count=2`, `hit_bet_count=1`, `hit_race_count=1`, investment 200, payout 300,
profit 100, `Decimal("150")` ROI, `Decimal("50")` bet/race hit rates, and maximum drawdown 100.

The dedicated, related, full-suite, forbidden-pattern, and `git diff --check` results above remain
approved. `database/keiba.db` and `logs/` remain outside the commit. The review commit and its
approval are ready for fast-forward integration into `feature/ver0.8-simulator`.
