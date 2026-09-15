# Current Phase

## Phase

POST_V0_8_DAILY_REPLAY_58

## Name / state

Tracked Phase57 Safety and Profile-A Failure-Evidence Durability Support — Design Revision 1

- Type: NO_NETWORK_OBSERVABILITY_DURABILITY_DESIGN
- Status: INTEGRATED_PENDING_REMOTE_VERIFICATION
- Outcome: IMPLEMENTED_PHASE57_FAILURE_EVIDENCE_DURABILITY_SUPPORT
- Branch: feature/post-v0.8-daily-replay
- Base: 3f4703c559ec24b52962c423efd62e919301f5da
- Predecessor: POST_V0_8_DAILY_REPLAY_57 — DESIGN_BLOCKED
- Authorization: no Phase58 live authority; `PHASE57_ACQUISITION_AUTHORIZATION_NOT_YET_ISSUED`
- Provider HTTP: 0
- Phase44 live acquisition: NOT_AUTHORIZED

- Revision: PHASE58_DESIGN_REVISION_1
- Design Review: PHASE58_DESIGN_REVIEW_PASS
- Formal Status: INTEGRATED_PENDING_REMOTE_VERIFICATION
- Review: PASS_FOR_INTEGRATION
- Implementation Manifest: four approved paths
- Phase44 Changes: NOT_AUTHORIZED
- Phase53 Changes: NOT_AUTHORIZED
- Phase56 Changes: NOT_AUTHORIZED
- Provider HTTP: 0
- Phase57 Authorization: NOT_YET_ISSUED
- Remote Verification: REQUIRED

The authorized worktree is `C:\Users\garim\Desktop\KeibaOS-post-v0.8`. Phase54 remains `PHASE54_AUTHORIZATION_UNCONSUMED_BUT_UNUSABLE_FOR_V2`. Phase57 is not authorized.

## Frozen Phase57 blockers and revised principle

Phase57 remains blocked for `DESIGN_BLOCKED_SAFETY_FAILURE_EVIDENCE_NOT_DURABLE` and `DESIGN_BLOCKED_PROFILE_A_FAILURE_EVIDENCE_NOT_DURABLE`. Existing durable evidence remains capture metadata through `DEBA_CAPTURE_METADATA_RETAINED` and `RACELIST_CAPTURE_METADATA_RETAINED`, and Profile-B diagnostics through `PROFILE_B_DIAGNOSTICS_RETAINED`.

Phase58 resolves only the two missing failure domains. Existing success milestones remain success evidence and are not duplicated:

1. a Phase56 safety result of `SAFE` is evidenced by `SAFETY_PASS`;
2. a non-`SAFE` safety result is retained by one new typed event before fail-closed cleanup;
3. a qualified Profile-A result is evidenced by `PROFILE_A_QUALIFIED`;
4. a blocked Profile-A result is retained by one new typed event before fail-closed cleanup.

`SAFETY_PASS` and `PROFILE_A_QUALIFIED` establish that their respective gates passed. They do not reconstruct a complete domain result and do not need to retain success-only diagnostics. Complete in-memory canonical results remain available for a successful manifest/publication path; a failed Phase57 run only needs to establish that an earlier gate passed or identify the exact blocking gate safely.

## Verified Profile-A blocked invariant

For every result emitted by the tracked public evaluator `diagnose_nar_race_entry_status_profile_a`, `overall_result == BLOCKED` implies that `SELECTED_NON14_LISTING.safe_fields.selected_provider_horse_no` is exactly `null`.

The implementation proves this by control flow: a non-PASS table scope forces shape and listing to `UNSUPPORTED` with `selected = None`; a non-PASS row shape forces listing to `UNSUPPORTED` with `selected = None`; no eligible ordinary horse and duplicate eligible horses likewise set `selected = None`; only the all-PASS branch assigns `selected = min(eligible)`, which makes the overall result `QUALIFIED`. The focused Profile-A tests cover each blocking source category and assert their non-PASS outcomes/blocked result. The Phase58 validator will independently require `null`, so a forged numeric value cannot enter the journal.

