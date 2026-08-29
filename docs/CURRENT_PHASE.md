# Current Phase

Status: `DRAFT_FOR_REVIEW`

## Identity and scope

- Phase: `4C-2d3b1i6d1d5f1c4i3a`
- Name: `Portable Official Fixture Evidence and Provenance PREPARE`
- Exact formal base/C4i2 formal commit:
  `7cec11686e7ac02d98782834200debe24bb9d15b`
- Formal branch: `feature/ver0.8-simulator`
- Review branch:
  `review/4c-2d3b1i6d1d5f1c4i3a-portable-official-fixture-evidence-prepare`
- C4i2: `FORMALLY_VERIFIED`

This is evidence-design work only. Allowed changed files are exactly:

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

No production, tests, fixtures, binary/HTML files, SQLite archives, schema,
migration, CLI, HTTP, capture creation/save, formal integration, C4i3b, or AI runtime
work is authorized.

## C4i3a purpose

C4i3a will make the two already-trusted official target-race responses portable after
a clean clone so C4i3b can exercise the real JRA/NAR result and payout normalizers in
one deterministic, no-network historical replay. C4i3a owns fixture bytes, exact
machine-readable provenance, minimal expected facts, and direct fixture
integrity/normalizer tests only. C4i3b retains CLI binding and the complete
mixed-provider replay acceptance test.

## Independently verified source evidence

Both isolated archives were opened read-only. Each capture was exact-loaded through
its formal SQLite capture repository. Repository reconstruction revalidated the formal
capture identity, and SHA-256 was recomputed directly from the loaded bytes. No archive
was mutated.

### JRA source evidence identity

```text
type: JRAOfficialResponseCapture
capture_id: jra-capture-v1:2d8fbee2df4a201923a49a48e02de3f6837293e0166a1347e30ef3f0b0aad296
canonical_source_url: https://www.jra.go.jp/JRADB/accessS.html?CNAME=pw01sde0106202504030420250913%2FDC
page_kind: race_result
source_race_identity: jra:race:2025:06:04:03:04
visible_race_identity: 2025-09-13 / 中山 / 4レース
response_sha256: f5daa967f05ae1ee0cfcbe8d4c0e59aa8a6b3ceef126ce9d8689fe10ffa8ed0e
response_byte_length: 94570
charset: cp932
requested_at: 2026-08-26T11:38:27.557867+00:00
observed_at: 2026-08-26T11:38:28.113891+00:00
stored_at: 2026-08-26T11:38:28.113897+00:00
http_status: 200
content_type: text/html
content_encoding: null
http_date: Wed, 26 Aug 2026 11:38:29 GMT
etag: null
last_modified: null
content_length: null
```

The body contains 963 CRLF sequences plus 893 bare LF sequences and no NUL byte.
Those mixed line endings are source evidence and must not be normalized.

### NAR source evidence identity

```text
type: NAROfficialResponseCapture
capture_id: nar-capture-v1:d6692261a54c1038a5ffd804ae79edda9ca543cb5d78f37c41ffaeefe281013b
canonical_source_url: https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceMarkTable?k_babaCode=31&k_raceDate=2026%2F05%2F03&k_raceNo=1
page_kind: race_mark_table
source_race_identity: nar:20260503:31:1
visible_race_identity: 2026-05-03 / 高知 / race 1
response_sha256: 3b909b6c9509713150199c3bb3821051181671e10c906f5c315aa4a4c4dbf2db
response_byte_length: 96614
charset: utf-8
requested_at: 2026-08-27T15:41:30.631495+00:00
observed_at: 2026-08-27T15:41:31.026438+00:00
stored_at: 2026-08-27T15:41:31.026443+00:00
http_status: 200
content_type: text/html; charset=UTF-8
content_encoding: null
http_date: Thu, 27 Aug 2026 15:41:31 GMT
etag: null
last_modified: null
content_length: null
```

The body contains 1,177 LF sequences, no CRLF sequence, and no NUL byte. Those line
endings are source evidence and must not be normalized.

`SOURCE_EVIDENCE_VERIFICATION=PASS_EXACT_FORMAL_RELOAD_IDENTITY_AND_RAW_BYTES`.

## Fixture derivation, identity, and time policy

`FIXTURE_DERIVATION_POLICY=EXACT_SOURCE_BYTES`.

The future repository fixtures must contain the exact two trusted response bodies.
For each provider, `fixture_sha256 == source_response_sha256` and
`fixture_byte_length == source_response_byte_length`. No DOM serialization, comment
removal, whitespace cleanup, line-ending conversion, transcoding, synthetic field
substitution, or reduced reconstruction is permitted.

