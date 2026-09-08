# Current Phase

Status: `APPROVED_FOR_COMMIT`

## Identity and authority

- Phase: `POST_V0_8_DAILY_REPLAY_19`
- Name: `NAR Daily Target Live Acquisition and Archive Completion Design`
- Phase type: `DESIGN_ONLY`
- Base Commit: `1ff6a42d7c7370efedabe7c87f0c3eb3c5ecd96a`
- Branch: `feature/post-v0.8-daily-replay`
- Outcome: `DURABLE_ARCHIVE_REQUIRED`
- Production/tests/schema/migration implementation: `NOT_AUTHORIZED`
- Stage/commit/push: `NOT_AUTHORIZED`

AGENTS.md, the committed Phase 2 through Phase 6 NAR daily-target contracts, the
committed Phase 17 source qualification and the committed Phase 18 bootstrap domain and
resolver are authority. Phase 18 was committed with its exact ten-file amended scope and
normally pushed. Fetch confirmed local HEAD and
`origin/feature/post-v0.8-daily-replay` both equal the Base Commit above, with a clean
worktree and index before this PREPARE.

## Objective

Design the missing production preparation path from exact `target_date` through official
NAR acquisition to one audited complete daily target set:

```text
official supplier capture chain
  -> NARMonthlyConveneInfoBootstrapEvidence
  -> resolve_nar_monthly_convene_info_request_identity
  -> exact MonthlyConveneInfo response capture
  -> strict envelope normalization and raw RaceList request identities
  -> every exact RaceList response capture
  -> build_nar_historical_daily_replay_target_set
  -> DailyHistoricalReplayTargetSet
```

The phase also decides whether existing concrete persistence can retain every exact raw
capture required to reproduce and audit that result. It does not implement acquisition,
an archive, a migration, a Daily Orchestrator, evidence resolution, manifest execution,
replay, reporting or ROI aggregation.

## Read-only repository audit

### Daily-target capture archive

`nar_historical_daily_target_capture.py` defines immutable
`NARHistoricalDailyTargetRequestIdentity` and
`NARHistoricalDailyTargetResponseCapture` values plus the exact-ID-only Protocols:

```python
class NARHistoricalDailyTargetCaptureSource(Protocol):
    def load_capture(*, capture_id: str) -> NARHistoricalDailyTargetResponseCapture | None: ...

class NARHistoricalDailyTargetCaptureArchive(NARHistoricalDailyTargetCaptureSource, Protocol):
    def save_capture(*, capture: NARHistoricalDailyTargetResponseCapture) -> None: ...
```

No production class implements those Protocols. The only implementations found are test
doubles. There is no SQLite table, migration, repository, filesystem archive or other
durable owner for MonthlyConveneInfo/RaceList daily-target captures.

### Bootstrap supplier evidence archive

Phase 18 defines immutable homepage, Monthly-root and locator-script supplier captures
and their derived aggregate evidence identity. It deliberately defines no Source,
Archive, save, load, list or latest surface. No concrete durable repository exists for
these three capture kinds. Fixture files are offline parser/source-contract evidence and
must never serve as a production archive.

### Existing NAR official response archive is not compatible

`SQLiteNAROfficialResponseCaptureRepository` is a real append-only archive, but accepts
only exact `NAROfficialResponseCapture`. Its closed `NAROfficialPageKind` vocabulary is
`DEBA_TABLE`, `HORSE_MARK_INFO` and `RACE_MARK_TABLE`; its canonical URL grammar and
`nar-capture-v1` identity do not admit bootstrap homepage/root/script or daily-target
MonthlyConveneInfo/RaceList values. Its v001 schema enforces that closed vocabulary.

Recasting daily-target captures into that domain, widening its enum/schema for
convenience, or discarding the source-owned raw request identity would mutate a distinct
v0.8 settlement/prediction archive contract. It is forbidden. That repository and its
migration remain read-only reuse references, not a storage solution for this flow.

### Existing live and normalization reuse

- `NARHistoricalDailyTargetLiveCaptureService.capture_supplied_response` already owns
  one validated Monthly/RaceList request fetch, exact response construction, injected
  clock sampling and archive save.
- Its requests transport already uses GET, `Accept-Encoding: identity`, TLS verification,
  redirects disabled, retry count zero, bounded streaming and exact response validation.
