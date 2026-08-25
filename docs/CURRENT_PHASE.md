# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase

`4C-2d3b1i6d1d5f1c4e` — JRA historical replay snapshot persistence composition.

Formal base: `ce5e749337a4d8675b728ee99368f024de29fef2`.

Review branch:
`review/4c-2d3b1i6d1d5f1c4e-jra-historical-snapshot-persistence-prepare`.

## Approved Phase Split

C4d remains unchanged, pure, and read-only. C4e owns only this application flow:

```text
exact seed ID / exact loaded seed
-> build_jra_race_historical_replay(...) exactly once
-> exact HistoricalInputSnapshot
-> save exact snapshot
-> exact natural-identity reload
-> immutable persisted reference
```

C4f remains a separate future phase that purely adapts an exact
`HistoricalInputSnapshot` to `SimulationRaceInput` / prediction input. C4e performs no
prediction, simulation, settlement, or snapshot-to-pipeline conversion. No snapshot
schema or migration change is required.

## Public C4e Surface

Future module:

```text
scripts/simulation/jra_race_historical_snapshot_persistence.py
```

Its module-local `__all__` is exactly:

```python
__all__ = (
    "JRARaceHistoricalSnapshotPersistenceError",
    "JRARaceHistoricalSnapshotPersistenceValidationError",
    "JRARaceHistoricalSnapshotPersistenceUnavailableError",
    "JRARaceHistoricalSnapshotPersistenceUnsupportedError",
    "JRAPersistedHistoricalSnapshotReference",
    "persist_jra_race_historical_snapshot",
)
```

There is no package-root export.

The public errors are frozen as:

```python
class JRARaceHistoricalSnapshotPersistenceError(ValueError): ...

class JRARaceHistoricalSnapshotPersistenceValidationError(
    JRARaceHistoricalSnapshotPersistenceError
): ...

class JRARaceHistoricalSnapshotPersistenceUnavailableError(
    JRARaceHistoricalSnapshotPersistenceError
): ...

class JRARaceHistoricalSnapshotPersistenceUnsupportedError(
    JRARaceHistoricalSnapshotPersistenceError
): ...
```

Error translation is exact:

- malformed `seed_id`, malformed collaborators, or a wrong returned domain object:
  persistence validation;
- seed provider `None` or exact snapshot reload `None`: persistence unavailable;
- c4d validation, unavailable, and unsupported public errors: persistence validation,
  unavailable, and unsupported respectively;
- `RepositoryValidationError`, `RepositoryConflictError`,
  `RepositoryDataIntegrityError`, and other provider-owned integrity errors propagate
  unchanged.

No broad `Exception` or `BaseException` catch is allowed.

## Persisted Reference

Freeze exactly:

```python
@dataclass(frozen=True, slots=True)
class JRAPersistedHistoricalSnapshotReference:
    seed_id: str
    snapshot_identity: HistoricalInputSnapshotIdentity
    content_sha256: str
```

`seed_id` must satisfy the existing canonical JRA replay seed-ID helper,
`snapshot_identity` must have exact type `HistoricalInputSnapshotIdentity`, and
`content_sha256` must be exactly 64 lowercase hexadecimal characters. The reference has
no duplicated race/cutoff/source data, snapshot object, raw evidence, or database row ID.
The digest proves all immutable snapshot content outside the five-column natural
identity.

## Private Structural Protocols

C4e defines a private seed loader directly satisfied by
`SQLiteJRARaceReplaySeedRepository.load_seed`, without importing that concrete
repository:

```python
class _JRARaceReplaySeedByIdProvider(Protocol):
    def __call__(
        self,
        *,
        seed_id: str,
    ) -> JRARaceReplaySeed | None: ...
```

C4e defines a narrow local persistence protocol:

```python
class _HistoricalInputSnapshotPersistence(Protocol):
    def save_snapshot(
        self,
        *,
        snapshot: HistoricalInputSnapshot,
    ) -> None: ...

    def load_snapshot_by_identity(
        self,
        *,
        identity: HistoricalInputSnapshotIdentity,
    ) -> HistoricalInputSnapshot | None: ...
```

The concrete SQLite snapshot repository structurally satisfies this protocol. The
existing domain-level `HistoricalInputSnapshotRepository` protocol is not changed merely
for c4e.

