# Current Phase

## Status

READY_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6d1a1` — provider-neutral historical race-time domain implementation.

Formal base: `7b4a0f5e28311c2d64685f6d3309f68556e67f8b`.

Implementation review branch: `review/4c-2d3b1i6d1a1-implementation`.

Approved preparation: `bcac7efbc6eb0ff149100225cbc1e6e53910d0cf`.

## Implemented Source Contract

```text
C1A_SCHEMA_VERSION = 4
SOURCE_ID_NAMESPACE = his-v4
SNAPSHOT_SCHEMA_VERSION = 4
GLOBAL_MIGRATION_FINAL_VERSION = 13
REFERENCE_TIME_DIFFERENCE_SOURCE_FIELD = REMOVED
RACE_TIME_SOURCE_FIELD = RETAINED_EXACT_TEXT
HISTORICAL_DOMAIN_DERIVED_VALUES_POLICY = DIRECT_OFFICIAL_SOURCE_FACTS_ONLY
TIME_DIFFERENCE_TO_PREDICTION_ADAPTER_STATUS = CONTRACT_GAP
```

All six c1a record kinds now construct source IDs in the exact `his-v4:{record_kind}:{sha256}` namespace. This is
intentional global source-ID churn; no v3 payload mode, alias, compatibility read, or dual-write exists.

`past_race` now contains exactly the retained official factual fields, including required NFC-normalized `race_time`
text and excluding `reference_time_difference_seconds`. `HistoricalPastRaceSnapshot`, the builder, canonical
snapshot payload, digest, and SQLite repository likewise contain no comparison field, property alias, default, or
fallback. Snapshot canonical payload schema version is 4.

The NAR pair normalizer retains the exact official race-time display (the representative result remains `1:32.4`) and
unchanged two-response evidence roles, raw-byte SHA-256, and timestamp semantics. HorseMarkInfo direct `差` is no
longer a factual c1a output key. Changing that raw response bytes still changes evidence SHA and therefore source ID;
it does not reintroduce a comparison fact.

## Migration

`v013_historical_past_race_race_time_domain_schema` is registered after v012. It removes
`reference_time_difference_seconds_text` only when `historical_input_snapshots` is empty. A nonempty store raises
before schema mutation, leaves v013 unapplied, and retains the old column. Identity and linkage rows may remain and
are preserved. v011 and v012 are unchanged.

The dedicated NAR capture migration registry and schema remain separate and unchanged. The global registry is exactly
`(8, 9, 10, 11, 12, 13)`; v013 is not registered in the dedicated capture runner.

## Explicitly Unchanged and Out of Scope

No legacy `PastRace.margin` adapter, AbilityEngine, JockeyEngine, JRA normalizer, JRA capture, prediction feature,
time subtraction, winner/second comparison, textual-margin conversion, provider acquisition, discovery, absence
logic, package export, database data, or logs changed.

```text
ABILITY_REFERENCE_DATE_STATUS = FUTURE_LEAKAGE_BLOCKER_IN_CURRENT_PERSISTED_COMPOSITION
JOCKEY_REFERENCE_DATE_STATUS = FUTURE_LEAKAGE_BLOCKER_IN_CURRENT_PERSISTED_COMPOSITION
```

## Allowed Files

```text
scripts/simulation/historical_input_source_records.py
scripts/simulation/historical_input_snapshots.py
scripts/simulation/historical_input_snapshot_builder.py
scripts/simulation/repositories/sqlite_historical_input_snapshot_repository.py
scripts/migrations/runner.py
scripts/migrations/versions/v013_historical_past_race_race_time_domain_schema.py
scripts/simulation/nar_historical_past_race_source.py
tests/test_historical_input_source_records.py
tests/test_historical_input_snapshots.py
tests/test_historical_input_snapshot_builder.py
tests/test_sqlite_historical_input_snapshot_repository.py
tests/test_historical_input_snapshot_migration.py
tests/test_simulation_migrations.py
tests/test_simulation_bet_plan_migration.py
tests/test_sqlite_persisted_simulation_application.py
tests/test_nar_historical_past_race_source.py
tests/test_nar_historical_input_source.py
tests/test_nar_historical_past_race_absence_source.py
tests/test_nar_official_response_capture_migration.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Verification and Stop Condition

Python 3.14.5 / pytest 8.3.5 verification passed: capture migration 8, core d1a1 targeted suite 82, related
migration/source suite 93, and full suite 2523. Stop for independent implementation review. Do not integrate formal
or begin d1b.
