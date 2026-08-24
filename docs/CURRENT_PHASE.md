# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase

`4C-2d3b1i6d1d5f1c4d0` — JRA race replay seed identity.

Formal base: `1394a6042da1938511798fbbbdf31b09b1a196f6`.

Approved c4d PREPARE reference:
`509e48fdadd74064a6ccaddcc60fab04ef98d9b1`.

Review branch:
`review/4c-2d3b1i6d1d5f1c4d0-jra-race-replay-seed-prepare`.

This PREPARE is documentation only. It adds no domain, repository, migration, importer,
test, HTTP, snapshot, or c4d implementation. The c4d PREPARE is an architecture
reference only and is not merged or otherwise integrated here.

## Phase Identity

The established prerequisite naming pattern inserts `0` after the blocked parent phase
identifier (c4c -> c4c0, followed by its children). The prerequisite immediately below
c4d is therefore `4C-2d3b1i6d1d5f1c4d0`, named **JRA race replay seed identity**.

## Domain Decision and Responsibilities

The provider-specific durable boundary is one immutable `JRARaceReplaySeed`, owned by a
new JRA race replay seed domain and SQLite repository/materializer. It is an acquisition
manifest for exactly one dataset-scoped target race and one replay causal policy. It is
not a neutral historical source record and no provider capture ID is added to
`HistoricalInputSourceRecord.record_values`.

The seed is created by the future JRA dataset acquisition/materialization composition
after all of these exact formal domains exist in memory:

1. `JRATargetRaceNavigationCaptureResult`, carrying the saved schema-v4 selection
   capture ID;
2. `JRATargetRaceCardResolution`, carrying the exact selected schema-v3 card revision;
3. `JRATargetRaceSourceCollection`, normalized from that exact card response;
4. caller-owned `dataset_id` and replay `information_cutoff`.

The repository materializer validates their shared lineage before opening its write
transaction. It then creates or reuses only formally proven internal race and entry
identities, persists the exact associations, and saves the immutable seed and its whole
ordered entry set atomically. C4d later consumes the loaded seed plus its existing
read-only capture/provider adapters. Identity proof, persistence, and replay consumption
are separate responsibilities.

The lifecycle is append-only:

```text
formal live/acquisition evidence
-> exact accessD resolution and normalization
-> atomic internal identity materialization + immutable seed save
-> process may terminate
-> exact seed load by seed_id
-> c4d read-only replay composition
```

The seed is process-boundary durable. It is never reconstructed by a latest/race-ID
search, names, current web access, or mutable run state.

## Race and Entry Identity Proof

Current code provides no safe bridge from a canonical JRA race to arbitrary legacy
`races`/`horses` rows. `races` has no canonical external race ID and its apparent key
`(race_date, organization, place, race_no)` is nullable, non-unique, and queried with
`LIMIT 1`. `horses` has no external entry/horse identity, no declared race FK, and no
unique `(race_id, horse_no)` constraint. Existing `save_race`/`save_horse` helpers use
separate connections and pre-checks and cannot atomically prove the associations.
`SQLiteRaceEntrySource` resolves prediction IDs, not JRA provider identities.

Consequently:

- the legacy race natural key is **not** formalized;
- no horse or race name may be used;
- arbitrary caller-supplied internal integers are forbidden;
- an unproven legacy natural-key match is never adopted;
- an unproven legacy natural-key collision fails closed rather than causing a duplicate
  formal row or a first-match selection.

The new materializer is the authoritative creation owner. On first acquisition it
creates one internal `races` row from the exact normalized target track facts and obtains
its generated ID in the same transaction. It creates one minimal internal `horses` row
for every canonical target entry, under that exact race ID, and obtains each generated
entry ID in that same transaction. It writes the corresponding existing
`historical_input_external_races` and `historical_input_external_entries` associations
before the seed becomes visible.

