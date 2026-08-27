# Current Phase

Status: `DRAFT_FOR_REVIEW`

## Identity and scope

- Phase: `4C-2d3b1i6d1d5f1c4h2a`
- Name: `NAR trusted target-race result evidence acquisition and grammar freeze`
- Exact formal base: `1e7550412481441a8e18f187092bdd46dd6db6e8`
- Approved PREPARE commit: `f2ba1e6f10d96d4299c9128f0fabc80d125bdbf7`
- Formal branch: `feature/ver0.8-simulator`
- Review branch:
  `review/4c-2d3b1i6d1d5f1c4h2a-nar-target-result-evidence`

This phase acquired and analyzed one exact official NAR `RaceMarkTable` response
through the formal live capture service. It changes documentation only. It does not
implement production code or Python tests, modify a repository or schema, commit raw
official bytes, discover another race, or start c4h3.

## Evidence sufficiency decision

`NAR_TARGET_RESULT_IMPLEMENTATION_EVIDENCE_STATUS`:
`SUFFICIENT_FOR_NARROW_IMPLEMENTATION`

The exact capture positively demonstrates the complete normal-final grammar needed
for an initial `COMPLETE_NORMAL_FINAL_ONLY` implementation: canonical and visible race
identity, one whole result table, one exact header, an exhaustive direct row set,
direct horse-number and finish-position cells, normal canonical decimal values, and a
same-response positive finality predicate.

This decision does not authorize any exceptional state. Scratch, exclusion, DQ, DNF,
dead heat, void, cancellation, provisional, and every unknown representation remain
fail closed. The evidence values for this race are not universal NAR row-count or
field-value constants.

## Immutable trusted capture

- `SOURCE_CAPTURE_ID`:
  `nar-capture-v1:d6692261a54c1038a5ffd804ae79edda9ca543cb5d78f37c41ffaeefe281013b`
- `SOURCE_CAPTURE_CANONICAL_URL`:
  `https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceMarkTable?k_babaCode=31&k_raceDate=2026%2F05%2F03&k_raceNo=1`
- `SOURCE_CAPTURE_RESPONSE_SHA256`:
  `3b909b6c9509713150199c3bb3821051181671e10c906f5c315aa4a4c4dbf2db`
- `SOURCE_CAPTURE_LENGTH`: `96614` bytes
- `SOURCE_CAPTURE_CHARSET`: `utf-8`
- `SOURCE_CAPTURE_REQUESTED_AT`: `2026-08-27T15:41:30.631495+00:00`
- `SOURCE_CAPTURE_OBSERVED_AT`: `2026-08-27T15:41:31.026438+00:00`
- `SOURCE_CAPTURE_STORED_AT`: `2026-08-27T15:41:31.026443+00:00`
- `SOURCE_CAPTURE_PAGE_KIND`: `NAROfficialPageKind.RACE_MARK_TABLE`
- `SOURCE_CAPTURE_HTTP_STATUS`: exact integer `200`
- `SOURCE_CAPTURE_CONTENT_TYPE`: `text/html; charset=UTF-8`
- `SOURCE_CAPTURE_CONTENT_ENCODING`: `None`
- `SOURCE_CAPTURE_HTTP_DATE`: `Thu, 27 Aug 2026 15:41:31 GMT`
- `SOURCE_CAPTURE_CONTENT_LENGTH`: `None`
- `SOURCE_CAPTURE_ETAG`: `None`
- `SOURCE_CAPTURE_LAST_MODIFIED`: `None`

The formal `NAROfficialLiveResponseCaptureService` performed the sole authorized
target-race HTTP attempt and called the archive before returning the immutable capture.
The capture was then reloaded by exact ID through
`SQLiteNAROfficialResponseCaptureRepository`; the reloaded value and raw bytes equal
the captured value exactly.

The isolated local archive is:

```text
C:\Users\garim\Desktop\KeibaAI-c4h2a-evidence-archive\nar-target-result-evidence.sqlite3
```

It is outside the repository and is not committed. Its post-capture file SHA-256 is
`976080b17a14988fb28a002aa778f4d487b4f76447c6a87398b811d89a8fea61`.
The raw response was neither altered nor transcoded; analysis used strict UTF-8 over
the exact archived bytes. The past race date was not used for any capture timestamp.

`ARCHIVE_RELOAD_VERIFICATION`: `PASS_EXACT_VALUE_AND_RAW_BYTES`

`BACKDATED_LIVE_RESPONSE`: `FORBIDDEN_AND_NOT_PERFORMED`

## Canonical and visible race identity

`RACE_IDENTITY_POLICY`:

```text
exact canonical URL
  k_raceDate=2026/05/03
  k_babaCode=31
  k_raceNo=1
-> nar:20260503:31:1
-> exact HistoricalInputSnapshot source identity at runtime
```

The same capture contains exactly one active course at
`.chartNavi.trackNameNavi a.cNaviBtn.courseBtn.active`, with whole value `高知`.
It contains exactly one direct race header at
`article.raceResult > div.innerWrapper > h4`, whose displayed value is:

```text
2026年5月3日（日）　高　知　第1競走 競走成績
```

After the already-formal display normalization, the visible calendar date is
`2026-05-03`, the place segment is exactly the active course `高知`, and the whole
race-number representation is exactly `第1競走`. All must agree with the canonical
URL identity. Substring race-number matching, alternate race/date/place fallback, row
context, horse name, and jockey name are forbidden.

`VISIBLE_RACE_IDENTITY_POLICY`:
`EXACT_URL_DATE_PLACE_RACE_NUMBER_AND_RESULT_HEADING_AGREEMENT`

## Whole-result container and header grammar

`RESULT_CONTAINER_POLICY`:
require exactly one direct result table at:

```text
article.raceResult > div.innerWrapper > section.gradeTable > table
```

The evidenced table has exactly one direct `tbody`, no `thead`, and direct `tr`
children. Its first direct row is the sole header row and contains exactly 16 direct
`th` children. Their classes are exactly `a` through `p` in order, and their
whitespace-normalized whole values are exactly:

```text
着順
枠
馬番
馬名
所属
性齢
負担重量
騎手（所属）
調教師
馬体重（増減）
タイム
着差
上がり3F
コーナー通過順
人気
単勝オッズ
```

`RESULT_HEADER_POLICY`:
`EXACT_ONE_DIRECT_HEADER_ROW_WITH_EXACT_A_TO_P_CLASS_AND_LABEL_GRAMMAR`

Missing, duplicate, reordered, extra, or contradictory header/table structure must
fail closed before any result write. Heading-name discovery across unrelated tables is
not an identity fallback.

## Applicable result-row grammar

`RESULT_ROW_POLICY`:
after the exact header, every remaining direct `tbody > tr` must be exactly one
applicable `tr.tBorder` normal-result row. Every applicable row must be classified and
parsed exactly once. Extra, mixed, malformed, unknown, or unclassified direct rows or
cells fail closed; no applicable row may be omitted.

The trusted capture has 11 applicable rows. Every row has exactly 16 direct `td`
children corresponding to the evidenced `a` through `p` field classes. There are no
additional direct rows inside the same table and no exceptional-state marker in the
result-table row values.

`RESULT_ROW_COUNT_IN_EVIDENCE`: `11`

The row count `11` is a fact about this capture, not a universal provider constant.
The future parser must derive `N` from the exhaustively classified direct row set.

`HORSE_NUMBER_POLICY`:
each accepted row has exactly one direct `td.c` horse-number cell whose complete
normalized value matches canonical positive ASCII decimal `[1-9][0-9]*`. The evidence
values in result-row display order are:

```text
8, 10, 11, 4, 1, 5, 7, 9, 3, 6, 2
```

