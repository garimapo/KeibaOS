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

d2 investigates whether one caller-supplied official NAR RaceMarkTable response can independently prove one c1a
`HistoricalInputSourceRecord(record_kind="past_race")` after the caller has supplied the frozen d1 target identity
`nar:horse:{k_lineageLoginCode}`. This is field-semantics and provenance design only. It does not normalize a page,
fetch HTTP, follow a horse link, inspect SQLite, alter c1a/c1b/c1c, or create past-race/absence records.

The investigation separates navigation evidence from normalized fact evidence. HorseMarkInfo may help a caller find a
historical page, but a future record may use the canonical historical RaceMarkTable URL as its sole fact provenance
only if that response itself proves the historical race, the exact horse, and every emitted value.

## Official Pages Inspected

Only official `https://www.keiba.go.jp` material was inspected. Representative completed pages were:

* `RaceMarkTable?k_babaCode=10&k_raceDate=2026%2F07%2F26&k_raceNo=8` (Morioka B2, dirt, numeric and textual
  margins, corner order present).
* `RaceMarkTable?k_babaCode=36&k_raceDate=2026%2F06%2F30&k_raceNo=2` (Monbetsu, 2-year maiden, fractions and
  `ハナ` margins).
* `RaceMarkTable?k_babaCode=3&k_raceDate=2026%2F07%2F26&k_raceNo=12` (Ban'ei variant, used only to establish
  unsupported variance).

The official HorseMarkInfo page for lineage `30077409996` links to the exact Morioka RaceMarkTable URL above. The
RaceMarkTable row itself contains the same official HorseMarkInfo lineage anchor; this is discovery evidence only and
is not proposed as additional provenance for normalized past-race facts.

## Historical Race URL and Identity Contract

The only candidate supported page kind is the exact path:

`/KeibaWeb/TodayRaceInfo/RaceMarkTable`

Its canonical URL must be absolute HTTPS on `www.keiba.go.jp`, with no credentials, fragment, control character, or
port other than absent/443. Its query is exactly one each of `k_babaCode`, `k_raceDate`, and `k_raceNo`; unknown,
duplicate, blank, plus-ambiguous, and malformed-percent values fail closed. `k_raceDate` is an actual canonical
`YYYY/MM/DD` date. `k_babaCode` and `k_raceNo` are lexical ASCII positive canonical decimal tokens
`[1-9][0-9]*`, without integer conversion or invented range limits. Canonical query order is:

`k_babaCode={code}&k_raceDate=YYYY%2FMM%2FDD&k_raceNo={number}`.

The canonical identity candidate is `nar:{YYYYMMDD}:{k_babaCode}:{k_raceNo}`. The future normalizer must cross-check
the URL date/race number with the one visible result `h4`; it must obtain semantic place from exactly one active course
selector and reject an h4 place mismatch. It must not infer place from a hard-coded baba-code table.

## Row-local Horse Identity

In normal completed result tables, each horse cell is `td.d.horseName` containing a HorseMarkInfo anchor. The exact
official link form observed is:

`/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=30077409996`.

A future boundary must require exactly one row-local HorseMarkInfo anchor with the already-frozen d1 path/query/token
contract, derive `nar:horse:{k_lineageLoginCode}`, and require exactly one result row equal to the caller-supplied
target `external_horse_id`. No matching row, multiple matching rows, malformed link, horse-name match, horse-number
match, or globally selected anchor fails closed. The row's identity therefore is independently present on the factual
RaceMarkTable response.

## Field Evidence Matrix

