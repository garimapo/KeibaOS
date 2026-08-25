# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase

`4C-2d3b1i6d1d5f1c4f0` — Formal historical prediction-contract alignment.

Formal base: `48dde0f5a5d1cce0176b578ccfcc87dbd9fc1fac`.

Architecture reference only:
`4f9ab065b13a2823e5a5d356a4adcd57cadfdd4f`.

Review branch:
`review/4c-2d3b1i6d1d5f1c4f0-formal-historical-prediction-contract-alignment-prepare`.

This phase is the prerequisite for
`4C-2d3b1i6d1d5f1c4f1`, the pure
`HistoricalInputSnapshot -> SimulationRaceInput` adapter. C4f1 remains blocked until
c4f0 is formal.

## Purpose and Scope

C4f0 makes the existing prediction domain compatible with exact historical snapshot
facts without inventing margin or sampling the process date. It resolves exactly:

1. the formal prediction protocol and immutable simulation input currently require a
   numeric margin that the historical snapshot does not contain; and
2. the historical prediction path needs one explicit race-calendar reference date for
   Ability, Jockey, and Track evaluation instead of their live/default current date.

This is a prediction-contract change only. It does not alter historical source records,
snapshot domains or digests, repositories, replay, c4d/c4e, schema, or migrations.

## Margin Availability and Negative Rules

`HistoricalPastRaceSnapshot` contains no canonical numeric margin. Formal historical
source records also contain no margin. A JRA parser's transient inspection of displayed
margin for unsupported dead-heat detection is not a retained numeric fact and is not
available to prediction replay.

Freeze:

```text
HISTORICAL_MARGIN_AVAILABLE: NO
SYNTHETIC_MARGIN_ALLOWED: NO
MARGIN_ZERO_DEFAULT_ALLOWED: NO
MARGIN_NAN_SENTINEL_ALLOWED: NO
LEGACY_DB_MARGIN_LOOKUP_ALLOWED: NO
RAW_HTML_REPARSE_ALLOWED: NO
RACE_TIME_AS_MARGIN_ALLOWED: NO
HISTORICAL_DOMAIN_REOPEN: NO_UNLESS_NEW_CANONICAL_EVIDENCE_IS_PROVEN
```

No malformed or missing historical value may be converted into a neutral compatibility
value. Failure remains explicit.

## Exact Margin Contract Alignment

Production attribute-read inspection found that only `AbilityEngine` reads
`PastRaceInput.margin`. Pace, Jockey, and Track engines do not. The exact minimal
alignment is:

- remove `margin` from the structural `PastRaceInput` protocol;
- remove `margin` from immutable formal `PastRaceSnapshot`;
- make `PastRaceSnapshot.from_past_race(...)` copy only the remaining formal fields, so
  a legacy mutable object can contain extra margin without preserving it in the immutable
  prediction input;
- remove every margin read, helper, constant, eligibility branch, and score component
  from `AbilityEngine`;
- retain `scripts.models.PastRace.margin` unchanged for legacy mutable callers;
- retain the schema-v1 persisted simulation request `margin` field and its existing
  parsing/validation unchanged for schema and parsing compatibility. Its legacy value is
  accepted at that boundary but is omitted by immutable conversion and has no prediction
  effect after c4f0.

The resulting immutable formal past-race field list is exactly:

```text
horse_id
race_date
place
race_name
race_class
distance
track
weather
track_condition
finish
time
weight
weight_diff
jockey
popularity
odds
passing_order
fourth_corner_position
```

This list is fully representable from `HistoricalPastRaceSnapshot`. C4f1 must construct
this immutable type directly and must not instantiate legacy `scripts.models.PastRace`.

## Ability Formula

The old per-race score is:

```text
finish      0.45
popularity  0.15
margin      0.15
class       0.25
total       1.00
```

Removing the margin term without rescaling would reduce the maximum retained-feature
score to 85 and silently compress the ability scale. No unrelated replacement feature
is justified. Freeze proportional renormalization of the three retained components:

```text
finish      (0.45 / 0.85) = 9 / 17
popularity  (0.15 / 0.85) = 3 / 17
class       (0.25 / 0.85) = 5 / 17
total                         17 / 17 = 1
```

The implementation should express the exact integer ratio or an equivalently testable
normalized computation, rather than depend on visually rounded decimal constants. The
new per-race score is:

```text
(finish_score * 9 + popularity_score * 3 + class_score * 5) / 17
```

