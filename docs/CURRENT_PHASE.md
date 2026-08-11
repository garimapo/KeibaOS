# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase and Base

Phase 4C-2d3b1i6d1 — JRA trusted historical source architecture preparation.

Formal branch/base: feature/ver0.8-simulator at 7b4a0f5e28311c2d64685f6d3309f68556e67f8b.

Review branch: review/4c-2d3b1i6d1-prepare.

## Current JRA State

| Contract area | Authoritative status | Current repository finding |
| --- | --- | --- |
| CURRENT_JRA_FETCH_STATUS | PLACEHOLDER | scripts/fetch_jra.py returns a hard-coded Race; it makes no official request. |
| CURRENT_JRA_PARSER_STATUS | UNSUPPORTED | No JRA URL parser, supplied response, capture/archive, or historical normalizer exists. |
| CURRENT_JRA_OFFICIAL_SOURCE_STATUS | PARTIAL | Official JRA page families are reachable but have no trusted KeibaOS boundary. |
| CURRENT_JRA_EXTERNAL_IDENTITY_STATUS | PARTIAL | Official CNAME navigation exists, but no stable provider identity is proven. |
| CURRENT_JRA_HISTORICAL_SOURCE_STATUS | UNSUPPORTED | No causally eligible JRA past-race source record can be produced. |

Legacy scripts/fetch_races.py, scripts/database.py, scripts/parsers/horse_parser.py, and scripts/fetch_past_races.py use local IDs or legacy REAL values. They are forbidden as a JRA trusted-source fallback.

## Official Page Families and URL Findings

| Page family | Official path | Approved purpose |
| --- | --- | --- |
| accessD | /JRADB/accessD.html?CNAME=<opaque> | Target entry card only. Its recent four-race columns are RECENT_DISPLAY_CONTEXT. |
| accessS | /JRADB/accessS.html?CNAME=<opaque> | Historical race result. |
| accessU | /JRADB/accessU.html?CNAME=<opaque> | Horse information and race history. |
| accessO | /JRADB/accessO.html | Odds navigation family; historical per-horse odds are not proven. |

All four investigated families require HTTPS on www.jra.go.jp, exact approved path, one CNAME where that page family requires it, no credentials, fragment, foreign host, non-default port, plus sign, malformed percent escape, duplicate key, or unknown key. The sampled accessS response was identical for raw slash and uppercase %2F CNAME-delimiter spelling; a future URL canonicalizer may normalize only that delimiter to %2F after strict decoding. No CNAME component may otherwise be rewritten, decomposed, generated, case-folded, or inferred.

## Authoritative Identity Status

EXACT_CNAME_AS_STABLE_ENTITY_ID = REJECTED.
SAME_JRA_RACE_MULTIPLE_ACCESS_S_CNAME = INCONCLUSIVE.
SAME_JRA_HORSE_MULTIPLE_ACCESS_U_CNAME = INCONCLUSIVE.

ACCESS_S_CNAME_COMPONENTS = observed page-family prefix pw01sde; leading variant, digit run, and slash-hex suffix have unproven semantics.
ACCESS_U_CNAME_COMPONENTS = observed page-family prefix pw01dud; leading variant, digit run, and slash-hex suffix have unproven semantics.

JRA_STABLE_RACE_ID = NOT_PROVEN.
JRA_STABLE_HORSE_ID = NOT_PROVEN.
JRA_STABLE_ENTRY_ID = NOT_APPROVED.
JRA_PROVIDER_RECORD_ID = PROVISIONAL.

The accessS matched-row horse link is https://www.jra.go.jp/JRADB/accessU.html?CNAME=<accessU-CNAME>.
ACCESS_S_ROW_HORSE_LINK = OFFICIAL_ROW_TO_PROFILE_NAVIGATION_ONLY_NOT_STABLE_ID.

Same sampled routes retained one CNAME, but no independent navigation form established same-entity invariance. No final external race identity, external horse identity, external entry identity, or provider_record_id syntax is approved. A future entry identity may use {stable-external-race-id}:entry:{horseNo} only after stable race identity and separately proven horse identity exist.

## Horse-History Completeness

JRA_HORSE_HISTORY_PAGE = accessU.html?CNAME=<profile-CNAME>.
JRA_DOMESTIC_REGISTERED_HORSE_HISTORY_COMPLETENESS = PROVEN_FOR_CURRENT_PAGE_CONTENT.
JRA_FOREIGN_HORSE_HISTORY_COMPLETENESS = NOT_COMPLETE_ALL_HISTORY.
FOREIGN_HORSE_COMPLETE_HISTORY_POLICY = UNSUPPORTED_FAIL_CLOSED.
JRA_DEBATABLE_RECENT_COLUMNS_AS_COMPLETE_HISTORY = FORBIDDEN.

The accessU domestic-horse statement covers JRA, local, and overseas race-result history. This current-page completeness finding remains subject to trusted observed-at causality, future closed parser validation, and provider exceptions. Foreign horses are generally limited to their latest four starts and cannot satisfy ALL_CAUSALLY_AVAILABLE_ACTUAL_PRIOR_STARTS from accessU alone. A current accessU response captured after an old cutoff cannot recreate historical availability.

## Result Field Matrix and Reference-Time Blocker

