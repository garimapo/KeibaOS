# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase

`4C-2d3b1i6d1d5f1c4c` — JRA causal target accessD resolution.

Formal base: `af0baed9050068ec6c2c5255ab82a12510968aa6`.

Review branch:
`review/4c-2d3b1i6d1d5f1c4c-jra-causal-target-accessd-prepare`.

This PREPARE is documentation only. It adds no production code, tests, schema,
migration, HTTP, or trusted capture.

## Responsibility and Public Boundary

C4c owns one pure, injected pre-normalization resolver. Given a canonical target race,
the exact retained schema-v4 race-selection capture ID, and one explicit effective
replay bound, it reconstructs the exact navigation evidence, rediscovers the accessD
locator through the formal c0b1 discovery contract, resolves one causally retained
schema-v3 capture for that exact URL, and returns its supplied response with audit
provenance.

The future module is `scripts/simulation/jra_target_race_card_resolution.py`. Its public
surface is:

```python
class JRATargetRaceSelectionCaptureProvider(Protocol):
    def __call__(
        self,
        *,
        capture_id: str,
    ) -> JRATargetRaceSelectionResponseCapture | None: ...

class JRATargetRaceCardCaptureProvider(Protocol):
    def __call__(
        self,
        *,
        locator: JRATargetRaceCardLocator,
        causal_cutoff: datetime,
    ) -> JRAOfficialTargetRaceCardResponseCapture | None: ...

class JRATargetRaceCardResolutionError(ValueError): ...
class JRATargetRaceCardResolutionValidationError(
    JRATargetRaceCardResolutionError
): ...
class JRATargetRaceCardResolutionUnavailableError(
    JRATargetRaceCardResolutionError
): ...

@dataclass(frozen=True, slots=True)
class JRATargetRaceCardResolution:
    response: JRASuppliedOfficialResponse
    discovery: JRATargetRaceCardDiscovery
    target_race_selection_capture_id: str
    target_race_card_capture_id: str
    target_race_card_response_sha256: str
    causal_cutoff: datetime

def resolve_jra_target_race_card_response(
    *,
    external_race_id: str,
    target_race_selection_capture_id: str,
    causal_cutoff: datetime,
    target_race_selection_capture_provider:
        JRATargetRaceSelectionCaptureProvider,
    target_race_card_capture_provider:
        JRATargetRaceCardCaptureProvider,
) -> JRATargetRaceCardResolution: ...
```

The future race-level replay orchestration is the caller. It must retain and supply the
exact v4 capture ID produced by c0b3 and derive `causal_cutoff` from the snapshot replay
boundary. The existing
`normalize_jra_target_race_input_source_records(response=resolution.response)` is the
immediate downstream consumer. C4c creates no source records or snapshot.

## Exact Navigation Evidence

The resolver parses the canonical external race ID before provider calls and requires
an exact v4 capture ID. The v4 provider is invoked once by that ID. `None` means causal
navigation evidence is unavailable. Otherwise the result must be the exact
`JRATargetRaceSelectionResponseCapture`, with the requested capture ID, schema version
4, `TARGET_RACE_SELECTION`, exact POST locator, valid request identity, and complete
domain reconstruction.

The resolver requires both:

```text
v4 observed_at <= causal_cutoff
v4 stored_at   <= causal_cutoff
```

It converts the validated capture through `to_supplied_official_response()` and invokes
the existing `discover_jra_target_race_card_locator(...)` with the original canonical
race ID. That formal discovery is the only URL source. C4c never builds a URL from race
fields, chooses site 01/10, guesses an opaque tail, scans v4 rows by race ID, or selects a
latest v4 row. Multiple retained v4 captures remain distinct; the caller must supply the
exact retained provenance ID. A response containing ambiguous matching URLs continues
to fail through formal discovery.

## Causal Cutoff

`causal_cutoff` is an exact timezone-aware datetime normalized only for comparison. It is
inclusive and supplied unchanged to the target-card provider. It is not automatically
replaced by scheduled start or `information_cutoff`.

For the future snapshot flow, the effective value is the snapshot assembly
`captured_at`, after the caller has established:

```text
captured_at <= information_cutoff <= scheduled_start_at
```

This is stricter than filtering only at `information_cutoff`, because every neutral
evidence observation must also be no later than `captured_at`. The target scheduled start
is first available after normalization; later orchestration must recheck the bound against
that value. No timestamp is rewritten and no `available_at` is invented.

`stored_at` is an archive-eligibility guard, not neutral evidence. A response observed
before the bound but not durably retained until after the bound is unavailable for that
replay. The returned target source records continue to carry only their established
response `observed_at` and `available_at=None`.

## Target-Card Archive Lookup

The repository requires one new family-specific method:

```python
def load_latest_target_race_card_capture(
    self,
    *,
    canonical_target_race_card_url: str,
    causal_cutoff: datetime,
) -> JRAOfficialTargetRaceCardResponseCapture | None: ...
```

It accepts only an exact canonical accessD `TARGET_RACE_CARD` URL and exact aware bound.
It queries only that exact URL and observations no later than the inclusive bound. It
reconstructs candidate rows before family acceptance so corrupt schema/page/method/
request/body/timestamp state cannot become false absence, then retains only captures
whose `stored_at <= causal_cutoff`.