`DERIVED_BYTES_POLICY=REJECTED_FOR_THIS_FIXTURE_SET`. A reduced JRA fixture would have
to replace the source's `4レース` identity text with the current parser's synthetic
`4R` grammar, and a reduced NAR fixture would have to remove official HTML comments to
fit the current payout parser. Either choice would hide a real source/parser mismatch
and would not provide equivalent parser coverage. If a later separately reviewed
phase ever authorizes derived bytes, it must assign a new fixture SHA, byte length,
capture identity, deterministic actual derivation timestamp, and explicit derivation
rule/version; source timestamps would remain provenance only.

`BACKDATING_POLICY=ORIGINAL_TIMESTAMPS_RETAINED_ONLY_WITH_EXACT_SOURCE_BYTES`.
Because the selected fixture bytes and all capture identity material are exact, the
original requested/observed/stored times remain exact capture metadata. No timestamp
from these captures may be assigned to changed bytes.

`FIXTURE_CAPTURE_IDENTITY_POLICY=RECONSTRUCT_AND_REQUIRE_EXACT_SOURCE_CAPTURE_ID`.
Future tests must construct the formal provider capture from the raw fixture plus the
provenance metadata and require its derived capture ID, page kind, URL, body digest,
and timestamps to equal the source capture exactly.

## Portable fixture representation

The future exact directory and files are:

```text
tests/fixtures/historical_replay/official/jra/race_result_20250913_nakayama_04.cp932.html
tests/fixtures/historical_replay/official/nar/race_mark_table_20260503_31_01.utf8.html
tests/fixtures/historical_replay/official/provenance.json
tests/fixtures/historical_replay/official/expected_facts.json
```

The HTML files are raw response bytes, not decoded text. JRA remains exact cp932; NAR
remains exact UTF-8. `FIXTURE_LINE_ENDING_POLICY=EXACT_SOURCE_BYTES_NO_NORMALIZATION`.
Because both bodies have no NUL byte and `core.autocrlf=true`, a future C4i3a commit
must add exact-path `-text` entries to `.gitattributes`; this is genuinely required to
make checkout bytes invariant. No broader attribute rule or Git configuration change
is allowed.

`FIXTURE_SHA_POLICY=RAW_CHECKOUT_BYTES_MUST_EQUAL_PROVENANCE_SHA256`.
Tests must digest the checked-out byte files before decoding or constructing a capture.

`PORTABILITY_POLICY=CLEAN_CLONE_REPOSITORY_RELATIVE_NO_EXTERNAL_ARCHIVE`.
Provenance contains no local absolute path, developer name, external SQLite database,
or machine-specific location. C4i3b will construct disposable archive databases from
the checked-out evidence rather than commit a developer archive.

## Exact provenance schema

`provenance.json` is strict UTF-8 JSON with duplicate-key rejection. Its root keys are
exactly `schema_version` and `fixtures`; `schema_version` is exact integer `1`, and
`fixtures` is an exact two-item array ordered JRA then NAR.

Each fixture object has exactly these keys:

```text
provider
fixture_role
source_capture_id
source_canonical_source_url
source_page_kind
source_response_sha256
source_response_byte_length
source_charset
source_requested_at
source_observed_at
source_stored_at
source_http_status
source_content_type
source_content_encoding
source_http_date
source_etag
source_last_modified
source_content_length
source_race_identity
derivation_kind
fixture_relative_path
fixture_sha256
fixture_byte_length
fixture_charset
fixture_capture_identity_policy
supported_normalization_roles
```

`fixture_role` is exactly `historical_replay_official_result_and_payout`,
`derivation_kind` is exactly `exact_source_bytes`,
`fixture_capture_identity_policy` is exactly
`reconstructs_exact_source_capture_identity`, and
`supported_normalization_roles` is exactly
`["target_race_result", "target_race_payout"]`. Nullable HTTP metadata remains an
explicit JSON null. All paths are the exact repository-relative paths above.

## Expected facts schema and source facts

`expected_facts.json` is strict UTF-8 JSON with duplicate-key rejection. Its root keys
are exactly `schema_version` and `fixtures`; version is exact integer `1`, and fixtures
are ordered JRA then NAR. Each fixture object has exactly `provider`,
`fixture_relative_path`, `source_race_identity`, `result_status`, `finish_order`, and
`payouts_by_bet_type`. Each finish item has exactly `horse_number`,
`finish_position`, and `result_status`. Each payout item has exactly `horse_numbers`,
`payout_per_100`, and `payout_status`.

The exact source facts derived offline from the verified bodies are:

- JRA complete finish order:
  `7, 3, 6, 12, 5, 2, 13, 4, 9, 10, 8, 11, 1`.
- JRA payouts: `単勝 7=160`; `馬連 3-7=1030`; `ワイド 3-7=420,
  6-7=300, 3-6=1370`; `3連複 3-6-7=2280`.
- NAR complete finish order:
  `8, 10, 11, 4, 1, 5, 7, 9, 3, 6, 2`.
