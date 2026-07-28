# Current Phase

## Status

APPROVED_FOR_CODEX

## Phase

Phase 4C-2d3b1e3 — Repository-backed RaceEntrySelectionResolver implementation

## Base Commit

`c63d428 docs: approve sqlite race entry source`

## Branch

`feature/ver0.8-simulator`

## Objective

Implement a concrete `RepositoryBackedRaceEntrySelectionResolver` that structurally satisfies
the existing `RaceEntrySelectionResolver` Protocol by adapting exactly one existing
`RaceEntrySource.load_race_entry_id_map()` call for one ordered horse-ID selection. The concrete
Resolver validates its public input and the Source response, then reconstructs verified race-entry
IDs in the original horse-ID order.

## Allowed Files

- `scripts/simulation/repository_backed_selection_resolver.py`
- `tests/test_repository_backed_selection_resolver.py`
- `docs/LATEST_CODEX_REPORT.md`

## Forbidden Files

- `AGENTS.md`
- `docs/CURRENT_PHASE.md` after approval and during implementation
- `docs/VER0.8_SIMULATOR_DESIGN.md`
- `scripts/simulation/selection_resolver.py`
- `scripts/simulation/race_entry_source.py`
- `scripts/simulation/repositories/sqlite_race_entry_source.py`
- `scripts/simulation/bet_plan_builder.py`
- `scripts/simulation/bet_source.py`
- `scripts/simulation/persisted_*`
- `scripts/simulation/bet_plan_snapshot*`
- package `__init__.py` files and package-root exports
- all other production code and tests
- schema, migrations, Pipeline, CLI, database, and `logs/`

## Proposed Contract

### Concrete class and placement

Add only `RepositoryBackedRaceEntrySelectionResolver` in
`scripts/simulation/repository_backed_selection_resolver.py`:

```python
class RepositoryBackedRaceEntrySelectionResolver:
    def __init__(self, *, race_entry_source: RaceEntrySource) -> None:
        ...

    def resolve_race_entry_ids(
        self,
        *,
        race_id: int,
        horse_ids: Sequence[int],
    ) -> tuple[int, ...]:
        ...
```

The constructor is keyword-only, retains the injected Source object without wrapping it, and must
not call the Source, DB, Builder, or other composition code. It verifies only that
`race_entry_source.load_race_entry_id_map` is callable; any other constructor input raises
`ValueError`. The Resolver must not use `isinstance(..., RaceEntrySource)`, because the Protocol is
not runtime-checkable. It structurally implements the existing `RaceEntrySelectionResolver`
Protocol; neither Protocol changes nor a package export are in scope.

### Public-input boundary

Before calling the Source, the Resolver copies `horse_ids` once to an immutable tuple and validates:

- `race_id` is a positive, non-`bool` `int`;
- `horse_ids` is a non-empty ordinary `Sequence`, not `str`, `bytes`, `bytearray`, `Mapping`, a
  generator, or another non-Sequence;
- every horse ID is a positive, non-`bool` `int`; and
- horse IDs are unique.

These Resolver-owned public-input failures raise `ValueError`. The caller collection is never
mutated. The Resolver neither sorts, deduplicates, canonicalizes, nor converts horse IDs into an
unverified identity mapping.

### Source adaptation and successful result

For each valid Resolver call, invoke exactly once:

```python
race_entry_source.load_race_entry_id_map(
    race_id=race_id,
    horse_ids=requested_horse_ids,
)
```

`requested_horse_ids` is the copied tuple in caller order. A successful Source result is a mapping
whose keys are exactly the requested horse IDs and whose values are unique, positive, non-`bool`
race-entry IDs. The return value is reconstructed only as:

```python
tuple(mapping[horse_id] for horse_id in requested_horse_ids)
```

It therefore preserves the caller's horse-ID order and returns a deterministic
`tuple[int, ...]`, independent of Source mapping iteration order. It does not consult SQLite,
perform an additional lookup, or infer entries for absent horses.

### Source-result fail-closed policy

The Resolver treats a missing requested horse key as an unresolved selection and raises
`ValueError`; this covers the partial or empty mapping that `SQLiteRaceEntrySource` intentionally
returns for a missing ID, a wrong-race ID, or a nonexistent race.

Before reconstruction, it must reject Source responses that are not mappings, have extra keys,
have keys that do not match the requested IDs, contain non-positive or `bool` IDs, map two
requested horses to the same race-entry ID, or otherwise cannot construct a complete one-to-one
tuple. All Resolver-detected Source-response violations raise `ValueError`.

The Resolver does not import, catch, wrap, translate, or newly construct repository exceptions.
`RepositoryValidationError`, `RepositoryDataIntegrityError`, and `RepositoryConflictError` raised
by the injected Source propagate as the identical exception object. Any other Source exception also
propagates unchanged.

### Dependency and lifecycle boundaries

- No SQLite query, connection, transaction, cache, mutable global state, current-time access,
  Provider, Repository construction, Builder call, Pipeline, CLI, network, or production
  composition is permitted.
- `SQLiteRaceEntrySource` remains unchanged and owns its batch query and row-level integrity work.
- The Resolver calls its injected Source once per valid selection. The existing
  `SimulationBetPlanBuilder` calls the Resolver once per allocation; a multi-allocation plan can
  therefore make multiple Source calls. Plan-wide batching is explicitly out of scope.
- Race-entry ID ordering is the resolution order only. `SimulationBet` remains the later boundary
  that canonicalizes its selected race-entry IDs for bet identity.

## Required Tests

The new dedicated test file must cover at least:

- exact keyword-only constructor and Resolver method signatures, structural Protocol conformance,
  and no constructor-time Source call;
- positive non-`bool` `race_id`, non-empty ordinary `Sequence`, unique positive non-`bool` horse
  IDs, invalid collection types, and caller-input immutability;
- one Source call with the copied ordered horse-ID tuple and no calls for invalid input;
- return order based on original horse-ID order rather than mapping iteration order;
- partial and empty Source mappings for missing IDs, wrong-race IDs, and nonexistent races;
- Source-output mapping type, key-set, value type/range, and duplicate race-entry-ID validation,
  all as `ValueError` when detected by the Resolver;
- unchanged object-identity propagation of repository exceptions and arbitrary exceptions produced
  by the Source;
- absence of SQLite, cache, Builder, Pipeline, package export, database-path, network, and
  current-time dependencies.

Run after implementation:

```text
python -m pytest tests/test_repository_backed_selection_resolver.py -q
python -m pytest tests/test_race_entry_selection_resolver_contract.py tests/test_race_entry_source_contract.py tests/test_sqlite_race_entry_source.py tests/test_repository_backed_selection_resolver.py -q
python -m pytest -q
git diff --check
git status --short
```

Also search the implementation and dedicated tests for forbidden concrete SQLite, Builder, cache,
and composition dependencies.

## Stop Condition

Stop and report without implementation if the design requires changing either existing Protocol or
`SQLiteRaceEntrySource`, if Builder wiring or plan-wide batching becomes necessary, if a schema or
migration change is required, if tests fail outside scope, or if Git status contains unexpected
files. Do not stage, commit, or push during this phase.
