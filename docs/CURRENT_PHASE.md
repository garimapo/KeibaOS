# Current Phase

## Status

READY_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6d1d5d2` — JRA zero-actual-start past-race-absence source implementation.

Formal base: `0fba21a39f0d1b39dcb516c287d1d06bdcf9c35f`.

Approved PREPARE: `9200030721eea582d59d890ff70a739f3cfa838b`.

Review branch: `review/4c-2d3b1i6d1d5d2-jra-zero-actual-start-absence`.

## Implemented Boundary

Added the pure provider-specific normalizer:

```python
normalize_jra_historical_past_race_absence_source_record(
    *,
    target_track_record: HistoricalInputSourceRecord,
    target_entry_record: HistoricalInputSourceRecord,
    horse_history_response: JRASuppliedOfficialResponse,
) -> HistoricalInputSourceRecord
```

Its module-defined public surface is exactly:

```text
JRAHistoricalPastRaceAbsenceSourceError
JRAHistoricalPastRaceAbsenceSourceValidationError
normalize_jra_historical_past_race_absence_source_record
```

No package-root export is added. The module is pure: it owns no accessU parsing, HTTP, archive/repository, SQLite,
filesystem, clock, randomness, subprocess, accessS/accessO work, orchestration, bridge, or Predictor behavior.

## Discovery Ownership and Acceptance

The normalizer calls formal d1d5b3 `discover_jra_historical_past_race_history(...)` exactly once. It treats the
returned exact discovery domain as the sole authority for target lineage, CP932, accessU identity, history parsing,
aggregate-count completeness, continuation, chronology, and the observation cutoff. It does not inspect raw HTML or
recompute flat/obstacle counts.

The accepted states are deliberately distinct:

```text
EMPTY_OFFICIAL_HISTORY
= discovery.proven_zero_history is True and discovery.events == ()

TRANSFER_ONLY_ZERO_ACTUAL_START
= discovery.proven_zero_history is False
   discovery.events is nonempty
   every event kind is JRAHistoricalEventKind.PROVEN_NON_START
```

The record means **zero actual prior starts**, not zero displayed events or zero JRA starts. Any event of kind
`JRA_ACTUAL_START`, `NON_JRA_ACTUAL_START`, or `UNSUPPORTED_ACTUAL_START` prevents absence, including when it
coexists with transfer events. Incoherent discovery state or type fails closed. The source does not invent a past-race
record for a transfer event.

## Output and Evidence

The output is exactly one existing neutral source record:

```text
record_kind        = "past_race_absence"
organization       = "JRA"
source_system      = "jra_official"
external_race_id   = discovery.target_external_race_id
external_entry_id  = discovery.target_external_entry_id
provider_record_id = None
```

Its record values contain no provider-specific fields:

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

`result_count` means zero actual prior starts. Exactly one evidence reference is emitted:

```text
evidence_role             = "past_race_absence_query"
canonical_source_url       = horse_history_response.response_url
response_sha256            = SHA-256(exact supplied response_body bytes)
available_at               = None
observed_at                = exact supplied observed_at
request_identity_sha256    = None
```

The normalizer neither decodes/re-encodes before hashing nor replaces timestamps. d1d5b3 owns
`observed_at <= scheduled_start_at`; the existing snapshot builder retains ownership of the later captured-at and
information-cutoff causal boundary.

## Snapshot Compatibility

The existing source-record validation accepts this exact neutral absence shape. The existing snapshot builder accepts
both empty official history and transfer-only zero-actual-start absence records, emits the established
`past_race/<race_entry_id>/none` provenance, and produces no past-race snapshot for that entry. It continues to reject
past-race plus absence evidence for one entry. No source/snapshot schema, migration, repository, or builder change is
required.

## Allowed Files

```text
scripts/simulation/jra_historical_past_race_absence_source.py
tests/test_jra_historical_past_race_absence_source.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Verification

Dedicated absence tests cover the exact public surface/purity, real discovery empty state, real transfer-only states,
all actual-start rejections, translated discovery failures, evidence SHA/timestamp source-ID semantics, neutral source
validation, snapshot compatibility for both accepted states, and the past-race/absence XOR.

Compatibility regressions cover d1d5b3 discovery, d1d5a normalizer, d1d5c2 locator/identity, JRA capture/archive/live,
NAR historical boundaries, and provider-neutral source/snapshot/builder behavior. Full-suite and static checks remain
required before review publication.

## Stop Condition

Create and push exactly one review commit: `feat: normalize JRA zero-actual-start history`. Do not formally integrate,
start historical collection/orchestration, acquire accessS/accessO evidence, perform real capture, modify schema or
migrations, implement a bridge, or connect Predictor. Stop for independent review.
