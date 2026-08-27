# Current Phase

Status: `DRAFT_FOR_REVIEW`

## Identity and scope

- Phase: `4C-2d3b1i6d1d5f1c4h2`
- Name: `NAR official target-race result normalization and persistence PREPARE`
- Exact formal base: `1e7550412481441a8e18f187092bdd46dd6db6e8`
- Formal branch: `feature/ver0.8-simulator`
- Review branch: `review/4c-2d3b1i6d1d5f1c4h2-nar-target-result-prepare`
- C4h0 formal commit: `2834fc9eca4571c0044b9491bd25149fa9473e18`
- C4h1 formal commit: `1e7550412481441a8e18f187092bdd46dd6db6e8`

This is a design and evidence PREPARE only. It changes no production Python, Python
tests, capture archive, repository, SQLite implementation, schema, migration,
package-root export, database, or fixture. It performs no live HTTP and creates no
trusted capture. C4h3 and C4h4 are unstarted.

`C4H2_PURPOSE`:
freeze the smallest fail-closed NAR target-race result persistence contract from
existing formal evidence, or explicitly stop at the exact missing trusted evidence.

C4h2 owns only NAR official target-race **result** normalization and persistence. NAR
payout normalization belongs to c4h3. Official acquisition/application composition,
settlement-cutoff choice, and final-completeness checks belong to c4h4. Prediction,
historical snapshots, bet plans, allocation, settlement arithmetic, and
`SimulationSummary` are outside this phase.

## Existing formal boundaries reused unchanged

The following existing contracts are sufficient as future collaborators and are not
redesigned by c4h2:

- `NAROfficialResponseCapture`, `NAROfficialResponseCaptureArchive`, and
  `NAROfficialPageKind.RACE_MARK_TABLE` provide immutable, strict-UTF-8 official
  evidence. A capture ID is content-addressed from canonical URL, observation time,
  page kind, digest, and schema version.
- `canonicalize_nar_official_capture_url(response_url)` validates the closed official
  RaceMarkTable URL boundary: HTTPS `www.keiba.go.jp`, exact path
  `/KeibaWeb/TodayRaceInfo/RaceMarkTable`, and exact `k_babaCode`, `k_raceDate`, and
  `k_raceNo` query keys. It returns the page kind and canonical URL.
- `NAROfficialLiveResponseCaptureService` is the sole existing live capture path. It
  samples `requested_at`, reads one complete identity-encoded HTTPS entity, samples
  `observed_at`, samples `stored_at`, archives the immutable capture before returning,
  and never backdates. C4h2 must not call it.
- `HistoricalInputSnapshot` requires each entry's
  `HistoricalExternalEntryIdentity.external_race_identity` to equal its snapshot
  `HistoricalSourceIdentity`; entries have unique internal `race_entry_id`, horse
  number, and external entry identity.
- `PersistedRaceResult`, `PersistedRaceResultEntry`, `RaceResultStatus`,
  `RaceResultEntryStatus`, and `RaceResultRepository` are the existing
  provider-neutral output contract. `RaceResultStatus.COMPLETE` requires aware
  `finalized_at`; entries have unique internal IDs.
- `SQLiteRaceResultRepository` is insert-only per internal race. An equal retry is
  idempotent; a differing later result raises `RepositoryConflictError`. No result
  publication versioning is introduced here.

`RACE_RESULT_REPOSITORY_PROTOCOL_CHANGE_REQUIRED`: `NO_FOR_NARROW_INITIAL_WRITE`

`SQLITE_RACE_RESULT_REPOSITORY_CHANGE_REQUIRED`: `NO_FOR_NARROW_INITIAL_WRITE`

`SCHEMA_CHANGE_REQUIRED`: `NO`

`MIGRATION_REQUIRED`: `NO`

A later official correction that differs from an already persisted result is outside
the insert-only c4h2 envelope and fails closed through the existing repository. It
requires its own evidence/versioning design rather than overwrite behavior.

## NAR race and entry identity contract

`RACE_IDENTITY_POLICY`:

```text
exact archived RaceMarkTable canonical URL
  k_raceDate + k_babaCode + k_raceNo
-> existing formal NAR external race ID grammar
   nar:YYYYMMDD:<canonical babaCode>:<canonical raceNo>
-> exact snapshot.identity.source_identity
```

The capture canonicalizer is the public URL authority. The current NAR historical
input normalizer is the formal source of the external-ID construction grammar; it
constructs exactly the string above. There is no separate public NAR external-race-ID
builder to reuse today. A future c4h2 module may derive that exact string locally only
after the canonical URL has been accepted, without changing the existing historical
normalizer.

`SNAPSHOT_CROSSWALK_POLICY`:

```text
exact accepted NAR external race ID
+ exact official canonical horseNum
-> nar:YYYYMMDD:<babaCode>:<raceNo>:entry:<horseNum>
-> exact snapshot entry.external_entry_identity.external_entry_id
-> exact internal race_entry_id
```

This is race-local only. Horse name, jockey name, HorseMarkInfo lineage/profile ID,
display order, table row index, prediction selection, global horse-number lookup,
cross-provider numeric coincidence, and fallback to another race are forbidden.
Missing, duplicate, wrong-race, incoherent, or ambiguous mappings are validation
failure before any result write.

`VISIBLE_RACE_IDENTITY_POLICY`:
the eventual parser must require the same exact capture URL identity and proven visible
RaceMarkTable date, active course/place, and whole race-number representation. Existing
historical parsing validates its own `h4` date/race number and active course coherence,
but no target-result capture yet proves the complete target parser selector/grammar.
No unproven selector is frozen as accepted.

## Existing evidence assessment

`NAR_TARGET_RESULT_EXISTING_EVIDENCE_STATUS`:
`NO_REVIEWABLE_TRUSTED_TARGET_RESULT_EVIDENCE`

The repository has synthetic/minimized NAR parser fixtures, including
`tests/fixtures/nar/race_mark_table_past_race_result.html`, and tests construct
supplied responses. They are useful parser regressions only; they do not carry an
immutable archived capture ID, trusted observation record, response digest/length,
or approved target-race provenance. They are not trusted target-result evidence.

The documented local isolated evidence archive is JRA-only. No formally reviewable NAR
capture ID, canonical RaceMarkTable URL, response SHA-256, response length, charset,
requested/observed/stored timestamps, page-kind record, or archive provenance exists
for a NAR target-race result in the formal repository or known local evidence
references. No fresh response was acquired during this PREPARE.

Consequently, the following target-result facts are **not** evidenced and must not be
implemented from the existing synthetic fixtures:

- the exact whole-result container/table selector and header set;
- direct official horse-number selector and complete token grammar for every result
  row;
- target-wide result-row selector and exact row membership;
- direct finish-position selector/grammar and whether positions are contiguous or may
  be tied;
- a positive terminal/finality predicate for a RaceMarkTable target result;
- normal-race exact row-to-snapshot mutual coverage;
- scratch/non-starter, DQ/DNF/exclusion, dead-heat, void/cancelled, provisional, and
  other official representation grammars.

The existing `nar_historical_past_race_source.py` is not a whole-target-result parser.
It locates one historical row through a HorseMarkInfo lineage anchor, reads historical
row fields, and explicitly rejects cancellation markers. Its RaceMarkTable table and
`td.a` finish handling cannot prove a target-wide horse-number crosswalk, coverage, or
terminality. No existing NAR helper may be widened or refactored for c4h2 merely for
reuse.

`NAR_TARGET_RESULT_IMPLEMENTATION_EVIDENCE_STATUS`:
`INSUFFICIENT_REQUIRES_SEPARATE_TRUSTED_EVIDENCE_PHASE`

## Proposed future public boundary — blocked pending evidence

Proposed module:

```text
scripts/simulation/nar_target_race_result_persistence.py
```

Proposed module-local public surface:

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

`PROPOSED_PUBLIC_API`: the keyword-only function above, with no package-root export.

`PUBLIC_ERROR_SURFACE`:

- `NARTargetRaceResultPersistenceValidationError`: malformed, contradictory, wrong
  type, incoherent identity/crosswalk, duplicate row/entry, or unclassified structure.
