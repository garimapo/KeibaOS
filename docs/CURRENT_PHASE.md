# Current Phase

## Status

READY_FOR_REVIEW

## Phase

`4C-2d3b1i6d1d5f1c3` — JRA accessD target-source normalization.

Formal base: `3d15d31a68500d05b224ffead60ee9a799064342`.

Approved prepare: `e2241f65a629858dc50b7966a82c627468998b27`.

Review branch: `review/4c-2d3b1i6d1d5f1c3-jra-accessd-target-source`.

## Allowed Files

```text
scripts/simulation/jra_target_race_input_source.py
tests/test_jra_target_race_input_source.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Implemented Contract

`normalize_jra_target_race_input_source_records(*, response)` is a pure accessD
normalizer. It accepts only exact canonical `JRASuppliedOfficialResponse` accessD
evidence, validates URL and visible race identity coherence, strict-decodes CP932, and
returns frozen/slotted `JRATargetRaceSourceCollection` values containing exactly one
track and ascending horse-number entry records.

For every fully supported normal runner, the normalizer creates one each of neutral
`entry`, `jockey`, and `odds_win` records. The stable horse identity comes only from
the row-local accessU anchor; the entry ID is rebuilt from the accessD URL race identity
and direct horse number. All records use one raw-byte response SHA, the actual observed
timestamp, no available/request identity, and `provider_record_id=None`.

The flat ordering is exactly `track`, then `entry`, `jockey`, and `odds_win` for each
ascending horse number. It builds the complete set in memory and calls the established
neutral source validator exactly once before collection construction. There is no row
skip or partial return.

The public collection constructor independently requires exact neutral source records
throughout the flat tuple, one JRA/`jra_official` family and target race, exact
entry/jockey/odds grouping, matching entry IDs, and matching odds/entry horse numbers.
It rejects extra, unmatched, foreign-family, and forged direct-construction records.

Missing/duplicate/malformed structure, anchors, values, identity contradictions, and
neutral conflicts are `JRATargetRaceSourceValidationError`. A structurally unique direct
odds value that is blank, placeholder, non-numeric, non-finite, zero, or negative is
`JRATargetRaceSourceUnsupportedError`. This does not establish non-runner semantics:
`ACCESSD_NON_RUNNER_SEMANTICS_READY = NO` remains frozen.

The normalizer requires `response.observed_at <= scheduled_start_at`; it preserves the
response timestamp and leaves snapshot-cutoff eligibility downstream. It owns no HTTP,
archive, repository, database, filesystem, clock, snapshot, Predictor, or bridge work.

## Required Verification

Run the dedicated target-source suite; related historical-source/evidence/snapshot
builder and JRA identity/capture regressions; full pytest; static public-surface and
forbidden-dependency checks; and `git diff --check`. No real capture, schema/migration,
package-root export, target acquisition, snapshot assembly, Predictor, or bridge change
is authorized.

## Stop Condition

Stop after one review commit is pushed for independent review.