| c1a field | official RaceMarkTable evidence | status | frozen initial policy |
| --- | --- | --- | --- |
| `race_date` | canonical URL plus result `h4` | PROVEN | exact date, cross-checked; later require strictly before target date |
| `place` | active course selector plus compact h4 place cross-check | PROVEN | NFC display text; no baba-code lookup |
| `race_name` | no dedicated, nonempty semantic name node is present on ordinary B2 pages; `p.subTitle` can be empty/sponsorship text | CONTRACT_GAP | do not substitute subtitle or reuse class text |
| `race_class` | exactly one nonempty `section.raceTitle > h3` such as `Ｂ２` or `２歳牝馬　未勝利` | PROVEN for flat pages | preserve exact NFC structured class/condition text; never use `subTitle` |
| `distance_m` | first `dataArea` fact, surface plus `NNNm` | PROVEN for flat dirt/turf | positive lexical decimal to guarded int; no target-distance fallback |
| `track` | same data-area surface | PROVEN for `ダート`/`芝` | Ban'ei/other variant not coerced into this contract |
| `weather` | `天候：` in same facts node | PROVEN when present | required nonempty value; no default |
| `track_condition` | `馬場：` in same facts node | PROVEN when present | required nonempty value; no default |
| `finish` | row-local `td.a` | PROVEN for positive numeric completed result | 取消/除外/競走中止/失格/取止/blank/non-numeric are UNSUPPORTED |
| `margin` | row-local `td.l` | CONTRACT_GAP | winner is blank; other rows include numeric text, fractions, `ハナ`, `クビ`, and `大差`; no numeric mapping is frozen |
| `race_time` | row-local `td.k` | PROVEN for nonempty normal result | preserve required official text; no-time/abnormal row unsupported |
| `weight` / `weight_diff` | row-local `td.j.horseWeight`, observed `473(-1)` | PROVEN for exact `digits(sign?digits)` form | parse directly to Decimal; `計不`, `－`, blank, or a different grammar unsupported |
| `jockey` | row-local `td.h.jockeyName` anchor | PROVEN | direct rider text excluding affiliation span, matching committed NAR convention |
| `popularity` | row-local `td.o` | PROVEN for numeric completed result | exact nonnegative integer only; missing/abnormal unsupported |
| `odds` | row-local `td.p` | PROVEN for canonical numeric completed result | direct Decimal; historical row only, never target odds or legacy DB |
| `passing_order` | row-local `td.n.corner_position` | PROVEN when present | preserve exact NFC official sequence; no commentary/global-order synthesis |
| `fourth_corner_position` | no universal row-local fourth-corner value | CONTRACT_GAP | only a future exact four-position syntax may prove its final component; two-corner/absent variants are unsupported |

`race_name`, `margin`, and `fourth_corner_position` block a valid current c1a `past_race` even though the remaining
normal flat-race values are locally evidenced. c1a requires all three as nonempty text, Decimal, and nonnegative int
respectively. No production fallback, fabricated zero, symbolic-margin conversion, or title/class duplication is
authorized.

## Abnormal, Weight, Odds, and Corner Policy

The initial eventual normalizer may support only a completed flat result row with a positive numeric finish, nonempty
time, exact body-weight grammar, numeric popularity/odds, and a row-local HorseMarkInfo identity. It must reject
cancelled, excluded, stopped, disqualified, no-time, missing-weight, or ambiguous-column rows; it must not create
fake numeric finish, weight, weight difference, popularity, odds, or corner values.

Literal decimal-looking margins are provider text and are not an approved universal semantic conversion. Fractions,
`ハナ`, `アタマ`, `クビ`, and `大差` likewise remain unrepresented by the current Decimal contract. Passing order is
not a substitute for a fourth-corner value: a two-position sequence such as `9-6` proves only those displayed
positions. A future support subset may require exactly four explicit positive positions before taking the fourth;
otherwise it must fail closed.

Ban'ei remains UNSUPPORTED: its result pages use a different race model and omit the required flat-race corner and
margin semantics. Same-day multiple starts remain UNSUPPORTED for snapshot assembly because c1c orders only by
`race_date` and deliberately rejects same-date chronological ambiguity; provider race identity must not silently
become a chronology tie-breaker.

## Provider Record and Provenance Decision

The historical URL identity plus exactly one matching official horse identity is sufficient to identify one provider
horse-result row. Subject to later field-contract approval, the deterministic provider-record-ID candidate is:

`nar:result:{YYYYMMDD}:{k_babaCode}:{k_raceNo}:horse:{k_lineageLoginCode}`

It is based only on provider-native race identity and the row's validated provider-native horse identity. It is not a
URL alone, horse number, name, local ID, source ID, hash, or UUID. Duplicate matching rows or a URL/h4 disagreement
must fail closed.

