# Current Phase

## Status

READY_FOR_REVIEW

## Phase

`4C-2d3b1i6d1d5f1c4b` — JRA historical accessS/accessO causal archive resolution.

Formal base: `8660f9f8ffdea03b0f7badc31429d8b572e7cfa0`.

Approved prepare: `c3bcfd5cddd1fbc65b6d2e486d6ef7db1f3dd569`.

Review branch: `review/4c-2d3b1i6d1d5f1c4b-jra-historical-causal-resolution`.

## Allowed Files

```text
scripts/simulation/jra_historical_input_source_collection.py
scripts/simulation/repositories/sqlite_jra_official_response_capture_repository.py
tests/test_jra_historical_input_source_collection.py
tests/test_sqlite_jra_official_response_capture_repository.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Implemented Contract

`collect_jra_historical_input_source_records(...)` now requires one explicit,
timezone-aware `observed_at_not_after` value. It rejects a bound after the target
scheduled start and rechecks the supplied accessU response before discovery. The exact
caller object is forwarded unchanged to every injected accessS and accessO provider;
each supplied response must be observed at or before the same inclusive bound. The
collector does not substitute the scheduled start as a lookup cutoff.

The collector continues to perform discovery exactly once, rejects non-JRA and
unsupported starts before response providers, preserves deterministic accessS and
accessO in-call caches, and retains the all-or-nothing/no-cap policy. A provider return
of `None` now raises `JRAHistoricalSourceCollectionUnavailableError`. Provider-raised
repository integrity, validation, and other errors propagate unchanged.

`SQLiteJRAOfficialResponseCaptureRepository` now has two family-specific latest
lookups: `load_latest_race_result_supplied_response(...)` and
`load_latest_final_win_odds_supplied_response(...)`. They use exact stable requested
identity plus an inclusive explicit cutoff, select the sole latest eligible row, and
reconstruct it before enforcing its complete stored capture family/domain. Candidate SQL
intentionally does not filter corrupt family metadata away as a false `None`; tied or
corrupt selected rows fail with `RepositoryDataIntegrityError`. A normal no-result is
the sole `None` case.

No schema, migration, index, package-root export, live capture, snapshot orchestration,
or real trusted capture change is part of this phase. Later race-level orchestration
remains responsible for deriving a replay cutoff compatible with snapshot causal inputs.

## Required Verification

Run the collector and repository dedicated suites; the listed JRA/accessU/discovery/
past-race/final-odds/capture/source/snapshot regressions; the full pytest suite; static
public-surface, forbidden-dependency, and broad-catch checks; `git diff --check`; and
final clean-status verification.

## Stop Condition

Stop after exactly one pushed review commit for independent review. Do not begin
race-level source union or snapshot assembly.
