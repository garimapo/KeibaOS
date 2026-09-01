# Current Phase

Status: `APPROVED_FOR_COMMIT`

## Identity and authority

- Phase: `POST_V0_8_DAILY_REPLAY_4`
- Name: `Historical Daily Supported Coverage Contract Design`
- Base Commit: `6b7b153cab518538ee0f2c9c5682ce79b6ebf7a2`
- Branch: `feature/post-v0.8-daily-replay`
- Release baseline: `v0.8.0` at `c08bedb5421b44d63a8bac017699efffca2a4b73`
- Phase type: `RESEARCH_AND_DESIGN_ONLY`
- Overall research/design outcome: `IMPLEMENTABLE_SUPPORTED_PROFILE`
- Production implementation: `NOT_AUTHORIZED`
- Test implementation: `NOT_AUTHORIZED`
- Migration / schema / database change: `NOT_AUTHORIZED`
- Stage / commit / push during PREPARE: `NOT_AUTHORIZED`
- `EXECUTE_APPROVED_PHASE`: `NOT_AUTHORIZED`
- Release/tag/history mutation: `FORBIDDEN`

This phase is prepared in the fresh clone
`C:\Users\garim\Desktop\KeibaOS-post-v0.8`. The old Ver0.8 working repository is
outside this work and must not be changed.

## Objective and decision

Define the smallest historical-day support profile which can construct the Phase 2
audited complete denominator without claiming universal historical coverage. A
requested provider/date is accepted only as `SUPPORTED_COMPLETE_DAY`; every other
case is `TARGET_DISCOVERY_INCOMPLETE`. There is no partial-day result, reduced venue
set, reduced race list, best-effort fallback, or hidden skip.

The Phase 3 universal conclusions remain unchanged:

```text
JRA universal qualification: UNPROVEN
NAR universal qualification: UNPROVEN
```

Phase 4 nevertheless finds an implementable date-specific supported profile. The
profile is a conjunction of positive, machine-checkable predicates over exact official
evidence. It does not accept a day merely because it looks ordinary, and it does not
turn source or normalization feasibility into proof of provider-day completeness.

## Governing invariants

- `NO FUTURE LEAKAGE`
- `NO HINDSIGHT`
- `FAIL CLOSED`
- `NO SILENT FALLBACK`
- `NO HIDDEN SKIP`
- `NO CURRENT-CLOCK CAUSALITY`
- exact provider, partition, meeting, and race identity
- deterministic ordering independent of SQLite row order or acquisition order
- no invented race number, meeting, venue, date, or status
- no current/live page backdating
- exact raw bytes, digest, request identity, and honest acquisition observation
- acquisition/preparation remains separate from no-network historical replay
- no prediction, bet generation, normalizer, settlement, or replay reimplementation
- no Ver0.8 contract, tag, or release-history mutation

## Research boundary

Only read-only official public-source research was performed. Responses observed in
this phase are research material, not formal replay evidence, were not archived or
inserted into a repository database, and acquire no historical `observed_at` merely
because their target dates are old. A future authorized acquisition must record its
own exact retrieval time and must not backdate it.

Search/navigation may locate official material, but only official `jra.go.jp` and
`keiba.go.jp` responses support the conclusions below. The research material was kept
outside the repository. No fixture or provider archive was created.

## Historical replay race-target definition

The candidate formal definition is:

> A historical replay race target is one exact provider-native race identity which
> official historical target-list evidence positively enumerates for `target_date`,
> whether the race was ultimately conducted or is formally preserved as non-run.

Consequences:

- an ordinary enumerated race is a target;
- a race cancelled after identity publication is a target only when the official
  historical evidence still preserves that exact identity;
- a whole meeting cancelled before exact race identities are available does not
  authorize hypothetical race targets;
- absence of identities in that case also does not prove a zero-race denominator;
- a substitute meeting is a target only when official evidence supplies its exact
  target-date identity and the original/replacement relation is not contradictory;
- an original scheduled meeting contributes races only when their exact identities
  remain positively preserved; and
- meeting existence, a likely 1-to-12 program, display venue, or race-number continuity
  must never synthesize a race identity.

