# Current Phase

Status: `DRAFT_FOR_REVIEW`

## Identity and scope

- Phase: `4C-2d3b1i6d1d5f1c4h4`
- Name: `Official settlement acquisition/application composition and final completeness`
- Exact formal base: `0efea458551ddc8b45fc105bf921334d0c18665e`
- Formal branch: `feature/ver0.8-simulator`
- PREPARE review branch:
  `review/4c-2d3b1i6d1d5f1c4h4-settlement-acquisition-prepare`
- Git setting: `core.autocrlf=true`; no Git configuration or attributes change is
  authorized.

This PREPARE changes only:

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

No production code, Python test, repository protocol, SQLite implementation, schema,
migration, database, capture, or HTTP activity is authorized. Formal c4h0 through
c4h3 remain frozen. C4h4 joins their existing public boundaries; it does not reopen
provider grammar or settlement arithmetic.

## C4H4_PURPOSE

C4h4 connects exact archived official evidence to the four formal provider-specific
normalizers, provider-neutral result/payout repositories, cutoff-aware historical
reads, and the existing historical settlement composition. It owns application
coordination and the distinction between an acquisition attempt and a final-complete
settlement run. It owns no prediction, value, bet-generation, allocation, raw parser,
ticket evaluation, payout arithmetic, or summary aggregation behavior.

## C4H4_INITIAL_OPERATING_MODE

`HISTORICAL_REPLAY_ONLY`

The initial boundary consumes already archived exact capture IDs. It performs no live
discovery or acquisition. Current/live operation and capture discovery remain a later
operational concern and may not present a current observation as historical evidence.

## PREDICTION_INFORMATION_BOUNDARY

`HistoricalInputSnapshot.information_cutoff` remains the pre-race prediction boundary.
The snapshot and its exact persisted bet-plan identity are immutable inputs. Result
captures, payout captures, finish positions, payout values, repository contents, and
settlement readiness may not mutate or select prediction inputs, EV, strategy,
allocation, or planned bets.

Required payout types are derived from the exact persisted bet plan before any result
or payout capture is loaded. Official-data availability must never decide which bet
types are required.

### DATASET_BINDING_POLICY

`SNAPSHOT_DATASET_ID_MUST_EXACTLY_EQUAL_RUN_CONTEXT_DATASET_ID`

Before plan-source or official-evidence I/O, c4h4a requires:

```text
snapshot.identity.dataset_id == run_context.dataset_id
```

The existing persisted bet-plan natural identity does not include `dataset_id`, so
same-race, same-cutoff, and same-strategy values cannot substitute for this explicit
binding. A mismatch fails before snapshot-to-race-input adaptation, before
`SimulationBetPlanSnapshotSource.load_snapshot`, before any capture archive load,
before any provider normalizer call, and before any result or payout repository write.
It produces zero plan-source loads, archive loads, result saves, and payout saves.

Dataset identity is never inferred from race ID, provider, capture URL, place,
strategy, or database contents. After the binding passes, c4h4a adapts the exact
`HistoricalInputSnapshot` through the existing historical snapshot-to-
`SimulationRaceInput` boundary and uses `PersistedSimulationBetSource` with the exact
run context, plan source, and strategy identity. It loads the persisted plan exactly
once and does not duplicate `SimulationBetPlanIdentity` construction, rerun prediction,
or regenerate bets.

## SETTLEMENT_INFORMATION_CUTOFF_POLICY

`settlement_information_cutoff` is a separate, exact timezone-aware post-race evidence
boundary. It is not `HistoricalInputSnapshot.information_cutoff`, is never supplied by
the current clock, and need not equal prediction time.

Historical evidence eligibility is exactly:

```text
capture.observed_at <= settlement_information_cutoff
persisted_result.observed_at <= settlement_information_cutoff
payout_publication.observed_at <= settlement_information_cutoff
```

Equality is eligible; one microsecond after the cutoff is not. `requested_at`,
`stored_at`, and `finalized_at` are not selection timestamps. Domain finalization still
must be present for complete facts, and the existing domain guarantees it is not later
than `observed_at`. No value is backdated.

## Evidence selection and provider dispatch

### PROVIDER_DISPATCH_POLICY

Provider ownership comes only from the snapshot's exact source identity:

```text
organization=JRA, source_system=jra_official -> c4h0 result + c4h1 payout
organization=NAR, source_system=nar_official -> c4h2 result + c4h3 payout
```

Any other or contradictory source identity fails before capture or repository I/O.
Dispatch never uses horse names, place, URL substrings, numeric coincidence, or
database provenance guesses. C4h4 calls the formal provider functions and duplicates
no HTML parser.

