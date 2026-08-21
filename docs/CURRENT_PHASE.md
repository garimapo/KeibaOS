# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase

`4C-2d3b1i6d1d5f1c4c0a` — official JRA target accessD discovery/navigation.

Formal base: `06b7d6df7ea57fab04a9abe70d67c580963ea3d2`.

Approved c4c0 prepare: `9f15aee55ca2197b63731d88c590305f188466c1`.

Review branch: `review/4c-2d3b1i6d1d5f1c4c0a-jra-target-accessd-discovery-prepare`.

## Scope

This documentation-only PREPARE identifies the official accessD navigation source for an
exact target-card locator. It does not implement identity/domain/capture/archive/schema
changes, retain raw response bytes, perform a trusted capture, or modify the formal
branch.

## Read-only Official Observation

At `2026-08-21T12:24Z` a transient read-only official JRA observation established this
chain. It was not archived, persisted, or treated as historical evidence:

```text
POST https://www.jra.go.jp/JRADB/accessD.html
form cname=pw01dli00/F3
-> 出馬表 開催選択 response
-> direct doAction('/JRADB/accessD.html', 'pw01drl00.../<HH>')
-> POST https://www.jra.go.jp/JRADB/accessD.html
   form cname=<that exact pw01drl00.../<HH>>
-> 出馬表 レース選択 response
-> literal relative accessD target-card hrefs
```

The established `doAction` implementation writes its raw argument to hidden lower-case
`cname` in `form#commForm01` and submits that form. The official endpoint is therefore
POST, not a GET URL synthesized from a navigation CNAME. Responses were HTTP 200,
`text/html`, uncompressed under `Accept-Encoding: identity`, advertised
`<meta charset="Shift_JIS">`, and strictly CP932-decodable. No redirect was observed;
future trusted transport must keep the established disabled-redirect, HTTPS, identity
encoding, 200-only, raw-byte, timeout/size, and TLS policies rather than create a second
transport stack.

The first selection page is only the direct source of the next POST request material.
The formal locator source is the second response: one race-selection page for one exact
date/venue/meeting/day, containing all listed races for that scope. No pagination or
continuation control was observed in the selected race table; unknown continuation or
pagination material must fail closed.

## Frozen Official Source Contract

`TARGET_NAVIGATION_PAGE_KIND: TARGET_RACE_SELECTION`.

`TARGET_NAVIGATION_ENDPOINT: https://www.jra.go.jp/JRADB/accessD.html`.

`TARGET_NAVIGATION_REQUEST_METHOD: POST`.

The request identity is a new dedicated immutable
`JRATargetRaceSelectionRequestLocator`, not an accessD card URL and not the final-odds
locator. It contains the fixed endpoint, raw lower-case form `cname`, and SHA-256 of
canonical UTF-8 JSON exactly:

```json
{"endpoint_url":"https://www.jra.go.jp/JRADB/accessD.html","form":{"cname":"<raw-cname>"},"method":"POST","schema_version":1}
```

with sorted keys and compact separators, following the existing JRA POST fingerprint
convention. The observed race-selection CNAME grammar is exactly
`pw01drl00<VV><YYYY><MM><DD><YYYYMMDD>/<HH>`, where `VV`, `YYYY`, `MM`, and `DD`
are the existing canonical venue/year/meeting/day lexical fields; the embedded calendar
date must validate and agree with the year. Its opaque uppercase `<HH>` is accepted only
as supplied raw official request material. The preceding meeting-selection response is
the only approved live source of that raw request CNAME; it is never constructed from a
target race identity.

The target-race-selection request locator must expose its parsed direct navigation
identity (year, venue, meeting, meeting day, and calendar date). Every selected card URL
must agree with those four race-identity fields and its own validated CNAME calendar date
before its race number is compared to the requested external race identity. A visible
heading may be a redundant cross-check only; it is never an identity substitute.

`TARGET_NAVIGATION_CHARSET: CP932_STRICT`.

`TARGET_NAVIGATION_RESPONSE_SCOPE: ONE_OFFICIAL_DATE_VENUE_MEETING_DAY_RACE_SELECTION`.

The page must have exactly:

```text
#contentsBody > div.race_select > table#race_list.basic.mt20 > tbody > tr
```

For every row, require one `th.race_num > a[href]` and one
`td.syutsuba > a.btn-def.btn-sm.btn-narrow[href]`. Both must resolve against
`https://www.jra.go.jp`, be canonicalized only by the approved raw-delimiter-to-`%2F`
operation, parse as an accessD target-card URL, and agree exactly. The row is not
identified by visible race name or `nR`; its direct target URL is the sole race identity
source. The future public identity module must expose one accessD canonicalizer for this
official raw href; discovery must not duplicate the current private v3 canonicalization.

For a requested canonical `external_race_id`, parse every row's direct canonical accessD
URL with `parse_jra_race_card_url_identity(...)`. Select exactly one matching identity.
Zero matching rows is discovery-unavailable; a malformed row, duplicate row, mismatched
two-anchor URL, or two distinct matching URLs is validation failure. Duplicate same URL
is accepted only for the two required anchors in the same exact official row; it is not a
general first-match rule.

`ACCESSD_LOCATOR_PRESENT_DIRECTLY_IN_RESPONSE: YES`.

`ACCESSD_LOCATOR_EXTRACTION_KIND: DIRECT_HREF`.

`ACCESSD_LOCATOR_SELECTOR_READY: YES`.

The raw accessD href contains the opaque target-card tail literally. Current official
evidence shows it as a relative path with raw `/` in its CNAME delimiter; resolution and
canonical `%2F` rendering preserve that exact CNAME, never infer it. The target-card
site variant is likewise taken only from that direct href; no variant is normalized or
synthesized.

## Supplied Response, Discovery, and Evidence Domains

Existing `JRASuppliedOfficialResponse` is not reusable: it recognizes only canonical
accessS/accessU/accessD target-card GET URLs, whereas this source is an accessD POST with
request-specific raw CNAME. Freeze a dedicated strict-CP932 supplied response:

```python
@dataclass(frozen=True, slots=True)
class JRATargetRaceSelectionSuppliedOfficialResponse:
    request_locator: JRATargetRaceSelectionRequestLocator
    response_body: bytes
    charset: str  # exact "cp932"
    observed_at: datetime  # exact aware, normalized UTC
```

Its endpoint is derived from the request locator; its raw body is nonempty strict CP932.
It has no synthetic response URL and no clock ownership.

The pure public discovery surface is:

```python
class JRATargetRaceCardDiscoveryError(ValueError): ...
class JRATargetRaceCardDiscoveryValidationError(
    JRATargetRaceCardDiscoveryError
): ...
class JRATargetRaceCardDiscoveryUnavailableError(
    JRATargetRaceCardDiscoveryError
): ...

@dataclass(frozen=True, slots=True)
class JRATargetRaceCardDiscovery:
    locator: JRATargetRaceCardLocator
    navigation_request_locator: JRATargetRaceSelectionRequestLocator
    navigation_response_sha256: str
    navigation_observed_at: datetime

def discover_jra_target_race_card_locator(
    *,
    external_race_id: str,
    navigation_response: JRATargetRaceSelectionSuppliedOfficialResponse,
) -> JRATargetRaceCardDiscovery: ...
```

The result retains the exact locator plus request identity, raw-byte digest, and actual
source observation without duplicating body bytes or placing JRA URL material in neutral
source-record values. Its observation is exactly the point at which the navigation bytes
were fully observed; the locator itself remains timestamp-free. The pure discovery has no
HTTP, archive, database, filesystem, clock, or raw-card parsing. It must fail closed and
must not use broad exception handling.

`DISCOVERY_OBSERVED_AT_OWNER: TARGET_RACE_SELECTION_SUPPLIED_RESPONSE`.

`LOCATOR_OBSERVED_AT_REQUIRED: NO_ON_LEXICAL_LOCATOR; YES_ON_DISCOVERY_EVIDENCE`.

`LOCATOR_PROVENANCE_READY: YES`.

`DISCOVERY_RESULT_DOMAIN_READY: YES`.

`DISCOVERY_PUBLIC_API_READY: YES`.

## Persistence and Archive Decision

