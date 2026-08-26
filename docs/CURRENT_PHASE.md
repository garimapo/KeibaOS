# Current Phase

## Status

`DRAFT_FOR_REVIEW`

## Phase

`4C-2d3b1i6d1d5f1c4h0` — JRA official target-race result normalization and
persistence.

Formal base: `90203b01cf370469e15242325ee40888d99d0f58`.

PREPARE review branch:
`review/4c-2d3b1i6d1d5f1c4h0-jra-target-result-prepare`.

## Hierarchy Decision

The existing hierarchy ends its required historical planning and settlement core at
`4C-2d3b1i6d1d5f1c4g2b`. `4C-2d3b1i6d1d5f1c4g2c` is reserved only for optional
per-race `SimulationResult` or settlement-evidence audit persistence. It is not the
official-data acquisition phase.

The design does not already assign an ID to official target-race result/payout
acquisition. The smallest consistent extension is therefore a new sibling `c4h`
family. The family is split by provider and fact type so no implementation phase must
simultaneously invent two provider parsers, two completeness policies, and an
application runner:

- `4C-2d3b1i6d1d5f1c4h0` — JRA official target-race result normalization and
  persistence.
- `4C-2d3b1i6d1d5f1c4h1` — JRA official target-race payout normalization and
  persistence.
- `4C-2d3b1i6d1d5f1c4h2` — NAR official target-race result normalization and
  persistence.
- `4C-2d3b1i6d1d5f1c4h3` — NAR official target-race payout normalization and
  persistence.
- `4C-2d3b1i6d1d5f1c4h4` — official settlement acquisition/application composition,
  cutoff choice, and final-completeness checks.

JRA result normalization is first because the formally complete historical replay path
is currently JRA-first and already has exact accessS race identity, immutable response
capture, live capture transport, archive persistence, and internal historical snapshot
crosswalks. The missing boundary is full target-race result interpretation and
persistence. Payout parsing remains a separate phase even if the same accessS response
contains both fact families.

## Purpose and Hard Separation

The complete future direction is:

```text
approved official response capture
+ exact HistoricalInputSnapshot race/entry crosswalk
-> provider-specific fail-closed parser and normalizer
-> provider-neutral PersistedRaceResult / PayoutPublication
-> existing RaceResultRepository / PayoutRepository
-> caller-selected settlement cutoff
-> existing c4g2a + c4g2b
-> AS_OF_SETTLEMENT_CUTOFF SimulationSummary
```

The acquisition family owns no prediction, historical snapshot mutation, bet
generation, allocation, plan mutation, settlement calculation, or summary calculation.
It does not call c4g0, c4g1, c4g2a, or c4g2b. Official result and payout facts never flow
back into `HistoricalInputSnapshot`, `SimulationRaceInput.pipeline_input`, prediction,
strategy, allocation, or a persisted bet plan.

## Existing Acquisition State

### JRA

The existing JRA boundary already provides:

- exact accessS race-result URL parsing through `parse_jra_result_url_identity`;
- race-local external entry IDs through `build_jra_external_entry_id`;
- `JRAOfficialPageKind.RACE_RESULT`;
- immutable strict-cp932 `JRAOfficialResponseCapture` values with canonical URL,
  response bytes, digest, capture ID, requested/observed/stored times, and HTTP facts;
- append-only capture archive and SQLite implementation;
- trusted live HTTPS capture that archives before returning; and
- exact reconstruction of a supplied response from archived evidence.

Existing JRA historical source code parses one selected horse's past-race facts from an
accessS result page. It is not a complete target-race result parser, does not classify
the whole race, and does not produce or persist target-race payouts.

Current status:

```text
JRA_TARGET_RESULT_ACQUISITION_STATUS:
CAPTURE_AND_ARCHIVE_READY_FULL_TARGET_RESULT_NORMALIZATION_AND_PERSISTENCE_MISSING

JRA_TARGET_PAYOUT_ACQUISITION_STATUS:
ACCESS_S_CAPTURE_READY_TARGET_PAYOUT_PARSER_COMPLETENESS_AND_PERSISTENCE_MISSING
```

