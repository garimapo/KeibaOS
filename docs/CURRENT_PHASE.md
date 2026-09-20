# Current Phase

## Phase75 V3 publication-plan implementation

- Phase: `POST_V0_8_DAILY_REPLAY_75`
- Title: `V3 Source-Profile Publication Plan Authority After Successful Phase74 Validation`
- Branch: `feature/post-v0.8-daily-replay`
- Starting tracking HEAD: `11e1aace4aae68640d0d38f88b38873d1bac5abd`
- Validated executable support HEAD/tree: `b2355113f969f6af713a254355e67a9feab5cc45` / `24b4f37391039e1ece2d573b4a0ea3f0de65e4cd`
- Worktree: `C:\Users\garim\Desktop\KeibaOS-post-v0.8`
- Status: `IMPLEMENTED_FOR_REVIEW`
- Outcome: `READY_FOR_INDEPENDENT_IMPLEMENTATION_REVIEW`
- Design Contract: `V3_SOURCE_PROFILE_PUBLICATION_PLAN_CONTRACT_COMPLETE`
- Support: `V3_SOURCE_PROFILE_PUBLICATION_PLAN_AUTHORITY_IMPLEMENTED`

## Frozen predecessor evidence

Phase74 is `FORMALLY_COMPLETE`; its evidence review is `PHASE74_VERSIONED_VALIDATION_EVIDENCE_REVIEW_PASS`. It ended `READY_FOR_REVIEW` with Phase50 outcome `READY_FOR_REVIEW` and authorization `PHASE74_VERSIONED_SOURCE_PROFILE_VALIDATION_AUTHORIZATION_CONSUMED_FAIL_CLOSED`. Its durable boundary, one Phase44, Deba/RaceList GET `1 / 1`, total GET `2`, retry `0`, and no-publication result are final.

Phase74 validates a current acquisition only. It establishes Profile-B v2 schema `2` as `QUALIFIED`, Safety v3 schema `3` as `SAFE`, and Profile-A v3 schema `3` as `QUALIFIED`; it does not establish historical availability, historical bytes, cutoff validity, or market eligibility. `market_eligibility`, `positive_market_eligibility`, and `WHOLE_MEETING_CANCELLATION` remain `UNSUPPORTED`.

Raw Phase74 capture bytes, journal, runner, and probe artifacts were removed. Bounded safe-final evidence is design input only and must never be used to reconstruct or substitute raw fixtures. Any V3 fixture publication requires a future fresh controlled current acquisition and a new one-shot authorization bound to reviewed post-Phase75 support.

## Phase75 implemented support

Allowed future implementation paths are exactly:

1. `scripts/simulation/nar_race_entry_status_source_profile_publication_plan.py`
2. `tests/test_nar_race_entry_status_source_profile_publication_plan.py`
3. `.gitattributes`
4. `docs/CURRENT_PHASE.md`
5. `docs/LATEST_CODEX_REPORT.md`

The implementation is additive and freezes every V2 authority: `Phase57PublicationPlan`, V2 constants/paths, V2 builder/validator, and V2 tests remain unchanged. Phase75 adds separate `SourceProfilePublicationPlanV3`, explicit V3 constants, a V3 builder, and a V3 validator. Both V3 entrypoints accept only exact `FixtureSetV3` and call `validate_nar_race_entry_status_fixture_set_v3`; V2 objects, dictionaries, duck types, coercion, conversion, or V2 fallback are rejected.

The V3 plan is pure planning/validation code. It introduces no network, subprocess, database, clock, randomness, filesystem-write behavior, raw bytes, arbitrary URLs, or provider values.

## Frozen V3 publication-plan authority

Target authority is exact: provider `NAR`, baba code `21`, race date `2025-01-01`, race number `6`. Fixture paths must derive from `FixtureSetV3.to_canonical_dict()` and be exactly:

1. `tests/fixtures/nar_race_entry_status/source_profiles/v3/baba_21__2025-01-01__race_06/deba_table.html`
2. `tests/fixtures/nar_race_entry_status/source_profiles/v3/baba_21__2025-01-01__race_06/race_list.html`
3. `tests/fixtures/nar_race_entry_status/source_profiles/v3/baba_21__2025-01-01__race_06/manifest.json`
4. `tests/test_nar_race_entry_status_source_profile_v3_fixtures.py`
5. `docs/CURRENT_PHASE.md`
6. `docs/LATEST_CODEX_REPORT.md`

The role order is respectively `DEBA_TABLE_FIXTURE`, `RACE_LIST_FIXTURE`, `MANIFEST`, `DEDICATED_FIXTURE_TEST`, `CURRENT_PHASE_DOC`, `LATEST_CODEX_REPORT`. The first four are `CREATE_ONLY`; the two docs are `MODIFY_EXISTING`. The future `.gitattributes` policy is `VALIDATE_ONLY`, after tracked Phase75 support adds exactly `tests/fixtures/nar_race_entry_status/source_profiles/v3/**/*.html -text -diff`.

The frozen V3 fixture-test requirements are:

```text
EXACT_DEBA_SHA256
EXACT_DEBA_BYTE_LENGTH
EXACT_RACELIST_SHA256
EXACT_RACELIST_BYTE_LENGTH
EXACT_TARGET
DOCUMENT_ROLE_ORDER
FIXTURE_SET_V3_RECOMPUTATION
QUALIFICATION_V3_RECOMPUTATION
MANIFEST_V3_CANONICAL_SERIALIZATION
MANIFEST_V3_VALIDATION
PUBLICATION_SAFETY_V3_SAFE
PROFILE_A_V3_QUALIFIED
PROFILE_B_V2_QUALIFIED
PROFILE_B_ALL_SIX_PREDICATES_PASS
PROFILE_B_TARGET_SCHEDULE_COUNT_ONE
PHASE66_DIRECT_SCHEDULE_COUNT_ONE
PROFILE_B_PHASE66_STRUCTURAL_CONSISTENCY
PROFILE_B_EXPLICIT_WITHDRAWAL_PRESENT
CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET
MARKET_ELIGIBILITY_UNSUPPORTED
NO_NETWORK
```

Qualification remains exact `ProfileADiagnosticsV3` plus `ProfileBDiagnosticsV2`, represented through `QualificationV3`; Safety remains exact `RawFixturePublicationSafetyV3`, `SAFE`, and all five categories safe; manifest remains exact `SourceProfileManifestV3` and must round-trip through `validate_nar_race_entry_status_manifest_v3`. Phase63/Phase66 are supplemental only. Structural consistency is only Profile-B v2 schedule count equals Phase66 direct-schedule count; it is never compared with broader Phase63/Phase66 totals.

## Readiness and stop condition

The approved implementation completed within the five listed paths. Raw V3 fixtures and the V3 manifest are `NOT_PUBLISHED`; future publication requires a new one-shot authorization bound to the reviewed post-Phase75 executable support. Provider HTTP, Phase44, GET, acquisition authorization, fixture/manifest write, and publication remain absent.

Required tests for the later implementation include V2 regression preservation; V3 target/path/entry/policy determinism; exact FixtureSetV3 acceptance and V2 rejection; malformed paths, role reordering, missing/duplicate entries, and V2-path substitution rejection; V3 `.gitattributes` validation; frozen requirement tuple coverage; and static no-side-effect checks.

Next permitted action: `CHATGPT_REVIEW_PHASE75_IMPLEMENTATION`.
