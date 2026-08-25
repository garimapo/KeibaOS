# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase

`4C-2d3b1i6d1d5f1c4f1` — Historical input snapshot -> SimulationRaceInput adapter.

Formal base: `53d85e8a5228fa7b8bef47dab4e74f9d3d1ce115`.

Review branch:
`review/4c-2d3b1i6d1d5f1c4f1-historical-snapshot-simulation-adapter-prepare`.

C4f1 is the direct formal successor to completed c4f0. C4f0 aligned the prediction
contract to the causally reproducible marginless model; c4f1 now performs only the pure
data conversion from one exact `HistoricalInputSnapshot` into one exact
`SimulationRaceInput`.

## Purpose and Boundary

The adapter receives one already validated immutable snapshot and returns one immutable
simulation race input. It owns no acquisition, persistence, selection, prediction
execution, clock, or fallback:

```text
HistoricalInputSnapshot
-> ImmutableRacePredictionInput
-> InputSnapshotAudit
-> SimulationRaceInput
```

Freeze:

```text
SNAPSHOT_ONLY_INPUT: YES
DATABASE_READ: NO
DATABASE_WRITE: NO
REPOSITORY: NO
PROVIDER: NO
LIVE_HTTP: NO
CURRENT_CLOCK: NO
FILESYSTEM: NO
RANDOM: NO
LEGACY_RACE_LOOKUP: NO
LEGACY_HORSE_LOOKUP: NO
LEGACY_PAST_RACE_LOOKUP: NO
NAME_MAPPING: NO
RESULT_LOOKUP: NO
PAYOUT_LOOKUP: NO
SETTLEMENT_LOOKUP: NO
PREDICTION_EXECUTION: NO
HISTORICAL_PIPELINE_FACTORY_CALL: NO
```

## Public Surface

Create:

```text
scripts/simulation/historical_input_snapshot_simulation_adapter.py
```

Its module-local public surface is exactly:

```python
__all__ = (
    "HistoricalInputSnapshotSimulationAdapterError",
    "build_simulation_race_input_from_historical_snapshot",
)

class HistoricalInputSnapshotSimulationAdapterError(ValueError):
    ...

def build_simulation_race_input_from_historical_snapshot(
    *,
    snapshot: HistoricalInputSnapshot,
) -> SimulationRaceInput:
    ...
```

No package-root export is required. The function accepts no collaborator, repository,
provider, strategy, pipeline, clock, or decomposed snapshot argument.

Require `type(snapshot) is HistoricalInputSnapshot`. A subclass, mapping, raw record,
or reconstructed compatibility shape fails with
`HistoricalInputSnapshotSimulationAdapterError` before conversion.

The one adapter-owned error class also owns explicit Decimal conversion failures. It
does not catch or translate `SimulationValidationError`, destination-domain
`ValueError`/`TypeError`, or any other exception. No broad `Exception` or
`BaseException` catch is allowed.

## SimulationRaceInput Mapping

Every destination field is explicit:

```text
SimulationRaceInput.race_id
    <- snapshot.internal_race_id

SimulationRaceInput.target_race_date
    <- snapshot.race.target_race_date

SimulationRaceInput.scheduled_start_at
    <- snapshot.race.scheduled_start_at

SimulationRaceInput.information_cutoff
    <- snapshot.information_cutoff

SimulationRaceInput.pipeline_input
    <- directly constructed exact ImmutableRacePredictionInput

SimulationRaceInput.input_snapshot_audit
    <- deterministic conversion of snapshot.provenance
```

The returned object must pass the unchanged `SimulationRaceInput.__post_init__` and
`validate_simulation_race_input(...)` boundary.

## Canonical Entity and Entry Order

The formal prediction entity key is the exact internal race-entry ID:

```text
PREDICTION_ENTITY_KEY: HistoricalRaceEntrySnapshot.race_entry_id
PAST_RACE_HORSE_ID_SEMANTICS: EXACT_INTERNAL_RACE_ENTRY_ID_ALIAS
```

