# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6d1d5f` — JRA target historical source boundary PREPARE.

Formal base: `776cd9123635eef3759284ff997a369857f3769e`.

Review branch: `review/4c-2d3b1i6d1d5f-jra-target-source-prepare`.

## Formal Findings

The existing neutral source schema already supports exactly the required target kinds: one `track`; and, per exact
external entry, one `entry`, `jockey`, and `odds_win`. The snapshot builder additionally requires exactly one
`past_race` or `past_race_absence` per entry. The completed JRA historical collector supplies only that downstream
past-evidence side and is unchanged.

Read-only official JRA inspection identifies `JRADB/accessD.html` as the race card / 出馬表 family. Its visible race
header provides candidate static track facts, while its displayed rows provide candidate horse number, jockey, and displayed
single-win odds. JRA describes the displayed single-win odds as nearly real time, so it is neither final odds nor a
historical fact that can be reconstructed later. This is structural investigation only; no official response was
captured, persisted, or copied.

Formal JRA code currently recognizes only accessS result, accessU horse-history, and accessO final-odds identities.
There is no accessD lexical identity parser, `JRAOfficialPageKind` member, canonical URL rule, supplied-response type,
archive schema family, live-capture authorization, or raw accessD row contract. Crucially, no formal evidence proves a
row-local accessD navigation to an exact accessU `jra:horse:<10 ASCII digits>` identity. Horse name, DOB, trainer,
pedigree, or display-text comparison must never substitute for this proof.

## Target Source Contract Status

```text
TARGET_SOURCE_PUBLIC_API = BLOCKED
TARGET_SOURCE_RESULT_DOMAIN = BLOCKED
ACCESSD_TO_ACCESSU_IDENTITY_STATUS = NOT_PROVEN
ACCESSD_STATIC_TRACK_FACTS = CONDITIONAL
TARGET_TRACK_CONDITION_SOURCE = NOT_PROVEN
COMPLETE_TARGET_TRACK_SOURCE = BLOCKED
SNAPSHOT_ASSEMBLY_READINESS = NOT_READY
```

No target-source public API or domain is approved yet. Returning a complete target-race tuple would require an exact
stable horse identity for every entry; returning a narrower target domain would still need that same identity before
the formal per-entry historical collector can be called. Creating either API before the accessD proof would create an
unapproved identity boundary.

## Frozen Candidate Evidence Roles (Not Yet an Implementation Contract)

If the predecessor proves one exact accessD supplied response family and its row-local accessU anchors, one response
may support four source roles without cross-page inference:

| Target kind | Candidate official source | Required future proof |
| --- | --- | --- |
| `track` | accessD race header plus separate condition evidence | accessD may provide only date/start/place/distance/surface/name/class; a causally eligible official track-condition source and exact race/time binding remain required; weather is optional and must not be invented |
| `entry` | accessD entry row | canonical positive horse number; exact row-local accessU anchor yielding the stable JRA horse identity; exact entry ID construction |
| `jockey` | same accessD entry row | exact direct jockey selector and row binding |
| `odds_win` | same accessD entry row | direct positive finite single-win odds selector, exact same horse number, and an observation no later than the prediction cutoff |

The response may be reused only with separate neutral evidence references whose roles are respectively `track`,
`entry`, `jockey`, and `odds_win`; each uses the exact raw-body SHA and actual observation. This is conditional design,
not permission to parse the current page loosely.

## Target Odds Temporal Policy

```text
TARGET_PREDICTION_ODDS != HISTORICAL_PAST_RACE_FINAL_ODDS
```

`TARGET_PREDICTION_ODDS` is a directly displayed target-race single-win value from evidence actually observed no later
than `information_cutoff` when the eventual snapshot is built. It is not accessO final odds for a historical past
race. It must never use final odds after the prediction cutoff, later page capture backdated to the target, a
latest/nearest reconstruction, settlement data, or a guessed publication time. `available_at` is `None` unless an
exact official availability time is separately established. The required causality chain remains:

```text
available_at (when proven) <= observed_at <= captured_at <= information_cutoff <= scheduled_start_at
```

```text
SOURCE_NORMALIZER =
  preserves exact observed_at;
  may enforce evidence no later than target scheduled_start_at where formally knowable;
  does not invent or backdate timestamps.

SNAPSHOT_BOUNDARY =
  owns final observed_at <= captured_at <= information_cutoff <= scheduled_start_at eligibility.
```

A target normalizer must not claim to reject prediction-cutoff-ineligible evidence unless a later approved API
explicitly receives `information_cutoff`. The snapshot builder remains the final owner of captured-at/cutoff
eligibility.

## Source Completeness and Order (Conditional)

After the prerequisite, a target normalizer must return one complete target-race tuple, not a partial target domain:

```text
(track, entry[horse_no ascending], jockey[matching entry], odds_win[matching entry])
```

It must reject missing, duplicate, mismatched, withdrawn/unsupported, unlinked, or scheduled-start-ineligible rows
where that boundary is formally knowable. It must call existing `validate_historical_input_source_record_set(...)`
exactly once after complete tuple construction;
it must not duplicate neutral validation. Per-entry historical collection remains a later assembly/orchestration
concern; snapshot construction is outside the target source boundary.

## Implementation Blockers and Recommended Predecessor

```text
IMPLEMENTATION_BLOCKERS =
  1. exact accessD canonical URL/race-identity grammar is absent;
  2. trusted accessD capture/supplied-response contract is absent;
  3. row-local accessD -> accessU stable-horse identity is NOT_PROVEN;
  4. causally available official target track_condition evidence and its exact race/time binding are NOT_PROVEN;
  5. exact target row/header/odds selectors and fail-closed unsupported states are not frozen.

RECOMMENDED_NEXT_PHASE =
  4C-2d3b1i6d1d5f1 — JRA accessD target identity/capture and track-condition PREPARE

NEXT_PHASE_ALLOWED_FILES =
  docs/CURRENT_PHASE.md
  docs/LATEST_CODEX_REPORT.md
```

The f1 PREPARE must inspect read-only official accessD structure and decide the exact accessD CNAME grammar, capture
family, target race identity cross-check, raw row-local accessU-link selector and parsing proof, direct target field
selectors, odds selector/time semantics, and cancellation/withdrawal handling. It must also identify the causally
available official target `track_condition` source and freeze its exact race/time binding. Both prerequisites are
required before any implementation phase.

Required future tests, after that contract is approved, include exact public API and no package export; URL/identity
and strict CP932 rejection; one complete target card; all target records and evidence roles; horse-no/entry-ID
coherence; direct accessD-to-accessU stable-horse proof; no name/DOB/trainer fallback; missing/duplicate/contradictory
rows; direct odds parsing and cutoff rejection; raw-SHA/timestamp/source-ID behavior; final neutral validation once;
snapshot input completeness; and no schema, migration, capture-family cross-contamination, bridge, or live network.

## Compatibility and Stop Condition

Source schema remains 4; snapshot schema remains 4; global migrations remain through 14; JRA capture migrations
remain `(1, 2)`. JRA historical discovery, absence projection, final-odds locator/capture, normalizer, collector, NAR,
provider-neutral source/snapshot, and package-root exports remain unchanged. `NAR_LINEAGE_TO_JRA_HORSE_ID_LINK` remains
`NOT_PROVEN`; no bridge, Predictor, live capture, archive, database, or schema work is approved.

Commit and push only this documentation PREPARE review. Stop for independent architecture review.