This uses only retained formal facts, preserves the old relative importance of every
remaining component, keeps the 0..100 interpretation, minimizes behavioral change, and
adds no new feature or result lookup.

Distance and recency continue to affect the existing outer race weighting exactly as
before. No Pace, Jockey, Track, Predictor, or Value score tuning belongs here.

## Ability Eligibility

Before c4f0 a race is eligible when at least one of the following is usable:

```text
finish > 0
popularity > 0
valid positive finite margin
nonblank race_class
```

After c4f0 the exact eligibility is:

```text
finish > 0
OR popularity > 0
OR nonblank race_class
```

There is no margin branch. Formal `HistoricalPastRaceSnapshot` already requires a
positive finish and a nonempty race class, so every formal past-race value passes the
feature-availability portion of this check. The engine retains its deterministic
handling of zero/missing retained fields; it does not add a permissive
fallback for malformed types.

## Reference-Date Semantics

For Ability, Jockey, and Track engines, `reference_date` is only the race-calendar
ceiling used to reject a purported past race dated after the evaluation target. It is
not the prediction timestamp and does not express evidence availability.

Freeze the historical reference date as:

```text
HistoricalInputSnapshot.race.target_race_date
```

This is the exact formal race calendar date and remains distinct from the full
`snapshot.information_cutoff` instant used by c4f1 as `prediction_time`. The snapshot
already proves every `past_race.race_date < target_race_date`, but explicit engine
construction with the same date preserves defense in depth for the structural
prediction boundary.

The reference date is a date-only official race-calendar fact. It is never derived from
`information_cutoff.date()` because the cutoff is normalized to UTC and its UTC calendar
date can differ from the Japanese target race date across JST midnight. No timezone
conversion occurs. Same-day or later purported history is already rejected by the
snapshot; engines continue rejecting dates later than the supplied reference date.

Freeze:

```text
REFERENCE_DATE_SOURCE: SNAPSHOT_RACE_TARGET_RACE_DATE
REFERENCE_DATE_TIMEZONE_SEMANTICS: EXACT_DATE_ONLY_OFFICIAL_RACE_CALENDAR_NO_UTC_PROJECTION
SAME_DAY_EDGE_CASE_SAFE: YES
PREDICTION_TIME_SOURCE_UNCHANGED: SNAPSHOT_INFORMATION_CUTOFF_INSTANT
```

## Current-Date Ownership Audit

The following constructors currently own current-date defaults:

- `AbilityEngine(reference_date=None)` calls `date.today()`;
- `JockeyEngine(reference_date=None)` calls `date.today()`;
- `TrackEngine(reference_date=None)` calls `date.today()`;
- `PipelineConfig()` indirectly samples all three defaults through its factories; and
- `PredictionPipeline(config=None)` indirectly constructs that default config.

These defaults may remain for intentionally current/live prediction. Historical
prediction must never call them implicitly.

## Historical Pipeline Construction Owner

Add one narrow public factory in `scripts/prediction/prediction_pipeline.py`:

```python
build_historical_prediction_pipeline(
    *,
    target_race_date: date,
    strategy_config: StrategyConfig,
) -> PredictionPipeline
```

It must require exact `date` (not `datetime`) and exact `StrategyConfig`, then construct
and inject:

```text
AbilityEngine(reference_date=target_race_date)
JockeyEngine(reference_date=target_race_date)
TrackEngine(reference_date=target_race_date)
```

into one `PipelineConfig` together with the supplied identical `strategy_config` and
the existing default Pace, Predictor, Value, BetGenerator, and RuleBasedBetStrategy
components. It returns `PredictionPipeline(config=that_exact_config)`.

The factory must validate before engine construction, must not call any clock, and must
not fall back to a default engine after failure. The three formal engine types stay
distinct and their existing explicit constructor APIs need no production change.

The later historical application/composition boundary owns calling this factory with
`SimulationRaceInput.target_race_date`. C4f1 remains a pure input adapter and does not
configure or execute engines. The normal formal historical path must not use
`PipelineConfig()` or `PredictionPipeline()` defaults.

This factory is the explicit historical construction boundary; `PredictionPipeline.run`
does not parse `prediction_time`, infer a date, or read a clock.

## Persisted Simulation Request Compatibility

The existing schema-v1 persisted request carries only `pipeline.track_reference_date`
and currently uses it only to construct `TrackEngine`. Changing that field to affect
Ability or Jockey would silently change the meaning and predictions of existing request
documents. Renaming/generalizing it or admitting two request shapes would also broaden
c4f0 unnecessarily.

Freeze:

```text
PERSISTED_REQUEST_SCHEMA_CHANGE: NO
PERSISTED_REQUEST_SCHEMA_COMPATIBILITY: YES
PERSISTED_REQUEST_PARSING_COMPATIBILITY: YES
PREDICTION_SEMANTICS_COMPATIBILITY: NO_INTENTIONAL_MODEL_CONTRACT_CHANGE
EXISTING_TRACK_REFERENCE_DATE_POLICY: RETAIN_EXACT_V1_TRACK_ENGINE_ONLY_SEMANTICS
```

Schema compatibility means schema version 1 and the JSON shape remain unchanged:
`past_race.margin` stays required and keeps its finite-number validation,
`track_reference_date` stays unchanged, and no request key or migration is added.
Parsing compatibility means existing valid request files remain loadable and continue
populating `scripts.models.PastRace.margin` at the legacy assembly boundary.

Prediction semantics are intentionally not backward-compatible. AbilityEngine no longer
reads that populated margin and uses the 9:3:5 formula globally. Consequently, the same
schema-v1 request can produce a different prediction under c4f0 than under an older code
revision. This is an explicit formal prediction-model contract change, not a silent
fallback or a claim that legacy request meaning is unchanged.

This semantic change is required because running historical prediction with a marginless
model while live/persisted-request prediction remained margin-aware would make formal
historical validation measure a different feature contract from the deployed model. C4f0
therefore aligns both paths to the intersection of causally reproducible snapshot facts:

```text
LIVE_PREDICTION_ABILITY_SEMANTICS_CHANGED: YES_INTENTIONAL
HISTORICAL_AND_LIVE_FORMAL_ABILITY_MODEL: SAME_MARGINLESS_9_3_5_MODEL
```

The new historical factory remains distinct from the persisted-request assembler. The
future snapshot-driven application composition must use the historical factory and must
not route through `track_reference_date`.

## Code-Version Reproducibility

The schema-v1 request retains `SimulationRunContext.target_commit_id`, but the existing
execution chain does not independently prove that the running checkout equals that ID.
C4f0 adds no runtime commit verification.

Freeze:

```text
SAME_CODE_REVISION_PLUS_SAME_EXACT_INPUT_CONFIG: DETERMINISTIC
CROSS_CODE_REVISION_PREDICTION_EQUALITY: NOT_GUARANTEED
TARGET_COMMIT_ID_RUNTIME_ENFORCEMENT_IN_C4F0: NO
TARGET_COMMIT_RUNTIME_VERIFICATION: OUT_OF_SCOPE_FOR_C4F0
```

Any future runtime commit check belongs to a separate hardening phase. Neither request
schema compatibility nor `target_commit_id` implies prediction equality across KeibaOS
revisions.

## Constructor Compatibility

`AbilityEngine()`, `JockeyEngine()`, `TrackEngine()`, `PipelineConfig()`, and
`PredictionPipeline()` remain callable with their existing constructor signatures, and
their explicit live/default current-date behavior may remain. This is constructor API
compatibility only:

```text
CONSTRUCTOR_API_COMPATIBILITY: YES
ABILITY_SCORE_SEMANTICS_COMPATIBILITY: NO
```

Ability scores may change because the model intentionally becomes marginless. Historical
execution must use `build_historical_prediction_pipeline(...)` and never those implicit
date defaults.

## Phase Cohesion

The marginless contract and explicit historical pipeline construction have different
code locations but are one narrow prerequisite: together they make the prediction input
both representable and execution-date deterministic. The implementation touches four
focused production files and no persisted request or historical data boundary.

Freeze:

```text
C4F0_SPLIT_REQUIRED: NO
C4F0_SUBPHASES: NONE
```

## Exact Future Implementation Scope

Production files:

```text
scripts/prediction/input_contracts.py
    remove margin from the formal structural protocol

scripts/prediction/ability_engine.py
    remove all margin dependency; implement exact 9:3:5 normalized formula and eligibility

scripts/prediction/prediction_pipeline.py
    add the explicit historical target-date pipeline factory

scripts/simulation/models.py
    remove margin from immutable PastRaceSnapshot and immutable conversion
```

No change is required to `scripts/models.py`: legacy mutable `PastRace.margin` remains.
No change is required to JockeyEngine or TrackEngine: their explicit `reference_date`
constructors already satisfy the historical factory. PaceEngine and ValueEngine do not
read margin and remain unchanged.

Focused test files:

```text
tests/test_ability_engine.py
tests/test_prediction_input_contracts.py
tests/test_prediction_pipeline.py
tests/test_persisted_simulation_race_inputs.py
```

