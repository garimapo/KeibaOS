# Current Phase

## Status

APPROVED_FOR_CODEX

## Phase

Phase 4C-2d3b1i2 — Prediction-to-persisted-simulation integration

## Base Commit

`3bf1ae4 docs: approve persisted bet plan service`

## Branch

`feature/ver0.8-simulator`

## Objective

Prove that a Snapshot generated and saved by `PersistedSimulationBetPlanService` can be loaded
unchanged through the already-persisted simulation path and produce a final
`SimulationSummary`. The test uses only an in-memory SQLite connection and real production
components:

```text
SimulationRaceInput
→ PredictionPipeline
→ PersistedSimulationBetPlanService
→ FixedStakeBetAllocator
→ SimulationBetPlanBuilder
→ SQLiteSimulationBetPlanSnapshotRepository
→ PersistedSimulationBetSource
→ RepositoryBackedPersistedRaceSettlementSource
→ PersistedRaceSimulationExecutor
→ Simulator.run()
→ SimulationSummary
```

## Proposed Implementation Scope

Preferred test file: `tests/test_persisted_simulation_integration.py`.

The existing file already owns the isolated parent schema, migrations, `horses` seed data,
race-result and payout fixtures, downstream composition, and manual-persistence regression
scenarios. Adding two service-originated cases there avoids duplicating private fixture setup and
keeps the existing manual scenarios intact. A new test file would improve topical isolation but
would duplicate the SQLite setup or improperly import the existing test class's private helpers.

The existing manual Snapshot scenarios must remain unchanged. The new cases must not manually
construct a `BetPlan`, `BetRecommendation`, `BetAllocationPlan`, or `SimulationBetPlanSnapshot`,
or directly call allocator, Builder, or Snapshot Repository save. They must write only through:

```python
service.build_and_save(race_input=race_input, budget=budget)
```

## Real Pipeline Contract

Use an exact `PredictionPipeline` instance, not a subclass, fake, patched `run`, patched engine,
or preconstructed `PipelineResult`/`BetPlan`:

```python
PredictionPipeline(
    PipelineConfig(
        ability_engine=AbilityEngine(reference_date=date(2026, 8, 1)),
        pace_engine=PaceEngine(),
        jockey_engine=JockeyEngine(reference_date=date(2026, 8, 1)),
        track_engine=TrackEngine(reference_date=date(2026, 8, 1)),
        predictor=Predictor(),
        value_engine=ValueEngine(),
        bet_generator=BetGenerator(),
        bet_strategy=RuleBasedBetStrategy(),
        strategy_config=strategy_config,
    )
)
```

The integration test must assert the exact production classes of the Pipeline, its
`PipelineConfig`, and each configured Ability, Pace, Jockey, Track, Predictor, Value, Generator,
and RuleBased strategy component. It must not execute the Pipeline separately to inspect its
result; the service-produced persisted Snapshot is the proof of the real Pipeline outcome.

The same `StrategyConfig` value used by this `PipelineConfig` creates `StrategyIdentity`.
`BetPlan.strategy_name` is the real `RuleBasedBetStrategy` name and is not compared with the
caller-defined `StrategyIdentity.strategy_name`.

Static code inspection establishes the non-empty fixture: one race entry with empty past races
receives neutral engine scores; the single Prediction receives softmax probability `1`; positive
odds `2.0` produce expected value `2.0`; `BetGenerator` emits one WIN recommendation; and the
default `RuleBasedBetStrategy` selects it. The integration test must assert this observed
persisted outcome rather than alter Pipeline output to make it fit expected values.

## Scenario A — Real Pipeline, non-empty Snapshot, SETTLED

- Use an isolated race ID and one seeded horse/race-entry ID from the existing SQLite fixture.
- Build a valid audited `SimulationRaceInput` with fixed timezone-aware datetimes, one entry,
  no past races, valid positive odds, and `race_horse_count == 1`.
- Use fixed-stake allocation policy (`stake_amount=100`), a real Pipeline, and
  `BetStakeBudget(total_amount=100)`.
