# Current Phase

## Phase74 approved authorization

- Phase: `POST_V0_8_DAILY_REPLAY_74`
- Title: `Fresh-Current Validation After Profile-B V2 ChangeInfo Token Repair`
- Branch: `feature/post-v0.8-daily-replay`
- Current / executable support HEAD: `b2355113f969f6af713a254355e67a9feab5cc45`
- Support tree: `24b4f37391039e1ece2d573b4a0ea3f0de65e4cd`
- Approval Base HEAD: `b2355113f969f6af713a254355e67a9feab5cc45`
- State: `APPROVED_UNCONSUMED_TRACKED`
- Authorization Tracking State: `APPROVED_UNCONSUMED_TRACKED`
- Formal Status: `APPROVED_FOR_CODEX`
- Design Review: `PHASE74_VALIDATION_DESIGN_REVIEW_PASS`
- Outcome: `APPROVED_PROFILE_B_V2_REPAIRED_FRESH_CURRENT_VALIDATION`
- Validation Contract: `PROFILE_B_V2_REPAIRED_FRESH_CURRENT_VALIDATION_CONTRACT_COMPLETE`
- Allowed files in this approval: `docs/CURRENT_PHASE.md`, `docs/LATEST_CODEX_REPORT.md`

## Issued authorization

- `PHASE74_VERSIONED_SOURCE_PROFILE_VALIDATION_AUTHORIZATION_UNCONSUMED`
- Reserved consumed state: `PHASE74_VERSIONED_SOURCE_PROFILE_VALIDATION_AUTHORIZATION_CONSUMED_FAIL_CLOSED`

This new one-shot authorization binds only to Phase74, target `NAR / 21 / 2025-01-01 / 6`, purpose `FRESH_CURRENT_VALIDATION_AFTER_PHASE73_PROFILE_B_V2_REPAIR`, semantics `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`, and support HEAD `b2355113f969f6af713a254355e67a9feab5cc45`. It is phase-specific, target-specific, purpose-specific, support-HEAD-specific, nontransferable, and nonrenewable after consumption. It is not a retry or reuse of Phase72.

During approval, Provider HTTP / Phase44 / GET are `0 / 0 / 0`; synthetic and live execution are `NOT RUN`; the boundary is `NOT WRITTEN`; and the authorization is not consumed.

## Frozen predecessor state

Phase73 is `FORMALLY_COMPLETE`, with repair `PROFILE_B_V2_CHANGEINFO_CLASS_TOKEN_REPAIRED`, commit `b2355113f969f6af713a254355e67a9feab5cc45`, tree `24b4f37391039e1ece2d573b4a0ea3f0de65e4cd`, and review `PHASE73_IMPLEMENTATION_REMOTE_VERIFICATION_PASS`.

Phase72 remains `POST_AUTHORIZATION_STOP` / `RECOVERY_PREFLIGHT_BLOCKED` / `PHASE72_VERSIONED_SOURCE_PROFILE_VALIDATION_AUTHORIZATION_CONSUMED_FAIL_CLOSED`. Its durable boundary, Phase44 `1`, Deba/RaceList GET `1 / 1`, total GET `2`, retry `0`, publication `NO`, and blocker `PROFILE_B_STRUCTURAL_CONSISTENCY` are final. Its authorization is permanently consumed and unusable.

## Future validation contract

Qualification authority is exclusively Profile-B v2 (`diagnose_nar_race_entry_status_profile_b_v2`, schema `2`), Profile-A v3 (`diagnose_nar_race_entry_status_profile_a_v3`, schema `3`), and Safety v3 (`assess_nar_race_entry_status_raw_fixture_publication_safety_v3`, schema `3`). Legacy authorities remain frozen and non-authoritative. Phase50 remains journal schema `1`, accepts Profile-B `{1,2}`, blocked Profile-A `{2,3}`, blocked Safety `{2,3}`, and requires the schema-3 Profile-A target to equal `TARGET_CONSTRUCTED`.

The mandatory synthetic topology is one ordinary schedule table plus one sibling sole `table.changeInfo` inside the unique `section.raceTable`. Profile-B v2 must retain schema `2`, count one target schedule row, pass all six predicates, and be `QUALIFIED`. On the same bytes, Phase63 must retain two broad candidates; Phase66 must retain two candidates: one direct `RACE_SCHEDULE_TABLE` and one `CHANGE_INFO_TABLE`.

Structural consistency is defined only as:

```text
Profile-B v2 target_6r_row_count
== count(Phase66 direct_schedule_table_descendant == true)
```

It must not compare Profile-B v2 against the broader Phase63 or Phase66 total candidate counts. The mandatory repair gate is `PHASE73_PROFILE_B_V2_CHANGEINFO_TOKEN_INTEGRATION_PASS`. The actual Profile-A-v3 canonical target gate `PHASE71_PROFILE_A_V3_TARGET_CONTRACT_INTEGRATION_PASS`, both blocked probes, full synthetic success path, no-network proof, runner parity, exact eleven-key metadata, and closed-bundle identity gates remain mandatory.

The future runner remains generated once externally, compiled once, byte-identical between synthetic/live modes, and uses one shared capture adapter and post-acquisition processor under fresh `-I -B` isolation. The exact preflight bytes are `NAR_REACQUISITION_OBSERVABILITY_PREFLIGHT_PASS\n` with LF only.

The sole future consumption boundary is durable `PHASE44_CALL_ABOUT_TO_ENTER` append, flush, and fsync. It permits at most one Phase44, one Deba GET, one RaceList GET, and two GETs total in DebaTable then RaceList order, without retry, fallback, discovery, or alternate targets.

Publication remains forbidden. Bounded external safe-final, raw cleanup, and historical non-inference remain mandatory. Market eligibility, positive market eligibility, and `WHOLE_MEETING_CANCELLATION` remain `UNSUPPORTED`.

## Stop condition

This approval does not execute Phase74. No synthetic or live execution, provider HTTP, Phase44, boundary, staged change, commit, or push has occurred.

Next permitted action: `TRACK_PHASE74_AUTHORIZATION_STATE_THEN_INDEPENDENT_REMOTE_VERIFICATION`.