The selected capture is the greatest actual eligible `observed_at`. At that latest
instant, exactly one reconstructed schema-v3 `TARGET_RACE_CARD` GET capture with null
request identity/CNAME and the exact URL must exist. Multiple rows at that instant fail
with `RepositoryDataIntegrityError`; SHA, capture-ID, body, metadata, or family
corruption also remains an integrity error. No eligible capture returns `None`.

Identical bodies captured at different observation times remain distinct and the latest
eligible observation wins. Changed bodies at different times follow the same rule.
Distinct bodies, duplicate evidence, or any other multiple capture state at the same
latest observation fail closed; stored time and capture ID are not arbitrary tie-breaks.
Different site variants and opaque-tail URLs never match because canonical URL equality
is exact.

No new schema, migration, table, column, or index is required. The current capture table
already retains URL, response digest/body, observed/stored times, family metadata, and
capture ID. The existing partial unique evidence index preserves exact evidence
integrity; this correctness-first lookup may scan the bounded exact-URL candidates, and
no speculative performance index is authorized.

## Resolution Validation and Provenance

The v3 provider is invoked exactly once with the discovered exact locator and the same
caller-supplied cutoff object/value. `None` raises the dedicated unavailable error. The
returned value must be exact `JRAOfficialTargetRaceCardResponseCapture`; its capture ID,
canonical URL, parsed external race identity, schema/page/GET family, body digest, and
timestamps are revalidated. Both `observed_at` and `stored_at` must be no later than the
bound. It then converts through the existing `to_supplied_official_response()`; the
normalizer input type and behavior remain unchanged.

The frozen result owns the audit handoff without duplicating raw bytes. Its discovery
retains exact v4 request locator, request identity, navigation response digest, observed
time, and target URL. It additionally retains v4 and v3 capture IDs, the selected v3
response digest, and the exact causal cutoff. The supplied response owns the single raw
target-card byte payload and its observation. Direct result construction rechecks all
cross-domain lineage.

Provider-owned errors, including `RepositoryDataIntegrityError`, propagate unchanged.
Missing exact v4 or eligible v3 evidence is unavailable. Existing but wrong, future,
contradictory, malformed, or ambiguous evidence is validation/integrity failure, never
missing. C4c adds no unsupported classification: recognized unsupported official card
values remain the existing target normalizer's responsibility.

## Future-Leak and Live Boundaries

Tests must prove that v4 or v3 captures observed after the bound are never inspected as
eligible; a v4 before the bound with only a future v3 returns unavailable; stored-after-
bound captures are unavailable even if observed earlier; alternate site variants never
substitute; and future/current rows cannot become fallback when causal evidence is
missing. Exact repeated resolution must be deterministic.

C4c contains no HTTP, live service, archive composition, filesystem, clock, random, or
subprocess ownership. It never invokes `capture_target_race_navigation(...)` or
`capture_target_race_card_response(...)`, auto-captures missing evidence, backdates a
response, or reparses target-card HTML. The sole HTML parse is the existing formal v4
navigation discovery needed to recover its retained direct locator.

## Future Test Intent

Implementation tests must directly cover canonical success; exact public surfaces and
signatures; exact v4 ID lookup; exact URL/site/tail retention; inclusive observation and
storage bounds; future v4/v3 and stored-late rejection; missing v4/v3 unavailable;
newer/current no-fallback; formal discovery ambiguity; corrupt v4/v3 propagation;
latest eligible exact-URL v3 selection; identical/changed body policy; same-time conflict;
provider call counts and unchanged cutoff; exact provenance; supplied response identity;
unchanged normalizer input; no race-ID/latest-v4 API; no live HTTP/auto-capture; no broad
catch; no package-root export; and deterministic offline behavior.

## Readiness Matrix

