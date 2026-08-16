# Current Phase

## Status

READY_FOR_REVIEW

## Phase

`4C-2d3b1i6d1d5f1c` — JRA accessD capture v003 preparation.

Formal base: `776cd9123635eef3759284ff997a369857f3769e`.

Structural evidence reference read only: `6515e61bbdc256eeaa721f67bc34c6b36eaf3be4`.

Review branch: `review/4c-2d3b1i6d1d5f1c-jra-accessd-capture-v003-prepare`.

## Allowed Files

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

Design only: production, tests, capture, archive, migration, schema, and live HTTPS
work are forbidden.

## Identity and Supplied Response

Add this exact public API in `jra_official_identity.py`:

```python
parse_jra_race_card_url_identity(value: str) -> JRAExternalRaceIdentity
```

It raises only existing `JRAOfficialIdentityValidationError`. It accepts exactly
`https://www.jra.go.jp/JRADB/accessD.html` with one uppercase `CNAME` query key and
the canonical raw `%2F` delimiter. Its one-token CNAME grammar is:

```text
pw01dde(?P<site>01|10)(?P<venue>0[1-9]|10)(?P<year>[0-9]{4})(?P<meeting>0[1-9]|[1-9][0-9])(?P<day>0[1-9]|1[0-2])(?P<race>0[1-9]|1[0-2])(?P<date>[0-9]{8})/(?P<tail>[0-9A-F]{2})
```

`date` is real and shares `year`; `site`/`tail` are opaque. The result is only
`JRAExternalRaceIdentity(year, venue, meeting, day, race)`. Invalid host, path,
query, case, delimiter, CNAME, or date fails closed. Display identity never falls
back to text.

Add `JRAOfficialPageKind.TARGET_RACE_CARD = "target_race_card"`, but freeze two
different URL-recognition boundaries:

```text
V1_CAPTURE_URL_FAMILY = RACE_RESULT, HORSE_PROFILE_HISTORY
V3_CAPTURE_URL_FAMILY = TARGET_RACE_CARD
```

`canonicalize_jra_official_capture_url(...)` remains the v1-only canonicalizer and
continues to reject `TARGET_RACE_CARD`. It must not be widened. Add a separate
internal supplied-response URL recognizer that accepts canonical accessS, accessU,
and accessD URLs. Only that broader recognizer permits the existing immutable
`JRASuppliedOfficialResponse` to accept accessD evidence. It remains strict CP932
exact bytes with actual aware `observed_at`; no second supplied-response type is
added. Existing accessS/accessU and POST final-odds semantics remain unchanged.

## v003 Capture Domain and ID

Add frozen/slotted `JRAOfficialTargetRaceCardResponseCapture` with exactly:

```text
canonical_source_url, response_body, charset, requested_at, observed_at, stored_at,
http_status, content_type, content_encoding, http_date, etag, last_modified,
content_length, schema_version=3, page_kind=TARGET_RACE_CARD, request_method="GET",
response_sha256, capture_id
```

It uses its own exact accessD canonicalization based on
`parse_jra_race_card_url_identity(...)`; it must not use the v1 canonicalizer. It
then reuses v1 field validation: exact canonical accessD URL; nonempty strict CP932 body;
charset `cp932`; HTTP 200; existing accepted HTML content type; absent/identity
encoding only; existing header checks; exact optional Content-Length; aware UTC
timestamps with `requested_at <= observed_at <= stored_at`; and SHA-256 of raw bytes.
It exposes only `to_supplied_official_response() -> JRASuppliedOfficialResponse`.

The capture ID is exactly:

```text
jra-capture-v3:SHA256(UTF-8 canonical JSON, sort_keys=True, separators=(',', ':'), ensure_ascii=False, {
  canonical_source_url, observed_at_utc, page_kind: "target_race_card",
  response_sha256, schema_version: 3
})
```

`request_method` is intentionally excluded: schema/version and page kind fix GET,
matching v1. v2 retains its current request-aware POST material unchanged. All v1/v2
capture IDs remain byte-for-byte immutable.

## Archive API

Add only these three family-specific methods to `JRAOfficialResponseCaptureArchive`:

```python
save_target_race_card_capture(*, capture: JRAOfficialTargetRaceCardResponseCapture) -> None
load_target_race_card_capture(*, capture_id: str) -> JRAOfficialTargetRaceCardResponseCapture | None
load_target_race_card_supplied_response_for_evidence(*, canonical_source_url: str, response_sha256: str, observed_at: datetime) -> JRASuppliedOfficialResponse
```