The legacy prediction field name `PastRaceSnapshot.horse_id` is a semantic alias at this
boundary and receives `HistoricalPastRaceSnapshot.race_entry_id`. It does not mean
`horse_no`, external horse identity, or a separately resolved legacy horse row.

The adapter sorts entries by ascending `entry_order`, which the snapshot domain proves
is contiguous `0..N-1`. It constructs `horse_past_races`,
`jockey_names_by_horse`, and `odds_by_horse` in that same order. It never relies on the
incidental order of `snapshot.entries`.

For each entry, past races are selected by exact `race_entry_id` and sorted by ascending
`past_race_index`, which the snapshot proves is contiguous `0..N-1`. No date/name/finish
sort is allowed. An entry with no past races receives an empty tuple; no fake race is
created.

Freeze:

```text
ENTRY_ITERATION_ORDER: ASCENDING_CONTIGUOUS_ENTRY_ORDER
PAST_RACE_ORDER: ASCENDING_CONTIGUOUS_PAST_RACE_INDEX_PER_RACE_ENTRY_ID
```

## Immutable Prediction Input

Construct exact `ImmutableRacePredictionInput` directly. Do not construct
`RacePredictionInput` or `scripts.models.PastRace` first.

Its fields are:

```text
horse_past_races
    <- entry-order mappings to tuples of directly constructed PastRaceSnapshot

jockey_names_by_horse[entry.race_entry_id]
    <- entry.jockey

track_conditions
    <- directly constructed TrackConditionsSnapshot(
           place=snapshot.race.place,
           distance=snapshot.race.distance_m,
           track=snapshot.race.track,
           track_condition=snapshot.race.track_condition,
       )

odds_by_horse[entry.race_entry_id]
    <- checked float conversion of entry.win_odds

race_horse_count
    <- len(snapshot.entries)

race_id
    <- snapshot.internal_race_id

prediction_time
    <- snapshot.information_cutoff.isoformat(timespec="microseconds")
```

Target-race weather is not part of `TrackConditionsSnapshot`. No current track or jockey
lookup and no text normalization beyond the formal snapshot value is permitted.

`PredictionPipeline.run` forwards `prediction_time` as a string and does not parse or
replace it. C4f1 does not execute the pipeline. The formal timestamp is the prediction
information boundary, not capture time, scheduled start, persistence time, or execution
time:

```text
PREDICTION_TIME_SOURCE: SNAPSHOT_INFORMATION_CUTOFF
PREDICTION_TIME_FORMAT: UTC_ISO8601_MICROSECONDS_WITH_PLUS_00_00
PREDICTION_TIME_EXAMPLE: 2026-08-05T12:30:00.000000+00:00
```

## PastRaceSnapshot Field Mapping

Construct each immutable past race directly with the exact mapping:

```text
horse_id                 <- item.race_entry_id
race_date                <- item.race_date.isoformat()
place                    <- item.place
race_name                <- item.race_name
race_class               <- item.race_class
distance                 <- item.distance_m
track                    <- item.track
weather                  <- item.weather
track_condition          <- item.track_condition
finish                   <- item.finish
time                     <- item.race_time
weight                   <- checked Decimal -> float(item.weight)
weight_diff              <- checked Decimal -> float(item.weight_diff)
jockey                   <- item.jockey
popularity               <- item.popularity
odds                     <- checked Decimal -> float(item.odds)
passing_order            <- item.passing_order
fourth_corner_position   <- item.fourth_corner_position
```

There is no margin and no replacement performance field.

## Decimal to Float Contract

Use one private pure conversion helper with an exact `Decimal` input and a field-specific
positivity policy. It performs `float(value)` directly with no decimal rounding, string
round trip, or fixed decimal places. It fails with
`HistoricalInputSnapshotSimulationAdapterError` when:

- the input type is not exact `Decimal`;
- conversion raises a narrow numeric conversion error;
- the converted value is non-finite;
- a nonzero Decimal converts to `0.0`;
- a positive Decimal converts to a non-positive float;
- a negative Decimal converts to a non-negative float; or
- the field-specific positive/non-negative rule is violated.

