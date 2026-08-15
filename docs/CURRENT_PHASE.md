# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6d1d5b2` — JRA accessU response-local complete-history proof PREPARE.

Formal base: `367602e64353244e27b1518014c0907b922fb4ae`.

Approved prior PREPAREs:

```text
d1d5b  be0941a3fef1ea8c0d652464de584a7d6350ff23
d1d5b1 4ba8541526b191a0642fd6b6bad7256a3689542a
```

Review branch: `review/4c-2d3b1i6d1d5b2-jra-history-count-proof-prepare`.

## Decision

`ACCESS_U_COMPLETE_HISTORY_PROOF = RESPONSE_LOCAL_AGGREGATE_COUNT_EQUALITY` is approved for the future pure
discovery boundary. It is a per-supplied-response proof; it does not assert that every accessU response is complete.
It requires all of the following in one exact, strict-CP932-decoded, supplied official accessU
`HORSE_PROFILE_HISTORY` response:

1. Its stable accessU horse identity equals the target entry's canonical `jra:horse:<10 ASCII digits>` identity, its
   `observed_at` is not later than the target `scheduled_start_at`, and the target track/entry chain is otherwise
   formally valid.
2. The unique `li#result_unit` section has the exact heading `レース条件別成績`, and its direct
   `div.race_data.mt10 > div.layout_grid` contains exactly two aggregate cells:
   `div.cell.left > table.basic.narrow` with caption `平地レース合計`, and
   `div.cell.right > table.basic.narrow` with caption `障害レース合計`.
3. Each aggregate table has exactly the expected condition-result header family, including exactly one
   `出走回数` column; exactly one ordinary data row; and a canonical non-negative ASCII decimal integer in that
   column. `1着 + 2着 + 3着 + 4着以下 == 出走回数` is a required internal coherence check, not an inferred total.
4. `total_actual_starts = flat_start_count + obstacle_start_count`.
5. Every displayed accessU historical row is structurally and closed-classified. The displayed actual-start count is
   the count of all `JRA_ACTUAL_START`, `NON_JRA_ACTUAL_START`, and explicitly recognized
   `UNSUPPORTED_ACTUAL_START` rows. It excludes only proven non-start rows such as `JRAへ転入`, `JRAより転出`,
   cancellation/non-start rows, and no-data rows. Unknown or ambiguous rows are validation failures.
6. Each displayed actual start has a deterministic event identity; duplicate events, contradictory dates, target-date
   or future events, or malformed/ambiguous official navigation fail closed. A JRA actual start requires its exact
   accessS result navigation and parsed `JRAExternalRaceIdentity`; a non-JRA or otherwise unsupported actual start
   remains an explicit event and is never dropped.
7. No official pagination, continuation, lazy-load, or omitted-history marker is present. Its presence is a
   completeness failure, not a request to fetch.
8. `displayed_actual_start_count == total_actual_starts` exactly. Either inequality fails closed and returns no
   discovery result.

The official accessU explanatory material says that race and condition results are for all races started in JRA,
local/NAR, and overseas racing, while the displayed race list states that foreign horses are generally shown only for
their latest four starts. The aggregate comparison directly detects that truncation (for example, aggregate 10 versus
four displayed actual starts) without deciding the undefined provider membership of `外国馬`. Thus
`FOREIGN_HORSE_SEMANTICS_REQUIRED = NO` for this count proof.

## Aggregate and Zero-History Structure

The aggregate selectors are frozen as semantic structure, not merely CSS presence:

```text
aggregate section: unique li#result_unit whose direct heading is レース条件別成績
flat total:        section > div.race_data.mt10 > div.layout_grid > div.cell.left
                   > table.basic.narrow with caption .main == 平地レース合計
obstacle total:    same unique grid > div.cell.right > table.basic.narrow
                   with caption .main == 障害レース合計
start count:       the only data cell position headed exactly 出走回数
```

`ZERO_HISTORY_PROOF = PROVEN_RESPONSE_LOCAL` only when the same response has all three exact, non-contradictory
facts: (a) the unique `出走レース` section is the official `該当するデータがありません。` no-data state with no event
row/navigation, (b) each required aggregate cell above is also the exact official no-data state, and (c) no
continuation/lazy-load marker exists. This establishes zero actual starts represented by the official aggregate at
that observation; absence of parser output alone never establishes zero history. A numeric aggregate state instead
uses the equality rule, including `0 + 0 == 0` only with the same exact no-history structural proof.

## Provider Policy, Causality, and Failure Handling

`INCOMPLETE_RESPONSE_POLICY = FAIL_CLOSED_VALIDATION_ERROR`: a missing/duplicate aggregate, bad layout, bad count,
arithmetic contradiction, actual-count mismatch, unknown row, duplicate event, or continuation marker returns no
discovery. There is no latest-N acceptance, page fetching, inferred foreign-horse status, or caller completeness
override.

`COMPLETE_UNSUPPORTED_EVENT_POLICY = EXPLICIT_UNSUPPORTED_EVENT_REFERENCE`: once equality proves a complete
response, a known non-JRA or known unsupported actual start is retained in the returned ordered discovery. Later
collection may not silently omit it; it must stop or report that the event cannot yet be normalized. This preserves
`ALL_CAUSALLY_AVAILABLE_ACTUAL_PRIOR_STARTS` while keeping d1d5a's JRA-only normalizer boundary unchanged.

JRA declares different update schedules for JRA and non-JRA data and warns of publication delays. A self-consistent
response passing this proof is valid only as the official information available at its supplied `observed_at`; it
does not claim knowledge of a start not yet represented by that response. Replay therefore additionally requires
`horse_history_response.observed_at <= target scheduled_start_at` and every returned event date strictly before the
target race date. No timestamp is backdated and a page fetched today cannot prove an earlier cutoff merely because
its rows are old.

## Future Discovery Contract

The next phase may implement exactly:

```python
discover_jra_historical_past_race_history(
    *,
    target_track_record: HistoricalInputSourceRecord,
    target_entry_record: HistoricalInputSourceRecord,
    horse_history_response: JRASuppliedOfficialResponse,
) -> JRAHistoricalPastRaceDiscovery
```

The function must perform the response-local aggregate proof itself. It accepts no eligibility flag, no caller
assertion such as `is_foreign=False`, no pagination response list, and no accessO locator. It discovers exact JRA
accessS event references only from actual accessU navigation; it does not normalize, obtain accessS/accessO, construct
an accessO CNAME, access an archive, or perform network/filesystem/database/clock work.

Recommended next phase: `4C-2d3b1i6d1d5b3 — JRA complete-history discovery implementation`.

Future allowed files:

```text
scripts/simulation/jra_historical_past_race_discovery.py
tests/test_jra_historical_past_race_discovery.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Unchanged Boundaries and Stop Condition

Source schema version 4, snapshot schema version 4, global migrations through 14, and JRA capture migrations `(1,2)`
remain unchanged. d1d5a, JRA accessS/accessU/accessO capture/archive/live code, NAR production, provider-neutral
evidence/source/snapshot code, target acquisition, Predictor integration, and the NAR/JRA bridge remain out of scope.
`NAR_LINEAGE_TO_JRA_HORSE_ID_LINK = NOT_PROVEN` and `MIXED_HISTORY_COLLECTION_READY = NO` remain frozen. No real
trusted capture, archive mutation, production implementation, fixture, test, schema, or migration is authorized in
this PREPARE phase.

Allowed files for this PREPARE phase:

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

Stop for independent design review.
