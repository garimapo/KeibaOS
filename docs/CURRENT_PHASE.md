# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase

`4C-2d3b1i6d1d5f1c4c` — JRA target accessD historical causal resolution.

Formal base: `06b7d6df7ea57fab04a9abe70d67c580963ea3d2`.

Review branch: `review/4c-2d3b1i6d1d5f1c4c-jra-target-accessd-causal-prepare`.

## Scope

This PREPARE is documentation only. It freezes the missing pre-normalization replay
boundary for one target accessD card. It does not implement target-source collection,
archive lookup, source union, internal entry mapping, snapshot construction, HTTP, or
real capture.

## Investigation Result

### Exact accessD URL source

`EXACT_ACCESSD_URL_CURRENTLY_PERSISTED: NO` for a formal JRA replay input.

`EXACT_ACCESSD_URL_CURRENTLY_FORMAL: NO` before a target-card response is supplied.

The schema-v3 JRA archive persists `canonical_source_url` only on an already-known
capture. Its target-card evidence loader likewise requires the exact URL, body digest,
and observation timestamp. `JRASuppliedOfficialResponse.response_url` proves the URL
only after the caller has already selected the response, while
`JRATargetRaceSourceCollection` deliberately retains only row-local accessU locators.

The legacy `races.deba_table_url` column is not a JRA locator source: current writes
are populated by `scripts/parsers/nar_parser.py`, and `scripts/fetch_local.py` consumes
it through the NAR provider. The generic sample `JRAFetcher` is not an official JRA
navigation/capture pipeline. The v3 live accessD service accepts a caller-provided URL;
it does not discover, retain, or expose one from a formal JRA race domain.

`EXACT_ACCESSD_URL_SOURCE: NONE_FORMAL_BEFORE_TARGET_NORMALIZATION`.

`TARGET_ACCESSD_LOCATOR_SOURCE_READY: NO`.

The existing accessD CNAME grammar includes an opaque two-hex tail. The parser maps a
canonical URL to a race identity but does not make the inverse mapping valid. Race-ID
archive scanning is therefore not approved: the archive has no external-race-ID column,
the grammar permits multiple tails for one identity, and enumeration would have to
separate valid candidates from corrupt v3 rows without a proven unique selection rule.

`RACE_ID_ONLY_ARCHIVE_LOOKUP_SAFE: NO`.

### Required predecessor

`TARGET_ACCESSD_LOCATOR_RETENTION_REQUIRED: YES`.

The smallest required JRA-specific domain is:

```python
@dataclass(frozen=True, slots=True)
class JRATargetRaceCardLocator:
    external_race_id: str
    canonical_target_race_card_url: str
```

Its constructor must require canonical `external_race_id`, canonical accessD URL, and
`parse_jra_race_card_url_identity(url).external_race_id == external_race_id`. The URL
must be emitted by the exact approved official JRA navigation/acquisition boundary that
first receives it; it must never be synthesized from the race identity or placed in
neutral `HistoricalInputSourceRecord.record_values`.

No current formal boundary owns that source. The next prerequisite is therefore
`4C-2d3b1i6d1d5f1c4c0 — JRA target accessD locator-source retention PREPARE`, to locate
and formalize the exact official navigation/acquisition handoff. It must not reuse the
NAR legacy column or invent a race-ID query.

## Frozen Subsequent Causal Contract

After locator retention is formal, add a separate pure JRA resolver module with exactly:

```python
class JRATargetRaceCardResponseProvider(Protocol):
    def __call__(
        self,
        *,
        locator: JRATargetRaceCardLocator,
        observed_at_not_after: datetime,
    ) -> JRASuppliedOfficialResponse | None: ...

class JRATargetRaceCardResolutionError(ValueError): ...
class JRATargetRaceCardResolutionValidationError(
    JRATargetRaceCardResolutionError
): ...
class JRATargetRaceCardResolutionUnavailableError(
    JRATargetRaceCardResolutionError
): ...

def resolve_jra_target_race_card_response(
    *,
    locator: JRATargetRaceCardLocator,
    observed_at_not_after: datetime,
    target_race_card_response_provider: JRATargetRaceCardResponseProvider,
) -> JRASuppliedOfficialResponse: ...
```

The pure resolver accepts only exact locator/aware datetime/response types, invokes its
provider once with the unchanged caller value, and accepts only the locator's exact
canonical accessD URL whose parsed race identity equals the locator identity and whose
`observed_at <= observed_at_not_after`. `None` becomes the dedicated unavailable error.
Provider exceptions, including `RepositoryDataIntegrityError`, propagate unchanged; no
broad catch, HTTP, archive, filesystem, clock, or raw HTML parsing is permitted.

