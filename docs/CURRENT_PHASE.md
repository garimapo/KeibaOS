# Current Phase

Status: `APPROVED_FOR_COMMIT`

## Identity and authority

- Phase: `POST_V0_8_DAILY_REPLAY_2`
- Name: `Historical Daily Target Discovery / Completeness Design`
- Base Commit: `dca745c3f8e076ad8bdc9ae4cd320d0a6df7a0ad`
- Branch: `feature/post-v0.8-daily-replay`
- Release baseline: `v0.8.0` at `c08bedb5421b44d63a8bac017699efffca2a4b73`
- Phase type: `DESIGN_ONLY`
- Production implementation: `NOT_AUTHORIZED`
- Test implementation: `NOT_AUTHORIZED`
- Migration / schema / database change: `NOT_AUTHORIZED`
- Stage / commit / push: `NOT_AUTHORIZED`
- `EXECUTE_APPROVED_PHASE`: `NOT_AUTHORIZED`
- Release/tag/history mutation: `FORBIDDEN`

This phase is prepared in the fresh clone
`C:\Users\garim\Desktop\KeibaOS-post-v0.8`. The old Ver0.8 working repository remains
outside this work and must not be changed.

## Objective

Design the audited boundary which, for one exact historical `target_date` and a closed
scope drawn from `JRA/jra_official` and `NAR/nar_official`, can prove that the canonical
target-race tuple is the complete denominator and can construct an immutable
`DailyHistoricalReplayTargetSet`.

This phase is exclusively about target discovery completeness. It does not resolve
`HistoricalInputSnapshot`, result capture, payout capture, or settlement cutoff; build
a schema-v1 replay manifest; invoke replay; persist a daily result; or report ROI.

## Governing invariants

- `NO FUTURE LEAKAGE`
- `NO HINDSIGHT`
- `FAIL CLOSED`
- `NO SILENT FALLBACK`
- `NO HIDDEN SKIP`
- `NO CURRENT-CLOCK CAUSALITY`
- exact provider and race identity
- deterministic ordering independent of SQLite row order
- no inferred race, meeting, venue, or race-number continuity
- no network acquisition inside no-network historical replay
- no raw-HTML reparse where an existing formal domain owns the same facts
- no Ver0.8 contract, tag, or release-history mutation

## Investigation findings

### 1. Legacy `races` population

`scripts/database.py.create_tables()` defines nullable `race_date`, `organization`,
`place`, `race_no`, `race_name`, `start_time`, course/weather fields, `horse_count`,
`deba_table_url`, and `status` beside an autoincrement integer ID. There is no database
`UNIQUE` constraint or index over date, organization, place, or race number.
`race_exists()` and `get_race_id()` use
`(race_date, organization, place, race_no)` with `LIMIT 1`; the application-level check
cannot prove uniqueness and cannot make concurrent or previously duplicated rows
unambiguous. `get_all_races()` merely returns saved rows ordered by
`(race_date, place, race_no)`.

The fresh clone's tracked `database/keiba.db`, inspected read-only, has only `races`,
`horses`, and `sqlite_sequence`; its `races` table has no indexes. Its saved population
does not contain the historical-input external identity mapping schema. These local
facts are not evidence that any provider day is complete.

The table may be used later to look up persisted candidates and reconcile a canonical
provider race to an internal ID. It must not assert that every race was acquired, turn
an absent row into proof that a race did not exist, resolve ambiguity by first row or
insertion order, use display `place` plus `race_no` as provider identity, or supply a
complete daily denominator.

### 2. `historical_input_external_races`

Migration v010 defines exact one-to-one mappings keyed by
`(organization, source_system, external_race_id)` with a reverse unique key on
`(organization, source_system, internal_race_id)`. This is the correct later
reconciliation boundary when the registered schema exists.

It maps identities already known to the application. It contains no target date,
day-level evidence, provider coverage assertion, or evidence provenance. Neither its
rows nor their absence prove target-set completeness. Phase 2 does not create mappings
or apply migrations.

### 3. JRA exact identity and target-card discovery