Horse number is formalized only as a race-bound **creation binding**. The external entry
ID is already canonically rebuilt from JRA external race identity plus official positive
horse number, and `JRATargetRaceSourceCollection` proves ascending unique horse numbers,
unique external horse identities, and exact entry identities. The materializer may use
that horse number to create a new row under the already-proven internal race. It may not
use horse number to select an arbitrary pre-existing row. An already-existing mapping is
reusable only when it was previously persisted by this formal boundary and its entire
external/internal association and race membership revalidate exactly.

Each seed entry retains:

- zero-based `entry_order` in ascending official horse-number order;
- canonical `external_entry_id`;
- canonical `external_horse_id`;
- official `horse_no`;
- exact `internal_race_entry_id`.

Every entry is bound to the seed's external and internal race. Duplicate order, horse
number, external entry, external horse, or internal entry is invalid. A foreign-race
internal entry is integrity failure. There is no missing or additional entry relative
to the exact normalized target collection.

## Exact Capture Provenance and Target Revision

`target_race_selection_capture_id` comes only from the exact
`JRATargetRaceNavigationCaptureResult` supplied during materialization. It is durable,
immutable, and retained verbatim. Race-ID-only or latest-v4 rediscovery is forbidden.

At creation, the navigation result and `JRATargetRaceCardResolution` must have identical
discovery provenance and schema-v4 capture ID. The existing c4c resolution contract is
the lineage authority that loads the exact v4 capture, reruns formal discovery, and
proves its selected target URL and canonical external race identity. The normalized
target records must then prove that same race and the exact resolution response.

The seed also retains:

- `target_race_card_capture_id`;
- `target_race_card_response_sha256`;
- `canonical_target_race_card_url`.

This is not redundant convenience data. It binds the entry set to the exact schema-v3
target-card revision from which it was normalized. A later archive insertion at an
eligible observation time must not silently change the target revision or runner set of
an existing seed. At c4d consumption, c4c is called using the seed's exact v4 ID and
`captured_at`, and its returned v3 ID, digest, URL, and race must equal the seed before
normalization or history acquisition continues. Capture-archive corruption and absence
remain provider errors; they are never converted to seed missing.

## Causal and Dataset Identity

`captured_at` is owned by the acquisition/seed materialization coordinator. It is the
inclusive evidence-observation bound used to select the exact accessD revision and later
accessU/accessS/accessO evidence. It is an exact aware datetime, normalized to UTC for
identity, and is part of immutable seed identity.

`information_cutoff` is caller-supplied dataset replay policy at seed creation. It is an
exact aware datetime, is part of immutable seed identity, and must satisfy:

```text
captured_at <= information_cutoff <= target scheduled_start_at
```

It does not select archive evidence and is not substituted for `captured_at`. Both times
are retained so a restarted replay receives exactly the same causal policy.

`dataset_id` is owned by the dataset acquisition/replay composition root. The current
schema has no dataset registry table, so it is a validated nonempty exact string rather
than a foreign key. It is part of seed identity. A seed cannot be reused under a
different dataset ID; a separate seed is required even when the underlying formally
proven external/internal mapping is the same.

## Seed Domain and Deterministic Identity

The future module owns exact frozen/slotted public types:

```python
@dataclass(frozen=True, slots=True)
class JRARaceReplaySeedEntry:
    entry_order: int
    external_entry_id: str
    external_horse_id: str
    horse_no: int
    internal_race_entry_id: int

@dataclass(frozen=True, slots=True)
class JRARaceReplaySeed:
    seed_id: str
    schema_version: int
    content_sha256: str
    dataset_id: str
    external_race_id: str
    internal_race_id: int
    target_race_selection_capture_id: str
    target_race_card_capture_id: str
    target_race_card_response_sha256: str
    canonical_target_race_card_url: str
    captured_at: datetime
    information_cutoff: datetime
    entries: tuple[JRARaceReplaySeedEntry, ...]
```

`schema_version` is exactly 1. `seed_id` is
`jra-race-replay-seed-v1:<64 lowercase hex>`. Its suffix equals
`content_sha256`, SHA-256 over the UTF-8 canonical JSON bytes of every field except
`seed_id` and `content_sha256`. Canonical JSON uses `sort_keys=True`, compact separators
`(",", ":")`, and `ensure_ascii=False`; datetimes are normalized UTC ISO 8601 with
microseconds. Entries are encoded as an array in ascending `entry_order`/horse-number
order, never as a mapping whose order could be lost.