Zero is canonical in the formal snapshot, so signed-zero ambiguity is not retained.

Field rules are:

```text
WIN_ODDS_CONVERSION:
EXACT_DECIMAL_TO_FINITE_POSITIVE_FLOAT; OVERFLOW_UNDERFLOW_SIGN_LOSS_FAIL_CLOSED

PAST_ODDS_CONVERSION:
EXACT_DECIMAL_TO_FINITE_NON_NEGATIVE_FLOAT; ZERO_ALLOWED;
NONZERO_UNDERFLOW_AND_SIGN_LOSS_FAIL_CLOSED

WEIGHT_CONVERSION:
EXACT_DECIMAL_TO_FINITE_NON_NEGATIVE_FLOAT; ZERO_ALLOWED;
NONZERO_UNDERFLOW_AND_SIGN_LOSS_FAIL_CLOSED

WEIGHT_DIFF_CONVERSION:
EXACT_DECIMAL_TO_FINITE_SIGN_PRESERVING_FLOAT; ZERO_ALLOWED;
NONZERO_UNDERFLOW_AND_SIGN_LOSS_FAIL_CLOSED
```

Ordinary deterministic binary-float approximation is accepted only as computation
representation. The exact Decimal in the immutable snapshot and its `content_sha256`
remain the audit truth.

## Audit Conversion

One exact `HistoricalInputProvenance` becomes exactly one `InputAuditEntry`. Preserve
without rewriting:

```text
input_type
audit_key
source
source_id
race_entry_id
past_race_index
```

The evidence timestamp reduction is conservative and order-independent:

```text
observed_at = max(evidence.observed_at for evidence in provenance.evidence)

available_at = None
    if any(evidence.available_at is None for evidence in provenance.evidence)
    else max(evidence.available_at for evidence in provenance.evidence)
```

Choosing maximum observed time cannot hide the latest required observation. Unknown
availability stays unknown. When all availability values are known, their maximum is
conservative. Because each known `available_at <= observed_at`, the reduced known
available time is no later than the reduced observed time. The snapshot already proves
every evidence timestamp is no later than `captured_at`, and
`captured_at <= information_cutoff`, so the reduced pair remains causal.

Do not substitute observed time, captured time, or cutoff for an unknown availability.

Freeze:

```text
AUDIT_OBSERVED_AT_REDUCTION: MAXIMUM_REQUIRED_EVIDENCE_OBSERVED_AT
AUDIT_AVAILABLE_AT_REDUCTION: NONE_IF_ANY_UNKNOWN_ELSE_MAXIMUM_REQUIRED_EVIDENCE_AVAILABLE_AT
```

## Canonical Audit Order and Header

Do not rely on incidental `snapshot.provenance` tuple order. Build an exact lookup by
`audit_key`, then emit:

```text
for each entry in ascending entry_order:
    entry/{race_entry_id}
    odds/{race_entry_id}
    jockey/{race_entry_id}
    if the entry has no past races:
        past_race/{race_entry_id}/none
    else:
        past_race/{race_entry_id}/0
        past_race/{race_entry_id}/1
        ...
then:
    track
```

The formal snapshot already proves this exact key set and past-race/absence XOR. Missing,
extra, contradictory, or duplicate material is never repaired.

Construct the audit header as:

```text
dataset_id  <- snapshot.identity.dataset_id
source      <- snapshot.identity.source_identity.source_system
captured_at <- snapshot.identity.captured_at
entries     <- canonical audit entries above
is_complete <- True
```

`InputSnapshotAudit.source` is the source system of the complete race-level snapshot;
each `InputAuditEntry.source` independently preserves the exact provenance source.

`is_complete=True` is justified only by the exact `HistoricalInputSnapshot` constructor,
which has already proven track, nonempty entries, jockey and target odds for every entry,
past races or formal absence, complete provenance keys, contiguous ordering, and causal
evidence. The adapter does not fill missing data or synthesize audit records.

## Validation and Determinism

