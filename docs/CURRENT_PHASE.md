# Current Phase

Status: `READY_FOR_REVIEW`

## Identity

- Phase: `POST_V0_8_DAILY_REPLAY_38`
- Name: `Controlled NAR Market Odds Source-Profile Fixture Acquisition and Qualification`
- Phase type: `CONTROLLED_ACQUISITION_FIXTURE_QUALIFICATION`
- Base Commit: `b1869296fe0b6a10698d2bac48ff85d22d8719d5`
- Branch: `feature/post-v0.8-daily-replay`
- Result: `SOURCE_PROFILE_FIXTURES_READY`
- Open dependency: `COMBINATION_EV_REQUIRES_MARKET_ODDS_CAPTURE`

## Completed scope

Phase38 used the integrated Phase36 state-neutral one-request boundary to acquire exactly eight official NAR market-odds responses. The complete source-profile matrix is exactly four Phase32 page kinds by OPEN/FINAL, with one fixture per state and page kind. All raw bodies passed public-data safety review, exact-byte publication, Phase32 request/capture reconstruction, manifest identity, source-state qualification, and Git byte-preservation checks.

No production parser, normalized odds type, Decimal conversion, horse-number mapping, expected-selection enumeration, persistence, replay resolver, probability/EV integration, strategy, settlement, scheduler, or JRA support was added.

## Frozen acquisition plan and execution

The single plan was fixed before the first odds request:

```text
OPEN  baba_code=23 race_date=2026-09-11 race_no=3
  ODDS_TAN_FUKU
  ODDS_UM_LEN_FUKU
  ODDS_WIDE
  ODDS_3_LEN_FUKU
FINAL baba_code=21 race_date=2026-09-10 race_no=11
  ODDS_TAN_FUKU
  ODDS_UM_LEN_FUKU
  ODDS_WIDE
  ODDS_3_LEN_FUKU
```

All eight calls used `build_nar_market_odds_request_identity(...)`, `NARMarketOddsRawAcquisitionTarget`, `RequestsNARMarketOddsRawAcquisitionTransport`, and `acquire_nar_market_odds_raw_response(...)`. Each slot used exactly one official HTTPS GET with no retry, no redirect, TLS verification, timeout `(10.0, 20.0)`, strict UTF-8, exact effective URL, absent/identity content encoding, and three actual UTC clock samples. Attempted: 8. Succeeded: 8. Retries: 0. No automatic target substitution occurred.

## Canonical fixture matrix

```text
open/odds_tan_fuku
  SHA-256 ce474a4da61427e915c2ee855b21e3130f2a039c7bd0b5a79080e412052d6966
  bytes 32102
open/odds_um_len_fuku
  SHA-256 81e25a663d821d7c5d7040d531981b26d3c97d27002a0027262e11d4898c979f
  bytes 31992
open/odds_wide
  SHA-256 3013966ede1be81527f4a92d271170503fb0ebabbc7d0a2665f307219f07663a
  bytes 32495
open/odds_3_len_fuku
  SHA-256 1da75c015e2035c26b1d4669b8893ae8541f26d41ca5dd66f0653ca31617edff
  bytes 37086
final/odds_tan_fuku
  SHA-256 266a3d3dad28c562a204173ed9247aea4ce4603a0dadc59edfb2e3baa7512e1f
  bytes 37270
final/odds_um_len_fuku
  SHA-256 1fd4e50edd52bc24b3c9af77c09ef0e10a67187bb5812d345fe6a0858c48c1fe
  bytes 37130
final/odds_wide
  SHA-256 3fad398e62187f3f9ba1647696bb4bccaf70d68157d219205faf38b629a7ca7c
  bytes 38211
final/odds_3_len_fuku
  SHA-256 f0802ff769dbdf70455ce2f05c538674c369a4cc34afaf01b9e63674300618dd
  bytes 50900
```

The exact real capture timestamps and Phase32 capture IDs are stored in the canonical manifest. No timestamp was edited, derived from race time, or backdated.

## Qualification and source grammar

Qualification method: `nar-market-odds-source-state-qualification-v1`.

Each fixture has exactly one full `h4.odd_title` state heading under `article.raceCard > div.innerWrapper > div#odd_content > div.odd_header`. OPEN headings contain the exact page-family title plus an `HH:MM 現在` market-as-of label. FINAL headings contain the exact page-family title plus `最終`. The complete heading token, byte offset, occurrence count, bounded raw context and SHA-256, structural locator, market-container byte range and SHA-256, selection representation, and odds representation are recorded. Classification does not rely on filename, plan expectation, race time, clock, or an isolated token.

The source-profile evidence establishes:

- WIN: `table.odd_popular_table_02`; horse number and scalar WIN odds coexist with a separate PLACE range.
- QUINELLA: `table#formation_renfuku.odd_table` plus ranking tables; pair keys are two horse numbers joined by ASCII hyphen; odds are scalar.
- WIDE: `table#formation_quinella.odd_table` plus ranking tables; pair keys are two horse numbers joined by ASCII hyphen; the range is lower decimal, `<br>`, ASCII hyphen, upper decimal. It is not converted to a scalar.
- TRIO: `table#formation_trio.odd_table` plus ranking tables; triple keys are three horse numbers joined by ASCII hyphens; odds are scalar.

This is fixture source-grammar qualification only. No production selector or quote parser exists.

## Manifest, safety, and reconstruction

Manifest path:

```text
tests/fixtures/nar_market_odds/source_profiles/v1/manifest.json
```

It is exact canonical JSON schema v1, serialized as UTF-8 sorted-key compact JSON with no trailing newline. Its identity is:

```text
nar-market-odds-source-profile-fixture-set-v1:14c2ecdbe85ac1f673c015643eabd7d757d971c85cd60599d7dd6c576926e470
```

The identity digest excludes only its own `fixture_set_identity` field and binds the ordered eight fixture objects, schema version, purpose, raw digests/lengths, request/capture provenance, real timestamps, qualification evidence, structural audit, and safety result.

Public-data safety method: `nar-market-odds-public-data-safety-review-v1`. Result: `approved_exact_public_bytes` for all eight response digests. The review found no session ID, authentication material, CSRF/XSRF token, credential, personalized account identifier, or private data. The pages contain only the known public Google custom-search identifier and public race display controls. `Set-Cookie` and all non-whitelisted response headers are excluded from the manifest. No response bytes were redacted or transformed.

For every entry, the integrity test rebuilds the exact Phase32 request, reads the raw fixture bytes, reconstructs `NARMarketOddsResponseCapture`, and verifies request identity SHA-256, response SHA-256, byte length, canonical/effective URL, actual timestamps, and capture ID. Result: PASS for 8/8.

## Git byte preservation

`.gitattributes` contains only the approved new rule:

```text
tests/fixtures/nar_market_odds/source_profiles/v1/** -text -diff
```

All nine source-profile files report `text: unset` and `diff: unset`. For each HTML fixture, `git hash-object --path=<path>` equals `git hash-object --no-filters <path>`, proving the Git attribute pipeline would preserve the exact raw bytes without staging. Worktree SHA/length checks match the manifest for 8/8. Formal post-commit `git cat-file blob HEAD:<path>` verification remains required during integration because no stage or commit is authorized in Phase38 execution.

The existing portable official-fixture test was changed only to require the two historical `.gitattributes` entries it owns instead of asserting obsolete whole-file equality. Existing raw-byte validations are unchanged.

## Verification

```text
Phase38 fixture-integrity + portable-fixture tests: 8 passed
same dedicated tests with ResourceWarning-as-error: 8 passed
Phase36/Phase32 acquisition, capture, archive, migration: 63 passed, 74 subtests passed
NAR source/fixture + Phase30 + Phase25/27/28 regressions: 158 passed, 132 subtests passed
full unittest discovery: 3231 passed
focused compilation/static boundary audit: passed
Phase32 reconstruction/manifest identity: passed for 8/8
Git attributes/would-be blob preservation: passed for 8/8
```

The full suite emitted only the existing unrelated SQLite `ResourceWarning`s. The dedicated Phase38 suite is clean when warnings are errors.

## Allowed Files

Exactly these 14 paths changed:

```text
.gitattributes
tests/fixtures/nar_market_odds/source_profiles/v1/open/odds_tan_fuku.html
tests/fixtures/nar_market_odds/source_profiles/v1/open/odds_um_len_fuku.html
tests/fixtures/nar_market_odds/source_profiles/v1/open/odds_wide.html
tests/fixtures/nar_market_odds/source_profiles/v1/open/odds_3_len_fuku.html
tests/fixtures/nar_market_odds/source_profiles/v1/final/odds_tan_fuku.html
tests/fixtures/nar_market_odds/source_profiles/v1/final/odds_um_len_fuku.html
tests/fixtures/nar_market_odds/source_profiles/v1/final/odds_wide.html
tests/fixtures/nar_market_odds/source_profiles/v1/final/odds_3_len_fuku.html
tests/fixtures/nar_market_odds/source_profiles/v1/manifest.json
tests/test_nar_market_odds_source_profile_fixtures.py
tests/test_portable_official_replay_fixtures.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

No Phase36 production file, database, log, other fixture, parser, or persistence file changed. Nothing is staged, committed, or pushed.

## Deferred state and stop condition

Phase33 remains `DESIGN_BLOCKED` until Phase38 is reviewed and integrated, after which it must be newly prepared against these exact fixtures. Phase34 is not formally resolved until Phase38 review/integration; after that it is resolved/superseded. `COMBINATION_EV_REQUIRES_MARKET_ODDS_CAPTURE` remains open because fixtures are parser-source-profile artifacts only, not causally valid replay/T-5/EV/decision evidence.

Stop at `READY_FOR_REVIEW`. Do not integrate or prepare Phase39.
