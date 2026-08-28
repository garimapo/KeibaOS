# Current Phase

Status: `READY_FOR_REVIEW`

## Identity and scope

- Phase: `4C-2d3b1i6d1d5f1c4h4b`
- Name: `Final historical settlement completeness wrapper`
- Exact formal base: `ca68556c377d8c4ea20b43764648833d36709392`
- Formal branch: `feature/ver0.8-simulator`
- Review branch:
  `review/4c-2d3b1i6d1d5f1c4h4b-final-historical-settlement`
- Git setting: `core.autocrlf=true`; no Git configuration or attributes change is
  authorized.

Allowed and changed files are exactly:

```text
scripts/simulation/final_historical_settlement_simulation.py
tests/test_final_historical_settlement_simulation.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

C4h0 through C4h4a remain frozen. This phase changes no provider normalizer, capture
infrastructure, repository protocol, SQLite implementation, schema, migration,
database, package export, snapshot adapter, persisted plan source, executor, simulator,
or existing historical settlement composition. C4h4c is not started.

## Public boundary

Module-local only, with no package-root export:

```python
def execute_final_historical_settlement_simulation(
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

`__all__` contains only `FinalHistoricalSettlementNotReadyError` and the public
function. The error subclasses `ValueError`. Existing C4g2b argument and collaborator
exceptions propagate unchanged.

## Frozen delegation and finality contract

- C4h4b calls existing `execute_historical_settlement_simulation(...)` exactly once,
  passing every caller-supplied argument through unchanged. It copies, reorders,
  validates, mutates, or reloads none of them.
- C4g2b remains the only owner of canonical race order, snapshot adaptation, persisted
  plan identity/loading, bounded result/payout repository reads, settlement cutoffs,
  latest eligible payout publication ordering, incomplete-latest behavior, matching,
  payout arithmetic, aggregation, and `SimulationSummary` construction.
- The only C4h4b predicate is final race-state completeness:

```text
settled_race_count + no_bet_race_count == race_count
unsettled_race_count == 0
void_race_count == 0
error_race_count == 0
unsupported_race_count == 0
```

- `SETTLED` and `NO_BET` are the only final states. `UNSETTLED`, `VOID`, `ERROR`, and
  `UNSUPPORTED` block final output. A count mismatch also blocks final output.
- If final, the function returns the exact same `SimulationSummary` object returned by
  C4g2b. It never reconstructs a summary, recomputes any metric, or exposes partial
  ROI as final.
- If not final, it raises only `FinalHistoricalSettlementNotReadyError` after C4g2b
  has successfully returned. Missing evidence is never converted to loss, skip, or
  `NO_BET`.

## Ownership exclusions

C4h4b performs no HTTP, capture acquisition/creation, current-clock access, repository
read/write, raw parsing, provider dispatch, prediction, bet generation, allocation,
ticket matching, payout/profit/ROI computation, or independent aggregation. It neither
constructs `HistoricalPersistedRaceSettlementSource`, `PersistedRaceSimulationExecutor`,
or `Simulator`.

## Verification and stop condition

Dedicated tests pin the exact public surface, one unchanged delegate call, final return
identity, all final state combinations, each blocking state, count mismatch, exception
propagation, argument immutability, static ownership, and narrow real-C4g2b paths for
missing result/payout, incomplete payout, unsupported result, and after-cutoff result.

Run the dedicated suite, focused C4g2b/source/executor/simulator-summary/plan-source and
bounded repository-read suites, full suite, `git diff --check`, static scope check, and
clean status. Stop for independent implementation review; do not integrate or begin
C4h4c.
