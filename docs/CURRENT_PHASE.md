# Current Phase

## Phase

`POST_V0_8_DAILY_REPLAY_63`

## Title

Tracked Safe Root-Cause Diagnostic Support

## Status and outcome

- Status: `INTEGRATED_PENDING_REMOTE_VERIFICATION`.
- Design review: `PHASE63_DESIGN_REVIEW_PASS`.
- Implementation review: `PHASE63_IMPLEMENTATION_REVIEW_PASS`.
- Base HEAD / Phase62 integration commit: `0c4098b8f34905b14d1f53ea59a1d8c26d31203d`.
- Required dependency: `POST_V0_8_DAILY_REPLAY_62` is formally complete.
- Branch: `feature/post-v0.8-daily-replay`.
- Outcome: `IMPLEMENTED_TRACKED_SAFE_ROOT_CAUSE_DIAGNOSTICS`.
- Remote verification: `REQUIRED`.
- Phase63 observability support is implemented. No future live recovery diagnostics have been collected; no acquisition or publication is authorized.
- Provider HTTP: `0`; Phase44: not entered; acquisition authorization issued: `NO`.

## Immutable Phase57 evidence

Phase57 remains `POST_AUTHORIZATION_STOP` with `SOURCE_PROFILE_FIXTURE_BLOCKED` and authorization `PHASE57_ACQUISITION_AUTHORIZATION_CONSUMED_FAIL_CLOSED`. It cannot be restored, retried, reused, transferred, or authorize another Phase44 call.

- Target and semantics: `NAR / 21 / 2025-01-01 / 6`; `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`.
- Phase44 calls: `1`; GET attempts: `2`; Deba response returns: `1`; RaceList response returns: `1`; closed bundle and identity verification: present / `PASS`.
- Publication began: `NO`; rollback: `NOT_REQUIRED`; retry: `FORBIDDEN`.
- Safe-final run ID: `77ed0459fe004d0abc74739d023e8a10`; bytes: `11110`; SHA-256: `e4c14a18c73127232efbc6e6f36aab7a9e37cdb3ccd4361b3bcd906f29c9b46f`.

The existing safe evidence proves only Safety `UNSUPPORTED` with all five category outcomes `UNSUPPORTED` and finding counts `0`. The direct outer collapse classes are exactly strict UTF-8 decode failure, Profile-A strict HTML-structure `ValueError`, and BeautifulSoup `ParserRejectedMarkup`. Locally caught `urlsplit(...)` and strict `parse_qsl(...)` `ValueError`s create bounded local ambiguous evidence; they are not direct `_unsupported_safety()` causes.

Therefore `SAFETY_ROOT_CAUSE_NOT_IDENTIFIABLE_FROM_CURRENT_SAFE_EVIDENCE` and `CURRENT_SAFE_EVIDENCE_INSUFFICIENT_FOR_DIRECT_SAFETY_FIX` remain frozen. No known failing document or failure class is claimed.

Profile-B remains `BLOCKED`: `RACE_TABLE_SCOPE=PASS`, `UNIQUE_TARGET_6R=AMBIGUOUS` with `target_6r_row_count=2`, derived `DEBA_LINK_RELATIONSHIP=UNSUPPORTED` and `DEBA_LINK_QUERY_BINDING=UNSUPPORTED`, while `WITHDRAWAL_ROW_SHAPE=PASS` and `HORSE_14_WITHDRAWAL_ASSOCIATION=PASS`. The two Deba-link outcomes are downstream dependency results, not independent incompatibilities.

`PROFILE_B_ROOT_CAUSE_NOT_IDENTIFIABLE_FROM_CURRENT_SAFE_EVIDENCE` and `CURRENT_SAFE_EVIDENCE_INSUFFICIENT_FOR_DIRECT_PROFILE_B_GRAMMAR_FIX` remain frozen. There is no approved row selection, deduplication, or qualification relaxation.

`ADDITIONAL_SAFE_DIAGNOSTIC_CAPTURE_REQUIRED` remains true; implementation of diagnostic support does not identify the old raw documents' root causes.

## Implemented bounded recovery diagnostics

Phase63 adds one pure deterministic module, `scripts/simulation/nar_race_entry_status_source_profile_recovery_diagnostics.py`. It accepts exact in-memory bytes and a formal target, and has no network, clock, filesystem, database, subprocess, publication, environment, randomness, or Git responsibility. It produces immutable typed results and canonical bounded metadata only.

