# Current Phase

Status: `APPROVED_FOR_COMMIT`

## Identity and authority

- Phase: `POST_V0_8_DAILY_REPLAY_20`
- Name: `NAR Daily Target Evidence Durable Archive Implementation`
- Phase type: `IMPLEMENTATION`
- Base Commit: `ed09365df9b77505a2b36a3ad13b2c54efb30bd7`
- Branch: `feature/post-v0.8-daily-replay`
- Outcome: `IMPLEMENTABLE`
- Production/tests/migration implementation: `COMPLETED_WITHIN_ALLOWED_FILES`
- Stage/commit/push: `NOT_AUTHORIZED`

AGENTS.md, the committed Phase 6 and Phase 18 capture domains, and the committed
Phase 19 `DURABLE_ARCHIVE_REQUIRED` decision are authority. Existing NAR/JRA capture
archive repositories and their isolated migration runners are read-only implementation
precedents. Phase 20 does not change their contracts or register anything in the main
KeibaOS migration sequence.

## Objective and scope

Implement, only after a later `EXECUTE_APPROVED_PHASE`, one separate SQLite daily-target
evidence archive capable of losslessly storing and exactly loading:

1. `NARMonthlyConveneInfoBootstrapSupplierCapture` values for official homepage,
   Monthly root and locator JavaScript evidence; and
2. `NARHistoricalDailyTargetResponseCapture` values for MonthlyConveneInfo and RaceList
   evidence.

This phase owns only the isolated archive schema/migration and its connection-injected
repository. It does not acquire evidence, assemble bootstrap aggregate evidence, build a
target set, resolve prediction/settlement evidence, write a replay manifest, run replay,
or persist daily results.

The database file is a dedicated NAR daily-target evidence archive. It is not the main
KeibaOS database, the closed NAR settlement official-response archive, or any JRA
archive. A first migration must reject a connection containing unrelated application
tables or another archive registry rather than silently co-locating this schema.

## Existing authority and reuse

- `NARMonthlyConveneInfoBootstrapSupplierCapture` remains the final authority for every
  bootstrap capture field, response digest and deterministic capture ID.
- `NARMonthlyConveneInfoBootstrapEvidence` remains a deterministic three-capture
  projection. It is reconstructed by a later caller from three exact loaded captures;
  it is not persisted as a redundant row.
- `NARHistoricalDailyTargetRequestIdentity` and
  `NARHistoricalDailyTargetResponseCapture` remain the final authorities for the daily
  request/capture fields and derived identities.
- `NARHistoricalDailyTargetCaptureSource` and
  `NARHistoricalDailyTargetCaptureArchive` remain unchanged. The concrete repository
  satisfies their existing `load_capture`/`save_capture` contract.
- Existing `RepositoryValidationError`, `RepositoryConflictError` and
  `RepositoryDataIntegrityError` are reused. No archive-specific exception hierarchy is
  added.
- The existing NAR settlement repository/schema is neither imported as storage nor
  widened. Its page-kind enum, URL identity and capture IDs remain closed and untouched.

No new supplier Protocol is justified in this phase: the concrete repository's typed
`save_supplier_capture` and `load_supplier_capture` methods are the minimum archive API.
A future acquisition composition phase may propose a Protocol only when an actual
consumer requires dependency inversion.

## Public production API

### `scripts/simulation/nar_daily_target_evidence_archive_migration.py`

The module owns the isolated v1 DDL and explicit runner in one minimal file:

```python
VERSION = 1
NAME = "v001_nar_daily_target_evidence_archive_schema"

def apply(connection: sqlite3.Connection) -> None: ...

def get_applied_nar_daily_target_evidence_archive_schema_versions(
    connection: sqlite3.Connection,
) -> dict[int, str]: ...

def get_pending_nar_daily_target_evidence_archive_migrations(
    connection: sqlite3.Connection,
) -> tuple[object, ...]: ...

def apply_nar_daily_target_evidence_archive_migrations(
    connection: sqlite3.Connection,
) -> None: ...

def require_nar_daily_target_evidence_archive_schema(
    connection: sqlite3.Connection,
) -> None: ...
```

`apply` is transaction-neutral and creates the v1 domain tables/indexes only. The
explicit runner alone creates/validates the registry, owns `BEGIN IMMEDIATE`, applies
pending versions and commits or rolls back. `require_..._schema` is read-only and
validates registry rows plus exact table, column, index and foreign-key fingerprints.

### `scripts/simulation/sqlite_nar_daily_target_evidence_archive.py`

