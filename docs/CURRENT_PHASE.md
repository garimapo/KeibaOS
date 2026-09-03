# Current Phase

Status: `APPROVED_FOR_COMMIT`

## Identity and authority

- Phase: `POST_V0_8_DAILY_REPLAY_8`
- Name: `JRA Daily Target Source Contract Qualification`
- Phase type: `RESEARCH_AND_DESIGN_ONLY`
- Base Commit: `57c78dc486e715535ea1f30e7c31db0f77597969`
- Branch: `feature/post-v0.8-daily-replay`
- Outcome: `BLOCKED`
- Implementation contract: `NOT_FROZEN`
- Production/test/fixture implementation or materialization: `NOT_AUTHORIZED`
- Stage/commit/push and `EXECUTE_APPROVED_PHASE`: `NOT_AUTHORIZED`

Authority is AGENTS.md and the approved Phase 7 design at the Base Commit, with
its Phase 2-6 dependencies unchanged. Phase 7 was committed and pushed normally;
local HEAD and fetched remote HEAD both equal the Base Commit. This document records
only Phase 8 qualification findings and unresolved gates, not replacement contracts.

## Objective, boundary, and outcome

Qualify only the eight Phase 7 implementation blockers against exact official source
responses. Research used public JRA responses and repository inspection; no production,
test, fixture, dependency, schema, database, archive, NAR, or shared-domain file changed.
Research response bytes and PDF render/text diagnostics remain outside the repository.

The source families are usable research candidates, but an implementation-safe composite
contract is NOT frozen. Strict PDF decoding/layout remains unqualified, and the supplied
accessS search/month navigation reveals an explicit Phase 7 capture-contract gap.
The phase stops for ChatGPT review rather than modifying that approved contract.

| Qualification target | Finding at this stop | Freeze state |
| --- | --- | --- |
| Year-program HTML/source/link | Exact year, panel, label and supplied href structure identified in 2020/2024 bytes | Candidate lexical structure documented; not a universal grammar |
| OFFICIAL_YEAR_PROGRAM_SCHEDULE_VERSION | Unique ordinary label in 2024; explicit April 6 revised label in 2020 | Approved unique-label rule unchanged; concrete spellings recorded |
| Nittei PDF | Calendar visually legible; deterministic text identity/font mapping and cell grammar unresolved | BLOCKED |
| Bangumi PDF | Explicit year/meeting/day/race columns visible; strict all-cell, annotation and multi-page grammar incomplete | BLOCKED |
| accessS month selection | Official select values plus source-owned JavaScript expression/tail table, not a literal historical-month CNAME link | Review required; not frozen |
| accessS meeting/race selection | Exact dated meeting links and complete table structure identified in four meeting responses | Candidate all-row grammar documented |
| Exact displayed start | Unique result-header selector and Japanese time lexeme identified for four 1R pages | Narrow selector/meaning documented; not a complete-day fixture contract |
| Official-byte fixtures/provenance | 21 research responses hashed; 19 partial candidates and 2 off-target controls | No complete acceptance/failure fixture set frozen; repository fixtures 0 |

No `IMPLEMENTATION_CONTRACT_FROZEN` outcome is claimed. There is no support expansion
for zero, cancellation, substitute, or partial dates.

## Official sources and representative scope