### Publication-Safety recovery diagnostics v1

Schema: `nar-race-entry-status-publication-safety-recovery-diagnostics`; schema version: exact integer `1`. Its ordered exact document roles are `deba_table`, then `race_list`. Every role result has only:

- `document_role`: one of those exact roles;
- `utf8_decode`: `PASS` or `FAIL`;
- `strict_structure`: `PASS`, `FAIL`, or `NOT_REACHED`;
- `beautifulsoup_parse`: `PASS`, `FAIL`, or `NOT_REACHED`.

The function `diagnose_nar_race_entry_status_publication_safety_recovery` uses the same authorities as Safety: `bytes.decode("utf-8", errors="strict")`, Phase56/Profile-A `_validate_html_structure`, and `BeautifulSoup(source, "html.parser")`. It maps only `UnicodeDecodeError` at decode, `ValueError` at strict structure, and `ParserRejectedMarkup` at BeautifulSoup. Unexpected errors produce a fixed validation error without original exception text or context; no stage outcome is invented. The exact top-level canonical keys are `schema`, `schema_version`, and `document_results`.

Exact valid stage combinations are:

1. decode `FAIL` → strict structure `NOT_REACHED` → BeautifulSoup `NOT_REACHED`;
2. decode `PASS`, strict structure `FAIL` → BeautifulSoup `NOT_REACHED`;
3. decode `PASS`, strict structure `PASS` → BeautifulSoup exactly `PASS` or `FAIL`.

All other combinations are rejected. This records parser-stage reachability only; it does not return Safety `SAFE`, `UNSAFE`, `AMBIGUOUS`, or `UNSUPPORTED`, and does not replace Phase56 Safety.

### Profile-B recovery diagnostics v1

Schema: `nar-race-entry-status-profile-b-recovery-diagnostics`; schema version: exact integer `1`. It uses the current Profile-B target discovery boundary without selecting a row: `section.raceTable`, `tr.data`, direct `td` cells, and the first direct cell normalized exactly to `{race_no}R`.

The function `diagnose_nar_race_entry_status_profile_b_recovery` returns exact top-level keys `schema`, `schema_version`, `target`, `race_table_scope_count`, `target_candidate_count`, `candidate_details_complete`, `candidate_results`, and `all_candidate_safe_projections_equal`. Target keys are exactly `baba_code`, `race_date`, and `race_no`. The equality field is `false` for zero candidates, `true` for one complete candidate, compares all approved projections excluding ordinal for two or more complete candidates, and is `false` whenever details are incomplete. No provider text participates in the comparison.

Each deterministic DOM-order candidate result has exactly:

- `candidate_ordinal` (one-based, contiguous);
- `direct_cell_count`;
- `anchor_count`;
- `deba_path_link_count`;
- `deba_href_unsupported_count`;
- `canonical_target_query_match_count`;
- `canonical_query_unsupported_count`;
- `canonical_target_query_match`.

All counts are exact nonnegative integers bounded by `10000`; all booleans are exact bools. The only source constant inspected is `/KeibaWeb/TodayRaceInfo/DebaTable`. A candidate increments `deba_href_unsupported_count` for an anchor with an `href` attribute whose value is not exact `str`, or whose `urlparse` raises `TypeError` or `ValueError`. Missing `href` and a parseable non-Deba path do not increment it. A parseable exact-Deba-path link increments `deba_path_link_count`; only then can strict `parse_qs(..., strict_parsing=True)` failure increment `canonical_query_unsupported_count`.

For parseable exact-Deba-path links, strict `parse_qs` uses `keep_blank_values=True` and `strict_parsing=True`. A canonical query is exactly the mapping `k_babaCode=[target.baba_code]`, `k_raceDate=[target.race_date.strftime("%Y/%m/%d")]`, and `k_raceNo=[str(target.race_no)]`. Only its count and the boolean are retained. As explicitly specified by EXECUTE, `canonical_target_query_match` is exactly `canonical_target_query_match_count >= 1`. Non-string href or URL-parse `TypeError/ValueError` increments only the href unsupported count; strict-query `TypeError/ValueError` increments only the exact Deba-path query unsupported count.

