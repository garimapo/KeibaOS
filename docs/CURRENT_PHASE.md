# Current Phase

## Status

READY_FOR_REVIEW

## Phase

Phase 4C-2d3b1i6c1d3b2a — NAR historical past-race pair normalizer implementation

## Base Commit and Branch

Formal base: `21c0c644f9bf8641afa5f007cd7fb14ac9eb030e feat: add historical input evidence contract`

Formal branch: `feature/ver0.8-simulator`

Implementation review branch: `review/4c-2d3b1i6c1d3b2a-implementation`

Canonical workspace: `C:\Users\garim\Desktop\KeibaAI-review-1i5b2b`

The original workspace, `C:\Users\garim\Desktop\KeibaAI`, is read-only.

## Implemented Public Boundary

`scripts/simulation/nar_historical_past_race_source.py` defines only:

```python
normalize_nar_historical_past_race_source_record(
    *,
    target_entry_record: HistoricalInputSourceRecord,
    horse_history_response: NarSuppliedOfficialResponse,
    race_result_response: NarSuppliedOfficialResponse,
) -> HistoricalInputSourceRecord
```

It is one validated c1a `entry` record plus exactly one supplied HorseMarkInfo response and one supplied
RaceMarkTable response to exactly one c1a v3 `past_race` record. It reuses the existing NAR response and error
types; it introduces no public dataclass, error, package-root export, fetch, pagination, database, filesystem, or
clock responsibility.

## Target Binding and Identity

The target entry record must be exact `HistoricalInputSourceRecord`, `record_kind="entry"`, `organization="NAR"`,
`source_system="nar_official"`, and have a non-null external entry ID. The normalizer derives — and does not accept
caller overrides for — the target race, entry, and horse identity. It strictly validates:

- `nar:{YYYYMMDD}:{babaCode}:{raceNo}` target race identity;
- `{target_race_id}:entry:{horseNo}` target entry identity; and
- `nar:horse:{k_lineageLoginCode}`, with lexical `[1-9][0-9]*` lineage.

`TARGET_ENTRY_HORSE_NO_CONSISTENCY = REQUIRED`: the canonical horse-number suffix in `external_entry_id` must equal
the committed positive exact-int `record_values["horse_no"]`. This only validates internal coherence of the target
entry. `HISTORICAL_ROW_IDENTITY = LINEAGE_ONLY`: target horse number is never used to locate a historical RaceMarkTable
row and need not equal that historical race's horse number.

`JRA_CLASSIFICATION = ROW_STRUCTURAL_NOT_PAGE_GLOBAL_TEXT`. A HorseMarkInfo row is recognized as JRA-only only from
its own official JRA result-navigation structure and only when the relevant history table has no supported NAR
RaceMarkTable link. `MIXED_NAR_JRA_HISTORY_PAGE = SUPPORTED_FOR_EXACT_NAR_SELECTION`: unrelated JRA rows are ignored
when one NAR link has the requested complete date/babaCode/raceNo identity. A missing requested NAR identity is always
`NarHistoricalInputSourceValidationError`, even if unrelated page text says JRA or the table includes JRA rows.
`JOCKEY_AFFILIATION_JRA_DOES_NOT_IMPLY_JRA_RACE = YES`.

The binding chain is exact:

```text
target entry external_horse_id
  == HorseMarkInfo URL lineage
  == HorseMarkInfo selected history context
  == RaceMarkTable matched horse-row lineage
```

The selected HorseMarkInfo navigation link and RaceMarkTable URL must have the same complete historical date,
`babaCode`, and `raceNo`; the historical date is strictly before the target date. Horse names, target/historical horse
numbers, jockeys, row order, race names, local identifiers, and fuzzy text never identify the historical horse.

The resulting envelope retains target race/entry IDs and has provider result identity:

```text
nar:result:{YYYYMMDD}:{k_babaCode}:{k_raceNo}:horse:{k_lineageLoginCode}
```

The target entry is contextual binding only: its source ID, evidence, and provider ID are not copied into the
past-race record.

## URL, Evidence, and Causality Contract