Primary pages inspected were [2024 year program](https://www.jra.go.jp/keiba/program/2024/)
and [2020 year program](https://www.jra.go.jp/keiba/program/2020/). Their own links supplied
the nittei and first Nakayama/Kyoto bangumi PDFs, and the official accessS search entry.
No PDF path or race identity was derived from its filename.

Ordinary-date research sampled 2024-01-06 and 2020-01-05, each with exact first-day
Nakayama and Kyoto meeting responses and their supplied first-race result links.
The month responses and PDFs were inspected, but only 1R result pages were acquired
for these four meetings. This is NOT a complete ordinary-day acceptance fixture bundle.

Two additional response bytes are for Kokura 2024-01-28, not 2024-01-06. A research
substring-date filter initially admitted the meeting because its meeting-day fields
contained similar digits. Exact anchored date-field validation identified the error.
Those bytes are retained only as off-target negative controls, with their real
request/date identities in the inventory; they never contribute to the candidate
2024-01-06 set. The temporary source filenames retain the original misleading date;
proposed fixture names reflect their true request date. Filenames never confer identity.

The exact official request and parent-navigation records are listed below. Search
snippets, third-party pages, PDF totals, and visually contiguous numbers are not evidence
of completeness.

## Year-program HTML and schedule-version candidate grammar

Both acquired HTML pages decode strictly as CP932. A future grammar must validate
charset/source agreement; replacement decoding and guessed alternate encodings are
not allowed. HTTP supplied `text/html`, without a charset parameter.

Observed selectors and lexical contexts:

- `#contentsBody > div.about_program`: unique year heading under
  `div.contents_header > h2`, e.g. `2024年度　競馬番組について`.
- `#main_program`: unique `h3.sub_header` with `開催日割・競馬番組等`;
  its `div.content > ul.link_list.multi.div2.center > li > a[href]` contains
  `span.inner > span.txt`. The child PDF-size `span.opt` is separate from
  the formal label.
- Exact schedule-label core: `開催日割表` (2024), or
  `開催日割表（2020年4月6日変更版）` (2020). The observed revised label
  uniquely identifies the supplied schedule version; acquisition time, HTTP
  Last-Modified, filename, and link position do not choose an operative version.
- `#seasons_program > div.panel > h3.sub_header` supplies season context;
  its link-list anchor text supplies meeting context such as `1回中山` or
  `1回京都`. The raw href is the locator authority.
- Other actual labels split a meeting by explicit day ranges. A parser cannot assume
  one season link or one PDF covers a whole meeting without reading that context.

The existing unique formal label/version rule is preserved. No arbitrary revision
ordering or fallback label is introduced. Full strict validation of duplicate sections,
unknown link variants and split-meeting coverage is not implemented or globally frozen.

## PDF findings and unresolved lexical/layout grammar

Research downloaded six exact PDFs, rendered them without OCR, and examined extracted
text/character geometry. The 2024 nittei and Nakayama/Kyoto bangumi first pages and the
2020 nittei were visually inspected alongside text diagnostics. Visual reading establishes
research observations, not a machine-normalization contract.

Nittei specifics:

- 2020 is one 595 x 842 point page; 2024 is one approximately 668.97 x 915.6 point
  page. Both have a month/day calendar grid, abbreviated venues, meeting numbers,
  and annotations. Blank cells and printed totals cannot prove a supported zero day.
- The inspected embedded CID fonts lack ToUnicode mappings. Text extraction with
  available pdfplumber/pdfminer, pypdf, and PDFium leaves CID tokens or incorrect
  characters in relevant content. `(cid:16093)` is one observed unresolved token.
- Font resources include Adobe Identity and Adobe Japan1 families; a deterministic,
  reviewed mapping/resource contract for every identity-bearing glyph is missing.
  This is not a claim that decoding is impossible. It is a concrete absence of a
  verified decoding contract in this phase.
- Cross-year calendar geometry, annotation ownership, and exact meeting/day
  association are not frozen. The page cannot be normalized by recognizing its
  filename or by reconstructing meeting-day sequence from dates.

Bangumi specifics:

- The sampled PDFs each have two pages: a race-program table and conditions/notes.
  The first-page heading explicitly binds year, meeting number and venue; day columns
  explicitly bind meeting-day labels and calendar dates.
- Race-number cells are interleaved with race-condition cells, not sorted race order.
  In the 2024 Nakayama first-day column the displayed race-number sequence is
  3, 4, 1, 2, 5, 7, 10, 6, 8, 12, 9, 11. Printed totals cannot replace reading these cells.
- The candidate parser must distinguish the actual race-number columns from money,
  distances, category counts, annotations and footers, and positively account for
  every page and relevant cell. A global digit regex or automatic table extraction
  without structural validation is insufficient.
- A versioned geometry/text grammar across the acquired layouts, including note-page
  recognition and split-day PDF coverage, has not been frozen.

Research tools included pdfplumber 0.11.9, pypdf 6.10.0 and PDFium rendering from the
bundled workspace runtime. Repository dependency requirements do not currently provide
a reviewed PDF extraction stack. No dependency was installed or changed for production.
A future review must select/pin the parser, font resources and layout-version rules
before implementation. OCR and manual glyph guesses are not alternatives.

## accessS source observations and contract review gate

The year page supplies the exact root action:

```text
doAction('/JRADB/accessS.html', 'pw01skl00999999/B3');return false
```

The actual form submission uses POST to
`https://www.jra.go.jp/JRADB/accessS.html` with the lower-case field `cname`.
The response contains `select#kaisaiY_list`, `select#kaisaiM_list`,
a `setParameter` function, and an exact `objParam` tail table.

For historical month selection, the supplied source expression combines the selected
year/month with its literal prefix and its own table tail. The two observed selections
were `pw01skl10202401/B3` and `pw01skl10202001/83`; the tail values were read
from the response, never predicted. The source also contains a `yearMonth` branch
discriminator. That value is navigation metadata, not historical availability,
prediction time, or snapshot causality. Research followed the source expression without
executing arbitrary JavaScript; this does NOT authorize a production date-to-CNAME builder.

There are two linked review questions:

1. Phase 7 explicitly requires captured accessS root/search evidence but its exact
   closed page-kind list omits a root/search kind. This phase does not silently add a
   kind, relabel that response as a month, or widen an existing capture repository.
2. The historical month is not supplied as one literal full CNAME link in the search
   response. Admitting a strict source-owned expression requires an explicitly reviewed
   authority/provenance contract consistent with Phase 7's no-manufactured-CNAME rule.
   Hard-coding the observed prefix/tail formula is not that contract.

Consequently capture/request canonical-byte identity is not frozen around an invented
root kind. These conflicts are returned to ChatGPT review.

### Candidate month-to-meeting and meeting-to-race structure

Observed month structure is `#past_result > ul.past_result_line > li >
div.past_result_line_unit`. Each `.head > h3.sub_header` binds the exact day text;
`.cell.kaisai` supplies meeting anchors. Adjacent graded-race cells are not the meeting
denominator. Empty layout slots are not automatically missing meetings.

Each raw meeting `onclick` must match one exact supplied accessS action; its full final
date field, year, venue, meeting and meeting-day fields must agree with the parent day
and visible label. Substring/date containment is forbidden. Exact observed tokens and
labels are preserved in the request inventory.

A meeting response has `div.race_select > table#race_list`. Its unique direct header
row has eight columns in order: `race_num, race_name, mov, dist, course, num, odds, win5`.
Every direct body row has a `th.race_num[scope=row]` with one supplied result href
and a race-number image alt, followed by the corresponding seven data cells.
The raw href is an accessS result request, not the separate accessO odds request.
Every row must be classified/validated; unknown, missing, duplicate or contradictory
rows reject the date. Each inspected ordinary meeting had twelve body rows; this
observation is NOT a fixed-count completeness rule.

Existing `JRAExternalRaceIdentity`/resolved accessS result-URL parsing remains reusable
to validate supplied identities. Existing accessD known-race discovery does not replace
this month/day coverage boundary.

## Exact displayed-start selector and semantics

The candidate selector is the unique `#race_result .race_header > .left >
.date_line > .inner`. Its `.cell.date` binds the actual calendar date and meeting;
its sibling `.cell.time` contains the literal `発走時刻：` and one
`strong` time value. The same header's race-number image alt must agree with the
supplied external race identity.

Observed lexical examples are `10時05分`, `9時50分`, `9時55分`,
and `10時10分`. The bounded candidate time lexeme is:

```text
(?:[0-9]|1[0-9]|2[0-3])時[0-5][0-9]分
```

The date must come from the independently validated result header, with aware JST
conversion. Duplicate time cells, absent/ambiguous date or race, extra semantic time
text, and identity disagreement are not accepted by the candidate grammar.

| Ordinary source sample | Official historical displayed start |
| --- | --- |
| 2024-01-06, 1回中山1日, 1R | 10:05 JST |
| 2024-01-06, 1回京都1日, 1R | 09:50 JST |
| 2020-01-05, 1回中山1日, 1R | 09:55 JST |
| 2020-01-05, 1回京都1日, 1R | 10:10 JST |

This is precisely Phase 7's official historical displayed-start meaning. Research does
not prove it is an unchanged original pre-race announcement or actual off-time.
The [official result-page help](https://www.jra.go.jp/JRADB/mikata/result.html) did not
supply that stronger guarantee. No stronger semantics, planned PDF time substitution,
delay/exception support, or time-availability claim is introduced. Only four sampled
1R pages were checked; the all-race fixture/selector gate is still open.

## Research byte inventory and provenance

Research root, outside both repositories:

```text
C:\Users\garim\AppData\Local\Temp\keiba-phase8-jra-24517bdcf7524eedb5bf7c7f2db7cc95
```

The sanitized `candidate-provenance.json` in that directory has SHA-256:

```text
bff17dec9bb3f65b5265adf000eeeed956283b52f83029f135840789ef666ad8
```

It records exact method/URL/form, parent source/href/action, raw byte length and digest,
honest requested/observed timestamps, response media/encoding metadata, and proposed
paths. All 21 response lengths and SHA-256 values were checked against that inventory.
No provider_available_at was established; HTTP Date/Last-Modified are not substitutes.

The following names are only proposed basenames under
`tests/fixtures/historical_daily_targets/official/jra/`; NONE was materialized there.
The two 20240128 controls are not acceptance-day evidence. All timestamps below are
2026-09-03 UTC; they are honest research acquisition times, not the historical target
date. These timestamps cannot be reused as formal bundle observed_at or enter
prediction/snapshot/settlement causality. Raw research bytes are not formal replay
dataset evidence, and no later materialization is authorized by this document.

| Proposed basename | Bytes | SHA-256 | Requested / observed time (UTC) |
| --- | ---: | --- | --- |
| `year_program_2024.html` | 79156 | `7b73fff9e0873fe1f056a50ccb49d1f85d742c16175b8bfe955eacc059e23b62` | `11:22:50.260905+00:00` / `11:22:50.600172+00:00` |
| `nittei_2024.pdf` | 443138 | `bc4a22849b33215bc9f1c127735654080c69b886b41b82d24f969197b4c553d1` | `11:23:06.973583+00:00` / `11:23:07.288932+00:00` |
| `bangumi_nakayama1_2024.pdf` | 117394 | `2cf7cba2265a00d1cdabb7f7ccdfc1682a7c033525a33c3d5882b249d509bd3a` | `11:23:07.292003+00:00` / `11:23:07.610101+00:00` |
| `bangumi_kyoto1_2024.pdf` | 127671 | `6149a6e4cb96554b142b2e2800eef46238a7321ff034ff2ff1829038e81a9139` | `11:23:07.612927+00:00` / `11:23:07.931729+00:00` |
| `accesss_search.cp932.html` | 75284 | `2af30f0f2dc1799ed8c2008c95e4550410669e178396dfea67dd2d341809a8fb` | `11:23:07.940612+00:00` / `11:23:08.184216+00:00` |
| `year_program_2020.html` | 79807 | `5373bb6574b97713c215cab16fbc8686e3794d06f4e13fc15e609b7ee77fdb53` | `11:23:08.186372+00:00` / `11:23:08.480770+00:00` |
| `nittei_2020.pdf` | 46902 | `2a4d09505de286a574f760b9a4b386baf65734fa273d621f279ed7330bacc139` | `11:23:08.526533+00:00` / `11:23:08.826077+00:00` |
| `bangumi_nakayama1_2020.pdf` | 508250 | `fa7ab3e6a38c7d3ab1de717af85594b44f4be02c17e143a32bc8dc7d4201928d` | `11:23:08.828955+00:00` / `11:23:09.105556+00:00` |
| `bangumi_kyoto1_2020.pdf` | 523275 | `301752db3d02846b29f9b87bb643edf499ccb0a02785e95313063ea06ed50f4c` | `11:23:09.108409+00:00` / `11:23:09.411964+00:00` |
| `accesss_month_202401.cp932.html` | 87662 | `7abbc350e7f16226304ba5b8f22e154f4b3edcba7b08247a0047f1da256eb359` | `11:24:57.604354+00:00` / `11:24:57.936977+00:00` |
| `accesss_meeting_20240106_06.cp932.html` | 79722 | `56a472cae9ba88d924167e1402d11c52146488fbeae230fc061d25d68c00fb88` | `11:24:57.984261+00:00` / `11:24:59.080405+00:00` |
| `accesss_result_20240106_06_01.cp932.html` | 97048 | `01fa8c6674d47aef7291145430fcbf0e2ffae15fcdb11a32f96443908c06e9b5` | `11:24:59.121160+00:00` / `11:24:59.613348+00:00` |
| `accesss_meeting_20240106_08.cp932.html` | 79397 | `5981dada3867a9d6e3d977324c8aadb9cdda9f71e657e7f6f09fc58a96815be6` | `11:24:59.667356+00:00` / `11:25:00.037908+00:00` |
| `accesss_result_20240106_08_01.cp932.html` | 97867 | `bfe8e52f47e2a6003e6821feb5b3175c8bafd1dfeba08b616fcd8422db650a83` | `11:25:00.078568+00:00` / `11:25:00.626587+00:00` |
| `accesss_meeting_20240128_10.cp932.html` | 78169 | `579b23a5386cccd3cafbb2c0475bc7e08382dd7d110a1afe1fadb9790d7668b1` | `11:25:01.009760+00:00` / `11:25:01.383585+00:00` |
| `accesss_result_20240128_10_01.cp932.html` | 91454 | `fac28498c34a3a7ea86593a672b988e7961cd011d62ca30e7ea932bff0a6557b` | `11:25:01.425562+00:00` / `11:25:01.996585+00:00` |
| `accesss_month_202001.cp932.html` | 86652 | `80c8e6c96224597cc3fb2702a4dd29e37eed4a65f5825e735007b25240442270` | `11:25:02.193237+00:00` / `11:25:02.922895+00:00` |
| `accesss_meeting_20200105_06.cp932.html` | 77576 | `0a739fcd965f74bd64592e1e4bbf25bc1c5593c2ebdf5b456e55b8ffbc2ce1f0` | `11:25:02.967325+00:00` / `11:25:03.900307+00:00` |
| `accesss_result_20200105_06_01.cp932.html` | 94243 | `0ca56ade1accc552f6244c4bbdc17d9bd31c206a63233b50ad1252658137eeac` | `11:25:03.943863+00:00` / `11:25:04.463082+00:00` |
| `accesss_meeting_20200105_08.cp932.html` | 77771 | `d928143492d2b413d457626cfa9a75ff89273dac9248abeea261f36e2453b5fe` | `11:25:04.519491+00:00` / `11:25:05.623671+00:00` |
| `accesss_result_20200105_08_01.cp932.html` | 94893 | `2e12cfef5b2597450806a502c53c55eb8ed66e8cd7ee6dc1224c40a5ff298df9` | `11:25:05.671817+00:00` / `11:25:06.443384+00:00` |

### Exact request / parent-reference inventory

This documents acquired source identity, not a recipe for rebuilding locators from
filenames or historical dates. A response's supplier reference traces to the exact
parent bytes above. Candidate monthly expression records describe research only and
remain subject to the root/month review gate.

| Proposed basename | Actual request | Source supplier |
| --- | --- | --- |
| `year_program_2024.html` | GET `https://www.jra.go.jp/keiba/program/2024/` | official historical year-program page identified in Phase 4 research |
| `nittei_2024.pdf` | GET `https://www.jra.go.jp/keiba/program/2024/pdf/nittei.pdf` | {"label":"開催日割表（PDF：433KB）","name":"year_program_2024.html","raw_href":"/keiba/program/2024/pdf/nittei.pdf"} |
| `bangumi_nakayama1_2024.pdf` | GET `https://www.jra.go.jp/keiba/program/2024/pdf/bangumi/nakayama1.pdf` | {"label":"1回中山（PDF：115KB）","name":"year_program_2024.html","raw_href":"/keiba/program/2024/pdf/bangumi/nakayama1.pdf"} |
| `bangumi_kyoto1_2024.pdf` | GET `https://www.jra.go.jp/keiba/program/2024/pdf/bangumi/kyoto1.pdf` | {"label":"1回京都（PDF：125KB）","name":"year_program_2024.html","raw_href":"/keiba/program/2024/pdf/bangumi/kyoto1.pdf"} |
| `accesss_search.cp932.html` | POST `https://www.jra.go.jp/JRADB/accessS.html`; form {"cname":"pw01skl00999999/B3"} | {"name":"year_program_2024.html","onclick":"doAction('/JRADB/accessS.html', 'pw01skl00999999/B3');return false"} |
| `year_program_2020.html` | GET `https://www.jra.go.jp/keiba/program/2020/` | official historical year-program page identified in Phase 4 research |
| `nittei_2020.pdf` | GET `https://www.jra.go.jp/keiba/program/2020/pdf/nittei.pdf` | {"label":"開催日割表（2020年4月6日変更版）（PDF：46KB）","name":"year_program_2020.html","raw_href":"/keiba/program/2020/pdf/nittei.pdf"} |
| `bangumi_nakayama1_2020.pdf` | GET `https://www.jra.go.jp/keiba/program/2020/pdf/bangumi/nakayama1.pdf` | {"label":"1回中山（PDF：497KB）","name":"year_program_2020.html","raw_href":"/keiba/program/2020/pdf/bangumi/nakayama1.pdf"} |
| `bangumi_kyoto1_2020.pdf` | GET `https://www.jra.go.jp/keiba/program/2020/pdf/bangumi/kyoto1.pdf` | {"label":"1回京都（PDF：512KB）","name":"year_program_2020.html","raw_href":"/keiba/program/2020/pdf/bangumi/kyoto1.pdf"} |
| `accesss_month_202401.cp932.html` | POST `https://www.jra.go.jp/JRADB/accessS.html`; form {"cname":"pw01skl10202401/B3"} | {"expression":"pw01skl10 + selected year/month + / + supplied table tail","name":"accesss_search.cp932.html","selector":"#kaisaiY_list/#kaisaiM_list + setParameter + exact objParam entry"} |
| `accesss_meeting_20240106_06.cp932.html` | POST `https://www.jra.go.jp/JRADB/accessS.html`; form {"cname":"pw01srl10062024010120240106/90"} | {"label":"1回中山1日","name":"accesss_month_202401.cp932.html","onclick":"return doAction('/JRADB/accessS.html', 'pw01srl10062024010120240106/90');"} |
| `accesss_result_20240106_06_01.cp932.html` | GET `https://www.jra.go.jp/JRADB/accessS.html?CNAME=pw01sde1006202401010120240106/21` | {"href":"/JRADB/accessS.html?CNAME=pw01sde1006202401010120240106/21","name":"accesss_meeting_20240106_06.cp932.html"} |
| `accesss_meeting_20240106_08.cp932.html` | POST `https://www.jra.go.jp/JRADB/accessS.html`; form {"cname":"pw01srl10082024010120240106/24"} | {"label":"1回京都1日","name":"accesss_month_202401.cp932.html","onclick":"return doAction('/JRADB/accessS.html', 'pw01srl10082024010120240106/24');"} |
| `accesss_result_20240106_08_01.cp932.html` | GET `https://www.jra.go.jp/JRADB/accessS.html?CNAME=pw01sde1008202401010120240106/B5` | {"href":"/JRADB/accessS.html?CNAME=pw01sde1008202401010120240106/B5","name":"accesss_meeting_20240106_08.cp932.html"} |
| `accesss_meeting_20240128_10.cp932.html` | POST `https://www.jra.go.jp/JRADB/accessS.html`; form {"cname":"pw01srl10102024010620240128/62"} | {"label":"1回小倉6日","name":"accesss_month_202401.cp932.html","onclick":"return doAction('/JRADB/accessS.html', 'pw01srl10102024010620240128/62');"} |
| `accesss_result_20240128_10_01.cp932.html` | GET `https://www.jra.go.jp/JRADB/accessS.html?CNAME=pw01sde1010202401060120240128/FB` | {"href":"/JRADB/accessS.html?CNAME=pw01sde1010202401060120240128/FB","name":"accesss_meeting_20240106_10.cp932.html"} |
| `accesss_month_202001.cp932.html` | POST `https://www.jra.go.jp/JRADB/accessS.html`; form {"cname":"pw01skl10202001/83"} | {"expression":"pw01skl10 + selected year/month + / + supplied table tail","name":"accesss_search.cp932.html","selector":"#kaisaiY_list/#kaisaiM_list + setParameter + exact objParam entry"} |
| `accesss_meeting_20200105_06.cp932.html` | POST `https://www.jra.go.jp/JRADB/accessS.html`; form {"cname":"pw01srl10062020010120200105/01"} | {"label":"1回中山1日","name":"accesss_month_202001.cp932.html","onclick":"return doAction('/JRADB/accessS.html', 'pw01srl10062020010120200105/01');"} |
| `accesss_result_20200105_06_01.cp932.html` | GET `https://www.jra.go.jp/JRADB/accessS.html?CNAME=pw01sde1006202001010120200105/48` | {"href":"/JRADB/accessS.html?CNAME=pw01sde1006202001010120200105/48","name":"accesss_meeting_20200105_06.cp932.html"} |
| `accesss_meeting_20200105_08.cp932.html` | POST `https://www.jra.go.jp/JRADB/accessS.html`; form {"cname":"pw01srl10082020010120200105/95"} | {"label":"1回京都1日","name":"accesss_month_202001.cp932.html","onclick":"return doAction('/JRADB/accessS.html', 'pw01srl10082020010120200105/95');"} |
| `accesss_result_20200105_08_01.cp932.html` | GET `https://www.jra.go.jp/JRADB/accessS.html?CNAME=pw01sde1008202001010120200105/DC` | {"href":"/JRADB/accessS.html?CNAME=pw01sde1008202001010120200105/DC","name":"accesss_meeting_20200105_08.cp932.html"} |

The external inventory is temporary research material, not a durable archive contract.
Its hash and the records above preserve the audit facts, but a later reviewed fixture
materialization still needs available matching bytes. Reacquisition is not assumed
byte-identical. A changed response SHA cannot silently replace a reviewed candidate.

## Remaining blockers and stop condition

1. Resolve deterministic nittei glyph decoding and strict versioned calendar layout;
   freeze bangumi all-cell/page/day binding and a reviewed extraction dependency/resource
   contract. Do not infer PDF identities or use OCR.
2. Obtain review of the root/search capture-kind gap and exact source-owned month
   selection semantics. No unilateral change to Phase 7 page kinds or CNAME authority.
3. After those gates, complete and independently review one whole ordinary composite
   fixture set, all-race start validation, and required fail-closed case fixtures.
   The current partial samples do not satisfy the implementation fixture gate.
4. Freeze future request/capture canonical bytes only against the resolved request
   contract: version, fixed fields/order, exact raw request and parent-reference
   representation, datetime/UTF-8 rules and response digest. Reuse the unchanged shared
   target-set digest; no accidental serialization or implementation is approved here.

Stop now with `Outcome: BLOCKED`, `Status: DRAFT_FOR_REVIEW`, and no
implementation authorization. Future `SUPPORTED_COMPLETE_DAY` cannot be returned
for this unqualified composite. Existing whole-day failure remains
`TARGET_DISCOVERY_INCOMPLETE`. No next phase starts.

## Allowed Files

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Forbidden Files and actions

All other repository files, including production, NAR/shared domains, tests, fixtures,
requirements, SQLite/migrations/schema/database, logs, archives, CLI and release/tag
history. No implementation, fixture materialization, stage, commit, push, or execution
phase during this PREPARE. The old KeibaAI repository remains untouched.

## Required PREPARE verification

```text
git diff --check
git diff --name-only
git status --short
git diff --cached --name-only
```

Verify exactly the two Allowed Files changed and the index is empty. No unit or full
suite is required/run for this research/docs-only PREPARE; no code/test file changed.