The database natural identity is:

```text
schema_version,
dataset_id,
external_race_id,
target_race_selection_capture_id,
captured_at_utc,
information_cutoff_utc
```

All other immutable fields are content. The same natural identity with different
content is a conflict. Identical content has the same digest/seed ID and an exact save
is idempotent. Changed evidence, causal policy, or dataset identity creates a distinct
seed unless it conflicts under the natural identity rule. Update, replacement, and
different-content upsert are forbidden.

## Persistence and Migration

The persistence owner is a new
`SQLiteJRARaceReplaySeedRepository` in the existing main application SQLite database
that already owns `races`, `horses`, historical external mappings, and historical
snapshots. The JRA capture archive remains a separately injected repository and is not
assumed to share the same physical database connection.

A global application migration v015 is required. It adds only provider-specific seed
storage and FK-supporting uniqueness:

- `jra_race_replay_seeds` — one immutable header per seed;
- `jra_race_replay_seed_entries` — the complete ordered mapping, owned by the header;
- `ux_historical_input_external_races_exact_mapping` over organization, source system,
  external race ID, and internal race ID;
- `ux_historical_input_external_entries_exact_mapping` over organization, source
  system, external race ID, external entry ID, internal race ID, and internal entry ID.

No existing table receives a provider-specific column. The seed tables use fixed
`organization='JRA'` and `source_system='jra_official'`, exact scalar/digest/ID/time
checks, a natural-identity `UNIQUE` constraint, child uniqueness for order/external
entry/external horse/horse number/internal entry, and `WITHOUT ROWID` where consistent
with current migration style.

The two explicit unique indexes are logically redundant with existing functional
mappings but are required as SQLite parent keys for exact composite foreign keys. The
header has exact FKs to the full external-race mapping and `races(id)`. Each child has
an exact FK to the full external-entry mapping, a composite membership FK
`(internal_race_id, internal_race_entry_id) -> horses(race_id, id)`, and a cascading FK
to its seed header. Existing v010 already provides the required unique parent key on
`horses(race_id, id)`.

There is no v4 capture FK because capture and application repositories are connection-
injected and cannot safely be assumed to be one SQLite database. Exact capture existence
and lineage are validated through formal provider domains both at creation and c4d
consumption. There is no dataset FK because no formal dataset table exists.

Migration v015 must validate the exact registered v014 state before mutation, preserve
all existing tables/rows, own no transaction, roll back completely through the global
migration runner, and reject lookalike/partial state. It does not alter JRA capture
migrations or archive schema.

## Creation and Load APIs

The exact materialization API is repository-owned because generated internal IDs and all
mapping/seed writes must share one SQLite transaction:

```python
class SQLiteJRARaceReplaySeedRepository:
    def materialize_seed(
        self,
        *,
        dataset_id: str,
        navigation_capture_result: JRATargetRaceNavigationCaptureResult,
        target_race_card_resolution: JRATargetRaceCardResolution,
        target_sources: JRATargetRaceSourceCollection,
        information_cutoff: datetime,
    ) -> JRARaceReplaySeed: ...

    def load_seed(
        self,
        *,
        seed_id: str,
    ) -> JRARaceReplaySeed | None: ...
```

The repository performs no HTTP and does not invoke c0b3 or c4c. Its inputs are already
formal proof objects. Creation validation order is frozen:

1. require exact input domain/scalar types, canonical dataset/race/capture/digest/URL
   shapes, aware times, and exact target collection types;
2. prove navigation result, c4c resolution, target response evidence, normalized race,
   scheduled start, and full entry/locator set agree exactly;
3. require `captured_at` from the resolution and
   `captured_at <= information_cutoff <= scheduled_start_at`;
4. begin one `BEGIN IMMEDIATE` transaction with foreign keys enabled;
5. load and fully validate an existing formal external-race mapping, or create the
   internal race and mapping only when no mapped or colliding unproven legacy row exists;
