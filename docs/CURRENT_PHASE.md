# Current Phase

## Status

APPROVED_FOR_COMMIT

## Phase

Phase 4C-2d3b1i6b3a — Historical input snapshot SQLite repository atomic save path

## Base Commit

`95d8c8e123828935c8283109fef80b86b8a3eb88 feat: add historical input snapshot schema`

## Branch

`feature/ver0.8-simulator`

## Canonical Workspace

`C:\Users\garim\Desktop\KeibaAI-review-1i5b2b`

The original workspace, `C:\Users\garim\Desktop\KeibaAI`, is not a modification target.

## Objective

Implement only the atomic save side of the approved V3d concrete SQLite repository contract for an already
valid V3a `HistoricalInputSnapshot` and the committed V3b v010 schema. Phase 4C-2d3b1i6b3b, eligible latest
load and full reconstruction, is deferred and remains unimplemented.

## Completed Dependencies

- V3a domain/Protocols are committed at `c031008`.
- V3b eight-table schema, four indexes, five triggers, and v010 registration are committed at `95d8c8e`.
- Existing immutable SQLite snapshot repositories establish the connection-injected write convention.

## Allowed Files

- `scripts/simulation/repositories/sqlite_historical_input_snapshot_repository.py`
- `tests/test_sqlite_historical_input_snapshot_repository.py`
- `docs/CURRENT_PHASE.md`
- `docs/LATEST_CODEX_REPORT.md`

No other file is authorized. If another file is necessary, set `REVISION_REQUIRED` in the report and stop.

## Forbidden Files

- `scripts/migrations/versions/v010_historical_input_snapshot_schema.py`, `scripts/migrations/runner.py`,
  `scripts/database.py`, package `__init__.py` files, composition, services, CLI, README, and all unrelated
  production/tests.
- `database/keiba.db`, `logs/`, schema/bootstrap changes, package-root exports, and runtime Protocol checks.
- V3c collection/parsing/mapping, source-record digests, external-ID construction, legacy conversion,
  `past_races`/`horses.odds` use, fetch, backfill, or raw-input snapshot construction.
- b3b `load_latest_snapshot`, eligibility/latest queries, reconstruction, DB Decimal/date/datetime parsing,
  digest verification on load, and malformed-latest fallback logic.

## Concrete Repository API

Create exactly one concrete class in the allowed module:

```python
class SQLiteHistoricalInputSnapshotRepository:
    def __init__(self, *, connection: sqlite3.Connection) -> None: ...

    def save_snapshot(
        self,
        *,
        snapshot: HistoricalInputSnapshot,
    ) -> None: ...
```

The method matches `HistoricalInputSnapshotRepository.save_snapshot` structurally. Do not inherit from the
Protocol, implement load, add a load stub, add runtime-checkable behavior, or add public list/get/delete/
update/upsert APIs. The constructor is keyword-only, retains the exact injected connection, and enables/
verifies foreign keys. Invalid connection or caller snapshot is `RepositoryValidationError`.

## Natural Identity and Save Precedence

Exact natural identity is:

```text
(dataset_id, organization, source_system, external_race_id, captured_at_utc)
```

`content_sha256`, `information_cutoff_utc`, `internal_race_id`, and `source_url` are not identity.
`content_sha256` is derived by the V3a snapshot; the repository never accepts a separate caller digest.

1. No matching identity: insert one complete snapshot atomically.
2. Matching identity and same stored `content_sha256`: successful no-op; no header, child, or mapping mutation.
3. Matching identity and different digest: roll back and raise unchanged `RepositoryConflictError`.

The identity lookup reads only the minimum header values needed to find the identity and digest. Multiple
matching rows are `RepositoryDataIntegrityError`; full existing snapshot reconstruction/digest verification is
b3b responsibility.

## Transaction Boundary

Follow the existing connection-injected immutable SQLite convention:

- reject an active caller transaction before writing with `RepositoryValidationError`, without committing it;
- verify foreign keys, issue `BEGIN IMMEDIATE`, then perform the complete save;
- commit only after every row succeeds;
- on `sqlite3.IntegrityError`, roll back and raise `RepositoryDataIntegrityError` with the original exception
  chained;
- on `RepositoryConflictError` or other exception, roll back and propagate the same exception object;
- keep the connection usable after failure; do not use context-manager transaction magic or another connection.

The migration runner owns migration transactions; this repository never applies migrations, bootstraps legacy
parents, manages paths, retries, caches, or opens/closes the connection.

## Mapping and Insert Rules

Use deterministic parent-first insertion across all eight V3b tables:

1. `historical_input_source_identities`
2. `historical_input_external_races`
3. `historical_input_external_entries`
4. `historical_input_snapshots`
5. `historical_input_snapshot_races`
6. `historical_input_snapshot_entries`
7. `historical_input_snapshot_past_races`
8. `historical_input_snapshot_provenance`

Reuse only compatible existing source, external-race, and external-entry mappings. Incompatible existing
mapping fails closed under the repository error contract; never use `INSERT OR REPLACE` or mutate a mapping
to fit a new snapshot. Source identity is `(organization, source_system)` only; source URL is header content.
External-entry identity excludes `external_horse_id`, which is nullable entry content.

## Mapping Conflict Error Classification

`historical_input_source_identities` has no mapping payload beyond its natural identity
`(organization, source_system)`: an absent row is inserted and an existing exact row is reused. It has no
content-mismatch conflict case. An impossible stored state or unexpected SQLite integrity failure is
`RepositoryDataIntegrityError`.

For `historical_input_external_races`, a row with the same forward identity
`(organization, source_system, external_race_id)` but a different `internal_race_id` is an immutable forward
mapping conflict and raises `RepositoryConflictError`. A row with the same
`(organization, source_system, internal_race_id)` but a different `external_race_id` is an immutable reverse
mapping conflict and also raises `RepositoryConflictError`. Compatible exact mappings are reused.

For `historical_input_external_entries`, a row with the same forward identity
`(organization, source_system, external_race_id, external_entry_id)` but a different `internal_race_id` or
`race_entry_id` is an immutable forward mapping conflict and raises `RepositoryConflictError`. A row with the
same `(organization, source_system, internal_race_id, race_entry_id)` but a different `external_entry_id` is
an immutable reverse mapping conflict and also raises `RepositoryConflictError`. Compatible exact mappings are
reused.

All explicit immutable mapping conflicts are detected inside the repository-owned `BEGIN IMMEDIATE`
transaction, rolled back, and propagated unchanged without mutation or partial snapshot persistence.
`RepositoryDataIntegrityError` is reserved for unrelated storage integrity failures, including an
unidentified `sqlite3.IntegrityError`, missing or mismatched legacy parents, CHECK/FK/trigger failures,
impossible duplicate/stored states, or malformed values read by the repository. Caller/boundary failures
(invalid connection or snapshot, active caller transaction, or foreign-key enable/verification failure) are
`RepositoryValidationError`, not mapping conflicts.

Persist the exact V3a snapshot: canonical six-microsecond `+00:00` UTC text, canonical date, fixed Decimal
text (never float), header source URL, nullable external horse ID, exact entry order/past index, empty
`passing_order` as `''` not NULL, and each provenance timestamp/index/audit key. Do not infer/default,
reorder/reindex, synthesize `/none`, or partially persist children.

## Required Tests

The new dedicated real-SQLite test module must cover:

- class path/API/type hints; keyword-only constructor; invalid connection/snapshot;
  `RepositoryValidationError`; foreign-key enablement; no package-root export;
- successful complete save and expected rows in every V3b table; exact header/source URL/external horse ID;
  canonical UTC/date/Decimal text; empty passing order; entry/past/provenance ordering and nullable values;
- same identity/same digest no-op without duplicate headers/children/mappings; distinct digest conflict without
  mutation; cutoff/digest/source URL are not identity;
- active transaction rejection, `BEGIN IMMEDIATE` ownership, success commit, conflict rollback, child failure
  rollback/no partial rows, and reusable connection;
- source identity exact reuse; external-race forward and reverse mapping conflicts;
  external-entry forward and reverse mapping conflicts; each explicit immutable conflict as unchanged
  `RepositoryConflictError`; and mapping identity excluding source URL/external horse ID;
- a genuine unrelated SQLite/FK/storage integrity failure as `RepositoryDataIntegrityError`;
- source/AST boundaries: no load implementation, migration/schema modification, DB file, V3c logic, or
  package-root export.

Use real `:memory:` SQLite, explicit legacy `races` / `horses` parents, and the committed migration chain.

## Verification Commands

The implementation must run the dedicated suite, relevant v010/migration and existing immutable-repository
regressions, the full suite, `git diff --check`, and `git status --short`; exact commands and expected counts
must be recorded before stopping `READY_FOR_REVIEW`.

## Stop Condition

Implement only the allowed b3a files after a separate `EXECUTE_APPROVED_PHASE` command. Otherwise do not
create production/test code, stage, commit, or push. Stop for review at `READY_FOR_REVIEW`.
