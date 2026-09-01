# Current Phase

Status: `APPROVED_FOR_COMMIT`

## Identity and authority

- Phase: `POST_V0_8_DAILY_REPLAY_3`
- Name: `Historical Daily Official Source Qualification`
- Base Commit: `873ab8eb854716c93886ed689cee93c1ef8bfd23`
- Branch: `feature/post-v0.8-daily-replay`
- Release baseline: `v0.8.0` at `c08bedb5421b44d63a8bac017699efffca2a4b73`
- Phase type: `RESEARCH_AND_DESIGN_ONLY`
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

Research official historical public JRA and NAR sources and determine, provider by
provider, whether an exact historical date's complete meeting/venue and target-race
denominator can be proven with immutable auditable evidence. Freeze a conceptual
single- or composite-source contract only when every required property is positively
qualified; otherwise return `UNPROVEN` or `UNQUALIFIED` without inference.

This phase performs read-only public-source research and contract design only. Research
responses are not replay evidence, are not archived or backdated, and are not written
to repository databases, logs, fixtures, or provider archives. Formal target discovery,
Evidence Resolver, manifest builder, replay, persistence, tests, and migrations remain
unauthorized.

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

## Inherited Phase 2 investigation baseline

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

Phase 3 research responses were honestly observed during research, but because they
were not formally captured, qualified, or persisted as
`HistoricalDailyTargetEvidenceBundle` evidence, their timestamps are not formal
completeness-evidence `observed_at` values for a replay dataset. A future authorized
acquisition must record the exact retrieval time of its own immutable capture as the
honest `observed_at`; research time, target date, or a time copied from this document
must never be substituted or backdated.

Completeness `observed_at` is orchestration/audit metadata. It is not prediction
`information_cutoff`, snapshot selection upper bound, `settlement_information_cutoff`,
provider `available_at`, or race `scheduled_start_at`, and must never substitute for
any of them. Daily completeness evidence must not flow into `PredictionPipeline` or
`BetStrategy`.

Formal `provider_available_at` handling retains the exact value only when the tested
official source contract supplies it. When the tested contract does not, the value is
`None` and no substitute is permitted. This is a fail-closed rule for the tested
candidate, not a permanent guarantee that every future response family lacks such a
field. It is never inferred from `observed_at`, insertion/storage/file metadata,
archive time, target date, HTTP `Date`, or current time. `stored_at` may be repository
metadata but is not historical availability or prediction/settlement causal time.

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

## Phase 3 research method and evidence boundary

Repository contracts were inspected before network research. Public-source research was
then limited to `jra.go.jp` and `keiba.go.jp`; search results were used only to locate
official material. Formal conclusions below rely on official responses/pages, never on
search snippets or third-party racing sites.

All responses observed during this phase are research material only. They were inspected
in memory or through the browsing boundary and were not saved to the repository, main
database, logs, fixtures, or provider archives. Phase 3 research responses were honestly
observed during research, but because they were not formally captured, qualified, or
persisted as `HistoricalDailyTargetEvidenceBundle` evidence, their timestamps are not
formal completeness-evidence `observed_at` values for a replay dataset. A future
authorized acquisition must record its exact retrieval time as honest `observed_at`.
Neither research time nor target date may be backdated or substituted as formal
`observed_at`, provider `available_at`, prediction cutoff, snapshot upper bound,
settlement cutoff, or scheduled start.

One page need not prove every property. A future source may be composite only when an
exact provider-day envelope proves all partitions, one exact list fragment proves every
race per partition, optional native status material preserves exceptional membership,
and the coverage relation binds every fragment exactly once. Page accumulation or
apparent agreement is not coverage proof.

### Denominator semantics which every composite must preserve

Qualification must distinguish these facts rather than collapse them into one
"race date" concept:

1. races actually conducted on `target_date`;
2. races officially scheduled for `target_date` but cancelled there;
3. a cancelled meeting or race conducted on a formally declared substitute date; and
4. the original-date identity versus replacement-date identity and their official
   relation.

The denominator retains an original target only when formal source evidence supplies
its exact identity. A schedule-level statement that a meeting was cancelled cannot be
expanded into guessed race numbers or synthetic original race identities. Likewise, a
substitute day's races are not silently copied back to the original date or treated as
the same identities merely because the program appears similar. Missing identity or
coverage evidence yields `TARGET_DISCOVERY_INCOMPLETE`.