```text
C4C_OWNER: PURE_INJECTED_jra_target_race_card_resolution_MODULE
C4C_PUBLIC_API: resolve_jra_target_race_card_response_WITH_EXACT_V4_CAPTURE_ID_AND_CAUSAL_CUTOFF
C4C_RESULT_DOMAIN: FROZEN_SLOTTED_JRATargetRaceCardResolution
C4C_CALLER: FUTURE_RACE_LEVEL_REPLAY_ORCHESTRATION_RETAINING_EXACT_C0B3_V4_CAPTURE_ID
C4C_DOWNSTREAM_CONSUMER: EXISTING_normalize_jra_target_race_input_source_records

TARGET_CARD_URL_SOURCE: FORMAL_DISCOVERY_FROM_EXACT_RETAINED_V4_RACE_SELECTION_CAPTURE
RACE_ID_URL_SYNTHESIS_ALLOWED: NO
SITE_VARIANT_GUESSING_ALLOWED: NO
OPAQUE_TAIL_GUESSING_ALLOWED: NO

CUTOFF_FIELD: EXPLICIT_CALLER_SUPPLIED_CAUSAL_CUTOFF_EXPECTED_TO_EQUAL_FUTURE_SNAPSHOT_CAPTURED_AT
RACE_SELECTION_ELIGIBILITY: observed_at_AND_stored_at_LE_CAUSAL_CUTOFF
TARGET_CARD_ELIGIBILITY: observed_at_AND_stored_at_LE_CAUSAL_CUTOFF
STORED_AT_ROLE: DURABLE_ARCHIVE_ELIGIBILITY_GUARD_NOT_NEUTRAL_EVIDENCE
AVAILABLE_AT_ROLE: NONE_NOT_INVENTED

RACE_SELECTION_ARCHIVE_LOOKUP_KEY: EXACT_CALLER_RETAINED_V4_CAPTURE_ID
RACE_ID_ONLY_V4_LOOKUP_ADDED: NO
LATEST_BY_RACE_V4_LOOKUP_ADDED: NO
WHY_LOOKUP_IS_AUDITABLE: EXACT_V4_ID_RECONSTRUCTION_THEN_FORMAL_DISCOVERY_AND_EXACT_URL_BOUNDED_V3_SELECTION

TARGET_CARD_V3_LOOKUP_KEY: EXACT_DISCOVERED_CANONICAL_ACCESSD_URL_PLUS_INCLUSIVE_CAUSAL_CUTOFF
TARGET_CARD_URL_MATCH_POLICY: EXACT_CANONICAL_URL_ONLY
TARGET_CARD_RESPONSE_DIGEST_POLICY: RECONSTRUCT_AND_VERIFY_SELECTED_CAPTURE; RETAIN_DIGEST_IN_RESULT
TARGET_CARD_OBSERVED_AT_POLICY: GREATEST_ELIGIBLE_OBSERVED_AT_WITH_STORED_AT_ALSO_ELIGIBLE
TARGET_CARD_MISSING_POLICY: REPOSITORY_NONE_TO_DEDICATED_RESOLUTION_UNAVAILABLE

MULTIPLE_ELIGIBLE_V4_POLICY: NO_ENUMERATION_OR_SELECTION; EXACT_CALLER_SUPPLIED_CAPTURE_ID_ONLY
MULTIPLE_ELIGIBLE_V3_POLICY: LATEST_ELIGIBLE_OBSERVED_AT; SAME_LATEST_TIME_FAILS_CLOSED
IDENTICAL_BODY_MULTIPLE_CAPTURE_POLICY: DISTINCT_TIMES_REMAIN_DISTINCT_AND_LATEST_ELIGIBLE_WINS; SAME_TIME_DUPLICATION_IS_INTEGRITY_FAILURE
DIFFERENT_BODY_MULTIPLE_CAPTURE_POLICY: DISTINCT_TIMES_LATEST_ELIGIBLE_WINS; SAME_LATEST_TIME_IS_INTEGRITY_FAILURE
SITE_VARIANT_COLLAPSE_ALLOWED: NO

LIVE_HTTP_IN_C4C: NO
LIVE_FALLBACK_ALLOWED: NO
CURRENT_TARGET_CARD_FALLBACK_ALLOWED: NO
AUTO_CAPTURE_ON_MISSING_ALLOWED: NO

FINAL_SUPPLIED_RESPONSE_TYPE: JRASuppliedOfficialResponse
TARGET_NORMALIZER_INPUT_UNCHANGED: YES
RAW_HTML_REPARSE_PATH_ADDED: NO_TARGET_CARD_REPARSE; EXISTING_FORMAL_V4_NAVIGATION_DISCOVERY_ONLY

PROVENANCE_OWNER: JRATargetRaceCardResolution
V4_CAPTURE_ID_RETAINED: YES
V3_CAPTURE_ID_RETAINED: YES
CUT_OFF_RETAINED: YES_EXACT_CAUSAL_CUTOFF
DUPLICATE_RAW_BYTES_RETAINED: NO

C4C_STOPS_AT: EXACT_TARGET_CARD_SUPPLIED_RESPONSE_PLUS_AUDIT_PROVENANCE
SOURCE_RECORD_CREATED_IN_C4C: NO
SNAPSHOT_ASSEMBLY_IN_C4C: NO

SCHEMA_CHANGE_REQUIRED: NO
MIGRATION_REQUIRED: NO
NEW_TABLE_REQUIRED: NO
NEW_COLUMN_REQUIRED: NO
NEW_INDEX_REQUIRED: NO
NEW_REPOSITORY_API_REQUIRED: YES_ONE_FAMILY_SPECIFIC_LATEST_EXACT_URL_CAUSAL_V3_CAPTURE_LOOKUP

C4C_IMPLEMENTATION_READY: YES
BLOCKERS: NONE_FOR_C4C; LATER_RACE_LEVEL_ORCHESTRATION_MUST_RETAIN_V4_ID_AND_SUPPLY_SNAPSHOT_DERIVED_BOUND
REAL_TRUSTED_CAPTURE_REQUIRED: NO
REAL_TRUSTED_CAPTURE_PERFORMED: NO
```

## Allowed Files

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Stop Condition

Stop after this docs-only review commit is pushed. Do not implement the resolver,
repository lookup, source normalization, entry mapping, source union, snapshot assembly,
HTTP, or real capture.
