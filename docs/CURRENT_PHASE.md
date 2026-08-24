# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase

`4C-2d3b1i6d1d5f1c4d` — JRA race-level historical replay orchestration.

Formal base: `f07a91fb55248d562202513f7b70c528528e7143`.

Formally integrated d0 prerequisite:
`f07a91fb55248d562202513f7b70c528528e7143`.

Historical architecture reference only:
`509e48fdadd74064a6ccaddcc60fab04ef98d9b1`.

Review branch:
`review/4c-2d3b1i6d1d5f1c4d-jra-race-level-historical-replay-final-prepare`.

This PREPARE is documentation only. It adds no production code, tests, migration,
database change, HTTP, archive mutation, snapshot persistence, or trusted capture.

## Responsibility and Final Input Boundary

C4d is one pure, read-only, one-race orchestrator over already-formal evidence and
normalization boundaries. It consumes one exact `JRARaceReplaySeed` plus injected
read-only evidence providers. The seed is the sole caller-owned source of dataset,
internal and external race identity, exact v4 and v3 capture provenance, replay times,
ordered target-entry identities, and external-to-internal entry mapping.

The former decomposed candidate API is rejected. A caller cannot separately supply
`dataset_id`, `internal_race_id`, `external_race_id`, entry mappings, `captured_at`,
`information_cutoff`, v4 capture ID, v3 capture ID, v3 response digest, or target-card
URL. Accepting those values independently would permit facts that are individually
valid but contradict the immutable seed.

The final public module is:

```text
scripts/simulation/jra_race_historical_replay.py
```

It has no package-root export and owns exactly these public names:

```python
class JRARaceHistoricalReplayError(ValueError): ...
class JRARaceHistoricalReplayValidationError(JRARaceHistoricalReplayError): ...
class JRARaceHistoricalReplayUnavailableError(JRARaceHistoricalReplayError): ...
class JRARaceHistoricalReplayUnsupportedError(JRARaceHistoricalReplayError): ...

@dataclass(frozen=True, slots=True)
class JRARaceHistoricalReplayResult:
    seed: JRARaceReplaySeed
    snapshot: HistoricalInputSnapshot

def build_jra_race_historical_replay(
    *,
    seed: JRARaceReplaySeed,
    target_race_selection_capture_provider:
        JRATargetRaceSelectionCaptureProvider,
    target_race_card_capture_by_id_provider:
        _JRATargetRaceCardCaptureByIdProvider,
    horse_history_response_provider:
        JRATargetHorseHistoryResponseProvider,
    race_result_response_provider:
        JRAHistoricalRaceResultResponseProvider,
    final_win_odds_response_provider:
        JRAHistoricalFinalWinOddsResponseProvider,
) -> JRARaceHistoricalReplayResult: ...
```

All five providers must be callable and the seed must be exact
`JRARaceReplaySeed`. Validation occurs before provider use. No seed repository,
connection, HTTP client, archive writer, clock, filesystem path, current date, or
snapshot repository belongs in the API.

The result retains the exact immutable seed object rather than duplicating its fields.
Its constructor requires exact seed and snapshot types and requires the snapshot to
agree with the seed's dataset, internal race, external JRA race, captured instant,
information cutoff, ordered external entry identities, and seed-derived internal entry
mapping. It contains no raw response bytes.

## Exact Seed-Bound V3 Adapter

The existing c4c `JRATargetRaceCardCaptureProvider` intentionally means a latest
eligible exact-URL lookup. It is not authoritative for replaying an existing seed.
C4d therefore defines a private protocol:

```python
class _JRATargetRaceCardCaptureByIdProvider(Protocol):
    def __call__(
        self,
        *,
        capture_id: str,
    ) -> JRAOfficialTargetRaceCardResponseCapture | None: ...
```

The protocol and adapter are private to the c4d module. The SQLite archive's existing
`load_target_race_card_capture(*, capture_id=...)` can satisfy the protocol without any
repository change.

The private seed-bound adapter satisfies formal c4c's existing locator-and-bound
provider protocol. On its sole call it requires:

```text
locator.external_race_id == seed.external_race_id
locator.canonical_target_race_card_url
    == seed.canonical_target_race_card_url
observed_at_not_after == seed.captured_at
```

