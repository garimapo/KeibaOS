# Current Phase

## Status

APPROVED_FOR_CODEX

## Phase

Phase 4C-2d3b1i5c — Persisted simulation request application, deterministic JSON CLI, and file-backed E2E

## Base Commit

`cd6f8e6f8e9024c33f3dc44d5f14486d5d77fdfb docs: approve persisted simulation race inputs`

## Branch

`feature/ver0.8-simulator`

## Canonical Workspace

Use only the clean clone:

```text
C:\Users\garim\Desktop\KeibaAI-review-1i5b2b
```

The original workspace `C:\Users\garim\Desktop\KeibaAI` must not be modified.

## Objective

Add only the thin request-to-application orchestrator, deterministic JSON CLI, documentation, and their
new tests. The phase composes existing approved boundaries in this exact order:

```text
request path
→ immutable request document
→ application inputs
→ audited race inputs
→ existing SQLite application runner
→ SimulationSummary
→ deterministic JSON / CLI exit code
```

This phase must not change request parsing, application-input parsing, race/audit parsing, SQLite
composition, repositories, migrations, pipeline logic, settlement logic, or summary calculations.

## Completed Dependencies

- 1i5a: `run_sqlite_persisted_simulation()` owns one connection, migrations, composition, run, and close.
- 1i5b1: `load_persisted_simulation_request_document()` owns immutable JSON request loading.
- 1i5b2a: `assemble_persisted_simulation_application_inputs()` owns run/strategy/pipeline/budget assembly.
- 1i5b2b: `assemble_persisted_simulation_race_inputs()` owns audited immutable race-input assembly.
- The remote base and approved 1i5b2b review branch are both `cd6f8e6`.

## Allowed Implementation Files

```text
scripts/simulation/persisted_simulation_request_application.py
scripts/cli/run_persisted_simulation.py
tests/test_persisted_simulation_request_application.py
tests/test_cli_run_persisted_simulation.py
README.md
docs/LATEST_CODEX_REPORT.md
```

`docs/CURRENT_PHASE.md` is approved contract documentation and is not an implementation target.

## Forbidden Files

```text
main.py
config/settings.json
scripts/database.py
existing simulation production
existing CLI
existing tests
migration
schema
package __init__ files
database/keiba.db
logs/
```

No production/test/README modification is permitted during this design-only activity. The eventual
implementation must not stage, commit, or push without a separate explicit approval.

## Application Public API

Create only this module-defined public function in
`scripts/simulation/persisted_simulation_request_application.py`:

```python
from __future__ import annotations

from pathlib import Path

from scripts.simulation.models import SimulationSummary


def run_persisted_simulation_request(
    *,
    request_path: str | Path,
) -> SimulationSummary:
    ...
```

All helpers are private. Do not add a public class, Protocol, dataclass, ABC, repository, service bundle,
or package-root export.

## Exact Call Order

For each valid call, make exactly one call at every stage and return the exact runner result:

```python
document = load_persisted_simulation_request_document(request_path=request_path)
application_inputs = assemble_persisted_simulation_application_inputs(document=document)
race_inputs = assemble_persisted_simulation_race_inputs(
    document=document,
    application_inputs=application_inputs,
)
return run_sqlite_persisted_simulation(
    database_path=application_inputs.database_path,
    run_context=application_inputs.run_context,
    strategy_identity=application_inputs.strategy_identity,
    prediction_pipeline=application_inputs.prediction_pipeline,
    race_inputs=race_inputs,
    budgets_by_race_id=application_inputs.budgets_by_race_id,
)
```

Do not sort, copy, reparse, recreate, or recompute document/application/race inputs. The race-input
assembler owns the required sort and the runner owns SQLite lifecycle, migration, composition, and run.

## Identity and Linkage

- Pass the exact `document` object from loader to both assemblers.
- Pass the exact `application_inputs` object to race assembly.
- Pass `application_inputs.database_path`, `run_context`, `strategy_identity`, `prediction_pipeline`, and
  `budgets_by_race_id` directly to the runner; do not copy or reparse them.
