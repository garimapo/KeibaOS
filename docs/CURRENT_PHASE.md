# Current Phase

## Phase

`POST_V0_8_DAILY_REPLAY_57`

## Revision

`PHASE57_REPREPARE_AFTER_PHASE61`

## Title

Controlled NAR Source-Profile v2 One-Shot Reacquisition and Publication

## Status

`APPROVED_FOR_CODEX`

## Design review

`PHASE57_REPREPARE_AFTER_PHASE61_DESIGN_REVIEW_PASS`

## Outcome

`READY_FOR_APPROVAL`

## Approval and new one-shot authorization

- Formal status: `APPROVED_FOR_CODEX`.
- Design review: `PHASE57_REPREPARE_AFTER_PHASE61_DESIGN_REVIEW_PASS`.
- Previous authorization: factually unconsumed but superseded; it is not reused.
- New authorization: `PHASE57_ACQUISITION_AUTHORIZATION_UNCONSUMED` against `ac405bd04dcda9c40d763402dc28285a4a71532f` only.
- Target: `NAR / 21 / 2025-01-01 / 6`; exactly one Phase44 closed-bundle call, DebaTable → RaceList, at most two GET attempts.
- Provider HTTP during APPROVE: `0`; Phase44 entered: no; `PHASE44_CALL_ABOUT_TO_ENTER` was not written.
- Approval-state tracking: `INTEGRATED_PENDING_REMOTE_VERIFICATION`; this docs-only tracking does not alter executable support behavior or consume authorization.
- Next permitted action: `EXECUTE_ONE_SHOT_AFTER_INDEPENDENT_REMOTE_VERIFICATION`.

## Base, worktree, and dependency authority

- Authorized worktree: `C:\Users\garim\Desktop\KeibaOS-post-v0.8`.
- Branch and base/local/remote HEAD: `feature/post-v0.8-daily-replay` / `ac405bd04dcda9c40d763402dc28285a4a71532f`.
- PREPARE began clean, with empty index and no untracked paths.
- Phase61 commit/tree: `ac405bd04dcda9c40d763402dc28285a4a71532f` / `dba91e0adbd15671771fb78ef41a0d68a24d98cc`.
- The present Phase57 instruction supplies the formal-complete dependency authority for Phases56, 58, 59, 60, and 61. The older Phase61 document state is historical and does not override this explicit dependency declaration.
- Phase61 is the formally complete baseline authority for the exact two-path dedicated-test compatibility; Phase60 remains the formally complete publication-plan and binary-preservation baseline.
- This is design only: no provider HTTP, Phase44 entry, authorization action, fixture write, stage, commit, or push.

## Authorization history and current authority

The authorization issued against `d14afa262900c8a1fb5f2c25ca8ef2867d5f52c9` was never consumed: provider HTTP `0`, Phase44 calls `0`, GET attempts `0`, and no `PHASE44_CALL_ABOUT_TO_ENTER` record. Its factual history is preserved, but Phase61 changed the HEAD and support baseline.

Frozen supersession state:

`PHASE57_PREVIOUS_AUTHORIZATION_FACTUALLY_UNCONSUMED_BUT_SUPERSEDED_BY_PHASE61`

It grants no permission at this HEAD and must not be reused. Its pre-APPROVE usable authorization state was `NONE`; this approval issued the separate new `PHASE57_ACQUISITION_AUTHORIZATION_UNCONSUMED` state above. Phase54 remains `PHASE54_AUTHORIZATION_UNCONSUMED_BUT_UNUSABLE_FOR_V2`.

## Target and one-shot acquisition contract

- Target: `NAR / baba_code=21 / 2025-01-01 / race_no=6`.
- Acquisition semantic: `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`.
- Phase44 is the sole future acquisition authority: exactly one closed-bundle call, `DebaTable` then `RaceList`, at most two GET attempts.
- No retry, fallback, discovery, alternate provider/target, partial bundle, or direct provider request is allowed.
- This never establishes historical availability, historical bytes, backdated response, historical cutoff, or market eligibility. `market_eligibility=UNSUPPORTED`.

## Phase61 blocker closure

