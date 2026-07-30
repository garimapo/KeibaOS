# Current Phase

## Status

APPROVED_FOR_CODEX

## Phase

Phase 4C-2d3b1i5b2a — Persisted simulation application input assembler

## Base Commit

`924a1e4 docs: approve persisted simulation request document loader`

## Branch

`feature/ver0.8-simulator`

## Objective

Assemble only the application-level inputs between the immutable 1i5b1 request document and the
1i5a application runner:

```text
PersistedSimulationRequestDocument
-> database_path
-> SimulationRunContext
-> AllocationPolicyConfig
-> StrategyConfig
-> StrategyIdentity
-> deterministic PredictionPipeline
-> Mapping[int, BetStakeBudget]
-> PersistedSimulationApplicationInputs
```

This phase must not create `SimulationRaceInput`, `RacePredictionInput`, `PastRace`,
`InputAuditEntry`, or `InputSnapshotAudit`. They belong to 1i5b2b. CLI, runner invocation, and
Summary output belong to 1i5c.

```text
1i5b1: JSON request document loader (complete)
1i5b2a: application input assembly (this phase)
1i5b2b: race inputs and audit assembly (unstarted)
1i5c: CLI, runner invocation, and Summary output (unstarted)
```

## Allowed Files

```text
scripts/simulation/persisted_simulation_application_inputs.py
tests/test_persisted_simulation_application_inputs.py
docs/LATEST_CODEX_REPORT.md
```

`docs/CURRENT_PHASE.md` is approved contract documentation, not an implementation target.

## Formal Production API

New module: `scripts/simulation/persisted_simulation_application_inputs.py`

```python
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from scripts.prediction.prediction_pipeline import PredictionPipeline
from scripts.simulation.models import SimulationRunContext, StrategyIdentity
from scripts.simulation.persisted_simulation_request_document import (
    PersistedSimulationRequestDocument,
)
from scripts.simulation.stake_allocation import BetStakeBudget


@dataclass(frozen=True)
class PersistedSimulationApplicationInputs:
    database_path: Path
    run_context: SimulationRunContext
    strategy_identity: StrategyIdentity
    prediction_pipeline: PredictionPipeline
    budgets_by_race_id: Mapping[int, BetStakeBudget]


def assemble_persisted_simulation_application_inputs(
    *,
    document: PersistedSimulationRequestDocument,
) -> PersistedSimulationApplicationInputs:
    ...
```

Only this class and function are public. Private helpers may start with `_`. Do not add a race-input
assembler, combined request bundle, runner wrapper, repository, Protocol, ABC, CLI parser, or
summary formatter.

## Document Boundary

Require exact type, rejecting subclasses:

```python
if type(document) is not PersistedSimulationRequestDocument:
    raise ValueError("document must be a PersistedSimulationRequestDocument")
```

Do not re-read files, parse JSON, inspect duplicate/non-finite JSON, repeat the top-level envelope,
or re-anchor database paths. Those are exclusively 1i5b1 responsibilities.

## Request Schema and Assembly

### Run context

`run_context` requires exactly `run_id`, `dataset_id`, `started_at`, and `target_commit_id`, otherwise
raise `ValueError("run_context keys must exactly match the run context schema")`. The three text
fields must be exact non-empty, non-whitespace `str` values without trimming. Their errors are:

```text
run_context.run_id must be a non-empty string
run_context.dataset_id must be a non-empty string
run_context.target_commit_id must be a non-empty string
```

`started_at` must be exact `str`, parse with `datetime.fromisoformat`, be timezone-aware, and return a
non-`None` UTC offset. `Z` may be interpreted as `+00:00`; naive/date-only values, timezone autofill,
clock fallback, and conversion are forbidden. Invalid values raise:

```text
run_context.started_at must be an ISO 8601 timezone-aware datetime
```

Create `SimulationRunContext(run_id, dataset_id, started_at, target_commit_id)`.

### Strategy and allocation policy

`strategy` requires exactly:

```text
strategy_name
allowed_bet_types
max_bet_count
selection_style
min_combination_score
max_candidates
sort_condition
allocation_policy
```

