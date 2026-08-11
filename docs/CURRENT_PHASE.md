# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6c1d3b2c0a` — NAR HorseMarkInfo completeness contract preparation.

Formal base: `93fad49e7b188e3b4492cc7fe0eb61d36d16b735`.

Preparation review branch: `review/4c-2d3b1i6c1d3b2c0a-prepare`.

Approved parent design: `0a6b31763a9529ae18c2a5333083beb4d52f6250`.

## Frozen Parent Window Policy

```text
SOURCE_ACQUISITION_HISTORY_POLICY = ALL_CAUSALLY_AVAILABLE_ACTUAL_PRIOR_STARTS
PREDICTION_HISTORY_WINDOW_POLICY = SEPARATELY_CONFIGURABLE
INITIAL_PREDICTION_WINDOW_DEFAULT = ALL_AVAILABLE
SNAPSHOT_HISTORY_CONTENT = ALL_ACQUIRED_CAUSALLY_ELIGIBLE_HISTORY
PROVIDER_FILTER_BEFORE_HISTORY_SELECTION = FORBIDDEN
COLLECTOR_MAY_SILENTLY_CHANGE_MODEL_HISTORY_WINDOW = NO
```

The result below concerns complete official event identity, not historical replay causality. Current-page research does
not make an old target causally replayable: `RETROACTIVE_TRUSTED_BACKFILL = IMPOSSIBLE` remains unchanged.

## Final Completeness Decision

```text
HORSE_MARK_COMPLETE_ACTUAL_START_SOURCE = YES
RACE_HORSE_INFO_RUNTIME_REQUIRED = NO
RACE_HORSE_INFO_EXTENSION_REQUIRED = NO
PAST_RACE_ABSENCE_PROOF_SOURCE = HORSEMARKINFO_ONLY
```

RaceHorseInfo is an official design-time cross-check only. It is not a fourth runtime capture, evidence role, page
kind, archive schema change, or c1a change. HorseMarkInfo itself can prove the complete event sequence under the
runtime conditions below, including a distinct explicit zero-history representation.

## Official Structural and Count Investigation

No official response body was retained. Each HorseMarkInfo/RaceHorseInfo pairing used exactly the same
`k_lineageLoginCode`; no horse name was used for identity.

| Class | Lineage | HorseMark rendered rows / classified actual starts | RaceHorseInfo lifetime total | Result |
| --- | --- | ---: | ---: | --- |
| high-career NAR-only, with non-starts | `30023406756` | 85 / 83 | 83 | Exact after two proven non-start rows. |
| high-career mixed NAR/JRA | `30074407776` | 34 / 34 | 34 | Exact: 15 NAR-link rows + 19 row-local JRA rows. |
| short history | `30022408717` | 1 / 1 | 1 | Exact one-start example. |
| additional short examples | `30088405917`, `30033402217` | 3 / 3, 2 / 2 | not re-used at runtime | Consistent finite short-history layout. |
| debut / zero history | `30055402717` | 0 / 0 | 0 | Explicit official no-history state. |

The high-career NAR-only page has 85 rows, proving no small hidden row cap; its RaceHorseInfo total is 83. It contains
two row-local official non-start states:

```text
2025-11-27: 差 = 取消, blank time/body-weight result fields
2020-12-15: 差 = 取止, blank time/body-weight result fields
```

Both retain a NAR race-navigation identity but do not represent a completed start. `85 rendered rows - 2 proven
non-starts = 83 lifetime starts`, exactly matching RaceHorseInfo. This directly establishes that RaceHorseInfo's
`生涯`/`合計` includes normal NAR starts and excludes the observed `取消` and `取止` non-starts.

The mixed page proves its lifetime total spans organizations: its 15 NAR RaceMarkTable rows plus 19 structurally JRA
rows equal `34`. It does not permit NAR filtering before event-sequence selection.

The short one-start HorseMarkInfo page has the normal unique history table and one NAR RaceMarkTable row; its lifetime
total is one. This is an exact reproducible short-history count match.

For `30055402717`, a future NAR two-year debut entry, the canonical HorseMarkInfo page has valid horse-page identity,
no history table, no RaceMarkTable history link, and the direct official message:

```text
指定の馬の出走履歴がありません。
```

Its same-lineage RaceHorseInfo lifetime total is zero. This is the official zero-history example. The zero state is
therefore not an empty malformed table: it is a separate, exact recognized HorseMarkInfo layout.

No sampled page contained an observed `中止`, `失格`, or `降着` row, nor observed `除外`/`競走除外` row. No count
claim is made for those unobserved tokens. A future discovery implementation must classify a directly observed started
abnormal RaceMark result as `UNSUPPORTED_ACTUAL_START` (it consumes chronological position) only when its structural
result state proves that conclusion; unknown row state fails closed and is never treated as non-start solely by label.

## Frozen HorseMarkInfo Runtime Completeness Conditions

The future pure discovery input must satisfy all of the following:

1. canonical HTTPS HorseMarkInfo URL, exact validated `k_lineageLoginCode`, and exact target-entry lineage match;
2. exact expected official HorseMarkInfo document identity; no generic HTML/content dispatch;
3. exactly one recognized state:
   - one expected history table with the complete approved heading family, or
   - the explicit no-history message above, with no history table and no RaceMarkTable history link;
4. for a table state, every row is completely parsed, has a unique provider-native event identity, and the official
   chronology is non-increasing by date (same-date identities remain distinct and unambiguous);
5. every row is structurally classified as NAR actual start, JRA actual start, proven non-start, or unsupported actual
   start; no unclassified row is silently omitted;
6. no official history pagination/next/previous/more/offset/limit continuation control, hidden history rows, or
   alternate history endpoint is present; and
7. provider filters occur only after the complete actual-start sequence is known.

Observed controls support this condition: high (85), mixed (34), short (1), and zero pages exposed no history
pagination/continuation control, no page/offset/limit inputs, and no alternate history endpoint. The only related
official navigation was RaceHorseInfo plus per-row RaceMarkTable links; the only form was site search. The zero page
has RaceHorseInfo navigation only.

Duplicate event identity, out-of-order chronology, an unknown state, extra table/state, continuation marker, or any
partial-row structure is validation failure. This preserves fail-closed completeness without requiring RaceHorseInfo
at runtime.

## Event and Provider Semantics

```text
NAR actual start: valid NAR RaceMarkTable provider identity and started/normal result path.
JRA actual start: row-local JRA representation; it counts before any provider filter.
Proven non-start: structurally observed 取消 or 取止 state with non-result fields; does not count.
Unsupported actual start: started abnormal or valid result outside d3b2a normal-completed support; counts and fails closed.
Unknown event state: validation failure; no name, affiliation, page-global text, or token-only fallback.
```

`除外` and `競走除外` are not assumed from a label; their first supported treatment requires the same direct
row/result structure as a proven non-start. `中止`, `失格`, and `降着` are not treated as non-start; if a future
official result demonstrates a started state, it counts and current d3b2a support fails closed.

## Consequences for c1 and the Roadmap

```text
ZERO_HISTORY_PROOF_AVAILABLE = YES
SHORT_HISTORY_PROOF_AVAILABLE = YES
PAST_RACE_ABSENCE_IMPLEMENTATION = APPROVED
D3B2C1_IMPLEMENTATION = APPROVED_NEXT
```

c1 must return the complete ordered actual-start event sequence; it must not select a 5/10/20 model window. A valid
zero page may produce one later `past_race_absence` record with HorseMarkInfo-only provenance. A legitimate short
history naturally returns its complete 1/2/3/... actual starts without fabrication.

`JRA_HISTORICAL_SOURCE_PREREQUISITE = REQUIRED_BEFORE_COMPLETE_MIXED_ALL_HISTORY_COLLECTION`. Even with approved
HorseMarkInfo completeness, mixed horses cannot yield a complete trusted all-history prediction input until JRA
official capture/normalization exists. JRA rows cannot be skipped to older NAR rows.

Recommended sequence:

```text
4C-2d3b1i6c1d3b2c1  pure complete HorseMark event discovery plus HorseMark-only zero-absence normalizer
JRA historical source preparation/implementation
4C-2d3b1i6c1d3b2c2  injected one-race collector, only complete all-history sets
4C-2d3b1i6c1d3b2c3  capture DB/live collector composition only
4C-2d3b1i6c1d3b2d  main identity, snapshot, deterministic prediction-window/reference-date/adapter integration
```

Future c1 allowed files must be separately approved and are expected to be exactly:

```text
scripts/simulation/nar_historical_past_race_discovery.py
scripts/simulation/nar_historical_past_race_absence_source.py
tests/test_nar_historical_past_race_discovery.py
tests/test_nar_historical_past_race_absence_source.py
tests/fixtures/nar/horse_mark_info_history_discovery.html
tests/fixtures/nar/horse_mark_info_zero_history.html
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

The already separate downstream blockers remain unchanged and do not block pure HorseMark discovery:

```text
ABILITY_REFERENCE_DATE_STATUS = FUTURE_LEAKAGE_BLOCKER_IN_CURRENT_PERSISTED_COMPOSITION
JOCKEY_REFERENCE_DATE_STATUS = FUTURE_LEAKAGE_BLOCKER_IN_CURRENT_PERSISTED_COMPOSITION
TIME_DIFFERENCE_TO_PREDICTION_ADAPTER_STATUS = NO_ADAPTER_CONTRACT_GAP
```

## PREPARE Scope and Stop Condition

Only `docs/CURRENT_PHASE.md` and `docs/LATEST_CODEX_REPORT.md` may change. No production code, test, fixture,
schema/migration, database, capture archive/body, or collector/discovery work was implemented. Stop after one docs-only
review commit and independent architecture review.