## Exact official source candidates investigated

### JRA official candidates

The official families actually inspected were:

- `https://www.jra.go.jp/JRADB/accessS.html`, including the past-results search POST
  family, month-selection CNAME, meeting/race-selection CNAME, and direct race-result
  GET family;
- `https://www.jra.go.jp/JRADB/accessD.html`, including the repository's root,
  meeting-selection, race-selection, and direct target-card grammar;
- historical annual `Racing Schedule` PDFs linked by the official racing calendar;
- year-specific `競馬番組一覧およびルール`, the official `開催日割表`, and the
  official `開催日割および重賞競走等について` material;
- historical static daily program pages under
  `https://www.jra.go.jp/keiba/calendarYYYY/YYYY/M/MMDD.html`; and
- official calendar and cancellation semantics in JRA FAQ, including the rule that a
  cancelled meeting may be conducted later with or without a new entry process.

The exact accessS research navigation was:

```text
POST pw01skl00999999/B3
  -> official year/month selectors and opaque month-tail map
POST pw01skl10YYYYMM/<officially supplied tail>
  -> historical meeting-selection CNAMEs embedding exact date/venue/meeting/day
POST one pw01srl10... CNAME
  -> one meeting/day race-selection response
GET one directly supplied pw01sde... URL
  -> one exact race-result response
```

Opaque suffixes are never generated or guessed. The accessD repository path is useful
for strict request grammar and exact race identity, but it is aimed at target cards and
known-race lookup. Historical accessD cards can report that publication has ended; the
v4 race-selection capture alone does not prove an historical provider-day denominator.

The official FAQ directs users to the racing calendar for monthly schedules and its
annual schedule PDF for yearly schedules. The 2024 year-specific program page provides
an exact `開催日割表` and an official document stating that the year's schedule was set
from January 6 through December 28. Those are formal planned-schedule sources, not by
themselves an after-the-fact actual-meeting ledger. Static daily pages explicitly say
their contents are pre-announced plans and may receive cancellation, postponement, or
other changes. The 2019 daily pages do retain the Tokyo October 12 cancellation and
October 15 substitute, while accessS contains actual-result navigation for Kyoto on the
12th and Tokyo on the 15th.

Two JRA composite candidates were compared:

```text
Candidate JRA-A
historical annual/period schedule
  -> planned date and meeting partitions
  -> exact official cancellation/substitute adjustment material
  -> accessS meeting/race fragments for actual or replacement dates

Candidate JRA-B
historical accessS month envelope
  -> accessS meeting/race fragments
  -> annual schedule cross-check
  -> exact official cancellation/substitute adjustment material
```

JRA-A is semantically safer because it starts from scheduled membership rather than
results, but no inspected official contract proved an exhaustive historical adjustment
index or how every original race identity is retained when an entire meeting is moved.
JRA-B starts from actual results and therefore cannot recover a fully cancelled original
denominator by absence. Neither candidate is qualified.

### NAR official candidates

The official families actually inspected were:

- `https://www.keiba.go.jp/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop` with exact
  `k_year` and `k_month`, including all displayed racecourse rows, date columns,
  ordinary/night/dirt-grade marks, and the substitute-day `△` mark;
- `https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceList` with exact historical
  `k_babaCode` and `k_raceDate`;
- same-day venue navigation emitted by historical RaceList responses;
- exact per-race `DebaTable` and `RaceMarkTable` links; and
- official `seisekipdf` result books and official cancellation notices only as
  supplemental provider-native non-run research, not as standalone denominators; and
- the NAR FAQ statement that the MonthlyConveneInfo path exposes all race results
  conducted since 1998.

The exact monthly request identity tested was:

```text
GET /KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop
    ?k_year=YYYY&k_month=M
```

It returned a historical year/month table with fixed date columns and displayed venue
rows. Marks link to the corresponding historical venue/date RaceList. The legend defines
`●`, `☆`, `Ｄ`, and `△`, and warns that disaster-related schedule changes may occur.
It does not define a blank cell as an audited assertion of actual zero and does not say
that the table is an immutable post-event actual-ledger snapshot.

