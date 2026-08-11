# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6c1d3b2c0` — historical prediction/source window contract preparation.

Formal base: `93fad49e7b188e3b4492cc7fe0eb61d36d16b735`.

Formal branch: `feature/ver0.8-simulator`.

Preparation review branch: `review/4c-2d3b1i6c1d3b2c0-prepare`.

Approved parent preparation context: `8f918c8081a2e261e9cfd0d9db435fab6ca84616`.

## Decision: Source Retention Is Not a Model Window

The two policies are distinct and provider-neutral:

```text
SOURCE_ACQUISITION_HISTORY_POLICY = ALL_CAUSALLY_AVAILABLE_ACTUAL_PRIOR_STARTS
PREDICTION_HISTORY_WINDOW_POLICY = SEPARATELY_CONFIGURABLE
INITIAL_PREDICTION_WINDOW_DEFAULT = ALL_AVAILABLE
SNAPSHOT_HISTORY_CONTENT = ALL_ACQUIRED_CAUSALLY_ELIGIBLE_HISTORY
COLLECTOR_MAY_SILENTLY_CHANGE_MODEL_HISTORY_WINDOW = NO
```

Source acquisition determines which complete official historical starts are captured and archived before the target
cutoff. Prediction filtering determines what an already archived immutable snapshot supplies to a particular model
run. The collector therefore does not derive a cap from the JockeyEngine's five-race *recent-score* component.

The preferred source policy preserves all complete, causally eligible actual-start evidence because a shallow archive
cannot be repaired later for an old target:

```text
ARCHIVE_HISTORY_TOO_SHALLOW = IRREVERSIBLE_FOR_OLD_CUTOFF
```

If only five starts were captured by cutoff T, later observations of starts six through ten have
`observed_at > T` and are ineligible for that old prediction. In contrast, all-history snapshots can later support
all, recent-5, recent-10, recent-20, time-bounded, or future explicitly designed selections without source reacquisition.

`RECENT_N_ACTUAL_PRIOR_STARTS` remains a valid future *prediction* policy, but N must be intentional configuration,
not NAR page size, UI convenience, or `JockeyEngine.RECENT_RACE_LIMIT`. Candidate N values 5/10/20 respectively retain
only their newest 5/10/20 starts; each loses older historical experimentation permanently if also used as acquisition.
A larger acquisition window plus a smaller configurable model window is better than a shallow matching window, but
is still irreversible for omitted starts. All causal acquisition has greater request/archive volume, exposes JRA and
unsupported results earlier, and takes longer; those costs do not justify silently making it a model policy.

## Existing Prediction Behavior and Reproducibility

Repository inspection confirms:

```text
AbilityEngine: evaluates every supplied eligible PastRaceInput in its weighted ability evaluation.
PaceEngine: uses every supplied PastRaceInput with usable passing/corner data.
JockeyEngine: rates/confidence use all eligible same-jockey races;
              only recent_score sorts and takes five.
```

The immutable historical snapshot has no history-count cap and its content digest includes all past-race rows, so
storing the acquisition corpus conflicts with no snapshot identity rule. Snapshot content SHA must remain a data
identity: the same complete snapshot plus two different prediction-window configurations produces different model
results, not different snapshot content.

Prediction-window configuration therefore belongs to a later provider-neutral prediction/simulation configuration
contract, included in its deterministic run/model configuration identity or hash. It is not mutable runtime state,
source-record payload, or snapshot digest. The initial `ALL_AVAILABLE` default preserves current Ability/Pace/Jockey
all-supplied-history behavior and avoids a hidden five-race change.

## Actual-Start and Completeness Semantics

History identity selection is always across organizations before provider filtering:

```text
ACTUAL_START_WINDOW_ACROSS_ORGANIZATIONS = YES
PROVIDER_FILTER_BEFORE_HISTORY_SELECTION = FORBIDDEN
```

The parent taxonomy is retained:

| Event | Meaning | Window/completion outcome |
| --- | --- | --- |
| NAR actual start | Official NAR RaceMarkTable identity and started outcome | Must be captured and normalized. |
| JRA actual start | Row-local official JRA history representation | Counts; required evidence is not yet supported. |
| Unsupported actual start | A started result outside d3b2a's normal completed envelope | Counts; fail closed, never replace with older history. |
| Proven non-start | Exact row-local official cancellation/exclusion semantics (`取消`, `除外`, `競走除外`) | Does not consume a start position, but is structurally validated. |
| Started abnormal outcome | Official started state such as `中止`, `失格`, or `降着` | Counts as unsupported actual start. |

