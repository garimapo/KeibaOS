# Latest Codex Report

## Status

READY_FOR_REVIEW

## Activity

KeibaOS Codex handoff workflow maintenance

## Updated files

- `AGENTS.md`
- `docs/CURRENT_PHASE.md`
- `docs/LATEST_CODEX_REPORT.md`

## New command-driven workflow

### Prepare

`PREPARE_PHASE <phase ID>` is documentation and scope preparation only. Codex reads the
working agreement, simulator design, latest report, and current Git state; researches the
requested phase; writes a `DRAFT_FOR_REVIEW` phase document and preparation report; then
stops. It must not change production code or tests, run implementation work, stage, commit,
or push.

### Review approval

`APPROVE_PHASE` carries either corrections or `NONE`. Codex applies the specified corrections
to `docs/CURRENT_PHASE.md`, changes status to `APPROVED_FOR_CODEX`, and waits for the separate
execution command. It does not implement code or tests at this step.

### Execution

`EXECUTE_APPROVED_PHASE` may execute only after verifying that the phase document is
`APPROVED_FOR_CODEX`, its Phase/Base Commit/Branch match current Git state, and its Allowed
Files, Forbidden Files, Required Tests, and Stop Condition are complete. Otherwise Codex stops
without implementation.

## Status vocabulary

Only these statuses are valid for `docs/CURRENT_PHASE.md`:

```text
WAITING_FOR_PHASE_INSTRUCTION
DRAFT_FOR_REVIEW
APPROVED_FOR_CODEX
READY_FOR_REVIEW
APPROVED_FOR_COMMIT
```

## Current reset state

`docs/CURRENT_PHASE.md` is reset to:

```text
Status: WAITING_FOR_PHASE_INSTRUCTION
Phase: NOT_SET
Base Commit: b7e142e
Branch: feature/ver0.8-simulator
Allowed Files: None
```

No next implementation phase is authorized.

## Safety preserved

- Explicit approval remains mandatory before staging, committing, or pushing.
- `database/keiba.db`, `logs/`, and all contents under `logs/` remain permanently excluded from staging and commits.
- The permanent bans on `git add .`, `git add -A`, `git commit -a`, clean, reset, restore, stash, amend, rebase, and force push remain in force.
- The domain invariants including `SimulationSummary.race_count` and no `target_race_count` remain documented in `AGENTS.md`.

## Verification

No production code or test was changed, so pytest was not rerun. `git diff --check` succeeds.
The final working tree contains only the three workflow documents plus the pre-existing
`database/keiba.db` modification and untracked `logs/` directory.

Stage, commit, and push were not performed. Review is required before any further action.
