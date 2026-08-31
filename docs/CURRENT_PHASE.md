# Current Phase

Status: `READY_FOR_REVIEW`

## Identity and scope

- Phase: `4C-2d3b1i6d1d5f1c4i3b`
- Name: `Historical Replay CLI Binding and Mixed-Provider No-Network Acceptance`
- Base Commit: `6ea6c3720f2e30e2dc0d1d13466193e8a4658ee0`
- Branch: `review/4c-2d3b1i6d1d5f1c4i3b-historical-replay-cli-acceptance`
- Formal branch: `feature/ver0.8-simulator`
- Approved PREPARE: `6fb5034042fe12327b7e8f9798fd8d77331ac1e7`

Allowed Files are exactly:

```text
scripts/cli/run_historical_replay.py
tests/test_cli_run_historical_replay.py
tests/test_historical_replay_mixed_provider_acceptance.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

Forbidden Files include every other path. In particular, do not modify existing
production modules, serializers, legacy CLIs, replay applications, repositories,
normalizers, migrations, schemas, package exports, or C4i3a fixtures.

## Corrected temporal provenance

```text
TEMPORAL_PROVENANCE_CORRECTION:
APPLIED

RUN_CONTEXT_STARTED_AT:
2026-08-30T15:25:00+00:00

TARGET_COMMIT_ID:
6ea6c3720f2e30e2dc0d1d13466193e8a4658ee0

TARGET_COMMIT_CREATED_AT:
2026-08-30T15:24:15+00:00

TARGET_COMMIT_TEMPORAL_ORDER:
PASS
```

The rejected PREPARE run start was not used. Test-controlled migration audit
timestamps use the corrected run start. After setup, the acceptance test installs a
fail-closed migration-clock sentinel for replay.

## CLI contract

Create `scripts/cli/run_historical_replay.py` with only the public functions
`build_parser`, `run`, and `main`. The parser has one required positional `Path`
argument, `request_path`, whose help is `Historical replay request JSON path`.

`run()` calls `run_historical_replay_request(request_path=arguments.request_path)`
exactly once. It owns no loader, SQLite, migration, repository, planning, capture,
acquisition, settlement, clock, or second replay path.

Success uses public `to_json_compatible` in an exact schema-v1 compact, sorted,
UTF-8-friendly JSON envelope followed by one newline. Expected application failures
catch exactly `(OSError, RuntimeError, TypeError, ValueError, sqlite3.Error)`, return
`1`, write one equivalent error envelope to stderr, and leave stdout empty. Success
returns `0` with stderr empty. Argparse retains its native `SystemExit` behavior.

## Mixed-provider acceptance contract

One test must run the normal public CLI/application path with both providers in the
same schema-v1 request. It reconstructs the exact C4i3a JRA and NAR captures from
unchanged repository evidence, writes them to test-temporary provider archives using
the formal migration runners and repositories, creates a test-temporary main database
with exact synthetic pre-race snapshots, and runs the existing C4g1 -> C4h4a -> C4h4b
composition without network access.

The synthetic prediction inputs are labeled `c4i3b_test_generated`. Exact identities
are JRA race `700`, entry IDs `1001..1013`, and NAR race `800`, entry IDs
`2001..2011`. Manifest race order is NAR then JRA. Canonical scheduled-start order is
therefore exercised by production.

Prediction timelines remain:

```text
JRA: 2025-09-12T23:50Z <= 23:55Z <= 2025-09-13T00:00Z <= 01:00Z <= 02:30Z
NAR: 2026-05-02T11:50Z <= 11:55Z <= 12:00Z <= 13:00Z <= 2026-05-03T03:00Z
```

Settlement cutoffs remain the exact official observed times:

```text
JRA: 2026-08-26T11:38:28.113891+00:00
NAR: 2026-08-27T15:41:31.026438+00:00
```

The strategy allows only `単勝`, one candidate/bet, formation selection,
generator-rank sorting, fixed stake `100`, and budget `100` per race. It must produce:

```text
STRATEGY_ID: RuleBasedBetStrategy:e05f27f5729da71b
STRATEGY_CONFIG_HASH: e05f27f5729da71b9d057aebe9b60c70c98ee2d7877266cdf6f392e65bb9e60e
JRA: entry 1001 / horse 1 / stake 100
NAR: entry 2001 / horse 1 / stake 100
```

Both bets lose. The exact summary has two settled races and bets, investment `200`,
payout `0`, profit `-200`, zero ROI/hit rates, maximum drawdown `200`, and only the
corresponding `単勝` summary.

The test must prove the network and replay-clock sentinels remain unused; temporary
archives and C4i3a fixture bytes remain unchanged; both official results and `単勝`
payout publications persist; and exactly the intended plan selections/stakes settle.

## Implementation result

```text
C4I3A:
FORMALLY_VERIFIED

C4I3B_IMPLEMENTATION:
COMPLETE_PENDING_INDEPENDENT_REVIEW

CLI_THIN_APPLICATION_CALL:
PASS

OUTPUT_CONTRACT:
PASS

ERROR_EXIT_CONTRACT:
PASS

MIXED_PROVIDER_ACCEPTANCE:
PASS

JRA_SETTLEMENT:
PASS

NAR_SETTLEMENT:
PASS

EXPECTED_BETS:
PASS

EXPECTED_SUMMARY:
PASS

NO_NETWORK_GUARD:
PASS

NO_CURRENT_CLOCK_DURING_REPLAY:
PASS

TEMP_JRA_ARCHIVE_UNCHANGED_BY_REPLAY:
PASS

TEMP_NAR_ARCHIVE_UNCHANGED_BY_REPLAY:
PASS

C4I3A_FIXTURES_UNCHANGED:
PASS

EXISTING_PRODUCTION_CHANGED:
NO

NEW_PRODUCTION_FILE_COUNT:
1

SCHEMA_CHANGED:
NO

MIGRATION_CHANGED:
NO

FIXTURE_CHANGED:
NO

AI_RUNTIME_CHANGED:
NO
```

## Required Tests

Run:

```text
python -m pytest tests/test_cli_run_historical_replay.py -q
python -m pytest tests/test_historical_replay_mixed_provider_acceptance.py -q
```

Then run the directly related historical replay request/application/SQLite runner,
portable fixture, C4g1, C4h4a, C4h4b, historical snapshot repository, provider capture
repository, and persisted CLI suites discovered in the formal tree. Finally run
`python -m pytest -q`, `git diff --check`, and the static five-file scope/ownership
checks. Remote GitHub Actions `Tests / pytest (3.12)` must pass.

Actual local results:

```text
DEDICATED_CLI_TESTS:
13 passed

DEDICATED_ACCEPTANCE_TESTS:
1 passed

RELATED_TESTS:
183 passed, 299 subtests passed

FULL_SUITE:
3125 passed, 2506 subtests passed

GIT_DIFF_CHECK:
PASS

STATIC_SCOPE_CHECK:
PASS

REMOTE_CI:
REQUIRED_BEFORE_READY_REPORT
```

## Stop Condition

Stop fail-closed on a moved formal head, a required sixth path or existing production
change, temporal/strategy/bet/summary mismatch, replay clock or network access, archive
or fixture mutation, schema/migration/C4i3a change, or failing remote CI that would
require scope expansion. After one review commit and successful review-branch CI, stop
for independent review. Formal integration and C4i3b successor work are not authorized.
