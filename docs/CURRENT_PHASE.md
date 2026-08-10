# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase

Phase 4C-2d3b1i6c1d3b2 — NAR historical past-race multi-response normalizer contract preparation

## Base Commit

21c0c644f9bf8641afa5f007cd7fb14ac9eb030e feat: add historical input evidence contract

## Branch and Workspace

Formal branch: feature/ver0.8-simulator

Preparation review branch: review/4c-2d3b1i6c1d3b2-prepare

Canonical workspace: C:\Users\garim\Desktop\KeibaAI-review-1i5b2b

The original workspace, C:\Users\garim\Desktop\KeibaAI, is read-only for this phase.

## Objective and Public Boundary

Freeze a pure supplied-response NAR pair normalizer: exactly one official HorseMarkInfo response plus exactly one
official RaceMarkTable response yield exactly one c1a v3 HistoricalInputSourceRecord(record_kind="past_race").
There is no list/pagination, fetch, cache, database, clock, filesystem, raw-body-persistence, or package-root role.

The selected future module is scripts/simulation/nar_historical_past_race_source.py. Its exact public surface is:

    normalize_nar_historical_past_race_source_record(
        *,
        target_external_race_id: str,
        target_external_entry_id: str,
        target_external_horse_id: str,
        horse_history_response: NarSuppliedOfficialResponse,
        race_result_response: NarSuppliedOfficialResponse,
    ) -> HistoricalInputSourceRecord

It reuses only the existing public NarSuppliedOfficialResponse,
NarHistoricalInputSourceValidationError, and NarHistoricalInputSourceUnsupportedError. No new public type or error is
required.

## Target and Response Identity

- Target race is exactly nar:{YYYYMMDD}:{k_babaCode}:{k_raceNo}; date and the two ASCII decimal tokens are
  canonical, positive, and have no sign, whitespace, Unicode digit, or leading zero.
- Target entry is exactly {target_external_race_id}:entry:{horse_no}, not a substring relationship.
- Target horse is exactly nar:horse:{k_lineageLoginCode}, retaining the committed d1 lexical [1-9][0-9]* lineage
  grammar. Name, horse number, jockey, trainer, local ID, row order, and fuzzy matching are forbidden.
- The historical URL date must be strictly before the target date. Same-day and future races fail; d3b2 never infers
  intraday ordering.
- Both responses are exact NarSuppliedOfficialResponse instances with charset == "utf-8". Hash exact body bytes before
  decoding; then decode once. No CP932/Latin-1 fallback, replacement, or ignored errors.

## URL and Host Contract

| Page | accepted hosts | path | query / canonical representation |
| --- | --- | --- | --- |
| HorseMarkInfo | www.keiba.go.jp, www2.keiba.go.jp | /KeibaWeb/DataRoom/HorseMarkInfo | exactly k_lineageLoginCode; retain accepted host and canonical lexical token |
| RaceMarkTable | www.keiba.go.jp | /KeibaWeb/TodayRaceInfo/RaceMarkTable | exactly k_babaCode,k_raceDate,k_raceNo; canonical order and YYYY%2FMM%2FDD date |

Both require HTTPS, an absent port or 443, no credentials, fragment, controls, surrounding whitespace, malformed percent
escape, plus ambiguity, duplicate/blank/unknown query key, or noncanonical number/date. Hosts are not rewritten:
accepted www and www2 remain distinct evidence URLs. URL equality is never race identity.

## Pair Selection and Provider Identity

1. Parse the RaceMarkTable URL into exact (race_date, baba_code, race_no).
2. Locate the unique HorseMarkInfo history table by its ordered labelled heading family (年月日, 競馬場, R,
   競走名, 格組, ..., 差, 体重, 騎手). In its data rows, canonicalize each official RaceMarkTable navigation anchor and
   select exactly one with that complete race identity. Zero/multiple match is validation failure; JRA row is
   unsupported.
3. HorseMarkInfo page lineage, selected history-row horse context, and exactly one RaceMarkTable row-local
   a.horseName[href] must all equal the target lineage. The RaceMarkTable response independently validates its official
   h4/active-course structure and full URL race identity.
4. History-link and RaceMarkTable race identity must agree exactly on date, baba code, and race number.

The only accepted chain is:

    target lineage == HorseMarkInfo lineage == selected history-row lineage == RaceMarkTable row lineage
    selected history link race identity == RaceMarkTable URL race identity

The frozen provider record ID is:

    nar:result:{YYYYMMDD}:{k_babaCode}:{k_raceNo}:horse:{k_lineageLoginCode}

## Evidence and Replay Causality

The record has exactly two distinct underlying responses:

| evidence role | response | availability / observation |
| --- | --- | --- |
| historical_race_context | HorseMarkInfo | URL and SHA-256 of its exact body; available_at=None; preserve supplied observed_at |
| historical_race_result | RaceMarkTable | URL and SHA-256 of its exact body; available_at=None; preserve supplied observed_at |

