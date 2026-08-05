# Current Phase

## Status

APPROVED_FOR_COMMIT

## Phase

Phase 4C-2d3b1i6b2 — Historical input snapshot SQLite DDL implementation

## Base Commit

`c031008c5ecc34dfb90b541a8c686b0868084709 feat: add historical input snapshot domain`

## Branch

`feature/ver0.8-simulator`

## Canonical Workspace

`C:\Users\garim\Desktop\KeibaAI-review-1i5b2b`

The original workspace, `C:\Users\garim\Desktop\KeibaAI`, is not a modification target.

## Objective

Implement only approved V3b executable SQLite DDL as migration identity
`v010_historical_input_snapshot_schema`. The phase creates the historical-input schema, its approved
indexes and linkage triggers, and registers the migration with the existing runner. It does not implement a
historical snapshot writer, reader, `save_snapshot`, `load_latest_snapshot`, collector, provider, parser,
source-record digest, import/backfill, `SimulationRaceInput` reconstruction, CLI, or any V3c policy.

V3a domain values are already implemented by Phase 4C-2d3b1i6b1. V3b is the only storage contract in
scope; V3c source policy and V3d repository semantics remain design-only context.

## Completed Dependencies

- Phase 4C-2d3b1i6a V3a/V3b/V3c/V3d design is approved in
  `docs/VER0.8_SIMULATOR_DESIGN.md`.
- Phase 4C-2d3b1i6b1 committed the V3a historical snapshot domain at the formal base.
- Existing migrations are v008 (`v008_simulation_schema`) and v009
  (`v009_simulation_bet_plan_schema`).
- The existing runner and its `schema_migrations` contract are reused unchanged except for explicit v010
  registration.

## Migration Infrastructure Findings

Migration modules live in `scripts/migrations/versions/`; the future module path is exactly
`scripts/migrations/versions/v010_historical_input_snapshot_schema.py`. Existing migrations expose
`VERSION`, `NAME`, `STATEMENTS`, optional `TRIGGERS`, and `apply(connection)`. The identity is fixed:

```text
VERSION = 10
NAME = "v010_historical_input_snapshot_schema"
```

`scripts/migrations/runner.py` explicitly imports version modules and declares the tuple
`MIGRATIONS = (v008_simulation_schema, v009_simulation_bet_plan_schema)`. It must import v010 and append it
once, yielding ordered versions `(8, 9, 10)`. `scripts/migrations/versions/__init__.py` has no registration
role and must remain unchanged.

The runner owns all transaction and migration-record work:

- it enables and verifies `PRAGMA foreign_keys = ON`;
- it rejects an already-active transaction;
- it creates `schema_migrations` in its own transaction when needed;
- for each pending migration, it issues `BEGIN IMMEDIATE`, calls `migration.apply(connection)`, inserts the
  `(version, name, applied_at)` record, then commits;
- on error it rolls back and re-raises.

`v010.apply(connection)` is transaction-neutral and must do only:

```python
for statement in STATEMENTS + INDEXES + TRIGGERS:
    connection.execute(statement)
```

It must not issue `BEGIN`, `BEGIN IMMEDIATE`, `COMMIT`, or `ROLLBACK`; call `connection.commit()` or
`connection.rollback()`; use `connection.executescript()`; open another connection; or insert migration
records.

Existing migration tests use in-memory SQLite with a minimal manually-created parent schema. The primary
conventions are `tests/test_simulation_migrations.py` and
`tests/test_simulation_bet_plan_migration.py`.

## Legacy Parent Findings

`scripts/database.py` defines `races.id INTEGER PRIMARY KEY AUTOINCREMENT` and
`horses.id INTEGER PRIMARY KEY AUTOINCREMENT` with `horses.race_id` as the legacy internal-race linkage.
The existing legacy helper index is `idx_horses_race_id ON horses(race_id)`. It is not equivalent to
`ux_horses_race_id_id`; no existing exact composite unique index is declared.

The required parent key is executable: `horses.id` is already unique as the primary key, so
`CREATE UNIQUE INDEX ux_horses_race_id_id ON horses(race_id, id)` cannot encounter duplicate pairs on a
clean parent schema. It supplies SQLite's required unique parent key for the V3b composite FK from an
external entry to `horses(race_id, id)`. `races(id)` supplies the external-race parent FK. No legacy table
definition changes are permitted.

## Allowed Files

- `scripts/migrations/versions/v010_historical_input_snapshot_schema.py`
- `scripts/migrations/runner.py` — explicit v010 import and one registry entry only.
- `tests/test_historical_input_snapshot_migration.py`
- `tests/test_simulation_migrations.py` — update the exact applied-version expectation to include v010.
- `tests/test_simulation_bet_plan_migration.py` — update exact registry/applied-version expectations to
  include v010 without changing v009 contract coverage.
