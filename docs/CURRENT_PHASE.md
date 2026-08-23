# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase

`4C-2d3b1i6d1d5f1c4d` — JRA race-level historical replay orchestration.

Formal base: `1394a6042da1938511798fbbbdf31b09b1a196f6`.

Review branch:
`review/4c-2d3b1i6d1d5f1c4d-jra-race-level-historical-replay-prepare`.

This PREPARE is documentation only. It adds no production code, tests, schema,
migration, HTTP, archive mutation, or trusted capture.

## Phase Identity and Responsibility

The adjacent formal sequence is c4a target-horse accessU resolution, c4b historical
accessS/accessO causal resolution, and c4c target accessD causal resolution. The next
identifier is therefore `4C-2d3b1i6d1d5f1c4d`.

C4d should add one new pure one-race module,
`scripts/simulation/jra_race_historical_replay.py`. It composes existing formal
boundaries; it does not duplicate their parsing, archive lookup, source normalization,
or snapshot validation. Its intended public surface is:

```python
class JRARaceHistoricalReplayError(ValueError): ...
class JRARaceHistoricalReplayValidationError(JRARaceHistoricalReplayError): ...
class JRARaceHistoricalReplayUnavailableError(JRARaceHistoricalReplayError): ...
class JRARaceHistoricalReplayUnsupportedError(JRARaceHistoricalReplayError): ...

@dataclass(frozen=True, slots=True)
class JRARaceHistoricalReplayResult:
    snapshot: HistoricalInputSnapshot
    target_race_selection_capture_id: str
    target_race_card_capture_id: str
    target_race_card_response_sha256: str
    captured_at: datetime
    information_cutoff: datetime

def build_jra_race_historical_replay(
    *,
    dataset_id: str,
    internal_race_id: int,
    external_race_id: str,
    target_race_selection_capture_id: str,
    captured_at: datetime,
    information_cutoff: datetime,
    race_entry_id_by_external_entry_id: Mapping[str, int],
    target_race_selection_capture_provider:
        JRATargetRaceSelectionCaptureProvider,
    target_race_card_capture_provider: JRATargetRaceCardCaptureProvider,
    horse_history_response_provider: JRATargetHorseHistoryResponseProvider,
    race_result_response_provider: JRAHistoricalRaceResultResponseProvider,
    final_win_odds_response_provider:
        JRAHistoricalFinalWinOddsResponseProvider,
) -> JRARaceHistoricalReplayResult: ...
```

The caller is a future dataset/replay composition root that owns dataset and internal
race identity, replay times, the exact retained v4 capture ID, the established external-
to-internal entry map, and injected read-only provider adapters. The immediate downstream
consumer is the existing historical snapshot repository/input flow through the returned
`HistoricalInputSnapshot`. Prediction, betting, settlement, multi-race scheduling, and
CLI ownership remain outside c4d.

No package-root export is required.

## Exact Target Provenance and Missing Durable Handoff

The public call requires the exact `jra-capture-v4:` ID as an explicit caller input.
It passes that ID unchanged to `resolve_jra_target_race_card_response(...)`. C4d never
enumerates v4 captures, scans by race ID, selects a latest v4 row, invokes c0b3, or
constructs navigation material.

Current code has no durable association from a replay/snapshot request to this exact v4
ID. `capture_target_race_navigation(...)` returns it in the transient frozen
`JRATargetRaceNavigationCaptureResult`, and the JRA archive can load the capture by ID,
but neither the neutral `HistoricalInputSnapshot` nor its repository stores the v4 ID.
The archive intentionally cannot rediscover it from external race identity. A future
production caller therefore cannot yet recover the required input after process loss.

This is an explicit prerequisite, not permission to add a fallback. A narrow upstream
acquisition manifest or JRA-specific replay-provenance persistence boundary must retain
the c0b3 result's exact v4 ID and hand it to c4d. The neutral source-record values must
not gain provider-specific capture IDs. The exact persistence owner and physical shape
require a separate approved design because no current durable caller identity exists to
key such a record safely.

## Causal Order and Time Guard

Before archive providers run, the orchestrator validates exact caller scalar types,
canonical external race identity, the v4 ID grammar, provider callability, and:

```text
captured_at <= information_cutoff
```

The complete success order is:

```text
exact retained v4 capture ID
-> resolve_jra_target_race_card_response(..., captured_at=...)
-> normalize_jra_target_race_input_source_records(response=resolution.response)
-> require normalized target race identity == requested external_race_id
-> obtain scheduled_start_at only from the normalized target track
-> require captured_at <= information_cutoff <= scheduled_start_at
-> for each target entry and aligned retained accessU locator in horse-number order:
     resolve_jra_target_horse_history_response(
         observed_at_not_after=captured_at,
     )
     collect_jra_historical_input_source_records(
         observed_at_not_after=captured_at,
     )
-> form one deterministic complete source-record tuple
-> call build_historical_input_snapshot(...) exactly once
-> construct and return the race-level result
```

