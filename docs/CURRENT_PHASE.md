# Current Phase

Status: `DRAFT_FOR_REVIEW`

## Identity and authorized scope

- Phase: `4C-2d3b1i6d1d5f1c4i3b`
- Name: `Historical Replay CLI Binding and Mixed-Provider No-Network Acceptance PREPARE`
- Formal base: `6ea6c3720f2e30e2dc0d1d13466193e8a4658ee0`
- Formal tree: `89edf702347a9be3a13c725fce5a7180b13c558d`
- Formal branch: `feature/ver0.8-simulator`
- Prepare branch: `review/4c-2d3b1i6d1d5f1c4i3b-historical-replay-cli-acceptance-prepare`

This PREPARE is documentation-only. Allowed changed files are exactly:

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

```text
C4I3A:
FORMALLY_VERIFIED

C4I3A_FORMAL_COMMIT:
6ea6c3720f2e30e2dc0d1d13466193e8a4658ee0

C4I3B_IMPLEMENTATION_AUTHORIZATION:
NO
```

## CLI architecture

The future module is exactly `scripts/cli/run_historical_replay.py`. Its public
functions and signatures follow the existing persisted-simulation CLI:

```python
def build_parser() -> argparse.ArgumentParser: ...

def run(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int: ...

def main() -> int: ...
```

There is no package-root export. The parser has exactly one required positional `Path`
argument named `request_path`, with help text `Historical replay request JSON path`.
There are no duplicate strategy, database, capture, race, cutoff, budget, output, clock,
or network flags.

`run()` parses once, calls the existing formal boundary exactly once, and returns only
the CLI exit code:

```python
run_historical_replay_request(
    request_path=arguments.request_path,
)
```

The CLI does not call the C4i1 loader, SQLite runner, planning, archives, C4h4a, C4h4b,
or repositories directly. `main()` returns `run()` and the module guard raises
`SystemExit(main())`.

```text
CLI_ARCHITECTURE:
ONE_POSITIONAL_REQUEST_PATH_THIN_EXISTING_APPLICATION_CALLER

CLI_ORCHESTRATION_POLICY:
NO_SECOND_REPLAY_PATH
```

## Output contract

Serializer decision is option A: use the existing public common
`scripts.simulation.serialization.to_json_compatible` for the returned exact
`SimulationSummary`. Inspection confirmed exact equality with the current
persisted-simulation CLI summary payload for populated, empty, and multi-bet-type
summaries. No serializer extraction, legacy CLI refactor, or duplicated summary mapper
is authorized.

Success is exactly one stdout line and exit `0`:

```json
{"schema_version":1,"status":"ok","summary":{}}
```

The displayed empty object is shorthand only; `summary` contains every exact
`SimulationSummary` field:

```text
strategy_id
strategy_name
strategy_config_hash
race_count
settled_race_count
unsettled_race_count
no_bet_race_count
void_race_count
error_race_count
unsupported_race_count
bet_count
settled_bet_count
settled_purchase_race_count
hit_bet_count
hit_race_count
investment
payout
profit
roi
bet_hit_rate
race_hit_rate
maximum_drawdown
by_bet_type
```

Each `by_bet_type` object contains exactly `bet_type`, `bet_count`,
`settled_bet_count`, `hit_bet_count`, `investment`, `payout`, `profit`, `roi`, and
`bet_hit_rate`. Decimal values are fixed-point strings; absent rates are JSON `null`.

Encoding is exactly:

```python
json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
```

followed by exactly one `\n`. Recursive key sorting, including `by_bet_type`, makes
identical inputs byte-deterministic.

```text
OUTPUT_SERIALIZER_POLICY:
REUSE_PUBLIC_TO_JSON_COMPATIBLE

OUTPUT_CONTRACT:
SCHEMA_V1_COMPACT_SORTED_UTF8_FRIENDLY_JSON_ONE_LINE
```

## Error and exit contract

The future CLI catches exactly the same expected boundary tuple as the persisted CLI:

```python
except (OSError, RuntimeError, TypeError, ValueError, sqlite3.Error) as error:
```

Expected failure is exit `1`, no stdout, and exactly one stderr line:

```json
{"error":{"message":"<str(error) or type name>","type":"<exact type name>"},"schema_version":1,"status":"error"}
```

There is no expected-error traceback, fallback, retry, `Exception`, or `BaseException`
catch. Argparse help and usage errors remain argparse-owned `SystemExit` behavior.

```text
ERROR_EXIT_CONTRACT:
SUCCESS_0_STDOUT_EXPECTED_FAILURE_1_STDERR_ARGPARSE_NATIVE
```

## Mixed-provider acceptance architecture

