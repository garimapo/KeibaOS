# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6d1d1` — JRA historical odds evidence/domain PREPARE.

Formal base: `0135cee4ad8e578e6bd20940b16198a576172c04`.

Approved d1d PREPARE reference: `3e7de6780c9fb8af6169d015b942bd4d72dde576`.

Review branch: `review/4c-2d3b1i6d1d1-odds-prepare`.

## Official Finding and Semantics

`OFFICIAL_HISTORICAL_FINAL_ODDS_SOURCE = PROVEN_JRA_ACCESSO_POST`.

JRA's official FAQ states that a finished race's `最終オッズ` is available from `レース結果`.  A completed official accessS result page has its race-specific `オッズ` navigation expressed as:

```text
POST https://www.jra.go.jp/JRADB/accessO.html
Content-Type: application/x-www-form-urlencoded
cname=pw151ou10<VV><YYYY><MM><DD><RR><YYYYMMDD>Z/<TT>
```

The CNAME is copied from the official result-page navigation, not synthesized.  Observed completed-race examples include:

```text
pw151ou1006202601050720260112Z/E1
pw151ou1009202603050420260620Z/49
pw151ou1010202601121020260301Z/43
```

Their returned response is server-rendered strict CP932 HTML, titled `単勝・複勝オッズ（馬番順）`, not a JavaScript-loaded data payload.  It contains one `table.tanpuku` with direct columns `馬番`, `馬名`, `単勝`, and `複勝（3着払い）`; every selected historical horse row can therefore be associated with its displayed final `単勝` by race-local horse number.  The response contains all horses' final single-win odds for that race.

`past_race.record_values["odds"] = OFFICIAL_FINAL_SINGLE_WIN_ODDS`.  It is the direct final `td.odds_tan` decimal token from the archived official accessO response.  It is not popularity, payout, probability, a margin conversion, a model estimate, an odds snapshot fetched at another time, or a later/current substitute.  Parse its exact approved decimal lexical token directly with `Decimal`, never through float; require finite and strictly positive for the initial completed-result envelope.

JRA's publication describes final odds, but this phase does not assume a current page is immutable or historically available.  The only trusted value is the exact archived raw response observed at its recorded time.

## Identity and Cross-Response Binding

The accessO CNAME's provider-native identity is the same tuple already used by `JRAExternalRaceIdentity`:

```text
venue_code, year, meeting_number, meeting_day, race_number, calendar_date
```

Its observed grammar is exact:

```text
pw151ou10<VV><YYYY><MM><DD><RR><YYYYMMDD>Z/<TT>
VV = 01..10
YYYY = ASCII four digits
MM = 01..99
DD = 01..12
RR = 01..12
calendar date = real YYYYMMDD with matching year
TT = two uppercase hexadecimal characters
```

The final-odds response must independently expose one official accessO race header and its `table.tanpuku`.  Its visible date, frozen venue mapping, meeting number, meeting day, and race number must each agree with the accessO CNAME and with the paired accessS identity.  A valid lexical CNAME alone does not prove a race.

The future JRA normalizer keeps stable-horse identity exclusively from the unique matched accessS row-local accessU anchor through `parse_jra_horse_profile_url_identity`.  It cross-checks exactly:

```text
accessS matched horse row td.num
==
accessO unique matched odds row td.num
```

The accessO horse name is not an identity key and cannot override this number cross-check.  Horse number is race-local only; it does not become the historical stable horse identity or provider record ID.

## Causality

```text
available_at = None
observed_at = supplied exact archived capture time
```

HTTP `Date`, race date, result finalization, and accessO display text are not a precise availability timestamp.  The normalizer must preserve each supplied response's observation unchanged.  Existing snapshot assembly remains the only owner of causal eligibility: every accessS and final-odds evidence observation must satisfy `observed_at <= captured_at <= information_cutoff`.  A page fetched today cannot be backdated for historical replay.

## Required Capture-Domain Extension

`JRA_CAPTURE_EXTENSION_REQUIRED = YES`.

The current JRA capture boundary accepts only GET-resolved accessS and accessU source URLs.  Official historical final odds is an accessO POST navigation, so it requires a third page kind:

```text
JRAOfficialPageKind.FINAL_WIN_ODDS = final_win_odds
```

The smallest truthful extension must make the CNAME from the official POST navigation a validated canonical request locator, with canonical delimiter `%2F` and no guessed CNAME generation.  It must distinguish that locator from the actual POST endpoint (`/JRADB/accessO.html`): the live transport submits exactly one form field `cname=<validated CNAME>` by POST; it must not claim a GET query response produced those bytes.  The supplied/capture/archive representation must retain a deterministic canonical locator carrying the exact validated CNAME, so that its response is auditable and race-bound.

