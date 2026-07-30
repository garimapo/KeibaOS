# Latest Codex Report

## Status

READY_FOR_REVIEW

## Current Phase

Phase 4C-2d3b1i5c — Persisted simulation request application, deterministic JSON CLI, and file-backed E2E

Base commit: `cd6f8e6f8e9024c33f3dc44d5f14486d5d77fdfb docs: approve persisted simulation race inputs`

Branch: `review/4c-2d3b1i5c-design`

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

blocker: none