For ordinary tested days the marked venue set exactly matched the RaceList same-day
navigation set:

```text
2025-05-05: Obihiro, Morioka, Funabashi, Kanazawa, Nagoya, Sonoda
2024-09-01: Obihiro, Morioka, Kanazawa, Saga
2025-08-30: Obihiro, Funabashi, Saga
```

This agreement is useful research but not a general exhaustiveness proof. The 2017-12
table marks Kanazawa on December 19 with `△`; official schedule material describes the
December 17 cancellation and December 19 substitute. However the monthly cell for the
cancelled original date is blank, so MonthlyConveneInfo alone does not preserve original
race identities. Conversely, the 2025-12-26 table still marks Kanazawa `●` although the
historical RaceList states that the whole meeting was cancelled with no substitute.
Thus a mark is scheduled/meeting membership evidence, not proof that races were
conducted, and native RaceList/status evidence remains necessary.

The date-qualified RaceList page is a plausible venue-day fragment. The visible title
and heading bind the requested historical date and venue, direct rows enumerate races,
and same-day navigation exposes other venues. However, no inspected official contract
states that the navigation is an exhaustive provider-day partition envelope or that an
error/empty response positively means zero venues. Therefore it is not yet an approved
provider-day source.

The exact request spelling is also unresolved. A literal `YYYY/MM/DD` request succeeded
in direct research while percent-encoded slash requests produced an official error in
the same direct client path, and official examples use both zero-padded and canonical
decimal `k_babaCode` spellings. A future contract must freeze request bytes, redirects,
host choice, slash encoding, and baba-code canonicalization rather than assuming URL
equivalence.

The stronger but still unapproved NAR composite candidate is:

```text
historical MonthlyConveneInfo year/month envelope
  -> marked venue partitions for exact target_date
  -> one exact date-qualified RaceList fragment per marked venue
  -> provider-native cancellation/substitute status evidence when needed
```

It improves on RaceList navigation as the proposed envelope and can preserve a
whole-day-cancelled venue when the monthly mark remains present. It remains unqualified
because blank-cell zero semantics, the table's exhaustive actual-versus-planned contract,
original identity on moved meetings, and complete adjustment behavior are not formally
proven.

## Representative historical cases

### JRA cases

1. `2024-09-01`, ordinary three-meeting date:
   `https://www.jra.go.jp/keiba/calendar2024/2024/9/0901.html` lists Niigata,
   Chukyo, and Sapporo with twelve planned races each. The page itself warns that it is
   a pre-announced program subject to cancellation, postponement, and changes.
   accessS monthly search independently returned three exact meeting CNAMEs for the
   date, and direct race-result pages retained same-day meeting and race navigation.
2. `2024` annual schedule and `2024-01-02`, zero-like normal date:
   the official year-specific program page exposes an annual `開催日割表`, and the
   official schedule decision states that the year begins with Nakayama and Kyoto on
   January 6. This positively establishes the planned first meeting date, but the
   inspected sources did not define every unlisted calendar date as a post-event
   audited actual zero or prove an exhaustive no-adjustment ledger. January 2 therefore
   remains a useful zero candidate, not a qualified zero contract.
3. `2020-01` and `2015-01`, older availability:
   exact accessS month requests returned historical meeting-selection responses.
   This proves only observed availability to the tested floor of January 2015, not the
   required retention horizon or a permanent SLA.
4. `2019-10-12` and `2019-10-15`, cancellation/substitute case:
   `https://www.jra.go.jp/keiba/calendar2019/2019/10/1012.html` states that the
   Tokyo meeting was cancelled because of the typhoon and the substitute meeting was
   held on `2019-10-15`, while Kyoto remained on `2019-10-12`. The accessS October
   response contains Kyoto on the 12th and Tokyo on the 15th, and the official October
   15 program contains the replacement Tokyo card. The JRA FAQ says a cancelled meeting
   may sometimes be conducted later without redoing entries when formal conditions are
   met. These sources are consistent, but they do not by themselves expose an exhaustive
   adjustment index or settle original-date race identity and replacement identity for
   every cancellation mode.

No JRA source contract was established which positively binds every ordinary unlisted
date to actual zero after all possible adjustments. Missing daily pages or absence from
accessS are never accepted as zero evidence.

### NAR cases

