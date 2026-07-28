# Latest Codex Report

## Status

APPROVED_FOR_COMMIT

## Completed Phase

Phase 4C-2d3b1e2 — SQLite RaceEntrySource implementation

Base commit: `fa51ab8 chore: automate codex phase handoff`
Base branch: `feature/ver0.8-simulator`

## Changed files

- `scripts/simulation/repositories/sqlite_race_entry_source.py`
- `tests/test_sqlite_race_entry_source.py`
- `docs/LATEST_CODEX_REPORT.md`

`docs/CURRENT_PHASE.md` remains `APPROVED_FOR_CODEX` intentionally: the approved phase marks it
as excluded from implementation-time changes.

## Implementation

`SQLiteRaceEntrySource` is a slotted, connection-injected concrete implementation of the
existing `RaceEntrySource` method signature. Its constructor accepts only `sqlite3.Connection`,
retains the exact connection object, enables and verifies foreign keys, and raises existing
`RepositoryValidationError` for invalid or unusable connections.

For each valid request, `load_race_entry_id_map()`:

- validates a positive non-`bool` race ID and a non-empty ordinary `Sequence` of unique, positive
  non-`bool` horse IDs, raising `RepositoryValidationError` for direct-input errors;
- copies the caller sequence without mutation;
- executes one parameter-bound batch `SELECT` against `horses` constrained by `race_id` and the
  requested IDs;
- reconstructs `prediction_horse_id -> race_entry_id` in requested-ID order, independent of SQL
  row order;
- returns partial or empty mappings for missing IDs, wrong-race IDs, and nonexistent races;
- fail-closes contradictory, duplicate, malformed, or schema-inconsistent rows with existing
  `RepositoryDataIntegrityError`; and
- propagates unexpected SQLite operational failures unchanged.

The Source does not issue an identity mapping without the race-scoped lookup. It performs no
separate race lookup, horse-by-horse N+1 query, write, transaction management, connection close
or reconfiguration, cache, schema/migration action, package-root export, Resolver, Builder,
adapter, Pipeline, CLI, network, or current-time work.

## Tests

The new dedicated suite verifies constructor/foreign-key behavior, exact Protocol signature and
type hints, direct-input validation, input immutability, requested-order mapping, partial/empty
absence mappings, one batch query, active transaction preservation, no writes/close, malformed
row handling, schema integrity handling, duplicate/extra mapping rejection, unexpected SQLite
error propagation, dependency boundaries, no cache, no package export, and no
`target_race_count`.

One fixture defect was found and corrected during testing: its initial in-memory row insertion
left a write transaction open, which prevented SQLite from enabling foreign keys. Committing the
fixture setup restored the intended constructor contract; production behavior was unchanged.

## Verification

| Check | Result |
| --- | --- |
| SQLiteRaceEntrySource dedicated tests | `32 passed, 18 subtests passed` |
| RaceEntrySource Protocol + dedicated tests | `48 passed, 18 subtests passed` |
| Snapshot SQLite repository + Source regressions | `72 passed, 55 subtests passed` |
| Full pytest suite | `2182 passed, 2 skipped, 592 subtests passed` |

Search checks:

- Tracked `git grep` does not yet list the new untracked concrete Source; worktree `rg` confirms
  exactly one `SQLiteRaceEntrySource` definition and one `FROM horses AS h` query in the new
  production module.
- The new production module has no `sqlite3.connect`, Resolver, Builder, adapter, transaction,
  connection-close, cache, or `target_race_count` reference.

## Scope deliberately not implemented

- Repository-backed `RaceEntrySelectionResolver`.
- Builder connection.
- `PersistedSimulationBetSource`.
- Schema or migration changes.
- Pipeline, CLI, package-root export, and composition wiring.

## Git and handoff

The implementation review is approved.

- Review branch: `review/4c-2d3b1e2-sqlite-race-entry-source`
- Review commit: `8a8fd8e review: implement sqlite race entry source`
- The review branch is pushed to
  `origin/review/4c-2d3b1e2-sqlite-race-entry-source`.
- `database/keiba.db` and `logs/` were not included in the review commit and remain uncommitted.

The current documentation-only approval update is the next review-branch commit. Base-branch
merge remains outside this step.