- `tests/test_sqlite_persisted_simulation_application.py` — update its two exact applied-version mappings
  to include v010.
- `docs/CURRENT_PHASE.md`
- `docs/LATEST_CODEX_REPORT.md`

Additionally, the following two existing real-chain success tests may change only to create and commit the
minimal `races` and `horses` parent-schema fixture at their resolved temporary request database path before
the existing application chain invokes default migrations:

- `tests/test_cli_run_persisted_simulation.py`
- `tests/test_persisted_simulation_request_application.py`

The three existing test updates are required only because their assertions enumerate the complete default
migration registry as v008/v009. No unrelated test behavior may change.

## Legacy Schema Prerequisite

v010 is an overlay migration over the existing KeibaOS legacy race/horse schema. Before the default chain
reaches v010, a database must have `races` and `horses`. v010 does not create, repair, or infer parents.
The migration runner does not own legacy bootstrap. The file-backed persisted-simulation application,
request application, and CLI do not gain bootstrap responsibility in this phase. The two authorized
real-chain success tests prepare the minimal real SQLite parent fixture at the resolved request database
path; they do not call `apply_migrations()` manually.

## Forbidden Files

- `scripts/simulation/historical_input_snapshots.py` and every other domain/production module outside the
  one migration module and explicit runner registration.
- `scripts/migrations/versions/__init__.py`, `scripts/database.py`, schema/bootstrap code, repositories,
  providers, parsers, services, composition, runner behavior other than registration, CLI, README, and
  package-root exports.
- All database files including `database/keiba.db`, and `logs/`.
- Any repository writer/reader, save/load API, source implementation, V3c source mapping/digest, legacy
  data backfill, external-identity inference, synthetic provenance, or historical snapshot reconstruction.
- Any ninth historical table, `is_complete`, repository metadata table, completeness/digest/backfill trigger,
  or migration-owned transaction control.

## Migration Identity

The only migration identity is `v010_historical_input_snapshot_schema` with version `10`. It is appended
after v009 through `runner.MIGRATIONS`; discovery is not dynamic.

## Exact Eight Tables

The migration creates exactly these eight historical-input tables and no other historical table:

1. `historical_input_source_identities`
2. `historical_input_external_races`
3. `historical_input_external_entries`
4. `historical_input_snapshots`
5. `historical_input_snapshot_races`
6. `historical_input_snapshot_entries`
7. `historical_input_snapshot_past_races`
8. `historical_input_snapshot_provenance`

There are exactly eight `CREATE TABLE` statements, four `CREATE INDEX`/`CREATE UNIQUE INDEX` statements,
and five `CREATE TRIGGER` statements in V3b migration scope.

## Indexes

The exact four index names are:

1. `ux_horses_race_id_id` — `UNIQUE horses(race_id, id)` legacy composite-parent helper.
2. `idx_his_external_races_internal`
3. `idx_his_external_entries_internal`
4. `idx_his_snapshots_latest_eligible`

No duplicate index is added for primary keys or existing unique constraints. In particular, entry ordering,
past-race identity, and provenance identity use table primary/unique keys rather than redundant explicit
indexes.

## Triggers

The exact five linkage-only trigger names are:

1. `trg_his_snapshot_entry_mapping_insert`
2. `trg_his_snapshot_entry_mapping_update`
3. `trg_his_snapshot_header_mapping_update`
4. `trg_his_external_entry_referenced_update`
5. `trg_his_external_entry_referenced_delete`

They protect mapping drift that cannot be represented by a direct FK. No trigger proves completeness,
requires future child rows during parent insertion, calculates a digest, repairs data, or backfills rows.

## Natural Identity

`historical_input_snapshots` uses exactly:

```sql
UNIQUE (
    dataset_id,
    organization,
    source_system,
    external_race_id,
    captured_at_utc
)
```

It does not include `snapshot_id`, `source_url`, `internal_race_id`, `information_cutoff_utc`, or
`content_sha256`. `source_url` is snapshot content on `historical_input_snapshots`; `external_horse_id` is
snapshot-entry content on `historical_input_snapshot_entries`. Neither belongs to the external natural
identity key.

## Foreign Keys

All V3b new-table foreign keys explicitly use `ON DELETE RESTRICT ON UPDATE RESTRICT`. The external-race
mapping references `races(id)`. The external-entry mapping references
`horses(race_id, id)` through the helper unique index. Snapshot header, race, entry, past-race, and
provenance linkage follows the exact approved V3b DDL.

