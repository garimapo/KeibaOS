# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6d1d5b1` — JRA accessU complete-history eligibility / source investigation PREPARE.

Formal base: `367602e64353244e27b1518014c0907b922fb4ae`.

Approved d1d5b PREPARE: `be0941a3fef1ea8c0d652464de584a7d6350ff23`.

Review branch: `review/4c-2d3b1i6d1d5b1-jra-history-eligibility-prepare`.

This is design and read-only official-source investigation only. It changes no production code, test, fixture, capture,
archive, repository, schema, migration, normalizer, discovery module, or package-root export.

## Official Facts Investigated

The accessU `出走レース` explanatory text says:

```text
JRA、地方、海外で出走したすべてのレースの成績となります。
なお、外国馬は原則として直近の過去４走のみの掲載となります。
```

That establishes the displayed-history scope and the foreign-horse latest-four exception, but it does not define
`外国馬` on the response or associate the exception with a row-local/profile-local status field.

Official JRA rule material independently distinguishes concepts that must not be collapsed:

```text
外国産馬 / （外） = foreign-bred horse category
カク外             = horse managed by a foreign trainer for an international exchange race
```

The rule material therefore proves that foreign-bred status and foreign-managed horse status are distinct official
concepts. It does **not** prove which, if either, is the exact `外国馬` category used by the accessU latest-four notice.
`外国産馬`, `（外）`, overseas starts, foreign birth place, pedigree, and a foreign trainer/owner are consequently not
eligibility proofs for this contract.

Read-only accessU inspection of both a populated profile and an exact `出走レース` no-data response found only ordinary
profile facts (parentage, sex, age, trainer, date of birth, breeding farm, and place of production). It found no direct
`外国馬` classification, no exhaustive non-foreign marker, and no response-local registration/affiliation field tied by
official semantics to the latest-four exception. Absence of those markers is not proof.

The no-data response has `div.race_detail` headed `出走レース` with a `div.caution.no_data` message
`該当するデータがありません`. This proves only that the response displays no applicable history data; it does not
state that the horse has never had an actual start or override the response's history-scope/update limitations.

## Eligibility Decision

```text
FOREIGN_HORSE_EXCEPTION =
  accessU states a latest-four exception for 外国馬, but its exact membership
  semantics are not defined on the page or bound to a supplied response field.

FOREIGN_HORSE_VS_FOREIGN_BRED =
  DISTINCT_OFFICIAL_CONCEPTS; accessU exception mapping is NOT_PROVEN.

ACCESS_U_ELIGIBILITY_MARKER = NONE_PROVEN
TARGET_SOURCE_ELIGIBILITY_MARKER = NONE_PROVEN
ACCESS_U_COMPLETE_HISTORY_ELIGIBILITY = NOT_PROVEN
```

Existing JRA target-entry records contain the external race ID, entry ID, stable ten-digit horse identity, and target
horse number. They contain no approved foreign-horse eligibility fact. The formal JRA trusted capture contract covers
accessS/accessU and accessO; it has no accessD target-card capture/identity contract. Read-only accessD inspection did
not establish a direct target-row field with official semantics proving that the target is outside the accessU
exception. In particular, a race-card `（外）`-style symbol, if present, would describe the distinct foreign-bred rule
category and cannot be used as a substitute.

An eligibility status could be affiliation/registration-sensitive rather than an immutable birth fact; the exact
accessU term is not defined sufficiently to freeze its time behavior. Therefore any future qualifying evidence must
be captured as an exact official response at or before the target cutoff. A current page may establish parser structure
only; it cannot prove eligibility for a historical target retrospectively.

```text
ELIGIBILITY_CAUSALITY =
  Any future direct classification must be contained in trusted evidence with
  observed_at <= target scheduled_start_at. No backdating, current-page inference,
  or unrecorded status reconstruction is allowed.
```

## Alternative Source Investigation

No alternative official JRA complete-history source was proven that simultaneously provides all of:

```text
official JRA ownership
stable mapping to jra:horse:<10 digits>
complete JRA/local/overseas history without the accessU exception
documented pagination/continuation semantics
causally capturable supplied bytes
```

The public race-by-race accessS result pages are exact results once a race is already known; they are not a
stable-horse complete-history index. They cannot be searched/scanned to fill omitted accessU history without
discovery/orchestration or a provider identity bridge. No third-party source is eligible.

```text
ALTERNATIVE_OFFICIAL_COMPLETE_SOURCE = NONE_PROVEN
ZERO_HISTORY_PROOF = NOT_PROVEN
ALL_PRIOR_STARTS_POLICY = BLOCKED_FOR_UNCONSTRAINED_JRA_TARGET
DISCOVERY_IMPLEMENTATION_READY = NO
```

## Frozen Consequences

Do not implement `discover_jra_historical_past_race_history` from one accessU response. It would claim
`ALL_CAUSALLY_AVAILABLE_ACTUAL_PRIOR_STARTS` without a valid universal completeness proof. Do not instead return the
latest displayed events under a misleading complete-history name, add a target-entry field speculatively, or use a
multi-response tuple of the same truncated source as a workaround.

The existing d1d5a normalizer, accessO no-synthesis rule, JRA capture/archive/live stack, NAR production, and neutral
evidence/source/snapshot stack remain unchanged. `NAR_LINEAGE_TO_JRA_HORSE_ID_LINK = NOT_PROVEN` and
`MIXED_HISTORY_COLLECTION_READY = NO` remain frozen. Source schema remains 4, snapshot schema remains 4, global
migrations remain through 14, and JRA capture migrations remain `(1,2)`.

```text
ARCHITECTURE_BLOCKERS =
  1. No direct, exhaustive, response-local accessU marker proves exemption from
     the foreign-horse latest-four exception.
  2. No proven target-race source fact carries that eligibility with approved
     capture/identity/causality semantics.
  3. No alternative official complete stable-horse history source is proven.
```

The recommended next phase is not implementation. It is `4C-2d3b1i6d1d5b2 — JRA foreign-horse exception official
semantics / source-capability escalation PREPARE`, documentation only, requiring an authoritative JRA source that
defines the accessU exception and exposes a causally capturable, exhaustive eligibility/completeness fact. If none is
available, the JRA complete-history feature remains intentionally unavailable.

```text
NEXT_PHASE_ALLOWED_FILES =
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Stop Condition

Stop for independent review. Do not implement discovery or eligibility parsing, mutate/archive a response, perform a
real trusted capture, add fixtures, change target acquisition, begin orchestration, connect Predictor, or begin a
NAR/JRA bridge.
