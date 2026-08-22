# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase

`4C-2d3b1i6d1d5f1c4c0b3` — JRA live target-navigation composition PREPARE.

Formal base: `b506973ac7718126c24795af2d457b721453cc90`.

Review branch:
`review/4c-2d3b1i6d1d5f1c4c0b3-jra-live-target-navigation-prepare`.

This phase freezes architecture only. It adds no production code, test, schema,
migration, trusted capture, or formal-branch change.

## Ownership and Public Boundary

Live composition remains in `jra_official_response_live_capture.py`. The existing
`JRAOfficialLiveResponseCaptureService` already exclusively owns the injected JRA HTTPS
transport, UTC clock, archive-before-return behavior, and production builder. Adding one
narrow method there avoids a second HTTP stack and avoids a new module whose only way to
reuse the existing transport would be to depend on its private implementation.

The frozen API is:

```python
def capture_target_race_navigation(
    self,
    *,
    external_race_id: str,
) -> JRATargetRaceNavigationCaptureResult: ...
```

`JRATargetRaceNavigationCaptureResult` is frozen/slotted and retains exactly:

```python
discovery: JRATargetRaceCardDiscovery
target_race_selection_capture_id: str
```

It retains no HTTP object or response bytes. Its custom exact constructor accepts the
exact discovery and exact `JRATargetRaceSelectionResponseCapture`, checks that capture
request locator, response SHA-256, and observed instant equal the discovery provenance,
then stores only the capture ID. This prevents direct public construction with an
unrelated syntactically valid v4 ID while avoiding retained/duplicated raw bytes. The
service invokes that constructor only after the exact capture has saved successfully.
No package-root export is added.

The caller supplies only canonical `external_race_id`. At the absolute service boundary,
before any clock sample, transport call, root GET, POST, or archive interaction, the
method validates that value with the existing formal JRA external-race-ID parser. It
does not normalize malformed input or introduce another parser. The validated original
canonical string is then passed unchanged to the formal discoveries; parsed race fields
are never used to construct navigation locators. Invalid or noncanonical input therefore
causes zero clock, transport, and archive calls.

The composition never derives a CNAME, opaque tail, site variant, URL, meeting, or date
from the target ID. Each locator is produced only by the immediately preceding formal
supplied response.

## Transport Contract

One existing `_RequestsJRAOfficialHTTPTransport` instance remains the sole requests
stack. It gains typed private root, meeting-selection, and race-selection methods. The
two locator types remain distinct at their typed transport entry points; those wrappers
share one private form-POST/send/read validation primitive.

The root request is fixed, query-free `GET https://www.jra.go.jp/`. A dedicated private
root entry point reuses the existing TLS-verified, zero-retry, 10/10-second timeout,
disabled-redirect, effective-URL, raw-stream, identity-encoding, canonical
Content-Length, and 4 MiB response checks. It prepares a cookie-free request rather than
calling the session's cookie-merging convenience GET. The response must be HTTP 200,
exact effective root URL, accepted `text/html` with no unsupported parameters, absent or
identity Content-Encoding, complete exact bytes, and strict CP932 when the formal root
supplied domain is built.

Both selection requests are exact POSTs to the locator endpoint with one lower-case
standard form field:

```text
cname=<exact locator cname>
Content-Type: application/x-www-form-urlencoded
Accept-Encoding: identity
User-Agent: existing frozen JRA live User-Agent
```

Requests owns the form encoding and exact Content-Length; the raw `/` therefore becomes
standard `%2F` request-body material without changing the locator's retained raw CNAME.
Cookie, Referer, and Origin are deliberately absent as an audit invariant. The formal
meeting/race request identities bind only their approved explicit endpoint, method, and
one-field form material; hidden session-derived request state is not part of those
identities and must not silently change the HTTP request they denote. Redirects remain disabled; TLS
verification, zero retries, 10/10-second timeouts, exact endpoint/effective-URL equality,
200-only status, absent/identity encoding, Content-Length agreement, 4 MiB maximum, and
complete raw bytes match the existing transport. Operational root and meeting responses
also require the established accepted HTML Content-Type grammar before supplied-domain
construction. The v4 capture domain performs the same check for race selection.