### NAR

The existing NAR boundary already provides:

- exact canonical RaceMarkTable URL identity from `k_raceDate`, `k_babaCode`, and
  `k_raceNo`;
- immutable strict-UTF-8 `NAROfficialResponseCapture` values with response digest,
  capture ID, and exact observation times;
- append-only capture archive and SQLite implementation; and
- trusted live HTTPS capture that archives before returning.

Existing NAR historical code parses one selected horse's past-race facts from a
HorseMarkInfo/RaceMarkTable pair. It is not a complete target-race result parser. The
repository contains no formal NAR target-payout section parser or completeness rule.

Current status:

```text
NAR_TARGET_RESULT_ACQUISITION_STATUS:
RACE_MARK_TABLE_CAPTURE_READY_FULL_TARGET_RESULT_NORMALIZATION_AND_PERSISTENCE_MISSING

NAR_TARGET_PAYOUT_ACQUISITION_STATUS:
RACE_MARK_TABLE_CAPTURE_FAMILY_READY_TARGET_PAYOUT_EVIDENCE_CONTRACT_AND_PERSISTENCE_MISSING
```

Legacy `JRAFetcher` is hard-coded sample data. Legacy `NARProvider` returns decoded text,
writes ad-hoc files under `logs/`, and uses unstable `hash(url)` filenames. Neither is
an approved settlement evidence boundary. New settlement work must use the formal
immutable capture services and archives instead.

## Provider-Neutral Persistence Contract

Reuse unchanged:

- `PersistedRaceResult`;
- `PersistedRaceResultEntry`;
- `PayoutPublication`;
- `PayoutRecord`;
- `RaceResultRepository`; and
- `PayoutRepository`.

No second settlement-domain model is introduced. The v008 schema and existing SQLite
repositories already persist these values and enforce exact race-entry foreign-key
membership. The capture ID is the normalization provenance value in `source`; payout
publications also retain the canonical `source_url`. Raw capture bytes remain in the
existing immutable capture archive and are saved before any normalization or domain
write.

The `RaceResultRepository` protocol is reused without adding idempotence or versioning
promises. The current SQLite implementation is sufficient only for a final-result
insert-once policy: an equal repeat succeeds and a differing result conflicts. It is not
sufficient for provisional-to-final replacement or as-of correction replay. C4h0 must
persist only an officially terminal result with its actual evidence observation time.
A positively recognized provisional/partial page remains safely archived but produces
no `RaceResultRepository` write, so c4g2a continues to see the result as unavailable and
returns `UNSETTLED`. A differing later correction fails closed and requires a separately
reviewed result-versioning phase; it must not overwrite or repair the stored result.

The `PayoutRepository` protocol is reused unchanged. Its current SQLite implementation
is sufficient for corrections because it stores multiple immutable publications ordered
by `observed_at` and publication ID. A later correction becomes another publication and
never mutates an earlier one.

## Exact Provider-to-Internal Identity

Every normalization call is bound to one exact `HistoricalInputSnapshot`. The capture's
provider race identity must equal the snapshot's exact
`(organization, source_system, external_race_id)` before any row is normalized or any
domain write occurs.

JRA mapping is:

```text
accessS canonical URL
-> parse_jra_result_url_identity(...).external_race_id
-> exact snapshot source external_race_id
-> snapshot.internal_race_id

result/payout horse number inside that exact accessS race
-> build_jra_external_entry_id(exact race identity, horse_no)
-> exact matching snapshot.entries[].external_entry_identity.external_entry_id
-> exact snapshot.entries[].race_entry_id
```

NAR mapping is:

```text
RaceMarkTable canonical URL k_raceDate/k_babaCode/k_raceNo
-> nar:{YYYYMMDD}:{babaCode}:{raceNo}
-> exact snapshot source external_race_id
-> snapshot.internal_race_id

result/payout horseNum inside that exact RaceMarkTable race
-> {exact external_race_id}:entry:{horseNum}
-> exact matching snapshot.entries[].external_entry_identity.external_entry_id
-> exact snapshot.entries[].race_entry_id
```