### RESULT_CAPTURE_SELECTION_POLICY

The application supplies one exact `result_capture_id` per race. C4h4 performs no
latest, nearest, URL, or current-page selection. Before any repository write it loads
every distinct supplied capture ID exactly once from the selected provider archive,
validates exact returned ID/type/page kind, and rejects an observation after the
settlement cutoff.

### PAYOUT_CAPTURE_SELECTION_POLICY

The application supplies an exact capture-ID mapping whose keys exactly equal the
required bet types derived from the frozen persisted plan. Each type has one explicit
capture ID. Result and payout IDs, and payout IDs across types, may be equal or
different; C4h4 does not impose false JRA/NAR symmetry. Reused IDs are loaded once in
the preflight. Missing, extra, unsupported, or after-cutoff mappings fail before any
write.

The formal archives do not expose one common bounded capture-selection contract:
their shared boundary is exact-ID load, and NAR supplies no generic latest-at-cutoff
lookup. Therefore automatic archive selection is outside initial c4h4. The implementation
uses a private read-only exact-ID cache/proxy so the provider normalizers consume the
already preflighted immutable captures without a second underlying archive read.

## Required facts and bounded repository reads

### REQUIRED_BET_TYPES_POLICY

`ONLY_SETTLEMENT_REQUIRED_TYPES_REQUIRED`

Required types are the unique `SimulationBet.bet_type` values from the exact persisted
plan, in first-occurrence order. They are established before official evidence I/O.
All-formal-type acquisition is unnecessary and could turn an unpurchased unsupported
type into a false blocker. A malformed or unsupported persisted plan fails through the
existing plan/domain boundary; it is never skipped.

### RESULT_COMPLETENESS_POLICY

For a race with purchased bets, settlement-ready result evidence is exactly one
`PersistedRaceResult` for the internal race with `RaceResultStatus.COMPLETE`, non-null
`finalized_at`, and `observed_at` at or before the settlement cutoff. The current
repository is insert-only per race; equal writes are idempotent and any differing
result, including a different correction/source, conflicts. C4h4 adds no result
versioning.

`RESULT_MULTIPLE_VERSION_POLICY`: `NOT_SUPPORTED_BY_CURRENT_REPOSITORY`

`RESULT_EQUAL_REWRITE` remains repository-owned idempotence.
`RESULT_DIFFERING_REWRITE_OR_CORRECTION` remains a repository conflict that propagates.
If the single persisted result was observed after a replay cutoff, the bounded source
treats it as unavailable. C4h4 does not look for an older result version because the
current model stores none and exposes no latest-result/correction selection contract.

An exact persisted empty plan is final `NO_BET` and requires no settlement fact read in
the final-completeness path, preserving the existing c4g2a/c4g2b behavior. The
acquisition subphase may still persist the explicitly supplied final result, but it
requires no payout capture mapping for that empty plan.

### PAYOUT_COMPLETENESS_POLICY

For every required purchased bet type, the latest eligible publication selected by the
existing repository/source rule must exist and have `is_complete=True` and non-null
`finalized_at`. Missing or incomplete latest eligible evidence is not a loss, empty
payout, or fallback to an older complete publication. No unrequired payout type is
needed for readiness.

### MULTIPLE_PUBLICATION_SELECTION_POLICY

This policy applies only to versioned, append-only `PayoutPublication` values. It does
not apply to `PersistedRaceResult`.

The existing formal rule remains:

```text
race_id + bet_type
observed_at <= settlement cutoff
ORDER BY observed_at DESC, publication_id DESC
require_complete=False
```

The latest eligible publication is authoritative for the as-of replay. If it is
incomplete, settlement is not ready; no older-complete fallback occurs. A correction
after the cutoff is invisible. A correction at or before the cutoff is selected by the
same ordering rule. Repository-returned wrong-race, wrong-type, or post-cutoff values
fail closed.

## Acquisition, partial state, and repeated runs

### ACQUISITION_WRITE_ORDER_POLICY

The exact pre-I/O order is:

```text
public argument validation
exact snapshot/run-context dataset binding
existing snapshot-to-race-input adaptation and identity validation
one existing PersistedSimulationBetSource plan load and validation
required bet-type freeze
provider dispatch
capture-ID mapping coverage
distinct exact-capture preload
settlement-cutoff validation for every capture
provider result/payout persistence calls
```

Only after the complete preflight passes does c4h4a invoke the formal result normalizer,
then one payout normalizer per required type in frozen first-occurrence order. Each
provider function retains its own complete validation and single-write contract.

