# Current Phase

## Phase

POST_V0_8_DAILY_REPLAY_53

## Name / state

Tracked NAR Profile-B Qualification Diagnostics and Failure-Evidence Retention

- Type: NO_NETWORK_SUPPORT_IMPLEMENTATION
- Status: INTEGRATED_PENDING_REMOTE_VERIFICATION
- Outcome: IMPLEMENTED_PROFILE_B_DIAGNOSTIC_SUPPORT
- Branch: feature/post-v0.8-daily-replay
- Base: c796e45467184efad97f312c605a67c65865b21b
- Predecessor: POST_V0_8_DAILY_REPLAY_52 — APPROVED_FOR_CODEX / PHASE52_DESIGN_REVIEW_PASS

Design Review: PHASE53_DESIGN_REVIEW_PASS.

Review: PASS_FOR_INTEGRATION.

Next permitted action: INDEPENDENT_REMOTE_VERIFICATION.

Implementation manifest: scripts/simulation/nar_race_entry_status_source_profile_diagnostics.py; tests/test_nar_race_entry_status_source_profile_diagnostics.py; scripts/simulation/nar_race_entry_status_reacquisition_observability.py; tests/test_nar_race_entry_status_reacquisition_observability.py; docs/CURRENT_PHASE.md; docs/LATEST_CODEX_REPORT.md.

Phase44 change: NOT_AUTHORIZED.

Phase50 change: ADDITIVE_TYPED_RETENTION_ONLY.

Future Phase54: NEW_AUTHORIZATION_REQUIRED.

## Historical invariants

Phase51 remains SOURCE_PROFILE_FIXTURE_BLOCKED, PHASE51_ACQUISITION_AUTHORIZATION_CONSUMED_FAIL_CLOSED, and PHASE51_REACQUISITION_NOT_AUTHORIZED. Historical Profile-B root cause remains HISTORICAL_PROFILE_B_FAILURE_ROOT_CAUSE_UNRECOVERABLE_FROM_RETAINED_EVIDENCE. Confirmed gaps remain QUALIFICATION_IMPLEMENTATION_COLLAPSED_FAILURES and QUALIFICATION_PREDICATE_DIAGNOSTICS_NOT_RETAINED.

Phase52 immediate direction is NO_NEW_ACQUISITION_YET. Future live work remains POST_V0_8_DAILY_REPLAY_54_REQUIRES_NEW_AUTHORIZATION. Phase41 remains DESIGN_BLOCKED. OPEN dependencies remain COMBINATION_EV_REQUIRES_MARKET_ODDS_CAPTURE and NAR_MARKET_ELIGIBILITY_REQUIRES_INDEPENDENT_ENTRY_STATUS_CAPTURE. Neither Profile B nor Phase53 establishes MARKET_ELIGIBLE; WHOLE_MEETING_CANCELLATION and positive_market_eligibility remain UNSUPPORTED.

## Exact six Profile-B predicates

The identifiers and order are frozen. Profile B means only EXPLICIT_WITHDRAWAL_PRESENT.

