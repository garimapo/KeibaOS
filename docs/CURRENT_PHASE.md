# Current Phase

## Phase

`POST_V0_8_DAILY_REPLAY_59`

## Title

Phase50 v2 Publication Identity Observability Compatibility Support

## Status

`INTEGRATED_PENDING_REMOTE_VERIFICATION`

## Outcome

`IMPLEMENTED_PHASE50_V2_PUBLICATION_IDENTITY_COMPATIBILITY`

## Approved design basis

- Formal Status: `APPROVED_FOR_CODEX`
- Design Review: `PHASE59_DESIGN_REVIEW_PASS`
- Integration Review: `PASS_FOR_INTEGRATION`.
- Remote Verification: `REQUIRED`.
- Current next action: independent remote verification; do not begin Phase57.
- Phase44 changes: `NOT_AUTHORIZED`.
- Phase53 changes: `NOT_AUTHORIZED`.
- Phase56 changes: `NOT_AUTHORIZED`.
- Provider HTTP: `NOT_AUTHORIZED`.

## Implementation result

- The confirmed `PHASE57_V2_MANIFEST_OBSERVABILITY_IDENTITY_INCOMPATIBLE` blocker is resolved and integrated locally, pending independent remote verification.
- Fixture-set and qualification identities now accept only the exact canonical v1 or v2 families frozen by this phase.
- Private Phase50 validators return canonical text plus derived exact version `1` or `2`; `MANIFEST_WRITTEN` requires the two derived versions to match.
- `v1/v1` and `v2/v2` pairs are accepted; `v1/v2` and `v2/v1` pairs are rejected fail-closed.
- Historical v1 acceptance remains only `LEXICALLY_CANONICAL_HISTORICAL_OBSERVABILITY_VALUE`; `V1_PUBLICATION_CONTRACT_NOT_EXACTLY_RECOVERABLE` remains unchanged.
- `MANIFEST_WRITTEN` and its keys, `JOURNAL_SCHEMA_VERSION = 1`, milestone ordering, Phase58 durability events, and `LIVE_PROCESS_COMPLETE` outcomes are unchanged.
- Phase44, Phase53, and Phase56 are unchanged. Provider HTTP and Phase44 live acquisition both remain zero/not entered.

## Verification evidence

- Focused Phase50 observability: `170 passed`.
- Relevant no-network NAR regression: `334 passed`.
- Full repository suite: `3840 passed, 2841 subtests passed`.
- Added-lines no-network/no-domain-import/no-market-inference audit: PASS.
- Repository delta: exactly the four approved implementation-manifest paths.
- Staging: empty; no untracked paths; `git diff --check`: PASS.

## Authority and Git basis

- Authorized worktree: `C:\Users\garim\Desktop\KeibaOS-post-v0.8`
- Branch: `feature/post-v0.8-daily-replay`
- Base HEAD: `be508d64c1004406445b2a5cdf33da37bdf2354d`
- Predecessor: Phase58, `FORMALLY_COMPLETE`
- Phase58 commit/tree: `be508d64c1004406445b2a5cdf33da37bdf2354d` / `ff9890c9289349408ad62522e3b6a20c7359da96`
- Phase44 remains the sole acquisition authority; Phase50 remains operational observability only; Phase56 remains the sole v2 publication-identity authority.

## Authorization and acquisition state

- Phase54: `PHASE54_AUTHORIZATION_UNCONSUMED_BUT_UNUSABLE_FOR_V2`.
- Phase57: `DESIGN_BLOCKED`; `PHASE57_ACQUISITION_AUTHORIZATION_NOT_YET_ISSUED`.
- Provider HTTP: `0`; Phase44 live acquisition: not entered.
- Phase59 issues and consumes no authorization and performs no live work.

## Confirmed compatibility blocker

`PHASE57_V2_MANIFEST_OBSERVABILITY_IDENTITY_INCOMPATIBLE`

At `be508d64c1004406445b2a5cdf33da37bdf2354d`, Phase50's local lexical validators in `scripts/simulation/nar_race_entry_status_reacquisition_observability.py` accept only these exact historical strings:

- `nar-race-entry-status-source-profile-fixture-set-v1:<64 lowercase hexadecimal characters>`
- `nar-race-entry-status-source-profile-qualification-v1:<64 lowercase hexadecimal characters>`

`MANIFEST_WRITTEN` uses those validators for its unchanged detail keys, `fixture_set_identity` and `qualification_identity`. Phase56's tracked publication contract instead emits the formally complete v2 families:

- `nar-race-entry-status-source-profile-fixture-set-v2:<64 lowercase hexadecimal characters>`
- `nar-race-entry-status-source-profile-qualification-v2:<64 lowercase hexadecimal characters>`

The v1-only Phase50 validators would reject the v2 identity strings before a future Phase57 manifest could be durably journaled.

## Frozen Phase59 scope

Phase59 is a strictly additive, no-network Phase50 lexical/structural compatibility change. It will not construct or recompute either identity, evaluate Phase56 payloads, decide semantic validity, redefine v1 or v2, parse provider data, acquire source data, or change manifest semantics. Phase56 remains the sole authority for v2 identity construction and semantic validation.

Historical v1 lexical acceptance means only “lexically canonical historical observability value.” It does not establish that the unresolved v1 publication contract was complete or semantically valid.

### Exact lexical acceptance

Fixture-set identity accepts exactly one of:

- `nar-race-entry-status-source-profile-fixture-set-v1:[0-9a-f]{64}`
- `nar-race-entry-status-source-profile-fixture-set-v2:[0-9a-f]{64}`

