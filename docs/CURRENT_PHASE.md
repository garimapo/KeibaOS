# Current Phase

Status: `DRAFT_FOR_REVIEW`

## Identity

- Phase: `4C-2d3b1i6d1d5f1c4h1`
- Name: JRA official target-race payout normalization and persistence
- Task: PREPARE only; architecture and evidence sufficiency review
- Formal branch: `feature/ver0.8-simulator`
- Exact formal base: `2834fc9eca4571c0044b9491bd25149fa9473e18`
- Review branch: `review/4c-2d3b1i6d1d5f1c4h1-jra-target-payout-prepare`
- Formal prerequisite: c4h0 is complete at the exact formal base and remains frozen.

## Purpose and boundary

`C4H1_PURPOSE`:
`NORMALIZE_ONE_SUPPORTED_JRA_TARGET_RACE_PAYOUT_TYPE_FROM_ONE_EXACT_ARCHIVED_ACCESS_S_CAPTURE_AND_PERSIST_ONE_PROVIDER_NEUTRAL_PUBLICATION`

```text
exact archived JRA accessS capture
+ exact HistoricalInputSnapshot race-local crosswalk
+ one exact supported bet type
-> fail-closed provider-specific payout parsing and normalization
-> one PayoutPublication / PayoutRecord tuple
-> existing PayoutRepository
```

C4h1 does not execute prediction, generate or allocate bets, mutate a snapshot or
persisted bet plan, calculate settlement, choose a settlement cutoff, or produce a
`SimulationSummary`. It owns no live HTTP or direct database work. No result or payout
fact may flow into prediction inputs.

## Evidence decision

`JRA_TARGET_PAYOUT_IMPLEMENTATION_EVIDENCE_STATUS`:
`INSUFFICIENT_REQUIRES_SEPARATE_TRUSTED_EVIDENCE_PHASE`

The approved formal c4h0 evidence proves one exact accessS capture and target-race
identity, exactly one `#race_result .refund_area`, heading `払戻金`, one `.refund_unit`,
eight displayed bet-type items, twelve positive `.yen` values, and a positive payout
publication structure suitable for c4h0's terminal-result predicate.

It does not freeze the runtime grammar needed to construct payout objects. No approved
raw or provenance-bound derived JRA payout fixture in the formal repository proves:

- the exact item/section selector and bet-type label grammar;
- the association between one displayed selection and one displayed amount;
- horse-number token and separator grammar;
- multiple-winning-row grouping and ordering;
- displayed amount semantics as payout per 100 yen;
- empty, refund, void, dead-heat, or correction representations; or
- safe exclusion of unsupported displayed types while proving one requested type
  complete.

The twelve documented amounts cannot establish those relationships. No selector,
status, or row grammar may be inferred from plausible HTML. Production implementation
is not authorized by this PREPARE.

## Formal payout domain

`SUPPORTED_BET_TYPES`:

```text
単勝
馬連
ワイド
3連複
```

These are exactly the existing formal `BET_TYPES`.

`UNSUPPORTED_BET_TYPES_POLICY`:
`複勝`, `枠連`, `馬単`, and `3連単` remain outside the formal domain. They must not be
coerced or partially mapped. They may be ignored only after approved evidence proves
exact disjoint item boundaries and complete coverage for the requested supported type.

Existing `PayoutPublication`, `PayoutRecord`, `PayoutStatus`, `PayoutRepository`,
selection normalization, and SQLite behavior are reused unchanged. A publication is for
one exact supported bet type. Winning selections are canonical internal
`race_entry_id` tuples. A `WINNING` record has a strictly positive integer
`payout_per_100`. Duplicate canonical selection identities are forbidden.

## Proposed post-evidence public surface

Proposed module:

```text
scripts/simulation/jra_target_race_payout_persistence.py
```

`PUBLIC_API`:

```python
def normalize_and_persist_jra_target_race_payout(
    *,
    capture_id: str,
    capture_archive: JRAOfficialResponseCaptureArchive,
    snapshot: HistoricalInputSnapshot,
    bet_type: str,
    payout_repository: PayoutRepository,
) -> PayoutPublication:
    ...
```

