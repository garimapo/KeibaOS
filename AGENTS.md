# KeibaOS Codex Working Agreement

## Roles and work order

- ChatGPT owns design, review, QA, and phase management.
- Codex owns implementation, tests, diff checks, and work reports.
- Work proceeds as: design, implementation, review, explicit commit approval, push, then the next phase.
- The authoritative detailed design is `docs/VER0.8_SIMULATOR_DESIGN.md`.
- Codex must update `docs/LATEST_CODEX_REPORT.md` before stopping after every authorized activity.
- Codex must never advance to a subsequent phase on its own initiative.

## Phase workflow commands

### `PREPARE_PHASE <phase ID>`

When the user issues this command, Codex must:

1. Read this file, `docs/VER0.8_SIMULATOR_DESIGN.md`, and `docs/LATEST_CODEX_REPORT.md`.
2. Inspect recent Git history, current branch, and working-tree status.
3. Investigate the requested phase's implementation scope without changing production code or tests.
4. Draft `docs/CURRENT_PHASE.md` for that phase with status `DRAFT_FOR_REVIEW`.
5. Write a preparation report to `docs/LATEST_CODEX_REPORT.md`.
6. Stop for review.

`PREPARE_PHASE` must not implement code, add tests, stage, commit, or push.

### `APPROVE_PHASE`

The user supplies this command followed by either required corrections or `NONE`.
Codex must apply only those corrections to `docs/CURRENT_PHASE.md`, set its status to
`APPROVED_FOR_CODEX`, and stop. Production code and tests remain unchanged until a later
`EXECUTE_APPROVED_PHASE` instruction.

### `EXECUTE_APPROVED_PHASE`

Before implementing, Codex must verify that `docs/CURRENT_PHASE.md`:

- has status `APPROVED_FOR_CODEX`;
- names a Phase whose Base Commit and Branch match the current Git state;
- declares Allowed Files and Forbidden Files; and
- declares Required Tests and Stop Condition.

Only when all checks pass may Codex implement the approved phase, restricted to its Allowed
Files. Otherwise it must not implement and must report the missing or inconsistent contract.

## Allowed phase statuses

`docs/CURRENT_PHASE.md` may use only these statuses:

```text
WAITING_FOR_PHASE_INSTRUCTION
DRAFT_FOR_REVIEW
APPROVED_FOR_CODEX
READY_FOR_REVIEW
APPROVED_FOR_COMMIT
```

## Scope and contract rules

- Change only files listed in the current phase's Allowed Files.
- If the design and an existing contract conflict, stop and report; do not make a speculative change.
- Do not change domain contracts for convenience.
- Do not add production APIs merely to satisfy tests.
- Do not infer missing behavior or silently broaden a phase's scope.

## Permanent Git safety rules

Do not stage, commit, or push without explicit user approval. The following commands are prohibited:

```text
git add .
git add -A
git commit -a
git clean
git reset
git restore
git stash
git commit --amend
git rebase
force push
```

When approved, stage only individually named files. Never stage or commit:

```text
database/keiba.db
logs/
logs/配下すべて
```

The ordinary permitted dirty state is:

```text
 M database/keiba.db
?? logs/
```

## KeibaOS domain invariants

- Keep `SimulationSummary.race_count` as the formal field; never add `target_race_count`.
- Preserve Engine -> Predictor -> Value -> Generator -> Strategy -> Pipeline -> CLI responsibility boundaries.
- Do not confuse prediction cutoff with settlement cutoff, or reject settlement data merely because it is later than prediction time.
- Do not change recommendation count, order, or object identity without explicit design approval.
- Do not confuse recommendation rank with purchase order.
- Do not equate horse IDs and race-entry IDs without verification.
- Repositories must not repair saved data automatically or silently overwrite immutable snapshots.

## Verification and stop conditions

At the end of every implementation or workflow-maintenance activity, run:

```text
git diff --check
git status --short
```

Run the phase's dedicated, related, full-suite, and search checks exactly as specified. Clearly report anything not run.

Stop rather than continuing when:

- design and implementation contracts conflict;
- a change outside Allowed Files is needed;
- schema or migration work belongs to another phase;
- an existing behavior would need to be guessed;
- a test fails for an out-of-scope reason;
- Git status contains an unexpected file; or
- commit approval is required.
