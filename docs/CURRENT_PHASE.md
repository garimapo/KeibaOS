# Current Phase

## Status

READY_FOR_REVIEW

## Phase

`4C-2d3b1i6d1d5e1` — JRA historical input-source collection.

Formal base: `c8008cdc15903b305219066c3b10b35e1255767f`.

Approved design: `7724e7a77017896eb6cb164672c63ec2af8b21b1`.

Review branch: `review/4c-2d3b1i6d1d5e1-jra-history-collection`.

## Allowed Files

```text
scripts/simulation/jra_historical_input_source_collection.py
tests/test_jra_historical_input_source_collection.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Public Contract

The new module exports only two callable provider Protocols, frozen/slotted
`JRAHistoricalSourceCollection`, its validation/unsupported error hierarchy, and:

```python
collect_jra_historical_input_source_records(
    *,
    target_track_record: HistoricalInputSourceRecord,
    target_entry_record: HistoricalInputSourceRecord,
    horse_history_response: JRASuppliedOfficialResponse,
    race_result_response_provider: JRAHistoricalRaceResultResponseProvider,
    final_win_odds_response_provider: JRAHistoricalFinalWinOddsResponseProvider,
) -> JRAHistoricalSourceCollection
```

The result carries exact target race/entry IDs plus ordered source records. Its direct constructor validates canonical
JRA race identity, exact race-scoped entry identity, canonical positive entry suffix, and reconstruction through
`build_jra_external_entry_id`; every contained record must match those target IDs.

## Required Behavior

Discovery is called exactly once and supplies the sole complete event sequence. Before a provider is called, any
`NON_JRA_ACTUAL_START` or `UNSUPPORTED_ACTUAL_START` aborts the whole collection. `PROVEN_NON_START` emits no record.
Zero actual starts use only public absence projection, with zero result/odds provider calls.

Every JRA actual start follows: exact discovery reference → injected accessS response bound to exact URL/race → formal
locator extraction → injected accessO response bound to that exact locator → existing JRA past-race normalizer. Output
order remains discovery newest-to-oldest; there is no history cap. Result reuse is per call by JRA race identity;
final-odds reuse is per call by request-identity SHA-256.

AccessU retains formal causality. Every injected accessS/accessO observation must be no later than target scheduled
start, with no timestamp change. The return is all-or-nothing. Existing
`validate_historical_input_source_record_set(...)` is called exactly once before result construction.

Exception translation is exact: discovery and normalizer validation errors map to collection validation; their
unsupported errors map to collection unsupported; locator/projection/neutral-validation errors map to collection
validation; provider-raised exceptions propagate unchanged. No broad exception catch.

## Required Tests

Cover public signatures/domain; direct constructor lineage failures; one discovery call; zero/transfer projection and
zero provider calls; ordering, binding, locator derivation, dedup, both causality checks, exact error translation,
provider propagation, pre-provider mixed rejection, no partial return, one neutral validation, no history cap, purity,
no package export, related JRA/NAR/neutral regressions, and the full suite.

## Verification

The correction suite directly exercises the real accessS/accessO response binding helpers for wrong canonical URL,
wrong JRA race identity, wrong response type, wrong final-odds locator, and both target-start cutoffs. It also pins
the complete exception-translation matrix, unchanged provider-exception propagation, and a six-start sequence with
no source-acquisition cap. Related JRA discovery/absence/normalizer/locator/identity/capture/archive,
provider-neutral source/snapshot/builder, and NAR historical-source regressions pass. Full-suite and final static
verification are recorded in `LATEST_CODEX_REPORT.md` before review publication.

## Boundaries and Stop Condition

No HTTP/live capture, archive, repository, database, migrations, schemas, snapshot construction, Predictor, NAR↔JRA
bridge, fallback, real capture, or package-root export. On success, commit exactly one review commit:
`feat: collect JRA historical input source records`; push only the review branch and stop for independent review.