The requests Session may be reused only for adapter/connection pooling. Navigation
requests are prepared without merging its cookie jar, including when that jar is already
seeded. Set-Cookie on root or meeting responses may be ignored operational state, but it
must never change the next formal navigation request and is not a failure merely by being
present. There is no logical session continuity. If JRA later requires cookie/session
state, the live boundary fails closed; enabling it requires a new architecture review of
formal request identity and replay evidence.

### Narrow read-only observation

A transient memory-only official observation from
`2026-08-22T08:20:17.926952Z` through `2026-08-22T08:20:18.936977Z` resolved the only
remaining compatibility question for the observed site state. The root returned 200
`text/html`, no Content-Encoding, no Set-Cookie, and no session cookie. For both response-derived selection locators, an
exact cookie-/Referer-/Origin-free form POST returned 200 `text/html`, no
Content-Encoding, and bytes identical in length and SHA-256 to the same POST through the
root-used Session. This is bounded supporting evidence only, not proof that future JRA
behavior can never require cookies. The durable cookie-free rule comes from the formal
request-identity audit boundary. No response bytes were saved, archived, or committed;
this was not a trusted capture.

## Causal Clock and Composition Order

The existing injected `utc_clock` is the only clock owner. Every sample must be an exact
aware datetime; domain construction normalizes/compares under the existing rules.

```text
validate external_race_id with the formal parser
-> invalid/noncanonical means zero clock, transport, or archive calls

complete root GET and validate transport result
-> sample root observed_at
-> construct strict-CP932 root supplied response
-> discover meeting-selection request locator

complete meeting-selection POST and validate transport result
-> sample meeting observed_at
-> construct strict-CP932 meeting supplied response
-> discover race-selection request locator

sample race-selection requested_at immediately before transport call
-> send exact race-selection POST and receive complete validated entity
-> sample race-selection observed_at
-> construct/validate strict-CP932 race-selection supplied response
-> sample stored_at immediately before capture construction
-> construct exact schema-v4 capture
-> save_target_race_selection_capture(...)
-> derive supplied evidence from the saved immutable capture object
-> discover exact target-card locator
-> return result containing discovery plus v4 capture ID
```

The v4 domain enforces `requested_at <= observed_at <= stored_at`. No timestamp is
backdated, copied from a later event, or exposed as invented `available_at`.

Archive save must succeed before discovery or a success result is exposed. Archive
exceptions propagate unchanged. Discovery uses `capture.to_supplied_official_response()`
only after save succeeds. Reload after save is not required: this matches existing
append-only capture service behavior, avoids an unnecessary database round trip, and the
immutable capture object is the exact object accepted by the archive. Exact evidence
reload remains available later for replay/audit. If post-save discovery fails, no API
success is returned; the already-retained append-only observation is not deleted or
misrepresented as a locator.

## Target-card Boundary Decision

C0b3 stops after durable race-selection evidence and the exact target-card locator. It
does not call `capture_target_race_card_response(...)`. Schema-v3 target-card GET
acquisition is already a complete independent live-capture responsibility. Returning its
exact input locator enables a later caller to invoke that existing method without a
second implementation, while keeping navigation failure and card-acquisition failure
separate and reviewable. C0b3 adds no target-card GET or second success contract.

## Failure and Persistence Policy

Malformed/noncanonical `external_race_id` fails through the formal identity validation
boundary before every collaborator. Root, meeting POST, race-selection POST, HTTP status/effective URL/redirect,
Content-Length, compression, size, CP932, formal supplied-domain, discovery, clock,
capture-domain, and archive failures all propagate through their existing narrow error
families and produce no result. There is no broad catch, automatic retry, stale/current
fallback, guessed locator, partial success result, or live target-card fallback. A
cookie-free request failure is never retried with Cookie, Referer, Origin, or other hidden
session state.

Persistence remains:

```text
root menu response: operational only; not persisted
meeting-selection response: operational only; not persisted
race-selection response: schema-v4 archive; required before success
target race card: existing schema-v3 capture owner; not invoked by c0b3
```

No schema, migration v005, table, index, repository API, pure discovery domain, target
normalizer, replay resolver, source union, entry mapping, or snapshot contract changes.

## Future Implementation Files

