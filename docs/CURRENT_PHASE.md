# Current Phase

Status: `APPROVED_FOR_COMMIT`

## Identity and authority

- Phase: `POST_V0_8_DAILY_REPLAY_9`
- Name: `JRA Daily Target Source Gap Resolution`
- Phase type: `RESEARCH_AND_DESIGN_ONLY`
- Base Commit: `58750303a5fca21c2e2fcea7dd13b74b1aa76b93`
- Branch: `feature/post-v0.8-daily-replay`
- Outcome: `BLOCKED`
- Implementation contract: `NOT_FROZEN`
- Production/test/fixture implementation or materialization: `NOT_AUTHORIZED`
- Stage/commit/push and `EXECUTE_APPROVED_PHASE`: `NOT_AUTHORIZED`

Phase 8's approved `BLOCKED` result, Phase 2-7 contracts and AGENTS.md remain
authoritative. This phase investigates only Phase 8's four identified gaps. It neither
broadens the JRA supported profile nor changes NAR or the shared daily-target domain.

## Purpose and stop result

The intended outcome is only `IMPLEMENTATION_CONTRACT_FROZEN` or `BLOCKED`.
Research resolves substantially more of the accessS actual-history side, but does not
resolve deterministic PDF extraction/layout. It also exposes an approved-Phase-7
capture-kind/authority gap for accessS root-to-month navigation. Therefore this PREPARE
stops as `BLOCKED`. No implementation contract is inferred from a partial result.

| Priority | Result | State |
| --- | --- | --- |
| 1. nittei/bangumi PDF text extraction/layout | Available deterministic libraries fail to produce identity-safe text; no approved font/CMap/layout contract | BLOCKED |
| 2. accessS root/month capture/request | Exact parent relation observed, but root/search response is not in Phase 7's closed daily page-kind set and month selection is a supplied expression, not literal href | REVIEW GATE |
| 3. accessS meeting/race selection | Full all-row evidence validated for four ordinary meetings | Candidate grammar recorded; dependent on priority 2 |
| 4. scheduled-start selector | Full all-row result set validates one strict selector and header/date/identity relationship | Candidate grammar recorded; dependent on composite |
| 5. official-byte candidate set | 65 unique proposed paths / 69 capture records, including 48 full ordinary result pages | Not materialized; planned/PDF and fail-closed fixture gates remain |

Research responses are parser research material only, not formal historical replay
evidence. Honest research timestamps are never backdated and never become a bundle
`observed_at`, provider availability, scheduled start, prediction, snapshot, or
settlement causal field.

## PDF extraction and layout result

Exact supplied 2020/2024 nittei and first Nakayama/Kyoto bangumi PDF bytes from Phase 8
were retained outside the repository and rendered visually without OCR. The PDFs visibly
contain the expected calendar and program tables, but visual appearance cannot supply a
normalization grammar.

The bundled runtime was tested with pypdf 6.10.0 and pdfplumber 0.11.9. Pypdf's nittei
output contains mojibake in identity-bearing Japanese text. Pdfplumber output renders
many relevant values as `(cid:...)`. The nittei font resources lack usable ToUnicode
maps for those CIDs; the observed PDFs contain Adobe Identity/Adobe Japan1 font
families. The installed Poppler bundle supplies `pdfinfo` and rendering, not
`pdftotext`. No deterministic mapping from all such CIDs to identity characters was
established. Bangumi text is likewise not consistently usable for strict cell semantics.

The following cannot be approved from the sampled bytes:

- versioned nittei calendar coordinate/cell grammar that binds target date to exact
  planned meeting identities;
- a bangumi all-page/all-cell grammar that binds each day column to every planned race
  tuple without race-count, filename, or row-order inference;
- a parser/library version plus required embedded/external CMap/font resource contract;
- treatment of any alternate/revised/split-meeting PDF layout.

