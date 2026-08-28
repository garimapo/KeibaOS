# Current Phase

Status: `DRAFT_FOR_REVIEW`

## Identity and scope

- Phase: `4C-2d3b1i6d1d5f1c4h3`
- Name: `NAR official target-race payout normalization and persistence PREPARE`
- Exact formal base: `e2bc465d71044b7ca91c80f17fac1ee7895a80fe`
- Formal branch: `feature/ver0.8-simulator`
- Review branch: `review/4c-2d3b1i6d1d5f1c4h3-nar-target-payout-prepare`
- C4h2 formal commit: `e2bc465d71044b7ca91c80f17fac1ee7895a80fe`
- Git setting: `core.autocrlf=true`; no Git configuration or attributes are changed.

This is design and existing-evidence inspection only. It changes only this document
and `docs/LATEST_CODEX_REPORT.md`. It performs no production or Python-test change,
live HTTP, new capture, archive write, database write, repository/SQLite/schema/
migration change, package export, or c4h4 work.

`C4H3_PURPOSE`:
normalize and persist one supported NAR target-race payout publication from one exact
archived `RaceMarkTable` capture after independent evidence approval. C4h3 does not
own result parsing/acquisition, prediction, bet generation/allocation, settlement
cutoff or arithmetic, summary computation, or c4h4 application composition.

## Existing capture reload and sufficiency

`EXISTING_CAPTURE_RELOAD_STATUS`: `PASS_EXACT_VALUE_AND_RAW_BYTES`

The existing isolated archive was opened read-only and the exact capture was loaded
once by exact capture ID through `SQLiteNAROfficialResponseCaptureRepository`:

- `SOURCE_CAPTURE_ID`:
  `nar-capture-v1:d6692261a54c1038a5ffd804ae79edda9ca543cb5d78f37c41ffaeefe281013b`
- `SOURCE_CAPTURE_URL`:
  `https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceMarkTable?k_babaCode=31&k_raceDate=2026%2F05%2F03&k_raceNo=1`
- `SOURCE_CAPTURE_SHA256`:
  `3b909b6c9509713150199c3bb3821051181671e10c906f5c315aa4a4c4dbf2db`
- `SOURCE_CAPTURE_LENGTH`: `96614` bytes
- `SOURCE_CAPTURE_CHARSET`: `utf-8`
- `SOURCE_CAPTURE_REQUESTED_AT`: `2026-08-27T15:41:30.631495+00:00`
- `SOURCE_CAPTURE_OBSERVED_AT`: `2026-08-27T15:41:31.026438+00:00`
- `SOURCE_CAPTURE_STORED_AT`: `2026-08-27T15:41:31.026443+00:00`
- `SOURCE_CAPTURE_PAGE_KIND`: `NAROfficialPageKind.RACE_MARK_TABLE`
- `SOURCE_CAPTURE_HTTP_STATUS`: `200`
- `SOURCE_CAPTURE_CONTENT_TYPE`: `text/html; charset=UTF-8`

Capture ID, canonical URL, digest, raw length, raw bytes, timestamps, page kind, and
charset match the approved c4h2a record. No latest/URL/fallback lookup occurred. The
archive was not modified and no replacement capture was created.

`NAR_TARGET_PAYOUT_EXISTING_EVIDENCE_STATUS`:
`EXISTING_TRUSTED_CAPTURE_SUFFICIENT_CANDIDATE`

The capture positively proves the normal-winning DOM grammar for all four formal bet
types. It does not, however, prove that ordinary displayed winning amounts are the
return for a 100-yen ticket.

`NAR_TARGET_PAYOUT_IMPLEMENTATION_EVIDENCE_STATUS`:
`INSUFFICIENT_REQUIRES_SEPARATE_TRUSTED_EVIDENCE_PHASE`

The only current implementation blocker is official NAR evidence for the denomination
of an ordinary winning payout. No parser implementation is authorized until that
semantic is independently established.

## Payout container and finality candidate

`PAYOUT_CONTAINER_POLICY`:

```text
article.raceResult > div.innerWrapper > section.newRefundTable
```

Require exactly one direct payout section. Its direct element children in the capture
are exactly:

```text
h4
div.twoRefundTable
```

The `h4` contains one direct `span.smallTitle` whose normalized whole value is exactly
`払戻金`. `div.twoRefundTable` has exactly two direct `table` elements; each has one
direct `tbody` and an exhaustively classified direct `tr` sequence. Comments and item
order are evidence, never payout identity.

`PAYOUT_COMPLETENESS_POLICY`:
the same exact capture must prove canonical and visible race identity, one exact payout
container and heading, the evidence-frozen two-table/group boundary, exactly one
requested supported-type group, every row belonging to that group, every selection/
amount association, exact race-local crosswalk resolution, unique canonical
selections, no malformed or unclassified applicable structure, and the existing c4h2
positive result-finality predicate. Only then may one requested-type publication be
`is_complete=True`. No incomplete publication is written in the initial phase.