They are unique. Horse-number identity remains race-local:

```text
nar:20260503:31:1 + horseNum
-> nar:20260503:31:1:entry:<horseNum>
-> exact snapshot external_entry_id
-> exact internal race_entry_id
```

Horse name, HorseMarkInfo lineage ID, jockey, row index, display order, global horse
number, prediction output, and cross-provider numeric coincidence are forbidden.

`FINISH_POSITION_POLICY`:
each accepted normal row has exactly one direct `td.a` finish-position cell whose
complete normalized value matches canonical positive ASCII decimal `[1-9][0-9]*`.
The evidence values are exactly the unique contiguous sequence `1` through `11`.

For the narrow normal-only implementation, require the parsed finish set to equal
`{1, ..., N}` for the exhaustively parsed `N` rows. This is a conservative accepted
normal-form restriction; it does not claim universal support for ties or exceptional
states. Row order is display evidence only and must not provide race-entry identity.

`NORMAL_FINAL_ROW_EVIDENCE`:
`ELEVEN_EXHAUSTIVE_UNIQUE_HORSE_ROWS_WITH_UNIQUE_CONTIGUOUS_FINISH_1_TO_11`

## Positive terminal/finality evidence

Finality is not inferred from HTTP 200, the past race date, numeric positions, or the
page path alone. The same exact capture contains both:

1. exactly one populated
   `article.raceResult > div.innerWrapper > section.winHorseTable`, headed by exactly
   one direct `h4 > span.smallTitle` with whole value `優勝馬情報`; and
2. exactly one official attention paragraph whose whole statement is:

```text
※2026年4月以降、優勝馬の情報はレース終了翌日までに表示されます。また、優勝馬の情報はレース結果確定時点の情報となります。
```

The populated winner-information section and the same-response official statement
that winner information is the information at `レース結果確定時点` are the positive
terminal predicate for this narrow grammar. No separate documentation HTTP was used.

`FINALITY_EVIDENCE_IN_CAPTURE`:
`POPULATED_UNIQUE_WIN_HORSE_SECTION_PLUS_EXACT_RESULT_FINALIZATION_STATEMENT`

`OFFICIAL_FINALITY_DOCUMENTATION_EVIDENCE`: `NOT_USED`

If either part is missing, duplicated, malformed, contradictory, or not paired with
the complete accepted normal result table in the same capture, no result may be
persisted.

## Coverage and provider-neutral result policy

`SNAPSHOT_RESULT_COVERAGE_POLICY`:
the future normal-only implementation must first resolve every unique official horse
number through the exact race-local snapshot crosswalk, then require exact mutual
coverage:

```text
set(mapped official result race_entry_ids)
==
set(snapshot entry race_entry_ids)
```

The capture proves an exhaustive 11-row normal result-table universe. This phase did
not fabricate or attach a `HistoricalInputSnapshot`; runtime mutual coverage remains
the fail-closed check that binds that official universe to the caller's exact snapshot.
Missing, extra, duplicate, wrong-race, or incoherent mappings prevent all writes.

After complete validation, create one `PersistedRaceResult` with:

- `race_id = snapshot.internal_race_id`;
- `status = RaceResultStatus.COMPLETE`;
- one `PersistedRaceResultEntry` per exhaustive normal row;
- every entry `status = RaceResultEntryStatus.CONFIRMED`;
- exact positive finish position from the accepted `td.a`;
- `observed_at = capture.observed_at`;
- `finalized_at = capture.observed_at` under the conservative
  first-capture-proves-final rule; and
- `source = capture.capture_id`.

No exact provider finalization timestamp is present. Using capture observation time
does not claim that NAR finalized the race at that time; it is the first time this
immutable capture proves finality. It must never be backdated.

## Narrow support envelope