The formal JRA race identity is:

```text
jra:race:{year}:{venue_code}:{meeting_number}:{meeting_day}:{race_number}
```

`JRAExternalRaceIdentity` and official URL parsers validate that full provider
identity. Venue display text and race number are not substitutes.

Existing pure components provide valuable fragments:

- `jra_target_race_card_locator.py` validates exact root/meeting/race-selection POST
  locators, meeting identity, calendar date, request material, and request digest;
- `jra_target_race_card_discovery.py` validates one supplied race-selection response,
  its exact race-list table, row identities, duplicate/absence states, response digest,
  and observation time, then selects one requested race;
- `jra_target_race_card_resolution.py` resolves exact retained v4 selection and v3
  target-card captures under an explicit upper bound without fallback; and
- `jra_target_race_input_source.py` normalizes one exact accessD race card into formal
  track/entry source records and scheduled start under causal checks.

Their tests prove strict CP932 decoding, request fingerprints, canonical URLs,
identity/date/meeting agreement, duplicate and ambiguous rejection, deterministic row
semantics, causal bounds, and pure injected boundaries.

These components start from a requested `external_race_id` and resolve one known
meeting/race. They do not enumerate and prove every JRA meeting for an arbitrary
historical date. The live navigation service fetches a current root and meeting menu;
those two responses are not retained in the existing capture archive. They may not be
replayed later or backdated as historical day-completeness evidence.

The v4 `target_race_selection` capture can be reused as an exact meeting-day race-list
fragment only when a separate audited historical day envelope proves that the request
belongs to the exact date/meeting, every JRA meeting for that date is represented
exactly once, and the fragment collection is complete. Archive presence or count alone
proves none of those conditions. A future JRA meeting/race-list normalizer must reuse
the existing formal locator/discovery grammar rather than independently reparsing the
same race-selection HTML.

### 4. JRA historical official domains

`jra_historical_past_race_discovery.py` discovers one horse's prior event history;
result, non-start, foreign-provider, and unsupported event kinds are formalized for
prediction evidence. Race-result, target-card, odds, replay-seed, and horse-history
domains are exact race- or request-specific evidence.

They are not historical day/card/race-list completeness evidence. Snapshot rows,
replay seeds, target cards, horse histories, result captures, and payout-bearing result
pages must not be unioned to infer the daily denominator.

### 5. NAR exact identity and historical sources

The formal NAR race identity produced by the trusted input boundary is:

```text
nar:{YYYYMMDD}:{baba_code}:{race_no}
```

It binds exact date, provider course code, and race number. Display place and race
number alone are not identity.

`nar_historical_input_source.py` normalizes one supplied official `DebaTable` response
into exact track/entry records and scheduled start. It validates URL identity, active
course, visible date/race number, and digest, and rejects unsupported cancelled runner
rows. `nar_historical_past_race_discovery.py` formalizes one horse's prior NAR/JRA
starts, proven non-starts, unsupported starts, and proven zero history. This is horse
history, not a target-date race-list source.

The existing NAR capture vocabulary is closed to `deba_table`, `race_mark_table`, and
`horse_mark_info`; the repository loads an exact capture ID or exact evidence tuple.
It has no formal day-level meeting/race-list capture or list-by-date completeness API.

### 6. Legacy NAR current discovery is not historical evidence

`NARProvider.fetch_today_race_list()` fetches the fixed current/live
`TopTodayRaceListMini` endpoint. `NARParser.parse_today_race_list()` and
`parse_race_list()` return mutable legacy values, skip malformed or missing rows,
return empty on missing structure, use display names, and carry no exact bytes, digest,
observation time, capture identity, or coverage assertion. `LocalFetcher` also drops
races without a card URL.

These components may inform later acquisition research, but cannot be used as-is for
historical completeness, cannot backdate a current response, and cannot distinguish a
proven zero-race day from parsing/acquisition failure.

### 7. Candidate official-source findings

The following concrete official families are candidates for the next qualification
phase. They are not approved completeness sources in this design.

JRA candidate:

- official historical JRADB `accessD`/`accessS` family;
- historical race pages which retain day/meeting navigation information;
- the repository's existing strict supplied root, meeting, and race-selection
  navigation domains and exact JRA identity grammar; and
- existing v4 race-selection captures as possible exact meeting-level fragments, not
  as proof of full provider-day coverage merely because some were saved.

Availability of one historical race page or menu does not by itself prove zero-day
semantics, cancellation/non-run semantics, complete meeting coverage, or sufficiently
old historical availability.

NAR candidate:

- official `TodayRaceInfo` family;
- date-qualified venue `RaceList` requests using exact `k_babaCode` plus
  `k_raceDate` identity;
- historical venue-specific full race-list pages; and
- historical official pages which may expose same-day venue navigation.

Legacy `TopTodayRaceListMini` and `NARParser` remain unsuitable as-is: they are
current/live-oriented and mutable, silently skip malformed material, and retain no
immutable completeness provenance.

Before adoption, `POST_V0_8_DAILY_REPLAY_3` must prove for each candidate:

- exact historical-date request semantics and canonical URL/request identity;
- coverage of every provider partition/meeting and complete races within each;
- proven zero-day behavior;
- representation of cancelled, postponed, abandoned, and other non-run targets;
- duplicate and contradictory behavior;
- charset/content requirements, exact response bytes, and digest;
- honest acquisition `observed_at` and whether formal `provider_available_at` exists;
- availability for sufficiently old historical dates;
- deterministic normalization with no silent row skip; and
- no current-page backdating.

Failure to prove any required property leaves that candidate unqualified and the
provider scope fail-closed.

### 8. Provider archives

The repository contains capture code and test-created archives, but no checked-in JRA
or NAR provider archive database. Replay accepts externally supplied archive paths.

The JRA archive can retain race result, horse history, odds, target race card, and one
meeting-day race-selection response. The NAR archive retains individual card/result/
horse-history families. Neither schema has an immutable provider-day coverage record.
Rows grouped by date, URL, venue, or race number are only an observed subset. Missing
rows cannot mean missing races, and a contiguous `1..12` sequence proves nothing about
complete meeting or provider-day coverage.

### 9. Cancelled, postponed, abandoned, and non-run races

A race can belong to the official historical target set while being unsuitable for
normal replay. That differs from a race which was never a target. Individual runner
cancellation also differs from whole-race non-run.

Discovery must retain every formally listed race and its provider-native race-level
status/disposition evidence. It must never remove a cancelled, postponed, abandoned,
or other non-run target. Target-set membership and later replay execution
classification are separate responsibilities. Unknown or contradictory native status
must not fall back to a normal race and must not make the race disappear.

This phase does not approve a provider-neutral closed disposition enum or any JRA/NAR
native-status mapping. Exact source semantics have not yet been qualified. The future
Official Source Qualification phase must inspect the real provider representations and
return the proposed vocabulary/mapping for ChatGPT review before it can become a
production contract.

### 10. Multiple meetings and venues

Completeness is hierarchical:

```text
closed provider scope
  -> each provider in scope
  -> every official meeting/venue partition on target_date
  -> every canonical race in each partition
```

Known venue lists, saved venues, or expected counts cannot prove which venues met on a
date. Each provider bundle must positively prove the complete partition set and the
complete race set inside every partition.

### 11. Baseline capability conclusion

At the base commit there is no formal immutable historical provider-day source which
proves complete meeting coverage for either provider. Therefore the only safe current
outcome for an attempted construction is `TARGET_DISCOVERY_INCOMPLETE`.

This is a design finding, not authorization to scrape pages, add models, widen archives,
add migrations, or implement fallback behavior.

## Formal source-of-truth decision

The formal normalized input is one shared provider-neutral immutable contract:
`HistoricalDailyTargetEvidenceBundle`. Each bundle contains exactly one provider
identity. Provider-specific adapters/source normalizers produce this common contract;
separate JRA/NAR bundle classes are not proposed unless the Official Source
Qualification phase proves a semantic need.