`captured_at` is the inclusive observation-selection bound for accessD, accessU,
accessS, and accessO and the snapshot capture time. `information_cutoff` is the
prediction-information ceiling supplied unchanged to the snapshot builder. The target
scheduled start is the outer limit and comes only from causally resolved accessD
evidence. Every source evidence observation must be no later than `captured_at`; the
existing resolvers/collector enforce that during acquisition and the existing snapshot
builder rechecks the complete union.

`stored_at` has no replay role. It is neither cutoff, selection input, fallback key,
tie-break, nor proof of historical availability.

## Per-Entry History and Past Form

The only accessU locator source is
`JRATargetRaceSourceCollection.target_horse_history_locators`, aligned one-for-one with
its ascending `target_entry_records`. The orchestrator passes the corresponding track,
entry, and locator to the existing target-horse resolver with the exact caller
`captured_at`. No URL synthesis, raw accessD reparse, horse-name linkage, or current
history fallback is permitted. Missing eligible accessU evidence is unavailable and
stops the entire race.

The existing `collect_jra_historical_input_source_records(...)` remains the sole owner
of complete accessU discovery, accessS reference selection, accessS-to-accessO locator
extraction, caching, absence projection, and past-race normalization. C4d supplies its
exact target track/entry, resolved accessU response, `observed_at_not_after=captured_at`,
and the injected accessS/accessO providers.

AccessS URLs come only from formal accessU discovery. AccessO request locators come only
from the selected accessS response. Proven zero history remains exactly one formal
`past_race_absence` record. A missing required accessS/accessO capture is unavailable;
non-JRA or unsupported actual history remains unsupported; neither becomes absence,
skipped history, or a partial result.

## Source Union, Entry Mapping, and Snapshot

C4d owns only the deterministic union of already-produced records. The exact order is:

```text
track,
for each target entry in ascending official horse number:
    entry, jockey, odds_win,
    that entry's past_race records in formal newest-to-oldest order
    OR its single formal past_race_absence record
```

There is exactly one target track, one target group per entry, and exactly one coherent
historical collection per target entry. No orphan, missing, additional, duplicate
`source_id`, or conflicting official past-race identity is accepted. C4d creates no
record itself. Existing collection constructors plus the neutral validator called by
`build_historical_input_snapshot(...)` own duplicate/conflict validation; c4d adds no
parallel neutral schema.

No current resolver maps canonical JRA external entry IDs to internal race-entry IDs.
`RaceEntrySelectionResolver` and `RaceEntrySource` resolve prediction horse selections,
not JRA external identities, and must not be repurposed. The c4d caller supplies
`race_entry_id_by_external_entry_id` from its already-established dataset/import
identity ownership. Keys must be exactly the target normalizer's canonical
`external_entry_id` values; the existing snapshot builder validates complete,
one-to-one mapping. Horse or jockey names are never mapping keys.

C4d calls the existing `build_historical_input_snapshot(...)` exactly once and passes
`dataset_id`, `internal_race_id`, `information_cutoff`, `captured_at`, the complete
source tuple, and the caller's entry map directly. It returns only after the builder has
accepted the full race. No second snapshot validation model is introduced.

## Result Provenance and Error Boundary

`JRARaceHistoricalReplayResult` is the race-level provenance owner. It retains the exact
v4 and selected v3 capture IDs, target-card response SHA, caller `captured_at`, caller
`information_cutoff`, and the built snapshot. The snapshot/source evidence already
retains exact canonical source URLs, response digests, and observations. Raw HTML bytes
are not duplicated in the result.

The orchestrator catches only exact existing domain errors:

- c4c, accessU, collector, target-normalizer, and snapshot caller/lineage contradictions
  translate to `JRARaceHistoricalReplayValidationError`;
- c4c, accessU, and collector absence translate to
  `JRARaceHistoricalReplayUnavailableError`;
- target-normalizer or collector supported-envelope failures translate to
  `JRARaceHistoricalReplayUnsupportedError`;
- neutral source-set/builder validation and conflict errors translate to race-level
  validation;
- provider-owned exceptions, especially `RepositoryDataIntegrityError`, propagate
  unchanged and are never converted to missing or validation.

There is no broad `Exception`/`BaseException` catch. Any failure returns no result and
no snapshot. The boundary performs no HTTP, archive write, auto-capture, current-page
fallback, timestamp rewriting, or partial return.