Module-local `__all__`:

```python
(
    "JRATargetRacePayoutPersistenceError",
    "JRATargetRacePayoutPersistenceValidationError",
    "JRATargetRacePayoutPersistenceUnavailableError",
    "JRATargetRacePayoutPersistenceUnsupportedError",
    "normalize_and_persist_jra_target_race_payout",
)
```

No package-root export.

`PUBLIC_ERROR_SURFACE`:

- `JRATargetRacePayoutPersistenceError(ValueError)` is the module-local base.
- `JRATargetRacePayoutPersistenceValidationError` covers contradictory or malformed
  capture, snapshot, crosswalk, selection, amount, or collaborator return data.
- `JRATargetRacePayoutPersistenceUnavailableError` covers absence of the exact capture
  or positively proven complete/final payout evidence.
- `JRATargetRacePayoutPersistenceUnsupportedError` covers a positively recognized but
  not evidence-approved official representation.
- Archive and repository exceptions propagate unchanged. No broad translation, retry,
  or fallback is permitted.

Exact messages and the provider-state classification matrix must be frozen after the
evidence phase. The hierarchy and ownership above are frozen.

## Call and write policy

`PAYOUT_SAVE_POLICY`:
`ONE_REQUESTED_SUPPORTED_BET_TYPE_PER_CALL_ONE_SAVE_AFTER_COMPLETE_VALIDATION`

One call parses every applicable row for one exact requested supported type from one
exact capture, constructs one complete `PayoutPublication`, invokes
`save_payout_publication` exactly once, and returns the exact repository result. This
matches the existing one-bet-type publication boundary and introduces no batch
transaction. A caller may invoke it separately for other types.

`PARTIAL_SUCCESS_POLICY`:
`NONE_WITHIN_ONE_PUBLIC_CALL`. If any applicable row fails validation, zero rows and
zero publications are saved. Cross-call atomicity is not owned by c4h1.

All capture, page, race, visible header, snapshot, crosswalk, finality, item, row,
selection, amount, completeness, and publication validation finishes before the sole
save.

## Capture and provenance

`CAPTURE_LOAD_POLICY`:
`EXACTLY_ONE_ARCHIVE_LOAD_BY_EXACT_CAPTURE_ID`

`CAPTURE_ID_POLICY`:
The caller supplies one nonempty exact capture ID. The archive must structurally provide
callable `load_capture`, called only as
`load_capture(capture_id=exact_capture_id)` exactly once. No latest, fallback, URL
lookup, capture creation, or live acquisition is permitted.

The loaded value must be an exact `JRAOfficialResponseCapture`, with the requested
`capture_id` and `JRAOfficialPageKind.RACE_RESULT`.

`SOURCE_POLICY`:
The publication `source` is the exact capture ID.

`SOURCE_URL_POLICY`:
The publication `source_url` is the capture's exact canonical source URL. No caller URL
or reconstructed alternative is accepted. Response bytes use the already-formal strict
JRA charset contract with no lossy replacement or guessed charset.

## Race identity and crosswalk

`RACE_IDENTITY_POLICY`:
The formal result-URL identity parser must resolve the exact canonical accessS URL and
agree with the exact JRA external race identity in the exact
`HistoricalInputSnapshot`. Date-only or numeric-coincidence identity is forbidden.

`VISIBLE_RACE_IDENTITY_POLICY`:
Visible date, venue, meeting number, meeting day, and whole-value race number must agree
with the accessS identity and snapshot under the frozen formal c4h0 concepts. C4h1 does
not mutate c4h0 or widen accepted representations.

`SNAPSHOT_CROSSWALK_POLICY`:

```text
exact accessS race identity
+ exact official horse number
-> build_jra_external_entry_id(...)
-> exact snapshot external_entry_identity.external_entry_id
-> exact snapshot race_entry_id
```

The mapping must be coherent, race-local, and unique in both directions. Missing,
duplicate, wrong-race, or contradictory mappings fail closed. Horse or jockey name,
display position, row order, global horse-number lookup, prediction selection, and
cross-provider numeric coincidence are never identity sources.

## Provider grammar policy pending evidence