NAR requires two distinct (canonical_source_url, response_sha256) identities even though generic c1a permits one or
two. Evidence timestamps are neither selected nor aggregated. A raw-byte change changes its response SHA and the
past-race source ID; timestamp-only change does not change source ID.

HISTORICAL_REPLAY_CAPTURE_REQUIREMENT = REQUIRED. Current live pages cannot be presented as historical-cutoff
evidence. Live use needs capture before cutoff; replay needs trusted causally observed bytes. Fixture timestamps prove
tests only, never historical availability.

## Field Authority Matrix

| field(s) | authority and exact rule | cross-check / unsupported state |
| --- | --- | --- |
| race_date, place | RaceMark URL; unique active course plus compact h4 place | history row/h4 must agree |
| race_name, race_class | HorseMarkInfo selected-row 競走名, 格組; exact NFC nonempty text | RaceMark h3, subtitle, sponsor text never substitutes |
| distance_m, track, weather, track_condition | RaceMark unique race facts: surface, positive NNNm, 天候：, 馬場： | exact history-side fact agrees when present |
| finish | RaceMark matched row, positive decimal token | normal completed state only |
| reference_time_difference_seconds | HorseMark selected-row direct 差, finite nonnegative Decimal, no float | literal displayed zero accepted; RaceMark 着差 is ignored |
| race_time | RaceMark matched row, nonempty NFC official time | direct history time agrees where present |
| weight, weight_diff | RaceMark body weight digits(sign digits), e.g. 495(1), as Decimal | assigned race weight forbidden; 計不/blank/other grammar unsupported |
| jockey | RaceMark jockey anchor name excluding affiliation span; NFC; allowance symbol retained if name text | normalized history jockey agrees |
| popularity, odds | RaceMark positive integer / direct positive Decimal | blank, zero, special or abnormal token unsupported |
| passing_order | RaceMark row-local コーナー通過順, exact NFC display | no global-order synthesis |
| fourth_corner_position | matched row’s fourth component only where same page’s 全馬コーナー通過順 proves label-compatible [1,2,3,4] or [3,4] and includes ４コーナー | missing/count-mismatch/ambiguous token is unsupported |

Any directly comparable cross-page disagreement is validation failure. RaceMarkTable 着差 labels/fractions are never
converted to seconds. The initial subset uses only ordinary flat NAR results; ばんえい is unsupported because corner
and condition semantics are not proven equivalent.

## Support and Error Policy

NORMAL_COMPLETED_NAR_RESULT_ONLY requires the complete two-page chain, every required direct field, completed numeric
finish/popularity/odds, valid body weight, direct HorseMarkInfo difference, and proven fourth corner.

Unsupported: JRA history, ばんえい, cancellation/exclusion/stopped/disqualification/ambiguous demotion, no time/odds,
missing class/difference/body weight, nonnumeric result values, absent or ambiguous fourth corner, all absence claims,
pagination, and acquisition. NarHistoricalInputSourceValidationError owns malformed/contradictory supplied evidence,
URLs, tokens, duplicate/zero matches, and cross-page disagreement. NarHistoricalInputSourceUnsupportedError owns
recognized valid but excluded official page/result variants. No broad wrapping.

## Future Tests and Files

The future dedicated suite must pin public signature/non-export; pair cardinality; response/UTF-8/page/URL rules;
host preservation; raw SHA; identity chains; JRA rejection; provider ID; two roles; every authority/cross-check;
winner literal zero; ignored RaceMark margin; body vs assigned weight; jockey/odds/popularity; passing/fourth-corner
proof; ambiguity/abnormal states; timestamp preservation; source-ID raw-byte sensitivity and timestamp stability; no
name fallback/HTTP/DB/filesystem/clock/legacy parser; c1a propagation; c1c assembly with valid track/entry/jockey/odds;
and builder rejection for either evidence observed after capture/cutoff.

Expected implementation files only:

    scripts/simulation/nar_historical_past_race_source.py
    tests/test_nar_historical_past_race_source.py
    tests/fixtures/nar/horse_mark_info_past_race_context.html
    tests/fixtures/nar/race_mark_table_past_race_result.html
    docs/CURRENT_PHASE.md
    docs/LATEST_CODEX_REPORT.md

The fixtures must be one authentic ordinary-NAR pair, minimized only outside selected official rows, with a direct
numeric difference, completed result, numeric odds, body-weight change, row-local passing order, page corner labels,
nonempty class, and pinned race/lineage IDs. Fixtures are not added in PREPARE.

## Frozen Non-changes and Stop Condition

No c1a/evidence/c1b/builder/SQLite/migration/schema/package-root/parser/provider/CLI/database/log change is expected.
NAR_PAST_RACE_ABSENCE = UNSUPPORTED; pagination and fetch/acquisition orchestration are out of scope.

Recommended next phase: 4C-2d3b1i6c1d3b2a — NAR historical past-race pair normalizer implementation. Trusted
capture/acquisition and multi-race orchestration are separate later work.

Stop at DRAFT_FOR_REVIEW. Do not implement the normalizer, capture or commit fixture HTML, or begin acquisition.
