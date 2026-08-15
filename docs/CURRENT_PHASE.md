# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6d1d5` — JRA historical past-race normalizer consolidation PREPARE.

Formal base: `dcdef4bd6559418fe7f179f42cd16a263604fc08`.

Review branch: `review/4c-2d3b1i6d1d5-jra-past-race-normalizer-prepare`.

## Selected Pure API

The next implementation owns a provider module, `scripts/simulation/jra_historical_past_race_source.py`, with this
exact normalization boundary:

```python
normalize_jra_historical_past_race_source_record(
    *,
    target_track_record: HistoricalInputSourceRecord,
    target_entry_record: HistoricalInputSourceRecord,
    race_result_response: JRASuppliedOfficialResponse,
    final_win_odds_response: JRAFinalWinOddsSuppliedOfficialResponse,
) -> HistoricalInputSourceRecord
```

Its module-defined public surface is exactly `JRAHistoricalPastRaceSourceError`,
`JRAHistoricalPastRaceSourceValidationError`, `JRAHistoricalPastRaceSourceUnsupportedError`, and the normalization
function. There is no package-root export. The module is pure: no HTTP, archive lookup, database, filesystem, clock,
randomness, subprocess, discovery, pagination, or bridge.

## Target and Historical Identity Chains

Both target values must be exact `HistoricalInputSourceRecord` instances with organization `JRA` and source system
`jra_official`.

```text
track: record_kind=track, external_entry_id=None, target_race_date is exact date
entry: record_kind=entry, non-null external_entry_id, same external_race_id as track
```

The normalizer parses the shared target race ID only through `parse_jra_external_race_id`. It requires the entry’s
non-null `external_horse_id` to parse through `parse_jra_external_horse_id`, and reconstructs the entry ID with
`build_jra_external_entry_id(race_identity=target_race, horse_no=entry.record_values["horse_no"])`. The
reconstruction must equal both the top-level entry ID and `record_values["external_entry_id"]`. Thus target horse
number is internally coherent but is never historical-race horse identity.

`race_result_response` must be exact `JRASuppliedOfficialResponse`, validate as accessS `RACE_RESULT`, and be parsed
through `parse_jra_result_url_identity`. The normalizer narrowly extracts the already-validated calendar date segment
from that accessS CNAME, validates it as a real date, and requires it to be strictly before the target track date. It
does not alter the public JRA identity API or infer intraday ordering.

In the unique official accessS result table, the only historical horse selection is a unique row-local
`td.horse a[href]`, resolved against accessS and parsed through `parse_jra_horse_profile_url_identity`. Its ten-digit
stable identity must equal the target entry horse ID. Names, jockey, trainer, sex/age, pedigree, and historical horse
number are forbidden fallbacks. The selected row’s `td.num` is a historical race-local horse number used only for the
accessO join.

`final_win_odds_response` must be exact `JRAFinalWinOddsSuppliedOfficialResponse`; its formal locator endpoint and
request fingerprint are retained unchanged, and its `external_race_identity` must equal accessS identity. Its one
`table.tanpuku` must contain exactly one `td.num` equal to the selected accessS historical horse number, and its direct
`td.odds_tan` is the sole odds authority. Target and historical horse numbers need not equal.

## Visible Race Identity Cross-checks

Neither lexical URL/request identity alone proves a physical race. accessS requires exactly one
`#race_result .race_header`; `.cell.date` must expose the calendar date, meeting number, venue, and meeting day;
`.race_number img[alt]` must expose race number; and `.race_name` is the page race heading. accessO requires exactly
one `.race_header`, with `.cell.date`, `.race_number`, and `.race_name` proving the same visible date/meeting/venue/
meeting-day/race-number/heading facts. Every directly available value must agree with both provider-native identities
and with the frozen mapping:

```text
01=札幌  02=函館  03=福島  04=新潟  05=東京
06=中山  07=中京  08=京都  09=阪神  10=小倉
```

Missing, duplicate, malformed, or contradictory identity nodes are validation failures. No date-only, race-name,
venue, horse-name, or ordinal fallback is permitted.

## Direct Field Authority

Display normalization is NFC plus controlled whitespace collapse. Numeric values are parsed directly to `int` or
`Decimal`, never through `float`; all required source fields are unique and nonempty. A missing/malformed direct fact
is validation failure; a recognized state outside the initial envelope is unsupported.

