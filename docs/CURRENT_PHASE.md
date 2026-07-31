# Current Phase

## Status

READY_FOR_REVIEW

## Phase

Phase 4C-2d3b1i6a — Historical input snapshot and audit persistence gap design

## Base Commit

`052a5c6e76a0f5bb0634be074bc1089bd81da663`

## Branch

`review/4c-2d3b1i6a-v3b-ddl`

## Canonical Workspace

`C:\Users\garim\Desktop\KeibaAI-review-1i5b2b`

The original workspace, `C:\Users\garim\Desktop\KeibaAI`, is not a modification target.

## Review State

V3a status: `APPROVED`.

V3b status: `READY_FOR_REVIEW`.

Overall 1i6a status: `REVISION_REQUIRED`.

Overall approval disposition: `NOT_APPROVED`.

## Objective

Define a complete executable SQLite DDL design and domain-to-column crosswalk that can persist every V3a
domain value without loss. This V3b activity is documentation only. It does not create, register, execute,
or test a production migration.

## V3b Scope

V3b fixes the exact eight-table set, all `CREATE TABLE`, `CREATE INDEX`, and approved `CREATE TRIGGER`
statements, SQL types/nullability/defaults/keys/FKs/checks, query indexes, SQL-owned versus
repository/domain-owned invariants, and the future migration ordering/atomicity contract. The authoritative
V3b detail is in `docs/VER0.8_SIMULATOR_DESIGN.md`.

The planned, but uncreated and unregistered, migration is
`v010_historical_input_snapshot_schema`. Its future runner contract verifies `PRAGMA foreign_keys = ON`,
uses one `BEGIN IMMEDIATE` transaction, succeeds atomically or rolls back atomically, and performs no
legacy-data backfill. No database file is accessed during this design phase.

V3b does not decide provider field/source mapping, source-ID formats, JRA/local organization policy, v008
odds eligibility/import policy, collector behavior, repository Python behavior, or request-source behavior.
Those are V3c or later responsibilities.

## Existing-schema observations

- `races.id` is `INTEGER PRIMARY KEY`.
- `horses.id` is `INTEGER PRIMARY KEY` and `horses.race_id` is the legacy internal-race linkage.
- Legacy tables do not declare every foreign key required by historical snapshots.
- The existing migration runner verifies foreign-key activation and applies each registered migration inside
  `BEGIN IMMEDIATE` with rollback on error. Existing SQLite repositories also require a clean caller
  transaction before their own `BEGIN IMMEDIATE` writes.

## Allowed Files

- `docs/CURRENT_PHASE.md`
- `docs/LATEST_CODEX_REPORT.md`
- `docs/VER0.8_SIMULATOR_DESIGN.md`

## Forbidden Files

- Production code, tests, and `README.md`.
- Migration files, migration registration, schema execution, and `scripts/database.py`.
- Database files, logs, package exports, `main.py`, and CLI code.
- The original workspace.

## Required Verification

- Inspect existing legacy schema, migration-runner, and repository conventions read-only.
- Confirm the DDL has exactly eight historical-input tables and a complete V3a field crosswalk.
- Confirm all V3b self-review items are `PASS`.
- Run `git diff --check`, `git diff --name-status`, and `git status --short`.

Pytest, database access, migration execution, runner execution, and CLI execution are out of scope.

## Stop Condition

Publish only the V3b DDL design documents for review, then stop. Do not begin V3c, V3d, 1i6b1, a
production migration, or any database operation.

## Blocker

V3b review, V3c source mapping/policy, and V3d consolidation remain incomplete.