The returned `SimulationRaceInput` must pass unchanged validation proving:

- race and pipeline race IDs agree;
- captured time is no later than information cutoff;
- audit completeness and all required categories;
- no missing or unknown audit key;
- audit key/type/entry/index metadata equality;
- every past race date precedes target race date; and
- every reduced audit timestamp is no later than information cutoff.

No validation weakening or exception translation is allowed.

Canonical sorting and order-independent evidence reduction guarantee:

```text
same exact snapshot content
-> equal SimulationRaceInput
```

This remains independent of process date, process restart, database state, later
snapshots, later archive enrichment, incidental tuple/dict/evidence order, results, and
payouts. The adapter has no latest selector.

## C4f0 and Scope Preservation

C4f1 does not change `PastRaceInput`, `PastRaceSnapshot`, `AbilityEngine`,
`build_historical_prediction_pipeline`, JockeyEngine, TrackEngine, or ValueEngine. It
does not change the historical snapshot domain, simulation validation, schema, or any
migration.

Future implementation files are exactly:

```text
scripts/simulation/historical_input_snapshot_simulation_adapter.py
tests/test_historical_input_snapshot_simulation_adapter.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

No other production file is required.

## Future Test Matrix

The dedicated future test must pin:

- exact module `__all__`, error class, and keyword-only function signature;
- exact `HistoricalInputSnapshot` input type and rejection before conversion;
- one and multiple entries in ascending `entry_order`;
- exact internal `race_entry_id` keys across all mappings;
- `horse_no`, external IDs, names, and numeric coincidence never used as keys;
- zero history to empty tuple and exact `/none` provenance;
- past races in ascending `past_race_index` regardless of source tuple order;
- every direct `PastRaceSnapshot` field mapping and absence of margin;
- direct exact `ImmutableRacePredictionInput` construction;
- exact track and jockey mapping;
- checked target odds, past odds, weight, and signed weight-difference conversion;
- overflow, non-finite result, nonzero underflow, and sign loss fail closed;
- accepted deterministic binary-float approximation with Decimal audit truth unchanged;
- exact race count, race ID, target date, scheduled start, and cutoff;
- exact UTC microsecond prediction-time string;
- exact provenance metadata preservation;
- single evidence, observed maximum, unknown availability, and all-known availability;
- evidence-order-independent reduction;
- canonical audit entry order and formal absence placement;
- exact source-system audit header and `is_complete=True` justification;
- final unchanged `SimulationRaceInput` validation;
- equivalent/reordered snapshot content produces equal output;
- restart and later-snapshot independence;
- no database, repository, provider, HTTP, clock, filesystem, random, legacy lookup,
  name mapping, result/payout/settlement, prediction execution, or historical factory;
- no broad exception catch or package-root export; and
- c4f0 production files remain unchanged.

## Readiness

```text
PUBLIC_ADAPTER_API_READY: YES
FIELD_MAPPING_READY: YES
ENTITY_IDENTITY_READY: YES
ORDERING_READY: YES
DECIMAL_CONVERSION_READY: YES
PREDICTION_TIMESTAMP_READY: YES
MULTI_EVIDENCE_AUDIT_REDUCTION_READY: YES
AUDIT_SOURCE_READY: YES
ERROR_POLICY_READY: YES
IMPLEMENTATION_READY: YES_AFTER_INDEPENDENT_APPROVAL
BLOCKERS: NONE
```

No production code, tests, pytest, live HTTP, or real trusted capture were performed.

## Allowed Files for This PREPARE

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Forbidden Files for This PREPARE

All production, tests, repositories, providers, schemas, migrations, c4f0, c4d, c4e,
prediction execution, CLI, JRA acquisition, NAR, live capture, betting, settlement, and
package-root files.

## Required PREPARE Checks

```text
git diff --check
git status --short
changed-file scope == the two allowed docs
```

No pytest or HTTP is required for this docs-only PREPARE.

## Stop Condition

Commit and push the single docs-only PREPARE review commit, then stop for independent
review. Do not implement c4f1 and do not modify the formal branch.