This definition does not weaken Phase 2. When a partition is proven but its individual
race identities cannot be recovered, Phase 4 chooses **Option 1**: the whole requested
provider/date is `TARGET_DISCOVERY_INCOMPLETE`. Option 2, a partition-level non-run with
zero canonical race targets, is rejected because it cannot prove a complete race
denominator.

## Exact `SUPPORTED_COMPLETE_DAY` contract

For every provider in the requested closed provider scope, all of the following must
be true. One failure makes the whole application `TARGET_DISCOVERY_INCOMPLETE`.

1. `target_date` is an exact calendar date and the provider identity is the exact
   closed identity `JRA` or `NAR`; aliases and display-name matching are forbidden.
2. The date satisfies the initial historical-floor gate and every required official
   source family is still addressable at acquisition time.
3. One exact provider-day envelope and every required subordinate fragment are
   captured as immutable raw bytes with canonical request identity, source URL or POST
   locator, response digest, response metadata, and honest `observed_at`.
4. Each response strictly decodes under its own fragment-family contract. HTML, PDF,
   and other binary fragments are not assigned one provider-wide charset.
5. The envelope yields exactly one target-date provider partition set; date, provider,
   and partition identities must agree visibly and lexically.
6. Every partition has exactly one required race-list fragment. No fragment is missing,
   duplicated, selected by arbitrary latest time, or silently discarded.
7. Every structural row in every fragment must normalize exactly once. A malformed,
   unknown, duplicate, or contradictory row is a whole-day failure, never a skip.
8. The provider-specific positive coverage relations below hold exactly. Set equality,
   not count equality or contiguous race numbers, is required.
9. Every replay-candidate target has an exact aware `scheduled_start_at` supplied by
   formal official evidence. A native exceptional target may retain `None` only under
   the approved Phase 2 rule. Display timetables are never guessed.
10. No unresolved cancellation, substitute, postponement, abandonment, status, request
    identity, or original/replacement identity can affect denominator membership.
11. The normalized target tuple is unique. Duplicate or contradictory evidence has no
    tie-break and fails the whole day.
12. Targets are ordered only by the Phase 2 canonical key
    `(organization, source_system, external_race_id)` and are frozen into the shared
    provider-neutral `HistoricalDailyTargetEvidenceBundle` and audited immutable
    `DailyHistoricalReplayTargetSet` projection.

A proven complete positive non-zero target set may be `SUPPORTED_COMPLETE_DAY`. A
zero-row result is never accepted by absence: the approved positive-zero contract is
still unavailable, so initial zero days fail closed.

## JRA initial supported profile

### Official composite

The proposed ordinary-day composite is:

```text
exact historical year program page (exact canonical request/reference and bytes)
  -> unique formally recognized 開催日割表 link, including an explicitly labeled
     revised version when that is the uniquely resolvable official schedule version
  -> exact OFFICIAL_YEAR_PROGRAM_SCHEDULE_VERSION PDF: official schedule meeting set
  -> exact per-meeting bangumi PDF: official program race-identity tuple

exact accessS past-result-search POST response for target year/month
  -> actual-history target-date meeting-selection locator set
  -> one exact accessS race-selection POST response per meeting
  -> exact actual-history race-identity tuple per meeting
  -> one exact supplied accessS race-result href per race for official displayed
     target date/identity/start-time facts
```

JRA is supported initially only when:

- the selected official schedule version's meeting identity set equals the accessS
  actual-history meeting identity set for the exact date;
- every official schedule meeting has exactly one official bangumi fragment and exactly one
  accessS race-selection fragment;
- for each meeting, the exact official program race identities enumerated by the
  bangumi fragment equal those enumerated by the accessS actual-history race-selection
  fragment;
- every race-selection href parses to the same year, venue code, meeting number,
  meeting day, race number, and target date;
- each exact accessS race page visibly agrees with that identity and supplies an exact
  official displayed start time that a future strict normalizer can convert to an
  aware `scheduled_start_at` without current-clock input; and
- no fragment exposes an exceptional or contradictory state which the initial profile
  has not explicitly approved.

