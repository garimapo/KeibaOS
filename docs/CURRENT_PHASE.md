# Current Phase

Status: `READY_FOR_REVIEW`

## Identity and scope

- Phase: `4C-2d3b1i6d1d5f1c4i3a0ci0`
- Name: `Remote CI SQLite Migration-Test Compatibility Correction`
- Formal base: `7cec11686e7ac02d98782834200debe24bb9d15b`
- Formal branch: `feature/ver0.8-simulator`
- Review branch:
  `review/4c-2d3b1i6d1d5f1c4i3a0ci0-jra-migration-test-ci-compatibility`

Allowed changed files are exactly:

```text
tests/test_jra_official_response_capture_migration.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## C4i3a0ci0 contract

`C4I2: FORMALLY_VERIFIED`

`C4I3A_PREPARE: ARCHITECTURE_APPROVED_WITH_BLOCKERS`

`C4I3A0: BLOCKED_PENDING_REMOTE_CI_BASELINE_CORRECTION`

The exact formal base was already remote-CI red. The correction is test-only and does
not modify production migrations, the migration contract, capture schema, parser
files, fixtures, attributes, workflow, requirements, CLI, or AI architecture.

`FORMAL_BASE_REMOTE_CI_BEFORE_CORRECTION: FAIL`

`REMOTE_CI_FAILING_TESTS:`

```text
tests/test_jra_official_response_capture_migration.py::JRAMigrationTests::test_v003_rejects_weakened_v002_schema_before_mutation
tests/test_jra_official_response_capture_migration.py::JRAMigrationTests::test_v004_rejects_lookalike_v003_before_mutation_and_rolls_back_failure
```

`REMOTE_CI_FAILING_VARIANTS: page (v002); page (v003)`

`REMOTE_CI_EXCEPTION: sqlite3.OperationalError: row value misused`

`REMOTE_CI_SQLITE_VERSION: UNAVAILABLE_FROM_WORKFLOW_LOG`

`LOCAL_SQLITE_VERSION: 3.50.4`

`REMOTE_CI_FAILURE_ROOT_CAUSE:` the fixture helper used an unbounded textual
replacement for a page-kind token. It changed both the intended column `IN (...)`
constraint and the final composite-family equality, yielding a malformed fragment such
as `page_kind='final_win_odds','other'`. GitHub Actions SQLite rejected that generated
fixture DDL before the migration validator could run.

`MIGRATION_TEST_FIXTURE_POLICY:` a valid weakened/lookalike schema must be constructed
and checked in `sqlite_master` before the formal migration validator is expected to
reject it. The helper now replaces only the first, intended occurrence and verifies the
created tables/indexes and `PRAGMA integrity_check` before each rejection probe.

`PRODUCTION_CHANGED: NO`

`MIGRATION_CONTRACT_CHANGED: NO`

`REMOTE_CI_CORRECTED_REVIEW: PASS`

`IMPLEMENTATION_BLOCKERS: NONE`

`RECOMMENDED_NEXT_PHASE:`
`C4I3A0_RESTART_FROM_NEW_FORMAL_BASE_AFTER_THIS_PHASE_FORMAL_INTEGRATION`

The deterministic baseline remains unchanged:

`FUTURE_AI_SIGNAL_ARCHITECTURE: OPTIONAL_AUDITABLE_AUGMENTATION_AFTER_VER0_8`

`AI_SIGNAL_USAGE_BASELINE: DISABLED`

`CURRENT_PHASE_AI_EFFECT: NONE`

Stop for independent ChatGPT review after the corrected review CI is confirmed. Do not
formal-integrate, modify C4i3a0 parser work, create fixtures, or begin C4i3a/C4i3b.
