# Latest Codex Report

## Status

APPROVED_FOR_COMMIT

## Phase

Phase 4C-2d3b1i2 — Prediction-to-persisted-simulation integration

Base commit: `3bf1ae4 docs: approve persisted bet plan service`

## Preparation Result

Phase 4C-2d3b1i1 is formally complete on `feature/ver0.8-simulator`. Its new
`PersistedSimulationBetPlanService` is the missing write-side boundary: it creates and persists a
Snapshot, while the existing persisted simulation integration test currently begins after a manual
`BetPlan → allocation → Builder → Snapshot Repository save` sequence.

The proposed Phase 4C-2d3b1i2 adds two service-originated paths to the existing
`tests/test_persisted_simulation_integration.py`. This is preferred to a new test file because the
existing class already owns the in-memory parent schema, migration invocation, horse seed helpers,
SQLite repositories, settlement fixtures, and downstream composition. Existing manual Snapshot
scenarios remain as lower-level regression coverage; none will be removed or replaced.

No production change is needed. The integration setup may create the real repositories, resolver,
settlement data, and `:memory:` SQLite database, but a new Snapshot must be written only through
`PersistedSimulationBetPlanService.build_and_save()`.

## Real Pipeline Feasibility

The test will instantiate an exact `PredictionPipeline` with an explicit `PipelineConfig` and
fixed reference date `2026-08-01`; it will not use a Pipeline subclass, fake, patch, test-double
strategy, or prebuilt Pipeline result/plan. `AbilityEngine` and `JockeyEngine` receive the fixed
reference date, eliminating their `date.today()` fallback.

For Scenario A, one seeded entry, empty past races, and odds `2.0` are sufficient. Empty history
produces neutral engine scores; the single prediction has softmax probability 1; `ValueEngine`
computes EV 2; `BetGenerator` produces one WIN recommendation; and real
`RuleBasedBetStrategy` admits it under the default allowed bet types. With fixed stake 100 and
budget 100, the expected persisted Snapshot has one bet and the final winning payout fixture of
300 produces one SETTLED result: investment 100, payout 300, profit 200, ROI 300, hit rates 100,
and maximum drawdown 0.

For Scenario B, a real Pipeline with `StrategyConfig(allowed_bet_types=frozenset(),
allocation_policy=policy_config)` still evaluates Prediction, Value, and BetGenerator but the real
strategy returns an empty plan. The service must persist an empty Snapshot with explicit budget
500, allocated amount 0, and unallocated amount 500. The existing settlement source returns early
for empty bets, so no result or payout record is needed; executor and Simulator return NO_BET with
planned investment 0 and a zero-money Summary.

For both scenarios, Pipeline config and `StrategyIdentity` use equal strategy config values.
`BetPlan.strategy_name` remains the real strategy class name and is not compared to the
caller-defined strategy identity name. Snapshot identity uses only run ID, race ID, strategy ID,
strategy-config hash, and information cutoff; it does not use prediction time or scheduled start.

## Scope and Failure Coverage

No additional conflict, identity-mismatch, or insufficient-budget integration case is proposed:
the service and repository tests already exercise those fail-closed boundaries. This phase proves
only the missing real-Pipeline write path plus its normal non-empty settlement and normal NO_BET
downstream behavior.

Implementation candidates are `tests/test_persisted_simulation_integration.py` and this report;
`docs/CURRENT_PHASE.md` is preparation-only. Production modules, migrations, schema, CLI,
package exports, `database/keiba.db`, and `logs/` are out of scope. Phase 4C-2d3b1i3 is not
started.

## Verification Plan

```text
python -m pytest tests/test_persisted_simulation_integration.py -q
python -m pytest tests/test_persisted_bet_plan_service.py tests/test_prediction_input_contracts.py -q
python -m pytest -q
git diff --check
git status --short
```

```text
blocker: none
```

No production code or tests were changed during this preparation. No file was staged, committed,
pushed, or placed on a review branch.

## Approval Record

The Phase 4C-2d3b1i2 design is approved for Codex implementation with no blocker and no
production change. The existing `tests/test_persisted_simulation_integration.py` is the sole test
file to extend; its manual Snapshot cases remain intact, and no new integration-test module is
permitted.

The approved scenarios use the exact real `PredictionPipeline` and its named production components
with `REFERENCE_DATE = date(2026, 8, 1)`. The test verifies their exact concrete classes. It must
not patch or subclass the Pipeline/components, prebuild a Pipeline result or plan, directly invoke
allocator/Builder/Repository save, or execute the Pipeline twice.

Scenario A uses the same `StrategyConfig` object to construct the Pipeline and strategy identity,
one entry with odds 2.0, fixed stake and budget 100, and a winning payout of 300. It proves a
single persisted WIN bet and the approved SETTLED Result/Summary values, including WIN aggregate
metrics. Scenario B uses the same real path with `allowed_bet_types=frozenset()` and budget 500;
it persists a valid empty Snapshot retaining the full unallocated budget, stores no settlement
facts, and proves the normal NO_BET Result/Summary path.