The per-meeting bangumi equality is essential. Annual meeting schedules alone cannot
detect a missing race, and accessS result rows alone cannot prove that a cancelled race
was never silently removed.

`OFFICIAL_YEAR_PROGRAM_SCHEDULE_VERSION` means only that the exact historical year
program page formally supplies the selected official schedule table. It may be an
explicitly labeled revised version. It is not asserted to be the original pre-race
plan, a prediction-time schedule, or a prediction information cutoff. It is
later-acquired completeness/audit evidence and must never flow into
`PredictionPipeline`, snapshot selection, or settlement causality.

The 2020 official year program page is a concrete reason for this distinction: research
observed multiple change documents and a schedule labeled
`開催日割表（2020年4月6日変更版）`. Its existence does not prove an original pre-event
schedule; it proves that schedule-version semantics and unique official selection must
be part of the source contract.

### JRA request, schedule-version, and byte contract

- Program entry: the exact historical year program page reached through a frozen
  canonical official URL or exact official navigation link. The future source contract
  must freeze redirect/canonical behavior; `/YYYY/` and `/YYYY/index.html` are not
  equivalent aliases by assumption.
- Official schedule meeting envelope: identify on the captured year page the unique
  formally recognized `開催日割表` schedule link. Retain its exact visible label/title
  and exact href, and allow an explicitly labeled revised version when the source
  semantics resolve it uniquely as the official schedule version. Capture the exact
  PDF bytes and digest and bind the selected evidence version to the year-page
  reference and digest. Zero matching schedule links fails closed. Multiple potentially
  operative schedule links whose semantics cannot be resolved uniquely fail closed and
  return for ChatGPT review.
- Selection by guessed filename, a hard-coded `nittei` name alone, first PDF, link
  position, filesystem/download time, or current clock is forbidden.
- Official program race fragments: take each exact per-meeting bangumi href from the
  captured year page. Its visible label/context must bind it to one exact normalized
  meeting identity; filename alone is never identity. Capture opaque exact PDF bytes
  plus digest. A future strict grammar must recognize every required day/race row;
  malformed or unrecognized layout fails the provider/date, and OCR or guessed race
  numbers are forbidden.
- Historical actual envelope: POST to exact
  `https://www.jra.go.jp/JRADB/accessS.html` using the exact `cname` request grammar and
  year/month token supplied by the official accessS past-search response. Tokens are
  not guessed or recomputed independently of that response.
- Meeting fragments: exact accessS race-selection `cname` locators supplied by the
  historical month response.
- Race fragments: exact accessS race-result hrefs supplied by each meeting fragment;
  the existing JRA lexical race identity and canonical result-URL rules are reused.
- The official-schedule/accessS equality compares exact meeting identities and exact
  race identities, never counts, display labels, or inferred race-number continuity.
- JRA program and accessS HTML are strict CP932/Shift_JIS-family fragments when their
  formal response metadata/body declaration agrees. The PDFs are opaque exact binary
  bytes and have no HTML charset contract.

Research confirmed the accessS past-search page itself supplies selectable years back
to 1986, a deterministic year/month token table, and exact meeting-selection locators.
This is source navigation evidence, not permission to synthesize an unknown CNAME.

### JRA exceptional-state decisions

| Case | Initial decision | Reason |
|---|---|---|
| ordinary official-schedule=actual-history day, with exact race-set equality | `SUPPORTED_INITIAL_PROFILE` | both meeting and race denominators are positively cross-checked |
| official schedule meeting absent from actual history | `DEFERRED_FAIL_CLOSED` | official-schedule/actual-history meeting sets disagree; exact status/identity contract is not universally qualified |
| substitute meeting later conducted | `DEFERRED_FAIL_CLOSED` | additional/moved actual meeting creates an unresolved original/replacement relation |
| partial or race-level cancellation | `DEFERRED_FAIL_CLOSED` | no reviewed universal native row-status mapping proves preservation; a race-set mismatch fails closed |
| zero-racing date | `DEFERRED_FAIL_CLOSED` | official schedule absence plus accessS absence is not a positive actual-zero assertion |

No reduced meeting set is rerun. A JRA disagreement rejects the provider/date in full.