- `NARTargetRaceResultPersistenceUnavailableError`: exact capture is absent or the
  evidence does not positively prove the required complete terminal normal result.
- `NARTargetRaceResultPersistenceUnsupportedError`: a positively recognized official
  representation outside the evidence-approved envelope.

The exact hierarchy is module-local and must inherit a small common
`NARTargetRaceResultPersistenceError(ValueError)`, following c4h0 only as an
architectural analogue. Archive and result-repository exceptions propagate unchanged;
there is no broad `Exception` or `BaseException` catch.

## Future read, validation, and write policy

`CAPTURE_ID_POLICY`: caller supplies one non-empty exact capture ID.

`CAPTURE_LOAD_POLICY`: exactly one
`capture_archive.load_capture(capture_id=capture_id)` per public call. No latest
selection, URL search, nearby-capture fallback, retry, HTTP, capture creation, or
capture write. The returned object must be exact `NAROfficialResponseCapture`, retain
the requested ID, and have exact `NAROfficialPageKind.RACE_MARK_TABLE`.

`RESULT_CONTAINER_POLICY`: no accepted selector is frozen until a trusted normal
target capture proves one exact container/table/header grammar. Existing historical
single-row selectors are not authorization for target-wide parsing.

`RESULT_ROW_POLICY`: each applicable official target result row must be discovered by
the evidence-frozen direct grammar, classified exactly once, and parsed before write.
No row order has identity semantics. Unknown, additional, malformed, duplicate, or
unclassified applicable rows fail closed.

`HORSE_NUMBER_POLICY`: only the trusted-capture-proven exact direct row value may be
accepted, using canonical positive ASCII decimal grammar and the race-local crosswalk
above. The exact selector remains an evidence blocker.

`FINISH_POSITION_POLICY`: only a capture-proven normal finish representation may map
to positive `finish_position` and `RaceResultEntryStatus.CONFIRMED`. The current
evidence proves neither normal target-wide position grammar nor tie handling.

`RESULT_COMPLETENESS_POLICY`: `RaceResultStatus.COMPLETE` may be created only after
all of the following are positively proven by the **same exact capture**:

1. capture, canonical URL, snapshot source identity, and visible identity agree;
2. the provider page is positively terminal/final under an evidence-frozen predicate;
3. every applicable target result row has been parsed and classified;
4. every official horse number resolves exactly through the race-local snapshot
   crosswalk; horse numbers and mapped `race_entry_id` values are unique;
5. every confirmed finish position obeys the evidence-frozen normal grammar; and
6. no applicable row, identity, status, or result evidence is malformed, unknown,
   duplicated, contradictory, or silently omitted.

`SNAPSHOT_RESULT_COVERAGE_POLICY`: for the narrow normal-final envelope, require exact
mutual coverage after the crosswalk:

```text
set(mapped official result race_entry_ids) == set(snapshot.entries race_entry_id)
```

This remains a proposed requirement, not an implemented rule, until a trusted normal
capture proves whether RaceMarkTable normal result rows cover exactly the target
snapshot entry universe. If the provider includes non-starter rows, that requires
separate evidence and must not be guessed.

`NORMAL_FINAL_POLICY`: `NOT_YET_PROVEN`.

`SCRATCH_POLICY`: `FAIL_CLOSED_NOT_EVIDENCED`.

`DQ_DNF_POLICY`: `FAIL_CLOSED_NOT_EVIDENCED`.

`DEAD_HEAT_POLICY`: `FAIL_CLOSED_NOT_EVIDENCED`.

`VOID_POLICY`: `FAIL_CLOSED_NOT_EVIDENCED`.

`PROVISIONAL_POLICY`: `NO_WRITE_UNTIL_POSITIVELY_PROVEN_TERMINAL`.

`UNKNOWN_ROW_POLICY`: `FAIL_CLOSED_ZERO_RESULT_WRITES`.

`OBSERVED_AT_POLICY`: exact immutable `capture.observed_at`; never race date,
scheduled start, insertion time, current clock, file mtime, or guessed publication
time.

