# Current Phase

Status: `APPROVED_FOR_COMMIT`

## Identity, authority and authorization

- Phase: `POST_V0_8_DAILY_REPLAY_16`
- Name: `Daily Replay Schema-v1 Manifest Projection Implementation`
- Phase type: `IMPLEMENTATION`
- Base Commit: `6d14a9bb8b0103d7c053c3d9a7dc7c75289bef08`
- Branch: `feature/post-v0.8-daily-replay`
- Preparation outcome: `IMPLEMENTABLE`
- Current authorization: final independent review approved the completed implementation for exact staging, commit and normal push.

AGENTS.md, the committed Phase 15 contract and the existing v0.8 schema-v1 request
domain/loader are authority. Phase 14 resolution remains the complete denominator.
Phase 15 was normally pushed and fetched; local and remote branch heads were verified
equal to this Base Commit before PREPARE. This phase implements the frozen projection
contract only after a separate APPROVE_PHASE and EXECUTE_APPROVED_PHASE.

## Exact Allowed Files

During PREPARE:

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

Only after explicit approved EXECUTE:

```text
scripts/simulation/historical_daily_replay_manifest_projection.py
tests/test_historical_daily_replay_manifest_projection.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

The production and test modules are new. Existing modules are read/reuse only. No
package re-export or helper file is needed; private helpers/tests remain in these files.

## Forbidden Files and actions

Every path outside the applicable Allowed Files, including the existing schema-v1
loader/model/application/runner, Phase 14 modules/tests, shared/NAR/JRA source code,
fixtures, schema/migrations, database/**, logs/**, archives, CLI, dependencies,
AGENTS.md and release history. Never stage database/keiba.db or logs/.

No schema-v1 change, migration, database/archive write or read, network, runner
execution, orchestration, result persistence, ROI/reporting, JRA support, evidence
resolution, settlement parsing, implicit clock/path default, stage, commit, push or
next-phase transition is authorized by PREPARE or the future EXECUTE.

## Exact public API

The new production module exports exactly these two definitions:

```python
@dataclass(frozen=True, slots=True)
class DailyHistoricalReplayManifestProjection:
    resolution: DailyHistoricalReplayEvidenceResolution
    document: HistoricalReplayRequestDocument | None


def write_daily_historical_replay_manifest(
    *,
    resolution: DailyHistoricalReplayEvidenceResolution,
    database_path: Path,
    nar_capture_archive_path: Path,
    run_context: SimulationRunContext,
    strategy_identity: StrategyIdentity,
    race_budget: BetStakeBudget,
    manifest_source_path: Path,
) -> DailyHistoricalReplayManifestProjection:
    ...
