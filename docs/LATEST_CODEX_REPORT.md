# Latest Codex Report

## Status

READY_FOR_REVIEW

## Prepared Phase

Phase 4C-2d3b1f — PersistedSimulationBetSource adapter

Base commit: `eab9a03 docs: approve repository backed selection resolver`
Branch: `feature/ver0.8-simulator`

## Preparation scope

This preparation examined the existing `SimulationBetSource` and
`SimulationBetPlanSnapshotSource` Protocols, `SimulationBetPlanIdentity`,
`SimulationBetPlanSnapshot`, `SimulationRaceInput`, `StrategyIdentity`,
`SimulationRunContext`, the SQLite Snapshot Repository read semantics, and the authoritative
design. No production code or tests were changed.

The proposed implementation is a new non-exported
`scripts/simulation/persisted_simulation_bet_source.py` with a dedicated test module at
`tests/test_persisted_simulation_bet_source.py`.

## Confirmed existing contracts

- `SimulationBetSource.load_bets(*, race_input, strategy_identity)` returns
  `tuple[SimulationBet, ...]` and has no run argument.
- `SimulationBetPlanSnapshotSource.load_snapshot(*, identity)` returns either a
  `SimulationBetPlanSnapshot` or `None`; `None` is exclusively not found.
- A stored empty `SimulationBetPlanSnapshot` is a valid, distinct persisted plan whose `bets` is
  the ordinary empty tuple.
- `SimulationBetPlanIdentity` has exactly `run_id`, `race_id`, `strategy_id`,
  `strategy_config_hash`, and timezone-aware `information_cutoff`.
- Existing snapshot construction guarantees its immutable `bets` tuple, policy identity, budget,
  and bet/identity invariants. The Adapter must not recalculate or reconstruct them.

## Proposed identity and response behavior

For every valid load, the Adapter will create exactly one identity from the fixed run, the supplied
race input, and the supplied strategy identity, then call the Snapshot Source exactly once. It will
verify that the returned object is `SimulationBetPlanSnapshot` and that its complete identity equals
the requested identity before returning `snapshot.bets` directly. This preserves the tuple object,
its purchase order, and contained `SimulationBet` object identities.

`None` is not an empty plan: it is a missing persisted plan and must fail closed. A stored empty
snapshot is the only path that returns `()`. Adapter-detected direct-input and response violations
are proposed to raise the established `SimulationValidationError`; repository and arbitrary
exceptions emitted by the Snapshot Source propagate unchanged by object identity.

## Approved constructor and exception boundaries

The initial `run_id: str` sketch is not adopted. The approved constructor uses the existing
`SimulationRunContext` object directly:

```python
PersistedSimulationBetSource(
    *,
    run_context: SimulationRunContext,
    snapshot_source: SimulationBetPlanSnapshotSource,
)
```

Only `run_context.run_id` participates in the requested plan identity. `dataset_id`, `started_at`,
`target_commit_id`, strategy name, policy identity, budget, current time, and repository metadata
do not participate. The constructor retains the exact context and Source objects, makes no Source
call, and raises `ValueError` for a non-`SimulationRunContext` or non-callable `load_snapshot`.

Invalid `race_input` or `strategy_identity` also raises `ValueError` before a Source call. Adapter-
detected missing, wrong-type, or identity-mismatched snapshot responses raise
`SimulationValidationError(race_input.race_id, "simulation_bet_plan_snapshot", ...)`. Source-
emitted repository and arbitrary exceptions continue to propagate unchanged by object identity.

## Resolved pre-implementation contract correction

`EXECUTE_APPROVED_PHASE` verification found that `docs/CURRENT_PHASE.md` still contains the
superseded exception wording in its Snapshot-response section: it names
`"persisted_simulation_bet_source"` and describes `SimulationValidationError` for constructor and
direct-input failures. The approved execution instruction instead requires `ValueError` for those
inputs and the exact Snapshot-response identifier `"simulation_bet_plan_snapshot"`.

Because `docs/CURRENT_PHASE.md` was explicitly forbidden during implementation, no production code
or test was changed while the inconsistency was present. This correction updates the phase contract
to the approved split: constructor and direct-input violations are `ValueError`; only missing,
wrong-type, and identity-mismatched Snapshot responses raise
`SimulationValidationError(..., "simulation_bet_plan_snapshot", ...)`.

The approved contract and `docs/CURRENT_PHASE.md` are now aligned. The blocker was resolved before
implementation; production code and tests remained untouched until the approved execution began.

## Implementation

Added `scripts/simulation/persisted_simulation_bet_source.py` with the non-exported concrete
`PersistedSimulationBetSource`. Its keyword-only constructor retains the exact injected
`SimulationRunContext` and Snapshot Source, checks only the concrete run-context type and a
callable `load_snapshot` method, and never invokes the Source.

For each valid `load_bets()` call, the adapter creates one `SimulationBetPlanIdentity` from:

- `run_id`: `run_context.run_id`;
- `race_id`: `race_input.race_id`;
- `strategy_id`: `strategy_identity.strategy_id`;
- `strategy_config_hash`: `strategy_identity.strategy_config_hash`; and
- `information_cutoff`: `race_input.information_cutoff`.

It calls `load_snapshot(identity=...)` exactly once, validates the returned Snapshot type and full
identity, then returns `snapshot.bets` itself without copying, rebuilding, sorting, or
revalidating it. A stored empty snapshot is the valid NO_BET path and returns its same empty tuple.
`None` is a missing persisted plan and fails closed.

Constructor and direct-input violations are `ValueError`. Adapter-detected missing, wrong-type,
and identity-mismatched Snapshot responses are `SimulationValidationError` with the required race
ID and `simulation_bet_plan_snapshot` identifier. Snapshot-Source repository exceptions and
arbitrary exceptions are not caught, so their original objects propagate unchanged.

Added `tests/test_persisted_simulation_bet_source.py` to cover signatures and hints, injection
identity, zero-call invalid paths, identity construction, one-call valid loading, direct tuple and
bet-object identity return, empty versus missing snapshots, response validation metadata, Source
exception identity propagation, and dependency/package boundaries.

## Verification

| Check | Result |
| --- | --- |
| Dedicated persisted adapter tests | `20 passed, 18 subtests passed` |
| Related Source, Snapshot Protocol/domain, identity, run-context, and validation tests | `151 passed, 49 subtests passed` |
| Full pytest suite | `2237 passed, 2 skipped, 641 subtests passed` |
| Forbidden production dependency / wrapping search | `0 matches` |
| Runtime Snapshot Source Protocol check search | `0 matches` |
| Package-root export search | `0 matches` |
| `git diff --check` | success |

## Deliberately excluded

- Snapshot Repository and SQLite changes.
- Schema and migration changes.
- BetPlan Builder and RaceEntry Resolver wiring.
- Persisted executor and settlement changes.
- Provider, Pipeline, Simulator, CLI, cache, package-root export, production composition, and
  integration tests.

## Git and handoff

No files were staged, committed, pushed, or branch-created. `database/keiba.db` and `logs/` remain
outside the phase scope. Awaiting implementation review and explicit commit approval.
