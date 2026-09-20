# Current Phase

## Phase73 implementation

- Phase: `POST_V0_8_DAILY_REPLAY_73`
- Title: `Profile-B V2 ChangeInfo Class-Token Compatibility Repair`
- Branch: `feature/post-v0.8-daily-replay`
- Starting tracking HEAD: `c8a9db01e1c6075dd028c4ed0fa4a77d6ea48eb2`
- Previous executable support HEAD: `b29e98259a3186f905220b0d66eae24597458059`
- State: `IMPLEMENTED_FOR_REVIEW`
- Outcome: `READY_FOR_INDEPENDENT_IMPLEMENTATION_REVIEW`
- Support Repair: `PROFILE_B_V2_CHANGEINFO_CLASS_TOKEN_REPAIRED`
- Allowed files: `scripts/simulation/nar_race_entry_status_source_profile_diagnostics.py`, `tests/test_nar_race_entry_status_source_profile_diagnostics.py`, `docs/CURRENT_PHASE.md`, `docs/LATEST_CODEX_REPORT.md`

## Frozen Phase72 result

- State: `POST_AUTHORIZATION_STOP`
- Phase50 outcome: `RECOVERY_PREFLIGHT_BLOCKED`
- Authorization: `PHASE72_VERSIONED_SOURCE_PROFILE_VALIDATION_AUTHORIZATION_CONSUMED_FAIL_CLOSED`
- Execution Integrity: `PASS`
- Evidence review: `PHASE72_VERSIONED_VALIDATION_EVIDENCE_REVIEW_PASS_WITH_TRACKED_SUPPORT_DEFECT`
- Exact blocker: `PROFILE_B_STRUCTURAL_CONSISTENCY`
- Provider HTTP / Phase44 / GET: `2 / 1 / 2`
- Post-boundary retries: `0`
- Publication: `NO`
- Safety v3 live: `NOT_REACHED`
- Profile-A v3 live: `NOT_REACHED`

Phase72 reproduced the previously retained current bytes. This is only `CURRENT_ACQUISITION_BYTES_REPRODUCED`; it does not establish historical source availability, provider state, timing, cutoff, or market eligibility. The consumed Phase72 authorization may never be retried or reused.

## Root cause and repair

The root cause is `PROFILE_B_V2_BEAUTIFULSOUP_CLASS_TOKEN_TYPE_COMPATIBILITY`. Profile-B v2 previously accepted only an exact built-in `list` for parsed class collections. BeautifulSoup supplies a list-compatible class collection, so a sole `table.changeInfo` ancestor was not recognized and was incorrectly admitted to the schedule domain.

Profile-B v2 now uses the same low-level class-token grammar independently implemented by Phase66: absent class is not a match; an exact string is whitespace-tokenized; list/tuple-compatible parsed collections, including subclasses, are accepted; every token must be an exact string; and unsupported representations fail closed. Matching remains exact and case-sensitive. `changeInformation` and `CHANGEINFO` do not match `changeInfo`.

The v2 schedule-domain contract remains: exactly one table ancestor before the selected `section.raceTable`, and that table must not contain the exact `changeInfo` token. The independent withdrawal domain and its `table.changeInfo` traversal are unchanged. Profile-B v1 remains frozen with recursive historical behavior. Profile-B v2 remains schema version `2`.

## Verification

- Profile-B diagnostics: `38 passed`
- Phase66 structural recovery: `152 passed`
- Phase63 recovery diagnostics: `80 passed`
- Phase50 observability: `355 passed`
- Profile-A: `17 passed`
- Safety/publication contract: `49 passed`
- Full repository: `4321 passed, 2841 subtests passed`
- Representative Profile-B v2 canonical diagnostics: `1037 bytes`
- Representative Phase50 record: `1318 / 4096 bytes`
- Journal schema: unchanged at `1`
- Provider HTTP / Phase44 / GET: `0 / 0 / 0`
- Acquisition authorization issued: `NONE`
- Publication: `NO`

The live-shape regression proves one direct schedule row plus one sole `changeInfo` row produces a qualified Profile-B v2 result with one schedule candidate, while Profile-B v1 retains two candidates and `AMBIGUOUS`. The regression suite also covers BeautifulSoup list-compatible class values, multi-token exact matching, exact-token negatives, nested ordinary tables, fail-closed unknown representations, withdrawal-domain preservation, and an eight-case parity matrix against Phase66 structural classification.

Phase50, Phase63, Phase66, Profile-A, and Safety remain unchanged. No network, process, database, filesystem-write, fixture, manifest, publication, or authorization capability was added.

## Stop condition

Phase73 is implemented for review but is not formally complete until independent remote verification. A future validation requires a new authorization bound to the newly reviewed executable support HEAD.

Next permitted action: `CHATGPT_REVIEW_PHASE73_IMPLEMENTATION`.
