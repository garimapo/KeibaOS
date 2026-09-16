# Current Phase

## Identity

- Phase: `POST_V0_8_DAILY_REPLAY_65`
- Title: `Post-Diagnostic Source-Profile Remediation and Evidence-Sufficiency Design`
- Base HEAD: `a58874824804856ff8be64df0bab4c2d867f1f94`
- Branch: `feature/post-v0.8-daily-replay`
- Status: `INTEGRATED_PENDING_REMOTE_VERIFICATION`
- Design Review: `PHASE65_POST_DIAGNOSTIC_REMEDIATION_DESIGN_REVIEW_PASS`
- Outcome: `APPROVED_ADDITIONAL_SAFE_STRUCTURAL_DIAGNOSTIC_DESIGN`
- Next phase: `POST_V0_8_DAILY_REPLAY_66`

## Git and dependency baseline

- `POST_V0_8_DAILY_REPLAY_63` is formally complete at commit `5b85d54a39c6b7d3e6c036cc0d479ba24e0a1797`, tree `6ebbe16b0d56e86a237e28cde38c489fc81a5310`.
- Phase64's approval-state tracking commit is `a58874824804856ff8be64df0bab4c2d867f1f94`; its parent is the unchanged executable Phase63 support commit.
- PREPARE began on the required branch with local and remote HEAD equal to the base, an empty index, no untracked paths, and a clean worktree.
- This phase changes only this file and `docs/LATEST_CODEX_REPORT.md`. It does not implement, authorize, acquire, publish, stage, commit, or push.

## Immutable Phase64 diagnostic run

- Phase64 is `FORMALLY_COMPLETE_DIAGNOSTIC_RUN` and `DIAGNOSTIC_OBJECTIVE_COMPLETED_WITH_SOURCE_PROFILE_BLOCK`: its approved diagnostic-only objective completed with a real source-profile block. This is not source-profile qualification or fixture-publication success.
- State: `POST_AUTHORIZATION_STOP`; Phase50 outcome: `SOURCE_PROFILE_FIXTURE_BLOCKED`; authorization: `PHASE64_DIAGNOSTIC_ACQUISITION_AUTHORIZATION_CONSUMED_FAIL_CLOSED`; retry: `FORBIDDEN`.
- One Phase44 entry obtained the closed DebaTable → RaceList bundle with two GET attempts: Deba `1` attempt / `1` response and RaceList `1` attempt / `1` response. Identity verification, parent validation, and cleanup passed. Publication did not start and Profile-A was not executed.
- The only reviewed safe-final artifact is `C:\Users\garim\AppData\Local\Temp\phase64-diagnostic-4b22b2a3fc2e471b820176f3c2645f38\safe-final.json`: run ID `4b22b2a3fc2e471b820176f3c2645f38`, `17655` bytes, SHA-256 `30fa91e8b69fd184a7a75404636f318bf84dd5c8f890a3be89ce6227ce705f3c`, journal SHA-256 `e7cfdbd97474174034a2549daba4eb0169e68746380123b57648f916da8058f4`, and `24` canonical records.
- No raw provider body was read, retained, searched for, reconstructed, or added to tracked documentation.

## Reproduced current-acquisition metadata

- DebaTable: SHA-256 `6c9aa3ea614c17e14f0e7a5050190ca923445925d67f8e61e71db95e87c87727`; length `313317`.
- RaceList: SHA-256 `1eb363621c7a152929765ff7ffecabea2d7cf15283d45fa9c31036527c0b53a1`; length `66307`.
- These equal the approved safe Phase57 metadata. Freeze `CURRENT_REACQUISITION_BYTES_REPRODUCED_ACROSS_TWO_CONTROLLED_RUNS`: two current 2026 acquisitions returned byte-identical content.
- This does not assert historical availability, 2025 bytes, historical provider state, historical timing/cutoff, or market eligibility. `market_eligibility`, `positive_market_eligibility`, and `WHOLE_MEETING_CANCELLATION` remain `UNSUPPORTED`.

## Safety evidence and strict-structure sufficiency

