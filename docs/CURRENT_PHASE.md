# Current Phase

## Phase

`POST_V0_8_DAILY_REPLAY_57`

## Revision

`PHASE57_FINAL_REPREPARE_AFTER_PHASE60`

## Title

Controlled NAR Source-Profile v2 One-Shot Reacquisition and Publication

## Status

`APPROVED_FOR_CODEX`

## Design review

`PHASE57_FINAL_DESIGN_REVIEW_PASS`

## Outcome

`READY_FOR_APPROVAL`

## Approval and one-shot authorization

- Formal status: `APPROVED_FOR_CODEX`.
- Design review: `PHASE57_FINAL_DESIGN_REVIEW_PASS`.
- Previous authorization state: `PHASE57_ACQUISITION_AUTHORIZATION_NOT_YET_ISSUED`.
- New authorization state: `PHASE57_ACQUISITION_AUTHORIZATION_UNCONSUMED`.
- Authorization target: `NAR / 21 / 2025-01-01 / 6`.
- Authorized Phase44 closed-bundle calls: `1`; maximum provider GET attempts: `2`; collection order: `DebaTable` then `RaceList`.
- Provider HTTP during APPROVE: `0`; Phase44 live acquisition: not entered; authorization remains unconsumed.
- Live execution: `NOT_STARTED`.
- Next permitted action: `EXECUTE_ONE_SHOT_AFTER_INDEPENDENT_REMOTE_VERIFICATION`.

## Git and dependency basis

- Authorized worktree: `C:\Users\garim\Desktop\KeibaOS-post-v0.8`.
- Branch and base/local/remote HEAD: `feature/post-v0.8-daily-replay` / `6cc7ee3dc28c9e1b88b0e0c940103765d875e7a3`.
- Phase60 integration commit/tree: `6cc7ee3dc28c9e1b88b0e0c940103765d875e7a3` / `950832b548551d4394afc14dc490647db57326d2`.
- User-supplied phase-state authority declares Phase56, Phase58, Phase59, and Phase60 formally complete dependencies. The earlier in-tree Phase60 integration report is historical and does not replace that declaration.
- Phase58 provides durable blocked Safety/Profile-A evidence; Phase59 accepts v2/v2 `MANIFEST_WRITTEN` pairs; Phase60 provides the prospective, tracked publication-plan and binary-preservation authority.

## Authorization and target

- Phase57 previous PREPARE state: `PHASE57_ACQUISITION_AUTHORIZATION_NOT_YET_ISSUED`.
- Phase57 current approved state: `PHASE57_ACQUISITION_AUTHORIZATION_UNCONSUMED`.
- Phase54: `PHASE54_AUTHORIZATION_UNCONSUMED_BUT_UNUSABLE_FOR_V2`; it can never be reused.
- This approval issued one new Phase57 authorization only; it is not Phase54 authority and has not been consumed.
- Frozen target: `NAR / baba_code=21 / 2025-01-01 / race_no=6`.
- Acquisition semantics: `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`. It does not establish historical bytes, provider availability/state, cutoff, market eligibility, or backdated response time. `market_eligibility=UNSUPPORTED`.

## Authorities and exact future live delta

Phase44 is the sole acquisition authority. There is exactly one closed-bundle call, in `DebaTable` then `RaceList` order, with at most two GET attempts. No retry, discovery, fallback, alternate provider/target, partial bundle, second Phase44 call, or direct provider request is allowed.

Phase60 authority is prospective (`PHASE60_PUBLICATION_PLAN_AUTHORITY_EFFECTIVE_FROM_INTEGRATION`) and freezes these exact six Phase57 paths, in role order:

1. `DEBA_TABLE_FIXTURE` — `tests/fixtures/nar_race_entry_status/source_profiles/v2/baba_21__2025-01-01__race_06/deba_table.html` — `CREATE_ONLY`
2. `RACE_LIST_FIXTURE` — `tests/fixtures/nar_race_entry_status/source_profiles/v2/baba_21__2025-01-01__race_06/race_list.html` — `CREATE_ONLY`
3. `MANIFEST` — `tests/fixtures/nar_race_entry_status/source_profiles/v2/baba_21__2025-01-01__race_06/manifest.json` — `CREATE_ONLY`
4. `DEDICATED_FIXTURE_TEST` — `tests/test_nar_race_entry_status_source_profile_v2_fixtures.py` — `CREATE_ONLY`
5. `CURRENT_PHASE_DOC` — `docs/CURRENT_PHASE.md` — `MODIFY_EXISTING`
6. `LATEST_CODEX_REPORT` — `docs/LATEST_CODEX_REPORT.md` — `MODIFY_EXISTING`

Phase56 remains sole raw-path and semantic-identity authority; Phase57 loads and validates the Phase60 plan against an exact Phase56 `FixtureSetV2`. `.gitattributes` is Phase60 baseline support, `VALIDATE_ONLY` for Phase57, and never part of its live delta or rollback scope. Its exact active rule is:

```text
tests/fixtures/nar_race_entry_status/source_profiles/v2/**/*.html -text -diff
```

Git resolves both frozen HTML paths to `text: unset` and `diff: unset`.

## Actual Phase50 order and completion outcomes

The integrated enum order is authoritative:

1. `PARENT_EXECUTION_PREPARED`
2. `LIVE_PROCESS_START`
3. `TARGET_CONSTRUCTED`
4. `PHASE44_CALL_ABOUT_TO_ENTER`
5. `PHASE44_FUNCTION_ENTERED`
6. `DEBA_TRANSPORT_FETCH_ENTERED`
7. `DEBA_HTTP_GET_ATTEMPT_ABOUT_TO_START`
8. `DEBA_HTTP_RESPONSE_RETURNED`
9. `DEBA_RAW_RESPONSE_CONSTRUCTED`
10. `RACELIST_TRANSPORT_FETCH_ENTERED`
11. `RACELIST_HTTP_GET_ATTEMPT_ABOUT_TO_START`
12. `RACELIST_HTTP_RESPONSE_RETURNED`
13. `RACELIST_RAW_RESPONSE_CONSTRUCTED`
14. `CLOSED_BUNDLE_RETURNED`
15. `DEBA_CAPTURE_METADATA_RETAINED`
16. `RACELIST_CAPTURE_METADATA_RETAINED`
17. `PROFILE_B_DIAGNOSTICS_RETAINED`
18. `IDENTITY_VERIFICATION_PASS`
19. `PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED`
20. `SAFETY_PASS`
21. `PROFILE_A_BLOCKED_DIAGNOSTICS_RETAINED`
22. `PROFILE_A_QUALIFIED`
23. `PROFILE_B_QUALIFIED`
24. `PUBLICATION_BEGIN`
25. `RAW_FIXTURES_WRITTEN`
26. `MANIFEST_WRITTEN`
27. `DEDICATED_TEST_WRITTEN`
28. `REGRESSIONS_PASS`
29. `ROLLBACK_BEGIN`
30. `ROLLBACK_COMPLETE`
31. `LIVE_PROCESS_COMPLETE`
32. `PARENT_EVIDENCE_VALIDATION_PASS`
33. `PARENT_CLEANUP_COMPLETE`

Existing allowed `LIVE_PROCESS_COMPLETE` outcomes are sufficient and unchanged: successful publication uses `READY_FOR_REVIEW`; a Safety/Profile-A/Profile-B source-profile block uses `SOURCE_PROFILE_FIXTURE_BLOCKED`; pre-live, acquisition-integrity, or recovery block uses `RECOVERY_PREFLIGHT_BLOCKED`. `SYNTHETIC_SUCCESS` and `SYNTHETIC_FAILURE` remain synthetic-only and are not live outcomes.

## Exact pre-live no-network gate

Before authorization consumption, complete in this exact order with provider HTTP `0`:

1. Validate authorized worktree, branch, local/remote HEAD, and cleanliness.
2. Import the exact Phase60 plan from the authorized root; validate its target and six entries against Phase56.
3. Validate Phase44, Phase50, Phase53, Phase56 Profile-A, Phase56 publication-contract, and Phase60 module origins from the authorized tree, after strict root/sentinel validation and `sys.path[0]` binding.
4. Compile generated preflight source; run the Phase50 synthetic observability preflight; validate its journal through the parent; clean generated/preflight artifacts.
5. Compare binary stdout exactly to `b"NAR_REACQUISITION_OBSERVABILITY_PREFLIGHT_PASS\n"`; reject CRLF, missing LF, extra bytes, stripping, normalization, or text-mode rewriting.
6. Self-check Phase58 blocked-event support, Phase59 v2/v2 `MANIFEST_WRITTEN` acceptance and mixed v1/v2 rejection, the Phase60 six-path plan, the active attribute rule, and both `check-attr` results.
7. Confirm all four create-only paths are absent, both documentation paths exist, compile future live-child source, then repeat the clean-repository check.

## Authorization, collection, and retained evidence

Immediately before the one Phase44 call, write the canonical `PHASE44_CALL_ABOUT_TO_ENTER` record, flush, and fsync. Only then is authorization `PHASE57_ACQUISITION_AUTHORIZATION_CONSUMED_FAIL_CLOSED`; it never reverts. A successful acquisition proves exactly one Phase44 entry, one Deba and one RaceList transport/pre-GET/response-return/raw-construction event, one closed-bundle return, and at most two GETs. Pre-GET alone never proves receipt.

After closed-bundle return, construct Phase53 `CaptureMetadataSummary` and durably emit both capture metadata milestones. Retain only role, request/capture IDs, SHA-256, byte length, requested/observed/captured timestamps, effective-URL canonical-match boolean, and closed-bundle identity; never raw body, URL/query, cookie, credential, or secret.

Use Phase53 only to diagnose exact RaceList bytes and target. Retain all six Profile-B predicates through `PROFILE_B_DIAGNOSTICS_RETAINED` before identity verification. This is evidence only, not a qualification event. Verify target, role/order, request/capture identities, SHA/length, six timestamps, URL-match flags, bundle identity, and Deba→RaceList relationship before emitting `IDENTITY_VERIFICATION_PASS`.

## Qualification, identities, and publication boundary

- Phase56 Safety alone evaluates exact captured Deba/RaceList bytes. `SAFE` emits `SAFETY_PASS`; every other outcome emits fsynced `PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED` and stops.
- Phase56 Profile-A alone evaluates exact Deba bytes and target. `QUALIFIED` with `ENTRY_LISTING_PRESENT` emits `PROFILE_A_QUALIFIED`; a non-qualified result emits fsynced `PROFILE_A_BLOCKED_DIAGNOSTICS_RETAINED` and stops.
- Only after identity, Safety, and Profile-A pass may the already-retained Phase53 Profile-B diagnostic yield `PROFILE_B_QUALIFIED`; it must be `QUALIFIED` with `EXPLICIT_WITHDRAWAL_PRESENT`. No parser is rerun and no market eligibility is inferred.
- Phase56 alone builds and independently validates fixture-set v2 (`nar-race-entry-status-source-profile-fixture-set-v2:`) from target plus exact capture summary, qualification v2 (`nar-race-entry-status-source-profile-qualification-v2:`) from exact target/fixture/Profile-A/Profile-B, and manifest v2. Manifest requires schema `nar-race-entry-status-source-profile-fixture-manifest`, version `2`, current-acquisition semantics, and `market_eligibility=UNSUPPORTED`.

`PUBLICATION_BEGIN` is forbidden until the closed bundle, both retained capture records, retained Profile-B diagnostics, identity/Safety/Profile-A/Profile-B success, independently validated fixture/qualification identities and manifest, validated Phase60 plan, six paths, absent create-only paths, present docs, active attributes, passing `check-attr`, and armed rollback snapshot all exist.

## Publication, test, cleanup, and rollback

