# Current Phase

## Status

APPROVED_FOR_CODEX

## Phase

Phase 4C-2d3b1f — PersistedSimulationBetSource adapter

## Base Commit

`eab9a03 docs: approve repository backed selection resolver`

## Branch

`feature/ver0.8-simulator`

## Objective

Implement a concrete, non-exported `PersistedSimulationBetSource` that structurally satisfies the
existing `SimulationBetSource` Protocol by loading one immutable
`SimulationBetPlanSnapshot` through `SimulationBetPlanSnapshotSource` and returning its already
persisted bet tuple without recomputation or reconstruction.

## Allowed Files

- `scripts/simulation/persisted_simulation_bet_source.py`
- `tests/test_persisted_simulation_bet_source.py`
- `docs/LATEST_CODEX_REPORT.md`

## Forbidden Files

- `AGENTS.md`
- `docs/CURRENT_PHASE.md` after approval and during implementation
- `docs/VER0.8_SIMULATOR_DESIGN.md`
- `scripts/simulation/bet_source.py`
- `scripts/simulation/bet_plan_snapshot_repository.py`
- `scripts/simulation/bet_plan_identity.py`
- `scripts/simulation/bet_plan_snapshot.py`
- `scripts/simulation/models.py`
- `scripts/simulation/repositories/sqlite_bet_plan_snapshot_repository.py`
- `scripts/simulation/bet_plan_builder.py`
- `scripts/simulation/repository_backed_selection_resolver.py`
- `scripts/simulation/persisted_executor.py`
- `scripts/simulation/persisted_settlement.py`
- package `__init__.py` files and package-root exports
- all other production code and tests
- schema, migrations, database, Pipeline, CLI, production composition, and `logs/`

## Proposed Contract

### Constructor and dependency choice

The constructor uses the existing, fully validated `SimulationRunContext`, not a bare `run_id`.
The fixed context prevents run-ID regeneration and keeps dataset/commit provenance available for
future composition. The approved API is:

```python
class PersistedSimulationBetSource:
    def __init__(
        self,
        *,
        run_context: SimulationRunContext,
        snapshot_source: SimulationBetPlanSnapshotSource,
    ) -> None:
        ...

    def load_bets(
        self,
        *,
        race_input: SimulationRaceInput,
        strategy_identity: StrategyIdentity,
    ) -> tuple[SimulationBet, ...]:
        ...
```

The constructor is keyword-only, stores the exact injected `run_context` and Snapshot Source,
does not call the Source, and validates that `run_context` is `SimulationRunContext` and
`snapshot_source.load_snapshot` is callable. Each constructor violation raises `ValueError`.
It must not use runtime `isinstance` checks against the non-runtime-checkable Snapshot Source
Protocol, create a synthetic `race_id=0`, raise `SimulationValidationError`, or trim, normalize,
or regenerate any run field.

### Requested snapshot identity

For a valid `load_bets()` call, construct exactly one new `SimulationBetPlanIdentity` from existing
values without trimming, normalizing, or recomputing any field:

| Identity field | Source |
| --- | --- |
| `run_id` | `self._run_context.run_id` |
| `race_id` | `race_input.race_id` |
| `strategy_id` | `strategy_identity.strategy_id` |
| `strategy_config_hash` | `strategy_identity.strategy_config_hash` |
| `information_cutoff` | `race_input.information_cutoff` |

The Adapter validates concrete `SimulationRaceInput` and `StrategyIdentity` input before calling
the Snapshot Source. Each direct-input violation raises `ValueError` and makes zero Source calls.
For each valid input, it calls
`snapshot_source.load_snapshot(identity=requested_identity)` exactly once with that identity. It
does not retain an identity cache, mutate either input, create a run ID, access current time, or
perform a second lookup.

### Snapshot-response and exception policy

`None` has the existing Snapshot Source meaning of **not found**, not an empty plan. It must fail
closed as
`SimulationValidationError(race_input.race_id, "simulation_bet_plan_snapshot", ...)`. The same
established simulation-boundary exception applies only to an Adapter-detected non-
`SimulationBetPlanSnapshot` response or a snapshot whose `identity != requested_identity`.

