# Current Phase

## Status

READY_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6d1d5b3` — JRA complete-history discovery implementation.

Formal base: `367602e64353244e27b1518014c0907b922fb4ae`.

Approved PREPARE: `f39aafb63f7538e55484cbc8171cf94865a17e1c`.

Review branch: `review/4c-2d3b1i6d1d5b3-jra-complete-history-discovery`.

## Implemented Boundary

Implemented the pure, single-supplied-response function:

```python
discover_jra_historical_past_race_history(
    *,
    target_track_record: HistoricalInputSourceRecord,
    target_entry_record: HistoricalInputSourceRecord,
    horse_history_response: JRASuppliedOfficialResponse,
) -> JRAHistoricalPastRaceDiscovery
```

The only module-defined public names are `JRAHistoricalEventKind`,
`JRAHistoricalPastRaceReference`, `JRAHistoricalPastRaceDiscovery`, the three stated discovery errors, and the
function. Domain values are immutable/slotted. No package-root export is permitted.

It validates exact target JRA c1a track/entry records and their coherent race/entry/horse identities, then requires exact
accessU `HORSE_PROFILE_HISTORY` supplied evidence for that horse, strict CP932 decoding, and
`observed_at <= scheduled_start_at`. There is no name fallback, no clock lookup, and no timestamp backdating.

Use only `div.race_detail > table.basic.narrow-xy.striped` with the exact ordered semantic headings:

```text
年月日 | 場 | レース名 | 距離 | 馬場 | 頭数 | 人気 | 着順 | 騎手名 | 負担重量 | 馬体重 | タイム | Rt | 1着馬（2着馬）
```

Classify every row exactly once as `JRA_ACTUAL_START`, `NON_JRA_ACTUAL_START`, `PROVEN_NON_START`, or
`UNSUPPORTED_ACTUAL_START`; unknown rows fail closed. JRA starts require one exact row-local official accessS anchor,
whose formal parsed identity and date agree with the row. Non-JRA/unsupported events remain explicit without an
invented JRA identity. Proven transfer/non-start rows never count. Actual events must remain reverse chronological,
strictly precede the target date, and be duplicate-free.

Mandatory response-local completeness proof: it requires the unique `li#result_unit` `レース条件別成績` aggregate section;
one `平地レース合計` and one `障害レース合計` table in its exact left/right grid cells; exact result aggregate headers;
canonical non-negative counts; independent `1着 + 2着 + 3着 + 4着以下 == 出走回数` checks; and equality between
`flat + obstacle` and all displayed actual events. Any mismatch, malformed aggregate, continuation/lazy-load marker,
unknown row, or ambiguity is a discovery validation error. No latest-N fallback or foreign-horse inference exists.

Zero history is accepted only for simultaneous exact `出走レース` no-data and both aggregate no-data/valid zero states,
with no row/navigation or continuation marker. `proven_zero_history == (events == ())` always holds. A known
unsupported actual event remains an event and participates in the count; it is never silently omitted.

The module must not use HTTP, archives, repositories, filesystem, SQLite, network, accessS/accessO fetching,
accessO locator synthesis, normalization, pagination fetching, discovery of races, Predictor, random, subprocess, or
clock ownership.

## Allowed Files

```text
scripts/simulation/jra_historical_past_race_discovery.py
tests/test_jra_historical_past_race_discovery.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Verification

Fresh verification using Python 3.14.5 / pytest 8.3.5 passed: the dedicated discovery suite (8 tests), the d1d5a,
JRA identity/capture/archive/live, NAR historical-source, and neutral source/snapshot/builder regression set (126
tests), and the full suite (2588 tests). Package-root export, forbidden-dependency/source, unchanged-production,
version, diff, and final-status checks are required before review publication.

## Stop Condition

Create and push exactly one review commit: `feat: discover complete JRA horse history`. Do not formally integrate,
perform real capture, implement orchestration or an accessO locator, create a NAR/JRA bridge, or connect Predictor.
