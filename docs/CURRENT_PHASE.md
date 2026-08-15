# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6d1d5e` — JRA historical source collection PREPARE correction.

Formal base: `a44df34017269b1b0a4e462b3bb775f7059681b7`.

Review branch: `review/4c-2d3b1i6d1d5e-jra-history-collection-prepare`.

## Corrected Outcome

The JRA historical source collector is **not implementation-ready**. Formal d1d5d2 absence normalization owns and
executes d1d5b3 discovery internally, while the collector requires one discovery call for every branch. Calling the
existing absence normalizer after collector discovery would execute discovery twice; recreating its record would
duplicate a formal boundary. Phase `4C-2d3b1i6d1d5e1` must not start until the predecessor below is formally complete
and the collector receives a fresh PREPARE/review against that new formal base.

The nonzero collector architecture remains provisional only. It continues to require
`ALL_CAUSALLY_AVAILABLE_ACTUAL_PRIOR_STARTS`, newest-to-oldest output, exact accessS/accessO binding, in-call reuse,
final neutral validation, fail-closed mixed/unsupported history, and no partial return, but none of those provisional
collector declarations authorizes production work in this phase.

## Recommended Predecessor Phase

Phase `4C-2d3b1i6d1d5e0` — JRA discovery-to-absence projection handoff implementation.

Its objective is to expose a public, pure absence projection from one already-validated exact discovery and the exact
accessU supplied response that produced it. It preserves the existing direct-call API and makes one discovery result
reusable without parsing accessU HTML again.

## Exact Discovery Evidence Binding

`JRAHistoricalPastRaceDiscovery` must add exactly these immutable fields:

```text
horse_history_response_url: str
horse_history_response_sha256: str
horse_history_observed_at: datetime
```

`discover_jra_historical_past_race_history(...)` populates them from the exact validated
`JRASuppliedOfficialResponse`:

```text
horse_history_response_url
  = canonical horse_history_response.response_url

horse_history_response_sha256
  = SHA-256(exact horse_history_response.response_body bytes)

horse_history_observed_at
  = exact normalized horse_history_response.observed_at
```

The discovery domain validates exact field types, canonical accessU URL/horse identity, lowercase 64-character SHA-256
grammar, aware UTC observation time, and the existing target lineage. This is evidence binding only: it does not store
the body, create evidence references, change event classification, or weaken the existing
`horse_history_observed_at <= target scheduled_start_at` discovery check.

## Exact Projection Public API

Add this public function to `scripts/simulation/jra_historical_past_race_absence_source.py`:

```python
project_jra_historical_past_race_absence_source_record(
    *,
    discovery: JRAHistoricalPastRaceDiscovery,
    horse_history_response: JRASuppliedOfficialResponse,
) -> HistoricalInputSourceRecord
```

The exact module public surface becomes:

```text
JRAHistoricalPastRaceAbsenceSourceError
JRAHistoricalPastRaceAbsenceSourceValidationError
normalize_jra_historical_past_race_absence_source_record
project_jra_historical_past_race_absence_source_record
```

No package-root export is added.

Both arguments must have exact formal types. The projection performs no discovery and no HTML decode or parse. It
must verify all of the following before constructing a record:

```text
horse_history_response.response_url
  == discovery.horse_history_response_url

SHA-256(exact horse_history_response.response_body bytes)
  == discovery.horse_history_response_sha256

horse_history_response.observed_at
  == discovery.horse_history_observed_at

parse_jra_horse_profile_url_identity(horse_history_response.response_url).external_horse_id
  == discovery.target_external_horse_id
```

The final identity check may use the formal URL identity parser only; it must not parse response HTML. URL, horse,
SHA, timestamp, type, or discovery-invariant disagreement raises
`JRAHistoricalPastRaceAbsenceSourceValidationError`. No fallback, closest/latest lookup, reconstructed response, or
caller assertion is accepted.

## Exact Accepted and Rejected States

The projection accepts exactly:

```text
EMPTY_OFFICIAL_HISTORY
  discovery.proven_zero_history is True
  discovery.events == ()

TRANSFER_ONLY_ZERO_ACTUAL_START
  discovery.proven_zero_history is False
  discovery.events is nonempty
  every event kind is JRAHistoricalEventKind.PROVEN_NON_START
```

It rejects incoherent discovery and every sequence containing at least one `JRA_ACTUAL_START`,
`NON_JRA_ACTUAL_START`, or `UNSUPPORTED_ACTUAL_START`, including transfer-plus-actual mixtures. Transfer events emit
no past-race record. Absence means zero actual prior starts, not zero displayed events or zero JRA starts.

The output remains the existing schema-v4 neutral record exactly:

```text
record_kind        = past_race_absence
organization       = JRA
source_system      = jra_official
external_race_id   = discovery.target_external_race_id
external_entry_id  = discovery.target_external_entry_id
provider_record_id = None
result_count       = 0
```