Qualification identity accepts exactly one of:

- `nar-race-entry-status-source-profile-qualification-v1:[0-9a-f]{64}`
- `nar-race-entry-status-source-profile-qualification-v2:[0-9a-f]{64}`

The match is whole-string ASCII only. Other versions, uppercase hexadecimal, a digest of any other length, missing digest, suffix text, whitespace, newline, malformed prefixes, and arbitrary text are rejected. The implementation uses explicit v1/v2 alternatives, not a permissive version pattern.

`MANIFEST_WRITTEN` keeps its milestone name, two detail keys, ordering, and meaning unchanged. A private local helper may derive a validated version from each identity solely to apply the frozen pair rule; it exposes no new public Phase50 API and imports no Phase56 production module.

### Pair compatibility decision

Only `v1/v1` and `v2/v2` pairs are accepted. `v1/v2` and `v2/v1` pairs are rejected fail-closed.

Targeted history for the Phase50 module and its focused tests finds only the original same-version v1 pair introduced at `c796e45467184efad97f312c605a67c65865b21b`; no tracked evidence requires mixed-version journal readability. Phase56 defines qualification v2 against fixture-set v2 identity, so a mixed pair is structurally suspicious even when each individual string is lexical-valid.

## Journal compatibility

- `JOURNAL_SCHEMA_VERSION` remains `1`.
- `MAX_RECORD_BYTES` remains `4096`.
- `MANIFEST_WRITTEN` detail keys remain exactly `fixture_set_identity` and `qualification_identity`.
- Existing v1 journal records remain readable.
- Phase58 blocked-event semantics and all existing retention event semantics remain unchanged.

This is an additive lexical compatibility extension: detail keys and milestone semantics do not change, so no journal migration or version bump is required.

## Frozen Phase50 milestone order

The current enum order, which Phase59 must not change, is:

1. `PROFILE_B_DIAGNOSTICS_RETAINED`
2. `IDENTITY_VERIFICATION_PASS`
3. `PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED`
4. `SAFETY_PASS`
5. `PROFILE_A_BLOCKED_DIAGNOSTICS_RETAINED`
6. `PROFILE_A_QUALIFIED`
7. `PROFILE_B_QUALIFIED`
8. `PUBLICATION_BEGIN`
9. `RAW_FIXTURES_WRITTEN`
10. `MANIFEST_WRITTEN`

## Live-process outcome audit

The existing Phase50 `LIVE_PROCESS_COMPLETE` vocabulary is sufficient without change:

- successful publication path: `READY_FOR_REVIEW`
- source-profile blocked path: `SOURCE_PROFILE_FIXTURE_BLOCKED`
- preflight blocked path: `RECOVERY_PREFLIGHT_BLOCKED`

The remaining synthetic outcomes are `SYNTHETIC_SUCCESS` and `SYNTHETIC_FAILURE`. No `PHASE57_LIVE_PROCESS_OUTCOME_VOCABULARY_INCOMPATIBLE` blocker is present.

## Future implementation manifest

Exactly four paths are authorized for a later Phase59 EXECUTE:

1. `scripts/simulation/nar_race_entry_status_reacquisition_observability.py`
2. `tests/test_nar_race_entry_status_reacquisition_observability.py`
3. `docs/CURRENT_PHASE.md`
4. `docs/LATEST_CODEX_REPORT.md`

No Phase44, Phase53, or Phase56 file; fixture; `.gitattributes` file; database; log; or additional path is authorized. A fifth path requires `DESIGN_BLOCKED_SCOPE_EXPANSION_REQUIRED`.

## Required future tests

- Each identity family: canonical v1 and v2 accept; v3, uppercase digest, short/long digest, malformed prefix, and trailing text reject.
- `MANIFEST_WRITTEN`: v1/v1 and v2/v2 accept; either mixed pair rejects; malformed fixture or qualification identity rejects; detail keys stay exact; canonical journal round-trip and existing record bound hold.
- Existing Phase58 blocked-event tests, the exact preflight token, journal schema version, and milestone ordering remain unchanged.
- Test economy: focused observability tests, one relevant no-network NAR observability/publication-contract regression, then one full suite when otherwise ready.

## Future success boundary

`POST_V0_8_DAILY_REPLAY_59` may become:

- Status: `READY_FOR_REVIEW`
- Outcome: `IMPLEMENTED_PHASE50_V2_PUBLICATION_IDENTITY_COMPATIBILITY`

Only after v1 lexical compatibility is preserved, both v2 identity shapes are accepted, the same-version pair rule is enforced, `MANIFEST_WRITTEN` keys/meaning and journal schema remain unchanged, Phase58 support remains unchanged, required no-network tests pass, the exact four-path delta is present, the index is empty, and `git diff --check` passes.

## Persistent constraints

- Phase41 remains `DESIGN_BLOCKED`.
- `positive_market_eligibility = UNSUPPORTED`.
- `WHOLE_MEETING_CANCELLATION = UNSUPPORTED`.
- Open: `COMBINATION_EV_REQUIRES_MARKET_ODDS_CAPTURE` and `NAR_MARKET_ELIGIBILITY_REQUIRES_INDEPENDENT_ENTRY_STATUS_CAPTURE`.
- No Phase50 identity string establishes `MARKET_ELIGIBLE`.

## Review boundary

Integration is pending independent remote verification. Phase59 must not be marked formally complete locally before that verification. No authorization, provider HTTP, Phase44 live entry, fixture publication, or Phase57 restart occurred.
