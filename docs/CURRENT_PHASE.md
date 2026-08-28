# Current Phase

Status: `READY_FOR_REVIEW`

## Identity and scope

- Phase: `4C-2d3b1i6d1d5f1c4h4a`
- Name: `Exact-capture official settlement acquisition and persistence composition`
- Exact formal base: `0efea458551ddc8b45fc105bf921334d0c18665e`
- Formal branch: `feature/ver0.8-simulator`
- Review branch:
  `review/4c-2d3b1i6d1d5f1c4h4a-exact-capture-settlement-acquisition`
- Git setting: `core.autocrlf=true`; no Git configuration or attributes change is
  authorized.

Allowed and changed files are exactly:

```text
scripts/simulation/official_settlement_acquisition.py
tests/test_official_settlement_acquisition.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

C4h0 through c4h3 remain frozen. This phase changes no provider normalizer, capture
infrastructure, repository protocol, SQLite implementation, schema, migration,
database, log, package export, settlement source/executor/composition, or prediction
boundary. C4h4b remains unstarted.

## Purpose and public API

C4h4a composes exact archived official evidence with the immutable persisted bet plan
for one historical race. It performs no HTTP, capture creation/discovery, latest
lookup, retry, current-clock lookup, prediction, bet generation, repository read, or
settlement arithmetic.

```python
def acquire_and_persist_official_settlement_facts(
    *,
    snapshot: HistoricalInputSnapshot,
    run_context: SimulationRunContext,
    strategy_identity: StrategyIdentity,
    settlement_information_cutoff: datetime,
    bet_plan_snapshot_source: SimulationBetPlanSnapshotSource,
    result_capture_id: str,
    payout_capture_ids_by_bet_type: Mapping[str, str],
    capture_archive: JRAOfficialResponseCaptureArchive | NAROfficialResponseCaptureArchive,
    race_result_repository: RaceResultRepository,
    payout_repository: PayoutRepository,
) -> PersistedRaceSettlementData:
    ...
```

The module-local `__all__` contains only this function plus
`OfficialSettlementAcquisitionError`, Validation, Unavailable, and Unsupported
subclasses. There is no package-root export. Provider-normalizer, archive, plan-source,
and repository exceptions propagate unchanged.

## Frozen acquisition contract

- Exact public values are validated before I/O. Snapshot, run context, and strategy
  identity are exact formal types; cutoff is aware; collaborators expose their required
  callables; capture IDs are exact nonempty strings; the payout mapping is not mutated.
- `snapshot.identity.dataset_id` must equal `run_context.dataset_id` before snapshot
  adaptation, plan loading, archive loading, provider invocation, or result/payout
  write. Dataset identity is never inferred from race, URL, place, strategy, or data.
- The existing snapshot adapter and `PersistedSimulationBetSource` load the immutable
  persisted plan exactly once. C4h4a does not reconstruct `SimulationBetPlanIdentity`,
  predict, or regenerate bets.
- Required payout types are unique plan `SimulationBet.bet_type` values in
  first-occurrence order. Mapping keys must match that set exactly. An empty plan needs
  an empty mapping, still persists the supplied result, and invokes no payout normalizer.
- Dispatch relies only on exact source identity: `JRA/jra_official` selects c4h0/c4h1;
  `NAR/nar_official` selects c4h2/c4h3. Other values fail before archive or writes.
- The result capture ID followed by payout IDs in plan order is preloaded with equal
  IDs deduplicated by first use. Every capture must have exact ID, provider type,
  compatible page kind, aware `observed_at`, and
  `observed_at <= settlement_information_cutoff`. Equality is allowed; a later
  microsecond fails. Requested/stored/finalized/current time are never substituted.
- Provider normalizers receive a private read-only exact-ID cache, avoiding a second
  underlying archive read and forbidding latest/fallback/URL selection.
- After complete preflight, the result normalizer runs once, then payout normalizers
  run in plan order. C4h4a writes no direct domain value; provider boundaries retain
  their complete validation and single-write contracts.
- No transaction, rollback, compensation, or retry is added. Earlier immutable writes
  may remain durable if a later provider call fails; no success value is returned and
  later payout types are not attempted. Repository idempotence/conflict behavior stays
  repository-owned.
- A successful value is existing `PersistedRaceSettlementData` with the exact persisted
  bets and provider-returned facts. C4h4a does not decide final completeness or execute
  settlement; those remain C4h4b work.

## Verification and stop condition

Dedicated tests cover public surface, pre-I/O validation/dataset binding, persisted plan
reuse, required-type map/order, JRA/NAR dispatch, exact-ID preload/cache/deduplication,
cutoff preflight, empty plan, provider ordering, unavailable/incompatible evidence,
partial failure, collaborator propagation, and static ownership restrictions.

Before review: run dedicated and directly relevant adapter, plan-source, capture,
provider-normalizer, repository/domain, c4g2a, and c4g2b tests; then full suite,
`git diff --check`, static scope check, and clean status. Stop for independent review;
do not integrate or begin C4h4b.