| Field group | Authority/status |
| --- | --- |
| race facts; finish; race time; body weight/change; jockey; popularity; row-local passing order | accessS candidate authority, pending a later closed selector/grammar contract. Body weight is not assigned weight; jockey allowance symbols must remain meaningful. |
| race name and race class | Separate official title and condition/class nodes required; do not regex-split a combined heading. |
| odds | JRA_HISTORICAL_ODDS_AUTHORITY = NOT_PROVEN. accessS supplies popularity, accessU supplies result context, and tested accessO navigation reached current odds selection rather than historical per-horse odds. |
| fourth corner | JRA_FOURTH_CORNER_MAPPING = LAYOUT_DEPENDENT. Use row-local passing components only where the same page’s ordered labelled corner rows prove exact alignment and exactly one fourth corner. Otherwise unsupported. |
| abnormal states | normal start; recognized cancellation/exclusion non-start; recognized stopped/disqualified/demoted started-abnormal; unknown or ambiguous state fails closed. No state may be skipped. |

REFERENCE_TIME_DIFFERENCE_STATUS = FIELD_DOMAIN_CONTRACT_GAP.
HISTORICAL_PAST_RACE_DOMAIN_CHANGE_REQUIRED = YES.

AccessS exposes race times and textual margin, but no direct official Decimal reference-time difference. Textual margin conversion is forbidden, and race-time subtraction is not approved. The future d1a domain design must independently resolve the semantic field, including first-place behavior.

## Evidence, Capture, and Encoding Contract

MINIMUM_JRA_PAST_RACE_RESPONSE_SET = UNRESOLVED.
C1A_EVIDENCE_ROLE_EXTENSION_REQUIRED = UNRESOLVED.

The required official JRA response set is not yet proven, so no evidence-role extension is authorized.

JRA_ACCESS_D_CHARSET = CP932.
JRA_ACCESS_S_CHARSET = CP932.
JRA_ACCESS_U_CHARSET = CP932.
JRA_ACCESS_O_CHARSET = CP932.
JRA_CHARSET_POLICY = CP932_FOR_APPROVED_PAGE_FAMILIES.

Each probe had Content-Type text/html, HTML meta charset Shift_JIS, no Content-Encoding with explicit identity request, and strict CP932 decode. Response SHA-256 remains over exact supplied bytes before decoding or transcoding.

JRA_SUPPLIED_RESPONSE_DECISION = JRA_SPECIFIC.
CAPTURE_ARCHITECTURE_DECISION = JRA_SPECIFIC.
CAPTURE_DATABASE_DECISION = SEPARATE_JRA_CAPTURE_DATABASE.
JRA_CAPTURE_REUSE_OF_NAR_DOMAIN = FORBIDDEN.
JRA_AVAILABLE_AT_POLICY = None.
JRA_SOURCE_SYSTEM = jra_official.

Future capture must preserve requested_at <= observed_at <= stored_at. Historical eligibility is still observed_at <= information_cutoff. Live current bytes are not evidence for an old target cutoff. Initial pacing remains serialized single requests without retry or concurrency; no official numeric rate limit is invented.

## NAR-to-JRA Bridge Blockers

NAR_JRA_EVENT_TO_JRA_RESULT_RESOLUTION = NOT_PROVEN.
NAR_LINEAGE_TO_JRA_HORSE_ID_LINK = NOT_PROVEN.

A NAR HorseMark JRA row contains row-local date, display place, race number, and display/result fields, but no JRA accessS URL, CNAME, or JRA horse key. Horse-name, date/place-only, local-ID, and fuzzy linkage are forbidden.

JRA_TARGET_ODDS_HISTORICAL_BACKFILL_FROM_FINAL = FORBIDDEN.
ABILITY_REFERENCE_DATE_STATUS = FUTURE_LEAKAGE_BLOCKER_IN_CURRENT_PERSISTED_COMPOSITION.
JOCKEY_REFERENCE_DATE_STATUS = FUTURE_LEAKAGE_BLOCKER_IN_CURRENT_PERSISTED_COMPOSITION.
TIME_DIFFERENCE_TO_PREDICTION_ADAPTER_STATUS = NO_ADAPTER_CONTRACT_GAP.

## Recommended Next Phases

1. 4C-2d3b1i6d1a — historical time/reference comparison domain contract PREPARE: docs/CURRENT_PHASE.md and docs/LATEST_CODEX_REPORT.md only.
2. 4C-2d3b1i6d1b — JRA canonical race/horse identity plus NAR/JRA bridge PREPARE: docs/CURRENT_PHASE.md and docs/LATEST_CODEX_REPORT.md only.
3. 4C-2d3b1i6d1c — JRA supplied response and capture/archive design/implementation: scripts/simulation/jra_official_response_capture.py; scripts/simulation/jra_official_response_capture_migration.py; scripts/simulation/jra_official_response_capture_migration_runner.py; scripts/simulation/jra_official_response_live_capture.py; scripts/simulation/repositories/sqlite_jra_official_response_capture_repository.py; tests/test_jra_official_response_capture.py; tests/test_jra_official_response_capture_migration.py; tests/test_jra_official_response_live_capture.py; tests/test_sqlite_jra_official_response_capture_repository.py; and the two docs.
4. 4C-2d3b1i6d1d — JRA result/odds/history normalization: scripts/simulation/jra_historical_past_race_source.py; tests/test_jra_historical_past_race_source.py; approved authentic files under tests/fixtures/jra/; and the two docs.
5. Only after these approvals may mixed-history NAR collection be designed.

## Allowed Files

docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md

## Stop Condition

Stop after this docs-only correction commit and independent architecture re-review. Do not begin d1a, d1b, d1c, d1d, JRA production, capture, fixtures, acquisition, c1a changes, NAR changes, or mixed-history collection.
