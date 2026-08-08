# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase

Phase 4C-2d3b1i6c1d2 — NAR historical RaceMarkTable field semantics preparation

## Base Commit

2b6d389b4296be2f6749b71fc4ed827f244ce570 feat: preserve NAR target horse identity

## Branch and Workspace

Formal branch: `feature/ver0.8-simulator`

Preparation review branch: `review/4c-2d3b1i6c1d2-prepare`

Canonical workspace: `C:\Users\garim\Desktop\KeibaAI-review-1i5b2b`

The original workspace, `C:\Users\garim\Desktop\KeibaAI`, is read-only for this phase.

## Objective and Boundary

d2 investigates whether a caller-supplied official NAR RaceMarkTable response can independently prove one c1a
`HistoricalInputSourceRecord(record_kind="past_race")` after the caller supplies the frozen d1 target identity
`nar:horse:{k_lineageLoginCode}`. This is field-semantics and provenance design only. It does not normalize a page,
fetch HTTP, follow a horse link, inspect SQLite, alter c1a/c1b/c1c, or create past-race/absence records.

HorseMarkInfo may help a caller discover historical pages, but it is navigation evidence. A later record can use the
canonical RaceMarkTable URL as its sole fact provenance only if that supplied response independently proves the
historical race, exact horse, and every emitted fact.

## Official URL and Horse Identity Findings

Only official `https://www.keiba.go.jp` material was inspected. The candidate page path is exactly
`/KeibaWeb/TodayRaceInfo/RaceMarkTable`. Canonical URLs are HTTPS on `www.keiba.go.jp`, no credentials, fragment,
control characters, or port other than absent/443, and exactly one each of `k_babaCode`, `k_raceDate`, and
`k_raceNo`. Unknown, duplicate, blank, plus-ambiguous, and malformed-percent values fail closed. The date is
canonical `YYYY/MM/DD`; numeric tokens are lexical ASCII `[1-9][0-9]*` without integer conversion or invented
range limits.

A future normalizer must cross-check URL date/race number with one result h4 and semantic place from exactly one active
course selector. In normal completed result tables, each `td.d.horseName` row contains the d1 HorseMarkInfo anchor.
The future boundary must require exactly one row whose `nar:horse:{k_lineageLoginCode}` equals the caller-supplied
target `external_horse_id`. Horse name, horse number, global anchors, and unverified navigation links cannot bind a
historical row. The RaceMarkTable response is therefore sufficient evidence for its observed row identity and facts.

## Field Evidence and Current Contract Gaps

| c1a field | observed RaceMarkTable evidence | status | d2 policy |
| --- | --- | --- | --- |
| `race_date` | canonical URL and result h4 | PROVEN | exact date; later require strictly before target date |
| `place` | active course selector and compact h4 cross-check | PROVEN | NFC display text; no baba-code lookup |
| `race_name` | h3 semantics vary; subtitle can be empty or sponsorship text | CONTRACT_GAP | no title/subtitle substitution or guessed split |
| `race_class` | the same h3 can be class-only, eligibility/condition-only, or combined named-race plus condition | CONTRACT_GAP | no class-code regex or display-text split |
| `distance_m` | data-area surface plus `NNNm` | PROVEN for flat dirt/turf | guarded positive lexical decimal to int |
| `track` | data-area surface | PROVEN for flat dirt/turf | incompatible variants are not coerced |
| `weather` / `track_condition` | data-area facts | PROVEN when present | exact nonempty values; no defaults |
| `finish` | row-local result-position cell | PROVEN for positive numeric completed result | abnormal/blank/non-numeric states unsupported |
| `margin` | row-local margin cell | CONTRACT_GAP | no approved Decimal semantics for all official display forms |
| `race_time` | row-local time cell | PROVEN for nonempty normal result | exact text; no-time unsupported |
| `weight` / `weight_diff` | exact body-weight display | PROVEN for exact grammar | direct Decimal parsing only |
| `jockey` | row-local jockey anchor | PROVEN | direct rider text excluding affiliation display |
| `popularity` / `odds` | row-local cells | PROVEN for numeric completed result | exact integer / direct Decimal |
| `passing_order` | row-local `td.n.corner_position` | PROVEN when present | exact NFC official display text |
| `fourth_corner_position` | row positions plus page `section.cornerPassTable` | NOT_YET_PROVEN | exact label-to-position mapping required |

`RACE_NAME_STATUS = CONTRACT_GAP` and `RACE_CLASS_STATUS = CONTRACT_GAP`. A h3 is not a one-to-one semantic
source: observed flat pages include class-only, eligibility/condition-only, and combined named-race plus
class/condition forms. Sponsor/prize text above h3 is not automatically a race name. No guessed split, class-code
regex, or subtitle substitution is approved.

This separation matters downstream. c1a and `HistoricalPastRaceSnapshot` require and digest both exact strings, and
persisted simulation input requires both. The ability engine consumes `race_class` for class scoring, so an arbitrary
title or condition cannot fill that field. No direct feature-engine consumer of `race_name` was found, but it remains
immutable persisted and digest-relevant content.

