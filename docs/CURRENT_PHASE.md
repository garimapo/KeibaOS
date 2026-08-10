# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6c1d3b2c` — NAR trusted historical source collection orchestration preparation.

Formal base: `93fad49e7b188e3b4492cc7fe0eb61d36d16b735`.

Formal branch: `feature/ver0.8-simulator`.

Preparation review branch: `review/4c-2d3b1i6c1d3b2c-prepare`.

## Goal and Fixed Boundaries

Design, but do not implement, the one-target-race collector:

```text
caller-supplied DebaTable URL
  -> trusted live DebaTable capture/archive
  -> c1b track, entry, jockey, odds_win records
  -> one trusted HorseMarkInfo capture per entry
  -> exact historical-start discovery
  -> trusted RaceMarkTable captures
  -> d3b2a pair normalization
  -> complete validated c1a v3 record set
```

The collector reuses without changing:

- `NAROfficialLiveResponseCaptureService.capture_response(*, response_url)`;
- `NAROfficialResponseCapture` and `NAROfficialResponseCaptureArchive`;
- `normalize_nar_historical_input_source_records(*, response)`;
- `normalize_nar_historical_past_race_source_record(*, target_entry_record, horse_history_response, race_result_response)`; and
- `build_historical_input_snapshot(...)`.

`TARGET_RACE_DISCOVERY = OUT_OF_SCOPE`. The sole initial caller input is one supported NAR DebaTable URL. Top-today
and race-list discovery, calendar scheduling, CLI, daemon/recurring execution, acquisition retries, and bulk
all-races crawling are not part of this phase.

## Existing Gap and Downstream Investigation

c1b emits exactly `track`, `entry`, `jockey`, and `odds_win`; it emits neither `past_race` nor
`past_race_absence`. The existing snapshot builder requires every entry to have one or more `past_race` records or
exactly one `past_race_absence` record. The collector must close that source-set completeness gap before any snapshot
can be built.

Investigated paths:

- `scripts/simulation/nar_historical_input_source.py`
- `scripts/simulation/nar_historical_past_race_source.py`
- `scripts/simulation/historical_input_source_records.py`
- `scripts/simulation/historical_input_evidence.py`
- `scripts/simulation/historical_input_snapshot_builder.py`
- `scripts/simulation/historical_input_snapshots.py`
- `scripts/simulation/nar_official_response_capture.py`
- `scripts/simulation/nar_official_response_live_capture.py`
- `scripts/simulation/repositories/sqlite_nar_official_response_capture_repository.py`
- `scripts/database.py`, `scripts/cli/run_prediction.py`, `scripts/prediction/prediction_pipeline.py`,
  `scripts/prediction/ability_engine.py`, `scripts/prediction/pace_engine.py`, and
  `scripts/prediction/jockey_engine.py`
- tests covering c1a source records, c1c snapshot building/domain, NAR source normalization, and NAR capture/archive.

There is **no existing repository-level c1a history-depth contract**. `database.get_past_races()` returns all prior
rows, c1c accepts all supplied past-race records, and Ability/Pace receive all supplied history. The JockeyEngine has
its own `RECENT_RACE_LIMIT = 5`, but that is a scoring rule, not a collection contract. Therefore this PREPARE
proposes, for independent approval only:

```text
PAST_RACE_HISTORY_DEPTH = 5 actual prior starts per target entry
PAST_RACE_DEPTH_SOURCE = proposed new collector contract
```

The window is formed before support filtering: the five newest actual starts strictly before the target race date are
the required window. A JRA row or any unsupported row inside that window fails the collection; it must not be skipped
to use an older NAR race. If fewer than five actual prior starts exist, collect every actual prior start. A history
absence means *proven zero actual prior starts*, not “zero supported NAR rows.”

## Causal Collection Contract

The c1b track record supplies `scheduled_start_at`. Once c1b normalization succeeds, all capture chronology is checked
against that single deadline:

```text
DebaTable observed_at <= scheduled_start_at
HorseMarkInfo observed_at <= scheduled_start_at
each RaceMarkTable observed_at <= scheduled_start_at
COLLECTION_CAPTURED_AT = max(observed_at over every accepted capture)
```

Any DebaTable capture after scheduled start rejects collection before historical capture. Any later HorseMarkInfo or
RaceMarkTable capture after that start likewise rejects collection. No timestamp is backdated, synthesized, aggregated
into evidence, or repaired. `COLLECTION_CAPTURED_AT` is collection metadata only; each c1a evidence reference retains
its own supplied observed-at value. A later snapshot-composition phase must set its information cutoff consistently
with this collection boundary; it must not manufacture causality.

Consequently, live pages retrieved after an old race's scheduled start cannot become trusted historical replay
evidence. `HISTORICAL_RETROACTIVE_LIVE_BACKFILL = IMPOSSIBLE`. Parser fixtures and capture timestamps used in tests are
not trusted historical captures.

