# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6c1d3b2c` — NAR trusted historical source collection orchestration preparation correction.

Formal base: `93fad49e7b188e3b4492cc7fe0eb61d36d16b735`.

Formal branch: `feature/ver0.8-simulator`.

Preparation review branch: `review/4c-2d3b1i6c1d3b2c-prepare`.

## Fixed Collection Problem

The future one-race collector remains:

```text
caller-supplied DebaTable URL
  -> trusted live DebaTable capture/archive
  -> c1b track, entry, jockey, odds_win records
  -> one trusted HorseMarkInfo capture per target entry
  -> historical-event discovery
  -> trusted RaceMarkTable capture(s)
  -> d3b2a pair normalization
  -> complete validated c1a source-record set
```

It reuses unchanged:

- `NAROfficialLiveResponseCaptureService.capture_response(*, response_url)`;
- `NAROfficialResponseCapture` and `NAROfficialResponseCaptureArchive`;
- `normalize_nar_historical_input_source_records(*, response)`;
- `normalize_nar_historical_past_race_source_record(*, target_entry_record, horse_history_response, race_result_response)`; and
- `build_historical_input_snapshot(...)`.

`TARGET_RACE_DISCOVERY = OUT_OF_SCOPE`. There is one caller-supplied supported DebaTable URL; TopTodayRaceListMini,
RaceList, calendar/scheduling, CLI, daemon/recurring capture, all-races crawling, automatic retry, and acquisition
pagination are not proposed here.

c1b emits `track`, `entry`, `jockey`, and `odds_win`, but not `past_race` or `past_race_absence`. The source-set
builder requires every entry to have one or more past-race records or exactly one absence record. The collector must
eventually close this gap without changing c1a/c1b/d3b2a/capture/archive/builder contracts.

## Repository Investigation: History Is Not Five By Contract

Inspected: `scripts/simulation/nar_historical_input_source.py`,
`scripts/simulation/nar_historical_past_race_source.py`, c1a evidence/source-record modules, c1c snapshot modules,
NAR capture/archive/live-capture modules and their tests, plus `scripts/database.py`, `scripts/cli/run_prediction.py`,
`scripts/prediction/prediction_pipeline.py`, `ability_engine.py`, `pace_engine.py`, and `jockey_engine.py`.

```text
AbilityEngine: uses every supplied eligible past race in weighted ability evaluation.
PaceEngine: uses every supplied past race with usable corner/passing data.
JockeyEngine: uses all eligible matching-jockey races for rate/confidence metrics;
              only its recent-score component limits itself to five.
```

Therefore:

```text
PAST_RACE_HISTORY_DEPTH = UNRESOLVED
PAST_RACE_HISTORY_DEPTH_5 = NOT_APPROVED_AS_COLLECTION_ONLY_CHANGE
COLLECTOR_MAY_SILENTLY_CHANGE_MODEL_HISTORY_WINDOW = NO
```

`SOURCE_ACQUISITION_HISTORY_POLICY` and `PREDICTION_HISTORY_WINDOW_POLICY` are separate contracts. A convenient
collector cap, or `JockeyEngine.RECENT_RACE_LIMIT`, cannot set either. Capturing only five pages would permanently
prevent a later ten-race historical experiment for the same target: subsequently fetched pages have
`observed_at > historical information_cutoff` and are causally ineligible. Acquisition depth is a long-term
replay/data-retention decision, not a request optimization.

Before c1/c2 implementation, a separate `4C-2d3b1i6c1d3b2c0` design phase must choose one provider-neutral policy:

```text
A. ALL_CAUSALLY_AVAILABLE_ACTUAL_PRIOR_STARTS
B. deliberately bounded RECENT_N_ACTUAL_STARTS
C. larger acquisition window plus a separately configurable prediction window
```

That decision must compare future strategy experimentation, network/archive volume, within-collection duplicate
capture reuse, JRA dependency, and causal inability to backfill old targets.

## Historical Event Classification

The history window is over `ACTUAL_PRIOR_STARTS`, never every rendered HorseMarkInfo row. c0 must freeze and fixture
the following structural event classifier before a collector can count a window:

| Event state | Required structural evidence | Window treatment |
| --- | --- | --- |
| NAR actual start | One valid NAR RaceMarkTable navigation identity and a started result state | Counts; pair-normalize it. |
| JRA actual start | Row-local official JRA history representation, not jockey affiliation | Counts; current support fails closed. |
| Unsupported actual start | Started official result, including initial d3b2a-unsupported nonstandard outcome | Counts; fail closed, never skip older history. |
| Non-start/cancelled entry | Exact row-local official status proving `取消`, `除外`, or `競走除外` rather than a started outcome | Does not consume a window position; retain/validate structurally. |
| Started abnormal outcome | Exact official started-state evidence such as `中止`, `失格`, or `降着` | Actual start; fail closed unsupported unless a later normalizer contract supports it. |