This statement concerns canonical outputs of the sole approved evaluator, not arbitrary construction of private implementation objects. No Phase56 production or test change is required to support the Phase58 event contract.

## New exact typed Phase50 retention events

Phase50 remains an operational observability layer. It must not import or execute Phase56 evaluators or parsers. It may only validate already-computed, safe, closed canonical projections with local structural allowlists.

### `PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED`

This event is permitted only for a Phase56 non-safe result. Its details object has exactly one key, `publication_safety`, whose value is exactly:

~~~json
{
  "schema_version": 2,
  "result": "UNSAFE|AMBIGUOUS|UNSUPPORTED",
  "raw_fixture_publication_safe": false,
  "category_results": [
    {"identifier": "NO_AUTHENTICATION_MATERIAL", "outcome": "SAFE|UNSAFE|AMBIGUOUS|UNSUPPORTED", "finding_count": 0},
    {"identifier": "NO_COOKIE_OR_SESSION_SECRET", "outcome": "SAFE|UNSAFE|AMBIGUOUS|UNSUPPORTED", "finding_count": 0},
    {"identifier": "NO_CSRF_OR_SECRET_TOKEN", "outcome": "SAFE|UNSAFE|AMBIGUOUS|UNSUPPORTED", "finding_count": 0},
    {"identifier": "NO_USER_ACCOUNT_IDENTIFIER", "outcome": "SAFE|UNSAFE|AMBIGUOUS|UNSUPPORTED", "finding_count": 0},
    {"identifier": "NO_PERSONALIZATION_IDENTIFIER", "outcome": "SAFE|UNSAFE|AMBIGUOUS|UNSUPPORTED", "finding_count": 0}
  ]
}
~~~

The category order is exact. Every `finding_count` is an exact integer in `0..10000`. The validator rederives the aggregate: all SAFE gives SAFE; otherwise any UNSAFE gives UNSAFE; otherwise any UNSUPPORTED gives UNSUPPORTED; otherwise AMBIGUOUS. It rederives the boolean as true only for SAFE and rejects SAFE from this blocking event. Phase56 has no primary-category field; parent reporting must deterministically derive the first non-SAFE category from the fixed order rather than persist a caller-controlled duplicate.

### `PROFILE_A_BLOCKED_DIAGNOSTICS_RETAINED`

This event is permitted only for a Phase56 Profile-A blocked result. Its details object has exactly one key, `profile_a_blocked_diagnostics`. The value is the closed, target-free blocked projection below:

~~~json
{
  "schema_version": 2,
  "profile": "ENTRY_LISTING_PRESENT",
  "overall_result": "BLOCKED",
  "terminal_semantic": null,
  "predicate_results": [
    {"identifier": "ENTRY_TABLE_SCOPE", "outcome": "PASS|FAIL|AMBIGUOUS|UNSUPPORTED", "safe_fields": {"entry_table_scope_count": 0}},
    {"identifier": "ORDINARY_HORSE_ROW_SHAPE", "outcome": "PASS|FAIL|AMBIGUOUS|UNSUPPORTED", "safe_fields": {"ordinary_row_count": 0}},
    {"identifier": "SELECTED_NON14_LISTING", "outcome": "PASS|FAIL|AMBIGUOUS|UNSUPPORTED", "safe_fields": {"selected_non14_candidate_count": 0, "selected_provider_horse_no": null}}
  ],
  "first_nonpass_predicate": "ENTRY_TABLE_SCOPE|ORDINARY_HORSE_ROW_SHAPE|SELECTED_NON14_LISTING",
  "terminal_reason": "UNSUPPORTED_INPUT|FIRST_NONPASS_PREDICATE"
}
~~~