## Database Impact and Readiness

No capture-archive schema, migration, table, column, index, or repository API is needed
to implement the pure orchestration mechanics: all required exact/bounded read APIs are
formal. The existing snapshot schema can persist the built neutral snapshot and its
source evidence, including the target accessD URL/SHA/observation, but it cannot persist
the v4 navigation capture ID or the explicit c4c v3 capture ID as race-level companion
provenance.

Accordingly, production historical replay is not implementation-ready until the exact
v4 handoff receives its own approved ownership. If that owner is database-backed, a
schema migration and a JRA-specific provenance save/load API will be required; whether
that is a new table or columns cannot be frozen safely until the durable manifest key
and lifecycle are defined. No speculative schema/index is authorized in c4d.

## Future Test Intent

Future offline tests must cover canonical complete one-race composition; exact v4 ID
use and call counts; no race-ID/latest-v4/c0b3 path; c4c response feeding the target
normalizer; scheduled start sourced from resolved target evidence; both halves of
`captured_at <= information_cutoff <= scheduled_start_at`; future accessD/accessU/
accessS/accessO rejection; exact aligned locator/entry iteration; accessU/accessS/
accessO missing behavior; formal zero-history absence only; unsupported history without
skip; integrity propagation unchanged; no name mapping; complete entry-map pass-through;
deterministic source order and repeated snapshot build; snapshot-builder compatibility;
no HTTP/write/current fallback; no partial result; exact result provenance; no raw-byte
duplication; no broad catch; and no package-root export.

## Readiness Matrix

