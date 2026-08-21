# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase

`4C-2d3b1i6d1d5f1c4c0` — JRA target accessD locator-source retention.

Formal base: `06b7d6df7ea57fab04a9abe70d67c580963ea3d2`.

Approved parent prepare: `3bb98aaa25e142ba7b104c0123349f961baa3da9`.

Review branch: `review/4c-2d3b1i6d1d5f1c4c0-jra-target-accessd-locator-retention-prepare`.

## Scope

This is documentation-only investigation. It freezes the owner and retention
boundary for the exact canonical accessD URL before target-card capture, archive
lookup, resolution, or normalization. It does not add a target locator, a navigation
parser, capture/archive APIs, persistence, schema, tests, HTTP, or real capture.

## Investigation Result

### Existing ownership is insufficient

`TARGET_CAPTURE_REAL_CALLER_EXISTS: NO`.

The only production definition of
`JRAOfficialLiveResponseCaptureService.capture_target_race_card_response(*,
response_url)` is the live service method itself. It canonicalizes and captures a
caller-provided accessD URL; it does not discover, retain, or return a locator. There
is consequently no production caller-owned URL origin, formal caller domain, retained
locator, or replay-safe caller handoff. Tests are not production ownership.

`JRA_TARGET_RACE_DISCOVERY_EXISTS: NO`.

There is no formal official JRA race-list/navigation boundary that emits canonical
accessD URLs. `JRAFetcher` is a hard-coded sample. `fetch_races.py` only dispatches
that sample. The legacy `races.deba_table_url` is written from the NAR parser and read
by the NAR local fetcher; it has no canonical JRA/accessD/race-identity semantics.
No persisted simulation request field or historical snapshot/source domain contains a
JRA target-card locator. The request document has an exact version-1 race schema and
cannot be silently extended or reused as such a locator domain.

The v3 response archive does retain `canonical_source_url`, but only on an already
selected schema-v3 capture. The exact-evidence loader therefore cannot answer the
pre-normalization question. `ACCESSD_URL_PERSISTED_IN_CAPTURE_ARCHIVE: YES`, while
`PRE_NORMALIZATION_ACCESSD_REPLAY_LOCATOR_PERSISTED: NO` remains true.

### Selected prerequisite: D

`SELECTED_ARCHITECTURE_CATEGORY:
NEW_OFFICIAL_JRA_TARGET_DISCOVERY_BOUNDARY_REQUIRED`.

The lexical locator domain is sufficient, but no existing formal producer gives it a
trusted origin. An explicit caller input alone would only relocate that missing
official discovery problem and would permit an arbitrary URL in production. A generic
source protocol accepting only `external_race_id` would be equally unsafe: the accessD
CNAME includes an opaque two-hex tail, and the URL parser is intentionally not an
inverse race-ID URL builder. Race-ID-only archive enumeration is not approved.

The next narrow predecessor must formalize one official JRA target-navigation discovery
boundary. It must consume exact supplied official navigation evidence, extract one
row/request-local canonical accessD URL, validate it with
`parse_jra_race_card_url_identity(...)`, and retain the result before either live
capture or replay selection. It must never infer a URL from displayed date/venue/race,
names, legacy NAR data, or opaque CNAME material.

### Frozen locator and retention contract

The new JRA-specific domain is ready to freeze in a dedicated module:

```python
@dataclass(frozen=True, slots=True)
class JRATargetRaceCardLocator:
    external_race_id: str
    canonical_target_race_card_url: str
```

Its constructor must require an exact canonical `JRAExternalRaceIdentity`, an exact
canonical accessD `TARGET_RACE_CARD` URL, and equality between the supplied race ID and
`parse_jra_race_card_url_identity(url).external_race_id`. It has no inverse URL
construction, no display-text identity, and no package-root export. Its ownership is
`scripts/simulation/jra_target_race_card_locator.py`, not neutral
`HistoricalInputSourceRecord.record_values` and not a capture-row retrofit.

The locator is immutable request metadata, not target-card response evidence. It carries
no observed timestamp and does not invent `available_at`. But the upstream discovery
that creates and retains it must preserve the exact official navigation source evidence
(canonical navigation URL, raw response SHA-256, and actual observation time) under its
own future formal evidence/capture contract. The later resolved accessD response remains
the sole evidence for target track/entry/jockey/odds source records.

`CAN_MULTIPLE_CANONICAL_ACCESSD_URLS_BIND_ONE_RACE_ID: YES_BY_LEXICAL_OPAQUE_TAIL`.
Identical URLs are equivalent duplicates. The upstream official discovery must emit one
exact locator for one target-navigation request. Different canonical URLs for the same
race in the same retained request context are a conflict and fail closed; timestamp or
provenance alone does not authorize choosing one. A future versioned/revision policy
would need its own approved design before differing locators could coexist.

For deterministic automated replay, locator retention must be durable. Existing
persisted simulation requests, neutral source records, snapshots, and the response
archive are not reusable because none owns this pre-capture JRA association. The future
discovery/retention prerequisite therefore needs a dedicated append-only JRA locator
repository domain and schema table. Its minimum immutable payload is the canonical race
ID, canonical accessD URL, and the source-navigation evidence identity above, with a
unique race-to-locator association and conflict-on-different-URL behavior. This is a
new locator-source persistence schema, not a change to capture schema-v3.

### Future live/replay handoff