`tests/test_ability_engine.py` pins the exact ratio formula, total scale, marginless
structural dummy, eligibility, and absence of margin reads. The input-contract tests pin
the formal protocol and exact immutable field list plus equality between legacy mutable
and immutable execution after legacy margin is discarded. Pipeline tests pin exact
factory signature/types, identical target date on all three engines, same output under
different monkeypatched process dates, future-to-reference rejection, and no default
factory use. Persisted-race tests preserve the legacy request margin schema/validation
but prove the immutable result omits it and changing only legacy margin cannot change
formal immutable prediction input or AbilityEngine output. They do not assert equal
predictions across pre-c4f0 and post-c4f0 revisions.

The related regression command must include, without implementation edits:

```text
tests/test_jockey_engine.py
tests/test_track_engine.py
tests/test_persisted_simulation_application_inputs.py
tests/test_persisted_simulation_request_document.py
tests/test_simulation_validation.py
```

Implementation verification must also run the full suite.

## Required Implementation Test Contract

Future c4f0 tests must prove at minimum:

- `PastRaceInput` has no margin property;
- exact `PastRaceSnapshot` field list omits margin;
- legacy mutable `PastRace.margin` remains accepted and unchanged;
- immutable conversion drops legacy margin without defaulting or preserving it;
- AbilityEngine succeeds with a structural past-race object that has no margin;
- no production AbilityEngine attribute read, helper, constant, or eligibility branch
  references margin;
- score components are exactly finish, popularity, and class at 9:3:5;
- the weight total is exactly one and the 0..100 scale is retained;
- eligibility is exactly retained-field eligibility;
- Pace, Jockey, and Track remain compatible with marginless `PastRaceInput`;
- the historical factory rejects invalid date/config before engine construction;
- all three date-sensitive engines receive the identical exact target race date;
- the historical factory and resulting execution never sample current date/time;
- two different monkeypatched process dates produce equal historical evaluations;
- a race later than the explicit reference remains excluded by Ability, Jockey, and
  Track according to their existing semantics;
- ordinary default/live constructor APIs remain available, while Ability score semantics
  are explicitly allowed and expected to change;
- schema-v1 requests still require and validate margin and still populate legacy
  `PastRace.margin`;
- changing only legacy margin yields equal immutable inputs and equal post-c4f0 Ability
  results;
- no test claims equal predictions across pre-c4f0 and post-c4f0 revisions;
- persisted request `track_reference_date` still configures TrackEngine only;
- no snapshot/source/replay/repository/schema/migration/ValueEngine change occurs; and
- c4f1 module and tests remain absent.

## Fail-Closed and Boundary Rules

The factory rejects malformed target dates or strategy configuration. Engines do not
turn malformed historical construction into neutral values. No automatic fallback,
current clock, database, HTTP, result/payout lookup, legacy history lookup, or hidden
pipeline default is allowed on the historical path.

No package-root export is required. C4f0 does not implement the snapshot adapter.

## Readiness

```text
HISTORICAL_MARGIN_AVAILABLE: NO
FORMAL_PAST_RACE_MARGIN_REQUIRED_AFTER: NO
LEGACY_PAST_RACE_MARGIN_POLICY: RETAIN_FIELD_FOR_INPUT_COMPATIBILITY_BUT_IGNORE_IN_FORMAL_PREDICTION
IMMUTABLE_PAST_RACE_MARGIN_POLICY: REMOVE
REFERENCE_DATE_OWNER: BUILD_HISTORICAL_PREDICTION_PIPELINE_FACTORY
IMPLEMENTATION_READY: YES_AFTER_INDEPENDENT_APPROVAL
BLOCKERS: NONE
C4F1_IMPLEMENTED: NO
C4F1_BLOCKED_UNTIL: C4F0_FORMALLY_COMPLETE
```

No production code, tests, live HTTP, or real trusted capture were performed.

## Allowed Files for This PREPARE

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Forbidden Files for This PREPARE

All production, tests, source/snapshot/replay/persistence, schema/migration,
persisted-request, adapter, CLI, live-capture, NAR, betting, settlement, and package-root
files.

## Required PREPARE Checks

```text
git diff --check
git status --short
changed-file scope == the two allowed docs
```

No pytest or HTTP is required for this docs-only PREPARE.

## Stop Condition

Commit and push the single docs-only PREPARE review commit, then stop for independent
review. Do not implement c4f0/c4f1 and do not modify the formal branch.
