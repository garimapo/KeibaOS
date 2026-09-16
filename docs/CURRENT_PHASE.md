# Current Phase

## Phase

`POST_V0_8_DAILY_REPLAY_57`

## Revision

`PHASE57_REPREPARE_AFTER_PHASE58_PHASE59`

## Title

Controlled NAR Source-Profile v2 Reacquisition and Publication

## Status

`DRAFT_FOR_REVIEW`

## Outcome

`DESIGN_BLOCKED_PHASE57_PUBLICATION_MANIFEST_AUTHORITY_UNAVAILABLE`

## Execution state

- Phase57 execution state: `DESIGN_BLOCKED`.
- Tracked blocker: `PHASE57_PUBLICATION_MANIFEST_AUTHORITY_UNAVAILABLE`.
- Next required support: `POST_V0_8_DAILY_REPLAY_60`, a new reviewed tracked publication-plan and binary-preservation authority phase.
- Next action after this docs-only integration: Phase60 PREPARE only after independent remote verification.
- Phase57 is not formally complete, authorized, ready for execution, or ready for live work.

## Git and predecessor basis

- Authorized worktree: `C:\Users\garim\Desktop\KeibaOS-post-v0.8`
- Branch: `feature/post-v0.8-daily-replay`
- Base/local/remote HEAD: `4de9849e87538bf1d6b83cdaba48430d2993885a`
- The required Phase56, Phase58, and Phase59 `FORMALLY_COMPLETE` states are accepted as the current user-supplied phase-state authority for this re-PREPARE.
- Their prior in-tree reports remain historical integration reports and must not be treated as a substitute for the current user-supplied formal-completion declaration.

## Authorization and target

- Phase54: `PHASE54_AUTHORIZATION_UNCONSUMED_BUT_UNUSABLE_FOR_V2`; it must never be reused.
- Phase57 at PREPARE entry: `PHASE57_ACQUISITION_AUTHORIZATION_NOT_YET_ISSUED`.
- No Phase57 authorization is issued or consumed by this PREPARE.
- Frozen future target: provider `NAR`; `baba_code=21`; `race_date=2025-01-01`; `race_no=6`.
- Frozen Phase44-only collection order: `DebaTable` then `RaceList`; maximum provider GET attempts: `2`; no retry, fallback, discovery, alternate target/provider, partial return, or second Phase44 attempt.
- Future evidence is `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`; it establishes neither historical bytes/availability/cutoff nor historical market eligibility or backdated response time.

## Reconfirmed integrated authorities

### Phase58 durability

Phase50 contains the additive, typed milestones:

- `PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED`: accepts only a closed, bounded, non-SAFE Phase56 safety projection and is durable through the canonical journal writer's write → flush → fsync path.
- `PROFILE_A_BLOCKED_DIAGNOSTICS_RETAINED`: accepts only a closed, bounded, BLOCKED Profile-A projection; its selected provider horse number is exactly null; it uses the same durability path.
- Existing `SAFETY_PASS` and `PROFILE_A_QUALIFIED` remain success-only milestones.

The former Safety and Profile-A blocked-result durability gaps are therefore closed. A non-SAFE Safety result or BLOCKED Profile-A result can be retained before raw cleanup.

### Phase59 v2 manifest observability

`MANIFEST_WRITTEN` keeps its exact keys, `fixture_set_identity` and `qualification_identity`, and `JOURNAL_SCHEMA_VERSION = 1`. Its private local validators now accept exactly v1 or v2 lowercase-hex identity strings, derive versions `1` or `2`, accept `v1/v1` and `v2/v2`, and reject either mixed pair. This closes the prior `PHASE57_V2_MANIFEST_OBSERVABILITY_IDENTITY_INCOMPATIBLE` blocker.

Acceptance of v1 is only `LEXICALLY_CANONICAL_HISTORICAL_OBSERVABILITY_VALUE`; it does not imply `V1_PUBLICATION_CONTRACT_RECOVERED`. `V1_PUBLICATION_CONTRACT_NOT_EXACTLY_RECOVERABLE` remains frozen.

## Actual Phase50 order and valid future live sequence

The integrated enum order is authoritative and must not be reordered:

1. `CLOSED_BUNDLE_RETURNED`
2. `DEBA_CAPTURE_METADATA_RETAINED`
3. `RACELIST_CAPTURE_METADATA_RETAINED`
4. `PROFILE_B_DIAGNOSTICS_RETAINED`
5. `IDENTITY_VERIFICATION_PASS`
6. `PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED`
7. `SAFETY_PASS`
8. `PROFILE_A_BLOCKED_DIAGNOSTICS_RETAINED`
9. `PROFILE_A_QUALIFIED`
10. `PROFILE_B_QUALIFIED`
11. `PUBLICATION_BEGIN`
12. `RAW_FIXTURES_WRITTEN`
13. `MANIFEST_WRITTEN`
14. `DEDICATED_TEST_WRITTEN`
15. `REGRESSIONS_PASS`
16. `LIVE_PROCESS_COMPLETE`
17. `PARENT_EVIDENCE_VALIDATION_PASS`
18. `PARENT_CLEANUP_COMPLETE`