`PHASE57_V2_DEDICATED_TEST_OBSERVABILITY_PATH_INCOMPATIBLE` is closed. Phase50 now validates `DEDICATED_TEST_WRITTEN` with exact membership in this closed union:

1. `tests/test_nar_race_entry_status_source_profile_fixtures.py`
2. `tests/test_nar_race_entry_status_source_profile_v2_fixtures.py`

The second value is exactly the Phase60-authorized future dedicated test path. All third paths—including v3, suffix/prefix variants, arbitrary paths, absolute/drive paths, backslashes, whitespace, controls, NUL, and traversal—remain rejected after unchanged `_safe_string` validation. The event remains `DEDICATED_TEST_WRITTEN` with exactly `test_path`; `JOURNAL_SCHEMA_VERSION=1`, `MAX_STRING_BYTES=512`, `MAX_RECORD_BYTES=4096`, `MAX_JOURNAL_BYTES=131072`, `MAX_PROCESS_STREAM_BYTES=16384`, `_ALLOWED_OUTCOMES`, `PREFLIGHT_PASS_TOKEN`, and enum order are unchanged.

## Integrated support authorities

- Phase58 retains non-SAFE Safety and BLOCKED Profile-A evidence via canonical write → flush → fsync events `PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED` and `PROFILE_A_BLOCKED_DIAGNOSTICS_RETAINED`; `SAFETY_PASS` and `PROFILE_A_QUALIFIED` remain success evidence.
- Phase59 keeps `MANIFEST_WRITTEN` v1/v1 and v2/v2 acceptance, with v1/v2 and v2/v1 rejection; keys and schema v1 are unchanged.
- Phase60 freezes the prospective six-path live delta: the two v2 raw HTML fixtures, target-local `manifest.json`, `tests/test_nar_race_entry_status_source_profile_v2_fixtures.py`, and the two documentation files. The first four are `CREATE_ONLY`, docs are `MODIFY_EXISTING`, and `.gitattributes` is `VALIDATE_ONLY`.
- The active Phase60 binary rule is `tests/fixtures/nar_race_entry_status/source_profiles/v2/**/*.html -text -diff`; both future HTML paths resolve `text: unset` and `diff: unset`.

## Actual Phase50 ordering and future no-network gates

The integrated order is authoritative:

`CLOSED_BUNDLE_RETURNED` → `DEBA_CAPTURE_METADATA_RETAINED` → `RACELIST_CAPTURE_METADATA_RETAINED` → `PROFILE_B_DIAGNOSTICS_RETAINED` → `IDENTITY_VERIFICATION_PASS` → `PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED` → `SAFETY_PASS` → `PROFILE_A_BLOCKED_DIAGNOSTICS_RETAINED` → `PROFILE_A_QUALIFIED` → `PROFILE_B_QUALIFIED` → `PUBLICATION_BEGIN` → `RAW_FIXTURES_WRITTEN` → `MANIFEST_WRITTEN` → `DEDICATED_TEST_WRITTEN` → `REGRESSIONS_PASS` → `ROLLBACK_BEGIN` → `ROLLBACK_COMPLETE` → `LIVE_PROCESS_COMPLETE` → `PARENT_EVIDENCE_VALIDATION_PASS` → `PARENT_CLEANUP_COMPLETE`.

Before any authorization consumption or provider HTTP, future execution must complete: authorized worktree/branch/local+remote HEAD/clean-tree checks; explicit module-origin binding; Phase60 plan and Phase56 raw-path agreement; generated preflight/live-child compilation; Phase50 synthetic preflight plus parent validation and exact binary-LF token comparison; preflight cleanup; Phase58 blocked-event checks; Phase59 v2/v2 and mixed-pair checks; Phase61 v2 acceptance and third-path rejection; Phase60 plan/attribute/check-attr validation; create-only absence; docs presence; and a final clean-tree check.

The token must be exact bytes `b"NAR_REACQUISITION_OBSERVABILITY_PREFLIGHT_PASS\n"`, with no CRLF, normalization, stripping, or extra/missing bytes.

## Future live sequence and publication boundary

