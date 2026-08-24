# Latest Codex Report

## Status

PHASE_4C_2D3B1I6C1D1_READY_FOR_REVIEW

## Previous Formal Phase

Phase 4C-2d3b1i6c1a — Historical input source-record domain and deterministic IDs

Base commit: `038130c9d84a082107e351e545c167a9019e7b3a feat: load historical input snapshots from sqlite`

Branch: `feature/ver0.8-simulator`

## Current Preparation

Phase 4C-2d3b1i6c1d1 — NAR target horse identity preparation

Base commit: `960c3419e52205cbfd94c3466eaabbb85d14e6ba feat: assemble historical input snapshots`

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

## Phase 4C-2d3b1i5b2b Preparation and Approval

Phase 4C-2d3b1i5b2a is formally complete at base HEAD `b06503c`. Phase 4C-2d3b1i5b2b is approved for
implementation on `feature/ver0.8-simulator` and is restricted to:

```text
scripts/simulation/persisted_simulation_race_inputs.py
tests/test_persisted_simulation_race_inputs.py
docs/LATEST_CODEX_REPORT.md
```

The new assembler will accept only the exact immutable request document and exact application inputs,
preserve their database-path object identity, pre-scan race IDs against application budget IDs before
domain construction, and build sorted audited `SimulationRaceInput` values only. It must generate
RacePredictionInput, InputSnapshotAudit, and canonical audit keys deterministically; preserve past-race
order; use `information_cutoff.isoformat()` as prediction time; and let existing simulation validation
fail closed without wrapping.

The approved contract defines canonical dates, timezone-aware timestamps, audit schemas, track/entry/
past-race schemas, huge-integer finite boundaries, immutable snapshot expectations, and the two-parser
exception-handler limit. No DB, runner, repository, CLI, schema, migration, 1i5b1, or 1i5b2a change is
authorized. Required tests include valid multi-race assembly, all input matrices, determinism, existing
fail-closed validation, and source/AST boundaries.

Phase 4C-2d3b1i5c remains unstarted. It alone owns request connection, runner invocation, CLI, output,
stdout/stderr, and exit codes. `main.py`, `config/settings.json`, `database/keiba.db`, and `logs/` remain
out of scope.

## Phase 4C-2d3b1i5b2b Implementation

Status: `READY_FOR_REVIEW`

Implemented the new `scripts/simulation/persisted_simulation_race_inputs.py` assembler and its dedicated
`tests/test_persisted_simulation_race_inputs.py` contract coverage. The assembler accepts only the exact
request document and application-input objects, preserves the exact `database_path` object linkage, and
pre-scans the immutable race array for exact schema, positive unique race IDs, and exact budget-ID parity
before constructing domain objects.

Race assembly now enforces canonical ISO dates, timezone-aware ISO datetimes (including `Z`), the cutoff
ordering invariant, exact race/track/entry/past-race/audit schemas, finite numeric boundaries including
huge integers, and explicit no-past-race audit evidence. It builds `PastRace`, `RaceTrackConditions`,
`RacePredictionInput`, `InputSnapshotAudit`, and `SimulationRaceInput`; existing immutable snapshot and
fail-closed simulation validation remain responsible for their existing invariants. Audit keys are emitted
in canonical entry-ID order and results are sorted by `(scheduled_start_at, race_id)`.

The module has no DB, loader, runner, migration, repository, CLI, clock, cache, retry, or package-root
responsibility. Its only exception handlers are the two parser-owned `ValueError` handlers for canonical
dates and aware datetimes; validation and domain exceptions are not caught or wrapped.

Codex local verification:

```text
Dedicated: 4 passed
Related: 75 passed, 245 subtests passed
Full suite: 2348 passed, 2 skipped, 976 subtests passed
Forbidden-dependency search: no matches
git diff --check: success
```

The initial implementation was subsequently committed as `225d7f7` and pushed to
`review/4c-2d3b1i5b2b-race-inputs` for GitHub review. `database/keiba.db` and `logs/` remain out of
scope. Phase 4C-2d3b1i5c remains unstarted.

## Phase 4C-2d3b1i5b2b Review Correction

Status remains `READY_FOR_REVIEW`. GitHub review identified that the original pre-scan could validate an
earlier race ID before it had verified every race schema. `_prevalidate_races()` now uses two passes:
all items are first confirmed as Mapping values with exact race keys, then all race IDs are validated,
deduplicated, and compared with the application budget-ID set. The focused failure-order case proves a
later malformed schema wins over an earlier invalid ID, while an invalid ID is reported once all schemas
are valid.

The initial dedicated suite had only four methods and did not provide the required matrix coverage. It
now covers the public surface and package-root non-export, exact type/path linkage, two-race assembly
with two past-race snapshots, canonical audit ordering, empty/budget-set cases, pre-scan ordering,
canonical dates, aware/Z datetimes, race/track/entry/audit boundaries, huge integer handling, past-race
absence/schema/numeric checks, cutoff fail-closed behavior, same-day/future past-race validation,
determinism, snapshot immutability, and the source/AST contract.

Codex local verification after the correction:

```text
Dedicated: 11 passed, 137 subtests passed
Related: 82 passed, 382 subtests passed
Full suite: 2355 passed, 2 skipped, 1113 subtests passed
Python: C:\Users\garim\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
Python version: 3.12.13
git diff --check: success
```

Only the assembler, its dedicated test, and this report changed in the review clone. `docs/CURRENT_PHASE.md`,
the 1i5b1 loader, 1i5b2a application assembler, 1i5a runner/composition, existing production/tests,
migration, schema, `scripts/database.py`, `main.py`, `config/settings.json`, CLI, and package root remain
unchanged. Phase 4C-2d3b1i5c remains unstarted.

## Phase 4C-2d3b1i5b2b Review Test Contract Correction

Status remains `READY_FOR_REVIEW`. GitHub re-review approved the production two-pass pre-scan without
any additional production change. This correction changes only the dedicated test contract and this
report; `scripts/simulation/persisted_simulation_race_inputs.py` and `docs/CURRENT_PHASE.md` have no
diff from review commit `88f2619`.

The valid two-race assertion now compares every `TrackConditionsSnapshot` field, every field of two
`PastRaceSnapshot` values (including the required `horse_id == race_entry_id` relationship), and every
`InputAuditEntry` field in canonical order. The audit contract now exercises the complete race-audit
matrix and the complete generic audit-stamp matrix at all six locations: track, entry, jockey, odds,
past-race absence, and past-race audit. It covers Mapping/schema failures, exact non-empty text fields,
aware/malformed/date-only/naive timestamps, both-null rejection, available-only, observed-only, both
timestamps, and `Z` timestamps.

Track, entry, and past-race coverage now includes their missing/extra schema boundaries, entry and
past-race container/item boundaries, duplicate race-entry IDs, exact positive/non-negative numeric
rules, normal numeric boundaries, valid integer/float odds conversion, canonical past-race date
rejection, and huge integer finite limits. Snapshot testing now uses an exact document instance created
with `object.__new__`, a tuple root, and mutable nested dict/list source values. It proves source
mutations cannot alter assembled jockey, odds, track, past-race, or audit snapshots, and that output
Mappings, tuples, and frozen snapshot fields reject mutation. Determinism compares race order,
scheduled time, pipeline input, track/past-race snapshots, audit entries and key order, prediction time,
and dataset ID across two assemblies. Direct-input tests now assert the three exact `ValueError`
messages. Source AST checks retain exactly the two parser-owned `ValueError` handlers and prohibit
catching `Exception`, `BaseException`, `OverflowError`, or `SimulationValidationError`.

The dedicated suite now has 17 test methods and 332 subtests. Codex local verification after this test
contract correction:

```text
Dedicated: 17 passed, 332 subtests passed
Related: 88 passed, 577 subtests passed
Full suite: 2361 passed, 2 skipped, 1308 subtests passed
Python: C:\Users\garim\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
Python version: 3.12.13
git diff --check: success
```

Only `tests/test_persisted_simulation_race_inputs.py` and this report are modified for this correction.
The original repository `C:\Users\garim\Desktop\KeibaAI` is untouched. The review clone has no DB,
runner, migration, schema, CLI, package-root, `database/keiba.db`, or `logs/` change. Phase
4C-2d3b1i5c remains unstarted.

## Phase 4C-2d3b1i5b2b GitHub Review Approval

GitHub implementation review is complete. Base branch: `feature/ver0.8-simulator`; base commit:
`b06503c`; review branch: `review/4c-2d3b1i5b2b-race-inputs`. The approved commits are `225d7f7`,
`88f2619`, and `711e05f`. The production race assembler, its two-pass race-schema/race-ID pre-scan,
and all dedicated contract corrections are approved; no further production or test correction is
required. Base-branch integration is pending.

Approved behavior includes the exact document/application-input boundary and database-path identity
linkage; race-budget ID agreement before any DB responsibility; canonical dates, timezone-aware and
`Z` datetimes; race, track, entry, past-race, audit-stamp schemas; generated canonical audit keys;
huge-integer finite limits; existing `SimulationRaceInput` fail-closed validation; deterministic race,
entry, and audit ordering; and immutable pipeline snapshots. The full dedicated contract suite is
approved with 17 test methods and 332 subtests.

Codex local verification results (not GitHub CI results):

```text
Dedicated: 17 passed, 332 subtests passed
Related: 88 passed, 577 subtests passed
Full suite: 2361 passed, 2 skipped, 1308 subtests passed
Python: C:\Users\garim\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
Python version: 3.12.13
git diff --check: success
```

Phase 1i5b1, 1i5b2a, and 1i5a remain unchanged; Phase 1i5c remains unstarted. `main.py` and
`config/settings.json` remain unchanged. `database/keiba.db` and `logs/` remain out of scope.

## Phase 4C-2d3b1i5c Preparation and Approval

Phase 4C-2d3b1i5b2b is formally complete at `cd6f8e6`; remote base and its approved review branch are
identical. The canonical workspace is the clean clone `C:\Users\garim\Desktop\KeibaAI-review-1i5b2b`.
The original `C:\Users\garim\Desktop\KeibaAI` workspace must not be modified.

Phase 4C-2d3b1i5c is `APPROVED_FOR_CODEX`. It will add the request-application orchestration module,
the deterministic JSON CLI, their dedicated tests, and README documentation only. The orchestrator's
exact four-stage chain is immutable request loading, application-input assembly, audited race-input
assembly, then the existing SQLite application runner. It will pass the same document/application objects
and the exact application-owned path, run context, strategy identity, pipeline, budgets, and race-input
tuple; it adds no duplicate DB, migration, composition, repository, validation, sorting, or runner work.

The CLI will own argparse, supplied stdout/stderr streams, deterministic compact JSON envelopes, and exit
codes only. Success is `{schema_version: 1, status: "ok", summary: ...}` on stdout with exit 0. Expected
`OSError`, `sqlite3.Error`, `RuntimeError`, `TypeError`, and `ValueError` become one deterministic error
envelope on stderr with exit 1; argparse usage/help retain native `SystemExit(2)`/`SystemExit(0)` behavior.
Decimal rates serialize as fixed-point JSON strings (or null); `by_bet_type` is deterministically ordered.
`main.py` remains unchanged.

Required tests include real empty and settled file-backed SQLite E2E, snapshot-persistence verification,
relative database-path anchoring, error envelopes, argparse behavior, exact source/AST boundaries, and
the specified dedicated, related, and full-suite verification. No mock, patch, monkeypatch, subprocess,
or duplicate database/migration/repository responsibility is permitted.

Candidate implementation files are:

```text
scripts/simulation/persisted_simulation_request_application.py
scripts/cli/run_persisted_simulation.py
tests/test_persisted_simulation_request_application.py
tests/test_cli_run_persisted_simulation.py
README.md
docs/LATEST_CODEX_REPORT.md
```

1i5b1, 1i5b2a, and 1i5a remain unchanged; 1i5c alone owns request application and CLI presentation.
`database/keiba.db`, `logs/`, migration, schema, `scripts/database.py`, `main.py`, and
`config/settings.json` are out of scope. This design-only activity changed no production, test, or README
file. The approved design was subsequently committed and pushed for GitHub review; no DB or runner was
invoked.

## Phase 4C-2d3b1i5c Design Review Publication

Design commit: `9a7cabc docs: design persisted simulation CLI`

Review branch: `review/4c-2d3b1i5c-design`

Base commit: `cd6f8e6`

Changed files:

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

The design was committed and pushed for GitHub review. Production, tests, and README remain unchanged;
no DB or runner was invoked. Implementation remains unstarted and Status remains
`APPROVED_FOR_CODEX` until review approval is recorded below.

## Phase 4C-2d3b1i5c Design Review Approval

GitHub design review is complete.

```text
Base branch: feature/ver0.8-simulator
Base commit: cd6f8e6
Review branch: review/4c-2d3b1i5c-design
```

Approved commits:

```text
9a7cabc docs: design persisted simulation CLI
35612b9 docs: correct persisted simulation CLI design
```

The approved design is a thin request-application orchestrator with the exact four-stage call chain and
a deterministic JSON CLI. It explicitly defines the `SimulationSummary` and `BetTypeSummary` serializer
schemas, Decimal string/null serialization, stdout/stderr separation, exit codes 0/1/2, native argparse
help behavior, and the expected exception boundary. It also approves real temporary file-backed SQLite
E2E coverage, snapshot-persistence verification, unchanged `main.py`, no duplicate DB/migration/
repository responsibility, and the rule that the original workspace must not be modified.

## Phase 4C-2d3b1i5c Implementation

Status: `READY_FOR_REVIEW`

Base branch: `feature/ver0.8-simulator`

Base commit: `e43a9be docs: approve persisted simulation CLI design`

Implemented the approved thin request application boundary at
`scripts/simulation/persisted_simulation_request_application.py`. Its only public function runs the
exact four-stage chain once: immutable request-document loading, application-input assembly, audited
race-input assembly, and the existing SQLite persisted-simulation runner. It adds no duplicate database,
migration, composition, repository, validation, sorting, retry, cache, logging, or exception handling.
Collaborator exceptions therefore retain their original object identity.

Implemented `scripts/cli/run_persisted_simulation.py` with the approved `build_parser()`, `run()`, and
`main()` public APIs. The parser has exactly one `Path` positional request path. Successful calls produce
one compact, deterministic, UTF-8 JSON success envelope on stdout and exit `0`; expected OSError,
RuntimeError, TypeError, ValueError, and sqlite3 errors produce one compact JSON error envelope on stderr
and exit `1`. Native argparse help and argument errors retain `SystemExit(0)` and `SystemExit(2)`.

The CLI explicitly serializes every current `SimulationSummary` and `BetTypeSummary` field. Decimal rates
are fixed-point strings or JSON null, and `by_bet_type` is ordered deterministically. No traceback,
fallback, retry, dynamic dataclass serialization, or extra DB/migration/repository responsibility was
introduced. `main.py` remains unchanged.

New dedicated coverage verifies formal APIs and AST responsibility boundaries, deterministic serializer
schema/Decimal behavior, argparse behavior, expected error envelopes, the real empty relative-path
file-backed SQLite path, and a real settled one-entry win path (100 investment, 300 payout, 200 profit)
including persisted snapshot verification. No mock, patch, monkeypatch, or subprocess is used.

README now documents the request CLI invocation, request-relative database path rule, stdout/stderr
contract, exit codes 0/1/2, Decimal string/null policy, and the research-only/no-profit-guarantee notice.

Codex local verification:

```text
Request application dedicated: 3 passed
CLI dedicated: 7 passed, 6 subtests passed
Related: 91 passed, 583 subtests passed
Full suite: 2371 passed, 2 skipped, 1314 subtests passed
Python: C:\Users\garim\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
Python version: 3.12.13
Forbidden-dependency/source search: approved boundary matches only
git diff --check: success
```

Only the six approved 1i5c files were changed: the new request application and CLI modules, their new
dedicated tests, README, and this report. `docs/CURRENT_PHASE.md`, existing production/tests, migration,
schema, `scripts/database.py`, `main.py`, configuration, package roots, `database/keiba.db`, `logs/`, and
the original workspace remain untouched. The initial implementation commit `c098cf8 feat: add persisted
simulation CLI` was committed and pushed to `review/4c-2d3b1i5c-implementation` for GitHub review; the
base branch remains unchanged. Phase 4C-2d3b1i5c now awaits implementation review.

## Phase 4C-2d3b1i5c Review Test Contract Correction

Status remains `READY_FOR_REVIEW`. GitHub review approved the production implementation and README without
correction. This correction changes only the two dedicated test files and this report on
`review/4c-2d3b1i5c-implementation`.

The application contract now asserts its exact four-statement AST body and call order, each keyword
linkage, direct runner return, no Try/Except, approved dependency boundary, and the full empty-summary
and file-backed database contract. The CLI contract now asserts its exact public APIs and type hints,
the single expected exception boundary, forbidden imports/symbols, all summary and bet-type serializer
fields, Decimal strings and nulls, deterministic compact Unicode JSON and sorted bet-type keys.

The empty and settled E2E contracts now assert all approved summary values, stdout/stderr ownership,
schema migration and snapshot tables, persisted snapshot count, and post-run reconnection. Expected error
coverage includes missing request, malformed JSON, root/application/race-audit failures, database-open
failure, and unknown future migration; every error is one stderr JSON envelope with no traceback. Native
argparse missing, extra, and help cases are also covered. The future-migration fixture additionally proves
that the temporary database can be reopened after the failed runner-owned connection closes.

Codex reran the dedicated, related, and full suites locally after this correction. Production, README,
`docs/CURRENT_PHASE.md`, `database/keiba.db`, `logs/`, and the original workspace remain unchanged.

```text
Request application dedicated: 3 passed
CLI dedicated: 9 passed, 6 subtests passed
Related: 93 passed, 583 subtests passed
Full suite: 2373 passed, 2 skipped, 1314 subtests passed
Python: C:\Users\garim\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
Python version: 3.12.13
```

## Phase 4C-2d3b1i5c Final Review Test Closure

Status remains `READY_FOR_REVIEW`. Production and README remain approved and unchanged. This final review
closure changes only the two dedicated test files and this report.

The application source contract now also rejects sys, clock, subprocess, requests, main/config,
environment access, and source-level sort/copy/list/tuple calls. The CLI serializer now uses a valid
multi-bet-type `SimulationSummary` to prove the payload order is the exact sorted bet-type order while
retaining every `BetTypeSummary` field, key/value identity, and Decimal-string rules.

Success and expected-error streams now explicitly require exactly one newline-terminated JSON record with
no blank second line. Error coverage also rejects both traceback and stack-trace text. Settled coverage
uses the explicit single bet-type key and verifies the nested `bet_type` field. CLI AST coverage now
asserts one Try, one expected handler, one application call, `main()` as direct `return run()`, and no
`sqlite3.connect`; application AST coverage additionally asserts the forbidden dependency/call boundary.

Codex reran the dedicated, related, and full tests locally after this closure. The original workspace,
`database/keiba.db`, and `logs/` remain unchanged. `git diff --check` succeeded.

```text
Request application dedicated: 3 passed
CLI dedicated: 10 passed, 6 subtests passed
Related: 94 passed, 583 subtests passed
Full suite: 2374 passed, 2 skipped, 1314 subtests passed
Python: C:\Users\garim\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
Python version: 3.12.13
```

## Phase 4C-2d3b1i5c GitHub Review Approval

GitHub implementation review is complete.

```text
Base branch: feature/ver0.8-simulator
Base commit: e43a9be
Review branch: review/4c-2d3b1i5c-implementation

Approved commits:
- c098cf8 feat: add persisted simulation CLI
- c2a8f9e test: complete persisted simulation CLI contract
- ecf472c test: close persisted simulation CLI review gaps
```

Approved: thin persisted request application boundary; exact four-stage call order and identity linkage;
unchanged application exception identity; compact deterministic success/error JSON; explicit
SimulationSummary and BetTypeSummary schemas; Decimal fixed-point string/null serialization; sorted
by_bet_type; stdout/stderr separation; exit codes 0/1/2; native argparse help; the single expected CLI
exception boundary; empty and settled file-backed SQLite E2E; snapshot persistence and post-run DB
reconnection; expected-error matrix; source/AST dependency boundaries; README CLI documentation and
research-use disclaimer; unchanged main.py; and no duplicate DB/migration/repository responsibility.

Codex local verification:

```text
Request application dedicated: 3 passed
CLI dedicated: 10 passed, 6 subtests passed
Related: 94 passed, 583 subtests passed
Full suite: 2374 passed, 2 skipped, 1314 subtests passed
Python version: 3.12.13
git diff --check: success
```

Production implementation, README, and dedicated test contracts require no further correction. Base
integration is pending. The original workspace remains unchanged; `database/keiba.db` and `logs/` remain
unchanged.

## Post-1i5c Next Phase Proposal

Status: `PROPOSED_FOR_REVIEW`

Phase 4C-2d3b1i5c integration is complete. The base branch and the approved implementation-review
branch both resolve to `154c04d`. Codex local verification for the integrated implementation was:

```text
Request application dedicated: 3 passed
CLI dedicated: 10 passed, 6 subtests passed
Related: 94 passed, 583 subtests passed
Full suite: 2374 passed, 2 skipped, 1314 subtests passed
git diff --check: success
```

The completed responsibility chain is intentionally reused rather than recreated:

```text
load_persisted_simulation_request_document
  -> assemble_persisted_simulation_application_inputs
  -> assemble_persisted_simulation_race_inputs
  -> run_persisted_simulation_request
  -> run_sqlite_persisted_simulation
  -> python -m scripts.cli.run_persisted_simulation <request_path>
```

It already provides immutable request loading and assembly, a single SQLite lifecycle/migration/composition
owner, deterministic success and error JSON, file-backed E2E coverage, and persisted bet-plan snapshots.
The next phase must not duplicate any of those boundaries.

### Remaining gaps

- There is no checked-in, canonical request document that an operator can copy as the safe first CLI
  invocation. The existing tests construct request dictionaries privately; they are not an operational
  artifact.
- The current successful CLI payload is a single `SimulationSummary` written to stdout. It does not yet
  create the design-level `SimulationReport` with race detail, multi-strategy comparison, or JSON/CSV
  artifact persistence.
- No DB-backed request generator exists. Constructing one now would require a separate approved policy for
  time-valid race, audit, and availability data; it must not infer those fields from the current SQLite
  schema.
- No batch-request or multi-strategy execution contract exists. Independent capital-curve and failure
  semantics remain a larger report/orchestration design question.

### Candidate A — Phase 4C-2d3b1i5d: Canonical persisted-simulation request example

**Purpose.** Add one schema-valid, empty persisted-simulation request example and concise usage guidance.
It is an operational health-check starting point, not a synthetic ROI example and not a DB data generator.

| Item | Proposal |
| --- | --- |
| Production files | None. Reuse the existing loader, assemblers, request application, runner, and CLI unchanged. |
| New files | `examples/persisted_simulation_empty_request.json`; `tests/test_persisted_simulation_request_example.py`. |
| Existing files | `README.md` only, to state copy/use semantics and that the sample has no races. |
| DB/migration | No product DB or migration change. The dedicated E2E test copies the example to a temporary directory and lets the existing runner create only a temporary file-backed SQLite database. |
| Connection points | `load_persisted_simulation_request_document()` validates the checked-in document; `run_persisted_simulation_request()` and the existing CLI execute the copied sample. |
| Completion | The exact request schema is loader-valid, its relative database path anchors to the copied request parent, and the existing CLI returns the deterministic empty-summary JSON without touching `database/keiba.db`. |
| Risks | An empty request is a plumbing/operational sample, not evidence of ROI. README wording must prevent it from being presented as a real race-data template. |
| Why now | It is the smallest independently reviewable gap between a tested CLI and a user-copyable invocation, and it introduces no new runtime responsibility. |

### Candidate B — Persisted simulation summary artifact writer

**Purpose.** Persist an explicit, deterministic `SimulationSummary` JSON artifact after a successful run.

| Item | Proposal |
| --- | --- |
| Production files | A new dedicated summary-artifact writer module only. |
| Test files | A new writer contract test with temporary output paths. |
| Existing files | No existing runner/repository change in the first split; later CLI integration would be separate. |
| DB/migration | None. |
| Connection points | Existing `SimulationSummary` and the established Decimal/null and sorted-bet-type serialization rules. |
| Completion | Exact output schema, deterministic bytes, safe file-write failure propagation, and no duplicate SQLite lifecycle. |
| Risks | The current CLI already emits a summary JSON document, while the Ver0.8 design-level report requires race detail and multi-strategy metadata. A writer added without a report contract could create a competing, incomplete output format. |
| Why not now | Its public artifact schema and ownership relative to the existing stdout serializer require design approval first. |

### Candidate C — DB-backed request-input assembly

**Purpose.** Build a persisted-simulation request from stored race data instead of hand-authored JSON.

| Item | Proposal |
| --- | --- |
| Production files | New read-only SQLite request-input assembler/repository boundary. |
| Test files | New temporary-DB integration suite with time/audit fixtures. |
| Existing files | Potentially a separate request-generation API; the existing loader/runner should remain unchanged. |
| DB/migration | Schema changes are not assumed, but the current data-availability/audit provenance must be proven before this can be designed. |
| Connection points | Existing immutable request document and race-input assembler contracts. |
| Completion | Every generated race/past-race/track/audit value has validated provenance and preserves the fail-closed cutoff rules. |
| Risks | The current schema does not by itself define the source of every `available_at`/`observed_at` audit value. Guessing would violate the simulator's future-information policy and duplicate the approved request boundary. |
| Why not now | This is a data-collection/request-generation phase, materially larger than the next independent operational increment. |

### Candidate D — Multi-request and multi-strategy execution report

**Purpose.** Produce the existing design-level `SimulationReport` across strategies and races.

| Item | Proposal |
| --- | --- |
| Production files | A new report/orchestration boundary, with carefully scoped extensions to result collection. |
| Test files | New multi-strategy and race-detail report contract/integration tests. |
| Existing files | Likely `PersistedSimulationRunService`/`Simulator` result-capture contracts, which currently return only `SimulationSummary`. |
| DB/migration | No schema change is assumed, but no product DB access may be added merely for reporting. |
| Connection points | Existing `SimulationReport`, `SimulationRunMetadata`, `SimulationResult`, and `SimulationSummary` models. |
| Completion | Deterministic multi-strategy result capture, explicit official-ROI validity, and unambiguous race-detail serialization. |
| Risks | It mixes result capture, reporting, strategy comparison, and independent capital-curve decisions; the design lists the latter as unresolved. |
| Why not now | It must be split after a separate report/result-capture design approval and is not a minimal phase. |

### Recommendation

Recommend **Phase 4C-2d3b1i5d — Canonical persisted-simulation request example**.

It is closest to making the already-complete CLI safely runnable by an operator: it reuses every completed
boundary, adds no production composition or repository logic, requires no migration or DB contract change,
and has a focused temporary-file dedicated test. It also creates a clear handoff point before the larger
future work of DB-derived request generation, run-level reporting, ROI analysis, batch execution, and
multi-strategy comparison. Candidate B is the next likely reporting direction after an explicit artifact
contract; Candidates C and D are deliberately deferred because their missing provenance and aggregation
decisions are not safe to infer.

The original workspace remains unchanged. `database/keiba.db` and `logs/` remain unchanged and out of
scope. No candidate has been implemented, staged, committed, pushed, or put on a review branch.

## Post-1i5c Next Phase Proposal Review

The previous recommendation, **Phase 4C-2d3b1i5d — Canonical persisted-simulation request example**,
has the review disposition `REJECTED_AS_NEXT_PHASE`.

The repository already contains both empty-request and settled-win request fixtures inside the completed
1i5c CLI tests, including real file-backed SQLite E2E and snapshot-persistence coverage. A checked-in
sample would therefore duplicate test-only data without establishing the provenance, historical-audit,
or real-race request-generation boundary required for Ver0.8. It remains a lower-priority documentation
candidate, not the next implementation or design phase.

## Post-1i5c Revised Next Phase Proposal

Status: `PROPOSED_FOR_REVIEW`

Current integrated HEAD: `154c04de40cbae6898c0a8b3ff67eb3891da1456`

Phase 4C-2d3b1i5c is complete: the base and implementation-review branches are both at `154c04d`, and
the completed chain remains:

```text
load_persisted_simulation_request_document
  -> assemble_persisted_simulation_application_inputs
  -> assemble_persisted_simulation_race_inputs
  -> run_persisted_simulation_request
  -> run_sqlite_persisted_simulation
  -> python -m scripts.cli.run_persisted_simulation <request_path>
```

This chain deliberately consumes an already-audited request document. It must not be repurposed to
invent, backfill, or silently derive historical prediction inputs.

### Request field-source matrix and audit findings

