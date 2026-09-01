# Historical Replay

## Purpose

KeibaOS Ver0.8 replays exact persisted historical prediction inputs through the real
prediction, strategy, fixed-stake planning, archived official settlement, and summary
boundaries. It is designed for deterministic research and audit, not for reconstructing
missing evidence or promising profitable results.

## Prerequisites

- Python 3.12 or later with `requirements.txt` installed.
- A main SQLite database containing the exact audited `HistoricalInputSnapshot` records
  named by the request.
- A separate archived capture database for each represented provider, containing the
  exact result and payout capture IDs named by the request.
- Exact run, strategy, budget, snapshot, capture, and cutoff values retained as part of
  the replay audit record.

The replay application applies current migrations to the main database. Capture
archives are existing replay inputs and are opened read-only; operators must not
hand-edit either schema.

## Trust Boundary

The request is an identity-and-configuration manifest, not the historical evidence
itself. A valid request must bind:

- an exact persisted snapshot natural identity for every race;
- the internal race ID as a cross-check only;
- one run context and one deterministic strategy/allocation configuration;
- explicit per-race budgets;
- exact provider-specific result and payout capture IDs; and
- a separate settlement cutoff for each race.

The replay CLI does not acquire historical source pages, create snapshots, discover a
latest capture, search another provider, or repair missing data. Exact referenced state
must already exist. Missing, malformed, inconsistent, unsupported, or non-final evidence
fails closed.

## Request File and Relative Paths

The request is strict UTF-8 JSON with `schema_version` equal to integer `1`. Duplicate
keys, comments, trailing data, non-finite numbers, missing keys, and unknown keys are
invalid.

Relative `database_path` and `capture_archives` values are anchored to the request
JSON's parent directory. They are not anchored to the shell's current directory. The
request file may live anywhere; its referenced files do not need to be inside the
repository.

The repository template is
[`examples/historical_replay_request.v1.example.json`](../examples/historical_replay_request.v1.example.json).

> The example is a schema template only. Placeholder capture IDs are not official
> evidence. Replace every `REPLACE_WITH_...` value with an exact audited value before
> replay. Successful schema parsing does not prove that a referenced database, archive,
> snapshot, or capture exists or is trustworthy.

## `database_path`

`database_path` is a non-empty path to the main SQLite database. It must contain the
historical input snapshots identified by `races`. During replay this same database owns
the immutable plan, normalized result/payout, and settlement reads.

## `capture_archives`

`capture_archives` is a non-empty object with supported keys:

- `JRA/jra_official`
- `NAR/nar_official`

Every provider represented by a race's exact snapshot identity needs its corresponding
archive. An unused configured supported archive is allowed, but the application opens
only represented providers. Archive paths may be the same path, although normal
operation keeps provider archives distinct. Each archive is opened at SQLite connection
time with read-only mode and an additional `query_only` check.

## `run_context`

`run_context` has exactly:

- `run_id`: stable, non-empty run identity;
- `dataset_id`: dataset identity shared by every race snapshot;
- `started_at`: timezone-aware ISO-8601 run start;
- `target_commit_id`: exact source commit used for the replay.

The request loader does not substitute the current clock or create a completion time.

## `strategy`

The supported request strategy is `RuleBasedBetStrategy`. Its exact fields are:

- `strategy_name`
- `allowed_bet_types`
- `max_bet_count`
- `selection_style` (`box` or `formation`)
- `min_combination_score`
- `max_candidates`
- `sort_condition`
- `allocation_policy`

Supported formal bet types are `単勝`, `馬連`, `ワイド`, and `3連複`. The fixed-stake
allocation policy is `fixed_stake_per_recommendation`, policy version string `"1"`,
with one positive 100-yen-multiple `stake_amount`. The public identity builder derives
the strategy/config hash deterministically; callers do not supply a hash.

## `budgets_by_race_id`

`budgets_by_race_id` maps canonical positive integer strings to exact objects containing
only `total_amount`. Each amount is a non-negative multiple of 100. Budget race-ID
coverage must exactly equal the internal race IDs in `races`. A zero budget is valid
and may produce an immutable empty plan.

## `races` and `snapshot_identity`

`races` is a non-empty array. Each race has exactly:

- `snapshot_identity`
- `internal_race_id`
- `settlement_information_cutoff`
- `result_capture_id`
- `payout_capture_catalog_by_bet_type`

