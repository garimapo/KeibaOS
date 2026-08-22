# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase

`4C-2d3b1i6d1d5f1c4c0b2` — JRA target race-selection capture v004 PREPARE.

Formal base: `d2e5afde954ed8eb374e6e45244b7129cc77e12b`.

Formally completed predecessor: `4C-2d3b1i6d1d5f1c4c0b1`.

Review branch:
`review/4c-2d3b1i6d1d5f1c4c0b2-jra-target-race-selection-capture-v004-prepare`.

## Scope

This documentation-only PREPARE freezes the durable archive boundary for the already
formal `JRATargetRaceSelectionRequestLocator` and
`JRATargetRaceSelectionSuppliedOfficialResponse`. It adds no production code, tests,
HTTP, live composition, database mutation, migration, trusted capture, or formal-branch
change.

The archive retains the exact official race-selection POST evidence needed to replay
target-card locator discovery. It never searches by external race ID, synthesizes a
CNAME, chooses a site variant, or substitutes a current response.

## Capture Domain

Add the distinct immutable family:

```python
@dataclass(frozen=True, slots=True)
class JRATargetRaceSelectionResponseCapture:
    request_locator: JRATargetRaceSelectionRequestLocator
    response_body: bytes
    charset: str
    requested_at: datetime
    observed_at: datetime
    stored_at: datetime
    http_status: int
    content_type: str
    content_encoding: str | None = None
    http_date: str | None = None
    etag: str | None = None
    last_modified: str | None = None
    content_length: int | None = None
    schema_version: int = field(init=False, default=4)
    page_kind: JRAOfficialPageKind = field(
        init=False,
        default=JRAOfficialPageKind.TARGET_RACE_SELECTION,
    )
    request_method: str = field(init=False, default="POST")
    response_sha256: str = field(init=False)
    capture_id: str = field(init=False)

    @property
    def canonical_source_url(self) -> str: ...

    def to_supplied_official_response(
        self,
    ) -> JRATargetRaceSelectionSuppliedOfficialResponse: ...
```

The exact page-kind addition is:

```python
JRAOfficialPageKind.TARGET_RACE_SELECTION = "target_race_selection"
```

The capture requires an exact formal request locator, nonempty strict-CP932 bytes,
exact `charset == "cp932"`, HTTP status 200, the existing accepted HTML content-type
grammar, absent or `identity` content encoding, exact content length when present,
valid optional response headers, aware timestamps, and
`requested_at <= observed_at <= stored_at`. Existing UTC normalization preserves the
actual instants. `available_at` is neither invented nor stored.

The fixed persisted request facts are:

```text
canonical_source_url = https://www.jra.go.jp/JRADB/accessD.html
request_method = POST
request_identity_sha256 = request_locator.request_identity_sha256
request_cname = request_locator.cname
```

The capture domain reuses the formal locator's lexical validation and request identity;
it does not duplicate the CNAME grammar or create another request-identity type. Its
supplied-response conversion returns the exact locator, exact raw bytes, `cp932`, and
the actual normalized observation instant. It performs no discovery parse, HTTP, clock,
or repository work.

Capture-family separation remains strict. `JRAOfficialResponseCapture`/`save_capture`
remain schema-v1 GET only; `JRAFinalWinOddsResponseCapture`/its save API remain schema-v2
accessO only; and the target-card domain/save API remain schema-v3 GET only. The existing
v1 URL canonicalizer is not widened for selection POST evidence, and
`JRASuppliedOfficialResponse` is not widened because a race-selection response is bound
to a POST request locator rather than a response URL. Existing `capture_response(...)`
must reject `TARGET_RACE_SELECTION` before clock, transport, or archive use. C0b2 adds
no v4 live service method; c0b3 owns any later dedicated composition.

### Capture identity

The exact v004 identity is:

```text
jra-capture-v4:<64 lowercase hexadecimal SHA-256>
```

