# Latest Codex Report

## Status

APPROVED_FOR_COMMIT

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

Implementation review was approved with no requested code changes. Review branch
`review/4c-2d3b1g-repository-backed-persisted-settlement-source` was pushed to origin with review
commit `63291ee review: implement repository backed persisted settlement source`.

The approved contract confirms the following:

- constructor and direct-input violations are `ValueError`;
- malformed Bet Source responses use `SimulationValidationError(identifier="simulation_bet_source")`;
- malformed RaceResult responses use `SimulationValidationError(identifier="race_result_repository")`;
- malformed Payout responses use `SimulationValidationError(identifier="payout_repository")`;
- each valid input calls the Bet Source once; NO_BET calls both Repositories zero times; non-empty
  bets call the RaceResult Repository once and the Payout Repository once per distinct required type;
- required payout types preserve first-occurrence order and use `observed_at_lte=None` with
  `require_complete=False`;
- missing (`None`) and incomplete publications are omitted, while only complete publications are
  stored, without fallback, retry, or re-query;
- the original bets tuple, bet order, and bet object identities are preserved; and
- Source, Repository, and bundle exceptions propagate as the same exception objects.

The prohibited-dependency and package-export boundaries, plus the dedicated, related, and full
pytest results above, remain approved. `database/keiba.db` and `logs/` remain outside the commit.

This approval commit is pending integration of the reviewed branch into
`feature/ver0.8-simulator`.
