# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6d1d4b` — JRA final-odds capture v002 PREPARE.

Formal base: `906628c5eb5f1639387b3625d494cf133bb27729`.

Review branch: `review/4c-2d3b1i6d1d4b-final-odds-v002-prepare`.

This is design only. It authorizes no production code, test, fixture, migration, database, capture execution, normalizer, bridge, or acquisition change.

## Official POST Request Contract

The approved official JRA accessS navigation proof remains the source of the request contract. Its `doAction(url, cname)` helper writes the lower-case hidden `cname` field in `commForm01`, sets the form action, and submits a form. The exact final-win-odds wire request is:

```text
method:       POST
endpoint:     https://www.jra.go.jp/JRADB/accessO.html
content type: application/x-www-form-urlencoded
form fields:  exactly one, cname=<canonical accessO CNAME>
```

The observed completed-race navigation value was `pw151ou1006202601021220260105Z/2E`; its form entity is exactly `cname=pw151ou1006202601021220260105Z%2F2E`. This is not a GET query request. The observed response was server-rendered strict CP932 HTML, HTTP 200, no redirect, and retained the endpoint as its effective URL. The final-odds page visibly identifies the JRA race and contains row-local horse-number and direct final single-win odds cells. No cookie, session, or referrer is an input to the approved request identity.

The future capture transport must use `Accept-Encoding: identity`, redirects disabled, TLS verification enabled, retry count zero, `(10.0, 10.0)` connect/read timeouts, `response.raw.stream(..., decode_content=False)`, a 4 MiB maximum complete body, canonical ASCII `Content-Length` validation, HTTP 200 only, and strict CP932 delegated to the capture domain. It must not decode/re-encode, parse fields, sleep, discover races, backdate timestamps, or synthesize a request from an external race ID.

## Immutable Request Locator

The selected new provider-owned value is exactly:

```python
JRAOfficialFinalWinOddsRequestLocator(
    endpoint_url: str,
    cname: str,
    external_race_identity: JRAExternalRaceIdentity,
    request_identity_sha256: str,
)
```

It is immutable and accepts only exact values. `endpoint_url` is exactly `https://www.jra.go.jp/JRADB/accessO.html`: HTTPS, `www.jra.go.jp`, no port, credentials, query, fragment, whitespace, or controls. It is not caller-configurable to another endpoint. The sole form-field name is the fixed lower-case literal `cname`; it is not a field on the locator because no alternative field is accepted.

`cname` is the raw canonical provider value, never a URL-escaped or form-escaped spelling. Its sole accepted grammar is:

```text
pw151ou10<VV><YYYY><MM><DD><RR><YYYYMMDD>Z/<HH>
```

`VV` is `01` through `10`; `YYYY` is four ASCII digits; `MM` uses the existing JRA meeting grammar `01`–`09` or `10`–`99`; `DD` and `RR` use the existing `01`–`12` meeting-day/race-number grammar; the embedded calendar date is real and has the same year as `YYYY`; `Z` is literal; and `<HH>` is exactly two uppercase ASCII hexadecimal characters. The slash is literal and exactly once. The opaque tail is retained but never becomes race identity.

Reject non-exact strings, whitespace/control characters, empty values, lower-case hex, invalid calendar dates, unsupported prefixes/selectors, alternate endpoints, plus encoding, percent encoding (including `%2F` and `%252F`), duplicate or extra form fields, and all CNAME derivation from `JRAExternalRaceIdentity`. The locator is constructed only from supplied official accessS navigation/form material that has already provided this CNAME. It derives `external_race_identity` from the five native tokens and verifies the supplied identity is exactly that derived value; it does not accept an independently contradictory race identity.

## Request Fingerprint

`request_identity_sha256` is provider-owned and is required to equal the lowercase SHA-256 hexadecimal digest of exactly these UTF-8 bytes:

```python
json.dumps(
    {
        "endpoint_url": "https://www.jra.go.jp/JRADB/accessO.html",
        "form": {"cname": "<canonical raw cname>"},
        "method": "POST",
        "schema_version": 1,
    },
    sort_keys=True,
    separators=(",", ":"),
    ensure_ascii=True,
).encode("utf-8")
```

The literal object keys, values, sort order, separators, ASCII rendering, and absence of a trailing newline are the complete preimage grammar. The raw form CNAME contains its literal slash in this JSON material; it is form-encoded only on the HTTP wire. Cookies, request headers, transient transport state, body timestamps, capture timestamps, and observation timestamps are excluded. This fingerprint distinguishes POST form identities at the shared endpoint and is independent of `observed_at`.