| Order / identifier | Source and deterministic scope | PASS | FAIL | AMBIGUOUS | UNSUPPORTED | Safe fields |
| --- | --- | --- | --- | --- | --- | --- |
| 1 RACE_TABLE_SCOPE | strict-UTF-8 RaceList bytes parsed in the pure layer; `section.raceTable` schedule scope | approved scope evaluable | no scope | competing scopes | decode/required DOM unavailable | `race_table_scope_count` |
| 2 UNIQUE_TARGET_6R | direct `tr.data`, first direct `td` normalized to target `6R` | count exactly 1 | count 0 | count >1 | direct row/cell unavailable | `target_race_no`, `target_6r_row_count` |
| 3 DEBA_LINK_RELATIONSHIP | anchors only in the unique target row; parsed path exactly `/KeibaWeb/TodayRaceInfo/DebaTable` | count exactly 1 | count 0 | count >1 | href/path cannot be evaluated | `deba_relationship_count`, `deba_relationship_present` |
| 4 DEBA_LINK_QUERY_BINDING | that relationship link has exactly one each target query date/no/baba | count exactly 1 | count 0 | count >1 | query multiplicity/value cannot be evaluated | `deba_query_binding_count`, `deba_query_binding_match` |
| 5 WITHDRAWAL_ROW_SHAPE | `table.changeInfo tr.data`, exactly six direct `td` cells | candidate row evaluable | count 0 | competing qualifying candidates | required table/cells unavailable | `withdrawal_row_shape_count` |
| 6 HORSE_14_WITHDRAWAL_ASSOCIATION | same direct cells 1/2/4 normalize to target `6R`, numeric 14, exact `出走取消` | count exactly 1 | count 0 | count >1 | numeric/status normalization impossible | `withdrawn_provider_horse_no`, `horse_14_withdrawal_count`, `withdrawal_label_match` |

No title, time, horse-name, jockey, or recovery association exists. Predicate outcome vocabulary is exactly PASS, FAIL, AMBIGUOUS, UNSUPPORTED. Overall qualification is QUALIFIED only when all six are PASS, otherwise BLOCKED. `first_nonpass_predicate` is the earliest non-PASS predicate in this table order; terminal reason is QUALIFIED, FIRST_NONPASS_PREDICATE, or UNSUPPORTED_INPUT.

## Input authority and pure tracked module

Phase53 adds exactly `scripts/simulation/nar_race_entry_status_source_profile_diagnostics.py`. It is pure, deterministic, no-network, no database, no filesystem persistence, no clock, no environment dependency, and no mutable global state.

Its primary API is `diagnose_nar_race_entry_status_profile_b(*, race_list_bytes: bytes, target: NARRaceEntryStatusRaceIdentity) -> ProfileBDiagnostics`. `target` must be the exact immutable Phase44 public type; query values derive only from it. The frozen Profile-B horse/status values remain 14 and `出走取消`. Input bytes must strict-decode as UTF-8. The module uses already available BeautifulSoup with `html.parser`; direct-child traversal and the six frozen selectors/checks are deterministic. Decode failure and an unavailable required structure return the applicable UNSUPPORTED predicate result. The layer never repairs, normalizes into a new source body, or writes input.

## Immutable diagnostic result

`ProfileBDiagnostics` and `ProfileBPredicateResult` are frozen dataclasses/StrEnums. The canonical `profile_b_diagnostics_v1` representation has exactly:

```json
{
  "schema_version": 1,
  "profile": "EXPLICIT_WITHDRAWAL_PRESENT",
  "overall_result": "QUALIFIED|BLOCKED",
  "terminal_semantic": "EXPLICIT_WITHDRAWAL_PRESENT",
  "target": {"baba_code": "21", "race_date": "2025-01-01", "race_no": 6},
  "predicate_results": [{"identifier": "<frozen identifier>", "outcome": "PASS|FAIL|AMBIGUOUS|UNSUPPORTED", "safe_fields": {}}],
  "first_nonpass_predicate": "<identifier>|null",
  "terminal_reason": "QUALIFIED|FIRST_NONPASS_PREDICATE|UNSUPPORTED_INPUT"
}
```

The six result records are ordered exactly as the table. Only the table's safe fields, exact identifiers/outcomes, bounded nonnegative integer counts, target 6, horse 14, and booleans are accepted. Raw HTML, DOM fragments, arbitrary source text, URLs/query strings, attributes, headers, cookies, credentials, tokens, sessions, account/user values, exception reprs, paths, and environment values are rejected.

No separate deterministic identity is added: canonical immutable result bytes plus the durable journal record are sufficient, while a new identity would create no additional authority and invite accidental cross-run use. Canonical bytes use `json.dumps(... ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")`; they exclude raw input, timestamps, run/PID/path, and runtime state.