The raw exact official response/capture remains the primary source evidence. The
normalized bundle is its immutable audited projection, not independent primary
evidence. It must retain exact capture/reference identity, digest, source/request
identity, and provenance sufficient to trace and exact-load the raw source. It is not
the main database, snapshot set, result/card capture collection, or a query over
whatever archive rows happen to exist.

Each bundle must assert and prove for exactly one provider:

- exact `target_date` and provider identity;
- the complete provider meeting/venue partition set, including explicit proven zero;
- the complete canonical race tuple in every partition;
- exact scheduled start for every normal replay-candidate target, optional exact
  original scheduled start when formal evidence supplies it for an exceptional target,
  and no inferred replacement when it does not;
- provider-native disposition/status evidence or its exact reference for every target,
  without a prematurely normalized closed enum;
- exact evidence/capture and source/request identities;
- exact content digests and honest aware observation time;
- provider-issued availability time only when formally supplied; and
- an exact coverage relation proving that no partition/list fragment is missing.

`DailyHistoricalReplayTargetSet` becomes the authoritative denominator only after the
bundles exactly cover the requested provider scope and pass all cross-evidence checks.
The raw official evidence remains the source facts; each bundle and the target set are
successive immutable audited projections with exact traceability back to that source.

No existing domain is widened to pretend it proves this. The shared bundle is necessary
because no current model expresses positive provider-day and partition coverage plus a
proven zero-day state. Provider-specific facts remain in evidence/reference values
rather than creating unproven provider-specific bundle types.

## Shared and provider-specific responsibilities

Provider-neutral logic owns exact scope/date coverage, immutable tuple construction,
uniqueness/conflict checks, proven-zero distinction, canonical ordering, target-set
digest, and the global `TARGET_DISCOVERY_INCOMPLETE` boundary.

Provider adapters own official historical source validation, native meeting/race
identity, complete partition/list proof, exact scheduled-start extraction when the
source supplies it, retention of provider-native disposition/status evidence, and
projection to the one shared bundle contract. They do not invent missing times or
statuses, query legacy races, resolve snapshots or settlement evidence, build
manifests, invoke replay, or report results.

For JRA, exact identities, request locators, v4 identity, and formal race-selection
parsing are reusable fragments; an audited historical all-meeting envelope is still
required. For NAR, a formal historical day/meeting/race-list capture and normalizer are
required. Exact source acquisition for both providers must return for ChatGPT review
before implementation authorization.

## Minimal proposed immutable values

### `DailyHistoricalReplayProviderScope`

A non-empty duplicate-free canonical tuple containing only exact identities from:

```text
JRA/jra_official
NAR/nar_official
```

It is sorted by `(organization, source_system)`. Caller order has no semantic effect;
aliases, display names, unknown organizations, and partial identities are invalid.

### `DailyHistoricalReplayTarget`

Each target minimally retains:

```text
provider_identity
external_race_id
scheduled_start_at: datetime | None
provider_disposition_evidence_or_reference
```

For a normal scheduled/replay-candidate target, `scheduled_start_at` is an exact aware
datetime and is canonicalized to UTC. For a non-run or exceptional target, an exact
original scheduled start is retained only when formal official evidence supplies it;
otherwise `None` is required. Display text, an expected timetable, neighboring race
times, race number, current time, or local database data must not fill the value.

The approved Phase 1 contract
`selection_upper_bound = audited_target.scheduled_start_at` applies only to a target
which may become a later replay candidate and has a formally proven exact
`scheduled_start_at`. A target with `scheduled_start_at is None` remains in the daily
denominator but is ineligible for `LATEST_CAUSAL_IN_DATASET` and must never reach
snapshot selection. Later Evidence Resolver classification owns that exclusion from
the executable projection without removing target-set membership.

`provider_disposition_evidence_or_reference` preserves auditable provider-native status
semantics. It is not a Phase 2 closed normalized enum. Membership must survive non-run
or unknown exceptional status; unknown/contradictory status must not fall back to a
normal race. A provider-neutral enum and native mapping require source qualification
and independent review.

