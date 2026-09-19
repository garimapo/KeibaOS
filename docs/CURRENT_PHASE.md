# Current Phase

## Identity and authority

- Phase: `POST_V0_8_DAILY_REPLAY_68`
- Title: `Hardened Structural Diagnostic Reacquisition After Phase67 Runner Block`
- Branch: `feature/post-v0.8-daily-replay`
- Current tracked/Base HEAD: `394aae12a7613f74212084756480a6af0338d2eb`
- Executable support HEAD: `d49adc20cd75b7975947cdc956bdfbf293852ef6`
- Formal Status: `APPROVED_FOR_CODEX`
- Design Review: `PHASE68_HARDENED_RUNNER_DESIGN_REVIEW_PASS`
- Outcome: `APPROVED_HARDENED_STRUCTURAL_DIAGNOSTIC_ONE_SHOT_REACQUISITION`
- Diagnostic Contract: `HARDENED_RUNNER_STRUCTURAL_DIAGNOSTIC_CONTRACT_COMPLETE`
- Authorization: `PHASE68_STRUCTURAL_DIAGNOSTIC_ACQUISITION_AUTHORIZATION_UNCONSUMED`
- Allowed files for this APPROVE: `docs/CURRENT_PHASE.md`, `docs/LATEST_CODEX_REPORT.md` only.

This APPROVE issues authorization only. It does not perform provider HTTP, enter Phase44, write the consumption boundary, consume authorization, execute live acquisition, change production/test authority, publish, stage, commit, or push.

The proposed purpose is `CONTROLLED_REACQUISITION_FOR_STRICT_STRUCTURE_AND_CANDIDATE_ANCESTRY_DIAGNOSTICS_WITH_VALIDATED_RUNNER_ADAPTER`. The frozen target is NAR / `21` / `2025-01-01` / `6`; semantics remain `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`.

The authorization is phase-specific, target-specific, purpose-specific, support-HEAD-specific, one-shot, nontransferable, and nonrenewable after consumption. Its only consumed state is `PHASE68_STRUCTURAL_DIAGNOSTIC_ACQUISITION_AUTHORIZATION_CONSUMED_FAIL_CLOSED`. It is distinct from, and cannot reuse, Phase57, Phase64, Phase67, or Phase54 authority.

## Phase67 immutable terminal record

Phase67 is exhausted and may never be retried:

- State: `POST_AUTHORIZATION_STOP`.
- Outcome: `RECOVERY_PREFLIGHT_BLOCKED`.
- Authorization: `PHASE67_STRUCTURAL_DIAGNOSTIC_ACQUISITION_AUTHORIZATION_CONSUMED_FAIL_CLOSED`.
- Diagnostic objective: `INCOMPLETE`.
- Exact blocker: `CAPTURE_METADATA_EVENT_PAYLOAD_MISSING_CLOSED_BUNDLE_IDENTITY`.
- Phase44 entries: `1`; Deba GET/response: `1/1`; RaceList GET/response: `1/1`; total GET: `2`; post-boundary retry: `0`.

The retained Phase67 safe-final at `C:\Users\garim\AppData\Local\Temp\phase67-structural-diagnostic-40ea70f1949442a39fd090ec34eb6e49\safe-final.json` was revalidated as available: run ID `40ea70f1949442a39fd090ec34eb6e49`, byte length `9009`, SHA-256 `025bc00eb8cd6e383da7fa6383f9a7708de53576601270b9414b3b727f4cf083`, journal SHA-256 `343e3a732b8f2581884488ed559d694714c8d7c5c6edbeda2ab1c8a697403e15`, canonical safe records `17`, and last milestone `PARENT_CLEANUP_COMPLETE`.

The closed bundle was `nar-race-entry-status-raw-bundle-v1:8236b01c8aa6772d57e8081bd6bded410406930c64fd331c24ee3602f64de164`. Deba capture identity was `nar-race-entry-status-capture-v1:d43540e844e7921d217ca072c6690856595dfbc8a1d56cd97d83c3a49413ada5`, SHA-256 `6c9aa3ea614c17e14f0e7a5050190ca923445925d67f8e61e71db95e87c87727`, length `313317`; RaceList capture identity was `nar-race-entry-status-capture-v1:a413d9249cd312f0a1b3a327b65e60f2172e145d9a8a0acd508fafefa046a1c4`, SHA-256 `1eb363621c7a152929765ff7ffecabea2d7cf15283d45fa9c31036527c0b53a1`, length `66307`.

