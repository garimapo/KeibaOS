# Current Phase

Status: APPROVED_FOR_COMMIT

## Identity and authority

- Phase: POST_V0_8_DAILY_REPLAY_11
- Name: JRA Calendar Locator and Identity Binding Qualification
- Phase type: RESEARCH_AND_DESIGN_ONLY
- Base Commit: 2445a997d6614bb4406548243a777c152599edfc
- Branch: feature/post-v0.8-daily-replay
- Outcome: BLOCKED
- Production/test/fixture implementation or materialization: NOT_AUTHORIZED
- Stage/commit/push and EXECUTE_APPROVED_PHASE: NOT_AUTHORIZED

Phase 10's approved BLOCKED conclusion and all prior approved contracts remain
authoritative. This phase investigates only the specified calendar-profile predicates:
source-owned daily locator authority, planned provider-day meeting completeness, and
calendar-to-accessS exact identity binding. It does not amend the PDF profile, accessS
contracts, Phase 4 supported profile, or NAR/shared code.

## Decision

The only permitted outcomes were HTML_PROFILE_BINDING_QUALIFIED or BLOCKED. This phase
concludes BLOCKED.

A JRA-owned calendar asset provides a source-owned month JSON request relation, but not
a source-owned historical daily calendar HTML locator. The JSON only supplies displayed
planned meeting names. It does not provide daily HTML hrefs, meeting day, JRA venue code,
all race rows, start time, or a complete-provider-day statement. The 2019-10-12 response
also demonstrates cancellation-adjusted content. It cannot prove an original planned
denominator or non-run membership.

The four ordinary samples preserve Phase 10's visible calendar/accessS agreement, but
visible Japanese meeting text and race number cannot replace exact identity fields.
Calendar data has no accessS CNAME, venue code, meeting day, or reviewed official
cross-reference. No predicate is promoted from sample observation to an implementation
contract.

## A. Source-owned locator authority

### Observed, narrow month-JSON relation

~~~text
/calendarYYYY/
  -- supplied raw href "jan.html" -->
/calendarYYYY/jan.html
  -- supplied script src "/keiba/common/calendar/cal.js?version=…" -->
cal.js
  -- source-owned setJSON() -->
/keiba/common/calendar/json/YYYYMM.json
~~~

The inspected JRA JavaScript takes YYYY from the source page's calendarYYYY path
segment and MM from the supplied month path, then calls $.getJSON(targetJSON). The two
recorded asset versions are byte-identical:

| Asset | Bytes | SHA-256 |
| --- | ---: | --- |
| /keiba/common/calendar/cal.js?version=2021 | 86,673 | 1c6e46c8bda0f75d548a95ca1be9af8ca5b2acf58d7b36ed9a46f869d07e4961 |
| /keiba/common/calendar/cal.js?version=2026 | 86,673 | 1c6e46c8bda0f75d548a95ca1be9af8ca5b2acf58d7b36ed9a46f869d07e4961 |

This is not authorization for developer-generated historical requests. The asset has
current-date UI branches, which cannot select historical identity, evidence time, or a
locator.

### Daily locator remains unqualified

Neither the four supplied January HTML responses nor either cal.js byte carries a daily
program locator, a YYYY/M/MMDD.html output grammar, or a JSON field with one. The script
only copies an already-present div.date_line … a[href] to a program link. The sampled
historical month pages contain no such day anchors.

The six direct daily pages therefore remain Phase 10 research-lead requests, not
source-owned locators. HTTP success cannot turn the suggested path pattern into
authority. Predicate A is unqualified.

## B. Planned provider-day meeting completeness

| JSON resource | Bytes | SHA-256 | Examined date / displayed meeting names |
| --- | ---: | --- | --- |
| 202001.json | 9,639 | 97c080a12ea8436eafe1ff26e5ab99adb685385cc55d49312d9c5038fb9ca552 | 2020-01-05: 1回中山, 1回京都 |
| 202101.json | 10,303 | 076c9049cf38db8c9bbbbcccab030fc055a69491f2f5e204c3defcd7bc5138e6 | 2021-01-05: 1回中山, 1回中京 |
| 202401.json | 10,359 | f34c865d381cc0e904f046901340b4abdd0b40c93e1bb46c81c4975cb6068f66 | 2024-01-06: 1回中山, 1回京都 |
| 202501.json | 10,302 | 4d1a0c4745ed53d1ff4519f6ee1aaf4a30d85dc13a83703685d04689e5381ced | 2025-01-05: 1回中山, 1回中京 |
| 201910.json | 12,680 | a0f78f2a632e7e28e30a2afebb6dc55f84f829da57fa94d96f1ef9c70d9782c1 | 2019-10-12: 4回京都; 2019-10-15: 4回東京 |