| Request field group | Current possible source | Provenance state | Result |
| --- | --- | --- | --- |
| `schema_version`, `database_path`, `run_context`, `strategy`, `pipeline`, budgets | Explicit request JSON and existing loader/application-input assembler | User-supplied and fully validated, but not DB-generated | Reusable unchanged. |
| Race identity, target date, scheduled start | Legacy `races` table has `id`, `race_date`, and text `start_time` | No source/audit identity, `available_at`, `observed_at`, or snapshot `captured_at` is persisted for prediction use | Cannot safely generate an audited historical request. |
| Track conditions | Legacy `races` table has place/distance/track/condition values | No historical input-audit stamp is stored | Cannot meet the request schema's required audit stamp. |
| Entries and jockey names | Legacy `horses` table is race-scoped and already supports the shared JRA/local row identity model | No input availability/observation timestamp or snapshot provenance is stored | Cannot safely assert cutoff availability. |
| Entry odds | Legacy `horses.odds`; v008 `odds_snapshot_batches` and `OddsSnapshotRepository` provide observed-time batches | Legacy odds lack history. v008 batches retain `observed_at`, but no historical `available_at` is persisted and no approved request-source mapping exists for all prediction inputs | Must not substitute later/current odds or infer availability. |
| Past races | Legacy `past_races` table and existing `PastRace` conversion | No source ID, available/observed time, or historical snapshot capture record | Cannot establish that every past-race fact was usable by the prediction cutoff. |
| Race, track, entry, jockey, odds, and past-race audit stamps | Existing request schema requires exact `source`, `source_id`, and at least one aware `available_at`/`observed_at`; `InputSnapshotAudit` also requires aware `captured_at` | No repository/schema persists a complete corresponding input-audit/snapshot set | Manual JSON is valid only when externally evidenced; DB-backed generation is blocked. |
| Results and payouts | v008 repositories persist `observed_at` and, when complete, `finalized_at` | These are settlement facts, not prediction-input provenance, and are allowed after prediction cutoff | Reuse only for settlement; never route them into request generation. |

The future-information rule is explicit: every prediction, entry, track, jockey, odds, and past-race input
must have `available_at` or `observed_at <= information_cutoff`; a missing stamp fails closed. In
particular, later odds must not fill an unavailable historical value. Existing `odds_snapshot_batches`
therefore do not close the request-generation gap by themselves.

The current generic race/horse identity supports both local racing and JRA without a separate ID model,
but the implemented acquisition foundation is NAR/local. There is no approved JRA request-source mapping,
organization discriminator policy, source URL/ID convention, or historical availability contract. JRA
connection work must remain a separate provider/source-design concern.

### Revised candidates

#### Candidate A — Phase 4C-2d3b1i6a: Historical input snapshot and audit persistence gap design

| Item | Proposal |
| --- | --- |
| Objective | Design the minimal source, snapshot, audit, and fail-closed contracts needed before a DB-backed persisted-simulation request can exist. |
| Production files | None. |
| Test files | None. This is a design-only phase. |
| Documentation files | `docs/CURRENT_PHASE.md` and `docs/LATEST_CODEX_REPORT.md`; amend the authoritative simulator design only if the approved phase explicitly directs it. |
| Existing API connection | The existing request document, `InputAuditEntry`, `InputSnapshotAudit`, `SimulationRaceInput`, legacy DB tables, v008 odds/result/payout repositories, and 1i5c application chain. |
| DB/migration impact | None in 1i6a. It identifies, but does not implement, the later schema/repository changes needed to persist historical input snapshots and audit stamps. |
| Completion criteria | A field-by-field authoritative source mapping; timestamp semantics; audit key/source ID policy; local/JRA organization boundary; exact fail-closed behavior; and a split, sequenced proposal for any later schema/migration/source phases. |
| Main risk | Treating legacy values or later observation times as proof of cutoff availability would create invalid ROI. The phase must record uncertainty instead of repairing it. |
| Why now | It is the smallest prerequisite that advances Ver0.8 toward real, reproducible ROI while avoiding a speculative request builder. |

#### Candidate B — Historical input snapshot and audit persistence schema/migration

| Item | Proposal |
| --- | --- |
| Objective | Persist the approved prediction-input snapshot and its audit stamps once Candidate A has fixed the data model. |
| Production/test files | New migration/repository modules and focused temporary-DB migration/repository tests, selected only after the 1i6a contract identifies exact names and fields. |
| Existing API connection | Candidate A's source/audit contract, `InputSnapshotAudit`, `InputAuditEntry`, and the current SQLite migration runner. |
| DB/migration impact | Yes; this is a separate schema/migration phase. |
| Completion criteria | Immutable stored snapshots preserve every required field, source ID, timezone-aware audit stamp, and cutoff-relevant fact without altering legacy records. |
| Main risk | Premature table design could lock in an unusable provenance model or mix settlement facts with prediction inputs. |
| Why later | It has no safe schema until Candidate A resolves the field-source and timestamp contract. |

#### Candidate C — Audited DB-backed persisted-simulation request source

| Item | Proposal |
| --- | --- |
| Objective | Construct a request-equivalent immutable input from only persisted, audit-complete historical data. |
| Production/test files | A new read-only source/assembler boundary and dedicated temporary-DB integration tests, without changing the 1i5c runner or CLI. |
| Existing API connection | Candidate B's persisted input snapshots; existing request/application/race assemblers or an explicitly approved equivalent boundary. |
| DB/migration impact | No additional change assumed beyond Candidate B. |
| Completion criteria | Exact race/budget selection, audit-complete input retrieval, cutoff validation, and object construction fail closed before prediction execution. |
| Main risk | It must not fabricate request JSON, fill missing historical data, or fold DB, JSON writing, CLI, batch execution, and reporting into one phase. |
| Why later | It requires a completed persistence contract and real persisted audit evidence. |

#### Lower-priority candidate — Canonical request example

Retain the former 1i5d idea only as a documentation phase after the audited generation path is defined.
It may later explain how to run an externally evidenced request, but it must not claim that a test fixture
or a manually written request establishes historical data availability.

### Recommendation and follow-up order

Recommend **Phase 4C-2d3b1i6a — Historical input snapshot and audit persistence gap design**.

Its scope is intentionally design-only: source architecture, request-field mapping, timestamp/audit
validation, fail-closed policy, and the split to later persistence/source phases. It excludes production
implementation, tests, migrations, schema changes, DB access, request-file generation, CLI work, runner
changes, batch execution, reporting, and strategy comparison.

Proposed order:

```text
1i6a  historical input snapshot and audit persistence gap design
1i6b  approved schema/migration and repository persistence for that audit-complete snapshot
1i6c  audited DB-backed persisted-simulation request source
later  request documentation, batch execution, report artifacts, and multi-strategy comparison
```

This advances the real operational requirement without disguising missing provenance as a runnable
simulation input. The original workspace remains unchanged. `database/keiba.db` and `logs/` remain
unchanged and out of scope. No candidate has been implemented, staged, committed, pushed, or put on a
review branch.

## Phase 4C-2d3b1i6a Design Report

Historical draft status: superseded; it was not approved.

Phase 4C-2d3b1i6a is the approved design-only response to the historical input snapshot and audit
provenance gap. Base commit: `154c04de40cbae6898c0a8b3ff67eb3891da1456` on
`feature/ver0.8-simulator`. The canonical workspace is
`C:\Users\garim\Desktop\KeibaAI-review-1i5b2b`; the original workspace remains unchanged.

The previous Phase 4C-2d3b1i5d canonical sample-request proposal is
`REJECTED_AS_NEXT_PHASE`. A sample request cannot prove historical availability and is deferred until an
auditable source exists.

### Approved audit and snapshot design

- Historical provenance is a complete race-level prediction-input snapshot with normalized child records
  and normalized audit rows, not a schemaless JSON document.
- The selected groups are race metadata, race entries, jockey data, track conditions, win odds, past
  races, and explicit past-race-absence evidence.
- Each group has a natural relation to the snapshot/race/race entry, source metadata, a stable source ID,
  audit timestamps, completeness evidence, and deterministic reconstruction order.
- `available_at` is source-public availability, `observed_at` is KeibaOS observation of the exact value,
  `captured_at` is complete snapshot capture, and `finalized_at` is settlement-only. Future audit times
  are timezone-aware UTC ISO timestamps.
- Every `InputAuditEntry` requires `available_at` or `observed_at`. Observed-only and available-only
  records have separate explicit rules; both timestamps describe the same value and satisfy
  `available_at <= observed_at <= captured_at`. Unknown or invalid provenance fails closed.
- Future cutoff selection uses race ID, information cutoff, input type, and source policy; it accepts only
  one complete snapshot whose header and all relevant audit timestamps are no later than the cutoff. It
  cannot mix records or use a later fallback. The deterministic future tie-break is latest `captured_at`,
  then `snapshot_id` descending.

### Existing-data findings and boundary

- Legacy `races`, `horses`, and `past_races` lack required historical source/timestamp provenance. They
  may remain references or prospective capture sources, but cannot be backfilled or used as formal
  historical DB-backed prediction input.
- v008 odds snapshots retain `observed_at`, completeness, source, and source URL but lack
  `available_at`. Until observed-only eligibility is separately approved, that absence means they cannot
  support official historical odds validation. A later approval must define that eligibility, any
  availability requirement, complete odds-batch granularity, and win-odds selection-to-entry mapping.
  Legacy `horses.odds` is not eligible for official historical odds validation.
- A future JRA/local source contract must distinguish organization, source system, external race/entry
  identifiers, canonical URL, internal mapping, and horse number. Current `horses.id` is internal and
  race scoped; `horse_no` is not an external provider identity.
- Settlement `race_results`, `race_result_entries`, `payout_publications`, and `payouts` remain separate.
  Their finalization/observation provenance must not become prediction-input audit evidence.

### Future implementation boundary

The approved sequence is: schema/domain design approval, migration, repository contracts, SQLite
repository implementation, and request-source integration. Future persistence must be normalized,
insert-only, idempotency-aware, conflict/data-integrity explicit, constrained and indexed, and
transactionally written. `source_id` must be a stable provider external ID, canonical URL, or later
approved canonical content digest; it must never use `hash()`, insertion order, or random UUID.

This activity changed only `docs/CURRENT_PHASE.md`, `docs/LATEST_CODEX_REPORT.md`, and
`docs/VER0.8_SIMULATOR_DESIGN.md`. Production, tests, README, migrations, schema, database files, and
logs were not changed. No stage, commit, push, branch creation, database operation, runner execution,
CLI execution, or pytest execution was performed.

## Phase 4C-2d3b1i6a Design Review Findings

- Review result: `PARTIAL`.
- Approval disposition: `NOT_APPROVED`.
- Revision status: `REVISION_REQUIRED`.
- PASS: time semantics, cutoff fail-closed rule, legacy no-backfill policy, race-level snapshot boundary,
  settlement separation, and staged follow-up direction.
- PARTIAL: field-to-source mapping, audit-entry detail, repository responsibility, and JRA/NAR identity.
- FAIL: formal domain values/Protocol, normalized SQLite schema/identity/constraint/index design, and the
  authoritative observed-only odds policy.
- Required correction: complete the contracts above without starting production implementation.

Production implementation was not started while the revision was prepared.

## Phase 4C-2d3b1i6a Revised Design Report

Historical revised-draft status: superseded; it was not approved.

The revised authoritative design supersedes the preliminary 1i6a note. It now fixes the complete
field-to-source/audit matrix for race metadata, race entry, jockey, track, WIN odds, past races, and
past-race absence evidence. Each field records request path, snapshot field, source record, source system,
stable source ID, source URL policy, availability/observation provenance, audit key, relation, ordering,
completeness rule, and legacy no-backfill result.

The design defines exact audit keys, `InputAuditEntry` field rules, UTC timestamp semantics, observed-only
and available-only eligibility, inclusive cutoff selection, deterministic ties, and source-identity digest
canonicalization. It explicitly approves observed-only v008 WIN-batch import only through an immutable
approved collection boundary with complete mapping and an eligible `observed_at`; all other v008 rows and
legacy `horses.odds` fail closed.

The following later domain values and keyword-only Protocols are approved for their dedicated follow-up:
`HistoricalSourceIdentity`, `HistoricalInputProvenance`, `HistoricalPastRaceSnapshot`,
`HistoricalRaceEntrySnapshot`, `HistoricalRaceSnapshot`, `HistoricalInputSnapshotIdentity`,
`HistoricalInputSnapshot`, `HistoricalInputSnapshotSource.load_latest_snapshot()`, and
`HistoricalInputSnapshotRepository.save_snapshot()`.

The normalized SQLite design now specifies source-race and source-entry mapping, snapshot header, race,
entry, past-race, and audit tables; natural identity; foreign keys; primary/unique/check constraints;
indexes; ordering columns; no-trigger policy; and domain/repository checks. Repository responsibilities
are fixed: caller-owned connection, one atomic insert-only transaction, canonical idempotent no-op,
conflict/data-integrity errors, rollback, deterministic complete-snapshot read, and no repair/retry/fallback.

JRA/NAR source identity is fixed to organization plus source system and external race/entry IDs, mapped
explicitly to internal race/race-entry IDs. `horse_no` remains only a local race number. Settlement records
remain excluded. The minimal implementation sequence is 1i6b1 domain/Protocols, 1i6b2 migration/schema,
1i6b3 write repository, 1i6b4 read source, then 1i6c request-source integration.

Completion criteria: all 13 revised 1i6a criteria are `PASS`. The former provenance/odds policy blocker is
superseded by this completed design; implementation remains deferred to the separately reviewed phases.

This revision changed only `docs/CURRENT_PHASE.md`, `docs/VER0.8_SIMULATOR_DESIGN.md`, and
`docs/LATEST_CODEX_REPORT.md`. Production, tests, README, migration, schema, DB files, logs, and the
original workspace remain unchanged. No stage, commit, push, branch creation, DB/migration/runner/CLI
execution, or pytest execution was performed.

## Phase 4C-2d3b1i6a Final Design Review Findings

review result: `REVISION_REQUIRED`
approval disposition: `NOT_APPROVED`

The final review identified an identity contradiction, incomplete SQLite schema and field-to-source mapping,
incomplete domain contracts, transaction/completeness gaps, incomplete v008 odds provenance, and blocker
consistency failure. Production implementation was not started.

## Phase 4C-2d3b1i6a Final Contract Revision

Historical final-draft status: superseded; it was not approved.

The final revision establishes one identity shared by domain equality, idempotency, and SQLite `UNIQUE`;
the frozen domain contract; explicit source-ID canonicalization; exact normalized table set, key/constraint/
trigger/index requirements; field-level provenance reconstruction; rejected-active-transaction writer
ownership; deterministic reader/tie-break; completeness states; trusted observed-only v008 WIN policy;
and JRA/NAR external-to-internal mapping. The final design section in
`docs/VER0.8_SIMULATOR_DESIGN.md` is authoritative and supersedes earlier preliminary/revised wording.

All 15 final completion criteria are explicit: identity, domain, crosswalk, DDL, timestamp provenance,
InputAuditEntry correspondence, write/read semantics, completeness, v008/digest policy, identity mapping,
cutoff fail-closed, deterministic reconstruction, settlement separation, and phase split. Production,
tests, README, migration, schema, DB, logs, and the original workspace remain unchanged; no Git operation
or runtime command was performed.

## Phase 4C-2d3b1i6a Cross-contract Review V2

review result: `REVISION_REQUIRED`; approval disposition: `NOT_APPROVED`.
The review found identity/content-digest contradiction, dataset isolation gap, domain/DB mismatch,
incomplete DDL, impossible completeness trigger, timestamp/order/provenance mismatch, unprovable v008
trust, incomplete source-ID formats, and organization/source-system mismatch.

## Phase 4C-2d3b1i6a Cross-contract Contract Revision V2

Historical V2 draft status: superseded; it was not approved. The V2 draft described one natural identity,
dataset-isolated read API, external identity matching DB uniqueness, canonical UTC text, zero-based order,
logical audit provenance, implementable transaction/trigger order, explicit JRA/local organization codes,
and prospective collector-attested v008 import only. Earlier v008 rows are untrusted. The required V2
completion criteria are explicit; production has not started.

## Phase 4C-2d3b1i6a V3a GitHub Review Findings

Reviewed commit: `11b85ef2361c9ca82cd47481fa3fb7f070910333`
(`docs: define historical input snapshot v3a contracts`).

- Review result: `REVISION_REQUIRED`.
- Approval disposition: `NOT_APPROVED`.
- Overall 1i6a status: `REVISION_REQUIRED`.
- The reviewed V3a prose was not a complete executable design: the nine dataclasses lacked formal field
  declarations and validation boundaries; child payload fields were incomplete; the digest builder and
  digest signatures were absent; and the exact Protocol declarations were incomplete.
- The previous CURRENT_PHASE and report metadata incorrectly implied readiness or approval. Those claims
  are superseded. Production, tests, README, migration, schema, database files, and the original workspace
  remain unchanged.

## Phase 4C-2d3b1i6a V3a Contract Revision

Historical V3a status: superseded by the compatibility revision; it was not approved.

Overall 1i6a status: `REVISION_REQUIRED`.

The revision makes the domain/digest/API slice directly reviewable without treating it as overall approval:

- `docs/VER0.8_SIMULATOR_DESIGN.md` now contains nine separate frozen, slotted dataclass code blocks:
  `HistoricalSourceIdentity`, `HistoricalExternalRaceIdentity`,
  `HistoricalExternalEntryIdentity`, `HistoricalInputSnapshotIdentity`,
  `HistoricalRaceSnapshot`, `HistoricalRaceEntrySnapshot`, `HistoricalPastRaceSnapshot`,
  `HistoricalInputProvenance`, and `HistoricalInputSnapshot`.
- It fixes the sole domain equality/hash identity to `dataset_id`, `organization`, `source_system`,
  `external_race_id`, and UTC-normalized `captured_at`. `content_sha256`, `source_url`, internal IDs,
  cutoff, and a future SQLite surrogate are excluded. `source_url` is nullable final-field metadata with
  `compare=False` and `hash=False`.
- It specifies the complete schema-version-1 payload keys and every child key for source identity, race,
  entry, past-race, and provenance values; `content_sha256` is recomputed from, but omitted from, its own
  payload.
- It fixes the keyword-only payload builder and SHA-256 digest signatures, UTF-8 compact sorted JSON,
  Decimal fixed-point strings, canonical date/UTC datetime formatting, and all child ordering rules.
- It fixes the exact keyword-only `HistoricalInputSnapshotSource.load_latest_snapshot()` and
  `HistoricalInputSnapshotRepository.save_snapshot()` Protocol signatures. The source identity parameter is
  a required `HistoricalExternalRaceIdentity`; `None` means only no eligible complete snapshot.
- It enumerates exact-type, tuple-only, positive/non-bool ID, contiguous-order, duplicate, UTC,
  provenance-relation, past-race absence-evidence, SHA-256 format, and digest-recomputation validation.

V3b executable DDL, V3c source mapping and observed-only policy, and V3d cross-contract consolidation are
not complete and are not authorized by this revision. No implementation phase has begun.

## Phase 4C-2d3b1i6a V3a Compatibility Review

Reviewed commit: `a66cbdd11e1c20bb5474d396642cbbf14d1b3b46`
(`docs: complete historical input snapshot v3a contracts`).

- Review result: `REVISION_REQUIRED`.
- Approval disposition: `NOT_APPROVED`.
- Overall 1i6a status: `REVISION_REQUIRED`.
- The reviewed contract omitted executable validation bodies; did not retain
  `HistoricalInputProvenance.source`; omitted `scheduled_start_at`; and did not match the existing audit-key
  and input-type validation contract.
- `external_horse_id` incorrectly participated in external-entry identity, and constructor-supplied
  `content_sha256` made the digest construction circular.

## Phase 4C-2d3b1i6a V3a Compatibility Contract Revision

V3a status: `REVISION_REQUIRED`.

Overall 1i6a status: `REVISION_REQUIRED`.

Approval disposition: `NOT_APPROVED`.

The revision now records a complete Python-equivalent construction contract for all nine dataclasses,
including shared helper signatures and `ValueError` rules; exact type and bool rejection; NFC text,
UTC datetime, and Decimal canonicalization through `object.__setattr__`; tuple-only child collections; and
duplicate, order, provenance, timestamp, cutoff, and past-race relation validation.

`HistoricalInputProvenance` has the exact existing-audit-compatible field order:
`input_type`, `audit_key`, `source`, `source_id`, `race_entry_id`, `available_at`, `observed_at`, and
`past_race_index`. Its allowed audit key set is `track`, `entry/{race_entry_id}`,
`odds/{race_entry_id}`, `jockey/{race_entry_id}`, `past_race/{race_entry_id}/{past_race_index}`, and
`past_race/{race_entry_id}/none`; allowed input types are `track`, `entry`, `odds`, `jockey`, and
`past_race`. This permits lossless one-to-one reconstruction of the existing `InputAuditEntry`.

`HistoricalRaceSnapshot` now contains `target_race_date`, UTC-aware `scheduled_start_at`, `place`,
`distance_m`, `track`, and `track_condition`, with optional historical-only race name, class, and weather.
This makes the date and scheduled-start values required for `SimulationRaceInput` reconstruction explicit.
`HistoricalExternalEntryIdentity` now excludes optional `external_horse_id` metadata from equality, hash,
and duplicate-entry identity.

Snapshot content SHA-256 is derived, not supplied: structural validation and canonicalization run first,
the private unchecked payload helper runs second, SHA-256 is computed third, and the frozen derived field is
set fourth. Public builder/digest APIs omit the digest and are never used from `__post_init__`. A repository
load owns stored-digest comparison and raises `RepositoryDataIntegrityError` on mismatch; a save writes only
the derived digest.

Self-review of this revision:

1. PASS — all nine classes specify executable construction/validation contracts.
2. PASS — provenance retains every `InputAuditEntry` field.
3. PASS — audit keys and input types exactly match existing validation.
4. PASS — race date and scheduled start can reconstruct `SimulationRaceInput`.
5. PASS — external horse metadata is outside external-entry identity.
6. PASS — digest construction has no constructor cycle.
7. PASS — repository load owns stored-digest validation.
8. PASS — cutoff and timestamp invariants are specified.
9. PASS — past-race and absence semantics match existing validation.
10. PASS — overall 1i6a remains `REVISION_REQUIRED`.

V3b executable DDL, V3c source mapping/policy, and V3d consolidation are not started. No production,
test, README, migration, schema, database, or original-workspace file changed.

## Phase 4C-2d3b1i6a V3a Final Review Findings

Reviewed commit: `05698a7`.

- Review result: `REVISION_REQUIRED`.
- Approval disposition: `NOT_APPROVED`.
- Missing before this revision: postponed-annotation import, external-entry/snapshot race linkage,
  available/observed/captured causal ordering, and Decimal scale canonicalization.
- Existing-audit compatibility, non-circular digest construction, scheduled-start preservation, and external
  horse metadata exclusion from entry identity were already resolved in the reviewed revision.

## Phase 4C-2d3b1i6a V3a Final Contract Revision

V3a status: `READY_FOR_REVIEW`.

Overall 1i6a status: `REVISION_REQUIRED`.

Approval disposition: `NOT_APPROVED`.

- The future module formally uses `from __future__ import annotations`, so private helpers may reference the
  nine domain values before their declarations under Python 3.12.
- Every entry external-race identity must equal the snapshot source organization, source system, and external
  race ID. `source_url` remains outside this comparison.
- Causal time ordering is `available_at <= observed_at <= captured_at <= information_cutoff <=
  scheduled_start_at`; nullable available/observed values each remain at or before capture.
- Decimal content values are canonicalized before digest serialization: `2`, `2.0`, and `2.00` serialize as
  `"2"`; both zero forms serialize as `"0"`; and `12.3400` serializes as `"12.34"`.
- Snapshot identity equality remains natural identity. Repository idempotency/conflict checks use natural
  identity plus derived `content_sha256`, never snapshot dataclass equality. Same identity plus same digest
  is an idempotent no-op; same identity plus different digest raises `RepositoryConflictError`.

Self-review:

1. PASS — Python 3.12 forward annotations are defined by the future import.
2. PASS — each entry external race identity must match the snapshot source identity.
3. PASS — available/observed/captured/cutoff/start causal ordering is complete.
4. PASS — numerically equal Decimal values produce one canonical content string.
5. PASS — repository comparison uses natural identity plus digest, not dataclass equality.
6. PASS — this revision is V3a documentation only.
7. PASS — overall 1i6a remains `REVISION_REQUIRED`.

V3b executable DDL, V3c source mapping/policy, and V3d consolidation remain unstarted. Production, tests,
README, migration, schema, database files, logs, and the original workspace remain unchanged.

## Phase 4C-2d3b1i6a V3a Past-race Compatibility Review

Reviewed commit: `8bd16bd`.

- Review result: `REVISION_REQUIRED`.
- Approval disposition: `NOT_APPROVED`.
- The existing `PastRace` contract permits an unavailable passing order as `passing_order=""`.
- The prior V3a `HistoricalPastRaceSnapshot.__post_init__` incorrectly passed this field through the
  non-empty-text validator.

## Phase 4C-2d3b1i6a V3a Past-race Compatibility Revision

V3a status: `READY_FOR_REVIEW`.

Overall 1i6a status: `REVISION_REQUIRED`.

Approval disposition: `NOT_APPROVED`.

`_normalize_text_allow_empty()` now accepts only exact `str`, NFC-normalizes it, and allows `""`.
`HistoricalPastRaceSnapshot.__post_init__` applies it only to `passing_order`; all other required
past-race text fields remain non-empty. The canonical payload retains `passing_order: str`, with missing
data serialized exactly as `{"passing_order":""}` rather than `null`, omission, or inferred content.

Self-review:

1. PASS — `passing_order` accepts exact `str`, including `""`.
2. PASS — `passing_order` is NFC-normalized.
3. PASS — missing passing order remains `""`, never `None`.
4. PASS — the digest payload preserves the empty string.
5. PASS — all other required past-race strings remain non-empty.
6. PASS — this is V3a documentation only.
7. PASS — overall 1i6a remains `REVISION_REQUIRED`.

V3b executable DDL, V3c source mapping/policy, and V3d consolidation remain unstarted. Production, tests,
README, migration, schema, database files, logs, and the original workspace remain unchanged.

## Phase 4C-2d3b1i6a V3a ChatGPT Approval

Reviewed commit:
`052a5c6e76a0f5bb0634be074bc1089bd81da663`.

Review result: `APPROVED`.

Approved scope: domain values, natural identity, canonical content digest, existing
`InputAuditEntry` compatibility, `HistoricalInputSnapshotSource` Protocol, and
`HistoricalInputSnapshotRepository` Protocol.

Disposition: `APPROVED_FOR_V3B`.

Overall 1i6a remains `REVISION_REQUIRED` with approval disposition `NOT_APPROVED`; V3b executable
DDL, V3c source mapping/policy, and V3d consolidation remain required.

## Phase 4C-2d3b1i6a V3b Executable DDL Design

V3b documents only the executable SQLite DDL and the exhaustive V3a domain-to-column crosswalk. The
planned, uncreated migration identity is `v010_historical_input_snapshot_schema`. No production migration,
registration, test, database access, or DDL execution occurred.

Read-only schema inspection confirmed: `races.id` is `INTEGER PRIMARY KEY`; `horses.id` is `INTEGER
PRIMARY KEY`; `horses.race_id` is the internal-race linkage; and legacy tables do not declare all required
foreign keys. The existing runner owns `PRAGMA foreign_keys = ON` verification, one per-migration
`BEGIN IMMEDIATE` transaction, commit, rollback, and the `schema_migrations` insert. The future migration
only calls `connection.execute(statement)` for its DDL and performs no legacy-data backfill.

The DDL specifies exactly eight historical-input tables:

- `historical_input_source_identities`
- `historical_input_external_races`
- `historical_input_external_entries`
- `historical_input_snapshots`
- `historical_input_snapshot_races`
- `historical_input_snapshot_entries`
- `historical_input_snapshot_past_races`
- `historical_input_snapshot_provenance`

It contains 8 `CREATE TABLE`, 4 `CREATE INDEX` (including the legacy composite-parent helper index), and 5
linkage-only `CREATE TRIGGER` statements. The header natural identity is exactly
`(dataset_id, organization, source_system, external_race_id, captured_at_utc)` and is enforced by the
matching SQLite `UNIQUE` constraint. Same natural identity plus same content SHA-256 is the planned
repository idempotent no-op; the same identity with a different digest remains a `RepositoryConflictError`.

`source_url` remains snapshot content rather than natural identity or global mapping metadata.
`external_horse_id` remains snapshot-entry content rather than external-entry identity. Decimal values are
canonical fixed-point `TEXT`, never `REAL`; UTC datetimes are canonical 32-character
`YYYY-MM-DDTHH:MM:SS.ffffff+00:00` `TEXT` with executable shape checks; and `passing_order` is `TEXT NOT
NULL`, preserving an unavailable value as the empty string. External-race rows link to `races(id)`;
external-entry rows use an executable `(internal_race_id, race_entry_id)` foreign key to
`horses(race_id, id)`; and snapshot-entry/header mapping consistency is enforced by linkage triggers. All
new-table foreign keys declare `ON DELETE RESTRICT ON UPDATE RESTRICT`.

The crosswalk contains 64 explicit domain-field rows across all nine V3a domain values. It allocates
canonical Decimal, NFC, calendar, ordering, contiguity, audit-key completeness, absence XOR, causal time,
and digest-reconstruction checks to repository/domain load validation, while retaining SQL-owned type,
nullability, key, foreign-key, coarse range, enum, and linkage invariants. It intentionally does not decide
provider field/source mapping, source-ID formats, JRA/local policy, v008 policy, or other V3c responsibilities.