## NAR initial supported profile

### Official composite

```text
MonthlyConveneInfo historical year/month envelope
  -> exact marked venue set for target_date
  -> one exact date-qualified RaceList link supplied by the envelope per marked venue
  -> strict all-row race identity/time normalization per RaceList
  -> same-day RaceList navigation venue set used only as consistency evidence
  -> exact provider-native non-run text/status retained when formally present
```

NAR is supported initially only when:

- the MonthlyConveneInfo target-date marked venue set is non-empty and has no `△`
  substitute marker or unknown mark;
- each marked cell supplies exactly one official RaceList locator for the same exact
  date and venue;
- exactly one RaceList fragment is captured for every marked venue;
- each RaceList visibly agrees with its date and active venue identity;
- every RaceList same-day navigation set equals the MonthlyConveneInfo marked venue
  set and equals the union of captured RaceList venue identities;
- each structural race row yields exactly one canonical NAR external identity and an
  exact official displayed start time, with no skip or guessed value;
- duplicate race identities, malformed rows, status ambiguity, or contradictory
  navigation fail the whole day; and
- any accepted non-run case retains every exact race row and exact provider-native
  disposition evidence without normal-race fallback.

RaceList same-day navigation is consistency evidence only. It cannot replace or expand
the MonthlyConveneInfo envelope. A navigation-only venue, envelope-only venue, missing
fragment, or unequal set is `TARGET_DISCOVERY_INCOMPLETE`.

### NAR canonical request identity

The canonical RaceList request is the exact raw locator supplied by the captured
official MonthlyConveneInfo envelope, not a URL reconstructed from known date and venue
facts:

1. Capture exact MonthlyConveneInfo raw response bytes under a separately versioned
   source-family contract. Until official navigation, form material, or a raw official
   href proves one exact ordering, its request identity is the exact endpoint/path,
   required year/month parameter set, and exact official-supplied request material; a
   manually ordered `?k_year=YYYY&k_month=M` string is not authoritative by itself.
2. From each accepted marked target-date cell, take the exact raw RaceList `href`
   attribute supplied by that captured envelope.
3. Apply HTML entity decoding only, resolve the result against the exact approved
   official base/origin, and validate the allowed official host and exact path
   `/KeibaWeb/TodayRaceInfo/RaceList`.
4. Freeze the official-envelope-supplied raw href request material, including parameter
   names, order, spelling, percent encoding, and `babaCode` spelling exactly as supplied.
   Do not reorder, rebuild, pad, decode/re-encode, or canonicalize it from known
   `babaCode` and date facts.
5. Do not accept `www2`, literal-slash dates, reversed query order, zero-padded
   babaCode, or any other alternate as an alias merely because a current server
   redirects or returns semantically similar bytes.

Research showed that current responses often tolerate reverse query order and literal
slashes, `www2` redirects to `www`, and `03` can return a different byte representation
from `3`. Those observations justify using the exact envelope-supplied locator rather
than normalizing alternates by assumption. If raw official href spelling or ordering
varies across supported years, a future source contract must preserve or explicitly
version that behavior; it must not normalize it speculatively and must stop for review
when the contract cannot account for the variation.

NAR MonthlyConveneInfo and RaceList HTML are separate strict UTF-8 fragment families.
Any future binary supplemental evidence remains opaque exact bytes plus digest.

### NAR exceptional-state decisions

| Case | Initial decision | Reason |
|---|---|---|
| ordinary day satisfying all equality and strict-row predicates | `SUPPORTED_INITIAL_PROFILE` | positive venue envelope and complete per-venue target rows agree |
| partial race cancellation with exact preserved row | `DEFERRED_FAIL_CLOSED` | no reviewed row-level native status example yet proves a safe normalized contract |
| whole meeting cancellation with exact preserved race rows and exact native no-substitute text | `SUPPORTED_INITIAL_PROFILE` | the denominator remains exact; all rows stay targets and later execution classification remains separate |
| substitute date marked `△` | `DEFERRED_FAIL_CLOSED` | original/replacement identity relation is not qualified |
| original cancelled date without exact race identities | `DEFERRED_FAIL_CLOSED` | partition-level evidence cannot replace exact race identities |
| all-blank or apparent zero date | `DEFERRED_FAIL_CLOSED` | blank semantics are not a positive zero contract |

