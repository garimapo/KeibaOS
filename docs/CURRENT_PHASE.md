# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase

Phase 4C-2d3b1i6c1d3a — Historical past-race field-domain contract preparation

## Base Commit

2b6d389b4296be2f6749b71fc4ed827f244ce570 feat: preserve NAR target horse identity

## Branch and Workspace

Formal branch: feature/ver0.8-simulator

Preparation review branch: review/4c-2d3b1i6c1d3a-prepare

Canonical workspace: C:\Users\garim\Desktop\KeibaAI-review-1i5b2b

The original workspace, C:\Users\garim\Desktop\KeibaAI, is read-only for this phase.

## Objective and Scope

d3a is PREPARE / design only. It freezes the minimum field-domain contract needed before a future NAR historical
RaceMarkTable normalizer can emit a semantically valid past_race source record. It changes documentation only.
Production code, tests, schema, migrations, repositories, database, providers, parsers, README, CLI, package
exports, logs, and the original workspace are read-only.

The field-domain correction is exact: replace the historic past-race field named margin with
reference_time_difference_seconds. This phase does not implement that replacement and does not normalize any official
response.

## Investigated Official Semantics

Official NAR HorseMarkInfo history displays a separate column named 差. Official CompeteTable describes that value as
the time difference from the winner, or for the winner, the time difference to the second horse. This is a direct
official time-difference display, not a horse-length margin, not a signed deficit, not a RaceMarkTable 着差 label, and
not a value inferred from race times. Historical HorseMarkInfo also exposes separate official 競走名 and 格組 values.

Therefore the required field is:

    reference_time_difference_seconds: Decimal

Its unit is seconds. For a nonwinner it is the provider-displayed difference to first; for a winner it is the
provider-displayed difference to second. The name deliberately states the unit and avoids the ambiguous legacy term
margin.

## Exact Decimal Contract

The field accepts only a direct provider value parsed as a finite Decimal. It is nonnegative; zero is permitted when
the official display directly supplies zero. It must reject int, float, bool, NaN, infinity, blank text, dash or
unavailable display markers, negative values, inferred values, and values derived from winner or race times. No
float conversion is permitted. Canonical Decimal text must use the committed canonical formatting rules.

Normal completed-row support remains conditional on every other required c1a past-race field being directly proven.
Abnormal, unavailable, or nonnumeric official values remain unsupported rather than being converted to 0, None, an
empty string, or a guessed number.

## Frozen Field-Domain Decision

| Concern | Frozen decision |
| --- | --- |
| New field | reference_time_difference_seconds: Decimal |
| Meaning | direct official time difference in seconds; nonwinner-to-winner and winner-to-second according to NAR display |
| Legacy margin | Removed from the new c1a, snapshot, SQLite, and canonical-payload contracts; no compatibility alias |
| Alias behavior | Passing margin, passing both names, or relying on a default fails validation; no dual-read or dual-write path |
| race_name | Unchanged: required nonempty official HorseMarkInfo 競走名 text |
| race_class | Unchanged: required nonempty official HorseMarkInfo 格組 text; never a subtitle substitute |
| passing_order | Unchanged in this phase |
| fourth_corner_position | Unchanged in this phase |

## Domain, Source-ID, and Snapshot-Version Contract

HistoricalInputSourceRecord past_race record_values will replace the margin key with
reference_time_difference_seconds at the same logical field position. This is a schema-breaking c1a payload change.
HistoricalInputSourceRecord.schema_version must change from 1 to 2, and the source-ID namespace must change from
his-v1 to his-v2. The record identity must be recomputed by the committed c1a canonical-payload algorithm; old source
IDs are intentionally not preserved.

HistoricalPastRaceSnapshot will replace its margin: Decimal field with
reference_time_difference_seconds: Decimal. HistoricalInputSnapshot canonical content payload will emit the new key
and must change its payload schema_version from 1 to 2. The snapshot domain, not the builder, continues to calculate
content_sha256. A new snapshot digest must never be presented as equivalent to a v1 payload.

## SQLite v011 Strategy and Old-row Policy

v010 currently persists margin_text TEXT NOT NULL in historical_input_snapshot_past_races and has no margin index.
The repository writes and reads that column directly. SQLite 3.50.4 supports ALTER TABLE RENAME COLUMN, but a rename
alone would falsely reinterpret old length/legacy-margin semantics as seconds.

The future v011 migration is therefore append-only and fail-closed:

1. Before altering the child column, it must reject migration when historical_input_snapshots contains any row.
2. Only an empty snapshot store may rename margin_text to reference_time_difference_seconds_text.
3. The migration registry appends version 11 after v010. Existing v010 history is not rewritten.
4. A nonempty-store rejection must be atomic: v011 is not recorded and the pre-v011 schema remains intact.

