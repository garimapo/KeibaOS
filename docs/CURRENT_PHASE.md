# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase

`4C-2d3b1i6d1d5f1c4c0a` — official JRA target accessD discovery/navigation.

Formal base: `06b7d6df7ea57fab04a9abe70d67c580963ea3d2`.

Previous review tip: `a8454fecf4a84a94910a3614996378737020e534`.

Review branch: `review/4c-2d3b1i6d1d5f1c4c0a-jra-target-accessd-discovery-prepare`.

## Scope

This documentation-only correction closes the complete official navigation chain that
produces an exact accessD target-card locator. It adds no production code, tests,
schema/migration, persistence, trusted capture, or formal-branch change.

## Read-only Official Navigation Evidence

Transient read-only official observations on 2026-08-21 and 2026-08-22 established the
following direct navigation chain. No response body was persisted, treated as trusted
historical evidence, or committed.

```text
canonical official JRA root GET https://www.jra.go.jp/
-> direct root-menu doAction('/JRADB/accessD.html', 'pw01dli00/F3')
-> POST https://www.jra.go.jp/JRADB/accessD.html, form cname=<that raw value>
-> 出馬表 開催選択 response
-> direct doAction('/JRADB/accessD.html', 'pw01drl00.../<HH>')
-> POST the same endpoint, form cname=<that exact raw value>
-> 出馬表 レース選択 response for one year/venue/meeting/day
-> direct same-row literal accessD target-card href
-> JRATargetRaceCardLocator
```

The canonical root page directly contains the required menu material, including the
official quick-menu control:

```html
<div id="quick_menu"> ...
  <a href="#" onclick="doAction('/JRADB/accessD.html','pw01dli00/F3');return false;">
```

The root GET is the closed public entrypoint; the `pw01dli00/F3` value is nevertheless
raw official response material, not a formal immutable CNAME constant. Future code must
strictly parse the direct control from its supplied root-menu response. It must never
insert this observed value as a caller-free literal, invent its opaque tail, or derive it
from race/date/venue/display text.

The established `doAction` implementation writes its raw argument to hidden lower-case
`cname` in `form#commForm01` and submits POST. Both selection requests therefore use the
official accessD POST endpoint, not synthesized GET URLs. The observed meeting- and
race-selection responses were HTTP 200 `text/html`, uncompressed under
`Accept-Encoding: identity`, advertised Shift_JIS and strictly CP932-decodable. Future
trusted transport must retain the established HTTPS, disabled-redirect, identity-
encoding, raw-byte, timeout/size, TLS, and 200-only policies; it must not create a
second transport stack.

## Complete Pure Discovery Contract

### Root menu to meeting-selection request

The first supplied domain is a dedicated immutable root-menu response. Existing
`JRASuppliedOfficialResponse` cannot represent it because that type accepts the JRA DB
accessS/accessU/accessD response families rather than the public root navigation page.
The future exact domain retains at least canonical root source URL, raw response bytes,
the strictly established source charset, and actual aware `observed_at`; it has no clock
or `available_at` ownership.

The future pure first producer is:

```python
discover_jra_target_meeting_selection_request_locator(
    *,
    navigation_menu_response: JRAOfficialTargetNavigationMenuSuppliedResponse,
) -> JRATargetMeetingSelectionRequestLocator
```

`JRATargetMeetingSelectionRequestLocator` is a dedicated immutable POST locator for the
fixed `https://www.jra.go.jp/JRADB/accessD.html` endpoint, the raw lower-case `cname`,
and its deterministic canonical POST fingerprint. Discovery inspects only the exact
official quick-menu control `#quick_menu a[href="#"][data-ga-click="quick_pc-1"]` with
one direct `doAction('/JRADB/accessD.html', '<raw-cname>')` invocation. Missing,
duplicate, malformed, escaped, wrong-endpoint, or distinct raw request controls fail
closed; duplicate exact markup may not create an arbitrary choice. The raw CNAME must
be validated only as direct official request material under the frozen meeting-selection
grammar; no target race identity is accepted as a substitute.

### Meeting-selection response to race-selection request