After `PUBLICATION_BEGIN`, write the two raw bodies only in binary mode, with no decode/re-encode, newline change, redaction, reconstruction, or formatting. Binary reread must equal captured bytes and match SHA-256/length before `RAW_FIXTURES_WRITTEN` (`document_count=2`). Write the already-validated in-memory canonical manifest, binary reread it, recheck canonicality and Phase56 validation, then emit `MANIFEST_WRITTEN` using the exact v2/v2 identities.

Only then create the dedicated no-network fixture test. It must verify both raw hashes/lengths, target and role order, Phase56 fixture/qualification recomputation, manifest canonicality/validation, Safety SAFE, Profile-A/Profile-B qualification and Profile-B `EXPLICIT_WITHDRAWAL_PRESENT`, current-acquisition semantics, `market_eligibility=UNSUPPORTED`, and no HTTP. Emit `DEDICATED_TEST_WRITTEN`; run it, relevant no-network NAR regression, and one full suite; then emit bounded truthful `REGRESSIONS_PASS` evidence.

Before `PUBLICATION_BEGIN`, a post-acquisition failure keeps authorization consumed, retains available safe evidence first, destroys transient raw bodies, generated source, temporary files, and run cache residue, and leaves all six official paths unchanged. After `PUBLICATION_BEGIN`, write `ROLLBACK_BEGIN`, restore only the six live paths to exact pre-run state, write `ROLLBACK_COMPLETE`, never reacquire, and never touch Phase60 baseline or authorization.

Parent final evidence must safely reconstruct authorization/boundary, entry and transport counts, capture metadata, Profile-B diagnostics, identity/Safety/Profile-A/Profile-B decisions, built identities/manifest status, publication/rollback/cleanup state—without raw HTML, arbitrary provider text/query, cookie, credential, or secret values.

## Success and approval readiness

The future successful live implementation outcome is `CONTROLLED_REACQUISITION_AND_SOURCE_PROFILE_V2_PUBLICATION_COMPLETE`; no competing tracked wording was found in the prior blocked-design record.

| Item | Result | Basis |
| --- | --- | --- |
| A. Phase58 failure-evidence durability closed | YES | Both blocked-only events are validated, journaled, flushed, and fsynced. |
| B. Phase59 v2 manifest observability closed | YES | v2/v2 accepts; mixed versions reject; schema v1 and keys are unchanged. |
| C. Phase60 authority formally complete and usable | YES | Accepted user-supplied dependency state and tracked commit/tree provide the prospective plan baseline. |
| D. Phase60 binary preservation active | YES | Exact rule is tracked; both future paths resolve `text/diff: unset`. |
| E. Actual Phase50 order compatible | YES | Early Profile-B retention precedes identity and later qualification without semantic contradiction. |
| F. Completion vocabulary sufficient | YES | Existing live success/source-profile/recovery outcomes map truthfully. |
| G. Pre-publication failures retain safe evidence | YES | Capture/Profile-B plus Phase58 blocked evidence are durable before raw cleanup. |
| H. Post-begin rollback is exact six-path scope | YES | Phase60 plan freezes scope; `.gitattributes` and support remain excluded. |
| I. All pre-live gates execute without provider HTTP | YES | They are compile/import/synthetic journal/attribute/path checks only. |
| J. Additional tracked support phase required | NO | Phase58/59/60 close the formerly missing durability, observability, plan, and binary-rule gaps. |

## Persistent constraints

- Phase41: `DESIGN_BLOCKED`.
- `positive_market_eligibility = UNSUPPORTED`; `WHOLE_MEETING_CANCELLATION = UNSUPPORTED`.
- Open: `COMBINATION_EV_REQUIRES_MARKET_ODDS_CAPTURE`; `NAR_MARKET_ELIGIBILITY_REQUIRES_INDEPENDENT_ENTRY_STATUS_CAPTURE`.
- No source profile, fixture, plan, or manifest establishes `MARKET_ELIGIBLE`.
- This approval creates no source/test/fixture/attribute change, provider HTTP, Phase44 entry, authorization consumption, staging, commit, or push.