These hashes and lengths reproduce the Phase57/64 current-capture metadata: `CURRENT_ACQUISITION_BYTES_REPRODUCED_ACROSS_THREE_CONTROLLED_ACQUISITIONS`. This establishes only byte-identical current acquisitions. It does not establish 2025 bytes, historical availability/state/timing/cutoff, or market eligibility.

## Confirmed runner-only defect

Phase50 production validation is correct and unchanged. Each capture event requires `capture_metadata` with exactly these eleven fields:

1. `schema_version`
2. `document_role`
3. `request_identity`
4. `capture_identity`
5. `response_sha256`
6. `response_byte_length`
7. `requested_at`
8. `observed_at`
9. `captured_at`
10. `effective_url_matches_canonical`
11. `closed_bundle_identity`

The external Phase67 runner omitted `closed_bundle_identity`. Therefore `RUNNER_EVENT_ADAPTER_DEFECT_CONFIRMED`; it is not a Phase44, Phase50, Phase53, Phase56, Phase63, or Phase66 production defect. Those authorities and tracked tests remain unchanged. Phase68 requires no tracked production/test support change.

## Hardened external runner design

The generated, external-only runner must expose one shared helper:

`build_capture_metadata_event_payload(capture, closed_bundle_identity, document_role)`.

Both the mandatory synthetic dry run and the real live run must use this same code path. It returns exactly the eleven-key mapping above, with no extras. `closed_bundle_identity` must originate directly from the exact returned `NARRaceEntryStatusRawCaptureBundle.bundle_id` for that same bundle; it must not be recomputed, inferred, copied from stale state, or hardcoded. Before appending either `DEBA_CAPTURE_METADATA_RETAINED` or `RACELIST_CAPTURE_METADATA_RETAINED`, the runner verifies the exact key set, correct document role, non-null canonical bundle identity, identical bundle identity for both captures, and `effective_url_matches_canonical == true`. The actual Phase50 writer and its independent validator remain the final authority.

The runner must also have one shared post-acquisition processor equivalent to `process_closed_bundle(*, bundle, target, journal, mode)`. The live branch may differ from synthetic mode only when obtaining the closed bundle: each invokes this same processor thereafter. The processor owns closed-bundle retention, both capture events, ordinary Profile-B, Phase63 recovery, Phase66 ancestry, ancestry consistency, identity handling, Phase63 Safety recovery, Phase66 strict recovery, strict consistency, normal Safety, and terminal mapping. Separate toy dry-run orchestration, duplicate event assembly, and live-only post-acquisition logic are forbidden.

The runner starts a fresh isolated interpreter using `-I -B`, explicitly inserts the authorized repository path, removes `C:\Users\garim\Desktop\KeibaAI` and any other desktop source path capable of supplying `scripts`, rejects preloaded `scripts` modules, and verifies `scripts`/`scripts.simulation` package-path exclusivity plus Phase44/50/53/56/63/66 module origins. The corrected PowerShell guard captures every native Git command exit code before evaluating output; clean status requires exit code zero and a collected porcelain-output count of zero. It must not use null/empty-string comparison, trimming, joining, or normalization to decide cleanliness.

## Mandatory synthetic no-network dry run

Before any future Phase68 authorization boundary, the generated runner must execute `SYNTHETIC_NO_NETWORK_DRY_RUN` in a distinct external temporary directory and use a distinct synthetic run ID/journal. It must be structurally unable to call Phase44 or provider transport; a fail-closed acquisition/network guard is required. It uses only simple local synthetic HTML bytes and bounded synthetic identities, SHA-256 values, positive lengths, canonical ordered UTC timestamps, and `effective_url_matches_canonical=true`.

The dry run uses the same adapter and post-acquisition orchestration as the live branch, not a toy copy. It must durably append and reconstruct:

`CLOSED_BUNDLE_RETURNED` → `DEBA_CAPTURE_METADATA_RETAINED` → `RACELIST_CAPTURE_METADATA_RETAINED` → ordinary Phase53 Profile-B → Phase63 Profile-B recovery → Phase66 ancestry recovery → ancestry consistency → identity path → Phase63 Safety recovery → Phase66 strict recovery → strict consistency → unchanged Phase56 Safety → truthful synthetic `LIVE_PROCESS_COMPLETE`.