The tested 2025-12-26 Kanazawa page is the narrow whole-meeting-cancellation example:
MonthlyConveneInfo includes Kanazawa, RaceList states that the meeting was cancelled
with no substitute, and the page preserves exact race rows 1 through 12. The support
decision depends on those exact retained rows and native statement, not on numerical
continuity. A different cancellation page without retained identities fails closed.

## Initial historical support floor

Result: `SUPPORTED_FLOOR_PROPOSAL`

```text
initial floor: 2020-01-01 (inclusive)
```

This is a conservative admission gate, not a claim of permanent retention and not a
replacement for per-date source predicates. Research observed:

- JRA year program pages, annual nittei PDFs, and first-meeting bangumi PDFs for every
  year 2020 through 2025;
- JRA accessS historical January month responses and first-day race-selection
  fragments for every year 2020 through 2025;
- NAR January MonthlyConveneInfo and exact RaceList fragments for every year 2020
  through 2025; and
- stable provider-native identity shapes across those tested years.

The JRA January first dates yielded two meetings and 12 exact accessS race identities
per meeting for 2020-01-05, 2021-01-05, 2022-01-05, 2023-01-05, 2024-01-06, and
2025-01-05. NAR 1 January envelope/navigation equality was observed for 2020 through
2025. These cases support a 2020 floor proposal, but every runtime preparation still
fails closed if any required family is unavailable or contradictory. Dates before the
floor are unsupported even if one fragment happens to remain reachable. Expansion
requires another reviewed phase.

## Source-support predicate matrix

`SATISFIED` below means the initial profile has a positive source predicate; it does
not mean universal provider history is qualified.

| Source-support predicate | JRA initial profile | NAR initial profile |
|---|---|---|
| exact historical date addressable | `SATISFIED` by year program + accessS month | `SATISFIED` by year/month envelope + date-qualified links |
| positive official-schedule/provider-day partition envelope | `SATISFIED` by selected official schedule version PDF | `SATISFIED` by MonthlyConveneInfo marked set for accepted non-zero/non-`△` dates |
| positive actual partition set | `SATISFIED` by accessS month meeting locators | `SATISFIED` by exact captured RaceList identities, with navigation as consistency only |
| official-schedule/actual-history partition equality | `REQUIRED_EXACT` | `REQUIRED_EXACT` across envelope, fragments, and navigation |
| exact official program race tuple per partition | `SATISFIED` by exact bangumi PDF rows | `NOT_SEPARATE`; qualified RaceList is the formal partition target list |
| exact historical race-list tuple | `SATISFIED` by accessS meeting fragment | `SATISFIED` by strict RaceList all-row normalization |
| official-program/actual-history race-tuple equality | `REQUIRED_EXACT` | `NOT_APPLICABLE`; no inferred second list |
| exact scheduled start for replay candidate | `REQUIRED` from exact accessS race fragment | `REQUIRED` from exact RaceList row |
| canonical official request identity | `SATISFIED` by supplied program hrefs and supplied accessS POST locators | `SATISFIED` by exact MonthlyConveneInfo-supplied RaceList href rule |
| exact response bytes and digest | `SATISFIED` per HTML/PDF family | `SATISFIED` per HTML family |
| positive zero | `UNSUPPORTED` | `UNSUPPORTED` |
| whole-meeting cancellation | `UNSUPPORTED_INITIAL` | `SUPPORTED_ONLY_IF_EXACT_ROWS_AND_NATIVE_NO-SUBSTITUTE_EVIDENCE` |
| substitute/original relation | `UNSUPPORTED` | `UNSUPPORTED` |
| partial/race-level cancellation | `UNSUPPORTED_INITIAL` | `UNSUPPORTED_INITIAL` |
| no silent skip | `REQUIRED_EXACT` | `REQUIRED_EXACT` |
| missing/duplicate/contradictory behavior | whole-day fail closed | whole-day fail closed |
| observed availability at 2020 floor | `SATISFIED_IN_RESEARCH` | `SATISFIED_IN_RESEARCH` |