Future work must first select a deterministic extraction mechanism and freeze its
version, resource inputs, byte handling, structural selectors, expected page roles and
fail-closed ambiguity rules against reviewed bytes. OCR, manual glyph replacement,
filename identity, global digit matching, printed totals, and table/race continuity
remain forbidden. This is a contract gap, not permission to add a library or parser.

## accessS root-to-month candidate relation

Exact official byte observations establish this parent chain:

```text
year-program HTML supplied onclick
  -> POST /JRADB/accessS.html, form cname=pw01skl00999999/B3
  -> CP932 search/root response
     -> selected #kaisaiY_list/#kaisaiM_list values
     + literal setParameter source expression
     + exact objParam year-month tail
  -> POST /JRADB/accessS.html, form cname=<source-owned derived selection>
  -> CP932 month response
     -> exact parent-day meeting onclicks
  -> POST /JRADB/accessS.html, form cname=<exact supplied meeting token>
  -> meeting response
     -> exact direct-row result hrefs
  -> GET exact supplied accessS result href
```

The observed 2024-01 and 2020-01 values are
`pw01skl10202401/B3` and `pw01skl10202001/83`. They were read from each captured
search response's `setParameter` and `objParam` source; they were not generated from
a date by an application rule. The source's `yearMonth` branch discriminator is
navigation material only and has no historical/causal meaning.

This resolves the factual relation but not the contract conflict. Phase 7 requires
captured root/search evidence while its approved exact page-kind list has no root/search
kind. Further, a raw supplied selection expression has different authority semantics
from a raw literal href/CNAME. Phase 9 cannot silently (a) add a page kind, (b) call the
response an `accesss_month` capture, (c) hard-code a prefix/tail formula, or
(d) allow a current date/time to select a branch. ChatGPT must approve a precise
capture-kind and source-owned-expression boundary before a later implementation phase.

If that review admits this chain, it must define exact raw request fields, parent
capture/reference identity, source lexical representation, selection inputs, branch
and table lookup uniqueness, CP932 validation, and canonical-byte fields. It must still
reject missing/duplicate/changed script/table/selectors and never synthesize an opaque
tail/CNAME. No SQLite/archive/migration/API is proposed or changed here.

## accessS meeting/race strict candidate grammar

The four captured meeting pages were decoded CP932 strictly. Each has one
`#race_list` with one direct header row whose ordered classes are:

```text
race_num, race_name, mov, dist, course, num, odds, win5
```

Each direct `tbody > tr` must have one `th.race_num[scope=row] > a[href]` that
matches the official accessS result grammar and one race-number image. The exact raw
href, not a separately navigated known-race locator, is the result request authority.
The accessO odds link is a different field and cannot be accepted as a target row.

The candidate normalizer must read all direct rows, validate the supplied URL through
the existing `parse_jra_result_url_identity`, reject unknown/malformed/missing/
duplicate/contradictory rows, and validate the calendar date from the result header
against the exact result CNAME date. It may not accept only a known race or use
twelve/contiguous race numbers as a completeness premise.

Research validation covered every direct row for:

| Historical day | Meeting | Validated supplied result rows |
| --- | --- | ---: |
| 2024-01-06 | 1回中山1日 | 12 |
| 2024-01-06 | 1回京都1日 | 12 |
| 2020-01-05 | 1回中山1日 | 12 |
| 2020-01-05 | 1回京都1日 | 12 |

The 48 result URLs are distinct, and their decoded parent headers/identities were
unique. This provides a full actual-result-page candidate set for those four meetings,
not provider-day completeness and not proof of planned/actual equality until the PDF
contract is resolved.

## Scheduled-start candidate selector

All 48 acquired result bytes contain exactly one candidate header relationship:

```text
#race_result .race_header > .left > .date_line > .inner
  .cell.date                    -> exact displayed historical calendar date
  .cell.time > strong           -> one displayed start value
#race_result .race_header .race_number img[alt]
                               -> race-number agreement with the supplied result identity
```

