# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6d1d4` — JRA final-win-odds trusted capture PREPARE.

Formal base: `41f2298820fe029bc06f024ff6da028f21ed5c7c`.

Review branch: `review/4c-2d3b1i6d1d4-jra-final-odds-capture-prepare`.

## Official accessO Protocol Proof

An official completed-race `accessS` page exposes an Odds navigation control that calls official
`/JRADB/js/common2.js` `doAction(url, cname)`. The helper assigns `cname` to the hidden input in the page's
`commForm01`, sets its action to the supplied endpoint, and submits it. The exact form contract observed is:

```text
method   = POST
enctype  = application/x-www-form-urlencoded
field    = cname
endpoint = https://www.jra.go.jp/JRADB/accessO.html
```

For the official completed 2026-01-05 Nakayama 12R result navigation, the source page supplies exactly
`pw151ou1006202601021220260105Z/2E`. The browser wire representation is the standard form body
`cname=pw151ou1006202601021220260105Z%2F2E`; it is not a GET query request. A direct official POST with
`Accept-Encoding: identity` returned 200, no redirect, the same effective endpoint URL, uncompressed `text/html`,
and strict CP932 bytes. No request cookie, session, or referrer was required by the observed response.

The server-rendered document title is `単勝・複勝オッズ（馬番順）　JRA`; its visible heading identifies the race as
`2026年1月5日（月曜）1回中山2日 12レース`. Its `table.tanpuku` has row-local `td.num` horse-number cells and
`td.odds_tan` direct single-win final-odds cells. JRA's official FAQ confirms that a finished-race Odds selection
displays final odds.

## Selected Request-Identity Model

The selected provider-specific model is **B: an immutable POST request locator distinct from URL identity**. A
future JRA identity boundary must add an exact value such as `JRAOfficialFinalWinOddsRequestLocator`, constructible
only from caller-supplied official navigation material:

```text
method          = POST
endpoint_url    = https://www.jra.go.jp/JRADB/accessO.html
form_field_name = cname
form_value      = validated accessO CNAME
```

No API may synthesize this value from a JRA race identity. The approved observed CNAME grammar is:

```text
pw151ou10<VV><YYYY><MM><DD><RR><YYYYMMDD>Z/<HH>
```

`VV` is `01` through `10`; `YYYY` is four ASCII digits; `MM` is the existing JRA meeting grammar; `DD` and `RR`
are the existing meeting-day/race-number grammars; the calendar date is real and has the same year; `Z` is literal;
and `<HH>` is exactly two uppercase ASCII hexadecimal characters. The tail remains opaque. Whitespace, controls,
lower-case or malformed percent escapes, `%252F`, plus encoding, unsupported fields, an alternate endpoint, and any
attempt to derive a CNAME from `JRAExternalRaceIdentity` fail closed.

The future parser returns the existing `JRAExternalRaceIdentity` from the validated locator's venue/year/meeting/day/
race fields. It preserves existing accessS/accessU parsers exactly.

## Page, Capture, and Archive Design — Deferred by Evidence-Locator Blocker

The intended new page kind is exactly:

```text
JRAOfficialPageKind.FINAL_WIN_ODDS = "final_win_odds"
```

Existing `RACE_RESULT` and `HORSE_PROFILE_HISTORY` remain unchanged. `JRASuppliedOfficialResponse`, whose
`response_url` means a canonical GET URL, cannot truthfully represent an accessO POST. A distinct supplied POST
response/value must retain the exact request locator, exact CP932 bytes, and actual observation time without a text
round trip; existing supplied GET response construction remains unchanged.

New final-odds archive rows would require a v002 capture representation with request method and CNAME as capture
identity material. Existing v001 IDs remain `jra-capture-v1:*` unchanged. A v002 final-odds record would use new
`jra-capture-v2:*` material containing schema version, page kind, actual endpoint URL, `POST`, validated CNAME,
body SHA-256, and observed UTC time. It must not change any v001 ID or row reconstruction behavior.

The deferred dedicated v002 table rebuild would retain every v001 column/value and raw body byte unchanged, add
`request_method TEXT NOT NULL` and `request_cname TEXT NULL`, permit only v001 old GET page kinds or v002
`final_win_odds` POST rows, replace the old single evidence index with a v001 partial exact-evidence index and a v002
partial exact-request-evidence index over endpoint, method, CNAME, SHA, and observed time. It would copy v001 rows
with `request_method='GET'` and `request_cname=NULL`, preserve body de-duplication and capture IDs, and retain all
append-only, registry-hardening, corruption, and no-repair rules. The global migration sequence remains through 13.

The deferred live API must preserve `capture_response(*, page_kind, response_url)` exactly for accessS/accessU. A
separate final-odds method taking a validated request locator is required; it must POST exactly one form field and
otherwise retain identity encoding, redirects-disabled, TLS verification, 200-only, retries-zero, 10/10 timeouts,
4 MiB size, canonical Content-Length, raw `decode_content=False`, closing, CP932 delegation, archive-before-return,
and no-pacing policies.

## Provider-Neutral Evidence Locator Blocker

The present `HistoricalInputEvidenceReference.canonical_source_url` contains only one absolute HTTPS URL. Recording
`https://www.jra.go.jp/JRADB/accessO.html?CNAME=...` would falsely claim a GET query request; recording only the
actual endpoint loses the CNAME and makes distinct POST requests indistinguishable when URL, body SHA, and observed
time coincide. The required JRA request locator cannot be carried by the frozen URL-only evidence tuple.

Therefore this phase does **not** authorize v002, archive, or live POST implementation. A provider-neutral,
request-aware evidence-locator design must first decide how c1a source identity, snapshot provenance, persistence,
and exact archive lookup represent an HTTP method plus request material without altering existing GET evidence IDs or
semantics.

```text
FINAL_DECISION = PROVIDER_NEUTRAL_EVIDENCE_LOCATOR_BLOCKER
EVIDENCE_CANONICAL_SOURCE_URL_SEMANTICS =
    Existing URL-only field cannot uniquely and truthfully identify accessO POST evidence.
AVAILABLE_AT = None
OBSERVED_AT = actual capture observation only
HISTORICAL_BACKDATING = FORBIDDEN
```

## Compatibility

```text
EXISTING_ACCESS_S_CAPTURE_IDS_PRESERVED = YES
EXISTING_ACCESS_U_CAPTURE_IDS_PRESERVED = YES
EXISTING_ACCESS_S_LIVE_API_PRESERVED = YES
EXISTING_ACCESS_U_LIVE_API_PRESERVED = YES
CAPTURE_ID_CHANGE_FOR_EXISTING_ROWS = NO
GLOBAL_MIGRATION_FINAL_VERSION = 13
NAR_CAPTURE_UNCHANGED = YES
D1D3_EVIDENCE_ROLE_CONTRACT_UNCHANGED = YES
```

## Recommended Next Work

First: `4C-2d3b1i6d1d4a — provider-neutral request-aware evidence locator PREPARE`. It must resolve the blocker
before any JRA final-odds capture implementation. Its PREPARE allowed files are only:

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

Only after that independent approval may a JRA-specific implementation be split into capture-domain/archive v002 and
live POST transport phases. JRA historical result normalization, an NAR/JRA bridge, acquisition orchestration, and
historical backdating remain out of scope.

## Allowed Files

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Stop Condition

Stop for independent design review. Do not implement accessO capture, a migration, archive changes, live POST
transport, a JRA normalizer, or an NAR/JRA bridge.
