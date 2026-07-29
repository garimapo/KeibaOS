# Current Phase

## Status

APPROVED_FOR_CODEX

## Phase

Phase 4C-2d3b1i0 — Prediction-side immutable input contracts

## Base Commit

`d50c27b docs: approve persisted simulation integration`

## Branch

`feature/ver0.8-simulator`

## Objective

Define prediction-owned readonly structural input Protocols so both existing
`RacePredictionInput` and simulation-owned `ImmutableRacePredictionInput` are formal inputs to
the prediction Pipeline.  This phase changes annotations and tests only; it must preserve all
runtime Pipeline and Engine behavior.

## Adopted Design

Add `scripts/prediction/input_contracts.py` with these non-runtime-checkable
`typing.Protocol` contracts:

```python
class PastRaceInput(Protocol):
    @property
    def horse_id(self) -> int: ...
    @property
    def race_date(self) -> str: ...
    @property
    def place(self) -> str: ...
    @property
    def race_name(self) -> str: ...
    @property
    def race_class(self) -> str: ...
    @property
    def distance(self) -> int: ...
    @property
    def track(self) -> str: ...
    @property
    def weather(self) -> str: ...
    @property
    def track_condition(self) -> str: ...
    @property
    def finish(self) -> int: ...
    @property
    def margin(self) -> float: ...
    @property
    def time(self) -> str: ...
    @property
    def weight(self) -> float: ...
    @property
    def weight_diff(self) -> float: ...
    @property
    def jockey(self) -> str: ...
    @property
    def popularity(self) -> int: ...
    @property
    def odds(self) -> float: ...
    @property
    def passing_order(self) -> str: ...
    @property
    def fourth_corner_position(self) -> int: ...


class RaceTrackConditionsInput(Protocol):
    @property
    def place(self) -> str: ...
    @property
    def distance(self) -> int: ...
    @property
    def track(self) -> str: ...
    @property
    def track_condition(self) -> str: ...


class PredictionPipelineInput(Protocol):
    @property
    def horse_past_races(self) -> Mapping[int, Sequence[PastRaceInput]]: ...
    @property
    def jockey_names_by_horse(self) -> Mapping[int, str]: ...
    @property
    def track_conditions(self) -> RaceTrackConditionsInput: ...
    @property
    def odds_by_horse(self) -> Mapping[int, object]: ...
    @property
    def race_horse_count(self) -> int: ...
    @property
    def race_id(self) -> int: ...
    @property
    def prediction_time(self) -> str: ...
```

The Protocol module must not import `scripts.simulation`, `scripts.models.PastRace`,
`RacePredictionInput`, or `RaceTrackConditions`.  Do not add `@runtime_checkable` or runtime
Protocol `isinstance()` checks.  `PastRace`/`PastRaceSnapshot`,
`RaceTrackConditions`/`TrackConditionsSnapshot`, and
`RacePredictionInput`/`ImmutableRacePredictionInput` must conform structurally.

## Required Production Annotation Changes

- `PredictionPipeline.run(self, race_input: PredictionPipelineInput) -> PipelineResult`
- `AbilityEngine`: every public/private annotation that receives a past race uses
  `PastRaceInput` or `Sequence[PastRaceInput]` as appropriate.
- `PaceEngine`: every public/private past-race annotation uses `PastRaceInput`,
  `Sequence[PastRaceInput]`, or `Mapping[int, Sequence[PastRaceInput]]` as appropriate.
- `JockeyEngine`: every public/private past-race annotation uses `PastRaceInput` or
  `Sequence[PastRaceInput]` as appropriate.
- `TrackEngine`: target and past-race annotations use `RaceTrackConditionsInput`,
  `PastRaceInput`, `Sequence[PastRaceInput]`, and
  `Mapping[int, Sequence[PastRaceInput]]` as appropriate.
- `ValueEngine.evaluate()` changes only `odds_by_horse` to `Mapping[int, object]`, matching its
  existing validation logic.  Prediction/result types and logic remain unchanged.