1. `2025-05-05`, ordinary multi-venue date:
   venue RaceList pages exposed same-day navigation for Obihiro, Morioka, Funabashi,
   Kanazawa, Nagoya, and Sonoda and listed each inspected venue's race rows.
2. `2024-09-01`, ordinary multi-venue date:
   `https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceList?k_babaCode=32&k_raceDate=2024/09/01`
   exposed Obihiro, Morioka, Kanazawa, and Saga and listed twelve Saga races.
3. `2020-01-03`, older date:
   the Saga RaceList remained available and exposed six same-day venues plus ten Saga
   races. The monthly site also exposes year selection back to 1998 and the FAQ says all
   conducted race results since 1998 are viewable, but direct representative RaceList
   qualification was tested only to January 2020. This is an observed floor, not a
   required-retention guarantee.
4. `2025-08-30`, whole-race cancellation case:
   `https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceList?k_babaCode=19&k_raceDate=2025/08/30`
   retained all twelve Funabashi rows and stated that races 10 onward were cancelled
   because of lighting trouble. The official result book also marks races 10 through 12
   as `競走取止め`.
5. `2026-04-04`, whole-race cancellation case:
   `https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceList?k_babaCode=31&k_raceDate=2026/04/04`
   retained all twelve Kochi rows and stated that race 4 onward was cancelled, with no
   substitute meeting. The official result book preserves the affected race identities.
6. `2025-12-26`, whole-meeting cancellation with no substitute:
   MonthlyConveneInfo retains a normal `●` mark for Kanazawa, while the historical
   RaceList states that the meeting was cancelled because of snow and no substitute
   would be held. This proves that the monthly mark is not actual-conducted semantics
   and that composite native status evidence is required.
7. `2017-12-17` and `2017-12-19`, substitute case:
   the historical monthly table leaves the original Kanazawa date blank and marks the
   substitute date `△`; official historical schedule material records the cancellation
   and substitute relation. This preserves meeting-level adjustment evidence but does
   not prove original race identities.
8. `2020-03-09`, all-blank provider-day candidate:
   every displayed venue row is blank in the exact March 2020 monthly table. The legend
   defines positive marks but not blank-cell semantics, and the FAQ's statement about
   all conducted results does not explicitly turn every blank column into an immutable
   audited actual-zero assertion. It is therefore not a proven-zero contract.
9. The earlier direct `2025-01-01` no-racing attempt was invalid as a zero case: the
   corrected monthly table shows racing at Kawasaki, Nagoya, and Kochi. A generic
   RaceList error for an arbitrarily chosen venue never proves provider zero.

No cancellation date above was invented. The official pages themselves identify the
cancelled meetings/races.

## Response bytes, charset, digest, and provenance findings

The inspected JRA accessS, accessD, and calendar responses returned exact non-empty
bytes, declared `<meta charset="Shift_JIS">`, and decoded strictly as CP932. Existing
JRA domains already use exact bytes, CP932, request fingerprints, response SHA-256,
aware observation time, and exact-load capture identities. HTTP `Content-Type` in the
inspected responses was `text/html` without a formal provider publication time.

The inspected NAR RaceList responses returned exact non-empty bytes with HTTP and HTML
UTF-8 declarations. Existing formal NAR per-race capture domains already require strict
UTF-8, exact canonical URL, response SHA-256, aware observation time, and exact-load
identity, but RaceList is not in their closed page-kind vocabulary.

Both source families are technically content-digestible. Research SHA-256 values only
fingerprint the bytes observed during research; they are not formal captures and are not
placed into a historical dataset. The tested JRA and NAR candidates exposed no formal
provider publication timestamp in their inspected HTML/HTTP contracts. Future
`FORMAL_PROVIDER_AVAILABLE_AT_HANDLING` therefore retains `None` for these tested
contracts and fails closed against substitutes. This finding is not a permanent claim
about all future provider families. HTTP response `Date`, research time, filesystem
time, database insertion time, and page target date must not be substituted.

## Existing formal repository-domain reuse

JRA reuse candidates:

- `JRAExternalRaceIdentity` and exact `jra:race:year:venue:meeting:day:race` grammar;
- strict CP932 supplied-response domains;
- request locator fingerprints and opaque-tail preservation;
- exact root/meeting/race-selection validation patterns;
- strict one-row validation, duplicate rejection, and no arbitrary locator tie-break;
- v1/v3/v4 exact-byte capture and exact repository-load semantics.

