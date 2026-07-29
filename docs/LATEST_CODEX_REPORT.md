# Latest Codex Report

## Status

APPROVED_FOR_COMMIT

## Current Phase

Phase 4C-2d3b1i5b1 — Persisted simulation request document loader

Base commit: `c5933aa docs: approve SQLite persisted simulation application runner`

Base branch: `feature/ver0.8-simulator`

Review branch: `review/4c-2d3b1i5b1-request-document-loader`

## GitHub Review Approval

GitHub implementation review is complete. The initial review commit
`6716b00 review: add persisted simulation request document loader` and correction commit
`1f58942 review: enforce request document invariants` were reviewed. Production implementation and
test coverage are approved; no additional production or test correction is required. There is no
blocker, and base branch integration is pending.

## Approved Production Contract

`PersistedSimulationRequestDocument` is a frozen dataclass and
`load_persisted_simulation_request_document()` is a keyword-only API. The loader enforces schema
version `1` and the exact seven top-level keys, performs request-path pre-read validation, reads
UTF-8 only, and propagates file `OSError` unchanged. `UnicodeDecodeError` and `JSONDecodeError` are
translated to their stable approved `ValueError` messages.

Duplicate JSON object keys are rejected at every level. `NaN`, `Infinity`, `-Infinity`, and `1e999`
are rejected before root validation. The root must be an exact dict and field validation order is
maintained. Relative database paths are anchored to the request parent and absolute paths are kept;
the loader does not resolve, make absolute, expand, or existence-check paths.

The loader converts JSON races list to tuple before dataclass construction. Direct construction
validates schema, Path, Mapping, and races types. Every mapping is copied into `MappingProxyType`,
every list/tuple into tuple, mapping keys must be strings, floats must be finite, and values must be
JSON-compatible. No SQLite, migration, runner, domain assembly, CLI, or package-root export is
introduced.

## Approved Test Coverage

The approved coverage includes formal module/class/loader API, frozen field order and type hints,
keyword-only request path, limited public definitions, package-root non-export, relative/absolute
paths, empty races/budgets, deep mutation rejection, direct-constructor defensive copy and every
direct-constructor validation boundary.

It covers invalid request-path cases including NUL str/Path values; unchanged file exceptions;
invalid UTF-8; empty/malformed/BOM JSON; top-level/nested/race/budget duplicate keys; all required
non-finite forms and root `1e999` error priority; root/non-object, key, schema-version,
database-path, object, and array validation matrices; nested reload independence; and source/AST
responsibility boundaries. The source check verifies no `Any`, `cast`, `runtime_checkable`,
type-ignore directive, or exception handler other than `UnicodeDecodeError` and
`json.JSONDecodeError`.

## Verification

These are Codex local results, not independently executed GitHub CI results:

```text
Dedicated: 15 passed, 67 subtests passed
Related: 55 passed, 193 subtests passed
Full suite: 2327 passed, 2 skipped, 894 subtests passed
Forbidden production-pattern search: no matches
Package-root export check: absent
git diff --check: success
```

The bundled workspace Python runtime was used because `python` is not present on the shell PATH.

## Scope and Follow-up

Phase 4C-2d3b1i5b2 and Phase 4C-2d3b1i5c are unstarted. Domain/application input assembly belongs
to 1i5b2. CLI, stdout, stderr, exit code, and summary output belong to 1i5c.

The 1i5a runner, migration/schema, `scripts/database.py`, `main.py`, `config/settings.json`, CLI,
and package-root exports remain unchanged. `database/keiba.db` and `logs/` are outside scope.

blocker: none
