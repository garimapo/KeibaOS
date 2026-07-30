# Latest Codex Report

## Status

APPROVED_FOR_COMMIT

## Current Phase

Phase 4C-2d3b1i5b2a — Persisted simulation application input assembler

Base commit: `924a1e4 docs: approve persisted simulation request document loader`

Branch: `feature/ver0.8-simulator`

## Preparation and Approval

Phase 4C-2d3b1i5b1 is formally complete: base and review reached the same `924a1e4` commit. The
former broad 1i5b work is split so application dependency assembly is reviewable separately from
race, past, and audit assembly.

Phase 1i5b2a is approved for implementation. Its only implementation files will be:

```text
scripts/simulation/persisted_simulation_application_inputs.py
tests/test_persisted_simulation_application_inputs.py
docs/LATEST_CODEX_REPORT.md
```

The output is frozen `PersistedSimulationApplicationInputs`, containing database path,
`SimulationRunContext`, `StrategyIdentity`, deterministic `PredictionPipeline`, and a sorted,
defensively copied `Mapping[int, BetStakeBudget]`. Its assembler accepts only an exact
`PersistedSimulationRequestDocument` and creates no race inputs or audit objects.

The approved contract fixes nested run-context schema and timezone-aware ISO parsing; the only
supported RuleBased strategy, bet types, enums, fixed-stake policy, and 100-yen stake validation; use
of existing `build_strategy_identity()`; one shared `StrategyConfig` object between identity and
pipeline; explicit TrackEngine reference date; canonical string race-ID budget conversion; direct
dataclass invariants; failure order; and no DB/file/JSON/CLI responsibility.

Required tests cover the formal API, valid construction, deterministic double assembly, direct
dataclass invariants, nested schema matrices, 1i4 composition preconditions without DB execution, and
source/AST boundaries.

Phase 4C-2d3b1i5b2b is unstarted and owns race/past/track/audit/`SimulationRaceInput` assembly.
Phase 4C-2d3b1i5c is unstarted and owns CLI, stdout/stderr, exit code, runner invocation, and Summary
output.

`main.py`, `config/settings.json`, migration/schema, `scripts/database.py`, package-root exports,
`database/keiba.db`, and `logs/` are out of scope.

## Implementation

Implemented Phase 4C-2d3b1i5b2a from base commit `924a1e4` on
`feature/ver0.8-simulator`.

New production module:

```text
scripts/simulation/persisted_simulation_application_inputs.py
```

New dedicated test module:

```text
tests/test_persisted_simulation_application_inputs.py
```

The frozen `PersistedSimulationApplicationInputs` and keyword-only
`assemble_persisted_simulation_application_inputs()` assemble only the approved application inputs.
They use the document's already-anchored database path, validate the nested run-context and strategy
schemas, parse only timezone-aware ISO datetimes, build the supported fixed-stake allocation policy,
derive `StrategyIdentity` only through `build_strategy_identity()`, and create a deterministic
`PredictionPipeline` with an explicit `TrackEngine` reference date.

The pipeline and identity share the exact same `StrategyConfig` object. Budget keys are converted only
from canonical positive integer strings and are exposed as a race-ID-sorted, defensively copied
`MappingProxyType` containing exact `BetStakeBudget` objects. Empty budgets and empty allowed bet types
remain valid. The output dataclass independently verifies its direct-construction invariants.

Failure handling is fail-closed. The assembler creates no race, past-race, track-condition, audit, DB,
repository, runner, or CLI object. It does not reread the request, parse JSON, use a clock, retry, or
wrap collaborator exceptions. The only translated exceptions are `ValueError` values from ISO datetime
and date parsing, which become the approved field-specific errors.

Verification (Codex local execution):

```text
Dedicated: 17 passed, 82 subtests passed
Related: 72 passed, 275 subtests passed
  tests/test_persisted_simulation_application_inputs.py
  tests/test_persisted_simulation_request_document.py
  tests/test_sqlite_persisted_simulation_application.py
  tests/test_sqlite_persisted_simulation_composition.py
  tests/test_persisted_simulation_run_service.py
  tests/test_simulation_models.py
Full suite: 2344 passed, 2 skipped, 976 subtests passed
Forbidden-dependency search: no matches
Exception-handler AST/source check: only the two ISO parser ValueError handlers
git diff --check: success
```

No existing production module or existing test was modified. The 1i5b1 document loader and 1i5a runner
and composition root remain unchanged. Migration, schema, `scripts/database.py`, `main.py`,
`config/settings.json`, CLI, and package-root exports remain unchanged. `database/keiba.db` and `logs/`
are out of scope and uncommitted.

