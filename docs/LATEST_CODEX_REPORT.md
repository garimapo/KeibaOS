# Latest Codex Report

## Phase73 implementation report

Phase: `POST_V0_8_DAILY_REPLAY_73`

State: `IMPLEMENTED_FOR_REVIEW`

Outcome: `READY_FOR_INDEPENDENT_IMPLEMENTATION_REVIEW`

Support Repair: `PROFILE_B_V2_CHANGEINFO_CLASS_TOKEN_REPAIRED`

Worktree: `C:\Users\garim\Desktop\KeibaOS-post-v0.8`

Starting tracking HEAD: `c8a9db01e1c6075dd028c4ed0fa4a77d6ea48eb2`

Previous executable support HEAD: `b29e98259a3186f905220b0d66eae24597458059`

### Frozen Phase72 evidence

Phase72 is `POST_AUTHORIZATION_STOP` with Phase50 outcome `RECOVERY_PREFLIGHT_BLOCKED`. Its authorization is permanently `PHASE72_VERSIONED_SOURCE_PROFILE_VALIDATION_AUTHORIZATION_CONSUMED_FAIL_CLOSED`. Boundary durability, all synthetic gates, exact runner parity, import isolation, one Phase44 call, exactly two GETs, zero retries, parent validation, cleanup, repository integrity, and the no-publication requirement all passed. The execution-integrity result is `PHASE72_VERSIONED_VALIDATION_EVIDENCE_REVIEW_PASS_WITH_TRACKED_SUPPORT_DEFECT`.

The exact blocker was `PROFILE_B_STRUCTURAL_CONSISTENCY`: Profile-B v2 counted two target rows while Phase66 classified only one as a direct schedule-domain descendant. Safety v3 and Profile-A v3 were not reached and are not claimed to have passed live.

The acquired Deba and RaceList hashes and lengths reproduced prior controlled current acquisitions. This is only `CURRENT_ACQUISITION_BYTES_REPRODUCED`; no historical availability, state, timing, cutoff, or market-eligibility inference is made.

### Root cause and implementation

The root cause is `PROFILE_B_V2_BEAUTIFULSOUP_CLASS_TOKEN_TYPE_COMPATIBILITY`. `_has_exact_class_token` used exact built-in-list type checking, while BeautifulSoup represents parsed class collections with a list-compatible subclass. In the live structure, the affected target row had exactly one table ancestor, so the missed `changeInfo` token caused the row to enter the v2 schedule domain.

The helper now:

- treats absent class as no match;
- whitespace-tokenizes an exact string;
- accepts list/tuple-compatible parsed class collections and subclasses;
- requires every retained token to be an exact string;
- matches only the exact, case-sensitive `changeInfo` token; and
- raises the existing diagnostics validation error for unsupported representations.

Profile-B v2 remains schema `2`. Profile-B v1 remains frozen and still uses its historical recursive candidate behavior. Withdrawal processing still independently selects `table.changeInfo`; no withdrawal predicate was altered.

### Regression evidence

The Phase72 live-shape regression uses sibling tables within one `section.raceTable`: one ordinary schedule table and one sole `table.changeInfo`, each containing a target 6R row. Profile-B v2 now has one target candidate and all six predicates pass; Profile-B v1 still has two target candidates and reports `UNIQUE_TARGET_6R = AMBIGUOUS`.

Additional tests prove observable support for BeautifulSoup list-compatible class values, multi-token `other changeInfo extra`, exact-token negatives `changeInformation` and `CHANGEINFO`, depth-two ordinary-table exclusion, fail-closed unknown class representations, withdrawal-domain preservation, and independent Profile-B-v2/Phase66 parity across eight structural wrappers.

### Test results

- `tests/test_nar_race_entry_status_source_profile_diagnostics.py`: `38 passed`
- `tests/test_nar_race_entry_status_source_profile_structural_recovery_diagnostics.py`: `152 passed`
- `tests/test_nar_race_entry_status_source_profile_recovery_diagnostics.py`: `80 passed`
- `tests/test_nar_race_entry_status_reacquisition_observability.py`: `355 passed`
- `tests/test_nar_race_entry_status_source_profile_profile_a.py`: `17 passed`
- `tests/test_nar_race_entry_status_source_profile_publication_contract.py`: `49 passed`
- Full repository: `4321 passed, 2841 subtests passed`

Representative Profile-B v2 canonical diagnostics are `1037 bytes`; the canonical Phase50 journal record is `1318 bytes`, below `MAX_RECORD_BYTES = 4096`. `JOURNAL_SCHEMA_VERSION` remains `1`; no record or journal limit changed.

### Scope and safety

Only the approved four files changed. Phase50, Phase63, Phase66, Profile-A, and Safety are unchanged. The implementation introduces no network, process, database, or filesystem-write capability and creates no fixture or manifest.

Provider HTTP / Phase44 / GET: `0 / 0 / 0`

Acquisition authorization issued: `NONE`

Publication: `NO`

Market eligibility remains `UNSUPPORTED`; positive market eligibility and `WHOLE_MEETING_CANCELLATION` remain `UNSUPPORTED`.

Next permitted action after successful integration: `CHATGPT_REVIEW_PHASE73_IMPLEMENTATION`.
