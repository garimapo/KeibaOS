# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6d1d5d1` — JRA zero-history past-race-absence source PREPARE.

Formal base: `0fba21a39f0d1b39dcb516c287d1d06bdcf9c35f`.

Review branch: `review/4c-2d3b1i6d1d5d1-jra-zero-history-absence-prepare`.

## Objective and Ownership

Freeze a narrow pure JRA boundary that turns only formal accessU proof of **zero actual prior starts** into one
provider-neutral `HistoricalInputSourceRecord(record_kind="past_race_absence")`. This closes the per-entry
past-history evidence alternative required before later historical collection/orchestration. It is neither accessU
parsing nor acquisition, archive work, race collection, accessS/accessO handling, normalization of a past race, or
Predictor work.

The future function must call the formal d1d5b3 discovery exactly once:

```python
discover_jra_historical_past_race_history(
    *,
    target_track_record: HistoricalInputSourceRecord,
    target_entry_record: HistoricalInputSourceRecord,
    horse_history_response: JRASuppliedOfficialResponse,
) -> JRAHistoricalPastRaceDiscovery
```

It must not independently inspect accessU HTML, row structure, aggregate tables, CP932 content, continuation markers,
target lineage, accessU horse identity, or chronology. Discovery remains the sole owner of target validation, strict
CP932, response-local aggregate-count completeness, zero-history proof, continuation rejection, and
`observed_at <= scheduled_start_at`.

## Frozen Proposed API and Surface

The next implementation must provide exactly:

```python
normalize_jra_historical_past_race_absence_source_record(
    *,
    target_track_record: HistoricalInputSourceRecord,
    target_entry_record: HistoricalInputSourceRecord,
    horse_history_response: JRASuppliedOfficialResponse,
) -> HistoricalInputSourceRecord
```

Module public names are exactly:

```text
JRAHistoricalPastRaceAbsenceSourceError
JRAHistoricalPastRaceAbsenceSourceValidationError
normalize_jra_historical_past_race_absence_source_record
```

No package-root export. The module is pure and owns no HTTP, archive/repository, SQLite, filesystem, environment,
clock, randomness, subprocess, accessS fetch, accessO locator/POST, bridge, or Predictor behavior.

Expected malformed-provider/target/discovery/source-record inputs are translated to
`JRAHistoricalPastRaceAbsenceSourceValidationError`. The implementation may narrowly catch discovery boundary errors
and `ValueError`, `TypeError`, `AttributeError`, or `OverflowError` needed to prevent incidental malformed-input
leaks; it must not catch `Exception` or conceal programmer/runtime defects.

## Zero-Actual-Start Acceptance

The absence record represents **zero actual prior starts**, not necessarily an empty displayed accessU history. The
following terms are deliberately distinct:

```text
EMPTY_OFFICIAL_HISTORY
= discovery.proven_zero_history is True and discovery.events == ()

ZERO_ACTUAL_PRIOR_STARTS
= no event in discovery.events has an actual-start event kind
```

The normalizer returns an absence record only for either exact discovery state:

```text
A. EMPTY_OFFICIAL_HISTORY

B. discovery.proven_zero_history is False
   discovery.events is nonempty
   every event.event_kind is JRAHistoricalEventKind.PROVEN_NON_START
```

d1d5b3's immutable discovery domain itself enforces
`proven_zero_history == (events == ())`. In state B, d1d5b3 has already established that the complete aggregate
actual-start total is zero: transfer rows such as `JRAへ転入` and `JRAより転出` are formal `PROVEN_NON_START` events
and do not contribute to its displayed actual-start count. The absence boundary may inspect only the formal
`proven_zero_history`, `events`, and closed `JRAHistoricalEventKind` projection; it must not reparse HTML or
recompute aggregate totals.

Reject any tuple containing `JRA_ACTUAL_START`, `NON_JRA_ACTUAL_START`, or `UNSUPPORTED_ACTUAL_START`. Thus an
actual JRA, NAR/local, overseas, or recognized unsupported prior start cannot become absence evidence. A history
with zero JRA starts but a non-JRA actual start is specifically not zero actual history. There is no caller override,
no “zero JRA starts” interpretation, and no fallback from an empty parser result.

