# Current Phase

## Status

READY_FOR_REVIEW

## Phase

`4C-2d3b1i6d1d5f1c4c0b2` — JRA target race-selection capture v004.

Formal base: `d2e5afde954ed8eb374e6e45244b7129cc77e12b`.

Approved prepare: `95612e45dad6baa4670e659fe51683f341036b59`.

Review branch:
`review/4c-2d3b1i6d1d5f1c4c0b2-jra-target-race-selection-capture-v004`.

## Implemented Contract

Added the distinct frozen/slotted schema-v4 POST family:

```python
JRATargetRaceSelectionResponseCapture
```

It accepts only the formal `JRATargetRaceSelectionRequestLocator`, preserves exact
strict-CP932 response bytes and the existing capture HTTP/timestamp validations, fixes
`schema_version=4`, `page_kind=TARGET_RACE_SELECTION`, and `request_method="POST"`, and
derives its endpoint, request identity, and raw CNAME only from that locator. It converts
only to `JRATargetRaceSelectionSuppliedOfficialResponse`; no URL-bound supplied response
or navigation discovery is widened.

Its capture ID is exactly `jra-capture-v4:` plus lower-case SHA-256 over sorted, compact,
UTF-8 `ensure_ascii=False` JSON containing fixed endpoint, normalized observation time,
`target_race_selection`, locator request identity, `POST`, raw-body SHA-256, and schema
version 4. It intentionally excludes raw CNAME as duplicate identity material because
the locator request digest already binds it.

`JRAOfficialPageKind.TARGET_RACE_SELECTION = "target_race_selection"` is added without
altering any v1/v2/v3 enum meaning. The legacy GET URL canonicalizer and live
`capture_response(...)` remain v1-only and reject this page kind before clock, transport,
or archive use. No live v4 capture method exists.

The archive Protocol and SQLite repository now expose only:

```python
save_target_race_selection_capture(
    *, capture: JRATargetRaceSelectionResponseCapture
) -> None

load_target_race_selection_capture(
    *, capture_id: str
) -> JRATargetRaceSelectionResponseCapture | None

load_target_race_selection_supplied_response_for_evidence(
    *,
    request_locator: JRATargetRaceSelectionRequestLocator,
    response_sha256: str,
    observed_at: datetime,
) -> JRATargetRaceSelectionSuppliedOfficialResponse
```

Save is exact-type, append-only, idempotent for exact identical content, conflict- and
corruption-fail-closed, transaction-owned by the repository, and never auto-migrates or
repairs a missing/corrupt body. V4 ID loaders accept valid v1/v2/v3 IDs as foreign and
return `None`; older loaders reciprocally return `None` for a valid v4 ID. Malformed IDs
remain repository validation errors.

Exact evidence replay queries only fixed endpoint, request identity, response digest, and
UTC observation time. It deliberately does not SQL-filter schema/page/method/CNAME,
then fully reconstructs the selected row as v4 and requires exact locator equality.
Absent evidence is the established capture-missing error; duplicates or corruption are
repository integrity errors. There is no race-ID lookup, latest-by-race lookup, HTTP,
clock, CNAME synthesis, site selection, or live fallback.

## Migration v004

`jra_official_response_capture_migration_v004.py` registers:

```text
VERSION = 4
NAME = v004_jra_official_response_capture_target_race_selection_schema
```

The runner now applies v001, v002, v003, then v004 under its existing foreign-key,
`BEGIN IMMEDIATE`, registry, commit, and rollback ownership. V004 itself is transaction
neutral.

Before mutation, v004 pins and validates exact v003 body/capture/index DDL, columns,
`WITHOUT ROWID`, foreign key, partial-index order/predicates, constraint SAVEPOINT
probes, body SHA integrity, and full v1/v2/v3 domain/capture-ID reconstruction. A
corrupt or lookalike v003 schema fails before rename or v4 registration.

Only `jra_official_response_captures` is rebuilt. Its 19 columns remain unchanged; the
new DDL admits version 4, page kind `target_race_selection`, and exactly the v4 POST
non-null request-identity/CNAME family branch. Existing v1/v2/v3 scalar and family
checks, response-body foreign key, timestamp order, `WITHOUT ROWID`, and both partial
unique indexes are preserved. `jra_official_response_bodies` is neither rebuilt nor
copied. No column, new table, global migration, or index was added.

## Verification

```text
tests/test_jra_official_response_capture.py: 7 passed
tests/test_jra_official_response_capture_migration.py: 12 passed
tests/test_sqlite_jra_official_response_capture_repository.py: 12 passed
dedicated capture/migration/repository: 31 passed

tests/test_jra_official_identity.py
tests/test_jra_target_race_card_locator.py
tests/test_jra_target_race_card_discovery.py
tests/test_jra_official_response_live_capture.py: 42 passed

full pytest suite: 2711 passed
```

Public-surface/family-separation coverage pins the v4 domain, deterministic known ID,
supplied conversion, exact repository APIs, cross-family loaders/saves, corrupt selected
evidence, exact v003 pre-mutation rejection, v1/v2/v3 19-field and body preservation,
v4 DDL family rejection, rollback/no-temp-table behavior, and no live collaborator use
for the new page kind.

## Allowed Files

```text
scripts/simulation/jra_official_response_capture.py
scripts/simulation/jra_official_response_capture_migration_runner.py
scripts/simulation/jra_official_response_capture_migration_v004.py
scripts/simulation/repositories/sqlite_jra_official_response_capture_repository.py
tests/test_jra_official_response_capture.py
tests/test_jra_official_response_capture_migration.py
tests/test_sqlite_jra_official_response_capture_repository.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Exclusions

No live navigation composition, HTTP acquisition, trusted capture, c0b3/c4c work,
target-source normalization, snapshot assembly, race-ID archive lookup, latest-by-race
lookup, package-root export, or global schema/migration work was added.

## Stop Condition

Stop after one pushed review commit for independent ChatGPT implementation review. Do not
start c0b3 or c4c and do not perform live HTTP or a real trusted capture.
