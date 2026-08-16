# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase

`4C-2d3b1i6d1d5f1c3` — JRA accessD target-source normalization preparation.

Formal base: `3d15d31a68500d05b224ffead60ee9a799064342`.

Review branch: `review/4c-2d3b1i6d1d5f1c3-jra-accessd-target-source-prepare`.

## Allowed Files

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

Design only. Production/tests, HTTP/live capture, archive/repository/database, schema/
migration, snapshot, Predictor, and bridge work are forbidden.

## Proposed Public Boundary

Create `scripts/simulation/jra_target_race_input_source.py` with exactly:

```python
class JRATargetRaceSourceError(ValueError): ...
class JRATargetRaceSourceValidationError(JRATargetRaceSourceError): ...
class JRATargetRaceSourceUnsupportedError(JRATargetRaceSourceError): ...

@dataclass(frozen=True, slots=True)
class JRATargetRaceSourceCollection:
    target_track_record: HistoricalInputSourceRecord
    target_entry_records: tuple[HistoricalInputSourceRecord, ...]
    source_records: tuple[HistoricalInputSourceRecord, ...]

def normalize_jra_target_race_input_source_records(
    *,
    response: JRASuppliedOfficialResponse,
) -> JRATargetRaceSourceCollection: ...
```

No package-root export. The exact supplied response is the sole input; no caller race,
entry, horse, time, URL, or odds override exists. The collection contains exactly one
`track` record, then entry records in ascending official horse-number order, and its
flat `source_records` is exactly:

```text
(track,
 entry(horse 1), jockey(horse 1), odds_win(horse 1),
 entry(horse 2), jockey(horse 2), odds_win(horse 2), ...)
```

`target_entry_records` is the ordered subset of only `entry` records. Constructor
invariants require exact `HistoricalInputSourceRecord` values, JRA/`jra_official`,
one common accessD race ID, unique positive horse numbers and horse identities, and
the canonical flat sequence. The normalizer calls the existing
`validate_historical_input_source_record_set(...)` exactly once before construction;
it does not create a second neutral validator.

Expected supplied-response, structural, identity, source-record/evidence, and neutral
conflict errors translate narrowly to `JRATargetRaceSourceValidationError`.
Recognized normal-row absence/placeholder/non-runner shapes translate to
`JRATargetRaceSourceUnsupportedError`. No broad `Exception`/`BaseException`
catch is allowed.

## Input and Identity

Require exact `JRASuppliedOfficialResponse`. It must be the canonical accessD family:
`parse_jra_race_card_url_identity(response.response_url)` derives the authoritative
`JRAExternalRaceIdentity`; raw bytes are strict-decoded as CP932 only for this parser.
The supplied type has already canonicalized the URL and preserved the actual aware
`observed_at`; nevertheless the normalizer rechecks the exact accessD family and
canonical URL rather than accepting accessS/accessU evidence.

The one unique table is:

```css
#contentsBody > div.syutsuba > table.basic.narrow-xy.mt20
```

It must have one caption/header with the observed semantic heading family and one
nonempty body of direct runner rows. There is no fixed field size or 16-runner
assumption. Any duplicate/missing container, header, required cell, or row-local
value fails the complete normalization.

The authoritative URL identity is cross-checked against exactly:

| Fact | Selector / rule |
| --- | --- |
| visible date, venue, meeting, day | `table > caption > div.race_header > div.left > div.date_line > div.inner > div.cell.date`; strict date plus `N回<venue>M日`, mapping the existing 10 JRA venue codes |
| race number | `#contentsBody > div.line.main > div.inner > h1`; strict `<race>レース` |
| scheduled start | same header `div.cell.time > strong`; strict `HH時MM分` joined to the visible date in `Asia/Tokyo`, then normalized UTC |
| race header facts | selectors below; every value is bound to that same unique accessD card |

The visible date must also equal the real accessD CNAME calendar date. Every
venue/meeting/day/race contradiction fails closed; display text never constructs a
race identity.

## Exact Target Track Mapping

All fields and the one `track` evidence reference originate from the same accessD
response. The neutral record keys are exact.

| Neutral track field | Exact source / parse | Status and failure policy |
| --- | --- | --- |
| `target_race_date` | unique header `div.cell.date` | required; strict visible date equals CNAME date/year |
| `scheduled_start_at` | same header `div.cell.time > strong` | required; strict `HH時MM分`; visible date + `Asia/Tokyo` |
| `place` | same `div.cell.date` `N回<venue>M日` | required; exact existing venue-code mapping |
| `distance_m` | `div.race_title > div.type > div.cell.course` | required positive metres in strict `コース：<m>メートル（<芝|ダート>・<direction>）` |
| `track` | `div.race_title > div.type > div.cell.course` | required `芝` or `ダート`; must agree with `li.turf`/ `li.dirt` |
| `track_condition` | `div.cell.baba > ul > li.turf|li.dirt > span.cap/span.txt` | required; exactly one surface/condition pair, direct nonempty text |
| `race_name` | `div.race_title > div.inner > div.txt > span.main > span.race_name` | neutral-optional but direct nonempty fact is required for supported card |
| `race_class` | `div.race_title > div.type > div.cell.class` | neutral-optional but direct nonempty fact is required for supported card |
| `weather` | `div.cell.baba > ul > li.weather > span.inner > span.txt` | neutral-optional; exactly one direct nonempty node when present, no node yields `None`; duplicate/blank fails |

This proves `TRACK_EVIDENCE_CARDINALITY = EXACTLY_ONE`,
`SINGLE_RESPONSE_COMPLETE_TRACK_SOURCE = PROVEN`, and
`TRACK_SOURCE_SCHEMA_CHANGE_REQUIRED = NO`.

## Exact Target Entry Mapping

