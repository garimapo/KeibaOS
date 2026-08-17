# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase

`4C-2d3b1i6d1d5f1c4` — JRA target-horse accessU history response resolution.

Formal base: `0b8a5b3b590478ac880d27c4ecf387f5136c4806`.

Review branch: `review/4c-2d3b1i6d1d5f1c4-jra-accessu-history-resolution-prepare`.

## Scope

This preparation freezes a narrow boundary for supplying the exact causally eligible
accessU `JRASuppliedOfficialResponse` required by the existing JRA historical source
collector. It does not add HTTP, live capture, source collection, snapshot assembly, or
any target parser change.

## Current-Formal Finding

`JRATargetRaceSourceCollection` retains a canonical horse identity but deliberately
does not retain the exact row-local accessU URL. The accessD normalizer did parse that
anchor; however, its result is currently discarded. The capture archive can reconstruct
only an *already identified* evidence tuple:

```text
canonical_source_url + response_sha256 + observed_at
```

It has no public identity-based enumeration or latest-before-cutoff lookup. Its schema
stores accessU canonical URLs but has no JRA horse identity column or horse-history
query API. Therefore an external horse ID alone cannot resolve an accessU response
without synthesizing the forbidden opaque CNAME tail.

```text
ACCESSU_IDENTITY_LOOKUP_FROM_ARCHIVE_READY: NO
ACCESSU_URL_SYNTHESIS_ALLOWED: NO
EXACT_ACCESSU_LOCATOR_CURRENTLY_RETAINED: NO
RAW_ACCESSD_REPARSE_ALLOWED: NO
```

Later orchestration must not reparse the same accessD body to recover the discarded
anchor. The target normalizer is the formal owner of that row-local fact.

## Frozen Locator Correction

The minimal prerequisite is a JRA-specific companion value, not a provider-neutral
record-value extension:

```python
@dataclass(frozen=True, slots=True)
class JRATargetHorseHistoryLocator:
    external_race_id: str
    external_entry_id: str
    external_horse_id: str
    canonical_horse_history_url: str
```

Its constructor must require canonical JRA race/entry/horse lineage using existing
`parse_jra_external_race_id`, `parse_jra_external_horse_id`, and
`build_jra_external_entry_id`, and require that
`parse_jra_horse_profile_url_identity(canonical_horse_history_url)` equals
`external_horse_id`. The URL comes only from the exact row-local accessD horse anchor,
resolved against `https://www.jra.go.jp` and canonicalized using the existing
accessU-v1 URL canonicalizer. No horse-ID-to-URL builder or opaque-tail inference is
introduced.

`JRATargetRaceSourceCollection` must later gain an ordered
`target_horse_history_locators` tuple aligned one-to-one with `target_entry_records`.
The existing neutral `HistoricalInputSourceRecord` values and their record values stay
unchanged. Collection construction must require each locator to bind its corresponding
entry exactly; no provider-specific URL enters neutral source records.

## Archived Resolution Contract

After locator retention, the archive may add the narrow family-specific query:

```python
load_latest_horse_profile_history_supplied_response(
    *,
    canonical_horse_history_url: str,
    observed_at_not_after: datetime,
) -> JRASuppliedOfficialResponse | None
```

It accepts only a canonical accessU URL, validates it with
`canonicalize_jra_official_capture_url(page_kind=HORSE_PROFILE_HISTORY, ...)`, and
requires the parsed URL horse identity to be the locator horse identity at the caller
binding layer. It queries only schema-v1 `HORSE_PROFILE_HISTORY` captures for that
exact canonical URL whose actual `observed_at <= observed_at_not_after`; accessS,
accessD, and accessO cannot match.

The deterministic policy is `latest causally eligible observed_at`. The repository must
order by normalized UTC observation time descending and inspect every row at the latest
time. The v1 evidence uniqueness constraint already prevents byte-identical duplicates
at one URL/SHA/time. Two distinct reconstructed captures at the same latest observation
time are conflicting evidence and raise the existing `RepositoryDataIntegrityError`,
not an arbitrary tie choice. Corrupt requested-family rows also raise that integrity
error. No qualifying row returns `None`; the resolver turns only that absence into its
dedicated unavailable failure.

The existing capture table can answer this query by canonical URL and observed time.
No schema or migration change is required for correctness, and no new index is required
by this contract; an implementation must not add a speculative schema/index change.

```text
ARCHIVE_SCHEMA_CHANGE_REQUIRED: NO
ARCHIVE_INDEX_CHANGE_REQUIRED: NO
MULTIPLE_CAPTURE_POLICY_READY: YES
NO_ELIGIBLE_CAPTURE_POLICY_READY: YES
```