- Phase63 Safety recovery v1 recorded DebaTable `utf8_decode=PASS`, `strict_structure=FAIL`, `beautifulsoup_parse=NOT_REACHED`; RaceList `PASS/PASS/PASS` in the same order.
- The unchanged Phase56 Safety result is `UNSUPPORTED`, with all five categories `UNSUPPORTED` and finding count `0`: `NO_AUTHENTICATION_MATERIAL`, `NO_COOKIE_OR_SESSION_SECRET`, `NO_CSRF_OR_SECRET_TOKEN`, `NO_USER_ACCOUNT_IDENTIFIER`, and `NO_PERSONALIZATION_IDENTIFIER`.
- The current strict validator uses `HTMLParser` with a non-void tag stack. `handle_endtag` raises the same generic `ValueError` when a non-void end tag sees either an empty stack or a different stack top; `close` raises the same generic `ValueError` when its stack is nonempty. These are the exact explicit strict-validator failure paths. The current stage-only recovery record cannot distinguish the two `handle_endtag` branches from the `close` branch.
- `CURRENT_SAFE_EVIDENCE_INSUFFICIENT_FOR_DIRECT_SAFETY_STRUCTURE_FIX` is frozen. No removal, weakening, tolerant replacement, or Deba special case is authorized.
- Verdict: `SAFETY_ADDITIONAL_STRUCTURE_DIAGNOSTIC_REQUIRED`.

## Proposed bounded strict-structure diagnostic

- Phase66 must prepare the exact schema `nar-race-entry-status-strict-structure-recovery-diagnostics`, version `1`, with one ordered result for each fixed document role `deba_table`, `race_list`.
- Its required conceptual `failure_kind` vocabulary is `PASS`, `END_TAG_EMPTY_STACK`, `END_TAG_MISMATCH`, and `UNCLOSED_STACK_AT_CLOSE`. Phase66 must audit any additional parser-feed failure class before adding it; no speculative enum is approved.
- Phase66 must select the smallest bounded fields from `failure_kind`, `event_index`, `stack_depth`, `unclosed_stack_depth`, and fixed-allowlist `expected_open_tag` / `observed_end_tag` enums. Unknown/custom tags must map to a bounded enum; no provider strings may be retained.
- Diagnostic-only `tolerant_parse` is approved for Phase66 investigation with the bounded vocabulary `PASS`, `FAIL`, `NOT_RUN`. It never changes Phase56 Safety and a pass never establishes publication Safety.
- The object contains no markup, attributes, snippets, text, URL/query, exception text, or raw body.

## Profile-B evidence and sufficiency

- Ordinary Phase53 Profile-B is `BLOCKED`; first nonpass is `UNIQUE_TARGET_6R` with count `2`. `RACE_TABLE_SCOPE` passed with count `1`. `DEBA_LINK_RELATIONSHIP` and `DEBA_LINK_QUERY_BINDING` are derived `UNSUPPORTED`, not independent incompatibilities. `WITHDRAWAL_ROW_SHAPE` and `HORSE_14_WITHDRAWAL_ASSOCIATION` both passed.
- Phase63 Profile-B recovery v1 is complete: scope count `1`, candidate count `2`, and `all_candidate_safe_projections_equal=false`.

| Candidate | Direct cells | Anchors | Exact Deba path | Href unsupported | Canonical query matches | Query unsupported | Canonical match |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 10 | 4 | 1 | 0 | 1 | 0 | true |
| 2 | 6 | 0 | 0 | 0 | 0 | 0 | false |

- Current Phase53 first collects all `section.raceTable tr.data` rows whose first direct cell normalizes exactly to `6R`, then computes `_outcome(len(target_rows))` for `UNIQUE_TARGET_6R`. Deba relationship inspection runs only if that outcome passes; query binding runs only if relationship passes. `PREDICATE_ORDERING_LIMITATION_CONFIRMED`.
- Option A—using canonical Deba binding to establish target-row identity—would materially change the meaning/order of the v1 predicates, needs a versioned Profile-B authority, and is not justified by current evidence alone. It must not silently reinterpret historical v1 diagnostics.
- Option B—narrowing the schedule-row DOM boundary—cannot be selected from the present safe fields. Candidate 2's six cells and zero anchors, together with a passing withdrawal predicate, do not prove that it is in `table.changeInfo` or any other auxiliary nested table. Freeze `CURRENT_SAFE_EVIDENCE_DOES_NOT_PROVE_CANDIDATE_2_ANCESTRY`.
- Verdict: `PROFILE_B_ADDITIONAL_ANCESTRY_DIAGNOSTIC_REQUIRED`. No row selection, deduplication, grammar relaxation, or profile qualification is authorized.