The candidate time lexical domain is:

```text
(?:[0-9]|1[0-9]|2[0-3])時[0-5][0-9]分
```

All 48 values passed that lexical check, and each header date agreed with the exact
calendar-date field in its supplied result CNAME. The existing formal
`JRAExternalRaceIdentity` parser accepted every result request identity. The candidate
meaning remains only the official historical **displayed** start: it is converted to an
aware JST time only after all selector, identity and date checks pass. It is not
inferred from a PDF, source observation time, current clock, or actual running time.
Research does not establish an unchanged original announcement or support exceptional
delays/cancellations.

This selector is not frozen as a production API because the composite source and fixture
gates remain incomplete. Future tests must include zero, missing, duplicate, ambiguous,
malformed, identity/date disagreement and unsupported exceptional cases; no relaxed
fallback is allowed.

## Candidate evidence and provenance

All research material is outside the repository:

```text
C:\Users\garim\AppData\Local\Temp\keiba-phase8-jra-24517bdcf7524eedb5bf7c7f2db7cc95
```

Phase 8's original sanitized 21-record provenance manifest remains
`bff17dec9bb3f65b5265adf000eeeed956283b52f83029f135840789ef666ad8`.
It includes the year program, six PDFs, root/search, two months, four meetings, four
1R results, and two 2024-01-28 off-target negative controls. Its 19 partial candidates
and two controls remain unchanged. Phase 9 re-acquired the 48 exact direct-row result
pages and verified each byte length/SHA-256. Its manifest SHA-256 is:

```text
3894ba1c608f052c47bf396ab3091d7227f432f4b2c079f52369517cca71e996
```

The four re-acquired 1R bytes equal their Phase 8 byte digests exactly. Thus there are
69 capture records but 65 unique proposed fixture paths (63 ordinary partial candidates
plus two off-target controls). No path has been materialized in the repository and none
is an approved formal replay evidence artifact.

Every following candidate records official raw href/request identity, byte length,
SHA-256 and honest requested/observed time. All times are UTC on 2026-09-03. This table
is an audit index only; it does not authorize replay use, backdating, materialization,
or a fresh network acquisition in tests.

