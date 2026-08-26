# Current Phase

## Status

`READY_FOR_REVIEW`

## Phase

`4C-2d3b1i6d1d5f1c4g2a` — Cutoff-aware historical persisted settlement source.

Formal base: `586174db3fcfd1e124fbb45d01fdfda0342f2396`.

Implementation review branch:
`review/4c-2d3b1i6d1d5f1c4g2a-historical-persisted-settlement-source`.

C4g0 and c4g1 are formally complete. C4g0 owns one race's historical prediction and
immutable bet-plan persistence. C4g1 owns complete preflight, canonical multi-race
ordering, and exactly one c4g0 call per race. C4g2 begins only after those purchase
decisions are fixed and persisted.

## Phase Split

C4g2 must be split. The existing generic persisted settlement source selects an
unbounded latest payout publication and therefore cannot be placed directly in a
historical replay composition.

The exact hierarchy is:

- `4C-2d3b1i6d1d5f1c4g2a` — Cutoff-aware historical persisted settlement source.
- `4C-2d3b1i6d1d5f1c4g2b` — Ordered historical settlement and `SimulationSummary`
  composition.
- `4C-2d3b1i6d1d5f1c4g2c` is reserved only if a later independently approved phase
  requires per-race `SimulationResult` persistence or audit output. It is not required
  for c4g2a or c4g2b.

The next implementation phase is c4g2a. Combining source selection and batch summary
composition would mix temporal repository policy with application orchestration and
would make the unbounded-latest defect harder to pin independently.

## Purpose and Hard Separation

The complete historical direction is:

```text
exact HistoricalInputSnapshot tuple
+ exact c4g1 persisted bet plans
+ one exact SimulationRunContext
+ one exact RuleBased StrategyIdentity
+ exact aware settlement cutoff per internal race ID
+ persisted official race-result and payout facts
-> cutoff-aware PersistedRaceSettlementData
-> PersistedRaceSimulationExecutor exactly once per race
-> SimulationResult per race inside Simulator
-> one SimulationSummary
```

C4g2 owns no prediction execution, historical pipeline construction, bet generation,
allocation, selection resolution, bet-plan construction, or bet-plan mutation. It does
not call c4g0 or c4g1. Result and payout facts may affect settlement only and must never
flow into `HistoricalInputSnapshot`, `SimulationRaceInput.pipeline_input`, prediction,
strategy, allocation, or the saved plan.

`PersistedSimulationRunService` is forbidden because it plans and saves bets before
calling `Simulator`. Historical planning is already complete and must not be reopened.

## Existing Formal Components

The following existing components are reused unchanged:

- in c4g2b, `PersistedSimulationBetSource` reconstructs the exact
  `SimulationBetPlanIdentity` from run, race, strategy, config hash, and prediction
  information cutoff, then exact-loads the immutable saved plan.
- `PersistedRaceSimulationExecutor` owns `NO_BET`, missing-result, partial, `VOID`,
  `UNSUPPORTED`, missing-payout, and `SETTLED` conversion.
- `Simulator` calls its race executor once per input and builds one
  `SimulationSummary` from the complete successful result tuple.
- the existing summary and per-bet settlement primitives retain all financial,
  hit-rate, by-bet-type, and drawdown semantics.

`RepositoryBackedPersistedRaceSettlementSource` remains unchanged for its generic final
settlement use. It is not reused by the historical path because it calls
`get_latest_payout_publication(..., observed_at_lte=None, require_complete=False)`.

The raw `ProviderBackedRaceSimulationExecutor` is not used. C4g2 consumes normalized
persisted official-domain values and does not reconstruct Raw values, rerun conversion
providers, or introduce `ProviderContext`/`RaceEntryUniverse` conversion ownership.

## C4g2a Public Contract

Implemented module:

`scripts/simulation/historical_persisted_race_settlement_source.py`

Exact module-local public surface:

```python
__all__ = (
    "HistoricalPersistedRaceSettlementSource",
)
```