The classifier must use exact row/result-link behavior, not labels alone, page-global text, jockey affiliation, horse
name, or table position. No start may be skipped to obtain an older NAR result.

```text
JRA_ACTUAL_START_POLICY = REQUIRED_EVIDENCE_NOT_YET_SUPPORTED
```

Under all-history acquisition, a mixed NAR/JRA horse cannot yield a complete NAR-only source-record collection until
JRA historical normalization/capture exists. There is no placeholder past-race record and no partial collection return.

Definitions:

```text
SOURCE_HISTORY_COMPLETE = the selected acquisition policy's entire actual-start sequence is proven complete,
                          every selected start has causally eligible official evidence, and every start is represented
                          by a validated supported source record; or a complete zero sequence has one valid absence.

PREDICTION_HISTORY_COMPLETE = every actual start selected by an explicit prediction-window configuration is present
                              in the immutable source snapshot and has a valid approved prediction-input adapter.
```

For the all-history source policy, any JRA or unsupported actual start makes the NAR-only source collection incomplete
and fails closed. A prediction window cannot be used to hide missing selected history.

## HorseMarkInfo Completeness Decision

The parent official structural investigation found four HorseMarkInfo/RaceHorseInfo count matches:

```text
30074407776: 34 HorseMark rows / 34 RaceHorseInfo lifetime total (mixed NAR/JRA)
30039401296: 14 / 14 (current NAR)
30036406666: 39 / 39 (mixed NAR/JRA)
30038401876: 36 / 36 (NAR)
```

The inspected HorseMarkInfo pages each had the expected unique history table, descending dates, and no visible
continuation control. Their official HorseMarkInfo navigation points to:

```text
/KeibaWeb/DataRoom/RaceHorseInfo?k_lineageLoginCode=<same lineage>&k_activeCode=1
```

RaceHorseInfo exposes a `着別回数` `生涯`/`合計` lifetime total. This is a usable representative cross-check, but
the evidence does not yet establish a universal zero/short-history proof: no verified fewer-than-five or debut/zero
case was obtained, and provider-wide continuation/row-limit semantics are not proven.

The c0 recommendation is therefore:

```text
HORSE_MARK_COMPLETE_ACTUAL_START_SOURCE = UNRESOLVED
RACE_HORSE_INFO_COMPLETENESS_SIGNAL = USABLE_REPRESENTATIVE_CROSSCHECK_ONLY
RACE_HORSE_INFO_RUNTIME_REQUIRED = UNRESOLVED
RACE_HORSE_INFO_EXTENSION_REQUIRED = NO_AT_THIS_TIME
ZERO_HISTORY_PROOF_AVAILABLE = NO
SHORT_HISTORY_PROOF_AVAILABLE = NO
```

This is recommendation C: further official completeness investigation is required before committing to either
HorseMarkInfo-only proof or runtime RaceHorseInfo cross-check. c1 remains blocked for zero/short/all-history
completeness. If runtime RaceHorseInfo is later required, it needs a separate approved extension to the closed capture
page vocabulary, URL canonicalization, SQLite page-kind CHECK/migration, live-capture verification, and c1a absence
evidence semantics. One HorseMarkInfo evidence reference cannot silently audit a RaceHorseInfo-dependent decision.

Once completeness conditions are approved, c1 discovery returns the complete ordered actual-start identity sequence;
it does not select a convenient N or embed prediction-window policy in HTML parsing. Under the selected all-history
source policy, c2 captures every supported identified actual start and fails closed if any required JRA or unsupported
actual start prevents a complete source set.

## Request, Archive, and Reuse Consequences

For one target race with 12 entries, request count is:

```text
1 DebaTable + 12 HorseMarkInfo + D unique RaceMarkTable pages
```

where `D` is deduplicated across all selected starts and is at most the total selected starts. Illustrative no-sharing
upper bounds are 73 requests at five starts per horse, 133 at ten, and 253 at twenty. All-history volume depends on
each horse's actual career history; shared historical races reduce RaceMarkTable requests. These are planning bounds,
not provider rate-limit claims.

