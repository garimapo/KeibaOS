# Current Phase

Status: `READY_FOR_REVIEW`

## Identity and scope

- Phase: `4C-2d3b1i6d1d5f1c4i3a0`
- Name: `Exact Source Parser Compatibility Correction`
- Exact formal base/C4i2 formal commit:
  `7cec11686e7ac02d98782834200debe24bb9d15b`
- Formal branch: `feature/ver0.8-simulator`
- Review branch:
  `review/4c-2d3b1i6d1d5f1c4i3a0-exact-source-parser-compatibility`
- C4i2: `FORMALLY_VERIFIED`
- C4i3a PREPARE: `ARCHITECTURE_APPROVED_WITH_BLOCKERS`
- C4i3a fixture implementation:
  `BLOCKED_PENDING_C4I3A0_INDEPENDENT_REVIEW`

The exact changed-file scope is:

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

No fixture, `.gitattributes`, CLI, schema, migration, C4i2, C4i3b, HTTP, archive
write, capture save, or AI runtime work is authorized.

## Exact correction

`JRA_OFFICIAL_RACE_NUMBER_GRAMMAR=ASCII_1_TO_12_PLUS_EXACT_R_OR_JAPANESE_RACE_SUFFIX`.
Both JRA target result and payout boundaries retain exact full-match behavior and now
accept only `1R` through `12R` or `1レース` through `12レース`. They continue to reject
leading zero, out-of-range, whitespace, full-width, English-word, prefixed, suffixed,
and concatenated forms. Race-number equality with the canonical capture/snapshot race
identity is unchanged.

`NAR_HTML_COMMENT_POLICY=STRUCTURAL_COMMENTS_IGNORED_ORDINARY_DIRECT_TEXT_STILL_REJECTED`.
The NAR payout structural direct-text guard ignores only BeautifulSoup `Comment` nodes.
It still rejects every non-whitespace ordinary direct text node and leaves the existing
exact tag/table/row/cell/selection/amount/finality/unsupported-state grammar unchanged.
The strict direct-text helper is unchanged: a comment in a selection or amount location
does not become valid payout content.

## Exact trusted-source compatibility recheck

The previously verified archives were read only. Exact capture body SHA-256 and byte
length were recomputed before public normalization. No source byte, archive row, or
capture was changed.

```text
JRA source capture: jra-capture-v1:2d8fbee2df4a201923a49a48e02de3f6837293e0166a1347e30ef3f0b0aad296
JRA SHA / bytes: f5daa967f05ae1ee0cfcbe8d4c0e59aa8a6b3ceef126ce9d8689fe10ffa8ed0e / 94570
NAR source capture: nar-capture-v1:d6692261a54c1038a5ffd804ae79edda9ca543cb5d78f37c41ffaeefe281013b
NAR SHA / bytes: 3b909b6c9509713150199c3bb3821051181671e10c906f5c315aa4a4c4dbf2db / 96614
```

`JRA_EXACT_SOURCE_RESULT_COMPATIBILITY=PASS`.
The exact JRA source produces complete order
`7,3,6,12,5,2,13,4,9,10,8,11,1`.

`JRA_EXACT_SOURCE_PAYOUT_COMPATIBILITY=PASS_ALL_FOUR_SUPPORTED_TYPES`.
Its accepted normal payouts are `単勝 7=160`, `馬連 3-7=1030`, `ワイド
3-7=420, 6-7=300, 3-6=1370`, and `3連複 3-6-7=2280`.

`NAR_EXACT_SOURCE_RESULT_COMPATIBILITY=PASS`.
The exact NAR source produces complete order `8,10,11,4,1,5,7,9,3,6,2`.

`NAR_EXACT_SOURCE_PAYOUT_COMPATIBILITY=PASS_ALL_FOUR_SUPPORTED_TYPES`.
Its accepted normal payouts are `単勝 8=720`, `馬連 8-10=730`, `ワイド
8-10=300, 8-11=410, 10-11=350`, and `3連複 8-10-11=1230`.

`EXACT_SOURCE_FACTS_MATCH_PREPARE=PASS` and `NEW_EXACT_SOURCE_BLOCKER=NONE`.

## Retained C4i3a fixture policy

The future C4i3a evidence design remains unchanged:

```text
FIXTURE_DERIVATION_POLICY: EXACT_SOURCE_BYTES
BACKDATING_POLICY: ORIGINAL_TIMESTAMPS_RETAINED_ONLY_WITH_EXACT_SOURCE_BYTES
FIXTURE_CAPTURE_IDENTITY_POLICY: RECONSTRUCT_AND_REQUIRE_EXACT_SOURCE_CAPTURE_ID
FIXTURE_DIRECTORY_POLICY: tests/fixtures/historical_replay/official
FIXTURE_ENCODING_POLICY: JRA_RAW_CP932; NAR_RAW_UTF8; NO_TRANSCODING
FIXTURE_LINE_ENDING_POLICY: EXACT_SOURCE_BYTES_NO_NORMALIZATION
```

C4i3a, after independent approval, remains expected to add exact-path
`.gitattributes -text` entries for its two raw source fixtures. This correction does
not create those files or alter Git configuration.

## Boundaries and disposition

- `EXACT_SOURCE_BYTES_MUTATED=NO`
- `HTTP_PERFORMED=NO`
- `SOURCE_ARCHIVE_MUTATED=NO`
- `CAPTURE_SAVED=NO`
- `FIXTURE_CREATED=NO`
- `C4I3B_STARTED=NO`
- `FUTURE_AI_SIGNAL_ARCHITECTURE=OPTIONAL_AUDITABLE_AUGMENTATION_AFTER_VER0_8`
- `AI_SIGNAL_USAGE_BASELINE=DISABLED`
- `CURRENT_C4I3A0_AI_EFFECT=NONE`
- `IMPLEMENTATION_BLOCKERS=NONE`
- `RECOMMENDED_NEXT_PHASE=C4I3A_PORTABLE_OFFICIAL_FIXTURE_IMPLEMENTATION_AFTER_INDEPENDENT_REVIEW`

C4i3a owns only portable fixture evidence/provenance and direct fixture
integrity/normalizer tests. C4i3b remains CLI binding plus complete mixed-provider,
no-network replay acceptance. Stop for independent implementation review.