No package-root export and no new public error hierarchy.

The class structurally satisfies the existing `PersistedRaceSettlementSource` protocol.
It accepts only:

- a `SimulationBetSource`;
- a `RaceResultRepository`;
- a `PayoutRepository`; and
- `settlement_cutoffs_by_race_id: Mapping[int, datetime]`.

The cutoff mapping is validated and defensively copied exactly once at construction. Every key
is a positive non-`bool` integer and every value is a timezone-aware `datetime`. The
source has no current-clock fallback, default cutoff, global cutoff, SQLite dependency,
transaction ownership, write method, or exact-publication-ID inference.

Before loading bets, the source validates the exact race-input and strategy boundary and
requires an exact frozen cutoff for the race. A missing cutoff raises
`SimulationValidationError(race_id, "settlement_cutoffs_by_race_id", "settlement cutoff
was not provided for race_id")` before any collaborator call.

For each load, c4g2a calls the injected structural `SimulationBetSource` exactly once and validates
only the returned bet tuple. The return value must have exact type `tuple`; every item
must be a `SimulationBet`; every `bet.race_id` must equal `race_input.race_id`; every
`bet.strategy_id` must equal `strategy_identity.strategy_id`; and every
`(bet.bet_type, bet.race_entry_ids)` identity must be unique. Invalid output raises the
historical source's frozen `SimulationValidationError`. Source-owned exceptions
propagate unchanged where the existing source boundary does not own a translation.

C4g2a does not infer or prove run ID, strategy-config hash, information-cutoff snapshot
identity, repository provenance, or missing persisted-plan semantics. It neither
reconstructs `SimulationBetPlanIdentity` nor queries a bet-plan repository. Its
constructor remains generic over `SimulationBetSource`; it must not require
`PersistedSimulationBetSource`, `SimulationRunContext`, or
`SimulationBetPlanSnapshotSource`.

The c4g2a bet-output validation error contract mirrors the existing generic source:

```text
input_identifier:
simulation_bet_source

non-tuple reason:
bet source must return a tuple of SimulationBet values

invalid-item reason:
bet source must return only SimulationBet values

race mismatch reason:
bet source bets must match race_input.race_id

strategy mismatch reason:
bet source bets must match strategy_identity.strategy_id

duplicate identity reason:
bet source bets must have unique bet identities
```

If the injected bet source returns exact `()`, c4g2a returns an empty
`PersistedRaceSettlementData` and performs no race-result or payout read. This is a
post-race-I/O short circuit only. C4g2a alone does not prove that the empty tuple came
from a persisted c4g1 `NO_BET` plan.

For a nonempty plan it reads the race result once. A result whose `observed_at` is later
than that race's settlement cutoff is treated as unavailable at the cutoff and is not
placed in the settlement bundle. It is not corruption, does not move the cutoff, and
does not become an empty plan.

For every distinct purchased bet type, in first-bet occurrence order, payout selection
is exactly:

```python
payout_repository.get_latest_payout_publication(
    race_id=race_input.race_id,
    bet_type=bet_type,
    observed_at_lte=settlement_cutoff,
    require_complete=False,
)
```

The source defensively rejects a repository response with `observed_at` after the
cutoff. A missing publication or the latest eligible incomplete publication is omitted
from the bundle, so the unchanged executor produces `UNSETTLED`. An older complete
publication must not be substituted when a later eligible incomplete publication is
the repository's latest eligible state. This preserves the distinction between an
absent record in a complete publication, which the existing evaluator may treat as a
loss, and absence from incomplete evidence, which may not be treated as a loss.

The payout temporal selection policy is latest eligible publication at or before the
explicit per-race cutoff. It is neither unbounded latest nor a caller-supplied
publication ID. The exact eligible repository state at or before the cutoff is a
determinism precondition, not an immutable standalone replay identity. A repository
change observed strictly after the cutoff has no effect; an inserted, backfilled, or
changed fact eligible at or before the cutoff is a changed replay input.

