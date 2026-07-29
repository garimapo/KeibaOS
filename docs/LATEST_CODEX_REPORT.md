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
document now validates direct construction before freezing: schema version must be exact integer `1`,
both paths must be `Path` instances, mapping fields must be `Mapping`, and races must be a tuple of
Mapping values. Recursive freeze rejects non-string mapping keys, non-finite floats, and non-JSON
compatible values with the approved exact errors. A stored empty races tuple or budgets mapping
remains valid.

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

GitHub review identified that the public dataclass invariant needed to be explicit. This correction
adds direct-constructor tests for schema/path/Mapping/races validation; recursive string-key and
JSON-compatible value checks; nested mapping/race/budget immutability; `Path("bad\\x00path")` request
validation; a nested budget duplicate key; root-level `1e999` error priority; the full root/schema/
database-path matrix; nested reload independence; the loader input type hint; and expanded source/AST
checks. The loader now converts parsed JSON races from list to tuple before calling the public
dataclass. No out-of-scope production code was changed.

Codex local results:

```text
Dedicated: 15 passed, 67 subtests passed
Related: 55 passed, 193 subtests passed
  tests/test_persisted_simulation_request_document.py
  tests/test_sqlite_persisted_simulation_application.py
  tests/test_sqlite_persisted_simulation_composition.py
  tests/test_persisted_simulation_run_service.py
  tests/test_simulation_models.py
Full suite: 2327 passed, 2 skipped, 894 subtests passed
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

`docs/CURRENT_PHASE.md` remains the approved contract and was not changed during this review
correction.
Existing production code/tests, the 1i5a application runner, composition root, migrations, schema,
`scripts/database.py`, `main.py`, CLI, package-root exports, `database/keiba.db`, and `logs/` were
not changed for this correction.

Review branch `review/4c-2d3b1i5b1-request-document-loader` contains the initial pushed review
commit `6716b00`. This report records the requested review correction; Phase 4C-2d3b1i5b2 and Phase
4C-2d3b1i5c are unstarted.

blocker: none