The future repository method is:

```python
load_latest_target_race_card_supplied_response(
    *,
    canonical_target_race_card_url: str,
    observed_at_not_after: datetime,
) -> JRASuppliedOfficialResponse | None
```

It accepts the exact canonical URL and inclusive aware bound, selects the greatest
eligible observed time, and queries by stable URL plus cutoff without filtering away
family metadata that corruption must expose. At the selected timestamp exactly one row
must reconstruct as schema-v3 `TARGET_RACE_CARD`, GET, null request identity/cname, and
the exact canonical URL; tied, malformed, wrong-family, or corrupt body/domain rows
raise `RepositoryDataIntegrityError`. A genuine no-result alone returns `None`. There is
no accessS/accessU/accessO fallback.

`ARCHIVE_SCHEMA_CHANGE_REQUIRED: NO` and `ARCHIVE_INDEX_CHANGE_REQUIRED: NO` once an
exact locator is available. The existing v3 capture table already stores canonical URL,
observed time, family, GET request fields, and raw body. No speculative index is
authorized.

## Causality and Handoff

The resolver/repository immediately enforce an explicit inclusive
`observed_at_not_after`; scheduled start is not substituted because it is first parsed
from the selected card. The existing normalizer then continues to require
`response.observed_at <= scheduled_start_at`. Later orchestration must additionally
require `observed_at_not_after <= normalized target scheduled_start_at` before using the
target records.

The snapshot builder requires every evidence observation to be no later than both
`captured_at` and `information_cutoff`, and independently requires
`captured_at <= information_cutoff <= scheduled_start_at`. Consequently, under the
current formal builder contract the single effective archive observation bound is
`captured_at` (after its normal builder relation to `information_cutoff` is validated),
not scheduled start and not a later/current capture.

`FUTURE_EFFECTIVE_LOOKUP_BOUND_READY: YES`.

`FUTURE_EFFECTIVE_LOOKUP_BOUND: captured_at`.

The intended later sequence is:

```text
retained exact accessD locator
-> latest eligible archived accessD response
-> pure target-card resolver
-> existing accessD target normalization
-> target records plus retained accessU locators
-> per-entry causal accessU resolution
-> complete accessU discovery
-> causal accessS/accessO historical collection
-> later full source union and mapping
-> existing snapshot builder
```

No live fallback, backdating, synthetic card, future capture, fake target records, or
raw accessD reparse is allowed.

## Internal Entry Mapping Investigation

`EXTERNAL_ENTRY_TO_INTERNAL_ENTRY_MAPPING_READY: NO`.

The target source can derive canonical external entry identity from JRA race identity
and horse number. The legacy `horses` table contains `race_id`, `id`, and `horse_no`,
but the current `RaceEntrySource` maps requested internal horse IDs to entry IDs; it has
no provider-neutral external-entry/horse-number mapping API and the examined schema has
no uniqueness proof for `(race_id, horse_no)`. A later narrow mapping boundary must use
only internal race ID plus exact horse number, require one row per target entry and a
one-to-one mapping, and fail closed for missing/duplicate rows. It must not use names or
create a JRA/NAR horse bridge.

`MAPPING_PREREQUISITE_REQUIRED: YES`.

## Readiness

```text
ACCESSD_LATEST_ARCHIVE_LOOKUP_READY: YES_AFTER_EXACT_LOCATOR_RETENTION
TARGET_ACCESSD_RESOLVER_REQUIRED: YES
EXPLICIT_CAUSAL_BOUND_REQUIRED: YES
NO_ELIGIBLE_CAPTURE_POLICY: Repository None -> resolver unavailable error
LIVE_FALLBACK_ALLOWED: NO
RACE_LEVEL_ASSEMBLY_READY_AFTER_THIS: NO
IMPLEMENTATION_READY: NO
BLOCKERS: exact pre-normalization official accessD locator source; later exact external-entry/internal-entry mapping
REAL_TRUSTED_CAPTURE_REQUIRED: NO
```

## Future Test Intent

After the locator-source predecessor, implementation tests must cover canonical
locator/race agreement; malformed and other-family URL rejection; inclusive cutoff;
older eligible response selection over a later response; no-result/unavailable;
same-time and selected schema/page/method/request/body corruption integrity errors;
exact bound propagation; wrong URL/race and late response rejection; unchanged provider
exception propagation; no live fallback; no broad catch; no package-root export; and no
real trusted capture.

## Allowed Files

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Stop Condition

Stop after this documentation-only review commit is pushed. Do not implement the
locator-source predecessor, resolver, repository lookup, mapping, race-level assembly,
or real capture.