V3b self-review:

1. PASS — exactly eight historical-input tables.
2. PASS — all V3a fields have storage columns.
3. PASS — header `UNIQUE` exactly matches natural identity.
4. PASS — `source_url` remains content, not identity.
5. PASS — `external_horse_id` remains content, not entry identity.
6. PASS — Decimal uses `TEXT`, never `REAL`.
7. PASS — `passing_order` allows empty string but not `NULL`.
8. PASS — fixed UTC format has executable checks.
9. PASS — external-race mapping links to `races.id`.
10. PASS — external-entry mapping proves `horses.race_id` consistency.
11. PASS — snapshot entries prove external-entry mapping consistency.
12. PASS — no impossible completeness trigger.
13. PASS — child order has explicit columns and indexes.
14. PASS — provenance has every `InputAuditEntry` field.
15. PASS — all FK delete/update actions are explicit.
16. PASS — query indexes are non-redundant.
17. PASS — a complete domain-to-column crosswalk exists.
18. PASS — no V3c policy is decided.
19. PASS — overall 1i6a remains `REVISION_REQUIRED`.

V3a status: `APPROVED`.

V3b status: `READY_FOR_REVIEW`.

Overall 1i6a status: `REVISION_REQUIRED`.

Production, tests, README, migration, schema, database files, logs, and the original workspace remain
unchanged. V3c and V3d remain unstarted.

## Phase 4C-2d3b1i6a V3b ChatGPT Review Findings

Reviewed commit: `27d82a6c2a37e095cb055876efd47d5b5ac5873b`.

Review result: `REVISION_REQUIRED`.

Approval disposition: `NOT_APPROVED`.

Findings:

- V3a NFC text normalization and V3b SQL `trim()` checks disagreed.
- Migration transaction ownership was ambiguous.
- The crosswalk used aliases rather than exact SQLite table names.
- A stray literal `+` line appeared before the V3b heading.

## Phase 4C-2d3b1i6a V3b Contract Alignment Revision

V3a accepts NFC-normalized text and rejects exact empty strings; it does not trim, strip, case-normalize, or
rewrite text. V3b required `TEXT` checks therefore now use only
`typeof(column_name) = 'text' AND column_name <> ''`. Optional V3a text accepts `NULL` or exact non-empty
`TEXT`. `passing_order` remains `TEXT NOT NULL` with only `typeof(passing_order) = 'text'`, preserving `""`.
NFC validation remains repository/domain work.

The existing migration runner exclusively owns foreign-key verification, the per-migration `BEGIN IMMEDIATE`
transaction, commit, rollback, and migration-record insertion. The future
`v010_historical_input_snapshot_schema.apply(connection)` only loops over `STATEMENTS + INDEXES + TRIGGERS`
and calls `connection.execute(statement)`. It must not issue transaction SQL, call `connection.commit()`,
`connection.rollback()`, or use `connection.executescript()`.

All 64 crosswalk rows now use exact V3b DDL table names; undocumented aliases were removed. The standalone
`+` before the V3b heading was removed. The DDL remains exactly 8 `CREATE TABLE`, 4 `CREATE INDEX`, and 5
`CREATE TRIGGER` statements; V3c source mapping/policy remains unstarted.

Self-review:

1. PASS — V3a-accepted text is not rejected by an extra SQL trim policy.
2. PASS — required `TEXT` rejects only exact empty strings at the coarse SQL level.
3. PASS — optional `TEXT` accepts `NULL` or exact non-empty `TEXT`.
4. PASS — `passing_order` still accepts `""`.
5. PASS — the migration runner exclusively owns transaction control.
6. PASS — future migration `apply()` uses `connection.execute()`, never `executescript()`.
7. PASS — all 64 crosswalk rows use exact full table names.
8. PASS — exactly eight tables, four indexes, and five triggers remain.
9. PASS — V3c policy has not started.
10. PASS — overall 1i6a remains `REVISION_REQUIRED`.

V3a status: `APPROVED`.

V3b status: `READY_FOR_REVIEW`.

Overall 1i6a status: `REVISION_REQUIRED`.

Overall approval disposition: `NOT_APPROVED`.

Production, tests, README, migration, schema, database files, logs, and the original workspace remain
unchanged. V3c and V3d remain unstarted.

## Phase 4C-2d3b1i6a V3b ChatGPT Approval

Reviewed commit: `524e3d729f40611bfec857d5152cc64ee023a1ab`.

Review result: `APPROVED`.

Disposition: `APPROVED_FOR_V3C`.

Approved scope: eight-table DDL, storage crosswalk, FK/linkage constraints, query indexes, trigger policy,
and the runner-owned transaction boundary. Overall 1i6a remains `REVISION_REQUIRED` with approval
disposition `NOT_APPROVED`.

## Phase 4C-2d3b1i6a V3c Source Mapping and Policy Design

V3c is documentation only. Read-only inspection covered the current NAR provider/parser, HorseParser,
JRAFetcher, legacy models/database, v008 simulation schema, migration runner, and existing input-audit
validation. No network, database, migration, runner, CLI, or test execution occurred.

The design fixes source-system literals `jra_official` and `nar_official`; organization literals `JRA` and
`NAR`; NAR external race ID `nar:{YYYYMMDD}:{k_babaCode}:{k_raceNo}`; and NAR external entry ID
`nar:{YYYYMMDD}:{k_babaCode}:{k_raceNo}:entry:{horseNum}`. The current NAR parser display value `地方` is
forbidden as an identity value. `external_horse_id` remains optional metadata and never becomes entry
identity. JRA external identities remain unsupported until a real official capture source exists.

`source_id` is `his-v1:{record_kind}:{sha256}` over a version-1 canonical UTF-8 JSON source-record payload.
The design fixes URL canonicalization, source record kinds, Decimal/UTC serialization, and forbids Python
hashes, random values, local database IDs, log filenames, temporary paths, and timestamp-only IDs.
`available_at` is an exact provider-publication time or `None`; `observed_at` is created when approved
collector code receives successful response bytes before parsing; and `captured_at` is successful complete
snapshot assembly time. Existing NAR code lacks this observation boundary and is therefore currently
ineligible for official historical snapshots.

All legacy `races`, `horses`, and `past_races` values are linkage-only and ineligible as historical content
or provenance. Existing v008 odds rows are `UNTRUSTED_FOR_OFFICIAL_HISTORICAL_INPUT`; `horses.odds` is
forbidden. Current JRA code is hard-coded sample data. Current HorseParser float conversion and `0.0`
fallback are not approved WIN-odds evidence. Past races use canonical zero-based order by
`(race_date, source_id)` ascending, and `/none` requires exact source evidence.

The V3c field-level source matrix has 64 rows covering every V3a scalar/normalized value, with JRA and NAR
origin or explicit current unsupported state for each. The current support matrix makes both source families
fail closed: no official historical snapshot is constructible until a future capture implementation obeys
this policy. V3b DDL is unchanged.

V3c self-review:

1. PASS — exact source-system and organization derivation.
2. PASS — exact NAR race and entry IDs; `external_horse_id` excluded from identity.
3. PASS — complete source-ID/digest/URL contract and forbidden-ID policy.
4. PASS — exact available/observed/captured timestamp origins.
5. PASS — every source-relevant V3a value has one of 64 matrix rows.
6. PASS — legacy, v008, and `horses.odds` policies fail closed.
7. PASS — V3b DDL unchanged; V3d unstarted.
8. PASS — overall 1i6a remains `REVISION_REQUIRED`.

V3a status: `APPROVED`.

V3b status: `APPROVED`.

V3c status: `READY_FOR_REVIEW`.

Overall 1i6a status: `REVISION_REQUIRED`.

Overall approval disposition: `NOT_APPROVED`.

Production, tests, README, migration, schema, database files, logs, and the original workspace remain
unchanged.

## Phase 4C-2d3b1i6a V3c ChatGPT Review Findings

Reviewed commit: `85a7fe4361c323b489a7e8339f280b931a789f0a`.

Review result: `REVISION_REQUIRED`.

Approval disposition: `NOT_APPROVED`.

Findings:

- The field-level matrix lacked its required per-field audit/source columns.
- Record-kind-specific canonical digest payloads were not fully enumerated.
- Past-race ordering conflicted with the existing newest-first prediction input.
- Official source URL host eligibility was not executable enough.

## Phase 4C-2d3b1i6a V3c Source Contract Revision

The normative field-level matrix is now exactly 64 rows and 11 columns: domain field; JRA official origin;
NAR official origin; provider field/HTML record; derivation allowed; source record kind; source-ID basis;
available-at origin; observed-at origin; missing-data policy; and legacy-reuse policy. No normative cell is
blank. The preceding four-column origin table is explicitly non-normative support-status context only.

The canonical source-ID envelope has fixed schema version 1 and six fully enumerated `record_values` schemas:
`track`, `entry`, `jockey`, `odds_win`, `past_race`, and `past_race_absence`. No extra record-values keys
are allowed. Digest input identifies parsed logical record values, never raw HTML bytes, CSS/DOM details,
parser representations, local paths, or local database IDs.

NAR official URL eligibility is machine-checkable: HTTPS, exact host `www.keiba.go.jp`, no credentials,
no fragment, and no non-default port; final redirected URLs must satisfy the same rule. JRA retains no host
allowlist and remains unsupported rather than guessed.

Past races are sorted by `(race_date DESC, source_id ASC)` before assigning zero-based index, so
`past_race_index = 0` is the newest applicable past race and remains compatible with existing
`get_past_races()` newest-first behavior. The V3a digest emits that stable index order.

V3c self-review: all 23 required items PASS. V3a and V3b remain approved; V3b DDL is untouched. V3c returns
to `READY_FOR_REVIEW`; overall 1i6a remains `REVISION_REQUIRED` with approval disposition `NOT_APPROVED`.
Production, tests, README, migration, schema, database files, logs, and the original workspace remain
unchanged. V3d remains unstarted.

## Phase 4C-2d3b1i6a V3c Absence-scope Review Finding

Reviewed commit: `88b7d623179a5f16b58b6a6f6b38fa35616a8150`.

Review result: `REVISION_REQUIRED`.

Approval disposition: `NOT_APPROVED`.

Finding: `past_race_absence.query_scope` lacked an exact canonical internal schema.

## Phase 4C-2d3b1i6a V3c Absence-scope Contract Revision

`query_scope` now has exactly three fixed keys: `external_entry_id`, `target_race_date`, and
`strictly_before_target_race`. No extra or omitted keys are allowed. The entry ID must exactly equal the
envelope entry ID; the target date must exactly equal `HistoricalRaceSnapshot.target_race_date`; and the
boolean must be exact `true`, limiting the scope to `past_race.race_date < target_race_date`.

The absence record requires exact integer `result_count = 0` (not `False`), a successful approved official
request, successful parsing, positively identified scope, and a valid complete result set. Database absence,
parser omission/failure, HTTP/network failure, unsupported pages, lookup failure, malformed/empty HTML,
legacy absence, and current refetches fail closed and never prove historical absence. The exact query-scope
object participates in the version-1 canonical digest, yielding
`his-v1:past_race_absence:{sha256}` for the same logical absence record.

The three related 64x11 matrix rows—`HistoricalInputSnapshot.past_races`,
`HistoricalInputProvenance.source_id`, and `HistoricalInputProvenance.past_race_index`—now use the exact
missing-data policy `exact validated absence query only`; no new matrix row was added.

V3a status: `APPROVED`.

V3b status: `APPROVED`.

V3c status: `READY_FOR_REVIEW`.

Overall 1i6a status: `REVISION_REQUIRED`.

Overall approval disposition: `NOT_APPROVED`.

V3c absence-scope self-review: all 13 required items PASS. Production, tests, README, migration, DDL,
schema, database files, logs, and the original workspace remain unchanged. V3d remains unstarted.

## Phase 4C-2d3b1i6a V3c ChatGPT Approval

Reviewed commit: `430add64f96c52db8d8cf86f86ea08fd1b7caac0`.

Review result: `APPROVED`.

Disposition: `APPROVED_FOR_V3D`.

Approved scope: source-system and organization policy; external identities; source URL eligibility;
source-ID/digest schemas; the 64x11 source matrix; provenance timestamps; past-race ordering; absence
evidence; and legacy/v008 fail-closed policy.

Overall 1i6a was `REVISION_REQUIRED` with disposition `NOT_APPROVED` at V3c approval.

## Phase 4C-2d3b1i6a V3d Consolidation Draft

V3d consolidates the approved V3a, V3b, and V3c contracts without production change. The authoritative
section establishes precedence, resolves repository selection and identity semantics, records a 31-row
cross-contract table, and passes all 20 implementation-readiness checks.

V3a status: `APPROVED`. V3b status: `APPROVED`. V3c status: `APPROVED`. V3d status:
`READY_FOR_REVIEW`. Overall 1i6a is `READY_FOR_FINAL_REVIEW` with disposition `NOT_APPROVED`.
Implementation authorization remains `NOT_YET_AUTHORIZED`.

Production, tests, README, migration, DDL, schema, database files, logs, and the original workspace remain
unchanged. V3d does not begin 1i6b1.

## Phase 4C-2d3b1i6a ChatGPT Final Approval

Reviewed V3d HEAD: `005457a7d4797de2286c70e0771438939a1aa818`.

V3a: `APPROVED`.

V3b: `APPROVED`.

V3c: `APPROVED`.

V3d: `APPROVED`.

Final phase result: `APPROVED`.

Implementation-readiness: 20/20 PASS.

Cross-contract consistency: 31/31 PASS.

Approved authoritative contract: V3a + V3b + V3c + V3d.

Next phase candidate: Phase 4C-2d3b1i6b1 — Historical input snapshot domain implementation.

Production implementation has not started in this integration commit.

## Phase 4C-2d3b1i6b1 Preparation

Status: `PHASE_4C_2D3B1I6B1_PREPARED`.

Formal base is `0ab53e57adaf4971cd8c576024d90647a6d1bf09` on
`feature/ver0.8-simulator`. The canonical workspace is
`C:\Users\garim\Desktop\KeibaAI-review-1i5b2b`; the original workspace remains untouched.

Inspected: `AGENTS.md`, `docs/CURRENT_PHASE.md`, `docs/LATEST_CODEX_REPORT.md`,
`docs/VER0.8_SIMULATOR_DESIGN.md`, `scripts/simulation/models.py`,
`scripts/simulation/validation.py`, `scripts/simulation/selection_resolver.py`,
`tests/test_simulation_models.py`, `tests/test_persisted_simulation_race_inputs.py`,
`tests/test_prediction_input_contracts.py`, and
`tests/test_race_entry_selection_resolver_contract.py`.

The proposed implementation files are
`scripts/simulation/historical_input_snapshots.py` and
`tests/test_historical_input_snapshots.py`; the only accompanying documentation files are
`docs/CURRENT_PHASE.md` and `docs/LATEST_CODEX_REPORT.md`. The proposed module has exactly 13 public API
members: nine dataclasses, two Protocols, and two public functions. It has no package-root export.

The implementation contract carries forward V3a/V3d's exact frozen/slotted values, natural identity,
metadata equality/hash exclusions, strict NFC/UTC/date/Decimal rules, `passing_order=""` compatibility,
provenance compatibility with `InputAuditEntry`, structural/audit/causal invariants, private construction-time
digest derivation, canonical payload ordering, and the exact keyword-only source/repository Protocols.
The current `InputAuditEntry` field shape and the existing resolver Protocol test style are compatible with the
approved single-module V3a contract.

Proposed verification commands after implementation:

```powershell
& "C:\Users\garim\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m pytest tests/test_historical_input_snapshots.py -q
& "C:\Users\garim\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m pytest tests/test_simulation_models.py tests/test_persisted_simulation_race_inputs.py tests/test_race_entry_selection_resolver_contract.py -q
& "C:\Users\garim\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m pytest -q
git diff --check
git status --short
```

Identified conflicts: none. `docs/CURRENT_PHASE.md` is `DRAFT_FOR_REVIEW`; production and tests remain
unchanged. `database/keiba.db` and `logs/` remain untouched. No stage, commit, or push was performed.

## Phase 4C-2d3b1i6b1 Preparation Approval

Status: `PHASE_4C_2D3B1I6B1_APPROVED_FOR_CODEX`.

ChatGPT preparation review result: `APPROVED`. No preparation corrections were required. The approved
implementation contract remains exactly as prepared: the formal base is
`0ab53e57adaf4971cd8c576024d90647a6d1bf09`, the branch is `feature/ver0.8-simulator`, and
`docs/CURRENT_PHASE.md` is `APPROVED_FOR_CODEX`. Implementation has not started.

Production, tests, `database/keiba.db`, and `logs/` remain untouched. No stage, commit, or push was
performed.

## Phase 4C-2d3b1i6b1 Execution

Status: `PHASE_4C_2D3B1I6B1_READY_FOR_REVIEW`.

Implemented the approved V3a/V3d domain contract from formal base
`0ab53e57adaf4971cd8c576024d90647a6d1bf09` on `feature/ver0.8-simulator` in the canonical workspace.

Created:

- `scripts/simulation/historical_input_snapshots.py`
- `tests/test_historical_input_snapshots.py`

The production module defines exactly 13 public API members: nine frozen, slotted domain dataclasses, two
keyword-only Protocols, and two public canonical payload/digest functions. It retains the approved natural
identity and metadata equality/hash exclusions; applies strict exact-type, NFC, UTC, date, Decimal, numeric,
provenance, child-completeness, causal-time, and past-race absence-XOR validation; and derives
`content_sha256` from the private canonical UTF-8 JSON payload. It has no package-root export, concrete
repository, SQLite, provider, parser, CLI, filesystem, clock, network, cache, or retry dependency.

Codex local verification with
`C:\Users\garim\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`:

```text
Dedicated: 13 passed, 3 subtests passed
Related: 41 passed, 332 subtests passed
  tests/test_simulation_models.py
  tests/test_persisted_simulation_race_inputs.py
  tests/test_race_entry_selection_resolver_contract.py
Full suite: 2387 passed, 2 skipped, 1317 subtests passed
```

The dedicated suite covers public surface and field contracts, frozen/slotted behavior, metadata identity
exclusions, strict validation, `passing_order=""`, provenance/InputAuditEntry compatibility, structural and
causal fail-closed boundaries, canonical ordering and digest sensitivity, public APIs, Protocol signatures,
and source/AST exclusions. `pytest` was installed into the approved bundled runtime because it was initially
absent; no repository dependency file was changed.

`git diff --check` succeeded. Production and tests outside the two new phase files are unchanged.
`database/keiba.db`, `logs/`, the original workspace, migrations, schema, repository implementations, and
package exports remain untouched. No stage, commit, or push was performed.

## Phase 4C-2d3b1i6b1 Test Coverage Correction

ChatGPT production review: `APPROVED`.

Review correction: dedicated test hardening only.

Production file modified during correction: `NO`.

The dedicated contract suite now directly verifies approved dataclass defaults; duplicate `entry_order` and
past-race identity rejection; both numbered-past versus `/none` audit XOR failures; complete nested payload
key orders; canonical payload-only ordering for past races and provenance; complete Source and Repository
Protocol hints plus structural ellipsis bodies; and the absence of all 13 API names from the package root.

`docs/CURRENT_PHASE.md` remains `READY_FOR_REVIEW`. No production behavior was changed.

## Phase 4C-2d3b1i6b1 Final Test-contract Correction

- HistoricalInputProvenance defaults explicitly verified.
- Past-race canonical ordering now verifies both `race_entry_id` and `past_race_index`.
- Production file unchanged.

Codex local verification after the final test-contract correction:

```text
Dedicated: 16 passed, 3 subtests passed
Related: 41 passed, 332 subtests passed
Full suite: 2390 passed, 2 skipped, 1317 subtests passed
```

Codex local verification with
`C:\Users\garim\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`:

```text
Dedicated: 16 passed, 3 subtests passed
Related: 41 passed, 332 subtests passed
Full suite: 2390 passed, 2 skipped, 1317 subtests passed
git diff --check: success
```

## Phase 4C-2d3b1i6b1 ChatGPT Final Review

Production review: `APPROVED`.

Test contract review: `APPROVED`.

Phase result: `APPROVED_FOR_COMMIT`.

Approved production SHA-256:
`E251E449E271944B609D1E81CE643BA51DCC37B94A89C061D26D548DAC2FADFE`

```text
Dedicated: 16 passed, 3 subtests passed
Related: 41 passed, 332 subtests passed
Full suite: 2390 passed, 2 skipped, 1317 subtests passed
```

## Phase 4C-2d3b1i6b2 Preparation

Status: `PHASE_4C_2D3B1I6B2_PREPARED`.

Formal base is `c031008c5ecc34dfb90b541a8c686b0868084709` on `feature/ver0.8-simulator`; the canonical
workspace is `C:\Users\garim\Desktop\KeibaAI-review-1i5b2b`. The original workspace remains unchanged.

Migration infrastructure inspection found `scripts/migrations/versions/` with v008 and v009, explicit
registration in `scripts/migrations/runner.py`, and the existing runner-owned `schema_migrations` flow.
The planned module is
`scripts/migrations/versions/v010_historical_input_snapshot_schema.py`; `runner.py` must explicitly import
and append it after v009. `versions/__init__.py` has no discovery role.

The runner enables and verifies foreign keys, rejects an active transaction, owns `BEGIN IMMEDIATE`, commit,
rollback, and migration-record insertion. v010 must use only `connection.execute()` over
`STATEMENTS + INDEXES + TRIGGERS`; it cannot own transaction SQL, commit, rollback, `executescript`, or a
connection lifecycle.

Read-only legacy-schema inspection found `races.id INTEGER PRIMARY KEY AUTOINCREMENT`,
`horses.id INTEGER PRIMARY KEY AUTOINCREMENT`, and `horses.race_id` as the parent linkage. The current
legacy index is only `idx_horses_race_id ON horses(race_id)`; no equivalent
`ux_horses_race_id_id` exists. The planned unique composite helper is valid because `horses.id` already
makes each `(race_id, id)` pair unique, and it makes the V3b composite parent FK executable.

The approved future migration scope is exactly eight tables:

- `historical_input_source_identities`
- `historical_input_external_races`
- `historical_input_external_entries`
- `historical_input_snapshots`
- `historical_input_snapshot_races`
- `historical_input_snapshot_entries`
- `historical_input_snapshot_past_races`
- `historical_input_snapshot_provenance`

It contains exactly four indexes — `ux_horses_race_id_id`, `idx_his_external_races_internal`,
`idx_his_external_entries_internal`, and `idx_his_snapshots_latest_eligible` — and exactly five linkage
triggers — `trg_his_snapshot_entry_mapping_insert`, `trg_his_snapshot_entry_mapping_update`,
`trg_his_snapshot_header_mapping_update`, `trg_his_external_entry_referenced_update`, and
`trg_his_external_entry_referenced_delete`.

The proposed dedicated test is `tests/test_historical_input_snapshot_migration.py`. Registration of v010
also requires minimal exact-version expectation updates in `tests/test_simulation_migrations.py`,
`tests/test_simulation_bet_plan_migration.py`, and
`tests/test_sqlite_persisted_simulation_application.py`; no production behavior outside registry inclusion
changes. Related verification will use those tests plus
`tests/test_sqlite_simulation_bet_plan_snapshot_repository.py` and
`tests/test_historical_input_snapshots.py`, then the full suite.

No contract conflict was identified. The approved V3b DDL is executable against a clean legacy parent
schema, preserves nullable `/none` provenance linkage, and leaves all historical tables empty after
migration. The preparation documents define the exact DDL/no-backfill/transaction boundaries and test
matrix; no production, test, migration, database, or log file was changed in this preparation activity.

`git diff --check`, `git diff --name-status`, and `git status --short` are recorded after the document
update. No stage, commit, or push is performed.

## Phase 4C-2d3b1i6b2 Preparation Approval

Status: `PHASE_4C_2D3B1I6B2_APPROVED_FOR_CODEX`.

ChatGPT preparation review: `APPROVED`.

Contract corrections: `NONE`.

Scope clarification: the exact existing migration tests
`tests/test_simulation_migrations.py`, `tests/test_simulation_bet_plan_migration.py`, and
`tests/test_sqlite_persisted_simulation_application.py` may change only for v010
registration/discovery expectations. Their unrelated migration behavior must not be refactored or broadened.

The approved future implementation remains restricted to the v010 module, its explicit runner registration,
one dedicated v010 migration test module, those three registration-expectation test updates, and the phase
documents. No production, test, or migration implementation has been changed during approval.

## Phase 4C-2d3b1i6b2 Execution Blocker

Status: `PHASE_4C_2D3B1I6B2_REVISION_REQUIRED`.

The dedicated v010 migration suite passed, as did the approved migration-related suite and the frozen
historical-input domain suite. The full suite exposed an out-of-scope runtime contract conflict:
`tests/test_cli_run_persisted_simulation.py` and
`tests/test_persisted_simulation_request_application.py` create a file-backed database without legacy
`races`/`horses` parent tables, then invoke the default migration runner. The approved v010 helper
`CREATE UNIQUE INDEX ux_horses_race_id_id ON horses(race_id, id)` correctly fails there with
`sqlite3.OperationalError: no such table: main.horses`.

V3b explicitly requires the legacy composite-parent helper index and describes v010 as executable against a
required legacy parent schema. The current phase allowlist forbids changing the request-application/CLI
bootstrap path and excludes both failing test modules. Skipping v010, conditionally suppressing the helper
index, creating legacy parent tables in v010, or changing migration-runner transaction/bootstrap behavior
would violate the approved V3b contract or phase scope.

Required design decision: define which existing application/bootstrap boundary owns provisioning the legacy
`races` and `horses` parent schema before the default runner applies v010, then explicitly authorize the
necessary production and test files in a revised phase contract. No out-of-scope file was changed.

Observed verification:

```text
Dedicated v010 migration: 5 passed
Migration-related: 52 passed, 78 subtests passed
Historical domain: 16 passed, 3 subtests passed
Full suite: 2 failed, 2393 passed, 2 skipped, 1317 subtests passed
```

The reported full-suite blocker was resolved by the approved test-fixture scope extension described below.

## Phase 4C-2d3b1i6b2 Blocker Resolution and Execution

Status: `PHASE_4C_2D3B1I6B2_READY_FOR_REVIEW`.

ChatGPT blocker disposition: `RESOLVED_BY_TEST_FIXTURE_SCOPE_EXTENSION`.

Design decision: the legacy `races`/`horses` schema is a prerequisite for v010; no production bootstrap
change is authorized. v010 remains an overlay migration over the existing KeibaOS legacy race/horse schema.
Before the default migration chain reaches v010, the target database must already contain `races` and
`horses`. v010 does not create, repair, or infer those parent tables. The migration runner, file-backed
persisted-simulation application, request application, and CLI do not own legacy-schema bootstrap.

Newly authorized test files:

- `tests/test_cli_run_persisted_simulation.py`
- `tests/test_persisted_simulation_request_application.py`

Only their blank file-backed real-chain success fixtures changed: each now creates, commits, and closes the
minimal real SQLite `races` and `horses` parent tables at the request-resolved database path before the
existing application chain applies its default migrations. Neither fixture calls `apply_migrations()`
manually, and their real request/CLI chain, output, migration, and persistence assertions remain intact.

The v010 migration path is
`scripts/migrations/versions/v010_historical_input_snapshot_schema.py`; it is registered once after v009 in
`scripts/migrations/runner.py`. The implementation creates the approved eight historical tables, four
indexes, and five linkage triggers.

Codex local verification:

```text
Dedicated v010 migration: 5 passed
Migration-related: 52 passed, 78 subtests passed
Higher-level request/CLI regression: 13 passed, 6 subtests passed
Historical domain: 16 passed, 3 subtests passed
Full suite: 2395 passed, 2 skipped, 1317 subtests passed
git diff --check: success
```

`docs/CURRENT_PHASE.md` is now `READY_FOR_REVIEW`. No production bootstrap change was made; the historical
domain module and suite are unchanged, and `scripts/database.py` is unchanged. `database/keiba.db`, `logs/`,
and the original workspace remain untouched. No stage, commit, or push was performed. Implementation
deviations: none.

## Phase 4C-2d3b1i6b2 ChatGPT DDL Review Correction

- exact `observed_at_utc` UTC suffix CHECK restored
- dedicated test locks all five UTC suffix clauses
- direct positive-range SQL coverage added
- dedicated runner idempotency coverage added
- stale natural-identity test wording corrected
- no runner/trigger/fixture/domain redesign

Codex local correction verification:

```text
Dedicated v010 migration: 6 passed
Migration-related: 53 passed, 78 subtests passed
Higher-level request/CLI regression: 13 passed, 6 subtests passed
Historical domain: 16 passed, 3 subtests passed
Full suite: 2396 passed, 2 skipped, 1317 subtests passed
git diff --check: success
```

## Phase 4C-2d3b1i6b2 ChatGPT Final Review

Result: `APPROVED_FOR_COMMIT`

V3b DDL: `APPROVED`

Tables: `8`

Indexes: `4`

Triggers: `5`