- Pass the race assembler's returned tuple directly as `race_inputs`.
- Do not add linkage validation or a second sort in 1i5c; approved upstream boundaries own those checks.

## Application Exception Boundary

The application module has no `try`, `except`, retry, fallback, logging, printing, stream handling, exit
code, or exception translation. Loader, assembler, and runner exceptions propagate unchanged, by object
identity. It must not import argparse, JSON, sys, SQLite connection APIs, migrations, composition factory,
repositories, clock/environment/network/subprocess APIs, `main.py`, or configuration files.

## CLI Public APIs

Create only these module-defined public functions in `scripts/cli/run_persisted_simulation.py`:

```python
def build_parser() -> argparse.ArgumentParser: ...

def run(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int: ...

def main() -> int: ...
```

No public class, Protocol, dataclass, ABC, formatter class, repository adapter, DB provider, or package-root
export is allowed. Formatting/payload helpers remain private.

## Parser Contract

`build_parser()` has exactly one positional argument:

```python
parser.add_argument(
    "request_path",
    type=Path,
    help="Persisted simulation request JSON path",
)
```

No options are added. Native argparse behavior is preserved: missing/extra arguments raise
`SystemExit(2)`; `--help` raises `SystemExit(0)`. The CLI must not catch either outcome.

## Exit Codes

`run()` parses arguments, selects supplied streams or `sys.stdout`/`sys.stderr`, calls
`run_persisted_simulation_request()` once, emits exactly one JSON line, and returns:

```text
success: 0
expected application failure: 1
argparse usage failure: SystemExit(2)
argparse help: SystemExit(0)
```

`main()` is exactly `return run()`. Under module execution use `raise SystemExit(main())`.

## Success JSON Schema

On success write one compact UTF-8 JSON line to stdout and nothing to stderr:

```json
{"schema_version":1,"status":"ok","summary":{}}
```

Use `json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))`, followed by one
newline. Construct `summary` explicitly from all and only `dataclasses.fields(SimulationSummary)`:

```text
strategy_id strategy_name strategy_config_hash race_count settled_race_count
unsettled_race_count no_bet_race_count void_race_count error_race_count
unsupported_race_count bet_count settled_bet_count settled_purchase_race_count
hit_bet_count hit_race_count investment payout profit roi bet_hit_rate
race_hit_rate maximum_drawdown by_bet_type
```

Do not use `repr`, `dataclasses.asdict`, `default=str`, floats for Decimal values, clocks, random values,
pretty-printing, or logging metadata.

## Error JSON Schema

Catch exactly this expected failure tuple once in CLI `run()`:

```python
except (OSError, RuntimeError, TypeError, ValueError, sqlite3.Error) as error:
    ...
```

Write one compact JSON line to stderr, write nothing to stdout, and return 1:

```json
{"error":{"message":"...","type":"ValueError"},"schema_version":1,"status":"error"}
```

The type is `type(error).__name__`; message is `str(error) or type(error).__name__`. Never include a
traceback, stack trace, request/database dump, or error output on stdout. Do not catch `Exception`,
`BaseException`, `SystemExit`, `KeyboardInterrupt`, `GeneratorExit`, or `MemoryError`.

## Decimal Serialization

For `roi`, `bet_hit_rate`, and `race_hit_rate`:

```text
None       → JSON null
Decimal    → format(value, "f") as a JSON string
```

For example, `Decimal("300")` serializes as `"300"`; precision is never lost through float conversion.

## by_bet_type Serialization

Build the payload in sorted bet-type-key order, although `json.dumps(sort_keys=True)` remains enabled.
Each `BetTypeSummary` payload contains exactly:

```text
bet_type bet_count settled_bet_count hit_bet_count investment payout profit roi bet_hit_rate
```

Use the same Decimal/null serialization rules. The Japanese bet-type key is preserved with
`ensure_ascii=False`.

## Stream Contract

