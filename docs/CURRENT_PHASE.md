# Current Phase

Status: `READY_FOR_REVIEW`

## Identity and authorised scope

- Phase: `4C-2d3b1i6d1d5f1c4h2`
- Phase name: `NAR official target-race result normalization and persistence`
- Exact formal base: `1e7550412481441a8e18f187092bdd46dd6db6e8`
- Approved PREPARE commit: `f2ba1e6f10d96d4299c9128f0fabc80d125bdbf7`
- Approved evidence commit: `af0d51b3dfa77dda1efb324b3a15d32cde3b9c07`
- Review branch: `review/4c-2d3b1i6d1d5f1c4h2-nar-target-result`

The implementation changes exactly these paths:

```text
scripts/simulation/nar_target_race_result_persistence.py
tests/test_nar_target_race_result_persistence.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

No existing production or test module, capture/archive contract, repository protocol,
SQLite repository, schema, migration, package export, database, or log changes are in
scope. C4h3 is unstarted.

## Approved evidence source

The implementation does not reload, recapture, or otherwise acquire evidence. Its
grammar is restricted to the independent evidence review's immutable NAR capture:

- Capture ID:
  `nar-capture-v1:d6692261a54c1038a5ffd804ae79edda9ca543cb5d78f37c41ffaeefe281013b`
- Canonical URL:
  `https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceMarkTable?k_babaCode=31&k_raceDate=2026%2F05%2F03&k_raceNo=1`
- Response SHA-256:
  `3b909b6c9509713150199c3bb3821051181671e10c906f5c315aa4a4c4dbf2db`
- Exact response length: `96614` UTF-8 bytes.
- Capture observation: `2026-08-27T15:41:31.026438+00:00`.

That capture proves one normal, exhaustive 11-row result table with the direct
horse-number sequence `8, 10, 11, 4, 1, 5, 7, 9, 3, 6, 2`, unique contiguous finish
positions `1..11`, and the positive finality structure used below. Eleven is evidence
for that capture, not a parser constant: the implementation derives `N` from the
exhaustively classified row set.

## Public boundary

Module-local `__all__` exposes exactly:

```python
NARTargetRaceResultPersistenceError
NARTargetRaceResultPersistenceValidationError
NARTargetRaceResultPersistenceUnavailableError
NARTargetRaceResultPersistenceUnsupportedError
normalize_and_persist_nar_target_race_result
```

```python
def normalize_and_persist_nar_target_race_result(
    *,
    capture_id: str,
    capture_archive: NAROfficialResponseCaptureArchive,
    snapshot: HistoricalInputSnapshot,
    race_result_repository: RaceResultRepository,
) -> PersistedRaceResult:
```

Each call validates the public boundary, loads exactly one archived capture by the
exact supplied ID, and has no latest, URL-search, fallback, retry, live HTTP, capture
write, direct database, clock, or prediction behavior. Archive and repository
exceptions propagate unchanged.

## Narrow supported envelope

`SUPPORTED_ENVELOPE`: `NORMAL_COMPLETE_FINAL_ONLY`

The capture must be an exact `NAROfficialResponseCapture` with matching ID and
`RACE_MARK_TABLE` page kind. Its canonical URL, visible date/place/race heading, and
active course must all agree with the exact NAR snapshot identity. The implementation
derives the race identity only from the canonical URL:

```text
nar:YYYYMMDD:<babaCode>:<raceNo>
```

The strict UTF-8 document requires the evidence-frozen whole-race table:

```text
article.raceResult > div.innerWrapper > section.gradeTable > table
  > tbody
    > tr                 exact a..p header
    > tr.tBorder...      exact result rows
```

Header labels and direct child structure, direct row/cell structure, and evidenced
field-class variants are all checked. Horse number and finish position are exact
positive ASCII decimal tokens. Result rows must contain unique horse numbers and a
complete contiguous finish set `1..N`; duplicate, nonnumeric, non-contiguous, tied,
dead-heat, scratched, excluded, DQ, DNF, void, partial, or unknown representations
are not normalized as COMPLETE and fail closed.

`KNOWN_EXCEPTIONAL_ROW_MARKER_POLICY`: `FAIL_CLOSED_REJECTION_ONLY`

Every applicable result row is also scanned as one normalized whole display value for
the existing formal NAR marker vocabulary `取消`, `除外`, `中止`, `失格`, and `降着`.
Any occurrence raises `NARTargetRaceResultPersistenceUnsupportedError` before result
construction or repository save, even when `td.a` otherwise contains a valid numeric
finish. The marker vocabulary does not authorize exceptional-state normalization:
it supplies no scratch, exclusion, DNF, DQ, demotion, replacement-position, void, or
settlement semantics.

Positive finality requires the exact evidence-frozen populated `winHorseTable` shape,
`優勝馬情報` heading, required winner-information structures, and exactly one official
attention statement saying winner information reflects result confirmation. Missing
positive evidence is unavailable; malformed or contradictory evidence is validation
failure; a recognized non-normal finish representation is unsupported. No partial
result is written.

## Race-local crosswalk and persistence

Only this mapping is accepted:

```text
exact canonical NAR race identity + official horse number
-> nar:...:entry:<horse number>
-> exact snapshot external_entry_identity.external_entry_id
-> exact internal race_entry_id
```

Horse name, jockey, row order, global horse-number lookup, prediction selection, and
cross-provider coincidence are never identity sources. Snapshot and official result
entry sets must cover one another exactly before construction.

After all public, capture, URL, visible identity, result-table, finality, and crosswalk
checks succeed, the boundary constructs one `PersistedRaceResult` with
`RaceResultStatus.COMPLETE`, confirmed entries, and both `observed_at` and
`finalized_at` equal to the exact capture observation. `source` is the exact capture
ID. It calls `save_race_result` exactly once and returns the constructed result. Any
validation failure writes zero results.

## Verification

- Dedicated: `13 passed, 66 subtests passed`
- Related: `153 passed, 245 subtests passed`
- Full suite: `3001 passed, 2177 subtests passed`
- Static ownership/scope checks: passed.
- `git diff --check`: passed.

No live HTTP, trusted evidence reload or recapture, database write, schema/migration,
or C4h3 work was performed during this implementation. This remains review work only;
formal integration is not claimed.