6. for every ordered target entry, load and validate its prior formal mapping, or create
   a new race-bound internal entry and mapping only when no colliding unproven row exists;
7. construct and revalidate the complete immutable seed and deterministic digest;
8. enforce natural-identity/idempotence/conflict rules, insert the header and all
   children, then commit once.

Any failure rolls back races, horses, external mappings, seed header, and seed entries.
A partial header or partial mapping is never loadable. Existing formal mappings may be
shared between dataset-specific seeds only after exact validation; the seeds themselves
cannot cross datasets.

`load_seed` accepts only exact seed-ID grammar. Missing is `None`; malformed input is
repository validation failure. It loads the header and complete ordered children,
reconstructs the exact domain, recomputes the digest/ID, and rechecks full external/
internal mapping and membership state. Missing/extra/duplicate/foreign/conflicting rows
or digest drift are integrity errors, never absence. No latest-by-race, race-ID-only,
dataset-latest, name, or natural-key load API is allowed.

## Error Boundary

- **Validation**: malformed caller/domain values, types, times, IDs, or internally
  contradictory formal inputs before persistence.
- **Unavailable**: an exact required seed or formal referenced capture does not exist at
  the owning resolution boundary.
- **Integrity**: persisted conflicts, unproven legacy collisions, duplicate mappings,
  foreign membership, partial children, digest mismatch, or contradictory referenced
  data.
- **Unsupported**: only an already-recognized official/import value outside the approved
  materialization envelope; never a substitute for ambiguity or corruption.

Provider/repository integrity errors propagate. Corruption never becomes missing,
identity contradiction never becomes missing, and missing never triggers a latest or
current fallback.

## C4d Handoff

After this phase is implemented, c4d should receive one exact loaded
`JRARaceReplaySeed`, not independently caller-supplied dataset, race, capture, mapping,
and time fields. Its final candidate API becomes:

```python
def build_jra_race_historical_replay(
    *,
    seed: JRARaceReplaySeed,
    target_race_selection_capture_provider:
        JRATargetRaceSelectionCaptureProvider,
    target_race_card_capture_provider: JRATargetRaceCardCaptureProvider,
    horse_history_response_provider: JRATargetHorseHistoryResponseProvider,
    race_result_response_provider: JRAHistoricalRaceResultResponseProvider,
    final_win_odds_response_provider:
        JRAHistoricalFinalWinOddsResponseProvider,
) -> JRARaceHistoricalReplayResult: ...
```

C4d revalidates the seed domain, invokes c4c with the seed's exact v4 ID and
`captured_at`, requires the returned v3 ID/SHA/URL to match the seed, normalizes the same
entry set, requires exact ordered entry-map equality, and then performs its already-
prepared read-only replay. It never creates or modifies the seed.

The restart guarantee is exact: after acquisition/materialization terminates, loading
the same `seed_id` yields the same v4 and v3 provenance, dataset/race identity, causal
times, and ordered external/internal entry mappings without web access.

## Future Implementation Scope

Expected allowed production files for the later approved implementation:

- `scripts/simulation/jra_race_replay_seed.py`
- `scripts/simulation/repositories/sqlite_jra_race_replay_seed_repository.py`
- `scripts/migrations/runner.py`
- `scripts/migrations/versions/v015_jra_race_replay_seed_schema.py`

Expected tests:

- `tests/test_jra_race_replay_seed.py`
- `tests/test_sqlite_jra_race_replay_seed_repository.py`
- directly relevant global migration tests

Plus `docs/CURRENT_PHASE.md` and `docs/LATEST_CODEX_REPORT.md`. No capture archive,
snapshot, target normalizer, c4d, live acquisition, prediction, betting, or settlement
file belongs to d0.

