# Current Phase

Status: `APPROVED_FOR_COMMIT`

## Identity, authority and authorization

- Phase: `POST_V0_8_DAILY_REPLAY_15`
- Name: `Daily Replay Schema-v1 Manifest Projection Design`
- Phase type: `DESIGN_ONLY`
- Base Commit: `40268c75bfd2ede8f4d64811e5a72db06fc8a9c3`
- Branch: `feature/post-v0.8-daily-replay`
- Preparation outcome: `IMPLEMENTABLE`
- Current authorization: design review only; no implementation, staging, commit or push.

AGENTS.md, the applicable existing Ver0.8 contracts, the approved Phase 1 manifest
artifact boundary and the committed Phase 13/14 resolution contracts are authority.
This phase does not amend them. The Base Commit was normally pushed, fetched and
verified equal to origin/feature/post-v0.8-daily-replay before this PREPARE.

## Exact Allowed Files

During this DESIGN_ONLY phase:

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

The following are future implementation candidates only and are not Allowed Files in
this phase:

```text
scripts/simulation/historical_daily_replay_manifest_projection.py
tests/test_historical_daily_replay_manifest_projection.py
```

No existing request-document, request-application, runner or package export needs a
change. A later implementation phase must separately PREPARE, receive ChatGPT review,
APPROVE and EXECUTE authorization before those two candidate files become writable.

## Forbidden Files and actions