The event deliberately omits `target`. The preceding `TARGET_CONSTRUCTED` record already establishes the target under the same run ID. Parent validation must bind this record to that same run ID and to the preceding canonical target record; it must not accept a blocked Profile-A event without that predecessor. Omitting the redundant target makes the durable event smaller without losing run-level audit binding.

The validator requires exactly three ordered predicate records and their exact field sets; all count fields are exact integers in `0..10000`; `selected_provider_horse_no` is exactly null; `first_nonpass_predicate` is non-null and must equal the earliest non-PASS predicate; and `terminal_reason` is `UNSUPPORTED_INPUT` iff any predicate is UNSUPPORTED, otherwise `FIRST_NONPASS_PREDICATE`. It rejects QUALIFIED, a terminal semantic, an all-PASS result, or every extra field.

## Exact ordering, durability, and parent contract

`JOURNAL_SCHEMA_VERSION` remains `1`. Phase53 added typed retained milestones without changing this version, and Phase58 remains strictly additive: no prior event, canonical JSON rule, observer mapping, preflight token, authorization accounting, cleanup rule, or existing semantic rule changes.

The enum must insert the new milestones without changing the relative rank of any existing milestone:

1. `CLOSED_BUNDLE_RETURNED`
2. `DEBA_CAPTURE_METADATA_RETAINED`
3. `RACELIST_CAPTURE_METADATA_RETAINED`
4. existing `PROFILE_B_DIAGNOSTICS_RETAINED`
5. `IDENTITY_VERIFICATION_PASS`
6. safety evaluation:
   - SAFE: existing `SAFETY_PASS`;
   - otherwise: `PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED`, then fail closed.
7. Profile-A evaluation after safety PASS:
   - QUALIFIED: existing `PROFILE_A_QUALIFIED`;
   - otherwise: `PROFILE_A_BLOCKED_DIAGNOSTICS_RETAINED`, then fail closed.
8. existing `PROFILE_B_QUALIFIED` only when the retained Profile-B result is qualified.
9. `PUBLICATION_BEGIN` only after every success gate.

Each blocked event uses the existing writer path: canonical JSON serialization, one LF, write, flush, and `fsync`. Only after a successful append may the child clean raw bytes or terminate for that blocked gate. The semantic validator must permit a blocked event followed only by terminal operational evidence (`LIVE_PROCESS_COMPLETE`, parent validation, and cleanup), require the existing capture/identity/safety predecessors as applicable, and reject contradictory `SAFETY_PASS`, `PROFILE_A_QUALIFIED`, `PROFILE_B_QUALIFIED`, or `PUBLICATION_BEGIN` after blocked evidence. Parent validation must check run-ID continuity, sequence/rank monotonicity, closed details, target-predecessor binding, first blocking milestone, and absence of contradictory success evidence.

## Finite payload and full-record bounds

All new nested fields are fixed allowlist strings, booleans, null, or counts bounded by the existing Phase50 bound of 10000. The former unbounded selected-provider-horse value is structurally impossible in the blocked event.

