# Current Phase

## Phase72 approved authorization

- Phase: `POST_V0_8_DAILY_REPLAY_72`
- Title: `Reauthorized Fresh-Current Validation After Phase50 Profile-A V3 Contract Repair`
- Branch: `feature/post-v0.8-daily-replay`
- Current / executable support HEAD: `b29e98259a3186f905220b0d66eae24597458059`
- Support tree: `04acbe48a554a1dd16548d4df8449f1775e3acbf`
- Approval Base HEAD: `b29e98259a3186f905220b0d66eae24597458059`
- State: `APPROVED_UNCONSUMED_TRACKED`
- Authorization Tracking State: `APPROVED_UNCONSUMED_TRACKED`
- Formal Status: `APPROVED_FOR_CODEX`
- Design Review: `PHASE72_VALIDATION_DESIGN_REVIEW_PASS`
- Outcome: `APPROVED_REAUTHORIZED_VERSIONED_SOURCE_PROFILE_VALIDATION`
- Validation Contract: `REAUTHORIZED_VERSIONED_SOURCE_PROFILE_VALIDATION_CONTRACT_COMPLETE`
- Allowed files in this preparation: `docs/CURRENT_PHASE.md`, `docs/LATEST_CODEX_REPORT.md`
- Provider HTTP / Phase44 / GET: `0 / 0 / 0`
- Authorization: `PHASE72_VERSIONED_SOURCE_PROFILE_VALIDATION_AUTHORIZATION_UNCONSUMED`
- Authorization consumed: `NO`
- Boundary: `NOT WRITTEN`

## Frozen predecessor states

- Phase71 is `FORMALLY_COMPLETE`, with support repair `PHASE50_PROFILE_A_V3_TARGET_CONTRACT_REPAIRED` and review `PHASE71_IMPLEMENTATION_REMOTE_VERIFICATION_PASS`.
- Phase70 is `PRE_AUTHORIZATION_STOP` with outcome `NOT_PRODUCED_PREBOUNDARY`, boundary absent, Provider HTTP / Phase44 / GET all `0`.
- Phase70 authorization remains `PHASE70_VERSIONED_SOURCE_PROFILE_VALIDATION_AUTHORIZATION_UNCONSUMED`, but its execution eligibility is `INVALIDATED_BY_EXECUTABLE_SUPPORT_HEAD_CHANGE`. It must never be reused, consumed, rebound, transferred, or treated as Phase72 authority.

## Phase72 authorization

Issued authorization:

- `PHASE72_VERSIONED_SOURCE_PROFILE_VALIDATION_AUTHORIZATION_UNCONSUMED`
- `PHASE72_VERSIONED_SOURCE_PROFILE_VALIDATION_AUTHORIZATION_CONSUMED_FAIL_CLOSED`

The authorization is newly issued for Phase72 and binds exactly to target `NAR / 21 / 2025-01-01 / 6`, purpose `FRESH_CURRENT_VALIDATION_AFTER_PHASE71_PROFILE_A_V3_TARGET_REPAIR`, semantics `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`, and support HEAD `b29e98259a3186f905220b0d66eae24597458059`. It is one-shot, phase-specific, target-specific, purpose-specific, support-HEAD-specific, nontransferable, and nonrenewable after consumption.

## Qualification and Phase50 authority

Future qualification uses only Profile-B v2 (`diagnose_nar_race_entry_status_profile_b_v2`, schema `2`), Profile-A v3 (`diagnose_nar_race_entry_status_profile_a_v3`, schema `3`), and Safety v3 (`assess_nar_race_entry_status_raw_fixture_publication_safety_v3`, schema `3`). Phase63 and Phase66 remain supplemental only.

Phase50 retains journal schema `1` and supports Profile-B `{1,2}`, blocked Profile-A `{2,3}`, blocked Safety `{2,3}`, and fixture/qualification identities v1/v2/v3. Schema-2 blocked Profile-A is historical and targetless; target is forbidden. Schema-3 blocked Profile-A requires the exact canonical target and Phase50 requires it to equal `TARGET_CONSTRUCTED` exactly.

## Future pre-live design

