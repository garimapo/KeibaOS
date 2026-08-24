# Current Phase

## Status

READY_FOR_REVIEW

## Phase

`4C-2d3b1i6d1d5f1c4d` — JRA race-level historical replay orchestration.

Formal base: `f07a91fb55248d562202513f7b70c528528e7143`.

Approved prepare: `079a86ade450ff0e40b04cc2e3044d0710e71ec0`.

Review branch:
`review/4c-2d3b1i6d1d5f1c4d-jra-race-level-historical-replay`.

## Implemented Contract

The phase adds one pure, read-only `build_jra_race_historical_replay(...)` boundary.
Its sole domain input is an exact immutable `JRARaceReplaySeed`; five injected read-only
providers supply exact v4 navigation, exact v3 target card by capture ID, accessU horse
history, accessS race results, and accessO final odds. No decomposed caller identity,
mapping, capture, URL, digest, or time fields are accepted.

The private seed-bound v3 adapter satisfies formal c4c's locator-and-cutoff provider
shape while loading only `seed.target_race_card_capture_id`. It requires the requested
locator and bound to equal the seed, calls the exact-by-ID provider once, and validates
the returned capture's exact type, ID, body digest, canonical URL, race identity, and
observation bound. Missing exact evidence remains unavailable. The generic latest-v3
archive lookup is never used, so later archive enrichment cannot change an existing
seed replay.

Formal c4c is called exactly once with the seed's race, v4 capture ID, and captured
instant. Its complete v4/v3/URL/digest/time provenance must equal the seed before its
supplied response is normalized exactly once. The normalized track, ordered entries,
and aligned accessU locators must equal the seed position-by-position before any
per-entry history provider is called.

Every accessU resolution and historical collector call uses `seed.captured_at` as the
inclusive evidence observation bound. C4d rechecks:

```text
seed.captured_at <= seed.information_cutoff <= normalized target scheduled_start_at
```

`stored_at` has no causal role. For every seed entry, the formal accessU resolver and
historical collector each run once. The complete source tuple is formed only after all
entries succeed: canonical target records first, then each complete historical
collection in seed order. Source IDs must be globally unique; no partial result is
possible.

The snapshot entry map is derived only from seed entries. The existing snapshot builder
is called exactly once with the seed's dataset, internal race, captured instant,
information cutoff, complete source tuple, and exact mapping. C4d performs no snapshot
persistence. The frozen/slotted public result retains exactly the supplied seed object
and the completed `HistoricalInputSnapshot`, and independently verifies all seed/
snapshot race, time, and ordered-entry identities.

Validation, unavailable, and unsupported errors from the formal composed boundaries
are translated into the matching c4d error family. Provider-owned integrity errors
propagate unchanged. There is no broad catch, HTTP, SQLite/repository dependency,
database or archive write, clock, filesystem, live capture, current fallback, seed
construction, latest lookup, raw HTML parser, legacy/name mapping, package-root export,
or multi-race ownership.

## Verification

Dedicated c4d tests: **35 passed**.

Related formal d0, c4c, target-source, accessU, historical collector, source-record,
snapshot-builder, and archive repository tests: **183 passed**.

Full pytest suite: **2843 passed**.

The dedicated suite includes actual formal end-to-end zero-history replay, multi-entry
ordering and mapping, every error translation, provider-integrity propagation, exact
result construction, and the deferred restart/archive-enrichment regression. That
regression persists capture A, crosses a repository restart, adds later eligible capture
B for the same URL, and proves c4d requests and consumes only A by its seed capture ID
while the generic latest-v3 method is forbidden.

`git diff --check`, exact four-file scope, public-surface, no-broad-catch, forbidden
dependency, no latest lookup, no write/persistence, and no package-root export checks
pass. No live HTTP or real trusted capture was performed.

## Changed Files

```text
scripts/simulation/jra_race_historical_replay.py
tests/test_jra_race_historical_replay.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Stop Condition

Stop after the single implementation review commit is pushed. Do not integrate the
formal branch, persist a snapshot, add repository/schema behavior, perform live HTTP,
or begin a later phase until independent review approves this exact result.