```text
Dedicated: 6 passed
Migration-related: 53 passed, 78 subtests passed
Higher-level: 13 passed, 6 subtests passed
Historical domain: 16 passed, 3 subtests passed
Full suite: 2396 passed, 2 skipped, 1317 subtests passed
git diff --check: PASS
```

## Phase 4C-2d3b1i6b3 Preparation

Status: `PHASE_4C_2D3B1I6B3_PREPARED`.

Formal base: `95d8c8e123828935c8283109fef80b86b8a3eb88` on `feature/ver0.8-simulator`; canonical workspace:
`C:\Users\garim\Desktop\KeibaAI-review-1i5b2b`. The original workspace remains unchanged.

Inspected existing repository boundaries:

- `scripts/simulation/repositories/sqlite_bet_plan_snapshot_repository.py`
- `scripts/simulation/repositories/sqlite.py`
- `scripts/simulation/repositories/sqlite_race_entry_source.py`
- `scripts/simulation/repositories/errors.py`
- `scripts/simulation/repositories/interfaces.py`
- `scripts/simulation/historical_input_snapshots.py`
- `scripts/migrations/versions/v010_historical_input_snapshot_schema.py`
- `scripts/migrations/runner.py`
- their SQLite repository, migration, and historical-domain test conventions.

`RepositoryValidationError`, `RepositoryConflictError`, and `RepositoryDataIntegrityError` are defined in
`scripts/simulation/repositories/errors.py`. Existing immutable SQLite repositories use a keyword-only,
connection-injected constructor, enable/verify foreign keys, reject active caller write transactions, own
`BEGIN IMMEDIATE` / commit / rollback for save, and reconstruct malformed stored rows fail-closed. Read-only
sources do not own a transaction. No package-root export is required by current conventions.

The proposed concrete module is
`scripts/simulation/repositories/sqlite_historical_input_snapshot_repository.py`, with dedicated test
`tests/test_sqlite_historical_input_snapshot_repository.py`. The proposed implementation set is those two
files plus the two phase documents; no migration, runner, schema, package registration, or V3c source file is
proposed.

Phase-size decision: split before implementation. Proposed b3a owns the atomic immutable save path across all
eight V3b tables; proposed b3b owns exact eligible latest selection, full V3a reconstruction, digest
verification, and malformed-latest fail-closed behavior. Combining both is not sufficiently small for one
reviewable phase.

The draft preserves V3d natural identity `(dataset_id, organization, source_system, external_race_id,
captured_at)`: same digest is a no-op, different digest is `RepositoryConflictError`, and content digest is
never a separate caller input. Proposed load selection has exact dataset/race/source/cutoff predicates and
`captured_at DESC` only, with no older/cross-source fallback on malformed latest data.

No production, test, migration, schema, database, or log file was modified in this preparation. `git diff
--check`, `git diff --name-status`, and `git status --short` were run after the documentation update. No
stage, commit, or push was performed.

## Phase 4C-2d3b1i6b3a Approval

Status: `PHASE_4C_2D3B1I6B3A_APPROVED_FOR_CODEX`.

ChatGPT preparation review: `APPROVED_WITH_SPLIT`.

The original b3 umbrella is split: b3a is the atomic save path now approved for implementation; b3b is the
eligible-latest load and full reconstruction phase, deferred and unimplemented. b3a has exactly four future
allowed files: the direct concrete repository module
`scripts/simulation/repositories/sqlite_historical_input_snapshot_repository.py`, its dedicated test
`tests/test_sqlite_historical_input_snapshot_repository.py`, and the two phase documents.

The approved save contract uses the existing connection-injected convention: keyword-only connection,
foreign-key enable/verification, active caller transaction rejection, repository-owned `BEGIN IMMEDIATE`,
commit on complete save, rollback on failure, reusable connection, and repository error classes from
`scripts/simulation/repositories/errors.py`.

Natural identity is exactly `(dataset_id, organization, source_system, external_race_id, captured_at_utc)`.
Same identity and digest is an idempotent no-op; same identity and different digest is unchanged
`RepositoryConflictError`. Content digest, cutoff, internal race ID, and source URL are not identity. b3b
load/reconstruction, eligible cutoff selection, stored digest verification, and malformed-latest handling
remain excluded.

## Phase 4C-2d3b1i6b3a Contract Correction and Reapproval

Status: `PHASE_4C_2D3B1I6B3A_APPROVED_FOR_CODEX`.

The mapping error classification is now explicit in `docs/CURRENT_PHASE.md`:

- source identity has no content-mismatch case; its exact key is reused;
- external-race forward mismatch is `RepositoryConflictError`;
- external-race reverse immutable mapping mismatch is `RepositoryConflictError`;
- external-entry forward mismatch is `RepositoryConflictError`;
- external-entry reverse immutable mapping mismatch is `RepositoryConflictError`;
- unrelated SQLite or stored-data integrity failures are `RepositoryDataIntegrityError`; and
- caller/boundary validation is `RepositoryValidationError`.

Production, tests, migration, and schema remain unimplemented or unchanged for this documentation-only
correction. Execution remains separately authorized after this reapproval.

## Phase 4C-2d3b1i6b3a Implementation

Status: `PHASE_4C_2D3B1I6B3A_READY_FOR_REVIEW`.

Implemented `SQLiteHistoricalInputSnapshotRepository` in
`scripts/simulation/repositories/sqlite_historical_input_snapshot_repository.py`. Its only public persistence
method is `save_snapshot(*, snapshot)`: it uses the injected connection, verifies foreign keys, owns
`BEGIN IMMEDIATE` / commit / rollback, and persists the complete V3a snapshot across all eight committed v010
tables in parent-first order. `load_latest_snapshot` remains unimplemented; b3b and V3c are unstarted.

Natural identity is `(dataset_id, organization, source_system, external_race_id, captured_at_utc)`. A same
digest is an idempotent no-op; a different digest under that identity is an unchanged
`RepositoryConflictError`. Source identity is reused. Explicit external-race and external-entry forward and
reverse mapping mismatches raise unchanged `RepositoryConflictError`; unrelated SQLite FK/CHECK/storage
failures raise `RepositoryDataIntegrityError`; invalid connection/snapshot or a caller-owned active
transaction raises `RepositoryValidationError`.

The dedicated real-`:memory:` SQLite tests cover all eight table row counts and exact header, race, entry,
past-race, and provenance fields; canonical six-microsecond UTC/date/fixed Decimal TEXT persistence; empty
`passing_order`; idempotency; mapping reuse/conflicts; and rollback/reusable-connection behavior. No package
root export was added. A real SQLite provenance-child trigger failure proves the rollback removes mappings,
header, and every child row. The migration runner, v010 schema, and frozen V3a domain were unchanged.

Verification (Codex local):

- Dedicated: `9 passed, 4 subtests passed`.
- Historical domain / v010 migration: `22 passed, 3 subtests passed`.
- Existing SQLite repository / migration regressions: `63 passed, 70 subtests passed`.
- Full suite: `2405 passed, 2 skipped, 1321 subtests passed`.

`database/keiba.db`, `logs/`, and the original workspace remain untouched. No stage, commit, or push was
performed.

## Phase 4C-2d3b1i6b3a ChatGPT Final Review

Result: `APPROVED_FOR_COMMIT`.

- Production review: APPROVED.
- Atomic save: APPROVED.
- Natural identity / idempotency: APPROVED.
- Mapping conflict classification: APPROVED.
- Transaction rollback: APPROVED.
- Canonical persistence: APPROVED.

Verification (Codex local):

- Dedicated: `9 passed, 4 subtests passed`.
- Historical domain / v010 migration: `22 passed, 3 subtests passed`.
- Existing SQLite repository / migration: `63 passed, 70 subtests passed`.
- Full suite: `2405 passed, 2 skipped, 1321 subtests passed`.

`load_latest_snapshot` is NOT IMPLEMENTED and deferred to b3b. b3b and V3c remain unimplemented.

## Phase 4C-2d3b1i6b3a Commit Verification Runtime Blocker

The isolated Windows TEMP venv now has Python 3.14.5, pytest 8.3.5, and verification-only `tzdata 2026.3`.
`ZoneInfo("Asia/Tokyo")` resolves successfully. The required existing SQLite repository / migration regression
set passed (`63 passed`); dedicated verification passed (`9 passed`); and historical domain / v010 migration
verification passed (`22 passed`). Requirements files were not changed.

The full suite then reported three pre-existing Python 3.14 runtime incompatibilities: tests that expect
`TypeError` for adding an attribute to frozen slotted dataclasses receive `dataclasses.FrozenInstanceError`
instead. The affected tests are in `test_persisted_settlement_contract.py`, `test_settlement_contract.py`, and
`test_simulation_bet_plan_identity.py`, outside b3a's allowed files. The full result is
`3 failed, 2404 passed`.

No stage, commit, or push was performed after this environment failure.

## Phase 4C-2d3b1i6b3a Python 3.14 Baseline Acceptance

ChatGPT final commit decision: `APPROVED_FOR_COMMIT`.

The Python 3.14.5 full-suite result is `3 failed, 2404 passed`. The only accepted environmental compatibility
failures are `PersistedRaceSettlementDataTests.test_uses_slots`, `RaceSettlementDataTests.test_uses_slots`,
and `SimulationBetPlanIdentityTest.test_uses_slots_and_rejects_new_attributes`. Each is the pre-existing
expectation of `TypeError` versus Python 3.14 `FrozenInstanceError` for unknown attribute assignment on a
frozen slotted dataclass. Those tests and their production dataclasses are outside b3a and were not modified.

The b3a results remain: dedicated `9 passed`; historical domain / v010 migration `22 passed`; and existing
SQLite repository / migration `63 passed`. Verification used a Windows isolated TEMP venv with Python 3.14.5,
pytest 8.3.5, and verification-only tzdata 2026.3. `requirements.txt` and `requirements-dev.txt` remain
unchanged.

## Phase 4C-2d3b1i6b3a1 Preparation

Status: `DRAFT_FOR_REVIEW`.

Formal base is `12ff00b45e2e4a8bc5761f3210fd45685a2a3dbb` on
`feature/ver0.8-simulator`. The canonical workspace is
`C:\Users\garim\Desktop\KeibaAI-review-1i5b2b`; the original workspace remains unchanged.

The completed b3a save repository remains unchanged. Its dedicated verification passed (`9 passed`), as did
historical domain/v010 migration (`22 passed, 3 subtests passed`) and existing SQLite repository/migration
regressions (`63 passed, 70 subtests passed`). Under a Windows Python 3.14.5 TEMP venv with pytest 8.3.5 and
manually installed verification-only `tzdata 2026.3`, the full suite reported `3 failed, 2404 passed`.

Preparation found two independent compatibility causes:

- `requirements.txt` declares only Beautiful Soup and requests, while `requirements-dev.txt` declares only
  pytest. A fresh Windows development/test venv cannot resolve `ZoneInfo("Asia/Tokyo")` without manual IANA
  time-zone data. The observed `ZoneInfo` import is test-only; no production module imports `ZoneInfo`.
- Three slots tests expect `TypeError` from unknown-attribute assignment. Python 3.14.5 raises
  `FrozenInstanceError` for the same rejected operation. This does not change the frozen/slotted/no-arbitrary-
  attribute contract, and the existing declared-field frozen tests still require `FrozenInstanceError`.

The recommended future dependency is the exact Windows-only PEP 508 development marker
`tzdata==2026.3; sys_platform == "win32"` in `requirements-dev.txt`. Exact pins are the existing requirements
convention; Windows-only dev scope is sufficient and avoids an unsupported production dependency expansion.

The recommended future test-only correction adds direct no-`__dict__` assertions to the persisted and regular
settlement slots tests, then accepts `(TypeError, FrozenInstanceError)` for unknown attributes. The identity
test already asserts no `__dict__`; it needs only the accepted-exception tuple. No dataclass or other
production change is proposed.

GitHub Actions currently tests only Ubuntu Python 3.12; README documents Python 3.12 or later. This phase
does not expand CI, README, production requirements, b3a, historical snapshot domain, v010, migration runner,
or b3b. The proposed future allowed files are `requirements-dev.txt`, the three named contract test modules,
and the two phase documents.

Future acceptance requires a fresh outside-repository Windows Python 3.14.5 venv installed solely from both
requirements files, successful `ZoneInfo("Asia/Tokyo")`, the three corrected contracts, b3a dedicated,
historical domain/migration, existing SQLite repository/migration regressions, and a zero-failure full suite.

No production, test, requirements, migration, schema, database, or log file was changed in this preparation.
Phase 4C-2d3b1i6b3b remains deferred and unimplemented. No stage, commit, or push was performed.

## Phase 4C-2d3b1i6b3a1 Approval

Status: `PHASE_4C_2D3B1I6B3A1_APPROVED_FOR_CODEX`.

ChatGPT design review approved Phase 4C-2d3b1i6b3a1 for Codex implementation at formal base
`12ff00b45e2e4a8bc5761f3210fd45685a2a3dbb` on `feature/ver0.8-simulator`.

The approved declarative development/test dependency is exactly:

```text
tzdata==2026.3; sys_platform == "win32"
```

It is not a production dependency and must not be unconditional. The approved portable Python 3.14 test rule is
`(TypeError, FrozenInstanceError)` only for unknown/new attributes on the three frozen slotted dataclasses. The
two settlement tests must explicitly prove no `__dict__`; the identity test already does so. Declared-field
mutation assertions remain `FrozenInstanceError` assertions.

The exact future allowed files are:

- `requirements-dev.txt`
- `tests/test_persisted_settlement_contract.py`
- `tests/test_settlement_contract.py`
- `tests/test_simulation_bet_plan_identity.py`
- `docs/CURRENT_PHASE.md`
- `docs/LATEST_CODEX_REPORT.md`

No production change is required or authorized. Future verification must use a fresh outside-repository Windows
Python 3.14.5 TEMP venv, install only both repository requirements files, resolve `ZoneInfo("Asia/Tokyo")`,
report pytest `8.3.5` and tzdata `2026.3`, and finish the complete required regression matrix with zero failures.
No Python 3.14 baseline exception is pre-approved after this phase. Phase 4C-2d3b1i6b3b remains deferred.

No production, test, requirements, database, or log file was changed for approval. No stage, commit, or push was
performed.

## Phase 4C-2d3b1i6b3a1 Execution

Status: `PHASE_4C_2D3B1I6B3A1_READY_FOR_REVIEW`.

The Windows-only development/test marker
`tzdata==2026.3; sys_platform == "win32"` was added to `requirements-dev.txt`; the existing
`pytest==8.3.5` pin is unchanged. No production requirement was added.

The only test changes are the three approved unknown-attribute portability assertions:

- `PersistedRaceSettlementDataTests.test_uses_slots` now explicitly asserts no `__dict__` and accepts
  `(TypeError, FrozenInstanceError)` for the rejected new attribute.
- `RaceSettlementDataTests.test_uses_slots` has the same structural and portable-exception assertions.
- `SimulationBetPlanIdentityTest.test_uses_slots_and_rejects_new_attributes` retained its existing no-
  `__dict__` assertion and accepts the same exception tuple.

Declared-field frozen tests remain unchanged and still require `FrozenInstanceError`. No production file,
dataclass implementation, migration, schema, database, or log file changed.

Fresh verification used this newly created outside-repository TEMP venv:

```text
C:\Users\garim\AppData\Local\Temp\keibaos-verify-1i6b3a1-767d4bfb71874ea88a1d55e75e671e91
```

It used Python `3.14.5`, installed only `-r requirements.txt -r requirements-dev.txt`, and reported pytest
`8.3.5`, tzdata `2026.3`, and `ZoneInfo("Asia/Tokyo")` as `Asia/Tokyo`. No separate tzdata install occurred.

Codex local verification:

```text
Targeted compatibility: 96 passed
b3a dedicated: 9 passed
Historical snapshot / v010 migration: 22 passed
Existing SQLite repository / migration: 63 passed
Full suite: 2407 passed
git diff --check: success
```

Phase 4C-2d3b1i6b3b remains deferred and unimplemented. No stage, commit, or push was performed.

## Phase 4C-2d3b1i6b3a1 Commit Approval

ChatGPT final review result: `APPROVED_FOR_COMMIT`. The approved six-file change preserves production behavior,
the existing pytest pin, and the completed Windows Python 3.14.5 verification results: pytest `8.3.5`, tzdata
`2026.3`, `ZoneInfo("Asia/Tokyo")` success, targeted compatibility `96 passed`, b3a `9 passed`, historical
snapshot/v010 `22 passed`, existing SQLite repository/migration `63 passed`, and full suite `2407 passed`.

## Phase 4C-2d3b1i6b3a1 Review Metadata Correction

ChatGPT approved the implementation, the three test changes, and the Windows-only requirements change. The
documentation review required only state wording cleanup: the phase is implemented and remains
`READY_FOR_REVIEW` awaiting ChatGPT commit review. No dependency, test, or production file changed during this
correction.

## Phase 4C-2d3b1i6b3b Preparation

Status: `PHASE_4C_2D3B1I6B3B_PREPARED`.

Formal base is `6c844e943b408074e6269858887846ff31233661` on `feature/ver0.8-simulator`. The committed b3a
repository already saves a complete V3a `HistoricalInputSnapshot`; b3b is limited to its eligible-latest load
and reconstruction method. V3c remains deferred.

The prepared API is `load_latest_snapshot(*, dataset_id, race_id, information_cutoff, source_identity)` with
return type `HistoricalInputSnapshot | None`. Caller invalidity is `RepositoryValidationError`; selected stored
data, joins, parsers, constructor failures, and digest mismatch are `RepositoryDataIntegrityError`.

Selection is exact by dataset ID, internal race ID, organization, source system, and external race ID, with both
`captured_at_utc <= requested_cutoff` and `information_cutoff_utc <= requested_cutoff`, then only
`ORDER BY captured_at_utc DESC`. The v010 natural identity makes an equal-captured-at tie impossible. No
eligible result returns `None`; a malformed selected latest result never falls back to an older snapshot.

The draft requires exact canonical UTC microsecond `+00:00` text, canonical dates, canonical finite Decimal
TEXT with no float conversion, exact SQLite value types, NFC text, and final V3a constructor validation. It
reconstructs every V3a child in entry-order, race-entry/past-index, and audit-key order, verifies the exact
external-race and external-entry mappings needed to bind the selected snapshot, then verifies the recomputed
canonical digest against `content_sha256`.

Load is read-only: it allows an active caller transaction and never begins, commits, rolls back, applies a
migration, opens a connection, or repairs data. The b3a save path is frozen.

The proposed future scope is exactly the repository module, its existing dedicated test module, and the two
phase documents. Dedicated coverage will include API, eligibility/no-fallback, full reconstruction, canonical
stored parsing, mapping/cardinality corruption, digest mismatch, caller validation, read-only transaction
behavior, and save regression. Regression uses the current Windows Python 3.14.5 / pytest 8.3.5 / tzdata 2026.3
baseline and targets zero full-suite failures.

No production, test, migration, schema, database, or log file was modified in preparation. No stage, commit,
or push was performed.

## Phase 4C-2d3b1i6b3b Approval

Status: `PHASE_4C_2D3B1I6B3B_APPROVED_FOR_CODEX`.

ChatGPT approved the b3b eligible-latest load and reconstruction contract. The critical frozen clarification is
that the latest eligible header is selected from `historical_input_snapshots` alone before any child or mapping
query. Missing/corrupt children or mappings therefore fail the selected latest snapshot with
`RepositoryDataIntegrityError`; they cannot suppress it in SQL or expose an older eligible snapshot.

The contract retains both eligibility predicates, exactly `ORDER BY captured_at_utc DESC`, no secondary key,
strict canonical datetime/date/Decimal/text parsing, exact mapping reconstruction, V3a constructor and digest
verification, and read-only transaction ownership. The approved active-transaction tests prove that both a
successful load and a data-integrity failure leave caller uncommitted work neither committed nor rolled back.

The exact future scope remains the existing concrete repository module, its dedicated test module, and the two
phase documents. No migration, schema, production module outside that repository, or additional test file is
authorized. V3c remains deferred and unimplemented. No stage, commit, or push was performed.

## Phase 4C-2d3b1i6b3b Implementation

Status: `PHASE_4C_2D3B1I6B3B_READY_FOR_REVIEW`.

Implemented the exact keyword-only `SQLiteHistoricalInputSnapshotRepository.load_latest_snapshot()` read API.
It validates exact caller dataset/race/cutoff/source inputs as `RepositoryValidationError`, selects one binding
latest header from `historical_input_snapshots` only, and applies both eligibility predicates with the sole
ordering `captured_at_utc DESC`. It returns `None` only when no eligible header exists; it never joins children
or mappings for selection and never falls back after selecting a header.

The selected header and every child value are reconstructed through strict stored UTC datetime, ISO date,
finite canonical Decimal, exact integer, NFC text, nullable-field, external-race mapping, and external-entry
mapping checks. The resulting V3a object graph is constructed in deterministic entry, past-race, and provenance
order. Its recomputed canonical digest must equal stored `content_sha256`; malformed data, mapping failures,
domain constructor failures, and digest mismatch fail closed as `RepositoryDataIntegrityError` without retry or
older-snapshot fallback.

Load is read-only: it neither begins, commits, nor rolls back transactions; it does not mutate PRAGMAs, apply
migrations, write data, alter mappings, or open another connection. Dedicated coverage proves successful and
integrity-failure loads preserve active caller transactions and uncommitted caller work. The frozen b3a save
path remains green.

Fresh outside-repository Windows TEMP verification used
`C:\Users\garim\AppData\Local\Temp\keibaos-verify-1i6b3b-70dc2c943d6441e0875c209b29da5d34` with Python
`3.14.5`, pytest `8.3.5`, and tzdata `2026.3`; `ZoneInfo("Asia/Tokyo")` succeeded.

Codex local verification:

```text
Dedicated repository: 17 passed
Historical domain / v010 migration: 22 passed
Existing SQLite repository / migration regressions: 63 passed
Full suite: 2415 passed
git diff --check: success
```

Only the approved repository module, dedicated test module, and phase documents changed. Migration, runner,
historical domain, database, logs, and the original workspace remain untouched. V3c remains deferred and
unimplemented. No stage, commit, or push was performed.

## Phase 4C-2d3b1i6b3b Review Correction

The datetime caller-validation boundary now catches `ValueError`, `TypeError`, and `OverflowError` raised while
evaluating an exact `datetime` timezone offset or converting it to UTC, translating them to
`RepositoryValidationError`. Naive values remain invalid, valid non-UTC aware values remain accepted and are
normalized to UTC, and stored-data parser classification remains unchanged.

Dedicated coverage adds a custom `tzinfo` whose `utcoffset()` raises. The load call raises
`RepositoryValidationError` before issuing a database query; the same test proves a valid Asia/Tokyo-offset
cutoff representing the requested instant loads normally. The phase remains `READY_FOR_REVIEW`; scope, save
behavior, and all non-approved files remain unchanged.

## Phase 4C-2d3b1i6c1 Preparation

Status: `PHASE_4C_2D3B1I6C1_PREPARED`.

The preparation used formal base `038130c9d84a082107e351e545c167a9019e7b3a` on
`feature/ver0.8-simulator`. V3a domain, v010 schema, and V3d SQLite save/load are complete and frozen. The
existing providers, parsers, fetchers, legacy database boundary, migrations, tests, and simulator design were
inspected without changing them.

The resulting policy is fail closed. Legacy race/horse IDs and horse number are linkage-only; legacy descriptive
fields/URLs are not provenance; `horses.odds` is forbidden; legacy past races, v008 odds, and result/settlement
data are untrusted or forbidden. NAR live parsing is only partial because it does not retain immutable raw
official records, complete official identities, or causal timestamps. The JRA fetcher is a static placeholder;
all JRA record kinds are unsupported/deferred.

Future NAR raw records use only official keys:
`nar:{YYYYMMDD}:{k_babaCode}:{k_raceNo}` and
`nar:{YYYYMMDD}:{k_babaCode}:{k_raceNo}:entry:{horseNum}`. Date is canonically validated; official key spelling is
preserved without place-name inference or synthetic zero-padding. Existing legacy rows alone cannot supply them.

The proposed frozen source-record domain permits exactly `track`, `entry`, `jockey`, `odds_win`, `past_race`, and
`past_race_absence`. Its source-ID envelope is `his-v1:{record_kind}:{sha256}` over canonical NFC UTF-8 JSON
with sorted keys, finite Decimal text, the canonical official URL, and explicit nulls; capture timestamps are
source evidence and are not source-ID members. The V2 refinement below freezes each exact payload key.
`odds_win` maps to provenance `odds`; `past_race_absence` maps to `past_race` with the `/none` audit key; neither
is a new provenance input type.

Past races sort `race_date DESC, source_id ASC`, then receive contiguous indexes. Missing/same-day/future dates,
duplicate source IDs, duplicate official identities, and malformed records fail closed. A no-history entry needs
one auditable zero-result absence search record whose exact `query_scope` is external entry ID, target race date,
and `strictly_before_target_race=True`, with exact zero count, canonical official URL, and time evidence; an empty
parser output is not proof.

`available_at` is optional and accepts only official publication time; `observed_at` is required and accepts only
an immutable capture-boundary response observation. Each must satisfy the later causal order. Current stored data
has neither trusted identity nor required observation evidence, so retrospective construction is intentionally
unavailable. This is an explicit gap, not a fallback opportunity.

The recommended sequence is (1) source-record domain/digest, (2) NAR supplied-raw normalization, (3) pure V3a
snapshot builder, and later (4) JRA normalization after a real official adapter exists. Candidate new files are
`historical_input_source_records.py`, `nar_historical_input_source.py`, and
`historical_input_snapshot_builder.py`, each with a dedicated deterministic test. Existing provider/parser changes
are not pre-authorized. The pure builder must not fetch, mutate/read a database, inspect settlement, infer
provenance, repair input, or invoke the repository.

Future tests require deterministic fixtures: canonical source digests, record-kind/mapping rules, NAR key
validation, duplicate conflicts, ordering, absence proof, future-leakage rejection, V3a builder digest stability,
no legacy fallback/result leakage, JRA unsupported behavior, and a focused repository round trip. No live network
calls are permitted.

Only `docs/CURRENT_PHASE.md` and this report changed. Production, tests, migrations, schema, database, logs, and
the original workspace remain untouched. No stage, commit, or push was performed.

## Phase 4C-2d3b1i6c1 Preparation Contract Refinement V2

Status remains `PHASE_4C_2D3B1I6C1_PREPARED`; this is a PREPARE-only contract refinement, not source-domain,
normalizer, builder, or repository implementation. The authoritative V3c envelope is now explicit: every c1a
source record has `schema_version`, `record_kind`, `organization`, `source_system`, `external_race_id`,
`external_entry_id`, `canonical_source_url`, `provider_record_id`, `record_values`, `available_at`, and
`observed_at`. The source-ID digest includes exactly the V3c nine-member JSON envelope through `record_values`;
it deliberately excludes `available_at` and `observed_at`, which remain immutable causal evidence rather than
logical-record identity.

The six exact per-kind payloads are frozen: complete track metadata; official entry identity, optional horse
identity, and horse number; entry-scoped jockey; entry-scoped positive Decimal win odds; every V3a past-race
scalar; and the three-key, zero-result past-race absence proof. Nullable values remain explicit JSON `null`.
`passing_order` is NFC-normalized and may be the empty string. A past race must carry a non-null opaque official
`provider_record_id`; the tuple `(source_system, external_race_id, external_entry_id, provider_record_id)` is
the future official-past-race conflict primitive. Same-source duplication is exact `source_id` equality.

Local `race_id` and `race_entry_id` are not c1a fields and never participate in a source ID. Future V3a assembly
uses a separate official-entry-to-local-entry mapping, while `entry_order` and `past_race_index` remain derived
only after complete trusted source validation. IDs use SHA-256 over canonical NFC UTF-8 JSON bytes with
`ensure_ascii=False`, `sort_keys=True`, compact separators, and `allow_nan=False`; the lowercase hexadecimal
digest is then placed in `his-v1:{record_kind}:{sha256}`.

Timestamp semantics were reconciled without changing V3a/V3c: `available_at` is optional and only an official
provider publication instant; `observed_at` is required and only the immutable response-receipt boundary prior to
parsing. A record lacking provider `available_at` is usable only when its valid immutable `observed_at` satisfies
the downstream causal order. Existing NAR rows lack that evidence, so NAR remains partial. JRA remains
unsupported/deferred. Legacy linkage-only data, `horses.odds`, legacy past races, results, and settlement remain
untrusted or forbidden.

The proposed exact c1a surface is the frozen/slotted `HistoricalInputSourceRecord`, `SourceRecordKind`, three
minimal source exceptions (`HistoricalInputSourceError`, `HistoricalInputSourceValidationError`, and
`HistoricalInputSourceConflictError`), canonical payload/ID functions, and one record-set conflict validator.
Its future allowed files are exactly `scripts/simulation/historical_input_source_records.py`,
`tests/test_historical_input_source_records.py`, and the two phase documents. The expanded deterministic test
matrix covers the exact field API, all payload schemas, nulls, canonical scalars, digest behavior, no local-ID
dependence, conflict primitives, strict absence proof, temporal validation, and no DB/network/filesystem or
package-root work.

