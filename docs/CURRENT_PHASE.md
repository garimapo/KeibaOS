# Current Phase

Status: `READY_FOR_REVIEW`

## Identity and authority

- Phase: `POST_V0_8_DAILY_REPLAY_25`
- Name: `NAR Daily Replay Orchestrator Implementation`
- Phase type: `IMPLEMENTATION`
- Base Commit: `9d9573d7ada6bf68a6f3e88da3cd66ae14189623`
- Branch: `feature/post-v0.8-daily-replay`
- Preparation outcome: `IMPLEMENTABLE`
- PREPARE authorization: documentation only

AGENTS.md, committed Phase 1, the approved/committed Phase 14, 16, 23 and 24 contracts
are authority. Phase 25 must implement the already-approved Phase 24 architecture only;
it may not redesign target discovery, evidence selection, manifest publication or the
existing replay engine.

## PREPARE Allowed Files

Only these files may change during PREPARE:

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

No production/test/fixture/database/archive file was changed during PREPARE. No test,
stage, commit or push is authorized before a correction is reviewed and approved.

## Proposed EXECUTE Allowed Files after correction

If the blocking conflict below is corrected and Phase 25 receives a new explicit
approval, execution scope is exactly:

```text
scripts/simulation/nar_daily_replay_orchestrator.py
tests/test_nar_daily_replay_orchestrator.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

All other paths remain forbidden, including Phase 14/16/23 production and tests, the
existing replay runner, migrations, schemas, database/**, logs/**, provider archives,
fixtures, CLI and AGENTS.md. `database/keiba.db` and logs/ are never staged or committed.
No scope expansion is authorized by this PREPARE.

## Execution result

The approved implementation is complete within the exact four-file scope. The new
orchestrator retains the frozen acquisition target set, verifies both caller SQLite
connection/path bindings with the sole approved `PRAGMA database_list`, preserves the
whole-day gate, reuses Phase 14 and Phase 16 exactly, passes the exact projection document
to the unchanged runner once, and verifies the published manifest identity and SHA-256
before and after execution. Partial and no-executable days return only deterministic
diagnostic results.

The immutable result and content-derived audit SHA follow the frozen v1 canonical payload.
No acquisition/network/current-clock behavior, provider parsing, migration invocation,
application SQL beyond the approved PRAGMA, new persistence, subset replay or fallback was
added. Dedicated tests passed 20 cases with `ResourceWarning` treated as errors, the
required related regressions passed 110 cases, and the full unittest suite passed 3,091
cases. Existing unrelated full-suite unclosed-SQLite warnings remain; the dedicated suite
emitted none. Static boundary and read-only prerequisite-file checks passed.

## Frozen public direction

The later implementation must expose only the Phase 24 API:

```python
class NARDailyReplayExecutionState(StrEnum):
    FULL_DAY_REPLAY_COMPLETED = "FULL_DAY_REPLAY_COMPLETED"
    NOT_RUN_PARTIAL_RESOLUTION = "NOT_RUN_PARTIAL_RESOLUTION"
    NOT_RUN_NO_EXECUTABLE_TARGETS = "NOT_RUN_NO_EXECUTABLE_TARGETS"


@dataclass(frozen=True, slots=True)
class NARDailyReplayOrchestrationResult:
    acquisition_result: NARDailyTargetLiveAcquisitionResult
    resolution: DailyHistoricalReplayEvidenceResolution
    execution_state: NARDailyReplayExecutionState
    manifest_projection: DailyHistoricalReplayManifestProjection | None
    manifest_sha256: str | None
    summary: SimulationSummary | None
    orchestration_audit_sha256: str = field(init=False)

    @property
    def canonical_target_count(self) -> int: ...

    @property
    def executable_count(self) -> int: ...


