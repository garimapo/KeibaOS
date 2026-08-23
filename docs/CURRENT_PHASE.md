# Current Phase

## Status

READY_FOR_REVIEW

## Phase

`4C-2d3b1i6d1d5f1c4c` — JRA causal target accessD resolution.

Formal base: `af0baed9050068ec6c2c5255ab82a12510968aa6`.

Approved prepare: `538bf53e6f0bde369e3f96335d77d348b83c021b`.

Review branch:
`review/4c-2d3b1i6d1d5f1c4c-jra-causal-target-accessd`.

## Implemented Contract

`resolve_jra_target_race_card_response(...)` is a pure injected replay boundary. It
validates the canonical external race ID, exact retained `jra-capture-v4:` ID, aware
`captured_at`, and both providers before any provider call. It loads the exact v4
race-selection capture once, requires `observed_at <= captured_at`, and uses only its
supplied-response conversion with formal c0b1 discovery to recover the exact accessD URL.
No race-ID lookup, CNAME or URL synthesis, site selection, opaque-tail inference, c0b3
call, live acquisition, archive write, or target-card reparse is present.

The resolver invokes the v3 provider once with the discovered locator and the unchanged
semantic `observed_at_not_after=captured_at` bound. It returns a frozen/slotted
`JRATargetRaceCardResolution` whose custom construction rechecks navigation and card
lineage, derives both capture IDs and the response digest from exact captures, retains the
caller-supplied `captured_at`, and exposes only the established
`JRASuppliedOfficialResponse` target-card bytes.

`captured_at` is the only c4c replay observation bound. Both v4 and v3 require
`observed_at <= captured_at`. `stored_at` remains capture audit metadata and an internal
timestamp invariant only: it is not a replay cutoff, selection key, tie-break, or proof
that archive persistence had completed. Captures with
`observed_at <= captured_at < stored_at` remain observation-eligible. C4c remains
pre-normalization, so downstream target normalization and snapshot assembly own the
scheduled-start guard `captured_at <= information_cutoff <= scheduled_start_at`.

The repository adds only `load_latest_target_race_card_capture(...)`. It accepts an exact
canonical accessD URL and inclusive `observed_at_not_after`, queries that exact URL only,
reconstructs eligible rows, returns the greatest eligible observed instant, and fails
closed on same-latest-time ambiguity or corruption. It does not filter or tie-break on
`stored_at`, add race/site/latest-by-race lookup, change schema/migration/indexes, or
weaken existing capture families.

## Allowed Files

```text
scripts/simulation/jra_target_race_card_resolution.py
scripts/simulation/repositories/sqlite_jra_official_response_capture_repository.py
tests/test_jra_target_race_card_resolution.py
tests/test_sqlite_jra_official_response_capture_repository.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Verification

Resolver suite: **14 passed**. Repository suite: **13 passed**. Related
locator/discovery/target-source/capture/live-capture suite: **74 passed**. Full pytest
suite: **2733 passed**. `git diff --check` passed. Static scope checks passed: exactly
six approved files changed; the pure resolver has no HTTP/SQLite/filesystem/clock/random/
subprocess ownership, broad catch, live fallback, or archive write; and the repository
has no `stored_at` causal filter.

No live HTTP or trusted real capture was performed.

## Stop Condition

Stop after this exact six-file review change is committed and pushed for independent
review. Do not integrate the formal branch or start another phase.