The digest is SHA-256 of compact, sorted-key, `ensure_ascii=False` canonical JSON UTF-8
bytes containing exactly:

```json
{
  "canonical_source_url": "https://www.jra.go.jp/JRADB/accessD.html",
  "observed_at_utc": "<UTC ISO-8601 with six fractional digits>",
  "page_kind": "target_race_selection",
  "request_identity_sha256": "<locator request identity>",
  "request_method": "POST",
  "response_sha256": "<SHA-256 of exact raw response bytes>",
  "schema_version": 4
}
```

This mirrors the established v2 POST identity convention. The request digest already
binds the fixed endpoint, POST method, raw CNAME, and request-fingerprint schema. Raw
CNAME remains separately persisted for exact locator reconstruction and integrity
checking. Request/stored timestamps and mutable HTTP headers are deliberately not
capture-ID material, as in v1/v2/v3.

## Physical SQLite Decision

The current v003 physical table cannot accept this family. Its exact DDL constrains
`schema_version IN (1,2,3)`, enumerates only the existing page kinds, and its family
CHECK has no schema-v4 POST branch. A real JRA capture migration v004 is therefore
required.

No column or body representation is missing. The existing capture columns already
store schema version, page kind, endpoint, request method, request identity, raw CNAME,
response digest, timestamps, HTTP metadata, and content length. The existing
`jra_official_response_bodies` table remains unchanged and shared.

Migration v004 is:

```text
VERSION = 4
NAME = v004_jra_official_response_capture_target_race_selection_schema
```

It is added after v001/v002/v003 in `JRA_CAPTURE_MIGRATIONS`. The migration runner
continues to own `PRAGMA foreign_keys=ON`, `BEGIN IMMEDIATE`, registration, commit, and
rollback. The migration step itself is transaction-neutral.

Before mutation, v004 must deterministically validate the exact approved v003 body
table, capture table, and both partial-index DDLs. PRAGMA structure/index/FK checks,
SAVEPOINT constraint probes, complete row/body digest checks, and reconstruction of
every v1/v2/v3 domain and capture ID remain defense-in-depth. Corrupt or merely
lookalike v003 fails before a rename or registry write; it is never repaired.

The migration renames and rebuilds only `jra_official_response_captures`, copies the
same 19 columns without transformation, recreates the two existing partial unique
indexes byte-for-byte in behavior, and drops the temporary old capture table only after
successful copy. It does not rebuild or copy the body table. Runner rollback removes
all temporary state on failure; rerunning the registered migration runner is a no-op.

The new table changes only these enumerations/family alternatives:

```text
schema_version IN (1,2,3,4)
page_kind IN (
  race_result,
  horse_profile_history,
  final_win_odds,
  target_race_card,
  target_race_selection
)

schema v4 family:
  page_kind = target_race_selection
  request_method = POST
  request_identity_sha256 IS NOT NULL
  request_cname IS NOT NULL
```

All existing scalar constraints, timestamp ordering, response-body FK, `WITHOUT
ROWID`, and v1/v2/v3 family branches remain exact. Invalid combinations such as v4 GET,
v4 target card/final odds, missing request material, or v2/v3 target selection are
rejected by DDL. The capture constructor and repository reconstruction independently
enforce the same family contract as defense-in-depth.

No new index is required. The existing request-evidence unique partial index already
covers `(canonical_source_url, request_identity_sha256, response_sha256,
observed_at_utc)` for every non-null request identity, exactly matching v004 evidence
lookup and uniqueness. A further performance-only index is unjustified.

## Repository Contract

The archive Protocol and SQLite repository gain family-specific APIs only:

```python
def save_target_race_selection_capture(
    *,
    capture: JRATargetRaceSelectionResponseCapture,
) -> None: ...

def load_target_race_selection_capture(
    *,
    capture_id: str,
) -> JRATargetRaceSelectionResponseCapture | None: ...

def load_target_race_selection_supplied_response_for_evidence(
    *,
    request_locator: JRATargetRaceSelectionRequestLocator,
    response_sha256: str,
    observed_at: datetime,
) -> JRATargetRaceSelectionSuppliedOfficialResponse: ...
```