SINGLE_RESPONSE_FACT_PROVENANCE is **INSUFFICIENT for a current c1a past_race**, but the insufficiency is field-domain
semantics (`race_name`, `margin`, and universal `fourth_corner_position`), not a second-page fact-provenance need.
The RaceMarkTable itself independently proves its URL race identity, matching lineage identity, and all values it
actually displays. Therefore `C1A_PROVENANCE_EXTENSION_REQUIRED = NO`: no multi-response provenance extension is
proposed. `observed_at` must remain the caller-supplied response timestamp; `available_at` is `None` unless an official
publication timestamp is separately proven. Past-race absence remains UNSUPPORTED because one result page cannot prove
complete zero-history/pagination scope.

## Support Matrix

| Case | status | reason |
| --- | --- | --- |
| normal completed flat RaceMarkTable identity and displayed row facts | NOT_PROVEN as a complete c1a record | three current field-contract gaps remain |
| positive numeric finish | SUPPORTED evidence | direct `td.a` only |
| abnormal finish/cancelled state | UNSUPPORTED | no fake positive integer |
| exact `weight(diff)` display | SUPPORTED evidence | Decimal grammar is direct |
| 計不 / － / missing weight | UNSUPPORTED | current c1a values cannot be inferred |
| simple decimal/integer-looking margin | NOT_PROVEN | no universal semantic mapping has been approved |
| ハナ / アタマ / クビ / fraction / 大差 margin | CONTRACT_GAP | current Decimal domain cannot preserve official semantic form |
| passing order with explicit four positions | NOT_PROVEN | future exact grammar still needs a dedicated contract decision |
| passing order absent or fewer than four positions | UNSUPPORTED | no provable `fourth_corner_position` |
| Ban'ei result | UNSUPPORTED | incompatible corner/margin race variant |
| same-date multiple start | UNSUPPORTED | c1c chronological ambiguity remains fail-closed |
| h3 race class/condition on flat page | SUPPORTED evidence | structured nonempty h3, not subtitle |
| dedicated nonempty race name on ordinary B2 page | CONTRACT_GAP | none was observed |
| `past_race_absence` | UNSUPPORTED | no complete official zero-history proof |

## Future API, Allowed Files, and Test Plan

No c1d production API, implementation module, or implementation Allowed Files are authorized while the three field
contracts remain unresolved. `NarSuppliedOfficialResponse` is not yet approved for reuse merely by convenience; any
later response type must make its RaceMarkTable page-kind semantics explicit. No package-root export is proposed.

After a field-contract decision, a future supplied-response normalizer must test exact response types/UTF-8, URL-only
page dispatch, URL/h4/place cross-checks, exactly one matching lineage row, provider-record-ID determinism, row-local
field ownership, historical-date-before-target enforcement, observed_at preservation, absence rejection, and source
purity (no HTTP, DB, filesystem, clock, legacy provider/parser, or package-root export). It must also test numeric and
abnormal finish, all supported/unsupported margin forms, weight grammar, odds/popularity, passing/fourth-corner
variants, same-day ambiguity, row permutation determinism, and unchanged c1a validation propagation.

## Recommended Next Phase and Stop Condition

Recommend **Phase 4C-2d3b1i6c1d3 — Historical past-race result-field contract preparation**. Its sole purpose is to
decide the provider-neutral representation/eligibility rules for `race_name`, official margin semantics, and
`fourth_corner_position`; it must not implement parsing, change provenance, or add past-race extraction. A later c1d
implementation PREPARE is blocked until that decision is approved.

Allowed Files for this PREPARE are exactly:

* `docs/CURRENT_PHASE.md`
* `docs/LATEST_CODEX_REPORT.md`

No production, test, fixture, migration, schema, database, provider, parser, CLI, README, package export, or original
workspace change is authorized. Stop at `DRAFT_FOR_REVIEW` for independent design review.

blocker: current c1a past_race requires semantic race_name, Decimal margin, and fourth_corner_position values that a
normal RaceMarkTable cannot universally prove without an approved field-contract decision.