The source asset loops every data entry and info[0].race item. That proves the UI
rendering procedure, not that the response is a complete provider-day target set. Its
schema has only month-local day number and display names such as 1回中山; it lacks
meeting day, individual race rows, start fields, and a complete-set assertion.

On 2019-10-12, the JSON has only 4回京都 plus the official notice 東京競馬開催を中止;
it cannot establish whether cancelled Tokyo remains in the original denominator. The
2019-10-15 substitute entry cannot be joined by inference. The ordinary JSON/daily-page
meeting-name agreement drops the latter's meeting-day suffix and is therefore not exact
identity equality. Predicate B is unproven; absence and zero-day remain fail-closed.

## C. Calendar to accessS actual-identity binding

Existing parse_jra_result_url_identity validates a supplied accessS result CNAME into
year, JRA venue code, meeting number, meeting day, and race number. It remains the only
origin of exact external race identity.

Calendar sources provide visible Japanese meeting text and candidate daily race numbers;
month JSON provides even less. Neither provides the accessS venue code, CNAME, meeting
day, or an official cross-reference. A local venue-name map, inferred meeting day, or
matching display text would violate the exact-identity contract.

For 2020-01-05, 2021-01-05, 2024-01-06 and 2025-01-05, Phase 10 observed two calendar
meetings and 24 race numbers visibly matching the source-owned accessS actual set. This
is sampled consistency only. Calendar planned start differed from actual accessS
displayed start in 4, 2, 1 and 1 rows respectively. The 2019-10-12 discrepancy remains
whole-day TARGET_DISCOVERY_INCOMPLETE, not a mapping rule. Predicate C is unqualified.

## Research material and audit boundary

All seven Phase 11 request bytes remain outside the repository:

~~~text
C:\Users\garim\AppData\Local\Temp\keiba-phase11-jra-calendar-assets-3efab61dc96d44cb9ea811991eb8d697
~~~

The asset manifest SHA-256 is
b8329e0d84926e7ffa0eaa754bc1e7f5dfe6b5842eacae4f441e5e9c12da89fd; the five-JSON
manifest SHA-256 is a5e5ce68979ae037cafdd769a580d6dc7f3758c72e4fe9d900d0125dbf2dd68b.
Every recorded byte length/SHA-256 was reverified. External manifests retain exact URL,
response metadata, and honest 2026-09-03 UTC request/observation times. These bytes
are research material only: never fixtures, captures/archives, formal replay evidence,
HistoricalDailyTargetEvidenceBundle.observed_at, causal input, or authorization to
materialize.

## Qualification matrix

| Required predicate | Result | Evidence / limit |
| --- | --- | --- |
| A. Source-owned historical daily HTML locator | unqualified | no supplied day href/output grammar in month pages or asset |
| Source-owned month-JSON locator | observed, narrow | root/month + cal.js setJSON() yields YYYYMM.json |
| B. Complete planned provider-day meeting set | unproven | display-name list has no complete-set semantics or full identity |
| Candidate daily all-row race table | observed only | four research-lead normal pages; locator remains unqualified |
| C. Exact calendar ↔ accessS identity binding | unqualified | no shared venue code, meeting day, CNAME, or official cross-reference |
| Visible calendar/accessS membership | observed only | four normal 2-meeting/24-race dates |
| Exceptional cancellation behavior | observed fail-closed | 2019-10-12 cannot produce a safe original target set |
| Zero-day semantics | unsupported | absence/missing never means no racing |
| Overall outcome | BLOCKED | A, B and C are all required |

## Blockers and stop condition

1. A source-owned locator relation must yield each historical daily program without
   target-date path synthesis. A month JSON locator is insufficient.
2. A formal source must express a complete planned provider-day meeting set with exact
   identity, zero/absence semantics, and preserved exceptional membership.
3. An official cross-reference or shared exact tuple must bind calendar records to
   accessS CNAME-originated actual identity.

Until all three are resolved, this profile is TARGET_DISCOVERY_INCOMPLETE. Do not
implement a calendar source/parser, alter the PDF profile, construct calendar URLs,
introduce a name mapping, materialize fixtures, or amend prior phases.

## Allowed Files

~~~text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
~~~

## Forbidden Files and actions

All other repository files, including production, tests, fixtures, dependencies,
NAR/shared domains, SQLite/migrations/schema/database, logs, archives, CLI, and release
history. No implementation, fixture materialization, staging, commit, push, execution
phase, or further phase advance is authorized during this PREPARE.

## Required PREPARE verification

~~~text
git diff --check
git diff --name-only
git status --short
git diff --cached --name-only
~~~

No tests are required or run for this research/design-only PREPARE.
