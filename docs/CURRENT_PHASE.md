# Current Phase

Status: `READY_FOR_REVIEW`

## Identity and scope

- Phase: `4C-2d3b1i6d1d5f1c4i3a`
- Name: `Portable Official Fixture Evidence and Provenance IMPLEMENTATION`
- Formal base: `08bf62135cf9dc1b555c7f26e728ae145e81f066`
- Formal branch: `feature/ver0.8-simulator`
- Review branch:
  `review/4c-2d3b1i6d1d5f1c4i3a-portable-official-fixtures`

Allowed changed files are exactly:

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

## Phase lineage

```text
C4I2:
FORMALLY_VERIFIED

C4I3A_PREPARE:
ARCHITECTURE_APPROVED

C4I3A0:
FORMALLY_VERIFIED

C4I3A0_FORMAL_COMMIT:
08bf62135cf9dc1b555c7f26e728ae145e81f066
```

## Fixture evidence contract

```text
FIXTURE_DERIVATION_POLICY:
EXACT_SOURCE_BYTES

DERIVED_BYTES_USED:
NO

BACKDATING_POLICY:
ORIGINAL_TIMESTAMPS_RETAINED_ONLY_WITH_EXACT_SOURCE_BYTES

FIXTURE_CAPTURE_IDENTITY_POLICY:
RECONSTRUCT_AND_REQUIRE_EXACT_SOURCE_CAPTURE_ID

JRA_FIXTURE_SHA256:
f5daa967f05ae1ee0cfcbe8d4c0e59aa8a6b3ceef126ce9d8689fe10ffa8ed0e

JRA_FIXTURE_BYTES:
94570

NAR_FIXTURE_SHA256:
3b909b6c9509713150199c3bb3821051181671e10c906f5c315aa4a4c4dbf2db

NAR_FIXTURE_BYTES:
96614

JRA_CAPTURE_ID_RECONSTRUCTION:
PASS_EXACT_COMPLETE_ID

NAR_CAPTURE_ID_RECONSTRUCTION:
PASS_EXACT_COMPLETE_ID

JRA_PUBLIC_RESULT_NORMALIZER:
PASS

JRA_PUBLIC_PAYOUT_NORMALIZERS:
PASS_ALL_FOUR_SUPPORTED_TYPES

NAR_PUBLIC_RESULT_NORMALIZER:
PASS

NAR_PUBLIC_PAYOUT_NORMALIZERS:
PASS_ALL_FOUR_SUPPORTED_TYPES
```

The two raw fixtures were written directly from the already-trusted read-only capture
objects without decoding, transcoding, newline normalization, comment removal, HTML
rewriting, or other byte mutation. The NAR complete capture ID is the exact
concatenation of prefix `nar-capture-v1:` and frozen suffix
`d6692261a54c1038a5ffd804ae79edda9ca543cb5d78f37c41ffaeefe281013b`.

## Portability and schemas

```text
PORTABILITY_POLICY:
CLEAN_CLONE_REPOSITORY_RELATIVE_NO_EXTERNAL_ARCHIVE

GIT_BINARY_POLICY:
EXACT_TWO_FIXTURE_MINUS_TEXT_MINUS_DIFF_RULES

PROVENANCE_SCHEMA:
STRICT_UTF8_SCHEMA_V1

EXPECTED_FACTS_SCHEMA:
STRICT_UTF8_SCHEMA_V1

COPYRIGHT_DATA_MINIMIZATION_POLICY:
TWO_EXACT_REQUIRED_TARGET_RESPONSES_ONLY
```

The fixture test uses only repository-relative files, reconstructs the exact formal
capture values, and exercises the public JRA and NAR result normalizers plus all four
supported public payout normalizers. It has no website, HTTP, browser, developer
archive, absolute-path, environment-variable, or current-clock dependency.

## Verification and boundaries

```text
DEDICATED_TESTS:
3 passed

RELATED_TESTS:
79 passed, 324 subtests passed

FULL_SUITE:
3111 passed, 2506 subtests passed

HTTP_PERFORMED:
NO

SOURCE_ARCHIVE_MUTATED:
NO

CAPTURE_SAVED:
NO

PRODUCTION_CHANGED:
NO

SCHEMA_CHANGED:
NO

MIGRATION_CHANGED:
NO

C4I3B_STARTED:
NO

FUTURE_AI_SIGNAL_ARCHITECTURE:
OPTIONAL_AUDITABLE_AUGMENTATION_AFTER_VER0_8

AI_SIGNAL_USAGE_BASELINE:
DISABLED

CURRENT_C4I3A_AI_EFFECT:
NONE

IMPLEMENTATION_BLOCKERS:
NONE

RECOMMENDED_NEXT_PHASE:
4C-2d3b1i6d1d5f1c4i3b_AFTER_INDEPENDENT_REVIEW_AND_FORMAL_INTEGRATION
```

Stop for independent ChatGPT review. Do not formal-integrate or begin C4i3b.
