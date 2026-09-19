# Current Phase

## Identity and baseline

- Phase: `POST_V0_8_DAILY_REPLAY_67`
- Title: `Controlled Structural Diagnostic One-Shot Reacquisition`
- Base HEAD: `d49adc20cd75b7975947cdc956bdfbf293852ef6`
- Branch: `feature/post-v0.8-daily-replay`
- Formal Status: `APPROVED_FOR_CODEX`
- Design Review: `PHASE67_STRUCTURAL_DIAGNOSTIC_DESIGN_REVIEW_PASS`
- Outcome: `APPROVED_STRUCTURAL_DIAGNOSTIC_ONE_SHOT_REACQUISITION`
- Diagnostic Contract: `STRUCTURAL_DIAGNOSTIC_TERMINAL_CONTRACT_COMPLETE`
- Authorization: `PHASE67_STRUCTURAL_DIAGNOSTIC_ACQUISITION_AUTHORIZATION_UNCONSUMED`
- Support HEAD: `d49adc20cd75b7975947cdc956bdfbf293852ef6`
- Authorization Tracking State: `APPROVED_UNCONSUMED_TRACKED`
- Allowed files for APPROVE: `docs/CURRENT_PHASE.md`, `docs/LATEST_CODEX_REPORT.md` only. No production code, tests, fixture, live acquisition, staging, commit, or push is authorized.

Phase66 is treated as `FORMALLY_COMPLETE` for this Phase67 dependency at integrated commit `d49adc20cd75b7975947cdc956bdfbf293852ef6`, tree `3ada2012ffc285b12dfafbed68e23b081dbef85d`. The clean tracked baseline and required support are present. Phase64 remains `FORMALLY_COMPLETE_DIAGNOSTIC_RUN`, interpreted only as `DIAGNOSTIC_OBJECTIVE_COMPLETED_WITH_SOURCE_PROFILE_BLOCK`.

## Objective and immutable limits

- Objective: `CONTROLLED_REACQUISITION_FOR_STRICT_STRUCTURE_AND_CANDIDATE_ANCESTRY_DIAGNOSTICS`.
- Frozen target: NAR / `21` / `2025-01-01` / `6`.
- Semantics: `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`. It establishes neither historical bytes, availability, timing, cutoff, nor market eligibility.
- `market_eligibility`, `positive_market_eligibility`, and `WHOLE_MEETING_CANCELLATION` remain `UNSUPPORTED`.
- Phase57 and Phase64 authorization states are both `CONSUMED_FAIL_CLOSED`; neither may be reused. This APPROVE issues `PHASE67_STRUCTURAL_DIAGNOSTIC_ACQUISITION_AUTHORIZATION_UNCONSUMED`, bound only to this phase, target, purpose, and support HEAD. It is one-shot, nontransferable, and nonrenewable after consumption.
- The reserved consumed token is `PHASE67_STRUCTURAL_DIAGNOSTIC_ACQUISITION_AUTHORIZATION_CONSUMED_FAIL_CLOSED`. This APPROVE does not cross the consumption boundary.
- One future Phase44 closed-bundle call at most; provider order is DebaTable then RaceList; provider GET attempts at most two. No retry, second call, alternate provider/target, fallback, discovery request, direct HTTP, or partial bundle acceptance.

The only future consumption boundary is `PHASE44_CALL_ABOUT_TO_ENTER` → canonical journal append → flush → fsync → exactly one Phase44 call. Before durable fsync authorization remains unconsumed; after it, it is permanently consumed fail-closed.

## Confirmed support and pre-live contract

Current support provides Phase63 recovery, Phase66 strict API `diagnose_nar_race_entry_status_strict_structure_recovery`, Phase66 ancestry API `diagnose_nar_race_entry_status_profile_b_candidate_ancestry_recovery`, and milestones `PROFILE_B_CANDIDATE_ANCESTRY_RECOVERY_DIAGNOSTICS_RETAINED` and `STRICT_STRUCTURE_RECOVERY_DIAGNOSTICS_RETAINED`.

- `JOURNAL_SCHEMA_VERSION = 1`; `MAX_RECORD_BYTES = 4096`.
- Measured maximum records including LF: strict `837`, ancestry `2598`.
- Phase50 retains append → flush → fsync semantics and accepts the existing terminal outcomes: `READY_FOR_REVIEW`, `SOURCE_PROFILE_FIXTURE_BLOCKED`, `RECOVERY_PREFLIGHT_BLOCKED`, `SYNTHETIC_SUCCESS`, and `SYNTHETIC_FAILURE`.

Before future consumption, an external, repository-free executor must pass all of these without provider I/O: exact worktree/branch/local/remote HEAD and clean-state checks; exact module-origin bindings for Phase44, Phase50, Phase53, Phase56 Safety, Phase63, and Phase66; exact target construction; historical v1 plus synthetic Phase57 22-record and Phase64 24-record compatibility; synthetic Phase63/66 payload and event-order validation; Phase63↔66 ancestry and strict consistency checks; both record-size checks; legal/illegal strict and ancestry state checks; <=8 and >8 candidate behavior; generated preflight/live source compilation; unique OS temp path outside the repository; transient-cleanup check; and final clean-tree check.

The preflight token is byte-for-byte `b"NAR_REACQUISITION_OBSERVABILITY_PREFLIGHT_PASS\n"`. CRLF, stripping, normalization, extra bytes, or missing LF fail preflight. Provider HTTP/Phase44/GET count is zero through every gate.

## Future diagnostic sequence