HorseMarkInfo accepts HTTPS `www.keiba.go.jp` or `www2.keiba.go.jp`, path
`/KeibaWeb/DataRoom/HorseMarkInfo`, and exactly `k_lineageLoginCode`. RaceMarkTable accepts HTTPS
`www.keiba.go.jp` only, path `/KeibaWeb/TodayRaceInfo/RaceMarkTable`, and exactly
`k_babaCode`, `k_raceDate`, and `k_raceNo`. URLs reject credentials, fragments, controls, surrounding whitespace,
invalid ports, malformed percent escapes, plus ambiguity, duplicate/blank/unknown query values, noncanonical lexical
tokens, and invalid dates. `www` and `www2` are never rewritten.

The output has exactly these two distinct raw-response identities:

| role | source | available_at | observed_at |
| --- | --- | --- | --- |
| `historical_race_context` | HorseMarkInfo | `None` | exact supplied value |
| `historical_race_result` | RaceMarkTable | `None` | exact supplied value |

Each SHA-256 is computed from exact supplied bytes before UTF-8 decoding or HTML parsing. Changing either body changes
the past-race source ID; changing only an observed timestamp preserves its source ID and changes only evidence time.
The normalizer does not backdate, aggregate, or otherwise repair evidence timestamps. Existing c1c remains responsible
for capture/cutoff eligibility.

## Field Authority and Initial Support

HorseMarkInfo selected row owns `race_name`, `race_class`, and direct Decimal
`reference_time_difference_seconds`. RaceMarkTable owns race date/place/facts, matched-row finish/time/body weight
and change/jockey/popularity/odds/passing order, and fourth-corner evidence. Directly comparable facts are
cross-checked; disagreement fails validation. RaceMarkTable `着差` is never converted into seconds.

The verified representative result is `nar:result:20260503:31:1:horse:30074407776`:

| field | value |
| --- | --- |
| race_date/place/race_name/race_class | 2026-05-03 / 高知 / Ｃ２－８ / Ｃ２ |
| distance_m/track/weather/track_condition | 1400 / ダート / 雨 / 不良 |
| finish/reference_time_difference_seconds/race_time | 9 / Decimal("2.6") / 1:32.4 |
| weight/weight_diff/jockey | Decimal("495") / Decimal("1") / 妹尾浩 |
| popularity/odds | 8 / Decimal("42.5") |
| passing_order/fourth_corner_position | 9-9-9-11 / 11 |

`weight` is horse body weight, never assigned racing weight. Jockey affiliation is excluded while allowance symbols
are retained. Initial support is normal completed ordinary-NAR results only: positive completed finish/popularity/odds,
direct numeric difference, time, body-weight change, and all required corner evidence. JRA history, ばんえい,
cancelled/excluded/stopped/disqualified states, missing class/difference/time/odds/body weight, and ambiguous corners
are unsupported.

Passing order comes only from the matched row-local `コーナー通過順`. `全馬コーナー通過順` supplies ordered explicit
corner labels (`１…４コーナー` or `１…４角`) for positional alignment. Labels must be unique, increasing, contain
corner 4 exactly once, and equal the number of numeric row components. `fourth_corner_position` is the component
mapped to label 4; fixed-fourth and blind-last-component rules are forbidden.

## Fixture and Replay Limitation

The two fixtures are `MINIMIZED_AUTHENTIC_STRUCTURAL_FIXTURE`s derived from the official ordinary-NAR representative
pair. They retain the selected official structural headers, links, fields, result row, and corner labels; their test
timestamps are parser-test values, not trusted historical captures. Historical replay still requires separately
acquired source bytes observed causally before its cutoff. Acquisition, pagination, orchestration, and
`past_race_absence` remain out of scope.

## Allowed Files

```text
scripts/simulation/nar_historical_past_race_source.py
tests/test_nar_historical_past_race_source.py
tests/fixtures/nar/horse_mark_info_past_race_context.html
tests/fixtures/nar/race_mark_table_past_race_result.html
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

All c1a, evidence, c1b, c1c builder, SQLite, migration, schema, package-root, provider/parser, CLI, database, and
log files are forbidden. No c1a v4 field, past-race horse identity field, provider-record parsing in c1c, or target
entry evidence role was added.

## Required Verification and Stop Condition

Run the dedicated pair-normalizer tests; related c1b/c1a/c1c/snapshot tests; full pytest using the external Python
3.14.5 environment; forbidden dependency/source/AST and package-root export checks; `git diff --check`; and
`git status --short`. Stop at READY_FOR_REVIEW after one review commit and normal push. Do not integrate formally,
acquire pages, implement pagination, or implement `past_race_absence`.