It then calls the exact-by-ID provider exactly once with only
`seed.target_race_card_capture_id`. `None` remains missing exact evidence. A returned
value must be exact `JRAOfficialTargetRaceCardResponseCapture` and must satisfy:

```text
capture.capture_id == seed.target_race_card_capture_id
capture.response_sha256 == seed.target_race_card_response_sha256
capture.canonical_source_url == seed.canonical_target_race_card_url
capture.observed_at <= seed.captured_at
parse_jra_race_card_url_identity(capture.canonical_source_url)
    == parse_jra_external_race_id(seed.external_race_id)
```

Wrong type, ID, digest, URL, race/site/tail lineage, or causal time fails closed. The
adapter never calls the generic latest-v3 lookup. Adding another eligible capture for
the URL cannot change replay of an existing seed.

## C4c Reuse and Seed Provenance Equality

C4d calls formal `resolve_jra_target_race_card_response(...)` exactly once with:

```text
external_race_id = seed.external_race_id
target_race_selection_capture_id = seed.target_race_selection_capture_id
captured_at = seed.captured_at
target_race_selection_capture_provider = injected exact-v4 provider
target_race_card_capture_provider = private seed-bound exact-v3 adapter
```

C4d does not modify c4c or duplicate navigation discovery. After resolution it requires
exact equality of all retained provenance:

```text
resolution.target_race_selection_capture_id
    == seed.target_race_selection_capture_id
resolution.target_race_card_capture_id
    == seed.target_race_card_capture_id
resolution.target_race_card_response_sha256
    == seed.target_race_card_response_sha256
resolution.discovery.locator.canonical_target_race_card_url
    == seed.canonical_target_race_card_url
resolution.response.response_url
    == seed.canonical_target_race_card_url
resolution.captured_at == seed.captured_at
```

No latest v3, URL-only latest v3, or race-ID-only v3 lookup is allowed in c4d.

## Target Normalization and Seed Entry Equality

Only `c4c_resolution.response` is passed to the formal
`normalize_jra_target_race_input_source_records(...)` boundary. C4d does not load
neutral target records from another store and does not independently reparse accessD
HTML.

The normalized target track must identify `seed.external_race_id`. The normalized
target entries and aligned horse-history locators must be exactly one-to-one with
`seed.entries`. In contiguous ascending seed order, each position requires:

```text
normalized external_entry_id == seed entry external_entry_id
normalized external_horse_id == seed entry external_horse_id
normalized horse_no == seed entry horse_no
locator external_race_id == seed.external_race_id
locator external_entry_id == seed entry external_entry_id
locator external_horse_id == seed entry external_horse_id
```

Missing, extra, reordered, duplicated, or contradictory entries fail before any
per-entry history resolution. No display name, internal-ID inference, legacy horse
lookup, or implicit horse-number mapping is permitted.

## Causality

The target scheduled start is read only from the exact normalized accessD track record.
C4d rechecks:

```text
seed.captured_at <= seed.information_cutoff <= target scheduled_start_at
```

`seed.captured_at` is the inclusive historical evidence observation bound for accessD,
accessU, accessS, and accessO. `seed.information_cutoff` is passed unchanged to the
snapshot builder and is not an acquisition bound. `stored_at` has no causal role: it is
not inspected, compared, selected, or used as a fallback/tie-break.

No timestamp is rewritten and no `available_at` is invented.

## Per-Entry Historical Collection

For every normalized target entry in exact ascending seed order, c4d uses the aligned
`JRATargetHorseHistoryLocator` already emitted by the target normalizer. It calls
`resolve_jra_target_horse_history_response(...)` with the exact target track, target
entry, aligned locator, injected accessU provider, and:

```text
observed_at_not_after = seed.captured_at
```

The resolved accessU response is then passed to exactly one call of
`collect_jra_historical_input_source_records(...)` for that entry with the injected
accessS and accessO providers and the same exact bound:

```text
observed_at_not_after = seed.captured_at
```

The existing resolver and collector remain sole owners of locator binding, complete
accessU discovery, event classification, accessS selection, accessS-to-accessO request
locator extraction, caching, formal absence, and past-race normalization. C4d adds no
history cap, skip, fallback, or duplicate implementation. Every entry must yield one
complete collection, including a formal absence collection where already proven by the
collector.

