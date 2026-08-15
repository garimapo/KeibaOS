# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6d1d5e` — JRA historical source collection PREPARE.

Formal base: `a44df34017269b1b0a4e462b3bb775f7059681b7`.

Review branch: `review/4c-2d3b1i6d1d5e-jra-history-collection-prepare`.

## Objective

Freeze the smallest pure, injected, all-or-nothing collector that turns one validated JRA target track/entry and
trusted supplied official evidence into complete provider-neutral past-history source records for that one entry. The
collector owns orchestration, discovery event ordering, exact response pairing, in-call reuse, all-or-nothing return,
and final neutral validation. It owns no HTTP, archive/repository, SQLite, clock, pacing, archive path, or provider
HTML parsing already owned by the formal components.

## Candidate Public API

Subject to the discovery-to-absence handoff blocker below, the intended API is:

```python
collect_jra_historical_input_source_records(
    *,
    target_track_record: HistoricalInputSourceRecord,
    target_entry_record: HistoricalInputSourceRecord,
    horse_history_response: JRASuppliedOfficialResponse,
    result_response_provider: JRAHistoricalRaceResultResponseProvider,
    final_odds_response_provider: JRAHistoricalFinalWinOddsResponseProvider,
) -> JRAHistoricalSourceCollection
```

Proposed module public names are exactly:

```text
JRAHistoricalRaceResultResponseProvider
JRAHistoricalFinalWinOddsResponseProvider
JRAHistoricalSourceCollection
JRAHistoricalSourceCollectionError
JRAHistoricalSourceCollectionValidationError
JRAHistoricalSourceCollectionUnsupportedError
collect_jra_historical_input_source_records
```

No package-root export. The immutable/slotted collection contains exactly:

```text
target_external_race_id: str
target_external_entry_id: str
source_records: tuple[HistoricalInputSourceRecord, ...]
```

It accepts only exact source-record types. Every record must retain the target race and entry identities and be either
`past_race` or `past_race_absence`. It must contain either one absence and no past races, or one-or-more past races
and no absence. The tuple order is deterministic.

## Injected Provider Contracts

The result provider is keyed by stronger formal race identity and bound discovery URL, not URL text alone:

```python
class JRAHistoricalRaceResultResponseProvider(Protocol):
    def __call__(
        self,
        *,
        race_identity: JRAExternalRaceIdentity,
        canonical_race_result_url: str,
    ) -> JRASuppliedOfficialResponse: ...
```

The collector requires an exact response object whose canonical response URL parses to, and equals, both supplied
race identity and the discovery event's canonical accessS URL. A missing result, wrong type, URL/identity mismatch,
or malformed provider response is a collection validation error.

For each validated accessS response, the formal d1d5c2 extractor creates the sole final-odds request locator. The
final-odds provider is keyed by that opaque formal locator, including its request identity:

```python
class JRAHistoricalFinalWinOddsResponseProvider(Protocol):
    def __call__(
        self,
        *,
        request_locator: JRAOfficialFinalWinOddsRequestLocator,
    ) -> JRAFinalWinOddsSuppliedOfficialResponse: ...
```

It must return the exact supplied final-odds response whose locator equals the extracted locator. Raw HTML, strings,
caller-made CNAMEs, response substitution, fallback/latest/nearest lookup, and duplicate/conflicting responses fail
closed. The formal past-race normalizer remains the owner of accessS/accessO pair parsing and evidence construction.

## Intended Nonzero Flow

1. Run formal accessU discovery exactly once.
2. Preserve its newest-to-oldest event order.
3. Ignore `PROVEN_NON_START` only as an output slot; it remains represented by discovery's completeness proof.
4. For each `JRA_ACTUAL_START`, obtain one exact accessS response through the result provider; validate its binding to
   the discovery event; extract its formal final-odds locator; obtain one exact accessO response through the odds
   provider; and call `normalize_jra_historical_past_race_source_record(...)`.
5. Run `validate_historical_input_source_record_set(records=...)` before returning the immutable collection.

