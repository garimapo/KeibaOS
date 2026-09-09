# Current Phase

Status: `APPROVED_FOR_COMMIT`

## Identity, authority and outcome

- Phase: `POST_V0_8_DAILY_REPLAY_24`
- Name: `NAR Daily Replay Orchestrator Design`
- Phase type: `DESIGN_ONLY`
- Base Commit: `7133771344b176fcef6ec0fb99fd91f822d6c701`
- Branch: `feature/post-v0.8-daily-replay`
- Preparation outcome: `IMPLEMENTABLE`
- Production/tests implementation during PREPARE: `NOT_AUTHORIZED`
- Stage/commit/push during PREPARE: `NOT_AUTHORIZED`

AGENTS.md, the committed Phase 1 whole-day orchestration contract and the committed
Phase 13-16 and Phase 23 contracts are authority. This phase only designs the final
sequencing boundary. It does not amend target discovery, evidence selection, manifest
schema/publication or Ver0.8 replay behavior.

## Exact Allowed Files for this DESIGN_ONLY phase

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

The following are future implementation candidates, not Allowed Files in Phase 24:

```text
scripts/simulation/nar_daily_replay_orchestrator.py
tests/test_nar_daily_replay_orchestrator.py
```

Every other path is forbidden, including existing production/tests, fixtures,
schema/migrations, database/**, logs/**, archives, CLI, AGENTS.md and release history.
No network acquisition, replay execution, test execution, staging, commit or push is
authorized by this PREPARE.

## Existing API audit

The existing boundaries are sufficient without modifying them:

- `NARDailyTargetLiveAcquisitionResult` is an immutable audit join containing the exact
  supplier, Monthly and ordered RaceList capture IDs, supplier evidence identity and
  audited `DailyHistoricalReplayTargetSet`.
- `resolve_sqlite_nar_daily_evidence(...)` accepts the exact target set, dataset ID,
  explicit settlement cutoff and distinct caller-supplied snapshot/capture SQLite
  connections. It returns the complete ordered Phase 14 resolution and owns all
  metadata selection plus exact repository loads. It performs no migration.
- `write_daily_historical_replay_manifest(...)` accepts that resolution plus exact
  absolute paths, caller run/strategy/budget values and an exact output path. It
  exclusively publishes deterministic schema-v1 bytes and reloads them with
  `load_historical_replay_request_document`, returning the exact loaded document.
- `run_sqlite_historical_replay(document=...)` is the existing Ver0.8 multi-race
  execution boundary. It owns main-database migration, exact snapshot reload, one
  multi-race prediction/bet-plan batch, official settlement normalization/persistence
  and final simulation. It returns one `SimulationSummary`.
- `run_historical_replay_request(request_path=...)` is the existing standalone artifact
  re-execution boundary. The initial orchestrator does not use it because Phase 16 has
  already loaded the artifact and returned that exact document; the orchestrator passes
  that exact object directly to `run_sqlite_historical_replay` once.

`SimulationSummary` contains strategy identity fields and aggregate race/bet/settlement
metrics, but no target-set, acquisition, manifest, run ID or daily-completeness identity.
No immutable daily-result repository or daily-result schema exists. A small wrapper
result is therefore justified, while result persistence remains separate.

## Acquisition/replay separation decision

The replay orchestrator accepts one already-frozen exact
`NARDailyTargetLiveAcquisitionResult`. It never constructs or calls
`NARDailyTargetLiveAcquisitionApplication`, any Phase 22/6 transport, or `.acquire()`.
Consequently replay contains no network and cannot silently create new observed times,
capture IDs, supplier identities or target-set content during a rerun.

The exact acquisition result, rather than a bare target set, is the initial NAR input
because it retains the complete Phase 23 trace needed to identify which supplier,
Monthly and RaceList evidence produced the denominator. The Phase 14 call receives
`acquisition_result.target_set` by exact object identity. No archive lookup reconstructs
or substitutes acquisition state. A later outer facade/CLI may visibly perform
`fresh acquire -> freeze result -> replay`, but that is two explicit operations and is
outside this phase.

## Proposed public API

One future production module exposes only:

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

The two explicit SQLite connections remain caller-owned and are passed unchanged to
Phase 14. The orchestrator neither closes them nor changes transaction ownership beyond
the behavior already owned by Phase 14. `database_path` and
`nar_settlement_capture_archive_path` are the exact paths later frozen into schema v1;
the latter is the existing settlement official-response archive, never the Phase 20
daily-target evidence archive.

Before resolution, the orchestrator must fail closed unless each connection's SQLite
`main` database, as reported by the read-only `PRAGMA database_list`, names the same
existing filesystem object as its corresponding absolute path. Attached databases,
empty/in-memory paths, ambiguity, missing files or disagreement are rejected. This
prevents resolution against one evidence store followed by execution against another.
The check performs no DDL/DML, migration or repair. It must not rewrite the caller's
path text; the exact supplied absolute paths still enter the manifest.

All inputs are exact domain types. Connections must be distinct and transaction-free;
paths must be absolute, nonempty and NUL-free; `dataset_id` must equal
`run_context.dataset_id`; and the acquisition target set must be the exact supported,
nonempty singleton `NAR/nar_official` scope. No value has a default and no current clock,
environment, cwd, file timestamp or database row order supplies missing context.

## Exact orchestration sequence

```text
validate all explicit inputs and connection/path bindings
  -> call resolve_sqlite_nar_daily_evidence exactly once with
       acquisition_result.target_set unchanged,
       exact dataset_id,
       exact settlement_information_cutoff,
       exact snapshot_connection and capture_connection
  -> retain the complete returned resolution
  -> inspect resolution.day_state
  -> if PARTIALLY_RESOLVED: return diagnostic NOT_RUN result; no manifest/runner
  -> if NO_EXECUTABLE_TARGETS: return diagnostic NOT_RUN result; no manifest/runner
  -> if ALL_TARGETS_RESOLVED: require every target outcome EXECUTABLE
  -> call write_daily_historical_replay_manifest exactly once with the exact
       resolution, database/archive paths, run context, strategy, budget and path
  -> require a non-None exact reloaded document covering every target
  -> hash the exact frozen manifest bytes
  -> call run_sqlite_historical_replay(document=projection.document) exactly once
  -> re-hash and require the manifest bytes remained unchanged
  -> validate the exact SimulationSummary type, strategy identity fields and
       race_count == canonical_target_count
  -> construct FULL_DAY_REPLAY_COMPLETED result
```

The orchestrator does not call the loader a second time. Phase 16's returned document is
already the loader-reconstructed schema-v1 authority and is passed by exact object
identity to the runner. The standalone request application remains available to rerun
the retained artifact later.

## Whole-day resolution and no-partial policy

| Phase 14 state | Phase 24 action | Meaning |
| --- | --- | --- |
| `ALL_TARGETS_RESOLVED` | Require a nonempty denominator whose every outcome is `EXECUTABLE`; generate one full manifest and invoke the runner once | Only state eligible for formal full-day replay |
| `PARTIALLY_RESOLVED` | Return `NOT_RUN_PARTIAL_RESOLUTION` with exact acquisition and resolution; do not call Phase 16 or runner | Diagnostic outcome only; no partial replay or metrics |
| `NO_EXECUTABLE_TARGETS` | Return `NOT_RUN_NO_EXECUTABLE_TARGETS` with exact acquisition and resolution; do not call Phase 16 or runner | Audited nonempty denominator has no executable target; never a successful zero-race day |

Phase 23's supported target set is nonempty. Therefore `NO_EXECUTABLE_TARGETS` never
means that a zero-race provider day was positively proven. A discovery/integrity error
raises before any result. Non-run results have `manifest_projection=None`,
`manifest_sha256=None` and `summary=None`; they expose no ROI or partial metrics.

The orchestrator intentionally does not use Phase 16's permitted partial projection.
That projection remains a valid lower-level diagnostic artifact contract, but the
initial formal daily replay policy is stricter. No race is dropped, skipped, retried or
reclassified by Phase 24.

## Result invariants and audit identity

The immutable result always retains the exact acquisition result and exact complete
resolution. `canonical_target_count` is derived from the audited target set;
`executable_count` is derived from exact dispositions. No `target_race_count` field is
introduced and `SimulationSummary.race_count` remains unchanged.

For `FULL_DAY_REPLAY_COMPLETED`, the result requires:

- exact target-set equality/object binding through acquisition, resolution and manifest;
- `executable_count == canonical_target_count > 0`;
- a non-None Phase 16 projection/document and lowercase manifest SHA-256;
- the document's source path equals the caller's manifest path;
- document run context, strategy, dataset, paths, budget coverage and ordered races are
  the exact Phase 16 outputs;
- an exact `SimulationSummary` whose strategy ID/name/config hash equal the supplied
  `StrategyIdentity` and whose `race_count` equals the full denominator.

`orchestration_audit_sha256` is a content-derived lowercase SHA-256, not a clock-based
run ID and not a persistence key. Its canonical payload version is
`nar-daily-replay-orchestration-audit-v1` and contains:

- target date; all Phase 23 supplier/Monthly/ordered RaceList capture IDs and supplier
  evidence identity; and `target_set.content_sha256`;
- dataset, selection policy, settlement cutoff, resolution state and every ordered
  outcome's target key, disposition/reasons, internal race ID, exact snapshot identity
  fields/content digest and exact result/payout reference fields;
- exact database/archive/manifest path strings, caller run-context fields, strategy
  ID/name/config hash and uniform budget amount;
- execution state and manifest SHA-256 or null.

Object keys are lexically sorted; lists retain their authoritative tuple order; text is
UTF-8/NFC; datetimes are UTC ISO-8601 with microseconds and explicit `+00:00`; JSON uses
`ensure_ascii=False`, `allow_nan=False`, separators `(',', ':')`, no trailing LF, then
SHA-256. Optional values are explicit JSON null. Python repr, unordered iteration,
locale, filesystem metadata and current time are forbidden digest material.

The audit digest identifies the frozen acquisition, complete resolution and exact replay
request/run inputs. The exact `SimulationSummary` remains a first-class result value and
is not redundantly reserialized into this request/evidence audit digest. Equal frozen
inputs produce the same audit digest; changing the target-set content digest, selected
evidence, run context, strategy, budget, paths, state or manifest bytes changes it.

## Manifest lifecycle

The caller exclusively owns selection and retention of the exact absolute manifest
destination. Its parent must already exist. Phase 24 never invents a clock/random/temp
name, creates directories, overwrites, selects another path or retries publication.

For an all-resolved day, Phase 16 owns exclusive creation and safe cleanup only when its
own publication/reload validation fails. Once Phase 16 returns successfully, the
manifest remains as an audit and exact-rerun artifact. Phase 24 never deletes it,
including after a runner or post-run validation failure. The caller may manage retention
outside this application, but no automatic cleanup is designed here.

The orchestrator hashes bytes after successful Phase 16 publication and again after the
runner. Any mutation/replacement/read failure prevents a successful daily result. It
does not trigger a rewrite, alternate filename or rerun. Existing runner durable effects
may remain, exactly as Phase 1 already permits after runner failure.

## Strategy, budget and causal boundaries

`StrategyIdentity` is the sole strategy authority and is passed unchanged to Phase 16.
There is no duplicate StrategyConfig, default strategy or current-market selection.
The one exact `BetStakeBudget` is passed unchanged; Phase 16 alone projects it to all
manifest races. No per-race/venue/confidence/portfolio fallback is introduced.

The exact caller `settlement_information_cutoff` is passed to Phase 14 and copied by
Phase 16. Snapshot selection remains bounded by each audited scheduled start inside
Phase 14. `SimulationRunContext.started_at` is caller-supplied. Acquisition observed
times, current time, manifest timestamps and file metadata are never substituted for a
prediction, settlement or snapshot cutoff.

## Runner and failure semantics

`run_sqlite_historical_replay` is called once and only once, only after an all-resolved
full manifest exists. Phase 24 never directly calls prediction, plan generation,
strategy allocation, provider normalizers, payout handling, settlement or metrics code.
It never parses raw HTML or reconstructs provider URLs/identities.

Resolver, connection-binding, projection, reload, file-integrity and runner exceptions
propagate with their existing type/cause. The orchestrator does not catch them into a
success or generic wrapper. A runner exception returns no orchestration result and no
partial `SimulationSummary`; it triggers no retry, target removal, reduced manifest,
fallback dataset/capture or per-race replay. Existing durable plan/result/payout prefix
may remain and is not repaired or rolled back by this layer.

An invalid runner return, summary strategy mismatch, summary race-count mismatch or
post-run manifest mutation also raises and returns no successful result. No daily-result
failure row is written in this phase.

## Network, migration and persistence boundaries

The future orchestrator is no-network and must contain no HTTP client, supplier
transport or Phase 23 `.acquire()` call. It has no browser/eval/exec and no current-clock
call. It performs no source acquisition, archive cache lookup or fallback.

Phase 24 adds no SQL domain logic, DDL, migration invocation or schema repair. Its only
SQLite-specific validation is read-only connection/path binding. Phase 14 owns evidence
reads and the existing runner remains the sole owner of main-database migration plus
replay writes. The Phase 20 daily-target archive is not opened by replay.

This is an ownership boundary, not a claim that the complete replay path is read-only.
The orchestrator itself must not call `apply_migrations`, persist an orchestration
aggregate, or implement settlement/bet-plan persistence. After the orchestrator makes
its one approved call, the unchanged existing `run_sqlite_historical_replay` is already
authorized to apply its main migrations, persist historical bet plans, persist official
settlement facts and race-result/payout data, then build `SimulationSummary`. Those are
existing runner behaviors, not new Phase 24 persistence. Only persistence of
`NARDailyReplayOrchestrationResult` or a daily aggregate remains deferred.

Daily replay result persistence and cumulative aggregation are deferred to a separately
reviewed phase, tentatively `Daily Replay Result Persistence and Aggregation`. That phase
may persist successful and failed batch audit state but must not alter this execution
contract or `SimulationSummary`. Phase 24 implementation must first close deterministic
execution only.

## Required tests for a later IMPLEMENTATION phase

One future test module must freeze at least these behavior groups:

1. exact public enum/result/function API and exact keyword-only signature;
2. exact frozen Phase 23 acquisition result required; no bare/substituted target set;
3. no Phase 23 application construction or `.acquire()` call;
4. exact acquisition target-set object passed unchanged to Phase 14;
5. exact dataset ID and settlement cutoff passed unchanged;
6. exact snapshot and settlement-capture connection objects passed unchanged;
7. connection/path binding accepts exact existing pair and rejects mismatch, attachment,
   in-memory/empty path, missing path and alias ambiguity without writes;
8. exact database, settlement archive and manifest paths propagated without cwd/default;
9. `ALL_TARGETS_RESOLVED` proceeds only when every target is EXECUTABLE;
10. `PARTIALLY_RESOLVED` returns diagnostic non-run state with full denominator;
11. `NO_EXECUTABLE_TARGETS` returns diagnostic non-run state and is not a zero-race success;
12. partial/no-executable states create no manifest and invoke no loader/runner;
13. no partial summary/ROI or successful full-day claim exists;
14. Phase 16 writer is called exactly once only for all-resolved input;
15. exact StrategyIdentity, uniform budget and SimulationRunContext propagate unchanged;
16. Phase 16 exclusive-create, existing-path and parent-missing failures propagate;
17. exact Phase 16 loaded document object is passed to the runner;
18. existing schema-v1 loader/revalidation is retained with no second custom loader;
19. existing Ver0.8 SQLite runner is called exactly once, is unchanged, and its existing
    internal migration/bet-plan/settlement/result/payout writes remain allowed;
20. runner summary exact type/strategy/race-count validation;
21. resolver failure creates no manifest and makes no runner call;
22. projection/reload failure makes no runner call;
23. runner failure returns no result/partial summary and does not retry;
24. invalid runner return or summary mismatch fails closed;
25. no target skip/drop, per-race loop, reduced-manifest rerun or fallback evidence;
26. manifest SHA is exact, retained, and unchanged before/after runner;
27. runner failure retains the successfully frozen manifest; no orchestrator cleanup;
28. exact acquisition capture IDs and supplier identity remain traceable in result/digest;
29. exact complete resolution and denominator remain in every returned state;
30. canonical target and outcome ordering remain deterministic;
31. canonical/executable count properties are derived correctly; no target_race_count;
32. deterministic canonical audit SHA for identical frozen inputs;
33. target-set digest/evidence/run/strategy/budget/path/state/manifest changes alter audit SHA;
34. audit SHA contains no clock/filesystem timestamp/repr/unordered material;
35. no network/HTTP/supplier transport/cache/live-acquisition behavior;
36. no direct current-clock dependency or causal timestamp substitution;
37. no prediction, bet, provider parser/normalizer, payout, settlement or metrics duplication;
38. orchestrator itself makes no migration call, DDL/DML, database repair or Phase 20
    archive use; this does not prohibit the invoked unchanged runner's existing writes;
39. caller-owned connections remain open and transaction-free after normal resolution;
40. Phase 14 resolver regression;
41. Phase 16 projection and schema-v1 loader/request-application regressions;
42. existing SQLite historical replay application regression;
43. Phase 23 acquisition regression;
44. full unittest suite and static boundary checks.

Future verification must include dedicated, Phase 14, Phase 16/request, runner and Phase
23 regressions plus:

```text
python -m unittest discover -s tests -p "test_*.py"
rg -n "requests|httpx|urllib\.request|socket|NARDailyTargetLiveAcquisitionApplication|\.acquire\(|datetime\.now|datetime\.today|utcnow|time\.time|apply_migrations|CREATE TABLE|INSERT |UPDATE |DELETE |BeautifulSoup|HTMLParser|PredictionPipeline|acquire_and_persist_official_settlement_facts|execute_final_historical_settlement_simulation" scripts/simulation/nar_daily_replay_orchestrator.py
git diff --check
git diff --name-only
git status --short
git diff --cached --name-only
```

Expected static hits from imported immutable result/types or explanatory strings must be
individually justified; direct boundary calls are forbidden. Tests use temporary SQLite
files and caller paths only, never database/keiba.db, logs, network or provider archives.
No failure is skipped or relaxed.

## Stop condition

Outcome is `IMPLEMENTABLE`: the current Phase 14, Phase 16 and Ver0.8 runner APIs can be
composed safely in one new production module and one new test module; no adapter split or
existing production/schema change is required.

Stop at `DRAFT_FOR_REVIEW` after updating only the two documentation files and running
Git checks. Do not implement, test, stage, commit, push, execute replay, begin result
persistence or advance to another phase. Any review-discovered inability to prove
connection/path binding, retain whole-day semantics, pass the exact loaded document, or
avoid modifying an existing contract changes the outcome to `ORCHESTRATOR_SPLIT_REQUIRED`
and must return to ChatGPT review.
