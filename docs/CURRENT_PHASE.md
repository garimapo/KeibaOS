# Current Phase

## Status

READY_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6d1d5e0` — JRA discovery-to-absence projection handoff implementation.

Formal base: `a44df34017269b1b0a4e462b3bb775f7059681b7`.

Corrected e architecture review: `19f841071522106176a6828ea02b455f91c1ac6f`.

Review branch: `review/4c-2d3b1i6d1d5e0-jra-discovery-absence-projection`.

## Implemented Discovery Evidence Binding

Extended immutable/slotted `JRAHistoricalPastRaceDiscovery` with exactly:

```text
horse_history_response_url: str
horse_history_response_sha256: str
horse_history_observed_at: datetime
```

Formal discovery binds these values from the exact validated accessU `JRASuppliedOfficialResponse`: its canonical URL,
SHA-256 of its exact raw response bytes, and its normalized UTC observed timestamp. The discovery domain validates the
canonical accessU URL, URL horse identity against `target_external_horse_id`, lowercase SHA-256 grammar, and exact UTC
datetime representation. It also proves directly constructed target lineage: the target race is a canonical formal JRA
race ID, and the target entry is the exact canonical entry ID built from that race and a positive canonical horse-number
suffix. It stores no body and creates no evidence reference. Existing classification, aggregate completeness, chronology,
cutoff, and zero-history behavior remain unchanged.

### Target-Lineage Correction

The discovery constructor now fails closed for malformed or non-JRA target race IDs, entries for another race,
leading-zero/zero/noncanonical entry horse-number material, and other malformed entry lineage. It uses the existing
formal race parser and entry-ID builder; no entry parser or persisted field was added. Capture-domain URL validation
errors for malformed direct accessU evidence binding are translated to
`JRAHistoricalPastRaceDiscoveryValidationError`, so the public discovery boundary does not leak a lower-level capture
validation exception. A normally constructed forged discovery cannot reach absence projection.

## Public Projection

Added the pure public handoff:

```python
project_jra_historical_past_race_absence_source_record(
    *,
    discovery: JRAHistoricalPastRaceDiscovery,
    horse_history_response: JRASuppliedOfficialResponse,
) -> HistoricalInputSourceRecord
```

The absence module public surface is exactly:

```text
JRAHistoricalPastRaceAbsenceSourceError
JRAHistoricalPastRaceAbsenceSourceValidationError
normalize_jra_historical_past_race_absence_source_record
project_jra_historical_past_race_absence_source_record
```

No package-root export. Projection accepts only exact formal types and performs no discovery, HTML decode, or HTML
parsing. Before constructing the existing schema-v4 neutral absence record, it verifies exact URL, raw-byte SHA,
normalized observed timestamp, and accessU horse identity binding to discovery. Any mismatch or incoherent discovery
fails closed with the existing absence validation error.

Projection accepts only empty official history or a nonempty event tuple entirely composed of
`JRAHistoricalEventKind.PROVEN_NON_START`. It rejects every JRA, non-JRA, or unsupported actual-start event, including
transfer-plus-actual mixtures. Its output remains exactly the formal JRA `past_race_absence` record with one
`past_race_absence_query` evidence reference, zero actual prior starts, and no extra provider fields.

## Direct-Call Compatibility

`normalize_jra_historical_past_race_absence_source_record(...)` retains its exact signature and direct-call behavior.
It calls formal discovery exactly once, translates formal discovery errors as before, and delegates output construction
to the public projection using the original supplied response. The absence constructor is not duplicated.

This enables a future collector to run discovery once and call projection only for the zero-actual-start branch,
without private-helper coupling or a second accessU parse.

## Compatibility and Boundaries

No source schema, snapshot schema, migration, capture/archive, repository, live transport, NAR, neutral validator,
snapshot builder, package-root export, bridge, or Predictor change occurred. The existing source record and snapshot
builder continue to accept empty and transfer-only absence results and reject past-race plus absence conflicts.

## Allowed Files

```text
scripts/simulation/jra_historical_past_race_discovery.py
scripts/simulation/jra_historical_past_race_absence_source.py
tests/test_jra_historical_past_race_discovery.py
tests/test_jra_historical_past_race_absence_source.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Verification

Dedicated discovery and absence tests cover the three bound fields, exact raw-byte SHA, canonical accessU URL,
normalized observed time, horse identity, frozen/slotted domain behavior, zero-discovery projection, one-discovery
direct normalizer delegation, empty/transfer output parity, mismatched types/binding failures, actual-event rejection,
neutral validation, and snapshot compatibility. The correction adds normal-constructor target race/entry lineage and
accessU exception-boundary regressions. Fresh verification passed 22 dedicated tests, 138 related tests, and 2,610
full-suite tests; package-export, forbidden-dependency/source/AST, source/snapshot/migration-unchanged, and diff
checks passed.

## Stop Condition

Create and push exactly one correction commit: `fix: harden JRA discovery target lineage`. Do not implement
the source collector, collector tests, HTTP/live capture, archive/repository/database/migration work, real capture,
mixed-provider bridge, or formal integration. Stop for independent implementation review.