The future acceptance performs one normal executable-path run:

```text
repository exact fixture bytes and strict provenance
-> exact formal JRA/NAR capture reconstruction
-> test-temporary formal capture archives
-> test-temporary main database and exact snapshots
-> schema-v1 manifest beside those databases
-> public historical replay CLI run(...)
-> run_historical_replay_request(...)
-> existing SQLite replay runner
-> C4g1 planning/persistence
-> C4h4a JRA and NAR official acquisition
-> C4h4b final settlement
-> exact stdout SimulationSummary payload
```

The test locates evidence only from
`Path(__file__).resolve().parents[1] / "tests/fixtures/historical_replay/official"`.
It strictly loads `provenance.json` with duplicate-key and non-finite-value rejection,
reads both bodies as bytes, and rechecks exact lengths, SHA-256 digests, encodings,
metadata, and complete capture IDs before and after execution. It reconstructs the
existing exact `JRAOfficialResponseCapture` and `NAROfficialResponseCapture` and never
changes fixture bytes.

```text
JRA_RESULT_AND_PAYOUT_CAPTURE:
jra-capture-v1:2d8fbee2df4a201923a49a48e02de3f6837293e0166a1347e30ef3f0b0aad296

NAR_RESULT_AND_PAYOUT_CAPTURE:
nar-capture-v1:d6692261a54c1038a5ffd804ae79edda9ca543cb5d78f37c41ffaeefe281013b
```

The same exact capture supplies result plus the required `単勝` payout for its provider.
No URL, latest, nearest, race-only, alternate-provider, name, or row-order lookup exists.

## Temporary SQLite ownership

All files live under one `tmp_path`. Main setup creates the established prerequisite
test `races` and `horses` tables, inserts race IDs `700` and `800` plus disjoint entries,
calls `apply_migrations`, constructs one
`SQLiteHistoricalInputSnapshotRepository`, saves both snapshots, and closes the setup
connection. The normal runner later opens `main.sqlite3` and reapplies migrations
idempotently.

JRA archive setup:

1. Open temporary `jra_official.sqlite3` writable.
2. Call `apply_jra_capture_schema_migrations(connection)`.
3. Construct `SQLiteJRAOfficialResponseCaptureRepository(connection=connection)`.
4. Call `save_capture(capture=reconstructed_jra_capture)` once.
5. Close the setup connection.

NAR archive setup:

1. Open temporary `nar_official.sqlite3` writable.
2. Call `apply_capture_schema_migrations(connection)` from the NAR runner.
3. Construct `SQLiteNAROfficialResponseCaptureRepository(connection=connection)`.
4. Call `save_capture(capture=reconstructed_nar_capture)` once.
5. Close the setup connection.

Setup connections are test-owned and always closed. Production later opens represented
archives only through its existing hard read-only URI plus verified `query_only`
boundary. It performs no archive migration or save.

The manifest lives beside the databases and uses only relative paths:

```text
database_path = main.sqlite3
capture_archives[JRA/jra_official] = jra_official.sqlite3
capture_archives[NAR/nar_official] = nar_official.sqlite3
```

```text
PORTABLE_FIXTURE_TO_TEMP_ARCHIVE_BINDING:
EXACT_RECONSTRUCTION_DEDICATED_MIGRATIONS_EXACT_REPOSITORY_SAVE_THEN_READ_ONLY_RUNNER
```

## Historical input source and causality

No official prediction snapshot accompanies the settlement fixtures. The acceptance
therefore constructs deterministic test prediction inputs through the existing formal
immutable domain types and saves them through the formal SQLite repository. Provenance
is explicitly labeled `c4i3b_test_generated`, uses
`https://c4i3b.example.test/...`, and hashes fixed test tokens. It does not claim to be
C4i3a official evidence.

```text
TEST_GENERATED_SNAPSHOT_DATA:
PRE_RACE_PREDICTION_INPUT_ONLY

EXACT_C4I3A_OFFICIAL_BYTES:
POST_RACE_RESULT_AND_PAYOUT_ONLY
```

Exact provider/crosswalk identities are:

```text
JRA:
organization = JRA
source_system = jra_official
external_race_id = jra:race:2025:06:04:03:04
internal_race_id = 700
race_entry_ids 1001..1013 map to horse numbers 1..13

NAR:
organization = NAR
source_system = nar_official
external_race_id = nar:20260503:31:1
internal_race_id = 800
race_entry_ids 2001..2011 map to horse numbers 1..11
```

JRA external entry IDs use the existing JRA identity builder. NAR uses exact
`nar:20260503:31:1:entry:<horse-number>` IDs.

Prediction timelines are frozen exactly:

