# Current Phase

## Status

APPROVED_FOR_CODEX

## Phase

Phase 4C-2d3b1g — Repository-backed persisted settlement source

## Base Commit

`cc51822 docs: approve persisted simulation bet source`

## Branch

`feature/ver0.8-simulator`

## Objective

Implement the concrete `RepositoryBackedPersistedRaceSettlementSource` at
`scripts/simulation/repository_backed_persisted_settlement_source.py`. It structurally implements
the existing `PersistedRaceSettlementSource` by composing the existing `SimulationBetSource`,
`RaceResultRepository`, and `PayoutRepository` into one validated
`PersistedRaceSettlementData` value.

## Allowed Files

- `scripts/simulation/repository_backed_persisted_settlement_source.py`
- `tests/test_repository_backed_persisted_settlement_source.py`
- `docs/LATEST_CODEX_REPORT.md`

`docs/CURRENT_PHASE.md` is not an implementation change target.

## Forbidden Files and Scope

- `AGENTS.md`, `docs/CURRENT_PHASE.md`, and `docs/VER0.8_SIMULATOR_DESIGN.md`
- `scripts/simulation/persisted_settlement.py`
- `scripts/simulation/persisted_simulation_bet_source.py`
- `scripts/simulation/persisted_executor.py`
- `scripts/simulation/bet_source.py`
- `scripts/simulation/repositories/interfaces.py`
- concrete SQLite repositories, schema, migrations, database, and `logs/`
- Provider, raw Source, Builder, Resolver, Simulator, Pipeline, CLI, production composition,
  integration tests, package-root export, cache, retry, and logging
- all other production code and tests

## Formal API

```python
class RepositoryBackedPersistedRaceSettlementSource:
    def __init__(
        self,
        *,
        bet_source: SimulationBetSource,
        race_result_repository: RaceResultRepository,
        payout_repository: PayoutRepository,
    ) -> None:
        ...

    def load_settlement_data(
        self,
        *,
        race_input: SimulationRaceInput,
        strategy_identity: StrategyIdentity,
    ) -> PersistedRaceSettlementData:
        ...
```

## Constructor and direct-input validation

The keyword-only constructor validates only that the following dependency methods are callable:

- `bet_source.load_bets`
- `race_result_repository.get_race_result`
- `payout_repository.get_latest_payout_publication`

Each constructor violation raises `ValueError`. Do not runtime-check the non-runtime-checkable
Protocols, inspect signatures, invoke test calls, wrap/copy dependencies, retain a Repository
exception class in the production module, or call a dependency in the constructor. Retain each
injected object by identity.

`load_settlement_data()` accepts only concrete `SimulationRaceInput` and `StrategyIdentity`.
Each direct-input violation raises `ValueError` and makes zero Bet Source, RaceResult Repository,
and Payout Repository calls.

## Formal processing flow

1. Call the Bet Source exactly once for valid direct inputs:

   ```python
   bets = bet_source.load_bets(
       race_input=race_input,
       strategy_identity=strategy_identity,
   )
   ```

   Pass the original `race_input` and `strategy_identity` objects. Do not catch, wrap, retry, or
   translate a Bet Source exception.
2. Before any Repository call, validate that `bets` is exactly a `tuple`; every item is a
   `SimulationBet`; every bet has the requested race and strategy IDs; and every
   `(bet_type, race_entry_ids)` identity is unique. A violation raises:

   ```python
   SimulationValidationError(
       race_input.race_id,
       "simulation_bet_source",
       reason,
   )
   ```

   Do not rebuild the tuple or bets, sort, alter stake/rank/selection/cutoff, or make a Repository
   call after a malformed Bet Source response.
3. If `bets == ()`, return the normal NO_BET bundle:

   ```python
   PersistedRaceSettlementData(
       race_id=race_input.race_id,
       bets=bets,
       race_result=None,
       payout_publications_by_bet_type={},
   )
   ```

   This path makes exactly one Bet Source call and zero Repository calls.
4. For non-empty bets, call
   `race_result_repository.get_race_result(race_input.race_id)` exactly once. `None` is valid and
   means an absent persisted result. A non-`None` response must be `PersistedRaceResult` with the
   requested race ID, otherwise raise:

   ```python
   SimulationValidationError(
       race_input.race_id,
       "race_result_repository",
       reason,
   )
   ```

   Repository exceptions propagate as their original exception object.