## Pure Resolver Boundary

The archive remains the only repository/SQLite owner. The pure injected boundary is:

```python
class JRATargetHorseHistoryResponseProvider(Protocol):
    def __call__(
        self,
        *,
        locator: JRATargetHorseHistoryLocator,
        observed_at_not_after: datetime,
    ) -> JRASuppliedOfficialResponse | None: ...

class JRATargetHorseHistoryResolutionError(ValueError): ...
class JRATargetHorseHistoryResolutionValidationError(
    JRATargetHorseHistoryResolutionError,
): ...
class JRATargetHorseHistoryResolutionUnavailableError(
    JRATargetHorseHistoryResolutionError,
): ...

def resolve_jra_target_horse_history_response(
    *,
    target_track_record: HistoricalInputSourceRecord,
    target_entry_record: HistoricalInputSourceRecord,
    locator: JRATargetHorseHistoryLocator,
    horse_history_response_provider: JRATargetHorseHistoryResponseProvider,
) -> JRASuppliedOfficialResponse: ...
```

It validates exact target lineage and locator binding, invokes the injected provider
once with the target scheduled start as the exclusive upper bound, then requires an
exact supplied response with canonical accessU URL whose parsed horse identity equals
the target entry horse identity and whose actual `observed_at <= scheduled_start_at`.
`None` raises `JRATargetHorseHistoryResolutionUnavailableError`. Malformed locator,
target, response, or late response raises the resolution validation error. Provider
exceptions, including repository integrity failures, propagate unchanged. There is no
broad exception catch, network, clock, archive access, or fallback in the pure resolver.

The repository method may serve as the provider through a thin adapter, but the existing
historical collector remains unchanged and still consumes the resolved exact response.
No package-root export is required.

## Causality and Flow

```text
trusted accessD target evidence                    [formal]
-> target source normalization + retained locator  [c4 prerequisite]
-> injected/archive accessU resolution             [c4]
-> complete accessU discovery                       [formal]
-> accessS/accessO historical collection            [formal]
-> target + historical source-record union          [later orchestration]
-> historical input snapshot builder                [formal]
```

The target accessD `observed_at` remains preserved by target normalization. The resolved
accessU response retains its actual `observed_at` and must be no later than the target
scheduled start. No timestamp is replaced or backdated; no `available_at` is invented.
The later snapshot boundary remains sole owner of
`observed_at <= captured_at <= information_cutoff <= scheduled_start_at`.

## Required Next Implementation Tests

The next phase must use no real capture and cover: exact locator public surface,
immutability, canonical URL/horse/race/entry binding, one locator per ordered target
entry, no neutral-record URL leakage, accessD row-anchor retention, no URL synthesis,
provider call count one, canonical accessU-only response binding, wrong horse/family,
late response, no result, provider exception propagation, and no raw accessD reparse.
Repository tests must cover exact URL/cutoff lookup, latest eligible selection, no
future fallback, same-time conflicting SHA integrity failure, corrupt requested-family
row failure, accessS/accessD/accessO exclusion, and no-result `None`. Existing target
normalizer, discovery, collector, capture/archive, and snapshot regressions must run.

## Readiness and Next Phase

```text
ACCESSU_IDENTITY_LOOKUP_FROM_ARCHIVE_READY: NO
ACCESSU_URL_SYNTHESIS_ALLOWED: NO
EXACT_ACCESSU_LOCATOR_CURRENTLY_RETAINED: NO
TARGET_DOMAIN_EXTENSION_REQUIRED: YES
ARCHIVE_SCHEMA_CHANGE_REQUIRED: NO
ARCHIVE_INDEX_CHANGE_REQUIRED: NO
MULTIPLE_CAPTURE_POLICY_READY: YES
NO_ELIGIBLE_CAPTURE_POLICY_READY: YES
RAW_ACCESSD_REPARSE_ALLOWED: NO
CAUSALITY_POLICY_READY: YES
IMPLEMENTATION_READY: YES_AFTER_LOCATOR_RETENTION
BLOCKERS: formal target collection currently discards exact row-local accessU URL
REAL_TRUSTED_CAPTURE_REQUIRED: NO
```

Recommended next phase: `4C-2d3b1i6d1d5f1c4a` — implement JRA target accessU locator
retention and archived history-response resolution.

Proposed allowed files are limited to the target source module/tests; a new pure JRA
target horse-history resolution module/tests; JRA capture archive Protocol and SQLite
repository/tests; and these phase docs. No migration, live capture, collector, neutral
source/snapshot, package-root, or bridge change is authorized.

## Stop Condition

Stop after the two documentation files are committed and pushed for independent
architecture review.