The evidence key is exact canonical accessD URL, lowercase 64-hex raw-body SHA, and
exact aware observed instant. It reads only v003 target-card GET rows, never falls
back, raises existing capture-missing error if absent, and raises
`RepositoryDataIntegrityError` for duplicate/corrupt family data. Existing APIs stay
concrete: no union widening.

Repository saves remain concrete and family-specific: `save_capture` is v1 only,
`save_final_win_odds_capture` is v2 only, and `save_target_race_card_capture` is v3
only. Each ID loader accepts only its own prefix. Valid foreign-family IDs return
`None`: v1/v2 for v3, v3 for v1/v2. Malformed IDs remain validation errors.
Requested-family prefix/schema/page-kind/method/request-column/body/domain
disagreement is `RepositoryDataIntegrityError`, not `None`.

## v003 Migration

Freeze `jra_official_response_capture_migration_v003.py`:

```text
VERSION = 3
NAME = v003_jra_official_response_capture_target_race_card_schema
JRA_CAPTURE_MIGRATIONS = (v001, v002, v003)
```

The runner alone owns `BEGIN IMMEDIATE`, commit, and rollback; `apply()` remains
transaction-neutral. Upgrade is sequential `1 -> 2 -> 3`.

v003 validates exact approved v002 body/capture tables, 19 capture columns, both
partial unique evidence indexes, FKs/checks, and every v1/v2 reconstruction/ID
before mutation. A malformed v002 state fails before mutation. The response body
table is reused unchanged and is never rebuilt.

SQLite cannot add the required v003 alternatives to v002 CHECK constraints in place;
therefore only the capture table is transactionally rebuilt. It retains all 19
columns, adds schema version 3/page kind target_race_card, and adds the v3 closed
family condition: GET with NULL request identity and request cname. All 19 v1/v2
stored columns copy exactly. Recreate the existing NULL-request-identity and
non-NULL-request-identity partial unique indexes; no third index is needed. On
failure, rollback restores exact v002 tables/indexes/data/registry; v1/v2 body bytes
and IDs are never altered.

## Live GET Compatibility and Readiness

The existing private GET transport is reusable unchanged after the dedicated v3
accessD canonical path authorizes its input: GET, TLS verification, redirects
disabled, 200 only, zero retries, 10/10 timeout, identity encoding,
compressed-response rejection, exact optional Content-Length, 4 MiB body limit, raw
undecoded stream/body SHA, and close paths.

The existing public `capture_response(...)` remains v1-only: it accepts only the
v1 capture URL family and rejects `TARGET_RACE_CARD` before clock, transport, or
archive work. It must not call the broader supplied-response URL recognizer. A later
live phase needs a separate
`capture_target_race_card_response(*, response_url: str) -> JRAOfficialTargetRaceCardResponseCapture`:
v3-accessD-canonicalize -> clock -> existing GET fetch -> clock -> v3 capture ->
`save_target_race_card_capture` -> return. The current GET API/call shape cannot
change.

From the referenced structural investigation only:

```text
ACCESSD_TO_ACCESSU_IDENTITY_STATUS = PROVEN
ACCESSD_SELECTORS_READY = YES
TARGET_ODDS_SOURCE_READY = YES
SINGLE_RESPONSE_COMPLETE_TRACK_SOURCE = PROVEN
TRACK_SOURCE_SCHEMA_CHANGE_REQUIRED = NO
```

Non-runner shapes remain unsupported. Target selectors are out of scope.

```text
ACCESSD_IDENTITY_IMPLEMENTATION_READY: YES
ACCESSD_SUPPLIED_RESPONSE_EXTENSION_READY: YES
ACCESSD_CAPTURE_DOMAIN_READY: YES
ACCESSD_CAPTURE_IDENTITY_READY: YES
ACCESSD_ARCHIVE_API_READY: YES
ACCESSD_MIGRATION_V003_READY: YES
ACCESSD_LIVE_GET_EXTENSION_READY: YES
ACCESSD_CAPTURE_IMPLEMENTATION_READY: YES — dedicated v003 phase only
TARGET_SOURCE_IMPLEMENTATION_READY: NO — formal accessD capture is not implemented
```

Next phase: narrow v003 identity/domain/archive/repository/migration implementation
with tests/docs. It must not include target normalization, snapshots, or live accessD
acquisition. Required regression tests prove: supplied accessD acceptance; v1 capture
accessD rejection; v1 live API rejection before transport/archive; v3 capture accessD
acceptance; dedicated v3 live save only; and unchanged v1 accessS/accessU plus v2
accessO IDs and behavior. Stop after the docs-only review commit is pushed.
