# Current Phase

Status: `READY_FOR_REVIEW`

## Identity and scope

- Phase: `4C-2d3b1i6d1d5f1c4h3`
- Name: `NAR official target-race payout normalization and persistence`
- Exact formal base: `e2bc465d71044b7ca91c80f17fac1ee7895a80fe`
- Formal branch: `feature/ver0.8-simulator`
- Review branch: `review/4c-2d3b1i6d1d5f1c4h3-nar-target-payout`
- Approved PREPARE commit: `a3a9bf2362c997ac284b1723c3efc03e93060b76`
- Approved evidence commit: `033be021f26749f0fe2cdf80894ad2365884276c`
- Approved evidence tree: `3375dbf3285a5f4131c95d88265502e63ecf7313`
- Git setting: `core.autocrlf=true`; no Git configuration or attributes changed.

Allowed and changed files are exactly:

```text
scripts/simulation/nar_target_race_payout_persistence.py
tests/test_nar_target_race_payout_persistence.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

No existing production module, package-root export, repository protocol, SQLite
repository, schema, migration, database, or c4h0/c4h1/c4h2 behavior changed. C4h4 is
unstarted.

## Approved evidence and supported envelope

`SUPPORTED_ENVELOPE`: `NORMAL_FINAL_WINNING_ONLY`

`SUPPORTED_BET_TYPES`:

```text
単勝
馬連
ワイド
3連複
```

Every persisted entry is `PayoutStatus.WINNING`. Refund, void, dead heat, no winner,
`特払い`, correction, unknown, malformed, and ambiguous representations fail closed.
No exceptional-state normalization was introduced.

The target-race grammar remains tied to immutable capture
`nar-capture-v1:d6692261a54c1038a5ffd804ae79edda9ca543cb5d78f37c41ffaeefe281013b`
with response SHA-256
`3b909b6c9509713150199c3bb3821051181671e10c906f5c315aa4a4c4dbf2db`.
Generic NAR documentation evidence commit
`033be021f26749f0fe2cdf80894ad2365884276c` freezes the official statement that
ordinary displayed payout amounts are returns for a 100-yen purchase. Therefore an
exact validated displayed integer yen amount becomes `PayoutRecord.payout_per_100`.
Documentation supplies denomination semantics only and is never read at runtime.

## Public boundary

Module:

```text
scripts/simulation/nar_target_race_payout_persistence.py
```

Module-local surface, with no package-root export:

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

`NARTargetRacePayoutPersistenceError(ValueError)` is the module-local base.
Validation covers malformed or contradictory evidence/identity/crosswalk data;
Unavailable covers an absent exact capture or absent positive complete-final evidence;
Unsupported covers positively recognized representations outside the normal-winning
envelope. Archive and repository exceptions propagate unchanged. There is no broad
exception catch.

All public arguments are validated before archive I/O. `capture_id` and `snapshot`
require exact types; the bet type must belong to formal `BET_TYPES`; archive and
repository objects must be non-type objects with their required callable method.

## Capture, identity, and finality

`CAPTURE_LOAD_COUNT`: `EXACTLY_ONE_BY_EXACT_ID`

The function calls only
`capture_archive.load_capture(capture_id=capture_id)`. It requires exact
`NAROfficialResponseCapture`, the requested ID, and `RACE_MARK_TABLE` page kind, then
strictly decodes exact response bytes as UTF-8. There is no latest/URL/fallback lookup,
retry, HTTP, documentation access, capture creation/write, current clock, or random
input.

The canonical RaceMarkTable URL derives the exact
`nar:YYYYMMDD:<babaCode>:<raceNo>` identity. Snapshot organization `NAR`, source
system `nar_official`, source race ID, target date, visible date/place, active course,
and whole-value race number must agree before payout normalization.

The same capture must also satisfy c4h2's frozen positive result-finality evidence:
one populated `winHorseTable`, exact `優勝馬情報` heading and winner structure, and
exactly one complete approved result-finalization statement. The c4h2 persistence
function is not called, and c4h3 neither constructs nor writes a race result.

## Exhaustive payout grammar

The parser requires exactly one:

```text
article.raceResult > div.innerWrapper > section.newRefundTable
```

Its direct children must be exactly `h4` and `div.twoRefundTable`; the heading has one
direct `span.smallTitle` with normalized whole value `払戻金`. The wrapper has exactly
two direct attribute-free tables, each with one direct `tbody` and only direct `tr`
rows.

Every table row belongs to exactly one explicit group. A start row has direct cells
`td.title[rowspan]`, the table's selection cell, `td.refundMoney`, and `td.c`.
Continuation rows have exactly selection, refund, and popularity cells. `rowspan` is a
canonical positive ASCII decimal and defines the exhaustive group boundary. Missing,
extra, overlapping, out-of-range, duplicate, unknown, or unclassified rows/groups fail
closed.

First-table labels are exactly `単勝`, `複勝`, `枠連複`, and `馬連複`, using direct
selection `td.a`. Second-table labels are exactly `馬連単`, `ワイド`, `三連複`, and
`三連単`, using direct selection `td.d`. Formal mappings are only:

```text
単勝   <- 単勝
馬連   <- 馬連複
ワイド <- ワイド
3連複  <- 三連複
```

The four unsupported sibling groups are structurally classified but never normalized
or allowed to leak selections/amounts into a supported publication.

One formal type is requested per call. Exact initial normal group sizes are
`単勝=1`, `馬連=1`, `ワイド=3`, and `3連複=1`; any other size fails closed without
inferring an exceptional state.

Selections are whole direct text using positive canonical ASCII horse numbers and
exact ASCII `-`, with arity 1/2/2/3. Whitespace, signs, leading zeroes, decimals,
full-width digits, empty or duplicate tokens, wrong separators/classes, and extra text
are rejected. Amounts are whole direct `td.refundMoney` text matching exactly:

```text
[1-9][0-9]{0,2}(?:,[0-9]{3})*円
```

The complete amount is validated before removing commas/suffix and converting to a
positive integer. Selection and amount always come from the same direct row;
popularity `td.c` is neither identity nor payout value.

## Race-local crosswalk, publication, and save

Each horse number resolves only through:

```text
exact NAR race identity + horse number
-> exact nar:...:entry:<horseNum>
-> exact snapshot external_entry_id
-> exact internal race_entry_id
```

Snapshot external and internal identities must be coherent and unique. Horse/jockey
name, lineage, row position, display order, global horse number, prediction selection,
and cross-provider numeric coincidence are forbidden. After each number resolves,
formal `normalize_selection` owns unordered pair/triple canonicalization. Duplicate
canonical payout selections fail before save.

After all capture, identity, finality, table, group, requested-row, selection, amount,
crosswalk, and duplicate checks pass, exactly one `PayoutPublication` is built with:

```text
race_id = snapshot.internal_race_id
bet_type = exact requested formal type
observed_at = capture.observed_at
finalized_at = capture.observed_at
is_complete = True
source = capture.capture_id
source_url = capture.canonical_source_url
entries = every exhaustive requested normal-winning row
```

`PAYOUT_SAVE_COUNT`: `EXACTLY_ONE_AFTER_COMPLETE_VALIDATION`

The function calls `payout_repository.save_payout_publication(publication)` once and
returns that method's exact result, preserving repository-assigned publication ID and
object identity. No incomplete or partial publication, retry, compensation, second
save, direct database transaction, settlement arithmetic, prediction, or bet mutation
occurs.

## Verification and stop condition

- Dedicated:
  `16 passed, 87 subtests passed`
- Related exact files:
  `tests/test_nar_official_response_capture.py`,
  `tests/test_sqlite_nar_official_response_capture_repository.py`,
  `tests/test_nar_target_race_result_persistence.py`,
  `tests/test_historical_input_snapshots.py`,
  `tests/test_simulation_repositories.py`,
  `tests/test_jra_target_race_payout_persistence.py`,
  `tests/test_historical_persisted_race_settlement_source.py`, and
  `tests/test_historical_settlement_simulation.py`
- Related result: `144 passed, 256 subtests passed`
- Full suite: `3017 passed, 2264 subtests passed`
- Static ownership/scope check: `PASS`
- Git diff check: `PASS`
- Live HTTP/documentation HTTP/target recapture during implementation: `NO`

Stop for independent implementation review. Do not integrate formally and do not
start c4h4.
