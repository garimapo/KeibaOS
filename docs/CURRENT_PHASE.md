# Current Phase

## Status

APPROVED_FOR_CODEX

## Phase

Phase 4C-2d3b1i3a — Persisted simulation identity accessors

## Base Commit

`74d2443 docs: approve prediction persisted integration`

## Branch

`feature/ver0.8-simulator`

## Objective

Add only the readonly public accessors a later multi-race service needs to validate complete
persisted-simulation identity coherence before Planning starts. Do not change runtime workflow,
validation, Repository, Pipeline, settlement, or Summary behavior.

Existing public accessors are `Simulator.strategy_identity`, `Simulator.race_executor`,
`PersistedRaceSimulationExecutor.strategy_identity`, and
`PersistedRaceSimulationExecutor.settlement_source`. This phase adds the missing four properties.

## Formal Production Changes

`scripts/simulation/persisted_bet_plan_service.py`:

```python
@property
def run_context(self) -> SimulationRunContext:
    return self._run_context

@property
def strategy_identity(self) -> StrategyIdentity:
    return self._strategy_identity
```

`scripts/simulation/persisted_simulation_bet_source.py`:

```python
@property
def run_context(self) -> SimulationRunContext:
    return self._run_context
```

Do not add a `snapshot_source` accessor.

`scripts/simulation/repository_backed_persisted_settlement_source.py`:

```python
@property
def bet_source(self) -> SimulationBetSource:
    return self._bet_source
```

Do not add race-result or payout Repository accessors.

## Accessor Contract

Each property returns the exact constructor-injected object with `is`. It must not copy, wrap,
recreate a dataclass, regenerate ID/hash, call a collaborator, read SQLite, consult current time,
or mutate state. It has no setter; assignment raises `AttributeError`. Constructor and method
signatures, validation, exceptions, `__slots__`, Repository/Pipeline calls, and runtime behavior
remain unchanged. Runtime Protocol `isinstance`, `Any`, `cast`, `type: ignore`, and package-root
exports are prohibited.

## Later 1i3b Identity Coherence

After 1i3a, 1i3b may inspect public APIs only:

```python
executor = simulator.race_executor
settlement_source = executor.settlement_source
bet_source = settlement_source.bet_source

bet_plan_service.strategy_identity is simulator.strategy_identity
simulator.strategy_identity is executor.strategy_identity
bet_plan_service.run_context is bet_source.run_context
```

The future composition boundary uses exact concrete persisted components. Private attributes,
value-only comparisons, regenerated identities/contexts, and `BetPlan.strategy_name` are forbidden.

## Allowed Files

```text
scripts/simulation/persisted_bet_plan_service.py
scripts/simulation/persisted_simulation_bet_source.py
scripts/simulation/repository_backed_persisted_settlement_source.py
tests/test_persisted_bet_plan_service.py
tests/test_persisted_simulation_bet_source.py
tests/test_repository_backed_persisted_settlement_source.py
docs/LATEST_CODEX_REPORT.md
```

`docs/CURRENT_PHASE.md` is not an implementation target.

## Forbidden Files and Scope

Do not change `Simulator`, `PersistedRaceSimulationExecutor`, models, Protocol definitions,
migration, schema, SQLite Repository, Prediction Pipeline, CLI, `main.py`, package exports,
`database/keiba.db`, or `logs/`. Do not start 1i3b, 1i4, or later work.

## Required Tests

```powershell
python -m pytest tests/test_persisted_bet_plan_service.py -q
python -m pytest tests/test_persisted_simulation_bet_source.py -q
python -m pytest tests/test_repository_backed_persisted_settlement_source.py -q
python -m pytest tests/test_persisted_bet_plan_service.py tests/test_persisted_simulation_bet_source.py tests/test_repository_backed_persisted_settlement_source.py -q
python -m pytest -q
git diff --check
git status --short
```

Test every accessor as a property with the formal type hint, exact-object identity on repeated reads,
no collaborator call while read, no setter, and existing constructor/runtime regression coverage.

## Stop Condition

Stop if an accessor requires a private workaround, a signature/behavior/validation change, an
out-of-scope file, test failure outside scope, unexpected Git change, or commit approval. Do not
stage, commit, push, or create a review branch without later explicit approval.