Missing/extra keys raise `strategy keys must exactly match the strategy schema`.

- `strategy_name` is exact `str` `RuleBasedBetStrategy`; otherwise
  `strategy.strategy_name must be RuleBasedBetStrategy`. No alias, case folding, class import path,
  plugin, or arbitrary class is accepted.
- `allowed_bet_types` is the exact tuple frozen by 1i5b1; otherwise
  `strategy.allowed_bet_types must be an array`. It permits only unique exact `str` values in `単勝`,
  `馬連`, `ワイド`, `3連複`; invalid values raise
  `strategy.allowed_bet_types must contain unique supported bet types`. Empty tuple is valid; convert
  to `frozenset` so input order does not affect identity.
- `max_bet_count` and `max_candidates` are exact non-bool `int` values >= 0; errors are respectively
  `strategy.max_bet_count must be a non-negative integer` and
  `strategy.max_candidates must be a non-negative integer`.
- `selection_style` is exact `str` `box` or `formation`, then `SelectionStyle(value)`; otherwise
  `strategy.selection_style must be box or formation`.
- `min_combination_score` is exact non-bool `int`/`float`, finite, and may be negative; convert to
  float. Invalid input raises `strategy.min_combination_score must be finite`.
- `sort_condition` is exact `str` one of `generator_rank`, `combination_score`, `prediction_score`,
  or `estimated_probability`, then `SortCondition(value)`; otherwise
  `strategy.sort_condition is unsupported`.

`allocation_policy` must be a Mapping, otherwise `strategy.allocation_policy must be an object`; it
requires exactly `policy_name`, `policy_version`, `parameters`, otherwise
`strategy.allocation_policy keys must exactly match the allocation policy schema`.

Only `fixed_stake_per_recommendation` and string version `1` are accepted; errors are
`strategy.allocation_policy.policy_name is unsupported` and
`strategy.allocation_policy.policy_version is unsupported`. `parameters` is Mapping-only, otherwise
`strategy.allocation_policy.parameters must be an object`; it requires only `stake_amount`, otherwise
`strategy.allocation_policy.parameters keys must exactly match the fixed stake schema`. Stake is exact
non-bool positive `int`, multiple of 100, otherwise
`strategy.allocation_policy.parameters.stake_amount must be a positive multiple of 100`.

Create `AllocationPolicyConfig`, then exactly one `StrategyConfig`, then call existing
`build_strategy_identity(strategy_name, strategy_config)`. Do not generate IDs, hashes, SHA-256, or
canonical JSON manually.

### Pipeline

`pipeline` requires exact key `track_reference_date`, otherwise
`pipeline keys must exactly match the pipeline schema`. It is exact `str` ISO `YYYY-MM-DD`, parsed by
`date.fromisoformat`, otherwise `pipeline.track_reference_date must be an ISO date`.

Do not use `date.today`, current time, run/race date, timezone conversion, or inferred date. Build:

```python
track_engine = TrackEngine(reference_date=track_reference_date)
pipeline_config = PipelineConfig(
    track_engine=track_engine,
    bet_strategy=RuleBasedBetStrategy(),
    strategy_config=strategy_config,
)
prediction_pipeline = PredictionPipeline(config=pipeline_config)
```

Other engines use PipelineConfig defaults. Require exact `PredictionPipeline`, `PipelineConfig`,
`RuleBasedBetStrategy`, and `TrackEngine` types; reference date equality; and object identity:

```python
prediction_pipeline.config.strategy_config is strategy_identity.strategy_config
```

### Budgets

`budgets_by_race_id` is a Mapping with canonical positive-integer string keys matching `[1-9][0-9]*`;
otherwise raise `budgets_by_race_id keys must be canonical positive integer strings`. Reject zero,
signs, leading zeroes, decimals, and whitespace; convert accepted keys with `int(key)`.