Production, tests, migrations, schema, database, logs, and the original workspace remain unchanged. No stage,
commit, or push was performed.

## Phase 4C-2d3b1i6c1 Preparation URL Contract Refinement V3

ChatGPT accepted the V2 source-record/domain design except that a generic `url-v1` normalization algorithm had
not been formally frozen. V3 removes that implication. URL canonicalization belongs exclusively to c1b/c1d
source-family normalizers; they provide an already-canonical `canonical_source_url`. c1a only validates its
already-canonical representation and includes that exact supplied string byte-for-byte in the existing digest.

For a non-null URL, c1a requires exact `str`, non-empty NFC text without leading/trailing whitespace, an absolute
`https` URL with a non-empty host, no credentials, no fragment, and no control character. It rejects invalid text
instead of normalizing it. It does not alter query ordering/content, ports, percent encoding, trailing slash,
`www`, path/query case, relative URLs, or tracking parameters. Canonical host spelling is therefore upstream
normalizer responsibility.

The per-kind policy is explicit: `track`, `entry`, `jockey`, `odds_win`, and `past_race` URL evidence are
optional; `past_race` still requires a non-null independent `provider_record_id`. `past_race_absence` requires a
non-null canonical successful-search response URL and does not require a provider record ID. URL and provider
record ID are independent and c1a must not synthesize either from the other.

The c1a future matrix now covers invalid URL types and syntax, NFC/whitespace, exact valid HTTPS retention without
transformation, per-kind required/optional policy, and rejection of missing absence-proof URL. The exact six
record kinds, payload schemas, timestamps, conflict rules, JSON/ID algorithm, exception API, c1a file scope,
JRA-deferred state, and NAR-partial state remain unchanged. This remains documentation preparation only.

Production, tests, migrations, schema, database, logs, and the original workspace remain unchanged. No stage,
commit, or push has occurred for this V3 refinement.

## Phase 4C-2d3b1i6c1a Design Approval

ChatGPT approved review head `9f2afe592930ff37220c3537822e66333ddf804d` for implementation from formal
base `038130c9d84a082107e351e545c167a9019e7b3a` on `feature/ver0.8-simulator`. This approval synchronizes only
the approved V3 source-record contract into the formal working tree; the review branch remains an immutable
artifact and is neither merged nor cherry-picked.

The exact future scope is four files only:
`scripts/simulation/historical_input_source_records.py`,
`tests/test_historical_input_source_records.py`, `docs/CURRENT_PHASE.md`, and
`docs/LATEST_CODEX_REPORT.md`. The public module is limited to `SourceRecordKind`,
`HistoricalInputSourceError`, `HistoricalInputSourceValidationError`, `HistoricalInputSourceConflictError`,
`HistoricalInputSourceRecord`, `canonical_historical_input_source_payload`,
`build_historical_input_source_id`, and `validate_historical_input_source_record_set`; there is no package-root
export.

The frozen source-ID contract remains `his-v1:{record_kind}:{lowercase_sha256_hex}` over the exact nine-key
canonical JSON envelope. It excludes internal/local IDs and timestamps. c1a validates but never canonicalizes
URLs; c1b/c1d own source-family URL canonicalization. `past_race_absence` requires its official successful-search
URL, while the other five kinds permit null URL under their exact policy. `past_race` requires its independent
official `provider_record_id`; the exact past-race conflict primitive and strict absence query scope remain
unchanged. `available_at` is optional official availability evidence and `observed_at` is required immutable
capture-boundary evidence.

NAR remains PARTIAL. JRA remains UNSUPPORTED / DEFERRED. c1b NAR normalization, c1c pure snapshot builder, and
c1d JRA normalization remain deferred. The lack of a persisted historical official raw/capture corpus does not
block the c1a supplied-record-domain implementation.

No production or test implementation has started. No stage, commit, or push was performed for this approval
synchronization.

## Phase 4C-2d3b1i6c1a Implementation

Status: `PHASE_4C_2D3B1I6C1A_READY_FOR_REVIEW`.

Implemented `scripts/simulation/historical_input_source_records.py` and its dedicated contract suite. The module
exports only the approved source-record kind alias, three minimal source errors, frozen/slotted
`HistoricalInputSourceRecord`, canonical payload/ID functions, and the ordered set validator; it has no
package-root export and performs no database, network, filesystem, provider/parser, migration, or repository work.

The record domain enforces the six exact `record_kind` schemas, defensive `MappingProxyType` freezing including
the nested absence query scope, exact scalar types, NFC text, canonical finite Decimal values, canonical UTC
datetimes, causal `available_at <= observed_at`, and the approved URL validation without URL transformation.
The nine-key UTF-8 JSON digest envelope excludes timestamps and all local IDs. Source IDs are deterministic
`his-v1:{record_kind}:{lowercase_sha256_hex}` values. Set validation preserves caller ordering, rejects duplicate
source IDs, and classifies same-official-past-race/different-content as
`HistoricalInputSourceConflictError` using the approved four-field primitive.

Fresh outside-repository TEMP verification used Python `3.14.5`, pytest `8.3.5`, and tzdata `2026.3` at
`C:\Users\garim\AppData\Local\Temp\keibaos-1i6c1a-81a6145f8aa1489ba365c93551d41192`.

Codex local verification:

```text
Dedicated source-record suite: 8 passed
Historical input snapshots: 16 passed
SQLite historical input snapshot repository: 18 passed
Historical input snapshot migration: 6 passed
Existing SQLite / migration regression: 63 passed
Full suite: 2424 passed
```

No production/test file outside this phase's two new files changed. NAR remains PARTIAL, JRA remains
UNSUPPORTED / DEFERRED, and c1b/c1c/c1d remain unimplemented. No stage, commit, or push was performed.

## Phase 4C-2d3b1i6c1a Implementation Approval

ChatGPT implementation review: `APPROVED`.

Approved review commit: `79133f59ab0334b16b05c9611c44ea74b047798b`.

Commit-state status: `PHASE_4C_2D3B1I6C1A_APPROVED_FOR_COMMIT`.

Approved verification retained:

```text
Python: 3.14.5
pytest: 8.3.5
tzdata: 2026.3
Dedicated source-record suite: 8 passed
Historical input snapshots: 16 passed
SQLite historical input snapshot repository: 18 passed
Historical input snapshot migration: 6 passed
Existing SQLite / migration regression: 63 passed
Full suite: 2424 passed, 0 failed
```

Production and test content are retained unchanged from the approved review commit. c1b is not started;
NAR remains PARTIAL and JRA remains UNSUPPORTED / DEFERRED.

## Phase 4C-2d3b1i6c1b Preparation

Status: `PHASE_4C_2D3B1I6C1B_DRAFT_FOR_REVIEW`.

Preparation used formal base `96e70d17f66f85689f568c7603977afdb508e31b` on
`feature/ver0.8-simulator`. The committed c1a source-record domain is frozen. c1b is proposed as the smallest
supplied-raw NAR-only normalizer: it receives one already successful official response and returns only validated
`HistoricalInputSourceRecord` values. It owns neither HTTP, raw persistence, a database, legacy parsing, snapshot
assembly, migration, repository behavior, nor JRA.

The tracked NAR `horse_page.html` fixture supplies the concrete initial evidence. It declares UTF-8 and shows
`https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/DebaTable` with exactly `k_raceDate`, `k_babaCode`, and
`k_raceNo`. Its race header/data area and `horseNum`, `jockeyName`, and `odds_weight` markup can provide a complete
track/entry/jockey/win-odds tuple. Existing `NARProvider` and legacy parsers are not reused: they fetch live data,
guess decoding, log responses, discard official keys/timestamps, and use float/zero fallback behavior.

The proposed frozen input is a slotted/frozen `NarSuppliedOfficialResponse(response_url, response_body: bytes,
charset: Literal["utf-8"], observed_at)`. Bytes plus an exact UTF-8 declaration preserve deterministic decoding;
the supplied response receipt instant is the only `observed_at`. No provider publication instant is evidenced, so
all c1b records have `available_at=None`. No local path, file mtime, database time, response-time guess, or parser
runtime can become source evidence.

The only initially supported official page is `DebaTable` on HTTPS `www.keiba.go.jp`, exact-case path
`/KeibaWeb/TodayRaceInfo/DebaTable`, no credentials/fragment/trailing slash, and exactly one of each required
query key. It canonicalizes the output query as `k_babaCode`, `k_raceDate`, `k_raceNo`, preserving validated
canonical decimal tokens and encoding date slashes as `%2F`. Unknown/duplicate keys, ambiguous percent encoding,
noncanonical date/decimal text, and URL/content race mismatch fail closed.

Support is `SUPPORTED` for `track`, `entry`, `jockey`, and `odds_win`; it is `UNSUPPORTED` for `past_race` and
`past_race_absence`. The existing past links cannot prove the complete c1a payload or a stable official
`provider_record_id`, and no complete successful scoped zero-result official search is available. Neither an
official past-race URL nor empty parser output may be substituted for those requirements.

NAR external identities remain exact:

```text
nar:{YYYYMMDD}:{k_babaCode}:{k_raceNo}
{external_race_id}:entry:{horseNum}
```

The normalizer derives no local identity. `horseNum` is direct official positive decimal content; duplicate or
conflicting values fail closed. The horse-detail href is not a stable provider horse identity, so
`external_horse_id=None`. Text cleanup is explicit NFC plus collapsed HTML whitespace; Decimal odds are parsed from
one positive official decimal span without float conversion. Unavailable, cancelled, zero, or non-numeric odds are
not silently omitted.

The proposed public module is `scripts/simulation/nar_historical_input_source.py`, exporting only the supplied
response dataclass, a minimal NAR source-error hierarchy, and
`normalize_nar_historical_input_source_records(*, response) -> tuple[HistoricalInputSourceRecord, ...]`.
Its output is one `track`, then per horse number ascending `entry`, `jockey`, and `odds_win`; it must pass the c1a
record-set validator. The candidate future scope is that one new module, one new dedicated test file, and the two
phase documents. Existing providers/parsers, migration/schema, repositories, package root, CLI, README, database,
and logs remain forbidden.

Required future tests are deterministic supplied UTF-8 HTML fixtures only: public API, input immutability, URL
policy, page dispatch, external IDs, selectors, Japanese whitespace, Decimal odds, observed/available timestamps,
canonical output ordering/IDs, c1a integration, and all missing/ambiguous/cancellation/unsupported/legacy-access
fail-closed boundaries. No live HTTP, raw persistence, or snapshot builder test is authorized.

NAR remains PARTIAL; JRA remains UNSUPPORTED / DEFERRED. c1c snapshot construction is unstarted. No production,
test, migration, database, or log file was modified in this preparation; no test was run because this is
documentation-only investigation.

## Phase 4C-2d3b1i6c1b Preparation Review Revision

GitHub design review of `419c85e83e47cb22be8f16fd7a0f18ed97993d4c` returned `REVISION_REQUIRED` for two
DebaTable source-semantic issues only. The supplied-bytes contract, strict UTF-8, response-receipt `observed_at`,
`available_at=None`, DebaTable-only support, URL/identity rules, Decimal odds, no legacy fallback, and unsupported
past-race/absence policy remain unchanged.

First, `section.raceTitle p.subTitle` is promotional display text in the tracked official fixture and is not a
race-class source. The initial normalizer now sets `track.record_values["race_class"]` to exact `None`; it must not
derive a class from subtitle, race name, data-area leftovers, legacy values, or place/race-number information.

Second, the semantic racecourse comes from exactly one active course node selected by
`article.raceCard .chartNavi.trackNameNavi a.cNaviBtn.courseBtn.active`. Its ordinary NFC/whitespace-normalized
text becomes `place`. The target h4 place segment remains an independent check only: c1b removes Unicode layout
whitespace from that segment alone and requires equality with the active course text. A missing, duplicate, empty,
or mismatching source fails closed. No global whitespace-compaction rule or NFKC normalization was introduced.

Future fixtures must prove promotional-subtitle exclusion, `race_class is None`, Japanese h4 layout spacing with an
active-course semantic value, active/h4 place conflict, and missing/duplicate active-course selector failures.
This remains a documentation-only PREPARE revision; production, tests, migrations, database, logs, package exports,
and the original workspace are unchanged.

## Phase 4C-2d3b1i6c1b Design Approval

ChatGPT approved the corrected PREPARE design at review commit
`3e2d373aa73fb5a1e9d9212968ca7ef325d52034` for implementation from formal base
`96e70d17f66f85689f568c7603977afdb508e31b`.

The active phase status is `APPROVED_FOR_CODEX`. The approved implementation scope remains exactly the new NAR
normalizer, its dedicated test module, and these two phase documents. The review branch is an immutable design
artifact and is not merged or otherwise modified.

blocker: no persisted supplied NAR raw/capture corpus exists; c1b is limited to caller-supplied DebaTable responses
and cannot create past-race or past-race-absence records.

## Phase 4C-2d3b1i6c1b Implementation

The supplied-response NAR normalizer is complete and `READY_FOR_REVIEW` from formal base
`96e70d17f66f85689f568c7603977afdb508e31b`.

Implemented public API:

```text
NarSuppliedOfficialResponse
NarHistoricalInputSourceError
NarHistoricalInputSourceValidationError
NarHistoricalInputSourceUnsupportedError
normalize_nar_historical_input_source_records(*, response)
```

`NarSuppliedOfficialResponse` is frozen and slotted, accepts only exact UTF-8 bytes plus an aware supplied
observation timestamp, and the normalizer never performs HTTP, filesystem, database, current-time, or legacy
provider/parser work. It canonicalizes the exact DebaTable URL and constructs c1a records through
`HistoricalInputSourceRecord`, followed by the committed c1a record-set validator.

Support matrix:

```text
track: SUPPORTED
entry: SUPPORTED
jockey: SUPPORTED
odds_win: SUPPORTED
past_race: UNSUPPORTED
past_race_absence: UNSUPPORTED
```

The deterministic output is one track record, then `entry`, `jockey`, and `odds_win` records for each direct
official horse number in ascending numeric order. It stores no horse-detail identity, treats promotional subtitle
content as non-schema content, fixes `race_class` to `None`, receives `observed_at` from the supplied response,
and uses `available_at=None`.

Codex local verification with Python 3.14.5 / pytest 8.3.5:

```text
Dedicated c1b: 8 passed
c1a source records: 8 passed
Historical snapshot / SQLite / migration related: 62 passed
Full suite: 2432 passed
Forbidden dependency source/AST check: included in dedicated suite
git diff --check: success
```

Changed files are limited to the new normalizer, its new dedicated test module, and the two phase documents. No
existing provider, parser, test, migration, schema, repository, database file, log, package export, CLI, README,
or original workspace file was changed. The remaining blocker is unchanged: no persisted supplied official NAR
capture corpus exists, so past-race and past-race-absence remain unsupported.

## Phase 4C-2d3b1i6c1b GitHub Implementation Review Correction

GitHub review of `cccacac2e2f1b532200b2e4c2196cf2ffe9916c7` found a structural mismatch: the tracked official
DebaTable has a header `article.raceCard` and a separate card-table `article.raceCard`. The correction extracts
header facts only from one exact header region and entry/jockey/odds facts only from one independently exact
supported entry table. No whole-document first-match selection or invented cross-page join was added.

HTML IDs and classes no longer re-dispatch a page kind. The canonical URL path is the sole page-kind boundary:
RaceMarkTable and other unsupported paths fail in URL validation, while a DebaTable URL with malformed structure
fails as normal c1b validation. The dedicated deterministic byte fixture now uses the official split-card shape,
including two horse rows in noncanonical source order and canonical output ordering.

Expanded coverage explicitly includes invalid host, required query-key absence, malformed percent escapes,
leading-zero baba code, missing active course selector, missing/duplicate UTF-8 meta declaration, missing odds,
missing/duplicate jockey selectors, exact wrong response type, Japanese place layout, package-root non-export, and
absence of `float(` source conversion.

Codex local rerun with Python 3.14.5 / pytest 8.3.5:

```text
Dedicated c1b: 8 passed
c1a source records: 8 passed
Historical snapshot / SQLite / migration related: 62 passed
Full suite: 2432 passed
Forbidden dependency source/AST check: passed
git diff --check: success
```

Status remains `PHASE_4C_2D3B1I6C1B_READY_FOR_REVIEW`. The only remaining blocker is unchanged: no persisted
supplied official NAR capture corpus exists, so c1b cannot create past-race or past-race-absence records.

## Phase 4C-2d3b1i6c1b GitHub Re-review Validation-boundary Correction

GitHub re-review of `8f758d33a615495cae3fe50616afd9e7687366fa` required two error-boundary corrections without
changing the approved split-card extraction or URL support semantics. `_canonical_url` now performs its sole
`urlsplit` call inside the validation-owned `ValueError` boundary before accessing `parsed.query`; malformed
bracketed-netloc input therefore raises exact `NarHistoricalInputSourceValidationError`.

The normalizer now uses a private guarded positive-decimal integer conversion helper for untrusted `horseNum` and
`distance_m`. It preserves arbitrary-length canonical positive decimal acceptance at the lexical level, but converts
Python's long-integer conversion `ValueError` to `NarHistoricalInputSourceValidationError`. No artificial provider
range, `sys.set_int_max_str_digits`, or broad exception handling was added.

Dedicated regressions cover malformed URL parser failure, a 10,000-digit horse number, and a 10,000-digit distance
token, each asserting the exact NAR validation exception type.

Codex local rerun with Python 3.14.5 / pytest 8.3.5:

```text
Dedicated c1b: 9 passed
c1a source records: 8 passed
Historical snapshot / SQLite / migration related: 62 passed
Full suite: 2433 passed
Forbidden dependency source/AST check: passed
git diff --check: success
```

Status remains `PHASE_4C_2D3B1I6C1B_READY_FOR_REVIEW`. The remaining blocker is unchanged: no persisted supplied
official NAR capture corpus exists, so c1b cannot create past-race or past-race-absence records.

## Phase 4C-2d3b1i6c1c Preparation

Phase c1b is formally complete at `f6a72be9e9a6934cfa48c6b0ff41954fb7d51de1` on
`feature/ver0.8-simulator`. c1c is `DRAFT_FOR_REVIEW` and is documentation-only: no production, test, migration,
schema, repository, database, log, README, CLI, or original-workspace file changed.

Read-only investigation confirms that c1a validates individual immutable source records and source IDs, while the
existing historical snapshot domain owns the immutable output schema, audit-key completeness, and content digest.
The new proposed boundary is a single pure keyword-only builder from an exact tuple of c1a records plus explicit
dataset/race/cutoff/capture inputs and an explicit external-entry to local-race-entry mapping.

The preparation freezes these design decisions for review:

- call the c1a set validator first and propagate its validation/conflict errors unchanged;
- require one source family, one track, full entry/jockey/odds triples, and exactly one form of past evidence per entry;
- select the sole track URL as the snapshot-level source URL only when it is present, otherwise preserve None, without requiring non-track URL equality;
- require a complete, exact, positive, unique caller mapping rather than DB lookup or horse-number fallback;
- order entries by horse number ascending and past races by strictly unique race date descending;
- map each immutable source record one-to-one to the established provenance key shape and preserve its exact source ID/timestamps;
- require every source stamp to be no later than both captured_at and information_cutoff;
- reject c1b DebaTable-only output because missing history is not absence proof.

The proposed implementation remains one new module, `historical_input_snapshot_builder.py`, one dedicated test
module, and the two phase documents. It has no repository/schema/migration or package-export change. The single
open blocker is complete official past-race or valid c1a absence evidence for every entry; c1c must not fabricate it.


## Phase 4C-2d3b1i6c1d1 Preparation — NAR Target Horse Identity

Status: DRAFT_FOR_REVIEW.

d1 is a docs-only prerequisite from formal base 960c341. It designs the smallest c1b entry-payload evolution and does
not implement it. Official target DebaTable inspection found row-local horse links in the same row as horse number,
jockey, and odds. Observed official link forms include:

    /KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=30036406666
    /KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=30038401876

The latter resolves to the official horse page. The code is treated as an official provider identifier based on supplied
anchor bytes; no HTTP result is needed or used by future c1b. The prior inline c1b fixture has a horseName anchor without
href, so it is insufficient as the positive contract fixture.

The frozen future row-local contract is exactly one a.horseName[href] in every selected entry tr. Relative links are
anchored to https://www.keiba.go.jp; absolute links must be https://www.keiba.go.jp. The path is exactly
/KeibaWeb/DataRoom/HorseMarkInfo and the sole query key is exactly k_lineageLoginCode. Unknown/duplicate/missing/blank
keys, malformed percent escapes, non-default ports, credentials, fragments, controls, wrong paths/hosts, and zero or
multiple row-local anchors fail at the existing validation boundary.

The lineage code is preserved lexically as ASCII [1-9][0-9]*: no leading zero, sign, whitespace, Unicode digit,
scientific notation, or int conversion. The future entry value is exactly:

    external_horse_id = nar:horse:{k_lineageLoginCode}

external_entry_id remains the target-race entry ID. c1a already accepts external_horse_id and will intentionally give
the more-complete entry record a new source_id. c1c already propagates the value into HistoricalExternalEntryIdentity.
No c1a or c1c change is required.

A new authentic fixture is required for the positive implementation test:
tests/fixtures/nar/deba_table_target_horse_identity.html. It must contain at least two official rows and pinned lineage
codes. Future scope is limited to c1b production/test, that fixture, and the two phase docs. Public API remains
unchanged; all helper parsing remains private.

The dedicated future tests will pin positive row-local mapping, deterministic identity/source IDs, distinct multi-row
codes, malformed link grammar, no fallback to None/name/horse number, no HTTP/DB/filesystem, c1a validation, c1c
propagation, and package-root non-export.

blocker: d1 must be independently approved before c1d can bind historical official rows to target entries; absence,
historical field mapping, and historical provenance remain out of scope.


## Phase 4C-2d3b1i6c1c Implementation Review Validation-boundary Correction

GitHub implementation review of `64865f2ec62a54c424fedfc16bde7e16cf679552` required one fail-closed caller
datetime correction. The shared exact-datetime helper now catches only `TypeError`, `ValueError`, and `OverflowError`
raised while evaluating `tzinfo.utcoffset()`, then raises exact `HistoricalInputSnapshotAssemblyError`. The existing
exact-type and awareness requirements are retained; no UTC substitution, current time, repair, or broad exception
handler was added. Dedicated regressions cover a deterministic custom `tzinfo` raising `ValueError` for both
`captured_at` and `information_cutoff`.

The correction also explicitly pins `information_cutoff > scheduled_start_at`, non-Mapping mappings, non-string
mapping keys, and zero/negative local race-entry IDs. All source grouping, completeness, source URL, provenance,
past evidence, and deterministic ordering contracts remain unchanged.

Codex local verification with Python 3.14.5 / pytest 8.3.5 / tzdata 2026.3:

```text
Dedicated c1c: 12 passed
c1a source records: 8 passed
Snapshot domain: 16 passed
SQLite/migration regression: 46 passed
Full suite: 2445 passed
Forbidden dependency/source/AST check: passed
git diff --check: success
```

Status remains `READY_FOR_REVIEW`; formal integration has not occurred.


## Phase 4C-2d3b1i6c1d1 Implementation

Status: READY_FOR_REVIEW.

Implemented the approved c1b-only target horse identity boundary. Every selected horse row now requires exactly one
row-local a.horseName[href]. The private validator accepts only relative or official absolute HTTPS HorseMarkInfo links,
with exact path /KeibaWeb/DataRoom/HorseMarkInfo and exactly one k_lineageLoginCode query value. It rejects malformed
URL parsing, fragments, credentials, unsupported port, foreign host, wrong path, unknown/duplicate/missing/blank key,
plus ambiguity, malformed percent encoding, and noncanonical lineage text.

The identity is lexical ASCII [1-9][0-9]* and the exact entry value is nar:horse:{k_lineageLoginCode}; no untrusted
integer conversion, HTTP request, filesystem access, DB access, legacy parser/provider, or public API was added.
external_entry_id remains unchanged. c1a is unchanged and intentionally recomputes entry source IDs from the new
entry payload; track/jockey/odds payloads are unchanged. c1c is unchanged and the dedicated regression proves its
existing external_horse_id propagation with explicit valid absence evidence.

Added official-derived immutable test fixture:
tests/fixtures/nar/deba_table_target_horse_identity.html. It contains two actual NAR DebaTable row structures and
pinned official HorseMarkInfo lineage links 30036406666 and 30038401876. Dedicated coverage includes row-local
association, deterministic output, source-ID evolution, strict anchor/token mutations, accepted relative/official
absolute links, huge lexical token behavior, c1a set validation, c1c propagation, package-root non-export, and existing
c1b source/AST boundary coverage.

Verification runtime recovery created the external Python 3.14.5 venv
`C:\\Users\\garim\\.cache\\keibaos-verification\\d1-py314` with system site packages, pytest 8.3.5, and tzdata
2026.3. The project import smoke check passed. Required pytest verification then passed: dedicated d1 11, c1a 8,
c1c 12, related historical snapshot/migration/SQLite repository 40, and full suite 2447. The forbidden
dependency/source/AST check and git diff --check passed. The runtime blocker is resolved; implementation remains
READY_FOR_REVIEW pending independent ChatGPT review and must not be integrated.


## Phase 4C-2d3b1i6c1c Implementation

The approved PREPARE contract from `20b7fb24c4772d7a12e5d8d6356000a3331f5d56` was materialized on
`review/4c-2d3b1i6c1c-implementation`, based directly on formal commit
`f6a72be9e9a6934cfa48c6b0ff41954fb7d51de1`. The implementation adds only the pure
`build_historical_input_snapshot` keyword-only boundary and its one assembler-owned
`HistoricalInputSnapshotAssemblyError`.

The builder first delegates c1a record-set validation and propagates its validation/conflict errors unchanged. It
then enforces one source family, one track, complete entry/jockey/odds triples, exact external-to-local mapping,
one past-evidence form per entry, track-only race facts, and causal capture/cutoff/start eligibility. It never reads
SQLite, calls a provider/parser, accesses files or the clock, saves a snapshot, or exports from the package root.

Track `canonical_source_url` remains provider-neutral: a non-null track URL is selected exactly, and a None track URL
is preserved as None. Non-track URLs are never selected or synthesized and remain represented through each exact c1a
source ID in provenance. c1b DebaTable-only source tuples are rejected because they lack both past-race records and
valid absence proof.

Entries are emitted by horse number with contiguous entry order. Per-entry past chronology is race date descending,
same-date ambiguity fails closed, and final snapshot tuples are canonicalized as `(race_entry_id, past_race_index)`
ascending for past races and `audit_key` ascending for provenance. The dedicated permutation case proves exact
snapshot equality and equal content digest despite materially different input tuple ordering.

Codex local verification using temporary Python 3.14.5 / pytest 8.3.5 / tzdata 2026.3:

```text
Dedicated c1c: 11 passed
Historical source/snapshot/SQLite repository/migration regressions: 70 passed
Full suite: 2444 passed
Forbidden dependency/source/AST check: passed
git diff --check: success
```

Status is `READY_FOR_REVIEW`. The only remaining blocker is unchanged: c1b supplies no past-race or
past-race-absence evidence, so a complete snapshot still requires a later supplied-source phase.

blocker: c1b supplies no past-race or past-race-absence evidence, so no complete HistoricalInputSnapshot can yet be
assembled from its DebaTable-only output.

## Phase 4C-2d3b1i6c1d3b2b2 Trusted NAR Live HTTPS Capture Implementation

Implemented the approved live acquisition boundary on review branch
`review/4c-2d3b1i6c1d3b2b2-implementation` from formal
`5ab64c6c9401b56e4bacd5b3b4049452609ddf60`. The only production module is
`scripts/simulation/nar_official_response_live_capture.py`; it reuses the completed capture-domain URL validator,
immutable `NAROfficialResponseCapture`, and archive protocol without changing their APIs, capture schema, archive
repository, global migrations, legacy provider, or any parser/normalizer.

The public surface is exactly `NAROfficialLiveResponseCaptureService`,
`NAROfficialResponseCaptureTransportError`, and
`build_nar_official_live_response_capture_service`. `capture_response(*, response_url)` first canonicalizes the URL,
then samples requested_at, completes one private HTTPS transport operation, samples observed_at and stored_at,
constructs the immutable capture, persists it once, and only then returns. Successful time order is
`requested_at <= observed_at <= stored_at`; malformed clock samples fail closed without fabricated replacements.

The private requests transport uses certificate verification, `stream=True`, `allow_redirects=False`, an explicit
`(10.0, 10.0)` connect/read timeout, `Accept-Encoding: identity`, a stable User-Agent, and zero-retry adapters.
Only a complete HTTP 200 response with absent or identity content encoding, canonical effective URL equality, valid
Content-Length (when supplied), and streamed bytes no larger than 4 MiB is accepted. The raw parser-input body is
accumulated only as bytes: no `response.text`, `response.content`, apparent encoding, or decode/re-encode path is
used. Redirect/status/network/stream/length/effective-URL failures are transport errors; unsupported content encoding,
strict UTF-8 rejection, capture-domain validation, and archive errors retain their existing ownership.