The minimal immutable meeting-selection supplied response is a dedicated strict-CP932
domain with its exact `JRATargetMeetingSelectionRequestLocator`, raw response bytes,
strict charset, and actual aware `observed_at`. Its request locator proves the exact
POST request identity; it does not need a fabricated response URL or timestamp.

The future pure second producer is:

```python
discover_jra_target_race_selection_request_locator(
    *,
    external_race_id: str,
    meeting_selection_response: JRATargetMeetingSelectionSuppliedOfficialResponse,
) -> JRATargetRaceSelectionRequestLocator
```

It parses the requested canonical JRA external race ID, examines only direct official
meeting-selection navigation controls, and takes the raw race-selection CNAME directly
from their unescaped single-quoted `doAction` request material. It parses the direct
navigation identity from the CNAME and requires exact year, venue, meeting number, and
meeting day agreement. Race number is intentionally not part of this stage. Display
names are not identities. Zero matching choices is unavailable; malformed candidate
material, a contradictory candidate, or multiple distinct matching request locators is
validation failure. There is no first-match choice and no opaque-tail synthesis.

The observed race-selection CNAME grammar remains exactly
`pw01drl00<VV><YYYY><MM><DD><YYYYMMDD>/<HH>`. Its canonical venue/year/meeting/day and
embedded calendar date are parsed and cross-checked; opaque uppercase `<HH>` is accepted
only when present literally in the official navigation control.

### Race-selection response to target-card locator

`TARGET_NAVIGATION_PAGE_KIND: TARGET_RACE_SELECTION`.

`TARGET_NAVIGATION_ENDPOINT: https://www.jra.go.jp/JRADB/accessD.html`.

`TARGET_NAVIGATION_REQUEST_METHOD: POST`.

`JRATargetRaceSelectionRequestLocator` contains the fixed endpoint, raw lower-case form
`cname`, and SHA-256 of canonical UTF-8 JSON:

```json
{"endpoint_url":"https://www.jra.go.jp/JRADB/accessD.html","form":{"cname":"<raw-cname>"},"method":"POST","schema_version":1}
```

using sorted keys and compact separators. It exposes the parsed direct selection identity
and is produced only by the preceding meeting-selection response.

The existing proposed race-selection supplied domain remains:

```python
@dataclass(frozen=True, slots=True)
class JRATargetRaceSelectionSuppliedOfficialResponse:
    request_locator: JRATargetRaceSelectionRequestLocator
    response_body: bytes
    charset: str  # exact "cp932"
    observed_at: datetime  # exact aware, normalized UTC
```

Its body is nonempty strict CP932. It is not an accessD card URL response and must not be
forced into `JRASuppliedOfficialResponse`.

The future pure final discovery API remains:

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

The exact page scope is:

```text
#contentsBody > div.race_select > table#race_list.basic.mt20 > tbody > tr
```

Every row requires one `th.race_num > a[href]` and one
`td.syutsuba > a.btn-def.btn-sm.btn-narrow[href]`. Both direct hrefs must resolve against
`https://www.jra.go.jp`, be canonicalized only through the approved raw-delimiter-to-
`%2F` accessD operation, parse through `parse_jra_race_card_url_identity(...)`, and
agree exactly. The row is selected solely by that parsed direct card identity; visible
names and labels are never identities. Its parsed date/venue/meeting/day must agree with
the selection request identity before race number is compared to the requested external
race identity. Missing target is unavailable. Malformed structure, two-anchor mismatch,
or multiple distinct matching URLs fails validation.

All three producers are pure: no HTTP, archive, database, filesystem, clock, or raw-card
parser ownership; no broad exception handling; and no arbitrary caller-provided raw
CNAME on the normal production path.

## Persistence and Causality

`MEETING_SELECTION_PERSISTENCE_REQUIRED: NO_OPERATIONAL_DISCOVERY_ONLY`.

The root-menu and meeting-selection responses are needed to make a current official
navigation request, but deterministic historical replay begins from the retained exact
race-selection POST response and request identity. It therefore does not need a second
persistent capture family merely to repeat stage one.

`RACE_SELECTION_PERSISTENCE_REQUIRED: YES`.