```

All parameters are keyword-only. Exact existing types are required; strings are not
accepted as Paths and bool is never accepted as an integer through projection. There
is no separate StrategyConfig, dataset, cutoff, payout-catalog, clock, repository,
connection, loader callback or runner argument. Helpers remain private and no new
exception class is exported.

The result stores the exact supplied resolution object. `document` is either the exact
successfully reloaded schema-v1 document or None. Its invariants are:

- NO_EXECUTABLE_TARGETS requires document None.
- ALL_TARGETS_RESOLVED and PARTIALLY_RESOLVED require a document.
- A document's ordered race tuple and budget keys must correspond exactly to the
  resolution's EXECUTABLE outcomes and no others.
- The value has no full-day-success flag and creates no alternative day-state enum;
  `resolution.day_state` is authority.

## Input validation and sole authorities

Validate all exact input domains before any filesystem mutation. Require
`resolution.dataset_id == run_context.dataset_id`, exact singleton target provider
scope `NAR/nar_official`, and the existing Phase 14 canonical denominator/outcome
invariants. Do not rediscover, repair or copy a replacement resolution.

`strategy_identity` is the only strategy authority. Require exact StrategyIdentity,
`strategy_name == "RuleBasedBetStrategy"`, and equality with the result of the existing
`build_strategy_identity(strategy_name, strategy_config)` contract. Serialization reads
only `strategy_identity.strategy_config`. Do not accept another StrategyConfig or
independently calculate/store a second config/hash/ID authority.

The strategy config must be exactly representable by the current schema-v1 loader:

- allowed_bet_types is the existing frozenset containing only supported types;
- max_bet_count and max_candidates are nonnegative non-bool integers;
- selection_style and sort_condition are exact existing enums;
- min_combination_score is a finite float that reloads exactly;
- allocation_policy is exact AllocationPolicyConfig with name
  fixed_stake_per_recommendation, version `1`, and exactly one `stake_amount` parameter,
  a positive non-bool 100-yen multiple.

Unsupported or non-round-trippable strategy content fails before file creation. The
existing domain/build function remains the validation authority; private serialization
checks only enforce the narrower existing loader shape.

`database_path`, `nar_capture_archive_path` and `manifest_source_path` must each be an
absolute Path. Reject relative values; never call Path.resolve(), consult cwd, prepend
the manifest directory or otherwise normalize/rewrite caller intent. Reject NUL. Use
`str(path)` as the exact absolute JSON text for database/archive. The source path is not
a JSON field and is passed to the loader unchanged. Require exact loaded Path equality
with all three caller inputs. Only for a nonempty executable projection, require
`manifest_source_path.parent.is_dir()`; never mkdir. Do not require/open/stat the
database or archive paths.

`run_context.started_at` is the exact caller-supplied aware datetime. No current time,
run-start default or environment value is generated. `race_budget` is one exact
BetStakeBudget and remains the sole budget input.

## Exact projection

Filter only outcomes with disposition exactly EXECUTABLE while traversing the existing
Phase 14 outcome tuple. Because that tuple is already aligned to the target-set order,
the manifest race array preserves canonical
`(organization, source_system, external_race_id)` order. Do not resort by race number,
scheduled time, internal ID, capture time or storage order.

Before constructing a race request, require:

- exact snapshot_identity, positive internal_race_id and both capture references;
- snapshot dataset/provider/external race identity exact agreement with the resolution,
  NAR target and run context;
- unique snapshot identities and unique internal race IDs across executable outcomes;
- result and payout references are the same exact Phase 14 selected settlement capture;
- capture IDs are retained verbatim and never generated from URL/body/target;
- resolution settlement_information_cutoff is retained exactly for every race.

Construct one existing `HistoricalReplayRaceRequest` per executable outcome. Its
`result_capture_id` is the selected result reference's exact capture_id. Its payout
catalog has exactly the keys `単勝`, `馬連`, `ワイド`, `3連複`, each mapped to the
selected payout reference's exact capture_id. Populate in lexical key order even though
the canonical JSON serializer also sorts object keys. Do not inspect or parse body bytes
or claim that a purchased bet type is present; existing normalizer/runner semantics are
unchanged.

Project the same exact `race_budget` value to every executable internal race ID and no
other target. Budget keys after construction and reload must equal manifest race IDs
exactly. The expected `HistoricalReplayRequestDocument` uses schema_version 1, exact
`manifest_source_path`, exact database path, only capture archive key
`NAR/nar_official`, exact caller run/strategy, ordered races and budgets. Construct and
fully validate this expected domain before serialization/write.

## Day-state and audit boundary

| Phase 14 state | Exact behavior |
| --- | --- |
| ALL_TARGETS_RESOLVED | Every target must be EXECUTABLE and projected; create one manifest |
| PARTIALLY_RESOLVED | Project only EXECUTABLE subset; retain the original complete resolution; never describe it as full-day replay/ROI success |
| NO_EXECUTABLE_TARGETS | Return projection with the original resolution and document None; do not inspect/create/read manifest_source_path and produce no runner-callable request |

The schema-v1 manifest never becomes daily denominator/completeness authority and gains
no day-state/non-executable fields. Filtering is not target deletion: the returned
resolution retains every missing/unsupported/invalid target. This module never invokes
the runner. A future orchestrator may pass a non-None document to exactly one multi-race
run while retaining the projection result; it may not retry, reduce and rerun or promote
partial execution to full-day success.

## Canonical schema-v1 bytes

Build only the existing exact root/nested schema. The byte contract is:

```python
(json.dumps(
    payload,
    sort_keys=True,
    ensure_ascii=False,
    allow_nan=False,
    separators=(",", ":"),
) + "\n").encode("utf-8")
```

This yields compact UTF-8 without BOM and exactly one final LF. Object keys are sorted
lexically. `races` preserves canonical executable order. Strategy allowed_bet_types is
serialized as a lexical list; payout keys are lexical; budget keys are canonical
positive decimal strings. No repr, Python hash, unordered set/mapping iteration,
locale, platform newline, filesystem time/order or current time participates.

Serialize every datetime after `astimezone(timezone.utc)` using
`isoformat(timespec="microseconds")`, yielding an explicit `+00:00` offset. Instant
semantics are preserved and the existing loader reconstructs equal datetimes. Serialize
database/archive paths with exact `str(caller_path)` text; no slash conversion or
filesystem canonicalization is permitted. `manifest_source_path` is represented only by
the exact loader argument/domain field, never a synthetic JSON field.

## Exclusive publication, reload and cleanup

The expected document and canonical bytes must exist and validate in memory before any
file operation. For an executable projection:

1. Verify the supplied parent exists as a directory without creating it.
2. Open the exact final `manifest_source_path` in exclusive binary creation mode (`xb`).
   A pre-existing path raises and is never opened for write, deleted or replaced.
3. Write all bytes, verify the full byte count, flush, fsync and close. Do not use a
   temporary/rename overwrite path and do not append or edit.
4. Call the unchanged
   `load_historical_replay_request_document(request_path=manifest_source_path)`.
5. Read the artifact bytes and require byte-for-byte equality with the canonical bytes.
   Require the loaded document equals the expected document field-by-field: schema,
   exact source/database/archive Paths, run context, strategy identity, budgets and
   ordered races.
6. Return the projection only after all checks pass.

Track whether this invocation won exclusive creation and the created file identity.
On any write/flush/close/reload/byte/equality failure after creation, delete the final
path only when it can still be proven to be the exact file created by this call, then
re-raise the original exception. File identity metadata may be used only for safe
cleanup, never serialization/digest/ordering. If identity cannot be proven or cleanup
fails, do not delete a possibly foreign file; retain the original failure with cleanup
context and return no success. Never touch a pre-existing target or adjacent path.

This is an exclusive no-overwrite publication boundary, not a durable repository or a
multi-file transaction. A concurrently visible incomplete file is never runner-callable
through this API because only the successfully validated returned document is eligible.
Reusing a frozen valid artifact goes directly through the existing loader/application;
the writer never overwrites it.

## Required tests during EXECUTE

All Phase 15 acceptance behaviors remain mandatory, including its review clarification.
Do not replace behavioral coverage with a fixed unittest-method count.

| # | Required behavior |
| --- | --- |
| 1 | ALL_TARGETS_RESOLVED projects every target in canonical target order |
| 2 | PARTIALLY_RESOLVED projects executable subset while retaining exact original resolution and no full-day-success signal |
| 3 | NO_EXECUTABLE_TARGETS returns None without inspecting/creating/reading source path |
| 4 | Exact snapshot/internal/result/payout/cutoff projection; all four payout keys use the selected payout capture ID without parsing body |
| 5 | Same BetStakeBudget covers exactly all manifest race IDs and no non-executable target |
| 6 | Dataset, provider, snapshot/external/internal identity and missing-reference contradictions fail before publication |
| 7 | Duplicate snapshot identity or internal race ID fails without hidden skip |
| 8 | Canonical race/catalog/set/object ordering and deterministic identical bytes under shuffled non-authoritative inputs |
| 9 | StrategyIdentity is the sole strategy argument/authority; exact loader round trip; unsupported or altered config/hash/ID fails |
| 10 | Relative manifest, database and archive Paths rejected; no cwd or Path.resolve dependency |
| 11 | Exact absolute source/database/archive Path text and Path equality after reload |
| 12 | Missing parent fails without mkdir or artifact; existing output is byte-preserved and never overwritten/deleted |
| 13 | Expected document validation completes before exclusive filesystem creation |
| 14 | Exact compact sorted-key UTF-8 bytes, one final LF, UTC microseconds/offset and no repr/nonfinite/implicit value |
| 15 | Existing loader reload and complete document equality; byte mismatch returns no success |
| 16 | Reload/equality failure deletes only the new same-identity file; adjacent/pre-existing/replaced file is preserved; cleanup failure stays fail closed |
| 17 | Explicit run_context.started_at; current-clock calls trapped and unused |
| 18 | Network/acquisition calls trapped and unused |
| 19 | SQLite/migration/runner/body-normalizer calls trapped and unused; no database/archive write/read |
| 20 | Original resolution/target/outcome object identities and denominator remain unchanged in all states |
| 21 | Exact frozen public exports, keyword-only signature, immutable result and state/document invariants |
| 22 | Existing schema-v1 loader/request application/SQLite runner and Phase 14 resolution regressions remain unchanged |

Use synthetic immutable values and temporary output directories only. Tests must not
touch database/keiba.db, logs, official fixtures/archives or network. Patch clock,
network, SQLite/migration/runner/normalizer entry points to fail if invoked. File tests
must compare bytes before/after and cover safe-cleanup identity behavior. Do not skip or
relax a failure.

### Exact verification commands during EXECUTE

Dedicated:

```text
python -m unittest tests.test_historical_daily_replay_manifest_projection
```

Related:

```text
python -m unittest tests.test_historical_daily_evidence_resolution tests.test_historical_replay_request_document tests.test_historical_replay_request_application tests.test_sqlite_historical_replay_application
```

Full suite:

```text
python -m unittest discover -s tests -p "test_*.py"
```

Static boundary search; inspect every hit, with no-match exit acceptable:

```text
rg -n "datetime\.now|datetime\.today|utcnow|time\.time|requests|httpx|urllib\.request|socket|sqlite3|apply_migrations|run_sqlite_historical_replay|target_race_count|Path\.resolve" scripts/simulation/historical_daily_replay_manifest_projection.py
```

Git checks:

```text
git diff --check
git diff --name-only
git status --short
git diff --cached --name-only
```

No fixed passing-test count is a substitute for the 22 behavior groups. Report the
actual dedicated, related and full counts separately. Account for both untracked new
files in status and whitespace-check them without staging. Cached output must remain
empty. Any warning or static-search hit is reported with evidence.

## EXECUTE_APPROVED_PHASE gate and stop condition

Before implementation verify Status APPROVED_FOR_CODEX, exact Phase/Branch/Base, only
the two PREPARE docs dirty, empty index, and the Allowed/Forbidden/Required Tests/Stop
Condition above. The user requests GPT-5.6 Sol for actual EXECUTE; PREPARE does not
initiate implementation.

On authorized EXECUTE success only: implement the two new production/test paths, run
dedicated/related/full suites and static/Git checks, keep every change within the four
exact EXECUTE Allowed Files, update Status to READY_FOR_REVIEW and append the result to
LATEST_CODEX_REPORT; then stop without stage/commit/push or a next phase.

On any contract conflict, need to edit an existing file, strategy/path round-trip
ambiguity, inability to prove safe own-file cleanup, failing test, unexpected path,
schema/migration/database/archive requirement or other blocker, stop without guessing,
fallback, path rewrite, overwrite or weakened assertion. Current preparation outcome is
IMPLEMENTABLE with no blocker.

## Execution completion

EXECUTE_APPROVED_PHASE completed within the four exact Allowed Files. The new production
module exports only the frozen immutable projection and keyword-only writer. It validates
the sole-authority StrategyIdentity, exact NAR resolution/provider/dataset/reference
relations and absolute caller Paths before publication. It projects only EXECUTABLE
outcomes in canonical target order, uses one uniform budget, preserves the exact cutoff
and selected capture IDs, and retains the complete original resolution in all day states.

Canonical existing schema-v1 JSON is written as compact sorted-key UTF-8 with exactly one
LF and UTC microsecond offsets. Publication exclusively creates the final path, then
performs exact byte and existing-loader domain/path/strategy round-trip checks. Failure
cleanup verifies the created file identity before unlinking; pre-existing, replaced and
adjacent paths are preserved. The implementation has no clock, network, SQLite,
migration, runner or body-parser dependency.

Verification: dedicated 20 tests PASS; related 51 tests PASS; full suite 2,987 tests
PASS. The frozen static boundary search has no matches. Dedicated tests emit no
ResourceWarning; full-suite warnings reproduce existing unclosed SQLite connections in
pre-existing tests/modules. No test was skipped or relaxed. Final Git checks and scope
are recorded in LATEST_CODEX_REPORT. Status is READY_FOR_REVIEW; stop without staging,
commit, push or another phase.