The accessD target-card locator/discovery cannot simply be relabeled as accessS daily
discovery. A future accessS month/meeting normalizer needs a separately reviewed formal
domain while reusing the identity and strict-validation primitives.

NAR reuse candidates:

- exact `nar:YYYYMMDD:babaCode:raceNo` historical race identity;
- exact date/baba/race query validation used by the per-race historical input source;
- strict UTF-8 response and immutable response-digest/capture primitives;
- exact repository load and fail-closed reconstruction;
- provider-native actual-start/non-start distinction in horse-history discovery.

`NARProvider`, `TopTodayRaceListMini`, and `NARParser` are not reusable as the formal
normalizer: they use current/live acquisition, write logs, rely on apparent encoding and
Python hash filenames, return mutable legacy models, skip malformed rows, and synthesize
zero/default values. A future RaceList normalizer must validate every direct row and
fail the whole fragment on malformed, missing, duplicate, or contradictory material.

No existing formal domain parses NAR MonthlyConveneInfo or a JRA annual schedule plus
adjustment relation. Exact-byte/digest/identity primitives can be reused, but new
source-specific normalizers and an explicitly reviewed composite coverage relation
would be required in a later phase. This phase does not implement them.

## Qualification matrix

`QUALIFIED` below is limited to the exact property and tested source family stated in
the notes. It does not imply overall provider qualification or a permanent availability
guarantee.

Property meanings are fixed as follows for this matrix:

- `HISTORICAL_DATE_ADDRESSABLE`: an exact historical date participates in an official
  source/request identity; this does not imply zero or complete coverage.
- `PROVIDER_DAY_PARTITION_COMPLETE`: positive official evidence exhaustively enumerates
  every provider meeting/venue partition for that date.
- `PARTITION_RACE_LIST_COMPLETE`: one partition source exhaustively enumerates its
  target race identities without a known-race bootstrap.
- `PROVEN_ZERO_SUPPORTED`: official evidence positively distinguishes actual provider
  zero from missing, empty, error, or unobserved evidence.
- `NON_RUN_MEMBERSHIP_PRESERVED`: cancelled/postponed/abandoned/non-run membership and
  provider-native status are retained without silent normal fallback.
- `EXACT_PROVIDER_IDENTITY`: source evidence binds the closed provider identity.
- `EXACT_RACE_IDENTITY`: each target binds the exact provider-native race identity.
- `CANONICAL_REQUEST_IDENTITY`: exact endpoint, method, parameters, redirects, and
  opaque supplied tokens can be frozen without guessed equivalence.
- `EXACT_RESPONSE_BYTES_CAPTURABLE`: the official response can be captured as exact
  immutable bytes.
- `CHARSET_DETERMINISTIC`: strict decoding is determined by the tested contract.
- `CONTENT_DIGEST_POSSIBLE`: a cryptographic digest over exact source bytes is possible.
- `HONEST_OBSERVED_AT`: future acquisition can record its own exact aware retrieval time
  without backdating; Phase 3 research timestamps are not dataset evidence.
- `FORMAL_PROVIDER_AVAILABLE_AT_HANDLING`: a formal provider timestamp is retained when
  supplied and otherwise exactly `None`; no substitute is invented.
- `OBSERVED_AVAILABLE_TO_TESTED_FLOOR`: read-only research observed the candidate at the
  stated oldest tested date only; this is not retention.
- `REQUIRED_RETENTION_HORIZON_SUPPORTED`: the source formally guarantees or has been
  qualified across the replay system's required historical horizon.
- `NO_SILENT_SKIP_NORMALIZATION_POSSIBLE`: a formal strict normalizer can reject any
  malformed, omitted, duplicate, or contradictory row rather than skip it.
- `EXISTING_FORMAL_DOMAIN_REUSE`: approved identity/capture/strict-validation primitives
  can be reused without raw-domain reimplementation.
- `COMPOSITE_COVERAGE_RELATION_DEFINABLE`: exact source identities and rules can bind one
  exhaustive envelope to every required fragment and adjustment exactly once.