Using canonical JSON, every category outcome at its longest permitted spelling, all counts at 10000, a six-digit sequence (the journal's 131072-byte total cap makes a larger sequence unattainable), a 32-character run ID, and canonical UTC text:

| Event | Inner canonical projection | Details wrapper | Complete JSON record | Record plus required LF | Margin to 4096 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED` | 552 | 575 | 846 | 847 | 3249 |
| `PROFILE_A_BLOCKED_DIAGNOSTICS_RETAINED` | 581 | 615 | 882 | 883 | 3213 |

The existing writer and reader separately enforce `MAX_RECORD_BYTES = 4096`; the finite field bounds above ensure the new details themselves cannot exhaust it. No Phase50 limit change is needed.

## Test plan and implementation scope

Focused Phase50 tests must prove:

- acceptance and durable canonical round-trip for non-SAFE blocked safety results, including all five category outcomes; SAFE rejection; aggregate/boolean rederivation; bounded counts; rejection of extra/raw/secret/arbitrary text/URL fields; full-record size; and unchanged `SAFETY_PASS` and preflight token;
- acceptance of blocked Profile-A FAIL, AMBIGUOUS, and UNSUPPORTED results; QUALIFIED rejection; required null selected horse; numeric selected-horse rejection; fixed predicate order; earliest-non-PASS and terminal-reason rederivation; bounded counts; closed-schema/raw/URL rejection; full-record size; durable round-trip; and unchanged `PROFILE_A_QUALIFIED`;
- retained capture/Profile-B behavior, old journal/preflight validity, monotonic ordering, and no network.

The exact Phase58 implementation manifest is four paths:

1. `scripts/simulation/nar_race_entry_status_reacquisition_observability.py`
2. `tests/test_nar_race_entry_status_reacquisition_observability.py`
3. `docs/CURRENT_PHASE.md`
4. `docs/LATEST_CODEX_REPORT.md`

No Phase44, Phase53, or Phase56 production/test change is required. Future execution order is focused observability tests, minimal Phase56 interoperability checks if needed, relevant NAR regression, and one full suite when otherwise ready.

## Future boundary

Phase58 implemented both blocked-only retention events with closed local validators and existing canonical write/flush/fsync durability. `PUBLICATION_SAFETY_BLOCKED_RESULT_RETAINED` rejects SAFE results and retains only the bounded five-category non-safe result. `PROFILE_A_BLOCKED_DIAGNOSTICS_RETAINED` rejects QUALIFIED results and numeric selected-horse values, requires the exact three predicates, and retains only the target-free bounded blocked projection. Complete maximum records including LF remain 847 and 883 bytes respectively.

Existing `SAFETY_PASS`, `PROFILE_A_QUALIFIED`, capture retention, Profile-B retention, journal schema version 1, and the exact preflight token are unchanged. Phase44, Phase53, and Phase56 are unchanged. Static inspection confirms that Phase50 gained no Phase56 domain import, provider-network path, database access, or raw-provider persistence.

Verification completed with 137 focused observability tests passing, 301 relevant NAR tests passing, and the full repository suite passing with 3807 tests and 2841 subtests. Provider HTTP remained zero and Phase44 live acquisition was not entered.

After Phase58 is formally complete, Phase57 must return to PREPARE/review. It still requires explicit APPROVE and a new one-shot Phase57 authorization; none is issued automatically. Phase41 remains `DESIGN_BLOCKED`; `positive_market_eligibility` and `WHOLE_MEETING_CANCELLATION` remain `UNSUPPORTED`.

## Approved implementation contract

Allowed files are exactly:

1. `scripts/simulation/nar_race_entry_status_reacquisition_observability.py`
2. `tests/test_nar_race_entry_status_reacquisition_observability.py`
3. `docs/CURRENT_PHASE.md`
4. `docs/LATEST_CODEX_REPORT.md`

Forbidden: every other repository path; Phase44, Phase53, and Phase56 changes; fixtures; `.gitattributes`; provider HTTP; Phase44 live acquisition; Phase57 authorization issuance; Phase54 authorization consumption; staging; commit; and push.

Required execution tests: focused Phase50 observability tests; only minimal no-network Phase56 interoperability if necessary; relevant NAR regression; and the full repository suite once when otherwise ready. The implementation must prove both blocked events reject closed-schema violations and unsafe data, preserve existing `SAFETY_PASS`, `PROFILE_A_QUALIFIED`, capture retention, Profile-B retention, and preflight behavior, retain no raw/secret data, and preserve journal schema version 1.

Integration state: `INTEGRATED_PENDING_REMOTE_VERIFICATION`. Do not mark Phase58 formally complete, issue Phase57 authorization, or advance phases until independent remote verification is explicitly recorded.