- Build and save through the service; assert a non-empty Snapshot, its formal five-field identity,
  policy identity, budget 100, resolved race-entry selection, and natural-identity Repository load
  equality.
- Persist the same race's COMPLETE result and a complete winning WIN payout of 300 per 100.
- Compose the existing persisted source, settlement source, executor, and `Simulator` using the
  same run context and strategy identity. Assert one SETTLED result with planned and settled
  investment 100, payout 300, profit 200, and one hit.
- Assert the one-race Summary: settled count 1, bet and settled-bet counts 1, hit counts 1,
  investment 100, payout 300, profit 200, ROI `Decimal("300")`, hit rates `Decimal("100")`, and
  maximum drawdown 0. Its WIN `by_bet_type` aggregate has one bet, one settled and hit bet,
  investment 100, payout 300, profit 200, and both rates `Decimal("300")` / `Decimal("100")`.

## Scenario B — Real Pipeline NO_BET, persisted empty Snapshot, NO_BET

- Use another isolated seeded race ID and the same valid one-entry input shape.
- Use a real Pipeline whose `StrategyConfig.allowed_bet_types` is `frozenset()` and whose
  allocation policy remains the fixed-stake policy. Pipeline, Predictor, Value Engine, and
  BetGenerator still run; the real RuleBased strategy returns an empty `BetPlan`.
- Persist only through the service with `BetStakeBudget(total_amount=500)`.
- Assert that the loaded Snapshot is empty, retains budget 500, has allocated amount 0 and
  unallocated amount 500.
- Do not persist a race result or payout. Existing settlement-source and executor contracts return
  NO_BET before looking up settlement facts for an empty bet tuple.
- Assert one NO_BET result with planned investment 0 and a one-race Summary with no bets,
  investment/payout/profit all 0, and `no_bet_race_count == 1`.

## Identity, Database, and Isolation

All composed components must use the same `run_context.run_id`, strategy ID, strategy config
hash, race ID, and information cutoff. Do not substitute prediction time, scheduled start, current
time, or database values into Snapshot identity.

Create `sqlite3.connect(":memory:")` per test, create the existing parent `races`/`horses` schema
and seed each test race, commit it, then run `apply_migrations(connection)`. Continue using the
existing repository transaction expectations. Do not use `database/keiba.db`, a file database,
network, Providers, or current-time APIs. Do not share Snapshot state, a connection, run ID, or
race ID between scenarios.

## Failure-Scenario Decision

Do not add Repository conflict, identity mismatch, or insufficient-budget integration tests in this
phase. They are already covered at repository/service boundaries; duplicating them would not prove
the new real-Pipeline-to-persisted path. This phase is intentionally limited to one successful
non-empty SETTLED path and one successful NO_BET path.

## Allowed Files During Implementation

- `tests/test_persisted_simulation_integration.py`
- `docs/LATEST_CODEX_REPORT.md`

`docs/CURRENT_PHASE.md` is not an implementation target after approval.

## Forbidden Files and Scope

No production code, existing manual integration assertion deletion, schema/migration, package
export, CLI, database file, network, Provider, Pipeline/Engine patch, fake/subclass Pipeline,
manual BetPlan/Recommendation/Allocation/Snapshot generation, direct allocator/Builder/Repository
save, `Any`, `cast`, or `type: ignore`. Do not start Phase 4C-2d3b1i3.

```text
blocker: none
```

## Required Tests

```powershell
python -m pytest tests/test_persisted_simulation_integration.py -q
python -m pytest tests/test_persisted_bet_plan_service.py tests/test_prediction_input_contracts.py -q
python -m pytest -q
git diff --check
git status --short
```

Use existing test names only; do not introduce mypy or pyright configuration.

## Stop Condition

Stop without implementing if the real Pipeline fixture does not produce the stated non-empty or
NO_BET behavior, the real component path needs a production change, an existing manual assertion
would need removal, an out-of-scope failure occurs, or commit approval is required.
