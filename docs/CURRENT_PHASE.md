# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase

`4C-2d3b1i6d1d5f1c4e` — JRA historical replay snapshot persistence composition.

Formal base: `ce5e749337a4d8675b728ee99368f024de29fef2`.

Review branch:
`review/4c-2d3b1i6d1d5f1c4e-jra-historical-snapshot-persistence-prepare`.

## Purpose and Phase Split

C4d already turns one exact durable `JRARaceReplaySeed` into one complete
`HistoricalInputSnapshot` without writing. It remains unchanged and read-only.

The next work is split to preserve ownership:

1. **c4e** loads one exact seed by `seed_id`, runs c4d, atomically persists the exact
   completed snapshot, exact-reloads it by its immutable identity, and returns a compact
   persisted reference.
2. **c4f** consumes an exact persisted snapshot and purely adapts it to the established
   `SimulationRaceInput` / `PredictionPipelineInput` boundary. It does not reacquire,
   rebuild, or enrich historical facts.

Combining these would mix SQLite transaction/restart behavior with prediction-domain
conversion. C4e therefore performs no prediction, simulation, bet construction, or
snapshot-to-pipeline conversion.

## Existing Snapshot Repository

`SQLiteHistoricalInputSnapshotRepository` already consumes the exact snapshot emitted by
c4d and requires no schema, migration, table, column, trigger, or index change.

Existing APIs are:

```python
save_snapshot(
    *,
    snapshot: HistoricalInputSnapshot,
) -> None

load_latest_snapshot(
    *,
    dataset_id: str,
    race_id: int,
    information_cutoff: datetime,
    source_identity: HistoricalExternalRaceIdentity,
) -> HistoricalInputSnapshot | None
```

The stored natural identity is exactly:

```text
dataset_id
+ organization
+ source_system
+ external_race_id
+ captured_at
```

`source_url`, internal IDs, `information_cutoff`, and `content_sha256` are not natural
identity fields. They are immutable canonical content and therefore affect the derived
`content_sha256`. Save requires an exact `HistoricalInputSnapshot`, starts one
`BEGIN IMMEDIATE` transaction, writes the complete normalized object graph, and commits
only after all children succeed. Re-saving the same natural identity and digest is an
idempotent no-op. The same natural identity with a different digest raises
`RepositoryConflictError`; no overwrite or repair occurs.

The existing latest loader is causal and source-isolated, but it is not an exact
persistence-reference loader. It selects the greatest eligible `captured_at` for the
requested dataset, internal race, source race, and cutoff. A later eligible snapshot can
therefore supersede an earlier candidate. That is correct for its existing API but is not
the restart-stable handoff required by c4e.

## Exact Persistence Reference and Load

C4e adds no schema. It adds a narrow exact natural-identity load method to the existing
concrete repository:

```python
load_snapshot_by_identity(
    *,
    identity: HistoricalInputSnapshotIdentity,
) -> HistoricalInputSnapshot | None
```

It queries only the five natural-identity columns. Zero rows returns `None`; more than
one row or any malformed header/child/mapping/digest is `RepositoryDataIntegrityError`.
It fully reconstructs and validates the snapshot and never falls back to an older,
newer, other-source, or legacy row. The existing `load_latest_snapshot(...)` contract is
unchanged.

The composition returns a frozen/slotted reference containing exactly:

```text
seed_id
snapshot_identity
content_sha256
```

After `save_snapshot(...)` succeeds, c4e calls the exact identity loader once and requires
the reconstructed identity and digest to equal the c4d snapshot. Archive or snapshot
enrichment cannot change that reference. Missing exact reload is unavailable; mismatch or
corruption fails closed. Repository/provider integrity and conflict exceptions propagate
unchanged.

## C4e Composition Contract

The future pure-application orchestration accepts one canonical `seed_id` plus injected
read-only seed/capture/history providers and an injected snapshot persistence boundary.
Its deterministic order is:

```text
validate seed_id and collaborators
-> load exact durable JRARaceReplaySeed once
-> require returned seed.seed_id equals requested seed_id
-> call build_jra_race_historical_replay(...) once
-> require replay result retains that exact seed
-> save the exact replay snapshot once
-> exact-reload by snapshot identity once
-> require exact identity and content_sha256 equality
-> return persisted snapshot reference
```

No result is returned before durable save and exact reload succeed. `None` from the seed
source or exact snapshot reload is a dedicated unavailable error. C4d validation,
unavailable, and unsupported categories remain distinguishable; provider/repository
exceptions are not collapsed into absence. There is no broad exception catch.