```text
ARCHIVE_VOLUME_DEPENDS_ON_HISTORY_POLICY = YES
CROSS_COLLECTION_CAPTURE_REUSE_POLICY = DEFERRED_FUTURE_OPTIMIZATION
MUTABLE_HORSEMARK_REUSE_POLICY = FRESH_CAPTURE_PREFERRED
RACEMARK_REUSE_POLICY = FRESH_CAPTURE_PREFERRED_INITIAL_CORRECTNESS
```

Initial c2 should fresh-capture/archive every required response. A same HorseMarkInfo URL must never be reused merely
because it exists: later history may be appended and an older capture may be insufficient for the target-date
requirement. A later reuse design may use an older exact archived RaceMarkTable response only after proving valid
archive identity and `observed_at <= target cutoff`; it must not assume provider immutability. This is different from
impermissible retroactive backfill.

## Current Downstream Integration Gaps

`AbilityEngine` and `JockeyEngine` accept an optional `reference_date` but default to `date.today()`. The current
persisted simulation application injects its request-document `track_reference_date` only into `TrackEngine`; it does
not construct AbilityEngine/JockeyEngine with the historical target date. No historical snapshot-to-prediction
composition path currently supplies those engines deterministically.

```text
ABILITY_REFERENCE_DATE_STATUS = FUTURE_LEAKAGE_BLOCKER_IN_CURRENT_PERSISTED_COMPOSITION
JOCKEY_REFERENCE_DATE_STATUS = FUTURE_LEAKAGE_BLOCKER_IN_CURRENT_PERSISTED_COMPOSITION
```

The snapshot domain stores exact Decimal `reference_time_difference_seconds`, while current `PastRaceInput` and
AbilityEngine require legacy float `margin`; AbilityEngine scores that margin and accepts only positive values. There
is no snapshot-to-PastRaceInput adapter. `reference_time_difference_seconds` must not be silently converted into
margin.

```text
TIME_DIFFERENCE_TO_PREDICTION_ADAPTER_STATUS = NO_ADAPTER_CONTRACT_GAP
```

The later main-identity/snapshot-to-prediction design must explicitly own date injection, provider-neutral window
selection, prediction-config identity, and any independently approved time-difference model/adapter decision. None
belongs in source collection.

## Updated Roadmap

```text
1. Further official completeness investigation / decide HorseMarkInfo-only versus RaceHorseInfo extension.
2. If RaceHorseInfo is required: separate trusted-capture and c1a evidence architecture preparation/approval.
3. d3b2c1: pure complete actual-start discovery, only after completeness conditions are approved.
4. JRA historical capture/normalization prerequisite, before all-history mixed-horse collection.
5. d3b2c2: injected NAR one-race collector, returning only complete all-history source sets.
6. d3b2c3: capture database/live collector composition only.
7. d3b2d: main identity mapping, snapshot composition, and separately approved prediction-input/window integration.
```

```text
JRA_HISTORICAL_SUPPORT_ROADMAP_IMPACT = REQUIRED_BEFORE_COMPLETE_ALL_HISTORY_MIXED_HORSE_COLLECTION
```

Architecture blockers:

```text
HORSEMARK_COMPLETE_ACTUAL_START_SOURCE_UNRESOLVED
ZERO_AND_SHORT_HISTORY_PROOF_UNRESOLVED
JRA_HISTORICAL_SOURCE_SUPPORT_REQUIRED_FOR_MIXED_ALL_HISTORY
PREDICTION_WINDOW_CONFIGURATION_AND_IDENTITY_NOT_DESIGNED
HISTORICAL_REFERENCE_DATE_INJECTION_NOT_DESIGNED
TIME_DIFFERENCE_TO_PREDICTION_ADAPTER_NOT_DESIGNED
```

Operational limitation only: trusted evidence for historical replay exists only where official response bytes were
observed before the historical cutoff; later live observations cannot repair the old corpus.

## PREPARE Scope and Stop Condition

Only `docs/CURRENT_PHASE.md` and `docs/LATEST_CODEX_REPORT.md` may change. No production/test/fixture/capture/DB/
migration work is authorized. Stop after this one docs-only review commit and independent architecture review; do not
implement c1/c2/c3/d.