def run_nar_daily_replay(
    *,
    acquisition_result: NARDailyTargetLiveAcquisitionResult,
    dataset_id: str,
    settlement_information_cutoff: datetime,
    snapshot_connection: sqlite3.Connection,
    capture_connection: sqlite3.Connection,
    database_path: Path,
    nar_settlement_capture_archive_path: Path,
    run_context: SimulationRunContext,
    strategy_identity: StrategyIdentity,
    race_budget: BetStakeBudget,
    manifest_source_path: Path,
) -> NARDailyReplayOrchestrationResult: ...
```

Inputs are explicit. The frozen Phase 23 acquisition result and its exact target set are
the replay authority. No fresh acquisition, supplier/daily-target transport, HTTP,
network fallback, cache lookup, target reconstruction, default cutoff, default strategy,
default budget or current-clock input is permitted.

## Frozen execution sequence

For exact caller inputs, the implementation must compose only existing boundaries:

```text
frozen NARDailyTargetLiveAcquisitionResult
  -> resolve_sqlite_nar_daily_evidence(
       exact target_set, dataset_id, settlement_information_cutoff,
       snapshot_connection, capture_connection)
  -> whole-day state gate
  -> write_daily_historical_replay_manifest(
       exact resolution, database/archive paths, run context, strategy, budget, path)
  -> exact Phase 16 projection.document
  -> SHA-256 of exact manifest bytes
  -> run_sqlite_historical_replay(document=projection.document) once
  -> require unchanged post-run manifest SHA-256
  -> immutable orchestration result
