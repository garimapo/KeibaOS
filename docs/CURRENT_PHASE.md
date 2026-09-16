# Current Phase

## Phase

`POST_V0_8_DAILY_REPLAY_61`

## Title

Phase50 v2 Dedicated-Test Path Observability Compatibility Support

## Status

`INTEGRATED_PENDING_REMOTE_VERIFICATION`

## Design review

`PHASE61_DESIGN_REVIEW_PASS`

## Outcome

`IMPLEMENTED_PHASE50_V2_DEDICATED_TEST_PATH_COMPATIBILITY`

## Approval

- Formal status before execution: `APPROVED_FOR_CODEX`.
- Design review: `PHASE61_DESIGN_REVIEW_PASS`.
- Confirmed blocker: `PHASE57_V2_DEDICATED_TEST_OBSERVABILITY_PATH_INCOMPATIBLE`.
- Approved compatibility: the exact closed two-path union only.
- Provider HTTP: `0`; Phase44: not entered.
- Phase57 authorization remains factually `PHASE57_ACQUISITION_AUTHORIZATION_UNCONSUMED`; its future usability is `REAPPROVAL_REQUIRED_AFTER_PHASE61`.
- Review: `PASS_FOR_INTEGRATION`.
- Current integration state: `INTEGRATED_PENDING_REMOTE_VERIFICATION`; remote verification is required and Phase61 is not formally complete.

## Base and authorized worktree

- Authorized worktree: `C:\Users\garim\Desktop\KeibaOS-post-v0.8`.
- Branch and base/local/remote HEAD: `feature/post-v0.8-daily-replay` / `d14afa262900c8a1fb5f2c25ca8ef2867d5f52c9`.
- PREPARE began with a clean worktree, empty index, and no untracked files.
- This is a no-network documentation-only design. It does not issue or consume an acquisition authorization, invoke Phase44, write fixtures, stage, commit, or push.

## Triggering pre-authorization stop

Phase57 stopped at `RECOVERY_PREFLIGHT_BLOCKED` before authorization consumption. Provider HTTP, Phase44 calls, GET attempts, and `PHASE44_CALL_ABOUT_TO_ENTER` records were all `0`/absent. The factual state remains `PHASE57_ACQUISITION_AUTHORIZATION_UNCONSUMED`.

The exact incompatibility is `PHASE57_V2_DEDICATED_TEST_OBSERVABILITY_PATH_INCOMPATIBLE`: Phase60 prospectively requires `tests/test_nar_race_entry_status_source_profile_v2_fixtures.py`, while the current Phase50 validator permits only `tests/test_nar_race_entry_status_source_profile_fixtures.py` for `DEDICATED_TEST_WRITTEN`.

## Approved design boundary for review

Phase61 is the smallest Phase50-only lexical compatibility change. It changes only the exact accepted value set for `test_path`; it does not make Phase50 a Phase60 planner or a publication validator.

The closed union is exactly:

1. Historical path: `tests/test_nar_race_entry_status_source_profile_fixtures.py`
2. Phase60-authorized v2 path: `tests/test_nar_race_entry_status_source_profile_v2_fixtures.py`

The implementation must use an exact local allowlist, not a pattern or a version parser. It must reject every third path, including v3/suffix/prefix variants, arbitrary `tests/*.py`, absolute and drive-prefixed paths, backslashes, whitespace, control characters, NUL, traversal, renamed files, and caller-supplied paths.

Historical acceptance remains unchanged and means only a structurally canonical historical observability value. Acceptance of the v2 string means only `STRUCTURALLY_APPROVED_DEDICATED_TEST_PATH`; it does not establish test correctness, fixture qualification, manifest validity, publication success, or market eligibility. Phase60 remains the sole tracked authority for the v2 test path.

## Event, schema, and semantic reconstruction

- `DEDICATED_TEST_WRITTEN` remains the exact milestone.
- Its exact closed detail-key set remains `test_path`; no version, identity, schema, or additional metadata is added.
- `JOURNAL_SCHEMA_VERSION` remains `1`; no migration is needed because the milestone and detail-key set are unchanged and the historical value remains valid.
- `MAX_STRING_BYTES` remains `512`; the historical path is 59 UTF-8 bytes and the v2 path is 62 UTF-8 bytes.
- Representative complete canonical JSONL records, including LF, are 322 bytes for the historical path and 325 bytes for the v2 path, both below `MAX_RECORD_BYTES = 4096`.
- `_safe_string` control-character and UTF-8 bounds remain in force.

The current semantic validator applies no cross-event or manifest-version binding to `DEDICATED_TEST_WRITTEN`; it only normalizes each record, checks exact detail keys, validates semantic milestone order, and applies the lexical `test_path` restriction. Phase61 therefore remains lexical only. It must not invent a manifest/test-path version correlation. Phase59 keeps its unchanged `MANIFEST_WRITTEN` v1/v1 and v2/v2 acceptance, mixed-version rejection, exact key set, and identity validation.

ObservationMilestone ordering is unchanged, in particular:

`RAW_FIXTURES_WRITTEN` → `MANIFEST_WRITTEN` → `DEDICATED_TEST_WRITTEN` → `REGRESSIONS_PASS`.