- `resolve_nar_monthly_convene_info_request_identity` remains the sole final authority
  for the Phase 18 homepage -> root -> locator-script -> year/month chain.
- `normalize_nar_monthly_convene_info` already converts the exact Monthly capture into
  ordered venue locators whose RaceList request identities retain raw official hrefs.
- `build_nar_historical_daily_target_evidence_bundle` already requires exact envelope /
  RaceList / same-day-navigation set equality and retains all evidence.
- `build_nar_historical_daily_replay_target_set` already builds the audited shared target
  set and fails closed instead of returning a partial denominator.

None of those functions discovers a bootstrap locator from `target_date` alone or owns a
concrete durable archive.

## Formal decision

Outcome is `DURABLE_ARCHIVE_REQUIRED`.

Both daily-target capture classes and all three bootstrap supplier capture classes must
be durably stored as exact immutable evidence before a production date-only acquisition
flow can be considered complete. A separate NAR daily-target capture archive is required;
the main `database/keiba.db`, legacy tables and existing closed NAR official-response
archive are not candidates.

The archive design must preserve complete raw bytes as BLOBs plus exact byte length,
SHA-256, request/effective identity, page kind, schema version, honest requested/
observed/stored timestamps, HTTP status/content metadata and derived capture identity.
Save is append-only and idempotent only for byte-for-byte identical content. Conflicting
identity, missing/corrupt body, digest mismatch or automatic repair is a global integrity
failure. Loads are exact capture-ID loads only; no latest, nearby, URL reconstruction or
fallback query is permitted.

An isolated archive schema and migration sequence are required. Migration application
belongs to an explicit archive setup/composition boundary before acquisition. Neither
the live acquisition service, target normalizer, target-set builder, historical replay
runner nor main-database migration owner may apply or duplicate those migrations.

## Minimal future archive contract

The smallest compatible design is one separate SQLite archive database with one exact
content-addressed response-body table and distinct immutable metadata tables for:

1. Phase 18 bootstrap supplier captures; and
2. Phase 6 MonthlyConveneInfo/RaceList daily-target captures.

The metadata tables remain distinct because their capture IDs, page-kind vocabularies,
request identities and URL semantics differ. Sharing exact response bodies by SHA-256 is
permitted only when reconstruction still validates each owning domain independently.

A new bootstrap boundary may expose only:

```python
class NARMonthlyConveneInfoBootstrapCaptureSource(Protocol):
    def load_bootstrap_capture(*, capture_id: str) -> NARMonthlyConveneInfoBootstrapSupplierCapture | None: ...

class NARMonthlyConveneInfoBootstrapCaptureArchive(
    NARMonthlyConveneInfoBootstrapCaptureSource, Protocol
):
    def save_bootstrap_capture(*, capture: NARMonthlyConveneInfoBootstrapSupplierCapture) -> None: ...
```

The concrete repository can implement those methods alongside the existing
`NARHistoricalDailyTargetCaptureArchive.save_capture/load_capture` surface without
changing either capture domain. Aggregate bootstrap evidence remains a deterministic
projection of three exact primary captures; storing a second mutable copy of that
aggregate is unnecessary. Callers reconstruct it from three exact capture IDs and rerun
the Phase 18 integrity checks.

## Missing production components

The repository lacks four pieces needed before a Daily Orchestrator:

1. a concrete durable archive and isolated migration for both raw capture families;
2. an official supplier live-capture service for homepage/root/locator-script that
   creates Phase 18 capture values and archives each exact response;
3. a preparation application that deterministically composes bootstrap, existing
   Monthly/RaceList live capture and target-set construction; and
4. a composition/setup boundary that supplies archive database connection, already-
   applied schema, strict transports and explicit UTC clock.

No new prediction, settlement, evidence resolver, manifest or replay logic is needed.

## Proposed future APIs and files

These are candidates for separately reviewed future phases, not Phase 19 Allowed Files:

```text
scripts/simulation/nar_historical_daily_target_capture_archive.py
scripts/simulation/nar_historical_daily_target_capture_archive_migration.py
scripts/simulation/nar_historical_daily_target_capture_archive_migration_runner.py
scripts/simulation/repositories/sqlite_nar_historical_daily_target_capture_repository.py
scripts/simulation/nar_historical_daily_target_supplier_live_capture.py
scripts/simulation/nar_historical_daily_target_acquisition.py

tests/test_nar_historical_daily_target_capture_archive.py
tests/test_nar_historical_daily_target_capture_archive_migration.py
tests/test_sqlite_nar_historical_daily_target_capture_repository.py
tests/test_nar_historical_daily_target_supplier_live_capture.py
tests/test_nar_historical_daily_target_acquisition.py
```