Horse number is therefore permitted only after the exact provider and target-race
identity are proven and only through the snapshot's complete race-local crosswalk.
Horse names, jockey names, global horse-number queries, cross-provider numeric
coincidence, prediction selections, row position, and display order are forbidden.
Missing, duplicate, wrong-race, or contradictory mappings fail closed before
persistence.

## Result Semantics

Provider-specific parsing must map only positively recognized official states:

- a formally final result with complete exact entry coverage becomes
  `RaceResultStatus.COMPLETE`;
- a positively recognized provisional or partial result maps semantically to
  `RaceResultStatus.PARTIAL`, must never be upgraded from row count alone, and remains
  capture-only under the final-only insert policy rather than being saved into the
  insert-only result repository;
- an explicitly cancelled, void, or non-established race becomes
  `RaceResultStatus.VOID`;
- a positively recognized state outside the supported formal result domain becomes
  `RaceResultStatus.UNSUPPORTED`; and
- an unknown, malformed, ambiguous, or contradictory state fails closed and is not
  persisted.

Entry mapping is:

- an officially confirmed finisher has `RaceResultEntryStatus.CONFIRMED` and an exact
  positive finish position;
- an explicitly scratched, excluded, or cancelled entry has
  `RaceResultEntryStatus.VOID` and no finish position;
- disqualification, non-finish, race-stoppage entry states, and other recognized states
  that the current three-value entry enum cannot faithfully distinguish become
  `RaceResultEntryStatus.UNSUPPORTED` with no finish position; and
- unknown or contradictory status/position combinations fail closed.

Dead heat is represented by multiple confirmed entries sharing the same positive finish
position. It must not be rank-renumbered or tie-broken. Every corresponding official
winning payout row remains present. Scratches/exclusions never remove or renumber the
snapshot entry and never become a loss by omission.

## Payout Semantics

The currently supported settlement/persistence bet types are exactly:

```text
単勝
馬連
ワイド
3連複
```

`複勝`, `枠連`, `馬単`, and `3連単` are currently outside the formal `BET_TYPES` domain.
In particular, ordered `馬単`/`3連単` cannot be represented by the current sorted
selection identity, and frame-based `枠連` is not a race-entry selection. C4h must not
silently coerce or discard these types, and widening the domain belongs to a separately
approved phase.

For supported types, every official winning combination maps to one canonical sorted
tuple of exact internal `race_entry_id` values and its exact integer
`payout_per_100`. Multiple winners and dead-heat payouts remain distinct records.
Selection-specific refunds map to exact affected canonical selections. A provider-wide
refund/all-refund may be expanded only when the exact official rule and complete exact
race universe deterministically identify every affected supported selection; otherwise
the publication remains incomplete or the parser fails closed. Explicit void and
unsupported records use the existing formal payout statuses. Zero winning payout,
unknown text, missing selection identity, and malformed values fail closed.

A positively identified but not-yet-final supported bet-type table may be persisted as
`is_complete=False`, with only safely parsed records and `finalized_at=None`. Missing
evidence alone does not create a publication. Unknown structure or ambiguous omissions
are parser failures, not losses. A publication may be `is_complete=True` only when the
same exact captured official response proves all of the following for that bet type:

- exact target race identity;
- explicit final/complete official state;
- exactly one recognized supported bet-type section;
- every published winning/refund/void row parsed without omission;
- every selection resolved through the exact race-local crosswalk;
- no unknown status, duplicate identity, malformed amount, or unclassified row; and
- positive evidence for an empty/no-winning-row state where the provider permits it.

These rules apply to both JRA and NAR. Provider-specific final markers, section
selectors, row grammars, and empty/refund representations must be frozen from approved
trusted response evidence before their parser implementation. An incomplete latest
publication is intentionally preserved as incomplete so c4g2a yields `UNSETTLED`; an
older complete publication is not substituted.

