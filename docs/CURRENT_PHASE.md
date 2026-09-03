# Current Phase

Status: `APPROVED_FOR_COMMIT`

## Identity and authority

- Phase: `POST_V0_8_DAILY_REPLAY_10`
- Name: `JRA Daily Calendar HTML Alternative Profile Qualification`
- Phase type: `RESEARCH_AND_DESIGN_ONLY`
- Base Commit: `adfac3946475d19058f9d24f15a1ae6588824fa7`
- Branch: `feature/post-v0.8-daily-replay`
- Outcome: `BLOCKED`
- Production/test/fixture implementation or materialization: `NOT_AUTHORIZED`
- Stage/commit/push and `EXECUTE_APPROVED_PHASE`: `NOT_AUTHORIZED`

Phase 9's approved `BLOCKED` conclusion and all Phase 2-7 contracts remain
authoritative. This is a parallel qualification of a possible planned-side HTML
profile only. It does not remove, relax, or replace the existing PDF profile, accessS
research, NAR implementation, or the provider-neutral target-set domain.

## Decision

The only permitted outcomes were `HTML_ALTERNATIVE_PROFILE_QUALIFIED` or
`BLOCKED`. This phase concludes `BLOCKED`.

The exact daily calendar HTML bytes are rich enough to be valuable research material:
sampled ordinary pages have a formal-looking date heading, meeting captions, all-row
race tables and planned start fields; sampled normal-day meeting/race membership agrees
with accessS actual history. However, the official annual/calendar root and its
source-supplied month links do not supply any daily-page locator for the tested
2020, 2021, 2024 or 2025 pages. The candidate daily URLs were supplied to this phase
as a research lead and directly inspected only as such. Their availability and content
cannot turn a developer-generated pattern into a formal locator authority.

The daily page also describes itself as a pre-announced program whose content can
change. It is not a complete actual-day source. The ordinary samples and the explicit
2019 cancellation/substitute case prove the required planned/actual separation, not a
general complete-denominator contract. Consequently the profile cannot amend Phase 4
or Phase 7 and cannot remove PDF dependency.

## Official locator research

The following exact root relation was positively observed from raw JRA HTML bytes for
each year:

```text
https://www.jra.go.jp/keiba/calendarYYYY/
  -- supplied href "jan.html" -->
https://www.jra.go.jp/keiba/calendarYYYY/jan.html
```

The root-side month anchor is source-owned and was unique after strict NFKC display
normalization to `1月`; its raw href was exactly `jan.html` in all four samples.
Every fetched root and January page decoded strictly as CP932. No redirect was followed.

The decisive negative result is equally exact: each sampled January page contained
zero anchors whose supplied href identified a `calendarYYYY/YYYY/M/MMDD.html`
daily page. No equivalent daily locator was found in the supplied HTML. This is not
a claim that no official daily pages exist; it means this inspected official navigation
does not establish their request identity.

The six direct requests below use the Phase 10 candidate-family lead for diagnostic
research only. Their provenance parent is explicitly
`RESEARCH_LEAD_NOT_OFFICIAL_SUPPLIED_LOCATOR`. A future implementation must not
construct, derive, or cache a target-date URL from this pattern, nor treat a successful
response as proof that the locator was supplied by an authoritative official relation.

| Case | Direct research-lead page | Result |
| --- | --- | --- |
| ordinary | 2020-01-05 | HTTP 200, CP932 daily program |
| ordinary | 2021-01-05 | HTTP 200, CP932 daily program |
| ordinary | 2024-01-06 | HTTP 200, CP932 daily program |
| ordinary | 2025-01-05 | HTTP 200, CP932 daily program |
| cancellation original | 2019-10-12 | HTTP 200, explicit Tokyo cancellation / October 15 substitute notice |
| substitute conduct | 2019-10-15 | HTTP 200, Tokyo replacement program |

No missing daily page was tested or interpreted as a zero-race date.

## Candidate daily-page grammar, not an implementation contract

