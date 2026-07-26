# Current Phase

## Status

`WAITING_FOR_PHASE_INSTRUCTION`

## Phase

`NOT_SET`

## Base Commit

`69538ec`

## Branch

`feature/ver0.8-simulator`

## Objective

No phase instruction is active. Do not start implementation.

## Allowed Files

None.

## Forbidden Files

All files are forbidden until an explicit phase instruction defines the allowed scope. In every phase, do not stage or commit `database/keiba.db`, `logs/`, or anything under `logs/`.

## Required Contracts

Use `docs/VER0.8_SIMULATOR_DESIGN.md` as the authoritative design source. Do not change an established domain contract merely to make an implementation or test pass.

## Implementation Requirements

When Status is `WAITING_FOR_PHASE_INSTRUCTION`, do not change production code. When Allowed Files is empty, do not change files. Do not begin implementation without an explicit phase instruction.

## Validation and Error Handling

Follow the validation and exception policy specified by the active phase. Do not infer missing behavior; stop and report a design or contract conflict.

## Required Tests

No tests are specified until an explicit phase instruction is recorded here.

## Search Checks

No search checks are specified until an explicit phase instruction is recorded here.

## Git Safety

Do not stage, commit, or push until explicit commit approval is received. Stage only explicitly approved files by individual path.

## Completion Report

After work, update `docs/LATEST_CODEX_REPORT.md` with the actual scope, validation, test results, Git state, unchanged areas, and blockers.

## Stop Condition

Do not advance Status to the next phase autonomously. Stop for review after the active phase is complete, and also stop on a contract conflict, required out-of-scope change, unexpected Git state, or pending commit approval.