Every path other than the two documentation files is forbidden in Phase 15, including
production, tests, fixtures, schema/migrations, database/**, logs/**, archives, CLI,
AGENTS.md and release history. database/keiba.db and logs/ must never be staged.

No implementation, fixture acquisition, network access, database access, migration,
runner call, stage, commit, push or next-phase transition. No new replay schema,
schema-v1 field, target count, prediction/bet/settlement logic, JRA support, daily
result persistence, reporting, ROI aggregation or CLI is designed or implemented here.

## Existing boundary findings

The existing `HistoricalReplayRequestDocument` is already the exact immutable domain
for schema version 1. Its root JSON keys are exactly:

```text
schema_version
database_path
capture_archives
run_context
strategy
budgets_by_race_id
races
```

`load_historical_replay_request_document(request_path=...)` is the authority for UTF-8
decoding, duplicate-key rejection, finite JSON numbers, exact nested key sets, enum/
strategy reconstruction, canonical positive budget IDs and request-domain validation.
It sets `source_path` to the real supplied request path and resolves relative database/
archive paths against that path. `HistoricalReplayRequestDocument` requires a nonempty
race tuple; therefore it cannot and must not represent a zero-executable day.

Each existing `HistoricalReplayRaceRequest` already carries the required exact snapshot
identity, internal race ID, settlement cutoff, result capture ID and payout capture
catalog. The document already proves unique snapshot/internal identities, exact budget
coverage, dataset agreement and archive coverage for represented providers. The
existing `run_historical_replay_request` loads the file and invokes the existing
multi-race SQLite runner exactly once; neither it nor the runner is called in this phase
or moved into the future manifest projection module.

The schema's strategy object is configuration-shaped rather than an independently
serialized strategy ID/hash. Loading rebuilds the existing `StrategyIdentity`. The
projection must therefore serialize the exact caller-supplied identity's config and
prove round-trip identity equality; it must not invent, weaken or separately override
strategy identity/configuration.

## Proposed public API and ownership

The single future production module owns only deterministic executable projection and
one real file artifact. Its proposed public surface is:

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

`strategy_identity` is the sole strategy authority. No separate StrategyConfig argument
is accepted. Serialization reads only `strategy_identity.strategy_config`; require
`strategy_identity.strategy_name == "RuleBasedBetStrategy"` and all existing
StrategyIdentity invariants. The writer must reuse the existing domain and
`build_strategy_identity` contract through loader reconstruction; it must not calculate
or maintain an independent strategy config/hash/ID authority. Reloaded StrategyIdentity
must equal the exact caller-supplied value. No clock, repository, connection, provider
client, loader callback or runner is injected. Helpers remain private. Existing ValueError/domain validation,
`HistoricalReplayRequestValidationError`, `FileExistsError` and ordinary I/O errors
propagate; no broad catch-and-success or new error hierarchy is needed.

The immutable return value is the audit join between the complete denominator and its
executable artifact. Its construction requires the exact Phase 14 resolution type.
When `document` exists it must be the exact object reloaded from `manifest_source_path`; when it
does not, the resolution state must be `NO_EXECUTABLE_TARGETS`. A document is mandatory
for the other two states. It exposes no replay-success boolean and introduces no new
day-state enum: `resolution.day_state` remains authoritative.

## Explicit caller inputs and validation

All context is explicit. The projection must not derive any input from current time,
SQLite row order, environment variables, repository state or output-file metadata.

- `resolution` supplies the complete audited denominator, dataset ID, exact uniform
  settlement_information_cutoff and all target outcomes/references.
- `database_path` is the future runner's main database path.
- `nar_capture_archive_path` is the sole `NAR/nar_official` capture archive path.
- `run_context` supplies run_id, dataset_id, caller-chosen aware started_at and target
  commit ID. In particular, started_at is never generated with a clock.
- `strategy_identity` supplies the exact supported RuleBasedBetStrategy configuration,
  including its fixed-stake allocation policy, and its derived identity/hash.
- `race_budget` is one exact BetStakeBudget projected unchanged to every executable
  internal race ID.
- `manifest_source_path` is the exact real manifest output path and becomes the loaded
  document's source_path. It is not a synthetic/nonexistent placeholder on success.

Require exact domain types, `resolution.dataset_id == run_context.dataset_id`, exact
singleton NAR provider identity `NAR/nar_official`, and absolute Path values for
`manifest_source_path`, `database_path` and `nar_capture_archive_path`. Relative paths
are rejected rather than interpreted through the process current directory. The writer
must not call Path.resolve(), use cwd, or otherwise rewrite caller path intent. Exact
caller-supplied absolute database/archive path text is serialized; after reload the
source, database and archive Paths must equal the caller inputs exactly. The builder
does not open or inspect the database/archive or use filesystem metadata to derive any
path. `manifest_source_path.parent` must already be a directory; the writer never calls
mkdir or creates parent directories.

The supplied strategy must be exactly reconstructible by the current schema-v1 loader:
RuleBasedBetStrategy, the loader-supported enums and finite score, unique supported bet
types, and fixed_stake_per_recommendation policy version 1 with exactly positive
100-yen-multiple `stake_amount`. Any config the existing loader cannot round-trip is a
projection error, not a reason to change the loader/schema or silently substitute a
default. Zero budget remains valid because existing BetStakeBudget/schema-v1 permits it.

Validate all caller inputs before the zero-executable branch, but do not inspect or
create `manifest_source_path` in that branch. Parent-directory creation is never performed.

## Exact projection contract

Only outcomes whose disposition is exactly `EXECUTABLE` enter the schema-v1 `races`
array. Iterate the already canonical Phase 14 outcome order and filter without sorting
by scheduled time, internal ID, capture time or database insertion order. This preserves
the target-set ordering `(organization, source_system, external_race_id)`.

For every executable outcome, fail closed unless all Phase 14 invariants remain true:

- snapshot identity and positive internal race ID exist; snapshot provider/external
  race and dataset agree exactly with target/resolution/run context;
- snapshot identities and internal race IDs are unique across the executable projection;
- result and payout references both exist and are the same exact selected settlement
  capture reference; no capture ID or URL is generated or looked up;
- the exact resolution `settlement_information_cutoff` is copied to the race request;
- the result capture ID is that selected capture's exact capture_id;
- payout catalog keys are exactly `単勝`, `馬連`, `ワイド`, `3連複`, each mapped to
  that same capture_id in deterministic lexical-key order;
- the same caller-supplied `race_budget` is mapped to every executable internal race
  ID, and no budget is synthesized for a non-executable denominator member.

The projection does not parse capture HTML or guarantee body-level result/payout
semantics. The existing runner/normalizers retain that responsibility and their
exceptions later propagate without partial summary, retry or reduced-manifest rerun.

The resulting document must have exactly schema_version 1, only the NAR archive key,
the explicit run/strategy/path inputs, budget keys exactly equal to race IDs, and the
canonical executable race order. It must satisfy the existing
`HistoricalReplayRaceRequest` and `HistoricalReplayRequestDocument` constructors before
bytes are written. No target, resolution outcome, reference or caller-owned mapping is
mutated.

## Day-state and denominator boundary

| Resolution state | Artifact rule | Audit meaning |
| --- | --- | --- |
| ALL_TARGETS_RESOLVED | Project every target; write one nonempty manifest | Full denominator is executable; this is still readiness, not replay/ROI success |
| PARTIALLY_RESOLVED | Project only EXECUTABLE outcomes; write one nonempty manifest | Resolution remains the full denominator; manifest is explicitly a subset and can never establish full-day success |
| NO_EXECUTABLE_TARGETS | Return `document=None`; do not create/read the output path | No manifest and no later runner invocation |

The return value retains the exact original Phase 14 resolution in all states. The
schema-v1 artifact is never denominator/completeness authority and receives no new
fields for missing/unsupported/invalid targets. A future orchestrator must retain the
projection result while passing only its non-None document to the existing runner.
It may call the runner at most once. It must not drop another race, retry per race,
reduce and rerun, or report partial execution as full-day replay/ROI success.

## Deterministic schema-v1 serialization

The future writer freezes the following canonical byte contract without adding a
manifest digest or schema field:

- Build only the existing schema-v1 JSON tree; object keys are lexically sorted at
  every level by `json.dumps(sort_keys=True)`.
- Use `ensure_ascii=False`, `allow_nan=False`, separators `(',', ':')`, append exactly
  one LF, and encode UTF-8 without BOM. Python repr, locale, platform newline, file
  timestamps and unordered mapping/set iteration are forbidden.
- Datetimes serialize after UTC conversion as ISO-8601 with six fractional digits and
  `+00:00`. This preserves the exact instant and uses no current clock.
- `races` retains canonical executable target order. `allowed_bet_types` and payout
  catalog keys are lexically ordered. Budget object keys are canonical decimal positive
  integer strings; deterministic JSON object-key ordering applies.
- Absolute database/archive paths use their exact caller-supplied text. source_path
  is not a JSON field; it is the exact Path passed to the loader after publication.

Construct and validate the complete expected HistoricalReplayRequestDocument domain
before serialization or filesystem mutation. The caller must supply a fresh output path
whose parent already exists. The writer uses exclusive binary creation of the final
path and writes the canonical bytes once; it never overwrites, appends, edits, replaces,
merges or silently accepts an existing file. Any pre-existing target or write/flush/
close error fails closed. A path is accepted as the frozen manifest artifact only after
the complete bytes are closed and reload validation succeeds. This design makes no
durable artifact repository or transaction claim and never writes a temporary file into
database/archive/fixture locations.

After writing, call the existing
`load_historical_replay_request_document(request_path=manifest_source_path)` directly. Require
exact equality of the loaded document against the prevalidated expected domain,
including source/database/archive paths, run context, reconstructed strategy identity,
budgets, canonical race tuple, snapshot identities, cutoff and capture catalogs. Also
require the file bytes still equal the canonical bytes just written. A mismatch raises;
no document or replay-ready result is returned, the runner is not called and no schema/
loader fallback is attempted. If reload or equality validation fails, remove only the
manifest final path that this invocation exclusively created, then re-raise the original
exception fail closed. Never delete, replace or modify a pre-existing file or any other
path. A cleanup failure must also stop and must not turn the invalid artifact into a
successful result. Re-execution of a frozen valid artifact uses the existing loader/
application directly, not a builder overwrite.

## Failure semantics and responsibility boundaries

Malformed/mismatched caller domains, provider/dataset/reference inconsistency,
duplicate identity/ID, unsupported strategy round-trip and projection contradiction
fail before publication. Output-path collision and I/O/reload mismatch fail without a
success value. There is no silent target skip beyond the explicit EXECUTABLE filter,
fallback capture, default context/budget, current-clock value, file overwrite or partial
document return.

This builder has no network, SQLite connection, migration, source discovery, evidence
resolution, archive lookup, capture parsing, prediction, bet generation, settlement,
runner or reporting responsibility. Existing schema-v1 loader and runner remain
unchanged. Manifest file creation is the only authorized future side effect.

## Required tests for a later implementation phase

All tests belong in the single proposed test module; production implementation and
tests require a separate approved phase.

| # | Required behavior |
| --- | --- |
| 1 | ALL_TARGETS_RESOLVED writes all executable targets in canonical target order |
| 2 | PARTIALLY_RESOLVED writes only executable subset and retains exact full resolution |
| 3 | Partial projection exposes no full-day success claim and cannot turn manifest races into denominator |
| 4 | NO_EXECUTABLE_TARGETS returns None and neither creates nor reads manifest_source_path |
| 5 | Exact snapshot identity/internal race projection and uniqueness enforcement |
| 6 | Exact shared result/payout capture ID and four-key payout catalog projection; distinct/missing references fail |
| 7 | One uniform race budget projected to all and only manifest race IDs |
| 8 | Budget keys exactly equal manifest race IDs after existing-loader round trip |
| 9 | resolution/run-context dataset mismatch fails before file creation |
| 10 | provider mismatch or mixed/JRA scope fails before file creation |
| 11 | duplicate internal race or snapshot identity fails before file creation |
| 12 | malformed EXECUTABLE reference/identity contradiction fails closed without hidden skip |
| 13 | shuffled non-authoritative inputs cannot alter canonical race ordering/output bytes |
| 14 | exact compact UTF-8/LF schema-v1 bytes, sorted objects/sets/catalog, canonical paths/times, no repr/nonfinite/current-time material |
| 15 | reload through existing loader yields exact expected document and exact real source/database/archive Paths; reload/equality failure removes only this-call-created manifest and returns no success |
| 16 | explicit fixed run_context.started_at; clock functions trapped and unused |
| 17 | network/acquisition functions trapped and unused |
| 18 | SQLite/migration/runner functions trapped and unused; only exclusive manifest file write occurs |
| 19 | original resolution/target denominator and outcome identities remain unchanged in full/partial/none cases |
| 20 | existing output path is never overwritten; relative manifest/database/archive paths, cwd-dependent resolution and missing parent fail closed without mkdir |
| 21 | existing request loader/application/SQLite runner regressions remain unchanged |
| 22 | StrategyIdentity is the sole strategy input; exact loader round trip succeeds and unsupported/mismatched identity fails without an independent config/hash/ID authority |

Future verification must include:

```text
python -m unittest tests.test_historical_daily_replay_manifest_projection
python -m unittest tests.test_historical_daily_evidence_resolution tests.test_historical_replay_request_document tests.test_historical_replay_request_application tests.test_sqlite_historical_replay_application
python -m unittest discover -s tests -p "test_*.py"
rg -n "datetime\.now|datetime\.today|utcnow|time\.time|requests|httpx|urllib\.request|socket|sqlite3|apply_migrations|run_sqlite_historical_replay|target_race_count" scripts/simulation/historical_daily_replay_manifest_projection.py
git diff --check
git diff --name-only
git status --short
git diff --cached --name-only
```

The static search's expected hits from imported type/module names, if any, must be
individually justified; network, current-clock, SQLite/migration and runner calls are
forbidden. Tests use temporary output directories and synthetic immutable domains only,
never database/keiba.db, logs, provider archives or network. No failing test may be
skipped or relaxed.

## Stop condition

Phase 15 completes only as a reviewed design. No implementation begins from this draft.
Any conflict with the existing loader/schema-v1, need to edit an existing production/
test/schema file, inability to round-trip the exact strategy identity, or unresolved
artifact publication ambiguity changes the outcome to CHANGES_REQUIRED and stops for
ChatGPT review rather than broadening scope.

Current outcome is IMPLEMENTABLE: one new production module and one new test module are
sufficient; no existing schema/loader/runner, database migration or archive protocol
change is required. Stop at DRAFT_FOR_REVIEW. Stage, commit, push, runner execution and
POST_V0_8_DAILY_REPLAY_16 are not authorized.