## Deterministic Source Union and Snapshot Mapping

C4d builds the source tuple only after every entry has completed successfully. Its exact
order is:

```text
all target_sources.source_records in their existing canonical order,
then for each seed entry in ascending seed order:
    that entry's complete historical collection source_records
    in their existing formal order
```

No provider or database return order can reorder the union. Duplicate source IDs,
incomplete entry coverage, foreign target lineage, or any partial union fails closed.
There is no partial result.

The snapshot entry mapping is constructed only from the seed:

```python
race_entry_id_by_external_entry_id = {
    entry.external_entry_id: entry.internal_race_entry_id
    for entry in seed.entries
}
```

Its keys must equal the normalized target entry IDs exactly. C4d does not query legacy
horses, a seed repository, or a snapshot repository and does not infer mapping through
horse numbers or names.

C4d calls `build_historical_input_snapshot(...)` exactly once with:

```text
dataset_id = seed.dataset_id
internal_race_id = seed.internal_race_id
captured_at = seed.captured_at
information_cutoff = seed.information_cutoff
source_records = complete deterministic union
race_entry_id_by_external_entry_id = exact seed-derived mapping
```

C4d returns the accepted snapshot but does not persist it.

## Error Taxonomy

The public error hierarchy is narrow:

- `JRARaceHistoricalReplayValidationError` covers non-exact inputs/providers, seed and
  c4c provenance contradiction, exact-v3 adapter contradiction, normalized target/seed
  contradiction, causal contradiction, neutral source-set conflict, snapshot assembly
  failure, and validation failures from formal target/c4c/accessU/collector boundaries.
- `JRARaceHistoricalReplayUnavailableError` covers genuine missing required exact v4,
  exact seed-bound v3, accessU, accessS, or accessO evidence reported by the existing
  unavailable boundaries.
- `JRARaceHistoricalReplayUnsupportedError` covers the existing target normalizer or
  historical collector reporting official evidence outside the supported envelope.
- Provider-owned errors, including `RepositoryDataIntegrityError`, propagate unchanged.

Corruption never becomes unavailable. Seed contradiction never becomes unavailable.
Missing exact v3 never invokes latest lookup. Unsupported history never becomes formal
absence unless the existing collector has independently proven absence. There is no
broad `Exception` or `BaseException` catch.

## Restart and Archive-Enrichment Invariant

The implementation test must materialize a seed against exact v3 capture A, cross a
simulated process boundary, add another causally eligible capture B for the same
canonical URL, and replay the original seed. The exact-by-ID provider must receive only
A's ID, the result must consume A, B must never be substituted, and the generic
latest-v3 method must never be invoked.

The same boundary must fail closed when A is missing or when the exact provider returns
the wrong capture, digest, URL, race/site/tail lineage, or an observation after
`seed.captured_at`.

## Future Test Intent

Offline deterministic tests must directly cover:

- exact public module surface, signatures, frozen/slotted result, and private adapter;
- rejection of non-exact seed and non-callable providers before provider calls;
- canonical one-entry replay and deterministic equivalent replay;
- multiple entries preserving exact seed order;
- exact v4 call and exact seed-bound v3 by-ID call counts;
- no race-ID/latest-v3/latest-v4/c0b3/live fallback path;
- restart/archive-enrichment stability with exact A retained over B;
- missing exact A and every wrong A identity/digest/URL/race/time case;
- exact c4c-to-seed provenance equality;
- target normalization receives only c4c's supplied response;
- missing, extra, reordered, wrong-horse, and wrong-horse-number target entries;
- exact aligned target horse-history locator equality;
- every accessU resolver and historical collector receives `seed.captured_at`;
- `information_cutoff` is never used as an evidence acquisition bound;
- `stored_at` is ignored causally;
- target records appear exactly once and first in canonical target order;
- per-entry historical records follow in seed order with complete coverage;
- duplicate source ID and partial-union rejection;
- seed-only snapshot entry mapping and no legacy/name/horse-number lookup;
- snapshot builder called exactly once with exact seed dataset/race/time/mapping;
- snapshot assembly error translation and provider integrity propagation;
- no snapshot persistence, database write, archive write, HTTP, current fallback, raw
  response duplication, broad catch, or package-root export.

