# Current Phase

## Status

APPROVED_FOR_COMMIT

## Phase

Phase 4C-2d3b1i6b3a1 — Python 3.14 / Windows verification compatibility

## Base Commit

`12ff00b45e2e4a8bc5761f3210fd45685a2a3dbb feat: add historical input snapshot save repository`

## Branch

`feature/ver0.8-simulator`

## Canonical Workspace

`C:\Users\garim\Desktop\KeibaAI-review-1i5b2b`

The original workspace, `C:\Users\garim\Desktop\KeibaAI`, is not a modification target.

## Objective

Restore a clean, reproducible Windows Python 3.14 full-suite verification baseline before Phase
4C-2d3b1i6b3b begins. This is a maintenance-only phase for exactly two observed compatibility issues:
the missing Windows IANA time-zone database in a fresh development/test environment, and portability of
unknown-attribute assignment assertions for frozen slotted dataclasses. No feature or production behavior
changes.

## Root Cause

At the formal base, Python 3.14.5 with pytest 8.3.5 in an isolated Windows TEMP venv passed the b3a
dedicated suite (`9 passed`), historical domain/v010 migration suite (`22 passed, 3 subtests passed`), and
existing SQLite repository/migration suite (`63 passed, 70 subtests passed`). The full suite reported
`3 failed, 2404 passed`.

Before this phase, `requirements.txt` contained only `beautifulsoup4==4.15.0` and `requests==2.34.2`, while
`requirements-dev.txt` contained only `pytest==8.3.5`. A clean Windows environment therefore had no declared
IANA time-zone data. `ZoneInfo("Asia/Tokyo")` is used by the SQLite snapshot repository test. No production
module imports `ZoneInfo`; the resolved need is a Windows development/test dependency rather than a production
runtime requirement.

The three failures are limited to assignment of an unknown attribute on frozen, slotted dataclasses:

- `PersistedRaceSettlementDataTests.test_uses_slots`
- `RaceSettlementDataTests.test_uses_slots`
- `SimulationBetPlanIdentityTest.test_uses_slots_and_rejects_new_attributes`

Before this phase, each test expected `TypeError`. On Python 3.14.5 the same rejected assignment raises
`dataclasses.FrozenInstanceError`. The frozen and no-arbitrary-attribute semantics remain intact. Existing
declared-field mutation tests already require `FrozenInstanceError` and are not part of this correction.

## CI and Supported-Python Findings

`README.md` documents Python 3.12 or later. The sole GitHub Actions workflow,
`.github/workflows/tests.yml`, runs pytest only on `ubuntu-latest` with Python 3.12 and installs both
requirements files. It does not exercise Windows or Python 3.14. This maintenance phase makes the documented
Windows developer/test installation reproducible; it does not expand the CI matrix.

## Implemented Dependency Rule

`requirements-dev.txt` now contains exactly this Windows-only development dependency:

```text
tzdata==2026.3; sys_platform == "win32"
```

The existing pytest pin remains unchanged. The exact pin follows the existing requirements convention and the
PEP 508 environment marker installs the IANA database only where the fresh Windows verification environment
needs it. `requirements.txt` remains unchanged because no production `ZoneInfo` dependency was found.

## Implemented Test Changes

Only unknown/new-attribute portability assertions changed:

- In `tests/test_persisted_settlement_contract.py`, add `self.assertFalse(hasattr(value, "__dict__"))` to
  `test_uses_slots`, then accept `(TypeError, FrozenInstanceError)` for `value.unexpected = ...`.
- In `tests/test_settlement_contract.py`, make the same structural slots assertion and accepted-exception
  adjustment in `test_uses_slots`.
- In `tests/test_simulation_bet_plan_identity.py`, retain its existing no-`__dict__` assertion and change only
  the unknown-attribute expectation to `(TypeError, FrozenInstanceError)`.

Do not modify `PersistedRaceSettlementData`, `RaceSettlementData`, or `SimulationBetPlanIdentity`. Do not
weaken declared-field frozen tests: they must continue to require `FrozenInstanceError`.

## Allowed Files

- `requirements-dev.txt`
- `tests/test_persisted_settlement_contract.py`
- `tests/test_settlement_contract.py`
- `tests/test_simulation_bet_plan_identity.py`
- `docs/CURRENT_PHASE.md`
- `docs/LATEST_CODEX_REPORT.md`

No production file was required or changed.

## Forbidden Files

- `requirements.txt`, all production modules, all migration/schema/runner files, and all other tests.
- `scripts/simulation/repositories/sqlite_historical_input_snapshot_repository.py` and
  `tests/test_sqlite_historical_input_snapshot_repository.py`.
- Historical snapshot domain, v010 migration, b3b load implementation, V3c, README, CI configuration,
  `database/keiba.db`, and `logs/`.
- Any dataclass implementation change intended only to preserve an old exception type.

## Verification Results

Using a fresh isolated TEMP venv outside the repository with Python 3.14.5:

1. Installed only `-r requirements.txt -r requirements-dev.txt`; no manual `pip install tzdata` occurred.
2. Confirmed pytest `8.3.5`, tzdata `2026.3`, and successful `ZoneInfo("Asia/Tokyo")` resolution.
3. The three corrected contract modules passed: `96 passed`.
4. `tests/test_sqlite_historical_input_snapshot_repository.py` passed: `9 passed`.
5. Historical snapshot/v010 migration tests passed: `22 passed`.
6. Existing SQLite repository/migration regression tests passed: `63 passed`.
7. The full suite passed: `2407 passed`.
8. `git diff --check` succeeded with only the allowed files changed.

## Approval

ChatGPT design review approved this phase for Codex implementation. The approved Windows-only development/test
dependency is exactly:

```text
tzdata==2026.3; sys_platform == "win32"
```

It was not added to `requirements.txt` or made unconditional. The fresh outside-repository Python 3.14.5 TEMP
venv installed only both repository requirements files, without a separate `pip install tzdata`, then resolved
`ZoneInfo("Asia/Tokyo")` and reported pytest `8.3.5` and tzdata `2026.3`.

For each of the three named compatibility tests, only an unknown/new attribute assignment may accept
`(TypeError, FrozenInstanceError)`. The two settlement tests must retain the explicit no-`__dict__` structural
assertion; the identity test's existing structural assertion remains without duplication. Declared-field mutation
tests must continue to require `FrozenInstanceError`.

No production change was authorized or made.

## Deferred Work and Stop Condition

Phase 4C-2d3b1i6b3b remains deferred and unimplemented. Do not begin b3b, V3c, or any feature work in this
phase. Implementation is complete; stop at `READY_FOR_REVIEW` awaiting ChatGPT commit review. Do not stage,
commit, or push without separate explicit authorization.
