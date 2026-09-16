# Current Phase

## Phase

`POST_V0_8_DAILY_REPLAY_60`

## Title

Tracked NAR Source-Profile v2 Publication Plan and Binary-Preservation Authority

## Status

`INTEGRATED_PENDING_REMOTE_VERIFICATION`

## Design review

`PHASE60_DESIGN_REVIEW_PASS`

## Outcome

`IMPLEMENTED_V2_PUBLICATION_PLAN_AND_BINARY_PRESERVATION_AUTHORITY`

## Execution record

- Implementation status: `INTEGRATED_PENDING_REMOTE_VERIFICATION`.
- Integration review: `PASS_FOR_INTEGRATION`.
- Remote verification: `REQUIRED`.
- Implementation manifest: exactly the five paths in this document.
- Future Phase57 live manifest: exactly the six paths in this document.
- Provider HTTP: `0`.
- Phase44 live acquisition: not entered.
- Phase57 authorization: `NOT_YET_ISSUED`.
- Next permitted action: independent remote verification only.

## Basis and prospective-authority boundary

- Authorized worktree: `C:\Users\garim\Desktop\KeibaOS-post-v0.8`.
- Branch and base/local/remote HEAD: `feature/post-v0.8-daily-replay` / `dba42a8135a9a0a66f9239e46b7cee36d90591bf`.
- Accepted predecessor: Phase57 `DESIGN_BLOCKED_TRACKED`, blocker `PHASE57_PUBLICATION_MANIFEST_AUTHORITY_UNAVAILABLE`.
- Phase58 and Phase59 are accepted as formally complete dependencies: they provide durable blocked Safety/Profile-A evidence and v2/v2 `MANIFEST_WRITTEN` identity compatibility.
- `PHASE60_PUBLICATION_PLAN_AUTHORITY_EFFECTIVE_FROM_INTEGRATION` is prospective only. The plan and binary rule become authority only after Phase60 review, approval, implementation, review, integration, independent remote verification, and `FORMALLY_COMPLETE`. It does not backfill Phase55/56/57, whose historical authority did not freeze a complete plan, the dedicated official test path, or this binary rule.

## Exact Phase60 implementation scope

The implementation delta is exactly:

1. `.gitattributes`
2. `scripts/simulation/nar_race_entry_status_source_profile_publication_plan.py`
3. `tests/test_nar_race_entry_status_source_profile_publication_plan.py`
4. `docs/CURRENT_PHASE.md`
5. `docs/LATEST_CODEX_REPORT.md`

No Phase44, Phase50, Phase53, or Phase56 change; no fixture and no dedicated fixture-backed test is created in Phase60. The new module is pure/no-network and does not acquire, parse, qualify, assess safety, construct identities or captures, write files, or mutate Git.

## Target-specific plan authority and API

The authority is intentionally target-specific to `NAR / 21 / 2025-01-01 / 6`, preventing accidental authority over unsupported future targets. It consumes a validated Phase56 `FixtureSetV2`, rejects every other target, and obtains the two raw paths from the Phase56 canonical document records. It must not reproduce Phase56 `_fixture_path` or any target-path algorithm.

Minimal public API:

- `build_nar_race_entry_status_phase57_publication_plan(*, fixture_set: FixtureSetV2) -> Phase57PublicationPlan`
- `validate_nar_race_entry_status_phase57_publication_plan(*, value: Phase57PublicationPlan, fixture_set: FixtureSetV2) -> Phase57PublicationPlan`

`Phase57PublicationPlan` is frozen and has a unique, ordered closed role/path/policy tuple plus the required attribute-rule text. Validation is fail-closed for wrong type, target, role/order, policy, path, duplication, or Phase56-path disagreement. No plan identity is added: Phase56 remains identity authority; a repository-control plan needs only deterministic tracked code, tests, and its integrating commit.

## Exact prospective Phase57 live publication delta

The unique role order and policy are:

1. `DEBA_TABLE_FIXTURE` — `tests/fixtures/nar_race_entry_status/source_profiles/v2/baba_21__2025-01-01__race_06/deba_table.html` — `CREATE_ONLY`
2. `RACE_LIST_FIXTURE` — `tests/fixtures/nar_race_entry_status/source_profiles/v2/baba_21__2025-01-01__race_06/race_list.html` — `CREATE_ONLY`
3. `MANIFEST` — `tests/fixtures/nar_race_entry_status/source_profiles/v2/baba_21__2025-01-01__race_06/manifest.json` — `CREATE_ONLY`
4. `DEDICATED_FIXTURE_TEST` — `tests/test_nar_race_entry_status_source_profile_v2_fixtures.py` — `CREATE_ONLY`
5. `CURRENT_PHASE_DOC` — `docs/CURRENT_PHASE.md` — `MODIFY_EXISTING`
6. `LATEST_CODEX_REPORT` — `docs/LATEST_CODEX_REPORT.md` — `MODIFY_EXISTING`

