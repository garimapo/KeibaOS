# Current Phase

## Status

READY_FOR_REVIEW

## Phase

`4C-2d3b1i6d1d5f1b` — JRA accessD structural prerequisites preparation.

Formal base: `776cd9123635eef3759284ff997a369857f3769e`.

Design reference inspected without merge or cherry-pick:
`353c3259fab1ad17c97040deb9522fcd66431d1f`.

Review branch:
`review/4c-2d3b1i6d1d5f1b-jra-accessd-structure-prepare`.

## Allowed Files

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

This is a read-only structural investigation. It authorizes no production code,
tests, trusted capture persistence, archive, migration, schema, target normalizer,
or live-capture implementation.

## Official Navigation and Transient Responses

The first transient official GET, at `2026-08-16T02:56:57.442112+00:00`, used the
then-expired 2026-07-26 Chukyo 9R accessD URL. It returned HTTP 200,
`Content-Type: text/html`, no `Content-Encoding`, and strict-CP932-decodable bytes,
but was the official expired-publication representation. It contained no entry table
or target fields. This proves only the expired-page byte contract:

```text
EXPIRED_ACCESSD_BYTE_CONTRACT = PROVEN
ACTIVE_CARD_BYTE_CONTRACT = superseded below by direct active-card observation
```

It does not establish active-card structure or encoding by generalization.

At `2026-08-16T03:03:24.871331+00:00`, the official JRA navigation page
`https://www.jra.go.jp/keiba/thisweek/` directly supplied the race-card navigation
href:

```text
/JRADB/accessD.html?CNAME=pw01dde0107202602080720260816/29
```

No CNAME was synthesized. A transient read-only GET of its canonical form at
`2026-08-16T03:03:43.289184+00:00` returned:

```text
ACTIVE_ACCESSD_HTTP_STATUS = 200
ACTIVE_ACCESSD_CONTENT_TYPE = text/html
ACTIVE_ACCESSD_CONTENT_ENCODING = absent
ACTIVE_ACCESSD_STRICT_CP932 = PASS
ACTIVE_ACCESSD_BYTE_LENGTH = 237794
ACTIVE_CARD_BYTE_CONTRACT = PROVEN
```

The canonical investigated URL was:

```text
https://www.jra.go.jp/JRADB/accessD.html?CNAME=pw01dde0107202602080720260816%2F29
```

It was a currently published 2026-08-16 2nd Chukyo meeting, day 8, race 7 card,
scheduled for 15:35 JST; the observation preceded that start. Both response bodies
were transient only: neither was saved, archived, copied, staged, nor committed.
Neither is trusted historical capture evidence.

## accessD Identity and Reusable Supplied Response

`ACCESSD_HTTP_METHOD = GET`; `ACCESSD_CHARSET = cp932` strict; and
`ACCESSD_CAN_REUSE_JRA_SUPPLIED_RESPONSE = YES_AFTER_ACCESSD_CANONICAL_URL_RECOGNITION`.
The existing immutable supplied-response type already has the required exact raw
bytes, strict decoding, and actual-observation fields. Its current URL allowlist
admits only accessS/accessU, so a later approved capture/domain phase must add the
formal accessD rule before that type receives accessD evidence.

The endpoint is exactly `https://www.jra.go.jp/JRADB/accessD.html`; its raw CNAME
grammar is the single concatenated ASCII token:

```text
pw01dde(?P<site>01|10)(?P<venue>0[1-9]|10)(?P<year>[0-9]{4})
(?P<meeting>0[1-9]|[1-9][0-9])(?P<day>0[1-9]|1[0-2])
(?P<race>0[1-9]|1[0-2])(?P<date>[0-9]{8})/(?P<tail>[0-9A-F]{2})
```

`date` must be real and share its year with `year`; `site` and `tail` are opaque.
The identity is `jra:race:<YYYY>:<VV>:<MM>:<DD>:<RR>`. The future
`parse_jra_race_card_url_identity(value: str) -> JRAExternalRaceIdentity` accepts
only the exact HTTPS host, accessD path, one uppercase `CNAME` key, canonical CNAME
grammar, and raw `%2F` URL delimiter, then renders the same canonical URL. URL
identity is authoritative over display text.

## Active-Card Selectors and Horse Identity

The exact unique active-card container is:

```text
#contentsBody > div.syutsuba > table.basic.narrow-xy.mt20
```

It must have one caption/header and a body whose direct row cells follow the
observed semantic headings: `枠`, `馬番`, horse/`単勝オッズ(人気)`,
sex-age/weight/`騎手名`, then four past-performance columns. Any duplicate,
missing, reordered, or unrecognized required node fails closed.

The future target parser must require each node exactly once:

| Fact | Exact selector / extraction | Required binding |
| --- | --- | --- |
| date, place, meeting/day | `table > caption > div.race_header > div.left > div.date_line > div.inner > div.cell.date` | strict date and `N回<venue>M日` agree with accessD identity and CNAME date |
| scheduled start | same header `div.cell.time > strong` | strict `HH時MM分` only |
| weather / track condition | same header `div.cell.baba > ul > li.weather > span.inner > span.txt`, plus exactly one `li.turf` or `li.dirt` `span.cap`/`span.txt` pair | direct weather/surface/condition; label only `芝` or `ダート` |
| race name | same header `div.race_title > div.inner > div.txt > span.main > span.race_name` | required direct nonempty text |
| race class | same header `div.race_title > div.type > div.cell.class` | required direct nonempty text |
| distance / surface | same header `div.race_title > div.type > div.cell.course` | strict `コース：<positive metres>メートル（<芝|ダート>・<direction>）`; surface agrees with condition pair |
| race number | `#contentsBody > div.line.main > div.inner > h1` | strict `<race>レース`, agreeing with accessD identity |
| horse number | `table > tbody > tr > td.num` | canonical positive decimal |
| stable horse anchor | same row `td.horse > div.name_line > div.name > a[href]` | exactly one relative official accessU href; resolve against JRA host, then use existing parser |
| jockey | same row `td.jockey > p.jockey` | required direct nonempty text |
| single-win odds | same row `td.horse > div.name_line > div.odds > div.odds_line > span.num` | exactly one canonical positive finite Decimal |

The active table had 16 rows. Every row had exactly one selector-scoped accessU
anchor, e.g. `/JRADB/accessU.html?CNAME=pw01dud002021105454/D5`; resolving it and
calling `parse_jra_horse_profile_url_identity(...)` yielded a canonical 10-digit
JRA horse key. Therefore:

```text
ACCESSD_TO_ACCESSU_IDENTITY_STATUS = PROVEN
ACCESSD_SELECTORS_READY = YES
TARGET_ODDS_SOURCE_READY = YES
```

These statuses apply only under the exact container, cardinality, semantic-heading,
and cross-check rules above. They do not authorize name, DOB, trainer, pedigree, or
fuzzy identity matching. A missing/duplicate anchor or value fails closed. Active
odds are target prediction-time evidence with their actual observed time; they are
not accessO historical-final odds, latest/nearest reconstruction, or settlement.

## Non-Runner Semantics

`ACCESSD_NON_RUNNER_SEMANTICS_READY = NO`. The 16 inspected rows were ordinary
populated entries. The response did not establish withdrawal, scratch, cancellation,
exclusion, or other non-runner shapes. Such states remain unsupported; they may not
be silently omitted without direct official row proof or documentation.

## Complete Single-Response Target Track

The neutral contract remains `TRACK_EVIDENCE_CARDINALITY = EXACTLY_ONE` and
`MULTI_RESPONSE_TRACK_EVIDENCE_SUPPORTED = NO`. The active response proves that one
`race_header` contains every required target track fact bound to the same canonical
accessD identity: date, scheduled start, place, distance, surface, track condition,
race name, and race class. Weather is also present but optional.

```text
SINGLE_RESPONSE_COMPLETE_TRACK_SOURCE = PROVEN
TRACK_SOURCE_SCHEMA_CHANGE_REQUIRED = NO
RECOMMENDED_TRACK_PHASE = NOT_REQUIRED
```

No second response is needed for the current neutral target-track record and no
track schema evolution is justified by this investigation.

## v003 Capture Readiness and Final Matrix

```text
ACCESSD_PAGE_KIND: TARGET_RACE_CARD (target_race_card)
ACCESSD_SUPPLIED_RESPONSE_TYPE: JRASuppliedOfficialResponse after URL recognition
ACCESSD_CAPTURE_SCHEMA_VERSION: 3
ACCESSD_CAPTURE_IDENTITY:
  jra-capture-v3:SHA256(canonical JSON {
    canonical_source_url, observed_at_utc, page_kind: "target_race_card",
    response_sha256, schema_version: 3
  })
ACCESSD_MIGRATION_REQUIRED: YES
```

Current schema-v1 accessS/accessU and schema-v2 POST accessO identities/semantics
are immutable. v003 capture/archive/migration design remains a later prerequisite.

```text
ACCESSD_IDENTITY_READY: YES — design only.
EXPIRED_ACCESSD_BYTE_CONTRACT: PROVEN.
ACTIVE_CARD_BYTE_CONTRACT: PROVEN.
ACCESSD_BYTE_CONTRACT_READY: YES — active GET/text-html/no-content-encoding/CP932 proved.
ACCESSD_CAPTURE_DESIGN_READY: YES_FOR_DEDICATED_V003.
ACCESSD_TO_ACCESSU_IDENTITY_STATUS: PROVEN.
ACCESSD_SELECTORS_READY: YES.
ACCESSD_NON_RUNNER_SEMANTICS_READY: NO.
TARGET_ODDS_SOURCE_READY: YES.
SINGLE_RESPONSE_COMPLETE_TRACK_SOURCE: PROVEN.
TRACK_SOURCE_SCHEMA_CHANGE_REQUIRED: NO.
TARGET_SOURCE_IMPLEMENTATION_READY: NO — formal accessD capture/archive family is absent.
SNAPSHOT_ASSEMBLY_READY: NO.
```

Stop after this docs-only correction is pushed. Do not implement accessD identity,
capture/archive/migration, target-source normalization, snapshot assembly, bridge,
Predictor, or any real trusted capture.