The labels alone are not enough: c0 must prove their row/result-link behavior from official representative pages and
must not use jockey affiliation, page-global text, horse name, or row position. Current d3b2a deliberately accepts
only normal completed results and rejects cancellation/abnormal markers; it does not itself define the collection
event count. A non-start is never silently transformed into a normal result. An unsupported actual start consumes its
chronological place and cannot be replaced with an older one.

For any later bounded policy, NAR/JRA support filtering happens **after** actual-start identity/window selection.
`SKIP_JRA_AND_USE_OLDER_NAR = FORBIDDEN` and `SKIP_UNSUPPORTED_AND_USE_OLDER = FORBIDDEN` remain fixed.

## HorseMarkInfo Completeness Investigation

The HorseMarkInfo URL remains derived solely from a validated c1b entry identity:

```text
https://www.keiba.go.jp/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=<lineage>
```

Official non-persisted structural checks found:

| Lineage / representative class | HorseMarkInfo history rows | RaceHorseInfo lifetime total | Finding |
| --- | ---: | ---: | --- |
| `30074407776` mixed NAR/JRA high-career horse | 34 | 34 | Exact count match; 15 NAR links plus JRA rows. |
| `30039401296` current NAR horse | 14 | 14 | Exact count match; 14 NAR links. |
| `30036406666` mixed NAR/JRA high-career horse | 39 | 39 | Exact count match. |
| `30038401876` high-career NAR horse | 36 | 36 | Exact count match. |

The inspected HorseMarkInfo documents had one expected `HorseMarkInfo_table`, descending dates, and no visible
pagination/next/previous control. This is promising structural evidence but is not a proof for every provider state;
no verified fewer-than-five or zero-start representative was obtained during this docs-only investigation.

Each inspected HorseMarkInfo page links row-locally to:

```text
/KeibaWeb/DataRoom/RaceHorseInfo?k_lineageLoginCode=<same lineage>&k_activeCode=1
```

The official RaceHorseInfo page exposes a `着別回数` table whose `生涯`/`合計` value matched the HorseMarkInfo
row count in the four representative checks. Thus:

```text
RACE_HORSE_INFO_COMPLETENESS_SIGNAL = USABLE_AS_A_REPRESENTATIVE_LIFETIME_COUNT_CROSSCHECK
RACE_HORSE_INFO_URL_DERIVATION = row-local official link; same lineage plus k_activeCode=1
RACE_HORSE_INFO_REQUIRED_FOR_RUNTIME = UNRESOLVED
RACE_HORSE_INFO_TRUSTED_CAPTURE_EXTENSION_REQUIRED = UNRESOLVED
```

RaceHorseInfo is **not** silently added to runtime. If c0 concludes it is needed to prove zero or fewer-than-window
history, that is an architecture expansion: `NAROfficialPageKind`, URL canonicalization, capture page-kind CHECK and
migration, live-capture tests, and the absence evidence contract must be reviewed. Current c1a absence permits only
`past_race_absence_query` evidence; a RaceHorseInfo-dependent decision would not be fully audited by a lone
HorseMarkInfo reference and may require a c1a evidence/schema revision. No such revision is authorized here.

Accordingly:

```text
ZERO_HISTORY_PROOF_AVAILABLE = NO
SHORT_HISTORY_COMPLETENESS_PROOF_AVAILABLE = NO
PAST_RACE_ABSENCE_IMPLEMENTATION = BLOCKED
```

Until a complete-source policy is approved, visible short history is `INCOMPLETE_HISTORY_SOURCE`, not permission to
return fewer records. A history row date greater than or equal to the target race date is a chronology contradiction.

## Causal Capture and NAR Link Rules

After c1b supplies `scheduled_start_at`, every accepted capture must satisfy:

```text
DebaTable observed_at <= scheduled_start_at
HorseMarkInfo observed_at <= scheduled_start_at
each RaceMarkTable observed_at <= scheduled_start_at
COLLECTION_CAPTURED_AT = max(accepted evidence observed_at)
```

A late DebaTable capture rejects before historical work. A later HorseMarkInfo/RaceMarkTable capture rejects the
collection. Captures are persisted before normalization; individual evidence timestamps remain unchanged. Current
live retrieval cannot create causal evidence for an old cutoff:

```text
RETROACTIVE_TRUSTED_BACKFILL = IMPOSSIBLE
EARLY_HISTORICAL_DATA_AVAILABILITY = LIMITED_TO_CAPTURES_ACTUALLY_OBSERVED_BEFORE_CUTOFF
```

This is an operational limitation, not a blocker for a future live collector.

HorseMarkInfo result links are structurally parsed for `(raceDate, babaCode, raceNo)`, then reconstructed only as the
d3b2a-supported capture URL on `www.keiba.go.jp`. A `www2` navigation link may supply the identity only after exact
validation; evidence always preserves the canonical URL of actually captured bytes. No date/place/name/row-order
fallback is allowed. One RaceMarkTable capture per canonical URL per collection remains approved; cross-collection
reuse is deferred.