All six direct research-lead bytes have one nonempty `h1` matching the visible
historical target-date form:

```text
YYYY年M月D日（weekday）　競馬番組
```

For a normal meeting, the candidate direct table shape is:

```text
table.basic.narrow-xy
  caption                         -> exact visible meeting descriptor
  thead > tr > th                 -> レース番号 / レース名・条件 / 発走時刻
  tbody > tr (one row per planned race)
    first cell                    -> Nレース
    second cell                   -> conditions (not identity authority)
    third cell                    -> H時MM分
```

A candidate regular table must have one caption, exactly the three direct headings
above, and every row must have three cells, a unique bounded race number and a bounded
planned time. Duplicate, missing, malformed or extra structural rows fail closed.
The caption and date are visible provider text, not an internal identity reconstructed
from a filename, SQLite ID, race count or race sequence.

This grammar is **not frozen** because the daily locator/coverage predicates are
unqualified. It must not be implemented or used to infer an external JRA race identity.
If a future source-qualified relation is adopted, each calendar row can only bind to an
accessS-originated exact identity after an explicit, one-to-one, same-date visible
meeting/race equality check. The calendar does not independently create a JRA external
identity.

The pages state that their information is a previously announced seasonal program
(`予定`) and that race number/order, course, distance, planned start, cancellation or
postponement can change. Calendar planned time is therefore never an actual start time,
a snapshot cutoff, a settlement cutoff, current-clock substitute, or causal input.
Actual result-header displayed start remains an independent accessS responsibility.

## Ordinary-date and accessS equality research

Each normal daily page contained two regular meetings with twelve valid planned race
rows each. Exact visible meeting descriptors and race-number sets were compared to
accessS actual meeting/result evidence. The actual side used source-owned accessS
root/month/meeting/result navigation, strict CP932 decoding, existing
`parse_jra_result_url_identity`, and result-header date/race checks. The relation
compares meeting captions and each supplied race number; exact provider external race
identity originates only from the validated accessS result locator.

| Date | Calendar planned tables/races | accessS actual tables/races | Visible meeting/race set | Planned vs actual displayed-start differences |
| --- | ---: | ---: | --- | ---: |
| 2020-01-05 | 2 / 24 | 2 / 24 | exact equality | 4 |
| 2021-01-05 | 2 / 24 | 2 / 24 | exact equality | 2 |
| 2024-01-06 | 2 / 24 | 2 / 24 | exact equality | 1 |
| 2025-01-05 | 2 / 24 | 2 / 24 | exact equality | 1 |

The time differences are expected evidence that calendar start fields are planned values,
not a replacement for actual historical accessS displayed start. These four successes
do not establish provider-day completeness for untested dates, zero-day semantics, or
the missing locator relation.

## Exception research and fail-closed result

The 2019-10-12 calendar page contains:

- a non-regular Tokyo table saying Tokyo racing was cancelled due to the typhoon and
  substitute racing would occur on 2019-10-15; and
- one regular Kyoto table with twelve planned race rows.

The corresponding accessS October envelope supplied exactly one 2019-10-12 actual
meeting, `4回京都3日`, with twelve direct result rows. It supplied exactly one
2019-10-15 actual meeting, `4回東京3日`, with twelve direct result rows. The
2019-10-15 calendar page separately contains the Tokyo replacement program.

This is a concrete planned/actual difference. The candidate profile must reject
2019-10-12 as `TARGET_DISCOVERY_INCOMPLETE`: its abnormal cancellation table,
planned Tokyo membership, original/substitute identity question and non-ordinary status
are outside the supported ordinary profile. It must not discard Tokyo and call Kyoto a
complete ordinary day, move Tokyo races to October 15, or equate planned and actual
start fields. The sample demonstrates fail-closed handling; it does not qualify a
general cancellation mapping.

## Research byte provenance

All material remains outside the repository at:

```text
C:\Users\garim\AppData\Local\Temp\keiba-phase10-jra-calendar-1f75d8f9f6c84f9d915b5b88494cfa38
```