The complete official payout table plus the same-response finalized-result evidence
is a sufficient structural finality candidate. It does not assert that later official
corrections are impossible; a later capture may create a later immutable publication
through the existing repository model.

## Exact supported-type group evidence

`SUPPORTED_BET_TYPES`: exact formal `BET_TYPES` only:

```text
単勝
馬連
ワイド
3連複
```

Provider labels are exact whole values and map only as follows:

| Formal type | Exact NAR label | Table | Selection cell | Evidence rows |
| --- | --- | --- | --- | --- |
| `単勝` | `単勝` | first | direct `td.a` | `8 -> 720円` |
| `馬連` | `馬連複` | first | direct `td.a` | `8-10 -> 730円` |
| `ワイド` | `ワイド` | second | direct `td.d` | `8-10 -> 300円`; `8-11 -> 410円`; `10-11 -> 350円` |
| `3連複` | `三連複` | second | direct `td.d` | `8-10-11 -> 1,230円` |

`BET_TYPE_ITEM_POLICY`:
parse both direct tables as exact row groups. A group begins with direct
`td.title[rowspan]`; its normalized whole label and canonical positive `rowspan` define
the exact number of direct rows in that group. Continuation rows have no title cell.
The requested formal type must match exactly one provider label above and the exact
normal evidence count: `単勝=1`, `馬連=1`, `ワイド=3`, `3連複=1`. Smaller or larger
groups fail closed rather than inferring dead heat or another state.

Unsupported displayed groups are structurally disjoint siblings:
`複勝`, `枠連複`, `馬連単`, and `三連単`. They may be skipped only after their exact
group boundaries are classified; their selections or amounts must never become a
supported record. No formal bet type is widened or coerced.

`SELECTION_GRAMMAR_POLICY`:
each requested group row has exactly one direct selection cell (`td.a` in the first
table or `td.d` in the second). Its complete normalized value is canonical positive
ASCII decimal horse-number tokens separated only by exact ASCII `-`, without spaces,
signs, leading zeroes, full-width digits, duplicates, missing tokens, or extra tokens.
Arity is exactly one for `単勝`, two unordered tokens for `馬連`/`ワイド`, and three
unordered tokens for `3連複`.

Evidence values are `8`, `8-10`, the three independent Wide selections `8-10`,
`8-11`, `10-11`, and `8-10-11`. Each row is a separate winning combination; the
three Wide rows must become three distinct records and never be collapsed.

`AMOUNT_GRAMMAR_POLICY`:
the same direct row contains exactly one direct `td.refundMoney` whose complete
normalized value matches:

```text
[1-9][0-9]{0,2}(?:,[0-9]{3})*円
```

Validate the entire value before removing commas and the exact `円` suffix. Zero,
signs, decimals, malformed comma grouping, wrong/missing unit, nested or duplicate
amount structure, and selection/amount values from different rows fail closed. The
direct popularity `td.c` is not identity or payout value.

`SNAPSHOT_CROSSWALK_POLICY`:

```text
exact accepted nar:YYYYMMDD:<babaCode>:<raceNo>
+ exact official horse number
-> nar:...:entry:<horseNum>
-> exact snapshot external_entry_id
-> exact internal race_entry_id
```

Horse name, jockey, lineage ID, display order, global horse-number lookup, prediction
selection, and cross-provider numeric coincidence are forbidden. Existing formal
selection normalization owns canonical sorting and arity after every number resolves.

## Payout-per-100 blocker

`PAYOUT_PER_100_EVIDENCE_STATUS`:
`INSUFFICIENT_REQUIRES_OFFICIAL_DOCUMENTATION_EVIDENCE`

The payout table displays ordinary amounts with `円`, but does not state their ticket
denomination. Elsewhere in the same response an official notice says that when a bet
type has no winner, all purchasers receive `70円` or `80円` **per `100円`**, and that
displayed `70円`/`80円` values indicate `特払い`. This establishes the denomination
of special payouts only. It does not establish that the ordinary winning amounts
listed above are amounts returned for a 100-yen ticket.

No already-approved official NAR documentation statement establishing the normal
winning denomination exists in the formal repository/docs. JRA documentation cannot
be transferred to NAR. Provider-neutral field names and simulator stake rules are
domain contracts, not provider evidence. Therefore the page amounts must not yet be
persisted as `payout_per_100`.

## Narrow status envelope

- `NORMAL_WINNING_POLICY`: `STRUCTURE_PROVEN_BUT_PAYOUT_PER_100_SEMANTIC_BLOCKED`
- `REFUND_POLICY`: `FAIL_CLOSED_NOT_EVIDENCED`
- `VOID_POLICY`: `FAIL_CLOSED_NOT_EVIDENCED`
- `DEAD_HEAT_POLICY`: `FAIL_CLOSED_NOT_EVIDENCED`
- `NO_WINNER_POLICY`: `FAIL_CLOSED_NOT_EVIDENCED`
- `CORRECTION_POLICY`: `FAIL_CLOSED_NOT_EVIDENCED`
- `UNKNOWN_POLICY`: `FAIL_CLOSED_ZERO_PAYOUT_WRITES`

