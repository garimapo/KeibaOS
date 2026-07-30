# Current Phase

## Status

APPROVED_FOR_CODEX

## Phase

Phase 4C-2d3b1i5b2b — Persisted simulation race input and audit assembler

## Base Commit

`b06503c docs: approve persisted simulation application inputs`

## Branch

`feature/ver0.8-simulator`

## Objective

Assemble complete, audited race inputs for the 1i5a application runner without opening a DB or invoking
the runner:

```text
PersistedSimulationRequestDocument.races
+ PersistedSimulationApplicationInputs
→ PastRace
→ RaceTrackConditions
→ RacePredictionInput
→ InputAuditEntry
→ InputSnapshotAudit
→ SimulationRaceInput
→ tuple[SimulationRaceInput, ...]
```

1i5b1 document loading and 1i5b2a application assembly are complete. This phase owns no CLI, runner,
DB, repository, schema, migration, summary, or persistence composition work. 1i5c alone owns:

```text
load document → application inputs → race inputs → runner invocation → summary output
```

## Allowed Files

```text
scripts/simulation/persisted_simulation_race_inputs.py
tests/test_persisted_simulation_race_inputs.py
docs/LATEST_CODEX_REPORT.md
```

`docs/CURRENT_PHASE.md` is approved contract documentation and is not an implementation target.

## Formal Public API

```python
from __future__ import annotations

from scripts.simulation.models import SimulationRaceInput
from scripts.simulation.persisted_simulation_application_inputs import (
    PersistedSimulationApplicationInputs,
)
from scripts.simulation.persisted_simulation_request_document import (
    PersistedSimulationRequestDocument,
)


def assemble_persisted_simulation_race_inputs(
    *,
    document: PersistedSimulationRequestDocument,
    application_inputs: PersistedSimulationApplicationInputs,
) -> tuple[SimulationRaceInput, ...]:
    ...
```

This function is the only public production definition. All helpers must begin with `_`. Do not add a
public dataclass, Protocol, ABC, repository, service, bundle, CLI helper, or package-root export.

## Input Boundary and Linkage

Require exact types; subclasses are rejected:

```python
if type(document) is not PersistedSimulationRequestDocument:
    raise ValueError("document must be a PersistedSimulationRequestDocument")
if type(application_inputs) is not PersistedSimulationApplicationInputs:
    raise ValueError(
        "application_inputs must be a PersistedSimulationApplicationInputs"
    )
if application_inputs.database_path is not document.database_path:
    raise ValueError(
        "application_inputs.database_path must be document.database_path"
    )
```

Do not reparse `document.run_context`, `strategy`, `pipeline`, or `budgets_by_race_id`. Use only
`application_inputs.run_context.dataset_id` and `application_inputs.budgets_by_race_id` for application
information. Do not reread JSON, revalidate its top-level envelope, or re-anchor the path.

## Containers, Pre-scan, and Ordering

- `document.races` must be an exact tuple or raise `document.races must be an array`.
- Empty races are valid only with empty budgets.
- Race items must be Mapping values or raise `document.races must contain objects`.
- Every race must have exactly `race_id`, `target_race_date`, `scheduled_start_at`,
  `information_cutoff`, `audit`, `track_conditions`, and `entries`; otherwise raise
  `race keys must exactly match the race schema`.
- First pre-scan every race schema and its exact positive non-bool integer `race_id`; malformed IDs raise
  `race.race_id must be a positive integer`.
- Duplicate IDs raise `document.races must not contain duplicate race_id values`.
- Before any domain object is made, require
  `set(race_ids) == set(application_inputs.budgets_by_race_id)`, otherwise raise
  `race IDs must exactly match application budget race IDs`.
- Assemble all successful races, then return an exact tuple sorted by `(scheduled_start_at, race_id)`.
  Request race order is not meaningful.

Formal assembly order:

```text
1 document exact type
2 application_inputs exact type
3 database_path identity
4 races exact tuple
5 race object/key pre-scan
6 race_id validation
7 duplicate race_id validation
8 race/budget ID set equality
9 race timings
10 race audit
11 track conditions and track audit
12 entries and entry IDs
13 entry scalars
14 entry audits
15 past races and past-race audits
16 RacePredictionInput
17 InputSnapshotAudit
18 SimulationRaceInput existing fail-closed validation
19 race sort
20 tuple return
```

Failure stops processing immediately: no later race/domain object, partial result, retry, fallback, or
generic exception translation is permitted.

## Date and Numeric Rules

### Dates and required datetimes

`race.target_race_date` and `past_race.race_date` are exact `str` canonical `YYYY-MM-DD` values:

```python
parsed = date.fromisoformat(value)
if value != parsed.isoformat():
    ...
```

Their errors are respectively:

```text
race.target_race_date must be a canonical ISO date
past_race.race_date must be a canonical ISO date
```

Reject basic, week, slash, unpadded, datetime, empty, and non-string forms. Preserve the original valid
past-race text in `PastRace.race_date`.

