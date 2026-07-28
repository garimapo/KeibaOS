# Latest Codex Report

## Status

READY_FOR_REVIEW

## Completed Phase

Phase 4C-2d3b1g — Repository-backed persisted settlement source

Base commit: `cc51822 docs: approve persisted simulation bet source`

## Changed files

- `scripts/simulation/repository_backed_persisted_settlement_source.py`
- `tests/test_repository_backed_persisted_settlement_source.py`
- `docs/LATEST_CODEX_REPORT.md`

`docs/CURRENT_PHASE.md` was not changed during implementation.

## Implementation

Added the non-exported concrete `RepositoryBackedPersistedRaceSettlementSource`. Its keyword-only
constructor retains the original Bet Source, RaceResult Repository, and Payout Repository objects;
it verifies only their required methods are callable and invokes none of them in the constructor.
Constructor and direct-input violations are `ValueError`.

For each valid load, the Source calls `SimulationBetSource.load_bets()` exactly once with the
original `SimulationRaceInput` and `StrategyIdentity` objects. It accepts only an exact tuple of
`SimulationBet` objects whose race and strategy IDs match the request and whose
`(bet_type, race_entry_ids)` identities are unique. A malformed Bet Source response fails before
Repository access as `SimulationValidationError` with identifier `simulation_bet_source`.

The empty tuple is a valid NO_BET plan: it produces one `PersistedRaceSettlementData` with no
race result and no payout mapping after exactly one Bet Source call and zero Repository calls.

For non-empty bets, the Source calls the RaceResult Repository once. `None` is retained as a
missing-result fact; wrong response type or race is rejected with identifier
`race_result_repository`. It derives distinct purchase types in first-occurrence order, then calls
the Payout Repository exactly once for each type with `observed_at_lte=None` and
`require_complete=False`.

`None` and incomplete Payout publications are both omitted from the resulting mapping. A complete,
matching Payout publication alone is included. No complete-only fallback, retry, second lookup, or
placeholder is used. Invalid Payout response type, race, or bet type is rejected with identifier
`payout_repository`.

The final bundle is constructed once from the original bet tuple, validated result, and complete
publications. Source, Repository, and bundle-constructor exceptions are not caught, wrapped, or
translated, so the original exception object propagates.

## Tests

The new dedicated suite covers formal signatures and hints, dependency retention, constructor and
direct-input validation, Bet Source validation before Repository calls, NO_BET, RaceResult and
Payout response validation, first-occurrence Payout calls, incomplete/missing/complete Payout
handling, exact exception identity propagation, bundle exception propagation, and prohibited
dependency/package boundaries.

| Check | Result |
| --- | --- |
| Dedicated settlement Source tests | `16 passed, 21 subtests passed` |
| Persisted settlement, bet Source, Repository, executor, and dedicated regressions | `160 passed, 92 subtests passed` |
| Full pytest suite | `2253 passed, 2 skipped, 662 subtests passed` |
| Forbidden dependency / wrapping / fallback search | `0 matches` |
| Runtime Protocol check search | `0 matches` |
| Repository exception import search | `0 matches` |
| Package-root export search | `0 matches` |

## Excluded scope

No Protocol, model, bundle, SQLite Repository, schema, migration, executor, Provider, raw Source,
Builder, Resolver, Simulator, Pipeline, CLI, composition, cache, retry, logging, or package-root
export was changed. `target_race_count` was not added.

## Git and handoff

`git diff --check` will be rerun after this report update. No files were staged, committed, pushed,
or branch-created. `database/keiba.db` and `logs/` remain outside the phase scope.

Awaiting implementation review and explicit commit approval.