C4g2a does not persist an immutable record of which repository-supplied
`PayoutPublication.publication_id` was selected. Any returned publication retains its
repository-supplied ID, but c4g2a uses neither that ID nor a synthetic digest as a
selector. Complete run-level settlement-evidence audit persistence belongs to a later
c4g2c/application phase if required.

No existing protocol, repository implementation, schema, or migration changes are
required for c4g2a. `RaceResultRepository.get_race_result()` is sufficient because the
current formal result model is one insert-only result per race and its returned
`observed_at` can be screened by the historical source. `PayoutRepository` is sufficient
because it already exposes bounded latest selection.

## Settlement Temporal Boundary

The boundary is an exact aware `settlement_cutoff` per internal race ID. Prediction
`information_cutoff` is not reused or renamed; the two cutoffs have distinct causal
meanings.

Formal temporal invariants are:

- every settlement cutoff is timezone-aware;
- no race result with `observed_at > settlement_cutoff` enters settlement;
- no payout publication with `observed_at > settlement_cutoff` enters settlement;
- facts observed exactly at the cutoff are eligible;
- `PersistedRaceResult` and `PayoutPublication` retain their existing
  `finalized_at <= observed_at` domain invariant;
- for a fully settled race, the unchanged executor's
  `settled_at = max(result.finalized_at, required publication.finalized_at...)`, and
  therefore `settled_at <= settlement_cutoff`; and
- no current-time comparison or fallback is allowed.

No additional inequality is imposed between scheduled start and official observation.
Official void/cancellation timing may legitimately differ, and the existing persisted
domains already own finalized/observed consistency. Prediction facts remain constrained
by their separate snapshot information cutoff.

## C4g2b Public Composition

Prepared implementation module:

`scripts/simulation/historical_settlement_simulation.py`

Prepared exact module-local public surface:

```python
__all__ = (
    "execute_historical_settlement_simulation",
)
```

Prepared exact keyword-only boundary:

```python
def execute_historical_settlement_simulation(
    *,
    snapshots: tuple[HistoricalInputSnapshot, ...],
    run_context: SimulationRunContext,
    strategy_identity: StrategyIdentity,
    settlement_cutoffs_by_race_id: Mapping[int, datetime],
    bet_plan_snapshot_source: SimulationBetPlanSnapshotSource,
    race_result_repository: RaceResultRepository,
    payout_repository: PayoutRepository,
) -> SimulationSummary:
    ...
```

The exact snapshot tuple mirrors c4g1. Empty snapshots with an empty cutoff mapping are
valid after shared-boundary validation and return the existing empty
`SimulationSummary`. No new result dataclass is introduced.

The composition validates all statically provable facts before the first bet-plan,
race-result, or payout read:

1. exact tuple and exact `HistoricalInputSnapshot` items;
2. exact `SimulationRunContext`;
3. exact `StrategyIdentity`;
4. settlement-cutoff Mapping boundary, one defensive copy, positive exact race-ID keys,
   and aware datetime values;
5. structural `load_snapshot`, `get_race_result`, and
   `get_latest_payout_publication` collaborators;
6. exact `RuleBasedBetStrategy.__name__` strategy binding;
7. canonical snapshot sort;
8. duplicate internal race-ID rejection;
9. exact cutoff-key coverage of batch race IDs; and
10. every snapshot dataset match, with the first mismatch selected in canonical order
    using c4g0/c4g1's exact `SimulationValidationError` shape.

Canonical order is ascending:

```python
(
    snapshot.race.scheduled_start_at,
    snapshot.internal_race_id,
)
```

After preflight, c4g2b calls
`build_simulation_race_input_from_historical_snapshot(snapshot=...)` exactly once per
canonical snapshot. All pure adapter calls complete before post-race repository I/O.
The reconstructed input is used only for race identity, prediction cutoff in exact plan
identity, and the executor/Simulator boundary. No prediction pipeline is built or run.