The only consumption boundary is canonical `PHASE44_CALL_ABOUT_TO_ENTER` append → flush → fsync → Phase44 entry. Only after fsync does authorization become `PHASE57_ACQUISITION_AUTHORIZATION_CONSUMED_FAIL_CLOSED`; no retry, reuse, or reversion is permitted.

This APPROVE does not cross that boundary. If a future EXECUTE stops before the durable record, the new authorization is factually unconsumed but must not be retried automatically; a later attempt still needs explicit review/instruction.

After a complete bundle: retain Phase53 capture metadata; retain the six-predicate Profile-B diagnostic before identity verification; verify the complete capture identity; apply Phase56 Safety; then Phase56 Profile-A. A non-SAFE or blocked Profile-A result is durably retained and finishes `SOURCE_PROFILE_FIXTURE_BLOCKED`. Later Profile-B qualification uses the already retained diagnostic only and requires `QUALIFIED` with `EXPLICIT_WITHDRAWAL_PRESENT`; it does not reparse raw content.

Only Phase56 builds and validates `FixtureSetV2`, qualification-v2, and manifest-v2. Required prefixes are `nar-race-entry-status-source-profile-fixture-set-v2:` and `nar-race-entry-status-source-profile-qualification-v2:`. Manifest requires `nar-race-entry-status-source-profile-fixture-manifest`, schema version `2`, current-acquisition semantics, and `market_eligibility=UNSUPPORTED`.

`PUBLICATION_BEGIN` is forbidden until the complete bundle, durable capture/Profile-B evidence, identity/Safety/Profile-A/Profile-B success, validated v2 identities and manifest, valid six-path plan, absent create-only artifacts, present docs, active attributes, passing check-attr, and armed rollback plan all exist. Raw fixtures are binary-write only and must binary-reread byte-for-byte. The exact v2 dedicated test then emits `DEDICATED_TEST_WRITTEN` using its newly accepted Phase61 path.

## Completion, failure, and rollback

`LIVE_PROCESS_COMPLETE` remains: `READY_FOR_REVIEW` for success, `SOURCE_PROFILE_FIXTURE_BLOCKED` for source-profile block, and `RECOVERY_PREFLIGHT_BLOCKED` for pre-live/acquisition-integrity/recovery block. The semantic success outcome remains `CONTROLLED_REACQUISITION_AND_SOURCE_PROFILE_V2_PUBLICATION_COMPLETE`.

Before `PUBLICATION_BEGIN`, post-consumption failures preserve safe durable evidence, clean transient raw data, and leave official paths unchanged. After `PUBLICATION_BEGIN`, `ROLLBACK_BEGIN` then `ROLLBACK_COMPLETE` restore exactly the six Phase57 paths; never `.gitattributes`, Phase60/61 support, Phase44/50/53/56, or authorization state.

## Approval-readiness matrix

| Item | Result |
| --- | --- |
| A. Phase58 blocked evidence durable | YES |
| B. Phase59 v2/v2 manifest observability valid | YES |
| C. Phase60 six-path authority usable | YES |
| D. Phase60 binary preservation active | YES |
| E. Phase61 v2 dedicated-test path accepted | YES |
| F. Phase61 arbitrary third path rejected | YES |
| G. Phase50 order compatible | YES |
| H. Completion vocabulary sufficient | YES |
| I. Safe evidence retainable before cleanup | YES |
| J. Exact six-path rollback possible | YES |
| K. All pre-live gates no-network | YES |
| L. Additional tracked support phase required | NO |

## Persistent constraints

- Phase41: `DESIGN_BLOCKED`.
- Open: `COMBINATION_EV_REQUIRES_MARKET_ODDS_CAPTURE`; `NAR_MARKET_ELIGIBILITY_REQUIRES_INDEPENDENT_ENTRY_STATUS_CAPTURE`.
- `market_eligibility = UNSUPPORTED`; `positive_market_eligibility = UNSUPPORTED`; `WHOLE_MEETING_CANCELLATION = UNSUPPORTED`.
- No source-profile fixture, manifest, or observability evidence establishes `MARKET_ELIGIBLE`.
