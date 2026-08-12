# Current Phase

## Status

READY_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6d1c1` — JRA supplied-response/capture domain plus dedicated SQLite archive implementation.

Formal base: `7632a1381c77403e55284e027392d0fbc1f5a346`.

Implementation review branch: `review/4c-2d3b1i6d1c1-implementation`.

Approved preparation: `7cf4083e27fd4d0df256c55b0487179ea28baeb4`.

## Implemented Contract

```text
JRA_CAPTURE_DOMAIN = IMPLEMENTED_FOR_REVIEW
JRA_CAPTURE_SCHEMA_VERSION = 1
JRA_CAPTURE_DATABASE = SEPARATE
JRA_CAPTURE_PAGE_KINDS = RACE_RESULT + HORSE_PROFILE_HISTORY
RAW_RESPONSE_SHA = EXACT_CP932_PARSER_INPUT_BYTES
JRA_CAPTURE_MIGRATION = DEDICATED_V001
JRA_CAPTURE_MIGRATION_REGISTRY_SCHEMA_VALIDATION = EXACT_FAIL_CLOSED
MALFORMED_REGISTRY_AUTO_REPAIR = FORBIDDEN
PREEXISTING_UNREGISTERED_CAPTURE_SCHEMA = REJECTED
GLOBAL_MIGRATION_FINAL_VERSION = 13
NAR_CAPTURE = UNCHANGED
JRA_LIVE_CAPTURE = NOT_IMPLEMENTED
NAR_LINEAGE_TO_JRA_HORSE_ID_LINK = NOT_PROVEN
MIXED_HISTORY_COLLECTION_READY = NO
```

The module `scripts/simulation/jra_official_response_capture.py` exposes exactly:

```text
JRAOfficialPageKind
JRAOfficialResponseCaptureError
JRAOfficialResponseCaptureValidationError
JRAOfficialResponseCaptureUnsupportedError
JRAOfficialResponseCaptureMissingError
JRASuppliedOfficialResponse
JRAOfficialResponseCapture
JRAOfficialResponseCaptureArchive
canonicalize_jra_official_capture_url
```

The supported page kinds are only `race_result` / accessS and `horse_profile_history` / accessU. The canonicalizer
uses the public JRA identity validators, preserves valid CNAME selector/date/tail retrieval identity, and renders the
single CNAME delimiter as uppercase `%2F`; raw slash is an alias, while lowercase and double-encoded forms fail
closed. Entity identities remain distinct from capture URLs.

Both supplied and archived capture values require exact nonempty CP932 bytes, strict CP932 decode, canonical supported
URL, exact `charset="cp932"`, and aware UTC observation. The capture derives page kind, raw lowercase SHA-256, and
`jra-capture-v1:<sha256>` from canonical URL, page kind, raw SHA, observed UTC microsecond text, and schema version.
Requested/observed/stored timestamps are monotonic; HTTP status is exact integer 200; HTML content type is normalized
to the approved `text/html` family, coding is absent or `identity`, and auxiliary headers remain non-semantic audit
metadata. No decoded text is retained or hashed.

The dedicated v001 registry is `jra_official_response_capture_schema_migrations`; its body and capture tables are
`jra_official_response_bodies` and `jra_official_response_captures`. Its structural validation is exact and
fail-closed: the two-column `WITHOUT ROWID` table, typed positive version check, typed nonempty unique name check,
and registered migration rows must all match the approved contract. A malformed registry or pre-existing unregistered
JRA capture table is rejected without adoption, alteration, or repair. The registry is separate from both global and
NAR registries, and no global migration is added. The connection-injected repository is
append-only, body-deduplicated, atomic, and fail-closed for malformed registry/tables, missing/corrupt bodies,
nonunique evidence tuples, or derived-identity mismatch. Exact replay is only by canonical URL, SHA, and observed UTC;
there is no latest/nearest/network fallback or repair-on-save.

## Allowed Files

```text
scripts/simulation/jra_official_response_capture.py
scripts/simulation/jra_official_response_capture_migration.py
scripts/simulation/jra_official_response_capture_migration_runner.py
scripts/simulation/repositories/sqlite_jra_official_response_capture_repository.py
tests/test_jra_official_response_capture.py
tests/test_jra_official_response_capture_migration.py
tests/test_sqlite_jra_official_response_capture_repository.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Verification and Stop Condition

Dedicated JRA archive tests and existing JRA identity/NAR capture regressions pass. Full-suite verification, source-boundary
checks, package-root export check, and diff check are required before publication. Stop for independent implementation
review after one review commit. Do not integrate formal or begin live capture, JRA result normalization, or a provider
bridge.
