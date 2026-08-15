# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6d1d5b` — JRA complete horse-history discovery PREPARE.

Formal base: `367602e64353244e27b1518014c0907b922fb4ae`.

Review branch: `review/4c-2d3b1i6d1d5b-jra-history-discovery-prepare`.

This is design only. It changes no production code, test, fixture, capture, archive, normalizer, repository, schema,
or migration.

## Evidence Examined and Completeness Decision

The formal `JRASuppliedOfficialResponse` contract already recognizes an exact canonical accessU
`HORSE_PROFILE_HISTORY` response. Its URL is validated through `parse_jra_horse_profile_url_identity`; supplied
bytes remain strict CP932 and `observed_at` remains the actual supplied observation. The d1d5a normalizer remains
separate and consumes only trusted accessS/accessO pairs.

Read-only official accessU inspection established one displayed history-table shape:

```text
div.race_detail > table.basic.narrow-xy.striped
headings (ordered):
年月日, 場, レース名, 距離, 馬場, 頭数, 人気, 着順,
騎手名, 負担重量, 馬体重, タイム, Rt, 1着馬（2着馬）
```

The observed table has fourteen direct cells per history row, is reverse chronological, carries exact relative
accessS links for JRA starts, includes local/NAR actual starts without an accessS link, and includes explicit transfer
rows such as `JRAへ転入` and `JRAより転出`. No pagination, continuation, lazy-load, offset, or page control was observed
on that official response.

However, the official accessU page states that its race-history section covers JRA, local, and overseas starts **and**
states the explicit exception that a foreign horse is generally shown only its latest four past starts. Existing target
entry contracts establish only `jra:horse:<10 digits>`; they do not prove that a horse is outside that exception.
Consequently, one accessU response cannot prove `ALL_CAUSALLY_AVAILABLE_ACTUAL_PRIOR_STARTS` for every valid JRA
target entry.

```text
ACCESS_U_COMPLETE_HISTORY = NOT_PROVEN
ALL_PRIOR_STARTS_POLICY = BLOCKED_FOR_UNCONSTRAINED_JRA_TARGET
CONTINUATION_MODEL = NONE_OBSERVED_ON_INSPECTED_ACCESSU,
                     BUT_NO_SINGLE_RESPONSE_COMPLETENESS_CLAIM
```

The absence of observed paging is not a substitute for a complete-history proof. A future implementation must reject
any continuation-like structure rather than silently accepting a partial page; it cannot make a complete result merely
because no continuation control is found.

## Frozen Target and Causality Boundary

Any later discovery boundary must use exact `HistoricalInputSourceRecord` values only:

```text
target_track_record:
  type exactly HistoricalInputSourceRecord
  organization=JRA, source_system=jra_official, record_kind=track
  external_entry_id is None
  external_race_id parses through parse_jra_external_race_id
  record_values.target_race_date is exact date
  record_values.scheduled_start_at is exact aware datetime

target_entry_record:
  type exactly HistoricalInputSourceRecord
  organization=JRA, source_system=jra_official, record_kind=entry
  external_race_id exactly equals track external_race_id
  external_entry_id is non-null and equals build_jra_external_entry_id(...)
  record_values.external_entry_id agrees with the top-level value
  record_values.horse_no is positive and agrees with the entry-ID suffix
  record_values.external_horse_id is non-null canonical jra:horse:<10 ASCII digits>
```

`horse_history_response` must be exact `JRASuppliedOfficialResponse`, have the accessU
`HORSE_PROFILE_HISTORY` URL family, and parse to the same stable horse identity as the target entry. Name, date of
birth, pedigree, trainer, owner, and target horse number are forbidden identity fallbacks.

The supplied observation must satisfy:

```text
horse_history_response.observed_at <= target_track_record.record_values.scheduled_start_at
```

Every discovered historical actual start must have `historical_race_date < target_race_date`. No same-day ordering,
clock lookup, timestamp aggregation, or backdating is permitted. Historical replay before trustworthy capture
deployment remains fail closed.

## Closed Displayed-Event Vocabulary

If a future provider boundary is authorized, every displayed accessU history row must be classified or fail:

| event kind | exact initial interpretation | later normalization/collection consequence |
|---|---|---|
| `JRA_ACTUAL_START` | one structurally valid actual-start row with exactly one resolved official accessS navigation; its URL parses through `parse_jra_result_url_identity`, its CNAME calendar date is real and agrees with the displayed row date | carries the date, parsed `JRAExternalRaceIdentity`, and exact canonical accessS result URL; eligible only for later trusted accessS/accessO collection |
| `NON_JRA_ACTUAL_START` | a structurally valid actual-start row with no accessS navigation, including observed local/NAR and possible overseas display rows | retained for audit and completeness accounting; no JRA accessS identity or result URL is invented |
| `PROVEN_NON_START` | one exact row-local official transfer/non-start representation, initially limited to observed `JRAへ転入` / `JRAより転出` layouts with no conflicting actual-start facts or navigation | retained; never normalized as a race |
| `UNSUPPORTED_ACTUAL_START` | a recognized started row with unsupported status or semantics | retained as unsupported or causes the complete boundary to fail closed; never silently skipped |