Readback through current Phase50 must prove both capture payloads contain the exact closed bundle identity from `CLOSED_BUNDLE_RETURNED.details.bundle_id`, both have exactly eleven keys, all event ordering and Phase63/66 consistency checks pass, the terminal mapping is legal, and journal syntax/semantics reconstruct. The synthetic journal is deleted after validation. A separate dry-run implementation or divergent live logic is forbidden.

Required future pre-live pass facts are `RUNNER_CAPTURE_METADATA_DRY_RUN_PASS`, `RUNNER_FULL_POST_ACQUISITION_DRY_RUN_PASS`, `CAPTURE_METADATA_EXACT_11_KEYS_PASS`, `CLOSED_BUNDLE_IDENTITY_PROPAGATION_PASS`, `DRY_RUN_PHASE50_SEMANTIC_RECONSTRUCTION_PASS`, `DRY_RUN_NO_NETWORK_PASS`, and `DRY_RUN_LIVE_LOGIC_PARITY_PASS`, in addition to every successful Phase67 no-network gate.

## Future boundary, safety, and cleanup contract

Only a real Phase68 journal may consume a future authorization: `PHASE44_CALL_ABOUT_TO_ENTER` → canonical append → flush → fsync → exactly one Phase44 call. Synthetic journals never cross that boundary. The future cap remains one Phase44 call, DebaTable then RaceList, one GET per document, and two GETs total; no retry, fallback, alternate provider/target, discovery, direct provider HTTP, or partial bundle acceptance.

After a complete real bundle, the retained order remains ordinary Profile-B → Phase63 Profile-B recovery → Phase66 ancestry → identity PASS → Phase63 Safety recovery → Phase66 strict recovery → normal Phase56 Safety → truthful terminal evidence. Phase-A is `NOT_REQUIRED`; publication, fixtures, manifests, dedicated tests, regression/publication milestones, and rollback are forbidden.

The safe-final, parent validation, and cleanup contracts remain unchanged: only allowlisted bounded evidence may remain outside the repository; no raw HTML, provider text, raw tag/class values, URLs/queries, credentials, cookies, or exception text may be retained. Parent validation must precede deletion of raw transient material. Phase68 requires a new current acquisition if the evidence is still wanted; Phase67 raw data may not be reconstructed or reused.

## Persistent constraints and readiness

`market_eligibility`, `positive_market_eligibility`, and `WHOLE_MEETING_CANCELLATION` remain `UNSUPPORTED`. Phase57 remains `POST_AUTHORIZATION_STOP` with consumed fail-closed authority; Phase64 remains `FORMALLY_COMPLETE_DIAGNOSTIC_RUN` with consumed fail-closed authority; Phase54 remains `PHASE54_AUTHORIZATION_UNCONSUMED_BUT_UNUSABLE_FOR_V2`; Phase41 remains `DESIGN_BLOCKED`.

- A Phase67 terminal evidence reviewed: YES.
- B Phase67 authorization permanently exhausted: YES.
- C runner root cause confirmed: YES.
- D production authorities remain correct: YES.
- E external runner-only remediation sufficient: YES.
- F exact capture metadata adapter designed: YES.
- G same helper used dry/live: YES.
- H synthetic closed-bundle path designed: YES.
- I synthetic capture-event validation designed: YES.
- J full post-acquisition dry run designed: YES.
- K dry run network-impossible: YES.
- L Phase50 semantic reconstruction included: YES.
- M import isolation preserved: YES.
- N PowerShell guard remediation preserved: YES.
- O one-shot boundary/cap frozen: YES.
- P safe-final/parent/cleanup contract preserved: YES.
- Q publication prohibition preserved: YES.
- R additional tracked support required: NO.

## Stop condition and next action

Provider HTTP, Phase44 calls, GET attempts, and `PHASE44_CALL_ABOUT_TO_ENTER` writes during this APPROVE are all `0`. The Phase68 authorization is unconsumed. The only changed paths are the two Phase68 documentation files; staging remains empty.

Next permitted action: `TRACK_PHASE68_AUTHORIZATION_STATE_THEN_INDEPENDENT_REMOTE_VERIFICATION`.
