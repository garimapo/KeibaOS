# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6d1a` — provider-neutral historical time/reference comparison domain preparation.

Formal base: `7b4a0f5e28311c2d64685f6d3309f68556e67f8b`.

Preparation review branch: `review/4c-2d3b1i6d1a-prepare`.

## Decision

`reference_time_difference_seconds` is not provider-neutral historical source fact.  Current c1a and snapshot
contracts require it as a nonnegative `Decimal`, but its implementation-specific meaning is NAR HorseMarkInfo's
direct displayed `差`.  The NAR normalizer does not calculate it from race times and deliberately ignores the
RaceMarkTable textual `着差`.  JRA official result pages instead expose each horse's displayed race time and a
textual margin; they do not expose the same direct decimal field.

The selected provider-neutral historical domain is therefore:

```text
required source fact: race_time (exact normalized official display text)
not a source fact: reference_time_difference_seconds
not a source fact: a derived winner/second comparison value
not a source fact: parsed official margin text
```

The existing raw official response archive/evidence preserves provider displays for later audit.  Any conversion of
official race times into a model comparison metric belongs to a later, explicitly versioned prediction adapter.  It
must not be performed by c1a, c1c, SQLite reconstruction, NAR normalization, or a future JRA source normalizer.

## Investigation Findings

### Current field semantic

`HistoricalInputSourceRecord` c1a `past_race` payload, `HistoricalPastRaceSnapshot`, the snapshot builder, SQLite
repository, and v011 currently all carry `reference_time_difference_seconds`.  The current c1a rule is exact
finite nonnegative `Decimal`; zero is allowed.  The NAR pair normalizer obtains it only from the selected
HorseMarkInfo row's direct `差`, cross-checks race time separately, and emits that value unchanged.  It does not
encode a generic winner-to-second rule.  The legacy `PastRaceInput.margin: float` / `AbilityEngine._margin_score`
path is separate legacy prediction input and is not an adapter from current historical snapshots.

### Official result semantics

The investigated ordinary NAR representative preserves a selected horse's direct HorseMarkInfo `差 = 2.6` and race
time `1:32.4`; its RaceMarkTable row displays textual `着差 = 1.1/2`.  This proves the two displayed fields are not
interchangeable.  The minimized structural fixture contains no winner row, so this preparation does not claim a
general NAR time-subtraction equivalence.  A direct displayed NAR zero remains an accepted NAR source display, not a
derived zero from finish position.

Official JRA result pages expose normal-result horse times and textual `着差`: for example the first two runners in
the investigated official result have `1:53.5` and `1:53.6`, while the winner's margin cell is blank.  Official JRA
dead-heat pages also use textual `同着` for tied result rows.  Time subtraction is arithmetically possible for some
normal rows, but it is not a direct official comparison field and cannot supply a provider-neutral winner, second,
or dead-heat policy without a separately designed rule.

## Frozen Domain Conclusions

| Decision | Frozen conclusion |
| --- | --- |
| `CURRENT_FIELD_SEMANTIC` | `NAR_HORSEMARK_DIRECT_DISPLAYED_DIFFERENCE_ONLY`; it is not a generic provider-neutral reference comparison. |
| `JRA_DIRECT_HORSE_TIME_AVAILABILITY` | `YES_FOR_INVESTIGATED_NORMAL_OFFICIAL_RESULT_ROWS`. |
| `JRA_DIRECT_WINNER_AND_SECOND_TIME_AVAILABILITY` | `YES_FOR_INVESTIGATED_NORMAL_OFFICIAL_RESULT_ROWS`; this does not define a source comparison value. |
| `JRA_DIRECT_REFERENCE_TIME_DIFFERENCE_AVAILABILITY` | `NO`. |
| `JRA_OFFICIAL_MARGIN_TEXT_AVAILABILITY` | `YES`; it is textual, including blank winner cells and `同着`. |
| `JRA_TEXTUAL_MARGIN_TO_SECONDS` | `FORBIDDEN`. |
| `HISTORICAL_DOMAIN_DERIVED_VALUES_POLICY` | `DIRECT_OFFICIAL_SOURCE_FACTS_ONLY`. |
| `NAR_DIRECT_DIFFERENCE_VS_TIME_SUBTRACTION` | `NOT_EQUIVALENT_AS_A_CONTRACT`; the direct NAR `差` and RaceMark textual margin are distinct, and no general subtraction equivalence is proven. |
| `JRA_TIME_SUBTRACTION_STATUS` | `DETERMINISTIC_ARITHMETIC_IN_SOME_NORMAL_ROWS_BUT_NOT_AN_APPROVED_SOURCE_FACT`. |
| `RACE_TIME_DOMAIN_STATUS` | `REQUIRED_NORMALIZED_OFFICIAL_TEXT_ONLY`; no new decimal-seconds field is added. |
| `WINNER_COMPARISON_SEMANTIC` | `NONE_IN_SOURCE_DOMAIN`. |
| `DEAD_HEAT_SEMANTIC` | `NO_DERIVED_SOURCE_COMPARISON_VALUE`; preserve the official time/text in raw evidence only. |
| `OFFICIAL_MARGIN_TEXT_POLICY` | `RAW_OFFICIAL_EVIDENCE_ONLY_NOT_C1A_PAST_RACE_PAYLOAD`. |
| `SOURCE_FACT_VS_MODEL_FEATURE_SEPARATION` | `REQUIRED`; a future adapter owns any comparison formula and its versioned policy. |
| `RECOMMENDED_HISTORICAL_PAST_RACE_DOMAIN` | `RACE_TIME_ONLY_FOR_TIME_RELATED_SOURCE_FACTS`; remove `reference_time_difference_seconds`. |

