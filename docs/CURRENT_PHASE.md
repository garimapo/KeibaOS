# Current Phase

Status: `READY_FOR_REVIEW`

## Identity and scope

- Phase: `4C-2d3b1i6d1d5f1c4h1`
- Subphase: trusted evidence acquisition and payout grammar freeze only
- Exact formal base: `2834fc9eca4571c0044b9491bd25149fa9473e18`
- Approved PREPARE commit: `04ee126d039f16bd745e2b41106a2dd44b8300e9`
- Review branch: `review/4c-2d3b1i6d1d5f1c4h1-jra-target-payout-evidence`

This is evidence work only. It authorizes no production, Python test, repository,
SQLite, schema, migration, package-export, settlement, prediction, or c4h2 change.

## Sufficiency decision

`JRA_TARGET_PAYOUT_IMPLEMENTATION_EVIDENCE_STATUS`:
`SUFFICIENT_FOR_NARROW_IMPLEMENTATION`

The exact approved capture demonstrates structurally disjoint normal-final winning
payout items for every current formal type: `単勝`, `馬連`, `ワイド`, and `3連複`.
It also demonstrates three separate normal-winning `ワイド` combinations, with each
selection and amount paired under one exact row.

Refund, void, dead heat, empty/no-winner, correction, special payout, and every other
exceptional representation are not proven. They remain unsupported and fail closed.
Evidence sufficiency is limited to the normal-winning grammar frozen below.

## Exact source capture

- `SOURCE_CAPTURE_ID`:
  `jra-capture-v1:2d8fbee2df4a201923a49a48e02de3f6837293e0166a1347e30ef3f0b0aad296`
- `SOURCE_CAPTURE_URL`:
  `https://www.jra.go.jp/JRADB/accessS.html?CNAME=pw01sde0106202504030420250913%2FDC`
- `SOURCE_CAPTURE_SHA256`:
  `f5daa967f05ae1ee0cfcbe8d4c0e59aa8a6b3ceef126ce9d8689fe10ffa8ed0e`
- `SOURCE_CAPTURE_LENGTH`: `94570` bytes
- `SOURCE_CAPTURE_REQUESTED_AT`: `2026-08-26T11:38:27.557867+00:00`
- `SOURCE_CAPTURE_OBSERVED_AT`: `2026-08-26T11:38:28.113891+00:00`
- `SOURCE_CAPTURE_STORED_AT`: `2026-08-26T11:38:28.113897+00:00`
- `SOURCE_CAPTURE_PAGE_KIND`: `JRAOfficialPageKind.RACE_RESULT`
- `SOURCE_CAPTURE_CHARSET`: exact `cp932`
- `SOURCE_CAPTURE_HTTP_STATUS`: exact integer `200`
- `SOURCE_CAPTURE_CONTENT_TYPE`: `text/html`

The capture was loaded once by exact ID through
`SQLiteJRAOfficialResponseCaptureRepository.load_capture` over a read-only SQLite URI.
The archive SHA-256 was
`2F26F22DD1A21268690B7122B753CFD1A035A176BD544CBC52FEBD7D3B94DB73`
before and after loading. Capture ID, URL, response digest, length, timestamps, page
kind, charset, status, content type, and raw bytes matched the approved record. No
replacement or fresh race capture was used.

## Payout container

`PAYOUT_AREA_SELECTOR`: `#race_result .refund_area`

- Exactly one match: `div.refund_area.mt30`.
- Direct children in evidence order: `div.block_header`,
  `div.refund_unit.mt15`, `div.caution.narrow.mt15`.
- Heading path: `:scope > .block_header > .content > h2`.
- Exact normalized heading: `払戻金`.

`PAYOUT_UNIT_SELECTOR`: `#race_result .refund_area > .refund_unit`

- Exactly one match: `div.refund_unit.mt15`.
- Direct child groups in evidence order: `div.left`, `div.center`, `div.right`.
- Every group has a direct `ul`; bet-type items are direct `li` children.

Position and item order are evidence only, never identity.

## Common normal-winning grammar

```text
li.<type-class>
└── dl
    ├── dt                         exact normalized bet-type label
    └── dd
        └── div.line               one direct child per winning combination
            ├── div.num            selection
            ├── div.yen            direct amount text + direct span.unit
            └── div.pop            popularity only; never identity
```

The requested item is identified by both its evidenced structural class and exact
normalized `dt` whole value. Class alone is not semantics. Every direct
`dd > div.line` in that item is applicable and must be parsed. Unknown, extra,
missing, duplicate, mixed, or unclassified applicable structure fails closed.

- `SELECTION_SELECTOR`: requested item
  `> dl > dd > div.line > div.num`, exactly one per line.