`PARENT_EXECUTION_PREPARED` → `LIVE_PROCESS_START` → `TARGET_CONSTRUCTED` → durable `PHASE44_CALL_ABOUT_TO_ENTER` → Phase44 function/transport/GET/response/raw milestones for DebaTable and then RaceList → `CLOSED_BUNDLE_RETURNED` → both capture metadata events → `PROFILE_B_DIAGNOSTICS_RETAINED` → `PROFILE_B_RECOVERY_DIAGNOSTICS_RETAINED` → `PROFILE_B_CANDIDATE_ANCESTRY_RECOVERY_DIAGNOSTICS_RETAINED` → `IDENTITY_VERIFICATION_PASS` → `PUBLICATION_SAFETY_RECOVERY_DIAGNOSTICS_RETAINED` → `STRICT_STRUCTURE_RECOVERY_DIAGNOSTICS_RETAINED` → exactly one normal Safety branch → `LIVE_PROCESS_COMPLETE` → `PARENT_EVIDENCE_VALIDATION_PASS` → `PARENT_CLEANUP_COMPLETE`.

Ordinary Phase53 Profile-B remains authoritative and unchanged. Phase63 Profile-B recovery and Phase66 ancestry must be calculated from the exact same RaceList bytes before identity; their target, scope count, candidate count, and completeness must agree. Ancestry retains only candidate ordinal, bounded table role, changeInfo boolean, bounded table depth, and direct-schedule boolean; it never selects a candidate.

After identity PASS, Phase63 Safety recovery and Phase66 strict recovery are calculated from the exact same DebaTable/RaceList bytes before normal Safety. Phase66 records only role, failure kind, event index, stack depth, bounded enum/null tags, and tolerant parse. `failure_kind=PASS` requires Phase63 UTF-8 PASS, strict PASS, and matching DOM-parse result. Any non-PASS strict failure requires Phase63 UTF-8 PASS and strict FAIL; its Phase63 DOM stage remains `NOT_REACHED`. Contradiction is a post-consumption integrity failure.

Phase56 Safety remains unchanged and is evaluated after all recovery records are durable. Phase-A is `NOT_REQUIRED` under the current terminal contract and must not run. No Profile-A, publication, fixture, manifest, dedicated-test, regression, or rollback milestone is permitted.

## Terminal mapping, safe-final, and cleanup

- Pre-consumption gate failure: no `LIVE_PROCESS_COMPLETE`; authorization remains unconsumed.
- Post-consumption acquisition, identity, recovery, parent-integrity, or safe-final failure: `RECOVERY_PREFLIGHT_BLOCKED`.
- Normal Safety non-SAFE: `SOURCE_PROFILE_FIXTURE_BLOCKED`.
- Safety SAFE plus ordinary Profile-B BLOCKED: `SOURCE_PROFILE_FIXTURE_BLOCKED`.
- Safety SAFE plus ordinary Profile-B QUALIFIED: `READY_FOR_REVIEW`, meaning only `STRUCTURAL_DIAGNOSTIC_EVIDENCE_READY_FOR_CHATGPT_REVIEW`, never publication.

The terminal mapping is accepted by the current Phase50 semantic validator: outcome vocabulary is allowlisted but not tied to publication milestones. Phase67 parent validation additionally enforces the mapping, absence of Profile-A/publication milestones, authorization boundary, transport caps, complete bundle/capture identity, all ordinary/recovery evidence, cross-consistency, normal Safety branch, and repository nonmutation.

The external canonical safe-final JSON may retain only phase/revision, run ID, starting HEAD, target, acquisition semantics, authorization state, bounded transport/capture metadata and closed-bundle identity, ordinary Profile-B, Phase63 recovery, Phase66 ancestry, identity result, Phase63 Safety recovery, Phase66 strict recovery, normal Safety result or SAFETY_PASS fact, terminal outcome, `publication_began=false`, journal digest/canonical safe records, parent validation, and cleanup. It may never retain raw HTML/tag strings/class values/URLs/queries/cookies/credentials/provider text/exception text.

Raw data and all generated child, journal, output, and cache artifacts remain outside the repository. Destruction is permitted only after all recovery and normal safe evidence, terminal evidence, validated safe-final, and parent validation are durable. The provider may have changed; new SHA/length may differ. Equality may be reported only as `CURRENT_ACQUISITION_BYTES_REPRODUCED` and never as historical identity or availability.

## Readiness and persistent constraints

- A Phase66 formally complete: YES.
- B clean baseline: YES.
- C exact target frozen: YES.
- D Phase44 one-shot cap frozen: YES.
- E Phase63 recovery support available: YES.
- F Phase66 structural support available: YES.
- G pre-live gates complete as a reviewed design: YES.
- H consumption boundary complete: YES.
- I terminal mapping truthful: YES.
- J safe-final design complete: YES.
- K parent validation contract complete: YES.
- L publication prohibition complete: YES.
- M additional support phase required: NO.

Current code is sufficient without changes to Phase44, Phase50, Phase53, Phase56, Phase63, or Phase66. No tracked safe-evidence artifact is needed. Phase57 remains `POST_AUTHORIZATION_STOP`; Phase64 remains formally complete diagnostic-only; Phase54 remains unusable for v2; Phase41 remains `DESIGN_BLOCKED`.

## Stop condition

This APPROVE does not acquire, enter Phase44, write `PHASE44_CALL_ABOUT_TO_ENTER`, consume authorization, or alter code/tests. Provider HTTP, Phase44 calls, and GET attempts are `0`; fixture/publication writes are `0`; index remains empty. The authorization is still unconsumed.

## Next permitted action

Independent remote verification is mandatory before Phase67 execution. This tracked authorization state does not start the acquisition or cross its consumption boundary.