The required future sequence is compatible:

1. After a closed Phase44 bundle, construct Phase53 `CaptureMetadataSummary` and durably retain both document metadata records.
2. Evaluate the exact RaceList raw bytes with the sole Phase53 Profile-B diagnostic function and durably emit `PROFILE_B_DIAGNOSTICS_RETAINED`. This preserves diagnostic evidence; it is not yet a success decision.
3. Validate the formal bundle/target/capture identities and emit `IDENTITY_VERIFICATION_PASS` only on exact success.
4. Evaluate Phase56 safety. Emit `SAFETY_PASS` only for SAFE; otherwise durably emit the Phase58 safety-blocked event and stop fail-closed.
5. Evaluate Phase56 Profile-A. Emit `PROFILE_A_QUALIFIED` only for QUALIFIED / `ENTRY_LISTING_PRESENT`; otherwise durably emit the Phase58 Profile-A-blocked event and stop fail-closed.
6. Inspect the already-retained Phase53 diagnostic; emit `PROFILE_B_QUALIFIED` only for QUALIFIED / `EXPLICIT_WITHDRAWAL_PRESENT`, otherwise stop fail-closed using retained diagnostics.

Current semantic validation permits that early Profile-B retention: it requires closed-bundle and both capture records, but does not treat retention as Profile-B qualification. It also rejects later success progression after either new blocked event.

## Proposed no-network pre-live gate

Before a future Phase57 authorization-consumption boundary, complete with provider HTTP `0`, no Phase44 live entry, and authorization still unconsumed:

1. Git/worktree/expected-HEAD validation and final cleanliness recheck.
2. Generated preflight source compile validation.
3. Phase50 synthetic observability preflight; exact binary comparison with `b"NAR_REACQUISITION_OBSERVABILITY_PREFLIGHT_PASS\n"` only, final byte `0A`, no CRLF, stripping, or normalization.
4. Preflight journal/evidence validation and cleanup of preflight/generated artifacts.
5. Strict explicit repository-root validation, sentinel checks, and `sys.path[0]` insertion before imports.
6. Import smoke proving Phase44, Phase50, Phase53, Phase56 Profile-A, and Phase56 publication-contract modules originate under the one authorized worktree, not cwd, an alternate checkout, copied modules, or an installed substitute.
7. Minimal deterministic v2 self-checks, including Phase58 blocked-event support and a Phase59 v2/v2 placeholder `MANIFEST_WRITTEN` acceptance plus mixed-pair rejection.
8. Future live-child generated source compile validation.

## Future authorization and acquisition evidence

Future APPROVE alone may change Phase57 to `PHASE57_ACQUISITION_AUTHORIZATION_UNCONSUMED`. Immediately before the single Phase44 closed-bundle call, the canonical `PHASE44_CALL_ABOUT_TO_ENTER` record must write, flush, and fsync. Only then is authorization `PHASE57_ACQUISITION_AUTHORIZATION_CONSUMED_FAIL_CLOSED`; it is never restored, retried, or reused.

The one successful acquisition must prove exactly one Phase44 entry, each Deba and RaceList transport/pre-GET/response-return/raw-construction event once, and one closed-bundle return. A pre-GET event alone never proves provider receipt; completed request claims require response-return evidence.

Capture retention uses Phase53 `CaptureMetadataSummary`, retaining only role, request/capture identity, SHA-256, byte length, three timestamps, effective/canonical URL match boolean, and closed-bundle identity. No raw body, URL/query, or secret enters the journal.

## Qualification, v2 identities, and manifest

- Phase44 formal identity verification checks the exact target, roles/order, request/capture IDs, SHA/length, six timestamps, bundle identity, effective URL canonical-match booleans, and DebaTable → RaceList relation.
- Phase56 safety is the sole five-category evaluator. SAFE emits `SAFETY_PASS`; every other outcome is durably retained through Phase58 then stops.
- Phase56 Profile-A is the sole `ENTRY_LISTING_PRESENT` evaluator. QUALIFIED emits `PROFILE_A_QUALIFIED`; every BLOCKED result is durably retained through Phase58 then stops. Neither path implies `MARKET_ELIGIBLE`.
- Phase53 is the sole Profile-B evaluator with its six frozen predicates. Its early retained result is reused for the later `PROFILE_B_QUALIFIED` decision; it is never reimplemented in launcher code.
- Phase56 builds and independently validates fixture-set v2 and qualification v2 identities. Fixture-set construction uses the exact formal capture summary and its two fixed v2 fixture-relative paths; qualification uses target, fixture-set, canonical Profile-A and Profile-B results, and `market_eligibility=UNSUPPORTED`.
- Phase56 builds and independently validates manifest v2 in memory before publication. It requires `manifest_schema=nar-race-entry-status-source-profile-fixture-manifest`, schema version `2`, `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`, and `market_eligibility=UNSUPPORTED`.
- After binary manifest reread/revalidation, Phase59 accepts the required v2/v2 `MANIFEST_WRITTEN` pair.