Three immutable-on-disk-for-research-only manifest digests were verified against every
listed byte length/SHA-256:

| Manifest | Records | SHA-256 | Contents |
| --- | ---: | --- | --- |
| `provenance.json` | 14 | `57720c11fd073dceebbabd89605cd8f4bc3a375825bf263ea79a6e7a1b56b353` | roots, January pages, six direct research-lead calendar pages |
| `accesss-2021-2025/provenance.json` | 55 | `9d1579624409dbedf65e5e17f31e51ac4dc70da2c851d6af0ccc9f307f8bc854` | official root/search, 2021/2025 months, meetings and 48 result pages |
| `accesss-exception-2019/provenance.json` | 4 | `b8c0f8283d5f090b19361220f7560551e3c787174524d0135814e846eee644e3` | official root/search, October month and 2019 exception meeting fragments |

All requests have honest 2026-09-03 UTC requested/observed timestamps in their
external manifests, together with exact method, URL/form, parent relation, media
metadata, byte length and SHA-256. The total Phase 10 candidate record count is 73.
These are research material only: none is a repository fixture, durable capture, formal
bundle evidence, or authorization to reacquire in a test. A fixture/provenance adoption
would require the locator issue and profile qualification to be resolved first.

## Qualification matrix

| Predicate | Result | Reason |
| --- | --- | --- |
| Year/calendar root to month locator | observed | unique official `jan.html` relation in four years |
| Official source-owned daily locator | unqualified | no day-page href/reference in all four supplied month pages |
| Exact target-date HTML grammar | candidate observed | one strict visible h1 in six research-lead pages; source locator missing |
| Planned meeting grammar | candidate observed | regular caption/table shape in four ordinary pages |
| Planned all-row race grammar | candidate observed | two 12-row tables on four ordinary samples |
| Planned start grammar | candidate observed | bounded time in regular table, explicitly planned only |
| Provider-day complete meeting/race enumeration | unqualified | daily locator absent; no formal all-meeting guarantee or zero semantics |
| accessS actual meeting/race equality | sampled positive only | 4 ordinary 24-race dates match visibly; no universal proof |
| Exception difference fail closed | observed | 2019-10-12 cancellation/substitute mismatch must reject |
| PDF dependency removable | no | alternative profile is not qualified |
| Phase 4/7 amendment | none | predicates above do not meet qualification threshold |

## Blockers and stop condition

1. Obtain a formal official source-owned locator relation to a historical daily program
   page. A documented, unique parent page/link/navigation contract must be evidence,
   not URL construction from `target_date`.
2. Prove that the admitted daily page is a complete provider-day planned meeting/race
   enumeration for the narrow ordinary profile, and separately prove no-race/missing
   behavior. Page existence and sampled 12-row tables are insufficient.
3. Establish a reviewed exact binding from calendar visible meeting/race tuples to
   accessS-originated external identities without display-name ambiguity.
4. Maintain the existing planned/actual and exceptional fail-closed boundaries.
   Planned time cannot become actual time; cancellation/substitute/partial/zero cases
   remain unsupported absent a separately qualified source contract.

Until every blocker is resolved, the future result for this candidate profile remains
whole-day `TARGET_DISCOVERY_INCOMPLETE`. No Phase 4 or 7 amendment, PDF removal,
production implementation, test/fixture materialization, or next phase is authorized.

## Allowed Files

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Forbidden Files and actions

All other repository files, including production, tests, fixtures, dependencies,
NAR/shared domains, SQLite/migrations/schema/database, logs, archives, CLI and
release/tag history. No implementation, materialization, staging, commit, push,
execution phase or phase advance occurs during this PREPARE.

## Required PREPARE verification

```text
git diff --check
git diff --name-only
git status --short
git diff --cached --name-only
```

Require exactly the two documentation paths and an empty index. No tests are required
or run for this research/docs-only PREPARE.