### PARTIAL_ACQUISITION_POLICY

`DURABLE_AUDITABLE_PARTIAL_STATE_ALLOWED_BUT_NEVER_SETTLEMENT_READY`

The repositories own separate transactions and explicitly reject being wrapped in an
active caller transaction. No application-level transaction is added. A later provider
validation or repository failure may therefore leave an earlier exact result or payout
publication durably persisted. This state is immutable/auditable and safe because
final readiness requires the complete bounded fact set. It never becomes zero payout,
a losing ticket, or a silently omitted race.

### IDEMPOTENCE_POLICY

No hidden retry occurs. Repeating the same snapshot, plan identity, cutoff, exact
capture set, and repository state follows the same deterministic order. Equal result
and payout writes retain repository-owned idempotence; differing immutable result or
publication identities/content retain repository-owned conflict behavior. Archive,
provider-normalizer, and repository exceptions propagate unchanged.

### REPOSITORY_EXCEPTION_POLICY

Collaborator exceptions propagate with exact identity and without retry,
compensation, fallback, or conversion to readiness. C4h4 errors cover only its own
argument, provider-dispatch, capture-set/cutoff, and final-readiness boundaries.

## Settlement readiness and handoff

### SETTLEMENT_READINESS_POLICY

`ACQUISITION_ATTEMPT_COMPLETED` and `SETTLEMENT_READY` are distinct.

For every race, an exact empty persisted plan is ready as `NO_BET`. Every nonempty plan
is ready only when the bounded source supplies the complete result and a complete
publication for every required type. The final batch is complete only when:

```text
settled_race_count + no_bet_race_count == race_count
unsettled_race_count == 0
void_race_count == 0
error_race_count == 0
unsupported_race_count == 0
```

The initial provider envelope is normal-final-winning only, so void/unsupported states
are not final-complete c4h4 outcomes. A not-ready batch raises the dedicated final
readiness error and returns no partial `SimulationSummary` as final ROI.

### NO_SKIP_POLICY

Missing, unsupported, partial, conflicting, or after-cutoff evidence never removes a
race from the canonical batch and never turns into loss, zero payout, or `NO_BET`.
The existing as-of composition may internally classify it as `UNSETTLED` or
`UNSUPPORTED`; the final-completeness wrapper rejects that summary rather than exposing
it as final ROI.

### SETTLEMENT_ENGINE_HANDOFF_POLICY

C4h4a persists facts and invokes no settlement engine. C4h4b calls the existing
`execute_historical_settlement_simulation(...)` exactly once and does not duplicate
bet matching, stake multiplication, payout/profit arithmetic, aggregation, or drawdown.
It returns that exact `SimulationSummary` only after the final-completeness predicate
passes; otherwise it raises and returns no summary.

## Public API proposals and phase split

### C4H4_SUBPHASE_DECISION

`TWO_SUBPHASES`

One phase would combine exact capture preflight, provider dispatch, multiple immutable
writes, bounded reads, readiness, and settlement execution. The smallest reviewable
split is:

1. `4C-2d3b1i6d1d5f1c4h4a`: exact-ID official settlement acquisition/persistence
   composition for one historical race.
2. `4C-2d3b1i6d1d5f1c4h4b`: final-complete historical settlement application wrapper
   over the unchanged c4g2b composition.

No c4h4c is currently required.

### PUBLIC_API_PROPOSAL — c4h4a

Module:

```text
scripts/simulation/official_settlement_acquisition.py
```

Module-local API with no package-root export:

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

The module-local `__all__` exposes the function plus
`OfficialSettlementAcquisitionError`,
`OfficialSettlementAcquisitionValidationError`,
`OfficialSettlementAcquisitionUnavailableError`, and
`OfficialSettlementAcquisitionUnsupportedError`. Provider persistence errors and all
archive/repository exceptions propagate unchanged.

The function validates exact public types and the snapshot/run-context dataset binding
before I/O, then adapts the immutable snapshot through the existing race-input boundary
and reuses `PersistedSimulationBetSource` to load the exact plan once. It derives
required types, preloads all distinct exact captures before writes, dispatches to
c4h0/c4h1 or c4h2/c4h3, and returns existing `PersistedRaceSettlementData` containing
the exact frozen bets and successful formal result/publications. It introduces no
near-copy of `SimulationBetPlanIdentity` and no new aggregate DTO.

### PUBLIC_API_PROPOSAL — c4h4b

Module:

```text
scripts/simulation/final_historical_settlement_simulation.py
```

