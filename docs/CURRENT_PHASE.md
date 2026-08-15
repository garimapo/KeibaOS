# Current Phase

## Status

READY_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6d1d5a` — JRA historical past-race normalizer implementation.

Formal base: `dcdef4bd6559418fe7f179f42cd16a263604fc08`.

Approved PREPARE: `3a8c1fc26eb90c83b0578aa30afe724a2779c2dd`.

Review branch: `review/4c-2d3b1i6d1d5a-jra-past-race-normalizer`.

## Implemented Boundary

`scripts/simulation/jra_historical_past_race_source.py` is a pure supplied-response normalizer with exactly these
module-defined public names:

```text
JRAHistoricalPastRaceSourceError
JRAHistoricalPastRaceSourceValidationError
JRAHistoricalPastRaceSourceUnsupportedError
normalize_jra_historical_past_race_source_record
```

The function accepts the approved target track/entry records, one exact accessS `JRASuppliedOfficialResponse`, and one
exact request-aware accessO `JRAFinalWinOddsSuppliedOfficialResponse`; it returns one target-scoped JRA `past_race`
record. It has no HTTP, archive, filesystem, database, clock, discovery, pagination, bridge, or package-root export.

Target records are exact c1a values with organization `JRA` and source system `jra_official`. Their target race ID,
entry ID, entry horse number, and stable `jra:horse:<10 digits>` identity are cross-checked through the formal JRA
identity constructors. Historical horse selection is only the unique accessS `td.horse a[href]` accessU anchor matching
that stable horse identity. The selected historical `td.num` is used only to join accessO and need not equal target
horse number.

## Identity, Facts, and Evidence

The normalizer parses accessS with the formal public result URL parser, narrowly validates its already-approved CNAME
calendar date, and requires it to precede the target track date. Unique visible accessS/accessO headers cross-check
date, venue mapping, meeting number/day, race number, and race heading. The result table must have the approved
semantic heading family; accessO must have exactly one `table.tanpuku`, with one matching `td.num` and direct positive
finite `td.odds_tan` value.

All 17 c1a values have direct authority: accessS supplies race/date/place/name/class/distance/surface/weather/
condition, finish/time, body weight/change, jockey, popularity, passing order, and fourth-corner position; accessO
supplies final single-win odds only. No float conversion, assigned-weight substitution, textual-margin conversion, or
derived odds is permitted. `td.corner li[title]` labels must uniquely and increasingly identify the explicit fourth
corner; neither a fixed component nor the final component is assumed.

The output keeps target external race/entry IDs and uses the historical JRA race plus stable horse identity in
`build_jra_provider_record_id`. It creates exactly three canonical evidence roles:

```text
historical_race_context    = accessS URL / raw SHA / None / supplied observed_at
historical_race_final_odds = accessO endpoint / request fingerprint / raw SHA / None / supplied observed_at
historical_race_result     = the same accessS evidence tuple as context
```

SHA-256 is calculated over supplied bytes before strict CP932 decode or parsing. Timestamp-only changes leave source
identity unchanged; body or accessO request-fingerprint changes do not. The existing builder remains the only causality
owner. No timestamp is backdated or fabricated.

## Fail-closed Scope

Malformed/contradictory identities, missing or duplicate headers/tables/rows/anchors, wrong lineage, malformed CP932,
or accessS/accessO disagreement raise the normalizer validation error. Recognized but unsupported result states include
withdrawal/exclusion/DNF/disqualification, blank class, invalid finish/time/body weight/popularity, nonpositive odds,
unsupported surface, and ambiguous/missing fourth-corner structure. There is no fallback.

Tests use only synthetic strict-CP932 HTML strings in the dedicated test module; no official page, archive record, or
fixture file was captured or committed. NAR production, JRA capture/domain/archive/live production, neutral evidence,
source/snapshot schema versions (4), global migrations (14), and JRA capture migrations `(1,2)` are unchanged.

## Allowed Files and Stop Condition

```text
scripts/simulation/jra_historical_past_race_source.py
tests/test_jra_historical_past_race_source.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

Stop for independent implementation review. Do not formally integrate, perform real accessO capture, begin historical
discovery/orchestration, change target acquisition, connect Predictor, or begin the NAR/JRA bridge.
