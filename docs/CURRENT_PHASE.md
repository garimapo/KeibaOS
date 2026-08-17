# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase

`4C-2d3b1i6d1d5f1c4b` — JRA historical accessS/accessO causal archive resolution.

Formal base: `8660f9f8ffdea03b0f7badc31429d8b572e7cfa0`.

Review branch: `review/4c-2d3b1i6d1d5f1c4b-jra-historical-causal-resolution-prepare`.

## Allowed Files

This PREPARE changes only:

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Frozen Design

### Explicit causal bound

The historical collector must receive exact timezone-aware
`observed_at_not_after: datetime`. It compares in UTC by actual instant, treats the
upper bound as inclusive, and rejects a bound after the target scheduled start. It must
not substitute scheduled start for the caller value or rewrite any observation time.

Before discovery and before either historical provider is called, the collector validates
that the supplied accessU `horse_history_response` is exact and has
`observed_at <= observed_at_not_after`. Discovery remains exactly once and remains the
sole owner of accessU completeness. The later race-level orchestration, not this
collector, derives the effective bound compatible with `captured_at` and
`information_cutoff` before snapshot construction.

### Collector API and errors

The implementation changes the existing public collector, not a duplicate adapter:

```python
collect_jra_historical_input_source_records(
    *,
    target_track_record: HistoricalInputSourceRecord,
    target_entry_record: HistoricalInputSourceRecord,
    horse_history_response: JRASuppliedOfficialResponse,
    observed_at_not_after: datetime,
    race_result_response_provider: JRAHistoricalRaceResultResponseProvider,
    final_win_odds_response_provider: JRAHistoricalFinalWinOddsResponseProvider,
) -> JRAHistoricalSourceCollection
```

```python
class JRAHistoricalRaceResultResponseProvider(Protocol):
    def __call__(
        self,
        *,
        race_reference: JRAHistoricalPastRaceReference,
        observed_at_not_after: datetime,
    ) -> JRASuppliedOfficialResponse | None: ...

class JRAHistoricalFinalWinOddsResponseProvider(Protocol):
    def __call__(
        self,
        *,
        request_locator: JRAOfficialFinalWinOddsRequestLocator,
        observed_at_not_after: datetime,
    ) -> JRAFinalWinOddsSuppliedOfficialResponse | None: ...
```

Add public module-local
`JRAHistoricalSourceCollectionUnavailableError(JRAHistoricalSourceCollectionError)`.
`None` from either provider raises this distinct unavailable error. Repository integrity
and other provider exceptions propagate unchanged; they are never converted to
unavailable. Validation and unsupported translations otherwise remain as currently
frozen.

Every returned accessS and accessO response must be at or before the exact explicit
bound as well as the outer scheduled-start maximum. The accessO locator remains extracted
only from its selected exact accessS response. No result URL, accessO CNAME, or opaque
request material is synthesized.

### Determinism and event policy

All provider calls in one collection receive the same caller-supplied bound. Preserve
one discovery call; unsupported mixed history rejection before providers; transfer row
handling; zero-history absence projection; newest-to-oldest complete event order; no
event skip, partial return, or history cap. Cache accessS by the exact discovered race
identity plus canonical result URL, and cache accessO by exact formal request identity
(with cached response/locator revalidation). A cache hit is still bound-validated.

### Family-specific repository lookups

Add concrete methods only to `SQLiteJRAOfficialResponseCaptureRepository`; the existing
exact-evidence archive Protocol/loaders stay unchanged.

```python
load_latest_race_result_supplied_response(
    *,
    canonical_race_result_url: str,
    observed_at_not_after: datetime,
) -> JRASuppliedOfficialResponse | None

load_latest_final_win_odds_supplied_response(
    *,
    request_locator: JRAOfficialFinalWinOddsRequestLocator,
    observed_at_not_after: datetime,
) -> JRAFinalWinOddsSuppliedOfficialResponse | None
```

Both require exact canonical input, an inclusive aware cutoff, and use no prefix, display
name, CNAME synthesis, or cross-family fallback. The accessS lookup selects only
schema-v1 `RACE_RESULT` rows at the exact canonical URL. The accessO lookup selects only
schema-v2 `FINAL_WIN_ODDS` rows at the exact formal endpoint/request-identity lineage;
after reconstruction its locator must equal the requested locator exactly.

For either lookup, the unique greatest eligible `observed_at` wins. At that timestamp,
multiple distinct rows or any corrupt selected requested-family row/body/domain state
raise `RepositoryDataIntegrityError`; no qualifying row returns `None`. Query and
reconstruction must retain corruption detection rather than filtering a corrupt row into
an apparent no-result. Existing exact-evidence loaders remain unchanged.

Existing table columns persist page kind, schema version, URL, request identity, raw
CNAME, and observation time for these queries. Therefore
`ARCHIVE_SCHEMA_CHANGE_REQUIRED = NO` and `ARCHIVE_INDEX_CHANGE_REQUIRED = NO`.

### Causality and out-of-scope work

No live fallback, current-response substitution, timestamp backdating, synthetic
result/final-odds response, fake zero-history result, schema/index migration, or raw
accessD reparse is allowed. Race-level target/historical union and snapshot assembly
remain out of scope.

## Implementation Files

If approved, the narrow implementation may change only:

```text
scripts/simulation/jra_historical_input_source_collection.py
scripts/simulation/repositories/sqlite_jra_official_response_capture_repository.py
tests/test_jra_historical_input_source_collection.py
tests/test_sqlite_jra_official_response_capture_repository.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

No package-root, capture-domain, schema, index, migration, live-capture, target-source,
snapshot, Predictor, or bridge file is needed.

## Required Future Tests

- accessS and accessO latest-before-bound repository lookups: canonical input, inclusive
  equality, older eligible selection, no-result, family/url/request exclusion, same-time
  conflict, and selected body/domain/request metadata corruption;
- explicit collector bound, accessU/accessS/accessO bound checks, exact provider argument
  identity, unavailable result, unchanged provider-integrity propagation, cache counts,
  all-or-nothing behavior, and unsupported history before acquisition;
- exact public signatures/error surface, no package-root export, no new forbidden
  dependencies, no schema/index changes, and full regression compatibility.

## Readiness

```text
ACCESSS_LATEST_ARCHIVE_LOOKUP_READY: YES
ACCESSO_LATEST_ARCHIVE_LOOKUP_READY: YES
EXPLICIT_CAUSAL_BOUND_REQUIRED: YES
COLLECTOR_API_CHANGE_REQUIRED: YES
PROVIDER_PROTOCOL_CHANGE_REQUIRED: YES
HORSE_HISTORY_BOUND_RECHECK_REQUIRED: YES
ACCESSS_BOUND_RECHECK_REQUIRED: YES
ACCESSO_BOUND_RECHECK_REQUIRED: YES
DEDICATED_UNAVAILABLE_ERROR_REQUIRED: YES
ARCHIVE_SCHEMA_CHANGE_REQUIRED: NO
ARCHIVE_INDEX_CHANGE_REQUIRED: NO
SAME_TIME_CONFLICT_POLICY_READY: YES
NO_ELIGIBLE_CAPTURE_POLICY_READY: YES
LIVE_FALLBACK_ALLOWED: NO
RACE_LEVEL_ASSEMBLY_READY_AFTER_THIS: NO
IMPLEMENTATION_READY: YES
BLOCKERS: NONE
REAL_TRUSTED_CAPTURE_REQUIRED: NO
```

## Stop Condition

Stop after the documentation-only review commit is pushed for independent architecture
review.