## Publication and cleanup design pending authority recovery

If an exact publication-path authority is established, `PUBLICATION_BEGIN` may occur only after complete bundle, both capture records, retained Profile-B diagnostics, identity verification, SAFE/`SAFETY_PASS`, qualified Profile-A, qualified Profile-B, validated v2 identities, in-memory validated manifest, exact path-plan validation, and an armed rollback plan.

Captured fixture bytes must be binary-written without decode/re-encode, newline conversion, redaction, formatting, or parser round-trip; binary reread, equality, SHA-256, and byte length must then pass before `RAW_FIXTURES_WRITTEN`. Any post-begin local failure must journal `ROLLBACK_BEGIN` and `ROLLBACK_COMPLETE`, restore only the approved publication paths to exact pre-run state, never restore authorization or reacquire, and retain truthful safe failure evidence. Pre-begin failure leaves official publication paths untouched; safe evidence is retained before transient raw bytes, child source, journal after parent validation, temp files, and run cache residue are removed.

## Unresolved tracked publication authority

The Phase56 tracked contract freezes only these v2 fixture-relative paths:

1. `tests/fixtures/nar_race_entry_status/source_profiles/v2/baba_21__2025-01-01__race_06/deba_table.html`
2. `tests/fixtures/nar_race_entry_status/source_profiles/v2/baba_21__2025-01-01__race_06/race_list.html`

Targeted tracked-history searches found no committed authority for the asserted seven-path Phase57 publication manifest, for `tests/test_nar_race_entry_status_source_profile_v2_fixtures.py`, or for the required v2 binary rule `tests/fixtures/nar_race_entry_status/source_profiles/v2/**/*.html -text`. The current `.gitattributes` has a distinct v1 market-odds rule but no v2 source-profile rule.

Therefore this PREPARE cannot truthfully reaffirm that the exact seven paths were already frozen, nor claim that the absent v2 `.gitattributes` rule is already active. The proposed seven-path list from the re-PREPARE instruction is not silently adopted as historical tracked authority.

Required resolution: an explicit reviewed publication-manifest decision must establish the seven exact paths, including the official v2 test path and exact v2 `.gitattributes` line, or provide the authoritative tracked source that already froze them. Until then, future Phase57 cannot enter `PUBLICATION_BEGIN` and must not receive live authorization.

## Completion-outcome and parent-evidence design

Current Phase50 outcomes are sufficient and unchanged:

- successful publication: `READY_FOR_REVIEW`
- source-profile block: `SOURCE_PROFILE_FIXTURE_BLOCKED`
- preflight/recovery block: `RECOVERY_PREFLIGHT_BLOCKED`

The parent must retain/report only safe supported evidence: authorization boundary/state, Phase44 and completion counts, capture/request identities, SHA/length/timestamps/bundle identity, retained Profile-B diagnostics, identity status, retained Safety/Profile-A outcomes, identities if safely available, manifest state, publication/rollback/cleanup state. It must never report raw bodies, secret values, cookie/credential data, arbitrary provider text, or arbitrary URL/query values.

## Approval-readiness answers

| Item | Result | Basis |
| --- | --- | --- |
| A. Phase58 Safety/Profile-A durability blockers closed | YES | Both blocked-only typed, fsynced events are integrated. |
| B. Phase59 v2 `MANIFEST_WRITTEN` incompatibility closed | YES | Exact v2/v2 pair is accepted; mixed pairs reject. |
| C. Actual Phase50 order compatible | YES | Early Profile-B retention then late qualification fits current semantic validation. |
| D. Completion outcomes sufficient | YES | Existing success/source-profile/preflight values map truthfully. |
| E. Exact seven-path manifest still frozen and valid | NO | No committed tracked authority for the full seven-path manifest was found. |
| F. v2 binary rule still correct and active | NO | The proposed rule is plausible but not tracked or active; it cannot be asserted as frozen. |
| G. Post-acquisition failures can preserve required existing safe evidence | YES | Capture, Profile-B, blocked Safety, and blocked Profile-A evidence are durably retained before cleanup; rollback is defined for post-begin failure. |
| H. Additional tracked support/authority phase required | YES | A reviewed tracked publication-manifest/binary-attributes authority decision is required before live approval. |

## Persistent constraints

- Phase41: `DESIGN_BLOCKED`.
- `positive_market_eligibility = UNSUPPORTED`; `WHOLE_MEETING_CANCELLATION = UNSUPPORTED`.
- Open: `COMBINATION_EV_REQUIRES_MARKET_ODDS_CAPTURE`; `NAR_MARKET_ELIGIBILITY_REQUIRES_INDEPENDENT_ENTRY_STATUS_CAPTURE`.
- No source-profile fixture or observability identity establishes `MARKET_ELIGIBLE`.
- PREPARE creates no Python, tests, fixtures, attributes change, provider HTTP, Phase44 entry, authorization, staging, commit, or push.