The exact race-selection POST response plus its exact request identity is the durable
evidence from which accessD locator discovery is replayed. The future archive extension
is a dedicated v004 `TARGET_RACE_SELECTION` family in the existing JRA archive, with its
own request identity, capture domain, methods, page kind, and migration. It reuses the
response-body table and preserves v1/v2/v3 semantics; it does not create a generic POST
union or locator table.

The response that proves a final locator retains actual `observed_at`, raw-byte digest,
and request identity. Later race-level orchestration must require that observation no
later than its explicit replay bound, which cannot exceed `captured_at`; it must neither
backdate navigation/card evidence nor invent `available_at`. The later target-card
resolver uses the retained exact locator with that same effective causal bound. No live
fallback is permitted in replay.

## Multiple accessD URLs and Site Variants

Current official navigation provides a counterexample to race-ID-only locator selection:
one target race is exposed through distinct canonical accessD URLs whose CNAMEs differ
by accessD site variant and opaque tail, while both URLs parse to the same formal
`JRAExternalRaceIdentity`. Site and opaque tail are not part of `external_race_id`.

```text
CAN_MULTIPLE_CANONICAL_ACCESSD_URLS_BIND_ONE_RACE_ID: YES_ACROSS_OFFICIAL_SITE_VARIANTS
EXTERNAL_RACE_ID_ONLY_LOCATOR_LOOKUP_SAFE: NO_PROVEN_BY_OFFICIAL_COUNTEREXAMPLE
RACE_ID_ONLY_ARCHIVE_LOOKUP_SAFE: NO_PROVEN_BY_OFFICIAL_COUNTEREXAMPLE
LOCATOR_UNIQUENESS_POLICY: EXACTLY_ONE_DISTINCT_MATCHING_URL_IN_ONE_SELECTION_RESPONSE
LOCATOR_CONFLICT_POLICY: DISTINCT_MATCHING_URLS_IN_ONE_SELECTION_RESPONSE_FAIL_CLOSED; CROSS_OBSERVATION_OR_SITE_VARIANT_SELECTION_IS_DEFINED_BY_RETAINED_NAVIGATION_EVIDENCE, NOT_BY_EXTERNAL_RACE_ID
SITE_VARIANT_SYNTHESIS_ALLOWED: NO
```

The same direct URL twice in the two designated anchors of one exact official row is one
distinct candidate, not a second URL. Nothing may collapse site `01` and `10`, choose an
arbitrary observed variant, or reconstruct a synthetic canonical URL.

## Readiness Matrix