No internal SQLite race ID is present. Internal reconciliation belongs to Phase B and
cannot define the denominator.

### `DailyHistoricalReplayCompletenessEvidence`

Each evidence reference minimally retains:

```text
provider_identity
evidence_kind_and_version
exact_capture_or_reference_identity
canonical_source_or_request_identity
content_sha256
observed_at
provider_available_at_when_formally_supplied
coverage_identity
```

`coverage_identity` binds date, provider, and partition/list. `observed_at` is the exact
time KeibaOS actually acquired/observed the official historical completeness evidence.
It may be later than `target_date`: evidence for a 2025 historical day acquired in 2026
must retain its honest 2026 observation and must never be backdated to 2025.

Completeness `observed_at` is orchestration/audit metadata. It is not prediction
`information_cutoff`, snapshot selection upper bound, `settlement_information_cutoff`,
provider `available_at`, or race `scheduled_start_at`, and must never substitute for
any of them. Daily completeness evidence must not flow into `PredictionPipeline` or
`BetStrategy`.

`provider_available_at` is retained only when the official source formally supplies
it. It is never inferred from `observed_at`, insertion/storage/file metadata, archive
time, target date, or current time. `stored_at` may be repository metadata but is not
historical availability or prediction/settlement causal time.

Use of later-acquired evidence also requires the next qualification phase to prove that
the historical source formally represents the requested date and does not silently
erase cancelled, postponed, abandoned, or other non-run targets.

### `DailyHistoricalReplayTargetSet`

The set minimally retains:

```text
target_date
provider_scope
canonical target_races
canonical completeness_evidence
content_sha256
```

Construction validates exact scope coverage, date/identity agreement, uniqueness,
auditable provider-native disposition evidence, deterministic ordering, and digest
reproducibility. `content_sha256` is the one canonical deterministic content digest of
the immutable target set. A later persistence/artifact phase may derive a versioned
external identity such as `daily-target-set-v1:<content_sha256>` without changing the
digest semantics. This phase designs no durable storage.

The value is immutable, frozen, and slotted. Mutable DTOs, ROI, internal
reconciliation, snapshot/settlement identities, and database paths do not belong here.

## Proven zero-race day

An empty target tuple is valid only when every provider in the closed scope has
positive immutable evidence explicitly proving zero meetings/races for the exact date.

```text
complete provider coverage + explicit zero assertions -> audited empty target set
missing/invalid/ambiguous provider evidence          -> TARGET_DISCOVERY_INCOMPLETE
```

Empty database queries, empty parser output, absent captures, HTTP absence, missing
archives, and zero matching snapshots/results never prove a zero-race day.

## Canonical ordering

```text
provider_scope: (organization, source_system)
targets:        (organization, source_system, external_race_id)
evidence:       (organization, source_system, coverage_identity,
                 evidence_kind_and_version,
                 canonical_source_or_request_identity,
                 exact_capture_or_reference_identity)
```

Provider-specific official ordering may be retained as evidence/provenance, but it does
not determine provider-neutral canonical set order or `content_sha256`. Ordering never
depends on nullable `scheduled_start_at`, provider display place, caller/dictionary
order, SQLite row/internal ID, insertion order/time, archive filename, or current clock.

## Duplicate and contradictory evidence

- Duplicate provider scope identity is invalid.
- Duplicate target identity is rejected even when visible facts agree; no silent dedup.
- One race identity with differing date, exact start, native status evidence,
  partition, digest, or lineage is contradictory.
- Overlapping or missing partition coverage is incomplete/contradictory.
- Competing bundles have no latest, row-ID, filename, digest, or time tie-break.

No such state produces a target set. The outward whole-request failure remains
`TARGET_DISCOVERY_INCOMPLETE`, with deterministic reasons such as
`MISSING_PROVIDER_COVERAGE`, `MISSING_PARTITION_COVERAGE`,
`DUPLICATE_TARGET_EVIDENCE`, `CONTRADICTORY_TARGET_EVIDENCE`,
`UNQUALIFIED_PROVIDER_STATUS`, or `INVALID_COMPLETENESS_EVIDENCE`. These are audit
details, not a prematurely frozen disposition enum or race-level replay
classifications.

