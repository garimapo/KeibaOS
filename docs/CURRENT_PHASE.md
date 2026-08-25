# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase

`4C-2d3b1i6d1d5f1c4f` — Historical input snapshot -> simulation/prediction adapter.

Formal base: `48dde0f5a5d1cce0176b578ccfcc87dbd9fc1fac`.

Review branch:
`review/4c-2d3b1i6d1d5f1c4f-historical-snapshot-simulation-adapter-prepare`.

The phase ID is the unoccupied successor already reserved by c4e for the pure
snapshot-to-prediction/simulation handoff. It does not conflict with the existing phase
hierarchy. Investigation found that the parent phase must be split before implementation:

```text
4C-2d3b1i6d1d5f1c4f0
    formal historical prediction-contract alignment

4C-2d3b1i6d1d5f1c4f1
    pure HistoricalInputSnapshot -> SimulationRaceInput adapter
```

The immediate implementation phase is c4f0. C4f1 remains blocked until c4f0 is formally
complete.

## Existing Boundary and Blocking Finding

An exact persisted `HistoricalInputSnapshot` now contains every target-race, entry,
odds, jockey, past-race-or-absence, provenance, and causal timestamp fact required by
the intended adapter except one current prediction-contract field:
`PastRaceInput.margin`.

`HistoricalPastRaceSnapshot` and formal past-race source records deliberately contain
no margin. Migration history removed `margin_text`, renamed the former comparison field
to `reference_time_difference_seconds_text`, and later removed that field too. The JRA
normalizer may inspect a display margin to reject an unsupported dead heat, but it does
not retain an exact numeric margin fact. That transient validation read is not a formal
source-record or snapshot value and cannot be reparsed or promoted by this adapter.

The current prediction side nevertheless requires `margin: float` in `PastRaceInput`
and `PastRaceSnapshot`. `AbilityEngine` reads it both for eligibility and for a non-zero
15-percent score component. The snapshot therefore cannot satisfy the current
`PredictionPipelineInput` contract without inventing data.

The following are forbidden:

```text
SYNTHETIC_MARGIN_ALLOWED: NO
MARGIN_ZERO_DEFAULT_ALLOWED: NO
MARGIN_NAN_SENTINEL_ALLOWED: NO
LEGACY_DB_MARGIN_LOOKUP_ALLOWED: NO
RAW_HTML_REPARSE_ALLOWED: NO
RACE_TIME_AS_MARGIN_ALLOWED: NO
```

The chosen resolution is prediction-contract alignment, not historical-domain
expansion. C4f0 must remove margin as a required formal prediction input and remove or
replace AbilityEngine's margin score using only fields already retained in the exact
snapshot. The replacement weights and eligibility semantics require their own approved
design; they are not guessed here. Existing legacy request parsing may retain its own
input field for backward compatibility, but a legacy-only margin must no longer be a
required or score-affecting member of the immutable formal prediction input.

Historical-domain expansion is rejected for this path because it would reopen source,
snapshot, digest, persistence, schema, migration, and replay contracts without a
currently retained canonical numeric fact. Preserving an old score formula is not
sufficient reason to weaken causal reproducibility.

C4f0 must also freeze the historical prediction execution reference date. The current
Ability, Jockey, and Track engines can default to `date.today()`. The pure c4f1 adapter
will never sample a clock, but later pipeline composition must inject a reference derived
from the exact snapshot rather than use the process date. This is an execution-wiring
contract, not permission for c4f1 to instantiate or run the prediction pipeline.

## Complete Destination Compatibility Matrix

The classifications below describe the current formal base. `NOT_REPRESENTABLE` is the
blocking state that c4f0 must resolve. `DERIVED_FROM_EXACT_SNAPSHOT_FACT` includes
deterministic construction and the explicitly checked numeric computation conversion;
it does not authorize another data source.