Required aware datetime paths are `race.scheduled_start_at`, `race.information_cutoff`, and
`race.audit.captured_at`. Require exact `str`, `datetime.fromisoformat` parsing (with terminal `Z`
interpreted as `+00:00`), `tzinfo`, and non-`None` `utcoffset()`. Their errors are:

```text
<field path> must be an ISO 8601 timezone-aware datetime
```

Generic-audit `available_at` and `observed_at` accept only exact `str` aware datetimes or exact `None`;
invalid values raise:

```text
<audit path>.<field> must be an ISO 8601 timezone-aware datetime or null
```

No timezone conversion, automatic timezone, current-time fallback, `datetime.now`, `datetime.utcnow`,
or `date.today` is allowed. Before domain construction require:

```text
race.information_cutoff <= race.scheduled_start_at
```

Otherwise raise `race.information_cutoff must be earlier than or equal to race.scheduled_start_at`.

### Numeric conversion

Numeric source values may be exact `int` or exact `float` only; bool, subclasses, strings, Decimal,
NaN, infinities, clamp, and fallback are forbidden. Before float conversion, exact ints must be bounded
against:

```python
_MAX_FINITE_FLOAT = float.fromhex("0x1.fffffffffffffp+1023")
```

Do not catch `OverflowError`. This rule applies to entry odds and all finite past-race fields.

## Race Audit and Generic Audit Stamps

`race.audit` must be a Mapping with exactly `source`, `captured_at`, `is_complete`:

```text
race.audit must be an object
race.audit keys must exactly match the race audit schema
race.audit.source must be a non-empty string
race.audit.is_complete must be a boolean
```

Text must be exact non-empty, non-whitespace `str` and must not be trimmed. Build:

```python
InputSnapshotAudit(
    dataset_id=application_inputs.run_context.dataset_id,
    source=source,
    captured_at=captured_at,
    entries=...,
    is_complete=is_complete,
)
```

`False` is schema-valid; final existing `SimulationRaceInput` validation must fail closed if incomplete.

All generic audit locations use the same exact Mapping schema:

```text
track_conditions.audit
entry.audits.entry
entry.audits.jockey
entry.audits.odds
entry.audits.past_race_absence
past_race.audit
```

Required keys are `source`, `source_id`, `available_at`, `observed_at`. Errors use the exact patterns:

```text
<audit path> must be an object
<audit path> keys must exactly match the audit stamp schema
<audit path>.source must be a non-empty string
<audit path>.source_id must be a non-empty string
<audit path> requires available_at or observed_at
```

At least one timestamp is non-null. Existing final validation, not a custom workaround, rejects audit
timestamps later than the cutoff as `SimulationValidationError`.

## Track Conditions

`race.track_conditions` is a Mapping with exact keys `place`, `distance`, `track`,
`track_condition`, `audit`; otherwise use:

```text
race.track_conditions must be an object
race.track_conditions keys must exactly match the track conditions schema
race.track_conditions.place must be a non-empty string
race.track_conditions.track must be a non-empty string
race.track_conditions.track_condition must be a non-empty string
race.track_conditions.distance must be a positive integer
```

Build exact `RaceTrackConditions`. Its audit becomes:

```python
InputAuditEntry(
    input_type="track", audit_key="track", race_entry_id=None,
    past_race_index=None, ...
)
```

## Entries and Past Races

`race.entries` is an exact nonempty tuple, otherwise
`race.entries must be a non-empty array`; each item is Mapping or
`race.entries must contain objects`. Each entry requires exact keys:

```text
race_entry_id
jockey_name
odds
past_races
audits
```

Key mismatch raises `entry keys must exactly match the entry schema`. `race_entry_id` is exact positive
non-bool `int` (`entry.race_entry_id must be a positive integer`) and must be unique per race
(`race.entries must not contain duplicate race_entry_id values`). Process entries in ascending
`race_entry_id`, not request order.

`jockey_name` is exact nonempty non-whitespace string or
`entry.jockey_name must be a non-empty string`. `odds` is exact finite positive int/float and converts to
float, otherwise `entry.odds must be a positive finite number`.

`audits` is Mapping with exactly `entry`, `jockey`, `odds`, `past_race_absence`; errors are
`entry.audits must be an object` and `entry.audits keys must exactly match the entry audits schema`.
Generated canonical keys for each sorted entry are:

```text
entry/{race_entry_id}
odds/{race_entry_id}
jockey/{race_entry_id}
past_race/{race_entry_id}/none             (no past races)
past_race/{race_entry_id}/{request index}  (one or more past races)
```

For empty exact-tuple `past_races`, `past_race_absence` must be a Mapping; otherwise raise
`entry.audits.past_race_absence is required when past_races is empty`. For nonempty exact-tuple
`past_races`, it must be exact `None`; otherwise raise
`entry.audits.past_race_absence must be null when past_races is not empty`. `past_races` itself must be
an exact tuple or `entry.past_races must be an array`; items must be Mapping or
`entry.past_races must contain objects`. Preserve its request order and indexes.

