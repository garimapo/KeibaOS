# Current Phase

## Identity

- Phase: `POST_V0_8_DAILY_REPLAY_64`
- Title: `Controlled NAR Diagnostic-Only Reacquisition`
- Base HEAD: `5b85d54a39c6b7d3e6c036cc0d479ba24e0a1797`
- Branch: `feature/post-v0.8-daily-replay`
- Required dependency: `POST_V0_8_DAILY_REPLAY_63` is formally complete at the matching integrated commit and tree `6ebbe16b0d56e86a237e28cde38c489fc81a5310`.

## Status and objective

- Formal Status: `APPROVED_FOR_CODEX`.
- Tracking State: `APPROVED_UNCONSUMED_TRACKED`.
- Design Review: `PHASE64_DIAGNOSTIC_ONLY_REACQUISITION_DESIGN_REVIEW_PASS`.
- Outcome: `APPROVED_DIAGNOSTIC_ONLY_REACQUISITION`.
- Project objective: `CONTROLLED_REACQUISITION_FOR_SAFE_ROOT_CAUSE_DIAGNOSTICS`.
- During APPROVE and approval-state tracking: provider HTTP `0`, Phase44 calls `0`, GET attempts `0`, `PHASE44_CALL_ABOUT_TO_ENTER` not written, and fixture/publication writes `0`.
- The sole future target is `NAR / 21 / 2025-01-01 / 6`, with `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`. It asserts neither historical availability/bytes/timing/cutoff nor market eligibility.

## Immutable prior state and future authority

- Phase57 remains `POST_AUTHORIZATION_STOP`; its outcome is `SOURCE_PROFILE_FIXTURE_BLOCKED`, authorization is `PHASE57_ACQUISITION_AUTHORIZATION_CONSUMED_FAIL_CLOSED`, and retry is `FORBIDDEN`. It cannot be restored, reused, renewed, transferred, or used for Phase44 again.
- Phase64 authorization before APPROVE: `NONE`. Issued authorization: `PHASE64_DIAGNOSTIC_ACQUISITION_AUTHORIZATION_UNCONSUMED`, bound to support HEAD `5b85d54a39c6b7d3e6c036cc0d479ba24e0a1797`, the frozen target, and this one diagnostic-only objective. It is target-specific, phase-specific, one-shot, and nontransferable; it is neither Phase57 nor Phase54 authority.
- Future authority is Phase44 only: one closed-bundle call maximum, DebaTable then RaceList, provider GET cap `2`. Retry, discovery, fallback, direct provider HTTP, alternate provider/target, manual requests, and partial bundles are forbidden.
- The only consumption boundary is `PHASE44_CALL_ABOUT_TO_ENTER` → canonical append → flush → fsync → exactly one Phase44 call. Before it, authorization is factually unconsumed; afterwards it is permanently fail-closed.
- `market_eligibility`, `positive_market_eligibility`, and `WHOLE_MEETING_CANCELLATION` remain `UNSUPPORTED`. No backdated live response is asserted.

## Phase63 authority and pre-live gates

- Explicit-root import inspection resolves Phase44, Phase50, Phase53 ordinary Profile-B, Phase56 Safety, and Phase63 recovery diagnostics only inside the authorized worktree.
- Phase63 provides exactly `PROFILE_B_RECOVERY_DIAGNOSTICS_RETAINED` and `PUBLICATION_SAFETY_RECOVERY_DIAGNOSTICS_RETAINED`; `JOURNAL_SCHEMA_VERSION = 1`, `MAX_RECORD_BYTES = 4096`, and `MAX_RETAINED_CANDIDATE_DETAILS = 8`. Historical v1 journals, including the Phase57 22-record blocked shape, remain tested/readable without optional recovery events.

All no-network gates must pass before consumption:

1. Worktree/branch/local/remote HEAD, empty index, no untracked paths, and clean tree.
2. Explicit-root authority binding; exact target construction; Phase44/50/53/56/63 imports.
3. Synthetic old-journal and recovery-event validation; recovery-order validation; worst-case record-size check; Phase63 Safety valid/impossible-state checks; Profile-B `<=8` and `>8` checks; Phase57 historical compatibility.
4. Generated preflight/live-child compilation; unique OS temporary directory; exact token check against `b"NAR_REACQUISITION_OBSERVABILITY_PREFLIGHT_PASS\\n"` with no stripping, normalization, CRLF, or text-mode conversion; cleanup and final clean-tree validation.

## Future live order and diagnostic retention

`PARENT_EXECUTION_PREPARED` → `LIVE_PROCESS_START` → `TARGET_CONSTRUCTED` → durable `PHASE44_CALL_ABOUT_TO_ENTER` → Phase44 Deba/RaceList transport, GET, response, and raw milestones → `CLOSED_BUNDLE_RETURNED` → both capture metadata records → `PROFILE_B_DIAGNOSTICS_RETAINED` → `PROFILE_B_RECOVERY_DIAGNOSTICS_RETAINED` → `IDENTITY_VERIFICATION_PASS` → `PUBLICATION_SAFETY_RECOVERY_DIAGNOSTICS_RETAINED` → normal Safety branch.

- Profile-B recovery uses exact RaceList bytes before cleanup and retains only its bounded schema: scope/candidate counts, completeness, at most eight ordered safe candidate projections, and safe-projection equality. It retains no row text or href/query value and selects no candidate.
- Safety recovery uses exact Deba/RaceList bytes and retains only ordered parser-stage tuples. It never replaces Phase56 Safety.
- Both recovery events use canonical append → flush → fsync before transient raw cleanup.
- Normal Phase56 Safety is unchanged: non-`SAFE` emits `PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED`; `SAFE` emits `SAFETY_PASS`. Ordinary Profile-B is unchanged and `PROFILE_B_QUALIFIED` is emitted only when its actual grammar qualifies.