- NAR payouts: `単勝 8=720`; `馬連 8-10=730`; `ワイド 8-10=300,
  8-11=410, 10-11=350`; `3連複 8-10-11=1230`.

All result entries use `confirmed`; all listed payouts use `winning`. Horse numbers
are race-local provider facts. Future tests must map them through fixture-specific
snapshot identities before comparing formal internal race-entry selections.

## Normalization coverage and blockers

`JRA_NORMALIZATION_COVERAGE=SOURCE_FACTS_PRESENT_BUT_EXACT_PUBLIC_RESULT_AND_PAYOUT_BLOCKED`.
The exact source contains all 13 normal final result rows and all four formal payout
types. The existing formal row/payout extractors recover the facts above, but both
public JRA persistence boundaries reject the exact page before save because the source
race-number `img[alt]` is `4レース` while the frozen regex accepts only `4R`.

`NAR_NORMALIZATION_COVERAGE=RESULT_PASSES_EXACT_SOURCE_PAYOUT_BLOCKED`.
The public NAR result boundary accepts the exact source and returns the 11-entry
complete result above. All four payout groups and amounts are present, but the public
NAR payout boundary rejects the exact source because BeautifulSoup `Comment` nodes
under `div.twoRefundTable` are treated as non-whitespace direct text. Comment-only
offline analysis confirms the payout facts above, but that is not a public normalizer
pass and must not be reported as one.

These are production/evidence compatibility defects, not fixture-creation details.
C4i3a must not rewrite the source to accommodate them. Therefore:

```text
IMPLEMENTATION_BLOCKERS:
1. JRA exact official race-number grammar (`4レース`) is rejected by both formal JRA boundaries.
2. NAR exact official payout comments are rejected as unclassified direct text.
```

No C4i3a fixture implementation is authorized until a separately reviewed narrow
parser-fidelity correction makes the exact source bytes pass without weakening the
fail-closed rules for genuine text/elements.

## Copyright minimization and tests

`COPYRIGHT_DATA_MINIMIZATION_POLICY=TWO_EXACT_REQUIRED_TARGET_RESPONSES_ONLY`.
No archive database, linked asset, script, stylesheet, other race, unrelated page, or
broader site content is included. Full response bodies are selected only because no
truthful reduced representation currently provides equivalent formal parser coverage;
the exact pages are the evidence needed to expose and later pin the source grammar.

After the blockers are independently corrected, C4i3a tests must exercise the public
normalizer boundaries, not private helpers. The one direct module must verify strict
provenance/expected-facts schemas, raw SHA/length/encoding, exact capture reconstruction,
result and all four supported payout facts for both providers, zero network/archive
dependency, and source immutability. No production fixture loader is required.

## Future C4i3a implementation scope

After separate parser-fidelity approval, the exact allowed files are:

```text
.gitattributes
tests/fixtures/historical_replay/official/jra/race_result_20250913_nakayama_04.cp932.html
tests/fixtures/historical_replay/official/nar/race_mark_table_20260503_31_01.utf8.html
tests/fixtures/historical_replay/official/provenance.json
tests/fixtures/historical_replay/official/expected_facts.json
tests/test_portable_official_replay_fixtures.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

No production module, repository, migration, archive database, CLI, or replay
orchestration change belongs to C4i3a.

## C4i3b and future AI boundary

`C4I3B_BOUNDARY=CLI_BINDING_PLUS_COMPLETE_MIXED_PROVIDER_NO_NETWORK_REPLAY_ACCEPTANCE`.
C4i3b remains responsible for building temporary main/archive databases from portable
evidence and proving the complete request-to-`SimulationSummary` path. C4i3a does not
start it.

`FUTURE_AI_SIGNAL_ARCHITECTURE=OPTIONAL_AUDITABLE_AUGMENTATION_AFTER_VER0_8`.
`AI_SIGNAL_USAGE_BASELINE=DISABLED` and `CURRENT_C4I3A_AI_EFFECT=NONE`. This phase adds
no AI client, prompt, external call, model setting, schema, persistence, weighting, or
fixture.

## Disposition

- `NO_NETWORK_POLICY=NO_HTTP_NO_RECAPTURE_NO_BROWSER_RECONSTRUCTION`
- `C4I3A_TEST_POLICY=PUBLIC_INTEGRITY_AND_NORMALIZER_TESTS_AFTER_BLOCKER_CORRECTION`
- `C4I3B_STARTED=NO`
- `RECOMMENDED_NEXT_PHASE=4C-2d3b1i6d1d5f1c4i3a0_EXACT_SOURCE_PARSER_COMPATIBILITY_CORRECTION_AFTER_INDEPENDENT_REVIEW`

Stop for independent evidence/provenance architecture review. C4i3a fixture creation
and C4i3b remain unstarted.
