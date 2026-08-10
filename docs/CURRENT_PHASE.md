# Current Phase

## Status

READY_FOR_REVIEW

## Phase

Phase 4C-2d3b1i6c1d3b1 - Uniform historical evidence contract implementation

## Base Commit

3cd5f2916213f32340782f1c069d9093a4e75499 feat: define historical time-difference contract

## Branch and Workspace

Formal branch: feature/ver0.8-simulator

Implementation review branch: review/4c-2d3b1i6c1d3b1-implementation

Canonical workspace: C:\Users\garim\Desktop\KeibaAI-review-1i5b2b

The original workspace, C:\Users\garim\Desktop\KeibaAI, is read-only for this phase.

## Objective

Implement the approved uniform, provider-neutral evidence contract atomically across c1a source records, c1c
assembly, historical snapshot provenance, SQLite persistence, and the existing NAR DebaTable singleton-record
normalizer. No HorseMarkInfo or RaceMarkTable parser is included.

## Frozen Contract

- HistoricalInputEvidenceReference is the only new public type and is not package-root exported.
- Every c1a record is schema version 3 with his-v3:{record_kind}:{sha256}.
- Record-level URL and timestamps are replaced by exact tuple evidence.
- Required role sets are track; entry; jockey; odds_win; historical_race_context plus historical_race_result; and
  past_race_absence_query, respectively.
- A generic past_race has exactly two role bindings but one or two distinct underlying responses. If two roles share
  URL/SHA, their available_at and observed_at must exactly agree.
- NAR remains a future two-response provider-normalizer rule; no parser is added here.
- Snapshot provenance holds nested evidence, has no aggregate timestamps, and snapshot canonical payload is version 3.
- v012 replaces scalar persisted provenance timestamps only when the snapshot store is empty; nonempty stores fail
  before mutation.
- InputAuditEntry is unchanged. No adapter or implicit timestamp collapse is permitted.
- Raw response SHA-256 is over exact supplied body bytes before decoding or normalization.
- Evidence canonicalization is ascending `evidence_role`; source IDs include role, URL, raw SHA-256, and record facts,
  but intentionally exclude evidence timestamps. Snapshot content SHA-256 includes the nested evidence timestamps.
- HistoricalSourceIdentity.source_url is selected only from the sole track record's `track` evidence URL; `None` remains
  valid and no non-track URL is substituted.
- SQLite stores one logical provenance parent row per audit key and role-ordered child evidence rows. It permits the
  same underlying `(canonical_source_url, response_sha256)` for distinct roles only when both timestamps agree.

## Implementation Result

The approved uniform evidence transition is implemented for review. c1a is globally schema version 3 and all six
record kinds use exact role sets. c1b computes one SHA-256 over the supplied DebaTable bytes and constructs singleton
evidence for track, entry, jockey, and odds-win records. c1c copies record evidence into one logical provenance item
and evaluates every evidence timestamp for causal eligibility. The snapshot digest is version 3 and preserves
role-ordered evidence observations.

Migration `v012_historical_input_evidence_schema` is registered after v011. It checks that the historical snapshot
store is empty before replacing scalar provenance observations with the normalized evidence child table; a nonempty
store fails before schema mutation. No HorseMarkInfo/RaceMarkTable normalizer, capture-body retention, or NAR
past-race-absence production behavior was added.

## Review Correction

Selected-snapshot reconstruction now explicitly rejects an evidence child whose `(snapshot_id, audit_key)` has no
logical provenance parent, including corruption introduced while SQLite foreign keys are disabled. A corrupt newest
eligible snapshot raises `RepositoryDataIntegrityError`; it never falls back to an older snapshot.

Two source-ID isolation rules are intentionally distinct. With evidence role, URL, and raw SHA-256 held constant, a
change to one entry's logical facts changes only that record's c1a source ID. Conversely, a c1b DebaTable byte change
changes the shared raw SHA-256 and therefore the source ID of every logical record derived from that supplied response.
This intentionally supersedes the prior d1 source-ID isolation consequence at the provider boundary while preserving
the exact horse-lineage factual identity rule.

`HistoricalInputProvenance` has no scalar `available_at` or `observed_at` fields and no automatic `InputAuditEntry`
adapter. The runtime audit type remains unchanged; no nested-evidence timestamp is selected or collapsed in production.

## Allowed Files

    scripts/simulation/historical_input_evidence.py
    scripts/simulation/historical_input_source_records.py
    scripts/simulation/historical_input_snapshots.py
    scripts/simulation/historical_input_snapshot_builder.py
    scripts/simulation/nar_historical_input_source.py
    scripts/simulation/repositories/sqlite_historical_input_snapshot_repository.py
    scripts/migrations/versions/v012_historical_input_evidence_schema.py
    scripts/migrations/runner.py
    tests/test_historical_input_source_records.py
    tests/test_historical_input_snapshots.py
    tests/test_historical_input_snapshot_builder.py
    tests/test_nar_historical_input_source.py
    tests/test_sqlite_historical_input_snapshot_repository.py
    tests/test_historical_input_snapshot_migration.py
    tests/test_simulation_migrations.py
    tests/test_simulation_bet_plan_migration.py
    tests/test_sqlite_persisted_simulation_application.py
    docs/CURRENT_PHASE.md
    docs/LATEST_CODEX_REPORT.md

## Forbidden Files and Work

No provider/past-race parser, HTTP fetching, capture-body storage, past-race absence NAR production, legacy
engine/model change, package-root export, README, database file, logs, or original-workspace modification is allowed.
No c1b semantic parser change beyond singleton evidence construction.

## Required Tests

Run the nine named dedicated/migration suites in the execution authorization, then the full pytest suite using the
external Python 3.14.5 environment, plus forbidden dependency/source checks, package-root export checks,
git diff --check, and git status --short.

## Stop Condition

Stop at READY_FOR_REVIEW after one review commit and normal push to
review/4c-2d3b1i6c1d3b1-implementation. Do not integrate formally or begin NAR HorseMarkInfo/RaceMarkTable
normalization without separate approval.