```python
class SQLiteNARDailyTargetEvidenceArchive:
    def __init__(self, *, connection: sqlite3.Connection) -> None: ...

    def save_supplier_capture(
        self,
        *,
        capture: NARMonthlyConveneInfoBootstrapSupplierCapture,
    ) -> None: ...

    def load_supplier_capture(
        self,
        *,
        capture_id: str,
    ) -> NARMonthlyConveneInfoBootstrapSupplierCapture | None: ...

    def save_capture(
        self,
        *,
        capture: NARHistoricalDailyTargetResponseCapture,
    ) -> None: ...

    def load_capture(
        self,
        *,
        capture_id: str,
    ) -> NARHistoricalDailyTargetResponseCapture | None: ...
```

Construction accepts an exact injected `sqlite3.Connection`, rejects an active caller
transaction, enables/verifies foreign keys and calls only the read-only schema verifier.
It never creates/applies/repairs schema. Callers must explicitly run the migration owner
before constructing the repository. The four methods are the complete initial API: no
list, latest, range, delete, update, repair, fallback or aggregate-evidence method exists.

## Schema version 1

All capture records are typed and separate. The one shared body table stores only
content-addressed raw bytes and does not collapse the two domain metadata contracts.
Every response body is a SQLite BLOB. No JSON, repr or pickle is used as storage
authority.

### Registry

`nar_daily_target_evidence_archive_schema_migrations`

| column | contract |
| --- | --- |
| `version` | `INTEGER PRIMARY KEY`, exact positive integer |
| `name` | `TEXT NOT NULL UNIQUE`, exact non-empty migration name |

Only `(1, "v001_nar_daily_target_evidence_archive_schema")` is valid initially.
Unknown versions, a mismatched name, malformed registry DDL/columns, unregistered domain
tables, or unrelated application/archive tables fail closed. The runner is not added to
`scripts.migrations.runner.MIGRATIONS` or either existing official-response archive.

### Exact response bodies

`nar_daily_target_evidence_bodies`

| column | contract |
| --- | --- |
| `response_sha256` | lowercase 64-hex `TEXT PRIMARY KEY` |
| `response_body` | non-empty `BLOB NOT NULL` |
| `byte_length` | positive exact `INTEGER NOT NULL`, equal to SQLite `length(response_body)` |

The table is `WITHOUT ROWID`. One digest maps to exactly one byte string. A missing body
referenced by metadata is corruption and save must not recreate it as a repair.

### Bootstrap supplier captures

`nar_daily_target_supplier_captures`

| column | SQLite contract |
| --- | --- |
| `capture_id` | `TEXT PRIMARY KEY`; exact `nar-monthly-bootstrap-capture-v1:` plus 64 lowercase hex |
| `schema_version` | `INTEGER NOT NULL`, exactly `1` |
| `page_kind` | `TEXT NOT NULL`; `official_home`, `monthly_root`, or `locator_script` |
| `canonical_request_url` | exact non-empty `TEXT NOT NULL` |
| `effective_url` | exact non-empty `TEXT NOT NULL` |
| `response_sha256` | lowercase 64-hex `TEXT NOT NULL`, restrictive FK to body table |
| `charset` | `TEXT NOT NULL`, exactly `utf-8` |
| `requested_at_utc` | canonical UTC-microsecond `TEXT NOT NULL` |
| `observed_at_utc` | canonical UTC-microsecond `TEXT NOT NULL` |
| `stored_at_utc` | canonical UTC-microsecond `TEXT NOT NULL` |
| `http_status` | exact integer `200` |
| `content_type` | exact non-empty `TEXT NOT NULL` |
| `content_encoding` | nullable `TEXT`; only `identity` when non-null |
| `content_length` | nullable non-negative `INTEGER` |

The table is `WITHOUT ROWID`; timestamps must satisfy
`requested_at_utc <= observed_at_utc <= stored_at_utc`. The unique evidence constraint is
`(page_kind, canonical_request_url, response_sha256, observed_at_utc)`. The domain owns
the exact URL/content-type relation and verifies `effective_url`, UTF-8, body length,
digest, timestamp order and capture ID again on load. HTTP date, ETag and Last-Modified
are not fields of this existing domain and are not invented by storage.

### Monthly/RaceList response captures

`nar_daily_target_response_captures`