`PAYOUT_SECTION_POLICY`:
Exactly one payout area with approved normalized heading and one payout unit must exist.
That proves only the container/finality boundary today; child item and row grammar still
requires approved evidence.

`BET_TYPE_SECTION_POLICY`:
The requested supported label must identify exactly one whole item under evidence-frozen
grammar. Missing, duplicate, ambiguous, nested, mixed, or substring-only labels fail
closed. Current evidence cannot safely name selectors or ignore unsupported items.

`SELECTION_GRAMMAR_POLICY`:
Every selection token, separator, row boundary, and multi-row grouping must be grounded
in approved evidence for that bet type. Official horse numbers resolve only through the
exact race-local crosswalk. Existing domain code owns arity and canonicalization. No
name, order, or inferred grouping fallback. Exact JRA grammar is blocked.

`PAYOUT_AMOUNT_POLICY`:
Only an evidence-frozen whole-value yen grammar may yield a base-10 integer. A winning
amount must be positive. Missing, zero, negative, fractional, duplicate, malformed,
overflowing, ambiguously grouped, or unpaired values fail closed. Selectors and format
remain blocked.

`PAYOUT_PER_100_POLICY`:
A displayed amount may populate `payout_per_100` only when approved evidence proves it
is explicitly a payout for a 100-yen stake. Documented `.yen` values alone do not prove
that interpretation.

`MULTIPLE_WINNER_POLICY`:
Every applicable official winning combination becomes one record. Evidence must prove
selection/amount grouping. Multiple combinations are not collapsed, and duplicate
canonical selections fail. No multiple-winner grammar is approved yet.

`REFUND_POLICY`: `FAIL_CLOSED_NOT_YET_EVIDENCE_FROZEN`

`VOID_POLICY`: `FAIL_CLOSED_NOT_YET_EVIDENCE_FROZEN`

`DEAD_HEAT_POLICY`: `FAIL_CLOSED_NOT_YET_EVIDENCE_FROZEN`

`EMPTY_WINNER_POLICY`: `FAIL_CLOSED_NOT_YET_EVIDENCE_FROZEN`

No status is inferred from zero, absence, empty layout, or adjacent text. Absence never
means complete loss, empty payout, or a complete publication.

`UNKNOWN_ROW_POLICY`:
Any unclassified applicable item or row causes zero saves. Unknown content is never
skipped to obtain completeness.

## Finality, time, and completeness

`FINALITY_POLICY`:
The same exact capture must positively prove a terminal official payout publication and
the complete requested-type grammar. Past race date, HTTP success, payout heading, or
positive yen text alone cannot prove that requested type complete. The c4h0 finality
predicate is necessary context but insufficient for payout normalization.

`OBSERVED_AT_POLICY`:
Exact aware `capture.observed_at`; never race date, scheduled start, displayed date, or
an inferred publication time.

`FINALIZED_AT_POLICY`:
When the same approved capture provides no provider-attested finalization timestamp, a
positively proven complete/final requested-type publication uses exact
`capture.observed_at` as the conservative first time this capture proves finality. This
does not claim provider finalization at that instant. A provider timestamp is usable
only under a separately approved parsing rule.

`PUBLICATION_COMPLETENESS_POLICY`:
`is_complete=True` requires the same exact capture to prove:

1. exact capture ID, page kind, canonical URL, and target-race identity;
2. exact visible race identity and coherent snapshot crosswalk;
3. positive terminal/final official payout evidence;
4. exactly one unambiguous requested supported-type item;
5. every applicable row classified and parsed under approved grammar;
6. every selection resolved through the race-local crosswalk;
7. every amount paired and validated under approved per-100 semantics;
8. no malformed, unknown, duplicate, contradictory, or unclassified applicable row;
9. no duplicate canonical selection; and
10. a `finalized_at` permitted by the frozen temporal rule.

Missing evidence never means loss, empty payout, complete payout, or `NO_BET`.

`INCOMPLETE_PUBLICATION_POLICY`:
`NO_INCOMPLETE_WRITE_IN_INITIAL_C4H1`. The domain can represent an incomplete
publication, but approved evidence does not define a safely recognizable partial JRA
payout state. Ambiguous, absent, nonterminal, or partially parsed evidence causes no
save. C4h1 must not invent `is_complete=False` semantics.