The output order is newest actual prior start to oldest actual prior start. It does not introduce a race-count cap:
source acquisition remains `ALL_CAUSALLY_AVAILABLE_ACTUAL_PRIOR_STARTS`.

Within one call, accessS requests are deduplicated by `JRAExternalRaceIdentity`; final-odds requests are deduplicated
by locator `request_identity_sha256`. The supplied response object is reused only for the same validated identity in
that call. Discovery already rejects duplicate JRA event identities and URLs; collector deduplication is defensive and
does not define cross-run cache/archive policy.

## Event and Mixed-Provider Policy

```text
PROVEN_NON_START
  No past_race output; consumes no actual-start response; remains completeness evidence only.

JRA_ACTUAL_START
  Requires one fully bound accessS/accessO pair and exactly one normalized past_race record.

NON_JRA_ACTUAL_START
  Fail closed. It cannot be silently skipped or represented by this JRA-only collector.

UNSUPPORTED_ACTUAL_START
  Fail closed. It cannot be skipped or normalized best-effort.
```

Thus `JRA_ONLY_COLLECTION_READY = YES` only for complete discovery sequences containing JRA actual starts and/or
proven non-starts, once the zero-history handoff is resolved. `COMPLETE_MIXED_HISTORY_COLLECTION_READY = NO`:
historical NAR/local/overseas actual starts require an approved cross-provider collector and an official identity path.
`NAR_LINEAGE_TO_JRA_HORSE_ID_LINK = NOT_PROVEN` remains unchanged.

## Zero-Actual-Start Handoff Blocker

Formal d1d5d2 intentionally owns absence projection by calling formal discovery itself. The collector requirement
demands discovery exactly once, including the zero-actual-start branch. Calling d1d5b2's public
`normalize_jra_historical_past_race_absence_source_record(...)` after the collector's discovery would run discovery a
second time; recreating its absence record directly would duplicate a formal boundary. Neither is acceptable.

Therefore an implementation cannot satisfy both frozen requirements without an approved discovery-to-absence handoff
contract. The smallest needed predecessor is a narrowly scoped design/implementation decision that exposes a formal
absence projection from an already-validated exact `JRAHistoricalPastRaceDiscovery` plus the original supplied
accessU response, while preserving the existing d1d5d2 public API and its discovery-owned validation for direct
callers. The collector must not import or depend on a private absence helper.

Until that handoff exists, `JRA_ONLY_COLLECTION_READY = NO` for implementation despite the nonzero JRA event flow
being otherwise fully specified. No partial `JRAHistoricalSourceCollection` may be returned in any failure branch.

## Causality, Validation, and Compatibility

The collector introduces no clock or timestamp transformation. It preserves supplied evidence timestamps and relies
on formal discovery/normalizer/domain validation plus the existing snapshot builder's causal eligibility boundary.
It never backdates live evidence. A failure after any earlier provider result yields no partial returned tuple; an
archive may independently retain captured evidence, but archive state is outside collector ownership.

Returned records must be valid inputs for the existing snapshot builder after target track/entry/jockey/odds records
are combined. This phase does not build snapshots. Existing source and snapshot schemas already admit both the
past-race and past-race-absence alternatives; no source schema, snapshot schema, migration, repository, or capture
change is required.

## Recommended Next Phase

Recommended next phase: `4C-2d3b1i6d1d5e0` — JRA discovery-to-absence projection handoff PREPARE. It must resolve
the exact public/internal contract needed to preserve both d1d5d2 direct-call semantics and the collector's required
single discovery call. Do not implement the collector until that review has approved the handoff.

Provisional collector implementation scope after the blocker is resolved:

```text
scripts/simulation/jra_historical_source_collection.py
tests/test_jra_historical_source_collection.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Allowed Files

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Stop Condition

Create and push exactly one documentation review commit: `docs: prepare JRA historical source collection`. Do not
implement collection, tests, capture, archive, migrations, database work, real acquisition, formal integration,
mixed-provider bridge, or Predictor work. Stop for independent architecture review.
