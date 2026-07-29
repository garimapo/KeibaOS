# Latest Codex Report

## Status

APPROVED_FOR_COMMIT

## Phase

Phase 4C-2d3b1i0 — Prediction-side immutable input contracts

Base commit: `d50c27b docs: approve persisted simulation integration`

## Result

Implemented the prediction-owned readonly input-contract boundary after the Phase 4C-2d3b1i
split. Phase 4C-2d3b1i1 remains untouched.

### Protocols and dependency direction

Added `scripts/prediction/input_contracts.py` with these `typing.Protocol` contracts:

- `PastRaceInput` (19 readonly fields)
- `RaceTrackConditionsInput` (4 readonly fields)
- `PredictionPipelineInput` (pipeline input fields)

The module has no import from simulation, no concrete `PastRace`, `RacePredictionInput`, or
`RaceTrackConditions` import, no runtime Protocol check, and no `@runtime_checkable` marker.
Prediction continues to have no dependency on simulation.

### Annotation-only production changes

- `PredictionPipeline.run()` now accepts `PredictionPipelineInput`.
- Ability, Pace, Jockey, and Track Engine past-race/track input annotations use the readonly
  Protocols throughout their public and private evaluation methods.
- `ValueEngine.evaluate()` now accepts `Mapping[int, object]` for odds, matching the existing
  runtime validation boundary.

No Pipeline stage order, calculation, logging, exception wrapping, result construction, strategy,
or domain/simulation model changed. Existing Engine `date.today()` constructor defaults were not
changed or newly introduced.

### Mutable and immutable input verification

The new deterministic test injects `date(2026, 8, 1)` into Ability, Jockey, and Track Engines.
It runs the same real `PredictionPipeline` directly with a mutable `RacePredictionInput` and the
equivalent `ImmutableRacePredictionInput`; no restoration to a mutable input occurs. The two
`PipelineResult` values, predictions, and BetPlans are equal by value, including prediction race
and horse IDs. The caller's past-race mapping/lists, jockey mapping, and odds mapping remain
unchanged.

### Verification

```text
Dedicated:
  python -m pytest tests/test_prediction_input_contracts.py -q
  4 passed

Related:
  prediction pipeline, Ability, Pace, Jockey, Track, Value, simulation validation,
  persisted simulation integration, and input-contract tests
  57 passed, 8 subtests passed

Full suite:
  2260 passed, 2 skipped, 666 subtests passed

Source search:
  typing.Any / typing.cast / # type: ignore / runtime_checkable / scripts.simulation: 0 matches
  new date.today() calls: 0

git diff --check: success
```

## Scope and Git state

Changed implementation/test files are limited to the Phase 4C-2d3b1i0 Allowed Files.
`database/keiba.db` and `logs/` remain out of scope and are not included in this work.

## Review correction

GitHub review found no production-code issue. It identified a test weakness: the prior annotation
regression assertion inspected only top-level hint values and could miss a concrete `PastRace`
nested inside a generic annotation. The test now uses a recursive `typing.get_args()` helper across
each parameter annotation for Ability, Pace, Jockey, and Track Engine methods. Dedicated assertions
prove that nested `Sequence[PastRace]` and `Mapping[int, Sequence[PastRace]]` are detected, while
`Sequence[PastRaceInput]` is accepted.

Production code remains unchanged by this correction. Re-verification results are recorded below.

```text
Correction dedicated test: 4 passed
Correction full suite: 2260 passed, 2 skipped, 666 subtests passed
Correction git diff --check: success
```

## Approval

GitHub implementation review is approved. The production implementation required no correction,
and correction commit `8a03b02` was re-reviewed and approved. The readonly Protocol design is
approved: prediction has no dependency on simulation; Pipeline and Engine runtime logic is
unchanged; both mutable `RacePredictionInput` and `ImmutableRacePredictionInput` are accepted by
the real Pipeline and produce equal `PipelineResult` values without mutating caller collections.
The recursive nested-concrete-`PastRace` annotation regression test is also approved.

The review branch is pushed to origin. Base-branch integration is pending. Phase 4C-2d3b1i1
remains unstarted.
