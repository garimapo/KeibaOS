# Current Phase

## POST_V0_8_DAILY_REPLAY_79

**Title:** Deterministic V3 Dedicated Fixture-Test Generation, End-to-End Preflight, and Failure Evidence Authority
**Status:** READY_FOR_REVIEW
**State:** IMPLEMENTED_FOR_REVIEW
**Design Review:** PHASE79_DEDICATED_TEST_HARDENING_DESIGN_REVIEW_PASS
**Outcome:** READY_FOR_INDEPENDENT_IMPLEMENTATION_REVIEW
**Design Contract:** V3_DEDICATED_FIXTURE_TEST_EXECUTION_AND_FAILURE_EVIDENCE_AUTHORITY_COMPLETE
**Support:** V3_DEDICATED_FIXTURE_TEST_EXECUTION_AND_FAILURE_EVIDENCE_AUTHORITY_IMPLEMENTED

### Execution baseline

- Branch: `feature/post-v0.8-daily-replay`
- Base Commit: `e1e176291e0a79ad79f807c64b35d67da4851469`
- Base Tree: `d2d1593adfa95835ed59d37cb0e35f33945e118b`
- Authorized worktree: `C:\Users\garim\Desktop\KeibaOS-post-v0.8`

### Frozen prior state

- Phase76: TERMINAL_CONSUMED_BLOCKED_ROLLBACK_COMPLETE.
- Phase76 review: PHASE76_CONSUMED_BLOCKED_RESULT_REVIEW_PASS.
- Phase76 authorization: PHASE76_V3_SOURCE_PROFILE_PUBLICATION_AUTHORIZATION_CONSUMED_FAIL_CLOSED.
- Dedicated-test blocker: REGRESSION_FAILURE_AT_DEDICATED_V3_FIXTURE_TEST.
- Underlying cause: UNKNOWN_AFTER_BOUNDED_EVIDENCE_GAP. No assertion or root cause may be inferred.
- Phase78: NOT_ENTERED_NO_PUBLICATION_DELTA and must not be repurposed.

### Allowed Files

The subsequent `EXECUTE_APPROVED_PHASE` may modify or create exactly:

1. `scripts/simulation/nar_race_entry_status_source_profile_fixture_test_generator.py`
2. `scripts/simulation/nar_race_entry_status_source_profile_fixture_test_preflight.py`
3. `tests/test_nar_race_entry_status_source_profile_fixture_test_generator.py`
4. `tests/test_nar_race_entry_status_source_profile_fixture_test_preflight.py`
5. `docs/CURRENT_PHASE.md`
6. `docs/LATEST_CODEX_REPORT.md`

### Forbidden Files and actions

Every path outside Allowed Files is forbidden. In particular, no existing source-profile contract, publication-plan, Profile-A, Profile-B, Phase50, Phase63, Phase66, raw-capture module, `.gitattributes`, `database/**`, or `logs/**` may change. An unavoidable need to change another path stops with PHASE79_APPROVED_CONTRACT_SUPPORT_MISMATCH.

Phase79 performs no provider HTTP, Phase44, GET, live authorization, acquisition, publication, staging of publication artifacts, or Phase76 reuse.

### Approved renderer API

```python
render_nar_race_entry_status_source_profile_v3_fixture_test(
    *,
    deba_table_bytes: bytes,
    race_list_bytes: bytes,
    manifest: SourceProfileManifestV3,
    publication_plan: SourceProfilePublicationPlanV3,
) -> bytes
```

The renderer requires exact types, is pure and deterministic, and has no filesystem writes, provider network, subprocess, clock, randomness, environment lookup, or mutable global state. It derives hashes, lengths, fixture-set identity, and qualification identity from exact raw bytes and formal V3 authority; it accepts no duplicate caller-supplied expected values.

Before rendering it must validate the formal V3 manifest and plan, their target/path relationship, SHA-256 and lengths of both raw documents, Profile-A v3 QUALIFIED, Profile-B v2 QUALIFIED, Safety v3 SAFE, market eligibility UNSUPPORTED, current-acquisition semantics, and the exact `FUTURE_OFFICIAL_FIXTURE_TEST_REQUIREMENTS_V3` tuple.

It emits UTF-8, LF-only, BOM-free, compilable Python source and rejects output larger than `MAX_GENERATED_FIXTURE_TEST_BYTES = 65536`. Generated source uses portable `Path(__file__)` repository-relative fixture resolution and contains no raw HTML, absolute worktree path, temporary path, clock, random identifier, or provider access.

### Approved preflight and evidence contract

The preflight module builds deterministic qualified synthetic V3 authority, an external mirror without a `scripts/` package, invokes the approved renderer, and executes actual pytest. The mandatory future gate is `V3_DEDICATED_FIXTURE_TEST_END_TO_END_PREFLIGHT_PASS`.

The launcher uses `python -I -B`, injects only the authorized worktree root, validates exactly one PEP 420 `scripts` namespace portion and every required `scripts.simulation.*` module origin, rejects KeibaAI/alternate roots/mirror-side `scripts`, uses `--import-mode=importlib`, and disables uncontrolled plugin autoload where practicable.