C4e also owns a private `_JRATargetRaceCardCaptureByIdProvider` with c4d's same exact
callable shape: a `capture_id` keyword argument returning
`JRAOfficialTargetRaceCardResponseCapture | None`. C4e does not import c4d's private
protocol or the concrete capture repository. The supplied provider object is passed to
c4d unchanged.

## Public Application API

Freeze the exact keyword-only function:

```python
def persist_jra_race_historical_snapshot(
    *,
    seed_id: str,
    seed_provider: _JRARaceReplaySeedByIdProvider,
    target_race_selection_capture_provider:
        JRATargetRaceSelectionCaptureProvider,
    target_race_card_capture_by_id_provider:
        _JRATargetRaceCardCaptureByIdProvider,
    horse_history_response_provider:
        JRATargetHorseHistoryResponseProvider,
    race_result_response_provider:
        JRAHistoricalRaceResultResponseProvider,
    final_win_odds_response_provider:
        JRAHistoricalFinalWinOddsResponseProvider,
    snapshot_persistence:
        _HistoricalInputSnapshotPersistence,
) -> JRAPersistedHistoricalSnapshotReference: ...
```

It accepts no decomposed race identity, dataset, internal race ID, `captured_at`,
`information_cutoff`, snapshot identity, digest, SQLite connection, or current clock.

Before any collaborator call, it must:

1. validate the exact canonical `seed_id`;
2. require the seed, v4, exact-v3, accessU, accessS, and accessO providers to be
   callable;
3. require `snapshot_persistence.save_snapshot` and
   `snapshot_persistence.load_snapshot_by_identity` to be callable.

Any failure is `JRARaceHistoricalSnapshotPersistenceValidationError`, with zero
provider or repository calls.

## Exact Seed and C4d Calls

Call the seed provider exactly once as `seed_provider(seed_id=seed_id)`. `None` is
persistence unavailable. The result must have exact type `JRARaceReplaySeed` and its
`seed_id` must equal the requested value; otherwise persistence validation fails. C4e
does not reconstruct or materialize a seed and performs no legacy identity lookup.

Call `build_jra_race_historical_replay(...)` exactly once with the exact loaded seed and
the five evidence providers unchanged. The result must have exact type
`JRARaceHistoricalReplayResult`, retain `replay_result.seed is loaded_seed`, and contain
an exact `HistoricalInputSnapshot`. Translate only c4d's formal public errors as defined
above; repository and provider errors propagate unchanged.

## Save and Transaction Ownership

Call exactly once:

```python
snapshot_persistence.save_snapshot(
    snapshot=replay_result.snapshot,
)
```

There is no success/reference before save returns. C4e owns no transaction and does not
attempt a cross-provider transaction:

```text
C4E_TRANSACTION_OWNER: SNAPSHOT_REPOSITORY_SAVE_ONLY
C4E_CROSS_PROVIDER_TRANSACTION: NO
```

The concrete SQLite repository retains its existing `BEGIN IMMEDIATE` transaction. A
process failure after a successful save but before return is restart-safe because retry
idempotently saves and exact-reloads the same snapshot.

## Exact Snapshot Load Extension

Add exactly this concrete repository method:

```python
def load_snapshot_by_identity(
    self,
    *,
    identity: HistoricalInputSnapshotIdentity,
) -> HistoricalInputSnapshot | None: ...
```

`type(identity) is HistoricalInputSnapshotIdentity` is required; invalid input raises
`RepositoryValidationError`. Its exact natural selector is the five stored columns:

```text
identity.dataset_id
identity.source_identity.organization
identity.source_identity.source_system
identity.source_identity.external_race_id
identity.captured_at
```

`source_url`, `information_cutoff`, `internal_race_id`, and `content_sha256` are not
selectors. The query uses equality on all five fields with multiplicity-aware
`fetchall()` or equivalent. It has no inequality, latest ordering, ambiguity-hiding
limit, other-source fallback, legacy fallback, or direct/indirect delegation to
`load_latest_snapshot(...)`.

Zero rows returns `None`; exactly one row is fully reconstructed; more than one raises
`RepositoryDataIntegrityError`. Reconstruction validates the stored natural identity,
exact race and entry mappings, every child, every provenance and evidence row,
cardinality/order, canonical stored scalars, and recomputed content digest. Any
corruption raises `RepositoryDataIntegrityError`. Existing `load_latest_snapshot(...)`
semantics remain unchanged.