The manifest is target-local rather than `.../v2/manifest.json`: it co-locates the manifest with the two captured bodies and avoids a root collision if another target is separately authorized. The test name follows the existing `test_nar_race_entry_status_source_profile_*.py` convention. Phase60 freezes this six-path live contract; Phase57 creates the provider-specific test only after a successful live publication.

`.gitattributes` is Phase60 baseline support, not a future Phase57 artifact: Phase57 must validate it, must not modify it, and must never roll it back.

## Binary-preservation authority

Phase60 adds exactly this line without weakening existing rules:

```text
tests/fixtures/nar_race_entry_status/source_profiles/v2/**/*.html -text -diff
```

`-text` prevents Git text/EOL conversion of captured bytes. `-diff` follows the existing raw-fixture convention, including NAR market-odds v1, and avoids treating provider bodies as ordinary text diffs. Git attribute resolution was verified with:

```text
git -C "C:\Users\garim\Desktop\KeibaOS-post-v0.8" check-attr text diff -- tests/fixtures/nar_race_entry_status/source_profiles/v2/baba_21__2025-01-01__race_06/deba_table.html tests/fixtures/nar_race_entry_status/source_profiles/v2/baba_21__2025-01-01__race_06/race_list.html
```

Both paths report `text: unset` and `diff: unset`.

## Closed path and publication policy

All plan paths are exact, non-empty `str` values, repository-relative and forward-slash canonical. They reject drive prefixes, leading slash, `.`/`..` components, NUL/control characters, duplication, and runtime substitution. Raw paths are limited to `tests/fixtures/nar_race_entry_status/source_profiles/v2/`; the test to `tests/`; documentation paths are exact closed values.

Before future `PUBLICATION_BEGIN`, Phase57 must validate the authorized-worktree plan, fixed target, Phase56 raw-path agreement, exact entries/order/count six, absent create-only paths, existing docs, active attributes with the above `check-attr` result, and an armed rollback snapshot. Any existing create-only path fails closed.

Rollback is confined to this exact six-path Phase57 delta: it can remove newly created artifacts and restore the two docs, but cannot change `.gitattributes` or Phase60 module/test support.

## Future fixture test and test economy

The future dedicated no-network test must check raw SHA-256/length, target, roles/order, Phase56 fixture-set and qualification recomputation, manifest canonicality/validation, Safety `SAFE`, Profile-A `QUALIFIED`, Profile-B `QUALIFIED` with `EXPLICIT_WITHDRAWAL_PRESENT`, `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`, `market_eligibility=UNSUPPORTED`, and no HTTP.

Verification completed with no provider HTTP: focused publication-plan tests `29 passed`; Phase56 publication-contract tests `32 passed`; relevant Phase50/53/56 NAR regression `268 passed`; full repository suite `3869 passed, 2841 subtests passed`. Static inspection found no network, database, provider-body, file-publication, Git-mutation, or `MARKET_ELIGIBLE` implementation path.

## Result and persistent constraints

Implementation result is:

```text
Phase: POST_V0_8_DAILY_REPLAY_60
Status: INTEGRATED_PENDING_REMOTE_VERIFICATION
Outcome: IMPLEMENTED_V2_PUBLICATION_PLAN_AND_BINARY_PRESERVATION_AUTHORITY
```

It requires the exact five-path support delta, prospective plan, frozen six-path future live plan, active/verified attributes, frozen rollback policies, no network, required tests, empty staging/untracked state, and `git diff --check` pass.

- Phase57 remains `DESIGN_BLOCKED` and `PHASE57_ACQUISITION_AUTHORIZATION_NOT_YET_ISSUED`; after Phase60 formal completion it must be re-prepared, reviewed, approved, and receive a new explicit authorization.
- Phase54: `PHASE54_AUTHORIZATION_UNCONSUMED_BUT_UNUSABLE_FOR_V2`.
- Phase41: `DESIGN_BLOCKED`.
- `positive_market_eligibility = UNSUPPORTED`; `WHOLE_MEETING_CANCELLATION = UNSUPPORTED`.
- Open: `COMBINATION_EV_REQUIRES_MARKET_ODDS_CAPTURE`; `NAR_MARKET_ELIGIBILITY_REQUIRES_INDEPENDENT_ENTRY_STATUS_CAPTURE`.
- Provider HTTP: `0`; Phase44 live acquisition: not entered.
- No official fixture or future fixture-backed test was created. Phase44/50/53/56 are unchanged. This integration is committed and pushed without marking Phase60 formally complete.