## Repository and correction policy

`PAYOUT_REPOSITORY_PROTOCOL_CHANGE_REQUIRED`: `NO`

`SQLITE_PAYOUT_REPOSITORY_CHANGE_REQUIRED`: `NO`

`SCHEMA_CHANGE_REQUIRED`: `NO`

`MIGRATION_REQUIRED`: `NO`

The immutable publication model is sufficient. Equal retries and conflicts remain
existing repository behavior. A later capture observation or source may create a new
immutable publication under that contract. C4h1 never overwrites an older publication
or invents correction/version semantics.

`REPOSITORY_EXCEPTION_POLICY`:
Save exceptions propagate unchanged. No retry, rollback, compensation, conflict
reinterpretation, or conversion to incomplete data.

## Existing-core freeze and future implementation

C4h0 result persistence remains unchanged. C4h1 may reproduce only narrowly necessary
private validation concepts in its own module after evidence approval. No broad shared
parser extraction is justified now.

`EXISTING_PRODUCTION_CHANGE_EXPECTED`:
After evidence approval, exactly one new production module is expected. Existing JRA
capture/identity/result modules, snapshot domain, payout domain and repositories,
SQLite, c4g2a, c4g2b, schema, migrations, and package root remain unchanged.

Provisional implementation files, not yet authorized:

```text
scripts/simulation/jra_target_race_payout_persistence.py
tests/test_jra_target_race_payout_persistence.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

Future tests must pin the exact public API; exact capture load once; no fallback or live
lookup; full pre-save identity/finality/grammar validation; exact race-local crosswalk;
all evidence-approved label/selection/amount/per-100/multiple-row cases; failure of all
unknown, missing, malformed, duplicate, or ambiguous content before save; one exact
complete save and return; repository exception propagation; immutable correction
behavior; c4g2a bounded selection/c4g2b integration; and static absence of prediction,
settlement arithmetic, HTTP, direct database, clock, random, name identity, broad
exception catches, and writes outside `PayoutRepository`.

## End-to-end status and next phase

`REAL_END_TO_END_READY_AFTER_C4H1`:
`NO_NOT_BY_C4H1_ALONE`. A real replay also needs the exact historical snapshot and plan,
approved result/payout evidence with honest observation times, and application-owned
settlement cutoffs. C4h1 does not choose cutoffs or certify final ROI.

`IMPLEMENTATION_BLOCKERS`:
No approved provenance-bound evidence freezes exact JRA item/row/selection/amount,
per-100, and completeness grammar for the four supported bet types. Multiple winners,
empty/refund/void/dead-heat representations also remain unproven.

`RECOMMENDED_NEXT_PHASE`:
`4C-2d3b1i6d1d5f1c4h1_TRUSTED_EVIDENCE_ACQUISITION_AND_PAYOUT_GRAMMAR_FREEZE_ONLY`

This is evidence work within c4h1, not c4h2. It must use the existing formal live
capture path and isolated archive, preserve raw bytes and honest times, and freeze only
positively demonstrated representations. At minimum it must provide reviewable
provenance-bound normal-winning structure for all four supported types: item labels,
selection/amount association, multiple rows where present, and explicit per-100
meaning. Unevidenced rare states remain fail closed.

`NEXT_PHASE_ALLOWED_FILES`:

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
new immutable evidence fixture and matching metadata manifest files only under tests/fixtures/jra/
```

No Python, database, repository, schema, or migration change is allowed in the evidence
stage. A fixture is optional and requires an explicit raw-versus-derived decision and an
audit link to the isolated original capture.

## This PREPARE scope and stop condition

Allowed files:

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

Every other path is forbidden. Required verification is exact formal remote head,
exactly these two changed docs, `git diff --check`, one review commit ahead and zero
behind the formal base, clean final status, and unchanged formal remote. No pytest,
live HTTP, trusted capture, or database write is authorized.

Stop after pushing the PREPARE review branch for independent architecture/evidence
review. Do not implement c4h1 and do not start c4h2.