Its sole `past_race_absence_query` evidence uses the discovery-bound canonical URL, exact response-body SHA, exact
observed time, `available_at=None`, and `request_identity_sha256=None`. Existing query-scope semantics remain
unchanged.

## Existing API Compatibility and Call Count

`normalize_jra_historical_past_race_absence_source_record(...)` retains its exact signature, public name, exception
family, output, and direct-call semantics. It must:

1. call `discover_jra_historical_past_race_history(...)` exactly once;
2. translate a formal discovery error to `JRAHistoricalPastRaceAbsenceSourceValidationError` as today; and
3. call the new public projection with that discovery and the original supplied response.

The projection calls discovery zero times. A future collector will call discovery exactly once and pass its result to
the public projection on the zero-actual-start branch. Neither path may import a private helper or duplicate the
absence-record constructor.

## Exception Contract

No new exception class is added. Wrong exact types, invalid discovery state, response/discovery binding mismatch,
identity mismatch, or neutral record construction failure raise
`JRAHistoricalPastRaceAbsenceSourceValidationError`, derived from
`JRAHistoricalPastRaceAbsenceSourceError`. Existing discovery-error translation remains unchanged for direct callers.

## Future Collector Causality Contract

The later collector PREPARE must freeze these checks before implementation:

- accessU discovery retains its existing `observed_at <= target scheduled_start_at` proof;
- every injected accessS `JRASuppliedOfficialResponse.observed_at` must be no later than the target
  `scheduled_start_at`;
- every injected accessO `JRAFinalWinOddsSuppliedOfficialResponse.observed_at` must be no later than the target
  `scheduled_start_at`;
- a later observation fails the entire collection before return;
- timestamps are never replaced or backdated;
- the collector does not invent `information_cutoff` or `captured_at`; the snapshot builder retains the stricter final
  eligibility check against caller-supplied cutoff/capture values.

Thus a collector cannot return a nominally complete source collection containing evidence first observed after the
target race start, while the snapshot boundary still owns the full
`observed_at <= captured_at <= information_cutoff <= scheduled_start_at` check.

## e0 Allowed Files

```text
scripts/simulation/jra_historical_past_race_discovery.py
scripts/simulation/jra_historical_past_race_absence_source.py
tests/test_jra_historical_past_race_discovery.py
tests/test_jra_historical_past_race_absence_source.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

No other file is allowed. In particular, no collector module or collector test may be created in e0.

## e0 Required Tests

Dedicated tests must prove:

- discovery exposes the exact three evidence-binding fields and keeps immutable/slotted exact-type invariants;
- binding uses exact response bytes, canonical accessU URL, exact normalized observed time, and formal horse identity;
- existing empty, transfer-only, JRA, non-JRA, unsupported, chronology, completeness, and cutoff discovery behavior is
  unchanged;
- projection performs zero discovery calls and zero HTML parsing;
- existing direct normalizer performs exactly one discovery call and delegates to the public projection;
- exact empty and transfer-only projection outputs remain byte/SHA/timestamp/source-ID compatible with the current
  formal output;
- wrong discovery/response types, URL, body SHA, timestamp, horse identity, and incoherent discovery fail closed;
- every actual-start kind and every transfer-plus-actual mixture is rejected;
- public module surface and no package-root export are exact;
- source validation and snapshot absence compatibility remain unchanged.

Run the dedicated discovery and absence suites, the related JRA identity/source/snapshot regressions, and the full
suite with the formal verification Python. Also run package-export, forbidden-dependency/AST, unchanged-schema,
unchanged-migration, `git diff --check`, and final status checks. Report every exact command and result.

## e0 Forbidden Dependencies and Changes

Production modules must not import HTTP/live capture, archive/repository, SQLite/database, filesystem, clock/current
time, sleep/retry, Predictor, or NAR bridge code. No HTML parser is added to the absence module. No source or snapshot
schema version, migration, capture format, archive API, neutral validator, snapshot builder, mixed-provider identity,
or prediction behavior changes. No real official response is fetched or archived.

## Schema and Readiness

```text
SOURCE_SCHEMA_CHANGE_REQUIRED = NO
SNAPSHOT_SCHEMA_CHANGE_REQUIRED = NO
MIGRATION_REQUIRED = NO
JRA_ONLY_COLLECTION_READY = NO
COMPLETE_MIXED_HISTORY_COLLECTION_READY = NO
NAR_LINEAGE_TO_JRA_HORSE_ID_LINK = NOT_PROVEN
```

The discovery-domain evidence binding is not a persisted source/snapshot schema change. Collector readiness may be
reconsidered only after e0 is formally integrated and independently remote-verified.

## Current Correction Allowed Files

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Current Stop Condition

Create and push exactly one additional documentation review commit:
`docs: refine JRA historical collection prerequisites`. Do not amend the existing review commit. Do not implement e0
or e1, add tests, perform capture/database/migration work, implement a bridge, modify Predictor, or formally integrate.
Stop for independent architecture re-review.
