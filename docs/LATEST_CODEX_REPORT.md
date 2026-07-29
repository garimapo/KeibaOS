# Latest Codex Report

## Status

READY_FOR_REVIEW

## Current Phase

Phase 4C-2d3b1i5b1 — Persisted simulation request document loader

Base commit: `c5933aa docs: approve SQLite persisted simulation application runner`

Branch: `feature/ver0.8-simulator`

## Implementation

Implemented `scripts/simulation/persisted_simulation_request_document.py` with only the approved
public frozen `PersistedSimulationRequestDocument` dataclass and keyword-only
`load_persisted_simulation_request_document()` loader.

The loader validates a non-empty `str`/`Path` request path before reading, uses UTF-8 only, and
preserves file `OSError` objects unchanged. It translates invalid UTF-8 to
`ValueError("request file must be UTF-8")` and malformed JSON to
`ValueError("request file must contain valid JSON")`.

It implements schema version `1`, the exact approved top-level key set, duplicate-key rejection at
every JSON object level, and non-finite number rejection including `NaN`, `Infinity`, `-Infinity`,
and `1e999`. A relative `database_path` is anchored exactly to `source_path.parent`; absolute paths
are retained without resolving, canonicalization, existence checks, or DB work.

Returned JSON content is recursively copied into `MappingProxyType` and tuple values. The frozen
document performs the same defensive copy on direct construction, so later caller mutation cannot
change a document. A stored empty races tuple or budgets mapping remains valid.

No `SimulationRunContext`, `StrategyConfig`, `StrategyIdentity`, `PredictionPipeline`,
`SimulationRaceInput`, `BetStakeBudget`, or `SimulationSummary` is constructed. The loader does not
open SQLite, run migrations, invoke the 1i5a runner/composition root, read configuration, use time,
network, logging, or CLI behavior.

## Tests and Verification

Added `tests/test_persisted_simulation_request_document.py` covering the formal API and field type
hints, frozen/deep immutable values, relative and absolute database paths, empty payloads, direct
constructor defensive copying, request/file/UTF-8/JSON failures, duplicate keys, non-finite values,
strict root/envelope/field validation, independent reloads, package-root non-export, and source/AST
boundary rules.

Codex local results:

```text
Dedicated: 13 passed, 32 subtests passed
Related: 53 passed, 158 subtests passed
  tests/test_persisted_simulation_request_document.py
  tests/test_sqlite_persisted_simulation_application.py
  tests/test_sqlite_persisted_simulation_composition.py
  tests/test_persisted_simulation_run_service.py
  tests/test_simulation_models.py
Full suite: 2325 passed, 2 skipped, 859 subtests passed
Forbidden production-pattern search: no matches
Package-root export check: absent
git diff --check: success
```

The bundled workspace Python runtime was used because `python` is not present on the shell PATH.

## Scope and Git State

Changed files for this phase are limited to:

```text
scripts/simulation/persisted_simulation_request_document.py
tests/test_persisted_simulation_request_document.py
docs/LATEST_CODEX_REPORT.md
```

`docs/CURRENT_PHASE.md` remains the approved contract and was not changed during implementation.
Existing production code/tests, the 1i5a application runner, composition root, migrations, schema,
`scripts/database.py`, `main.py`, CLI, package-root exports, `database/keiba.db`, and `logs/` were
not changed for this implementation.

No files were staged, committed, pushed, or placed on a review branch. Phase 4C-2d3b1i5b2 and
Phase 4C-2d3b1i5c are unstarted.

blocker: none
