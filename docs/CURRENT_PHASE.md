# Current Phase

## Status

READY_FOR_REVIEW

## Phase

Phase 4C-2d3b1i6c1d1 — NAR target horse identity preparation

## Base Commit

960c3419e52205cbfd94c3466eaabbb85d14e6ba feat: assemble historical input snapshots

## Branch and Workspace

Formal branch: feature/ver0.8-simulator

Preparation review branch: review/4c-2d3b1i6c1d1-prepare

Canonical workspace: C:\Users\garim\Desktop\KeibaAI-review-1i5b2b

The original workspace, C:\Users\garim\Desktop\KeibaAI, is read-only for this phase.

## Objective and Scope

d1 designs the smallest c1b extension that preserves a verified provider-native target-horse identity from the same
supplied official DebaTable row that already supplies horse number, jockey, and win odds. It changes no historical
past-race behavior and does not fetch HorseMarkInfo. The only future output evolution is entry
external_horse_id from None to a validated official identity.

This is PREPARE only. It changes documentation only and creates a docs-only review commit. Production, tests, fixtures,
providers, parsers, database, schema, migration, README, CLI, package exports, and the original workspace are
read-only.

## Read-only Investigation Findings

The committed c1b entry parser currently returns only horse_no, external_entry_id, jockey, and odds; entry records
deliberately contain external_horse_id=None. Its inline dedicated fixture has a horseName anchor without href, so it
cannot prove the new identity contract. This is Outcome C: the current fixture is incomplete/sanitized for d1 proof.

Official supplied-page inspection of the NAR DebaTable for 2026-07-04 Funabashi race 11 proved that the horse anchor
is in the same visible target entry row as horse number, jockey, and odds. Two observed anchors resolve to:

    /KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=30036406666
    /KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=30038401876

The second response resolves to the official horse page. The first was a supplied-link observation whose target returned
404 during later retrieval; d1 treats link syntax and row-local evidence as the contract, not successful HTTP retrieval.
The previously inspected current and historical RaceMarkTable rows use the same HorseMarkInfo path and lineage-code
form. No target horse name is required or used as identity.

Observed lineage values are ASCII positive canonical decimal tokens: digits only, no sign, no whitespace, no leading
zero, and no non-ASCII digit. They are provider identifiers, not arithmetic values, so future c1b preserves their
validated lexical text and never converts untrusted arbitrary-length text with int().

## Exact Future Horse-anchor Contract

Within each selected supported entry-table row, future c1b must require exactly one row-local:

    a.horseName[href]

The anchor must be part of that same tr as the already selected horseNum, jockeyName, and odds weight nodes. c1b must
not locate horse links globally by display name, and must not combine cells across rows.

The href may be a relative path or an absolute URL. After NFC validation it must canonicalize only to:

    https://www.keiba.go.jp/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=<token>

The anchor URL rules are exact:

| Component | Required rule |
| --- | --- |
| scheme / host | Relative is accepted then anchored to https://www.keiba.go.jp. Absolute form must be exact https and www.keiba.go.jp. |
| port | None or explicit default 443 only; any other port fails. |
| path | Exact /KeibaWeb/DataRoom/HorseMarkInfo; no trailing slash or alternate path. |
| query keys | Exactly one k_lineageLoginCode; unknown, duplicate, blank, and missing keys fail. |
| fragments / credentials / control text | Forbidden. |
| percent encoding | Malformed escapes fail. The decoded lineage token must still meet the exact ASCII lexical grammar; encoding may not conceal a changed token. |
| Unicode | href and decoded token are NFC-normalized for validation; non-ASCII digits remain rejected. |
| canonical spelling | Output always uses the one canonical absolute URL form above, with the lexical token unchanged. |

The token grammar is ASCII [1-9][0-9]* as text. It rejects sign, decimal point, scientific notation, whitespace,
Unicode digits, empty text, and leading zeros. No numeric conversion or numeric range is performed.

## Exact Output and Compatibility

The future entry record remains:

    external_entry_id = nar:{YYYYMMDD}:{k_babaCode}:{k_raceNo}:entry:{horseNum}
    external_horse_id = nar:horse:{k_lineageLoginCode}
    horse_no = existing positive horse number

This namespaced external_horse_id is deterministic, stable, unambiguous, directly reconstructable from the official
anchor, and distinct from a local database ID or target-race entry ID. external_entry_id and external_horse_id coexist;
neither replaces the other. No horse name, horse number, target entry ID, URL hash, source ID, or local ID is used.

No c1a change is required. HistoricalInputSourceRecord already accepts optional external_horse_id text. Changing None to
the proven namespaced value intentionally changes the entry record content and hence its deterministic c1a source_id;
backward source-id preservation is neither possible nor desired.

No c1c change is required. The committed builder already copies entry external_horse_id into
HistoricalExternalEntryIdentity.external_horse_id. c1d may later compare a historical row's independently verified
provider identity with that target identity, but d1 itself does not parse historical results.

## Error Policy and Determinism

A selected supported row missing horseNum, exactly one valid official horse anchor, jockey, or valid positive win odds
raises NarHistoricalInputSourceValidationError. These are malformed/ambiguous supplied DebaTable bytes at the existing
c1b validation boundary, not recognized page kinds outside support. Cancellation behavior remains c1b's existing
fail-closed validation behavior. No row may fall back to external_horse_id=None after d1.

Same supplied bytes, response URL, and observed_at must yield equal records and source IDs. A different validated lineage
token changes only the corresponding entry record source_id because only that entry payload changes; track, jockey, and
odds record payloads and source IDs remain unchanged. HTML outside a selected target row must not affect another row.