| Proposed basename | Exact supplied raw href | Bytes | SHA-256 | Requested / observed UTC |
| --- | --- | ---: | --- | --- |
| `accesss_result_20240106_06_01.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1006202401010120240106/21` | 97048 | `01fa8c6674d47aef7291145430fcbf0e2ffae15fcdb11a32f96443908c06e9b5` | `2026-09-03T11:40:01.673482+00:00` / `2026-09-03T11:40:02.224952+00:00` |
| `accesss_result_20240106_06_02.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1006202401010220240106/D6` | 98485 | `e9a2a5ad20a2e081b213389f72b1aa1dd0de9bafa5696f032db8fe28564257d7` | `2026-09-03T11:40:02.226143+00:00` / `2026-09-03T11:40:02.485351+00:00` |
| `accesss_result_20240106_06_03.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1006202401010320240106/8B` | 96814 | `05d492ef8be994e5327354210909e274e8a7fdcb824b29cf82c7002aeda71782` | `2026-09-03T11:40:02.486443+00:00` / `2026-09-03T11:40:02.743922+00:00` |
| `accesss_result_20240106_06_04.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1006202401010420240106/40` | 98124 | `0258612c2967da36d2006e75267dfcd50d7743b8855209c3a9176d602c8bccea` | `2026-09-03T11:40:02.744748+00:00` / `2026-09-03T11:40:03.015634+00:00` |
| `accesss_result_20240106_06_05.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1006202401010520240106/F5` | 99748 | `9094464732f4542c5b2b2b3371d0065fbe3503a5f653180bc119e8a27ec68e91` | `2026-09-03T11:40:03.016491+00:00` / `2026-09-03T11:40:03.290753+00:00` |
| `accesss_result_20240106_06_06.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1006202401010620240106/AA` | 98976 | `134f2f013dd1f9b19bee9df1f9dcc44b41a1eabb79e27304bd50fa8ffa7173db` | `2026-09-03T11:40:03.291697+00:00` / `2026-09-03T11:40:03.566825+00:00` |
| `accesss_result_20240106_06_07.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1006202401010720240106/5F` | 93976 | `e483f18b53f0eb81ee4c8a33f96f39f3ac024b710eea3c87fff0c1234b035a3e` | `2026-09-03T11:40:03.567741+00:00` / `2026-09-03T11:40:03.827132+00:00` |
| `accesss_result_20240106_06_08.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1006202401010820240106/14` | 98868 | `327c2ab5f0ebdf53d449c60dbec37a7e7899f13beb56093d477e51cbe079efb9` | `2026-09-03T11:40:03.828044+00:00` / `2026-09-03T11:40:04.103108+00:00` |
| `accesss_result_20240106_06_09.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1006202401010920240106/C9` | 89644 | `c7b8425c37df8ba2afef72966580609a891acbbcda6f16317064e47bf90cea6d` | `2026-09-03T11:40:04.104051+00:00` / `2026-09-03T11:40:04.455174+00:00` |
| `accesss_result_20240106_06_10.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1006202401011020240106/BE` | 90897 | `9b5e0e327bf57c3e9ef04da787535f75b3236ea43bbd0cdf5084c5d4225e5d8b` | `2026-09-03T11:40:04.456116+00:00` / `2026-09-03T11:40:04.700106+00:00` |
| `accesss_result_20240106_06_11.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1006202401011120240106/73` | 101211 | `471e5c20233ac2ac185e3969c154b74c5f4a5b672e73f62e374054089410e79d` | `2026-09-03T11:40:04.701103+00:00` / `2026-09-03T11:40:05.053983+00:00` |
| `accesss_result_20240106_06_12.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1006202401011220240106/28` | 99737 | `4dca43803141d04fd4bc67bb6b1548abd2c57a1901fe934f281a2465eba2d414` | `2026-09-03T11:40:05.054991+00:00` / `2026-09-03T11:40:05.304611+00:00` |
| `accesss_result_20240106_08_01.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1008202401010120240106/B5` | 97867 | `bfe8e52f47e2a6003e6821feb5b3175c8bafd1dfeba08b616fcd8422db650a83` | `2026-09-03T11:40:05.342319+00:00` / `2026-09-03T11:40:05.603995+00:00` |
| `accesss_result_20240106_08_02.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1008202401010220240106/6A` | 98750 | `71582c309c1e0b0236556e34221a17c5daff9d3539ac727a59ecdcd10227d58c` | `2026-09-03T11:40:05.604928+00:00` / `2026-09-03T11:40:05.904495+00:00` |
| `accesss_result_20240106_08_03.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1008202401010320240106/1F` | 96590 | `11f9a142e1d8ec61630e46357ad1a86e80d3b637f37e6807e488c60948f90799` | `2026-09-03T11:40:05.905557+00:00` / `2026-09-03T11:40:06.205982+00:00` |
| `accesss_result_20240106_08_04.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1008202401010420240106/D4` | 98319 | `81983ff15cff8180630656b63135b4b6d771e3b40aaac6e5e29ce110e4c5d9b3` | `2026-09-03T11:40:06.207016+00:00` / `2026-09-03T11:40:06.447197+00:00` |
| `accesss_result_20240106_08_05.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1008202401010520240106/89` | 98736 | `04f74189915c1ced0e6fcf530d73fef0ef1d369fa8270f2b36fbca9df3394ddd` | `2026-09-03T11:40:06.448334+00:00` / `2026-09-03T11:40:06.697271+00:00` |
| `accesss_result_20240106_08_06.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1008202401010620240106/3E` | 89654 | `acd474bccb5e9b71a8c535d44200a2ed8763d7707b4b887906a28ca8393330ed` | `2026-09-03T11:40:06.698391+00:00` / `2026-09-03T11:40:06.999334+00:00` |
| `accesss_result_20240106_08_07.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1008202401010720240106/F3` | 92494 | `b9e6f3da341bb4da8f06288c8f3612e6c345ab40bf12316ad3adabec8ed8e204` | `2026-09-03T11:40:07.000339+00:00` / `2026-09-03T11:40:07.271237+00:00` |
| `accesss_result_20240106_08_08.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1008202401010820240106/A8` | 97032 | `0aeebf2f0d3aa4d5bac79e63d26910899ab90b4e010d7caa16a724c17c7ad4bc` | `2026-09-03T11:40:07.272200+00:00` / `2026-09-03T11:40:07.592171+00:00` |
| `accesss_result_20240106_08_09.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1008202401010920240106/5D` | 93106 | `08a80c8425d6822b16e0733b80922005c87a05e21664d639eae3d85d144251ec` | `2026-09-03T11:40:07.593091+00:00` / `2026-09-03T11:40:07.862439+00:00` |
| `accesss_result_20240106_08_10.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1008202401011020240106/52` | 95927 | `d6e737bcfe2595803c08e472463505d0ad7e528a2cc3e6ab37ee781d463afd9f` | `2026-09-03T11:40:07.863417+00:00` / `2026-09-03T11:40:08.125838+00:00` |
| `accesss_result_20240106_08_11.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1008202401011120240106/07` | 100108 | `326d97d6ccf53b5c263d5badb24df6f2e9232397ef64282ae3d2641dc99e8609` | `2026-09-03T11:40:08.126757+00:00` / `2026-09-03T11:40:08.367428+00:00` |
| `accesss_result_20240106_08_12.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1008202401011220240106/BC` | 97475 | `cb11196385b0cb29b6a1cf06401393f6cab10fa910cf88c5e330eb0920d30491` | `2026-09-03T11:40:08.368454+00:00` / `2026-09-03T11:40:08.630481+00:00` |
| `accesss_result_20200105_06_01.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1006202001010120200105/48` | 94243 | `0ca56ade1accc552f6244c4bbdc17d9bd31c206a63233b50ad1252658137eeac` | `2026-09-03T11:40:08.667397+00:00` / `2026-09-03T11:40:08.924508+00:00` |
| `accesss_result_20200105_06_02.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1006202001010220200105/FD` | 96690 | `c730b2d6f373ec1befbe8377521c4df32854714a0ab2d047d82b1de5e763288c` | `2026-09-03T11:40:08.925337+00:00` / `2026-09-03T11:40:09.142082+00:00` |
| `accesss_result_20200105_06_03.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1006202001010320200105/B2` | 94955 | `fa571beeebc443fe306b08543d13e1bdc856d8017d8402de4f5d23b882629818` | `2026-09-03T11:40:09.143296+00:00` / `2026-09-03T11:40:09.389340+00:00` |
| `accesss_result_20200105_06_04.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1006202001010420200105/67` | 96524 | `21c331ce3891dc0f18e0495c04b2f122f9acf623f1041f078b24cb54fe0f65a2` | `2026-09-03T11:40:09.390252+00:00` / `2026-09-03T11:40:09.633049+00:00` |
| `accesss_result_20200105_06_05.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1006202001010520200105/1C` | 88912 | `ad76cd683dcd32fb52e51c0f286510ca90d6d2915061e86031c44ea485d9a612` | `2026-09-03T11:40:09.633972+00:00` / `2026-09-03T11:40:09.908097+00:00` |
| `accesss_result_20200105_06_06.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1006202001010620200105/D1` | 95133 | `a52951c9088c467829b3e28919a180982553d9ced4becbff9ea3396319aa7a22` | `2026-09-03T11:40:09.909050+00:00` / `2026-09-03T11:40:10.149074+00:00` |
| `accesss_result_20200105_06_07.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1006202001010720200105/86` | 97601 | `5f02911c59f943b79242bc75c9dd1deb5623241c6408fdd0997340c124bf6007` | `2026-09-03T11:40:10.150496+00:00` / `2026-09-03T11:40:10.270169+00:00` |
| `accesss_result_20200105_06_08.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1006202001010820200105/3B` | 95086 | `4c3756d289107384a440e400bfeb2b6e04749956c3f143102a33345b1e48c47b` | `2026-09-03T11:40:10.271039+00:00` / `2026-09-03T11:40:10.512446+00:00` |
| `accesss_result_20200105_06_09.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1006202001010920200105/F0` | 97389 | `c53b2e5d5534b8ac6f6e50020054bd0bc0ea17cca636cfa6ad76b03af81c6f88` | `2026-09-03T11:40:10.513341+00:00` / `2026-09-03T11:40:10.754990+00:00` |
| `accesss_result_20200105_06_10.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1006202001011020200105/E5` | 96152 | `b0cec1e5fd673036f756d9f85e9136cf9643f8dca43e49919d7c0ea3777618fd` | `2026-09-03T11:40:10.755918+00:00` / `2026-09-03T11:40:11.009799+00:00` |
| `accesss_result_20200105_06_11.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1006202001011120200105/9A` | 98762 | `4a0d815f1bcce7d8714492a3956e9ce7d1a25579671eda23e71c3cf6c9fc1d5f` | `2026-09-03T11:40:11.010680+00:00` / `2026-09-03T11:40:11.300083+00:00` |
| `accesss_result_20200105_06_12.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1006202001011220200105/4F` | 94519 | `2f759b8e26e8f173012548a8673fff83cf33210cbfe9f697932a8a82e1c66253` | `2026-09-03T11:40:11.301068+00:00` / `2026-09-03T11:40:11.518800+00:00` |
| `accesss_result_20200105_08_01.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1008202001010120200105/DC` | 94893 | `2e12cfef5b2597450806a502c53c55eb8ed66e8cd7ee6dc1224c40a5ff298df9` | `2026-09-03T11:40:11.558726+00:00` / `2026-09-03T11:40:11.797748+00:00` |
| `accesss_result_20200105_08_02.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1008202001010220200105/91` | 96730 | `c17860cef05ef835ee05ddc362ef2516428231c837081206b5e744ea1b4d9650` | `2026-09-03T11:40:11.798653+00:00` / `2026-09-03T11:40:12.043155+00:00` |
| `accesss_result_20200105_08_03.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1008202001010320200105/46` | 94118 | `49d2e9b3020891751a6a4b54e5eaff243c02968bf92a5fa1ed2d6dca9aefc94f` | `2026-09-03T11:40:12.044032+00:00` / `2026-09-03T11:40:12.300256+00:00` |
| `accesss_result_20200105_08_04.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1008202001010420200105/FB` | 92514 | `ec78860251b2c8ab38c0f0684237dc06de87778fbf7b4cff25a9954ad60b6fe2` | `2026-09-03T11:40:12.301232+00:00` / `2026-09-03T11:40:12.576076+00:00` |
| `accesss_result_20200105_08_05.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1008202001010520200105/B0` | 94559 | `33ee8e1905c93f282e3e402e13e0c879a96d866922e7bf7a1cb5387541160489` | `2026-09-03T11:40:12.577019+00:00` / `2026-09-03T11:40:12.848981+00:00` |
| `accesss_result_20200105_08_06.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1008202001010620200105/65` | 94444 | `3e753dfb04879c5b4cb6f376b1019da019a3d9acb1a5f7bfe96503e285c4c54e` | `2026-09-03T11:40:12.850528+00:00` / `2026-09-03T11:40:13.119440+00:00` |
| `accesss_result_20200105_08_07.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1008202001010720200105/1A` | 95529 | `01d70b768b55b6c74b32dbbef7357f33f0116f0aafcf7a1cc90ab08c077507a0` | `2026-09-03T11:40:13.120324+00:00` / `2026-09-03T11:40:13.371597+00:00` |
| `accesss_result_20200105_08_08.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1008202001010820200105/CF` | 97062 | `63863e6a84a34edcf1681a5d911201aecbd900b31ad63e302597406ea42a5c5d` | `2026-09-03T11:40:13.372668+00:00` / `2026-09-03T11:40:13.592402+00:00` |
| `accesss_result_20200105_08_09.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1008202001010920200105/84` | 86147 | `2239fbeb23be593a303eed2b1211a708b7f960be4fbf34a60426a50a25a781ee` | `2026-09-03T11:40:13.593325+00:00` / `2026-09-03T11:40:13.813071+00:00` |
| `accesss_result_20200105_08_10.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1008202001011020200105/79` | 94993 | `f3e3e58004a8d027af137e46a643aba9883f2f896305638a309011be8f0cc43e` | `2026-09-03T11:40:13.813969+00:00` / `2026-09-03T11:40:14.074830+00:00` |
| `accesss_result_20200105_08_11.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1008202001011120200105/2E` | 98076 | `5302a8890f1af91875afe6d2d491c4149fecaac2a50a4ad898c184749f95c100` | `2026-09-03T11:40:14.075682+00:00` / `2026-09-03T11:40:14.320754+00:00` |
| `accesss_result_20200105_08_12.cp932.html` | `/JRADB/accessS.html?CNAME=pw01sde1008202001011220200105/E3` | 94361 | `8a6ce90045e7c4de0512efe70d18c1e8eaef457f76f1e50f20173f47ba5a28bb` | `2026-09-03T11:40:14.321656+00:00` / `2026-09-03T11:40:14.556035+00:00` |