The initial review commit `093dd23` was pushed to
`review/4c-2d3b1i5b2a-application-inputs`. Phase 4C-2d3b1i5b2b and Phase 4C-2d3b1i5c remain
unstarted.

## Review Correction

GitHub review found that `date.fromisoformat()` accepts basic and ISO week-date forms, even though the
approved request boundary requires canonical `YYYY-MM-DD`. `_parse_iso_date()` now compares the original
text with `parsed.isoformat()`, so basic (`20260805`) and week (`2026-W32-3`) forms fail with the stable
pipeline date error.

The review also found that applying `math.isfinite()` or `float()` directly to an arbitrarily large
integer can leak `OverflowError`. `_finite_score()` now bounds exact integers against the largest finite
float before conversion, preserving the stable `strategy.min_combination_score must be finite` error for
both huge positive and negative integers without an additional exception handler.

The dedicated tests now additionally verify assembler type hints, module-defined public definitions,
package-root non-export, the canonical date matrix, huge-integer behavior, valid assembly details,
determinism details, source/AST exception ownership, and exact allocation-policy type enforcement in the
direct output dataclass. Production changes are limited to the assembler; no existing production or test
file was changed.

Verification was rerun locally by Codex after the correction:

```text
Dedicated: 17 passed, 82 subtests passed
Related: 72 passed, 275 subtests passed
Full suite: 2344 passed, 2 skipped, 976 subtests passed
Forbidden-dependency search: no matches
git diff --check: success
```

## Review Test Contract Correction

GitHub re-review found no further production correction: canonical ISO date validation, huge-integer
finite validation, shared `StrategyConfig`, and pipeline/budget assembly remain approved.

The normal assembly test now proves that `database_path` is the exact same already-anchored `Path`
object from the document. The source contract now explicitly rejects the `# type: ignore` literal,
parses with `type_comments=True`, validates `tree.type_ignores`, and checks `typing` imports by their
original names so aliases cannot hide `Any`, `cast`, or `runtime_checkable`. The AST Name check includes
`runtime_checkable`, and the exact two parser-owned `ValueError` handlers remain verified.

The duplicated blocker entry was removed. Codex reran verification locally after this test correction:

```text
Dedicated: 17 passed, 82 subtests passed
Related: 72 passed, 275 subtests passed
Full suite: 2344 passed, 2 skipped, 976 subtests passed
```

Production remains unchanged.

## GitHub Review Approval

GitHub implementation review is complete. The initial review commit `093dd23`, production correction
commit `7c982ca`, and test-contract correction commit `ac1b951` were reviewed and approved. Production
implementation and test coverage are approved; no additional production or test correction is required.
There is no blocker, and base-branch integration is pending.

Base branch: `feature/ver0.8-simulator`

Review branch: `review/4c-2d3b1i5b2a-application-inputs`

Base commit: `924a1e4`

Approved contract: frozen `PersistedSimulationApplicationInputs`; exact request-document boundary;
identity-preserved database path; timezone-aware and Z datetime parsing without clock fallback; only the
supported RuleBased strategy, bet types, enums, fixed-stake policy, canonical date, and canonical budget
keys; exact immutable domain types; shared StrategyConfig identity; deterministic pipeline assembly;
sorted defensive budget freeze; and no SQLite, runner, race, audit, CLI, or package-root responsibility.

Approved coverage includes the formal API/type hints, exact public surface and package-root non-export,
identity and deterministic assembly, direct-constructor exact types, all nested validation matrices,
canonical-date and huge-integer boundaries, and the source/AST contract. The only exception handlers are
the two ISO parser-owned `ValueError` handlers; `Exception`, `BaseException`, and `OverflowError` are
not caught.

Codex local verification results remain:

```text
Dedicated: 17 passed, 82 subtests passed
Related: 72 passed, 275 subtests passed
Full suite: 2344 passed, 2 skipped, 976 subtests passed
Forbidden-dependency search: no matches
Package-root export: none
Exception-handler AST: only the two ISO parser ValueError handlers
git diff --check: success
```

Phase 4C-2d3b1i5b2b and Phase 4C-2d3b1i5c remain unstarted. Race, past-race, track, audit, and
`SimulationRaceInput` assembly belong to 1i5b2b; CLI/output/runner invocation belong to 1i5c. The 1i5b1
loader and 1i5a runner/composition remain unchanged. Migration, schema, `scripts/database.py`, `main.py`,
`config/settings.json`, CLI, and package-root remain unchanged. `database/keiba.db` and `logs/` remain
out of scope.

blocker: none