Module-local API with no package-root export:

```python
def execute_final_historical_settlement_simulation(
    *,
    snapshots: tuple[HistoricalInputSnapshot, ...],
    run_context: SimulationRunContext,
    strategy_identity: StrategyIdentity,
    settlement_cutoffs_by_race_id: Mapping[int, datetime],
    bet_plan_snapshot_source: SimulationBetPlanSnapshotSource,
    race_result_repository: RaceResultRepository,
    payout_repository: PayoutRepository,
) -> SimulationSummary:
    ...
```

It reuses c4g2b's exact public arguments and return type, invokes c4g2b once, validates
the final counts above, and either returns the exact summary or raises module-local
`FinalHistoricalSettlementNotReadyError`. It adds no second settlement source, DTO,
metric, or repository query policy.

### RETURN_VALUE_POLICY

C4h4a reuses `PersistedRaceSettlementData`; c4h4b returns the exact existing
`SimulationSummary`. No acquisition result is represented as final readiness, and no
partial/as-of summary is represented as guaranteed final ROI.

## Persistence and operational decisions

- `REPOSITORY_PROTOCOL_CHANGE_REQUIRED`: `NO`
- `SQLITE_REPOSITORY_CHANGE_REQUIRED`: `NO`
- `SCHEMA_CHANGE_REQUIRED`: `NO`
- `MIGRATION_REQUIRED`: `NO`
- `LIVE_HTTP_POLICY`: `FORBIDDEN_IN_INITIAL_C4H4`
- `HISTORICAL_REPLAY_POLICY`: exact archived captures and persisted publications are
  eligible only by actual `observed_at` at or before the explicit cutoff; a current
  capture is not usable for an earlier historical cutoff.

## Required future tests

C4h4a must pin:

- exact module-local public surface and keyword-only signature;
- exact matching snapshot/run-context dataset IDs proceed through the identity
  boundary;
- mismatched dataset IDs fail before plan-source load, archive load, provider call,
  result save, and payout save, including otherwise equal race ID, information cutoff,
  and strategy values;
- required payout types cannot come from a mismatched-dataset plan;
- the exact persisted plan is loaded once through existing
  `PersistedSimulationBetSource` semantics, with no custom near-copy of
  `SimulationBetPlanIdentity` construction;
- exact JRA and NAR dispatch from source identity;
- one result plus every unique frozen-plan payout type in deterministic order;
- required types fixed before official reads and unaffected by payout availability;
- exact capture-ID mapping coverage and one underlying load per distinct ID;
- shared and distinct result/payout capture IDs;
- observation exactly at cutoff accepted and one microsecond after rejected before any
  repository write;
- no current-clock fallback, live HTTP, latest capture lookup, or raw HTML parser;
- no snapshot, persisted-plan, prediction, value, allocation, or strategy mutation;
- result-first and payout first-occurrence write order;
- partial durable writes never reported as a completed acquisition return;
- equal retry remains repository-idempotent and conflicts propagate unchanged;
- an equal result rewrite remains idempotent, while any differing result/correction
  remains a propagated repository conflict;
- neither c4h4a nor c4h4b performs latest-result or result-correction selection;
- missing/invalid/unsupported capture and provider errors fail closed;
- no unsupported bet-type, missing mapping, or extra mapping skip;
- no package-root export, schema, SQLite, settlement arithmetic, or result/payout model
  duplication.

C4h4b must pin:

- exact delegation to c4g2b and exact summary return identity;
- all-settled plus no-bet batches accepted;
- missing result, missing required payout, incomplete latest publication, unsupported
  facts, conflict-derived failure, and after-cutoff evidence rejected with no summary;
- payout correction after cutoff invisible and payout correction at/before cutoff
  chosen by the formal payout-publication ordering rule;
- no silent race or unsupported type skip;
- no prediction snapshot or planned-bet mutation;
- no settlement arithmetic, raw parser, repository write, HTTP, or current-clock logic.

## Implementation readiness and next step

`IMPLEMENTATION_BLOCKERS`: `NONE_AFTER_INDEPENDENT_RE_REVIEW`

`RECOMMENDED_NEXT_PHASE`:
`4C-2d3b1i6d1d5f1c4h4a_EXACT_CAPTURE_SETTLEMENT_ACQUISITION_COMPOSITION`

`NEXT_PHASE_ALLOWED_FILES`:

```text
scripts/simulation/official_settlement_acquisition.py
tests/test_official_settlement_acquisition.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

C4h4b remains unstarted until c4h4a is formally complete. Stop for independent
architecture review.