| Property | JRA | NAR | Research basis |
|---|---|---|---|
| `HISTORICAL_DATE_ADDRESSABLE` | `QUALIFIED` | `QUALIFIED` | JRA year-specific racing calendar/day pages and NAR year/month table plus exact date columns give official historical date identities; completeness and zero are separate. |
| `PROVIDER_DAY_PARTITION_COMPLETE` | `UNPROVEN` | `UNPROVEN` | JRA planned schedule lacks exhaustive adjustment coverage; NAR monthly rows are promising but no formal statement proves an exhaustive actual provider-day ledger. |
| `PARTITION_RACE_LIST_COMPLETE` | `UNPROVEN` | `QUALIFIED` | JRA race fragments remain entangled with planned/cancelled coverage; NAR venue RaceList directly retained all rows in ordinary and cancellation cases. |
| `PROVEN_ZERO_SUPPORTED` | `UNPROVEN` | `UNPROVEN` | JRA planned first-date evidence and NAR 2020-03-09 all-blank column do not formally define post-adjustment actual zero. |
| `NON_RUN_MEMBERSHIP_PRESERVED` | `UNPROVEN` | `UNPROVEN` | Exact cancellation/substitute examples are preserved across composite material, but all native variants and original identities are not qualified. |
| `EXACT_PROVIDER_IDENTITY` | `QUALIFIED` | `QUALIFIED` | Closed `JRA/jra_official` and `NAR/nar_official` identities already exist. |
| `EXACT_RACE_IDENTITY` | `QUALIFIED` | `QUALIFIED` | Existing exact JRA and NAR external race grammars bind provider-native identity. |
| `CANONICAL_REQUEST_IDENTITY` | `QUALIFIED` | `UNPROVEN` | JRA annual URLs and opaque CNAMEs are official-supplied; NAR RaceList slash encoding, redirects, host, and baba spelling remain unresolved even though MonthlyConveneInfo year/month is exact. |
| `EXACT_RESPONSE_BYTES_CAPTURABLE` | `QUALIFIED` | `QUALIFIED` | Exact response bytes were obtainable over official HTTPS. |
| `CHARSET_DETERMINISTIC` | `QUALIFIED` | `QUALIFIED` | JRA inspected pages declare Shift_JIS/strict CP932; NAR RaceList declares UTF-8. |
| `CONTENT_DIGEST_POSSIBLE` | `QUALIFIED` | `QUALIFIED` | SHA-256 over exact response bytes is possible for both. |
| `HONEST_OBSERVED_AT` | `QUALIFIED` | `QUALIFIED` | Acquisition owns an aware receipt time and never backdates it. |
| `FORMAL_PROVIDER_AVAILABLE_AT_HANDLING` | `QUALIFIED` | `QUALIFIED` | Tested contracts expose no formal value, so future capture retains exact `None`; this is not a guarantee for other source families. |
| `OBSERVED_AVAILABLE_TO_TESTED_FLOOR` | `QUALIFIED` | `QUALIFIED` | JRA accessS January 2015 and NAR RaceList January 2020 were observed; NAR monthly year selection reaches 1998, but direct fragment qualification was not extended to that floor. |
| `REQUIRED_RETENTION_HORIZON_SUPPORTED` | `UNPROVEN` | `UNPROVEN` | No required replay horizon or provider retention guarantee has been frozen and tested end-to-end. |
| `NO_SILENT_SKIP_NORMALIZATION_POSSIBLE` | `QUALIFIED` | `QUALIFIED` | New strict all-row normalizers can reuse fail-closed primitives; legacy NARParser is excluded. |
| `EXISTING_FORMAL_DOMAIN_REUSE` | `QUALIFIED` | `QUALIFIED` | Exact identity, bytes, digest, observation, and repository-load primitives are reusable. |
| `COMPOSITE_COVERAGE_RELATION_DEFINABLE` | `UNPROVEN` | `UNPROVEN` | Candidate relations are concrete, but planned/actual adjustment exhaustiveness and positive zero remain missing. |

## Formal provider qualification outcomes

```text
JRA: UNPROVEN
NAR: UNPROVEN
```

Neither `QUALIFIED_SINGLE_SOURCE` nor `QUALIFIED_COMPOSITE_SOURCE` is approved. The
correct future behavior for either provider scope remains
`TARGET_DISCOVERY_INCOMPLETE`.