Every past race requires exactly:

```text
race_date place race_name race_class distance track weather track_condition finish margin time
weight weight_diff jockey popularity odds passing_order fourth_corner_position audit
```

Key mismatch raises `past_race keys must exactly match the past race schema`. Use the current
`race_entry_id` as `PastRace.horse_id`; never accept `horse_id` in the request. Exact string fields
`place`, `race_name`, `race_class`, `track`, `weather`, `track_condition`, `time`, `jockey`, and
`passing_order` allow empty strings but otherwise raise `past_race.<field> must be a string`.

The exact integer and numeric constraints/errors are:

```text
distance, finish: positive int
  → past_race.distance must be a positive integer
  → past_race.finish must be a positive integer
popularity, fourth_corner_position: non-negative int
  → past_race.popularity must be a non-negative integer
  → past_race.fourth_corner_position must be a non-negative integer
margin, weight_diff: finite numeric
  → past_race.margin must be finite
  → past_race.weight_diff must be finite
weight, odds: non-negative finite numeric
  → past_race.weight must be a non-negative finite number
  → past_race.odds must be a non-negative finite number
```

Build its generic audit with `past_race/{race_entry_id}/{index}` and request index as
`past_race_index`.

## Domain Assembly and Existing Validation

For sorted entries build:

```python
RacePredictionInput(
    horse_past_races=...,
    jockey_names_by_horse=...,
    track_conditions=track_conditions,
    odds_by_horse=...,
    race_horse_count=len(entries),
    race_id=race_id,
    prediction_time=information_cutoff.isoformat(),
)
```

Audit entries are ordered by each ascending entry ID as entry, odds, jockey, then absence or indexed
past races; append `track` last. Build `InputSnapshotAudit`, then build `SimulationRaceInput`. The latter
must perform its existing defensive conversion to `ImmutableRacePredictionInput` and existing
fail-closed validation. Do not catch/wrap its `SimulationValidationError`, or domain `ValueError`/
`TypeError`.

Existing validation must reject, among other conditions: incomplete audits, audit captured/timestamped
after cutoff, same/future past races, missing category entries, unknown audit keys, metadata/key mismatch,
and race/pipeline ID mismatch.

## Failure, Dependency, and Immutability Boundaries

Only two production `ExceptHandler`s are allowed:

```text
_parse_canonical_iso_date → ValueError
_parse_aware_datetime → ValueError
```

No `Exception`, `BaseException`, `OverflowError`, broad catches, retry, fallback, logging, print, or
partial result is allowed. Generated snapshots must retain immutable mappings/tuples and have no mutable
reference sharing with corrupt raw request containers.

Forbidden dependencies include file/JSON parsing, path anchoring, SQLite/migrations/runner/composition,
`PersistedSimulationRunService`, repository/DB/network/subprocess, logging/print/argparse/stdout/stderr,
exit code, clock/UUID/environment/config loading, `main.py`, summary formatting, and package-root export.
Do not modify 1i5b2a production.

## Required Tests

Add `tests/test_persisted_simulation_race_inputs.py` using real objects only; mocks, patches, and
monkeypatches are forbidden. Cover:

- formal module/function API, keyword-only argument order/type hints, one public function/no public
  class, package-root non-export;
- two-race valid assembly in reverse request/time order, two entries including one two-item past-race
  history and one absence case; all generated domain/audit fields, immutable snapshots, canonical orders,
  dataset linkage, database-path identity, and budget IDs;
- deterministic double assembly; document/application exact-type and path-identity linkage;
- all race container/ID/budget-set, timing/date, race-audit, generic-audit, track, entry, absence,
  past-race, numeric huge-int, and direct snapshot immutability matrices described above;
- existing `SimulationValidationError` fail-closed cases for audit timing/completeness and past-race dates;
- source literal/AST contract: no forbidden dependencies, no type-ignore/Any/cast/runtime_checkable,
  no broad handlers, and exactly the two parser-owned ValueError handlers.

Run exactly the dedicated test plus relevant existing suites (use existing nearest names if absent):

```text
tests/test_persisted_simulation_race_inputs.py
tests/test_persisted_simulation_application_inputs.py
tests/test_persisted_simulation_request_document.py
tests/test_simulation_validation.py
tests/test_sqlite_persisted_simulation_application.py
tests/test_persisted_simulation_run_service.py
tests/test_prediction_pipeline.py
tests/test_track_engine.py
python -m pytest -q
git diff --check
git status --short
```

## Forbidden Files and Stop Condition

Do not change existing production/tests, 1i5b1, 1i5b2a, 1i5a runner/composition, migration/schema,
`scripts/database.py`, `main.py`, `config/settings.json`, CLI, or package `__init__`. Never stage or
commit `database/keiba.db` or `logs/`.

After implementation set the report status to `READY_FOR_REVIEW` and stop. Do not stage, commit, push,
create a review branch, read a DB, invoke the runner, or begin 1i5c.

blocker: none