`MAX_RETAINED_CANDIDATE_DETAILS` is exactly `8`. With one race-table scope and `0..8` candidates, details are complete and retain every candidate. With `9..10000` candidates, `candidate_details_complete=false`, `candidate_results=[]`, and `all_candidate_safe_projections_equal=false`; no prefix is silently retained. The PREPARE-frozen unavailable-discovery representation is retained for decoding/parser rejection or a nonunique scope: target count zero, incomplete details, empty results, and equality false. It does not assert that unavailable rows were absent. Counts above `10000` fail closed; formal provider codes are also limited to `512` UTF-8 bytes and target race numbers to `10000`.

No row text, horse name, anchor text, href, host, scheme, fragment, arbitrary path, query text, class, raw HTML, source snippet, exception text, selected candidate, preferred candidate, canonical candidate, or deduplicated candidate appears in the result. The recovery diagnostic cannot change ordinary Profile-B output.

### Canonical form

Both result families are frozen dataclasses with exact field/key allowlists, exact enum/type validation, tuple ordering, and canonical UTF-8 bytes from `json.dumps(..., ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)`. They expose only canonical dictionaries and canonical bytes. No free-form provider-derived string is accepted or emitted.

## Implemented durable Phase50 support

Two typed milestones are required; existing fields are not overloaded:

| Milestone | Exact detail keys |
| --- | --- |
| `PROFILE_B_RECOVERY_DIAGNOSTICS_RETAINED` | `{"profile_b_recovery_diagnostics"}` |
| `PUBLICATION_SAFETY_RECOVERY_DIAGNOSTICS_RETAINED` | `{"publication_safety_recovery_diagnostics"}` |

The exact new order is:

`RACELIST_CAPTURE_METADATA_RETAINED` → `PROFILE_B_DIAGNOSTICS_RETAINED` → `PROFILE_B_RECOVERY_DIAGNOSTICS_RETAINED` → `IDENTITY_VERIFICATION_PASS` → `PUBLICATION_SAFETY_RECOVERY_DIAGNOSTICS_RETAINED` → (`PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED` or `SAFETY_PASS`) → all existing later milestones in their present relative order.

Safety recovery diagnostics are always emitted before the normal Safety branch during a future diagnostic run. Both recovery events use normal append → flush → fsync durability before any transient raw cleanup. Phase50 validates exact detail keys, nested schema/version, enum values, field keys, bool/int types, `0..10000` bounds, candidate ordinal continuity, count/detail consistency, the Safety stage invariants, canonical serialization, and the `4096`-byte record limit. Raw bytes are rejected as journal detail values.

`JOURNAL_SCHEMA_VERSION` remains exact `1`: this is additive optional milestone support with no change to record top-level schema, existing event names, existing detail keys, or their relative ordering. The new reader accepts historical journals that omit the new records, including the valid Phase57 blocked journal; there is no migration, rewrite, or new-event requirement for historical evidence. Adding the milestones preserves the rank of every existing milestone relative to every other existing milestone.

No completion vocabulary changes. A future diagnostic run uses `SOURCE_PROFILE_FIXTURE_BLOCKED` for an unchanged Safety/Profile-B qualification block and `RECOVERY_PREFLIGHT_BLOCKED` for pre-live, acquisition-integrity, or recovery failure. `CONTROLLED_REACQUISITION_FOR_SAFE_ROOT_CAUSE_DIAGNOSTICS` is a future project objective only—not a Phase50 outcome, authorization, or publication authority.

## Future run and raw cleanup contract

After Phase63 is formally complete, a later phase may separately PREPARE, review, and APPROVE one new Phase44-only diagnostic reacquisition for this unchanged target. It must retain normal capture metadata and Profile-B diagnostics, then Profile-B recovery diagnostics, verify identity, retain Safety recovery diagnostics, run normal Phase56 Safety, retain the normal blocked/pass result, and stop fail-closed under unchanged qualification semantics. It has no automatic publication requirement.

Transient raw bytes must be destroyed only after both recovery results, all normal safe evidence, and parent validation are durably retained. The previous raw bytes cannot be reconstructed from hashes, diagnostics, or internet guesses.

`NO_ADDITIONAL_TRACKED_SAFE_EVIDENCE_ARTIFACT_REQUIRED` is chosen. The Phase62 tracked documents already preserve the immutable run ID, safe-final fingerprint, target, authorization and transport facts, capture metadata, Profile-B and Safety facts, outcome, and evidence limits. The OS-temp safe-final file is not project storage and no seventh implementation path is justified.

## Exact implementation boundary and verification

The exact six changed paths are:

1. `scripts/simulation/nar_race_entry_status_source_profile_recovery_diagnostics.py`
2. `tests/test_nar_race_entry_status_source_profile_recovery_diagnostics.py`
3. `scripts/simulation/nar_race_entry_status_reacquisition_observability.py`
4. `tests/test_nar_race_entry_status_reacquisition_observability.py`
5. `docs/CURRENT_PHASE.md`
6. `docs/LATEST_CODEX_REPORT.md`

Phase44 change required: `NO`; Phase53 ordinary semantics changed: `NO`; Phase56 semantics changed: `NO`; Phase60/61 changed: `NO`. No fixture, `.gitattributes`, database, or logs path is in scope.

Focused tests must cover valid and per-role failed Safety stages; impossible stage states; deterministic/no-exception-text canonical bytes; zero/one/two/overflow target candidates; deterministic candidate DOM order; each safe candidate count/boolean; malformed or non-string href/query bounded counters; no retained URL/query; candidate ordinal and count consistency; and ordinary Profile-B invariance.

Phase50 tests must cover both events, exact detail keys, malformed nested schemas, invalid Safety stage combinations, candidate mismatch, oversized records, ordering, old journals without recovery events, the historical Phase57 blocked journal, preflight, unchanged Phase58/59/61 behavior, and unchanged `LIVE_PROCESS_COMPLETE` vocabulary. Static audit proves the new module has no HTTP, socket, filesystem, subprocess, database, clock, randomness, environment, or Git operation.

## Implemented verification results and stop condition

- Recovery focused command: `python -m pytest -q tests/test_nar_race_entry_status_source_profile_recovery_diagnostics.py`: `80 passed`.
- Phase50 focused command: `python -m pytest -q tests/test_nar_race_entry_status_reacquisition_observability.py`: `262 passed`.
- Relevant NAR command: `python -m pytest -q tests/test_nar_race_entry_status_source_profile_recovery_diagnostics.py tests/test_nar_race_entry_status_reacquisition_observability.py tests/test_nar_race_entry_status_source_profile_diagnostics.py tests/test_nar_race_entry_status_source_profile_profile_a.py tests/test_nar_race_entry_status_source_profile_publication_contract.py tests/test_nar_race_entry_status_source_profile_publication_plan.py`: `440 passed`.
- Final full-suite command: `python -m pytest -q`: `4041 passed, 2841 subtests passed`; failed: `0`.
- Full suite ran initially once (`4038 passed, 2841 subtests passed`), then once after three narrowly added tests exposed unexpected-exception text propagation. Fixed diagnostic errors suppress original exception context; focused/relevant tests and the final full suite pass.
- Maximal recovery JSONL measurements including LF: Profile-B `3177` bytes; Safety `677` bytes. The tests use eight candidate records at count bound `10000`, a `512`-byte provider code, race number `10000`, canonical date, and sequence `131072`. `MAX_RECORD_BYTES=4096` remains unchanged.
- ParserRejectedMarkup branches are tested by controlled parser substitution and bounded typed-state validation. No natural input inducing this stage rejection after the strict structure gate was established; there is no claim that the old provider bytes had that failure.
- Static AST/import and added-diff audit: `PASS`; no provider HTTP or acquisition call was added. Exact nested validation and the existing durable writer are used; the writer itself is unchanged.
- Phase44/53/56/60 files and `.gitattributes` are unchanged. Phase58/59 Safety-blocked/identity semantics, Phase61 dedicated-test path compatibility, bounds, outcomes, and token are unchanged and covered by passing Phase50 tests.
- Staged: empty; untracked: only the approved new module and its test. No new pyc/cache files were created. `git diff --check`: `PASS`.

Stop at `INTEGRATED_PENDING_REMOTE_VERIFICATION`. Remote verification is required; do not mark the phase formally complete, prepare a new acquisition, acquire, or issue authorization.

## Persistent constraints

- Phase54: `PHASE54_AUTHORIZATION_UNCONSUMED_BUT_UNUSABLE_FOR_V2`.
- Phase41: `DESIGN_BLOCKED`.
- `market_eligibility`, `positive_market_eligibility`, and `WHOLE_MEETING_CANCELLATION`: `UNSUPPORTED`.
- Open: `COMBINATION_EV_REQUIRES_MARKET_ODDS_CAPTURE`; `NAR_MARKET_ELIGIBILITY_REQUIRES_INDEPENDENT_ENTRY_STATUS_CAPTURE`.

## Next permitted action

`INDEPENDENT_REMOTE_VERIFICATION`.