The notice mentioning `特払い` does not prove its table-row grammar and authorizes no
special-payout mapping. Exact normal row counts and structure prevent an unapproved
alternative from being silently treated as ordinary winning evidence.

## Proposed public boundary after evidence approval

Proposed module:

```text
scripts/simulation/nar_target_race_payout_persistence.py
```

Proposed module-local surface, with no package-root export:

```python
__all__ = (
    "NARTargetRacePayoutPersistenceError",
    "NARTargetRacePayoutPersistenceValidationError",
    "NARTargetRacePayoutPersistenceUnavailableError",
    "NARTargetRacePayoutPersistenceUnsupportedError",
    "normalize_and_persist_nar_target_race_payout",
)

def normalize_and_persist_nar_target_race_payout(
    *,
    capture_id: str,
    capture_archive: NAROfficialResponseCaptureArchive,
    snapshot: HistoricalInputSnapshot,
    bet_type: str,
    payout_repository: PayoutRepository,
) -> PayoutPublication:
    ...
```

`PUBLIC_ERROR_SURFACE`:
a module-local `NARTargetRacePayoutPersistenceError(ValueError)` base with Validation,
Unavailable, and Unsupported specializations. Malformed/contradictory structure or
identity is Validation; absent exact capture or positive complete evidence is
Unavailable; a recognized representation outside normal-winning support is
Unsupported. Archive and repository exceptions propagate unchanged. No broad catch.

`CAPTURE_LOAD_POLICY`:
exactly one `capture_archive.load_capture(capture_id=capture_id)`. Require exact
`NAROfficialResponseCapture`, matching capture ID, and exact `RACE_MARK_TABLE` page
kind. No latest/URL/fallback lookup, retry, HTTP, capture creation, or capture write.

`RACE_IDENTITY_POLICY`:
reuse c4h2 unchanged: canonical RaceMarkTable URL date/babaCode/raceNo must form the
exact snapshot NAR source identity and agree with visible date/place/race identity.

`OBSERVED_AT_POLICY`: exact `capture.observed_at`.

`FINALIZED_AT_POLICY`: exact `capture.observed_at` only after the same capture proves
the complete normal publication; this is conservative first-observed complete
evidence, not a backdated provider publication claim.

`SOURCE_POLICY`:
`source=capture.capture_id` and `source_url=capture.canonical_source_url`; both fields
exist in the formal `PayoutPublication` domain.

`PAYOUT_SAVE_POLICY`:
one supported requested bet type per call; validate all applicable rows, selections,
amounts, crosswalks, duplicates, completeness, and the constructed publication before
one `payout_repository.save_payout_publication(publication)`. Return that repository
method's exact `PayoutPublication` result. No incomplete publication, second save,
retry, compensation, or direct database transaction.

`PARTIAL_SUCCESS_POLICY`: `FORBIDDEN_WITHIN_ONE_CALL`.

`REPOSITORY_EXCEPTION_POLICY`: propagate unchanged.

## Repository and implementation scope decisions

- `PAYOUT_REPOSITORY_PROTOCOL_CHANGE_REQUIRED`: `NO`
- `SQLITE_PAYOUT_REPOSITORY_CHANGE_REQUIRED`: `NO`
- `SCHEMA_CHANGE_REQUIRED`: `NO`
- `MIGRATION_REQUIRED`: `NO`
- `EXISTING_PRODUCTION_CHANGE_EXPECTED`:
  `NEW_C4H3_MODULE_ONLY_AFTER_EVIDENCE_APPROVAL`

The current repository already returns the persisted publication, supports immutable
later publications, equal-write idempotence, conflict rejection, complete/incomplete
selection, source URL, and bounded settlement reads. No existing c4h0/c4h1/c4h2,
historical parser, capture, repository, SQLite, or settlement module needs change.

## Required next evidence phase

`IMPLEMENTATION_BLOCKERS`:

```text
The trusted RaceMarkTable capture proves the complete normal payout grammar, but no
approved official NAR evidence proves that an ordinary displayed winning amount is the
return for a 100-yen ticket and may therefore populate payout_per_100.
```

`RECOMMENDED_NEXT_PHASE`:
`4C-2d3b1i6d1d5f1c4h3a_NAR_OFFICIAL_NORMAL_PAYOUT_DENOMINATION_DOCUMENTATION_EVIDENCE`

This smallest evidence-only phase should acquire or locate one exact official NAR
rules/help statement for ordinary winning payout denomination, recording official URL,
retrieval/observation time, exact relevant statement, and response provenance. It
must not fetch or replace the race capture, backdate the documentation observation, or
use third-party/JRA/common-knowledge evidence. If no statement is found, c4h3 remains
blocked.

`NEXT_PHASE_ALLOWED_FILES`:

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

No raw fixture or production/test change is required unless independently authorized
after evidence review. C4h4 remains unstarted.