## Preserved authorities and invariants

Phase61 must not change the semantics or validators for `PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED`, `PROFILE_A_BLOCKED_DIAGNOSTICS_RETAINED`, `SAFETY_PASS`, `PROFILE_A_QUALIFIED`, `PROFILE_B_DIAGNOSTICS_RETAINED`, `MANIFEST_WRITTEN`, Phase59 fixture/qualification identities, or `LIVE_PROCESS_COMPLETE` outcomes. Phase60’s publication-plan authority and `.gitattributes` binary rule are unchanged. No Phase44, Phase53, Phase56, Phase60, fixture, dedicated fixture-test, or `.gitattributes` change is in scope.

## Phase57 authorization after this support phase

The existing authorization is factually unconsumed, but it was approved against `d14afa262900c8a1fb5f2c25ca8ef2867d5f52c9`. Phase61 integration changes the support baseline and HEAD. No shorter tracked vocabulary expresses this distinction, so the frozen state is:

`PHASE57_EXISTING_AUTHORIZATION_FACTUALLY_UNCONSUMED_BUT_REAPPROVAL_REQUIRED_AFTER_PHASE61`

This does not call the authorization consumed. After Phase61 is formally complete, Phase57 must be re-PREPAREd and re-reviewed against the new HEAD; only a new explicit Phase57 approval may issue a new one-shot authorization. Phase54 remains `PHASE54_AUTHORIZATION_UNCONSUMED_BUT_UNUSABLE_FOR_V2`.

## Future implementation contract

Allowed files, exactly four:

1. `scripts/simulation/nar_race_entry_status_reacquisition_observability.py`
2. `tests/test_nar_race_entry_status_reacquisition_observability.py`
3. `docs/CURRENT_PHASE.md`
4. `docs/LATEST_CODEX_REPORT.md`

Forbidden: Phase44/53/56/60 files, `.gitattributes`, fixtures, the v2 dedicated test, database, logs, generated artifacts, provider HTTP, Phase44 entry, and authorization action. If another path or a schema/event/order semantic change is required, stop with `DESIGN_BLOCKED_SCOPE_EXPANSION_REQUIRED`.

Focused tests must prove both exact paths accepted; every listed malformed/third-path class rejected; missing and extra detail keys rejected; historical and v2 canonical journal round trips; record and string bounds; unchanged schema version and enum order; v2/v2 manifest acceptance and mixed rejection; unchanged Phase58 blocked events, completion vocabulary, and binary preflight token. Execute later in this order: focused observability tests, relevant Phase50/Phase57/Phase60 no-network regression, then one full repository suite when otherwise ready.

## Proposed success state

`POST_V0_8_DAILY_REPLAY_61` has reached `READY_FOR_REVIEW` with outcome `IMPLEMENTED_PHASE50_V2_DEDICATED_TEST_PATH_COMPATIBILITY`. The exact two-path union, all preserved contracts, focused and relevant regression tests, one full suite, no network/Phase44 entry, exact four-path delta, empty index, and `git diff --check` pass are confirmed.

## Implementation and verification evidence

- Production change: one local immutable `_DEDICATED_TEST_PATHS` allowlist and membership enforcement in the existing `test_path` branch, after unchanged `_safe_string` validation.
- Accepted paths are exactly the historical path and Phase60’s v2 path; no third path or permissive matching is accepted.
- `DEDICATED_TEST_WRITTEN`, its exact `test_path` key, `JOURNAL_SCHEMA_VERSION = 1`, milestone order, `MAX_*` bounds, `_ALLOWED_OUTCOMES`, and preflight token are unchanged.
- Phase59 manifest identity validators and same-version enforcement are unchanged; v1/v1 and v2/v2 pass, while v1/v2 and v2/v1 reject.
- Phase58 Safety/Profile-A blocked events and Phase60 publication-plan/binary-preservation authority are unchanged.
- Focused observability: `190 passed`.
- Related Phase53/56/60 no-network regression: `98 passed`.
- Full repository suite: `3889 passed, 2841 subtests passed`.
- Static audit: no new network, HTTP, socket, provider-body, database, Git-mutation, authorization-mutation, Phase60-mutation, or `MARKET_ELIGIBLE` behavior.
- Provider HTTP: `0`; Phase44 live acquisition: not entered.
- Integration preserves the exact two-path union, historical compatibility, no-third-path rejection, Phase58/59/60 invariants, and the factual-but-not-reusable Phase57 authorization state. No fixture, `.gitattributes`, authorization, or live-acquisition action occurred.

## Persistent constraints

- Phase57 live execution is blocked during Phase61; no authorization action occurs.
- Phase41: `DESIGN_BLOCKED`.
- `market_eligibility = UNSUPPORTED`; `positive_market_eligibility = UNSUPPORTED`; `WHOLE_MEETING_CANCELLATION = UNSUPPORTED`.
- Open: `COMBINATION_EV_REQUIRES_MARKET_ODDS_CAPTURE`; `NAR_MARKET_ELIGIBILITY_REQUIRES_INDEPENDENT_ENTRY_STATUS_CAPTURE`.
- No observability path acceptance establishes `MARKET_ELIGIBLE`.
