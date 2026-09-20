# Current Phase

## Phase70 approved authorization

- Phase: `POST_V0_8_DAILY_REPLAY_70`
- Title: `Fresh-Current Validation of Versioned NAR Source Profile Authority`
- Branch: `feature/post-v0.8-daily-replay`
- Starting and executable support HEAD: `79d6faaa30a54840232c0b73cd0e4ce1451a088e`
- Approval Base HEAD: `79d6faaa30a54840232c0b73cd0e4ce1451a088e`
- Executable Support HEAD: `79d6faaa30a54840232c0b73cd0e4ce1451a088e`
- State: `APPROVED_UNCONSUMED_TRACKED`
- Authorization Tracking State: `APPROVED_UNCONSUMED_TRACKED`
- Formal Status: `APPROVED_FOR_CODEX`
- Design Review: `PHASE70_VALIDATION_DESIGN_REVIEW_PASS`
- Outcome: `APPROVED_VERSIONED_SOURCE_PROFILE_FRESH_CURRENT_VALIDATION`
- Validation Contract: `VERSIONED_SOURCE_PROFILE_FRESH_CURRENT_VALIDATION_CONTRACT_COMPLETE`
- Allowed files during this authorization record: `docs/CURRENT_PHASE.md`, `docs/LATEST_CODEX_REPORT.md` only.

Phase69 is `FORMALLY_COMPLETE`; its remote implementation verification is `PHASE69_IMPLEMENTATION_REMOTE_VERIFICATION_PASS`. Phase70 requires no production, test, Phase63, or Phase66 modification. Authorization is issued but has not been consumed: `PHASE70_VERSIONED_SOURCE_PROFILE_VALIDATION_AUTHORIZATION_UNCONSUMED`.

## Frozen target and authority

The sole future target is `NAR / 21 / 2025-01-01 / 6` with semantics `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`. This means only a current acquisition concerning the historical target; it does not establish 2025 source bytes, historical availability, timing, provider state, or market eligibility.

The future qualification authorities are exclusively:

- Profile-B v2: `diagnose_nar_race_entry_status_profile_b_v2`, exact `ProfileBDiagnosticsV2`, schema `2`.
- Profile-A v3: `diagnose_nar_race_entry_status_profile_a_v3`, exact `ProfileADiagnosticsV3`, schema `3`.
- Safety v3: `assess_nar_race_entry_status_raw_fixture_publication_safety_v3`, exact `RawFixturePublicationSafetyV3`, schema `3`.

Legacy V1/V2 results may be retained only as optional bounded comparison evidence and never as Phase70 qualification authority. Phase63 and Phase66 remain recommended supplemental recovery/consistency authorities only; they cannot override V2/V3 results.

## Expected, not assumed, fresh results

The expected-but-not-assumed validation outcome is Profile-B v2 `QUALIFIED`, Profile-A v3 `QUALIFIED`, and Safety v3 `SAFE`. In particular, Profile-B v2 is expected to count only the direct schedule-domain candidate and Profile-A v3 is expected not to treat the historical Deba nesting mismatch as a qualification prerequisite. Safety v3 is expected to complete all five nesting-independent categories. Every actual result, including any non-pass, must be retained truthfully without forced qualification.

## Future no-network preflight and shared runner

The external runner must be generated once outside the repository, compiled before use, and used byte-for-byte unchanged for a synthetic no-network dry run and then, only if approved later, real live mode. It must retain one shared capture-metadata adapter and one shared post-acquisition processor; dry and live modes may differ only in how their closed bundle is obtained.

The synthetic mode must use the new V2/V3 authorities and exercise Profile-B v2, Phase63 Profile-B recovery, Phase66 ancestry, ancestry consistency, identity, Phase63 Safety recovery, Phase66 strict recovery, strict consistency, Safety v3, Profile-A v3, terminal mapping, and Phase50 reconstruction. It is structurally forbidden from calling Phase44, transport, provider URLs, or any network path.

Required future gates are:

- `PROFILE_B_V2_DRY_RUN_PASS`
- `PROFILE_A_V3_DRY_RUN_PASS`
- `SAFETY_V3_DRY_RUN_PASS`
- `PHASE50_VERSIONED_PAYLOAD_DRY_RUN_PASS`
- `PHASE50_SAFETY_V3_BLOCKED_PAYLOAD_PASS`
- `PHASE50_PROFILE_A_V3_BLOCKED_PAYLOAD_PASS`
- `RUNNER_FULL_VERSIONED_POST_ACQUISITION_DRY_RUN_PASS`
- `DRY_RUN_NO_NETWORK_PASS`
- `DRY_RUN_LIVE_LOGIC_PARITY_PASS`
- `CAPTURE_METADATA_EXACT_11_KEYS_PASS`
- `CLOSED_BUNDLE_IDENTITY_PROPAGATION_PASS`

The existing hardened execution controls remain required: a fresh `-I -B` interpreter, explicit authorized-worktree bootstrap, exclusion of KeibaAI, no preloaded `scripts` modules, package-path/module-origin exclusivity, and native Git exit-code checks before evaluating output cardinality. No `git fetch` is permitted.

## Future acquisition and evidence contract

The issued authorization is bound exactly to Phase70, target `NAR / 21 / 2025-01-01 / 6`, purpose `FRESH_CURRENT_VALIDATION_OF_VERSIONED_NAR_SOURCE_PROFILE_AUTHORITY`, semantics `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`, and executable support HEAD `79d6faaa30a54840232c0b73cd0e4ce1451a088e`. It is one-shot, nontransferable, and nonrenewable after consumption:

