# Current Phase

## Status

READY_FOR_REVIEW

## Phase

Phase 4C-2d3b1i6c1d3a - Historical past-race field-domain contract implementation

## Base Commit

2b6d389b4296be2f6749b71fc4ed827f244ce570 feat: preserve NAR target horse identity

## Branch and Workspace

Formal branch: feature/ver0.8-simulator

Implementation review branch: review/4c-2d3b1i6c1d3a-implementation

Canonical workspace: C:\Users\garim\Desktop\KeibaAI-review-1i5b2b

The original workspace, C:\Users\garim\Desktop\KeibaAI, is read-only for this phase.

## Objective and Scope

d3a implements the approved field-domain contract only. It changes the listed historical domain, builder, SQLite
repository, append-only migration, dedicated tests, and these documents. Providers, parsers, legacy models,
AbilityEngine, database data, README, CLI, package exports, logs, and the original workspace remain read-only.

d3a replaces the ambiguous historic past-race field margin with reference_time_difference_seconds. It does not
normalize official responses, derive values, or introduce a compatibility path.

## Approved Official Field Semantics

Official NAR HorseMarkInfo history displays a separate column named 差. Official CompeteTable describes that value as
the time difference from the winner, or for the winner, the time difference to second. The required field is:

    reference_time_difference_seconds: Decimal

It is the direct official time difference in seconds: nonwinner to first and winner to second. It is not a
horse-length margin, a signed deficit, RaceMarkTable 着差, or a value inferred from race times. HorseMarkInfo
separately provides the required official 競走名 (race_name) and 格組 (race_class).

## Exact Decimal Contract

Only a direct provider value parsed as a finite Decimal is permitted. It is nonnegative; zero is valid only when
the official display directly supplies zero. int, float, bool, NaN, infinity, blank text, dash/unavailable display
markers, negatives, aliases, inferred values, legacy-parser mappings, and derived time differences fail closed. No
float conversion is permitted. Canonical Decimal formatting remains the committed canonical formatting rule.

Normal completed-row support remains conditional on direct official evidence for every other required c1a past-race
field. Abnormal, unavailable, or nonnumeric official displays are unsupported and are never converted to 0, None, an
empty string, or a guess.

## Frozen Field Contract

| Concern | Frozen decision |
| --- | --- |
| New field | reference_time_difference_seconds: Decimal |
| Meaning | direct official NAR time difference in seconds |
| Legacy margin | removed from new c1a, snapshot, SQLite, and canonical-payload contracts |
| Alias behavior | margin, both names, a default, dual-read, and dual-write are rejected |
| race_name | unchanged required nonempty HorseMarkInfo 競走名 |
| race_class | unchanged required nonempty HorseMarkInfo 格組; never RaceMarkTable h3 or a subtitle |
| passing_order | unchanged in d3a |
| fourth_corner_position | unchanged in d3a |

## Global c1a Union-schema Versioning

HistoricalInputSourceRecord has one public schema_version field, one canonical payload shape, and one globally
hardcoded his-v1 source-ID namespace across the union of track, entry, jockey, odds_win, past_race, and
past_race_absence. The incompatible past_race record_values change therefore versions the complete c1a union
contract, not an individual provider page or record kind.

The frozen decision is:

    GLOBAL_C1A_SCHEMA_VERSION = 2

After d3a implementation every newly constructed c1a record is version 2:

    track.schema_version == 2
    entry.schema_version == 2
    jockey.schema_version == 2
    odds_win.schema_version == 2
    past_race.schema_version == 2
    past_race_absence.schema_version == 2

Every v2 source ID uses:

    his-v2:{record_kind}:{sha256}

Consequently even semantically unchanged track, entry, jockey, odds_win, and past_race_absence records have new v2
canonical payloads and source IDs relative to v1. This is intentional version identity, not accidental hash churn.
Mixed record versions such as track v1 and past_race v2 are forbidden.

The earlier d1 source-ID isolation rule remains true within a single schema version: changing only one entry lineage
changes only that entry payload/source ID. The one-time his-v1 to his-v2 transition is separate and intentionally
changes every newly emitted c1a record kind.

Future d3a tests must prove all six kinds have schema_version 2; every source ID has the matching his-v2 kind prefix;
canonical payloads contain schema_version 2; deterministic rebuilding is stable; no v2 record uses his-v1; a
past-race-only content mutation still leaves unrelated v2 records unchanged; and existing record-set conflict
behavior is unchanged. The existing public-contract assertion of default schema_version 1 changes intentionally.

## Snapshot Contract Versioning

HistoricalPastRaceSnapshot replaces margin: Decimal with reference_time_difference_seconds: Decimal. The
HistoricalInputSnapshot canonical content payload replaces the past_races key and changes its hardcoded
schema_version from 1 to 2. All new snapshots after d3a are v2 payloads and use the committed snapshot-domain
content_sha256 calculation. No v1 digest is represented as equivalent to a v2 payload.

## SQLite v011 Strategy and Old-data Policy

v010 contains historical_input_snapshot_past_races.margin_text TEXT NOT NULL and no margin index. The future v011
migration is append-only and fail-closed:

1. It first checks SELECT COUNT(*) FROM historical_input_snapshots.
2. If the count is nonzero, it aborts before every schema mutation and v011 is not recorded.
3. If the count is zero, it may rename margin_text to reference_time_difference_seconds_text.
4. Dedicated migration tests must prove empty-store success and nonempty-store atomic failure.

No old margin value is copied, converted, deleted, silently invalidated, or reinterpreted as seconds. The guard is
against historical_input_snapshots rows because they carry v1 snapshot semantic payload/digest contracts, including
snapshots with no past-race child rows.