The dedicated suite has fake transport, archive, clock, requests Session, and streaming response collaborators. It
pins canonical URL-before-network, exact byte identity through the archive and supplied-response conversion, causal
event ordering, all required status/redirect cases, no-retry request configuration, encoding policy, 4 MiB and
Content-Length limits, effective URL rejection, narrow requests failure translation, archive propagation, and source/
AST/package-root boundaries.

An unpersisted manual official probe using `Accept-Encoding: identity` completed on 2026-08-11. DebaTable www
returned HTTP 200, no Content-Encoding/Content-Length, and 297718 body bytes; RaceMarkTable www returned HTTP 200,
no Content-Encoding/Content-Length, and 96614 bytes; HorseMarkInfo www returned HTTP 200, no
Content-Encoding/Content-Length, and 83949 bytes. HorseMarkInfo www2 returned HTTP 301 with zero declared/body bytes,
which is correctly fail-closed under redirect-disabled policy. No probe body, fixture, or capture database row was
created. `LIVE_PROBE = PASS` for the supported www endpoints.

Status is `READY_FOR_REVIEW`; d3b2c composition, database-path ownership, discovery, collection, pagination,
scheduling, CLI, formal integration, and historical absence remain unstarted.

## Phase 4C-2d3b1i6c1d3b1 Uniform Historical Evidence Implementation

Status: READY_FOR_REVIEW.

Implemented the approved provider-neutral `HistoricalInputEvidenceReference` contract. Historical source records are
now schema version 3 with `his-v3:{record_kind}:{sha256}` identifiers derived from logical record content and ordered
evidence role/URL/raw-response-SHA values; evidence observations remain excluded from source IDs. Snapshot provenance
now owns the exact ordered evidence tuple, and snapshot content SHA-256 version 3 includes each evidence timestamp.

The existing NAR DebaTable normalizer computes SHA-256 from exact caller-supplied bytes and builds singleton evidence
for track, entry, jockey, and odds-win records without changing its parsing scope. The snapshot builder evaluates
every evidence observation against captured-at and information-cutoff. SQLite v012 replaces scalar provenance
timestamps only for an empty snapshot store, then persists normalized evidence children and reconstructs them
fail-closed on load.

Verification using the external Python 3.14.5 / pytest 8.3.5 runtime:

The approved migration-registry test scope extension was used only for
`tests/test_simulation_bet_plan_migration.py` and `tests/test_sqlite_persisted_simulation_application.py`, which now
pin v012 registry presence in their existing migration/application coverage.

- dedicated source-record tests: 11 passed
- snapshot-domain tests: 16 passed
- snapshot-builder tests: 12 passed
- NAR source tests: 12 passed
- SQLite/migration/application regression set: 74 passed
- combined phase suites: 125 passed
- full suite: 2454 passed
- `git diff --check`: success

No network, filesystem, database-file, capture-body, provider/parser, package-root, legacy model, or original-workspace
change was made. NAR historical past-race normalization and past-race absence remain out of scope.

## Phase 4C-2d3b1i6c1d3b1 Review Correction

Status: READY_FOR_REVIEW.

The SQLite repository now fail-closes when a selected snapshot contains an evidence child without its logical
provenance parent. The check is scoped to the selected snapshot and an invalid newest eligible snapshot never falls
back to an older snapshot. Dedicated corruption coverage now pins missing children, wrong roles, noncontiguous orders,
invalid hashes/timestamps, late observations, same-response timestamp disagreements, and an FK-disabled orphan child.

The source-ID contract is clarified without changing raw SHA-256 semantics. `C1A_FACT_CHANGE_ISOLATION_WITH_CONSTANT_
EVIDENCE_IDENTITY=YES`: with role/URL/raw SHA held constant, one logical factual change changes only its record ID.
`C1B_SHARED_RESPONSE_BYTE_CHANGE_SOURCE_ID_CHURN=ALL_RECORDS_FROM_RESPONSE`: a changed supplied DebaTable body changes
the shared raw SHA and all c1b-derived source IDs. This supersedes the old d1 source-ID consequence at that provider
boundary only; horse-lineage factual identity is unchanged.

HistoricalInputProvenance still has no scalar timestamp fields and no automatic InputAuditEntry adapter or production
dependency. v012 nonempty-store tests now prove failure occurs before any provenance-table replacement, child-table
creation, temporary-table residue, or migration registration.

Correction verification with the external Python 3.14.5 / pytest 8.3.5 runtime passed: source-record, snapshot,
NAR, repository, and v012 migration suites 68 passed; the remaining approved d3b1 targeted suites 59 passed; and
the full suite 2456 passed. Forbidden dependency/source/AST and package-root export checks passed, as did
`git diff --check`.

## Phase 4C-2d3b1i6c1d3b2a Implementation

Status: READY_FOR_REVIEW.

Implemented the separate pure `scripts/simulation/nar_historical_past_race_source.py` boundary. Its only
module-defined public name is `normalize_nar_historical_past_race_source_record`, with the approved keyword-only
inputs: one exact c1a NAR entry record, one supplied HorseMarkInfo response, and one supplied RaceMarkTable response.
The entry record supplies the target race, entry, and canonical NAR lineage; no independent caller identity override,
horse-name fallback, horse-number linkage, database, fetch, filesystem, or clock path exists.

The normalizer validates the full binding chain from target entry lineage through HorseMarkInfo and the selected history
link to the unique RaceMarkTable result-row lineage. It emits exactly one c1a v3 `past_race` with provider ID
`nar:result:20260503:31:1:horse:30074407776`, target race/entry envelope, and exactly two raw-response evidence roles:
`historical_race_context` for HorseMarkInfo and `historical_race_result` for RaceMarkTable. Each evidence reference
uses SHA-256 over exact supplied bytes, `available_at=None`, and the unmodified supplied `observed_at`. Timestamp-only
changes leave source IDs stable; changing either raw body changes the source ID.

The representative official-derived pair is stored as `MINIMIZED_AUTHENTIC_STRUCTURAL_FIXTURE`s: it preserves the
official selected structural headers, HorseMarkInfo history row/result link, RaceMark result row, and corner labels.
It yields 2026-05-03 高知 1R, Ｃ２－８ / Ｃ２, ダート 1400m, 雨 / 不良, finish 9, direct difference Decimal(2.6),
time 1:32.4, body weight Decimal(495) with Decimal(1), 妹尾浩, popularity 8, odds Decimal(42.5), passing order
9-9-9-11, and fourth-corner position 11. RaceMarkTable 着差 remains excluded from time-difference semantics.

Fourth-corner extraction uses row-local `コーナー通過順` only for the horse positions and the same page's
`全馬コーナー通過順` only for explicit label alignment. It requires unique increasing labels with exactly one corner 4
and matching component count, thereby supporting both `[1,2,3,4]` and `[2,3,4]` layouts without a fixed-index or
blind-last-component rule. JRA history, ばんえい, abnormal results, and missing/ambiguous direct facts remain fail-closed
unsupported states.

The dedicated regression suite covers the successful pair, every output field, URL/host validation, target entry and
lineage binding, raw-body and timestamp source-ID semantics, direct difference versus RaceMark margin, weight/change,
jockey normalization, positional corner alignment, multiplicity, horse-name fallback prohibition, c1c compatibility,
and c1c causal rejection for late evidence. No c1a/c1b/c1c builder/SQLite/migration/schema/package-root production
change was made. Historical replay still needs separately trusted causally observed captures; fixture timestamps are
test values only.

Verification used the external Python 3.14.5 / pytest 8.3.5 runtime. The dedicated pair suite passed 11 tests; the
related NAR/c1a/c1c/snapshot suites passed 52 tests; the full suite passed 2467 tests. Dedicated source/AST and
package-root non-export checks pass. `git diff --check` and the approved changed-file scope are verified before review
publication.

## Phase 4C-2d3b1i6d1d5e0 JRA Discovery-to-Absence Projection Handoff

Extended the immutable/slotted JRA complete-history discovery with evidence binding for the exact accessU response:
canonical URL, raw response SHA-256, and normalized UTC observed time. The discovery validates that its bound accessU
URL identifies the same formal horse as its target horse. Existing discovery parsing, closed event classification,
aggregate completeness, chronology, and cutoff behavior are unchanged.

Added the public pure absence projection from an exact bound discovery and the original exact supplied response. It
performs no discovery and no HTML parsing. It verifies the URL, raw body SHA, observed timestamp, and formal accessU
horse identity before emitting the existing neutral JRA absence record. It accepts only empty history or complete
transfer-only zero-actual-start history and rejects every actual-start category.

The existing direct absence normalizer still calls discovery exactly once and now delegates record construction to the
public projection. This resolves the collector predecessor's double-discovery conflict without duplicating the
absence-record constructor. No collector, capture, archive, migration, source/snapshot schema, NAR, bridge, or real
official acquisition work was added.

### d1d5e0 discovery target-lineage correction

Hardened the public `JRAHistoricalPastRaceDiscovery` constructor so that its authoritative target race and entry
lineage cannot be forged through direct construction. It now parses the target race through the formal JRA race parser,
requires the target entry to use that exact race prefix, requires a canonical positive horse-number suffix, and proves
the final entry ID with the existing formal JRA entry-ID builder. Malformed/non-JRA race IDs, wrong-race entries,
leading-zero or zero suffixes, and malformed entry material fail as
`JRAHistoricalPastRaceDiscoveryValidationError` before absence projection can emit neutral data.

The same discovery-domain error boundary now translates the expected lower-level capture validation error raised for
malformed direct accessU evidence-binding URLs. Existing discovery parsing, projection zero-discovery behavior, direct
normalizer one-discovery behavior, output shape, schemas, migrations, capture/archive behavior, and NAR behavior are
unchanged. Fresh verification under Python 3.14.5 / pytest 8.3.5 passed 22 dedicated discovery/absence tests, 138
related JRA/NAR/neutral tests, and the 2,610-test full suite. Package-export, forbidden-dependency/source/AST,
source-schema/snapshot-schema/migration-registry unchanged, and `git diff --check` checks passed.

## Phase 4C-2d3b1i6d1d5d2 JRA Zero-Actual-Start Past-Race-Absence Source

Implemented the narrow pure JRA absence-source boundary. It calls the formal d1d5b3 accessU discovery exactly once
and projects only its exact discovery domain. It performs no accessU HTML/CP932/aggregate/continuation/identity/
cutoff parsing or recomputation, and has no acquisition, archive, repository, database, filesystem, clock, or
orchestration responsibility.

The source accepts both formally complete zero-actual-start states: an empty official history, and a nonempty
transfer-only discovery whose event kinds are all `PROVEN_NON_START`. It rejects JRA, non-JRA, and unsupported actual
starts even when they coexist with transfers. The neutral `past_race_absence` record remains the existing exact
three-value shape, with `result_count=0` meaning zero actual prior starts rather than zero displayed rows.

Each record has one `past_race_absence_query` evidence reference tied to the exact supplied accessU URL and raw-byte
SHA-256, with `available_at=None`, unchanged `observed_at`, and no request identity. Existing source canonicalization
therefore preserves timestamp-only source-ID stability and changes source ID when raw evidence bytes change.

Dedicated tests cover real discovery for empty, one-transfer, and multi-transfer complete histories; all actual-start
rejections; translated discovery failures; public surface/purity; neutral validation; and snapshot acceptance for
both empty and transfer-only absence states plus the existing past-race/absence XOR rejection. No schema, builder,
repository, capture, discovery, normalizer, NAR, or package-export change was made.

### d3b2a Target-entry Binding Correction

`TARGET_ENTRY_HORSE_NO_CONSISTENCY = REQUIRED`: the normalizer now extracts the canonical horse-number suffix from
the exact target entry ID and fails validation unless it equals that entry record's committed `horse_no`. This closes
the target-entry internal-coherence gap without changing c1a. `HISTORICAL_ROW_IDENTITY = LINEAGE_ONLY` remains frozen:
the historical RaceMarkTable row is still selected exclusively by `k_lineageLoginCode`, and a valid target horse number
need not equal the historical race's horse number.

The dedicated regression now rejects an entry-ID suffix/record-value mismatch, proves a changed historical horse
number with the same lineage still normalizes, directly tests both supplied-response exact-type boundaries, and proves
that both late HorseMarkInfo evidence and late RaceMarkTable evidence are rejected by the unchanged c1c builder.
`BOTH_EVIDENCE_CAUSALITY_REGRESSIONS = PASS`; target-entry source-ID independence remains covered. Fixtures are
unchanged.

### d3b2a Structural JRA History Classification Correction

`JRA_CLASSIFICATION = ROW_STRUCTURAL_NOT_PAGE_GLOBAL_TEXT`. Missing requested NAR history is no longer classified from
arbitrary page text such as `JRA` or a jockey affiliation. The HorseMarkInfo history table now inspects each result
navigation link: supported NAR RaceMarkTable links retain exact date/babaCode/raceNo identity; recognizable official
JRA navigation is a JRA-only state only when no NAR navigation exists in that table. Thus
`MIXED_NAR_JRA_HISTORY_PAGE = SUPPORTED_FOR_EXACT_NAR_SELECTION`, while
`MISSING_REQUESTED_NAR_IDENTITY = VALIDATION_ERROR` and
`JRA_ONLY_RECOGNIZED_HISTORY = UNSUPPORTED_ERROR`.

The dedicated tests pin a local NAR result whose jockey affiliation displays `(JRA)`, unrelated page-global JRA text,
mixed NAR/JRA selection and missing-NAR behavior, structurally JRA-only history, and generic missing navigation.
`JOCKEY_AFFILIATION_JRA_DOES_NOT_IMPLY_JRA_RACE = YES`. No fixture or collaborator changed.

## Phase 4C-2d3b1i6c1d3b2b1 Trusted NAR Capture Archive Implementation

Implemented the approved d3b2b design on a review branch based exactly on formal
`4af5a7ba4f18769f365ac2c934bcfd0ffcf38818`. The implementation is deliberately isolated from the main KeibaOS
database and migration registry. `DATABASE_LOCATION = SEPARATE_NAR_CAPTURE_DATABASE`; the main migration sequence
remains `(8, 9, 10, 11, 12)`, with no v013, global migration runner/version/test change, or capture table in the
simulation database.

The new pure capture domain owns the closed DebaTable/HorseMarkInfo/RaceMarkTable URL vocabulary, deterministic URL
canonicalization, immutable frozen/slotted capture values, strict UTF-8 parser-input bytes, exact raw SHA-256, and the
deterministic `nar-capture-v1:` JSON identity. It contains no HTTP, SQLite, filesystem, clock, or normalizer-private
helper dependency. It reconstructs the existing `NarSuppliedOfficialResponse` exactly, including original archived
body bytes and supplied observation time.

The dedicated v001 migration is transaction-neutral and creates only content-addressed body storage, immutable capture
observations, and `ux_nar_official_response_captures_evidence` over the exact evidence tuple. Its independent runner
owns foreign-key activation, registry validation, transaction ownership, pending ordering, and rollback. It does not
import or invoke the global migration runner. The injected-connection archive repository is append-only: it atomically
deduplicates valid body bytes, rejects same-ID metadata conflicts, makes exact reinsert idempotent, and rolls back a
new body when later capture insertion fails. Every retrieval revalidates all stored identity/body/URL/timestamp/header
invariants and fails closed for corruption. Exact lookup miss raises the capture-domain missing error with no fallback.

`CROSS_DATABASE_LINKAGE = EXISTING_EVIDENCE_IDENTITY_TUPLE`; no cross-database transaction, FK, c1a field, snapshot
field, or body persistence in evidence was added. Future composition owns `capture_database_path`; d3b2b2 live HTTP,
clock, collection, pagination, and orchestration remain unimplemented.

Verification with external Python 3.14.5 / pytest 8.3.5 passed: dedicated capture suites 20 passed; related existing
NAR/c1a/c1c snapshot suites 53 passed; complete suite 2488 passed. Source/public-surface checks confirm package root
unchanged, global migrations unchanged, capture domain/repository free of network/filesystem/clock ownership, and
repository free of `ATTACH`. `git diff --check` passed. Status is `READY_FOR_REVIEW` pending independent GitHub code
review; no formal integration was performed.

### d3b2b1 Archive Corruption Fail-Closed Correction

Review found that a same capture save could insert a missing body before discovering that the capture row already
existed, thereby repairing pre-existing archive corruption. The archive now preflights capture ID, exact evidence tuple,
and body SHA before any body insert. `SAVE_ON_PREEXISTING_ARCHIVE_CORRUPTION = FAIL_CLOSED_NO_REPAIR`: a missing body
referenced by the same capture or by an older observation with the same SHA now raises `RepositoryDataIntegrityError`,
leaves the body missing, leaves existing rows intact, and ends the transaction. An existing capture additionally proves
its exact evidence tuple is uniquely coherent before idempotent success.

Both load routes now apply symmetric exact-evidence uniqueness validation during reconstruction. Broken tuple uniqueness,
missing body, body/content-length corruption, and SQLite errors from reconstruction/body/evidence reads are all
`RepositoryDataIntegrityError`; valid tuple absence remains `NAROfficialResponseCaptureMissingError` and malformed
caller input remains `RepositoryValidationError`.

Dedicated v001 DDL no longer uses `IF NOT EXISTS`. `PREEXISTING_UNREGISTERED_CAPTURE_SCHEMA = FAIL_CLOSED`: a manually
created colliding capture table without v001 registration aborts dedicated migration and leaves v001 unregistered. Direct
v001 application is transaction-neutral but intentionally has no independent idempotency promise; registry-runner
idempotency remains the sole approved path. Fresh verification passed 25 dedicated tests, 53 related existing tests,
and 2493 full-suite tests.

### d3b2b1 Dedicated Migration Registry Structural Validation Correction

The dedicated runner no longer trusts a same-name migration registry solely because `SELECT version,name` succeeds.
Before reading applied versions or applying v001, it now verifies `sqlite_master` object kind and normalized approved
DDL, then exact ordered `PRAGMA table_info` columns, declared types, primary-key, and NOT NULL properties. This pins
the approved `WITHOUT ROWID` registry containing only positive integer `version` and nonempty text `name` checks.

`CAPTURE_MIGRATION_REGISTRY_SCHEMA_VALIDATION = REQUIRED` and
`PREEXISTING_MALFORMED_CAPTURE_MIGRATION_REGISTRY = FAIL_CLOSED`. A weak pre-existing same-name table aborts before
capture table creation or v001 registration; `get_applied_capture_schema_versions()` fails as well. No ALTER, DROP,
replacement, row copy, or constraint addition is permitted (`MALFORMED_REGISTRY_AUTO_REPAIR = FORBIDDEN`). Dedicated
tests additionally pin stored name mismatch and malformed-row failure. Existing v001 table-collision, runner
idempotency, rollback, active-transaction, foreign-key, and global-migration isolation behavior remains covered.
Fresh verification passed 27 dedicated tests, 53 related existing tests, and 2495 full-suite tests.

## Phase 4C-2d3b1i6c1d3a Implementation Verification Scope Blocker

The approved d3a implementation updated only its allowed historical domain, builder, repository, v011 migration,
runner, and dedicated tests. External Python 3.14.5 / pytest 8.3.5 verification passed the directly affected suites:
96 passed across c1a, snapshot domain, builder, SQLite repository, migration, simulation-migration, and d1 regressions.
The changed simulation modules also passed the forbidden dependency/source check.

The full suite ran and found five migration-registry expectation failures, not a production defect: 2445 passed and 5
failed. The failures are in the currently unauthorized files `tests/test_simulation_bet_plan_migration.py` (three) and
`tests/test_sqlite_persisted_simulation_application.py` (two). Each still asserts that runner-applied migrations end at
v010; the approved runner contract now registers and applies v011 to an empty store. Their production behavior is
otherwise successful.

Updating those expectations is necessary for a passing full suite, but those files are outside d3a Allowed Files. No
scope expansion or edit was made. The phase is returned to DRAFT_FOR_REVIEW pending explicit authorization to include
only those affected tests. No commit or push was performed.

blocker: full-suite completion requires an explicit d3a Allowed Files correction for the five v011 registry-expectation tests.

## Phase 4C-2d3b1i6c1d3a Implementation Scope Extension Result

The scope extension authorized only `tests/test_simulation_bet_plan_migration.py` and
`tests/test_sqlite_persisted_simulation_application.py`. They now assert the exact global migration sequence 8, 9,
10, 11 and the approved v011 name, while preserving their original v009 and persisted-application responsibilities.
No production code changed after the extension.

External Python 3.14.5 / pytest 8.3.5 verification passed: added bet-plan migration suite 17 passed; added persisted
application suite 8 passed; c1a/snapshot/builder/repository/migration/d1 targeted suite 96 passed; full suite 2450
passed. The forbidden dependency/source check passed and `git diff --check` passed. Status is
`PHASE_4C_2D3B1I6C1D3A_READY_FOR_REVIEW` pending independent ChatGPT code review.

blocker: none for d3a implementation verification; d3b multi-source evidence/provenance work remains unstarted.

## Phase 4C-2d3b1i6c1d3a Final Regression Correction

GitHub implementation review of `001c2e77b759fa7c420f38176abd3fea8c9ce82c` approved production and required two
test-only contract pins. The c1a suite now proves within-v2 past-race-only source isolation: changing only
`reference_time_difference_seconds` changes only that past-race source ID/payload; track, entry, jockey, and odds
records retain equal v2 payloads and source IDs, and both record sets validate independently.

The snapshot-domain suite now independently proves that `HistoricalPastRaceSnapshot` accepts Decimal zero and rejects
int, bool, float, negative Decimal, NaN, and infinities at its own dataclass boundary. It also pins the public new
field and absence of a `margin` compatibility attribute. No production, migration, fixture, or scope-extension test
changed in this correction.

External Python 3.14.5 / pytest 8.3.5 verification passed: c1a 9, snapshot domain 16, complete d3a targeted set 97,
and full suite 2451. Forbidden dependency/source checking and `git diff --check` passed. Status remains
`PHASE_4C_2D3B1I6C1D3A_READY_FOR_REVIEW` pending independent ChatGPT re-review.

blocker: none for d3a implementation verification; d3b remains unstarted.

## Phase 4C-2d3b1i6c1d1 Source-ID Isolation Review Correction

GitHub implementation review of `86c26816d894fbee98691c9c8f231dee2129503e` approved the d1 production module,
authentic official fixture, and HorseMarkInfo parsing. The sole required correction is a dedicated deterministic
source-ID isolation regression; production and the fixture remain unchanged.

Starting with a valid two-entry supplied DebaTable response, the regression changes only entry 1's valid
`k_lineageLoginCode` from `30000000001` to `30000000999`. It proves that only entry 1's c1a entry payload
`external_horse_id` and entry `source_id` change. The target-race URL, horse number, jockey, odds, track facts,
entry 2 identity, and observed_at remain unchanged. It explicitly proves equal track source ID, equal selected-entry
jockey and odds-win source IDs, and equal entry/jockey/odds payloads and source IDs for entry 2.

Verification using external Python 3.14.5 / pytest 8.3.5 / tzdata 2026.3:

```text
Dedicated d1: 12 passed
c1a: 8 passed
c1c: 12 passed
Historical snapshot/migration/SQLite repository regressions: 40 passed
Full suite: 2448 passed
Forbidden dependency/source/AST check: passed
git diff --check: success
```

Status remains `PHASE_4C_2D3B1I6C1D1_READY_FOR_REVIEW`; the correction is pending independent ChatGPT review and
must not be integrated into the formal branch.

## Phase 4C-2d3b1i6c1c Source URL Policy Revision

GitHub design review of `3c64a809bc015bee494dd4c97a6cdc67f4ffb8a2` found that c1c must preserve the committed
provider-neutral optionality of the sole track record's `canonical_source_url`. The corrected policy is exact:
when the track URL is non-null, `HistoricalSourceIdentity.source_url` is that exact URL; when it is None, snapshot
construction remains valid and `HistoricalSourceIdentity.source_url` is None. A missing track URL is not a failure.

c1c must not synthesize a snapshot URL from a non-track record, provider_record_id, source_id, external_race_id,
local data, or legacy URLs, and it must not select a non-track URL. Differing non-track URLs remain immutable c1a
record payload and participate through their exact c1a `source_id`; provenance continues to reference the exact
source ID without duplicating canonical URLs. The existing c1a non-null URL rule for `past_race_absence` remains
unchanged and is merely consumed by c1c.

The dedicated c1c plan now explicitly covers both valid track-source-identity cases, including a non-null track URL
and a None track URL, plus non-track URL nonselection, invariance under differing non-track URLs, and exact c1a
source-ID provenance propagation. Status remains `DRAFT_FOR_REVIEW`; implementation has not started.

blocker: c1b supplies no past-race or past-race-absence evidence, so no complete HistoricalInputSnapshot can yet be
assembled from its DebaTable-only output.

## Phase 4C-2d3b1i6c1c Snapshot Child Ordering Revision

GitHub design re-review of `731e6849be675612d58a060d80009195ade31c6e` approved the source URL policy and required
only explicit final child-tuple ordering. Entries remain sorted by `horse_no` ascending and receive contiguous
zero-based `entry_order` values. Per-entry past-race chronology remains `race_date` descending with same-date
ambiguity rejected and contiguous zero-based `past_race_index` values.

After those indexes are assigned, the final snapshot `past_races` tuple is sorted globally by exactly
`(race_entry_id, past_race_index)` ascending. The final snapshot `provenance` tuple is sorted globally by exactly
canonical `audit_key` ascending using normal Python string ordering. Neither final tuple may depend on supplied source
tuple order, horse number, external entry ID, source ID, record kind, insertion order, database rows, provider IDs,
or hash/random order.

The future dedicated suite now includes a materially noncanonical source-record permutation with two entries and
multiple past races. It must prove exact snapshot equality and equal `content_sha256`, plus exact final entry,
past-race, and provenance tuple orders. Status remains `DRAFT_FOR_REVIEW`; implementation has not started.

blocker: c1b supplies no past-race or past-race-absence evidence, so no complete HistoricalInputSnapshot can yet be
assembled from its DebaTable-only output.

## Phase 4C-2d3b1i6c1d3b2c1 Complete NAR HorseMark History Discovery Implementation

Implemented the pure supplied-response c1 boundary on formal base `93fad49e7b188e3b4492cc7fe0eb61d36d16b735`.
`discover_nar_historical_past_race_history` accepts only validated NAR target track/entry c1a records and one exact
UTF-8 HorseMarkInfo response. It validates the target race/entry/lineage chain, HorseMarkInfo canonical host and
lineage, strict target-date chronology, and the supplied observation time against scheduled start. It returns every
classified row in official order: NAR actual starts, row-structural JRA actual starts, proven `取消`/`取止` non-starts,
or a fail-closed unsupported/validation result. It does not filter providers or truncate history.

NAR row-local RaceMark identities become canonical `www.keiba.go.jp` result URLs and `nar:event` identifiers. JRA
rows retain a deterministic date/place/R identity with no invented NAR result URL. Proven non-starts remain visible
for audit but do not count as actual starts. The exact HorseMarkInfo zero-history layout produces `events=()` with
`proven_zero_history=True`; a table never becomes zero merely because it has no normal starts.

`normalize_nar_historical_past_race_absence_source_record` internally reruns discovery and accepts only that exact
zero state. It creates the existing v3 `past_race_absence` record with the exact target query scope, result count zero,
one HorseMarkInfo-only evidence role, SHA-256 over the supplied bytes, `available_at=None`, and preserved observed
time. Evidence timestamp changes do not change its source ID; raw byte changes do.

Added minimized authentic structural HorseMark fixtures for complete-history classification and the official explicit
zero-history layout. They are parser fixtures, not trusted historical captures. JRA result normalization, collection,
archive access, network, snapshots, and prediction integration remain unimplemented.

Verification: dedicated c1 tests 10 passed; related c1a/NAR/capture/snapshot tests 87 passed; full suite 2520 passed
under Python 3.14.5 and pytest 8.3.5. Status is `READY_FOR_REVIEW`; stop for independent implementation review.

## Phase 4C-2d3b1i6c1d3b2c1 Exact HorseMarkInfo Table Schema Correction

The discovery boundary now requires the complete normalized approved HorseMarkInfo heading tuple in its exact order,
not heading membership. The only accepted span is `天候・馬場` with exact `colspan="3"`; all other headings are
unspanned and no heading may use `rowspan`. History rows continue to require exactly 23 direct unspanned cells.
Unknown, duplicated, reordered, missing, or span-altered headings fail closed before any history discovery. The
separate exact zero-history page state remains unchanged because it has no history table.

Regression coverage now directly rejects unknown, duplicate, reordered, and missing headings; incorrect or missing
weather/track colspan; and both 22-cell and 24-cell rows. Dedicated verification is pending the final required
related and full-suite reruns. Status remains `READY_FOR_REVIEW`.

Correction verification completed under Python 3.14.5 / pytest 8.3.5: dedicated discovery/absence tests 11 passed;
related c1a/NAR/capture/snapshot tests 87 passed; full suite 2521 passed. Package-root export and forbidden
dependency/source/AST checks passed. Status remains `READY_FOR_REVIEW`; stop for independent re-review.

## Phase 4C-2d3b1i6d1a1 Implementation Stop — Out-of-Scope Global Namespace Regressions