Candidate application API:

```python
@dataclass(frozen=True, slots=True)
class NARHistoricalDailyTargetAcquisition:
    supplier_evidence: NARMonthlyConveneInfoBootstrapEvidence
    envelope_capture: NARHistoricalDailyTargetResponseCapture
    race_list_captures: tuple[NARHistoricalDailyTargetResponseCapture, ...]
    target_set: DailyHistoricalReplayTargetSet


class NARHistoricalDailyTargetAcquisitionService:
    def acquire(*, target_date: date) -> NARHistoricalDailyTargetAcquisition: ...
```

The exact API/file split must be frozen by later PREPARE/review; Phase 19 does not
authorize these names as production contracts.

## Acquisition sequence and invariants

1. Require exact `target_date`; do not sample current date/time for identity.
2. Starting only from the approved official homepage locator, capture homepage, then
   source-supplied Monthly-root href, then source-supplied pinned locator-script src.
   Each request uses official HTTPS GET, redirects false, retries zero, TLS verify,
   bounded complete body and explicit injected clock.
3. Archive every exact supplier capture before using it. Build Phase 18 supplier
   evidence and run the existing resolver; missing, duplicate, altered or contradictory
   relations fail closed. No target-date URL template is allowed.
4. Pass the resulting existing Monthly request identity to
   `NARHistoricalDailyTargetLiveCaptureService`; archive its exact response.
5. Run `normalize_nar_monthly_convene_info` and use only its raw official RaceList request
   identities. Do not reconstruct URLs from `target_date` or `baba_code`.
6. Fetch each unique venue request once in deterministic canonical `baba_code` order via
   the existing live-capture service and archive each exact response. A duplicate request
   identity is an integrity failure, not a tie to break.
7. Only after every expected capture exists, invoke
   `build_nar_historical_daily_replay_target_set` exactly once with the complete tuple.
8. Return the acquisition value only if the audited set builds successfully. Any missing,
   unsupported, malformed, contradictory, transport or archive state returns no target
   set. Already archived immutable raw captures may remain as honest incomplete-attempt
   evidence, but must never be presented as a complete denominator or silently reused by
   a latest/fallback policy.

Network acquisition is a preparation concern. Historical replay remains no-network and
consumes only frozen target/evidence/manifest identities.

## Failure and test contract for future phases

Future archive tests must prove exact BLOB round trips, worktree-independent bytes,
idempotent identical save, conflict rejection, corruption/missing-body rejection, exact-
ID-only loads, no repair/latest/list fallback, transaction rollback and migration drift
failure for both capture families.

Future supplier/acquisition tests must prove exact source-owned chain order, one GET per
identity, redirects/retries disabled, bounded response, injected clock, no current clock,
no URL reconstruction, raw href preservation, deterministic venue order, archive-before-
use, complete set construction and no target set on any missing/duplicate/malformed/
transport/archive/navigation/set-equality failure. Partial archived evidence must not be
converted to a partial or zero target set.

## Remaining blockers before Daily Orchestrator

- The archive schema, migration runner and exact repository contract are not yet reviewed
  or implemented.
- Production bootstrap supplier HTTP acquisition is absent.
- The complete acquisition application and its composition/setup owner are absent.
- No durable daily-result/denominator persistence exists; that remains a later separately
  gated phase and is not required to decide this raw-capture archive gap.

The recommended next phase is a separately reviewed durable archive implementation
design/implementation phase, followed by supplier/live acquisition completion. Daily
Orchestrator implementation must not start before both are complete.

## Allowed Files

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Forbidden Files and stop condition

Every other path is forbidden during Phase 19 PREPARE, including production, tests,
fixtures, `.gitattributes`, schemas, migrations, repositories, databases, archives, CLI,
release history and provider evidence. Stage, commit and push are forbidden.

PREPARE stops at `DRAFT_FOR_REVIEW` with outcome `DURABLE_ARCHIVE_REQUIRED`. A later
review must decide the archive phase split, exact schema/API names and whether the
proposed acquisition surface is sufficiently narrow before any implementation begins.