```text
scripts/simulation/jra_official_response_live_capture.py
tests/test_jra_official_response_live_capture.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

No new production module is required. Existing locator/discovery, capture, repository,
and migration files remain unchanged.

## Required Implementation Tests

Offline synthetic fake-transport/clock/archive tests must pin the exact public method and
result; malformed/noncanonical target IDs must fail before any clock, transport, or
archive call. Tests must also pin the fixed cookie-free root GET, response-derived
locators only, exact typed form POSTs, and a pre-seeded Session cookie jar that cannot add
a Cookie header. Synthetic Set-Cookie on root must not affect the meeting request, and
Set-Cookie on meeting must not affect race selection; Referer and Origin remain absent,
with no cookie-enabled fallback after failure. Tests also pin complete-entity clock order, v4 metadata and save
before discovery/return, archive and post-save discovery failure behavior, exact
capture-bound discovery source, site/tail preservation, target unavailable/ambiguity,
transport/domain/CP932/HTML failures at every stage, no hard-coded CNAME or identity URL
synthesis, no retry/fallback, and no real network. Existing final-odds and target-card
live behavior must remain unchanged; static checks must prove no schema/migration,
package-root export, or new transport stack. Dedicated, related, and full pytest suites
remain required in implementation.

## Readiness Matrix

```text
LIVE_COMPOSITION_OWNER: JRAOfficialLiveResponseCaptureService_IN_jra_official_response_live_capture.py
NEW_MODULE_REQUIRED: NO
OWNERSHIP_REASON: existing sole JRA HTTPS/clock/archive owner can compose the formal stages without a second transport stack

LIVE_NAVIGATION_API_READY: YES
LIVE_NAVIGATION_API_SIGNATURE: JRAOfficialLiveResponseCaptureService.capture_target_race_navigation(*, external_race_id: str) -> JRATargetRaceNavigationCaptureResult
LIVE_NAVIGATION_RESULT_DOMAIN: frozen/slotted custom-exact-construction JRATargetRaceNavigationCaptureResult retaining discovery + target_race_selection_capture_id and validating lineage from the exact v4 capture
EXTERNAL_RACE_ID_VALIDATION_ORDER: BEFORE_ANY_CLOCK_HTTP_OR_ARCHIVE
INVALID_ID_ZERO_SIDE_EFFECTS: YES_ZERO_CLOCK_ZERO_TRANSPORT_ZERO_ARCHIVE

ROOT_TRANSPORT_REUSE_SAFE: YES_VIA_DEDICATED_COOKIE_FREE_ROOT_ENTRY_AND_EXISTING_PRIVATE_VALIDATION_READ_CORE
ROOT_RESPONSE_ARCHIVED: NO
ROOT_OBSERVED_AT_SEMANTICS: ACTUAL_CLOCK_SAMPLE_AFTER_COMPLETE_VALIDATED_ENTITY_RECEIPT

MEETING_POST_REQUEST_SEMANTICS_READY: YES
MEETING_POST_COOKIE_POLICY: DELIBERATELY_ABSENT_AS_AUDIT_INVARIANT
MEETING_POST_REFERER_POLICY: DELIBERATELY_ABSENT_AS_AUDIT_INVARIANT
MEETING_POST_ORIGIN_POLICY: DELIBERATELY_ABSENT_AS_AUDIT_INVARIANT
MEETING_POST_SESSION_POLICY: NO_LOGICAL_SESSION_CONTINUITY; CONNECTION_POOL_ONLY

RACE_SELECTION_POST_REQUEST_SEMANTICS_READY: YES_IDENTICAL_HTTP_POLICY_WITH_EXACT_RACE_LOCATOR
RACE_SELECTION_POST_HIDDEN_STATE_POLICY: SAME_DELIBERATELY_ABSENT_AUDIT_INVARIANT_AS_MEETING_POST
POST_TRANSPORT_PRIMITIVE_SHARED: YES_PRIVATE_ONLY
POST_FORMAL_TYPES_REMAIN_DISTINCT: YES