## Acquisition and replay separation

```text
network-capable historical acquisition/preparation
  -> validate official provider responses
  -> persist exact immutable evidence without backdating
  -> freeze HistoricalDailyTargetEvidenceBundle
  -> build/freeze DailyHistoricalReplayTargetSet

no-network historical replay preparation/execution
  -> exact-load and revalidate frozen target set/evidence
  -> later Phase B evidence resolution
  -> later Phase C schema-v1 manifest construction
  -> later Phase D existing replay invocation
```

Replay never fetches missing evidence. Acquisition failure cannot trigger live fallback.
A current page cannot be asserted as a past observation unless it is a formal historical
view for that date and the adapter proves the coverage contract.

## Storage and migration decision

The baseline has no adequate day-completeness schema. A future implementation will
likely need provider capture/source domains and durable content-addressed storage, but
this phase does not choose DDL before exact official sources are proven.

No migration is added or applied. Main DB migrations are not owned by discovery. Any
future schema, migration, repository, artifact format, or archive-family change requires
separate PREPARE, ChatGPT review, approval, implementation contract, and tests. Existing
capture schemas must not be widened for convenience.

## Phase gates

Phase 2 remains design-only. Approval does not authorize implementation. The
recommended next phase, which is recorded but not started, is:

```text
Phase: POST_V0_8_DAILY_REPLAY_3
Name: Historical Daily Official Source Qualification
Type: RESEARCH_AND_DESIGN_ONLY
```

Its future purpose is to qualify the candidate JRA historical JRADB navigation/
race-selection family and NAR date-qualified `TodayRaceInfo`/`RaceList` family for
complete partition/race coverage, proven zero-day behavior, non-run semantics, exact
identity, historical availability, charset/content, exact bytes/digest, honest
provenance times, and deterministic no-skip normalization.

Phase 3 requires its own PREPARE, ChatGPT review, and approval. It must not implement
target discovery or durable storage. A later implementation phase remains separately
gated. Evidence Resolver work must not start before Daily Target Discovery sources are
formally qualified. Manifest builder, orchestrator, persistence, reporting, and
strategy comparison also remain out of scope and separately gated.

## Unresolved questions requiring later review

1. Can the candidate historical JRA JRADB navigation/race-selection family prove all
   meetings on one date and a genuine zero-meeting day without backdating a current
   root/menu?
2. Can the candidate NAR date-qualified `TodayRaceInfo`/`RaceList` family prove all
   venues/races on one date, including zero and non-run membership?
3. What exact provider status and identity behavior applies to a postponed race,
   especially when moved to another date?
4. Do official sources provide formal `available_at`, or must audit retain only honest
   acquisition `observed_at` without an availability claim?
5. After sources are qualified, what separately reviewed storage boundary is necessary
   without changing `content_sha256` semantics?

These questions permit no inference. Until each provider in scope has an approved
answer, construction fails closed as `TARGET_DISCOVERY_INCOMPLETE`.

## Current phase Allowed Files

Only:

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Forbidden Files and actions

All production code, tests, migrations, schemas, CLI, databases, archives, fixtures,
release/tag/history files, and every file outside the two Allowed Files are forbidden.
Provider acquisition, implementation, test addition, migration/database mutation,
archive mutation, `EXECUTE_APPROVED_PHASE`, stage, commit, push, and transition to Phase
3 or later are also forbidden. `database/keiba.db` and `logs/` must never be staged or
committed.

## Required verification

No tests are added or run because this is a design-only approval correction. Required
checks are:

```text
git diff --check
git diff --name-only
git status --short
git diff --cached --name-only
```

Only the two Allowed Files may be changed, with no staged files.

## Stop condition

Stop with `APPROVED_FOR_CODEX` after applying only the independent-review corrections
and running the required checks. Wait for ChatGPT final confirmation and explicit
commit authorization. Do not execute, implement, test, stage, commit, push, acquire
provider data, or advance.