The preflight retains a bounded immutable evidence result: generated source SHA/length; manifest SHA/length; pytest command and return code; stdout/stderr SHA, original length, classification, and safe bounded result; pass state; external mirror root; and import-isolation result. It reuses Phase50 `MAX_PROCESS_STREAM_BYTES` and `sanitize_process_stream` where applicable.

Before a future live rollback, retain and durably validate generated source, bounded validated manifest, fixture hashes/lengths, V3 identities, command/return code, and sanitized process evidence. The order is pytest failure, evidence retention and durability, ROLLBACK_BEGIN, rollback, then ROLLBACK_COMPLETE.

Canonical SourceProfileManifestV3 bytes are retainable only after formal V3 validation and only at or below `MAX_FAILURE_MANIFEST_BYTES = 32768`; otherwise retain SHA/length and safe projection only, without truncating canonical bytes. No raw HTML is retained.

### Required tests

Run exactly in this order during the subsequent execution:

1. `tests/test_nar_race_entry_status_source_profile_fixture_test_generator.py`
2. `tests/test_nar_race_entry_status_source_profile_fixture_test_preflight.py`
3. `tests/test_nar_race_entry_status_source_profile_publication_plan.py`
4. `tests/test_nar_race_entry_status_source_profile_publication_contract.py`
5. `tests/test_nar_race_entry_status_source_profile_diagnostics.py`
6. `tests/test_nar_race_entry_status_source_profile_profile_a.py`
7. `tests/test_nar_race_entry_status_source_profile_structural_recovery_diagnostics.py`
8. `tests/test_nar_race_entry_status_reacquisition_observability.py`
9. full repository suite

The new focused tests must cover exact-type/V2/dict/duck rejection, target/plan/manifest/raw-byte contradiction, nonqualified and non-SAFE authority rejection, deterministic source, LF/BOM/size/compile requirements, external isolation failures, and actual-pytest fixture/manifest/target/identity/market mutations.

### Implementation evidence

- The exact renderer API is implemented with `MAX_GENERATED_FIXTURE_TEST_BYTES = 65536`.
- The external preflight uses an external mirror, `python -I -B`, importlib pytest mode, disabled plugin autoload, exact PEP 420 namespace validation, and production-module origin validation.
- Deterministic synthetic topology produces Phase63 candidates 2, Phase66 candidates 2, direct schedule 1, changeInfo 1, and structural consistency 1 == 1.
- Actual generated-test pytest: 4 passed, return code 0.
- Gate: V3_DEDICATED_FIXTURE_TEST_END_TO_END_PREFLIGHT_PASS.
- Generated source: SHA-256 `447535319ad465f44df2fd1e03cab6988d284ea5431e9badc01454e3de7264ef`, 10462 bytes.
- Synthetic manifest: SHA-256 `0be206f04b8a7a4a6bffa3bc83e6eb8527a034870ecf82366b995f8be338eb46`, 4247 bytes.
- Import isolation: PASS.
- Independent external-pytest mutations fail for Deba bytes, RaceList bytes, manifest bytes, expected Deba SHA, expected RaceList length, target race number, fixture-set identity, qualification identity, and market eligibility.
- Missing/alternate roots, mirror-side `scripts`, a second namespace portion, and outside module origins fail closed.
- Failure evidence retains safe generated source, bounded formally validated manifest or safe projection, fixture/authority identities, command/result, Phase50-sanitized streams, safe failing nodes, and full stream hashes/lengths.
- Durable failure evidence support uses exclusive creation, flush, fsync, and byte-exact readback validation before rollback.
- `MAX_FAILURE_MANIFEST_BYTES = 32768`; canonical manifest bytes are never truncated.
- Generator purity audit and preflight static scope audit passed.

### Test results

1. Generator: 17 passed.
2. Preflight: 17 passed.
3. Publication plan: 45 passed.
4. Publication contract: 49 passed.
5. Profile-B diagnostics: 38 passed.
6. Profile-A: 17 passed.
7. Phase66 structural recovery: 152 passed.
8. Phase50 observability: 367 passed.
9. Full suite: 4383 passed and 2841 subtests passed.

Provider HTTP, Phase44, and GET remained 0 / 0 / 0. Authorization is NONE. Publication is NO. Phase76 remains TERMINAL_CONSUMED_BLOCKED_ROLLBACK_COMPLETE, and Phase78 remains NOT_ENTERED_NO_PUBLICATION_DELTA. Any future live publication requires a new Phase80-or-later one-shot authorization after independent review and must pass the committed end-to-end preflight.

### Git and stop condition

Only after all tests and scope checks pass: individually stage the six Allowed Files, commit with `feat: harden V3 fixture test generation preflight`, and push normally. The expected parent is the Base Commit. Never use bulk add, amend, force push, or stage/commit database or logs.

Implementation is complete within the exact approved six-path scope. The next action is `CHATGPT_REVIEW_PHASE79_IMPLEMENTATION`.
