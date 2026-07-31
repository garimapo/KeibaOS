# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase

Phase 4C-2d3b1i6a — Historical input snapshot and audit persistence gap design

## Base Commit

`154c04de40cbae6898c0a8b3ff67eb3891da1456`

## Branch

`feature/ver0.8-simulator`

## Canonical Workspace

`C:\Users\garim\Desktop\KeibaAI-review-1i5b2b`

The original workspace, `C:\Users\garim\Desktop\KeibaAI`, is not a modification target.

## Review State

Overall 1i6a status: `REVISION_REQUIRED`.

Approval disposition: `NOT_APPROVED`.

V3a domain, identity, digest, and Protocol revision status: `READY_FOR_REVIEW`. This is a reviewable
sub-contract only; it does not approve the overall 1i6a design or authorize production work.

## Objective

Define the missing historical prediction-input snapshot boundary, including its prospective provenance,
identity, canonical content digest, and future read/write Protocol surface. This remains design-only.
It does not create a domain module, migration, repository, request source, database, or CLI feature.

## V3a Scope

V3a is limited to the nine frozen domain dataclasses, their immutable validation/canonicalization contract,
the schema-version-1 canonical content payload and SHA-256 digest, and the exact Source and Repository
Protocol signatures. The authoritative V3a detail is in `docs/VER0.8_SIMULATOR_DESIGN.md`.

V3b executable DDL, V3c source mapping and observed-only policy, and V3d consolidation remain incomplete.
No wording in V3a resolves those later responsibilities.

## Allowed Files

- `docs/CURRENT_PHASE.md`
- `docs/LATEST_CODEX_REPORT.md`
- `docs/VER0.8_SIMULATOR_DESIGN.md`

## Forbidden Files

- Production code and tests.
- `README.md`.
- Migrations, schema, and `scripts/database.py`.
- `main.py`, CLI code, package exports, database files, and logs.
- The original workspace.

## Required Verification

- Read the existing design and historical-input boundaries without executing runtime code.
- Confirm that the three allowed documents agree on the unapproved overall state and V3a review state.
- Run `git diff --check`, `git diff --name-status`, and `git status --short`.

Pytest, database access, migration execution, runner execution, and CLI execution are out of scope.

## Stop Condition

Publish only the revised V3a design documents for review, then stop. Do not begin V3b, V3c, V3d,
1i6b1, or any production implementation.

## Blocker

V3a domain contracts remain under review; V3b executable DDL, V3c source mapping/policy, and V3d consolidation are incomplete.