The locator’s fingerprint is copied unchanged into the future `HistoricalInputEvidenceReference.request_identity_sha256`. Its final-odds evidence has exactly:

```text
evidence_role:              historical_race_final_odds
canonical_source_url:       https://www.jra.go.jp/JRADB/accessO.html
request_identity_sha256:    locator fingerprint
response_sha256:            SHA-256 of exact supplied CP932 response bytes
available_at:               None
observed_at:                actual capture observation
```

The returned odds page’s directly visible race identity must be parsed and cross-checked against `locator.external_race_identity`; disagreement is validation failure. A current capture is not proof of historical causal eligibility. The existing builder alone later enforces `observed_at <= captured_at <= information_cutoff`.

## Page and Supplied-Response Model

Add exactly `JRAOfficialPageKind.FINAL_WIN_ODDS = "final_win_odds"`. Existing `RACE_RESULT` and `HORSE_PROFILE_HISTORY` values are unchanged.

Keep `JRASuppliedOfficialResponse` byte-for-byte constructor-compatible for accessS/accessU GET evidence. Add a separate immutable `JRAFinalWinOddsSuppliedOfficialResponse`, carrying exactly the validated `request_locator`, exact CP932 `response_body`, fixed `charset="cp932"`, and actual aware `observed_at`. Its canonical source URL is the locator endpoint and its request identity is the locator fingerprint. It must not pretend that the POST response is represented by a fabricated GET CNAME URL.

## Capture Domain v002

Keep `JRAOfficialResponseCapture` and every v001 GET capture’s public construction, fields, schema version, `jra-capture-v1:<sha256>` material, and capture IDs unchanged. Add a separate immutable final-odds capture value rather than changing legacy constructor semantics. Its fields are the existing raw response/HTTP/timestamp fields plus the validated `request_locator`; it has:

```text
schema_version: 2
page_kind:      FINAL_WIN_ODDS
request_method: POST
capture_id:     jra-capture-v2:<sha256>
```

Its exact capture-ID preimage is canonical UTF-8 JSON with `sort_keys=True`, `separators=(",", ":")`, and `ensure_ascii=False` over:

```text
{
  "canonical_source_url": "https://www.jra.go.jp/JRADB/accessO.html",
  "observed_at_utc": <UTC microsecond ISO-8601 text>,
  "page_kind": "final_win_odds",
  "request_identity_sha256": <locator SHA-256>,
  "request_method": "POST",
  "response_sha256": <raw response SHA-256>,
  "schema_version": 2
}
```

The digest is prefixed `jra-capture-v2:`. The locator CNAME itself is stored separately in the dedicated archive as raw provider-specific request material and is verified against the stored request fingerprint during reconstruction; it need not be duplicated in the ID preimage because the fingerprint is its canonical complete request identity. `observed_at` remains part of both v001 and v002 capture identity.

## Dedicated Archive Migration v002

Add dedicated migration module `jra_official_response_capture_migration_v002.py` with exactly:

```text
VERSION = 2
NAME = v002_jra_official_response_capture_request_identity_schema
```

Register it after v001 only in `JRA_CAPTURE_MIGRATIONS`. Global migrations remain exactly `(8, 9, 10, 11, 12, 13, 14)`.

v001 cannot be safely altered in place: its `schema_version=1` and two-value `page_kind` CHECK constraints exclude final odds. v002 therefore performs one deterministic transaction-owned rebuild of only `jra_official_response_captures`:

1. Require the exact registered v001 archive shape and validate every v001 capture through the legacy capture domain before schema mutation; malformed, duplicate, missing-body, or unregistered state fails closed.
2. Rename the v001 capture table to a temporary v001 name, drop only its old evidence index, and create the v002 capture table `WITHOUT ROWID` with all v001 columns plus `request_method TEXT NOT NULL`, `request_identity_sha256 TEXT NULL`, and `request_cname TEXT NULL`.
3. Enforce exact row families: v001 permits only legacy GET page kinds, `request_method='GET'`, and NULL request fingerprint/CNAME; v002 permits only `final_win_odds`, `request_method='POST'`, lowercase 64-hex request fingerprint, and nonempty raw CNAME. Other combinations are rejected. Retain all existing raw-body FK, CP932, HTTP, content, timestamp, and immutable identity checks.
4. Copy every v001 capture column byte-for-byte, adding only `GET`, NULL, NULL. Do not change capture IDs, timestamps, response bodies, digest rows, or body de-duplication.
5. Create two exact partial unique evidence indexes: legacy `(canonical_source_url,response_sha256,observed_at_utc)` for rows with NULL request fingerprint; request-aware `(canonical_source_url,request_identity_sha256,response_sha256,observed_at_utc)` for rows with non-NULL request fingerprint. Drop the renamed temporary table only after successful copy and index creation.

