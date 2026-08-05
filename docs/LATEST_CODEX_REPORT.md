# Latest Codex Report

## Status

READY_FOR_REVIEW

## Current Phase

Phase 4C-2d3b1i6b1 — Historical input snapshot domain implementation

Base commit: `0ab53e57adaf4971cd8c576024d90647a6d1bf09 docs: approve historical input snapshot v3 contract`

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

blocker: none