- `AMOUNT_SELECTOR`: same line `> div.yen`, exactly one per line.
- `SELECTION_AMOUNT_ASSOCIATION`: `SAME_EXACT_DIRECT_DIV_LINE_PARENT`.
- `SELECTION_TOKEN_GRAMMAR`: existing c4h0/formal JRA canonical positive ASCII
  decimal horse number; evidenced tokens are `3`, `6`, and `7`. Signs, leading
  zeroes, whitespace, non-ASCII digits, empty, and nondecimal tokens are not normal.
- `SELECTION_SEPARATOR_GRAMMAR`: exact ASCII `-`, no whitespace. `単勝` has none.
  Formal arity is one for `単勝`, two for `馬連` and `ワイド`, three for `3連複`.
- `AMOUNT_GRAMMAR`: direct text
  `[1-9][0-9]{0,2}(?:,[0-9]{3})*` plus exactly one direct `span.unit` with whole
  value `円`. Commas are removed only after full validation. Zero, sign, decimal,
  malformed grouping, missing/different unit, duplicate text, and unpaired values fail.

## Exact supported-type evidence

### 単勝

- `BET_TYPE_LABEL_EXACT`: `単勝`
- `BET_TYPE_ITEM_SELECTOR`:
  `#race_result .refund_area > .refund_unit > .left > ul > li.win`
- Label: `:scope > dl > dt`; rows: `:scope > dl > dd > div.line`
- `SELECTION_EXAMPLE_EXACT`: `7`
- `SELECTION_TOKEN_GRAMMAR`: one canonical decimal token
- `SELECTION_SEPARATOR_GRAMMAR`: none
- `AMOUNT_EXAMPLE_EXACT`: direct `160`, direct unit `円`
- `AMOUNT_GRAMMAR`: common positive yen grammar
- `SELECTION_AMOUNT_ASSOCIATION`: same exact direct `div.line`
- `WINNING_COMBINATION_COUNT_IN_EVIDENCE`: `1`
- `ITEM_COMPLETENESS_EVIDENCE`: exactly one fully classified direct line.

### 馬連

- `BET_TYPE_LABEL_EXACT`: `馬連`
- `BET_TYPE_ITEM_SELECTOR`:
  `#race_result .refund_area > .refund_unit > .right > ul > li.umaren`
- Label: `:scope > dl > dt`; rows: `:scope > dl > dd > div.line`
- `SELECTION_EXAMPLE_EXACT`: `3-7`
- `SELECTION_TOKEN_GRAMMAR`: two canonical decimal tokens
- `SELECTION_SEPARATOR_GRAMMAR`: one exact ASCII hyphen
- `AMOUNT_EXAMPLE_EXACT`: direct `1,030`, direct unit `円`
- `AMOUNT_GRAMMAR`: common positive yen grammar
- `SELECTION_AMOUNT_ASSOCIATION`: same exact direct `div.line`
- `WINNING_COMBINATION_COUNT_IN_EVIDENCE`: `1`
- `ITEM_COMPLETENESS_EVIDENCE`: exactly one fully classified direct line.

### ワイド

- `BET_TYPE_LABEL_EXACT`: `ワイド`
- `BET_TYPE_ITEM_SELECTOR`:
  `#race_result .refund_area > .refund_unit > .center > ul > li.wide`
- Label: `:scope > dl > dt`; rows: `:scope > dl > dd > div.line`
- `SELECTION_EXAMPLE_EXACT`: `3-7`, `6-7`, `3-6`
- `SELECTION_TOKEN_GRAMMAR`: two canonical decimal tokens per line
- `SELECTION_SEPARATOR_GRAMMAR`: one exact ASCII hyphen per line
- `AMOUNT_EXAMPLE_EXACT`: respectively `420 円`, `300 円`, `1,370 円`
- `AMOUNT_GRAMMAR`: common positive yen grammar
- `SELECTION_AMOUNT_ASSOCIATION`: each pair shares its exact direct `div.line`
- `WINNING_COMBINATION_COUNT_IN_EVIDENCE`: `3`
- `ITEM_COMPLETENESS_EVIDENCE`: exactly three fully classified direct line
  siblings; none may be collapsed, omitted, or inferred from adjacency.

### 3連複

- `BET_TYPE_LABEL_EXACT`: `3連複`
- `BET_TYPE_ITEM_SELECTOR`:
  `#race_result .refund_area > .refund_unit > .right > ul > li.trio`
