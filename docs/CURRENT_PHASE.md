# Current Phase

## Status

READY_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6c1d3b2c1` — pure NAR HorseMarkInfo complete-history discovery and zero-history absence normalization.

Formal base: `93fad49e7b188e3b4492cc7fe0eb61d36d16b735`.

Implementation review branch: `review/4c-2d3b1i6c1d3b2c1-implementation`.

Approved completeness design: `db9329ac6febddabf7f5289f6440250e6cdba5fb`.

## Implemented Pure Boundaries

`discover_nar_historical_past_race_history` accepts exactly one validated target track record, target entry record,
and supplied UTF-8 HorseMarkInfo response. It returns the complete official row order without NAR filtering or a
5/10/20-race truncation. The target race date comes only from the target track record and every discovered event must
strictly precede it; the supplied observation must also be no later than the target scheduled start.

The public discovery domain is exactly:

```text
NARHistoricalEventKind
NARHistoricalPastRaceReference
NARHistoricalPastRaceDiscovery
NARHistoricalPastRaceDiscoveryError
NARHistoricalPastRaceDiscoveryValidationError
NARHistoricalPastRaceDiscoveryUnsupportedError
discover_nar_historical_past_race_history
```

The closed event vocabulary is `NAR_ACTUAL_START`, `JRA_ACTUAL_START`, `PROVEN_NON_START`, and
`UNSUPPORTED_ACTUAL_START`. NAR rows use `nar:event:{YYYYMMDD}:{babaCode}:{raceNo}` and reconstruct the canonical
`www.keiba.go.jp` RaceMarkTable URL from the proven row-local identity. Structurally recognized JRA starts remain in
the complete sequence with a deterministic row-local date/place/R identity and no NAR result URL. The approved
`取消`/`取止` non-result pattern is retained as `PROVEN_NON_START` with its NAR event identity and audit URL, but it
is not an actual start and is not a later RaceMark capture candidate. Unknown or unapproved states fail closed.

HorseMarkInfo accepts canonical `www.keiba.go.jp` and `www2.keiba.go.jp` inputs while preserving the supplied host
identity. It requires the exact target lineage, expected document identity, one complete official table or the exact
zero-history layout (never both), complete parseable rows, unique event IDs, non-increasing official chronology, and
no continuation, pagination, extra table, or hidden additional history marker.

The HISTORY_TABLE schema is now fail-closed: its normalized 21-heading tuple must equal the approved fixture order
exactly. Unknown, duplicate, missing, or reordered headings are rejected. `天候・馬場` is the only span and must be
exactly `colspan="3"`; no heading may have `rowspan`, and no other heading may have `colspan`. Every history row has
exactly 23 direct unspanned `td` cells. The stricter schema applies only to the HISTORY_TABLE state; the exact
no-table zero-history state is unchanged.

`normalize_nar_historical_past_race_absence_source_record` accepts the same three inputs and internally reruns
discovery; it never trusts a caller-provided empty sequence. Only the exact official zero-history layout creates one
v3 `past_race_absence` record. Its c1a payload is exactly the target entry scope, target race date,
`strictly_before_target_race=True`, and `result_count=0`; its sole evidence is the exact HorseMarkInfo response body
SHA-256, canonical supplied URL, `available_at=None`, and supplied `observed_at`.

## Fixture and Scope Decision

Both fixtures are `MINIMIZED_AUTHENTIC_STRUCTURAL_FIXTURE`s: official HorseMarkInfo page/table, result-link,
JRA-row, and zero-layout semantics were retained. They are parser fixtures only, not trusted historical captures.
No production network, archive, SQLite, filesystem, clock, JRA result normalization, collection, snapshot building,
or prediction configuration was added.

`HORSE_MARK_COMPLETE_ACTUAL_START_SOURCE = YES`; `RACE_HORSE_INFO_RUNTIME_REQUIRED = NO`; and
`PAST_RACE_ABSENCE_PROOF_SOURCE = HORSEMARKINFO_ONLY` remain frozen. JRA result normalization is not implemented,
and complete mixed-history collection remains blocked until its separate official source support exists.

## Allowed Files

```text
scripts/simulation/nar_historical_past_race_discovery.py
scripts/simulation/nar_historical_past_race_absence_source.py
tests/test_nar_historical_past_race_discovery.py
tests/test_nar_historical_past_race_absence_source.py
tests/fixtures/nar/horse_mark_info_history_discovery.html
tests/fixtures/nar/horse_mark_info_zero_history.html
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Stop Condition

Stop after one review commit and independent implementation review. Do not start JRA historical result normalization,
d3b2c2 collection, d3b2c3 composition, d3b2d prediction integration, or formal integration.
