# Current Phase

## Status

APPROVED_FOR_CODEX

## Phase

Phase 4C-2d3b1i5b1 — Persisted simulation request document loader

## Base Commit

`c5933aa docs: approve SQLite persisted simulation application runner`

## Branch

`feature/ver0.8-simulator`

## Objective

Load one UTF-8 JSON request file, reject malformed/non-deterministic document forms, validate its
strict top-level envelope, anchor a relative database path to the request file, and return a deeply
immutable request document:

```text
request JSON path
-> UTF-8 read
-> duplicate-key rejection
-> strict JSON parse
-> exact top-level schema validation
-> relative database path anchoring
-> recursive immutable snapshot
-> PersistedSimulationRequestDocument
```

This phase does not build simulation domain objects or invoke the application runner.

## Phase Split

```text
1i5b1: JSON document loader and strict top-level envelope
1i5b2: document-to-domain/application input assembler
1i5c: CLI, exit code, stdout/stderr, and Summary output
```

1i5b1 must not create `SimulationRunContext`, `StrategyConfig`, `StrategyIdentity`,
`PredictionPipeline`, `SimulationRaceInput`, `InputSnapshotAudit`, `PastRace`, `BetStakeBudget`, or
`SimulationSummary`.

## Allowed Files

```text
scripts/simulation/persisted_simulation_request_document.py
tests/test_persisted_simulation_request_document.py
docs/LATEST_CODEX_REPORT.md
```

`docs/CURRENT_PHASE.md` is approved contract documentation and is not an implementation target.

## Formal Production API

New module: `scripts/simulation/persisted_simulation_request_document.py`

```python
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PersistedSimulationRequestDocument:
    schema_version: int
    source_path: Path
    database_path: Path
    run_context: Mapping[str, object]
    strategy: Mapping[str, object]
    pipeline: Mapping[str, object]
    races: tuple[Mapping[str, object], ...]
    budgets_by_race_id: Mapping[str, object]


def load_persisted_simulation_request_document(
    *,
    request_path: str | Path,
) -> PersistedSimulationRequestDocument:
    ...
```

These are the only public production definitions. Private helpers are permitted. Do not add an
application request bundle, domain assembler, database connection, runner wrapper, CLI parser,
summary formatter, repository, Protocol, or abstract class.

## Schema Version and Exact Envelope

Schema version is exactly integer `1`; `bool` is invalid. The only top-level keys are:

```text
schema_version
database_path
run_context
strategy
pipeline
races
budgets_by_race_id
```

Missing or extra keys raise `ValueError("request JSON keys must exactly match the request schema")`.
Key order is irrelevant. The formal minimal document is:

```json
{
  "schema_version": 1,
  "database_path": "database/simulation.db",
  "run_context": {},
  "strategy": {},
  "pipeline": {},
  "races": [],
  "budgets_by_race_id": {}
}
```

## Request Path and File Read

Before file read accept a non-empty `str`, `Path`, or `Path` subclass only. Reject `None`, bytes,
bytearray, int, bool, arbitrary objects, empty/whitespace paths, and NUL-containing paths as
`ValueError("request_path must be a non-empty path")`.

```python
if not isinstance(request_path, (str, Path)):
    raise ValueError("request_path must be a non-empty path")
source_path = Path(request_path)
request_path_text = str(request_path)
if not request_path_text.strip() or "\x00" in request_path_text:
    raise ValueError("request_path must be a non-empty path")
```

Do not call `resolve()`, canonicalize/symlink-resolve, pre-check existence, or alter the source
path. Read only with `source_path.read_text(encoding="utf-8")`. Translate `UnicodeDecodeError` to
`ValueError("request file must be UTF-8")`; propagate every other `OSError` unchanged. Do not strip
a BOM, use a fallback encoding/path, or retry.

## Strict JSON Parse

Use standard-library `json` only. Translate `json.JSONDecodeError` to
`ValueError("request file must contain valid JSON")`.

All object levels must reject duplicate keys using `object_pairs_hook`; duplicate top-level keys,
nested `run_context` keys, and nested race-item keys raise
`ValueError("request JSON must not contain duplicate object keys")`. Do not permit last-write-wins.

Reject `NaN`, `Infinity`, `-Infinity`, and finite-range overflow to float infinity at every level.
Use `parse_constant` and recursive `math.isfinite` validation; raise
`ValueError("request JSON must not contain non-finite numbers")`. Do not catch this or duplicate-key
`ValueError` as generic JSON decode failure.

