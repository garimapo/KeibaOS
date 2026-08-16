# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6d1d5e` — JRA historical source collection PREPARE v2.

Formal base: `c8008cdc15903b305219066c3b10b35e1255767f`.

Review branch: `review/4c-2d3b1i6d1d5e-jra-history-collection-prepare-v2`.

## Exact Public API

The next implementation introduces one pure injected module:

```text
scripts/simulation/jra_historical_input_source_collection.py
```

Its public surface is exactly:

```text
JRAHistoricalRaceResultResponseProvider
JRAHistoricalFinalWinOddsResponseProvider
JRAHistoricalSourceCollection
JRAHistoricalSourceCollectionError
JRAHistoricalSourceCollectionValidationError
JRAHistoricalSourceCollectionUnsupportedError
collect_jra_historical_input_source_records
```

There is no package-root export.

```python
class JRAHistoricalRaceResultResponseProvider(Protocol):
    def __call__(
        self,
        *,
        race_reference: JRAHistoricalPastRaceReference,
    ) -> JRASuppliedOfficialResponse: ...


class JRAHistoricalFinalWinOddsResponseProvider(Protocol):
    def __call__(
        self,
        *,
        request_locator: JRAOfficialFinalWinOddsRequestLocator,
    ) -> JRAFinalWinOddsSuppliedOfficialResponse: ...


def collect_jra_historical_input_source_records(
    *,
    target_track_record: HistoricalInputSourceRecord,
    target_entry_record: HistoricalInputSourceRecord,
    horse_history_response: JRASuppliedOfficialResponse,
    race_result_response_provider: JRAHistoricalRaceResultResponseProvider,
    final_win_odds_response_provider: JRAHistoricalFinalWinOddsResponseProvider,
) -> JRAHistoricalSourceCollection: ...
```

The result is a frozen, slotted `JRAHistoricalSourceCollection` with exactly:

```text
target_external_race_id: str
target_external_entry_id: str
source_records: tuple[HistoricalInputSourceRecord, ...]
```

Its direct constructor validates target JRA lineage using existing formal identity APIs only:

1. `parse_jra_external_race_id(target_external_race_id)` must succeed;
2. `target_external_entry_id` must use that exact parsed race's entry prefix;
3. the remaining horse-number suffix must be canonical positive decimal material; and
4. `build_jra_external_entry_id(race_identity=parsed_race, horse_no=suffix)` must exactly equal
   `target_external_entry_id`.

It creates no second JRA grammar or public entry parser. It accepts exact source-record values only. Every record must
be target-bound to these validated exact external IDs, have
`organization="JRA"` and `source_system="jra_official"`, and have record kind `past_race` or
`past_race_absence`. The tuple is nonempty and is exactly one of: one absence and no past races; or one-or-more past
races and no absence. Its constructor performs only this collection-envelope validation; the collector performs the
one required existing neutral `validate_historical_input_source_record_set(records=...)` call before construction. It
does not reproduce that validator.

## One Discovery, Complete Event Sequence

`discover_jra_historical_past_race_history(...)` is called exactly once with the original target records and exact
accessU supplied response. Its returned formal discovery is the sole event sequence; the collector does not decode or
parse accessU HTML, recalculate aggregate counts, rediscover history, or alter event order.

```text
DISCOVERY_CALL_COUNT = 1
SOURCE_ACQUISITION_HISTORY_POLICY = ALL_CAUSALLY_AVAILABLE_ACTUAL_PRIOR_STARTS
PARTIAL_COLLECTION_RETURN = FORBIDDEN
```

The collector reads the already-validated target scheduled start only after formal discovery succeeds, to enforce the
additional accessS/accessO observation checks below. It does not add an information-cutoff or captured-at input.

## Event Policies

The collector examines the complete formal event tuple before obtaining result or odds evidence.

| Event kind | Frozen collector action |
| --- | --- |
| `PROVEN_NON_START` | Emit no record and consume no actual-start slot. |
| `JRA_ACTUAL_START` | Only allowed actual-start kind. Obtain and bind exact accessS and accessO responses, then call the existing JRA past-race normalizer. |
| `NON_JRA_ACTUAL_START` | Raise `JRAHistoricalSourceCollectionUnsupportedError` for the entire call before provider use; never skip it to continue JRA collection. |
| `UNSUPPORTED_ACTUAL_START` | Raise `JRAHistoricalSourceCollectionUnsupportedError` for the entire call before provider use; never skip it. |

For zero actual starts, including complete transfer-only history, call only the existing public
`project_jra_historical_past_race_absence_source_record(discovery=..., horse_history_response=...)`. It performs no
second discovery or accessU parsing. The returned collection contains its one absence record; neither response provider
is called.

## JRA Actual-Start Flow and Provider Binding

For histories made only of `JRA_ACTUAL_START` and `PROVEN_NON_START`, process formal JRA events in their displayed
discovery order, newest-to-oldest. For each JRA reference:

1. Call `race_result_response_provider(race_reference=reference)` once per unique
   `reference.race_identity.external_race_id`.
2. Require an exact `JRASuppliedOfficialResponse`, exact canonical response URL equal to
   `reference.canonical_race_result_url`, and `parse_jra_result_url_identity(response.response_url)` equal to
   `reference.race_identity`.
3. Call the existing public `extract_jra_final_win_odds_request_locator(race_result_response=response)`. The collector
   delegates that already-formal accessS navigation parse; it does not parse raw HTML or synthesize CNAME material.
