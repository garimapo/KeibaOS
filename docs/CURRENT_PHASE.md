# Current Phase

## Status

READY_FOR_REVIEW

## Phase

`4C-2d3b1i6d1d5f1c1` — JRA accessD capture v003.

Formal base: `776cd9123635eef3759284ff997a369857f3769e`.

Approved design: `ff217c3fdc4b1249d057909ad974430851710ed5`.

Review branch: `review/4c-2d3b1i6d1d5f1c1-jra-accessd-capture-v003`.

## Allowed Files

```text
scripts/simulation/jra_official_identity.py
scripts/simulation/jra_official_response_capture.py
scripts/simulation/jra_official_response_capture_migration_runner.py
scripts/simulation/jra_official_response_capture_migration_v003.py
scripts/simulation/repositories/sqlite_jra_official_response_capture_repository.py
tests/test_jra_official_identity.py
tests/test_jra_official_response_capture.py
tests/test_jra_official_response_capture_migration.py
tests/test_sqlite_jra_official_response_capture_repository.py
tests/test_jra_official_response_live_capture.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Frozen Contract

`parse_jra_race_card_url_identity` accepts only canonical accessD URLs. Supplied
responses may recognize accessS/accessU/accessD, while the existing v1 canonicalizer
and `JRAOfficialResponseCapture` remain accessS/accessU-only. Schema-v3
`JRAOfficialTargetRaceCardResponseCapture` is GET-only, derives deterministic
`jra-capture-v3` identity, and converts to the existing supplied-response type.

Archive APIs stay family-specific. v003 validates v002, reuses response bodies,
rebuilds only captures, preserves both partial indexes and every v1/v2 row and ID.
Valid foreign-family IDs return `None`; requested-family corruption fails closed.

## Required Tests and Stop Condition

Run dedicated identity/capture/repository/migration/live suites, related JRA
regressions, full pytest, and `git diff --check`. No live accessD acquisition, target
parser, source records, snapshots, Predictor, bridge, package export, or unrelated
schema work is authorized. Stop after one review commit and push only this branch.
