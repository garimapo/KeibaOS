# Current Phase

## POST_V0_8_DAILY_REPLAY_80

Title: Fresh Current V3 Source-Profile Publication After Executable Dedicated-Test Preflight

Formal Status: APPROVED_FOR_CODEX

Authorization Tracking State: APPROVED_UNCONSUMED_TRACKED after this approval document is committed, normally pushed, and local HEAD equals remote-tracking HEAD.

Outcome: APPROVED_FRESH_V3_PUBLICATION_AFTER_EXECUTABLE_TEST_PREFLIGHT

Design Contract: V3_FRESH_PUBLICATION_AFTER_EXECUTABLE_TEST_PREFLIGHT_CONTRACT_COMPLETE

Design Review: PHASE80_PUBLICATION_DESIGN_REVIEW_PASS_WITH_REGRESSION_ORDER_CORRECTION

### Authorized baseline

Branch: feature/post-v0.8-daily-replay

Executable Support HEAD: 321868ac827677700da2c2ec41fded860eb464cc

Executable Support Tree: 0c422b45118131b8e3bb8ce5dd7189f2368e683e

Target: NAR / 21 / 2025-01-01 / 6

Future Purpose: FRESH_CURRENT_V3_SOURCE_PROFILE_PUBLICATION_AFTER_EXECUTABLE_TEST_PREFLIGHT

Semantics: CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET

### Frozen prior phases

Phase76: TERMINAL_CONSUMED_BLOCKED_ROLLBACK_COMPLETE

Phase76 Review: PHASE76_CONSUMED_BLOCKED_RESULT_REVIEW_PASS

Phase76 Authorization: PHASE76_V3_SOURCE_PROFILE_PUBLICATION_AUTHORIZATION_CONSUMED_FAIL_CLOSED

Phase76 blocker: REGRESSION_FAILURE_AT_DEDICATED_V3_FIXTURE_TEST

Phase76 underlying cause: UNKNOWN_AFTER_BOUNDED_EVIDENCE_GAP

Phase78: NOT_ENTERED_NO_PUBLICATION_DELTA. It remains unused and must not be repurposed.

Phase79: FORMALLY_COMPLETE

Phase79 Verification: PHASE79_IMPLEMENTATION_REMOTE_VERIFICATION_PASS

Phase79 Support: V3_DEDICATED_FIXTURE_TEST_EXECUTION_AND_FAILURE_EVIDENCE_AUTHORITY_IMPLEMENTED

### Phase80 authorization and approval tracking

The approval tracking commit itself performs no live execution. The authorization is executable only after this exact approved contract is present in both documents, the docs-only commit succeeds, its normal push succeeds, and local HEAD equals remote-tracking HEAD. Until then it is not executable.

After those tracking conditions, the issued one-shot token is PHASE80_V3_SOURCE_PROFILE_PUBLICATION_AUTHORIZATION_UNCONSUMED and its tracking state is APPROVED_UNCONSUMED_TRACKED. Its permanent post-boundary state is PHASE80_V3_SOURCE_PROFILE_PUBLICATION_AUTHORIZATION_CONSUMED_FAIL_CLOSED. It binds only to POST_V0_8_DAILY_REPLAY_80, support HEAD 321868ac827677700da2c2ec41fded860eb464cc, support tree 0c422b45118131b8e3bb8ce5dd7189f2368e683e, target NAR / 21 / 2025-01-01 / 6, purpose FRESH_CURRENT_V3_SOURCE_PROFILE_PUBLICATION_AFTER_EXECUTABLE_TEST_PREFLIGHT, and CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET semantics. It is one-shot, nontransferable, support-specific, target-specific, purpose-specific, and phase-specific; it cannot be reused after its durable boundary.

### Mandatory pre-live gates

No authorization boundary may be crossed unless every gate passes:

- IMPORT_ISOLATION_PASS, including PEP 420 `scripts` namespace validation and all Phase80 authority-module origins under the approved worktree and support identity.
- V3_DEDICATED_FIXTURE_TEST_END_TO_END_PREFLIGHT_PASS by calling the exact committed `run_nar_race_entry_status_source_profile_v3_fixture_test_preflight` support. It must use `python -I -B`, an external mirror outside the repository, `--import-mode=importlib`, controlled plugin autoload, authorized production origins only, and an actual generated pytest PASS.
- The preflight evidence must retain generated-source and manifest SHA-256/length, pytest command identity and return code, Phase50-sanitized stdout/stderr evidence, and import-isolation result. It must report `test_passed = true` with Provider HTTP / actual Phase44 / GET equal to 0 / 0 / 0.
- PUBLICATION_PLAN_V3_DRY_RUN_PASS, V3 publication-contract validation, Phase50 V3 dedicated-test-path integration, Profile-B v2 and sibling `table.changeInfo` topology gates, Profile-A v3, Safety v3, Phase50 versioned/blocked-payload gates, Phase71 target-contract integration, exact 11-key metadata, closed-bundle identity propagation, runner parity, no-network and live-logic parity gates.
- CREATE_ONLY_TARGETS_ABSENT_PASS, repository clean, staged empty, untracked empty, exact LF preflight, and `GITATTRIBUTES_V3_VALIDATE_ONLY_PASS`.

Any failed pre-live gate is PRE_AUTHORIZATION_STOP: no Phase80 authorization consumption, provider HTTP, Phase44, GET, publication, or automatic retry.

### Closed publication authority

The exact future six-path delta is:

- CREATE_ONLY: `tests/fixtures/nar_race_entry_status/source_profiles/v3/baba_21__2025-01-01__race_06/deba_table.html`
- CREATE_ONLY: `tests/fixtures/nar_race_entry_status/source_profiles/v3/baba_21__2025-01-01__race_06/race_list.html`
- CREATE_ONLY: `tests/fixtures/nar_race_entry_status/source_profiles/v3/baba_21__2025-01-01__race_06/manifest.json`
- CREATE_ONLY: `tests/test_nar_race_entry_status_source_profile_v3_fixtures.py`
- MODIFY_EXISTING: `docs/CURRENT_PHASE.md`
- MODIFY_EXISTING: `docs/LATEST_CODEX_REPORT.md`

All four CREATE_ONLY paths must be absent before the live boundary. The tracked V3 binary rule must occur exactly once: `tests/fixtures/nar_race_entry_status/source_profiles/v3/**/*.html -text -diff`. The two future HTML paths must have `text` and `diff` unset; `.gitattributes` is VALIDATE_ONLY and must not be changed.

The committed Phase79 renderer `render_nar_race_entry_status_source_profile_v3_fixture_test` is the sole dedicated-test generation authority. The future live runner must not contain an inline template or a duplicate renderer.

### Future transaction

The sole durable authorization boundary is `PHASE44_CALL_ABOUT_TO_ENTER`, appended, flushed, and fsynced. Only after that succeeds does the external token become PHASE80_V3_SOURCE_PROFILE_PUBLICATION_AUTHORIZATION_CONSUMED_FAIL_CLOSED. Phase50 separately reconstructs `UNCONSUMED`, `CONSUMED_FAIL_CLOSED`, or, after `PHASE44_FUNCTION_ENTERED`, `CONSUMED_CONFIRMED`.

The request caps are one Phase44 invocation, one Deba transport/GET, one RaceList transport/GET, and two GETs total, in DebaTable then RaceList order. Retries, fallback, alternate targets, and discovery are forbidden.

The exact same new response-body bytes must be used for capture metadata, Profile-B v2, Phase63/66, Safety v3, Profile-A v3, FixtureSetV3, QualificationV3, SourceProfileManifestV3, renderer input, and repository raw fixtures. Refetching, Phase74/76 substitution, decoding/re-encoding, and HTML serialization are forbidden.

Before `PUBLICATION_BEGIN`, require the exact 11-key metadata contract, closed-bundle identity propagation, identity verification, Profile-B v2 QUALIFIED with all six predicates and target schedule count one, Phase66 direct schedule count one and structural consistency, Safety v3 SAFE with five SAFE categories and zero findings, Profile-A v3 QUALIFIED with three predicates, and validated FixtureSetV3, QualificationV3, SourceProfileManifestV3, and SourceProfilePublicationPlanV3.

Only then append durable `PUBLICATION_BEGIN` with `planned_path_count: 6`. Raw fixtures must be written as original bytes and read back for exact equality, SHA-256, length, and attributes. The manifest must be exact canonical bytes, read back, and validated. The dedicated test must be generated only by the Phase79 renderer, be UTF-8/LF/no-BOM, compile, be at most 65536 bytes, and be read back exactly.