Future tests must directly pin canonical creation; deterministic content/ID; exact v4
and v3 provenance; wrong v4/race and wrong v3/revision rejection; restart equality;
identical idempotence; natural-identity content conflict; no race/latest-v4 lookup;
first snapshot readiness without an existing historical snapshot; atomic new internal
race/entry creation; exact prior formal mapping reuse; unproven legacy natural-key and
horse-number collision failure; no name matching; exact complete ordered entry set;
missing/extra/duplicate/foreign mappings; membership FKs; digest corruption; partial
write rollback; migration rollback and exact v014 validation; neutral records unchanged;
no live HTTP/current fallback; and no c4d implementation.

Required implementation verification will include dedicated domain/repository/migration
tests, related target navigation/resolution/normalization/snapshot repository tests, the
full pytest suite, `git diff --check`, and static scope/no-HTTP/no-c4d checks.

## Stop Condition

This PREPARE stops after its docs-only review commit. It does not authorize production,
test, schema, migration, importer, c4d, or live changes. Implementation must wait for
independent approval. A later implementation must stop if exact target evidence cannot
materialize the legacy row shapes without guessing, if an unproven legacy collision is
encountered, or if a required change falls outside its approved files.

## Readiness Matrix

```text
NEXT_PHASE_ID: 4C-2d3b1i6d1d5f1c4d0
NEXT_PHASE_NAME: JRA_RACE_REPLAY_SEED_IDENTITY

DOMAIN_OWNER: NEW_PROVIDER_SPECIFIC_JRA_RACE_REPLAY_SEED_DOMAIN_AND_SQLITE_REPOSITORY_MATERIALIZER
DOMAIN_NAME: JRARaceReplaySeed_WITH_JRARaceReplaySeedEntry
PURPOSE: PROCESS_DURABLE_AUDITABLE_HANDOFF_OF_EXACT_CAPTURE_PROVENANCE_AND_PROVEN_RACE_ENTRY_IDENTITY_TO_C4D
CREATED_BY: FUTURE_JRA_DATASET_ACQUISITION_MATERIALIZATION_COMPOSITION_AFTER_C0B3_C4C_AND_TARGET_NORMALIZATION
CONSUMED_BY: FUTURE_C4D_RACE_LEVEL_HISTORICAL_REPLAY_ORCHESTRATOR
LIFECYCLE: CREATE_ONCE_APPEND_ONLY_LOAD_BY_EXACT_SEED_ID
IMMUTABLE: YES
PROCESS_BOUNDARY_DURABLE: YES

RACE_IDENTITY_PROOF_SOURCE: EXACT_NORMALIZED_JRA_TARGET_TRACK_PLUS_ATOMIC_INTERNAL_RACE_CREATION_OR_EXACT_PRIOR_FORMAL_MAPPING
ENTRY_IDENTITY_PROOF_SOURCE: EXACT_NORMALIZED_TARGET_ENTRY_SET_PLUS_RACE_BOUND_ATOMIC_INTERNAL_ENTRY_CREATION_OR_EXACT_PRIOR_FORMAL_MAPPING
INTERNAL_RACE_CREATION_OWNER: SQLiteJRARaceReplaySeedRepository_MATERIALIZE_SEED_TRANSACTION
INTERNAL_ENTRY_CREATION_OWNER: SQLiteJRARaceReplaySeedRepository_MATERIALIZE_SEED_TRANSACTION
CALLER_SUPPLIED_UNVERIFIED_INTERNAL_IDS_ALLOWED: NO

RACE_NATURAL_KEY_FORMALIZED: NO
HORSE_NUMBER_MAPPING_FORMALIZED: YES_ONLY_AS_RACE_BOUND_CREATION_BINDING_OR_REVALIDATION_OF_A_PRIOR_FORMAL_MAPPING_NEVER_LEGACY_LOOKUP
NAME_MATCHING_ALLOWED: NO
ENTRY_MEMBERSHIP_PROOF_REQUIRED: YES

V4_CAPTURE_ID_SOURCE: EXACT_JRATargetRaceNavigationCaptureResult.target_race_selection_capture_id
V4_CAPTURE_ID_DURABLE: YES_IN_IMMUTABLE_SEED
V4_CAPTURE_ID_MUTABLE: NO
RACE_ID_ONLY_V4_REDISCOVERY_ALLOWED: NO
LATEST_V4_REDISCOVERY_ALLOWED: NO
V4_RACE_LINEAGE_VALIDATION_OWNER: EXISTING_C4C_RESOLVER_PLUS_SEED_CROSS_DOMAIN_VALIDATION
V4_RACE_LINEAGE_VALIDATED_AT_CREATE: YES
V4_RACE_LINEAGE_REVALIDATED_AT_LOAD_OR_CONSUME: YES_AT_C4D_CONSUME_THROUGH_C4C_AND_EXACT_SEED_MATCH

EXTERNAL_ENTRY_SET_SOURCE: EXACT_JRATargetRaceSourceCollection_NORMALIZED_FROM_THE_SEED_BOUND_V3_RESPONSE
EXPECTED_ENTRY_SET_POLICY: EXACT_COMPLETE_ASCENDING_TARGET_REVISION_SET_WITH_NO_EXTRA_MISSING_DUPLICATE_OR_FOREIGN_ENTRY

V3_CAPTURE_ID_IN_SEED: YES
V3_RESPONSE_SHA_IN_SEED: YES
TARGET_CARD_URL_IN_SEED: YES
WHY: BINDS_THE_ENTRY_MAPPING_TO_ONE_EXACT_TARGET_CARD_REVISION_AND_PREVENTS_LATER_ARCHIVE_CONTENT_FROM_CHANGING_AN_EXISTING_SEED

CAPTURED_AT_OWNER: DATASET_ACQUISITION_AND_SEED_MATERIALIZATION_COORDINATOR
CAPTURED_AT_PART_OF_SEED_IDENTITY: YES
INFORMATION_CUTOFF_OWNER: CALLER_SUPPLIED_DATASET_REPLAY_POLICY_AT_SEED_CREATION
INFORMATION_CUTOFF_PART_OF_SEED_IDENTITY: YES

DATASET_ID_OWNER: DATASET_ACQUISITION_AND_REPLAY_COMPOSITION_ROOT
DATASET_ID_PART_OF_SEED_IDENTITY: YES
CROSS_DATASET_REUSE_ALLOWED: NO_FOR_SEED; YES_ONLY_FOR_SEPARATELY_REVALIDATED_UNDERLYING_FORMAL_EXTERNAL_INTERNAL_MAPPING

SEED_NATURAL_IDENTITY: schema_version+dataset_id+external_race_id+target_race_selection_capture_id+captured_at_utc+information_cutoff_utc
SEED_CONTENT_DIGEST: SHA256_LOWER_HEX_OF_FROZEN_CANONICAL_JSON_ALL_CONTENT_FIELDS
CANONICAL_JSON: UTF8_SORTED_KEYS_COMPACT_SEPARATORS_ENSURE_ASCII_FALSE_UTC_MICROSECONDS_ORDERED_ENTRY_ARRAY
ENTRY_ORDER: ZERO_BASED_ASCENDING_OFFICIAL_HORSE_NUMBER
DUPLICATE_POLICY: FAIL_CLOSED_FOR_ANY_ORDER_HORSE_NUMBER_EXTERNAL_ENTRY_EXTERNAL_HORSE_OR_INTERNAL_ENTRY_DUPLICATE

UPDATE_ALLOWED: NO
UPSERT_DIFFERENT_CONTENT_ALLOWED: NO
REPLACEMENT_ALLOWED: NO
IDEMPOTENT_IDENTICAL_SAVE_ALLOWED: YES

PERSISTENCE_OWNER: SQLiteJRARaceReplaySeedRepository
DATABASE: EXISTING_MAIN_APPLICATION_SQLITE_DATABASE_WITH_RACES_HORSES_AND_HISTORICAL_MAPPING_TABLES
TABLE_STRATEGY: TWO_NEW_PROVIDER_SPECIFIC_NORMALIZED_TABLES_PLUS_EXISTING_FORMAL_MAPPING_TABLES
SCHEMA_VERSION: 1_FOR_SEED_DOMAIN
MIGRATION_REQUIRED: YES_GLOBAL_APPLICATION_V015
NEW_TABLES: jra_race_replay_seeds_AND_jra_race_replay_seed_entries
NEW_COLUMNS: NEW_TABLE_COLUMNS_ONLY; NO_EXISTING_TABLE_COLUMN_CHANGE
NEW_INDEXES: TWO_EXPLICIT_EXACT_MAPPING_UNIQUE_INDEXES_FOR_COMPOSITE_FK_PARENT_KEYS; TABLE_PK_UNIQUE_CONSTRAINTS_AS_DECLARED

RACE_FK: YES_TO_races.id_AND_EXACT_historical_input_external_races_MAPPING
ENTRY_FK: YES_TO_EXACT_historical_input_external_entries_MAPPING
ENTRY_RACE_MEMBERSHIP_CONSTRAINT: COMPOSITE_FK_internal_race_id_internal_race_entry_id_TO_horses.race_id_id_PLUS_DOMAIN_RECONSTRUCTION
V4_CAPTURE_FK: NO_SEPARATELY_INJECTED_ARCHIVE_CONNECTION; FORMAL_PROVIDER_VALIDATION_AT_CREATE_AND_CONSUME
DATASET_FK: NO_CURRENT_DATASET_TABLE

CREATE_API: SQLiteJRARaceReplaySeedRepository.materialize_seed
CREATE_INPUTS: EXACT_dataset_id+JRATargetRaceNavigationCaptureResult+JRATargetRaceCardResolution+JRATargetRaceSourceCollection+information_cutoff
CREATE_OUTPUT: JRARaceReplaySeed
VALIDATION_ORDER: EXACT_DOMAIN_AND_LINEAGE_VALIDATION_THEN_BEGIN_IMMEDIATE_THEN_FORMAL_MAPPING_REUSE_OR_ATOMIC_CREATION_THEN_SEED_BUILD_CONFLICT_CHECK_INSERT_AND_SINGLE_COMMIT

LOAD_API: SQLiteJRARaceReplaySeedRepository.load_seed
LOAD_KEY: EXACT_jra-race-replay-seed-v1_CONTENT_DIGEST_ID
LATEST_BY_RACE_ALLOWED: NO
RACE_ID_ONLY_LOOKUP_ALLOWED: NO
AMBIGUITY_POLICY: IMPOSSIBLE_FOR_VALID_PK; ANY_DUPLICATE_PARTIAL_CONFLICT_OR_DIGEST_DRIFT_IS_INTEGRITY_ERROR

FINAL_C4D_INPUT_STYLE: ONE_EXACT_JRARaceReplaySeed_PLUS_READ_ONLY_PROVIDERS
FINAL_C4D_PUBLIC_API_SHAPE: build_jra_race_historical_replay(seed=...,target_race_selection_capture_provider=...,target_race_card_capture_provider=...,horse_history_response_provider=...,race_result_response_provider=...,final_win_odds_response_provider=...)

RESTART_REPRODUCIBLE: YES
SAVE_TRANSACTION: ONE_BEGIN_IMMEDIATE_TRANSACTION_COVERING_INTERNAL_ROWS_MAPPINGS_SEED_HEADER_AND_ALL_ENTRIES
PARTIAL_SEED_LOADABLE: NO
PARTIAL_ENTRY_MAPPING_LOADABLE: NO

IMPLEMENTATION_READY: YES_FOR_NEW_PROVIDER_SPECIFIC_SEED_AND_ATOMIC_MATERIALIZATION_BOUNDARY_AFTER_INDEPENDENT_APPROVAL
BLOCKERS: NONE_FOR_NEW_FORMAL_MATERIALIZATION; UNPROVEN_LEGACY_ROWS_ARE_INTENTIONALLY_NOT_ADOPTABLE_AND_C4D_REMAINS_BLOCKED_UNTIL_D0_IS_IMPLEMENTED

LIVE_HTTP_PERFORMED: NO
REAL_TRUSTED_CAPTURE_REQUIRED: NO
REAL_TRUSTED_CAPTURE_PERFORMED: NO
```