| Destination | Snapshot source | Classification | Frozen semantics |
| --- | --- | --- | --- |
| `PredictionPipelineInput.horse_past_races` keys | `entries[].race_entry_id` | `DERIVED_FROM_EXACT_SNAPSHOT_FACT` | Exact internal race-entry ID only. |
| past-race sequence | `past_races[].past_race_index` | `DERIVED_FROM_EXACT_SNAPSHOT_FACT` | Consume indices `0..N-1`; never sort by date/name or insertion order. Formal absence maps to `()`. |
| past `horse_id` | owning `race_entry_id` | `DIRECT` | Field name remains legacy; value is exact internal race-entry ID. |
| past `race_date` | `race_date` | `LOSSLESS_CONVERSION` | Canonical `YYYY-MM-DD`. |
| past `place` | `place` | `DIRECT` | No lookup or normalization. |
| past `race_name` | `race_name` | `DIRECT` | No display-name linkage. |
| past `race_class` | `race_class` | `DIRECT` | No lookup. |
| past `distance` | `distance_m` | `DIRECT` | Exact integer with field rename only. |
| past `track` | `track` | `DIRECT` | Exact snapshot text. |
| past `weather` | `weather` | `DIRECT` | Past-race weather only. |
| past `track_condition` | `track_condition` | `DIRECT` | No weather substitution. |
| past `finish` | `finish` | `DIRECT` | Exact integer. |
| past `margin` | none | `NOT_REPRESENTABLE` | C4f0 prerequisite; no default/sentinel/reparse. |
| past `time` | `race_time` | `DIRECT` | Exact snapshot text; never treated as margin. |
| past `weight` | `weight` | `DERIVED_FROM_EXACT_SNAPSHOT_FACT` | Checked deterministic Decimal-to-float computation representation. |
| past `weight_diff` | `weight_diff` | `DERIVED_FROM_EXACT_SNAPSHOT_FACT` | Checked deterministic Decimal-to-float computation representation. |
| past `jockey` | `jockey` | `DIRECT` | Exact historical value. |
| past `popularity` | `popularity` | `DIRECT` | Exact integer. |
| past `odds` | `odds` | `DERIVED_FROM_EXACT_SNAPSHOT_FACT` | Checked deterministic Decimal-to-float computation representation. |
| past `passing_order` | `passing_order` | `DIRECT` | Exact snapshot text. |
| past `fourth_corner_position` | `fourth_corner_position` | `DIRECT` | Exact integer. |
| `jockey_names_by_horse` | `entries[].jockey` | `DERIVED_FROM_EXACT_SNAPSHOT_FACT` | Map by exact internal race-entry ID. |
| target track `place` | `race.place` | `DIRECT` | No current track lookup. |
| target track `distance` | `race.distance_m` | `DIRECT` | Exact integer with field rename only. |
| target track `track` | `race.track` | `DIRECT` | Exact snapshot text. |
| target `track_condition` | `race.track_condition` | `DIRECT` | Target weather must not substitute. |
| target `race_name`, `race_class`, `weather` | snapshot race metadata | `MUST_NOT_POPULATE` | No destination fields exist. |
| `odds_by_horse` | `entries[].win_odds` | `DERIVED_FROM_EXACT_SNAPSHOT_FACT` | Checked deterministic Decimal-to-float map by race-entry ID. |
| `race_horse_count` | `len(entries)` | `DERIVED_FROM_EXACT_SNAPSHOT_FACT` | Snapshot entries are already complete and unique. |
| pipeline `race_id` | `internal_race_id` | `DIRECT` | No external-ID rebuild. |
| `prediction_time` | `information_cutoff` | `LOSSLESS_CONVERSION` | Canonical UTC ISO-8601 microseconds string. |
| simulation `race_id` | `internal_race_id` | `DIRECT` | Must equal pipeline race ID. |
| `target_race_date` | `race.target_race_date` | `DIRECT` | Exact date. |
| `scheduled_start_at` | `race.scheduled_start_at` | `DIRECT` | Exact aware normalized instant. |
| `information_cutoff` | `information_cutoff` | `DIRECT` | Exact aware normalized instant. |
| `pipeline_input` | mapped fields above | `NOT_REPRESENTABLE` | Becomes derived only after c4f0 removes the margin gap. |
| `input_snapshot_audit` | identity plus provenance/evidence | `DERIVED_FROM_EXACT_SNAPSHOT_FACT` | Conservative deterministic reduction specified below. |
| external entry/horse identity, horse number/name | snapshot metadata | `MUST_NOT_POPULATE` | Never used as prediction entity keys. |
| result, payout, settlement facts | none | `MUST_NOT_POPULATE` | Prediction input must not contain them. |

No required destination field other than margin remains unresolved.

## Identity, Ordering, and Exact Mappings

The prediction entity key is always
`HistoricalRaceEntrySnapshot.race_entry_id`, the exact internal race-entry identity
bound by d0 and retained by the snapshot. Horse number, external horse ID, external
entry ID, horse name, independently queried legacy IDs, and numeric coincidence are not
mapping sources.

For each entry, past races are materialized by exact `past_race_index` lookup in the
contiguous sequence `0..N-1`. The adapter must not reorder by race date or any incidental
field. An entry with no past-race rows and exact `past_race/{race_entry_id}/none`
provenance receives an empty tuple, never a fabricated race.