The migration runner’s encompassing `BEGIN IMMEDIATE` transaction registers v002 only after `apply` succeeds. A failure leaves v001 tables, index, registry row set, and data intact; no adoption, repair, update, delete, prune, or fallback is allowed. `jra_official_response_bodies` is never rebuilt.

The repository must reconstruct either exact capture family, verify v002 locator/CNAME/fingerprint coherence, preserve append-only/idempotent semantics, and fail closed on corrupt stored request material. Legacy `load_supplied_response_for_evidence(canonical_source_url, response_sha256, observed_at)` remains exactly URL+raw-SHA+observation lookup and returns only a legacy GET supplied response. Add a separate exact final-odds lookup taking canonical endpoint URL, request fingerprint, raw response SHA, and observation time, returning only `JRAFinalWinOddsSuppliedOfficialResponse`. There is no nearest/latest lookup and no URL-only POST fallback.

## Future Live POST API

Preserve `JRAOfficialLiveResponseCaptureService.capture_response(*, page_kind, response_url)` exactly for GET accessS/accessU. Add only:

```python
capture_final_win_odds_response(
    *, request_locator: JRAOfficialFinalWinOddsRequestLocator,
) -> JRAFinalWinOddsSuppliedOfficialResponse
```

It validates the locator before any clock, transport, or archive interaction. It POSTs only the canonical endpoint and exactly the one form field `cname=<canonical raw locator CNAME>` using standard form encoding; the captured effective endpoint must remain exactly the locator endpoint. Its sequence is: validate locator, obtain `requested_at`, fetch one complete raw body, obtain `observed_at`, obtain `stored_at`, construct v002 capture, archive it, then return the supplied response. Archive failure propagates and nothing is returned. No live transport or timing code is in d1d4b1.

## Frozen Scope and Compatibility

```text
EXISTING_ACCESS_S_CAPTURE_IDS_PRESERVED = YES
EXISTING_ACCESS_U_CAPTURE_IDS_PRESERVED = YES
EXISTING_GET_LIVE_API_PRESERVED = YES
GLOBAL_MIGRATION_FINAL_VERSION = 14
NAR_CAPTURE_UNCHANGED = YES
NEUTRAL_REQUEST_EVIDENCE_UNCHANGED = YES
JRA_FINAL_ODDS_CAPTURE_READY_FOR_IMPLEMENTATION = YES
```

No JRA historical result/final-odds normalizer, accessO live capture, NAR/JRA bridge, history discovery, pagination, pacing, historical backdating, capture execution, or package-root export is in this phase.

## Recommended Implementation Split

`4C-2d3b1i6d1d4b1 — JRA final-odds request/capture domain and dedicated archive v002` should implement the locator, final-odds supplied/capture domains, FINAL_WIN_ODDS page kind, v002 migration/runner registration, repository reconstruction and exact lookup, and dedicated regression tests. It must not modify live HTTP transport.

Its exact allowed files are:

```text
scripts/simulation/jra_official_identity.py
scripts/simulation/jra_official_response_capture.py
scripts/simulation/jra_official_response_capture_migration_runner.py
scripts/simulation/jra_official_response_capture_migration_v002.py
scripts/simulation/repositories/sqlite_jra_official_response_capture_repository.py
tests/test_jra_official_identity.py
tests/test_jra_official_response_capture.py
tests/test_jra_official_response_capture_migration.py
tests/test_sqlite_jra_official_response_capture_repository.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

`4C-2d3b1i6d1d4b2 — JRA final-odds live POST transport` can then alter only the live-capture module and its dedicated tests plus phase documents. It must consume the approved b1 public values and leave all archive/domain behavior unchanged.

## Allowed Files

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Stop Condition

Stop for independent design review. Do not implement d1d4b1 or d1d4b2, capture an official response, create a migration, modify an archive, perform HTTP, or start a JRA normalizer or bridge.