```text
JRA:
available_at 2025-09-12T23:50:00+00:00
observed_at 2025-09-12T23:55:00+00:00
captured_at 2025-09-13T00:00:00+00:00
information_cutoff 2025-09-13T01:00:00+00:00
scheduled_start_at 2025-09-13T02:30:00+00:00

NAR:
available_at 2026-05-02T11:50:00+00:00
observed_at 2026-05-02T11:55:00+00:00
captured_at 2026-05-02T12:00:00+00:00
information_cutoff 2026-05-02T13:00:00+00:00
scheduled_start_at 2026-05-03T03:00:00+00:00
```

Both satisfy `available_at <= observed_at <= captured_at <= information_cutoff <=
scheduled_start_at`.

Settlement remains a separate post-race timeline. Each manifest cutoff equals the exact
official capture observation:

```text
JRA: 2026-08-26T11:38:28.113891+00:00
NAR: 2026-08-27T15:41:31.026438+00:00
```

No official response is backdated. Test setup fixes the main migration audit timestamp
source at `2026-08-28T00:00:00+00:00`; neither replay logic nor expected results depend
on the wall clock.

```text
CAUSALITY_CHECK:
PASS_BY_CONSTRUCTION_WITH_SEPARATE_PRE_RACE_SYNTHETIC_AND_POST_RACE_OFFICIAL_TIMELINES
```

## Deterministic strategy, bets, and summary

Both snapshots contain every official horse number, no past-race rows, equal win odds
`2.0`, and complete test-generated provenance. The exact strategy is:

```json
{"strategy_name":"RuleBasedBetStrategy","allowed_bet_types":["単勝"],"max_bet_count":1,"selection_style":"formation","min_combination_score":0.0,"max_candidates":1,"sort_condition":"generator_rank","allocation_policy":{"policy_name":"fixed_stake_per_recommendation","policy_version":"1","parameters":{"stake_amount":100}}}
```

Each budget is `100`. Equal pre-race scores cause the existing internal-entry-ID
tie-break to select exactly:

```text
JRA: 単勝 entry 1001 / horse 1 / stake 100
NAR: 単勝 entry 2001 / horse 1 / stake 100
```

This rule is fixed without settlement knowledge. Horse 1 loses both exact official
races. The acceptance therefore exercises both normal result and required payout paths
without duplicating C4i3a all-four-bet-type parser coverage. `NO BET` remains a valid
general outcome but is not expected here.

```text
STRATEGY_ID:
RuleBasedBetStrategy:e05f27f5729da71b

STRATEGY_CONFIG_HASH:
e05f27f5729da71b9d057aebe9b60c70c98ee2d7877266cdf6f392e65bb9e60e
```

Exact summary assertions are:

```text
race_count=2
settled_race_count=2
unsettled_race_count=0
no_bet_race_count=0
void_race_count=0
error_race_count=0
unsupported_race_count=0
bet_count=2
settled_bet_count=2
settled_purchase_race_count=2
hit_bet_count=0
hit_race_count=0
investment=200
payout=0
profit=-200
roi=Decimal("0")
bet_hit_rate=Decimal("0")
race_hit_rate=Decimal("0")
maximum_drawdown=200
```

`by_bet_type` contains only `単勝`: counts `2/2/0`, investment `200`, payout `0`,
profit `-200`, ROI `0`, and hit rate `0`.

## Complete schema-v1 request shape

The future test writes `historical_replay.json` below. Races are deliberately NAR then
JRA so production must establish canonical scheduled-start order.