C4g2b, not c4g2a, owns the exact persisted-plan binding. It constructs exactly:

```python
bet_source = PersistedSimulationBetSource(
    run_context=run_context,
    snapshot_source=bet_plan_snapshot_source,
)
```

The exact constructed `PersistedSimulationBetSource` object is injected into the c4g2a
historical source. C4g2b does not accept an arbitrary external `SimulationBetSource`.
The exact run-context and snapshot-source objects are preserved, and the existing bet
source alone constructs and loads the five-field `SimulationBetPlanIdentity`.

C4g2b then constructs one unchanged `PersistedRaceSimulationExecutor` and one unchanged
`Simulator`, all sharing the caller's exact run context, strategy identity,
repositories, and frozen cutoff values as applicable. It calls `Simulator.run(...)`
exactly once with the canonically ordered race-input tuple and returns that exact
`SimulationSummary`.

## Bet Plan and Settlement Policies

C4g2b's exact `PersistedSimulationBetSource` selects the saved c4g1 plan by the existing
five-field `SimulationBetPlanIdentity`. There is no latest-plan lookup, fallback plan,
another run/strategy/cutoff substitution, or bet regeneration. Missing persisted
snapshot fails closed and is not `NO_BET`. A present exact persisted snapshot with
empty bets is the legitimate historical `NO_BET` case; the resulting c4g2a empty-tuple
short circuit performs no official result or payout read.

Payout matching remains exactly `bet_type` plus canonical internal
`race_entry_ids`. No horse name, horse number fallback, external ID, prediction ID,
legacy lookup, or numeric-coincidence remapping is allowed.

The unchanged settlement status policy is:

- present exact persisted empty plan -> `NO_BET`;
- missing or after-cutoff race result -> `UNSETTLED`;
- partial race result -> `UNSETTLED`;
- official void race result -> `VOID`;
- unsupported official result or payout status -> `UNSUPPORTED`;
- missing or incomplete required payout publication -> `UNSETTLED`; and
- complete result plus sufficient complete required payout evidence -> `SETTLED`.

Repository corruption, invalid identity, and inconsistent domain data propagate as
errors. They do not become `UNSETTLED`, `NO_BET`, or a loss. Existing refund/void payout
record evaluation is reused unchanged; c4g2 does not redesign payout arithmetic.

## Summary Semantics

`Simulator` and its formal summary logic are reused unchanged:

- only `SETTLED` races contribute settled investment, payout, profit, ROI, settled-bet
  hit rate, and settled-purchase race hit rate;
- `NO_BET` contributes a race count and `NO_BET` count but no planned bets or settled
  money;
- `UNSETTLED`, `VOID`, `ERROR`, and `UNSUPPORTED` never turn planned stake into settled
  investment or loss;
- ROI is `payout * 100 / investment`, or `None` when settled investment is zero;
- bet hit rate is settled hit bets divided by settled bets;
- race hit rate is hit settled purchase races divided by settled purchase races;
- by-bet-type aggregation remains the existing exact aggregation; and
- maximum drawdown remains over `SETTLED` results ordered by
  `(settled_at, race_id)` with initial peak zero.

The public c4g2b result is `SimulationSummary` only. Per-race results are created once
inside `Simulator` but are not exposed by its current API. Per-race result persistence
or audit output is not required to establish the summary composition and would require
a distinct c4g2c/later architecture decision. C4g2a/b must not modify `Simulator` or
execute each race twice merely to expose results.

C4g2c is optional for the current summary computation. Separately, c4g2a/b do not own
full run-level settlement-evidence audit persistence. If replay independent of later
eligible-state mutation is required, a later c4g2c/application phase may freeze the
selected payout publication IDs, result identity or digest, per-race
`SimulationResult`, and equivalent audit evidence without making c4g2a depend on that
future phase.

## Failure, Writes, and Determinism

C4g2a/b perform reads only. They do not persist results, payouts, settlement results, or
summaries and own no transaction.