Every direct runner row must contain exactly one selector-scoped official horse anchor:

```css
td.horse > div.name_line > div.name > a[href]
```

Its relative official accessU href is resolved only against `https://www.jra.go.jp`
and passed to `parse_jra_horse_profile_url_identity(...)`. The resulting canonical
`jra:horse:<10 ASCII digits>` is the only horse identity. Horse name is not retained
by the neutral schema and is never identity evidence.

| Record kind / neutral key | Exact source / rule | Status and failure policy |
| --- | --- | --- |
| `entry.external_entry_id` | `td.num` strict positive canonical decimal, then existing `build_jra_external_entry_id(race_identity, horse_no)` | required; rebuilt value must be exact |
| `entry.external_horse_id` | row-local accessU anchor above | required non-null canonical JRA horse ID; missing/duplicate/malformed anchor fails |
| `entry.horse_no` | `td.num` | required positive canonical decimal |
| `jockey.external_entry_id` | same rebuilt entry ID | required exact duplicate |
| `jockey.jockey` | `td.jockey > p.jockey` | required direct nonempty normalized display text |
| `odds_win.external_entry_id` | same rebuilt entry ID | required exact duplicate |
| `odds_win.horse_no` | same `td.num` | required exact duplicate positive number |
| `odds_win.win_odds` | `td.horse > div.name_line > div.odds > div.odds_line > span.num` | required direct canonical positive finite `Decimal` |

Current neutral target-entry keys contain no sex/age, carried weight, gate, horse name,
or popularity field. They must not be added or inferred in this phase. Duplicate horse
number, duplicate canonical horse identity, duplicate rebuilt entry ID, malformed
relative accessU href, or noncanonical entry ID rejects the entire card.

The odds are only the direct accessD value visible at `response.observed_at`:
`TARGET_PREDICTION_ODDS`, not final odds. AccessO final odds, latest/nearest
replacement, settlement data, placeholders, zero/negative/non-finite text, or missing
odds are unsupported and cannot be backfilled.

## Non-Runner and Completeness Policy

`ACCESSD_NON_RUNNER_SEMANTICS_READY = NO`: the approved active-card investigation
proved only fully populated ordinary runner rows. No withdrawal, scratch, cancellation,
exclusion, or non-runner display meaning was proven.

Accordingly, a row is supported only if it satisfies the complete normal-runner shape
above. A row with missing/duplicate required cells or anchor, blank/placeholder/non-
numeric odds, or any other departure from that full shape is an unsupported row, not a
silently omitted entry. The complete normalization raises
`JRATargetRaceSourceUnsupportedError`; it returns neither track-only data nor a
partial runner collection. This fail-closed policy supports normal cards without
claiming an unproven non-runner classification.

Output order is ascending official horse number. The normalizer parses all rows,
rejects duplicate identities before construction, builds all records in memory, runs
the neutral validator once, then returns. No latest-N cap, row skip, or partial return
is permitted.

## Evidence, Causality, and Purity

For each produced record use exactly one `HistoricalInputEvidenceReference` from
the raw accessD bytes before HTML parsing:

| Record kind | Evidence role |
| --- | --- |
| track | `track` |
| entry | `entry` |
| jockey | `jockey` |
| odds_win | `odds_win` |

Every reference has `canonical_source_url=response.response_url`,
`response_sha256=sha256(response.response_body).hexdigest()`,
`available_at=None`, `observed_at=response.observed_at`, and
`request_identity_sha256=None` (accessD is GET). `provider_record_id=None` for
all target records. Existing `HistoricalInputSourceRecord` owns canonical
`source_id` construction; the parser never supplies a source ID.

The normalizer requires `response.observed_at <= scheduled_start_at`; a later card
response is rejected and no timestamp is changed. It does not receive an information
cutoff and does not invent `available_at`. The snapshot boundary remains the owner of
`observed_at <= captured_at <= information_cutoff <= scheduled_start_at`.

The future module is pure: no HTTP, live service, archive/repository/database,
filesystem, clock, random, subprocess, snapshot assembly, Predictor, or NAR/JRA
bridge. It strict-decodes supplied bytes only while producing records; later
collection/orchestration consumes those records and does not reparse accessD HTML.

## Next Implementation

Recommended exact files:

```text
scripts/simulation/jra_target_race_input_source.py
tests/test_jra_target_race_input_source.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

Tests use only minimal synthetic CP932 HTML. They must cover public surface/domain;
exact canonical accessD input/strict CP932; every URL/header identity cross-check;
all track and entry field mappings; accessU identity/entry-ID rebuilding; odds parsing
and body-SHA/source-ID determinism; evidence roles/timestamps; sorted output; duplicate
identities; all-or-nothing failure; every unsupported normal-row departure; late
observation; neutral validator exactly once; snapshot-builder compatibility after
separate past-race/absence records are combined; no package export/forbidden
dependencies; and no real capture. No fixture may contain a full official page.

## Readiness and Stop Condition

```text
TARGET_TRACK_MAPPING_READY: YES
TARGET_ENTRY_MAPPING_READY: YES
ACCESSD_ODDS_READY: YES
ACCESSD_TO_ACCESSU_IDENTITY_READY: YES
NON_RUNNER_SEMANTICS_READY: NO
FAIL_CLOSED_NON_RUNNER_POLICY: YES
SCHEMA_CHANGE_REQUIRED: NO
IMPLEMENTATION_READY: YES_FOR_SUPPORTED_NORMAL_RUNNERS
REAL_TRUSTED_CAPTURE_REQUIRED: NO
```

There is no schema or selector blocker for a supported-normal-runner implementation.
Unsupported non-runner semantics remain deliberately excluded. Stop after review of
the two documentation files, one review commit, and push; do not implement the next
phase.
