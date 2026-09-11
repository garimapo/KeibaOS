# Latest Codex Report

## Phase 38 — Controlled NAR Market Odds Source-Profile Fixture Acquisition and Qualification

Status: `READY_FOR_REVIEW`
Result: `SOURCE_PROFILE_FIXTURES_READY`
Base: `b1869296fe0b6a10698d2bac48ff85d22d8719d5`
Branch: `feature/post-v0.8-daily-replay`
Blockers: none

### Acquisition and matrix

One explicit eight-slot plan was frozen before any odds request. OPEN used NAR race identity `baba_code=23`, `race_date=2026-09-11`, `race_no=3`; FINAL used `baba_code=21`, `race_date=2026-09-10`, `race_no=11`. Each race supplied all four Phase32 page kinds.

Phase36 performed exactly eight official HTTPS GET acquisitions: 8 attempted, 8 succeeded, 0 retries, 0 substitutions. All used exact canonical Phase32 requests, actual three-sample UTC timestamps, TLS verification, no redirects, timeout `(10.0, 20.0)`, HTTP 200, exact effective URLs, strict UTF-8, and absent/identity content encoding.

The complete matrix is 8/8: 4 OPEN and 4 FINAL, exactly one of each per page kind. Response SHA-256 and byte length:

```text
open/odds_tan_fuku      ce474a4da61427e915c2ee855b21e3130f2a039c7bd0b5a79080e412052d6966 32102
open/odds_um_len_fuku   81e25a663d821d7c5d7040d531981b26d3c97d27002a0027262e11d4898c979f 31992
open/odds_wide          3013966ede1be81527f4a92d271170503fb0ebabbc7d0a2665f307219f07663a 32495
open/odds_3_len_fuku    1da75c015e2035c26b1d4669b8893ae8541f26d41ca5dd66f0653ca31617edff 37086
final/odds_tan_fuku     266a3d3dad28c562a204173ed9247aea4ce4603a0dadc59edfb2e3baa7512e1f 37270
final/odds_um_len_fuku  1fd4e50edd52bc24b3c9af77c09ef0e10a67187bb5812d345fe6a0858c48c1fe 37130
final/odds_wide         3fad398e62187f3f9ba1647696bb4bccaf70d68157d219205faf38b629a7ca7c 38211
final/odds_3_len_fuku   f0802ff769dbdf70455ce2f05c538674c369a4cc34afaf01b9e63674300618dd 50900
```

### Qualification, safety, and identity

All eight responses qualified with `nar-market-odds-source-state-qualification-v1`. Each uses a unique complete market-heading token under the exact `odd_title` context, bounded byte context/hash, market-container range/hash, and explicit source-grammar description. OPEN uses page-family headings with `HH:MM 現在`; FINAL uses page-family headings with `最終`. WIDE's lower/`<br>`/hyphen/upper range and QUINELLA/TRIO combination forms are explicitly qualified without normalization.

Public-data safety passed for 8/8 under `nar-market-odds-public-data-safety-review-v1`. No session/authentication/CSRF/credential/personalized data was found. No body was redacted or transformed; non-whitelisted headers are absent from the manifest.

Canonical fixture-set identity:

```text
nar-market-odds-source-profile-fixture-set-v1:14c2ecdbe85ac1f673c015643eabd7d757d971c85cd60599d7dd6c576926e470
```

The exact canonical manifest and raw files reconstruct all eight Phase32 requests/captures with exact request SHA, response SHA, length, capture ID, URL, metadata, and actual timestamps.

### Git preservation and tests

The exact path-scoped `.gitattributes` `-text -diff` rule is present. Git reports text and diff unset for all nine source-profile files. Filtered and raw `git hash-object` values match for every fixture without staging. Formal committed-blob verification remains an integration gate.

```text
Phase38 dedicated + portable: 8 passed
Phase38 dedicated ResourceWarning-as-error: 8 passed
Phase36/Phase32: 63 passed, 74 subtests passed
NAR/Phase30/Phase25/27/28 related: 158 passed, 132 subtests passed
full unittest: 3231 passed
compilation/static audit: passed
```

Only pre-existing unrelated SQLite ResourceWarnings appeared in the full suite.

### Boundaries and Git state

Exactly the 14 approved Phase38 paths changed. Phase36 production code, database, logs, and unrelated fixtures are unchanged. Cached state is empty; nothing was staged, committed, or pushed.

No normalized parser, Decimal odds, horse/entry mapping, completeness, persistence, replay resolver, EV, strategy, scheduler, settlement, or JRA work was performed. Phase33 remains `DESIGN_BLOCKED` and Phase34 remains unresolved until Phase38 review/integration. `COMBINATION_EV_REQUIRES_MARKET_ODDS_CAPTURE` remains open.
