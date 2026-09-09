# Current Phase

Status: `READY_FOR_REVIEW`

## Identity and scope

- Phase: `POST_V0_8_DAILY_REPLAY_27`
- Name: `NAR Daily Replay Result Persistence Implementation`
- Phase type: `IMPLEMENTATION`
- Base Commit: `daa976b546610daceee670b4408238c87164c9a8`
- Branch: `feature/post-v0.8-daily-replay`
- Preparation outcome: `IMPLEMENTABLE`

Phase 27 persists one already-valid Phase 25 orchestration result into the main simulation
SQLite database as an immutable, reload-validated daily-result record. It does not execute,
repeat, alter, or automatically persist Phase 25 replay orchestration. It does not select or
aggregate multiple days; that remains exclusively Phase 28.

## PREPARE scope

Only these files may change during this PREPARE:

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

No production, test, migration, schema, fixture, database/**, logs/**, archive or CLI change is
authorized in PREPARE. No stage, commit or push is authorized.

## Read-only audit and migration decision

- The current branch and `origin/feature/post-v0.8-daily-replay` both resolve to
  `daa976b546610daceee670b4408238c87164c9a8` before this PREPARE.
- `scripts/migrations/runner.py` registers v008 through v015, and the registered highest
  migration is exactly `v015_jra_race_replay_seed_schema`. No daily-result relation exists.
- The next migration is therefore frozen as version 16 with
  `NAME = "v016_nar_daily_replay_result_schema"` in
  `scripts/migrations/versions/v016_nar_daily_replay_result_schema.py`; it is appended exactly
  once to `scripts/migrations/runner.py` after v015. No version is skipped or reused.
- Existing injected-connection repositories establish the applicable model: caller-owned active
  transactions are rejected, migration is explicit, writes use one `BEGIN IMMEDIATE` transaction,
  immutable exact duplicates are idempotent, and corruption/conflict uses the existing repository
  exceptions.
- The main simulation database is the exclusive Phase 27 owner. The Phase 20 daily-target archive
  and the NAR settlement archive remain separate and are neither altered nor used as daily-result
  stores.

## Phase 25 audit-verification boundary

`NARDailyReplayOrchestrationResult.orchestration_audit_sha256` is valid only when recomputed from
the exact public source values. The existing Phase 25 canonical implementation is private
(`_AuditInputs` / `_audit_digest`), and no other public verifier exists. Persistence must not
import those private names, copy their payload, trust the stored digest, or rerun replay.

Phase 27 therefore adds one thin, public, pure boundary to the existing Phase 25 module:

```python
compute_nar_daily_replay_orchestration_audit_sha256(
    *,
    acquisition_result: NARDailyTargetLiveAcquisitionResult,
    resolution: DailyHistoricalReplayEvidenceResolution,
    execution_state: NARDailyReplayExecutionState,
    manifest_sha256: str | None,
    database_path: Path,
    nar_settlement_capture_archive_path: Path,
    run_context: SimulationRunContext,
    strategy_identity: StrategyIdentity,
    race_budget: BetStakeBudget,
    manifest_source_path: Path,
) -> str
```

It validates the same public invariants and delegates to the existing single canonical audit
algorithm. `NARDailyReplayOrchestrationResult` must be routed through that same implementation;
the digest version and canonical payload remain exactly
`nar-daily-replay-orchestration-audit-v1`. This exposes no replay operation, performs no
network/clock/SQL work, and does not change Phase 25 execution semantics.

## Public persistence boundary

Create `scripts/simulation/nar_daily_replay_result_persistence.py` with these exact public
values and pure/application entry point:

```python
@dataclass(frozen=True, slots=True)
class NARDailyReplayResultPersistenceRequest:
    orchestration_result: NARDailyReplayOrchestrationResult
    database_path: Path
    nar_settlement_capture_archive_path: Path
    run_context: SimulationRunContext
    strategy_identity: StrategyIdentity
    race_budget: BetStakeBudget
    manifest_source_path: Path

@dataclass(frozen=True, slots=True)
class PersistedNARDailyReplayResult:
    ...  # the immutable fields frozen below

def persist_nar_daily_replay_result(
    *,
    request: NARDailyReplayResultPersistenceRequest,
    repository: SQLiteNARDailyReplayResultRepository,
) -> PersistedNARDailyReplayResult:
    ...
```

The request constructor requires exact, immutable Phase 25 public values. Publication is:

```text
validate request/result state
-> recompute the Phase 25 audit SHA through the public verifier
-> require exact equality with result.orchestration_audit_sha256
-> project and validate immutable persisted content
-> compute persisted_content_sha256
-> repository.save_result(record)
-> repository.load_result(persisted_content_sha256)
-> require exact equality with the projected record
-> return that exact reload
```

It never calls `run_nar_daily_replay`, acquisition, Phase 14, Phase 16, a runner, network, a
clock, or aggregation. It neither creates nor migrates a database. An error from Phase 25 that
did not create a valid result has no request/record and cannot be persisted.

All three valid Phase 25 result states are persistable:

```text
FULL_DAY_REPLAY_COMPLETED
NOT_RUN_PARTIAL_RESOLUTION
NOT_RUN_NO_EXECUTABLE_TARGETS
```

Diagnostic records are durable audit facts only. They retain state and provenance but have no
summary, by-bet-type child, published manifest artifact path or manifest digest; zero-valued
financial fields must never be fabricated. `configured_manifest_source_path` remains a separate
mandatory audit input for every state. A completed record stores a published manifest path and
digest; Phase 25 requires that artifact path to equal the configured source path, but the two
fields remain semantically distinct.

## Immutable record and deterministic content identity

`PersistedNARDailyReplayResult` is a compact audited projection, not a serialization of the whole
runtime object graph. It contains exactly:

- `schema_version = 1`, `persisted_content_sha256`, `orchestration_audit_sha256`, target date,
  `NAR` / `nar_official` provider, execution state and resolution state;
- target-set content SHA; supplier evidence identity; homepage, Monthly-root and locator-JS
  supplier capture IDs; Monthly capture ID; and authoritative ordered RaceList capture IDs;
- dataset ID, selection policy, settlement-information cutoff, canonical target count,
  executable count, and authoritative ordered resolution references (target key, disposition,
  reasons, internal race ID, snapshot identity/content and result/payout reference fields);
- run ID, UTC-microsecond run start, target commit ID, strategy ID/name/config hash, uniform
  race-budget amount, configured manifest path, and completed-only published artifact path/SHA;
- completed-only exact `SimulationSummary` scalar fields and lexically ordered exact
  `BetTypeSummary` values; or no summary content for diagnostics.

The content identity is primary:

```text
nar-daily-replay-persisted-result-v1
```

Its lower-case SHA-256, `persisted_content_sha256`, covers every persisted semantic header field,
the authoritative ordered reference lists, every optional summary scalar, and every ordered
by-bet-type child. `orchestration_audit_sha256` remains the separate Phase 25 request/evidence
identity and is unique in storage. Thus the same audit identity plus exact content is an
idempotent no-op, while the same audit identity with any different persisted content is a
`RepositoryConflictError`. Different audit identities may coexist for the same target date.

Canonical structured payloads are frozen as schema-versioned JSON TEXT, not pickle/repr/eval:

- UTF-8, NFC text, `ensure_ascii=False`, `allow_nan=False`, lexical key sort, separators
  `(',', ':')`, and no trailing LF;
- authoritative tuple/list order is retained; order-insensitive maps are emitted in lexical key
  order;
- aware datetimes are UTC ISO-8601 with microseconds and explicit `+00:00`;
- finite `Decimal` values use canonical normalized fixed-point text (zero is `"0"`), are checked
  against their integer numerator/denominator formulas, and are never stored as floats.

Reload rejects malformed, noncanonical or semantically contradictory structured content rather
than normalizing or repairing it.

## v016 schema and storage invariants

The migration creates only these two append-only main-schema tables:

```text
nar_daily_replay_results
nar_daily_replay_result_bet_type_summaries
```

`nar_daily_replay_results.persisted_content_sha256` is the primary key and
`orchestration_audit_sha256` is `UNIQUE NOT NULL`. It carries all header/provenance, canonical
JSON, run/configuration, optional artifact, and optional completed-summary scalar columns.
`nar_daily_replay_result_bet_type_summaries` has primary key
`(persisted_content_sha256, bet_type)`, a restrictive foreign key to the header, and exact
by-bet-type scalar/rate columns. Its rows are lexical by `bet_type` on reload.

SQLite checks cover the fixed provider, digest shape, exact allowed execution/resolution states,
nonempty canonical text, UTC text shape, nonnegative count/money shape, and state-specific
NULL consistency. Completed headers require a complete summary and child mapping that exactly
matches it. Diagnostic headers require every summary scalar and artifact field NULL and have no
children. Domain reconstruction and both digest re-computations remain the final authority.

The migration first requires the exact v015 registry/schema state, rejects pre-existing v016
objects, and makes no backfill, inference, seed, daily-result timestamp or other semantic data.
It is applied only by the existing explicit runner transaction. `BEFORE UPDATE` and `BEFORE
DELETE` abort triggers protect both tables from mutation; no update/delete API is added.

## Repository boundary and exact load

Create `scripts/simulation/repositories/sqlite_nar_daily_replay_result_repository.py`:

```python
class SQLiteNARDailyReplayResultRepository:
    def __init__(self, *, connection: sqlite3.Connection, database_path: Path) -> None: ...
    def save_result(self, *, record: PersistedNARDailyReplayResult) -> None: ...
    def load_result(
        self, *, persisted_content_sha256: str
    ) -> PersistedNARDailyReplayResult | None: ...
```

The constructor accepts an exact SQLite connection and an exact caller-supplied existing absolute
main-database path, verifies no active transaction, foreign-key enablement and the registered
v016 schema, but never invokes migration. It uses the normal repository read-only
`PRAGMA database_list` filesystem-identity check without changing the caller's path spelling;
the supplied path remains the audit authority. Load does no migration, no write, no clock and
no network.

Save rejects a caller transaction, validates the record and begins one `BEGIN IMMEDIATE`
transaction. It exact-loads by both primary content SHA and unique audit SHA before inserting
the complete header and children. Equal material succeeds without mutation; any disagreement
is conflict; SQLite/schema/canonical reconstruction/digest failures are integrity errors. A
failed write rolls back all logical rows. Missing exact content ID returns `None` only. There
is no latest/date/list/fuzzy lookup, automatic selection, update, delete, repair, replacement or
fallback.

Use only existing `RepositoryValidationError` for invalid caller values,
`RepositoryConflictError` for immutable different-content publication, and
`RepositoryDataIntegrityError` for stored/schema/constraint corruption; preserve causes. Do not
extend `repositories/interfaces.py`, avoiding simulation-domain import cycles.

## Future-information and Phase 28 boundaries

Persistence output is analysis output only. The Phase 27 modules/tables must not be imported or
read by historical snapshot construction, Phase 14 resolution, target discovery,
`PredictionPipeline`, value computation or strategy code. No automatic outcome-feedback path is
introduced.

Phase 27 stops at one exact daily record persisted and reload-verified. It does not implement
explicit multi-day selection, duplicate-date series policy, cumulative counts/money/rates,
by-bet-type aggregation, drawdown aggregation, aggregate digest, reporting, CLI, cache, or an
aggregate table. Those belong to Phase 28.

## Exact future implementation scope

Only the following files are proposed for a separately approved Phase 27 EXECUTE:

```text
scripts/migrations/runner.py
scripts/migrations/versions/v016_nar_daily_replay_result_schema.py
scripts/simulation/nar_daily_replay_orchestrator.py
scripts/simulation/nar_daily_replay_result_persistence.py
scripts/simulation/repositories/sqlite_nar_daily_replay_result_repository.py
tests/test_simulation_migrations.py
tests/test_nar_daily_replay_orchestrator.py
tests/test_nar_daily_replay_result_persistence.py
tests/test_sqlite_nar_daily_replay_result_repository.py
tests/test_jra_race_replay_seed_migration.py
tests/test_historical_input_snapshot_migration.py
tests/test_nar_official_response_capture_migration.py
tests/test_simulation_bet_plan_migration.py
tests/test_sqlite_persisted_simulation_application.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

All other production, tests, migrations, schemas, database/**, logs/**, archives, CLI and the
Phase 25 runner are forbidden. The Phase 25 file/test exception is solely the thin public audit
verifier and its regression coverage; a replay refactor is not authorized.

## Required later verification

The future implementation must cover these behavior groups:

1. exact public audit verifier matches the existing Phase 25 digest; changed database/archive
   path, run context, strategy, budget or configured manifest path fails verification; no private
   helper import or second audit algorithm;
2. completed, partial diagnostic and no-executable diagnostic results each persist/reload;
   failed/no-result cannot persist; diagnostics remain summary-less; completed no-bet remains
   distinct from diagnostics;
3. exact scalar summary, Decimal rates, maximum drawdown and ordered by-bet-type values round
   trip; result content SHA is deterministic and invalid content SHA is rejected;
4. exact duplicate is a no-op; same audit identity with changed summary or metadata conflicts;
   different immutable attempts on one date remain allowed;
5. v016 is registered exactly once after v015; migration is explicit/idempotent; absent or
   malformed schema fails closed; constructor never migrates. The JRA v015, historical-input,
   NAR response-capture, simulation bet-plan, and persisted-simulation application migration
   regressions retain their original semantics through explicit migration boundaries/current
   registry expectations rather than assumptions that v015 is the registry tail;
6. exact-ID-only absence returns `None`; corrupt scalar, child, enum, UTC text, canonical JSON,
   Decimal, digest or state/NULL relation fails closed; no latest/fallback/update/delete/repair;
7. failed writes roll back; caller transaction state is preserved; connection/path identity is
   checked; no network/current clock/replay/acquisition/aggregation; and no analysis-output
   dependency reaches prediction/evidence/strategy;
8. Phase 25 public-audit regression, migration regression, existing simulation repository
   regressions and the full unittest suite pass; `database/**` and `logs/**` remain unchanged.

## Stop condition

Stop at `DRAFT_FOR_REVIEW`. No implementation, test creation, migration creation, stage,
commit, push or Phase 28 preparation is authorized in this run.

## PREPARE revision: migration-regression scope correction

Preparation outcome: `IMPLEMENTABLE`.

The previously identified v016 registry-tail blocker is resolved by adding exactly these existing
regression tests to the Phase 27 implementation Allowed Files:

```text
tests/test_jra_race_replay_seed_migration.py
tests/test_historical_input_snapshot_migration.py
```

The JRA v015 regression must explicitly construct a through-v014 state when testing v015, assert
v015's unique registered identity and expected objects, and stop treating v015 as permanently
terminal. The historical-input regression must update only the assumptions that the full registry
ends at v015 and express any v010--v015 historical boundary by version identity. Neither test may
lose its existing migration-specific coverage.

No workaround in `MIGRATIONS`, hidden v016 registry, conditional omission, or weakened regression
coverage is permitted. This revision touched documentation only; the pre-existing unstaged partial
Phase 27 implementation remains untouched. No database/** or logs/** path is changed. Blockers:
none.

## Resumed EXECUTE scope blocker

Execution outcome: `CHANGES_REQUIRED`.

The resumed implementation completed the approved corrections above, then an exhaustive
migration-registry assumption search and focused execution found two additional existing
regressions outside the exact 13-file Allowed Files:

```text
tests/test_nar_official_response_capture_migration.py
tests/test_simulation_bet_plan_migration.py
```

With the honest v016 registry, the first has one failure because it asserts the unrelated main
registry is permanently `(8, ..., 15)`. The second has three failures because its v009-focused
tests assert the current full registry/applied set ends at v015. Their dedicated combined run was
21 passes / 4 failures. Both corrections are registry-expectation maintenance only; neither
requires a production, migration, archive, or domain change.

These paths are not in the approved scope, so Codex did not edit them, hide v016, weaken the
registry, run the full suite, or continue implementation. ChatGPT must explicitly authorize any
scope correction. All partial Phase 27 work remains unstaged and preserved; no database/** or
logs/** path changed.

## PREPARE revision: exhaustive v016 global-registry audit

Preparation outcome: `IMPLEMENTABLE`. Status remains `DRAFT_FOR_REVIEW`.

The v016 main registry extension remains authoritative. No production registry workaround,
conditional test registry, v015 terminal rule, or migration omission is permitted. This revision
performed a read-only audit of every test using `MIGRATIONS` or applying the global migration
registry. The classifications are:

```text
A — unaffected by v016 registry-tail semantics
tests/test_cli_run_persisted_simulation.py
tests/test_historical_replay_mixed_provider_acceptance.py
tests/test_jra_race_historical_replay.py
tests/test_nar_daily_target_evidence_archive_migration.py
tests/test_persisted_simulation_integration.py
tests/test_simulation_repositories.py
tests/test_sqlite_historical_input_snapshot_repository.py
tests/test_sqlite_jra_race_replay_seed_repository.py
tests/test_sqlite_nar_daily_evidence_resolver.py
tests/test_sqlite_persisted_simulation_composition.py
tests/test_sqlite_simulation_bet_plan_snapshot_repository.py

B — already in the Phase 27 Allowed Files
tests/test_historical_input_snapshot_migration.py
tests/test_jra_race_replay_seed_migration.py
tests/test_nar_daily_target_evidence_archive_migration.py
tests/test_simulation_migrations.py
tests/test_sqlite_nar_daily_replay_result_repository.py

C — narrow v016 current-registry expectation correction required
tests/test_nar_official_response_capture_migration.py
tests/test_simulation_bet_plan_migration.py
tests/test_sqlite_persisted_simulation_application.py
```

The first Category-C file asserts the unrelated global registry is exactly versions 8--15 even
though its dedicated `CAPTURE_MIGRATIONS == (1,)` contract remains unchanged. The second asserts
both the current registry and full `get_applied_versions(...)` maps end at v015; its v008/v009
upgrade boundaries must remain explicit. The third verifies two full `apply_migrations(...)`
databases against exact version/name maps ending at v015. Each must include v016 while preserving
its existing simulation-application assertions. No other audit match contains a stale v015-tail
assumption.

The exact newly added future implementation files are:

```text
tests/test_nar_official_response_capture_migration.py
tests/test_simulation_bet_plan_migration.py
tests/test_sqlite_persisted_simulation_application.py
```

The final future Phase 27 Allowed Files count is exactly 16. This PREPARE revision changes only
the two phase documents; all existing unstaged partial implementation remains untouched. No
database/** or logs/** path is changed. Blockers: none.

## Approval

ChatGPT approved Phase 27 for Codex execution with outcome `IMPLEMENTABLE`. The final 16-file
Allowed Files scope is frozen. The v016 registry extension remains authoritative, and later
Category-C corrections are limited to the three listed migration-registry expectations; no
production registry workaround or further scope expansion is authorized. This approval changes
only the phase documents. The preserved partial implementation remains unstaged and untouched.

## Execution completion

Phase 27 implementation is complete and `READY_FOR_REVIEW`. Migration v016 is registered once
after v015 and creates the two frozen append-only daily-result tables and their immutability
triggers. The public Phase 25 audit helper and orchestration result share the single existing
canonical audit implementation. The immutable persistence request/domain, content digest,
connection-injected main-DB repository, atomic duplicate/conflict behavior, and exact-ID reload
verification are implemented for all three valid Phase 25 states.

All five approved migration-regression files retain their original scope while recognizing v016
as the current global migration. Verification passed: 32 dedicated tests with ResourceWarning
treated as an error, 21 Phase 25 tests, 267 related unittest tests, the five migration files
individually (13, 11, 8, 17, and 8 tests), and the full 3,124-test unittest suite. The dedicated
suite emitted no warning; broader suites retain pre-existing unclosed-SQLite ResourceWarnings.
Static inspection found no private Phase 25 audit imports, second canonical audit algorithm,
network/current-clock/random/UUID/pickle/eval/replay/aggregation dependency, target-date
uniqueness, implicit latest selection, or mutation API. No file is staged; database/** and logs/**
remain unchanged. Blockers: none.

The final review corrections are complete. The v016 migration now owns one exact read-only schema
contract verifier shared by migration DDL and repository construction; it compares SQLite schema
SQL, full column metadata, PK/UNIQUE index identity and order, foreign-key actions, WITHOUT ROWID
state, and exact trigger definitions. Dedicated negative coverage rejects missing/changed keys,
checks, foreign keys, WITHOUT ROWID, index order/uniqueness, and same-name no-op triggers. The
persistence application now requires the exact concrete SQLite repository at both its resolved
public type hint and runtime boundary; duck-typed and unrelated repositories fail closed.