The inherited Phase 8 21-record manifest retains the same fields for its year/PDF/root/
month/meeting/1R/control candidates. The four overlapping result records match the
corresponding rows above; use only their byte digest, not either acquisition time, for
that equality. HTTP `Date`/Last-Modified are not provider availability fields.

## Remaining blockers and required review

1. Establish and independently review a deterministic, complete, non-OCR PDF
   extraction/layout contract; otherwise nittei/bangumi planned evidence is unusable.
2. Resolve the exact accessS root/search page-kind and source-expression request/capture
   contract without weakening raw supplied-token authority.
3. Materialize and review the complete fixture/provenance set only after 1 and 2:
   one ordinary composite requires all selected PDF/root/month/meeting/result bytes,
   exact parser grammar and planned/actual equality. Required fail-closed fixture cases
   for zero, cancellation, substitute, partial and malformed/ambiguous layouts are
   still absent.
4. Freeze only after the above the canonical-byte/capture identity representation,
   including schema version, ordered fields, UTF-8/CP932 handling, raw request form
   representation, parent-reference identity, timestamps and response digest. The
   existing shared target-set digest stays unchanged.

This PREPARE stops. The prospective behavior for any unresolved date remains whole-day
`TARGET_DISCOVERY_INCOMPLETE`; no partial actual result sample can be reported as
a supported complete day.

## Allowed Files

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Forbidden Files and actions

All other repository files, including production, tests, fixtures, requirements,
NAR/shared domains, SQLite/migrations/schema/database, logs, archives, CLI and
release/tag history. No implementation, fixture materialization, dependency change,
stage, commit, push, execution phase or next phase is authorized during PREPARE.

## Required PREPARE verification

```text
git diff --check
git diff --name-only
git status --short
git diff --cached --name-only
```

Verify exactly the two Allowed Files changed and the index is empty. No test suite is
required/run for this research/docs-only PREPARE.