The d0 materializer already creates the same application-database `races`, `horses`,
`historical_input_source_identities`, `historical_input_external_races`, and
`historical_input_external_entries` lineage that the snapshot repository checks. C4d
uses the seed's exact internal race/entry IDs. Consequently d0-created mappings satisfy
all snapshot-save prerequisites; c4e reuses them exactly and any forward/reverse mismatch
remains `RepositoryConflictError` or `RepositoryDataIntegrityError`.

## Prediction Handoff Finding

`HistoricalInputSnapshot` is not currently accepted directly by prediction or simulation:

- `PredictionPipeline.run(...)` accepts the structural `PredictionPipelineInput` contract.
- `SimulationRaceInput` accepts `RacePredictionInput` or `ImmutableRacePredictionInput`
  plus `InputSnapshotAudit`.
- `assemble_persisted_simulation_race_inputs(...)` currently builds those values from
  mutable request-document race mappings, not from the formal snapshot repository.
- CLI `DatabaseRaceInputProvider` still reads legacy `races`, `horses`, `past_races`, and
  `horses.odds`; that path is ineligible for historical replay input.

C4f therefore requires a new pure adapter from one exact `HistoricalInputSnapshot` to one
`SimulationRaceInput`. It must use only the snapshot's exact internal race-entry IDs,
track, entry, jockey, win-odds, ordered past-race, cutoff, and provenance values. It may
not query mutable tables, map by horse name, equate horse and entry IDs by numeric
coincidence, or use result/payout/settlement facts. Exact Decimal-to-prediction-number and
provenance-to-`InputAuditEntry` conversion will be frozen in c4f's own PREPARE before
implementation.

## Future-Leakage Guard

For both phases:

- no live/current fallback;
- no latest-snapshot substitution for an exact persisted reference;
- no legacy race, horse, past-race, jockey, or odds content after the formal snapshot is
  available;
- no horse-name mapping or entry-identity reconstruction;
- no information observed or available after `snapshot.information_cutoff`;
- no race result, payout, settlement, or final-odds substitution into prediction input;
- no timestamp rewriting and no invented availability;
- no snapshot overwrite, partial save, silent repair, or cross-source fallback.

## Future Implementation Files

Immediate c4e production:

```text
scripts/simulation/jra_race_historical_snapshot_persistence.py
scripts/simulation/repositories/sqlite_historical_input_snapshot_repository.py
```

Immediate c4e tests:

```text
tests/test_jra_race_historical_snapshot_persistence.py
tests/test_sqlite_historical_input_snapshot_repository.py
```

Following c4f candidate production:

```text
scripts/simulation/historical_input_snapshot_simulation_adapter.py
```

Following c4f candidate tests:

```text
tests/test_historical_input_snapshot_simulation_adapter.py
```

Both implementation phases may also update only `docs/CURRENT_PHASE.md` and
`docs/LATEST_CODEX_REPORT.md`. C4e must not modify c4d, prediction, simulation models,
snapshot schema/migrations, package-root exports, CLI, live capture, or settlement.

## Required C4e Tests

- exact public surface/signatures and frozen/slotted persisted reference;
- malformed seed ID or collaborator rejected before provider/repository use;
- exact seed loaded once and exact seed ID rechecked;
- c4d called once with the exact loaded seed and unchanged providers;
- exact c4d snapshot saved once and no success before save;
- idempotent existing equivalent snapshot succeeds;
- same-identity/different-content conflict propagates unchanged;
- exact identity load returns the persisted snapshot after process restart;
- exact load never calls or delegates to `load_latest_snapshot`;
- later eligible snapshot enrichment cannot substitute the referenced snapshot;
- missing exact seed or exact persisted snapshot is unavailable;
- malformed/corrupt selected snapshot is integrity failure, never absence;
- d0-created race and entry mappings are reused exactly without new identity inference;
- archive/c4d/provider errors propagate according to their established contracts;
- no prediction, simulation, snapshot persistence inside c4d, HTTP, clock, current/legacy
  fallback, result/payout use, package-root export, or schema/migration change;
- full related and repository regressions plus full pytest suite and `git diff --check`.

## Stop Condition

Stop after this docs-only PREPARE review commit is pushed. Do not implement c4e, begin
c4f, modify the formal branch, or run prediction/simulation until independent review
approves this contract.