If settlement raises for canonical race R3 after R1/R2 were evaluated, the exact error
propagates, no partial `SimulationSummary` is returned, later races are not executed,
and there is no settlement mutation to roll back. Existing c4g1 bet plans remain
immutable and untouched.

For the same exact historical snapshots, run context, strategy identity, exact persisted
bet plans, per-race settlement cutoffs, exact eligible official repository state at or
before those cutoffs, code revision, and equivalent successful repository behavior, c4g2
produces an equal `SimulationSummary`. Caller snapshot order, process date, process
restart, publications observed after cutoff, current time, random state, network state,
and process-local state do not affect the result.

The guarantee does not cover a newly inserted/backfilled or otherwise changed eligible
fact whose `observed_at` is at or before the cutoff. Such eligible repository state is
an explicit changed replay input. Publications added strictly after the cutoff are
invisible. C4g2a/b provide deterministic computation under this precondition but no
immutable settlement-evidence identity across repository mutation.

## Official Acquisition and Provider Scope

The persisted settlement domain and c4g2 source/composition remain provider-neutral.
The repository contains pure Raw-to-persisted result and payout conversion providers and
provider-neutral SQLite persistence, but no formally complete target-race official
result-plus-payout acquisition and persistence composition for either JRA or NAR.

The existing JRA historical replay's result evidence supports retained past-race input
construction; it is not a target-race payout acquisition boundary. The existing NAR/JRA
capture modules likewise do not constitute a complete normalized target-result and
payout persistence flow.

Therefore real end-to-end provider coverage is currently `NONE_COMPLETE`. A separate
official result/payout capture, conversion, identity, and persistence phase is required
before a real JRA or NAR historical run can populate these repositories. That work must
not be hidden inside c4g2a/b and does not authorize HTTP, parsing, or capture work here.
It is not a blocker to implementing and testing the provider-neutral c4g2a source
against the existing formal repositories, but it remains an explicit blocker for a real
data end-to-end historical settlement application.

## Frozen Decision Summary