All collaborators use the same run context, strategy identity, race ID, and information cutoff.
The identity must exclude run start, scheduled start, and prediction time. Existing unit/repository
coverage remains responsible for conflict, identity-mismatch, and insufficient-budget failures, so
this phase adds no new failure integration scenario.

`docs/CURRENT_PHASE.md` now records `APPROVED_FOR_CODEX`; it is not an implementation target.
Only `tests/test_persisted_simulation_integration.py` and this report may change during execution.

## Implementation Result

Production code was not changed. `tests/test_persisted_simulation_integration.py` now contains two
additional service-originated integration scenarios; all existing manual `BetPlan`, allocation,
Snapshot, settlement-state, and identity-mismatch scenarios remain intact.

Both scenarios construct exact production `PredictionPipeline` / `PipelineConfig` objects with
`AbilityEngine`, `PaceEngine`, `JockeyEngine`, `TrackEngine`, `Predictor`, `ValueEngine`,
`BetGenerator`, and `RuleBasedBetStrategy`. The date-dependent engines use fixed
`REFERENCE_DATE = date(2026, 8, 1)`. The tests assert the concrete classes and do not use a
Pipeline/component patch, subclass, fake, prebuilt Pipeline result, or a second Pipeline run.

Scenario A uses one seeded race entry, empty history, odds 2.0, the same `StrategyConfig` source
for the Pipeline and `StrategyIdentity`, fixed stake/budget 100, and only
`PersistedSimulationBetPlanService.build_and_save()` for Snapshot creation. The persisted Snapshot
contains one WIN bet with stake 100 and resolved race-entry ID. A complete first-place result and
WIN payout 300 then produce a SETTLED result with investment 100, payout 300, profit 200, and one
hit. The one-race Summary has ROI, bet hit rate, and race hit rate `Decimal("300")`,
`Decimal("100")`, and `Decimal("100")`, respectively, with maximum drawdown 0; the WIN aggregate
matches those settled values.

Scenario B uses the same real path with `allowed_bet_types=frozenset()` and budget 500. It saves a
formal empty Snapshot retaining budget 500, allocated amount 0, and unallocated amount 500. No
race result or payout is saved. The persisted settlement path returns NO_BET with planned
investment 0, proving that the Snapshot budget is separate from Result investment; the Summary has
zero money/counts, `None` rates, zero drawdown, and an empty bet-type mapping.

Both scenarios construct Snapshot identity only from run ID, race ID, strategy ID,
strategy-config hash, and information cutoff. They use Repository round trips for verification,
but do not manually construct a recommendation/plan/allocation/Snapshot or directly invoke
allocator, Builder, or repository save. No additional failure integration case was added; existing
repository/service/allocator coverage remains authoritative for those boundaries.

## Verification

```text
Dedicated: tests/test_persisted_simulation_integration.py
5 passed, 4 subtests passed

Related: tests/test_persisted_bet_plan_service.py tests/test_prediction_input_contracts.py
22 passed, 35 subtests passed

Full: python -m pytest -q
2280 passed, 2 skipped, 701 subtests passed

Forbidden-pattern search of the newly added test diff: no matches
git diff --check: success
```

## GitHub Implementation Review Approval

GitHub implementation review is complete. Review commit `9d43c08 review: integrate prediction
with persisted simulation` was confirmed and is committed and pushed on
`review/4c-2d3b1i2-prediction-persisted-integration`. The review confirms that no production code
changed and that the existing manual integration coverage was preserved.

The review approves use of the real `PredictionPipeline` and every production component in its
`PipelineConfig`: Ability, Pace, Jockey, Track, Predictor, Value, Generator, and RuleBased
strategy. No Pipeline subclass, patch, fake, second Pipeline execution, manual
`BetPlan`/`BetRecommendation`/Snapshot construction, or direct Snapshot Repository save is used;
Snapshot creation goes only through `PersistedSimulationBetPlanService.build_and_save()`.

Scenario A is approved as one WIN bet with stake 100, a Repository round trip, SETTLED result,
payout 300, profit 200, and ROI 300%. Scenario B is approved with
`allowed_bet_types=frozenset()`, non-zero budget 500, a formal empty Snapshot, allocated amount 0,
unallocated amount 500, no stored result or payout, normal NO_BET, and planned investment 0. The
formal five-field Snapshot identity, in-memory SQLite-only isolation, and decision not to duplicate
failure integration coverage are approved.

`database/keiba.db` and `logs/` remain out of scope. Phase 4C-2d3b1i3 is not started. The current
state is `APPROVED_FOR_COMMIT`: GitHub implementation review approved, review commit `9d43c08`
committed and pushed, and base-branch integration pending.