CLOCK_OWNER: EXISTING_INJECTED_JRA_LIVE_SERVICE_UTC_CLOCK
ROOT_OBSERVED_AT_ORDER: AFTER_COMPLETE_ROOT_ENTITY_AND_TRANSPORT_VALIDATION
MEETING_OBSERVED_AT_ORDER: AFTER_COMPLETE_MEETING_ENTITY_AND_TRANSPORT_VALIDATION
RACE_SELECTION_REQUESTED_AT_ORDER: IMMEDIATELY_BEFORE_RACE_SELECTION_TRANSPORT_CALL
RACE_SELECTION_OBSERVED_AT_ORDER: AFTER_COMPLETE_RACE_SELECTION_ENTITY_AND_TRANSPORT_VALIDATION
RACE_SELECTION_STORED_AT_ORDER: AFTER_SUPPLIED_RESPONSE_VALIDATION_AND_IMMEDIATELY_BEFORE_V4_CAPTURE_CONSTRUCTION

ARCHIVE_BEFORE_SUCCESS_RETURN: YES
ARCHIVE_FAILURE_FAILS_CLOSED: YES_NO_DISCOVERY_OR_RESULT
DISCOVERY_USES_ARCHIVED_OR_CAPTURE_BOUND_BYTES: YES_IMMUTABLE_SAVED_CAPTURE_BOUND_BYTES

POST_ARCHIVE_DISCOVERY_SOURCE: capture.to_supplied_official_response_AFTER_SUCCESSFUL_SAVE
RELOAD_AFTER_SAVE_REQUIRED: NO
RELOAD_REASON: immutable accepted capture is exact evidence; existing service precedent and no added audit value from immediate round trip

C0B3_STOPS_AT_LOCATOR: YES
C0B3_INVOKES_EXISTING_TARGET_CARD_CAPTURE: NO
DECISION_REASON: navigation owns durable locator proof; existing schema-v3 method separately owns the exact card GET

SESSION_CONTINUITY_REQUIRED: NO_LOGICAL_SESSION_CONTINUITY
NAVIGATION_HIDDEN_REQUEST_STATE_ALLOWED: NO
COOKIE_STATE_ALLOWED: NO_IN_NAVIGATION_REQUESTS
COOKIE_STATE_ALLOWED_IN_OUTGOING_NAVIGATION_REQUESTS: NO
COOKIE_JAR_MAY_AFFECT_NAVIGATION_REQUEST: NO
SET_COOKIE_MAY_CHANGE_NEXT_NAVIGATION_REQUEST: NO
FUTURE_COOKIE_REQUIREMENT_POLICY: FAIL_CLOSED_AND_REVIEW_IDENTITY_CONTRACT
COOKIE_STATE_REPLAY_EVIDENCE_REQUIRED: NO
COOKIE_CAUSALITY_REASON: formal request identities exclude hidden session-derived state, so outgoing navigation must exclude it; the 2026-08-22 observation is supporting compatibility evidence only

PARTIAL_SUCCESS_ALLOWED: NO
LIVE_FALLBACK_ALLOWED: NO
AUTOMATIC_RETRY_ADDED: NO

ROOT_PERSISTENCE: NO_OPERATIONAL_ONLY
MEETING_SELECTION_PERSISTENCE: NO_OPERATIONAL_ONLY
RACE_SELECTION_PERSISTENCE: YES_SCHEMA_V4_BEFORE_SUCCESS
TARGET_CARD_PERSISTENCE_OWNER: EXISTING_SCHEMA_V3_capture_target_race_card_response
SCHEMA_CHANGE_REQUIRED: NO

IMPLEMENTATION_FILES: jra_official_response_live_capture.py; CURRENT_PHASE.md; LATEST_CODEX_REPORT.md
IMPLEMENTATION_TEST_FILES: test_jra_official_response_live_capture.py

C0B3_IMPLEMENTATION_READY: YES
BLOCKERS: NONE

READ_ONLY_LIVE_OBSERVATION_REQUIRED: YES_ONLY_TO_CLOSE_COOKIE_SESSION_REFERER_ORIGIN_POLICY
READ_ONLY_LIVE_OBSERVATION_PERFORMED: YES_TRANSIENT_MEMORY_ONLY_2026-08-22
READ_ONLY_LIVE_OBSERVATION_REPEATED: NO
REAL_TRUSTED_CAPTURE_REQUIRED: NO
REAL_TRUSTED_CAPTURE_PERFORMED: NO
```

## Allowed Files

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Stop Condition

Stop after the two documentation files are committed and the review branch is pushed for
independent ChatGPT architecture review. Do not implement c0b3, start c4c, alter the
formal branch, or perform a real trusted capture.