## Implementation and audit feasibility matrix

These rows describe whether later work can build and audit the contract. They do not
qualify source completeness and authorize no code in this phase.

| Feasibility concern | JRA | NAR |
|---|---|---|
| exact raw byte capture and SHA-256 | feasible for CP932 HTML and opaque PDFs | feasible for UTF-8 HTML |
| honest aware `observed_at` | feasible; future acquisition time only | feasible; future acquisition time only |
| exact request fingerprint | feasible from endpoint, method, exact official-supplied `cname`/href, and version | feasible from exact official-supplied envelope request material/raw href and version |
| exact provider/race identity reuse | reuse `JRAExternalRaceIdentity` and strict accessS URL parsing | reuse `nar:YYYYMMDD:babaCode:raceNo` grammar and positive decimal tokens |
| existing capture repository reuse | exact accessS result loads are reusable; month/selection/PDF families need separately reviewed capture design | exact NAR capture primitives inform the design; Monthly/RaceList kinds need separately reviewed capture design |
| existing normalizer reuse | existing accessS identity/header domains can be reused where they own facts; strict month/PDF/list normalizers are new future work | legacy `NARParser` is forbidden; exact NAR URL/identity primitives are reusable; strict envelope/list normalizers are new future work |
| PDF normalization | new versioned strict layout contract required; extraction failure is whole-day failure | not required for the initial composite |
| strict no-skip normalization | feasible but not implemented | feasible but not implemented |
| acquisition/no-network replay separation | feasible through immutable prepared evidence bundle | feasible through immutable prepared evidence bundle |
| deterministic bundle/target-set digest | feasible after a later phase freezes versioned canonical bytes | feasible after a later phase freezes versioned canonical bytes |
| durable storage/migration | not designed or authorized here | not designed or authorized here |

Existing repositories must not be bypassed merely to reconstruct a formal domain from
raw rows. Conversely, existing accessD target-input normalization cannot be reused on a
newly observed historical card when its formal causal contract requires observation no
later than scheduled start. A future implementation must stop for review rather than
weaken that invariant.

## Coverage construction and failure boundary

The future preparation boundary is conceptually:

```text
exact requested target_date + closed provider scope
  -> acquire/freeze every profile-required official fragment
  -> strict provider-specific normalization
  -> exact coverage-relation checks
  -> SUPPORTED_COMPLETE_DAY or TARGET_DISCOVERY_INCOMPLETE
  -> only on support: shared HistoricalDailyTargetEvidenceBundle
  -> audited immutable DailyHistoricalReplayTargetSet
```

No evidence resolver, snapshot selection, manifest builder, replay runner, persistence,
or reporting work occurs in this phase. Later replay remains no-network. For a mixed
closed scope such as `{JRA, NAR}`, both provider-day profiles must pass; one provider
failure rejects the complete requested scope.

## Digest boundary

Phase 2 still owns `content_sha256` as the sole target-set content identity. Phase 4
does not implement serialization. A later implementation design must version and
freeze canonical bytes, including schema identifier, exact field ordering, canonical
datetime representation, canonical Unicode/string rules, canonical tuple ordering,
and exact byte encoding. Python `repr`, unordered mappings, locale formatting,
filesystem metadata, SQLite row IDs/order, redirects, and current time are forbidden
digest material.

## Existing repository domains to reuse

- `scripts/simulation/jra_official_identity.py` for exact JRA race identity and strict
  supplied accessS/accessD URL identity rules.
- `scripts/simulation/jra_target_race_card_locator.py` and
  `jra_target_race_card_discovery.py` as examples of supplied-navigation, exact POST
  request fingerprints, unique table/row requirements, and no arbitrary choice. They
  do not themselves prove an historical daily denominator.
- `scripts/simulation/jra_official_response_capture.py` and its SQLite repository for
  immutable exact-byte/digest/observation patterns and exact accessS result loads.
- `scripts/simulation/jra_historical_past_race_source.py` only for formal accessS facts
  it already owns; it is not a daily discovery source.