## Exact terminal-outcome contract

Phase50 validates `LIVE_PROCESS_COMPLETE` against its fixed outcome allowlist but does not require publication milestones for `READY_FOR_REVIEW` and does not couple an outcome value to publication. The exact mapping is:

| Branch | Terminal evidence | Outcome |
| --- | --- | --- |
| Pre-boundary no-network gate failure | no live call; authorization factually unconsumed | no `LIVE_PROCESS_COMPLETE` |
| Post-boundary Phase44, bundle, metadata, identity, or recovery-integrity failure | retain available safe evidence; no publication | `RECOVERY_PREFLIGHT_BLOCKED` |
| Normal Safety non-`SAFE` | safety recovery and canonical blocked Safety evidence retained | `SOURCE_PROFILE_FIXTURE_BLOCKED` |
| Safety `SAFE`, ordinary Profile-B `BLOCKED` | `SAFETY_PASS` and ordinary/recovery Profile-B evidence retained | `SOURCE_PROFILE_FIXTURE_BLOCKED` |
| Safety `SAFE`, ordinary Profile-B `QUALIFIED` | all recovery, identity, capture, Safety-pass, and safe-final evidence retained; no publication | `READY_FOR_REVIEW` |

`READY_FOR_REVIEW` in the last branch means ready for diagnostic review only, never fixture publication. `SOURCE_PROFILE_FIXTURE_BLOCKED` is used only for a real unchanged Safety/Profile-B block; `RECOVERY_PREFLIGHT_BLOCKED` only for preflight, acquisition-integrity, or recovery failure. Existing Phase50 vocabulary is sufficient; no support phase is needed. Phase56 Profile-A is not required, because no manifest or publication path is entered.

## No-publication, safe-final, and cleanup contract

- The future run must never emit `PUBLICATION_BEGIN`, `RAW_FIXTURES_WRITTEN`, `MANIFEST_WRITTEN`, `DEDICATED_TEST_WRITTEN`, or `REGRESSIONS_PASS`; it must not create fixtures, manifest, or fixture test. Publication rollback is therefore unnecessary.
- Repository paths remain unchanged. Journal, generated source, streams, raw bytes, and safe-final output live only in a unique OS temporary directory; the child does not edit documentation.
- Canonical safe-final JSON contains only schema/version, run ID, starting HEAD, target, authorization final state, Phase44/GET counts, safe capture metadata, ordinary and recovery Profile-B results, Safety recovery, normal Safety result or Safety-pass fact, terminal evidence, journal SHA-256/safe records, parent validation, and cleanup status. It contains no raw HTML, arbitrary URL/query, credentials, cookies, or secrets.
- The parent independently validates one run, boundary durability, one Phase44 entry, at most two GETs, response/closed-bundle evidence, captures, ordinary/recovery Profile-B, identity, recovery/normal Safety, absence of publication milestones, outcome truthfulness, and no contradictions. Only after safe-final and parent validation may transient raw bytes be destroyed.

## Sufficiency and changed-provider-state handling

- Safety root-cause review requires each role’s exact `utf8_decode`, `strict_structure`, and `beautifulsoup_parse` tuple.
- Profile-B review requires scope/candidate count, completeness, bounded candidate details when count is at most eight, and safe-projection equality. More than eight candidates is valid but explicitly incomplete, never a grammar decision.
- The provider may differ from Phase57: Safety can pass or fail elsewhere; candidate count can differ; Profile-B can qualify. New hashes/lengths are current-acquisition evidence only and never prove historical identity.

## Approval readiness

| A. Phase63 formally complete | YES |
| B. Clean tracked baseline | YES |
| C. Exact target frozen | YES |
| D. Phase44 one-shot contract valid | YES |
| E. Phase63 recovery events available | YES |
| F. Pre-live gates complete | YES |
| G. Authorization boundary complete | YES |
| H. Evidence sufficiency defined | YES |
| I. Safe-final design complete | YES |
| J. No-publication contract complete | YES |
| K. Truthful Phase50 terminal mapping complete | YES |
| L. Additional support phase required | NO |

## Scope and stop condition

- PREPARE may modify only `docs/CURRENT_PHASE.md` and `docs/LATEST_CODEX_REPORT.md`.
- No Phase44, Phase50, Phase63, Phase53, Phase56, Phase60, Phase61, fixture, `.gitattributes`, database, log, test, authorization, or network change is authorized.
- Phase44 changes required: `NO`; Phase50 changes required: `NO`; Phase63 changes required: `NO`.
- Phase54 remains `PHASE54_AUTHORIZATION_UNCONSUMED_BUT_UNUSABLE_FOR_V2`; Phase41 remains `DESIGN_BLOCKED`. Open constraints remain `COMBINATION_EV_REQUIRES_MARKET_ODDS_CAPTURE` and `NAR_MARKET_ELIGIBILITY_REQUIRES_INDEPENDENT_ENTRY_STATUS_CAPTURE`.

This docs-only tracking commit does not change executable acquisition, observability, or publication behavior; authorization remains bound to support HEAD `5b85d54a39c6b7d3e6c036cc0d479ba24e0a1797`. Independent remote verification is required before execution. Do not execute, acquire, or consume authorization in this integration.

## Next recommended action

`EXECUTE_DIAGNOSTIC_ONE_SHOT_AFTER_INDEPENDENT_REMOTE_VERIFICATION`.