The exact selection response plus its request identity is sufficient durable replay
identity: a later replay supplies/reconstructs that exact navigation evidence, calls the
pure discovery, and obtains the locator without race-ID archive enumeration. Thus no
separate locator table is required. Replay must not select a navigation response by race
ID alone or use a current navigation page as a historical substitute.

The existing JRA capture archive is reusable only through a new dedicated POST navigation
capture family, not by widening v1/v2/v3. The future extension must add page kind
`TARGET_RACE_SELECTION`, a dedicated schema-v4 immutable response capture and archive
methods, its exact request locator/fingerprint, and migration support while preserving all
v1/v2/v3 IDs and behavior. It reuses the response-body table and existing trusted HTTP
transport mechanics; whether the capture table requires the established controlled
rebuild is the later v004 migration design detail. It must not add a generic POST union.

The capture archive, not a locator repository, is the persistence owner. The discovery
result's digest/request/observation fields bind an exact archived selection response. No
new locator table is authorized.

## Multiple Locators and Causality

One observed selection response had two designated same-row target-card anchors with the
same direct URL. No observed response had two different target URLs parsing to one race,
and repeated observations were not used to infer tail revision semantics.

`CAN_MULTIPLE_CANONICAL_ACCESSD_URLS_BIND_ONE_RACE_ID: NOT_PROVEN`.

`LOCATOR_UNIQUENESS_POLICY: EXACTLY_ONE_DISTINCT_MATCHING_URL_IN_ONE_SELECTION_RESPONSE`.

`LOCATOR_CONFLICT_POLICY: DISTINCT_MATCHING_URLS_FAIL_CLOSED; CROSS_OBSERVATION_REVISION_SEMANTICS_NOT_PROVEN`.

The navigation response has actual `observed_at`; future race-level orchestration must
require it no later than its explicit replay bound, which cannot exceed `captured_at`.
It never backdates navigation or target-card evidence and does not invent `available_at`.
The later accessD resolver uses the resulting locator to select latest archived target
card at or before the same effective causal bound. No live fallback is allowed.

## Readiness Matrix