```json
{
  "schema_version": 1,
  "database_path": "main.sqlite3",
  "capture_archives": {
    "JRA/jra_official": "jra_official.sqlite3",
    "NAR/nar_official": "nar_official.sqlite3"
  },
  "run_context": {
    "run_id": "c4i3b-mixed-provider-run-v1",
    "dataset_id": "c4i3b-mixed-provider-dataset-v1",
    "started_at": "2026-08-28T00:00:00+00:00",
    "target_commit_id": "6ea6c3720f2e30e2dc0d1d13466193e8a4658ee0"
  },
  "strategy": {
    "strategy_name": "RuleBasedBetStrategy",
    "allowed_bet_types": ["単勝"],
    "max_bet_count": 1,
    "selection_style": "formation",
    "min_combination_score": 0.0,
    "max_candidates": 1,
    "sort_condition": "generator_rank",
    "allocation_policy": {
      "policy_name": "fixed_stake_per_recommendation",
      "policy_version": "1",
      "parameters": {"stake_amount": 100}
    }
  },
  "budgets_by_race_id": {
    "700": {"total_amount": 100},
    "800": {"total_amount": 100}
  },
  "races": [
    {
      "snapshot_identity": {
        "dataset_id": "c4i3b-mixed-provider-dataset-v1",
        "organization": "NAR",
        "source_system": "nar_official",
        "external_race_id": "nar:20260503:31:1",
        "captured_at": "2026-05-02T12:00:00+00:00"
      },
      "internal_race_id": 800,
      "settlement_information_cutoff": "2026-08-27T15:41:31.026438+00:00",
      "result_capture_id": "nar-capture-v1:d6692261a54c1038a5ffd804ae79edda9ca543cb5d78f37c41ffaeefe281013b",
      "payout_capture_catalog_by_bet_type": {
        "単勝": "nar-capture-v1:d6692261a54c1038a5ffd804ae79edda9ca543cb5d78f37c41ffaeefe281013b"
      }
    },
    {
      "snapshot_identity": {
        "dataset_id": "c4i3b-mixed-provider-dataset-v1",
        "organization": "JRA",
        "source_system": "jra_official",
        "external_race_id": "jra:race:2025:06:04:03:04",
        "captured_at": "2025-09-13T00:00:00+00:00"
      },
      "internal_race_id": 700,
      "settlement_information_cutoff": "2026-08-26T11:38:28.113891+00:00",
      "result_capture_id": "jra-capture-v1:2d8fbee2df4a201923a49a48e02de3f6837293e0166a1347e30ef3f0b0aad296",
      "payout_capture_catalog_by_bet_type": {
        "単勝": "jra-capture-v1:2d8fbee2df4a201923a49a48e02de3f6837293e0166a1347e30ef3f0b0aad296"
      }
    }
  ]
}
```

There is no schema v2, pipeline field, CLI-only manifest, fixture descriptor, or second
race shape.

```text
REQUEST_DOCUMENT_REUSE:
EXACT_C4I1_SCHEMA_V1_ONLY
```

## Acceptance and no-network gates

The acceptance calls the future CLI `run()` with the real manifest, asserts exact exit,
streams, one-line JSON, summary, persisted plans/results/payouts, and unchanged fixture
bytes, then verifies only the temporary main database. Socket connection attempts are
guarded to fail. Static checks exclude HTTP/browser clients, capture acquisition/save in
the CLI, current-clock APIs, alternate SQLite orchestration, prediction construction,
settlement arithmetic, AI clients, and package exports.

```text
HTTP_PERFORMED:
NO
LIVE_CAPTURE_PERFORMED:
NO
SOURCE_ARCHIVE_REQUIRED:
NO
EXTERNAL_DEVELOPER_ARCHIVE_REQUIRED:
NO
CURRENT_CLOCK_REQUIRED:
NO
BACKDATED_LIVE_RESPONSE:
NO
NO_NETWORK_CONTRACT:
REPOSITORY_FIXTURES_AND_TEST_TEMPORARY_STATE_ONLY_SOCKET_GUARDED
```

## Future tests and implementation scope

CLI tests pin exact signatures, parser, one application call, common serialization,
JSON/streams/exits, caught classes, argparse behavior, and static thin ownership.
Acceptance tests pin strict fixtures, exact capture reconstruction, archive/main setup,
crosswalks, causality, relative paths, reverse manifest order, two exact plans, both
provider acquisitions, final summary, no network/current clock/developer archive, and
cleanup.

Future verification includes the two new suites, current CLI/request/runner/fixture,
C4g1/C4h4a/C4h4b, snapshot and capture repository suites, then the full suite and
`git diff --check`. Exact existing filenames must be revalidated at implementation.

Proposed implementation files are exactly:

```text
scripts/cli/run_historical_replay.py
tests/test_cli_run_historical_replay.py
tests/test_historical_replay_mixed_provider_acceptance.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

```text
PHASE_SPLIT_RECOMMENDATION:
ONE_PHASE

SPLIT_REASON:
EXISTING_PUBLIC_SERIALIZATION_AND_ORCHESTRATION_REMOVE_INDEPENDENT_REFACTOR_RISK

ARCHITECTURAL_BLOCKERS:
NONE

FUTURE_AI_SIGNAL_ARCHITECTURE:
OPTIONAL_AUDITABLE_AUGMENTATION_AFTER_VER0_8

AI_SIGNAL_USAGE_BASELINE:
DISABLED

CURRENT_C4I3B_AI_EFFECT:
NONE

C4I3B_IMPLEMENTATION_AUTHORIZATION:
PENDING_CHATGPT_ARCHITECTURE_REVIEW
```

Stop after publishing this PREPARE and remote CI success. Do not implement C4i3b,
formal-integrate PREPARE, or advance to another phase.