Provenance preserves nullable linkage: a `past_race/{entry}/none` record has `input_type = 'past_race'`, a
non-null `race_entry_id`, and `past_race_index = NULL`. The nullable composite FK must not make that valid
absence record impossible. Numbered past-race provenance uses a non-null index. SQL permits both structural
forms without independently enforcing domain-level past-versus-`/none` XOR.

## Storage Types

Approved Decimal columns are `TEXT`: `win_odds_text`, `margin_text`, `weight_text`,
`weight_diff_text`, and `odds_text`. No Decimal field uses `REAL`, `FLOAT`, `DOUBLE`, or SQL coercion.

Dates use shaped `TEXT` `YYYY-MM-DD`; UTC datetimes use shaped 32-character `TEXT`
`YYYY-MM-DDTHH:MM:SS.ffffff+00:00`. Required text checks use exactly
`typeof(value) = 'text' AND value <> ''`; they do not use `trim`. Optional text is `NULL` or exact nonempty
`TEXT`. `passing_order` is `TEXT NOT NULL` with a type check only, so `''` is valid and `NULL` is rejected.

`entry_order`, `past_race_index`, `fourth_corner_position`, and `popularity` are non-negative integer
columns. Approved IDs and positive numeric fields remain positive. Provenance input types are exactly
`track`, `entry`, `odds`, `jockey`, and `past_race`.

## DDL Validation Boundary

V3b enforces storage type/nullability, coarse ranges, nonempty required text, UTC/date shape, key/unique
constraints, provenance structural shapes, foreign keys, and linkage triggers. It deliberately does not
enforce NFC, Decimal canonicality, calendar validity, contiguous orders, full audit-key completeness,
past-race versus `/none` XOR, full digest reconstruction, causal time ordering, or source/provenance
semantic consistency. Those remain V3a domain and later repository responsibilities.

## Migration Transaction Boundary

The runner owns foreign-key verification, transaction start, commit, rollback, and `schema_migrations`
insertion. v010 performs DDL only through `connection.execute()` and has no retry, fallback, connection
lifecycle, database-path, or backfill responsibility.

## No-Backfill Rule

v010 must not read legacy rows to construct historical snapshots, copy `horses.odds`, trust v008 odds,
populate historical rows, infer external identities, or synthesize provenance. After successful migration,
all eight historical-input tables may be empty.

## Required Tests

The new dedicated in-memory migration suite must verify:

- v010 identity, import, registration after v009, and idempotent one-time application;
- exactly eight historical table names, exactly four index names, and exactly five trigger names;
- `PRAGMA foreign_keys` remains enabled, `foreign_key_check` is clean, and runner ownership remains intact;
- `apply()` has no begin/commit/rollback/`executescript` behavior and the runner inserts the migration record;
- snapshot natural identity rejects an exact duplicate; changing only `information_cutoff_utc` or
  `content_sha256` does not create a distinct identity, while changing `captured_at_utc` does;
- external-race FK; external-entry composite FK to `horses(race_id,id)`; and all RESTRICT/update/delete
  linkage behavior including each of the five triggers;
- source URL/header storage and external horse ID/snapshot-entry storage;
- accepted empty `passing_order`, rejected NULL passing order, all four zero-based fields accepting zero,
  positive ID/range rejection, and provenance input-type/shape matrix including nullable `/none`;
- Decimal `TEXT` storage, date/UTC shape checks, required text without trim rejection, and no historical
  backfill on an upgraded database.

Existing exact default-registry expectations must be updated only in:
`tests/test_simulation_migrations.py`, `tests/test_simulation_bet_plan_migration.py`, and
`tests/test_sqlite_persisted_simulation_application.py`. The historical domain suite remains unchanged.

## Verification Commands

Use the repository-approved Python runtime:

```powershell
& "C:\Users\garim\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m pytest tests/test_historical_input_snapshot_migration.py -q
& "C:\Users\garim\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m pytest tests/test_simulation_migrations.py tests/test_simulation_bet_plan_migration.py tests/test_sqlite_persisted_simulation_application.py tests/test_sqlite_simulation_bet_plan_snapshot_repository.py tests/test_historical_input_snapshots.py -q
& "C:\Users\garim\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m pytest -q
git diff --check
git status --short
```

No test may use `database/keiba.db`; use `:memory:` or temporary SQLite fixtures following existing
migration-test conventions.

## Stop Condition

Preparation only. Do not modify production, tests, migration modules, runner, registry, README, database, or
logs beyond these two preparation documents. Do not stage, commit, or push. Stop for ChatGPT review.