```text
NEXT_PHASE_ID: 4C-2d3b1i6d1d5f1c4d
NEXT_PHASE_NAME: JRA_RACE_LEVEL_HISTORICAL_REPLAY_ORCHESTRATION

ORCHESTRATION_OWNER: NEW_PURE_scripts/simulation/jra_race_historical_replay.py
PUBLIC_API: build_jra_race_historical_replay_WITH_EXACT_V4_ID_CAPTURED_AT_INFORMATION_CUTOFF_MAPPING_AND_INJECTED_PROVIDERS
RESULT_DOMAIN: FROZEN_SLOTTED_JRARaceHistoricalReplayResult_CONTAINING_SNAPSHOT_AND_CAPTURE_PROVENANCE
CALLER: FUTURE_DATASET_OR_REPLAY_COMPOSITION_ROOT
DOWNSTREAM_CONSUMER: EXISTING_HISTORICAL_SNAPSHOT_REPOSITORY_AND_SIMULATION_INPUT_FLOW

V4_CAPTURE_ID_INPUT_OWNER: C4D_CALLER_FROM_PREVIOUSLY_RETAINED_C0B3_PROVENANCE
V4_CAPTURE_ID_PERSISTENCE_OR_HANDOFF: NOT_CURRENTLY_FORMAL_OR_DURABLE; TRANSIENT_C0B3_RESULT_ONLY
RACE_ID_ONLY_V4_DISCOVERY_ALLOWED: NO
LATEST_V4_LOOKUP_ALLOWED: NO
LIVE_C0B3_FALLBACK_ALLOWED: NO

TARGET_RESOLUTION_ORDER: EXACT_V4_ID_TO_C4C_TO_TARGET_NORMALIZATION_TO_SCHEDULE_GUARD_TO_PER_ENTRY_HISTORY
CAPTURED_AT_ROLE: INCLUSIVE_OBSERVATION_BOUND_FOR_ALL_FOUR_JRA_RESPONSE_FAMILIES_AND_SNAPSHOT_CAPTURE_TIME
INFORMATION_CUTOFF_ROLE: CALLER_SUPPLIED_PREDICTION_INFORMATION_CEILING
SCHEDULED_START_ROLE: OUTER_CAUSAL_LIMIT_FROM_RESOLVED_NORMALIZED_TARGET_ACCESSD_ONLY
FULL_TIME_INVARIANT: ALL_EVIDENCE_observed_at_LE_captured_at_LE_information_cutoff_LE_scheduled_start_at
STORED_AT_REPLAY_ROLE: NONE

TARGET_HISTORY_LOCATOR_SOURCE: EXACT_ALIGNED_JRATargetRaceSourceCollection_LOCATORS
TARGET_HISTORY_BOUND: captured_at
TARGET_HISTORY_MISSING_POLICY: DEDICATED_RACE_LEVEL_UNAVAILABLE_AND_NO_PARTIAL_RESULT
NAME_BASED_HORSE_LINK_ALLOWED: NO

PAST_FORM_OWNER: EXISTING_collect_jra_historical_input_source_records
PAST_FORM_BOUND: captured_at
ACCESS_S_URL_SOURCE: FORMAL_ACCESSU_DISCOVERY_RACE_REFERENCE_ONLY
ACCESS_O_LOCATOR_SOURCE: FORMAL_EXTRACTION_FROM_SELECTED_EXACT_ACCESS_S_RESPONSE_ONLY
ABSENCE_POLICY: ONLY_FORMALLY_PROVEN_ZERO_ACTUAL_HISTORY; MISSING_OR_UNSUPPORTED_IS_NOT_ABSENCE

SOURCE_RECORD_UNION_OWNER: C4D_PURE_ORCHESTRATOR
SOURCE_RECORD_ORDER: TRACK_THEN_EACH_ASCENDING_ENTRY_TARGET_GROUP_THEN_ITS_FORMAL_HISTORY_OR_ABSENCE
SOURCE_RECORD_DUPLICATE_POLICY: FAIL_CLOSED_THROUGH_EXISTING_NEUTRAL_VALIDATION
SOURCE_RECORD_CONFLICT_POLICY: FAIL_CLOSED_THROUGH_EXISTING_NEUTRAL_VALIDATION

ENTRY_MAPPING_OWNER: CALLER_EXISTING_DATASET_IMPORT_IDENTITY_BOUNDARY
EXTERNAL_ENTRY_ID_SOURCE: FORMAL_TARGET_ACCESSD_NORMALIZER_ONLY
INTERNAL_ENTRY_MAPPING_SOURCE: CALLER_SUPPLIED_EXACT_EXTERNAL_ENTRY_TO_INTERNAL_RACE_ENTRY_MAP
NAME_BASED_MAPPING_ALLOWED: NO

SNAPSHOT_BUILDER_CALLED_IN_THIS_PHASE: YES_EXACTLY_ONCE
ORCHESTRATION_STOPS_AT: FROZEN_RACE_LEVEL_RESULT_CONTAINING_COMPLETE_HistoricalInputSnapshot_AND_CAPTURE_PROVENANCE

LIVE_HTTP: NO
ARCHIVE_WRITE: NO
AUTO_CAPTURE: NO
CURRENT_FALLBACK: NO
PARTIAL_RESULT_ALLOWED: NO

RACE_LEVEL_PROVENANCE_OWNER: JRARaceHistoricalReplayResult
V4_ID_RETAINED: YES
V3_ID_RETAINED: YES
TARGET_CARD_SHA_RETAINED: YES
CAPTURED_AT_RETAINED: YES
INFORMATION_CUTOFF_RETAINED: YES
RAW_BYTES_DUPLICATED: NO

SCHEMA_CHANGE_REQUIRED: NO_FOR_PURE_C4D; YES_OR_EQUIVALENT_DURABLE_MANIFEST_REQUIRED_FOR_PRODUCTION_HANDOFF
MIGRATION_REQUIRED: NOT_IN_C4D; REQUIRED_ONLY_IF_THE_SEPARATE_HANDOFF_IS_DATABASE_BACKED
NEW_TABLE_REQUIRED: NOT_DETERMINED_PENDING_DURABLE_MANIFEST_IDENTITY_AND_LIFECYCLE
NEW_COLUMN_REQUIRED: NOT_DETERMINED; DO_NOT_ADD_PROVIDER_FIELDS_TO_NEUTRAL_SOURCE_RECORDS
NEW_INDEX_REQUIRED: NO_C4D_INDEX; FUTURE_PROVENANCE_STORAGE_MUST_JUSTIFY_ITS_OWN_INDEX
NEW_REPOSITORY_API_REQUIRED: NO_FOR_C4D_READ_COMPOSITION; YES_IF_A_DATABASE_PROVENANCE_HANDOFF_IS_SELECTED

IMPLEMENTATION_READY: NO_FOR_PRODUCTION_REPLAY_PENDING_FORMAL_DURABLE_EXACT_V4_CAPTURE_ID_HANDOFF; PURE_ORCHESTRATION_CONTRACT_OTHERWISE_READY
BLOCKERS: NO_CURRENT_DURABLE_REPLAY_OR_SNAPSHOT_ASSOCIATION_OWNS_THE_EXACT_C0B3_V4_CAPTURE_ID

REAL_TRUSTED_CAPTURE_REQUIRED: NO
REAL_TRUSTED_CAPTURE_PERFORMED: NO
```

## Allowed Files

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Stop Condition

Stop after this docs-only review commit is pushed. Do not implement c4d, provenance
persistence, schema, migration, repository APIs, HTTP, capture, source normalization,
snapshot persistence, prediction, betting, or settlement. Independent review must first
decide the exact durable v4 provenance handoff.