## Proposed bounded candidate-ancestry diagnostic

- Phase66 must prepare the bounded schema `nar-race-entry-status-profile-b-candidate-ancestry-recovery-diagnostics`, version `1`, reusing the exact Phase53 candidate boundary, DOM order, target, and maximum of eight retained candidates.
- Top-level fields: schema/version, formal target, `race_table_scope_count`, `target_candidate_count`, `candidate_details_complete`, and ordered `candidate_results`. More than eight candidates is explicit incomplete evidence with empty details, never truncation.
- Each candidate has only `candidate_ordinal`, `nearest_table_role`, `inside_change_info_table`, `nested_table_depth_within_race_scope`, and `direct_schedule_table_descendant`.
- `nearest_table_role` is a closed enum derived only from fixed selector/class authorities: `RACE_SCHEDULE_TABLE`, `CHANGE_INFO_TABLE`, `OTHER_TABLE`, `NO_TABLE`. Phase66 must freeze the precise selector definitions, without retaining class strings, DOM paths, text, hrefs, queries, or HTML.

## Combined next support phase and durability

- Approved one next support phase: `POST_V0_8_DAILY_REPLAY_66`, `Tracked Safe Structural Root-Cause Diagnostics`.
- Its responsibility is only the two bounded diagnostics above and their durable observability. It does not alter Phase44, Phase53 ordinary grammar, Phase56 Safety/Profile-A/publication semantics, Phase60/61, fixtures, or `.gitattributes`.
- Conceptual durable Phase50 event names are `PROFILE_B_CANDIDATE_ANCESTRY_RECOVERY_DIAGNOSTICS_RETAINED` and `STRICT_STRUCTURE_RECOVERY_DIAGNOSTICS_RETAINED`; Phase66 must freeze their exact keys, schema validation, order, and bounds. They cannot truthfully overload Phase63 recovery events.
- Preferred relative order for Phase66 review: normal Profile-B → Phase63 Profile-B recovery → candidate-ancestry recovery → identity pass → strict-structure recovery → Phase63 Safety recovery → unchanged normal Safety branch. Existing relative order remains intact. Every future record must use canonical append → flush → fsync.
- The Phase66 design must prove each independent JSONL record is within `MAX_RECORD_BYTES = 4096`; retain at most eight bounded ancestry entries and no arbitrary text.
- Preferred exact implementation manifest: new `scripts/simulation/nar_race_entry_status_source_profile_structural_recovery_diagnostics.py`; its dedicated test; Phase50 observability module/test; these two documentation files. No seventh path, absent a separately reported scope expansion.

## Future acquisition and persistent state

- Another live acquisition is eventually required to collect these new diagnostics. It needs a separate PREPARE → review → APPROVE → one-shot authorization; it is not a retry. Proposed purpose: `CONTROLLED_REACQUISITION_FOR_STRICT_STRUCTURE_AND_CANDIDATE_ANCESTRY_DIAGNOSTICS`.
- No authorization is issued in Phase65. Provider HTTP and Phase44 entry in this phase are both `0`.
- Phase57 remains `POST_AUTHORIZATION_STOP` with consumed-fail-closed authorization. Phase54 remains `PHASE54_AUTHORIZATION_UNCONSUMED_BUT_UNUSABLE_FOR_V2`; Phase41 remains `DESIGN_BLOCKED`.

## Scope and next action

- Allowed paths: `docs/CURRENT_PHASE.md`, `docs/LATEST_CODEX_REPORT.md` only.
- Unresolved blockers: exact strict failure class and candidate-2 ancestry are not retained by current bounded evidence; direct Safety/Profile-B remediation is therefore unsupported.
- Remote verification: `REQUIRED`.
- Next permitted action: `PREPARE_PHASE66_AFTER_INDEPENDENT_REMOTE_VERIFICATION`.
