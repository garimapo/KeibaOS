# Current Phase

Status: `READY_FOR_REVIEW`

## Identity and scope

- Phase: `4C-2d3b1i6d1d5f1c4i3a0`
- Name: `Exact Source Parser Compatibility Correction RESTART — Contract Correction 1`
- Exact formal base: `54cc6b8b02ff53ec2168ae9d3c0f0816b9b1b122`
- Formal branch: `feature/ver0.8-simulator`
- Review branch:
  `review/4c-2d3b1i6d1d5f1c4i3a0-exact-source-parser-compatibility-restart`

Allowed changed files are exactly:

```text
scripts/simulation/jra_target_race_result_persistence.py
scripts/simulation/jra_target_race_payout_persistence.py
scripts/simulation/nar_target_race_payout_persistence.py
tests/test_jra_target_race_result_persistence.py
tests/test_jra_target_race_payout_persistence.py
tests/test_nar_target_race_payout_persistence.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Restart provenance

```text
C4I3A0:
RESTARTED_WITH_CONTRACT_CORRECTION_1

PREVIOUS_CANDIDATE:
d28176095f56c642f30e8eca2589cb98ced1720b

PREVIOUS_CANDIDATE_OVERALL_APPROVAL:
REVOKED_FOR_NAR_SEMANTIC_COMMENT_HOLE

C4I3A0CI0:
FORMALLY_VERIFIED

C4I3A0CI0_FORMAL_COMMIT:
54cc6b8b02ff53ec2168ae9d3c0f0816b9b1b122

FORMAL_BASELINE_CI:
PASS

FOUR_JRA_CANDIDATE_BLOBS_REUSED_EXACTLY:
YES

TWO_NAR_CANDIDATE_BLOBS_USED_AS_STARTING_POINT:
YES

TWO_NAR_FINAL_BLOBS_DIFFER_FROM_OLD_CANDIDATE:
EXPECTED

OLD_REVIEW_DOCS_REUSED:
NO
```

The four JRA production/test blobs remain byte-identical to the individually reviewed
candidate blobs. The two NAR candidate blobs supplied only the reviewed structural
starting point; their final blobs include the independently required semantic-comment
correction and its dedicated regression tests. The formal SQLite-portable migration
test correction remains inherited unchanged as blob
`3ee4f329abc39e56c2c7e74f9a0fed24ff47b1fc`.

## Frozen parser semantics

```text
JRA_OFFICIAL_RACE_NUMBER_GRAMMAR:
ASCII_1_TO_12_PLUS_EXACT_R_OR_JAPANESE_RACE_SUFFIX

NAR_STRUCTURAL_COMMENT_POLICY:
STRUCTURAL_COMMENTS_IGNORED

NAR_SEMANTIC_COMMENT_POLICY:
COMMENTS_NEVER_BECOME_SEMANTIC_TEXT
```

Both JRA boundaries accept only ASCII `1`–`12` followed by exact `R` or `レース`,
using full-match grammar and unchanged canonical race-identity equality. Leading zero,
zero, omitted/English/full-width/whitespace suffixes, prefixes, concatenations, and
extra suffixes remain rejected.

NAR structural guards ignore only BeautifulSoup `Comment` nodes where structural
comments are expressly allowed; ordinary non-whitespace direct text and unexpected
tags remain rejected. Strict semantic text requires no direct child tag and exactly
one ordinary `NavigableString`; a sole `Comment` is invalid. Comments never provide a
payout group label, selection, or amount, and comment-plus-text remains invalid. All
failures occur before payout save.

No public API, error hierarchy, provider/race identity, finality, crosswalk, payout
table/group/row count, supported bet type, selection/amount grammar, unsupported-state
handling, or persistence behavior changed.

## Exact-source and verification disposition

The exact immutable JRA (`94570` bytes; SHA-256
`f5daa967f05ae1ee0cfcbe8d4c0e59aa8a6b3ceef126ce9d8689fe10ffa8ed0e`)
and NAR (`96614` bytes; SHA-256
`3b909b6c9509713150199c3bb3821051181671e10c906f5c315aa4a4c4dbf2db`)
capture bodies were reloaded through read-only SQLite archives without mutation. Both
public result boundaries and all four supported payout boundaries reproduced the
approved finish orders, selections, and amounts.

```text
JRA_SOURCE_SHA_RECHECK: PASS
NAR_SOURCE_SHA_RECHECK: PASS
JRA_EXACT_SOURCE_RESULT_COMPATIBILITY: PASS
JRA_EXACT_SOURCE_PAYOUT_COMPATIBILITY: PASS_ALL_FOUR_SUPPORTED_TYPES
NAR_EXACT_SOURCE_RESULT_COMPATIBILITY: PASS
NAR_EXACT_SOURCE_PAYOUT_COMPATIBILITY: PASS_ALL_FOUR_SUPPORTED_TYPES
EXACT_SOURCE_FACTS_MATCH_PREPARE: PASS
NEW_EXACT_SOURCE_BLOCKER: NONE

DEDICATED_TESTS: 42 passed, 200 subtests passed
RELATED_TESTS: 59 passed, 106 subtests passed
FULL_SUITE: 3108 passed, 2506 subtests passed
REMOTE_CI: PASS
```

No fixture, HTTP, capture save, archive mutation, schema, migration, public surface,
AI runtime, or C4i3b work occurred. The future AI policy remains
`OPTIONAL_AUDITABLE_AUGMENTATION_AFTER_VER0_8` with baseline usage disabled and
`CURRENT_C4I3A0_AI_EFFECT=NONE`.

Stop for independent ChatGPT review. Do not formal-integrate or begin C4i3a fixture
provenance/C4i3b work.