Save accepts the exact v4 type only. It remains append-only and transactional, verifies
capture/body identities, performs an idempotent identical re-save, raises
`RepositoryConflictError` when one capture ID names different immutable content, fails
closed on corrupt pre-existing bodies/evidence, and never repairs or auto-migrates.

Load-by-ID accepts only exact `jra-capture-v4:<sha>` grammar. A valid v1/v2/v3 ID is a
foreign-family request and returns `None`; malformed IDs raise
`RepositoryValidationError`; a missing valid v4 ID returns `None`; a stored row reached
by v4 ID that cannot reconstruct as the exact v4 family raises
`RepositoryDataIntegrityError`. Existing v1/v2/v3 loaders reciprocally return `None`
for a valid v4 ID and retain all current behavior.

Exact evidence replay accepts an exact formal request locator, exact lowercase response
SHA-256, and exact aware observation instant. It selects by the fixed endpoint, exact
request identity, response digest, and UTC observation. It deliberately does not filter
away schema/page/method/CNAME metadata whose corruption must be detected during full
row reconstruction. Exactly one reconstructed v4 capture whose reconstructed locator
equals the supplied locator returns its supplied response. No row raises the existing
`JRAOfficialResponseCaptureMissingError`; duplicate or corrupt selected state raises
`RepositoryDataIntegrityError`.

There is no external-race-ID enumeration, latest-by-race lookup, current/live fallback,
URL/CNAME synthesis, site-variant choice, discovery parse, filesystem, or clock in the
repository.

## Backward Compatibility

V1, v2, and v3 capture domains, ID prefixes/material, raw response digests, page kinds,
request locators, supplied conversions, save/load/evidence APIs, and reconstruction
semantics remain byte-for-byte and behaviorally immutable. Migration copies all 19
capture fields without transformation and leaves every response body untouched. Tests
must pin representative v1/v2/v3 capture IDs and exact pre/post-migration row/body/index
equality.

## Future Implementation Scope

Recommended next phase: `4C-2d3b1i6d1d5f1c4c0b2` implementation of the prepared
capture/archive boundary only. Its Allowed Files should be:

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

No locator/discovery production change, live-capture production change, package-root
export, generic union API, schema outside this JRA capture table, or real capture is
needed.

Future tests must cover exact frozen/slotted v4 domain/type/signatures, strict locator
type and CP932/body/header/timestamp validation, raw SHA, deterministic ID material,
supplied reconstruction, and mutated request identity rejection. Repository tests must
cover exact save/load/evidence signatures, idempotence, conflicts, body corruption,
missing and malformed IDs, every cross-family load direction, exact locator equality,
duplicate evidence, selected-row corruption, no race-ID API, and no HTTP/clock.

Family-separation regressions must prove the existing v1 canonicalizer and live
`capture_response(...)` reject `TARGET_RACE_SELECTION` before collaborators; no v4
capture can enter a v1/v2/v3 save path; and the new v4 save path rejects every legacy
capture type. No live-capture production file changes are authorized.

Migration tests must cover clean install through v004, exact 1->2->3->4 upgrade,
pre-mutation exact-v003 rejection, nonempty v1/v2/v3 row/body/ID preservation, unchanged
body table and both indexes, accepted v4 insertion, rejected invalid family matrices,
rollback with no temporary table/registry row, and safe runner rerun. Existing v1/v2/v3
capture/repository/migration regressions and the full suite remain required.

## Readiness Matrix

