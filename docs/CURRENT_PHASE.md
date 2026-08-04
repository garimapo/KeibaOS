# Current Phase

## Status

WAITING_FOR_PHASE_INSTRUCTION

## Phase

Phase 4C-2d3b1i6a V3d — Historical input snapshot contract consolidation

## Base Commit

`430add64f96c52db8d8cf86f86ea08fd1b7caac0`

## Branch

`review/4c-2d3b1i6a-v3d-consolidation`

## Canonical Workspace

`C:\Users\garim\Desktop\KeibaAI-review-1i5b2b`

The original workspace, `C:\Users\garim\Desktop\KeibaAI`, is not a modification target.

## Review State

V3a status: `APPROVED`.

V3b status: `APPROVED`.

V3c status: `APPROVED`.

V3d status: `APPROVED`.

Overall 1i6a status: `APPROVED`.

Overall approval disposition: `APPROVED`.

## Objective

Consolidate V3a, V3b, and V3c into one authoritative implementation contract. Resolve precedence,
cross-contract semantics, natural identity, selection, save/load integrity, causal time order, digest, audit,
storage, and legacy-policy ambiguity before any historical-input implementation phase.

## V3d Scope

V3d establishes authoritative precedence; final identity/content/context/linkage classification; natural
identity and information-cutoff semantics; repository save/load and integrity validation rules; source/audit
semantics; a cross-contract consistency table; and the implementation-readiness gate.

V3d does not revise V3b's eight tables, columns, constraints, indexes, triggers, crosswalk, or runner-owned
transaction boundary. It does not implement a collector, provider, parser, repository, importer, backfill,
migration, or tests.

## Allowed Files

- `docs/CURRENT_PHASE.md`
- `docs/LATEST_CODEX_REPORT.md`
- `docs/VER0.8_SIMULATOR_DESIGN.md`

## Forbidden Files

- Production code, tests, and `README.md`.
- Migration modules, migration runner, V3b DDL/schema, and `scripts/database.py`.
- Database files, logs, CLI/settings, provider/parser/collector/repository implementation, package exports, and
  the original workspace.

## Required Verification

- Confirm the V3d precedence, natural identity, selection, and integrity rules resolve prior ambiguity.
- Confirm all cross-contract rows and all 20 implementation-readiness checks are `PASS` before publishing.
- Run `git diff --check`, `git diff --name-status`, and `git status --short`.

## Stop Condition

Publish only the V3d consolidation documents for review, then stop. Do not begin 1i6b1, provider/parser/
collector/repository work, migration work, database operations, or implementation.

## Blocker

None for Phase 4C-2d3b1i6a. Implementation authorization is `APPROVED_FOR_NEXT_PHASE`; the next candidate is
Phase 4C-2d3b1i6b1 — Historical input snapshot domain implementation. Integrate the approved V3 contract and
stop; do not begin Phase 4C-2d3b1i6b1 in this commit.