- `NORMAL_FINAL_POLICY`: `SUPPORTED_BY_APPROVED_EVIDENCE`
- `SCRATCH_POLICY`: `FAIL_CLOSED_NOT_EVIDENCED`
- `DQ_DNF_POLICY`: `FAIL_CLOSED_NOT_EVIDENCED`
- `DEAD_HEAT_POLICY`: `FAIL_CLOSED_NOT_EVIDENCED`
- `VOID_POLICY`: `FAIL_CLOSED_NOT_EVIDENCED`
- `PROVISIONAL_POLICY`: `NO_WRITE_UNTIL_POSITIVELY_PROVEN_TERMINAL`
- `UNKNOWN_POLICY`: `FAIL_CLOSED_ZERO_RESULT_WRITES`

The capture contains no result-table representation of a scratch, exclusion, DQ,
DNF, dead heat, cancellation, void, provisional state, or unknown result. Their
absence proves no grammar for them. The future parser must not guess markers or widen
the support envelope.

## Approved future implementation proposal

Proposed new module:

```text
scripts/simulation/nar_target_race_result_persistence.py
```

Proposed module-local public boundary:

```python
__all__ = (
    "NARTargetRaceResultPersistenceError",
    "NARTargetRaceResultPersistenceValidationError",
    "NARTargetRaceResultPersistenceUnavailableError",
    "NARTargetRaceResultPersistenceUnsupportedError",
    "normalize_and_persist_nar_target_race_result",
)

def normalize_and_persist_nar_target_race_result(
    *,
    capture_id: str,
    capture_archive: NAROfficialResponseCaptureArchive,
    snapshot: HistoricalInputSnapshot,
    race_result_repository: RaceResultRepository,
) -> PersistedRaceResult:
    ...
```

One exact capture-ID load per call; no latest, fallback, URL search, retry, HTTP, or
capture write. Validate exact capture type/ID/page kind, canonical and visible race
identity, exact result grammar, finality, race-local crosswalk, exhaustive row and
snapshot coverage, and constructed domain value before exactly one
`save_race_result(result)`. Repository exceptions propagate unchanged. There is no
partial persistence, retry, compensation, or package-root export.

The module-local error hierarchy remains the PREPARE proposal: a common
`NARTargetRaceResultPersistenceError(ValueError)` with Validation, Unavailable, and
Unsupported specializations. Unknown or malformed normal structure fails closed;
recognized but unapproved provider states are unsupported; missing exact capture or
missing positive complete/final evidence is unavailable.

`RACE_RESULT_REPOSITORY_PROTOCOL_CHANGE_REQUIRED`: `NO`

`SQLITE_RACE_RESULT_REPOSITORY_CHANGE_REQUIRED`: `NO`

`SCHEMA_CHANGE_REQUIRED`: `NO`

`MIGRATION_REQUIRED`: `NO`

The insert-only result repository remains sufficient for this narrow initial write.
A differing later correction is outside this phase and must conflict rather than
overwrite.

## Evidence artifact and scope decisions

`DERIVED_FIXTURE_POLICY`: `NO_NEW_FIXTURE`

The existing minimized structural fixture remains a parser regression artifact and
was not rewritten. The complete 96,614-byte official response is retained only in the
isolated immutable archive. No raw or derived response fixture is committed.

`IMPLEMENTATION_BLOCKERS`: `NONE_FOR_NARROW_COMPLETE_NORMAL_FINAL_ONLY`

`RECOMMENDED_NEXT_PHASE`:
`4C-2d3b1i6d1d5f1c4h2_NAR_TARGET_RACE_RESULT_NORMALIZATION_AND_PERSISTENCE_IMPLEMENTATION_AFTER_INDEPENDENT_EVIDENCE_APPROVAL`

The evidence does not authorize c4h3 or any payout work. C4h3 remains unstarted.

Allowed changes in this evidence phase are exactly:

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

No pytest is required because no Python changed. Stop after the docs-only evidence
branch is published for independent review.
