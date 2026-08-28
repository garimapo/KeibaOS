# Current Phase

Status: `DRAFT_FOR_REVIEW`

## Identity and scope

- Phase: `4C-2d3b1i6d1d5f1c4h3a`
- Name: `NAR official normal-payout denomination documentation evidence`
- Exact formal base: `e2bc465d71044b7ca91c80f17fac1ee7895a80fe`
- Formal branch: `feature/ver0.8-simulator`
- Review branch:
  `review/4c-2d3b1i6d1d5f1c4h3a-nar-payout-denomination-evidence`
- Approved c4h3 PREPARE commit:
  `a3a9bf2362c997ac284b1723c3efc03e93060b76`
- Git setting: `core.autocrlf=true`; no Git configuration or attributes changed.

This is documentation evidence only. It changes this document and
`docs/LATEST_CODEX_REPORT.md`. It makes no production, Python-test, fixture,
repository, SQLite, schema, migration, package-export, database, target-race capture,
or c4h4 change.

## Preserved current documentation evidence

The exact authorized NAR documentation response is preserved outside the repository:

- `LOCAL_EVIDENCE_DIRECTORY`:
  `C:\Users\garim\Desktop\KeibaAI-c4h3a-documentation-evidence`
- `LOCAL_RESPONSE_FILE`:
  `C:\Users\garim\Desktop\KeibaAI-c4h3a-documentation-evidence\response.bin`
- `LOCAL_METADATA_FILE`:
  `C:\Users\garim\Desktop\KeibaAI-c4h3a-documentation-evidence\metadata.json`
- `LOCAL_RESPONSE_IMMUTABILITY_CHECK`: `PASS`

The response bytes were written before charset inspection, decoding, HTML parsing, or
semantic verification. SHA-256 computed by rereading `response.bin` exactly matched
the digest of the in-memory HTTP body. All later analysis read `response.bin`; no
second request, browser text, cache, or copied text was used.

Exact observation provenance:

- `DOCUMENTATION_URL`:
  `https://www.keiba.go.jp/beginner/step6.html`
- `DOCUMENTATION_REQUESTED_AT`: `2026-08-28T04:13:27.115899+00:00`
- `DOCUMENTATION_OBSERVED_AT`: `2026-08-28T04:13:27.189489+00:00`
- `DOCUMENTATION_FINAL_URL`:
  `https://www.keiba.go.jp/beginner/step6.html`
- `DOCUMENTATION_REDIRECT_COUNT`: `0`
- `DOCUMENTATION_HTTP_STATUS`: `200`
- `DOCUMENTATION_CONTENT_TYPE`: `text/html`
- `DOCUMENTATION_CONTENT_ENCODING`: `ABSENT`
- `DOCUMENTATION_RESPONSE_LENGTH`: `12771` bytes
- `DOCUMENTATION_RESPONSE_SHA256`:
  `f5270936608bc77df5942af7bdc0f70ccc0838ee710fa789b22080c751ff15f2`
- `BOM_STATUS`: `NONE`

The requested URL, final URL, status, media type, no-redirect boundary, raw length,
and digest all passed. No target-race HTTP request or capture was made.

## Charset and document identity

`DOCUMENTATION_CHARSET`: `utf-8`

`DOCUMENTATION_CHARSET_SOURCE`: `HTML_META_DECLARATION`

The HTTP `Content-Type` had no charset and the raw body had no BOM. A byte-only scan
of raw `meta` tags extracted only the ASCII charset token and found exactly:

```html
<meta charset="UTF-8">
```

No whole tag or unrelated attribute value was ASCII-decoded. The declaration
normalized unambiguously to UTF-8, and the complete saved body then decoded with
strict UTF-8 and no replacement behavior.

`DOCUMENTATION_TITLE`:
`結果を確認する｜Let'地方競馬｜地方競馬情報サイト`

The decoded document contains the visible `結果を確認する` identity and an `h3`
inside `article#content1` whose whole text is
`１．レース結果・払戻金が知りたい！`. The required statement is a descendant
paragraph of that same article. This excludes an unrelated page, generic home page,
error template, or arbitrary occurrence elsewhere.

## Ordinary payout denomination evidence

The saved response contains exactly once, within the ordinary result/payout section,
the exact official statement:

```text
払戻金は購入金額１００円に対する配当金額を表示します。
```

`NAR_NORMAL_PAYOUT_DENOMINATION_POLICY`:
`DISPLAYED_PAYOUT_IS_RETURN_FOR_100_YEN_PURCHASE`

`PAYOUT_PER_100_MAPPING`:

```text
ordinary validated displayed integer yen payout
-> PayoutRecord.payout_per_100
```

Thus `720円`, `730円`, and `1,230円` map semantically to `720`, `730`, and
`1230` respectively after the separately frozen amount grammar validates them.
These examples explain denomination only; they do not establish a race selection,
amount, result, finality, observation time, or historical availability.

The separate target-race capture remains the sole owner of race identity, winning
selection, actual payout amount, target observation time, structural finality, and
source provenance. The generic documentation observation supplies only the ordinary
100-yen denomination semantic. The target capture's distinct `特払い` notice does not
authorize special-payout parsing.