## Required Contract Migration

This decision requires a deliberate historical-source contract evolution before any JRA past-race normalizer is
implemented:

```text
HistoricalInputSourceRecord.schema_version: 3 -> 4
source-id namespace: his-v3 -> his-v4
HistoricalInputSnapshot.schema_version: 3 -> 4
past_race source/snapshot/SQLite key: remove reference_time_difference_seconds
```

The proposed v013 migration is empty-store only, matching v011/v012's fail-closed policy.  It must reject a
nonempty `historical_input_snapshots` store before every schema mutation; it must not reinterpret old NAR direct
differences as a new provider-neutral quantity, dual-read, dual-write, alias, coerce, or synthesize a replacement.
On an empty store it will remove the obsolete SQLite field through the SQLite-safe schema migration chosen in the
implementation design.  Old v011/v012 migrations remain unchanged.

The legacy `PastRaceInput.margin` and `AbilityEngine` remain unchanged in this phase and d1a1.  There is currently
no valid snapshot-to-prediction adapter for the new source contract:

```text
TIME_DIFFERENCE_TO_PREDICTION_ADAPTER_STATUS = CONTRACT_GAP
```

The later adapter must be a separate phase and must choose, document, and test its own normal-result, winner,
second-place, dead-heat, precision, and textual-margin policy.  It cannot silently consume the legacy float-margin
parser or invent a value from `race_time`.

## Compatibility and Scope Decisions

```text
C1A_SCHEMA_CHANGE_REQUIRED = YES
SNAPSHOT_SCHEMA_CHANGE_REQUIRED = YES
SQLITE_MIGRATION_REQUIRED = YES
NAR_SOURCE_CHANGE_REQUIRED = YES
JRA_PAST_RACE_DOMAIN_COMPATIBILITY = YES_AFTER_D1A1
BUILDER_CHANGE_REQUIRED = YES
```

`NAR_SOURCE_CHANGE_REQUIRED` means only removal of the NAR-only direct-difference payload mapping after the c1a
contract changes.  It does not alter NAR raw-response evidence, HorseMarkInfo/RaceMarkTable linkage, field authority
for other facts, historical causality, capture, discovery, or absence proof.  It does not authorize JRA parsing.

The JRA result investigation is sufficient to select a common time-source domain, but it does not approve JRA
identity, capture, history discovery, odds, or normalization implementation.  Those remain separate d1 phases.

### Persisted-composition blockers

`scripts/prediction/ability_engine.py` and `scripts/prediction/jockey_engine.py` each default their
`reference_date` to `date.today()` and use it to exclude future races.  In
`scripts/simulation/persisted_simulation_application_inputs.py`, the sole persisted pipeline date is
`track_reference_date`; it is injected only into `TrackEngine`.  `PipelineConfig` therefore default-constructs
AbilityEngine and JockeyEngine with the runtime date.  A historical persisted simulation can consequently evaluate
ability and jockey inputs with a future reference date.

```text
ABILITY_REFERENCE_DATE_STATUS = FUTURE_LEAKAGE_BLOCKER_IN_CURRENT_PERSISTED_COMPOSITION
JOCKEY_REFERENCE_DATE_STATUS = FUTURE_LEAKAGE_BLOCKER_IN_CURRENT_PERSISTED_COMPOSITION
```

These are independently real prediction-composition blockers, not reasons to distort the historical source domain.
They are explicitly out of scope for d1a and d1a1 and require a later prediction-composition phase.

## Future Implementation Phase

Recommended next phase:

```text
4C-2d3b1i6d1a1 — provider-neutral historical race-time domain implementation
```

It must complete before d1d prediction-adapter work.  It is logically independent of JRA capture/identity
investigation.  `d1b` identity-bridge PREPARE may proceed independently because it does not consume the time field,
but JRA result normalization must wait for d1a1 so it never targets the rejected field.

Proposed allowed files for d1a1 are exactly:

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
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

It must not change legacy parsers, `PastRaceInput`, AbilityEngine, provider acquisition, JRA production code,
fixtures, package exports, database data, or logs.  Its required test plan includes source-ID/snapshot digest schema
evolution, exact race-time preservation, absence of the removed key everywhere, v013 nonempty-store pre-mutation
failure and empty-store success, NAR regression without a derived difference, SQLite round-trip, and proof that no
prediction adapter has been introduced.

## Stop Condition

This is PREPARE only.  No production code, test, fixture, migration, SQLite database, capture archive, JRA
normalizer, prediction adapter, or acquisition work is authorized.  Stop after the docs-only review commit and
independent design review.