| c1a past-race field | Exact authority / selector | normalization and initial support |
|---|---|---|
| `race_date` | accessS validated CNAME calendar date, cross-checked against `.race_header .cell.date` | `date` |
| `place` | accessS `.race_header .cell.date` venue | exact frozen venue mapping |
| `race_name` | accessS `.race_header .race_name` | nonempty text |
| `race_class` | accessS `.race_header .type > .cell.class` | nonempty text; blank unsupported |
| `distance_m` | accessS `.race_header .type > .cell.course` | direct positive ASCII meter token |
| `track` | accessS `.race_header .baba` | direct `芝` or `ダート`; obstacle/special unsupported |
| `weather` | accessS `.race_header li.weather .txt` | nonempty text |
| `track_condition` | accessS `.race_header .baba li > .txt` matching selected surface | nonempty direct text |
| `finish` | selected accessS `td.place` | positive completed integer |
| `race_time` | selected accessS `td.time` | direct normalized official time text |
| `weight` | selected accessS `td.h_weight` number before span | nonnegative `Decimal`; never assigned `td.weight` |
| `weight_diff` | selected accessS `td.h_weight span` parenthesized signed/zero change | exact `Decimal` |
| `jockey` | selected accessS `td.jockey` | direct text; retain meaningful allowance symbols |
| `popularity` | selected accessS `td.pop` | direct positive integer |
| `odds` | accessO `table.tanpuku` matching row `td.odds_tan` | direct finite positive `Decimal` |
| `passing_order` | selected accessS `td.corner li[title]` | canonical `-` joined positive components |
| `fourth_corner_position` | component whose same-row title is `4コーナー通過順位` | positive integer only |

`着差` is never converted to seconds; `reference_time_difference_seconds` does not exist in schema v4. Popularity is
not odds, payout is not odds, and accessS assigned racing weight is not body weight. This remains
`HISTORICAL_DOMAIN_DERIVED_VALUES_POLICY = DIRECT_OFFICIAL_SOURCE_FACTS_ONLY`.

## Corners, Evidence, and Causality

The ordered accessS `td.corner li[title]` components are authoritative. Their labels must normalize to unique,
strictly increasing ordinals from `{1,2,3,4}`, with exactly one label 4; the position carrying label 4 supplies
`fourth_corner_position`. A fixed fourth component, blind last component, whole-field reconstruction, or zero
missing sentinel is forbidden. Missing, duplicate, out-of-order, nonnumeric, or ambiguous labels/components are
unsupported.

The output is target-scoped with `record_kind=past_race`, `organization=JRA`, `source_system=jra_official`, target
`external_race_id`/`external_entry_id`, and:

```text
provider_record_id = build_jra_provider_record_id(
    race_identity=historical accessS identity,
    horse_identity=matched accessU identity,
)
```

It has exactly the canonical role tuple:

```text
historical_race_context    = accessS URL, request_identity_sha256=None, accessS raw SHA, None, accessS observed_at
historical_race_final_odds = accessO endpoint, locator request fingerprint, accessO raw SHA, None, accessO observed_at
historical_race_result     = same accessS tuple as context
```

Raw SHA-256 is over supplied bytes before strict CP932 decode or HTML parsing. Same-response accessS reuse is valid
only under existing full URL/request-identity/SHA/timestamp coherence. No timestamp is backdated, aggregated, or used
in c1a source identity; the builder alone later enforces causal eligibility.

## Fail-closed Envelope

Unsupported recognized states include scratches/withdrawals, exclusion, DNF/stopped, disqualification, ambiguous
dead-heat formatting, missing race time, missing/`計不` body weight/change, missing popularity, blank class,
obstacle/mixed/special surface, missing final odds, nonnumeric/zero/negative final odds, and unsupported corner
layout. Validation failures include malformed CP932, wrong supplied-response type, invalid target coherence, missing
or duplicate accessU horse anchor, missing/duplicate accessO horse number, accessS/accessO identity mismatch, and
visible identity mismatch. There is no best-effort recovery.

## Fixtures, Compatibility, and Next Phase

Implementation tests use minimal synthetic strict-CP932 HTML snippets containing only the approved official structural
nodes, not full copyrighted pages. In-memory mutations cover malformed/multiplicity/unsupported branches. No fixture
file is currently required.

No c1a/c1b/domain/archive/live/migration/builder/repository/package-root change is needed. Source schema stays 4,
snapshot schema stays 4, global migrations end at 14, and JRA capture migrations remain `(1,2)`. NAR production is
unchanged. `NAR_LINEAGE_TO_JRA_HORSE_ID_LINK = NOT_PROVEN`; mixed-provider collection, historical discovery, and
orchestration remain out of scope.

```text
ARCHITECTURE_BLOCKERS = NONE
RECOMMENDED_NEXT_PHASE = 4C-2d3b1i6d1d5a — JRA historical past-race normalizer implementation
```

The recommended implementation allows exactly:

```text
scripts/simulation/jra_historical_past_race_source.py
tests/test_jra_historical_past_race_source.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Allowed Files and Stop Condition

This PREPARE changes only `docs/CURRENT_PHASE.md` and `docs/LATEST_CODEX_REPORT.md`. Stop for independent design
review. Do not implement the normalizer, capture or archive any response, add fixtures, modify production/tests/
migrations, begin discovery, or begin a bridge.
