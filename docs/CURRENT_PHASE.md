# Current Phase

Status: `APPROVED_FOR_CODEX`

## Identity and scope

- Phase: `POST_V0_8_DAILY_REPLAY_26`
- Name: `NAR Daily Replay Result Persistence and Aggregation Design`
- Phase type: `DESIGN_ONLY`
- Base Commit: `ec4f7b475185c78f19ce814fa73e21693a435425`
- Branch: `feature/post-v0.8-daily-replay`
- Preparation outcome: `PERSISTENCE_AGGREGATION_SPLIT_REQUIRED`

This phase designs the durable post-replay result and explicit multi-day aggregation
boundaries only. Phase 25 replay execution, discovery, evidence resolution, manifest,
runner, prediction, settlement and existing archives are read-only authority.

## PREPARE scope

Only these files may change:

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

Production, tests, fixtures, migrations, schemas, database/**, logs/**, archives and CLI are
forbidden. No stage, commit or push is authorized.

## Read-only audit findings and database ownership

- Phase 25 produces valid immutable outcomes for all three execution states; diagnostic
  results deliberately contain no summary, projection or financial metric.
- `orchestration_audit_sha256` is an evidence/request identity and intentionally excludes
  `SimulationSummary` and by-bet-type values.
- Completed results expose run/strategy/budget/path values through their manifest document;
  diagnostic results intentionally do not retain those inputs.
- The main migration registry ends at v015 and owns the existing simulation schema. No daily
  replay-result table exists. Phase 20's dedicated evidence archive and settlement archive
  are separate ownership boundaries and cannot store daily-result records.
- Existing immutable repositories use injected SQLite connections, explicit migration setup,
  exact-key reload, and the existing validation/conflict/data-integrity error classes.

Daily-result records therefore belong to the explicit main simulation SQLite database. Future
repository construction, save and load do not migrate, auto-create a database, use a hidden
path, choose a fallback store or use network. The next main migration is provisionally
`v016_nar_daily_replay_result_schema`; Phase 27 PREPARE must confirm the exact v015 registry
precondition before freezing that version/file name.

## Persistence coverage and audit receipt

Every successfully constructed Phase 25 result is persistable:

```text
FULL_DAY_REPLAY_COMPLETED
NOT_RUN_PARTIAL_RESOLUTION
NOT_RUN_NO_EXECUTABLE_TARGETS
```

An exception from Phase 25 produces no valid result and no row. Diagnostic rows are immutable
audit records only: summary fields are absent and never replaced with a fabricated zero-money
summary.

Phase 25 intentionally omits audit inputs from diagnostic result fields. Phase 27 must thus
require an immutable persistence request containing the exact result plus exact database path,
NAR settlement-capture archive path, manifest path, `SimulationRunContext`, `StrategyIdentity`
and `BetStakeBudget`. Its constructor must rebuild the frozen
`nar-daily-replay-orchestration-audit-v1` canonical payload and require that digest to equal
the result's audit SHA before projecting a persisted record. This is a verifier for the
committed Phase 25 protocol, not a new Phase 25 identity or a Phase 25 modification.

## Persisted record and content identity

Phase 27 should add a provider-specific immutable persistence-record domain and an
independent repository protocol/module, rather than extending `repositories/interfaces.py`.
The record is an audited projection; it need not reconstruct the complete runtime result.

Minimum record content:

- target date; exact `NAR`/`nar_official` provider; execution/resolution state;
- orchestration audit SHA and distinct persisted full-content SHA;
- target-set content SHA; supplier homepage/root/JS IDs, supplier evidence identity, Monthly
  ID and authoritative ordered RaceList IDs;
- dataset, selection policy, settlement cutoff and ordered resolution outcome references
  (target key, disposition/reasons, internal ID, snapshot/result/payout identity data);
- run ID, target commit ID, strategy ID/name/config hash, uniform race budget, exact requested
  manifest path and optional manifest SHA; and
- completed-only exact `SimulationSummary` scalars and ordered `BetTypeSummary` values.

Canonical structured values may use compact JSON only with a frozen schema/version, lexical
object-key sorting, authoritative list order, NFC text, UTC microsecond `+00:00` datetimes,
UTF-8, `ensure_ascii=False`, `allow_nan=False`, separators `(',', ':')`, and no trailing LF.
No pickle, repr, locale or unordered serialization is permitted. Decimal rates use normalized
finite fixed-point text and are recomputed from saved integer numerators/denominators on load.

The separate `nar-daily-replay-persisted-result-v1` SHA-256 covers every stored header, ordered
outcome reference, optional summary scalar and ordered by-bet-type value. It is not a
replacement for `orchestration_audit_sha256`.

## Proposed append-only main schema

Subject to the v016 registry audit, use exactly two tables:

```text
nar_daily_replay_results
nar_daily_replay_result_bet_type_summaries
```

The header natural primary key is `orchestration_audit_sha256`; it retains all non-child fields
above. The child primary key is `(orchestration_audit_sha256, bet_type)` and holds exact
by-bet-type values. No surrogate identity, latest flag, current-clock `created_at`, mutable
cumulative row or foreign key to a separate capture archive is added.

Checks enforce provider, state relation, digest shape, canonical UTC text, money/count shape
and summary-nullability. Completed rows require a complete summary; diagnostic rows require
all summary fields NULL and no child rows. Domain reload is authoritative for complete state
and content validation. Append-only triggers plus repository scope forbid update/delete/repair,
replacement and latest-wins behavior.

## Repository semantics

The future connection- and exact-main-path-injected repository proves its connection names the
caller-supplied existing main database, has no caller transaction, verifies foreign keys and
registered schema, and never invokes migration. Save uses one `BEGIN IMMEDIATE` transaction:

```text
exact persistence request
-> verify existing Phase 25 audit SHA
-> build record/full-content digest
-> exact audit-ID load
-> absent: insert header and children atomically
-> exact equal: idempotent no-op
-> different content: RepositoryConflictError
```

Exact load returns `None` only for exact absence. Duplicate headers/children, malformed
canonical field, digest mismatch, invalid state/summary relation, corrupt child content or
schema disagreement are `RepositoryDataIntegrityError`; invalid caller input is
`RepositoryValidationError`. No latest/date/fuzzy lookup, update/delete, repair or fallback
API is introduced.

## Explicit series selection and compatibility

Multiple immutable attempts for one date may exist when orchestration identities differ.
Phase 28 aggregation accepts an explicit immutable selection of exact-loaded records, ordered
strictly by target date and containing at most one record per date. Empty, unsorted or duplicate
date/identity selections, implicit latest/newest/insertion-order choices and unknown members
fail closed.

All selected records must share this compatibility key:

```text
provider organization/source system
dataset ID
selection policy
strategy ID
strategy name
strategy config hash
target commit ID
uniform race-budget amount
```

`run_id` is an execution identity and may differ. Settlement cutoff remains immutable per-day
evidence provenance, not a selection preference or tie breaker. Any incompatible key fails
closed.

## Read-only aggregation

Phase 28 computes an immutable aggregate on demand; it persists no cache. It reports selected,
completed, partial-resolution and no-executable day counts. Diagnostics contribute only to
those status counts, never to financial amounts or rate denominators. A completed no-bet day
remains distinct because it has an actual completed summary.

All additive count/money fields are summed; profit is recomputed as payout minus investment.
Rates are recomputed, never averaged:

```text
ROI = None if investment == 0 else Decimal(payout) * 100 / Decimal(investment)
bet hit rate = None if settled_bet_count == 0 else Decimal(hit_bet_count) * 100 / Decimal(settled_bet_count)
race hit rate = None if settled_purchase_race_count == 0 else Decimal(hit_race_count) * 100 / Decimal(settled_purchase_race_count)
```

Each by-bet-type value uses the same summed numerators/denominators and is deterministic by bet
type. A plain cumulative `maximum_drawdown` is omitted: it cannot be reconstructed from daily
summaries. The only optional safe statistic is `max_single_day_maximum_drawdown`, explicitly
not a cumulative race-level MDD.

The aggregate receives `nar-daily-replay-series-aggregate-v1`, a canonical content SHA binding
ordered member audit/content identities, compatibility key, status counts and derived values.
No clock, UUID, random, filesystem metadata, database row order or float enters it.

Daily result/aggregate storage is analysis output only. Phase 14 resolution, historical snapshot
construction, PredictionPipeline, strategy/value logic and target discovery must not import or
read it.

## Required follow-up phases

`PERSISTENCE_AGGREGATION_SPLIT_REQUIRED` is the formal decision.

1. **POST_V0_8_DAILY_REPLAY_27 — NAR Daily Replay Result Persistence Implementation**
   - v016-style main migration, immutable persistence request/record, exact-ID repository,
     audit/content verification and storage integrity tests.
   - Likely future files: `scripts/migrations/runner.py`,
     `scripts/migrations/versions/v016_nar_daily_replay_result_schema.py`,
     `scripts/simulation/nar_daily_replay_result_persistence.py`,
     `scripts/simulation/repositories/sqlite_nar_daily_replay_result_repository.py`, and
     dedicated migration/repository tests.
2. **POST_V0_8_DAILY_REPLAY_28 — NAR Daily Replay Series Aggregation Implementation**
   - explicit selection, compatibility gate, Decimal/by-bet-type aggregation, status counts,
     safe drawdown statistic and no-mutation aggregate identity.
   - Likely future files: `scripts/simulation/nar_daily_replay_series_aggregation.py` and
     dedicated tests.

Each is independently PREPARE/review/approval gated. No subsequent phase is started here.

## Required later tests

Phase 27: all three states; complete/by-bet-type round trips; diagnostic summary absence;
explicit audit-input mismatch; idempotent exact duplicate; same-audit/different-content
conflict; absent/incompatible schema; header/child/digest/enum/JSON/Decimal/timestamp
corruption; no implicit migration/update/delete/repair; distinct same-date attempts; exact-ID
load only; and no database/** fixtures.

Phase 28: explicit-only sorted unique selection; every compatibility conflict; differing allowed
run IDs; diagnostic versus completed-no-bet distinction; integer sums; recomputed overall and
by-bet-type rates; zero denominators; no daily-rate averaging; safe drawdown naming;
deterministic/changed-member aggregate digest; no network/current clock/prediction imports;
Phase 25 regression; and full suite.

## Stop condition

Stop at `DRAFT_FOR_REVIEW`. No implementation, tests, migration, stage, commit, push or Phase
27 PREPARE is authorized in this run.