Discovery owns the underlying exact no-data and aggregate-count proof in both accepted cases. Incomplete/truncated
aggregate counts, continuation, malformed response, target mismatch, horse mismatch, or a late observation fail in
discovery and are translated by this boundary.

## Exact Output and Evidence

The output is exactly:

```text
record_kind        = "past_race_absence"
organization       = "JRA"
source_system      = "jra_official"
external_race_id   = discovery.target_external_race_id
external_entry_id  = discovery.target_external_entry_id
provider_record_id = None
```

`jra_official` is fixed because formal discovery has already required the exact JRA target-track/entry family. Its
record values are exactly:

```python
{
    "external_entry_id": discovery.target_external_entry_id,
    "query_scope": {
        "external_entry_id": discovery.target_external_entry_id,
        "target_race_date": discovery.target_race_date,
        "strictly_before_target_race": True,
    },
    "result_count": 0,
}
```

There are no JRA-specific record values.

Create exactly one `HistoricalInputEvidenceReference` with:

```text
evidence_role             = "past_race_absence_query"
canonical_source_url       = horse_history_response.response_url
request_identity_sha256    = None (omitted from canonical payload)
response_sha256            = sha256(exact horse_history_response.response_body)
available_at               = None
observed_at                = horse_history_response.observed_at
```

Hash only the original exact supplied bytes; never decoded/re-encoded HTML. The one trusted accessU response is the
official evidence proving the zero-actual-start query, including transfer-only discovery state B. No separate
aggregate/history evidence references are added.

## Causality and Snapshot Compatibility

The normalizer does not introduce a clock or alter timestamps. Discovery requires its supplied response at or before
the target scheduled start. The absence evidence preserves the exact supplied `observed_at`; the existing
`HistoricalInputSnapshotBuilder` remains the sole owner of
`observed_at <= captured_at <= information_cutoff <= scheduled_start_at`.

No schema, migration, builder, repository, or neutral-domain change is required. Formal
`HistoricalInputSourceRecord` already permits `past_race_absence` with exactly
`external_entry_id/query_scope/result_count` and the one `past_race_absence_query` role. Formal builder grouping
requires each entry to have either one-or-more `past_race` records or exactly one absence record, rejects both forms
together, checks the absence query target date, and emits its established `past_race/<race_entry_id>/none`
provenance. Both empty official history and transfer-only, zero-actual-start discovery may therefore produce an
accepted absence record; any actual-start event prevents absence. Transfer events are not invented as `past_race`
records, while their official source remains auditable through the absence evidence.

## Recommended Implementation Scope

Recommended next phase: `4C-2d3b1i6d1d5d2` — JRA zero-history past-race-absence source implementation.

Exact recommended allowed files:

```text
scripts/simulation/jra_historical_past_race_absence_source.py
tests/test_jra_historical_past_race_absence_source.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

Tests must use minimal synthetic CP932 accessU responses and cover empty-history output/evidence/SHA/timestamps/
source-ID determinism; one and multiple `PROVEN_NON_START` transfer rows with zero actual starts; rejection of every
actual-start event kind even when transfer rows coexist; neutral record-set validation; snapshot-builder acceptance
for both empty and transfer-only zero-actual-start JRA entries; builder rejection of a past-race plus absence
conflict; incomplete/continuation/mismatch rejection; public surface; package-root absence; and forbidden
dependencies.

After formal d1d5d2 completion, the recommended design-only follow-on is
`4C-2d3b1i6d1d5e1` — JRA historical collection/orchestration PREPARE. Do not begin it now.

## Allowed Files

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Stop Condition

Create and push exactly one documentation review commit: `docs: prepare JRA zero-history absence source`. Do not
implement production or tests, change schema/capture/discovery/normalizer/orchestration, acquire/archive official
responses, synthesize CNAME material, build a bridge, or connect Predictor. Stop for independent review.