```text
TARGET_RACE_SELECTION_CAPTURE_DOMAIN_READY: YES
TARGET_RACE_SELECTION_CAPTURE_DOMAIN_NAME: JRATargetRaceSelectionResponseCapture

V004_CAPTURE_ID_PREFIX: jra-capture-v4:
V004_CAPTURE_ID_MATERIAL: FIXED_ENDPOINT + OBSERVED_AT_UTC + TARGET_RACE_SELECTION + REQUEST_IDENTITY_SHA256 + POST + RESPONSE_SHA256 + SCHEMA_VERSION_4
V004_CAPTURE_ID_READY: YES

V004_CANONICAL_SOURCE_URL: https://www.jra.go.jp/JRADB/accessD.html
V004_REQUEST_METHOD: POST
V004_REQUEST_IDENTITY_REQUIRED: YES_EXACT_LOCATOR_SHA256
V004_REQUEST_CNAME_REQUIRED: YES_EXACT_RAW_LOCATOR_CNAME

V004_ROW_CONTRACT_READY: YES
V004_ROW_CONSTRAINT_OWNER: DDL_CHECK + CAPTURE_DOMAIN + REPOSITORY_RECONSTRUCTION

LOGICAL_CAPTURE_SCHEMA_V004_REQUIRED: YES
PHYSICAL_SQLITE_DDL_CHANGE_REQUIRED: YES
TABLE_REBUILD_REQUIRED: YES_CAPTURE_TABLE_ONLY
NEW_COLUMN_REQUIRED: NO
NEW_TABLE_REQUIRED: NO
NEW_INDEX_REQUIRED: NO
INDEX_REASON: EXISTING_NON_NULL_REQUEST_IDENTITY_PARTIAL_UNIQUE_INDEX_EXACTLY_COVERS_V004_EVIDENCE_IDENTITY

MIGRATION_REQUIRED: YES
MIGRATION_NUMBER: 4_IN_DEDICATED_JRA_CAPTURE_REGISTRY; GLOBAL_APPLICATION_MIGRATIONS_UNCHANGED
MIGRATION_STRATEGY: VALIDATE_EXACT_V003_THEN_TRANSACTION_NEUTRAL_CAPTURE_TABLE_ONLY_REBUILD

V1_IMMUTABILITY: REQUIRED_BYTE_FOR_BYTE_AND_BEHAVIORALLY
V2_IMMUTABILITY: REQUIRED_BYTE_FOR_BYTE_AND_BEHAVIORALLY
V3_IMMUTABILITY: REQUIRED_BYTE_FOR_BYTE_AND_BEHAVIORALLY

SAVE_API_READY: YES
SAVE_API_SIGNATURE: save_target_race_selection_capture(*, capture: JRATargetRaceSelectionResponseCapture) -> None

LOAD_BY_ID_API_READY: YES
LOAD_BY_ID_API_SIGNATURE: load_target_race_selection_capture(*, capture_id: str) -> JRATargetRaceSelectionResponseCapture | None

EXACT_EVIDENCE_LOADER_READY: YES
EXACT_EVIDENCE_LOADER_SIGNATURE: load_target_race_selection_supplied_response_for_evidence(*, request_locator: JRATargetRaceSelectionRequestLocator, response_sha256: str, observed_at: datetime) -> JRATargetRaceSelectionSuppliedOfficialResponse

RACE_ID_ONLY_ARCHIVE_LOOKUP_SAFE: NO
EXTERNAL_RACE_ID_ONLY_LOCATOR_LOOKUP_SAFE: NO

LIVE_HTTP_IN_C0B2: NO
LIVE_COMPOSITION_DEFERRED_TO: 4C-2d3b1i6d1d5f1c4c0b3

C0B2_IMPLEMENTATION_READY: YES
IMPLEMENTATION_READY: YES
BLOCKERS: NONE
REAL_TRUSTED_CAPTURE_REQUIRED: NO
```

## Allowed Files

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Required Checks

```text
git diff --check
git status --short
changed-file scope == the two allowed docs
formal remote head remains d2e5afde954ed8eb374e6e45244b7129cc77e12b
```

## Stop Condition

Commit and push this documentation-only review branch, then stop for independent
ChatGPT architecture review. Do not implement c0b2, start c0b3/c4c, perform live HTTP,
or perform a real trusted capture.
