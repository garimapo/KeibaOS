# Current Phase

## Identity and status

- Phase: `POST_V0_8_DAILY_REPLAY_69`
- Title: `Evidence-Backed NAR Source Profile Grammar and HTML Recovery Remediation`
- Branch: `feature/post-v0.8-daily-replay`
- Starting HEAD: `7d07f3f2e1d7ef43c5fbab50861170073d2cd788`
- State: `IMPLEMENTED_FOR_REVIEW`
- Outcome: `READY_FOR_INDEPENDENT_IMPLEMENTATION_REVIEW`
- Design Contract: `EVIDENCE_BACKED_SOURCE_PROFILE_REMEDIATION_CONTRACT_COMPLETE`
- Design Review: `PHASE69_CORRECTED_REMEDIATION_DESIGN_REVIEW_PASS`
- Version Compatibility: `FORMALLY_IMPLEMENTED`

Phase69 is a no-network authority implementation. Provider HTTP, Phase44, GET, and acquisition authorization are all `0`/`NONE`. No fixture, manifest, or other publication artifact was created.

## Implemented version authorities

Historical authority remains frozen. The unversioned Profile-B API still returns schema v1 with its original recursive candidate semantics. The unversioned Profile-A API still returns schema v2 and retains the strict nesting prerequisite. The unversioned publication Safety and every `_v2` fixture, qualification, and manifest API remain canonical v2 authority.

The additive authorities are:

- Profile-B v2: `ProfileBDiagnosticsV2` and `diagnose_nar_race_entry_status_profile_b_v2`. Only rows having exactly one table ancestor before the selected `section.raceTable`, with that table not carrying exact `changeInfo`, enter `UNIQUE_TARGET_6R`. The independent changeInfo traversal for withdrawal predicates is unchanged.
- Profile-A v3: `ProfileADiagnosticsV3` and `diagnose_nar_race_entry_status_profile_a_v3`. Exact UTF-8 and tolerant `html.parser` parsing are mandatory; XML-like nesting is not a positive prerequisite, while all explicit selectors, cardinalities, numeric horse rules, and ambiguity handling remain fail closed.
- Safety v3: `RawFixturePublicationSafetyV3` and `assess_nar_race_entry_status_raw_fixture_publication_safety_v3`. A nesting-independent streaming `HTMLParser` scans start/start-end attributes, direct sensitive names, name/id carriers with value/content, href/src/action queries, malformed percent/query cases, and Authorization/Cookie/Set-Cookie raw lines. Decode, parser, runtime, attribute, or incomplete-scan failure cannot become SAFE.
- Publication v3: `FixtureSetV3`, `QualificationV3`, `SourceProfileManifestV3`, and explicit `_v3` build/validate functions. Identities use `fixture-set-v3:` and `qualification-v3:`; paths are under `source_profiles/v3/`. Qualification v3 requires Profile-A v3 and Profile-B v2; manifest v3 requires Safety v3 SAFE plus both profiles QUALIFIED.

No ordinal, cell-count, anchor-count, link-presence, current-target, current-SHA, or provider-body special case exists. `MARKET_ELIGIBILITY`, positive market eligibility, and whole-meeting cancellation remain `UNSUPPORTED`.

## Phase50 compatibility

Phase50 now accepts and retains only these nested versions: Profile-B `{1,2}`, blocked Profile-A `{2,3}`, and blocked Safety `{2,3}`. Fixture and qualification identity patterns accept v1/v2/v3 and still require matching versions. Unsupported versions are rejected and no version is normalized.

`JOURNAL_SCHEMA_VERSION` remains `1`; top-level records, milestones, ordering, authorization semantics, `MAX_RECORD_BYTES = 4096`, `MAX_JOURNAL_BYTES = 131072`, process-stream bounds, and the v1/v2 dedicated-test-path allowlist are unchanged. Historical journal shapes remain valid. Phase63 and Phase66 production modules were not changed.

## Compatibility and security verification

Frozen v2 golden regressions retain fixture canonical length `1644` and identity digest `ac1e76922cfb0a49e03afb2c58da57ddb5ea68c3c4308279e4b090b1698bdcc6`; qualification length `2012` and identity digest `071e035ea8279b603958460550835cec529be3b02f69c28a165ddf9250e3e86b`; manifest length `4247` and SHA-256 `df40f436d40da434e3ceed6744a7204eb6d7405868cec7440934d3d817d42be0`.

Safety monotonicity passed: every exercised pre-existing UNSAFE or AMBIGUOUS condition remained non-SAFE under v3. Representative Profile-B v2, Profile-A v3, and Safety v3 Phase50 records measure `1318`, `856`, and `784` bytes including LF; their representative journal is `2958` bytes. These remain within `4096` / `131072`; limits were not raised.

Tests:

- Targeted Phase50/Profile-B/Profile-A/publication contract: `432 passed`, `0 failed`.
- Phase63/Phase66 recovery plus frozen V2 publication-plan compatibility: `261 passed`, `0 failed`.
- Full repository: `4294 passed`, `2841 subtests passed`, `0 failed`.

## Exact implementation paths

1. `scripts/simulation/nar_race_entry_status_reacquisition_observability.py`
2. `tests/test_nar_race_entry_status_reacquisition_observability.py`
3. `scripts/simulation/nar_race_entry_status_source_profile_diagnostics.py`
4. `tests/test_nar_race_entry_status_source_profile_diagnostics.py`
5. `scripts/simulation/nar_race_entry_status_source_profile_profile_a.py`
6. `tests/test_nar_race_entry_status_source_profile_profile_a.py`
7. `scripts/simulation/nar_race_entry_status_source_profile_publication_contract.py`
8. `tests/test_nar_race_entry_status_source_profile_publication_contract.py`
9. `docs/CURRENT_PHASE.md`
10. `docs/LATEST_CODEX_REPORT.md`

A separately reviewed V3 publication-plan phase is required before any v3 fixture publication. Any fresh provider validation likewise requires a new, separately reviewed current-acquisition authorization and cannot establish historical availability.

Next permitted action: `CHATGPT_REVIEW_PHASE69_IMPLEMENTATION`.