The dedicated V3 fixture test executes exactly once, as regression step #1. On its failure, first build and durably retain bounded evidence using `build_v3_fixture_test_failure_evidence` and `retain_v3_fixture_test_failure_evidence_durably`; receipt must confirm flush, fsync, and validated readback. Evidence includes generated source, validated bounded manifest or safe projection, identities, fixture SHA/length, command/return code, and Phase50-sanitized output, never raw HTML. Only then may `ROLLBACK_BEGIN` occur. If a later regression fails, retain bounded command/result evidence sufficient to identify that regression before the same rollback sequence.

The exact regression order is: (1) `tests/test_nar_race_entry_status_source_profile_v3_fixtures.py`; (2) `tests/test_nar_race_entry_status_source_profile_fixture_test_generator.py`; (3) `tests/test_nar_race_entry_status_source_profile_fixture_test_preflight.py`; (4) `tests/test_nar_race_entry_status_source_profile_publication_plan.py`; (5) `tests/test_nar_race_entry_status_source_profile_publication_contract.py`; (6) `tests/test_nar_race_entry_status_source_profile_diagnostics.py`; (7) `tests/test_nar_race_entry_status_source_profile_profile_a.py`; (8) `tests/test_nar_race_entry_status_source_profile_structural_recovery_diagnostics.py`; (9) `tests/test_nar_race_entry_status_reacquisition_observability.py`; and (10) the full repository suite. All must pass before `REGRESSIONS_PASS`.

### Success, rollback, and integration split

A successful Phase80 stops for review with only the two documentation files modified and the four CREATE_ONLY artifacts untracked; the index is empty and there is no commit or push. `git diff --check` must pass. The result is `V3_SOURCE_PROFILE_PUBLICATION_DELTA_READY_FOR_CHATGPT_REVIEW` with external authorization consumed fail-closed and Phase50 authorization `CONSUMED_CONFIRMED`.

Any failure after `PUBLICATION_BEGIN` retains required evidence first, appends `ROLLBACK_BEGIN`, deletes only the four Phase80 CREATE_ONLY artifacts, restores the two documents byte-exact to the Phase80 pre-live baseline, verifies a clean repository, and appends `ROLLBACK_COMPLETE`. No reset, restore, checkout, stash, clean, or retry is allowed.

Git integration is explicitly separate. Phase78 remains unused. Only after independent review of a successful Phase80 delta may a new no-network Phase81-or-later integration phase stage exactly the six paths, commit once, and push normally. It must not acquire, refetch, invoke Phase44, or use GET.

### Historical interpretation

Market eligibility, positive market eligibility, and WHOLE_MEETING_CANCELLATION remain UNSUPPORTED. Current-byte reproduction or fixture existence never proves historical bytes, historical availability, or historical market eligibility.

### Readiness matrix

A–U: YES.

A. Phase79 formally complete. B. Phase76 permanently consumed and frozen. C. Phase78 frozen not entered. D. Phase79 support HEAD/tree fixed. E. New Phase80 authorization defined but not issued. F. Phase79 executable pytest preflight mandatory. G. Six paths fixed. H. CREATE_ONLY absence gate defined. I. Exact gitattributes gate defined. J. Sole durable boundary defined. K. One-Phase44/two-GET caps defined. L. Same-byte authority defined. M. Qualification gates defined. N. Repo-owned renderer is sole generator. O. Dedicated pytest precedes broader regressions. P. Failure evidence is durable before rollback. Q. Manifest/source/hash evidence is preserved. R. Exact success unstaged delta is defined. S. Rollback restores the clean baseline. T. New no-network Phase81-or-later integration is defined. U. Historical non-inference is preserved.

### APPROVE activity scope and record

This approval changes only `docs/CURRENT_PHASE.md` and `docs/LATEST_CODEX_REPORT.md`. It performs no production/test change, provider HTTP, Phase44, GET, acquisition, publication, synthetic/live preflight execution, fixture-delta creation, or staging of publication artifacts.

Provider HTTP / Phase44 / GET: 0 / 0 / 0

Authorization consumed: NO

Publication: NO

Next action after successful approval tracking: INDEPENDENT_REMOTE_VERIFICATION_BEFORE_PHASE80_EXECUTE