Related verification must include formal d0 seed, c4c target resolution, target-source,
target-horse history, historical collector, source-record, and snapshot-builder tests,
followed by the full pytest suite, `git diff --check`, and static forbidden-dependency/
public-surface/call-count checks.

## Implementation Scope After Approval

Future implementation changes only:

```text
scripts/simulation/jra_race_historical_replay.py
tests/test_jra_race_historical_replay.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

No existing production module is expected to change. The exact-by-ID repository method,
c4c resolver, target normalizer, accessU resolver, historical collector, snapshot
builder, and seed domain are consumed through their current formal contracts.

Forbidden work includes repository/schema/migration changes, seed creation/update,
snapshot persistence, capture archive write, live HTTP/capture, current fallback,
target/accessU/accessS/accessO parser redesign, package-root exports, prediction,
betting, settlement, NAR, multi-race orchestration, and c4e or later work.

## Readiness Matrix

```text
D0_PREREQUISITE_STATUS: FORMALLY_COMPLETE
C4D_LOGICAL_CONTRACT: FINALIZED
C4D_PUBLIC_API_SHAPE: FINAL
FINAL_C4D_PUBLIC_API_SHAPE: build_jra_race_historical_replay(seed, five read-only providers) -> JRARaceHistoricalReplayResult
IMPLEMENTATION_READY: YES_AFTER_INDEPENDENT_APPROVAL
BLOCKERS: NONE

FINAL_C4D_INPUT_STYLE: ONE_EXACT_JRA_RACE_REPLAY_SEED_PLUS_READ_ONLY_PROVIDERS
CONTRADICTORY_DECOMPOSED_CALLER_FIELDS_ALLOWED: NO

C4D_V3_SELECTION: EXACT_SEED_BOUND_CAPTURE_ID
LATEST_V3_LOOKUP_IN_C4D: NO
RACE_ID_ONLY_V3_LOOKUP: NO
URL_ONLY_LATEST_V3_LOOKUP: NO
ARCHIVE_ENRICHMENT_CAN_CHANGE_EXISTING_SEED_REPLAY: NO

SEED_C4C_PROVENANCE_EQUALITY: EXACT_ALL_RETAINED_FIELDS_REQUIRED
SEED_TARGET_ENTRY_SET_EQUALITY: EXACT_ORDERED_IDENTITY_EQUALITY_REQUIRED

HISTORICAL_EVIDENCE_OBSERVATION_BOUND: seed.captured_at
SNAPSHOT_INFORMATION_CUTOFF: seed.information_cutoff
STORED_AT_CAUSAL_ROLE: NONE

TARGET_HORSE_HISTORY_LOCATOR_POLICY: EXACT_NORMALIZER_LOCATOR_ALIGNED_TO_CORRESPONDING_SEED_ENTRY
SOURCE_UNION_POLICY: TARGET_RECORDS_THEN_PER_ENTRY_HISTORICAL_RECORDS_IN_SEED_ORDER
PARTIAL_SOURCE_UNION_ALLOWED: NO

SNAPSHOT_MAPPING_SOURCE: EXACT_SEED_ENTRIES_ONLY
SNAPSHOT_BUILDER_CALL_COUNT: EXACTLY_ONCE
SNAPSHOT_PERSISTENCE_IN_C4D: NO

RESULT_DOMAIN: FROZEN_SLOTTED_JRARaceHistoricalReplayResult
RESULT_FIELDS: seed; snapshot
RAW_RESPONSE_BYTES_DUPLICATED: NO

EXACT_V3_BY_ID_PROTOCOL_OWNER: C4D_MODULE_PRIVATE_PROTOCOL
SEED_BOUND_ADAPTER_VISIBILITY: PRIVATE_TO_C4D_MODULE

C4D_DATABASE_WRITE: NO
C4D_LIVE_HTTP: NO
C4D_ARCHIVE_WRITE: NO
```

## PREPARE Allowed Files

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Stop Condition

Stop after this docs-only PREPARE commit is pushed for independent review. Do not
implement c4d, modify formal contracts, persist a snapshot, query latest target-card
evidence, write an archive, perform live HTTP, or begin a later phase.