```text
OFFICIAL_NAVIGATION_CHAIN_PROVEN: YES_TWO_STAGE_POST
TARGET_NAVIGATION_PAGE_KIND: TARGET_RACE_SELECTION
TARGET_NAVIGATION_ENDPOINT: https://www.jra.go.jp/JRADB/accessD.html
TARGET_NAVIGATION_REQUEST_METHOD: POST
TARGET_NAVIGATION_REQUEST_IDENTITY: DEDICATED_RAW_CNAME_POST_LOCATOR_WITH_CANONICAL_SHA256
TARGET_NAVIGATION_CHARSET: CP932_STRICT
TARGET_NAVIGATION_RESPONSE_SCOPE: ONE_OFFICIAL_DATE_VENUE_MEETING_DAY_RACE_SELECTION

ACCESSD_LOCATOR_PRESENT_DIRECTLY_IN_RESPONSE: YES
ACCESSD_LOCATOR_EXTRACTION_KIND: DIRECT_HREF
ACCESSD_LOCATOR_SELECTOR_READY: YES

TARGET_RACE_BINDING_READY: YES_BY_PARSED_DIRECT_ACCESSD_URL_IDENTITY
SITE_VARIANT_SOURCE_READY: YES_DIRECT_ACCESSD_HREF_ONLY
CAN_MULTIPLE_CANONICAL_ACCESSD_URLS_BIND_ONE_RACE_ID: NOT_PROVEN
LOCATOR_UNIQUENESS_POLICY: EXACTLY_ONE_DISTINCT_MATCHING_URL_IN_ONE_SELECTION_RESPONSE
LOCATOR_CONFLICT_POLICY: FAIL_CLOSED_FOR_DISTINCT_MATCHING_URLS; CROSS_OBSERVATION_SEMANTICS_NOT_PROVEN

NAVIGATION_SUPPLIED_RESPONSE_REUSABLE: NO
NEW_NAVIGATION_SUPPLIED_RESPONSE_DOMAIN_REQUIRED: YES

DISCOVERY_OBSERVED_AT_OWNER: TARGET_RACE_SELECTION_SUPPLIED_RESPONSE
LOCATOR_OBSERVED_AT_REQUIRED: NO_ON_LEXICAL_LOCATOR; YES_ON_DISCOVERY_EVIDENCE
LOCATOR_PROVENANCE_READY: YES
DISCOVERY_RESULT_DOMAIN_READY: YES
DISCOVERY_PUBLIC_API_READY: YES

LOCATOR_PERSISTENCE_REQUIRED: YES_AS_EXACT_NAVIGATION_EVIDENCE
LOCATOR_PERSISTENCE_OWNER: DEDICATED_TARGET_RACE_SELECTION_CAPTURE_FAMILY_IN_EXISTING_JRA_ARCHIVE
EXISTING_PERSISTENCE_DOMAIN_REUSABLE: YES_WITH_DEDICATED_CAPTURE_FAMILY_EXTENSION
NEW_SCHEMA_REQUIRED: YES_JRA_CAPTURE_SCHEMA_V004
NEW_TABLE_REQUIRED: NO

JRA_CAPTURE_ARCHIVE_EXTENSION_REQUIRED: YES
ARCHIVE_SCHEMA_CHANGE_REQUIRED: YES
ARCHIVE_NEW_PAGE_KIND_REQUIRED: YES_TARGET_RACE_SELECTION
ARCHIVE_REQUEST_IDENTITY_CHANGE_REQUIRED: YES_DEDICATED_POST_NAVIGATION_LOCATOR

LIVE_CAPTURE_API_CHANGE_REQUIRED: YES_FOR_DEDICATED_TARGET_RACE_SELECTION_POST_CAPTURE
LIVE_CAPTURE_LOCATOR_BINDING_READY: YES_AFTER_DISCOVERY_CAPTURE_CONTRACT_IMPLEMENTATION

TARGET_ACCESSD_LOCATOR_SOURCE_READY: NO_UNTIL_DISCOVERY_IMPLEMENTED
TARGET_ACCESSD_LOCATOR_RETENTION_READY: NO_UNTIL_V004_NAVIGATION_CAPTURE_IMPLEMENTED
EXACT_ACCESSD_LOCATOR_AVAILABLE_BEFORE_RESOLUTION: NO_UNTIL_EXACT_NAVIGATION_EVIDENCE_IS_RETAINED
C4C_IMPLEMENTATION_READY_AFTER_DISCOVERY_IMPLEMENTATION: YES

IMPLEMENTATION_READY: YES_FOR_TARGET_RACE_SELECTION_DISCOVERY_AND_CAPTURE_PREREQUISITE
BLOCKERS: implement dedicated navigation identity/supplied/capture/archive/migration/discovery boundary; separate external-entry/internal-entry mapping remains later
REAL_TRUSTED_CAPTURE_REQUIRED: NO
REAL_TRUSTED_CAPTURE_MISSING_FACT: NONE
```

## Future Tests

The next implementation must use synthetic strict-CP932 selection HTML only and test the
exact public API/signatures; POST request fingerprint and grammar; canonical source
endpoint; direct current-row hrefs; resolved-relative raw-slash-to-canonical-`%2F`
conversion; parsed identity-only selection; missing, malformed, other-family, duplicate,
and distinct-conflicting href rejection; no target unavailable; source digest and observed
time; no tail/site-variant synthesis; no display-name binding; pure dependency surface;
and no package export/real capture. Capture tests must pin v1/v2/v3 immutability, v4
family-only archive/load/corruption behavior, request identity, migration preservation,
and exact evidence replay. Causal tests must reject navigation evidence after the future
explicit replay bound without a live/current fallback.

## Next Phase

Recommend `4C-2d3b1i6d1d5f1c4c0b — JRA target race-selection discovery and capture
v004 IMPLEMENTATION`, limited to the locator/request/supplied/discovery domains,
dedicated v4 capture/archive/migration/live POST boundary, and tests. It must not
implement c4c accessD latest lookup/resolver, target normalization, source union, entry
mapping, snapshot assembly, or real capture.

## Allowed Files

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Stop Condition

Stop after this docs-only review commit is pushed. Do not implement discovery/capture,
perform a trusted capture, or start c4c.