## Capture metadata summary and journal composition

The same module supplies `summarize_nar_race_entry_status_capture_bundle(*, bundle: NARRaceEntryStatusRawCaptureBundle) -> CaptureMetadataSummary`. It accepts only the exact Phase44 bundle type and fails closed if formal fields are missing or contradictory. It contains, for each role, request identity, capture identity, response SHA-256, byte length, requested_at/observed_at/captured_at in the existing UTC text format, and boolean `effective_url_matches_canonical`; it also contains the closed bundle identity. It does not contain raw bodies or URLs.

Responsibility remains separated:

- Phase44 owns acquisition and all formal capture/bundle identities; its public API is unchanged.
- The new Phase53 module owns Profile-B predicates and immutable safe source/capture summaries.
- Phase50 observability owns durable generic execution evidence, not parsing.
- Future orchestration composes publication safety, Profile A, Profile B diagnostics, capture metadata, and operational journal evidence without folding them into fixture identity.

Phase53 necessarily makes a narrow additive change to `scripts/simulation/nar_race_entry_status_reacquisition_observability.py`: new ordered evidence milestones `DEBA_CAPTURE_METADATA_RETAINED`, `RACELIST_CAPTURE_METADATA_RETAINED`, and `PROFILE_B_DIAGNOSTICS_RETAINED`, after CLOSED_BUNDLE_RETURNED and before IDENTITY_VERIFICATION_PASS. Their detail validators accept only the fixed safe capture fields above and the canonical profile_b_diagnostics_v1 object. This is evidence transport only; it does not import or execute the domain parser, alter Phase44, or change Phase50 public APIs. The future child computes the pure summaries and passes only validated values to the journal.

## Phase53 implementation manifest

1. `scripts/simulation/nar_race_entry_status_source_profile_diagnostics.py` — new pure diagnostics and capture-summary support.
2. `scripts/simulation/nar_race_entry_status_reacquisition_observability.py` — narrow additive safe journal schema/validator/milestone support.
3. `tests/test_nar_race_entry_status_source_profile_diagnostics.py` — new synthetic-only no-network tests.
4. `tests/test_nar_race_entry_status_reacquisition_observability.py` — focused journal-schema retention regressions.
5. `docs/CURRENT_PHASE.md`
6. `docs/LATEST_CODEX_REPORT.md`

No Phase44 change is required: every retained field already exists on its public formal objects. Phase50 change is required only because the current journal has no typed place to retain capture summaries or predicate diagnostics after a child failure; a composition-side stdout or generic opaque blob would violate the durable allowlisted evidence contract.

## Synthetic test matrix

All inputs are inline/minimal synthetic HTML, named synthetic, not provider evidence and not source-profile fixtures. Tests cover: valid unique target 6R; missing/duplicate 6R; horse 14 withdrawal; horse 14 without withdrawal; withdrawal for another horse; nonnumeric horse; missing/malformed/multiple Deba relationship; wrong query binding; multiple withdrawal rows; ambiguous association; valid elements in the wrong scope; malformed source structure; deterministic repetition/order/first failure; raw/source-text exclusion; canonical result serialization; summary completeness; and missing/contradictory capture metadata failing closed. They also cover journal retention/validation of the three new events without network.

Future EXECUTE order: focused Phase53 tests during development; relevant NAR regression once; full suite once only when ready. No HTTP in any test. Phase53 completion does not acquire data, qualify the target, publish fixtures, unblock Phase41, or authorize Phase54.

## PREPARE scope

Only docs/CURRENT_PHASE.md and docs/LATEST_CODEX_REPORT.md change in this PREPARE. Forbidden: implementation, tests, fixtures, .gitattributes, HTTP, Phase44 entry, staging, commit, push, and Phase54. Required final check: git diff --check. Stop at DRAFT_FOR_REVIEW.

## Phase53 approval record