The extension requires a public `parse_jra_final_win_odds_url_identity` or equivalent narrowly scoped public identity parser returning the existing `JRAExternalRaceIdentity`; existing accessS/accessU parsing remains unchanged.  `JRASuppliedOfficialResponse`, `JRAOfficialResponseCapture`, and archive lookup must accept this third kind only after its canonical request-locator validation.  Raw response SHA-256 continues to cover exact returned CP932 bytes only, before decoding.

The live service needs a page-kind-directed POST transport path while preserving the frozen capture ordering, TLS verification, no redirects, identity content coding, 10/10 timeout, no retries, 4 MiB byte limit, exact Content-Length check, archive-before-return, and no pacing.  It must retain no unapproved request-body persistence beyond the CNAME encoded in the canonical request locator.

Dedicated JRA capture schema v1 has `page_kind IN ('race_result','horse_profile_history')`.  SQLite cannot alter that CHECK in place, so a dedicated archive v002 migration must rebuild or replace the capture table atomically to admit `final_win_odds`, preserve existing captures, and keep the global migration registry untouched.  `MIGRATION_REQUIRED = YES` for this dedicated JRA archive only; no global simulator migration is authorized by this PREPARE.

## Evidence-Role Decision

`C1A_EVIDENCE_EXTENSION_REQUIRED = YES`.

The current provider-neutral `past_race` evidence set is exactly:

```text
historical_race_context
historical_race_result
```

Option A is rejected.  Binding accessS (the official result page that supplies finish/time/body-weight/jockey/etc.) to `historical_race_context` and binding accessO only to `historical_race_result` would make both semantic role names misleading and obscure which raw evidence establishes race-result facts.

Option B is selected as the smallest truthful model: retain the existing two roles for current NAR records unchanged, and extend the provider-neutral past-race evidence contract to allow an explicit ordered three-response semantic set for the JRA final-odds case:

```text
historical_race_context
historical_race_result
historical_race_final_odds
```

For JRA, accessS must bind `historical_race_context` and `historical_race_result` only if a separate c1a design proves same-response role reuse remains semantically truthful; otherwise that prerequisite must choose a non-misleading generic result/context role assignment before implementation.  AccessO binds exactly `historical_race_final_odds`.  The c1a prerequisite must freeze accepted per-provider role sets, canonical ordering, source-ID schema/version behavior, snapshot digest/provenance behavior, transition/compatibility policy, and any needed global snapshot migration before JRA normalizer work.  It must preserve every existing NAR two-role past-race record unchanged.

No normalizer may omit accessS result evidence, conceal accessO evidence, reuse a role for two distinct response identities, or treat timestamps as source-ID inputs.

## Field Ownership and Fail-Closed Policy

```text
accessS: historical race identity/date/place/name/class/distance/surface/weather/condition,
         selected stable horse, race-local horse number, finish, race_time, body weight/change,
         jockey, popularity, passing order, fourth-corner position.
accessO: final single-win odds only.
accessS horse number == accessO horse number: mandatory cross-check.
```

The future normalizer must fail closed for absent/malformed/ambiguous odds response, accessS/accessO CNAME or visible-race identity disagreement, missing/duplicate horse number, failed horse-number match, target stable-horse mismatch, missing/nonnumeric/nonpositive odds, cancellation/exclusion or other state without valid final-odds semantics, malformed official layout, and causally late evidence when assembling a replay snapshot.

## Architecture Decision and Follow-up

```text
ARCHITECTURE_DECISION = BOTH_EXTENSIONS_REQUIRED
JRA_FINAL_ODDS_NORMALIZER_IMPLEMENTATION = BLOCKED
NAR_UNCHANGED = YES
NAR_LINEAGE_TO_JRA_HORSE_ID_LINK = NOT_PROVEN
MIXED_HISTORY_COLLECTION_READY = NO
```

Recommended next phase: `4C-2d3b1i6d1d2 — provider-neutral historical final-odds evidence-role PREPARE`.  It is docs-only and must settle the c1a/snapshot role-set and source-ID transition before either capture or JRA normalizer implementation proceeds.

Exact next-phase allowed files:

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

The later, separately approved JRA final-odds capture implementation is expected to require only:

```text
scripts/simulation/jra_official_identity.py
scripts/simulation/jra_official_response_capture.py
scripts/simulation/jra_official_response_capture_migration.py
scripts/simulation/jra_official_response_capture_migration_runner.py
scripts/simulation/repositories/sqlite_jra_official_response_capture_repository.py
scripts/simulation/jra_official_response_live_capture.py
tests/test_jra_official_identity.py
tests/test_jra_official_response_capture.py
tests/test_jra_official_response_capture_migration.py
tests/test_sqlite_jra_official_response_capture_repository.py
tests/test_jra_official_response_live_capture.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

That expected list does not authorize implementation and does not include a global migration, NAR file, normalizer, fixture, bridge, or acquisition orchestration.

## Allowed Files

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Stop Condition

Stop for independent architecture review.  Do not implement d1d2, c1a evidence changes, accessO capture, live POST transport, JRA historical normalizer, fixture capture, bridge, NAR work, or acquisition orchestration.