```text
OFFICIAL_NAVIGATION_CHAIN_PROVEN: YES_THREE_RESPONSE_DERIVED_STAGES_FROM_CANONICAL_OFFICIAL_ROOT_MENU

MEETING_SELECTION_ENTRYPOINT_SOURCE: CANONICAL_OFFICIAL_JRA_ROOT_MENU_DIRECT_DOACTION
MEETING_SELECTION_REQUEST_IDENTITY_READY: YES_AS_RESPONSE_DERIVED_DEDICATED_POST_LOCATOR
MEETING_SELECTION_REQUEST_IS_FORMAL_CONSTANT: NO
MEETING_SELECTION_REQUEST_REQUIRES_UPSTREAM_DISCOVERY: YES_FROM_EXACT_OFFICIAL_ROOT_MENU_CONTROL
MEETING_SELECTION_SUPPLIED_RESPONSE_READY: YES_DEDICATED_STRICT_CP932_REQUEST_BOUND_DOMAIN
MEETING_SELECTION_DISCOVERY_PUBLIC_API_READY: YES
MEETING_SELECTION_PERSISTENCE_REQUIRED: NO_OPERATIONAL_DISCOVERY_ONLY

RACE_SELECTION_REQUEST_DISCOVERY_READY: YES_AFTER_MEETING_SELECTION_RESPONSE_DOMAIN
RACE_SELECTION_REQUEST_LOCATOR_READY: YES_DEDICATED_RAW_CNAME_POST_LOCATOR
RACE_SELECTION_PERSISTENCE_REQUIRED: YES

ACCESSD_LOCATOR_PRESENT_DIRECTLY_IN_RESPONSE: YES
TARGET_RACE_BINDING_READY: YES_BY_PARSED_DIRECT_ACCESSD_URL_IDENTITY

CAN_MULTIPLE_CANONICAL_ACCESSD_URLS_BIND_ONE_RACE_ID: YES_ACROSS_OFFICIAL_SITE_VARIANTS
EXTERNAL_RACE_ID_ONLY_LOCATOR_LOOKUP_SAFE: NO_PROVEN_BY_OFFICIAL_COUNTEREXAMPLE
RACE_ID_ONLY_ARCHIVE_LOOKUP_SAFE: NO_PROVEN_BY_OFFICIAL_COUNTEREXAMPLE
LOCATOR_UNIQUENESS_POLICY: EXACTLY_ONE_DISTINCT_MATCHING_URL_IN_ONE_SELECTION_RESPONSE
LOCATOR_CONFLICT_POLICY: DISTINCT_MATCHING_URLS_IN_ONE_SELECTION_RESPONSE_FAIL_CLOSED; CROSS_OBSERVATION_OR_SITE_VARIANT_SELECTION_IS_DEFINED_BY_RETAINED_NAVIGATION_EVIDENCE, NOT_BY_EXTERNAL_RACE_ID
SITE_VARIANT_SYNTHESIS_ALLOWED: NO

JRA_CAPTURE_ARCHIVE_EXTENSION_REQUIRED: YES
ARCHIVE_SCHEMA_CHANGE_REQUIRED: YES_JRA_CAPTURE_SCHEMA_V004
ARCHIVE_NEW_PAGE_KIND_REQUIRED: YES_TARGET_RACE_SELECTION

TARGET_ACCESSD_LOCATOR_SOURCE_READY: YES_AFTER_THREE_PURE_DISCOVERY_STAGES_ARE_IMPLEMENTED
TARGET_ACCESSD_LOCATOR_RETENTION_READY: YES_AFTER_RETAINED_RACE_SELECTION_CAPTURE_IS_IMPLEMENTED
EXACT_ACCESSD_LOCATOR_AVAILABLE_BEFORE_RESOLUTION: YES_ONLY_FROM_RETAINED_EXACT_NAVIGATION_EVIDENCE

IMPLEMENTATION_READY: NO_PENDING_COMPLETE_FIRST_STAGE_DISCOVERY_CONTRACT_APPROVAL
BLOCKERS: independent approval and implementation of root-menu-derived meeting-selection request production, meeting-selection-to-race-selection request discovery, dedicated v004 race-selection capture/archive/migration, and final direct-href discovery; external-entry/internal-entry mapping remains later
REAL_TRUSTED_CAPTURE_REQUIRED: NO
REAL_TRUSTED_CAPTURE_MISSING_FACT: NONE
```

## Future Tests and Next Phase

The future implementation must use synthetic strict-CP932 selection HTML and synthetic
root-menu navigation material. It must test the exact public APIs/signatures; root direct
control grammar and no hard-coded menu CNAME; raw request fingerprints; direct
meeting-selection controls selected only by year/venue/meeting/day; no race-number at
that stage; zero/ambiguous/malformed requests; exact response/request lineage; direct
race-row hrefs; raw-slash-to-canonical-`%2F` conversion; row-local parsed identity;
same-row duplicate treatment; distinct same-response URL conflict; cross-variant retained
evidence behavior; source digest/observation; no tail/site synthesis; no display-name
binding; pure dependency surface; no package export; and no real capture. Capture tests
must pin v1/v2/v3 immutability and v4 family-only POST archive/load/corruption/migration
behavior. Causal tests must reject retained selection evidence after the future explicit
replay bound without a live/current fallback.

After independent approval, `4C-2d3b1i6d1d5f1c4c0b — JRA target race-selection discovery
and capture v004 IMPLEMENTATION` may implement the lexical target locator, root-menu and
meeting-selection navigation/request discovery domains, `JRATargetRaceSelectionRequestLocator`,
race-selection supplied response, pure target-card discovery, dedicated v4
capture/archive/migration, and dedicated live POST composition from an exact discovered
locator. It must not accept arbitrary raw CNAME input on the production path or implement
accessD latest lookup/resolver, target normalization, source union, entry mapping,
snapshot assembly, or real capture.

## Allowed Files

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Stop Condition

Stop after this docs-only correction commit is pushed. Do not implement discovery/capture,
perform a trusted capture, or start the next phase.