No old margin value is copied, converted, deleted, silently invalidated, or interpreted as seconds. The guard applies
to any snapshot row, including snapshots without past-race children, because the snapshot canonical payload itself
changes from schema version 1 to 2.

## Repository and Builder Impact

The future builder maps only the renamed c1a record value into the renamed historical snapshot field. It does not
derive a time difference or change past-race ordering, source grouping, mapping, provenance, captured_at, or cutoff
semantics. The SQLite repository changes only its exact child-column serialization/deserialization and keeps its
immutable save/load and identity guarantees.

The current legacy models, database, old past-race parser, fetch path, and persisted simulation adapters contain
legacy margin behavior. They are out of scope and untrusted for this contract. They must not be used as a fallback
or a source of conversion rules.

## Ability Engine Boundary

The legacy AbilityEngine reads legacy PastRace.margin as a float and applies legacy margin scoring. It does not
consume HistoricalPastRaceSnapshot directly. reference_time_difference_seconds must not be wired into AbilityEngine,
mapped to its legacy margin input, or interpreted as a performance score in this phase.

Ability Engine change required: LATER_FEATURE_PHASE. Such a phase needs its own approved feature semantics, score
formula, temporal evidence policy, regression plan, and compatibility decision.

## Exact Future Implementation Impact

| Area | Required future change |
| --- | --- |
| c1a source-record domain | rename past_race key, enforce direct finite nonnegative Decimal, bump record schema/source-ID namespace |
| historical snapshot domain | rename HistoricalPastRaceSnapshot field and canonical payload key, bump payload schema version |
| c1c builder | direct renamed-value mapping only |
| SQLite repository | renamed text column read/write only |
| migration | new guarded v011 rename migration and runner registration |
| dedicated tests | update field/payload/source-ID/version, builder, repository, v011 and migration-registry contracts |
| AbilityEngine | no change; explicitly deferred |

## Future Dedicated Test Plan

The future phase must prove exact public dataclass/API fields; rejection of margin and aliases; Decimal direct parsing
without float; finite/nonnegative/zero semantics; c1a v2 source-ID behavior; snapshot payload v2 key and digest
behavior; unchanged race_name/race_class requirements; unchanged passing_order/fourth_corner behavior; direct builder
mapping; repository round trip; exact v011 registration/order; empty-store rename success; nonempty-store atomic
failure; and no migration of historical rows.

It must also retain existing source-set validation, provenance, temporal eligibility, canonical entry/past-race/
provenance ordering, c1b-only incomplete-source rejection, SQLite atomic-save behavior, and unrelated migration
regressions. It must assert that AbilityEngine is not imported or modified as part of this domain/storage phase.

## Future Allowed Files

    scripts/simulation/historical_input_source_records.py
    scripts/simulation/historical_input_snapshots.py
    scripts/simulation/historical_input_snapshot_builder.py
    scripts/simulation/repositories/sqlite_historical_input_snapshot_repository.py
    scripts/migrations/versions/v011_historical_past_race_time_difference_schema.py
    scripts/migrations/runner.py
    tests/test_historical_input_source_records.py
    tests/test_historical_input_snapshots.py
    tests/test_historical_input_snapshot_builder.py
    tests/test_sqlite_historical_input_snapshot_repository.py
    tests/test_historical_input_snapshot_migration.py
    tests/test_simulation_migrations.py
    docs/CURRENT_PHASE.md
    docs/LATEST_CODEX_REPORT.md

No other production, test, migration, parser, provider, repository, package-root, database, log, or README file is
authorized. Any need to expand this list is REVISION_REQUIRED.

## Public Break and Follow-on Order

This is an intentional public domain break for callers that construct c1a past_race records or
HistoricalPastRaceSnapshot directly: margin is replaced by reference_time_difference_seconds. There is no runtime
compatibility mode. Stored v010 snapshots are intentionally ineligible for a semantic in-place conversion.

The recommended next phase after approval is Phase 4C-2d3b1i6c1d3b — historical past-race provenance contract
preparation. It must decide how a RaceMarkTable record can prove a single-response fact provenance, provider record
identity, and source URL without weakening the c1a model. d3a does not start d3b.

## Blockers and Stop Condition

c1d past-race implementation remains blocked by three independent prerequisites: d3a field-domain approval and
implementation; d3b provenance/identity approval; and the remaining official RaceMarkTable field evidence including
race_class, result-state, passing/corner variants, and pagination/absence proof. past_race_absence remains
UNSUPPORTED.

Stop after design review. Do not implement, stage, commit, or push without a separate explicit instruction.

blocker: historical NAR past-race normalization cannot begin until the field-domain and provenance prerequisites are
separately approved and implemented.
