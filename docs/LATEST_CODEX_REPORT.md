# Latest Codex Report

## Status

READY_FOR_REVIEW

## Current Phase

Phase 4C-2d3b1i3b - Multi-race persisted simulation run orchestration

Base commit: `0d2d8cd docs: approve persisted simulation identity accessors`

## Implementation

Added `scripts/simulation/persisted_simulation_run_service.py` with
`PersistedSimulationRunService`. Its keyword-only constructor retains exact
`PersistedSimulationBetPlanService` and `Simulator` objects. Constructor and every `run()` verify
the exact persisted concrete chain and the three public-API object-identity relationships before
Planning begins.

`run()` validates all Sequence race inputs, all Mapping budgets, duplicate race IDs, positive
non-bool budget keys, budget value types, and exact race-ID/budget-key equality before any Snapshot
save. It snapshots input collections without mutation, fixes execution order to
`(scheduled_start_at, race_id)`, calls `build_and_save()` once for every ordered race with the exact
race and budget objects, then calls `Simulator.run()` once with the exact ordered tuple. The returned
`SimulationSummary` is returned unchanged.

Empty runs make zero Planning calls and execute `Simulator.run()` once. Planning failure preserves
already-saved immutable Snapshots, stops later Planning and simulation, and propagates the exact
exception object. Simulator failure likewise propagates unchanged after all Snapshots are saved; no
retry, rollback, deletion, compensation, fallback, Snapshot reload, or Snapshot/Summary validation
duplication was added. Backend write/read object and connection coherence remain Phase 4C-2d3b1i4
composition-root responsibilities.

## Tests

Added `tests/test_persisted_simulation_run_service.py` using exact production planning, settlement,
executor, and Simulator components with existing structural collaborators supplied as recording
fixtures. It covers API/slots, zero constructor work, validation before side effects, official order,
exact forwarding, empty runs, Planning failure, Simulator failure, and run-time composition
revalidation.

Extended `tests/test_persisted_simulation_integration.py` with one in-memory SQLite mixed three-race
scenario. Caller order is deliberately unsorted; the service saves all Snapshots in official order.
It verifies a SETTLED win, a non-zero-budget empty NO_BET Snapshot, and a non-empty UNSETTLED race.
All Snapshots are created through one `PersistedSimulationRunService.run()` call; no manual Snapshot,
allocation-plan, direct builder, or direct repository save is used by the new scenario.

Mixed summary result:

```text
race_count = 3
settled_race_count = 1
no_bet_race_count = 1
unsettled_race_count = 1
settled_purchase_race_count = 1
bet_count = 2
settled_bet_count = 1
hit_bet_count = 1
hit_race_count = 1
investment = 100
payout = 300
profit = 200
roi = Decimal("300")
bet_hit_rate = Decimal("100")
race_hit_rate = Decimal("100")
maximum_drawdown = 0
```

## Verification

```text
Dedicated service test: 7 passed, 9 subtests passed
Integration test: 6 passed, 4 subtests passed
Related contracts: 200 passed, 95 subtests passed
Full suite: 2291 passed, 2 skipped, 710 subtests passed
Forbidden-pattern search in new production/test diffs: no matches
git diff --check: success
```

`tests/test_persisted_executor.py` does not exist; the related verification used the existing
`tests/test_persisted_race_simulation_executor.py` instead. Existing production modules, manual
integration coverage, and 1i2 real-Pipeline scenarios are unchanged. No migration, schema, CLI,
package-root export, or `target_race_count` change was made.

Phase 4C-2d3b1i4 and later phases remain unstarted. `database/keiba.db` and `logs/` are outside
scope. No file has been staged, committed, pushed, or placed on a review branch for this phase.

blocker: none
