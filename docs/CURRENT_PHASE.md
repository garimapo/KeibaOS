# Current Phase

## Status

READY_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6c1d3b2b1` — NAR official-response capture domain and dedicated SQLite archive implementation.

Formal base: `4af5a7ba4f18769f365ac2c934bcfd0ffcf38818 feat: normalize NAR historical past races`.

Formal branch: `feature/ver0.8-simulator`.

Implementation review branch: `review/4c-2d3b1i6c1d3b2b1-implementation`.

Only these files changed: capture domain, dedicated SQLite repository, dedicated v001 migration and runner, their three dedicated tests, and these two documents. No main migration, global runner, c1a/c1b/d3b2a/builder, fixture, HTTP, clock, acquisition, or orchestration changed.

## Implemented Trust and URL Boundary

`TRUST_MODEL = OPERATIONALLY_TRUSTED_LOCAL_CAPTURE`; `RETROACTIVE_LIVE_SITE_BACKFILL = IMPOSSIBLE_TO_TRUST`; `available_at = None`. The archive stores exact parser-input entity bytes and SHA-256 before UTF-8 decoding, NFC, parsing, or whitespace processing. `EXACT_PARSER_INPUT_BYTES = YES`; strict UTF-8 is required and bytes are never text-round-tripped. Unsupported content encodings fail closed; only absent or `identity` is accepted.

`canonicalize_nar_official_capture_url()` is pure and supports exactly:

| kind | accepted HTTPS host(s) | exact path | exact keys |
| --- | --- | --- | --- |
| `deba_table` | `www.keiba.go.jp` | `/KeibaWeb/TodayRaceInfo/DebaTable` | `k_babaCode`, `k_raceDate`, `k_raceNo` |
| `horse_mark_info` | `www.keiba.go.jp`, `www2.keiba.go.jp` | `/KeibaWeb/DataRoom/HorseMarkInfo` | `k_lineageLoginCode` |
| `race_mark_table` | `www.keiba.go.jp` | `/KeibaWeb/TodayRaceInfo/RaceMarkTable` | `k_babaCode`, `k_raceDate`, `k_raceNo` |

It rejects non-HTTPS, foreign/IP hosts, credentials, fragments, whitespace/control text, invalid ports, unknown paths/keys, duplicate or blank keys, malformed percent escapes, `+`, invalid real dates, and noncanonical positive ASCII tokens. Race URLs canonicalize to ordered `k_babaCode`, escaped `k_raceDate=YYYY%2FMM%2FDD`, and `k_raceNo`; HorseMark preserves accepted `www`/`www2` host identity.

## Immutable Capture Domain

`scripts/simulation/nar_official_response_capture.py` defines exactly:

```python
NAROfficialPageKind
NAROfficialResponseCapture
NAROfficialResponseCaptureArchive
NAROfficialResponseCaptureError
NAROfficialResponseCaptureValidationError
NAROfficialResponseCaptureUnsupportedError
NAROfficialResponseCaptureMissingError
canonicalize_nar_official_capture_url
```

`NAROfficialResponseCapture` is frozen/slotted. Callers supply canonical URL, exact bytes, UTF-8 charset, requested/observed/stored aware datetimes, status, and optional retained header metadata. It derives schema version 1, page kind, raw-body SHA-256, and capture ID. Datetimes normalize to fixed 32-character microsecond UTC text and require `requested_at <= observed_at <= stored_at`.

`capture_id` is exactly `nar-capture-v1:` plus SHA-256 of canonical sorted compact UTF-8 JSON containing only `schema_version`, `page_kind`, `canonical_source_url`, `response_sha256`, and `observed_at_utc`. URL/body/observed-time changes alter the ID; requested/stored/header-only changes do not. `to_supplied_official_response()` reconstructs the existing `NarSuppliedOfficialResponse` with byte-identical body, canonical URL, UTF-8, and preserved observed time.

## Separate Capture Database and Dedicated v001

`DATABASE_LOCATION = SEPARATE_NAR_CAPTURE_DATABASE`; `CROSS_DATABASE_LINKAGE = EXISTING_EVIDENCE_IDENTITY_TUPLE`; `CROSS_DATABASE_ATOMIC_TRANSACTION = NOT_REQUIRED`; `CAPTURE_DATABASE_PATH = COMPOSITION_OWNED`. The repository is connection-injected, knows no main/simulation database table or path, and never `ATTACH`es. Capture persistence happens before later normalization; unused successful captures are safe and persistence failure means no trusted operational evidence.

`GLOBAL_MIGRATION_REQUIRED = NO`. Global sequence stays exactly `(8, 9, 10, 11, 12)`; no v013 or global migration test/runner/version change exists.

Dedicated migration API:

```python
VERSION = 1
NAME = "v001_nar_official_response_capture_schema"
apply(connection)
CAPTURE_MIGRATIONS
get_applied_capture_schema_versions
get_pending_capture_schema_migrations
apply_capture_schema_migrations
```

The dedicated migration registry is `nar_official_response_capture_schema_migrations`. The transaction-neutral v001 migration creates only `nar_official_response_bodies`, `nar_official_response_captures`, and the sole unique lookup index `ux_nar_official_response_captures_evidence(canonical_source_url, response_sha256, observed_at_utc)`. The runner independently validates its registry, enables/verifies foreign keys, rejects active transactions and invalid applied state, and owns `BEGIN IMMEDIATE`/commit/rollback. It imports neither global migration registry nor main simulation schema.

## Archive Operations and Fail-Closed Behavior

`SQLiteNAROfficialResponseCaptureRepository(*, connection: sqlite3.Connection)` is the only repository public class. It reuses `RepositoryValidationError`, `RepositoryConflictError`, and `RepositoryDataIntegrityError`. It exposes only save, capture-ID load, and exact evidence-tuple reconstruction.

Save is append-only and atomic: verify caller capture and raw SHA, deduplicate/validate content-addressed body, compare an existing same-ID capture as full immutable content, reject conflicts, then insert the capture. Failed late insert rolls back a newly inserted body. Same body with a different observed time has one body and two observations. Exact evidence lookup has no nearest/latest/same-URL/same-SHA/network fallback; absent evidence raises `NAROfficialResponseCaptureMissingError`.

Every load reconstructs and validates body length/digest, canonical URL, derived kind/ID/SHA, UTC timestamp text/order, UTF-8 charset, HTTP 200, header metadata, and Content-Length. Missing bodies, corruption, duplicate/impossible identity, or SQLite data failure raise `RepositoryDataIntegrityError`; storage is never repaired or normalized.

`SAVE_ON_PREEXISTING_ARCHIVE_CORRUPTION = FAIL_CLOSED_NO_REPAIR`. Save preflights capture ID, exact evidence tuple, and body SHA before inserting any missing body. A capture row with missing/corrupt body, an absent body already referenced by another capture, or duplicate/contradictory evidence identity is `RepositoryDataIntegrityError`; save leaves that body absent and the pre-existing rows unchanged. `MISSING_REFERENCED_BODY_ON_SAVE = REPOSITORY_DATA_INTEGRITY_ERROR`.

`LOAD_CAPTURE_EVIDENCE_UNIQUENESS = REQUIRED`. Reconstruction verifies that the loaded capture's exact evidence tuple has exactly one row and the expected capture ID; both capture-ID load and evidence-tuple load therefore fail closed on broken uniqueness. `RECONSTRUCTION_SQLITE_ERRORS = REPOSITORY_DATA_INTEGRITY_ERROR`: SQLite errors from capture reconstruction/body/evidence reads never leak raw. Genuine exact tuple absence remains `NAROfficialResponseCaptureMissingError`, and malformed callers remain `RepositoryValidationError`.

`PREEXISTING_UNREGISTERED_CAPTURE_SCHEMA = FAIL_CLOSED`. v001 uses plain `CREATE TABLE` / `CREATE UNIQUE INDEX`, not `IF NOT EXISTS`; the dedicated registry, not direct migration application, owns idempotency. `DIRECT_V001_APPLY_IDEMPOTENT = NO_REQUIREMENT`; `RUNNER_IDEMPOTENT = YES`.

## Verification and Stop Condition

External verification used Python 3.14.5 and pytest 8.3.5. Dedicated capture domain/migration/repository tests: 25 passed. Related existing NAR/c1a/c1c snapshot tests: 53 passed. Full suite: 2493 passed. Dedicated static checks confirm no package-root export, no main migration change, no HTTP/filesystem/clock ownership in domain/repository, no global migration import in dedicated runner, and no `ATTACH` behavior.

`PERSIST_BEFORE_NORMALIZATION`, live HTTP transport, clock construction, scheduling, composition, `capture_database_path`, multi-race collection, pagination, `past_race_absence`, and formal integration remain out of scope. Stop for independent GitHub implementation review.