Implemented the allowed v4 source/snapshot/migration changes in the uncommitted d1a1 worktree and verified the
in-scope source/snapshot/builder/NAR suite (52 passed) and SQLite/migration suite (77 passed). The required broader
source-producer run then found two failures caused solely by hard-coded `his-v3` expectations outside the approved
Allowed Files:

* `tests/test_nar_historical_input_source.py::NarHistoricalInputSourceTests::test_lineage_change_isolates_factual_payload_but_changes_shared_response_source_ids`
* `tests/test_nar_historical_past_race_absence_source.py::NARHistoricalPastRaceAbsenceSourceTests::test_zero_fixture_creates_exact_c1a_absence_record`

The d1a1 contract requires every record kind to use `his-v4`, including c1b and past-race-absence records, but the
authorized list does not permit updating either failed test. Per the phase stop rule, no out-of-scope edit, commit,
push, full-suite run, or formal integration was performed. The uncommitted allowed-file implementation is preserved
unchanged pending an explicit scope extension.

Scope extension verification updated only the two authorized stale `his-v3` assertions. Those tests pass (16
passed), as do the d1a1 source/snapshot/builder/NAR suite (82 passed) and SQLite/migration suite (77 passed). The
fresh full suite then collected 2523 tests and produced 2522 passed, one failure:

* `tests/test_nar_official_response_capture_migration.py::CaptureMigrationTests::test_runner_creates_exact_dedicated_schema_and_no_global_tables`

Its dedicated NAR capture schema is unaffected; the failure is solely its hard-coded global `MIGRATIONS` tuple
`(8, 9, 10, 11, 12)`, which now correctly contains v013. That test is outside the authorized 20-file scope. Per the
stop condition, no change to it, no commit, and no push were made. The complete allowed-file worktree remains
preserved for an explicit additional scope decision.

## Phase 4C-2d3b1i6d1a1 Provider-Neutral Historical Race-Time Domain Implementation

Implemented the approved global historical source transition on formal base
`7b4a0f5e28311c2d64685f6d3309f68556e67f8b`. c1a schema version is now 4 and all six record kinds use the `his-v4`
source-ID namespace. Snapshot canonical payload schema version is 4. `reference_time_difference_seconds` has been
removed from c1a past-race values, `HistoricalPastRaceSnapshot`, builder mapping, SQLite persistence/reconstruction,
and the NAR pair normalizer; exact normalized official `race_time` text remains.

Added empty-store-only v013, `v013_historical_past_race_race_time_domain_schema`, which removes
`reference_time_difference_seconds_text`. It refuses nonempty snapshot stores before schema mutation and preserves
identity/linkage rows on empty stores. v011/v012 remain unchanged. No legacy prediction adapter, race-time
calculation, textual-margin conversion, provider acquisition, JRA production work, or reference-date fix was added.

The two approved namespace test extensions now assert `his-v4`; the capture migration extension asserts the global
registry `(8, 9, 10, 11, 12, 13)` while preserving its dedicated capture-registry isolation checks. Fresh verification
under Python 3.14.5 / pytest 8.3.5 passed: capture migration 8, core targeted d1a1 suite 82, related suite 93, and
full suite 2523. Status is `READY_FOR_REVIEW`; stop for independent implementation review.

## Phase 4C-2d3b1i6d1b3 Pure JRA Official Race/Horse Identity Implementation

Implemented the pure supplied-string JRA identity domain on formal base `04c0fbcad2ea13b2e325e795e6de022718edb01a`.
The new module owns only strict race, horse, entry, and result identity construction plus resolved accessS/accessU
URL validation. It uses the b1 native key grammar exactly and preserves canonical lexical tokens without integer
normalization. `jra:race:<YYYY>:<VV>:<MM>:<DD>:<RR>`, `jra:horse:<10-digit-key>`, race-local entry IDs, and
`jra:result:<...>:horse:<key>` are the only output spellings.

Officially observed accessS aliases with selectors `01` and `10`, raw or `%2F` CNAME separators, and distinct
opaque tails collapse to the same JRA race identity. The accessU `00` and `10` selector forms likewise collapse to
the same ten-digit horse identity. All inputs are fail-closed: non-JRA hosts, ports, credentials, fragments,
duplicate/unknown query keys, ambiguous encoding, unobserved selector families, lowercase/non-hex tails, invalid
token domains, and malformed types are rejected. The calendar CNAME date is validated only as date material and
year consistency; it never becomes entity identity or a reconstructed meeting date.

No network, capture, storage, clock, HTML parser, provider lookup, bridge, race discovery, normalizer, NAR code,
or package-root export was added. The b2 blocker remains exact: `NAR_LINEAGE_TO_JRA_HORSE_ID_LINK = NOT_PROVEN`;
mixed-history collection remains unsupported. Status is `READY_FOR_REVIEW` pending independent implementation
review.


## Phase 4C-2d3b1i6d1c1 JRA Capture Domain and Dedicated Archive Implementation

Implemented the approved pure JRA capture domain, dedicated v001 schema/migration runner, and connection-injected
append-only SQLite archive on formal base `7632a1381c77403e55284e027392d0fbc1f5a346`. The new capture boundary
accepts only accessS race-result and accessU horse-profile/history URLs validated through the public JRA identity
contract. It canonicalizes only the CNAME delimiter to uppercase `%2F`, preserves selector/date/tail URL identity,
requires strict CP932 bytes, hashes the exact bytes before decoding, and derives deterministic
`jra-capture-v1:<sha256>` identities. No live HTTP service, JRA result normalizer, NAR modification, bridge,
global migration, package export, database file, or log changed.

The separate archive has dedicated registry `jra_official_response_capture_schema_migrations`, raw-BLOB dedup table,
and immutable capture-observation table. It uses exact evidence lookup by canonical URL, raw SHA, and observed UTC
timestamp; exact reinserts are idempotent, differing immutable content conflicts, and missing/corrupt body rows,
duplicate evidence, and malformed stored values fail closed without repair. The global migration sequence remains
8 through 13 and NAR capture remains unchanged.

Verification so far under Python 3.14.5 / pytest 8.3.5: dedicated JRA domain/migration/repository tests 7 passed;
existing JRA identity plus NAR capture/migration/repository regressions 35 passed. Full-suite and static verification
remain required before this review branch is published. Status is `READY_FOR_REVIEW`; no formal integration or d1c2
live-capture work has begun.

## Phase 4C-2d3b1i6d1c1 Migration Registry Hardening Correction

The dedicated JRA capture migration runner now validates the pre-existing registry schema exactly and fail-closed:
the approved two-column `WITHOUT ROWID` shape, positive integer version check, unique typed nonempty name check,
and registered migration rows are all required. Missing constraints, extra columns, wrong or unknown registrations,
and malformed rows are rejected. Pre-existing JRA body or capture tables without a valid registry are also rejected.
No registry/table adoption, alteration, drop, or automatic repair is permitted; the migration transaction rolls back.

Fresh migration verification passed 6 tests under Python 3.14.5 / pytest 8.3.5. The correction remains
`READY_FOR_REVIEW`; full dedicated, related, static, and full-suite verification is required before publishing the
review correction. No live capture, provider bridge, NAR change, global migration, or formal integration has begun.

## Phase 4C-2d3b1i6d1c1 Final Registry Semantic Hardening

The JRA capture registry validator now proves the required database constraint behavior with rollback-only savepoint
probes rather than trusting CHECK text from `sqlite_master.sql`. It requires SQLite to reject zero and negative
versions, a non-integer version value, empty and non-text names, and duplicate names, while rolling back every probe
write. `PRAGMA table_list`, `table_info`, and `index_list` retain the exact structural checks, including `WITHOUT ROWID`.
A weaker registry whose SQL comment merely contains the approved CHECK text is rejected.

The validator still fails closed without registry/table repair or adoption. The review documentation now correctly
stops at the final approved review tip rather than prescribing an obsolete one-review-commit count. Fresh migration
verification passed 7 tests; the remaining dedicated, related, static, and full-suite checks are required before
publication.

## Phase 4C-2d3b1i6d1c2 JRA Trusted Live HTTPS Capture Implementation

Implemented the approved live JRA acquisition boundary on formal base
`93da236d319f686fd06842b46404b780e73dff72`. The new service accepts only a caller-declared supported page kind and
an already-resolved official accessS/accessU URL, canonicalizes the URL before any clock, network, or archive action,
then captures one complete raw HTTP entity and archives the immutable c1 value before returning it.

The private requests transport disables redirects, requires TLS verification, uses ten-second connect/read timeouts,
sets `Accept-Encoding: identity`, and configures no automatic retries. It accepts only 200 responses and absent or
identity Content-Encoding; it rejects noncanonical Content-Length, mismatched/oversized bodies, unsupported coding,
effective-URL disagreement, and incomplete transport failures while always closing the response. Raw streaming has
content decoding disabled and no text, CP932, UTF-8, or normalization round-trip occurs in the live layer. c1 remains
the sole owner of strict CP932 validation, raw SHA, and immutable capture identity.

The live service owns no pacing, discovery, field parsing, source normalization, database path, global migration,
NAR behavior, or NAR-to-JRA bridge. Status is `READY_FOR_REVIEW`; no formal integration, JRA result normalizer, race
history discovery, or bridge work has begun.

## Phase 4C-2d3b1i6d1d3 Historical Final-Odds Evidence Role Implementation

Implemented the approved provider-neutral final-odds evidence extension on formal base
`0135cee4ad8e578e6bd20940b16198a576172c04`. Only the c1a source-record and snapshot-provenance validators changed.
Past-race records now accept exactly the legacy two-role tuple or the complete lexical three-role tuple containing
`historical_race_final_odds`; all other role contracts and source payload structure remain unchanged.

The formal-base NAR-style two-role source payload and `his-v4` source ID are frozen as literal regressions, as is a
complete two-role snapshot digest. Final odds changes new source IDs and snapshot digests, while timestamp-only
changes remain excluded from c1a source identity. Same-response reuse across all three roles requires exactly equal
timestamps. Competing past-race records with the same result identity and differing final-odds evidence still raise
the existing conflict error.

The builder production module is unchanged. Regression coverage proves it propagates the third role to provenance,
accepts it when causally eligible, and rejects a late final-odds observation. No evidence-domain module, repository,
migration, NAR/JRA normalizer, capture module, package export, database, or fixture changed. Focused source,
snapshot, and builder verification passed 43 tests under Python 3.14.5 / pytest 8.3.5. Remaining related, full-suite,
and static verification is required before review publication.

Fresh implementation verification completed under Python 3.14.5 / pytest 8.3.5: dedicated changed-domain suites
passed 43 tests; the related source/snapshot/builder/NAR suite passed 67 tests; and the full suite passed 2555 tests.
Package-root export, forbidden dependency/source/AST, migration/global-version unchanged, repository unchanged, NAR
production unchanged, and `git diff --check` checks all passed. Status is `READY_FOR_REVIEW`; stop for independent
implementation review.

## Phase 4C-2d3b1i6d1d4a1 Request-Aware Historical Evidence Implementation Stop

Implemented the approved provider-neutral optional request fingerprint on formal base
`41f2298820fe029bc06f024ff6da028f21ed5c7c`, within the exact allowed production/test/migration files. The final
field on `HistoricalInputEvidenceReference` is `request_identity_sha256: str | None = None`; it preserves the legacy
five-argument positional constructor. Non-null values are strict lowercase SHA-256 and require a canonical HTTPS
endpoint. The neutral domain remains provider agnostic: no JRA method, `cname`, form, request-body, or accessO logic
was added.

Same-response coherence now uses `(canonical_source_url, request_identity_sha256, response_sha256)`. Legacy `None`
is omitted from canonical source/snapshot payloads, preserving the frozen formal-base two-role source payload,
`his-v4` source ID, and snapshot digest exactly. A non-null fingerprint is serialized for new evidence and changes
its source ID and snapshot digest; timestamps remain source-ID-independent. The builder was not modified and its
existing causality behavior still passes with propagated request-aware evidence.

Added global additive v014, `v014_historical_input_request_identity_schema`, which adds nullable strict SHA-256
`request_identity_sha256` to provenance evidence. It supports nonempty v013 stores without rebuilding, rewriting, or
deleting rows, and advances global migration order to `(8, 9, 10, 11, 12, 13, 14)`. The SQLite repository reads and
writes the field, preserves both NULL and non-null values, and fails closed on corrupt stored fingerprints. NAR and
existing JRA GET capture/live production remain unchanged; JRA accessO has not started.

Fresh focused verification passed 101 tests; current NAR historical-source and JRA capture/live regressions passed
47 tests. Package-export, provider-specific dependency, builder-unchanged, NAR-unchanged, JRA-GET-unchanged, and
`git diff --check` checks passed. The full suite collected 2561 tests: 2555 passed and six failed solely because
these out-of-scope tests still assert global migrations end at v013:

* `tests/test_nar_official_response_capture_migration.py` (1)
* `tests/test_simulation_bet_plan_migration.py` (3)
* `tests/test_sqlite_persisted_simulation_application.py` (2)

All six need their stale expected global migration registry extended with v014, but those files are not in the exact
allowed list. Per the stop condition, no out-of-scope edit, commit, or push was performed. The allowed-file worktree
is preserved unchanged pending an explicit scope extension.

## Phase 4C-2d3b1i6d1d4a1 Scope Extension and Final Verification

The approved scope extension added only three stale global-migration expectation tests. They now recognize the exact
approved registry `(8, 9, 10, 11, 12, 13, 14)` and v014's registered name; no production behavior changed after the
extension. The six formerly failing assertions passed. Fresh verification under Python 3.14.5 / pytest 8.3.5 passed:
focused d1d4a1 source/snapshot/builder/repository/migration tests 101; scope-extension tests 6; NAR historical-source
and existing JRA capture/live tests 47; complete migration-related suites 33; and the full suite 2561.

Package-root export, provider-specific dependency/source, builder-unchanged, NAR-unchanged, JRA-GET-capture-unchanged,
and `git diff --check` checks passed. The final allowed scope is exactly 17 files. Status is `READY_FOR_REVIEW`; one
review commit is authorized, with no JRA accessO capture, archive v002, live POST, normalizer, bridge, or acquisition
work started.

## Phase 4C-2d3b1i6d1d4b1 JRA Final-Odds Capture Domain and Archive v002 Implementation

Implemented the approved pure JRA accessO final-win-odds request/capture domain on formal base
`906628c5eb5f1639387b3625d494cf133bb27729`. The new frozen/slotted request locator accepts only the official POST
endpoint and validated raw canonical accessO CNAME grammar, derives the existing JRA race identity, and verifies the
exact SHA-256 request fingerprint over canonical POST/endpoint/form JSON. Existing race/horse identity and accessS/
accessU behavior remain unchanged.

Added separate final-odds supplied-response and v2 capture values. They preserve exact strict-CP932 bytes and actual
aware timestamps, expose no fabricated GET response URL, and produce `jra-capture-v2` identities from the approved
request-aware preimage. v1 GET capture constructors and `jra-capture-v1` IDs remain unchanged. FINAL_WIN_ODDS is
explicitly POST-only and cannot be accepted by the existing GET canonicalizer.

Added transaction-neutral dedicated migration v002 and registered it after v001. It validates v001 data before
rebuilding only the capture table, preserves body storage and legacy rows/IDs byte-for-byte, adds disjoint GET/v1 and
POST/v2 request-family constraints, and creates separate legacy/request-aware evidence indexes. The runner retains
sole transaction ownership. The repository now has family-specific final-odds save/load/exact-lookup methods while
the three legacy GET signatures and behavior remain unchanged. Cross-family ID loads return `None`; stored corruption
fails closed.

Focused domain/archive/migration tests and related live-GET, neutral evidence, NAR capture, and migration regressions
are required before publication. No live POST transport, real capture, JRA normalizer, NAR change, global migration,
or bridge work was performed. Status is `READY_FOR_REVIEW` pending full verification and independent review.

Fresh implementation verification under Python 3.14.5 / pytest 8.3.5 passed: four dedicated changed modules 24,
related JRA-live/neutral/NAR/migration regressions 94, and the full suite 2565. Package-root export and forbidden
dependency/source checks passed; the live capture module, NAR capture production, neutral request-evidence production,
and global v014 registry are unchanged. `git diff --check` passed. Status remains `READY_FOR_REVIEW`; no live POST,
real accessO capture, historical odds normalizer, formal integration, or bridge work has begun.

## Phase 4C-2d3b1i6d1d4b1 v001 Pre-Migration Schema Hardening

Hardened only the v002 pre-migration trust boundary. Before any capture-table rename, the migration now proves the
complete v001 response-body and capture table structures through `table_info`, `table_list`, `foreign_key_list`,
`index_list`, `index_info`, and `index_xinfo`: exact columns/types/PK/NOT-NULL shape, `WITHOUT ROWID`, the required
RESTRICT body foreign key, and the one unique non-partial three-column evidence index without expression keys.

Rollback-only SAVEPOINT probes additionally prove the live v001 DDL rejects representative malformed SHA/body/length
rows and invalid capture version, page kind, URL, foreign key, charset, HTTP status, content encoding/length, and
timestamp order. The migration requires FK enforcement to be active as well as validating the declared FK. Every
stored v001 capture still reconstructs through the legacy domain before mutation. Weakened schema cases now fail before
`ALTER TABLE`, leaving the original tables, index, data, and version-1 registry intact with no temporary table or v002
registration. The v002 target schema and all other b1 production behavior remain unchanged.

Fresh correction verification under Python 3.14.5 / pytest 8.3.5 passed: JRA migration tests 9, all four b1
dedicated modules 25, related JRA/NAR/neutral/migration regressions 94, and the full suite 2566. Package-root export,
forbidden dependency/source, unchanged-live-module, and `git diff --check` checks passed. The correction is
`READY_FOR_REVIEW`; no live POST, real capture, normalizer, formal integration, or bridge work has begun.

## Phase 4C-2d3b1i6d1d4b2 JRA Final-Odds Live POST Transport

Implemented only the approved live accessO POST transport on formal base
`d91063fade86cfcc19b7dbd05bad3ed6172fde58`. The existing accessS/accessU `capture_response` API and GET transport
call shape remain unchanged; `FINAL_WIN_ODDS` remains excluded from that GET path. The existing service now has the
separate `capture_final_win_odds_response` method, which requires an exact validated
`JRAOfficialFinalWinOddsRequestLocator` before clock, network, or archive work.

The private POST path uses exactly the locator endpoint and a one-field standard form body, preserving the raw CNAME
and encoding its slash as `%2F`. It explicitly prepares a cookie-free, referer-free, origin-free request rather than
depending on persistent session state. It retains `Accept-Encoding: identity`, form content type, disabled redirects,
TLS verification, zero retries, ten-second connect/read timeouts, and byte-only streaming with content decoding off.
HTTP status, effective endpoint, encoding, canonical Content-Length, 4 MiB limits, stream chunks, and all transport
errors fail closed while responses are closed on every path.

The service samples requested/observed/stored timestamps around one raw entity, builds only the existing v2
`JRAFinalWinOddsResponseCapture`, archives it through `save_final_win_odds_capture`, then returns its supplied
response. Strict CP932 remains capture-domain validation; an invalid domain object or failed archive produces no
return value. No real accessO call was performed. The archive/domain, migrations, neutral evidence, NAR production,
normalizers, discovery, and bridge remain unchanged. Initial dedicated verification passed 13 tests under Python
3.14.5 / pytest 8.3.5; related, full, and static verification remain required before publication.

Fresh review verification under Python 3.14.5 / pytest 8.3.5 passed: the dedicated POST/GET live module 13 tests,
the frozen b1 identity/capture/repository/migration modules 25 tests, and the neutral snapshot plus NAR capture
regressions 95 tests. The full suite passed 2570 tests. Package-root export, source/AST boundary, unchanged b1/NAR/
neutral production, global migration v014, and `git diff --check` verification remain part of the final review
handoff. Status remains `READY_FOR_REVIEW`; no formal integration or real accessO capture has occurred.

Final review static verification passed: the module has no package-root export, no new clock ownership, no forbidden
file/database/network-client dependencies outside its approved `requests` byte transport, and no NAR dependency. The
b1 capture-domain/archive/migration production files, NAR production, and provider-neutral evidence production are
unchanged; global migrations remain through v014. `git diff --check` is clean and the only changed files are the four
approved d1d4b2 files. The review branch is ready for independent review; formal remote remains at the approved base.

## Phase 4C-2d3b1i6d1d5a JRA Historical Past-Race Normalizer Implementation

Implemented the approved pure JRA normalizer on formal base
`dcdef4bd6559418fe7f179f42cd16a263604fc08`. The new provider module has only the three JRA-specific error types and
`normalize_jra_historical_past_race_source_record`. It consumes a validated JRA target track/entry pair plus exact
accessS/accessO supplied responses and returns one target-scoped c1a v4 `past_race`; it performs no HTTP, archive,
filesystem, database, clock, discovery, pagination, or bridge work.

The implementation validates target race/entry/horse coherence with existing public JRA identities, chooses the
historical stable horse only through the unique accessS row-local accessU anchor, and uses that row's historical horse
number only to join exactly one accessO `table.tanpuku` odds row. Both visible headers cross-check calendar date,
venue, meeting/day, race number, and heading with their formal provider identities. accessS supplies sixteen direct
facts; accessO `td.odds_tan` supplies the direct positive final-win odds. The explicit accessS corner labels, rather
than a fixed or final component, determine fourth-corner position.

The record has exactly context/accessS, final-odds/accessO, and result/accessS evidence roles. It preserves exact raw
SHA-256 semantics, request-aware accessO identity, no fabricated availability timestamp, supplied observations, and
source-ID timestamp independence. Synthetic strict-CP932 HTML is defined only in the dedicated test module; no
official fixture, archive row, or live accessO capture was created.

Fresh verification under Python 3.14.5 / pytest 8.3.5 passed: dedicated normalizer 8; JRA identity/capture/archive/
live regressions 38; neutral source/snapshot/builder regressions 47; NAR historical-source regressions 35; and full
suite 2578. Static boundary and unchanged-production verification remains required before review publication. Status
is `READY_FOR_REVIEW`; no formal integration, discovery/orchestration, target acquisition, Predictor connection, or
bridge work has begun.

Final static and scope verification passed: the module has no package-root export and no forbidden HTTP, archive,
database, filesystem, clock, randomness, or subprocess dependency. NAR production, JRA identity/capture/archive/live
production, and provider-neutral evidence/source/snapshot production are unchanged. Global migrations remain
`(8, 9, 10, 11, 12, 13, 14)` and JRA capture migrations remain `(1, 2)`. `git diff --check` is clean; the review
scope is exactly the four approved d1d5a files. The formal remote remains
`dcdef4bd6559418fe7f179f42cd16a263604fc08`; no real accessO capture was performed.

### Dead-heat fail-closed correction

The accessS result-row inspection confirmed that the official `着差` value is row-local `td.margin`. The normalizer
now inspects that direct display only for the exact official dead-heat marker `同着` and raises
`JRAHistoricalPastRaceSourceUnsupportedError` when present; it neither converts ordinary margin text nor adds a
margin field. A numeric finish consequently cannot bypass dead-heat handling. The result-table structural validator
also normalizes official presentational line breaks in fixed semantic headings (including `馬<br>番`, `負担<br>重量`,
`コーナー<br>通過順位`, `馬体重<br>（増減）`, and `単勝<br>人気`) without widening the required heading family.

Fresh verification under Python 3.14.5 / pytest 8.3.5 passed: dedicated normalizer 10; JRA identity/capture/archive/
live regressions 38; neutral source/snapshot/builder regressions 47; NAR historical-source regressions 35; and full
suite 2580. Package-root export, forbidden-dependency, unchanged JRA capture/NAR/neutral production, migration
version, and `git diff --check` checks passed. No official response was archived or persisted, and no real accessO
capture was performed.

## Phase 4C-2d3b1i6d1d5b3 JRA Complete-History Discovery Implementation

Implemented `scripts/simulation/jra_historical_past_race_discovery.py` as a pure single-response accessU discovery
boundary. Its public surface is the closed `JRAHistoricalEventKind`, immutable/slotted event-reference and discovery
values, the three discovery errors, and `discover_jra_historical_past_race_history`. It has no package-root export,
network, archive/repository, filesystem, database, clock, normalization, accessO locator, or Predictor ownership.

The implementation validates the exact JRA target track/entry race-entry-horse chain, exact accessU supplied response
and horse identity, strict CP932 bytes, and supplied observation against target scheduled start. It accepts only the
frozen accessU history table and headings. Every row becomes a JRA actual start through one row-local formal accessS
navigation, a retained non-JRA actual start, a proven non-start transfer/cancellation, or a retained unsupported actual
start; anything else fails closed. JRA identity is never invented from display text, and non-JRA/unsupported entries
carry no fabricated cross-provider identity.

The required response-local completeness proof validates the unique flat and obstacle aggregate cells, their exact
headings, canonical counts, independent finish arithmetic, and equality with every actual displayed event. A four-row
history against an aggregate of ten is rejected; non-JRA and unsupported actual starts count, while proven non-starts
do not. Continuation/lazy-load markers, duplicates, chronology violations, target/future rows, unknown structures, and
all count disagreement reject the whole discovery. Exact simultaneous history/aggregate no-data is the sole zero-
history path. The proof preserves provider information available at `observed_at` and never backdates delayed data.

Fresh verification under Python 3.14.5 / pytest 8.3.5 passed: dedicated discovery 8, related JRA/NAR/neutral
regressions 126, and the complete suite 2588. No real trusted response was fetched or archived; d1d5a, JRA
capture/domain/archive/live, NAR, provider-neutral source/snapshot, migrations, bridge, orchestration, and Predictor
remain unchanged.

### d1d5b3 strict non-start and unsupported accessS correction

The event classifier now recognizes `PROVEN_NON_START` only for the exact observed transfer rows `JRAへ転入` and
`JRAより転出`, including their no-navigation/no-start-facts shape. The unproven cancellation-style display values
`取消`, `取止`, and `除外` no longer remove a row from aggregate accounting: they fail closed, including when the row
also carries contradictory actual-start facts.

Every row-local parsable accessS navigation is now fully checked before the public event kind is chosen. This includes
unsupported starts: their CNAME calendar date must equal the accessU row date, and their private navigation metadata
participates in duplicate canonical accessS URL and JRA race-identity rejection. Unsupported public references remain
explicit and count toward completeness but expose no fabricated JRA result identity. Fresh verification passed:
dedicated discovery 9, related regressions 126, and the full suite 2589.

## Phase 4C-2d3b1i6d1d5c2 JRA accessS Final-Odds Locator Extraction Implementation

Implemented the approved pure accessS-to-accessO locator boundary on formal base
`d53d2df5c7f9aee91b9cbea0dda07145aefb3acf`, within exactly the approved identity/parser/test/documentation files. The
identity domain now exposes only the narrow public builder
`build_jra_final_win_odds_request_locator(*, cname: str)`. It fixes the existing official endpoint, derives the
formal race identity, and computes the existing private canonical request fingerprint; no fingerprint implementation
was copied into the HTML parser and all prior locator behavior remains unchanged.

The new pure extractor consumes exact `JRASuppliedOfficialResponse` accessS evidence, validates its formal result URL,
strictly decodes exact CP932 bytes, and accepts only the unique `オッズ` control in the official result-table-caption
`race_header` related-link path. Its direct raw source must be the approved single-quoted
`return doAction('/JRADB/accessO.html', '<raw-cname>');` spelling. The parser rejects generic page-menu controls,
hidden `commForm01` values, DOM-only HTML entity quote recovery, double quotes, escapes, concatenation, extra
arguments/script, endpoint changes, percent-encoded CNAMEs, malformed CNAMEs, duplicates, and race-identity
disagreement. It returns the existing locator only after its race identity equals the supplied accessS identity; it
never synthesizes CNAME material from any result identity or display fact.

Synthetic strict-CP932 tests cover the approved builder fingerprint, exact control, raw slash/uppercase tail,
input/family/URL/encoding failures, generic/hidden-form exclusion, JavaScript grammar, source-spelling/entity
rejection, identity mismatch, ambiguity, public surface, and purity. Fresh verification under Python 3.14.5 / pytest
8.3.5 passed: dedicated identity/locator suites 16, related JRA/NAR/neutral regression set 138, and full suite 2596.
No real accessO response was captured, archived, or posted; d1d5a, d1d5b3, JRA capture/archive/live, NAR,
provider-neutral production, migrations, orchestration, bridge, and Predictor remain unchanged. Status is
`READY_FOR_REVIEW` pending independent review.

### Raw selected-control binding correction

Corrected the source-spelling proof so it no longer counts decoded `onclick` text across the whole page. The extractor
now uses a quote-aware raw HTML token scan that skips comments and script bodies, aligns raw anchor start tags with
BeautifulSoup anchors in document order, identifies the exact selected result-header anchor, and validates only that
raw tag's literal lowercase `onclick` attribute. The raw value must equal the approved unescaped single-quoted
doAction spelling. Entity spellings `&#39;`, `&#x27;`, and `&apos;` remain invalid even if the DOM parser decodes them.