```text
PHASE_SPLIT:
C4G2A_THEN_C4G2B

C4G2A_BET_SOURCE_TYPE:
SIMULATION_BET_SOURCE

C4G2A_EXACT_PERSISTED_PLAN_GUARANTEE:
NO

C4G2A_BET_TUPLE_VALIDATION:
EXACT_TUPLE_OF_SIMULATION_BET_MATCHING_RACE_AND_STRATEGY_WITH_UNIQUE_BET_IDENTITIES

C4G2B_EXACT_PLAN_SOURCE:
PERSISTED_SIMULATION_BET_SOURCE

C4G2B_BET_PLAN_IDENTITY_POLICY:
EXACT_FIVE_FIELD_SIMULATION_BET_PLAN_IDENTITY_LOAD

C4G2B_MISSING_PLAN_POLICY:
FAIL_CLOSED_NOT_NO_BET

C4G2A_EMPTY_BET_SOURCE_RESULT:
SHORT_CIRCUITS_POST_RACE_IO_WITHOUT_PROVING_PERSISTED_PLAN_ORIGIN

C4G2B_EXACT_EMPTY_PLAN_POLICY:
EXACT_PRESENT_PERSISTED_EMPTY_PLAN_IS_LEGITIMATE_HISTORICAL_NO_BET

PUBLIC_C4G2_INPUT:
EXACT_SNAPSHOT_TUPLE_PLUS_RUN_CONTEXT_PLUS_STRATEGY_IDENTITY_PLUS_PER_RACE_SETTLEMENT_CUTOFFS_PLUS_EXACT_BET_PLAN_SOURCE_PLUS_RESULT_AND_PAYOUT_REPOSITORIES

PUBLIC_C4G2_RESULT:
SIMULATION_SUMMARY

PER_RACE_RESULT_VISIBILITY_REQUIRED:
NO_NOT_FOR_C4G2B

PREDICTION_EXECUTION_IN_C4G2:
NO

BET_GENERATION_IN_C4G2:
NO

C4G0_CALL:
NO

C4G1_CALL:
NO

SIMULATOR_REUSED:
YES_UNCHANGED_IN_C4G2B

PERSISTED_RACE_EXECUTOR_REUSED:
YES_UNCHANGED

PERSISTED_BET_SOURCE_REUSED:
YES_UNCHANGED_IN_C4G2B

REPOSITORY_BACKED_SETTLEMENT_SOURCE_REUSED_UNCHANGED:
NO_FOR_HISTORICAL_REPLAY

NEW_HISTORICAL_SETTLEMENT_SOURCE_REQUIRED:
YES_C4G2A

SETTLEMENT_DOMAIN:
PERSISTED_PROVIDER_NEUTRAL_OFFICIAL_DOMAIN

SETTLEMENT_TEMPORAL_BOUNDARY:
EXPLICIT_AWARE_SETTLEMENT_CUTOFF_BY_INTERNAL_RACE_ID

GLOBAL_OR_PER_RACE:
PER_RACE

CURRENT_CLOCK_FALLBACK:
NO

RACE_RESULT_AFTER_SETTLEMENT_CUTOFF_POLICY:
TREAT_AS_UNAVAILABLE_AND_DO_NOT_PLACE_IN_SETTLEMENT_BUNDLE

PAYOUT_TEMPORAL_SELECTION_POLICY:
LATEST_ELIGIBLE_PUBLICATION_AT_OR_BEFORE_EXACT_SETTLEMENT_CUTOFF

PAYOUT_COMPLETENESS_POLICY:
REQUIRE_COMPLETE_FALSE_THEN_OMIT_LATEST_ELIGIBLE_INCOMPLETE_PUBLICATION

SETTLEMENT_DETERMINISM_REPOSITORY_PRECONDITION:
EXACT_ELIGIBLE_REPOSITORY_STATE_AT_OR_BEFORE_CUTOFF

POST_CUTOFF_REPOSITORY_CHANGE_EFFECT:
NONE

AT_OR_BEFORE_CUTOFF_BACKFILL_OR_CHANGE:
CHANGED_REPLAY_INPUT

IMMUTABLE_SETTLEMENT_EVIDENCE_IDENTITY_IN_C4G2A:
NO

UNBOUNDED_LATEST_PAYOUT:
FORBIDDEN

BET_PLAN_REPLAY_POLICY:
C4G2B_OWNS_EXACT_FIVE_FIELD_SIMULATION_BET_PLAN_IDENTITY_LOAD

MISSING_PLAN_POLICY:
FAIL_CLOSED_NOT_NO_BET_IN_C4G2B

NO_BET_RACE_RESULT_READ:
NO

NO_BET_PAYOUT_READ:
NO

C4F1_ADAPTER_REUSED_FOR_SETTLEMENT:
YES_IN_C4G2B

ADAPTER_CALL_COUNT_PER_RACE:
EXACTLY_ONE

C4G2_SNAPSHOT_COLLECTION_TYPE:
EXACT_TUPLE_OF_EXACT_HISTORICAL_INPUT_SNAPSHOT

CANONICAL_RACE_ORDER:
ASCENDING_SCHEDULED_START_AT_THEN_INTERNAL_RACE_ID

ALL_STATIC_PREFLIGHT_BEFORE_POST_RACE_IO:
YES

POST_RACE_FACTS_ALLOWED:
YES_ONLY_IN_SETTLEMENT_BOUNDARY

TARGET_RESULT_TO_PREDICTION_PATH:
FORBIDDEN

PAYOUT_TO_PREDICTION_PATH:
FORBIDDEN

SETTLED_AT_POLICY:
MAX_COMPLETE_RESULT_AND_REQUIRED_PAYOUT_FINALIZED_AT

SETTLEMENT_STATUS_POLICY:
EXISTING_PERSISTED_EXECUTOR_POLICY_UNCHANGED

PAYOUT_MATCH_IDENTITY:
BET_TYPE_PLUS_CANONICAL_INTERNAL_RACE_ENTRY_IDS

SIMULATION_SUMMARY_SEMANTICS_REUSED:
YES_UNCHANGED

ROI_DENOMINATOR:
EXISTING_SETTLED_INVESTMENT_ONLY

UNSETTLED_FINANCIAL_POLICY:
NO_SETTLED_MONEY_AND_NOT_A_LOSS

MAX_DRAWDOWN_ORDER:
EXISTING_SETTLED_AT_THEN_RACE_ID

PERSISTED_SIMULATION_RUN_SERVICE_USED:
NO

PROVIDER_BACKED_EXECUTOR_USED:
NO

RESULT_PAYOUT_ACQUISITION_READY:
NO_FOR_REAL_END_TO_END_TARGET_RACE_SETTLEMENT

ADDITIONAL_OFFICIAL_CAPTURE_PHASE_REQUIRED:
YES_SEPARATE_FROM_C4G2A_AND_C4G2B

SETTLEMENT_PROVIDER_NEUTRAL:
YES

REAL_DATA_PROVIDER_COVERAGE:
NONE_FORMALLY_COMPLETE_FOR_TARGET_RESULT_PLUS_PAYOUT

RACE_RESULT_REPOSITORY_SUFFICIENT:
YES_WITH_CUTOFF_SCREENING_IN_C4G2A

PAYOUT_REPOSITORY_SUFFICIENT:
YES_USING_EXISTING_BOUNDED_LATEST_API

SCHEMA_CHANGE_REQUIRED:
NO

MIGRATION_REQUIRED:
NO

C4G2_WRITES:
NO

PARTIAL_SUMMARY_RETURN:
NO

LATER_RACES_AFTER_SETTLEMENT_FAILURE:
NOT_EXECUTED

SETTLEMENT_DETERMINISM_CONTRACT:
SAME_EXACT_INPUTS_CUTOFFS_AND_ELIGIBLE_REPOSITORY_STATE_PRODUCE_EQUAL_SUMMARY_POST_CUTOFF_FACTS_IRRELEVANT

FULL_RUN_SETTLEMENT_EVIDENCE_AUDIT_PERSISTENCE:
NOT_OWNED_BY_C4G2A_OR_C4G2B

C4G2C_OPTIONAL_FOR_CURRENT_SUMMARY_COMPUTATION:
YES

NEXT_IMPLEMENTATION_PHASE:
4C-2d3b1i6d1d5f1c4g2a_CUTOFF_AWARE_HISTORICAL_PERSISTED_SETTLEMENT_SOURCE
```