## Temporal Evidence

`observed_at` is exactly the immutable capture's aware observation time sampled after
the complete HTTP response bytes were received and before parsing. It is never the race
date, scheduled start, displayed page date, database insertion time, file mtime, or a
caller-invented historical time.

`finalized_at` is an exact provider-attested finalization/publication timestamp only
when the same captured record formally supplies one. When the provider supplies no
trustworthy exact final timestamp but the capture positively proves a final state, the
conservative first-proven-final value is the exact capture `observed_at`; it is not
backdated. Partial result or payout evidence has `finalized_at=None`.

For a trusted historical archive, replay time comes from the capture's already-attested
historical `observed_at`. A live response fetched now is observed now and can support
only a settlement cutoff at or after that observation. It cannot establish that the
fact was available at an earlier historical cutoff.

```text
BACKDATED_LIVE_RESPONSE:
FORBIDDEN
```

Acquisition stores facts and evidence. It does not choose c4g2a settlement cutoffs.
Cutoff choice and the check that all intended races have reached final formal statuses
belong to c4h4's application boundary. A summary with unresolved races remains an
as-of-cutoff summary and must not be labelled final ROI.

## Source Capture and Correction Policy

The required order is:

```text
HTTP response bytes
-> validate and immutably archive exact capture
-> parse/normalize the archived capture
-> save provider-neutral domain values
```

No HTTP-to-domain direct write is allowed. Parser or repository failure leaves the raw
capture archived. The domain value's `source` binds the exact capture ID so the raw
response can be audited. No raw response is reconstructed from normalized rows.

JRA and NAR use their existing capture layers unchanged. Current live capture records
actual observation time. A supplied trusted historical capture must already satisfy the
same archive and timing contract; filename, source URL alone, copied HTML, and claimed
race date are insufficient attestation.

## No Silent Fallback

```text
NO_RESULT_FOUND:
NOT_COMPLETE

NO_PAYOUT_FOUND:
NOT_COMPLETE

PARSER_UNKNOWN_STATE:
FAIL_CLOSED

MISSING_ID_CROSSWALK:
FAIL_CLOSED

PARTIAL_PUBLICATION:
NOT_COMPLETE

UNSUPPORTED:
ONLY_EXPLICIT_FORMAL_CLASSIFICATION
```

Missing or incomplete acquisition is never converted into a loss, complete result,
void result, empty payout, or `NO_BET`.

## Recommended Implementation Scope and Blocker

Candidate c4h0 implementation scope after the blocker is resolved:

- new `scripts/simulation/jra_target_race_result_persistence.py`;
- new `tests/test_jra_target_race_result_persistence.py`;
- one approved trusted JRA accessS target-result fixture/capture if review authorizes it;
- `docs/CURRENT_PHASE.md`; and
- `docs/LATEST_CODEX_REPORT.md`.

C4h0 consumes an exact `capture_id`, structural `JRAOfficialResponseCaptureArchive`,
exact `HistoricalInputSnapshot`, and structural `RaceResultRepository`. It exact-loads
the already archived `JRAOfficialResponseCapture` before parsing, validates complete
identity and terminal result semantics before the first domain write, constructs one
exact `PersistedRaceResult` with `source=capture.capture_id`, saves it exactly once, and
returns the exact normalized value. A missing capture or nonterminal result performs no
result write. It owns no HTTP, payout parsing, cutoff choice, settlement, or prediction.

Implementation is not yet ready. The repository has synthetic fragments and single
past-horse parsing tests, but no approved trusted full target-race accessS capture/fixture
that freezes the exact final-result marker, complete-table membership, scratch,
disqualification/non-finish, cancellation, and dead-heat representations. Guessing those
provider facts would risk persisting provisional or incomplete results as complete.

The exact blocker is:

```text
APPROVED_TRUSTED_JRA_TARGET_RESULT_EVIDENCE_CONTRACT:
MISSING
```

