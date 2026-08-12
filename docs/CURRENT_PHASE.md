# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6d1d` — JRA historical-result normalizer PREPARE.

Formal base: `0135cee4ad8e578e6bd20940b16198a576172c04`.

Review branch: `review/4c-2d3b1i6d1d-prepare`.

## Decision

`ACCESS_S_ONLY_JRA_PAST_RACE_NORMALIZER = BLOCKED`.

One trusted official JRA accessS result response is sufficient to bind one historical JRA horse result and to supply most of the current c1a `past_race` facts.  It is not sufficient to create the current provider-neutral record: the official result table directly exposes `単勝人気` (popularity), but no horse-level historical `単勝オッズ` value.  Current c1a `past_race.record_values` requires `odds: Decimal`; popularity, payout, margin, present-day odds, and a derived estimate must not be substituted.

This is an architectural prerequisite, not a reason to weaken c1a, invent a third evidence role, or implement a partial past-race record.  A future normalizer implementation is not yet authorized.

## Conditional Future Public Boundary

Once the historical-odds evidence/domain prerequisite is independently designed and approved, the intended module boundary is:

```python
normalize_jra_historical_past_race_source_record(
    *,
    target_track_record: HistoricalInputSourceRecord,
    target_entry_record: HistoricalInputSourceRecord,
    race_result_response: JRASuppliedOfficialResponse,
) -> HistoricalInputSourceRecord
```

The conditional module-defined public surface is exactly:

```text
JRAHistoricalPastRaceSourceError
JRAHistoricalPastRaceSourceValidationError
JRAHistoricalPastRaceSourceUnsupportedError
normalize_jra_historical_past_race_source_record
```

It must not be package-root exported.  It remains a pure supplied-response normalizer: no HTTP, archive lookup, database, filesystem, current clock, global mutable state, acquisition, discovery, NAR-to-JRA bridge, or horse-name lookup.

## Target Binding and Chronology

`target_track_record` and `target_entry_record` must both be exact `HistoricalInputSourceRecord` instances.

The future boundary must require:

```text
target_track_record.record_kind = track
target_track_record.organization = JRA
target_track_record.source_system = jra_official
target_track_record.external_entry_id = None

target_entry_record.record_kind = entry
target_entry_record.organization = JRA
target_entry_record.source_system = jra_official
target_entry_record.external_entry_id != None

target_track_record.external_race_id == target_entry_record.external_race_id
```

The normalizer derives, and accepts no caller override for:

```text
target_external_race_id  = target_entry_record.external_race_id
target_external_entry_id = target_entry_record.external_entry_id
target_external_horse_id = target_entry_record.record_values["external_horse_id"]
target_race_date         = target_track_record.record_values["target_race_date"]
```

`target_race_date` is the authoritative provider-neutral date provenance.  It is a validated c1a `date`, not a free caller string and not an inferred date from the JRA stable race ID.

The future boundary must parse `target_external_race_id` with `parse_jra_external_race_id`, require a non-null canonical `jra:horse:<10 ASCII digits>` through `parse_jra_external_horse_id`, and reconstruct `target_external_entry_id` using `build_jra_external_entry_id(race_identity=..., horse_no=target_entry_record.record_values["horse_no"])`.  The reconstruction must equal both the top-level entry ID and `record_values["external_entry_id"]`.  Thus the target entry's race, horse number, and stable horse identity remain coherent without treating a race-local horse number as historical horse identity.

The historical calendar date is the eight-digit date segment already present in the validated accessS CNAME.  The future module first calls public `parse_jra_result_url_identity`, then narrowly extracts and validates that date from the already-validated canonical CNAME; it does not duplicate or weaken the public race-identity grammar.  The historical date must be strictly before `target_race_date`.  Same-day and future historical races are validation failures; no intraday ordering is inferred.

`IDENTITY_API_CHANGE_REQUIRED = NO` for this date extraction design.

## Historical Race and Horse Identity

`race_result_response` must be an exact `JRASuppliedOfficialResponse`.  Its canonical accessS URL is validated with public `parse_jra_result_url_identity`; this yields the historical `JRAExternalRaceIdentity`.  The result CNAME date is only calendar-date material, not a replacement race identity.

The response HTML must independently prove one official accessS result layout.  The selected result table is unique and has the official semantic headings:

```text
着順, 枠, 馬番, 馬名, 性齢, 負担重量, 騎手名, タイム, 着差,
コーナー通過順位, 推定上り (ordinary flat) or 平均1F (obstacle),
馬体重（増減）, 調教師名, 単勝人気
```

The initial supported envelope is ordinary completed flat turf/dirt only.  Obstacle layouts are explicitly unsupported; their `障害` course/race form and repeated-course semantics are not forced into the ordinary past-race contract.

For the matched result row, require exactly one row-local `td.horse a[href]`.  Resolve a relative official accessU href against the supplied accessS URL and parse it only with `parse_jra_horse_profile_url_identity`.  Its resulting `jra:horse:<key>` must exactly equal the target entry's canonical horse identity.  Zero, multiple, malformed, foreign, or mismatched anchors are validation errors.  Horse names, jockeys, trainers, sex/age, pedigree, and historical horse number are forbidden as identity fallbacks.

The output, after the odds prerequisite is solved, remains target-entry scoped:

```text
record_kind        = past_race
organization       = JRA
source_system      = jra_official
external_race_id   = target_external_race_id
external_entry_id  = target_external_entry_id
provider_record_id = build_jra_provider_record_id(
    race_identity=historical_access_s_identity,
    horse_identity=matched_access_u_identity,
)
```

Visible accessS identity is independently cross-checked against the CNAME identity: exactly one `#race_result .race_header`; its `.cell.date` calendar date, meeting number, venue text, and meeting-day text must agree with the CNAME date and the frozen venue mapping; `.race_number img[alt]` must agree with the CNAME race number.  The frozen venue mapping is `01=札幌`, `02=函館`, `03=福島`, `04=新潟`, `05=東京`, `06=中山`, `07=中京`, `08=京都`, `09=阪神`, `10=小倉`.  Missing, duplicate, malformed, or contradictory visible facts fail validation.

## Evidence and Causality

The existing c1a v4 evidence contract permits one underlying response to fill both required `past_race` roles when URL/SHA and timestamps are identical.  The conditional normalizer therefore creates exactly:

```text
historical_race_context = accessS canonical URL, SHA-256(exact raw CP932 bytes), None, supplied observed_at
historical_race_result  = accessS canonical URL, SHA-256(exact raw CP932 bytes), None, supplied observed_at
```

The body digest is calculated before CP932 decoding, HTML parsing, NFC, or display normalization.  `available_at = None`; HTTP `Date`, race date, and present observation are not availability evidence.  `observed_at` is preserved unchanged.  Timestamp-only changes leave the c1a source ID unchanged; any raw-byte change changes it.  Existing snapshot assembly, not this normalizer, remains the sole owner of `observed_at <= captured_at <= information_cutoff` eligibility.

The two same-response roles are deliberate and valid; no fabricated second response is required.  No target-record evidence is copied into past-race evidence.

## Direct Official Field Mapping

All fields are direct facts from the unique official accessS result layout.  Display text is NFC-normalized with controlled whitespace collapse only; no semantically distinct punctuation is removed.  A required missing, duplicated, malformed, or contradictory direct fact is a validation error.  A recognized official representation outside the narrow support envelope is `JRAHistoricalPastRaceSourceUnsupportedError`.