The later runner is generated once outside the repository, compiled once, and used unchanged for synthetic and live modes. It retains one capture-metadata adapter and one shared post-acquisition processor. It runs under a fresh `-I -B` interpreter with explicit repository bootstrap, KeibaAI exclusion, no preloaded `scripts` modules, package-path exclusivity, module-origin checks, and the exact LF preflight token `NAR_REACQUISITION_OBSERVABILITY_PREFLIGHT_PASS\n`.

The synthetic main path must exercise Profile-B v2, Phase63 recovery, Phase66 ancestry, structural consistency, identity, Phase63 Safety recovery, Phase66 strict recovery, strict consistency, Safety v3 SAFE, Profile-A v3 QUALIFIED, Profile-B qualification, and real Phase50 reconstruction without network or publication.

Two separate synthetic blocked probes are mandatory: a schema-3 non-SAFE Safety payload and an actual `ProfileADiagnosticsV3` blocked canonical payload, passed directly to Phase50 without stripping its target. The latter must retain schema `3`, retain the target, equal `TARGET_CONSTRUCTED`, reconstruct semantically, and establish `PHASE71_PROFILE_A_V3_TARGET_CONTRACT_INTEGRATION_PASS`.

Required gates are:

- `PROFILE_B_V2_DRY_RUN_PASS`
- `PROFILE_A_V3_DRY_RUN_PASS`
- `SAFETY_V3_DRY_RUN_PASS`
- `PHASE50_VERSIONED_PAYLOAD_DRY_RUN_PASS`
- `PHASE50_SAFETY_V3_BLOCKED_PAYLOAD_PASS`
- `PHASE50_PROFILE_A_V3_BLOCKED_PAYLOAD_PASS`
- `PHASE71_PROFILE_A_V3_TARGET_CONTRACT_INTEGRATION_PASS`
- `RUNNER_FULL_VERSIONED_POST_ACQUISITION_DRY_RUN_PASS`
- `DRY_RUN_NO_NETWORK_PASS`
- `DRY_RUN_LIVE_LOGIC_PARITY_PASS`
- `CAPTURE_METADATA_EXACT_11_KEYS_PASS`
- `CLOSED_BUNDLE_IDENTITY_PROPAGATION_PASS`

## Future live bounds and terminal contract

Only after all gates pass may a future real journal durably append `PHASE44_CALL_ABOUT_TO_ENTER`, flush, and fsync. That is the sole consumption boundary. Phase44 is capped at `1`; Deba GET at `1`; RaceList GET at `1`; total GET at `2`, in DebaTable then RaceList order, with no retry or fallback.

Capture metadata retains the exact eleven-key contract and both records use `closed_bundle_identity = bundle.bundle_id`. Publication remains forbidden. The external safe-final remains bounded; cleanup removes raw captures, journals, runner, synthetic/probe material, streams, and caches after parent validation. Current-byte reproduction never establishes historical availability, state, timing, or market eligibility.

Expected only, not assumed: Profile-B v2 `QUALIFIED`, Profile-A v3 `QUALIFIED`, Safety v3 `SAFE`. Terminal mapping remains `RECOVERY_PREFLIGHT_BLOCKED`, `SOURCE_PROFILE_FIXTURE_BLOCKED`, or `READY_FOR_REVIEW` as truthfully determined. Market eligibility remains `UNSUPPORTED`.

## Readiness

All readiness items A–R are `YES`: Phase71 review/support is frozen; Phase70 is unconsumed but unusable; Phase72 identity and target are frozen; V2/V3 authority and the Phase50 target repair are confirmed; actual V3 blocked-payload testing and the repair-specific gate are specified; synthetic, runner, isolation, boundary, cap, publication, and no-new-support constraints are complete.

## Approval effect and stop condition

During this approval, Provider HTTP, Phase44, and GET are `0`; synthetic and live execution are `NOT RUN`; the boundary is `NOT WRITTEN`; authorization remains unconsumed. No staged, committed, or pushed change is permitted in this approval.

Next permitted action after integration: `INDEPENDENT_REMOTE_VERIFICATION_BEFORE_PHASE72_EXECUTE`.