## HorseMarkInfo Discovery and Zero Proof

For every c1b entry, derive the one HorseMarkInfo URL only from its validated
`external_horse_id = nar:horse:<lineage>`:

```text
https://www.keiba.go.jp/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=<lineage>
```

The lexical lineage token is reused exactly; horse name, target horse number, local IDs, and database history are
forbidden fallbacks. The capture service canonicalizes and archives this URL before discovery consumes the supplied
response.

Official live investigation of `k_lineageLoginCode=30074407776` found one `HorseMarkInfo_table`, 34 displayed history
rows in descending date order, and 15 row-local relative NAR RaceMarkTable links, e.g.
`/KeibaWeb/TodayRaceInfo/RaceMarkTable?k_raceDate=2026%2F05%2F03&k_raceNo=1&k_babaCode=31`. The remaining displayed
JRA rows had no NAR RaceMarkTable link. No pagination or page/next/previous control was exposed in that supplied
document. A second official page (`30039401296`) displayed 14 rows and 14 NAR result links with no such control.

This is enough to freeze row-local identity and descending order for the observed pages, but it is **not yet a generic
provider completeness proof**. `ZERO_HISTORY_PROOF_AVAILABLE = NO` until c1 proves, from the exact supplied
HorseMarkInfo response and any official pagination/continuation state, that the history is complete. If the provider
has a pagination/row-limit mechanism, c1 must return an explicit incomplete/unsupported outcome rather than emit an
absence. A row date greater than or equal to the target race date is a chronology contradiction and fails closed.

Discovery parses every row structurally, preserves actual-start order, and uses complete provider-native RaceMark
identity `(raceDate, babaCode, raceNo)`. The selected five are the newest actual starts before the target date; no
date/place/name/position fallback is allowed. A recognized JRA row within the required actual-start window is
unsupported. A recognized NAR row whose later pair normalization is unsupported also fails the collection instead of
being skipped.

For a discovered NAR result link, c1 validates the relative or accepted official absolute link, parses its three
provider-native tokens, and constructs the d3b2a-supported canonical supplied RaceMark URL:

```text
https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceMarkTable
  ?k_babaCode=<canonical>
  &k_raceDate=YYYY%2FMM%2FDD
  &k_raceNo=<canonical>
```

The historical race identity—not link text or source host spelling—is the mapping proof. A `www2` HorseMark navigation
link may be accepted only after this exact identity is validated and reconstructed as the supported `www` RaceMark
capture URL. Evidence URLs remain the canonical URLs of bytes actually captured; no response host is silently
rewritten after capture.

## Proposed c1 Discovery and Absence Boundary

The first implementation phase should be pure and supplied-response-only. It neither performs HTTP nor reads the
archive/database.

Proposed module-defined public types/functions:

```text
NARHistoricalPastRaceReference
NARHistoricalPastRaceDiscovery
discover_nar_historical_past_race_history(
    *, target_entry_record: HistoricalInputSourceRecord,
    horse_history_response: NarSuppliedOfficialResponse,
) -> NARHistoricalPastRaceDiscovery

normalize_nar_historical_past_race_absence_source_record(
    *, target_entry_record: HistoricalInputSourceRecord,
    horse_history_response: NarSuppliedOfficialResponse,
    discovery: NARHistoricalPastRaceDiscovery,
) -> HistoricalInputSourceRecord
```

`NARHistoricalPastRaceDiscovery` must make the difference between nonzero discovered actual starts and a structurally
proven complete zero history explicit; an empty tuple alone is insufficient. It is responsible for the selected,
newest-first bounded actual-start references and for declaring whether zero is proven. Its private URL/entry parsing
must independently uphold the established c1b/d3b2a lexical rules; it must not import private normalizer helpers.

The proposed NAR absence normalizer may emit only from the explicit proven-zero state. Its exact c1a v3 content is:

```text
record_kind: past_race_absence
organization/source_system: NAR / nar_official
external_race_id/external_entry_id: derived from target_entry_record
provider_record_id: None
record_values:
  external_entry_id: exact target entry ID
  query_scope:
    external_entry_id: exact target entry ID
    target_race_date: target date as YYYY-MM-DD
    strictly_before_target_race: true
  result_count: 0
evidence: exactly one past_race_absence_query reference
  canonical_source_url: canonical HorseMarkInfo response URL
  response_sha256: SHA-256 of exact supplied HorseMarkInfo body
  available_at: None
  observed_at: exact supplied HorseMarkInfo observed_at
```

Its c1a source ID is the existing generic `his-v3:past_race_absence:<sha256>` canonical payload: it includes the
above facts and evidence role/URL/raw SHA, and excludes evidence timestamps. There is no synthetic query URL, no
RaceMark evidence, and no absent-result inference from JRA or unsupported rows.