5. Derive required bet types in first-occurrence order only:

   ```python
   required_bet_types = tuple(dict.fromkeys(bet.bet_type for bet in bets))
   ```

   Do not sort, recreate bets, request unpurchased types, or alter the order.
6. For each distinct required type, call the Payout Repository exactly once:

   ```python
   publication = payout_repository.get_latest_payout_publication(
       race_id=race_input.race_id,
       bet_type=bet_type,
       observed_at_lte=None,
       require_complete=False,
   )
   ```

   Prediction cutoff must not be supplied as `observed_at_lte`; settlement data is not bounded by
   the prediction timeline. Do not use `require_complete=True` or make a second fallback lookup.
7. For a non-`None` Payout response, require `PayoutPublication`, the requested race ID, and the
   requested bet type. A violation raises:

   ```python
   SimulationValidationError(
       race_input.race_id,
       "payout_repository",
       reason,
   )
   ```

   A `None` response is an absent payout fact. An incomplete response (`is_complete is False`) is
   also omitted from the mapping; do not retain it, re-query a complete publication, create a
   placeholder, or convert it to `None` through a fallback. Only a complete response is stored in
   the mapping under its requested bet type.
8. After all response checks, construct exactly one bundle:

   ```python
   PersistedRaceSettlementData(
       race_id=race_input.race_id,
       bets=bets,
       race_result=race_result,
       payout_publications_by_bet_type=publications,
   )
   ```

   Preserve the Bet Source tuple and contained bet object identities. Do not catch, wrap, or
   translate an exception raised by the bundle constructor.

## Exception and dependency policy

- Constructor and direct-input violations: `ValueError`.
- Malformed Bet Source response: `SimulationValidationError` identifier `simulation_bet_source`.
- Malformed RaceResult response: `SimulationValidationError` identifier `race_result_repository`.
- Malformed Payout response: `SimulationValidationError` identifier `payout_repository`.
- Existing bundle validation errors and all dependency exceptions propagate unchanged by object
  identity.
- Do not add DB/SQLite, SQL, raw conversion, Provider, time, cache, retry, logging, Executor,
  Simulator, Builder, Resolver, Pipeline, CLI, network, package-root export, or
  `target_race_count` dependencies.

## Required Tests

Create a dedicated test module covering at least:

- constructor and `PersistedRaceSettlementSource` signature/type-hint compatibility;
- callable-only constructor validation, no runtime Protocol checks, no constructor calls, and
  dependency identity retention;
- invalid direct inputs with zero calls to all dependencies;
- one Bet Source call with original argument objects and dependency exception identity propagation;
- malformed Bet Source tuple/type/race/strategy/duplicate identity cases, each with zero
  Repository calls and the `simulation_bet_source` identifier;
- normal NO_BET bundle with zero Repository calls;
- non-empty one RaceResult lookup and one Payout lookup per distinct type;
- first-occurrence type order, no unpurchased type, and no bet reconstruction/sort;
- RaceResult normal `None`, malformed type, and wrong-race cases;
- Payout normal `None`, malformed type, wrong race/type, exact keyword arguments, and exception
  identity propagation;
- complete-only mapping behavior, incomplete omission, no fallback, and no re-query;
- exact bundle construction, tuple/bet identity preservation, and unchanged bundle exceptions;
- absence of prohibited dependencies, package export, and `target_race_count`.

Run after implementation:

```text
python -m pytest tests/test_repository_backed_persisted_settlement_source.py -q
python -m pytest tests/test_persisted_settlement_contract.py tests/test_persisted_simulation_bet_source.py tests/test_simulation_repositories.py tests/test_persisted_race_simulation_executor.py tests/test_repository_backed_persisted_settlement_source.py -q
python -m pytest -q
git diff --check
git status --short
```

Also search the implementation and dedicated tests for runtime Protocol checks, concrete SQLite,
Provider, raw conversion, cache/retry, exception wrapping, fallback Payout lookup, package-root
export, and `target_race_count`.

## Stop Condition

Stop and report if implementation requires a change to a Protocol, model, bundle contract, SQLite
repository, schema, migration, executor, or composition boundary; if a required error policy cannot
be implemented within the allowed files; if an out-of-scope test fails; or if Git contains
unexpected files. Do not stage, commit, push, create a review branch, or begin a subsequent phase.