The six predicate identifiers, order, parser/input authority, immutable `profile_b_diagnostics_v1` result schema, no-identity decision, and separate capture-metadata summary are approved unchanged. Profile B remains only EXPLICIT_WITHDRAWAL_PRESENT; no predicate or aggregate result implies MARKET_ELIGIBLE.

The only approved foundational change is the narrow additive Phase50 journal extension for DEBA_CAPTURE_METADATA_RETAINED, RACELIST_CAPTURE_METADATA_RETAINED, and PROFILE_B_DIAGNOSTICS_RETAINED. Existing schema/version, milestones, sequence/canonical/allowlist contracts, preflight, authorization semantics, stream classification, cleanup, and Phase44 mapping remain unchanged. If implementation needs any existing Phase50 semantic contract change, it must stop as IMPLEMENTATION_BLOCKED_PHASE50_CONTRACT_CHANGE_REQUIRED. Any Phase44 change stops as IMPLEMENTATION_BLOCKED_PHASE44_CHANGE_REQUIRED.

Synthetic Phase53 tests remain no-network and non-official. Phase53 completion does not authorize Phase54; Phase54 requires formal integration/verification of Phase53, all synthetic and retention tests, Phase50 preflight, import smoke, Git gate, and a new explicit one-shot authorization.

## Phase53 implementation result

The approved pure diagnostics module now implements the six frozen predicates in their exact order over strict-UTF-8 RaceList bytes plus exact formal Phase44 target identity. Its immutable `profile_b_diagnostics_v1` result retains only the approved safe counts/booleans and deterministic predicate outcomes, first non-PASS predicate, and terminal reason. Canonical bytes are repeatable; there is no separate diagnostic identity and no MARKET_ELIGIBLE semantic.

The separate immutable capture-metadata summary is constructed only from a revalidated formal Phase44 bundle. It retains request/capture identities, SHA/length, all six UTC timestamps, closed-bundle identity, and effective-URL-match booleans, without raw bodies or URL values. Missing or contradictory formal metadata fails closed.

Phase50 observability now accepts only the three approved typed retention milestones in the frozen location: `DEBA_CAPTURE_METADATA_RETAINED`, `RACELIST_CAPTURE_METADATA_RETAINED`, and `PROFILE_B_DIAGNOSTICS_RETAINED`. Exact nested allowlists, types, identity formats, count bounds, timestamp/order checks, role checks, canonical JSON, and prerequisite ordering are enforced. Existing Phase50 journal version, existing events and meanings, preflight, authorization, stream, cleanup, and Phase44 observer mapping remain unchanged. Phase44 itself is unchanged.

Verification passed without network: focused diagnostics 23 passed; affected Phase50 observability 83 passed; relevant NAR regression 540 passed plus 514 subtests; full repository suite 3,707 passed plus 2,841 subtests; static in-memory compile PASS; git diff --check PASS. Tests prove deterministic six-predicate ordering/outcomes and first non-PASS selection, raw/unsafe URL-query exclusion, capture metadata retention alongside qualification failure, strict rejection of unsafe fields by all three new events, and unchanged old Phase50 preflight behavior.

Repository scope remains exactly the approved six paths; index remains empty. No HTTP, Phase44 acquisition, official fixture, manifest, `.gitattributes`, database/log, Phase54, stage, commit, or push action occurred. Phase51 remains blocked and consumed; Phase41 remains DESIGN_BLOCKED; Phase54 remains unauthorized.

## Phase53 integration record

Phase53 is integrated locally and pending independent remote verification. The reviewed implementation remains exactly the six-path manifest: tracked six-predicate diagnostics, separate capture-metadata summary, and the three additive typed Phase50 retention events. Phase44 is unchanged; HTTP was not performed; Phase51 remains blocked/non-retryable; Phase41 remains DESIGN_BLOCKED; Phase54 is not authorized and requires a new one-shot acquisition authorization. This state is not FORMALLY_COMPLETE.