| c1a field | AccessS authority and deterministic normalization | Type / initial support |
|---|---|---|
| `race_date` | validated CNAME date; exact cross-check with `.race_header .cell.date` | `date` |
| `place` | venue text inside `.race_header .cell.date`; exact cross-check to the frozen CNAME venue-code mapping | nonempty `str` |
| `race_name` | `.race_header .race_name` | nonempty `str` |
| `race_class` | `.race_header .type > .cell.class` | nonempty `str`; blank is unsupported |
| `distance_m` | `.race_header .type > .cell.course`, direct comma-free/ASCII-decimal meter token | positive `int`; no distance inference |
| `track` | `.race_header .baba` direct surface label (`芝` or `ダート`) | nonempty `str`; obstacle/mixed/special forms unsupported |
| `weather` | `.race_header li.weather .txt` | nonempty `str` |
| `track_condition` | selected direct turf/dirt `.race_header .baba li > .txt` matching `track` | nonempty `str`; no venue inference |
| `finish` | matched row `td.place` | positive `int`; nonnumeric result unsupported |
| `race_time` | matched row `td.time` | normalized direct official time `str`; no float-seconds conversion |
| `weight` | matched row `td.h_weight` body-weight number before the increase/decrease span | nonnegative `Decimal`; never `td.weight` assigned racing weight |
| `weight_diff` | matched row `td.h_weight span`, parenthesized signed/zero change | exact `Decimal`; absent/計不/special state unsupported |
| `jockey` | matched row `td.jockey` direct visible jockey text | nonempty `str`, NFC/controlled whitespace; retain meaningful allowance symbols |
| `popularity` | matched row `td.pop` (`単勝人気`) | positive `int` initially; no zero/blank/special substitute |
| `odds` | **No direct horse-level historical single-win odds is present in accessS.** `td.pop` is popularity, not odds. | **BLOCKED** — must not be fabricated or derived |
| `passing_order` | matched row `td.corner li[title]` ordered direct official position components, normalized as canonical `-`-joined component text | nonempty `str`; special/nonnumeric component unsupported |
| `fourth_corner_position` | matched row component positionally aligned to its own `title="4コーナー通過順位"` label | positive `int`; requires one unambiguous label-4 component |

`着差` is not a provider-neutral time field.  It is neither converted to seconds nor used to reconstruct `race_time`.  `負担重量` is not body weight.  `単勝人気` is not odds.  This preserves `HISTORICAL_DOMAIN_DERIVED_VALUES_POLICY = DIRECT_OFFICIAL_SOURCE_FACTS_ONLY`.

## Passing Order and Unsupported States

The row-local ordered `td.corner li` values are authoritative for `passing_order`; the row-local official `title` labels establish which corner each component represents.  The normalizer must require all labels to normalize to unique, strictly increasing members of `{1, 2, 3, 4}`, require exactly one label `4`, and require only positive canonical integer row components.  It maps positionally and uses the component carrying label `4` as `fourth_corner_position`.

This is deliberately not a fixed fourth component or a blind final component rule.  It supports observed ordinary layouts such as `[1,2,3,4]` and `[3,4]`; no missing corners are invented.  Missing/duplicate/out-of-order/unrecognized label, nonnumeric component, or absent corner 4 is unsupported.  No `0` missing sentinel and no whole-field-order reconstruction are allowed.

Recognized but initially unsupported result/layout states include `取消`, `除外`, `中止`, `失格`, nonnumeric/ambiguous finish, missing time, missing body-weight change, missing odds/popularity, unsupported passing/corner layout, obstacle, mixed-surface or special track form, and blank class.  Malformed URL/HTML, duplicate target-horse row, ambiguous horse anchor, visible/URL identity conflict, target-record incoherence, and horse-identity mismatch are validation errors.

## Scope, Prerequisite, and Next Phase

```text
NAR_LINEAGE_TO_JRA_HORSE_ID_LINK = NOT_PROVEN
MIXED_HISTORY_COLLECTION_READY = NO
JRA_ACCESSU_HISTORY_DISCOVERY = OUT_OF_SCOPE
JRA_TARGET_ACCESSD_NORMALIZATION = OUT_OF_SCOPE
JRA_ACCESSO_OR_OTHER_HISTORICAL_ODDS_EVIDENCE = UNDESIGNED_PREREQUISITE
CAPTURE_ARCHIVE_CHANGES = OUT_OF_SCOPE
```

An accessS response observed today is a parser-development artifact, not trusted evidence for an earlier prediction cutoff.  No observation may be backdated.

Recommended next phase: `4C-2d3b1i6d1d1 — JRA historical odds evidence/domain PREPARE`.  It must establish whether an official immutable historical odds fact can exist, its causality, and whether the frozen c1a two-role evidence model requires an independent architecture change.  It must not implement the normalizer.

The conditional implementation phase after that prerequisite is approved separately and may change only:

```text
scripts/simulation/jra_historical_past_race_source.py
tests/test_jra_historical_past_race_source.py
tests/fixtures/jra/<approved official structural fixture files>
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

No c1a, c1b, snapshot builder, SQLite repository, migration, package root, bridge, capture, discovery, or acquisition change is authorized by this PREPARE phase.

## Allowed Files

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Stop Condition

Stop for independent architecture review.  Do not implement d1d1, a JRA normalizer, historical odds acquisition, accessU discovery, bridge, fixture capture, migration, or any NAR change.