Unknown rows, ambiguous link sets, duplicate identities, malformed dates, incomplete cells, unsupported status text, or a
row that does not meet one of these closed definitions are validation/unsupported failure; they are never discarded.
The historic race-local horse number is not a JRA stable identity and is not a cross-provider bridge.

For `JRA_ACTUAL_START`, the future reference must contain only directly supplied accessU evidence:

```text
historical_race_date
historical_race_identity: JRAExternalRaceIdentity
canonical_accessS_result_url
```

The tuple `(historical_race_date, historical_race_identity, canonical_accessS_result_url)` is the duplicate-detection
identity. No accessO locator, final odds, parsed result fact, synthetic CNAME, or target horse number belongs in this
reference. Canonical accessS URL construction must use only the exact resolved official anchor and existing public
JRA URL validation/canonicalization; it must not synthesize a result URL.

## Zero History, Continuation, and Mixed Providers

No explicit official accessU zero-history state was observed or proven. An empty/absent table, absence of JRA links,
or parser result containing no JRA starts is not proof of zero history.

```text
ZERO_HISTORY_PROOF = NOT_PROVEN
PROVEN_ZERO_HISTORY = UNSUPPORTED
ACCESS_O_LOCATOR_IN_DISCOVERY = NO
```

The accessU evidence demonstrates that JRA profile history can expose non-JRA actual starts. Those events remain in a
future displayed-event sequence; they cannot be skipped to make a JRA-only list appear complete. No official stable
JRA-horse-to-NAR-lineage linkage was established, so names, birth dates, and pedigree cannot bridge them.

```text
NAR_LINEAGE_TO_JRA_HORSE_ID_LINK = NOT_PROVEN
MIXED_HISTORY_COLLECTION_READY = NO
```

The later orchestration remains explicitly separate:

```text
accessU displayed-event discovery
-> exact JRA actual-start reference
-> trusted accessS response
-> accessO locator from actual official navigation material (never synthesized)
-> trusted accessO response
-> normalize_jra_historical_past_race_source_record(...)
```

No acquisition, archive lookup, HTTP, filesystem, SQLite, clock, pagination crawl, result normalizer invocation, or
Predictor connection belongs in discovery.

## API and Architecture Blocker

The proposed single-response complete API is **not frozen for implementation**:

```python
discover_jra_historical_past_race_history(
    *,
    target_track_record: HistoricalInputSourceRecord,
    target_entry_record: HistoricalInputSourceRecord,
    horse_history_response: JRASuppliedOfficialResponse,
) -> JRAHistoricalPastRaceDiscovery
```

It would falsely promise complete history for foreign horses covered by the official latest-four exception. A tuple of
the same accessU page cannot repair provider-level omission, and no authorized current contract identifies a complete
alternative source or a trustworthy non-foreign eligibility proof.

```text
ARCHITECTURE_BLOCKER =
  JRA accessU officially truncates foreign-horse history to latest four starts;
  current target/capture contracts cannot prove the target is outside that exception
  or provide a complete official continuation/source.
DISCOVERY_API = BLOCKED
```

The smallest recommended next phase is `4C-2d3b1i6d1d5b1 — JRA accessU complete-history eligibility/source
investigation PREPARE`, docs only. It must establish either (a) an exact official response-local proof that a target
is not subject to the foreign-horse limit, or (b) an official complete-history source and trusted supplied-response
contract. Until that proof exists, do not implement a complete-history discovery module.

```text
NEXT_PHASE_ALLOWED_FILES =
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Compatibility and Stop Condition

Source schema version remains 4; snapshot schema version remains 4; global migrations remain through 14; JRA capture
migrations remain `(1,2)`. NAR discovery/normalization, d1d5a normalization, JRA identity/capture/archive/live,
provider-neutral evidence/source/snapshot code, and package-root exports remain unchanged.

This PREPARE changes only `docs/CURRENT_PHASE.md` and `docs/LATEST_CODEX_REPORT.md`. Stop for independent design
review. Do not implement discovery, acquire or archive a response, perform a real trusted capture, add fixture HTML,
begin orchestration, connect Predictor, or begin a NAR/JRA bridge.