## Implementation Scope

C4g2a production implemented:

- `scripts/simulation/historical_persisted_race_settlement_source.py` (new)

C4g2a dedicated test implemented:

- `tests/test_historical_persisted_race_settlement_source.py` (new)

C4g2b future production:

- `scripts/simulation/historical_settlement_simulation.py` (new)

C4g2b future dedicated test:

- `tests/test_historical_settlement_simulation.py` (new)

Each implementation phase may update only its phase docs in addition to its one new
production and one new test file. Existing `simulator.py`, `persisted_executor.py`,
`persisted_simulation_bet_source.py`, generic settlement source, c4f1, c4g0, c4g1,
models, protocols, SQLite repositories, schemas, migrations, and package roots remain
unchanged.

## Implemented C4g2a Test Contract

C4g2a tests pin:

- exact public surface and structural `PersistedRaceSettlementSource` compatibility;
- structural `SimulationBetSource` constructor compatibility without requiring
  `PersistedSimulationBetSource`;
- aware per-race cutoffs, defensive mapping freeze, and missing-key failure;
- exact tuple return required from the bet source;
- invalid bet item, race-ID mismatch, strategy-ID mismatch, and duplicate bet identity
  rejected through the frozen historical-source `SimulationValidationError` policy;
- bet-source exceptions propagate unchanged where appropriate;
- empty returned tuple -> no result or payout repository call, without claiming
  persisted-plan origin;