| column | SQLite contract |
| --- | --- |
| `capture_id` | `TEXT PRIMARY KEY`; exact `nar-daily-target-capture-v1:` plus 64 lowercase hex |
| `schema_version` | `INTEGER NOT NULL`, exactly `1` |
| `page_kind` | `TEXT NOT NULL`; `monthly_convene_info` or `race_list` |
| `request_schema_version` | `INTEGER NOT NULL`, exactly `1` |
| `request_identity` | `TEXT NOT NULL`; exact `nar-daily-target-request-v1:` plus the stored request digest |
| `request_identity_sha256` | lowercase 64-hex `TEXT NOT NULL` |
| `request_method` | `TEXT NOT NULL`, exactly `GET` |
| `request_official_origin` | `TEXT NOT NULL`, exactly `https://www.keiba.go.jp` |
| `official_supplied_request_material` | non-empty exact `BLOB NOT NULL` |
| `resolved_request_url` | exact non-empty `TEXT NOT NULL` |
| `supplier_evidence_identity` | exact non-empty `TEXT NOT NULL` |
| `request_target_date` | nullable canonical `YYYY-MM-DD` `TEXT` |
| `request_baba_code` | nullable exact non-empty `TEXT` |
| `request_target_year` | `INTEGER NOT NULL`, 1 through 9999 |
| `request_target_month` | `INTEGER NOT NULL`, 1 through 12 |
| `response_sha256` | lowercase 64-hex `TEXT NOT NULL`, restrictive FK to body table |
| `charset` | `TEXT NOT NULL`, exactly `utf-8` |
| `requested_at_utc` | canonical UTC-microsecond `TEXT NOT NULL` |
| `observed_at_utc` | canonical UTC-microsecond `TEXT NOT NULL` |
| `stored_at_utc` | canonical UTC-microsecond `TEXT NOT NULL` |
| `http_status` | exact integer `200` |
| `content_type` | nullable `TEXT` |
| `content_encoding` | nullable `TEXT`; only `identity` when non-null |
| `http_date` | nullable exact `TEXT` |
| `etag` | nullable exact `TEXT` |
| `last_modified` | nullable exact `TEXT` |
| `content_length` | nullable non-negative `INTEGER` |

The table is `WITHOUT ROWID`; timestamps have the same exact order check. For Monthly,
`request_target_date` and `request_baba_code` are both null; for RaceList, both are
non-null. The unique evidence constraint is
`(request_identity_sha256, response_sha256, observed_at_utc)`. There is deliberately no
FK from `supplier_evidence_identity`: Monthly refers to the deterministic three-capture
aggregate identity while RaceList can refer to its exact Monthly source evidence. Their
meaning is reconstructed and validated by the existing request domain, not guessed by
SQLite.

The migration creates exactly the registry, these three domain tables and the two named
unique indexes:

- `ux_nar_daily_target_supplier_captures_evidence`
- `ux_nar_daily_target_response_captures_evidence`

No other first-version index, trigger, view or table is justified. Exact ID lookup uses
the primary keys; the unique indexes are concurrency/integrity defences for deterministic
evidence identities, not latest-selection APIs.

## Timestamp and serialization boundary

Every aware datetime is normalized to UTC and stored as exactly 32-character ISO 8601
text with microseconds and `+00:00`, e.g.
`2026-09-08T12:34:56.123456+00:00`. Load accepts only that canonical form. No filesystem
timestamp, SQLite clock, current clock, target date or inferred availability may fill a
timestamp. Original instants are preserved; provider display offsets are not separately
persisted because both existing domains normalize their datetime fields to UTC.

`None` remains SQL NULL for every nullable metadata field. Empty strings, whitespace
rewrites and value trimming are forbidden. `official_supplied_request_material` and both
response bodies remain byte-exact BLOBs, including CRLF, trailing whitespace and
space-before-tab bytes.

## Save, transaction and conflict semantics

Each public save validates exact type, capture ID pattern and response digest before
opening a transaction. It rejects a caller-owned transaction, enables/verifies foreign
keys, executes one `BEGIN IMMEDIATE`, and atomically handles one capture plus its body.
It commits on success and rolls back the complete operation on every exception.

- A new capture identity inserts one immutable typed metadata row and ensures the exact
  body row.
- The same identity reconstructed as the exact same complete domain value is an
  idempotent success/no-op.
- The same identity with any different body, request material, URL, timestamp, metadata
  or derived field raises `RepositoryConflictError`.
- A digest associated with different bytes raises `RepositoryConflictError` after stored
  integrity has first been proved.
- A distinct capture ID colliding with an existing deterministic evidence tuple, or any
  duplicate/corrupt persisted identity, raises `RepositoryDataIntegrityError`.
- `INSERT OR REPLACE`, UPSERT update, UPDATE, DELETE, delete/reinsert, repair and
  latest-wins are forbidden.

One save is one transaction. A future acquisition flow may save homepage, root, script,
Monthly and RaceList captures independently. Correctly committed captures remain honest
audit records if a later capture fails. The archive exposes no operation that interprets
those partial rows as a successful bootstrap, complete day or zero day.