`FINALIZED_AT_POLICY`: an exact provider-attested final timestamp only if the same
trusted capture proves its meaning. Otherwise, after a capture positively proves a
terminal result, use exact `capture.observed_at` as conservative first-proven-final
time. Never backdate.

`SOURCE_POLICY`: `PersistedRaceResult.source == exact capture.capture_id`. The existing
result domain has no `source_url` field; capture ID remains immutable provenance.

`RESULT_SAVE_POLICY`: construct exactly one `PersistedRaceResult` only after complete
validation; then call `race_result_repository.save_race_result(result)` exactly once
and return the constructed exact result. No partial-row write, no retry, no rollback
or compensation owned by c4h2.

`REPOSITORY_EXCEPTION_POLICY`: propagate the exact repository exception unchanged;
never translate it into a partial result, unavailable result, retry, or empty result.

`PARTIAL_SUCCESS_POLICY`: `FORBIDDEN`.

## Evidence phase required before implementation

`IMPLEMENTATION_BLOCKERS`:

```text
No approved immutable trusted NAR RaceMarkTable target-race capture establishes the
whole-race normal-final table, positive terminality, row-to-horseNum grammar,
finish-position grammar, or exact result-row/snapshot coverage.
```

`RECOMMENDED_NEXT_PHASE`:
`4C-2d3b1i6d1d5f1c4h2a_NAR_TRUSTED_TARGET_RESULT_EVIDENCE_ACQUISITION_AND_GRAMMAR_FREEZE`

That evidence-only phase must first locate or acquire through the existing formal NAR
live capture service one ordinary completed RaceMarkTable capture and archive it before
returning. It must freeze immutable capture ID, canonical URL, digest, length, strict
UTF-8 metadata, requested/observed/stored timestamps, page kind, visible identity,
whole table/row/horse-number/finish grammar, finality proof, and row-to-snapshot
coverage. It may support only states positively demonstrated; all others remain fail
closed. It must not backdate a live response or treat a synthetic fixture as trusted
evidence.

`NEXT_PHASE_ALLOWED_FILES`:

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
tests/fixtures/nar/ only if an independently approved evidence policy authorizes an
immutable provenance manifest or derived fixture; no existing fixture rewrite
```

`EXISTING_PRODUCTION_CHANGE_EXPECTED`:
`NEW_C4H2_MODULE_ONLY_AFTER_EVIDENCE_APPROVAL`; existing NAR historical parsers,
capture/archive modules, repository protocol, SQLite repository, schema, migrations,
c4h0, c4h1, c4g2a, and c4g2b remain frozen.

`REAL_END_TO_END_READY_AFTER_C4H2`: `NO`. Even after a result boundary, c4h3 NAR
payout evidence/normalization and c4h4 acquisition/application composition, cutoff
choice, and final-completeness checks remain required.

## Required future test matrix

The later c4h2 implementation tests must use only approved trusted evidence or a
clearly labelled synthetic grammar fixture derived from it. They must pin:

- module public surface, exact keyword-only signature/type hints, no package export,
  and no HTTP/direct SQLite/current-clock ownership;
- exact single capture-ID load, wrong type/ID/page-kind rejection, and unchanged
  archive exceptions;
- exact URL/source/visible identity agreement and no name/order/global-horse-number
  crosswalk;
- complete normal table parsing, exact row/horse/finish grammar, unique identities,
  exact mutual snapshot coverage, and zero result saves for every invalid case;
- positive terminality, exact capture timestamps/source, one result save only after
  complete validation, and unchanged repository exception propagation;
- no partial collection return or result write; unsupported special/unknown forms
  fail closed before save;
- result domain/repository round-trip plus c4g2a bounded result reading and c4g2b
  summary consumption without changing their contracts; and
- static proof of no prediction, bet planning, payout parsing, settlement arithmetic,
  database ownership, HTTP, fallback lookup, broad catch, or c4h3/c4h4 work.

## PREPARE scope and stop

Allowed changed files for this phase:

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

No pytest, live HTTP, trusted capture, database write, production implementation,
Python test change, schema/migration, or c4h3 work is authorized. Stop after the
docs-only review branch is published for independent architecture/evidence review.