- race result before/at cutoff eligible and after cutoff absent;
- bounded payout call with the exact cutoff and `require_complete=False`;
- payout before/at cutoff eligible and after cutoff invisible;
- later publication after cutoff cannot change older-cutoff replay;
- latest eligible incomplete publication is not replaced by an older complete one;
- complete-publication missing selection remains existing loss semantics downstream;
- exact race-entry-ID payout matching;
- collaborator corruption and invalid values fail closed without broad translation;
- no unbounded latest, current clock, SQLite concrete dependency, write, HTTP, provider,
  raw conversion, prediction, planning, or broad catch; and
- generic settlement source, repositories, protocols, schemas, and migrations remain
  unchanged.

C4g2a tests do not claim run-ID, strategy-config-hash, information-cutoff snapshot
identity, repository provenance, or missing persisted-snapshot behavior from an
arbitrary recording `SimulationBetSource`.

## Future C4g2b Test Contract

C4g2b tests must pin:

- exact public API/type hints and no package-root export;
- exact tuple boundary, empty-batch behavior, canonical ordering, race-ID tie-break,
  duplicate rejection, cutoff-key exact coverage, and defensive cutoff freeze;
- all static validation and all c4f1 conversions before post-race I/O;
- exact dataset and RuleBased strategy binding;
- c4f1 exactly once per race and no prediction/c4g0/c4g1 call;
- exact `PersistedSimulationBetSource` construction with the exact run-context and
  exact `bet_plan_snapshot_source` objects, followed by exact reuse in the c4g2a source;
- exact construction/reuse of the c4g2a source,
  `PersistedRaceSimulationExecutor`, and `Simulator`;
- exact five-field `SimulationBetPlanIdentity` load;
- missing persisted snapshot fails closed and is not `NO_BET`;
- exact persisted empty plan -> `NO_BET` without official reads;
- win, complete-publication loss, refund/void, missing payout, partial result, official
  void, unsupported, and corruption paths;
- exact investment, payout, profit, ROI, hit counts/rates, counts by status,
  by-bet-type values, and existing maximum-drawdown order;
- exact exception propagation, no partial summary, and no later race after failure;
- same frozen inputs/cutoffs/eligible repository state -> equal summary;
- later-after-cutoff publications are irrelevant;
- no result/payout fact reaches prediction or mutates a bet plan;
- no writes, current clock, random, HTTP, live acquisition, latest snapshot selection,
  `PersistedSimulationRunService`, or broad fallback; and
- c4f1, c4g0, c4g1, executor, simulator, generic source, repository, schema, and
  migration blobs remain unchanged.

## Implementation Scope and Review State

This implementation changes exactly:

- `docs/CURRENT_PHASE.md`
- `docs/LATEST_CODEX_REPORT.md`
- `scripts/simulation/historical_persisted_race_settlement_source.py`
- `tests/test_historical_persisted_race_settlement_source.py`

Dedicated verification passed `15 tests, 23 subtests`; the related persisted settlement,
bet-source, executor, and simulator contracts passed `205 tests, 61 subtests`; and the
full suite passed `2940 tests, 1998 subtests`. No live HTTP or trusted capture was
performed.

```text
IMPLEMENTATION_STATUS:
READY_FOR_REVIEW

PRODUCTION_IMPLEMENTATION:
COMPLETE

DEDICATED_TEST_CONTRACT:
COMPLETE

BLOCKERS:
NONE_PENDING_INDEPENDENT_REVIEW
REAL_END_TO_END_RESULT_PAYOUT_ACQUISITION_REMAINS_A_SEPARATE_REQUIRED_PHASE
```

Formal integration is not complete. C4g2b remains unstarted. Stop after pushing the
implementation review branch for independent review.