## Combined evidence decision

`NAR_TARGET_PAYOUT_IMPLEMENTATION_EVIDENCE_STATUS`:
`SUFFICIENT_FOR_NARROW_IMPLEMENTATION`

`SUPPORTED_ENVELOPE`: `NORMAL_FINAL_WINNING_ONLY`

`SUPPORTED_BET_TYPES`:

```text
単勝
馬連
ワイド
3連複
```

`NORMAL_WINNING_POLICY`:
`SUPPORTED_BY_TARGET_CAPTURE_PLUS_OFFICIAL_100_YEN_DOCUMENTATION`

- `REFUND_POLICY`: `FAIL_CLOSED_NOT_EVIDENCED`
- `VOID_POLICY`: `FAIL_CLOSED_NOT_EVIDENCED`
- `DEAD_HEAT_POLICY`: `FAIL_CLOSED_NOT_EVIDENCED`
- `NO_WINNER_POLICY`: `FAIL_CLOSED_NOT_EVIDENCED`
- `CORRECTION_POLICY`: `FAIL_CLOSED_NOT_EVIDENCED`
- `SPECIAL_PAYOUT_POLICY`: `FAIL_CLOSED_NOT_EVIDENCED`
- `UNKNOWN_POLICY`: `FAIL_CLOSED_ZERO_PAYOUT_WRITES`

Rare, special, alternative-count, malformed, or ambiguous representations remain
unsupported. No status or payout semantics are inferred beyond the evidence-backed
ordinary normal-winning form.

## Frozen c4h3 implementation boundary after approval

Proposed module:

```text
scripts/simulation/nar_target_race_payout_persistence.py
```

Module-local public surface only, with no package-root export:

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
Unavailable, and Unsupported specializations. Malformed or contradictory identity or
structure is Validation; missing exact capture or positive complete evidence is
Unavailable; positively recognized but unevidenced representations are Unsupported.
Archive and repository exceptions propagate unchanged; no broad catch is allowed.

`CAPTURE_LOAD_POLICY`:
exactly one archive load by exact capture ID. Require exact capture type, matching ID,
and exact RaceMarkTable page kind. No latest, URL, fallback, retry, HTTP,
documentation lookup, recapture, or capture write exists in implementation.

`RACE_IDENTITY_POLICY`:
reuse c4h2's exact canonical NAR RaceMarkTable URL identity and visible date/place/
race agreement without changing c4h2.

`SNAPSHOT_CROSSWALK_POLICY`:

```text
exact nar:YYYYMMDD:<babaCode>:<raceNo>
+ exact official horse number
-> exact race-local external entry ID
-> exact snapshot external entry ID
-> exact internal race_entry_id
```

Horse name, jockey, lineage ID, row order, global horse number, prediction selection,
and cross-provider numeric coincidence are forbidden.

One formal supported type is requested per call. The exact initial normal row counts
are `単勝=1`, `馬連=1`, `ワイド=3`, and `3連複=1`. Every requested-type row,
selection, amount, association, crosswalk, duplicate boundary, and completeness check
must succeed before publication construction. Alternate counts fail closed without
being classified as dead heat or another exceptional state.

Each accepted record uses `PayoutStatus.WINNING`; its exact validated displayed yen
integer becomes `payout_per_100` under the documentation semantic above. Construct
exactly one complete publication with:

```text
race_id = snapshot.internal_race_id
bet_type = exact requested formal bet type
observed_at = capture.observed_at
finalized_at = capture.observed_at
is_complete = True
source = capture.capture_id
source_url = capture.canonical_source_url
```

After all validation, call
`payout_repository.save_payout_publication(publication)` exactly once and return its
exact result. There is no incomplete publication, partial row persistence, retry,
compensation, second save, direct database ownership, current clock, or settlement
calculation.

## Repository and next-phase decisions

- `PAYOUT_REPOSITORY_PROTOCOL_CHANGE_REQUIRED`: `NO`
- `SQLITE_PAYOUT_REPOSITORY_CHANGE_REQUIRED`: `NO`
- `SCHEMA_CHANGE_REQUIRED`: `NO`
- `MIGRATION_REQUIRED`: `NO`
- `EXISTING_PRODUCTION_CHANGE_EXPECTED`:
  `NEW_C4H3_MODULE_ONLY_AFTER_INDEPENDENT_EVIDENCE_APPROVAL`
- `IMPLEMENTATION_BLOCKERS`:
  `NONE_FOR_NARROW_NORMAL_FINAL_WINNING_ONLY`
- `RECOMMENDED_NEXT_PHASE`:
  `4C-2d3b1i6d1d5f1c4h3_NAR_TARGET_RACE_PAYOUT_IMPLEMENTATION_AFTER_INDEPENDENT_EVIDENCE_REVIEW`

`NEXT_PHASE_ALLOWED_FILES`:

```text
scripts/simulation/nar_target_race_payout_persistence.py
tests/test_nar_target_race_payout_persistence.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

No implementation is authorized by this evidence document. C4h4 remains unstarted.