The new regression proves the defect against the previous review source in memory: a selected entity-encoded control
plus an unrelated comment containing the exact decoded raw `onclick` was accepted by the prior page-global count. It
is now rejected; an equivalent script-text decoy is rejected as well. The builder, fingerprint ownership, selector,
identity cross-check, raw CNAME policy, and all unrelated c2 boundaries remain unchanged.

Fresh correction verification under Python 3.14.5 / pytest 8.3.5 passed: dedicated identity/locator suites 17,
related JRA/NAR/neutral regressions 139, and the full suite 2597. Package-export, forbidden-dependency/source/AST,
identity-ownership, unchanged-production, version, and `git diff --check` validation remain required before review
publication.

## Phase 4C-2d3b1i6d1d5e1 JRA Historical Input-Source Collection Implementation

Implemented the approved pure injected collector in
`scripts/simulation/jra_historical_input_source_collection.py`. Its exact public surface is the two typed response
provider Protocols, frozen/slotted `JRAHistoricalSourceCollection`, its validation/unsupported error hierarchy, and
`collect_jra_historical_input_source_records`. No package-root export, network, live capture, archive, database,
clock, raw accessU parsing, snapshot construction, bridge, or Predictor integration was added.

The collector calls formal accessU discovery exactly once and uses its complete event order as the only history
sequence. It rejects discovered non-JRA and unsupported actual starts before either injected provider can run. Proven
non-starts emit no record. Empty and transfer-only zero-actual-start histories use only the formal public absence
projection, with zero result/odds provider calls and no second discovery.

For each JRA actual start, the collector binds an exact injected accessS response to the discovery URL and race
identity, extracts the formal accessO request locator from that exact response, binds the injected final-odds response
to that locator, and delegates to the existing JRA past-race normalizer. AccessS responses are reused only within a
call by canonical JRA race ID; final-odds responses are reused only within a call by request-fingerprint SHA-256.
Output remains newest-to-oldest with no history cap, and all-or-nothing collection prevents partial returns.

The collection result directly validates canonical JRA race/entry lineage through the existing identity parser and
entry-ID builder, including a positive canonical horse-number suffix. It additionally requires every source record to
be JRA/jra_official and exact-target bound. The collector invokes the existing neutral source-set validator exactly
once before constructing this result. It preserves response timestamps and rejects accessS/accessO observations later
than the target scheduled start. Formal discovery, locator, normalizer, absence-projection, and neutral-validation
errors translate to the approved collection boundaries; provider-raised exceptions propagate unchanged.

Fresh focused verification under Python 3.14.5 / pytest 8.3.5 passed: dedicated collector 7 and related JRA/NAR/
neutral regression set 142. Full-suite and final static validation are recorded with the review commit. No real
official response was captured, archived, or fetched; formal branch content remains unchanged.

### Collection-boundary regression correction

Strengthened the collector-only dedicated tests without changing production. The correction now exercises the real
accessS and accessO binding/cutoff helpers for wrong canonical result URL, valid-but-wrong JRA result identity, wrong
result and odds supplied-response types, a final-odds response for a different exact request locator, and a final-odds
observation after the target scheduled start. These paths fail closed as collection validation errors rather than being
tested through mocked binding helpers.

### 4C-2d3b1i6d1d5f1c1 — accessD capture v003 implementation

Implemented the isolated accessD identity/capture/archive prerequisite from formal
`776cd912…`. The v1 URL canonicalizer remains accessS/accessU-only; a separate
supplied-response recognizer admits canonical accessD. Schema-v3 target-card GET
captures use their own accessD identity path and cannot create v1 identities. The
archive/repository adds family-specific v3 APIs and migration v003 rebuilds only the
capture table while retaining the shared body table and both partial evidence indexes.
No live accessD acquisition, target parser, source records, snapshots, or bridge work
was performed.

### v003 pre-mutation validation correction

The initial v003 migration check was strengthened before review: it now reconstructs
every persisted v1 and v2 row against its frozen capture domain, verifies exact body
digest/length and canonical timestamps, and confirms each stored capture ID/page kind
before capture-table mutation. A malformed v002 row therefore fails before rebuild;
the body table remains read-only throughout v003 validation and migration.

### Exact v002 pre-mutation schema validation revision

v003 now verifies exact v002 body/capture columns, types, nullability, primary-key
shape, WITHOUT ROWID tables, foreign key actions, the complete two-index set, index
key order, partial predicates, and index xinfo key layout. SAVEPOINT probes prove the
approved v002 body and capture CHECK behavior; persisted rows are still reconstructed
and ID-verified before any table rename. Dedicated weakened-v002 regression cases
confirm rollback preserves the registered v002 tables and indexes with no temporary
table or v003 registry entry. Verification passed: migration 10, dedicated 42,
related 99, full suite 2626.

### Exact v002 DDL pinning correction

The v003 validator now normalizes and exactly compares the two approved v002 table
DDLs and both partial-index DDLs before any mutation. This independently detects
removed, weakened, or extra request identity/cname/method CHECKs even when family
constraints would mask a SAVEPOINT probe. PRAGMA checks, probes, body verification,
and v1/v2 reconstruction remain defense-in-depth. Regression variants cover removed
and weakened request identity/cname checks, removed request-method checks, and an
otherwise harmless extra CHECK, each pinned to rollback without a v003 registry row.
Verification remains migration 10, dedicated 42, related 99, full 2626.

The suite also pins locator extraction validation, past-race normalizer validation and unsupported translation,
absence-projection validation, neutral validation and conflict translation, and unchanged propagation of both result-
and final-odds-provider exceptions. A six-event JRA actual-start sequence confirms that the collector retains every
newest-to-oldest event and imposes no source-history cap. Existing one-discovery, zero-provider, direct-lineage,
mixed-history, deterministic-order, all-or-nothing, and purity coverage remains intact. Production, schema,
migrations, package exports, live capture, archive, database, bridge, and formal branch remain unchanged.


## Phase 4C-2d3b1i6d1d5f1c2 JRA accessD Live Capture Implementation

Implemented the dedicated schema-v3 accessD GET service method
`capture_target_race_card_response(*, response_url)` in the existing JRA live capture
service. It first uses the existing private v3 canonical accessD validation, so malformed,
raw-slash noncanonical, and accessS/accessU/accessO inputs are rejected before the
clock, transport, or archive are touched.

For valid canonical accessD, the method samples requested time, reuses the unchanged
GET transport, verifies the exact returned byte entity and URL, samples observed and
stored times, constructs `JRAOfficialTargetRaceCardResponseCapture`, saves through
`save_target_race_card_capture`, and then returns that exact capture. The v3 domain
continues to own strict CP932, headers, raw-byte SHA, and timestamp ordering. No caller
timestamp is accepted; live evidence retains only actual service clock observations.

The live suite now pins the public method signature, successful v3-only archive-before-
return flow, exact three-clock ordering, raw/canonical/family rejection before
collaborators, contradictory transport/domain/clock failures without archive writes, and
unchanged propagation of archive exceptions. It also retains the v1 accessD rejection
and v1/v2 success regressions, transport raw-stream/configuration tests, no
package-root export, and no real HTTP capture. No capture/archive/domain/repository/schema
or migration boundary was changed.


## Phase 4C-2d3b1i6d1d5f1c3 JRA accessD Target-Source Normalization Implementation

Implemented the pure supported-normal-runner accessD target-source boundary on formal
`3d15d31a68500d05b224ffead60ee9a799064342`. The new
`normalize_jra_target_race_input_source_records(*, response)` accepts only a canonical
supplied accessD response, strict-decodes its CP932 bytes, and cross-checks CNAME,
visible date/venue/meeting/day, race number, and scheduled start before creating a
frozen/slotted target collection.

One response produces exactly one track record and ordered entry, jockey, and direct
prediction-time odds records for every normal runner. Horse identity is only the unique
row-local accessU anchor; every entry identity is rebuilt from the formal accessD race
identity and official horse number. The result uses one role-specific raw-byte evidence
reference per neutral record, preserves actual observation time, rejects later-than-start
evidence, and calls the existing neutral source-record validator exactly once.

Missing, duplicate, malformed, or contradictory structural facts fail as validation;
only a unique, intelligible direct unsupported odds value fails as unsupported. No row
is treated as a proven non-runner, skipped, or returned partially. No schema, package
export, live capture, archive, snapshot, Predictor, or bridge work was added.

### Collection-invariant correction

`JRATargetRaceSourceCollection` now independently validates every member of its public
flat source-record tuple. Every record must be an exact neutral source record in the
JRA/`jra_official` family for the target track race; every three-record runner group is
the exact target entry object followed by same-entry jockey and odds records. The odds
horse number must equal its entry horse number. Direct construction now rejects foreign
organization/source/race records, unmatched items, and odds/entry disagreement before
returning a collection. The normalizer still performs its one and only neutral validator
call before that constructor boundary.


## Phase 4C-2d3b1i6d1d5f1c4a JRA accessU Target-Horse History Resolution

Implemented the narrow handoff from formal accessD target normalization to an exact,
causally bounded accessU horse-history response. Every target collection now retains a
frozen/slotted `JRATargetHorseHistoryLocator` alongside, but separate from, neutral
source records. Its canonical accessU URL comes only from the selected row-local accessD
anchor, is bound to the formal race/entry/horse identities, and is never synthesized
from a horse ID or recovered by a later raw-card parse.

The JRA capture repository now provides a family-specific latest accessU lookup with an
inclusive explicit observation cutoff. It searches only schema-v1 horse-profile captures
at the exact canonical URL, returns the unique latest eligible response, returns `None`
when none is eligible, and fails closed on tied latest captures or corrupt requested
storage. No schema, migration, index, or cross-family fallback was added.

`resolve_jra_target_horse_history_response(...)` is a pure injected response-binding
boundary. It validates exact target lineage and retained locator alignment, passes the
caller's exact `observed_at_not_after` to its provider once, and accepts only that exact
canonical accessU response before the explicit cutoff and target start. It supplies no
scheduled-start fallback, backdating, live HTTP, or synthetic zero-history evidence;
missing evidence is an explicit unavailable error and provider exceptions remain
unchanged.

Verification passed: target/resolver/repository dedicated tests 41 passed; related JRA
tests 121 passed; full suite 2666 passed; `git diff --check` passed. No real trusted
capture was performed.

### Regression-contract correction

The prior `124` label was not the exact related-suite command and is superseded. The
correction reran the exact related command:
`test_jra_historical_input_source_collection.py`,
`test_jra_historical_past_race_discovery.py`,
`test_jra_historical_past_race_absence_source.py`,
`test_jra_historical_past_race_source.py`,
`test_jra_final_win_odds_request_locator.py`,
`test_jra_official_identity.py`,
`test_jra_official_response_capture.py`,
`test_jra_official_response_capture_migration.py`,
`test_jra_official_response_live_capture.py`,
`test_historical_input_source_records.py`, and
`test_historical_input_snapshot_builder.py`: **121 passed**.

Test-only contract coverage now directly pins malformed/non-JRA track and entry lineage,
forged entry identity, locator race/entry/horse mismatch, non-exact locator/provider
types, accessS/accessD/accessO and wrong-horse/different-accessU response boundaries,
inclusive explicit bounds, provider call count, and no broad catch. Repository coverage
now directly pins exact URL/family rejection, no fallback to future or other accessU
navigation/horse evidence, same-time ambiguity, corrupt selected response body, and
corrupt selected schema-v1 request metadata. Target-locator coverage explicitly rejects
accessD/accessO/noncanonical/wrong-horse URLs and retains the URL only in aligned JRA
locator data, never neutral record values. No production files changed.

Fresh correction verification: dedicated target/resolver/repository suites **56 passed**;
the exact related command above **121 passed**; full pytest suite **2681 passed**.


## Phase 4C-2d3b1i6d1d5f1c4b JRA Historical Causal Archive Resolution

Implemented replay-causal accessS and accessO acquisition without changing the
historical discovery, response-capture schemas, indexes, live transport, or snapshot
boundary. `collect_jra_historical_input_source_records(...)` now receives one explicit,
inclusive, timezone-aware `observed_at_not_after` and passes that unchanged exact value
to every accessS and final-odds provider call. It rejects a bound later than the target
scheduled start and rechecks the supplied accessU, accessS, and accessO observations
against the explicit bound as well as the established outer start limit.

The collector still calls discovery once, rejects non-JRA/unsupported actual starts
before providers, uses the same deterministic result/odds caches, retains every actual
JRA start, and returns only after the existing neutral validator accepts the full set.
`None` from a required causal provider now raises the dedicated
`JRAHistoricalSourceCollectionUnavailableError`; provider errors, including archive
integrity errors, are deliberately propagated unchanged.

The repository adds only family-specific latest-before-cutoff methods for schema-v1
accessS and schema-v2 accessO. Both use stable exact requested identity and an inclusive
UTC cutoff, choose the sole latest eligible row, and reconstruct the selected row before
validating its full family/domain/request material. SQL does not filter family metadata
whose corruption must surface as `RepositoryDataIntegrityError`; tied latest rows and
selected metadata/body/request corruption therefore fail closed, while a genuine
no-result is `None`. No current/live fallback, backdating, synthetic odds/result, or
historical-start skip is possible in this boundary.

Verification after implementation: collector and repository dedicated tests **26
passed**; the JRA/accessU/discovery/past-race/final-odds/capture/source/snapshot related
selection **155 passed**. Full-suite and final static verification are recorded with the
review commit after they complete. No real trusted capture was performed.

Final verification: full pytest suite **2689 passed**. The collector public surface,
forbidden dependency, and broad-catch AST check passed; `git diff --check` passed.


## Phase 4C-2d3b1i6d1d5f1c4c0b1 JRA Target Navigation / Locator Discovery

Implemented the pure supplied-navigation chain from canonical strict-CP932 JRA root-menu
bytes to an exact canonical accessD target-card locator. The only identity addition is
`canonicalize_jra_race_card_href(...)`: it canonicalizes direct official relative or
canonical accessD href material to the fixed HTTPS host and uppercase `%2F` delimiter,
validates the existing accessD grammar, and preserves the observed site variant and opaque
tail exactly. It provides no external-race-ID URL or tail synthesis.

The new locator module owns frozen/slotted response and request domains, exact raw
meeting CNAME grammar, deterministic POST fingerprints, and the two pure navigation
discoveries. Root navigation is fixed to query-free `https://www.jra.go.jp/`, GET, and
strict `cp932`. Its one structurally bound quick-menu anchor must carry the literal raw
`doAction('/JRADB/accessD.html','<cname>');return false;` spelling. Entity recovery,
comments/scripts, arbitrary calls, escaped/concatenated JavaScript, and visible-text
binding cannot supply the request material. The meeting selection then yields one
race-selection locator only by exact canonical year/venue/meeting/day, never race text or
an inferred opaque tail.

The final discovery module strictly parses only the supplied race-selection response. It
requires the exact selection-table scope and two agreeing direct row anchors, canonicalizes
through the new identity helper, binds rows to the supplied navigation identity, retains
the raw-byte SHA-256 and actual observation time, and returns exactly one frozen target
locator. Absence is unavailable; malformed, duplicate, contradictory, or same-response
site-variant evidence fails validation. Multiple official accessD variants remain distinct
even when they map to the same external race ID.

Verification passed: dedicated identity/locator/discovery **23 passed**; related JRA
target-source, accessU, collector, final-odds, capture, and live-capture tests **95
passed** (**118 combined**); full pytest suite **2702 passed**. Static public-surface, forbidden dependency,
no-broad-catch, package-root export, changed-file scope, and `git diff --check` checks
passed. No archive, migration, HTTP/live capture, real official response fixture, or
trusted capture was added.


### Phase 4C-2d3b1i6d1d5f1c4c0b1 calendar-date binding correction

The accessD URL identity boundary now exposes the CNAME's validated `YYYYMMDD` through
`parse_jra_race_card_url_calendar_date(...)`. Both public accessD parsers reuse one
private resolution/grammar/date-validation path; `JRAExternalRaceIdentity` and canonical
external race IDs remain unchanged.

Final target-card discovery now reads the validated date from both direct row anchors and
requires exact equality with the race-selection request locator's `calendar_date` before
race-number matching. A valid same-race accessD URL dated one day differently fails as
validation. The public `JRATargetRaceCardDiscovery` constructor independently rechecks
the same locator/request invariant, preventing forged direct domain construction.

Fresh verification passed: dedicated c0b1 identity/locator/discovery tests **26 passed**;
related JRA target/accessD/accessU/accessS/accessO regressions **95 passed**; full suite
**2705 passed**. Site variants remain distinct, and no locator module, HTTP, archive,
database, migration, filesystem, clock, package export, or trusted-capture behavior was
changed.


## Phase 4C-2d3b1i6d1d5f1c4c0b2 JRA Target Race-Selection Capture v004

Implemented the durable schema-v4 JRA target-race-selection POST capture boundary from
the approved PREPARE. `JRATargetRaceSelectionResponseCapture` is frozen/slotted, accepts
only the formal c0b1 race-selection request locator, preserves strict CP932 bytes and
the established capture metadata/timestamp contract, fixes v4/`target_race_selection`/
POST, and reconstructs only `JRATargetRaceSelectionSuppliedOfficialResponse`.

Its `jra-capture-v4:` identity uses the established v2 POST canonical JSON convention:
fixed accessD endpoint, normalized observed instant, page kind, exact locator request
digest, POST, raw-body digest, and version 4. The raw CNAME is deliberately not a second
capture-ID component because the formal locator digest already binds it; it remains
persisted and is rebuilt through the formal locator builder during repository reads.

V004 is registered after v003 in the dedicated JRA capture migration runner. It first
pins exact v003 DDL/index/FK/`WITHOUT ROWID` structure, runs constraint probes, validates
all stored body digests, and reconstructs every v1/v2/v3 capture before mutation. It
then rebuilds only the unchanged 19-column capture table to admit the v4 page/family
branch, copies old fields byte-for-byte, preserves both existing partial unique indexes,
and reuses the untouched body table. No new column, table, index, global migration, or
legacy identity behavior was introduced.

The repository adds only family-specific v4 save, v4-ID load, and exact-evidence replay
methods. Exact evidence lookup uses endpoint/request digest/body digest/observed instant,
then reconstructs the full row and exact locator so corrupt metadata cannot turn into
false absence. There is no race-ID or latest-by-race retrieval, HTTP, clock, CNAME
synthesis, site-variant choice, or live fallback. Existing v1/v2/v3 loaders recognize a
valid v4 ID as foreign and return `None`; the inverse also holds.

The existing v1 live GET boundary remains unchanged and now has a regression proving it
rejects `TARGET_RACE_SELECTION` before clock, transport, or archive use. No v4 live
method and no real HTTP/trusted capture were added.

Verification passed: capture **7**, migration **12**, repository **12** (**31**
dedicated); c0b1 identity/locator/discovery plus live-capture regressions **42**; full
pytest suite **2711**. `git diff --check`, public-surface/family-separation, changed-file
scope, and no-live-production-change checks are recorded with the review commit.


## Phase 4C-2d3b1i6d1d5f1c4c0b3 JRA Live Target-Navigation Composition

Implemented the approved live composition exclusively in the existing JRA live capture
service. `capture_target_race_navigation(...)` first validates the supplied canonical
JRA external race ID, before any clock sample, root GET, POST, or archive interaction.
It then obtains the meeting-selection locator only from strict-CP932 root-menu bytes,
the race-selection locator only from strict-CP932 meeting response bytes, and never
synthesizes a CNAME, tail, site variant, or target-card URL from race identity.

All three navigation requests use explicit prepared requests: root is the fixed HTTPS
GET and both selections are exact one-field POSTs. Cookie, Referer, and Origin are
removed before sending, so neither a pre-seeded Session jar nor root/meeting Set-Cookie
can alter a formal navigation request. A cookie-dependent future site state fails closed
until its request-identity implications receive separate review.

The race-selection entity becomes the formal v4 capture with requested, observed, and
stored timestamps sampled in the frozen order. It is saved before discovery; only the
immutable saved capture's supplied-response conversion reaches target-card locator
discovery. `JRATargetRaceNavigationCaptureResult` is frozen/slotted and verifies that the
exact v4 capture matches discovery request-locator, response-digest, and observed-time
provenance while retaining only its capture ID. C0b3 deliberately stops at that locator:
it performs no target-card GET and changes no schema, migration, repository, or pure
discovery boundary.

Verification passed: focused live-capture **22 passed**; related
locator/discovery/capture/repository **33 passed**; full pytest suite **2717 passed**.
Static public-surface, no-broad-catch, no-package-export, no-new-module, changed-file
scope, and `git diff --check` checks are recorded with the review commit. No live HTTP,
read-only observation, or real trusted capture was performed.

### Cookie-isolation test correction

The navigation hidden-state regression now uses an actual populated `requests.Session`
cookie jar rather than synthetic Session headers. It seeds an applicable cookie before
the root request, deterministically adds root and meeting response cookie states before
the following formal POSTs, and proves all three outbound prepared requests still omit
Cookie, Referer, and Origin. A separate offline failure regression proves one cookie-free
send failure makes exactly one attempt and does not retry with hidden state. Production
code is unchanged from the prior review tip.


## Phase 4C-2d3b1i6d1d5f1c4c JRA Causal Target accessD Resolution

Implemented the pure injected c4c resolver from exact previously retained v4 navigation
provenance to one causally eligible v3 target-card supplied response. It validates the
canonical external race ID, exact v4 capture ID, aware `captured_at`, and provider
callability before either provider call. The v4 provider is called exactly once by the
retained ID; formal race-selection discovery is the only accessD URL source; and the v3
provider is called exactly once with that exact locator and
`observed_at_not_after=captured_at`.

Both capture families use only `observed_at <= captured_at` for replay causality.
`stored_at` remains audit/internal timestamp metadata, not a replay cutoff, selection key,
tie-break, or proof of durable save completion. The frozen/slotted result rechecks v4
request/digest/observation lineage and v3 exact URL/race/capture lineage before deriving
the retained IDs, response SHA, caller `captured_at`, and supplied target-card response.
Provider integrity and validation exceptions propagate; genuine absent v4/v3 evidence is
the dedicated unavailable condition.

The repository adds one exact-URL target-card latest-observation method. It accepts only
canonical accessD input and an inclusive aware `observed_at_not_after`, reconstructs
candidate rows without a `stored_at` filter, selects the greatest eligible observation,
and fails closed on same-time multiplicity or corrupted selected family/body metadata. No
schema, migration, index, capture-domain, live-capture, normalizer, snapshot, or package
export change was made.

Verification passed: resolver **14 passed**; repository **13 passed**; related target
locator/discovery/source/capture/live suite **74 passed**; full pytest suite **2733
passed**. `git diff --check` and the six-file/pure-boundary/no-`stored_at`-filter static
checks passed. No live HTTP or real trusted capture was performed.

## Phase 4C-2d3b1i6d1d5f1c4d0 JRA Race Replay Seed — implementation blocker

Implementation began only in the independent review workspace on
`review/4c-2d3b1i6d1d5f1c4d0-jra-race-replay-seed`; no commit or push was made.  The
required v015 migration registration makes the repository-wide migration runner report
version 15.  The existing `tests/test_simulation_migrations.py` hard-codes the registry
through v014, so it fails with the otherwise successful v015 migration solely because it
expects no v015 row.  That test is outside the phase's Allowed Files (which permits only
`tests/test_historical_input_snapshot_migration.py` for a registry adjustment).  Updating
the global registry expectation requires explicit scope authorization; leaving it
unchanged prevents the required full suite from passing.

Diagnostic command: `python -m pytest tests/test_simulation_migrations.py -q --tb=short`.
Result after correcting the local v015 DDL formatting: **1 failed, 21 passed**.  The sole
failure is `MigrationTests.test_apply_idempotent_and_utc_history`, whose expected mapping
ends at v014 but the actual registered mapping correctly includes
`15: v015_jra_race_replay_seed_schema`.  No live HTTP or trusted capture was performed.

### Approved scope expansion and full-suite stop condition

The approved one-file expansion updated `tests/test_simulation_migrations.py` without
weakening its exact registry assertion.  That regression now passes (**22 passed**).  The
corresponding permitted historical-migration registry expectations were updated in
`tests/test_historical_input_snapshot_migration.py`; the focused seed/migration run then
passed (**42 passed**), and the required related JRA/source stack passed (**92 passed**).

The subsequent full suite stopped at **6 failed, 2736 passed**.  Every failure is another
hard-coded pre-v015 global migration history assertion in a file that remains outside the
expanded Allowed Files:

- `tests/test_nar_official_response_capture_migration.py::CaptureMigrationTests::test_runner_creates_exact_dedicated_schema_and_no_global_tables`
- `tests/test_simulation_bet_plan_migration.py::SimulationBetPlanMigrationTests::test_fresh_database_applies_v008_and_v009_once`
- `tests/test_simulation_bet_plan_migration.py::SimulationBetPlanMigrationTests::test_v008_to_v009_upgrade_preserves_existing_rows`
- `tests/test_simulation_bet_plan_migration.py::SimulationBetPlanMigrationTests::test_v009_is_registered_after_v008_without_duplicate_version`
- `tests/test_sqlite_persisted_simulation_application.py::SQLitePersistedSimulationApplicationTests::test_file_backed_settled_run_preserves_caller_collections_and_persists_snapshot`
- `tests/test_sqlite_persisted_simulation_application.py::SQLitePersistedSimulationApplicationTests::test_pending_migrations_are_applied_for_empty_run_and_connection_closes`

Each expects the complete global registry to end at v014, while correct runner output now
also contains `15: v015_jra_race_replay_seed_schema`.  Under the explicit d0 stop
condition, no further changes, commit, or push were made.  No live HTTP or trusted capture
was performed.

### Second approved scope expansion — complete verification

The three newly approved global-registry test files were changed only to extend their
literal v8–v14 expectations with exact entry `15: v015_jra_race_replay_seed_schema`.
No assertion was weakened or made dynamic. The additional-registry command passed
**33 passed**, the existing simulation migration regression remained **22 passed**, the
seed/repository tests passed **7 passed**, the expanded migration coverage passed
**68 passed**, and the related JRA/source/snapshot stack passed **92 passed**. Full pytest
verification completed with **2742 passed**. No live HTTP or trusted capture was performed.

### D0 integrity correction

The correction makes prior d0 seed references the sole durable proof for reusing existing
JRA race and entry mappings. Bare pre-existing mappings and legacy race/horse-number
collisions now fail as integrity errors. Proven race reuse validates only stable legacy
identity fields, leaving weather, condition, and runner count revision-specific. Every
target source record is checked against the same exact v3 response before transaction
start; repeated child identity columns are validated during load; and a final transaction
safety boundary rolls back and rethrows any otherwise-unhandled post-begin exception.

V015 prerequisite validation now pins the v014 request-identity evidence column, v010
source/race/entry keys and foreign keys, horses membership key, and absence of unregistered
partial v015 objects. Verification passed: domain **29**, repository **33**, migration
**13**, related **92**, migration regressions **66**, and full suite **2808** tests. No
HTTP, capture-archive lookup, c4d implementation, or trusted capture was performed.

## Phase 4C-2d3b1i6d1d5f1c4d final PREPARE refresh

The formally integrated d0 seed closes both prerequisites recorded by the historical
c4d architecture reference. The final orchestrator accepts one exact
`JRARaceReplaySeed` plus five read-only evidence providers; decomposed dataset, race,
entry-map, time, URL, digest, and capture-ID caller fields are forbidden. Its public
result is the frozen/slotted pair of the exact seed object and the completed
`HistoricalInputSnapshot`, with no duplicated raw response bytes.

Existing archive and c4c contracts support exact replay without production changes.
C4d owns a private exact-v3-by-ID provider protocol and a private adapter to c4c's
locator/bound provider shape. The adapter validates c4c's URL, race, and bound against
the seed, loads only `seed.target_race_card_capture_id`, and requires exact capture ID,
response digest, canonical URL, race identity, and `observed_at <= seed.captured_at`.
It never invokes the generic latest-v3 lookup, so later archive enrichment cannot change
an existing seed's replay.

The c4c result must equal all seed v4/v3/URL/digest/time provenance before its supplied
accessD response is normalized. Normalized target entries and accessU locators must then
equal the seed's ordered entry identities exactly. Every accessU resolution and accessS/
accessO historical collection uses `seed.captured_at` as its observation bound. C4d
rechecks `captured_at <= information_cutoff <= scheduled_start_at`; `stored_at` has no
causal role.

The complete source union is all canonical target records followed by each entry's
complete historical records in seed order. It is built only after full entry coverage.
The snapshot entry mapping comes only from seed entries, and the existing snapshot
builder is called exactly once with the seed's dataset, internal race, times, complete
union, and mapping. C4d performs no database/archive write, snapshot persistence, HTTP,
live capture, current fallback, name matching, or legacy identity lookup.

The future implementation scope is only
`scripts/simulation/jra_race_historical_replay.py`, its new dedicated test module, and
the two phase documents. Required tests include the deferred restart/archive-enrichment
case proving exact v3 A remains selected after eligible B is added, exact seed/target
entry equality, causal bounds, complete deterministic union, exact seed mapping, error
translation, provider integrity propagation, and a single snapshot-builder call. No
pytest was run for this docs-only PREPARE; changed-file scope, status, and
`git diff --check` are verified before commit. No live HTTP or trusted capture was
performed.
