# Current Phase

## Status

APPROVED_FOR_CODEX

## Phase

Phase 4C-2d3b1i6a — Historical input snapshot and audit persistence gap design

## Base Commit

`154c04de40cbae6898c0a8b3ff67eb3891da1456`

## Branch

`feature/ver0.8-simulator`

## Canonical Workspace

`C:\Users\garim\Desktop\KeibaAI-review-1i5b2b`

The original workspace, `C:\Users\garim\Desktop\KeibaAI`, is not a modification target.

## Objective

Finalize the design gap for historical prediction-input snapshots and their audit provenance. The design must define which race-level input records must be captured prospectively, how their source and timestamps are interpreted, how a historical snapshot is selected at an information cutoff, and which legacy records cannot be used as authoritative historical evidence.

This phase is design only. It does not add a persistence implementation, a repository, a migration, a request source, or a CLI feature.

## Approved Design Decisions

- An official historical prediction input is one complete, race-level snapshot with normalized child records and normalized audit rows; it is not a schemaless JSON blob.
- Every `InputAuditEntry` must contain at least one of `available_at` or `observed_at`. Missing both is invalid and fails closed.
- `available_at` means when the source made the exact information publicly usable. `observed_at` means when KeibaOS observed or stored that exact information. `captured_at` is the time the complete race-level snapshot was recorded. `finalized_at` belongs only to settlement data and is never prediction-input audit evidence.
- All future persisted audit timestamps are timezone-aware UTC ISO values. Unknown, invalid, or future-for-cutoff provenance fails closed.
- A historical source selection uses `race_id`, `information_cutoff`, input type, and source policy. It must select one complete snapshot whose header `captured_at` and every relevant non-null `available_at` and `observed_at` are no later than the cutoff. It must not mix components from different snapshots or fall back to later records.
- If more than one complete eligible snapshot exists, a future repository contract must select deterministically by latest `captured_at`, then stable `snapshot_id` descending.
- Legacy `races`, `horses`, and `past_races` do not have the required historical provenance and cannot be backfilled or treated as official historical prediction input. They may remain references or prospective capture sources only.
- Existing v008 odds batches preserve `observed_at`, completeness, source, and source URL, but not `available_at`. Until a later phase approves the authoritative observed-only odds policy, their missing `available_at` means they cannot be used for official historical odds validation. Legacy `horses.odds` has no auditable timestamp and cannot be used either.
- JRA and local-racing provider identities must be designed explicitly. Existing `horses.id` is a race-scoped race-entry identifier and `horse_no` is a local race number; neither is a provider external identity by itself.
- `source_id` must be a stable provider external identifier, canonical URL, or later-approved canonical content digest. It must never be based on `hash()`, row insertion order, or a random UUID.
- Settlement records (`race_results`, `race_result_entries`, `payout_publications`, and `payouts`) remain separate from prediction-input audit data.

## Future Follow-up Boundary

The follow-up sequence is intentionally split into separate reviewable phases:

1. Schema and domain design approval.
2. Migration.
3. Repository contracts.
4. SQLite repository implementation.
5. Request-source integration.

No part of that sequence is implemented in this phase.

## Completion Criteria

The following design items must all be explicit and internally consistent before this documentation-only
phase is `READY_FOR_REVIEW`:

1. Field-to-source and field-to-audit mapping for race metadata, entry, jockey, track, win odds, past
   race, and past-race absence evidence.
2. Canonical `available_at`, `observed_at`, `captured_at`, and `finalized_at` semantics.
3. Complete `InputAuditEntry` field, audit-key, source-ID, timestamp, and absence-evidence rules.
4. Deterministic cutoff selection and fail-closed behavior.
5. Legacy-data and no-backfill policy.
6. A single race-level normalized snapshot boundary.
7. Approved domain-value and Protocol API designs.
8. Approved SQLite table, natural-identity, constraint, index, and ordering designs.
9. Approved repository read/write, insert-only, idempotency, conflict, and transaction responsibilities.
10. Approved v008 observed-only odds and missing-`available_at` policy.
11. Approved JRA/NAR source and internal/external identity mapping.
12. Settlement separation, deterministic reconstruction, and a minimal follow-up phase split.

The revision in `docs/VER0.8_SIMULATOR_DESIGN.md` is authoritative for these criteria and supersedes the
earlier preliminary 1i6a notes.

## Final Contract Completion Criteria

The final revision additionally requires: one identity shared by domain equality and SQLite `UNIQUE`;
complete frozen-domain field/type/canonicalization contracts; a domain-to-column crosswalk; complete DDL
with types, nullability, keys, checks, indexes, and triggers; field-level time-source mapping; one-to-one
provenance/InputAuditEntry reconstruction; rejected-active-transaction writer semantics; exact read/tie-
break semantics; explicit completeness states; trusted-v008/digest/URL policy; JRA/NAR mapping; cutoff
fail-closed behavior; deterministic reconstruction; settlement separation; and the 1i6b1–1i6c split.

## Allowed Files

- `docs/CURRENT_PHASE.md`
- `docs/LATEST_CODEX_REPORT.md`
- `docs/VER0.8_SIMULATOR_DESIGN.md`

## Forbidden Files

- Production code.
- Tests.
- `README.md`.
- Migrations, schema, and `scripts/database.py`.
- `main.py`, CLI code, package exports, database files, and logs.
- The original workspace.

## Required Verification

- Inspect the existing simulator, request, audit, migration, repository, and design contracts read-only.
- Confirm the design distinguishes source availability from KeibaOS observation.
- Confirm the approved design excludes legacy unprovenanced records from official historical validation.
- Run `git diff --check`, `git diff --name-status`, and `git status --short`.

Pytest, migration execution, database access, runner execution, and CLI execution are not part of this documentation-only phase.

## Stop Condition

After the three allowed design documents are internally consistent, report the design as `READY_FOR_REVIEW` in `docs/LATEST_CODEX_REPORT.md` and stop without staging, committing, pushing, creating a branch, or beginning a follow-up phase.

## Blocker

none

## V2 Authority

The V2 section of `docs/VER0.8_SIMULATOR_DESIGN.md` supersedes all preliminary/final notes. Completion
requires the V2 identity, dataset-isolated read signature, executable DDL, non-impossible trigger policy,
canonical `+00:00` timestamps, zero-based ordering, logical provenance granularity, and prospective v008
attestation to be internally consistent.