- Label: `:scope > dl > dt`; rows: `:scope > dl > dd > div.line`
- `SELECTION_EXAMPLE_EXACT`: `3-6-7`
- `SELECTION_TOKEN_GRAMMAR`: three canonical decimal tokens
- `SELECTION_SEPARATOR_GRAMMAR`: two exact ASCII hyphens
- `AMOUNT_EXAMPLE_EXACT`: direct `2,280`, direct unit `円`
- `AMOUNT_GRAMMAR`: common positive yen grammar
- `SELECTION_AMOUNT_ASSOCIATION`: same exact direct `div.line`
- `WINNING_COMBINATION_COUNT_IN_EVIDENCE`: `1`
- `ITEM_COMPLETENESS_EVIDENCE`: exactly one fully classified direct line.

## Unsupported displayed items

Evidence order:

```text
left:   単勝 (li.win), 複勝 (li.place)
center: 枠連 (li.wakuren), ワイド (li.wide)
right:  馬連 (li.umaren), 馬単 (li.umatan),
        3連複 (li.trio), 3連単 (li.tierce)
```

`UNSUPPORTED_DISPLAYED_ITEM_BOUNDARY_POLICY`:
`STRUCTURALLY_DISJOINT_SIBLING_LI_ITEMS_MAY_BE_IGNORED_ONLY_AFTER_EXACT_REQUESTED_ITEM_AND_LABEL_VALIDATION`

Each unsupported type has a separate sibling `li`, class, `dl > dt` label, and
`dl > dd` rows. No line is shared with a supported type. A requested type is complete
only after exactly one class-and-label matched item is found and all its direct lines
are classified. Order is not identity. Duplicate requested labels/classes, cross-item
lines, mixed labels, or unknown requested-item children fail closed.

## Payout-per-100 evidence

The race capture contains no `100円` text and is not used alone to infer denomination.

`PAYOUT_PER_100_EVIDENCE`:

- Official URL: `https://www.jra.go.jp/keiba/rules/kakutei.html`
- Title: `レースの確定：競馬のルール`
- Retrieval/observation: `2026-08-27T03:19:17.5934489Z`
- Exact statement:
  `払戻は100円の馬券を購入した場合に払戻される金額で表示されます。`
- Frozen meaning: an official displayed payout is the amount returned for a 100-yen
  ticket and maps to `payout_per_100` after race-page amount validation.

This current official documentation observation establishes denomination semantics
only. It supplies or changes no historical race fact, is not backdated, and does not
alter the capture observation time.

## Narrow support envelope

- `NORMAL_WINNING_GRAMMAR_STATUS`:
  `SUPPORTED_BY_EXACT_CAPTURE_FOR_ALL_FOUR_FORMAL_TYPES`
- `MULTIPLE_WINNER_GRAMMAR_STATUS`:
  `SUPPORTED_FOR_NORMAL_DIRECT_LINE_SIBLINGS_AS_EVIDENCED_BY_THREE_WIDE_COMBINATIONS`
- `REFUND_GRAMMAR_STATUS`: `FAIL_CLOSED_NOT_EVIDENCED`
- `VOID_GRAMMAR_STATUS`: `FAIL_CLOSED_NOT_EVIDENCED`
- `DEAD_HEAT_GRAMMAR_STATUS`: `FAIL_CLOSED_NOT_EVIDENCED`
- `EMPTY_WINNER_GRAMMAR_STATUS`: `FAIL_CLOSED_NOT_EVIDENCED`
- `CORRECTION_GRAMMAR_STATUS`: `FAIL_CLOSED_NOT_EVIDENCED`
- `UNKNOWN_REPRESENTATION_POLICY`:
  `FAIL_CLOSED_ZERO_PAYOUT_PUBLICATION_WRITES`

The initial parser may accept only the exact normal-winning structure. Any alternative
must raise the frozen module-local unsupported, unavailable, or validation error before
save. It must not reinterpret an exception as normal win, loss, empty, refund, or void.

## Identity and temporal freeze

The capture remains the formally approved c4h0 target race. C4h1 reuses canonical
accessS identity and visible date, venue, meeting number, meeting day, and whole-value
race-number agreement without redefining or modifying c4h0.

```text
exact capture JRA race identity
+ official horse-number token
-> build_jra_external_entry_id(...)
-> exact HistoricalInputSnapshot external entry identity
-> exact internal race_entry_id
```

Horse/jockey name, display or row order, global horse-number lookup, prediction
selection, and cross-provider numeric coincidence are forbidden.

Future `observed_at` is exact `capture.observed_at`. For this positively terminal
normal capture, absent a provider finalization timestamp, `finalized_at` is also exact
`capture.observed_at` as the conservative first time this capture proves finality.
Neither timestamp is backdated.

## Fixture decision

- `DERIVED_FIXTURE_POLICY`: `NO_FIXTURE`
- `RAW_CAPTURE_COMMITTED`: `NO`
- `DERIVED_FIXTURE_COMMITTED`: `NO`
- `AUDIT_LINK`: the original raw bytes remain in the isolated archive under the exact
  ID, URL, digest, observed time, and length above. This document records selectors,
  node relationships, values, and extraction results. No official bytes were copied,
  transcoded, reserialized, reconstructed, or hand-edited into Git.

