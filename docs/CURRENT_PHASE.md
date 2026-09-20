# Current Phase

## Phase71 implementation

- Phase: `POST_V0_8_DAILY_REPLAY_71`
- Title: `Phase50 Profile-A v3 Target Payload Compatibility Repair`
- Branch: `feature/post-v0.8-daily-replay`
- Base / starting tracking HEAD: `4c18597eac7ec8b180650c89acddbe88f0294047`
- Previous executable support HEAD: `79d6faaa30a54840232c0b73cd0e4ce1451a088e`
- Status: `READY_FOR_REVIEW`
- State: `IMPLEMENTED_FOR_REVIEW`
- Outcome: `READY_FOR_INDEPENDENT_IMPLEMENTATION_REVIEW`
- Support Repair: `PHASE50_PROFILE_A_V3_TARGET_CONTRACT_REPAIRED`
- Provider HTTP / Phase44 / GET: `0 / 0 / 0`
- Acquisition authorization issued: `NONE`

## Scope

Allowed and changed paths are exactly:

1. `scripts/simulation/nar_race_entry_status_reacquisition_observability.py`
2. `tests/test_nar_race_entry_status_reacquisition_observability.py`
3. `docs/CURRENT_PHASE.md`
4. `docs/LATEST_CODEX_REPORT.md`

No Profile-A, Profile-B, Safety, Phase44, Phase63, or Phase66 production authority changed. `JOURNAL_SCHEMA_VERSION` remains `1`; record and journal limits remain `4096` and `131072` bytes.

## Repaired contract

Phase50 now validates blocked Profile-A payloads by incoming version:

- Schema `2` retains the frozen historical targetless shape. A `target` field remains forbidden.
- Schema `3` requires the exact canonical Profile-A v3 shape, including `target` with exactly `baba_code`, `race_date`, and `race_no`.
- The schema-3 target requires a canonical positive ASCII provider code, exact valid `YYYY-MM-DD` date, and exact positive race number bounded to `1..12`. Values are validated without coercion or version normalization.
- Journal semantic validation requires a retained schema-3 Profile-A target to equal the same journal's `TARGET_CONSTRUCTED` details exactly. Any baba-code, date, or race-number contradiction fails closed.

Historical schema-2 Phase50 evidence remains reconstructable. Unsupported Profile-A versions remain rejected.

## Verification

- Phase50 targeted suite: `355 passed in 3.05s`.
- Profile-A, Phase63 recovery, and Phase66 structural suites: `249 passed in 0.71s`.
- Full repository suite: `4309 passed, 2841 subtests passed in 28.82s`.
- Representative schema-3 blocked Profile-A record: `923` bytes excluding LF, `924` bytes including LF; limit `4096`.
- Representative seven-record journal: `2695` bytes; limit `131072`.

Tests cover schema-2 targetless acceptance and target rejection, direct acceptance of an actual blocked `ProfileADiagnosticsV3.to_canonical_dict()` payload, missing/malformed schema-3 targets, exact matching with `TARGET_CONSTRUCTED`, all three mismatch dimensions, unsupported versions, historical regression behavior, and unchanged size bounds.

## Phase70 authorization state

The Phase70 authorization was never consumed:

`PHASE70_VERSIONED_SOURCE_PROFILE_VALIDATION_AUTHORIZATION_UNCONSUMED`

It is now recorded as:

`INVALIDATED_BY_EXECUTABLE_SUPPORT_HEAD_CHANGE`

It must not be consumed, reused, rebound, or treated as valid against the Phase71 executable support state. Phase71 does not issue a replacement acquisition authorization.

## Stop condition

Stop after the exact four-file implementation is tested, committed, pushed, and reported for independent review. Do not run a live acquisition or issue an acquisition authorization.

Next permitted action: `CHATGPT_REVIEW_PHASE71_IMPLEMENTATION`.
