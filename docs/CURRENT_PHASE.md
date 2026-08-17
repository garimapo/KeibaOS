# Current Phase

## Status

READY_FOR_REVIEW

## Phase

`4C-2d3b1i6d1d5f1c4a` — JRA accessU target-horse history resolution.

Formal base: `0b8a5b3b590478ac880d27c4ecf387f5136c4806`.

Approved prepare: `019b6bf839d009baa76798fa388017fed56994c1`.

Review branch: `review/4c-2d3b1i6d1d5f1c4a-jra-accessu-history-resolution`.

## Allowed Files

```text
scripts/simulation/jra_target_race_input_source.py
tests/test_jra_target_race_input_source.py
scripts/simulation/jra_target_horse_history_resolution.py
tests/test_jra_target_horse_history_resolution.py
scripts/simulation/repositories/sqlite_jra_official_response_capture_repository.py
tests/test_sqlite_jra_official_response_capture_repository.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Implemented Contract

`JRATargetRaceSourceCollection` now retains one frozen/slotted
`JRATargetHorseHistoryLocator` per ascending target entry. The locator is constructed
only from the already selected row-local accessD horse anchor, resolves relative hrefs
against the official host, canonicalizes only an accessU URL, and proves race, entry,
horse, and accessU URL coherence. No provider URL enters neutral source-record values
and no later accessD HTML reparse or horse-ID-to-URL synthesis is possible.

`SQLiteJRAOfficialResponseCaptureRepository.load_latest_horse_profile_history_supplied_response`
performs an exact canonical accessU, schema-v1 horse-profile lookup with an inclusive,
explicit UTC-normalized observation bound. It returns the unique latest eligible capture,
returns `None` for no eligible capture, and fails closed for same-time ambiguity or
corrupt requested-family storage. It does not query other JRA page families and does not
change schema or indexes.

The pure injected
`resolve_jra_target_horse_history_response(...)` boundary validates exact JRA target
lineage and locator binding, calls its provider exactly once with the caller's unchanged
`observed_at_not_after`, and accepts only the locator's exact canonical accessU response
observed no later than that bound and the scheduled start. `None` becomes a dedicated
unavailable error; provider exceptions propagate unchanged. It owns no repository,
HTTP, live capture, clock, filesystem, database, snapshot, or historical collector work.

The effective replay cutoff remains a later orchestration responsibility. This phase
does not substitute scheduled start for the explicit lookup bound, backdate evidence,
or introduce a live fallback.

## Required Verification

Run dedicated target-source, resolver, and repository suites; related JRA
identity/capture/discovery/collector/source/snapshot regressions; full pytest; static
public-surface and forbidden-dependency checks; and `git diff --check`. No real trusted
capture, schema/index/migration, package-root export, snapshot orchestration, or bridge
change is authorized.

The exact related command is the eleven-suite historical/JRA/source/snapshot selection
recorded in `LATEST_CODEX_REPORT.md`; its fresh correction-run result is `121 passed`.

## Stop Condition

Stop after one review commit is pushed for independent review.
