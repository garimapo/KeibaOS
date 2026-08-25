# Current Phase

## Status

READY_FOR_REVIEW

## Phase

`4C-2d3b1i6d1d5f1c4e` — JRA historical replay snapshot persistence composition.

Formal base: `ce5e749337a4d8675b728ee99368f024de29fef2`.

Approved PREPARE: `f73777cde96ca276cb1db78ffeab9bef98b3f413`.

Review branch:
`review/4c-2d3b1i6d1d5f1c4e-jra-historical-snapshot-persistence`.

## Implemented C4e Application Boundary

The new module
`scripts/simulation/jra_race_historical_snapshot_persistence.py` implements the frozen
keyword-only `persist_jra_race_historical_snapshot(...)` application flow:

```text
validate canonical seed ID and every collaborator
-> load exact durable JRARaceReplaySeed once
-> build_jra_race_historical_replay(...) once with unchanged evidence providers
-> save exact HistoricalInputSnapshot once
-> reload once by exact natural identity
-> validate natural fields, source URL, and complete digest
-> return immutable JRAPersistedHistoricalSnapshotReference
```

Its module-local `__all__` is exactly the four persistence error classes,
`JRAPersistedHistoricalSnapshotReference`, and
`persist_jra_race_historical_snapshot`. There is no package-root export.

The frozen/slotted reference contains exactly:

```text
seed_id
snapshot_identity
content_sha256
```

It validates the existing canonical JRA seed-ID grammar, exact
`HistoricalInputSnapshotIdentity`, and exact lowercase SHA-256 grammar.

All six provider callables plus the persistence object's callable `save_snapshot` and
`load_snapshot_by_identity` methods are validated before any collaborator call. The
seed provider is called exactly once and must return an exact `JRARaceReplaySeed` whose
ID equals the request. C4d is called exactly once with the identical seed and the five
evidence-provider objects unchanged. Its result must be an exact
`JRARaceHistoricalReplayResult`, retain the identical seed object, and contain an exact
`HistoricalInputSnapshot`.

C4d validation, unavailable, and unsupported errors translate only to their matching
c4e categories. Repository validation, conflict, integrity, and other provider-owned
integrity errors propagate unchanged. There is no broad exception catch.

The exact replay snapshot is saved once. C4e issues no transaction statements and owns
no cross-provider transaction; the concrete snapshot repository remains the sole
`BEGIN IMMEDIATE` save-transaction owner. No reference is returned before save and
exact reload complete. Retry after a completed save is safe through the repository's
existing immutable idempotence contract.

## Exact Snapshot Repository Load

`SQLiteHistoricalInputSnapshotRepository` now exposes exactly:

```python
load_snapshot_by_identity(
    *,
    identity: HistoricalInputSnapshotIdentity,
) -> HistoricalInputSnapshot | None
```

The input requires exact `HistoricalInputSnapshotIdentity`; invalid caller input raises
`RepositoryValidationError`. The SQL selector uses equality on only these five natural
identity columns:

```text
dataset_id
organization
source_system
external_race_id
captured_at_utc
```

`source_url`, `information_cutoff`, `internal_race_id`, and `content_sha256` are not
selectors. The exact method uses a multiplicity-aware fetch, no cutoff comparison,
ordering, `LIMIT`, latest selection, other-source/legacy fallback, or direct/indirect
`load_latest_snapshot(...)` delegation. Zero rows returns `None`; more than one is
`RepositoryDataIntegrityError`.

Latest and exact selection now share only a neutral full-row reconstruction helper.
Latest-query argument validation, causal selection, and post-selection checks remain in
`load_latest_snapshot(...)`; its semantics are unchanged. Exact load independently
rechecks the five selected natural fields, then reconstructs and validates the complete
header, race, entries, past races, mappings, provenance, evidence, canonical scalar
forms, ordering/cardinality, domain invariants, and stored digest. Corruption remains
`RepositoryDataIntegrityError`, never false absence.

An exact request for snapshot A remains bound to A after database restart and after a
later snapshot B is persisted for the same dataset/source/race. The existing latest
loader may correctly select B under an eligible cutoff, but the exact loader never
substitutes it.

## Exact Reload Proof

After save, c4e calls `load_snapshot_by_identity(identity=result.snapshot.identity)`
exactly once. `None` is persistence unavailable; a wrong returned domain type is
persistence validation. It explicitly compares:

- dataset ID;
- organization;
- source system;
- external race ID;
- captured instant;
- source URL;
- complete content digest.

The source URL is deliberately not a natural selector and is excluded from Python
identity comparison, so its explicit post-reload comparison is mandatory. The digest
proves every immutable content field. Any mismatch fails closed as c4e validation;
repository-detected corruption propagates unchanged.

## Ownership and Leakage Guards

C4d remains unchanged and read-only. C4e contains no SQLite connection, transaction,
HTTP/network, filesystem, subprocess, clock, random, seed materialization, mutable
current/legacy lookup, prediction, simulation execution, betting, settlement, NAR,
schema/migration, or package-root-export ownership. It never calls the latest snapshot
loader and provides no live/current fallback.

C4f remains unimplemented. The later pure snapshot-to-prediction/simulation adapter is
outside this phase.

## Verification

- c4e application tests: **14 passed**;
- SQLite historical snapshot repository tests: **25 passed**;
- related c4d, d0 seed/repository, snapshot-builder, and snapshot-domain tests:
  **130 passed**;
- full pytest suite: **2861 passed** (formal baseline: 2843);
- static public-surface, exact-call, no-latest-delegation, forbidden-dependency,
  no-broad-catch, schema/migration, and six-file scope checks: **PASS**;
- `git diff --check`: **PASS**.

No live HTTP or real trusted capture was performed.

## Changed Files

```text
scripts/simulation/jra_race_historical_snapshot_persistence.py
scripts/simulation/repositories/sqlite_historical_input_snapshot_repository.py
tests/test_jra_race_historical_snapshot_persistence.py
tests/test_sqlite_historical_input_snapshot_repository.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

No schema or migration changed.

## Stop Condition

Stop after the single implementation review commit is pushed. Do not modify the formal
branch, begin c4f, or integrate prediction/simulation until independent review approves
this exact implementation.