Once the retained source exists, both live capture and replay must consume the same exact
locator. A later live API should accept `locator: JRATargetRaceCardLocator` rather than
a bare string, validate it, fetch only `locator.canonical_target_race_card_url`, and
preserve the race-identity agreement in its schema-v3 response. Live capture still does
not discover a locator.

The later replay sequence is:

```text
official target navigation evidence
-> retained JRATargetRaceCardLocator
-> latest archived accessD at or before captured_at
-> pure c4c target-card resolver
-> existing target normalization
-> retained accessU locators
-> causal accessU, accessS, and accessO resolution
-> later source union and exact entry mapping
-> existing snapshot builder
```

The current snapshot builder makes `captured_at` the effective archive bound because it
requires each evidence observation to be no later than both `captured_at` and
`information_cutoff`, with `captured_at <= information_cutoff`. The locator itself is
not an evidence timestamp and does not change that causal rule.

## Readiness Matrix

```text
TARGET_CAPTURE_REAL_CALLER_EXISTS: NO
TARGET_CAPTURE_CALLER_OWNS_EXACT_URL: N/A_NO_PRODUCTION_CALLER
TARGET_CAPTURE_CALLER_URL_ORIGIN: NONE
TARGET_CAPTURE_CALLER_FORMAL_DOMAIN: NONE
TARGET_CAPTURE_CALLER_PERSISTED: NO
TARGET_CAPTURE_CALLER_REPLAY_SAFE: NO
JRA_TARGET_RACE_DISCOVERY_EXISTS: NO
JRA_TARGET_RACE_DISCOVERY_FORMAL: NO
JRA_TARGET_RACE_DISCOVERY_RETURNS_EXACT_ACCESSD_URL: NO
JRA_TARGET_RACE_DISCOVERY_CAUSALLY_AUDITABLE: NO

EARLIEST_EXACT_ACCESSD_URL_OWNER: MISSING_OFFICIAL_JRA_TARGET_NAVIGATION_DISCOVERY
LOCATOR_RETENTION_MOMENT: IMMEDIATELY_ON_EXACT_OFFICIAL_NAVIGATION_EXTRACTION_BEFORE_CAPTURE_OR_REPLAY

LOCATOR_DOMAIN_READY: YES_LEXICAL_DOMAIN_ONLY
LOCATOR_MODULE: scripts/simulation/jra_target_race_card_locator.py
LOCATOR_PROVENANCE_REQUIRED: YES_AT_UPSTREAM_DISCOVERY_RETENTION_BOUNDARY
LOCATOR_OBSERVED_AT_REQUIRED: NO_ON_LOCATOR_DOMAIN
LOCATOR_SOURCE_EVIDENCE_REQUIRED: YES

LOCATOR_PERSISTENCE_REQUIRED: YES
LOCATOR_PERSISTENCE_OWNER: DEDICATED_APPEND_ONLY_JRA_TARGET_LOCATOR_REPOSITORY
EXISTING_PERSISTENCE_DOMAIN_REUSABLE: NO
NEW_SCHEMA_REQUIRED: YES
NEW_TABLE_REQUIRED: YES

CAN_MULTIPLE_CANONICAL_ACCESSD_URLS_BIND_ONE_RACE_ID: YES_BY_LEXICAL_OPAQUE_TAIL
LOCATOR_UNIQUENESS_POLICY: ONE_EXACT_UPSTREAM_LOCATOR_PER_RETAINED_TARGET_REQUEST; IDENTICAL_URL_DUPLICATES_EQUIVALENT
LOCATOR_CONFLICT_POLICY: DIFFERENT_CANONICAL_URLS_FOR_SAME_RACE_AND_REQUEST_CONTEXT_FAIL_CLOSED

LOCATOR_SOURCE_PROTOCOL_REQUIRED: YES_AFTER_OFFICIAL_DISCOVERY_AND_RETENTION_ARE_FORMAL
EXTERNAL_RACE_ID_ONLY_LOCATOR_LOOKUP_SAFE: NO

LIVE_CAPTURE_API_CHANGE_REQUIRED: YES
LIVE_CAPTURE_LOCATOR_BINDING_READY: YES_AFTER_DISCOVERY_AND_RETENTION_IMPLEMENTATION

TARGET_ACCESSD_LOCATOR_SOURCE_READY: NO
TARGET_ACCESSD_LOCATOR_RETENTION_READY: NO
EXACT_ACCESSD_LOCATOR_AVAILABLE_BEFORE_RESOLUTION: NO

RACE_ID_ONLY_ARCHIVE_LOOKUP_SAFE: NO
MAPPING_PREREQUISITE_REQUIRED: YES

C4C_IMPLEMENTATION_READY_AFTER_THIS: NO
IMPLEMENTATION_READY: NO
BLOCKERS: official JRA target-navigation discovery; durable exact-locator retention; separate external-entry/internal-entry mapping
REAL_TRUSTED_CAPTURE_REQUIRED: NO
```

## Next Phase

Recommend `4C-2d3b1i6d1d5f1c4c0a — JRA official target-navigation locator discovery
and retention PREPARE`. It must first identify the exact official navigation response
family, supplied-response/capture/evidence contract, selector, race/request binding,
and append-only locator persistence contract. It must not implement c4c resolver or
accessD archive lookup. Only after that phase is implemented and the three target-locator
readiness fields are `YES` may c4c implement its exact accessD lookup/resolver.

## Allowed Files

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Stop Condition

Stop after this documentation-only review commit is pushed. Do not implement official
navigation discovery, locator storage, capture changes, resolver/archive lookup, entry
mapping, source union, snapshot assembly, or real capture.