Each value is Mapping-only, otherwise `budgets_by_race_id values must be objects`; it requires exact
key `total_amount`, otherwise `budget keys must exactly match the budget schema`. Total is exact
non-bool `int`, non-negative and a multiple of 100, otherwise
`budget.total_amount must be a non-negative multiple of 100`. Create `BetStakeBudget(total_amount)`.
Empty budgets are valid. Do not inspect `races` or enforce race/budget key-set agreement in 1i5b2a.

## Output Invariants

`PersistedSimulationApplicationInputs` is frozen and its listed field order is formal. Direct
construction requires: Path database; exact `SimulationRunContext`, `StrategyIdentity`, and
`PredictionPipeline`; Mapping budgets; exact positive non-bool integer keys; and exact
`BetStakeBudget` values. Errors are:

```text
database_path must be a Path
run_context must be a SimulationRunContext
strategy_identity must be a StrategyIdentity
prediction_pipeline must be a PredictionPipeline
budgets_by_race_id must be a Mapping
budgets_by_race_id keys must be positive integers
budgets_by_race_id values must be BetStakeBudget
```

Require exact `PipelineConfig`, shared StrategyConfig identity, and exact `AllocationPolicyConfig`:

```text
prediction_pipeline.config must be a PipelineConfig
prediction_pipeline strategy_config must be strategy_identity.strategy_config
strategy_identity allocation_policy must be an AllocationPolicyConfig
```

Defensively copy budgets into a new race-ID-sorted dict and expose `MappingProxyType`. Do not copy
the immutable domain objects. Caller mutation must not affect output, and output mapping mutation must
fail.

## Formal Order and Failure Semantics

The order is mandatory:

```text
1. document exact type
2. run_context schema and values
3. SimulationRunContext
4. strategy schema, scalar/enum values, allocation policy
5. AllocationPolicyConfig
6. StrategyConfig
7. StrategyIdentity
8. pipeline schema and track date
9. PipelineConfig and PredictionPipeline
10. budgets schema and BetStakeBudget values
11. PersistedSimulationApplicationInputs
```

Never construct later objects after failure. Do not wrap collaborator exceptions. Only `ValueError`
from `datetime.fromisoformat` or `date.fromisoformat` may be translated to the stable field-specific
errors. Broad exception handling, retry, fallback, partial results, logging, print, DB work, and
mutation of the document/nested Mapping are forbidden.

## Responsibility Boundary

Allowed dependencies: datetime/date parsing, `math.isfinite`, `MappingProxyType`, existing run,
policy, strategy, enum, identity, track, pipeline, and budget classes/functions. Forbidden: file or
JSON loading, SQLite/migrations/runner/composition, race/past/audit assembly, repositories, network,
logging, print, argparse, stdout/stderr, exit code, clock/UUID/environment/config loading, `main.py`,
and package-root export.

## Required Tests

Add `tests/test_persisted_simulation_application_inputs.py` using real objects only; mocks, patches,
and monkeypatches are forbidden. Cover API/frozen/field/type invariants, valid direct 1i5b1 documents,
offset and Z parsing, all strategy/enums/policy/identity/pipeline/budget outputs, deterministic double
assembly, and 1i4 preconditions without DB execution.

Cover direct construction validation and defensive-copy mutation rejection; run-context, strategy,
pipeline, and budget matrices, including empty bet types and budgets; and source/AST checks rejecting
file/JSON/DB/runner/race/audit/network/time/CLI/config dependencies, `Any`, `cast`,
`runtime_checkable`, type ignores, and broad except. Only date-parse `ValueError` handlers are allowed.

Run dedicated, related 1i5b1/application/composition/run-service/model tests, full pytest, required
source searches, `git diff --check`, and `git status --short`.

## Forbidden Files and Stop Condition

Do not modify existing production/tests, 1i5b1 loader, 1i5a runner/composition, migration/schema,
`scripts/database.py`, `main.py`, `config/settings.json`, CLI, or package `__init__`. Never
stage/commit `database/keiba.db`, `logs/`, or its contents.

After implementation set `docs/LATEST_CODEX_REPORT.md` to `READY_FOR_REVIEW` and stop. Do not stage,
commit, push, create a review branch, start 1i5b2b/1i5c, read a DB, or invoke the runner.

blocker: none