Existing rows in historical_input_source_identities, historical_input_external_races, and
historical_input_external_entries are allowed when historical_input_snapshots is empty. They are provider
identity/linkage mappings, not persisted v1 snapshot semantic payloads; v011 neither rewrites nor destroys them.

## Builder, Repository, and Ability Boundaries

The future builder maps only the renamed c1a record value into the renamed snapshot field. It does not derive a time
difference or change source grouping, mapping, ordering, provenance, captured_at, or cutoff semantics. The SQLite
repository changes only its child-column serialization/deserialization while preserving immutable save/load behavior.

Legacy models, database, parser, fetch path, and persisted simulation adapters still use legacy margin semantics.
They are untrusted and out of scope; they provide no fallback or conversion rule.

AbilityEngine consumes only legacy PastRace.margin float and does not receive HistoricalPastRaceSnapshot directly.
ABILITY_ENGINE_CHANGE_REQUIRED = LATER_FEATURE_PHASE. d3a must not wire seconds into legacy margin scoring, change
coefficients, or adapt seconds to old semantics.

## Multi-source Evidence Prerequisite

d3 established SINGLE_RESPONSE_COMPLETE_SOURCE = NO, MULTI_RESPONSE_EVIDENCE_REQUIRED = YES, and
C1A_PROVENANCE_EXTENSION_REQUIRED = YES. d3a does not reopen a single-response RaceMarkTable design.

The currently required logical factual evidence set is HorseMarkInfo plus RaceMarkTable. HorseMarkInfo and
RaceMarkTable roles, immutable evidence references, evidence ordering, per-response observed_at/available_at, cutoff
eligibility, provider_record_id, post-extension canonical_source_url semantics, persistence, and source-ID impact
belong to d3b. CompeteTable was semantic-reference evidence only and must not become a required factual evidence
reference or digest input merely for that reason.

## Remaining Provider-normalizer Evidence Work

race_name and race_class are already frozen to HorseMarkInfo and are not remaining RaceMarkTable blockers.
FOURTH_CORNER_CHANGE = NO. Remaining future provider-normalizer evidence work includes exact result-state support;
HorseMarkInfo historical-row identity linkage; historical odds; passing order; corner-label mapping; supported
weight/time/popularity variants; abnormal-state rejection; and historical race-identity cross-check. Pagination and
past_race_absence remain separate fail-closed work; past_race_absence is UNSUPPORTED.

## Future Implementation Impact

| Area | Required future change |
| --- | --- |
| c1a source-record domain | global v2, his-v2 namespace, renamed past_race key, direct Decimal validation |
| historical snapshot domain | renamed field/key and canonical content payload v2 |
| c1c builder | direct renamed-value mapping only |
| SQLite repository | renamed text-column read/write only |
| migration | guarded append-only v011 and runner registration |
| dedicated tests | global c1a v2, snapshot v2, builder, repository, v011 and registry contracts |
| AbilityEngine | no change; deferred feature phase |

## Future Dedicated Test Plan

The future phase must prove exact public fields; rejection of margin/aliases; direct finite/nonnegative Decimal
semantics without float; all-six-kind global c1a v2 schema/payload/source-ID behavior; within-v2 record isolation;
unchanged record-set conflicts; snapshot payload v2; unchanged race_name/race_class; unchanged passing/fourth-corner;
builder mapping; repository round trip; v011 order; empty-store rename; nonempty snapshot atomic failure; and
retention of identity/linkage rows when no snapshots exist.

It must retain existing source-set, provenance, temporal eligibility, canonical ordering, c1b-only incomplete-source,
SQLite atomic-save, and unrelated migration regressions. It must assert that AbilityEngine is neither imported nor
modified by this domain/storage phase.

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

No c1b production change is required. No other production, test, migration, parser, provider, package-root,
database, log, or README file is authorized. A scope expansion is REVISION_REQUIRED.

## Public Break and Follow-on Order

This is an intentional public break: margin becomes reference_time_difference_seconds with no compatibility mode.
Stored v010 snapshots are ineligible for semantic in-place conversion.

The exact next phase after d3a implementation is Phase 4C-2d3b1i6c1d3b - Historical multi-source
evidence/provenance contract preparation. It does not implement a single-response provenance path and d3a does not
start it.

## Blockers and Stop Condition

Historical NAR past-race normalization remains blocked by d3a implementation, d3b multi-source provenance/identity
design, and provider-normalizer evidence work listed above. past_race_absence remains UNSUPPORTED.

Implementation is complete and stopped at READY_FOR_REVIEW pending independent ChatGPT code review. Do not commit to
or integrate the formal branch without separate explicit authorization.

blocker: historical NAR past-race normalization awaits d3b multi-source evidence/provenance design and remaining provider evidence work.

## Implementation Result

The approved implementation applies global c1a schema version 2 and the his-v2 source-ID namespace for every
new record kind; it replaces the past-race source/snapshot field and canonical snapshot payload with
reference_time_difference_seconds; and it adds guarded v011. v011 rejects a nonempty historical_input_snapshots
store before mutation, while preserving identity/linkage rows when that snapshot store is empty.

The builder and SQLite repository use only the renamed exact Decimal field. No legacy margin fallback, source
parser, provider, network, filesystem, clock, AbilityEngine, PaceEngine, or fourth-corner behavior was changed.

The explicitly approved scope extension updated only the two stale global migration-registry expectation test files.
External Python 3.14.5 / pytest 8.3.5 verification now passes: added bet-plan regression 17, added persisted
application regression 8, d3a targeted suites 96, and full suite 2450. Status is READY_FOR_REVIEW pending
independent ChatGPT code review.
