# Latest Codex Report

## Status

READY_FOR_REVIEW

## Phase

Phase 4C-2d3b1i1 — Prediction-to-snapshot persistence service

Base commit: `dafb04d docs: approve prediction immutable input contracts`

## Implementation Report

Implemented `PersistedSimulationBetPlanService` in
`scripts/simulation/persisted_bet_plan_service.py` and added service-unit coverage in
`tests/test_persisted_bet_plan_service.py`. This occurred after the approved contract correction;
`docs/CURRENT_PHASE.md` was not changed during implementation.

The service requires the approved concrete `PredictionPipeline` and
`SimulationBetPlanBuilder` dependencies, retains every injected object by identity, and accepts
the allocator and snapshot repository structurally. Constructor and direct input violations fail
as `ValueError` before collaborators are called.

For each valid call, it revalidates the runtime `PipelineConfig`, verifies strategy-config equality,
requires `strategy_identity.strategy_config.allocation_policy`, derives one allocation-policy
identity, constructs the five-field `SimulationBetPlanIdentity`, and then calls Pipeline,
allocator, Builder, and Repository exactly once in that order. The identity fields are taken only
from: `run_context.run_id`, `race_input.race_id`, `strategy_identity.strategy_id`,
`strategy_identity.strategy_config_hash`, and `race_input.information_cutoff`.

`StrategyIdentity.strategy_name` is intentionally not compared with
`PipelineResult.bet_plan.strategy_name`; they are distinct domain concepts. The service validates
only the approved Pipeline, allocation-plan, and snapshot response boundaries and uses the
specified `SimulationValidationError` identifiers. Collaborator exceptions are not caught or
retried, so Pipeline, allocator, Builder, and Repository exception objects propagate unchanged.

An empty persisted plan follows the full Pipeline → allocator → Builder → Repository path. It saves
and returns the exact empty Snapshot object while preserving the explicit supplied budget; it is
not treated as a missing plan.

## Review Test Strengthening

GitHub review found no production-code correction. The NO_BET contract test now uses an explicit
`BetStakeBudget(500)`, proving that the exact non-zero budget reaches the allocator, allocation
plan, and empty Snapshot unchanged. It verifies `Snapshot.bets == ()`, `allocated_amount == 0`,
and `unallocated_amount == 500`, together with exact Snapshot identity at Repository input and
service return.

The forbidden-dependency test now reads the complete production module rather than only the class
source, verifies both `ast.Import` and `ast.ImportFrom`, and rejects SQLite imports, time calls,
runtime Protocol decoration, `typing.Any`, `typing.cast`, type-ignore comments, concrete SQLite
Repository imports, and package-root export. The production module was not changed.

The final typing regression check closes a module-qualified detection gap: direct `import typing`
and aliased `import typing as t` are now inspected for `typing.Any`, `typing.cast`, `t.Any`, and
`t.cast` AST attributes. Small direct, aliased, and clean sample trees verify the helper itself;
the existing `from typing import Any` / `cast` checks remain in place. Production code was not
changed.

Repository-stage propagation coverage now explicitly verifies object-identity propagation with no
retry for `RepositoryValidationError`, `RepositoryConflictError`, and
`RepositoryDataIntegrityError`; all preceding collaborators are called once and Repository is
called exactly once.

## Verification

```text
Dedicated: python -m pytest tests/test_persisted_bet_plan_service.py -q
18 passed, 35 subtests passed

Related: PredictionPipeline, simulation models, allocation policy, fixed allocator,
stake-allocation contract, Builder, Snapshot, Snapshot Repository protocol,
persisted integration, and service tests
281 passed, 131 subtests passed

Full: python -m pytest -q
2278 passed, 2 skipped, 701 subtests passed

Forbidden-dependency / runtime-Protocol / package-export search: no prohibited production match
git diff --check: success
```

`database/keiba.db` and `logs/` remain out of scope and were not changed by this phase. The latest
correction is committed and pushed on the review branch; GitHub review remains pending. Phase
4C-2d3b1i2 has not been started.