The strongest unapproved JRA composite candidate is:

```text
historical annual/period schedule envelope
  -> exact official cancellation/substitute adjustment material
  -> every exact accessS meeting/day race-selection fragment
```

The strongest unapproved NAR composite candidate is:

```text
historical MonthlyConveneInfo year/month envelope
  -> one exact date-qualified RaceList fragment per marked venue
  -> provider-native cancellation/substitute reference when needed
```

These are research candidates only. They cannot be frozen until the envelope is proven
exhaustive, zero semantics are positive, duplicate/contradictory evidence is defined,
and non-run identity across postponement/substitution is resolved.

## Missing, duplicate, contradictory, and failure semantics

- Missing provider envelope, partition fragment, exact request identity, or raw bytes:
  `TARGET_DISCOVERY_INCOMPLETE`.
- Generic error, empty parser output, HTTP absence, or absent date row: never proven zero.
- Duplicate identical-looking partition/target: invalid; no silent deduplication.
- Distinct responses for one coverage identity: contradictory; no arbitrary latest.
- Malformed or skipped row: invalidate the full fragment; never reduce the denominator.
- Current page or current root observed later: never backdated to `target_date`.
- Result/card/snapshot collections: never denominator evidence.
- No network acquisition occurs inside no-network historical replay.

## Digest qualification

Future source and target-set digests must include only formally versioned canonical
content. A later implementation design must freeze a schema/version identifier,
canonical field order, exact datetime representation, string normalization, tuple/list
ordering, and exact byte encoding. It must also decide whether a source digest covers
raw response bytes, a normalized bundle covers canonical source references and coverage
relations, and the target-set `content_sha256` covers the final ordered projection.

Python `repr`, unordered dictionaries, locale formatting, filesystem metadata, SQLite
row identity/order, insertion time, and current time are forbidden digest material.
This phase implements no serializer or digest builder.

## Unresolved conflicts and questions

1. What exact JRA official index exhaustively lists all schedule changes and binds them
   to annual planned partitions and accessS actual fragments?
2. What source positively proves a JRA actual zero-meeting day after all possible
   substitute/adjustment activity rather than merely showing an unlisted planned day?
3. For a cancelled and substituted JRA meeting, which exact original race identities
   remain members of the original date, and how are replacement identities related?
4. Does NAR formally define MonthlyConveneInfo as an exhaustive historical provider-day
   partition ledger, and does an all-blank column assert post-adjustment actual zero?
5. When NAR MonthlyConveneInfo removes an original cancelled date and shows only `△` on
   a substitute date, which official source preserves the original race identities?
6. What canonical NAR RaceList request spelling resolves literal versus percent-encoded
   slashes, `www` versus `www2`, and `3` versus `03` baba codes?
7. How do both providers represent postponed and abandoned races beyond the tested
   cancellation/substitute cases without a prematurely normalized enum?
8. What replay retention horizon is required, and can every envelope, fragment, and
   adjustment source meet it beyond the observed JRA-2015 and NAR-2020 fragment floors?

These questions permit no inference and reveal no Phase 2 contract conflict. Phase 2's
shared bundle, nullable start, native disposition evidence, honest observation time,
ordering, and `content_sha256` remain unchanged.

## Phase gates

Phase 3 is research-and-design only. This PREPARE does not authorize a source
implementation, acquisition/archive pipeline, Evidence Resolver, tests, schemas,
migrations, database changes, CLI, or Phase 4. Because both providers remain
`UNPROVEN`, no Daily Target Discovery production implementation should begin. Any next
activity requires separate ChatGPT review and explicit phase instruction.

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
4 or later are also forbidden. `database/keiba.db` and `logs/` must never be staged or
committed.

## Required verification

No tests are added or run because this is a research-and-design-only PREPARE. Required
checks are:

```text
git diff --check
git diff --name-only
git status --short
git diff --cached --name-only
```

Only the two Allowed Files may be changed, with no staged files.

## Stop condition

Stop with `DRAFT_FOR_REVIEW` after completing the research report and required checks.
Wait for ChatGPT independent review and explicit phase approval. Do not execute,
implement, test, stage, commit, push, archive research material, or advance.
