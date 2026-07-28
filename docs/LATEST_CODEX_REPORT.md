# Latest Codex Report

## Status

APPROVED_FOR_COMMIT

## Completed Phase

Phase 4C-2d3b1e3 — Repository-backed RaceEntrySelectionResolver implementation

Base commit: `c63d428 docs: approve sqlite race entry source`
Review branch: `review/4c-2d3b1e3-repository-backed-selection-resolver`

## Changed files

- `scripts/simulation/repository_backed_selection_resolver.py`
- `tests/test_repository_backed_selection_resolver.py`
- `docs/LATEST_CODEX_REPORT.md`

`docs/CURRENT_PHASE.md` remains unchanged during implementation, as required by the approved phase.

## Implementation

`RepositoryBackedRaceEntrySelectionResolver` is a slotted, keyword-only, structural implementation
of the existing `RaceEntrySelectionResolver` Protocol. Its constructor retains the injected
`RaceEntrySource` object and validates only that `load_race_entry_id_map` is callable. It does not
call the Source in the constructor and does not runtime-check the non-runtime-checkable Protocol.
An object that is itself a class is accepted when its static `load_race_entry_id_map` method is
callable, matching the approved callable-only constructor boundary.

For a valid request, the Resolver:

- accepts only a positive non-`bool` integer `race_id` and a non-empty ordinary `Sequence` of
  unique, positive non-`bool` horse IDs;
- copies the selection once to a tuple without mutating the caller;
- calls `RaceEntrySource.load_race_entry_id_map()` exactly once with that ordered tuple;
- validates that the Source result is a complete, exact mapping for the requested horse IDs;
- rejects missing, empty, extra, malformed, non-positive, `bool`, and duplicate race-entry result
  values with `ValueError`; and
- reads each requested mapping value once, validates the resulting tuple, and returns that same
  verified tuple in original horse-ID order without sorting or identity-mapping shortcuts.

All Resolver-detected constructor, direct-input, and Source-response contract violations raise
`ValueError`. The production module imports no repository exception classes and does not catch,
wrap, translate, or construct Source exceptions. `RepositoryValidationError`,
`RepositoryDataIntegrityError`, `RepositoryConflictError`, and arbitrary unexpected exceptions
raised by the Source propagate as the same exception object.

No SQLite query, cache, Builder, Provider, Repository construction, Pipeline, CLI, transaction,
network, current-time, package-root export, schema, or migration behavior was added.

## Tests

The dedicated suite covers constructor and Protocol signatures/type hints, callable Source
validation, no constructor call, direct-input validation, zero calls for invalid input, one call for
valid input, defensive tuple passing, caller immutability, mapping-order independence, missing and
empty result handling, extra keys, malformed keys and values, duplicate race-entry values,
exception object identity propagation, no identity shortcut, and dependency/package boundaries.
The review correction adds staticmethod-class Source acceptance and a value-access-counting mapping
test that proves each requested Source result is read exactly once on the successful path.

## Verification

| Check | Result |
| --- | --- |
| Resolver dedicated tests | `35 passed, 31 subtests passed` |
| Resolver/Source Protocol and SQLite Source regressions | `95 passed, 49 subtests passed` |
| Full pytest suite | `2217 passed, 2 skipped, 623 subtests passed` |
| Forbidden dependency search | `0 matches` |
| Runtime Protocol `isinstance` search | `0 matches` |
| Source method reference search | constructor validation plus one execution call only |
| `git diff --check` | success |

## Scope deliberately not implemented

- `SQLiteRaceEntrySource` changes.
- `RaceEntrySource` and `RaceEntrySelectionResolver` Protocol changes.
- Builder wiring and production composition.
- Persisted simulation bet sources and snapshot repositories.
- Schema, migrations, Pipeline, CLI, package-root export, and cache.

## Git and handoff

The implementation review is approved.

- Review branch: `review/4c-2d3b1e3-repository-backed-selection-resolver`
- Implementation review commit: `f5abed1 review: implement repository backed selection resolver`
- Review correction commit: `926366d fix: align repository backed selection resolver contract`
- The review branch is pushed to
  `origin/review/4c-2d3b1e3-repository-backed-selection-resolver`.
- The two review findings are resolved: the constructor checks only for a callable Source method,
  and each Source mapping value is read once before the verified tuple is returned.
- `database/keiba.db` and `logs/` remain uncommitted and outside the phase scope.

Awaiting explicit fast-forward integration approval for `feature/ver0.8-simulator`.
