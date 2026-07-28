# Current Phase

## Status

APPROVED_FOR_CODEX

## Phase

Phase 4C-2d3b1e2 — SQLite RaceEntrySource implementation

## Base Commit

`fa51ab8`

## Branch

`feature/ver0.8-simulator`

## Objective

Implement only the connection-injected `SQLiteRaceEntrySource` concrete read boundary that
structurally implements the existing `RaceEntrySource` Protocol. It resolves a requested,
non-empty prediction-horse-ID selection for one race into a mapping of
`prediction_horse_id -> race_entry_id` using one parameter-bound SQLite batch query.

## Allowed Files

- `scripts/simulation/repositories/sqlite_race_entry_source.py`
- `tests/test_sqlite_race_entry_source.py`
- `docs/LATEST_CODEX_REPORT.md`

## Forbidden Files

- `AGENTS.md`
- `docs/CURRENT_PHASE.md` (not an implementation-time change target)
- `docs/VER0.8_SIMULATOR_DESIGN.md`
- `scripts/simulation/race_entry_source.py`
- `scripts/simulation/selection_resolver.py`
- `scripts/simulation/repository_backed_selection_resolver.py`
- `scripts/simulation/bet_plan_builder.py`
- `scripts/simulation/bet_source.py`
- `scripts/simulation/repositories/__init__.py`
- all other production code and tests
- schema, migrations, Pipeline, CLI, `database/keiba.db`, and `logs/`

## Required Contract

### Concrete class and placement

Add `SQLiteRaceEntrySource` only in
`scripts/simulation/repositories/sqlite_race_entry_source.py`:

```python
class SQLiteRaceEntrySource:
    def __init__(self, *, connection: sqlite3.Connection) -> None:
        ...

    def load_race_entry_id_map(
        self,
        *,
        race_id: int,
        horse_ids: Sequence[int],
    ) -> Mapping[int, int]:
        ...
```

The constructor is keyword-only, retains the injected connection, and does not close it.
The module imports the existing `RaceEntrySource` Protocol only for structural/type-contract
clarity, `sqlite3`, typing, and the existing repository errors. It must not be package-root
exported if that would alter imports or introduce a cycle.

### Constructor and connection policy

- Accept only `sqlite3.Connection`; reject other values with existing
  `RepositoryValidationError`.
- Enable and verify `PRAGMA foreign_keys=ON` at construction; an unusable connection or a
  failure to enable foreign keys raises `RepositoryValidationError` with the source exception
  retained where applicable.
- Do not create schema or migrations, open a fixed database path, change row factory or
  isolation level, close the connection, add cache state, or perform a query in the constructor.

### Direct Source input validation

`load_race_entry_id_map` validates enough direct input to be safe without the future Resolver:

- `race_id` is a positive non-`bool` `int`.
- `horse_ids` is an ordinary non-empty `Sequence`, not `str`, `bytes`, `bytearray`, `Mapping`,
  generator, or non-sequence value.
- Each horse ID is a positive non-`bool` `int`; duplicates are rejected.
- Caller input is not mutated and is copied once before query construction.
- These failures raise existing `RepositoryValidationError`; the source owns no bet-type,
  cardinality, selection canonicalization, or Resolver response-validation policy.

### Query and mapping behavior

- Execute exactly one parameter-bound batch query per method call:

  ```sql
  SELECT h.id AS prediction_horse_id, h.id AS race_entry_id
  FROM horses AS h
  WHERE h.race_id = ?
    AND h.id IN (?, ?, ...)
  ```

- The aliases remain distinct even though both current columns are `horses.id`, preserving the
  semantic conversion boundary.
- Reconstruct the returned mapping in requested horse-ID order without relying on SQLite row order.
- No separate `races` lookup, horse-by-horse query, chunking, implicit identity completion,
  extra mapping entry, or cache is allowed.
- Missing requested IDs, IDs belonging to another race, and a nonexistent race are represented by
  a partial or empty mapping for the future Resolver; this Source does not raise an exception for
  those absence conditions.
- Contradictory, duplicate, or type-invalid fetched rows and invalid constructed mappings fail
  closed with existing `RepositoryDataIntegrityError`.
- Unexpected `sqlite3` operational errors are not broadly wrapped.

### Transaction and dependency boundaries

- Reads must not begin, commit, or roll back transactions; an active caller read transaction is
  allowed.
- No DB write, Provider, Repository-backed Resolver, Builder, Snapshot Repository, prediction,
  Pipeline, Simulator, network, current-time, schema, or migration dependency is permitted.
- No new exception class is added. Existing repository exceptions are used exactly as specified.

## Required Tests

The new dedicated test file must cover at least:

- keyword-only constructor and exact `load_race_entry_id_map` signature/type hints;
- connection type and foreign-key validation;
- positive non-`bool` race ID and horse-ID input validation, non-empty ordinary Sequence rules,
  duplicate rejection, and caller-input immutability;
- one parameter-bound batch query for all requested IDs, without a per-horse N+1 query;
- mapping semantics, arbitrary SQL row order, missing and wrong-race IDs as absent keys, and no
  extras or identity synthesis;
- row/mapping integrity failure behavior and unchanged propagation of unexpected SQLite errors;
- no writes, transaction begin/commit/rollback, schema/migration, fixed database path, cache,
  package export, Resolver, Builder, Pipeline, or network behavior;
- `database/keiba.db` is never used by tests; use `:memory:` fixtures only.

Run after implementation:

```text
python -m pytest tests/test_sqlite_race_entry_source.py -q
python -m pytest tests/test_race_entry_source_contract.py tests/test_sqlite_race_entry_source.py -q
python -m pytest tests/test_sqlite_simulation_bet_plan_snapshot_repository.py tests/test_race_entry_source_contract.py tests/test_sqlite_race_entry_source.py -q
python -m pytest -q
git diff --check
git status --short
```

Also search the worktree for the concrete class, query count, and forbidden composition imports.

## Stop Condition

Stop and report without implementation if the design conflicts with existing SQLite repository
contracts, the required behavior needs a schema/migration/Resolver/Builder change, concrete
module placement would require an out-of-scope package export, test failures originate outside
this scope, or Git status contains unexpected files. Do not stage, commit, or push in this phase.