## Proposed c2 Collector Boundary

c2 owns one sequential, injected-capture-service orchestration call for one caller-supplied DebaTable URL. It first
captures/archives DebaTable, converts that capture to `NarSuppliedOfficialResponse`, runs c1b, validates the scheduled
start chronology, then processes entries in c1b canonical horse-number order. For each entry it captures/archives the
derived HorseMarkInfo URL and invokes c1 discovery:

- proven zero history produces one absence record;
- nonzero discovery requires every selected start to be captured/archived and normalized by d3b2a; and
- one RaceMarkTable capture is reused at most once per canonical RaceMark URL *within that collection*.

`ONE_RACEMARK_CAPTURE_PER_CANONICAL_URL_PER_COLLECTION = YES`. Cross-collection cache/reuse and archival lookup
policy are explicitly out of scope. Capture persistence precedes every normalization. If any request, archive write,
parse, chronology, discovery, or normalization step fails, no partial source-record collection result is returned;
already persisted immutable captures may remain (`PARTIAL_ARCHIVE_ON_COLLECTION_FAILURE = ALLOWED`).

The collector has no automatic retry. It is sequential (`REQUEST_CONCURRENCY = 1`) and must use an injected,
testable pacing collaborator between live capture operations. The proposed default policy for review is a minimum
one-second interval, owned by composition rather than hard-coded sleep in parsing code. This is a conservative
collection safeguard, not an inferred NAR rate-limit promise. `AUTOMATIC_RETRY = NONE`.

After all entries are complete, c2 calls `validate_historical_input_source_record_set(...)` exactly once as the final
source-set validator. It returns deterministic records ordered by existing c1b order followed, per entry, by
historical races in descending race date (with a one-per-entry absence in the corresponding historical slot). It does
not build a snapshot and does not compose the capture database with the main database.

Proposed c2 public surface:

```text
NARHistoricalSourceCollection
collect_nar_historical_input_source_records(
    *, deba_table_url: str,
    capture_service: NAROfficialLiveResponseCaptureService,
    pacing: NAROfficialResponseCapturePacing,
) -> NARHistoricalSourceCollection
```

The returned immutable collection carries the validated source-record tuple plus `collection_captured_at`; it does not
hide partial output. The interface is intentionally one race per call and does not become a scheduler or a database
composition API.

## Proposed c3 Composition Boundary

c3, not c1/c2, owns caller-supplied capture-database path/archive composition with main-database race/entry mapping
and `build_historical_input_snapshot(...)`. It must use the c2 complete tuple unchanged, preserve capture evidence
identities, and make snapshot cutoff/captured-at policy explicit. No cross-database transaction, `ATTACH`, archive
mutation, source re-normalization, target discovery, or historical replay timestamp repair is approved.

`SNAPSHOT_BUILDING_SCOPE = separate c3 only`.

## Support Boundaries and Blockers

- `JRA_TARGET_RACE_COLLECTION = FUTURE_REQUIRED`.
- `JRA_HISTORICAL_PAST_RACE_COLLECTION = FUTURE_REQUIRED`.
- `NAR_PAST_RACE_ABSENCE` is supported only after c1 proves complete zero actual starts; it is otherwise unsupported.
- Pagination/row-limit completeness is the remaining design blocker for generic zero-history proof.
- The five-start collector depth is a proposed new contract requiring review; it is not silently inherited from the
  prediction engines.
- Trusted historical replay requires pre-cutoff archived official captures. The future live collector cannot repair
  missing historical observation evidence.

## Proposed Phase Split and Future Allowed Files

### `4C-2d3b1i6c1d3b2c1` — discovery and zero-history absence normalizer

```text
scripts/simulation/nar_historical_past_race_discovery.py
scripts/simulation/nar_historical_past_race_absence_source.py
tests/test_nar_historical_past_race_discovery.py
tests/test_nar_historical_past_race_absence_source.py
tests/fixtures/nar/horse_mark_info_history_discovery.html
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

### `4C-2d3b1i6c1d3b2c2` — injected one-race live source collector

```text
scripts/simulation/nar_historical_source_collection.py
tests/test_nar_historical_source_collection.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

### `4C-2d3b1i6c1d3b2c3` — capture/main-database snapshot composition

```text
scripts/simulation/nar_historical_source_collection_composition.py
tests/test_nar_historical_source_collection_composition.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

Each future phase must revalidate its exact allowed-file scope. None is authorized by this PREPARE.

## PREPARE Allowed Files and Stop Condition

Only this PREPARE's two documentation files may change. No production code, test, fixture, migration, database,
archived response, acquisition, pagination, or source collection was implemented. Stop after the docs-only review
commit and independent architecture review.