```python
active_stdout = sys.stdout if stdout is None else stdout
active_stderr = sys.stderr if stderr is None else stderr
```

Do not close either stream. Success writes only stdout; expected failures write only stderr. The supplied
objects need only be writable; runtime `TextIO` validation is forbidden.

## File-backed E2E

Use real files, real SQLite, and existing migrations/repository APIs without mock/patch/monkeypatch:

- Empty request with relative `simulation.db`, no races, and empty budgets verifies path anchoring,
  migration application, an empty summary, and a usable file-backed DB.
- A one-race, one-entry, no-past-race request with complete audits, 100-yen fixed stake, and 100-yen
  budget uses parent tables plus complete race result and win payout fixture. It verifies snapshot
  persistence and a settled 100 investment / 300 payout / 200 profit / `"300"` ROI summary.
- Expected errors cover invalid request path, malformed/root/application/race-audit request failures,
  database-open failure, and unknown-future migration; each returns the deterministic error envelope.

The application function must not produce partial/empty fallback summaries, retry, supply path/timezone/
clock fallbacks, or translate errors.

## README Contract

Add only the persisted-simulation CLI usage documentation: module command syntax, request JSON path,
relative `database_path` anchoring, stdout success JSON, stderr error JSON, exit codes 0/1, and Decimal
rates as JSON strings. Do not remove or alter legacy Ver0.7 CLI guidance.

## Failure Semantics

```text
loader failure              → no DB open
application assembly failure → no DB open
race assembly failure        → no DB open
runner failure               → runner owns connection close
expected CLI failure         → stderr JSON and exit 1
argparse failure             → native argparse exit
unexpected programming error → propagates
```

No partial summary, retry, fallback, error-as-success JSON, or manual DB/migration/repository work is
allowed.

## Source and AST Contract

Application source must show each four-stage collaborator exactly once, direct runner-result return,
zero `Try` and `ExceptHandler` nodes, and no SQLite/migration/composition/repository/CLI/JSON/stream/
clock/subprocess/network/config dependency. CLI may import `sqlite3` only to catch `sqlite3.Error`; it
may depend on the application function but must not import loader, assemblers, runner, migrations,
repositories, or `PredictionPipeline`. CLI has exactly the one expected exception handler and no broad
handler. Both modules have no package-root export and no type-ignore/`Any`/`cast`/`runtime_checkable`.

## Required Tests

New tests use real objects only; mock, patch, and monkeypatch are forbidden.

- Application API/public-surface/type-hint contract; exact four-stage call chain; identity/linkage;
  no exception wrapper; real empty file-backed SQLite integration; source/AST boundary.
- CLI API/parser/stream/exit contract; serializer field-completeness and byte-for-byte deterministic JSON;
  Decimal/null/by-bet-type serialization; empty and settled real file-backed E2E; expected failures;
  argparse behavior; dependency/exception AST boundaries.
- Preserve and execute the related existing suites.

## Verification Commands

Use the bundled interpreter only:

```text
C:\Users\garim\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
Python 3.12.13
```

```powershell
python -m pytest tests/test_persisted_simulation_request_application.py -q
python -m pytest tests/test_cli_run_persisted_simulation.py -q
python -m pytest tests/test_persisted_simulation_request_application.py tests/test_cli_run_persisted_simulation.py tests/test_persisted_simulation_request_document.py tests/test_persisted_simulation_application_inputs.py tests/test_persisted_simulation_race_inputs.py tests/test_sqlite_persisted_simulation_application.py tests/test_persisted_simulation_run_service.py tests/test_simulation_models.py -q
python -m pytest -q
git diff --check
git status --short
```

## Stop Conditions

After implementation, update only the report to `READY_FOR_REVIEW` and stop. Do not stage, commit, push,
create a review branch/PR, read or modify a DB, invoke the runner, modify the original workspace, or
start any later phase. Stop immediately if an approved contract conflicts with existing code or requires
a file outside Allowed Implementation Files.

blocker: none