If snapshot A exists at `captured_at=T1` and B exists for the same dataset/source/race at
`T2 > T1`, exact loading A always returns A, including after restart. It never substitutes
B even when the latest loader would select B for a cutoff.

## Exact Reload and Content Proof

After save, call exactly once:

```python
snapshot_persistence.load_snapshot_by_identity(
    identity=replay_snapshot.identity,
)
```

Do not call `load_latest_snapshot` directly or indirectly. `None` is persistence
unavailable; a non-exact `HistoricalInputSnapshot` is persistence validation.

After reconstruction require explicit equality for:

- `dataset_id`;
- source `organization`;
- source `source_system`;
- source `external_race_id`;
- `captured_at`;
- `content_sha256`;
- source `source_url`.

The explicit URL comparison is mandatory because source URL is immutable digest-bound
content but is intentionally excluded from dataclass identity comparison. Any mismatch
is persistence validation; repository-detected corruption propagates unchanged.

Return exactly:

```python
JRAPersistedHistoricalSnapshotReference(
    seed_id=loaded_seed.seed_id,
    snapshot_identity=reloaded_snapshot.identity,
    content_sha256=reloaded_snapshot.content_sha256,
)
```

## Existing Repository and Mapping Compatibility

`SQLiteHistoricalInputSnapshotRepository.save_snapshot(...)` already saves the c4d
snapshot, owns one `BEGIN IMMEDIATE` transaction, and performs idempotent success only
when natural identity and complete digest agree. Same identity with different content
raises `RepositoryConflictError`; no overwrite or repair occurs.

The d0 materializer already creates the exact race, horse, external-race, external-entry,
and source-identity mappings checked by this repository. C4e reuses those mappings and
does not rebuild or infer identity.

## Future-Leakage Guard

- no live/current fallback;
- no latest-snapshot substitution after an exact snapshot exists;
- no legacy mutable race, horse, entry, past-race, jockey, or odds lookup;
- no name mapping and no rebuilt entry identity;
- no information after `snapshot.information_cutoff`;
- no race result, payout, settlement, or final-odds substitution into prediction input;
- no timestamp rewriting or invented availability;
- no overwrite, partial save, repair, or cross-source fallback.

## Implementation Scope

Future c4e production files:

```text
scripts/simulation/jra_race_historical_snapshot_persistence.py
scripts/simulation/repositories/sqlite_historical_input_snapshot_repository.py
```

Future c4e test files:

```text
tests/test_jra_race_historical_snapshot_persistence.py
tests/test_sqlite_historical_input_snapshot_repository.py
```

Documentation files remain `docs/CURRENT_PHASE.md` and
`docs/LATEST_CODEX_REPORT.md`. There is no migration/schema, c4d, prediction,
simulation, c4f, package-root, HTTP, live capture, or settlement change.

## Required Future Tests

Repository tests must pin the exact method signature/type validation, exact five-column
lookup, no latest delegation, restart-stable A load, later B non-substitution,
`source_url` non-selector behavior, malformed stored URL/digest handling, corruption of
header/children/mappings/provenance/evidence/digest as integrity failure, zero-row
`None`, and unchanged latest-loader behavior.

Application tests must pin exact `__all__`, signature, frozen/slotted reference,
validation before collaborators, one exact seed load, wrong seed type/ID failure, one
c4d call with identical objects, c4d error translation, unchanged repository/provider
errors, one save with no early result, one exact reload with no latest call, missing
reload unavailable, digest and source-URL mismatch validation, equivalent existing
snapshot success, same-identity/different-content conflict propagation, retry
idempotence after prior save, and absence of HTTP/current/legacy/prediction/settlement
ownership.

Implementation verification will include dedicated repository/application tests,
related regressions, the full pytest suite, static public-surface/no-broad-catch/scope
checks, `git diff --check`, and final status.

## Readiness and Stop Condition

```text
IMPLEMENTATION_READY: YES_AFTER_INDEPENDENT_APPROVAL
BLOCKERS: NONE
```

Stop after this docs-only correction review commit is pushed. Do not implement c4e,
begin c4f, modify the formal branch, or run prediction/simulation until independent
review approves the corrected contract.