`RacePredictionInput` and `RaceTrackConditions` remain their existing concrete models.  Do not
change their fields, `PastRaceSnapshot`, `TrackConditionsSnapshot`, or any simulation model.

## Runtime Invariants

Do not change Engine calculations, Pipeline stage order, PipelineResult, strategy, predictor,
BetGenerator, Value calculation, existing current-date defaults, logging, exception wrapping, or
domain-model behavior.  Pipeline reads the supplied object only: it does not copy, restore a
mutable input, sort, normalize, supplement from DB/Provider, or use current time.

Never use `typing.Any`, `typing.cast`, `# type: ignore`, a TYPE_CHECKING simulation import,
concrete-type unions, a broad `object` input contract, or runtime Protocol checks.  `object` is
permitted only for `PredictionPipelineInput.odds_by_horse` and the matching existing ValueEngine
validation boundary.

## Allowed Files

- `scripts/prediction/input_contracts.py`
- `scripts/prediction/prediction_pipeline.py`
- `scripts/prediction/ability_engine.py`
- `scripts/prediction/pace_engine.py`
- `scripts/prediction/jockey_engine.py`
- `scripts/prediction/track_engine.py`
- `scripts/prediction/value_engine.py`
- `tests/test_prediction_input_contracts.py`
- `docs/LATEST_CODEX_REPORT.md`

`docs/CURRENT_PHASE.md` is not an implementation target after this approval.

## Forbidden Files and Scope

Do not change `scripts/simulation/models.py`, any other simulation code, `PastRaceSnapshot`,
`TrackConditionsSnapshot`, `RacePredictionInput` fields, `RaceTrackConditions` fields,
package-root exports, service/orchestration code, allocator/builder/Repository code, schema,
migrations, CLI, `main.py`, DB paths, `database/keiba.db`, or `logs/`.  Do not add retry, cache,
network, DB/Provider access, or current-time behavior.

## Required Tests

Create `tests/test_prediction_input_contracts.py` to verify:

1. `get_type_hints()` confirms the listed public APIs use the new Protocols.
2. No remaining production annotation requires `PastRace` where `PastRaceInput` is required.
3. Fixed, reference-date-controlled real Pipeline accepts existing mutable `RacePredictionInput`.
4. The equivalent `ImmutableRacePredictionInput` runs through that same real Pipeline.
5. Mutable and immutable Pipeline results, BetPlans, recommendation order, prediction race IDs,
   and horse IDs are equal by value.
6. Pipeline execution does not mutate caller mutable mappings/sequences and does not reconstruct
   the immutable input as a mutable object.
7. No DB, Provider, network, current-date test dependency, runtime Protocol check, simulation
   import from prediction production modules, or package-root export is added.

Inject fixed reference dates into AbilityEngine, JockeyEngine, and TrackEngine for deterministic
tests.  Run the dedicated test, relevant Prediction/Engine/SimulationRaceInput/immutable-input/
persisted-integration regression tests found in the repository, the full pytest suite, source
searches for the prohibited patterns, `git diff --check`, and `git status --short`.

## Stop Condition

Stop and report if structural Protocol typing requires a change outside Allowed Files, if an
existing runtime behavior changes, if a test failure is out of scope, or if unexpected Git changes
appear.  Do not stage, commit, push, create a review branch, or start Phase 4C-2d3b1i1 without
explicit instruction.

## Follow-up (Not Approved for Implementation)

Phase 4C-2d3b1i1 — Prediction-to-snapshot persistence service.

After Phase 4C-2d3b1i0 has been implemented and reviewed, re-review the retained service design:
one `PersistedSimulationBetPlanService`; explicit `BetStakeBudget`; fail-closed
StrategyIdentity/Pipeline alignment; policy identity derived from StrategyConfig; one Pipeline,
allocator, builder, and Repository call; NO_BET snapshot persistence; and same-object exception
propagation.  No service code is authorized in Phase 4C-2d3b1i0.