## Corrected c2 and c3 Boundaries

c2 is an injected one-race collector only after c0 and c1 prerequisites are approved. Its exact module-defined public
surface is:

```text
NARHistoricalSourceCollection
NARHistoricalSourceCollectionError
collect_nar_historical_input_source_records
```

`NARHistoricalSourceCollectionError` is only for collection-owned contradictions such as a post-scheduled-start
capture or internally contradictory collection plan. Existing live-capture/transport, archive, c1b, discovery,
d3b2a, and c1a validation errors propagate unchanged. Pacing is a **private injected protocol/collaborator**:

```text
PACING_CORE_COLLECTOR = INJECTED
PACING_DEFAULT_IMPLEMENTATION = COMPOSITION_OWNED
PACING_OFFICIAL_RATE_LIMIT_CLAIM = NONE
REQUEST_CONCURRENCY = 1
AUTOMATIC_RETRY = NONE
```

No public pacing type is approved. A composition-provided conservative interval may be selected later but is not an
official NAR rate-limit claim. The pure discovery layer owns no sleep.

Successful collection order is exactly:

```text
track
then each target horse by horse_no ascending:
  entry
  jockey
  odds_win
  then past_race newest-to-oldest
  OR one proven past_race_absence
```

Before return c2 performs collection-completeness validation: exactly one track and, for every entry, exactly one
entry/jockey/odds-win plus exactly one history form (one-or-more selected past races or one proven absence). It then
uses `validate_historical_input_source_record_set(...)` as final provider-neutral validation. No partial collection
result is returned on failure; immutable captures already archived may remain.

```text
PARTIAL_ARCHIVE_ON_COLLECTION_FAILURE = ALLOWED
PARTIAL_SOURCE_COLLECTION_RESULT = FORBIDDEN
```

`d3b2c3 = CAPTURE_COLLECTION_COMPOSITION_ONLY`: it may own caller-supplied capture database path, SQLite capture
connection lifecycle, capture migration application, capture repository, live-service construction, composition-owned
pacing, and c2 construction. It does **not** own main simulation database lookup, entry mapping, snapshot building, or
snapshot persistence.

The separate later `4C-2d3b1i6c1d3b2d` phase owns main-DB identity mapping, information-cutoff policy,
`build_historical_input_snapshot(...)`, and snapshot persistence. Trusted acquisition, main-DB identity, and snapshot
construction remain separate concerns.

## Required Decision and Future Scope

Architecture blockers:

```text
HISTORY_WINDOW_POLICY_UNRESOLVED
HORSE_MARK_COMPLETENESS_FOR_ZERO_OR_SHORT_HISTORY_UNRESOLVED
RACE_HORSE_INFO_RUNTIME_COMPLETENESS_DEPENDENCY = UNRESOLVED
```

Operational limitation only: trusted historical data exists only where official captures were actually observed before
the applicable cutoff. It does not block live collection implementation once the architecture blockers are resolved.

Recommended split:

```text
4C-2d3b1i6c1d3b2c0  historical prediction/source window contract (design only)
4C-2d3b1i6c1d3b2c1  pure HorseMark historical-event discovery only
4C-2d3b1i6c1d3b2c2  injected one-race trusted source collector
4C-2d3b1i6c1d3b2c3  capture DB/live collector composition only
4C-2d3b1i6c1d3b2d  collected NAR source set -> main identity mapping -> snapshot composition
```

If c0 approves a complete HorseMark-only zero proof, a separately authorized absence-normalizer extension may follow
c1. If it requires RaceHorseInfo, first prepare the trusted-capture/evidence architecture extension. Neither outcome
is pre-approved here.

Exact future allowed files:

### d3b2c0

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

### d3b2c1

```text
scripts/simulation/nar_historical_past_race_discovery.py
tests/test_nar_historical_past_race_discovery.py
tests/fixtures/nar/horse_mark_info_history_discovery.html
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

### d3b2c2

```text
scripts/simulation/nar_historical_source_collection.py
tests/test_nar_historical_source_collection.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

### d3b2c3

```text
scripts/simulation/nar_historical_source_collection_composition.py
tests/test_nar_historical_source_collection_composition.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

### d3b2d

```text
scripts/simulation/nar_collected_source_snapshot_composition.py
tests/test_nar_collected_source_snapshot_composition.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

`JRA_TARGET_RACE_COLLECTION = FUTURE_REQUIRED` and
`JRA_HISTORICAL_PAST_RACE_COLLECTION = FUTURE_REQUIRED` remain explicit.

## PREPARE Scope and Stop Condition

Only `docs/CURRENT_PHASE.md` and `docs/LATEST_CODEX_REPORT.md` may change in this correction. No production code,
tests, fixtures, migration, DB, capture archive/body, discovery, collector, absence normalizer, or composition phase
was implemented. Stop after the docs-only correction commit and independent architecture re-review.