- `scripts/simulation/nar_official_response_capture.py` and its repository for strict
  host/path/query, byte, digest, and provenance patterns.
- `scripts/simulation/nar_historical_input_source.py` for canonical positive-decimal
  NAR identity grammar and formal facts it already owns.
- `scripts/providers/nar_provider.py` and `scripts/parsers/nar_parser.py` must not be
  reused as the historical completeness boundary: they are mutable/live-oriented,
  write logs, infer encoding, and silently skip malformed rows.

No existing formal API is broadened for convenience in this phase.

## Unresolved blockers deferred to implementation or expansion review

The supported profile is implementable as a contract, but none of these items may be
guessed during implementation:

1. A strict versioned JRA year-program HTML source contract must freeze its canonical
   request/reference, redirect behavior, recognized schedule label semantics, revised
   version selection, exact supplied hrefs, and ambiguity failure.
2. A versioned strict JRA nittei PDF normalization grammar and layout-version
   recognition must be designed and tested. Opaque PDF capture alone is not a
   normalized meeting denominator.
3. A versioned strict JRA bangumi PDF grammar must bind exact year-page link context to
   an exact meeting and recognize every required day/race row without OCR, filename
   identity, or guessed race numbers.
4. A strict accessS month and meeting-selection normalizer must prove unique structural
   rows and preserve supplied POST locators without inventing tails.
5. The exact accessS selector and semantics used for the displayed start time must be
   frozen. If it cannot support Phase 2 `scheduled_start_at` without ambiguity, JRA
   dates remain fail closed and the design returns for ChatGPT review.
6. A versioned strict NAR MonthlyConveneInfo raw-href grammar must preserve official
   parameter spelling, order, and encoding and must reject unsupported variation rather
   than reconstruct a locator.
7. A versioned strict NAR RaceList all-row grammar must reject every malformed,
   duplicate, silently skipped, or unrecognized target row.
8. NAR row-level partial cancellation semantics remain unqualified. Only the exact
   preserved whole-meeting/no-substitute case is admitted initially.
9. Provider-neutral disposition enum/mapping remains deferred; native evidence is
   preserved exactly as Phase 2 requires.
10. No positive zero-day source contract exists for either provider.
11. A future artifact/persistence phase must freeze canonical serialization and new
   capture kinds before any migration is proposed.

None of these blockers authorizes weakening the predicates. If a later implementation
cannot satisfy one, the affected provider/date is `TARGET_DISCOVERY_INCOMPLETE` or the
phase stops for ChatGPT review.

## Phase gates

Phase 4 is research and design only. `IMPLEMENTABLE_SUPPORTED_PROFILE` means a later
phase has a sufficiently precise contract against which it may separately propose and
test implementation. It does not mean the source parsers or normalizers are ready, and
it does not authorize implementation now. Every production, test, schema, migration,
acquisition/archive, persistence, and CLI change requires a separate `PREPARE_PHASE`,
independent ChatGPT review, and `APPROVE_PHASE`.

## Current phase Allowed Files

Only:

- `docs/CURRENT_PHASE.md`
- `docs/LATEST_CODEX_REPORT.md`

## Forbidden Files and actions

- all production code
- all tests and fixtures
- all migrations and schemas
- `database/**`, including `database/keiba.db`
- `logs/**`
- provider archives or captured research responses
- CLI, manifests, persistence, reporting, and replay artifacts
- stage, commit, push, tag, release, and history mutation during PREPARE
- `EXECUTE_APPROVED_PHASE`
- `POST_V0_8_DAILY_REPLAY_5`

## Required verification

PREPARE completion requires:

```text
git diff --check
git diff --name-only
git status --short
git diff --cached --name-only
```

Expected changed files are exactly the two Allowed Files and the cached diff is empty.
No production or test suite is required or authorized for this document-only phase.

## Stop condition

Stop with `DRAFT_FOR_REVIEW` after updating the two Allowed Files and reporting the
research/design result, matrices, blockers, verification, and complete Phase 4
`docs/CURRENT_PHASE.md` diff. Do not implement, stage, commit, push, start Phase 5, or
acquire/freeze formal provider evidence.