## Fixture Decision

A new authentic immutable official fixture is required for the future positive test because the current inline fixture
contains a horseName anchor with no href. The implementation phase must add exactly one fixture:

    tests/fixtures/nar/deba_table_target_horse_identity.html

It must be captured from an official NAR DebaTable response, retain at least two horse rows with their official
HorseMarkInfo anchors and pinned lineage codes, and be used as the positive source-contract proof. It may be minimized
only by removing unrelated document regions without changing the selected official row structure or hrefs. A
hand-invented href fixture alone is forbidden.

## Public API and Future Allowed Files

Public API change: NO. c1b must retain exactly:

    NarSuppliedOfficialResponse
    NarHistoricalInputSourceError
    NarHistoricalInputSourceValidationError
    NarHistoricalInputSourceUnsupportedError
    normalize_nar_historical_input_source_records

All anchor parsing/canonicalization helpers are private. c1b still receives one caller-supplied DebaTable response and
does no HTTP, urllib, filesystem, database, or legacy provider/parser work.

Future Allowed Files are exactly:

    scripts/simulation/nar_historical_input_source.py
    tests/test_nar_historical_input_source.py
    tests/fixtures/nar/deba_table_target_horse_identity.html
    docs/CURRENT_PHASE.md
    docs/LATEST_CODEX_REPORT.md

No historical_input_source_records.py, historical_input_snapshot_builder.py, repository, migration, schema, database,
provider/parser, CLI, package root, or README change is authorized. Any need for another file is REVISION_REQUIRED.

## Future Dedicated Test Plan

The future test module must prove unchanged public API; a valid official target anchor; exact lexical lineage extraction;
exact external_horse_id; intentional entry source_id change; unchanged external_entry_id/jockey/odds behavior; multiple
rows with distinct lineage values; and row-local association between horseNum, anchor, jockey, and odds.

It must reject zero/multiple anchors, wrong HorseMarkInfo path, wrong host, credentials, fragment, unsupported port,
unknown/missing/duplicate lineage query, blank token, malformed percent escape, sign, whitespace, leading zero,
non-ASCII digits, scientific notation, and an absolute nonofficial URL. It must cover relative canonicalization and
official absolute form if the authentic fixture supplies it; it must prove c1a set validation still succeeds, c1c
propagates the new external_horse_id without c1c modification, no package-root export, and no HTTP/DB/filesystem/
current-time dependency. The authentic fixture is mandatory for the positive source-contract case.

## Blockers and Stop Condition

d1 implementation is complete and remains unapproved pending independent code review. The only d1 responsibility is target-row
official horse-identity preservation. It does not solve historical field mapping, race_class, Decimal margins,
passing/fourth-corner variants, provider-record-ID syntax, past-race normalization, pagination, or absence proof.

blocker: d1 must be approved before c1d can bind a historical RaceMarkTable horse identity to a target external entry;
past_race_absence remains UNSUPPORTED.

## Implementation Result

The d1 implementation requires one row-local a.horseName[href] for every supported c1b entry row and canonicalizes
only relative or official absolute HorseMarkInfo URLs to the validated lexical identity
nar:horse:{k_lineageLoginCode}. The lineage token is never converted to int. Entry records now carry that identity;
the existing target external_entry_id, track, jockey, and odds payloads remain unchanged. The committed c1a validator
continues to build source IDs, so entry source IDs intentionally change while non-entry source IDs remain stable.

The positive regression uses the approved official-derived fixture
tests/fixtures/nar/deba_table_target_horse_identity.html with two official rows and pinned lineage values. Dedicated
negative cases cover missing/multiple anchors and strict link/token rejection. A c1c regression uses explicit valid
absence evidence only to prove that external_horse_id propagates unchanged; it does not weaken c1c's normal past-
evidence requirement.

Verification runtime recovery used the external Python 3.14.5 venv at
C:\\Users\\garim\\.cache\\keibaos-verification\\d1-py314 with pytest 8.3.5 and tzdata 2026.3. All required pytest
verification passed: dedicated c1b 11, c1a 8, c1c 12, related historical snapshot/migration/SQLite repository 40,
and full suite 2447. The forbidden dependency/source/AST check and git diff --check also passed. Status remains
READY_FOR_REVIEW pending independent review.

## GitHub Review Correction: Source-ID Isolation

GitHub review of d1 implementation commit `86c26816d894fbee98691c9c8f231dee2129503e` approved production,
the authentic fixture, and horse-identity parsing. No production or fixture change is required. The dedicated suite
now pins deterministic selective c1a source-ID isolation: changing only entry 1's valid
`k_lineageLoginCode` changes only that entry record's `external_horse_id` and `source_id`.

The regression proves that the track record, entry 1's jockey and odds-win records, and every entry/jockey/odds
record for untouched entry 2 retain exactly equal record payloads and source IDs. It also proves the selected
entry's `external_entry_id` remains unchanged and that the sole changed committed record payload value is
`external_horse_id`. It does not reintroduce `external_horse_id=None` output or alter c1a/c1c behavior.

Verification with external Python 3.14.5 / pytest 8.3.5 / tzdata 2026.3 passed: d1 dedicated 12, c1a 8, c1c 12,
historical snapshot/migration/SQLite repository regressions 40, full suite 2448, and the forbidden
dependency/source/AST check. `git diff --check` passed. Status remains READY_FOR_REVIEW pending independent review.
