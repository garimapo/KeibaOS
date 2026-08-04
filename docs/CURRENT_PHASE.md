# Current Phase

## Status

READY_FOR_REVIEW

## Phase

Phase 4C-2d3b1i6a — Historical input snapshot and audit persistence gap design

## Base Commit

`524e3d729f40611bfec857d5152cc64ee023a1ab`

## Branch

`review/4c-2d3b1i6a-v3c-source-policy`

## Canonical Workspace

`C:\Users\garim\Desktop\KeibaAI-review-1i5b2b`

The original workspace, `C:\Users\garim\Desktop\KeibaAI`, is not a modification target.

## Review State

V3a status: `APPROVED`.

V3b status: `APPROVED`.

V3c status: `READY_FOR_REVIEW`.

Overall 1i6a status: `REVISION_REQUIRED`.

Overall approval disposition: `NOT_APPROVED`.

The V3c revision has an exact 64-row, 11-column normative field-level matrix; six fixed record-kind digest
payload schemas; executable NAR official-host eligibility; and prediction-input-compatible past-race ordering
`(race_date DESC, source_id ASC)`, where index `0` is the newest applicable past race. V3c self-review is
23/23 PASS. This preserves V3a/V3b approval while V3c remains `READY_FOR_REVIEW` and V3d remains unstarted.

## Objective

Define the field-level official-source mapping, source-system and external-identity contracts, provenance-time
rules, and fail-closed eligibility policy for the V3a/V3b historical input snapshot. This V3c activity is
documentation only; it does not modify or execute production providers, parsers, migrations, DDL, databases,
or tests.

## V3c Scope

V3c fixes the source families `jra_official` and `nar_official`; organization and external race/entry identity
derivation; canonical source URL and source-record digest rules; `source_id`, `available_at`, `observed_at`,
and `captured_at` contracts; the field-level JRA/NAR mapping matrix; legacy-data eligibility; v008 odds
eligibility; and the JRA/NAR fail-closed support matrix.

V3c does not revise V3b's eight tables, columns, constraints, indexes, triggers, or runner-owned transaction
boundary. It does not decide a collector/provider/parser implementation, create an importer, or backfill
legacy values.

## Read-only Evidence

- `NARProvider` uses `https://www.keiba.go.jp/`, but has no approved observed-at, canonical source-record
  digest, or stable `source_id` capture boundary; log filenames use `abs(hash(url))` and are ineligible.
- `NARParser` currently sets `RaceMeeting.organization` to the generic display value `"地方"`; V3c forbids
  using that display value as historical identity.
- `JRAFetcher` is hard-coded sample data and is not official historical provenance.
- `HorseParser` converts odds through `float` and silently substitutes `0.0` on parse failure; it is not
  official historical WIN-odds evidence.
- Legacy `races`, `horses`, and `past_races` lack adequate historical provenance timestamps and source-record
  identity; they are linkage references only.
- Existing v008 odds rows are not collector-attested historical input and are untrusted for official history.

## Allowed Files

- `docs/CURRENT_PHASE.md`
- `docs/LATEST_CODEX_REPORT.md`
- `docs/VER0.8_SIMULATOR_DESIGN.md`

## Forbidden Files

- Production code, tests, and `README.md`.
- Migration modules, migration runner, V3b DDL/schema, and `scripts/database.py`.
- Database files, logs, CLI/settings, provider/parser implementation, package exports, and the original
  workspace.

## Required Verification

- Read the current provider, parser, legacy model/database, v008, migration-runner, and existing audit/input
  validation sources without network, database, runner, CLI, or test execution.
- Confirm a V3b approval record and no V3b schema revision.
- Confirm every V3a source-relevant scalar is represented in the V3c source matrix.
- Confirm the V3c self-review items are `PASS` before publishing.
- Run `git diff --check`, `git diff --name-status`, and `git status --short`.

## Stop Condition

Publish only the V3c source mapping and policy documents for review, then stop. Do not begin V3d, 1i6b1,
provider/parser/collector work, migration work, or database operations.

## Blocker

V3c review and V3d consolidation remain incomplete.