Once independently supplied/approved evidence freezes those representations, c4h0 can
be revised to `IMPLEMENTATION_READY: YES_AFTER_INDEPENDENT_APPROVAL` without changing
the existing domain, repository, capture archive, schema, or simulation core.

## Future Test Contract

### Identity

- accessS identity must exactly equal the snapshot's JRA external race identity;
- every horse number must resolve through the exact race-scoped external entry ID;
- duplicate, missing, wrong-race, or contradictory entry mappings fail before save;
- horse name, jockey name, row order, cross-race horse number, cross-provider number,
  and prediction selections are never identity sources.

### Temporal and Capture

- only exact archived captures are accepted;
- capture ID/digest/URL/observed-at identity is retained through `source`;
- aware observed time is preserved exactly;
- a current live response is never backdated;
- a trusted historical capture retains its attested observation time;
- finalization uses exact provider time or conservative exact observed time;
- parser/persistence failure cannot delete or rewrite the capture.

### Result

- complete final result with full entry coverage;
- positive partial/provisional evidence remains archived and performs no insert-only
  result-repository write;
- explicit void/cancelled race;
- explicit unsupported state;
- scratch/exclusion maps to entry `VOID`;
- DQ/DNF/non-finish maps to entry `UNSUPPORTED` until a richer domain is approved;
- dead heat preserves duplicate finish positions;
- missing finish and contradictory status fail closed;
- malformed/ambiguous page fails closed;
- unknown official state is never inferred as complete, void, or loss.

### Payout Family

- all four supported bet types;
- four unsupported provider bet types are rejected/not silently coerced;
- exact selection identity and payout-per-100;
- multiple winners/dead heat;
- selection refund and all-refund rules;
- complete and known incomplete publications;
- malformed/missing/unknown rows fail closed;
- correction creates a later immutable publication;
- incomplete latest does not fall back to older complete.

### Persistence

- exact domain round trip;
- equal result write succeeds and differing result conflicts;
- payout publication ordering by observation time and ID;
- capture saved before domain persistence;
- no direct database access outside existing repositories;
- no repair, overwrite, or transaction widening.

### End to End

- approved trusted official capture;
- provider-specific parse and exact crosswalk normalization;
- existing repository persistence;
- c4g2a bounded read at/after exact observation;
- c4g2b summary without mocked settlement facts;
- before-observation cutoff remains unsettled;
- final-ROI label only after application completeness check.

### Static Scope

- no prediction dependency, c4g0/c4g1/c4g2a/c4g2b change, bet generation, allocation,
  latest-plan fallback, name identity, backdated response, current-time substitution,
  broad silent fallback, schema change, or migration;
- no legacy `JRAFetcher`, legacy `NARProvider`, ad-hoc logs, or unstable `hash(url)`
  evidence;
- no c4g2c audit persistence.

## Frozen Scope

This PREPARE changes only:

- `docs/CURRENT_PHASE.md`
- `docs/LATEST_CODEX_REPORT.md`

No production, tests, fixtures, schema, migration, capture, or live request changes are
made. C4f1, c4g0, c4g1, c4g2a, c4g2b, the persisted bet source and executor,
`Simulator`, repositories, capture archives, and provider-neutral models remain
unchanged.

```text
EXACT_NEXT_PHASE_ID:
4C-2d3b1i6d1d5f1c4h0

EXACT_NEXT_PHASE_NAME:
JRA_OFFICIAL_TARGET_RACE_RESULT_NORMALIZATION_AND_PERSISTENCE

NEXT_IMPLEMENTATION_PHASE:
4C-2d3b1i6d1d5f1c4h0_AFTER_TRUSTED_EVIDENCE_CONTRACT_APPROVAL

IMPLEMENTATION_READY:
NO

BLOCKERS:
APPROVED_TRUSTED_JRA_TARGET_RESULT_EVIDENCE_CONTRACT_MISSING
```

Stop for independent review. Do not implement c4h0, c4h1, NAR acquisition,
c4g2c, or an application runner.