Constructor violations (`run_context` not `SimulationRunContext`, or a non-callable Snapshot Source
method) and direct `load_bets()` input violations (`race_input` not `SimulationRaceInput`, or
`strategy_identity` not `StrategyIdentity`) raise `ValueError`. They do not call the Snapshot
Source. The Adapter never uses `"persisted_simulation_bet_source"` as a validation identifier.

The equality check covers all five identity fields, including `run_id`, race, strategy ID, strategy
config hash, and cutoff. It is value equality rather than identity equality; timezone-aware datetime
equality therefore preserves the persisted identity instant without requiring display-offset equality.

Exceptions raised by `snapshot_source.load_snapshot()`, including `RepositoryValidationError`,
`RepositoryDataIntegrityError`, `RepositoryConflictError`, and arbitrary unexpected exceptions,
propagate unchanged. The Adapter must not catch, wrap, translate, or create a replacement exception
for a Source failure.

### Returned bets and empty plans

After type and full identity validation, return `snapshot.bets` directly. Do not call `tuple()`,
copy, sort, validate individual bets, recalculate policy/budget/stake, rebuild `SimulationBet`, or
otherwise normalize snapshot content. Direct return preserves the snapshot tuple object, bet order,
and every contained bet object identity.

An existing snapshot with `bets == ()` is the persisted, valid NO_BET plan and returns the same
empty tuple. It is distinct from a missing snapshot (`None`), which fails closed.

### Dependency boundaries

The module may depend only on the two Protocol/domain snapshot modules, `SimulationRunContext`,
`SimulationRaceInput`, `StrategyIdentity`, `SimulationBet`, `SimulationValidationError`, and
ordinary Python typing. It must not import a concrete SQLite repository or SQLite, Provider,
Prediction, Builder, Resolver, Settlement, Simulator, Pipeline, CLI, network, time, cache, schema,
or migration module. It is not package-root exported and is not a production composition root.

## Required Tests

The new dedicated test file must cover at least:

- constructor and `SimulationBetSource` signature/type-hint compatibility;
- full `SimulationRunContext` injection, with no bare-run-ID constructor alternative;
- invalid `run_context` and non-callable Snapshot Source as `ValueError`, and no constructor-time
  Snapshot Source call;
- direct `SimulationRaceInput` and `StrategyIdentity` validation with zero Source calls on invalid
  inputs and `ValueError` results;
- construction of each requested identity field from the prescribed object and field;
- exactly one Snapshot Source call for a valid input, including identity value equality;
- snapshot type and complete identity validation, including mismatches in each identity field;
- successful direct return of the original bet tuple, preserving tuple, bet order, and bet object
  identity;
- a persisted empty snapshot returning its empty tuple and `None` failing closed distinctly;
- `SimulationValidationError` for Adapter-detected violations;
- unchanged object-identity propagation of repository and arbitrary Source exceptions;
- no policy, budget, stake, or bet recomputation/reconstruction;
- no DB, SQLite, Builder, Resolver, Settlement, Provider, Pipeline, CLI, network, current-time,
  cache, package-root export, schema, or migration dependency.

Run after implementation:

```text
python -m pytest tests/test_persisted_simulation_bet_source.py -q
python -m pytest tests/test_simulation_bet_source_contract.py tests/test_simulation_bet_plan_snapshot_repository_contract.py tests/test_simulation_bet_plan_snapshot.py tests/test_persisted_simulation_bet_source.py -q
python -m pytest -q
git diff --check
git status --short
```

Also search the implementation and dedicated tests for concrete SQLite, Source-exception wrapping,
Builder, Resolver, Settlement, cache, and composition dependencies.

## Stop Condition

Stop and report without implementation if the required fail-closed exception policy requires a new
exception or a change to existing Protocols/models, if a Snapshot Repository or SQLite change is
needed, if Builder/Resolver/Executor composition becomes necessary, if tests fail outside scope, or
if Git status contains unexpected files. Do not stage, commit, or push during this phase.