## Preserved future API

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

- One requested supported type per call.
- One exact archive load; no latest, fallback, or live race-page lookup.
- Complete identity, crosswalk, finality, row, selection, amount, denomination,
  completeness, and domain validation before write.
- Exactly one `save_payout_publication` on success.
- No incomplete publication or partial success.
- Repository exceptions propagate unchanged.
- No package-root export.
- No protocol, SQLite, schema, migration, c4h0, c4g2a, or c4g2b change.

## Readiness and next phase

`IMPLEMENTATION_BLOCKERS`:
`NONE_FOR_THE_FROZEN_NORMAL_FINAL_WINNING_ONLY_ENVELOPE`

Rare states remain out of scope, not blockers, because only the frozen normal form may
be recognized. A matching real historical snapshot and persisted plan remain necessary
for later real end-to-end replay but do not block this parser boundary.

`RECOMMENDED_NEXT_PHASE`:
`4C-2d3b1i6d1d5f1c4h1_NARROW_NORMAL_WINNING_IMPLEMENTATION`

Proposed next allowed files:

```text
scripts/simulation/jra_target_race_payout_persistence.py
tests/test_jra_target_race_payout_persistence.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

It must not add rare states, alter existing production/repositories/schema, start
c4h2, perform HTTP, or create a capture.

## Implementation review outcome

The evidence-frozen boundary is implemented in:

```text
scripts/simulation/jra_target_race_payout_persistence.py
```

Its sole public operation is:

```python
normalize_and_persist_jra_target_race_payout(
    *,
    capture_id: str,
    capture_archive: JRAOfficialResponseCaptureArchive,
    snapshot: HistoricalInputSnapshot,
    bet_type: str,
    payout_repository: PayoutRepository,
) -> PayoutPublication
```

The module has exactly the frozen module-local error surface and no package-root export.
It loads one exact archived `RACE_RESULT` capture once, validates exact JRA
capture/snapshot and visible race identity, validates the race-local external-entry
crosswalk, and accepts only the frozen normal-winning payout area, unit layout,
class-and-label matched requested item, direct lines, selections, amounts, and
selection-to-amount pairing.

One call normalizes exactly one formal supported type. It constructs one complete
`PayoutPublication` with exact capture timestamps, source, and URL only after every
requested-item line and canonical internal selection has validated. It then calls
`PayoutRepository.save_payout_publication` exactly once and returns that exact result.
Missing capture or missing normal-winning evidence is unavailable; malformed or
contradictory content is validation failure; recognized exceptional markers are
unsupported. No incomplete publication, fallback, retry, compensation, or partial
requested-type save exists.

The dedicated test suite covers all four normal types, the three distinct Wide records,
public surface, archive and repository behavior, exact source/timestamps, identity and
crosswalk failures, visible header/race-number failures, container/item structure,
selection and amount grammar, duplicate canonical selections, partial Wide failure,
exceptional/empty cases, and static ownership. It uses synthetic HTML only and makes no
claim that a fixture is trusted official evidence.

## Correction review outcome — exact normal-winning grammar

The requested item now accepts only the exact evidence-frozen direct-line counts:
`単勝=1`, `馬連=1`, `ワイド=3`, and `3連複=1`. Any smaller or larger count is a
validation failure before `PayoutRepository.save_payout_publication`; it is not
interpreted as dead heat or any other unsupported provider state.

The requested-type path also rejects unclassified direct content before save: its
`li` must contain only one direct `dl`; that `dl` must contain only direct `dt` then
`dd`; the `dd` must contain only the evidence-frozen direct `div.line` children; and
each line must contain only direct `div.num`, `div.yen`, and `div.pop` children. Any
additional direct element or non-whitespace direct text fails closed. Unsupported
sibling bet-type items remain isolated and are not parsed.

Verification:

```text
dedicated: 13 passed, 61 subtests passed
related:   91 passed, 114 subtests passed
full:      2988 passed, 2111 subtests passed
```

Only the new production module, new dedicated test, and these two documents changed.
No live HTTP, trusted recapture, direct database access, repository protocol, SQLite,
schema, migration, c4h0, c4g2a, c4g2b, or c4h2 change occurred. Formal integration is
not complete; stop for independent implementation review.

## Implementation scope and stop

Changed files:

```text
scripts/simulation/jra_target_race_payout_persistence.py
tests/test_jra_target_race_payout_persistence.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

No fixture was committed. No existing production or test code, race-page live HTTP, new
capture, database write, schema/migration, or c4h2 work occurred. Stop after publishing
this implementation branch for independent review.
