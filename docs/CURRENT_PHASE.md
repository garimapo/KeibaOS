# Current Phase

## Status

WAITING_FOR_PHASE_INSTRUCTION

## Phase

NOT_SET

## Base Commit

`b7e142e`

## Branch

`feature/ver0.8-simulator`

## Allowed Files

None.

## Forbidden Files

All files until a phase is prepared and approved, including production code, tests, schema,
migrations, `database/keiba.db`, and `logs/`.

## Required Tests

Not set. No implementation or test execution is authorized while this phase is waiting.

## Stop Condition

Wait for `PREPARE_PHASE <phase ID>` from the user. Do not infer or begin a phase.
