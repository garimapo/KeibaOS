# KeibaOS Architecture

## Overview

KeibaOS separates source acquisition, parsing, immutable historical inputs,
prediction, purchase planning, official settlement, and reporting. Ver0.8's public
application boundary is deterministic archived historical replay; live acquisition is
a separate concern.

The authoritative detailed design is
[`VER0.8_SIMULATOR_DESIGN.md`](VER0.8_SIMULATOR_DESIGN.md).

## Ver0.8 historical replay flow

```text
HistoricalInputSnapshot
        ↓
PredictionPipeline
        ↓
BetStrategy
        ↓
BetStakeAllocator
        ↓
SimulationBetPlanSnapshot
        ↓
SQLite persisted immutable plan
        ↓
Archived official JRA/NAR result + payout evidence
        ↓
Final historical settlement
        ↓
SimulationSummary
        ↓
Historical replay CLI deterministic JSON
```

`HistoricalInputSnapshot` is an immutable, audited prediction-time boundary. The replay
loads it by exact natural identity; internal race ID is only a binding cross-check.
The real historical `PredictionPipeline` executes the normal responsibility chain:

```text
Engine -> Predictor -> Value -> Generator -> Strategy -> Pipeline
```

Allocation is a separate deterministic step after strategy selection. The resulting
`SimulationBetPlanSnapshot` fixes race, run, strategy/config hash, prediction cutoff,
selection, stake, and purchase order. SQLite persistence is immutable and
conflict-detecting. Settlement later reloads this plan rather than regenerating bets.

## Time and causal boundaries

### Prediction information cutoff

The prediction `information_cutoff` is the latest permitted time for evidence used by
the historical prediction and purchase plan. Snapshot evidence must prove that it was
available and observed within the causal boundary. Missing or unverifiable provenance
fails closed.

### Settlement information cutoff

Each race has a separate settlement information cutoff. Exact archived official
result/payout captures must be observed at or before this later cutoff. Results and
payouts are expected to occur after prediction; they are never passed backward into
the pipeline, strategy, allocator, or persisted plan.

## Application composition

The strict schema-v1 request identifies the main SQLite database, represented provider
archives, run context and target commit, strategy/allocation configuration, race
budgets, exact historical snapshot identities, capture IDs, and settlement cutoffs.
Relative database/archive paths are anchored to the request file.

The request CLI is a thin boundary. The SQLite replay application:

1. applies main-database migrations and exact-loads every requested snapshot;
2. canonicalizes race order and executes one complete planning batch;
3. validates the returned plan coverage and required payout catalog subset;
4. opens only represented JRA/NAR archives in SQLite read-only mode;
5. acquires and persists exact official settlement facts for every race;
6. performs one final settlement pass from the persisted plans and facts; and
7. returns the exact `SimulationSummary` serialized by the CLI.

No archive is opened before planning completes. No provider or latest-capture fallback
exists. Partial immutable writes may remain as an auditable durable prefix after a
failure, but no failed execution returns a final summary.

## Provider and persistence boundaries

Provider capture repositories store immutable official response bytes and identities.
Provider-specific normalizers parse JRA/NAR result and payout pages and map official
horse numbers through the race-local snapshot entry identity. Replay capture archives
are opened with SQLite `mode=ro` and verified `query_only`.

The main database stores historical snapshots, immutable bet plans, normalized official
results, and payout publications. Schema changes are owned by numbered migrations;
operators use the application migration workflow and do not hand-edit tables.

## Supported settlement and reporting

Normal-final archived settlement supports `単勝`, `馬連`, `ワイド`, and `3連複`.
Official payout-per-100-yen facts determine realized payout. Prediction scores and
combination ranking values never substitute for official settlement.

`SimulationSummary` aggregates final status counts, bets, investment, payout, profit,
ROI, hit rates, per-bet-type metrics, and maximum drawdown. Its deterministic JSON is
the Ver0.8 operator output. Missing, malformed, incompatible, unsupported, or non-final
evidence is rejected rather than repaired or guessed.