## Exact load and integrity semantics

`load_supplier_capture` and `load_capture` accept only the exact family-specific capture
ID and perform one exact-key load. A valid absent ID returns `None`, matching the existing
daily-target capture Protocol. No other row is considered.

For a present row the repository:

1. requires exactly one typed metadata row and one referenced body row;
2. verifies BLOB type, byte length and SHA-256 before domain construction;
3. parses only canonical UTC-microsecond timestamps and preserves every nullable value;
4. reconstructs the existing request identity where applicable;
5. reconstructs the exact existing capture domain object, thereby re-running UTF-8,
   URL, enum/page-kind, timestamp, content-length and causal validation;
6. recomputes and compares request identity/digest, response digest, capture ID, derived
   request date/baba/year/month and every stored field; and
7. requires the deterministic evidence tuple to identify only that capture.

A malformed timestamp, invalid enum/page kind, bad UTF-8, truncated/missing body, digest
mismatch, ID mismatch, request/domain disagreement, invalid nullable metadata or schema
drift raises `RepositoryDataIntegrityError`. Corruption is never returned as `None`,
repaired, skipped, or followed by fallback to another capture.

Load paths execute SELECT/read-only PRAGMA operations only. They do not begin a write
transaction, apply migration, update access metadata, use the clock or access a network.
The same class works with a caller-opened SQLite URI `mode=ro` connection for exact loads.

## Failure taxonomy

- Wrong caller type, invalid capture-ID syntax, unusable connection or active caller
  transaction: `RepositoryValidationError`.
- Existing immutable identity with different valid supplied content:
  `RepositoryConflictError`.
- Missing/incompatible archive schema, malformed registry, SQLite constraint/storage
  failure, corrupt persisted row/body, duplicate deterministic evidence or reconstructed
  domain disagreement: `RepositoryDataIntegrityError` at repository boundary.
- Migration setup misuse, unknown future version, name drift or non-dedicated database:
  `ValueError` for invalid API arguments and `RuntimeError` for incompatible persisted
  migration/schema state, following existing isolated runner conventions.

The repository never catches a domain validation failure and converts it to missing.
All integrity failures are global for the requested archive operation; no partial domain
value is returned.

## Migration ownership

Migration application is an explicit setup/composition action only. It is deterministic,
idempotent, contains no network or clock access, and is never invoked from a repository
constructor, save/load method, acquisition service, normalizer, target-set builder,
historical replay application, or main database migration runner.

The runner requires an exact `sqlite3.Connection` with no active transaction, enables
foreign keys, rejects schema collisions, then applies the complete pending sequence in
one `BEGIN IMMEDIATE`. Migration failure rolls back schema and registry changes and
immediately re-raises. Re-running on the exact v1 schema is a no-op after read-only drift
validation. Direct `apply` is intentionally non-idempotent and transaction-neutral; only
the explicit runner owns idempotence and transactions.

## Allowed Files

Only these files may change during a later approved execution:

```text
scripts/simulation/nar_daily_target_evidence_archive_migration.py
scripts/simulation/sqlite_nar_daily_target_evidence_archive.py
tests/test_nar_daily_target_evidence_archive_migration.py
tests/test_sqlite_nar_daily_target_evidence_archive.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

The two production modules and two tests are new. No separate supplier Protocol/adapter,
migration-runner file or aggregate-evidence table is authorized; the minimal responsibilities
are fully owned by the two approved modules above.

## Forbidden Files and operations

Every other path is forbidden, including existing Phase 6/18 production and tests,
fixtures, `.gitattributes`, main migrations, existing NAR/JRA archives, schemas,
`database/keiba.db`, `logs/`, CLI, replay runner, manifest, release tags and history.

Live HTTP acquisition, browser/eval use, supplier/Monthly/RaceList transport changes,
target-set orchestration, prediction snapshot resolution, settlement acquisition,
manifest/replay, daily result persistence, ROI/reporting, JRA support and main database
migration are non-goals. No stage, commit or push is authorized during PREPARE or a later
EXECUTE unless separately approved after review.

## Required Tests

`tests/test_nar_daily_target_evidence_archive_migration.py` must prove:

1. fresh dedicated migration creates exactly the frozen v1 objects;
2. runner idempotence and exact applied/pending version reporting;
3. transaction-neutral direct `apply` and runner-owned rollback;
4. unknown/mismatched/malformed registry and incompatible schema fail closed;
5. unregistered tables, main DB schema and settlement/JRA archive schema are rejected;
6. migration is absent from the main and existing archive registries;
7. repository construction does not implicitly migrate or create any object; and
8. migration has no network, clock or current-time dependency.

`tests/test_sqlite_nar_daily_target_evidence_archive.py` must prove:

9. official-home supplier capture exact round trip;
10. Monthly-root supplier capture exact round trip;
11. locator-JS supplier capture exact round trip;
12. MonthlyConveneInfo response capture and full request identity exact round trip;
13. RaceList response capture and full request identity exact round trip;
14. BLOB round trip preserves CRLF, trailing whitespace, space-before-tab and non-ASCII
    UTF-8 bytes;
15. UTC microseconds and every nullable metadata field are preserved exactly;
16. exact duplicate save is an idempotent no-op for both capture families;
17. same ID with conflicting body is rejected without overwrite;
18. same ID with conflicting request/HTTP/timestamp metadata is rejected;
19. stored response SHA, BLOB byte length and capture ID corruption are detected;
20. malformed/noncanonical timestamp and invalid enum/page kind are detected;
21. missing exact capture returns `None`, while corrupt rows never become missing;
22. missing/corrupt body is not repaired during save or load;
23. there is no fallback to another row and no latest/list selection behavior;
24. load through a read-only connection performs no database write;
25. save is one atomic transaction and rolls back body plus metadata on failure;
26. insertion order cannot change exact load output;
27. production archive code has no network or clock dependency;
28. existing Phase 6 capture Protocol behavior remains compatible;
29. Phase 18 supplier capture/bootstrap domain behavior remains compatible;
30. existing NAR settlement archive schema/repository remains untouched, and separately
    stored partial bootstrap/daily captures expose no complete-target-set claim.

Execution must run:

```text
python -m unittest tests.test_nar_daily_target_evidence_archive_migration tests.test_sqlite_nar_daily_target_evidence_archive
python -m unittest tests.test_nar_historical_daily_target_capture tests.test_nar_historical_daily_target_bootstrap_capture tests.test_nar_historical_daily_target_bootstrap tests.test_nar_historical_daily_target_source tests.test_nar_historical_daily_target_live_capture tests.test_nar_official_response_capture_migration tests.test_sqlite_nar_official_response_capture_repository
python -m unittest discover -s tests -p "test_*.py"
```

Static boundary checks must confirm that the new production modules do not import HTTP,
browser, clock/time, target-set builder, replay, manifest, main migration runner or
settlement archive modules; repository construction contains no migration call; the
repository defines no latest/list/delete/update/repair API; and no SQL mutation other
than INSERT exists outside the explicit migration/setup and save paths.

Tests use temporary or `:memory:` dedicated databases only. They must never open or
modify `database/keiba.db`, provider archives or research fixtures. Tests may not relax,
skip or replace a fail-closed assertion to pass.

## Execution Results

- Dedicated Phase 20: `28 tests PASS`; these tests cover all frozen 30 behavior groups.
- Dedicated ResourceWarning gate: `28 tests PASS` with
  `-W error::ResourceWarning`; no new warning originates from Phase 20 tests.
- Related Phase 6/18 and existing NAR SQLite archive regressions: `67 tests PASS`.
- Full suite: `3041 tests PASS`.
- Full-suite ResourceWarnings originate from pre-existing historical snapshot, JRA
  capture migration, main migration and bet-plan test paths; neither new Phase 20 test
  module appears in a warning.
- Static boundary search and Python compilation: `PASS`; no network/current-clock,
  forbidden immutable mutation, main-migration or settlement-storage shortcut was found.
- Schema smoke test created and validated exactly the four frozen tables and two frozen
  integrity indexes.
- Git scope contains exactly the six Allowed Files and no staged file.

Implementation remains exact-ID only and connection-injected. It stores response bodies
and official request material as byte-exact BLOBs, reconstructs both existing domain
types on load, detects stored schema/body/identity/metadata corruption, preserves
append-only idempotent/conflict semantics, and exposes no aggregate, target-set, latest,
fallback, repair, network, clock or implicit migration path.

## Stop Condition

During PREPARE, stop at `DRAFT_FOR_REVIEW` after changing only the two docs with no
staged files. No implementation is authorized yet.

During a later approved execution, stop without guessing if exact schema ownership,
domain reconstruction, immutable identity, byte preservation or existing Protocol
compatibility conflicts with this contract; if another file/schema/migration is needed;
or if any dedicated, related, full-suite, static, Git scope or diff check fails.

Successful execution requires all 30 behavior groups, related tests, full suite and
static checks to pass; `git diff --check` to pass; only the six Allowed Files to be
changed; cached state to remain empty; docs to record exact results; and Status to become
`READY_FOR_REVIEW`. Stage, commit and push remain separately gated.