## Root and Field Validation

The JSON root must be exact `dict`, otherwise
`ValueError("request JSON root must be an object")`. Validate fields without any domain interpretation:

- `schema_version`: exact non-bool integer `1`, otherwise `ValueError("schema_version must be 1")`.
- `database_path`: non-empty, non-whitespace, NUL-free string only, otherwise
  `ValueError("database_path must be a non-empty string")`.
- `run_context`, `strategy`, `pipeline`, and `budgets_by_race_id`: exact JSON object/dict only, with
  their specified `"... must be an object"` errors.
- `races`: exact JSON array/list only, otherwise `ValueError("races must be an array")`; every item
  must be an exact JSON object/dict, otherwise `ValueError("races must contain objects")`.

Empty races and budgets are valid. Nested domain keys and values belong to 1i5b2.

## Database Path Anchoring

Convert the validated JSON path to `Path`. Preserve an absolute path unchanged. For a relative path,
use exactly:

```python
database_path = source_path.parent / Path(database_path_text)
```

Do not resolve, force a CWD basis, check existence, create a directory/file, or use
`scripts.database.DB_PATH`.

## Recursive Immutable Snapshot

The returned document must share no mutable parsed JSON containers. Recursively convert every JSON
object to `MappingProxyType`, every list to `tuple`, retain strings/ints/bools/None, and retain only
finite floats. This applies to `run_context`, `strategy`, `pipeline`, every race item and nested
array/object, and `budgets_by_race_id`. Object keys remain strings.

`PersistedSimulationRequestDocument` is frozen. Its optional `__post_init__` may protect direct
constructor values, defensive Mapping/tuple copies, and exact Path fields, but must not introduce a
second schema interpretation or duplicate loader validation.

## Failure and Responsibility Boundaries

- Pre-read validation: stable `ValueError`, with no read/parse.
- File `OSError`: same exception object, no retry/fallback.
- UTF-8, JSON, duplicate-key, non-finite, root, or envelope failure: stable `ValueError`, no partial
  document, no database work, logging, or print.

Allowed production concerns are `Path`, UTF-8 `read_text`, `json.loads` with hooks,
`math.isfinite`, `MappingProxyType`, frozen dataclass, and recursive immutable conversion. Do not
add sqlite/migrations/runner calls, domain creation, current time, UUID/git ID, network, logging,
print, argparse, stdout/stderr, exit code, environment/config loading, or changes to `main.py` and
`config/settings.json`.

## Required Tests

Add `tests/test_persisted_simulation_request_document.py` covering:

- module API, frozen dataclass, exact field order/type hints, keyword-only loader/return type, exactly
  one public class/function, and no package-root export;
- valid documents: source path preservation, relative parent anchoring, absolute path preservation,
  empty races/budgets, deep `MappingProxyType`/tuple conversion, mutation failure, and frozen fields;
- all request-path rejection cases before read; raw file failures, invalid UTF-8, empty/malformed JSON;
- duplicate keys at top level, nested run context, and nested race item; and all required non-finite
  values including `1e999`;
- non-object root, exact key set, schema version variants, invalid database path, invalid object
  fields, non-array races, and non-object race items;
- independence from later file rewriting/reload; and
- AST/source checks excluding application/database/domain/CLI/time/network imports and confirming no
  `Any`, `cast`, `type: ignore`, `runtime_checkable`, or broad exception handling. Only
  `UnicodeDecodeError` and `json.JSONDecodeError` exception handlers are permitted.

Run the dedicated test, relevant request/JSON contract tests if present, full `pytest`, required
searches, `git diff --check`, and `git status --short`.

## Forbidden Files and Follow-up

Do not modify existing production/tests, the 1i5a runner, migration/schema, `scripts/database.py`,
`main.py`, `config/settings.json`, existing CLI, or package `__init__` files. Never stage/commit
`database/keiba.db`, `logs/`, or its contents.

1i5b2 owns mapping-to-domain/application inputs. 1i5c owns argparse, request-path intake, stdout,
stderr, exit codes, CLI entry point, and Summary display.

## Stop Condition

After implementation and verification, set `docs/LATEST_CODEX_REPORT.md` to `READY_FOR_REVIEW` and
stop. Do not stage, commit, push, create a review branch, start 1i5b2/1i5c, or create domain objects.

blocker: none