```

`ALL_TARGETS_RESOLVED` is the only state allowed to reach manifest and runner. The exact
Phase 16 reloaded `HistoricalReplayRequestDocument` is passed directly to the runner;
there is no CLI subprocess, second loader, rebuilt request, rewritten budget or capture
catalog.

`PARTIALLY_RESOLVED` and `NO_EXECUTABLE_TARGETS` produce only their approved immutable
diagnostic result. They have `manifest_projection=None`, `manifest_sha256=None` and
`summary=None`, generate no manifest, call no runner and never claim partial metrics,
formal daily success or a successful zero-race day. Phase 16's lower-level executable
subset capability must not weaken this whole-day gate.

The manifest path is an exact caller-supplied absolute path. Phase 16 retains exclusive
creation, no overwrite, no alternative filename, no random/clock suffix and reload
validation. After successful publication it remains available as an audit/rerun artifact;
the orchestrator does not delete it, including after a runner failure. Mutation before or
after the runner fails closed without a retry or alternate manifest.

## Existing runner boundary

The Phase 25 orchestrator itself must not execute direct SQLite application SQL, invoke
migrations, implement prediction/betting/allocation/settlement/payout logic, persist a
new daily orchestration aggregate, or alter the replay runner. Its sole direct SQLite
metadata exception is the exact fixed literal `PRAGMA database_list` for the private
connection/path binding check below. It also must not parse source HTML/JS, generate
provider URLs, use network/current-clock APIs, or call Phase 23 `.acquire()`.

The unchanged existing `run_sqlite_historical_replay` remains the sole runner boundary
and is explicitly allowed to retain its already-approved internal behavior: main-database
migration, historical bet-plan persistence, official settlement/result/payout persistence
and final `SimulationSummary` generation. Deferred persistence means only that new
`NARDailyReplayOrchestrationResult`/daily aggregate persistence is outside Phase 25.

`StrategyIdentity`, uniform `BetStakeBudget`, `SimulationRunContext`, database/archive
paths and the explicit settlement cutoff pass unchanged to the existing components.
Acquisition timestamps, stored timestamps, manifest metadata and runner time never become
prediction or settlement causality.

## Result and deterministic audit identity

The successful result retains the frozen acquisition result, complete Phase 14 resolution,
execution state, Phase 16 projection, manifest SHA-256 and exact `SimulationSummary`.
It requires `ALL_TARGETS_RESOLVED`, a non-None exact document/summary, full canonical
target coverage and `summary.race_count == canonical_target_count`. It adds no
`target_race_count` field and computes no metric itself.

The deterministic `orchestration_audit_sha256` remains the Phase 24 content-derived
identity. It binds the frozen acquisition identities/target-set digest, complete ordered
resolution, state, exact explicit orchestration inputs and manifest digest/null. It uses
the Phase 24 frozen UTF-8/NFC canonical JSON rules, UTC microsecond datetimes, sorted
object keys and authoritative tuple order. It contains no UUID, random value, current
time, mtime, object ID, memory address, repr or unordered iteration. Diagnostic results
also receive this deterministic audit identity, but never an empty fake summary.

## Approved SQLite connection/path binding exception

Phase 24's anti-cross-store guarantee remains mandatory. Before calling Phase 14, a
private `_require_connection_path_binding(connection, expected_path, name)` helper uses
the only direct SQLite query authorized in this module, exactly the fixed literal:

```text
PRAGMA database_list
```

The helper accepts no SQL from a caller and constructs no SQL. It exists only to prove
that the caller-owned connection resolves to the same existing filesystem object as the
exact caller-supplied path later named in the manifest/replay request.

For both `snapshot_connection -> database_path` and
`capture_connection -> nar_settlement_capture_archive_path`, require before Phase 14:

- exact approved SQLite connections, distinct and transaction-free;
- an absolute, nonempty, NUL-free expected Path which exists as a filesystem file;
- a successful `PRAGMA database_list` result with exactly one usable `main` binding;
- no attached database, empty filename, `:memory:`/in-memory state, unexpected row
  shape, ambiguous/non-filesystem result or path mismatch; and
- filesystem-object equality using `Path.samefile(...)` or an equivalent identity check,
  rather than textual spelling equality.

Aliases to the same existing file may therefore bind successfully. The exact original
caller Path text nevertheless remains authoritative for Phase 16 serialization; it is
never replaced, resolved or rewritten from SQLite's reported text.

The binding query must neither begin nor leave a transaction. The helper verifies
`connection.in_transaction` before and after it, issues no commit/rollback, does not
close/reopen/repair a connection and fails closed before Phase 14, Phase 16 or the runner
on any uncertainty. No SELECT against application tables, INSERT, UPDATE, DELETE, DDL,
VACUUM, ATTACH, DETACH, transaction control, schema inspection, arbitrary/dynamic PRAGMA,
migration or application data read/write is permitted in the orchestrator.

No utility module, repository, schema or migration is added for this one private
infrastructure invariant.

## Required tests after correction

The implementation must carry the Phase 24 frozen behavior groups, including:

- exact frozen acquisition result; no Phase 23 acquisition/network/cache;
- exact target set, dataset, settlement cutoff and caller connections into Phase 14;
- exact private binding: correct snapshot/archive pairs pass; wrong paths, unexpected
  pairings, attachments, in-memory/empty/missing/non-file paths and active transactions
  fail closed before Phase 14/16/runner; supported same-file aliases pass; no transaction
  remains after the fixed PRAGMA; and PRAGMA errors propagate;
- only all-resolved execution; partial/zero diagnostic-only with no manifest/runner/summary;
- exact Phase 16 reuse and propagation of paths, run context, strategy and uniform budget;
- exact `projection.document` passed to unchanged runner once; no subset/retry/fallback;
- SHA-256 before/after runner, mutation fail-closed, frozen manifest retained on runner error;
- exact full-day `SimulationSummary`, no new aggregate persistence and no metric logic;
- deterministic audit SHA, including changes to semantic acquisition/target inputs;
- no network, current clock, direct migration, source parsing, provider URL construction,
  prediction, allocation, settlement, payout parsing or manifest-schema duplication;
- static inspection proves the only direct `.execute(...)` SQL is exactly
  `PRAGMA database_list`, with no executemany/executescript, SQL construction or other
  SQLite application query;
- Phase 14, Phase 16/schema-v1 request, SQLite replay runner and Phase 23 regressions;
- full unittest suite and static-boundary inspection.

Dedicated tests must use temporary caller-supplied SQLite files/paths only, never
database/keiba.db, logs, network or provider archives. Dedicated warnings are errors;
existing unrelated suite warnings must be reported separately.

## Stop condition

Stop at `DRAFT_FOR_REVIEW` with outcome `IMPLEMENTABLE`. Do not implement, create tests,
run implementation tests, stage, commit, push or advance automatically. A separate
`APPROVE_PHASE` and `EXECUTE_APPROVED_PHASE` remain required before the exact four-file
implementation scope becomes writable.