4. Call `final_win_odds_response_provider(request_locator=locator)` once per unique exact
   `locator.request_identity_sha256`.
5. Require an exact `JRAFinalWinOddsSuppliedOfficialResponse` whose exact `request_locator` equals the extracted
   locator. Consequently its formal race identity equals the discovery reference; no URL-only/fallback final-odds
   lookup is allowed.
6. Call the existing `normalize_jra_historical_past_race_source_record(...)` with the original target records and this
   exact accessS/accessO pair.

`IN_CALL_ACCESS_S_DEDUP` is a per-call cache keyed by canonical JRA external race ID. `IN_CALL_FINAL_ODDS_DEDUP` is a
per-call cache keyed by exact final-odds request-identity SHA-256. A cache hit reuses the already-bound supplied object;
there is no cross-call cache, archive lookup, “latest”, nearest, or alternate-evidence policy. Formal discovery already
rejects duplicated JRA race identities and result URLs; conflicting metadata for a repeated cache key is a validation
failure rather than permission to select one response.

`RETURN_ORDER` is the discovery's retained newest-to-oldest JRA actual-start order. `PROVEN_NON_START` has no output
slot. The collector does not impose a source-history depth cap; model-window truncation remains downstream policy.

## Causality and Failure Boundary

The accessU response remains governed by formal discovery, including its existing
`horse_history_response.observed_at <= target scheduled_start_at` proof. Before normalizing each JRA event, the
collector additionally requires both injected response observations to be no later than that same scheduled start:

```text
race_result_response.observed_at <= target scheduled_start_at
final_win_odds_response.observed_at <= target scheduled_start_at
```

Any late, missing, wrong-type, malformed, wrong-URL, wrong-race, wrong-locator, locator-extraction, or normalizer
failure aborts the entire call with no returned collection. Timestamps are preserved exactly and never replaced or
backdated. The exact upstream exception translation table is:

| Upstream failure | Collection failure |
| --- | --- |
| discovery `ValidationError` | collection `ValidationError` |
| discovery `UnsupportedError` | collection `UnsupportedError` |
| locator-extraction validation | collection `ValidationError` |
| past-race normalizer validation | collection `ValidationError` |
| past-race normalizer unsupported | collection `UnsupportedError` |
| absence-projection validation | collection `ValidationError` |
| neutral source validation or conflict | collection `ValidationError` |
| provider-raised exception | propagate unchanged |

No broad `Exception` or `BaseException` catch is allowed. The existing snapshot boundary remains the sole owner of
`observed_at <= captured_at <= information_cutoff <= scheduled_start_at` eligibility.

`FINAL_NEUTRAL_VALIDATION` is exactly one final call to the existing
`validate_historical_input_source_record_set(records=source_records)` before constructing the collection result. It is
not a snapshot build and does not validate unrelated track, entry, jockey, or target-odds records.

## Readiness and Boundaries

```text
JRA_ONLY_COLLECTION_READY = YES
  only for complete discovery histories composed exclusively of
  JRA_ACTUAL_START and PROVEN_NON_START.

COMPLETE_MIXED_HISTORY_COLLECTION_READY = NO
NAR_LINEAGE_TO_JRA_HORSE_ID_LINK = NOT_PROVEN
SOURCE_SCHEMA_CHANGE_REQUIRED = NO
SNAPSHOT_SCHEMA_CHANGE_REQUIRED = NO
MIGRATION_REQUIRED = NO
```

There is no approved provider-neutral representation for a discovered NAR/non-JRA or unsupported actual start in a
JRA-only collection. This is an intentional fail-closed blocker, not a reason to omit that history. The collector owns
only injected orchestration, exact evidence binding, in-call reuse, deterministic ordering, all-or-nothing completion,
and final neutral validation. It owns no HTTP/live capture, archive/repository/SQLite/database, current clock,
sleep/retry, raw accessU parsing, snapshot construction, Predictor, NAR↔JRA bridge, or real acquisition.

## Recommended Next Phase

`4C-2d3b1i6d1d5e1 — JRA historical source collection IMPLEMENTATION`

Allowed files:

```text
scripts/simulation/jra_historical_input_source_collection.py
tests/test_jra_historical_input_source_collection.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

Required tests include exact public surface/signature and frozen/slotted result domain; normal direct-constructor
rejection of malformed/non-JRA race IDs, an entry from another race, `entry:07`, `entry:0`, `entry:+7`, an extra entry
suffix, and target/record ID disagreement; one discovery call; empty and transfer-only projection without provider
calls; multi-start newest-to-oldest output; exact event/result URL/race binding; extractor-derived locator and exact
final-odds locator binding; per-call result/request dedup; the exact upstream exception-translation table; late/
missing/wrong-type/wrong-identity evidence rejection; non-JRA and unsupported whole-call rejection before provider use;
no partial return after a later event fails; final neutral-validation invocation and target-bound result invariants; no
source-history cap; purity/no package export; and regression coverage for JRA discovery, projection, normalizer,
locator, capture/archive/live, NAR, and neutral source/snapshot boundaries.

## Allowed Files

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Stop Condition

Commit and push this documentation-only PREPARE review. Do not implement the collector, alter tests or production,
perform real capture, create a bridge, integrate formal, or begin another phase. Stop for independent architecture
review.