- `PHASE70_VERSIONED_SOURCE_PROFILE_VALIDATION_AUTHORIZATION_UNCONSUMED`
- `PHASE70_VERSIONED_SOURCE_PROFILE_VALIDATION_AUTHORIZATION_CONSUMED_FAIL_CLOSED`

Only a future real journal boundary may consume authorization:

`PHASE44_CALL_ABOUT_TO_ENTER` → canonical append → flush → fsync → one Phase44 call.

The cap is Phase44 `1`; DebaTable GET `1`; RaceList GET `1`; total GET `2`; order is DebaTable then RaceList; no retry, fallback, alternate target, or alternate provider is allowed after the durable boundary.

In addition to the main synthetic successful path, two separate no-network synthetic probes are mandatory before the boundary. One must retain a legitimate schema-3 non-SAFE `RawFixturePublicationSafetyV3` through `PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED`; the other must retain a legitimate schema-3 blocked `ProfileADiagnosticsV3` through `PROFILE_A_BLOCKED_DIAGNOSTICS_RETAINED`. Both must reconstruct through real Phase50 with incoming schema version `3`, without normalization. Their journals and data are synthetic, separate from the future live journal, and deleted after validation.

Future retained progression is:

`CLOSED_BUNDLE_RETURNED` → capture metadata → Profile-B v2 diagnostics → Phase63 Profile-B recovery → Phase66 ancestry → ancestry consistency → identity → Phase63 Safety recovery → Phase66 strict recovery → strict consistency → Safety v3 result → `SAFETY_PASS` if SAFE → Profile-A v3 → Profile-A outcome event → Profile-B qualification event if qualified → truthful terminal completion.

Phase50 v1 accepts Profile-B schemas `{1,2}`, blocked Profile-A schemas `{2,3}`, and blocked Safety schemas `{2,3}`. V3 fixture/qualification identity patterns are available but FixtureSetV3 and QualificationV3 are not required for this no-publication validation; SourceProfileManifestV3 must not be constructed or validated.

## Terminal, publication, and cleanup contract

Pre-boundary failure leaves authorization unconsumed with HTTP/Phase44/GET all zero. Post-boundary acquisition or integrity failure maps to `RECOVERY_PREFLIGHT_BLOCKED`. Safety v3 non-SAFE, Profile-A v3 non-qualified after Safety SAFE, or Profile-B v2 non-qualified after Safety SAFE maps to `SOURCE_PROFILE_FIXTURE_BLOCKED`. All three qualifying maps to `READY_FOR_REVIEW`, meaning only `VERSIONED_SOURCE_PROFILE_VALIDATION_READY_FOR_CHATGPT_REVIEW`, never publication approval.

Publication is prohibited: no `PUBLICATION_BEGIN`, `RAW_FIXTURES_WRITTEN`, `MANIFEST_WRITTEN`, `DEDICATED_TEST_WRITTEN`, `REGRESSIONS_PASS`, rollback, fixture path, or manifest. A separate V3 publication-plan phase remains required.

The external safe-final may retain only bounded run/target/authorization/capture identity/hash/length, V2/V3 canonical diagnostics, Phase63/66 diagnostics, Safety v3 categories, terminal result, journal digest, parent validation, and cleanup facts. It must not retain raw provider content. After parent validation, all raw bytes, journals after safe-final retention, runner, streams, and synthetic data are removed; no raw-bearing artifact may remain.

Current-byte SHA/length comparison to Phase57/64/67/68 metadata is allowed. Equality may be reported only as `CURRENT_ACQUISITION_BYTES_REPRODUCED`, without historical inference. Market eligibility, positive market eligibility, and whole-meeting cancellation remain `UNSUPPORTED`.

## Readiness

- A Phase69 remote verification passed: YES.
- B executable support HEAD frozen: YES.
- C V3 authorities identified: YES.
- D Phase50 version compatibility confirmed: YES.
- E Phase63/66 supplemental-only role preserved: YES.
- F dry-run uses new authorities: YES.
- G dry/live shared runner designed: YES.
- H no-network dry-run complete in design: YES.
- I exact authorization boundary frozen: YES.
- J Phase44/GET caps frozen: YES.
- K Profile-B v2 expected evidence defined without assuming result: YES.
- L Profile-A v3 expected evidence defined without assuming result: YES.
- M Safety v3 expected evidence defined without assuming result: YES.
- N terminal mapping complete: YES.
- O publication prohibited: YES.
- P safe-final/cleanup preserved: YES.
- Q historical non-inference preserved: YES.
- R no tracked implementation change required: YES.

During APPROVE: Provider HTTP: `0`; Phase44: `0`; GET: `0`; synthetic dry-run: `NOT RUN`; live run: `NOT RUN`; boundary: `NOT WRITTEN`; authorization consumed: `NO`. Authorization state: `PHASE70_VERSIONED_SOURCE_PROFILE_VALIDATION_AUTHORIZATION_UNCONSUMED`.

Phase57, Phase64, Phase67, and Phase68 remain consumed fail-closed; Phase54 remains `UNCONSUMED_BUT_UNUSABLE_FOR_V2`; Phase41 remains `DESIGN_BLOCKED`.

Next permitted action: `TRACK_PHASE70_AUTHORIZATION_STATE_THEN_INDEPENDENT_REMOTE_VERIFICATION`.