`snapshot_identity` has exactly `dataset_id`, `organization`, `source_system`,
`external_race_id`, and `captured_at`. Supported provider pairs are exact and
case-sensitive: `JRA / jra_official` and `NAR / nar_official`. The loader preserves
manifest order, while replay executes races canonically by scheduled start and internal
race ID after exact snapshot loading.

`payout_capture_catalog_by_bet_type` may contain only the four formal bet types and may
be empty. After planning, replay derives purchased bet types from the immutable returned
plans and requires the corresponding catalog subset. Unused supported catalog entries
are ignored. The same exact capture ID may serve result and multiple payout keys.

## Prediction Cutoff vs Settlement Cutoff

The historical snapshot's prediction `information_cutoff` bounds evidence that could
influence prediction and purchase planning. Evidence must be available, observed, and
captured within the formal causal timeline before the race's scheduled start.

`settlement_information_cutoff` is a separate, later request value that bounds which
archived official result and payout captures may be consumed. Later settlement evidence
is expected and cannot flow backward into `PredictionPipeline`, `BetStrategy`, stake
allocation, or the immutable plan.

## Running the CLI

```bash
python -m scripts.cli.run_historical_replay <request_path>
```

The CLI loads the request exactly once and delegates to the SQLite historical replay
application. It does not own another loader, repository, prediction, capture, or
settlement path.

## Success Output

Success exits `0`, writes nothing to stderr, and writes exactly one compact, sorted,
UTF-8 JSON line to stdout:

```json
{"schema_version":1,"status":"ok","summary":{"...":"SimulationSummary fields"}}
```

`Decimal` rates are fixed-point JSON strings. A rate with no denominator is `null`.
The summary includes race/status counts, bet counts, investment, payout, profit, ROI,
hit rates, maximum drawdown, and by-bet-type summaries.

## Expected Errors and Exit Codes

Expected filesystem, request, application, and SQLite failures exit `1`, leave stdout
empty, and write one compact JSON line to stderr:

```json
{"error":{"message":"<message>","type":"<exception type>"},"schema_version":1,"status":"error"}
```

If an exception message is empty, the exception type name is used. Argument parsing is
owned by argparse: invalid CLI syntax exits `2`, while `--help` exits `0`.

## Archived No-Network Replay

The normal replay path reads persisted snapshots and local SQLite capture archives.
It performs no HTTP/HTTPS acquisition, DNS-dependent discovery, live capture creation,
or provider fallback. Exact portable JRA/NAR evidence and mixed-provider acceptance
demonstrate the application boundary without requiring network availability.

This does not mean every possible historical race is bundled or automatically
available. Operators are responsible for retaining lawful, audited source evidence and
its exact identities before replay.

## Fail-Closed Conditions

Replay stops without a final summary when, among other conditions:

- request JSON or cross-field identity is invalid;
- an exact snapshot is missing or contradicts the request binding;
- planning fails or returns an incoherent batch;
- a purchased bet type lacks an exact payout capture ID;
- an archive cannot be opened read-only;
- an exact capture is missing, late, corrupt, for another race/provider, or malformed;
- official result/payout evidence is non-final, incomplete, exceptional, or unsupported;
- persisted plan/result/payout identities conflict; or
- final settlement contains any non-final race state.

Earlier immutable writes may remain as an auditable durable prefix after failure. The
application does not delete, compensate, retry, or misreport that prefix as a completed
summary.

## Reproducibility Checklist

Retain and independently verify:

1. the exact target commit and request JSON;
2. the main database containing every named snapshot natural identity;
3. every represented provider archive and exact capture ID;
4. snapshot evidence timestamps and prediction cutoff;
5. run, strategy, allocation policy, and race budgets;
6. result/payout capture observation times and settlement cutoffs;
7. immutable persisted plan identity and purchase order;
8. Python/dependency environment and successful test/CI state; and
9. the deterministic CLI JSON output.

## Supported Capabilities and Non-Claims

Ver0.8 supports deterministic replay for identical audited inputs, configuration, and
evidence; future-information isolation; fixed-stake allocation; immutable plans;
archived official JRA/NAR normal settlement; official payout-per-100 arithmetic;
deterministic metrics/JSON; and fail-closed validation.

It does not guarantee profit, 120% ROI, calibrated probabilities, or a demonstrated
strategy edge. Prediction-time market-odds EV is formal only for `単勝`;
`combination_score` is not true market EV. Ver0.8 does not claim complete provider-wide
historical coverage, every exceptional settlement state, automatic historical-input
construction, live automated betting, or active external AI/LLM augmentation. External
AI signals remain disabled in the deterministic baseline and are post-Ver0.8 work.