## Margin and Corner Policy

`MARGIN_STATUS = CONTRACT_GAP`. Literal decimal-looking margins, fractions, and Japanese textual margin forms are
provider display values; no universal conversion to the current c1a Decimal margin is approved.

`passing_order` remains exact NFC row-local display text. `FOURTH_CORNER_STATUS = NOT_YET_PROVEN` and
`CORNER_LABEL_MAPPING = NOT_YET_PROVEN`. The future contract must prove the relationship between positions in
`td.n.corner_position` and labels in the same response's `section.cornerPassTable`, including labels such as
`全馬コーナー通過順`, `3コーナー`, and `4コーナー`.

Two row positions can be sufficient only if the same response proves they are corners `[3, 4]`. Four can be
sufficient only if the same response proves `[1, 2, 3, 4]`. Missing labels, mismatched counts, absent corner 4, or
any ambiguous mapping fail closed. Row length, the last token, distance/course lookup, and legacy-parser behavior are
not substitutes.

Ban'ei is UNSUPPORTED. Abnormal finish, no-time, unavailable weight, missing odds/popularity, and ambiguous row columns
are unsupported. Same-day multiple starts remain unsupported because c1c rejects same-date chronology ambiguity.

## Provider-record and Provenance Decision

The historical URL identity plus exactly one matching official horse identity is sufficient to identify one provider
horse-result row. Subject to later complete field-contract approval, the provider-record-ID candidate is
`nar:result:{YYYYMMDD}:{k_babaCode}:{k_raceNo}:horse:{k_lineageLoginCode}`. It uses provider-native race and horse
identity only; it is not a URL alone, horse number, name, local ID, source ID, hash, or UUID.

`SINGLE_RESPONSE_SOURCE_EVIDENCE = SUFFICIENT_FOR_OBSERVED_FACTS`. The RaceMarkTable response independently proves
its URL race identity, matching lineage identity, and every value it displays. `CURRENT_C1A_RECORD_COMPLETENESS =
NOT_YET_PROVEN` because title/class, margin, and corner semantics are unresolved, not because another factual response
page is needed. Therefore `C1A_PROVENANCE_EXTENSION_REQUIRED = NO`. `observed_at` remains caller supplied and
`available_at` is `None` unless official publication semantics are separately proven.

`past_race_absence = UNSUPPORTED`: one result page cannot prove complete zero-history/pagination scope.

## Support Matrix

| Case | status | reason |
| --- | --- | --- |
| normal completed flat RaceMarkTable identity and displayed facts | NOT_PROVEN as complete c1a record | title/class, margin, and corner mapping gaps remain |
| h3 title/class/condition | CONTRACT_GAP | observed semantic families are not one-to-one with current fields |
| all observed margin forms | CONTRACT_GAP | current Decimal semantics unresolved |
| passing order with labels that prove corner 4 | NOT_YET_PROVEN | exact label-to-position contract required |
| absent, mismatched, or ambiguous corner labels | UNSUPPORTED | no provable fourth corner |
| Ban'ei result | UNSUPPORTED | incompatible variant |
| same-date multiple start | UNSUPPORTED | c1c chronology ambiguity remains fail-closed |
| `past_race_absence` | UNSUPPORTED | no complete official zero-history proof |

## Future Scope and Test Plan

No c1d production API, implementation module, or implementation Allowed Files are authorized while field contracts
remain unresolved. No package-root export, parser, provenance extension, or past-race extraction is proposed.

After field-contract approval, testing must cover exact supplied response types/UTF-8, URL-only page dispatch,
URL/h4/place cross-checks, exactly one matching lineage row, provider-record-ID determinism, row-local ownership,
historical-date-before-target enforcement, observed-at preservation, all relevant abnormal values, title/class cases,
margin cases, page-label/row-position corner cases, response permutation determinism, and unchanged c1a validation.

## Recommended Next Phase and Stop Condition

Recommend **Phase 4C-2d3b1i6c1d3 — Historical past-race result-field contract preparation**. Its sole design
responsibility is to decide:

1. `race_name` / `race_class` semantic separation;
2. margin domain representation; and
3. page corner-label to row-position mapping for `fourth_corner_position`.

d3 must not implement parsing, add past-race extraction, or extend provenance. A later c1d implementation PREPARE is
blocked until d3 is approved.

Allowed Files for this PREPARE are exactly:

* `docs/CURRENT_PHASE.md`
* `docs/LATEST_CODEX_REPORT.md`

No production, test, fixture, migration, schema, database, provider, parser, CLI, README, package export, or original
workspace change is authorized. Stop at `DRAFT_FOR_REVIEW` for independent design review.

blocker: race_name/race_class semantic separation, margin domain representation, and exact corner-label-to-row-position
mapping for fourth_corner_position remain unresolved.