The target track object contains only exact `race.place`, `race.distance_m`,
`race.track`, and `race.track_condition`. Target weather is not substituted for track
condition. The jockey map uses exact `entries[].jockey` and exact race-entry keys, with
no repository, current table, name mapping, or adapter-owned normalization.

## Numeric Computation Representation

Snapshot win odds and past-race odds, weight, and weight difference are exact `Decimal`
values and remain canonical in the persisted snapshot and its content digest. Current
prediction models and engines require binary floats; notably, `ValueEngine` rejects a
`Decimal` as an invalid odds object. Therefore c4f1 must use an explicit checked
`Decimal -> float` conversion rather than allow structural Decimal flow.

For each conversion, require the source to satisfy its already-formal sign/domain rule,
require the result to be finite, preserve the required sign, and reject a non-zero
Decimal that underflows to float zero. Target win odds must remain strictly positive;
past odds and weight remain non-negative; weight difference may be signed. No explicit
rounding is allowed. Python's deterministic correctly-rounded float conversion is the
computation representation; any unavoidable binary precision loss is accepted only for
engine computation. The exact Decimal snapshot and content digest remain audit truth.

## Prediction Timestamp

`prediction_time` means the prediction information boundary, not evidence capture,
persistence, replay execution, result, current time, or scheduled start. It is exactly:

```python
snapshot.information_cutoff.isoformat(timespec="microseconds")
```

The snapshot domain normalizes the instant to UTC, so the resulting format is canonical
`YYYY-MM-DDTHH:MM:SS.ffffff+00:00`. `identity.captured_at` remains
`InputSnapshotAudit.captured_at` and retains its distinct evidence-capture meaning.

## Conservative Audit Reduction

The existing `InputAuditEntry` has one observed/available pair, while one exact
`HistoricalInputProvenance` may require multiple evidence references. This is still
causally representable because the simulation audit is a conservative cutoff guard and
the persisted historical snapshot remains the complete evidence audit object.

For each provenance item, freeze the order-independent reduction:

```text
observed_at = maximum actual instant among every required evidence.observed_at

available_at = None
    if any required evidence.available_at is None
    otherwise maximum actual instant among every evidence.available_at
```

This never hides a later observation, never invents known availability when any required
evidence has unknown availability, and is invariant under evidence ordering. Each source
evidence value is already no later than `snapshot.identity.captured_at`, which is no
later than `snapshot.information_cutoff`; the reduced values retain those inequalities.

Each `InputAuditEntry` preserves `input_type`, `audit_key`, `source`, `source_id`,
`race_entry_id`, and `past_race_index` exactly from its provenance item. Audit entries
are emitted in canonical `audit_key` order so dictionary/tuple insertion order cannot
change output. `InputSnapshotAudit` uses:

```text
dataset_id  = snapshot.identity.dataset_id
source      = snapshot.identity.source_identity.source_system
captured_at = snapshot.identity.captured_at
entries     = the exact conservative reductions
is_complete = True
```

The source is therefore the formal source-system string (`jra_official` for c4d output),
not the organization label `JRA`. `is_complete=True` is justified only because an exact
`HistoricalInputSnapshot` has already proved track, every entry, jockey, odds,
past-race-or-formal-absence, complete provenance keys, and causal evidence timestamps.
The adapter does not repair or fill missing material. A forged or semantically
incompatible object fails closed.

## Final Construction Choice

After c4f0, c4f1 should construct `ImmutableRacePredictionInput` directly, using frozen
mappings, tuples of the aligned immutable past-race domain, and
`TrackConditionsSnapshot`. It must not create a mutable `RacePredictionInput` merely to
have `SimulationRaceInput.__post_init__` copy it. No parallel simulation input model is
needed once c4f0 aligns the existing immutable input.

The resulting `SimulationRaceInput` must pass its existing `__post_init__` and
`validate_simulation_race_input(...)` unchanged. The adapter must not weaken validation.
An explicit adapter validation error is useful for exact snapshot-type, numeric
conversion, and conversion-shape failures; the existing `SimulationValidationError`
should propagate unchanged so future-leak or audit incompatibility is never obscured.

The proposed c4f1 module-local public surface is:

```python
HistoricalInputSnapshotSimulationAdapterError
HistoricalInputSnapshotSimulationAdapterValidationError

build_simulation_race_input_from_historical_snapshot(
    *,
    snapshot: HistoricalInputSnapshot,
) -> SimulationRaceInput
```

There is no package-root export and no collaborator argument.

## Future-Leak and Determinism Contract

The c4f1 adapter receives one exact `HistoricalInputSnapshot` and nothing else needed
for race facts:

```text
SNAPSHOT_ONLY_INPUT: YES
DATABASE_READ: NO
LIVE_HTTP: NO
CURRENT_FALLBACK: NO
LEGACY_RACE_LOOKUP: NO
LEGACY_HORSE_LOOKUP: NO
LEGACY_PAST_RACE_LOOKUP: NO
RESULT_LOOKUP: NO
PAYOUT_LOOKUP: NO
SETTLEMENT_LOOKUP: NO
FINAL_ODDS_AFTER_CUTOFF: NO
HORSE_NAME_MAPPING: NO
CURRENT_CLOCK: NO
```

The adapter cannot select latest and has no repository. Equal exact snapshot content
must produce equal output across process restart, database changes, dictionary insertion
order, current date, later archive/snapshot enrichment, result, payout, and settlement.
Later snapshot B cannot change adapter output for exact snapshot A.

The future pipeline composition must separately avoid default current-date ownership in
date-sensitive engines and use the c4f0-approved exact historical reference. C4f1 does
not run or configure prediction engines.

## Required Future Test Intent

C4f0 tests must pin the approved marginless historical prediction contract, exact
AbilityEngine replacement formula/eligibility/weights, legacy compatibility decision,
immutable input shape, and snapshot-derived reference-date wiring without current-clock
dependence.

C4f1 tests must cover at minimum:

- exact public surface/signature and exact snapshot type;
- one and multiple entries keyed only by `race_entry_id`;
- zero history to empty tuple and exact absence audit;
- past races consumed in `past_race_index` order;
- exact jockey, track, race ID, target date, scheduled start, and cutoff;
- checked target/past odds and weight conversions, including overflow and underflow;
- canonical information-cutoff prediction time;
- complete audit keys and exact provenance scalar preservation;
- conservative multi-evidence maximum/unknown-availability reduction;
- all reduced audit times causal and no post-cutoff evidence;
- direct immutable pipeline input construction;
- final unchanged `SimulationRaceInput` validation success;
- no name/external-ID mapping, DB, HTTP, current clock, legacy lookup, result, payout,
  or settlement dependency;
- exact deterministic equality across insertion order and restart-equivalent snapshots;
- later snapshot enrichment irrelevant to snapshot A;
- the c4f0 margin resolution directly exercised with no synthetic compatibility value.

## Future File Scope

C4f0 must receive its own PREPARE before implementation. Its expected focused production
area is:

```text
scripts/prediction/input_contracts.py
scripts/prediction/ability_engine.py
scripts/prediction/prediction_pipeline.py          # only if reference-date wiring belongs here
scripts/prediction/jockey_engine.py                 # only for the approved reference-date contract
scripts/prediction/track_engine.py                  # only for the approved reference-date contract
scripts/simulation/models.py
```

Direct focused tests are expected in the corresponding prediction/simulation test files.
The c4f0 PREPARE must minimize this list and decide legacy `PastRace`/persisted-request
compatibility explicitly; this parent PREPARE does not authorize edits.

After c4f0 is formal, c4f1 should be limited to:

```text
scripts/simulation/historical_input_snapshot_simulation_adapter.py
tests/test_historical_input_snapshot_simulation_adapter.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

No snapshot domain, repository, schema, migration, c4d, c4e, persisted simulation
application, CLI, betting, settlement, NAR, or package-root file belongs to c4f1.

## Readiness

```text
SNAPSHOT_TO_PREDICTION_COMPATIBILITY: BLOCKED_BY_REQUIRED_MARGIN_AND_PREDICTION_REFERENCE_DATE_ALIGNMENT
HISTORICAL_MARGIN_AVAILABLE: NO
ABILITY_MARGIN_DEPENDENCY: YES_NONZERO_WEIGHT_AND_ELIGIBILITY
AUDIT_MULTI_EVIDENCE_REPRESENTABLE: YES_CONSERVATIVE_ORDER_INDEPENDENT_REDUCTION
IMPLEMENTATION_READY: NO
BLOCKERS: C4F0_FORMAL_HISTORICAL_PREDICTION_CONTRACT_ALIGNMENT
```

No production code, tests, HTTP, or real trusted capture were performed in this
PREPARE.

## Allowed Files

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Forbidden Files

All production, tests, schema/migration, c4d/c4e, prediction, simulation execution,
CLI, betting, settlement, NAR, live-capture, and package-root files.

## Required Checks

```text
git diff --check
git status --short
changed-file scope == the two allowed docs
```

No pytest or HTTP is required for this docs-only PREPARE.

## Stop Condition

Commit and push the single docs-only PREPARE review commit, then stop for independent
architecture review. Do not implement c4f0 or c4f1 and do not modify the formal branch.
